#!/usr/bin/env python3
"""G10: execute actual native Scheduler Push/Resume/Declare owners, Clang/GCC.

Tests the host GPFIFO ownership transition when a driver reuses a channel
bind_id, without ever producing guest completion for its retired generation.
This is not a guest shader, PS5 Vulkan, or complete G10 fence qualification.
"""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[2]
OWNER=ROOT / "vendor/encore-active/ns2-runtime/gpu_dispatch/video_core/control/scheduler.cpp"
source=OWNER.read_text()
def extract(start: str, stop: str) -> str:
    assert source.count(start)==1 and source.count(stop)==1, (start, stop)
    return start + source.split(start,1)[1].split(stop,1)[0]

push=extract("void Scheduler::Push(", "void Scheduler::ResumePendingNative(")
resume=extract("void Scheduler::ResumePendingNative(", "void Scheduler::DeclareChannel(")
declare=extract("void Scheduler::DeclareChannel(", "} // namespace Tegra::Control")
assert 'std::erase(pending_native_channels, retired);' in declare
assert 'existing->second = std::move(new_channel);' in declare
assert 'if (existing->second == new_channel)' in declare
assert 'std::runtime_error("Native GPFIFO: missing channel owner")' in push

fixture=r"""
#include <algorithm>
#include <cassert>
#include <functional>
#include <memory>
#include <mutex>
#include <shared_mutex>
#include <atomic>
#include <chrono>
#include <thread>
#include <stdexcept>
#include <unordered_map>
#include <utility>
#include <vector>

namespace Tegra {
using s32=int;
struct CommandList {};
struct GPU {
    int current{-1};
    unsigned binds{};
    void BindChannel(s32 id) { current=id; ++binds; }
};
namespace Control {
struct TestSystem { bool IsPoweredOn() const { return true; } };
struct Pusher {
    TestSystem system{};
    bool pending{}, ready{};
    unsigned pushes{}, dispatches{}, retries{};
    std::function<void()> after_dispatch{};
    void Push(CommandList&&) { ++pushes; }
    void DispatchCalls() { ++dispatches; if (after_dispatch) after_dispatch(); }
    bool HasPendingNativeAcquire() const { return pending; }
    bool ResumeNativeAcquire() {
        ++retries;
        if (!pending) return true;
        if (!ready) return false;
        pending=false;
        return true;
    }
};
struct Payload { Pusher dma_pusher; };
struct ChannelState {
    s32 bind_id{};
    std::shared_ptr<Payload> payload{std::make_shared<Payload>()};
};
class Scheduler {
public:
    void Push(GPU&, s32, CommandList&&);
    void ResumePendingNative(GPU&);
    void DeclareChannel(std::shared_ptr<ChannelState>);
    bool HasPendingNativeChannels() const noexcept {
        const std::scoped_lock lock(pending_guard);
        return !pending_native_channels.empty();
    }
private:
    std::unordered_map<s32,std::shared_ptr<ChannelState>> channels;
    std::vector<std::shared_ptr<ChannelState>> pending_native_channels;
    std::shared_mutex scheduling_guard;
    mutable std::mutex pending_guard;
};
__REAL_OWNER__
}
}
using namespace Tegra;
using namespace Tegra::Control;
static std::shared_ptr<ChannelState> channel(int id) {
    auto c=std::make_shared<ChannelState>();
    c->bind_id=id;
    return c;
}
int main() {
    GPU gpu;
    Scheduler scheduler;
    auto previous=channel(7);
    previous->payload->dma_pusher.pending=true;
    scheduler.DeclareChannel(previous);
    scheduler.Push(gpu, 7, CommandList{});
    assert(scheduler.HasPendingNativeChannels());
    assert(previous->payload->dma_pusher.dispatches==1);
    const unsigned before_old=previous->payload->dma_pusher.dispatches;

    auto current=channel(7); // Driver reuses numeric bind ID.
    scheduler.DeclareChannel(current);
    assert(!scheduler.HasPendingNativeChannels());
    previous->payload->dma_pusher.ready=true;
    scheduler.ResumePendingNative(gpu);
    assert(previous->payload->dma_pusher.dispatches==before_old);
    scheduler.Push(gpu, 7, CommandList{});
    assert(current->payload->dma_pusher.dispatches==1);
    assert(previous->payload->dma_pusher.dispatches==before_old);

    // Re-registering the exact SAME generation must preserve its wait.
    auto& cur=current->payload->dma_pusher;
    cur.pending=true;
    cur.ready=false;
    scheduler.Push(gpu, 7, CommandList{});
    assert(scheduler.HasPendingNativeChannels());
    scheduler.DeclareChannel(current);
    assert(scheduler.HasPendingNativeChannels());
    const unsigned before_resume=cur.dispatches;
    cur.ready=true;
    scheduler.ResumePendingNative(gpu);
    assert(!scheduler.HasPendingNativeChannels());
    assert(cur.dispatches==before_resume+1);

    // Missing/invalid owners must fail before binding or enqueuing.
    const unsigned binds=gpu.binds;
    bool rejected=false;
    try { scheduler.Push(gpu, 99, CommandList{}); }
    catch (const std::runtime_error&) { rejected=true; }
    assert(rejected && gpu.binds==binds);
    rejected=false;
    try { scheduler.DeclareChannel(nullptr); }
    catch (const std::runtime_error&) { rejected=true; }
    assert(rejected);
    rejected=false;
    auto missing_payload=channel(12);
    missing_payload->payload.reset();
    try { scheduler.DeclareChannel(missing_payload); }
    catch (const std::runtime_error&) { rejected=true; }
    assert(rejected);

    // Two valid parked owners: later channel releases an earlier one;
    // scheduler retries and processes the first without a busy-wait.
    auto a=channel(22), b=channel(23);
    auto& aw=a->payload->dma_pusher;
    auto& bw=b->payload->dma_pusher;
    aw.pending=true; aw.ready=false;
    bw.pending=true; bw.ready=false;
    scheduler.DeclareChannel(a);
    scheduler.DeclareChannel(b);
    scheduler.Push(gpu,22,CommandList{});
    scheduler.Push(gpu,23,CommandList{});
    assert(scheduler.HasPendingNativeChannels());
    bw.ready=true;
    bw.after_dispatch=[&] { aw.ready=true; };
    scheduler.ResumePendingNative(gpu);
    assert(aw.dispatches>=2 && bw.dispatches>=2);
    assert(!aw.pending && !bw.pending && !scheduler.HasPendingNativeChannels());

    // A service thread must never swap a live channel epoch while a GPU
    // worker is inside the original native DispatchCalls owner.
    auto in_flight=channel(35), replacement=channel(35);
    scheduler.DeclareChannel(in_flight);
    std::atomic<bool> entered{false}, allowed{false}, swapped{false};
    in_flight->payload->dma_pusher.after_dispatch=[&] {
        entered.store(true);
        while (!allowed.load()) std::this_thread::yield();
    };
    std::thread worker([&] { scheduler.Push(gpu,35,CommandList{}); });
    while (!entered.load()) std::this_thread::yield();
    std::thread registrar([&] {
        scheduler.DeclareChannel(replacement);
        swapped.store(true);
    });
    std::this_thread::sleep_for(std::chrono::milliseconds{12});
    assert(!swapped.load()); // Exclusive epoch lease still blocked.
    allowed.store(true);
    worker.join();
    registrar.join();
    assert(swapped.load());
    scheduler.Push(gpu,35,CommandList{});
    assert(replacement->payload->dma_pusher.dispatches==1);
}
""".replace("__REAL_OWNER__",push+"\n"+resume+"\n"+declare)

compilers=list(dict.fromkeys(c for c in (shutil.which("clang++"),shutil.which("g++")) if c))
assert compilers,"C++20 compiler required"
with tempfile.TemporaryDirectory(prefix="eden-g10-scheduler-reuse-") as d:
    src=Path(d)/"test.cpp"
    src.write_text(fixture)
    for compiler in compilers:
        for opt in ("-O0","-O2"):
            exe=Path(d)/(Path(compiler).name+opt)
            command=[compiler,"-std=c++20",opt,"-Wall","-Wextra","-Werror",
                     "-fsanitize=undefined","-fno-sanitize-recover=all",
                     str(src),"-pthread","-o",str(exe)]
            built=subprocess.run(command,capture_output=True,text=True,
                                 timeout=60,env=os.environ.copy())
            assert built.returncode==0,built.stderr[-4500:]
            ran=subprocess.run([str(exe)],capture_output=True,text=True,timeout=25)
            assert ran.returncode==0,ran.stderr[-4500:]
            print("G10_NATIVE_SCHEDULER_OWNER_REUSE_PASS",Path(compiler).name,opt,
                  "stale_wait_retired=1 same_owner_preserved=1"
                  " unknown_owner_rejected=1 two_channel_replay=1 epoch_concurrency=1",flush=True)
