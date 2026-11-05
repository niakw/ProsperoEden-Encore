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
import sys

ROOT=Path(__file__).resolve().parents[2]
CMAKE=(ROOT/"headless/CMakeLists.txt").read_text()
section=CMAKE.split("# P0.2: the native SPIR-V compiler and QMD3 bounds emitter",1)[1].split("# N50: shared native PS5 device-memory",1)[0]
assert 'set(EDEN_SHARED_NS2_SPIRV_COMPILER OFF)' in section
assert 'if(EDEN_SHARED_NS2_AMPERE_CORE)' in section
assert 'if(EDEN_SHARED_NS2_SPIRV_COMPILER)' in section
assert 'EDEN_NS2_VULKAN_SHADER_BRIDGE_EXPERIMENTAL' not in section
assert 'target_sources(video_core PRIVATE "${EDEN_NS2_VULKAN_SHADER_BRIDGE}")' in section
assert 'target_sources(video_core PRIVATE "${EDEN_NS2_NATIVE_GPU_SPIRV_CAPTURE}")' in section
assert 'list(REMOVE_ITEM eden_ns2_shader_sources' in section
assert 'backend/spirv/spirv_emit_context.cpp' in section
assert 'backend/spirv/emit_spirv_context_get_set.cpp' in section
assert 'set_property(TARGET shader_recompiler PROPERTY SOURCES' in section
assert 'configure_file("${EDEN_NS2_RASTERIZER_INTERFACE}"' in section
assert 'EDEN_NS2_NATIVE_VULKAN' not in section

# Exact real CMake configure-only target source graph, shared with P0.2.
owner=root_probe=ROOT/'tools/ns2/check_unified_native_gpu_graph_host.py'
assert owner.is_file()
env=os.environ.copy()
if platform.system()=='Darwin':
    sdk=Path('/Library/Developer/CommandLineTools/SDKs/MacOSX15.4.sdk')
    if sdk.is_dir():env['SDKROOT']=str(sdk)
real=subprocess.run([sys.executable,'-B',str(owner)],cwd=ROOT,env=env,
                    capture_output=True,text=True,timeout=85)
assert real.returncode==0 and 'UNIFIED_NATIVE_GPU_SOURCE_GRAPH_PASS' in real.stdout,(
    real.stdout[-1600:],real.stderr[-2200:])
print('P0_2_UNIFIED_SPIRV_CMAKE_GRAPH_PASS ps5_npdm_owners=1 maxwell=preserved',flush=True)

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
