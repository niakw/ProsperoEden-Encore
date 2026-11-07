// SPDX-License-Identifier: MIT
// R09 portable first-frame feature-head compositor contract and CPU oracle.
#pragma once
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
namespace Eden::Graphics::NeuralRDNA2 {
struct NRNoHistoryComposeShape {
    std::uint32_t width{};
    std::uint32_t height{};
    float intensity{1.0f};
    std::uint32_t reserved{};
};
[[nodiscard]] inline bool CanNRNoHistoryCompose(
    NRNoHistoryComposeShape shape,
    std::array<std::uint64_t,3> capacities) noexcept {
    if(!shape.width||!shape.height||
       shape.width>524280u||shape.height>524280u||
       shape.reserved!=0u||!std::isfinite(shape.intensity)||
       shape.intensity<0.0f||shape.intensity>1.0f)return false;
    const auto pixels=std::uint64_t(shape.width)*shape.height;
    constexpr std::uint64_t max_bytes=256ull*1024u*1024u;
    const std::array<std::uint64_t,3> needed{
        pixels*16u,pixels*32u,pixels*16u};
    for(std::size_t i=0;i<needed.size();++i)
        if(!capacities[i]||capacities[i]<needed[i]||
           capacities[i]>max_bytes)return false;
    return true;
}
// Mirrors the head's first-frame RGB rule. Inputs are already normalized.
// The learned out_project's first THREE of 16 channels are the RGB residual.
[[nodiscard]] inline std::array<float,4> NRNoHistoryComposeReference(
    std::array<float,4> proxy,std::array<float,3> residual,
    float intensity) noexcept {
    std::array<float,4> output{};
    bool valid=true;
    for(float r:residual)valid=valid&&std::isfinite(r);
    for(std::size_t i=0;i<3u;++i){
        const float base=std::isfinite(proxy[i])?
            std::clamp(proxy[i],0.0f,1.0f):0.0f;
        const float neural=valid?
            std::clamp(base+residual[i]*0.25f,0.0f,1.0f):base;
        output[i]=std::clamp(base+(neural-base)*intensity,0.0f,1.0f);
    }
    output[3]=std::isfinite(proxy[3])?
        std::clamp(proxy[3],0.0f,1.0f):1.0f;
    return output;
}
} // namespace Eden::Graphics::NeuralRDNA2
