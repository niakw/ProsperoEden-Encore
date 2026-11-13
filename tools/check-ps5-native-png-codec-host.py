#!/usr/bin/env python3
"""Compile the actual PS5 stb translation unit and decode a valid PNG.

The pinned upstream common/stb.cpp defines STBI_ONLY_JPEG, so PNG files from
LaunchBox and local profile avatars were rejected despite valid signatures.
This test builds the MAINTAINED production implementation, not a dummy codec.
"""
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile
import zlib

root = Path(__file__).resolve().parents[1]
owner = root / "vendor/encore-active/eden-core/src/common/stb_image_png.cpp"
header_root = root / "vendor/sources/eden/externals/stb"
cmake = (root / "headless/CMakeLists.txt").read_text(encoding="utf-8")
impl = owner.read_text(encoding="utf-8")
assert impl.count("#define STBI_ONLY_JPEG 1") == 1
assert impl.count("#define STBI_ONLY_PNG 1") == 1
assert impl.count("#define STB_IMAGE_IMPLEMENTATION 1") == 1
assert 'list(REMOVE_ITEM eden_stb_common_sources "stb.cpp")' in cmake
assert 'list(APPEND eden_stb_common_sources "${EDEN_NATIVE_STB_CODECS}")' in cmake
assert "TARGET common PROPERTY SOURCES" in cmake

def chunk(kind, body):
    data = kind + body
    return struct.pack(">I", len(body)) + data + struct.pack(">I", zlib.crc32(data))

# 2x2 RGBA, each scanline starts with filter=0.
pixels = (b"\x00" + b"\xff\x00\x00\xff" + b"\x00\xff\x00\xff" +
          b"\x00" + b"\x00\x00\xff\xff" + b"\xff\xff\x00\xff")
png = (b"\x89PNG\r\n\x1a\n" +
       chunk(b"IHDR", struct.pack(">IIBBBBB", 2, 2, 8, 6, 0, 0, 0)) +
       chunk(b"IDAT", zlib.compress(pixels)) +
       chunk(b"IEND", b""))
cpp = r'''
#include <cassert>
#include <stb_image.h>
int main(int argc, char** argv) {
    assert(argc == 2);
    int width=0, height=0, n=0;
    assert(stbi_info(argv[1], &width, &height, &n));
    assert(width == 2 && height == 2 && n == 4);
    unsigned char* rgba = stbi_load(argv[1], &width, &height, &n, 4);
    assert(rgba && width == 2 && height == 2);
    assert(rgba[0] == 255 && rgba[1] == 0 && rgba[2] == 0 && rgba[3] == 255);
    assert(rgba[12] == 255 && rgba[13] == 255 && rgba[14] == 0);
    stbi_image_free(rgba);
}
'''
compiler = shutil.which("clang++") or shutil.which("g++")
assert compiler, "C++ compiler missing"
with tempfile.TemporaryDirectory(prefix="eden-png-codec-") as tmp:
    folder = Path(tmp)
    image = folder / "valid-2x2.png"
    image.write_bytes(png)
    test = folder / "test.cpp"
    test.write_text(cpp, encoding="utf-8")
    exe = folder / "test"
    subprocess.run([compiler, "-std=c++20", "-O0", "-I", str(header_root),
                    str(owner), str(test), "-o", str(exe)], check=True, timeout=90)
    subprocess.run([str(exe), str(image)], check=True, timeout=10)
print("ENCORE_NATIVE_STB_PNG_REAL_SOURCE_PASS decoded_2x2_rgba=1 jpeg_kept=1")
