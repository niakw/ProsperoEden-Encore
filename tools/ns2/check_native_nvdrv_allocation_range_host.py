#!/usr/bin/env python3
"""P1.2/NS2 NVDRV: real fixed/remap allocation owner + C++ range oracle."""
import os
from pathlib import Path
import subprocess
import tempfile

root = Path(__file__).resolve().parents[2]
vendor = root / "vendor/encore-active/eden/src_as"
header = vendor / "core/hle/service/nvdrv/devices/native_gpu_allocation_range.h"
source = (vendor / "core/hle/service/nvdrv/devices/nvhost_as_gpu.cpp").read_text()
assert header.is_file()
assert 'native_gpu_allocation_range.h' in source
assert source.count("NativeGpuAllocation::FindContaining(") == 2
assert "alloc-- == allocation_map.begin()" not in source
assert "if (alloc == allocation_map.end())" in source
assert "bytes > gpu_limit - address" in header.read_text()
assert "bytes > it->second.size - offset" in header.read_text()
assert "it == allocations.begin()" in header.read_text()
assert "ContainsSubrange(" in header.read_text()

# The research 4-KiB GPU owner can outlive its GMMU (session teardown /
# invalidated address space). A VM initialised bit is NOT evidence of a
# still-bound GMMU. The lifetime gate must precede all side effects.
for entrypoint in (
    "MapNative4K", "MapNativeImage", "ReserveNativeSparse4K",
    "RemapNativeSparse", "ReleaseNativeSparse4K",
    "UnmapNative4K", "ModifyNativeKind",
):
    marker = "NvResult nvhost_as_gpu::" + entrypoint + "("
    assert source.count(marker) == 1, ("Missing native GPU owner", entrypoint)
    body = source.split(marker, 1)[1].split("\nNvResult nvhost_as_gpu::", 1)[0]
    gate = body.find("!vm.initialised || !gmmu")
    assert gate >= 0, ("Native GMMU can be dereferenced without an owner", entrypoint)
    lock = body.find("const std::scoped_lock lock{mutex};")
    assert lock >= 0 and lock < gate, ("Native GMMU check must hold AS mutex", entrypoint)
    for mutation in ("gmmu->", "vm.small_page_allocator->AllocateFixed(",
                     "nvmap.PinHandle(", "FreeMappingLocked("):
        first = body.find(mutation)
        assert first == -1 or gate < first, (
            "Native GMMU lifetime gate must precede side effects",
            entrypoint, mutation)
remap = source.split("NvResult nvhost_as_gpu::MapBufferEx(", 1)[1].split(
    "NvResult nvhost_as_gpu::UnmapBuffer(", 1)[0]
assert remap.index("NativeGpuAllocation::ContainsSubrange(handle->orig_size") < remap.index(
    "nvmap.PinHandle(params.handle, false)")
assert remap.index("fixed_alloc = NativeGpuAllocation::FindContaining(") < remap.index(
    "nvmap.PinHandle(params.handle, false)")
assert "nvmap.UnpinHandle(params.handle); // Allocation failed after NvMap pin." in remap
assert "NativeGpuAllocation::ContainsSubrange(" in remap.split(
    "auto handle{nvmap.GetHandle(params.handle)};", 1)[0]

# Exercise both actual driver methods, not a parallel implementation of
# their retirement logic. Inject allocator failure after GMMU mutation.
release_begin = "NvResult nvhost_as_gpu::ReleaseNativeSparse4K("
release_end = "NvResult nvhost_as_gpu::ModifyNativeKind("
assert source.count(release_begin) == source.count(release_end) == 1
retirement = release_begin + source.split(release_begin, 1)[1].split(release_end, 1)[0]
retirement_fixture = r'''
#include <cassert>
#include <cstdint>
#include <limits>
#include <map>
#include <mutex>
#include <new>
#include <set>
#include <vector>
using u32=std::uint32_t; using u64=std::uint64_t; using s64=std::int64_t;
enum class NvResult {Success,BadParameter,InvalidState,InsufficientMemory,BadValue};
struct NativeSparseRange {u64 address,size;u32 handle;u64 offset;};
struct NativeSparseMappingTable {
    bool fail{},mapped{true};
    void Replace(NativeSparseRange){if(fail)throw std::bad_alloc{};mapped=false;}
    std::set<u32> ReferencedHandles()const{return {2};}
};
struct Gmmu {
    bool fail{};unsigned calls{};
    void Unmap(u64,u64){++calls;if(fail)throw std::bad_alloc{};}
};
struct Alloc {
    bool fail{};unsigned calls{};
    void Free(u32,u32){++calls;if(fail)throw std::bad_alloc{};}
};
struct NvMap {
    Gmmu* g{};Alloc* a{};unsigned unpins{};
    void UnpinHandle(u32){assert(g->calls==1 && a->calls==1);++unpins;}
};
struct nvhost_as_gpu {
    struct VM {
        static constexpr u64 YUZU_PAGESIZE=4096;
        static constexpr u32 PAGE_SIZE_BITS=12;
        bool initialised{true};Alloc* small_page_allocator{};
    } vm;
    struct Mapping {u64 size;u32 handle;bool fixed,sparse_alloc;};
    struct Allocation {std::vector<u64> mappings;u64 size;u32 page_size;bool sparse,big_pages;};
    struct Region {u64 size;};
    std::map<u64,Mapping> mapping_map;
    std::map<u64,Allocation> allocation_map;
    std::map<u64,Region> native_sparse_regions;
    std::map<u32,u64> native_sparse_pins;
    std::set<s64> map_buffer_offsets;
    NativeSparseMappingTable native_sparse_mappings;
    bool native_sparse_poisoned{};
    std::mutex mutex;
    Gmmu gpu;Alloc allocator;Gmmu* gmmu{&gpu};NvMap nvmap{&gpu,&allocator};
    explicit nvhost_as_gpu(bool sparse) {
        vm.small_page_allocator=&allocator;
        allocation_map.emplace(0x20000,Allocation{
            sparse?std::vector<u64>{}:std::vector<u64>{0x20000},0x2000,4096,sparse,false});
        if(sparse){
            native_sparse_regions.emplace(0x20000,Region{0x2000});
            native_sparse_pins={{1,0x40000},{2,0x50000}};
        }else{
            mapping_map.emplace(0x20000,Mapping{0x2000,1,true,false});
            map_buffer_offsets.insert(0x20000);
        }
    }
    NvResult ReleaseNativeSparse4K(u64,u64);
    NvResult UnmapNative4K(u64,u64);
};
__RETIREMENT__
int main(){
    for(bool sparse:{false,true})for(unsigned failure=0;failure<3;++failure){
        nvhost_as_gpu as{sparse};as.gpu.fail=failure==1;as.allocator.fail=failure==2;
        auto run=[&]{return sparse?as.ReleaseNativeSparse4K(0x20000,0x2000)
                                  :as.UnmapNative4K(0x20000,0x2000);};
        assert(run()==(failure?NvResult::InvalidState:NvResult::Success));
        assert(as.gpu.calls==1 && as.allocator.calls==(failure==1?0U:1U));
        assert(as.native_sparse_poisoned==(failure!=0));
        assert(as.nvmap.unpins==(failure?0U:1U));
        assert(as.allocation_map.size()==(failure?1U:0U));
        if(sparse){
            assert(as.native_sparse_regions.size()==(failure?1U:0U));
            assert(as.native_sparse_pins.size()==(failure?2U:1U));
            assert(as.native_sparse_pins.contains(2));
            assert(as.native_sparse_mappings.mapped==(failure!=0));
        }else{
            assert(as.mapping_map.size()==(failure?1U:0U));
            assert(as.map_buffer_offsets.size()==(failure?1U:0U));
        }
        assert(run()!=NvResult::Success);
        assert(as.gpu.calls==1 && as.nvmap.unpins==(failure?0U:1U));
    }
    nvhost_as_gpu as{true};
    as.native_sparse_mappings.fail=true;
    assert(as.ReleaseNativeSparse4K(0x20000,0x2000)==NvResult::InsufficientMemory);
    assert(!as.native_sparse_poisoned && !as.gpu.calls && !as.allocator.calls &&
           !as.nvmap.unpins && as.native_sparse_pins.size()==2);
    as.native_sparse_mappings.fail=false;
    assert(as.ReleaseNativeSparse4K(0x20000,0x2000)==NvResult::Success);
}
'''.replace("__RETIREMENT__", retirement)

env = os.environ.copy()
sdk = Path("/Library/Developer/CommandLineTools/SDKs/MacOSX15.4.sdk")
if sdk.is_dir():
    env["SDKROOT"] = str(sdk)
with tempfile.TemporaryDirectory(prefix="encore-nvdrv-range-") as tmp:
    retirement_cpp = Path(tmp) / "native-retirement.cpp"
    retirement_cpp.write_text(retirement_fixture)
    for compiler in ("clang++", "g++"):
        for opt in ("-O0", "-O2"):
            exe = Path(tmp) / f"allocation-{compiler}-{opt}"
            args = [compiler, "-std=c++20", opt, "-Wall", "-Wextra", "-Werror",
                    "-fsanitize=address,undefined", "-fno-sanitize-recover=all",
                    "-I", str(vendor),
                    str(root / "tools/ns2/test_native_nvdrv_allocation_range.cpp"),
                    "-o", str(exe)]
            result = subprocess.run(args, env=env, capture_output=True, text=True, timeout=60)
            assert result.returncode == 0, (compiler, opt, result.stderr[-5000:])
            run_env = {**env, "ASAN_OPTIONS": "detect_leaks=0", "UBSAN_OPTIONS": "halt_on_error=1"}
            result = subprocess.run([str(exe)], env=run_env,
                                    capture_output=True, text=True, timeout=30)
            assert result.returncode == 0, (compiler, opt, result.stderr[-5000:])
            assert "P1_2_NVDRV_ALLOCATION_RANGE_HOST_PASS" in result.stdout
            retirement_exe = Path(tmp) / f"retirement-{compiler}-{opt}"
            retirement_args = [compiler, "-std=c++20", opt, "-Wall", "-Wextra",
                               "-Werror", "-fsanitize=undefined", "-fno-sanitize-recover=all",
                               str(retirement_cpp), "-o", str(retirement_exe)]
            result = subprocess.run(retirement_args, env=env, capture_output=True,
                                    text=True, timeout=60)
            assert result.returncode == 0, (compiler, opt, result.stderr[-5000:])
            result = subprocess.run([str(retirement_exe)], env=run_env,
                                    capture_output=True, text=True, timeout=30)
            assert result.returncode == 0, (compiler, opt, result.stderr[-5000:])
            print(f"NS2_NATIVE_213_215_RETIREMENT_PASS compiler={compiler} opt={opt}")
            print(f"P1_2_NVDRV_RANGE_PASS compiler={compiler} opt={opt} "
                  "before_begin=guarded overflow=guarded zero=refused "
                  "source_owners=2 ASAN_UBSAN=pass")
