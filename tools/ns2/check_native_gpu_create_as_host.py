#!/usr/bin/env python3
"""H06: execute the production CreateAddressSpace GPU TIPC owner transaction.

Real method compiled with Clang/GCC and UBSan. Exercise valid NVDRV VA
allocation and malformed input, session/device/IOCTL OOM, bad device process,
duplicate FD and capacity exhaustion. No guest console or PS5 build.
"""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[2]
VENDOR=ROOT/"vendor"
source=(VENDOR/"encore-active/ns2-runtime/gpu_session/core/hle/service/am/service/gpu_session.cpp").read_text()
start="void IGpuSession::CreateAddressSpace("
end="void IGpuSession::GetAddressSpacePartition("
assert source.count(start)==source.count(end)==1
owner=start+source.split(start,1)[1].split(end,1)[0]
translate_start="static Result Translate(GP::Status status) {"
translate_end="// Actual worker KSession"
assert source.count(translate_start)==source.count(translate_end)==1
translate=translate_start+source.split(translate_start,1)[1].split(translate_end,1)[0]
for required in ("GP::IsCreateAddressSpace(command)", "OpenSession(m_process).id",
                 "m_module->Open(\"/dev/nvhost-as-gpu\"", "ioctl.raw = 0x40284109",
                 "m_module->Ioctl1(fd, ioctl, input, output)",
                 "as->OwnsNativeProcess(m_process)", "opened_gpu_as.try_emplace",
                 "address_spaces.Add(candidate)", "m_module->Close(fd)",
                 "catch (const std::bad_alloc&)"):
    assert required in owner, required
fixture=r"""
#include <array>
#include <cassert>
#include <cstdint>
#include <cstring>
#include <limits>
#include <map>
#include <memory>
#include <mutex>
#include <new>
#include <optional>
#include <string_view>
#include <vector>
#include "core/hle/service/am/service/gpu_session_protocol.h"
using u8=std::uint8_t;
using u32=std::uint32_t;
using u64=std::uint64_t;
using u32_le=u32;
using u64_le=u64;
struct Result {
    u32 raw{};
    constexpr bool IsSuccess() const noexcept {return raw==0;}
    constexpr bool IsError() const noexcept {return raw!=0;}
};
inline constexpr Result ResultSuccess{0};
namespace Kernel {
struct KProcess {int pid{};};
inline constexpr Result ResultInvalidCombination{1},ResultInvalidState{2},
    ResultOutOfResource{3}, ResultNotFound{4}, ResultNotImplemented{5};
}
struct HLERequestContext {
    std::array<u32,3> packet{};
    unsigned words{};
    std::vector<u64> reply{};
    const u32* CommandBuffer() const {return packet.data();}
};
namespace IPC {
struct ResponseBuilder {
    HLERequestContext& ctx;
    ResponseBuilder(HLERequestContext& c,unsigned count):ctx(c) {
        ctx.words=count;ctx.reply.clear();
    }
    template<class T> void Push(T value) {ctx.reply.push_back(u64(value));}
};
}
namespace Nvidia {
using DeviceFD=int;
inline constexpr DeviceFD INVALID_NVDRV_FD=-1;
struct Ioctl {u32 raw{};};
enum class NvResult {Success,InvalidState};
namespace NvCore {struct SessionId {std::size_t id{};};}
namespace Devices {
inline constexpr u64 NativeNs2GpuVaStart=0x100000000ULL;
inline constexpr u64 NativeNs2GpuVaEnd=0x200000000ULL;
inline constexpr u64 NativeNs2GpuVaSmallSplit=0x180000000ULL;
struct nvhost_as_gpu {
    Kernel::KProcess* owner{};
    bool OwnsNativeProcess(Kernel::KProcess* candidate) const {return owner==candidate;}
};
}
struct Container {
    bool throw_oom{};
    unsigned opens{};
    NvCore::SessionId OpenSession(Kernel::KProcess* process) {
        assert(process);
        ++opens;
        if(throw_oom)throw std::bad_alloc{};
        return {1};
    }
};
struct Module {
    Container container{};
    std::shared_ptr<Devices::nvhost_as_gpu> device=
        std::make_shared<Devices::nvhost_as_gpu>();
    bool throw_open{},throw_ioctl{},invalid_ioctl{},missing_device{};
    DeviceFD fd{17};
    unsigned device_opens{},ioctls{},closes{};
    Container& GetContainer() {return container;}
    DeviceFD Open(const char* name,NvCore::SessionId session) {
        assert(std::string_view{name}=="/dev/nvhost-as-gpu" && session.id==1);
        ++device_opens;
        if(throw_open)throw std::bad_alloc{};
        return fd;
    }
    NvResult Ioctl1(DeviceFD f,Ioctl command,const std::array<u8,40>& input,
                    std::array<u8,40>& output) {
        (void)output;
        assert(f==17 && command.raw==0x40284109);
        assert(input.size()==40);
        u32 page_size{};
        std::memcpy(&page_size,input.data()+8,sizeof(page_size));
        assert(page_size==0x20000);
        ++ioctls;
        if(throw_ioctl)throw std::bad_alloc{};
        return invalid_ioctl ? NvResult::InvalidState : NvResult::Success;
    }
    template<class T> std::shared_ptr<T> GetDevice(DeviceFD f) {
        if(missing_device || f!=17)return {};
        return std::static_pointer_cast<T>(device);
    }
    void Close(DeviceFD f) {assert(f==17 || f==0);++closes;}
};
}
namespace Service::AM {
namespace GP=GpuSessionProtocol;
struct State {
    std::mutex mutex{};
    GP::AddressSpaceSlots address_spaces{};
    std::optional<std::size_t> nv_session{};
    std::map<u32,std::weak_ptr<Nvidia::Devices::nvhost_as_gpu>> opened_gpu_as{};
};
struct IGpuSession {
    std::shared_ptr<State> m_shared=std::make_shared<State>();
    std::shared_ptr<Nvidia::Module> m_module=std::make_shared<Nvidia::Module>();
    Kernel::KProcess* m_process{};
    void CreateAddressSpace(HLERequestContext&);
};
__TRANSLATE__
__OWNER__
}
struct Fixture {
    Kernel::KProcess process{7};
    Service::AM::IGpuSession session{};
    Fixture() {
        session.m_process=&process;
        session.m_module->device->owner=&process;
    }
    HLERequestContext Create(u32 reserved=0) {
        HLERequestContext req{{0x31,1,reserved}};
        session.CreateAddressSpace(req);
        assert(req.words==3 && req.reply.size()==2);
        return req;
    }
};
int main() {
    using Service::AM::GP::Status;
    {
        Fixture f;
        auto r=f.Create(1);
        assert(r.reply[0]==Kernel::ResultInvalidCombination.raw && r.reply[1]==0);
        assert(f.session.m_module->device_opens==0);
        r=f.Create();
        assert(r.reply[0]==0 && r.reply[1]==17);
        assert(f.session.m_shared->address_spaces.Owns(17));
        assert(f.session.m_shared->opened_gpu_as.at(17).lock()==
               f.session.m_module->device);
        assert(f.session.m_module->container.opens==1);
        assert(f.session.m_module->ioctls==1);
        assert(f.session.m_module->closes==0);
    }
    {
        Fixture f;
        f.session.m_module->container.throw_oom=true;
        auto r=f.Create();
        assert(r.reply[0]==Kernel::ResultOutOfResource.raw && r.reply[1]==0);
        assert(!f.session.m_shared->nv_session);
        assert(f.session.m_module->device_opens==0);
        assert(f.session.m_shared->address_spaces.Count()==0);
    }
    {
        Fixture f;
        f.session.m_module->throw_open=true;
        auto r=f.Create();
        assert(r.reply[0]==Kernel::ResultOutOfResource.raw && r.reply[1]==0);
        assert(f.session.m_shared->address_spaces.Count()==0);
        assert(f.session.m_module->closes==0);
    }
    {
        Fixture f;
        f.session.m_module->throw_ioctl=true;
        auto r=f.Create();
        assert(r.reply[0]==Kernel::ResultOutOfResource.raw && r.reply[1]==0);
        assert(f.session.m_shared->address_spaces.Count()==0);
        assert(f.session.m_module->closes==1);
    }
    {
        Fixture f;
        f.session.m_module->invalid_ioctl=true;
        auto r=f.Create();
        assert(r.reply[0]==Kernel::ResultInvalidState.raw && r.reply[1]==0);
        assert(f.session.m_shared->address_spaces.Count()==0);
        assert(f.session.m_module->closes==1);
    }
    {
        Fixture f;
        Kernel::KProcess foreign{8};
        f.session.m_module->device->owner=&foreign;
        auto r=f.Create();
        assert(r.reply[0]==Kernel::ResultInvalidState.raw && r.reply[1]==0);
        assert(f.session.m_shared->address_spaces.Count()==0);
        assert(f.session.m_module->closes==1);
    }
    {
        Fixture f;
        f.session.m_module->missing_device=true;
        auto r=f.Create();
        assert(r.reply[0]==Kernel::ResultInvalidState.raw && r.reply[1]==0);
        assert(f.session.m_shared->address_spaces.Count()==0);
        assert(f.session.m_module->closes==1);
    }
    {
        Fixture f;
        assert(f.session.m_shared->address_spaces.Add(17)==Status::Success);
        auto r=f.Create();
        assert(r.reply[0]==Kernel::ResultInvalidState.raw && r.reply[1]==0);
        assert(f.session.m_shared->address_spaces.Count()==1);
        assert(f.session.m_shared->opened_gpu_as.empty());
        assert(f.session.m_module->closes==1);
    }
    {
        Fixture f;
        for(u32 id=1;id<=8;++id)
            assert(f.session.m_shared->address_spaces.Add(id)==Status::Success);
        auto r=f.Create();
        assert(r.reply[0]==Kernel::ResultOutOfResource.raw && r.reply[1]==0);
        assert(f.session.m_shared->address_spaces.Count()==8);
        assert(f.session.m_module->device_opens==0);
    }
}
""".replace("__TRANSLATE__",translate).replace("__OWNER__",owner)
compilers=list(dict.fromkeys(x for x in (shutil.which("clang++"),shutil.which("g++")) if x))
assert compilers,"Host C++20 compiler required"
with tempfile.TemporaryDirectory(prefix="eden-h06-as-owner-") as tmp:
    cpp=Path(tmp)/"owner.cpp";cpp.write_text(fixture)
    for cc in compilers:
        for opt in ("-O0","-O2"):
            exe=Path(tmp)/(Path(cc).name+opt)
            argv=[cc,"-std=c++20",opt,"-Wall","-Wextra","-Werror",
                  "-fsanitize=undefined","-fno-sanitize-recover=all",
                  "-I"+str(VENDOR/"encore-active/ns2-runtime/hle"),
                  str(cpp),"-o",str(exe)]
            built=subprocess.run(argv,capture_output=True,text=True,timeout=65,env=os.environ.copy())
            assert built.returncode==0,built.stderr[-6500:]
            done=subprocess.run([str(exe)],capture_output=True,text=True,timeout=25)
            assert done.returncode==0,done.stderr[-6500:]
            print("H06_CREATE_GPU_VA_REAL_OWNER_PASS",Path(cc).name,opt,
                  "valid=1 malformed=refused oom=3 foreign=refused fd=rolled_back",flush=True)
