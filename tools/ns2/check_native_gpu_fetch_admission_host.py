#!/usr/bin/env python3
"""P2.7: real live GPFIFO fetch mapping recheck and GPU source TU gate.

DmaPusher reads live command words after NVDRV's earlier ioctl validation.
The two maintained owners revalidate against the current GMMU directly
before GPU dirty checks and SafeRead; reject unmapped spans rather than
replaying them as zero words. Host tests never claim a console GPU fence.
"""
from pathlib import Path
import os
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor

ROOT=Path(__file__).resolve().parents[2]
DMA=ROOT/'vendor/encore-active/eden-core/src/video_core'
NATIVE=ROOT/'vendor/encore-active/ns2-runtime/nvdrv_gpu'
TEST=ROOT/'tools/ns2/test_native_gpu_fetch_admission.cpp'
HELPER=NATIVE/'core/hle/service/nvdrv/devices/native_gpu_fetch_admission.h'
assert HELPER.is_file() and TEST.is_file()
helper=HELPER.read_text()
assert 'words > (native_limit - address) / bytes_per_word' in helper
assert 'std::forward<IsMapped>(is_mapped)(address, words * bytes_per_word)' in helper
assert 'if (words == 0) return true;' in helper
cmake=(ROOT/'headless/CMakeLists.txt').read_text()
assert 'target_compile_definitions(video_core PRIVATE EDEN_NS2_NATIVE_GPU_DISPATCH=1)' in cmake
assert 'set(EDEN_MAINTAINED_GPU_DMA ' in cmake
assert 'set(EDEN_NS2_NVDRV_GPU_ROOT ' in cmake
assert '"${EDEN_NS2_NVDRV_GPU_ROOT}"' in cmake
for name in ('dma_pusher.cpp','dma_pusher_dev.cpp'):
    source=(DMA/name).read_text()
    step=source.split('bool DmaPusher::Step() {',1)[1].split(
        'void DmaPusher::ProcessCommands(',1)[0]
    assert '"core/hle/service/nvdrv/devices/native_gpu_fetch_admission.h"' in source
    assert '#ifdef EDEN_NS2_NATIVE_GPU_DISPATCH' in step
    assert 'NativeGpfifoFetchMapped(' in step
    assert 'memory_manager.IsFullyMappedRange(addr, bytes)' in step
    assert '::Eden::RecordGpuFailure(std::make_exception_ptr(' in step
    assert 'return false;' in step.split('NativeGpfifoFetchMapped(',1)[1].split('if (subchannels[dma_state.subchannel]',1)[0]
    fetch=step.index('NativeGpfifoFetchMapped(')
    assert step.index('dma_state.dma_get = header.addr;') < fetch
    assert fetch < step.index('memory_manager.IsMemoryDirty(') < step.index('ProcessCommands(headers);')
    assert step.index('if (signal_sync && !synced)') < fetch
    assert step.index('::Eden::RecordGpuFailure') < step.index('ProcessCommands(headers);')
    assert 'signal_sync = explicit_sync && user_sync;' in step
    assert 'NativeGpuChannelRegistry::Instance().IsNative(' in step
    assert 'if (header.size > 0) {' in step

compiler=shutil.which('clang++') or shutil.which('g++')
assert compiler
env=os.environ.copy()
sdk15=Path('/Library/Developer/CommandLineTools/SDKs/MacOSX15.4.sdk')
sdk26=Path('/Library/Developer/CommandLineTools/SDKs/MacOSX26.5.sdk')
if sdk15.is_dir():env['SDKROOT']=str(sdk15)
standard=[]
if sys.platform=='darwin' and sdk26.is_dir():
    standard=['-target','arm64-apple-macos15','-nostdinc++',
              '-isystem',str(sdk26/'usr/include/c++/v1')]
with tempfile.TemporaryDirectory(prefix='encore-gpfifo-fetch-') as td:
    for opt in (0,2):
        exe=Path(td)/f'fetch-O{opt}'
        build=subprocess.run([compiler,'-std=c++20',f'-O{opt}','-Wall',
                              '-Wextra','-Werror','-fsanitize=undefined',
                              '-fno-sanitize-recover=all',*standard,
                              '-I'+str(NATIVE),str(TEST),'-o',str(exe)],
                             capture_output=True,text=True,env=env,timeout=70)
        assert build.returncode==0,build.stderr[-3400:]
        run=subprocess.run([str(exe)],capture_output=True,text=True,env=env,timeout=20)
        assert run.returncode==0,run.stderr[-3400:]
        assert 'P2_7_REAL_NATIVE_GPFIFO_FETCH_RECHECK_PASS' in run.stdout
        print('P2_7_GPFIFO_FETCH_RECHECK_UBSAN_PASS',f'O{opt}',flush=True)
    # The real GPU worker and puller units must compile under the NATIVE
    # macro regime; normal host source-only checks do not exercise it.
    deps=ROOT/'vendor/sources/eden-cpm'
    includes=[ROOT/'headless',
              *[ROOT/'vendor/encore-active/ns2-runtime'/n for n in (
                  'kernel_wait64','gpu_access_svc','gpu_dispatch','nvdrv_gpu',
                  'nvdrv_as','gpu_session','graphics_supervisor','self_controller',
                  'hle','nvdrv','ampere')],
              ROOT/'vendor/encore-active/ns2-helpers/include',
              ROOT/'vendor/sources/eden/src',
              ROOT/'vendor/sources/fmt/include',
              ROOT/'vendor/sources/eden/src/dynarmic/src',
              *sorted((deps/'boost/boost-1.90.0/libs').glob('*/include'))]
    inc=['-I'+str(v) for v in includes if v.is_dir()]
    flags=[compiler,'-std=c++20','-fsyntax-only',
           '-Wno-unused-parameter','-DFMT_HEADER_ONLY',
           '-DPS5_NATIVE=1','-DEDEN_NS2_NATIVE_GPU_DISPATCH=1',
           '-DEDEN_NS2_VULKAN_SHADER_BRIDGE_EXPERIMENTAL=1',
           *standard,*inc]
    sources=[DMA/'dma_pusher.cpp',DMA/'dma_pusher_dev.cpp',
             ROOT/'vendor/encore-active/ns2-runtime/nvdrv_as/core/hle/service/nvdrv/devices/nvhost_as_gpu.cpp',
             ROOT/'vendor/encore-active/ns2-runtime/nvdrv_gpu/core/hle/service/nvdrv/devices/nvhost_gpu.cpp',
             ROOT/'vendor/encore-active/ns2-runtime/gpu_dispatch/video_core/engines/puller.cpp',
             ROOT/'vendor/encore-active/ns2-runtime/ampere/video_core/native_shader_capture.cpp',
             ROOT/'vendor/encore-active/ns2-runtime/ampere/video_core/ns2_shader_spirv_compile.cpp']
    def compile_owner(path:Path):
        # The existing development-only performance profiler contains x86
        # pause intrinsics and is not a qualified ARM64 PS5 source. Compile
        # that separate profile on its supported x86 target; the normal
        # shipping DmaPusher is verified with the ARM64 native ABI macros.
        active_flags=flags.copy()
        if path.name=='dma_pusher_dev.cpp' and '-target' in active_flags:
            active_flags[active_flags.index('-target')+1]='x86_64-apple-macos15'
        result=subprocess.run([*active_flags,str(path)],capture_output=True,
                              text=True,env=env,timeout=95)
        return path.name,result
    with ThreadPoolExecutor(max_workers=4) as pool:
        checked=list(pool.map(compile_owner,sources))
    for name,result in checked:
        assert result.returncode==0,(name,result.stderr[-3200:])
        print('P2_7_NATIVE_GPU_REAL_MACRO_TU_PASS',name,flush=True)
    print('P2_7_GPFIFO_NATIVE_FETCH_OWNER_AND_UBSAN_PASS PS5_runtime=P5',flush=True)
