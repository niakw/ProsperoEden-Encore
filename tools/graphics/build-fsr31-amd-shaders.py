#!/usr/bin/env python3
"""Compile AMD FidelityFX FSR 3.1.4 compute passes to validated SPIR-V.

Inputs: unmodified MIT-licensed GPU shaders/headers vendored in
vendor/encore-active/amd-fsr31 (tag v1.1.4, AMD commit c6efa6bf...).
Host tool only. Vulkan backend dispatch/source integration is separate.
"""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
VARIANTS = (
    ("prepare_inputs","prepare_inputs",False,False),
    ("luma_pyramid","luma_pyramid",False,False),
    ("luma_pyramid_nowave","luma_pyramid",True,False),
    ("shading_change_pyramid","shading_change_pyramid",False,False),
    ("shading_change_pyramid_nowave","shading_change_pyramid",True,False),
    ("shading_change","shading_change",False,False),
    ("prepare_reactivity","prepare_reactivity",False,False),
    ("luma_instability","luma_instability",False,False),
    ("accumulate","accumulate",False,False),
    ("accumulate_sharpen","accumulate",False,True),
    ("rcas","rcas",False,False),
)
FLAGS = (
    "FFX_GPU=1","FFX_GLSL=1",
    "FFX_FSR3UPSCALER_OPTION_UPSAMPLE_SAMPLERS_USE_DATA_HALF=0",
    "FFX_FSR3UPSCALER_OPTION_ACCUMULATE_SAMPLERS_USE_DATA_HALF=0",
    "FFX_FSR3UPSCALER_OPTION_REPROJECT_SAMPLERS_USE_DATA_HALF=1",
    "FFX_FSR3UPSCALER_OPTION_POSTPROCESSLOCKSTATUS_SAMPLERS_USE_DATA_HALF=0",
    "FFX_FSR3UPSCALER_OPTION_UPSAMPLE_USE_LANCZOS_TYPE=2",
    "FFX_FSR3UPSCALER_OPTION_REPROJECT_USE_LANCZOS_TYPE=0",
    "FFX_FSR3UPSCALER_OPTION_HDR_COLOR_INPUT=1",
    "FFX_FSR3UPSCALER_OPTION_LOW_RESOLUTION_MOTION_VECTORS=1",
    "FFX_FSR3UPSCALER_OPTION_JITTERED_MOTION_VECTORS=0",
    "FFX_FSR3UPSCALER_OPTION_INVERTED_DEPTH=1",
)

def build_one(args):
    name, base, no_wave, sharpen, gpu, passes, glslang, validator, out, keep_binary = args
    source=passes/("ffx_fsr3upscaler_"+base+"_pass.glsl")
    if not source.is_file():
        raise FileNotFoundError(source)
    with tempfile.TemporaryDirectory(prefix="eden-fsr31-") as temp:
        binary=Path(temp)/(name+".spv")
        command=[glslang,"-V","--quiet","-S","comp","--target-env","spirv1.3",
                 "-I"+str(gpu), "-I"+str(gpu/"fsr3upscaler")]
        command.extend("-D"+value for value in FLAGS)
        if no_wave:command.append("-DFFX_SPD_NO_WAVE_OPERATIONS=1")
        command.append("-DFFX_FSR3UPSCALER_OPTION_APPLY_SHARPENING="+("1" if sharpen else "0"))
        command.extend(["-o",str(binary),str(source)])
        subprocess.run(command,check=True,capture_output=True,text=True)
        subprocess.run([validator,"--target-env","spv1.3",str(binary)],
                       check=True,capture_output=True,text=True)
        data=binary.read_bytes()
        if len(data)%4!=0 or data[:4]!=b"\x03\x02\x23\x07":
            raise ValueError("Not a valid little-endian SPIR-V module")
        words=struct.unpack("<"+str(len(data)//4)+"I",data)
        variable="FSR3_UPSCALER_"+name.upper()+"_COMP_SPV"
        header=out/("fsr3_upscaler_"+name+"_comp_spv.h")
        body=(f"// AMD FidelityFX SDK v1.1.4 FSR3.1.4 -- generated, no edits\n"
              f"// SPDX-License-Identifier: MIT\n#pragma once\n#include <cstdint>\n"
              f"inline constexpr std::uint32_t {variable}[] = {{\n")
        for i in range(0,len(words),8):
            body+="    "+", ".join(f"0x{word:08x}" for word in words[i:i+8])+",\n"
        body+="};\n"
        header.write_text(body,encoding="utf-8")
        if keep_binary:shutil.copyfile(binary,out/("fsr3_upscaler_"+name+".spv"))
        return {"pass":name,"bytes":len(data),"sha256":hashlib.sha256(data).hexdigest()}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--vendor",type=Path,
                        default=ROOT/"vendor"/"encore-active"/"amd-fsr31")
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--keep-spv",action="store_true")
    parser.add_argument("--jobs",type=int,default=4)
    args=parser.parse_args()
    gpu=args.vendor/"include/FidelityFX/gpu"
    passes=args.vendor/"shaders/fsr3upscaler"
    if not (args.vendor/"LICENSE.txt").is_file() or not (gpu/"ffx_core.h").is_file():
        parser.error("Missing pinned AMD FSR3.1.4 subset and MIT license in vendor")
    glslang=shutil.which("glslangValidator")
    validator=shutil.which("spirv-val")
    if not glslang or not validator:
        parser.error("Host glslangValidator and spirv-val required")
    args.output.mkdir(parents=True,exist_ok=True)
    work=[(*item,gpu,passes,glslang,validator,args.output,args.keep_spv)
          for item in VARIANTS]
    with ThreadPoolExecutor(max_workers=max(1,min(4,args.jobs))) as pool:
        results=list(pool.map(build_one,work))
    print(json.dumps(results,indent=2))
    print("AMD_FSR31_11_VALID_SPIRV_PASSES")
if __name__=="__main__":
    main()
