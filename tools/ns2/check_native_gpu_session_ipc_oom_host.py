#!/usr/bin/env python3
"""H06: execute the maintained GPU session's event and VA partition IPC owners.

Clang/GCC UBSan, both optimization levels, inject real C++ bad_alloc at
notification creation and NVDRV partition IOCTL. Require exact result words,
COPY rights, zeroed rejected partition and reuse of existing event. This is
a scoped IPC/handle witness, not a claim that every H06 command is complete.
"""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[2]
vendor=ROOT/"vendor"
owner_path=vendor/"encore-active/ns2-runtime/gpu_session/core/hle/service/am/service/gpu_session.cpp"
owner=owner_path.read_text()
def extract(begin, end):
    assert owner.count(begin)==owner.count(end)==1,(begin,end)
    return begin+owner.split(begin,1)[1].split(end,1)[0]
event=extract("void IGpuSession::GetNotificationEvent(", "std::shared_ptr<Nvidia::Devices::nvhost_as_gpu>\nIGpuSession::ResolveOpenedAddressSpace(")
partition=extract("void IGpuSession::GetAddressSpacePartition(", "void IGpuSession::CreateGraphicsDevice(")
assert 'catch (const std::bad_alloc&)' in event
assert "ctx.AddCopyObject(readable);" in event
assert event.index("ctx.AddCopyObject(readable);") < event.index("IPC::ResponseBuilder rb{ctx, 2, 1, 0};")
assert "IPC::ResponseBuilder rb{ctx, 2};" in event
assert "ioctl_oom = true;" in partition
assert "result = Kernel::ResultOutOfResource;" in partition
assert "if (ioctl_oom)" in partition and "result = Kernel::ResultInvalidState;" in partition
assert "GP::AddressSpaceRegionEnd(" in partition

harness=r"""
#include <array>
#include <cassert>
#include <cstdint>
#include <cstring>
#include <memory>
#include <mutex>
#include <new>
#include <span>
#include <string>
#include <vector>
#include "core/hle/service/am/service/gpu_session_protocol.h"

using u8=std::uint8_t;
using u32=std::uint32_t;
using u64=std::uint64_t;
using u32_le=u32;
struct Result {
    u32 raw{};
    constexpr bool IsSuccess() const noexcept { return raw==0; }
};
inline constexpr Result ResultSuccess{0};
namespace Kernel {
inline constexpr Result ResultInvalidCombination{1}, ResultNotFound{2},
    ResultOutOfResource{3}, ResultInvalidState{4};
struct KReadableEvent { int id{17}; };
struct KEvent {
    KReadableEvent readable{};
    KReadableEvent& GetReadableEvent() { return readable; }
};
}
struct HLERequestContext {
    std::array<u32,3> packet{};
    u32 command{};
    std::vector<u64> reply{};
    unsigned words{},copy_count{},move_count{},response_copies{};
    bool fail_copy{};
    const u32* CommandBuffer() const { return packet.data(); }
    void AddCopyObject(Kernel::KReadableEvent* readable) {
        assert(readable && readable->id==17);
        if (fail_copy) throw std::bad_alloc{};
        ++copy_count;
    }
    u32 GetCommand() const { return command; }
};
namespace IPC {
struct ResponseBuilder {
    HLERequestContext& ctx;
    explicit ResponseBuilder(HLERequestContext& c,unsigned words,unsigned copies=0,
                             unsigned moves=0):ctx(c) {
        ctx.words=words;
        ctx.reply.clear();
        ctx.move_count=0;
        ctx.response_copies=copies;
        assert(copies<=1 && moves==0);
    }
    template<typename T> void Push(T value) { ctx.reply.push_back(u64(value)); }
};
}
namespace Nvidia {
using DeviceFD=int;
struct Ioctl { u32 raw{}; };
enum class NvResult { Success, InvalidState };
namespace Devices {
struct nvhost_as_gpu {
    struct VaRegion {
        u64 offset{};
        u32 page_size{};
        u32 reserved{};
        u64 pages{};
    };
};
}
struct Module {
    bool fail_oom{}, fail_ioctl{};
    int malformed_mode{}; // injected NVDRV protocol replies, not synthetic owners
    unsigned calls{};
    NvResult Ioctl1(DeviceFD fd,Ioctl command,std::span<const u8> input,
                    std::span<u8> output) {
        ++calls;
        assert(fd==9 && command.raw==0xc0404108U);
        assert(input.size()==64 && output.size()==64);
        if(fail_oom)throw std::bad_alloc{};
        if(fail_ioctl)return NvResult::InvalidState;
        std::array<Devices::nvhost_as_gpu::VaRegion,2> regions{{
            {0x10000,4096,0,2},{0x20000,4096,0,2}
        }};
        if(malformed_mode==1) regions[0].pages=0; // missing first extent
        if(malformed_mode==2) {regions[0].offset=~u64{0}-3;regions[0].pages=2;} // overflow
        if(malformed_mode==3) regions[0].offset=0x30000; // reversed bounds
        if(malformed_mode==4) regions[0].pages=256; // first extent beyond second
        if(malformed_mode==5) {regions[0].offset=0x1f000;regions[0].pages=2;} // overlaps second region
        if(malformed_mode==6) regions[1].pages=0; // missing second extent
        if(malformed_mode==7) {regions[1].offset=~u64{0}-3;regions[1].pages=2;} // second overflow
        std::memcpy(output.data()+16,regions.data(),sizeof(regions));
        return NvResult::Success;
    }
};
}
namespace Service::AM {
namespace GP=GpuSessionProtocol;
struct EventContext {
    Kernel::KEvent item{};
    bool fail_oom{};
    unsigned calls{};
    Kernel::KEvent* CreateEvent(const char* name) {
        assert(std::string{name}=="GpuNotification");
        ++calls;
        if(fail_oom)throw std::bad_alloc{};
        return &item;
    }
};
struct SharedState {
    std::mutex mutex{};
    std::array<Kernel::KEvent*,GP::MaxNotificationEvents> events{};
    GP::AddressSpaceSlots address_spaces{};
    EventContext event_context{};
    bool opened{true};
};
struct IGpuSession {
    std::shared_ptr<SharedState> m_shared{std::make_shared<SharedState>()};
    std::shared_ptr<Nvidia::Module> m_module{std::make_shared<Nvidia::Module>()};
    bool ResolveOpenedAddressSpace(u32 id) {
        return id==9 && m_shared->opened;
    }
    void GetNotificationEvent(HLERequestContext&);
    void GetAddressSpacePartition(HLERequestContext&);
};
__REAL_EVENT__
__REAL_PARTITION__
}
static HLERequestContext cmd(u32 command,u32 index) {
    return HLERequestContext{{16+command,1,index},command};
}
int main(){
    using Service::AM::IGpuSession;
    IGpuSession s;
    {
        HLERequestContext bad{{0x1c,1,64},12};
        s.GetNotificationEvent(bad);
        assert(bad.reply.size()==1 && bad.reply[0]==Kernel::ResultInvalidCombination.raw);
        assert(bad.words==2 && bad.copy_count==0);
        assert(s.m_shared->event_context.calls==0);
    }
    {
        auto& context=s.m_shared->event_context;
        context.fail_oom=true;
        HLERequestContext req{{0x1c,1,3},12};
        s.GetNotificationEvent(req);
        assert(req.words==2 && req.reply.size()==1);
        assert(req.reply[0]==Kernel::ResultOutOfResource.raw);
        assert(req.copy_count==0 && s.m_shared->events[3]==nullptr);
        context.fail_oom=false;
        req.fail_copy=true;
        s.GetNotificationEvent(req);
        assert(req.reply.size()==1 &&
               req.reply[0]==Kernel::ResultOutOfResource.raw);
        assert(req.copy_count==0 && req.response_copies==0);
        assert(s.m_shared->events[3]==&context.item && context.calls==2);
        req.fail_copy=false;
        s.GetNotificationEvent(req);
        assert(req.reply.size()==1 && req.reply[0]==0 && req.copy_count==1);
        assert(req.response_copies==1 && context.calls==2);
        req.copy_count=0;
        s.GetNotificationEvent(req);
        assert(req.reply[0]==0 && req.copy_count==1 &&
               req.response_copies==1 && context.calls==2);
    }
    auto& slots=s.m_shared->address_spaces;
    assert(slots.Add(9)==Service::AM::GP::Status::Success);
    {
        auto req=cmd(203,10);
        s.GetAddressSpacePartition(req);
        assert(req.reply.size()==10 && req.words==20);
        assert(req.reply[0]==Kernel::ResultNotFound.raw);
        for(u64 value:req.reply) if(value!=req.reply[0])assert(value==0);
        assert(s.m_module->calls==0);
    }
    {
        s.m_shared->opened=false;
        auto req=cmd(203,9);
        s.GetAddressSpacePartition(req);
        assert(req.reply[0]==Kernel::ResultInvalidState.raw);
        assert(s.m_module->calls==0);
        s.m_shared->opened=true;
    }
    {
        s.m_module->fail_oom=true;
        auto req=cmd(203,9);
        s.GetAddressSpacePartition(req);
        assert(req.words==20 && req.reply.size()==10);
        assert(req.reply[0]==Kernel::ResultOutOfResource.raw);
        for(std::size_t i=1;i<req.reply.size();++i)assert(req.reply[i]==0);
        s.m_module->fail_oom=false;
    }
    {
        s.m_module->fail_ioctl=true;
        auto req=cmd(203,9);
        s.GetAddressSpacePartition(req);
        assert(req.reply[0]==Kernel::ResultInvalidState.raw);
        for(std::size_t i=1;i<req.reply.size();++i)assert(req.reply[i]==0);
        s.m_module->fail_ioctl=false;
    }
    // Reject malformed NVDRV region metadata before publishing ANY guest VA.
    for (int mode=1; mode<=7; ++mode) {
        s.m_module->malformed_mode=mode;
        auto req=cmd(203,9);
        s.GetAddressSpacePartition(req);
        assert(req.words==20 && req.reply.size()==10);
        assert(req.reply[0]==Kernel::ResultInvalidState.raw);
        for(std::size_t i=1;i<req.reply.size();++i)assert(req.reply[i]==0);
    }
    s.m_module->malformed_mode=0;
    {
        auto req=cmd(203,9);
        s.GetAddressSpacePartition(req);
        assert(req.reply.size()==10 && req.words==20);
        assert(req.reply[0]==0 && req.reply[1]==1);
        assert(req.reply[2]==0x10000 && req.reply[3]==0x21fff);
        for(unsigned i=4;i<req.reply.size();++i)assert(req.reply[i]==0);
    }
    {
        auto req=cmd(202,9);
        s.GetAddressSpacePartition(req);
        assert(req.reply.size()==3 && req.words==6);
        assert(req.reply[0]==0 && req.reply[1]==~u64{0});
    }
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
                  str(src),"-o",str(exe)]
            build=subprocess.run(argv,capture_output=True,text=True,timeout=60,
                                 env=os.environ.copy())
            assert build.returncode==0,build.stderr[-5000:]
            run=subprocess.run([str(exe)],capture_output=True,text=True,timeout=20)
            assert run.returncode==0,run.stderr[-5000:]
            print("H06_REAL_GPU_IPC_EVENT_PARTITION_OOM_PASS",Path(compiler).name,opt,
                  "copy_event=1 oom_no_handle=1 partition_oom=1"
                  " stale_owner=refused valid_partition=1",flush=True)
