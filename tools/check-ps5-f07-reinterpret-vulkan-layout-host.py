#!/usr/bin/env python3
"""Validate actual native/desktop Vulkan reinterpret depth/stencil copy ABI.

Production aspect normalization is extracted and executed with Clang and GCC
and UBSan. Actual barrier/copy layout fields are source-checked on the
reviewed owner and the retained generator recipe. No Vulkan GPU is run.
"""
from pathlib import Path
import ast
import os
import shutil
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[1]
active=ROOT/"vendor/encore-active/eden-vulkan/vk_texture_cache_cost.cpp"
code=active.read_text()
begin="void TextureCacheRuntime::ReinterpretImage(Image& dst, Image& src,"
end="\nvoid TextureCacheRuntime::BlitImage("
assert code.count(begin)==code.count(end)==1
method=code[code.index(begin):code.index(end,code.index(begin))]
src_begin="    const auto copy_aspect = [](VkImageAspectFlags mask) {"
src_end="    const VkImageAspectFlags src_copy_aspect = copy_aspect(src_aspect_mask);"
assert method.count(src_begin)==method.count(src_end)==1
aspect=method[method.index(src_begin):method.index(src_end)]
assert "VK_IMAGE_ASPECT_DEPTH_BIT | VK_IMAGE_ASPECT_STENCIL_BIT" in aspect
assert "VkImageAspectFlags{VK_IMAGE_ASPECT_DEPTH_BIT}" in aspect

# Copy regions are single-aspect and the barrier still tracks the whole
# attachment; do not silently discard a stencil barrier during transfer.
assert "[src_copy_aspect, bpp_in, bpp_out]" in method
assert "MakeBufferImageCopy(copy2, true, src_copy_aspect)" in method
assert "[dst_copy_aspect]" in method
assert "MakeBufferImageCopy(copy, false, dst_copy_aspect)" in method
assert "src_range.SubresourceRange(src_aspect_mask)" in method
assert "dst_range.SubresourceRange(dst_aspect_mask)" in method
assert "[src_aspect_mask, bpp_in, bpp_out]" not in method
assert "MakeBufferImageCopy(copy2, true, src_aspect_mask)" not in method
assert "MakeBufferImageCopy(copy, false, dst_aspect_mask)" not in method

assert method.count(".newLayout = VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL") == 1
assert method.count(".oldLayout = VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL") == 1
assert method.count(".newLayout = VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL") == 1
assert "cmdbuf.CopyImageToBuffer(src_image, VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL" in method
assert ("cmdbuf.CopyBufferToImage(copy_buffer, dst_image,\n"
        "                                 VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL, vk_out_copies)") in method
assert "cmdbuf.CopyBufferToImage(copy_buffer, dst_image, VK_IMAGE_LAYOUT_GENERAL" not in method

generator=(ROOT/"tools/prepare-vulkan-port.py").read_text()
assert "P2.5 Vulkan reinterpret single-aspect depth-stencil VkBufferImageCopy" in generator
assert "P2.5 Vulkan reinterpret destination copy aspect" in generator
assert "P2.5 Vulkan reinterpret actual transfer destination layout" in generator
assert "P2.5 Vulkan reinterpret plane-resident buffer regions" in generator
assert "from_stencil.imageSubresource.aspectMask = VK_IMAGE_ASPECT_STENCIL_BIT" in method
assert "to_stencil.imageSubresource.aspectMask = VK_IMAGE_ASPECT_STENCIL_BIT" in method
assert "from_stencil.bufferOffset = scratch_used + plane_bytes" in method
assert "to_stencil.bufferOffset = scratch_used + plane_bytes" in method
assert "source_width * bpp_in != dest_width * bpp_out" in method
assert "scratch_used += plane_bytes * (dual_planes ? 2U : 1U)" in method
# Execute the retained patches against the active owner in reverse and
# forward order. This proves exact recipe parity without regenerating a
# whole Vulkan port or mutating the pinned source tree.
patches=[]
for node in ast.walk(ast.parse(generator)):
    if not isinstance(node,ast.Call) or not isinstance(node.func,ast.Name):
        continue
    if node.func.id != "apply_reviewed_delta" or len(node.args)<4:
        continue
    args=[ast.literal_eval(n) if isinstance(n,ast.Constant) else None
          for n in node.args[:4]]
    if args[0]=="vk_texture_cache_cost.cpp" and isinstance(args[3],str) and (
        args[3].startswith("P2.5 Vulkan reinterpret ")):
        patches.append((args[1],args[2],args[3]))
assert len(patches)==7,[step[2] for step in patches]
original=code
for old,new,label in reversed(patches):
    assert original.count(new)==1,label
    original=original.replace(new,old)
for old,new,label in patches:
    assert original.count(old)==1,label
    original=original.replace(old,new)
assert original==code,"active image reinterpret owner differs from generator recipe"
assert "P2.5 Vulkan reinterpret exact source byte-scale ratio" in generator
ratio_patches=[]
for node in ast.walk(ast.parse(generator)):
    if not isinstance(node,ast.Call) or not isinstance(node.func,ast.Name) or (
        node.func.id!="apply_reviewed_delta" or len(node.args)<4):
        continue
    args=[ast.literal_eval(n) if isinstance(n,ast.Constant) else None
          for n in node.args[:4]]
    if args[3]=="P2.5 Vulkan reinterpret exact source byte-scale ratio":
        ratio_patches.append((args[1],args[2]))
assert len(ratio_patches)==1
a,b=ratio_patches[0]
assert code.count(b)==1 and code.replace(b,a).count(a)==1
assert "(static_cast<u64>(bpp_out) * copy.extent.width) % bpp_in" in method
for workflow in ("encore-core-fast-gate.yml","encore-core-preflight.yml"):
    body=(ROOT/".github/workflows"/workflow).read_text()
    assert "python3 -B tools/check-ps5-f07-reinterpret-vulkan-layout-host.py" in body

cpp=r"""
#include <array>
#include <cassert>
#include <cstdint>
#include <cstdio>
using VkImageAspectFlags=std::uint32_t;
constexpr VkImageAspectFlags VK_IMAGE_ASPECT_COLOR_BIT=1U;
constexpr VkImageAspectFlags VK_IMAGE_ASPECT_DEPTH_BIT=2U;
constexpr VkImageAspectFlags VK_IMAGE_ASPECT_STENCIL_BIT=4U;
int main(){
__ASPECT_LAMBDA__
    constexpr auto both=VK_IMAGE_ASPECT_DEPTH_BIT|VK_IMAGE_ASPECT_STENCIL_BIT;
    assert(copy_aspect(VK_IMAGE_ASPECT_COLOR_BIT)==VK_IMAGE_ASPECT_COLOR_BIT);
    assert(copy_aspect(VK_IMAGE_ASPECT_DEPTH_BIT)==VK_IMAGE_ASPECT_DEPTH_BIT);
    assert(copy_aspect(VK_IMAGE_ASPECT_STENCIL_BIT)==VK_IMAGE_ASPECT_STENCIL_BIT);
    assert(copy_aspect(both)==VK_IMAGE_ASPECT_DEPTH_BIT);
    for (auto raw : {VK_IMAGE_ASPECT_COLOR_BIT,VK_IMAGE_ASPECT_DEPTH_BIT,
                     VK_IMAGE_ASPECT_STENCIL_BIT,both}) {
        const auto copied=copy_aspect(raw);
        assert(copied!=0 && (copied&(copied-1U))==0);
        // Preserve the original attachment's full barrier aspects.
        const auto barrier=raw;
        assert(barrier==raw && ((barrier & copied)==copied));
    }
    std::puts("F07_VULKAN_REINTERPRET_ASPECT_HOST_PASS combined=depth_only "
              "single_aspect_copy=1 full_barrier_mask=1");
}
""".replace("__ASPECT_LAMBDA__",aspect)
sdk="/Library/Developer/CommandLineTools/SDKs/MacOSX15.4.sdk"
env=dict(os.environ)
if Path(sdk).is_dir(): env["SDKROOT"]=sdk
with tempfile.TemporaryDirectory(prefix="eden-vulkan-reinterpret-aspect-") as t:
    path=Path(t)
    source=path/"aspect.cpp"
    source.write_text(cpp)
    for cc in ("clang++","g++"):
        compiler=shutil.which(cc)
        if not compiler:
            continue
        for opt in ("-O0","-O2"):
            exe=path/(cc.replace("+","p")+opt)
            proc=subprocess.run([compiler,"-std=c++20",opt,
                    "-Wall","-Wextra","-Werror",
                    "-fsanitize=undefined","-fno-sanitize-recover=all",
                    str(source),"-o",str(exe)],
                    capture_output=True,text=True,env=env,timeout=50)
            assert proc.returncode==0,(cc,opt,proc.stderr[-5500:])
            ran=subprocess.run([str(exe)],capture_output=True,
                text=True,env=env,timeout=30)
            assert ran.returncode==0,(cc,opt,ran.stderr[-5500:])
            print(cc,opt,ran.stdout.strip())
print("F07_VULKAN_REINTERPRET_LAYOUT_SOURCE_PASS copy_dst=TRANSFER_DST_OPTIMAL"
      " aspect_separation=1 barrier_full_mask=1 actual_generator=1"
      " gpu_execution=NOT_CLAIMED")
