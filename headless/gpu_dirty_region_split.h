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
    // A one-region guest write needs only the first boundary comparison,
    // not a std::min plus two subsequent loop/tail condition checks.
    const auto first_span = kRegionBytes - (address & (kRegionBytes - 1));
    if (size <= first_span) {
        collect(address, size);
        return;
    }
    // At least one byte remains after this first partial/full region.
    collect(address, first_span);
    address += first_span;
    size -= first_span;
    // If bytes remain after peeling the first region, address is now
    // aligned to 2 KiB. Consume complete regions without re-masking the
    // already aligned address or re-running std::min on each region.
    while (size >= kRegionBytes) {
        collect(address, kRegionBytes);
        address += kRegionBytes;
        size -= kRegionBytes;
    }
    if (size != 0) collect(address, size);
}
} // namespace Eden::GpuDirty
