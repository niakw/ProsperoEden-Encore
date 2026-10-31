#!/usr/bin/env python3
"""N56: source-bound PS5 Vulkan pipeline cache short-header guard, Clang/GCC."""
from pathlib import Path
import subprocess
import tempfile
ROOT=Path(__file__).resolve().parents[2]
ORIG=ROOT/'vendor/encore-active/eden-vulkan/vk_pipeline_cache_cost.cpp'
CMAKE=(ROOT/'headless/CMakeLists.txt').read_text()
before="        u32 cache_version;\n        file.read(magic_number.data(), magic_number.size())"
after="        u32 cache_version;\n        // N56: reject truncated (including failed tellg) Vulkan driver caches\n        // before reading their header or subtracting a size_t header length.\n        if (end < std::streampos{static_cast<std::streamoff>(\n                      magic_number.size() + sizeof(cache_version))}) {\n            file.close();\n            LOG_WARNING(Common_Filesystem, \"Short Vulkan driver cache; rebuilding fresh\");\n            Common::FS::RemoveFile(filename);\n            return create_pipeline_cache(0, nullptr);\n        }\n        file.read(magic_number.data(), magic_number.size())"
original=ORIG.read_text()
assert original.count(before)==1,'PS5 cache owner drift'
assert 'Saved PS5 driver pipeline cache atomically' in original
expected=original.replace(before,after)
assert 'EDEN_NS2_EGLANTINE_PIPELINE_CACHE_EXPERIMENTAL OR' in CMAKE
assert 'list(REMOVE_ITEM video_sources "${eden_ns2_pipeline_owner}")' in CMAKE
assert 'NOT EDEN_NS2_METADATA_EXPERIMENTAL OR EDEN_FINAL_RELEASE_PROFILE' in CMAKE
with tempfile.TemporaryDirectory(prefix='n56-native-cache-') as td:
    out=Path(td)
    generated=out/'vk_pipeline_cache.cpp'
    subprocess.run(['cmake','-DINPUT='+str(ORIG),'-DOUTPUT='+str(generated),
          '-P',str(ROOT/'tools/ns2/prepare_egl_pipeline_cache.cmake')],check=True)
    assert generated.read_text()==expected,'PS5 native cache owner parity failed'
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
                       str(source),'-o',str(exe)],check=True)
        subprocess.run([str(exe),str(out)],check=True)
print('N56_PS5_VULKAN_ATOMIC_OWNER_TRUNCATION_GUARD_PASS')
