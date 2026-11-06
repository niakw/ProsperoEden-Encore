#!/usr/bin/env python3
"""Compile and ABI-validate RDNA2 Split-Swin FP16-first ProjPool SPIR-V."""
import argparse
from pathlib import Path
import re
import struct
import subprocess
import tempfile

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--vendor",type=Path,required=True)
    ap.add_argument("--header",type=Path)
    a=ap.parse_args()
    source=(a.vendor/"encore-active/eden-vulkan/r09_rdna2_nr/"
            "split_projection_pool_rdna2.comp")
    contents=source.read_text(encoding="utf-8")
    for forbidden in ("cooperative_matrix","GL_EXT_shader_8bit_storage",
                      "GL_EXT_shader_explicit_arithmetic_types_float16",
                      "GL_KHR_shader_subgroup"):
        assert forbidden not in contents, forbidden
    with tempfile.TemporaryDirectory(prefix="eden-split-pool-") as d:
        spv=Path(d)/"split_projection_pool.spv"
        subprocess.run(["glslangValidator","-V","--target-env","vulkan1.1",
                        "-S","comp","-o",str(spv),str(source)],
                       capture_output=True,check=True)
        subprocess.run(["spirv-val","--target-env","vulkan1.1",str(spv)],
                       capture_output=True,check=True)
        asm=subprocess.check_output(["spirv-dis",str(spv)],text=True)
        assert "OpExecutionMode %main LocalSize 128 1 1" in asm
        for name,slot in (("source",0),("residual",1),
                          ("gains",2),("pooled",3)):
            assert re.search(rf"OpDecorate %{name} DescriptorSet 0\b",asm),name
            assert re.search(rf"OpDecorate %{name} Binding {slot}\b",asm),name
        for i in range(9):
            assert re.search(
                rf"OpMemberDecorate %Params {i} Offset {i*4}\b",asm),i
        assert re.findall(r"OpCapability ([A-Za-z0-9_]+)",asm)==["Shader"]
        if a.header:
            raw=spv.read_bytes()
            words=struct.unpack("<"+"I"*(len(raw)//4),raw)
            lines=["// SPDX-License-Identifier: MIT","#pragma once",
                   "#include <array>","#include <cstdint>",
                   f"inline constexpr std::array<std::uint32_t, {len(words)}> RDNA2_NR_SPLIT_PROJECTION_POOL_COMP_SPV = {{"]
            for i in range(0,len(words),8):
                lines.append("    "+", ".join(
                    f"0x{x:08x}u" for x in words[i:i+8])+",")
            lines.append("};")
            a.header.parent.mkdir(parents=True,exist_ok=True)
            a.header.write_text("\n".join(lines)+"\n",encoding="utf-8")
        print("RDNA2_SPLIT_PROJECTION_POOL_SPIRV_ABI_PASS",len(spv.read_bytes()))

if __name__=="__main__":
    main()
