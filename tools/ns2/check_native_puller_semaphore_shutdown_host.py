#!/usr/bin/env python3
"""Execute the genuine native GPU puller Acquire semaphore loop on host.

Tests completed waits, shutdown, and GPU-worker failure against the same
loop as shared NS1. This never claims hardware/GPU-fence completion on PS5.
"""
from __future__ import annotations
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
NATIVE = ROOT/'vendor/encore-active/ns2-runtime/gpu_dispatch/video_core/engines/puller.cpp'
SHARED = ROOT/'vendor/encore-active/eden-core/src/video_core/engines/puller.cpp'
DEV = ROOT/'vendor/encore-active/eden-core/src/video_core/engines/puller_dev.cpp'
START = 'void Puller::ProcessSemaphoreAcquire(DmaPusher& dma_pusher) {'
END = '\n/// Calls a GPU puller method.'


def get_method(path: Path) -> str:
    source = path.read_text()
    assert source.count(START) == 1 and source.count(END) == 1, path
    return START + source.split(START, 1)[1].split(END, 1)[0]

native = get_method(NATIVE)
shared = get_method(SHARED)
assert native == shared, 'NS2 native puller diverged from shipping NS1 wait semantics'
assert '#ifdef PS5_NATIVE\n#include "gpu_failure.h"\n#endif' in NATIVE.read_text()
assert 'IsShuttingDown()' in native and '::Eden::PeekGpuFailure()' in native
# DEV has a timing diagnostic wrapper only; it must retain the same safety checks.
assert 'IsShuttingDown()' in get_method(DEV)
assert '::Eden::PeekGpuFailure()' in get_method(DEV)

cpp = r'''
#include <cassert>
#include <cstdint>
#include <cstdio>
#include <exception>
#include <stdexcept>
using u32 = std::uint32_t;
namespace Eden {
static unsigned checks = 0;
static bool failed = false;
std::exception_ptr PeekGpuFailure() {
    ++checks;
    if (failed) return std::make_exception_ptr(std::runtime_error("worker failed"));
    return {};
}
}
struct SemaphoreAddressRegister {
    constexpr u32 SemaphoreAddress() const { return 0x1234; }
};
struct FakeMemory {
    u32 word = 0;
    unsigned reads = 0;
    template <typename T> T Read(u32 addr) {
        assert(addr == 0x1234);
        ++reads;
        return static_cast<T>(word);
    }
};
struct FakeSystem {
    bool stopping = false;
    bool IsShuttingDown() const { return stopping; }
};
struct DmaPusher;
struct FakeRasterizer {
    DmaPusher* pusher = nullptr;
    unsigned releases = 0;
    unsigned complete_at = 0;
    unsigned stop_at = 0;
    unsigned fail_at = 0;
    void ReleaseFences();
};
struct DmaPusher {
    FakeMemory memory_manager{};
    FakeSystem system{};
    FakeRasterizer* rasterizer = nullptr;
};
void FakeRasterizer::ReleaseFences() {
    ++releases;
    if (complete_at != 0 && releases == complete_at)
        pusher->memory_manager.word = 77;
    if (stop_at != 0 && releases == stop_at)
        pusher->system.stopping = true;
#ifdef PS5_NATIVE
    if (fail_at != 0 && releases == fail_at)
        Eden::failed = true;
#endif
}
class Puller {
public:
    struct Registers {
        SemaphoreAddressRegister semaphore_address{};
        u32 semaphore_acquire = 77;
        bool acquire_active{}, acquire_mode{}, acquire_source{};
        u32 acquire_value{};
    } regs;
    void ProcessSemaphoreAcquire(DmaPusher& dma_pusher);
};
__REAL_METHOD__
int main() {
    FakeRasterizer gpu;
    DmaPusher dma;
    dma.rasterizer = &gpu;
    gpu.pusher = &dma;
    Puller puller;
    // Already satisfied: no needless queue release or failure probe.
    dma.memory_manager.word = 77;
    puller.ProcessSemaphoreAcquire(dma);
    assert(dma.memory_manager.reads == 1 && gpu.releases == 0);
    // The GPU genuinely advances a wait; no artificial success is returned.
    dma.memory_manager.word = 0;
    dma.memory_manager.reads = 0;
    gpu.complete_at = 3;
    puller.ProcessSemaphoreAcquire(dma);
    assert(gpu.releases == 3 && dma.memory_manager.reads == 4);
    assert(puller.regs.acquire_active && puller.regs.acquire_value == 77);
    // An unsatisfied guest wait cannot strand shutdown forever.
    dma.memory_manager.word = 0;
    gpu.complete_at = 0;
    gpu.releases = 0;
    gpu.stop_at = 2;
    puller.ProcessSemaphoreAcquire(dma);
    assert(gpu.releases == 2 && dma.system.stopping);
    gpu.releases = 0;
    const unsigned already_read = dma.memory_manager.reads;
    puller.ProcessSemaphoreAcquire(dma);
    assert(gpu.releases == 0 && dma.memory_manager.reads == already_read + 1);
#ifdef PS5_NATIVE
    // A reported failed worker must propagate before any new GPU release.
    dma.system.stopping = false;
    gpu.stop_at = 0;
    gpu.releases = 0;
    Eden::failed = true;
    const unsigned old_checks = Eden::checks;
    try {
        puller.ProcessSemaphoreAcquire(dma);
        assert(false && "failed worker was swallowed");
    } catch (const std::runtime_error&) { }
    assert(gpu.releases == 0 && Eden::checks == old_checks + 1);
    // Polling is bounded: the second failure check occurs after 64 releases.
    Eden::failed = false;
    gpu.fail_at = 1;
    gpu.releases = 0;
    const unsigned before_delayed_checks = Eden::checks;
    try {
        puller.ProcessSemaphoreAcquire(dma);
        assert(false && "deferred GPU worker failure was swallowed");
    } catch (const std::runtime_error&) { }
    assert(gpu.releases == 64);
    assert(Eden::checks == before_delayed_checks + 2);
    Eden::failed = false;
#endif
    std::puts("P2_7_NATIVE_PULLER_SEMAPHORE_LIVENESS_PASS");
}
'''
# The first-sample test proves propagation. Delayed failure sampling is
# source-checked explicitly to avoid mocking failure into an unrelated class.
assert '(acquire_polls++ & 63u) == 0u' in native


def main() -> None:
    compilers = list(dict.fromkeys(p for p in (
        shutil.which('clang++'), shutil.which('g++')) if p))
    assert compilers, 'C++20 host compiler missing'
    env = os.environ.copy()
    sdk=Path('/Library/Developer/CommandLineTools/SDKs/MacOSX15.4.sdk')
    if sdk.is_dir(): env['SDKROOT'] = str(sdk)
    with tempfile.TemporaryDirectory(prefix='encore-puller-acquire-') as scratch:
        source=Path(scratch)/'semaphore.cpp'
        source.write_text(cpp.replace('__REAL_METHOD__', native))
        for compiler in compilers:
            for native_mode in (False, True):
                for opt in (0, 2):
                    exe=Path(scratch)/f'{Path(compiler).name}-{int(native_mode)}-{opt}'
                    cmd=[compiler,'-std=c++20',f'-O{opt}','-Wall','-Wextra',
                         '-Werror','-fsanitize=undefined','-fno-sanitize-recover=all']
                    if native_mode: cmd.append('-DPS5_NATIVE=1')
                    cmd += [str(source),'-o',str(exe)]
                    build=subprocess.run(cmd,env=env,text=True,capture_output=True,timeout=45)
                    assert build.returncode==0,build.stderr[-3000:]
                    run=subprocess.run([str(exe)],env=env,text=True,capture_output=True,timeout=15)
                    assert run.returncode==0,run.stderr[-3000:]
                    assert 'P2_7_NATIVE_PULLER_SEMAPHORE_LIVENESS_PASS' in run.stdout
                    print('P2_7_NATIVE_SEMAPHORE_HOST_PASS',Path(compiler).name,
                          'O'+str(opt), 'PS5' if native_mode else 'shared',flush=True)


if __name__ == '__main__':
    main()
