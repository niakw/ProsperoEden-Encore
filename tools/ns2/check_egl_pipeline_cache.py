#!/usr/bin/env python3
"""N56: source-bound PS5 Vulkan pipeline cache short-header guard, Clang/GCC."""
from pathlib import Path
import os
import subprocess
import tempfile
ROOT=Path(__file__).resolve().parents[2]
ORIG=ROOT/'vendor/encore-active/eden-vulkan/vk_pipeline_cache_cost.cpp'
CMAKE=(ROOT/'headless/CMakeLists.txt').read_text()
import hashlib
before="        u32 cache_version;\n        file.read(magic_number.data(), magic_number.size())"
after="""        u32 cache_version;
#ifdef EDEN_NS2_PIPELINE_CACHE_GUARD
        // Reject truncated (including failed tellg) Vulkan driver cache headers
        // before reading or subtracting an unsigned header size.
        if (end < std::streampos{static_cast<std::streamoff>(
                      magic_number.size() + sizeof(cache_version))}) {
            file.close();
            LOG_WARNING(Common_Filesystem, "Short Vulkan driver cache; rebuilding fresh");
            Common::FS::RemoveFile(filename);
            return create_pipeline_cache(0, nullptr);
        }
#endif
        file.read(magic_number.data(), magic_number.size())"""
current=ORIG.read_text()
assert current.count(after)==1, "N56 exact vendor source guard drift"
assert "Saved PS5 driver pipeline cache atomically" in current
# The old N3m snapshot oracle expected three guarded Vulkan regions; the
# actual maintained pipeline now has seven independent regions and a signed
# final stage recheck. The active generator and fully reviewed vendor-source
# parity guard are stronger than stripping these evolving regions here.
# Preserve the exact N56 source snippet + binary negative test below.
import sys
subprocess.run([sys.executable, str(ROOT / 'tools/check-vendored-vulkan-fork.py')],
               check=True)
assert 'if(PS5_NATIVE AND EDEN_PS5_VULKAN)' in CMAKE
assert 'option(EDEN_NS2_PIPELINE_CACHE_EXPERIMENTAL' not in CMAKE
assert 'target_compile_definitions(video_core PRIVATE EDEN_NS2_PIPELINE_CACHE_GUARD=1)' in CMAKE
assert 'prepare_egl_pipeline_cache.cmake' not in CMAKE
# Apple CLT 27.0 SDK stubs require a newer TAPI than the local linker.
# This is only a host C++ fixture override; native PS5 flags are unaffected.
compiler_env = os.environ.copy()
if sys.platform == 'darwin' and not compiler_env.get('SDKROOT'):
    supported_sdk = Path('/Library/Developer/CommandLineTools/SDKs/MacOSX15.4.sdk')
    if supported_sdk.is_dir():
        compiler_env['SDKROOT'] = str(supported_sdk)
with tempfile.TemporaryDirectory(prefix='n56-native-cache-') as td:
    out=Path(td)
    snippet=after.split('        file.read(magic_number.data()')[0].split('        u32 cache_version;')[1]
    src=r'''#include <array>
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <filesystem>
#include <fstream>
#include <vector>
#define LOG_WARNING(...) ((void)0)
using u32=std::uint32_t;
namespace Common::FS {
bool RemoveFile(const std::filesystem::path& filename) {
    return std::filesystem::remove(filename);
}
}
bool Test(const std::filesystem::path& filename) {
    const auto create_pipeline_cache=[](std::size_t bytes,const void* ptr) {
        assert(bytes==0 && ptr==nullptr); return true;
    };
    std::ifstream file(filename,std::ios::binary|std::ios::ate);
    assert(file.is_open());
    const auto end=file.tellg();
    file.seekg(0,std::ios::beg);
    std::array<char,8> magic_number{};
    u32 cache_version{};
''' + snippet + r'''
    return false;
}
int main(int argc,char** argv) {
    assert(argc==2);
    auto dir=std::filesystem::path(argv[1]);
    for(int size=0;size<=24;++size) {
        auto filename=dir/("cache_"+std::to_string(size));
        {
            std::ofstream out(filename,std::ios::binary);
            std::vector<char> data(static_cast<std::size_t>(size),42);
            out.write(data.data(),size);
        }
        const bool rejected=Test(filename);
        assert(rejected==(size<12));
        assert(std::filesystem::exists(filename)==(size>=12));
    }
}
'''
    source=out/'test.cpp'
    source.write_text(src)
    for cxx in ('clang++','g++'):
        exe=out/('n56-'+cxx.replace('+','p'))
        subprocess.run([cxx,'-std=c++20','-O2','-Wall','-Wextra','-Werror',
                       '-fsanitize=undefined','-fno-sanitize-recover=all',
                       '-DEDEN_NS2_PIPELINE_CACHE_GUARD=1',
                       str(source),'-o',str(exe)],check=True, env=compiler_env)
        subprocess.run([str(exe),str(out)],check=True, env=compiler_env)
print('N56_VENDOR_NATIVE_ATOMIC_OWNER_TRUNCATION_GUARD_PASS')
