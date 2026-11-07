#!/usr/bin/env python3
"""Validate real Vulkan sampled-image -> native proxy compute shader ABI."""
import argparse
import re
import struct
import subprocess
import tempfile
from pathlib import Path
def check(shader:Path,header:Path|None)->None:
    src=shader.read_text(encoding="utf-8")
    for required in ("sampler2D source_texture","texelFetch",
                     "ivec2(native.y,native.x)","pc.paper_white",
                     "pc.color_mode","proxy_output.pixels"):
        assert required in src,required
    for forbidden in ("shader_float8","cooperative_matrix","VK_NV",
                      "GL_EXT_shader_explicit_arithmetic_types_float16"):
        assert forbidden not in src,forbidden
    with tempfile.TemporaryDirectory(prefix="r09-texture-proxy-") as t:
        spv=Path(t)/"texture_proxy.spv"
        subprocess.run(["glslangValidator","-V","--target-env","vulkan1.1",
                        "-S","comp","-o",str(spv),str(shader)],
                       check=True,capture_output=True)
        subprocess.run(["spirv-val","--target-env","vulkan1.1",str(spv)],
                       check=True,capture_output=True)
        asm=subprocess.check_output(["spirv-dis",str(spv)],text=True)
        assert "OpExecutionMode %main LocalSize 8 8 1" in asm
        for name,b in (("source_texture",0),("proxy_output",1)):
            assert re.search(rf"OpDecorate %{name} DescriptorSet 0\b",asm),name
            assert re.search(rf"OpDecorate %{name} Binding {b}\b",asm),name
        for i in range(4):
            assert re.search(rf"OpMemberDecorate %Params {i} Offset {i*4}\b",asm),i
        assert re.findall(r"OpCapability ([A-Za-z0-9_]+)",asm)==["Shader"]
        if header:
            raw=spv.read_bytes()
            words=struct.unpack("<"+"I"*(len(raw)//4),raw)
            lines=["// SPDX-License-Identifier: MIT","#pragma once",
                   "#include <array>","#include <cstdint>",
                   f"inline constexpr std::array<std::uint32_t, {len(words)}> "
                   "RDNA2_NR_TEXTURE_PROXY_COMP_SPV = {"]
            for i in range(0,len(words),8):
                lines.append("    "+", ".join(f"0x{x:08x}u" for x in words[i:i+8])+",")
            lines.append("};")
            header.parent.mkdir(parents=True,exist_ok=True)
            header.write_text("\n".join(lines)+"\n",encoding="utf-8")
        print("R09_TEXTURE_PROXY_SPIRV_ABI_PASS",spv.stat().st_size)
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--vendor",required=True,type=Path)
    p.add_argument("--header",type=Path)
    a=p.parse_args()
    check(a.vendor/"encore-active/eden-vulkan/r09_rdna2_nr/"
          "texture_proxy_rdna2.comp",a.header)
