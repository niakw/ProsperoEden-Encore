// SPDX-License-Identifier: GPL-3.0-or-later
// HOST-ONLY candidate ViT scratch pool / cross-block alias inventory.
// Based on the exact *current* sequential NrRdna2VitRun::Record() and
// NrRdna2VitBlock::CanOwnVitBuffers() contracts in pinned vendor.
// Does NOT allocate VkBuffer, insert Vulkan barriers or change PS5 runtime.
// Safe GPU interblock reuse remains UNPROVEN and disabled.
#pragma once
#include "dlss_nr_min_vit_memory_audit.h"
#include <array>
#include <cstdint>
#include <limits>
#include <string_view>
#include <vector>

namespace Eden::Graphics::DlssNrMin {
enum class VitField : std::uint8_t {
    Input, Hidden, Ffwd, Attention, Output, Scratch, Query, Key, Value, Count
};
inline constexpr std::size_t kVitFieldCount=
    static_cast<std::size_t>(VitField::Count);
struct VitAliasedBlock {
    std::array<std::uint32_t,kVitFieldCount> slots{};
};
struct VitSlot {
    std::uint32_t id{};
    std::uint64_t requested_bytes{};
};
struct VitReuseCandidate {
    std::vector<VitAliasedBlock> blocks{};
    std::array<VitSlot,9> pool_slots{};
    std::uint64_t baseline_requested_bytes{};
    std::uint64_t candidate_requested_bytes{};
    std::uint64_t nominal_difference_bytes{};
    bool in_block_distinct{};
    bool previous_output_matches_next_input{};
    bool gpu_barriers_proven{false};
    bool gpu_fences_proven{false};
    bool runnable{false};
};
[[nodiscard]] inline bool BuildVitCrossBlockReuseCandidate(
    std::string_view native_plan,Extent raster,VitReuseCandidate& out) {
    out={};
    VitMemoryAudit sizes{};
    if(!AuditVitRequestedBufferBytes(native_plan,raster,sizes) ||
       sizes.vit_blocks!=8u || sizes.requested_buffers!=65u ||
       sizes.plane_bytes==0u) return false;
    constexpr std::array<std::uint32_t,9> scale{
        1u,1u,4u,1u,1u,4u,4u,4u,4u};
    // Slots 0,1: two ping-pong input/output full-plane buffers.
    // Slots 2...8: scratch groups, all distinct INSIDE one VitBlock.
    // 0 input/out, 1 output/input, 2 hidden, 3 ffwd, 4 attention,
    // 5 scratch, 6 query, 7 key, 8 value.
    constexpr std::array<std::uint32_t,kVitFieldCount> base_slots{
        0u,2u,3u,4u,1u,5u,6u,7u,8u};
    // 2 IO planes + (4 hidden + 1 ffwd + 1 attention + 4 scratch
    // + 4 Q + 4 K + 4 V) = 24 planes, versus 185 as now requested.
    const std::array<std::uint32_t,9> byte_factors{
        1u,1u,4u,1u,1u,4u,4u,4u,4u};
    VitReuseCandidate candidate{};
    candidate.baseline_requested_bytes=sizes.requested_bytes;
    std::uint64_t total=0u;
    for(std::size_t i=0u;i<candidate.pool_slots.size();++i) {
        if(sizes.plane_bytes>std::numeric_limits<std::uint64_t>::max()/
           byte_factors[i])return false;
        const auto b=sizes.plane_bytes*byte_factors[i];
        if(total>std::numeric_limits<std::uint64_t>::max()-b)return false;
        candidate.pool_slots[i]={static_cast<std::uint32_t>(i),b};
        total+=b;
    }
    candidate.candidate_requested_bytes=total;
    if(total>=sizes.requested_bytes)return false;
    candidate.nominal_difference_bytes=sizes.requested_bytes-total;
    candidate.blocks.reserve(sizes.vit_blocks);
    for(std::uint32_t i=0;i<sizes.vit_blocks;++i) {
        VitAliasedBlock b{};
        b.slots=base_slots;
        b.slots[static_cast<std::size_t>(VitField::Input)]=i%2u;
        b.slots[static_cast<std::size_t>(VitField::Output)]=(i+1u)%2u;
        // Mirrors strict within-block nonaliasing in CanOwnVitBuffers().
        for(std::size_t a=0u;a<kVitFieldCount;++a)
            for(std::size_t d=0u;d<a;++d)
                if(b.slots[a]==b.slots[d])return false;
        if(!candidate.blocks.empty() &&
           candidate.blocks.back().slots[static_cast<std::size_t>(VitField::Output)]!=
           b.slots[static_cast<std::size_t>(VitField::Input)])
            return false;
        candidate.blocks.push_back(b);
    }
    candidate.in_block_distinct=true;
    candidate.previous_output_matches_next_input=true;
    // A graph of nominal aliases is NOT GPU-safe automatically. The Vulkan
    // queue must execute every recorded block in order with explicit memory
    // barriers between all buffer writes/reads, plus a completed end fence
    // before recycling across sessions/frames. Neither proof exists here.
    candidate.gpu_barriers_proven=false;
    candidate.gpu_fences_proven=false;
    candidate.runnable=false;
    out=std::move(candidate);
    return true;
}
} // namespace Eden::Graphics::DlssNrMin
