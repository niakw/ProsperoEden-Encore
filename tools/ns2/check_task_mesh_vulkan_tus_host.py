#!/usr/bin/env python3
"""P2.4: parse the REAL maintained Vulkan Task/Mesh graphics pipeline owners.

Host Clang C++20 checks actual pinned/active header compatibility, not an
isolated snippet. These are shared Vulkan TUs, without PS5 SDK or GPU activity.
No claim of guest frame, on-console compilation or Vulkan execution.
"""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import os
import platform
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
ACTIVE = ROOT / "vendor/encore-active/eden-vulkan"
SHADER = ROOT / "vendor/encore-active/eden-shader/src"
CPM = ROOT / "vendor/sources/eden-cpm"
OWNERS = (
    "vk_graphics_pipeline_cost.cpp",
    "vk_pipeline_cache_cost.cpp",
    "vulkan_rasterizer.cpp",
)
cmake = (ROOT / "headless/CMakeLists.txt").read_text()
assert "EDEN_NATIVE_TASK_MESH_ROOT" in cmake
assert "shader_recompiler/backend/spirv/emit_spirv_mesh.cpp" in cmake
stage = (SHADER / "shader_recompiler/stage.h").read_text()
assert "Task," in stage and "Mesh," in stage
device = (ACTIVE / "include/video_core/vulkan_common/vulkan_device.h").read_text()
assert "IsExtMeshShaderSupported()" in device
for owner in OWNERS:
    assert (ACTIVE / owner).is_file(), owner
assert "DrawMeshTasksEXT(" in (ACTIVE / "vulkan_rasterizer.cpp").read_text()
assert "StageFlag(const Shader::Info&" in (ACTIVE / "vk_graphics_pipeline_cost.cpp").read_text()

includes = [
    ROOT / "headless",
    SHADER,
    ACTIVE / "include",
    ROOT / "vendor/encore-active/ns2-astc/include",
    ROOT / "vendor/encore-active/ns2-helpers/include",
    ROOT / "vendor/sources/eden/src",
    CPM / "vulkanheaders/v1.4.345/include",
    CPM / "vulkanmemoryallocator/v3.3.0/include",
    CPM / "fmt/12.1.0/include",
    CPM / "sirit/v1.0.5/include",
    CPM / "spirv-headers/vulkan-sdk-1.4.341.0/include",
]
boost = CPM / "boost/boost-1.90.0/libs"
assert boost.is_dir()
includes.extend(sorted(boost.glob("*/include")))
assert len(includes) >= 95
assert all(path.is_dir() for path in includes), "Maintained Vulkan dependency missing"
compiler = shutil.which("clang++-18") or shutil.which("clang++")
assert compiler, "Clang C++20 host compiler not installed"
command = [compiler, "-std=c++20", "-O0", "-fsyntax-only",
           "-Wno-unused-parameter", "-DFMT_HEADER_ONLY",
           *["-I" + str(path) for path in includes]]
env = os.environ.copy()
with tempfile.TemporaryDirectory(prefix="encore-task-mesh-host-") as scratch:
    if platform.system() == "Darwin":
        sdk = next((p for p in (
            Path("/Library/Developer/CommandLineTools/SDKs/MacOSX26.5.sdk"),
            Path("/Library/Developer/CommandLineTools/SDKs/MacOSX27.0.sdk"))
            if (p / "usr/include/c++/v1/__thread/jthread.h").is_file()), None)
        assert sdk, "C++20 Apple SDK missing for host Vulkan syntax witness"
        env["SDKROOT"] = str(sdk)
        shim = Path(scratch) / "arm64-pause-syntax.h"
        shim.write_text(
            "#pragma once\\n#ifdef __aarch64__\\n"
            "#ifndef __builtin_ia32_pause\\n"
            '#define __builtin_ia32_pause() __asm__ __volatile__("yield")\\n'
            "#endif\\n#endif\\n")
        command += ["-target", "arm64-apple-macos15", "-nostdinc++",
                    "-isystem", str(sdk / "usr/include/c++/v1"),
                    "-include", str(shim)]
    def check(owner):
        result = subprocess.run(
            command + [str(ACTIVE / owner)], cwd=ROOT, env=env,
            capture_output=True, text=True, timeout=180)
        return owner, result.returncode, result.stderr[-6000:]
    with ThreadPoolExecutor(max_workers=3) as pool:
        checked = list(pool.map(check, OWNERS))
    for owner, code, stderr in checked:
        assert code == 0, ("P2.4 maintained Vulkan TU syntax failed", owner, stderr)
        print("P24_REAL_VULKAN_TASK_MESH_TU_PASS", owner, flush=True)
print("P24_REAL_VULKAN_TASK_MESH_HOST_ONLY_PASS count=3 console=NOT_TESTED", flush=True)
