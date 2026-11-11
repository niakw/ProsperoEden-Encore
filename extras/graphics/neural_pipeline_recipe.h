// SPDX-License-Identifier: GPL-3.0-or-later
// Versioned ordered video stages, ready for future per-game profile storage.
// Builder never manufactures GPU resources/weights/proofs. Bind the ACTUAL
// Vulkan owner/fence evidence before calling PipelineComposer::Plan().
#pragma once
#include "neural_pipeline_composer.h"
#include <array>
#include <cstddef>
#include <cstdint>

namespace Eden::Graphics::PipelineComposer {

inline constexpr std::uint32_t kRecipeVersion=1u;
struct RecipeStage {
    Kind kind{Kind::Spatial};
    int method{};
    Extent output{};
    // Explicit when a later pass must transform ALL generated and real
    // surfaces rather than accidentally filtering just the real frame.
    bool processes_real_and_generated{};
};
struct Recipe {
    std::uint32_t version{kRecipeVersion};
    Extent source_extent{1280u,720u};
    std::array<RecipeStage,kMaxSteps> stages{};
    std::size_t count{};
};
[[nodiscard]] constexpr bool InsertStep(Recipe& r,std::size_t pos,
                                        RecipeStage step) noexcept {
    if(r.version!=kRecipeVersion||r.count>=kMaxSteps||pos>r.count)
        return false;
    for(std::size_t i=r.count;i>pos;--i)r.stages[i]=r.stages[i-1u];
    r.stages[pos]=step;
    ++r.count;
    return true;
}
[[nodiscard]] constexpr bool RemoveStep(Recipe& r,std::size_t pos) noexcept {
    if(r.version!=kRecipeVersion||pos>=r.count)return false;
    for(std::size_t i=pos+1u;i<r.count;++i)r.stages[i-1u]=r.stages[i];
    r.stages[r.count-1u]=RecipeStage{};
    --r.count;
    return true;
}
// Evidence is passed by the live native owner, never stored in the preset.
// A saved preset MUST NOT claim real VkImage handles or model credentials.
struct StageEvidence {
    std::uint64_t image{},view{};
    bool native_gpu_pass_recorded{};
    bool compatible_queue{};
    bool producer_to_consumer_visible{};
    bool owner_retained_through_gpu_fence{};
    bool trained_model_and_weights_verified{};
    bool two_distinct_composited_real_frames{};
    bool hud_history_safe{};
    bool native_fg_provider_verified{};
    bool measured_gpu_memory_and_time_budget{};
};
struct Bindings {
    std::uint64_t guest_image{},guest_view{};
    std::array<StageEvidence,kMaxSteps> stages{};
};
[[nodiscard]] constexpr bool BindRecipe(const Recipe& recipe,
                                        const Bindings& native,
                                        Chain& bound) noexcept {
    if(recipe.version!=kRecipeVersion||!recipe.count||
       recipe.count>kMaxSteps||!native.guest_image||!native.guest_view)
        return false;
    Chain result{};
    result.source_extent=recipe.source_extent;
    result.source_image=native.guest_image;
    result.source_view=native.guest_view;
    result.count=recipe.count;
    for(std::size_t i=0u;i<recipe.count;++i){
        const auto& spec=recipe.stages[i];
        const auto& proof=native.stages[i];
        Step s{};
        s.kind=spec.kind;
        s.method=spec.method;
        s.output=spec.output;
        if(spec.kind==Kind::Present) {
            // Terminal Present binds existing frame; it must not supply
            // a fabricated extra output resource.
            if(proof.image||proof.view)return false;
        }else{
            s.image=proof.image;s.view=proof.view;
        }
        s.processes_real_and_generated=
            spec.processes_real_and_generated;
        s.native_gpu_pass_recorded=proof.native_gpu_pass_recorded;
        s.compatible_queue=proof.compatible_queue;
        s.producer_to_consumer_visible=
            proof.producer_to_consumer_visible;
        s.owner_retained_through_gpu_fence=
            proof.owner_retained_through_gpu_fence;
        s.trained_model_and_weights_verified=
            proof.trained_model_and_weights_verified;
        s.two_distinct_composited_real_frames=
            proof.two_distinct_composited_real_frames;
        s.hud_history_safe=proof.hud_history_safe;
        s.native_fg_provider_verified=proof.native_fg_provider_verified;
        s.measured_gpu_memory_and_time_budget=
            proof.measured_gpu_memory_and_time_budget;
        result.steps[i]=s;
    }
    bound=result;
    return true;
}
[[nodiscard]] constexpr Verdict QualifyBoundRecipe(
    const Recipe& recipe,const Bindings& native) noexcept {
    Chain bound{};
    if(!BindRecipe(recipe,native,bound)) {
        Verdict out{};
        out.reason=Reason::MissingInput;
        return out;
    }
    return Plan(bound);
}
} // namespace Eden::Graphics::PipelineComposer
