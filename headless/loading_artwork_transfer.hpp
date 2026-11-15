// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
// Renderer-independent transfer of actual title-scoped launcher artwork.
// The input is a launcher RGBA frame, not a guest framebuffer.
#include "launch_handoff.hpp"
#include <algorithm>
#include <cstdint>
#include <span>

namespace Eden::LoadingArtwork {
enum class PixelOrder { RGBA, BGRA };
struct Rect { std::uint32_t x{}, y{}, width{}, height{}; };
inline constexpr Rect Fit(std::uint32_t sw, std::uint32_t sh,
                          std::uint32_t dw, std::uint32_t dh) noexcept {
    if (!sw || !sh || !dw || !dh) return {};
    std::uint32_t w = dw, h = dh;
    if (std::uint64_t(sw) * dh > std::uint64_t(dw) * sh)
        h = std::max(1u, std::uint32_t(std::uint64_t(dw) * sh / sw));
    else
        w = std::max(1u, std::uint32_t(std::uint64_t(dh) * sw / sh));
    return {(dw - w) / 2, (dh - h) / 2, w, h};
}

// One bounded conversion into existing upload storage. Preserve the artwork
// aspect, and extend edge pixels rather than introducing a branded strip.
inline bool Repack(const LaunchHandoff::Frame& source,
                   std::uint32_t width, std::uint32_t height,
                   PixelOrder order, std::span<std::uint8_t> destination) noexcept {
    if (!LaunchHandoff::Valid(source) || !width || !height ||
        width > 4096 || height > 2160) return false;
    const auto size = std::size_t(width) * height * 4u;
    if (destination.size() < size) return false;
    const Rect fit = Fit(source.width, source.height, width, height);
    for (std::uint32_t y = 0; y < height; ++y) {
        const auto local_y = std::clamp(y, fit.y, fit.y + fit.height - 1) - fit.y;
        const auto sy = std::uint32_t(std::uint64_t(local_y) * source.height / fit.height);
        for (std::uint32_t x = 0; x < width; ++x) {
            const auto local_x = std::clamp(x, fit.x, fit.x + fit.width - 1) - fit.x;
            const auto sx = std::uint32_t(std::uint64_t(local_x) * source.width / fit.width);
            const auto src = (std::size_t(sy) * source.width + sx) * 4u;
            const auto dst = (std::size_t(y) * width + x) * 4u;
            const bool bgra = order == PixelOrder::BGRA;
            destination[dst] = source.rgba[src + (bgra ? 2 : 0)];
            destination[dst + 1] = source.rgba[src + 1];
            destination[dst + 2] = source.rgba[src + (bgra ? 0 : 2)];
            destination[dst + 3] = 255;
        }
    }
    return true;
}
} // namespace Eden::LoadingArtwork
