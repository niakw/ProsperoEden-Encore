// SPDX-License-Identifier: MIT
// Derive native Split-Swin16H block plans from BOTH real model schedules.
// No per-game routing, no guessed manual shifts or silently dropped pool.
#pragma once
#include "rdna2_nr_split_block_policy.h"
#include "video_core/renderer_vulkan/nr_rdna2_native_graph_schedule.h"
#include <array>
#include <cstddef>
#include <cstdint>
#include <span>
namespace Eden::Graphics::NeuralRDNA2 {
enum class SplitNativeRoutesError : std::uint8_t {
    Ok, InvalidSchedule, NoSplit, TooMany, InvalidLayers,
    InvalidShape, InvalidShift, BadPredecessor, BadBoundary
};
struct NativeSplitBlockRoute {
    SplitBlockPlan plan{};
    std::uint32_t block{},first_row{},layer_count{},source_block{};
    std::uint32_t native_compute_tokens{}; // 4x4 tile domain, not padded windows
    bool input_view{},output_view{};
    // Real XY feature raster orientation, upstream gemmpool p.W=s.H.
    std::uint32_t raster_width{},raster_height{};
};
struct NativeSplitRun {
    std::uint32_t start{},count{},entry_block{},terminal_block{};
};
struct NativeSplitRoutes {
    std::array<NativeSplitBlockRoute,32> blocks{};
    std::array<NativeSplitRun,2> runs{};
    std::uint32_t count{},run_count{};
};
[[nodiscard]] inline SplitNativeRoutesError BuildNativeSplitRoutes(
    std::span<const NativePlanStep> rows,NativeSplitRoutes& out) {
    out={};
    NativeNrSchedule schedule;
    if(BuildNativeNrSchedule(rows,schedule)!=NativeNrGraphError::Ok)
        return SplitNativeRoutesError::InvalidSchedule;
    NativeSplitRoutes built{};
    for(std::uint32_t i=0u;i<rows.size();++i){
        const auto op=schedule.instructions[i].operation;
        if(!IsNativeNrSplitOp(op))continue;
        if(op!=NativeNrOp::SplitFfwd)
            return SplitNativeRoutesError::InvalidLayers;
        if(built.count>=built.blocks.size())
            return SplitNativeRoutesError::TooMany;
        const auto& first=rows[i];
        if(first.layer!=0u||first.input0<0)
            return SplitNativeRoutesError::InvalidLayers;
        const std::uint32_t block=first.block;
        if(i+3u>=rows.size())return SplitNativeRoutesError::InvalidLayers;
        constexpr std::array<NativeNrOp,3> kRequired{
            NativeNrOp::SplitFfwdProjection,NativeNrOp::SplitQkvAttention,
            NativeNrOp::SplitProjection};
        const auto& ffproj=rows[i+1u];
        const auto& qkv=rows[i+2u];
        const auto& last=rows[i+3u];
        if(schedule.instructions[i+1u].operation!=kRequired[0]||
           schedule.instructions[i+2u].operation!=kRequired[1]||
           (schedule.instructions[i+3u].operation!=kRequired[2]&&
            schedule.instructions[i+3u].operation!=NativeNrOp::SplitProjectionPool))
            return SplitNativeRoutesError::InvalidLayers;
        const bool pooled=
            schedule.instructions[i+3u].operation==NativeNrOp::SplitProjectionPool;
        const std::uint32_t layer_count=pooled?5u:4u;
        if(i+layer_count>rows.size())return SplitNativeRoutesError::InvalidLayers;
        for(std::uint32_t layer=1u;layer<layer_count;++layer){
            const auto& s=rows[i+layer];
            if(s.block!=block||s.layer!=layer||
               s.width!=first.width||s.height!=first.height||
               s.tokens!=first.tokens||s.input0!=static_cast<std::int32_t>(block))
                return SplitNativeRoutesError::InvalidLayers;
        }
        if(pooled&&schedule.instructions[i+4u].operation!=
                      NativeNrOp::SplitFinalHead)
            return SplitNativeRoutesError::InvalidLayers;
        if(!pooled&&i+4u<rows.size()&&
           rows[i+4u].block==block)
            return SplitNativeRoutesError::InvalidLayers;
        const std::uint32_t wx=(first.height+7u)/8u;
        const std::uint32_t wy=(first.width+7u)/8u;
        const std::uint64_t total=std::uint64_t(wx)*wy;
        const std::uint64_t compute=
            std::uint64_t((first.width+3u)/4u)*
            ((first.height+3u)/4u)*16u;
        if(!total||total>1023u||compute>65535u||
           std::uint64_t(first.tokens)!=total*64u||
           qkv.grid_x!=wx||qkv.grid_y!=wy||
           qkv.grid_z!=4u||first.channels!=512u||
           ffproj.channels!=512u||last.channels!=512u)
            return SplitNativeRoutesError::InvalidShape;
        // Never accept missing optional native shift fields (sentinel 100).
        if(qkv.shift_x<-1||qkv.shift_x>1||
           qkv.shift_y<-1||qkv.shift_y>1||
           ((qkv.shift_x!=0||qkv.shift_y!=0)!=qkv.shifted))
            return SplitNativeRoutesError::InvalidShift;
        SplitBlockPlan p{};
        p.windows=static_cast<std::uint32_t>(total);
        p.window_grid_x=wx;
        p.window_grid_y=wy;
        p.attention_shift_x=qkv.shift_x;
        p.attention_shift_y=qkv.shift_y;
        p.has_pooled_projection=pooled;
        if(pooled){
            p.pool_width=first.height; // upstream gemmpool p.W=s.H
            p.pool_height=first.width; // and p.rows=s.W
            p.pool_windows_x=wx;
            p.pool_windows_y=wy;
            // Upstream GEMM domain is 4x4 tiles; the side buffer MUST
            // include zero-filled tail up to the FinalHead read extent.
            p.pool_output_tokens=static_cast<std::uint32_t>(compute);
            p.final_head_tokens=static_cast<std::uint32_t>(compute);
        }
        const bool input_view=first.kernel.find("_inpview_")!=
                              std::string::npos;
        const bool output_view=last.kernel.find("_outview_")!=
                               std::string::npos;
        if(output_view&&pooled)return SplitNativeRoutesError::BadBoundary;
        if(built.count==0u||
           first.input0!=static_cast<std::int32_t>(
                              built.blocks[built.count-1u].block)){
            if(built.run_count>=built.runs.size())
                return SplitNativeRoutesError::BadBoundary;
            built.runs[built.run_count++]={
                built.count,0u,static_cast<std::uint32_t>(first.input0),block};
        } else if(built.runs[built.run_count-1u].terminal_block!=
                  built.blocks[built.count-1u].block) {
            return SplitNativeRoutesError::BadPredecessor;
        }
        auto& run=built.runs[built.run_count-1u];
        ++run.count;
        run.terminal_block=block;
        built.blocks[built.count++]={
            p,block,i,layer_count,static_cast<std::uint32_t>(first.input0),
            static_cast<std::uint32_t>(compute),input_view,output_view,
            first.height,first.width};
        i+=layer_count-1u;
    }
    if(!built.count||built.run_count!=2u)
        return built.count?SplitNativeRoutesError::BadBoundary:
                           SplitNativeRoutesError::NoSplit;
    // Native 152 and 76 models each cross FSwin->Split, Split->ViT
    // and ViT->Split->FSwin exactly once; their block IDs differ.
    const auto& r0=built.runs[0];
    const auto& r1=built.runs[1];
    if(!built.blocks[r0.start].input_view||
       !built.blocks[r0.start+r0.count-1u].plan.has_pooled_projection||
       !built.blocks[r1.start+r1.count-1u].output_view||
       built.blocks[r0.start+r0.count-1u].output_view||
       built.blocks[r1.start].input_view)
        return SplitNativeRoutesError::BadBoundary;
    std::uint32_t pools=0u,finals=0u,ins=0u,outs=0u;
    for(std::uint32_t k=0u;k<built.count;++k){
        pools+=built.blocks[k].plan.has_pooled_projection;
        finals+=built.blocks[k].plan.final_head_tokens!=0u;
        ins+=built.blocks[k].input_view;
        outs+=built.blocks[k].output_view;
    }
    if(pools!=1u||finals!=1u||ins!=1u||outs!=1u)
        return SplitNativeRoutesError::BadBoundary;
    out=built;
    return SplitNativeRoutesError::Ok;
}
} // namespace Eden::Graphics::NeuralRDNA2
