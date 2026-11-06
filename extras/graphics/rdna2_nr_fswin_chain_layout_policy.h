// SPDX-License-Identifier: MIT
// RDNA2 FSwin multi-layer window-layout contract.
// Positions are in 4x4-token tiles relative to an 8x8-token window.
#pragma once
#include <cstddef>
#include <cstdint>
#include <span>

namespace Eden::Graphics::NeuralRDNA2 {
struct FSwinWindowLayout {
    std::uint32_t windows_x{};
    std::uint32_t windows_y{};
    std::int32_t shift_x{};
    std::int32_t shift_y{};
};
[[nodiscard]] constexpr bool FSwinNeedsWindowRepack(
    const FSwinWindowLayout& from,
    const FSwinWindowLayout& to) noexcept {
    return from.shift_x!=to.shift_x || from.shift_y!=to.shift_y;
}
[[nodiscard]] constexpr bool CanFSwinChainWindowLayouts(
    std::span<const FSwinWindowLayout> layouts,
    std::uint32_t windows) noexcept {
    if(layouts.empty()||layouts.size()>160u||windows==0u||
       windows>65535u)return false;
    const auto first=layouts.front();
    const bool has_grid=first.windows_x!=0u||first.windows_y!=0u;
    if(has_grid &&
       (!first.windows_x||!first.windows_y||
        std::uint64_t(first.windows_x)*first.windows_y!=windows))
        return false;
    for(const auto& l:layouts) {
        if(l.shift_x<-1||l.shift_x>1||
           l.shift_y<-1||l.shift_y>1)return false;
        if(has_grid) {
            if(l.windows_x!=first.windows_x||
               l.windows_y!=first.windows_y)return false;
        }else if(l.windows_x||l.windows_y||l.shift_x||l.shift_y) {
            // Legacy chains without explicit grid are unshifted only.
            return false;
        }
    }
    return true;
}
} // namespace Eden::Graphics::NeuralRDNA2
