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
#include <utility>
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


// Evidence required BEFORE considering a Vulkan implementation of the
// candidate. These fields are independent of successful host CPU tests.
// A green structural plan cannot turn these flags on by itself.
enum class VitReuseGate : std::uint8_t {
    InvalidCandidate,
    ConcurrentGpuUse,
    MissingInterBlockBarrier,
    MissingLifetimeProof,
    MissingGpuValidation,
    RuntimeHardDisabled
};
struct VitReuseEvidence {
    bool same_queue_serial_recording{};
    bool no_concurrent_frame_or_queue{};
    std::array<bool,7u> explicit_compute_write_to_read_write_barrier{};
    bool no_external_live_temporary_consumer{};
    bool no_early_release_or_async_readback{};
    bool descriptor_sets_immutable_until_fence{};
    bool per_frame_end_fence_completed{};
    bool positive_gpu_test{};
    bool negative_gpu_test{};
};
inline constexpr bool kVitReusePs5RuntimeEnabled=false;
[[nodiscard]] inline VitReuseGate CheckVitReuseAdmission(
    const VitReuseCandidate& plan,const VitReuseEvidence& evidence) noexcept {
    if(plan.blocks.size()!=8u || !plan.in_block_distinct ||
       !plan.previous_output_matches_next_input ||
       plan.candidate_requested_bytes==0u ||
       plan.candidate_requested_bytes>=plan.baseline_requested_bytes ||
       plan.pool_slots.size()!=9u)
        return VitReuseGate::InvalidCandidate;
    for(std::size_t i=0u;i<plan.blocks.size();++i) {
        const auto& slots=plan.blocks[i].slots;
        for(std::size_t role=0u;role<slots.size();++role) {
            if(slots[role]>=plan.pool_slots.size())
                return VitReuseGate::InvalidCandidate;
            for(std::size_t j=0u;j<role;++j)
                if(slots[role]==slots[j])
                    return VitReuseGate::InvalidCandidate;
        }
        if(i>0u && plan.blocks[i-1u].slots[
                static_cast<std::size_t>(VitField::Output)] !=
                       slots[static_cast<std::size_t>(VitField::Input)])
            return VitReuseGate::InvalidCandidate;
    }
    if(!evidence.same_queue_serial_recording ||
       !evidence.no_concurrent_frame_or_queue)
        return VitReuseGate::ConcurrentGpuUse;
    for(bool barrier:evidence.explicit_compute_write_to_read_write_barrier)
        if(!barrier) return VitReuseGate::MissingInterBlockBarrier;
    if(!evidence.no_external_live_temporary_consumer ||
       !evidence.no_early_release_or_async_readback ||
       !evidence.descriptor_sets_immutable_until_fence ||
       !evidence.per_frame_end_fence_completed)
        return VitReuseGate::MissingLifetimeProof;
    if(!evidence.positive_gpu_test || !evidence.negative_gpu_test)
        return VitReuseGate::MissingGpuValidation;
    // No PS5 renderer rebind/fence proof exists; cannot be overridden by
    // synthetic evidence. A separate qualified integration is required.
    return VitReuseGate::RuntimeHardDisabled;
}
} // namespace Eden::Graphics::DlssNrMin
