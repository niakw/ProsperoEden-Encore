#!/usr/bin/env python3
"""F07 V01: compile the actual native/desktop FIFO worker-wait callbacks.

Do not infer PS5 game stalls from these simulated build completions.
"""
from pathlib import Path
import hashlib
import shutil
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
perf = (root / "headless/performance.h").read_text()
gen = (root / "tools/prepare-vulkan-port.py").read_text()
cache = (root / "vendor/encore-active/eden/src/video_core/renderer_vulkan/vk_pipeline_cache_cost.cpp").read_text()
header = (root / "vendor/encore-active/eden/src/video_core/renderer_vulkan/vk_compute_pipeline.h").read_text()
g = (root / "vendor/encore-active/eden/src/video_core/renderer_vulkan/vk_graphics_pipeline_cost.cpp").read_text()
c = (root / "vendor/encore-active/eden/src/video_core/renderer_vulkan/vk_compute_pipeline_cost.cpp").read_text()

begin = perf.index("struct PipelineWaitTrace {")
end = perf.index("\n};", begin) + len("\n};")
trace = perf[begin:end]
assert "if (!enabled) return;" in trace
assert "WasBlockedOnMutex() const noexcept" in trace
assert "lock_acquired - started) >= std::chrono::milliseconds(1)" in trace
assert "wait_ns=%llu usable=%u" in trace
assert "finished - started" in trace
assert "lock_acquired - started" in trace
assert "post_mutex_ns = elapsed - mutex_ns" in trace
assert "mutex_ns=%llu post_mutex_ns=%llu" in trace
assert "struct ShaderMissStageCosts" in perf
assert "result->SetDiagnosticCacheKeyHash(key.Hash());" in cache
assert "void SetDiagnosticCacheKeyHash(u64 hash) noexcept" in header
assert "u64 diagnostic_cache_key_hash{};" in header
for phrase in (
    "F07 keyed graphics worker-wait diagnostic admission",
    "F07 keyed compute worker-wait diagnostic admission",
    "F07 keyed graphics worker-wait after mutex release",
    "F07 keyed compute worker-wait after mutex release",
    "F07 publish diagnostic compute cache key before first Configure",
):
    assert phrase in gen, phrase
# Generator uses an f-string for the path-dependent label. Validate the
# actual strict delta and both target filenames, rather than looking for
# strings which are constructed only when prepare-vulkan-port.py runs.
assert 'for pipeline_file in ("vk_graphics_pipeline_cost.cpp", "vk_compute_pipeline_cost.cpp"):' in gen
assert 'f"F07 V01 keyed {pipeline_file} mutex-versus-postlock phase split"' in gen
assert '"            keyed_wait.MarkLockAcquired();\\n"' in gen or 'keyed_wait.MarkLockAcquired();' in gen

def callback_body(text, kind):
    first = text.index("        scheduler.Record([this](vk::CommandBuffer) {")
    last = text.index("        });", first) + len("        });")
    block = text[first:last]
    assert text.rfind("if (!is_built.load(std::memory_order_acquire)) {", 0, first) >= 0
    assert "RunBuild();" in block
    assert block.index("RunBuild();") < block.index("if (is_built.load(std::memory_order_acquire)) return;")
    assert "if (is_built.load(std::memory_order_acquire)) return;" in block
    assert block.count("std::unique_lock lock{build_mutex};") == 2
    assert block.count("if (is_built.load(std::memory_order_acquire)) return;") == 1
    assert "if (keyed_wait.WasBlockedOnMutex())" in block
    assert block.index("if (is_built.load(std::memory_order_acquire)) return;") < block.index("PipelineWaitTrace keyed_wait;")
    assert block.index("PipelineWaitTrace keyed_wait;") < block.index("std::unique_lock lock{build_mutex};") < block.index("keyed_wait.MarkLockAcquired();") < block.index("if (is_built.load(std::memory_order_acquire)) {")
    # The first ready check still skips diagnostics entirely. A publication
    # after it emits a trace ONLY for >1ms mutex contention; no condvar wait.
    assert "#ifndef PS5_NATIVE\n            std::unique_lock lock{build_mutex};" in block
    assert "build_condvar.wait(lock, [this] { return is_built.load(std::memory_order::relaxed); });" in block
    assert "lock.unlock();" in block
    assert block.rindex("lock.unlock();") < block.index("pipeline_ready_wait.Stop();") < block.index("timer.reset();") < block.rindex("keyed_wait.Complete")
    assert 'keyed_wait.Complete("' + kind + '"' in block
    assert "#ifdef PS5_NATIVE" in block and "#endif" in block
    return block

graphics = callback_body(g, "graphics")
compute = callback_body(c, "compute")

# Exact R457 (vendor edcc311c) GPU wait callbacks: the maintained change
# is a single RunBuild() claim before the acquire. A baseline witness must
# reconstruct both old excerpts byte-for-byte, not approximate old behavior.
r457_callback_sha1 = {
    "graphics": "3c8a59d1202924e6d8668294dcfa22151b3c455f",
    "compute": "55cb6c5e18d151229860f8ff2208657ecdb9d30c",
}
r457_callbacks = {}
for kind, updated in (("graphics", graphics), ("compute", compute)):
    addition = "            RunBuild();\\n".replace("\\n", "\n")
    assert updated.count(addition) == 1, (kind, "first-use callback drift")
    old_callback = updated.replace(addition, "", 1)
    assert hashlib.sha1(old_callback.encode()).hexdigest() == r457_callback_sha1[kind], (
        kind, "exact R457 callback predecessor not recovered")
    r457_callbacks[kind] = old_callback

cpp = r"""
#include <atomic>
#include <cassert>
#include <chrono>
#include <condition_variable>
#include <cstdint>
#include <cstdio>
#include <functional>
#include <mutex>
#include <optional>
#include <thread>
#include <utility>
using u64 = std::uint64_t;
namespace vk { struct CommandBuffer {}; }
namespace Eden::Performance {
inline std::atomic_bool detailed_gpu_profile{false};
enum class CachePhase { GraphicsPipelineWait, ComputePipelineWait };
struct Timer { ~Timer() {} };
inline std::optional<Timer> VulkanTimer(unsigned) { return std::optional<Timer>{std::in_place}; }
struct CachePhaseTimer {
    explicit CachePhaseTimer(CachePhase, bool) {}
    void Stop() noexcept {}
};
__REAL_TRACE__
}
struct Scheduler {
    std::function<void(vk::CommandBuffer)> callback;
    template<class F> void Record(F&& f) { callback = std::forward<F>(f); }
    void Run() { callback(vk::CommandBuffer{}); }
};
struct Key {
    std::size_t Hash() const noexcept { return 0x1234; }
};
struct Pipeline {
    Scheduler scheduler;
    std::atomic_bool is_built{false};
    // RunBuild models the maintained first-use claim. Existing wait scenarios
    // start with claimed=true to represent a builder already executing.
    std::atomic_bool build_claimed{true};
    std::function<void()> build_task;
    std::mutex build_mutex;
    std::condition_variable build_condvar;
    Key key;
    u64 diagnostic_cache_key_hash{0xabcd};
    bool bound{true};
    std::function<void()> on_before_lock = [] {};
    std::function<void()> on_before_wait = [] {};
    bool CanExecuteDraw() const {
        return is_built.load(std::memory_order_acquire) && bound;
    }
    bool IsBound() const { return bound; }
    void RunBuild() {
        if (build_claimed.exchange(true, std::memory_order_acq_rel)) return;
        assert(build_task);
        auto task=std::move(build_task);
        build_task=nullptr;
        task();
    }
    void Queue() {
        if (is_built.load(std::memory_order_acquire)) return;
__ACTUAL_CALLBACK__
    }
    void Publish() {
        { std::lock_guard lock{build_mutex};
          is_built.store(true, std::memory_order_release); }
        build_condvar.notify_all();
    }
};
int main() {
    using Eden::Performance::detailed_gpu_profile;
    // New first-use path: if queued work has not been claimed yet, the
    // ordered GPU callback claims and builds it inline instead of waiting
    // behind unrelated ThreadWorker jobs.
    {
        Pipeline first_use;
        first_use.build_claimed.store(false,std::memory_order_release);
        first_use.build_task=[&]{first_use.Publish();};
        first_use.Queue();
#ifdef R457_NEGATIVE_CONTROL
        // Historical callback has no inline RunBuild claim. Make the GPU
        // callback enter its actual condvar wait, prove it cannot complete
        // before a separate worker publishes, then release it. No wall-clock
        // threshold or host scheduler speed is used for the comparison.
        std::atomic_bool entered_wait{false};
        std::atomic_bool callback_returned{false};
        first_use.on_before_wait = [&] {
            entered_wait.store(true, std::memory_order_release);
            entered_wait.notify_one();
        };
        std::thread gpu_callback([&] {
            first_use.scheduler.Run();
            callback_returned.store(true, std::memory_order_release);
        });
        entered_wait.wait(false, std::memory_order_acquire);
        assert(!callback_returned.load(std::memory_order_acquire));
        assert(!first_use.build_claimed.load(std::memory_order_acquire));
        assert(first_use.build_task);
        first_use.Publish();
        gpu_callback.join();
        assert(callback_returned.load(std::memory_order_acquire));
        assert(!first_use.build_claimed.load(std::memory_order_acquire));
#else
        // The maintained callback itself claims the queued build without
        // requiring an external shader-worker publication.
        first_use.scheduler.Run();
        assert(first_use.IsBound() && first_use.build_claimed.load());
        assert(!first_use.build_task);
#endif
    }
    // Quiet mode may wait, but must never add a wall-clock log.
    {
        Pipeline quiet;
        quiet.Queue();
        std::thread publisher([&]{ std::this_thread::sleep_for(std::chrono::milliseconds(4)); quiet.Publish(); });
        quiet.scheduler.Run();
        publisher.join();
    }
    detailed_gpu_profile.store(true);
    // Published after Record but before callback -> no actual blocking wait.
    {
        Pipeline already;
        already.Queue();
        already.Publish();
        already.scheduler.Run();
        assert(already.IsBound());
    }
    // The injected pre-lock publication hook exists only in the native branch.
#ifdef PS5_NATIVE
    // Publication between the first acquire and the mutex must not emit a false wait.
    {
        Pipeline raced;
        raced.Queue();
        raced.on_before_lock = [&] { raced.Publish(); };
        raced.scheduler.Run();
        assert(raced.IsBound());
    }
#endif
    // Publication really delayed while callback executes.
    {
        Pipeline blocked;
        blocked.Queue();
        std::thread publisher([&] { std::this_thread::sleep_for(std::chrono::milliseconds(6)); blocked.Publish(); });
        blocked.scheduler.Run();
        publisher.join();
    }
    // Failure must still publish and release waiting worker; usable=0.
    {
        Pipeline rejected;
        rejected.bound = false;
        rejected.Queue();
        std::thread publisher([&] { std::this_thread::sleep_for(std::chrono::milliseconds(5)); rejected.Publish(); });
        rejected.scheduler.Run();
        publisher.join();
    }
#ifdef PS5_NATIVE
    // Force a real build_mutex wait *before* the condition wait. The owner
    // stays locked until the measured callback reaches its pre-lock hook.
    // A timer incorrectly started AFTER mutex acquisition would undercount
    // this 14-ms phase as only the subsequent 9-ms builder delay.
    {
        Pipeline contended;
        contended.Queue();
        std::atomic<bool> holder_ready{false};
        std::atomic<bool> caller_at_lock{false};
        std::thread holder([&] {
            std::unique_lock mutex_hold{contended.build_mutex};
            holder_ready.store(true,std::memory_order_release);
            holder_ready.notify_one();
            caller_at_lock.wait(false,std::memory_order_acquire);
            std::this_thread::sleep_for(std::chrono::milliseconds(14));
        });
        holder_ready.wait(false,std::memory_order_acquire);
        contended.on_before_lock = [&] {
            caller_at_lock.store(true,std::memory_order_release);
            caller_at_lock.notify_one();
        };
        std::atomic<bool> callback_at_wait{false};
        contended.on_before_wait = [&] {
            callback_at_wait.store(true,std::memory_order_release);
            callback_at_wait.notify_one();
        };
        std::thread publisher([&] {
            holder.join();
            // Do not publish before the callback has passed its second
            // acquire check: otherwise the fast path can return without
            // a condition wait and this fixture would be schedule-dependent.
            callback_at_wait.wait(false,std::memory_order_acquire);
            std::this_thread::sleep_for(std::chrono::milliseconds(9));
            contended.Publish();
        });
        contended.scheduler.Run();
        publisher.join();
    }
    // A shader builder may finish WHILE the GPU worker waits for its mutex.
    // A real 14ms mutex stall must be traced without a condition wait.
    {
        Pipeline published_under_mutex;
        published_under_mutex.Queue();
        std::atomic<bool> locked{false};
        std::atomic<bool> gpu_at_mutex{false};
        std::thread publisher([&] {
            std::unique_lock hold{published_under_mutex.build_mutex};
            locked.store(true, std::memory_order_release);
            locked.notify_one();
            gpu_at_mutex.wait(false, std::memory_order_acquire);
            std::this_thread::sleep_for(std::chrono::milliseconds(14));
            published_under_mutex.is_built.store(true, std::memory_order_release);
            hold.unlock();
            published_under_mutex.build_condvar.notify_all();
        });
        locked.wait(false, std::memory_order_acquire);
        published_under_mutex.on_before_lock = [&] {
            gpu_at_mutex.store(true, std::memory_order_release);
            gpu_at_mutex.notify_one();
        };
        published_under_mutex.on_before_wait = [&] {assert(false);};
        published_under_mutex.scheduler.Run();
        publisher.join();
        assert(published_under_mutex.IsBound());
    }
#endif
    detailed_gpu_profile.store(false);
    {
        Pipeline no_work;
        no_work.Publish();
        no_work.Queue();
        assert(!no_work.scheduler.callback);
    }
}
""".replace("__REAL_TRACE__", trace)

compiler = shutil.which("clang++-18") or shutil.which("clang++") or shutil.which("g++")
assert compiler, "C++20 compiler required"
with tempfile.TemporaryDirectory(prefix="f07-v01-worker-keyed-") as tmp:
    for kind, callback in (("graphics", graphics), ("compute", compute)):
        source = Path(tmp) / f"{kind}.cpp"
        source.write_text(cpp.replace("__ACTUAL_CALLBACK__", callback.replace(
            "            std::unique_lock lock{build_mutex};",
            "            on_before_lock();\n            std::unique_lock lock{build_mutex};", 1).replace(
            "            build_condvar.wait(lock,",
            "            on_before_wait();\n            build_condvar.wait(lock,", 1)))
        for native in (False, True):
            for opt in ("-O0", "-O2"):
                exe = Path(tmp) / f"{kind}-{'ps5' if native else 'desktop'}-{opt[1:]}"
                cmd = [compiler, "-std=c++20", opt, "-Wall", "-Wextra", "-Werror",
                       "-pthread", "-fsanitize=undefined", "-fno-sanitize-recover=all",
                       *(["-DPS5_NATIVE=1"] if native else []),
                       str(source), "-o", str(exe)]
                build = subprocess.run(cmd, capture_output=True, text=True, timeout=45)
                assert build.returncode == 0, (kind, native, opt, build.stderr[-4000:])
                out = subprocess.run([str(exe)], capture_output=True, text=True, timeout=20)
                assert out.returncode == 0, (kind, native, opt, out.stderr[-3000:])
                lines = [line for line in out.stdout.splitlines()
                         if line.startswith("EDEN_VULKAN_PIPELINE_WAIT ")]
                if native:
                    assert len(lines) == 4, (kind, opt, lines)
                    assert all(f"kind={kind}" in line for line in lines)
                    expected_key = "0000000000001234" if kind == "graphics" else "000000000000abcd"
                    assert all(f"key={expected_key}" in line for line in lines)
                    assert "usable=1" in lines[0]
                    assert "usable=0" in lines[1]
                    assert "usable=1" in lines[2]
                    assert "usable=1" in lines[3]
                    assert all(int(line.split("wait_ns=")[1].split()[0]) > 0 for line in lines)
                    # The new recorded wait combines the forced 14ms mutex
                    # ownership plus 9ms condition wait; the old trace only
                    # saw the latter. Use a conservative >=12ms floor.
                    assert int(lines[2].split("wait_ns=")[1].split()[0]) >= 12_000_000
                    for item in lines:
                        total = int(item.split("wait_ns=")[1].split()[0])
                        mutex = int(item.split("mutex_ns=")[1].split()[0])
                        post = int(item.split("post_mutex_ns=")[1].split()[0])
                        assert total == mutex + post, (kind, opt, item)
                    assert int(lines[2].split("mutex_ns=")[1].split()[0]) >= 12_000_000
                    assert int(lines[2].split("post_mutex_ns=")[1].split()[0]) >= 1_000_000
                    assert int(lines[3].split("mutex_ns=")[1].split()[0]) >= 12_000_000
                else:
                    assert not lines, (kind, opt, lines)
                print(f"F07_KEYED_PIPELINE_WAIT_PASS kind={kind} native={int(native)} {opt}")
# Compare against the byte-identical R457 wait callbacks under a
# forced unclaimed shader task. Both old callbacks need a separate worker;
# both current callbacks are validated above to claim that work inline.
# The legacy run preserves ALL other wait and diagnostic scenarios.
    for kind, predecessor in r457_callbacks.items():
        source = Path(tmp) / f"{kind}-r457-wait.cpp"
        source.write_text(cpp.replace("__ACTUAL_CALLBACK__", predecessor.replace(
            "            std::unique_lock lock{build_mutex};",
            "            on_before_lock();\\n            std::unique_lock lock{build_mutex};".replace("\\n", "\n"), 1).replace(
            "            build_condvar.wait(lock,",
            "            on_before_wait();\\n            build_condvar.wait(lock,".replace("\\n", "\n"), 1)))
        for opt in ("-O0", "-O2"):
            exe = Path(tmp) / f"{kind}-r457-ps5-{opt[1:]}"
            cmd = [compiler, "-std=c++20", opt, "-Wall", "-Wextra",
                   "-Werror", "-pthread", "-fsanitize=undefined",
                   "-fno-sanitize-recover=all", "-DPS5_NATIVE=1",
                   "-DR457_NEGATIVE_CONTROL=1", str(source), "-o", str(exe)]
            built = subprocess.run(cmd, capture_output=True, text=True, timeout=45)
            assert built.returncode == 0, (kind, opt, built.stderr[-4000:])
            out = subprocess.run([str(exe)], capture_output=True, text=True, timeout=20)
            assert out.returncode == 0, (kind, opt, out.stderr[-4000:])
            lines = [line for line in out.stdout.splitlines()
                     if line.startswith("EDEN_VULKAN_PIPELINE_WAIT ")]
            assert len(lines) == 4, (kind, opt, lines)
            print(f"F07_R457_WAIT_NEGATIVE_CONTROL_PASS kind={kind} {opt}")

print("F07_FIRST_USE_INLINE_CLAIM_PASS graphics_compute=1 queued_worker_bypass=1")
print("F07_R457_VS_CURRENT_CALLBACK_REPLAY_PASS exact_r457=1 blocked_until_external_worker=1 current_inline_claim=1")
print("HOST_ONLY no Sony SDK, real GPU worker, FIFO timing in FC27 or frame latency proof")
