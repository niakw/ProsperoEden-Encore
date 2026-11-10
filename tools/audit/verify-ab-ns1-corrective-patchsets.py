#!/usr/bin/env python3
"""Check staged C01/C02 vendor patches against an unchanged pinned vendor.

All checks are read-only. git apply --check is deliberately used instead of
git apply, so C01/C02 remain UNAPPLIED research inputs. C03 has source SHA
provenance only and is NOT a generated or compiled patch.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
VENDOR = ROOT / "vendor"
PIN = "f9f08786de9e623f2a40865027451dbf0676f6b4"

SOURCES = {
    "C01": (
        "encore-active/eden-core/src/core/file_sys/fsmitm_romfsbuild.cpp",
        "94cbb31b48054a62d88446a3920ecef734861b18",
        "docs/audits/patchsets/C01-romfs-destructor.vendor.patch",
    ),
    "C02": (
        "encore-active/ns2-runtime/ampere/shader_recompiler/backend/spirv/"
        "emit_spirv_context_get_set.cpp",
        "f768235d3a6667f18ee5900311364c7d9a7853ba",
        "docs/audits/patchsets/C02-shared-spirv-nan.vendor.patch",
    ),
    "C03-command-buffer": (
        "encore-active/ps5-mesa/src/amd/vulkan/radv_cmd_buffer.c",
        "9dd12c19a1a277a2753432e1411a449fdf923c4a",
        None,
    ),
    "C03-meta-buffer": (
        "sources/ps5-mesa/src/amd/vulkan/meta/radv_meta_buffer.c",
        "559272a4c99014a1cfb6c62aa7d81b2301729fd7",
        None,
    ),
    "C03-meta-copy": (
        "sources/ps5-mesa/src/amd/vulkan/meta/radv_meta_copy.c",
        "b48ad04b1637898c5e2b95e438e2e9ae9ac522a1",
        None,
    ),
}


def git_blob_sha(path: Path) -> str:
    size = path.stat().st_size
    h = hashlib.sha1(b"blob " + str(size).encode() + b"\0")
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def run_git(*args: str) -> str:
    proc = subprocess.run(
        ["git", "-C", str(VENDOR), *args], text=True, capture_output=True,
        check=False,
    )
    if proc.returncode:
        raise RuntimeError(
            f"git {args!r} exited {proc.returncode}: {proc.stderr.strip()[:900]}"
        )
    return proc.stdout.strip()


def main() -> int:
    actual_pin = run_git("rev-parse", "HEAD")
    if actual_pin != PIN:
        raise ValueError(f"vendor pin changed: expected {PIN}, got {actual_pin}")
    dirty_before = run_git("status", "--porcelain", "--untracked-files=all")
    if dirty_before:
        raise ValueError("vendor working tree not clean before inspection")
    results = {}
    for name, (source, expected_sha, patch) in SOURCES.items():
        target = VENDOR / source
        sha = git_blob_sha(target)
        if sha != expected_sha:
            raise ValueError(f"{name}: source changed: {source}: {sha}")
        result = {
            "path": source,
            "selected_source_git_blob": sha,
            "patch_applied": False,
            "patch_staged_and_context_valid": False,
            "compiled": False,
            "tested_on_ps5": False,
        }
        if patch is not None:
            relative_patch = ROOT / patch
            data = relative_patch.read_text()
            before = f"--- a/{source}\n"
            after = f"+++ b/{source}\n"
            if data.count(before) != 1 or data.count(after) != 1:
                raise ValueError(f"{name}: patch not scoped solely to maintained {source}")
            if data.count("diff --git ") != 1 or data.count("\n@@ ") != 1:
                raise ValueError(f"{name}: unexpected patch structure")
            run_git("apply", "--check", str(relative_patch))
            result["patch_staged_and_context_valid"] = True
        results[name] = result
    dirty_after = run_git("status", "--porcelain", "--untracked-files=all")
    if dirty_after != dirty_before:
        raise AssertionError("read-only audit changed vendor files")
    if not all(row["patch_staged_and_context_valid"] for key, row in results.items()
               if key in ("C01", "C02")):
        raise AssertionError("both staged patches must have valid context")
    print(json.dumps({
        "scope": "C01/C02 exact Git patch check, C03 exact Git blob freeze",
        "vendor_gitlink": PIN,
        "vendor_worktree_clean": True,
        "implementation_proof": False,
        "units": results,
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, RuntimeError, ValueError, AssertionError) as error:
        print(f"AB_NS1_PATCHSET_PROVENANCE_FAIL: {error}", file=sys.stderr)
        sys.exit(2)
