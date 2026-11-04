#!/usr/bin/env python3
"""Compile REAL additive NS2 auddmg:u C++ class with strict fake IPC transport.

Only metadata/property IPC and explicit non-availability of sysmix are proven.
No native PS5, audio rendering, memory-mapped guest stream or system service ABI.
"""
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VENDOR = ROOT / "vendor/encore-active/ns2-runtime/audio"
HEADER = VENDOR / "core/hle/service/audio/nx2_audio_user_client.h"
AUDIO = (VENDOR / "core/hle/service/audio/audio.cpp").read_text()
source = HEADER.read_text()
assert AUDIO.count('RegisterNamedService("auddmg:u"') == 1
assert "INx2AudioDeviceManagerService" in source
assert "GetVirtualOutputDeviceProperties" in source
assert "GetDefaultVirtualOutputDevice" in source
assert "if (ctx.GetWriteBufferSize() < 0x228)" in source
assert "rb.Push(ResultNotSupported);" in source
assert '"AttachStream (not available)"' in source
assert "GetVirtualOutputDeviceProperties" in source
assert "rb.PushIpcInterface<INx2AudioVirtualDeviceManager>(ctx, system);" in source
assert "INx2Sysmix" not in source
assert "python3 -B tools/ns2/check_native_audio_virtual_device_host.py" in (
    ROOT / ".github/workflows/encore-core-preflight.yml").read_text()

FAKES = {
    "core/hle/service/audio/errors.h": r'''
#pragma once
using Result = int;
namespace Service::Audio {
inline constexpr Result ResultNotFound = -1;
inline constexpr Result ResultInsufficientBuffer = -2;
inline constexpr Result ResultNotSupported = -3;
}
''',
    "core/hle/service/audio/audio_in_manager.h": r'''
#pragma once
struct IAudioInManager {};
''',
    "core/hle/service/audio/audio_out_manager.h": r'''
#pragma once
struct IAudioOutManager {};
''',
    "core/hle/service/audio/audio_renderer_manager.h": r'''
#pragma once
struct IAudioRendererManager {};
''',
    "core/hle/service/ipc_helpers.h": r'''
#pragma once
#include <array>
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <span>
#include <vector>
using u8 = std::uint8_t;
using u32 = std::uint32_t;
using u64 = std::uint64_t;
using Result = int;
inline constexpr Result ResultSuccess = 0;
namespace Core { struct System {}; }
namespace Service {
struct HLERequestContext {
    Result result{-999};
    std::size_t write_capacity{};
    std::vector<u8> read, write;
    u32 response_count{};
    int response_size{}, object_count{};
    std::size_t GetWriteBufferSize() const { return write_capacity; }
    std::vector<u8> ReadBuffer(std::size_t) const { return read; }
    template<std::size_t N> void WriteBuffer(const std::array<u8,N>& buffer) {
        assert(N <= write_capacity);
        write.assign(buffer.begin(),buffer.end());
    }
};
}
namespace IPC {
struct RequestParser {
    explicit RequestParser(Service::HLERequestContext&) {}
    template<class T> T Pop() { return {}; }
};
struct ResponseBuilder {
    Service::HLERequestContext& ctx;
    ResponseBuilder(Service::HLERequestContext& c,int n,int=0,int=0):ctx(c) {
        ctx.response_size=n;
    }
    void Push(Result result) { ctx.result=result; }
    void Push(u32 count) { ctx.response_count=count; }
    template<class T> void PushIpcInterface(Service::HLERequestContext& c,Core::System&) {
        assert(&c==&ctx);
        ++ctx.object_count;
    }
};
}
''',
    "core/hle/service/service.h": r'''
#pragma once
#include <cassert>
#include <cstddef>
#include "core/hle/service/ipc_helpers.h"
#define LOG_WARNING(...) ((void)0)
namespace Service {
template<class T> class ServiceFramework {
protected:
    Core::System& system;
public:
    struct FunctionInfo { int command; void(T::*method)(HLERequestContext&); const char* label; };
    explicit ServiceFramework(Core::System& owner,const char*) : system{owner} {}
    virtual ~ServiceFramework()=default;
    template<std::size_t N> void RegisterHandlers(const FunctionInfo (&functions)[N]) {
        handlers=functions; count=N;
    }
    bool HasCommand(int cmd) const {
        for(std::size_t i=0;i<count;++i)
            if(handlers[i].command==cmd) return true;
        return false;
    }
    void Dispatch(int cmd,HLERequestContext& ctx) {
        for(std::size_t i=0;i<count;++i) {
            if(handlers[i].command==cmd) {
                (static_cast<T*>(this)->*(handlers[i].method))(ctx);
                return;
            }
        }
        assert(false && "unsupported IPC command passed as a handler");
    }
private:
    const FunctionInfo* handlers{};
    std::size_t count{};
};
}
''',
}
CPP = r'''
#include <cassert>
#include <cstdio>
#include <cstring>
#include <string_view>
#include "core/hle/service/audio/nx2_audio_user_client.h"
using namespace Service::Audio;
using Service::HLERequestContext;
static u32 Word(const std::vector<u8>& bytes,std::size_t at) {
    assert(at+sizeof(u32)<=bytes.size());
    u32 out{};
    std::memcpy(&out,bytes.data()+at,sizeof(out));
    return out;
}
int main() {
    Core::System system{};
    INx2AudioDeviceManagerService root{system};
    assert(root.HasCommand(0) && !root.HasCommand(1));
    HLERequestContext opened{};
    root.Dispatch(0,opened);
    assert(opened.result==ResultSuccess &&
           opened.response_size==2 && opened.object_count==1);

    INx2AudioVirtualDeviceManager dev{system};
    assert(dev.HasCommand(0) && dev.HasCommand(100) &&
           dev.HasCommand(300) && dev.HasCommand(401) &&
           dev.HasCommand(700) && dev.HasCommand(800) &&
           !dev.HasCommand(500)); // no fake change notification event
    HLERequestContext missing_space{};
    dev.Dispatch(0,missing_space);
    assert(missing_space.result==ResultSuccess &&
           missing_space.response_count==0 && missing_space.write.empty());
    HLERequestContext list{};
    list.write_capacity=256;
    dev.Dispatch(0,list);
    assert(list.result==ResultSuccess && list.response_count==1 &&
           list.write.size()==256 &&
           std::memcmp(list.write.data(),"AudioVirtualOutput0",19)==0 &&
           list.write[19]==0);
    HLERequestContext too_small{};
    too_small.write_capacity=255;
    dev.Dispatch(100,too_small);
    assert(too_small.result==ResultInsufficientBuffer &&
           too_small.write.empty());
    HLERequestContext default_name{};
    default_name.write_capacity=256;
    dev.Dispatch(100,default_name);
    assert(default_name.result==ResultSuccess &&
           default_name.write==list.write);
    HLERequestContext bad_name{};
    bad_name.write_capacity=0x228;
    bad_name.read={'N','o','n','e',0};
    dev.Dispatch(401,bad_name);
    assert(bad_name.result==ResultNotFound && bad_name.write.empty());
    HLERequestContext short_prop{};
    short_prop.write_capacity=0x227;
    short_prop.read=list.write;
    dev.Dispatch(401,short_prop);
    assert(short_prop.result==ResultInsufficientBuffer && short_prop.write.empty());
    HLERequestContext properties{};
    properties.write_capacity=0x228;
    properties.read=list.write;
    dev.Dispatch(401,properties);
    assert(properties.result==ResultSuccess &&
           properties.write.size()==0x228);
    assert(Word(properties.write,0x100)==3 &&
           Word(properties.write,0x104)==2 &&
           Word(properties.write,0x108)==2 &&
           Word(properties.write,0x10c)==48000 &&
           Word(properties.write,0x220)==1);
    assert(std::memcmp(properties.write.data()+0x110,"AudioTvOutput",13)==0);
    for(std::size_t at=0x218;at<0x220;++at)
        assert(properties.write[at]==0); // latency is UNKNOWN
    HLERequestContext no_hid{};
    no_hid.read=list.write;
    no_hid.write_capacity=0x228;
    for(const int command:{300,700,800}) {
        HLERequestContext unsupported=no_hid;
        dev.Dispatch(command,unsupported);
        assert(unsupported.result==ResultNotSupported &&
               unsupported.write.empty() && unsupported.object_count==0);
    }
    // Existing NS1 aud:u manager bridge remains available; no source
    // fork or blanket unknown-command success was introduced.
    INx2AudioUserClient existing{system};
    assert(existing.HasCommand(1) && existing.HasCommand(2) &&
           !existing.HasCommand(0));
    std::puts("NS2_AUDIO_VIRTUAL_DEVICE_HOST_PASS list=1 default=1 properties=1 "
              "invalid_name=1 small_buffer=1 unknown_latency=1 "
              "stream_fail_closed=3 ns1_audio_bridge=1");
}
'''
compiler = shutil.which("clang++-18") or shutil.which("clang++") or shutil.which("g++")
assert compiler
env = os.environ.copy()
sdk = Path("/Library/Developer/CommandLineTools/SDKs/MacOSX15.4.sdk")
if sdk.is_dir(): env["SDKROOT"] = str(sdk)
with tempfile.TemporaryDirectory(prefix="encore-virtual-audio-") as temporary:
    temp = Path(temporary)
    for name, contents in FAKES.items():
        path = temp / name
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(contents)
    src=temp/"fixture.cpp"
    src.write_text(CPP)
    for opt in ("-O0","-O2"):
        binary=temp/("fixture"+opt)
        build = subprocess.run(
            [compiler,"-std=c++20",opt,"-Wall","-Wextra","-Werror","-Wno-unused-variable",
             "-fsanitize=undefined","-fno-sanitize-recover=all",
             "-I",str(temp),"-I",str(VENDOR),str(src),"-o",str(binary)],
            capture_output=True,text=True,env=env,timeout=45)
        assert build.returncode == 0,(opt,build.stderr[-6000:])
        run=subprocess.run([str(binary)],capture_output=True,text=True,env=env,timeout=20)
        assert run.returncode == 0,(opt,run.stderr,run.stdout)
        assert "NS2_AUDIO_VIRTUAL_DEVICE_HOST_PASS" in run.stdout
        print(run.stdout.strip(),opt)
