// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#include <vulkan/vulkan.h>
#include <cstdint>
#include <memory>
namespace ps5::framegen { class interpolator; }
namespace Eden::FeatureLab {
// AMD FSR3 optical-flow derivative, powered by pinned ps5-framegen source.
// No guessed guest depth or motion vectors. Same Vulkan device as renderer.
class Fsr3OpticalSession final {
public:
    Fsr3OpticalSession() = default;
    ~Fsr3OpticalSession();
    Fsr3OpticalSession(const Fsr3OpticalSession&) = delete;
    Fsr3OpticalSession& operator=(const Fsr3OpticalSession&) = delete;
    bool Create(PFN_vkGetInstanceProcAddr proc, VkInstance instance,
                VkPhysicalDevice physical, VkDevice device,
                std::uint32_t width, std::uint32_t height, VkFormat format);
    void Destroy() noexcept;
    bool Ready() const noexcept;
    std::uint32_t Width() const noexcept { return width_; }
    std::uint32_t Height() const noexcept { return height_; }
    VkFormat Format() const noexcept { return format_; }
    // Must run on the serial Vulkan command recording worker, with the
    // source frame held alive until the enclosing Scheduler::Flush.
    bool Record(VkCommandBuffer cmd, VkImage real, VkImage synthetic,
                bool generate) noexcept;
private:
    std::unique_ptr<ps5::framegen::interpolator> engine_;
    VkDevice device_ = VK_NULL_HANDLE;
    std::uint32_t width_ = 0, height_ = 0;
    VkFormat format_ = VK_FORMAT_UNDEFINED;
};
} // namespace Eden::FeatureLab
