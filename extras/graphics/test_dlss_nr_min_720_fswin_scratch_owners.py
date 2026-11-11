#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Fail closed when the REAL pinned FSwin serialization owner changes.

The separate 720p scratch-only reuse policy is NOT wired to native buffers.
This contract checks prerequisites to an eventual opt-in pool, but neither
static source matches nor CPU tests prove GPU race freedom / PS5 safety.
"""
from __future__ import annotations
import argparse
import subprocess
from pathlib import Path
from test_dlss_nr_min_vendor_source_guard import Drift, compact, git, method, require, ordered

ROOT="encore-active/eden-vulkan/"
FILES={
    "chain":"nr_rdna2_fswin_chain.cpp",
    "runtime":"nr_rdna2_fswin_layer_runtime.cpp",
    "graph":"nr_rdna2_fswin_graph.cpp",
    "dense":"nr_rdna2_fswin_dense.cpp",
    "qkv":"nr_rdna2_fswin_qkv.cpp",
    "attention":"nr_rdna2_window_attention.cpp",
    "repack":"nr_rdna2_fswin_window_repack.cpp",
}
def check(files:dict[str,str])->None:
    if set(files)!=set(FILES):
        raise Drift("Missing source owners for pool barrier contract")
    chain=method(compact(files["chain"]),
                 "boolNrRdna2FSwinChain::Record(")
    runtime=method(compact(files["runtime"]),
                   "boolNrRdna2FSwinLayerRuntime::Record(")
    link=method(compact(files["runtime"]),
                "boolNrRdna2FSwinLayerRuntime::LinkInputFrom(")
    shift=method(compact(files["runtime"]),
                 "boolNrRdna2FSwinLayerRuntime::LinkInputFromShifted(")
    graph=method(compact(files["graph"]),"boolNrRdna2FSwinGraph::Record(")
    dense=method(compact(files["dense"]),"boolNrRdna2FSwinDense::Record(")
    qkv=method(compact(files["qkv"]),"boolNrRdna2FSwinQkv::Record(")
    att=method(compact(files["attention"]),
               "boolNrRdna2WindowAttention::Record(")
    repack=method(compact(files["repack"]),
                  "boolNrRdna2FSwinWindowRepack::Record(")
    for key,m in {"chain":chain,"runtime":runtime,"link":link,
                  "shift":shift,"graph":graph,"dense":dense,
                  "qkv":qkv,"attention":att,"repack":repack}.items():
        if not m:raise Drift("Missing native method: "+key)
    ordered(chain,(
        "for(std::size_ti=0u;i<layers.size();++i)",
        "if(i>0u)",
        "FSwinNeedsWindowRepack(",
        "layers[i]->LinkInputFromShifted(",
        "layers[i]->LinkInputFrom(*layers[i-1u])",
        "if(!layers[i]->Record())returnfalse",
    ),"Native chain records layers sequentially")
    ordered(runtime,(
        "graph.Record(descriptors.Sets(),plan)",
        "if(raw_c32_bound",
        "output_recorded=true",
    ),"Native layer finishes its graph before allowing successor")
    require(link,"src==dst", "Inter-layer native copy forbids same buffer")
    ordered(link,(
        "VK_ACCESS_SHADER_WRITE_BIT",
        "VK_ACCESS_TRANSFER_READ_BIT",
        "cmd.CopyBuffer(src,dst,copy);",
        "VK_ACCESS_TRANSFER_WRITE_BIT",
        "VK_ACCESS_SHADER_READ_BIT",
    ),"Native link compute -> transfer -> compute")
    require(shift,"src.buffer==dst.buffer",
            "Shifted inter-layer link forbids alias")
    require(shift,"repacker.Record(validated_set,layout,",
            "Shifted link submits repack")
    ordered(graph,(
        "dense.Record(sets.dense[i],plan.dense[i],plan.dense_storage[i])",
        "qkv.Record(sets.qkv,plan.qkv,plan.qkv_storage)",
        "attention.Record(sets.attention,plan.attention,",
        "dense.Record(sets.dense[3],plan.dense[3],",
    ),"Real FSwin pass order and terminal dense epilogue")
    for name,value in (("dense",dense),("qkv",qkv),
                       ("attention",att),("repack",repack)):
        require(value,"cmd.PipelineBarrier(",
                f"{name} emits a compute memory barrier")
        require(value,"VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,",
                f"{name} compute barrier stage")
    # A hypothetical future native pool needs these to remain true;
    # do not enable the experiment on the strength of this source guard.
def negatives(files:dict[str,str])->int:
    cases=(
      ("chain order","chain",
       "if(!layers[i]->Record())return false;",
       "if(!layers.front()->Record())return false;"),
      ("remove copy source protection","runtime",
       "if(!src||!dst||src==dst||!size)return false;",
       "if(!src||!dst||!size)return false;"),
      ("remove native copy","runtime",
       "cmd.CopyBuffer(src,dst,copy);",
       "cmd.CopyBuffer(src,src,copy);"),
      ("drop shifted alias check","runtime",
       "src.buffer==dst.buffer||",
       "src.buffer!=dst.buffer||"),
      ("omit last dense graph stage","graph",
       "if(!dense.Record(sets.dense[3],plan.dense[3],",
       "if(!dense.Record(sets.dense[2],plan.dense[3],"),
      ("remove dense pipeline barrier","dense",
       "cmd.PipelineBarrier(VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,",
       "cmd.NotPipelineBarrier(VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,"),
      ("remove QKV pipeline barrier","qkv",
       "cmd.PipelineBarrier(VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,",
       "cmd.NotPipelineBarrier(VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,"),
      ("remove shifted repack barrier","repack",
       "cmd.PipelineBarrier(VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,",
       "cmd.NotPipelineBarrier(VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,"),
    )
    for name,owner,before,after in cases:
        if before not in files[owner]:
            raise Drift(f"Mutation fixture changed: {name}")
        modified=dict(files)
        modified[owner]=modified[owner].replace(before,after)
        try:check(modified)
        except Drift:continue
        raise Drift(f"Unsafe pool source drift accepted: {name}")
    return len(cases)

def main()->None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--vendor",type=Path,required=True)
    args=parser.parse_args()
    sources={name:git(args.vendor,"show",f"HEAD:{ROOT}{path}")
             for name,path in FILES.items()}
    check(sources)
    count=negatives(sources)
    print("R09_MIN_720_FSWIN_SCRATCH_ORDER_GUARD_PASS "
          f"pinned_vendor={git(args.vendor,'rev-parse','HEAD').strip()} "
          f"source_owners={len(sources)} deliberate_rejections={count}")
    print("R09_MIN_720_CHAIN_POOL_HOST_ONLY_RUNTIME_NOT_WIRED")

if __name__=="__main__":
    try:main()
    except (Drift,subprocess.CalledProcessError) as exc:
        print(f"R09_MIN_720_FSWIN_SCRATCH_ORDER_FAIL: {exc}")
        raise SystemExit(1)
