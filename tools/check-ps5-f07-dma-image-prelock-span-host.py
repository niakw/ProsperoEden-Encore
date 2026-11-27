#!/usr/bin/env python3
"""F07 native DMA image invalid byte spans must not wait on both caches."""
from pathlib import Path
import shutil
import subprocess
import tempfile

root=Path(__file__).resolve().parents[1]
source=(root/"vendor/encore-active/eden-vulkan/vulkan_rasterizer.cpp").read_text()
variant=(root/"vendor/encore-active/eden/src/video_core/renderer_vulkan/vk_rasterizer_deferred.cpp").read_text()
gen=(root/"tools/prepare-vulkan-port.py").read_text()
needle="bool AccelerateDMA::DmaBufferImageCopy("
a=source.index(needle)
b=source.index("    static constexpr auto sync_info",a)
prefix=source[a:b]
# The legacy bridge is a provenance baseline, not the active PS5 source.
# Only the reviewed current-channel GMMU preflight may differ in this method.
fragment_guard = """#ifdef PS5_NATIVE
    // ObtainBuffer translates only the first GPU VA into one CPU interval.
    // A buffer spanning noncontiguous GMMU pages would upload/download
    // unrelated physical memory. The normal MaxwellDMA CPU fallback
    // supports a page-aware transfer for both image-copy directions.
    // Test the channel currently bound to this rasterizer; no stale GMMU.
    if (!gpu_memory ||
        (!gpu_memory->IsGranularRange(buffer_operand.address, checked_bytes) &&
         !gpu_memory->IsContinuousRange(buffer_operand.address, checked_bytes))) {
        return false;
    }
#endif
"""
lock_anchor="    std::scoped_lock lock{buffer_cache.mutex, texture_cache.mutex};\n"
baseline=variant[variant.index(needle):variant.index("    static constexpr auto sync_info",variant.index(needle))]
assert baseline.count(lock_anchor)==1
assert prefix==baseline.replace(lock_anchor,lock_anchor+fragment_guard)
assert prefix.index(fragment_guard) > prefix.index(lock_anchor)
assert prefix.index(fragment_guard) < prefix.index("texture_cache.DmaImageId(")
# Channel switch proof: the accelerator stores a reference to the rasterizer's
# active GMMU pointer, not the GMMU captured during object construction.
owner=(root/"vendor/encore-active/eden-vulkan/include/video_core/renderer_vulkan/vk_rasterizer.h").read_text()
assert owner.count("Tegra::MemoryManager* const& gpu_memory;")==1
assert owner.count("Scheduler& scheduler, Tegra::MemoryManager* const& gpu_memory);")==1
assert "accelerate_dma(buffer_cache, texture_cache, scheduler, gpu_memory)" in source
assert "gpu_memory{gpu_memory_}" in source
assert "GPU-22 DMA image GMMU continuity before cache mutation" in gen
assert "F07 native DMA image byte guard before paired cache mutex" in gen
guard=prefix.index("if (checked_bytes == 0 ||")
lock=prefix.index("std::scoped_lock lock{buffer_cache.mutex, texture_cache.mutex};")
assert guard < lock
assert prefix.count("const u32 buffer_size = ")==2
for flow in (".github/workflows/encore-core-fast-gate.yml",".github/workflows/encore-core-preflight.yml"):
    assert "python3 -B tools/check-ps5-f07-dma-image-prelock-span-host.py" in (root/flow).read_text()
cpp=r"""
#include <cassert>
#include <cstdint>
#include <mutex>
using u32=std::uint32_t;using u64=std::uint64_t;
namespace Tegra {
struct MemoryManager {
    bool fragmented{};
    int checks{};
    bool IsGranularRange(u64, u64) { ++checks; return !fragmented; }
    bool IsContinuousRange(u64, u64) { ++checks; return !fragmented; }
};
namespace DMA {
struct ImageCopy {};
struct BufferOperand {u32 pitch{};u32 height{};u64 address{};};
struct ImageOperand {};
} }
namespace VideoCommon { constexpr int NULL_IMAGE_ID=0; }
struct CountingMutex {
    std::mutex owned;
    int requests{};
    void lock(){++requests;owned.lock();}
    bool try_lock(){++requests;return owned.try_lock();}
    void unlock(){owned.unlock();}
};
struct BufferCacheMock {CountingMutex mutex;};
struct TextureCacheMock {
    CountingMutex mutex;
    int looked_up{};
    int DmaImageId(const Tegra::DMA::ImageOperand&,bool) {
        ++looked_up;
        return 1;
    }
};
struct AccelerateDMA {
    BufferCacheMock buffer_cache;
    TextureCacheMock texture_cache;
    Tegra::MemoryManager current{};
    Tegra::MemoryManager* bound_channel=&current;
    Tegra::MemoryManager* const& gpu_memory=bound_channel;
    template<bool IS_IMAGE_UPLOAD>
    bool DmaBufferImageCopy(const Tegra::DMA::ImageCopy&,
       const Tegra::DMA::BufferOperand&,
       const Tegra::DMA::ImageOperand&);
};
"""+"template <bool IS_IMAGE_UPLOAD>\n"+prefix+"""
    (void)buffer_size;
    (void)copy_info;
    return true;
}
"""+r"""
int main(){
    for(bool upload:{false,true}){
        const auto check=[&](u32 pitch,u32 height,bool valid){
            AccelerateDMA cache;
            Tegra::DMA::BufferOperand buffer{pitch,height,7};
            Tegra::DMA::ImageCopy copy{};
            Tegra::DMA::ImageOperand image{};
            const bool ok=upload?cache.DmaBufferImageCopy<true>(copy,buffer,image)
                                :cache.DmaBufferImageCopy<false>(copy,buffer,image);
            assert(ok==valid);
#ifdef PS5_NATIVE
            if(!valid){
                assert(cache.buffer_cache.mutex.requests==0);
                assert(cache.texture_cache.mutex.requests==0);
                assert(cache.texture_cache.looked_up==0);
            } else {
                assert(cache.texture_cache.looked_up==1);
                assert(cache.buffer_cache.mutex.requests>0);
            }
#else
            if(!valid)assert(cache.texture_cache.looked_up==1);
#endif
        };
        // Zero-length DMA is rejected before mutexes only on PS5.
#ifdef PS5_NATIVE
        check(0,900,false);
        check(8,0,false);
#else
        check(0,900,true);
        check(8,0,true);
#endif
        check(0xffffffffu,2,false);
        check(64,32,true);
#ifdef PS5_NATIVE
        // A valid byte count but fragmented GMMU must be rejected before
        // DmaImageId mutates cache ownership. This tests both directions.
        AccelerateDMA fragmented;
        Tegra::MemoryManager next_channel;
        next_channel.fragmented=true;
        fragmented.bound_channel=&next_channel;
        Tegra::DMA::BufferOperand image_buffer{64,32,0x1000};
        Tegra::DMA::ImageCopy copy{};
        Tegra::DMA::ImageOperand image{};
        const bool admitted = upload
            ? fragmented.DmaBufferImageCopy<true>(copy,image_buffer,image)
            : fragmented.DmaBufferImageCopy<false>(copy,image_buffer,image);
        assert(!admitted);
        assert(next_channel.checks==2);
        assert(fragmented.current.checks==0);
        assert(fragmented.texture_cache.looked_up==0);
        assert(fragmented.buffer_cache.mutex.requests>0);
#endif
    }
}
"""
# The executable below already covers span validation; also pin the distinct
# Vulkan-handle guard and its position before image-cache lookup and upload.
dma_method = source[source.index(needle):source.index("\nbool AccelerateDMA::ImageToBuffer(",source.index(needle))]
dma_mirror = variant[variant.index(needle):variant.index("\nbool AccelerateDMA::ImageToBuffer(",variant.index(needle))]
assert dma_method == dma_mirror.replace(lock_anchor,lock_anchor+fragment_guard)
assert dma_method.count("if (!buffer || buffer->Handle() == VK_NULL_HANDLE)") == 1
assert dma_method.index("if (!buffer || buffer->Handle() == VK_NULL_HANDLE)") < dma_method.index("texture_cache.DmaBufferImageCopy(")
assert "F07 DMA image reject null Vulkan handles" in gen
compiler=shutil.which("clang++-18") or shutil.which("clang++") or shutil.which("g++")
assert compiler
with tempfile.TemporaryDirectory(prefix="f07-dma-image-prelock-") as folder:
    cppfile=Path(folder)/"dma.cpp"
    cppfile.write_text(cpp)
    for opt in ("-O0","-O2"):
        for native in (True,False):
            exe=Path(folder)/(("native" if native else "desktop")+opt[1:])
            cmd=[compiler,"-std=c++20",opt,"-Wall","-Wextra","-Werror",
                 "-fsanitize=undefined","-fno-sanitize-recover=all",
                 *(["-DPS5_NATIVE=1"] if native else []),str(cppfile),"-o",str(exe)]
            build=subprocess.run(cmd,capture_output=True,text=True,timeout=45)
            assert build.returncode==0,(native,opt,build.stderr[-4000:])
            result=subprocess.run([str(exe)],capture_output=True,text=True,timeout=15)
            assert result.returncode==0,(native,opt,result.stderr[-4000:])

# Execute the exact DMA acquisition/handle guard from the active source. A
# valid guest buffer can still have no Vulkan allocation on PS5.
first="    static constexpr auto sync_info = VideoCommon::ObtainBufferSynchronize::FullSynchronize;"
last="    const auto [image, copy] = texture_cache.DmaBufferImageCopy("
def extract_guard(src):
    begin=src.index(needle)
    return src[src.index(first,begin):src.index(last,begin)]
guard_code=extract_guard(source)
assert guard_code==extract_guard(variant)
assert guard_code.count("if (!buffer || buffer->Handle() == VK_NULL_HANDLE)") == 1
cpp_guard=r"""
#include <cassert>
#include <cstdint>
#include <utility>
#include <initializer_list>
using u32=std::uint32_t;
using u64=std::uint64_t;
inline constexpr int VK_NULL_HANDLE=0;
namespace VideoCommon {
enum class ObtainBufferSynchronize { FullSynchronize };
enum class ObtainBufferOperation { DoNothing, MarkAsWritten };
}
struct Buffer {int handle{9};int Handle()const{return handle;}};
struct BufferCache {
    Buffer* active{};
    std::pair<Buffer*,u32> ObtainBuffer(u64,u32,
        VideoCommon::ObtainBufferSynchronize,VideoCommon::ObtainBufferOperation){
        return {active,0};
    }
};
struct Driver {
    Buffer stored{};
    BufferCache buffer_cache{};
    template<bool IS_IMAGE_UPLOAD> bool Check(bool present,int handle) {
        stored.handle=handle;
        buffer_cache.active=present?&stored:nullptr;
        struct Operand {u64 address{};} buffer_operand{12};
        const u32 buffer_size=48;
""" + guard_code + r"""
        (void)offset;
        return true;
    }
};
int main(){
    for (bool upload:{true,false}) {
        const auto check=[&](bool present,int handle){
            Driver driver;
            return upload?driver.Check<true>(present,handle):
                          driver.Check<false>(present,handle);
        };
#ifdef PS5_NATIVE
        assert(!check(false,9));
        assert(!check(true,VK_NULL_HANDLE));
#endif
        assert(check(true,9));
    }
}
"""
with tempfile.TemporaryDirectory(prefix="f07-dma-handle-") as folder:
    src=Path(folder)/"guard.cpp"
    src.write_text(cpp_guard)
    for opt in ("-O0","-O2"):
        for native in (True,False):
            exe=Path(folder)/(("native" if native else "desktop")+opt[1:])
            flags=["-DPS5_NATIVE=1"] if native else []
            build=subprocess.run(
                [compiler,"-std=c++20",opt,"-Wall","-Wextra","-Werror",
                 "-fsanitize=undefined","-fno-sanitize-recover=all",
                 *flags,str(src),"-o",str(exe)],
                capture_output=True,text=True,timeout=45)
            assert build.returncode==0,(native,opt,build.stderr[-6000:])
            run=subprocess.run([str(exe)],capture_output=True,text=True,timeout=15)
            assert run.returncode==0,(native,opt,run.stderr[-5000:])
print("F07_DMA_IMAGE_HANDLE_PASS ps5_null_pointer=1 ps5_null_vk_handle=1 both_directions=1 desktop_valid=1 O0=1 O2=1 UBSan=1")

print("F07_DMA_IMAGE_PRELOCK_SPAN_PASS native=1 desktop=1 O0=1 O2=1 zero=1 overflow=1 valid=1 paired_mutex_skipped=1")
