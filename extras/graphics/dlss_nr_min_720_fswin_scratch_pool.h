// SPDX-License-Identifier: GPL-3.0-or-later
// HOST-ONLY conservative FSwin scratch-pooling design for a candidate
// R09 Original/Compact 720p graph. No borrowed native VkBuffer handles,
// descriptor writes, Vulkan scheduling changes or PS5 execution.
//
// Unlike speculative full ping-pong, ONLY intra-layer temporary roles
// expanded/middle/contracted/context are shared BETWEEN sequential layers
// in ONE native FSwin segment. Each layer retains a private UPLOAD input
// and a private GPU output, preserving LinkInputFrom's real CopyBuffer,
// input/output handle inequality and each layer's published descriptors.
// Q/K/V are already non-owning views into expanded and are never counted
// as distinct allocations. Nothing is shared across chains or sessions.
#pragma once
#include "dlss_nr_min_720_fswin_tensor_audit.h"
#include <algorithm>
#include <array>
#include <cstdint>
#include <limits>
#include <string_view>

namespace Eden::Graphics::DlssNrMin {
enum class FSwinScratchPoolIssue : std::uint8_t {
    None, BadReference, BadSegment, BadPlan, BadRole,
    InvalidCapacity, SourceDrift, ArithmeticOverflow
};
struct FSwinScratchChainPlan {
    std::uint32_t layers{},channels{},windows{};
    std::uint32_t private_buffers{},pool_buffers{};
    std::uint64_t reference_bytes{},proposed_bytes{},saved_bytes{};
    std::uint64_t private_input_bytes{},private_output_bytes{};
    // Four scratch roles. Index 1 is absent for C32.
    std::array<std::uint64_t,4u> pooled_scratch_bytes{};
    bool private_input_output{true},cross_chain_aliasing{false};
};
struct FSwinScratchPoolPlan {
    FSwinScratchPoolIssue issue{FSwinScratchPoolIssue::None};
    std::array<FSwinScratchChainPlan,8u> chains{};
    std::uint32_t chain_count{},layers{};
    std::uint32_t reference_buffers{},proposed_buffers{};
    std::uint64_t reference_bytes{},proposed_bytes{},saved_bytes{};
    // Sharing raw buffers requires separate native VkBuffer ownership,
    // binding and synchronization verification on a real GPU.
    bool runtime_wired{false},sync_qualified{false};
};
[[nodiscard]] inline bool MakeFSwinScratchPool720Candidate(
    std::string_view reference,FSwinScratchPoolPlan& out) {
    out={};
    Route720Trial trial{};
    if(!BuildR09Min720Routes(reference,trial)) {
        out.issue=FSwinScratchPoolIssue::BadReference;
        return false;
    }
    const auto segments=NR::ExtractNativeFSwinSegments(trial.rows);
    if(segments.size()!=8u) {
        out.issue=FSwinScratchPoolIssue::BadSegment;
        return false;
    }
    FSwin720TensorEstimate original{};
    if(!AuditFSwin720OwnedTensorBuffers(reference,original)) {
        out.issue=FSwinScratchPoolIssue::SourceDrift;
        return false;
    }
    FSwinScratchPoolPlan result{};
    constexpr std::uint64_t kBufferMax=256ull<<20u;
    for(std::size_t segment_index=0;segment_index<segments.size();
        ++segment_index) {
        const auto& segment=segments[segment_index];
        if(segment.layers.empty()||segment.layers.size()>160u) {
            out.issue=FSwinScratchPoolIssue::BadSegment;
            return false;
        }
        auto& chain=result.chains[segment_index];
        chain.layers=static_cast<std::uint32_t>(segment.layers.size());
        chain.channels=segment.layers.front().channels;
        chain.windows=segment.layers.front().windows;
        const auto c32=chain.channels==32u;
        // Native chain initializer requires a uniform channel/shape.
        if(!chain.windows||!chain.channels) {
            out.issue=FSwinScratchPoolIssue::BadSegment;
            return false;
        }
        for(const auto& layer:segment.layers) {
            if(layer.channels!=chain.channels||layer.windows!=chain.windows) {
                out.issue=FSwinScratchPoolIssue::BadSegment;
                return false;
            }
            NR::FSwinGraph p{};
            if(!NR::MakeFSwinGraphPlan(layer.channels,layer.windows,p)) {
                out.issue=FSwinScratchPoolIssue::BadPlan;
                return false;
            }
            const auto input=std::max(p.dense_storage[0].input_bytes,
                                      p.dense_storage[2].residual_bytes);
            const auto expanded=p.dense_storage[0].output_bytes;
            const auto middle=c32?0u:p.dense_storage[1].output_bytes;
            const auto contracted=std::max({
                p.dense_storage[2].output_bytes,
                p.dense_storage[3].residual_bytes,
                p.qkv_storage.activation_bytes});
            const auto context=std::max(
                p.attention_storage.out_bytes,
                p.dense_storage[3].input_bytes);
            const auto output=p.dense_storage[3].output_bytes;
            if(!input||!expanded||(!c32&&!middle)||
               !contracted||!context||!output||
               (input|expanded|middle|contracted|context|output)&3u||
               input>kBufferMax||expanded>kBufferMax||
               middle>kBufferMax||contracted>kBufferMax||
               context>kBufferMax||output>kBufferMax) {
                out.issue=FSwinScratchPoolIssue::InvalidCapacity;
                return false;
            }
            // Within a layer all these roles MUST keep distinct identities.
            // Shared across layers only AFTER that layer is completed.
            const std::array<std::uint64_t,4u> scratch{
                expanded,middle,contracted,context};
            for(std::size_t role=0;role<scratch.size();++role)
                chain.pooled_scratch_bytes[role]=std::max(
                    chain.pooled_scratch_bytes[role],scratch[role]);
            const auto native_total=input+output+expanded+middle+
                                    contracted+context;
            chain.reference_bytes+=native_total;
            chain.private_input_bytes+=input;
            chain.private_output_bytes+=output;
            chain.private_buffers+=2u;
        }
        // All original buffers are per-layer. The proposed ONLY persistent
        // extra owners are scratch roles 1/2/3/7, one per chain.
        const auto scratch_count=c32?3u:4u;
        std::uint64_t scratch_total{};
        for(const auto n:chain.pooled_scratch_bytes)
            scratch_total+=n;
        chain.pool_buffers=scratch_count;
        chain.proposed_bytes=chain.private_input_bytes+
                             chain.private_output_bytes+scratch_total;
        if(chain.proposed_bytes>chain.reference_bytes) {
            out.issue=FSwinScratchPoolIssue::InvalidCapacity;
            return false;
        }
        chain.saved_bytes=chain.reference_bytes-chain.proposed_bytes;
        result.reference_bytes+=chain.reference_bytes;
        result.proposed_bytes+=chain.proposed_bytes;
        result.reference_buffers+=chain.layers*(c32?5u:6u);
        result.proposed_buffers+=chain.private_buffers+chain.pool_buffers;
        result.layers+=chain.layers;
        ++result.chain_count;
    }
    result.saved_bytes=result.reference_bytes-result.proposed_bytes;
    if(result.reference_bytes!=original.requested_bytes||
       result.reference_buffers!=original.buffer_count||
       result.layers!=original.layers||result.chain_count!=8u||
       result.proposed_bytes>=result.reference_bytes||
       result.proposed_buffers>=result.reference_buffers) {
        out.issue=FSwinScratchPoolIssue::SourceDrift;
        return false;
    }
    result.runtime_wired=false;
    result.sync_qualified=false;
    out=result;
    return true;
}
} // namespace Eden::Graphics::DlssNrMin
