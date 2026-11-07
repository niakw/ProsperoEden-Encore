#!/usr/bin/env python3
"""Build and verify the Vulkan 1.1 RDNA2 no-history RGB compositor ABI."""
import argparse
import re
import struct
import subprocess
import tempfile
from pathlib import Path
def check(shader:Path,header:Path|None)->None:
    src=shader.read_text(encoding="utf-8")
    for required in ("unpackHalf2x16","delta*0.25",
                     "pc.intensity","finite3","features.packed"):
        assert required in src,required
    for forbidden in ("GL_EXT_shader_explicit_arithmetic_types_float16",
                      "cooperative_matrix","shader_float8","VK_NV"):
        assert forbidden not in src,forbidden
    with tempfile.TemporaryDirectory(prefix="r09-nohistory-compose-") as tmp:
        spv=Path(tmp)/"nohistory_compose.spv"
        subprocess.run(["glslangValidator","-V","--target-env","vulkan1.1",
                        "-S","comp","-o",str(spv),str(shader)],
                       check=True,capture_output=True)
        subprocess.run(["spirv-val","--target-env","vulkan1.1",str(spv)],
                       check=True,capture_output=True)
        asm=subprocess.check_output(["spirv-dis",str(spv)],text=True)
        assert "OpExecutionMode %main LocalSize 8 8 1" in asm
        for name,b in (("proxy",0),("features",1),("output_color",2)):
            assert re.search(rf"OpDecorate %{name} DescriptorSet 0\\b",asm),name
            assert re.search(rf"OpDecorate %{name} Binding {b}\\b",asm),name
        for i in range(4):
            assert re.search(rf"OpMemberDecorate %Params {i} Offset {i*4}\\b",asm),i
        assert re.findall(r"OpCapability ([A-Za-z0-9_]+)",asm)==["Shader"]
        if header:
            data=spv.read_bytes()
            words=struct.unpack("<"+"I"*(len(data)//4),data)
            lines=["// SPDX-License-Identifier: MIT","#pragma once",
                   "#include <array>","#include <cstdint>",
                   f"inline constexpr std::array<std::uint32_t, {len(words)}> "
                   "RDNA2_NR_NOHISTORY_COMPOSE_COMP_SPV = {"]
            for i in range(0,len(words),8):
                lines.append("    "+", ".join(
                    f"0x{x:08x}u" for x in words[i:i+8])+",")
            lines.append("};")
            header.parent.mkdir(parents=True,exist_ok=True)
            header.write_text("\n".join(lines)+"\n",encoding="utf-8")
        print("R09_NOHISTORY_COMPOSE_SPIRV_ABI_PASS",spv.stat().st_size)
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--vendor",required=True,type=Path)
    p.add_argument("--header",type=Path)
    a=p.parse_args()
    check(a.vendor/"encore-active/eden-vulkan/r09_rdna2_nr/"
          "nohistory_compose_rdna2.comp",a.header)
