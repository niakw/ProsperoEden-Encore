#!/usr/bin/env python3
"""Test the production one-shot NS2 loading SVC snapshot without a PS5."""
from pathlib import Path
import shutil
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
graphics = (root / "headless/graphics.cpp").read_text()
header = (root / "headless/ns2_loading_svc_snapshot.h").read_text()
cmake = (root / "headless/CMakeLists.txt").read_text()
assert graphics.count("::Eden::NS2::LoadingSvcSnapshot::Report(10);") == 1
assert graphics.count("::Eden::NS2::LoadingSvcSnapshot::Report(30);") == 1
assert graphics.index("Report(10);") > graphics.index('stage=10s')
assert graphics.index("Report(30);") > graphics.index('stage=30s')
assert graphics.count('#include "ns2_loading_svc_snapshot.h"') == 1
assert graphics.index("Report(10);") < graphics.index("return true;",graphics.index("bool LoadingTick(VideoCore::RendererBase& renderer, bool idle) {"))
assert 'target_include_directories(core BEFORE PUBLIC' in cmake
assert '"${EDEN_NS2_CORE_HELPERS}"' in cmake
assert "SvcTrace::FormatCriticalRecent" in header
assert "SvcTrace::recent_sequence.load(std::memory_order_acquire)" in header
assert "SvcTrace::active_pid.load(std::memory_order_acquire)" in header
assert header.count("std::fprintf(stderr,") == 1
assert "no per-SVC, per-draw or per-present work" in header

sample = r"""
#include <cassert>
#include <cstring>
#include "ns2_loading_svc_snapshot.h"
extern "C" bool eden_native_detailed_logging() noexcept { return true; }
int main() {
    using namespace Eden::NS2;
    SvcTrace::ResetForTitle();
    auto before = LoadingSvcSnapshot::Capture();
    assert(before.pid == 0 && before.traced_count == 0);
    SvcTrace::Register(123);
    std::array<std::uint64_t, 8> args{};
    const auto seq = SvcTrace::RecordRecent(123, 0x29, true, args);
    assert(seq == 1);
    SvcTrace::RecordOutcome(123, seq, 0, 0x9876, 0x12000, 0x34567);
    const auto after = LoadingSvcSnapshot::Capture();
    assert(after.pid == 123 && after.traced_count == 1);
    assert(after.detailed_enabled);
    assert(std::strstr(after.last_critical.data(),"svc=0x29 done") != nullptr);
    LoadingSvcSnapshot::Report(10);
    SvcTrace::Unregister(123);
    const auto later = LoadingSvcSnapshot::Capture();
    assert(later.pid == 0);
    SvcTrace::ResetForTitle();
    assert(LoadingSvcSnapshot::Capture().traced_count == 0);
}
"""
compilers = [shutil.which(c) for c in ("clang++", "g++")]
compilers = [c for c in compilers if c]
assert compilers
with tempfile.TemporaryDirectory(prefix="ns2-svc-loading-snapshot-") as tmp:
    source = Path(tmp) / "test.cpp"
    source.write_text(sample)
    for compiler in compilers:
        for opt in ("-O0", "-O2"):
            binary = Path(tmp) / (Path(compiler).name + opt)
            subprocess.run([
                compiler, "-std=c++20", "-Wall", "-Wextra", "-Werror", "-DPS5_NATIVE=1",
                opt, "-fsanitize=undefined", "-fno-sanitize-recover=all",
                "-I",str(root / "headless"),
                "-I",str(root / "vendor/encore-active/eden/src"),
                str(source), "-o",str(binary)
            ], check=True,timeout=45)
            subprocess.run([str(binary)],check=True,timeout=10)
print("NS2_LOADING_SVC_10S_30S_SNAPSHOT_HOST_PASS per_frame_work=0")
