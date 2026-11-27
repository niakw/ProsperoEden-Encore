#!/usr/bin/env python3
"""ASan/UBSan regression: canonical native worker Stop drains queued work after join."""
from pathlib import Path
import shutil,subprocess,tempfile
ROOT=Path(__file__).resolve().parents[1]
worker=(ROOT/"vendor/encore-active/eden/src/video_core/gpu_thread.cpp").read_text()
hdr=(ROOT/"vendor/encore-active/eden/src/common/bounded_threadsafe_queue.h").read_text()
ci=(ROOT/".github/workflows/encore-core-preflight.yml").read_text()
assert "python3 -B tools/check-native-gpu-worker-restart-drain-host.py" in ci
anchor="void ThreadManager::Stop() {"; tail="\n} // namespace VideoCommon::GPUThread"
assert worker.count(anchor)==1
body=worker[worker.index(anchor):worker.index(tail,worker.index(anchor))]
assert body.index("pthread_join(thread, nullptr)")<body.index("state.queue.TryPop(abandoned)")
assert body.index("std::scoped_lock lock{state.write_lock};")<body.index("state.queue.TryPop(abandoned)")
assert "stop_source.request_stop();" in body
cpp=r"""
#include <array>
#include <atomic>
#include <cassert>
#include <condition_variable>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <memory>
#include <mutex>
#include <pthread.h>
#include <stop_token>
#include <thread>
#include <utility>
#include "common/bounded_threadsafe_queue.h"
struct CommandDataContainer { std::uint64_t id{}; std::shared_ptr<int> lifetime{};
 CommandDataContainer()=default; CommandDataContainer(std::uint64_t key,std::shared_ptr<int> ptr):id(key),lifetime(std::move(ptr)){} };
struct ThreadManager { struct SynchState { std::mutex write_lock; Common::SPSCQueue<CommandDataContainer,256> queue; } state;
 std::stop_source stop_source{}; pthread_t thread{}; bool thread_joinable=false; void Stop(); };
INJECT_STOP
int main(){
 ThreadManager manager; auto resource=std::make_shared<int>(17); std::weak_ptr<int> weak=resource;
 assert(manager.state.queue.TryEmplace(11,resource)); assert(manager.state.queue.TryEmplace(12,resource));
 resource.reset(); assert(!weak.expired()); manager.Stop(); assert(weak.expired());
 CommandDataContainer out{}; assert(!manager.state.queue.TryPop(out)); manager.Stop();
 manager.stop_source=std::stop_source{}; assert(manager.state.queue.TryEmplace(31,std::shared_ptr<int>{}));
 assert(manager.state.queue.TryPop(out)&&out.id==31); assert(!manager.state.queue.TryPop(out));
 manager.stop_source=std::stop_source{};
 int rc=pthread_create(&manager.thread,nullptr,[](void* arg)->void*{
   auto& self=*static_cast<ThreadManager*>(arg);
   while(!self.stop_source.get_token().stop_requested()) std::this_thread::yield();
   return nullptr;
 },&manager);
 assert(rc==0); manager.thread_joinable=true; assert(manager.state.queue.TryEmplace(41,std::shared_ptr<int>{}));
 manager.Stop(); assert(!manager.thread_joinable&&manager.stop_source.stop_requested()); assert(!manager.state.queue.TryPop(out));
 std::puts("ENCORE_GPU_WORKER_RESTART_DRAIN_HOST_PASS");
}
""".replace("INJECT_STOP",body)
compiler=shutil.which("clang++-18") or shutil.which("clang++") or shutil.which("g++"); assert compiler
with tempfile.TemporaryDirectory(prefix="encore-gpu-worker-restart-") as name:
 folder=Path(name); common=folder/"common"; common.mkdir()
 (common/"polyfill_thread.h").write_text("#pragma once\n#include <stop_token>\n")
 (common/"bounded_threadsafe_queue.h").write_text(hdr)
 source=folder/"test.cpp"; exe=folder/"test"; source.write_text(cpp)
 subprocess.run([compiler,"-std=c++20","-O1","-g","-pthread","-Wall","-Wextra","-Werror",
   "-fsanitize=address,undefined","-fno-sanitize-recover=all","-I",str(folder),str(source),"-o",str(exe)],check=True,timeout=90)
 subprocess.run([str(exe)],check=True,timeout=30)
print("NATIVE_GPU_WORKER_RESTART_DRAIN_HOST_PASS canonical_owner=1")
