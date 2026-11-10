#!/usr/bin/env python3
"""Attest actual bytes of all 6 pinned archive blobs and 8 compiler-rt files.

Offline/read-only. Confirms repository-custodied bytes match checksums declared
by tools/deps.json, NOT the identity/authenticity of inaccessible upstreams,
native binary linkage, SDK ABI or licensing completeness.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import tempfile

ROOT = Path(__file__).resolve().parents[2]
CHUNK_NAME = re.compile(r"^\d{4}\.chunk$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
HEX128 = re.compile(r"^[0-9a-f]{128}$")
ARCHIVES = {"eden", "ffmpeg", "fmt", "pacbrew", "harfbuzz", "opengl-mesa-26-2"}
COMPILER_RT = {
    "emutls.c", "int_endianness.h", "int_lib.h", "int_types.h",
    "int_util.h", "cxa_thread_atexit.reference.cpp",
    "cpu_model_x86.c", "cpu_model.h",
}


def stream_file(path: Path, hashes: tuple) -> int:
    length = 0
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            length += len(block)
            for h in hashes:
                h.update(block)
    return length


def check(root: Path) -> dict:
    deps = json.loads((root / "tools/deps.json").read_text(encoding="utf-8"))
    items = deps["items"]
    archives = {item["name"]: item for item in items if item["kind"] == "archive"}
    if set(archives) != ARCHIVES or len(archives) != len(ARCHIVES):
        raise ValueError("expected six individually pinned archive entries")
    archive_out = {}
    for name, item in sorted(archives.items()):
        folder = root / "vendor/objects" / name
        manifest = json.loads((folder / "chunks.json").read_text())
        chunks = manifest["chunks"]
        if manifest.get("name") != name or not chunks:
            raise ValueError(f"{name}: invalid chunks manifest")
        if len({c["file"] for c in chunks}) != len(chunks):
            raise ValueError(f"{name}: duplicate chunk names")
        cumulative_256 = hashlib.sha256()
        cumulative_512 = hashlib.sha512()
        total = 0
        for idx, chunk in enumerate(chunks):
            filename = chunk["file"]
            if not CHUNK_NAME.fullmatch(filename) or filename != f"{idx:04d}.chunk":
                raise ValueError(f"{name}: unsafe/noncontiguous chunks")
            if not HEX64.fullmatch(chunk["sha256"]):
                raise ValueError(f"{name}: malformed chunk digest")
            path = folder / filename
            if not path.is_file() or path.is_symlink():
                raise ValueError(f"{name}: missing/linked chunk")
            h256 = hashlib.sha256()
            h512 = hashlib.sha512()
            size = 0
            with path.open("rb") as data:
                for block in iter(lambda: data.read(1 << 20), b""):
                    size += len(block)
                    h256.update(block)
                    h512.update(block)
                    cumulative_256.update(block)
                    cumulative_512.update(block)
            if size != chunk["size"] or h256.hexdigest() != chunk["sha256"]:
                raise ValueError(f"{name}: chunk actual bytes digest mismatch")
            total += size
        actual_sha256 = cumulative_256.hexdigest()
        actual_sha512 = cumulative_512.hexdigest()
        if total != manifest["size"] or actual_sha256 != manifest["sha256"]:
            raise ValueError(f"{name}: whole archived bytes differ from chunk manifest")
        digest_type = "sha512" if "sha512" in item else "sha256"
        pinned = item[digest_type]
        actual = actual_sha512 if digest_type == "sha512" else actual_sha256
        if not (HEX128 if digest_type == "sha512" else HEX64).fullmatch(pinned):
            raise ValueError(f"{name}: invalid tools/deps.json pinned digest")
        if actual != pinned:
            raise ValueError(f"{name}: actual bytes differ from tools/deps.json {digest_type}")
        archive_out[name] = {
            "sha256_actual": actual_sha256, "sha512_actual_if_pinned": actual_sha512
            if digest_type == "sha512" else None,
            "pinned_digest_algorithm": digest_type,
            "matches_tools_deps": True, "bytes": total, "chunk_count": len(chunks)
        }
    rt = next((item for item in items if item["name"] == "compiler-rt"), None)
    if rt is None or rt.get("kind") != "files":
        raise ValueError("compiler-rt pinned file set missing")
    if {entry["name"] for entry in rt["files"]} != COMPILER_RT or len(rt["files"]) != 8:
        raise ValueError("compiler-rt eight pinned input files changed")
    rt_out = {}
    for item in rt["files"]:
        filename = item["name"]
        path = root / "vendor/sources/compiler-rt" / filename
        if not path.is_file() or path.is_symlink():
            raise ValueError(f"compiler-rt {filename}: missing/non-regular")
        sha = hashlib.sha256()
        bytes_count = stream_file(path, (sha,))
        if sha.hexdigest() != item["sha256"]:
            raise ValueError(f"compiler-rt {filename}: digest mismatch")
        rt_out[filename] = {"sha256": sha.hexdigest(), "bytes": bytes_count}
    return {
        "scope": "custodied vendor archive / compiler-rt bytes vs declared tools/deps.json",
        "external_upstream_independently_authenticated": False,
        "linked_into_native_binary": False, "modified_files": 0,
        "archive_count": len(archive_out),
        "compiler_rt_file_count": len(rt_out),
        "archive_bytes_verified": sum(x["bytes"] for x in archive_out.values()),
        "archives": archive_out, "compiler_rt": rt_out,
    }


def self_test() -> None:
    with tempfile.TemporaryDirectory() as folder:
        root = Path(folder)
        (root / "tools").mkdir()
        (root / "vendor/sources/compiler-rt").mkdir(parents=True)
        archives, rt = [], []
        for name in sorted(ARCHIVES):
            path = root / "vendor/objects" / name
            path.mkdir(parents=True)
            data = ("pinned archive " + name).encode()
            (path / "0000.chunk").write_bytes(data)
            digest = hashlib.sha256(data).hexdigest()
            (path / "chunks.json").write_text(json.dumps({
                "name": name, "size": len(data), "sha256": digest,
                "chunks": [{"file": "0000.chunk", "size": len(data), "sha256": digest}],
            }))
            algo = "sha512" if name == "ffmpeg" else "sha256"
            archives.append({"kind": "archive", "name": name,
                             algo: getattr(hashlib, algo)(data).hexdigest()})
        for name in sorted(COMPILER_RT):
            data = ("LLVM source " + name).encode()
            (root / "vendor/sources/compiler-rt" / name).write_bytes(data)
            rt.append({"name": name, "sha256": hashlib.sha256(data).hexdigest()})
        (root / "tools/deps.json").write_text(json.dumps({
            "items": archives + [{"kind": "files", "name": "compiler-rt", "files": rt}]
        }))
        outcome = check(root)
        assert outcome["archive_count"] == 6 and outcome["compiler_rt_file_count"] == 8
        (root / "vendor/objects/eden/0000.chunk").write_bytes(b"corrupt")
        try:
            check(root)
        except ValueError:
            pass
        else:
            raise AssertionError("archive tampering not detected")
    print("R18_ARCHIVE_COMPILERRT_BYTES_SELFTEST_OK")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=ROOT)
    ap.add_argument("--self-test", action="store_true")
    opts = ap.parse_args()
    if opts.self_test:
        self_test()
    else:
        print(json.dumps(check(opts.root), indent=2, sort_keys=True))
