// SPDX-FileCopyrightText: Copyright 2026 Eden Encore Project
// SPDX-License-Identifier: GPL-3.0-or-later
// Real native QMD scheduler with deterministic host allocation-failure injection.
#include <atomic>
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <new>
#include <stdexcept>
#include "video_core/native_qmd.h"

namespace {
std::atomic<bool> fail_next_allocation{false};
}
void* operator new(std::size_t bytes) {
    if (fail_next_allocation.exchange(false, std::memory_order_relaxed))
        throw std::bad_alloc{};
    if (void* result = std::malloc(bytes ? bytes : 1)) return result;
    throw std::bad_alloc{};
}
void operator delete(void* allocation) noexcept { std::free(allocation); }
void operator delete(void* allocation, std::size_t) noexcept { std::free(allocation); }

int main() {
    Tegra::NativeQmdScheduler scheduler;
    Tegra::NativeQmdScheduler::Descriptor descriptor{};
    descriptor[18] = 0x30;
    constexpr std::uint64_t address=0x123400;
    unsigned dispatched{},released{},reads{};
    const auto read=[&](std::uint64_t addr, auto& result) {
        assert(addr==address);
        ++reads;
        result=descriptor;
        return true;
    };
    const auto release=[&](std::uint64_t, std::uint32_t, std::uint32_t) {
        ++released;
        return true;
    };
    const auto dispatch=[&](const auto&) {++dispatched;return true;};
    // Action 7 creates an entry but cannot dispatch. Fail the exact
    // unordered_map allocation. The rejection must not escape, and must
    // neither publish a release nor poison the subsequent valid signal.
    fail_next_allocation.store(true, std::memory_order_relaxed);
    const auto first=scheduler.Signal(address,7,read,release,dispatch);
    assert(first=="QMD state allocation failed");
    assert(!fail_next_allocation.load(std::memory_order_relaxed));
    assert(reads==0 && dispatched==0 && released==0);
    // The same guest can retry a valid action; the failed allocation did
    // not leave a phantom deferred dependency or consume the cache budget.
    assert(scheduler.Signal(address,3,read,release,dispatch).empty());
    assert(reads==2 && dispatched==0 && released==0);
    assert(scheduler.Signal(address,2,read,release,dispatch).empty());
    assert(reads==2 && dispatched==0 && released==0);
    // A second fresh process-like scheduler also rejects allocation errors.
    Tegra::NativeQmdScheduler independent;
    fail_next_allocation.store(true, std::memory_order_relaxed);
    assert(independent.Signal(address,3,read,release,dispatch)=="QMD state allocation failed");
    assert(independent.Signal(address,3,read,release,dispatch).empty());
    assert(dispatched==0 && released==0);
    std::puts("P2_7_REAL_QMD_ALLOCATION_RECOVERY_PASS");
}
