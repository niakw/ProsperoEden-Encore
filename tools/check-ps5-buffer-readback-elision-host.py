#!/usr/bin/env python3
"""ASan/UBSan actual-method buffer readback mutex elision witness."""
from pathlib import Path
import shutil, subprocess, tempfile
root=Path(__file__).resolve().parents[1]
def read(x):return (root/x).read_text()
raster=read("vendor/encore-active/eden-vulkan/vulkan_rasterizer.cpp")
bridge=read("vendor/encore-active/eden-core/guest-bridge/vulkan_rasterizer.cpp")
pinned=read("vendor/sources/eden/src/video_core/renderer_vulkan/vk_rasterizer.cpp")
oracle=read("tools/prepare-vulkan-port.py")
workflow=read(".github/workflows/encore-core-preflight.yml")
buf=read("vendor/encore-active/eden-core/src/video_core/buffer_cache/buffer_cache.h")
begin="void RasterizerVulkan::FlushRegion(DAddr addr, u64 size, VideoCommon::CacheType which) {"
end="VideoCore::RasterizerDownloadArea RasterizerVulkan::GetFlushArea("
def extract(x):
 assert x.count(begin)==x.count(end)==1
 return x[x.index(begin):x.index(end,x.index(begin))]
body=extract(raster)
assert body==extract(bridge) and body!=extract(pinned)
assert body.count("::Eden::BufferPages::NeverRegistered(addr, size)")==2
assert body.count("::Eden::ImagePages::NeverHeld(addr, size)")==2
assert body.index("buffer_cache.DownloadMemory(addr, size)") < body.index(
 "query_cache.FlushRegion(addr, size)")
assert body.index("buffer_cache.IsRegionGpuModified(addr, size)") < body.index(
 "if (!Settings::IsGPULevelHigh())")
assert '::Eden::BufferPages::Mark(buffer.CpuAddr(), size);' in buf
assert "CPU page registration proof for buffer-only guest readbacks" in oracle
assert "python3 -B tools/check-ps5-buffer-readback-elision-host.py" in workflow
code=r"""
#include <cassert>
#include <cstdint>
#include <mutex>
#include "image_pages.h"
#include "buffer_pages.h"
using DAddr=std::uint64_t;using u64=std::uint64_t;
namespace VideoCommon{enum class CacheType:unsigned {TextureCache=1,BufferCache=2,QueryCache=4};}
constexpr VideoCommon::CacheType operator&(VideoCommon::CacheType a,VideoCommon::CacheType b){
 return static_cast<VideoCommon::CacheType>(static_cast<unsigned>(a)&static_cast<unsigned>(b));
}
constexpr bool True(VideoCommon::CacheType v){return static_cast<unsigned>(v)!=0;}
namespace Settings{inline bool high=true;bool IsGPULevelHigh(){return high;}}
struct Mutex{
 std::recursive_mutex lockable;unsigned counts{};
 void lock(){lockable.lock();++counts;}
 void unlock(){lockable.unlock();}
};
struct Cache{
 Mutex mutex;unsigned downloads{},checks{};bool modified{};
 void DownloadMemory(DAddr,u64){++downloads;}
 bool IsRegionGpuModified(DAddr,u64){++checks;return modified;}
};
struct Query{unsigned calls{};void FlushRegion(DAddr,u64){++calls;}};
class RasterizerVulkan{
public:
 Cache buffer_cache,texture_cache;Query query_cache;
 void FlushRegion(DAddr,u64,VideoCommon::CacheType);
 bool MustFlushRegion(DAddr,u64,VideoCommon::CacheType);
};
__REAL__
int main(){
 using namespace Eden; constexpr u64 p=4096;
 RasterizerVulkan r;
 auto all=static_cast<VideoCommon::CacheType>(7);
 auto b=VideoCommon::CacheType::BufferCache;
 // No buffer registered: query still flushes, buffer mutex is spared.
 r.FlushRegion(10*p,p,all);
 assert(r.buffer_cache.mutex.counts==0 && r.buffer_cache.downloads==0);
 assert(r.texture_cache.mutex.counts==0 && r.query_cache.calls==1);
 // A buffer ever registered retains locked download/probe paths.
 BufferPages::Mark(20*p,p);
 r.FlushRegion(20*p,p,all);
 assert(r.buffer_cache.mutex.counts==1 && r.buffer_cache.downloads==1);
 assert(r.texture_cache.mutex.counts==0 && r.query_cache.calls==2);
 r.FlushRegion(19*p,2*p,b);
 assert(r.buffer_cache.downloads==2 && r.buffer_cache.mutex.counts==2);
 // An unowned 256 KiB readback stays lock-free after the wider bitmap
 // probe; larger/overflowed ranges still take the conservative path.
 r.FlushRegion(40*p,256*1024,b);
 assert(r.buffer_cache.downloads==2 && r.buffer_cache.mutex.counts==2);
 r.FlushRegion(40*p,256*1024+1,b);
 r.FlushRegion(BufferPages::kSpace-2,8,b);
 assert(r.buffer_cache.downloads==4 && r.buffer_cache.mutex.counts==4);
 r.FlushRegion(0,p,all);r.FlushRegion(10*p,0,all);
 assert(r.query_cache.calls==2);
 r.buffer_cache.modified=true;
 assert(!r.MustFlushRegion(30*p,p,b));
 assert(r.buffer_cache.checks==0);
 assert(r.MustFlushRegion(20*p,p,b));
 assert(r.buffer_cache.checks==1);
 assert(r.MustFlushRegion(50*p,0,b)); // unknown zero remains conservative
 assert(r.MustFlushRegion(BufferPages::kSpace,p,b));
 assert(r.buffer_cache.checks==3 && r.buffer_cache.mutex.counts==7);
 // The texture domain is independent of the buffer occupancy map.
 ImagePages::Mark(70*p,p);
 r.texture_cache.modified=true;
 assert(r.MustFlushRegion(70*p,p,all));
 assert(r.buffer_cache.checks==3 && r.texture_cache.checks==1);
 assert(r.texture_cache.mutex.counts==1);
 Settings::high=false;
 assert(!r.MustFlushRegion(70*p,p,all));
 assert(r.texture_cache.checks==1);
}
""".replace("__REAL__",body)
cxx=shutil.which("clang++-18") or shutil.which("clang++")
assert cxx
with tempfile.TemporaryDirectory(prefix="encore-buffer-readback-") as tmp:
 src=Path(tmp)/"test.cpp";exe=Path(tmp)/"test";src.write_text(code)
 subprocess.run([cxx,"-std=c++20","-O1","-pthread","-Wall","-Wextra","-Werror",
                 "-fsanitize=address,undefined","-fno-sanitize-recover=all",
                 "-I"+str(root/"headless"),str(src),"-o",str(exe)],check=True,timeout=55)
 subprocess.run([str(exe)],check=True,timeout=20)
print("VULKAN_BUFFER_READBACK_ELISION_HOST_PASS real_methods=2 no_buffer=1 "
      "registered=1 size_limit=1 zero=1 overflow=1 texture_independent=1 asan_ubsan=1")


# A CPU read of a GPU-written storage buffer (without any image on its page)
# must request a GPU sync rather than return a falsely preemptive area. Run the
# ACTUAL selected Vulkan method against both cache-domain ownership paths.
area_begin = "VideoCore::RasterizerDownloadArea RasterizerVulkan::GetFlushArea(DAddr addr, u64 size) {"
area_end = "\nvoid RasterizerVulkan::InvalidateRegion("
def get_read_method(text):
    assert text.count(area_begin) == text.count(area_end) == 1
    a = text.index(area_begin)
    return text[a:text.index(area_end, a)]
read_method = get_read_method(raster)
bridge_method = get_read_method(bridge)
# The bridge is an older oracle; the active owner corrected only two
# GuestCacheLock function invocations. Replay exactly those predecessors.
assert read_method.count("::Eden::Performance::GuestCacheLock(texture_cache.mutex, true);")==1
assert read_method.count("::Eden::Performance::GuestCacheLock(buffer_cache.mutex, false);")==1
assert read_method + "\n" == "VideoCore::RasterizerDownloadArea RasterizerVulkan::GetFlushArea(DAddr addr, u64 size) {\n    ::Eden::Performance::DiagnosticTimer guest_read_timer(::Eden::Performance::guest_cpu_read);\n    const VideoCore::RasterizerDownloadArea clean_area{\n        .start_address = Common::AlignDown(addr, Core::DEVICE_PAGESIZE),\n        .end_address = Common::AlignUp(addr + size, Core::DEVICE_PAGESIZE),\n        .preemtive = true,\n    };\n    // A clean/never-held texture page does not prove that a GPU-written\n    // storage buffer is current in guest memory. Query each cache independently:\n    // never-owned pages remain lock-free, and no two cache locks are nested.\n    std::optional<VideoCore::RasterizerDownloadArea> texture_area;\n    if (!::Eden::ImagePages::NeverHeld(addr, size)) {\n        ::Eden::Performance::GuestCacheLock(texture_cache.mutex, true);\n        std::lock_guard lock{texture_cache.mutex, std::adopt_lock};\n        texture_area = texture_cache.GetFlushArea(addr, size);\n    }\n    if (texture_area && !texture_area->preemtive) {\n        // The existing GPU sync flushes both cache domains.\n        return *texture_area;\n    }\n    auto area = texture_area.value_or(clean_area);\n    // Core::Memory caches the returned interval, not just the original\n    // scalar read. A preemptive texture can extend over other GPU-written\n    // buffers. Check EVERY byte the caller may subsequently read without\n    // re-entering GetFlushArea. Keep the original texture extent when clean.\n    const DAddr buffer_start = area.start_address;\n    const u64 buffer_size = area.end_address - buffer_start;\n    if (!::Eden::BufferPages::NeverRegistered(buffer_start, buffer_size)) {\n        ::Eden::Performance::GuestCacheLock(buffer_cache.mutex, false);\n        std::lock_guard lock{buffer_cache.mutex, std::adopt_lock};\n        if (buffer_cache.IsRegionGpuModified(buffer_start, buffer_size)) {\n            // Preserve the real GPU ownership and the existing ordered\n            // FlushRegion on the GPU worker. Do not certify stale siblings.\n            area.preemtive = false;\n        }\n    }\n    return area;\n}\n" or read_method == "VideoCore::RasterizerDownloadArea RasterizerVulkan::GetFlushArea(DAddr addr, u64 size) {\n    ::Eden::Performance::DiagnosticTimer guest_read_timer(::Eden::Performance::guest_cpu_read);\n    const VideoCore::RasterizerDownloadArea clean_area{\n        .start_address = Common::AlignDown(addr, Core::DEVICE_PAGESIZE),\n        .end_address = Common::AlignUp(addr + size, Core::DEVICE_PAGESIZE),\n        .preemtive = true,\n    };\n    // A clean/never-held texture page does not prove that a GPU-written\n    // storage buffer is current in guest memory. Query each cache independently:\n    // never-owned pages remain lock-free, and no two cache locks are nested.\n    std::optional<VideoCore::RasterizerDownloadArea> texture_area;\n    if (!::Eden::ImagePages::NeverHeld(addr, size)) {\n        ::Eden::Performance::GuestCacheLock(texture_cache.mutex, true);\n        std::lock_guard lock{texture_cache.mutex, std::adopt_lock};\n        texture_area = texture_cache.GetFlushArea(addr, size);\n    }\n    if (texture_area && !texture_area->preemtive) {\n        // The existing GPU sync flushes both cache domains.\n        return *texture_area;\n    }\n    auto area = texture_area.value_or(clean_area);\n    // Core::Memory caches the returned interval, not just the original\n    // scalar read. A preemptive texture can extend over other GPU-written\n    // buffers. Check EVERY byte the caller may subsequently read without\n    // re-entering GetFlushArea. Keep the original texture extent when clean.\n    const DAddr buffer_start = area.start_address;\n    const u64 buffer_size = area.end_address - buffer_start;\n    if (!::Eden::BufferPages::NeverRegistered(buffer_start, buffer_size)) {\n        ::Eden::Performance::GuestCacheLock(buffer_cache.mutex, false);\n        std::lock_guard lock{buffer_cache.mutex, std::adopt_lock};\n        if (buffer_cache.IsRegionGpuModified(buffer_start, buffer_size)) {\n            // Preserve the real GPU ownership and the existing ordered\n            // FlushRegion on the GPU worker. Do not certify stale siblings.\n            area.preemtive = false;\n        }\n    }\n    return area;\n}\n"
prior_method="VideoCore::RasterizerDownloadArea RasterizerVulkan::GetFlushArea(DAddr addr, u64 size) {\n    ::Eden::Performance::DiagnosticTimer guest_read_timer(::Eden::Performance::guest_cpu_read);\n    const VideoCore::RasterizerDownloadArea clean_area{\n        .start_address = Common::AlignDown(addr, Core::DEVICE_PAGESIZE),\n        .end_address = Common::AlignUp(addr + size, Core::DEVICE_PAGESIZE),\n        .preemtive = true,\n    };\n    // A clean/never-held texture page does not prove that a GPU-written\n    // storage buffer is current in guest memory. Query each cache independently:\n    // never-owned pages remain lock-free, and no two cache locks are nested.\n    std::optional<VideoCore::RasterizerDownloadArea> texture_area;\n    if (!::Eden::ImagePages::NeverHeld(addr, size)) {\n        ::Eden::Performance::GuestCacheLock(texture_cache.mutex, true);\n        std::lock_guard lock{texture_cache.mutex, std::adopt_lock};\n        texture_area = texture_cache.GetFlushArea(addr, size);\n    }\n    if (texture_area && !texture_area->preemtive) {\n        // The existing GPU sync flushes both cache domains.\n        return *texture_area;\n    }\n    if (!::Eden::BufferPages::NeverRegistered(addr, size)) {\n        ::Eden::Performance::GuestCacheLock(buffer_cache.mutex, false);\n        std::lock_guard lock{buffer_cache.mutex, std::adopt_lock};\n        if (buffer_cache.IsRegionGpuModified(\n                clean_area.start_address, clean_area.end_address - clean_area.start_address)) {\n            // GPU::OnCPURead must not return early for buffer-only GPU writes.\n            // Keep any texture-covered extent, including its sibling bytes.\n            return VideoCore::RasterizerDownloadArea{\n                .start_address = texture_area\n                    ? (std::min)(texture_area->start_address, clean_area.start_address)\n                    : clean_area.start_address,\n                .end_address = texture_area\n                    ? (std::max)(texture_area->end_address, clean_area.end_address)\n                    : clean_area.end_address,\n                .preemtive = false,\n            };\n        }\n    }\n    return texture_area.value_or(clean_area);\n}\n".replace(
    "::Eden::Performance::GuestCacheLock(texture_cache.mutex, true);",
    "::Eden::Performance::GuestCacheLock texture_wait(texture_cache.mutex, true);",1
).replace(
    "::Eden::Performance::GuestCacheLock(buffer_cache.mutex, false);",
    "::Eden::Performance::GuestCacheLock buffer_wait(buffer_cache.mutex, true);",1)
assert prior_method == bridge_method
assert read_method != get_read_method(pinned)
assert read_method.count("::Eden::BufferPages::NeverRegistered(buffer_start, buffer_size)") == 1
assert read_method.count("::Eden::ImagePages::NeverHeld(addr, size)") == 1
assert "buffer_cache.IsRegionGpuModified(" in read_method
assert "texture_area && !texture_area->preemtive" in read_method
assert "auto area = texture_area.value_or(clean_area);" in read_method
assert "return area;" in read_method
assert read_method.index("texture_cache.GetFlushArea") < read_method.index(
    "buffer_cache.IsRegionGpuModified(")

read_cpp = r"""
#include <algorithm>
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <mutex>
#include <optional>
#include "image_pages.h"
#include "buffer_pages.h"
using DAddr=std::uint64_t;
using u64=std::uint64_t;
namespace Core { inline constexpr DAddr DEVICE_PAGESIZE=4096; }
namespace Common {
template<class T> constexpr T AlignDown(T n, T a) {return n/a*a;}
template<class T> constexpr T AlignUp(T n, T a) {return n/a*a + (n%a ? a : 0);}
}
namespace VideoCore {
struct RasterizerDownloadArea {
    DAddr start_address{};
    DAddr end_address{};
    bool preemtive{};
};
}
struct CountMutex {
    std::mutex real;
    unsigned locks{};
    void lock(){real.lock();++locks;}
    void unlock(){real.unlock();}
};
namespace Eden::Performance {
inline int guest_cpu_read=0;
struct DiagnosticTimer { explicit DiagnosticTimer(int) {} };
inline void GuestCacheLock(CountMutex& m, bool) {m.lock();}
}
struct BufferCache {
    CountMutex mutex;
    bool gpu_dirty{};
    DAddr dirty_address{};
    unsigned probes{};
    bool IsRegionGpuModified(DAddr addr, u64 size){
        ++probes;
        return gpu_dirty && (dirty_address == 0 ||
            (dirty_address >= addr && dirty_address - addr < size));
    }
};
struct TextureCache {
    CountMutex mutex;
    unsigned probes{};
    std::optional<VideoCore::RasterizerDownloadArea> simulated_area;
    std::optional<VideoCore::RasterizerDownloadArea> GetFlushArea(DAddr, u64){
        ++probes;
        return simulated_area;
    }
};
struct RasterizerVulkan {
    BufferCache buffer_cache;
    TextureCache texture_cache;
    VideoCore::RasterizerDownloadArea GetFlushArea(DAddr,u64);
};
""" + read_method + r"""
int main() {
    using namespace Eden;
    constexpr DAddr p=4096, unused=48*p, storage=80*p;
    RasterizerVulkan absent;
    const auto clean=absent.GetFlushArea(unused+19,13);
    assert(clean.preemtive && clean.start_address==unused && clean.end_address==unused+p);
    assert(absent.buffer_cache.mutex.locks==0 && absent.texture_cache.mutex.locks==0);

    BufferPages::Mark(storage,p);
    RasterizerVulkan gpu_owned;
    gpu_owned.buffer_cache.gpu_dirty=true;
    const auto owed=gpu_owned.GetFlushArea(storage+19,13);
    assert(!owed.preemtive && owed.start_address==storage && owed.end_address==storage+p);
    assert(gpu_owned.buffer_cache.mutex.locks==1 && gpu_owned.buffer_cache.probes==1);
    assert(gpu_owned.texture_cache.mutex.locks==0);

    RasterizerVulkan cpu_current;
    const auto no_wait=cpu_current.GetFlushArea(storage+19,13);
    assert(no_wait.preemtive);
    assert(cpu_current.buffer_cache.mutex.locks==1);

    ImagePages::Mark(storage,p);
    RasterizerVulkan mixed;
    mixed.buffer_cache.gpu_dirty=true;
    mixed.texture_cache.simulated_area=VideoCore::RasterizerDownloadArea{
        storage-p,storage+2*p,true};
    const auto both=mixed.GetFlushArea(storage+19,13);
    assert(!both.preemtive && both.start_address==storage-p &&
           both.end_address==storage+2*p);
    assert(mixed.texture_cache.mutex.locks==1 && mixed.buffer_cache.mutex.locks==1);

    // A dirty texture already needs the same full-domain FlushRegion; never
    // acquire an unnecessary BufferCache lock while its texture lock is held.
    RasterizerVulkan image_dirty;
    image_dirty.buffer_cache.gpu_dirty=true;
    image_dirty.texture_cache.simulated_area=VideoCore::RasterizerDownloadArea{
        storage-2*p,storage+p,false};
    const auto image_owed=image_dirty.GetFlushArea(storage+19,13);
    assert(!image_owed.preemtive && image_owed.start_address==storage-2*p);
    assert(image_dirty.buffer_cache.mutex.locks==0);
    assert(image_dirty.texture_cache.mutex.locks==1);

    // Regression: the initial read's page has no registered buffer, but
    // the returned texture interval includes a GPU-written sibling page.
    constexpr DAddr image=112*p, sibling=image+2*p;
    ImagePages::Mark(image,3*p);
    BufferPages::Mark(sibling,p);
    RasterizerVulkan sibling_dirty;
    sibling_dirty.texture_cache.simulated_area=VideoCore::RasterizerDownloadArea{
        image,image+3*p,true};
    sibling_dirty.buffer_cache.gpu_dirty=true;
    sibling_dirty.buffer_cache.dirty_address=sibling+17;
    const auto sibling_owed=sibling_dirty.GetFlushArea(image+19,13);
    assert(!sibling_owed.preemtive && sibling_owed.start_address==image &&
           sibling_owed.end_address==image+3*p);
    assert(sibling_dirty.buffer_cache.probes==1);
    RasterizerVulkan sibling_clean;
    sibling_clean.texture_cache.simulated_area=sibling_dirty.texture_cache.simulated_area;
    const auto sibling_current=sibling_clean.GetFlushArea(image+19,13);
    assert(sibling_current.preemtive && sibling_clean.buffer_cache.probes==1);

    RasterizerVulkan former_image;
    const auto fallback=former_image.GetFlushArea(storage+19,13);
    assert(fallback.preemtive && former_image.texture_cache.mutex.locks==1);
    assert(former_image.buffer_cache.mutex.locks==1);
}
"""
with tempfile.TemporaryDirectory(prefix="encore-ns1-cpu-read-") as td:
    source=Path(td)/"read.cpp"
    source.write_text(read_cpp)
    for opt in ("-O0","-O2"):
        exe=Path(td)/("read-"+opt)
        subprocess.run([cxx,"-std=c++20",opt,"-Wall","-Wextra","-Werror",
                        "-fsanitize=address,undefined","-fno-sanitize-recover=all",
                        "-pthread","-I"+str(root/"headless"),str(source),"-o",str(exe)],
                       check=True,timeout=55)
        subprocess.run([str(exe)],check=True,timeout=20)
        print("NS1_BUFFER_CPU_READ_DIRTY_HOST_PASS",opt)
