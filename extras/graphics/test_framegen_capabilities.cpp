// SPDX-License-Identifier: GPL-3.0-or-later
#include "framegen_capabilities.h"
#include <cassert>
using namespace Eden::FeatureLab;

int main() {
    constexpr GraphicsCapabilities empty{};
    static_assert(QualifyFrameGeneration(FrameGeneration::Off, empty)
                  == Availability::Disabled);
    static_assert(QualifyFrameGeneration(
                      FrameGeneration::DlssPcOnlyUnsupported, empty)
                  == Availability::Unsupported);
    auto caps = GraphicsCapabilities{};
    caps.native_vulkan = true;
    caps.game_fps = 30;
    assert(QualifyFrameGeneration(FrameGeneration::Fsr3Vulkan, caps)
           == Availability::Unsupported);
    caps.fsr3_swapchain = true;
    caps.guest_motion_vectors = true;
    assert(QualifyFrameGeneration(FrameGeneration::Fsr3Vulkan, caps)
           == Availability::Unsupported); // Depth absent.
    caps.guest_depth = true;
    assert(QualifyFrameGeneration(FrameGeneration::Fsr3Vulkan, caps)
           == Availability::ExperimentalLowCadence);
    caps.game_fps = 60;
    assert(QualifyFrameGeneration(FrameGeneration::Fsr3Vulkan, caps)
           == Availability::Experimental);
    assert(QualifyFrameGeneration(FrameGeneration::MihawkGen, caps)
           == Availability::Unsupported); // Backend & weights missing.
    caps.mihawk_compute = true;
    caps.model_weights_verified_and_licensed = true;
    assert(QualifyFrameGeneration(FrameGeneration::MihawkGen, caps)
           == Availability::Experimental);
    caps.game_fps = 29;
    assert(QualifyFrameGeneration(FrameGeneration::MihawkGen, caps)
           == Availability::Unsupported);
    caps.game_fps = 60;
    assert(QualifyFrameGeneration(FrameGeneration::LosslessScaling, caps)
           == Availability::Unsupported);
    caps.lossless_scaling_provider_available = true;
    assert(QualifyFrameGeneration(FrameGeneration::LosslessScaling, caps)
           == Availability::Experimental);
    assert(QualifyFrameGeneration(
               FrameGeneration::DlssPcOnlyUnsupported, caps)
           == Availability::Unsupported);
}
