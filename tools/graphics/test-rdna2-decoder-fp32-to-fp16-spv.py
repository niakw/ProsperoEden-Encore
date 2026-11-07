#!/usr/bin/env python3
"""RDNA2 native decoder FP32->FP16 Vulkan 1.1 shader/ABI guard."""
import argparse
import re
import struct
import subprocess
import tempfile
from pathlib import Path

def run(shader:Path,header:Path|None)->None:
    source=shader.read_text(encoding="utf-8")
    assert "packHalf2x16" in source
    for forbidden in (
        "GL_EXT_shader_explicit_arithmetic_types_float16",
        "GL_EXT_shader_16bit_storage","cooperative_matrix","shader_float8"):
        assert forbidden not in source
    with tempfile.TemporaryDirectory(prefix="encore-r09-decoder-half-") as tmp:
        spv=Path(tmp)/"decoder_fp32_to_fp16.spv"
        subprocess.run(["glslangValidator","-V","--target-env","vulkan1.1",
                        "-S","comp","-o",str(spv),str(shader)],
                       check=True,capture_output=True)
        subprocess.run(["spirv-val","--target-env","vulkan1.1",str(spv)],
                       check=True,capture_output=True)
        assembly=subprocess.check_output(["spirv-dis",str(spv)],text=True)
        assert "OpExecutionMode %main LocalSize 128 1 1" in assembly
        for name,binding in (("source",0),("destination",1)):
            assert re.search(rf"OpDecorate %{name} DescriptorSet 0\b",assembly),name
            assert re.search(rf"OpDecorate %{name} Binding {binding}\b",assembly),name
        for j in range(3):
            assert re.search(rf"OpMemberDecorate %Params {j} Offset {j*4}\b",
                             assembly),j
        assert re.findall(r"OpCapability ([A-Za-z0-9_]+)",assembly)==["Shader"]
        if header:
            data=spv.read_bytes()
            words=struct.unpack("<"+"I"*(len(data)//4),data)
            lines=["// SPDX-License-Identifier: MIT","#pragma once",
                   "#include <array>","#include <cstdint>",
                   f"inline constexpr std::array<std::uint32_t, {len(words)}> "
                   "RDNA2_NR_DECODER_FP32_TO_FP16_COMP_SPV = {"]
            for i in range(0,len(words),8):
                lines.append("    "+", ".join(
                    f"0x{w:08x}u" for w in words[i:i+8])+",")
            lines.append("};")
            header.parent.mkdir(parents=True,exist_ok=True)
            header.write_text("\n".join(lines)+"\n",encoding="utf-8")
        print("RDNA2_NATIVE_DECODER_FP32_HALF_SPIRV_ABI_PASS",
              spv.stat().st_size)

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--vendor",type=Path,required=True)
    p.add_argument("--header",type=Path)
    args=p.parse_args()
    run(args.vendor/"encore-active/eden-vulkan/r09_rdna2_nr/"
        "decoder_fp32_to_fp16_rdna2.comp",args.header)
