#!/usr/bin/env python3
"""Hash archived Git-pin chunks for the three currently unreachable upstream repos.

This proves vendor archive SHA256 self-integrity only; NEVER claim the exact
official upstream commit/tree is independently proved by this check.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import tempfile

ROOT = Path(__file__).resolve().parents[2]
FAMILIES = ("boilerplate", "opengl-native-boilerplate", "opengl-source")
HASH = re.compile(r"^[a-f0-9]{64}$")
FILE = re.compile(r"^\d{4}\.chunk$")

def attest(root: Path, families=FAMILIES) -> dict:
    results = {}
    for family in families:
        if family not in FAMILIES:
            raise ValueError("unknown dependency origin family")
        folder = root / "vendor/objects" / family
        manifest = json.loads((folder / "chunks.json").read_text(encoding="utf-8"))
        if manifest.get("name") != family:
            raise ValueError("manifest family name mismatch")
        chunks = manifest.get("chunks")
        if not isinstance(chunks, list) or not chunks:
            raise ValueError("missing or empty archive chunks")
        whole = hashlib.sha256()
        total = 0
        first = b""
        parts = []
        for item in chunks:
            name = item.get("file")
            digest = item.get("sha256")
            if not isinstance(name, str) or not FILE.fullmatch(name):
                raise ValueError("unsafe chunk name")
            if not isinstance(digest, str) or not HASH.fullmatch(digest):
                raise ValueError("invalid expected SHA256")
            p = folder / name
            if not p.is_file() or p.stat().st_size != item.get("size"):
                raise ValueError("chunk not found or wrong size: " + name)
            actual = hashlib.sha256()
            size = 0
            with p.open("rb") as stream:
                for block in iter(lambda: stream.read(1 << 20), b""):
                    if not first:
                        first = block[:16]
                    actual.update(block)
                    whole.update(block)
                    size += len(block)
            if actual.hexdigest() != digest:
                raise ValueError("chunk digest mismatch: " + name)
            total += size
            parts.append({"name": name, "bytes": size, "sha256": digest})
        if manifest.get("size") != total or manifest.get("sha256") != whole.hexdigest():
            raise ValueError("aggregate archive digest mismatch")
        results[family] = {
            "status": "archived-chunks-sha256-verified",
            "archive_sha256": whole.hexdigest(),
            "archive_bytes": total,
            "chunk_count": len(chunks),
            "prefix_hex": first.hex(),
            "chunk_receipts": parts,
            "official_upstream_git_commit_verified": False,
        }
    return {"scope": "self-custodied vendor archive bytes only",
            "upstream_origin_verified": False, "families": results}

def self_test() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        for name in FAMILIES:
            folder = root / "vendor/objects" / name
            folder.mkdir(parents=True)
            data = ("archive " + name).encode()
            digest = hashlib.sha256(data).hexdigest()
            (folder / "0000.chunk").write_bytes(data)
            (folder / "chunks.json").write_text(json.dumps({
                "name": name, "size": len(data), "sha256": digest,
                "chunks": [{"file": "0000.chunk", "size": len(data), "sha256": digest}]}))
        assert len(attest(root)["families"]) == 3
        (root / "vendor/objects/boilerplate/0000.chunk").write_bytes(b"broken")
        try:
            attest(root)
        except ValueError:
            pass
        else:
            raise AssertionError("tampered chunk was accepted")
    print("R18_ORPHAN_PIN_ARCHIVE_INTEGRITY_SELFTEST_OK")

def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, default=ROOT)
    p.add_argument("--self-test", action="store_true")
    args = p.parse_args()
    if args.self_test:
        self_test()
    else:
        print(json.dumps(attest(args.root), indent=2, sort_keys=True))

if __name__ == "__main__":
    main()
