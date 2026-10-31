#!/usr/bin/env python3
"""Compile the native, NS1/NS2 shared GPU pool memory policy (Clang/GCC)."""
from pathlib import Path
import subprocess
import tempfile
ROOT=Path(__file__).resolve().parents[2]
native=ROOT/"vendor/encore-active/eden-vulkan/include"
header=native/"video_core/renderer_vulkan/vk_shared_gpu_budget.h"
s=header.read_text()
assert "namespace Eden::Vulkan::MemoryPolicy" in s
assert "Switch2" not in s and "FC27" not in s
assert "shared_pool_used" in s
assert "reliable_shared_pool_usage" in s
program=r"""
#include <cassert>
#include <cstdio>
#include <cstdint>
#include "video_core/renderer_vulkan/vk_shared_gpu_budget.h"
using namespace Eden::Vulkan::MemoryPolicy;
constexpr std::uint64_t GiB=1ULL<<30;
constexpr std::uint64_t MiB=1ULL<<20;
int main() {
 // No pool data means do not invent memory usage or reject regular images.
 constexpr auto unknown=SparseBackingBudget(6*GiB, 5*GiB, false, 384*MiB);
 static_assert(!unknown.measured&&unknown.max_new_bytes==384*MiB);
 constexpr auto standard=SparseBackingBudget(12*GiB, 6*GiB, true, 768*MiB);
 static_assert(standard.measured && standard.headroom_bytes==GiB);
 static_assert(standard.max_new_bytes==768*MiB);
 constexpr auto short_pool=SparseBackingBudget(6*GiB, 6*GiB-768*MiB-2*MiB,
                                               true,384*MiB);
 static_assert(short_pool.measured&&short_pool.headroom_bytes==768*MiB);
 static_assert(short_pool.max_new_bytes==2*MiB);
 constexpr auto exhausted=SparseBackingBudget(6*GiB,6*GiB-768*MiB,
                                               true,384*MiB);
 static_assert(exhausted.max_new_bytes==0);
 constexpr auto corrupt=SparseBackingBudget(6*GiB,7*GiB,true,384*MiB);
 static_assert(corrupt.measured&&corrupt.max_new_bytes==0);
 constexpr auto no_space=SparseBackingBudget(0,0,true,384*MiB);
 static_assert(no_space.max_new_bytes==0);
 constexpr auto small=SparseBackingBudget(2*GiB,1*GiB,true,384*MiB);
 static_assert(small.headroom_bytes==256*MiB);
 constexpr auto untouched=SparseBackingBudget(12*GiB,10*GiB,true,768*MiB);
 static_assert(untouched.max_new_bytes==768*MiB);
 std::puts("N75_SHARED_NS1_NS2_GPU_POOL_BUDGET_PASS");
}
"""
with tempfile.TemporaryDirectory(prefix="n75-shared-gpu-pool-") as tmp:
    d=Path(tmp);src=d/"budget.cpp";src.write_text(program)
    for compiler in ("clang++","g++"):
        exe=d/compiler.replace("+","p")
        subprocess.run([compiler,"-std=c++20","-O2","-Wall","-Wextra",
                        "-Werror","-fsanitize=undefined",
                        "-fno-sanitize-recover=all",
                        "-I",str(native),str(src),"-o",str(exe)],check=True)
        subprocess.run([str(exe)],check=True)
print("N75_SHARED_GPU_BUDGET_VENDOR_CLANG_GCC_UBSAN_PASS")
