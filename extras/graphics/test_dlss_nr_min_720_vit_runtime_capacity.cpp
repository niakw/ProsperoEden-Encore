// SPDX-License-Identifier: GPL-3.0-or-later
// 720p Original/Compact: validate real 960-token ViT batch policies and
// tiled boundary repack with no dropped tails, no private model weights.
// No dispatches, no Vulkan objects, no PS5 runtime switch.
#include "dlss_nr_min_720_route_trial.h"
#include "rdna2_nr_vit_qkv_batches_policy.h"
#include "rdna2_nr_vit_projection_stage_policy.h"
#include "rdna2_nr_vit_boundary_repack_policy.h"
#include "r09_native_plans.h"
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
    assert(!candidate.ready_to_enable_720p);
}
int main(){
    TestVariant(Eden::NeuralPlans::Original,true);
    TestVariant(Eden::NeuralPlans::Compact,false);
}
