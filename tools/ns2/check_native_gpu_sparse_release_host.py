#!/usr/bin/env python3
"""H06: execute real TIPC 215 sparse GPU VA release with OOM and retry.

Compiles maintained DestroySparseRegion method without rewriting the owner.
Fake NVDRV reports its documented pre-mutation InsufficientMemory state.
Verify no guest completion/event and no ledger loss; successful retry can
retire the exact region, whereas a pre-released dense GMMU is not freed twice.
"""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[2]
vendor=ROOT/"vendor"
owner=(vendor/"encore-active/ns2-runtime/gpu_session/core/hle/service/am/service/gpu_worker.cpp").read_text()
begin="void IGpuWorker::DestroySparseRegion("
end="void IGpuWorker::ExecuteSparseMapRequests("
assert owner.count(begin)==owner.count(end)==1
method=begin+owner.split(begin,1)[1].split(end,1)[0]
translate_begin="Result TranslateMappingStatus("
translate_end="} // namespace\n\nvoid IGpuWorker::NormalMapGpuMemory4K("
assert owner.count(translate_begin)==owner.count(translate_end)==1
translate=translate_begin+owner.split(translate_begin,1)[1].split(translate_end,1)[0]
for required in ("as->ReleaseNativeSparse4K(", "Nvidia::NvResult::InsufficientMemory",
                 "result = Kernel::ResultOutOfResource;",
                 "m_mappings.RecordReleasedSparse(",
                 "m_shared->events[request->notification]->Signal(kernel)"):
    assert required in method,required

fixture=r"""
#include <algorithm>
#include <array>
#include <cassert>
#include <cstdint>
#include <map>
#include <memory>
#include <mutex>
#include <vector>
#include "core/hle/service/am/service/gpu_worker_protocol.h"
#include "core/hle/service/am/service/gpu_session_protocol.h"
using u32=std::uint32_t;
using u64=std::uint64_t;
struct Result {
    u32 raw{};
    constexpr bool IsSuccess() const {return raw==0;}
};
inline constexpr Result ResultSuccess{0};
namespace Kernel {
inline constexpr Result ResultInvalidCombination{1},ResultNotFound{2},
    ResultInvalidState{3},ResultOutOfResource{4};
struct KernelCore {};
struct KEvent {
    unsigned signals{};
    void Signal(KernelCore&) {++signals;}
};
}
namespace Service::Nvidia {
using DeviceFD=int;
enum class NvResult {Success,InvalidState,InsufficientMemory};
namespace Devices {
struct NativeAS {
    NvResult next{NvResult::Success};
    unsigned releases{};
    NvResult ReleaseNativeSparse4K(u64 address,u64 size) {
        assert(address==0x20000 && size==0x2000);
        ++releases;
        return next;
    }
};
}
}
struct HLERequestContext {
    std::array<u32,9> packet{};
    std::vector<u64> reply{};
    unsigned words{};
    u32 GetCommand() const {return 215;}
    const u32* CommandBuffer() const {return packet.data();}
};
namespace IPC {
struct ResponseBuilder {
    HLERequestContext& ctx;
    ResponseBuilder(HLERequestContext& c,unsigned count):ctx(c) {
        c.words=count;c.reply.clear();
    }
    template <class T> void Push(T v) {ctx.reply.push_back(u64(v));}
};
}
namespace Service::AM {
namespace GW=GpuWorkerProtocol;
inline void TraceNs2WorkerResult(unsigned,u32){}
struct GpuSystem {
    unsigned waits{};
    void WaitForIdle() {++waits;}
};
struct System {
    GpuSystem gpu{};
    GpuSystem& GPU() {return gpu;}
};
struct SharedState {
    std::mutex mutex{};
    GpuSessionProtocol::AddressSpaceSlots address_spaces{};
    std::array<Kernel::KEvent*,GW::MaxNotifications> events{};
    std::shared_ptr<Nvidia::Devices::NativeAS> as=
        std::make_shared<Nvidia::Devices::NativeAS>();
    std::shared_ptr<Nvidia::Devices::NativeAS> FindOwnedAddressSpace(Nvidia::DeviceFD id) {
        return address_spaces.Owns(static_cast<u32>(id)) ? as : nullptr;
    }
};
struct IGpuWorker {
    std::mutex m_mutex{};
    std::shared_ptr<SharedState> m_shared=std::make_shared<SharedState>();
    GW::MappingLedger m_mappings{};
    struct Dense {bool gmmu_released{};};
    std::map<std::pair<u32,u64>,Dense> m_dense_regions{};
    System system{};
    Kernel::KernelCore kernel{};
    unsigned dense_retires{};
    bool RetireGpuOnlyRegion(u32 as,u64 address) {
        ++dense_retires;
        m_dense_regions.erase({as,address});
        return true;
    }
    void DestroySparseRegion(HLERequestContext&);
};
__TRANSLATE__
__REAL_OWNER__
}
static HLERequestContext packet(u32 notification=3) {
    return {{0xe7,7,7,0x20000,0,0x21fff,0,0,notification}};
}
int main() {
    using Service::AM::IGpuWorker;
    using Service::AM::GW::LedgerStatus;
    IGpuWorker w;
    Kernel::KEvent e{};
    w.m_shared->events[3]=&e;
    assert(w.m_shared->address_spaces.Add(7)==Service::AM::GpuSessionProtocol::Status::Success);
    assert(w.m_mappings.RecordSparse(7,1,0x20000,0x2000)==LedgerStatus::Success);
    auto& as=*w.m_shared->as;
    as.next=Service::Nvidia::NvResult::InsufficientMemory;
    auto oom=packet();
    w.DestroySparseRegion(oom);
    assert(oom.words==2 && oom.reply.size()==1);
    assert(oom.reply[0]==Kernel::ResultOutOfResource.raw);
    assert(w.m_mappings.CanReleaseSparse(7,0x20000,0x2000)==LedgerStatus::Success);
    assert(as.releases==1 && e.signals==0 && w.system.gpu.waits==1);
    as.next=Service::Nvidia::NvResult::Success;
    auto retry=packet();
    w.DestroySparseRegion(retry);
    assert(retry.reply[0]==0 && as.releases==2 && e.signals==1);
    assert(w.m_mappings.Count()==0);
    auto replay=packet();
    w.DestroySparseRegion(replay);
    assert(replay.reply[0]==Kernel::ResultNotFound.raw && as.releases==2);
    assert(e.signals==1);

    // Retry of an already-released dense reservation retires physical
    // ownership without issuing a second destructive GMMU free.
    assert(w.m_mappings.RecordSparse(7,1,0x20000,0x2000)==LedgerStatus::Success);
    w.m_dense_regions.emplace(std::make_pair(7U,u64{0x20000}),IGpuWorker::Dense{true});
    auto dense=packet();
    w.DestroySparseRegion(dense);
    assert(dense.reply[0]==0 && w.dense_retires==1 && as.releases==2);
    assert(w.m_mappings.Count()==0 && e.signals==2);

    auto unknown=packet(4);
    w.DestroySparseRegion(unknown);
    assert(unknown.reply[0]==Kernel::ResultNotFound.raw && as.releases==2);
}
""".replace("__TRANSLATE__",translate).replace("__REAL_OWNER__",method)

compilers=list(dict.fromkeys(x for x in (shutil.which("clang++"),shutil.which("g++")) if x))
assert compilers,"Host Clang/GCC C++20 required"
with tempfile.TemporaryDirectory(prefix="eden-h06-sparse215-") as directory:
    cpp=Path(directory)/"owner.cpp";cpp.write_text(fixture)
    for cc in compilers:
        for opt in ("-O0","-O2"):
            exe=Path(directory)/(Path(cc).name+opt)
            command=[cc,"-std=c++20",opt,"-Wall","-Wextra","-Werror",
                     "-fsanitize=undefined","-fno-sanitize-recover=all",
                     "-I"+str(vendor/"encore-active/ns2-runtime/hle"),
                     "-I"+str(vendor/"encore-active/ns2-runtime/nvdrv"),
                     "-I"+str(vendor/"sources/eden/src"),
                     str(cpp),"-o",str(exe)]
            built=subprocess.run(command,capture_output=True,text=True,timeout=60,
                                 env=os.environ.copy())
            assert built.returncode==0,built.stderr[-5000:]
            done=subprocess.run([str(exe)],capture_output=True,text=True,timeout=20)
            assert done.returncode==0,done.stderr[-5000:]
            print("H06_REAL_SPARSE_215_OOM_RETRY_PASS",Path(cc).name,opt,
                  "oom=OutOfResource ledger=retained retry=success dense=no_double_free",
                  flush=True)
