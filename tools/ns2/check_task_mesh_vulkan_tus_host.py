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
assert "virtual bool DispatchNativeCompute(" in (
    ROOT / "vendor/encore-active/ns2-runtime/vulkan_abi/video_core/rasterizer_interface.h"
).read_text()
assert (
    ROOT / "vendor/encore-active/ns2-runtime/hle/core/hle/service/nvdrv/devices/native_gpu_process_registry.h"
).is_file()
assert "DrawMeshTasksEXT(" in (ACTIVE / "vulkan_rasterizer.cpp").read_text()
assert "StageFlag(const Shader::Info&" in (ACTIVE / "vk_graphics_pipeline_cost.cpp").read_text()

includes = [
    ROOT / "headless",
    SHADER,
    # Native Maxwell/Ampere shader captures share this single reviewed
    # frontend root with the real renderer and pipeline-cache TUs.
    ROOT / "vendor/encore-active/ns2-runtime/ampere",
    # The reviewed QMD3 command ABI is owned by the shared GPU dispatcher,
    # separate from the Ampere shader frontend. Match CMake's native roots.
    ROOT / "vendor/encore-active/ns2-runtime/gpu_dispatch",
    # CMake stages the reviewed PS5-native RasterizerInterface into
    # PORT_BUILD_DIR/include; source-derived host syntax must select the same
    # virtual ABI before the pinned (pre-NS2) interface, never strip override.
    ROOT / "vendor/encore-active/ns2-runtime/vulkan_abi",
    # NVDRV process tickets are owned by the native HLE overlay, not nvdrv_gpu.
    ROOT / "vendor/encore-active/ns2-runtime/hle",
    ACTIVE / "include",
    ROOT / "vendor/encore-active/ns2-astc/include",
    ROOT / "vendor/encore-active/ns2-helpers/include",
    ROOT / "vendor/encore-active/ns2-runtime/nvdrv_gpu",
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
# These maintained TUs are selected in the PS5_NATIVE Vulkan graph.
# Desktop builds use the pinned upstream owners; compiling this native
# graphics TU without PS5_NATIVE deliberately omits its exact-descriptor
# queue API and is NOT a valid production syntax proof.
command = [compiler, "-std=c++20", "-O0", "-fsyntax-only",
           "-DPS5_NATIVE=1", "-Wno-unused-parameter",
           "-DFMT_HEADER_ONLY",
           *["-I" + str(path) for path in includes]]
env = os.environ.copy()
with tempfile.TemporaryDirectory(prefix="encore-task-mesh-host-") as scratch:
    sysdir = Path(scratch) / "sys"
    sysdir.mkdir()
    # FreeBSD/Prospero cpuset API is absent from Linux/macOS CI. The shim
    # supplies only declarations needed by syntax-only parsing; no affinity
    # behavior, PS5 headers, object or ELF is synthesized.
    (sysdir / "cpuset.h").write_text(
        "#pragma once\n"
        "#define CPU_LEVEL_WHICH 3\n#define CPU_WHICH_TID 4\n"
        "#ifdef __linux__\n"
        "#include <sched.h>\n"
        "using cpuset_t = cpu_set_t;\n"
        "inline int cpuset_getaffinity(int, int, int, size_t size, cpuset_t* mask) {\n"
        "    return sched_getaffinity(0, size, mask);\n"
        "}\n"
        "#else\n"
        "struct cpuset_t { unsigned long bits[16]; };\n"
        "inline int cpuset_getaffinity(int, int, int, size_t, cpuset_t*) { return -1; }\n"
        "#ifndef CPU_ISSET\n#define CPU_ISSET(cpu, mask) false\n#endif\n"
        "#endif\n")
    # PS5_NATIVE builds compile the R437 maintained buffer-cache owner from a
    # CMake-generated include overlay (headless/CMakeLists.txt). The source
    # archive alone has a different template/BufferCacheRuntime interface.
    # Recreate the exact tracked header overlay for the real syntax witness.
    buffer_overlay = Path(scratch) / "buffer-pages/video_core/buffer_cache"
    buffer_overlay.mkdir(parents=True)
    maintained_buffer = ROOT / (
        "vendor/encore-active/eden-core/src/video_core/buffer_cache/buffer_cache.h"
    )
    assert maintained_buffer.is_file(), "R437 maintained BufferCache owner missing"
    shutil.copyfile(maintained_buffer, buffer_overlay / "buffer_cache.h")
    command += ["-I" + str(Path(scratch) / "buffer-pages")]
    command += ["-I" + str(Path(scratch))]
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
        return owner, result.returncode, result.stderr[-20000:]
    with ThreadPoolExecutor(max_workers=3) as pool:
        checked = list(pool.map(check, OWNERS))
    failures = []
    for owner, code, stderr in checked:
        if code:
            failures.append((owner, stderr))
            print("P24_REAL_VULKAN_TASK_MESH_TU_FAIL", owner, stderr, flush=True)
        else:
            print("P24_REAL_VULKAN_TASK_MESH_TU_PASS", owner, flush=True)
    assert not failures, ("P2.4 maintained Vulkan TU syntax failed", failures)
print("P24_REAL_VULKAN_TASK_MESH_HOST_ONLY_PASS count=3 console=NOT_TESTED", flush=True)
