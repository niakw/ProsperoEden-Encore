// SPDX-License-Identifier: MIT
// Prepare the complete GPU FP8 GEMM -> FP32 transient -> E4M3FN edge.
// The caller must bind matching, independent STORAGE buffer descriptors.
#pragma once
#include "rdna2_nr_projection_policy.h"
#include "rdna2_nr_float_quantize_policy.h"
#include <algorithm>
#include <array>
#include <cstdint>
#include <limits>
namespace Eden::Graphics::NeuralRDNA2 {
struct QuantizedProjectionPlan {
    FloatQuantize quant{};
    std::uint64_t fp32_bytes{};
    std::uint64_t fp8_bytes{};
};
[[nodiscard]] constexpr bool PrepareQuantizedProjection(
    const Projection& gemm,const Storage& storage,
    std::uint64_t quantized_output_bytes,
    QuantizedProjectionPlan& result,
    std::uint32_t output_offset_bytes=0u) noexcept {
    result={};
    const auto elements=std::uint64_t(gemm.tokens)*gemm.channels;
    if(!gemm.tokens||!gemm.channels||
       elements>std::numeric_limits<std::uint32_t>::max()||
       (elements&3u)!=0u||!CanDispatch(gemm,storage))return false;
    QuantizedProjectionPlan prepared{
        .quant={static_cast<std::uint32_t>(elements),0u,output_offset_bytes,0u},
        .fp32_bytes=elements*4u,
        .fp8_bytes=elements,
    };
    if(!CanFloatQuantize(
        prepared.quant,{storage.output_bytes,quantized_output_bytes}))
        return false;
    result=prepared;
    return true;
}
// Wide ViT FFN 2560x4096x1024 exceeds the single GEMM product budget.
// Split by TOKENS, not by channels: existing weight/activation ABI, one
// reused FP32 transient, packed FP8 output at disjoint byte offsets.
struct QuantizedProjectionBatch {
    Projection gemm{};
    QuantizedProjectionPlan prepared{};
};
struct QuantizedProjectionBatches {
    std::array<QuantizedProjectionBatch,16> batches{};
    std::uint32_t count{};
    std::uint32_t total_tokens{};
};
[[nodiscard]] constexpr bool BuildQuantizedProjectionBatches(
    const Projection& full,const Storage& shared,
    std::uint64_t quantized_output_bytes,std::uint32_t max_tokens_per_batch,
    QuantizedProjectionBatches& result) noexcept {
    result={};
    if(!full.tokens||!full.channels||!full.inner||
       !max_tokens_per_batch||max_tokens_per_batch>65535u)return false;
    if(std::uint64_t(full.tokens)*full.channels>quantized_output_bytes||
       std::uint64_t(full.tokens)*full.channels>std::numeric_limits<std::uint32_t>::max())
        return false;
    QuantizedProjectionBatches staged{};
    std::uint32_t done=0u;
    while(done<full.tokens){
        if(staged.count>=staged.batches.size())return false;
        const std::uint32_t take=std::min(max_tokens_per_batch,full.tokens-done);
        const auto input_base=std::uint64_t(full.a_base_bytes)+
            std::uint64_t(done)*full.lda_bytes;
        const auto output_base=std::uint64_t(done)*full.channels;
        if(input_base>std::numeric_limits<std::uint32_t>::max()||
           output_base>std::numeric_limits<std::uint32_t>::max())return false;
        Projection part=full;
        part.tokens=take;
        part.a_base_bytes=static_cast<std::uint32_t>(input_base);
        QuantizedProjectionPlan prepared{};
        if(!PrepareQuantizedProjection(part,shared,quantized_output_bytes,
            prepared,static_cast<std::uint32_t>(output_base)))return false;
        staged.batches[staged.count++]={part,prepared};
        done+=take;
    }
    staged.total_tokens=done;
    result=staged;
    return true;
}
} // namespace Eden::Graphics::NeuralRDNA2
