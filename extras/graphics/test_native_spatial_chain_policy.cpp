// SPDX-License-Identifier: GPL-3.0-or-later
#include "native_spatial_chain_policy.h"
#include <cassert>
#include <iostream>
using namespace Eden::Graphics::PipelineComposer;
using R=TwoPassReason;
constexpr TwoPassInput Good(int first=1,int second=5) {
    TwoPassInput x{};
    x.first=first;x.second=second;
    x.source={1280u,720u};x.intermediate={2560u,1440u};
    x.target={3840u,2160u};
    x.source_image=101u;x.source_view=102u;
    x.first_image=201u;x.first_view=202u;
    x.second_image=301u;x.second_view=302u;
    x.same_vulkan_queue=true;
    x.first_renderpass_recorded=true;
    x.color_write_to_fragment_read_barrier=true;
    x.second_renderpass_recorded=true;
    x.both_owners_live_through_gpu_tick=true;
    return x;
}
constexpr bool Candidate(TwoPassInput x) {
    auto r=AssessTwoPass(x);
    return r.reason==R::CandidateOnly&&
           r.host_contract_passed&&!r.ps5_runtime_allowed;
}
constexpr bool Rejected(TwoPassInput x,R why) {
    auto r=AssessTwoPass(x);
    return r.reason==why&&!r.host_contract_passed&&
           !r.ps5_runtime_allowed;
}
int main() {
    static_assert(!kNativeSpatialVulkanChainQualified);
    static_assert(!kComposablePs5RuntimeQualified);
    static_assert(Candidate(Good()));
    unsigned candidates=0u;
    for(int first:{1,5,6})for(int second:{1,5,6}){
        assert(Candidate(Good(first,second)));
        ++candidates;
    }
    assert(candidates==9u);
    unsigned rejected=0u;
    const auto check=[&](TwoPassInput x,R reason) {
        assert(Rejected(x,reason));++rejected;
    };
    {auto x=Good();x.first=0;check(x,R::UnsupportedStage);}
    {auto x=Good();x.second=4;check(x,R::UnsupportedStage);}
    {auto x=Good();x.source={1920u,1080u};check(x,R::WrongSourceOrTarget);}
    {auto x=Good();x.target={1920u,1080u};check(x,R::WrongSourceOrTarget);}
    {auto x=Good();x.intermediate={1920u,1000u};check(x,R::InvalidShape);}
    {auto x=Good();x.intermediate={3840u,2160u};check(x,R::InvalidShape);}
    {auto x=Good();x.intermediate={1280u,720u};check(x,R::InvalidShape);}
    {auto x=Good();x.first_image=0u;check(x,R::MissingNativeImageOwnership);}
    {auto x=Good();x.second_view=x.first_view;check(x,R::MissingNativeImageOwnership);}
    {auto x=Good();x.first_image=x.source_image;check(x,R::MissingNativeImageOwnership);}
    {auto x=Good();x.second_image=x.first_image;check(x,R::MissingNativeImageOwnership);}
    {auto x=Good();x.first_renderpass_recorded=false;check(x,R::MissingBarrier);}
    {auto x=Good();x.second_renderpass_recorded=false;check(x,R::MissingBarrier);}
    {auto x=Good();x.color_write_to_fragment_read_barrier=false;check(x,R::MissingBarrier);}
    {auto x=Good();x.same_vulkan_queue=false;check(x,R::MissingFence);}
    {auto x=Good();x.both_owners_live_through_gpu_tick=false;check(x,R::MissingFence);}
    std::cout<<"R09_NATIVE_TWO_SPATIAL_OWNERS_HOST_PASS candidates="
             <<candidates<<" negatives="<<rejected
             <<" actual_FSR_SGSR_owner_source=SEPARATE_RESEARCH"
                " runtime=OFF\n";
}
