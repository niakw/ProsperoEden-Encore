#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Fail-closed audit of real per-FSwin-layer allocated tensor requests.

Native FrameSession external tensor accounting is NOT comprehensive unless
the separately owned FSwinLayerRuntime::tensors buffers are accounted for.
"""
from __future__ import annotations
import argparse
import subprocess
from pathlib import Path
from test_dlss_nr_min_vendor_source_guard import Drift, compact, git, method, require

PREFIX="encore-active/eden-vulkan/"
PATHS={
    "tensors":PREFIX+"nr_rdna2_fswin_gpu_tensors.cpp",
    "runtime":PREFIX+"nr_rdna2_fswin_layer_runtime.cpp",
    "chain":PREFIX+"nr_rdna2_fswin_chain.cpp",
    "plan":PREFIX+"include/video_core/renderer_vulkan/nr_rdna2_fswin_plan.h"
}
def guard(files:dict[str,str])->None:
    if set(files)!=set(PATHS):raise Drift("Missing native FSwin owners")
    tensor=method(compact(files["tensors"]),
                  "boolNrRdna2FSwinGpuTensors::Initialize(")
    runtime=method(compact(files["runtime"]),
                   "boolNrRdna2FSwinLayerRuntime::Initialize(")
    chain=method(compact(files["chain"]),
                 "boolNrRdna2FSwinChain::Initialize(")
    plan=method(compact(files["plan"]),"boolMakeFSwinGraphPlan(")
    for name,value in {"tensors":tensor,"runtime":runtime,
                       "chain":chain,"plan":plan}.items():
        if not value:raise Drift(f"No actual FSwin allocation method: {name}")
    for fragment,why in (
        ("constboolc32=p.dense[0].channels==32u;",
         "C32 optional middle buffer"),
        ("std::max(p.dense_storage[0].input_bytes,p.dense_storage[2].residual_bytes)",
         "Actual input buffer allocation"),
        ("p.dense_storage[0].output_bytes,",
         "4x expansion buffer allocation"),
        ("c32?0u:p.dense_storage[1].output_bytes,",
         "C64+ dense middle buffer"),
        ("std::max({p.dense_storage[2].output_bytes,p.dense_storage[3].residual_bytes,p.qkv_storage.activation_bytes})",
         "Contracted activation buffer"),
        ("0u,0u,0u,", "QKV alias expanded, no separate VMA"),
        ("std::max(p.attention_storage.out_bytes,p.dense_storage[3].input_bytes)",
         "Context storage"),
        ("p.dense_storage[3].output_bytes", "Output storage"),
        ("constexprstd::uint64_tkMaxTotal=512ull<<20;",
         "FSwin single-layer 512 MiB cap"),
        ("bytes>(256ull<<20)", "FSwin single-buffer 256 MiB cap"),
        ("total+=bytes;", "FSwin total request accounting"),
        ("created[i]=allocator.CreateBuffer(", "Native VMA allocation"),
    ):
        require(tensor,fragment,why)
    require(runtime,"MakeFSwinGraphPlan(channels,windows,proposed)",
            "FSwin graph plan real source")
    require(runtime,"if(!tensors.Initialize(proposed))returnfalse;",
            "FSwin layer creates its own tensor owner")
    require(chain,"for(constauto&spec:specs)", "Independent runtime per layer")
    require(chain,"prepared.emplace_back(std::move(runtime));",
            "All FSwin layers stay owned until session retirement")
    require(plan,"conststd::uint64_ttokens=std::uint64_t(windows)*64u;",
            "Per-layer padded window token count")
    require(plan,"conststd::uint64_ttensor=tokens*C;",
            "Per-layer FP8 tensor")
    require(plan,"plan.dense_storage[i]={in,weights,tokens*C,",
            "Dense residual tensor shape")
    require(plan,"plan.attention_storage={tensor,tensor,tensor,tensor,",
            "Attention context tensor shape")

def negatives(original:dict[str,str])->int:
    mutations=(
      ("drop input max","tensors",
       "std::max(p.dense_storage[0].input_bytes,",
       "std::min(p.dense_storage[0].input_bytes,"),
      ("drop C32 optimization","tensors",
       "c32?0u:p.dense_storage[1].output_bytes",
       "p.dense_storage[1].output_bytes"),
      ("inflate QKV","tensors","0u,0u,0u, // Q/K/V",
       "32u,32u,32u, // Q/K/V"),
      ("skip total accumulation","tensors","total+=bytes;","total+=0u;"),
      ("change total cap","tensors","512ull<<20","256ull<<20"),
      ("change per-buffer cap","tensors","bytes>(256ull<<20)",
       "bytes>(128ull<<20)"),
      ("skip owner initialization","runtime",
       "if(!tensors.Initialize(proposed))return false;",
       "if(false)return false;"),
      ("fail to retain layer","chain",
       "prepared.emplace_back(std::move(runtime));",
       "prepared.clear();"),
      ("change window token size","plan",
       "std::uint64_t(windows)*64u",
       "std::uint64_t(windows)*32u"),
    )
    for name,owner,before,after in mutations:
        if before not in original[owner]:
            raise Drift(f"Mutation pattern drift: {name}")
        mutated=dict(original)
        mutated[owner]=original[owner].replace(before,after)
        try: guard(mutated)
        except Drift: continue
        raise Drift(f"Unsafe source change was accepted: {name}")
    return len(mutations)

def main()->None:
    p=argparse.ArgumentParser()
    p.add_argument("--vendor",type=Path,required=True)
    a=p.parse_args()
    sources={name:git(a.vendor,"show",f"HEAD:{path}")
             for name,path in PATHS.items()}
    guard(sources)
    count=negatives(sources)
    print("R09_MIN_720_FSWIN_NATIVE_OWNER_GUARD_PASS "
          f"mutations={count} "
          f"pin={git(a.vendor,'rev-parse','HEAD').strip()}")
    print("R09_MIN_720_FSWIN_VMA_REQUESTS_ONLY_NO_REAL_GPU")

if __name__=="__main__":
    try: main()
    except (Drift,subprocess.CalledProcessError) as e:
        print(f"R09_MIN_720_FSWIN_OWNER_GUARD_FAIL: {e}")
        raise SystemExit(1)
