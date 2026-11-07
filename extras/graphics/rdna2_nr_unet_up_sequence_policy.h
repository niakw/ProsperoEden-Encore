// SPDX-License-Identifier: MIT
// R09: checked four-edge U-Net ascent from C512 into C32 raster.
// Validates the Original/Compact native skip geometry, not GPU parity.
#pragma once
#include "video_core/renderer_vulkan/nr_rdna2_unet_skip_map.h"
#include "rdna2_nr_fswin_chain_layout_policy.h"
#include <array>
#include <cstdint>
namespace Eden::Graphics::NeuralRDNA2 {
[[nodiscard]] inline bool CanNativeUNetUpSequence(
    const NativeUNetSkipMap& graph,
    const std::array<FSwinWindowLayout,4>& inputs,
    const std::array<FSwinWindowLayout,4>& outputs,
    std::uint64_t initial_c512_bytes,
    const std::array<std::uint64_t,4>& raster_bytes) noexcept {
    if(graph.count!=4u)return false;
    std::array<const NativeUNetSkipEdge*,4> edges{};
    for(const auto& e:graph.edges){
        std::size_t i=4u;
        switch(e.channels){
        case 256u:i=0u;break;
        case 128u:i=1u;break;
        case 64u:i=2u;break;
        case 32u:i=3u;break;
        default:return false;
        }
        if(edges[i]||e.down_block>=e.up_block||
           e.up_input_block>=e.up_block)return false;
        edges[i]=&e;
    }
    constexpr auto limit=256ull<<20;
    for(std::size_t i=0u;i<4u;++i){
        if(!edges[i])return false;
        const auto& e=*edges[i];
        const std::uint64_t w=e.skip_height,h=e.skip_width;
        const auto C=256u>>i;
        if(w<2u||h<2u||w>16384u||h>16384u||
           e.skip_windows_x!=(w+7u)/8u||
           e.skip_windows_y!=(h+7u)/8u||
           e.up_input_width!=e.skip_width/2u||
           e.up_input_height!=e.skip_height/2u||
           (i&&(e.up_block<=edges[i-1u]->up_block||
                 e.up_input_block<=edges[i-1u]->up_block)))
            return false;
        const auto a=inputs[i],b=outputs[i];
        if(a.windows_x!=e.skip_windows_x||
           a.windows_y!=e.skip_windows_y||
           b.windows_x!=e.skip_windows_x||
           b.windows_y!=e.skip_windows_y||
           a.shift_x<-1||a.shift_x>1||
           a.shift_y<-1||a.shift_y>1||
           b.shift_x<-1||b.shift_x>1||
           b.shift_y<-1||b.shift_y>1)return false;
        // The 2C low raster is the prior full-resolution C raster.
        const auto needed_low=(w/2u)*(h/2u)*(C*2u);
        const auto present_low=i?raster_bytes[i-1u]:initial_c512_bytes;
        const auto needed_high=w*h*C;
        if(needed_low>limit||needed_high>limit||
           needed_low>present_low||needed_high>raster_bytes[i])
            return false;
    }
    return true;
}
} // namespace Eden::Graphics::NeuralRDNA2
