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
    # One real PS5 VFS owner, shared by NS1 and NS2. The 128-entry LRU
    # budget and Mesa's four database parts must ship together.
    active_vfs = read('vendor/encore-active/eden-core/src/core/file_sys/vfs/vfs_real.cpp')
    pinned_vfs = read('vendor/sources/eden/src/core/file_sys/vfs/vfs_real.cpp')
    old_cap = 'constexpr size_t MaxOpenFiles = 8192;'
    ps5_cap = '''// PS5 has a substantially lower *effective* descriptor budget than
// RLIMIT_NOFILE reports. EglantinePS5's MKW/loose RomFS failure (267 real
// handles) was addressed by a 128-reference VFS cache budget together with
// limiting Mesa's multipart cache to four parts. Keep the existing locked
// LRU eviction/reopen machinery and the normal desktop limit.
#if defined(__PROSPERO__)
constexpr size_t MaxOpenFiles = 128;
#else
constexpr size_t MaxOpenFiles = 8192;
#endif'''
    require(pinned_vfs.count(old_cap) == 1 and active_vfs.count(ps5_cap) == 1
            and active_vfs.replace(ps5_cap, old_cap) == pinned_vfs,
            'selected PS5 VFS differs outside the reviewed descriptor-cap hunk')
    require('"file_sys/vfs/vfs_real.cpp"' in CMAKE and
            'list(REMOVE_ITEM core_sources "${eden_vfs_relative}")' in CMAKE and
            'list(APPEND core_sources "${eden_vfs_maintained}")' in CMAKE,
            'native build does not select reviewed VFS file budget')
    startup = read('headless/main.cpp')
    parts = 'setenv("MESA_DISK_CACHE_DATABASE_NUM_PARTS", "4", 0)'
    require(startup.count(parts) == 1 and
            startup.index(parts) < startup.index('setenv("MESA_SHADER_CACHE_DIR"'),
            'Mesa multipart FD limit must precede RADV initialization')
    # PS5 native NS2-only HLE reply peer window, Lichii 9757e3b1.
    selected_ipc = read('vendor/encore-active/eden-threading/src/core/hle/kernel/k_server_session.cpp')
    for marker in ('AllowNs2PeerBeforeHleReply(kernel, client_thread);',
                   'std::chrono::microseconds{50}',
                   '(process->GetProgramId() >> 56) != 0x04',
                   'if (is_hle && !closed && R_SUCCEEDED(client_result)'):
        require(marker in selected_ipc, 'NS2 HLE IPC peer source drift: '+marker)
    require('AllowNs2PeerBeforeHleReply' not in
            read('vendor/sources/eden/src/core/hle/kernel/k_server_session.cpp'),
            'Immutable kernel IPC source changed')
    hle_select = read('vendor/encore-active/eden-threading/native-hle-overrides.cmake')
    require('encore_replace_core_source(\n        "hle/kernel/k_server_session.cpp" "core/hle/kernel/k_server_session.cpp")' in hle_select,
            'Native PS5 CMake does not select NS2 peer owner')
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
    kprocess=read('vendor/encore-active/ns2-runtime/process/core/hle/kernel/k_process.cpp')
    require('if (metadata.IsSwitch2())' in kprocess and
            'm_page_table.GetHeapRegionSize() + m_page_table.GetAliasRegionSize()' in kprocess and
            'm_is_switch2' not in kprocess and
            'set(EDEN_NS2_KPROCESS_SOURCE' in CMAKE and
            'list(REMOVE_ITEM eden_ns2_process_sources "hle/kernel/k_process.cpp")' in CMAKE and
            'list(APPEND eden_ns2_process_sources "${EDEN_NS2_KPROCESS_SOURCE}")' in CMAKE,
            'upstream NS2 KProcess alias-region budget is not the selected owner')
    # Source-scoped PS5 receipt: core is a static archive and never inherits
    # eden-headless PS5_NATIVE. The full CMake selection test below must keep
    # selecting this exact owner; otherwise the guest stack/context markers
    # silently vanish from native logs.
    require('set_property(SOURCE "${EDEN_NS2_KPROCESS_SOURCE}"' in CMAKE and
            'TARGET_DIRECTORY core APPEND PROPERTY COMPILE_DEFINITIONS "PS5_NATIVE=1"' in
            CMAKE.split('set_property(SOURCE "${EDEN_NS2_KPROCESS_SOURCE}"', 1)[1].split(')', 1)[0] and
            '#if defined(PS5_NATIVE)' in kprocess and
            'EDEN_MAIN_STACK_MAP' in kprocess and
            'EDEN_MAIN_THREAD_CONTEXT' in kprocess,
            'selected native KProcess stack/context receipts are not compiled')
    svc=read('vendor/encore-active/ns2-runtime/gpu_access_svc/core/hle/kernel/svc.cpp')
    require('Eden::NS2::GpuAccess::Validate' in svc and
            'target_include_directories(core BEFORE PUBLIC "${EDEN_NS2_GPU_ACCESS_ROOT}")' in CMAKE and
            'EDEN_SHARED_NS2_WAIT64' in CMAKE,
            'shared SVC/Wait64 kernel owner missing')
    memory=read('vendor/encore-active/ns2-runtime/nvdrv_as/core/hle/service/nvdrv/devices/nvhost_as_gpu.cpp')
    require('MapNative4K' in memory and 'UnmapNative4K' in memory,
            '4 KiB native GMMU memory source missing')
    decoder=read('vendor/encore-active/eden-core/src/video_core/textures/decoders.cpp')
    decoder_header=read('vendor/encore-active/eden-core/overrides/native-tiling/video_core/textures/decoders.h')
    memory_header=read('vendor/encore-active/eden-core/overrides/native-tiling/video_core/memory_manager.h')
    pinned_memory_header=read('vendor/sources/eden/src/video_core/memory_manager.h')
    i2m=read('vendor/encore-active/eden-core/src/video_core/engines/engine_upload.cpp')
    blitter=read('vendor/encore-active/eden-core/src/video_core/engines/sw_blitter/blitter.cpp')
    nvhost=read('vendor/encore-active/ns2-runtime/nvdrv_gpu/core/hle/service/nvdrv/devices/nvhost_gpu.cpp')
    channel_state=read('vendor/encore-active/ns2-runtime/gpu_dispatch/video_core/control/channel_state.cpp')
    pinned_decoder_header=read('vendor/sources/eden/src/video_core/textures/decoders.h')
    require('NativeGobOffset' in decoder and
            decoder.count('bool native_tiling')>=8 and
            'bool native_tiling = false' in decoder_header and
            'native_tiling' not in pinned_decoder_header and
            'EnableNativeTiling()' in memory_header and
            'UsesNativeTiling() const' in memory_header and
            'bool native_tiling{};' in memory_header and
            'EnableNativeTiling' not in pinned_memory_header and
            'EnableNativeTiling' not in channel_state and
            'memory_manager.UsesNativeTiling()' in i2m and
            blitter.count('memory_manager.UsesNativeTiling()') == 2,
            'Lichii #2085/#2121 native tiling source contract missing')
    registry_pos=nvhost.index('auto& native_channel_registry = NativeGpuChannelRegistry::Instance();')
    bind_pos=nvhost.index('native_channel_registry.Bind(')
    enable_pos=nvhost.index('channel_state->memory_manager->EnableNativeTiling();')
    require(registry_pos < bind_pos < enable_pos and
            'if (native && (!channel_state->initialized || !channel_state->memory_manager))' in nvhost,
            'NS2 native tiling is not gated by authenticated ready channel admission')
    for token in (
        'set(EDEN_NS2_NATIVE_TILING_ROOT',
        'set(EDEN_NS2_MEMORY_MANAGER_HEADER',
        'set(EDEN_NS2_I2M_UPLOAD',
        'set(EDEN_NS2_SW_BLITTER',
        'target_include_directories(video_core BEFORE PRIVATE "${EDEN_NS2_NATIVE_TILING_ROOT}")',
        'target_include_directories(core BEFORE PRIVATE "${EDEN_NS2_NATIVE_TILING_ROOT}")',
        'list(REMOVE_ITEM video_sources "engines/engine_upload.cpp")',
        'list(APPEND video_sources "${EDEN_NS2_I2M_UPLOAD}")',
        'list(REMOVE_ITEM video_sources "engines/sw_blitter/blitter.cpp")',
        'list(APPEND video_sources "${EDEN_NS2_SW_BLITTER}")',
    ):
        require(token in CMAKE,'Lichii #2085 source owner not selected: '+token)
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
    gamechat=read('vendor/encore-active/ns2-runtime/gamechat/core/hle/service/friend/friend.cpp')
    require('RegisterNamedService("chat:u"' in gamechat and
            'class IChatSession final' in gamechat and 'class IChatService final' in gamechat and
            'EDEN_NS2_GAMECHAT_SOURCE' in CMAKE and
            'list(REMOVE_ITEM eden_ns2_gamechat_sources "hle/service/friend/friend.cpp")' in CMAKE,
            'MKW 1.8.0 GameChat friend service is not selected')
    for command in (601,602,1201,1202,1211,1212,1291):
        require(('{'+str(command)+', &IGraphicsSupervisor::') in supervisor,
                'MKW GameChat/camera GSV command missing: '+str(command))
    require('class INativeChatGsvSession final' in supervisor and
            'class INativeCameraSession final' in supervisor and
            'CalculateChatCameraImageLayout' in supervisor and
            'preference[6] != 0x38' in supervisor and 'ctx.AddMoveObject(client)' in supervisor,
            'MKW GameChat session/image-pool contract incomplete')
    font=read('vendor/encore-active/ns2-runtime/font_service/core/hle/service/ns/platform_service_manager.cpp')
    font_merge=read('vendor/encore-active/ns2-runtime/font_service/core/hle/service/ns/font_merge.cpp')
    for legacy in (
        '{0, D<&IPlatformServiceManager::RequestLoad>, "RequestLoad"}',
        '{1, D<&IPlatformServiceManager::GetLoadState>, "GetLoadState"}',
        '{2, D<&IPlatformServiceManager::GetSize>, "GetSize"}',
        '{3, D<&IPlatformServiceManager::GetSharedMemoryAddressOffset>, "GetSharedMemoryAddressOffset"}',
        '{4, D<&IPlatformServiceManager::GetSharedMemoryNativeHandle>, "GetSharedMemoryNativeHandle"}',
        '{5, D<&IPlatformServiceManager::GetSharedFontInOrderOfPriority>, "GetSharedFontInOrderOfPriority"}',
    ):
        require(legacy in font, 'legacy NS1 pl:u command lost: '+legacy)
    for native in (
        '{2000, &IPlatformServiceManager::GetBuiltInFontSharedMemory',
        '{2010, &IPlatformServiceManager::GetBuiltInFontData',
        '{2020, &IPlatformServiceManager::GetBuiltInFontDataSet',
        '{2100, &IPlatformServiceManager::RequestLoadNxFont',
    ):
        require(native in font, 'NS2 built-in font protocol missing: '+native)
    require('MergeGlyphs(' in font and 'MergeGlyphs(' in font_merge and
            'set(EDEN_NS2_FONT_SERVICE_ROOT' in CMAKE and
            'list(REMOVE_ITEM eden_ns2_font_sources' in CMAKE and
            '"hle/service/ns/platform_service_manager.cpp")' in CMAKE and
            'core/hle/service/ns/font_merge.cpp' in CMAKE and
            'target_include_directories(core BEFORE PRIVATE "${EDEN_NS2_FONT_SERVICE_ROOT}")' in CMAKE,
            'reviewed NS2 font service is not the selected pl:u owner')
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
    # The selected PS5 rasterizer must enforce *live* QMD3 atomics against
    # the reflected storage plan; the compiler-side check is not enough.
    require('Shader::Ampere::NativeQmdAtomicSpansFitBindings(' in raster and
            'compiled.native_atomic_spans.data()' in raster and
            'resources->storage_buffers' in raster and
            'cmdbuf.Dispatch(dim[0], dim[1], dim[2])' in raster,
            'production Vulkan native atomic span admission missing')
    vk_select=read('headless/vulkan.cmake')
    require('file(COPY "${EDEN_ACTIVE_VULKAN}/" DESTINATION "${PORT_BUILD_DIR}")' in vk_select and
            '"${PORT_BUILD_DIR}/vulkan_rasterizer.cpp"' in vk_select,
            'production Vulkan renderer no longer uses maintained source')
    pinned=read('vendor/sources/eden/src/video_core/buffer_cache/buffer_cache_base.h')
    selected=read('vendor/encore-active/eden-core/src/video_core/buffer_cache/buffer_cache_base.h')
    ampere=read('vendor/encore-active/ns2-runtime/shader_resource/include/video_core/buffer_cache/buffer_cache_base.h')
    require('NUM_STORAGE_BUFFERS = 16;' in pinned and
            'NUM_STORAGE_BUFFERS = 32;' in selected and
            'NUM_STORAGE_BUFFERS = 32;' in ampere and
            'static_assert(NUM_STORAGE_BUFFERS <= 32' in selected,
            'selected shared PS5 storage ABI is not the reviewed 32-slot layout')
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
    print('NS1_NS2_UNIFIED_SOURCE_OWNER_PASS cpu6=6 nvdrv=4k qmd=real font=selected i2m_native_tiling=1 blitter_native_tiling=1 tiling_auth=1 nup=always maxwell=unchanged')
