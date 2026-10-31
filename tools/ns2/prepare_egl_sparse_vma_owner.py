# SPDX-License-Identifier: GPL-3.0-or-later
"""Generate opt-in PS5 VMA sparse memory allocation owner, leaving vendor unchanged."""
from pathlib import Path
import argparse

def single(content,anchor,replacement):
    if content.count(anchor)!=1:
        raise RuntimeError("N62 pinned PS5 memory owner changed: "+anchor[:100])
    return content.replace(anchor,replacement)

def adapt(header,body):
    header=single(header,'''        vk::Image CreateImage(const VkImageCreateInfo &ci) const;''',
'''        vk::Image CreateImage(const VkImageCreateInfo &ci) const;

        // N62 research: a single device-local chunk for sparse Vulkan
        // image tiles or mip tails. Caller owns GPU/fence lifetime.
        struct SparseMemoryAllocation {
            VmaAllocation allocation{};
            VkDeviceMemory memory{};
            VkDeviceSize offset{};
        };
        [[nodiscard]] bool AllocateSparseMemory(
            const VkMemoryRequirements &requirements, SparseMemoryAllocation &result) const noexcept;
        void ReleaseSparseMemory(SparseMemoryAllocation &allocation) const noexcept;''')
    body=single(body,'''vk::Buffer MemoryAllocator::CreateBuffer(const VkBufferCreateInfo &ci, MemoryUsage usage) const {''',
'''bool MemoryAllocator::AllocateSparseMemory(
    const VkMemoryRequirements &requirements, SparseMemoryAllocation &out) const noexcept {
    // Do not overwrite a live token. Always use VMA's *within budget*
    // allocation; never call vkAllocateMemory outside the native allocator.
    if (out.allocation || requirements.size == 0 ||
        requirements.alignment == 0 ||
        (requirements.alignment & (requirements.alignment - 1)) != 0 ||
        requirements.memoryTypeBits == 0) {
        return false;
    }
    VmaAllocationCreateInfo create{};
    create.flags = VMA_ALLOCATION_CREATE_WITHIN_BUDGET_BIT;
    create.usage = VMA_MEMORY_USAGE_AUTO_PREFER_DEVICE;
    create.requiredFlags = VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT;
    create.memoryTypeBits = requirements.memoryTypeBits;
    VmaAllocation allocation{};
    VmaAllocationInfo info{};
    const VkResult result = vmaAllocateMemory(
        allocator, &requirements, &create, &allocation, &info);
    if (result != VK_SUCCESS || !allocation || !info.deviceMemory) {
        // Some drivers return an allocation token even when the bindable
        // memory handle is missing; never leak that partial allocation.
        if (allocation) {
            vmaFreeMemory(allocator, allocation);
        }
        return false;
    }
    out = SparseMemoryAllocation{allocation, info.deviceMemory, info.offset};
    return true;
}

void MemoryAllocator::ReleaseSparseMemory(SparseMemoryAllocation &token) const noexcept {
    // The caller must first wait for the sparse queue / GPU to retire.
    if (token.allocation) {
        vmaFreeMemory(allocator, token.allocation);
    }
    token = {};
}

vk::Buffer MemoryAllocator::CreateBuffer(const VkBufferCreateInfo &ci, MemoryUsage usage) const {''')
    return header,body
def main():
    ap=argparse.ArgumentParser()
    for arg in ('header','source','output'):ap.add_argument('--'+arg,required=True)
    v=ap.parse_args()
    h,c=adapt(Path(v.header).read_text(),Path(v.source).read_text())
    root=Path(v.output)
    p=root/'include/video_core/vulkan_common/vulkan_memory_allocator.h'
    q=root/'vulkan_memory_allocator.cpp'
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(h);q.write_text(c)
    print('N62_NATIVE_VMA_SPARSE_MEMORY_OWNER_GENERATED')
if __name__=='__main__': main()
