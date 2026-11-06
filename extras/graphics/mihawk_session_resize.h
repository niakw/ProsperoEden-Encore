// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
// Device/session switch handling independent of the PS5 render thread.
// A Vulkan image group is keyed by extent AND composition format.
#include <vulkan/vulkan.h>
#include <cstdint>

namespace Eden::FeatureLab {

enum class MihawkSessionAction : std::uint8_t {
    Keep, Initialize, RecreateAfterGpuIdle, InvalidTarget
};

constexpr MihawkSessionAction ChooseMihawkSessionAction(
    bool session_ready, std::uint32_t old_width, std::uint32_t old_height,
    VkFormat old_format, std::uint32_t new_width, std::uint32_t new_height,
    VkFormat new_format) noexcept {
    if (!new_width || !new_height || new_width > 3840 || new_height > 2160 ||
        (new_format != VK_FORMAT_R8G8B8A8_UNORM &&
         new_format != VK_FORMAT_B8G8R8A8_UNORM))
        return MihawkSessionAction::InvalidTarget;
    if (!session_ready) return MihawkSessionAction::Initialize;
    return old_width == new_width && old_height == new_height &&
                   old_format == new_format
               ? MihawkSessionAction::Keep
               : MihawkSessionAction::RecreateAfterGpuIdle;
}
} // namespace Eden::FeatureLab
