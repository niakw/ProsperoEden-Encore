#!/usr/bin/env python3
"""Validate native FP16 2x2 C32 preblock pooling Vulkan 1.1 ABI."""
import argparse
import re
import struct
import subprocess
import tempfile
from pathlib import Path
def run(shader:Path,header:Path|None)->None:
    src=shader.read_text(encoding="utf-8")
    assert "layout(local_size_x=8" in src
    for unsupported in ("cooperative_matrix","shader_float8",
                        "GL_EXT_shader_explicit_arithmetic_types_float16"):
        assert unsupported not in src
    with tempfile.TemporaryDirectory(prefix="r09-prepool-") as temp:
        spv=Path(temp)/"preblock_pool.spv"
        subprocess.run(["glslangValidator","-V","--target-env","vulkan1.1",
                        "-S","comp","-o",str(spv),str(shader)],
                       check=True,capture_output=True)
        subprocess.run(["spirv-val","--target-env","vulkan1.1",str(spv)],
                       check=True,capture_output=True)
        asm=subprocess.check_output(["spirv-dis",str(spv)],text=True)
        assert "OpExecutionMode %main LocalSize 8 8 1" in asm
        for name,binding in (("raw_full",0),("pooled",1)):
            assert re.search(rf"OpDecorate %{name} DescriptorSet 0\b",asm),name
            assert re.search(rf"OpDecorate %{name} Binding {binding}\b",asm),name
        for i in range(2):
            assert re.search(rf"OpMemberDecorate %Params {i} Offset {4*i}\b",asm),i
        assert re.findall(r"OpCapability ([A-Za-z0-9_]+)",asm)==["Shader"]
        if header:
            raw=spv.read_bytes()
            words=struct.unpack("<"+"I"*(len(raw)//4),raw)
            lines=["// SPDX-License-Identifier: MIT","#pragma once",
                   "#include <array>","#include <cstdint>",
                   f"inline constexpr std::array<std::uint32_t, {len(words)}> "
                   "RDNA2_NR_PREBLOCK_POOL_COMP_SPV = {"]
            for j in range(0,len(words),8):
                lines.append("    "+", ".join(
                    f"0x{w:08x}u" for w in words[j:j+8])+",")
            lines.append("};")
            header.parent.mkdir(parents=True,exist_ok=True)
            header.write_text("\n".join(lines)+"\n",encoding="utf-8")
        print("R09_PREBLOCK_POOL_SPIRV_ABI_PASS",spv.stat().st_size)
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--vendor",required=True,type=Path)
    p.add_argument("--header",type=Path)
    a=p.parse_args()
    run(a.vendor/"encore-active/eden-vulkan/r09_rdna2_nr/"
        "preblock_pool_rdna2.comp",a.header)
