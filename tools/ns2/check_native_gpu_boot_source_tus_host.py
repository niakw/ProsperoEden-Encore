#!/usr/bin/env python3
"""P0.2 syntax preflight of actual NS2 HLE, NVDRV and Ampere GPU owners.

A host-only source/ABI smoke test; deliberately does not compile PS5-native
rendering, link the console app, or authorize the runtime release flags.
"""
from pathlib import Path
import os, subprocess, shutil, sys, tempfile
r=Path(__file__).resolve().parents[2];deps=r/'vendor/sources/eden-cpm';sdk15=Path('/Library/Developer/CommandLineTools/SDKs/MacOSX15.4.sdk');sdk26=Path('/Library/Developer/CommandLineTools/SDKs/MacOSX26.5.sdk');env=os.environ.copy();env['SDKROOT']=str(sdk15)
inc=['vendor/encore-active/eden-sync/overrides/h05-syncpoint','vendor/encore-active/eden-core/overrides/native-tiling','vendor/encore-active/ns2-runtime/kernel_wait64','vendor/encore-active/ns2-runtime/gpu_access_svc','vendor/encore-active/ns2-runtime/gpu_dispatch','vendor/encore-active/ns2-runtime/nvdrv_gpu','vendor/encore-active/ns2-runtime/nvdrv_as','vendor/encore-active/ns2-runtime/gpu_session','vendor/encore-active/ns2-runtime/graphics_supervisor','vendor/encore-active/ns2-runtime/video_decoder','vendor/encore-active/ns2-runtime/self_controller','vendor/encore-active/ns2-runtime/hle','vendor/encore-active/ns2-runtime/nvdrv','vendor/encore-active/ns2-runtime/ampere','vendor/encore-active/ns2-helpers/include','vendor/sources/eden/src','vendor/sources/fmt/include','vendor/sources/eden/src/dynarmic/src']
# Match the one maintained IOCTL header staged into the native CMake include
# overlay. The pinned Eden header lacks the InputCapacity template signature.
ioctl=r/'vendor/encore-active/eden-core/src/core/hle/service/nvdrv/devices/ioctl_serialization.h'
assert ioctl.is_file() and 'template <size_t InputCapacity = 0' in ioctl.read_text()
ioctl_temp=tempfile.TemporaryDirectory(prefix='encore-ioctl-')
ioctl_dest=Path(ioctl_temp.name)/'core/hle/service/nvdrv/devices/ioctl_serialization.h'
ioctl_dest.parent.mkdir(parents=True,exist_ok=True)
shutil.copyfile(ioctl,ioctl_dest)
inc=[Path(ioctl_temp.name),*[r/i for i in inc],*list((deps/'boost/boost-1.90.0/libs').glob('*/include'))]
# The PS5 native NVDRV/AM owners instantiate a large C++20 template graph.
# Ubuntu's Clang 18 frontend has repeatedly crashed while parsing it, even
# when compiled serially. Keep the full six-owner syntax proof on Linux
# using GCC; Clang still checks the other smaller host/native fixtures.
compiler=(shutil.which('g++') if sys.platform=='linux' else None) or shutil.which('clang++') or shutil.which('g++')
flags=[compiler,'-std=c++20',
       '-fsyntax-only','-Wno-unused-parameter','-DFMT_HEADER_ONLY']
if sys.platform=='darwin' and sdk26.is_dir():
    flags+=['-target','arm64-apple-macos15','-nostdinc++',
            '-isystem',str(sdk26/'usr/include/c++/v1')]
flags+=['-I'+str(i) for i in inc if i.is_dir()]
assert flags[0] and all((r/i).exists() for i in [
    'vendor/encore-active/ns2-runtime/vulkan_abi',
    'vendor/encore-active/ns2-runtime/nvdrv_as',
    'vendor/encore-active/ns2-runtime/nvdrv_gpu',
    'vendor/encore-active/ns2-runtime/gpu_dispatch',
    'vendor/encore-active/ns2-runtime/gpu_session',
    'vendor/encore-active/ns2-runtime/graphics_supervisor',
    'vendor/encore-active/ns2-runtime/video_decoder']), 'Expected pinned NS2 source owners missing'
cmake=(r/'headless/CMakeLists.txt').read_text()
assert 'configure_file("${EDEN_MAINTAINED_IOCTL}"' in cmake
# This syntax gate must select the same MemoryManager public header as the
# shipping PS5 graph. The NS2 NVDRV owner calls the syncpoint shim API
# unconditionally, while pinned Eden does not expose that combined shim/tiling ABI.
native_tiling=r/'vendor/encore-active/eden-core/overrides/native-tiling'
selected_mm=native_tiling/'video_core/memory_manager.h'
assert selected_mm.is_file(), 'Shipping native-tiling MemoryManager header missing'
mmh=selected_mm.read_text()
for required in ('void SetNativeSyncpointShim(GPUVAddr address);',
                 'static constexpr u32 NumShimSyncpoints = 192;',
                 'std::atomic<GPUVAddr> native_syncpoint_shim{0};',
                 'void EnableNativeTiling()', 'bool native_tiling{};'):
    assert required in mmh, ('Shipping MemoryManager ABI missing',required)
assert 'EnqueueDeferredCPUWrite' not in mmh, 'Experimental guest-write bridge is not shipping owner'
assert 'target_include_directories(core BEFORE PRIVATE "${EDEN_NS2_NATIVE_TILING_ROOT}")' in cmake
assert 'target_include_directories(video_core BEFORE PRIVATE "${EDEN_NS2_NATIVE_TILING_ROOT}")' in cmake
assert 'EDEN_NS2_GPU_SESSION_SOURCE' in cmake and 'EDEN_NS2_NVDRV_GPU_SOURCE' in cmake
# gpu_session.cpp owns bounded PS5-only command admission telemetry just like
# gpu_worker.cpp and graphics_supervisor.cpp. The 19-Nov artifact audit proved
# that a TU-local definition is required: core does not define PS5_NATIVE
# globally. Keep the real session owner observable in the next native binary.
session_native_flag = '''set_property(SOURCE "${EDEN_NS2_GPU_SESSION_SOURCE}"
        TARGET_DIRECTORY core APPEND PROPERTY COMPILE_DEFINITIONS "PS5_NATIVE=1")'''
worker_native_flag = '''set_property(SOURCE "${EDEN_NS2_GPU_WORKER_SOURCE}"
        TARGET_DIRECTORY core APPEND PROPERTY COMPILE_DEFINITIONS "PS5_NATIVE=1")'''
assert session_native_flag in cmake, 'Selected GPU session lost PS5_NATIVE command telemetry'
assert worker_native_flag in cmake, 'Selected GPU worker lost PS5_NATIVE command telemetry'
assert 'EDEN_NS2_RASTERIZER_INTERFACE' in cmake
# The actual PS5 target must use the same paired NVDRV declaration and
# implementation as this host syntax probe. Otherwise GSV 1402 compiles here
# but fails in the native build against the older pinned Eden class.
native_nvdrv_dir=r/'vendor/sources/eden/src/core/hle/service/nvdrv'
for file in ('nvdrv_interface.h', 'nvdrv_interface.cpp'):
    assert 'InitializeForProcess' in (native_nvdrv_dir/file).read_text(), file
for selected_owner in (
    'set(EDEN_NS2_NVDRV_SESSION_ROOT',
    'configure_file("${EDEN_NS2_NVDRV_SESSION_HEADER}"',
    'list(REMOVE_ITEM eden_ns2_nvdrv_session_sources',
    '"hle/service/nvdrv/nvdrv_interface.cpp")',
    'list(APPEND eden_ns2_nvdrv_session_sources',
    '"${EDEN_NS2_NVDRV_SESSION_SOURCE}")',
    'target_include_directories(core BEFORE PRIVATE "${EDEN_NS2_NVDRV_SESSION_INCLUDE}")',
):
    assert selected_owner in cmake, ('Native NVDRV process-session selection missing', selected_owner)
for forbidden in ('EDEN_NS2_GPU_SESSION_EXPERIMENTAL','EDEN_NS2_NVDRV_EXPERIMENTAL',
                  'EDEN_NS2_VULKAN_SHADER_BRIDGE_EXPERIMENTAL',
                  'EDEN_FINAL_RELEASE_PROFILE'):
    assert forbidden not in cmake
assert 'if(PS5_NATIVE AND EDEN_REVIEWED_DUAL_NPDM)' in cmake
sources=['vendor/encore-active/ns2-runtime/nvdrv_as/core/hle/service/nvdrv/devices/nvhost_as_gpu.cpp','vendor/encore-active/ns2-runtime/nvdrv_gpu/core/hle/service/nvdrv/devices/nvhost_gpu.cpp','vendor/encore-active/ns2-runtime/gpu_dispatch/video_core/engines/puller.cpp','vendor/encore-active/ns2-runtime/gpu_session/core/hle/service/am/service/gpu_session.cpp','vendor/encore-active/ns2-runtime/gpu_session/core/hle/service/am/service/gpu_worker.cpp','vendor/encore-active/ns2-runtime/graphics_supervisor/core/hle/service/am/service/graphics_supervisor.cpp']
def run(p):
    owner=r/p
    assert owner.is_file(),p
    o=subprocess.run(flags+[str(owner)],capture_output=True,text=True,env=env,timeout=80)
    return p,o.returncode,o.stderr[-3300:]
# Six full NVDRV/graphics TUs instantiate substantial C++20 templates.
# On the shared Linux runner, four simultaneous Clang frontends can crash
# before diagnostics are produced. Keep every real owner, but check in
# bounded sequence so compilation failures remain attributable to one TU.
results=[]
for path in sources:
    p,rc,err=run(path)
    results.append((p,rc,err))
    print(('PASS' if rc==0 else 'FAIL')+' P0_2_SOURCE_TU '+p,flush=True)
    if rc:
        print(err[-3100:],file=sys.stderr,flush=True)
        raise AssertionError(('P0.2 native GPU source syntax failed',p,rc))
assert len(results)==6 and all(rc==0 for _,rc,_ in results), 'P0.2 NS2 native owner syntax failed'

# The unified QMD3 puller must compile with the actual PS5 rasterizer ABI:
# earlier desktop-only TU probes did not instantiate DispatchNativeCompute.
# The real Vulkan renderer owns shader capture; no duplicate diagnostic read
# is permitted on the latency-sensitive GPU worker path.
puller = r/'vendor/encore-active/ns2-runtime/gpu_dispatch/video_core/engines/puller.cpp'
body = puller.read_text()
assert body.count('pusher.rasterizer->DispatchNativeCompute(*launch)') == 1
assert 'CaptureNativeComputeShader(' not in body
assert 'EDEN_NS2_COMPUTE_SHADER_CAPTURE' not in body
assert 'if (sample && (!mapped || !release_targets_mapped))' in body
abi = r/'vendor/encore-active/ns2-runtime/vulkan_abi'
native_flags = [
    flags[0], '-I'+str(abi), '-I'+str(r/'headless'),
    *flags[1:], '-DPS5_NATIVE=1']
built = subprocess.run(native_flags+[str(puller)], capture_output=True,
                       text=True, env=env, timeout=95)
assert built.returncode == 0, ('PS5 native QMD3 puller ABI',built.stderr[-3500:])
print('P2_7_NATIVE_QMD3_SINGLE_SHADER_CAPTURE_PASS native_abi=1 dispatch=1 redundancy=0')
# P2.7: compile the REAL DMA cursor and native scheduler implementation
# against the same DmaPusher/Puller headers and PS5-native Rasterizer ABI.
# Checking the Puller alone misses a broken dispatch/resume boundary.
native_gpfifo_owners = [
    r/'vendor/encore-active/eden-core/src/video_core/dma_pusher.cpp',
    r/'vendor/encore-active/ns2-runtime/gpu_dispatch/video_core/control/scheduler.cpp',
    r/'vendor/encore-active/ns2-runtime/gpu_dispatch/video_core/control/channel_state.cpp',
]
# Exact production receipt for the NVN2 split-method continuation fix.
# The actual source TU is compiled below with PS5_NATIVE and the shipping
# native DmaPusher ABI; these source seals prevent a same-pin semantic drift.
import hashlib
dma_owner = native_gpfifo_owners[0]
dma_header = r/'vendor/encore-active/ns2-runtime/gpu_dispatch/video_core/dma_pusher.h'
def git_blob(path):
    raw=path.read_bytes()
    return hashlib.sha1(b'blob '+str(len(raw)).encode()+bytes([0])+raw).hexdigest()
assert git_blob(dma_owner) == 'a8c95c51445ddafc2b8f42a92099359aae33e836'
assert git_blob(dma_header) == '7965c196bff1364f64e747f152bcc314b1db3658'
dma_text=dma_owner.read_text()
dma_header_text=dma_header.read_text()
for token in (
    'native_channel && command_resume_offset == 0',
    'header.addr != split_method_end',
    'header.size != dma_state.method_count',
    'SplitResumesLater(command_list, dma_pushbuffer_subindex + 1)',
    'ResolveSplitMethod(header.addr, park_call)',
    'split_method_end = header.addr + static_cast<GPUVAddr>(header.size) * sizeof(u32)',
    'parked_methods.clear();',
):
    assert token in dma_text, ('NS2 split GPFIFO owner drift',token)
for token in (
    'struct ParkedMethod {',
    'static constexpr std::size_t MaxParkedMethods = 16;',
    'std::vector<ParkedMethod> parked_methods;',
    'GPUVAddr split_method_end{};',
):
    assert token in dma_header_text, ('NS2 split GPFIFO ABI drift',token)
assert dma_text.count('ResolveSplitMethod(') == 2
assert dma_text.count('SplitResumesLater(') == 2
for owner in native_gpfifo_owners:
    assert owner.is_file(), owner
    built = subprocess.run(native_flags + [str(owner)], capture_output=True,
                           text=True, env=env, timeout=95)
    if built.returncode:
        print('P2_7_NATIVE_GPFIFO_SOURCE_TU_FAIL',owner,built.stderr[-4500:],
              file=sys.stderr,flush=True)
        raise AssertionError(('Native GPFIFO source ABI invalid',str(owner)))
    print('P2_7_NATIVE_GPFIFO_SOURCE_TU_PASS',owner,flush=True)
print('P2_7_NATIVE_GPFIFO_DISPATCH_SYNTAX_PASS units=4 host_only=1 m2mf_default=1')
print('P0_2_NATIVE_GPU_BOOT_SOURCES_SYNTAX_PASS 6/6 host_only=1 PS5_build=OFF',flush=True)
