#!/usr/bin/env python3
"""H06: execute actual GPU TIPC 22 COPY-handle owner and OOM reply.

A copied client-session handle must keep the retained worker reference stable.
An outgoing COPY descriptor allocation failure must publish no guest handle.
"""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[2]
vendor=ROOT/"vendor"
source=(vendor/"encore-active/eden/src/core/hle/service/am/service/gpu_session.cpp").read_text()
begin="void IGpuSession::AcquireWorker("
end="void IGpuSession::GetNotificationRange("
assert source.count(begin)==source.count(end)==1
owner=begin+source.split(begin,1)[1].split(end,1)[0]
assert "ctx.AddCopyObject(m_worker);" in owner
assert "ctx.AddMoveObject(" not in owner
assert "client->Open(kernel);" not in owner
assert "client->Close(kernel);" not in owner
assert owner.index("ctx.AddCopyObject(m_worker);") < owner.index("result = ResultSuccess;")
assert owner.index("ctx.AddCopyObject(m_worker);") < owner.index("IPC::ResponseBuilder rb{ctx, 2, 1, 0};")
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
    constexpr bool IsSuccess() const noexcept {return raw==0;}
};
inline constexpr Result ResultSuccess{0};
namespace Kernel {
inline constexpr Result ResultInvalidCombination{1},
    ResultInvalidState{2}, ResultOutOfResource{3};
struct KClientSession {
    unsigned owned_refs{1};
};
}
struct HLERequestContext {
    std::array<u32,2> command{};
    bool fail_copy{};
    Kernel::KClientSession* copied{};
    unsigned copies{}, reply_copies{}, reply_moves{}, reply_words{};
    u32 reply_code{~u32{0}};
    const u32* CommandBuffer() const {return command.data();}
    void AddCopyObject(Kernel::KClientSession* object) {
        assert(object);
        if (fail_copy) throw std::bad_alloc{};
        copied=object;
        ++copies;
    }
};
namespace IPC {
struct ResponseBuilder {
    HLERequestContext& ctx;
    ResponseBuilder(HLERequestContext& c,unsigned words,
                    unsigned ncopy=0,unsigned nmove=0):ctx{c} {
        assert(words==2 && ncopy<=1 && nmove==0);
        ctx.reply_words=words;
        ctx.reply_copies=ncopy;
        ctx.reply_moves=nmove;
    }
    void Push(u32 value) {ctx.reply_code=value;}
};
}
namespace Service::AM {
namespace GP=GpuSessionProtocol;
struct IGpuSession {
    std::mutex m_lock{};
    Kernel::KClientSession* m_worker{};
    void AcquireWorker(HLERequestContext&);
};
__OWNER__
}
int main() {
    using Service::AM::IGpuSession;
    IGpuSession owner;
    Kernel::KClientSession client;
    {
        HLERequestContext ctx{{0x25,0}};
        owner.AcquireWorker(ctx);
        assert(ctx.reply_code==Kernel::ResultInvalidCombination.raw);
        assert(ctx.reply_words==2 && ctx.reply_copies==0 && ctx.reply_moves==0);
        assert(ctx.copies==0 && client.owned_refs==1);
    }
    {
        HLERequestContext ctx{{0x26,0}};
        owner.AcquireWorker(ctx);
        assert(ctx.reply_code==Kernel::ResultInvalidState.raw);
        assert(ctx.reply_copies==0 && ctx.copies==0);
    }
    owner.m_worker=&client;
    {
        HLERequestContext ctx{{0x26,0},true};
        owner.AcquireWorker(ctx);
        assert(ctx.reply_code==Kernel::ResultOutOfResource.raw);
        assert(ctx.reply_copies==0 && ctx.reply_moves==0);
        assert(ctx.copied==nullptr && ctx.copies==0 && client.owned_refs==1);
    }
    for (unsigned iteration=0;iteration<2;++iteration) {
        HLERequestContext ctx{{0x26,0}};
        owner.AcquireWorker(ctx);
        assert(ctx.reply_code==ResultSuccess.raw);
        assert(ctx.reply_words==2 && ctx.reply_copies==1 && ctx.reply_moves==0);
        assert(ctx.copied==&client && ctx.copies==1);
        // The retained worker owns the reference. The IPC writer adds the
        // independent guest handle later, with no extra owner Open().
        assert(client.owned_refs==1);
    }
    {
        HLERequestContext ctx{{0x26,1}};
        owner.AcquireWorker(ctx);
        assert(ctx.reply_code==Kernel::ResultInvalidCombination.raw);
        assert(ctx.reply_copies==0 && ctx.copies==0);
        assert(client.owned_refs==1);
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
                  "-I"+str(vendor/"encore-active/eden/src"),
                  str(src),"-o",str(exe)]
            built=subprocess.run(argv,text=True,capture_output=True,timeout=55,env=os.environ.copy())
            assert built.returncode==0,built.stderr[-5500:]
            done=subprocess.run([str(exe)],text=True,capture_output=True,timeout=20)
            assert done.returncode==0,done.stderr[-5500:]
            print("H06_GPU_ACQUIRE_WORKER_COPY_OOM_PASS",Path(cc).name,opt,
                  "invalid=refused no_worker=refused oom=no_copy"
                  " success=stable_copy_owner invalid_packet=refused",flush=True)
