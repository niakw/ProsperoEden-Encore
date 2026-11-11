// SPDX-License-Identifier: GPL-3.0-or-later
// One selected A4K CNN (Detail/Soft/Denoise) plus a SEPARATE spatial
// filter. Preview describes future wiring; console activation is DENIED.
#pragma once
#include "neural_video_policy.h"
#include "dlss_nr_min_720_framegen_bridge.h"

namespace Eden::Graphics::DlssNrMin {
struct A4kSpatialLaunchRoute {
    int selected_neural{};
    int present_filter{};
    int downstream_framegen{};
    bool candidate{};
    bool combine_enabled{};
    bool needs_native_a4k_output_frame{};
};

// Used only for a guarded selection. The user preferences stay intact;
// the original A4K (internal 7/8/9) fallback remains in effect today.
[[nodiscard]] constexpr A4kSpatialLaunchRoute
ResolveA4kSpatialLaunch(int neural,int renderer,int spatial,int aa,
                        int framegen,bool legacy_selectable) noexcept {
    A4kSpatialLaunchRoute result{};
    result.selected_neural=neural;
    result.present_filter=spatial;
    result.downstream_framegen=0;
    const bool a4k=Eden::NeuralVideo::IsA4k(neural);
    if(!a4k){
        return result;
    }
    const bool candidate=renderer==1&&ValidSpatialFilter(spatial)&&
        aa==0&&framegen>=0&&framegen<=3;
    result.candidate=candidate;
    // Never allow the UI to request an unsupported combined runtime.
    // These are independent, FALSE evidence gates on this research branch.
    result.combine_enabled=candidate&&
        kA4kNeuralToSpatialRuntimeQualified&&
        kPostNeuralSpatialRuntimeWired&&
        (framegen==0||kNeuralToFramegenRuntimeWired);
    result.needs_native_a4k_output_frame=result.combine_enabled;
    if(result.combine_enabled) {
        result.downstream_framegen=framegen;
        // A4K remains the selected neural engine; user spatial filter
        // now stays 0-6, allowing FSR/SGSR or native sampler downstream.
        result.present_filter=spatial;
    }else if(legacy_selectable){
        // Old, already working 1-stage A4K behavior is unchanged.
        result.present_filter=Eden::NeuralVideo::InternalA4kFilter(neural);
    }
    return result;
}
} // namespace Eden::Graphics::DlssNrMin
