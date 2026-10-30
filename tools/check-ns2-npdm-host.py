#!/usr/bin/env python3
"""Run the real NS2 ACID layout header in standalone C++20 host regressions."""
from __future__ import annotations
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent
HEADER_DIR = ROOT / "headless" / "ns2"
TEST = ROOT / "tools" / "ns2" / "test_npdm_layout.cpp"
SOURCE = HEADER_DIR / "overrides/core/file_sys/program_metadata.cpp"
CMAKE = ROOT / "headless" / "CMakeLists.txt"

def main() -> int:
    compiler = shutil.which("clang++") or shutil.which("g++")
    if compiler is None:
        print("No C++20 compiler found", file=sys.stderr)
        return 2
    if 'FindAcidBody(' not in SOURCE.read_text(encoding="utf-8"):
        print("Production metadata reader not wired to the tested helper", file=sys.stderr)
        return 2
    if 'option(EDEN_NS2_METADATA_EXPERIMENTAL' not in CMAKE.read_text(encoding="utf-8"):
        print("Explicit experimental CMake gate missing", file=sys.stderr)
        return 2
    with tempfile.TemporaryDirectory(prefix="encore-ns2-npdm-") as tmp:
        for opt in ("-O0", "-O2"):
            executable = Path(tmp) / ("test_" + opt[1:])
            command = [compiler, "-std=c++20", "-Wall", "-Wextra", "-Werror",
                       "-pedantic", opt, "-fsanitize=undefined",
                       "-fno-sanitize-recover=all", "-I", str(HEADER_DIR),
                       str(TEST), "-o", str(executable)]
            subprocess.run(command, check=True)
            subprocess.run([str(executable)], check=True,
                           env={**os.environ, "UBSAN_OPTIONS": "halt_on_error=1"})
            print(f"NS2 NPDM experimental helper {opt}: PASS")
    print("NOTE: parser helper tested; complete Eden core / native PS5 build NOT tested")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
