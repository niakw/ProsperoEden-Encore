#!/usr/bin/env python3
"""Attest all 22 pinned CPM source directory file/byte counts (not archive digests).

Every lock drift is reported as an explicit unresolved finding without hiding\nother components. Does not reconstruct upstream archives or equate source-tree byte counts with
the lock's declared sha256 / upstream_sha512; those checks remain open.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import tempfile

ROOT = Path(__file__).resolve().parents[2]


def checked(root: Path) -> dict:
    folder = root / "vendor/sources/eden-cpm"
    lock = json.loads((folder / "VENDOR-CPM-LOCK.json").read_text(encoding="utf-8"))
    expected = lock["entries"]
    if len(expected) != 22 or len(set(expected)) != 22:
        raise ValueError("CPM source lock must have exactly 22 distinct entries")
    present = {p.name for p in folder.iterdir() if p.is_dir()}
    if set(expected) != present:
        raise ValueError(f"CPM root drift: missing={sorted(set(expected)-present)}, unexpected={sorted(present-set(expected))}")
    paths = {}
    for name, record in sorted(expected.items()):
        base = folder / name
        if name in {".", ".."} or "/" in name or "\\" in name:
            raise ValueError("unsafe CPM lock name")
        total, count, links = 0, 0, 0
        for walk, dirs, files in os.walk(base, followlinks=False):
            dirs[:] = sorted(dirs)
            if ".git" in dirs:
                raise ValueError(f"{name}: transient Git directory not permitted")
            for fn in sorted(files):
                p = Path(walk) / fn
                if p.is_symlink():
                    links += 1
                if not p.is_file():
                    raise ValueError(f"{name}: unsupported non-regular file")
                total += p.stat().st_size
                count += 1
        count_match = count == record["files"]
        bytes_match = total == record["bytes"]
        paths[name] = {
            "files": count, "file_bytes": total, "symlinks_counted": links,
            "lock_files": record["files"], "lock_file_bytes": record["bytes"],
            "file_count_matches_lock": count_match,
            "byte_count_matches_lock": bytes_match,
            "byte_difference_vs_lock": total - record["bytes"],
            "declared_tar_sha256_verified": False,
            "declared_upstream_sha512_verified": False,
        }
    cpmfile = root / "vendor/sources/eden/cpmfile.json"
    if not cpmfile.is_file():
        raise ValueError("official pinned cpmfile.json missing")
    sha = hashlib.sha256(cpmfile.read_bytes()).hexdigest()
    if sha != lock["cpmfile_sha256"]:
        raise ValueError("CPM manifest cpmfile hash mismatch")
    return {
        "scope": "22 vendored CPM tree file/byte counts and original cpmfile hash",
        "source_tree_count": len(paths),
        "file_count": sum(x["files"] for x in paths.values()),
        "file_bytes": sum(x["file_bytes"] for x in paths.values()),
        "lock_tree_discrepancies": {
            name: {"actual_files": row["files"], "actual_bytes": row["file_bytes"],
                   "lock_files": row["lock_files"], "lock_bytes": row["lock_file_bytes"],
                   "byte_difference": row["byte_difference_vs_lock"],
                   "symlinks": row["symlinks_counted"]}
            for name, row in paths.items()
            if not row["file_count_matches_lock"] or not row["byte_count_matches_lock"]
        },
        "all_lock_tree_sizes_match": all(
            row["file_count_matches_lock"] and row["byte_count_matches_lock"]
            for row in paths.values()),
        "cpmfile_sha256": sha,
        "declared_archives_cryptographically_verified": False,
        "excluded_unfetched_pins": lock["excluded_unfetched_cpm_pins"],
        "components": paths,
    }


def self_test() -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        folder = root / "vendor/sources/eden-cpm"
        folder.mkdir(parents=True)
        (root / "vendor/sources/eden").mkdir(parents=True)
        (root / "vendor/sources/eden/cpmfile.json").write_text("test cpmfile")
        expected = {}
        for i in range(22):
            name = f"part{i:02d}"
            sub = folder / name
            sub.mkdir()
            content = f"source-{i}".encode()
            (sub / "source.cpp").write_bytes(content)
            expected[name] = {"files": 1, "bytes": len(content)}
        (folder / "VENDOR-CPM-LOCK.json").write_text(json.dumps({
            "entries": expected, "cpmfile_sha256":
                hashlib.sha256(b"test cpmfile").hexdigest(),
            "excluded_unfetched_cpm_pins": [],
        }))
        assert checked(root)["source_tree_count"] == 22
        # A same-size edit is intentionally NOT caught by size/count receipts.
        # This witness must never claim cryptographic archive identity.
        (folder / "part00/source.cpp").write_bytes(b"XXXXXXXX")
        assert checked(root)["source_tree_count"] == 22
        (folder / "part00/source.cpp").write_text("tampered-with-different-length")
        mismatched = checked(root)
        assert not mismatched["all_lock_tree_sizes_match"]
        assert mismatched["lock_tree_discrepancies"]["part00"]["byte_difference"] > 0
        assert mismatched["source_tree_count"] == 22
    print("R18_CPM_TREE_COUNTS_SELFTEST_OK")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
    else:
        print(json.dumps(checked(args.root), indent=2, sort_keys=True))
