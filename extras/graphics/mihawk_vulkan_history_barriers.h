// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
// Explicit barriers for copying a composited REAL frame into privately
// allocated history. This helper does not own or recycle Vulkan images.
// Caller must keep history alive until all GPU work referring to it is done.
// Caller must record vkCmdCopyImage between the Before/After barriers.
#include <vulkan/vulkan.h>

namespace Eden::FeatureLab {

struct HistoryBarriers {
    VkImageMemoryBarrier source;
    VkImageMemoryBarrier history;
    VkPipelineStageFlags src_stage;
    VkPipelineStageFlags dst_stage;
};

constexpr VkImageMemoryBarrier MakeImageBarrier(
    VkImage image, VkAccessFlags src_access, VkAccessFlags dst_access,
    VkImageLayout old_layout, VkImageLayout new_layout) noexcept {
    VkImageMemoryBarrier b{};
    b.sType = VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER;
    b.srcAccessMask = src_access;
    b.dstAccessMask = dst_access;
    b.oldLayout = old_layout;
    b.newLayout = new_layout;
    b.srcQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
    b.dstQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
    b.image = image;
    b.subresourceRange.aspectMask = VK_IMAGE_ASPECT_COLOR_BIT;
    b.subresourceRange.levelCount = 1;
    b.subresourceRange.layerCount = 1;
    return b;
}

// Encore's active WindowAdaptPass finishes in GENERAL. Never use UNDEFINED
// for a rendered source (it would discard the pixels). A reused snapshot
// remains SHADER_READ_ONLY_OPTIMAL after the prior interpolation.
constexpr HistoryBarriers BeforeHistoryCopy(
    VkImage real_image, VkImage history_image, bool history_initialized) noexcept {
    return {
        MakeImageBarrier(real_image,
                         VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT,
                         VK_ACCESS_TRANSFER_READ_BIT,
                         VK_IMAGE_LAYOUT_GENERAL,
                         VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL),
        MakeImageBarrier(history_image,
                         history_initialized ? VK_ACCESS_SHADER_READ_BIT : 0U,
                         VK_ACCESS_TRANSFER_WRITE_BIT,
                         history_initialized ? VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL
                                             : VK_IMAGE_LAYOUT_UNDEFINED,
                         VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL),
        static_cast<VkPipelineStageFlags>(
            VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT |
            (history_initialized ? VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT : 0U)),
        VK_PIPELINE_STAGE_TRANSFER_BIT
    };
}

constexpr HistoryBarriers AfterHistoryCopy(
    VkImage real_image, VkImage history_image) noexcept {
    return {
        MakeImageBarrier(real_image,
                         VK_ACCESS_TRANSFER_READ_BIT,
                         VK_ACCESS_TRANSFER_READ_BIT |
                             VK_ACCESS_COLOR_ATTACHMENT_READ_BIT |
                             VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT,
                         VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL,
                         VK_IMAGE_LAYOUT_GENERAL),
        MakeImageBarrier(history_image,
                         VK_ACCESS_TRANSFER_WRITE_BIT,
                         VK_ACCESS_SHADER_READ_BIT,
                         VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,
                         VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL),
        VK_PIPELINE_STAGE_TRANSFER_BIT,
        VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT | VK_PIPELINE_STAGE_TRANSFER_BIT |
            VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT
    };
}

// A generated RGBA8 intermediate is *owned* by this backend; it must not
// alias PresentManager's image (potentially BGRA). Convert it by supported
// vkCmdBlitImage before asking PresentManager to present the synthetic frame.
// On first use its content is undefined. On reuse, the previous blit left it
// in TRANSFER_SRC_OPTIMAL, and this barrier must precede the compute pass.
constexpr VkImageMemoryBarrier BeforeNeuralOutput(
    VkImage rgba_storage, bool previous_blit_completed) noexcept {
    return MakeImageBarrier(
        rgba_storage,
        previous_blit_completed ? VK_ACCESS_TRANSFER_READ_BIT : 0U,
        VK_ACCESS_SHADER_WRITE_BIT,
        previous_blit_completed ? VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL
                                : VK_IMAGE_LAYOUT_UNDEFINED,
        VK_IMAGE_LAYOUT_GENERAL);
}

// Assumes fg_record_generate wrote RGBA8 storage in GENERAL earlier on the
// same queue. Synthetic target is fully overwritten by a format-aware blit.
constexpr HistoryBarriers BeforeGeneratedBlit(
    VkImage rgba_storage, VkImage synthetic_present_image) noexcept {
    return {
        MakeImageBarrier(rgba_storage,
                         VK_ACCESS_SHADER_WRITE_BIT,
                         VK_ACCESS_TRANSFER_READ_BIT,
                         VK_IMAGE_LAYOUT_GENERAL,
                         VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL),
        MakeImageBarrier(synthetic_present_image,
                         0U, VK_ACCESS_TRANSFER_WRITE_BIT,
                         VK_IMAGE_LAYOUT_UNDEFINED,
                         VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL),
        VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,
        VK_PIPELINE_STAGE_TRANSFER_BIT
    };
}

constexpr VkImageMemoryBarrier AfterGeneratedBlit(VkImage synthetic_present_image) noexcept {
    return MakeImageBarrier(synthetic_present_image,
                            VK_ACCESS_TRANSFER_WRITE_BIT,
                            VK_ACCESS_TRANSFER_READ_BIT |
                                VK_ACCESS_COLOR_ATTACHMENT_READ_BIT |
                                VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT,
                            VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,
                            VK_IMAGE_LAYOUT_GENERAL);
}
} // namespace Eden::FeatureLab
