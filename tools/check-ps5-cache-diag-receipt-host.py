#!/usr/bin/env python3
"""Validate exact reversible proof for the optional vendor PS5 cache probe.

Historical source SHA must stay frozen; an unrelated source edit must fail.
This host test never replaces production sources or launches the PS5.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / "tools"))
from ci.ps5_cache_diag_receipt import (
    OPEN, CLOSE, OWNER, ORIGINAL_BLOB, REVIEWED_DIAGNOSTIC_BLOB,
    REVIEWED_DRIVER_HEADER_BLOB, DRIVER_HEADER_REVERSES,
    git_blob, normalize_for_historical_proof,
)

owner_file = root / "vendor" / OWNER
source = owner_file.read_text()
original, was_diagnostic = normalize_for_historical_proof(source)
assert git_blob(original) == ORIGINAL_BLOB

if was_diagnostic:
    assert git_blob(source) in {REVIEWED_DIAGNOSTIC_BLOB, REVIEWED_DRIVER_HEADER_BLOB}
    assert source.count(OPEN) == source.count(CLOSE) == 7
    assert source != original
else:
    assert git_blob(source) == ORIGINAL_BLOB
    assert OPEN not in source and CLOSE not in source

def rejects(text: str) -> None:
    try:
        normalize_for_historical_proof(text)
    except AssertionError:
        return
    raise AssertionError("unreviewed vendor mutation was accepted")

rejects(source + "\n// unrelated native source drift\n")
rejects(source.replace("PipelineCache", "PipelineCacheX", 1))
rejects(source + "\n// ENCORE_PS5_CACHE_DIAG_BEGIN\n")
rejects(source + "\n// ENCORE_PS5_CACHE_DIAG_END\n")
if git_blob(source) == REVIEWED_DRIVER_HEADER_BLOB:
    assert len(DRIVER_HEADER_REVERSES) == 5
    for successor, predecessor in DRIVER_HEADER_REVERSES:
        assert source.count(successor) == 1
        rejects(source.replace(successor, predecessor, 1))
    assert "NativeDriverCacheHeaderMatches" in source
    assert "kNativeDriverCacheStagingLimit" in source

# Review the engine preflight integration itself: vendor must be normalized
# only after the raw owner has passed the pin, before comparison to the
# original generator/R23/P24 oracles.
checker = (root / "tools/check-vendored-vulkan-fork.py").read_text()
assert checker.count("normalize_for_historical_proof(cache_source)") == 1
assert checker.index("normalize_for_historical_proof(cache_source)") < checker.index(
    "n56_current = expected[n56_name].read_text()")
assert checker.index("normalize_for_historical_proof(cache_source)") < checker.index(
    "r23_combined_owners = {")
assert "expected[native_cache_owner] = cache_historic_file" in checker
assert "ENCORE_PS5_SHADER_CACHE_SOURCE_RECEIPT_PASS" in checker

print("PS5_SHADER_CACHE_VENDOR_RECEIPT_HOST_PASS "
      f"diagnostics={int(was_diagnostic)} frozen_blob=1 negative_tests=4 "
      "generator_proof=retained native_ps5=unverified")
