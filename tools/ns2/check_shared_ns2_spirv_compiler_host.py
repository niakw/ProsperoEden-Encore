#!/usr/bin/env python3
"""P0.2 source-owner proof: integrate native SPIR-V compiler without NS1 dispatch.

Executes the real CMake selector and parses maintained C++ compiler units.
Does not build a PS5 ELF, enable native NVDRV, or invoke a Vulkan GPU.
"""
from pathlib import Path
import os
import platform
import shutil
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[2]
CMAKE=(ROOT/"headless/CMakeLists.txt").read_text()
section=CMAKE.split("# P0.2: the native SPIR-V compiler and QMD3 bounds emitter",1)[1].split("# N50: shared native PS5 device-memory",1)[0]
assert "set(EDEN_SHARED_NS2_SPIRV_COMPILER OFF)" in section
assert "if(EDEN_SHARED_NS2_AMPERE_CORE)" in section
assert "if(EDEN_NS2_VULKAN_SHADER_BRIDGE_EXPERIMENTAL OR EDEN_SHARED_NS2_SPIRV_COMPILER)" in section
assert "target_sources(video_core PRIVATE" in section
assert "target_sources(shader_recompiler PRIVATE" not in section
assert "list(REMOVE_ITEM eden_ns2_shader_sources" in section
assert "backend/spirv/spirv_emit_context.cpp" in section
assert "backend/spirv/emit_spirv_context_get_set.cpp" in section
assert "target_include_directories(video_core BEFORE PRIVATE" in section
assert section.count("if(EDEN_NS2_VULKAN_SHADER_BRIDGE_EXPERIMENTAL)") == 2
assert 'target_compile_definitions(core PUBLIC EDEN_NS2_VULKAN_SHADER_BRIDGE_EXPERIMENTAL=1)' in section
# The real Vulkan rasterizer's native-Compute virtual and its ABI-breaking
# macro remain inside the research-only nested conditional.
assert section.index("    if(EDEN_NS2_VULKAN_SHADER_BRIDGE_EXPERIMENTAL)\n    # Native Vulkan") < section.index(
    "target_compile_definitions(core PUBLIC EDEN_NS2_VULKAN_SHADER_BRIDGE_EXPERIMENTAL=1)")

selector=section[section.index("set(EDEN_SHARED_NS2_SPIRV_COMPILER OFF)"):section.index(
    "if(EDEN_NS2_VULKAN_SHADER_BRIDGE_EXPERIMENTAL OR EDEN_SHARED_NS2_SPIRV_COMPILER)")]
with tempfile.TemporaryDirectory(prefix="encore-shared-spirv-") as tmp:
    script=Path(tmp)/"selector.cmake"
    for active,expected in ((True,"ON"),(False,"OFF")):
        script.write_text(
            "set(EDEN_SHARED_NS2_AMPERE_CORE "+("ON" if active else "OFF")+")\n"
            +selector+'\nmessage(STATUS "NS2_SPIRV=@{EDEN_SHARED_NS2_SPIRV_COMPILER}")\n'.replace("@{",chr(36)+"{"))
        result=subprocess.run(["cmake","-P",str(script)],capture_output=True,
                              text=True,timeout=15)
        assert result.returncode==0 and "NS2_SPIRV="+expected in result.stdout, (
            result.stdout,result.stderr)
print("P0_2_SHARED_SPIRV_SELECTOR_PASS qualified=ON desktop=OFF research_macro=OFF",flush=True)

# Verify the real source-owner CMake block in a tiny configure-only
# project, not merely by grepping conditional text. This checks the two
# actual target source lists while leaving the native PS5 build disabled.
block=CMAKE[CMAKE.index("option(EDEN_NS2_VULKAN_SHADER_BRIDGE_EXPERIMENTAL"):
            CMAKE.index("# N50: shared native PS5 device-memory")]
with tempfile.TemporaryDirectory(prefix="encore-spv-graph-") as temp:
    for active in (False,True):
        stage=Path(temp)/("native_release" if active else "desktop")
        (stage/"backend/spirv").mkdir(parents=True)
        for name in ("spirv_emit_context.cpp","emit_spirv_context_get_set.cpp"):
            (stage/"backend/spirv"/name).write_text("int stub_"+name.split(".")[0]+"=0;")
        (stage/"stub.cpp").write_text("int stub=0;")
        cxx_root=stage/"CMakeLists.txt"
        bootstrap=(
            "cmake_minimum_required(VERSION 3.23)\n"
            "set(CMAKE_TRY_COMPILE_TARGET_TYPE STATIC_LIBRARY)\n"
            "project(EncoreSpirvPreview LANGUAGES CXX)\n"
            "add_library(core STATIC stub.cpp)\n"
            "add_library(video_core STATIC stub.cpp)\n"
            "add_library(shader_recompiler STATIC stub.cpp)\n"
            "target_sources(shader_recompiler PRIVATE "
            "backend/spirv/spirv_emit_context.cpp "
            "backend/spirv/emit_spirv_context_get_set.cpp)\n"
        )
        config=(
            "set(PS5_NATIVE "+("ON" if active else "OFF")+")\n"
            "set(EDEN_REVIEWED_DUAL_NPDM "+("ON" if active else "OFF")+")\n"
            "set(EDEN_PS5_VULKAN "+("ON" if active else "OFF")+")\n"
            "set(EDEN_FINAL_RELEASE_PROFILE "+("ON" if active else "OFF")+")\n"
            "set(EDEN_SHARED_NS2_AMPERE_CORE "+("ON" if active else "OFF")+")\n"
            'set(PORT_ROOT "'+str(ROOT)+'")\n'
            'set(PORT_BUILD_DIR "'+str(stage/"derived")+'")\n'
            'set(EDEN_NS2_AMPERE_ROOT "'+
                str(ROOT/"vendor/encore-active/ns2-runtime/ampere")+'")\n'
        )
        dollar=chr(36)
        checks=(
            f'get_target_property(spv_sources shader_recompiler SOURCES)\n'
            f'get_target_property(video_sources video_core SOURCES)\n'
            f'get_target_property(video_flags video_core COMPILE_DEFINITIONS)\n'
            f'get_target_property(core_flags core COMPILE_DEFINITIONS)\n'
            f'message(STATUS "NATIVE_SPIRV_SOURCE={dollar}{{EDEN_SHARED_NS2_SPIRV_COMPILER}}")\n'
            f'message(STATUS "SHADER_SOURCES={dollar}{{spv_sources}}")\n'
            f'message(STATUS "VIDEO_SOURCES={dollar}{{video_sources}}")\n'
            f'message(STATUS "NATIVE_FLAGS={dollar}{{video_flags}};{dollar}{{core_flags}}")\n'
        )
        cxx_root.write_text(bootstrap+config+block+checks)
        env=os.environ.copy()
        args=["cmake","-S",str(stage),"-B",str(stage/"build"),
              "-DCMAKE_TRY_COMPILE_TARGET_TYPE=STATIC_LIBRARY"]
        if platform.system()=="Darwin":
            env["SDKROOT"]="/Library/Developer/CommandLineTools/SDKs/MacOSX15.4.sdk"
            args.append("-DCMAKE_OSX_SYSROOT="+env["SDKROOT"])
        result=subprocess.run(args,capture_output=True,text=True,
                              env=env,timeout=70)
        assert result.returncode==0,(active,result.stdout[-1800:],result.stderr[-3000:])
        output=result.stdout
        expected="ON" if active else "OFF"
        assert "NATIVE_SPIRV_SOURCE="+expected in output
        compiler_owner="vendor/encore-active/ns2-runtime/ampere/shader_recompiler/backend/spirv/spirv_emit_context.cpp"
        renderer_owner="vendor/encore-active/ns2-runtime/ampere/shader_recompiler/frontend/ampere/renderer_spirv_bridge.cpp"
        assert (compiler_owner in output)==active
        assert (renderer_owner in output)==active
        assert "NATIVE_FLAGS=video_flags-NOTFOUND;core_flags-NOTFOUND" in output
        print("P0_2_SHARED_SPIRV_REAL_CMAKE_GRAPH_PASS",
              "native_release" if active else "desktop",flush=True)

pinned=(ROOT/"vendor/sources/eden/src/shader_recompiler/backend/spirv/spirv_emit_context.cpp").read_text()
native=(ROOT/"vendor/encore-active/ns2-runtime/ampere/shader_recompiler/backend/spirv/spirv_emit_context.cpp").read_text()
marker="        std::array<Id, Info::MAX_INDIRECT_CBUFS> buf_labels;"
start=pinned.index(marker)
end=pinned.index("        return func;",start)+len("        return func;")
reference=pinned[start:end].strip()
area=native.split("void EmitContext::DefineConstantBufferIndirectFunctions(",1)[1]
assert "if (!Shader::Ampere::NativeSpirvCbufBoundsActive()) {" in area
begin=area.index("            std::array<Id, Info::MAX_INDIRECT_CBUFS> buf_labels;")
stop=area.index("            return func;",begin)+len("            return func;")
copy="\n".join(line[4:] for line in area[begin:stop].splitlines()).strip()
assert copy==reference, "Maxwell indirect CBUF emitter drifted from pinned source"
assert "OpSwitch(selector, invalid_label," in area[stop:]
assert "const Id valid_offset{OpULessThan(" in area[stop:]
assert "inline thread_local bool native_spirv_cbuf_bounds_active = false" in (
    ROOT/"vendor/encore-active/ns2-runtime/ampere/shader_recompiler/frontend/ampere/native_indirect_cbuf.h"
).read_text()
print("P0_2_NS1_PINNED_CBUF_PARITY_PASS sparse_maxwell=unchanged native_scope=thread_local",flush=True)

cpm=ROOT/"vendor/sources/eden-cpm"
sources=(
    "shader_recompiler/backend/spirv/spirv_emit_context.cpp",
    "shader_recompiler/backend/spirv/emit_spirv_context_get_set.cpp",
    "shader_recompiler/frontend/ampere/renderer_spirv_bridge.cpp",
    "video_core/ns2_shader_spirv_compile.cpp",
)
native_root=ROOT/"vendor/encore-active/ns2-runtime/ampere"
includes=[
    native_root,
    ROOT/"vendor/encore-active/ns2-runtime/gpu_dispatch",
    ROOT/"vendor/encore-active/ns2-runtime/hle",
    ROOT/"vendor/sources/eden/src",
    ROOT/"vendor/sources/eden/src/dynarmic/src",
    cpm/"fmt/12.1.0/include",
    cpm/"sirit/v1.0.5/include",
    cpm/"spirv-headers/vulkan-sdk-1.4.341.0/include",
    cpm/"vulkanheaders/v1.4.345/include",
]
boost=cpm/"boost/boost-1.90.0/libs"
assert boost.is_dir()
includes.extend(sorted(boost.glob("*/include")))
assert len(includes)>100
compiler=shutil.which("clang++-18") or shutil.which("clang++")
assert compiler, "Clang C++20 required"
cmd=[compiler,"-std=c++20","-fsyntax-only","-Wno-unused-parameter",
     "-DPS5_NATIVE=1","-DFMT_HEADER_ONLY","-DCANNOT_EXPLICITLY_INSTANTIATE",
     *["-I"+str(inc) for inc in includes]]
env=os.environ.copy()
if platform.system()=="Darwin":
    sdk=Path("/Library/Developer/CommandLineTools/SDKs/MacOSX26.5.sdk")
    assert (sdk/"usr/include/c++/v1/__thread/jthread.h").is_file()
    env["SDKROOT"]=str(sdk)
    cmd+=["-nostdinc++","-isystem",str(sdk/"usr/include/c++/v1")]
for relative in sources:
    source=native_root/relative
    assert source.is_file()
    proc=subprocess.run(cmd+["-O0",str(source)],env=env,capture_output=True,
                        text=True,timeout=105)
    assert proc.returncode==0,(relative,proc.stderr[-5500:])
    print("P0_2_REAL_SHARED_SPIRV_OWNER_PASS",relative,flush=True)
print("P0_2_SHARED_SPIRV_COMPILER_SYNTAX_PASS files=4 ns1=preserved gpu_dispatch=not_enabled",flush=True)
