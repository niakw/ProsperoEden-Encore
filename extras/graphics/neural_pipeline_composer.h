// SPDX-License-Identifier: GPL-3.0-or-later
// Research-only COMPOSABLE Vulkan video pipeline planner, not a PS5 renderer.
// Ordered stages may omit Neural, include multiple spatial passes, or insert
// frame generation after a real-frame composition. All provider IDs preserve
// the existing Encore menu values. No fake Vulkan work or PS5 activation.
#pragma once
#include <array>
#include <cstddef>
#include <cstdint>

namespace Eden::Graphics::PipelineComposer {

struct Extent {
    std::uint32_t width{},height{};
    [[nodiscard]] constexpr bool operator==(const Extent&) const = default;
};
enum class Kind : std::uint8_t {
    Neural,Spatial,ComposeRealFrame,FrameGeneration,Present
};
enum class Reason : std::uint8_t {
    HostCandidateOnly,EmptyOrTooMany,MissingInput,InvalidExtent,
    UnknownStageOrProvider,DuplicateNeural,DuplicateFramegen,
    NeuralAfterGeneration,NeuralInputNot720,NeuralOutputMismatch,
    SpatialShaderCannotDownscale,MissingNativeVkImageAndView,
    MissingQueueBarrierOrFence,FramegenRequiresComposedRealFrames,
    MissingHistoryHudProviderOrBudget,GeneratedFramesNotProcessed,
    InvalidPresentOrder,MissingPresent
};
inline constexpr bool kComposablePs5RuntimeQualified=false;
// Mode 1/2/3: maintained A4K CNN 2x; 4: Original 720p denoise;
// mode 5 (Compact) is deliberately excluded pending its own full GPU proof.
// Spatial 0/2/3/4 = native samplers, 1 = FSR1, 5/6 = SGSR/SGSR Edge.
// FG 1 = MihawkGen, 2 = FSR3 optical flow, 3 = LSFG user DLL.
struct Step {
    Kind kind{Kind::Spatial};
    int method{};
    Extent output{};
    // Opaque logical identifiers in the host planner, NOT VkImage handles.
    // Runtime must bind each to a genuine VkImage+VkImageView and owner.
    std::uint64_t image{},view{};
    bool native_gpu_pass_recorded{};
    bool compatible_queue{};
    bool producer_to_consumer_visible{};
    bool owner_retained_through_gpu_fence{};
    // Neural model and FG providers have separate independent evidence.
    bool trained_model_and_weights_verified{};
    bool two_distinct_composited_real_frames{};
    bool hud_history_safe{};
    bool native_fg_provider_verified{};
    bool measured_gpu_memory_and_time_budget{};
    // Required when a transform follows FG: it must transform EVERY real
    // and generated image at the same output extent, not only real frames.
    bool processes_real_and_generated{};
};
inline constexpr std::size_t kMaxSteps=12u;
struct Chain {
    Extent source_extent{1280u,720u};
    std::uint64_t source_image{1u},source_view{2u};
    std::array<Step,kMaxSteps> steps{};
    std::size_t count{};
};
struct Verdict {
    Reason reason{Reason::EmptyOrTooMany};
    std::size_t at{};
    Extent result{};
    std::uint32_t spatial_passes{};
    bool neural{},frame_generation{},has_real_composition{};
    bool processes_generated_stream{};
    bool shape_qualified{};
    bool runtime_enabled{};  // Always false in research.
};
[[nodiscard]] constexpr bool ValidExtent(Extent e) noexcept {
    // Crop/full-raster proof currently only covers aspect 16:9.
    return e.width>=320u&&e.height>=180u&&
           e.width<=3840u&&e.height<=2160u&&
           std::uint64_t(e.width)*9u==std::uint64_t(e.height)*16u;
}
[[nodiscard]] constexpr bool IsSpatial(int method) noexcept {
    return method>=0&&method<=6;
}
[[nodiscard]] constexpr bool IsNeural(int method) noexcept {
    return method>=1&&method<=4;
}
[[nodiscard]] constexpr bool IsFg(int method) noexcept {
    return method>=1&&method<=3;
}
[[nodiscard]] constexpr bool ShaderUpscaleOnly(int spatial) noexcept {
    return spatial==1||spatial==5||spatial==6;
}
// Treat the step's image ID as a distinct logical OUTPUT token only. Native
// samplers may be executed in the final compositor, but the real renderer
// still must supply the required final image+view identities and fences.
[[nodiscard]] constexpr Verdict Plan(const Chain& chain) noexcept {
    Verdict out{};
    out.result=chain.source_extent;
    if(!chain.count||chain.count>kMaxSteps)return out;
    if(!ValidExtent(chain.source_extent)) {
        out.reason=Reason::InvalidExtent;return out;
    }
    if(!chain.source_image||!chain.source_view||
       chain.source_image==chain.source_view) {
        out.reason=Reason::MissingInput;return out;
    }
    std::uint64_t current_image=chain.source_image;
    std::uint64_t current_view=chain.source_view;
    std::array<std::uint64_t,kMaxSteps+1u> prior_images{};
    std::array<std::uint64_t,kMaxSteps+1u> prior_views{};
    prior_images[0]=current_image;
    prior_views[0]=current_view;
    std::size_t owner_count=1u;
    bool presented=false,composed=false,generated=false;
    for(std::size_t i=0u;i<chain.count;++i){
        const auto& step=chain.steps[i];
        out.at=i;
        if(presented) {
            out.reason=Reason::InvalidPresentOrder;return out;
        }
        if(step.kind==Kind::Present){
            if(i+1u!=chain.count||step.image||step.view||
               step.output!=out.result) {
                out.reason=Reason::InvalidPresentOrder;return out;
            }
            presented=true;
            continue;
        }
        if(!ValidExtent(step.output)){
            out.reason=Reason::InvalidExtent;return out;
        }
        if(!step.image||!step.view||step.image==step.view ||
           step.image==current_image||step.view==current_view) {
            out.reason=Reason::MissingNativeVkImageAndView;return out;
        }
        // Conservative: do not alias ANY earlier intermediate until a
        // separate lifetime/barrier proof exists (particularly after FG).
        for(std::size_t j=0;j<owner_count;++j){
            if(step.image==prior_images[j]||step.view==prior_views[j]) {
                out.reason=Reason::MissingNativeVkImageAndView;return out;
            }
        }
        if(!step.native_gpu_pass_recorded||!step.compatible_queue||
           !step.producer_to_consumer_visible||
           !step.owner_retained_through_gpu_fence){
            out.reason=Reason::MissingQueueBarrierOrFence;return out;
        }
        switch(step.kind){
        case Kind::Neural:
            if(!IsNeural(step.method)||!step.trained_model_and_weights_verified){
                out.reason=Reason::UnknownStageOrProvider;return out;
            }
            if(out.neural){out.reason=Reason::DuplicateNeural;return out;}
            if(generated){out.reason=Reason::NeuralAfterGeneration;return out;}
            if(out.result!=Extent{1280u,720u}){
                out.reason=Reason::NeuralInputNot720;return out;
            }
            if(step.output!=(step.method<=3?Extent{2560u,1440u}:
                                           Extent{1280u,720u})){
                out.reason=Reason::NeuralOutputMismatch;return out;
            }
            out.neural=true;
            break;
        case Kind::Spatial:
            if(!IsSpatial(step.method)){
                out.reason=Reason::UnknownStageOrProvider;return out;
            }
            if(ShaderUpscaleOnly(step.method)&&
               (step.output.width<out.result.width||
                step.output.height<out.result.height)){
                out.reason=Reason::SpatialShaderCannotDownscale;return out;
            }
            if(generated&&!step.processes_real_and_generated){
                out.reason=Reason::GeneratedFramesNotProcessed;return out;
            }
            ++out.spatial_passes;
            break;
        case Kind::ComposeRealFrame:
            if(step.output!=out.result){
                out.reason=Reason::InvalidExtent;return out;
            }
            if(generated&&!step.processes_real_and_generated){
                out.reason=Reason::GeneratedFramesNotProcessed;return out;
            }
            composed=true;
            out.has_real_composition=true;
            break;
        case Kind::FrameGeneration:
            if(!IsFg(step.method)){
                out.reason=Reason::UnknownStageOrProvider;return out;
            }
            if(generated){out.reason=Reason::DuplicateFramegen;return out;}
            if(!composed){
                out.reason=Reason::FramegenRequiresComposedRealFrames;return out;
            }
            if(step.output!=out.result){
                out.reason=Reason::InvalidExtent;return out;
            }
            if(!step.two_distinct_composited_real_frames||
               !step.hud_history_safe||
               !step.native_fg_provider_verified||
               !step.measured_gpu_memory_and_time_budget){
                out.reason=Reason::MissingHistoryHudProviderOrBudget;return out;
            }
            generated=true;
            out.frame_generation=true;
            out.processes_generated_stream=true;
            break;
        default:
            out.reason=Reason::UnknownStageOrProvider;return out;
        }
        out.result=step.output;
        current_image=step.image;
        current_view=step.view;
        prior_images[owner_count]=current_image;
        prior_views[owner_count]=current_view;
        ++owner_count;
    }
    if(!presented) {
        out.at=chain.count;
        out.reason=Reason::MissingPresent;return out;
    }
    out.at=chain.count;
    out.reason=Reason::HostCandidateOnly;
    out.shape_qualified=true;
    out.runtime_enabled=kComposablePs5RuntimeQualified;
    return out;
}
} // namespace Eden::Graphics::PipelineComposer
