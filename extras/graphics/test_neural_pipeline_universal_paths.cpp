// SPDX-License-Identifier: GPL-3.0-or-later
// Research-only universal OPTIONAL path coverage, no Vulkan/PS5/GPU proof.
// Not just NR+AA+FG: every ordered role sequence up to six stages is
// exhausted, including none, duplicates, AA-only, spatial-only, FG-only,
// NR-free, repeated AA/spatial and asymmetric before/after orderings.
#include "neural_pipeline_path_selection.h"
#include <array>
#include <cassert>
#include <cstdint>
#include <initializer_list>
#include <iostream>
using namespace Eden::Graphics::PipelineComposer;
using K=Kind;
using R=Reason;
using E=Extent;
constexpr E p720{1280u,720u},p1440{2560u,1440u},p4k{3840u,2160u};

static Chain Start(E source=p720) {
    Chain c{};
    c.source_extent=source;
    c.source_image=11u;
    c.source_view=12u;
    c.count=0u;
    return c;
}
static void Add(Chain& c,K kind,int method,E target) {
    assert(c.count+1u<kMaxSteps);
    const unsigned n=static_cast<unsigned>(c.count+1u);
    Step s{};
    s.kind=kind;s.method=method;s.output=target;
    s.image=1100u+10u*n;s.view=s.image+1u;
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
    c.steps[c.count++]=s;
}
static Chain Finish(Chain c,E expected) {
    assert(c.count<kMaxSteps);
    c.steps[c.count].kind=K::Present;
    c.steps[c.count].output=expected;
    ++c.count;
    return c;
}
static void ExpectCandidate(const Chain& c) {
    const auto v=Plan(c);
    assert(v.reason==R::HostCandidateOnly);
    assert(v.shape_qualified&&!v.runtime_enabled);
}
static void ExhaustiveOrders() {
    constexpr std::array<K,5> roles{
        K::Neural,K::Spatial,K::AntiAlias,K::ComposeRealFrame,
        K::FrameGeneration
    };
    std::array<std::uint64_t,16> accepted_by_optional_mask{};
    std::uint64_t all=0u,accepted=0u,rejected=0u;
    std::uint32_t possibilities=1u;
    for(unsigned length=0;length<=6u;++length) {
        for(std::uint32_t code=0;code<possibilities;++code) {
            auto c=Start();
            std::uint32_t encoded=code;
            bool seen_neural=false,seen_fg=false,has_composition=false;
            bool oracle_ok=true;
            unsigned requested_mask=0u;
            for(unsigned index=0;index<length;++index) {
                const K kind=roles[encoded%roles.size()];
                encoded/=static_cast<unsigned>(roles.size());
                switch(kind) {
                case K::Neural:
                    requested_mask|=1u;
                    if(seen_neural||seen_fg)oracle_ok=false;
                    seen_neural=true;
                    Add(c,kind,4,p720); // Original 720p constant geometry
                    break;
                case K::Spatial:
                    requested_mask|=2u;
                    Add(c,kind,0,p720); // bilinear, no resize
                    break;
                case K::AntiAlias:
                    requested_mask|=4u;
                    Add(c,kind,2,p720); // SMAA
                    break;
                case K::ComposeRealFrame:
                    has_composition=true;
                    Add(c,kind,0,p720);
                    break;
                case K::FrameGeneration:
                    requested_mask|=8u;
                    if(seen_fg||!has_composition)oracle_ok=false;
                    seen_fg=true;
                    Add(c,kind,1,p720);
                    break;
                case K::Present:
                    assert(false);
                }
            }
            c=Finish(c,p720);
            const auto v=Plan(c);
            const bool allowed=v.reason==R::HostCandidateOnly &&
                               v.shape_qualified&&!v.runtime_enabled;
            // Independent structural oracle, not self-checking Plan().
            assert(allowed==oracle_ok);
            if(allowed) {
                ++accepted;
                ++accepted_by_optional_mask[requested_mask];
            } else ++rejected;
            ++all;
        }
        possibilities*=5u;
    }
    assert(all==19531u);
    assert(accepted>0u&&rejected>0u);
    for(auto count:accepted_by_optional_mask)assert(count>0u);
    std::cout<<"R09_UNIVERSAL_ALL_ORDERED_ROLE_WORDS_PASS length0to6="
             <<all<<" accepted="<<accepted<<" rejected="<<rejected
             <<" optional_NR_Spatial_AA_FG_masks=16of16"
             <<" PS5_RUNTIME_OFF\n";
}
static void FullMethodMatrix() {
    std::uint64_t total=0u,without_neural=0u,without_fg=0u;
    std::uint64_t no_extra=0u,has_two_spatial=0u,post_fg_aa=0u;
    // Method IDs map to the existing settings catalog; zero means
    // OMIT a stage (not insert a fake 0-effect Vulkan pass).
    for(int nr=0;nr<=4;++nr)
      for(int aa=0;aa<=3;++aa)
        for(int first=0;first<=7;++first)
          for(int second=0;second<=7;++second)
            for(int fg=0;fg<=3;++fg)
              for(int aa_position=0;aa_position<=3;++aa_position) {
                auto c=Start();
                E extent=p720;
                const auto maybe_aa=[&](int position) {
                    if(aa!=0&&aa_position==position)
                        Add(c,K::AntiAlias,aa,extent);
                };
                maybe_aa(0);
                // Pre-NR spatial: keep 720p for admissible Original/A4K.
                if(first)Add(c,K::Spatial,first-1,extent);
                if(nr) {
                    extent=nr<=3?p1440:p720;
                    Add(c,K::Neural,nr,extent);
                }
                maybe_aa(1);
                if(second) {
                    extent=p4k;
                    Add(c,K::Spatial,second-1,extent);
                }
                maybe_aa(2);
                if(fg) {
                    Add(c,K::ComposeRealFrame,0,extent);
                    Add(c,K::FrameGeneration,fg,extent);
                }
                maybe_aa(3);
                c=Finish(c,extent);
                ExpectCandidate(c);
                ++total;
                if(nr==0)++without_neural;
                if(fg==0)++without_fg;
                if(nr==0&&fg==0&&aa==0&&first==0&&second==0)
                    ++no_extra;
                if(first&&second)++has_two_spatial;
                if(fg&&aa&&aa_position==3)++post_fg_aa;
              }
    assert(total==20480u&&without_neural==4096u);
    assert(without_fg==5120u&&no_extra==4u);
    assert(has_two_spatial>0u&&post_fg_aa>0u);
    // Three different output resolutions without Neural. GPU presenter
    // output selection remains external and must be validated independently.
    for(E source:{p720,p1440,p4k}) {
        auto plain=Finish(Start(source),source);
        ExpectCandidate(plain);
        auto only_aa=Start(source);
        Add(only_aa,K::AntiAlias,1,source);
        ExpectCandidate(Finish(only_aa,source));
        auto only_spatial=Start(source);
        Add(only_spatial,K::Spatial,3,source);
        ExpectCandidate(Finish(only_spatial,source));
    }
    std::cout<<"R09_UNIVERSAL_OPTIONAL_METHOD_MATRIX_PASS candidates="
             <<total<<" without_neural="<<without_neural
             <<" without_fg="<<without_fg<<" none="<<no_extra
             <<" two_spatial="<<has_two_spatial
             <<" post_fg_aa="<<post_fg_aa
             <<" source720_1440_4k=YES PS5_RUNTIME_OFF\n";
}
static void BoundaryAndRasterWithoutNeural() {
    // The authored graph has room for eleven processing steps plus Present.
    auto maximal=Start();
    for(unsigned i=0;i<kMaxSteps-1u;++i) {
        const K type=i%2u?K::Spatial:K::AntiAlias;
        Add(maximal,type,type==K::Spatial?0:1,p720);
    }
    assert(maximal.count==kMaxSteps-1u);
    maximal=Finish(maximal,p720);
    assert(maximal.count==kMaxSteps);
    ExpectCandidate(maximal);
    auto overflow=maximal;
    overflow.count=kMaxSteps+1u;
    assert(Plan(overflow).reason==R::EmptyOrTooMany);

    // An otherwise EMPTY graphics-effects graph must still accept an
    // authentic resolved guest-MSAA source. Neither NR nor AA/FG required.
    for(auto raster : {RasterAa::GuestNative,RasterAa::ForcedX2,
                       RasterAa::ForcedX4,RasterAa::ForcedX8,
                       RasterAa::ForcedX16}) {
        auto no_post=Start();
        no_post.source_raster_aa=raster;
        no_post=Finish(no_post,p720);
        assert(Plan(no_post).reason==
               R::MissingRasterAaResolveOrNativeOwner);
        no_post.source_raster_resolve_and_owner_verified=true;
        no_post.source_raster_guest_attachment_safe=true;
        no_post.source_raster_fences_retired=true;
        assert(Plan(no_post).reason==R::MissingRasterAaFormatOrBudget);
        no_post.source_raster_format_and_sample_count_supported=true;
        if(ForcedRasterAa(raster))
            assert(Plan(no_post).reason==
                   R::MissingRasterAaFormatOrBudget);
        no_post.source_raster_gpu_budget_measured=true;
        ExpectCandidate(no_post);
    }
    std::cout<<"R09_MAX_12_STEPS_AND_NR_FREE_SOURCE_MSAA_PASS "
                "forced_msaa_fails_without_real_budget=YES "
                "no_postprocessing_with_guest_msaa=YES runtime=OFF\n";
}
static Recipe BuildRecipe(bool add_aa) {
    Recipe r{};
    r.source_extent=p720;
    r.count=add_aa?3u:2u;
    r.stages[0]={K::Spatial,1,p4k,false};
    if(add_aa)r.stages[1]={K::AntiAlias,2,p4k,false};
    r.stages[add_aa?2u:1u]={K::Present,0,p4k,false};
    return r;
}
static Bindings NativeBindings(bool with_aa) {
    Bindings b{};
    b.guest_image=11;b.guest_view=12;
    const unsigned n=with_aa?2u:1u;
    for(unsigned i=0;i<n;++i){
        auto& e=b.stages[i];
        e.image=3000u+10u*i;e.view=e.image+1u;
        e.native_gpu_pass_recorded=true;
        e.compatible_queue=true;
        e.producer_to_consumer_visible=true;
        e.owner_retained_through_gpu_fence=true;
    }
    return b;
}
static void StageStrengthParameterMatrix() {
    static_assert(HasExistingStrengthControl(K::Neural,4));
    static_assert(HasExistingStrengthControl(K::Spatial,1));
    static_assert(HasExistingStrengthControl(K::Spatial,5));
    static_assert(HasExistingStrengthControl(K::Spatial,6));
    static_assert(!HasExistingStrengthControl(K::Neural,1));
    static_assert(!HasExistingStrengthControl(K::AntiAlias,2));
    unsigned cases=0u,positive=0u,negative=0u;
    for(int method=1;method<=4;++method)
      for(int strength:{-2,-1,0,25,50,100,101}) {
        auto c=Start();
        const E shape=method<=3?p1440:p720;
        Add(c,K::Neural,method,shape);
        c.steps[0].strength_percent=static_cast<std::int16_t>(strength);
        c=Finish(c,shape);
        const bool valid=strength==-1||
             (method==4&&strength>=0&&strength<=100);
        assert((Plan(c).reason==R::HostCandidateOnly)==valid);
        ++cases;
        valid?++positive:++negative;
      }
    for(int method=0;method<=6;++method)
      for(int strength:{-2,-1,0,25,50,100,101}) {
        auto c=Start();
        Add(c,K::Spatial,method,p720);
        c.steps[0].strength_percent=static_cast<std::int16_t>(strength);
        c=Finish(c,p720);
        const bool adjustable=method==1||method==5||method==6;
        const bool valid=strength==-1||
             (adjustable&&strength>=0&&strength<=100);
        assert((Plan(c).reason==R::HostCandidateOnly)==valid);
        ++cases;
        valid?++positive:++negative;
      }
    for(int aa=1;aa<=3;++aa) {
        auto c=Start();
        Add(c,K::AntiAlias,aa,p720);
        c.steps[0].strength_percent=50;
        c=Finish(c,p720);
        assert(Plan(c).reason==R::InvalidStageStrengthParameter);
        ++cases;++negative;
    }
    assert(cases==80u&&positive>0u&&negative>0u);
    std::cout<<"R09_PER_STAGE_NR_AND_SPATIAL_STRENGTH_MATRIX_PASS cases="
             <<cases<<" accepted="<<positive<<" rejected="<<negative
             <<" FXAA_SMAA_NO_FAKE_INTENSITY=YES runtime=OFF\n";
}
static void MeasuredOptimizationOnly() {
    const Recipe spatial=BuildRecipe(false);
    const Recipe spatial_aa=BuildRecipe(true);
    const Bindings owner0=NativeBindings(false);
    const Bindings owner1=NativeBindings(true);
    static_assert(!kComposablePs5RuntimeQualified);
    assert(SameRecipe(spatial,spatial));
    assert(!SameRecipe(spatial,spatial_aa));
    auto spatial_tuned=spatial;
    spatial_tuned.stages[0].strength_percent=75;
    assert(!SameRecipe(spatial,spatial_tuned));
    const auto tuned=std::array<MeasuredCandidate,2>{
        MeasuredCandidate{&spatial,&owner0,9000000u,40000000u,true,true,true,true},
        MeasuredCandidate{&spatial_tuned,&owner0,8000000u,40000000u,true,true,true,true}
    };
    auto separate=SelectMeasuredPath(
        tuned,{p4k,11000000u,80000000u});
    assert(separate.reason==SelectionReason::ResearchWinnerOnly);
    assert(separate.index==1u&&separate.valid_candidates==2u);
    assert(separate.duplicate_recipes==0u);
    auto candidates=std::array<MeasuredCandidate,4>{
        MeasuredCandidate{&spatial,&owner0,9000000u,40000000u,true,true,true,true},
        MeasuredCandidate{&spatial,&owner0,9000000u,40000000u,true,true,true,true},
        MeasuredCandidate{&spatial_aa,&owner1,7000000u,50000000u,true,true,true,true},
        MeasuredCandidate{&spatial_aa,&owner1,7000000u,50000000u,true,true,true,true}
    };
    const MeasuredBudget budget{p4k,11000000u,80000000u};
    auto result=SelectMeasuredPath(candidates,budget);
    assert(result.reason==SelectionReason::ResearchWinnerOnly);
    assert(result.index==2u&&result.valid_candidates==2u);
    assert(result.duplicate_recipes==2u&&!result.ps5_runtime_enabled);
    candidates[2].physical_ps5_measurement=false;
    candidates[3].physical_ps5_measurement=false;
    result=SelectMeasuredPath(candidates,budget);
    assert(result.index==0u&&result.valid_candidates==1u);
    candidates[0].physical_ps5_measurement=false;
    candidates[1].physical_ps5_measurement=false;
    result=SelectMeasuredPath(candidates,budget);
    assert(result.reason==SelectionReason::NoVerifiedCandidate);
    // A "fast" answer with no image A/B or native owner cannot win.
    candidates[2].physical_ps5_measurement=true;
    candidates[2].output_image_quality_ab_accepted=false;
    result=SelectMeasuredPath(candidates,budget);
    assert(result.reason==SelectionReason::NoVerifiedCandidate);
    candidates[2].output_image_quality_ab_accepted=true;
    result=SelectMeasuredPath(candidates,{p720,11000000u,80000000u});
    assert(result.reason==SelectionReason::NoVerifiedCandidate);
    result=SelectMeasuredPath(candidates,{p4k,11000000u,0u});
    assert(result.reason==SelectionReason::InvalidBudget);
    result=SelectMeasuredPath(candidates,{p4k,11000000u,42000000u});
    assert(result.reason==SelectionReason::NoVerifiedCandidate);
    auto bad_native=owner1;
    bad_native.stages[1].view=bad_native.stages[0].view;
    candidates[2].native=&bad_native;
    result=SelectMeasuredPath(candidates,budget);
    assert(result.reason==SelectionReason::NoVerifiedCandidate);
    std::cout<<"R09_MEASURED_PATH_SELECTOR_HOST_PASS "
                "dedup=2 no_fake_gpu_measurement=YES "
                "quality_owner_resolution_budget_gates=YES runtime=OFF\n";
}
int main(){
    ExhaustiveOrders();
    FullMethodMatrix();
    BoundaryAndRasterWithoutNeural();
    StageStrengthParameterMatrix();
    MeasuredOptimizationOnly();
}
