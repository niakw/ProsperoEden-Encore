#!/usr/bin/env python3
"""Read-only compile_commands.json provenance triage for Eden Encore A/B NS1.

No build, no compiler execution, no repository mutations. A compile database proves
only which source paths were *scheduled* for a target; not a linked binary, runtime
reachability, or the original byte provenance of a copied RADV build input.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

OWNERS = {
    "audio_adapter": "audio.cpp",
    "romfs_builder": "fsmitm_romfsbuild.cpp",
    "shader_emitter": "emit_spirv_context_get_set.cpp",
    "jit_data": "emit_x64_data_processing.cpp",
    "jit_vector": "emit_x64_vector.cpp",
    "jit_fp": "emit_x64_floating_point.cpp",
    "radv_cmd": "radv_cmd_buffer.c",
    "radv_meta_buffer": "radv_meta_buffer.c",
    "radv_meta_copy": "radv_meta_copy.c",
}
PATH_HINTS = {
    "audio_adapter": "/headless/audio.cpp",
    "romfs_builder": "/core/file_sys/fsmitm_romfsbuild.cpp",
    "shader_emitter": "/shader_recompiler/backend/spirv/emit_spirv_context_get_set.cpp",
    "jit_data": "/backend/x64/emit_x64_data_processing.cpp",
    "jit_vector": "/backend/x64/emit_x64_vector.cpp",
    "jit_fp": "/backend/x64/emit_x64_floating_point.cpp",
    "radv_cmd": "/amd/vulkan/radv_cmd_buffer.c",
    "radv_meta_buffer": "/amd/vulkan/meta/radv_meta_buffer.c",
    "radv_meta_copy": "/amd/vulkan/meta/radv_meta_copy.c",
}

def source_path(entry: dict) -> str:
    value = entry.get("file")
    directory = entry.get("directory")
    if not isinstance(value, str) or not value or not isinstance(directory, str) or not directory:
        raise ValueError("compile command missing non-empty file/directory")
    path = Path(value)
    if not path.is_absolute():
        path = Path(directory) / path
    return path.resolve(strict=False).as_posix()

def kind(path: str) -> str:
    if "/vendor/encore-active/" in path:
        return "maintained-source-path"
    if "/vendor/sources/" in path:
        return "pinned-source-path"
    if "/headless/" in path:
        return "project-source-path"
    if "/.deps/" in path or "/radv-src/" in path:
        return "build-copy-origin-unknown"
    return "other-path-origin-unknown"

def inspect(commands: list) -> dict:
    if not isinstance(commands, list):
        raise ValueError("compile database root must be an array")
    found = {key: [] for key in OWNERS}
    for entry in commands:
        if not isinstance(entry, dict):
            raise ValueError("compile database contains a non-object entry")
        path = source_path(entry)
        for key, filename in OWNERS.items():
            if path.endswith(PATH_HINTS[key]) and Path(path).name == filename:
                found[key].append(path)
    rows = {}
    for key, paths in found.items():
        unique = sorted(set(paths))
        rows[key] = {
            "status": "not-in-database" if not unique else
                      "one-source-path" if len(unique) == 1 else
                      "ambiguous-multiple-source-paths",
            "compilation_entries": len(paths),
            "source_paths": [{"path": path, "path_class": kind(path)} for path in unique],
        }
    return rows

def self_test() -> None:
    p = "/work/vendor/encore-active/eden-core/src/dynarmic/backend/x64/emit_x64_vector.cpp"
    a = {"directory": "/work", "file": p, "command": "c++ -c vector.cpp"}
    assert source_path(a) == p
    r = inspect([a, a])
    assert r["jit_vector"]["status"] == "one-source-path"
    assert r["jit_vector"]["compilation_entries"] == 2
    b = {"directory": "/work", "file": "vendor/sources/eden/src/dynarmic/src/dynarmic/backend/x64/emit_x64_vector.cpp"}
    r = inspect([a, b])
    assert r["jit_vector"]["status"] == "ambiguous-multiple-source-paths"
    assert r["romfs_builder"]["status"] == "not-in-database"
    assert kind("/tmp/.deps/work/radv-src/src/amd/vulkan/radv_cmd_buffer.c") == "build-copy-origin-unknown"
    try:
        inspect([{"directory": "/work"}])
    except ValueError:
        pass
    else:
        raise AssertionError("missing input was not rejected")

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("compile_commands", nargs="*", type=Path,
                        help="one or more existing JSON compile databases (native and RADV may be separate)")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--require", action="append", choices=sorted(OWNERS),
                        help="optionally gate named source owner (repeatable)")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        print("AB_NS1_COMPILE_OWNER_SELFTEST_OK")
        return 0
    if not args.compile_commands:
        parser.error("provide at least one existing compile_commands.json or --self-test")
    commands = []
    try:
        for f in args.compile_commands:
            with f.open(encoding="utf-8") as handle:
                data = json.load(handle)
            if not isinstance(data, list):
                raise ValueError(f"{f}: root must be an array")
            commands.extend(data)
        result = inspect(commands)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(json.dumps({"status": "incomplete-inputs", "error": str(error)}))
        return 2
    missing = [k for k in (args.require or []) if result[k]["status"] != "one-source-path"]
    print(json.dumps({
        "scope": "compile-command-paths-only",
        "linked_binary_provenance": "not-established",
        "copied_RADV_inputs_require_build_receipts": True,
        "databases": [str(p) for p in args.compile_commands],
        "required_owner_gaps": missing,
        "owners": result,
    }, indent=2, sort_keys=True))
    return int(bool(missing))

if __name__ == "__main__":
    sys.exit(main())
