// SPDX-License-Identifier: MIT
// R09 native raster to Vulkan image: dimensions are transposed by the
// recovered model plan, not guessed from the game or the crop rectangle.
#pragma once
#include <array>
#include <cstdint>
namespace Eden::Graphics::NeuralRDNA2 {
struct NRNoHistoryPresentShape {
    std::uint32_t raster_width{};
    std::uint32_t raster_height{};
    std::uint32_t reserved0{};
    std::uint32_t reserved1{};
};
[[nodiscard]] inline bool CanNRNoHistoryPresent(
    NRNoHistoryPresentShape s,std::uint64_t input_bytes,
    std::array<std::uint32_t,2> output_extent) noexcept{
    if(!s.raster_width||!s.raster_height||
       s.raster_width>16384u||s.raster_height>16384u||
       s.reserved0||s.reserved1||
       output_extent[0]!=s.raster_height||
       output_extent[1]!=s.raster_width)return false;
    const std::uint64_t required=
        std::uint64_t(s.raster_width)*s.raster_height*16u;
    return input_bytes>=required&&input_bytes<=(256ull<<20);
}
[[nodiscard]] inline std::uint64_t NativeRgbaSourceIndex(
    NRNoHistoryPresentShape s,std::uint32_t output_x,
    std::uint32_t output_y) noexcept {
    return std::uint64_t(output_x)*s.raster_width+output_y;
}
} // namespace Eden::Graphics::NeuralRDNA2
