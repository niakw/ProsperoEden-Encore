// SPDX-License-Identifier: GPL-3.0-or-later
// Isolated HOST-ONLY R09 Min 720p -> FSR -> presentation handoff contract.
// This is not connected to Layer::ConfigureDraw; it never records Vulkan work.
// Do not treat a structurally admissible candidate as a runnable PS5 feature.
#pragma once
#include "dlss_nr_min_policy.h"
#include <array>
#include <cstdint>

namespace Eden::Graphics::DlssNrMin {

enum class Present720Reason : std::uint8_t {
    NoNeuralSelection, MissingAuthenticFrame, InvalidRaster,
    InvalidFilterOrder, MissingNeuralCompletion, MissingImageOwnership,
    MissingVisibilityOrFence, InvalidFsrOutput, HostCandidateOnly
};
enum class Present720Stage : std::uint8_t {
    NeuralCompute, ComputeToFragment, FsrEasu, FsrRcas, SwapchainPresent
};

// Opaque IDs model the fact that FSR::Draw requires BOTH VkImage and
// VkImageView. Equality of image views alone is not sufficient. These are
// never created from actual Vulkan handles and cannot be submitted.
struct Present720Image {
    std::uint64_t image{},view{};
    Extent extent{};
};
struct Present720Evidence {
    bool neural_selected{},original_graph_ready{},authentic_guest_frame{};
    bool antialiasing_disabled{},pre_neural_upscaler_disabled{};
    bool fsr_selected{},record_completed{},result_view_valid{};
    bool compute_to_fragment_visible{},same_scheduler_queue{};
    bool resources_held_through_fsr_tick{};
    Present720Image guest{},neural{},fsr_source{},fsr_target{};
};
struct Present720Candidate {
    Present720Reason reason{Present720Reason::NoNeuralSelection};
    std::array<Present720Stage,5> order{};
    Present720Image fsr_input{};
    Extent fsr_output{};
    bool host_shape_valid{},runtime_executable{};
};

inline constexpr bool kPostNeuralFsrRuntimeWired = false;
[[nodiscard]] constexpr bool ValidPresent720Output(Extent e) noexcept {
    return (e.width==1920u&&e.height==1080u)||
           (e.width==2560u&&e.height==1440u)||
           (e.width==3840u&&e.height==2160u);
}
[[nodiscard]] constexpr Present720Candidate
MakePresent720Candidate(const Present720Evidence& e) noexcept {
    Present720Candidate out{};
    if(!e.neural_selected)return out;
    if(!e.authentic_guest_frame||!e.guest.image||!e.guest.view||
       !e.original_graph_ready) {
        out.reason=Present720Reason::MissingAuthenticFrame;
        return out;
    }
    if(e.guest.extent.width!=1280u||e.guest.extent.height!=720u||
       e.neural.extent.width!=1280u||e.neural.extent.height!=720u||
       e.fsr_source.extent.width!=1280u||
       e.fsr_source.extent.height!=720u) {
        out.reason=Present720Reason::InvalidRaster;
        return out;
    }
    if(!e.antialiasing_disabled||!e.pre_neural_upscaler_disabled||
       !e.fsr_selected) {
        out.reason=Present720Reason::InvalidFilterOrder;
        return out;
    }
    if(!e.record_completed||!e.result_view_valid) {
        out.reason=Present720Reason::MissingNeuralCompletion;
        return out;
    }
    // Source-image and source-view must BOTH refer to the actual neural
    // result. Never transition the original guest image instead.
    if(!e.neural.image||!e.neural.view||
       e.neural.image==e.guest.image||
       e.neural.view==e.guest.view||
       e.fsr_source.image!=e.neural.image||
       e.fsr_source.view!=e.neural.view||
       !e.fsr_target.image||!e.fsr_target.view||
       e.fsr_target.image==e.neural.image||
       e.fsr_target.view==e.neural.view||
       e.fsr_target.image==e.guest.image) {
        out.reason=Present720Reason::MissingImageOwnership;
        return out;
    }
    if(!e.compute_to_fragment_visible||!e.same_scheduler_queue||
       !e.resources_held_through_fsr_tick) {
        out.reason=Present720Reason::MissingVisibilityOrFence;
        return out;
    }
    if(!ValidPresent720Output(e.fsr_target.extent)) {
        out.reason=Present720Reason::InvalidFsrOutput;
        return out;
    }
    out.reason=Present720Reason::HostCandidateOnly;
    out.order={
        Present720Stage::NeuralCompute,
        Present720Stage::ComputeToFragment,
        Present720Stage::FsrEasu,
        Present720Stage::FsrRcas,
        Present720Stage::SwapchainPresent};
    out.fsr_input=e.neural;
    out.fsr_output=e.fsr_target.extent;
    out.host_shape_valid=true;
    // Hard-coded fail closed: the current production presenter does NOT
    // support post-neural FSR. Neither a host success nor a compile flag
    // can silently enable it on PS5.
    out.runtime_executable=
        kPs5MinRuntimeQualified&&kPostNeuralFsrRuntimeWired;
    return out;
}
} // namespace Eden::Graphics::DlssNrMin
