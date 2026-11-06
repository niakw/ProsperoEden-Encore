// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
// R24: AA source-image sizing contract, independent of Vulkan headers.
// The source of the AA pass can be either an accelerated guest texture
// with scaled dimensions, or a raw framebuffer readback at guest size.
#include <cstdint>

namespace Eden::Graphics {
struct AaExtent {
    std::uint32_t width{};
    std::uint32_t height{};
};
[[nodiscard]] constexpr bool AaValid(AaExtent v) noexcept {
    return v.width != 0 && v.height != 0 &&
           v.width <= 8192 && v.height <= 8192;
}
[[nodiscard]] constexpr AaExtent AaSourceExtent(
    bool accelerated, AaExtent raw_guest, AaExtent scaled_guest) noexcept {
    const AaExtent source = accelerated ? scaled_guest : raw_guest;
    return AaValid(source) ? source : AaExtent{};
}
[[nodiscard]] constexpr bool AaExtentChanged(AaExtent before,
                                             AaExtent after) noexcept {
    return before.width != after.width || before.height != after.height;
}
} // namespace Eden::Graphics
