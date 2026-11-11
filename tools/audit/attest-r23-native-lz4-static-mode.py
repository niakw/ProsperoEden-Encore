#!/usr/bin/env python3
"""Read-only R23 #20/#66 native YUZU_STATIC_BUILD CMake cache attestation.

A default option is NOT the effective cached option. Never claim lz4 static
behavior without the actual native CMakeCache and pinned source predicates.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import tempfile

ROOT = Path(__file__).resolve().parents[2]

def parse_cache(text: str) -> dict:
    d = {}
    for line in text.splitlines():
        if line.startswith("//") or line.startswith("#") or "=" not in line:
            continue
        left, value = line.split("=", 1)
        if ":" not in left:
            continue
        name, kind = left.split(":", 1)
        d[name] = {"type": kind, "value": value}
    return d

def inspect(path: Path | None, root: Path) -> dict:
    build = (root / "tools/build-headless-native.sh").read_text()
    eden = (root / "vendor/sources/eden/CMakeLists.txt").read_text()
    find = (root / "vendor/sources/eden/CMakeModules/find/Findlz4.cmake").read_text()
    if '-DPS5_NATIVE=ON' not in build or '-DYUZU_STATIC_BUILD=' in build:
        raise ValueError("PS5 native recipe no longer uses the reviewed default")
    if 'option(YUZU_STATIC_BUILD "Use static libraries and executables if available" OFF)' not in eden:
        raise ValueError("upstream pinned YUZU_STATIC_BUILD default changed")
    if 'if (YUZU_STATIC_BUILD)' not in eden or 'if (TARGET LZ4::lz4_shared)' not in find:
        raise ValueError("upstream static-mode guarded source diverged")
    rows = parse_cache(path.read_text()) if path is not None and path.is_file() else {}
    val = rows.get("YUZU_STATIC_BUILD", {}).get("value", "unknown").upper()
    if val not in {"OFF", "ON", "FALSE", "TRUE", "0", "1", "UNKNOWN"}:
        val = "unknown"
    off = val in {"OFF", "FALSE", "0"}
    on = val in {"ON", "TRUE", "1"}
    return {
        "scope": "historical selected native CMake configuration; not current main binary",
        "native_cache_present": path is not None and path.is_file(),
        "native_cache_path": str(path) if path else None,
        "YUZU_STATIC_BUILD": val,
        "upstream_20_force_bundled_static_condition_active": on if off or on else None,
        "upstream_66_static_library_alias_condition_active": on if off or on else None,
        "both_lz4_changes_inert_in_this_cached_static_profile": off,
        "current_PS5_elf_or_link_qualified": False,
    }

def self_test() -> None:
    for text, want in (
        ("YUZU_STATIC_BUILD:BOOL=OFF\n", "OFF"),
        ("YUZU_STATIC_BUILD:BOOL=ON\n", "ON"),
        ("YUZU_STATIC_BUILD:BOOL=0\n", "0"),
        ("YUZU_STATIC_BUILD:UNINITIALIZED=TRUE\n", "TRUE"),
    ):
        assert parse_cache(text)["YUZU_STATIC_BUILD"]["value"].upper() == want
    assert parse_cache("#nothing\n").get("YUZU_STATIC_BUILD") is None
    print("R23_NATIVE_LZ4_STATIC_MODE_PARSER_SELFTEST_PASS")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("native_cmake_cache", nargs="?", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    print(json.dumps(inspect(args.native_cmake_cache, ROOT), indent=2, sort_keys=True))

if __name__ == "__main__":
    main()
