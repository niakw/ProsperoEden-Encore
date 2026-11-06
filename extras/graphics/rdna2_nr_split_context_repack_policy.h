// SPDX-License-Identifier: MIT
// WindowAttention output [window][head][token][dim32] must be transposed
// to the following GEMM's [window][token][head][dim32] FP8 row-major.
#pragma once
#include <cstdint>
#include <limits>
namespace Eden::Graphics::NeuralRDNA2 {
struct SplitContextRepack {
    std::uint32_t windows{},heads{},input_base_bytes{},output_base_bytes{};
};
struct SplitContextRepackStorage {
    std::uint64_t source_bytes{},target_bytes{};
};
[[nodiscard]] constexpr std::uint32_t SplitContextRepackGridX(
    const SplitContextRepack& p) noexcept {
    return static_cast<std::uint32_t>(
        (std::uint64_t(p.windows)*p.heads*64u*8u+255u)/256u);
}
[[nodiscard]] constexpr bool CanSplitContextRepack(
    const SplitContextRepack& p,
    const SplitContextRepackStorage& s) noexcept {
    if(!p.windows||p.windows>1024u||p.heads!=16u||
       ((p.input_base_bytes|p.output_base_bytes)&3u)!=0u)return false;
    const auto bytes=std::uint64_t(p.windows)*p.heads*64u*32u;
    const auto src=std::uint64_t(p.input_base_bytes)+bytes;
    const auto dst=std::uint64_t(p.output_base_bytes)+bytes;
    constexpr auto max=std::numeric_limits<std::uint32_t>::max();
    return src<=max&&dst<=max&&
           src<=s.source_bytes&&dst<=s.target_bytes&&
           src<=(256ull<<20)&&dst<=(256ull<<20)&&
           SplitContextRepackGridX(p)<=65535u;
}
} // namespace Eden::Graphics::NeuralRDNA2
