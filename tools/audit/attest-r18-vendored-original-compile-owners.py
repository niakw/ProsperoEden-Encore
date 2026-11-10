#!/usr/bin/env python3
"""Audit exact original-vs-mutated Eden source owners using an EXISTING compile DB.

Read-only: no compilation, linking, device access, downloads or source changes.
Git blob SHA-1 identities are recomputed from the bytes on disk, not inferred
from path strings or from source manifest syntax. Headers need separate -H /
depfile provenance and are not declared active by this tool.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = ROOT / "docs/audits/R18_VENDOR_EDEN_35_SOURCE_MUTATIONS_2026-11-10.json"


def blob_hash(path: Path) -> str:
    size = path.stat().st_size
    h = hashlib.sha1()
    h.update(b"blob " + str(size).encode("ascii") + b"\0")
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def source_path(item: dict) -> str:
    if not isinstance(item, dict):
        raise ValueError("compile database entries must be objects")
    file, directory = item.get("file"), item.get("directory")
    if not isinstance(file, str) or not file or not isinstance(directory, str) or not directory:
        raise ValueError("compile command missing file or directory")
    path = Path(file)
    return str((path if path.is_absolute() else Path(directory) / path).resolve(strict=False))


def inspect(manifest: dict, compile_commands: list, root: Path) -> dict:
    if manifest.get("schema") != "vendor-eden-snapshot-tree-compare-v1":
        raise ValueError("unexpected manifest schema")
    rows = manifest.get("rows")
    if not isinstance(rows, list) or len(rows) != 35:
        raise ValueError("source manifest must contain exactly 35 rows")
    if not isinstance(compile_commands, list):
        raise ValueError("compile database must be a JSON array")
    sources = [source_path(item) for item in compile_commands]
    results = []
    for item in rows:
        relative = item.get("path")
        official = item.get("official_blob")
        mutated = item.get("vendor_blob")
        if (not isinstance(relative, str) or not relative.startswith("src/")
                or relative.startswith("src/../")
                or ".." in Path(relative).parts
                or not all(isinstance(v, str) and len(v) == 40 for v in (official, mutated))):
            raise ValueError(f"invalid source record: {item!r}")
        vendor_file = root / "vendor/sources/eden" / relative
        vendor_hash = blob_hash(vendor_file) if vendor_file.is_file() else None
        vendor_manifest_ok = vendor_hash == mutated

        # The compilation database describes translation units, not header
        # resolution or header visibility.
        if Path(relative).suffix not in (".c", ".cc", ".cpp", ".cxx", ".C"):
            status = "header-not-attested-by-compile-db"
            matches = []
        else:
            matches = sorted(set(src for src in sources if src.endswith("/" + relative)))
            if not matches:
                status = "source-not-scheduled-in-this-db"
            elif len(matches) != 1:
                status = "ambiguous-multiple-source-paths"
            elif not Path(matches[0]).is_file():
                status = "scheduled-source-not-on-disk"
            else:
                selected = blob_hash(Path(matches[0]))
                matched_active = any(
                    Path(matches[0]).resolve(strict=False) == candidate.resolve(strict=False)
                    and candidate.is_file()
                    and blob_hash(candidate) == selected
                    for candidate in (
                        root / "vendor/encore-active/eden-shader" / relative,
                        root / "vendor/encore-active/eden-core" / relative,
                    )
                )
                status = ("scheduled-official-original" if selected == official else
                          "scheduled-vendor-mutated" if selected == mutated else
                          "scheduled-maintained-override" if matched_active else
                          "scheduled-unrecognized-source")
        results.append({
            "path": relative,
            "status": status,
            "official_blob": official,
            "vendor_snapshot_blob": mutated,
            "vendor_snapshot_file_matches_manifest": vendor_manifest_ok,
            "scheduled_source_paths": matches,
            "scheduled_blob": blob_hash(Path(matches[0])) if
                len(matches) == 1 and Path(matches[0]).is_file() else None,
        })
    return {
        "scope": "existing-compile-command-source-identities-only",
        "proves-linked-binary-or-header-inclusion": False,
        "upstream_commit": manifest.get("upstream_commit"),
        "vendor_commit": manifest.get("vendor_commit"),
        "total_source_divergences": len(rows),
        "status_counts": dict(sorted(Counter(x["status"] for x in results).items())),
        "all_vendor_snapshot_blobs_match_manifest": all(
            x["vendor_snapshot_file_matches_manifest"] for x in results),
        "rows": results,
    }


def self_test() -> None:
    with tempfile.TemporaryDirectory(prefix="r18-owner-") as folder:
        top = Path(folder)
        root = top / "repo"
        rel = "src/video_core/demo.cpp"
        filename = root / "vendor/sources/eden" / rel
        filename.parent.mkdir(parents=True)
        filename.write_bytes(b"vendor edit\n")
        official_path = top / "source" / rel
        official_path.parent.mkdir(parents=True)
        official_path.write_bytes(b"official\n")
        def git_hash_bytes(data: bytes) -> str:
            return hashlib.sha1(b"blob " + str(len(data)).encode() +
                                b"\0" + data).hexdigest()
        sample = {
            "path": rel,
            "official_blob": git_hash_bytes(b"official\n"),
            "vendor_blob": git_hash_bytes(b"vendor edit\n"),
        }
        # The fixed 35-row fixture uses distinct paths to reject accidental
        # matching of a different translation unit's same basename.
        rows = [sample]
        for i in range(34):
            data = b"x" + bytes([i])
            sub = f"src/core/audit_{i}.h"
            p = root / "vendor/sources/eden" / sub
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(data)
            rows.append({"path": sub, "official_blob": git_hash_bytes(b"y"+bytes([i])),
                         "vendor_blob": git_hash_bytes(data)})
        manifest = {"schema": "vendor-eden-snapshot-tree-compare-v1", "rows": rows}
        db = [{"directory": str(top), "file": str(official_path)}]
        x = inspect(manifest, db, root)
        assert x["status_counts"] == {
            "header-not-attested-by-compile-db": 34,
            "scheduled-official-original": 1,
        }
        assert x["all_vendor_snapshot_blobs_match_manifest"]
        official_path.write_bytes(b"vendor edit\n")
        assert inspect(manifest, db, root)["rows"][0]["status"] == "scheduled-vendor-mutated"
        official_path.write_bytes(b"unknown\n")
        assert inspect(manifest, db, root)["rows"][0]["status"] == "scheduled-unrecognized-source"
        maintained = root / "vendor/encore-active/eden-shader" / rel
        maintained.parent.mkdir(parents=True, exist_ok=True)
        maintained.write_bytes(b"maintained\n")
        maintained_db = [{"directory": str(root), "file": str(maintained)}]
        assert inspect(manifest, maintained_db, root)["rows"][0]["status"] == "scheduled-maintained-override"
        official_path.unlink()
        assert inspect(manifest, db, root)["rows"][0]["status"] == "scheduled-source-not-on-disk"
        assert inspect(manifest, [], root)["rows"][0]["status"] == "source-not-scheduled-in-this-db"
        filename.write_bytes(b"untracked\n")
        assert not inspect(manifest, [], root)["all_vendor_snapshot_blobs_match_manifest"]
    print("R18_ORIGINAL_VS_VENDOR_COMPILE_OWNER_SELFTEST_OK")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("compile_commands", nargs="?", type=Path)
    p.add_argument("--root", type=Path, default=ROOT)
    p.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    p.add_argument("--self-test", action="store_true")
    args = p.parse_args()
    if args.self_test:
        self_test()
        return 0
    if args.compile_commands is None:
        p.error("provide an existing compile_commands.json or --self-test")
    try:
        with args.manifest.open(encoding="utf-8") as handle:
            manifest = json.load(handle)
        with args.compile_commands.open(encoding="utf-8") as handle:
            db = json.load(handle)
        out = inspect(manifest, db, args.root)
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "incomplete-inputs", "reason": str(exc)}))
        return 2
    print(json.dumps(out, indent=2, sort_keys=True))
    # Fail explicitly on a checkout incompatible with the pinned manifest,
    # without treating known unresolved source drift as an execution failure.
    return 0 if out["all_vendor_snapshot_blobs_match_manifest"] else 2


if __name__ == "__main__":
    sys.exit(main())
