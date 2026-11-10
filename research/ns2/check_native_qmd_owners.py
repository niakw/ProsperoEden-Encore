#!/usr/bin/env python3
"""Research-only owner witness: compiles the EXACT native-QMD GMMU guard from pinned vendor.

This intentionally does not build PS5 binaries, alter the source tree, or change
any CI trigger. It tests a real extracted function body with synthetic mappings,
not an actual guest process or Vulkan device.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

VENDOR_HEADER = Path("encore-active/ns2-runtime/ampere/shader_recompiler/frontend/ampere/native_qmd_compute_environment.h")
VULKAN_PIPE = Path("encore-active/eden-vulkan/vk_compute_pipeline_cost.cpp")
VULKAN_RASTER = Path("encore-active/eden-vulkan/vulkan_rasterizer.cpp")
SHARED_BUFFER = Path("encore-active/eden-core/src/video_core/buffer_cache/buffer_cache.h")
EXPECTED_VENDOR = "22b69d6053db41b74edac2633c012f925b84f69e"

def require(test: bool, message: str) -> None:
    if not test:
        raise RuntimeError(message)

def function_body(source: str, name: str) -> str:
    marker = source.index(name + "(")
    start = source.index("{", marker)
    depth = 0
    for index in range(start, len(source)):
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
            if depth == 0:
                return source[marker:index + 1]
    raise RuntimeError("unbalanced source owner: " + name)

def extract_mapping_guard(source: str) -> str:
    fn = "NativeQmdContiguousGpuSpan"
    marker = source.index(fn + "(")
    start = source.rfind("template <typename Map>", 0, marker)
    require(start >= 0, "Native QMD mapping guard is not templated")
    const_match = re.search(r"inline constexpr u64 kNativeQmdMaxContiguousBytes = [^;]+;", source)
    require(const_match is not None, "native guard budget constant absent")
    return const_match.group(0) + "\n" + source[start:source.index(
        function_body(source, fn), marker) + len(function_body(source, fn))]

HARNESS = r"""
#include <cassert>
#include <cstdint>
#include <iostream>
#include <limits>
#include <optional>
#include <stdexcept>
using u64 = std::uint64_t;
using u32 = std::uint32_t;
__REAL_NATIVE_QMD_FUNCTION__

int main() {
    int checks = 0;
    const auto check = [&](bool valid) { assert(valid); ++checks; };
    constexpr u64 gpu = 0x100000;
    constexpr u64 cpu = 0x200000;
    int lookups = 0;
    const auto contiguous = [&](u64 x) -> std::optional<u64> {
        ++lookups;
        return x + (cpu - gpu);
    };
    check(NativeQmdContiguousGpuSpan(gpu, 8192, contiguous));
    check(lookups == 3); // start, next 4 KiB page, final byte.
    lookups = 0;
    check(NativeQmdContiguousGpuSpan(gpu, 32U * 1024 * 1024, contiguous));
    check(lookups == 8193); // real O(number of pages) lookup cost.
    check(!NativeQmdContiguousGpuSpan(gpu, 0, contiguous));
    check(!NativeQmdContiguousGpuSpan(0, 4096, contiguous));
    check(!NativeQmdContiguousGpuSpan(gpu, 256U * 1024 * 1024 + 1, contiguous));
    check(!NativeQmdContiguousGpuSpan((u64{1} << 49) - 4096, 8192, contiguous));
    check(NativeQmdContiguousGpuSpan(gpu + 1, 8192, contiguous));
    check(!NativeQmdContiguousGpuSpan(gpu, 8192,
        [&](u64 x) -> std::optional<u64> {
            if (x >= gpu + 4096) return std::nullopt;
            return contiguous(x);
        }));
    check(!NativeQmdContiguousGpuSpan(gpu, 8192,
        [&](u64 x) -> std::optional<u64> {
            if (x >= gpu + 4096) return contiguous(x).value() + 4096;
            return contiguous(x);
        }));
    check(!NativeQmdContiguousGpuSpan(gpu, 8192,
        [&](u64 x) -> std::optional<u64> {
            if (x == gpu + 8191) return contiguous(x).value() + 1;
            return contiguous(x);
        }));
    check(!NativeQmdContiguousGpuSpan(gpu, 8192,
        [](u64) -> std::optional<u64> {
            throw std::runtime_error("synthetic mapping fault");
        }));
    check(!NativeQmdContiguousGpuSpan(gpu, 8192,
        [](u64) -> std::optional<u64> { return std::nullopt; }));
    check(!NativeQmdContiguousGpuSpan(gpu, 8192,
        [](u64) -> std::optional<u64> {
            return std::numeric_limits<u64>::max() - 100;
        }));
    check(NativeQmdContiguousGpuSpan(gpu, 1, contiguous));
    check(NativeQmdContiguousGpuSpan(gpu, 4096, contiguous));
    std::cout << "PASS: " << checks << " exact-source native QMD mapped-span checks\\n";
}
"""

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--vendor", type=Path, default=Path("vendor"))
    parser.add_argument("--compiler", action="append", choices=["clang++", "g++"])
    args = parser.parse_args()
    vendor = args.vendor
    header = (vendor / VENDOR_HEADER).read_text(encoding="utf-8")
    pipe = (vendor / VULKAN_PIPE).read_text(encoding="utf-8")
    raster = (vendor / VULKAN_RASTER).read_text(encoding="utf-8")
    shared = (vendor / SHARED_BUFFER).read_text(encoding="utf-8")
    legacy = function_body(pipe, "ComputePipeline::Configure")
    native = function_body(pipe, "ComputePipeline::ConfigureNative")
    require("BindComputeStorageBuffer" in legacy, "Legacy binding owner changed")
    require("BindComputeStorageBuffer" not in native, "Native path now delegates to legacy")
    require("StageVulkanBufferBindings" in native, "Native QMD binding owner changed")
    require("ConfigureNative(" in raster and "staged_buffer_mappings.Matches(" in raster,
            "PS5 native descriptor/mapping recheck changed")
    require("const bool known_size = tag == 0 && bytes != 0;" in header,
            "Native SSBO descriptor word recognition changed")
    require("result.requires_memory_layout |= !known_size;" in header,
            "Native unknown-length policy changed")
    require("if (requires_memory_layout ||" in header and
            "if (!storage.known_size || !storage.bytes || !storage.gpu_address)" in header,
            "Native fail-closed sizing gate changed")
    require("static_cast<u32>(8_MiB)" in shared and
            "StorageBufferBinding(ssbo_addr, cbuf_index, is_written)" in shared,
            "The legacy size fallback changed")
    source = HARNESS.replace("__REAL_NATIVE_QMD_FUNCTION__", extract_mapping_guard(header))
    compilers = args.compiler or ["clang++", "g++"]
    reports = []
    with tempfile.TemporaryDirectory(prefix="encore-ns2-owner-") as td:
        src = Path(td) / "owner.cpp"
        src.write_text(source, encoding="utf-8")
        for compiler in compilers:
            resolved = shutil.which(compiler)
            require(resolved is not None, "Required compiler missing: " + compiler)
            output = Path(td) / compiler.replace("+", "p")
            command = [resolved, "-std=c++20", "-O1", "-Wall", "-Wextra",
                       "-Werror", "-fsanitize=undefined",
                       "-fno-sanitize-recover=all", str(src), "-o", str(output)]
            subprocess.run(command, check=True, capture_output=True, text=True)
            executed = subprocess.run([str(output)], check=True, capture_output=True, text=True)
            reports.append({"compiler": compiler, "result": executed.stdout.strip()})
    print(json.dumps({
        "mode": "offline research; real extracted GMMU source, mocked mappings",
        "vendor_path": str(vendor), "reviewed_vendor_pin": EXPECTED_VENDOR,
        "native_uses_legacy_buffer_binding": False,
        "unknown_native_lengths_currently_rejected": True,
        "native_descriptor_tag_zero_length_nonzero_gate": True,
        "compilers": reports,
    }, indent=2))

if __name__ == "__main__":
    main()
