// SPDX-License-Identifier: GPL-3.0-or-later
#include "mihawk_vulkan_stage.h"

#include <array>
#include <cmath>

namespace Eden::FeatureLab {
namespace {
constexpr VkImageSubresourceLayers ColorLayers() noexcept {
    VkImageSubresourceLayers layer{};
    layer.aspectMask = VK_IMAGE_ASPECT_COLOR_BIT;
    layer.layerCount = 1;
    return layer;
}
constexpr VkImageCopy FullImageCopy(std::uint32_t width, std::uint32_t height) noexcept {
    VkImageCopy copy{};
    copy.srcSubresource = ColorLayers();
    copy.dstSubresource = ColorLayers();
    copy.extent = {width, height, 1};
    return copy;
}
constexpr VkImageBlit FullImageBlit(std::uint32_t width, std::uint32_t height) noexcept {
    VkImageBlit blit{};
    blit.srcSubresource = ColorLayers();
    blit.dstSubresource = ColorLayers();
    blit.srcOffsets[1] = {static_cast<std::int32_t>(width), static_cast<std::int32_t>(height), 1};
    blit.dstOffsets[1] = blit.srcOffsets[1];
    return blit;
}
bool Distinct3(VkImage a, VkImage b, VkImage c) noexcept {
    return a != b && a != c && b != c;
}
} // namespace

MihawkRecordResult ValidateOwnedSnapshotInput(const MihawkSourceRecord& r) noexcept {
    if (!r.source_real || !r.history_owned ||
        r.width == 0 || r.height == 0 || r.width > 7680 || r.height > 4320)
        return MihawkRecordResult::InvalidHandles;
    if (r.source_real == r.history_owned)
        return MihawkRecordResult::DuplicateImages;
    return MihawkRecordResult::Recorded;
}

MihawkRecordResult ValidateOwnedSnapshot(const MihawkSourceRecord& r) noexcept {
    if (!r.cmd) return MihawkRecordResult::InvalidHandles;
    return ValidateOwnedSnapshotInput(r);
}

MihawkRecordResult RecordOwnedSnapshot(const MihawkSourceRecord& r) noexcept {
    const auto validated = ValidateOwnedSnapshot(r);
    if (validated != MihawkRecordResult::Recorded) return validated;
    const auto before = BeforeHistoryCopy(r.source_real, r.history_owned, r.history_initialized);
    const std::array barriers{before.source, before.history};
    vkCmdPipelineBarrier(r.cmd, before.src_stage, before.dst_stage, 0, 0, nullptr,
                         0, nullptr, static_cast<std::uint32_t>(barriers.size()), barriers.data());
    const auto copy = FullImageCopy(r.width, r.height);
    vkCmdCopyImage(r.cmd, r.source_real, VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL,
                   r.history_owned, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL, 1, &copy);
    const auto after = AfterHistoryCopy(r.source_real, r.history_owned);
    const std::array after_barriers{after.source, after.history};
    vkCmdPipelineBarrier(r.cmd, after.src_stage, after.dst_stage, 0, 0, nullptr,
                         0, nullptr, static_cast<std::uint32_t>(after_barriers.size()),
                         after_barriers.data());
    return MihawkRecordResult::Recorded;
}

MihawkRecordResult ValidateNativeMihawkPairInput(const MihawkGenerateRecord& r) noexcept {
    if (CheckNativeMihawkSurface(r.capabilities) != NativeMihawkReject::None)
        return MihawkRecordResult::Unsupported;
    if (!r.context || !fg_method_available(r.context, FG_METHOD_NEURAL))
        return MihawkRecordResult::NotReady;
    if (r.descriptor_slot >= r.context_slot_count || r.context_slot_count == 0 ||
        r.context_slot_count > 8)
        return MihawkRecordResult::InvalidSlot;
    if (!r.previous_owned || !r.current_owned || !r.previous_view ||
        !r.current_view || !r.private_rgba_output || !r.private_rgba_view ||
        !r.synthetic_present || r.width != r.capabilities.width ||
        r.height != r.capabilities.height)
        return MihawkRecordResult::InvalidHandles;
    if (!Distinct3(r.previous_owned, r.current_owned, r.private_rgba_output) ||
        r.synthetic_present == r.private_rgba_output ||
        r.synthetic_present == r.previous_owned ||
        r.synthetic_present == r.current_owned)
        return MihawkRecordResult::DuplicateImages;
    return MihawkRecordResult::Recorded;
}

MihawkRecordResult ValidateNativeMihawkPair(const MihawkGenerateRecord& r) noexcept {
    if (!r.cmd) return MihawkRecordResult::InvalidHandles;
    return ValidateNativeMihawkPairInput(r);
}

MihawkRecordResult RecordNativeMihawkPair(const MihawkGenerateRecord& r) noexcept {
    const auto validated = ValidateNativeMihawkPair(r);
    if (validated != MihawkRecordResult::Recorded) return validated;
    const VkImageMemoryBarrier output_prepare =
        BeforeNeuralOutput(r.private_rgba_output, r.output_was_blitted);
    vkCmdPipelineBarrier(r.cmd,
                         r.output_was_blitted ? VK_PIPELINE_STAGE_TRANSFER_BIT
                                              : VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT,
                         VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT, 0,
                         0, nullptr, 0, nullptr, 1, &output_prepare);

    fg_frame_pair pair{};
    pair.prev_color = r.previous_view;
    pair.next_color = r.current_view;
    pair.t = 0.5f; // x2 only, protected by present cadence gate
    fg_record_generate(r.context, r.cmd, r.descriptor_slot, FG_METHOD_NEURAL,
                       &pair, r.private_rgba_view);

    const auto pre_blit = BeforeGeneratedBlit(r.private_rgba_output, r.synthetic_present);
    const std::array barriers{pre_blit.source, pre_blit.history};
    vkCmdPipelineBarrier(r.cmd, pre_blit.src_stage, pre_blit.dst_stage, 0,
                         0, nullptr, 0, nullptr,
                         static_cast<std::uint32_t>(barriers.size()), barriers.data());

    const auto blit = FullImageBlit(r.width, r.height);
    // VkImageBlit converts RGBA8 storage to the presentation image's BGRA8
    // format when supported. The format/properties must be checked by caller.
    vkCmdBlitImage(r.cmd, r.private_rgba_output, VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL,
                   r.synthetic_present, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,
                   1, &blit, VK_FILTER_NEAREST);

    const VkImageMemoryBarrier synthetic_ready = AfterGeneratedBlit(r.synthetic_present);
    vkCmdPipelineBarrier(r.cmd, VK_PIPELINE_STAGE_TRANSFER_BIT,
                         VK_PIPELINE_STAGE_TRANSFER_BIT, 0,
                         0, nullptr, 0, nullptr, 1, &synthetic_ready);
    return MihawkRecordResult::Recorded;
}
} // namespace Eden::FeatureLab
