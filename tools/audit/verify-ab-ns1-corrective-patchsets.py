#!/usr/bin/env python3
"""Check staged C01/C02/C04 vendor patches against an unchanged pinned vendor.

All checks are read-only. git apply --check is deliberately used instead of
git apply, so C01/C02/C04 remain UNAPPLIED research inputs. C03 has source SHA
provenance only and is NOT a generated or compiled patch.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
VENDOR = ROOT / "vendor"
PIN = "22b69d6053db41b74edac2633c012f925b84f69e"

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
    "R23-fw23-ns-cmd23": (
        "sources/eden/src/core/hle/service/ns/read_only_application_control_data_interface.cpp",
        "c7606a83bf771c9251ef8a44add72b72a2589870",
        "docs/audits/patchsets/R23-fw23-ns-cmd23.vendor.patch",
    ),
    "R23-glslang-include": (
        "sources/eden/src/video_core/host_shaders/CMakeLists.txt",
        "c4e7ac3f6fe1778423db2933a82ba9febb53637b",
        "docs/audits/patchsets/R23-glslang-include-quoting.vendor.patch",
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
    "R23-viewport": (
        "encore-active/eden-vulkan/vulkan_rasterizer.cpp",
        "921fd6d9db216d3a4a745bcdccb4a454addcf623",
        "docs/audits/patchsets/R23-viewport-negative-y.vendor.patch",
    ),
    "R23-path-root": (
        "encore-active/eden-core/src/common/fs/path_util.cpp",
        "d473cfb2fd57e7026a1da3cd6aa933e75b208b66",
        "docs/audits/patchsets/R23-shared-path-root-posix.vendor.patch",
    ),
    "C04-SDIV32": (
        "encore-active/eden-core/src/dynarmic/backend/x64/emit_x64_data_processing.cpp",
        "3dd13ebc5c519de63672f0699a796009024e4a13",
        "docs/audits/patchsets/C04-dynarmic-two-maintained-x64-fixes.vendor.patch",
    ),
    "C04-SQSHLU": (
        "encore-active/eden-core/src/dynarmic/backend/x64/emit_x64_vector.cpp",
        "4afc50c77b167d6e36d180e04c5cf58259db62b7",
        "docs/audits/patchsets/C04-dynarmic-two-maintained-x64-fixes.vendor.patch",
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
            expected_sources = {src for src, _, p in SOURCES.values() if p == patch}
            changed = re.findall(r"^diff --git a/(\S+) b/(\S+)$", data, re.MULTILINE)
            if (not changed or len(changed) != len(expected_sources) or
                    {a for a,b in changed if a == b} != expected_sources or
                    data.count("\n@@ ") != (2 if name == "R23-glslang-include" else len(expected_sources))):
                raise ValueError(f"{name}: patch contains unexpected/missing maintained source")
            if name == "R23-fw23-ns-cmd23":
                exact_new = (
                    "+        {23, D<&IReadOnlyApplicationControlDataInterface::"
                    'GetApplicationControlData3>, "GetApplicationControlData"},'
                )
                if data.count(exact_new) != 1 or data.count("\n+") != 1:
                    raise ValueError("FW23 cmd23 staged patch must add exactly one IPC alias")
            # Applicability is not proof of actual native compiled-owner selection.
            run_git("apply", "--check", str(relative_patch))
            result["patch_staged_and_context_valid"] = True
        results[name] = result
    dirty_after = run_git("status", "--porcelain", "--untracked-files=all")
    if dirty_after != dirty_before:
        raise AssertionError("read-only audit changed vendor files")
    if not all(row["patch_staged_and_context_valid"] for key, row in results.items()
               if key in ("C01", "C02", "C04-SDIV32", "C04-SQSHLU", "R23-viewport", "R23-path-root", "R23-glslang-include", "R23-fw23-ns-cmd23")):
        raise AssertionError("all staged owner hunks must have valid context")
    print(json.dumps({
        "scope": "C01/C02/C04/R23 viewport/path root/glslang/FW23 NS cmd23 patch contexts, C03 Git blobs (not compiled)",
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
