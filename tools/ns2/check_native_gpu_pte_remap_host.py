#!/usr/bin/env python3
"""P1.2: exercise actual shared GPU small/big PTE Map/Unmap functions.

The previous implementation notified the rasterizer only if PTE *status*
changed. Mapped->Mapped to a different physical page silently reused stale
texture/buffer cache entries. This test extracts the real source methods and
executes both the shipping and research-batched notification paths.
"""
from pathlib import Path
import os
import subprocess
import tempfile

root = Path(__file__).resolve().parents[2]
owner = root / "vendor/encore-active/eden-core/src/video_core/memory_manager.cpp"
source = owner.read_text()
guard = root / "vendor/encore-active/eden-core/src/video_core/native_gpu_page_remap.h"
assert guard.is_file()
assert '#include "native_gpu_page_remap.h"' in source
assert source.count("Eden::GpuMemory::NeedsRasterizerUnmap(") == 2
assert source.count("changed_runs.Record(current_gpu_addr, mapping_changed, notify_changed);") == 2
assert source.count("if (mapping_changed) notify_changed(current_gpu_addr,") == 2
assert source.count("All old mappings have been evicted") == 1
assert source.count("Commit big-page backing only after the old cache owner") == 1
assert source.count("gpu_page_table_revision.fetch_add(1, std::memory_order_release)") == 4
assert source.count("std::atomic<u64> gpu_page_table_revision{1};") == 1

def extract(begin: str, end: str) -> str:
    assert source.count(begin) == 1 and source.count(end) == 1
    start = source.index(begin)
    return source[start:source.index(end, start)]

small = extract("GPUVAddr MemoryManager::PageTableOp(", "\nGPUVAddr MemoryManager::BigPageTableOp(")
big = extract("GPUVAddr MemoryManager::BigPageTableOp(", "\nvoid MemoryManager::BindRasterizer(")

fixture = r"""
#include <array>
#include <atomic>
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <functional>
#include <mutex>
#include <tuple>
#include <vector>
#include "native_gpu_page_remap.h"
#include "video_core/ns2_egl_gpu_range_batch.h"
using u8=std::uint8_t;
using u32=std::uint32_t;
using u64=std::uint64_t;
using GPUVAddr=u64;
using DAddr=u64;
// Use the SAME revision declaration as the real shared memory manager.
// This fixture extracts real PageTableOp/BigPageTableOp bodies unchanged.
std::atomic<u64> gpu_page_table_revision{1};
enum class PTEKind{INVALID,Color};
struct SmallTable {
    std::array<u32, 256> entries{};
    void ReserveRange(u64, size_t) {}
    u32& operator[](size_t x) { return entries.at(x); }
    u32 operator[](size_t x) const { return entries.at(x); }
};
struct BigTable {
    std::array<u32, 256> entries{};
    void Set(size_t x,u32 value) { entries.at(x)=value; }
    u32 operator[](size_t x) const { return entries.at(x); }
};
struct Rasterizer {
    std::vector<std::pair<u64,u64>> events;
    std::function<void(u64,u64)> before_unmap;
    void ModifyGPUMemory(size_t,u64 address,u64 bytes) {
        if (before_unmap) before_unmap(address,bytes);
        events.emplace_back(address,bytes);
    }
};
struct Backing {
    std::array<u8,1<<20> data{};
    template<class T> T* GetPointer(DAddr a) {
        return reinterpret_cast<T*>(data.data() + (a % data.size()));
    }
};
struct KindMap {void Map(u64,u64,PTEKind){}};
class MemoryManager {
public:
    enum class EntryType {Free,Reserved,Mapped};
    static constexpr u64 page_size=4096, big_page_size=16384;
    static constexpr u32 cpu_page_bits=12;
    SmallTable page_table;
    BigTable big_page_table_dev;
    std::array<EntryType,256> small_entries{};
    std::array<EntryType,256> big_entries{};
    Rasterizer recorder;
    Rasterizer* rasterizer=&recorder;
    Backing memory;
    KindMap kind_map;
    std::mutex guard;
    size_t unique_identifier=1;
    EntryType GetEntry(u64 address,bool is_big) const {
        return is_big ? big_entries.at(address/big_page_size)
                      : small_entries.at(address/page_size);
    }
    void SetEntry(u64 address,EntryType next,bool is_big) {
        auto& entries=is_big?big_entries:small_entries;
        entries.at(address/(is_big?big_page_size:page_size))=next;
    }
    size_t PageEntryIndex(u64 address,bool is_big) const {
        return address/(is_big?big_page_size:page_size);
    }
    void SetBigPageContinuous(size_t,bool) {}
    GPUVAddr PageTableOp(GPUVAddr, DAddr, size_t, PTEKind, EntryType);
    GPUVAddr BigPageTableOp(GPUVAddr, DAddr, size_t, PTEKind, EntryType);
};
__SMALL__
__BIG__
static void Same(const std::vector<std::pair<u64,u64>>& got,
                 std::initializer_list<std::pair<u64,u64>> want) {
    const std::vector<std::pair<u64,u64>> expected(want);
    assert(got==expected);
}
int main() {
    using Entry=MemoryManager::EntryType;
    static_assert(Eden::GpuMemory::NeedsRasterizerUnmap(Entry::Free,Entry::Mapped,Entry::Mapped,0,7));
    static_assert(!Eden::GpuMemory::NeedsRasterizerUnmap(Entry::Mapped,Entry::Mapped,Entry::Mapped,7,7));
    static_assert(Eden::GpuMemory::NeedsRasterizerUnmap(Entry::Mapped,Entry::Mapped,Entry::Mapped,7,8));
    static_assert(Eden::GpuMemory::NeedsRasterizerUnmap(Entry::Mapped,Entry::Reserved,Entry::Mapped,7,0));
    static_assert(!Eden::GpuMemory::NeedsRasterizerUnmap(Entry::Reserved,Entry::Reserved,Entry::Mapped,0,0));
    MemoryManager small;
    const u64 base=0x4000;
    auto map_small=[&](u64 at,u64 physical,size_t bytes) {
        small.PageTableOp(at,physical,bytes,PTEKind::Color,Entry::Mapped);
    };
    const auto small_revision_before = gpu_page_table_revision.load();
    map_small(base,0x200000,3*4096);
    assert(gpu_page_table_revision.load() == small_revision_before + 2);
#ifdef EDEN_NS2_GPU_RANGE_BATCH
    Same(small.recorder.events,{{base,3*4096}});
#else
    Same(small.recorder.events,{{base,4096},{base+4096,4096},{base+8192,4096}});
#endif
    small.recorder.events.clear();
    map_small(base,0x200000,3*4096);
    Same(small.recorder.events,{});
    small.recorder.before_unmap=[&](u64,u64) {
        assert(small.GetEntry(base+4096,false)==Entry::Mapped);
        assert(small.page_table[(base+4096)/4096]==0x200000/4096+1);
    };
    map_small(base+4096,0x300000,4096);
    small.recorder.before_unmap={};
    Same(small.recorder.events,{{base+4096,4096}});
    assert(small.page_table[(base+4096)/4096]==0x300000/4096);
    small.recorder.events.clear();
    map_small(base+4096,0x300000,4096);
    Same(small.recorder.events,{});
    small.recorder.before_unmap=[&](u64,u64) {
        assert(small.page_table[base/4096]==0x200000/4096);
        assert(small.page_table[(base+4096)/4096]==0x300000/4096);
        assert(small.page_table[(base+8192)/4096]==0x200000/4096+2);
    };
    map_small(base,0x600000,3*4096);
    small.recorder.before_unmap={};
    small.recorder.events.clear();
    small.recorder.before_unmap=[&](u64,u64) {
        assert(small.GetEntry(base+4096,false)==Entry::Mapped);
        assert(small.page_table[(base+4096)/4096]==0x600000/4096+1);
    };
    small.PageTableOp(base+4096,0,4096,PTEKind::INVALID,Entry::Reserved);
    small.recorder.before_unmap={};
    Same(small.recorder.events,{{base+4096,4096}});
    small.recorder.events.clear();
    small.PageTableOp(base+4096,0,4096,PTEKind::INVALID,Entry::Reserved);
    Same(small.recorder.events,{});

    MemoryManager big;
    const u64 big_base=0x10000;
    auto map_big=[&](u64 at,u64 physical,size_t bytes) {
        big.BigPageTableOp(at,physical,bytes,PTEKind::Color,Entry::Mapped);
    };
    const auto big_revision_before = gpu_page_table_revision.load();
    map_big(big_base,0x400000,2*16384);
    assert(gpu_page_table_revision.load() == big_revision_before + 2);
#ifdef EDEN_NS2_GPU_RANGE_BATCH
    Same(big.recorder.events,{{big_base,2*16384}});
#else
    Same(big.recorder.events,{{big_base,16384},{big_base+16384,16384}});
#endif
    big.recorder.events.clear();
    map_big(big_base,0x400000,2*16384);
    Same(big.recorder.events,{});
    map_big(big_base+16384,0x500000,16384);
    Same(big.recorder.events,{{big_base+16384,16384}});
    assert(big.big_page_table_dev[(big_base+16384)/16384]==0x500000/4096);
    big.recorder.events.clear();
    map_big(big_base+16384,0x500000,16384);
    Same(big.recorder.events,{});
    big.recorder.before_unmap=[&](u64,u64) {
        assert(big.big_page_table_dev[big_base/16384]==0x400000/4096);
        assert(big.big_page_table_dev[(big_base+16384)/16384]==0x500000/4096);
    };
    map_big(big_base,0x700000,2*16384);
    big.recorder.before_unmap={};
    big.recorder.events.clear();
    big.recorder.before_unmap=[&](u64,u64) {
        assert(big.GetEntry(big_base,true)==Entry::Mapped);
        assert(big.GetEntry(big_base+16384,true)==Entry::Mapped);
    };
    big.BigPageTableOp(big_base,0,2*16384,PTEKind::INVALID,Entry::Free);
    big.recorder.before_unmap={};
#ifdef EDEN_NS2_GPU_RANGE_BATCH
    Same(big.recorder.events,{{big_base,2*16384}});
#else
    Same(big.recorder.events,{{big_base,16384},{big_base+16384,16384}});
#endif
    std::puts("P1_2_GPU_REMAP_PTE_INVALIDATION_PASS");
}
""".replace("__SMALL__", small).replace("__BIG__", big)

env = os.environ.copy()
sdk = Path("/Library/Developer/CommandLineTools/SDKs/MacOSX15.4.sdk")
if sdk.is_dir():
    env.setdefault("SDKROOT", str(sdk))
with tempfile.TemporaryDirectory(prefix="eden-guest-gpu-remap-") as temp:
    unit = Path(temp) / "remap.cpp"
    unit.write_text(fixture)
    for compiler in ("clang++","g++"):
        for opt in ("-O0","-O2"):
            for batching in (False,True):
                exe = Path(temp) / f"remap-{compiler}-{opt}-{int(batching)}"
                args=[compiler,"-std=c++20",opt,"-Wall","-Wextra","-Werror",
                      "-fsanitize=undefined","-fno-sanitize-recover=all",
                      "-I",str(guard.parent),
                      "-I",str(root/"vendor/encore-active/ns2-helpers/include")]
                if batching:
                    args.append("-DEDEN_NS2_GPU_RANGE_BATCH=1")
                result=subprocess.run([*args,str(unit),"-o",str(exe)],
                    env=env,capture_output=True,text=True,timeout=55)
                assert result.returncode==0,(compiler,opt,batching,result.stderr[-4000:])
                result=subprocess.run([str(exe)],env=env,capture_output=True,text=True,timeout=20)
                assert result.returncode==0,(compiler,opt,batching,result.stderr[-3000:])
                print(f"P1_2_GPU_PTE_REMAP_PASS compiler={compiler} opt={opt} batch={int(batching)} small=1 big=1 old_backing_verified=1 NS1=preserved")
