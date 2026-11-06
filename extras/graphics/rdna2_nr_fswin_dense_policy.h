// SPDX-License-Identifier: MIT
#pragma once
#include <cstdint>
#include <limits>
namespace Eden::Graphics::NeuralRDNA2 {
struct FSwinDense {
    std::uint32_t x_base_bytes,w_base_bytes,residual_base_bytes;
    std::uint32_t scale_base_floats,out_base_bytes,windows,channels,stage;
};
struct FSwinDenseStorage {
    std::uint64_t input_bytes,weight_bytes,residual_bytes,scales_bytes,output_bytes;
};
[[nodiscard]] constexpr bool CanFSwinDense(
    const FSwinDense& p,const FSwinDenseStorage& s) noexcept {
    if(!p.windows||p.windows>256u||p.stage>3u||
       (p.stage==1u&&p.channels==32u)||
       (p.channels!=32u&&p.channels!=64u&&
        p.channels!=128u&&p.channels!=256u))return false;
    if((p.x_base_bytes|p.w_base_bytes|
        p.residual_base_bytes|p.out_base_bytes)&3u)return false;
    const std::uint64_t C=p.channels;
    const std::uint64_t tokens=std::uint64_t(p.windows)*64u;
    const std::uint64_t xbytes=tokens*(
        p.stage==1u||(p.stage==2u&&C==32u)?4u*C:C);
    const std::uint64_t wbytes=p.stage==0u?4u*C*C:
        p.stage==1u?C*128u:
        (p.stage==2u&&C==32u)?4u*C*C:C*C;
    const std::uint64_t obytes=tokens*(p.stage==0u?4u*C:C);
    constexpr auto max=std::numeric_limits<std::uint32_t>::max();
    if(xbytes>(256ull<<20)||wbytes>(256ull<<20)||obytes>(256ull<<20))
        return false;
    const auto xe=std::uint64_t(p.x_base_bytes)+xbytes;
    const auto we=std::uint64_t(p.w_base_bytes)+wbytes;
    const auto oe=std::uint64_t(p.out_base_bytes)+obytes;
    if(xe>max||we>max||oe>max)return false;
    if(xe>s.input_bytes||we>s.weight_bytes||oe>s.output_bytes)return false;
    if(p.stage>=2u){
        const auto re=std::uint64_t(p.residual_base_bytes)+tokens*C;
        const auto se=std::uint64_t(p.scale_base_floats)+C;
        if(re>max||se>max||re>s.residual_bytes||
           se*4u>s.scales_bytes)return false;
    }
    return true;
}
[[nodiscard]] constexpr std::uint32_t FSwinDenseGridX(
    const FSwinDense& p) noexcept {
    return p.stage==0u?(p.channels+63u)/64u:1u;
}
} // namespace Eden::Graphics::NeuralRDNA2
