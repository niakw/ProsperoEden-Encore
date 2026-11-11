#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Check host 720p frame-allocation estimates against genuine pinned owner.

Guard is deliberately rigid: if the native owner changes, the estimate
MUST fail rather than silently undercounting the buffer allocations.
"""
from __future__ import annotations
import argparse
import subprocess
from pathlib import Path
from test_dlss_nr_min_vendor_source_guard import Drift, compact, git, method, require

PATH="encore-active/eden-vulkan/nr_rdna2_frame_session.cpp"

def guard(native: str) -> None:
    source=compact(native)
    make=method(source,"VkDescriptorBufferInfoMake(")
    split=method(source,"boolMakeFirstSplitBuffers(")
    vit=method(source,"boolMakeVitBuffers(")
    initialize=method(source,"boolNrRdna2FrameSession::Initialize(")
    for name,fn in {"State::Make":make,"MakeFirstSplitBuffers":split,
                    "MakeVitBuffers":vit,"Initialize":initialize}.items():
        if not fn:
            raise Drift(f"Required native allocation owner missing: {name}")
    require(make,"constexprstd::uint64_tper=256ull<<20;",
            "Native single-buffer 256 MiB cap")
    require(make,"constexprstd::uint64_ttotal=3ull<<30;",
            "Native 3 GiB frame-session cap")
    require(make,"owned_bytes>total-size", "Overflow-safe total cap")
    require(make,"size>dev.GetMaxStorageBufferRange()",
            "Vulkan maxStorageBufferRange independent constraint")
    require(make,"(size&3u)", "Four-byte buffer alignment")
    require(make,"owned_bytes+=size;", "Native allocation byte counter")

    require(split,"b.input=i?result.back().projected:",
            "Actual split projected-input alias")
    require(split,"decoder_input.buffer?decoder_input:Make(linear);",
            "Second split reuses existing decoder buffer")
    for field in ("ffwd","ffwd_projected","context_heads","context_tokens",
                  "projected","query","key","value"):
        require(split,f"b.{field}=Make(linear);",f"Split {field} plane")
    require(split,"b.fp32_scratch=Make(linear*4u);",
            "Split 4x scratch allocation")
    require(split,"b.shifted_input=Make(linear);",
            "Split shifted input plane")
    require(split,"b.unshifted_context=Make(linear);",
            "Split shifted context plane")
    require(split,"b.pooled=Make(std::uint64_t(p.pool_output_tokens)*512u);",
            "Split pooled input")
    require(split,
        "b.final_fp32=Make(std::uint64_t(p.final_head_tokens)*1024u*4u);",
        "Split final projection FP32")
    require(split,
        "b.final_output=Make(std::uint64_t(p.final_head_tokens)*1024u);",
        "Split final projection output")

    require(vit,"b.input=i?result.back().output:Make(plane);",
            "ViT block0 allocated, later blocks aliased")
    for field,mul in {
        "hidden":4,"ffwd":1,"attention_context":1,"output":1,
        "scratch":4,"query":4,"key":4,"value":4}.items():
        suffix="*4u" if mul==4 else ""
        require(vit,f"b.{field}=Make(plane{suffix});",
                f"ViT {field} allocation")

    # All non-FSwin external allocations must retain these precise stage
    # sizes; internal per-chain allocations remain outside the estimate.
    for field,size in {
        "proxy":"n*16u",
        "feature16":"n*32u",
        "lifted":"n*32u",
        "full_skip":"n*32u",
        "raw_pre":"n*64u",
        "first_half":"n*32u/4u",
        "decoder_tiles":"std::uint64_t(q.vit_route.tokens)*1024u",
        "post_mixed":"n*32u",
        "post_swin":"n*32u",
        "post_raw":"n*64u",
        "post_features":"n*32u",
        "image":"n*16u",
        "second_low":"valid*512u"
    }.items():
        require(initialize,
                f"constauto{field}=q.Make({size});" if field not in (
                    "post_mixed","post_swin","post_raw","post_features") else
                f"q.{field}=q.Make({size});",
                f"FrameSession {field} external buffer")
    for fragment,description in {
        "std::uint64_t(edge.skip_height/2u)*":"Downsample height",
        "(edge.skip_width/2u)*(2u*edge.channels)":"Downsample width/channels",
        "q.up_outputs[i]=q.Make(std::uint64_t(edge.skip_height)*edge.skip_width*edge.channels);":
            "UNet up output",
        "constautolinear=q.Make(valid*1024u),fp32=q.Make(valid*512u*4u),half=q.Make(valid*512u*2u),skip_tiled=q.Make(std::uint64_t(q.vit_route.tokens)*512u),decoder_output=q.Make(std::uint64_t(q.vit_route.tokens)*512u);":
            "Six decoder external surfaces",
    }.items():
        require(initialize,fragment,description)

def check_mutations(original: str)->int:
    mutations=(
        ("per-buffer cap","256ull<<20","128ull<<20"),
        ("total cap","3ull<<30","2ull<<30"),
        ("preblock input bytes","const auto proxy=q.Make(n*16u);",
         "const auto proxy=q.Make(n*32u);"),
        ("ViT 4x scratch","b.scratch=Make(plane*4u);",
         "b.scratch=Make(plane*8u);"),
        ("ViT output alias","b.input=i?result.back().output:Make(plane);",
         "b.input=Make(plane);"),
        ("Split FP32 scratch","b.fp32_scratch=Make(linear*4u);",
         "b.fp32_scratch=Make(linear*8u);"),
        ("Split extra projection","b.ffwd=Make(linear);",
         "b.ffwd=Make(linear*2u);"),
        ("Unet up output","edge.skip_width*edge.channels",
         "edge.skip_width*edge.channels*2u"),
        ("Decoder FP32 projection","fp32=q.Make(valid*512u*4u)",
         "fp32=q.Make(valid*512u*8u)"),
        ("Neural compose buffer","const auto image=q.Make(n*16u);",
         "const auto image=q.Make(n*32u);"),
        ("Lost second split low","const auto second_low=q.Make(valid*512u);",
         "const auto second_low=q.Make(valid*1024u);"),
    )
    for name,before,after in mutations:
        if before not in original:
            raise Drift(f"Mutation fixture changed: {name}")
        try:
            guard(original.replace(before,after))
        except Drift:
            continue
        raise Drift(f"Unsafe native allocation mutation accepted: {name}")
    return len(mutations)

def main()->None:
    p=argparse.ArgumentParser()
    p.add_argument("--vendor",required=True,type=Path)
    options=p.parse_args()
    source=git(options.vendor,"show",f"HEAD:{PATH}")
    guard(source)
    negatives=check_mutations(source)
    print(f"R09_MIN_720_NATIVE_FRAME_SOURCE_OWNER_PIN="
          f"{git(options.vendor,'rev-parse','HEAD').strip()}")
    print(f"R09_MIN_720_NATIVE_FRAME_ALLOCATION_GUARD_PASS "
          f"negative_mutations={negatives} fswin_internal=EXCLUDED")
    print("R09_MIN_720_GPU_VRAM_NOT_MEASURED_RUNTIME_DISABLED")

if __name__=="__main__":
    try:
        main()
    except (Drift, subprocess.CalledProcessError) as e:
        print(f"R09_MIN_720_NATIVE_FRAME_ALLOCATION_FAIL {e}")
        raise SystemExit(1)
