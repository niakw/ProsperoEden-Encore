// SPDX-License-Identifier: GPL-3.0-or-later
// Tests only the proposed presentation order/ownership contract. NO Vulkan.
#include "dlss_nr_min_720_present_handoff.h"
#include <array>
#include <cassert>
#include <cstdint>
#include <iostream>

using namespace Eden::Graphics::DlssNrMin;
static constexpr Present720Evidence kReference{
    .neural_selected=true,
    .original_graph_ready=true,
    .authentic_guest_frame=true,
    .antialiasing_disabled=true,
    .pre_neural_upscaler_disabled=true,
    .fsr_selected=true,
    .record_completed=true,
    .result_view_valid=true,
    .compute_to_fragment_visible=true,
    .same_scheduler_queue=true,
    .resources_held_through_fsr_tick=true,
    .guest={11u,12u,{1280u,720u}},
    .neural={21u,22u,{1280u,720u}},
    .fsr_source={21u,22u,{1280u,720u}},
    .fsr_target={31u,32u,{3840u,2160u}},
};
static void ExpectReject(Present720Evidence e,Present720Reason why) {
    const auto route=MakePresent720Candidate(e);
    assert(route.reason==why);
    assert(!route.host_shape_valid&&!route.runtime_executable);
    assert(route.fsr_input.image==0u&&route.fsr_input.view==0u);
}
int main() {
    static_assert(!kPs5MinRuntimeQualified);
    static_assert(!kPostNeuralFsrRuntimeWired);
    constexpr std::array<Present720Stage,5u> correct{
        Present720Stage::NeuralCompute,
        Present720Stage::ComputeToFragment,
        Present720Stage::FsrEasu,
        Present720Stage::FsrRcas,
        Present720Stage::SwapchainPresent};
    for(const auto target:std::array<Extent,3u>{
        Extent{1920u,1080u},Extent{2560u,1440u},
        Extent{3840u,2160u}}) {
        auto trial=kReference;
        trial.fsr_target.extent=target;
        const auto route=MakePresent720Candidate(trial);
        assert(route.reason==Present720Reason::HostCandidateOnly);
        assert(route.host_shape_valid&&!route.runtime_executable);
        assert(route.order==correct);
        assert(route.fsr_input.image==trial.neural.image);
        assert(route.fsr_input.view==trial.neural.view);
        assert(route.fsr_output.width==target.width);
        assert(route.fsr_output.height==target.height);
    }
    auto bad=kReference;
    bad.neural_selected=false;
    ExpectReject(bad,Present720Reason::NoNeuralSelection);
    bad=kReference;bad.authentic_guest_frame=false;
    ExpectReject(bad,Present720Reason::MissingAuthenticFrame);
    bad=kReference;bad.original_graph_ready=false;
    ExpectReject(bad,Present720Reason::MissingAuthenticFrame);
    bad=kReference;bad.guest.extent={1920u,1080u};
    ExpectReject(bad,Present720Reason::InvalidRaster);
    bad=kReference;bad.neural.extent={1920u,1080u};
    ExpectReject(bad,Present720Reason::InvalidRaster);
    bad=kReference;bad.fsr_source.extent={1920u,1080u};
    ExpectReject(bad,Present720Reason::InvalidRaster);
    bad=kReference;bad.antialiasing_disabled=false;
    ExpectReject(bad,Present720Reason::InvalidFilterOrder);
    bad=kReference;bad.pre_neural_upscaler_disabled=false;
    ExpectReject(bad,Present720Reason::InvalidFilterOrder);
    bad=kReference;bad.fsr_selected=false;
    ExpectReject(bad,Present720Reason::InvalidFilterOrder);
    bad=kReference;bad.record_completed=false;
    ExpectReject(bad,Present720Reason::MissingNeuralCompletion);
    bad=kReference;bad.result_view_valid=false;
    ExpectReject(bad,Present720Reason::MissingNeuralCompletion);
    bad=kReference;bad.neural.image=0u;
    ExpectReject(bad,Present720Reason::MissingImageOwnership);
    bad=kReference;bad.neural.image=bad.guest.image;
    ExpectReject(bad,Present720Reason::MissingImageOwnership);
    bad=kReference;bad.neural.view=bad.guest.view;
    ExpectReject(bad,Present720Reason::MissingImageOwnership);
    bad=kReference;bad.fsr_source.image=bad.guest.image;
    ExpectReject(bad,Present720Reason::MissingImageOwnership);
    bad=kReference;bad.fsr_source.view=bad.guest.view;
    ExpectReject(bad,Present720Reason::MissingImageOwnership);
    bad=kReference;bad.fsr_target.image=bad.neural.image;
    ExpectReject(bad,Present720Reason::MissingImageOwnership);
    bad=kReference;bad.compute_to_fragment_visible=false;
    ExpectReject(bad,Present720Reason::MissingVisibilityOrFence);
    bad=kReference;bad.same_scheduler_queue=false;
    ExpectReject(bad,Present720Reason::MissingVisibilityOrFence);
    bad=kReference;bad.resources_held_through_fsr_tick=false;
    ExpectReject(bad,Present720Reason::MissingVisibilityOrFence);
    bad=kReference;bad.fsr_target.extent={4096u,2160u};
    ExpectReject(bad,Present720Reason::InvalidFsrOutput);
    bad=kReference;bad.fsr_target.extent={1280u,720u};
    ExpectReject(bad,Present720Reason::InvalidFsrOutput);
    std::cout<<"R09_MIN_720_POST_NEURAL_FSR_HOST_CONTRACT_PASS "
             <<"positive_targets=3 negative_conditions=22 "
             <<"stage_order=NEURAL_BARRIER_EASU_RCAS_PRESENT "
             <<"runtime=DISABLED\n";
}
