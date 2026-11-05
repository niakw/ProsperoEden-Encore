#!/usr/bin/env python3
"""Resolve release R-label from the exact native artifact, never workflow HEAD.

Legacy exception: the single immutable public R1 artifact (run #38752177232,
SHA 56293953..) predates the attestation file. All later artifacts MUST
include an attestation written when their eboot.bin was packaged.
"""
import argparse
import json
import re
import sys
from pathlib import Path

LEGACY_SHA = "5629395324ff65c98b50c44f35f2142a4a92654a"
TITLE = "PPSA99008"
CONTENT_ID = "UP9000-PPSA99008_00-PROSPEROEDEN0001"


def resolve(app: Path, expected_sha: str):
    if not re.fullmatch(r"[0-9a-f]{40}", expected_sha):
        raise ValueError("expected an exact 40-character source SHA")
    native = json.loads((app / "sce_sys/param.json").read_text(encoding="utf-8"))
    if native.get("titleId") != TITLE or native.get("contentId") != CONTENT_ID:
        raise ValueError("native title identity mismatch")
    content_version = native.get("contentVersion")
    if not isinstance(content_version, str) or not re.fullmatch(r"[0-9]{2}\.[0-9]{3}\.[0-9]{3}", content_version):
        raise ValueError("invalid PS5 native contentVersion")
    manifest_path = app / "encore-release.json"
    if manifest_path.is_file():
        if manifest_path.stat().st_size > 4096:
            raise ValueError("oversized release attestation")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("source_sha") != expected_sha:
            raise ValueError("artifact source SHA does not match approved green CI")
        if manifest.get("native_content_version") != content_version:
            raise ValueError("artifact native contentVersion mismatch")
        label = manifest.get("build_revision")
        if not isinstance(label, str) or not re.fullmatch(r"R[1-9][0-9]{0,5}", label):
            raise ValueError("missing or invalid compiled R revision")
    elif expected_sha == LEGACY_SHA and content_version == "01.000.041":
        # The only public pre-attestation release. Never infer R1 for any
        # other source SHA or for a rewritten native content version.
        label = "R1"
    else:
        raise ValueError("release attestation missing: cannot infer R revision safely")
    short = expected_sha[:8]
    return {
        "label": label,
        "tag": f"encore-{label}-{short}",
        "zip": f"Eden-Encore-{label}-{short}-FTP-{TITLE}.zip",
        "native_content_version": content_version,
        "legacy": not manifest_path.is_file(),
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("app", type=Path)
    p.add_argument("--source-sha", required=True)
    p.add_argument("--github-outputs", action="store_true")
    args = p.parse_args()
    try:
        value = resolve(args.app, args.source_sha)
    except (OSError, ValueError, TypeError, KeyError) as exc:
        raise SystemExit(f"Release refused: {exc}") from exc
    if args.github_outputs:
        for field in ("label", "tag", "zip", "native_content_version"):
            print(f"{field}={value[field]}")
    else:
        print(json.dumps(value, sort_keys=True))


if __name__ == "__main__":
    main()
