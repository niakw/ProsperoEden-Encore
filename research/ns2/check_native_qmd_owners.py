#!/usr/bin/env python3
"""Research-only owner witness: compiles the EXACT native-QMD GMMU guard from pinned vendor.

This intentionally does not build PS5 binaries, alter the source tree, or change
any CI trigger. It tests a real extracted function body with synthetic mappings,
not an actual guest process or Vulkan device.
"""
from __future__ import annotations

import argparse
import hashlib
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
GPU_MEMORY_MANAGER = Path("encore-active/eden-core/src/video_core/memory_manager.cpp")
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

def normalized_function_sha256(source: str, function_name: str) -> str:
    """Hash function behavior after removing only comments and whitespace."""
    function = function_body(source, function_name)
    body = function[function.index("{"):]
    body = re.sub(r"//[^\n]*", "", body)
    body = re.sub(r"/\*[\s\S]*?\*/", "", body)
    body = "".join(body.split())
    return hashlib.sha256(body.encode("utf-8")).hexdigest()

def extract_mapping_guard(source: str) -> str:
    fn = "NativeQmdContiguousGpuSpan"
    marker = source.index(fn + "(")
    start = source.rfind("template <typename Map>", 0, marker)
    require(start >= 0, "Native QMD mapping guard is not templated")
    const_match = re.search(r"inline constexpr u64 kNativeQmdMaxContiguousBytes = [^;]+;", source)
    require(const_match is not None, "native guard budget constant absent")
    return const_match.group(0) + "\n" + source[start:marker] + function_body(source, fn)

def count_native_mapping_scans(header: str, pipe: str, raster: str) -> dict[str, int]:
    """Fail closed if any of the six real native mapping validation owners drift."""
    configure = function_body(pipe, "ComputePipeline::ConfigureNative")
    stage = function_body(header, "StageVulkanBufferBindings")
    validation = function_body(header, "ValidateGpuBufferMappings")
    dispatch = function_body(raster, "RasterizerVulkan::DispatchNativeCompute")
    snapshot_anchor = "struct NativeQmdPhysicalBufferSnapshot final {"
    require(snapshot_anchor in header, "Physical buffer snapshot owner missing")
    snapshot = header[header.index(snapshot_anchor):]
    capture = function_body(snapshot, "Capture")
    matches = function_body(snapshot, "Matches")
    native_direct = configure.count("resources.ValidateGpuBufferMappings(mapped)")
    native_stage = configure.count("resources.StageVulkanBufferBindings(")
    raster_capture = dispatch.count("staged_buffer_mappings.Capture(")
    raster_match = dispatch.count("staged_buffer_mappings.Matches(")
    require((native_direct, native_stage, raster_capture, raster_match) == (2, 1, 1, 2),
            "Native GMMU pass call graph changed; do not quote 6 passes")
    require(stage.count("ValidateGpuBufferMappings(mapped)") == 1 and
            stage.count("ValidateGpuMappings(mapped)") == 1,
            "Native stage preflight path changed")
    require("ValidateGpuBufferMappings(std::forward<IsMapped>(mapped))" in header,
            "Native no-image validation delegate changed")
    require("mapped(storage.gpu_address, storage.bytes)" in validation,
            "Reflected native storage buffer mapping loop changed")
    require(capture.count("NativeQmdContiguousGpuSpan(address, bytes, map)") == 1 and
            matches.count("NativeQmdContiguousGpuSpan(address, bytes, map)") == 1,
            "Native snapshot physical-span validation changed")
    func = function_body(header, "NativeQmdContiguousGpuSpan")
    require("delta = 4096 - (gpu_addr & 4095U)" in func and
            "delta += 4096" in func and
            "map(gpu_addr + bytes - 1)" in func,
            "Native GMMU page granularity or final-byte check changed")
    # Aligned 32 MiB: one start lookup, 8,191 interior page starts, one
    # last-byte lookup. A successful native dispatch performs six full
    # scans on its CBUF/SSBO spans (plus snapshot endpoint lookups).
    direct_scans = native_direct + native_stage + raster_capture + raster_match
    require(direct_scans == 6, "Native QMD3 pass-count mismatch")
    bytes_32mib = 32 * 1024 * 1024
    lookups_per_span = 2 + (bytes_32mib // 4096 - 1)
    return {
        "native_full_span_passes_per_successful_dispatch": direct_scans,
        "aligned_32mib_lookups_per_pass": lookups_per_span,
        "aligned_32mib_minimum_lookups_in_six_passes": direct_scans * lookups_per_span,
    }


def extract_native_size_expression(source: str) -> str:
    """Embed the exact maintained condition, not a guessed descriptor heuristic."""
    match = re.search(
        r"const bool known_size = tag == 0 && bytes != 0;", source)
    require(match is not None, "Native size admission condition changed")
    require("const u32 bytes = record[2], tag = record[3];" in source,
            "QMD3 four-word descriptor fields changed")
    require("result.requires_memory_layout |= !known_size;" in source,
            "Native unknown-length rejection changed")
    return match.group(0)


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

[[nodiscard]] bool NativeSizeKnown(u32 bytes, u32 tag) {
    __REAL_NATIVE_SIZE_CONDITION__
    return known_size;
}

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
    // The condition below is the actual BuildResourcePlan descriptor policy.
    check(NativeSizeKnown(266, 0)); // Ambiguous word is admitted as a 266-byte extent.
    check(NativeSizeKnown(16 * 1024 * 1024, 0));
    check(!NativeSizeKnown(0, 0));
    check(!NativeSizeKnown(0, 1));
    check(!NativeSizeKnown(266, 1));
    check(!NativeSizeKnown(1024, std::numeric_limits<u32>::max()));
    check(NativeSizeKnown(256U * 1024 * 1024 + 1, 0)); // Tag admits it, GMMU guard later rejects >256 MiB.
    std::cout << "PASS: " << checks << " exact-source native QMD mapped-span checks\\n";
}
"""

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--vendor", type=Path, default=Path("vendor"))
    parser.add_argument("--compiler", action="append", choices=["clang++", "g++"])
    args = parser.parse_args()
    vendor = args.vendor
    git = shutil.which("git")
    require(git is not None, "Git required to verify exact pinned vendor commit")
    pinned = subprocess.run([git, "-C", str(vendor), "rev-parse", "HEAD"],
                            capture_output=True, text=True, check=True).stdout.strip()
    require(pinned == EXPECTED_VENDOR,
            "Vendor SHA changed: re-audit first (expected " + EXPECTED_VENDOR +
            ", got " + pinned + ")")
    header = (vendor / VENDOR_HEADER).read_text(encoding="utf-8")
    pipe = (vendor / VULKAN_PIPE).read_text(encoding="utf-8")
    raster = (vendor / VULKAN_RASTER).read_text(encoding="utf-8")
    shared = (vendor / SHARED_BUFFER).read_text(encoding="utf-8")
    memory_impl = (vendor / GPU_MEMORY_MANAGER).read_text(encoding="utf-8")
    map_lookup = function_body(memory_impl, "MemoryManager::GpuToCpuAddress")
    native_owner = function_body(pipe, "ComputePipeline::ConfigureNative")
    require("GetEntry(gpu_addr, true)" in map_lookup and
            "GetEntry(gpu_addr, false)" in map_lookup,
            "Native mapping point lookup implementation changed")
    # This is a narrowly scoped source observation, not a proof about external locks.
    require("shared_lock" not in map_lookup and "scoped_lock" not in map_lookup and
            "shared_lock" not in native_owner and "gpu_page_table_revision" not in native_owner,
            "Native mapping read-lease/revision policy changed; re-audit")
    require("std::atomic<u64> gpu_page_table_revision{1};" in memory_impl,
            "Global page-table revision owner changed")
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
    guard_sha256 = normalized_function_sha256(header, "NativeQmdContiguousGpuSpan")
    require(guard_sha256 ==
            "90c871905ad8c6d5a193acea84a457816cf1bc432d71c06de6f6ab68e0f9b7a2",
            "Maintained native GMMU source differs from compiled local owner witness")
    source = (HARNESS.replace("__REAL_NATIVE_QMD_FUNCTION__", extract_mapping_guard(header))
              .replace("__REAL_NATIVE_SIZE_CONDITION__", extract_native_size_expression(header)))
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
    mapping_scans = count_native_mapping_scans(header, pipe, raster)
    print(json.dumps({
        "mode": "offline research; real extracted GMMU source, mocked mappings",
        "mapping_passes_static_owner_witness": mapping_scans,
        "vendor_path": str(vendor), "reviewed_vendor_pin": EXPECTED_VENDOR,
        "exact_mapping_guard_normalized_sha256": guard_sha256,
        "native_uses_legacy_buffer_binding": False,
        "unknown_native_lengths_currently_rejected": True,
        "no_explicit_gmmu_read_lease_in_examined_native_owners": True,
        "native_descriptor_tag_zero_length_nonzero_gate": True,
        "compilers": reports,
    }, indent=2))

if __name__ == "__main__":
    main()
