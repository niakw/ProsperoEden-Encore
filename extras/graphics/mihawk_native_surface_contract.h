// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
// Native Vulkan *resource contract*, not an enabled frame generator.
// The presenter's recycled Frame* is NEVER an interpolation history image.
// Two dedicated, stable, same-extent snapshots plus a private RGBA8 output
// are required. These checks precede any optional GPU dispatch.
#include <cstdint>

namespace Eden::FeatureLab {

enum class NativeMihawkReject : std::uint8_t {
    None,
    Disabled,
    MissingCompute,
    UnlicensedWeights,
    NonNativeVulkan,
    UnsupportedFormat,
    InsufficientSlots,
    UnownedHistory,
    IncorrectHistoryFormat,
    InvalidOutputFormat,
    MissingPresentTransferUsage,
    InFlightResources,
    MissingBlitSupport,
    UnsafeHud,
    NoPresenterSync,
    InvalidExtent
};

enum class ColorFormat : std::uint8_t {
    Rgba8Unorm,
    Bgra8Unorm,
    Other
};

struct MihawkSurfaceCapabilities {
    bool enabled = false;                 // qualified backend actually built
    bool native_vulkan = false;
    bool compute_and_storage = false;
    bool model_licensed_and_loaded = false;
    bool blit_rgba_to_present = false;     // both formats support src/dst BLIT
    bool owned_history_pair = false;
    bool history_matches_source_format = false;
    bool private_output_rgba8_storage = false;
    bool present_image_transfer_dst = false;
    bool history_descriptor_slots_fenced = false;
    bool present_queue_ordered = false;
    bool hud_isolated = false;
    std::uint8_t available_present_frames = 0;
    std::uint32_t width = 0, height = 0;
    ColorFormat compositor_format = ColorFormat::Other;
};

constexpr NativeMihawkReject CheckNativeMihawkSurface(
    const MihawkSurfaceCapabilities& x) noexcept {
    if (!x.enabled) return NativeMihawkReject::Disabled;
    if (!x.native_vulkan) return NativeMihawkReject::NonNativeVulkan;
    if (!x.compute_and_storage) return NativeMihawkReject::MissingCompute;
    if (!x.model_licensed_and_loaded) return NativeMihawkReject::UnlicensedWeights;
    if (!x.width || !x.height || x.width > 7680 || x.height > 4320)
        return NativeMihawkReject::InvalidExtent;
    if (x.compositor_format != ColorFormat::Rgba8Unorm &&
        x.compositor_format != ColorFormat::Bgra8Unorm)
        return NativeMihawkReject::UnsupportedFormat;
    // This reserves at least a real frame, a synthetic frame and one spare.
    if (x.available_present_frames < 3) return NativeMihawkReject::InsufficientSlots;
    if (!x.owned_history_pair) return NativeMihawkReject::UnownedHistory;
    if (!x.history_matches_source_format) return NativeMihawkReject::IncorrectHistoryFormat;
    if (!x.private_output_rgba8_storage) return NativeMihawkReject::InvalidOutputFormat;
    if (!x.present_image_transfer_dst) return NativeMihawkReject::MissingPresentTransferUsage;
    if (!x.history_descriptor_slots_fenced) return NativeMihawkReject::InFlightResources;
    if (!x.present_queue_ordered) return NativeMihawkReject::NoPresenterSync;
    if (!x.hud_isolated) return NativeMihawkReject::UnsafeHud;
    // The source may be BGRA, but the network writes *RGBA8*. A dedicated
    // storage image must be blitted (including format conversion if BGRA).
    // Even RGBA->RGBA requires that BLIT_SRC and BLIT_DST be supported.
    if (!x.blit_rgba_to_present)
        return NativeMihawkReject::MissingBlitSupport;
    return NativeMihawkReject::None;
}
} // namespace Eden::FeatureLab
