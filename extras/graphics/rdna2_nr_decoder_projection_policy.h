// SPDX-License-Identifier: MIT
// RDNA2 decoder learned 1024->512 GEMM + lossless FP32->FP16 tensor ABI.
// Preserve 4x4 tile token order; use only model-provided weights/skip gain.
#pragma once
#include "rdna2_nr_projection_policy.h"
#include <algorithm>
#include <array>
#include <cstdint>
#include <limits>
namespace Eden::Graphics::NeuralRDNA2 {
[[nodiscard]] constexpr std::uint64_t DecoderTileTokens(
    std::uint32_t width,std::uint32_t height) noexcept {
    return ((std::uint64_t(width)+3u)/4u)*
           ((std::uint64_t(height)+3u)/4u)*16u;
}
struct DecoderFp32ToFp16 {
    // Each batch reads contiguous FP32 tokens but scatters FP16 output
    // into padded 4x4 spatial tiles. No raster/tile alias is permitted.
    std::uint32_t elements{},input_offset_floats{},output_offset_halfwords{};
    std::uint32_t width{},height{};
};
struct DecoderFp32ToFp16Storage {
    std::uint64_t input_bytes{},output_bytes{};
};
[[nodiscard]] constexpr bool CanDecoderFp32ToFp16(
    const DecoderFp32ToFp16& p,
    const DecoderFp32ToFp16Storage& b) noexcept {
    constexpr std::uint64_t kChannels=512u;
    if(!p.elements||(p.elements%kChannels)||
       (p.input_offset_floats&1u)||
       (p.output_offset_halfwords%kChannels)||
       !p.width||!p.height||
       p.width>4096u||p.height>4096u)return false;
    const auto pixels=std::uint64_t(p.width)*p.height;
    const auto first=std::uint64_t(p.output_offset_halfwords)/kChannels;
    const auto count=std::uint64_t(p.elements)/kChannels;
    if(!count||pixels>4096u||first>=pixels||count>pixels-first)
        return false;
    const auto input_end=(std::uint64_t(p.input_offset_floats)+
                          p.elements)*4u;
    const auto output_end=DecoderTileTokens(p.width,p.height)*
                          kChannels*2u;
    constexpr std::uint64_t kLimit=256ull<<20;
    return input_end<=b.input_bytes&&output_end<=b.output_bytes&&
           input_end<=kLimit&&output_end<=kLimit&&
           (std::uint64_t(p.elements)+255u)/256u<=65535u;
}
struct DecoderProjectionCapacity {
    std::uint64_t linear_input{},weights{},fp32_scratch{},fp16_projected{};
};
struct DecoderProjectionBatch {
    Projection projection{};
    Storage storage{};
    DecoderFp32ToFp16 convert{};
    DecoderFp32ToFp16Storage conversion_storage{};
};
struct DecoderProjectionBatches {
    std::array<DecoderProjectionBatch,16> slices{};
    std::uint32_t count{},pixels{},tokens{};
    std::uint32_t width{},height{};
};
[[nodiscard]] constexpr bool BuildDecoderProjectionBatches(
    std::uint32_t width,std::uint32_t height,
    const DecoderProjectionCapacity& buffers,
    DecoderProjectionBatches& output) noexcept {
    output={};
    if(!width||!height||width>4096u||height>4096u)return false;
    constexpr std::uint32_t channels=512u,inner=1024u;
    const auto pixels=std::uint64_t(width)*height;
    const auto tiled_tokens=DecoderTileTokens(width,height);
    if(pixels>4096u||tiled_tokens>4096u||
       buffers.linear_input<pixels*inner||
       buffers.weights<channels*inner||
       buffers.fp16_projected<tiled_tokens*channels*2u)
        return false;
    const auto per_batch=std::min<std::uint64_t>({
        std::uint64_t(1024u),pixels,
        buffers.fp32_scratch/(std::uint64_t(channels)*4u),
        kMaxProducts/(std::uint64_t(channels)*inner)});
    if(per_batch==0u||pixels>per_batch*16u)return false;
    DecoderProjectionBatches plan{};
    plan.width=width;
    plan.height=height;
    plan.pixels=static_cast<std::uint32_t>(pixels);
    plan.tokens=static_cast<std::uint32_t>(tiled_tokens);
    for(std::uint32_t done=0;done<pixels;){
        const std::uint32_t take=static_cast<std::uint32_t>(
            std::min(per_batch,pixels-done));
        DecoderProjectionBatch slice{
            .projection={take,channels,inner,inner,inner,
                         done*inner,0u},
            .storage={buffers.linear_input,buffers.weights,
                      buffers.fp32_scratch,buffers.fp32_scratch},
            .convert={take*channels,0u,done*channels,width,height},
            .conversion_storage={buffers.fp32_scratch,
                                 buffers.fp16_projected}};
        if(!CanDispatch(slice.projection,slice.storage)||
           !CanDecoderFp32ToFp16(slice.convert,slice.conversion_storage))
            return false;
        plan.slices[plan.count++]=slice;
        done+=take;
    }
    output=plan;
    return true;
}
[[nodiscard]] constexpr bool ValidDecoderProjectionBatches(
    const DecoderProjectionBatches& plan) noexcept {
    if(!plan.count||plan.count>16u||
       plan.pixels!=std::uint64_t(plan.width)*plan.height||
       plan.tokens!=DecoderTileTokens(plan.width,plan.height))
        return false;
    std::uint64_t done=0u;
    for(std::uint32_t i=0;i<plan.count;++i){
        const auto& b=plan.slices[i];
        if(!b.projection.tokens||b.projection.tokens>1024u||
           b.projection.channels!=512u||b.projection.inner!=1024u||
           b.projection.lda_bytes!=1024u||
           b.projection.ldw_bytes!=1024u||
           b.projection.a_base_bytes!=done*1024u||
           b.projection.w_base_bytes!=0u||
           b.convert.elements!=b.projection.tokens*512u||
           b.convert.input_offset_floats!=0u||
           b.convert.output_offset_halfwords!=done*512u||
           b.convert.width!=plan.width||b.convert.height!=plan.height||
           !CanDispatch(b.projection,b.storage)||
           !CanDecoderFp32ToFp16(b.convert,b.conversion_storage))
            return false;
        done+=b.projection.tokens;
    }
    return done==plan.pixels;
}
} // namespace Eden::Graphics::NeuralRDNA2
