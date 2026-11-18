#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Actual BootTrace OFF -> ON -> OFF -> ON append/retention host contract.

No real PS5 filesystem, title launch or SDK behavior is asserted by this test.
"""
from pathlib import Path
import shutil
import subprocess
import tempfile

R = Path(__file__).resolve().parents[1]
header = (R / "headless/boot_trace.h").read_text()
service = (R / "headless/prosperoeden/eden_services.cpp").read_text()
main = (R / "headless/main.cpp").read_text()
assert header.count("inline bool Resume(const std::string& logs_dir)") == 1
resume = header.split("inline bool Resume(const std::string& logs_dir)", 1)[1].split(
    "inline void Ready(", 1)[0]
for x in ('O_WRONLY | O_CREAT | O_APPEND', 'if (output < 0) return false;',
          'detail::QuietMode() = false;', 'detail::File() = output;'):
    assert x in resume, x
for forbidden in ("O_TRUNC", "std::remove", "std::rename", "boot-trace.prev.txt"):
    assert forbidden not in resume, forbidden
assert "Eden::BootTrace::Resume(Eden::LogsDir())" in service
assert service.index("Eden::BootTrace::Quiet(Eden::LogsDir());") < service.index(
    "Eden::BootTrace::Resume(Eden::LogsDir())")
assert "Eden::BootTrace::Ready(Eden::LogsDir(), Eden::FilesystemAccess());" in main
assert "Eden::Crash::Install(Eden::LogsDir()" in main

cc = shutil.which("clang++") or shutil.which("g++")
assert cc, "C++ compiler required"
cpp = r"""
#include <cassert>
#include <cstdio>
#include <fstream>
#include <string>
#include <sys/types.h>
#include "boot_trace.h"
extern "C" int sceKernelDebugOutText(int, const char*) { return 0; }
extern "C" int sysctlbyname(const char*, void*, size_t*, const void*, size_t) { return -1; }
static std::string read(const std::string& name) {
    std::ifstream f(name);
    return {std::istreambuf_iterator<char>(f), std::istreambuf_iterator<char>()};
}
int main(int argc, char** argv) {
    assert(argc == 2);
    const std::string dir = argv[1];
    const std::string current = dir + "/boot-trace.txt";
    const std::string previous = dir + "/boot-trace.prev.txt";
    { std::ofstream out(current); out << "ORIGINAL\n"; }
    { std::ofstream out(previous); out << "HISTORIC\n"; }
    using namespace Eden::BootTrace;
    assert(!detail::QuietMode());
    Quiet(dir);
    assert(detail::QuietMode() && detail::File() == -1);
    assert(read(current) == "ORIGINAL\n");
    assert(read(previous) == "HISTORIC\n");
    Line("DO_NOT_WRITE");
    assert(Resume(dir));
    assert(!detail::QuietMode() && detail::File() >= 0);
    Line("AFTER_FIRST_ON");
    const auto first = read(current);
    assert(first.starts_with("ORIGINAL\n"));
    assert(first.find("AFTER_FIRST_ON") != std::string::npos);
    assert(first.find("DO_NOT_WRITE") == std::string::npos);
    assert(read(previous) == "HISTORIC\n");
    Quiet(dir);
    assert(detail::QuietMode());
    const auto before_second = read(current);
    assert(Resume(dir));
    Line("AFTER_SECOND_ON");
    const auto second = read(current);
    assert(second.starts_with(before_second));
    assert(second.find("AFTER_SECOND_ON") != std::string::npos);
    assert(read(previous) == "HISTORIC\n");
    Quiet(dir);
    assert(!Resume(dir + "/not-a-real-parent"));
    assert(detail::QuietMode() && detail::File() == -1);
    assert(read(current) == second && read(previous) == "HISTORIC\n");
    return 0;
}
"""
with tempfile.TemporaryDirectory(prefix="eden-boottrace-") as d:
    path = Path(d)
    src = path / "witness.cpp"
    exe = path / "witness"
    src.write_text(cpp)
    for level in ("-O0", "-O2"):
        subprocess.run([cc, "-std=c++20", level, "-Wall", "-Wextra", "-Werror",
                        "-I", str(R / "headless"), str(src), "-o", str(exe)],
                       check=True, timeout=45, capture_output=True, text=True)
        run = subprocess.run([str(exe), d], capture_output=True, text=True, timeout=10)
        if run.returncode:
            raise AssertionError((level, run.returncode, run.stdout, run.stderr))
print("PS5_BOOTTRACE_OFF_ON_HOST_PASS append=1 historical=preserved normal=quiet while_off=1 failed_reopen=quiet O0=1 O2=1")
print("No PS5 filesystem, native build, FC27 relaunch or memory fix is claimed.")
