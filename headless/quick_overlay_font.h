// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#include <array>
#include <cstdint>
#include <string_view>

namespace Eden::QuickOverlay {

// Shapes one quick-menu row with the same HarfBuzz/SystemFonts path used by
// the launcher. Each word packs a generated atlas slot plus its positioned
// baseline origin. The legacy FPS HudSnapshot encoding is unchanged.
std::array<std::uint32_t, 24> EncodeMenuText(std::string_view text, int language);

} // namespace Eden::QuickOverlay
