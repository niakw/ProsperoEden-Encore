// SPDX-License-Identifier: MIT
// Full native-raster temporal compositor resource/shape boundary.
// Motion is current -> previous in UV units with an independent valid flag.
// No synthesized history or guessed neural blend coefficient is permitted.
#pragma once
#include <array>
#include <cmath>
#include <cstdint>
namespace Eden::Graphics::NeuralRDNA2 {
struct NRTemporalComposeShape {
    std::uint32_t width{},height{};
    float intensity{},blend_scale{};
    std::uint32_t history_valid{},reserved0{},reserved1{},reserved2{};
};
[[nodiscard]] inline bool CanNRTemporalCompose(
    NRTemporalComposeShape s,
    std::array<std::uint64_t,6> buffers) noexcept {
    if(!s.width||!s.height||s.width>16384u||s.height>16384u||
       !std::isfinite(s.intensity)||s.intensity<0.0f||s.intensity>1.0f||
       !std::isfinite(s.blend_scale)||s.blend_scale<0.0f||
       s.blend_scale>1.0f||s.history_valid>1u||
       s.reserved0||s.reserved1||s.reserved2)return false;
    const auto n=std::uint64_t(s.width)*s.height;
    const std::array<std::uint64_t,6> required{
        n*16u,n*32u,n*16u,n*16u,n*16u,n*16u};
    for(std::size_t i=0u;i<6u;++i)
        if(buffers[i]<required[i]||buffers[i]>(256ull<<20))
            return false;
    return true;
}
} // namespace Eden::Graphics::NeuralRDNA2
