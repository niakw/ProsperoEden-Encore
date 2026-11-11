// SPDX-License-Identifier: MIT
// Genuine R09 QKV/attention and FFN batch-policy evidence for a 1-plane QKV.
// Does not load proprietary model weights or dispatch a Vulkan GPU.
#include "rdna2_nr_vit_qkv_batches_policy.h"
#include "rdna2_nr_vit_projection_stage_policy.h"
#include <array>
#include <cassert>
#include <cstdint>
#include <initializer_list>
#include <iostream>
#include <utility>
using namespace Eden::Graphics::NeuralRDNA2;

int main() {
    for (const std::uint32_t tokens : {960u,2560u,4096u}) {
        const auto plane=std::uint64_t(tokens)*1024u;
        const VitQkvBuffersCapacity compact{
            plane,3072u*1024u,4u*plane,128u,
            plane,plane,plane,plane};
        const VitQkvBuffersCapacity padded{
            plane,3072u*1024u,4u*plane,128u,
            4u*plane,4u*plane,4u*plane,plane};
        VitQkvBatches lean{},oversized{};
        assert(BuildVitQkvBatches(tokens,compact,lean));
        assert(BuildVitQkvBatches(tokens,padded,oversized));
        assert(ValidVitQkvBatches(lean));
        assert(ValidVitQkvBatches(oversized));
        assert(lean.count==oversized.count);
        assert(lean.count!=0u);
        for(std::uint32_t i=0;i<lean.count;++i) {
            // Lower Q/K/V storage must not increase GEMM/normalize batches.
            const auto& a=lean.slices[i];
            const auto& b=oversized.slices[i];
            assert(a.gemm.tokens==b.gemm.tokens);
            assert(a.normalize.tokens==b.normalize.tokens);
            assert(a.normalize.q_base_bytes==b.normalize.q_base_bytes);
            assert(a.normalize.k_base_bytes==b.normalize.k_base_bytes);
            assert(a.normalize.v_base_bytes==b.normalize.v_base_bytes);
        }
        assert(lean.attention_storage.q_bytes==plane);
        assert(lean.attention_storage.k_bytes==plane);
        assert(lean.attention_storage.v_bytes==plane);
        assert(CanVitAttention(lean.attention,lean.attention_storage));
        {
            // Exact packed E4M3FN [tokens,32,32] footprint, not 4 planes.
            const VitQkvNorm normalized{tokens,0u,0u,0u,0u,0u};
            const VitQkvNormStorage capacity{
                12u*plane,128u,plane,plane,plane};
            assert(CanVitQkvNorm(normalized,capacity));
            auto too_small=capacity;
            too_small.q_bytes=plane-4u;
            assert(!CanVitQkvNorm(normalized,too_small));
            too_small=capacity;
            too_small.k_bytes=plane-4u;
            assert(!CanVitQkvNorm(normalized,too_small));
            too_small=capacity;
            too_small.v_bytes=plane-4u;
            assert(!CanVitQkvNorm(normalized,too_small));
        }
        for(std::uint32_t r=0u;r<3u;++r) {
            auto too_small=compact;
            if(r==0u)too_small.query=plane-4u;
            if(r==1u)too_small.key=plane-4u;
            if(r==2u)too_small.value=plane-4u;
            VitQkvBatches rejected{};
            assert(!BuildVitQkvBatches(tokens,too_small,rejected));
            assert(rejected.count==0u);
        }
        {
            // Quantify the memory-versus-dispatch frontier for scratch:
            // P<4 may lower buffer bytes, but necessarily increases
            // real FFN Expand batch count at these exact token sizes.
            const VitProjectionStageCapacity baseline_exp{
                plane,4096u*1024u,4u*plane,
                0u,0u,4u*plane};
            VitProjectionStageBatches base_exp{};
            assert(BuildVitProjectionStage(
                VitProjectionKind::Expand,tokens,baseline_exp,base_exp));
            assert(ValidateVitProjectionStage(base_exp));
            for(std::uint32_t planes=1u;planes<4u;++planes) {
                auto smaller=baseline_exp;
                smaller.scratch_bytes=planes*plane;
                VitProjectionStageBatches sliced{};
                assert(BuildVitProjectionStage(
                    VitProjectionKind::Expand,tokens,smaller,sliced));
                assert(ValidateVitProjectionStage(sliced));
                assert(sliced.count>base_exp.count);
            }
            // Larger scratch reduces some batches, but increases memory.
            // This is a Pareto tradeoff, not a universally optimal FPS
            // decision; the 4-plane setting preserves baseline dispatches.
            for(std::uint32_t planes : {4u,8u,12u}) {
                auto expanded=baseline_exp;
                expanded.scratch_bytes=planes*plane;
                VitProjectionStageBatches exp_batches{};
                assert(BuildVitProjectionStage(
                    VitProjectionKind::Expand,tokens,expanded,exp_batches));
                auto norm_capacity=compact;
                norm_capacity.fp32=planes*plane;
                VitQkvBatches qkv_batches{};
                assert(BuildVitQkvBatches(tokens,norm_capacity,qkv_batches));
                assert(ValidVitQkvBatches(qkv_batches));
                const auto total_planes=11u+planes;
                assert(total_planes>=15u);
                std::cout<<"R09_MIN_VIT_PARETO tokens="<<tokens
                         <<" scratch_planes="<<planes
                         <<" viT_total_planes="<<total_planes
                         <<" ffwd_expand_batches="<<exp_batches.count
                         <<" qkv_batches="<<qkv_batches.count<<"\n";
            }
        }
        if(tokens==2560u) {
            // Exhaustive integer scratch capacity frontier on the authentic
            // Original 1080p ViT shape. No guessed GPU timings. Intra-block
            // FFN expand, contract, terminal projection and QKV use actual
            // BuildVit* scheduling policies and one-plane packed Q/K/V.
            struct Work {
                std::uint32_t expand{},contract{},projection{},qkv{};
            };
            std::array<Work,17u> schedules{};
            constexpr std::array<std::uint32_t,4u> expected{4u,5u,6u,12u};
            std::array<std::uint32_t,4u> frontier{};
            std::size_t frontier_count{};
            for(std::uint32_t scratch=4u;scratch<=16u;++scratch) {
                auto qkv_capacity=compact;
                qkv_capacity.fp32=std::uint64_t(scratch)*plane;
                VitQkvBatches qkv{};
                assert(BuildVitQkvBatches(tokens,qkv_capacity,qkv));
                assert(ValidVitQkvBatches(qkv));
                auto& work=schedules[scratch];
                work.qkv=qkv.count;
                for(const auto kind : {
                    VitProjectionKind::Expand,
                    VitProjectionKind::Contract,
                    VitProjectionKind::ResidualProjection}) {
                    const auto capacity=VitProjectionStageCapacity{
                        kind==VitProjectionKind::Contract ? 4u*plane : plane,
                        kind==VitProjectionKind::Expand ? 4096u*1024u :
                        kind==VitProjectionKind::Contract ? 4096u*1024u :
                        1024u*1024u,
                        std::uint64_t(scratch)*plane,
                        kind==VitProjectionKind::Expand ? 0u : plane,
                        kind==VitProjectionKind::Expand ? 0u : 2048u,
                        kind==VitProjectionKind::Expand ? 4u*plane : plane
                    };
                    VitProjectionStageBatches batches{};
                    assert(BuildVitProjectionStage(
                        kind,tokens,capacity,batches));
                    assert(ValidateVitProjectionStage(batches));
                    if(kind==VitProjectionKind::Expand)
                        work.expand=batches.count;
                    if(kind==VitProjectionKind::Contract)
                        work.contract=batches.count;
                    if(kind==VitProjectionKind::ResidualProjection)
                        work.projection=batches.count;
                }
                const auto better_or_equal=[](const Work& a,const Work& b){
                    return a.expand<=b.expand &&
                           a.contract<=b.contract &&
                           a.projection<=b.projection && a.qkv<=b.qkv;
                };
                // A less expensive scratch setting dominates this one
                // when it schedules no more dispatch batches in ANY stage.
                bool dominated=false;
                for(std::uint32_t cheaper=4u;cheaper<scratch;++cheaper)
                    if(better_or_equal(schedules[cheaper],work))
                        dominated=true;
                if(!dominated) {
                    assert(frontier_count<frontier.size());
                    frontier[frontier_count++]=scratch;
                    std::cout<<"R09_MIN_VIT_1080P_PARETO scratch="<<scratch
                             <<" total_planes="<<(11u+scratch)
                             <<" requested_MiB="<<(2.5*(11u+scratch))
                             <<" expand="<<work.expand
                             <<" contract="<<work.contract
                             <<" projection="<<work.projection
                             <<" qkv="<<work.qkv<<"\n";
                }
                if(scratch>=7u&&scratch<=11u) {
                    // These options are dominated by 6 planes at 1080p;
                    // previous rough 8-plane recommendation was wasteful.
                    assert(dominated);
                }
                if(scratch>=13u)assert(dominated);
            }
            assert(frontier_count==expected.size());
            assert(frontier==expected);
            assert(schedules[4u].expand==4u && schedules[4u].qkv==4u);
            assert(schedules[5u].expand==4u && schedules[5u].qkv==3u);
            assert(schedules[6u].expand==3u && schedules[6u].qkv==2u);
            assert(schedules[12u].expand==3u && schedules[12u].qkv==1u);
            std::cout<<"R09_MIN_VIT_1080P_EXHAUSTIVE_PARETO_PASS\n";
        }
        {
            // Preserve all three authentic ViT learned projection plans
            // and their original FP32 scratch batch count.
            const VitProjectionStageCapacity expand{
                plane,4096u*1024u,4u*plane,
                0u,0u,4u*plane};
            const VitProjectionStageCapacity contract{
                4u*plane,1024u*4096u,4u*plane,
                plane,2048u,plane};
            const VitProjectionStageCapacity residual{
                plane,1024u*1024u,4u*plane,
                plane,2048u,plane};
            for(const auto& [kind,cap] : {
                std::pair{VitProjectionKind::Expand,expand},
                std::pair{VitProjectionKind::Contract,contract},
                std::pair{VitProjectionKind::ResidualProjection,residual}}) {
                VitProjectionStageBatches batches{};
                assert(BuildVitProjectionStage(kind,tokens,cap,batches));
                assert(ValidateVitProjectionStage(batches));
                assert(batches.count!=0u);
            }
        }
    }
}
