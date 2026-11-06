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
               "pending acquire unsupported"):
    assert symbol in puller, symbol
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
