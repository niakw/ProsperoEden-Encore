#!/usr/bin/env python3
"""H04: execute real VI2 MaxResolution/Encoding owner bodies, both IPC verdicts.

This is a source-extracted, compiler-executed HOST test; it does not claim
a PS5 display, a real guest IPC transport, or a rendered NS2 frame.
"""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "vendor/encore-active/ns2-runtime/graphics_supervisor/core/hle/service/am/service/graphics_supervisor.cpp"
source = SOURCE.read_text()

def method(signature):
    assert source.count(signature) == 1, signature
    start = source.index(signature)
    brace = source.index("{", start)
    level = 0
    for i in range(brace, len(source)):
        if source[i] == "{":
            level += 1
        elif source[i] == "}":
            level -= 1
            if level == 0:
                return source[start:i + 1]
    raise AssertionError("Unterminated native VI2 method: " + signature)

members = {
    "W": method("    static u64 W(const u32* p,size_t i) {"),
    "Find": method("    Client* Find(u64 id) {"),
    "Validate": method("    Result ValidateDisplayStatus(HLERequestContext& ctx, u32 command) const {"),
    "Max": method("    void MaxResolution(HLERequestContext& ctx) {"),
    "Encoding": method("    void Encoding(HLERequestContext& ctx) {"),
}
assert source.count("{106,&IVi2Session::MaxResolution,\"GetBufferMaxResolution\"}") == 1
assert source.count("{351,&IVi2Session::Encoding,\"SetClientOutputEncoding\"}") == 1
assert 'GraphicsSupervisorProtocol::Vi2MaxResolutionMode(' in members["Max"]
assert 'W(p,4)==0x14' in members["Encoding"]
assert 'Find(W(p,2))' in members["Encoding"]
assert "IsDefaultVi2DisplayQuery(" in members["Validate"]

code = r"""
#include <algorithm>
#include <array>
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <memory>
#include <optional>
#include <ranges>
#include <vector>
#include "core/hle/service/am/service/graphics_supervisor_protocol.h"
// Types come from the real shared protocol header (no ABI redefinition).

struct Result {
    u32 raw;
    [[nodiscard]] constexpr bool IsSuccess() const { return raw == 0; }
    constexpr bool operator==(const Result&) const = default;
};
inline constexpr Result ResultSuccess{0};
namespace Kernel {
inline constexpr Result ResultInvalidCombination{11};
inline constexpr Result ResultNotImplemented{12};
inline constexpr Result ResultNotFound{13};
inline constexpr Result ResultInvalidState{14};
}
struct HLERequestContext {
    std::array<u32,16> words{};
    std::vector<u32> reply{};
    size_t response_words{};
    const u32* CommandBuffer() const { return words.data(); }
};
namespace IPC {
struct ResponseBuilder {
    HLERequestContext& ctx;
    ResponseBuilder(HLERequestContext& c, size_t words): ctx{c} {
        ctx.reply.clear();
        ctx.response_words=words;
    }
    template<typename T> void Push(T v) {
        if constexpr(sizeof(T) == 8) {
            ctx.reply.push_back(static_cast<u32>(v));
            ctx.reply.push_back(static_cast<u32>(u64{v} >> 32));
        } else {
            ctx.reply.push_back(static_cast<u32>(v));
        }
    }
};
}
namespace Settings {
inline bool docked = true;
inline bool IsDockedMode() { return docked; }
}
namespace Service::AM {
struct FakeVi {
    s64 width{2560}, height{1440};
    Result status{ResultSuccess};
    Result GetDisplayResolution(s64* w, s64* h, u64) const {
        if (!status.IsSuccess()) return status;
        *w=width; *h=height;
        return ResultSuccess;
    }
};
struct Client { u64 token; };
class IVi2Session {
public:
    FakeVi* m_vi{};
    std::optional<u64> m_display{};
    std::vector<Client> m_clients{};

__W__
__FIND__
__VALIDATE__
__MAX__
__ENCODING__
};
}
static void SetQuery(HLERequestContext& ctx, u32 command) {
    ctx.words.fill(0);
    ctx.words[0]=command+16; ctx.words[1]=2;
    const u64 display=Service::AM::GraphicsSupervisorProtocol::Vi2DefaultDisplayName;
    ctx.words[2]=static_cast<u32>(display);
    ctx.words[3]=static_cast<u32>(display >> 32);
}
int main() {
    using namespace Service::AM;
    FakeVi real_vi{};
    IVi2Session service{};
    service.m_vi=&real_vi;
    service.m_display=7;
    service.m_clients.push_back(Client{0x1122334455667788ULL});
    HLERequestContext ctx{};

    SetQuery(ctx,106);
    Settings::docked=true;
    service.MaxResolution(ctx);
    assert(ctx.response_words==4 && ctx.reply.size()==3 &&
           ctx.reply[0]==0 && ctx.reply[1]==4 && ctx.reply[2]==0);
    Settings::docked=false;
    service.MaxResolution(ctx);
    assert(ctx.reply[0]==0 && ctx.reply[1]==2 && ctx.reply[2]==0);

    ctx.words[2]=0; // wrong display, cannot advertise a real mode
    service.MaxResolution(ctx);
    assert(ctx.reply[0]==Kernel::ResultInvalidCombination.raw &&
           ctx.reply[1]==0 && ctx.reply[2]==0);
    SetQuery(ctx,106);
    ctx.words[1]=1; // malformed count
    service.MaxResolution(ctx);
    assert(ctx.reply[0]==Kernel::ResultInvalidCombination.raw && ctx.reply[1]==0);
    SetQuery(ctx,106);
    service.m_display.reset(); // no active guest display
    service.MaxResolution(ctx);
    assert(ctx.reply[0]==Kernel::ResultInvalidState.raw && ctx.reply[1]==0);
    service.m_display=7;
    real_vi.width=0; // reject fake display resolution
    service.MaxResolution(ctx);
    assert(ctx.reply[0]==Kernel::ResultNotImplemented.raw && ctx.reply[1]==0);
    real_vi.width=2560;
    real_vi.status=Kernel::ResultNotFound;
    service.MaxResolution(ctx);
    assert(ctx.reply[0]==Kernel::ResultNotFound.raw && ctx.reply[1]==0);
    real_vi.status=ResultSuccess;

    ctx.words.fill(0);
    ctx.words[0]=0x16f; ctx.words[1]=4;
    ctx.words[2]=0x55667788; ctx.words[3]=0x11223344;
    ctx.words[4]=0x14; // the one admitted SDK output encoding
    service.Encoding(ctx);
    assert(ctx.response_words==2 && ctx.reply.size()==1 && ctx.reply[0]==0);
    ctx.words[4]=0x15;
    service.Encoding(ctx);
    assert(ctx.reply[0]==Kernel::ResultNotImplemented.raw);
    ctx.words[4]=0x14;ctx.words[2]=42; // no owned client
    service.Encoding(ctx);
    assert(ctx.reply[0]==Kernel::ResultNotFound.raw);
    ctx.words[2]=0x55667788;ctx.words[0]=0;
    service.Encoding(ctx);
    assert(ctx.reply[0]==Kernel::ResultInvalidCombination.raw);
    ctx.words[0]=0x16f;ctx.words[1]=2;
    service.Encoding(ctx);
    assert(ctx.reply[0]==Kernel::ResultInvalidCombination.raw);
    std::puts("H04_REAL_VI2_IPC_OWNER_PASS maxres=2 live_rejections=5 encoding=0x14 only unknown_client=refused malformed=refused");
}
"""
for key, value in members.items():
    code=code.replace("__" + key.upper() + "__",value)

headers = [
    "-I" + str(ROOT/"vendor/encore-active/ns2-runtime/hle"),
    "-I" + str(ROOT/"vendor/sources/eden/src"),
]
compilers=list(dict.fromkeys(filter(None,(shutil.which("clang++"),shutil.which("g++")))))
assert compilers, "C++20 compiler required"
with tempfile.TemporaryDirectory(prefix="eden-h04-real-vi2-ipc-") as temp:
    src=Path(temp)/"vi2.cpp"
    src.write_text(code)
    for compiler in compilers:
        for opt in ("-O0","-O2"):
            exe=Path(temp)/(Path(compiler).name+opt)
            build=[compiler,"-std=c++20",opt,"-Wall","-Wextra","-Werror",
                   "-Wno-unused-variable","-fsanitize=undefined",
                   "-fno-sanitize-recover=all",*headers,str(src),"-o",str(exe)]
            result=subprocess.run(build,env=os.environ.copy(),capture_output=True,
                                  text=True,timeout=60)
            assert result.returncode==0,(compiler,opt,result.stderr[-5000:])
            run=subprocess.run([str(exe)],capture_output=True,text=True,timeout=20)
            assert run.returncode==0,(compiler,opt,run.stderr[-3000:])
            assert "H04_REAL_VI2_IPC_OWNER_PASS" in run.stdout
            print("H04_REAL_VI2_IPC_OWNER_PASS",Path(compiler).name,opt,flush=True)
