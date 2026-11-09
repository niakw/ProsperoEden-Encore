#!/usr/bin/env python3
"""H06: execute real IGpuSession::RequestWorker TIPC admission and signal owner.

The original method is compiled under Clang/GCC/UBSan; kernel KSession
creation is independently tested by check_gpu_session_kernel_rollback_host.py.
This witness covers malformed event indices, missing events, handler OOM,
registration failure, success and repeated requests without extra handles.
"""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[2]
source=(ROOT/"vendor/encore-active/ns2-runtime/gpu_session/core/hle/service/am/service/gpu_session.cpp").read_text()
begin="void IGpuSession::RequestWorker("
end="void IGpuSession::AcquireWorker("
assert source.count(begin)==source.count(end)==1
owner=begin+source.split(begin,1)[1].split(end,1)[0]
for exact in ("GP::DecodeEventIndex(command, 0x25)", "CreateWorkerKernelSession(",
              "std::make_shared<IGpuWorker>", "m_shared->events[*index]->Signal(kernel)",
              "catch (const std::bad_alloc&)"):
    assert exact in owner,exact
harness=r"""
#include <array>
#include <cassert>
#include <cstdint>
#include <memory>
#include <mutex>
#include <new>
#include <vector>
#include "core/hle/service/am/service/gpu_session_protocol.h"
using u32=std::uint32_t;
struct Result {
    u32 raw{};
    constexpr bool IsSuccess() const noexcept {return raw==0;}
};
inline constexpr Result ResultSuccess{0};
namespace Kernel {
inline constexpr Result ResultInvalidCombination{1},
    ResultInvalidState{2}, ResultOutOfResource{3};
struct KernelCore {};
struct KProcess {};
struct KClientSession {};
struct KEvent {
    int signals{};
    void Signal(KernelCore&) {++signals;}
};
}
struct HLERequestContext {
    std::array<u32,3> packet{};
    std::vector<u32> reply{};
    unsigned words{};
    const u32* CommandBuffer() const {return packet.data();}
};
namespace IPC {
struct ResponseBuilder {
    HLERequestContext& ctx;
    ResponseBuilder(HLERequestContext& c,unsigned size):ctx{c} {
        c.words=size;c.reply.clear();
    }
    void Push(u32 code) {ctx.reply.push_back(code);}
};
}
namespace Core {struct System {};}
namespace Nvidia {struct Module {};}
namespace Service::AM {
namespace GP=GpuSessionProtocol;
struct GpuWorkerSharedState {
    std::mutex mutex{};
    std::array<Kernel::KEvent*,GP::MaxNotificationEvents> events{};
};
inline bool fail_handler{},fail_register{};
inline unsigned registrations{};
struct IGpuWorker {
    IGpuWorker(Core::System&,std::shared_ptr<Nvidia::Module>,
               Kernel::KProcess*,std::shared_ptr<GpuWorkerSharedState>) {
        if(fail_handler)throw std::bad_alloc{};
    }
};
static Result CreateWorkerKernelSession(Core::System&,HLERequestContext&,
                                        std::shared_ptr<IGpuWorker> worker,
                                        Kernel::KClientSession** out) {
    assert(worker);
    ++registrations;
    if(fail_register)return Kernel::ResultOutOfResource;
    static Kernel::KClientSession client;
    *out=&client;
    return ResultSuccess;
}
struct IGpuSession {
    Core::System system{};
    Kernel::KernelCore kernel{};
    Kernel::KProcess process{};
    Kernel::KProcess* m_process{&process};
    std::shared_ptr<Nvidia::Module> m_module=std::make_shared<Nvidia::Module>();
    std::shared_ptr<GpuWorkerSharedState> m_shared=
        std::make_shared<GpuWorkerSharedState>();
    std::mutex m_lock{};
    Kernel::KClientSession* m_worker{};
    void RequestWorker(HLERequestContext&);
};
__REAL_OWNER__
}
int main() {
    using Service::AM::IGpuSession;
    IGpuSession session;
    Kernel::KEvent event3{},event4{};
    HLERequestContext invalid{{0x25,1,64}};
    session.RequestWorker(invalid);
    assert(invalid.words==2 && invalid.reply.size()==1 &&
           invalid.reply[0]==Kernel::ResultInvalidCombination.raw);
    assert(Service::AM::registrations==0);

    HLERequestContext req{{0x25,1,3}};
    session.RequestWorker(req);
    assert(req.reply[0]==Kernel::ResultInvalidState.raw);
    assert(!session.m_worker && Service::AM::registrations==0);

    session.m_shared->events[3]=&event3;
    Service::AM::fail_handler=true;
    session.RequestWorker(req);
    assert(req.reply[0]==Kernel::ResultOutOfResource.raw);
    assert(!session.m_worker && event3.signals==0);
    Service::AM::fail_handler=false;

    Service::AM::fail_register=true;
    session.RequestWorker(req);
    assert(req.reply[0]==Kernel::ResultOutOfResource.raw);
    assert(!session.m_worker && event3.signals==0);
    assert(Service::AM::registrations==1);
    Service::AM::fail_register=false;

    session.RequestWorker(req);
    assert(req.reply[0]==0 && session.m_worker);
    assert(Service::AM::registrations==2 && event3.signals==1);
    session.RequestWorker(req);
    assert(req.reply[0]==0 && Service::AM::registrations==2);
    assert(event3.signals==2);

    session.m_shared->events[4]=&event4;
    HLERequestContext second{{0x25,1,4}};
    session.RequestWorker(second);
    assert(second.reply[0]==0 && event4.signals==1);
    assert(Service::AM::registrations==2);
    HLERequestContext wrong{{0x26,1,3}};
    session.RequestWorker(wrong);
    assert(wrong.reply[0]==Kernel::ResultInvalidCombination.raw);
    assert(Service::AM::registrations==2 && event3.signals==2);
}
""".replace("__REAL_OWNER__",owner)
compilers=list(dict.fromkeys(x for x in (shutil.which("clang++"),shutil.which("g++")) if x))
assert compilers,"Host C++20 compiler required"
with tempfile.TemporaryDirectory(prefix="eden-h06-request-worker-") as temp:
    cpp=Path(temp)/"owner.cpp";cpp.write_text(harness)
    for cc in compilers:
        for opt in ("-O0","-O2"):
            exe=Path(temp)/(Path(cc).name+opt)
            args=[cc,"-std=c++20",opt,"-Wall","-Wextra","-Werror",
                  "-fsanitize=undefined","-fno-sanitize-recover=all",
                  "-I"+str(ROOT/"vendor/encore-active/ns2-runtime/hle"),
                  str(cpp),"-o",str(exe)]
            built=subprocess.run(args,capture_output=True,text=True,timeout=50,env=os.environ.copy())
            assert built.returncode==0,built.stderr[-4500:]
            run=subprocess.run([str(exe)],capture_output=True,text=True,timeout=20)
            assert run.returncode==0,run.stderr[-4500:]
            print("H06_GPU_WORKER_REQUEST_REAL_OWNER_PASS",Path(cc).name,opt,
                  "invalid=refused missing=refused oom=rolled_back success=signal_once",flush=True)
