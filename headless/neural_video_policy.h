// SPDX-License-Identifier: GPL-3.0-or-later
// One selectable Neural Rendering mode per game: three A4K + two DLSS-NR.
// Upscaling and frame generation remain separate, exclusive controls.
#pragma once
namespace Eden::NeuralVideo {
inline constexpr bool kRuntimeValidated=false; // DLSS-NR PS5 image execution, not menu selection.
inline constexpr int kOff=0;
inline constexpr int kA4kDetail=1;
inline constexpr int kA4kSoft=2;
inline constexpr int kA4kDenoise=3;
inline constexpr int kDlssOriginal=4;
inline constexpr int kDlssCompact=5;
inline constexpr int kRdna2=kDlssOriginal; // legacy call-site alias
inline constexpr int kModeCount=6;
enum class Reason {
    Available,Disabled,EngineIncomplete,RequiresVulkan,
    NeedsExclusiveUpscaler,MsaaUnverified,FrameGenerationUnverified
};
[[nodiscard]] constexpr bool IsA4k(int mode) noexcept {
    return mode>=kA4kDetail&&mode<=kA4kDenoise;
}
[[nodiscard]] constexpr bool IsDlss(int mode) noexcept {
    return mode==kDlssOriginal||mode==kDlssCompact;
}
[[nodiscard]] constexpr bool IsA4kFilter(int value) noexcept {
    return value>=7&&value<=9; // legacy internal Vulkan presenter IDs
}
[[nodiscard]] constexpr int InternalA4kFilter(int mode) noexcept {
    return IsA4k(mode)?mode+6:-1; // NR A4K 1/2/3 -> internal shader 7/8/9
}
[[nodiscard]] constexpr int ModeFromLegacyA4kFilter(int filter) noexcept {
    return IsA4kFilter(filter)?filter-6:kOff;
}
[[nodiscard]] constexpr int DlssModelIndex(int mode) noexcept {
    return mode==kDlssOriginal?0:mode==kDlssCompact?1:-1;
}
[[nodiscard]] constexpr bool HasStrength(int mode) noexcept {
    return IsDlss(mode);
}
[[nodiscard]] constexpr Reason Check(
    int mode,int renderer,int upscaling,int aa,int framegen,
    bool runtime_validated=kRuntimeValidated) noexcept {
    if(mode==kOff)return Reason::Disabled;
    if(!IsA4k(mode)&&!IsDlss(mode))return Reason::EngineIncomplete;
    if(renderer!=1)return Reason::RequiresVulkan;
    // Conservative until specific image composition is proven.
    if(upscaling!=0)return Reason::NeedsExclusiveUpscaler;
    if(aa<0||aa>3)return Reason::MsaaUnverified;
    if(framegen!=0)return Reason::FrameGenerationUnverified;
    if(IsDlss(mode)&&!runtime_validated)return Reason::EngineIncomplete;
    return Reason::Available;
}
[[nodiscard]] constexpr Reason CheckSelectable(
    int mode,int renderer,int filter,int aa,int fg) noexcept {
    return Check(mode,renderer,filter,aa,fg,true);
}
[[nodiscard]] constexpr bool CanSelect(
    int mode,int renderer,int filter,int aa,int fg) noexcept {
    return CheckSelectable(mode,renderer,filter,aa,fg)==Reason::Available;
}
[[nodiscard]] constexpr bool CanEnable(
    int renderer,int filter,int aa,int fg,
    bool validated=kRuntimeValidated) noexcept {
    return Check(kDlssOriginal,renderer,filter,aa,fg,validated)==Reason::Available;
}
[[nodiscard]] constexpr bool RuntimeParametersEnabled(
    int mode,bool validated=kRuntimeValidated) noexcept {
    return IsA4k(mode)||(IsDlss(mode)&&validated);
}
[[nodiscard]] constexpr bool FramegenMethodSelectable(
    int method,int renderer,int mode,bool has_lossless) noexcept {
    return method>=0&&method<=3&&
        (method==0||(renderer==1&&mode==kOff&&(method!=3||has_lossless)));
}
[[nodiscard]] constexpr bool UpscaleSelectable(
    int filter,int renderer,int mode) noexcept {
    if(filter<0||filter>6||(filter>=5&&renderer!=1))return false;
    return mode==kOff||filter==0;
}
[[nodiscard]] constexpr bool AntiAliasingSelectable(
    int aa,int renderer,int mode) noexcept {
    return aa>=0&&aa<=7&&(aa<=3||renderer==1)&&
           (mode==kOff||aa<=3);
}
[[nodiscard]] constexpr bool PresetsMayBeStored(int model,int strength) noexcept {
    return model>=0&&model<=1&&strength>=0&&strength<=100;
}
} // namespace Eden::NeuralVideo
