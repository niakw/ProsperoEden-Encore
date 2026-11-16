#!/usr/bin/env python3
"""Host contract for the exact upstream LZ4 #1601 build-metadata adaptation."""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
source = ROOT / "vendor/sources/eden-cpm/lz4/ebb370ca83/build/cmake/CMakeLists.txt"
stage = ROOT / "tools/stage-lz4-cmake-policy.py"
prepare = (ROOT / "tools/prepare-build.sh").read_text(encoding="utf-8")
raw = source.read_bytes()
assert raw.count(b"cmake_minimum_required(VERSION 3.5)\n") == 1
assert b"cmake_minimum_required(VERSION 3.5...3.16)\n" not in raw
assert 'python3 -B tools/stage-lz4-cmake-policy.py "$eden"' in prepare

with tempfile.TemporaryDirectory(prefix="encore-lz4-policy-") as td:
    eden = Path(td)
    target = eden / ".cache/cpm/lz4/ebb370ca83/build/cmake/CMakeLists.txt"
    target.parent.mkdir(parents=True)
    target.write_bytes(raw)
    subprocess.run(["python3", "-B", str(stage), str(eden)], cwd=ROOT, check=True)
    out = target.read_bytes()
    assert out.count(b"cmake_minimum_required(VERSION 3.5...3.16)\n") == 1
    assert out.replace(
        b"cmake_minimum_required(VERSION 3.5...3.16)\n",
        b"cmake_minimum_required(VERSION 3.5)\n",
        1,
    ) == raw
    # Idempotent on an incremental CPM cache.
    subprocess.run(["python3", "-B", str(stage), str(eden)], cwd=ROOT, check=True)
    assert target.read_bytes() == out
    # Unknown/stale bytes fail closed.
    target.write_bytes(out + b"# drift\n")
    bad = subprocess.run(["python3", "-B", str(stage), str(eden)], cwd=ROOT)
    assert bad.returncode != 0
print("PASS LZ4 upstream #1601 policy-only staging; immutable vendor source preserved")
