#!/usr/bin/env python3
"""H06: real 211/212/213 GPU worker TIPC transaction owner under host UBSan.

Compiles the maintained IPC handlers unmodified with the real worker
MappingLedger, GPU-session slots and packet decoders. NVDRV returns injected
success, OOM and non-retryable errors; verify that event signals, selected
kind, GMMU mutations and guest TIPC response never disagree.
"""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[2]
vendor=ROOT/"vendor"
owner=(vendor/"encore-active/ns2-runtime/gpu_session/core/hle/service/am/service/gpu_worker.cpp").read_text()
def extract(begin,end):
    assert owner.count(begin)==owner.count(end)==1,(begin,end)
    return begin+owner.split(begin,1)[1].split(end,1)[0]
translate=extract("Result TranslateMappingStatus(", "} // namespace\n\nvoid IGpuWorker::NormalMapGpuMemory4K(")
mapping=extract("void IGpuWorker::NormalMapGpuMemory4K(", "void IGpuWorker::NormalModifyGpuMemory4K(")
modify=extract("void IGpuWorker::NormalModifyGpuMemory4K(", "void IGpuWorker::NormalUnmapGpuMemory4K(")
unmap=extract("void IGpuWorker::NormalUnmapGpuMemory4K(", "void IGpuWorker::CreateSparseRegion(")
assert mapping.index("m_mappings.PrepareMapped") < mapping.index("as->MapNative4K") < mapping.index("CommitPrepared")
assert "mapped == Nvidia::NvResult::InsufficientMemory" in mapping
assert modify.index("system.GPU().WaitForIdle()") < modify.index("as->ModifyNativeKind")
assert unmap.index("system.GPU().WaitForIdle()") < unmap.index("as->UnmapNative4K")
assert "m_mappings.RecordUnmapped(*request);" in unmap

fixture=r"""
#include <algorithm>
#include <array>
#include <cassert>
#include <cstdint>
#include <map>
#include <memory>
#include <mutex>
#include <optional>
#include <vector>
#include "core/hle/service/am/service/gpu_worker_protocol.h"
#include "core/hle/service/am/service/gpu_session_protocol.h"
using u32=std::uint32_t;
using u64=std::uint64_t;
struct Result {
    u32 raw{};
    constexpr bool IsSuccess() const noexcept {return raw==0;}
};
inline constexpr Result ResultSuccess{0};
namespace Kernel {
inline constexpr Result ResultInvalidCombination{1}, ResultInvalidState{2},
    ResultNotFound{3}, ResultOutOfResource{4};
struct KernelCore {};
struct KEvent {
    unsigned signals{};
    void Signal(KernelCore&) {++signals;}
};
}
namespace Service::Nvidia {
using DeviceFD=int;
enum class NvResult {Success,InvalidState,InsufficientMemory};
struct NvMapHandle {u64 orig_size{0x4000};};
struct NvMapFile {
    std::shared_ptr<NvMapHandle> handle=std::make_shared<NvMapHandle>();
    std::shared_ptr<NvMapHandle> GetHandle(u32 id) {
        return id==27 ? handle : nullptr;
    }
};
struct Container {
    NvMapFile file{};
    NvMapFile& GetNvMapFile() {return file;}
};
struct Module {
    Container container{};
    Container& GetContainer() {return container;}
};
namespace Devices {
struct NativeAS {
    NvResult next_map{NvResult::Success};
    NvResult next_modify{NvResult::Success};
    NvResult next_unmap{NvResult::Success};
    unsigned map_calls{}, modify_calls{}, unmap_calls{};
    NvResult MapNative4K(u32 handle,u64 address,u64 offset,u64 size,std::uint8_t) {
        assert(handle==27 && address==0x20000 && offset==0 && size==0x2000);
        ++map_calls;
        return next_map;
    }
    NvResult ModifyNativeKind(u64 address,u64 size,std::uint8_t) {
        assert(address==0x20000 && size==0x2000);
        ++modify_calls;
        return next_modify;
    }
    NvResult UnmapNative4K(u64 address,u64 size) {
        assert(address==0x20000 && size==0x2000);
        ++unmap_calls;
        return next_unmap;
    }
};
}
}
struct HLERequestContext {
    std::array<u32,18> packet{};
    u32 command{};
    unsigned words{};
    std::vector<u64> reply{};
    const u32* CommandBuffer() const {return packet.data();}
    u32 GetCommand() const {return command;}
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
namespace Service::AM {
namespace GW=GpuWorkerProtocol;
inline void TraceNs2WorkerResult(unsigned,u32){}
struct FakeGPU {
    unsigned idle_waits{};
    void WaitForIdle() {++idle_waits;}
};
struct FakeSystem {
    FakeGPU gpu{};
    FakeGPU& GPU() {return gpu;}
};
struct SharedState {
    std::mutex mutex{};
    GpuSessionProtocol::AddressSpaceSlots address_spaces{};
    GpuSessionProtocol::DeviceSlots devices{};
    std::array<Kernel::KEvent*,GpuSessionProtocol::MaxNotificationEvents> events{};
    std::shared_ptr<Nvidia::Devices::NativeAS> owner=
        std::make_shared<Nvidia::Devices::NativeAS>();
    std::shared_ptr<Nvidia::Devices::NativeAS> FindOwnedAddressSpace(Nvidia::DeviceFD fd) {
        return address_spaces.Owns(u32(fd)) ? owner : nullptr;
    }
};
struct IGpuWorker {
    std::mutex m_mutex{};
    std::shared_ptr<SharedState> m_shared=std::make_shared<SharedState>();
    std::shared_ptr<Nvidia::Module> m_module=std::make_shared<Nvidia::Module>();
    std::vector<u32> m_memory{27};
    GW::MappingLedger m_mappings{};
    FakeSystem system{};
    Kernel::KernelCore kernel{};
    void NormalMapGpuMemory4K(HLERequestContext&);
    void NormalModifyGpuMemory4K(HLERequestContext&);
    void NormalUnmapGpuMemory4K(HLERequestContext&);
};
__TRANSLATE__
__MAP__
__MODIFY__
__UNMAP__
}
static HLERequestContext valid_map() {
    HLERequestContext c{};
    c.command=211;
    c.packet={0xe3,16,7,0x20000,0,0x21fff,0,27,
              0,0,0,0,0,0,0,1,0,3};
    return c;
}
static HLERequestContext valid_modify() {
    HLERequestContext c{};
    c.command=212;
    c.packet={0xe4,9,7,0x20000,0,0x21fff,0,0,0,0,3};
    return c;
}
static HLERequestContext valid_unmap() {
    HLERequestContext c{};
    c.command=213;
    c.packet={0xe5,7,7,0x20000,0,0x21fff,0,0,3};
    return c;
}
int main() {
    using Service::AM::IGpuWorker;
    using Service::AM::GpuSessionProtocol::Status;
    IGpuWorker w;
    Kernel::KEvent event{};
    auto& shared=*w.m_shared;
    auto& as=*shared.owner;
    assert(shared.address_spaces.Add(7)==Status::Success);
    const std::array<u32,8> device{0x39,6,1,0,0,0,2,0};
    assert(shared.devices.Create(device).status==Status::Success);
    // Missing event must reject with no device/GMMU mutation.
    auto missing=valid_map();
    w.NormalMapGpuMemory4K(missing);
    assert(missing.reply.size()==2 && missing.reply[0]==Kernel::ResultNotFound.raw);
    assert(as.map_calls==0 && w.m_mappings.Count()==0);
    shared.events[3]=&event;
    auto malformed=valid_map();
    malformed.packet[1]=17;
    w.NormalMapGpuMemory4K(malformed);
    assert(malformed.reply[0]==Kernel::ResultInvalidCombination.raw);
    assert(as.map_calls==0);
    // A real NVDRV allocation failure cannot claim a committed ledger entry.
    as.next_map=Service::Nvidia::NvResult::InsufficientMemory;
    auto oom=valid_map();
    w.NormalMapGpuMemory4K(oom);
    assert(oom.reply[0]==Kernel::ResultOutOfResource.raw && oom.reply[1]==0);
    assert(as.map_calls==1 && w.m_mappings.Count()==0 && event.signals==0);
    as.next_map=Service::Nvidia::NvResult::Success;
    auto first=valid_map();
    w.NormalMapGpuMemory4K(first);
    assert(first.words==3 && first.reply.size()==2 && first.reply[0]==0);
    assert(first.reply[1]==0 && as.map_calls==2 && event.signals==1);
    assert(w.m_mappings.Count()==1);
    auto overlap=valid_map();
    w.NormalMapGpuMemory4K(overlap);
    assert(overlap.reply[0]==Kernel::ResultInvalidState.raw);
    assert(as.map_calls==2 && w.m_mappings.Count()==1 && event.signals==1);

    as.next_modify=Service::Nvidia::NvResult::InvalidState;
    auto failed_modify=valid_modify();
    w.NormalModifyGpuMemory4K(failed_modify);
    assert(failed_modify.reply[0]==Kernel::ResultInvalidState.raw);
    assert(failed_modify.reply[1]==0 && as.modify_calls==1 && event.signals==1);
    as.next_modify=Service::Nvidia::NvResult::Success;
    auto good_modify=valid_modify();
    w.NormalModifyGpuMemory4K(good_modify);
    assert(good_modify.reply[0]==0 && event.signals==2);
    assert(as.modify_calls==2 && w.system.gpu.idle_waits==2);

    as.next_unmap=Service::Nvidia::NvResult::InvalidState;
    auto failed_unmap=valid_unmap();
    w.NormalUnmapGpuMemory4K(failed_unmap);
    assert(failed_unmap.words==4 && failed_unmap.reply[0]==Kernel::ResultInvalidState.raw);
    assert(failed_unmap.reply[1]==0 && w.m_mappings.Count()==1);
    assert(event.signals==2 && as.unmap_calls==1);
    as.next_unmap=Service::Nvidia::NvResult::Success;
    auto good_unmap=valid_unmap();
    w.NormalUnmapGpuMemory4K(good_unmap);
    assert(good_unmap.reply[0]==0 && good_unmap.reply[1]==0x2000);
    assert(w.m_mappings.Count()==0 && event.signals==3 && as.unmap_calls==2);
    auto repeated=valid_unmap();
    w.NormalUnmapGpuMemory4K(repeated);
    assert(repeated.reply[0]==Kernel::ResultNotFound.raw);
    assert(as.unmap_calls==2 && event.signals==3);
    assert(w.system.gpu.idle_waits==4);
}
""".replace("__TRANSLATE__",translate).replace("__MAP__",mapping)
   .replace("__MODIFY__",modify).replace("__UNMAP__",unmap)

compilers=list(dict.fromkeys(x for x in (shutil.which("clang++"),shutil.which("g++")) if x))
assert compilers,"Clang/GCC C++20 required"
with tempfile.TemporaryDirectory(prefix="eden-h06-worker211-213-") as directory:
    sourcefile=Path(directory)/"owner.cpp";sourcefile.write_text(fixture)
    for cc in compilers:
        for opt in ("-O0","-O2"):
            exe=Path(directory)/(Path(cc).name+opt)
            args=[cc,"-std=c++20",opt,"-Wall","-Wextra","-Werror",
                  "-fsanitize=undefined","-fno-sanitize-recover=all",
                  "-I"+str(vendor/"encore-active/ns2-runtime/hle"),
                  "-I"+str(vendor/"encore-active/ns2-runtime/nvdrv"),
                  "-I"+str(vendor/"sources/eden/src"),
                  str(sourcefile),"-o",str(exe)]
            built=subprocess.run(args,capture_output=True,text=True,timeout=65,
                                 env=os.environ.copy())
            assert built.returncode==0,built.stderr[-6000:]
            done=subprocess.run([str(exe)],capture_output=True,text=True,timeout=25)
            assert done.returncode==0,done.stderr[-6000:]
            print("H06_REAL_WORKER_211_212_213_PASS",Path(cc).name,opt,
                  "map_oom=rolled_back modify=ordered unmap=retryable signals=exact",
                  flush=True)
