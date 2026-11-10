#!/usr/bin/env python3
"""Read-only evidence for 5 historical Eden C++ sources replaced by native owners.

Checks an EXISTING CMake compile_commands.json and Git-blob equality against the
pinned vendor. Does not compile/link or attest header inclusion or an ELF.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import tempfile

ROOT = Path(__file__).resolve().parents[2]
OWNERS = {
    "kernel_address_arbiter": (
        "src/core/hle/kernel/k_address_arbiter.cpp",
        "vendor/encore-active/ns2-runtime/kernel_wait64/core/hle/kernel/k_address_arbiter.cpp",
        "/vendor/encore-active/ns2-runtime/kernel_wait64/core/hle/kernel/k_address_arbiter.cpp"),
    "kernel_svc": (
        "src/core/hle/kernel/svc.cpp",
        "vendor/encore-active/ns2-runtime/gpu_access_svc/core/hle/kernel/svc.cpp",
        "/vendor/encore-active/ns2-runtime/gpu_access_svc/core/hle/kernel/svc.cpp"),
    "kernel_svc_address_arbiter": (
        "src/core/hle/kernel/svc/svc_address_arbiter.cpp",
        "vendor/encore-active/ns2-runtime/kernel_wait64/core/hle/kernel/svc/svc_address_arbiter.cpp",
        "/vendor/encore-active/ns2-runtime/kernel_wait64/core/hle/kernel/svc/svc_address_arbiter.cpp"),
    "spirv_emit_context": (
        "src/shader_recompiler/backend/spirv/spirv_emit_context.cpp",
        "vendor/encore-active/ns2-runtime/ampere/shader_recompiler/backend/spirv/spirv_emit_context.cpp",
        "/vendor/encore-active/ns2-runtime/ampere/shader_recompiler/backend/spirv/spirv_emit_context.cpp"),
    "vulkan_texture_cache": (
        "src/video_core/renderer_vulkan/vk_texture_cache.cpp",
        "vendor/encore-active/eden-vulkan/vk_texture_cache_cost.cpp",
        "/native-local/headless/vk_texture_cache_cost.cpp"),
}

def git_blob_hash(path: Path) -> str:
    if not path.is_file():
        raise FileNotFoundError(path)
    h = hashlib.sha1(b"blob " + str(path.stat().st_size).encode() + b"\0")
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def as_source_path(row: dict) -> str:
    file, directory = row.get("file"), row.get("directory")
    if not isinstance(file, str) or not file or not isinstance(directory, str) or not directory:
        raise ValueError("compile DB entry requires file and directory")
    p = Path(file)
    return str((p if p.is_absolute() else Path(directory) / p).resolve(strict=False))

def inspect(commands: list, root: Path) -> dict:
    if not isinstance(commands, list):
        raise ValueError("compile DB must contain an array")
    paths = [as_source_path(x) for x in commands]
    result = {}
    for name, (original, maintained, suffix) in OWNERS.items():
        orig_paths = sorted({x for x in paths if x.endswith("/" + original)})
        owners = sorted({x for x in paths if x.endswith(suffix)})
        canonical = root / maintained
        row = {
            "original": original,
            "maintained": maintained,
            "scheduled_owner_paths": owners,
            "original_scheduled_paths": orig_paths,
            "expected_blob": None,
            "selected_blob": None,
        }
        if not canonical.is_file():
            status = "maintained-owner-missing"
        elif len(owners) > 1 or orig_paths:
            status = "ambiguous-or-original-still-compiled"
        elif not owners:
            status = "owner-not-scheduled-in-this-db"
        elif not Path(owners[0]).is_file():
            status = "scheduled-input-missing-on-disk"
        else:
            row["expected_blob"] = git_blob_hash(canonical)
            row["selected_blob"] = git_blob_hash(Path(owners[0]))
            status = ("scheduled-maintained-exact-bytes" if row["expected_blob"] == row["selected_blob"]
                      else "scheduled-maintained-path-byte-mismatch")
        row["status"] = status
        result[name] = row
    counts = dict(sorted(Counter(x["status"] for x in result.values()).items()))
    return {
        "scope": "historical native CMake source schedule only",
        "build_or_link_proof": False,
        "cases": result, "counts": counts,
        "all_exact": counts == {"scheduled-maintained-exact-bytes": len(OWNERS)},
    }

def self_test() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        db = []
        for name, (_, maintained, _) in OWNERS.items():
            canonical = root / maintained
            canonical.parent.mkdir(parents=True, exist_ok=True)
            canonical.write_text("source owner " + name + "\n")
            selected = (root / "cache/native-local/headless/vk_texture_cache_cost.cpp"
                        if name == "vulkan_texture_cache" else canonical)
            selected.parent.mkdir(parents=True, exist_ok=True)
            if not selected.exists():
                selected.write_bytes(canonical.read_bytes())
            db.append({"directory": str(root), "file": str(selected)})
        assert inspect(db, root)["all_exact"]
        db[0]["file"] = str(root / OWNERS["kernel_address_arbiter"][0])
        assert inspect(db, root)["cases"]["kernel_address_arbiter"]["status"] == "ambiguous-or-original-still-compiled"
        db[0]["file"] = str(root / OWNERS["kernel_address_arbiter"][1])
        (root / "cache/native-local/headless/vk_texture_cache_cost.cpp").write_text("unknown variant\n")
        assert inspect(db, root)["cases"]["vulkan_texture_cache"]["status"] == "scheduled-maintained-path-byte-mismatch"
    print("R18_REPLACED_NATIVE_OWNER_SELFTEST_OK")

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("compile_db", nargs="?", type=Path)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    if args.compile_db is None:
        parser.error("specify an existing compile_commands.json or --self-test")
    with args.compile_db.open(encoding="utf-8") as handle:
        commands = json.load(handle)
    print(json.dumps(inspect(commands, args.root), indent=2, sort_keys=True))

if __name__ == "__main__":
    main()
