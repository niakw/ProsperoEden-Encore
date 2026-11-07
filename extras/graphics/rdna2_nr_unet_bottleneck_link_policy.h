// SPDX-License-Identifier: MIT
// R09: native C512 down -> Split/ViT bottleneck -> C512 up boundary.
// This checks model geometry/graph order/capacities, NOT GPU execution.
#pragma once
#include "rdna2_nr_bottleneck_route_policy.h"
#include "video_core/renderer_vulkan/nr_rdna2_unet_skip_map.h"
#include <cstdint>
namespace Eden::Graphics::NeuralRDNA2 {
[[nodiscard]] inline bool CanNativeUNetBottleneckLink(
    const NativeUNetSkipMap& graph,
    const NativeSplitRoutes& split,
    const NativeVitRoute& vit,
    std::uint64_t down_c512_bytes,
    std::uint64_t split_input_bytes,
    std::uint64_t split_output_bytes) noexcept {
    if(graph.count!=4u||!CanLinkNativeNrBottleneckRoutes(split,vit))
        return false;
    const NativeUNetSkipEdge* last_down=nullptr;
    std::uint32_t found=0u;
    for(const auto& edge:graph.edges){
        const auto c=edge.channels;
        const auto index=c==32u?0u:c==64u?1u:c==128u?2u:
                         c==256u?3u:4u;
        if(index==4u||(found&(1u<<index)))return false;
        found|=(1u<<index);
        if(index==3u)last_down=&edge;
    }
    if(found!=15u||!last_down)return false;
    const auto& entry=split.runs[0];
    const auto& exit=split.runs[1];
    const auto& first=split.blocks[entry.start];
    const auto& final=split.blocks[exit.start+exit.count-1u];
    const std::uint32_t width=last_down->skip_height/2u;
    const std::uint32_t height=last_down->skip_width/2u;
    if(!width||!height||entry.entry_block!=last_down->down_block||
       exit.terminal_block!=last_down->up_input_block||
       !first.input_view||!final.output_view||
       first.raster_width!=width||first.raster_height!=height||
       final.raster_width!=width||final.raster_height!=height||
       last_down->up_input_width!=height||
       last_down->up_input_height!=width||
       vit.raster_width!=width||vit.raster_height!=height)
        return false;
    const auto needed=std::uint64_t(width)*height*512u;
    constexpr auto kLimit=256ull<<20;
    return needed<=kLimit&&needed<=down_c512_bytes&&
           needed<=split_input_bytes&&needed<=split_output_bytes&&
           down_c512_bytes<=kLimit&&split_input_bytes<=kLimit&&
           split_output_bytes<=kLimit;
}
} // namespace Eden::Graphics::NeuralRDNA2
