// SPDX-License-Identifier: MIT
// ViT graph routing from the complete native 152/76-row MIT model plans.
// Exactly eight blocks with five real operations each, no silent skips.
#pragma once
#include "video_core/renderer_vulkan/nr_rdna2_native_graph_schedule.h"
#include <array>
#include <cstdint>
#include <span>
namespace Eden::Graphics::NeuralRDNA2 {
enum class NativeVitRouteError:std::uint8_t {
    Ok,MissingVit,InvalidOrder,InvalidShape,InvalidSource,
    MissingInput,MissingDecoder,Incomplete
};
struct NativeVitBlockRoute {
    std::uint32_t block{},first_row{},tokens{},input_block{};
};
struct NativeVitRoute {
    std::array<NativeVitBlockRoute,8> blocks{};
    std::uint32_t count{},input_split_block{},decoder_block{},tokens{};
};
[[nodiscard]] inline NativeVitRouteError BuildNativeVitRoute(
    std::span<const NativePlanStep> rows,NativeVitRoute& output) {
    output={};
    NativeNrSchedule schedule;
    if(BuildNativeNrSchedule(rows,schedule)!=NativeNrGraphError::Ok)
        return NativeVitRouteError::InvalidOrder;
    NativeVitRoute staged{};
    constexpr std::array<NativeNrOp,5> expected{
        NativeNrOp::VitFfwdExpand,NativeNrOp::VitFfwdContract,
        NativeNrOp::VitQkv,NativeNrOp::VitAttention,
        NativeNrOp::VitProjection};
    for(std::uint32_t i=0u;i<rows.size();++i){
        if(!IsNativeNrVitOp(schedule.instructions[i].operation))
            continue;
        if(staged.count>=staged.blocks.size()||i+5u>rows.size())
            return NativeVitRouteError::Incomplete;
        const auto& first=rows[i];
        if(first.layer!=0u||first.inputs!=1u||first.input0<0||
           first.tokens>4096u||first.tokens==0u)
            return NativeVitRouteError::InvalidShape;
        if(staged.count==0u){
            if(i==0u||
               schedule.instructions[i-1u].operation!=
                   NativeNrOp::SplitFinalHead||
               rows[i-1u].block!=static_cast<std::uint32_t>(first.input0))
                return NativeVitRouteError::MissingInput;
            staged.input_split_block=static_cast<std::uint32_t>(first.input0);
            staged.tokens=static_cast<std::uint32_t>(first.tokens);
        } else if(first.block!=staged.blocks[staged.count-1u].block+1u||
                  first.input0!=static_cast<std::int32_t>(
                      staged.blocks[staged.count-1u].block))
            return NativeVitRouteError::InvalidSource;
        if(first.tokens!=staged.tokens)return NativeVitRouteError::InvalidShape;
        for(std::uint32_t j=0u;j<5u;++j){
            const auto& s=rows[i+j];
            if(schedule.instructions[i+j].operation!=expected[j]||
               s.block!=first.block||s.layer!=j||s.tokens!=first.tokens||
               s.width!=first.width||s.height!=first.height||
               s.inputs!=1u||s.input1!=-1||
               (j!=0u&&s.input0!=static_cast<std::int32_t>(first.block)))
                return NativeVitRouteError::InvalidShape;
        }
        staged.blocks[staged.count++]={
            first.block,i,staged.tokens,
            static_cast<std::uint32_t>(first.input0)};
        i+=4u;
    }
    if(!staged.count)return NativeVitRouteError::MissingVit;
    if(staged.count!=8u)return NativeVitRouteError::Incomplete;
    const auto last=staged.blocks.back();
    const std::uint32_t after=last.first_row+5u;
    if(after>=rows.size()||
       schedule.instructions[after].operation!=
          NativeNrOp::DecoderUpsample)
        return NativeVitRouteError::MissingDecoder;
    const auto& decoder=rows[after];
    if(decoder.input0!=static_cast<std::int32_t>(last.block)||
       decoder.input1!=static_cast<std::int32_t>(
           staged.input_split_block)||decoder.inputs!=2u)
        return NativeVitRouteError::InvalidSource;
    staged.decoder_block=decoder.block;
    output=staged;
    return NativeVitRouteError::Ok;
}
} // namespace Eden::Graphics::NeuralRDNA2
