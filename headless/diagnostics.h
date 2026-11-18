// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#include <chrono>
#include <cstdio>
#include <string>
#include <cstdint>
#include <cstddef>
#include <cerrno>
#include <cstring>
#include <fcntl.h>
#include <sys/stat.h>
#include <unistd.h>
#if defined(__PROSPERO__)
extern "C" int sceKernelDebugOutText(int, const char*);
#endif
namespace Eden {
// Only concise lifecycle/error text belongs here, never key or ticket contents.
inline void Report(const char* stage, const char* message) {
    char line[1024];
    std::snprintf(line, sizeof(line), "[ProsperoEden] %s: %.900s\n", stage, message);
    std::fputs(line, stderr);
    std::fflush(stderr);
#if defined(__PROSPERO__)
    (void)sceKernelDebugOutText(0, line);
#endif
}
// A recoverable PS5 failure is NOT a fatal signal. When Detailed Logs are OFF,
// stdout/stderr deliberately go to /dev/null, so Report() alone can never retain
// the allocation RC, title, failing stage or the final memory headroom.
// Persist exactly ONE bounded incident at the catch site. Do not change
// general logging policy or write during an emulator/GPU frame.
inline bool WriteSessionFailureReceipt(const std::string& path, const char* source_sha,
                                       std::uint64_t title_id, std::uint64_t attempt,
                                       const char* kind, const char* reason, bool detailed,
                                       bool free_query_ok, std::size_t largest_free,
                                       bool direct_failure, std::uint32_t direct_stage,
                                       std::uint32_t direct_rc, std::uint64_t direct_bytes,
                                       std::uint64_t direct_extent) noexcept {
    char clean_reason[241]{};
    for (std::size_t i = 0; reason && reason[i] && i < sizeof(clean_reason) - 1; ++i) {
        const unsigned char ch = static_cast<unsigned char>(reason[i]);
        clean_reason[i] = ch < 32 || ch == 127 ? ' ' : static_cast<char>(ch);
    }
    const auto mono_ms = std::chrono::duration_cast<std::chrono::milliseconds>(
        std::chrono::steady_clock::now().time_since_epoch()).count();
    char line[1024];
    const int size = std::snprintf(line, sizeof(line),
        "EDEN_SESSION_FAILURE_V1 monotonic_ms=%lld sha=%.40s "
        "title=%016llx attempt=%llu kind=%.32s detailed=%u "
        "largest_query_ok=%u largest_free_bytes=%zu "
        "direct_failure=%u direct_stage=%u direct_rc=0x%08x "
        "direct_bytes=%llu direct_extent=%llu reason=%.240s\n",
        static_cast<long long>(mono_ms), source_sha ? source_sha : "unknown",
        static_cast<unsigned long long>(title_id),
        static_cast<unsigned long long>(attempt), kind ? kind : "unknown",
        unsigned(detailed), unsigned(free_query_ok), largest_free,
        unsigned(direct_failure), direct_stage, direct_rc,
        static_cast<unsigned long long>(direct_bytes),
        static_cast<unsigned long long>(direct_extent), clean_reason);
    if (size <= 0 || static_cast<std::size_t>(size) >= sizeof(line)) return false;
    // The log is application-private and only grows on actual failed sessions.
    // Keep the last 2 MiB without rotating away potentially unique evidence.
    const int file = open(path.c_str(), O_WRONLY | O_CREAT | O_APPEND | O_NOFOLLOW, 0600);
    if (file < 0) return false;
    struct stat info{};
    if (fstat(file, &info) != 0 || !S_ISREG(info.st_mode) ||
        info.st_size < 0 || info.st_size > 2 * 1024 * 1024 - size) {
        (void)close(file);
        return false;
    }
    std::size_t at = 0;
    while (at < static_cast<std::size_t>(size)) {
        const ssize_t written = write(file, line + at, static_cast<std::size_t>(size) - at);
        if (written > 0) at += static_cast<std::size_t>(written);
        else if (written < 0 && errno == EINTR) continue;
        else break;
    }
    const bool synced = at == static_cast<std::size_t>(size) && fsync(file) == 0;
    const bool closed = close(file) == 0;
    return synced && closed;
}
// Crash-only lifecycle breadcrumb: at most a handful of writes per title.
// Retained if the PS5 process exits unexpectedly before C++ stack unwinding.
// Do not sample the GPU, guest memory or per-frame state.
inline bool WriteSessionPhaseReceipt(const std::string& path, const char* source_sha,
                                     std::uint64_t title_id, std::uint64_t attempt,
                                     const char* stage) noexcept {
    if (!stage) return false;
    const auto now_ms = std::chrono::duration_cast<std::chrono::milliseconds>(
        std::chrono::steady_clock::now().time_since_epoch()).count();
    char message[256];
    const int n = std::snprintf(message, sizeof(message),
        "EDEN_SESSION_ACTIVE_V1 mono_ms=%lld sha=%.40s title=%016llx "
        "attempt=%llu stage=%.32s\n",
        static_cast<long long>(now_ms), source_sha ? source_sha : "unknown",
        static_cast<unsigned long long>(title_id),
        static_cast<unsigned long long>(attempt), stage);
    if (n <= 0 || static_cast<std::size_t>(n) >= sizeof(message)) return false;
    // Atomic replacement: a crash *while* writing the next stage must keep
    // the previous complete stage. Never truncate the sole incident marker.
    struct stat prior{};
    if (lstat(path.c_str(), &prior) == 0 && !S_ISREG(prior.st_mode))
        return false;
    char staging[384];
    const int path_size = std::snprintf(staging, sizeof(staging), "%s.next", path.c_str());
    if (path_size <= 0 || static_cast<std::size_t>(path_size) >= sizeof(staging))
        return false;
    const int file = open(staging, O_WRONLY | O_CREAT | O_TRUNC | O_NOFOLLOW, 0600);
    if (file < 0) return false;
    struct stat info{};
    if (fstat(file, &info) != 0 || !S_ISREG(info.st_mode)) {
        (void)close(file);
        return false;
    }
    std::size_t done = 0;
    while (done < static_cast<std::size_t>(n)) {
        const ssize_t count = write(file, message + done, static_cast<std::size_t>(n) - done);
        if (count > 0) done += static_cast<std::size_t>(count);
        else if (count < 0 && errno == EINTR) continue;
        else break;
    }
    const bool synced = done == static_cast<std::size_t>(n) && fsync(file) == 0;
    const bool closed = close(file) == 0;
    if (!synced || !closed || rename(staging, path.c_str()) != 0) {
        (void)unlink(staging);
        return false;
    }
    return true;
}

inline bool ReadPreviousSessionPhase(const std::string& path, char* buffer,
                                     std::size_t capacity) noexcept {
    if (!buffer || capacity < 2) return false;
    buffer[0] = '\0';
    const int file = open(path.c_str(), O_RDONLY | O_NOFOLLOW);
    if (file < 0) return false;
    struct stat info{};
    if (fstat(file, &info) != 0 || !S_ISREG(info.st_mode) ||
        info.st_size <= 0 || info.st_size >= static_cast<off_t>(capacity)) {
        (void)close(file);
        return false;
    }
    const ssize_t n = read(file, buffer, capacity - 1);
    const bool closed = close(file) == 0;
    if (!closed || n != info.st_size) {
        buffer[0] = '\0';
        return false;
    }
    buffer[n] = '\0';
    if (std::strncmp(buffer, "EDEN_SESSION_ACTIVE_V1 ", 23) != 0) {
        buffer[0] = '\0';
        return false;
    }
    // This file is written exclusively from the fixed-format phase helper.
    // Sanitize anyway before including it in a new incident record.
    for (ssize_t i = 0; i < n; ++i)
        if (static_cast<unsigned char>(buffer[i]) < 32) buffer[i] = ' ';
    return true;
}

// A shutdown step with the milliseconds since the previous one (some games take 14-16 s).
inline void ReportStep(const char* stage, const char* message) {
    using Clock = std::chrono::steady_clock;
    static Clock::time_point previous = Clock::now();
    const auto now = Clock::now();
    const auto ms = std::chrono::duration_cast<std::chrono::milliseconds>(now - previous).count();
    previous = now;
    Report(stage, (std::string(message) + " (+" + std::to_string(ms) + " ms)").c_str());
}
}
