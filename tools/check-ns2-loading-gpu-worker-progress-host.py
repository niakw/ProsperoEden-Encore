#!/usr/bin/env python3
"""Source-extracted GPU-worker progress witness for NS2 first-frame loading.

The 64-command crash breadcrumb measures completed GPU worker commands, not
guest GPFIFO entries, QMD submits, CPU retirement or guest first-present.
Only two existing loading milestones sample it; there is no per-frame
GPU atomic read or new stderr logging.
"""
from __future__ import annotations

from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
graphics = (ROOT / "headless/graphics.cpp").read_text()
crash = (ROOT / "headless/crash_report.h").read_text()
watchdog = (ROOT / "headless/stall_watchdog.h").read_text()
gpu_owner = (ROOT / "tools/check-native-gpu-thread.py").read_text()

assert "#ifdef EDEN_PS5_VULKAN\n#include \"crash_report.h\"\n#endif" in graphics
assert "inline std::atomic<std::uint64_t> gpu_completed_commands{0};" in crash
assert "::Eden::Crash::gpu_completed_commands.fetch_add(64" in gpu_owner
assert "Crash::gpu_completed_commands.load(std::memory_order_relaxed)" in watchdog
assert graphics.count("gpu_worker_completed_floor64=") == 2
assert graphics.count("gpu_worker_delta_floor64=") == 2
assert graphics.count("gpu_worker_counter_reset=") == 2

start = graphics.index("struct LoadingGpuProgress {")
end = graphics.index("\n#endif\nLoadingPace vulkan_loading_pace;", start)
helper = graphics[start:end]
assert helper.count("Crash::gpu_completed_commands.load(std::memory_order_relaxed)") == 1
assert "current < vulkan_loading_gpu_completion_baseline" in helper
assert "reset ? 0 : current - vulkan_loading_gpu_completion_baseline" in helper

loading = graphics.split("bool LoadingTick(VideoCore::RendererBase& renderer, bool idle) {", 1)[1].split(
    "GraphicsWindow::GraphicsWindow(bool use_vulkan)", 1)[0]
for milestone in ("10s", "30s"):
    assert loading.count(f"EDEN_VULKAN_LOADING_WAIT stage={milestone}") == 1
assert loading.count("const auto gpu = SampleLoadingGpuProgress();") == 2
assert loading.count("std::fprintf(stderr,") == 2
assert loading.index("const auto gpu = SampleLoadingGpuProgress();") > loading.index(
    "vulkan_loading_diagnostic_stage == 0 && elapsed >= 10.0")
# The two snapshots may only happen on the milestone branches, not on
# every jacket draw or inside PresentVulkanLoading.
outside = loading.split("if (vulkan_loading_diagnostic_stage == 0 && elapsed >= 10.0)", 1)[0]
assert "SampleLoadingGpuProgress()" not in outside
assert "PresentVulkanLoading(renderer);" in outside
assert "guest_frame_handoff=0" in loading

ctor = graphics.split("GraphicsWindow::GraphicsWindow(bool use_vulkan)", 1)[1].split(
    "GraphicsWindow::~GraphicsWindow()", 1)[0]
assert ctor.count("vulkan_loading_gpu_completion_baseline =") == 1
assert ctor.index("vulkan_loading_diagnostic_stage = 0;") < ctor.index(
    "vulkan_loading_gpu_completion_baseline =")
assert ctor.index("vulkan_loading_gpu_completion_baseline =") < ctor.index(
    "vulkan_loading_pace = {};")
assert "Crash::gpu_completed_commands.store(" not in ctor, (
    "A title transition must not clear the signal/crash breadcrumb.")

cpp = r"""
#include <atomic>
#include <cstdint>
#include <cassert>
namespace Crash {
inline std::atomic<std::uint64_t> gpu_completed_commands{0};
}
std::uint64_t vulkan_loading_gpu_completion_baseline{};
""" + helper + r"""
int main() {
    Crash::gpu_completed_commands.store(128);
    vulkan_loading_gpu_completion_baseline = 128;
    auto a = SampleLoadingGpuProgress();
    assert(a.total_floor64 == 128 && a.since_window_floor64 == 0 && !a.counter_reset);
    Crash::gpu_completed_commands.store(192);
    a = SampleLoadingGpuProgress();
    assert(a.total_floor64 == 192 && a.since_window_floor64 == 64 && !a.counter_reset);
    Crash::gpu_completed_commands.store(320);
    a = SampleLoadingGpuProgress();
    assert(a.since_window_floor64 == 192 && !a.counter_reset);
    // A second game in this app gets a new baseline, not stale GPU work.
    vulkan_loading_gpu_completion_baseline = 320;
    a = SampleLoadingGpuProgress();
    assert(a.since_window_floor64 == 0 && !a.counter_reset);
    Crash::gpu_completed_commands.store(384);
    a = SampleLoadingGpuProgress();
    assert(a.since_window_floor64 == 64 && !a.counter_reset);
    // A future counter reset must not wrap into a huge unsigned delta.
    Crash::gpu_completed_commands.store(16);
    a = SampleLoadingGpuProgress();
    assert(a.total_floor64 == 16 && a.since_window_floor64 == 0 && a.counter_reset);
    vulkan_loading_gpu_completion_baseline = 16;
    a = SampleLoadingGpuProgress();
    assert(a.since_window_floor64 == 0 && !a.counter_reset);
}
"""
compiler = shutil.which("clang++") or shutil.which("g++")
assert compiler, "C++20 compiler is required for extracted source test"
with tempfile.TemporaryDirectory(prefix="ns2-loading-gpu-progress-") as td:
    src = Path(td) / "probe.cpp"
    exe = Path(td) / "probe"
    src.write_text(cpp)
    subprocess.run([compiler, "-std=c++20", "-O1", "-Wall", "-Wextra",
                    "-Werror", "-fsanitize=address,undefined",
                    "-fno-omit-frame-pointer", str(src), "-o", str(exe)],
                   check=True, timeout=35)
    subprocess.run([str(exe)], check=True, timeout=20)
print("NS2_LOADING_GPU_PROGRESS_HOST_PASS samples=7 "
      "window_reset=1 wraps_rejected=1 first_guest_frame=unverified")
