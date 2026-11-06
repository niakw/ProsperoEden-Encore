// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
// R07: match the authenticated guest image/view IDs to the actual Vulkan
// inputs handed to the temporal compute bridge. Independent of Vulkan headers
// so this is host-testable without a renderer or fabricated game motion.
#include <array>
#include <cstdint>
#include "fsr31_temporal_contract.h"

namespace Eden::Graphics::Temporal {
struct NativeResource {
    std::uint64_t image{};
    std::uint64_t view{};
};
struct NativeResources {
    NativeResource color{}, depth{}, motion{};
};

// Reject an in-place temporal blit into any input image, even if Vulkan
// scheduling would place compute before rasterization: guest texture cache
// aliasing and future frame-history reads must remain strictly unchanged.
struct NativeDestination {
    std::uint64_t image{};
    std::uint32_t width{};
    std::uint32_t height{};
    std::uint32_t samples{};
    bool single_color_no_depth{};
};
[[nodiscard]] constexpr Rejection ValidateNativeDestination(
    const Inputs& metadata, const NativeDestination& dst) noexcept {
    if (!dst.image) return Rejection::MissingResource;
    if (dst.image == metadata.scene_color.image ||
        dst.image == metadata.depth.image ||
        dst.image == metadata.motion.image)
        return Rejection::OutputAliasesInput;
    if (!dst.single_color_no_depth || dst.samples != 1 ||
        dst.width != metadata.output_width || dst.height != metadata.output_height)
        return Rejection::InvalidResolution;
    return Rejection::None;
}

[[nodiscard]] constexpr Rejection ValidateNativeResources(
    const Inputs& metadata, const NativeResources& native) noexcept {
    const std::array<Resource,3> declared{
        metadata.scene_color, metadata.depth, metadata.motion};
    const std::array<NativeResource,3> actual{
        native.color,native.depth,native.motion};
    for (std::size_t i=0;i<declared.size();++i) {
        if (!actual[i].image || !actual[i].view) {
            return Rejection::MissingResource;
        }
        if (declared[i].image!=actual[i].image ||
            declared[i].view!=actual[i].view) {
            return Rejection::MismatchedNativeResource;
        }
    }
    // Distinct resources must represent distinct semantic inputs. A repeated
    // view would confuse depth/motion sampling even if a caller marked it verified.
    if (native.color.view==native.depth.view ||
        native.color.view==native.motion.view ||
        native.depth.view==native.motion.view) {
        return Rejection::MismatchedNativeResource;
    }
    return Rejection::None;
}
} // namespace Eden::Graphics::Temporal
