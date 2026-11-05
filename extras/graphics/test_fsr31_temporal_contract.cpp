// SPDX-License-Identifier: GPL-3.0-or-later
#include "fsr31_temporal_contract.h"
#include <cassert>
#include <limits>
using namespace Eden::Graphics::Temporal;

static Inputs Verified(std::uint64_t frame=1) {
    auto resource=[&](std::uint64_t handle) {
        return Resource{.image=handle,.view=handle+100,
                        .frame_id=frame,.scene_id=7,
                        .producer=Producer::GuestGpuVerified};
    };
    return {.scene_color=resource(1),.depth=resource(2),.motion=resource(3),
            .render_width=1280,.render_height=720,
            .output_width=1920,.output_height=1080,
            .depth_convention=DepthConvention::Reversed,
            .motion_convention=MotionConvention::PixelOffsetToPreviousFrame,
            .jitter={0.25f,-0.25f},.motion_scale={1.0f,1.0f},
            .depth_to_view={0.0f,0.1f,1.0f,1.0f},
            .tan_half_fov=0.577350f,
            .elapsed_ms=33.3f,.native_hud_is_separate=true,
            .guest_hud_is_separate=true,.captured_gpu_work_complete=true,
            .vulkan_inputs_in_general_layout=true};
}
int main() {
    auto f=Verified();
    assert(Validate(f)==Rejection::None);
    FrameContinuity sequence;
    assert(sequence.Observe(f)==Rejection::None);
    assert(sequence.Observe(Verified(2))==Rejection::None);
    assert(sequence.Observe(Verified(4))==Rejection::NonConsecutiveFrame);
    assert(sequence.Observe(Verified(5))==Rejection::None);
    f=Verified(6);f.scene_color.scene_id=9;
    f.depth.scene_id=f.motion.scene_id=9;
    assert(sequence.Observe(f)==Rejection::SceneChanged);
    f=Verified(7); f.scene_color.scene_id=f.motion.scene_id=f.depth.scene_id=9;
    assert(sequence.Observe(f)==Rejection::None);

    f=Verified(); f.motion={};
    assert(Validate(f)==Rejection::MissingResource);
    f=Verified(); f.motion.producer=Producer::GuessedFromPresentation;
    assert(Validate(f)==Rejection::UntrustedProvenance);
    f=Verified(); f.depth.frame_id=2;
    assert(Validate(f)==Rejection::MixedFrame);
    f=Verified(); f.motion.scene_id=8;
    assert(Validate(f)==Rejection::MixedFrame);
    f=Verified(); f.depth_convention=DepthConvention::Unknown;
    assert(Validate(f)==Rejection::MissingDepthConvention);
    f=Verified(); f.motion_convention=MotionConvention::Unknown;
    assert(Validate(f)==Rejection::MissingMotionConvention);
    f=Verified(); f.depth_convention=DepthConvention::Forward;
    assert(Validate(f)==Rejection::UnsupportedDepthConvention);
    f=Verified(); f.motion_convention=MotionConvention::NormalizedOffsetToPreviousFrame;
    assert(Validate(f)==Rejection::UnsupportedMotionConvention);
    f=Verified(); f.render_width=1;
    assert(Validate(f)==Rejection::InvalidResolution);
    f=Verified(); f.guest_hud_is_separate=false;
    assert(Validate(f)==Rejection::MissingHudSeparation);
    f=Verified(); f.render_width=4000;
    assert(Validate(f)==Rejection::InvalidResolution);
    f=Verified(); f.jitter[0]=std::numeric_limits<float>::quiet_NaN();
    assert(Validate(f)==Rejection::InvalidJitter);
    f=Verified(); f.motion_scale[0]=-1;
    assert(Validate(f)==Rejection::InvalidMotionScale);
    f=Verified(); f.elapsed_ms=1000;
    assert(Validate(f)==Rejection::InvalidTiming);
    f=Verified(); f.vulkan_inputs_in_general_layout=false;
    assert(Validate(f)==Rejection::InvalidVulkanImageLayout);
    f=Verified(); f.tan_half_fov=0.0f;
    assert(Validate(f)==Rejection::InvalidProjection);
    f=Verified(); f.depth_to_view[0]=std::numeric_limits<float>::infinity();
    assert(Validate(f)==Rejection::InvalidProjection);
    f=Verified(); f.captured_gpu_work_complete=false;
    assert(Validate(f)==Rejection::MissingGpuCompletion);
    assert(sequence.Observe(f)==Rejection::MissingGpuCompletion);
    assert(sequence.Observe(Verified(8))==Rejection::None); // reset
    return 0;
}
