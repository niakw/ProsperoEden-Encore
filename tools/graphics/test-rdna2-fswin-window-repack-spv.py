#!/usr/bin/env python3
"""Validate RDNA2 FSwin shifted-window Vulkan 1.1 shader and ABI."""
import argparse
import re
import struct
import subprocess
import tempfile
from pathlib import Path
def validate(shader:Path,header:Path|None):
    text=shader.read_text(encoding="utf-8")
    for forbidden in ("cooperative_matrix","shader_float8",
                      "GL_EXT_shader_8bit_storage"):
        assert forbidden not in text,forbidden
    with tempfile.TemporaryDirectory(prefix="encore-rdna2-window-") as tmp:
        spv=Path(tmp)/"fswin_window_repack.spv"
        subprocess.run(["glslangValidator","-V","--target-env","vulkan1.1",
                        "-S","comp","-o",str(spv),str(shader)],
                       check=True,capture_output=True)
        subprocess.run(["spirv-val","--target-env","vulkan1.1",str(spv)],
                       check=True,capture_output=True)
        asm=subprocess.check_output(["spirv-dis",str(spv)],text=True)
        assert "OpExecutionMode %main LocalSize 64 1 1" in asm
        for name,slot in (("input_words",0),("output_words",1)):
            assert re.search(rf"OpDecorate %{name} DescriptorSet 0\b",asm)
            assert re.search(rf"OpDecorate %{name} Binding {slot}\b",asm)
        for i in range(7):
            assert re.search(
                rf"OpMemberDecorate %Params {i} Offset {i*4}\b",asm)
        assert re.findall(r"OpCapability ([A-Za-z0-9_]+)",asm)==["Shader"]
        if header:
            raw=spv.read_bytes()
            words=struct.unpack("<"+"I"*(len(raw)//4),raw)
            lines=["// SPDX-License-Identifier: MIT","#pragma once",
                   "#include <array>","#include <cstdint>",
                   f"inline constexpr std::array<std::uint32_t, {len(words)}> RDNA2_NR_FSWIN_WINDOW_REPACK_COMP_SPV = {{"]
            for start in range(0,len(words),8):
                lines.append("    "+", ".join(
                    f"0x{value:08x}u" for value in words[start:start+8])+",")
            lines.append("};")
            header.parent.mkdir(parents=True,exist_ok=True)
            header.write_text("\n".join(lines)+"\n",encoding="utf-8")
        print("RDNA2_FSWIN_WINDOW_REPACK_SPIRV_PASS",spv.stat().st_size)
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--vendor",type=Path,required=True)
    p.add_argument("--header",type=Path)
    a=p.parse_args()
    validate(a.vendor/"encore-active/eden-vulkan/r09_rdna2_nr/fswin_window_repack_rdna2.comp",a.header)
