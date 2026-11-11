// SPDX-License-Identifier: GPL-3.0-or-later
// Single running game's independently selected neural video mode.
// Frontend sets it during game launch; Vulkan present layer reads it.
// A4K is applied by its existing independent Vulkan shader path.
 // Preserve the selected mode for selection/FG safety; this state does
 // not instantiate or activate a separate neural engine.
#pragma once
#include "neural_video_policy.h"
#include <atomic>
#include <algorithm>
namespace Eden::NeuralRuntime {
struct Selection {
    int mode{};
    int strength{};
};
inline std::atomic<int> current_mode{NeuralVideo::kOff};
inline std::atomic<int> current_strength{65};
inline void Configure(int requested_mode,int requested_strength) noexcept {
    const int strength=std::clamp(requested_strength,0,100);
    current_strength.store(strength,std::memory_order_relaxed);
    current_mode.store((NeuralVideo::IsA4k(requested_mode)||
                        NeuralVideo::IsDlss(requested_mode))?
        requested_mode:NeuralVideo::kOff,std::memory_order_release);
}
[[nodiscard]] inline Selection Current() noexcept {
    return {current_mode.load(std::memory_order_acquire),
            current_strength.load(std::memory_order_relaxed)};
}
} // namespace Eden::NeuralRuntime
