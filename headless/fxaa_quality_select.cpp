// SPDX-License-Identifier: GPL-3.0-or-later
#include "fxaa_quality_select.h"
#include <atomic>
namespace Eden::Graphics {
namespace {
std::atomic<bool> enhanced_fxaa{false};
}
void SetEnhancedFxaa(bool enabled) noexcept {
    enhanced_fxaa.store(enabled, std::memory_order_release);
}
bool EnhancedFxaa() noexcept {
    return enhanced_fxaa.load(std::memory_order_acquire);
}
}
