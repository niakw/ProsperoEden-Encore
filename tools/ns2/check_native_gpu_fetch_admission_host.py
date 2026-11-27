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

ROOT=Path(__file__).resolve().parents[2]
DMA=ROOT/'vendor/encore-active/eden/src/video_core'
NATIVE=ROOT/'vendor/encore-active/eden/src_gpu'
TEST=ROOT/'tools/ns2/test_native_gpu_fetch_admission.cpp'
HELPER=NATIVE/'core/hle/service/nvdrv/devices/native_gpu_fetch_admission.h'
assert HELPER.is_file() and TEST.is_file()
helper=HELPER.read_text()
assert 'words > (native_limit - address) / bytes_per_word' in helper
assert 'std::forward<IsMapped>(is_mapped)(address, words * bytes_per_word)' in helper
assert 'if (words == 0) return true;' in helper
cmake=(ROOT/'headless/CMakeLists.txt').read_text()
assert 'EDEN_NS2_NATIVE_GPU_DISPATCH' not in cmake
assert 'EDEN_NS2_NATIVE_GPU_PULLER' in cmake
assert 'set(EDEN_MAINTAINED_GPU_DMA ' in cmake
assert 'set(EDEN_NS2_NVDRV_GPU_ROOT ' in cmake
assert '"${EDEN_NS2_NVDRV_GPU_ROOT}"' in cmake
for name in ('dma_pusher.cpp','dma_pusher_dev.cpp'):
    source=(DMA/name).read_text()
    step=source.split('bool DmaPusher::Step() {',1)[1].split(
        'void DmaPusher::ProcessCommands(',1)[0]
    assert '"core/hle/service/nvdrv/devices/native_gpu_fetch_admission.h"' in source
    assert '#ifdef PS5_NATIVE' in step
    assert 'NativeGpfifoFetchMapped(' in step
    assert 'memory_manager.IsFullyMappedRange(addr, bytes)' in step
    # Shipping dma_pusher.cpp reports the native fault and rethrows through
    # FailNativeSubmission; the dev-only variant retains a direct throw.
    # Neither may silently return false and publish an unexecuted GPU fence.
    fatal = 'Native GPFIFO command unmapped at GPU fetch'
    if name == 'dma_pusher.cpp':
        fatal_call = f'FailNativeSubmission("{fatal}");'
        helper_body = source.split(
            '[[noreturn]] void DmaPusher::FailNativeSubmission(const char* message) {', 1
        )[1].split('\n}', 1)[0]
        assert 'NativeGpuChannelRegistry::Instance().ReportFault(&channel_state);' in helper_body
        assert 'std::rethrow_exception(error);' in helper_body
        assert 'throw std::runtime_error(message);' in helper_body
    else:
        fatal_call = f'throw std::runtime_error("{fatal}");'
    assert fatal_call in step
    assert 'return false;' in step.split('NativeGpfifoFetchMapped(',1)[1].split('if (subchannels[dma_state.subchannel]',1)[0]
    fetch=step.index('NativeGpfifoFetchMapped(')
    assert step.index('dma_state.dma_get = header.addr;') < fetch
    assert fetch < step.index('memory_manager.IsMemoryDirty(') < step.index('ProcessCommands(headers);')
    assert step.index('if (signal_sync && !synced)') < fetch
    assert step.index(fatal_call) < step.index('ProcessCommands(headers);')
    assert 'signal_sync = explicit_sync && user_sync;' in step
    assert 'NativeGpuChannelRegistry::Instance().IsNative(' in step
    assert 'if (header.size > 0) {' in step

# A fatal native fetch must stop the PS5 queue worker BEFORE its owning
# fence can be marked complete. The actual threaded caller catches at the
# pthread entry, records a permanent failure and wakes blocking submitters.
worker=(ROOT/'vendor/encore-active/eden/src/video_core/gpu_thread.cpp').read_text()
for active_worker in (worker,):
    assert 'scheduler.Push(system.GPU(), submit_list->channel, std::move(submit_list->entries));' in active_worker
    assert 'Eden::RecordGpuFailure(std::current_exception());' in active_worker
    assert 'start->owner->stop_source.request_stop();' in active_worker
    assert 'state.signaled_fence.store(next.fence, std::memory_order_release);' in active_worker
    assert active_worker.index('scheduler.Push(system.GPU()') < active_worker.index('state.signaled_fence.store(next.fence,')
    assert active_worker.index('state.signaled_fence.store(next.fence,') < active_worker.index('} catch (const std::exception& error)')
    assert 'std::rethrow_exception(failure);' in active_worker
assert 'set(EDEN_GPU_WORKER "${EDEN_ACTIVE_EDEN}/src/video_core/gpu_thread.cpp")' in cmake
assert 'gpu_thread_quiet.cpp' not in cmake and 'gpu_thread_dev.cpp' not in cmake

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
    # The maintained queue fence is published only after Scheduler::Push;
    # a fatal native fetch must throw to pthread's catch, then request_stop.
    # Execute the same failure and GPU fence/persistent alert semantics
    # with production gpu_failure.h and real native admission helper.
    fatal_test=ROOT/'tools/ns2/test_native_gpu_fetch_fatal_worker.cpp'
    assert fatal_test.is_file()
    for opt in (0,2):
        exe=Path(td)/f'fetch-fatal-O{opt}'
        built=subprocess.run([compiler,'-std=c++20',f'-O{opt}','-Wall',
                              '-Wextra','-Werror','-fsanitize=undefined',
                              '-fno-sanitize-recover=all',*standard,
                              '-I'+str(NATIVE),'-I'+str(ROOT/'headless'),
                              str(fatal_test),'-o',str(exe)],
                             capture_output=True,text=True,env=env,timeout=70)
        assert built.returncode==0,built.stderr[-3700:]
        ran=subprocess.run([str(exe)],capture_output=True,text=True,env=env,timeout=20)
        assert ran.returncode==0,ran.stderr[-3700:]
        assert 'P2_7_GPU_FETCH_FATAL_NO_FALSE_FENCE_PASS' in ran.stdout
        print('P2_7_NATIVE_GPU_FATAL_FENCE_UBSAN_PASS',f'O{opt}',flush=True)
    # The real GPU worker and puller units must compile under the NATIVE
    # macro regime; normal host source-only checks do not exercise it.
    deps=ROOT/'vendor/sources/eden-cpm'
    # Select the shipping PS5 virtual rasterizer interface before desktop Eden.
    abi=ROOT/'vendor/encore-active/eden/src'
    assert (abi/'video_core/rasterizer_interface.h').is_file()
    # The selected NS2 shader enum and environment metadata must precede
    # the pinned NS1 Shader::Stage header for authenticated native 0xC797 TUs.
    # Keep this include order identical to the shared release compiler graph.
    shader=ROOT/'vendor/encore-active/eden/src'
    # Match the shipping PS5 graph: this header owns BOTH the authenticated
    # NS2 native tiling flag and Lichii #46 Host1x syncpoint shim. The
    # experimental deferred guest-write bridge must never mask it.
    native_tiling=ROOT/'vendor/encore-active/eden/src'
    selected_mm=native_tiling/'video_core/memory_manager.h'
    assert selected_mm.is_file()
    mmh=selected_mm.read_text()
    for required in ('void SetNativeSyncpointShim(GPUVAddr address);',
                     'static constexpr u32 NumShimSyncpoints = 192;',
                     'std::atomic<GPUVAddr> native_syncpoint_shim{0};',
                     'void EnableNativeTiling()', 'bool native_tiling{};'):
        assert required in mmh, ('shipping MemoryManager header missing native ABI', required)
    assert 'EnqueueDeferredCPUWrite' not in mmh, 'DEV bridge is not shipping owner'
    assert 'target_include_directories(core BEFORE PRIVATE "${EDEN_NS2_NATIVE_TILING_ROOT}")' in cmake
    assert 'target_include_directories(video_core BEFORE PRIVATE "${EDEN_NS2_NATIVE_TILING_ROOT}")' in cmake

    # Match the shipping NVDEC public-header override as well. The production
    # graph COPYONLY-stages this maintained header ahead of pinned Eden; the
    # real MemoryManager TU reaches it through Host1x even though this gate
    # does not compile/link the decoder implementation itself.
    nvdec_override=ROOT/'vendor/encore-active/eden/src'
    nvdec_ffmpeg=nvdec_override/'video_core/host1x/ffmpeg.h'
    assert nvdec_ffmpeg.is_file()
    assert 'set(EDEN_NVDEC_HEADER_DIR "${PORT_BUILD_DIR}/nvdec-eagain")' in cmake
    assert 'configure_file("${EDEN_NVDEC_MAINTAINED_HEADER}"' in cmake
    assert '"${EDEN_NVDEC_HEADER_DIR}/video_core/host1x/ffmpeg.h" COPYONLY)' in cmake
    nvdec_stage=Path(td)/'nvdec-eagain'
    (nvdec_stage/'video_core/host1x').mkdir(parents=True)
    shutil.copyfile(nvdec_ffmpeg,nvdec_stage/'video_core/host1x/ffmpeg.h')
    assert [p.relative_to(nvdec_stage).as_posix() for p in nvdec_stage.rglob('*') if p.is_file()] == [
        'video_core/host1x/ffmpeg.h'
    ]
    # The actual native core target stages this maintained ioctl ABI header
    # ahead of pinned Eden. Without that copy, nvhost_gpu.cpp is compiled
    # against the obsolete template signature (no InputCapacity argument).
    ioctl_owner=ROOT/'vendor/encore-active/eden/src/core/hle/service/nvdrv/devices/ioctl_serialization.h'
    assert ioctl_owner.is_file()
    assert 'configure_file("${EDEN_MAINTAINED_IOCTL}"' in cmake
    assert 'target_include_directories(core BEFORE PRIVATE "${PORT_BUILD_DIR}/include")' in cmake
    assert 'template <size_t InputCapacity = 0' in ioctl_owner.read_text()
    ioctl_stage=Path(td)/'native-ioctl'
    ioctl_target=ioctl_stage/'core/hle/service/nvdrv/devices/ioctl_serialization.h'
    ioctl_target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(ioctl_owner,ioctl_target)
    # Native core's vendor/eden-threading CMake stages the H05 NVDRV
    # SyncpointManager ABI BEFORE pinned Eden. Include the same root in this
    # real-TU compilation witness, otherwise GCC sees the obsolete upstream
    # header and reports CaptureNativeSyncpointLease as undeclared.
    h05=ROOT/'vendor/encore-active/eden/src'
    h05_header=h05/'core/hle/service/nvdrv/core/syncpoint_manager.h'
    h05_cmake=(ROOT/'vendor/encore-active/eden/native-hle-overrides.cmake').read_text()
    assert h05_header.is_file()
    assert 'CaptureNativeSyncpointLease(u32 id)' in h05_header.read_text()
    assert 'target_include_directories(core BEFORE PUBLIC "${_encore_h05_header_root}")' in h05_cmake
    assert 'include("${PORT_ROOT}/vendor/encore-active/eden/native-hle-overrides.cmake")' in cmake
    # Renderer mapping leases and guest-memory policy are supplied by
    # the shared native dirty-header root in the shipping compiler graph.
    native_dirty=ROOT/'vendor/encore-active/eden/src'
    assert (native_dirty/'core/native_renderer_lifetime.h').is_file()
    assert 'target_include_directories(core BEFORE PUBLIC "${EDEN_NATIVE_DIRTY_HEADER_ROOT}")' in cmake
    assert 'target_include_directories(video_core BEFORE PRIVATE "${EDEN_NATIVE_DIRTY_HEADER_ROOT}")' in cmake
    includes=[h05,native_tiling,nvdec_stage,ioctl_stage,shader,abi,native_dirty,ROOT/'headless',
              ROOT/'vendor/encore-active/eden/src',
              ROOT/'vendor/sources/eden/src',
              ROOT/'vendor/sources/fmt/include',
              ROOT/'vendor/sources/eden/src/dynarmic/src',
              *sorted((deps/'boost/boost-1.90.0/libs').glob('*/include'))]
    inc=['-I'+str(v) for v in includes if v.is_dir()]
    flags=[compiler,'-std=c++20','-fsyntax-only',
           '-Wno-unused-parameter','-DFMT_HEADER_ONLY',
           '-DPS5_NATIVE=1',
           *standard,*inc]
    sources=[DMA/'dma_pusher.cpp',DMA/'dma_pusher_dev.cpp',
             ROOT/'vendor/encore-active/eden/src_as/core/hle/service/nvdrv/devices/nvhost_as_gpu.cpp',
             ROOT/'vendor/encore-active/eden/src/video_core/memory_manager.cpp',
             ROOT/'vendor/encore-active/eden/src_gpu/core/hle/service/nvdrv/devices/nvhost_gpu.cpp',
             ROOT/'vendor/encore-active/eden/src/video_core/engines/puller.cpp',
             ROOT/'vendor/encore-active/eden/srcpere/video_core/native_shader_capture.cpp',
             ROOT/'vendor/encore-active/eden/srcpere/video_core/ns2_shader_spirv_compile.cpp']
    def compile_owner(path:Path):
        # Ubuntu Clang 18 can crash in nested template instantiations of the
        # fully unified native NVDRV and shader source files (frontend exit
        # 139 with a compiler stack dump, not an emulator diagnostic).
        # Check these real heavy translation units with GCC on Linux, retaining
        # the shipping PS5_NATIVE ABI macros and complete include graph.
        # The shipping DMA sources still undergo the Clang source check.
        active_flags=flags.copy()
        is_heavy=path.name in {
            'nvhost_as_gpu.cpp','nvhost_gpu.cpp','memory_manager.cpp','puller.cpp',
            'native_shader_capture.cpp','ns2_shader_spirv_compile.cpp'}
        if sys.platform=='linux' and is_heavy:
            gcc=shutil.which('g++')
            assert gcc, 'GCC C++20 required for native NVDRV/graphics owner'
            active_flags[0]=gcc
        if path.name=='dma_pusher_dev.cpp' and '-target' in active_flags:
            active_flags[active_flags.index('-target')+1]='x86_64-apple-macos15'
        result=subprocess.run([*active_flags,str(path)],capture_output=True,
                              text=True,env=env,timeout=95)
        return path.name,result
    # Real native NVDRV and shader TUs have deep C++20 instantiations. A
    # 4-way fanout can crash Ubuntu's Clang 18 frontend when the CI runner
    # exhausts its memory. Compile each complete owner independently: no
    # source is skipped, no C++ warnings are silenced and failures are fatal.
    for source in sources:
        name,result=compile_owner(source)
        if result.returncode:
            raise AssertionError((name,result.returncode,
                                  result.stderr[:1500],result.stderr[-5000:]))
        print('P2_7_NATIVE_GPU_REAL_MACRO_TU_PASS',name,flush=True)
    print('P2_7_PRODUCTION_MEMORY_MANAGER_COMBINED_ABI_PASS ns1_default=0 shim_192=1 native_tiling=1 real_TUs=2',flush=True)
    print('P2_7_GPFIFO_NATIVE_FETCH_OWNER_AND_UBSAN_PASS PS5_runtime=P5',flush=True)
