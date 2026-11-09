#!/usr/bin/env python3
"""H06: execute the original GPU TIPC unknown-command dispatch owner.

This real-owner Clang/GCC UBSan witness verifies fail-closed unknown command
reply, known-handler delegation, and no guest success on unrecognized TIPC.
It does not claim that the entire worker mapping ABI is finished.
"""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[2]
source=(ROOT/"vendor/encore-active/ns2-runtime/gpu_session/core/hle/service/am/service/gpu_session.cpp").read_text()
begin="Result IGpuSession::HandleSyncRequest("
end="static Result Translate("
assert source.count(begin)==source.count(end)==1
owner=begin+source.split(begin,1)[1].split(end,1)[0]
assert "handlers_tipc.contains(ctx.GetCommand())" in owner
assert "Kernel::ResultNotImplemented.raw" in owner
assert "ctx.WriteToOutgoingCommandBuffer()" in owner
fixture=r"""
#include <atomic>
#include <cassert>
#include <cstdint>
#include <cstdio>
#include <mutex>
#include <unordered_set>
#include <vector>
using u32=std::uint32_t;
struct Result {
    u32 raw{};
    constexpr bool IsSuccess() const {return raw==0;}
};
inline constexpr Result ResultSuccess{0};
namespace Kernel {
inline constexpr Result ResultNotImplemented{15};
struct KServerSession {};
}
struct HLERequestContext {
    bool tipc{true};
    u32 command{};
    std::vector<u32> reply{};
    unsigned writes{};
    bool IsTipc() const {return tipc;}
    u32 GetCommand() const {return command;}
    Result WriteToOutgoingCommandBuffer() {
        ++writes;
        return ResultSuccess;
    }
};
namespace IPC {
struct ResponseBuilder {
    HLERequestContext& ctx;
    ResponseBuilder(HLERequestContext& c,unsigned words):ctx{c} {
        assert(words==2);ctx.reply.clear();
    }
    void Push(u32 word) {ctx.reply.push_back(word);}
};
}
struct PowerState {
    bool on{true};
    bool IsPoweredOn() const {return on;}
};
struct ServiceFrameworkBase {
    unsigned handled{};
    Result HandleSyncRequest(Kernel::KServerSession&,HLERequestContext&) {
        ++handled;
        return ResultSuccess;
    }
};
struct IGpuSession: ServiceFrameworkBase {
    std::unordered_set<u32> handlers_tipc{11,12,21,22,33,41,42,202,203};
    std::mutex mutex{};
    unsigned unknown_invocations{};
    PowerState system{};
    std::unique_lock<std::mutex> LockService() {
        return std::unique_lock<std::mutex>{mutex};
    }
    void InvokeRequestTipc(HLERequestContext&) {++unknown_invocations;}
    Result HandleSyncRequest(Kernel::KServerSession&,HLERequestContext&);
};
__OWNER__
int main() {
    IGpuSession session;
    Kernel::KServerSession channel;
    HLERequestContext unknown{true,9999};
    assert(session.HandleSyncRequest(channel,unknown).IsSuccess());
    assert(unknown.writes==1 && unknown.reply.size()==1 &&
           unknown.reply[0]==Kernel::ResultNotImplemented.raw);
    assert(session.unknown_invocations==1 && session.handled==0);

    HLERequestContext known{true,22};
    assert(session.HandleSyncRequest(channel,known).IsSuccess());
    assert(known.writes==0 && known.reply.empty());
    assert(session.handled==1 && session.unknown_invocations==1);

    HLERequestContext non_tipc{false,9999};
    assert(session.HandleSyncRequest(channel,non_tipc).IsSuccess());
    assert(non_tipc.writes==0 && non_tipc.reply.empty());
    assert(session.handled==2 && session.unknown_invocations==1);

    session.system.on=false;
    HLERequestContext shutdown{true,1000};
    assert(session.HandleSyncRequest(channel,shutdown).IsSuccess());
    assert(shutdown.writes==0 && session.unknown_invocations==2);
    assert(shutdown.reply.size()==1 &&
           shutdown.reply[0]==Kernel::ResultNotImplemented.raw);
}
""".replace("__OWNER__",owner)
compilers=list(dict.fromkeys(x for x in (shutil.which("clang++"),shutil.which("g++")) if x))
assert compilers,"Host C++20 compiler required"
with tempfile.TemporaryDirectory(prefix="eden-h06-unknown-") as d:
    source_file=Path(d)/"owner.cpp";source_file.write_text(fixture)
    for cc in compilers:
        for opt in ("-O0","-O2"):
            exe=Path(d)/(Path(cc).name+opt)
            cmd=[cc,"-std=c++20",opt,"-Wall","-Wextra","-Werror",
                 "-fsanitize=undefined","-fno-sanitize-recover=all",
                 str(source_file),"-o",str(exe)]
            built=subprocess.run(cmd,capture_output=True,text=True,timeout=50,env=os.environ.copy())
            assert built.returncode==0,built.stderr[-5000:]
            run=subprocess.run([str(exe)],capture_output=True,text=True,timeout=20)
            assert run.returncode==0,run.stderr[-5000:]
            print("H06_UNKNOWN_TIPC_REAL_OWNER_PASS",Path(cc).name,opt,
                  "unknown=refused known=delegated shutdown=no_publish",flush=True)
