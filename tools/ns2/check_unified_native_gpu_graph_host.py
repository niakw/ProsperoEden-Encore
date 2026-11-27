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
# The source archive may predate the header-only TSG device. Verify the real
# common include overlay independently of the Module TU selector.
abi_start = '# PS5 shared NS1/NS2 GPU/NVDRV ABI:'
abi_end = '# The native rasterizer is the reviewed layered-clear implementation'
assert cmake.count(abi_start) == 1 and cmake.count(abi_end) == 1
abi_owner = cmake[cmake.index(abi_start):cmake.index(abi_end)]
stub_relative = 'core/hle/service/nvdrv/devices/nx2_stub_device.h'
module = root/'vendor/sources/eden/src/core/hle/service/nvdrv/nvdrv.cpp'
stub = root/'vendor/sources/eden/src'/stub_relative
assert '#include "' + stub_relative + '"' in module.read_text()
assert stub.is_file() and 'class nx2_stub_device final' in stub.read_text()
assert abi_owner.count(stub_relative) == 1
assert 'set(EDEN_NATIVE_GPU_ABI_ROOT "${PORT_ROOT}/vendor/sources/eden/src")' in abi_owner
assert '"${PORT_BUILD_DIR}/include/${eden_native_gpu_header}" COPYONLY' in abi_owner
assert 'target_include_directories(core BEFORE PRIVATE "${PORT_BUILD_DIR}/include")' in abi_owner
with tempfile.TemporaryDirectory(prefix='encore-unified-gpu-') as directory:
 base=Path(directory);proj=base/'source';proj.mkdir();(proj/'dummy.cpp').write_text('int dummy=0;\n')
 files=['hle/service/nvdrv/devices/nvhost_ctrl_gpu.cpp',
        'hle/service/nvdrv/devices/nvhost_as_gpu.cpp',
        'hle/service/nvdrv/devices/nvhost_gpu.cpp',
        'hle/service/nvdrv/nvdrv_interface.cpp',
        'hle/service/nvdrv/nvdrv.cpp',
        'hle/service/am/service/self_controller.cpp',
        'hle/service/ns/platform_service_manager.cpp',
        'hle/service/friend/friend.cpp',
        'control/scheduler.cpp',
        'control/channel_state.cpp',
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
    hle/service/nvdrv/nvdrv_interface.cpp
    hle/service/nvdrv/nvdrv.cpp
    hle/service/am/service/self_controller.cpp
    hle/service/ns/platform_service_manager.cpp
    hle/service/friend/friend.cpp)
add_library(video_core STATIC "{puller}" dummy.cpp control/scheduler.cpp control/channel_state.cpp)
add_library(shader_recompiler STATIC dummy.cpp
    backend/spirv/spirv_emit_context.cpp
    backend/spirv/emit_spirv_context_get_set.cpp
    backend/spirv/emit_spirv_image.cpp)
# Mirror the real NS1 maintained SampleMask/descriptor owner selection
# before applying the shared NS2 QMD3 replacements.
set(EDEN_NS1_SAMPLE_MASK_ROOT "{root}/vendor/encore-active/eden/src/shader_recompiler")
set(EDEN_NS1_IMAGE_DESCRIPTOR_SOURCE "${{EDEN_NS1_SAMPLE_MASK_ROOT}}/backend/spirv/emit_spirv_image.cpp")
get_target_property(ns1_shader_sources shader_recompiler SOURCES)
foreach(unit IN ITEMS spirv_emit_context.cpp emit_spirv_context_get_set.cpp emit_spirv_image.cpp)
    list(REMOVE_ITEM ns1_shader_sources "backend/spirv/${{unit}}")
    list(APPEND ns1_shader_sources "${{EDEN_NS1_SAMPLE_MASK_ROOT}}/backend/spirv/${{unit}}")
endforeach()
set_property(TARGET shader_recompiler PROPERTY SOURCES "${{ns1_shader_sources}}")
add_library(dynarmic STATIC dummy.cpp)
add_executable(eden-headless dummy.cpp)
'''+owner+abi_owner+'''
if(NOT EXISTS "${PORT_BUILD_DIR}/include/core/hle/service/nvdrv/devices/nx2_stub_device.h")
    message(FATAL_ERROR "Native NVDRV TSG device header missing from selected ABI overlay")
endif()
file(SHA256 "${PORT_BUILD_DIR}/include/core/hle/service/nvdrv/devices/nx2_stub_device.h" stub_selected_sha)
file(SHA256 "${PORT_ROOT}/vendor/sources/eden/src/core/hle/service/nvdrv/devices/nx2_stub_device.h" stub_vendor_sha)
if(NOT stub_selected_sha STREQUAL stub_vendor_sha)
    message(FATAL_ERROR "Native NVDRV TSG header drift")
endif()
get_target_property(selected_core core SOURCES)
list(FIND selected_core "hle/service/nvdrv/nvdrv.cpp" legacy_nvdrv_module)
if(NOT legacy_nvdrv_module EQUAL -1)
    message(FATAL_ERROR "Pinned NVDRV Module compiled beside maintained lifetime owner")
endif()
string(REGEX MATCHALL "vendor/sources/eden/src/core/hle/service/nvdrv/nvdrv[.]cpp"
    native_nvdrv_module_owners "${selected_core}")
list(LENGTH native_nvdrv_module_owners native_nvdrv_module_count)
if(NOT native_nvdrv_module_count EQUAL 1)
    message(FATAL_ERROR "Expected exactly one native NVDRV Module owner")
endif()
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
list(FIND selected_video "control/channel_state.cpp" legacy_channel_state)
if(NOT legacy_channel_state EQUAL -1)
    message(FATAL_ERROR "Pinned channel_state compiled beside native NVK/M2MF owner")
endif()
string(REGEX MATCHALL "ns2-runtime/gpu_dispatch/video_core/control/channel_state\\.cpp"
    native_channel_state_owners "${selected_video}")
list(LENGTH native_channel_state_owners native_channel_state_count)
if(NOT native_channel_state_count EQUAL 1)
    message(FATAL_ERROR "Expected exactly one native NVK/M2MF channel_state owner")
endif()
foreach(needle IN ITEMS
    "ns2-runtime/nvdrv_gpu/" "ns2-runtime/nvdrv_as/"
    "ns2-runtime/gpu_session/" "ns2-runtime/graphics_supervisor/")
    string(FIND "${selected_core}" "${needle}" found)
    if(found LESS 0)
        message(FATAL_ERROR "Missing unified native core owner: ${needle}: ${selected_core}")
    endif()
endforeach()
# Model Eden's real legacy pl:u owner too: the release selector must remove
# that relative TU and install exactly one maintained NS2/NS1-compatible owner.
list(FIND selected_core "hle/service/ns/platform_service_manager.cpp" legacy_pl_u)
if(NOT legacy_pl_u EQUAL -1)
    message(FATAL_ERROR "Pinned pl:u owner compiled beside maintained font service")
endif()
string(REGEX MATCHALL
    "ns2-runtime/font_service/core/hle/service/ns/platform_service_manager\\.cpp"
    native_pl_u_owners "${selected_core}")
list(LENGTH native_pl_u_owners native_pl_u_count)
if(NOT native_pl_u_count EQUAL 1)
    message(FATAL_ERROR "Expected exactly one maintained pl:u owner")
endif()
string(REGEX MATCHALL
    "ns2-runtime/font_service/core/hle/service/ns/font_merge\\.cpp"
    native_font_merge_owners "${selected_core}")
list(LENGTH native_font_merge_owners native_font_merge_count)
if(NOT native_font_merge_count EQUAL 1)
    message(FATAL_ERROR "Expected exactly one native font merge owner")
endif()
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
