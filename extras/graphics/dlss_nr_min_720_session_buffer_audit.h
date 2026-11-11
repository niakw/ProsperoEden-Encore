// SPDX-License-Identifier: GPL-3.0-or-later
// HOST-ONLY 720p budget mirror of NrRdna2FrameSession::State::Make().
// These are the EXTERNAL buffers requested by the pinned native frame
// assembler, not FSwin-internal allocations, model weights or physical VRAM.
// Never enable a PS5 path from a successful estimate.
#pragma once
#include "dlss_nr_min_720_route_trial.h"
#include <array>
#include <cstdint>
#include <limits>
#include <string_view>

namespace Eden::Graphics::DlssNrMin {
inline constexpr std::uint64_t kNativeMaxOneBuffer = 256ull<<20u;
inline constexpr std::uint64_t kNativeMaxFrameBuffers = 3ull<<30u;
enum class NativeSessionStage : std::uint8_t {
    Preblock, DownOutputs, SplitBeforeVit, EightVitBlocks,
    Decoder, SplitAfterVit, UpOutputs, Postblock, Count
};
enum class NativeSessionBudgetIssue : std::uint8_t {
    None, InvalidRoute, InvalidShape, InvalidBuffer, PerBufferCap,
    TotalFrameCap
};
struct NativeSessionStageBudget {
    std::uint32_t buffers{};
    std::uint64_t requested_bytes{};
};
struct NativeSessionBufferBudget {
    NativeSessionBudgetIssue issue{NativeSessionBudgetIssue::None};
    std::array<NativeSessionStageBudget,
        static_cast<unsigned>(NativeSessionStage::Count)> stages{};
    std::uint32_t buffer_count{};
    std::uint64_t external_bytes{},largest_buffer{};
    std::uint32_t split_blocks{},vit_blocks{};
    bool source_lifetime_qualified{false};
    bool gpu_executable{false};
};
// Exact positive-only Make() admission as long as the vendor's per-buffer
// and per-session caps remain unchanged, validated by a separate source guard.
// Vulkan device maxStorageBufferRange, allocator failures and REAL VMA state
// cannot be known here, and remain independent runtime rejection causes.
[[nodiscard]] inline bool AuditNativeSession720BufferRequests(
    std::string_view reference,NativeSessionBufferBudget& output) {
    output={};
    Route720Trial route{};
    if(!BuildR09Min720Routes(reference,route)) {
        output.issue=NativeSessionBudgetIssue::InvalidRoute;
        return false;
    }
    NativeSessionBufferBudget draft{};
    auto add=[&](NativeSessionStage stage,std::uint64_t n)->bool {
        if(!n||(n&3u)) {
            draft.issue=NativeSessionBudgetIssue::InvalidBuffer;
            return false;
        }
        if(n>kNativeMaxOneBuffer) {
            draft.issue=NativeSessionBudgetIssue::PerBufferCap;
            return false;
        }
        if(n>kNativeMaxFrameBuffers||
           draft.external_bytes>kNativeMaxFrameBuffers-n){
            draft.issue=NativeSessionBudgetIssue::TotalFrameCap;
            return false;
        }
        auto& q=draft.stages[static_cast<unsigned>(stage)];
        ++q.buffers;
        q.requested_bytes+=n;
        ++draft.buffer_count;
        draft.external_bytes+=n;
        if(n>draft.largest_buffer)draft.largest_buffer=n;
        return true;
    };
    const auto width=route.rows.front().height;
    const auto height=route.rows.front().width;
    const auto pixels=std::uint64_t(width)*height;
    if(width!=720u||height!=1280u||
       route.vit.count!=8u||route.vit.tokens!=960u||
       route.skips.count!=4u||route.split.run_count!=2u){
        output.issue=NativeSessionBudgetIssue::InvalidShape;
        return false;
    }
    // FrameSession::Initialize(): proxy, feature16, lifted, full_skip,
    // raw_pre and first_half. Independent buffers, NO aliases.
    for(const auto channels:{16ull,32ull,32ull,32ull,64ull,8ull})
        if(!add(NativeSessionStage::Preblock,pixels*channels)){
            output.issue=draft.issue;return false;
        }
    // Each matching UNet down edge produces its own half-size storage.
    std::array<bool,4> down_seen{},up_seen{};
    for(const auto& edge:route.skips.edges){
        const auto c=edge.channels;
        const unsigned d=c==32u?0u:c==64u?1u:c==128u?2u:3u;
        const unsigned u=c==256u?0u:c==128u?1u:c==64u?2u:3u;
        if((c!=32u&&c!=64u&&c!=128u&&c!=256u)||
           down_seen[d]||up_seen[u]||!edge.skip_width||!edge.skip_height) {
            output.issue=NativeSessionBudgetIssue::InvalidShape;
            return false;
        }
        down_seen[d]=true;
        up_seen[u]=true;
        const auto low=std::uint64_t(edge.skip_height/2u)*
                       (edge.skip_width/2u)*(2u*c);
        if(!add(NativeSessionStage::DownOutputs,low)){
            output.issue=draft.issue;return false;
        }
    }
    // Actual MakeFirstSplitBuffers(): first input is externally allocated
    // only on run0. Every other input aliases previous projected output,
    // or for run1 the existing learned decoder output. Never double-count.
    for(unsigned run_index=0;run_index<2u;++run_index) {
        const auto& run=route.split.runs[run_index];
        if(!run.count||run.start+run.count>route.split.count){
            output.issue=NativeSessionBudgetIssue::InvalidShape;
            return false;
        }
        const auto stage=run_index==0u?
            NativeSessionStage::SplitBeforeVit:
            NativeSessionStage::SplitAfterVit;
        for(unsigned i=0u;i<run.count;++i) {
            const auto& p=route.split.blocks[run.start+i].plan;
            if(!p.windows){
                output.issue=NativeSessionBudgetIssue::InvalidShape;
                return false;
            }
            const auto linear=std::uint64_t(p.windows)*64ull;
            const auto linear512=linear*512ull;
            if((!run_index&&!i&&!add(stage,linear512))||
               !add(stage,linear512)|| // ffwd
               !add(stage,linear512)|| // ffwd_projected
               !add(stage,linear512)|| // context_heads
               !add(stage,linear512)|| // context_tokens
               !add(stage,linear512)|| // projected
               !add(stage,linear512)|| // query
               !add(stage,linear512)|| // key
               !add(stage,linear512)|| // value
               !add(stage,linear512*4ull)) { // fp32_scratch
                output.issue=draft.issue;return false;
            }
            if(p.attention_shift_x||p.attention_shift_y) {
                if(!add(stage,linear512)||!add(stage,linear512)) {
                    output.issue=draft.issue;return false;
                }
            }
            if(p.has_pooled_projection) {
                if(!p.pool_output_tokens||!p.final_head_tokens||
                   !add(stage,std::uint64_t(p.pool_output_tokens)*512ull)||
                   !add(stage,std::uint64_t(p.final_head_tokens)*4096ull)||
                   !add(stage,std::uint64_t(p.final_head_tokens)*1024ull)){
                    output.issue=NativeSessionBudgetIssue::InvalidShape;
                    return false;
                }
            }
            ++draft.split_blocks;
        }
    }
    // Native MakeVitBuffers() is 1 plane for block0 input plus eight
    // buffers per block: 4+1+1+1+4+4+4+4 = 23 planes.
    const auto plane=std::uint64_t(route.vit.tokens)*1024ull;
    if(!add(NativeSessionStage::EightVitBlocks,plane)) {
        output.issue=draft.issue;return false;
    }
    for(unsigned i=0u;i<route.vit.count;++i){
        for(const auto size:{4ull,1ull,1ull,1ull,4ull,4ull,4ull,4ull})
            if(!add(NativeSessionStage::EightVitBlocks,plane*size)){
                output.issue=draft.issue;return false;
            }
        ++draft.vit_blocks;
    }
    // Decoder_tiles + exact valid-raster conversion, projection, skip,
    // and output buffers. The second split's second_low buffer is distinct.
    const auto valid=std::uint64_t(route.vit.raster_width)*
                     route.vit.raster_height;
    if(valid!=880ull){
        output.issue=NativeSessionBudgetIssue::InvalidShape;return false;
    }
    for(const auto size:{plane,valid*1024ull,valid*512ull*4ull,
                         valid*512ull*2ull,
                         std::uint64_t(route.vit.tokens)*512ull,
                         std::uint64_t(route.vit.tokens)*512ull})
        if(!add(NativeSessionStage::Decoder,size)){
            output.issue=draft.issue;return false;
        }
    if(!add(NativeSessionStage::SplitAfterVit,valid*512ull)){
        output.issue=draft.issue;return false;
    }
    for(const auto& edge:route.skips.edges){
        const auto bytes=std::uint64_t(edge.skip_height)*
                         edge.skip_width*edge.channels;
        if(!add(NativeSessionStage::UpOutputs,bytes)){
            output.issue=draft.issue;return false;
        }
    }
    // post_mixed, post_swin, post_raw, post_features, composed RGBA32F
    // *buffer*. A separate sampled/storage Vulkan image is NOT included.
    for(const auto channels:{32ull,32ull,64ull,32ull,16ull})
        if(!add(NativeSessionStage::Postblock,pixels*channels)){
            output.issue=draft.issue;return false;
        }
    if(draft.stages[static_cast<unsigned>(
        NativeSessionStage::EightVitBlocks)].buffers!=65u||
       draft.vit_blocks!=8u||draft.stages[static_cast<unsigned>(
        NativeSessionStage::Preblock)].buffers!=6u||
       draft.stages[static_cast<unsigned>(
        NativeSessionStage::DownOutputs)].buffers!=4u||
       draft.stages[static_cast<unsigned>(
        NativeSessionStage::UpOutputs)].buffers!=4u||
       draft.stages[static_cast<unsigned>(
        NativeSessionStage::Postblock)].buffers!=5u||
       draft.stages[static_cast<unsigned>(
        NativeSessionStage::Decoder)].buffers!=6u) {
        output.issue=NativeSessionBudgetIssue::InvalidShape;
        return false;
    }
    draft.source_lifetime_qualified=false;
    draft.gpu_executable=false;
    output=draft;
    return true;
}
} // namespace Eden::Graphics::DlssNrMin
