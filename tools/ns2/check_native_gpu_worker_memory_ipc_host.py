#!/usr/bin/env python3
"""H06: execute production GPU worker TIPC 101/102 command decoding and reply.

Exercise actual CreateGpuAccessibleMemory/DestroyGpuAccessibleMemory owners
against the real native registration/release packet decoders. NVMap/process
memory operations are independently qualified by existing rollback witnesses;
this scope verifies command admission, error payloads and handle visibility.
"""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[2]
vendor=ROOT/"vendor"
owner=(vendor/"encore-active/ns2-runtime/gpu_session/core/hle/service/am/service/gpu_worker.cpp").read_text()
begin="void IGpuWorker::CreateGpuAccessibleMemory("
middle="void IGpuWorker::DestroyGpuAccessibleMemory("
end="} // namespace Service::AM"
assert owner.count(begin)==owner.count(middle)==owner.count(end)==1
create=begin+owner.split(begin,1)[1].split(middle,1)[0]
destroy=middle+owner.split(middle,1)[1].split(end,1)[0]
assert "DecodeGpuMemoryRegistration(command)" in create
assert "RegisterMemory(req->begin, req->end, req->flags, req->device, id)" in create
assert "DecodeGpuMemoryRelease(command)" in destroy
assert "ReleaseMemory(release->id, release->notification)" in destroy
fixture=r"""
#include <array>
#include <cassert>
#include <cstdint>
#include <memory>
#include <mutex>
#include <vector>
#include "core/hle/service/am/service/gpu_memory_registration.h"
using u32=std::uint32_t;
using u64=std::uint64_t;
struct Result {
    u32 raw{};
    constexpr bool IsSuccess() const noexcept {return raw==0;}
};
inline constexpr Result ResultSuccess{0};
namespace Kernel {
inline constexpr Result ResultInvalidCombination{1}, ResultInvalidSize{2},
    ResultOutOfResource{3}, ResultBusy{4};
}
struct HLERequestContext {
    std::array<u32,8> packet{};
    u32 command{};
    std::vector<u64> reply{};
    unsigned words{};
    const u32* CommandBuffer() const {return packet.data();}
    u32 GetCommand() const {return command;}
};
namespace IPC {
struct ResponseBuilder {
    HLERequestContext& ctx;
    ResponseBuilder(HLERequestContext& c,unsigned words):ctx(c) {
        ctx.words=words;ctx.reply.clear();
    }
    template<class T> void Push(T value) {ctx.reply.push_back(u64(value));}
};
}
namespace Service::AM {
inline void TraceNs2WorkerResult(unsigned,u32){}
struct Shared {std::mutex mutex{};};
struct IGpuWorker {
    std::mutex m_mutex{};
    std::shared_ptr<Shared> m_shared=std::make_shared<Shared>();
    bool fail_create{}, busy_release{};
    unsigned registers{}, releases{};
    Result RegisterMemory(u64 begin,u64 end,u32 flags,u32 device,u32& id) {
        ++registers;
        assert(begin==0x4000 && end==0x4fff && flags==0 && device==1);
        if(fail_create)return Kernel::ResultOutOfResource;
        id=42;
        return ResultSuccess;
    }
    Result ReleaseMemory(u32 id,u32 event) {
        ++releases;
        assert(id==42 && event==3);
        return busy_release ? Kernel::ResultBusy : ResultSuccess;
    }
    void CreateGpuAccessibleMemory(HLERequestContext&);
    void DestroyGpuAccessibleMemory(HLERequestContext&);
};
__CREATE__
__DESTROY__
}
static HLERequestContext create() {
    HLERequestContext c{};
    c.command=101;
    c.packet={0x75,6,0x4000,0,0x4fff,0,0,1};
    return c;
}
static HLERequestContext destroy() {
    HLERequestContext c{};
    c.command=102;
    c.packet={0x76,2,42,3};
    return c;
}
int main() {
    Service::AM::IGpuWorker worker;
    auto invalid=create();invalid.packet[0]=0;
    worker.CreateGpuAccessibleMemory(invalid);
    assert(invalid.words==3 && invalid.reply.size()==2);
    assert(invalid.reply[0]==Kernel::ResultInvalidCombination.raw);
    assert(invalid.reply[1]==0 && worker.registers==0);
    auto valid=create();
    worker.CreateGpuAccessibleMemory(valid);
    assert(valid.reply[0]==0 && valid.reply[1]==42 && worker.registers==1);
    worker.fail_create=true;
    auto oom=create();
    worker.CreateGpuAccessibleMemory(oom);
    assert(oom.reply[0]==Kernel::ResultOutOfResource.raw);
    assert(oom.reply[1]==0 && worker.registers==2);
    auto bad_release=destroy();bad_release.packet[2]=0;
    worker.DestroyGpuAccessibleMemory(bad_release);
    assert(bad_release.words==2 && bad_release.reply.size()==1);
    assert(bad_release.reply[0]==Kernel::ResultInvalidCombination.raw);
    assert(worker.releases==0);
    worker.busy_release=true;
    auto busy=destroy();
    worker.DestroyGpuAccessibleMemory(busy);
    assert(busy.reply[0]==Kernel::ResultBusy.raw && worker.releases==1);
    worker.busy_release=false;
    auto good=destroy();
    worker.DestroyGpuAccessibleMemory(good);
    assert(good.reply[0]==0 && worker.releases==2);
}
""".replace("__CREATE__",create).replace("__DESTROY__",destroy)
compilers=list(dict.fromkeys(x for x in (shutil.which("clang++"),shutil.which("g++")) if x))
assert compilers,"Host C++20 compiler required"
with tempfile.TemporaryDirectory(prefix="eden-h06-worker101-102-") as directory:
    src=Path(directory)/"owner.cpp";src.write_text(fixture)
    for cc in compilers:
        for opt in ("-O0","-O2"):
            exe=Path(directory)/(Path(cc).name+opt)
            args=[cc,"-std=c++20",opt,"-Wall","-Wextra","-Werror",
                  "-fsanitize=undefined","-fno-sanitize-recover=all",
                  "-I"+str(vendor/"encore-active/ns2-runtime/hle"),
                  "-I"+str(vendor/"encore-active/ns2-runtime/nvdrv"),
                  "-I"+str(vendor/"sources/eden/src"),
                  str(src),"-o",str(exe)]
            built=subprocess.run(args,capture_output=True,text=True,timeout=50,
                                 env=os.environ.copy())
            assert built.returncode==0,built.stderr[-5000:]
            done=subprocess.run([str(exe)],capture_output=True,text=True,timeout=20)
            assert done.returncode==0,done.stderr[-5000:]
            print("H06_REAL_WORKER_101_102_IPC_PASS",Path(cc).name,opt,
                  "bad_packet=refused create_oom=zero_handle release_busy=preserved",
                  flush=True)
