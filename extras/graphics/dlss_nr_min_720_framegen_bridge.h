// SPDX-License-Identifier: GPL-3.0-or-later
// Unified A4K x2 / DLSS-NR Original host-only post-neural FG bridge.
// Neural denoise, spatial FSR and frame interpolation are distinct passes.
// Does not invoke Vulkan, load user DLLs, synthesize frames, or enable PS5 FG.
#pragma once
#include "dlss_nr_min_720_spatial_bridge.h"
#include "framegen_capabilities.h"
#include "framegen_present_gate.h"
#include <cstdint>

namespace Eden::Graphics::DlssNrMin {
namespace FG=Eden::FeatureLab;

inline constexpr bool kNeuralToFramegenRuntimeWired=false;

enum class FramegenBridgeReason : std::uint8_t {
    NoNeuralSelection, Disabled, UnsupportedBackend, MissingOriginal,
    MissingGuestOrNeuralImage, WrongOrderOrExtent, MissingGpuOwnership,
    UnsafeHistoryOrHud, UnmeasuredBudget, InvalidProvider,
    HostCandidateOnly
};
struct FramegenBridgeInput {
    int neural_mode{};
    FG::FrameGeneration method{FG::FrameGeneration::Off};
    FG::GraphicsCapabilities graphics{};
    // All IDs refer to REAL VkImage/view objects, not CPU timestamps.
    Present720Image guest{},neural{},post_spatial{};
    int spatial_filter{}; // stable existing 0..6 (no A4K as spatial)
    bool original_152_model_authenticated{};
    bool original_152_gpu_recorded{};
    bool a4k_native_x2_gpu_recorded{};
    bool a4k_output_image_and_view_identified{};
    bool neural_result_submitted{};
    bool post_spatial_filter_recorded{};
    bool final_post_spatial_frame_composited{};
    bool stable_real_frame_pair{};
    bool independent_guest_hud_or_explicitly_verified{};
    bool same_graphics_queue{};
    bool prior_real_frame_gpu_fence_complete{};
    bool resource_lifetime_through_interpolation_fence{};
    bool confirmed_free_vram_and_frametime{};
    // LSFG requires native loaded/shader-validated resources; MZ file
    // presence is never interpreted as a ready Vulkan implementation.
    bool lossless_native_shaders_validated{};
    std::uint32_t display_hz{};
    std::uint32_t real_game_fps{};
};
struct FramegenBridgeCandidate {
    FramegenBridgeReason reason{FramegenBridgeReason::NoNeuralSelection};
    FG::FrameGeneration downstream{FG::FrameGeneration::Off};
    Present720Image post_spatial_source{};
    bool a4k_source{};
    bool host_shape_qualified{};
    bool ps5_runtime_enabled{};
};

// Called by the CURRENT renderer selection path. It must keep existing
// Mihawk/FSR3/LSFG untouched when no neural mode is selected, but suppress
// their use with any selected DLSS-NR until real image+frame GPU proof exists.
// FSR spatial and the NR output are NOT synthetic frames.
[[nodiscard]] constexpr int EffectiveCompositeFramegen(
    int selected_neural_mode,int requested_method) noexcept {
    if(requested_method<0||requested_method>3)return 0;
    // A4K Detail/Soft/Denoise (1-3) and DLSS-NR Original/Compact
    // (4-5) are all independently selected Neural Rendering methods.
    const bool neural=selected_neural_mode>=1&&selected_neural_mode<=5;
    return neural ? 0 : requested_method;
}

[[nodiscard]] constexpr FramegenBridgeCandidate
AssessPostNeuralFramegen(const FramegenBridgeInput& e) noexcept {
    FramegenBridgeCandidate result{};
    const bool a4k=e.neural_mode>=1&&e.neural_mode<=3;
    const bool original=e.neural_mode==4;
    if(!a4k&&!original){
        // The 720p combined bridge is not yet qualified for DLSS Compact;
        // preserve explicit "model not qualified" instead of silently
        // treating a selected neural engine as switched OFF.
        if(e.neural_mode==5)
            result.reason=FramegenBridgeReason::MissingOriginal;
        return result;
    }
    if(e.method==FG::FrameGeneration::Off){
        result.reason=FramegenBridgeReason::Disabled;return result;
    }
    if(e.method!=FG::FrameGeneration::MihawkGen&&
       e.method!=FG::FrameGeneration::Fsr3Vulkan&&
       e.method!=FG::FrameGeneration::LosslessScaling){
        result.reason=FramegenBridgeReason::UnsupportedBackend;return result;
    }
    if((original&&(!e.original_152_model_authenticated||
                   !e.original_152_gpu_recorded))||
       (a4k&&(!e.a4k_native_x2_gpu_recorded||
              !e.a4k_output_image_and_view_identified))){
        result.reason=FramegenBridgeReason::MissingOriginal;return result;
    }
    if(!e.guest.image||!e.guest.view||!e.neural.image||!e.neural.view||
       !e.post_spatial.image||!e.post_spatial.view||
       e.guest.image==e.neural.image||e.guest.image==e.post_spatial.image||
       e.neural.image==e.post_spatial.image||
       e.guest.view==e.neural.view||e.guest.view==e.post_spatial.view||
       e.neural.view==e.post_spatial.view){
        result.reason=FramegenBridgeReason::MissingGuestOrNeuralImage;
        return result;
    }
    if(e.guest.extent.width!=1280u||e.guest.extent.height!=720u||
       e.neural.extent.width!=(a4k?2560u:1280u)||
       e.neural.extent.height!=(a4k?1440u:720u)||
       !ValidPresent720Output(e.post_spatial.extent)||
       !ValidSpatialFilter(e.spatial_filter)||
       !e.post_spatial_filter_recorded||
       !e.final_post_spatial_frame_composited){
        result.reason=FramegenBridgeReason::WrongOrderOrExtent;return result;
    }
    if(!e.neural_result_submitted||!e.same_graphics_queue||
       !e.prior_real_frame_gpu_fence_complete||
       !e.resource_lifetime_through_interpolation_fence){
        result.reason=FramegenBridgeReason::MissingGpuOwnership;return result;
    }
    if(!e.stable_real_frame_pair||
       !e.independent_guest_hud_or_explicitly_verified||
       (e.display_hz!=60u&&e.display_hz!=120u)||
       e.real_game_fps<30u||e.real_game_fps>=e.display_hz){
        result.reason=FramegenBridgeReason::UnsafeHistoryOrHud;return result;
    }
    if(!e.confirmed_free_vram_and_frametime){
        result.reason=FramegenBridgeReason::UnmeasuredBudget;return result;
    }
    // Reuse existing backend qualification, never an invented provider.
    FG::GraphicsCapabilities caps=e.graphics;
    caps.game_fps=e.real_game_fps;
    if(FG::QualifyFrameGeneration(e.method,caps)==FG::Availability::Unsupported||
       (e.method==FG::FrameGeneration::LosslessScaling&&
        !e.lossless_native_shaders_validated)){
        result.reason=FramegenBridgeReason::InvalidProvider;return result;
    }
    result.reason=FramegenBridgeReason::HostCandidateOnly;
    result.downstream=e.method;
    result.post_spatial_source=e.post_spatial;
    result.a4k_source=a4k;
    result.host_shape_qualified=true;
    // Cannot be enabled by toggling the UI, providing a DLL or merely
    // compiling the research code. The PS5 neural+FG proof is absent.
    result.ps5_runtime_enabled=kNeuralToFramegenRuntimeWired&&
        kPostNeuralSpatialRuntimeWired&&
        (a4k?kA4kNeuralToSpatialRuntimeQualified:
             kPs5MinRuntimeQualified);
    return result;
}
} // namespace Eden::Graphics::DlssNrMin
