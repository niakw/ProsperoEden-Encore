// SPDX-License-Identifier: MIT
// Host-only PS5 R09 spatial-coordinate model. Adapts symmetric peripheral
// radius transforms published by BeliyG3/optimizer-fps-dlss5 (MIT).
// Copyright (c) 2026 Yuri Grib (BeliyG3), see LICENSES/optimizer-fps-dlss5-MIT.txt.
#pragma once
#include <algorithm>
#include <cmath>
#include <cstdint>

namespace Eden::Graphics::DlssNrMin {
struct AxisWarp {
    std::uint32_t original{}, work{};
    float center_fraction{0.8f}, work_fraction{0.9f};
};
[[nodiscard]] inline bool Valid(AxisWarp a) noexcept {
    return a.original >= 2u && a.work >= 2u &&
        std::isfinite(a.center_fraction) && std::isfinite(a.work_fraction) &&
        a.center_fraction > 0.0f && a.center_fraction < a.work_fraction &&
        a.work_fraction <= 1.0f &&
        std::fabs(float(a.work) / float(a.original) - a.work_fraction) <=
            2.0f / float(a.original);
}
[[nodiscard]] inline float WarpRadius(float r, float c, float w) noexcept {
    if (r <= c) return r;
    const float compression = (w - c) / (1.0f - c);
    const float t = (r - c) / (1.0f - c);
    return c + (w - c) * t / (compression + (1.0f - compression) * t);
}
[[nodiscard]] inline float UnwarpRadius(float r, float c, float w) noexcept {
    if (r <= c) return r;
    const float compression = (w - c) / (1.0f - c);
    const float y = (r - c) / (w - c);
    const float denominator = 1.0f - (1.0f - compression) * y;
    return c + (1.0f - c) * compression * y / denominator;
}
// Pixel coordinates rather than pixel indices. Invalid input returns NaN.
[[nodiscard]] inline float WarpPixel(float source_pixel, AxisWarp a) noexcept {
    if (!Valid(a) || !std::isfinite(source_pixel) ||
        source_pixel < 0.0f || source_pixel > float(a.original))
        return std::nanf("");
    const float radius = 2.0f * source_pixel / float(a.original) - 1.0f;
    const float warped = std::copysign(
        WarpRadius(std::fabs(radius), a.center_fraction, a.work_fraction), radius);
    return (warped / a.work_fraction + 1.0f) * 0.5f * float(a.work);
}
[[nodiscard]] inline float UnwarpPixel(float work_pixel, AxisWarp a) noexcept {
    if (!Valid(a) || !std::isfinite(work_pixel) ||
        work_pixel < 0.0f || work_pixel > float(a.work))
        return std::nanf("");
    const float radius = (2.0f * work_pixel / float(a.work) - 1.0f) * a.work_fraction;
    const float original = std::copysign(
        UnwarpRadius(std::fabs(radius), a.center_fraction, a.work_fraction), radius);
    return (original + 1.0f) * 0.5f * float(a.original);
}
} // namespace Eden::Graphics::DlssNrMin
