#!/usr/bin/env python3
"""Apply the reviewed upstream LZ4 CMake-policy-only fix to mutable CPM staging."""
from pathlib import Path
import argparse
import hashlib

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "vendor/sources/eden-cpm/lz4/ebb370ca83/build/cmake/CMakeLists.txt"
OLD = b"cmake_minimum_required(VERSION 3.5)\n"
NEW = b"cmake_minimum_required(VERSION 3.5...3.16)\n"

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def transformed(raw: bytes) -> bytes:
    if raw.count(OLD) != 1 or NEW in raw:
        raise RuntimeError("Pinned LZ4 CMake preimage is not the reviewed 1.10.0 form")
    return raw.replace(OLD, NEW, 1)

def apply(eden: Path) -> None:
    source = SOURCE.read_bytes()
    expected = transformed(source)
    target = eden / ".cache/cpm/lz4/ebb370ca83/build/cmake/CMakeLists.txt"
    if not target.is_file():
        raise RuntimeError(f"Missing staged pinned LZ4 CMake file: {target}")
    current = target.read_bytes()
    if current == source:
        target.write_bytes(expected)
        current = target.read_bytes()
    elif current != expected:
        raise RuntimeError(
            "Refusing unknown LZ4 staging bytes: "
            f"source={sha(source)} expected={sha(expected)} observed={sha(current)}"
        )
    if current != expected or current.replace(NEW, OLD, 1) != source:
        raise RuntimeError("LZ4 policy overlay is not exactly reversible")
    print(
        "LZ4_CMAKE_POLICY_STAGE_PASS "
        f"upstream=7f71be01 source_sha256={sha(source)} staged_sha256={sha(current)} runtime_sources_changed=0"
    )

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("eden", type=Path)
    args = ap.parse_args()
    apply(args.eden)
