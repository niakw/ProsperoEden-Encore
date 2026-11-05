// SPDX-License-Identifier: GPL-3.0-or-later
#include "framegen_present_gate.h"
#include <cassert>
using namespace Eden::FeatureLab;

int main() {
    GraphicsCapabilities caps{};
    caps.native_vulkan = true;
    caps.mihawk_compute = true;
    caps.model_weights_verified_and_licensed = true;
    caps.game_fps = 30;
    PresentGateInput f{};
    f.real_frame_id = 1; f.timestamp_ns = 1'000'000'000;
    f.width = 1920; f.height = 1080; f.output_hz = 60;
    f.display_mode_verified = true;
    FramegenPresentGate gate;
    assert(gate.OnRealFrame(FrameGeneration::MihawkGen, caps, f).reason ==
           PresentGateReason::NoStablePair);
    ++f.real_frame_id; f.timestamp_ns += 33'333'333;
    assert(gate.OnRealFrame(FrameGeneration::MihawkGen, caps, f).eligible());
    ++f.real_frame_id; f.timestamp_ns += 33'333'333;
    f.overlay_changed = true;
    assert(gate.OnRealFrame(FrameGeneration::MihawkGen, caps, f).reason ==
           PresentGateReason::UnsafeOverlay);
    f.overlay_changed = false;
    ++f.real_frame_id; f.timestamp_ns += 33'333'333;
    assert(!gate.OnRealFrame(FrameGeneration::MihawkGen, caps, f).eligible());
    ++f.real_frame_id; f.timestamp_ns += 33'333'333;
    assert(gate.OnRealFrame(FrameGeneration::MihawkGen, caps, f).eligible());
    ++f.real_frame_id; f.timestamp_ns += 83'333'333;
    assert(gate.OnRealFrame(FrameGeneration::MihawkGen, caps, f).reason ==
           PresentGateReason::WrongCadence);
    f.real_frame_id += 2; f.timestamp_ns += 33'333'333;
    assert(!gate.OnRealFrame(FrameGeneration::MihawkGen, caps, f).eligible());
    ++f.real_frame_id; f.timestamp_ns += 33'333'333;
    assert(gate.OnRealFrame(FrameGeneration::MihawkGen, caps, f).eligible());
    f.scene_reset = true;
    assert(gate.OnRealFrame(FrameGeneration::MihawkGen, caps, f).reason ==
           PresentGateReason::Paused);
    f.scene_reset = false;
    caps.model_weights_verified_and_licensed = false;
    assert(gate.OnRealFrame(FrameGeneration::MihawkGen, caps, f).reason ==
           PresentGateReason::Unsupported);
    caps.model_weights_verified_and_licensed = true;
    caps.game_fps = 60; f.output_hz = 120; f.real_frame_id = 1;
    f.timestamp_ns = 2'000'000'000;
    assert(!gate.OnRealFrame(FrameGeneration::MihawkGen, caps, f).eligible());
    f.real_frame_id++; f.timestamp_ns += 16'666'667;
    assert(gate.OnRealFrame(FrameGeneration::MihawkGen, caps, f).eligible());
    f.output_hz = 60;
    assert(gate.OnRealFrame(FrameGeneration::MihawkGen, caps, f).reason ==
           PresentGateReason::NoDisplayHeadroom);
    caps.guest_motion_vectors = false;
    assert(gate.OnRealFrame(FrameGeneration::Fsr3Vulkan, caps, f).reason ==
           PresentGateReason::Unsupported);
    assert(gate.OnRealFrame(FrameGeneration::LosslessScaling, caps, f).reason ==
           PresentGateReason::Unsupported);
    assert(gate.OnRealFrame(FrameGeneration::Off, caps, f).reason ==
           PresentGateReason::Disabled);
}
