#!/usr/bin/env python3
"""P0.2: real native 32-slot QMD3->Vulkan staging host witness.

Compiles/runs the maintained QMD3 environment fixture; it tests 32 real
descriptor records, strict refusal of 33, last-slot unmap, and rollback.
No PS5 SDK, CMake build, Vulkan device or console needed.
"""
from pathlib import Path
import os
import platform
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[2]
fixture = ROOT / "tools/ns2/test_native_qmd_compute_environment.cpp"
source = fixture.read_text()
assert "wide_info.storage_buffers_descriptors.push_back({0,0,32,true});" in source
assert "wide->storage_buffers.size() == 32" in source
assert "wide_info.storage_buffers_descriptors[0].count = 33;" in source
assert "forged.storage_buffers.push_back(forged.storage_buffers.back());" in source
assert "wide_bindings == 31 && rollback_count == 1" in source
assert "wide_bindings == 0 && rollback_count == 1" in source

native = (ROOT / "vendor/encore-active/ns2-runtime/ampere/shader_recompiler/frontend/ampere/native_qmd_compute_environment.h").read_text()
vulkan = (ROOT / "vendor/encore-active/eden-vulkan/vk_compute_pipeline_cost.cpp").read_text()
legacy = (ROOT / "vendor/sources/eden/src/video_core/buffer_cache/buffer_cache_base.h").read_text()
assert "storage_buffers.size() > 32" in native
assert "desc.count > 32 - result.storage_buffers.size()" in native
assert "bool ComputePipeline::ConfigureNative(" in vulkan
native_method = vulkan.split("bool ComputePipeline::ConfigureNative(",1)[1]
assert "resources.StageVulkanBufferBindings(" in native_method
assert "buffer_cache.ObtainBuffer(" in native_method
assert "buffer_cache.BindComputeStorageBuffer(" not in native_method
assert "constexpr u32 NUM_STORAGE_BUFFERS = 16;" in legacy

base = ROOT / "vendor/sources/eden-cpm"
includes = [
    base / "fmt/12.1.0/include",
    ROOT / "vendor/encore-active/ns2-runtime/ampere",
    ROOT / "vendor/encore-active/ns2-runtime/gpu_dispatch",
    ROOT / "vendor/sources/eden/src",
]
includes += sorted((base/"boost/boost-1.90.0/libs").glob("*/include"))
assert len(includes) > 100
environment = os.environ.copy()
if platform.system() == "Darwin":
    environment.setdefault(
        "SDKROOT", "/Library/Developer/CommandLineTools/SDKs/MacOSX26.5.sdk")
build = ROOT / ".build-local"
build.mkdir(exist_ok=True)
for compiler in ("clang++", "g++"):
    binary = shutil.which(compiler)
    assert binary, f"Missing compiler: {compiler}"
    for optimization in ("-O0", "-O2"):
        output = build / f"p02-qmd32-{compiler.replace('+','p')}-{optimization[1:]}"
        cmd = [
            binary, "-std=c++20", optimization,
            "-Wall", "-Wextra", "-Werror", "-Wno-unused-parameter",
            "-fsanitize=undefined", "-fno-sanitize-recover=all",
            *("-I"+str(p) for p in includes), str(fixture), "-o", str(output),
        ]
        result = subprocess.run(cmd, text=True, capture_output=True,
                                env=environment, timeout=150)
        assert result.returncode == 0, (compiler, optimization, result.stderr[-4000:])
        result = subprocess.run([str(output)], text=True, capture_output=True,
                                env=environment, timeout=90)
        assert result.returncode == 0, (
            compiler, optimization, result.stdout[-2000:], result.stderr[-4000:])
        print(f"P0_2_QMD32_REAL_STAGING_PASS {compiler} {optimization}", flush=True)
print("P0_2_QMD32_NS1_ABI_UNCHANGED_PASS valid=32 refused=33 owner=ObtainBuffer")
