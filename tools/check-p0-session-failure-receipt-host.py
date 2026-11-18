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
        false, 0, false, 0, 0, 0));
    assert(read(path) == second);
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
        compilation = subprocess.run(
            [compiler, "-std=c++20", opt, "-Wall", "-Wextra", "-Werror", "-pedantic",
             "-I", str(ROOT / "headless"), str(src), "-o", str(binary)],
            capture_output=True, text=True, timeout=60)
        assert compilation.returncode == 0, (opt, compilation.stdout, compilation.stderr)
        result = subprocess.run([str(binary), str(work)], capture_output=True, text=True, timeout=15)
        assert result.returncode == 0, (opt, result.stdout, result.stderr)

print("P0_SESSION_FAILURE_RECEIPT_HOST_PASS O0=1 O2=1 quiet=1 append=1 kernel_rc=1 title=1 bounded=1 no_symlink=1")
print("This does not prove PS5 native ABI, real FC27 relaunch, NS2 frame or performance.")
