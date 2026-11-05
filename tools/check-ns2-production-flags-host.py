#!/usr/bin/env python3
"""P0 production contract: one native application, zero NS2/DEV build modes.

Checks the selected real sources and launch command. This is not a proof of
PS5 linking, renderer output or guest title compatibility.
"""
from pathlib import Path
import re
import subprocess

ROOT=Path(__file__).resolve().parents[1]
CMAKE=(ROOT/'headless/CMakeLists.txt').read_text()
SCRIPT=(ROOT/'tools/build-headless-native.sh').read_text()
NUP=(ROOT/'headless/nup_v1_runtime.cmake').read_text()

# No selectable experimental/release/DEV program. Hardware capabilities,
# PS5_NATIVE and guest process identities are legitimate technical checks.
for source in (CMAKE,SCRIPT,NUP):
    assert not re.search(r'\bEDEN_NS2_[A-Z0-9_]*EXPERIMENTAL\b',source)
    for option in ('EDEN_DEV_PROFILE','EDEN_DEV_VULKAN',
                   'EDEN_FINAL_RELEASE_PROFILE','EDEN_NS2_NATIVE_EXPERIMENTAL'):
        assert option not in source,option
assert not re.search(r'^\s*option\(EDEN_NS2_',CMAKE,re.M)
assert '"${ns2_cmake_args[@]}"' not in SCRIPT
assert '-DEDEN_PS5_VULKAN=ON' in SCRIPT
assert '-DEDEN_VULKAN_DRIVER=RADV' in SCRIPT
assert 'if(PS5_NATIVE AND (NOT EDEN_PS5_VULKAN OR NOT EDEN_PS5_OPENGL OR' in CMAKE
assert 'NOT EDEN_VULKAN_DRIVER STREQUAL "RADV"' in CMAKE
assert 'include("${CMAKE_CURRENT_LIST_DIR}/nup_v1_runtime.cmake")' in CMAKE
assert 'option(EDEN_NUP_V1_RUNTIME' not in NUP
assert 'EDEN_FINAL_RELEASE_PROFILE' not in NUP
assert NUP.count('target_compile_definitions(eden-headless PRIVATE EDEN_NUP_V1_RUNTIME=1)')==1
assert NUP.count('target_compile_definitions(eden-metadata PRIVATE EDEN_NUP_V1_RUNTIME=1)')==1
assert 'get_target_property(eden_nup_core_sources core SOURCES)' in NUP
assert 'if(NOT eden_nup_match_count EQUAL 1)' in NUP
assert 'target_link_libraries(core PRIVATE libzstd_static ZLIB::ZLIB)' in NUP

for symbol in ('EDEN_SHARED_NS2_EXEFS','EDEN_SHARED_NS2_GUEST_COUNTER',
               'EDEN_SHARED_NS2_GPU_ACCESS_SVC','EDEN_SHARED_NS2_WAIT64',
               'EDEN_SHARED_NS2_AUDIO','EDEN_SHARED_NS2_AMPERE_CORE',
               'EDEN_SHARED_NS2_SPIRV_COMPILER','EDEN_NS2_GPU_SESSION_SOURCE',
               'EDEN_NS2_SUPERVISOR_ROOT','EDEN_NS2_NVDRV_GPU_SOURCE',
               'EDEN_NS2_NATIVE_GPU_PULLER','EDEN_NS2_RASTERIZER_INTERFACE'):
    assert symbol in CMAKE,('missing unified source owner',symbol)
for required in (
  'vendor/encore-active/ns2-runtime/metadata/core/file_sys/program_metadata.cpp',
  'vendor/encore-active/ns2-runtime/metadata/core/loader/loader.cpp',
  'vendor/encore-active/ns2-runtime/metadata/core/loader/nso.cpp',
  'vendor/encore-active/ns2-runtime/cpu6/core/hardware_properties.h',
  'vendor/encore-active/ns2-runtime/nvdrv_gpu/core/hle/service/nvdrv/devices/nvhost_gpu.cpp',
  'vendor/encore-active/ns2-runtime/gpu_session/core/hle/service/am/service/gpu_session.cpp',
  'vendor/encore-active/ns2-runtime/gpu_dispatch/video_core/engines/puller.cpp',
  'vendor/encore-active/ns2-runtime/vulkan_abi/video_core/rasterizer_interface.h',
  'vendor/encore-active/eden-vulkan/vulkan_rasterizer.cpp',
  'headless/jit_memory_policy.h',
):
    assert (ROOT/required).is_file(),required
assert not any((ROOT/'vendor/encore-active/ns2-experimental').rglob('*.*'))
assert 'EDEN_NS2_NATIVE_GPU_DISPATCH' not in CMAKE
assert 'EDEN_NS2_NATIVE_VULKAN' not in CMAKE
rasterizer=(ROOT/'vendor/encore-active/ns2-runtime/vulkan_abi/video_core/rasterizer_interface.h').read_text()
assert 'virtual bool DispatchNativeCompute(const Tegra::NativeComputeLaunch&)' in rasterizer
assert '#ifdef PS5_NATIVE' in rasterizer
assert 'EDEN_NS2_VULKAN_SHADER_BRIDGE_EXPERIMENTAL' not in rasterizer
for producer in (
    'vendor/encore-active/ns2-runtime/gpu_dispatch/video_core/engines/puller.cpp',
    'vendor/encore-active/eden-core/src/video_core/dma_pusher.cpp',
    'vendor/encore-active/ns2-runtime/nvdrv_gpu/core/hle/service/nvdrv/devices/nvhost_gpu.cpp',
):
    owner=(ROOT/producer).read_text()
    assert '#ifdef PS5_NATIVE' in owner

subprocess.run(['bash','-n',str(ROOT/'tools/build-headless-native.sh')],check=True)
subprocess.run(['bash','-n',str(ROOT/'tools/build-package.sh')],check=True)
print('P0_UNIFIED_NATIVE_PROFILE_SOURCE_PASS modes=1 ns1_preserved=1 nup=always gpu_owner=shared no_experimental=1')
