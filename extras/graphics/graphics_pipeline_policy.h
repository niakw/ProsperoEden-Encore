// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
// R06 optional Vulkan post-process routing CONTRACT, not an engine.
// Every effect fails closed until its real backend, resources and license
// have been verified. Never advertise unsupported modes as installed.
#include "framegen_capabilities.h"
#include <cstdint>

namespace Eden::FeatureLab {
enum class ResolutionStage : std::uint8_t {
    Native,
    SpatialFsr,
    TemporalFsr3,
};
enum class NeuralStage : std::uint8_t {
    Off,
    AMDCompute,
};
enum class TextureStage : std::uint8_t {
    Original,
    VerifiedHdPack,
};
struct RequestedPipeline {
    ResolutionStage resolution{ResolutionStage::Native};
    FrameGeneration frame_generation{FrameGeneration::Off};
    NeuralStage neural{NeuralStage::Off};
    TextureStage textures{TextureStage::Original};
    std::uint16_t display_hz{60};
};
struct PipelineCapabilities {
    GraphicsCapabilities framegen{};
    bool fsr_spatial_backend_ready{};
    bool fsr_temporal_backend_ready{};
    bool temporal_jitter_valid{};
    bool hud_separated{};
    bool neural_vulkan_spirv_ready{};
    bool neural_weights_redistributable{};
    bool neural_hdr_and_colorspace_checked{};
    bool neural_ui_exclusion_mask{};
    bool verified_hd_texture_pack{};
    bool output_120hz_negotiated{};
};
enum class Rejection : std::uint8_t {
    None=0, Unsupported=1, MissingSceneData=2, HudUnsafe=4,
    UnlicensedModel=8, UnverifiedOutput=16,
};
constexpr Rejection operator|(Rejection a, Rejection b) noexcept {
    return static_cast<Rejection>(static_cast<unsigned>(a)|static_cast<unsigned>(b));
}
struct SelectedPipeline {
    ResolutionStage resolution{ResolutionStage::Native};
    FrameGeneration frame_generation{FrameGeneration::Off};
    NeuralStage neural{NeuralStage::Off};
    TextureStage textures{TextureStage::Original};
    std::uint16_t display_hz{60};
    Rejection resolution_reason{Rejection::None};
    Rejection generation_reason{Rejection::None};
    Rejection neural_reason{Rejection::None};
    Rejection texture_reason{Rejection::None};
    // Being schedulable here is NOT proof of a working PS5 renderer.
    bool runtime_qualified{false};
};

constexpr SelectedPipeline ResolveGraphicsPipeline(
    RequestedPipeline request, const PipelineCapabilities& available) noexcept {
    SelectedPipeline selected{};
    selected.display_hz = (request.display_hz == 120 && available.output_120hz_negotiated)
                              ? 120 : 60;
    if (request.display_hz != 60 && request.display_hz != 120)
        selected.resolution_reason = Rejection::UnverifiedOutput;
    else if (request.display_hz == 120 && !available.output_120hz_negotiated)
        selected.resolution_reason = Rejection::UnverifiedOutput;
    if (request.resolution == ResolutionStage::SpatialFsr) {
        if (available.fsr_spatial_backend_ready)
            selected.resolution = request.resolution;
        else
            selected.resolution_reason = selected.resolution_reason | Rejection::Unsupported;
    } else if (request.resolution == ResolutionStage::TemporalFsr3) {
        if (!available.fsr_temporal_backend_ready)
            selected.resolution_reason = selected.resolution_reason | Rejection::Unsupported;
        else if (!available.framegen.guest_motion_vectors ||
                 !available.framegen.guest_depth || !available.temporal_jitter_valid)
            selected.resolution_reason = selected.resolution_reason | Rejection::MissingSceneData;
        else if (!available.hud_separated)
            selected.resolution_reason = selected.resolution_reason | Rejection::HudUnsafe;
        else
            selected.resolution = request.resolution;
    }
    if (request.frame_generation != FrameGeneration::Off) {
        const auto eligibility = QualifyFrameGeneration(request.frame_generation, available.framegen);
        if (eligibility == Availability::Unsupported)
            selected.generation_reason = Rejection::Unsupported;
        else if (!available.hud_separated)
            selected.generation_reason = Rejection::HudUnsafe;
        else
            selected.frame_generation = request.frame_generation;
    }
    if (request.neural == NeuralStage::AMDCompute) {
        if (!available.neural_vulkan_spirv_ready)
            selected.neural_reason = Rejection::Unsupported;
        else if (!available.neural_weights_redistributable)
            selected.neural_reason = Rejection::UnlicensedModel;
        else if (!available.neural_ui_exclusion_mask || !available.neural_hdr_and_colorspace_checked)
            selected.neural_reason = Rejection::HudUnsafe;
        else
            selected.neural = request.neural;
    }
    if (request.textures == TextureStage::VerifiedHdPack) {
        if (available.verified_hd_texture_pack)
            selected.textures = request.textures;
        else
            selected.texture_reason = Rejection::Unsupported;
    }
    // Activation of an actual Vulkan engine is a separate runtime contract.
    return selected;
}
} // namespace Eden::FeatureLab
