// SPDX-License-Identifier: MIT
// R09: explicit sampled guest image -> transposed neural proxy contract.
#pragma once
#include <array>
#include <cmath>
#include <cstdint>
namespace Eden::Graphics::NeuralRDNA2 {
struct NRTextureProxyShape{
    std::uint32_t raster_width{},raster_height{};
    float paper_white{1.0f};
    std::uint32_t color_mode{}; // 0: LDR UNORM; 1: linear HDR float
};
[[nodiscard]] inline bool CanNRTextureProxy(
    NRTextureProxyShape s,std::array<std::uint32_t,2> source_extent,
    std::uint64_t output_bytes) noexcept {
    if(!s.raster_width||!s.raster_height||
       s.raster_width>16384u||s.raster_height>16384u||
       s.color_mode>1u||!std::isfinite(s.paper_white)||
       s.paper_white<0.05f||
       source_extent[0]!=s.raster_height||
       source_extent[1]!=s.raster_width)return false;
    const auto required=std::uint64_t(s.raster_width)*s.raster_height*16u;
    return output_bytes>=required&&output_bytes<=(256ull<<20);
}
[[nodiscard]] inline std::uint64_t NRTextureProxyIndex(
    NRTextureProxyShape s,std::uint32_t native_x,
    std::uint32_t native_y) noexcept {
    return std::uint64_t(native_y)*s.raster_width+native_x;
}
} // namespace Eden::Graphics::NeuralRDNA2
