// SPDX-License-Identifier: GPL-3.0-or-later
// No GPU: mocked allocation, format support, and lifetime failure paths.
#include "mihawk_vulkan_resources.h"
#include <cassert>
#include <cstdint>
#include <type_traits>

namespace {
int created = 0, views = 0, allocations = 0, bound = 0;
int destroyed = 0, destroyed_views = 0, freed = 0, waited = 0;
int fail_image_at = 0, fail_view_at = 0, fail_mem_at = 0, fail_bind_at = 0;
bool permit_format = true, permit_local = true;

template<typename T> T H(std::uintptr_t x) {
    if constexpr (std::is_pointer_v<T>) return reinterpret_cast<T>(x);
    else return static_cast<T>(x);
}
void Reset() {
    created = views = allocations = bound = 0;
    destroyed = destroyed_views = freed = waited = 0;
    fail_image_at = fail_view_at = fail_mem_at = fail_bind_at = 0;
    permit_format = permit_local = true;
}
}

extern "C" VKAPI_ATTR void VKAPI_CALL vkGetPhysicalDeviceFormatProperties(
    VkPhysicalDevice, VkFormat, VkFormatProperties* props) {
    *props = {};
    props->optimalTilingFeatures = permit_format ?
        VK_FORMAT_FEATURE_SAMPLED_IMAGE_BIT | VK_FORMAT_FEATURE_TRANSFER_DST_BIT |
        VK_FORMAT_FEATURE_TRANSFER_SRC_BIT | VK_FORMAT_FEATURE_STORAGE_IMAGE_BIT |
        VK_FORMAT_FEATURE_BLIT_SRC_BIT | VK_FORMAT_FEATURE_BLIT_DST_BIT : 0U;
}
extern "C" VKAPI_ATTR void VKAPI_CALL vkGetPhysicalDeviceMemoryProperties(
    VkPhysicalDevice, VkPhysicalDeviceMemoryProperties* props) {
    *props = {};
    props->memoryTypeCount = 2;
    props->memoryTypes[0].propertyFlags = VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT;
    props->memoryTypes[1].propertyFlags =
        permit_local ? VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT : VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT;
}
extern "C" VKAPI_ATTR VkResult VKAPI_CALL vkCreateImage(
    VkDevice, const VkImageCreateInfo* info, const VkAllocationCallbacks*, VkImage* image) {
    assert(info && info->extent.width == 1920 && info->extent.height == 1080);
    assert(info->format == VK_FORMAT_R8G8B8A8_UNORM ||
           info->format == VK_FORMAT_B8G8R8A8_UNORM);
    ++created;
    if (created == fail_image_at) {
        *image = H<VkImage>(0xdead); // failed output is untrusted
        return VK_ERROR_OUT_OF_DEVICE_MEMORY;
    }
    *image = H<VkImage>(0x100 + created);
    return VK_SUCCESS;
}
extern "C" VKAPI_ATTR void VKAPI_CALL vkGetImageMemoryRequirements(
    VkDevice, VkImage, VkMemoryRequirements* r) {
    *r = {};
    r->size = 8u * 1024 * 1024;
    r->alignment = 256;
    r->memoryTypeBits = 3;
}
extern "C" VKAPI_ATTR VkResult VKAPI_CALL vkAllocateMemory(
    VkDevice, const VkMemoryAllocateInfo* info, const VkAllocationCallbacks*,
    VkDeviceMemory* memory) {
    assert(info && info->allocationSize == 8u * 1024 * 1024);
    assert(info->memoryTypeIndex == 1);
    ++allocations;
    if (allocations == fail_mem_at) {
        *memory = H<VkDeviceMemory>(0xbeef);
        return VK_ERROR_OUT_OF_DEVICE_MEMORY;
    }
    *memory = H<VkDeviceMemory>(0x200 + allocations);
    return VK_SUCCESS;
}
extern "C" VKAPI_ATTR VkResult VKAPI_CALL vkBindImageMemory(
    VkDevice, VkImage, VkDeviceMemory, VkDeviceSize offset) {
    assert(offset == 0);
    ++bound;
    return bound == fail_bind_at ? VK_ERROR_OUT_OF_DEVICE_MEMORY : VK_SUCCESS;
}
extern "C" VKAPI_ATTR VkResult VKAPI_CALL vkCreateImageView(
    VkDevice, const VkImageViewCreateInfo* info, const VkAllocationCallbacks*,
    VkImageView* view) {
    assert(info && info->subresourceRange.aspectMask == VK_IMAGE_ASPECT_COLOR_BIT);
    ++views;
    if (views == fail_view_at) {
        *view = H<VkImageView>(0xcafe);
        return VK_ERROR_OUT_OF_DEVICE_MEMORY;
    }
    *view = H<VkImageView>(0x300 + views);
    return VK_SUCCESS;
}
extern "C" VKAPI_ATTR void VKAPI_CALL vkDestroyImageView(
    VkDevice, VkImageView v, const VkAllocationCallbacks*) {
    assert(v != H<VkImageView>(0xcafe));
    ++destroyed_views;
}
extern "C" VKAPI_ATTR void VKAPI_CALL vkDestroyImage(
    VkDevice, VkImage i, const VkAllocationCallbacks*) {
    assert(i != H<VkImage>(0xdead));
    ++destroyed;
}
extern "C" VKAPI_ATTR void VKAPI_CALL vkFreeMemory(
    VkDevice, VkDeviceMemory m, const VkAllocationCallbacks*) {
    assert(m != H<VkDeviceMemory>(0xbeef));
    ++freed;
}
extern "C" VKAPI_ATTR VkResult VKAPI_CALL vkDeviceWaitIdle(VkDevice) {
    ++waited;
    return VK_SUCCESS;
}
int main() {
    using namespace Eden::FeatureLab;
    const auto device = H<VkDevice>(0x1);
    const auto physical = H<VkPhysicalDevice>(0x2);
    Reset();
    {
        MihawkVulkanResources images;
        assert(images.Create(device, physical, 1920, 1080,
                             VK_FORMAT_B8G8R8A8_UNORM) == MihawkAllocateError::None);
        assert(images.IsReady());
        assert(images.Generation() == 1);
        assert(images.SourceFormat() == VK_FORMAT_B8G8R8A8_UNORM);
        assert(images.AllocatedBytes() == 24u * 1024 * 1024);
        assert(images.History(0).image != images.History(1).image);
        assert(images.RgbaOutput().image != images.History(0).image);
        assert(images.Create(device, physical, 1920, 1080,
                             VK_FORMAT_R8G8B8A8_UNORM) == MihawkAllocateError::AlreadyAllocated);
        images.MarkInitialized(0);
        assert(images.Initialized(0) && !images.Initialized(1));
        images.ResetHistory();
        assert(!images.Initialized(0));
    }
    assert(created == 3 && destroyed == 3);
    assert(allocations == 3 && freed == 3 && views == 3 && destroyed_views == 3);
    assert(waited == 1);

    Reset();
    {
        MihawkVulkanResources images;
        permit_format = false;
        assert(images.Create(device, physical, 1920, 1080,
                             VK_FORMAT_R8G8B8A8_UNORM) == MihawkAllocateError::UnsupportedFormat);
        assert(created == 0);
        permit_format = true;
        assert(images.Create(device, physical, 1920, 1080,
                             VK_FORMAT_R8G8B8A8_UNORM, 16u*1024*1024) ==
               MihawkAllocateError::ExcessiveMemory);
        assert(!images.IsReady() && destroyed == 3 && freed == 2 && waited == 0);
    }

    Reset();
    permit_local = false;
    {
        MihawkVulkanResources images;
        assert(images.Create(device, physical, 1920, 1080,
                             VK_FORMAT_R8G8B8A8_UNORM) == MihawkAllocateError::NoDeviceLocalMemory);
        assert(created == 1 && destroyed == 1 && freed == 0 && waited == 0);
    }

    Reset();
    fail_image_at = 2;
    {
        MihawkVulkanResources images;
        assert(images.Create(device, physical, 1920, 1080,
                             VK_FORMAT_R8G8B8A8_UNORM) == MihawkAllocateError::ImageCreationFailed);
        assert(created == 2 && destroyed == 1 && freed == 1);
    }
    Reset();
    fail_mem_at = 2;
    {
        MihawkVulkanResources images;
        assert(images.Create(device, physical, 1920, 1080,
                             VK_FORMAT_R8G8B8A8_UNORM) == MihawkAllocateError::AllocationFailed);
        assert(created == 2 && destroyed == 2 && freed == 1);
    }
    Reset();
    fail_view_at = 2;
    {
        MihawkVulkanResources images;
        assert(images.Create(device, physical, 1920, 1080,
                             VK_FORMAT_R8G8B8A8_UNORM) == MihawkAllocateError::ViewCreationFailed);
        assert(created == 2 && destroyed == 2 && freed == 2 && destroyed_views == 1);
    }
}
