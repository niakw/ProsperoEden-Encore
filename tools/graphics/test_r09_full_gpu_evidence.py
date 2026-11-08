#!/usr/bin/env python3
"""Negative-only regression: incomplete, fixture or fake GPU proofs MUST fail."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools/graphics/r09_verify_full_gpu_evidence.py"

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def run(folder, name, payload, expected_reason=None):
    e = folder / "evidence.json"
    e.write_text(json.dumps(payload), encoding="utf-8")
    p = subprocess.run(
        [sys.executable, str(TOOL), "--evidence", str(e),
         "--model", str(folder / "model.nrmodel"),
         "--plan", str(folder / "plan.txt"),
         "--output", str(folder / "output.rgba32f")],
        capture_output=True, text=True, check=False)
    assert p.returncode == 20, (name, p.stdout, p.stderr)
    assert "R09_FULL_GPU_152_AND_REFERENCE_IMAGE_PASS" not in p.stdout
    if expected_reason is not None:
        assert expected_reason in p.stderr, (name, p.stdout, p.stderr)
    print("R09_FULL_GPU_EVIDENCE_NEGATIVE_PASS", name)

def main():
    with tempfile.TemporaryDirectory(prefix="r09-gpu-proof-neg-") as tmp:
        root = Path(tmp)
        (root / "model.nrmodel").write_bytes(b"not an authentic model")
        rows = [f"{n} 0 1 1920 1080 placeholder" for n in range(152)]
        (root / "plan.txt").write_text("\n".join(rows) + "\n")
        (root / "output.rgba32f").write_bytes(b"\0" * 16)
        base = {
            "schema": "EDEN_R09_FULL_GPU_V1",
            "source": "NrRdna2FrameSession",
            "variant": "original",
            "backend": "vulkan",
            "format": "RGBA32F_LE",
            "readback": "vkCmdCopyImageToBuffer_after_completed_fence",
            "model_sha256": sha(root / "model.nrmodel"),
            "plan_sha256": sha(root / "plan.txt"),
            "output_sha256": sha(root / "output.rgba32f"),
            "gpu_device": "TEST-ONLY",
            "gpu_driver": "TEST-ONLY",
            "scheduler_record_succeeded": True,
            "queue_submitted": True,
            "fence_wait_succeeded": True,
            "input_is_real_capture": True,
            "source_image_sha256": "f" * 64,
            "width": 1920, "height": 1080,
            "operations": [
                {"ordinal": n, "native_plan_row": row,
                 "vk_dispatch_recorded": True, "queue_submission_completed": True,
                 "shader": "not-a-real-shader.spv"}
                for n, row in enumerate(rows)],
        }
        run(root, "empty-evidence", {})
        run(root, "fake-readback", base,
            "Original 599-tensor SHA-256 authenticity failed")
        fixture = dict(base, input_is_real_capture=False)
        run(root, "fixture-refused", fixture)
        truncated = dict(base, operations=base["operations"][:-1])
        run(root, "incomplete-151-ops", truncated)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
