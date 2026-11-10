#!/usr/bin/env python3
"""Compile broad real PS5 video/Vulkan translation units in syntax-only mode.

Uses the current native CMake compile database and toolchain, NOT a fabricated
host compiler invocation. No objects, archive, ELF, ZIP or release are built.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from pathlib import Path
import shlex
import subprocess
import sys


def source_file(record: dict) -> Path:
    candidate = Path(record["file"])
    return candidate if candidate.is_absolute() else Path(record["directory"]) / candidate


def category(path: str) -> tuple[int, str] | None:
    # First scan the upstream consumers of the two failed header contracts.
    if "/source/src/video_core/renderer_vulkan/" in path:
        return (0, path)
    if "/source/src/video_core/texture_cache/" in path:
        return (1, path)
    if "/vendor/encore-active/eden-vulkan/" in path:
        return (2, path)
    if "/native-local/headless/" in path and path.endswith(".cpp"):
        return (3, path)
    if "/headless/" in path and (
        "/vulkan_" in path or "/mihawk_" in path or "/fsr" in path
    ):
        return (4, path)
    # After the high-risk Vulkan/FSR3 owners, sweep other *real* native
    # translation units. They are present in CMake's exact PS5 compile DB
    # but were never covered by the previous 163/163 scan. Keep the priority
    # order deterministic so --max-tus can bound expensive host work.
    if "/source/src/video_core/" in path:
        return (5, path)
    if "/source/src/core/" in path:
        return (6, path)
    if "/source/src/audio_core/" in path:
        return (7, path)
    if "/source/src/common/" in path:
        return (8, path)
    return None


def command(record: dict) -> list[str]:
    argv = (list(record["arguments"]) if "arguments" in record
            else shlex.split(record["command"]))
    assert "-c" in argv and "-o" in argv, record["file"]
    argv.remove("-c")
    p = argv.index("-o")
    del argv[p:p + 2]
    # Avoid emitting depfiles during syntax validation.
    for flag in ("-MD", "-MMD", "-MP"):
        while flag in argv:
            argv.remove(flag)
    for flag in ("-MT", "-MQ", "-MF"):
        while flag in argv:
            p = argv.index(flag)
            del argv[p:p + 2]
    argv.extend(("-fsyntax-only", "-ferror-limit=5"))
    return [flag for flag in argv if flag != "-Wno-error-all"]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("native_build_dir", type=Path)
    parser.add_argument("--jobs", type=int, default=4)
    parser.add_argument("--max-tus", type=int, default=240)
    args = parser.parse_args()
    if not 1 <= args.jobs <= 8 or args.max_tus < 40:
        parser.error("jobs must be 1..8 and max-tus >=40")
    path = args.native_build_dir.resolve() / "compile_commands.json"
    records = json.loads(path.read_text())
    eligible = []
    for record in records:
        file = source_file(record)
        grouping = category(file.as_posix())
        if grouping is not None and file.is_file() and file.suffix in (".cpp", ".cc"):
            eligible.append((grouping, file, record))
    eligible.sort(key=lambda item: item[0])
    if len(eligible) < 40:
        raise RuntimeError(f"Expected at least 40 real video/Vulkan C++ units; found {len(eligible)}")
    selected = eligible[:args.max_tus]
    print(f"PS5_VIDEO_SYNTAX_SCOPE selected={len(selected)} eligible={len(eligible)} "
          f"unscanned={len(eligible)-len(selected)} jobs={args.jobs}", flush=True)

    def check(item: tuple):
        _grouping, file, record = item
        try:
            result = subprocess.run(command(record), cwd=record["directory"],
                                    capture_output=True, text=True, timeout=180)
        except (OSError, ValueError, AssertionError, subprocess.TimeoutExpired) as exc:
            return file, False, str(exc)
        return file, result.returncode == 0, result.stderr[-3500:]

    failed = []
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        futures = [pool.submit(check, item) for item in selected]
        for future in as_completed(futures):
            file, ok, diagnostic = future.result()
            if not ok:
                failed.append((str(file), diagnostic))
                print(f"PS5_VIDEO_SYNTAX_FAIL {file}\n{diagnostic}", file=sys.stderr, flush=True)
            else:
                print(f"PS5_VIDEO_SYNTAX_OK {file.name}", flush=True)
    if failed:
        print(f"PS5_VIDEO_SYNTAX_RESULT FAILED={len(failed)} PASS={len(selected)-len(failed)}",
              file=sys.stderr)
        return 1
    print(f"PS5_VIDEO_SYNTAX_PASS scanned={len(selected)} unscanned={len(eligible)-len(selected)} "
          "PS5_hardware_unverified=1 no_link=1", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
