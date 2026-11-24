#!/usr/bin/env python3
"""Execute actual GSV VM allocation/registration and NVDRV AS_IMPORT methods.
The real process registry and slot protocol are compiled with controlled
NVDRV allocation/binding seams; actual GMMU and console are not simulated."""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[2]
VENDOR=ROOT/"vendor"
source=(VENDOR/"encore-active/ns2-runtime/gpu_session/core/hle/service/am/service/gpu_session.cpp").read_text()
as_source=(VENDOR/"encore-active/ns2-runtime/nvdrv_as/core/hle/service/nvdrv/devices/nvhost_as_gpu.cpp").read_text()
def function(src, begin):
    assert src.count(begin)==1,begin
    return begin+src.split(begin,1)[1].split("\n}",1)[0]+"\n}"
owner=function(source,"void IGpuSession::CreateAddressSpace(")
register=function(source,"Result IGpuSession::RegisterAddressSpace(")
translate=function(source,"static Result Translate(GP::Status status) {")
import_vm=function(as_source,"NvResult nvhost_as_gpu::ImportNativeVm(")
assert "AllocateVm(" in owner and "address_spaces.Add(*candidate)" in owner
assert 'm_module->Open(' not in owner and 'm_module->Ioctl1(' not in owner
assert "RegisterVm(m_process, id)" in register
assert import_vm.index("FindRegisteredVmOwner(")<import_vm.index("AllocAsEx(layout)")<import_vm.index("BindImportedAddressSpace(")
fixture=r"""
#include <array>
#include <cassert>
#include <cstdint>
#include <memory>
#include <mutex>
#include <optional>
#include <vector>
#include "core/hle/service/am/service/gpu_session_protocol.h"
#include "core/hle/service/nvdrv/devices/native_gpu_process_registry.h"
using u32=std::uint32_t;
using u64=std::uint64_t;
struct Result {
    u32 raw{};
    constexpr bool IsSuccess() const noexcept {return raw==0;}
    constexpr bool IsError() const noexcept {return raw!=0;}
};
inline constexpr Result ResultSuccess{0};
namespace Kernel {
class KProcess {public: int pid{};};
inline constexpr Result ResultInvalidCombination{1},ResultInvalidState{2},
    ResultOutOfResource{3},ResultNotFound{4},ResultNotImplemented{5};
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
namespace Service::Nvidia {
enum class NvResult {Success,InvalidState,BadParameter,InsufficientMemory};
namespace Devices {
inline constexpr u64 NativeNs2GpuVaStart=0x08000000ULL;
inline constexpr u64 NativeNs2GpuVaSmallSplit=0xc000000000ULL;
inline constexpr u64 NativeNs2GpuVaEnd=0x10000000000ULL;
struct nvhost_as_gpu : std::enable_shared_from_this<nvhost_as_gpu> {
    struct NativeVmImport {u32 version{},vm_id{};u64 reserved{},user_first{},user_end{},reserved2{};};
    struct IoctlAllocAsEx {u32 big_page_size{};u64 va_range_start{},va_range_end{},va_range_split{};};
    Kernel::KProcess* m_native_process{};
    u32 m_native_vm_id{};
    struct VM {bool initialised{};} vm;
    std::unique_ptr<int> gmmu;
    bool fail_alloc{};
    unsigned allocations{},resets{};
    NvResult AllocAsEx(IoctlAllocAsEx& p) {
        ++allocations;
        assert(p.big_page_size==0x20000 && p.va_range_start==NativeNs2GpuVaStart &&
               p.va_range_split==NativeNs2GpuVaSmallSplit && p.va_range_end==NativeNs2GpuVaEnd);
        if(fail_alloc)return NvResult::InsufficientMemory;
        gmmu=std::make_unique<int>(1);vm.initialised=true;return NvResult::Success;
    }
    bool ResetFailedNativeVmImport(){++resets;gmmu.reset();vm={};return true;}
    NvResult ImportNativeVm(const NativeVmImport&);
};
}
}
namespace Service::AM {
namespace GP=GpuSessionProtocol;
struct GpuWorkerSharedState {
    std::mutex mutex{};
    GP::AddressSpaceSlots address_spaces{};
    bool fail_bind{};
    unsigned binds{};
    Nvidia::NvResult BindImportedAddressSpace(u32 id,const std::shared_ptr<Nvidia::Devices::nvhost_as_gpu>& as) {
        ++binds;assert(as && as->gmmu && address_spaces.Registered(id));
        return fail_bind?Nvidia::NvResult::InsufficientMemory:Nvidia::NvResult::Success;
    }
};
struct IGpuSession {
    std::shared_ptr<GpuWorkerSharedState> m_shared=std::make_shared<GpuWorkerSharedState>();
    Kernel::KProcess* m_process{};
    void CreateAddressSpace(HLERequestContext&);
    Result RegisterAddressSpace(u32);
};
__TRANSLATE__
__OWNER__
__REGISTER__
}
namespace Service::Nvidia::Devices {
__IMPORT__
}
using Registry=Service::Nvidia::Devices::NativeGpuProcessRegistry;
using Device=Service::Nvidia::Devices::nvhost_as_gpu;
using NvResult=Service::Nvidia::NvResult;
struct Fixture {
    Kernel::KProcess process{7};
    Service::AM::IGpuSession session{};
    Fixture(){session.m_process=&process;assert(Registry::Instance().Register(&process));}
    ~Fixture(){Registry::Instance().Unregister(&process);}
    HLERequestContext Create(u32 reserved=0){
        HLERequestContext req{{0x31,1,reserved}};
        session.CreateAddressSpace(req);
        assert(req.words==3 && req.reply.size()==2);
        return req;
    }
};
int main(){
    using namespace Service::Nvidia::Devices;
    auto& registry=Registry::Instance();
    Fixture f,foreign;
    auto bad=f.Create(1);
    assert(bad.reply[0]==Kernel::ResultInvalidCombination.raw && bad.reply[1]==0);
    auto r=f.Create();
    assert(r.reply[0]==0 && r.reply[1]>0);
    const u32 id=static_cast<u32>(r.reply[1]);
    assert(f.session.m_shared->address_spaces.Owns(id));
    assert(!registry.FindRegisteredVmOwner(&f.process,id));
    auto as=std::make_shared<Device>();
    as->m_native_process=&f.process;
    Device::NativeVmImport p{5,id,0,NativeNs2GpuVaStart,NativeNs2GpuVaSmallSplit,0};
    assert(as->ImportNativeVm(p)==NvResult::InvalidState && as->allocations==0);
    assert(foreign.session.RegisterAddressSpace(id).raw==Kernel::ResultNotFound.raw);
    assert(f.session.RegisterAddressSpace(id).IsSuccess());
    assert(registry.FindRegisteredVmOwner(&f.process,id)==f.session.m_shared);
    assert(!registry.FindRegisteredVmOwner(&foreign.process,id));
    auto other=std::make_shared<Device>();other->m_native_process=&foreign.process;
    assert(other->ImportNativeVm(p)==NvResult::InvalidState && other->allocations==0);
    auto malformed=p;malformed.version=4;
    assert(as->ImportNativeVm(malformed)==NvResult::BadParameter);
    malformed=p;malformed.user_end--;
    assert(as->ImportNativeVm(malformed)==NvResult::BadParameter);
    as->fail_alloc=true;
    assert(as->ImportNativeVm(p)==NvResult::InsufficientMemory && !as->gmmu && !as->m_native_vm_id);
    as->fail_alloc=false;f.session.m_shared->fail_bind=true;
    assert(as->ImportNativeVm(p)==NvResult::InsufficientMemory && as->resets==1 && !as->gmmu && !as->m_native_vm_id);
    f.session.m_shared->fail_bind=false;
    assert(as->ImportNativeVm(p)==NvResult::Success && as->gmmu && as->m_native_vm_id==id);
    assert(as->ImportNativeVm(p)==NvResult::InvalidState);
    const auto next=foreign.Create();
    assert(next.reply[0]==0 && next.reply[1]!=id);
    for(unsigned i=1;i<Service::AM::GP::MaxAddressSpaces;++i)assert(f.Create().reply[0]==0);
    assert(f.Create().reply[0]==Kernel::ResultOutOfResource.raw);
    assert(f.session.m_shared->address_spaces.Count()==Service::AM::GP::MaxAddressSpaces);
    assert(!registry.RemoveVm(&f.process,id,foreign.session.m_shared.get()));
    assert(registry.RemoveVm(&f.process,id,f.session.m_shared.get()));
    assert(!registry.FindRegisteredVmOwner(&f.process,id));
}
""".replace("__TRANSLATE__",translate).replace("__OWNER__",owner).replace("__REGISTER__",register).replace("__IMPORT__",import_vm)
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
                  "vm_opaque=1 register=1 foreign=refused exhaustion=1 import_oom=1 bind_rollback=1",flush=True)
