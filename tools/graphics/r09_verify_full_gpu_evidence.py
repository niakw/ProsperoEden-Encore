#!/usr/bin/env python3
"""Fail-closed verifier for a REAL R09 Vulkan full-network evidence bundle.

This does not execute any inference or synthesize a model output.
No weights or input images are uploaded.
"""
from __future__ import annotations
import argparse
from array import array
import hashlib
import json
import math
from pathlib import Path
import re
import sys

from r09_verify_model_pack import ModelRejected, policy_for, verify_model

class Reject(Exception):
    pass

def require(condition, message):
    if not condition:
        raise Reject(message)

def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()

def rgba32f(path, width, height):
    length = width * height * 4
    require(sys.byteorder == "little", "little-endian host required")
    require(path.stat().st_size == length * 4,
            "RGBA32F buffer has wrong size")
    pixels = array("f")
    with path.open("rb") as stream:
        pixels.fromfile(stream, length)
    require(len(pixels) == length, "short RGBA32F readback")
    require(all(math.isfinite(v) for v in pixels),
            "non-finite pixel output")
    return pixels

def verify(args):
    obj = json.loads(args.evidence.read_text(encoding="utf-8"))
    require(type(obj) is dict, "missing JSON evidence object")
    for name, expected in (
        ("schema", "EDEN_R09_FULL_GPU_V1"),
        ("source", "NrRdna2FrameSession"),
        ("variant", "original"),
        ("backend", "vulkan"),
        ("format", "RGBA32F_LE"),
        ("readback", "vkCmdCopyImageToBuffer_after_completed_fence"),
    ):
        require(obj.get(name) == expected, "unexpected " + name)
    # Verify the actual original capture, not a self-reported input hash.
    # A claimed capture in JSON alone is not provenance evidence.
    require(args.input.is_file() and args.input.stat().st_size == 1920 * 1080 * 4,
            "missing or wrongly sized 1920x1080 RGBA8 capture")
    require(obj.get("source_image_sha256") == sha256(args.input),
            "capture SHA-256 differs from actual input bytes")
    for key, path in (
        ("model_sha256", args.model),
        ("plan_sha256", args.plan),
        ("output_sha256", args.output),
    ):
        require(obj.get(key) == sha256(path), "bad " + key)
    if args.reference is not None:
        require(args.reference.is_file(), "reference image missing")
        require(not args.reference.samefile(args.output),
                "self-reference cannot prove independent output")
        require(sha256(args.reference) != obj["output_sha256"],
                "bit-identical reference cannot establish independence")
    # An arbitrary model SHA embedded in the evidence is not authenticity.
    # Independently verify every actual learned tensor against the 599 public
    # Original digests BEFORE accepting any GPU trace or framebuffer claim.
    # No private weights are ever bundled into this verifier.
    try:
        verify_model(args.model, policy_for("original"))
    except ModelRejected as error:
        raise Reject("Original 599-tensor SHA-256 authenticity failed: "
                     + str(error)) from error
    require(obj.get("gpu_device") and obj.get("gpu_driver"),
            "missing Vulkan device/driver")
    require(obj.get("scheduler_record_succeeded") is True,
            "full graph not recorded")
    require(obj.get("queue_submitted") is True and
            obj.get("fence_wait_succeeded") is True,
            "GPU completion not demonstrated")
    require(obj.get("input_is_real_capture") is True,
            "test fixture is not a true guest image")
    require(obj.get("source_image_sha256") and
            obj["source_image_sha256"] != obj["output_sha256"],
            "source/output identity invalid")
    require(obj.get("width") == 1920 and obj.get("height") == 1080,
            "full Original output must be 1920x1080")
    plan = [row.strip() for row in args.plan.read_text(encoding="utf-8").splitlines()
            if row.strip() and not row.lstrip().startswith("#")]
    require(len(plan) == 152, "native Original plan must have 152 rows")
    require(all(re.match(r"^\d+\s+\d+\s+", row) for row in plan),
            "invalid plan syntax")
    operations = obj.get("operations")
    require(type(operations) is list and len(operations) == 152,
            "missing per-operation GPU trace (152 rows)")
    for i, (row, operation) in enumerate(zip(plan, operations)):
        require(type(operation) is dict and operation.get("ordinal") == i,
                f"operation ordinal {i} missing")
        require(operation.get("native_plan_row") == row,
                f"operation {i} does not match public plan")
        require(operation.get("vk_dispatch_recorded") is True and
                operation.get("queue_submission_completed") is True,
                f"operation {i} has no GPU completion proof")
        shader = operation.get("shader")
        require(isinstance(shader, str) and shader.endswith(".spv"),
                f"operation {i} has no SPIR-V identity")
    output = rgba32f(args.output, 1920, 1080)
    require(max(output) - min(output) > 0.001,
            "nearly constant output")
    print("R09_REAL_152_TRACE_AND_GPU_READBACK_PRESENT")
    require(args.reference is not None,
            "no independent reference; NOT a complete image validation")
    reference = rgba32f(args.reference, 1920, 1080)
    maximum = max(abs(a - b) for a, b in zip(output, reference))
    mse = sum((a-b)**2 for a, b in zip(output, reference)) / len(output)
    print(f"R09_IMAGE_REFERENCE max_abs={maximum:.8g} mse={mse:.8g}")
    require(maximum <= args.maximum_error,
            "image differs from independent oracle")
    print("R09_FULL_GPU_152_AND_REFERENCE_IMAGE_PASS")

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for field in ("evidence", "model", "plan", "input", "output"):
        parser.add_argument("--" + field, required=True, type=Path)
    parser.add_argument("--reference", type=Path)
    parser.add_argument("--maximum-error", type=float, default=1e-3)
    args = parser.parse_args()
    try:
        require(math.isfinite(args.maximum_error) and
                0 <= args.maximum_error <= 0.01,
                "unreasonable tolerance")
        verify(args)
        return 0
    except (Reject, OSError, KeyError, ValueError, OverflowError) as error:
        print("R09_FULL_GPU_PROOF_REJECTED:", error, file=sys.stderr)
        return 20

if __name__ == "__main__":
    raise SystemExit(main())
