#!/usr/bin/env python3
"""Compile full R2 translation units with the *newly configured* native graph.

No objects are emitted. Unlike the earlier cached-flag probe, this uses the
actual R2 CMake source paths, PS5 compiler commands and generated ABI overlay.
Requires check_r2_native_cmake_graph.py to have succeeded first.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shlex
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

TARGETS = ("vk_staging_buffer_pool.cpp", "vk_buffer_cache_cost.cpp",
           "vulkan_rasterizer.cpp", "vulkan_scheduler.cpp")

def check_one(name: str, record: dict, native: Path) -> tuple[str, str]:
    expected = (native / "headless" / name).resolve()
    if Path(record["file"]).resolve() != expected:
        raise RuntimeError(f"{name}: source not the current R2 generated overlay")
    argv = (list(record["arguments"]) if "arguments" in record
            else shlex.split(record["command"]))
    if "-c" not in argv or "-o" not in argv:
        raise RuntimeError(f"{name}: expected genuine CMake native compile flags")
    if not any(x.startswith("-DPS5_NATIVE") for x in argv):
        raise RuntimeError(f"{name}: missing native PS5 compiler definition")
    if "-DEDEN_RESEARCH_NS2_STAGE_BACKING=1" not in argv:
        raise RuntimeError(f"{name}: missing R2 compile definition")
    argv.remove("-c")
    output_index = argv.index("-o")
    del argv[output_index:output_index + 2]
    # Do not generate native objects, depfiles, dependency targets or package
    # metadata. The only PS5 compiler action is syntax checking.
    idx = 0
    while idx < len(argv):
        if argv[idx] in ("-MF", "-MT", "-MQ"):
            del argv[idx:idx+2]
        elif argv[idx] in ("-MD", "-MMD", "-MP", "-Wno-error-all"):
            del argv[idx]
        else:
            idx += 1
    if argv.count(str(record["file"])) != 1:
        raise RuntimeError(f"{name}: CMake native source argument missing/duplicated")
    argv.extend(("-fsyntax-only", "-ferror-limit=8"))
    result = subprocess.run(
        argv, cwd=record["directory"], text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=180)
    if result.returncode:
        raise RuntimeError(
            f"{name}: native PS5 C++ source syntax failure\n"
            + result.stderr[-14000:])
    return name, f"R2_CONFIGURED_NATIVE_SYNTAX_PASS {name}"

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("native_build_dir", type=Path)
    args = ap.parse_args()
    native = args.native_build_dir.resolve()
    try:
        data = json.loads((native / "compile_commands.json").read_text())
        rows = {}
        for name in TARGETS:
            matches = [item for item in data
                       if Path(item["file"]).name == name]
            if len(matches) != 1:
                raise RuntimeError(
                    f"{name}: expected exact one configured R2 TU, got {len(matches)}")
            rows[name] = matches[0]
        # Bounded parallel syntax checks reduce CI time without overloading
        # the native SDK compiler's memory-heavy C++ frontend.
        errors = []
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = {pool.submit(check_one, name, rows[name], native): name
                       for name in TARGETS}
            for future in as_completed(futures):
                try:
                    _, receipt = future.result()
                    print(receipt, flush=True)
                except (OSError, RuntimeError, subprocess.TimeoutExpired) as exc:
                    errors.append(str(exc))
        if errors:
            for error in errors:
                print("R2_CONFIGURED_NATIVE_SYNTAX_FAIL " + error,
                      file=sys.stderr, flush=True)
            return 1
        print("R2_CONFIGURED_NATIVE_SYNTAX_PASS 4 exact R2-native graph TUs; "
              "zero objects, link targets, packages or console actions",
              flush=True)
        return 0
    except (OSError, RuntimeError, ValueError) as exc:
        print("R2_CONFIGURED_NATIVE_SYNTAX_FAIL " + str(exc),
              file=sys.stderr, flush=True)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
