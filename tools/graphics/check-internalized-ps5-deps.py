#!/usr/bin/env python3
"""Offline dependency/source-boundary closure without revision allowlists."""
from pathlib import Path
import hashlib
import subprocess

ROOT = Path(__file__).resolve().parents[2]
VENDOR = ROOT / "vendor"

def git(c, *args):
    return subprocess.check_output(["git", "-C", str(c), *args], text=True).strip()

modules = [
    s.split()[-1] for s in git(ROOT, "ls-tree", "-r", "HEAD").splitlines()
    if s.startswith("160000 commit ")
]
assert modules == ["encore-overrides", "vendor"], modules
assert git(ROOT, "rev-parse", "HEAD:vendor") == git(VENDOR, "rev-parse", "HEAD")
subprocess.check_call(["python3", "-B", "tools/check-source-tree-layout.py"], cwd=VENDOR)

# These are dependency snapshots, not override owners. Their exact upstream
# revision belongs in provenance metadata; current source admission must never
# depend on a rolling tree-SHA allowlist.
provenance = (VENDOR / "docs/PS5_INTERNAL_DEPENDENCY_ORIGINS_2026-11-10.md").read_text()
for name in ("ps5-mihawkgen", "ps5-fsr3-optical-flow", "libwebp"):
    path = VENDOR / "sources" / name
    assert path.is_dir() and not (path / ".git").exists(), name
    assert name in provenance, ("missing dependency provenance", name)

# Example of the mandatory source/override split: the imported training
# requirements stay upstream-clean; the reviewed Encore dependency bump lives
# at the identical relative path under encore-active/.
upstream_req = VENDOR / "sources/ps5-mihawkgen/train/requirements.txt"
active_req = VENDOR / "encore-active/ps5-mihawkgen/train/requirements.txt"
assert upstream_req.read_text().count("pillow==12.3.0") == 1
assert "pillow==13.0.0" not in upstream_req.read_text()
assert active_req.read_text().count("pillow==13.0.0") == 1

# Binary model integrity is artifact provenance, not C++ source selection.
model = VENDOR / "sources/ps5-mihawkgen/framegen/models/network.fgw"
assert model.stat().st_size == 1757240
assert hashlib.sha256(model.read_bytes()).hexdigest() == (
    "31ecc7d69af1e9defd62b9abad71bc3430cd8a0a4d2f4eafcabaafa48c34bf6b"
)
for p in (
    "ps5-mihawkgen/LICENSE.md",
    "ps5-mihawkgen/THIRD_PARTY_NOTICES.txt",
    "ps5-fsr3-optical-flow/COPYING",
    "ps5-fsr3-optical-flow/shaders/LICENSE.txt",
    "libwebp/COPYING",
    "libwebp/PATENTS",
):
    assert (VENDOR / "sources" / p).is_file(), p
assert "version 1.6.0" in (VENDOR / "sources/libwebp/NEWS").read_text()

print(
    "PS5_INTERNAL_DEPENDENCIES_PASS",
    "gitlink_match=1",
    "sources=frozen",
    "active_override_precedence=1",
    "revision_allowlists=0",
    "model_integrity=1",
)
