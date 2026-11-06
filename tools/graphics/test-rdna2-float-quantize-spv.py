#!/usr/bin/env python3
"""RDNA2 FSwin dense shader: SPIR-V Vulkan 1.1 and ABI."""
import argparse
import re
import struct
import subprocess
import tempfile
from pathlib import Path

def validate(shader:Path,header:Path|None):
    source=shader.read_text()
    for forbidden in ("GL_KHR_cooperative_matrix","GL_EXT_float_e4m3",
                      "GL_EXT_shader_8bit_storage"):
        assert forbidden not in source,forbidden
    with tempfile.TemporaryDirectory(prefix="encore-rdna2-fswin-") as d:
        spv=Path(d)/"float_quantize.spv"
        subprocess.run(["glslangValidator","-V","--target-env","vulkan1.1",
                        "-S","comp","-o",str(spv),str(shader)],
                       check=True,capture_output=True)
        subprocess.run(["spirv-val","--target-env","vulkan1.1",str(spv)],
                       check=True,capture_output=True)
        asm=subprocess.check_output(["spirv-dis",str(spv)],text=True)
        assert "OpExecutionMode %main LocalSize 64 1 1" in asm
        for name,slot in (("input_tensor",0),("output_tensor",1)):
            assert re.search(rf"OpDecorate %{name} DescriptorSet 0\b",asm),name
            assert re.search(rf"OpDecorate %{name} Binding {slot}\b",asm),name
        for n in range(4):
            assert re.search(rf"OpMemberDecorate %Params {n} Offset {n*4}\b",asm),n
        assert re.findall(r"OpCapability ([A-Za-z0-9_]+)",asm)==["Shader"]
        if header:
            data=spv.read_bytes()
            words=struct.unpack("<"+"I"*(len(data)//4),data)
            lines=["// SPDX-License-Identifier: MIT","#pragma once",
                   "#include <array>","#include <cstdint>",
                   f"inline constexpr std::array<std::uint32_t, {len(words)}> RDNA2_NR_FLOAT_QUANTIZE_COMP_SPV = {{"]
            for i in range(0,len(words),8):
                lines.append("    "+", ".join(f"0x{x:08x}u" for x in words[i:i+8])+",")
            lines.append("};")
            header.parent.mkdir(parents=True,exist_ok=True)
            header.write_text("\n".join(lines)+"\n")
        print("RDNA2_FLOAT_QUANTIZE_SPIRV_ABI_PASS",spv.stat().st_size)
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--vendor",type=Path,required=True)
    p.add_argument("--header",type=Path)
    a=p.parse_args()
    validate(a.vendor/"encore-active/eden-vulkan/r09_rdna2_nr/float_quantize_rdna2.comp",a.header)
