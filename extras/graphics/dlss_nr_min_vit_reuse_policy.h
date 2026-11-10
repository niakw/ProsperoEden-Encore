// SPDX-License-Identifier: GPL-3.0-or-later
// R09 Min: proposal-only ViT temporary-buffer reuse map.
// Based on the pinned vendor's eight serialized NrRdna2VitBlock::Record()
// invocations and MakeVitBuffers() allocation roles. This file DOES NOT
// change Vulkan allocations, record barriers, resource lifetime, or runtime.
// Cross-block aliases MUST NOT be enabled until driver+fence validation.
#pragma once
#include "dlss_nr_min_vit_memory_audit.h"
#include <array>
#include <cstdint>
#include <limits>

namespace Eden::Graphics::DlssNrMin {
inline constexpr std::uint32_t kVitBlocks=8u;
inline constexpr std::uint32_t kVitBufferRoles=9u;
inline constexpr std::uint32_t kVitReusePhysicalBuffers=9u;
inline constexpr std::uint32_t kVitReusePlanes=24u;
inline constexpr bool kVitReuseQualifiedForPs5=false;

enum class VitReuseReject : std::uint8_t {
    None, InvalidModel, InvalidGeometry, IntraBlockOverlap,
    BrokenInputOutputChain, MissingComputeBarrier,
    ConcurrentFrameOrQueue, MissingLiveRangeProof,
    NotQualifiedOnHardware
};
struct VitReuseBlock {
    // Every role within a block must own a DISTINCT buffer handle.
    // Only cross-block scratch buffers and ping-pong IO are shared.
    std::array<std::uint32_t,kVitBufferRoles> handle{};
    // handle roles: input, hidden, ffwd, attention, output, scratch,
    // query, key, value. 2 IO slots (0,1) and seven unique temp slots.
};
struct VitReuseProposal {
    VitReuseReject reason{VitReuseReject::None};
    std::array<VitReuseBlock,kVitBlocks> blocks{};
    std::uint32_t physical_buffers{};
    std::uint64_t plane_bytes{}, baseline_requested_bytes{},
                  candidate_requested_bytes{}, candidate_difference_bytes{};
    // ABI marker; never a claim that writes have a matching Vulkan barrier.
    bool is_non_executable_proposal{true};
};
[[nodiscard]] constexpr bool HasDistinctHandlesWithinBlock(
    const VitReuseBlock& block) noexcept {
    for (std::uint32_t i=0u;i<kVitBufferRoles;++i)
        for(std::uint32_t j=0u;j<i;++j)
            if(block.handle[i]==block.handle[j])return false;
    return true;
}
[[nodiscard]] constexpr bool IsValidVitReuseMap(
    const std::array<VitReuseBlock,kVitBlocks>& blocks) noexcept {
    for(std::uint32_t i=0;i<kVitBlocks;++i) {
        if(!HasDistinctHandlesWithinBlock(blocks[i]))return false;
        if(i && blocks[i].handle[0]!=blocks[i-1u].handle[4])
            return false;
        if(i && blocks[i].handle[4]==blocks[i-1u].handle[4])
            return false;
    }
    return true;
}
[[nodiscard]] inline bool MakeVitReuseProposal(
    std::string_view native_plan,Extent extent,VitReuseProposal& output) {
    output={};
    VitMemoryAudit measured_requests{};
    if(!AuditVitRequestedBufferBytes(native_plan,extent,measured_requests) ||
       measured_requests.vit_blocks!=kVitBlocks ||
       measured_requests.requested_buffers!=65u ||
       measured_requests.plane_bytes==0u) {
        output.reason=VitReuseReject::InvalidModel;
        return false;
    }
    if(measured_requests.plane_bytes>
       std::numeric_limits<std::uint64_t>::max()/kVitReusePlanes) {
        output.reason=VitReuseReject::InvalidGeometry;
        return false;
    }
    VitReuseProposal staged{};
    // Even blocks read from IO slot A and write B, odd blocks read B and
    // write A. Those IO buffers remain distinct within each block.
    // Temporary roles are logically shared across all eight blocks, but
    // ONLY if a compute->compute barrier ends each previous block.
    for(std::uint32_t i=0u;i<kVitBlocks;++i) {
        const auto in=i&1u;
        const auto out=1u-in;
        staged.blocks[i].handle={in,2u,3u,4u,out,5u,6u,7u,8u};
    }
    if(!IsValidVitReuseMap(staged.blocks)) {
        output.reason=VitReuseReject::IntraBlockOverlap;
        return false;
    }
    staged.physical_buffers=kVitReusePhysicalBuffers;
    staged.plane_bytes=measured_requests.plane_bytes;
    staged.baseline_requested_bytes=measured_requests.requested_bytes;
    staged.candidate_requested_bytes=measured_requests.plane_bytes*
                                     kVitReusePlanes;
    if(staged.baseline_requested_bytes<staged.candidate_requested_bytes) {
        output.reason=VitReuseReject::InvalidGeometry;
        return false;
    }
    staged.candidate_difference_bytes=staged.baseline_requested_bytes-
                                       staged.candidate_requested_bytes;
    output=staged;
    return true;
}
struct VitReuseEvidence {
    bool blocks_recorded_serially{};
    bool no_concurrent_frame_or_queue{};
    // One explicit SHADER_WRITE -> SHADER_READ|SHADER_WRITE compute barrier
    // must exist BETWEEN every pair of block records, on the same queue.
    std::array<bool,kVitBlocks-1u> compute_barrier_after_block{};
    bool no_external_consumer_of_temporary_buffers{};
    bool no_async_readback_of_shared_buffers{};
    bool no_live_descriptor_update_or_rebind_hazard{};
    bool positive_gpu_validation{};
    bool negative_gpu_validation{};
};
[[nodiscard]] constexpr VitReuseReject CheckVitReuseEvidence(
    const VitReuseProposal& p,const VitReuseEvidence& e) noexcept {
    if(p.reason!=VitReuseReject::None ||
       p.physical_buffers!=kVitReusePhysicalBuffers ||
       !IsValidVitReuseMap(p.blocks))
        return VitReuseReject::InvalidModel;
    if(!e.blocks_recorded_serially || !e.no_concurrent_frame_or_queue)
        return VitReuseReject::ConcurrentFrameOrQueue;
    for(const bool barrier:e.compute_barrier_after_block)
        if(!barrier)return VitReuseReject::MissingComputeBarrier;
    if(!e.no_external_consumer_of_temporary_buffers ||
       !e.no_async_readback_of_shared_buffers ||
       !e.no_live_descriptor_update_or_rebind_hazard)
        return VitReuseReject::MissingLiveRangeProof;
    if(!e.positive_gpu_validation || !e.negative_gpu_validation ||
       !kVitReuseQualifiedForPs5)
        return VitReuseReject::NotQualifiedOnHardware;
    return VitReuseReject::None;
}
} // namespace Eden::Graphics::DlssNrMin
