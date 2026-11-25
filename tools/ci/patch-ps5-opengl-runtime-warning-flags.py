#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Silence only reviewed third-party diagnostics in the PS5 OpenGL runtime build.

The caller operates on a disposable pinned checkout and restores the original
file byte-for-byte. All other warnings remain under the upstream -Werror policy.
"""
from pathlib import Path
import sys

REPLACEMENTS = (
    ("-Wno-error=unused-parameter", "-Wno-unused-parameter", 3),
    ("-Wno-error=missing-field-initializers", "-Wno-missing-field-initializers", 1),
    ("-Wno-error=unused-function", "-Wno-unused-function", 1),
)


def patched_text(text: str) -> str:
    if all(new in text and old not in text for old, new, _ in REPLACEMENTS):
        return text
    for old, new, expected in REPLACEMENTS:
        if text.count(old) != expected:
            raise ValueError(
                f"PS5 OpenGL runtime warning policy drift: {old!r} "
                f"count={text.count(old)} expected={expected}"
            )
        text = text.replace(old, new)
    if "-Werror" not in text:
        raise ValueError("PS5 OpenGL runtime unexpectedly lost global -Werror")
    return text


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: patch-ps5-opengl-runtime-warning-flags.py ps5-opengl-core33.mk")
    path = Path(sys.argv[1])
    if path.is_symlink() or not path.is_file():
        raise SystemExit("refusing missing/symlinked PS5 OpenGL runtime makefile")
    path.write_text(patched_text(path.read_text(encoding="utf-8")), encoding="utf-8")
    print("PS5_OPENGL_RUNTIME_THIRDPARTY_WARNING_SCOPE_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
