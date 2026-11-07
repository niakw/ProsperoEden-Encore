// SPDX-License-Identifier: MIT
// Native ViT C1024 E4M3FN tile-major -> raster-major input for RDNA2 GEMM.
// The ViT output's 4x4 token order is not compatible with row-major GEMM.
#pragma once
#include <cstdint>
namespace Eden::Graphics::NeuralRDNA2 {
struct DecoderTileToLinear {
    std::uint32_t width{},height{};
};
struct DecoderTileToLinearStorage {
    std::uint64_t tiled_bytes{},linear_bytes{};
};
[[nodiscard]] constexpr std::uint64_t DecoderTileCount(
    const DecoderTileToLinear& p) noexcept {
    return ((std::uint64_t(p.width)+3u)/4u)*
           ((std::uint64_t(p.height)+3u)/4u)*16u;
}
[[nodiscard]] constexpr bool CanDecoderTileToLinear(
    const DecoderTileToLinear& p,
    const DecoderTileToLinearStorage& buffers) noexcept {
    if(!p.width||!p.height||p.width>4096u||p.height>4096u)
        return false;
    const auto pixels=std::uint64_t(p.width)*p.height;
    const auto padded=DecoderTileCount(p);
    constexpr std::uint64_t kBytes=256ull<<20;
    constexpr std::uint64_t kChannelBytes=1024u;
    const auto src=padded*kChannelBytes;
    const auto dst=pixels*kChannelBytes;
    return pixels<=4096u&&src<=kBytes&&dst<=kBytes&&
           src<=buffers.tiled_bytes&&dst<=buffers.linear_bytes&&
           (pixels*256u+127u)/128u<=65535u;
}
} // namespace Eden::Graphics::NeuralRDNA2
