#!/usr/bin/env python3
"""Run real source-extracted synchronous/async Vulkan Present and GetRenderFrame.

A recycled frame must be pushed under free_mutex and wake consumers only
after it is available. The async path and failed copy must remain unchanged.
Host ASan/UBSan, not a native-console performance experiment.
"""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[1]
SOURCE=(ROOT/"headless/vulkan_present_manager_ps5.cpp").read_text()
cmake=(ROOT/"headless/vulkan.cmake").read_text()
assert 'configure_file("${EDEN_PORT_DIR}/vulkan_present_manager_ps5.cpp"' in cmake
GEN=(ROOT/"tools/prepare-vulkan-port.py").read_text()
CI=(ROOT/".github/workflows/encore-core-preflight.yml").read_text()
start=SOURCE.index("Frame* PresentManager::GetRenderFrame() {")
end=SOURCE.index("\nsize_t PresentManager::MaxExtraFrames() const {", start)
METHODS=SOURCE[start:end]
assert METHODS.count("void PresentManager::Present(Frame* frame) {")==1
assert "const bool wake_presenter = present_queue.empty() && !present_in_flight;" in METHODS
sync=METHODS.split("    } else {\n        scheduler.WaitWorker();",1)[1]
assert sync.index("CopyToSwapchain(frame);") < sync.index("std::scoped_lock lock{free_mutex};")
assert sync.index("free_queue.push_back(frame);") < sync.index("free_cv.notify_one();")
assert "wake_free_waiter = free_waiters != 0;" in sync
assert "if (wake_free_waiter) free_cv.notify_one();" in sync
assert "std::scoped_lock lock{free_mutex};" in sync
assert "free_cv.wait_for(lock, std::chrono::milliseconds(10));" in METHODS
assert "while (!present_failure && free_queue.empty() && !::Eden::PeekGpuFailure())" in METHODS
assert "frame->game_frame_presents = 1;" in METHODS
assert "std::unique_lock lock{queue_mutex};" in METHODS
assert "Synchronous presentation must publish its recycled frame" in GEN
assert "python3 -B tools/check-vulkan-sync-recycle-host.py" in CI

CPP=r"""
#include <atomic>
#include <cassert>
#include <chrono>
#include <condition_variable>
#include <cstddef>
#include <cstdint>
#include "gpu_failure.h"
#include <deque>
#include <exception>
#include <functional>
#include <mutex>
#include <stdexcept>
#include <thread>
#include <utility>
#include <vector>
using VkResult=int;
constexpr VkResult VK_SUCCESS=0,VK_TIMEOUT=2,VK_ERROR_DEVICE_LOST=-4;
namespace vk { using CommandBuffer=int; void Check(VkResult r){if(r!=VK_SUCCESS)throw std::runtime_error("fence failure");} }
namespace Eden::Performance {
inline constexpr int gpu_present_wait=0;
inline constexpr int gpu_present_free_wait=1;
inline constexpr int gpu_present_fence_wait=2;
struct DiagnosticTimer { explicit DiagnosticTimer(int) {} };
}
struct Frame {
    std::uint32_t game_frame_presents{3};
    struct Fence {
        unsigned waits=0, resets=0;
        VkResult result=VK_SUCCESS;
        VkResult Wait(std::uint64_t) { ++waits; return result; }
        void Reset() { ++resets; }
    } present_done;
};
struct CheckedMutex {
    std::mutex mutex;
    std::atomic<bool> locked{false};
    std::atomic<unsigned> locks{0};
    inline static thread_local const CheckedMutex* owned=nullptr;
    void lock() {
        mutex.lock();
        owned=this;
        locked.store(true);
        locks.fetch_add(1);
    }
    void unlock() {
        assert(owned==this);
        owned=nullptr;
        locked.store(false);
        mutex.unlock();
    }
};
struct CheckedFrames {
    CheckedMutex* gate=nullptr;
    std::deque<Frame*> items;
    bool empty() const { return items.empty(); }
    Frame* front() { assert(CheckedMutex::owned==gate); return items.front(); }
    void pop_front() { assert(CheckedMutex::owned==gate); items.pop_front(); }
    void push_back(Frame* frame) {
        assert(CheckedMutex::owned==gate && "free_queue writer must own free_mutex");
        items.push_back(frame);
    }
};
struct FreeCV {
    std::condition_variable_any condition;
    std::atomic<bool> entered{false};
    std::atomic<unsigned> notifications{0};
    template <class Lock, class Duration> void wait_for(Lock& lock, Duration duration) {
        entered.store(true);
        condition.wait_for(lock, duration);
    }
    void notify_one() { ++notifications; condition.notify_one(); }
};
struct PresentReadyCV {
    std::atomic<unsigned> notifications{0};
    void notify_one() { notifications.fetch_add(1); }
};
struct Scheduler {
    unsigned drains=0;
    std::vector<std::function<void(vk::CommandBuffer)>> queued;
    void WaitWorker() { ++drains; }
    template <class F> void Record(F&& f) { queued.emplace_back(std::forward<F>(f)); }
};
struct PresentManager {
    explicit PresentManager(bool async)
        : use_present_thread(async) { free_queue.gate=&free_mutex; }
    bool use_present_thread=false;
    bool throw_copy=false;
    unsigned copies=0;
    CheckedMutex free_mutex;
    FreeCV free_cv;
    std::size_t free_waiters{}; // guarded by free_mutex
    CheckedFrames free_queue;
    std::mutex queue_mutex;
    std::deque<Frame*> present_queue;
    // Mirrors the queue-mutex-guarded state read by the extracted Present().
    bool present_in_flight{};
    std::condition_variable frame_cv;
    PresentReadyCV present_ready_cv;
    std::exception_ptr present_failure;
    Scheduler scheduler;
    void CopyToSwapchain(Frame*) {
        assert(CheckedMutex::owned!=&free_mutex && "copy caller must not hold free mutex");
        ++copies;
        if (throw_copy) throw std::runtime_error("native copy failed");
    }
    Frame* GetRenderFrame();
    void Present(Frame*);
};
INJECT_METHODS
int main() {
    {
        PresentManager p(false);
        Frame frame;
        std::atomic<Frame*> received{nullptr};
        std::thread waiter([&] { received.store(p.GetRenderFrame()); });
        const auto deadline=std::chrono::steady_clock::now()+std::chrono::seconds(4);
        // Present acquires the same mutex; timed wakes do not invalidate the handshake.
        while (!p.free_cv.entered.load() && std::chrono::steady_clock::now()<deadline)
            std::this_thread::yield();
        assert(p.free_cv.entered.load());
        p.Present(&frame);
        waiter.join();
        assert(received.load()==&frame && frame.present_done.waits==1);
        assert(frame.game_frame_presents==1 && frame.present_done.resets==1 && p.scheduler.drains==1);
        assert(p.copies==1 && p.free_cv.notifications.load()==1);
        assert(p.present_ready_cv.notifications.load()==0);
        assert(p.free_waiters==0);
        assert(p.free_mutex.locks.load()>=2 && p.free_queue.empty());
    }
    {
        PresentManager p(false);
        Frame frame;
        p.throw_copy=true;
        bool threw=false;
        try { p.Present(&frame); } catch (const std::runtime_error&) { threw=true; }
        assert(threw && p.scheduler.drains==1 && p.copies==1);
        assert(p.free_queue.empty() && p.free_cv.notifications.load()==0);
    }
    {
        PresentManager p(false);
        Frame frame;
        frame.present_done.result=VK_ERROR_DEVICE_LOST;
        p.Present(&frame);
        bool threw=false;
        try { p.GetRenderFrame(); } catch (const std::runtime_error&) { threw=true; }
        assert(threw && frame.present_done.resets==0 && frame.game_frame_presents==3 && p.free_queue.empty());
    }
    {
        PresentManager p(true);
        Frame frame;
        p.Present(&frame);
        assert(p.scheduler.drains==0 && p.copies==0);
        assert(p.free_queue.empty() && p.scheduler.queued.size()==1);
        p.scheduler.queued.front()(0);
        assert(p.present_queue.size()==1 && p.present_queue.front()==&frame);
        assert(p.free_cv.notifications.load()==0);
        assert(p.present_ready_cv.notifications.load()==1);
    }
}
""".replace("INJECT_METHODS",METHODS)
compiler=os.environ.get("CXX") or shutil.which("clang++") or shutil.which("g++")
assert compiler, "A host C++20 compiler is required"
with tempfile.TemporaryDirectory(prefix="encore-sync-present-recycle-") as tmp:
    out=Path(tmp)
    src=out/"witness.cpp"
    exe=out/"witness"
    src.write_text(CPP)
    compile_result=subprocess.run(
        [compiler,"-std=c++20","-O1","-Wall","-Wextra","-Werror",
         "-pthread","-fsanitize=address,undefined",
         "-fno-sanitize-recover=all","-I",str(ROOT/"headless"),str(src),"-o",str(exe)],
        capture_output=True,text=True,timeout=80)
    assert compile_result.returncode==0, (
        compile_result.returncode,compile_result.stderr[-4000:])
    result=subprocess.run([str(exe)],capture_output=True,text=True,timeout=20)
    assert result.returncode==0,(result.returncode,result.stdout[-1000:],result.stderr[-2000:])
print("ENCORE_SYNC_PRESENT_RECYCLE_PASS source_extracted=1 mutex=1 wake=1 copy_failure=1 async_unchanged=1 asan_ubsan=1")
