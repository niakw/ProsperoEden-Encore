#!/usr/bin/env python3
"""Host ASan/UBSan: source-extracted Vulkan worker fatal-exit and queue drain.

Checks the actual maintained constructor lambda, WorkerThread body and
WaitWorker in PS5_NATIVE and non-native configurations. No console timings.
"""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[1]
SRC=(ROOT/"headless/vulkan_scheduler_ps5.cpp").read_text()
GEN=(ROOT/"tools/prepare-vulkan-port.py").read_text()
HDR=(ROOT/"headless/vk_scheduler_ps5.h").read_text()
start=HDR.index("    void RegisterOnSubmit(")
REGISTER=HDR[start:HDR.index("\n    }",start)+6]
assert "std::scoped_lock lock{execution_mutex};" in REGISTER
assert "Registration is owner-only" in GEN
CI=(ROOT/".github/workflows/encore-core-preflight.yml").read_text()
def extract(begin, end):
    assert SRC.count(begin)==1, (begin, SRC.count(begin))
    a=SRC.index(begin)
    return SRC[a:SRC.index(end,a)].rstrip()
CTOR=extract("    worker_thread = std::jthread([this](std::stop_token token) {", "\n}\n\nScheduler::~Scheduler")
WAIT=extract("void Scheduler::WaitWorker() {", "\nvoid Scheduler::DispatchWork()")
WORKER=extract("void Scheduler::WorkerThread(std::stop_token stop_token) {", "\nvoid Scheduler::AllocateWorkerCommandBuffer()")
assert "RecordGpuFailure(std::current_exception())" in CTOR
assert "RecordGpuFailure(std::current_exception())" in WORKER
assert "PeekGpuFailure()" in WAIT
assert WAIT.count("--queue_drain_waiters;")==1
assert "worker_in_flight = false;" in WORKER
assert "worker_in_flight = true;" in WORKER
assert "bool worker_in_flight{};" in (ROOT/"headless/vk_scheduler_ps5.h").read_text()
assert "event_cv.notify_all();" in CTOR and "event_cv.notify_all();" in WORKER
assert "try {" in WORKER and "catch (...)" in WORKER
assert WORKER.index("::Eden::RecordGpuFailure(")<WORKER.index("event_cv.notify_all();",WORKER.index("::Eden::RecordGpuFailure("))
assert "Publish failure before releasing execution_mutex" in SRC
assert "Background setup failures must also reach native GPU observers." in GEN
assert "python3 -B tools/check-vulkan-worker-fatal-drain-host.py" in CI

CPP=r"""
#include <atomic>
#include <cassert>
#include <chrono>
#include <condition_variable>
#include <exception>
#include <future>
#include <functional>
#include <memory>
#include <mutex>
#include <queue>
#include <stdexcept>
#include <stop_token>
#include <thread>
#include <utility>
#include <vector>
#ifdef PS5_NATIVE
#include "gpu_failure.h"
namespace Eden::Performance {
inline void ProbeSchedulerOnce(const char*) {}
}
#endif
namespace Common {
enum class ThreadPriority { Critical };
inline void SetCurrentThreadName(const char*) {}
inline void SetCurrentThreadPriority(ThreadPriority) {}
inline void SetCurrentThreadToPerformanceCores() {}
}
struct CommandChunk {
    enum Kind { Ordinary, ThrowExecute, ThrowAllocate };
    Kind kind=Ordinary;
    std::atomic<unsigned>* completed=nullptr;
    bool HasSubmit() const { return kind==ThrowAllocate; }
    void ExecuteAll(int,int) {
        if(kind==ThrowExecute) throw std::runtime_error("Vulkan command callback");
        if(completed) completed->fetch_add(1);
    }
};
class Scheduler {
public:
    std::queue<std::unique_ptr<CommandChunk>> work_queue;
    std::vector<std::unique_ptr<CommandChunk>> chunk_reserve;
    std::mutex execution_mutex, reserve_mutex, queue_mutex;
    std::function<void()> on_submit;
INJECT_REGISTER
    std::condition_variable_any event_cv;
    unsigned queue_drain_waiters{};
    bool worker_in_flight{};
    std::jthread worker_thread;
    std::atomic<unsigned> completed{0};
    int current_cmdbuf=0,current_upload_cmdbuf=0;
    Scheduler() {
INJECT_CTOR
    }
    ~Scheduler() {
        worker_thread.request_stop();
        event_cv.notify_all();
        if(worker_thread.joinable()) worker_thread.join();
    }
    void DispatchWork() {}
    void AllocateWorkerCommandBuffer() {
        throw std::runtime_error("Vulkan allocation");
    }
    void Push(CommandChunk::Kind kind) {
        auto command=std::make_unique<CommandChunk>();
        command->kind=kind;
        command->completed=&completed;
        {
            std::scoped_lock lock{queue_mutex};
            work_queue.push(std::move(command));
        }
        event_cv.notify_all();
    }
    void WaitWorker();
    void WorkerThread(std::stop_token stop_token);
};
INJECT_WAIT
INJECT_WORKER
int main() {
    using namespace std::chrono_literals;
#ifdef PS5_NATIVE
    Eden::ResetGpuFailureForTitle();
    {
        Scheduler scheduler;
        std::unique_lock lock{scheduler.execution_mutex};
        std::promise<void> started;
        auto entered=started.get_future();
        auto replacement=std::async(std::launch::async,[&] {
            started.set_value();
            scheduler.RegisterOnSubmit([] {});
        });
        entered.wait();
        assert(replacement.wait_for(50ms)==std::future_status::timeout);
        lock.unlock();
        assert(replacement.wait_for(4s)==std::future_status::ready);
        replacement.get();
        assert(scheduler.on_submit);
    }
#endif
    {
        Scheduler scheduler;
        scheduler.Push(CommandChunk::Ordinary);
        auto future=std::async(std::launch::async,[&] { scheduler.WaitWorker(); });
        assert(future.wait_for(4s)==std::future_status::ready);
        future.get();
        assert(scheduler.completed.load()==1);
        assert(scheduler.queue_drain_waiters==0);
    }
#ifdef PS5_NATIVE
    {
        Scheduler scheduler;
        // Leave another command queued behind the failing one. Without the
        // fail-aware drain predicate, WaitWorker would never complete.
        scheduler.Push(CommandChunk::ThrowExecute);
        scheduler.Push(CommandChunk::Ordinary);
        auto future=std::async(std::launch::async,[&] { scheduler.WaitWorker(); });
        assert(future.wait_for(4s)==std::future_status::ready);
        bool caught=false;
        try { future.get(); } catch(const std::runtime_error& e) {
            caught=std::string(e.what())=="Vulkan command callback";
        }
        assert(caught && scheduler.queue_drain_waiters==0);
        assert(scheduler.completed.load()==0 && Eden::PeekGpuFailure());
        assert(Eden::TakeGpuFailure());
        assert(Eden::PeekGpuFailure());
    }
    Eden::ResetGpuFailureForTitle();
    {
        Scheduler scheduler;
        scheduler.Push(CommandChunk::ThrowAllocate);
        auto future=std::async(std::launch::async,[&] { scheduler.WaitWorker(); });
        assert(future.wait_for(4s)==std::future_status::ready);
        bool caught=false;
        try { future.get(); } catch(const std::runtime_error& e) {
            caught=std::string(e.what())=="Vulkan allocation";
        }
        assert(caught && scheduler.queue_drain_waiters==0);
    }
    Eden::ResetGpuFailureForTitle();
#endif
}
""".replace("INJECT_REGISTER",REGISTER).replace("INJECT_CTOR",CTOR).replace("INJECT_WAIT",WAIT).replace("INJECT_WORKER",WORKER)
compiler=os.environ.get("CXX") or shutil.which("clang++") or shutil.which("g++")
assert compiler, "C++20 compiler required"
with tempfile.TemporaryDirectory(prefix="encore-vulkan-worker-fatal-") as tmp:
    d=Path(tmp)
    src=d/"worker.cpp"
    src.write_text(CPP)
    for name,flags in (("host",[]),("native",["-DPS5_NATIVE=1"])):
        exe=d/name
        subprocess.run([compiler,"-std=c++20","-O1","-Wall","-Wextra",
            "-pthread","-fsanitize=address,undefined","-fno-sanitize-recover=all",
            "-I",str(ROOT/"headless"),*flags,str(src),"-o",str(exe)],
            check=True,capture_output=True,text=True,timeout=70)
        result=subprocess.run([str(exe)],capture_output=True,text=True,timeout=20)
        assert result.returncode==0,(name,result.stdout[-900:],result.stderr[-1600:])
print("ENCORE_VULKAN_WORKER_FATAL_DRAIN_PASS source_extracted=3 host_normal=1 native_failure=2 waiters_released=1 sanitizer=1")


# The native semaphore and guest-fence overrides are CMake-selected, not
# alternate experimental paths. Compile their actual blocking methods.
master = (ROOT/"headless/vulkan_master_semaphore_ps5.cpp").read_text()
fences = (ROOT/"headless/fence_manager_ps5.h").read_text()
cmake = (ROOT/"headless/vulkan.cmake").read_text()
for name in ("vulkan_master_semaphore_ps5.cpp", "fence_manager_ps5.h", "vk_fence_manager_ps5.h"):
    assert name in cmake
assert "list(REMOVE_ITEM video_sources renderer_vulkan/vk_master_semaphore.cpp)" in cmake
assert "~FenceManager() override { StopFenceThread(); }" in (
    ROOT/"headless/vk_fence_manager_ps5.h").read_text()
assert "std::unique_lock queue_lock{guard, std::defer_lock};" in fences
assert "guard.lock();" not in fences and "guard.unlock();" not in fences
assert "std::function<void()> func([state]" in fences
assert "std::scoped_lock lock{guard};\n                fence_thread.request_stop();" in fences
assert "if (auto failure = ::Eden::PeekGpuFailure()) std::rethrow_exception(failure);\n            PopAsyncFlushes();" in fences
start=master.index("constexpr u64 kFailurePollNs")
helper=master[start:master.index("\nMasterSemaphore::MasterSemaphore",start)]
start=master.index("void MasterSemaphore::Wait(u64 tick)")
wait=master[start:master.index("\nVkResult MasterSemaphore::SubmitQueue(",start)]
start=master.index("void MasterSemaphore::WaitThread(")
thread=master[start:master.index("\nvk::Fence MasterSemaphore::GetFreeFence()",start)]
start=fences.index("    void WaitPendingFences(")
guest_wait=fences[start:fences.index("\nprotected:",start)]
assert thread.index("vk::Check(result);") < thread.index("pending->Reset();") < thread.index("gpu_tick.store(")
assert thread.index("vk::Check(result);") < thread.index("wait_queue.pop();")
assert "gpu_tick.wait(" not in wait
assert "wait_cv.wait_for(lock," in wait
assert "wait_cv.notify_all();" in thread
assert "std::scoped_lock lock{wait_mutex, free_mutex};" in thread
submit_owner = master[master.index("    const auto submit_owned_fence ="):master.index("    if (device.HasSynchronization2())",master.index("    const auto submit_owned_fence ="))]
assert submit_owner.index("wait_queue.emplace(") < submit_owner.index("submit(*wait_queue.back().second)")
assert submit_owner.index("RecordGpuFailure(") < submit_owner.index("wait_cv.notify_all();")
cpp=r"""
#include <atomic>
#include <cassert>
#include <chrono>
#include <condition_variable>
#include <deque>
#include <functional>
#include <future>
#include <memory>
#include <mutex>
#include <queue>
#include <stdexcept>
#include <thread>
#include <utility>
#include "gpu_failure.h"
using u64=std::uint64_t;
using namespace std::chrono_literals;
enum VkResult { VK_SUCCESS, VK_TIMEOUT, VK_ERROR_DEVICE_LOST };
namespace vk {
struct FenceState {
    std::atomic<VkResult> result{VK_TIMEOUT};
    unsigned resets{};
};
struct Fence {
    std::shared_ptr<FenceState> state;
    int operator*() const { return 1; }
    VkResult Wait(u64) const { std::this_thread::sleep_for(1ms); return state->result.load(); }
    void Reset() { ++state->resets; }
};
void Check(VkResult r) {
    if(r!=VK_SUCCESS) throw std::runtime_error("fence error");
}
}
struct Semaphore {
    bool enabled{};
    std::atomic<bool> completed{};
    explicit operator bool() const { return enabled; }
    bool Wait(u64,u64) { std::this_thread::sleep_for(1ms); return completed.load(); }
};
class MasterSemaphore {
public:
    Semaphore semaphore;
    std::atomic<u64> gpu_tick{};
    std::mutex wait_mutex,free_mutex;
    std::condition_variable_any wait_cv;
    std::queue<std::pair<u64,vk::Fence>> wait_queue;
    std::deque<vk::Fence> free_queue;
    bool IsFree(u64 tick) const { return gpu_tick.load()>=tick; }
    void Refresh() { if(semaphore.completed.load()) gpu_tick.store(9); }
    void Wait(u64);
    void WaitThread(std::stop_token);
    vk::Fence GetFreeFence() { return {std::make_shared<vk::FenceState>()}; }
    VkResult SubmitOwned(u64 host_tick, VkResult result, bool& called);
};
INJECT_HELPER
VkResult MasterSemaphore::SubmitOwned(u64 host_tick, VkResult result, bool& called) {
INJECT_SUBMIT
    return submit_owned_fence([&](auto){ called=true; return result; });
}
INJECT_WAIT
INJECT_THREAD
struct Guest {
    static constexpr bool can_async_check=true;
    std::function<void()> pending;
    std::promise<void> queued;
    void SignalFence(std::function<void()> cb) { pending=std::move(cb); queued.set_value(); }
    template<bool> void TryReleasePendingFences() {}
INJECT_GUEST
};
static void fail() { Eden::RecordGpuFailure(std::make_exception_ptr(std::runtime_error("submit error"))); }
static bool failed(std::future<void>& f) {
    assert(f.wait_for(2s)==std::future_status::ready);
    try { f.get(); } catch(const std::runtime_error&) { return true; }
    return false;
}
int main() {
    for(bool timeline:{false,true}) {
        Eden::ResetGpuFailureForTitle();
        MasterSemaphore m;
        m.semaphore.enabled=timeline;
        auto f=std::async(std::launch::async,[&]{m.Wait(9);});
        std::this_thread::sleep_for(5ms);
        fail();
        assert(Eden::TakeGpuFailure()); // UI delivery cannot clear fatal state
        assert(failed(f) && m.gpu_tick.load()==0);
    }
    Eden::ResetGpuFailureForTitle();
    {
        MasterSemaphore m;
        m.semaphore.enabled=true;
        auto f=std::async(std::launch::async,[&]{m.Wait(9);});
        m.semaphore.completed.store(true);
        assert(f.wait_for(2s)==std::future_status::ready);
        f.get();
        assert(m.IsFree(9));
    }
    for(bool error:{false,true}) {
        Eden::ResetGpuFailureForTitle();
        MasterSemaphore m;
        auto state=std::make_shared<vk::FenceState>();
        state->result.store(error ? VK_ERROR_DEVICE_LOST : VK_SUCCESS);
        m.wait_queue.emplace(7,vk::Fence{state});
        std::jthread worker([&](std::stop_token stop){
            try { m.WaitThread(stop); } catch(...) { Eden::RecordGpuFailure(std::current_exception()); }
        });
        const auto deadline=std::chrono::steady_clock::now()+2s;
        while(!m.IsFree(7) && !Eden::PeekGpuFailure() &&
              std::chrono::steady_clock::now()<deadline) std::this_thread::sleep_for(1ms);
        worker.request_stop(); m.wait_cv.notify_all(); worker.join();
        if(error) {
            assert(Eden::PeekGpuFailure() && m.gpu_tick.load()==0);
            assert(m.wait_queue.size()==1 && m.free_queue.empty() && state->resets==0);
        } else {
            assert(m.IsFree(7) && m.wait_queue.empty() && m.free_queue.size()==1 && state->resets==1);
        }
    }
    Eden::ResetGpuFailureForTitle();
    {
        MasterSemaphore m;
        bool called=false;
        assert(m.SubmitOwned(7,VK_ERROR_DEVICE_LOST,called)==VK_ERROR_DEVICE_LOST);
        assert(called && Eden::PeekGpuFailure() && m.wait_queue.size()==1);
        assert(m.gpu_tick.load()==0 && m.free_queue.empty());
        auto f=std::async(std::launch::async,[&]{m.WaitThread({});});
        assert(failed(f)); // rejected submission cannot be consumed or published
        assert(m.wait_queue.size()==1);
    }
    Eden::ResetGpuFailureForTitle();
    {
        Guest g;
        auto queued=g.queued.get_future();
        auto f=std::async(std::launch::async,[&]{g.WaitPendingFences(true);});
        assert(queued.wait_for(2s)==std::future_status::ready);
        fail();
        assert(failed(f));
        // Callback still owns its state after the waiter has unwound.
        g.pending();
    }
    Eden::ResetGpuFailureForTitle();
    {
        Guest g;
        auto queued=g.queued.get_future();
        auto f=std::async(std::launch::async,[&]{g.WaitPendingFences(true);});
        assert(queued.wait_for(2s)==std::future_status::ready);
        g.pending();
        assert(f.wait_for(2s)==std::future_status::ready);
        f.get();
    }
}
""".replace("INJECT_HELPER",helper).replace("INJECT_WAIT",wait).replace("INJECT_THREAD",thread).replace("INJECT_GUEST",guest_wait).replace("INJECT_SUBMIT",submit_owner)
with tempfile.TemporaryDirectory(prefix="encore-native-fatal-fences-") as tmp:
    d=Path(tmp)
    src=d/"fences.cpp"
    src.write_text(cpp)
    for opt in ("-O0","-O2"):
        exe=d/("fences"+opt[1:])
        subprocess.run([compiler,"-std=c++20",opt,"-Wall","-Wextra","-Werror","-pthread",
            "-fsanitize=address,undefined","-fno-sanitize-recover=all",
            "-I",str(ROOT/"headless"),str(src),"-o",str(exe)],check=True,timeout=70)
        subprocess.run([str(exe)],check=True,timeout=20)
print("ENCORE_NATIVE_GPU_FATAL_FENCES_PASS timeline=1 fallback=1 fence_result=2 rejected_submit=1 late_callback=1 normal_callback=1 O0_O2=2 ASan_UBSan=1")

# The failure-aware source is now selected in the existing native build path.
assert 'configure_file("${EDEN_PORT_DIR}/vulkan_scheduler_ps5.cpp"' in cmake
assert 'configure_file("${EDEN_PORT_DIR}/vk_scheduler_ps5.h"' in cmake
assert 'configure_file("${EDEN_PORT_DIR}/vulkan_present_manager_ps5.cpp"' in cmake
assert "event_cv.wait_for(ql, std::chrono::milliseconds(10));" in WAIT
assert "~CommandChunk()" in HDR
assert "first = command->GetNext();" in SRC
presentation = (ROOT/"headless/vulkan_present_manager_ps5.cpp").read_text()
assert "vk::Check(device.GetGraphicsQueue().Submit(submit_info, *frame->present_done));" in presentation
assert "frame->present_done.Wait(10'000'000)" in presentation
assert "if (present_thread.joinable()) present_thread.join();" in presentation
