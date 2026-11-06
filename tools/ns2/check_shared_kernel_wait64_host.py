#!/usr/bin/env python3
"""P1.3: execute the real dual-generation address-arbiter compare under UBSan.

The test extracts the maintained kernel's actual 32/64-bit read/compare,
keeps the pinned 32-bit policy, compiles the two complete kernel owners and
the selected SVC dispatcher. Does not simulate scheduling, PS5 or game boot.
"""
from pathlib import Path
import difflib
import os
import platform
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT/'vendor/sources/eden/src/core/hle/kernel'
KERNEL = ROOT/'vendor/encore-active/ns2-runtime/kernel_wait64/core/hle/kernel'
SVC_GPU = ROOT/'vendor/encore-active/ns2-runtime/gpu_access_svc/core/hle/kernel'
SOURCE = KERNEL/'k_address_arbiter.cpp'
ARB_SVC = KERNEL/'svc/svc_address_arbiter.cpp'
NATIVE_SVC = ROOT/'vendor/encore-active/ns2-runtime/kernel/core/hle/kernel/svc.cpp'
CMAKE = (ROOT/'headless/CMakeLists.txt').read_text()

for name in ('k_address_arbiter.h','k_address_arbiter.cpp','k_process.h',
             'svc.h','svc/svc_address_arbiter.cpp'):
    original = (BASE/name).read_text().splitlines(keepends=True)
    reviewed = (KERNEL/name).read_text().splitlines(keepends=True)
    edits=list(difflib.unified_diff(original,reviewed))
    if not edits:
        # The pinned kernel already includes some reviewed 64-bit ABI
        # declarations. Byte-identical source is the strongest baseline
        # parity result, not an absent implementation. The per-file value
        # signatures and compiled comparisons are checked below.
        assert original == reviewed, ("Pinned kernel parity drift", name)
    else:
        assert 0 < len(edits) < 105, (name,len(edits))
assert 'set(EDEN_SHARED_NS2_WAIT64 ON)' in CMAKE
assert 'if(EDEN_SHARED_NS2_GPU_ACCESS_SVC)' in CMAKE
for path in ('k_address_arbiter.cpp','svc/svc_address_arbiter.cpp'):
    assert f'"hle/kernel/{path}"' in CMAKE, path
assert 'target_include_directories(core BEFORE PUBLIC "${EDEN_NS2_WAIT64_ROOT}")' in CMAKE
assert 'target_include_directories(video_core BEFORE PRIVATE "${EDEN_NS2_WAIT64_ROOT}")' in CMAKE

assert 'WaitIfEqual64 = 3' in (SVC_GPU/'svc_types.h').read_text()
for filename in (SVC_GPU/'svc.cpp', NATIVE_SVC):
    s=filename.read_text();start=s.index('static void SvcWrap_WaitForAddress64(Core::System& system')
    end=s.index('\n}', start)
    wrapper=s[start:end]
    assert 'int64_t value = Convert<int64_t>(GetArg64(args, 2));' in wrapper
    assert 'int32_t value = Convert<int32_t>(GetArg64(args, 2));' not in wrapper
    wrapper32=s[s.index('static void SvcWrap_WaitForAddress64From32'):s.index('\n}',s.index('static void SvcWrap_WaitForAddress64From32'))]
    assert 'int32_t value = Convert<int32_t>(GetArg32(args, 2));' in wrapper32

for name in ('svc.h','k_process.h','k_address_arbiter.h'):
    assert 's64 value' in (KERNEL/name).read_text() or 'int64_t value' in (KERNEL/name).read_text()

source=SOURCE.read_text()
start=source.index('        s64 user_value{};')
end=source.index('        // Check that the timeout is non-zero.',start)
read_compare=source[start:end]
assert 'GetCurrentMemory(system.Kernel())' in read_compare
assert 'memory.IsValidVirtualAddressRange(addr, sizeof(s64))' in read_compare
assert 'static_cast<s64>(memory.Read64(addr))' in read_compare
assert 'ReadFromUser(system.Kernel(), std::addressof(low_word), addr)' in read_compare
assert 'value != user_value' in read_compare
svc_source=ARB_SVC.read_text()
start=svc_source.index('constexpr bool IsValidArbitrationType(')
end=svc_source.index('\n}',start)+2
valid_type=svc_source[start:end]
assert 'WaitIfEqual64' in valid_type
alignment='const size_t alignment = arb_type == ArbitrationType::WaitIfEqual64 ? sizeof(s64) : sizeof(s32);'
assert alignment in svc_source

# Exercise the actual CMake selector, rather than inferring target changes
# from the words inside its conditional source-selection block.
selector = 'set(EDEN_SHARED_NS2_WAIT64 OFF)' + CMAKE.split(
    'set(EDEN_SHARED_NS2_WAIT64 OFF)', 1)[1].split('# N52:', 1)[0]
with tempfile.TemporaryDirectory(prefix='encore-wait64-cmake-') as cmake_tmp:
    cmake_root=Path(cmake_tmp)
    for selected in (False,True):
        project = cmake_root/('on' if selected else 'off')
        project.mkdir()
        for rel in ('hle/kernel/k_address_arbiter.cpp',
                    'hle/kernel/svc/svc_address_arbiter.cpp', 'dummy.cpp'):
            actual_source=project/rel
            actual_source.parent.mkdir(parents=True,exist_ok=True)
            actual_source.write_text('int probe_%s = 0;\n' % len(rel))
        probe = f'''cmake_minimum_required(VERSION 3.20)
project(wait64_select LANGUAGES CXX)
set(PORT_ROOT "{ROOT.as_posix()}")
set(EDEN_SHARED_NS2_GPU_ACCESS_SVC {"ON" if selected else "OFF"})
add_library(core STATIC hle/kernel/k_address_arbiter.cpp
                        hle/kernel/svc/svc_address_arbiter.cpp)
add_library(video_core STATIC dummy.cpp)
'''
        probe += selector
        probe += '''
get_target_property(actual core SOURCES)
get_target_property(exposed core INTERFACE_INCLUDE_DIRECTORIES)
message(STATUS "WAIT64_SELECTED=${EDEN_SHARED_NS2_WAIT64}")
message(STATUS "WAIT64_SOURCES=${actual}")
message(STATUS "WAIT64_INCLUDES=${exposed}")
'''
        (project/'CMakeLists.txt').write_text(probe)
        sdk_arg = (['-DCMAKE_OSX_SYSROOT=/Library/Developer/CommandLineTools/SDKs/MacOSX15.4.sdk']
                   if platform.system() == 'Darwin' and
                   Path('/Library/Developer/CommandLineTools/SDKs/MacOSX15.4.sdk').is_dir()
                   else [])
        result = subprocess.run(['cmake','-S',str(project),'-B',str(project/'build'),
                                 *sdk_arg], capture_output=True,text=True,timeout=40)
        assert result.returncode==0,result.stderr[-4000:]
        assert ('WAIT64_SELECTED=ON' if selected else 'WAIT64_SELECTED=OFF') in result.stdout
        chosen = str(KERNEL/'k_address_arbiter.cpp')
        assert (chosen in result.stdout) == selected, result.stdout[-1600:]
        print('P1_3_KERNEL_WAIT64_CMAKE_OWNER_PASS',
              'enabled' if selected else 'disabled',flush=True)

unit=r'''
#include <array>
#include <cassert>
#include <cstdint>
#include <cstring>
#include <cstdio>
#include <memory>
using u64=std::uint64_t;
using u32=std::uint32_t;
using s64=std::int64_t;
using s32=std::int32_t;
namespace Svc {
enum class ArbitrationType : u32 {
    WaitIfLessThan=0,DecrementAndWaitIfLessThan=1,WaitIfEqual=2,WaitIfEqual64=3
};
}
__VALID_ENUM__
using ArbitrationType=Svc::ArbitrationType;
static bool AlignForType(u64 addr, ArbitrationType arb_type) {
    __REAL_ALIGNMENT__
    return (addr % alignment)==0;
}
enum Result { Ok, ResultInvalidCurrentMemory, ResultInvalidState };
#define R_THROW(error) throw (error)
struct Memory {
    static constexpr u64 base=0x1000;
    std::array<std::uint8_t,16> data{};
    bool IsValidVirtualAddressRange(u64 addr,u64 bytes) const {
        return addr>=base && addr-base<=data.size() && bytes<=data.size()-(addr-base);
    }
    u64 Read64(u64 addr) const {
        u64 word{};
        assert(IsValidVirtualAddressRange(addr,8));
        std::memcpy(&word,data.data()+addr-base,8);
        return word;
    }
    u32 Read32(u64 addr) const {
        u32 word{};
        assert(IsValidVirtualAddressRange(addr,4));
        std::memcpy(&word,data.data()+addr-base,4);
        return word;
    }
};
struct KernelCore { Memory memory; };
struct System {KernelCore kernel;KernelCore& Kernel(){return kernel;}};
static Memory& GetCurrentMemory(KernelCore& kernel) {return kernel.memory;}
static bool ReadFromUser(KernelCore& kernel,s32* output,u64 addr) {
    if (!kernel.memory.IsValidVirtualAddressRange(addr,4))return false;
    *output=static_cast<s32>(kernel.memory.Read32(addr));
    return true;
}
struct Sleep { unsigned cancels{};void CancelSleep(){++cancels;} };
struct Arbiter {
    System system;
    Result Compare(u64 addr,s64 value,bool is_64_bit) {
        Sleep slp;
        try {
__REAL_COMPARE__
            return Ok;
        } catch(Result error) {
            assert(slp.cancels==1);
            return error;
        }
    }
};
int main() {
    assert(IsValidArbitrationType(ArbitrationType::WaitIfLessThan));
    assert(IsValidArbitrationType(ArbitrationType::WaitIfEqual));
    assert(IsValidArbitrationType(ArbitrationType::WaitIfEqual64));
    assert(!IsValidArbitrationType(static_cast<ArbitrationType>(4)));
    assert(AlignForType(0x1004,ArbitrationType::WaitIfEqual));
    assert(!AlignForType(0x1004,ArbitrationType::WaitIfEqual64));
    assert(AlignForType(0x1008,ArbitrationType::WaitIfEqual64));
    Arbiter a;
    const u64 wide=0x12345678abcdef00ULL;
    std::memcpy(a.system.kernel.memory.data.data(),&wide,8);
    const s64 exact=static_cast<s64>(wide);
    const s32 low=static_cast<s32>(wide);
    assert(a.Compare(0x1000,exact,true)==Ok);
    assert(a.Compare(0x1000,static_cast<s64>(static_cast<u32>(wide)),true)==ResultInvalidState);
    assert(a.Compare(0x1000,static_cast<s64>(low),false)==Ok);
    assert(a.Compare(0x1000,static_cast<s64>(low)+1,false)==ResultInvalidState);
    assert(a.Compare(0x1000,exact+1,true)==ResultInvalidState);
    assert(a.Compare(0x1010,exact,true)==ResultInvalidCurrentMemory);
    assert(a.Compare(0x1010,static_cast<s64>(low),false)==ResultInvalidCurrentMemory);
    // The current 32-bit legacy path is sign-extended from a signed s32.
    const u64 all_ones=~u64{0};
    std::memcpy(a.system.kernel.memory.data.data()+8,&all_ones,8);
    assert(a.Compare(0x1008,-1,true)==Ok);
    assert(a.Compare(0x1008,-1,false)==Ok);
    assert(a.Compare(0x1008,0xffffffffULL,true)==ResultInvalidState);
    std::puts("P1_3_REAL_KERNEL_WAIT64_COMPARE_PASS");
}
'''
unit=unit.replace('__VALID_ENUM__',valid_type).replace('__REAL_ALIGNMENT__',alignment).replace('__REAL_COMPARE__',read_compare)


def main() -> None:
    deps=ROOT/'vendor/sources/eden-cpm'
    sdk26=Path('/Library/Developer/CommandLineTools/SDKs/MacOSX26.5.sdk')
    sdk15=Path('/Library/Developer/CommandLineTools/SDKs/MacOSX15.4.sdk')
    env=os.environ.copy()
    if sdk15.is_dir():env['SDKROOT']=str(sdk15)
    includes=[KERNEL.parents[2],SVC_GPU.parents[2],ROOT/'vendor/encore-active/ns2-helpers/include',ROOT/'vendor/sources/eden/src',
              deps/'fmt/12.1.0/include']+list((deps/'boost/boost-1.90.0/libs').glob('*/include'))
    actual=[KERNEL/'k_address_arbiter.cpp',ARB_SVC,SVC_GPU/'svc.cpp']
    compilers=list(dict.fromkeys(c for c in (shutil.which('clang++'),shutil.which('g++')) if c))
    assert compilers
    with tempfile.TemporaryDirectory(prefix='encore-kernel-wait64-') as scratch:
        harness=Path(scratch)/'kernel.cpp';harness.write_text(unit)
        for compiler in compilers:
            for opt in (0,2):
                exe=Path(scratch)/f'{Path(compiler).name}-{opt}'
                cmd=[compiler,'-std=c++20',f'-O{opt}','-Wall','-Wextra','-Werror',
                     '-fsanitize=undefined','-fno-sanitize-recover=all',str(harness),'-o',str(exe)]
                built=subprocess.run(cmd,env=env,text=True,capture_output=True,timeout=40)
                assert built.returncode==0,built.stderr[-3800:]
                run=subprocess.run([str(exe)],env=env,text=True,capture_output=True,timeout=15)
                assert run.returncode==0,run.stderr[-3800:]
                assert 'P1_3_REAL_KERNEL_WAIT64_COMPARE_PASS' in run.stdout
                print('P1_3_KERNEL_WAIT64_HARNESS_PASS',Path(compiler).name,f'O{opt}',flush=True)
        # Also parse complete kernel owners with the actual override ABI.
        clang=shutil.which('clang++')
        if clang and sdk26.is_dir():
            flags=[clang,'-std=c++20','-fsyntax-only','-DFMT_HEADER_ONLY',
                   '-target','arm64-apple-macos15','-nostdinc++','-isystem',
                   str(sdk26/'usr/include/c++/v1'),
                   *[f'-I{x}' for x in includes]]
            for source in actual:
                done=subprocess.run(flags+[str(source)],env=env,text=True,
                                    capture_output=True,timeout=80)
                assert done.returncode==0,(source,done.stderr[-3600:])
                print('P1_3_KERNEL_WAIT64_REAL_TU_SYNTAX_PASS',source.name,flush=True)

if __name__=='__main__':main()
