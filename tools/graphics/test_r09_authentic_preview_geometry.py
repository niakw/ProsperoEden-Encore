#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Strict host converter geometry tests only: NOT neural output or a GPU proof."""
import importlib.util
from pathlib import Path
import struct
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
script = HERE / "r09_authentic_preview_png.py"
spec = importlib.util.spec_from_file_location("r09_private_preview", script)
assert spec and spec.loader
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
assert m.SUPPORTED_RASTERS == frozenset({(1280, 720), (1920, 1080)})
for width, height in sorted(m.SUPPORTED_RASTERS):
    assert width * height * 4 in (3_686_400, 8_294_400)
    assert width * height * 16 in (14_745_600, 33_177_600)
    png = m.png([b"\x00" * (width * 3)] * height, width, height)
    assert png.startswith(m.PNG_SIGNATURE)
    assert struct.unpack_from(">II", png, len(m.PNG_SIGNATURE) + 8) == (width, height)

# A tiny fixture validates RGB conversion only. It is deliberately never
# labeled or published as an authentic model or Vulkan readback.
rgba8 = bytes([11, 22, 33, 255, 44, 55, 66, 255])
assert m.source_rgb_rows(rgba8, 2) == [bytes([11, 22, 33, 44, 55, 66])]
out = struct.pack("<8f", 0.0, 0.5, 1.0, 1.0,
                  0.25, 0.75, 0.0, 1.0)
rows, clipped, low, high = m.neural_rgb_rows(out, 2, 1)
assert len(rows) == 1 and len(rows[0]) == 6
assert clipped == 0 and low == 0.0 and high == 1.0

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    common = [
        sys.executable, "-B", str(script),
        "--input-rgba8", str(root / "not-uploaded.rgba8"),
        "--output-rgba32f", str(root / "not-uploaded.rgba32f"),
        "--before-png", str(root / "before.png"),
        "--after-png", str(root / "after.png")
    ]
    for width, height in [(0, 0), (1920, 720), (1280, 1080),
                          (3840, 2160), (1281, 720), (2**32-1, 2**32-1)]:
        p = subprocess.run(common + ["--width", str(width), "--height", str(height)],
                           capture_output=True, text=True, check=False)
        assert p.returncode == 20 and "R09_REAL_PREVIEW_RASTER_UNSUPPORTED" in p.stderr
    assert not (root / "before.png").exists()
    assert not (root / "after.png").exists()
print("R09_PRIVATE_PREVIEW_720_1080_PNG_GEOMETRY_AND_SIX_NEGATIVES_PASS non_neural_fixture_only")
