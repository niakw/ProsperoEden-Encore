// SPDX-License-Identifier: MIT
// Portable FSwin _upsample: [H/2,W/2,2C] projection -> nearest 2x
// with [H,W,C] skip/gain -> [H,W,C] feature raster.
#pragma once
#include <cstdint>
#include <limits>
namespace Eden::Graphics::NeuralRDNA2 {
struct FSwinUpsample {
    std::uint32_t width,height,windows_x,windows_y,channels;
    std::uint32_t low_base_bytes,skip_base_bytes,weight_base_bytes;
    std::uint32_t gain_base_floats,out_base_bytes;
};
struct FSwinUpsampleStorage {
    std::uint64_t low_bytes,skip_bytes,weight_bytes,gain_bytes,out_bytes;
};
[[nodiscard]] constexpr bool CanFSwinUpsample(
    const FSwinUpsample& p,const FSwinUpsampleStorage& s) noexcept {
    if(!p.width||!p.height||p.width>16384u||p.height>16384u||
       (p.channels!=32u&&p.channels!=64u&&
        p.channels!=128u&&p.channels!=256u)||
       (p.low_base_bytes|p.skip_base_bytes|
        p.weight_base_bytes|p.out_base_bytes)&3u)return false;
    const auto wx=(std::uint64_t(p.width)+7u)/8u;
    const auto wy=(std::uint64_t(p.height)+7u)/8u;
    if(wx*wy>65535u||p.windows_x!=wx||p.windows_y!=wy)return false;
    const std::uint64_t C=p.channels;
    const auto low=((std::uint64_t(p.width)+1u)/2u)*
        ((std::uint64_t(p.height)+1u)/2u)*(2u*C);
    const auto high=std::uint64_t(p.width)*p.height*C;
    const auto weight=2u*C*C;
    const auto gain=C;
    constexpr std::uint64_t limit=256ull<<20;
    constexpr auto max=std::numeric_limits<std::uint32_t>::max();
    if(low>limit||high>limit||weight>limit)return false;
    const auto le=std::uint64_t(p.low_base_bytes)+low;
    const auto se=std::uint64_t(p.skip_base_bytes)+high;
    const auto we=std::uint64_t(p.weight_base_bytes)+weight;
    const auto ge=std::uint64_t(p.gain_base_floats)+gain;
    const auto oe=std::uint64_t(p.out_base_bytes)+high;
    return le<=max&&se<=max&&we<=max&&ge<=max&&oe<=max&&
           le<=s.low_bytes&&se<=s.skip_bytes&&we<=s.weight_bytes&&
           ge*4u<=s.gain_bytes&&oe<=s.out_bytes;
}
[[nodiscard]] constexpr std::uint32_t FSwinUpsampleGridX(
    const FSwinUpsample& p) noexcept {return p.channels/4u;}
} // namespace Eden::Graphics::NeuralRDNA2
