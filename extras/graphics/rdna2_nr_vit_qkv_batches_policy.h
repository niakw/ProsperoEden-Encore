// SPDX-License-Identifier: MIT
// Whole native ViT QKV edge: prevalidate all sequential GEMM/normalize
// slices BEFORE recording the first Vulkan command. No partial tensor reuse.
#pragma once
#include "rdna2_nr_projection_policy.h"
#include "rdna2_nr_vit_qkv_norm_policy.h"
#include "rdna2_nr_vit_attention_policy.h"
#include <algorithm>
#include <array>
#include <cstdint>
namespace Eden::Graphics::NeuralRDNA2 {
struct VitQkvBuffersCapacity {
    std::uint64_t input{},weights{},fp32{},temperatures{};
    std::uint64_t query{},key{},value{},context{};
};
struct VitQkvBatch {
    Projection gemm{};
    Storage gemm_storage{};
    VitQkvNorm normalize{};
    VitQkvNormStorage normalize_storage{};
};
struct VitQkvBatches {
    std::array<VitQkvBatch,16> slices{};
    std::uint32_t count{},total_tokens{};
    VitAttention attention{};
    VitAttentionStorage attention_storage{};
};
[[nodiscard]] constexpr bool BuildVitQkvBatches(
    std::uint32_t tokens,const VitQkvBuffersCapacity& capacity,
    VitQkvBatches& output) noexcept {
    output={};
    if(!tokens||tokens>4096u||!capacity.fp32)return false;
    constexpr std::uint64_t kMatrixWidth=3072u;
    constexpr std::uint64_t kInner=1024u;
    const std::uint64_t temp_tokens=capacity.fp32/(kMatrixWidth*4u);
    const std::uint64_t compute_tokens=
        kMaxProducts/(kMatrixWidth*kInner);
    const std::uint64_t per_batch=std::min({
        std::uint64_t(tokens),temp_tokens,compute_tokens});
    if(!per_batch||std::uint64_t(tokens)>per_batch*16u)return false;
    const VitAttention attn{0u,0u,0u,0u,tokens};
    const VitAttentionStorage attn_storage{
        capacity.query,capacity.key,capacity.value,capacity.context};
    if(!CanVitAttention(attn,attn_storage))return false;
    VitQkvBatches prepared{};
    std::uint32_t done=0u;
    while(done<tokens){
        if(prepared.count>=prepared.slices.size())return false;
        const std::uint32_t take=std::min(
            static_cast<std::uint32_t>(per_batch),tokens-done);
        const auto input_base=std::uint64_t(done)*kInner;
        const auto output_base=std::uint64_t(done)*1024u;
        if(input_base>UINT32_MAX||output_base>UINT32_MAX)return false;
        VitQkvBatch batch{
            .gemm={take,3072u,1024u,1024u,1024u,
                   static_cast<std::uint32_t>(input_base),0u},
            .gemm_storage={capacity.input,capacity.weights,
                           capacity.fp32,capacity.fp32},
            .normalize={take,0u,0u,
                        static_cast<std::uint32_t>(output_base),
                        static_cast<std::uint32_t>(output_base),
                        static_cast<std::uint32_t>(output_base)},
            .normalize_storage={capacity.fp32,capacity.temperatures,
                                capacity.query,capacity.key,capacity.value}};
        if(!CanDispatch(batch.gemm,batch.gemm_storage)||
           !CanVitQkvNorm(batch.normalize,batch.normalize_storage))
            return false;
        prepared.slices[prepared.count++]=batch;
        done+=take;
    }
    prepared.total_tokens=done;
    prepared.attention=attn;
    prepared.attention_storage=attn_storage;
    output=prepared;
    return true;
}
[[nodiscard]] constexpr bool ValidVitQkvBatches(
    const VitQkvBatches& p) noexcept {
    if(!p.count||p.count>p.slices.size()||
       !p.total_tokens||p.total_tokens!=p.attention.tokens||
       !CanVitAttention(p.attention,p.attention_storage))return false;
    std::uint64_t done=0u;
    for(std::uint32_t i=0u;i<p.count;++i){
        const auto& s=p.slices[i];
        if(!CanDispatch(s.gemm,s.gemm_storage)||
           !CanVitQkvNorm(s.normalize,s.normalize_storage)||
           s.gemm.tokens!=s.normalize.tokens||
           s.gemm.channels!=3072u||s.gemm.inner!=1024u||
           s.gemm.a_base_bytes!=done*1024u||
           s.normalize.src_base_floats!=0u||
           s.normalize.scale_base_floats!=0u||
           s.normalize.q_base_bytes!=done*1024u||
           s.normalize.k_base_bytes!=done*1024u||
           s.normalize.v_base_bytes!=done*1024u)return false;
        done+=s.gemm.tokens;
    }
    return done==p.total_tokens;
}
} // namespace Eden::Graphics::NeuralRDNA2
