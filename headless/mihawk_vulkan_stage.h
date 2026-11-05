// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
// MihawkGen R08: command recording into CALLER-OWNED GPU resources.
// This module does not allocate, publish, recycle or present frames.
// Lifetime: the caller guarantees fenced dedicated history images, a distinct
// output RGBA8 image, and a safe PresentManager slot.
#include "mihawk_native_surface_contract.h"
#include "mihawk_vulkan_history_barriers.h"
#include "framegen.h"

namespace Eden::FeatureLab {

enum class MihawkRecordResult : std::uint8_t {
    Recorded, Unsupported, NotReady, InvalidHandles, DuplicateImages, InvalidSlot
};
struct MihawkSourceRecord {
    VkCommandBuffer cmd = VK_NULL_HANDLE;
    VkImage source_real = VK_NULL_HANDLE; // last compositor pass finished in GENERAL
    VkImage history_owned = VK_NULL_HANDLE; // separate stable sampled image
    bool history_initialized = false; // true iff this history survived the prior pass
    std::uint32_t width = 0, height = 0;
};

// Prepares copy with explicit GENERAL -> TRANSFER_SRC -> GENERAL on the
// actual composed frame. Only the private image is kept for interpolation.
MihawkRecordResult ValidateOwnedSnapshot(const MihawkSourceRecord& record) noexcept;
MihawkRecordResult RecordOwnedSnapshot(const MihawkSourceRecord& record) noexcept;

struct MihawkGenerateRecord {
    fg_context* context = nullptr;
    VkCommandBuffer cmd = VK_NULL_HANDLE;
    VkImage previous_owned = VK_NULL_HANDLE;
    VkImage current_owned = VK_NULL_HANDLE;
    VkImageView previous_view = VK_NULL_HANDLE;
    VkImageView current_view = VK_NULL_HANDLE;
    VkImage private_rgba_output = VK_NULL_HANDLE;
    VkImageView private_rgba_view = VK_NULL_HANDLE;
    VkImage synthetic_present = VK_NULL_HANDLE;
    std::uint32_t width = 0, height = 0;
    std::uint32_t descriptor_slot = 0;
    std::uint32_t context_slot_count = 0;
    bool output_was_blitted = false;
    // Caller must verify all these from the active renderer, not hardcode true.
    MihawkSurfaceCapabilities capabilities{};
};

// Records one neural interpolation with format-aware transfer to a distinct
// presentation frame. Does not submit, flush, present or increment guest FPS.
MihawkRecordResult ValidateNativeMihawkPair(const MihawkGenerateRecord& record) noexcept;
MihawkRecordResult RecordNativeMihawkPair(const MihawkGenerateRecord& record) noexcept;

} // namespace Eden::FeatureLab
