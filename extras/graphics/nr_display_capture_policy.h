// SPDX-License-Identifier: MIT
// R09: accept only an actual, full-frame model-resolution sampled texture.
// The GPU texture cache may return a scaled view of a smaller guest image.
// Its view is already sampled in GENERAL by the existing Vulkan presenter.
#pragma once
#include <cstdint>
namespace Eden::Graphics {
struct NRDisplayCapture {
    bool accelerated{},live_image{};
    std::uint32_t native_width{},native_height{};
    std::uint32_t sampled_width{},sampled_height{};
    float crop_left{},crop_top{},crop_right{},crop_bottom{};
};
[[nodiscard]] constexpr bool CanR09CaptureDisplay(
    NRDisplayCapture s) noexcept {
    constexpr std::uint32_t model_width=1920u,model_height=1080u;
    if(!s.live_image||!s.native_width||!s.native_height||
       s.native_width>16384u||s.native_height>16384u||
       s.sampled_width!=model_width||s.sampled_height!=model_height||
       s.crop_left!=0.0f||s.crop_top!=0.0f||
       s.crop_right!=1.0f||s.crop_bottom!=1.0f)return false;
    // Raw uploads always use the guest framebuffer's own extent.
    // Accelerated views may have been resolution-scaled to the exact
    // 1920x1080 physical image and need not have 1080p guest dimensions.
    if(!s.accelerated &&
       (s.native_width!=model_width||
        s.native_height!=model_height))return false;
    return true;
}
} // namespace Eden::Graphics
