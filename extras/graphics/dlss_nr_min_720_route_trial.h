// SPDX-License-Identifier: GPL-3.0-or-later
// Fail-closed CPU-only R09 Min native 720p structural route candidate.
// This is NOT an executable GPU plan, weight-model port or PS5 feature.
#pragma once
#include "dlss_nr_min_graph_geometry.h"
#include "rdna2_nr_split_native_routes_policy.h"
#include "rdna2_nr_vit_native_route_policy.h"
#include "video_core/renderer_vulkan/nr_rdna2_unet_skip_map.h"
#include <cstddef>
#include <cstdint>
#include <string_view>
#include <utility>
#include <vector>
namespace Eden::Graphics::DlssNrMin {
enum class Route720Issue : std::uint8_t {
    None, Geometry, Parse, Schedule, UNet, Split, ViT, FSwin,
    Bottleneck, MissingSpecializedProof
};
struct Route720Trial {
    Route720Issue issue{Route720Issue::None};
    std::vector<NR::NativePlanStep> rows{};
    NR::NativeNrSchedule schedule{};
    NR::NativeUNetSkipMap skips{};
    NR::NativeSplitRoutes split{};
    NR::NativeVitRoute vit{};
    std::uint32_t fswin_segments{},mapped_fswin_dispatches{};
    std::uint32_t mapped_split_dispatches{},unqualified_specialized{};
    std::uint32_t padded_vit_tokens{},logical_vit_tokens{};
    bool gpu_dispatch_qualified{false},ready_to_enable_720p{false};
};
[[nodiscard]] inline bool BuildR09Min720Routes(
    std::string_view original_plan,Route720Trial& result) {
    result={};
    GeometryAudit geometry{};
    if(!AuditNativeR09Candidate(original_plan,kCandidateMinRaster,geometry)) {
        result.issue=Route720Issue::Geometry;return false;
    }
    std::vector<NR::NativePlanStep> rows;
    if(NR::ParseNativePlan(original_plan,rows)!=NR::NativePlanError::Ok ||
       rows.size()!=geometry.rows.size()) {
        result.issue=Route720Issue::Parse;return false;
    }
    Route720Trial draft{};
    for(std::size_t i=0;i<rows.size();++i) {
        auto& s=rows[i];
        const auto& g=geometry.rows[i];
        const auto op=NR::ClassifyNativeNrOp(s);
        const auto oldwx=Ceil8(s.height),oldwy=Ceil8(s.width);
        if(!oldwx||!oldwy) {
            result.issue=Route720Issue::Schedule;return false;
        }
        const auto oldgx=s.grid_x,oldgy=s.grid_y;
        s.width=g.width;s.height=g.height;s.tokens=g.padded_tokens;
        if(g.fswin){
            // Learned upsample dispatch runs over PREVIOUS level windows.
            s.grid_x=g.input_dispatch_x;s.grid_y=g.input_dispatch_y;
            ++draft.mapped_fswin_dispatches;
        } else if(op==NR::NativeNrOp::PreImage ||
                  op==NR::NativeNrOp::PostImage) {
            s.grid_x=Ceil8(kCandidateMinRaster.height);
            s.grid_y=Ceil8(kCandidateMinRaster.width);
        } else if(NR::IsNativeNrSplitOp(op)) {
            // Per-op dispatch-X multiplier is preserved from reference.
            if(oldgx%oldwx!=0u || oldgy!=oldwy) {
                result.issue=Route720Issue::Split;return false;
            }
            const auto ratio=oldgx/oldwx;
            if(ratio==0u||ratio>16u){
                result.issue=Route720Issue::Split;return false;
            }
            s.grid_x=g.canonical_windows_x*ratio;
            s.grid_y=g.canonical_windows_y;
            ++draft.mapped_split_dispatches;
        } else {
            // The ViT and decoder need independent learned launch/buffer
            // adapter proof: DO NOT re-use the unchanged grid on a GPU.
            ++draft.unqualified_specialized;
        }
    }
    if(NR::BuildNativeNrSchedule(rows,draft.schedule)!=
       NR::NativeNrGraphError::Ok) {
        result.issue=Route720Issue::Schedule;return false;
    }
    if(NR::BuildNativeUNetSkipMap(rows,draft.skips)!=
       NR::NativeUNetSkipError::Ok) {
        result.issue=Route720Issue::UNet;return false;
    }
    if(NR::BuildNativeSplitRoutes(rows,draft.split)!=
       NR::SplitNativeRoutesError::Ok) {
        result.issue=Route720Issue::Split;return false;
    }
    if(NR::BuildNativeVitRoute(rows,draft.vit)!=
       NR::NativeVitRouteError::Ok) {
        result.issue=Route720Issue::ViT;return false;
    }
    const auto sections=NR::ExtractNativeFSwinSegments(rows);
    if(sections.size()!=8u) {
        result.issue=Route720Issue::FSwin;return false;
    }
    for(const auto& section:sections)
        if(section.layers.empty()) {
            result.issue=Route720Issue::FSwin;return false;
        }
    draft.fswin_segments=static_cast<std::uint32_t>(sections.size());
    draft.padded_vit_tokens=draft.vit.tokens;
    draft.logical_vit_tokens=draft.vit.raster_width*draft.vit.raster_height;
    if(draft.skips.count!=4u||draft.split.run_count!=2u||
       draft.vit.count!=8u||draft.vit.tokens!=960u||
       draft.vit.raster_width!=22u||draft.vit.raster_height!=40u||
       draft.padded_vit_tokens<draft.logical_vit_tokens||
       draft.mapped_fswin_dispatches!=
           geometry.standard_fswin+geometry.upsample_fswin||
       draft.mapped_split_dispatches==0u||
       draft.unqualified_specialized==0u){
        result.issue=Route720Issue::Bottleneck;return false;
    }
    draft.rows=std::move(rows);
    // This is explicitly NOT a source for Vulkan command submission.
    draft.gpu_dispatch_qualified=false;
    draft.ready_to_enable_720p=false;
    result=std::move(draft);
    return true;
}
} // namespace Eden::Graphics::DlssNrMin
