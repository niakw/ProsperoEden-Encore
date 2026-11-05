#!/usr/bin/env python3
"""Unified PS5 source-owner audit (P0.2) for NS1 and NS2.

Audits actual CMake selection, process ownership and ABI contracts. The
historical optional-overlay oracle is preserved in earlier Git revisions;
this check applies to the single current production source graph. Functional
shader/GMMU/NVDRV/IPC assertions are exercised by the separate host tests.
"""
from pathlib import Path
import re
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
CMAKE=(ROOT/'headless/CMakeLists.txt').read_text()
VENDOR=ROOT/'vendor/encore-active'

def require(ok: bool, reason: str) -> None:
    if not ok:
        raise AssertionError(reason)

def read(path: str) -> str:
    p=ROOT/path
    require(p.is_file(),f'missing source owner: {path}')
    return p.read_text()

def check() -> None:
    # No second runtime, switch by TitleID or release/DEV build selector.
    for forbidden in ('EDEN_NS2_VULKAN_SHADER_BRIDGE_EXPERIMENTAL',
                      'EDEN_NS2_NVDRV_EXPERIMENTAL',
                      'EDEN_NS2_GPU_SESSION_EXPERIMENTAL',
                      'EDEN_NS2_CPU6_EXPERIMENTAL',
                      'EDEN_NS2_EXEFS_EXPERIMENTAL',
                      'EDEN_NS2_AMPERE_PROBE_EXPERIMENTAL',
                      'EDEN_FINAL_RELEASE_PROFILE', 'EDEN_DEV_PROFILE',
                      'ns2-experimental/src/'):
        require(forbidden not in CMAKE,f'non-production source selector: {forbidden}')
    require(not re.search(r'^\s*option\(EDEN_NS2_',CMAKE,re.M),
            'alternate NS2 executable profile was reintroduced')
    require('if(PS5_NATIVE AND EDEN_REVIEWED_DUAL_NPDM)' in CMAKE,
            'hardware/NPDM guest-selection boundary missing')
    require('if(PS5_NATIVE AND EDEN_PS5_VULKAN)' in CMAKE,
            'normal Vulkan memory owners missing')
    require('include("${CMAKE_CURRENT_LIST_DIR}/nup_v1_runtime.cmake")' in CMAKE,
            'NUP missing from the single normal content loader')
    require('set(EDEN_SHARED_NS2_EXEFS ON)' in CMAKE and
            'EDEN_NS2_METADATA_OVERLAY' in CMAKE,
            'unified NS1/NS2 ExeFS owner missing')
    for path in (
        'vendor/encore-active/ns2-runtime/metadata/core/file_sys/program_metadata.cpp',
        'vendor/encore-active/ns2-runtime/metadata/core/loader/loader.cpp',
        'vendor/encore-active/ns2-runtime/metadata/core/loader/nso.cpp',
        'vendor/encore-active/ns2-runtime/metadata/core/loader/deconstructed_rom_directory.cpp',
    ):
        read(path)

    # CPU6 and GPU access are runtime properties of the recorded process,
    # not flags that permit native commands for a foreign NS1 owner.
    cpu6=read('vendor/encore-active/ns2-runtime/cpu6/core/hardware_properties.h')
    monitor=read('vendor/encore-active/ns2-runtime/cpu6/dynarmic/interface/exclusive_monitor.h')
    require('NUM_CPU_CORES = 6' in cpu6 and
            'MAX_NUM_CPU_CORES = 6' in monitor and
            'include("${CMAKE_CURRENT_LIST_DIR}/ns2_cpu6_source_bridge.cmake")' in CMAKE,
            'six-core CPU/JIT source graph missing')
    jit=read('headless/jit_memory_policy.h')
    require('A64BaselineBytes(std::size_t core)' in jit and
            'A32BaselineBytes(std::size_t core)' in jit,
            'six-core native JIT fallback is out-of-bounds')
    process=read('vendor/encore-active/ns2-runtime/process/core/hle/service/os/process.cpp')
    require('EDEN_NS2_PROCESS_RUN_GUARD' in process and
            'target_compile_definitions(core PRIVATE EDEN_NS2_PROCESS_RUN_GUARD=1)' in CMAKE,
            'native process Run admission omitted')
    svc=read('vendor/encore-active/ns2-runtime/gpu_access_svc/core/hle/kernel/svc.cpp')
    require('Eden::NS2::GpuAccess::Validate' in svc and
            'target_include_directories(core BEFORE PUBLIC "${EDEN_NS2_GPU_ACCESS_ROOT}")' in CMAKE and
            'EDEN_SHARED_NS2_WAIT64' in CMAKE,
            'shared SVC/Wait64 kernel owner missing')
    memory=read('vendor/encore-active/ns2-runtime/nvdrv_as/core/hle/service/nvdrv/devices/nvhost_as_gpu.cpp')
    require('MapNative4K' in memory and 'UnmapNative4K' in memory,
            '4 KiB native GMMU memory source missing')
    nvdrv=read('vendor/encore-active/ns2-runtime/nvdrv_gpu/core/hle/service/nvdrv/devices/nvhost_gpu.cpp')
    require('ValidateChannelOwner(' in nvdrv and
            nvdrv.count('ValidateChannelOwner(fd, program_id)')>=2 and
            'SubmitGPFIFOImpl' in nvdrv and
            'NativeGpuProcessRegistry' in nvdrv,
            'GPFIFO ownership/range preflight not selected')
    require('EDEN_NS2_NVDRV_GPU_SOURCE' in CMAKE and
            'EDEN_NS2_NVDRV_AS_SOURCE' in CMAKE,
            'the native NVDRV drivers are not selected')
    session=read('vendor/encore-active/ns2-runtime/gpu_session/core/hle/service/am/service/gpu_session.cpp')
    supervisor=read('vendor/encore-active/ns2-runtime/graphics_supervisor/core/hle/service/am/service/graphics_supervisor.cpp')
    require('EDEN_NS2_IPC owner=gpu_session' in session and
            'EDEN_NS2_IPC owner=graphics_supervisor' in supervisor and
            'EDEN_NS2_GPU_SESSION_SOURCE' in CMAKE and
            'EDEN_NS2_SUPERVISOR_ROOT' in CMAKE,
            'IPC native session/VI2 owners missing')
    puller=read('vendor/encore-active/ns2-runtime/gpu_dispatch/video_core/engines/puller.cpp')
    require('NativeGpuChannelRegistry::Instance().IsNative(' in puller and
            'ProcessNativeComputeQmdAt(' in puller and
            'pusher.rasterizer->DispatchNativeCompute(*launch)' in puller and
            'CaptureNativeComputeShader(' not in puller and
            'if (mapped && release_targets_mapped)' in puller,
            'native Ampere QMD3 single-dispatch graph missing or capture duplicated')
    require('EDEN_NS2_NATIVE_GPU_PULLER' in CMAKE and
            'EDEN_SHARED_NS2_AMPERE_CORE' in CMAKE and
            'EDEN_SHARED_NS2_SPIRV_COMPILER' in CMAKE,
            'unified Ampere SPIR-V sources not selected')
    qmd=read('vendor/encore-active/ns2-runtime/gpu_dispatch/video_core/native_qmd.h')
    require('class NativeQmdScheduler' in qmd and
            'std::unordered_map<Address, State> states;' in qmd and
            'NativeQmdReleaseTargetsMapped' in qmd,
            'QMD3 has lost its state and release-target validation')
    header=read('vendor/encore-active/ns2-runtime/vulkan_abi/video_core/rasterizer_interface.h')
    raster=read('vendor/encore-active/eden-vulkan/vulkan_rasterizer.cpp')
    require('virtual bool DispatchNativeCompute(const Tegra::NativeComputeLaunch&)' in header and
            'bool RasterizerVulkan::DispatchNativeCompute(' in raster and
            'CaptureNativeComputeShader(' in raster and
            'if (!captured.Ready()' in raster and
            'configure_file("${EDEN_NS2_RASTERIZER_INTERFACE}"' in CMAKE and
            'EDEN_NS2_NATIVE_VULKAN' not in CMAKE,
            'native compute vtable not unified across core/renderer')
    maxwell=read('vendor/sources/eden/src/video_core/buffer_cache/buffer_cache_base.h')
    ampere=read('vendor/encore-active/ns2-runtime/shader_resource/include/video_core/buffer_cache/buffer_cache_base.h')
    require('NUM_STORAGE_BUFFERS = 16;' in maxwell and
            'NUM_STORAGE_BUFFERS = 32;' in ampere,
            'NS1 Maxwell and NS2 Ampere storage ABIs no longer isolated')
    read('tools/ns2/check_unified_native_gpu_graph_host.py')
    read('tools/ns2/check_unified_jit_cpu6_baseline_host.py')

    # Configure the real selected source lists, not a hand-written substitute.
    proof=subprocess.run([sys.executable,'-B',
                          str(ROOT/'tools/ns2/check_unified_native_gpu_graph_host.py')],
                         cwd=ROOT,capture_output=True,text=True,timeout=80)
    require(proof.returncode==0 and 'UNIFIED_NATIVE_GPU_SOURCE_GRAPH_PASS' in proof.stdout,
            'actual CMake source ownership failed: '+proof.stdout[-1700:]+proof.stderr[-1700:])

if __name__=='__main__':
    try:check()
    except (AssertionError,OSError,subprocess.SubprocessError) as error:
        print('NS1_NS2_UNIFIED_SOURCE_OWNER_FAIL',error,file=sys.stderr)
        sys.exit(1)
    print('NS1_NS2_UNIFIED_SOURCE_OWNER_PASS cpu6=6 nvdrv=4k qmd=real nup=always maxwell=unchanged')
