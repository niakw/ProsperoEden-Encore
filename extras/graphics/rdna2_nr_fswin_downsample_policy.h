// SPDX-License-Identifier: MIT
// RDNA2 scalar FSwin _ds epilogue contract: shifted 2x2 feature pooling,
// 2C x C learned matrix, half-size E4M3FN raster output.
#pragma once
#include <cstdint>
#include <limits>
namespace Eden::Graphics::NeuralRDNA2 {
struct FSwinDownsample {
    std::uint32_t width,height,windows_x,windows_y,channels;
    std::int32_t shift_x,shift_y;
    std::uint32_t input_base_bytes,weight_base_bytes,output_base_bytes;
};
struct FSwinDownsampleStorage{
    std::uint64_t input_bytes,weight_bytes,output_bytes;
};
[[nodiscard]] constexpr bool CanFSwinDownsample(
    const FSwinDownsample& p,const FSwinDownsampleStorage& s) noexcept {
    if(p.width<2u||p.height<2u||
       p.width>16384u||p.height>16384u||
       (p.channels!=32u&&p.channels!=64u&&
        p.channels!=128u&&p.channels!=256u)||
       p.shift_x<-1||p.shift_x>1||
       p.shift_y<-1||p.shift_y>1||
       (p.input_base_bytes|p.weight_base_bytes|p.output_base_bytes)&3u)
        return false;
    const auto wx=(std::uint64_t(p.width)+7u)/8u;
    const auto wy=(std::uint64_t(p.height)+7u)/8u;
    const auto W=wx*wy;
    if(W==0u||W>65535u||p.windows_x!=wx||p.windows_y!=wy)
        return false;
    const std::uint64_t C=p.channels;
    const auto input=W*64u*C;
    const auto weights=2u*C*C;
    const auto output=(std::uint64_t(p.width)/2u)*
        (std::uint64_t(p.height)/2u)*(2u*C);
    constexpr auto limit=256ull<<20;
    constexpr auto max=std::numeric_limits<std::uint32_t>::max();
    if(input>limit||weights>limit||output>limit)return false;
    const auto ie=std::uint64_t(p.input_base_bytes)+input;
    const auto we=std::uint64_t(p.weight_base_bytes)+weights;
    const auto oe=std::uint64_t(p.output_base_bytes)+output;
    return ie<=max&&we<=max&&oe<=max&&
           ie<=s.input_bytes&&we<=s.weight_bytes&&oe<=s.output_bytes;
}
[[nodiscard]] constexpr std::uint32_t FSwinDownsampleGridX(
    const FSwinDownsample& p) noexcept {return p.channels/8u;}
} // namespace Eden::Graphics::NeuralRDNA2
