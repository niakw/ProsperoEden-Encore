// SPDX-License-Identifier: GPL-3.0-or-later
#include "mihawk_vulkan_resources.h"

#include <limits>

namespace Eden::FeatureLab {
namespace {
bool Supports(VkPhysicalDevice physical, VkFormat format,
              VkFormatFeatureFlags required) noexcept {
    VkFormatProperties properties{};
    vkGetPhysicalDeviceFormatProperties(physical, format, &properties);
    return (properties.optimalTilingFeatures & required) == required;
}

int DeviceLocalIndex(const VkPhysicalDeviceMemoryProperties& props,
                     std::uint32_t bits) noexcept {
    for (std::uint32_t i = 0; i < props.memoryTypeCount; ++i) {
        if ((bits & (1U << i)) &&
            (props.memoryTypes[i].propertyFlags & VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT))
            return static_cast<int>(i);
    }
    return -1;
}
} // namespace

MihawkVulkanResources::~MihawkVulkanResources() {
    Destroy();
}

void MihawkVulkanResources::ReleaseImages() noexcept {
    if (!device_) return;
    for (auto& image : images_) {
        if (image.view) vkDestroyImageView(device_, image.view, nullptr);
        if (image.image) vkDestroyImage(device_, image.image, nullptr);
        if (image.memory) vkFreeMemory(device_, image.memory, nullptr);
        image = {};
    }
    ready_ = false;
    initialized_ = {};
    total_bytes_ = 0;
}

void MihawkVulkanResources::Destroy() noexcept {
    if (device_) {
        // Safe when this object's containing renderer owns device_. The app
        // must destroy this *before* destroying VkDevice.
        (void)vkDeviceWaitIdle(device_);
        ReleaseImages();
    }
    device_ = VK_NULL_HANDLE;
    source_format_ = VK_FORMAT_UNDEFINED;
    width_ = height_ = 0;
}

bool MihawkVulkanResources::CreateImage(
    std::uint32_t slot, VkFormat format, VkImageUsageFlags usage,
    VkDeviceSize budget, const VkPhysicalDeviceMemoryProperties& types,
    MihawkAllocateError& error) noexcept {
    auto& out = images_[slot];
    VkImageCreateInfo image{};
    image.sType = VK_STRUCTURE_TYPE_IMAGE_CREATE_INFO;
    image.imageType = VK_IMAGE_TYPE_2D;
    image.format = format;
    image.extent = {width_, height_, 1};
    image.mipLevels = 1;
    image.arrayLayers = 1;
    image.samples = VK_SAMPLE_COUNT_1_BIT;
    image.tiling = VK_IMAGE_TILING_OPTIMAL;
    image.usage = usage;
    image.sharingMode = VK_SHARING_MODE_EXCLUSIVE;
    image.initialLayout = VK_IMAGE_LAYOUT_UNDEFINED;

    VkImage created_image = VK_NULL_HANDLE;
    if (vkCreateImage(device_, &image, nullptr, &created_image) != VK_SUCCESS) {
        error = MihawkAllocateError::ImageCreationFailed;
        return false;
    }
    out.image = created_image;
    VkMemoryRequirements requirements{};
    vkGetImageMemoryRequirements(device_, out.image, &requirements);
    if (requirements.size == 0 || requirements.size > budget - total_bytes_) {
        error = MihawkAllocateError::ExcessiveMemory;
        return false;
    }
    const int index = DeviceLocalIndex(types, requirements.memoryTypeBits);
    if (index < 0) {
        error = MihawkAllocateError::NoDeviceLocalMemory;
        return false;
    }
    VkMemoryAllocateInfo allocate{};
    allocate.sType = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO;
    allocate.allocationSize = requirements.size;
    allocate.memoryTypeIndex = static_cast<std::uint32_t>(index);
    VkDeviceMemory allocated_memory = VK_NULL_HANDLE;
    if (vkAllocateMemory(device_, &allocate, nullptr, &allocated_memory) != VK_SUCCESS) {
        error = MihawkAllocateError::AllocationFailed;
        return false;
    }
    out.memory = allocated_memory;
    out.allocation_size = requirements.size;
    total_bytes_ += requirements.size;
    if (vkBindImageMemory(device_, out.image, out.memory, 0) != VK_SUCCESS) {
        error = MihawkAllocateError::BindFailed;
        return false;
    }

    VkImageViewCreateInfo view{};
    view.sType = VK_STRUCTURE_TYPE_IMAGE_VIEW_CREATE_INFO;
    view.image = out.image;
    view.viewType = VK_IMAGE_VIEW_TYPE_2D;
    view.format = format;
    view.components = {VK_COMPONENT_SWIZZLE_IDENTITY, VK_COMPONENT_SWIZZLE_IDENTITY,
                       VK_COMPONENT_SWIZZLE_IDENTITY, VK_COMPONENT_SWIZZLE_IDENTITY};
    view.subresourceRange.aspectMask = VK_IMAGE_ASPECT_COLOR_BIT;
    view.subresourceRange.levelCount = 1;
    view.subresourceRange.layerCount = 1;
    VkImageView created_view = VK_NULL_HANDLE;
    if (vkCreateImageView(device_, &view, nullptr, &created_view) != VK_SUCCESS) {
        error = MihawkAllocateError::ViewCreationFailed;
        return false;
    }
    out.view = created_view;
    return true;
}

MihawkAllocateError MihawkVulkanResources::Create(
    VkDevice device, VkPhysicalDevice physical, std::uint32_t width,
    std::uint32_t height, VkFormat compositor_format,
    VkDeviceSize max_allocation_bytes) {
    if (device_ || ready_) return MihawkAllocateError::AlreadyAllocated;
    // The first native implementation does not authorize 8K interpolation.
    // 4K+ or unsupported extents fail before allocating anything.
    if (!device || !physical || !width || !height ||
        width > 3840 || height > 2160 ||
        max_allocation_bytes < 1ull * 1024 * 1024 ||
        max_allocation_bytes > 512ull * 1024 * 1024)
        return MihawkAllocateError::InvalidArguments;
    if (compositor_format != VK_FORMAT_R8G8B8A8_UNORM &&
        compositor_format != VK_FORMAT_B8G8R8A8_UNORM)
        return MihawkAllocateError::UnsupportedFormat;
    const VkFormatFeatureFlags history_features =
        VK_FORMAT_FEATURE_SAMPLED_IMAGE_BIT | VK_FORMAT_FEATURE_TRANSFER_DST_BIT |
        VK_FORMAT_FEATURE_TRANSFER_SRC_BIT;
    const VkFormatFeatureFlags rgba_features =
        VK_FORMAT_FEATURE_STORAGE_IMAGE_BIT | VK_FORMAT_FEATURE_BLIT_SRC_BIT;
    if (!Supports(physical, compositor_format, history_features) ||
        !Supports(physical, compositor_format, VK_FORMAT_FEATURE_BLIT_DST_BIT) ||
        !Supports(physical, VK_FORMAT_R8G8B8A8_UNORM, rgba_features))
        return MihawkAllocateError::UnsupportedFormat;

    VkPhysicalDeviceMemoryProperties types{};
    vkGetPhysicalDeviceMemoryProperties(physical, &types);
    device_ = device;
    width_ = width;
    height_ = height;
    source_format_ = compositor_format;

    MihawkAllocateError error = MihawkAllocateError::None;
    for (std::uint32_t i = 0; i < 3; ++i) {
        const VkFormat fmt = i == 2 ? VK_FORMAT_R8G8B8A8_UNORM : compositor_format;
        const VkImageUsageFlags usage =
            i == 2 ? (VK_IMAGE_USAGE_STORAGE_BIT | VK_IMAGE_USAGE_TRANSFER_SRC_BIT)
                   : (VK_IMAGE_USAGE_SAMPLED_BIT | VK_IMAGE_USAGE_TRANSFER_DST_BIT);
        if (!CreateImage(i, fmt, usage, max_allocation_bytes, types, error)) {
            // No GPU commands have been submitted: these allocations can be
            // destroyed immediately. Do not keep partial/stale resources.
            ReleaseImages();
            device_ = VK_NULL_HANDLE;
            source_format_ = VK_FORMAT_UNDEFINED;
            width_ = height_ = 0;
            return error;
        }
    }
    ++generation_;
    ready_ = true;
    return MihawkAllocateError::None;
}
} // namespace Eden::FeatureLab
