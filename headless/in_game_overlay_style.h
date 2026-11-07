// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#include <algorithm>
#include <cstdint>

// In-game quick menu style mirrors the launcher palette/accent selection.
// Packed into the existing menu-only 32-bit HUD mode; no ABI expansion.
namespace Eden::QuickOverlay {
inline constexpr std::uint32_t kStyleTag=0xff100000u;
inline constexpr std::uint32_t kTagMask=0xfff00000u;
inline constexpr std::uint32_t kKindMask=15u;
inline constexpr std::uint32_t kBackdrop=kStyleTag|1u;
inline constexpr std::uint32_t kRow=kStyleTag|2u;
inline constexpr std::uint32_t kSelectedRow=kStyleTag|3u;
inline constexpr std::uint32_t kWarningRow=kStyleTag|4u;
[[nodiscard]] constexpr std::uint32_t StyleId(
  int palette,int accent,bool high_contrast,bool switch_home) noexcept {
    const int effective=switch_home?0:std::clamp(palette,0,3);
    return std::uint32_t(effective+4*std::clamp(accent,0,4)+
                         (high_contrast?20:0));
}
[[nodiscard]] constexpr std::uint32_t StyledMode(
    std::uint32_t primitive,std::uint32_t style) noexcept {
    return primitive|((style&63u)<<8u);
}
[[nodiscard]] constexpr bool IsQuickMode(std::uint32_t mode) noexcept {
    return (mode&kTagMask)==kStyleTag &&
           (mode&kKindMask)>=1u && (mode&kKindMask)<=4u;
}
static_assert(StyleId(1,3,true,false)==33u);
static_assert(StyleId(3,4,false,true)==16u);
static_assert(IsQuickMode(StyledMode(kBackdrop,20u)));
static_assert(!IsQuickMode(1u));
} // namespace Eden::QuickOverlay
