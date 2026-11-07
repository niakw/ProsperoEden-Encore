#!/usr/bin/env python3
"""Validate native tiled-C1024->linear-C1024 Vulkan 1.1 shader ABI."""
import argparse
import re
import struct
import subprocess
import tempfile
from pathlib import Path

def validate(shader:Path,header:Path|None)->None:
    source=shader.read_text(encoding="utf-8")
    assert "tile*256u+channel_word" in source
    for forbidden in (
        "cooperative_matrix","shader_float8",
        "GL_EXT_shader_explicit_arithmetic_types_float16",
        "GL_EXT_shader_16bit_storage"):
        assert forbidden not in source
    with tempfile.TemporaryDirectory(prefix="encore-nr-tile-linear-") as tmp:
        spv=Path(tmp)/"decoder_tile_linear.spv"
        subprocess.run(["glslangValidator","-V","--target-env","vulkan1.1",
                        "-S","comp","-o",str(spv),str(shader)],
                       check=True,capture_output=True)
        subprocess.run(["spirv-val","--target-env","vulkan1.1",str(spv)],
                       check=True,capture_output=True)
        asm=subprocess.check_output(["spirv-dis",str(spv)],text=True)
        assert "OpExecutionMode %main LocalSize 128 1 1" in asm
        for name,binding in (("tiled",0),("linear",1)):
            assert re.search(
                rf"OpDecorate %{name} DescriptorSet 0\b",asm),name
            assert re.search(
                rf"OpDecorate %{name} Binding {binding}\b",asm),name
        for i in range(2):
            assert re.search(
                rf"OpMemberDecorate %Params {i} Offset {i*4}\b",asm),i
        assert re.findall(r"OpCapability ([A-Za-z0-9_]+)",asm)==["Shader"]
        if header:
            raw=spv.read_bytes()
            words=struct.unpack("<"+"I"*(len(raw)//4),raw)
            lines=["// SPDX-License-Identifier: MIT","#pragma once",
                   "#include <array>","#include <cstdint>",
                   f"inline constexpr std::array<std::uint32_t, {len(words)}> "
                   "RDNA2_NR_DECODER_TILE_LINEAR_COMP_SPV = {"]
            for j in range(0,len(words),8):
                lines.append("    "+", ".join(
                    f"0x{x:08x}u" for x in words[j:j+8])+",")
            lines.append("};")
            header.parent.mkdir(parents=True,exist_ok=True)
            header.write_text("\n".join(lines)+"\n",encoding="utf-8")
        print("RDNA2_DECODER_TILE_LINEAR_SPIRV_ABI_PASS",
              spv.stat().st_size)

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--vendor",required=True,type=Path)
    p.add_argument("--header",type=Path)
    a=p.parse_args()
    validate(a.vendor/"encore-active/eden-vulkan/r09_rdna2_nr/"
             "decoder_tile_linear_rdna2.comp",a.header)
