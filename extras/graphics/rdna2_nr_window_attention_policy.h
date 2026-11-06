// SPDX-License-Identifier: MIT
// Validated dispatch for unfused RDNA2 attention/context on preprojected
// Q/K/V with 64 tokens x 32 channels per head and shared relative bias.
#pragma once
#include <cstdint>
#include <limits>
namespace Eden::Graphics::NeuralRDNA2 {
struct WindowAttention {
    std::uint32_t q_base_bytes,k_base_bytes,v_base_bytes,out_base_bytes;
    std::uint32_t bias_base_floats,windows,heads;
};
struct AttentionStorage {
    std::uint64_t q_bytes,k_bytes,v_bytes,out_bytes,bias_bytes;
};
[[nodiscard]] constexpr bool CanWindowAttention(
    const WindowAttention& p,const AttentionStorage& s) {
    if(!p.windows || !p.heads || p.windows>65535u ||
       (p.heads!=1u && p.heads!=2u && p.heads!=4u &&
        p.heads!=8u && p.heads!=16u))return false;
    if((p.q_base_bytes|p.k_base_bytes|p.v_base_bytes|p.out_base_bytes)&3u)
        return false;
    // 64 token rows, 32 packed E4M3FN channels, 64x64 float bias per head.
    constexpr std::uint64_t kMaxBytes=256ull<<20;
    const auto tensor=std::uint64_t(p.windows)*p.heads*64u*32u;
    const auto bias_words=std::uint64_t(p.heads)*64u*64u;
    if(tensor>kMaxBytes || bias_words*4u>kMaxBytes)return false;
    const auto qe=std::uint64_t(p.q_base_bytes)+tensor;
    const auto ke=std::uint64_t(p.k_base_bytes)+tensor;
    const auto ve=std::uint64_t(p.v_base_bytes)+tensor;
    const auto oe=std::uint64_t(p.out_base_bytes)+tensor;
    const auto be_words=std::uint64_t(p.bias_base_floats)+bias_words;
    // Shader addresses are 32-bit, and each byte stream is uint32 packed.
    if(qe>std::numeric_limits<std::uint32_t>::max() ||
       ke>std::numeric_limits<std::uint32_t>::max() ||
       ve>std::numeric_limits<std::uint32_t>::max() ||
       oe>std::numeric_limits<std::uint32_t>::max() ||
       be_words>std::numeric_limits<std::uint32_t>::max())return false;
    if(qe>s.q_bytes || ke>s.k_bytes || ve>s.v_bytes ||
       oe>s.out_bytes || be_words*4u>s.bias_bytes)return false;
    // Caller must supply five distinct nonaliasing storage ranges and
    // keep the VkDescriptorSet live until scheduler submission.
    return true;
}
} // namespace Eden::Graphics::NeuralRDNA2
