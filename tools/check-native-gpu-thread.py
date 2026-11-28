#!/usr/bin/env python3
"""Exercise the actual native lifecycle and verify the generated worker body is preserved."""
from pathlib import Path
import subprocess
import sys
import tempfile

from ci.ps5_g21_gpu_shutdown_receipt import (
    REVIEWED, OLD_OPENGL, normalize_g21_shutdown_source,
)

root = Path(__file__).resolve().parents[1]

def verify_g21_teardown():
    """Require current reviewed GPU lifetime fix; replay historic receipt only in memory."""
    owner_dir = root / 'vendor/encore-active/eden/src/video_core'
    normalized = {}
    for name in REVIEWED:
        source = (owner_dir / name).read_text()
        historical, corrected = normalize_g21_shutdown_source(name, source)
        assert corrected, ('Missing reviewed G21 renderer-before-channels fix', name)
        # Full byte/hash and ordering verification lives in the reviewed receipt.
        # Explicitly retain the GL MakeCurrent/Finish contract on every GL owner.
        if name != 'gpu_vulkan.cpp':
            destructor = source.split('    ~Impl() {', 1)[1].split(
                '    std::shared_ptr<Control::ChannelState> CreateChannel(', 1)[0]
            assert destructor.index('NotifyShutdown();') < destructor.index('gpu_thread.Stop();') < (
                destructor.index('renderer->Context().MakeCurrent();')) < destructor.index('glFinish();') < (
                destructor.index('renderer.reset();'))
            assert OLD_OPENGL in historical
        normalized[name] = historical
    print('GPU_G21_CURRENT_SHUTDOWN_SOURCE_PASS owners=5 historic_parity=1 renderer_before_channels=1')
    return normalized

reviewed_g21 = verify_g21_teardown()
native_pending_wait = """            if (scheduler.HasPendingNativeChannels()) {
                // CPU writes may satisfy a semaphore even without a new GPU
                // submission; retry without blocking the command queue.
                scheduler.ResumePendingNative(system.GPU());
                if (!state.queue.TryPop(next)) {
                    Eden::LoadingTick(renderer, true);
                    std::this_thread::sleep_for(std::chrono::milliseconds(1));
                    continue;
                }
            } else if (Eden::LoadingTick(renderer, false)) {
                if (!state.queue.TryPop(next)) {
                    Eden::LoadingTick(renderer, true);
                    std::this_thread::sleep_for(std::chrono::milliseconds(1));
                    continue;
                }
            } else {
                state.queue.PopWait(next, stop_token);
            }"""
# The native build requires both renderers; the common GPU owner is selected by the GL branch.
cmake = (root / "headless/CMakeLists.txt").read_text()
assert 'set(EDEN_MAINTAINED_G21_GPU "${EDEN_G21_GPU_ROOT}/gpu_gl_native.cpp")' in cmake
owner = (root / "vendor/encore-active/eden/src/video_core/gpu_gl_native.cpp").read_text()
release = owner.split("void ReleaseChannel(Control::ChannelState& to_release) {", 1)[1].split("/// Binds a renderer", 1)[0]
assert "gpu_thread.RetireChannelAtBoundary(" in release
assert "scheduler.RetireChannel(owner.get());" in release
assert "RequestSyncOperation(" not in release and "WaitForSyncOperation(" not in release
assert release.index("scheduler.RetireChannel(owner.get());") < release.index("std::scoped_lock lock{channel_mutex};")
assert "last_sync_fence.load(std::memory_order_acquire)" in owner
assert "std::make_shared<std::vector<u8>>()" in owner
if sys.argv[1:] == ['--source-only']:
    # Validate the maintained compiled worker without requiring a PS5 SDK,
    # generated cache or host C++ compilation.
    native = (root / 'vendor/encore-active/eden/src/video_core/gpu_thread.cpp').read_text()
    assert native.count(native_pending_wait) == 1, (
        'Maintained release GPU worker lost native-channel wake/idle arbitration')
    assert native.count('::Eden::PublishGpuSubmissionSample(count);') == 1, (
        'Maintained release GPU worker lost sampled submission breadcrumb')
    print('GPU_NATIVE_CHANNEL_LOADING_WAIT_SOURCE_PASS submit_sample=1')
    raise SystemExit(0)

cache = Path((root / '.local/headless-cache').read_text().strip())
upstream = cache / 'source/src'
source = (upstream / 'video_core/gpu_thread.cpp').read_text()
maintained_worker = root / 'vendor/encore-active/eden/src/video_core/gpu_thread.cpp'
worker = maintained_worker.read_text()

# The canonical architecture compiles the maintained worker directly. Older
# native build caches may still contain an unreferenced headless/gpu_thread.cpp
# from the retired generated-source layout; never use that stale file as the
# source oracle. Verify the actual Ninja compile edge instead.
ninja = (cache / 'native-local/build.ninja').read_text()
gpu_edges = [
    line for line in ninja.splitlines()
    if line.startswith('build ') and 'gpu_thread.cpp.o:' in line
]
assert len(gpu_edges) == 1, ('expected one native GPU worker compile edge', gpu_edges)
gpu_input = gpu_edges[0].split(':', 1)[1]
canonical_worker = str(maintained_worker.resolve())
assert canonical_worker in gpu_input or 'vendor/encore-active/eden/src/video_core/gpu_thread.cpp' in gpu_input, (
    'native build graph does not compile canonical GPU worker', gpu_edges[0])
assert 'native-local/headless/gpu_thread.cpp' not in gpu_input, (
    'retired generated GPU worker still selected by native build graph', gpu_edges[0])
print('GPU_NATIVE_BUILD_GRAPH_OWNER_PASS owner=canonical generated_cache_ignored=1')
body = source.split('thread = std::jthread([&](std::stop_token stop_token) {', 1)[1].split('\n    });', 1)[0]
dispatch_call = '                scheduler.Push(system.GPU(), submit_list->channel, std::move(submit_list->entries));'
development = 'EDEN_DEV_PROFILE:BOOL=ON' in (cache / 'native-local/CMakeCache.txt').read_text()
for call, timer, indent in (
    (dispatch_call, 'dispatch_timer(::Eden::Performance::gpu_dispatch)', '                '),
    ('            state.queue.PopWait(next, stop_token);',
     'idle_timer(::Eden::Performance::gpu_queue_wait)', '            '),
):
    wrapped = indent + '{ ::Eden::Performance::DiagnosticTimer ' + timer + ';\n' + call + '\n' + indent + '}'
    assert worker.count(wrapped) == int(development)
    worker = worker.replace(wrapped, call)

trace_when = 'count <= 3 || ::Eden::Performance::BootTrace()' if development else 'count <= 3'
dispatch_trace = ('                const auto count = ++dispatches;\n'
                  '                ::Eden::PublishGpuSubmissionSample(count);\n'
                  f'                if ({trace_when}) LOG_INFO(Render_OpenGL, "EDEN_GPU_DISPATCH_BEGIN count={{}}", count);\n'
                  + dispatch_call + '\n'
                  f'                if ({trace_when}) LOG_INFO(Render_OpenGL, "EDEN_GPU_DISPATCH_END count={{}}", count);')
assert worker.count(dispatch_trace) == 1
untraced = worker.replace(dispatch_trace, dispatch_call).replace('        unsigned dispatches = 0;\n', '')
# R293 diagnostic-only timers wrap the other three GPU worker command types.
# Restore original calls when comparing the generated worker to pinned Eden.
for metric, call in (
    ('gpu_command_tick', '                system.GPU().TickWork();'),
    ('gpu_command_flush', '                renderer.ReadRasterizer()->FlushRegion(flush->addr, flush->size);'),
    ('gpu_command_invalidate',
     '                renderer.ReadRasterizer()->OnCacheInvalidation(invalidate->addr, invalidate->size);'),
):
    wrapped = ('                { ::Eden::Performance::DiagnosticTimer category_timer('
               '::Eden::Performance::' + metric + ');\n' + call + '\n                }')
    assert untraced.count(wrapped) == int(development)
    untraced = untraced.replace(wrapped, call)
# The producer is outside the upstream worker body. Compare its complete
# compiled TU to the selected maintained source, including failure propagation
# and acquire loads, rather than normalizing an obsolete relaxed-load fragment.
# The maintained source above is the exact translation unit selected by the
# native build graph; no generated C++ parity file participates anymore.
producer = worker.split('u64 ThreadManager::PushCommand(', 1)[1].split('\n} // namespace', 1)[0]
assert producer.count('TryEmplace(') == 1
assert producer.count('EmplaceWaitWithStopToken(') == 1
assert producer.count('Eden::PeekGpuFailure()') == 2
assert 'std::memory_order_relaxed' not in producer
loading_wait = """            if (Eden::LoadingTick(renderer, false)) {
                if (!state.queue.TryPop(next)) {
                    Eden::LoadingTick(renderer, true);
                    std::this_thread::sleep_for(std::chrono::milliseconds(1));
                    continue;
                }
            } else {
            state.queue.PopWait(next, stop_token);
            }"""
wait_pattern = loading_wait if development else native_pending_wait
assert untraced.count(wait_pattern) == 1, ('native GPU channel/loading queue arbitration changed')
untraced = untraced.replace(wait_pattern, '            state.queue.PopWait(next, stop_token);')
# The native crash-only breadcrumb is coarse (one relaxed atomic per 64
# completed GPU commands); strip it solely for the upstream-body comparison.
progress_marker = (
    '            // Release publishes completed GPU work to acquire-side fence readers.\n'
    '            state.signaled_fence.store(next.fence, std::memory_order_release);\n'
    '            if ((++completed_gpu_commands & 63u) == 0u)\n'
    '                ::Eden::Crash::gpu_completed_commands.fetch_add(64, std::memory_order_relaxed);'
)
assert untraced.count(progress_marker) == 1
# Normalize the maintained release-store fast path to the pinned seq_cst
# publication only for this legacy full-body parity oracle. The separate
# source-extracted concurrency fixture verifies its acquire/release protocol.
untraced = untraced.replace(progress_marker, '            state.signaled_fence.store(next.fence);')
assert untraced.count('        unsigned completed_gpu_commands = 0;\n') == 1
untraced = untraced.replace('        unsigned completed_gpu_commands = 0;\n', '')
retire_branch = ('            } else if (auto* retire = std::get_if<RetireChannelCommand>(&next.data)) {\n'
                 '                // Unlike TickWork from a draw, this is outside all dispatch leases.\n'
                 '                retire->action();\n')
assert untraced.count(retire_branch) == 1
untraced = untraced.replace(retire_branch, '', 1)
# Replay only the GPU completion lock split on the historical audit copy.
# The real selected method is compiled by the FIFO saturation witness.
notify_current = """                // The producer may hold write_lock while the FIFO is full.
                // Never acquire it here: only this separate completion mutex
                // participates in the wait/notify handshake.
                std::scoped_lock lk{state.completion_lock};"""
notify_old = """                // We have to lock the write_lock to ensure that the condition_variable wait not get a
                // race between the check and the lock itself.
                std::scoped_lock lk{state.write_lock};"""
assert untraced.count(notify_current) == 1
untraced = untraced.replace(notify_current, notify_old, 1)
assert body in untraced, 'GPU worker semantics changed beyond reviewed dispatch-boundary retirement and startup wait'

assert 'stop_source.get_token()' in worker and 'thread.get_stop_token()' not in worker
assert 'ThreadManager::~ThreadManager() { Stop(); }' in worker
gpu = (root / 'vendor/encore-active/eden/src' / ('video_core/gpu_gl_native_dev.cpp' if development else 'video_core/gpu_gl_native.cpp')).read_text()
assert 'GPU::~GPU() { impl->NotifyShutdown(); }' in gpu
shutdown = gpu.split('    void NotifyShutdown() {', 1)[1].split('    /// Obtain', 1)[0]
assert 'sync_cv.notify_all();\n        }\n        gpu_thread.Stop();' in shutdown
assert shutdown.index('gpu_thread.Stop();') < shutdown.index('sync_requests.clear();') < shutdown.index('sync_requests_stopped = true;')
# The historic one-line destructor is checked only after exact G21 receipt replay.
# Keep the real source for all current shutdown/worker ordering checks above.
selected_gpu_name = 'gpu_gl_native_dev.cpp' if development else 'gpu_gl_native.cpp'
assert OLD_OPENGL in reviewed_g21[selected_gpu_name]
core = (cache / 'native-local/headless/core.cpp').read_text()
shutdown_core = core.split('    void ShutdownMainProcess() {', 1)[1].split('    bool IsShuttingDown()', 1)[0]
# The selected shared NS1/NS2 core now joins and destroys its GPU worker
# after guest CPU suspension but BEFORE CloseServices releases the NVDRV
# channel/GMMU backing. The previous services-before-GPU assertion would
# restore the shutdown use-after-free that this ordering prevents.
assert (shutdown_core.index('gpu_core->NotifyShutdown()')
        < shutdown_core.index('kernel.SuspendEmulation(true);')
        < shutdown_core.index('gpu_core.reset();')
        < shutdown_core.index('kernel.CloseServices();')
        < shutdown_core.index('services.reset();')
        < shutdown_core.index('host1x_core.reset();'))
if sys.platform == 'darwin':
    # The behavioral harness below validates the Linux pthread stack with
    # pthread_getattr_np. All generated native GPU shutdown/stop/join ordering
    # assertions above still run on macOS; the real implementation is compiled
    # for PS5 by the native target and the pthread runtime harness stays in CI.
    print('Native GPU generated lifecycle/ordering contract PASS (Linux pthread runtime harness deferred to CI)')
    raise SystemExit(0)
code = r'''
#include "gpu_failure.h"
#include "diagnostics.h"
#include <cstdio>
#include <mutex>
#include <string>
#include <cassert>
#include <cerrno>
#include <memory>
#include <pthread.h>
#include <semaphore>
#include <stop_token>
#include <system_error>
#include <functional>
#include <thread>
#include "common/bounded_threadsafe_queue.h"
static int fault, attributes_live, joins;
static std::binary_semaphore* joining;
static int init(pthread_attr_t* a) {
    if (fault == 1) return ENOMEM;
    int result = pthread_attr_init(a); if (!result) ++attributes_live; return result;
}
static int stack(pthread_attr_t* a, size_t size) {
    assert(size == 1024 * 1024);
    return fault == 2 ? EINVAL : pthread_attr_setstacksize(a, size);
}
static int destroy(pthread_attr_t* a) { --attributes_live; return pthread_attr_destroy(a); }
static int create(pthread_t* t, const pthread_attr_t* a, void* (*f)(void*), void* p) {
    return fault == 3 ? EAGAIN : pthread_create(t, a, f, p);
}
static int join(pthread_t t, void** out) {
    ++joins;
    if (joining) joining->release();
    return pthread_join(t, out);
}
namespace VideoCore { struct RendererBase { void* ReadRasterizer() { return this; } }; }
namespace Core::Frontend { struct GraphicsContext {}; }
namespace Tegra::Control { struct Scheduler {}; }
namespace VideoCommon::GPUThread {
class ThreadManager {
public:
    ~ThreadManager() { Stop(); }
    void StartThread(VideoCore::RendererBase&, Core::Frontend::GraphicsContext&, Tegra::Control::Scheduler&);
    void Stop();
    using CommandDataContainer = int;
    struct { std::mutex write_lock; Common::SPSCQueue<int, 4> queue; } state;
    std::binary_semaphore ready{0};
    bool finished{};
    std::function<void()> command;
private:
    void RunWorker(VideoCore::RendererBase&, Core::Frontend::GraphicsContext&, Tegra::Control::Scheduler&) {
        pthread_attr_t a;
        assert(pthread_getattr_np(pthread_self(), &a) == 0);
        size_t size;
        assert(pthread_attr_getstacksize(&a, &size) == 0 && size == 1024 * 1024);
        assert(pthread_attr_destroy(&a) == 0);
        int value = 0;
        state.queue.PopWait(value, stop_source.get_token());
        assert(value == 42 && !stop_source.stop_requested());
        if (command) { command(); finished = true; return; }
        ready.release();
        state.queue.PopWait(value, stop_source.get_token());
        assert(stop_source.stop_requested());
        finished = true;
    }
    void* rasterizer{};
    pthread_t thread{};
    std::stop_source stop_source;
    bool thread_joinable{};
};
}
#define pthread_attr_init init
#define pthread_attr_setstacksize stack
#define pthread_attr_destroy destroy
#define pthread_create create
#define pthread_join join
LIFECYCLE
int main(int argc, char**) {
    VideoCore::RendererBase renderer;
    Core::Frontend::GraphicsContext context;
    Tegra::Control::Scheduler scheduler;
    using VideoCommon::GPUThread::ThreadManager;
    if (argc > 1) {
        ThreadManager manager;
        manager.command = [&] { manager.ready.release(); throw std::runtime_error("injected worker failure"); };
        manager.StartThread(renderer, context, scheduler);
        manager.state.queue.EmplaceWait(42);
        manager.ready.acquire();
        manager.Stop();
        assert(Eden::PeekGpuFailure());
        assert(Eden::TakeGpuFailure());
        assert(Eden::PeekGpuFailure() && !Eden::TakeGpuFailure());
        try { std::rethrow_exception(Eden::PeekGpuFailure()); }
        catch (const std::runtime_error& error) {
            assert(std::string(error.what()) == "injected worker failure");
            return 0;
        }
        return 1;
    }
    for (fault = 1; fault <= 3; ++fault) {
        ThreadManager manager;
        try { manager.StartThread(renderer, context, scheduler); assert(false); }
        catch (const std::system_error&) {}
        assert(attributes_live == 0 && joins == 0);
    }
    fault = 0;
    ThreadManager manager;
    for (int i = 1; i <= 3; ++i) {
        manager.finished = false;
        manager.state.queue.EmplaceWait(7);
        manager.StartThread(renderer, context, scheduler);
        manager.state.queue.EmplaceWait(42);
        manager.ready.acquire();
        manager.Stop();
        manager.Stop();
        assert(manager.finished && joins == i && attributes_live == 0);
    }
    { ThreadManager implicit;
      implicit.StartThread(renderer, context, scheduler);
      implicit.state.queue.EmplaceWait(42);
      implicit.ready.acquire(); }
    assert(joins == 4 && attributes_live == 0);
    // A command already executing must exit before the protected owner goes.
    // Old ordering deterministically exposes the cleared unique_ptr, without
    // dereferencing it or relying on a scheduling delay.
    for (bool early_join : {false, true}) {
        std::binary_semaphore entered{0}, release{0}, join_started{0};
        bool pointer_alive = false, owner_destroyed = false;
        struct Protected {
            ThreadManager worker;
            bool& destroyed;
            explicit Protected(bool& flag) : destroyed(flag) {}
            ~Protected() { worker.Stop(); destroyed = true; }
        };
        auto owner = std::make_unique<Protected>(owner_destroyed);
        owner->worker.command = [&] {
            entered.release();
            release.acquire();
            pointer_alive = owner != nullptr && !owner_destroyed;
        };
        owner->worker.StartThread(renderer, context, scheduler);
        owner->worker.state.queue.EmplaceWait(42);
        entered.acquire();
        joining = &join_started;
        std::thread teardown([&] {
            if (early_join) owner->worker.Stop();
            owner.reset();
        });
        join_started.acquire();
        assert(!owner_destroyed);
        release.release();
        teardown.join();
        joining = nullptr;
        assert(owner_destroyed && pointer_alive == early_join);
    }
}
'''
lifecycle = worker.split('// PS5-only ThreadManager lifecycle;', 1)[1]
lifecycle = lifecycle[lifecycle.index('namespace VideoCommon::GPUThread {'):]
code = code.replace('LIFECYCLE', lifecycle)
with tempfile.TemporaryDirectory(prefix='eden-gpu-thread-') as folder:
    temp = Path(folder)
    (temp / 'check.cpp').write_text(code)
    subprocess.run(['c++', '-std=c++20', '-pthread', '-Wall', '-Wextra', '-Werror',
                    '-I', str(upstream), '-I', str(root / 'headless'), str(temp / 'check.cpp'),
                    '-o', str(temp / 'check')], check=True)
    subprocess.run([str(temp / 'check')], check=True, timeout=15)
    failed = subprocess.run([str(temp / 'check'), 'throw'], capture_output=True, text=True, timeout=15)
    assert failed.returncode == 0 and '[ProsperoEden] GPU worker: injected worker failure' in failed.stderr
print('Native GPU stack, stop/wake/join, creation failures and blocked-command teardown ordering/rejection PASS')

# Native channel retirement must use a distinct worker FIFO command: a draw's
# TickWork may execute inside the scheduler's shared epoch/execution leases.
owner = (root / "vendor/encore-active/eden/src/video_core/gpu_vulkan.cpp").read_text()
release = owner.split("void ReleaseChannel(Control::ChannelState& to_release) {", 1)[1].split("/// Binds a renderer", 1)[0]
assert "gpu_thread.RetireChannelAtBoundary(" in release
assert "scheduler.RetireChannel(owner.get());" in release
assert "RequestSyncOperation(" not in release and "WaitForSyncOperation(" not in release
assert release.index("scheduler.RetireChannel(owner.get());") < release.index("std::scoped_lock lock{channel_mutex};")
