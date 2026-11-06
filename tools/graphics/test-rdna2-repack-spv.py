#!/usr/bin/env python3
"""RDNA2 NR: validate tile-byte permutation SPIR-V, no FP8 storage or WMMA."""
import argparse
import re
import struct
import subprocess
import tempfile
from pathlib import Path

def validate(shader: Path, header: Path | None) -> None:
    content=shader.read_text(encoding="utf-8")
    for forbidden in ("cooperative_matrix","shader_float8","GL_EXT_shader_8bit_storage",
                      "GL_EXT_shader_explicit_arithmetic_types_int8"):
        assert forbidden not in content, forbidden
    with tempfile.TemporaryDirectory(prefix="encore-rdna2-repack-") as tmp:
        binary=Path(tmp)/"repack.spv"
        subprocess.run(["glslangValidator","-V","--target-env","vulkan1.1",
                        "-S","comp","-o",str(binary),str(shader)],
                       check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        subprocess.run(["spirv-val","--target-env","vulkan1.1",str(binary)],
                       check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        asm=subprocess.check_output(["spirv-dis",str(binary)],text=True)
        assert "OpExecutionMode %main LocalSize 64 1 1" in asm
        assert re.search(r"OpDecorate %arena Binding 0\b",asm)
        assert re.search(r"OpDecorate %arena DescriptorSet 0\b",asm)
        for i in range(6):
            assert re.search(rf"OpMemberDecorate %Push {i} Offset {4*i}\b",asm),i
        assert re.findall(r"OpCapability ([A-Za-z0-9_]+)",asm)==["Shader"]
        assert "OpTypeCooperativeMatrix" not in asm
        if header:
            data=binary.read_bytes()
            words=struct.unpack("<"+"I"*(len(data)//4),data)
            lines=[
                "// SPDX-License-Identifier: MIT",
                "// MIT adaptation from mochizuki0323/DLSSNR-AMD token layout.",
                "#pragma once",
                "#include <array>",
                "#include <cstdint>",
                f"inline constexpr std::array<std::uint32_t, {len(words)}> "
                "RDNA2_NR_REPACK_TOKENS_COMP_SPV = {",
            ]
            for j in range(0,len(words),8):
                lines.append("    "+", ".join(f"0x{x:08x}u" for x in words[j:j+8])+",")
            lines.append("};")
            header.parent.mkdir(parents=True,exist_ok=True)
            header.write_text(chr(10).join(lines)+chr(10))
        print("RDNA2_TOKEN_REPACK_SPIRV_ABI_PASS",f"shader_bytes={binary.stat().st_size}")

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--vendor",type=Path,required=True)
    parser.add_argument("--header",type=Path)
    args=parser.parse_args()
    shader=args.vendor/"encore-active/eden-vulkan/r09_rdna2_nr/repack_tokens_rdna2.comp"
    validate(shader,args.header)

if __name__=="__main__":
    main()
