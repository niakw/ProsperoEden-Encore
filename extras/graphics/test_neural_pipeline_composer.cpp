// SPDX-License-Identifier: GPL-3.0-or-later
// CPU-only graph contracts with public opaque IDs; NOT a neural GPU test.
#include "neural_pipeline_composer.h"
#include <cassert>
#include <initializer_list>
#include <iostream>
using namespace Eden::Graphics::PipelineComposer;
using K=Kind;
using R=Reason;
using E=Extent;
static Step Make(K k,int method,E to,unsigned id){
    Step s{};
    s.kind=k;s.method=method;s.output=to;
    s.image=100u+id*10u;s.view=101u+id*10u;
    s.native_gpu_pass_recorded=true;
    s.compatible_queue=true;
    s.producer_to_consumer_visible=true;
    s.owner_retained_through_gpu_fence=true;
    s.trained_model_and_weights_verified=true;
    s.two_distinct_composited_real_frames=true;
    s.hud_history_safe=true;
    s.native_fg_provider_verified=true;
    s.measured_gpu_memory_and_time_budget=true;
    s.processes_real_and_generated=true;
    return s;
}
static Step End(E size){
    Step s{};s.kind=K::Present;s.output=size;return s;
}
static Chain MakeChain(E source,std::initializer_list<Step> steps){
    Chain out{};out.source_extent=source;out.count=steps.size();
    std::size_t i=0u;
    for(auto& s:steps){
        if(i<kMaxSteps)out.steps[i]=s;
        ++i;
    }
    return out;
}
static void Accept(const Chain& c,E target,unsigned spatial,bool neural,
                   bool fg){
    const auto v=Plan(c);
    assert(v.reason==R::HostCandidateOnly);
    assert(v.shape_qualified);
    assert(!v.runtime_enabled);
    assert(v.result==target);
    assert(v.spatial_passes==spatial);
    assert(v.neural==neural);
    assert(v.frame_generation==fg);
}
static void Reject(const Chain& c,R reason){
    const auto v=Plan(c);
    assert(v.reason==reason);
    assert(!v.shape_qualified&&!v.runtime_enabled);
}
int main(){
    static_assert(!kComposablePs5RuntimeQualified);
    static_assert(ValidExtent({640u,360u}));
    static_assert(ValidExtent({1280u,720u}));
    static_assert(!ValidExtent({1024u,768u}));
    static_assert(ShaderUpscaleOnly(1)&&ShaderUpscaleOnly(5)&&ShaderUpscaleOnly(6));
    static_assert(!ShaderUpscaleOnly(0)&&!ShaderUpscaleOnly(4));

    constexpr E p360{640u,360u},p720{1280u,720u},p1080{1920u,1080u},
                p1440{2560u,1440u},p4k{3840u,2160u};
    // Spatial only -> real compositing -> present; no neural prerequisite.
    Accept(MakeChain(p720,{
        Make(K::Spatial,1,p1440,1),Make(K::ComposeRealFrame,0,p1440,2),
        End(p1440)}),p1440,1u,false,false);
    // Native spatial only; no extra real compositor needed before present.
    Accept(MakeChain(p4k,{Make(K::Spatial,2,p1080,1),End(p1080)}),
           p1080,1u,false,false);
    // Neural -> upscale -> present; as requested, framegen is optional.
    Accept(MakeChain(p720,{
        Make(K::Neural,4,p720,1),Make(K::Spatial,1,p4k,2),End(p4k)}),
        p4k,1u,true,false);
    // Spatial -> neural -> spatial -> spatial -> render frame -> FG -> present.
    Accept(MakeChain(p360,{
        Make(K::Spatial,1,p720,1),Make(K::Neural,4,p720,2),
        Make(K::Spatial,5,p1440,3),Make(K::Spatial,4,p4k,4),
        Make(K::ComposeRealFrame,0,p4k,5),
        Make(K::FrameGeneration,1,p4k,6),End(p4k)}),
        p4k,3u,true,true);
    // Two independent upscalers before the compositor, then LSFG.
    Accept(MakeChain(p720,{
        Make(K::Spatial,1,p1440,1),Make(K::Spatial,5,p4k,2),
        Make(K::ComposeRealFrame,0,p4k,3),
        Make(K::FrameGeneration,3,p4k,4),End(p4k)}),
        p4k,2u,false,true);
    // A4K x2 -> FSR1 -> render -> FSR3 optical flow (FG).
    for(int mode=1;mode<=3;++mode)
      for(int spatial:{0,1,2,3,4,5,6})
        for(int fg=1;fg<=3;++fg){
        auto c=MakeChain(p720,{
            Make(K::Neural,mode,p1440,1),
            Make(K::Spatial,spatial,p4k,2),
            Make(K::ComposeRealFrame,0,p4k,3),
            Make(K::FrameGeneration,fg,p4k,4),End(p4k)});
        Accept(c,p4k,1u,true,true);
      }
    // A4K 1440 -> native downsample to 1080 -> FSR1 upscale to 4K.
    Accept(MakeChain(p720,{
        Make(K::Neural,2,p1440,1),Make(K::Spatial,4,p1080,2),
        Make(K::Spatial,1,p4k,3),End(p4k)}),p4k,2u,true,false);
    // FG can precede spatial only if the filter genuinely processes
    // BOTH the original/composited real and its generated frames.
    auto fg_before_spatial=MakeChain(p720,{
        Make(K::ComposeRealFrame,0,p720,1),
        Make(K::FrameGeneration,1,p720,2),
        Make(K::Spatial,1,p1440,3),End(p1440)});
    Accept(fg_before_spatial,p1440,1u,false,true);
    fg_before_spatial.steps[2].processes_real_and_generated=false;
    Reject(fg_before_spatial,R::GeneratedFramesNotProcessed);
    // Same requirement applies to a SECOND composition after FG.
    auto fg_then_compose=MakeChain(p720,{
        Make(K::ComposeRealFrame,0,p720,1),
        Make(K::FrameGeneration,2,p720,2),
        Make(K::ComposeRealFrame,0,p720,3),End(p720)});
    Accept(fg_then_compose,p720,0u,false,true);
    fg_then_compose.steps[2].processes_real_and_generated=false;
    Reject(fg_then_compose,R::GeneratedFramesNotProcessed);

    // Every A4K/Original engine with all 7x7 ordered spatial pairs
    // and each FG method. The first upscaler can be BEFORE the neural
    // engine; both later filters may repeat and operate at 4K.
    // This is strictly CPU topology/ownership evidence, not GPU FPS.
    unsigned order_matrix=0u;
    for(int neural=1;neural<=4;++neural)
      for(int before=0;before<=6;++before)
        for(int after=0;after<=6;++after)
          for(int fg_method=1;fg_method<=3;++fg_method){
          const E neural_extent=neural<=3?p1440:p720;
          auto c=MakeChain(p360,{
              Make(K::Spatial,before,p720,1),
              Make(K::Neural,neural,neural_extent,2),
              Make(K::Spatial,after,p4k,3),
              Make(K::Spatial,4,p4k,4),
              Make(K::ComposeRealFrame,0,p4k,5),
              Make(K::FrameGeneration,fg_method,p4k,6),
              End(p4k)});
          Accept(c,p4k,3u,true,true);
          ++order_matrix;
        }
    assert(order_matrix==588u);
    // A build may declare many stages but may not alias an earlier
    // VkImage/VkImageView even if the current stage has moved on.
    auto stale_reuse=MakeChain(p720,{
        Make(K::Spatial,1,p1440,1),
        Make(K::Spatial,2,p4k,2),
        Make(K::Spatial,4,p4k,3),End(p4k)});
    stale_reuse.steps[2].image=stale_reuse.steps[0].image;
    Reject(stale_reuse,R::MissingNativeVkImageAndView);

    // Shape, nonduplicated model and denoiser ordering failures.
    Reject(MakeChain(p1440,{Make(K::Neural,4,p1440,1),End(p1440)}),
           R::NeuralInputNot720);
    Reject(MakeChain(p720,{Make(K::Neural,4,p1440,1),End(p1440)}),
           R::NeuralOutputMismatch);
    Reject(MakeChain(p720,{Make(K::Neural,5,p720,1),End(p720)}),
           R::UnknownStageOrProvider);
    Reject(MakeChain(p720,{Make(K::Neural,4,p720,1),
           Make(K::Neural,4,p720,2),End(p720)}),R::DuplicateNeural);
    Reject(MakeChain(p720,{Make(K::Spatial,1,p360,1),End(p360)}),
           R::SpatialShaderCannotDownscale);
    Reject(MakeChain(p1440,{Make(K::Spatial,5,p1080,1),End(p1080)}),
           R::SpatialShaderCannotDownscale);
    Reject(MakeChain(p720,{Make(K::FrameGeneration,1,p720,1),
           End(p720)}),R::FramegenRequiresComposedRealFrames);
    Reject(MakeChain(p720,{
        Make(K::ComposeRealFrame,0,p720,1),Make(K::FrameGeneration,2,p720,2),
        Make(K::Neural,4,p720,3),End(p720)}),R::NeuralAfterGeneration);
    Reject(MakeChain(p720,{
        Make(K::ComposeRealFrame,0,p720,1),Make(K::FrameGeneration,2,p720,2),
        Make(K::FrameGeneration,3,p720,3),End(p720)}),
        R::DuplicateFramegen);
    Reject(MakeChain(p720,{Make(K::Spatial,8,p1080,1),End(p1080)}),
           R::UnknownStageOrProvider);

    auto modified=MakeChain(p720,{Make(K::Neural,4,p720,1),
                                  Make(K::Spatial,1,p1440,2),End(p1440)});
    modified.steps[0].trained_model_and_weights_verified=false;
    Reject(modified,R::UnknownStageOrProvider);
    modified.steps[0].trained_model_and_weights_verified=true;
    modified.steps[0].native_gpu_pass_recorded=false;
    Reject(modified,R::MissingQueueBarrierOrFence);
    modified.steps[0].native_gpu_pass_recorded=true;
    modified.steps[0].owner_retained_through_gpu_fence=false;
    Reject(modified,R::MissingQueueBarrierOrFence);
    modified.steps[0].owner_retained_through_gpu_fence=true;
    modified.steps[1].image=modified.steps[0].image;
    Reject(modified,R::MissingNativeVkImageAndView);
    modified.steps[1].image=100u+2u*10u;
    modified.steps[1].view=modified.steps[0].view;
    Reject(modified,R::MissingNativeVkImageAndView);
    modified.steps[1].view=101u+2u*10u;
    modified.steps[1].output={1000u,720u};
    Reject(modified,R::InvalidExtent);
    modified.steps[1].output=p1440;
    modified.steps[2].output=p1080;
    Reject(modified,R::InvalidPresentOrder);
    modified.steps[2].output=p1440;
    modified.count=2u;
    Reject(modified,R::MissingPresent);
    modified.count=3u;
    Accept(modified,p1440,1u,true,false);

    auto fg=MakeChain(p720,{Make(K::ComposeRealFrame,0,p720,1),
        Make(K::FrameGeneration,1,p720,2),End(p720)});
    fg.steps[1].two_distinct_composited_real_frames=false;
    Reject(fg,R::MissingHistoryHudProviderOrBudget);
    fg.steps[1].two_distinct_composited_real_frames=true;
    fg.steps[1].hud_history_safe=false;
    Reject(fg,R::MissingHistoryHudProviderOrBudget);
    fg.steps[1].hud_history_safe=true;
    fg.steps[1].native_fg_provider_verified=false;
    Reject(fg,R::MissingHistoryHudProviderOrBudget);
    fg.steps[1].native_fg_provider_verified=true;
    fg.steps[1].measured_gpu_memory_and_time_budget=false;
    Reject(fg,R::MissingHistoryHudProviderOrBudget);
    fg.steps[1].measured_gpu_memory_and_time_budget=true;
    Accept(fg,p720,0u,false,true);
    auto empty=Chain{};empty.count=0u;
    Reject(empty,R::EmptyOrTooMany);
    empty.count=kMaxSteps+1u;Reject(empty,R::EmptyOrTooMany);
    std::cout<<"R09_COMPOSABLE_VIDEO_GRAPH_HOST_PASS "
                "spatial_only=YES neural_after_spatial=YES "
                "repeated_spatial=YES post_FG_spatial=CONDITIONAL "
                "a4k_spatial_fg_matrix=63 ordered_permutations="<<order_matrix
             <<" unsafe_orderings=REJECTED "
                "ps5_runtime=OFF\n";
}
