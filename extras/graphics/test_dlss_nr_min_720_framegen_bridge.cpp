// SPDX-License-Identifier: GPL-3.0-or-later
#include "dlss_nr_min_720_framegen_bridge.h"
#include <cassert>
#include <cstdint>
#include <iostream>
using namespace Eden::Graphics::DlssNrMin;
namespace FG=Eden::FeatureLab;
using R=FramegenBridgeReason;

static FramegenBridgeInput Fixture(FG::FrameGeneration mode){
    FramegenBridgeInput x{};
    x.neural_mode=4;
    x.method=mode;
    x.graphics.native_vulkan=true;
    x.graphics.mihawk_compute=true;
    x.graphics.model_weights_verified_and_loaded=true;
    x.graphics.fsr3_optical_flow=true;
    x.graphics.lossless_scaling_provider_available=true;
    x.original_152_model_authenticated=true;
    x.original_152_gpu_recorded=true;
    x.guest={11u,12u,{1280u,720u}};
    x.neural={21u,22u,{1280u,720u}};
    x.post_spatial={31u,32u,{3840u,2160u}};
    x.neural_result_submitted=true;
    x.post_spatial_filter_recorded=true;
    x.final_post_spatial_frame_composited=true;
    x.stable_real_frame_pair=true;
    x.independent_guest_hud_or_explicitly_verified=true;
    x.same_graphics_queue=true;
    x.prior_real_frame_gpu_fence_complete=true;
    x.resource_lifetime_through_interpolation_fence=true;
    x.confirmed_free_vram_and_frametime=true;
    x.lossless_native_shaders_validated=true;
    x.display_hz=60u;
    x.real_game_fps=30u;
    return x;
}
static void Expect(FramegenBridgeInput x,R why){
    const auto candidate=AssessPostNeuralFramegen(x);
    assert(candidate.reason==why);
    assert(!candidate.ps5_runtime_enabled);
    if(why!=R::HostCandidateOnly)assert(!candidate.host_shape_qualified);
}
int main(){
    static_assert(!kNeuralToFramegenRuntimeWired);
    static_assert(!kPostNeuralFsrRuntimeWired);
    static_assert(!kPs5MinRuntimeQualified);
    // Current user selection remains exclusive: no change to any
    // existing working framegen mode when neural is OFF.
    for(int fg=0;fg<=3;++fg){
        assert(EffectiveCompositeFramegen(0,fg)==fg);
        for(int neural=1;neural<=5;++neural)
            assert(EffectiveCompositeFramegen(neural,fg)==0);
    }
    assert(EffectiveCompositeFramegen(0,4)==0);
    assert(EffectiveCompositeFramegen(4,-1)==0);
    for(auto method:{FG::FrameGeneration::MihawkGen,
                     FG::FrameGeneration::Fsr3Vulkan,
                     FG::FrameGeneration::LosslessScaling}){
        auto x=Fixture(method);
        const auto candidate=AssessPostNeuralFramegen(x);
        assert(candidate.reason==R::HostCandidateOnly);
        assert(candidate.host_shape_qualified);
        assert(!candidate.ps5_runtime_enabled);
        assert(candidate.downstream==method);
        assert(candidate.post_spatial_source.image==x.post_spatial.image);
        assert(candidate.post_spatial_source.view==x.post_spatial.view);
        assert(candidate.post_spatial_source.extent.width==3840u);
        // The established FPS/pacing authority remains FramegenPresentGate.
        // First REAL 30fps frame primes history; the next may permit 1
        // synthetic 60Hz display frame. Neither creates a neural frame.
        FG::FramegenPresentGate gate{};
        x.graphics.game_fps=30u;
        FG::PresentGateInput source{};
        source.real_frame_id=41u;
        source.timestamp_ns=1000000000ull;
        source.width=3840u;source.height=2160u;source.output_hz=60u;
        source.display_mode_verified=true;
        auto initial=gate.OnRealFrame(method,x.graphics,source);
        assert(!initial.eligible());
        assert(initial.reason==FG::PresentGateReason::NoStablePair);
        source.real_frame_id=42u;
        source.timestamp_ns+=33333333ull;
        auto consecutive=gate.OnRealFrame(method,x.graphics,source);
        assert(consecutive.eligible()&&consecutive.synthetic_frames==1u);
        source.overlay_changed=true;
        assert(!gate.OnRealFrame(method,x.graphics,source).eligible());
        std::cout<<"R09_MIN_720_POST_FSR_FRAMEGEN_HOST_AB_PASS method="
                 <<static_cast<unsigned>(method)<<" runtime=OFF\n";
    }
    // Matrix: A4K Detail/Soft/Denoise × 7 spatial filters ×
    // Mihawk, FSR3 and LSFG × 1080p/1440p/2160p. The native A4K
    // x2 output is 2560x1440 before the spatial/composite stage.
    // This certifies host gate logic only, never PS5 FG throughput.
    unsigned a4k_fg_candidates=0u;
    for(int neural_mode=1;neural_mode<=3;++neural_mode){
        for(int spatial=0;spatial<=6;++spatial){
            for(auto method:{FG::FrameGeneration::MihawkGen,
                             FG::FrameGeneration::Fsr3Vulkan,
                             FG::FrameGeneration::LosslessScaling}){
                for(const auto output:{Extent{1920u,1080u},
                                       Extent{2560u,1440u},
                                       Extent{3840u,2160u}}){
                    auto e=Fixture(method);
                    e.neural_mode=neural_mode;
                    e.original_152_model_authenticated=false;
                    e.original_152_gpu_recorded=false;
                    e.a4k_native_x2_gpu_recorded=true;
                    e.a4k_output_image_and_view_identified=true;
                    e.neural.extent={2560u,1440u};
                    e.spatial_filter=spatial;
                    e.post_spatial.extent=output;
                    const auto candidate=AssessPostNeuralFramegen(e);
                    const bool shader_downscale=output.width<2560u &&
                        SelectSpatialBackend(spatial)!=SpatialBackend::NativeSampler;
                    if(shader_downscale){
                        assert(candidate.reason==R::WrongOrderOrExtent);
                        assert(!candidate.host_shape_qualified);
                        assert(!candidate.ps5_runtime_enabled);
                        continue;
                    }
                    assert(candidate.reason==R::HostCandidateOnly);
                    assert(candidate.a4k_source);
                    assert(candidate.post_spatial_source.extent.width==output.width);
                    assert(candidate.post_spatial_source.image==e.post_spatial.image);
                    assert(candidate.host_shape_qualified);
                    assert(!candidate.ps5_runtime_enabled);
                    a4k_fg_candidates++;
                }
            }
        }
    }
    assert(a4k_fg_candidates==162u);
    auto q=Fixture(FG::FrameGeneration::MihawkGen);
    q.neural_mode=0;Expect(q,R::NoNeuralSelection);
    q=Fixture(FG::FrameGeneration::MihawkGen);
    q.neural_mode=5;Expect(q,R::MissingOriginal);
    q=Fixture(FG::FrameGeneration::Off);Expect(q,R::Disabled);
    q=Fixture(FG::FrameGeneration::DlssPcOnlyUnsupported);
    Expect(q,R::UnsupportedBackend);
    // A4K must fail unless a REAL native x2 image and its true VkImage
    // owner have been verified. A disabled or stale A4K mode must never
    // leak into a misleading framegen eligibility result.
    q=Fixture(FG::FrameGeneration::MihawkGen);
    q.neural_mode=1;q.neural.extent={2560u,1440u};
    q.original_152_model_authenticated=false;
    q.original_152_gpu_recorded=false;
    Expect(q,R::MissingOriginal);
    q.a4k_native_x2_gpu_recorded=true;
    Expect(q,R::MissingOriginal);
    q.a4k_output_image_and_view_identified=true;
    q.neural.extent={1280u,720u};
    Expect(q,R::WrongOrderOrExtent);
    q=Fixture(FG::FrameGeneration::MihawkGen);
    q.original_152_model_authenticated=false;Expect(q,R::MissingOriginal);
    q=Fixture(FG::FrameGeneration::MihawkGen);
    q.original_152_gpu_recorded=false;Expect(q,R::MissingOriginal);
    q=Fixture(FG::FrameGeneration::MihawkGen);
    q.neural.image=0u;Expect(q,R::MissingGuestOrNeuralImage);
    q=Fixture(FG::FrameGeneration::MihawkGen);
    q.post_spatial.view=0u;Expect(q,R::MissingGuestOrNeuralImage);
    q=Fixture(FG::FrameGeneration::MihawkGen);
    q.post_spatial.image=q.neural.image;Expect(q,R::MissingGuestOrNeuralImage);
    q=Fixture(FG::FrameGeneration::MihawkGen);
    q.post_spatial.extent={1280u,720u};Expect(q,R::WrongOrderOrExtent);
    q=Fixture(FG::FrameGeneration::MihawkGen);
    q.neural.extent={1920u,1080u};Expect(q,R::WrongOrderOrExtent);
    q=Fixture(FG::FrameGeneration::MihawkGen);
    q.post_spatial_filter_recorded=false;
    Expect(q,R::WrongOrderOrExtent);
    q=Fixture(FG::FrameGeneration::MihawkGen);
    q.final_post_spatial_frame_composited=false;
    Expect(q,R::WrongOrderOrExtent);
    q=Fixture(FG::FrameGeneration::MihawkGen);
    q.neural_result_submitted=false;Expect(q,R::MissingGpuOwnership);
    q=Fixture(FG::FrameGeneration::MihawkGen);
    q.same_graphics_queue=false;Expect(q,R::MissingGpuOwnership);
    q=Fixture(FG::FrameGeneration::MihawkGen);
    q.prior_real_frame_gpu_fence_complete=false;
    Expect(q,R::MissingGpuOwnership);
    q=Fixture(FG::FrameGeneration::MihawkGen);
    q.resource_lifetime_through_interpolation_fence=false;
    Expect(q,R::MissingGpuOwnership);
    q=Fixture(FG::FrameGeneration::MihawkGen);
    q.stable_real_frame_pair=false;Expect(q,R::UnsafeHistoryOrHud);
    q=Fixture(FG::FrameGeneration::MihawkGen);
    q.independent_guest_hud_or_explicitly_verified=false;
    Expect(q,R::UnsafeHistoryOrHud);
    q=Fixture(FG::FrameGeneration::MihawkGen);
    q.display_hz=75u;Expect(q,R::UnsafeHistoryOrHud);
    q=Fixture(FG::FrameGeneration::MihawkGen);
    q.real_game_fps=25u;Expect(q,R::UnsafeHistoryOrHud);
    q=Fixture(FG::FrameGeneration::MihawkGen);
    q.real_game_fps=60u;Expect(q,R::UnsafeHistoryOrHud);
    q=Fixture(FG::FrameGeneration::MihawkGen);
    q.confirmed_free_vram_and_frametime=false;Expect(q,R::UnmeasuredBudget);
    q=Fixture(FG::FrameGeneration::MihawkGen);
    q.graphics.model_weights_verified_and_loaded=false;
    Expect(q,R::InvalidProvider);
    q=Fixture(FG::FrameGeneration::Fsr3Vulkan);
    q.graphics.fsr3_optical_flow=false;Expect(q,R::InvalidProvider);
    q=Fixture(FG::FrameGeneration::LosslessScaling);
    q.graphics.lossless_scaling_provider_available=false;
    Expect(q,R::InvalidProvider);
    q=Fixture(FG::FrameGeneration::LosslessScaling);
    q.lossless_native_shaders_validated=false;Expect(q,R::InvalidProvider);
    std::cout<<"R09_MIN_720_MIHAWK_FSR3_LSFG_BRIDGE_PASS "
                "A4K_189_MATRIX_CANDIDATES_NO_PS5_FG_ENABLE\n";
}
