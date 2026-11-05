#!/usr/bin/env python3
"""Derive increasing native PS5 contentVersion from the compiled Encore R label.

The immutable public R1 release is 01.000.041. Its successor R2 must be
01.000.042, and so on. The user-visible R revision is still independent.
"""
import re
import sys

LEGACY_FIRST = 40
MAX_COUNTER = 999_999


def package_version(revision: str) -> str:
    if not re.fullmatch(r"R[1-9][0-9]{0,5}", revision):
        raise ValueError("invalid native Encore release revision")
    count = LEGACY_FIRST + int(revision[1:])
    if count > MAX_COUNTER:
        raise ValueError("native contentVersion would exceed the PS5 format")
    return f"01.{count // 1000:03d}.{count % 1000:03d}"


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: native-content-version.py R<number>")
    try:
        print(package_version(sys.argv[1]))
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc


if __name__ == "__main__":
    main()
