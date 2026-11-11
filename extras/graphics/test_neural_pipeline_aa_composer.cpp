// SPDX-License-Identifier: GPL-3.0-or-later
// Host-only R09 AA ordering & real-binding policy tests, NOT a GPU AA pass.
// FXAA/SMAA Ultra/FXAA+ are 1x fullscreen post stages. Forced MSAA
// belongs to the guest raster and must be resolved BEFORE all post stages.
#include "neural_pipeline_recipe.h"
#include <cassert>
#include <cstdint>
#include <initializer_list>
#include <iostream>
using namespace Eden::Graphics::PipelineComposer;
using K=Kind;
using R=Reason;
using E=Extent;
constexpr E p720{1280u,720u},p1440{2560u,1440u},p4k{3840u,2160u};

static Step S(K kind,int method,E extent,unsigned id) {
    Step s{};
    s.kind=kind;s.method=method;s.output=extent;
    s.image=1000u+10u*id;s.view=s.image+1u;
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
static Chain End(Chain c, E extent) {
    assert(c.count<kMaxSteps);
    c.steps[c.count].kind=K::Present;
    c.steps[c.count].output=extent;
    ++c.count;
    return c;
}
static Chain Matrix(int aa,int spatial,int fg,int neural,int pos) {
    Chain c{};
    c.source_extent=p720;
    c.source_image=7;c.source_view=8;
    const E neural_extent=neural==4?p720:p1440;
    unsigned id=1u;
    auto push=[&](K k,int method,E extent) {
        assert(c.count<kMaxSteps);
        c.steps[c.count++]=S(k,method,extent,id++);
    };
    if(pos==0)push(K::AntiAlias,aa,p720);
    push(K::Neural,neural,neural_extent);
    if(pos==1)push(K::AntiAlias,aa,neural_extent);
    push(K::Spatial,spatial,p4k);
    if(pos==2)push(K::AntiAlias,aa,p4k);
    push(K::ComposeRealFrame,0,p4k);
    push(K::FrameGeneration,fg,p4k);
    if(pos==3)push(K::AntiAlias,aa,p4k);
    return End(c,p4k);
}
static void Good(const Chain& c,unsigned aaCount) {
    const auto v=Plan(c);
    assert(v.reason==R::HostCandidateOnly);
    assert(v.shape_qualified&&!v.runtime_enabled);
    assert(v.aa_passes==aaCount);
}
static void Bad(const Chain& c,R expected) {
    const auto v=Plan(c);
    assert(v.reason==expected);
    assert(!v.shape_qualified&&!v.runtime_enabled);
}
static StageEvidence NativeEvidence(unsigned i) {
    StageEvidence p{};
    p.image=200u+i*10u;p.view=p.image+1u;
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
int main() {
    static_assert(!kComposablePs5RuntimeQualified);
    static_assert(kRecipeVersion==2u);
    static_assert(IsPostAa(1)&&IsPostAa(2)&&IsPostAa(3));
    static_assert(!IsPostAa(0)&&!IsPostAa(4)&&!IsPostAa(8));
    static_assert(ForcedRasterAa(RasterAa::ForcedX16));
    static_assert(!ForcedRasterAa(RasterAa::GuestNative));
    unsigned matrix=0u;
    for(int neural : {1,4})
      for(int aa=1;aa<=3;++aa)
        for(int spatial=0;spatial<=6;++spatial)
          for(int fg=1;fg<=3;++fg)
            for(int pos=0;pos<4;++pos) {
                auto c=Matrix(aa,spatial,fg,neural,pos);
                Good(c,1u);
                assert(Plan(c).frame_generation);
                assert(Plan(c).neural);
                assert(Plan(c).spatial_passes==1u);
                ++matrix;
            }
    assert(matrix==504u);
    // Stacking all 3 different AA options is a *topological candidate*, NOT
    // a quality recommendation: FXAA/SMAA stacking can blur fine details.
    auto stacked=Matrix(1,5,1,4,0);
    for(std::size_t i=stacked.count;i>2u;--i)
        stacked.steps[i]=stacked.steps[i-1u];
    stacked.steps[2]=S(K::AntiAlias,2,p720,18);
    ++stacked.count;
    // The moved neural is now index 1, the second AA consumes 720p.
    // Add third AA after FSR at 4K without changing the other stage owners.
    std::size_t spatial_index=3u;
    assert(stacked.steps[spatial_index].kind==K::Spatial);
    for(std::size_t i=stacked.count;i>spatial_index+1u;--i)
        stacked.steps[i]=stacked.steps[i-1u];
    stacked.steps[spatial_index+1u]=S(K::AntiAlias,3,p4k,19);
    ++stacked.count;
    Good(stacked,3u);
    // Post-FG AA must process the real AND generated image streams.
    auto post=Matrix(2,1,1,4,3);
    post.steps[post.count-2u].processes_real_and_generated=false;
    Bad(post,R::GeneratedFramesNotProcessed);
    post=Matrix(2,1,1,4,3);
    post.steps[post.count-2u].owner_retained_through_gpu_fence=false;
    Bad(post,R::MissingQueueBarrierOrFence);
    post=Matrix(2,1,1,4,3);
    post.steps[post.count-2u].image=post.steps[0].image;
    Bad(post,R::MissingNativeVkImageAndView);
    post=Matrix(2,1,1,4,0);
    post.steps[0].output=p1440;
    Bad(post,R::PostAaCannotResize);
    // MSAA is not a framebuffer image-space filter; TAA is not qualified.
    for(int msaa : {4,5,6,7}) {
        auto c=Matrix(1,1,1,4,0);
        c.steps[0].method=msaa;
        Bad(c,R::RasterAaNotAFullscreenFilter);
    }
    post=Matrix(1,1,1,4,0);
    post.steps[0].method=8;
    Bad(post,R::TemporalAaMotionHistoryUnqualified);
    post.steps[0].method=0;
    Bad(post,R::UnknownStageOrProvider);
    // Source raster MSAA must have actual guest draw, format/sample,
    // resolve and retire-fence evidence, *before* any fullscreen stage.
    for(auto raster : {RasterAa::GuestNative,RasterAa::ForcedX2,
                       RasterAa::ForcedX4,RasterAa::ForcedX8,
                       RasterAa::ForcedX16}) {
        auto c=Matrix(2,5,2,4,0);
        c.source_raster_aa=raster;
        Bad(c,R::MissingRasterAaResolveOrNativeOwner);
        c.source_raster_resolve_and_owner_verified=true;
        c.source_raster_guest_attachment_safe=true;
        c.source_raster_fences_retired=true;
        Bad(c,R::MissingRasterAaFormatOrBudget);
        c.source_raster_format_and_sample_count_supported=true;
        if(ForcedRasterAa(raster))
            Bad(c,R::MissingRasterAaFormatOrBudget);
        c.source_raster_gpu_budget_measured=true;
        Good(c,1u);
        assert(Plan(c).source_raster_aa==raster);
    }
    auto invalid=Matrix(1,5,1,4,1);
    invalid.source_raster_aa=static_cast<RasterAa>(99);
    Bad(invalid,R::UnknownRasterAa);
    // A persisted v2 recipe stores the AA METHOD and source MSAA choice,
    // NOT Vulkan images, resolve proofs, or optional driver support.
    Recipe saved{};
    saved.source_extent=p720;
    saved.source_raster_aa=RasterAa::ForcedX4;
    saved.count=4;
    saved.stages[0]={K::Neural,4,p720,false};
    saved.stages[1]={K::Spatial,5,p4k,false};
    saved.stages[2]={K::AntiAlias,3,p4k,false};
    saved.stages[3]={K::Present,0,p4k,false};
    Bindings native{};
    native.guest_image=7;native.guest_view=8;
    for(unsigned i=0;i<3u;++i)native.stages[i]=NativeEvidence(i);
    auto v=QualifyBoundRecipe(saved,native);
    assert(v.reason==R::MissingRasterAaResolveOrNativeOwner);
    native.raster_resolve_and_owner_verified=true;
    native.raster_guest_attachment_safe=true;
    native.raster_format_and_sample_count_supported=true;
    native.raster_fences_retired=true;
    v=QualifyBoundRecipe(saved,native);
    assert(v.reason==R::MissingRasterAaFormatOrBudget);
    native.raster_gpu_budget_measured=true;
    v=QualifyBoundRecipe(saved,native);
    assert(v.reason==R::HostCandidateOnly&&v.aa_passes==1u&&!v.runtime_enabled);
    saved.version=1u; // no silent v1 -> v2 compatibility.
    v=QualifyBoundRecipe(saved,native);
    assert(v.reason==R::MissingInput);
    std::cout<<"R09_AA_NEURAL_SPATIAL_FG_HOST_MATRIX_PASS permutations="
             <<matrix<<" source_msaa=GUEST_OR_FORCED_REQUIRES_REAL_RESOLVE"
             <<" postAA=FXAA_SMAA_ULTRA_FXAA_PLUS"
             <<" TAA=DISABLED PS5_RUNTIME=OFF\n";
}
