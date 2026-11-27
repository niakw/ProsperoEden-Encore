#!/usr/bin/env python3
"""F07 C01/C03: actual frame-housekeeping lock-owner and wait phase fixture.

The frame callback retains texture-then-buffer lock ordering, no lock widening,
and no quiet-path clocks. Test with the real CachePhaseTimer and TickFrame.
Host-only: not a PS5 timing or FC27 frame proof.
"""
from pathlib import Path
import json
import shutil
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
perf = (root / "headless/performance.h").read_text()
report = (root / "headless/performance.cpp").read_text()
raster = (root / "vendor/encore-active/eden/src/video_core/renderer_vulkan/vulkan_rasterizer.cpp").read_text()
generator = (root / "tools/prepare-vulkan-port.py").read_text()
workflow = (root / ".github/workflows/encore-core-preflight.yml").read_text()

start = raster.index("void RasterizerVulkan::TickFrame() {")
end = raster.index("\n}\n", start) + 2
body = raster[start:end]
# Historical F07 generator is frozen. The selected P1 C++ extends it
# with a single pre-lock GPU-budget sample. Reverse only that P1 delta
# on an audit copy while compiling the actual runtime body below.
budget = """#ifdef PS5_NATIVE
    // Both native caches share the same RADV/PS5 GPU-memory budget.
    // Query ONCE before either guest cache mutex, retaining original
    // texture and buffer GC thresholds and retirement ordering.
    const std::optional<u64> frame_memory_usage =
        texture_cache_runtime.CanReportMemoryUsage()
            ? std::optional<u64>{texture_cache_runtime.GetDeviceMemoryUsage()}
            : std::nullopt;
#endif
"""
assert body.count(budget) == 1
historical = body.replace(budget, "", 1)
for cache in ("texture_cache", "buffer_cache"):
    newer = ("#ifdef PS5_NATIVE\n"
             f"        {cache}.TickFrame(frame_memory_usage);\n"
             "#else\n"
             f"        {cache}.TickFrame();\n"
             "#endif")
    assert historical.count(newer) == 1, cache
    historical = historical.replace(newer, f"        {cache}.TickFrame();", 1)
historical = historical.replace(
    "\n\n    {\n#ifdef PS5_NATIVE\n        ::Eden::Performance::CachePhaseTimer buffer_wait",
    "\n    {\n#ifdef PS5_NATIVE\n        ::Eden::Performance::CachePhaseTimer buffer_wait", 1)
assert json.dumps(historical, ensure_ascii=False) in generator, (
    "Pinned F07 generator must reproduce exact P1-reversed active body"
)
assert body.count("TickFrame(frame_memory_usage);") == 2
assert body.index("GetDeviceMemoryUsage()") < body.index("std::scoped_lock lock{texture_cache.mutex};")
assert generator.count("F07 frame GC texture and buffer lock ownership instrumentation") == 1
assert "python3 -B tools/check-ps5-f07-frame-cache-ownership-host.py" in workflow
assert report.count('"frame_texture_wait"') == 1
assert report.count('"frame_texture_held"') == 1
assert report.count('"frame_buffer_wait"') == 1
assert report.count('"frame_buffer_held"') == 1
for name in ("FrameTextureWait", "FrameTextureHeld", "FrameBufferWait", "FrameBufferHeld"):
    assert perf.count(name) == 1
    assert "CachePhase::" + name in body
assert "ShouldSampleCacheFrame()" in body
assert "std::scoped_lock lock{texture_cache.mutex};" in body
assert "std::scoped_lock lock{buffer_cache.mutex};" in body
assert body.index("texture_cache.TickFrame();") < body.index("buffer_cache.TickFrame();")
assert body.index("texture_wait.Stop();") < body.index("texture_held{")
assert body.index("buffer_wait.Stop();") < body.index("buffer_held{")

phase_start = perf.index("enum class CachePhase : unsigned {")
phase_end = perf.index("// V01:", phase_start)
phase_source = perf[phase_start:phase_end]

cpp = r"""
#include <array>
#include <atomic>
#include <cassert>
#include <chrono>
#include <cstdint>
#include <cstdio>
#include <mutex>
#include <optional>
#include <thread>
#include <vector>
namespace Common {
struct Clock {
    std::chrono::nanoseconds GetTimeNS() const {
        return std::chrono::duration_cast<std::chrono::nanoseconds>(
            std::chrono::steady_clock::now().time_since_epoch());
    }
};
inline Clock g_wall_clock;
}
using u64 = std::uint64_t;
namespace Eden::Performance {
inline std::atomic<bool> detailed_gpu_profile{false};
__PHASE_SOURCE__
}
struct Tracker {
    std::mutex inner;
    std::atomic_bool held{false};
    static thread_local unsigned held_by_this_thread;
    void lock() {
        inner.lock();
        ++held_by_this_thread;
        held.store(true, std::memory_order_release);
    }
    void unlock() {
        held.store(false, std::memory_order_release);
        assert(held_by_this_thread > 0);
        --held_by_this_thread;
        inner.unlock();
    }
};
thread_local unsigned Tracker::held_by_this_thread = 0;
struct SmallManager {
    std::vector<int>* sequence{};
    int number{};
    void TickFrame() { sequence->push_back(number); }
};
struct Cache {
    Tracker mutex;
    std::vector<int>* sequence{};
    int number{};
    std::optional<u64> last_budget;
    void TickFrame(std::optional<u64> budget = std::nullopt) {
        assert(mutex.held.load(std::memory_order_acquire));
        last_budget = budget;
        sequence->push_back(number);
        std::this_thread::sleep_for(std::chrono::microseconds(150));
    }
};
struct RuntimeStub {
    Cache* texture;
    Cache* buffer;
    unsigned queries{};
    bool CanReportMemoryUsage() const { return true; }
    u64 GetDeviceMemoryUsage() {
        // A second thread intentionally holds texture_cache during the
        // contention test. Only the querying GPU thread must own no lock.
        assert(texture && buffer);
        assert(Tracker::held_by_this_thread == 0);
        ++queries;
        return 0x12345678u;
    }
};
class RasterizerVulkan {
public:
    int draw_counter{13};
    std::vector<int> sequence;
    SmallManager guest_descriptor_queue{&sequence, 1};
    SmallManager compute_pass_descriptor_queue{&sequence, 2};
    SmallManager descriptor_buffer_ring{&sequence, 3};
    SmallManager fence_manager{&sequence, 4};
    SmallManager staging_pool{&sequence, 5};
    Cache texture_cache{{}, &sequence, 6, std::nullopt};
    Cache buffer_cache{{}, &sequence, 7, std::nullopt};
    RuntimeStub texture_cache_runtime{&texture_cache, &buffer_cache};
    void TickFrame();
};
__REAL_TICK__
int main() {
    RasterizerVulkan raster;
    using namespace Eden::Performance;
    const auto samples = [](CachePhase phase) {
        return cache_phase_totals[static_cast<unsigned>(phase)].samples.load();
    };
    for (int i = 0; i < 16; ++i) raster.TickFrame();
    assert(raster.draw_counter == 0);
    assert(raster.sequence.size() == 16 * 7);
#ifdef PS5_NATIVE
    assert(raster.texture_cache_runtime.queries == 16);
    assert(raster.texture_cache.last_budget == std::optional<u64>{0x12345678u});
    assert(raster.buffer_cache.last_budget == raster.texture_cache.last_budget);
#else
    assert(raster.texture_cache_runtime.queries == 0);
#endif
    for (int i = 0; i < 16; ++i) {
        for (int j = 0; j < 7; ++j) assert(raster.sequence[7*i+j] == j+1);
    }
    assert(samples(CachePhase::FrameTextureWait) == 0);
    assert(samples(CachePhase::FrameTextureHeld) == 0);
    assert(samples(CachePhase::FrameBufferWait) == 0);
    assert(samples(CachePhase::FrameBufferHeld) == 0);
    detailed_gpu_profile.store(true);
    for (int i = 0; i < 16; ++i) raster.TickFrame();
#ifdef PS5_NATIVE
    assert(samples(CachePhase::FrameTextureWait) == 1);
    assert(samples(CachePhase::FrameTextureHeld) == 1);
    assert(samples(CachePhase::FrameBufferWait) == 1);
    assert(samples(CachePhase::FrameBufferHeld) == 1);
    assert(cache_phase_totals[static_cast<unsigned>(CachePhase::FrameTextureHeld)]
               .total_ns.load() > 0);
    assert(cache_phase_totals[static_cast<unsigned>(CachePhase::FrameBufferHeld)]
               .total_ns.load() > 0);
    // Next sampled frame: a real, independent holder blocks the acquisition.
    // Never unlock a std::mutex from a thread other than its owner.
    for (int i = 0; i < 15; ++i) raster.TickFrame();
    std::atomic_bool holding{false};
    std::thread holder([&] {
        raster.texture_cache.mutex.lock();
        holding.store(true, std::memory_order_release);
        std::this_thread::sleep_for(std::chrono::milliseconds(5));
        raster.texture_cache.mutex.unlock();
    });
    while (!holding.load(std::memory_order_acquire)) std::this_thread::yield();
    raster.TickFrame();
    holder.join();
    assert(samples(CachePhase::FrameTextureWait) == 2);
    assert(cache_phase_totals[static_cast<unsigned>(CachePhase::FrameTextureWait)]
               .max_ns.load() >= 2'000'000);
#else
    assert(samples(CachePhase::FrameTextureWait) == 0);
    assert(samples(CachePhase::FrameBufferHeld) == 0);
#endif
    detailed_gpu_profile.store(false);
    for (int i = 0; i < 16; ++i) raster.TickFrame();
#ifdef PS5_NATIVE
    assert(samples(CachePhase::FrameTextureWait) == 2);
#endif
}
""".replace("__PHASE_SOURCE__", phase_source).replace("__REAL_TICK__", body)

# Cache's members are aggregates but Tracker contains a nonmovable std::mutex;
# aggregate initialization of a prvalue Tracker in place is supported in C++20.
compiler = shutil.which("clang++-18") or shutil.which("clang++") or shutil.which("g++")
assert compiler
with tempfile.TemporaryDirectory(prefix="f07-frame-cache-owner-") as folder:
    path = Path(folder) / "tick.cpp"
    path.write_text(cpp)
    for native in (False, True):
        for flags in ("-O0", "-O2"):
            exe = Path(folder) / f"{'ps5' if native else 'desktop'}-{flags[1:]}"
            cmd = [compiler, "-std=c++20", flags, "-pthread", "-Wall", "-Wextra",
                   "-Werror", "-fsanitize=undefined", "-fno-sanitize-recover=all",
                   *(["-DPS5_NATIVE=1"] if native else []),
                   str(path), "-o", str(exe)]
            built = subprocess.run(cmd, capture_output=True, text=True, timeout=45)
            assert built.returncode == 0, (native, flags, built.stderr[-6000:])
            ran = subprocess.run([str(exe)], capture_output=True, text=True, timeout=15)
            assert ran.returncode == 0, (native, flags, ran.stderr[-3500:])
            print(f"F07_FRAME_CACHE_OWNER_PASS native={int(native)} {flags} phase_sample=1 quiet=1 order=1 mutex_lifetime=1")
print("HOST_ONLY: no claimed PS5 frame timing, HUD gain or real VRAM driver latency")
