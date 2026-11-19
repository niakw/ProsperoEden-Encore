// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
// Read ONLY at the two already-existing NS2 loading milestones (10s, 30s).
// This reuses the fixed SVC ring; no per-SVC, per-draw or per-present work.
#include <array>
#include <atomic>
#include <cstdint>
#include <cstdio>
#include <cstddef>
#include "core/loader/ns2_svc_trace.h"

namespace Eden::NS2::LoadingSvcSnapshot {
struct Snapshot {
    std::uint64_t pid{};
    std::uint64_t traced_count{};
    std::uint32_t first32_count{};
    bool detailed_enabled{};
    std::array<char, 384> last_critical{};
};

inline Snapshot Capture() noexcept {
    Snapshot snapshot{};
    snapshot.pid = SvcTrace::active_pid.load(std::memory_order_acquire);
    snapshot.traced_count = SvcTrace::recent_sequence.load(std::memory_order_acquire);
    snapshot.first32_count = SvcTrace::observations.load(std::memory_order_relaxed);
    snapshot.detailed_enabled = SvcTrace::DetailedEnabled();
    if (snapshot.pid != 0) {
        (void)SvcTrace::FormatCriticalRecent(snapshot.pid, snapshot.last_critical.data(),
                                             snapshot.last_critical.size());
    }
    return snapshot;
}

inline void Report(unsigned stage_seconds) noexcept {
    const auto snapshot = Capture();
    // A zero PID during an NS2 launch is itself diagnostic: the loader
    // never installed, or already retired, its guest SVC process owner.
    // In quiet mode the ring counts only GetInfo/QueryMemory; zero does
    // NOT mean that the guest executed no SVC at all.
    std::fprintf(stderr,
        "EDEN_NS2_LOADING_SVC stage=%us active_pid=%llu tracked_recent=%llu "
        "sampled_first32=%u detailed=%u critical=%s\n",
        stage_seconds,
        static_cast<unsigned long long>(snapshot.pid),
        static_cast<unsigned long long>(snapshot.traced_count),
        snapshot.first32_count, unsigned(snapshot.detailed_enabled),
        snapshot.last_critical[0] ? snapshot.last_critical.data() : "none");
}
} // namespace Eden::NS2::LoadingSvcSnapshot
