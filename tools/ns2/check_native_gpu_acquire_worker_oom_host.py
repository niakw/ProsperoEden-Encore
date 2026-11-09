#!/usr/bin/env python3
"""H06: execute the actual native AcquireWorker move-handle IPC owner.

Inject outgoing-descriptor std::bad_alloc AFTER a real KClientSession
reference was opened. Validate error reply without moved handles, exact
ref-count rollback, subsequent successful retry and legacy invalid packets.
This is an extracted production method under a kernel lifecycle harness.
"""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[2]
vendor=ROOT/"vendor"
source=(vendor/"encore-active/ns2-runtime/gpu_session/core/hle/service/am/service/gpu_session.cpp").read_text()
begin="void IGpuSession::AcquireWorker("
end="void IGpuSession::GetNotificationRange("
assert source.count(begin)==source.count(end)==1
owner=begin+source.split(begin,1)[1].split(end,1)[0]
assert "client->Open(kernel);" in owner
assert "ctx.AddMoveObject(client);" in owner
assert "client->Close(kernel);" in owner
assert owner.index("ctx.AddMoveObject(client);") < owner.index("result = ResultSuccess;")
assert owner.index("ctx.AddMoveObject(client);") < owner.index("IPC::ResponseBuilder rb{ctx, 2, 0, 1};")
assert 'catch (const std::bad_alloc&)' in owner
assert "IPC::ResponseBuilder rb{ctx, 2};" in owner

harness=r"""
#include <array>
#include <cassert>
#include <cstdint>
#include <mutex>
#include <new>
#include <span>
#include "core/hle/service/am/service/gpu_session_protocol.h"
using u32=std::uint32_t;
struct Result {
    u32 raw{};
    constexpr bool IsSuccess() const noexcept { return raw==0; }
};
inline constexpr Result ResultSuccess{0};
namespace Kernel {
inline constexpr Result ResultInvalidCombination{1},
    ResultInvalidState{2},ResultOutOfResource{3};
struct KernelCore {};
struct KClientSession {
    int refs{1},opens{},closes{};
    void Open(KernelCore&) { ++refs;++opens; }
    void Close(KernelCore&) { assert(refs>0);--refs;++closes; }
};
}
struct HLERequestContext {
    std::array<u32,2> command{};
    bool fail_move{};
    Kernel::KClientSession* transferred{};
    unsigned transfer_count{},response_words{},response_moves{};
    u32 reply_code{~u32{0}};
    const u32* CommandBuffer() const { return command.data(); }
    void AddMoveObject(Kernel::KClientSession* client) {
        assert(client);
        if(fail_move)throw std::bad_alloc{};
        transferred=client;
        ++transfer_count;
    }
};
namespace IPC {
struct ResponseBuilder {
    HLERequestContext& ctx;
    ResponseBuilder(HLERequestContext& context,unsigned words,
                    unsigned copies=0,unsigned moves=0):ctx{context} {
        assert(!copies && words==2);
        ctx.response_words=words;
        ctx.response_moves=moves;
    }
    void Push(u32 value) { ctx.reply_code=value; }
};
}
namespace Service::AM {
namespace GP=GpuSessionProtocol;
struct IGpuSession {
    std::mutex m_lock{};
    Kernel::KernelCore kernel{};
    Kernel::KClientSession* m_worker{};
    void AcquireWorker(HLERequestContext&);
};
__OWNER__
}
int main(){
    using Service::AM::IGpuSession;
    IGpuSession owner;
    Kernel::KClientSession client;
    {
        HLERequestContext ctx{{0x25,0}};
        owner.AcquireWorker(ctx);
        assert(ctx.reply_code==Kernel::ResultInvalidCombination.raw);
        assert(ctx.response_words==2 && ctx.response_moves==0);
        assert(ctx.transfer_count==0 && client.refs==1);
    }
    {
        HLERequestContext ctx{{0x26,0}};
        owner.AcquireWorker(ctx);
        assert(ctx.reply_code==Kernel::ResultInvalidState.raw);
        assert(ctx.response_words==2 && ctx.response_moves==0);
        assert(ctx.transfer_count==0 && client.refs==1);
    }
    owner.m_worker=&client;
    {
        HLERequestContext ctx{{0x26,0},true};
        owner.AcquireWorker(ctx);
        assert(ctx.reply_code==Kernel::ResultOutOfResource.raw);
        assert(ctx.response_words==2 && ctx.response_moves==0);
        assert(ctx.transferred==nullptr && ctx.transfer_count==0);
        assert(client.refs==1 && client.opens==1 && client.closes==1);
    }
    {
        HLERequestContext ctx{{0x26,0}};
        owner.AcquireWorker(ctx);
        assert(ctx.reply_code==ResultSuccess.raw);
        assert(ctx.response_words==2 && ctx.response_moves==1);
        assert(ctx.transferred==&client && ctx.transfer_count==1);
        assert(client.refs==2 && client.opens==2 && client.closes==1);
        client.Close(owner.kernel); // guest consumes transferred move handle
        assert(client.refs==1 && client.opens==2 && client.closes==2);
    }
    {
        HLERequestContext ctx{{0x26,1}};
        owner.AcquireWorker(ctx);
        assert(ctx.reply_code==Kernel::ResultInvalidCombination.raw);
        assert(ctx.response_moves==0 && ctx.transfer_count==0);
        assert(client.refs==1 && client.opens==2);
    }
}
""".replace("__OWNER__",owner)
compilers=list(dict.fromkeys(x for x in (shutil.which("clang++"),shutil.which("g++")) if x))
assert compilers,"C++20 compiler required"
with tempfile.TemporaryDirectory(prefix="eden-h06-acquire-worker-") as d:
    src=Path(d)/"real_owner.cpp";src.write_text(harness)
    for cc in compilers:
        for opt in ("-O0","-O2"):
            exe=Path(d)/(Path(cc).name+opt)
            argv=[cc,"-std=c++20",opt,"-Wall","-Wextra","-Werror",
                  "-fsanitize=undefined","-fno-sanitize-recover=all",
                  "-I"+str(vendor/"encore-active/ns2-runtime/hle"),
                  str(src),"-o",str(exe)]
            built=subprocess.run(argv,text=True,capture_output=True,timeout=55,env=os.environ.copy())
            assert built.returncode==0,built.stderr[-5500:]
            done=subprocess.run([str(exe)],text=True,capture_output=True,timeout=20)
            assert done.returncode==0,done.stderr[-5500:]
            print("H06_GPU_ACQUIRE_WORKER_MOVE_OOM_PASS",Path(cc).name,opt,
                  "invalid=refused no_worker=refused oom=rolled_back"
                  " success=exact_move_refcount invalid_packet=refused",flush=True)
