// SPDX-License-Identifier: GPL-3.0-or-later
// Generic measured-path selector for ALREADY QUALIFIED R09 recipes.
// Does not create Vulkan work, reorder AA/FG, estimate imaginary FPS,
// infer missing GPU timings or enable the PS5 runtime.
#pragma once
#include "neural_pipeline_recipe.h"
#include <array>
#include <cstddef>
#include <cstdint>
namespace Eden::Graphics::PipelineComposer {

[[nodiscard]] constexpr bool SameRecipe(const Recipe& a,
                                         const Recipe& b) noexcept {
    if(a.version!=b.version || a.source_extent!=b.source_extent ||
       a.source_raster_aa!=b.source_raster_aa ||
       a.count!=b.count || a.count>kMaxSteps) return false;
    for(std::size_t i=0;i<a.count;++i) {
        const auto& x=a.stages[i];
        const auto& y=b.stages[i];
        if(x.kind!=y.kind||x.method!=y.method||x.output!=y.output||
           x.processes_real_and_generated!=y.processes_real_and_generated)
            return false;
    }
    return true;
}

// The resolution and Hz of a TV are independent of shader order and game
// source FPS. This selector is deliberately restricted to ONE display
// raster and independent runtime measurements. Never add modeled "FPS".
struct MeasuredBudget {
    Extent display_extent{};
    std::uint64_t gpu_frame_budget_ns{};
    std::uint64_t gpu_memory_budget_bytes{};
};

struct MeasuredCandidate {
    const Recipe* recipe{};
    const Bindings* native{};
    std::uint64_t measured_gpu_frame_ns{};
    std::uint64_t measured_gpu_peak_bytes{};
    bool physical_ps5_measurement{};
    bool per_stage_gpu_trace_complete{};
    bool output_image_quality_ab_accepted{};
    bool presentation_and_fallback_verified{};
};

enum class SelectionReason : std::uint8_t {
    InvalidBudget,NoVerifiedCandidate,ResearchWinnerOnly
};
struct Selection {
    SelectionReason reason{SelectionReason::NoVerifiedCandidate};
    std::size_t index{};
    std::size_t valid_candidates{},duplicate_recipes{};
    std::uint64_t measured_gpu_frame_ns{},measured_gpu_peak_bytes{};
    bool ps5_runtime_enabled{};  // ALWAYS false until actual renderer wired
};

// No automatic reordering: different AA positions can change picture
// quality and HUD history. Caller supplies alternatives with real A/B
// captures and measurements; the fastest admissible one wins.
template<std::size_t N>
[[nodiscard]] constexpr Selection SelectMeasuredPath(
    const std::array<MeasuredCandidate,N>& candidates,
    MeasuredBudget budget) noexcept {
    Selection best{};
    best.index=N;
    if(!ValidExtent(budget.display_extent)||
       !budget.gpu_frame_budget_ns||!budget.gpu_memory_budget_bytes){
        best.reason=SelectionReason::InvalidBudget;return best;
    }
    std::array<std::size_t,N> previously_seen{};
    std::size_t seen_count=0;
    for(std::size_t i=0;i<N;++i){
        const auto& c=candidates[i];
        if(!c.recipe||!c.native||
           !c.physical_ps5_measurement||
           !c.per_stage_gpu_trace_complete||
           !c.output_image_quality_ab_accepted||
           !c.presentation_and_fallback_verified||
           !c.measured_gpu_frame_ns||!c.measured_gpu_peak_bytes||
           c.measured_gpu_frame_ns>budget.gpu_frame_budget_ns||
           c.measured_gpu_peak_bytes>budget.gpu_memory_budget_bytes)
            continue;
        const auto qualification=QualifyBoundRecipe(*c.recipe,*c.native);
        if(qualification.reason!=Reason::HostCandidateOnly||
           !qualification.shape_qualified||
           qualification.runtime_enabled||
           qualification.result!=budget.display_extent)
            continue;
        bool duplicate=false;
        for(std::size_t j=0;j<seen_count;++j){
            if(SameRecipe(*c.recipe,*candidates[previously_seen[j]].recipe)){
                duplicate=true;break;
            }
        }
        if(duplicate){++best.duplicate_recipes;continue;}
        previously_seen[seen_count++]=i;
        ++best.valid_candidates;
        if(best.reason!=SelectionReason::ResearchWinnerOnly||
           c.measured_gpu_frame_ns<best.measured_gpu_frame_ns||
           (c.measured_gpu_frame_ns==best.measured_gpu_frame_ns&&
            c.measured_gpu_peak_bytes<best.measured_gpu_peak_bytes)){
            best.index=i;
            best.reason=SelectionReason::ResearchWinnerOnly;
            best.measured_gpu_frame_ns=c.measured_gpu_frame_ns;
            best.measured_gpu_peak_bytes=c.measured_gpu_peak_bytes;
        }
    }
    return best;
}
} // namespace Eden::Graphics::PipelineComposer
