#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Host C++ test of the *real* quiet PS5 session-failure recorder.

Covers lost evidence under Detailed Logging OFF, bounded append-only
incident storage and direct-memory kernel rc/size provenance. Not PS5 runtime.
"""
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
read = lambda p: (ROOT / p).read_text(encoding="utf-8")
record = read("headless/diagnostics.h")
main = read("headless/main.cpp")
native = read("src/memory_pages.cpp")
assert "inline bool WriteSessionFailureReceipt(" in record
assert "O_WRONLY | O_CREAT | O_APPEND | O_NOFOLLOW" in record
assert "EDEN_SESSION_FAILURE_V1" in record
assert "inline bool WriteSessionBoundaryReceipt(" in record
assert "EDEN_SESSION_BOUNDARY_V1" in record
assert "2U * 1024U * 1024U" in record
assert "O_WRONLY | O_CREAT | O_APPEND | O_NOFOLLOW" in record
assert 'record_session_boundary("title_resolved");' in main
assert 'record_session_boundary("system_run_returned");' in main
assert 'record_session_boundary("title_destroyed");' in main
assert 'Eden::NativeLogs::Generation()' in main
assert 'active_session_stage' in main
assert "inline bool WriteSessionPhaseReceipt(" in record
assert "inline bool ReadPreviousSessionPhase(" in record
assert "EDEN_SESSION_ACTIVE_V1" in record
assert "O_WRONLY | O_CREAT | O_TRUNC | O_NOFOLLOW" in record
phase_body = record.split("inline bool WriteSessionPhaseReceipt(", 1)[1].split(
    "inline bool ReadPreviousSessionPhase(", 1)[0]
assert 'lstat(path.c_str(), &prior)' in phase_body
assert 'std::snprintf(staging, sizeof(staging), "%s.next", path.c_str())' in phase_body
assert 'rename(staging, path.c_str())' in phase_body
assert phase_body.index('fsync(file)') < phase_body.index('rename(staging, path.c_str())')
assert 'unlink(staging)' in phase_body
for marker in (
    '"previous_session_unfinished"',
    '"selected"', '"title_resolved"', '"guest_loading"', '"gpu_starting"',
    '"guest_running"', '"guest_stopping"', '"renderer_release"', '"title_destroyed"',
    'SCOPE_EXIT {',
    'if (session_marker_owned) (void)std::remove(unfinished_session_path.c_str());',
):
    assert marker in main, marker
assert main.index('ReadPreviousSessionPhase(') < main.index('Eden::StopLimit::Start(stop_note);')

assert "fsync(file)" in record
assert "2 * 1024 * 1024 - size" in record
assert "eden_ps5_direct_failure_snapshot(" in main and "eden_ps5_direct_failure_snapshot(" in native
assert "const std::uint64_t direct_failure_baseline = eden_ps5_direct_failure_snapshot(" in main
assert "sequence > direct_failure_baseline" in main
assert "++session_failure_attempt;" in main
assert "incident_title_id = launch_title_id;" in main
assert 'Eden::LogFile("session-failures.log")' in main
assert 'capture_session_failure("std_bad_alloc"' in main
assert 'capture_session_failure("std_exception"' in main
assert 'Eden::NativeLogs::Detailed(), largest_ok, largest,' in main
assert "NoteDirectAllocationFailure(1, static_cast<std::uint32_t>(rc), total," in native
assert "NoteDirectAllocationFailure(2, static_cast<std::uint32_t>(rc), total," in native
assert "NoteDirectAllocationFailure(3, EINVAL, size, 0);" in native
assert "std::atomic_flag gate = ATOMIC_FLAG_INIT" in native
assert "record.gate.test_and_set(std::memory_order_acquire)" in native
assert "record.gate.clear(std::memory_order_release)" in native
assert "src/memory_pages.cpp" in read("headless/CMakeLists.txt") or "memory_pages.cpp" in read("headless/CMakeLists.txt")

cpp = r"""
#include <cassert>
#include <cstdint>
#include <fstream>
#include <iterator>
#include <string>
#include <sys/stat.h>
#include <unistd.h>
#include "diagnostics.h"

static std::string read(const std::string& file) {
    std::ifstream f(file);
    return {std::istreambuf_iterator<char>(f), std::istreambuf_iterator<char>()};
}
int main(int argc, char** argv) {
    assert(argc == 2);
    const std::string dir = argv[1];
    const std::string path = dir + "/session-failures.log";
    const std::string history = "older incident must survive\n";
    {
        std::ofstream out(path);
        out << history;
    }
    assert(Eden::WriteSessionFailureReceipt(
        path, "0123456789abcdef0123456789abcdef01234567",
        0x0100000000000123ull, 2, "std_exception",
        "Backing allocation: Cannot allocate memory\nmultiline",
        false, true, 127 * 1024 * 1024ull, true, 1, 0x80020023,
        4297064448ull, 13019119616ull));
    const auto first = read(path);
    assert(first.starts_with(history));
    assert(first.find("EDEN_SESSION_FAILURE_V1") != std::string::npos);
    assert(first.find("title=0100000000000123") != std::string::npos);
    assert(first.find("attempt=2") != std::string::npos);
    assert(first.find("detailed=0") != std::string::npos);
    assert(first.find("direct_failure=1 direct_stage=1 direct_rc=0x80020023") != std::string::npos);
    assert(first.find("direct_bytes=4297064448 direct_extent=13019119616") != std::string::npos);
    assert(first.find("reason=Backing allocation: Cannot allocate memory multiline") != std::string::npos);
    assert(Eden::WriteSessionFailureReceipt(
        path, "unknown", 4, 3, "std_bad_alloc", "heap exceeded", true,
        false, 0, false, 0, 0, 0, 0));
    const auto second = read(path);
    assert(second.starts_with(first));
    assert(second.find("detailed=1 largest_query_ok=0 largest_free_bytes=0") != std::string::npos);
    assert(second.find("direct_failure=0") != std::string::npos);
    // No GPU/frame I/O: two lifecycle boundaries are explicit, durable and
    // independent of detailed logging. The preceding game survives relaunch.
    const std::string boundaries = dir + "/session-boundaries.log";
    assert(Eden::WriteSessionBoundaryReceipt(
        boundaries, "0123456789abcdef0123456789abcdef01234567",
        0x0400c3f00006e000ull, 1, "title_destroyed", 150000,
        false, 3, true, 10ull * 1024 * 1024 * 1024, 1200, 1));
    assert(Eden::WriteSessionBoundaryReceipt(
        boundaries, "0123456789abcdef0123456789abcdef01234567",
        0x0400c3f00006e000ull, 2, "title_resolved", 1,
        true, 4, true, 9ull * 1024 * 1024 * 1024, 1200, 0));
    const auto b = read(boundaries);
    assert(b.find("EDEN_SESSION_BOUNDARY_V1") != std::string::npos);
    assert(b.find("attempt=1 phase=title_destroyed") != std::string::npos);
    assert(b.find("attempt=2 phase=title_resolved") != std::string::npos);
    assert(b.find("detailed=0 logging_generation=3") != std::string::npos);
    assert(b.find("detailed=1 logging_generation=4") != std::string::npos);
    assert(b.find("gpu_completed=1200 gpu_stall_suspicions=1") != std::string::npos);
    const std::string boundary_link = dir + "/boundary-trap";
    assert(symlink(boundaries.c_str(), boundary_link.c_str()) == 0);
    assert(!Eden::WriteSessionBoundaryReceipt(
        boundary_link, "unknown", 0, 3, "fault", 0, false, 0, false, 0, 0, 0));
    assert(read(boundaries) == b);
    const std::string boundary_full = dir + "/boundary-full";
    { std::ofstream out(boundary_full); out << "historical"; }
    assert(truncate(boundary_full.c_str(), 2 * 1024 * 1024 + 1) == 0);
    assert(!Eden::WriteSessionBoundaryReceipt(
        boundary_full, "unknown", 0, 3, "fault", 0, false, 0, false, 0, 0, 0));
    struct stat st{};
    assert(stat(path.c_str(), &st) == 0 && S_ISREG(st.st_mode));
    // Logging failure must not follow an attacker-controlled symlink.
    const std::string target = dir + "/historical";
    { std::ofstream out(target); out << "immutable"; }
    const std::string link = dir + "/trap";
    assert(symlink(target.c_str(), link.c_str()) == 0);
    assert(!Eden::WriteSessionFailureReceipt(
        link, "unknown", 0, 4, "std_exception", "x", false,
        false, 0, false, 0, 0, 0, 0));
    assert(read(target) == "immutable");
    // A corrupt run that repeatedly fails may not fill the user partition.
    const std::string full = dir + "/full";
    { std::ofstream out(full); out << "historical"; }
    assert(truncate(full.c_str(), 2 * 1024 * 1024 + 1) == 0);
    assert(!Eden::WriteSessionFailureReceipt(
        full, "unknown", 0, 5, "std_exception", "x", false,
        false, 0, false, 0, 0, 0, 0));
    assert(read(path) == second);
    const std::string active = dir + "/session-active.txt";
    assert(Eden::WriteSessionPhaseReceipt(
        active, "0123456789abcdef0123456789abcdef01234567",
        0x0400c3f00006e000ull, 42, "guest_loading"));
    char previous[256]{};
    assert(Eden::ReadPreviousSessionPhase(active, previous, sizeof(previous)));
    assert(std::string(previous).find("title=0400c3f00006e000") != std::string::npos);
    assert(std::string(previous).find("attempt=42 stage=guest_loading") != std::string::npos);
    assert(Eden::WriteSessionPhaseReceipt(
        active, "0123456789abcdef0123456789abcdef01234567",
        0x0400c3f00006e000ull, 42, "gpu_starting"));
    assert(Eden::ReadPreviousSessionPhase(active, previous, sizeof(previous)));
    assert(std::string(previous).find("stage=gpu_starting") != std::string::npos);
    // Each atomic stage update leaves no temporary file on success.
    assert(access((active + ".next").c_str(), F_OK) != 0);
    assert(std::string(previous).find("stage=guest_loading") == std::string::npos);
    assert(!Eden::WriteSessionPhaseReceipt(
        link, "unknown", 4, 42, "guest_running"));
    assert(!Eden::ReadPreviousSessionPhase(link, previous, sizeof(previous)));
    assert(read(target) == "immutable");
    // Clean C++ shutdown removes the marker, so only an interrupted session
    // is imported during the next launcher process boot.
    assert(std::remove(active.c_str()) == 0);
    assert(!Eden::ReadPreviousSessionPhase(active, previous, sizeof(previous)));
}
"""
compiler = shutil.which("clang++") or shutil.which("g++")
assert compiler, "C++20 compiler required"
with tempfile.TemporaryDirectory(prefix="encore-p0-receipt-") as tmp:
    work = Path(tmp)
    src = work / "test.cpp"
    binary = work / "test"
    src.write_text(cpp, encoding="utf-8")
    for opt in ("-O0", "-O2"):
        # The O2 witness must start with an independent filesystem: the O0
        # case intentionally leaves an attacker-controlled symlink behind.
        test_dir = work / opt.removeprefix("-")
        test_dir.mkdir()
        compilation = subprocess.run(
            [compiler, "-std=c++20", opt, "-Wall", "-Wextra", "-Werror", "-pedantic",
             "-I", str(ROOT / "headless"), str(src), "-o", str(binary)],
            capture_output=True, text=True, timeout=60)
        assert compilation.returncode == 0, (opt, compilation.stdout, compilation.stderr)
        result = subprocess.run([str(binary), str(test_dir)], capture_output=True, text=True, timeout=15)
        assert result.returncode == 0, (opt, result.stdout, result.stderr)

# Exercise the production lock-free/no-heap failure snapshot extracted from
# the actual allocator source, not an independently reimplemented test double.
state_start = native.index("struct LastDirectAllocationFailure {")
state_end = native.index("std::atomic<std::int64_t> cached_direct_memory_extent{0};", state_start)
snap_start = native.index('extern "C" std::uint64_t eden_ps5_direct_failure_snapshot(')
snap_end = native.index("\n#endif\n\nnamespace Common {", snap_start)
allocator_fixture = (
    "#include <atomic>\n#include <cassert>\n#include <cstdint>\n"
    "namespace {\n" + native[state_start:state_end] + "}\n" +
    native[snap_start:snap_end] + """
int main() {
    std::uint64_t bytes = 7, extent = 7;
    std::uint32_t rc = 7, stage = 7;
    const auto before = eden_ps5_direct_failure_snapshot(&bytes, &extent, &rc, &stage);
    assert(before == 0 && bytes == 0 && extent == 0 && rc == 0 && stage == 0);
    NoteDirectAllocationFailure(1, 0x80020023u, 4297064448ull, 13019119616ull);
    const auto one = eden_ps5_direct_failure_snapshot(&bytes, &extent, &rc, &stage);
    assert(one == 1 && stage == 1 && rc == 0x80020023u);
    assert(bytes == 4297064448ull && extent == 13019119616ull);
    NoteDirectAllocationFailure(2, 0x80020104u, 262144ull, 13019119616ull);
    const auto two = eden_ps5_direct_failure_snapshot(&bytes, &extent, &rc, &stage);
    assert(two == 2 && stage == 2 && rc == 0x80020104u);
    assert(bytes == 262144ull && extent == 13019119616ull);
    // A fresh title records its baseline sequence and cannot report a
    // previous title's last failed allocation as this title's kernel RC.
    const auto next_title_baseline = two;
    const auto now = eden_ps5_direct_failure_snapshot(&bytes, &extent, &rc, &stage);
    assert(now == next_title_baseline);
    NoteDirectAllocationFailure(3, 22u, 0ull, 0ull);
    const auto three = eden_ps5_direct_failure_snapshot(&bytes, &extent, &rc, &stage);
    assert(three > next_title_baseline && stage == 3 && rc == 22u);
    return 0;
}
""")
with tempfile.TemporaryDirectory(prefix="encore-p0-allocator-") as temp:
    root = Path(temp)
    fixture = root / "allocator.cpp"
    binary = root / "allocator"
    fixture.write_text(allocator_fixture, encoding="utf-8")
    for opt in ("-O0", "-O2"):
        compiled = subprocess.run([compiler, "-std=c++20", opt, "-Wall", "-Wextra",
                                   "-Werror", str(fixture), "-o", str(binary)],
                                  capture_output=True, text=True, timeout=60)
        assert compiled.returncode == 0, (opt, compiled.stderr)
        run = subprocess.run([str(binary)], capture_output=True, text=True, timeout=10)
        assert run.returncode == 0, (opt, run.stderr)

print("P0_SESSION_FAILURE_RECEIPT_HOST_PASS O0=1 O2=1 quiet=1 append=1 kernel_rc=1 allocator_real=1 lifecycle_atomic=1 boundaries=1 relaunch=1 title=1 bounded=1 no_symlink=1")
print("This does not prove PS5 native ABI, real FC27 relaunch, NS2 frame or performance.")
