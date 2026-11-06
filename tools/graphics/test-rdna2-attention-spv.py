#!/usr/bin/env python3
"""RDNA2 unfused 64-token attention: Vulkan 1.1 ABI + no WMMA check."""
import argparse
import re
import struct
import subprocess
import tempfile
from pathlib import Path

def validate(shader: Path, header: Path | None) -> None:
    source=shader.read_text(encoding="utf-8")
    for forbidden in ("cooperative_matrix", "shader_float8",
                      "GL_EXT_shader_explicit_arithmetic_types_float16",
                      "GL_EXT_shader_8bit_storage", "GL_KHR_shader_subgroup"):
        assert forbidden not in source, forbidden
    with tempfile.TemporaryDirectory(prefix="encore-rdna2-attention-") as d:
        spv=Path(d)/"window_attention.spv"
        subprocess.run(["glslangValidator","-V","--target-env","vulkan1.1",
                        "-S","comp","-o",str(spv),str(shader)],
                       check=True,capture_output=True)
        subprocess.run(["spirv-val","--target-env","vulkan1.1",str(spv)],
                       check=True,capture_output=True)
        asm=subprocess.check_output(["spirv-dis",str(spv)],text=True)
        assert "OpExecutionMode %main LocalSize 64 1 1" in asm
        for name,slot in (("q_data",0),("k_data",1),("v_data",2),
                          ("bias",3),("result",4)):
            assert re.search(rf"OpDecorate %{name} DescriptorSet 0\b",asm),name
            assert re.search(rf"OpDecorate %{name} Binding {slot}\b",asm),name
        for n in range(7):
            assert re.search(rf"OpMemberDecorate %Params {n} Offset {n*4}\b",asm),n
        assert re.findall(r"OpCapability ([A-Za-z0-9_]+)",asm)==["Shader"]
        assert "OpTypeCooperativeMatrix" not in asm
        if header:
            raw=spv.read_bytes()
            words=struct.unpack("<"+"I"*(len(raw)//4),raw)
            lines=["// SPDX-License-Identifier: MIT",
                   "// Unfused RDNA2 attention adapted from MIT DLSSNR-AMD.",
                   "#pragma once","#include <array>","#include <cstdint>",
                   f"inline constexpr std::array<std::uint32_t, {len(words)}> RDNA2_NR_WINDOW_ATTENTION_COMP_SPV = {{"]
            for i in range(0,len(words),8):
                lines.append("    "+", ".join(f"0x{x:08x}u" for x in words[i:i+8])+",")
            lines.append("};")
            header.parent.mkdir(parents=True,exist_ok=True)
            header.write_text("\n".join(lines)+"\n",encoding="utf-8")
        print("RDNA2_WINDOW_ATTENTION_SPIRV_ABI_PASS",spv.stat().st_size)

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--vendor",type=Path,required=True)
    p.add_argument("--header",type=Path)
    a=p.parse_args()
    validate(a.vendor/"encore-active/eden-vulkan/r09_rdna2_nr/window_attention_rdna2.comp",
             a.header)
