#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Export real before/after PNG previews from a completed R09 Vulkan readback.

This tool NEVER synthesizes a frame, performs inference, validates 152 GPU
operations, or claims NVIDIA-reference image quality. Inputs MUST be actual
files produced by a separately executed authentic R09 session.
"""
from __future__ import annotations

import argparse
import hashlib
import math
from pathlib import Path
import struct
import sys
import zlib

DEFAULT_WIDTH, DEFAULT_HEIGHT = 1920, 1080
# Output geometry is determined by the same raster as the native GPU readback.
# Do not let a wrong width/height silently reinterpret captured pixel bytes.
SUPPORTED_RASTERS = frozenset({(1920, 1080), (1280, 720)})
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"

def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def read_exact(path: Path, length: int) -> bytes:
    if path.is_symlink() or not path.is_file() or path.stat().st_size != length:
        raise ValueError(f"R09_REAL_PREVIEW_SIZE_OR_FILE_REJECTED: {path}")
    data = path.read_bytes()
    if len(data) != length:
        raise ValueError(f"R09_REAL_PREVIEW_SHORT_READ: {path}")
    return data

def chunk(tag: bytes, payload: bytes) -> bytes:
    return (struct.pack(">I", len(payload)) + tag + payload +
            struct.pack(">I", zlib.crc32(tag + payload) & 0xffffffff))

def png(rows: list[bytes], width: int, height: int) -> bytes:
    if len(rows) != height or any(len(row) != width * 3 for row in rows):
        raise ValueError("R09_REAL_PREVIEW_ROW_GEOMETRY_REJECTED")
    scanlines = b"".join(b"\0" + row for row in rows)
    compressed = zlib.compress(scanlines, 6)
    header = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return (PNG_SIGNATURE + chunk(b"IHDR", header) +
            chunk(b"IDAT", compressed) + chunk(b"IEND", b""))

def source_rgb_rows(rgba8: bytes, width: int) -> list[bytes]:
    result = []
    stride = width * 4
    for start in range(0, len(rgba8), stride):
        row = rgba8[start:start + stride]
        rgb = bytearray(width * 3)
        rgb[0::3] = row[0::4]
        rgb[1::3] = row[1::4]
        rgb[2::3] = row[2::4]
        result.append(bytes(rgb))
    return result

def neural_rgb_rows(rgba32f: bytes, width: int, height: int) -> tuple[list[bytes], int, float, float]:
    rows = []
    clipped = 0
    minimum, maximum = math.inf, -math.inf
    values = struct.iter_unpack("<4f", rgba32f)
    for y in range(height):
        row = bytearray(width * 3)
        for x in range(width):
            pixel = next(values)
            if not all(math.isfinite(value) for value in pixel):
                raise ValueError(f"R09_REAL_PREVIEW_NONFINITE_OUTPUT at ({x},{y})")
            for channel in range(3):
                value = pixel[channel]
                minimum = min(minimum, value)
                maximum = max(maximum, value)
                if value < 0.0 or value > 1.0:
                    clipped += 1
                row[x * 3 + channel] = max(
                    0, min(255, round(max(0.0, min(value, 1.0)) * 255.0)))
        rows.append(bytes(row))
    return rows, clipped, minimum, maximum

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--width", type=int, default=DEFAULT_WIDTH)
    parser.add_argument("--height", type=int, default=DEFAULT_HEIGHT)
    parser.add_argument("--input-rgba8", required=True, type=Path)
    parser.add_argument("--output-rgba32f", required=True, type=Path)
    parser.add_argument("--before-png", required=True, type=Path)
    parser.add_argument("--after-png", required=True, type=Path)
    args = parser.parse_args()
    try:
        if (args.width, args.height) not in SUPPORTED_RASTERS:
            raise ValueError("R09_REAL_PREVIEW_RASTER_UNSUPPORTED")
        if args.before_png == args.after_png:
            raise ValueError("R09_REAL_PREVIEW_OUTPUT_PATH_ALIAS")
        if any(path.exists() for path in (args.before_png, args.after_png)):
            raise ValueError("R09_REAL_PREVIEW_WOULD_OVERWRITE")
        original = read_exact(args.input_rgba8, args.width * args.height * 4)
        result = read_exact(args.output_rgba32f, args.width * args.height * 16)
        before_rows = source_rgb_rows(original, args.width)
        after_rows, clipped, minimum, maximum = neural_rgb_rows(result, args.width, args.height)
        before_image = png(before_rows, args.width, args.height)
        after_image = png(after_rows, args.width, args.height)
        # Never write a preview for a non-finite or geometrically invalid
        # GPU result. A valid all-black capture remains a diagnostic image.
        args.before_png.write_bytes(before_image)
        args.after_png.write_bytes(after_image)
        print("R09_REAL_RGBA32F_PREVIEW_EXPORT_ONLY_NOT_A_152_OP_PROOF")
        print(f"source_sha256={digest(original)} output_sha256={digest(result)}")
        print(f"before_png_sha256={digest(before_image)}")
        print(f"after_png_sha256={digest(after_image)}")
        print(f"neural_range=[{minimum:.8g},{maximum:.8g}] clipped_channels={clipped}")
        print("Color mapping: direct clamp of normalized floats to 8-bit RGB; "
              "not an independent NVIDIA DLSS-NR reference.")
        return 0
    except (ValueError, OSError, struct.error) as exc:
        print("R09_REAL_PREVIEW_REJECTED", exc, file=sys.stderr)
        return 20

if __name__ == "__main__":
    raise SystemExit(main())
