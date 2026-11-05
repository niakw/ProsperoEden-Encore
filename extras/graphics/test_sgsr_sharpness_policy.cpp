// SPDX-License-Identifier: GPL-3.0-or-later
#include "sgsr_sharpness_policy.h"
#include <cassert>
#include <cmath>
int main() {
    using Eden::Graphics::SgsrEdgeIntensityFromInternal;
    assert(SgsrEdgeIntensityFromInternal(200)==0.0f);
    assert(SgsrEdgeIntensityFromInternal(100)==1.0f);
    assert(SgsrEdgeIntensityFromInternal(0)==2.0f);
    assert(SgsrEdgeIntensityFromInternal(-100)==2.0f);
    assert(SgsrEdgeIntensityFromInternal(1000)==0.0f);
    float previous=-1;
    for (int percent=0;percent<=100;++percent) {
        const float strength=SgsrEdgeIntensityFromInternal(200-percent*2);
        assert(strength>=0 && strength<=2);
        assert(strength>=previous);
        assert(std::abs(strength-static_cast<float>(percent)/50.0f)<0.0001f);
        previous=strength;
    }
    return 0;
}
