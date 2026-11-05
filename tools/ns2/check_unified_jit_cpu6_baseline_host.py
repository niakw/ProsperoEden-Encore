#!/usr/bin/env python3
"""Exact A32/A64 JIT retry baseline contract shared by 4- and 6-core guests.

Host-only UBSan witness against the production header. No console build.
"""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[2]
HEADER=ROOT/'headless/jit_memory_policy.h'
assert HEADER.is_file()
for bits in (32,64):
    for profile in ('normal','dev'):
        source=(ROOT/'vendor/encore-active/eden-core/src/core/arm/dynarmic/g11'/
                f'arm_dynarmic_{bits}_native_{profile}.cpp').read_text()
        assert source.count(f'::Eden::JitMemory::A{bits}BaselineBytes(m_core_index)')==1
        assert f'kA{bits}Baseline[m_core_index]' not in source

fixture=r'''
#include <array>
#include <cassert>
#include <cstddef>
#include <cstdio>
#include "jit_memory_policy.h"
int main() {
    using namespace Eden::JitMemory;
    constexpr std::array<std::uint32_t,6> a64{
        256u*kMiB,192u*kMiB,192u*kMiB,16u*kMiB,16u*kMiB,16u*kMiB};
    constexpr std::array<std::uint32_t,6> a32{
        512u*kMiB,64u*kMiB,64u*kMiB,16u*kMiB,16u*kMiB,16u*kMiB};
    for (std::size_t i=0;i<64;++i) {
        const auto a64_expected=i<6 ? a64[i] : 16u*kMiB;
        const auto a32_expected=i<6 ? a32[i] : 16u*kMiB;
        assert(A64BaselineBytes(i)==a64_expected);
        assert(A32BaselineBytes(i)==a32_expected);
        assert(A64CacheBytes(i,A64BaselineBytes(i))==a64_expected);
        assert(A32CacheBytes(i,A32BaselineBytes(i))==a32_expected);
    }
    auto plan=ChooseJitMemoryPlan(false,true,8ull*1024*kMiB);
    ApplyJitMemoryPlan(plan);
    for (std::size_t i=4;i<6;++i) {
        assert(A64CacheBytes(i,A64BaselineBytes(i))==16u*kMiB);
        assert(A32CacheBytes(i,A32BaselineBytes(i))==16u*kMiB);
    }
    for (std::size_t i=0;i<4;++i) {
        assert(A64CacheBytes(i,A64BaselineBytes(i))==plan.a64[i]);
        assert(A32CacheBytes(i,A32BaselineBytes(i))==plan.a32[i]);
    }
    std::puts("UNIFIED_JIT_CPU6_BOUNDED_BASELINES_PASS");
}
'''
compiler=shutil.which('clang++') or shutil.which('g++')
assert compiler
sdk15=Path('/Library/Developer/CommandLineTools/SDKs/MacOSX15.4.sdk')
env=os.environ.copy()
if sdk15.is_dir():env['SDKROOT']=str(sdk15)
with tempfile.TemporaryDirectory(prefix='encore-unified-jit6-') as folder:
    source=Path(folder)/'test.cpp';source.write_text(fixture)
    for optimization in (0,2):
        binary=Path(folder)/f'jit6-O{optimization}'
        command=[compiler,'-std=c++20',f'-O{optimization}',
                 '-Wall','-Wextra','-Werror','-pedantic',
                 '-fsanitize=undefined','-fno-sanitize-recover=all',
                 '-I'+str(ROOT/'headless'),str(source),'-o',str(binary)]
        result=subprocess.run(command,capture_output=True,text=True,env=env,timeout=60)
        assert result.returncode==0,result.stderr[-4000:]
        executed=subprocess.run([str(binary)],capture_output=True,text=True,env=env,timeout=12)
        assert executed.returncode==0,executed.stderr[-4000:]
        assert 'UNIFIED_JIT_CPU6_BOUNDED_BASELINES_PASS' in executed.stdout
        print('UNIFIED_JIT_CPU6_REAL_POLICY_UBSAN_PASS',f'O{optimization}',flush=True)
