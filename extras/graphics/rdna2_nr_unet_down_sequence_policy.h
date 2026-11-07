// SPDX-License-Identifier: MIT
// R09 native four-depth U-Net descent: C32,C64,C128,C256 -> C512.
// Only validates raster shapes, level ordering and buffer capacities.
// It does not claim the preblock, bottleneck or post-image is integrated.
#pragma once
#include "video_core/renderer_vulkan/nr_rdna2_unet_skip_map.h"
#include "rdna2_nr_fswin_level_link_policy.h"
#include "rdna2_nr_fswin_downsample_policy.h"
#include <array>
#include <cstdint>
namespace Eden::Graphics::NeuralRDNA2 {
[[nodiscard]] inline bool CanNativeUNetDownSequence(
    const NativeUNetSkipMap& map,
    const std::array<FSwinWindowLayout,4>& input_windows,
    const std::array<FSwinWindowLayout,4>& output_windows,
    std::uint64_t first_raster_capacity,
    const std::array<std::uint64_t,4>& down_raster_capacity) noexcept {
    if(map.count!=4u)return false;
    std::array<const NativeUNetSkipEdge*,4> edges{};
    for(const auto& edge:map.edges){
        std::size_t index=4u;
        switch(edge.channels){
        case 32u:index=0u;break;
        case 64u:index=1u;break;
        case 128u:index=2u;break;
        case 256u:index=3u;break;
        default:return false;
        }
        if(edges[index]||edge.down_block>=edge.up_block)return false;
        edges[index]=&edge;
    }
    for(std::size_t i=0u;i<4u;++i){
        if(!edges[i])return false;
        const auto& e=*edges[i];
        const std::uint64_t w=e.skip_height,h=e.skip_width;
        const auto channels=32u<<i;
        if(w<2u||h<2u||w>16384u||h>16384u||
           (i&&edges[i-1u]->down_block>=e.down_block)||
           e.skip_windows_x!=(w+7u)/8u||
           e.skip_windows_y!=(h+7u)/8u||
           input_windows[i].windows_x!=e.skip_windows_x||
           input_windows[i].windows_y!=e.skip_windows_y||
           input_windows[i].shift_x||input_windows[i].shift_y||
           output_windows[i].windows_x!=e.skip_windows_x||
           output_windows[i].windows_y!=e.skip_windows_y||
           output_windows[i].shift_x<-1||
           output_windows[i].shift_x>1||
           output_windows[i].shift_y<-1||
           output_windows[i].shift_y>1)return false;
        if(i==0u&&w*h*32u>first_raster_capacity)return false;
        if(i<3u){
            const auto next_capacity=
                std::uint64_t(input_windows[i+1u].windows_x)*
                input_windows[i+1u].windows_y*64u*(channels*2u);
            if(!CanFSwinLevelLink(
                   {static_cast<std::uint32_t>(w),
                    static_cast<std::uint32_t>(h),channels,channels*2u,
                    output_windows[i],input_windows[i+1u]},
                   down_raster_capacity[i],next_capacity))
                return false;
        }else{
            const FSwinDownsample last{
                static_cast<std::uint32_t>(w),
                static_cast<std::uint32_t>(h),
                e.skip_windows_x,e.skip_windows_y,channels,
                output_windows[i].shift_x,output_windows[i].shift_y,
                0u,0u,0u};
            const FSwinDownsampleStorage capacities{
                std::uint64_t(e.skip_windows_x)*e.skip_windows_y*
                    64u*channels,
                256ull<<20,down_raster_capacity[i]};
            if(!CanFSwinDownsample(last,capacities))return false;
        }
    }
    return true;
}
} // namespace Eden::Graphics::NeuralRDNA2
