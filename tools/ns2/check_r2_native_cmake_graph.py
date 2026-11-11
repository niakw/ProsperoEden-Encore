#!/usr/bin/env python3
"""Validate the REAL reconfigured PS5 CMake compile graph for opt-in R2.

Read-only graph inspection after CMake configure: no C++ compilation or link.
Reject stale old staging owner, missing R2 defs, ABI overlay drift and
duplicate graphics TUs. This is not a PS5 GPU/device acceptance test.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shlex
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
VENDOR = "4f08b9c9dd2f34deecc9c9fa0d8196dcd6575c2e"
FILES = {
    "vk_staging_buffer_pool.cpp": (
        "vendor/encore-active/eden-vulkan/vk_staging_buffer_pool.cpp",
        "headless/vk_staging_buffer_pool.cpp"),
    "vk_buffer_cache_cost.cpp": (
        "vendor/encore-active/eden-vulkan/vk_buffer_cache_cost.cpp",
        "headless/vk_buffer_cache_cost.cpp"),
    "vulkan_rasterizer.cpp": (
        "vendor/encore-active/eden-vulkan/vulkan_rasterizer.cpp",
        "headless/vulkan_rasterizer.cpp"),
    "vulkan_scheduler.cpp": (
        "vendor/encore-active/eden-vulkan/vulkan_scheduler.cpp",
        "headless/vulkan_scheduler.cpp"),
}
HEADER_FILES = {
    "vendor/encore-active/eden-vulkan/include/video_core/renderer_vulkan/vk_staging_buffer_pool.h":
        "include/video_core/renderer_vulkan/vk_staging_buffer_pool.h",
    "vendor/encore-active/eden-vulkan/include/video_core/renderer_vulkan/ns2_staging_upload_bounds.h":
        "include/video_core/renderer_vulkan/ns2_staging_upload_bounds.h",
    "vendor/encore-active/eden-vulkan/include/video_core/renderer_vulkan/ns2_gpu_retirement_hold.h":
        "include/video_core/renderer_vulkan/ns2_gpu_retirement_hold.h",
    "vendor/encore-active/eden-core/src/video_core/buffer_cache/buffer_cache.h":
        "buffer-pages/video_core/buffer_cache/buffer_cache.h",
    "vendor/encore-active/eden-vulkan/include/video_core/renderer_vulkan/vk_scheduler.h":
        "include/video_core/renderer_vulkan/vk_scheduler.h",
    "vendor/encore-active/eden-vulkan/include/video_core/renderer_vulkan/vk_buffer_cache.h":
        "include/video_core/renderer_vulkan/vk_buffer_cache.h",
}

def git_sha(path: Path) -> str:
    return subprocess.check_output(
        ["git", "hash-object", str(path)], text=True).strip()

def verify_overlay(native: Path) -> None:
    generated = native / "headless"
    for path, (origin, copy) in FILES.items():
        source = ROOT / origin
        dst = generated / Path(copy).name
        if not source.is_file() or not dst.is_file():
            raise RuntimeError(f"missing R2 real overlay translation unit: {path}")
        if git_sha(source) != git_sha(dst):
            raise RuntimeError(f"R2 real translation unit drift: {path}")
        print("R2_NATIVE_GRAPH_REAL_SOURCE_PASS", path, flush=True)
    for original, generated_relative in HEADER_FILES.items():
        source = ROOT / original
        selected = generated / generated_relative
        if not source.is_file() or not selected.is_file():
            raise RuntimeError(f"missing research native header: {generated_relative}")
        if git_sha(source) != git_sha(selected):
            raise RuntimeError(f"research ABI overlay drift: {generated_relative}")
        print("R2_NATIVE_GRAPH_REAL_HEADER_PASS", generated_relative, flush=True)

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("native_build", type=Path)
    args = parser.parse_args()
    native = args.native_build.resolve()
    try:
        actual_vendor = subprocess.check_output(
            ["git", "rev-parse", "HEAD:vendor"], cwd=ROOT, text=True).strip()
        if actual_vendor != VENDOR:
            raise RuntimeError(f"unexpected research vendor pin: {actual_vendor}")
        cache = (native / "CMakeCache.txt").read_text()
        if "EDEN_RESEARCH_NS2_STAGE_BACKING:BOOL=ON" not in cache:
            raise RuntimeError("real native CMake cache did not enable R2")
        if "EDEN_PS5_VULKAN:BOOL=ON" not in cache:
            raise RuntimeError("real native CMake cache did not enable Vulkan")
        verify_overlay(native)
        data = json.loads((native / "compile_commands.json").read_text())
        for name in FILES:
            correct = (native / "headless" / name).resolve()
            matches = [row for row in data
                       if Path(row["file"]).name == name]
            if len(matches) != 1 or Path(matches[0]["file"]).resolve() != correct:
                raise RuntimeError(
                    f"{name} must be selected exactly once from maintained "
                    f"native overlay; matches={[(r['file']) for r in matches]}")
            row = matches[0]
            flags = (list(row["arguments"]) if "arguments" in row
                     else shlex.split(row["command"]))
            if not any(s in ("-DEDEN_RESEARCH_NS2_STAGE_BACKING=1",
                             "-DEDEN_RESEARCH_NS2_STAGE_BACKING")
                       for s in flags):
                raise RuntimeError(f"R2 compile definition absent: {name}")
            if not any(s == "-DPS5_NATIVE" or s.startswith("-DPS5_NATIVE=")
                       for s in flags):
                raise RuntimeError(f"PS5 native compile definition absent: {name}")
            print("R2_NATIVE_GRAPH_SELECTED_EXACTLY_ONCE", name, flush=True)
        old = [row["file"] for row in data
               if str(row["file"]).endswith(
                   "/src/video_core/renderer_vulkan/vk_staging_buffer_pool.cpp")]
        if old:
            raise RuntimeError(f"old staging TU still compiles: {old}")
        subprocess.run(["ninja", "-C", str(native), "-t", "targets", "all"],
                       check=True, stdout=subprocess.DEVNULL)
        print("R2_NATIVE_CMAKE_GRAPH_PASS: four REAL maintained TUs selected, "
              "ABI overlays SHA-matched; no app C++ compile, link or package",
              flush=True)
        return 0
    except (OSError, RuntimeError, subprocess.CalledProcessError) as exc:
        print("R2_NATIVE_CMAKE_GRAPH_FAIL", str(exc), file=sys.stderr, flush=True)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
