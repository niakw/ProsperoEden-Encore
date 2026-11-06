#!/usr/bin/env python3
"""Validate the RDNA2 noise-field shader ABI and generate the PS5 C++ SPIR-V header."""
import argparse
import re
import struct
import subprocess
import tempfile
from pathlib import Path

def validate(shader: Path, header: Path | None) -> None:
    text = shader.read_text(encoding="utf-8")
    for forbidden in ("cooperative_matrix", "shader_float8",
                      "GL_EXT_shader_explicit_arithmetic_types_float16",
                      "GL_EXT_shader_16bit_storage"):
        assert forbidden not in text, forbidden
    with tempfile.TemporaryDirectory(prefix="encore-rdna2-noise-") as temp:
        binary = Path(temp) / "noise_field.spv"
        subprocess.run(["glslangValidator", "-V", "--target-env", "vulkan1.1",
                        "-S", "comp", "-o", str(binary), str(shader)],
                       check=True, capture_output=True)
        subprocess.run(["spirv-val", "--target-env", "vulkan1.1", str(binary)],
                       check=True, capture_output=True)
        asm = subprocess.check_output(["spirv-dis", str(binary)], text=True)
        assert "OpExecutionMode %main LocalSize 8 8 1" in asm
        assert re.search(r"OpDecorate %result_noise Binding 0\b", asm)
        assert re.search(r"OpDecorate %result_noise DescriptorSet 0\b", asm)
        for n in range(5):
            assert re.search(rf"OpMemberDecorate %Dispatch {n} Offset {4*n}\b", asm), n
        assert re.findall(r"OpCapability ([A-Za-z0-9_]+)", asm) == ["Shader"]
        assert "OpTypeCooperativeMatrix" not in asm
        if header:
            payload = binary.read_bytes()
            words = struct.unpack("<" + "I" * (len(payload) // 4), payload)
            lines = ["// SPDX-License-Identifier: MIT",
                     "// RDNA2 noise field: MIT adaptation of DLSSNR-AMD.",
                     "#pragma once", "#include <array>", "#include <cstdint>",
                     f"inline constexpr std::array<std::uint32_t, {len(words)}> RDNA2_NR_NOISE_FIELD_COMP_SPV = {{"]
            for i in range(0, len(words), 8):
                lines.append("    " + ", ".join(f"0x{x:08x}u" for x in words[i:i+8]) + ",")
            lines.append("};")
            header.parent.mkdir(parents=True, exist_ok=True)
            header.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print("RDNA2_NOISE_FIELD_SPIRV_ABI_PASS", binary.stat().st_size)

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--vendor", type=Path, required=True)
    p.add_argument("--header", type=Path)
    a = p.parse_args()
    validate(a.vendor / "encore-active/eden-vulkan/r09_rdna2_nr/noise_field_rdna2.comp",
             a.header)
