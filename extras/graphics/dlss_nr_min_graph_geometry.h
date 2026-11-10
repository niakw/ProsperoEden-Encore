// SPDX-License-Identifier: GPL-3.0-or-later
// Host-only geometry *audit* for a candidate R09 Min model resolution.
// NEVER serialize these candidates into executable plans or Vulkan dispatches.
// See ENCORE_DLSS_NR_MIN_ISOLATED_BRANCH.md.
#pragma once
#include "dlss_nr_min_policy.h"
#include "video_core/renderer_vulkan/nr_rdna2_native_graph_schedule.h"
#include <cstdint>
#include <string_view>
#include <utility>
#include <vector>

namespace Eden::Graphics::DlssNrMin {
namespace NR = Eden::Graphics::NeuralRDNA2;
enum class GeometryIssue : std::uint8_t {
    None, UnsupportedRaster, InvalidReference, UnsupportedModelLength,
    InvalidNativeSchedule, ReferenceGeometryMismatch, Overflow
};
struct GeometryCandidate {
    std::uint32_t block{}, layer{}, divisor{};
    std::uint32_t width{}, height{};
    std::uint32_t canonical_windows_x{}, canonical_windows_y{};
    std::uint32_t input_dispatch_x{}, input_dispatch_y{};
    std::uint64_t padded_tokens{};
    bool fswin{false}, fswin_upsample{false};
    // Explicitly NOT enough to issue compute work. Specialized Split/ViT
    // and model-ABI dispatches still require independent native proofs.
    bool vulkan_dispatch_qualified{false};
};
struct GeometryAudit {
    GeometryIssue issue{GeometryIssue::None};
    Extent candidate_raster{};
    std::vector<GeometryCandidate> rows{};
    std::uint32_t standard_fswin{}, upsample_fswin{}, specialized{};
    std::uint64_t aggregate_padded_tokens{};
    bool complete_gpu_plan{false};
};
[[nodiscard]] constexpr std::uint32_t Ceil8(std::uint32_t n) noexcept {
    return n / 8u + (n % 8u != 0u ? 1u : 0u);
}
// The reference native plan has horizontal and vertical dimensions in the
// upstream order (1920,1080); the preflight raster swaps presentation axes.
[[nodiscard]] inline bool AuditNativeR09Candidate(
    std::string_view reference_plan, Extent raster, GeometryAudit& result) {
    result={};
    // Deliberate MIN trial scope; smaller/eccentric sizes are unsupported.
    if (!IsValid16x9(raster) || raster.width < 1280u ||
        raster.height < 720u || raster.width > kCurrentR09Graph.width ||
        raster.height > kCurrentR09Graph.height) {
        result.issue=GeometryIssue::UnsupportedRaster;
        return false;
    }
    std::vector<NR::NativePlanStep> native_rows{};
    if (NR::ParseNativePlan(reference_plan,native_rows) !=
        NR::NativePlanError::Ok) {
        result.issue=GeometryIssue::InvalidReference;
        return false;
    }
    if (native_rows.size()!=152u && native_rows.size()!=76u) {
        result.issue=GeometryIssue::UnsupportedModelLength;
        return false;
    }
    NR::NativeNrSchedule original_schedule{};
    if (NR::BuildNativeNrSchedule(native_rows,original_schedule)!=
        NR::NativeNrGraphError::Ok) {
        result.issue=GeometryIssue::InvalidNativeSchedule;
        return false;
    }
    GeometryAudit staged{};
    staged.candidate_raster=raster;
    staged.rows.reserve(native_rows.size());
    for (const auto& step : native_rows) {
        if (step.div==0u || step.div>32u ||
            step.width!=kCurrentR09Graph.width/step.div ||
            step.height!=kCurrentR09Graph.height/step.div) {
            result.issue=GeometryIssue::ReferenceGeometryMismatch;
            return false;
        }
        const bool pre=step.type.starts_with("CCTinlayoutFusedPreBlock");
        const bool up=step.type.starts_with("CCTinlayoutFusedSwin") &&
            step.kernel.ends_with("_upsample_fp8");
        const bool fswin=step.type.starts_with("CCTinlayoutFusedSwin");
        if(up && step.div<2u) {
            result.issue=GeometryIssue::ReferenceGeometryMismatch;
            return false;
        }
        const std::uint32_t ref_windows_x=Ceil8(step.height);
        const std::uint32_t ref_windows_y=Ceil8(step.width);
        const std::uint64_t ref_padded_tokens =
            pre ? std::uint64_t(step.width)*step.height :
            std::uint64_t(ref_windows_x)*ref_windows_y*64u;
        if(step.tokens!=ref_padded_tokens) {
            result.issue=GeometryIssue::ReferenceGeometryMismatch;
            return false;
        }
        if(fswin) {
            // A learned FSwin upsample dispatch works in the previous level's
            // larger window grid while the output has current-level tokens.
            // Failing to distinguish the two produces bogus 720p buffers.
            const auto ref_x=up?Ceil8(kCurrentR09Graph.height/(step.div/2u)):
                                ref_windows_x;
            const auto ref_y=up?Ceil8(kCurrentR09Graph.width/(step.div/2u)):
                                ref_windows_y;
            if(step.grid_x!=ref_x || step.grid_y!=ref_y) {
                result.issue=GeometryIssue::ReferenceGeometryMismatch;
                return false;
            }
        }
        const std::uint32_t width=raster.width/step.div;
        const std::uint32_t height=raster.height/step.div;
        if(!width || !height) {
            result.issue=GeometryIssue::UnsupportedRaster;
            return false;
        }
        const std::uint32_t windows_x=Ceil8(height);
        const std::uint32_t windows_y=Ceil8(width);
        const std::uint64_t tokens=
            pre?std::uint64_t(width)*height:
                std::uint64_t(windows_x)*windows_y*64u;
        if(tokens>0xffffffffull || staged.aggregate_padded_tokens>
            0xffffffffffffffffull-tokens) {
            result.issue=GeometryIssue::Overflow;
            return false;
        }
        GeometryCandidate candidate{};
        candidate.block=step.block;
        candidate.layer=step.layer;
        candidate.divisor=step.div;
        candidate.width=width;
        candidate.height=height;
        candidate.canonical_windows_x=windows_x;
        candidate.canonical_windows_y=windows_y;
        candidate.input_dispatch_x=up?
            Ceil8(raster.height/(step.div/2u)):windows_x;
        candidate.input_dispatch_y=up?
            Ceil8(raster.width/(step.div/2u)):windows_y;
        candidate.padded_tokens=tokens;
        candidate.fswin=fswin;
        candidate.fswin_upsample=up;
        // Never silently promote calculated coordinates into GPU dispatches.
        staged.rows.push_back(candidate);
        staged.aggregate_padded_tokens+=tokens;
        if(up)++staged.upsample_fswin;
        else if(fswin)++staged.standard_fswin;
        else ++staged.specialized;
    }
    if(staged.standard_fswin+staged.upsample_fswin+staged.specialized !=
       staged.rows.size() || staged.upsample_fswin!=4u) {
        result.issue=GeometryIssue::ReferenceGeometryMismatch;
        return false;
    }
    // Structural candidates only. The real output depends on proprietary
    // weights, learned transitions, and renderer-native Vulkan resource ABI.
    staged.complete_gpu_plan=false;
    result=std::move(staged);
    return true;
}
} // namespace Eden::Graphics::DlssNrMin
