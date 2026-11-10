// SPDX-License-Identifier: GPL-3.0-or-later
// Host-only Vit GPU requested-buffer byte accounting from the exact
// NrRdna2FrameSession::State::MakeVitBuffers() implementation in pinned
// vendor/encore-active/eden-vulkan/nr_rdna2_frame_session.cpp.
// NOT a VRAM residency measurement, an allocation guard or a pooling plan.
// No GPU buffers are created and no runtime behavior is changed.
#pragma once
#include "dlss_nr_min_graph_geometry.h"
#include <cstdint>
#include <limits>
#include <string_view>
#include <vector>

namespace Eden::Graphics::DlssNrMin {
enum class VitAuditIssue : std::uint8_t {
    None, GraphRejected, MissingVit, UnexpectedVitOrder,
    InconsistentTokens, ArithmeticOverflow
};
struct VitMemoryAudit {
    VitAuditIssue issue{VitAuditIssue::None};
    std::uint32_t vit_blocks{},vit_rows{},tokens{};
    std::uint32_t requested_buffers{};
    std::uint64_t plane_bytes{},requested_bytes{};
    bool runtime_qualified{};
};
[[nodiscard]] inline bool AuditVitRequestedBufferBytes(
    std::string_view native_plan, Extent raster, VitMemoryAudit& result) {
    result={};
    GeometryAudit geometry{};
    if(!AuditNativeR09Candidate(native_plan,raster,geometry)) {
        result.issue=VitAuditIssue::GraphRejected;
        return false;
    }
    std::vector<NR::NativePlanStep> rows{};
    if(NR::ParseNativePlan(native_plan,rows)!=NR::NativePlanError::Ok ||
       rows.size()!=geometry.rows.size()) {
        result.issue=VitAuditIssue::GraphRejected;
        return false;
    }
    constexpr NR::NativeNrOp order[]{
        NR::NativeNrOp::VitFfwdExpand,
        NR::NativeNrOp::VitFfwdContract,
        NR::NativeNrOp::VitQkv,
        NR::NativeNrOp::VitAttention,
        NR::NativeNrOp::VitProjection
    };
    VitMemoryAudit audit{};
    std::uint32_t prior=std::numeric_limits<std::uint32_t>::max();
    std::uint32_t next=0u;
    for(std::size_t i=0;i<rows.size();++i) {
        const auto type=NR::ClassifyNativeNrOp(rows[i]);
        if(!NR::IsNativeNrVitOp(type))continue;
        if(rows[i].block!=prior) {
            if(prior!=std::numeric_limits<std::uint32_t>::max() &&
               next!=5u) {
                result.issue=VitAuditIssue::UnexpectedVitOrder;
                return false;
            }
            prior=rows[i].block;
            next=0u;
            ++audit.vit_blocks;
        }
        if(next>=5u || type!=order[next]) {
            result.issue=VitAuditIssue::UnexpectedVitOrder;
            return false;
        }
        ++next;
        ++audit.vit_rows;
        const auto tokens=geometry.rows[i].padded_tokens;
        if(tokens==0u || tokens>std::numeric_limits<std::uint32_t>::max() ||
           (audit.tokens!=0u && audit.tokens!=tokens)) {
            result.issue=VitAuditIssue::InconsistentTokens;
            return false;
        }
        audit.tokens=static_cast<std::uint32_t>(tokens);
    }
    if(audit.vit_blocks!=8u || audit.vit_rows!=40u || next!=5u ||
       audit.tokens==0u) {
        result.issue=VitAuditIssue::MissingVit;
        return false;
    }
    // MakeVitBuffers allocates exactly 1 input plane for first block,
    // then 8 buffers per block (each block's input aliases the preceding
    // block's output):
    // hidden x4, ffwd x1, attention_context x1, output x1, scratch x4,
    // query x4, key x4, value x4 = 23 planes per block.
    // 1 + 8*23 = 185 reference planes, 1 + 8*8 = 65 buffers.
    constexpr std::uint64_t planes_per_block=23u;
    constexpr std::uint32_t buffers_per_block=8u;
    const auto plane=std::uint64_t(audit.tokens)*1024u;
    const auto total_planes=1u+
        std::uint64_t(audit.vit_blocks)*planes_per_block;
    if(plane>std::numeric_limits<std::uint64_t>::max()/total_planes) {
        result.issue=VitAuditIssue::ArithmeticOverflow;
        return false;
    }
    audit.plane_bytes=plane;
    audit.requested_bytes=plane*total_planes;
    audit.requested_buffers=1u+audit.vit_blocks*buffers_per_block;
    audit.runtime_qualified=false; // no VMA/alias barriers/fences measured
    result=audit;
    return true;
}
} // namespace Eden::Graphics::DlssNrMin
