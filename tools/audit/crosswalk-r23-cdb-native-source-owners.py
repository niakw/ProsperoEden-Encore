#!/usr/bin/env python3
"""R23: crosswalk all 155 upstream changed C/C++ units to an EXISTING native CDB.

A compile_commands entry proves an input was *scheduled* on the historic
configured build; it does not prove object success, linkage, headers, or a
current main/PS5 executable. Unmatched filenames are NOT proof of absence:
Encore may rename/copy them under headless/native-local or an override owner.
"""
from __future__ import annotations
import argparse
from collections import Counter
import json
from pathlib import Path
import tempfile

ROOT = Path(__file__).resolve().parents[2]
REGISTER = ROOT / "docs/audits/r23/R23_EDEN_COMPLETE_155_COMMIT_PATH_REGISTER.json"
TU_SUFFIXES = (".cpp", ".c", ".cc", ".cxx", ".mm")
HEADER_SUFFIXES = (".h", ".hpp", ".hh", ".inc", ".inl")


def source_path(row: dict) -> str:
    path = Path(row["file"])
    if not path.is_absolute():
        path = Path(row["directory"]) / path
    return str(path.resolve(strict=False)).replace("\\", "/")


def owner_class(path: str) -> str:
    if "/vendor/encore-active/" in path:
        return "maintained_vendor_source"
    if "/native-local/" in path or "/headless/" in path:
        return "native_generated_or_headless"
    if "/source/src/" in path or "/vendor/sources/eden/src/" in path:
        return "pinned_original_source"
    return "other_scheduled_source"


def classify(reg: dict, db: list[dict]) -> dict:
    if not isinstance(db, list) or not isinstance(reg.get("rows"), list):
        raise ValueError("expected CMake CDB and upstream path register")
    scheduled = sorted(set(source_path(row) for row in db))
    output = []
    all_cases = Counter()
    for item in reg["rows"]:
        matched = []
        unlocated = []
        headers = []
        for record in item["files"]:
            path = record["path"]
            if path.endswith(HEADER_SUFFIXES):
                headers.append(path)
            if not path.endswith(TU_SUFFIXES):
                continue
            if not path.startswith("src/"):
                # Usually platform-specific or an auxiliary dependency:
                # never claim the PS5 emulation-core owner from its path.
                unlocated.append({"path": path, "reason": "not_an_engine_src_path"})
                all_cases["tu_not_engine_source_path"] += 1
                continue
            # Match suffixes only on complete src/ path boundaries. This
            # includes direct pinned Eden CDB paths and maintained full-TU
            # sources retaining the original relative src/ hierarchy.
            matches = [x for x in scheduled if x.endswith("/" + path)]
            if matches:
                owners = [{"compiled_input": x, "ownership": owner_class(x)} for x in matches]
                matched.append({"upstream_path": path, "scheduled_sources": owners})
                all_cases["changed_tu_with_historical_schedule"] += 1
            else:
                unlocated.append({"path": path, "reason": "no_exact_suffix_in_historical_CDB"})
                all_cases["changed_tu_requires_owner_mapping"] += 1
        output.append({
            "index": item["index"],
            "sha": item["sha"],
            "title": item["title"],
            "ns1_shared_path_candidate": item["ns1_or_shared_candidate"],
            "scheduled_changed_tus": matched,
            "unmapped_changed_tus": unlocated,
            "changed_headers_in_commit": len(headers),
            "header_direct_inclusion_proven": False,
        })
        if matched:
            all_cases["commits_with_direct_scheduled_TU_witness"] += 1
        if unlocated:
            all_cases["commits_with_unmapped_changed_TUs"] += 1
        if headers:
            all_cases["commits_with_header_changes_without_depfile_proof"] += 1
    return {
        "scope": "historical configured CMake compile database only, not current main or a binary",
        "source_commit_baseline": reg.get("baseline"),
        "source_commit_head": reg.get("head"),
        "commits_inspected": len(output),
        "historical_scheduled_file_count": len(scheduled),
        "build_or_link_proven": False,
        "header_inclusion_proven": False,
        "counts": dict(sorted(all_cases.items())),
        "commits": output,
    }


def self_test() -> None:
    with tempfile.TemporaryDirectory() as temp:
        folder = Path(temp)
        db = [
            {"directory": str(folder),
             "file": str(folder / "cache/source/src/core/managed.cpp")},
            {"directory": str(folder),
             "file": str(folder / "vendor/encore-active/eden-core/src/video_core/gpu.cpp")},
        ]
        reg = {"baseline": "test", "head": "test", "rows": [
            {"index": 1, "sha": "a", "title": "scheduled", "ns1_or_shared_candidate": True,
             "files": [{"path": "src/core/managed.cpp"},
                       {"path": "src/video_core/gpu.cpp"},
                       {"path": "src/common/only_header.h"}]},
            {"index": 2, "sha": "b", "title": "unmapped", "ns1_or_shared_candidate": True,
             "files": [{"path": "src/core/renamed.cpp"}]},
        ]}
        r = classify(reg, db)
        assert r["counts"]["changed_tu_with_historical_schedule"] == 2
        assert r["counts"]["changed_tu_requires_owner_mapping"] == 1
        assert r["commits"][0]["scheduled_changed_tus"][0]["scheduled_sources"][0]["ownership"] == "pinned_original_source"
        assert r["commits"][0]["scheduled_changed_tus"][1]["scheduled_sources"][0]["ownership"] == "maintained_vendor_source"
        assert r["commits"][0]["changed_headers_in_commit"] == 1
        assert r["commits"][1]["unmapped_changed_tus"][0]["reason"] == "no_exact_suffix_in_historical_CDB"
    print("R23_HISTORICAL_NATIVE_TU_OWNER_CROSSWALK_SELFTEST_OK")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("compile_commands", nargs="?", type=Path)
    parser.add_argument("--register", type=Path, default=REGISTER)
    parser.add_argument("--self-test", action="store_true")
    a = parser.parse_args()
    if a.self_test:
        self_test()
        return
    if a.compile_commands is None:
        parser.error("an EXISTING compile_commands.json is mandatory")
    reg = json.loads(a.register.read_text(encoding="utf-8"))
    if len(reg["rows"]) != 155 or reg.get("complete_commit_file_lists") != 155:
        raise ValueError("R23 complete 155-entry register not attested")
    db = json.loads(a.compile_commands.read_text(encoding="utf-8"))
    result = classify(reg, db)
    if result["commits_inspected"] != 155:
        raise AssertionError("missing R23 changed-file commit")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
