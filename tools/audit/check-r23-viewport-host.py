#!/usr/bin/env python3
"""R23 AB-11: static exact-source and source-extracted viewport math regression.

Checks pinned original SHA and the only maintained generator hunk, then
compiles/runs the C++ lower-left viewport block under ASan/UBSan.
This is not Vulkan SPIR-V, native PS5 compile, WSI, or on-console proof.
"""
from __future__ import annotations
import ast
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
PINNED = ROOT / "vendor/sources/eden/src/video_core/renderer_vulkan/vk_rasterizer.cpp"
GENERATE = ROOT / "tools/prepare-vulkan-port.py"
SOURCE_BLOB = "f43bea1220c262678b744f793876b7e5ea69bdff"

def patch_pair() -> tuple[str, str]:
    module = ast.parse(GENERATE.read_text(), filename=str(GENERATE))
    found = []
    for node in ast.walk(module):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name):
            continue
        if node.func.id != "adapt" or len(node.args) < 3:
            continue
        try:
            relative = ast.literal_eval(node.args[0])
        except (ValueError, TypeError):
            continue
        if relative != "src/video_core/renderer_vulkan/vk_rasterizer.cpp":
            continue
        for item in node.args[2].elts:
            try:
                before, after = ast.literal_eval(item)
            except (ValueError, TypeError):
                continue
            if "// Flip by surface clip height" in before:
                found.append((before, after))
    assert len(found) == 1, "one source-owned viewport Y-flip transform required"
    return found[0]

def main() -> None:
    raw = PINNED.read_bytes()
    sha = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
    assert sha == SOURCE_BLOB, "original pinned Vulkan source changed"
    original = raw.decode("utf-8")
    before, after = patch_pair()
    assert original.count(before) == 1, "source must match old 5-line viewport block"
    assert original.count(after) == 0, "source original unexpectedly already contains new fix"
    assert before.count("y += conv(static_cast<f32>(regs.surface_clip.height));") == 1
    assert after.count("const float clip_height = conv(static_cast<f32>(regs.surface_clip.height));") == 1
    assert after.count("if (src.scale_y < 0.0f && y >= clip_height)") == 1
    assert after.count("y = clip_height - y;") == 1
    assert after.count("y += clip_height;") == 1
    assert after.count("height = -height;") == 1
    assert original.replace(before, after).count(after) == 1
    # Compile the exact fragment selected by prepare-vulkan-port.py, with
    # only the required local viewport C++ types mocked.
    code = r"""
#include <cassert>
#include <cmath>
#include <utility>
using f32 = float;
struct Regs {
    struct { unsigned height; } surface_clip{};
};
struct Src { float scale_y{}; };
std::pair<float, float> render(float input_y, float scale_y, unsigned clip,
                              bool lower_left) {
    const Regs regs{{clip}};
    const Src src{scale_y};
    const auto conv = [](float v) { return v; };
    float y = input_y;
    float height = 48.0f;
""" + after + r"""
    return {y, height};
}
int main() {
    assert(render(100, -1, 100, true).first == 0.0f);
    assert(render(120, -1, 100, true).first == -20.0f);
    assert(render(20, -1, 100, true).first == 120.0f);
    assert(render(20, +1, 100, true).first == 120.0f);
    assert(render(20, -1, 100, false).first == 20.0f);
    assert(render(20, -1, 100, true).second == -48.0f);
    assert(render(20, -1, 100, false).second == 48.0f);
}
"""
    with tempfile.TemporaryDirectory(prefix="ab-r23-vp-") as folder:
        source, program = Path(folder) / "viewport.cpp", Path(folder) / "viewport"
        source.write_text(code)
        subprocess.run(
            ["clang++", "-std=c++20", "-O1", "-g", "-Wall", "-Wextra",
             "-Werror", "-fsanitize=address,undefined", "-fno-omit-frame-pointer",
             str(source), "-o", str(program)],
            check=True, cwd=ROOT, timeout=80,
        )
        subprocess.run([str(program)], check=True, cwd=ROOT, timeout=15,
                       env={**os.environ, "ASAN_OPTIONS":"detect_leaks=1:halt_on_error=1"})
    print("R23_AB11_EXACT_VIEWPORT_SOURCE_HOST_ASAN_UBSAN_PASS",
          "native_vulkan_ps5_not_tested=1")

if __name__ == "__main__":
    try:
        main()
    except (AssertionError, OSError, ValueError, subprocess.CalledProcessError,
            subprocess.TimeoutExpired) as exc:
        print("R23_AB11_SOURCE_HOST_FAIL", str(exc), file=sys.stderr)
        sys.exit(1)
