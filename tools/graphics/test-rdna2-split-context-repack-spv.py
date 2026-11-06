#!/usr/bin/env python3
"""Compile portable 16-head context layout transpose to Vulkan 1.1."""
import argparse
from pathlib import Path
import re
import struct
import subprocess
import tempfile

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--vendor",type=Path,required=True)
    parser.add_argument("--header",type=Path)
    args=parser.parse_args()
    shader=(args.vendor/"encore-active/eden-vulkan/r09_rdna2_nr/"
            "split_context_repack_rdna2.comp")
    text=shader.read_text(encoding="utf-8")
    for forbidden in ("cooperative_matrix","shader_float8",
                      "GL_EXT_shader_explicit_arithmetic_types_float16",
                      "GL_EXT_shader_8bit_storage"):
        assert forbidden not in text,forbidden
    with tempfile.TemporaryDirectory(prefix="eden-split-repack-") as d:
        binary=Path(d)/"split_context_repack.spv"
        subprocess.run(["glslangValidator","-V","--target-env","vulkan1.1",
                        "-S","comp","-o",str(binary),str(shader)],
                       check=True,capture_output=True)
        subprocess.run(["spirv-val","--target-env","vulkan1.1",
                        str(binary)],check=True,capture_output=True)
        asm=subprocess.check_output(["spirv-dis",str(binary)],text=True)
        assert "OpExecutionMode %main LocalSize 256 1 1" in asm
        for name,binding in (("source",0),("destination",1)):
            assert re.search(rf"OpDecorate %{name} DescriptorSet 0\b",asm)
            assert re.search(rf"OpDecorate %{name} Binding {binding}\b",asm)
        for i in range(4):
            assert re.search(
                rf"OpMemberDecorate %Params {i} Offset {i*4}\b",asm)
        assert re.findall(r"OpCapability ([A-Za-z0-9_]+)",asm)==["Shader"]
        if args.header:
            raw=binary.read_bytes()
            words=struct.unpack("<"+"I"*(len(raw)//4),raw)
            lines=["// SPDX-License-Identifier: MIT","#pragma once",
                   "#include <array>","#include <cstdint>",
                   f"inline constexpr std::array<std::uint32_t, {len(words)}> RDNA2_NR_SPLIT_CONTEXT_REPACK_COMP_SPV = {{"]
            for i in range(0,len(words),8):
                lines.append("    "+", ".join(
                    f"0x{x:08x}u" for x in words[i:i+8])+",")
            lines.append("};")
            args.header.parent.mkdir(parents=True,exist_ok=True)
            args.header.write_text("\n".join(lines)+"\n",encoding="utf-8")
    print("RDNA2_SPLIT_CONTEXT_REPACK_SPIRV_ABI_PASS")

if __name__=="__main__":
    main()
