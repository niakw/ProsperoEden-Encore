// SPDX-License-Identifier: GPL-3.0-or-later
// Hermetic host test. Records the GPU command sequence with mocked Vulkan
// entry points; no device, real driver or controller is involved.
#include "mihawk_vulkan_stage.h"
#include <cassert>
#include <cstdint>
#include <type_traits>
#include <vector>

namespace {
std::vector<char> calls;
std::vector<VkImageMemoryBarrier> captured;
fg_frame_pair last_pair{};
bool neural_available = true;
template <typename T>
T H(std::uintptr_t x) {
    if constexpr (std::is_pointer_v<T>) return reinterpret_cast<T>(x);
    else return static_cast<T>(x);
}
}

bool fg_method_available(const fg_context*, fg_method method) {
    return neural_available && method == FG_METHOD_NEURAL;
}

void fg_record_generate(fg_context*, VkCommandBuffer, uint32_t slot,
                        fg_method method, const fg_frame_pair* pair,
                        VkImageView output) {
    assert(slot == 0 && method == FG_METHOD_NEURAL);
    assert(output == H<VkImageView>(0x12345));
    assert(pair && pair->t == 0.5f);
    calls.push_back('G');
    last_pair = *pair;
}

extern "C" VKAPI_ATTR void VKAPI_CALL vkCmdPipelineBarrier(
    VkCommandBuffer, VkPipelineStageFlags, VkPipelineStageFlags,
    VkDependencyFlags, std::uint32_t, const VkMemoryBarrier*,
    std::uint32_t, const VkBufferMemoryBarrier*,
    std::uint32_t count, const VkImageMemoryBarrier* barriers) {
    calls.push_back('B');
    for (std::uint32_t i = 0; i < count; ++i) captured.push_back(barriers[i]);
}

extern "C" VKAPI_ATTR void VKAPI_CALL vkCmdCopyImage(
    VkCommandBuffer, VkImage src, VkImageLayout src_layout,
    VkImage dst, VkImageLayout dst_layout, std::uint32_t count,
    const VkImageCopy* regions) {
    calls.push_back('C');
    assert(src == H<VkImage>(0x2) && dst == H<VkImage>(0x3));
    assert(src_layout == VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL);
    assert(dst_layout == VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL);
    assert(count == 1 && regions && regions->extent.width == 1920);
}

extern "C" VKAPI_ATTR void VKAPI_CALL vkCmdBlitImage(
    VkCommandBuffer, VkImage src, VkImageLayout src_layout,
    VkImage dst, VkImageLayout dst_layout, std::uint32_t count,
    const VkImageBlit* regions, VkFilter filter) {
    calls.push_back('L');
    assert(src == H<VkImage>(0x8) && dst == H<VkImage>(0x9));
    assert(src_layout == VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL);
    assert(dst_layout == VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL);
    assert(count == 1 && regions && regions->srcOffsets[1].x == 1920);
    assert(filter == VK_FILTER_NEAREST);
}

int main() {
    using namespace Eden::FeatureLab;
    MihawkSourceRecord source{};
    source.cmd = H<VkCommandBuffer>(0x1);
    source.source_real = H<VkImage>(0x2);
    source.history_owned = H<VkImage>(0x3);
    source.width = 1920;
    source.height = 1080;
    assert(RecordOwnedSnapshot(source) == MihawkRecordResult::Recorded);
    assert((calls == std::vector<char>{'B','C','B'}));
    assert(captured.size() == 4);
    assert(captured[0].oldLayout == VK_IMAGE_LAYOUT_GENERAL);
    assert(captured[1].oldLayout == VK_IMAGE_LAYOUT_UNDEFINED);
    assert(captured[2].newLayout == VK_IMAGE_LAYOUT_GENERAL);
    assert(captured[3].newLayout == VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL);

    calls.clear(); captured.clear();
    source.history_initialized = true;
    assert(RecordOwnedSnapshot(source) == MihawkRecordResult::Recorded);
    assert(captured[1].oldLayout == VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL);

    calls.clear(); captured.clear();
    source.history_owned = source.source_real;
    assert(RecordOwnedSnapshot(source) == MihawkRecordResult::DuplicateImages);
    assert(calls.empty());

    MihawkGenerateRecord r{};
    r.cmd = H<VkCommandBuffer>(0x1);
    r.context = H<fg_context*>(0x100);
    r.previous_owned = H<VkImage>(0x4);
    r.current_owned = H<VkImage>(0x5);
    r.previous_view = H<VkImageView>(0x456);
    r.current_view = H<VkImageView>(0x567);
    r.private_rgba_output = H<VkImage>(0x8);
    r.private_rgba_view = H<VkImageView>(0x12345);
    r.synthetic_present = H<VkImage>(0x9);
    r.width = 1920; r.height = 1080;
    r.context_slot_count = 3;
    r.capabilities = {
        .enabled=true, .native_vulkan=true, .compute_and_storage=true,
        .model_licensed_and_loaded=true, .blit_rgba_to_present=true,
        .owned_history_pair=true, .history_matches_source_format=true,
        .private_output_rgba8_storage=true, .present_image_transfer_dst=true,
        .history_descriptor_slots_fenced=true,
        .present_queue_ordered=true, .hud_isolated=true,
        .available_present_frames=3,
        .width=1920, .height=1080,
        .compositor_format=ColorFormat::Bgra8Unorm
    };
    assert(RecordNativeMihawkPair(r) == MihawkRecordResult::Recorded);
    assert((calls == std::vector<char>{'B','G','B','L','B'}));
    assert(last_pair.prev_color == r.previous_view);
    assert(last_pair.next_color == r.current_view);
    assert(captured.size() == 4);
    assert(captured[0].newLayout == VK_IMAGE_LAYOUT_GENERAL);
    assert(captured[1].newLayout == VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL);
    assert(captured[2].oldLayout == VK_IMAGE_LAYOUT_UNDEFINED);
    assert(captured[3].newLayout == VK_IMAGE_LAYOUT_GENERAL);

    calls.clear(); captured.clear();
    r.output_was_blitted = true;
    assert(RecordNativeMihawkPair(r) == MihawkRecordResult::Recorded);
    assert(captured[0].oldLayout == VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL);

    calls.clear(); captured.clear();
    r.capabilities.hud_isolated = false;
    assert(RecordNativeMihawkPair(r) == MihawkRecordResult::Unsupported);
    r.capabilities.hud_isolated = true;
    r.synthetic_present = r.previous_owned;
    assert(RecordNativeMihawkPair(r) == MihawkRecordResult::DuplicateImages);
    r.synthetic_present = H<VkImage>(0x9);
    r.descriptor_slot = 4;
    assert(RecordNativeMihawkPair(r) == MihawkRecordResult::InvalidSlot);
    r.descriptor_slot = 0;
    neural_available = false;
    assert(RecordNativeMihawkPair(r) == MihawkRecordResult::NotReady);
    assert(calls.empty()); // no half-recorded frame on error
}
