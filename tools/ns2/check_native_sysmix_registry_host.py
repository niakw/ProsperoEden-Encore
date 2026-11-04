#!/usr/bin/env python3
"""P1.3: execute actual Sysmix registry source, concurrent capacity + batch preflight.

The tested methods are extracted verbatim from the maintained service header.
The KProcess, timer and host sink are deterministic mocks; no PS5 playback
or cross-process kernel scheduler behavior is claimed.
"""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/"vendor/encore-active/ns2-runtime/audio/core/hle/service/audio/nx2_sysmix_user_service.h"
body=SOURCE.read_text()
assert "std::map<u32, std::shared_ptr<SysmixOutput>> streams;" in body
assert "if (buffer.size() % sizeof(u32) == 0 && buffer.size() <= 32 * sizeof(u32))" in body
assert "result = streams->SetEngagedBatch(" in body
assert "std::memcpy(&ids[i], buffer.data() + i * sizeof(u32), sizeof(u32));" in body
assert "streams->CreateBounded(" in body
assert "catch (const std::bad_alloc&)" in body
assert "std::scoped_lock lock{mutex}" in body
def member(marker:str)->str:
    assert body.count(marker)==1,marker
    start=body.index(marker)
    opening=body.index("{",start)
    depth=0
    for stop in range(opening,len(body)):
        if body[stop]=="{": depth+=1
        elif body[stop]=="}":
            depth-=1
            if depth==0:
                return body[start:stop+1]
    raise AssertionError("incomplete method "+marker)
batch=member("    Result SetEngagedBatch(")
single=member("    Result SetEngaged(u32 id,")
create=member("    template <typename Factory>\n    Result CreateBounded(")
assert batch.count("std::scoped_lock lock{mutex};")==1
assert create.count("std::scoped_lock lock{mutex};")==1
assert batch.find("for (std::size_t i = 0; i < ids.size(); ++i)") < batch.find(
       "const Result result = selected[i]->SetEngaged(engaged);")
CPP=r'''
#include <algorithm>
#include <array>
#include <atomic>
#include <cassert>
#include <cstdint>
#include <cstdio>
#include <limits>
#include <map>
#include <memory>
#include <mutex>
#include <new>
#include <span>
#include <stdexcept>
#include <thread>
#include <utility>
#include <vector>
using u32=std::uint32_t;
struct Result {
 int raw{};
 constexpr bool IsFailure() const {return raw!=0;}
 constexpr operator bool() const {return raw==0;}
 constexpr bool operator==(Result other) const {return raw==other.raw;}
};
constexpr Result ResultSuccess{0}, ResultInvalidHandle{1},
 ResultInvalidArgument{2}, ResultNotFound{3},
 ResultOperationFailed{4}, ResultOutOfSessions{5};
#define R_UNLESS(expression,error) do {if(!(expression)) return (error);}while(false)
namespace Kernel{struct KProcess{u32 id;};}
struct SysmixOutput {
 const Kernel::KProcess* owner{};
 bool engaged{};
 bool open{true};
 bool fail_transition{};
 unsigned transitions{};
 explicit SysmixOutput(const Kernel::KProcess* who):owner{who}{}
 bool IsOwnedBy(const Kernel::KProcess* p) const {return owner==p && p;}
 u32 GetState() const{return open ? (engaged?2:1) : 0;}
 Result SetEngaged(bool want) {
  ++transitions;
  if(!open || (fail_transition && engaged!=want))
    return ResultOperationFailed;
  engaged=want;
  return ResultSuccess;
 }
};
struct Nx2SysmixStreams {
 std::mutex mutex;
 std::map<u32,std::shared_ptr<SysmixOutput>> streams;
 u32 next_id{1};
__BATCH__
__SINGLE__
__CREATE__
};
int main(){
 Kernel::KProcess owner{1}, foreign{2};
 Nx2SysmixStreams registry;
 constexpr int trials=96;
 std::atomic<int> success{},fail{}, collisions{};
 std::array<std::thread,trials> threads;
 std::array<u32,trials> ids{};
 for(int i=0;i<trials;++i){
  threads[i]=std::thread([&,i]{
   u32 id{};
   std::shared_ptr<SysmixOutput> value;
   auto r=registry.CreateBounded(
     [&](u32) { std::this_thread::yield();
                return std::make_shared<SysmixOutput>(&owner); },id,value);
   if(r==ResultSuccess){++success;ids[i]=id;assert(value);}
   else {assert(r==ResultOutOfSessions);++fail;}
  });
 }
 for(auto& t:threads)t.join();
 assert(success==32 && fail==trials-32);
 assert(registry.streams.size()==32 && registry.next_id==33);
 std::array<bool,33> seen{};
 for(auto id:ids) {
  if(!id)continue;
  assert(id<=32 && !seen[id]);seen[id]=true;
 }
 for(u32 i=1;i<=32;++i)assert(seen[i] && registry.streams.contains(i));
 u32 not_published=777;
 auto unchanged=registry.streams.begin()->second;
 std::shared_ptr<SysmixOutput> untouched=unchanged;
 assert(registry.CreateBounded(
   [&](u32){++collisions;return std::make_shared<SysmixOutput>(&owner);},
   not_published,untouched)==ResultOutOfSessions);
 assert(collisions==0 && not_published==777 && untouched==unchanged);
 // Bad ownership and a late invalid ID must not even start the first stream.
 auto first=registry.streams.at(1), second=registry.streams.at(2);
 for(auto batch: {std::vector<u32>{1,99}, std::vector<u32>{1,1},
                  std::vector<u32>{1,2,99}}) {
  const auto old1=first->transitions,old2=second->transitions;
  auto r=registry.SetEngagedBatch(batch,true,&owner);
  assert(r.IsFailure() && !first->engaged && !second->engaged);
  assert(first->transitions==old1 && second->transitions==old2);
 }
 assert(registry.SetEngaged(1,true,&foreign)==ResultInvalidHandle);
 assert(registry.SetEngaged(1,true,nullptr)==ResultInvalidHandle);
 assert(!first->engaged);
 second->open=false;
 assert(registry.SetEngagedBatch(std::array<u32,2>{1,2},true,&owner)==ResultOperationFailed);
 assert(!first->engaged);
 second->open=true;
 assert(registry.SetEngagedBatch(std::array<u32,2>{1,2},true,&owner)==ResultSuccess);
 assert(first->engaged && second->engaged);
 assert(registry.SetEngagedBatch(std::array<u32,2>{1,2},false,&owner)==ResultSuccess);
 assert(!first->engaged && !second->engaged);
 // The second sink fails its Start: undo the first, and surface failure.
 second->fail_transition=true;
 assert(registry.SetEngagedBatch(std::array<u32,2>{1,2},true,&owner)==ResultOperationFailed);
 assert(!first->engaged && !second->engaged);
 second->fail_transition=false;
 // Failed factories and duplicate IDs preserve the map and next ID.
 registry.streams.erase(32);
 const u32 before=registry.next_id;
 u32 discarded_id=55;std::shared_ptr<SysmixOutput> discarded;
 assert(registry.CreateBounded([&](u32) {return std::shared_ptr<SysmixOutput>{};},
    discarded_id,discarded)==ResultOperationFailed);
 assert(discarded_id==55 && !discarded && registry.next_id==before);
 bool threw{};
 try {
  (void)registry.CreateBounded([&](u32)->std::shared_ptr<SysmixOutput>{
   throw std::bad_alloc{};},discarded_id,discarded);
 } catch(const std::bad_alloc&) {threw=true;}
 assert(threw && registry.next_id==before && registry.streams.size()==31);
 // Create an ID once and reject its reuse, even after reset/corruption.
 registry.next_id=1;
 assert(registry.CreateBounded(
   [&](u32){return std::make_shared<SysmixOutput>(&owner);},
   discarded_id,discarded)==ResultOutOfSessions);
 assert(registry.next_id==1 && registry.streams.size()==31);
 registry.next_id=std::numeric_limits<u32>::max();
 assert(registry.CreateBounded(
   [&](u32){return std::make_shared<SysmixOutput>(&owner);},
   discarded_id,discarded)==ResultSuccess);
 assert(discarded_id==std::numeric_limits<u32>::max());
 assert(registry.next_id==0 && registry.streams.size()==32);
 registry.streams.erase(discarded_id);
 assert(registry.CreateBounded(
   [&](u32){return std::make_shared<SysmixOutput>(&owner);},
   discarded_id,discarded)==ResultOutOfSessions);
 assert(registry.streams.size()==31);
 std::array<u32,33> too_many{};
 assert(registry.SetEngagedBatch(too_many,true,&owner)==ResultInvalidArgument);
 assert(registry.SetEngagedBatch({},true,&owner)==ResultSuccess);
 std::puts("P1_3_SYSMIX_REAL_REGISTRY_PASS concurrent=96 admitted=32 "
   "invalid_batch_no_effect=1 ownership=1 rollback=1 factory_exception=1 "
   "id_overflow=1");
}
'''
CPP=CPP.replace("__BATCH__",batch).replace("__SINGLE__",single).replace("__CREATE__",create)
assert "__" not in CPP.replace("std::numeric_limits", "") or "__" not in (batch+single+create)
compilers=list(dict.fromkeys(filter(None,[shutil.which("clang++"),shutil.which("g++")])))
assert compilers
env=os.environ.copy()
sdk=Path("/Library/Developer/CommandLineTools/SDKs/MacOSX15.4.sdk")
if sdk.is_dir():env["SDKROOT"]=str(sdk)
with tempfile.TemporaryDirectory(prefix="encore-sysmix-registry-") as tmp:
    source=Path(tmp)/"registry.cpp"
    source.write_text(CPP)
    for compiler in compilers:
        for optimization in ("-O0","-O2"):
            exe=Path(tmp)/(Path(compiler).name+optimization)
            args=[compiler,"-std=c++20",optimization,"-Wall","-Wextra","-Werror",
                  "-pthread","-fsanitize=undefined","-fno-sanitize-recover=all",
                  str(source),"-o",str(exe)]
            build=subprocess.run(args,env=env,capture_output=True,text=True,timeout=70)
            assert build.returncode==0,(compiler,optimization,build.stderr[-5500:])
            result=subprocess.run([str(exe)],env=env,capture_output=True,text=True,timeout=35)
            assert result.returncode==0,(compiler,optimization,result.stdout,result.stderr)
            print(Path(compiler).name,optimization,result.stdout.strip(),flush=True)
