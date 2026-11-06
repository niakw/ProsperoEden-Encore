#!/usr/bin/env python3
"""P1.2/P1.3: replay the exact maintained NVMap SMMU reclaim loop on host."""
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

root = Path(__file__).resolve().parents[2]
source = root / 'vendor/encore-active/eden-core/src/core/hle/service/nvdrv/core/nvmap.cpp'
if not source.exists():
    source = root.parent / 'vendor/encore-active/eden-core/src/core/hle/service/nvdrv/core/nvmap.cpp'
body = source.read_text()
start = '            std::size_t busy_candidates{};\n            while ((address = smmu.Allocate(aligned_up)) == 0) {'
end = '\n\n            handle_description->d_address = address;'
assert body.count(start) == 1 and body.count(end) == 1
loop = body[body.index(start):body.index(end, body.index(start))]
assert 'unmap_queue.empty() || busy_candidates >= unmap_queue.size()' in loop
assert 'std::unique_lock freeLock(freeHandleDesc->mutex, std::try_to_lock);' in loop
assert 'unmap_queue.splice(unmap_queue.end(), unmap_queue,' in loop
assert 'freeHandleDesc->d_address' in loop
assert 'if (handle_description->d_address)' not in loop
assert 'unmap_queue.pop_front();' in loop
assert 'UnmapHandle(*freeHandleDesc);' in loop
assert 'return 0;' in loop

fixture = r'''
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <list>
#include <memory>
#include <mutex>
#include <optional>
#define LOG_ERROR(...) ((void)0)
using DAddr=std::uint64_t;
struct Handle;
using Queue=std::list<std::shared_ptr<Handle>>;
struct Handle {
 std::mutex mutex;
 std::optional<Queue::iterator> unmap_queue_entry{};
 DAddr d_address{};
};
struct Smmu {
 std::size_t remaining{};
 unsigned allocations{};
 DAddr Allocate(std::size_t size) {
  ++allocations;
  if (remaining<size) return 0;
  remaining-=size;
  return DAddr{0x100000}+allocations*0x10000;
 }
 void Free(std::size_t size) {remaining+=size;}
};
struct NvMap {
 Queue unmap_queue{};
 std::mutex unmap_queue_lock{};
 Smmu smmu{};
 unsigned reclaimed{};
 void Enqueue(const std::shared_ptr<Handle>& h) {
  unmap_queue.push_back(h);
  if(h) h->unmap_queue_entry=std::prev(unmap_queue.end());
 }
 void UnmapHandle(Handle& h) {
  assert(h.unmap_queue_entry && h.d_address);
  unmap_queue.erase(*h.unmap_queue_entry);
  h.unmap_queue_entry.reset();
  h.d_address=0;
  smmu.Free(4096);
  ++reclaimed;
 }
 DAddr TryPin(const std::shared_ptr<Handle>& handle_description,
              std::size_t aligned_up) {
  DAddr address{};
  auto& smmu=this->smmu;
__REAL_LOOP__
  return address;
 }
};
int main() {
 auto h=std::make_shared<Handle>();
 NvMap empty;
 assert(empty.TryPin(h,4096)==0);
 assert(empty.smmu.allocations==1 && empty.reclaimed==0);
 NvMap one;
 auto old=std::make_shared<Handle>();old->d_address=0x8000;
 one.Enqueue(old);
 assert(one.TryPin(h,4096)!=0);
 assert(old->d_address==0 && !old->unmap_queue_entry && one.unmap_queue.empty());
 assert(one.reclaimed==1 && one.smmu.allocations==2);
 NvMap two;
 auto a=std::make_shared<Handle>();a->d_address=0x8000;
 auto b=std::make_shared<Handle>();b->d_address=0x9000;
 two.Enqueue(a);two.Enqueue(b);
 assert(two.TryPin(h,8192)!=0 && two.reclaimed==2);
 assert(two.unmap_queue.empty());
 NvMap stale;
 stale.Enqueue(std::shared_ptr<Handle>{});
 auto zero=std::make_shared<Handle>();stale.Enqueue(zero);
 auto valid=std::make_shared<Handle>();valid->d_address=0xa000;stale.Enqueue(valid);
 assert(stale.TryPin(h,4096)!=0 && stale.reclaimed==1);
 assert(stale.unmap_queue.empty() && !zero->unmap_queue_entry);
 NvMap self;
 self.Enqueue(h);
 assert(self.TryPin(h,4096)==0 && !h->unmap_queue_entry && self.unmap_queue.empty());
 NvMap exhausted;
 exhausted.Enqueue(std::shared_ptr<Handle>{});
 assert(exhausted.TryPin(h,8192)==0 && exhausted.smmu.allocations==2);
 NvMap busy;
 auto locked=std::make_shared<Handle>();locked->d_address=0x1000;
 busy.Enqueue(locked);
 {
  std::unique_lock guard(locked->mutex);
  assert(busy.TryPin(h,4096)==0 && busy.reclaimed==0);
  assert(busy.unmap_queue.size()==1);
 }
 assert(busy.TryPin(h,4096)!=0 && busy.reclaimed==1);
 NvMap mixed;
 auto busy_first=std::make_shared<Handle>();busy_first->d_address=0x2000;
 auto available=std::make_shared<Handle>();available->d_address=0x3000;
 mixed.Enqueue(busy_first);mixed.Enqueue(available);
 {
  std::unique_lock guard(busy_first->mutex);
  assert(mixed.TryPin(h,4096)!=0 && mixed.reclaimed==1);
  assert(mixed.unmap_queue.size()==1);
  assert(mixed.unmap_queue.front().get()==busy_first.get());
 }
 assert(mixed.TryPin(h,4096)!=0 && mixed.reclaimed==2);
}
'''.replace('__REAL_LOOP__',loop)
compilers = list(dict.fromkeys(filter(None,(shutil.which('clang++'),shutil.which('g++')))))
assert compilers
env = os.environ.copy()
sdk=Path('/Library/Developer/CommandLineTools/SDKs/MacOSX15.4.sdk')
if sdk.is_dir():env['SDKROOT']=str(sdk)
with tempfile.TemporaryDirectory(prefix='eden-smmu-reclaim-') as folder:
    cpp=Path(folder)/'reclaim.cpp';cpp.write_text(fixture)
    for compiler in compilers:
        for optimization in ('-O0','-O2'):
            exe=Path(folder)/(Path(compiler).name+optimization)
            cmd=[compiler,'-std=c++20',optimization,'-Wall','-Wextra','-Werror',
                 '-fsanitize=undefined','-fno-sanitize-recover=all',str(cpp),'-o',str(exe)]
            done=subprocess.run(cmd,text=True,capture_output=True,env=env,timeout=80)
            assert done.returncode==0,(cmd,done.stderr[-2500:])
            test=subprocess.run([str(exe)],text=True,capture_output=True,env=env,timeout=20)
            assert test.returncode==0,(cmd,test.stderr[-2500:])
            print(Path(compiler).name,optimization,'P1_NATIVE_NVDRV_SMMU_RECLAIM_PASS',flush=True)
print('P1_NVDRV_SMMU_RECLAIM_VALIDATION_PASS empty=fail finite_queue=1 valid_reclaim=1 lock_inversion=refused busy_skip=1 no_faux_success=1')
