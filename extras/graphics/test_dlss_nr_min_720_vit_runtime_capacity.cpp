// SPDX-License-Identifier: GPL-3.0-or-later
// 720p Original/Compact: validate real 960-token ViT batch policies and
// tiled boundary repack with no dropped tails, no private model weights.
// No dispatches, no Vulkan objects, no PS5 runtime switch.
#include "dlss_nr_min_720_route_trial.h"
#include "rdna2_nr_vit_qkv_batches_policy.h"
#include "rdna2_nr_vit_projection_stage_policy.h"
#include "rdna2_nr_vit_boundary_repack_policy.h"
#include "r09_native_plans.h"
#include <array>
#include <cassert>
#include <cstdint>
#include <iostream>
using namespace Eden::Graphics::DlssNrMin;
namespace NR=Eden::Graphics::NeuralRDNA2;

static void TestVariant(std::string_view native,bool original) {
    Route720Trial candidate{};
    assert(BuildR09Min720Routes(native,candidate));
    assert(candidate.vit.tokens==960u);
    assert(candidate.vit.raster_width==22u&&candidate.vit.raster_height==40u);
    constexpr auto tokens=960u;
    constexpr std::uint64_t plane=std::uint64_t(tokens)*1024u;
    const NR::VitBoundaryRepack into{22u,40u,1024u,tokens,0u,0u,0u};
    const NR::VitBoundaryRepack out{22u,40u,1024u,tokens,1u,0u,0u};
    const NR::VitBoundaryStorage exact{plane,plane};
    assert(NR::VitTiledTokenCount(into)==tokens);
    assert(NR::VitBoundaryGrid(into)==tokens);
    assert(NR::VitBoundaryGrid(out)==tokens);
    assert(NR::CanVitBoundaryRepack(into,exact));
    assert(NR::CanVitBoundaryRepack(out,exact));
    assert(!NR::CanVitBoundaryRepack(into,{plane-4u,plane}));
    assert(!NR::CanVitBoundaryRepack(out,{plane,plane-4u}));
    for(const auto scratch : {4u,5u,6u,12u}){
        const std::uint64_t scratch_bytes=std::uint64_t(scratch)*plane;
        const NR::VitQkvBuffersCapacity qkv_capacity{
            plane,3072u*1024u,scratch_bytes,128u,
            plane,plane,plane,plane};
        NR::VitQkvBatches qkv{};
        assert(NR::BuildVitQkvBatches(tokens,qkv_capacity,qkv));
        assert(NR::ValidVitQkvBatches(qkv));
        assert(qkv.total_tokens==tokens);
        std::uint32_t counted{};
        for(std::uint32_t i=0u;i<qkv.count;++i){
            const auto& b=qkv.slices[i];
            assert(b.gemm.tokens>0u);
            assert(b.normalize.tokens==b.gemm.tokens);
            counted+=b.gemm.tokens;
        }
        assert(counted==tokens);
        for(auto too_small:{0u,1u,2u}){
            auto bad=qkv_capacity;
            if(too_small==0u)bad.query=plane-4u;
            if(too_small==1u)bad.key=plane-4u;
            if(too_small==2u)bad.value=plane-4u;
            NR::VitQkvBatches output{};
            assert(!NR::BuildVitQkvBatches(tokens,bad,output));
            assert(output.count==0u);
        }
        std::uint32_t stage_count{};
        for(const auto kind : {NR::VitProjectionKind::Expand,
                                NR::VitProjectionKind::Contract,
                                NR::VitProjectionKind::ResidualProjection}){
            const NR::VitProjectionStageCapacity cap{
                kind==NR::VitProjectionKind::Contract?4u*plane:plane,
                kind==NR::VitProjectionKind::Expand?4096u*1024u:
                kind==NR::VitProjectionKind::Contract?1024u*4096u:
                1024u*1024u,
                scratch_bytes,
                kind==NR::VitProjectionKind::Expand?0u:plane,
                kind==NR::VitProjectionKind::Expand?0u:2048u,
                kind==NR::VitProjectionKind::Expand?4u*plane:plane
            };
            NR::VitProjectionStageBatches batches{};
            assert(NR::BuildVitProjectionStage(kind,tokens,cap,batches));
            assert(NR::ValidateVitProjectionStage(batches));
            assert(batches.tokens==tokens);
            std::uint32_t coverage{};
            for(std::uint32_t i=0u;i<batches.count;++i)
                coverage+=batches.slices[i].gemm.tokens;
            assert(coverage==tokens);
            stage_count+=batches.count;
        }
        assert(stage_count>0u);
        std::cout<<"R09_MIN_720P_VIT_NATIVE_BATCH_PASS "
                 <<(original?"Original":"Compact")
                 <<" scratch="<<scratch
                 <<" qkv_batches="<<qkv.count
                 <<" projections="<<stage_count
                 <<" tokens="<<tokens<<" GPU_DISABLED\n";
    }
    // Exhaustive *720p-specific* scratch Pareto frontier. The 1080p
    // frontier does NOT apply to this smaller learned token shape.
    struct BatchWork {std::uint32_t expand{},contract{},projection{},qkv{};};
    std::array<BatchWork,17u> measured{};
    std::array<std::uint32_t,4u> frontier{};
    std::uint32_t count{};
    for(std::uint32_t scratch=4u;scratch<=16u;++scratch){
        const std::uint64_t bytes=std::uint64_t(scratch)*plane;
        const NR::VitQkvBuffersCapacity cap{
            plane,3072u*1024u,bytes,128u,plane,plane,plane,plane};
        NR::VitQkvBatches qkv{};
        assert(NR::BuildVitQkvBatches(tokens,cap,qkv));
        assert(NR::ValidVitQkvBatches(qkv));
        auto& work=measured[scratch];
        work.qkv=qkv.count;
        for(const auto kind:{NR::VitProjectionKind::Expand,
                            NR::VitProjectionKind::Contract,
                            NR::VitProjectionKind::ResidualProjection}){
            const NR::VitProjectionStageCapacity stage{
                kind==NR::VitProjectionKind::Contract?4u*plane:plane,
                kind==NR::VitProjectionKind::Expand?4096u*1024u:
                kind==NR::VitProjectionKind::Contract?4096u*1024u:
                1024u*1024u,
                bytes,kind==NR::VitProjectionKind::Expand?0u:plane,
                kind==NR::VitProjectionKind::Expand?0u:2048u,
                kind==NR::VitProjectionKind::Expand?4u*plane:plane
            };
            NR::VitProjectionStageBatches stages{};
            assert(NR::BuildVitProjectionStage(kind,tokens,stage,stages));
            assert(NR::ValidateVitProjectionStage(stages));
            if(kind==NR::VitProjectionKind::Expand)
                work.expand=stages.count;
            if(kind==NR::VitProjectionKind::Contract)
                work.contract=stages.count;
            if(kind==NR::VitProjectionKind::ResidualProjection)
                work.projection=stages.count;
        }
        const auto no_more=[](const BatchWork& a,const BatchWork& b){
            return a.expand<=b.expand&&a.contract<=b.contract&&
                   a.projection<=b.projection&&a.qkv<=b.qkv;
        };
        bool dominated=false;
        for(std::uint32_t cheaper=4u;cheaper<scratch;++cheaper)
            dominated|=no_more(measured[cheaper],work);
        if(!dominated){
            assert(count<frontier.size());
            frontier[count++]=scratch;
            std::cout<<"R09_MIN_720P_PARETO scratch="<<scratch
                     <<" memory_planes="<<(11u+scratch)
                     <<" expand="<<work.expand
                     <<" qkv="<<work.qkv<<"\n";
        }
    }
    constexpr std::array<std::uint32_t,4u> expected{4u,6u,8u,12u};
    assert(frontier==expected);
    assert(count==expected.size());
    assert(measured[4u].expand==4u&&measured[4u].qkv==3u);
    assert(measured[6u].expand==3u&&measured[6u].qkv==2u);
    assert(measured[8u].expand==2u&&measured[8u].qkv==2u);
    assert(measured[12u].expand==2u&&measured[12u].qkv==1u);
    std::cout<<"R09_MIN_720P_PARETO_ALL_FOUR_VERIFIED\n";
    assert(!candidate.ready_to_enable_720p);
}
int main(){
    TestVariant(Eden::NeuralPlans::Original,true);
    TestVariant(Eden::NeuralPlans::Compact,false);
}
