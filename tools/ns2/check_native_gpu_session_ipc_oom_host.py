#!/usr/bin/env python3
"""Execute actual GSV notification MOVE owner and pre-import VA queries.
The event allocation and outgoing handle queue can fail independently."""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[2]
vendor=ROOT/"vendor"
owner=(vendor/"encore-active/ns2-runtime/gpu_session/core/hle/service/am/service/gpu_session.cpp").read_text()
def extract(begin,end):
    assert owner.count(begin)==owner.count(end)==1,(begin,end)
    return begin+owner.split(begin,1)[1].split(end,1)[0]
event=extract("void IGpuSession::GetNotificationEvent(","std::shared_ptr<Nvidia::Devices::nvhost_as_gpu>\nIGpuSession::ResolveOpenedAddressSpace(")
partition=extract("void IGpuSession::GetUserPartition(","void IGpuSession::CreateGraphicsDevice(")
assert "ctx.AddMoveObject(readable);" in event and "readable->Close(kernel);" in event
assert "IPC::ResponseBuilder rb{ctx, 2, 0, 1};" in event
assert "ResolveOpenedAddressSpace" not in partition and "m_module->Ioctl" not in partition
harness=r"""
#include <array>
#include <cassert>
#include <cstdint>
#include <memory>
#include <mutex>
#include <new>
#include <string>
#include <vector>
#include "core/hle/service/am/service/gpu_session_protocol.h"
#include "core/hle/service/nvdrv/devices/native_gpu_va_layout.h"
using u32=std::uint32_t;using u64=std::uint64_t;using u64_le=u64;
struct Result {u32 raw{};constexpr bool IsSuccess()const{return raw==0;}};
inline constexpr Result ResultSuccess{0};
namespace Kernel {
inline constexpr Result ResultInvalidCombination{1},ResultNotFound{2},ResultOutOfResource{3},ResultInvalidState{4};
struct KReadableEvent {
    unsigned refs{1};bool fail_open{};
    bool Open(int&){if(fail_open)return false;++refs;return true;}
    void Close(int&){assert(refs>1);--refs;}
};
struct KEvent {KReadableEvent readable;KReadableEvent& GetReadableEvent(){return readable;}};
}
struct HLERequestContext {
    std::array<u32,3> packet{};
    std::vector<u64> reply{};
    unsigned words{},moves{},response_moves{};
    bool fail_move{};
    const u32* CommandBuffer()const{return packet.data();}
    void AddMoveObject(Kernel::KReadableEvent* p){
        assert(p&&p->refs==2);
        if(fail_move)throw std::bad_alloc{};
        ++moves;--p->refs; // guest closes the transferred reference in this harness
    }
};
namespace IPC {
struct ResponseBuilder {
    HLERequestContext& ctx;
    ResponseBuilder(HLERequestContext& c,unsigned words,unsigned copies=0,unsigned moves=0):ctx(c){
        assert(copies==0);ctx.words=words;ctx.reply.clear();ctx.response_moves=moves;
    }
    template<class T>void Push(T x){ctx.reply.push_back(u64(x));}
    template<class T,std::size_t N>void PushRaw(const std::array<T,N>& a){for(auto x:a)Push(x);}
};
}
namespace Service::AM {
namespace GP=GpuSessionProtocol;
struct EventContext {
    Kernel::KEvent item{};
    bool fail_oom{};unsigned calls{};
    Kernel::KEvent* CreateEvent(const char* name){
        assert(std::string{name}=="GpuNotification");++calls;
        if(fail_oom)throw std::bad_alloc{};return &item;
    }
};
struct SharedState {
    std::mutex mutex{};
    std::array<Kernel::KEvent*,GP::MaxNotificationEvents> events{};
    GP::AddressSpaceSlots address_spaces{};
    EventContext event_context{};
};
struct IGpuSession {
    std::shared_ptr<SharedState> m_shared=std::make_shared<SharedState>();
    int kernel{};
    void GetNotificationEvent(HLERequestContext&);
    void GetUserPartition(HLERequestContext&);
    void GetGsvPartition(HLERequestContext&);
    void GetVaRange(HLERequestContext&);
};
__REAL_EVENT__
__REAL_PARTITION__
}
int main(){
    using Service::AM::IGpuSession;
    using Service::Nvidia::Devices::NativeNs2GpuVaStart;
    using Service::Nvidia::Devices::NativeNs2GpuVaSmallSplit;
    IGpuSession s;
    auto& ctx=s.m_shared->event_context;
    HLERequestContext bad{{0x1c,1,64}};
    s.GetNotificationEvent(bad);
    assert(bad.words==2&&bad.reply[0]==Kernel::ResultInvalidCombination.raw&&ctx.calls==0);
    HLERequestContext req{{0x1c,1,3}};
    ctx.fail_oom=true;s.GetNotificationEvent(req);
    assert(req.words==2&&req.reply[0]==Kernel::ResultOutOfResource.raw&&!s.m_shared->events[3]);
    ctx.fail_oom=false;ctx.item.readable.fail_open=true;s.GetNotificationEvent(req);
    assert(req.reply[0]==Kernel::ResultInvalidState.raw&&ctx.item.readable.refs==1&&req.response_moves==0);
    ctx.item.readable.fail_open=false;req.fail_move=true;s.GetNotificationEvent(req);
    assert(req.reply[0]==Kernel::ResultOutOfResource.raw&&ctx.item.readable.refs==1&&req.response_moves==0);
    req.fail_move=false;s.GetNotificationEvent(req);
    assert(req.reply[0]==0&&req.response_moves==1&&req.moves==1&&ctx.calls==2);
    s.GetNotificationEvent(req);
    assert(req.reply[0]==0&&req.moves==2&&ctx.calls==2&&ctx.item.readable.refs==1);
    auto& slots=s.m_shared->address_spaces;
    assert(slots.Add(9)==Service::AM::GP::Status::Success);
    assert(!slots.Registered(9)); // no NVDRV import required
    HLERequestContext range{{16+203,1,9}};
    s.GetVaRange(range);
    assert(range.words==20&&range.reply.size()==10&&range.reply[0]==0&&range.reply[1]==1);
    assert(range.reply[2]==0x08000000ULL&&range.reply[3]==0xbfffffffffULL);
    for(unsigned i=4;i<range.reply.size();++i)assert(range.reply[i]==0);
    HLERequestContext user{{16+201,1,9}};
    s.GetUserPartition(user);
    assert(user.words==6&&user.reply.size()==3&&user.reply[0]==0&&user.reply[1]==NativeNs2GpuVaStart);
    assert(user.reply[2]==NativeNs2GpuVaSmallSplit-NativeNs2GpuVaStart);
    HLERequestContext gsv{{16+202,1,9}};
    s.GetGsvPartition(gsv);
    assert(gsv.words==6&&gsv.reply[0]==0&&gsv.reply[1]==~u64{0}&&gsv.reply[2]==0);
    range.packet[2]=10;s.GetVaRange(range);
    assert(range.reply[0]==Kernel::ResultNotFound.raw);
    for(unsigned i=1;i<range.reply.size();++i)assert(range.reply[i]==0);
    range.packet={16+203,2,9};s.GetVaRange(range);
    assert(range.reply[0]==Kernel::ResultInvalidCombination.raw);
    for(unsigned i=1;i<range.reply.size();++i)assert(range.reply[i]==0);
}
""".replace("__REAL_EVENT__",event).replace("__REAL_PARTITION__",partition)
compilers=list(dict.fromkeys(x for x in (shutil.which("clang++"),shutil.which("g++")) if x))
assert compilers,"Host C++20 compiler unavailable"
with tempfile.TemporaryDirectory(prefix="eden-h06-ipc-resource-") as d:
    src=Path(d)/"owner.cpp";src.write_text(harness)
    for compiler in compilers:
        for opt in ("-O0","-O2"):
            exe=Path(d)/(Path(compiler).name+opt)
            argv=[compiler,"-std=c++20",opt,"-Wall","-Wextra","-Werror",
                  "-fsanitize=undefined","-fno-sanitize-recover=all",
                  "-I"+str(vendor/"encore-active/ns2-runtime/hle"),
                  "-I"+str(vendor/"encore-active/ns2-runtime/nvdrv_as"),
                  str(src),"-o",str(exe)]
            build=subprocess.run(argv,capture_output=True,text=True,timeout=60,
                                 env=os.environ.copy())
            assert build.returncode==0,build.stderr[-5000:]
            run=subprocess.run([str(exe)],capture_output=True,text=True,timeout=20)
            assert run.returncode==0,run.stderr[-5000:]
            print("H06_REAL_GPU_IPC_EVENT_PARTITION_OOM_PASS",Path(compiler).name,opt,
                  "move_event=1 oom_no_handle=1 move_rollback=1 pre_import_partition=1 malformed=refused",flush=True)
