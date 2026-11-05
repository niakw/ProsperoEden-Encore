#!/usr/bin/env python3
"""Map new Encore revisions R1..R999 to native PS5 01.400.001..01.400.999.

The already-published legacy R1 artifact (01.000.041) is immutable and
handled only by the separately pinned legacy resolver exception.
"""

import re
import sys

NATIVE_MAJOR = 1
NATIVE_MINOR = 400
MAX_REVISION = 999


def package_version(revision: str) -> str:
    if not re.fullmatch(r"R[1-9][0-9]{0,5}", revision):
        raise ValueError("invalid native Encore release revision")
    number = int(revision[1:])
    if number > MAX_REVISION:
        raise ValueError("R revision exceeds the supported 01.400.xxx format")
    return f"{NATIVE_MAJOR:02d}.{NATIVE_MINOR:03d}.{number:03d}"


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: native-content-version.py R<number>")
    try:
        print(package_version(sys.argv[1]))
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc


if __name__ == "__main__":
    main()
