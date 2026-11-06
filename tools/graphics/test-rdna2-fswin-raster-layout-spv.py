#!/usr/bin/env python3
"""Validate RDNA2 raster<->FSwin window layout shader on Vulkan 1.1."""
import argparse
import re
import struct
import subprocess
import tempfile
from pathlib import Path

def validate(shader:Path, header:Path|None)->None:
    src=shader.read_text(encoding="utf-8")
    for forbidden in ("GL_KHR_cooperative_matrix",
                      "GL_EXT_shader_8bit_storage", "shader_float8"):
        assert forbidden not in src, forbidden
    with tempfile.TemporaryDirectory(prefix="rdna2-fswin-raster-") as d:
        spv=Path(d)/"fswin_raster_layout.spv"
        subprocess.run(["glslangValidator","-V","--target-env","vulkan1.1",
                        "-S","comp","-o",str(spv),str(shader)],
                       check=True,capture_output=True)
        subprocess.run(["spirv-val","--target-env","vulkan1.1",str(spv)],
                       check=True,capture_output=True)
        asm=subprocess.check_output(["spirv-dis",str(spv)],text=True)
        assert "OpExecutionMode %main LocalSize 64 1 1" in asm
        for name,slot in (("source",0),("dest",1)):
            assert re.search(rf"OpDecorate %{name} DescriptorSet 0\b",asm),name
            assert re.search(rf"OpDecorate %{name} Binding {slot}\b",asm),name
        for n in range(6):
            assert re.search(
                rf"OpMemberDecorate %Params {n} Offset {4*n}\b",asm),n
        assert re.findall(r"OpCapability ([A-Za-z0-9_]+)",asm)==["Shader"]
        if header:
            data=spv.read_bytes()
            words=struct.unpack("<"+"I"*(len(data)//4),data)
            lines=["// SPDX-License-Identifier: MIT","#pragma once",
                   "#include <array>","#include <cstdint>",
                   f"inline constexpr std::array<std::uint32_t, {len(words)}> RDNA2_NR_FSWIN_RASTER_LAYOUT_COMP_SPV = {{"]
            for i in range(0,len(words),8):
                lines.append("    "+", ".join(f"0x{x:08x}u" for x in words[i:i+8])+",")
            lines.append("};")
            header.parent.mkdir(parents=True,exist_ok=True)
            header.write_text("\n".join(lines)+"\n")
        print("RDNA2_FSWIN_RASTER_LAYOUT_SPIRV_ABI_PASS",len(data) if header else spv.stat().st_size)

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--vendor",required=True,type=Path)
    p.add_argument("--header",type=Path)
    a=p.parse_args()
    validate(a.vendor/"encore-active/eden-vulkan/r09_rdna2_nr/fswin_raster_layout_rdna2.comp",a.header)
