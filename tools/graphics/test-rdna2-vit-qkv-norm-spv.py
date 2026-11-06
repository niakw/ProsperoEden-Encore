#!/usr/bin/env python3
"""Validate Vulkan 1.1 FP32->FP8 ViT QKV normalized producer ABI."""
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
            "vit_qkv_norm_rdna2.comp")
    source=shader.read_text(encoding="utf-8")
    for forbidden in ("GL_EXT_shader_explicit_arithmetic_types_float16",
                      "GL_EXT_shader_8bit_storage",
                      "GL_KHR_shader_subgroup","cooperative_matrix"):
        assert forbidden not in source, forbidden
    with tempfile.TemporaryDirectory(prefix="eden-rdna2-vit-qkv-") as d:
        binary=Path(d)/"vit_qkv_norm.spv"
        subprocess.run(["glslangValidator","-V","--target-env","vulkan1.1",
                        "-S","comp","-o",str(binary),str(shader)],
                       check=True,capture_output=True)
        subprocess.run(["spirv-val","--target-env","vulkan1.1",
                        str(binary)],check=True,capture_output=True)
        asm=subprocess.check_output(["spirv-dis",str(binary)],text=True)
        assert "OpExecutionMode %main LocalSize 8 1 1" in asm
        for name,slot in (("input_f32",0),("temperatures",1),
                          ("query_out",2),("key_out",3),("value_out",4)):
            assert re.search(rf"OpDecorate %{name} DescriptorSet 0\b",asm),name
            assert re.search(rf"OpDecorate %{name} Binding {slot}\b",asm),name
        for member in range(6):
            assert re.search(
                rf"OpMemberDecorate %Params {member} Offset {member*4}\b",
                asm),member
        assert re.findall(r"OpCapability ([A-Za-z0-9_]+)",asm)==["Shader"]
        if args.header:
            words=struct.unpack("<"+"I"*(binary.stat().st_size//4),
                                binary.read_bytes())
            lines=["// SPDX-License-Identifier: MIT",
                   "// Portable RDNA2 ViT QKV norm, no vendor FP8 extension.",
                   "#pragma once","#include <array>","#include <cstdint>",
                   f"inline constexpr std::array<std::uint32_t, {len(words)}> RDNA2_NR_VIT_QKV_NORM_COMP_SPV = {{"]
            for i in range(0,len(words),8):
                lines.append("    "+", ".join(
                    f"0x{v:08x}u" for v in words[i:i+8])+",")
            lines.append("};")
            args.header.parent.mkdir(parents=True,exist_ok=True)
            args.header.write_text("\n".join(lines)+"\n",encoding="utf-8")
        print("RDNA2_VIT_QKV_NORM_SPIRV_ABI_PASS",binary.stat().st_size)

if __name__=="__main__":
    main()
