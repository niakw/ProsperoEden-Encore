#!/usr/bin/env python3
"""H06: execute real TIPC range and GPU-device owners, including error replies.

Extracts the production methods and GP decoder without rewriting their logic.
Clang/GCC UBSan tests exact words, ranges, allocation identity and rollback.
"""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[2]
vendor=ROOT/"vendor"
owner=(vendor/"encore-active/ns2-runtime/gpu_session/core/hle/service/am/service/gpu_session.cpp").read_text()
def extract(begin,end):
    assert owner.count(begin)==owner.count(end)==1,(begin,end)
    return begin+owner.split(begin,1)[1].split(end,1)[0]
translate=extract("static Result Translate(", "// Actual worker KSession")
notification=extract("void IGpuSession::GetNotificationRange(", "void IGpuSession::GetNotificationEvent(")
devices=extract("void IGpuSession::CreateGraphicsDevice(", "} // namespace Service::AM")
assert "result.IsSuccess() ? GP::MaxNotificationEvents - 1 : 0" in notification
assert "m_shared->devices.Create(command)" in devices
assert "m_shared->devices.Destroy(command)" in devices
fixture=r"""
#include <array>
#include <cassert>
#include <cstdint>
#include <memory>
#include <mutex>
#include <vector>
#include "core/hle/service/am/service/gpu_session_protocol.h"
using u32=std::uint32_t;
struct Result {
    u32 raw{};
    constexpr bool IsSuccess() const { return raw==0; }
};
inline constexpr Result ResultSuccess{0};
namespace Kernel {
inline constexpr Result ResultInvalidCombination{1}, ResultNotImplemented{2},
    ResultNotFound{3}, ResultOutOfResource{4}, ResultInvalidState{5};
}
struct HLERequestContext {
    std::array<u32,8> words{};
    unsigned response_size{};
    std::vector<std::uint64_t> reply{};
    const u32* CommandBuffer() const { return words.data(); }
};
namespace IPC {
struct ResponseBuilder {
    HLERequestContext& ctx;
    ResponseBuilder(HLERequestContext& c,unsigned n):ctx{c} {
        c.response_size=n; c.reply.clear();
    }
    template <class T> void Push(T value) {
        ctx.reply.push_back(static_cast<std::uint64_t>(value));
    }
};
}
namespace Service::AM {
namespace GP=GpuSessionProtocol;
struct Shared {std::mutex mutex; GP::DeviceSlots devices;};
struct IGpuSession {
    std::shared_ptr<Shared> m_shared=std::make_shared<Shared>();
    void GetNotificationRange(HLERequestContext&);
    void CreateGraphicsDevice(HLERequestContext&);
    void DestroyGraphicsDevice(HLERequestContext&);
};
__TRANSLATE__
__NOTIFICATION__
__DEVICES__
}
int main() {
    using Service::AM::IGpuSession;
    IGpuSession s;
    {
        HLERequestContext req{{0x1b,0}};
        s.GetNotificationRange(req);
        assert(req.response_size==4 && req.reply.size()==3);
        assert(req.reply[0]==0 && req.reply[1]==0 &&
               req.reply[2]==Service::AM::GP::MaxNotificationEvents-1);
        req.words[1]=1;
        s.GetNotificationRange(req);
        assert(req.reply.size()==3 && req.reply[0]==Kernel::ResultInvalidCombination.raw);
        assert(req.reply[1]==0 && req.reply[2]==0);
    }
    {
        HLERequestContext req{{0x39,6,123,0,0,0,72,0}};
        s.CreateGraphicsDevice(req);
        assert(req.response_size==3 && req.reply.size()==2);
        assert(req.reply[0]==0 && req.reply[1]==1 && s.m_shared->devices.Count()==1);
        assert(s.m_shared->devices.Get(1)->name==123);
        assert(s.m_shared->devices.Get(1)->debug_label==72);
        req.words[4]=1; // nonzero reserved device type remains unsupported
        s.CreateGraphicsDevice(req);
        assert(req.reply[0]==Kernel::ResultNotImplemented.raw);
        assert(req.reply[1]==0 && s.m_shared->devices.Count()==1);
        req.words[4]=0;
        req.words[1]=7;
        s.CreateGraphicsDevice(req);
        assert(req.reply[0]==Kernel::ResultInvalidCombination.raw);
        assert(req.reply[1]==0 && s.m_shared->devices.Count()==1);
    }
    {
        HLERequestContext req{{0x3a,1,0}};
        s.DestroyGraphicsDevice(req);
        assert(req.response_size==2 && req.reply.size()==1);
        assert(req.reply[0]==Kernel::ResultInvalidCombination.raw);
        assert(s.m_shared->devices.Count()==1);
        req.words[2]=2;
        s.DestroyGraphicsDevice(req);
        assert(req.reply[0]==Kernel::ResultNotFound.raw);
        assert(s.m_shared->devices.Count()==1);
        req.words[2]=1;
        s.DestroyGraphicsDevice(req);
        assert(req.reply[0]==0 && s.m_shared->devices.Count()==0);
        assert(!s.m_shared->devices.Get(1));
        s.DestroyGraphicsDevice(req);
        assert(req.reply[0]==Kernel::ResultNotFound.raw);
        assert(s.m_shared->devices.Count()==0);
    }
}
""".replace("__TRANSLATE__",translate).replace("__NOTIFICATION__",notification).replace("__DEVICES__",devices)
compilers=list(dict.fromkeys(x for x in (shutil.which("clang++"),shutil.which("g++")) if x))
assert compilers,"C++20 compiler required"
with tempfile.TemporaryDirectory(prefix="eden-h06-devices-") as d:
    src=Path(d)/"owner.cpp";src.write_text(fixture)
    for cc in compilers:
        for opt in ("-O0","-O2"):
            exe=Path(d)/(Path(cc).name+opt)
            cmd=[cc,"-std=c++20",opt,"-Wall","-Wextra","-Werror",
                 "-fsanitize=undefined","-fno-sanitize-recover=all",
                 "-I"+str(vendor/"encore-active/ns2-runtime/hle"),
                 str(src),"-o",str(exe)]
            built=subprocess.run(cmd,capture_output=True,text=True,timeout=60,env=os.environ.copy())
            assert built.returncode==0,built.stderr[-6000:]
            run=subprocess.run([str(exe)],capture_output=True,text=True,timeout=20)
            assert run.returncode==0,run.stderr[-6000:]
            print("H06_REAL_GPU_DEVICE_IPC_PASS",Path(cc).name,opt,
                  "range=valid+invalid devices=create+destroy unsupported=refused",flush=True)
