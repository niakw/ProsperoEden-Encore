#!/usr/bin/env python3
"""N73: compile exact vendor cache admission and audit native integration."""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
vendor = ROOT / "vendor/encore-active"
entry = vendor / "eden-vulkan/vk_texture_cache_cost.cpp"
hdr = vendor / "ns2-astc/include/video_core/renderer_vulkan/vk_texture_cache.h"
source = entry.read_text(encoding="utf-8")
header = hdr.read_text(encoding="utf-8")
begin = "// NS2 N73 BEGIN: one real cache-side VkImage sparse admission/bind/retire probe."
end = "// NS2 N73 END"
assert source.count(begin) == source.count(end) == 1
chunk = source[source.index(begin):source.index(end)]
for item in (
    "memory_allocator.CreateSparseImage(image_ci)",
    "logical.GetImageMemoryRequirements(*candidate)",
    "logical.GetSparseImageMemoryRequirements(*candidate)",
    "AdmitSparseCacheImage(",
    "SparseBindOwner<MemoryAllocator>",
    "owner.Bind(",
    "scheduler, fence",
    "owner.RetireAfterDeviceIdle(",
    "candidate = {};",
):
    assert item in chunk, (item, "native sparse cache owner drift")
assert header.count("ProbeSparseImage(const VideoCommon::ImageInfo& info)") == 1
assert "#ifdef EDEN_NS2_SPARSE_CACHE_PROBE" in chunk
assert "original_image(MakeImage(" in source   # standard game images remain dense
assert "return allocator.CreateImage(image_ci);" in source

stub = r"""
#pragma once
#include <cstdint>
using VkFlags = std::uint32_t;
using VkDeviceSize = std::uint64_t;
using VkImageCreateFlags = VkFlags;
using VkImageUsageFlags = VkFlags;
using VkImageAspectFlags = VkFlags;
using VkSparseImageFormatFlags = VkFlags;
constexpr VkFlags VK_IMAGE_CREATE_CUBE_COMPATIBLE_BIT=1u<<0;
constexpr VkFlags VK_IMAGE_CREATE_MUTABLE_FORMAT_BIT=1u<<1;
constexpr VkFlags VK_IMAGE_CREATE_EXTENDED_USAGE_BIT=1u<<2;
constexpr VkFlags VK_IMAGE_CREATE_ALIAS_BIT=1u<<3;
constexpr VkFlags VK_IMAGE_USAGE_SAMPLED_BIT=1u<<0;
constexpr VkFlags VK_IMAGE_USAGE_TRANSFER_DST_BIT=1u<<1;
constexpr VkFlags VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT=1u<<2;
constexpr VkFlags VK_IMAGE_USAGE_DEPTH_STENCIL_ATTACHMENT_BIT=1u<<3;
constexpr VkFlags VK_IMAGE_USAGE_STORAGE_BIT=1u<<4;
constexpr VkFlags VK_IMAGE_ASPECT_COLOR_BIT=1u<<0;
constexpr VkFlags VK_SPARSE_IMAGE_FORMAT_SINGLE_MIPTAIL_BIT=1u<<0;
constexpr VkFlags VK_SPARSE_IMAGE_FORMAT_NONSTANDARD_BLOCK_SIZE_BIT=1u<<1;
constexpr VkFlags VK_SPARSE_IMAGE_FORMAT_ALIGNED_MIP_SIZE_BIT=1u<<2;
constexpr auto VK_IMAGE_TYPE_2D=1U;
constexpr auto VK_IMAGE_TILING_OPTIMAL=1U;
constexpr auto VK_SAMPLE_COUNT_1_BIT=1U;
struct VkExtent3D {std::uint32_t width{},height{},depth{};};
struct VkImageCreateInfo {
 std::uint32_t sType{};const void* pNext{};VkImageCreateFlags flags{};
 std::uint32_t imageType{},format{};
 VkExtent3D extent{};
 std::uint32_t mipLevels{},arrayLayers{},samples{},tiling{};
 VkImageUsageFlags usage{};
};
struct VkMemoryRequirements {
 VkDeviceSize size{},alignment{};
 std::uint32_t memoryTypeBits{};
};
struct VkSparseImageFormatProperties {
 VkImageAspectFlags aspectMask{};
 VkExtent3D imageGranularity{};
 VkSparseImageFormatFlags flags{};
};
struct VkSparseImageMemoryRequirements {
 VkSparseImageFormatProperties formatProperties{};
 std::uint32_t imageMipTailFirstLod{};
 VkDeviceSize imageMipTailSize{},imageMipTailOffset{},imageMipTailStride{};
};
"""
cpp = r"""
#include <cassert>
#include <cstdio>
#include "video_core/renderer_vulkan/ns2_sparse_cache_admission.h"
using namespace Eden::NS2::Cache;
static VkImageCreateInfo Image() {
 VkImageCreateInfo ci{};
 ci.imageType=VK_IMAGE_TYPE_2D;
 ci.extent={256,256,1};
 ci.mipLevels=2;ci.arrayLayers=4;ci.samples=VK_SAMPLE_COUNT_1_BIT;
 ci.tiling=VK_IMAGE_TILING_OPTIMAL;
 ci.usage=VK_IMAGE_USAGE_SAMPLED_BIT|VK_IMAGE_USAGE_TRANSFER_DST_BIT;
 return ci;
}
static VkMemoryRequirements Memory() {
 return {16ULL*1024*1024,65536,7};
}
static VkSparseImageMemoryRequirements Sparse() {
 VkSparseImageMemoryRequirements r{};
 r.formatProperties.aspectMask=VK_IMAGE_ASPECT_COLOR_BIT;
 r.formatProperties.imageGranularity={64,64,1};
 r.imageMipTailFirstLod=1;
 r.imageMipTailSize=65536;
 r.imageMipTailOffset=12ULL*1024*1024;
 r.imageMipTailStride=65536;
 return r;
}
int main() {
 auto ci=Image();auto mem=Memory();
 auto sparse=std::vector<VkSparseImageMemoryRequirements>{Sparse()};
 auto a=AdmitSparseCacheImage(ci,mem,sparse,6ULL<<30,true);
 assert(a.Accepted());
 assert(a.complete_layers.size()==4 && a.complete_layers[0]==0 &&
        a.complete_layers[3]==3);
 assert(a.spec.layers==4 && a.spec.tail_first_lod==1);
 assert(a.resident_bytes==17ULL*65536*4);
 assert(!AdmitSparseCacheImage(ci,mem,sparse,6ULL<<30,false).Accepted());
 ci.usage=VK_IMAGE_USAGE_SAMPLED_BIT;
 assert(AdmitSparseCacheImage(ci,mem,sparse,6ULL<<30,true).rejection==
        SparseCacheReject::UnsupportedImage);
 ci=Image();ci.usage|=VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT;
 assert(!AdmitSparseCacheImage(ci,mem,sparse,6ULL<<30,true).Accepted());
 ci=Image();ci.flags|=VK_IMAGE_CREATE_MUTABLE_FORMAT_BIT;
 assert(!AdmitSparseCacheImage(ci,mem,sparse,6ULL<<30,true).Accepted());
 ci=Image();
 mem.memoryTypeBits=0;
 assert(!AdmitSparseCacheImage(ci,mem,sparse,6ULL<<30,true).Accepted());
 mem=Memory();
 sparse.push_back(Sparse());sparse[1].formatProperties.aspectMask=2;
 assert(AdmitSparseCacheImage(ci,mem,sparse,6ULL<<30,true).rejection==
        SparseCacheReject::UnsupportedAspect);
 sparse={Sparse()};
 sparse[0].formatProperties.flags=VK_SPARSE_IMAGE_FORMAT_NONSTANDARD_BLOCK_SIZE_BIT;
 assert(!AdmitSparseCacheImage(ci,mem,sparse,6ULL<<30,true).Accepted());
 sparse={Sparse()};
 ci.arrayLayers=4096;
 assert(!AdmitSparseCacheImage(ci,mem,sparse,6ULL<<30,true).Accepted());
 ci=Image();
 sparse[0].formatProperties.flags=VK_SPARSE_IMAGE_FORMAT_SINGLE_MIPTAIL_BIT;
 sparse[0].imageMipTailStride=0;
 auto shared=AdmitSparseCacheImage(ci,mem,sparse,6ULL<<30,true);
 assert(shared.Accepted() && shared.complete_layers.size()==4);
 assert(shared.resident_bytes==16ULL*65536*4+65536);
 std::puts("N73_REAL_VENDOR_CACHE_ADMISSION_PASS");
}
"""
with tempfile.TemporaryDirectory(prefix="ns2-n73-cache-") as temporary:
    root=Path(temporary)
    (root/"vulkan").mkdir()
    (root/"vulkan/vulkan_core.h").write_text(stub,encoding="utf-8")
    sourcefile=root/"admission.cpp"
    sourcefile.write_text(cpp,encoding="utf-8")
    for compiler in ("clang++","g++"):
        exe=root/compiler.replace("+","p")
        subprocess.run([
            compiler,"-std=c++20","-O2","-Wall","-Wextra","-Werror",
            "-fsanitize=undefined","-fno-sanitize-recover=all",
            "-I",str(root),
            "-I",str(vendor/"ns2-helpers/include"),
            str(sourcefile),"-o",str(exe),
        ],check=True)
        subprocess.run([str(exe)],check=True)
print("N73_NATIVE_CACHE_ADMISSION_CLANG_GCC_UBSAN_PASS")
