// SPDX-License-Identifier: GPL-3.0-or-later
// Hermetic host test. Records the GPU command sequence with mocked Vulkan
// entry points; no device, real driver or controller is involved.
#include "mihawk_vulkan_stage.h"
#include "mihawk_vulkan_encoder.h"
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
    assert(src == H<VkImage>(0x2) && (dst == H<VkImage>(0x3) || dst == H<VkImage>(0x5)));
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
        .model_verified_and_loaded=true, .blit_rgba_to_present=true,
        .owned_history_pair=true, .history_matches_source_format=true,
        .private_output_rgba8_storage=true, .present_image_transfer_dst=true,
        .history_descriptor_slots_fenced=true,
        .present_queue_ordered=true, .native_hud_absent=true,
        .available_present_frames=3,
        .width=1920, .height=1080,
        .compositor_format=ColorFormat::Bgra8Unorm
    };
    assert(ValidateNativeMihawkPairInput(r) == MihawkRecordResult::Recorded);
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
    r.capabilities.native_hud_absent = false;
    assert(RecordNativeMihawkPair(r) == MihawkRecordResult::Unsupported);
    r.capabilities.native_hud_absent = true;
    r.synthetic_present = r.previous_owned;
    assert(RecordNativeMihawkPair(r) == MihawkRecordResult::DuplicateImages);
    r.synthetic_present = H<VkImage>(0x9);
    r.descriptor_slot = 4;
    assert(RecordNativeMihawkPair(r) == MihawkRecordResult::InvalidSlot);
    r.descriptor_slot = 0;
    neural_available = false;
    assert(RecordNativeMihawkPair(r) == MihawkRecordResult::NotReady);
    assert(calls.empty()); // no half-recorded frame on error

    // End-to-end *recording* of a frame pair (still no GPU/PS5).
    neural_available = true;
    MihawkVulkanEncoder encoder{};
    MihawkEncoderInput input{};
    input.request.mode = FrameGeneration::MihawkGen;
    input.request.graphics.native_vulkan = true;
    input.request.graphics.mihawk_compute = true;
    input.request.graphics.model_weights_verified_and_loaded = true;
    input.request.graphics.game_fps = 30;
    input.request.surface = r.capabilities;
    input.request.source = {
        .real_frame_id = 1, .timestamp_ns = 1'000'000'000,
        .width = 1920, .height = 1080,
        .output_hz = 60, .display_mode_verified = true
    };
    input.request.reserved_gpu_serial = 1;
    input.commands = H<VkCommandBuffer>(0x1);
    input.real_composited_image = H<VkImage>(0x2);
    input.synthetic_present_image = H<VkImage>(0x9);
    input.neural_context = H<fg_context*>(0x100);
    input.descriptor_slots = 3;
    input.images.history[0] = H<VkImage>(0x3);
    input.images.history[1] = H<VkImage>(0x5);
    input.images.history_view[0] = H<VkImageView>(0x456);
    input.images.history_view[1] = H<VkImageView>(0x567);
    input.images.rgba_output = H<VkImage>(0x8);
    input.images.rgba_view = H<VkImageView>(0x12345);

    // Validating a source before the scheduler assigns a real command
    // buffer is a pure input check, NOT a forged Vulkan handle.
    MihawkSourceRecord preflight{};
    preflight.source_real = input.real_composited_image;
    preflight.history_owned = input.images.history[0];
    preflight.width = input.request.source.width;
    preflight.height = input.request.source.height;
    assert(ValidateOwnedSnapshotInput(preflight) == MihawkRecordResult::Recorded);
    assert(ValidateOwnedSnapshot(preflight) == MihawkRecordResult::InvalidHandles);
    preflight.history_owned = preflight.source_real;
    assert(ValidateOwnedSnapshotInput(preflight) == MihawkRecordResult::DuplicateImages);

    calls.clear(); captured.clear();
    auto encoded = encoder.Record(input);
    assert(encoded.IsRecorded() && !encoded.WillPresentSynthetic());
    assert((calls == std::vector<char>{'B','C','B'}));
    auto pending = encoder.Record(input);
    assert(pending.plan.status == MihawkPlanStatus::SubmissionPending);
    assert((calls == std::vector<char>{'B','C','B'}));
    assert(encoder.Commit(encoded, encoded.plan.reserved_gpu_serial));
    assert(!encoder.Commit(encoded, encoded.plan.reserved_gpu_serial));


    ++input.request.source.real_frame_id;
    input.request.source.timestamp_ns += 33'333'333;
    input.request.completed_gpu_serial = 1;
    input.request.reserved_gpu_serial = 2;
    calls.clear(); captured.clear();
    encoded = encoder.Record(input);
    assert(encoded.IsRecorded() && encoded.WillPresentSynthetic());
    assert((calls == std::vector<char>{'B','C','B','B','G','B','L','B'}));
    assert(last_pair.prev_color == input.images.history_view[0]);
    assert(last_pair.next_color == input.images.history_view[1]);
    assert(encoder.Commit(encoded, encoded.plan.reserved_gpu_serial));


    // Do not copy into a snapshot still referenced by neural work.
    ++input.request.source.real_frame_id;
    input.request.source.timestamp_ns += 33'333'333;
    input.request.reserved_gpu_serial = 3;
    calls.clear(); captured.clear();
    encoded = encoder.Record(input);
    assert(!encoded.IsRecorded());
    assert(encoded.plan.status == MihawkPlanStatus::GpuBusy);
    assert(calls.empty());

    ++input.request.source.real_frame_id;
    input.request.source.timestamp_ns += 33'333'333;
    input.request.completed_gpu_serial = 2;
    calls.clear(); captured.clear();
    encoded = encoder.Record(input);
    assert(encoded.IsRecorded() && !encoded.WillPresentSynthetic());
    assert((calls == std::vector<char>{'B','C','B'}));
    assert(encoder.Commit(encoded, encoded.plan.reserved_gpu_serial));

    // Before recording even the first copy, reject unavailable neural model.
    ++input.request.source.real_frame_id;
    input.request.source.timestamp_ns += 33'333'333;
    input.request.reserved_gpu_serial = 4;
    input.request.completed_gpu_serial = 3;
    neural_available = false;
    calls.clear(); captured.clear();
    encoded = encoder.Record(input);
    assert(!encoded.IsRecorded() && encoded.recording == MihawkRecordResult::NotReady);
    assert(calls.empty());
    neural_available = true;

    // A HUD that cannot be separated from the game image fails closed.
    input.request.surface.native_hud_absent = false;
    encoded = encoder.Record(input);
    assert(!encoded.IsRecorded() && encoded.plan.status == MihawkPlanStatus::UnsafeResources);
    assert(calls.empty());

    // Even if Vulkan recycles identical opaque VkImage handles, an allocation
    // generation change discards the encoder's old history and layouts.
    input.request.surface.native_hud_absent = true;
    ++input.images.resource_generation;
    ++input.request.source.real_frame_id;
    input.request.source.timestamp_ns += 33'333'333;
    calls.clear(); captured.clear();
    encoded = encoder.Record(input);
    assert(encoded.IsRecorded() && !encoded.WillPresentSynthetic());
    assert(captured[1].oldLayout == VK_IMAGE_LAYOUT_UNDEFINED);
    encoder.Abort();
    assert(calls.size() == 3);
}
