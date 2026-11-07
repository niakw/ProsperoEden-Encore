// SPDX-License-Identifier: MIT
// Fail-closed native GPU bottleneck route: Split0 -> ViT8 -> decoder -> Split1.
// A decoded 152/76-step schedule alone is not executable inference.
#pragma once
#include "rdna2_nr_split_native_routes_policy.h"
#include "rdna2_nr_vit_native_route_policy.h"
namespace Eden::Graphics::NeuralRDNA2 {
[[nodiscard]] constexpr bool CanLinkNativeNrBottleneckRoutes(
    const NativeSplitRoutes& split,
    const NativeVitRoute& vit) noexcept {
    if(split.run_count!=2u||split.count==0u||
       vit.count!=8u||vit.tokens==0u||
       !vit.raster_width||!vit.raster_height)return false;
    const auto& a=split.runs[0];
    const auto& b=split.runs[1];
    if(!a.count||!b.count||a.start+a.count>split.count||
       b.start+b.count>split.count||a.start!=0u||
       b.start!=a.start+a.count||b.start+b.count!=split.count)
        return false;
    const auto& before=split.blocks[a.start+a.count-1u];
    const auto& after=split.blocks[b.start];
    if(!before.plan.has_pooled_projection||
       before.block!=a.terminal_block||
       before.block!=vit.input_split_block||
       before.plan.final_head_tokens==0u||
       !after.block||
       after.source_block!=vit.decoder_block||
       b.entry_block!=vit.decoder_block||
       vit.decoder_block!=vit.blocks[7].block+1u||
       vit.blocks[0].input_block!=before.block||
       vit.raster_width!=before.raster_width||
       vit.raster_height!=before.raster_height||
       !split.blocks[b.start+b.count-1u].output_view)
        return false;
    for(std::uint32_t i=0u;i<8u;++i){
        if(vit.blocks[i].block!=vit.blocks[0].block+i||
           vit.blocks[i].tokens!=vit.tokens||
           vit.blocks[i].input_block!=(i==0u?before.block:
                                          vit.blocks[i-1u].block))
            return false;
    }
    return true;
}
} // namespace Eden::Graphics::NeuralRDNA2
