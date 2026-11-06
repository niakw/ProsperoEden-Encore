// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#include "pe/core/strings.hpp"
#include <algorithm>

namespace pe::ui {
// R10 texture sampling, not upscaling or AI-generated texture replacement.
// The numeric choices are 2x/4x/8x/16x anisotropic sampler levels.
inline constexpr const char* kTextureAnisotropyLabels[] = {
    TR("Automatic"), TR("Game default"), "2x", "4x", "8x", "16x"};
inline const char* TextureAnisotropyName(int choice) {
    return pe::tr(kTextureAnisotropyLabels[std::clamp(choice, 0, 5)]);
}
}
