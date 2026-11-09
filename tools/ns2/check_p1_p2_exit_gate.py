#!/usr/bin/env python3
"""Bounded P1/P2 release gate: 17 contracts, not a claim of full emulator parity.

Default mode audits the manifest and live owner/witness wiring. It deliberately
succeeds with open items so CI can produce an honest numerical progress report.
--enforce is the separate fail-closed P1/P2 exit decision; it requires every
in-scope item to have positive AND negative executed proof, no outstanding
blocker, and the required GitHub workflows green at one exact engine/vendor SHA.
Never builds PS5 or opens a console.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "docs" / "NS2_P1_P2_EXIT_CONTRACT.json"
EXPECTED = tuple(f"H{n:02}" for n in range(1, 8)) + tuple(
    f"G{n:02}" for n in range(1, 11))
ALLOWED = {"open", "host_verified", "scope_excluded"}
EXECUTED = {"real-owner-exec", "spirv-val", "real-owner-ipc"}
REPO = "niakw/ProsperoEden-Encore"


def local_sha(*parts: str) -> str:
    result = subprocess.run(["git", *parts], cwd=ROOT, text=True,
                            capture_output=True, timeout=20)
    if result.returncode:
        raise ValueError(f"git {' '.join(parts)}: {result.stderr.strip()}")
    return result.stdout.strip()


def active_witnesses() -> str:
    # A witness is not active just because its file exists: it must be invoked
    # by the maintained host batch or a live CI workflow.
    batch = (ROOT / "tools/ns2/qualify_host_batch.py").read_text()
    workflows = ROOT / ".github/workflows"
    return batch + "\n" + "\n".join(
        p.read_text() for p in workflows.glob("*.yml"))


def validate_manifest(data: dict) -> tuple[list[str], dict[str, int]]:
    errors: list[str] = []
    counts = {"open": 0, "host_verified": 0, "scope_excluded": 0}
    if data.get("schema") != 1:
        errors.append("unsupported contract schema")
    items = data.get("items")
    if not isinstance(items, list):
        return ["items must be an array"], counts
    ids = [x.get("id") for x in items if isinstance(x, dict)]
    if len(items) != 17 or sorted(ids) != sorted(EXPECTED):
        errors.append("P1/P2 contract must contain exactly H01-H07 and G01-G10")
    source = active_witnesses()
    for item in items:
        if not isinstance(item, dict):
            errors.append("non-object contract row")
            continue
        ident = item.get("id", "?")
        state = item.get("status")
        if state not in ALLOWED:
            errors.append(f"{ident}: invalid state {state!r}")
            continue
        counts[state] += 1
        owner = item.get("owner", "")
        if not isinstance(owner, str) or not owner.startswith("vendor/") or (
                not (ROOT / owner).is_file()):
            errors.append(f"{ident}: missing real vendor owner {owner!r}")
        for key in ("positive", "negative"):
            if not isinstance(item.get(key), str) or len(item[key].strip()) < 35:
                errors.append(f"{ident}: imprecise {key} acceptance criterion")
        checks = item.get("validators")
        if not isinstance(checks, list) or not checks:
            errors.append(f"{ident}: no validation scripts")
            checks = []
        active = 0
        for p in checks:
            if not isinstance(p, str) or not p.startswith("tools/") or not p.endswith(".py"):
                errors.append(f"{ident}: invalid test path {p!r}")
            elif not (ROOT / p).is_file():
                errors.append(f"{ident}: missing witness {p}")
            elif p in source:
                active += 1
        if not active:
            errors.append(f"{ident}: no witness in maintained CI or host batch")
        evidence = item.get("evidence")
        if not isinstance(evidence, dict):
            errors.append(f"{ident}: evidence must be a map")
            continue
        if state == "open":
            if not item.get("blocker"):
                errors.append(f"{ident}: open item has no stated blocker")
            if evidence:
                errors.append(f"{ident}: open item cannot claim completion evidence")
        elif state == "host_verified":
            if item.get("blocker"):
                errors.append(f"{ident}: verified row still has a blocker")
            for key in ("positive", "negative"):
                proof = evidence.get(key)
                if not isinstance(proof, dict) or (
                        proof.get("validator") not in checks or
                        proof.get("kind") not in EXECUTED or
                        not isinstance(proof.get("run_id"), int) or
                        proof["run_id"] <= 0):
                    errors.append(f"{ident}: {key} needs real executed witness + run ID")
        elif state == "scope_excluded":
            # An optional SDK form may be intentionally rejected only with an
            # ABI justification AND real rejection proof; never a silent pass.
            if len(str(evidence.get("abi_reason", ""))) < 60:
                errors.append(f"{ident}: exclusion needs explicit SDK/ABI rationale")
            rejection = evidence.get("negative")
            if not isinstance(rejection, dict) or (
                    rejection.get("validator") not in checks or
                    rejection.get("kind") not in EXECUTED or
                    not isinstance(rejection.get("run_id"), int)):
                errors.append(f"{ident}: exclusion needs executed native rejection")
    workflows = data.get("mandatory_workflows")
    required = {
        "Encore core fast gate",
        "Encore source preflight (host only)",
        "NS2 research host guards",
        "NS2 standalone graphics SPIR-V qualification (main only)",
        "Eden P0-P4 host qualification (sharded)",
        "Verify pinned vendor submodule",
    }
    if not isinstance(workflows, list) or set(workflows) != required:
        errors.append("mandatory same-SHA workflows must retain six exact checks")
    return errors, counts


def fetch_successful_run_ids(main_sha: str) -> tuple[set[str], set[int]]:
    headers = {"User-Agent": "eden-p1-p2-exit-contract",
               "Accept": "application/vnd.github+json"}
    if os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = "Bearer " + os.environ["GITHUB_TOKEN"]
    url = ("https://api.github.com/repos/" + REPO +
           "/actions/runs?head_sha=" + main_sha + "&per_page=100")
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=20) as response:
        runs = json.load(response).get("workflow_runs", [])
    # Only this SHA, not a green run from a previous engine/vendor pairing.
    ok = [r for r in runs if r.get("head_sha") == main_sha and
          r.get("status") == "completed" and r.get("conclusion") == "success"]
    return {r["name"] for r in ok}, {r["id"] for r in ok}


def enforce_exit(data: dict) -> list[str]:
    errors: list[str] = []
    if any(x["status"] == "open" for x in data["items"]):
        return ["open H/G contracts block release; no CI result overrides them"]
    main = local_sha("rev-parse", "HEAD")
    vendor = local_sha("-C", "vendor", "rev-parse", "HEAD")
    tree = local_sha("ls-tree", "HEAD", "vendor").split()
    if len(tree) < 3 or tree[0] != "160000" or tree[2] != vendor:
        return ["working vendor does not match immutable engine gitlink"]
    for root in (ROOT, ROOT / "vendor"):
        if subprocess.check_output(["git", "status", "--porcelain",
                                    "--untracked-files=no"], cwd=root,
                                   text=True, timeout=15).strip():
            return ["tracked sources are dirty; SHA attestation impossible"]
    try:
        workflow_names, success_ids = fetch_successful_run_ids(main)
    except (urllib.error.URLError, OSError, ValueError, TimeoutError) as exc:
        return [f"cannot verify live GitHub run status: {exc}"]
    missing = sorted(set(data["mandatory_workflows"]) - workflow_names)
    if missing:
        errors.append("mandatory CI not green at exact SHA " + main[:12] +
                      ": " + ", ".join(missing))
    for item in data["items"]:
        for key in (("positive", "negative") if item["status"] == "host_verified"
                    else ("negative",)):
            run_id = item["evidence"][key]["run_id"]
            if run_id not in success_ids:
                errors.append(f"{item['id']} {key}: run {run_id} not green at this SHA")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--enforce", action="store_true",
                        help="fail closed unless all 17 real contracts and same-SHA CI pass")
    parser.add_argument("--json", action="store_true", dest="machine",
                        help="print one machine-readable progress report")
    args = parser.parse_args()
    try:
        data = json.loads(MANIFEST.read_text())
        problems, counts = validate_manifest(data)
        if args.enforce and not problems:
            problems.extend(enforce_exit(data))
    except (OSError, ValueError, KeyError, TypeError) as exc:
        problems = [str(exc)]
        counts = {"open": 0, "host_verified": 0, "scope_excluded": 0}
    result = {"schema": 1, "goal": "P1_P2_HOST_EXIT",
              "total": 17,
              "verified": counts["host_verified"],
              "explicit_exclusions": counts["scope_excluded"],
              "open": counts["open"],
              "exit_ready": args.enforce and not problems,
              "structural_audit": not args.enforce,
              "errors": problems,
              "no_ps5_build": True}
    if args.machine:
        print(json.dumps(result, sort_keys=True))
    else:
        print("P1_P2_EXIT_" + ("ENFORCE" if args.enforce else "AUDIT"),
              f"verified={result['verified']}/17",
              f"excluded={result['explicit_exclusions']}/17",
              f"open={result['open']}/17",
              f"ready={result['exit_ready']}", flush=True)
        for error in problems:
            print("P1_P2_EXIT_BLOCKER:", error, flush=True)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
