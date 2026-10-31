#!/usr/bin/env python3
"""F07: compile source-selected writable multi-range rejection under O0/O2.

The GPU source must avoid expensive gathered fallback allocation when sparse
binding is unavailable. Read-only gathers, sparse writes and desktop keep
the previous result and FIFO commands. No real PS5 GPU/FPS proof.
"""
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
source = (ROOT / "vendor/encore-active/eden-vulkan/vk_buffer_cache_cost.cpp").read_text()
generator = (ROOT / "tools/prepare-vulkan-port.py").read_text()
fast = (ROOT / ".github/workflows/encore-core-fast-gate.yml").read_text()
pre = (ROOT / ".github/workflows/encore-core-preflight.yml").read_text()
call = "python3 -B tools/check-ps5-f07-multirange-write-preflight-host.py"
assert call in fast and call in pre
assert "F07 reject unsupported native writable multirange before fallback allocation" in generator
begin = "bool BufferCacheRuntime::BindMultiRangeStorageBuffer(u64 key, bool is_written) {"
end = "\nvoid BufferCacheRuntime::BindIndexBuffer("
assert source.count(begin)==1
body = source[source.index(begin):source.index(end,source.index(begin))]
assert "if (is_written && !multi_range_buffers.use_sparse)" in body
assert body.index("if (is_written && !multi_range_buffers.use_sparse)") < body.index("multi_range_buffers.Get(")
assert body.count("if (is_written && !ref.sparse)") == 1
assert "#ifdef PS5_NATIVE" in body and "std::array<VideoCommon::BufferCopy, 8> grouped_copies{};" in body
assert "if (source.handle != grouped_source || grouped_count == grouped_copies.size())" in body
assert "flush_group();" in body and "multi_range_buffers.MarkGathered(key);" in body
assert "F07 coalesce adjacent native multirange gather slices into bounded FIFO batches" in generator
cpp = r"""
#include <array>
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <span>
#include <vector>
using u64 = std::uint64_t;
using VkDeviceSize = std::uint64_t;
using VkBuffer = std::uint64_t;
constexpr VkBuffer VK_NULL_HANDLE=0;
namespace Eden::DevVulkan { inline bool disable_multi_range=false; }
struct Device {};
struct Scheduler {};
struct Allocator {};
struct MultiRangeSource { VkBuffer handle{2}; VkDeviceSize offset{}; VkDeviceSize size{8}; };
struct MultiRangeRef {
    VkBuffer handle{5};
    VkDeviceSize address{11},size{8};
    bool sparse{},needs_gather{true};
};
namespace VideoCommon {
struct BufferCopy { u64 src_offset{},dst_offset{}; std::size_t size{}; };
}
struct MultiRangeBufferCache {
    bool use_sparse{};
    unsigned gets{},marked{};
    MultiRangeRef Get(Device&,Scheduler&,Allocator&,u64,
                      const std::vector<MultiRangeSource>&,VkDeviceSize total) {
        ++gets;
        return MultiRangeRef{5,11,total,use_sparse,!use_sparse};
    }
    void MarkGathered(u64) {++marked;}
};
struct Queue {
    unsigned adds{};
    void AddBuffer(VkBuffer, VkDeviceSize, VkDeviceSize, VkDeviceSize){++adds;}
};
struct BufferCacheRuntime {
    Device device{};
    Scheduler scheduler{};
    Allocator memory_allocator{};
    MultiRangeBufferCache multi_range_buffers{};
    std::vector<MultiRangeSource> multi_range_sources{{}};
    VkDeviceSize multi_range_total{8};
    Queue guest_descriptor_queue{};
    struct ActualCopy { VkBuffer source{}; u64 src{}, dst{}, size{}; };
    std::vector<ActualCopy> recorded;
    std::vector<std::size_t> group_sizes;
    unsigned before{},after{},copies{};
    void PreCopyBarrier(){++before;}
    void PostCopyBarrier(){++after;}
    template<class T>
    void CopyBuffer(VkBuffer target,VkBuffer src,const T& regions,bool barrier) {
        assert(target==5 && !barrier);
        assert(!regions.empty() && regions.size() <= 8);
        ++copies;
        group_sizes.push_back(regions.size());
        for (const auto& v:regions)recorded.push_back({src,v.src_offset,v.dst_offset,v.size});
    }
    bool BindMultiRangeStorageBuffer(u64,bool);
};
__SOURCE__
int main() {
    {
        BufferCacheRuntime c;
        assert(!c.BindMultiRangeStorageBuffer(1,true));
#ifdef PS5_NATIVE
        assert(c.multi_range_buffers.gets==0 && c.copies==0);
#else
        assert(c.multi_range_buffers.gets==1 && c.copies==0);
#endif
        assert(c.guest_descriptor_queue.adds==0);
    }
    {
        BufferCacheRuntime c;
        assert(c.BindMultiRangeStorageBuffer(1,false));
        assert(c.multi_range_buffers.gets==1 && c.copies==1);
        assert(c.before==1 && c.after==1);
        assert(c.recorded.size()==1 && c.recorded[0].source==2);
        assert(c.multi_range_buffers.marked==1 && c.guest_descriptor_queue.adds==1);
    }
    {
        // 3 repeated owner slices, 2 of a new owner, 9 of a third.
        // PS5: one + one + two bounded batches; desktop unchanged.
        BufferCacheRuntime c;
        c.multi_range_sources.clear();
        u64 total=0;
        std::vector<BufferCacheRuntime::ActualCopy> expected;
        for (unsigned i=0;i<14;++i) {
            const VkBuffer owner = i<3?2:(i<5?7:11);
            const u64 size = static_cast<u64>(i%5+1)*8;
            const u64 offset = static_cast<u64>(i*64);
            c.multi_range_sources.push_back({owner,offset,size});
            expected.push_back({owner,offset,total,size});
            total+=size;
        }
        c.multi_range_total=total;
        assert(c.BindMultiRangeStorageBuffer(5,false));
        assert(c.before==1 && c.after==1 && c.multi_range_buffers.marked==1);
        assert(c.recorded.size()==14 && c.guest_descriptor_queue.adds==1);
        for(std::size_t i=0;i<expected.size();++i) {
            const auto& actual=c.recorded[i];
            const auto& wanted=expected[i];
            assert(actual.source==wanted.source && actual.src==wanted.src &&
                   actual.dst==wanted.dst && actual.size==wanted.size);
        }
#ifdef PS5_NATIVE
        assert(c.copies==4 && (c.group_sizes==std::vector<std::size_t>{3,2,8,1}));
#else
        assert(c.copies==14 && c.group_sizes.size()==14);
#endif
    }
    {
        BufferCacheRuntime c;
        c.multi_range_buffers.use_sparse=true;
        assert(c.BindMultiRangeStorageBuffer(1,true));
        assert(c.multi_range_buffers.gets==1 && c.copies==0);
        assert(c.before==0 && c.after==0 && c.guest_descriptor_queue.adds==1);
    }
    {
        BufferCacheRuntime c;
        c.multi_range_sources.clear();
        assert(!c.BindMultiRangeStorageBuffer(1,true));
        assert(c.multi_range_buffers.gets==0);
    }
    {
        BufferCacheRuntime c;
        Eden::DevVulkan::disable_multi_range=true;
        assert(!c.BindMultiRangeStorageBuffer(1,true));
        assert(c.multi_range_buffers.gets==0);
        Eden::DevVulkan::disable_multi_range=false;
    }
}
""".replace("__SOURCE__",body)
compiler = shutil.which("clang++") or shutil.which("g++")
assert compiler, "C++20 compiler required"
with tempfile.TemporaryDirectory(prefix="f07-multirange-writes-") as d:
    src=Path(d)/"multi.cpp"
    src.write_text(cpp)
    for native in (False,True):
        for opt in ("-O0","-O2"):
            exe=Path(d)/(str(int(native))+opt)
            cmd=[compiler,"-std=c++20",opt,"-Wall","-Wextra","-Werror",
                 "-fsanitize=undefined","-fno-sanitize-recover=all",
                 *(["-DPS5_NATIVE=1"] if native else []),str(src),"-o",str(exe)]
            result=subprocess.run(cmd,capture_output=True,text=True,timeout=60)
            assert result.returncode==0,(native,opt,result.stderr[-5000:])
            result=subprocess.run([str(exe)],capture_output=True,text=True,timeout=20)
            assert result.returncode==0,(native,opt,result.stderr[-5000:])
            print("F07_MULTIRANGE_WRITE_PREFLIGHT_PASS native="+str(int(native)),opt)
print("F07_NO_PS5_GPU_OR_FPS_PROOF")
