#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Fast PNG structural/CRC/pixel-stream check for the PS5 case footer."""
import base64
from pathlib import Path
import struct
import zlib

root = Path(__file__).resolve().parents[1]
source = root / "headless/prosperoeden/ui/art/switch-rear-footer.png.b64"
image = base64.b64decode(source.read_text().strip(), validate=True)
assert image.startswith(b"\x89PNG\r\n\x1a\n")
offset, chunks, streams = 8, [], []
while offset < len(image):
    assert offset + 12 <= len(image)
    size = struct.unpack_from(">I", image, offset)[0]
    assert size <= 10 * 1024 * 1024
    kind = image[offset + 4:offset + 8]
    payload = image[offset + 8:offset + 8 + size]
    end = offset + 8 + size
    assert end + 4 <= len(image)
    crc = struct.unpack_from(">I", image, end)[0]
    assert zlib.crc32(kind + payload) & 0xffffffff == crc
    chunks.append(kind)
    if kind == b"IHDR":
        assert struct.unpack_from(">IIBBBBB", payload) == (600, 286, 1, 0, 0, 0, 0)
    if kind == b"IDAT":
        streams.append(payload)
    offset = end + 4
assert offset == len(image)
assert chunks == [b"IHDR", b"IDAT", b"IEND"], chunks
decoded = zlib.decompress(b"".join(streams))
assert len(decoded) == 286 * (1 + (600 + 7) // 8), len(decoded)
for index in range(286):
    assert decoded[index * 76] <= 4
print("PASS lossless gray PNG footer, valid CRCs, no invalid RGB ICC profile")
