#!/usr/bin/env python3
"""Configure the real unified native GPU selector into synthetic host targets.

This checks exact source ownership and ABI boundaries, not PS5 linking or
Switch 2 framebuffer output. Tests must not change the production graph.
"""
from pathlib import Path
import os,subprocess,tempfile
root=Path(__file__).resolve().parents[2]
cmake=(root/'headless/CMakeLists.txt').read_text()
for forbidden in (
        'option(EDEN_NS2_SPARSE_CACHE_PROBE_EXPERIMENTAL',
        'option(EDEN_NS2_EXEFS_EXPERIMENTAL',
        'option(EDEN_NS2_A64_EXPERIMENTAL',
        'option(EDEN_NS2_CPU6_EXPERIMENTAL',
        'option(EDEN_NS2_NVDRV_EXPERIMENTAL',
        'option(EDEN_NS2_GPU_SESSION_EXPERIMENTAL',
        'option(EDEN_NS2_GRAPHICS_SUPERVISOR_EXPERIMENTAL',
        'option(EDEN_NS2_AMPERE_PROBE_EXPERIMENTAL',
        'option(EDEN_NS2_VULKAN_SHADER_BRIDGE_EXPERIMENTAL',
        'option(EDEN_DEV_PROFILE',
        'EDEN_FINAL_RELEASE_PROFILE',
        'if(EDEN_DEV_VULKAN)',
        'if(EDEN_NS2_VULKAN_SHADER_BRIDGE_EXPERIMENTAL)',
):
    assert forbidden not in cmake, f'Build profile still selects a second program: {forbidden}'
assert cmake.count('include("${CMAKE_CURRENT_LIST_DIR}/nup_v1_runtime.cmake")') == 1
assert 'EDEN_NUP_V1_RUNTIME=1' in (root/'headless/nup_v1_runtime.cmake').read_text()
start='# The native GPU-characteristics IOCTL owner is additive:'
end='# N50: shared native PS5 device-memory contiguous page-run safety.'
assert cmake.count(start)==1 and cmake.count(end)==1
owner=cmake[cmake.index(start):cmake.index(end)]
assert 'EDEN_NS2_AMPERE_PROBE_EXPERIMENTAL' not in owner
assert 'EDEN_NS2_NATIVE_VULKAN' not in owner
assert 'EDEN_NS2_GPU_SESSION_SOURCE' in owner
assert 'EDEN_NS2_NVDRV_GPU_SOURCE' in owner
assert 'EDEN_NS2_NATIVE_GPU_DISPATCH' not in owner
with tempfile.TemporaryDirectory(prefix='encore-unified-gpu-') as directory:
 base=Path(directory);proj=base/'source';proj.mkdir();(proj/'dummy.cpp').write_text('int dummy=0;\n')
 files=['hle/service/nvdrv/devices/nvhost_ctrl_gpu.cpp',
        'hle/service/nvdrv/devices/nvhost_as_gpu.cpp',
        'hle/service/nvdrv/devices/nvhost_gpu.cpp',
        'hle/service/am/service/self_controller.cpp',
        'control/scheduler.cpp',
        'backend/spirv/spirv_emit_context.cpp',
        'backend/spirv/emit_spirv_context_get_set.cpp',
        'backend/spirv/emit_spirv_image.cpp']
 for f in files:
  path=proj/f;path.parent.mkdir(parents=True,exist_ok=True);path.write_text('int fake=0;\n')
 puller=root/'vendor/encore-active/eden-core/src/video_core/engines/puller.cpp'
 assert puller.is_file(),puller
 body=f'''cmake_minimum_required(VERSION 3.24)
project(UnifiedGpuOwners LANGUAGES CXX)
set(PORT_ROOT "{root}")
set(EDEN_PORT_DIR "{root}/headless")
set(PORT_BUILD_DIR "{base}/derived")
set(EDEN_NS2_CORE_HELPERS "{root}/vendor/encore-active/ns2-helpers/include")
set(EDEN_MAINTAINED_GPU_PULLER "{puller}")
set(PS5_NATIVE ON)
set(EDEN_PS5_VULKAN ON)
set(EDEN_REVIEWED_DUAL_NPDM ON)
set(EDEN_SHARED_NS2_AM ON)
set(EDEN_SHARED_NS2_GPU_ACCESS_SVC ON)
add_library(core STATIC dummy.cpp
    hle/service/nvdrv/devices/nvhost_ctrl_gpu.cpp
    hle/service/nvdrv/devices/nvhost_as_gpu.cpp
    hle/service/nvdrv/devices/nvhost_gpu.cpp
    hle/service/am/service/self_controller.cpp)
add_library(video_core STATIC "{puller}" dummy.cpp control/scheduler.cpp)
add_library(shader_recompiler STATIC dummy.cpp
    backend/spirv/spirv_emit_context.cpp
    backend/spirv/emit_spirv_context_get_set.cpp
    backend/spirv/emit_spirv_image.cpp)
add_library(dynarmic STATIC dummy.cpp)
add_executable(eden-headless dummy.cpp)
'''+owner+'''
get_target_property(selected_core core SOURCES)
get_target_property(selected_video video_core SOURCES)
get_target_property(selected_shader shader_recompiler SOURCES)
get_target_property(core_definitions core COMPILE_DEFINITIONS)
get_target_property(video_definitions video_core COMPILE_DEFINITIONS)
# The fixture has to model Eden's real relative scheduler owner. The
# production selector then MUST replace, not append alongside, that TU.
list(FIND selected_video "control/scheduler.cpp" legacy_scheduler)
if(NOT legacy_scheduler EQUAL -1)
    message(FATAL_ERROR "Pinned GPFIFO scheduler compiled beside native scheduler")
endif()
string(REGEX MATCHALL "ns2-runtime/gpu_dispatch/video_core/control/scheduler\\.cpp"
    native_scheduler_owners "${selected_video}")
list(LENGTH native_scheduler_owners native_scheduler_count)
if(NOT native_scheduler_count EQUAL 1)
    message(FATAL_ERROR "Expected exactly one native GPFIFO scheduler owner")
endif()
foreach(needle IN ITEMS
    "ns2-runtime/nvdrv_gpu/" "ns2-runtime/nvdrv_as/"
    "ns2-runtime/gpu_session/" "ns2-runtime/graphics_supervisor/")
    string(FIND "${selected_core}" "${needle}" found)
    if(found LESS 0)
        message(FATAL_ERROR "Missing unified native core owner: ${needle}: ${selected_core}")
    endif()
endforeach()
foreach(needle IN ITEMS "ns2-runtime/gpu_dispatch/" "ns2-runtime/ampere/")
    string(FIND "${selected_video}" "${needle}" found)
    if(found LESS 0)
        message(FATAL_ERROR "Missing unified native video owner: ${needle}")
    endif()
endforeach()
if(core_definitions MATCHES "EDEN_NS2_NATIVE_VULKAN" OR
   video_definitions MATCHES "EDEN_NS2_NATIVE_VULKAN" OR
   video_definitions MATCHES "EDEN_NS2_NATIVE_GPU_DISPATCH")
    message(FATAL_ERROR "Native GPU ABI still depends on a build-mode switch")
endif()
list(FIND selected_shader "backend/spirv/spirv_emit_context.cpp" legacy_emitter)
list(FIND selected_shader "backend/spirv/emit_spirv_context_get_set.cpp" legacy_direct)
list(FIND selected_shader "backend/spirv/emit_spirv_image.cpp" legacy_image)
if(NOT selected_shader MATCHES "ns2-runtime/ampere/" OR
   NOT selected_shader MATCHES "ns2-runtime/ampere/shader_recompiler/backend/spirv/emit_spirv_image.cpp" OR
   NOT legacy_emitter EQUAL -1 OR NOT legacy_direct EQUAL -1 OR
   NOT legacy_image EQUAL -1)
    message(FATAL_ERROR "SPIR-V QMD3 owner not installed exactly once")
endif()
# C02 source has a unique exact owner; the fixture also supplies EDEN_PORT_DIR.
string(FIND "${selected_shader}" "/headless/c02_spirv_fragcolor_ps5.cpp" c02_selected_idx)
if(c02_selected_idx LESS 0)
    message(FATAL_ERROR "C02 shared fragment source owner not selected")
endif()
if(NOT EXISTS "${PORT_BUILD_DIR}/include/video_core/rasterizer_interface.h")
    message(FATAL_ERROR "Unified RasterizerInterface ABI not generated")
endif()
message(STATUS "UNIFIED_NATIVE_GPU_SOURCE_GRAPH_PASS core=${selected_core}")
'''
 (proj/'CMakeLists.txt').write_text(body)
 env=os.environ.copy();sdk=Path('/Library/Developer/CommandLineTools/SDKs/MacOSX15.4.sdk')
 if sdk.is_dir():env['SDKROOT']=str(sdk)
 cmd=['cmake','-S',str(proj),'-B',str(base/'build')]
 if sdk.is_dir():cmd.append(f'-DCMAKE_OSX_SYSROOT={sdk}')
 run=subprocess.run(cmd,capture_output=True,text=True,env=env,timeout=70)
 if run.returncode:
  print('UNIFIED_NATIVE_GPU_SOURCE_GRAPH_FAIL',run.stdout[-1600:],run.stderr[-4000:])
 else:
  print('UNIFIED_NATIVE_GPU_SOURCE_GRAPH_PASS NVDRV GPFIFO GPU_SESSION VI2 AMPERE SPIRV ONE_ABI')
 raise SystemExit(run.returncode)
