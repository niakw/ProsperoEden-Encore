#!/usr/bin/env python3
"""P0.2 syntax preflight of actual NS2 HLE, NVDRV and Ampere GPU owners.

A host-only source/ABI smoke test; deliberately does not compile PS5-native
rendering, link the console app, or authorize the runtime release flags.
"""
from pathlib import Path
import os, subprocess, shutil, sys
r=Path(__file__).resolve().parents[2];deps=r/'vendor/sources/eden-cpm';sdk15=Path('/Library/Developer/CommandLineTools/SDKs/MacOSX15.4.sdk');sdk26=Path('/Library/Developer/CommandLineTools/SDKs/MacOSX26.5.sdk');env=os.environ.copy();env['SDKROOT']=str(sdk15)
inc=['vendor/encore-active/ns2-runtime/kernel_wait64','vendor/encore-active/ns2-runtime/gpu_access_svc','vendor/encore-active/ns2-runtime/gpu_dispatch','vendor/encore-active/ns2-runtime/nvdrv_gpu','vendor/encore-active/ns2-runtime/nvdrv_as','vendor/encore-active/ns2-runtime/gpu_session','vendor/encore-active/ns2-runtime/graphics_supervisor','vendor/encore-active/ns2-runtime/video_decoder','vendor/encore-active/ns2-runtime/self_controller','vendor/encore-active/ns2-runtime/hle','vendor/encore-active/ns2-runtime/nvdrv','vendor/encore-active/ns2-runtime/ampere','vendor/encore-active/ns2-helpers/include','vendor/sources/eden/src','vendor/sources/fmt/include','vendor/sources/eden/src/dynarmic/src']
inc=[r/i for i in inc]+list((deps/'boost/boost-1.90.0/libs').glob('*/include'))
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
assert 'EDEN_NS2_GPU_SESSION_SOURCE' in cmake and 'EDEN_NS2_NVDRV_GPU_SOURCE' in cmake
assert 'EDEN_NS2_RASTERIZER_INTERFACE' in cmake
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
print('P0_2_NATIVE_GPU_BOOT_SOURCES_SYNTAX_PASS 6/6 host_only=1 PS5_build=OFF',flush=True)
