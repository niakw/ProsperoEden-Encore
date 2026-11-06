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
    caps.fsr3_optical_flow = true;
    assert(QualifyFrameGeneration(FrameGeneration::Fsr3Vulkan, caps) ==
           Availability::ReadyLowCadence); // AMD optical flow: no guessed guest MV
    caps.fsr3_optical_flow = false;
    caps.fsr3_swapchain = true;
    caps.guest_motion_vectors = true;
    assert(QualifyFrameGeneration(FrameGeneration::Fsr3Vulkan, caps)
           == Availability::Unsupported); // Depth absent.
    caps.guest_depth = true;
    assert(QualifyFrameGeneration(FrameGeneration::Fsr3Vulkan, caps)
           == Availability::ReadyLowCadence);
    caps.game_fps = 60;
    assert(QualifyFrameGeneration(FrameGeneration::Fsr3Vulkan, caps)
           == Availability::Ready);
    assert(QualifyFrameGeneration(FrameGeneration::MihawkGen, caps)
           == Availability::Unsupported); // Backend & weights missing.
    caps.mihawk_compute = true;
    caps.model_weights_verified_and_loaded = true;
    assert(QualifyFrameGeneration(FrameGeneration::MihawkGen, caps)
           == Availability::Ready);
    caps.game_fps = 29;
    assert(QualifyFrameGeneration(FrameGeneration::MihawkGen, caps)
           == Availability::Unsupported);
    caps.game_fps = 60;
    assert(QualifyFrameGeneration(FrameGeneration::LosslessScaling, caps)
           == Availability::Unsupported);
    caps.lossless_scaling_provider_available = true;
    assert(QualifyFrameGeneration(FrameGeneration::LosslessScaling, caps)
           == Availability::Ready);
    assert(QualifyFrameGeneration(
               FrameGeneration::DlssPcOnlyUnsupported, caps)
           == Availability::Unsupported);
}
