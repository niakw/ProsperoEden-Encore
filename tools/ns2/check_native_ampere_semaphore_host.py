#!/usr/bin/env python3
"""Compile maintained Ampere SEM_EXECUTE helper and audit real puller routing."""
from pathlib import Path
import shutil, subprocess, tempfile
ROOT = Path(__file__).resolve().parents[2]
OWNER = ROOT / "vendor/encore-active/ns2-runtime/gpu_dispatch"
puller = (OWNER / "video_core/engines/puller.cpp").read_text()
for symbol in ("ProcessNativeSemaphoreExecute(dma_pusher, method_call.argument)",
               "ProcessSemaphoreRelease(dma_pusher)",
               "ProcessSemaphoreAcquire(dma_pusher)",
               "IsNative(&dma_pusher.channel_state)",
               "pending_native_acquire = PendingNativeAcquire",
               "ResumeNativeAcquire(DmaPusher& dma_pusher)"):
    assert symbol in puller, symbol
# Production P2.7 coherence: initial compare and scheduler retry share the
# same cache-flushing GMMU read, not an out-of-date CPU-side value.
reader = puller.split("static u32 ReadCoherentNativeSemaphore(", 1)[1].split(
    "// Called only by the native GPFIFO scheduler", 1)[0]
native_acquire = puller.split("void Puller::ProcessNativeSemaphoreExecute(", 1)[1].split(
    "void Puller::ProcessSemaphoreAcquire(", 1)[0]
native_resume = puller.split("bool Puller::ResumeNativeAcquire(", 1)[1].split(
    "// 0xC797 Ampere host SEM_EXECUTE", 1)[0]
assert "GpuToCpuAddress(address, sizeof(u32))" in reader
assert 'Ampere SEM_EXECUTE: unmapped acquire address' in reader
assert reader.count("VideoCommon::CacheType::BufferCache") == 2
assert reader.index("MustFlushRegion(") < reader.index("rasterizer->FlushRegion(")
assert reader.index("rasterizer->FlushRegion(") < reader.index("memory_manager.Read<u32>(address)")
assert "ReadCoherentNativeSemaphore(dma_pusher, address)" in native_acquire
assert "ReadCoherentNativeSemaphore(dma_pusher, pending.address)" in native_resume
assert "pending_native_acquire.reset();" in native_resume
assert "return false;" in native_resume
assert "pending acquire unsupported" not in native_acquire
assert "ProcessSemaphoreRelease(dma_pusher);" in puller
assert "ProcessNativeSemaphoreExecute(dma_pusher, method_call.argument);" in puller
# Real P2.7 channel suspension must keep the per-entry cursor, run other GPU
# channels and retry CPU-released waits even when no new queue item arrives.
dma = (ROOT / "vendor/encore-active/eden-core/src/video_core/dma_pusher.cpp").read_text()
dma_header = (OWNER / "video_core/dma_pusher.h").read_text()
scheduler = (OWNER / "video_core/control/scheduler.cpp").read_text()
scheduler_header = (OWNER / "video_core/control/scheduler.h").read_text()
worker = (ROOT / "vendor/encore-active/eden-gpu/gpu_thread_quiet.cpp").read_text()
cmake = (ROOT / "headless/CMakeLists.txt").read_text()
assert "command_resume_offset" in dma and "command_resume_offset" in dma_header
# Header size must not depend on a per-TU PS5_NATIVE macro: core and video_core
# both materialize ChannelState with DmaPusher by value.
assert "#ifdef PS5_NATIVE" not in dma_header
assert 'SOURCE "${EDEN_MAINTAINED_GPU_DMA}"' in cmake
assert 'APPEND PROPERTY COMPILE_DEFINITIONS "PS5_NATIVE=1"' in cmake
assert "commands.subspan(command_resume_offset)" in dma
assert dma.count(".subspan(command_resume_offset)") >= 3
assert "if (HasPendingNativeAcquire())" in dma
assert "ResumeNativeAcquire()" in dma
assert "if (!ResumeNativeAcquire())" in dma
assert "max_write = 1;" in dma
assert "HasPendingNativeChannels" in scheduler_header
assert "ResumePendingNative(GPU& gpu)" in scheduler
assert "pending_native_channels.push_back" in scheduler
assert "pusher.DispatchCalls();" in scheduler
assert "HasPendingNativeChannels()" in worker
assert "scheduler.ResumePendingNative(system.GPU());" in worker
assert "state.queue.TryPop(next)" in worker
assert "control/scheduler.cpp" in cmake and "EDEN_NS2_GPFIFO_SCHEDULER" in cmake
assert "target_include_directories(core BEFORE PRIVATE" in cmake
assert "target_include_directories(video_core BEFORE PRIVATE" in cmake
print("NATIVE_AMPERE_GPFIFO_SUSPEND_RESUME_SOURCE_PASS",flush=True)
code = r"""
#include <cassert>
#include <cstdint>
#include "video_core/engines/native_ampere_semaphore.h"
using namespace Tegra::Engines::NativeSemaphore;
int main() {
  assert(Address(0x10001,0x1043)==0x1000100001040ULL);
  assert(IsAddressAdmissible(Address(0x10001,0x1043)));
  assert(!IsAddressAdmissible(std::uint64_t{1}<<49));
  assert(!IsAddressAdmissible((std::uint64_t{1}<<49)-2));
  assert(AcquireReady(0,3,3)==true && AcquireReady(0,2,3)==false);
  assert(AcquireReady(2,4,3)==true && AcquireReady(2,2,3)==false);
  assert(AcquireReady(3,0,0xffffffffU)==true);
  assert(AcquireReady(3,0xffffffffU,0)==false);
  assert(AcquireReady(4,2,2)==true && AcquireReady(4,4,2)==false);
  assert(AcquireReady(5,4,2)==true && AcquireReady(5,2,2)==false);
  assert(!AcquireReady(1,0,0).has_value());
  assert(!AcquireReady(6,0,0).has_value());
  assert(!AcquireReady(7,0,0).has_value());
}
"""
with tempfile.TemporaryDirectory(prefix="ampere-sem-") as folder:
    source = Path(folder)/"host.cpp"
    source.write_text(code)
    for cc in ("clang++","g++"):
        if not shutil.which(cc): continue
        for opt in ("-O0","-O2"):
            exe = Path(folder)/(cc+opt)
            cmd = [cc,"-std=c++20",opt,"-Wall","-Wextra","-Werror",
                   "-I",str(OWNER),str(source),"-o",str(exe)]
            done=subprocess.run(cmd,capture_output=True,text=True,timeout=50)
            assert done.returncode==0,done.stderr
            done=subprocess.run([str(exe)],capture_output=True,text=True,timeout=8)
            assert done.returncode==0,done.stderr
            print("NATIVE_AMPERE_SEM_EXECUTE_HOST_PASS",cc,opt,flush=True)
print("NATIVE_AMPERE_SEM_EXECUTE_HOST_ONLY_PASS",flush=True)
