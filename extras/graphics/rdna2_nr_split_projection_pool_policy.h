// SPDX-License-Identifier: MIT
// Split-Swin ProjPool: pool FP16 residual-projection values BEFORE FP8.
// Source [window8x8][quadrant4x4][slot][512]; destination half-res
// raster in 4x4 tile order, including zeroed padding and optional tail.
#pragma once
#include <cstdint>
#include <limits>
namespace Eden::Graphics::NeuralRDNA2 {
struct SplitProjectionPool {
    std::uint32_t width{},height{},windows_x{},windows_y{};
    std::uint32_t scratch_base_floats{},residual_base_bytes{};
    std::uint32_t gain_base_halfwords{},pool_base_bytes{},output_tokens{};
};
struct SplitProjectionPoolStorage {
    std::uint64_t scratch_bytes{},residual_bytes{},gain_bytes{},pool_bytes{};
};
[[nodiscard]] constexpr std::uint64_t SplitPoolAlign4(
    std::uint64_t n) noexcept {return (n+3u)&~std::uint64_t(3u);}
[[nodiscard]] constexpr std::uint32_t SplitPoolWidth(
    const SplitProjectionPool& p) noexcept {
    return static_cast<std::uint32_t>(SplitPoolAlign4(
        (std::uint64_t(p.width)+1u)/2u));
}
[[nodiscard]] constexpr std::uint32_t SplitPoolHeight(
    const SplitProjectionPool& p) noexcept {
    return static_cast<std::uint32_t>(SplitPoolAlign4(
        (std::uint64_t(p.height)+1u)/2u));
}
[[nodiscard]] constexpr std::uint32_t SplitPoolLiveTokens(
    const SplitProjectionPool& p) noexcept {
    return SplitPoolWidth(p)*SplitPoolHeight(p);
}
[[nodiscard]] constexpr std::uint32_t SplitPoolOutputTokens(
    const SplitProjectionPool& p) noexcept {
    return p.output_tokens?p.output_tokens:SplitPoolLiveTokens(p);
}
[[nodiscard]] constexpr bool CanSplitProjectionPool(
    const SplitProjectionPool& p,
    const SplitProjectionPoolStorage& s) noexcept {
    if(!p.width||!p.height||!p.windows_x||!p.windows_y||
       p.windows_x>1023u||p.windows_y>1023u||
       (std::uint64_t(p.width)+7u)/8u!=p.windows_x||
       (std::uint64_t(p.height)+7u)/8u!=p.windows_y||
       (p.residual_base_bytes|p.pool_base_bytes)&3u)return false;
    const std::uint64_t windows=
        std::uint64_t(p.windows_x)*p.windows_y;
    if(!windows||windows>1023u)return false;
    const std::uint64_t in_bytes=windows*64u*512u;
    const std::uint64_t pool_tokens=
        std::uint64_t(SplitPoolWidth(p))*SplitPoolHeight(p);
    const std::uint64_t out_tokens=SplitPoolOutputTokens(p);
    if(!pool_tokens||pool_tokens>65535u||
       out_tokens<pool_tokens||out_tokens>65535u)return false;
    const std::uint64_t src_end=
        (std::uint64_t(p.scratch_base_floats)+in_bytes)*4u;
    const std::uint64_t resid_end=
        std::uint64_t(p.residual_base_bytes)+in_bytes;
    const std::uint64_t gain_end=
        ((std::uint64_t(p.gain_base_halfwords)+513u)/2u)*4u;
    const std::uint64_t out_end=
        std::uint64_t(p.pool_base_bytes)+out_tokens*512u;
    constexpr std::uint64_t limit=256ull<<20;
    constexpr auto u32=std::numeric_limits<std::uint32_t>::max();
    return src_end<=u32&&resid_end<=u32&&gain_end<=u32&&
           out_end<=u32&&src_end<=limit&&resid_end<=limit&&
           gain_end<=limit&&out_end<=limit&&
           src_end<=s.scratch_bytes&&
           resid_end<=s.residual_bytes&&
           gain_end<=s.gain_bytes&&
           out_end<=s.pool_bytes;
}
} // namespace Eden::Graphics::NeuralRDNA2
