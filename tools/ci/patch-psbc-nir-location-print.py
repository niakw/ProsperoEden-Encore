#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Repair a real Mesa NIR debug-location output buffer in an isolated PSBC build.

A uint32 location may print 10 decimal digits plus NUL. The pinned Mesa
26.2 source has two char[4] callers and snprintf(buf, 4, "%u", location).
Patch ONLY the staged PSBC working checkout, fail closed on source drift and
restore the exact original source before the next upstream verifier.
"""
from pathlib import Path
import hashlib
import subprocess
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


PINNED_PRINTER = "abc711758a37fd678a49c693f70d002b3f637c11"
PINNED_RADV_STUB = "34437d0216c5438d209b544accddb0030e7fae98"
RADV_STUB_ANCHOR = b"struct radv_instance {"
RADV_FORWARD = b"struct radv_physical_device;\n\n"


def gitblob(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()


def patched_radv_stub(raw: bytes) -> bytes:
    if gitblob(raw) != PINNED_RADV_STUB:
        raise ValueError("Unexpected pinned PSBC RADV stub bytes")
    if raw.count(RADV_STUB_ANCHOR) != 1 or RADV_FORWARD in raw:
        raise ValueError("PSBC RADV declaration drift")
    return raw.replace(RADV_STUB_ANCHOR, RADV_FORWARD + RADV_STUB_ANCHOR, 1)


def compile_window(file: Path, command: list[str]) -> int:
    if not file.is_file() or file.is_symlink() or not command:
        raise ValueError("Unsafe PSBC compile-window input")
    original = file.read_bytes()
    digest = hashlib.sha1(b"blob " + str(len(original)).encode() + bytes([0]) + original).hexdigest()
    if digest != PINNED_PRINTER:
        raise ValueError("Unexpected pinned PSBC NIR printer original bytes")
    fixed = patched_bytes(original)
    # Resolve only the sibling stub in the same verified PSBC source tree.
    header = file.parent.parent.parent / "amd/vulkan/radv_instance.h"
    if not header.is_file() or header.is_symlink():
        raise ValueError("Unsafe or missing PSBC RADV stub")
    header_original = header.read_bytes()
    header_fixed = patched_radv_stub(header_original)
    try:
        file.write_bytes(fixed)
        header.write_bytes(header_fixed)
        print("PSBC_NIR_LOCATION_BUFFER_11_SAFE compile_window=1", flush=True)
        print("PSBC_RADV_STUB_FILE_SCOPE_PASS compile_window=1", flush=True)
        return subprocess.run(command, check=False).returncode
    finally:
        # Nested finally ensures the other owner is restored even if one write fails.
        try:
            header.write_bytes(header_original)
        finally:
            file.write_bytes(original)
        if file.read_bytes() != original or header.read_bytes() != header_original:
            raise RuntimeError("PSBC compiler source restoration failed")

def main() -> int:
    if len(sys.argv) >= 4 and sys.argv[1] == "--compile":
        return compile_window(Path(sys.argv[2]), sys.argv[3:])
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
