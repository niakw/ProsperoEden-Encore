// SPDX-License-Identifier: MIT
// Exact 2x2 native preblock pooling boundary:
// full-res RAW FP16 C32 -> half-res E4M3FN C32.
// Input may NEVER be the already quantized preblock skip.
#pragma once
#include <cstdint>
namespace Eden::Graphics::NeuralRDNA2 {
struct PreblockPoolShape {std::uint32_t width{},height{};};
struct PreblockPoolStorage {std::uint64_t full_fp16{},half_fp8{};};
[[nodiscard]] constexpr bool CanPreblockPool(
    PreblockPoolShape s,PreblockPoolStorage v) noexcept {
    if(!s.width||!s.height||s.width>8192u||s.height>8192u||
       (s.width&1u)||(s.height&1u))return false;
    const auto pixels=std::uint64_t(s.width)*s.height;
    constexpr auto limit=256ull<<20;
    const auto input=pixels*64u;
    const auto output=(pixels/4u)*32u;
    return input<=limit&&output<=limit&&
           v.full_fp16>=input&&v.full_fp16<=limit&&
           v.half_fp8>=output&&v.half_fp8<=limit;
}
} // namespace Eden::Graphics::NeuralRDNA2
