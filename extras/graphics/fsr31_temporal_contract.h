// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
// R07 — strict generic input contract for a REAL FSR3.1 temporal upscaler.
//
// This contract is independent of guest game IDs and is kept separate from
// native PresentManager/FSR3 optical-flow frame generation. It must not turn
// guessed depth or motion into "verified" evidence. It is NOT an upscaler.
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>

namespace Eden::Graphics::Temporal {
enum class Producer : std::uint8_t {
    None, GuessedFromPresentation, GuestGpuVerified,
};
enum class DepthConvention : std::uint8_t { Unknown, Forward, Reversed };
enum class MotionConvention : std::uint8_t {
    Unknown, PixelOffsetToPreviousFrame, NormalizedOffsetToPreviousFrame,
};
enum class Rejection : std::uint8_t {
    None, MissingFrame, MissingResource, UntrustedProvenance, MixedFrame,
    MissingMotionConvention, MissingDepthConvention, MissingHudSeparation,
    InvalidResolution, InvalidJitter, InvalidMotionScale, InvalidTiming,
    MissingGpuCompletion, NonConsecutiveFrame, SceneChanged,
    InvalidProjection, InvalidVulkanImageLayout, InvalidSharpening, UnsupportedDevice,
    UnsupportedDepthConvention, UnsupportedMotionConvention,
    UnsupportedInputFormat, InsufficientMemoryBudget, MismatchedNativeResource, NativeBackendFailure,
    OutputAliasesInput,
};

// A non-owning identity. The real backend will convert these into actual
// VkImage/VkImageView and must keep them resident until the scheduler tick is
// finished. Zero means missing. No conversion to pointers in these tests.
struct Resource {
    std::uint64_t image{};
    std::uint64_t view{};
    std::uint64_t frame_id{};
    std::uint64_t scene_id{};
    Producer producer{Producer::None};
};
struct Inputs {
    Resource scene_color;
    Resource depth;
    Resource motion;
    std::uint32_t render_width{};
    std::uint32_t render_height{};
    std::uint32_t output_width{};
    std::uint32_t output_height{};
    DepthConvention depth_convention{DepthConvention::Unknown};
    MotionConvention motion_convention{MotionConvention::Unknown};
    std::array<float,2> jitter{};
    std::array<float,2> motion_scale{};
    std::array<float,4> depth_to_view{};
    float tan_half_fov{};
    float elapsed_ms{};
    bool native_hud_is_separate{};
    bool guest_hud_is_separate{};
    bool captured_gpu_work_complete{};
    bool vulkan_inputs_in_general_layout{};
};
[[nodiscard]] inline Rejection Validate(const Inputs& f) noexcept {
    if (!f.scene_color.frame_id || !f.scene_color.scene_id)
        return Rejection::MissingFrame;
    for (const Resource* r : {&f.scene_color,&f.depth,&f.motion}) {
        if (!r->image || !r->view) return Rejection::MissingResource;
        if (r->producer != Producer::GuestGpuVerified)
            return Rejection::UntrustedProvenance;
        if (r->frame_id != f.scene_color.frame_id ||
            r->scene_id != f.scene_color.scene_id)
            return Rejection::MixedFrame;
    }
    if (f.depth_convention == DepthConvention::Unknown)
        return Rejection::MissingDepthConvention;
    if (f.depth_convention != DepthConvention::Reversed)
        return Rejection::UnsupportedDepthConvention;
    if (f.motion_convention == MotionConvention::Unknown)
        return Rejection::MissingMotionConvention;
    if (f.motion_convention != MotionConvention::PixelOffsetToPreviousFrame)
        return Rejection::UnsupportedMotionConvention;
    if (!f.native_hud_is_separate || !f.guest_hud_is_separate)
        return Rejection::MissingHudSeparation;
    if (f.render_width < 64 || f.render_height < 64 ||
        f.output_width < 64 || f.output_height < 64 || f.render_width>8192 || f.render_height>8192 ||
        f.output_width>8192 || f.output_height>8192 ||
        f.output_width < f.render_width ||
        f.output_height < f.render_height ||
        f.output_width > 3ULL * f.render_width ||
        f.output_height > 3ULL * f.render_height)
        return Rejection::InvalidResolution;
    for (const auto j : f.jitter)
        if (!std::isfinite(j) || std::abs(j)>1.0f)
            return Rejection::InvalidJitter;
    for (const auto s : f.motion_scale)
        if (!std::isfinite(s) || s<=0.0f || s>8192.0f)
            return Rejection::InvalidMotionScale;
    for (float parameter : f.depth_to_view)
        if (!std::isfinite(parameter))
            return Rejection::InvalidProjection;
    if (!std::isfinite(f.tan_half_fov) || f.tan_half_fov<=0.0f ||
        f.tan_half_fov>100.0f || f.depth_to_view[1] <= 0.0f ||
        f.depth_to_view[3] <= 0.0f)
        return Rejection::InvalidProjection;
    if (!std::isfinite(f.elapsed_ms) || f.elapsed_ms<=0.0f ||
        f.elapsed_ms>250.0f)
        return Rejection::InvalidTiming;
    if (!f.vulkan_inputs_in_general_layout)
        return Rejection::InvalidVulkanImageLayout;
    if (!f.captured_gpu_work_complete)
        return Rejection::MissingGpuCompletion;
    return Rejection::None;
}

// History must reset whenever a source frame is skipped, a scene changes,
// resource resolution changes, or the input contract is not satisfied.
// The backend is responsible for shader dispatch and true GPU synchronization.
class FrameContinuity {
public:
    [[nodiscard]] Rejection Observe(const Inputs& inputs) noexcept {
        const Rejection valid=Validate(inputs);
        if (valid!=Rejection::None) {
            Reset();
            return valid;
        }
        const auto frame_id=inputs.scene_color.frame_id;
        const auto scene_id=inputs.scene_color.scene_id;
        const bool has_previous=last_frame_!=0;
        const bool scene_changed=has_previous && scene_id!=scene_;
        const bool not_consecutive=has_previous &&
            (frame_id<=last_frame_ || frame_id-last_frame_!=1);
        const bool size_changed=has_previous &&
            (width_!=inputs.render_width || height_!=inputs.render_height ||
             output_width_!=inputs.output_width ||
             output_height_!=inputs.output_height);
        last_frame_=frame_id;
        scene_=scene_id;
        width_=inputs.render_width;
        height_=inputs.render_height;
        output_width_=inputs.output_width;
        output_height_=inputs.output_height;
        if (scene_changed || size_changed) return Rejection::SceneChanged;
        if (not_consecutive) return Rejection::NonConsecutiveFrame;
        return Rejection::None;
    }
    void Reset() noexcept {
        last_frame_=scene_=0;
        width_=height_=output_width_=output_height_=0;
    }
private:
    std::uint64_t last_frame_{};
    std::uint64_t scene_{};
    std::uint32_t width_{},height_{},output_width_{},output_height_{};
};
} // namespace Eden::Graphics::Temporal
