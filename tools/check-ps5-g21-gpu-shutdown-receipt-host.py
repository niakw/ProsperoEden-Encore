#!/usr/bin/env python3
"""Host source receipt guard for five exact PS5 G21 shutdown owners.

Baseline and reviewed candidate must each have consistent 5-owner source
provenance. Mutations may not be admitted as historic source equivalence.
"""
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from ci.ps5_g21_gpu_shutdown_receipt import (
    OLD, REVIEWED, git_blob, normalize_g21_shutdown_source,
)

assert len(OLD) == len(REVIEWED) == 5
base = ROOT / "vendor/encore-active/eden-core/src/video_core"
candidates = []
for filename in sorted(OLD):
    source = (base / filename).read_text()
    historic, reviewed = normalize_g21_shutdown_source(filename, source)
    assert git_blob(historic) == OLD[filename]
    assert git_blob(source) == (REVIEWED[filename] if reviewed else OLD[filename])
    candidates.append(reviewed)
    for mutation in (
        source + "\n// unknown vendor source\n",
        source.replace("NotifyShutdown();", "NotifyShutdown(1);", 1)
          if reviewed else source.replace("~Impl()", "~Impl(int)", 1),
        source.replace("renderer.reset();", "renderer.release();", 1)
          if reviewed else source.replace("renderer;", "renderer_dummy;", 1),
    ):
        try:
            normalize_g21_shutdown_source(filename, mutation)
        except AssertionError:
            pass
        else:
            raise AssertionError(("Unreviewed G21 source drift accepted", filename))
assert all(candidates) or not any(candidates), (
    "Mixed historical and candidate GPU shutdown owners", candidates)
# Ensure the matrix consumes the strict receipt *before* N76/old G21 compare.
matrix = (ROOT / "tools/check-g21-gpu-profile-matrix-host.py").read_text()
assert matrix.count("normalize_g21_shutdown_source(") == 1
assert matrix.index("normalize_g21_shutdown_source(") < matrix.index(
    'if profile == "vulkan_native":')
assert 'assert maintained == expected, "G21 maintained source parity drift: " + profile' in matrix
assert 'assert results["vulkan_native"] == results["vulkan_native_dev"]' in matrix
print("G21_GPU_SHUTDOWN_SOURCE_RECEIPT_HOST_PASS five_owners=5 "
      f"candidate={int(all(candidates))} negative_mutations=15 "
      "G21_frozen_oracle=retained console_exit=unverified")
