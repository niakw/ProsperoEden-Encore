// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#include "mihawk_vulkan_encoder.h"
#include <vulkan/vulkan.h>
#include <cstdint>
#include <string>
namespace Eden::FeatureLab {
struct MihawkSessionCreate {
    PFN_vkGetInstanceProcAddr instance_proc = nullptr;
    VkInstance instance = VK_NULL_HANDLE;
    VkPhysicalDevice physical = VK_NULL_HANDLE;
    VkDevice device = VK_NULL_HANDLE;
    VkFormat compositor_format = VK_FORMAT_UNDEFINED;
    std::uint32_t width = 0, height = 0;
    std::string model_path;
};
class MihawkNativeSession {
public:
    MihawkNativeSession() = default;
    ~MihawkNativeSession();
    MihawkNativeSession(const MihawkNativeSession&) = delete;
    MihawkNativeSession& operator=(const MihawkNativeSession&) = delete;
    bool Create(const MihawkSessionCreate& setup) noexcept;
    void Destroy() noexcept;
    bool Ready() const noexcept { return model_loaded_ && owned_.IsReady() && context_; }
    MihawkVulkanEncoder& Encoder() noexcept { return encoder_; }
    const MihawkVulkanResources& Images() const noexcept { return owned_; }
    MihawkVulkanResources& Images() noexcept { return owned_; }
    fg_context* Context() const noexcept { return context_; }
    bool OutputWasBlitted() const noexcept { return output_was_blitted_; }
    void MarkOutputBlitted() noexcept { output_was_blitted_ = true; }
    std::uint32_t DescriptorSlots() const noexcept { return 1; }
    MihawkEncoderImages CaptureImages() const noexcept {
        return MihawkEncoderImages::FromOwned(owned_);
    }
private:
    fg_context* context_ = nullptr;
    bool model_loaded_ = false;
    bool output_was_blitted_ = false;
    MihawkVulkanResources owned_{};
    MihawkVulkanEncoder encoder_{};
};
} // namespace Eden::FeatureLab
