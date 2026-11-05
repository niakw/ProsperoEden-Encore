// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#include <cstdint>

namespace Eden::EncoreTextureProfiles {
// R10 extension of niakw/encore-overrides PR #1 (037ecb3), while the
// immutable 8,993-game vendor snapshot remains pinned. No vendor edits.
// 0 Auto, 1 Game default, 2 2x, 3 4x, 4 8x, 5 16x.
inline constexpr int kGeneralAnisotropy[4]{1,3,4,5};
inline constexpr int kFc27Anisotropy[4]{1,2,3,4};
inline constexpr std::uint64_t kFc27TitleId = 0x0100C49025D3E000ULL;

constexpr int ForTitle(std::uint64_t title_id,int tier) noexcept {
    tier = tier < 0 ? 0 : tier > 3 ? 3 : tier;
    return title_id == kFc27TitleId
        ? kFc27Anisotropy[tier] : kGeneralAnisotropy[tier];
}
static_assert(ForTitle(0,1)==3);
static_assert(ForTitle(kFc27TitleId,1)==2);
static_assert(ForTitle(0,3)==5);
}
