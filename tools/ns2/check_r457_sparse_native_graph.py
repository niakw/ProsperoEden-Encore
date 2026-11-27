#!/usr/bin/env python3
"""Verify the current native sparse graph from CMake, without revision allowlists.

The engine gitlink selects one physical vendor checkout. sources/ is immutable
upstream input; every maintained sparse owner must be compiled from
vendor/encore-active. This gate follows the configured compile graph instead of
encoding a history of vendor commit/blob hashes.
"""
from __future__ import annotations

import json
from pathlib import Path
import shlex
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
VENDOR = ROOT / "vendor"

def argv(row: dict) -> list[str]:
    return list(row["arguments"]) if "arguments" in row else shlex.split(row["command"])

def ends_with(path: Path, suffix: str) -> bool:
    wanted = Path(suffix).parts
    return path.parts[-len(wanted):] == wanted

def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: check_r457_sparse_native_graph.py <native-build-dir>")
    native = Path(sys.argv[1]).resolve()
    db_path = native / "compile_commands.json"
    cache_path = native / "CMakeCache.txt"
    if not db_path.is_file() or not cache_path.is_file():
        raise RuntimeError("native CMake graph is missing")

    pinned = subprocess.check_output(
        ["git", "rev-parse", "HEAD:vendor"], cwd=ROOT, text=True
    ).strip()
    checkout = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=VENDOR, text=True
    ).strip()
    if pinned != checkout:
        raise RuntimeError(f"vendor checkout differs from engine gitlink: {checkout} != {pinned}")

    subprocess.check_call(
        ["python3", "-B", "tools/check-source-tree-layout.py"], cwd=VENDOR
    )

    cmake = (ROOT / "headless/CMakeLists.txt").read_text()
    cache = cache_path.read_text()
    if "set(EDEN_NS2_SPARSE_BACKING ON)" not in cmake:
        raise RuntimeError("production sparse backing is not selected")
    if "EDEN_PS5_VULKAN:BOOL=ON" not in cache:
        raise RuntimeError("real native Vulkan profile is not configured")

    db = json.loads(db_path.read_text())
    active_root = (VENDOR / "encore-active").resolve()
    sources_root = (VENDOR / "sources").resolve()

    def active_rows_for_suffix(suffix: str) -> list[dict]:
        rows = []
        for row in db:
            path = Path(row["file"]).resolve()
            if ends_with(path, suffix) and (path == active_root or active_root in path.parents):
                rows.append(row)
        return rows

    def assert_one_active(suffix: str, label: str) -> dict:
        rows = active_rows_for_suffix(suffix)
        if len(rows) != 1:
            raise RuntimeError(f"{label}: expected one encore-active owner for {suffix}, got {len(rows)}")
        selected = Path(rows[0]["file"]).resolve()
        conflicting = [
            Path(row["file"]).resolve() for row in db
            if ends_with(Path(row["file"]).resolve(), suffix)
            and sources_root in Path(row["file"]).resolve().parents
        ]
        if conflicting:
            raise RuntimeError(f"{label}: upstream sources owner compiled beside override: {conflicting}")
        return rows[0]

    selected: list[tuple[str, dict, bool]] = []

    # Engine-owned sparse adapter/storage bridge: exactly one configured TU.
    for path in (ROOT / "src/ns2_sparse_guest.cpp", ROOT / "src/host_memory.cpp"):
        rows = [row for row in db if Path(row["file"]).resolve() == path.resolve()]
        if len(rows) != 1:
            raise RuntimeError(f"expected one configured engine owner {path}, got {len(rows)}")
        selected.append((path.name, rows[0], True))

    # Maintained vendor owners. Their directory may still move while legacy
    # roots are folded into encore-active/eden; the logical source suffix and
    # encore-active ownership are the stable contract.
    guest_variants = []
    for suffix in ("core/memory_native_a32.cpp", "core/memory_native_standard.cpp"):
        guest_variants.extend(active_rows_for_suffix(suffix))
    if len(guest_variants) != 1:
        raise RuntimeError(f"expected one native guest PTE owner, got {len(guest_variants)}")
    guest_path = Path(guest_variants[0]["file"]).resolve()
    if sources_root in guest_path.parents:
        raise RuntimeError("native guest PTE resolved to sources/")
    selected.append(("native_guest_pte", guest_variants[0], True))

    for suffix, label in (
        ("core/hle/kernel/k_shared_memory.cpp", "native_shared_memory"),
        ("core/hle/kernel/k_memory_manager.cpp", "native_memory_manager"),
        ("core/hle/kernel/init/init_slab_setup.cpp", "native_slab_setup"),
        ("core/hle/kernel/k_page_heap.cpp", "native_page_heap"),
    ):
        selected.append((label, assert_one_active(suffix, label), True))

    def has_ps5_target(command: list[str]) -> bool:
        for i, token in enumerate(command):
            if token == "--target=x86_64-sie-ps5":
                return True
            if token in ("-target", "--target") and i + 1 < len(command):
                if command[i + 1] == "x86_64-sie-ps5":
                    return True
        return False

    for label, row, require_sparse in selected:
        command = argv(row)
        if not has_ps5_target(command):
            raise RuntimeError(f"{label}: configured command is not the PS5 target")
        if require_sparse and not any(
            token.startswith("-DEDEN_NS2_SPARSE_BACKING") for token in command
        ):
            raise RuntimeError(f"{label}: missing EDEN_NS2_SPARSE_BACKING")

        # Reuse the exact configured compiler/includes/definitions; remove only
        # output/dependency-generation switches and ask the compiler for syntax.
        cleaned: list[str] = []
        i = 0
        while i < len(command):
            token = command[i]
            if token in ("-o", "-MF", "-MT", "-MQ"):
                i += 2
                continue
            if token in ("-c", "-MD", "-MMD", "-MP"):
                i += 1
                continue
            cleaned.append(token)
            i += 1
        if "-fsyntax-only" not in cleaned:
            cleaned.append("-fsyntax-only")
        run = subprocess.run(
            cleaned, cwd=row.get("directory", str(native)),
            text=True, capture_output=True, timeout=90,
        )
        if run.returncode != 0:
            raise RuntimeError(
                f"{label}: configured native syntax failed\n"
                + run.stdout[-3000:] + run.stderr[-6000:]
            )
        print("R457_NS2_SPARSE_NATIVE_OWNER_PASS", label, row["file"], flush=True)

    print(
        "R457_NS2_SPARSE_NATIVE_GRAPH_PASS",
        f"owners={len(selected)}",
        "gitlink_match=1",
        "active_only=1",
        "revision_allowlists=0",
        "real_ps5_commands=1",
    )

if __name__ == "__main__":
    main()
