#!/usr/bin/env python3
"""Build ALL maintained R09 GPU shader headers from actual Vulkan-1.1 SPIR-V.

No model DLL, weights, fixtures, or user captures are read. The generated
headers contain only shader machine code for the open-source RDNA2 path.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import re
import struct
import subprocess
import sys

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--vendor", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    root = args.vendor / "encore-active/eden-vulkan"
    shaders = sorted((root / "r09_rdna2_nr").glob("*_rdna2.comp"))
    owners = sorted(root.glob("nr_rdna2_*.cpp"))
    if len(shaders) < 35 or len(owners) < 73:
        raise RuntimeError("incomplete production R09 source inventory")
    args.output.mkdir(parents=True, exist_ok=True)
    produced = {}
    for shader in shaders:
        stem = shader.name.removesuffix("_rdna2.comp")
        public_name = "ffwd3" if stem == "ffwd3_group" else stem
        symbol = "RDNA2_NR_" + public_name.upper() + "_COMP_SPV"
        header = args.output / f"rdna2_nr_{public_name}_comp_spv.h"
        if public_name in produced:
            raise RuntimeError(f"duplicate R09 shader symbol {public_name}")
        produced[public_name] = header
        # Fail if even one shader is absent, fails compilation or fails SPIR-V validation.
        spv = args.output / (public_name + ".spv")
        subprocess.run(["glslangValidator", "-V", "--target-env", "vulkan1.1",
                        "-S", "comp", "-o", str(spv), str(shader)],
                       check=True, stdout=subprocess.DEVNULL)
        subprocess.run(["spirv-val", "--target-env", "vulkan1.1",
                        str(spv)], check=True)
        data = spv.read_bytes()
        if not data or len(data) % 4:
            raise RuntimeError(f"invalid SPIR-V byte count: {shader.name}")
        words = struct.unpack("<" + "I" * (len(data) // 4), data)
        lines = ["// SPDX-License-Identifier: MIT", "#pragma once",
                 "#include <array>", "#include <cstdint>",
                 f"inline constexpr std::array<std::uint32_t, {len(words)}> {symbol} = {{"]
        for i in range(0, len(words), 8):
            lines.append("    " + ", ".join(
                f"0x{word:08x}u" for word in words[i:i + 8]) + ",")
        lines.append("};")
        header.write_text("\n".join(lines) + "\n", encoding="utf-8")
        spv.unlink()  # No unnecessary binary duplicate in the public artifact.
    includes = set()
    for owner in owners:
        for included in re.findall(
                r'#include\s+["<]video_core/host_shaders/([^">]+)[">]',
                owner.read_text(encoding="utf-8")):
            includes.add(included)
            if not (args.output / included).is_file():
                raise RuntimeError(f"unbuilt shader required by {owner.name}: {included}")
    if len(includes) < 30:
        raise RuntimeError("R09 expected shader dependencies not present")
    print(f"R09_REAL_SHADERS_HEADER_BUILD_PASS shaders={len(shaders)} "
          f"owners={len(owners)} includes={len(includes)}")

if __name__ == "__main__":
    try:
        main()
    except (OSError, RuntimeError, subprocess.CalledProcessError) as exc:
        print("R09_HOST_SHADER_BUILD_FAILED", exc, file=sys.stderr)
        sys.exit(1)
