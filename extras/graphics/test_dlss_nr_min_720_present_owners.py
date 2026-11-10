#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Audit the *currently unconnected* 720p R09 -> FSR handoff owners.

This is a fail-closed source guard, not a demonstration of a functioning
post-neural FSR path. It requires actual Encore presenter and pinned vendor
source, and rejects mutations that would invalidate the integration plan.
"""
from __future__ import annotations

import argparse
import hashlib
import re
import subprocess
from pathlib import Path
from test_dlss_nr_min_vendor_source_guard import Drift, compact, git, method, ordered, require

OWNERS = {
    "fsr": "sources/eden/src/video_core/renderer_vulkan/present/fsr.cpp",
    "neural_present": "encore-active/eden-vulkan/nr_rdna2_nohistory_present.cpp",
}

def check(presenter: str, owners: dict[str, str]) -> None:
    if set(owners) != set(OWNERS):
        raise Drift("Pinned presenter owner list mismatch")
    draw = method(compact(presenter), "voidLayer::ConfigureDraw(")
    # Existing code still passes FSR BEFORE R09, which must be changed in
    # a later isolated, preflighted integration commit, not by this test.
    ordered(draw, (
        "source_image_view=fsr->Draw(",
        "constautoselected=Eden::NeuralRuntime::Current();",
        "constboolnr_exclusive=",
        "neural_images[image_index]=memory_allocator.CreateImage(",
        "constboolr09_recorded=neural_sessions[image_index]->Record();",
        "source_image_view=*neural_views[image_index];",
        "SetMatrixData(",
    ), "Existing FSR-before-R09 presenter order")
    require(draw, "std::holds_alternative<std::monostate>(sr_filter)",
            "Present-mode FSR exclusivity")
    require(draw, "std::holds_alternative<std::monostate>(anti_alias)",
            "Present-mode AA exclusivity")
    require(draw, ".extent={1920u,1080u,1u}",
            "Still-fixed R09 Vulkan output image")
    require(draw, "VK_FORMAT_R32G32B32A32_SFLOAT",
            "Neural storage image format")
    ordered(draw, (
        "scheduler.Wait(resource_ticks[image_index]);",
        "neural_sessions[image_index].reset();",
    ), "Current per-slot frame resource retirement")
    # The current neural-result path updates the VIEW, not the actual image
    # passed to FSR::Draw (which is currently called earlier anyway).
    result=draw[draw.find("constboolr09_recorded="):]
    result=result[:result.find("SetMatrixData(")]
    if re.search(r"\bsource_image\s*=", result):
        raise Drift("Presenter unexpectedly changed post-neural image ownership")
    require(result, "source_image_view=*neural_views[image_index];",
            "R09 successful result publishes only the view")

    fsr=method(compact(owners["fsr"]), "VkImageViewFSR::Draw(")
    ordered(fsr, (
        "UpdateDescriptorSets(device,source_image_view,image_index);",
        "TransitionImageLayout(cmdbuf,source_image,VK_IMAGE_LAYOUT_GENERAL);",
        "BeginRenderPass(cmdbuf,renderpass,easu_framebuffer,extent);",
        "BeginRenderPass(cmdbuf,renderpass,rcas_framebuffer,extent);",
        "return*images.image_views[Rcas];",
    ), "Actual FSR EASU then RCAS command owner")
    require(fsr, "FsrEasuConOffset(", "FSR source/target extent math")
    require(fsr, "FsrRcasCon(", "FSR sharpening")

    neural=compact(owners["neural_present"])
    require(neural, "srcAccessMask=VK_ACCESS_SHADER_WRITE_BIT",
            "R09 write visibility source")
    require(neural, "dstAccessMask=VK_ACCESS_SHADER_READ_BIT",
            "R09 sample visibility destination")
    record=method(neural, "NrRdna2NoHistoryPresent::Record()")
    ordered(record, (
        "cmd.Dispatch(gx,gy,1u);",
        "cmd.PipelineBarrier(",
        "VK_PIPELINE_STAGE_FRAGMENT_SHADER_BIT|",
    ), "Last neural write -> fragment reader synchronization")

def negative_tests(presenter: str, owners: dict[str, str]) -> int:
    tests=(
        ("premature 720p presenter", "presenter",
         ".extent={1920u,1080u,1u}", ".extent={1280u,720u,1u}"),
        ("lost FSR shader input view", "fsr",
         "UpdateDescriptorSets(device, source_image_view, image_index);",
         "UpdateDescriptorSets(device, VK_NULL_HANDLE, image_index);"),
        ("lost slot fence", "presenter",
         "scheduler.Wait(resource_ticks[image_index]);",
         "scheduler.NotWait(resource_ticks[image_index]);"),
        ("wrong neural result view", "presenter",
         "source_image_view=*neural_views[image_index];",
         "source_image_view=*raw_image_views[image_index];"),
        ("missing neural fragment visibility", "neural_present",
         "VK_PIPELINE_STAGE_FRAGMENT_SHADER_BIT |",
         "VK_PIPELINE_STAGE_TRANSFER_BIT |"),
        ("discard NR-FSR exclusivity", "presenter",
         "std::holds_alternative<std::monostate>(sr_filter)",
         "std::holds_alternative<FSR>(sr_filter)"),
    )
    for name,owner,before,after in tests:
        original=presenter if owner=="presenter" else owners[owner]
        if before not in original:
            raise Drift(f"Mutation source drift: {name}")
        changed=original.replace(before, after)
        p=changed if owner=="presenter" else presenter
        v=dict(owners)
        if owner!="presenter":
            v[owner]=changed
        try:
            check(p,v)
        except Drift:
            continue
        raise Drift(f"Unsafe mutation accepted: {name}")
    return len(tests)

def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("--vendor",type=Path,required=True)
    parser.add_argument("--presenter",type=Path,
                        default=Path("headless/vulkan_present_layer_r24.cpp"))
    args=parser.parse_args()
    if not args.presenter.is_file():
        raise Drift("Encore native presenter not present")
    presenter=args.presenter.read_text(encoding="utf-8")
    source={key:git(args.vendor,"show",f"HEAD:{path}")
            for key,path in OWNERS.items()}
    check(presenter,source)
    negatives=negative_tests(presenter,source)
    pin=git(args.vendor,"rev-parse","HEAD").strip()
    print(f"R09_MIN_720_PRESENT_OWNER_VENDOR_PIN={pin}")
    for key,data in [("presenter",presenter),*source.items()]:
        print(f"R09_MIN_720_PRESENT_SOURCE {key} "
              f"sha256={hashlib.sha256(data.encode()).hexdigest()[:16]}")
    print(f"R09_MIN_720_PRESENT_SOURCE_GUARD_PASS negatives={negatives}")
    print("R09_MIN_720_CURRENT_FSR_IS_PRE_NEURAL_AND_FIXED_1080")
    print("R09_MIN_720_POST_NEURAL_FSR_NOT_WIRED_NOT_GPU_QUALIFIED")
    return 0

if __name__=="__main__":
    try:
        raise SystemExit(main())
    except (Drift,subprocess.CalledProcessError) as exc:
        print(f"R09_MIN_720_PRESENT_OWNER_FAIL: {exc}")
        raise SystemExit(1)
