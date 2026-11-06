// SPDX-License-Identifier: MIT
// Checked GPU FSwin downsample -> next-resolution input-view edge.
#pragma once
#include "rdna2_nr_fswin_chain_layout_policy.h"
#include <cstdint>
namespace Eden::Graphics::NeuralRDNA2 {
struct FSwinLevelLink {
    std::uint32_t source_width{},source_height{};
    std::uint32_t source_channels{},destination_channels{};
    FSwinWindowLayout source_grid{};
    FSwinWindowLayout destination_grid{};
};
[[nodiscard]] constexpr bool CanFSwinLevelLink(
    const FSwinLevelLink& p,std::uint64_t raster_capacity,
    std::uint64_t destination_input_capacity) noexcept {
    if(!p.source_width||!p.source_height||
       p.source_width>16384u||p.source_height>16384u||
       (p.source_channels!=32u&&p.source_channels!=64u&&
        p.source_channels!=128u)||
       p.destination_channels!=p.source_channels*2u)return false;
    const std::uint64_t W=p.source_width,H=p.source_height;
    const auto sx=(W+7u)/8u,sy=(H+7u)/8u;
    const auto tw=(W+1u)/2u,th=(H+1u)/2u;
    const auto tx=(tw+7u)/8u,ty=(th+7u)/8u;
    if(p.source_grid.windows_x!=sx||p.source_grid.windows_y!=sy||
       p.destination_grid.windows_x!=tx||
       p.destination_grid.windows_y!=ty||
       p.source_grid.shift_x<-1||p.source_grid.shift_x>1||
       p.source_grid.shift_y<-1||p.source_grid.shift_y>1||
       p.destination_grid.shift_x||p.destination_grid.shift_y)
        return false;
    if(sx*sy>65535u||tx*ty>65535u)return false;
    const auto C=std::uint64_t(p.source_channels);
    constexpr auto lim=256ull<<20;
    const auto source_bytes=sx*sy*64u*C;
    const auto raster_bytes=tw*th*2u*C;
    const auto destination_bytes=tx*ty*64u*2u*C;
    return source_bytes<=lim&&raster_bytes<=lim&&
           destination_bytes<=lim&&
           raster_bytes<=raster_capacity&&
           destination_bytes<=destination_input_capacity;
}
} // namespace Eden::Graphics::NeuralRDNA2
