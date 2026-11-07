// SPDX-License-Identifier: MIT
// Model-native preblock -> half-resolution C32 contract.
// This only checks the recovered plan. It neither supplies texture guides
// nor claims that the fused, learned PreBlock Vulkan kernel is implemented.
#pragma once
#include "video_core/renderer_vulkan/nr_rdna2_unet_skip_map.h"
#include <cstdint>
#include <span>
namespace Eden::Graphics::NeuralRDNA2 {
[[nodiscard]] inline bool CanNativePreblockBoundary(
    std::span<const NativePlanStep> rows,
    const NativeUNetSkipMap& graph,
    std::uint64_t half_c32_bytes) noexcept {
    if(rows.size()<3u||graph.count!=4u)return false;
    const auto& pre=rows[0];
    const auto& first=rows[1];
    if(pre.block!=0u||pre.layer!=0u||
       pre.type!="CCTinlayoutFusedPreBlockSwin1H"||
       pre.kernel!="cc_tinlayout_fused_pre_block_swin_1h_32_1_ds_fp8"||
       pre.div!=1u||pre.channels!=3u||pre.heads!=0u||
       pre.input_channels!=3u||pre.output_channels!=32u||
       pre.inputs!=0u||pre.input0!=-1||pre.input1!=-1||
       pre.shifted||pre.shift_x!=0||pre.shift_y!=0||
       !pre.width||!pre.height||pre.width>8192u||pre.height>8192u||
       (pre.width&1u)||(pre.height&1u)||
       pre.grid_z!=1u||
       pre.grid_x!=(pre.height+7u)/8u||
       pre.grid_y!=(pre.width+7u)/8u||
       pre.tokens!=std::uint64_t(pre.width)*pre.height)
        return false;
    if(first.block!=1u||first.layer!=0u||first.div!=2u||
       first.type!="CCTinlayoutFusedSwin1H"||
       first.kernel!="cc_tinlayout_fused_swin_1h_32_1_inpview_fp8"||
       first.width!=pre.width/2u||first.height!=pre.height/2u||
       first.channels!=32u||first.heads!=1u||
       first.input_channels!=32u||first.output_channels!=32u||
       first.inputs!=1u||first.input0!=0||first.input1!=-1||
       first.grid_z!=1u||
       first.grid_x!=(first.height+7u)/8u||
       first.grid_y!=(first.width+7u)/8u||
       first.tokens!=std::uint64_t(first.grid_x)*first.grid_y*64u)
        return false;
    // Don't silently permit a second preblock or an unrelated C32 U-Net
    // skip entry to masquerade as this model's downscaled boundary.
    for(std::size_t i=2u;i<rows.size();++i)
        if(rows[i].type.starts_with("CCTinlayoutFusedPreBlock"))
            return false;
    const NativeUNetSkipEdge* c32=nullptr;
    for(const auto& edge:graph.edges)
        if(edge.channels==32u){
            if(c32)return false;
            c32=&edge;
        }
    if(!c32||c32->down_block<=first.block||
       c32->skip_width!=first.width||
       c32->skip_height!=first.height||
       c32->skip_windows_x!=first.grid_x||
       c32->skip_windows_y!=first.grid_y)
        return false;
    const auto needed=std::uint64_t(first.width)*first.height*32u;
    constexpr auto limit=256ull<<20;
    return needed<=limit&&half_c32_bytes>=needed&&half_c32_bytes<=limit;
}
} // namespace Eden::Graphics::NeuralRDNA2
