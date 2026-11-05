// SPDX-License-Identifier: GPL-3.0-or-later
#include "fsr1_sharpness_policy.h"
#include <cassert>
#include <cmath>
int main() {
    using Eden::Graphics::Fsr1SharpnessFromPercent;
    using Eden::Graphics::Fsr1SharpnessFromInternal;
    const auto off=Fsr1SharpnessFromPercent(0);
    const auto low=Fsr1SharpnessFromPercent(25);
    const auto mid=Fsr1SharpnessFromPercent(50);
    const auto high=Fsr1SharpnessFromPercent(75);
    const auto max=Fsr1SharpnessFromPercent(100);
    assert(!off.rcas_enabled);
    assert(low.rcas_enabled && mid.rcas_enabled &&
           high.rcas_enabled && max.rcas_enabled);
    assert(off.rcas_stops == 2.0f);
    assert(mid.rcas_stops == 1.0f);
    assert(max.rcas_stops == 0.0f);
    // SDK mapping FsrRcasCon -> exp2(-stops). The previous code
    // mistakenly used 0% => strongest and 100% => weaker.
    assert(std::exp2(-low.rcas_stops) < std::exp2(-mid.rcas_stops));
    assert(std::exp2(-mid.rcas_stops) < std::exp2(-high.rcas_stops));
    assert(std::exp2(-high.rcas_stops) < std::exp2(-max.rcas_stops));
    assert(Fsr1SharpnessFromPercent(-500).rcas_stops == 2.0f);
    assert(!Fsr1SharpnessFromPercent(-500).rcas_enabled);
    assert(Fsr1SharpnessFromPercent(800).rcas_stops == 0.0f);
    // Critically test the real launcher->shared-settings->Vulkan bridge.
    // Launch path writes internal 200 - user_percent*2, NOT user_percent.
    for (int percent=0; percent<=100; ++percent) {
        const auto ui=Fsr1SharpnessFromPercent(percent);
        const auto native=Fsr1SharpnessFromInternal(200-percent*2);
        assert(ui.rcas_enabled==native.rcas_enabled);
        assert(ui.rcas_stops==native.rcas_stops);
    }
    assert(!Fsr1SharpnessFromInternal(200).rcas_enabled);
    assert(Fsr1SharpnessFromInternal(100).rcas_stops==1.0f);
    assert(Fsr1SharpnessFromInternal(0).rcas_stops==0.0f);
    return 0;
}
