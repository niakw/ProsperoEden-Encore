#!/usr/bin/env python3
"""N64: preserve native PS5 VMA allocator; add opt-in sparse VkImage factory."""
import argparse
from pathlib import Path
def replace(src,anchor,body):
    if src.count(anchor)!=1:
        raise RuntimeError("N64 exact native PS5 image source owner drift: "+anchor[:100])
    return src.replace(anchor,body)
def generate(header,code):
    anchor='''        vk::Image CreateImage(const VkImageCreateInfo &ci) const;'''
    header=replace(header,anchor,anchor+'''

        // N64: sparse 2D array image without full backing. GPU queue binds
        // and fence retirement are the caller's responsibility.
        [[nodiscard]] vk::Image CreateSparseImage(const VkImageCreateInfo &ci) const;''')
    anchor='''bool MemoryAllocator::AllocateSparseMemory('''
    body='''vk::Image MemoryAllocator::CreateSparseImage(const VkImageCreateInfo &ci) const {
    // No sparse image may be created unless the actual selected graphics
    // queue and device expose sparse residency for 2D images (N58).
    if (!device.IsSparseResidencyImage2DSupported() ||
        ci.imageType != VK_IMAGE_TYPE_2D || ci.arrayLayers <= 1 ||
        ci.mipLevels == 0 || ci.samples != VK_SAMPLE_COUNT_1_BIT ||
        ci.tiling != VK_IMAGE_TILING_OPTIMAL ||
        ci.extent.width == 0 || ci.extent.height == 0 || ci.extent.depth != 1) {
        return {};
    }
    // PS5 Vulkan shim can leave optional entry points unbound.
    if (!device.GetDispatchLoader().vkCreateImage ||
        !device.GetDispatchLoader().vkDestroyImage) {
        return {};
    }
    VkImageCreateInfo sparse_ci = ci;
    sparse_ci.flags |= VK_IMAGE_CREATE_SPARSE_BINDING_BIT |
                       VK_IMAGE_CREATE_SPARSE_RESIDENCY_BIT;
    VkImage image{};
    const auto result = device.GetDispatchLoader().vkCreateImage(
        *device.GetLogical(), &sparse_ci, nullptr, &image);
    if (result != VK_SUCCESS || !image) {
        // An unsuccessful driver call may still produce a non-null handle.
        if (image) {
            device.GetDispatchLoader().vkDestroyImage(
                *device.GetLogical(), image, nullptr);
        }
        return {};
    }
    // The pinned vk::Image RAII wrapper calls vmaDestroyImage. VMA documents
    // allocation == null as a valid destroy-only image. Do not allocate full
    // image backing here; N62 allocates page/tail memory separately.
    return vk::Image(image, sparse_ci.usage, *device.GetLogical(), allocator,
                     VK_NULL_HANDLE, device.GetDispatchLoader());
}

'''
    return header,replace(code,anchor,body+anchor)
def main():
    p=argparse.ArgumentParser()
    for a in ('header','source','output'):p.add_argument('--'+a,required=True)
    x=p.parse_args()
    h,c=generate(Path(x.header).read_text(),Path(x.source).read_text())
    root=Path(x.output)
    hp=root/'include/video_core/vulkan_common/vulkan_memory_allocator.h'
    cp=root/'vulkan_memory_allocator.cpp'
    hp.parent.mkdir(parents=True,exist_ok=True)
    hp.write_text(h);cp.write_text(c)
    print("N64_NATIVE_PS5_SPARSE_IMAGE_OWNER_GENERATED")
if __name__=="__main__":main()
