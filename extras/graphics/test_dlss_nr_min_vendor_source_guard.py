#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Fail-closed source-drift guard for the *pinned* R09 native ViT pipeline.

This verifies source-level *necessary* preconditions for the isolated ViT
scratch-reuse proposal, NOT sufficient GPU safety or permission to enable
buffer aliasing in the real PS5 renderer.
"""
from __future__ import annotations

import argparse
import hashlib
import re
import subprocess
from pathlib import Path

ROOT = "encore-active/eden-vulkan/"
FILES = {
    "session": "nr_rdna2_frame_session.cpp",
    "run": "nr_rdna2_vit_run.cpp",
    "block": "nr_rdna2_vit_block.cpp",
    "projection": "nr_rdna2_vit_projection_stage.cpp",
    "epilogue": "nr_rdna2_vit_epilogue.cpp",
    "qkv": "nr_rdna2_vit_qkv_attention_link.cpp",
}
# Source preconditions are necessary, not a GPU lifetime proof.
class Drift(Exception):
    pass


def compact(source: str) -> str:
    source = re.sub(r"/\*.*?\*/", "", source, flags=re.S)
    source = re.sub(r"//[^\n]*", "", source)
    return re.sub(r"\s+", "", source)


def method(source: str, needle: str) -> str:
    pos = source.find(needle)
    if pos < 0:
        raise Drift(f"Missing method {needle}")
    start = source.find("{", pos + len(needle))
    if start < 0:
        raise Drift(f"Missing body {needle}")
    level = 0
    for i in range(start, len(source)):
        if source[i] == "{":
            level += 1
        elif source[i] == "}":
            level -= 1
            if level == 0:
                return source[start : i + 1]
    raise Drift(f"Unbalanced braces in {needle}")


def require(haystack: str, token: str, context: str) -> None:
    if token not in haystack:
        raise Drift(f"{context}: missing {token}")


def ordered(haystack: str, tokens: tuple[str, ...], context: str) -> None:
    previous = -1
    for token in tokens:
        next_pos = haystack.find(token, previous + 1)
        if next_pos < 0:
            raise Drift(f"{context}: missing/out-of-order {token}")
        previous = next_pos


def check(source: dict[str, str]) -> None:
    if set(source) != set(FILES):
        raise Drift("Missing authentic source file")

    session = method(compact(source["session"]), "MakeVitBuffers(")
    ordered(session, (
        "b.input=i?result.back().output:Make(plane);",
        "b.hidden=Make(plane*4u);",
        "b.ffwd=Make(plane);",
        "b.attention_context=Make(plane);",
        "b.output=Make(plane);",
        "b.scratch=Make(plane*4u);",
        "b.query=Make(plane*4u);",
        "b.key=Make(plane*4u);",
        "b.value=Make(plane*4u);",
        "result.emplace_back(b);",
    ), "MakeVitBuffers allocation roles")
    require(session, "result.reserve(vit_route.count);", "Eight-block allocator")
    require(session, "for(std::uint32_ti=0u;i<vit_route.count;++i)",
            "Eight-block allocator")

    run = compact(source["run"])
    initialize = method(run, "NrRdna2VitRun::InitializeWithModel(")
    require(initialize, "buffers.size()!=route.count", "Native route buffer count")
    require(initialize, "route.count!=8u", "Eight learned blocks")
    require(initialize,
            "!ExactBuffer(buffers[i].input,buffers[i-1u].output)",
            "Cross-block output/input identity")
    require(initialize, "block->InitializeWithModel(", "Real learned block")
    require(initialize, "prepared.push_back(std::move(block));",
            "Native prepared-block sequencing")
    record_run = method(run, "NrRdna2VitRun::Record()")
    ordered(record_run, (
        "if(has_incoming&&",
        "boundary.Record(",
        "for(constauto&block:blocks)",
        "if(!block||!block->Record())returnfalse;",
        "return!has_outgoing||",
    ), "Serial ViT orchestration")

    block = compact(source["block"])
    prepare_block = method(block, "NrRdna2VitBlock::InitializeWithModel(")
    ordered(prepare_block, (
        "prepared->expand.InitializeWithModel(",
        "prepared->contract.InitializeWithModel(",
        "prepared->qkv.InitializeWithModel(",
        "prepared->projection.InitializeWithModel(",
    ), "ViT initialization stage bindings")
    require(prepare_block, "b.input,b.scratch,b.hidden", "FFN input")
    require(prepare_block, "b.hidden,b.scratch,b.ffwd,b.input",
            "FFN residual dependency")
    require(prepare_block, "b.ffwd,{},b.scratch,{},b.query,b.key,b.value,b.attention_context",
            "QKV intermediate dependency")
    require(prepare_block, "b.attention_context,b.scratch,b.output,b.ffwd",
            "Terminal projection dependency")
    record_block = method(block, "NrRdna2VitBlock::Record()")
    ordered(record_block, (
        "state->expand.Record()",
        "state->contract.Record()",
        "state->qkv.Record()",
        "state->projection.Record()",
    ), "Four serial GPU subgraphs")

    projection = method(compact(source["projection"]),
                        "NrRdna2VitProjectionStage::Record()")
    ordered(projection, (
        "gemm.Record(",
        "if(kind==NR::VitProjectionKind::Expand)",
        "epilogue.RecordActivation(",
        "epilogue.RecordResidual(",
    ), "Projection stage record order")

    epilogue = compact(source["epilogue"])
    require(epilogue, "srcAccessMask=VK_ACCESS_SHADER_WRITE_BIT",
            "Visibility barrier source")
    require(epilogue,
            "dstAccessMask=VK_ACCESS_SHADER_READ_BIT|VK_ACCESS_SHADER_WRITE_BIT",
            "Visibility barrier destination")
    residual = method(epilogue, "NrRdna2VitEpilogue::RecordResidual(")
    ordered(residual, (
        "scheduler.RequestOutsideRenderPassOperationContext();",
        "scheduler.Record(",
        "cmd.Dispatch(",
        "cmd.PipelineBarrier(",
    ), "Terminal projection memory visibility")
    require(residual,
        "cmd.PipelineBarrier(VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,"
        "VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,0,kVisible);",
        "Inter-stage compute visibility")

    qkv = method(compact(source["qkv"]),
                 "NrRdna2VitQkvAttentionLink::Record()")
    ordered(qkv, (
        "gemm.Record(",
        "normalize.Record(",
        "attention.Record(",
    ), "Learned QKV ordering")
    require(compact(source["qkv"]), "DistinctBuffers(",
            "Independent QKV/weight descriptors")


def git(vendor: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(vendor), *args],
        check=True, capture_output=True, text=True,
    )
    return result.stdout


def load_pinned(vendor: Path) -> dict[str, str]:
    # Exact tree object, not vendor's moving main. Partial-clone Git may
    # lazily fetch these six pinned blobs. No checkout/pin update occurs.
    return {
        key: git(vendor, "show", f"HEAD:{ROOT}{filename}")
        for key, filename in FILES.items()
    }


def negative_self_tests(source: dict[str, str]) -> int:
    mutations = (
        ("missing epilogue barrier", "epilogue",
         "cmd.PipelineBarrier(VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,",
         "cmd.RemovedBarrier(VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,"),
        ("lost read/write visibility", "epilogue",
         "VK_ACCESS_SHADER_READ_BIT|VK_ACCESS_SHADER_WRITE_BIT",
         "VK_ACCESS_SHADER_READ_BIT"),
        ("broken cross-block identity", "run",
         "!ExactBuffer(buffers[i].input,buffers[i-1u].output)",
         "false"),
        ("wrong block stage order", "block",
         "if(!state->contract.Record())return false;",
         "if(!state->projection.Record())return false;"),
        ("broken pool allocation role", "session",
         "b.scratch=Make(plane*4u);", "b.scratch=Make(plane);"),
        ("missing serial record", "run",
         "if(!block||!block->Record())return false;",
         "if(!block)return false;"),
        ("wrong terminal source", "block",
         "b.attention_context,b.scratch,\n        b.output,b.ffwd",
         "b.attention_context,b.scratch,\n        b.input,b.ffwd"),
    )
    for name, filename, old, new in mutations:
        if old not in source[filename]:
            raise Drift(f"Mutation fixture drifted: {name}")
        mutated = dict(source)
        # Replace all matching barriers, including the terminal residual one.
        # Otherwise the negative fixture could modify RecordActivation
        # while leaving the critical RecordResidual barrier intact.
        mutated[filename] = source[filename].replace(old, new)
        try:
            check(mutated)
        except Drift:
            continue
        raise Drift(f"Unsafe mutation wrongly accepted: {name}")
    return len(mutations)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--vendor", required=True, type=Path)
    args = parser.parse_args()
    vendor = args.vendor.resolve()
    pinned = git(vendor, "rev-parse", "HEAD").strip()
    if len(pinned) != 40:
        raise Drift("Expected pinned vendor Git SHA")
    sources = load_pinned(vendor)
    check(sources)
    negatives = negative_self_tests(sources)
    for key, filename in FILES.items():
        sha = hashlib.sha256(sources[key].encode()).hexdigest()[:16]
        print(f"R09_MIN_VENDOR_SOURCE_GUARD {filename} sha256={sha}")
    print(f"R09_MIN_VENDOR_PIN={pinned}")
    print(f"R09_MIN_VENDOR_SOURCE_ORDER_BARRIERS_GUARD_PASS negatives={negatives}")
    print("R09_MIN_SOURCE_GUARD_NECESSARY_NOT_GPU_SAFETY_PROOF")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (Drift, subprocess.CalledProcessError) as error:
        print(f"R09_MIN_VENDOR_SOURCE_GUARD_FAIL: {error}")
        raise SystemExit(1)
