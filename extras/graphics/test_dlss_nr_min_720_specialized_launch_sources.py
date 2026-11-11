#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Fail-closed source-owner audit of 720p R09 specialized Vulkan launches.

Authentic pinned vendor source, never a substitute for actual GPU execution.
The 1080p NRMODEL1 grid metadata is NOT itself a VkCommandBuffer dispatch:
native ViT/decoder owners calculate launch sizes from validated tokens/tiles.
"""
from __future__ import annotations

import argparse
import hashlib
import subprocess
from pathlib import Path

from test_dlss_nr_min_vendor_source_guard import Drift, compact, git, method, require

ROOT = "encore-active/eden-vulkan/"
OWNERS = {
    "attention": "nr_rdna2_vit_attention.cpp",
    "normalize": "nr_rdna2_vit_qkv_norm.cpp",
    "decoder": "nr_rdna2_decoder_upsample.cpp",
    "decoder_link": "nr_rdna2_native_decoder_link.cpp",
    "boundary": "nr_rdna2_vit_boundary_repack.cpp",
    "epilogue": "nr_rdna2_vit_epilogue.cpp",
    "vit_run": "nr_rdna2_vit_run.cpp",
}

# Each assertion refers to an actual command owner, not model-plan grid_x/y.
RECORDS = {
    "attention": (
        "NrRdna2VitAttention::Record(",
        ("CanVitAttention(request,storage)",
         "cmd.Dispatch((request.tokens+31u)/32u,32,1);",
         "cmd.PipelineBarrier("),
    ),
    "normalize": (
        "NrRdna2VitQkvNorm::Record(",
        ("CanVitQkvNorm(shape,storage)",
         "cmd.Dispatch(shape.tokens,32u,1u);",
         "cmd.PipelineBarrier("),
    ),
    "decoder": (
        "NrRdna2DecoderUpsample::Record(",
        ("CanDecoderUpsample(request,storage)",
         "DecoderOutputTileTokens(request)+63u)/64u",
         "cmd.Dispatch(group_x,128,1);",
         "cmd.PipelineBarrier("),
    ),
    "boundary": (
        "NrRdna2VitBoundaryRepack::Record(",
        ("CanVitBoundaryRepack(", "constautogroups=NR::VitBoundaryGrid(shape);",
         "cmd.Dispatch(groups,1u,1u);",
         "cmd.PipelineBarrier("),
    ),
    "epilogue_activation": (
        "NrRdna2VitEpilogue::RecordActivation(",
        ("CanVitActivation(", "NR::VitEpilogueGroups(p.tokens,p.channels)",
         "cmd.Dispatch(groups,1,1);", "cmd.PipelineBarrier("),
    ),
    "epilogue_residual": (
        "NrRdna2VitEpilogue::RecordResidual(",
        ("CanVitResidual(", "NR::VitEpilogueGroups(p.tokens,p.channels)",
         "cmd.Dispatch(groups,1,1);", "cmd.PipelineBarrier("),
    ),
}


def check(source: dict[str, str]) -> None:
    if set(source) != set(OWNERS):
        raise Drift("Native owner list incomplete")
    for label, (signature, requirements) in RECORDS.items():
        key = "epilogue" if label.startswith("epilogue_") else label
        body = method(compact(source[key]), signature)
        for token in requirements:
            require(body, token, label)
        if "grid_x" in body or "grid_y" in body or "grid_z" in body:
            raise Drift(f"{label}: model-plan grid unexpectedly drives GPU launch")

    link = method(compact(source["decoder_link"]),
                  "NrRdna2NativeDecoderLink::InitializeWithModel(")
    require(link, "BuildDecoderProjectionBatches(width,height,", "Dynamic decoder projection")
    require(link, "0u,0u,0u,0u,width,width,height", "Native decoder request")
    require(link, "CanDecoderUpsample(request,storage)", "Decoder resource preflight")
    record = method(compact(source["decoder_link"]),
                    "NrRdna2NativeDecoderLink::Record()")
    require(record, "returnupsample.Record(", "Decoder submit path")

    vit = method(compact(source["vit_run"]),
                 "NrRdna2VitRun::InitializeWithModel(")
    for required in ("route.count!=8u", "route.tokens>4096u",
                     "route.raster_width,route.raster_height,1024u,route.tokens,0u",
                     "route.raster_width,route.raster_height,1024u,route.tokens,1u",
                     "block->InitializeWithModel(model,step.block,step.tokens,buffers[i])"):
        require(vit, required, "Dynamic eight-block ViT route")
    record_vit = method(compact(source["vit_run"]), "NrRdna2VitRun::Record()")
    for required in ("boundary.Record(", "block->Record()"):
        require(record_vit, required, "ViT command owners")


def negative_tests(source: dict[str, str]) -> int:
    mutations = (
        ("attention launch", "attention",
         "cmd.Dispatch((request.tokens+31u)/32u,32,1);",
         "cmd.Dispatch((request.tokens+63u)/64u,32,1);"),
        ("normalization launch", "normalize",
         "cmd.Dispatch(shape.tokens,32u,1u);",
         "cmd.Dispatch(shape.tokens,16u,1u);"),
        ("decoder launch", "decoder",
         "cmd.Dispatch(group_x,128,1);",
         "cmd.Dispatch(group_x,64,1);"),
        ("boundary launch", "boundary",
         "cmd.Dispatch(groups,1u,1u);",
         "cmd.Dispatch(groups,2u,1u);"),
        ("residual launch", "epilogue",
         "const u32 groups=NR::VitEpilogueGroups(p.tokens,p.channels);",
         "const u32 groups=NR::VitEpilogueGroups(p.tokens,p.channels/2u);"),
        ("decoder 720p shape", "decoder_link",
         "0u,0u,0u,0u,width,width,height",
         "0u,0u,0u,0u,width,1920u,height"),
        ("ViT eight-block count", "vit_run",
         "route.count!=8u", "route.count!=4u"),
    )
    for title, key, before, after in mutations:
        if before not in source[key]:
            raise Drift(f"Mutation fixture drift: {title}")
        variant = dict(source)
        variant[key] = source[key].replace(before, after)
        try:
            check(variant)
        except Drift:
            continue
        raise Drift(f"Mutation wrongly accepted: {title}")
    return len(mutations)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--vendor", type=Path, required=True)
    args = parser.parse_args()
    vendor = args.vendor.resolve()
    pinned = git(vendor, "rev-parse", "HEAD").strip()
    if len(pinned) != 40:
        raise Drift("Missing full SHA of pinned vendor")
    source = {name: git(vendor, "show", f"HEAD:{ROOT}{filename}")
              for name, filename in OWNERS.items()}
    check(source)
    negatives = negative_tests(source)
    for name, filename in OWNERS.items():
        digest = hashlib.sha256(source[name].encode()).hexdigest()[:16]
        print(f"R09_MIN_720_OWNER {filename} sha256={digest}")
    print(f"R09_MIN_720_OWNER_VENDOR_PIN={pinned}")
    print(f"R09_MIN_720_OWNER_SOURCE_GUARD_PASS owners={len(OWNERS)} "
          f"record_contracts={len(RECORDS)} negatives={negatives}")
    print("R09_MIN_720_41_INHERITED_PLAN_GRIDS_NOT_NATIVE_DISPATCH_WITNESS")
    print("R09_MIN_720_GPU_MODEL_INFERENCE_NOT_QUALIFIED_RUNTIME_DISABLED")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (Drift, subprocess.CalledProcessError) as error:
        print(f"R09_MIN_720_OWNER_GUARD_FAIL: {error}")
        raise SystemExit(1)
