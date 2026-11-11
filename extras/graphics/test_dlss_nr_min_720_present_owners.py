#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Audit default + dormant research 720p R09 -> FSR Vulkan ownership.

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
    # The DEFAULT presenter still runs FSR first. The research-only
    # path is dormant behind TWO independent FALSE qualification flags.
    # Both paths must remain correctly ordered and resource-owned.
    ordered(draw, (
        "constautoselected=Eden::NeuralRuntime::Current();",
        "boolresearch_post_neural_fsr=false;",
        "source_image_view=fsr->Draw(",
        "constboolnr_exclusive=",
        "neural_images[image_index]=memory_allocator.CreateImage(",
        "constboolr09_recorded=neural_sessions[image_index]->Record();",
        "source_image=target;",
        "source_image_view=*neural_views[image_index];",
        "constVkImageViewupscaled=fsr->Draw(",
        "SetMatrixData(",
    ), "Default FSR-before-R09 and separately gated post-R09 FSR")
    for token,why in (
        ("if(!research_post_neural_fsr){",
         "Default pre-neural FSR must be unchanged"),
        ("Eden::Graphics::DlssNrMin::kPostNeuralFsrRuntimeWired",
         "Missing first explicit runtime denial"),
        ("Eden::Graphics::DlssNrMin::kPs5MinRuntimeQualified",
         "Missing second explicit runtime denial"),
        ("std::holds_alternative<std::monostate>(sr_filter)",
         "Default FSR exclusivity"),
        ("std::holds_alternative<FSR>(sr_filter)",
         "Research FSR selection"),
        ("std::holds_alternative<std::monostate>(anti_alias)",
         "AA exclusivity"),
        ("VkExtent2D{1280u,720u}", "Research neural output shape"),
        ("VkExtent2D{1920u,1080u}", "Unmodified 1080p default shape"),
        (".extent={neural_extent.width,neural_extent.height,1u}",
         "Output VkImage matches admitted neural extent"),
        ("target,*neural_views[image_index],neural_extent,crop_rect",
         "FSR input must be real neural VkImage AND VkImageView"),
        ("srcAccessMask=VK_ACCESS_SHADER_WRITE_BIT",
         "Neural compute write visibility"),
        ("dstAccessMask=VK_ACCESS_SHADER_READ_BIT",
         "FSR shader sample visibility"),
        ("VK_PIPELINE_STAGE_FRAGMENT_SHADER_BIT",
         "Compute-to-fragment barrier"),
        ("source_image_view=preserved_guest_view;",
         "Restore original guest image view after failure"),
        ("crop_rect=preserved_guest_crop;",
         "Restore original guest crop after failure"),
        ("if(!upscaled)throwstd::runtime_error(",
         "Null FSR output must fail closed"),
        ("VK_FORMAT_R32G32B32A32_SFLOAT",
         "Neural output/storage format"),
    ):
        require(draw,token,why)
    ordered(draw, (
        "scheduler.Wait(resource_ticks[image_index]);",
        "neural_sessions[image_index].reset();",
    ), "Per-slot fence before neural-image lifetime retirement")

    # The GPU result is a distinct image+view, not the guest image.
    result=draw[draw.find("constboolr09_recorded="):]
    result=result[:result.find("SetMatrixData(")]
    require(result,"source_image=target;",
            "Real neural VkImage owner must be forwarded")
    require(result,"source_image_view=*neural_views[image_index];",
            "Neural output VkImageView identity")
    require(result,"constVkImageViewupscaled=fsr->Draw(",
            "FSR after neural output must exist under research macro")
    require(result,"source_image_view=upscaled;",
            "FSR RCAS result must feed final presentation")

    fsr_images=method(compact(owners["fsr"]), "voidFSR::CreateImages(")
    require(fsr_images, "m_dynamic_images.resize(m_image_count);",
            "Per-frame FSR image slots")
    for stage in ("Easu","Rcas"):
        require(fsr_images,
                f"images.images[{stage}]=CreateWrappedImage(m_memory_allocator,"
                "m_extent,VK_FORMAT_R16G16B16A16_SFLOAT);",
                f"Native {stage} RGBA16F output surface")
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
        ("default FSR mode exclusivity","presenter",
         "std::holds_alternative<std::monostate>(sr_filter)",
         "std::holds_alternative<FSR>(sr_filter)"),
        ("premature 720-only output","presenter",
         "VkExtent2D{1920u,1080u}","VkExtent2D{1280u,720u}"),
        ("wrong research raster","presenter",
         "VkExtent2D{1280u,720u}","VkExtent2D{1920u,1080u}"),
        ("lost pre-FSR defer guard","presenter",
         "if(!research_post_neural_fsr){","if(research_post_neural_fsr){"),
        ("lifted first qualification gate","presenter",
         "Eden::Graphics::DlssNrMin::kPostNeuralFsrRuntimeWired",
         "true"),
        ("lost neural VkImage ownership","presenter",
         "source_image=target;","source_image=guest_source;"),
        ("wrong FSR input image","presenter",
         "target,*neural_views[image_index],",
         "guest_source,*neural_views[image_index],"),
        ("lost compute to fragment barrier","presenter",
         "VK_PIPELINE_STAGE_FRAGMENT_SHADER_BIT,",
         "VK_PIPELINE_STAGE_TRANSFER_BIT,"),
        ("null FSR result accepted","presenter",
         "if(!upscaled)throw std::runtime_error(",
         "if(false)throw std::runtime_error("),
        ("lost guest fallback","presenter",
         "source_image_view=preserved_guest_view;",
         "source_image_view=source_image_view;"),
        ("lost slot fence","presenter",
         "scheduler.Wait(resource_ticks[image_index]);",
         "scheduler.NotWait(resource_ticks[image_index]);"),
        ("wrong neural result view","presenter",
         "source_image_view=*neural_views[image_index];",
         "source_image_view=*raw_image_views[image_index];"),
        ("lost FSR shader input","fsr",
         "UpdateDescriptorSets(device, source_image_view, image_index);",
         "UpdateDescriptorSets(device, VK_NULL_HANDLE, image_index);"),
        ("lost native neural fragment visibility","neural_present",
         "VK_PIPELINE_STAGE_FRAGMENT_SHADER_BIT |",
         "VK_PIPELINE_STAGE_TRANSFER_BIT |"),
        ("FSR EASU output format drift","fsr",
         "images.images[Easu] = CreateWrappedImage(m_memory_allocator, m_extent, VK_FORMAT_R16G16B16A16_SFLOAT);",
         "images.images[Easu] = CreateWrappedImage(m_memory_allocator, m_extent, VK_FORMAT_R32G32B32A32_SFLOAT);"),
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
    # Both flags MUST remain false. Do not let a successful source
    # guard silently enable a console runtime or declare GPU proof.
    present_policy=compact(Path(
        "extras/graphics/dlss_nr_min_720_present_handoff.h").read_text())
    runtime_policy=compact(Path(
        "extras/graphics/dlss_nr_min_policy.h").read_text())
    require(present_policy,"inlineconstexprboolkPostNeuralFsrRuntimeWired=false;",
            "Post-neural FSR remains default-OFF")
    require(runtime_policy,"inlineconstexprboolkPs5MinRuntimeQualified=false;",
            "PS5 neural mode remains default-OFF")
    print("R09_MIN_720_DEFAULT_FSR_FIRST_RESEARCH_FSR_AFTER_NEURAL_SOURCE_PRESENT")
    print("R09_MIN_720_POST_NEURAL_FSR_RUNTIME_DISABLED_NOT_GPU_QUALIFIED")
    return 0

if __name__=="__main__":
    try:
        raise SystemExit(main())
    except (Drift,subprocess.CalledProcessError) as exc:
        print(f"R09_MIN_720_PRESENT_OWNER_FAIL: {exc}")
        raise SystemExit(1)
