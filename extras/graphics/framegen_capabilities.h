// SPDX-License-Identifier: GPL-3.0-or-later
// PS5-native frame generation capabilities; user preference is not proof of displayed frames.
// Prevent a PC-only NVIDIA/DLSS option from being advertised as native PS5.
#pragma once
#include <cstdint>

namespace Eden::FeatureLab {
enum class FrameGeneration : std::uint8_t {
    Off = 0,
    MihawkGen = 1,
    Fsr3Vulkan = 2,
    LosslessScaling = 3,
    DlssPcOnlyUnsupported = 4,
};
enum class Availability : std::uint8_t {
    Disabled,
    Unsupported,
    ReadyLowCadence,
    Ready,
};
struct GraphicsCapabilities {
    bool native_vulkan = false;
    bool fsr3_swapchain = false;
    bool guest_motion_vectors = false;
    bool guest_depth = false;
    bool mihawk_compute = false;
    bool model_weights_verified_and_licensed = false;
    bool lossless_scaling_provider_available = false;
    // Real game progression FPS: NEVER interpolated display FPS.
    std::uint32_t game_fps = 0;
};

constexpr Availability QualifyFrameGeneration(
    FrameGeneration requested, const GraphicsCapabilities& caps) noexcept {
    if (requested == FrameGeneration::Off) return Availability::Disabled;
    // Unsupported on the PS5 GPU through a native NVIDIA NGX/DLSS5 path.
    if (requested == FrameGeneration::DlssPcOnlyUnsupported)
        return Availability::Unsupported;
    if (!caps.native_vulkan || caps.game_fps < 30)
        return Availability::Unsupported;
    switch (requested) {
    case FrameGeneration::Fsr3Vulkan:
        if (!caps.fsr3_swapchain || !caps.guest_motion_vectors ||
            !caps.guest_depth) return Availability::Unsupported;
        break;
    case FrameGeneration::MihawkGen:
        if (!caps.mihawk_compute || !caps.model_weights_verified_and_licensed)
            return Availability::Unsupported;
        break;
    case FrameGeneration::LosslessScaling:
        if (!caps.lossless_scaling_provider_available)
            return Availability::Unsupported;
        break;
    case FrameGeneration::Off:
    case FrameGeneration::DlssPcOnlyUnsupported:
        return Availability::Unsupported;
    }
    // 30->60 presented is not 60 Hz game simulation, and AMD recommends
    // a source cadence at or above 60 fps for good interpolation quality.
    return caps.game_fps < 60 ? Availability::ReadyLowCadence
                              : Availability::Ready;
}
} // namespace Eden::FeatureLab
