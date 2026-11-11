// SPDX-License-Identifier: GPL-3.0-or-later
#include "dlss_nr_min_720_spatial_bridge.h"
#include <cassert>
#include <iostream>
using namespace Eden::Graphics::DlssNrMin;
using R=SpatialBridgeReason;
static SpatialBridgeEvidence Fixture(int filter,Extent output){
    SpatialBridgeEvidence e{};
    e.neural_mode=4;
    e.filter=filter;
    e.guest={1u,11u,{1280u,720u}};
    e.neural={2u,22u,{1280u,720u}};
    e.output={3u,33u,output};
    e.authenticated_original_model=true;
    e.original_152_gpu_recorded=true;
    e.guest_frame_ready=true;
    e.antialiasing_disabled=true;
    e.no_pre_neural_scaling=true;
    e.original_neural_image_completed=true;
    e.compute_to_fragment_barrier=true;
    e.actual_filter_pass_recorded=true;
    e.final_image_composited=true;
    e.same_vulkan_scheduler_queue=true;
    e.all_images_held_through_gpu_tick=true;
    e.full_crop_no_msaa=true;
    return e;
}
static void Reject(SpatialBridgeEvidence e,R reason){
    const auto result=AssessPostNeuralSpatial(e);
    assert(result.reason==reason);
    assert(!result.host_shape_qualified);
    assert(!result.runtime_executable);
}
int main(){
    static_assert(!kPostNeuralSpatialRuntimeWired);
    static_assert(!kPs5MinRuntimeQualified);
    static_assert(!ValidSpatialFilter(-1));
    static_assert(!ValidSpatialFilter(7));
    static_assert(SelectSpatialBackend(0)==SpatialBackend::NativeSampler);
    static_assert(SelectSpatialBackend(1)==SpatialBackend::FsrEasuRcas);
    static_assert(SelectSpatialBackend(5)==SpatialBackend::SgsrOnePass);
    static_assert(SelectSpatialBackend(6)==SpatialBackend::SgsrOnePass);
    unsigned candidates=0u,negative=0u;
    for(const auto extent:{Extent{1920u,1080u},Extent{2560u,1440u},
                           Extent{3840u,2160u}}){
        for(int filter=0;filter<=6;++filter){
            auto e=Fixture(filter,extent);
            const auto r=AssessPostNeuralSpatial(e);
            assert(r.reason==R::HostCandidateOnly);
            assert(r.host_shape_qualified&&!r.runtime_executable);
            assert(r.filter_input.image==2u&&r.filter_input.view==22u);
            assert(r.output.extent.width==extent.width);
            assert(r.output.extent.height==extent.height);
            assert(r.backend==SelectSpatialBackend(filter));
            candidates++;
        }
    }
    auto valid=Fixture(1,{3840u,2160u});
    auto test=[&](SpatialBridgeEvidence e,R reason){
        Reject(e,reason);negative++;
    };
    {auto e=valid;e.neural_mode=0;test(e,R::NoOriginal);}
    {auto e=valid;e.neural_mode=5;test(e,R::NoOriginal);}
    {auto e=valid;e.authenticated_original_model=false;test(e,R::NoOriginal);}
    {auto e=valid;e.original_152_gpu_recorded=false;test(e,R::NoOriginal);}
    {auto e=valid;e.filter=-1;test(e,R::UnsupportedFilter);}
    {auto e=valid;e.filter=7;test(e,R::UnsupportedFilter);}
    {auto e=valid;e.guest_frame_ready=false;test(e,R::MissingGuestOrNeuralImage);}
    {auto e=valid;e.guest.view=0u;test(e,R::MissingGuestOrNeuralImage);}
    {auto e=valid;e.neural.image=0u;test(e,R::MissingGuestOrNeuralImage);}
    {auto e=valid;e.neural.image=e.guest.image;test(e,R::MissingGuestOrNeuralImage);}
    {auto e=valid;e.neural.view=e.guest.view;test(e,R::MissingGuestOrNeuralImage);}
    {auto e=valid;e.neural.extent={1920u,1080u};test(e,R::InvalidRasterOrOutput);}
    {auto e=valid;e.guest.extent={640u,360u};test(e,R::InvalidRasterOrOutput);}
    {auto e=valid;e.output.extent={4096u,2160u};test(e,R::InvalidRasterOrOutput);}
    {auto e=valid;e.antialiasing_disabled=false;test(e,R::WrongOperationOrder);}
    {auto e=valid;e.no_pre_neural_scaling=false;test(e,R::WrongOperationOrder);}
    {auto e=valid;e.original_neural_image_completed=false;test(e,R::WrongOperationOrder);}
    {auto e=valid;e.compute_to_fragment_barrier=false;test(e,R::WrongOperationOrder);}
    {auto e=valid;e.full_crop_no_msaa=false;test(e,R::WrongOperationOrder);}
    {auto e=valid;e.final_image_composited=false;test(e,R::WrongOperationOrder);}
    {auto e=valid;e.actual_filter_pass_recorded=false;test(e,R::WrongOperationOrder);}
    {auto e=valid;e.same_vulkan_scheduler_queue=false;test(e,R::MissingImageLifetime);}
    {auto e=valid;e.all_images_held_through_gpu_tick=false;test(e,R::MissingImageLifetime);}
    {auto e=valid;e.output.image=0u;test(e,R::MissingGuestOrNeuralImage);}
    {auto e=valid;e.output.view=0u;test(e,R::MissingGuestOrNeuralImage);}
    {auto e=valid;e.output.image=e.neural.image;test(e,R::MissingGuestOrNeuralImage);}
    {auto e=valid;e.output.view=e.neural.view;test(e,R::MissingGuestOrNeuralImage);}
    // Native presentation scaling uses the true final real composite:
    // no extra FSR/SGSR image is required by the 4 generic sampler filters.
    for(int filter:{0,2,3,4}){
        auto e=Fixture(filter,{3840u,2160u});
        e.output.image=0u;e.output.view=0u;
        const auto result=AssessPostNeuralSpatial(e);
        assert(result.host_shape_qualified);
        assert(result.backend==SpatialBackend::NativeSampler);
        assert(!result.runtime_executable);
    }
    std::cout<<"R09_MIN_720_ALL_7_SPATIAL_BRIDGES_HOST_PASS candidates="
             <<candidates<<" negative="<<negative
             <<" neural_runtime=OFF upscaler_runtime=OFF ps5=NO\n";
}
