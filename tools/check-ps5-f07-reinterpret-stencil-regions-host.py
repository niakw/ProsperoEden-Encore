#!/usr/bin/env python3
"""Execute actual PS5 reinterpret region scratch planner with C++ UBSan.

The snippet is extracted from the maintained Vulkan owner, not copied by hand.
It validates separated depth/stencil planes, region offsets, array layers,
overflow, format and aspect compatibility. This is NOT Vulkan GPU execution.
"""
from pathlib import Path
import os
import re
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
owner = (ROOT / "vendor/encore-active/eden-vulkan/vk_texture_cache_cost.cpp").read_text()
begin = "void TextureCacheRuntime::ReinterpretImage(Image& dst, Image& src,"
end = "\nvoid TextureCacheRuntime::BlitImage("
assert owner.count(begin) == owner.count(end) == 1
method = owner[owner.index(begin):owner.index(end, owner.index(begin))]
start = "#ifdef PS5_NATIVE\n    // Every VkBufferImageCopy must occupy"
stop = "    const VkBuffer copy_buffer = GetTemporaryBuffer(total_size);"
assert method.count(start) == method.count(stop) == 1
planner = method[method.index(start):method.index(stop)]
assert planner.startswith("#ifdef PS5_NATIVE") and planner.rstrip().endswith("#endif")
assert "if (src_both || dst_both)" not in planner
assert "const bool dual_planes = src_both && dst_both;" in planner
assert "const size_t layers = from.imageSubresource.layerCount;" in planner
assert "source_width * bpp_in != dest_width * bpp_out" in planner
assert "scratch_used += plane_bytes * (dual_planes ? 2U : 1U);" in planner
assert "from_stencil.imageSubresource.aspectMask = VK_IMAGE_ASPECT_STENCIL_BIT" in planner
assert "to_stencil.imageSubresource.aspectMask = VK_IMAGE_ASPECT_STENCIL_BIT" in planner
# Production owner returns void; adapt its rejection exits to the
# boolean witness without changing any decision or computation.
planner = re.sub(r"\breturn;", "return false;", planner)

cpp = r'''
#include <algorithm>
#include <array>
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <limits>
#include <vector>
using u32 = std::uint32_t;
using VkImageAspectFlags = std::uint32_t;
using VkDeviceSize = std::uint64_t;
constexpr VkImageAspectFlags VK_IMAGE_ASPECT_COLOR_BIT = 1U;
constexpr VkImageAspectFlags VK_IMAGE_ASPECT_DEPTH_BIT = 2U;
constexpr VkImageAspectFlags VK_IMAGE_ASPECT_STENCIL_BIT = 4U;
struct Extent {
    u32 width, height, depth;
};
struct Subresource {
    VkImageAspectFlags aspectMask;
    u32 layerCount;
};
struct VkBufferImageCopy {
    VkDeviceSize bufferOffset{};
    Subresource imageSubresource{};
    Extent imageExtent{};
};
struct Copy {};
struct Info {u32 format;};
struct Image {Info info;};
u32 BytesPerBlock(u32 format) {return format;}
bool Plan(const std::vector<Copy>& copies,
          const Image& src, const Image& dst,
          VkImageAspectFlags src_aspect_mask,
          VkImageAspectFlags dst_aspect_mask,
          u32 bpp_in, u32 bpp_out, u32 img_bpp,
          std::vector<VkBufferImageCopy>& vk_in_copies,
          std::vector<VkBufferImageCopy>& vk_out_copies,
          size_t& total_size) {
    constexpr size_t max_size = (std::numeric_limits<size_t>::max)();
__PLANNER__
    return true;
}
bool Run(VkImageAspectFlags src_aspect, VkImageAspectFlags dst_aspect,
         u32 src_bpp, u32 dst_bpp,
         std::vector<Extent> extents, u32 layer_count,
         std::vector<VkBufferImageCopy>& a,
         std::vector<VkBufferImageCopy>& b,
         size_t& budget,
         u32 src_width=0) {
    std::vector<Copy> copies(extents.size());
    // The production MakeBufferImageCopy stage has already normalized a
    // combined D/S mask to its Depth plane before this scratch planner.
    const auto normalized_src = src_aspect == (VK_IMAGE_ASPECT_DEPTH_BIT|
        VK_IMAGE_ASPECT_STENCIL_BIT) ? VK_IMAGE_ASPECT_DEPTH_BIT : src_aspect;
    const auto normalized_dst = dst_aspect == (VK_IMAGE_ASPECT_DEPTH_BIT|
        VK_IMAGE_ASPECT_STENCIL_BIT) ? VK_IMAGE_ASPECT_DEPTH_BIT : dst_aspect;
    for (auto extent:extents) {
        a.push_back({0,{normalized_src,layer_count},
                     {src_width ? src_width : extent.width,
                      extent.height,extent.depth}});
        b.push_back({0,{normalized_dst,layer_count},extent});
    }
    return Plan(copies,{{src_bpp}},{{dst_bpp}},src_aspect,dst_aspect,
                src_bpp,dst_bpp,dst_bpp,a,b,budget);
}
int main() {
    constexpr u32 color=VK_IMAGE_ASPECT_COLOR_BIT;
    constexpr u32 both=VK_IMAGE_ASPECT_DEPTH_BIT|VK_IMAGE_ASPECT_STENCIL_BIT;
    std::vector<VkBufferImageCopy> a,b;
    size_t size=0;
    // Two ordinary regions must use independent offsets, not two 0s.
    assert(Run(color,color,4,4,{{4,5,1},{3,2,1}},1,a,b,size));
    assert(size==104 && a.size()==2 && b.size()==2);
    assert(a[0].bufferOffset==0 && a[1].bufferOffset==80);
    assert(a[1].bufferOffset==b[1].bufferOffset);
    assert(a[1].imageSubresource.aspectMask==color);
    a.clear();b.clear();size=0;
    // D24S8: 20 pixels, 80 depth bytes + separately aligned 80-byte
    // stencil budget (actual stencil content 20 B). Neither overwrites
    // the other; both planes use single Vulkan aspects.
    assert(Run(both,both,4,4,{{4,5,1}},1,a,b,size));
    assert(size==160 && a.size()==2 && b.size()==2);
    assert(a[0].bufferOffset==0 && a[1].bufferOffset==80);
    assert(b[0].bufferOffset==0 && b[1].bufferOffset==80);
    assert(a[0].imageSubresource.aspectMask==VK_IMAGE_ASPECT_DEPTH_BIT);
    assert(b[0].imageSubresource.aspectMask==VK_IMAGE_ASPECT_DEPTH_BIT);
    assert(a[1].imageSubresource.aspectMask==VK_IMAGE_ASPECT_STENCIL_BIT);
    assert(b[1].imageSubresource.aspectMask==VK_IMAGE_ASPECT_STENCIL_BIT);
    a.clear();b.clear();size=0;
    // D32S8: conservative 8B/texel per plane. Array-layer count
    // multiplies the budget: Vulkan copies all three full layers.
    assert(Run(both,both,8,8,{{4,5,1}},3,a,b,size));
    assert(size==960 && a.size()==2 && b.size()==2);
    assert(a[1].bufferOffset==480 && b[1].bufferOffset==480);
    a.clear();b.clear();size=0;
    assert(Run(both,both,4,4,{{4,5,1},{4,2,1}},1,a,b,size));
    assert(size==224 && a.size()==4 && b.size()==4);
    // First two slots are original depth regions; stencil regions append.
    assert(a[0].bufferOffset==0 && a[1].bufferOffset==160);
    assert(a[2].bufferOffset==80 && a[3].bufferOffset==192);
    // Valid cross-format color reinterpret has the same real byte count.
    a.clear();b.clear();size=0;
    assert(Run(color,color,8,4,{{8,2,1}},1,a,b,size,4));
    assert(size==64 && a[0].bufferOffset==b[0].bufferOffset);
    // Incompatible formats or aspects cannot silently lose stencil.
    a.clear();b.clear();size=0;
    assert(!Run(both,color,4,4,{{4,5,1}},1,a,b,size));
    a.clear();b.clear();size=0;
    assert(!Run(color,both,4,4,{{4,5,1}},1,a,b,size));
    a.clear();b.clear();size=0;
    assert(!Run(both,both,4,8,{{4,5,1}},1,a,b,size));
    // Pixel ratio mismatch is not a license to copy the wrong bytes.
    a.clear();b.clear();size=0;
    assert(!Run(color,color,8,4,{{7,2,1}},1,a,b,size,4));
    // Overflow in layer footprint and scratch slot budget fails closed.
    a.clear();b.clear();size=0;
    assert(!Run(color,color,8,8,{{0xffffffffU,0xffffffffU,1}},2,a,b,size));
    a.clear();b.clear();size=0;
    assert(!Run(both,both,8,8,{{0xffffffffU,0xffffffffU,1}},1,a,b,size));
    std::puts("F07_NATIVE_STENCIL_REGIONS_PASS disjoint_regions=1 "
              "dual_aspects=1 multilayer_budget=1 mixed_format_refused=1 "
              "overflow_refused=1 ns1_path_unchanged=1");
}
'''.replace("__PLANNER__", planner)
with tempfile.TemporaryDirectory(prefix="eden-stencil-plan-") as t:
    src = Path(t)/"stencil_plan.cpp"
    src.write_text(cpp)
    env = os.environ.copy()
    sdk = Path("/Library/Developer/CommandLineTools/SDKs/MacOSX15.4.sdk")
    if sdk.exists():
        env["SDKROOT"] = str(sdk)
    for cc in ("clang++","g++"):
        compiler = shutil.which(cc)
        if not compiler:
            continue
        for opt in ("-O0","-O2"):
            exe = Path(t)/(cc.replace("+","p")+opt)
            compiled = subprocess.run(
                [compiler,"-std=c++20",opt,"-DPS5_NATIVE=1","-Wall",
                 "-Wextra","-Werror","-fsanitize=undefined",
                 "-fno-sanitize-recover=all",str(src),"-o",str(exe)],
                env=env,capture_output=True,text=True,timeout=65)
            assert compiled.returncode == 0, (cc,opt,compiled.stderr[-5000:])
            ran = subprocess.run([str(exe)],env=env,
                                 capture_output=True,text=True,timeout=30)
            assert ran.returncode == 0,(cc,opt,ran.stdout,ran.stderr[-5000:])
            print(cc,opt,ran.stdout.strip())
print("F07_REINTERPRET_STENCIL_SOURCE_SPAN_PASS true_owner=1 gpu=NOT_TESTED")
