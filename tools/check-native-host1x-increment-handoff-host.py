#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""N04/F05 current Host1x numeric-handle/cancellation/concurrency witness.

Compiles the exact maintained syncpoint_manager.cpp and public header at O0/O2.
Covers callback reentrance, ordered thresholds, pending/running cancellation,
counter wake before a blocked callback, unrelated-domain progress, concurrent
same-syncpoint increments, guest mirroring and a 256-action stress loop.
No GPU scanout, guest HIPC or FC27 gameplay is inferred.
"""
from pathlib import Path
import shutil, subprocess, tempfile

ROOT=Path(__file__).resolve().parents[1]
PIN=(ROOT/"vendor/sources/eden/src/video_core/host1x/syncpoint_manager.cpp").read_text()
ACT=(ROOT/"vendor/encore-active/eden-core/src/video_core/host1x/syncpoint_manager.cpp").read_text()
HDR=(ROOT/"vendor/sources/eden/src/video_core/host1x/syncpoint_manager.h").read_text()
SELECTED_HDR=(ROOT/"vendor/encore-active/eden-core/overrides/video_core/host1x/syncpoint_manager.h").read_text()
CM=(ROOT/"headless/CMakeLists.txt").read_text()
FAST=(ROOT/".github/workflows/encore-core-fast-gate.yml").read_text()
FULL=(ROOT/".github/workflows/encore-core-preflight.yml").read_text()
COMMAND="python3 -B tools/check-native-host1x-increment-handoff-host.py"
assert COMMAND in FAST and COMMAND in FULL
assert 'list(APPEND video_sources "' in CM and "EDEN_MAINTAINED_HOST1X_SYNCPOINT" in CM
assert 'list(REMOVE_ITEM video_sources host1x/syncpoint_manager.cpp)' in CM
assert "using ActionHandle = u64;" in HDR
assert "struct DueActions" in HDR and "action_done_cv" in HDR
assert "std::list<RegisteredAction>::iterator" not in HDR
for token in ("due.pending.splice(", "due.running = due.pending.front().id;",
              "action_done_cv.notify_all();", "wait_cv.notify_all();"):
    assert token in ACT, token
assert ACT.index("wait_cv.notify_all();") < ACT.index("due.pending.splice(")
assert "DueActions" not in PIN and "using ActionHandle = u64;" not in PIN
assert "void WaitHost(u32 syncpoint_id, u32 expected_value, std::stop_token stop);" in SELECTED_HDR
assert "EDEN_HOST1X_SYNCPOINT_ABI_ROOT" in CM
assert 'target_include_directories(video_core BEFORE PUBLIC "${EDEN_HOST1X_SYNCPOINT_ABI_ROOT}")' in CM

HARNESS=r"""
#include <atomic>
#include <cassert>
#include <chrono>
#include <future>
#include <thread>
#include <vector>
#include "video_core/host1x/syncpoint_manager.h"
using Tegra::Host1x::SyncpointManager;
using namespace std::chrono_literals;

int main(){
  SyncpointManager m;

  // Reentrance: maintained callbacks run outside the global action-list lock.
  std::atomic<unsigned> callbacks{},nested{};
  m.RegisterGuestAction(1,1,[&]{
    m.RegisterGuestAction(4,0,[&]{++nested;});
    ++callbacks;
  });
  m.IncrementGuest(1);
  assert(callbacks==1 && nested==1);

  // Threshold ordering and ordinary cancellation by stable numeric handle.
  std::vector<u32> ordered;
  m.RegisterGuestAction(2,3,[&]{ordered.push_back(3);});
  m.RegisterGuestAction(2,1,[&]{ordered.push_back(1);});
  m.RegisterGuestAction(2,2,[&]{ordered.push_back(2);});
  auto future=m.RegisterGuestAction(2,4,[&]{assert(false);});
  assert(future!=0);
  m.IncrementGuest(2); m.IncrementGuest(2); m.IncrementGuest(2);
  m.DeregisterGuestAction(2,future);
  m.IncrementGuest(2);
  assert((ordered==std::vector<u32>{1,2,3}));

  // Equal-threshold LIFO makes blocker first, leaving cancellable work in
  // DueActions::pending while the callback executes without the global guard.
  std::promise<void> entered,release,waited;
  auto entered_f=entered.get_future(), waited_f=waited.get_future();
  std::atomic<unsigned> cancelled{},same_id{},independent{};
  auto pending_handle=m.RegisterGuestAction(5,1,[&]{++cancelled;});
  auto running_handle=m.RegisterGuestAction(5,1,[&]{
    entered.set_value();
    release.get_future().wait();
  });
  assert(pending_handle && running_handle);
  std::thread waiter([&]{m.WaitGuest(5,1); waited.set_value();});
  std::thread first([&]{m.IncrementGuest(5);});
  assert(entered_f.wait_for(2s)==std::future_status::ready);
  // Counter publication/waiter wake is independent of the blocked callback.
  assert(waited_f.wait_for(1s)==std::future_status::ready);

  // Pending action can be cancelled immediately while another due action runs.
  auto pending_cancel=std::async(std::launch::async,[&]{
    m.DeregisterGuestAction(5,pending_handle);
  });
  assert(pending_cancel.wait_for(1s)==std::future_status::ready);
  pending_cancel.get();

  // Cancelling the currently running callback waits until callback completion.
  auto running_cancel=std::async(std::launch::async,[&]{
    m.DeregisterGuestAction(5,running_handle);
  });
  assert(running_cancel.wait_for(100ms)==std::future_status::timeout);

  // Other Host1x work and a later threshold on the same id are not globally
  // serialized behind the blocked callback.
  m.RegisterHostAction(7,1,[&]{++independent;});
  m.IncrementHost(7);
  m.WaitHost(7,1);
  assert(independent==1);
  m.RegisterGuestAction(5,2,[&]{++same_id;});
  std::thread second([&]{m.IncrementGuest(5);});
  second.join();
  assert(same_id==1);

  release.set_value();
  first.join(); waiter.join();
  assert(running_cancel.wait_for(2s)==std::future_status::ready);
  running_cancel.get();
  assert(cancelled==0);

  // Legacy guest progress is immediate, but NS2 native completion is
  // mirrored only on host retirement, before publishing the wide counter.
  std::atomic<u64> mirrored{},observed{};
  m.SetGuestMirror([&](u32 id,u64 value){
    assert(id==3); mirrored=value; observed=m.GetNativeGuestSyncpointValue(id);
  });
  m.IncrementGuest(3);
  assert(mirrored==0 && m.GetGuestSyncpointValue(3)==1 &&
         m.GetNativeGuestSyncpointValue(3)==0);
  m.IncrementHost(3);
  assert(mirrored==1 && observed==0 && m.GetHostSyncpointValue(3)==1 &&
         m.GetNativeGuestSyncpointValue(3)==1);
  m.WithGuestValuesStable([&]{assert(m.GetNativeGuestSyncpointValue(3)==1);});
  m.SetGuestMirror({});

  std::atomic<unsigned> stress{};
  for(u32 i=1;i<=256;++i){
    m.RegisterGuestAction(9,i,[&]{++stress;});
    m.IncrementGuest(9);
  }
  assert(stress==256);
}
"""
compiler=shutil.which("clang++-18") or shutil.which("clang++") or shutil.which("g++")
assert compiler,"C++20 compiler required"
with tempfile.TemporaryDirectory(prefix="encore-host1x-current-") as d:
    t=Path(d)
    (t/"common").mkdir(parents=True)
    (t/"common/common_types.h").write_text(
        "#pragma once\n#include <cstdint>\nusing u32=std::uint32_t; using u64=std::uint64_t;\n")
    (t/"common/logging.h").write_text("#pragma once\n#define LOG_ERROR(...) ((void)0)\n")
    (t/"test.cpp").write_text(HARNESS)
    for opt in ("-O0","-O2"):
        exe=t/("run"+opt)
        build=subprocess.run([compiler,"-std=c++20",opt,"-Wall","-Wextra","-Werror",
                              "-pthread","-fsanitize=undefined","-fno-sanitize-recover=all",
                              "-I",str(t),
                              "-I",str(ROOT/"vendor/encore-active/eden-core/overrides"),
                              "-I",str(ROOT/"vendor/sources/eden/src"),
                              str(ROOT/"vendor/encore-active/eden-core/src/video_core/host1x/syncpoint_manager.cpp"),
                              str(t/"test.cpp"),"-o",str(exe)],
                             capture_output=True,text=True,timeout=60)
        assert build.returncode==0,(opt,build.stderr[-5000:])
        run=subprocess.run([str(exe)],capture_output=True,text=True,timeout=20)
        assert run.returncode==0,(opt,run.stdout,run.stderr[-3000:])
        print("N04_HOST1X_CURRENT_PASS",opt,
              "numeric_handles=1 pending_cancel=1 running_cancel=1 same_id_progress=1 "
              "counter_wake=1 guest_mirror=1 stress=256")
print("N04_HOST1X_GUEST_PROGRESS_UNVERIFIED host_concurrency_only")
