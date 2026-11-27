#!/usr/bin/env python3
"""N04: current Host1x late-ready RegisterAction reentrance witness.

Compiles the exact maintained RegisterAction body at O0/O2 and deterministically
forces the syncpoint to become ready after the first lock-free check but before
the guarded recheck. The callback must execute after the guard scope ends.
The pinned source is retained as a source-level negative showing its callback
was invoked while std::scoped_lock still owned the guard.
"""
from pathlib import Path
import shutil, subprocess, tempfile

ROOT=Path(__file__).resolve().parents[1]
PIN=(ROOT/"vendor/sources/eden/src/video_core/host1x/syncpoint_manager.cpp").read_text()
ACT=(ROOT/"vendor/encore-active/eden/src/video_core/host1x/syncpoint_manager.cpp").read_text()
HDR=(ROOT/"vendor/encore-active/eden-core/overrides/video_core/host1x/syncpoint_manager.h").read_text()
CM=(ROOT/"headless/CMakeLists.txt").read_text()
FAST=(ROOT/".github/workflows/encore-core-fast-gate.yml").read_text()
FULL=(ROOT/".github/workflows/encore-core-preflight.yml").read_text()
NAME="python3 -B tools/check-native-host1x-register-reentrant-host.py"
assert NAME in FAST and NAME in FULL
assert "list(REMOVE_ITEM video_sources host1x/syncpoint_manager.cpp)" in CM
assert "EDEN_MAINTAINED_HOST1X_SYNCPOINT" in CM
assert "using ActionHandle = u64;" in HDR
assert "std::list<RegisteredAction>::iterator" not in HDR

# The full native PS5 graph can materialize a stale Eden header under its
# dependency checkout, even when the vendor's source/header unit test passes.
# Require CMake to select the matching reviewed pinned header for both
# video_core (maintained .cpp) and core (NS2 graphics supervisor).
for token in (
    'set(EDEN_MAINTAINED_HOST1X_HEADER',
    'vendor/encore-active/eden-core/overrides/video_core/host1x/syncpoint_manager.h',
    'configure_file("${EDEN_MAINTAINED_HOST1X_HEADER}"',
    'target_include_directories(video_core BEFORE PUBLIC "${EDEN_HOST1X_SYNCPOINT_ABI_ROOT}")',
    'target_include_directories(core BEFORE PUBLIC "${EDEN_HOST1X_SYNCPOINT_ABI_ROOT}")',
):
    assert token in CM, ("Native Host1x ABI header not selected",token)
for token in (
    'using ActionHandle = u64;',
    'void SetGuestMirror(GuestMirror mirror);',
    'void WithGuestValuesStable(Func&& func)',
    'u64 last_action_id{};',
    'struct DueActions {',
    'std::condition_variable action_done_cv;',
):
    assert token in HDR, token

# Compile the ACTUAL maintained Host1x TU with a clean stub platform and a
# conflicting old header. The reviewed include root MUST win; a reversed
# include order is the deliberate negative control.
vendor_root=ROOT/"vendor"
host1x_source=vendor_root/"encore-active/eden-core/src/video_core/host1x/syncpoint_manager.cpp"
host1x_header=vendor_root/"encore-active/eden-core/overrides/video_core/host1x/syncpoint_manager.h"
compiler=shutil.which("clang++-18") or shutil.which("clang++") or shutil.which("g++")
assert compiler
with tempfile.TemporaryDirectory(prefix="encore-host1x-native-abi-") as d:
    base=Path(d)
    selected=base/"reviewed"
    stale=base/"stale"
    sdk=base/"sdk"
    for root in (selected,stale):
        (root/"video_core/host1x").mkdir(parents=True)
    (sdk/"common").mkdir(parents=True)
    (selected/"video_core/host1x/syncpoint_manager.h").write_text(HDR)
    (stale/"video_core/host1x/syncpoint_manager.h").write_text(
        '#pragma once\n#include "common/common_types.h"\n'
        'namespace Tegra::Host1x { class SyncpointManager { public:\n'
        ' using ActionHandle = int; }; }\n')
    (sdk/"common/common_types.h").write_text(
        "#pragma once\n#include <cstdint>\n"
        "using u32=std::uint32_t; using u64=std::uint64_t;\n")
    (sdk/"common/logging.h").write_text(
        "#pragma once\n#define LOG_ERROR(...) ((void)0)\n")
    main=base/"main.cpp"
    main.write_text(r'''
#include <type_traits>
#include "video_core/host1x/syncpoint_manager.h"
using Tegra::Host1x::SyncpointManager;
static_assert(std::is_same_v<SyncpointManager::ActionHandle, u64>);
static_assert(SyncpointManager::NUM_MAX_SYNCPOINTS == 192);
int main() {
  SyncpointManager sync;
  sync.SetGuestMirror([](u32, u32){});
  sync.WithGuestValuesStable([&] { (void)sync.GetGuestSyncpointValue(7); });
  auto handle=sync.RegisterGuestAction(7, 2, []{});
  if (!handle) return 1;
  sync.DeregisterGuestAction(7, handle);
  return 0;
}
''')
    base_cmd=[compiler,"-std=c++20","-O0","-Wall","-Wextra","-Werror",
              "-pthread","-I",str(sdk)]
    positive=subprocess.run(base_cmd+["-I",str(selected),"-I",str(stale),
                           str(host1x_source),str(main),"-o",str(base/"match")],
                          capture_output=True,text=True,timeout=60)
    assert positive.returncode==0,("Matching shipping Host1x API did not compile",positive.stderr[-4000:])
    run=subprocess.run([str(base/"match")],capture_output=True,text=True,timeout=15)
    assert run.returncode==0,(run.returncode,run.stderr)
    negative=subprocess.run(base_cmd+["-I",str(stale),"-I",str(selected),
                           str(host1x_source),str(main),"-o",str(base/"stale-bin")],
                          capture_output=True,text=True,timeout=60)
    assert negative.returncode!=0,"Stale Host1x header unexpectedly accepted"
    print("NATIVE_HOST1X_SHIPPING_ABI_PASS selected_header=1 numeric_handles=1 guest_mirror=1 stale_negative=1")

def extract(text,name):
    assert text.count(name)==1,name
    start=text.index(name); opening=text.index("{",start); depth=0
    for i in range(opening,len(text)):
        if text[i]=="{": depth+=1
        elif text[i]=="}":
            depth-=1
            if depth==0: return text[start:i+1]
    raise AssertionError(name)

SIG="SyncpointManager::ActionHandle SyncpointManager::RegisterAction("
pinned=extract(PIN,SIG)
current=extract(ACT,SIG)
# Historical negative: late-ready action is called before scoped_lock leaves scope.
assert "std::scoped_lock lk(guard);" in pinned
pinned_late=pinned.index("if (syncpoint.load(std::memory_order_relaxed) >= expected_value)")
assert pinned_late < pinned.index("action();",pinned_late) < pinned.index("return {};",pinned_late)
# Current upstream/Lichii contract: only insertion happens under guard; late-ready callback is outside.
for token in (
    "{\n        std::scoped_lock lk(guard);",
    "if (syncpoint.load(std::memory_order_relaxed) < expected_value)",
    "do { ++last_action_id; } while (last_action_id == 0);",
    "emplace(it, expected_value, last_action_id, std::move(action))->id;",
):
    assert token in current,token
guard_end=current.index("    }\n    action();")
assert guard_end > current.index("std::scoped_lock lk(guard);")
assert "action();\n    return {};" in current[guard_end:]

# Instrument only the host witness so the main thread knows the worker passed
# the first lock-free check before publishing the new syncpoint value.
probe='    {\n        std::scoped_lock lk(guard);'
assert current.count(probe)==1
instrumented=current.replace(
    probe,
    '    prelock_hits.fetch_add(1, std::memory_order_release);\n'+probe,1)

CPP=r"""
#include <atomic>
#include <cassert>
#include <cstdint>
#include <functional>
#include <list>
#include <mutex>
#include <thread>
using u32=std::uint32_t; using u64=std::uint64_t;
static std::atomic<unsigned> prelock_hits{};
class SyncpointManager {
public:
 struct RegisteredAction {
   RegisteredAction(u32 v,u64 i,std::function<void()>&& a)
      :expected_value(v),id(i),action(std::move(a)){}
   u32 expected_value; u64 id; std::function<void()> action;
 };
 using ActionHandle=u64;
 std::atomic<u32> syncpoint{};
 std::list<RegisteredAction> actions;
 std::mutex guard;
 u64 last_action_id{};
 ActionHandle RegisterAction(std::atomic<u32>&,std::list<RegisteredAction>&,
                             u32,std::function<void()>&&);
 template<class F> ActionHandle Register(u32 expected,F&& f) {
   return RegisterAction(syncpoint,actions,expected,std::forward<F>(f));
 }
};
__METHOD__
int main(){
 SyncpointManager m;
 std::atomic<unsigned> callbacks{},nested{};
 for(unsigned round=0;round<32;++round){
   m.syncpoint.store(0,std::memory_order_release);
   const unsigned before=prelock_hits.load(std::memory_order_acquire);
   std::unique_lock hold{m.guard};
   std::thread worker([&]{
     const auto h=m.Register(1,[&]{
       assert(m.guard.try_lock());
       m.guard.unlock();
       ++callbacks;
       // Re-enter RegisterAction from the callback: an already-ready callback
       // must not be under the global action-list mutex.
       const auto inner=m.Register(0,[&]{++nested;});
       assert(inner==0);
     });
     assert(h==0);
   });
   while(prelock_hits.load(std::memory_order_acquire)==before)
     std::this_thread::yield();
   m.syncpoint.store(1,std::memory_order_release);
   hold.unlock();
   worker.join();
 }
 assert(callbacks==32 && nested==32 && m.actions.empty());
 // Non-ready insertion still returns a stable non-zero numeric handle.
 m.syncpoint.store(0,std::memory_order_release);
 auto pending=m.Register(3,[]{});
 assert(pending!=0 && m.actions.size()==1 && m.actions.front().id==pending);
}
""".replace("__METHOD__",instrumented)
compiler=shutil.which("clang++-18") or shutil.which("clang++") or shutil.which("g++")
assert compiler,"Host C++20 compiler required"
with tempfile.TemporaryDirectory(prefix="encore-host1x-register-") as d:
    p=Path(d); src=p/"test.cpp"; src.write_text(CPP)
    for opt in ("-O0","-O2"):
        exe=p/("test"+opt)
        build=subprocess.run([compiler,"-std=c++20",opt,"-Wall","-Wextra","-Werror",
                              "-pthread","-fsanitize=undefined","-fno-sanitize-recover=all",
                              str(src),"-o",str(exe)],capture_output=True,text=True,timeout=60)
        assert build.returncode==0,(opt,build.stderr[-4000:])
        run=subprocess.run([str(exe)],capture_output=True,text=True,timeout=20)
        assert run.returncode==0,(opt,run.stdout,run.stderr[-3000:])
        print("N04_HOST1X_REGISTER_REENTRANT_PASS",opt,
              "late_ready=32 callback_outside_guard=1 numeric_handle=1")
print("N04_HOST1X_PINNED_NEGATIVE_SOURCE_PASS callback_under_guard=1")
