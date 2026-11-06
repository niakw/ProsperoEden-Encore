// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
// Graphics option 3: a separate FXAA quality shader on native Vulkan.
// Runtime accessors are implemented in one video_core translation unit,
// shared by the launcher and the presentation layer.
namespace Eden::Graphics {
void SetEnhancedFxaa(bool enabled) noexcept;
[[nodiscard]] bool EnhancedFxaa() noexcept;
}
