// SPDX-License-Identifier: MIT
#pragma once
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
namespace Eden::Graphics::NeuralRDNA2 {
struct NRHDRProxyShape {
    std::uint32_t width{},height{};
    float paper_white{1.0f};
    std::uint32_t reserved{};
};
[[nodiscard]] inline bool CanNRHDRProxy(
    NRHDRProxyShape s,std::array<std::uint64_t,2> caps) noexcept {
    if(!s.width||!s.height||s.width>524280u||s.height>524280u||
       !std::isfinite(s.paper_white)||s.paper_white<0.05f||
       s.reserved)return false;
    const auto bytes=std::uint64_t(s.width)*s.height*16u;
    constexpr auto max=256ull*1024u*1024u;
    for(const auto cap:caps)if(cap<bytes||cap>max)return false;
    return true;
}
[[nodiscard]] inline float HDRProxyReference(float input,float paper_white) noexcept {
    const float v=(!std::isfinite(input)||input<0.0f)?
        0.0f:input/std::max(paper_white,0.05f);
    const float shoulder=v>0.75f?
        0.75f+0.25f*(1.0f-std::exp(-5.770780f*(v-0.75f))):v;
    const float x=std::clamp(shoulder,0.0f,1.0f);
    return std::clamp(x<=0.0031308f?12.92f*x:
        1.055f*std::pow(x,1.0f/2.4f)-0.055f,0.0f,1.0f);
}
}
