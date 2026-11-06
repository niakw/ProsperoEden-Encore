#!/usr/bin/env python3
"""Compile portable RDNA2 1.1 ViT activation/residual SPV and check ABI."""
import argparse
from pathlib import Path
import re
import struct
import subprocess
import tempfile

def compile_one(root: Path, name: str, slots: tuple[str,...],
                count: int, output: Path | None) -> None:
    source=root/f"r09_rdna2_nr/{name}_rdna2.comp"
    contents=source.read_text(encoding="utf-8")
    for ext in ("GL_EXT_shader_8bit_storage","cooperative_matrix",
                "GL_EXT_shader_explicit_arithmetic_types_float16",
                "GL_KHR_shader_subgroup"):
        assert ext not in contents, ext
    with tempfile.TemporaryDirectory(prefix=f"eden-{name}-") as d:
        spv=Path(d)/f"{name}.spv"
        subprocess.run(["glslangValidator","-V","--target-env","vulkan1.1",
                        "-S","comp","-o",str(spv),str(source)],
                       check=True,capture_output=True)
        subprocess.run(["spirv-val","--target-env","vulkan1.1",
                        str(spv)],check=True,capture_output=True)
        asm=subprocess.check_output(["spirv-dis",str(spv)],text=True)
        assert "OpExecutionMode %main LocalSize 128 1 1" in asm
        for i,var in enumerate(slots):
            assert re.search(rf"OpDecorate %{var} DescriptorSet 0\b",asm),var
            assert re.search(rf"OpDecorate %{var} Binding {i}\b",asm),var
        for i in range(count):
            assert re.search(
                rf"OpMemberDecorate %Params {i} Offset {i*4}\b",asm),i
        assert re.findall(r"OpCapability ([A-Za-z0-9_]+)",asm)==["Shader"]
        if output:
            raw=spv.read_bytes()
            words=struct.unpack("<"+"I"*(len(raw)//4),raw)
            symbol="RDNA2_NR_"+name.upper()+"_COMP_SPV"
            lines=["// SPDX-License-Identifier: MIT","#pragma once",
                   "#include <array>","#include <cstdint>",
                   f"inline constexpr std::array<std::uint32_t, {len(words)}> {symbol} = {{"]
            for i in range(0,len(words),8):
                lines.append("    "+", ".join(
                    f"0x{x:08x}u" for x in words[i:i+8])+",")
            lines.append("};")
            output.mkdir(parents=True,exist_ok=True)
            (output/f"rdna2_nr_{name}_comp_spv.h").write_text(
                "\n".join(lines)+"\n",encoding="utf-8")
    print(f"RDNA2_{name.upper()}_SPIRV_ABI_PASS")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--vendor",type=Path,required=True)
    p.add_argument("--output",type=Path)
    a=p.parse_args()
    root=a.vendor/"encore-active/eden-vulkan"
    compile_one(root,"vit_activation",("source","output_tensor"),4,a.output)
    compile_one(root,"vit_residual",
                ("source","residual","gains","output_tensor"),6,a.output)
if __name__=="__main__":
    main()
