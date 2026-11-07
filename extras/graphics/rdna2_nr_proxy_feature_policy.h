// SPDX-License-Identifier: MIT
// No-history, display-referred RGBA32F proxy -> learned preblock FP16[16].
// MIT 16-lane reference: maanHimself/OpenDLSS-NR (310.8 Original only).
// This is a standalone tensor builder, NOT an HDR/readback/presenter hook.
#pragma once
#include <cstdint>
namespace Eden::Graphics::NeuralRDNA2 {
struct NeuralProxyFeatures {
    std::uint32_t full_width{},full_height{},valid_width{},valid_height{};
    std::uint32_t source_width{},source_height{},seed{};
    float auto_mask{},local_tone{},local_structure{},skin_structure{},style{};
};
struct NeuralProxyStorage {
    std::uint64_t proxy_bytes{},feature_bytes{};
};
[[nodiscard]] constexpr bool CanNeuralProxyFeatures(
    const NeuralProxyFeatures& p,const NeuralProxyStorage& buffers) noexcept {
    if(!p.full_width||!p.full_height||
       p.full_width>8192u||p.full_height>8192u||
       !p.valid_width||!p.valid_height||
       p.valid_width>p.full_width||p.valid_height>p.full_height||
       p.full_width>2u*p.valid_width-1u||
       p.full_height>2u*p.valid_height-1u||
       !p.source_width||!p.source_height||
       p.source_width>8192u||p.source_height>8192u)
        return false;
    // All conditional lanes must be finite and within bounded UI-range.
    // Comparisons reject NaN without depending on C++23 constexpr isfinite.
    if(!(p.auto_mask>=0.0f&&p.auto_mask<=1.0f)||
       !(p.local_tone>=-2.0f&&p.local_tone<=2.0f)||
       !(p.local_structure>=-2.0f&&p.local_structure<=2.0f)||
       !(p.skin_structure>=-2.0f&&p.skin_structure<=2.0f)||
       !(p.style>=0.0f&&p.style<=128.0f))return false;
    const auto source=std::uint64_t(p.source_width)*p.source_height*16u;
    const auto output=std::uint64_t(p.full_width)*p.full_height*32u;
    constexpr auto budget=256ull<<20;
    return source<=budget&&output<=budget&&
           buffers.proxy_bytes>=source&&
           buffers.feature_bytes>=output&&
           (p.full_width+7u)/8u<=65535u&&
           (p.full_height+7u)/8u<=65535u;
}
} // namespace Eden::Graphics::NeuralRDNA2
