// SPDX-License-Identifier: MIT
// RDNA2 2D feature raster <-> 8x8 FSwin window transform ABI.
#pragma once
#include <cstdint>
namespace Eden::Graphics::NeuralRDNA2 {
struct FSwinRasterLayout {
    std::uint32_t width,height,windows_x,windows_y,channels,direction;
};
struct FSwinRasterLayoutStorage {
    std::uint64_t input_bytes,output_bytes;
};
[[nodiscard]] constexpr bool CanFSwinRasterLayout(
    const FSwinRasterLayout& p,
    const FSwinRasterLayoutStorage& storage) noexcept {
    if(!p.width||!p.height||
       (p.channels!=32u&&p.channels!=64u&&
        p.channels!=128u&&p.channels!=256u)||
       p.direction>1u)return false;
    const auto wx=(std::uint64_t(p.width)+7u)/8u;
    const auto wy=(std::uint64_t(p.height)+7u)/8u;
    if(p.windows_x!=wx||p.windows_y!=wy||
       wx*wy>65535u)return false;
    const auto raster=std::uint64_t(p.width)*p.height*p.channels;
    const auto padded=wx*wy*64u*p.channels;
    constexpr std::uint64_t max=256ull<<20;
    if(raster>max||padded>max)return false;
    if(p.direction==0u)
        return raster<=storage.input_bytes&&
               padded<=storage.output_bytes;
    return padded<=storage.input_bytes&&
           raster<=storage.output_bytes;
}
[[nodiscard]] constexpr std::uint32_t FSwinRasterLayoutGridX(
    const FSwinRasterLayout& p) noexcept {
    return p.channels/4u;
}
} // namespace Eden::Graphics::NeuralRDNA2
