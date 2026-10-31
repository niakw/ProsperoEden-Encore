#!/usr/bin/env python3
"""N72: execute actual native Scheduler::BindSparseImage method, including mutex."""
from pathlib import Path
import subprocess
import tempfile
ROOT=Path(__file__).resolve().parents[2]
V=ROOT/"vendor/encore-active/eden-vulkan"
cpp=(V/"vulkan_scheduler.cpp").read_text()
hdr=(V/"include/video_core/renderer_vulkan/vk_scheduler.h").read_text()
a="// NS2 N72 BEGIN: serialized sparse Vulkan page submission"
b="// NS2 N72 END"
assert cpp.count(a)==cpp.count(b)==1
fragment=cpp[cpp.index(a)+len(a):cpp.index(b)]
assert fragment.count("Scheduler::BindSparseImage(")==1
assert "std::scoped_lock lock{submit_mutex};" in fragment
assert "device.GetGraphicsQueue().BindSparseImage(" in fragment
assert "VK_ERROR_INITIALIZATION_FAILED" in fragment
assert hdr.count("EDEN_NS2_SPARSE_QUEUE_BRIDGE") == 1
assert hdr.count("VkResult BindSparseImage(") == 1
# No fake copy of the N72 method: compile exact versioned vendor bytes.
source=r"""
#include <atomic>
#include <cassert>
#include <cstdint>
#include <cstdio>
#include <mutex>
#include <span>
#include <thread>
#include <vector>
using VkImage=void*;
using VkFence=void*;
using VkSemaphore=void*;
using VkResult=int;
constexpr VkResult VK_SUCCESS=0,VK_ERROR_INITIALIZATION_FAILED=-3,VK_ERROR_DEVICE_LOST=-4;
struct VkSparseImageMemoryBind {int n{};};
struct VkSparseMemoryBind {int n{};};
#define EDEN_NS2_SPARSE_QUEUE_BRIDGE 1
struct TestMutex {
 std::mutex inner;
 std::atomic<bool> held{false};
 void lock(){inner.lock(); held.store(true,std::memory_order_release);}
 void unlock(){held.store(false,std::memory_order_release); inner.unlock();}
 bool try_lock(){if(!inner.try_lock())return false;held.store(true,std::memory_order_release);return true;}
};
namespace Vulkan {
namespace vk {template<class T>using Span=std::span<const T>;}
struct Observed {
 std::atomic<int> entered{}, max_overlap{}, calls{}, bad_mutex{};
 std::atomic<int> wait_seen{}, signal_seen{};
 VkResult result=VK_SUCCESS;
};
struct Queue {
 TestMutex* gate{};
 Observed* state{};
 VkResult BindSparseImage(VkImage,Vulkan::vk::Span<VkSparseImageMemoryBind> tiles,
  Vulkan::vk::Span<VkSparseMemoryBind> tails,VkFence fence,
  VkSemaphore wait,VkSemaphore signal) const {
  assert(fence&&(tiles.size()||tails.size()));
  if(!gate->held.load(std::memory_order_acquire))++state->bad_mutex;
  const auto overlap=++state->entered;
  if(overlap>1)++state->max_overlap;
  ++state->calls;
  if(wait)++state->wait_seen;
  if(signal)++state->signal_seen;
  std::this_thread::yield();
  --state->entered;
  return state->result;
 }
};
struct Device{
 TestMutex* gate{};
 Observed* state{};
 Queue GetGraphicsQueue()const{return {gate,state};}
};
struct Scheduler {
 Device device{};
 TestMutex submit_mutex;
 Scheduler(Observed& state):device{&submit_mutex,&state}{}
 VkResult BindSparseImage(VkImage,vk::Span<VkSparseImageMemoryBind>,
  vk::Span<VkSparseMemoryBind>,VkFence,VkSemaphore,VkSemaphore);
};
""" + fragment + r"""
}
int main(){
 Vulkan::Observed state;
 Vulkan::Scheduler s(state);
 VkSparseImageMemoryBind tile{1};
 VkSparseMemoryBind tail{2};
 const std::span<const VkSparseImageMemoryBind> tiles{&tile,1}, none_tiles{};
 const std::span<const VkSparseMemoryBind> tails{&tail,1},none_tails{};
 const auto image=reinterpret_cast<VkImage>(0x123);
 const auto fence=reinterpret_cast<VkFence>(0x234);
 const auto wait=reinterpret_cast<VkSemaphore>(0x345);
 const auto signal=reinterpret_cast<VkSemaphore>(0x456);
 assert(s.BindSparseImage(nullptr,tiles,tails,fence,nullptr,nullptr)==VK_ERROR_INITIALIZATION_FAILED);
 assert(s.BindSparseImage(image,none_tiles,none_tails,fence,nullptr,nullptr)==VK_ERROR_INITIALIZATION_FAILED);
 assert(s.BindSparseImage(image,tiles,tails,nullptr,nullptr,nullptr)==VK_ERROR_INITIALIZATION_FAILED);
 assert(state.calls==0);
 assert(s.BindSparseImage(image,tiles,tails,fence,wait,signal)==VK_SUCCESS);
 assert(state.wait_seen==1 && state.signal_seen==1);
 state.result=VK_ERROR_DEVICE_LOST;
 assert(s.BindSparseImage(image,tiles,none_tails,fence,nullptr,nullptr)==VK_ERROR_DEVICE_LOST);
 state.result=VK_SUCCESS;
 std::vector<std::thread> threads;
 for(int t=0;t<6;++t){
  threads.emplace_back([&]{for(int i=0;i<200;++i)
   assert(s.BindSparseImage(image,tiles,tails,fence,nullptr,nullptr)==VK_SUCCESS);});
 }
 for(auto& thread:threads)thread.join();
 assert(state.calls==1202);
 assert(state.bad_mutex==0 && state.max_overlap==0 && state.entered==0);
 // The mutex is released even on VK_ERROR_DEVICE_LOST.
 assert(s.submit_mutex.try_lock()); s.submit_mutex.unlock();
 std::puts("N72_REAL_NATIVE_SCHEDULER_QUEUE_LOCK_PASS");
}
"""
with tempfile.TemporaryDirectory(prefix="ns2-n72-scheduler-") as folder:
    root=Path(folder)
    target=root/"test.cpp";target.write_text(source)
    for compiler in ("clang++","g++"):
        exe=root/compiler.replace("+","p")
        subprocess.run([compiler,"-std=c++20","-O2","-Wall","-Wextra","-Werror",
            "-pthread","-fsanitize=undefined","-fno-sanitize-recover=all",
            str(target),"-o",str(exe)],check=True)
        subprocess.run([str(exe)],check=True)
print("N72_REAL_VENDOR_SCHEDULER_CLANG_GCC_UBSAN_PASS")
