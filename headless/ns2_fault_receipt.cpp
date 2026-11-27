// SPDX-License-Identifier: GPL-3.0-or-later
// NS2 guest-fault evidence survives when the user switches Detailed Logs OFF.
// This translation unit is linked into the actual PS5 frontend; it does not
// allocate, enumerate guest memory, block a guest frame, or modify emulation.
#include "storage_paths.h"

#include <cerrno>
#include <chrono>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <fcntl.h>
#include <sys/stat.h>
#include <unistd.h>

namespace Eden::NS2Fault {
inline constexpr std::size_t MaxBytes = 2U * 1024U * 1024U;

bool AppendIncident(const char* path, std::uint64_t pid, std::uint64_t program_id,
                    std::uint64_t pc, std::uint64_t lr, std::uint64_t sp,
                    const char* critical_svc) noexcept {
    if (!path || !*path || !critical_svc) return false;

    // Avoid arbitrary multiline output or embedded control characters in a
    // guest-derived diagnostic. The vendor supplies a bounded 240-byte buffer.
    char clean_svc[221]{};
    std::size_t n = 0;
    for (; critical_svc[n] && n + 1 < sizeof(clean_svc); ++n) {
        const unsigned char ch = static_cast<unsigned char>(critical_svc[n]);
        clean_svc[n] = ch < 32 || ch == 127 ? ' ' : static_cast<char>(ch);
    }

#ifdef EDEN_NATIVE_SOURCE_COMMIT
    constexpr const char* source_sha = EDEN_NATIVE_SOURCE_COMMIT;
#else
    constexpr const char* source_sha = "unknown";
#endif
    const auto monotonic_ms = std::chrono::duration_cast<std::chrono::milliseconds>(
        std::chrono::steady_clock::now().time_since_epoch()).count();
    char line[512]{};
    const int length = std::snprintf(line, sizeof(line),
        "EDEN_NS2_GUEST_FAULT_V1 mono_ms=%lld sha=%.40s pid=%llu title=%016llx "
        "pc=0x%llx lr=0x%llx sp=0x%llx svc=%.220s\n",
        static_cast<long long>(monotonic_ms), source_sha,
        static_cast<unsigned long long>(pid),
        static_cast<unsigned long long>(program_id),
        static_cast<unsigned long long>(pc),
        static_cast<unsigned long long>(lr),
        static_cast<unsigned long long>(sp), clean_svc);
    if (length <= 0 || static_cast<std::size_t>(length) >= sizeof(line)) return false;

    // This is a fatal-guest-branch-only OS write. The game does not enter
    // this path on SVC dispatch, normal memory allocation or successful frames.
    const int fd = open(path, O_WRONLY | O_CREAT | O_APPEND | O_NOFOLLOW, 0600);
    if (fd < 0) return false;
    struct stat st{};
    if (fstat(fd, &st) != 0 || !S_ISREG(st.st_mode) || st.st_size < 0 ||
        static_cast<std::uint64_t>(st.st_size) >
            MaxBytes - static_cast<std::size_t>(length)) {
        (void)close(fd);
        return false;
    }
    std::size_t written = 0;
    while (written < static_cast<std::size_t>(length)) {
        const ssize_t count = write(fd, line + written,
                                    static_cast<std::size_t>(length) - written);
        if (count > 0) written += static_cast<std::size_t>(count);
        else if (count < 0 && errno == EINTR) continue;
        else break;
    }
    const bool saved = written == static_cast<std::size_t>(length) && fsync(fd) == 0;
    const bool closed = close(fd) == 0;
    return saved && closed;
}
} // namespace Eden::NS2Fault

#ifdef PS5_NATIVE
// Strong C symbol paired with the optional weak callback from the selected
// canonical vendor eden/src/core/hle/kernel/svc.cpp. The same path is
// used by P0 recoverable OOM and previous-launch interruption receipts.
extern "C" void eden_native_capture_ns2_svc_fault(
    std::uint64_t pid, std::uint64_t program_id, std::uint64_t fault_pc,
    std::uint64_t fault_lr, std::uint64_t fault_sp,
    const char* critical_svc) noexcept {
    constexpr const char* elevated = "/data/prosperoeden/logs/session-failures.log";
    constexpr const char* sandbox = "/download0/eden-headless-g7/session-failures.log";
    (void)Eden::NS2Fault::AppendIncident(
        Eden::FilesystemAccess() ? elevated : sandbox,
        pid, program_id, fault_pc, fault_lr, fault_sp, critical_svc);
}
#endif
