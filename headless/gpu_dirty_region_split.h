// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
// The GPU dirty collector's 32-bit mask represents exactly 32 x 64-byte
// cells (2 KiB). A guest write crossing a collector boundary must be split
// BEFORE calling GPUDirtyMemoryManager::Collect(), not after.
#include <algorithm>
#include <cstdint>
#include <exception>
#include <limits>

namespace Eden::GpuDirty {
inline constexpr std::uint64_t kRegionBytes = 2048;
static_assert((kRegionBytes & (kRegionBytes - 1)) == 0, "mask region must be power of two");

template <class Collect>
void ForEachRegion(std::uint64_t address, std::uint64_t size, Collect&& collect) {
    // Fail closed rather than silently wrap a guest address or lose a range.
    if (size > std::numeric_limits<std::uint64_t>::max() - address) {
        std::terminate();
    }
    if (size == 0) return;
    // Most guest dirty writes fit in one 2 KiB mask. Peel the first
    // collection so they avoid the generic loop back-edge and second size
    // check, without changing the exact 64-byte mask boundaries.
    auto amount = std::min(size, kRegionBytes - (address & (kRegionBytes - 1)));
    collect(address, amount);
    address += amount;
    size -= amount;
    while (size != 0) {
        amount = std::min(size, kRegionBytes - (address & (kRegionBytes - 1)));
        collect(address, amount);
        address += amount;
        size -= amount;
    }
}
} // namespace Eden::GpuDirty
