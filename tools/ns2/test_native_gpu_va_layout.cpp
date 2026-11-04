// SPDX-License-Identifier: GPL-3.0-or-later
// Host-only native GMMU VA fixture; does not submit GPU commands.
#include <cassert>
#include <cstdint>
#include <cstdio>
#include "core/hle/service/nvdrv/devices/native_gpu_va_layout.h"

using Service::Nvidia::Devices::PlanNativeGpuVaLayout;
using Service::Nvidia::Devices::NativePinnedPhysicalSpan;
using Service::Nvidia::Devices::NativeNs2GpuVaStart;
using Service::Nvidia::Devices::NativeNs2GpuVaSmallSplit;
using Service::Nvidia::Devices::NativeNs2GpuVaEnd;
int main() {
    const auto defaults = PlanNativeGpuVaLayout(0x8000000, 1ULL << 34, 1ULL << 37, 0x20000);
    assert(defaults && defaults->small_begin == 32768 &&
           defaults->small_end == 4194304 && defaults->big_begin == 131072 &&
           defaults->big_end == 1048576);
    // The 37-bit Maxwell default cannot contain a 0x81_0000_0000 GPU-only
    // render target. The NS2-only session uses 40-bit VA with 4K pages high
    // enough for it, while the second partition remains a valid big-page VA.
    const auto ns2 = PlanNativeGpuVaLayout(
        NativeNs2GpuVaStart, NativeNs2GpuVaSmallSplit,
        NativeNs2GpuVaEnd, 0x20000);
    constexpr std::uint64_t gpu_only_target = 0x8100000000ULL;
    assert(ns2 && gpu_only_target >= NativeNs2GpuVaStart &&
           gpu_only_target + 0x20000000ULL < NativeNs2GpuVaSmallSplit &&
           NativeNs2GpuVaSmallSplit < NativeNs2GpuVaEnd);
    assert(std::uint64_t{ns2->small_end} * 0x1000 == NativeNs2GpuVaSmallSplit);
    assert(std::uint64_t{ns2->big_end} * 0x20000 == NativeNs2GpuVaEnd);
    // Both FlatAllocator limits are absolute; a relative (end-split)
    // calculation would incorrectly return half this custom large-page end.
    const auto custom = PlanNativeGpuVaLayout(0x1000000, 1ULL << 30, 1ULL << 31, 0x10000);
    assert(custom && custom->big_begin == 16384 && custom->big_end == 32768);
    assert(!PlanNativeGpuVaLayout(0x8000000, 1ULL << 37, 1ULL << 34, 0x20000));
    assert(!PlanNativeGpuVaLayout(0x8000000, 1ULL << 34, 1ULL << 34, 0x20000));
    assert(!PlanNativeGpuVaLayout(0, 1ULL << 34, 1ULL << 37, 0x20000));
    assert(!PlanNativeGpuVaLayout(0x8000001, 1ULL << 34, 1ULL << 37, 0x20000));
    assert(!PlanNativeGpuVaLayout(0x8000000, (1ULL << 34) + 0x1000, 1ULL << 37, 0x20000));
    assert(!PlanNativeGpuVaLayout(0x8000000, 1ULL << 34, (1ULL << 37) + 0x1000, 0x20000));
    assert(!PlanNativeGpuVaLayout(0x8000000, 1ULL << 45, 1ULL << 46, 0x20000));
    assert(!PlanNativeGpuVaLayout(0x8000000, 1ULL << 34, 1ULL << 37, 0x40000));
    // Physical NVMap bases and suballocation offsets must never wrap.
    // Exercise both exact half-open endpoints and overflow by one byte.
    constexpr auto max = std::uint64_t{~std::uint64_t{0}};
    static_assert(NativePinnedPhysicalSpan(1, 0, max - 1));
    static_assert(NativePinnedPhysicalSpan(0x1000, 0x2000, 0x4000));
    static_assert(!NativePinnedPhysicalSpan(0, 0, 0x1000));
    static_assert(!NativePinnedPhysicalSpan(1, 0, 0));
    static_assert(!NativePinnedPhysicalSpan(max - 2, 3, 1));
    static_assert(!NativePinnedPhysicalSpan(max - 2, 1, 2));
    assert(NativePinnedPhysicalSpan(max - 2, 1, 1));
    assert(!NativePinnedPhysicalSpan(0x1000, max - 0x1000, 1));
    std::puts("NS2 pinned physical spans: PASS (exact-end/overflows)");
    std::puts("NS2 real 4K GMMU page partitions: PASS");
}
