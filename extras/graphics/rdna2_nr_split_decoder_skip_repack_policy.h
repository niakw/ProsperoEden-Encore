// SPDX-License-Identifier: MIT
// Convert the Split-Swin16H primary ProjPool residual (padded window-major
// FP8[512]) to the real decoder's 4x4-tile / 16x16-channel packed skip.
#pragma once
#include <cstdint>
#include <limits>
namespace Eden::Graphics::NeuralRDNA2 {
struct SplitDecoderSkipRepack {
    std::uint32_t width{},height{},windows_x{},windows_y{},channels{};
};
struct SplitDecoderSkipStorage {
    std::uint64_t source_bytes{},destination_bytes{};
};
[[nodiscard]] constexpr std::uint64_t SplitSkipInputTokens(
    const SplitDecoderSkipRepack& p) noexcept {
    return std::uint64_t(p.windows_x)*p.windows_y*64u;
}
[[nodiscard]] constexpr std::uint64_t SplitSkipOutputTokens(
    const SplitDecoderSkipRepack& p) noexcept {
    return ((std::uint64_t(p.width)+3u)/4u)*
           ((std::uint64_t(p.height)+3u)/4u)*16u;
}
[[nodiscard]] constexpr bool CanSplitDecoderSkipRepack(
    const SplitDecoderSkipRepack& p,
    const SplitDecoderSkipStorage& buffers) noexcept {
    if(!p.width||!p.height||
       p.width>4096u||p.height>4096u||
       p.channels!=512u||
       p.windows_x!=(std::uint64_t(p.width)+7u)/8u||
       p.windows_y!=(std::uint64_t(p.height)+7u)/8u||
       !p.windows_x||!p.windows_y||
       std::uint64_t(p.windows_x)*p.windows_y>1023u)
        return false;
    const auto source=SplitSkipInputTokens(p)*p.channels;
    const auto destination=SplitSkipOutputTokens(p)*p.channels;
    constexpr std::uint64_t kLimit=256ull<<20;
    return source<=kLimit&&destination<=kLimit&&
           source<=buffers.source_bytes&&
           destination<=buffers.destination_bytes&&
           SplitSkipOutputTokens(p)<=65535u;
}
} // namespace Eden::Graphics::NeuralRDNA2
