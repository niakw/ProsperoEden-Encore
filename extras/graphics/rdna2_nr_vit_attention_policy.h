// SPDX-License-Identifier: MIT
// RDNA2 scalar 32-head ViT attention on E4M3FN row-major Q/K/V tensors.
// The native 1920x1080 model uses 2560 tokens; its real size must pass.
#pragma once
#include <cstdint>
#include <limits>
namespace Eden::Graphics::NeuralRDNA2 {
struct VitAttention {
    std::uint32_t q_base_bytes,k_base_bytes,v_base_bytes;
    std::uint32_t out_base_bytes,tokens;
};
struct VitAttentionStorage {
    std::uint64_t q_bytes,k_bytes,v_bytes,out_bytes;
};
[[nodiscard]] constexpr bool CanVitAttention(
    const VitAttention& p,const VitAttentionStorage& s){
    if(!p.tokens || p.tokens>4096u)return false;
    if((p.q_base_bytes|p.k_base_bytes|
        p.v_base_bytes|p.out_base_bytes)&3u)return false;
    const auto extent=std::uint64_t(p.tokens)*32u*32u;
    constexpr auto max=std::numeric_limits<std::uint32_t>::max();
    const auto q=std::uint64_t(p.q_base_bytes)+extent;
    const auto k=std::uint64_t(p.k_base_bytes)+extent;
    const auto v=std::uint64_t(p.v_base_bytes)+extent;
    const auto o=std::uint64_t(p.out_base_bytes)+extent;
    if(q>max||k>max||v>max||o>max)return false;
    if(q>s.q_bytes||k>s.k_bytes||v>s.v_bytes||o>s.out_bytes)return false;
    // Caller verifies all four buffers are live, distinct/nonaliasing;
    // Q/K must already be normalized/scaled and all values finite.
    return true;
}
} // namespace Eden::Graphics::NeuralRDNA2
