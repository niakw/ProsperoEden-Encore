// SPDX-License-Identifier: GPL-3.0-or-later
#include "dlss_nr_min_spatial_math.h"
#include <cassert>
#include <cmath>
#include <limits>
using namespace Eden::Graphics::DlssNrMin;
int main() {
    const AxisWarp width{1920u, 1728u, 0.8f, 0.9f};
    const AxisWarp height{1080u, 972u, 0.8f, 0.9f};
    assert(Valid(width) && Valid(height));
    assert(!Valid({1920u, 1728u, 0.9f, 0.9f}));
    assert(!Valid({1920u, 1728u, 0.8f, 1.1f}));
    assert(!Valid({1920u, 1000u, 0.8f, 0.9f}));
    assert(std::isnan(WarpPixel(-1.0f, width)));
    assert(std::isnan(UnwarpPixel(10000.0f, width)));
    assert(std::isnan(WarpPixel(std::numeric_limits<float>::infinity(), width)));
    for (const auto a : {width, height}) {
        float previous = -1.0f;
        for (std::uint32_t i=0; i<=a.original; ++i) {
            const float x = float(i);
            const float work = WarpPixel(x, a);
            assert(std::isfinite(work) && work > previous);
            assert(work >= -0.001f && work <= float(a.work) + 0.001f);
            const float back = UnwarpPixel(work, a);
            assert(std::isfinite(back) && std::fabs(back - x) < 0.002f);
            previous = work;
        }
        assert(std::fabs(WarpPixel(float(a.original)/2.0f, a) -
                         float(a.work)/2.0f) < 0.001f);
        // Exact uncompressed center band, up to float rounding.
        const float band = float(a.original) * a.center_fraction * 0.5f;
        assert(std::fabs((WarpPixel(float(a.original)/2.0f + band,a) -
                         float(a.work)/2.0f) - band) < 0.001f);
    }
}
