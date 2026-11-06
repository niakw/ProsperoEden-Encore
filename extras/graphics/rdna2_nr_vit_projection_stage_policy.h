// SPDX-License-Identifier: MIT
// Complete preflight of each 1x1 ViT FFN projection and its FP16 residual
// or cubic activation, in sequential GPU token batches. No dropped tails.
#pragma once
#include "rdna2_nr_projection_policy.h"
#include "rdna2_nr_vit_epilogue_policy.h"
#include <algorithm>
#include <array>
#include <cstdint>
#include <limits>
namespace Eden::Graphics::NeuralRDNA2 {
enum class VitProjectionKind:std::uint8_t {
    Expand,Contract,ResidualProjection
};
struct VitProjectionStageCapacity {
    std::uint64_t input_bytes{},weights_bytes{},scratch_bytes{};
    std::uint64_t residual_bytes{},gain_bytes{},output_bytes{};
};
struct VitProjectionStageBatch {
    Projection gemm{};
    Storage gemm_storage{};
    VitActivation activation{};
    VitResidual residual{};
    VitEpilogueStorage epilogue_storage{};
};
struct VitProjectionStageBatches {
    std::array<VitProjectionStageBatch,16> slices{};
    std::uint32_t count{},tokens{};
    VitProjectionKind kind{};
};
[[nodiscard]] constexpr bool VitStageShape(
    VitProjectionKind kind,std::uint32_t& N,
    std::uint32_t& K) noexcept {
    switch(kind) {
    case VitProjectionKind::Expand:N=4096u;K=1024u;return true;
    case VitProjectionKind::Contract:N=1024u;K=4096u;return true;
    case VitProjectionKind::ResidualProjection:N=1024u;K=1024u;return true;
    }
    return false;
}
[[nodiscard]] constexpr bool BuildVitProjectionStage(
    VitProjectionKind kind,std::uint32_t tokens,
    const VitProjectionStageCapacity& b,
    VitProjectionStageBatches& output) noexcept {
    output={};
    std::uint32_t N=0u,K=0u;
    if(!VitStageShape(kind,N,K)||!tokens||tokens>4096u||
       !b.scratch_bytes)return false;
    const std::uint64_t max_by_products=kMaxProducts/
        (std::uint64_t(N)*K);
    const std::uint64_t max_by_scratch=b.scratch_bytes/
        (std::uint64_t(N)*4u);
    const std::uint64_t stride=std::min({
        std::uint64_t(tokens),std::uint64_t(1024u),
        max_by_products,max_by_scratch});
    if(!stride||std::uint64_t(tokens)>stride*16u)return false;
    VitProjectionStageBatches ready{};
    ready.tokens=tokens;
    ready.kind=kind;
    for(std::uint32_t done=0u;done<tokens;){
        if(ready.count>=ready.slices.size())return false;
        const auto take=static_cast<std::uint32_t>(
            std::min<std::uint64_t>(stride,tokens-done));
        const std::uint64_t a_base=std::uint64_t(done)*K;
        const std::uint64_t out_base=std::uint64_t(done)*N;
        if(a_base>std::numeric_limits<std::uint32_t>::max()||
           out_base>std::numeric_limits<std::uint32_t>::max())
            return false;
        VitProjectionStageBatch step{
            .gemm={take,N,K,K,K,
                   static_cast<std::uint32_t>(a_base),0u},
            .gemm_storage={b.input_bytes,b.weights_bytes,
                           b.scratch_bytes,b.scratch_bytes},
            .activation={take,N,0u,static_cast<std::uint32_t>(out_base)},
            .residual={take,N,0u,
                       static_cast<std::uint32_t>(out_base),
                       static_cast<std::uint32_t>(out_base),0u},
            .epilogue_storage={b.scratch_bytes,b.residual_bytes,
                               b.gain_bytes,b.output_bytes}};
        if(!CanDispatch(step.gemm,step.gemm_storage)||
           (kind==VitProjectionKind::Expand?
            !CanVitActivation(step.activation,step.epilogue_storage):
            !CanVitResidual(step.residual,step.epilogue_storage)))
            return false;
        ready.slices[ready.count++]=step;
        done+=take;
    }
    output=ready;
    return true;
}
[[nodiscard]] constexpr bool ValidateVitProjectionStage(
    const VitProjectionStageBatches& p) noexcept {
    std::uint32_t N=0u,K=0u;
    if(!VitStageShape(p.kind,N,K)||!p.tokens||
       p.tokens>4096u||p.count==0u||p.count>p.slices.size())
        return false;
    std::uint64_t done=0u;
    for(std::uint32_t i=0u;i<p.count;++i) {
        const auto& step=p.slices[i];
        const auto expected_a=done*K,expected_out=done*N;
        if(step.gemm.channels!=N||step.gemm.inner!=K||
           step.gemm.lda_bytes!=K||step.gemm.ldw_bytes!=K||
           step.gemm.a_base_bytes!=expected_a||
           step.gemm.w_base_bytes!=0u||
           !CanDispatch(step.gemm,step.gemm_storage)||
           step.gemm.tokens==0u||step.gemm.tokens>1024u)
            return false;
        if(p.kind==VitProjectionKind::Expand) {
            if(step.activation.tokens!=step.gemm.tokens||
               step.activation.channels!=N||
               step.activation.input_offset_floats!=0u||
               step.activation.output_offset_bytes!=expected_out||
               !CanVitActivation(step.activation,step.epilogue_storage))
                return false;
        } else {
            if(step.residual.tokens!=step.gemm.tokens||
               step.residual.channels!=N||
               step.residual.input_offset_floats!=0u||
               step.residual.output_offset_bytes!=expected_out||
               step.residual.residual_offset_bytes!=expected_out||
               step.residual.gain_offset_halfwords!=0u||
               !CanVitResidual(step.residual,step.epilogue_storage))
                return false;
        }
        done+=step.gemm.tokens;
    }
    return done==p.tokens;
}
} // namespace Eden::Graphics::NeuralRDNA2
