// SPDX-License-Identifier: MIT
// VMA-owned GPU scratch for the ViT QKV/attention subgraph.
// Input activation arrives from the preceding graph on the GPU.
#pragma once
#include "rdna2_nr_vit_qkv_batches_policy.h"
#include <algorithm>
#include <array>
#include <cstdint>
namespace Eden::Graphics::NeuralRDNA2 {
struct VitQkvTensorLayout {
    // FP32 scratch, Q, K, V and attention context.
    std::array<std::uint64_t,5> sizes{};
    std::uint32_t batch_tokens{};
    std::uint64_t total_bytes{};
};
[[nodiscard]] constexpr bool BuildVitQkvTensorLayout(
    std::uint32_t tokens,std::uint64_t max_storage_range,
    VitQkvTensorLayout& result) noexcept {
    result={};
    if(!tokens||tokens>4096u||!max_storage_range)return false;
    constexpr std::uint64_t kMaxPerBuffer=256ull<<20;
    constexpr std::uint64_t kMaxCombined=512ull<<20;
    const std::uint64_t output_bytes=std::uint64_t(tokens)*1024u;
    constexpr std::uint64_t kFp32PerToken=3072u*4u;
    const std::uint64_t slice_tokens=std::min({
        std::uint64_t(tokens),std::uint64_t(2048u),
        max_storage_range/kFp32PerToken,
        kMaxPerBuffer/kFp32PerToken});
    if(!slice_tokens||std::uint64_t(tokens)>slice_tokens*16u||
       output_bytes>max_storage_range||output_bytes>kMaxPerBuffer)
        return false;
    VitQkvTensorLayout staged{};
    staged.sizes={slice_tokens*kFp32PerToken,
                  output_bytes,output_bytes,output_bytes,output_bytes};
    for(auto bytes:staged.sizes){
        if(!bytes||bytes>max_storage_range||bytes>kMaxPerBuffer||
           staged.total_bytes>kMaxCombined-bytes)return false;
        staged.total_bytes+=bytes;
    }
    staged.batch_tokens=static_cast<std::uint32_t>(slice_tokens);
    // The scalar GEMM can have a tighter product budget than the scratch
    // budget: validate the actual downstream plan as a final preflight.
    const VitQkvBuffersCapacity capacity{
        output_bytes,3072ull*1024u,staged.sizes[0],128u,
        output_bytes,output_bytes,output_bytes,output_bytes};
    VitQkvBatches batches{};
    if(!BuildVitQkvBatches(tokens,capacity,batches))return false;
    result=staged;
    return true;
}
} // namespace Eden::Graphics::NeuralRDNA2
