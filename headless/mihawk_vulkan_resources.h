// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
// R08 private history and output resources. Offline by default: not linked to
// Encore's actual renderer until presentation lifetime and HUD are qualified.
#include <vulkan/vulkan.h>
#include <array>
#include <cstdint>

namespace Eden::FeatureLab {

enum class MihawkAllocateError : std::uint8_t {
    None, AlreadyAllocated, InvalidArguments, UnsupportedFormat,
    ExcessiveMemory, NoDeviceLocalMemory, ImageCreationFailed,
    AllocationFailed, BindFailed, ViewCreationFailed
};

struct MihawkOwnedImage {
    VkImage image = VK_NULL_HANDLE;
    VkImageView view = VK_NULL_HANDLE;
    VkDeviceMemory memory = VK_NULL_HANDLE;
    VkDeviceSize allocation_size = 0;
};

// Resource lifetime must be shorter than VkDevice lifetime. Destruction
// synchronizes (vkDeviceWaitIdle) before releasing GPU memory; never call
// Destroy from the 60 Hz render loop.
class MihawkVulkanResources {
public:
    MihawkVulkanResources() = default;
    ~MihawkVulkanResources();
    MihawkVulkanResources(const MihawkVulkanResources&) = delete;
    MihawkVulkanResources& operator=(const MihawkVulkanResources&) = delete;
    MihawkVulkanResources(MihawkVulkanResources&&) = delete;
    MihawkVulkanResources& operator=(MihawkVulkanResources&&) = delete;

    MihawkAllocateError Create(VkDevice device, VkPhysicalDevice physical,
                               std::uint32_t width, std::uint32_t height,
                               VkFormat compositor_format,
                               VkDeviceSize max_allocation_bytes = 128ull * 1024 * 1024);
    void Destroy() noexcept;
    void ResetHistory() noexcept { initialized_ = {}; }

    bool IsReady() const noexcept { return ready_; }
    const MihawkOwnedImage& History(std::uint32_t slot) const noexcept {
        return images_[slot % 2];
    }
    const MihawkOwnedImage& RgbaOutput() const noexcept { return images_[2]; }
    bool Initialized(std::uint32_t slot) const noexcept { return initialized_[slot % 2]; }
    void MarkInitialized(std::uint32_t slot) noexcept { initialized_[slot % 2] = true; }
    VkFormat SourceFormat() const noexcept { return source_format_; }
    VkDeviceSize AllocatedBytes() const noexcept { return total_bytes_; }
    std::uint32_t Width() const noexcept { return width_; }
    std::uint32_t Height() const noexcept { return height_; }

private:
    bool CreateImage(std::uint32_t slot, VkFormat format, VkImageUsageFlags usage,
                     VkDeviceSize budget, const VkPhysicalDeviceMemoryProperties& types,
                     MihawkAllocateError& error) noexcept;
    void ReleaseImages() noexcept;
    std::array<MihawkOwnedImage, 3> images_{};
    std::array<bool, 2> initialized_{};
    VkDevice device_ = VK_NULL_HANDLE;
    VkFormat source_format_ = VK_FORMAT_UNDEFINED;
    std::uint32_t width_ = 0, height_ = 0;
    VkDeviceSize total_bytes_ = 0;
    bool ready_ = false;
};

} // namespace Eden::FeatureLab
