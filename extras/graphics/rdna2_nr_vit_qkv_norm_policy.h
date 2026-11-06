// SPDX-License-Identifier: MIT
// RDNA2 ViT 32-head Q/K normalization and V quantization after FP32 GEMM.
// Input FP32 row-major [tokens,3072] (Q|K|V, each 1024 channels).
// Output 3 independent packed E4M3FN [tokens,32,32] row-major buffers.
// The source temperatures MUST be finite as verified by model loader.
#pragma once
#include <cstdint>
#include <limits>
namespace Eden::Graphics::NeuralRDNA2 {
struct VitQkvNorm {
    std::uint32_t tokens{};
    std::uint32_t src_base_floats{};
    std::uint32_t scale_base_floats{};
    std::uint32_t q_base_bytes{};
    std::uint32_t k_base_bytes{};
    std::uint32_t v_base_bytes{};
};
struct VitQkvNormStorage {
    std::uint64_t input_bytes{},scale_bytes{},q_bytes{},k_bytes{},v_bytes{};
};
[[nodiscard]] constexpr bool CanVitQkvNorm(
    const VitQkvNorm& p,const VitQkvNormStorage& s) noexcept {
    constexpr std::uint64_t kMax=256ull<<20;
    if(p.tokens==0u||p.tokens>4096u||
       ((p.q_base_bytes|p.k_base_bytes|p.v_base_bytes)&3u)!=0u)
        return false;
    if(s.input_bytes==0u||s.scale_bytes==0u||
       s.q_bytes==0u||s.k_bytes==0u||s.v_bytes==0u)
        return false;
    const std::uint64_t input_floats=
        std::uint64_t(p.src_base_floats)+std::uint64_t(p.tokens)*3072u;
    const std::uint64_t scales=
        std::uint64_t(p.scale_base_floats)+32u;
    const std::uint64_t tensor=std::uint64_t(p.tokens)*1024u;
    const std::uint64_t qe=std::uint64_t(p.q_base_bytes)+tensor;
    const std::uint64_t ke=std::uint64_t(p.k_base_bytes)+tensor;
    const std::uint64_t ve=std::uint64_t(p.v_base_bytes)+tensor;
    constexpr auto u32=std::numeric_limits<std::uint32_t>::max();
    if(input_floats>u32||scales>u32||
       qe>u32||ke>u32||ve>u32)return false;
    return input_floats*4u<=kMax&&scales*4u<=kMax&&
           qe<=kMax&&ke<=kMax&&ve<=kMax&&
           input_floats*4u<=s.input_bytes&&
           scales*4u<=s.scale_bytes&&qe<=s.q_bytes&&
           ke<=s.k_bytes&&ve<=s.v_bytes;
}
} // namespace Eden::Graphics::NeuralRDNA2
