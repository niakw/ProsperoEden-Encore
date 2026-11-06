// SPDX-License-Identifier: MIT
// Prepare the complete GPU FP8 GEMM -> FP32 transient -> E4M3FN edge.
// The caller must bind matching, independent STORAGE buffer descriptors.
#pragma once
#include "rdna2_nr_projection_policy.h"
#include "rdna2_nr_float_quantize_policy.h"
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
    QuantizedProjectionPlan& result) noexcept {
    result={};
    const auto elements=std::uint64_t(gemm.tokens)*gemm.channels;
    if(!gemm.tokens||!gemm.channels||
       elements>std::numeric_limits<std::uint32_t>::max()||
       (elements&3u)!=0u||!CanDispatch(gemm,storage))return false;
    QuantizedProjectionPlan prepared{
        .quant={static_cast<std::uint32_t>(elements),0u,0u,0u},
        .fp32_bytes=elements*4u,
        .fp8_bytes=elements,
    };
    if(!CanFloatQuantize(
        prepared.quant,{storage.output_bytes,quantized_output_bytes}))
        return false;
    result=prepared;
    return true;
}
} // namespace Eden::Graphics::NeuralRDNA2
