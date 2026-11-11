// SPDX-License-Identifier: GPL-3.0-or-later
#include "neural_pipeline_recipe.h"
#include <cassert>
#include <iostream>
using namespace Eden::Graphics::PipelineComposer;
using K=Kind;
using R=Reason;
constexpr Extent p360{640u,360u},p720{1280u,720u},
                 p1440{2560u,1440u},p4k{3840u,2160u};
static RecipeStage S(K kind,int method,Extent target,
                     bool all_generated=false){
    return RecipeStage{kind,method,target,all_generated};
}
static StageEvidence Proof(unsigned idx){
    StageEvidence p{};
    p.image=1000u+idx*10u;
    p.view=p.image+1u;
    p.native_gpu_pass_recorded=true;
    p.compatible_queue=true;
    p.producer_to_consumer_visible=true;
    p.owner_retained_through_gpu_fence=true;
    p.trained_model_and_weights_verified=true;
    p.two_distinct_composited_real_frames=true;
    p.hud_history_safe=true;
    p.native_fg_provider_verified=true;
    p.measured_gpu_memory_and_time_budget=true;
    return p;
}
int main(){
    static_assert(kRecipeVersion==1u);
    static_assert(!kComposablePs5RuntimeQualified);
    Recipe preset{};
    preset.source_extent=p360;
    assert(InsertStep(preset,0,S(K::Spatial,1,p720)));
    assert(InsertStep(preset,1,S(K::Neural,4,p720)));
    assert(InsertStep(preset,2,S(K::Spatial,5,p1440)));
    assert(InsertStep(preset,3,S(K::Spatial,4,p4k)));
    assert(InsertStep(preset,4,S(K::ComposeRealFrame,0,p4k)));
    assert(InsertStep(preset,5,S(K::FrameGeneration,1,p4k)));
    assert(InsertStep(preset,6,S(K::Present,0,p4k)));
    assert(preset.count==7u);
    Bindings native{};
    native.guest_image=1u;
    native.guest_view=2u;
    for(std::size_t i=0;i+1u<preset.count;++i)
        native.stages[i]=Proof(static_cast<unsigned>(i));
    auto v=QualifyBoundRecipe(preset,native);
    assert(v.reason==R::HostCandidateOnly);
    assert(v.result==p4k);
    assert(v.spatial_passes==3u);
    assert(v.neural&&v.frame_generation);
    assert(!v.runtime_enabled);
    // Inserting a valid additional native-sampler stage in the middle
    // preserves following order. The saved recipe still contains NO
    // Vulkan handles, weights, or permission assertions.
    assert(InsertStep(preset,4,S(K::Spatial,2,p4k)));
    assert(preset.count==8u);
    for(std::size_t i=0;i+1u<preset.count;++i)
        native.stages[i]=Proof(static_cast<unsigned>(i));
    native.stages[7]=StageEvidence{};
    v=QualifyBoundRecipe(preset,native);
    assert(v.reason==R::HostCandidateOnly&&v.spatial_passes==4u);
    assert(RemoveStep(preset,4));
    assert(preset.count==7u);
    for(std::size_t i=0;i+1u<preset.count;++i)
        native.stages[i]=Proof(static_cast<unsigned>(i));
    native.stages[6]=StageEvidence{};
    v=QualifyBoundRecipe(preset,native);
    assert(v.reason==R::HostCandidateOnly&&v.spatial_passes==3u);
    // Native bindings are MANDATORY: never manufacture evidence.
    auto no_real_images=native;
    no_real_images.stages[2].image=0u;
    assert(QualifyBoundRecipe(preset,no_real_images).reason==
           R::MissingNativeVkImageAndView);
    no_real_images=native;
    no_real_images.stages[5].measured_gpu_memory_and_time_budget=false;
    assert(QualifyBoundRecipe(preset,no_real_images).reason==
           R::MissingHistoryHudProviderOrBudget);
    no_real_images=native;
    no_real_images.stages[1].trained_model_and_weights_verified=false;
    assert(QualifyBoundRecipe(preset,no_real_images).reason==
           R::UnknownStageOrProvider);
    no_real_images=native;
    no_real_images.stages[1].owner_retained_through_gpu_fence=false;
    assert(QualifyBoundRecipe(preset,no_real_images).reason==
           R::MissingQueueBarrierOrFence);
    // A generation stage may precede an upscaler only when all stream
    // surfaces are processed; do NOT leave synthetic images unscaled.
    Recipe after_fg{};
    assert(InsertStep(after_fg,0,S(K::ComposeRealFrame,0,p720)));
    assert(InsertStep(after_fg,1,S(K::FrameGeneration,3,p720)));
    assert(InsertStep(after_fg,2,S(K::Spatial,1,p1440,true)));
    assert(InsertStep(after_fg,3,S(K::Present,0,p1440)));
    auto proof=native;proof.guest_image=1u;proof.guest_view=2u;
    for(unsigned i=0;i<3u;++i)proof.stages[i]=Proof(i);
    proof.stages[3]=StageEvidence{};
    auto result=QualifyBoundRecipe(after_fg,proof);
    assert(result.reason==R::HostCandidateOnly&&result.frame_generation);
    after_fg.stages[2].processes_real_and_generated=false;
    assert(QualifyBoundRecipe(after_fg,proof).reason==
           R::GeneratedFramesNotProcessed);
    // Terminal Present cannot secretly allocate a new image or be omitted.
    after_fg.stages[2].processes_real_and_generated=true;
    proof.stages[3].image=777u;
    assert(QualifyBoundRecipe(after_fg,proof).reason==R::MissingInput);
    proof.stages[3].image=0u;
    after_fg.count=3u;
    assert(QualifyBoundRecipe(after_fg,proof).reason==R::MissingPresent);
    after_fg.count=4u;
    after_fg.version=2u;
    assert(QualifyBoundRecipe(after_fg,proof).reason==R::MissingInput);
    assert(!InsertStep(after_fg,0,S(K::Spatial,1,p720)));
    after_fg.version=kRecipeVersion;
    after_fg.count=kMaxSteps;
    assert(!InsertStep(after_fg,kMaxSteps,S(K::Present,0,p4k)));
    assert(!RemoveStep(after_fg,kMaxSteps));
    // Prototype is a versioned sequence of types/ids/resolutions only.
    // The separate live native owners must bind real resources later.
    std::cout<<"R09_COMPOSABLE_RECIPE_V1_HOST_PASS "
             <<"add_remove_reorder=YES native_bindings_required=YES "
             <<"post_FG_all_streams_guard=YES runtime=OFF\n";
}
