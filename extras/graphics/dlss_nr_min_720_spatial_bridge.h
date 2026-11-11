// SPDX-License-Identifier: GPL-3.0-or-later
// Host-only R09 Original 720p -> USER-SELECTED spatial upscaling contract.
// Existing Eden filter IDs MUST remain stable; this is not FSR3 temporal.
// No Vulkan work, no synthetic output, no default PS5 runtime activation.
#pragma once
#include "dlss_nr_min_720_present_handoff.h"
#include <cstdint>

namespace Eden::Graphics::DlssNrMin {
// The stable UI/settings filter IDs. Anime4K is a separate neural engine.
enum class SpatialFilter : std::uint8_t {
    Bilinear=0, Fsr1=1, Bicubic=2, Nearest=3, Lanczos=4,
    Sgsr=5, SgsrEdge=6,
};
enum class SpatialBackend : std::uint8_t {
    NativeSampler, FsrEasuRcas, SgsrOnePass
};
enum class SpatialBridgeReason : std::uint8_t {
    NoOriginal, UnsupportedFilter, MissingGuestOrNeuralImage,
    InvalidRasterOrOutput, WrongOperationOrder, MissingImageLifetime,
    HostCandidateOnly
};
inline constexpr bool kPostNeuralSpatialRuntimeWired=false;
[[nodiscard]] constexpr bool ValidSpatialFilter(int filter) noexcept {
    return filter>=0&&filter<=6;
}
[[nodiscard]] constexpr SpatialBackend SelectSpatialBackend(int filter) noexcept {
    return filter==1?SpatialBackend::FsrEasuRcas:
           filter>=5?SpatialBackend::SgsrOnePass:
                     SpatialBackend::NativeSampler;
}
struct SpatialBridgeEvidence {
    int neural_mode{4};
    int filter{};
    Present720Image guest{},neural{},output{};
    bool authenticated_original_model{};
    bool original_152_gpu_recorded{};
    bool guest_frame_ready{};
    bool antialiasing_disabled{};
    bool no_pre_neural_scaling{};
    bool original_neural_image_completed{};
    bool compute_to_fragment_barrier{};
    bool actual_filter_pass_recorded{};
    bool final_image_composited{};
    bool same_vulkan_scheduler_queue{};
    bool all_images_held_through_gpu_tick{};
    bool full_crop_no_msaa{};
};
struct SpatialBridgeCandidate {
    SpatialBridgeReason reason{SpatialBridgeReason::NoOriginal};
    SpatialBackend backend{SpatialBackend::NativeSampler};
    Present720Image filter_input{},output{};
    bool host_shape_qualified{};
    bool runtime_executable{};
};
[[nodiscard]] constexpr SpatialBridgeCandidate
AssessPostNeuralSpatial(const SpatialBridgeEvidence& e) noexcept {
    SpatialBridgeCandidate out{};
    if(e.neural_mode!=4||!e.authenticated_original_model||
       !e.original_152_gpu_recorded)
        return out;
    if(!ValidSpatialFilter(e.filter)){
        out.reason=SpatialBridgeReason::UnsupportedFilter;return out;
    }
    const auto backend=SelectSpatialBackend(e.filter);
    if(!e.guest_frame_ready||!e.guest.image||!e.guest.view||
       !e.neural.image||!e.neural.view||
       e.guest.image==e.neural.image||
       e.guest.view==e.neural.view) {
        out.reason=SpatialBridgeReason::MissingGuestOrNeuralImage;
        return out;
    }
    if(e.guest.extent.width!=1280u||e.guest.extent.height!=720u||
       e.neural.extent.width!=1280u||e.neural.extent.height!=720u||
       !ValidPresent720Output(e.output.extent)){
        out.reason=SpatialBridgeReason::InvalidRasterOrOutput;return out;
    }
    if(!e.antialiasing_disabled||!e.no_pre_neural_scaling||
       !e.original_neural_image_completed||
       !e.compute_to_fragment_barrier||
       !e.full_crop_no_msaa||
       !e.final_image_composited||
       !e.actual_filter_pass_recorded){
        out.reason=SpatialBridgeReason::WrongOperationOrder;return out;
    }
    // Native bilinear/nearest/bicubic/lanczos are handled by the
    // existing presentation sampler. They need no new upscaled VkImage:
    // the real post-composite presenter owns the final 1080p/1440p/4K image.
    // SGSR/FSR are distinct graphics-pass images, not aliases of NR.
    if(backend!=SpatialBackend::NativeSampler &&
       (!e.output.image||!e.output.view||
        e.output.image==e.neural.image||
        e.output.view==e.neural.view||
        e.output.image==e.guest.image||
        e.output.view==e.guest.view)){
        out.reason=SpatialBridgeReason::MissingGuestOrNeuralImage;
        return out;
    }
    if(!e.same_vulkan_scheduler_queue||
       !e.all_images_held_through_gpu_tick){
        out.reason=SpatialBridgeReason::MissingImageLifetime;return out;
    }
    out.reason=SpatialBridgeReason::HostCandidateOnly;
    out.backend=backend;
    out.filter_input=e.neural;
    out.output=e.output;
    out.host_shape_qualified=true;
    out.runtime_executable=kPs5MinRuntimeQualified &&
        kPostNeuralSpatialRuntimeWired;
    return out;
}
} // namespace Eden::Graphics::DlssNrMin
