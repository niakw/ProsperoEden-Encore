// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#include <cstdint>
namespace Eden::DiagnosticsSharing {
// Pure policy; no threads, clocks, network or filesystem calls. The owner
// must supply real monotonic time and cancel a bounded transfer when leaving
// the launcher. No caller in gameplay/crash callbacks may open a connection.
enum class Category { Standard, Advanced };
enum class Phase { Starting, LauncherIdle, GameStarting, Playing, Stopping, Crash };
struct Consent {
    bool standard = false;
    bool advanced = false;
    constexpr bool Allows(Category c) const {
        return c == Category::Standard ? standard : advanced;
    }
};
inline constexpr std::uint32_t kMaxQueuedReports = 4;
inline constexpr std::uint32_t kMaxReportBytes = 32 * 1024;
inline constexpr std::uint32_t kMaxAttemptsPerVisit = 2;
inline constexpr std::uint32_t kIdleSeconds = 5;
inline constexpr std::uint32_t kMinIntervalSeconds = 30;
inline constexpr std::uint32_t kMaxTransferSeconds = 5;
// Re-evaluate at dispatch and immediately before reading/sending. A revoked
// category must be purged and in-flight transmission cancelled by the owner.
struct Gate {
    Phase phase = Phase::Starting;
    Consent consent{};
    bool service_available = false;
    bool network_available = false;
    bool in_flight = false;
    bool retry_due = false;
    std::uint32_t idle_seconds = 0;
    std::uint32_t attempts_this_visit = 0;
    std::uint32_t seconds_since_attempt = 0;
    constexpr bool MayStart(Category category, std::uint32_t bytes,
                            bool created_after_consent) const {
        return phase == Phase::LauncherIdle && service_available &&
               network_available && consent.Allows(category) &&
               created_after_consent && !in_flight && retry_due &&
               idle_seconds >= kIdleSeconds &&
               attempts_this_visit < kMaxAttemptsPerVisit &&
               seconds_since_attempt >= kMinIntervalSeconds &&
               bytes > 0 && bytes <= kMaxReportBytes;
    }
    constexpr bool MustCancel(Category category) const {
        return phase != Phase::LauncherIdle || !service_available ||
               !network_available || !consent.Allows(category);
    }
};
} // namespace Eden::DiagnosticsSharing
