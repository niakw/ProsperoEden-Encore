#!/usr/bin/env python3
"""P0.2 syntax preflight of actual NS2 HLE, NVDRV and Ampere GPU owners.

A host-only source/ABI smoke test; deliberately does not compile PS5-native
rendering, link the console app, or authorize the runtime release flags.
"""
from pathlib import Path
import os, subprocess, concurrent.futures, shutil, sys
r=Path(__file__).resolve().parents[2];deps=r/'vendor/sources/eden-cpm';sdk15=Path('/Library/Developer/CommandLineTools/SDKs/MacOSX15.4.sdk');sdk26=Path('/Library/Developer/CommandLineTools/SDKs/MacOSX26.5.sdk');env=os.environ.copy();env['SDKROOT']=str(sdk15)
inc=['vendor/encore-active/ns2-runtime/kernel_wait64','vendor/encore-active/ns2-runtime/gpu_access_svc','vendor/encore-active/ns2-runtime/gpu_dispatch','vendor/encore-active/ns2-runtime/nvdrv_gpu','vendor/encore-active/ns2-runtime/nvdrv_as','vendor/encore-active/ns2-runtime/gpu_session','vendor/encore-active/ns2-runtime/graphics_supervisor','vendor/encore-active/ns2-runtime/self_controller','vendor/encore-active/ns2-runtime/hle','vendor/encore-active/ns2-runtime/nvdrv','vendor/encore-active/ns2-runtime/ampere','vendor/encore-active/ns2-helpers/include','vendor/sources/eden/src','vendor/sources/fmt/include','vendor/sources/eden/src/dynarmic/src']
inc=[r/i for i in inc]+list((deps/'boost/boost-1.90.0/libs').glob('*/include'))
flags=[shutil.which('clang++') or shutil.which('g++'),'-std=c++20',
       '-fsyntax-only','-Wno-unused-parameter','-DFMT_HEADER_ONLY']
if sys.platform=='darwin' and sdk26.is_dir():
    flags+=['-target','arm64-apple-macos15','-nostdinc++',
            '-isystem',str(sdk26/'usr/include/c++/v1')]
flags+=['-I'+str(i) for i in inc if i.is_dir()]
assert flags[0] and all((r/i).exists() for i in [
    'vendor/encore-active/ns2-runtime/nvdrv_as',
    'vendor/encore-active/ns2-runtime/nvdrv_gpu',
    'vendor/encore-active/ns2-runtime/gpu_dispatch',
    'vendor/encore-active/ns2-runtime/gpu_session',
    'vendor/encore-active/ns2-runtime/graphics_supervisor']), 'Expected pinned NS2 source owners missing'
cmake=(r/'headless/CMakeLists.txt').read_text()
assert 'EDEN_NS2_GPU_SESSION_EXPERIMENTAL' in cmake and 'EDEN_NS2_NVDRV_EXPERIMENTAL' in cmake
assert 'EDEN_NS2_VULKAN_SHADER_BRIDGE_EXPERIMENTAL' in cmake
assert 'if(EDEN_FINAL_RELEASE_PROFILE)' in cmake
assert 'if(${eden_release_flag})' in cmake
sources=['vendor/encore-active/ns2-runtime/nvdrv_as/core/hle/service/nvdrv/devices/nvhost_as_gpu.cpp','vendor/encore-active/ns2-runtime/nvdrv_gpu/core/hle/service/nvdrv/devices/nvhost_gpu.cpp','vendor/encore-active/ns2-runtime/gpu_dispatch/video_core/engines/puller.cpp','vendor/encore-active/ns2-runtime/gpu_session/core/hle/service/am/service/gpu_session.cpp','vendor/encore-active/ns2-runtime/gpu_session/core/hle/service/am/service/gpu_worker.cpp','vendor/encore-active/ns2-runtime/graphics_supervisor/core/hle/service/am/service/graphics_supervisor.cpp']
def run(p):
    owner=r/p
    assert owner.is_file(),p
    o=subprocess.run(flags+[str(owner)],capture_output=True,text=True,env=env,timeout=80)
    return p,o.returncode,o.stderr[-3300:]
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
    results=list(pool.map(run,sources))
for path,rc,err in results:
    print(('PASS' if rc==0 else 'FAIL')+' P0_2_SOURCE_TU '+path,flush=True)
    if rc:print(err[-3100:],file=sys.stderr,flush=True)
assert len(results)==6 and all(rc==0 for _,rc,_ in results), 'P0.2 NS2 native owner syntax failed'
print('P0_2_NATIVE_GPU_BOOT_SOURCES_SYNTAX_PASS 6/6 host_only=1 PS5_build=OFF',flush=True)
