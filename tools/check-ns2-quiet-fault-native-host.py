#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Host executable of production PS5 fault receipt with selected vendor ring."""
from pathlib import Path
import subprocess, shutil, tempfile

R = Path(__file__).resolve().parents[1]
get = lambda p: (R / p).read_text()
src = get("headless/ns2_fault_receipt.cpp")
cmake = get("headless/CMakeLists.txt")
hdr = get("headless/diagnostics.h")
svc = get("vendor/encore-active/eden/src/core/hle/kernel/svc.cpp")
ring = get("vendor/encore-active/eden/src/core/loader/ns2_svc_trace.h")
std = get("vendor/encore-active/eden-core/src/core/hle/kernel/physical_core_standard.cpp")
dev = get("vendor/encore-active/eden-core/src/core/hle/kernel/physical_core_dev.cpp")
assert '"${EDEN_PORT_DIR}/ns2_fault_receipt.cpp"' in cmake
assert 'SOURCE "${EDEN_PORT_DIR}/ns2_fault_receipt.cpp" APPEND PROPERTY' in cmake
assert 'extern "C" void eden_native_capture_ns2_svc_fault(' in src
assert '"EDEN_NS2_GUEST_FAULT_V1 ' in src
assert "O_WRONLY | O_CREAT | O_APPEND | O_NOFOLLOW" in src
assert "fsync(fd)" in src
assert "EDEN_NATIVE_SOURCE_COMMIT" in src
assert "eden_native_capture_ns2_svc_fault(pid, program_id, fault_pc, fault_lr, fault_sp, last_svc)" in svc
assert '"svc=not_observed"' in svc
assert "RecentSamples = 64" in ring
assert "(!IsHangBoundarySvc(imm) && !DetailedEnabled())" in ring
assert "case 0x18: // WaitSynchronization" in ring
assert "case 0x21: // SendSyncRequest" in ring
assert "case 0x43: // ReplyAndReceive" in ring
assert "Eden::NS2::SvcTrace::IsHangBoundarySvc(imm)" in svc
for source in (std, dev):
    assert "eden_ns2_dump_recent_svc(process->GetProcessId()," in source
    assert "process->GetProgramId(), fault_context.pc," in source
    assert "fault_context.lr, fault_context.sp)" in source
# Earlier R457 emitted *literal* backslash-n, not a line break.
assert r'reason=%.240s\n"' in hdr and r'reason=%.240s\\n"' not in hdr
assert r'stage=%.32s\n"' in hdr and r'stage=%.32s\\n"' not in hdr

cpp = r"""
#include <cassert>
#include <cstdint>
#include <cstdio>
#include <fstream>
#include <iterator>
#include <string>
#include <sys/stat.h>
#include <unistd.h>
namespace Eden::NS2Fault {
bool AppendIncident(const char*, std::uint64_t, std::uint64_t,
                    std::uint64_t, std::uint64_t, std::uint64_t, const char*) noexcept;
}
std::string load(const std::string& name) {
    std::ifstream f(name);
    return {std::istreambuf_iterator<char>(f), std::istreambuf_iterator<char>()};
}
int main(int argc, char** argv) {
    assert(argc == 2);
    const std::string dir = argv[1], path = dir + "/session-failures.log";
    { std::ofstream out(path); out << "history\n"; }
    assert(Eden::NS2Fault::AppendIncident(path.c_str(), 91, 0x0400000000000000ull,
        4, 0, 0x1083d03f80ull, "svc=0x29 done r=0x0 v=0x1000 sp=0x1083d03f40 pc=0x80298004;"));
    const auto a = load(path);
    assert(a.starts_with("history\nEDEN_NS2_GUEST_FAULT_V1 "));
    assert(a.find("sha=abcdef0123456789abcdef0123456789abcdef01") != std::string::npos);
    assert(a.find("pid=91 title=0400000000000000 pc=0x4 lr=0x0 sp=0x1083d03f80") != std::string::npos);
    assert(a.find("svc=0x29 done r=0x0") != std::string::npos && a.back() == '\n');
    assert(Eden::NS2Fault::AppendIncident(path.c_str(), 92, 0, 0x44, 0x88, 0x100,
                                           "svc=not_observed\ninject"));
    const auto b = load(path);
    assert(b.starts_with(a) && b.back() == '\n');
    assert(b.find("\ninject") == std::string::npos);
    const auto guarded = dir + "/guarded", link = dir + "/trap";
    { std::ofstream out(guarded); out << "immutable"; }
    assert(symlink(guarded.c_str(), link.c_str()) == 0);
    assert(!Eden::NS2Fault::AppendIncident(link.c_str(), 9, 0, 4, 0, 1, "x"));
    assert(load(guarded) == "immutable");
    const auto full = dir + "/full";
    { std::ofstream out(full); out << "historical"; }
    assert(truncate(full.c_str(), 2 * 1024 * 1024 + 1) == 0);
    assert(!Eden::NS2Fault::AppendIncident(full.c_str(), 9, 0, 4, 0, 1, "x"));
    assert(load(path) == b);
}
"""
cc = shutil.which("clang++") or shutil.which("g++")
assert cc, "C++20 compiler required"
with tempfile.TemporaryDirectory(prefix="encore-ns2-fault-") as tmp:
    work = Path(tmp)
    source = work / "test.cpp"
    source.write_text(cpp)
    for opt in ("-O0", "-O2"):
        outdir = work / opt.removeprefix("-")
        outdir.mkdir()
        exe = work / ("test" + opt)
        cmd = [cc, "-std=c++20", opt, "-Wall", "-Wextra", "-Werror", "-pedantic",
               "-DPS5_NATIVE=1", '-DEDEN_NATIVE_SOURCE_COMMIT="abcdef0123456789abcdef0123456789abcdef01"',
               "-I", str(R / "headless"), str(R / "headless/ns2_fault_receipt.cpp"),
               str(source), "-o", str(exe)]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        assert result.returncode == 0, (opt, result.stdout, result.stderr)
        result = subprocess.run([str(exe), str(outdir)], capture_output=True, text=True, timeout=15)
        assert result.returncode == 0, (opt, result.stdout, result.stderr)
print("NS2_QUIET_FATAL_NATIVE_HOST_PASS O0=1 O2=1 strong_sink=1 title=1 pc_lr_sp=1 quiet=1 bounded=1")
print("No native SDK link or PS5 console game validation.")
