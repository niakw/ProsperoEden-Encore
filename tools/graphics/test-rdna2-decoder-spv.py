#!/usr/bin/env python3
"""Vulkan 1.1 RDNA2 decoder upsample: compile, validate ABI, create C++ header."""
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
                      "GL_EXT_shader_16bit_storage"):
        assert forbidden not in source, forbidden
    with tempfile.TemporaryDirectory(prefix="encore-rdna2-decoder-") as d:
        spv=Path(d)/"decoder_upsample.spv"
        subprocess.run(["glslangValidator", "-V", "--target-env", "vulkan1.1",
                        "-S", "comp", "-o", str(spv), str(shader)],
                       check=True, capture_output=True)
        subprocess.run(["spirv-val", "--target-env", "vulkan1.1", str(spv)],
                       check=True, capture_output=True)
        asm=subprocess.check_output(["spirv-dis", str(spv)], text=True)
        assert "OpExecutionMode %main LocalSize 64 1 1" in asm
        for name, binding in (("projection",0),("activations",1),("gains",2)):
            assert re.search(rf"OpDecorate %{name} DescriptorSet 0\b", asm), name
            assert re.search(rf"OpDecorate %{name} Binding {binding}\b", asm), name
        for index in range(7):
            assert re.search(rf"OpMemberDecorate %Params {index} Offset {index*4}\b", asm), index
        assert re.findall(r"OpCapability ([A-Za-z0-9_]+)", asm)==["Shader"]
        assert "OpTypeCooperativeMatrix" not in asm
        if header:
            raw=spv.read_bytes()
            words=struct.unpack("<"+"I"*(len(raw)//4),raw)
            lines=["// SPDX-License-Identifier: MIT",
                   "// RDNA2 decoder upsample from MIT DLSSNR-AMD architecture.",
                   "#pragma once","#include <array>","#include <cstdint>",
                   f"inline constexpr std::array<std::uint32_t, {len(words)}> RDNA2_NR_DECODER_UPSAMPLE_COMP_SPV = {{"]
            for i in range(0,len(words),8):
                lines.append("    "+", ".join(f"0x{x:08x}u" for x in words[i:i+8])+",")
            lines.append("};")
            header.parent.mkdir(parents=True,exist_ok=True)
            header.write_text("\n".join(lines)+"\n",encoding="utf-8")
        print("RDNA2_DECODER_UPSAMPLE_SPIRV_ABI_PASS", spv.stat().st_size)

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--vendor",type=Path,required=True)
    p.add_argument("--header",type=Path)
    a=p.parse_args()
    validate(a.vendor/"encore-active/eden-vulkan/r09_rdna2_nr/decoder_upsample_rdna2.comp",
             a.header)
