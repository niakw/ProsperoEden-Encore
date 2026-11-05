// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#include <algorithm>

namespace Eden::Graphics {
// The launch process has already mapped UI percentage to RCAS internal
// 200 - (percentage*2). SGSR uses a different 0..2 intensity scale.
// This maps 0% to 0, 50% to 1, and 100% to 2 for BOTH SGSR shaders.
[[nodiscard]] constexpr float SgsrEdgeIntensityFromInternal(int raw) noexcept {
    return 2.0f - static_cast<float>(std::clamp(raw,0,200))/100.0f;
}
static_assert(SgsrEdgeIntensityFromInternal(200)==0.0f);
static_assert(SgsrEdgeIntensityFromInternal(100)==1.0f);
static_assert(SgsrEdgeIntensityFromInternal(0)==2.0f);
}
