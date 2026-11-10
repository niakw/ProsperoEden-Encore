#!/usr/bin/env python3
"""Read-only SHA provenance of 17 divergent headers from historical Ninja deps.

Ninja -t deps is a historical object-dependency ledger, NOT live preprocessor,
linkage or PS5 execution proof. This script does not compile anything.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import tempfile

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "docs/audits/R18_VENDOR_EDEN_35_SOURCE_MUTATIONS_2026-11-10.json"
OBJECT = re.compile(r"^(.+?): #deps (\d+), deps mtime .+ \((VALID|STALE)\)\s*$")

def blob_sha1(path: Path) -> str:
    h = hashlib.sha1(b"blob " + str(path.stat().st_size).encode() + b"\0")
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def inspect(manifest: dict, deps_text: str, build_dir: Path) -> dict:
    items = [x for x in manifest["rows"] if Path(x["path"]).suffix in (".h", ".hpp", ".inc")]
    if len(items) != 17:
        raise ValueError("expected exactly 17 original-source header differences")
    refs = {x["path"]: [] for x in items}
    active_obj, active_valid = None, False
    for line in deps_text.splitlines():
        if not line.startswith((" ", "\t")):
            match = OBJECT.match(line)
            active_obj = match.group(1) if match else None
            active_valid = bool(match and match.group(3) == "VALID")
            continue
        if active_obj is None:
            continue
        dep = line.strip()
        if not dep:
            continue
        for key in refs:
            if dep.endswith("/" + key[4:]) or dep == key[4:]:
                path = Path(dep)
                resolved = (path if path.is_absolute() else build_dir / path).resolve(strict=False)
                hit = {"path": str(resolved), "object": active_obj,
                       "ledger_valid": active_valid, "blob": None}
                if resolved.is_file():
                    hit["blob"] = blob_sha1(resolved)
                refs[key].append(hit)
    rows = {}
    for item in items:
        name = item["path"]
        all_hits = refs[name]
        valid = [h for h in all_hits if h["ledger_valid"] and h["blob"]]
        blobs = sorted({h["blob"] for h in valid})
        paths = sorted({h["path"] for h in valid})
        status = ("no-valid-historical-object-dep" if not blobs else
                  "multiple-different-blobs" if len(blobs) > 1 else
                  "one-blob-official-original" if blobs[0] == item["official_blob"] else
                  "one-blob-vendor-mutated" if blobs[0] == item["vendor_blob"] else
                  "one-blob-other-version")
        rows[name] = {
            "status": status,
            "ledger_references": len(all_hits),
            "valid_object_references": len(valid),
            "object_examples": sorted({h["object"] for h in valid})[:8],
            "header_paths": paths[:20], "selected_git_blobs": blobs,
            "official_git_blob": item["official_blob"],
            "vendor_mutated_git_blob": item["vendor_blob"],
        }
    return {
        "scope": "historical native Ninja -t deps: not current live -H or linked binary",
        "changed_header_count": len(items),
        "result_counts": dict(sorted(Counter(row["status"] for row in rows.values()).items())),
        "rows": rows,
    }

def self_test() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        build = Path(tmp)
        rows = []
        for i in range(17):
            rel = f"src/core/hle/kernel/header_{i}.h"
            file = build / f"include/{rel[4:]}"
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_text(f"header-{i}\n")
            rows.append({"path": rel, "official_blob": blob_sha1(file),
                         "vendor_blob": "0" * 40})
        m = {"rows": rows}
        p0 = build / "include/core/hle/kernel/header_0.h"
        p1 = build / "include/core/hle/kernel/header_1.h"
        deps = f"a.o: #deps 1, deps mtime 100 (VALID)\n    {p0}\n"
        deps += f"b.o: #deps 1, deps mtime 100 (STALE)\n    {p1}\n"
        a = inspect(m, deps, build)
        assert a["result_counts"] == {"no-valid-historical-object-dep": 16,
                                       "one-blob-official-original": 1}
        p0.write_text("different\n")
        assert inspect(m, deps, build)["rows"][rows[0]["path"]]["status"] == "one-blob-other-version"
        deps += f"c.o: #deps 1, deps mtime 110 (VALID)\n    {p0}\n"
        assert inspect(m, deps, build)["rows"][rows[0]["path"]]["valid_object_references"] == 2
    print("R18_NINJA_DEPS_HEADERS_SELFTEST_OK")

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("ninja_deps_text", nargs="?", type=Path)
    ap.add_argument("--build-dir", type=Path)
    ap.add_argument("--manifest", type=Path, default=MANIFEST)
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        self_test()
        return
    if a.ninja_deps_text is None or a.build_dir is None:
        ap.error("provide existing ninja -t deps text and --build-dir")
    manifest = json.loads(a.manifest.read_text())
    deps_text = a.ninja_deps_text.read_text(errors="replace") if a.ninja_deps_text.is_file() else ""
    result = inspect(manifest, deps_text, a.build_dir)
    result["ninja_deps_text_present"] = bool(deps_text)
    print(json.dumps(result, indent=2, sort_keys=True))

if __name__ == "__main__":
    main()
