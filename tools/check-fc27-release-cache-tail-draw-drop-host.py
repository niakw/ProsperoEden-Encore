#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Compile the actual release-facing FC27 cache-tail/draw-drop snapshots on host.

These are read-only windows over counters that already exist on the cache-lock
and graphics-pipeline paths. They identify lost draws and individual long lock
waits; they do NOT prove a game-FPS improvement or the cause of a HUD stall.
"""
from pathlib import Path
import shutil
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
graphics = (root / "headless/graphics.cpp").read_text(encoding="utf-8")
header = (root / "headless/graphics.h").read_text(encoding="utf-8")
performance = (root / "headless/performance.h").read_text(encoding="utf-8")
start = "using FrameCacheTailNumbers = std::array<unsigned long long, 4>;"
end = "\n#ifdef EDEN_DEV_PROFILE\n// Diagnostic-only:"
assert graphics.count(start) == graphics.count(end) == 1
actual = graphics.split(start, 1)[1].split(end, 1)[0]
actual = start + actual
for value in (
    "frame_cache_tail_previous = CaptureFrameCacheTail();",
    "frame_draw_drop_previous = CaptureFrameDrawDrops();",
    "const auto cache_tail_now = CaptureFrameCacheTail();",
    "const auto drop_now = CaptureFrameDrawDrops();",
    "cache_tail_delta[i] = cache_tail_now[i] - frame_cache_tail_previous[i];",
    "drop_delta[i] = drop_now[i] - frame_draw_drop_previous[i];",
    "frame_cache_tail_previous = cache_tail_now;",
    "frame_draw_drop_previous = drop_now;",
    "EDEN_FRAME_CACHE_TAIL frame=%u domain=%s",
    "EDEN_FRAME_DRAW_DROP frame=%u reason=%s",
    "scope=measured_guest_waits",
    "scope=existing_gpu_counters",
):
    assert graphics.count(value) == 1, value
for value in (
    "std::array<unsigned long long, 4> frame_cache_tail_previous{};",
    "std::array<unsigned long long, 5> frame_draw_drop_previous{};",
):
    assert header.count(value) == 1, value
for value in ("waited_ge1ms", "waited_ge10ms", "max_wait_ns",
              "graphics_draw_drop_totals", "RecordGraphicsDrawDrop("):
    assert value in performance, value
# In ordinary gameplay the fast path does not capture a snapshot per draw or
# per present. It is only in the existing once/5s detailed report.
assert graphics.index("const auto cache_tail_now = CaptureFrameCacheTail();") > graphics.index(
    "const auto pressure_now = CaptureFramePressure();")
assert graphics.index("const auto drop_now = CaptureFrameDrawDrops();") < graphics.index(
    "bool pressure_valid = frame_pressure_was_detailed")
assert graphics.count("CaptureFrameCacheTail();") == 2  # initialize / report
assert graphics.count("CaptureFrameDrawDrops();") == 2
assert "frame_pressure_logging_generation == report_logging_generation" in graphics
assert "for (std::size_t i = 0; pressure_valid && i < cache_tail_delta.size();" in graphics
assert "for (std::size_t i = 0; pressure_valid && i < drop_delta.size();" in graphics

mock = r"""
#include <array>
#include <atomic>
#include <cassert>
#include <cstdint>
#include <cstddef>
namespace Eden::Performance {
struct GuestCacheDomainTotals {
  std::atomic<unsigned long long> waited_ge1ms{}, waited_ge10ms{}, max_wait_ns{};
};
inline std::array<GuestCacheDomainTotals, 2> guest_cache_domain_totals{};
enum class GraphicsDrawDrop : unsigned {
 NoPipeline, ConfigureRejected, BuiltPipelineFailed, DescriptorBufferFull,
 WorkerPipelineFailed, Count
};
inline std::array<std::atomic<unsigned long long>,5> graphics_draw_drop_totals{};
}
""" + actual + r"""
int main() {
  auto old_tail = CaptureFrameCacheTail();
  auto old_drop = CaptureFrameDrawDrops();
  for (auto n : old_tail) assert(n == 0);
  for (auto n : old_drop) assert(n == 0);
  auto& buffer = Eden::Performance::guest_cache_domain_totals[0];
  auto& texture = Eden::Performance::guest_cache_domain_totals[1];
  buffer.waited_ge1ms.store(5);
  buffer.waited_ge10ms.store(2);
  texture.waited_ge1ms.store(3);
  texture.waited_ge10ms.store(0);
  Eden::Performance::graphics_draw_drop_totals[0].store(4);
  Eden::Performance::graphics_draw_drop_totals[3].store(1);
  auto tail = CaptureFrameCacheTail();
  auto drop = CaptureFrameDrawDrops();
  assert(tail[0]-old_tail[0] == 5 && tail[1]-old_tail[1] == 2);
  assert(tail[2]-old_tail[2] == 3 && tail[3]-old_tail[3] == 0);
  assert(drop[0]-old_drop[0] == 4 && drop[3]-old_drop[3] == 1);
  buffer.waited_ge1ms.store(0); // another title resets counters
  old_tail = tail;
  tail = CaptureFrameCacheTail();
  assert(tail[0] < old_tail[0]); // caller must reject/reset mixed window
  for (std::size_t i=0;i<5;i++) Eden::Performance::graphics_draw_drop_totals[i].store(0);
  assert(CaptureFrameDrawDrops()[0] == 0);
  return 0;
}
"""
compiler = shutil.which("clang++-18") or shutil.which("clang++") or shutil.which("g++")
assert compiler, "Host C++ compiler is required"
with tempfile.TemporaryDirectory(prefix="encore-fc27-release-observation-") as d:
    source = Path(d) / "frame.cpp"
    binary = Path(d) / "frame"
    source.write_text(mock, encoding="utf-8")
    for optimize in ("-O0", "-O2"):
        subprocess.run([compiler, "-std=c++20", optimize, "-Wall", "-Wextra",
                        "-Werror", str(source), "-o", str(binary)],
                       check=True, capture_output=True, text=True, timeout=30)
        subprocess.run([str(binary)], check=True, timeout=10)
print("FC27_RELEASE_CACHE_TAIL_DRAW_DROP_HOST_PASS existing_counters=1 release_windows=1 O0=1 O2=1 resets=1 quiet_hotpath=unchanged")
print("No console performance or HUD correctness is claimed by this diagnostic gate.")
