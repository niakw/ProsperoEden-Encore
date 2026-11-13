#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Enable supported GCC/Clang noreturn and unused attributes for temporary PSBC builds.

The caller must back up and restore its original pinned upstream inputs.
No changes to third-party shader source or global warning suppression.
"""
from pathlib import Path
import sys


def patched_bytes(raw: bytes) -> bytes:
    marker = b"\t-DHAVE_FUNC_ATTRIBUTE_PACKED=1 " + bytes((92, 10))
    addition = (b"\t-DHAVE_FUNC_ATTRIBUTE_NORETURN=1 " + bytes((92, 10)) +
                b"\t-DHAVE_FUNC_ATTRIBUTE_UNUSED=1 " + bytes((92, 10)))
    if (raw.count(marker) != 1 or raw.count(b"-DHAVE_FUNC_ATTRIBUTE_PACKED=1") != 1
            or b"-DHAVE_FUNC_ATTRIBUTE_NORETURN=1" in raw
            or b"-DHAVE_FUNC_ATTRIBUTE_UNUSED=1" in raw):
        raise ValueError("PSBC config drift: require exactly one PACKED and neither NORETURN nor UNUSED")
    return raw.replace(marker, marker + addition, 1)


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: patch-psbc-noreturn-flags.py CONFIG.mak")
    path = Path(sys.argv[1])
    if path.is_symlink() or not path.is_file():
        raise SystemExit("refusing missing/symlinked compiler config")
    path.write_bytes(patched_bytes(path.read_bytes()))
    print("PSBC_NORETURN_UNUSED_COMPILER_ATTRIBUTES_ADDED", path.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
