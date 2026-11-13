#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Repair a real Mesa NIR debug-location output buffer in an isolated PSBC build.

A uint32 location may print 10 decimal digits plus NUL. The pinned Mesa
26.2 source has two char[4] callers and snprintf(buf, 4, "%u", location).
Patch ONLY the staged PSBC working checkout, fail closed on source drift and
let build-opengl-sdk.sh restore the original source byte-for-byte on exit.
"""
from pathlib import Path
import sys

BEFORE = b'snprintf(buf, 4, "%u", location);'
AFTER = b'snprintf(buf, 11, "%u", location);'
SMALL = b'char buf[4];'
LARGE = b'char buf[11];'


def patched_bytes(raw: bytes) -> bytes:
    if (raw.count(BEFORE) != 1 or raw.count(SMALL) != 2 or
            AFTER in raw or LARGE in raw):
        raise ValueError("PSBC NIR location formatter drift: require one 4-byte printf and two callers")
    fixed = raw.replace(BEFORE, AFTER, 1).replace(SMALL, LARGE)
    assert fixed.count(AFTER) == 1 and fixed.count(LARGE) == 2
    return fixed


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: patch-psbc-nir-location-print.py path/to/nir_print.c")
    file = Path(sys.argv[1])
    if not file.is_file() or file.is_symlink():
        raise SystemExit("refusing absent/symlinked PSBC NIR source")
    file.write_bytes(patched_bytes(file.read_bytes()))
    print("PSBC_NIR_LOCATION_BUFFER_11_SAFE", file.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
