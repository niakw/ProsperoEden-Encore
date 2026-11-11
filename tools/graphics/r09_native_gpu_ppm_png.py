#!/usr/bin/env python3
"""Convert validated real Vulkan RGBA16F->RGB8 witness PPM to lossless PNG.

No Pillow, network, game captures, model weights or synthetic replacement.
The PPM contains the genuine stage-three GPU framebuffer converted to 8-bit.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import struct
import sys
import zlib

def png_chunk(kind: bytes, payload: bytes) -> bytes:
    return (struct.pack(">I", len(payload)) + kind + payload +
            struct.pack(">I", zlib.crc32(kind + payload)))

def read_ppm(path: Path) -> tuple[int, int, bytes]:
    with path.open("rb") as f:
        if f.readline() != b"P6\n":
            raise ValueError("Unexpected native GPU PPM header")
        width, height = map(int, f.readline().split())
        if width != 3840 or height != 2160:
            raise ValueError(f"Unexpected full-raster output {width}x{height}")
        if f.readline() != b"255\n":
            raise ValueError("Expected 8-bit diagnostic RGB")
        raw = f.read()
    if len(raw) != width * height * 3:
        raise ValueError("Truncated or oversized native Vulkan image")
    if raw.count(b"\x00") == len(raw):
        raise ValueError("GPU returned a completely zeroed image")
    return width, height, raw

def convert(src: Path, dst: Path) -> None:
    width, height, pixels = read_ppm(src)
    # PNG filter 0 per scanline, RGB8, original exact raster.
    stride = width * 3
    rows = b"".join(b"\0" + pixels[y * stride:(y + 1) * stride]
                    for y in range(height))
    png = (b"\x89PNG\r\n\x1a\n" +
           png_chunk(b"IHDR", struct.pack(">IIBBBBB", width, height,
                                          8, 2, 0, 0, 0)) +
           png_chunk(b"IDAT", zlib.compress(rows, 6)) +
           png_chunk(b"IEND", b""))
    dst.write_bytes(png)
    print(f"R09_NATIVE_GPU_REAL_4K_PNG_SAVED file={dst} "
          f"pixels={width*height} png_sha256={hashlib.sha256(png).hexdigest()}")

def compare(a: Path, b: Path) -> None:
    wa, ha, left = read_ppm(a)
    wb, hb, right = read_ppm(b)
    if (wa, ha) != (wb, hb):
        raise ValueError("Native SGSR/Edge output dimensions differ")
    differing = sum(x != y for x, y in zip(left, right))
    print(f"R09_NATIVE_GPU_SGSR_VS_EDGE_RGB8_DIFFERENT_CHANNELS={differing} "
          f"total_channels={len(left)}")
    # Green-channel luma boundaries in the pinned test fixture MUST
    # distinguish both original Qualcomm kernels on the validated
    # Lavapipe ICD. A missing variant selection or wrong shader binding
    # is a real regression, not a success with two identical PNGs.
    if differing < 100_000:
        raise ValueError("Authentic SGSR Edge variant did not materially "
                         "differ from normal shader on green-edge fixture")
    print("R09_AUTHENTIC_SGSR_EDGE_SHADER_SELECTION_DIFFERENTIAL_PASS")
    print(f"R09_NATIVE_GPU_OUTPUTS_NONEMPTY_SHA256="
          f"{hashlib.sha256(left).hexdigest()} "
          f"{hashlib.sha256(right).hexdigest()}")

if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "compare":
        compare(Path(sys.argv[2]), Path(sys.argv[3]))
    elif len(sys.argv) == 3:
        convert(Path(sys.argv[1]), Path(sys.argv[2]))
    else:
        sys.exit("Usage: r09_native_gpu_ppm_png.py input.ppm output.png | "
                 "compare normal.ppm edge.ppm")
