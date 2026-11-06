// SPDX-License-Identifier: GPL-3.0-or-later
// R09: one policy for Neural Rendering dependencies in settings and UI.
// This describes *supported* combinations, not performance recommendations.
// Do not change to true until BOTH models and image I/O are validated on PS5.
#pragma once
namespace Eden::NeuralVideo {
inline constexpr bool kRuntimeValidated = false;
inline constexpr int kOff = 0;
inline constexpr int kRdna2 = 1;
enum class Reason {
    Available, Disabled, EngineIncomplete, RequiresVulkan,
    NeedsExclusiveUpscaler, MsaaUnverified, FrameGenerationUnverified
};
[[nodiscard]] constexpr Reason Check(
    int mode, int renderer, int upscaling_filter, int anti_aliasing,
    int frame_generation, bool runtime_validated=kRuntimeValidated) noexcept {
    if(mode==kOff)return Reason::Disabled;
    if(mode!=kRdna2||!runtime_validated)return Reason::EngineIncomplete;
    if(renderer!=1)return Reason::RequiresVulkan;
    // Two reconstruction/upscale pipelines must not silently overwrite each
    // other's output. Lift only after the specific composition is validated.
    if(upscaling_filter!=0)return Reason::NeedsExclusiveUpscaler;
    // Post FXAA/SMAA may coexist, guest MSAA >1x is unqualified.
    if(anti_aliasing>=4)return Reason::MsaaUnverified;
    // NR and framegen are NOT inherently incompatible; this particular
    // PS5 implementation has not qualified the simultaneous pipeline.
    if(frame_generation!=0)return Reason::FrameGenerationUnverified;
    return Reason::Available;
}
[[nodiscard]] constexpr bool CanEnable(
    int renderer,int filter,int aa,int frame_generation,
    bool validated=kRuntimeValidated) noexcept {
    return Check(kRdna2,renderer,filter,aa,frame_generation,validated)==
           Reason::Available;
}
[[nodiscard]] constexpr bool RuntimeParametersEnabled(
    int mode,bool validated=kRuntimeValidated) noexcept {
    return mode==kRdna2 && validated;
}
// Preset storage remains editable even when mode=Off. This is *not*
// permission to execute a GPU graph or to show the active controls.
[[nodiscard]] constexpr bool PresetsMayBeStored(int model,int strength) noexcept {
    return (model>=0&&model<=1)&&(strength>=0&&strength<=100);
}
} // namespace Eden::NeuralVideo
