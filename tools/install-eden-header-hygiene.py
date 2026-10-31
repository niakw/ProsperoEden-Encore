#!/usr/bin/env python3
"""Install warning-free shared Eden headers without editing pinned upstream source snapshots.

Only exact reviewed C++-semantic-neutral changes are permitted: non-constexpr
atomic methods and removal of nodiscard from a void method. Original vendored
upstream files remain immutable and hash-verifiable. Both host and PS5 builds
compile maintained active headers, not a throwaway generated rewrite.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import shutil
import tempfile

ROOT = Path(__file__).resolve().parents[1]
PIN = "5f142c7926d0c7fcbbd0ce30794d72f638a43b2a"
ORIGINAL = ROOT / "vendor/sources/eden/src"
ACTIVE = ROOT / "vendor/encore-active/eden-header-hygiene/include"
FIXES = {
    "common/page_table.h": (
        ("constexpr void Store(bool marked, PageType type, u16 block, uintptr_t pointer) noexcept",
         "void Store(bool marked, PageType type, u16 block, uintptr_t pointer) noexcept"),
        ("constexpr void MarkRasterizerCached() noexcept",
         "void MarkRasterizerCached() noexcept"),
        ("constexpr void MarkDebug(u64 ptr, u16 block) noexcept",
         "void MarkDebug(u64 ptr, u16 block) noexcept"),
    ),
    "video_core/macro.h": (
        ("[[nodiscard]] inline void SetMethodAddress(u32 address) noexcept",
         "inline void SetMethodAddress(u32 address) noexcept"),
    ),
}


def verify_sources() -> dict[str, tuple[bytes, bytes]]:
    verified = {}
    for relative, replacements in FIXES.items():
        original = (ORIGINAL / relative).read_bytes()
        expected = original
        for old_text, new_text in replacements:
            old, new = old_text.encode(), new_text.encode()
            if expected.count(old) != 1:
                raise RuntimeError(f"Unexpected pinned Eden revision: {relative} {old_text}")
            expected = expected.replace(old, new)
        maintained = (ACTIVE / relative).read_bytes()
        if maintained != expected or original == expected:
            raise RuntimeError(f"Unreviewed active header drift: {relative}")
        verified[relative] = original, expected
    return verified


def install(destination: Path, verified: dict[str, tuple[bytes, bytes]], *, check: bool) -> None:
    if (destination / "GIT-COMMIT").read_text().strip() != PIN:
        raise RuntimeError("Incorrect pinned Eden source checkout")
    changed = 0
    for relative, (original, expected) in verified.items():
        target = destination / "src" / relative
        if not target.is_file():
            raise RuntimeError(f"Missing native Eden source: {relative}")
        current = target.read_bytes()
        if check:
            if current != expected:
                raise RuntimeError(f"Shared header was not installed: {relative}")
            continue
        if current == expected:
            continue
        if current != original:
            raise RuntimeError(f"Unexpected native source revision: {relative}")
        with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as out:
            temp = Path(out.name)
        try:
            shutil.copyfile(ACTIVE / relative, temp)
            temp.replace(target)
        finally:
            temp.unlink(missing_ok=True)
        changed += 1
    print(f"ENCORE_SHARED_HEADER_HYGIENE_PASS sources={len(verified)} changed={changed} check={check}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("destination", nargs="?", type=Path)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    if args.check and args.destination is None:
        parser.error("--check requires a prepared Eden source destination")
    if args.verify and args.destination is not None:
        parser.error("--verify does not accept a destination")
    verified = verify_sources()
    if args.destination is not None:
        install(args.destination, verified, check=args.check)
    else:
        print(f"ENCORE_SHARED_HEADER_HYGIENE_SOURCE_PASS sources={len(verified)}")


if __name__ == "__main__":
    main()
