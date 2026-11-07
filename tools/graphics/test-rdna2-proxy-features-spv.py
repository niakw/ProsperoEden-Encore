#!/usr/bin/env python3
"""Verify no-history FP16[16] proxy feature shader on Vulkan 1.1 RDNA2."""
import argparse
import re
import struct
import subprocess
import tempfile
from pathlib import Path
def check(shader:Path,header:Path|None)->None:
    source=shader.read_text(encoding="utf-8")
    for required in ("packHalf2x16","0x243f6a88u","0x108ef2d9u",
                     "pc.valid_width","pc.valid_height","pc.seed",
                     "pc.auto_mask>0.0","lanes[16]"):
        assert required in source,required
    for forbidden in (
        "VK_NV","cooperative_matrix","GL_EXT_shader_16bit_storage",
        "GL_EXT_shader_explicit_arithmetic_types_float16","shader_float8"):
        assert forbidden not in source,forbidden
    with tempfile.TemporaryDirectory(prefix="encore-r09-proxy-lanes-") as d:
        spv=Path(d)/"proxy_features.spv"
        subprocess.run(["glslangValidator","-V","--target-env","vulkan1.1",
                        "-S","comp","-o",str(spv),str(shader)],
                       capture_output=True,check=True)
        subprocess.run(["spirv-val","--target-env","vulkan1.1",str(spv)],
                       capture_output=True,check=True)
        asm=subprocess.check_output(["spirv-dis",str(spv)],text=True)
        assert "OpExecutionMode %main LocalSize 8 8 1" in asm
        for name,binding in (("source",0),("output_lanes",1)):
            assert re.search(
                rf"OpDecorate %{name} DescriptorSet 0\b",asm),name
            assert re.search(
                rf"OpDecorate %{name} Binding {binding}\b",asm),name
        for i in range(12):
            assert re.search(
                rf"OpMemberDecorate %Params {i} Offset {i*4}\b",asm),i
        assert re.findall(r"OpCapability ([A-Za-z0-9_]+)",asm)==["Shader"]
        if header:
            data=spv.read_bytes()
            words=struct.unpack("<"+"I"*(len(data)//4),data)
            lines=["// SPDX-License-Identifier: MIT","#pragma once",
                   "#include <array>","#include <cstdint>",
                   f"inline constexpr std::array<std::uint32_t, {len(words)}> "
                   "RDNA2_NR_PROXY_FEATURES_COMP_SPV = {"]
            for i in range(0,len(words),8):
                lines.append("    "+", ".join(
                    f"0x{w:08x}u" for w in words[i:i+8])+",")
            lines.append("};")
            header.parent.mkdir(parents=True,exist_ok=True)
            header.write_text("\n".join(lines)+"\n",encoding="utf-8")
        print("R09_PROXY_FEATURES_SPIRV_ABI_PASS",spv.stat().st_size)
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--vendor",required=True,type=Path)
    p.add_argument("--header",type=Path)
    opts=p.parse_args()
    check(opts.vendor/"encore-active/eden-vulkan/r09_rdna2_nr/"
          "proxy_features_rdna2.comp",opts.header)
