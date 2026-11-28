#!/usr/bin/env python3
"""Detect a queued GPU read callback retaining an unwound caller's stack.

The actual pinned GPU::Impl::OnCPURead method is compiled in a host fixture.
Failure before its queued callback runs must not leave a dangling read-area
reference. Original source is an ASan negative control, native capture passes.
No console build or game-performance claim.
"""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
gpu = (root / "vendor/sources/eden/src/video_core/gpu.cpp").read_text()
cmake = (root / "headless/CMakeLists.txt").read_text()
workflow = (root / ".github/workflows/encore-core-preflight.yml").read_text()
start = "    VideoCore::RasterizerDownloadArea OnCPURead(DAddr addr, u64 size) {"
end = "    /// Notify rasterizer that any caches of the specified region should be invalidated"
assert gpu.count(start) == 1 and gpu.count(end) == 1
body = start + gpu.split(start, 1)[1].split(end, 1)[0]
old = "RequestSyncOperation([this, &raster_area]() {"
fixed = "RequestSyncOperation([this, raster_area]() {"
assert body.count(old) == 1
assert 'list(APPEND video_sources "${EDEN_MAINTAINED_G21_GPU}")' in cmake
assert 'gpu_read_capture_original' not in cmake
for filename in ("gpu_gl_host.cpp", "gpu_gl_host_dev.cpp",
                 "gpu_gl_native.cpp", "gpu_gl_native_dev.cpp"):
    maintained = (root/"vendor/encore-active/eden/src/video_core"/filename).read_text()
    assert maintained.count(fixed) == 1, filename
    assert old not in maintained, filename
vulkan = (root/"vendor/encore-active/eden/src/video_core/gpu_vulkan.cpp").read_text()
assert vulkan.count(fixed) == 1 and old not in vulkan
assert 'set(EDEN_MAINTAINED_G21_GPU "${EDEN_G21_GPU_ROOT}/gpu_vulkan.cpp")' in cmake
vulkan_body = start + vulkan.split(start, 1)[1].split(end, 1)[0]
assert vulkan_body.count(fixed) == 1
wait_body = vulkan.split("    void WaitForSyncOperation(const u64 fence) {", 1)[1].split(
    "\n    void WaitForIdle()", 1)[0]
for needle in ("shutting_down.load(std::memory_order_relaxed)",
               "::Eden::PeekGpuFailure()",
               "sync_request_cv.wait_for(lck, std::chrono::milliseconds(100))"):
    assert needle in wait_body, needle
assert wait_body.count("::Eden::PeekGpuFailure()") == 2
assert "sync_request_cv.wait(lck, [this, fence]" not in wait_body
assert "python3 -B tools/check-native-gpu-read-capture-host.py" in workflow

cpp = r"""
#include <cassert>
#include <cstdint>
#include <functional>
#include <stdexcept>
#include <utility>
using DAddr = std::uint64_t;
using u64 = std::uint64_t;
namespace VideoCore {
struct RasterizerDownloadArea {
    DAddr start_address{};
    DAddr end_address{};
    bool preemtive{};
};
}
struct FakeRasterizer {
    VideoCore::RasterizerDownloadArea next_area{0x1000,0x2000,false};
    unsigned flushes{};
    VideoCore::RasterizerDownloadArea GetFlushArea(DAddr,u64) {
        return next_area;
    }
    void FlushRegion(DAddr a,u64 n) {
        assert(a == 0x1000 && n == 0x1000);
        ++flushes;
    }
};
struct FakeRenderer {
    FakeRasterizer raster;
    FakeRasterizer* ReadRasterizer() {return &raster;}
};
struct FakeThread {
    unsigned ticks{};
    void TickGPU(bool) {++ticks;}
};
struct FakeGPU {
    FakeRenderer store{};
    FakeRenderer* renderer = &store;
    FakeThread gpu_thread{};
    bool is_async = true;
    bool fail_wait = true;
    std::function<void()> pending{};
    template<class Fn> u64 RequestSyncOperation(Fn&& fn) {
        pending=std::forward<Fn>(fn);
        return 1;
    }
    void WaitForSyncOperation(u64 fence) {
        assert(fence == 1);
        if(fail_wait) throw std::runtime_error("GPU worker failure");
        assert(static_cast<bool>(pending));
        pending();
        pending={};
    }
@@METHOD@@
};
int main(int argc,char**) {
    if(argc > 1) {
        FakeGPU gpu;
        try {
            (void)gpu.OnCPURead(0x1100,16);
            assert(false && "wait should throw");
        } catch (const std::runtime_error&) {}
        assert(gpu.gpu_thread.ticks == 1);
        assert(gpu.store.raster.flushes == 0);
        // Simulate the pending callback outliving the failed caller stack.
        auto replay = std::move(gpu.pending);
        replay();
        assert(gpu.store.raster.flushes == 1);
        return 0;
    }
    FakeGPU gpu;
    gpu.fail_wait = false;
    auto area = gpu.OnCPURead(0x1100,16);
    assert(area.preemtive && gpu.gpu_thread.ticks == 1);
    assert(gpu.store.raster.flushes == 1 && !gpu.pending);
    gpu.store.raster.next_area.preemtive = true;
    auto fast = gpu.OnCPURead(0x1100,16);
    assert(fast.preemtive && gpu.gpu_thread.ticks == 1);
}
"""
clang = shutil.which("clang++-18") or shutil.which("clang++")
assert clang, "Clang C++20 required"
with tempfile.TemporaryDirectory(prefix="encore-read-capture-") as tmp:
    work = Path(tmp)
    for label, source_body, is_native in (
        ("pinned", body, False),
        ("native", body.replace(old,fixed), True),
        ("native-vulkan", vulkan_body, True),
    ):
        unit = work / (label + ".cpp")
        binary = work / label
        unit.write_text(cpp.replace("@@METHOD@@", source_body))
        subprocess.run(
            [clang, "-std=c++20", "-O1", "-g", "-Wall", "-Wextra",
             "-Werror", "-fsanitize=address,undefined",
             "-fsanitize-address-use-after-return=always",
             "-fno-sanitize-recover=all", str(unit), "-o", str(binary)],
            check=True, timeout=45,
        )
        env = dict(os.environ, ASAN_OPTIONS="detect_stack_use_after_return=1")
        if is_native:
            subprocess.run([str(binary)], env=env, check=True, timeout=45)
            subprocess.run([str(binary), "--failed-wait"], env=env,
                           check=True, timeout=45)
        else:
            subprocess.run([str(binary)], env=env, check=True, timeout=45)
            broken = subprocess.run(
                [str(binary), "--failed-wait"], env=env,
                text=True, capture_output=True, timeout=45
            )
            assert broken.returncode != 0, "Original dangling capture was not detected"
            assert ("stack-use-after-return" in broken.stderr or
                    "stack-use-after-scope" in broken.stderr), broken.stderr

# The selected Vulkan GPU worker runs queued callbacks outside the sync mutex.
# If a callback raises (e.g. channel/rasterizer teardown), std::unique_lock
# must know it was unlocked; a raw mutex.unlock left it falsely owning the
# lock during unwinding. Compile the exact TickWork method with sanitizer
# and check success, re-entrant enqueue, failed callback and recovery.
tick_start = "    void TickWork() {"
tick_end = "    [[nodiscard]] u64 GetTicks() const {"
assert vulkan.count(tick_start) == 1 and vulkan.count(tick_end) == 1
tick = tick_start + vulkan.split(tick_start, 1)[1].split(tick_end, 1)[0]
original_tick = (root / "vendor/sources/eden/src/video_core/gpu.cpp").read_text()
original_tick = tick_start + original_tick.split(tick_start, 1)[1].split(tick_end, 1)[0]
assert "sync_request_mutex.unlock();" in original_tick
assert "sync_request_mutex.lock();" in original_tick
assert tick.count("lck.unlock();") == 1
assert tick.count("lck.lock();") == 1
assert "sync_request_mutex.unlock();" not in tick
assert "sync_request_mutex.lock();" not in tick
assert tick.index("lck.unlock();") < tick.index("request();") < tick.index("lck.lock();")

tick_fixture = r"""
#include <atomic>
#include <cassert>
#include <condition_variable>
#include <cstdint>
#include <functional>
#include <list>
#include <mutex>
#include <stdexcept>
#include <utility>
using u64 = std::uint64_t;
struct FakeGpu {
    std::mutex sync_request_mutex;
    std::list<std::function<void()>> sync_requests;
    std::atomic<u64> current_sync_fence{};
    std::atomic<u64> last_sync_fence{};
    std::condition_variable sync_request_cv;
@@TICK@@
};
int main() {
    FakeGpu gpu;
    int executed = 0;
    {
        std::scoped_lock lock{gpu.sync_request_mutex};
        gpu.sync_requests.emplace_back([&] {
            ++executed;
            std::scoped_lock lock2{gpu.sync_request_mutex};
            gpu.sync_requests.emplace_back([&] { ++executed; });
            ++gpu.last_sync_fence;
        });
        ++gpu.last_sync_fence;
    }
    gpu.TickWork();
    assert(executed == 2 && gpu.current_sync_fence == 2);
    {
        std::scoped_lock lock{gpu.sync_request_mutex};
        gpu.sync_requests.emplace_back([&] {
            ++executed;
            throw std::runtime_error("GPU channel release failed");
        });
        ++gpu.last_sync_fence;
    }
    try {
        gpu.TickWork();
        assert(false && "callback must propagate its failure");
    } catch (const std::runtime_error&) {}
    assert(executed == 3 && gpu.current_sync_fence == 2);
    {
        // A failed callback must not strand the queue mutex.
        std::unique_lock lock{gpu.sync_request_mutex, std::try_to_lock};
        assert(lock.owns_lock());
        gpu.sync_requests.emplace_back([&] { ++executed; });
        ++gpu.last_sync_fence;
    }
    gpu.TickWork();
    assert(executed == 4 && gpu.current_sync_fence == 3);
}
"""
with tempfile.TemporaryDirectory(prefix="encore-sync-ownership-") as tmp:
    work = Path(tmp)
    source = work / "gpu_tickwork.cpp"
    source.write_text(tick_fixture.replace("@@TICK@@", tick))
    for opt in ("0", "2"):
        binary = work / ("gpu_tickwork_O" + opt)
        subprocess.run(
            [clang, "-std=c++20", "-O" + opt, "-g", "-Wall", "-Wextra",
             "-Werror", "-pthread", "-fsanitize=address,undefined",
             "-fno-sanitize-recover=all", str(source), "-o", str(binary)],
            check=True, timeout=45,
        )
        subprocess.run([str(binary)], check=True, timeout=45)
print("NS1_GPU_SYNC_LOCK_OWNERSHIP_PASS native_tickwork=1 reentrant_queue=1 "
      "failure_unlock=1 recovery=1 sanitizers=address_undefined profiles=O0_O2")


# A failed std::list node allocation must not consume a sync fence number.
# The original pinned Vulkan method incremented last_sync_fence first; its
# subsequent successful request could therefore wait for a permanently
# unreachable fence even though no GPU callback itself failed.
request_start = "    template <typename Func>\n    [[nodiscard]] u64 RequestSyncOperation(Func&& action) {"
request_end = "    /// Obtains current flush request fence id."
assert vulkan.count(request_start) == 1 and vulkan.count(request_end) == 1
request_source = request_start + vulkan.split(request_start, 1)[1].split(request_end, 1)[0]
pinned_gpu = (root / "vendor/sources/eden/src/video_core/gpu.cpp").read_text()
original_request = request_start + pinned_gpu.split(request_start, 1)[1].split(
    request_end, 1)[0]
assert original_request.index("++last_sync_fence") < original_request.index(
    "sync_requests.emplace_back")
assert request_source.index("sync_requests.emplace_back") < request_source.index(
    "++last_sync_fence")
assert request_source.count("sync_requests.emplace_back") == 1

oom_fixture = r"""
#include <atomic>
#include <cassert>
#include <condition_variable>
#include <cstdint>
#include <functional>
#include <list>
#include <mutex>
#include <new>
#include <utility>
using u64 = std::uint64_t;
struct FailQueue {
    std::list<std::function<void()>> callbacks;
    bool fail_next{};
    template<class F> void emplace_back(F&& callback) {
        if (std::exchange(fail_next, false)) throw std::bad_alloc{};
        callbacks.emplace_back(std::forward<F>(callback));
    }
    bool empty() const { return callbacks.empty(); }
    auto& front() { return callbacks.front(); }
    void pop_front() { callbacks.pop_front(); }
};
struct FakeGpu {
    std::mutex sync_request_mutex;
    FailQueue sync_requests;
    std::atomic<u64> current_sync_fence{};
    std::atomic<u64> last_sync_fence{};
    std::condition_variable sync_request_cv;
@@REQUEST@@
@@TICK@@
};
int main() {
    FakeGpu gpu;
    unsigned completed{};
    gpu.sync_requests.fail_next = true;
    try {
        (void)gpu.RequestSyncOperation([&]{ ++completed; });
        assert(false && "allocation fault was not injected");
    } catch (const std::bad_alloc&) {}
    assert(gpu.last_sync_fence == 0 && gpu.current_sync_fence == 0);
    assert(gpu.sync_requests.empty());

    const auto first = gpu.RequestSyncOperation([&]{ ++completed; });
    const auto second = gpu.RequestSyncOperation([&]{ ++completed; });
    assert(first == 1 && second == 2);
    gpu.TickWork();
    assert(completed == 2 && gpu.current_sync_fence == second);
    assert(gpu.sync_requests.empty());

    gpu.sync_requests.fail_next = true;
    try {
        (void)gpu.RequestSyncOperation([&]{ ++completed; });
        assert(false && "second allocation fault was not injected");
    } catch (const std::bad_alloc&) {}
    assert(gpu.last_sync_fence == second && gpu.current_sync_fence == second);
    const auto third = gpu.RequestSyncOperation([&]{ ++completed; });
    assert(third == second + 1);
    gpu.TickWork();
    assert(completed == 3 && gpu.current_sync_fence == third);
}
"""
with tempfile.TemporaryDirectory(prefix="encore-fence-oom-") as tmp:
    work = Path(tmp)
    source = work / "gpu_fence_oom.cpp"
    source.write_text(oom_fixture.replace("@@REQUEST@@", request_source).replace(
        "@@TICK@@", tick))
    for opt in ("0", "2"):
        binary = work / ("gpu_fence_oom_O" + opt)
        subprocess.run(
            [clang, "-std=c++20", "-O" + opt, "-g", "-Wall", "-Wextra",
             "-Werror", "-pthread", "-fsanitize=address,undefined",
             "-fno-sanitize-recover=all", str(source), "-o", str(binary)],
            check=True, timeout=45,
        )
        subprocess.run([str(binary)], check=True, timeout=45)
print("NS1_GPU_SYNC_FENCE_OOM_PASS native_request=1 rejected_alloc=2 "
      "no_fence_gap=1 worker_ack=1 profiles=O0_O2 sanitizers=address_undefined")

print("NATIVE_GPU_READ_CAPTURE_HOST_PASS original_stack_use_after_return=1 native_callback_owns_range=1 vulkan_real_owner=1 failure_aware_wait=1 shutdown_exit=1 normal_wait=1 preemptive_skip=1 sanitizer=address_undefined")

# The selected capture request must own its output across early shutdown or
# failed waits. Test the actual method with a callback executed after return.
capture_start = "    std::vector<u8> GetAppletCaptureBuffer() {"
capture_end = "\n\n    Core::System& system;"
capture_method = capture_start + vulkan.split(capture_start, 1)[1].split(capture_end, 1)[0]
assert "std::make_shared<std::vector<u8>>()" in capture_method
assert "if (CurrentSyncRequestFence() < wait_fence)" in capture_method
capture_fixture = r"""
#include <atomic>
#include <cassert>
#include <cstdint>
#include <functional>
#include <memory>
#include <stdexcept>
#include <vector>
#include <utility>
using u8 = std::uint8_t;
using u64 = std::uint64_t;
struct Renderer {
    std::vector<u8> GetAppletCaptureBuffer() { return {1,2,3}; }
};
struct FakeGpu {
    Renderer backing;
    Renderer* renderer = &backing;
    struct Worker { void TickGPU(bool) {} } gpu_thread;
    bool is_async = true, cancelled = false, failure = false;
    u64 last{}, current{};
    std::function<void()> pending;
    template<class F> u64 RequestSyncOperation(F&& f) {
        pending = std::forward<F>(f);
        return ++last;
    }
    u64 CurrentSyncRequestFence() const { return current; }
    void Complete() { auto callback = std::move(pending); callback(); ++current; }
    void WaitForSyncOperation(u64) {
        if (failure) throw std::runtime_error("worker failed");
        if (!cancelled) Complete();
    }
@@CAPTURE@@
};
int main() {
    FakeGpu gpu;
    assert((gpu.GetAppletCaptureBuffer() == std::vector<u8>{1,2,3}));
    gpu.cancelled = true;
    assert(gpu.GetAppletCaptureBuffer().empty());
    gpu.Complete();
    assert(gpu.current == 2);
    gpu.failure = true;
    try { (void)gpu.GetAppletCaptureBuffer(); assert(false); }
    catch (const std::runtime_error&) {}
    gpu.Complete();
    assert(gpu.current == 3);
}
"""
with tempfile.TemporaryDirectory(prefix="encore-applet-capture-") as tmp:
    source = Path(tmp) / "capture.cpp"
    source.write_text(capture_fixture.replace("@@CAPTURE@@", capture_method))
    for opt in ("0", "2"):
        binary = Path(tmp) / ("capture_O" + opt)
        subprocess.run([clang, "-std=c++20", "-O" + opt, "-Wall", "-Wextra",
                        "-Werror", "-fsanitize=address,undefined",
                        "-fno-sanitize-recover=all", str(source), "-o", str(binary)],
                       check=True, timeout=45)
        subprocess.run([str(binary)], check=True, timeout=45)
print("NATIVE_GPU_APPLET_CAPTURE_LIFETIME_PASS success=1 cancellation=1 failure=1")
