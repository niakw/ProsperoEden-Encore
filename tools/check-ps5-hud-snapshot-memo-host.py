#!/usr/bin/env python3
"""Source-linked Vulkan HUD memo witness: no repeated glyph conversion per frame.

Host-only C++20 regression. Does not estimate GPU frame-time savings.
"""
from pathlib import Path
import shutil
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
source = (root / "headless/graphics.cpp").read_text()
header = (root / "headless/hud.h").read_text()
assert source.count("HudSnapshotMemo vulkan_hud_memo;") == 1
assert source.count("vulkan_hud_memo.Reset();") == 1
guard = "if (vulkan_hud_memo.RefreshNeeded(vulkan_hud_clock, vulkan_hud_speed))"
draw = "vulkan_hud = MakeHudSnapshot(vulkan_hud_clock, vulkan_hud_speed);"
assert source.count(guard) == source.count(draw) == 1
assert source.index(guard) < source.index(draw)
assert source.index("vulkan_hud_memo.Reset();") < source.index(guard)
assert "struct HudSnapshotMemo" in header
assert "if (valid && fps == clock.fps && worst_ms == clock.worst_ms &&" in header
assert "speed == current_speed) return false;" in header
compiler = shutil.which("clang++-18") or shutil.which("clang++") or shutil.which("g++")
assert compiler, "C++20 host compiler is required"
fixture = r"""
#include "hud.h"
#include <cassert>
#include <limits>
#include <string_view>
int main() {
    Eden::HudSnapshotMemo memo{};
    Eden::HudClock clock{};
    double speed = 100.0;
    assert(memo.RefreshNeeded(clock, speed));
    auto current = Eden::MakeHudSnapshot(clock, speed);
    assert(current.glyphs == Eden::HudText("VLK F-- S-- W--"));
    for (int i = 0; i < 50000; ++i)
        assert(!memo.RefreshNeeded(clock, speed));
    clock.Present(1.0);
    assert(!memo.RefreshNeeded(clock, speed));
    clock.fps = 30.0;
    assert(memo.RefreshNeeded(clock, speed));
    current = Eden::MakeHudSnapshot(clock, speed);
    assert(current.glyphs == Eden::HudText("VLK F30 S100 W0"));
    assert(!memo.RefreshNeeded(clock, speed));
    clock.worst_ms = 200.0;
    assert(memo.RefreshNeeded(clock, speed));
    current = Eden::MakeHudSnapshot(clock, speed);
    assert(current.glyphs == Eden::HudText("VLK F30 S100 W200"));
    assert(!memo.RefreshNeeded(clock, speed));
    speed = 80.0;
    assert(memo.RefreshNeeded(clock, speed));
    current = Eden::MakeHudSnapshot(clock, speed);
    assert(current.glyphs == Eden::HudText("VLK F30 S80 W200"));
    assert(!memo.RefreshNeeded(clock, speed));
    // A new game must replace the previous title's loading snapshot.
    memo.Reset();
    assert(memo.RefreshNeeded(clock, speed));
    assert(!memo.RefreshNeeded(clock, speed));
    // NaN never appears as an unchanged stable cache key.
    clock.fps = std::numeric_limits<double>::quiet_NaN();
    assert(memo.RefreshNeeded(clock, speed));
    assert(memo.RefreshNeeded(clock, speed));
}
"""
with tempfile.TemporaryDirectory(prefix="eden-hud-memo-") as tmp:
    file = Path(tmp) / "hud.cpp"
    file.write_text(fixture)
    for opt in ("0", "2", "3"):
        binary = Path(tmp) / ("hud-" + opt)
        flags = [compiler, "-std=c++20", "-O" + opt,
                 "-Wall", "-Wextra", "-Werror", "-pedantic",
                 "-fsanitize=address,undefined", "-fno-sanitize-recover=all",
                 "-I" + str(root / "headless"), str(file), "-o", str(binary)]
        result = subprocess.run(flags, capture_output=True, text=True, timeout=60)
        assert result.returncode == 0, (opt, result.stderr[-3000:])
        result = subprocess.run([str(binary)], capture_output=True, text=True, timeout=30)
        assert result.returncode == 0, (opt, result.stderr[-3000:])
print("PS5_VULKAN_HUD_SNAPSHOT_MEMO_PASS O0_O2_O3=1 sanitizer=asan_ubsan repeated=50000 session_reset=1")
