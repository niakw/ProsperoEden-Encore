// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#include <algorithm>

namespace Eden::Graphics {
struct Fsr1Sharpness {
    bool rcas_enabled;
    float rcas_stops;
};
// AMD RCAS takes sharpening *stops*: 0 = strongest, 2 = softer.
// The PS5 UI is "Netteté (%)": 0 should disable RCAS, 100 the strongest.
// A 50% preference maps to 1 stop, consistent with the historic default.
[[nodiscard]] constexpr Fsr1Sharpness Fsr1SharpnessFromPercent(int percent) noexcept {
    const int bounded = std::clamp(percent, 0, 100);
    return {.rcas_enabled = bounded != 0,
            .rcas_stops = static_cast<float>(100 - bounded) / 50.0f};
}
// Eden's shared Settings::values.fsr_sharpening_slider is a 0..200
// RCAS-stop quantity. The Encore launch path ALREADY maps user-facing
// percentages to it as: internal = 200 - 2 * percent. Never feed the
// internal value back to Fsr1SharpnessFromPercent: doing so would
// clamp >100 and apply the strongest RCAS at almost every UI setting.
[[nodiscard]] constexpr Fsr1Sharpness Fsr1SharpnessFromInternal(int raw) noexcept {
    const int bounded = std::clamp(raw, 0, 200);
    return {.rcas_enabled = bounded != 200,
            .rcas_stops = static_cast<float>(bounded) / 100.0f};
}
static_assert(!Fsr1SharpnessFromInternal(200).rcas_enabled);
static_assert(Fsr1SharpnessFromInternal(100).rcas_stops == 1.0f);
static_assert(Fsr1SharpnessFromInternal(0).rcas_stops == 0.0f);
static_assert(Fsr1SharpnessFromPercent(0).rcas_enabled == false);
static_assert(Fsr1SharpnessFromPercent(50).rcas_stops == 1.0f);
static_assert(Fsr1SharpnessFromPercent(100).rcas_stops == 0.0f);
}
