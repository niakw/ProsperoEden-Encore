#!/usr/bin/env python3
"""Compile/validate RDNA2 native Split window->decoder skip ABI."""
import argparse
import re
import struct
import subprocess
import tempfile
from pathlib import Path

def validate(shader:Path,header:Path|None)->None:
    source=shader.read_text(encoding="utf-8")
    assert "destination.words[target]=0u" in source
    for term in ("cooperative_matrix","GL_EXT_shader_16bit_storage",
                 "GL_EXT_shader_explicit_arithmetic_types_float16",
                 "shader_float8"):
        assert term not in source
    with tempfile.TemporaryDirectory(prefix="encore-split-decoder-") as directory:
        spv=Path(directory)/"skip_repack.spv"
        subprocess.run(["glslangValidator","-V","--target-env","vulkan1.1",
                        "-S","comp","-o",str(spv),str(shader)],
                       capture_output=True,check=True)
        subprocess.run(["spirv-val","--target-env","vulkan1.1",str(spv)],
                       capture_output=True,check=True)
        asm=subprocess.check_output(["spirv-dis",str(spv)],text=True)
        assert "OpExecutionMode %main LocalSize 128 1 1" in asm
        for name,binding in (("source",0),("destination",1)):
            assert re.search(rf"OpDecorate %{name} DescriptorSet 0\b",asm),name
            assert re.search(rf"OpDecorate %{name} Binding {binding}\b",asm),name
        for i in range(5):
            assert re.search(
                rf"OpMemberDecorate %Params {i} Offset {4*i}\b",asm),i
        assert re.findall(r"OpCapability ([A-Za-z0-9_]+)",asm)==["Shader"]
        if header:
            data=spv.read_bytes()
            words=struct.unpack("<"+"I"*(len(data)//4),data)
            lines=["// SPDX-License-Identifier: MIT","#pragma once",
                   "#include <array>","#include <cstdint>",
                   f"inline constexpr std::array<std::uint32_t, {len(words)}> "
                   "RDNA2_NR_SPLIT_DECODER_SKIP_REPACK_COMP_SPV = {"]
            for i in range(0,len(words),8):
                lines.append("    "+", ".join(
                    f"0x{w:08x}u" for w in words[i:i+8])+",")
            lines.append("};")
            header.parent.mkdir(parents=True,exist_ok=True)
            header.write_text("\n".join(lines)+"\n",encoding="utf-8")
        print("RDNA2_SPLIT_DECODER_SKIP_REPACK_SPIRV_ABI_PASS",
              spv.stat().st_size)

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--vendor",required=True,type=Path)
    parser.add_argument("--header",type=Path)
    args=parser.parse_args()
    validate(args.vendor/"encore-active/eden-vulkan/r09_rdna2_nr/"
             "split_decoder_skip_repack_rdna2.comp",args.header)
