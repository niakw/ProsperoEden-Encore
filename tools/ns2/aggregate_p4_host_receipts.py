#!/usr/bin/env python3
"""Verify all four P4 host receipts on the same exact main/vendor pair.

This is a host-only qualification artifact, NOT a claim that the
P0-P4 functional backlog is complete or that PS5 runtime was exercised.
"""
from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import runpy
import tempfile

ROOT = Path(__file__).resolve().parents[2]
QUALIFIER = runpy.run_path(str(ROOT / "tools/ns2/qualify_host_batch.py"))
TESTS = QUALIFIER["TESTS"]
checked_revisions = QUALIFIER["checked_revisions"]
SHA = re.compile(r"[0-9a-f]{40}\Z")
SHARDS = 4


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def verify(receipts_dir: Path, main_sha: str, vendor_sha: str) -> dict:
    require(bool(SHA.fullmatch(main_sha)) and bool(SHA.fullmatch(vendor_sha)),
            "invalid main/vendor SHA")
    files = sorted(receipts_dir.rglob("p4-host-batch-*.json"))
    require(len(files) == SHARDS,
            f"expected exactly {SHARDS} host receipts; found {len(files)}")
    names = tuple(TESTS)
    seen: set[str] = set()
    shards: dict[int, dict] = {}
    for path in files:
        receipt = json.loads(path.read_text())
        index = receipt.get("shard_index")
        require(type(index) is int and 0 <= index < SHARDS,
                f"invalid host shard index: {path.name}")
        require(index not in shards, f"duplicate host shard {index}")
        require(receipt.get("main_sha") == main_sha and
                receipt.get("vendor_sha") == vendor_sha,
                f"mixed main/vendor SHA in shard {index}")
        require(receipt.get("scope") == "core" and
                receipt.get("shard_count") == SHARDS and
                receipt.get("host_only") is True and
                receipt.get("ps5_build") is False and
                receipt.get("console_frame") is False,
                f"shard {index} is not a core host-only receipt")
        require(isinstance(receipt.get("utc"), str),
                f"missing UTC start for shard {index}")
        datetime.fromisoformat(receipt["utc"])
        expected = tuple(name for k, name in enumerate(names) if k % SHARDS == index)
        results = receipt.get("results")
        require(isinstance(results, list), f"missing results on shard {index}")
        actual = tuple(result.get("name") for result in results
                       if isinstance(result, dict))
        require(actual == expected, f"shard {index} source witness inventory drift")
        require(receipt.get("total") == len(expected) and
                receipt.get("passed") == len(expected),
                f"shard {index} did not pass all {len(expected)} witnesses")
        for result in results:
            name = result["name"]
            require(name not in seen, f"duplicate host witness: {name}")
            require(result.get("script") == TESTS[name] and
                    result.get("passed") is True and
                    result.get("returncode") == 0,
                    f"host witness did not pass: {name}")
            seen.add(name)
        shards[index] = {
            "shard": index,
            "tests": len(results),
            "receipt_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }
    require(set(shards) == set(range(SHARDS)), "one or more host shards missing")
    require(seen == set(TESTS), f"missing tests: {sorted(set(TESTS) - seen)}")
    return {
        "schema": 1,
        "main_sha": main_sha,
        "vendor_sha": vendor_sha,
        "scope": "core",
        "host_only": True,
        "ps5_build": False,
        "console_frame": False,
        "functional_backlog_closed": False,
        "shards_passed": SHARDS,
        "tests_passed": len(seen),
        "tests_expected": len(TESTS),
        "witnesses": list(names),
        "shards": [shards[i] for i in range(SHARDS)],
    }


def self_test() -> None:
    main_sha, vendor_sha = "a" * 40, "b" * 40
    with tempfile.TemporaryDirectory(prefix="eden-p4-verify-") as temp:
        folder = Path(temp)
        sources = tuple(TESTS)
        for index in range(SHARDS):
            selected = [name for i, name in enumerate(sources) if i % SHARDS == index]
            receipt = {
                "main_sha": main_sha, "vendor_sha": vendor_sha,
                "utc": "2026-11-06T00:00:00+00:00", "scope": "core",
                "shard_index": index, "shard_count": SHARDS,
                "host_only": True, "ps5_build": False, "console_frame": False,
                "passed": len(selected), "total": len(selected),
                "results": [{"name": name, "script": TESTS[name], "passed": True,
                             "returncode": 0} for name in selected],
            }
            (folder / f"p4-host-batch-{index}.json").write_text(json.dumps(receipt))
        valid = verify(folder, main_sha, vendor_sha)
        require(valid["tests_passed"] == len(TESTS), "valid matrix failed")
        first = folder / "p4-host-batch-0.json"
        initial = first.read_text()
        broken = json.loads(initial)
        broken["vendor_sha"] = "c" * 40
        first.write_text(json.dumps(broken))
        try:
            verify(folder, main_sha, vendor_sha)
        except ValueError:
            pass
        else:
            raise AssertionError("mixed vendor SHA was accepted")
        first.write_text(initial)
        broken = json.loads(initial)
        broken["results"].pop()
        first.write_text(json.dumps(broken))
        try:
            verify(folder, main_sha, vendor_sha)
        except ValueError:
            pass
        else:
            raise AssertionError("missing host witness was accepted")
        first.write_text(initial)
        (folder / "p4-host-batch-3.json").unlink()
        try:
            verify(folder, main_sha, vendor_sha)
        except ValueError:
            pass
        else:
            raise AssertionError("missing host shard was accepted")
        print(f"P4_HOST_RECEIPT_SELF_TEST_PASS tests={len(TESTS)} negative=3")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--receipts-dir", type=Path,
                        default=ROOT / ".build-local/host-receipts")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    main_sha, vendor_sha = checked_revisions()
    summary = verify(args.receipts_dir, main_sha, vendor_sha)
    path = ROOT / ".build-local" / f"p4-host-verified-{main_sha[:8]}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n")
    print(f"P4_HOST_MATRIX_VERIFIED main={main_sha} vendor={vendor_sha} "
          f"tests={summary['tests_passed']}/{summary['tests_expected']} "
          f"shards={summary['shards_passed']}/{SHARDS} "
          f"receipt={path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
