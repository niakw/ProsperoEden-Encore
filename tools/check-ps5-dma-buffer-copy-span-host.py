#!/usr/bin/env python3
"""Compile selected native DMA spans and NS1 DMA->TextureCache ownership policy."""
from pathlib import Path
import subprocess
import tempfile
root=Path(__file__).resolve().parents[1]
core=(root/"vendor/encore-active/eden-core/src/video_core/buffer_cache/buffer_cache.h").read_text()
texture=(root/"vendor/encore-active/eden/src/video_core/texture_cache/texture_cache.h").read_text()
active=(root/"vendor/encore-active/eden-vulkan/vulkan_rasterizer.cpp").read_text()
bridge=(root/"vendor/encore-active/eden-core/guest-bridge/vulkan_rasterizer.cpp").read_text()
core_start=("bool BufferCache<P>::DMACopy(\n"
            "    GPUVAddr src_address, GPUVAddr dest_address, u64 amount, bool* gpu_written,\n"
            "    boost::container::small_vector<std::pair<DAddr, size_t>, 4>* gpu_written_dest) {")
end="    const bool source_dirty = IsRegionRegistered(*cpu_src_address, amount);"
block=core[core.index(core_start):core.index(end,core.index(core_start))]
assert "if (amount == 0 || amount > static_cast<u64>(~u32{0}))" in block
assert block.index("if (amount == 0") < block.index("gpu_memory->GpuToCpuAddress(src_address)")
rest=core[core.index(end,core.index(core_start)):core.index("bool BufferCache<P>::DMAClear(",core.index(core_start))]
for pattern in ("FindBuffer(*cpu_src_address, static_cast<u32>(amount), false)",
                "FindBuffer(*cpu_dest_address, static_cast<u32>(amount), false)",
                "SynchronizeBuffer(src_buffer, *cpu_src_address, static_cast<u32>(amount))"):
    assert pattern in rest
assert "*gpu_written_dest = tmp_intervals;" in rest
assert "gpu_written_dest->clear();" in block
wrap_begin="bool AccelerateDMA::BufferCopy(GPUVAddr src_address, GPUVAddr dest_address, u64 amount) {"
wrap_end="\ntemplate <bool IS_IMAGE_UPLOAD>"
def grab(s):
    a=s.index(wrap_begin)
    return s[a:s.index(wrap_end,a)].rstrip()
wrapper=grab(active)
# Native P1 copies track GPU-owned image bytes and lock both cache domains.
# The immutable guest-bridge fallback intentionally does neither.
assert wrapper != grab(bridge)
assert "return buffer_cache.DMACopy(src_address, dest_address, amount);" in grab(bridge)
assert "buffer_cache.DMACopy(src_address, dest_address, amount, &copied_gpu_bytes," in wrapper
assert "&gpu_written_dest" in wrapper
assert "gpu_memory->UsesNativeTiling()" in wrapper
assert "texture_cache.IsGpuMemoryGpuModified(src_address, amount)" in wrapper
assert "texture_cache.WriteGpuMemory(dest_address, amount)" in wrapper
assert "texture_cache.WriteDmaCopy(src_address, dest_address" in wrapper
assert wrapper.index("gpu_memory->UsesNativeTiling()") < wrapper.index("texture_cache.WriteDmaCopy(")
for token in (
    "void TextureCache<P>::WriteDmaCopy(",
    "gpu_written_dest",
    "image.flags & ImageFlagBits::GpuModified",
    "const bool keeps_gpu_contents =",
    "overlaps_unheld(image)",
    "image.flags |= ImageFlagBits::CpuModified;",
    "UntrackImage(image, image_id);",
    "*src > (std::numeric_limits<DAddr>::max)() - size",
    "*dest > (std::numeric_limits<DAddr>::max)() - size",
):
    assert token in texture, token
assert wrapper.index("if (amount == 0") < wrapper.index("std::scoped_lock lock{buffer_cache.mutex, texture_cache.mutex};")
oracle=(root/"tools/prepare-vulkan-port.py").read_text()
assert "empty/oversized copy before the guest buffer-cache mutex" in oracle
contract=(root/"tools/check-ps5-buffer-pages-r437.py").read_text()
assert "# DMA copy's byte count also reaches FindBuffer(u32)" in contract
cmake=(root/"headless/CMakeLists.txt").read_text()
assert 'configure_file("${EDEN_MAINTAINED_BUFFER_PAGES}"' in cmake
preamble=r"""
#include <cassert>
#include <cstdint>
#include <cstddef>
#include <mutex>
#include <optional>
#include <limits>
#include <span>
#include <utility>
#include <vector>
namespace boost::container {
template<class T, std::size_t N> using small_vector = std::vector<T>;
}
using u64 = std::uint64_t;
using u32 = std::uint32_t;
using DAddr = std::uint64_t;
using GPUVAddr = std::uint64_t;
struct Memory {
    unsigned translations=0;
    unsigned contiguous_checks=0;
    bool mapped=true;
    bool aliased_gpu_pages=false;
    bool native_tiling=false;
    bool IsGranularRange(GPUVAddr, u64) { ++contiguous_checks; return mapped; }
    bool UsesNativeTiling() const { return native_tiling; }
    bool IsContinuousRange(GPUVAddr, u64) { ++contiguous_checks; return false; }
    std::optional<DAddr> GpuToCpuAddress(GPUVAddr a) {
        ++translations;
        return aliased_gpu_pages && a==0x4000 ? DAddr{0x1000} : a;
    }
};
template<class P>
struct BufferCache {
    Memory owner;
    Memory* gpu_memory=&owner;
    bool DMACopy(
        GPUVAddr,GPUVAddr,u64,bool* gpu_written = nullptr,
        boost::container::small_vector<std::pair<DAddr, size_t>, 4>* gpu_written_dest = nullptr);
};
"""
source=preamble+ "template<class P>\n"+block+ r"""
    (void)gpu_written;
    (void)gpu_written_dest;
    // The core's range tracking begins after this point. The proof checks
    // that invalid lengths cannot reach it.
    return true;
}
struct CountingMutex {
    std::mutex inner;
    unsigned locks=0;
    void lock(){inner.lock();++locks;}
    bool try_lock(){if(inner.try_lock()){++locks;return true;}return false;}
    void unlock(){inner.unlock();}
};
struct RasterBuffer {
    CountingMutex mutex;
    unsigned copy_calls=0;
    bool gpu_owned=false;
    bool DMACopy(
        GPUVAddr,GPUVAddr,u64,bool* gpu_written,
        boost::container::small_vector<std::pair<DAddr, size_t>, 4>* gpu_written_dest=nullptr) {
        ++copy_calls;
        *gpu_written=gpu_owned;
        if (gpu_written_dest) {
            gpu_written_dest->clear();
            if (gpu_owned) gpu_written_dest->push_back({0x2800,0x800});
        }
        return true;
    }
};
struct RasterTexture {
    CountingMutex mutex;
    bool gpu_modified=false;
    unsigned old_writes=0;
    unsigned dma_writes=0;
    std::size_t last_unheld=0;
    bool IsGpuMemoryGpuModified(GPUVAddr,u64) const{return gpu_modified;}
    void WriteGpuMemory(GPUVAddr,u64){++old_writes;}
    void WriteDmaCopy(GPUVAddr,GPUVAddr,std::size_t,
                      std::span<const std::pair<DAddr,std::size_t>> ranges) {
        ++dma_writes; last_unheld=ranges.size();
    }
};
struct AccelerateDMA {
    RasterBuffer buffer_cache;
    RasterTexture texture_cache;
    Memory native_memory;
    Memory* gpu_memory=&native_memory;
    bool BufferCopy(GPUVAddr,GPUVAddr,u64);
};
""" + wrapper + r"""
int main() {
    constexpr u64 max=static_cast<u64>(std::numeric_limits<u32>::max());
    BufferCache<int> inner;
    AccelerateDMA outer;
    for(const u64 size : {u64{0}, max+1, std::numeric_limits<u64>::max()}) {
        assert(!inner.DMACopy(0x1000,0x2000,size));
        assert(!outer.BufferCopy(0x1000,0x2000,size));
        assert(inner.owner.translations==0);
        assert(inner.owner.contiguous_checks==0);
        assert(outer.buffer_cache.mutex.locks==0);
        assert(outer.texture_cache.mutex.locks==0);
        assert(outer.buffer_cache.copy_calls==0);
    }
    for(const u64 size : {u64{1}, max}) {
        // A valid 4-GiB transfer must not be mistaken for overlapping
        // memory merely because its small test addresses were adjacent.
        const u64 dst = size == max ? 0x200000000ULL : 0x2000ULL;
        assert(inner.DMACopy(0x1000,dst,size));
        assert(outer.BufferCopy(0x1000,dst,size));
    }
    assert(inner.owner.translations==4);
    assert(inner.owner.contiguous_checks==4);
    assert(outer.buffer_cache.mutex.locks==2);
    assert(outer.texture_cache.mutex.locks==2);
    assert(outer.buffer_cache.copy_calls==2);
    assert(outer.texture_cache.dma_writes==2);
    assert(outer.texture_cache.old_writes==0);
    // NS1 forwards exact GPU-owned BufferCache subranges instead of suppressing
    // every destination invalidation for the whole copy.
    outer.buffer_cache.gpu_owned=true;
    assert(outer.BufferCopy(0x1000,0x2000,4096));
    assert(outer.buffer_cache.copy_calls==3);
    assert(outer.texture_cache.dma_writes==3);
    assert(outer.texture_cache.last_unheld==1);
    // Native-tiling/NS2 keeps the prior all-or-nothing policy unchanged.
    outer.native_memory.native_tiling=true;
    outer.buffer_cache.gpu_owned=false;
    outer.texture_cache.gpu_modified=false;
    assert(outer.BufferCopy(0x1000,0x2000,4096));
    assert(outer.texture_cache.old_writes==1);
    outer.buffer_cache.gpu_owned=true;
    assert(outer.BufferCopy(0x1000,0x2000,4096));
    assert(outer.texture_cache.old_writes==1);
    // Both ordinary overlapping ranges and distinct GPU virtual addresses
    // mapped to one physical page must be refused before dirty bookkeeping.
    const auto before_alias_translations=inner.owner.translations;
    assert(!inner.DMACopy(0x1000,0x1004,16));
    inner.owner.aliased_gpu_pages=true;
    assert(!inner.DMACopy(0x1000,0x4000,16));
    assert(inner.owner.translations==before_alias_translations+4);
    assert(inner.DMACopy(0x1000,0x5000,16));
    inner.owner.aliased_gpu_pages=false;
    // Sparse GMMU spans leave the fast path before CPU address translation.
    inner.owner.mapped=false;
    const auto before=inner.owner.translations;
    assert(!inner.DMACopy(0x1000,0x2000,4096));
    assert(inner.owner.translations==before);
}
"""
with tempfile.TemporaryDirectory(prefix="encore-dma-copy-span-") as tmp:
    cpp=Path(tmp)/"main.cpp";cpp.write_text(source)
    for opt in ("-O0","-O2"):
        exe=Path(tmp)/opt
        subprocess.run(["c++","-std=c++20",opt,"-Wall","-Wextra","-Werror","-pthread",
                        str(cpp),"-o",str(exe)],check=True,timeout=30)
        subprocess.run([str(exe)],check=True,timeout=10)
        print("ENCORE_DMA_COPY_SPAN_PASS",opt)
        print("NS1_DMA_TEXTURE_COHERENCE_HOST_PASS",opt,
              "exact_gpu_ranges=1 ns1_granular=1 ns2_policy_unchanged=1")
