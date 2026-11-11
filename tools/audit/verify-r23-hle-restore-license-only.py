#!/usr/bin/env python3
"""Check whether two *large* Eden HLE commits leave any executable source delta.

Read-only: compares the exact parent of upstream #74 (before introduction)
with upstream #69 (after revert), across the entire HLE service subtree.
It NEVER assumes "Revert" in a commit title implies semantic equivalence.

This tool does not compile code, modify a vendor tree, or update main.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess
import sys

BEFORE = "4dc69c06f764a235bccd01afbfc765d9ddbebc9f"
AFTER = "e255c20db4111485d228c10478bda63aabcfdde5"
SUBTREE = "src/core/hle/service"
NOTICE = (
    "+// SPDX-FileCopyrightText: Copyright 2026 Eden Emulator Project",
    "+// SPDX-License-Identifier: GPL-3.0-or-later",
    "+",
)
HUNK = re.compile(r"^@@ -0,0 \+1,3 @@(?:.*)?$")

def git(path: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(path), *args],
        check=True, capture_output=True, text=True,
    )
    return result.stdout

def inspect(repo: Path) -> dict:
    for sha in (BEFORE, AFTER):
        git(repo, "cat-file", "-e", sha + "^{commit}")
    changes = git(repo, "diff", "--no-ext-diff", "--no-renames", "--numstat",
                  BEFORE, AFTER, "--", SUBTREE)
    stats: dict[str, tuple[str, str]] = {}
    for line in changes.splitlines():
        added, removed, file = line.split("\t", 2)
        stats[file] = (added, removed)
    patch = git(repo, "diff", "--no-ext-diff", "--no-renames", "--unified=0",
                BEFORE, AFTER, "--", SUBTREE)
    blocks = re.split(r"(?=^diff --git )", patch, flags=re.M)
    accepted: list[str] = []
    residual: list[dict] = []
    seen = set()
    for block in blocks:
        if not block.startswith("diff --git "):
            if block.strip():
                raise ValueError("nonempty unrecognized Git diff prefix")
            continue
        head = block.splitlines()[0]
        match = re.match(r"^diff --git a/(.*?) b/(.*?)$", head)
        if not match or match[1] != match[2]:
            residual.append({"path": head, "reason": "rename-or-parse-failure"})
            continue
        file = match[1]
        seen.add(file)
        lines = block.splitlines()
        hunks = [i for i,l in enumerate(lines) if l.startswith("@@ ")]
        patch_content = [l for l in lines[hunks[0] + 1:] if l.startswith(("+", "-"))] if hunks else []
        valid = (stats.get(file) == ("3", "0") and len(hunks) == 1
                 and HUNK.match(lines[hunks[0]]) is not None
                 and tuple(patch_content) == NOTICE)
        if valid:
            accepted.append(file)
        else:
            residual.append({"path": file, "reason": "not-only-3-line-copyright-prefix",
                             "added_removed": stats.get(file),
                             "hunks": len(hunks),
                             "content_preview": patch_content[:7]})
    if set(stats) != seen:
        raise ValueError("numstat/diff file sets disagree")
    # Ignore whitespace-only edits and SPDX comment-only hunks, but not
    # normal statement, string or identifier changes. The first strict pass
    # above enumerates every deviation from precisely +3 licence lines.
    cosmetic_ignored = git(
        repo, "diff", "--no-ext-diff", "--no-renames",
        "--ignore-all-space", "--ignore-blank-lines",
        "-I", r"^([[:space:]]*// SPDX-.*|[[:space:]]*)$",
        "--unified=0", BEFORE, AFTER, "--", SUBTREE
    )
    remaining_code_paths = []
    for line in cosmetic_ignored.splitlines():
        if line.startswith("diff --git "):
            m = re.match(r"^diff --git a/(.*?) b/(.*?)$", line)
            remaining_code_paths.append(m.group(1) if m else line)
    # The original CMake owner must be unchanged after the giant reversion;
    # otherwise a native build can still pick different HLE code.
    native_cmake_changed = bool(git(
        repo, "diff", "--no-ext-diff", "--no-renames", "--numstat",
        BEFORE, AFTER, "--", "src/core/CMakeLists.txt"
    ).strip())
    return {
        "basis": "exact Git blob-to-blob net diff of HLE service subtree",
        "before_74_parent": BEFORE,
        "after_69_revert": AFTER,
        "subtree": SUBTREE,
        "changed_paths": len(stats),
        "copyright_notice_only_paths": len(accepted),
        "behavioral_residual_paths": len(residual),
        "copyright_notice_only_verified": len(stats) > 0 and not residual,
        "cosmetic_only_hle_service_source": not remaining_code_paths,
        "non_cosmetic_hle_paths": remaining_code_paths,
        "non_cosmetic_hle_path_count": len(remaining_code_paths),
        "native_core_cmake_unchanged": not native_cmake_changed,
        "copyright_only_paths": sorted(accepted),
        "residual": residual,
        "native_build_performed": False,
        "ps5_runtime_proven": False,
    }

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("eden_repo", type=Path)
    p.add_argument("--output", type=Path)
    p.add_argument("--assert-license-only", action="store_true")
    args = p.parse_args()
    result = inspect(args.eden_repo)
    content = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(content)
    print("R23_HLE_LARGE_REVERT_GIT_DIFF", json.dumps({
        k: v for k,v in result.items() if k not in ("copyright_only_paths", "residual")
    }, sort_keys=True))
    if args.assert_license_only and (not result["cosmetic_only_hle_service_source"] or
                                     not result["native_core_cmake_unchanged"]):
        print(json.dumps(result["residual"][:12], indent=2), file=sys.stderr)
        return 2
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
