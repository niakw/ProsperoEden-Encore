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
import runpy
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
# Compile real shader-stage construction, native translation environment and
# GPU-source admission too: a graphics TU alone cannot prove that Mesh/Task
# reaches the native Maxwell-to-IR stage or uses the correct CBUF bank.
MESH_STAGE_OWNERS = (
    ROOT / "vendor/encore-active/eden-core/src/video_core/shader_environment.cpp",
    ROOT / "vendor/encore-active/ns2-runtime/ampere/shader_recompiler/frontend/ampere/maxwell_environment.cpp",
    ROOT / "vendor/encore-active/ns2-runtime/ampere/video_core/native_shader_capture.cpp",
)
# The real SPIR-V mesh emitter must compile too. The previous six-TU
# witness checked the pipeline but never parsed this stage-buffer lowering.
MESH_SPIRV_OWNERS = (
    SHADER / "shader_recompiler/backend/spirv/emit_spirv_mesh.cpp",
    ROOT / "vendor/encore-active/ns2-runtime/ampere/shader_recompiler/backend/spirv/spirv_emit_context.cpp",
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
for path in MESH_STAGE_OWNERS + MESH_SPIRV_OWNERS:
    assert path.is_file(), path
mesh_emit = MESH_SPIRV_OWNERS[0].read_text()
mesh_context = MESH_SPIRV_OWNERS[1].read_text()
assert "Invalid native Task/Mesh shader dimensions" in mesh_context
assert "Native Mesh output region exceeds u32 indexing" in mesh_context
assert "const u64 vertex_words" in mesh_context
assert "const u64 map_bytes" in mesh_context
assert "TypeArray(U32[1], Const((std::max)(mesh_info.payload_words, 1U)))" in mesh_context
# Ensure invalid dimensions fail explicitly and guest out-of-bounds writes
# cannot alias the final live primitive/payload byte.
assert 'Mesh shader has zero workgroup threads' in mesh_emit
assert 'Task shader payload missing mesh-group count' in mesh_emit
assert 'Mesh shader has no task payload words' in mesh_emit
assert 'index, ctx.Const(ctx.mesh_attribute_words)' in mesh_emit
assert 'address, ctx.Const(ctx.mesh_map_bytes)' in mesh_emit
assert "SharedWord(ctx, ctx.mesh_map, Clamped(" not in mesh_emit
assert "SharedWord(ctx, ctx.mesh_attributes, Clamped(" not in mesh_emit
stage_owner = MESH_STAGE_OWNERS[0].read_text()
assert 'CaptureGraphicsTicket(maxwell3d).has_value()' in stage_owner
assert 'Shader::Stage::Task : Shader::Stage::Mesh' in stage_owner
assert 'IsShaderConfigEnabled(Maxwell::ShaderType::TessellationInit)' in stage_owner
env_owner = MESH_STAGE_OWNERS[1].read_text()
assert 'mesh_registers = source.MeshRegisters();' in env_owner
assert 'mesh_primitive_header = source.MeshPrimitiveHeader();' in env_owner
capture_owner = MESH_STAGE_OWNERS[2].read_text()
assert 'NativeMeshSlotCbufBank(shader_stage, has_task)' in capture_owner
assert 'NativeMeshRegisterPipelineKey(' in capture_owner
assert 'NativeMeshPrimitiveHeaderPipelineKey(' in capture_owner
assert 'NativeMeshPrimitiveHeaderAddress(' in capture_owner
assert 'IsShaderConfigEnabled(Maxwell::ShaderType::Geometry)' in stage_owner
assert 'mesh_primitive_header' in stage_owner
assert 'live_executable_stages' in (ACTIVE / "vk_pipeline_cache_cost.cpp").read_text()
assert 'NativeMeshRegisterPipelineKey(' in (
    ROOT / "vendor/encore-active/ns2-runtime/ampere/shader_recompiler/frontend/ampere/native_graphics_stage_policy.h"
).read_text()
cache_owner = (ACTIVE / "vk_pipeline_cache_cost.cpp").read_text()
assert cache_owner.count("NativeMeshSlotCbufBank(stage, has_task)") == 3
assert cache_owner.count("NativeMeshGraphicsStageMaskSupported(") == 2
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
    ROOT / "extras/graphics",
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
    # The PS5 renderer uses the *reviewed* 83-source settings.h and a
    # separately staged graphics-enum extension (Msaa2/4/8/16), not
    # pristine Eden Settings::AntiAliasing. This is the identical audited
    # overlay used by headless/CMakeLists.txt for the actual native build.
    graphics_stage = Path(scratch) / "graphics-enums/common"
    graphics_stage.mkdir(parents=True)
    graphics_tools = runpy.run_path(
        str(ROOT / "tools/stage-ps5-graphics-enums.py"))
    _, reviewed = graphics_tools["approved_bytes"]()
    graphics_enums = graphics_tools["extend_graphics_enums"](
        reviewed.decode("utf-8"))
    (graphics_stage / "settings_enums.h").write_text(
        graphics_enums, encoding="utf-8")
    reviewed_settings = (
        ROOT / "vendor/encore-active/eden-backports/src/common/settings.h")
    assert reviewed_settings.is_file()
    shutil.copyfile(reviewed_settings, graphics_stage / "settings.h")
    command.insert(command.index("-I" + str(includes[0])),
                   "-I" + str(graphics_stage.parent))
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
    maintained_base = ROOT / (
        "vendor/encore-active/eden-core/src/video_core/buffer_cache/buffer_cache_base.h"
    )
    assert maintained_base.is_file(), "R437 matching BufferCacheBase owner missing"
    base_contract = maintained_base.read_text()
    assert "bool needs_sync = true" in base_contract
    assert "void SynchronizeBufferWrites(Buffer& buffer);" in base_contract
    assert "EDEN_MAINTAINED_BUFFER_BASE" in cmake
    shutil.copyfile(maintained_base, buffer_overlay / "buffer_cache_base.h")
    # Header search must prefer the PS5-native generated R437 owner over
    # vendor/sources/eden/src; appending this -I selects the wrong template.
    command.insert(command.index("-I" + str(includes[0])),
                   "-I" + str(Path(scratch) / "buffer-pages"))
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
    def check(source):
        result = subprocess.run(
            command + [str(source)], cwd=ROOT, env=env,
            capture_output=True, text=True, timeout=180)
        return str(source.relative_to(ROOT)), result.returncode, result.stderr[-20000:]
    sources = ([ACTIVE / owner for owner in OWNERS] +
               list(MESH_STAGE_OWNERS) + list(MESH_SPIRV_OWNERS))
    with ThreadPoolExecutor(max_workers=3) as pool:
        checked = list(pool.map(check, sources))
    failures = []
    for owner, code, stderr in checked:
        if code:
            failures.append((owner, stderr))
            print("P24_REAL_VULKAN_TASK_MESH_TU_FAIL", owner, stderr, flush=True)
        else:
            print("P24_REAL_VULKAN_TASK_MESH_TU_PASS", owner, flush=True)
    assert not failures, ("P2.4 maintained Vulkan TU syntax failed", failures)
print("P24_REAL_VULKAN_TASK_MESH_HOST_ONLY_PASS count=8 console=NOT_TESTED", flush=True)
