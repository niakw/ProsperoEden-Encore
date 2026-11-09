#!/usr/bin/env python3
"""R09 RDNA2: shader-only Vulkan fallback proof and ABI check.

This does NOT attest DLSS compatibility or PS5 performance.
Requires glslangValidator, spirv-val and spirv-dis on build host.
"""
import argparse
import re
import struct
import subprocess
import tempfile
from pathlib import Path

def validate(shader: Path, header: Path | None):
    assert shader.is_file(), shader
    source=shader.read_text(encoding="utf-8")
    assert "cooperative_matrix" not in source.lower(), "RDNA4-only instruction"
    assert "shader_float8" not in source.lower(), "RDNA4-only extension"
    assert "GL_EXT_shader_explicit_arithmetic_types_float8" not in source, "FP8 extension"
    assert "shared float a_tile[16][16]" in source
    assert "shared float w_tile[16][16]" in source
    with tempfile.TemporaryDirectory(prefix="encore-rdna2-nr-") as directory:
        spv=Path(directory)/"projection.spv"
        subprocess.run(
            ["glslangValidator","-V","--target-env","vulkan1.1","-S","comp",
             "-o",str(spv),str(shader)],
            check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(["spirv-val","--target-env","vulkan1.1",str(spv)],
                       check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        asm=subprocess.check_output(["spirv-dis",str(spv)],text=True)
        assert re.search(r"OpExecutionMode %main LocalSize 16 16 1", asm)
        expected={"activations":0,"weights":1,"output_tensor":2}
        for variable,binding in expected.items():
            assert re.search(rf"OpDecorate %{variable} Binding {binding}\b",asm), variable
            assert re.search(rf"OpDecorate %{variable} DescriptorSet 0\b",asm), variable
        for i in range(8):
            assert re.search(
                rf"OpMemberDecorate %Dispatch {i} Offset {4*i}\b",asm), i
        capabilities=re.findall(r"OpCapability ([A-Za-z0-9_]+)",asm)
        assert capabilities == ["Shader"], capabilities
        assert "OpTypeCooperativeMatrixKHR" not in asm
        assert "OpTypeFloat8EXT" not in asm
        assert spv.stat().st_size > 512
        if header:
            binary=spv.read_bytes()
            assert len(binary)%4==0
            words=struct.unpack("<"+"I"*(len(binary)//4),binary)
            lines=[
                "// SPDX-License-Identifier: MIT",
                "// Generated RDNA2 Vulkan fallback projection. No proprietary model.",
                "#pragma once",
                "#include <array>",
                "#include <cstdint>",
                f"inline constexpr std::array<std::uint32_t, {len(words)}> "
                "RDNA2_NR_FP8_PROJ_COMP_SPV = {",
            ]
            for i in range(0,len(words),8):
                lines.append("    "+", ".join(f"0x{n:08x}u" for n in words[i:i+8])+",")
            lines.append("};")
            header.parent.mkdir(parents=True,exist_ok=True)
            header.write_text(chr(10).join(lines)+chr(10))
        print("RDNA2_SCALAR_FP8_GEMM_VULKAN_1_1_SPIRV_ABI_PASS",
              f"shader_bytes={spv.stat().st_size}")

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--vendor",type=Path,required=True)
    parser.add_argument("--header",type=Path,default=None)
    args=parser.parse_args()
    validate(args.vendor/"encore-active/eden-vulkan/r09_rdna2_nr/fp8_proj_rdna2.comp",
             args.header)

if __name__ == "__main__":
    main()
