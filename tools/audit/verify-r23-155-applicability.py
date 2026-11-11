#!/usr/bin/env python3
"""Fail-closed 155-commit R23 applicability register validator.

Checks exact immutable commit/changed-file receipts and all action categories.
Does NOT infer compiled PS5 source, semantic equivalence, ELF or runtime.
"""
from __future__ import annotations
import argparse
from collections import Counter
import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = "docs/audits/R23_EDEN_ALL_155_COMMITS_2026-11-10.json"
PATHS = "docs/audits/r23/R23_EDEN_COMPLETE_155_COMMIT_PATH_REGISTER.json"
APP = "docs/audits/r23/R23_EDEN_155_APPLICABILITY_2026-11-11.json"

def validate(root: Path, app: dict | None = None) -> dict:
    original = json.loads((root / SRC).read_text())
    receipt = json.loads((root / PATHS).read_text())
    if app is None:
        app = json.loads((root / APP).read_text())
    expected = {item["index"]: item for item in original["items"]}
    paths = {item["index"]: item for item in receipt["rows"]}
    rows = app["individual_commits"]
    if (original["commit_count"] != 155 or receipt["commits"] != 155 or
            app["exact_commit_count"] != 155 or not app["complete_file_lists"] or
            len(rows) != 155 or set(expected) != set(range(1, 156)) or
            set(paths) != set(expected)):
        raise ValueError("155-commit source inventory is incomplete")
    seen = set()
    categories = Counter()
    for item in rows:
        number = item["index"]
        if number in seen or number not in expected:
            raise ValueError(f"bad or duplicate commit index {number}")
        seen.add(number)
        original_item, path_item = expected[number], paths[number]
        if (item["sha"] != original_item["sha"] or
                item["title"] != original_item["title"] or
                item["sha"] != path_item["sha"] or
                item["file_count"] != path_item["file_count"] or
                item["paths"] != [p["path"] for p in path_item["files"]]):
            raise ValueError(f"R23 entry #{number}: upstream source proof drift")
        label = item["classification"]
        if not label or item.get("scope", "") == "" or item.get("action", "") == "":
            raise ValueError(f"R23 entry #{number}: missing explicit disposition")
        categories[label] += 1
    if set(seen) != set(expected):
        raise ValueError("one or more upstream commits are not categorized")
    if dict(categories) != app["classification_counts"] or sum(categories.values()) != 155:
        raise ValueError("inconsistent applicability class totals")
    # This dated pin is a frozen audit decision, not permission to silently
    # drop pending counts without exact source and owner proof.
    mandatory = {
        "runtime-semantic-review-pending": 105,
        "asset-and-translation-package-review": 8,
        "not-applicable-to-native-runtime-source": 25,
        "staged-host-source-fix": 5,
        "not-applicable-PS5-x64-execution": 4,
        "native-build-or-dependency-review": 4,
        "test-only-upstream": 1,
        "upstream-runtime-then-reverted-equivalent": 2,
        "reviewed-observability-only-no-NS1-behavioral-port": 1,
    }
    if dict(categories) != mandatory:
        raise ValueError("R23 dated classification changed without reviewed baseline bump")
    by_index = {item["index"]: item for item in rows}
    if (by_index[53]["classification"] != "reviewed-observability-only-no-NS1-behavioral-port"
            or by_index[5]["classification"] != "not-applicable-to-native-runtime-source"
            or any(by_index[i]["classification"] != "runtime-semantic-review-pending"
                   for i in (30, 93, 123, 141))):
        raise ValueError("semantically guarded source cases silently reclassified")
    if by_index[44]["classification"] != "staged-host-source-fix":
        raise ValueError("viewport is a proposed host fix, not tested native behavior")
    return {
        "immutable_commit_sha_file_receipts": 155,
        "classified_commits": 155,
        "class_counts": dict(sorted(categories.items())),
        "runtime_semantic_cases_pending": categories["runtime-semantic-review-pending"],
        "asset_and_dependency_cases_pending":
            categories["asset-and-translation-package-review"] +
            categories["native-build-or-dependency-review"],
        "five_staged_fixes_native_PS5_qualified": False,
        "header_include_provenance_qualified": False,
        "native_ELF_or_console_qualified": False,
    }

def self_test(root: Path) -> None:
    current = json.loads((root / APP).read_text())
    assert validate(root)["runtime_semantic_cases_pending"] == 105
    bad = copy.deepcopy(current)
    bad["individual_commits"][4]["classification"] = "runtime-semantic-review-pending"
    try:
        validate(root, bad)
    except ValueError:
        pass
    else:
        raise AssertionError("incorrect source classification was accepted")
    bad = copy.deepcopy(current)
    bad["individual_commits"][0]["paths"][0] = "forged/source.cpp"
    try:
        validate(root, bad)
    except ValueError:
        pass
    else:
        raise AssertionError("forged changed-file provenance was accepted")
    print("R23_155_APPLICABILITY_SELFTEST_OK")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test(args.root)
    else:
        print(json.dumps(validate(args.root), indent=2, sort_keys=True))
