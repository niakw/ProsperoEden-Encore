#!/usr/bin/env python3
"""Compile the real NS2 native GPU class binder with fake channel ownership.

An unknown class on an authenticated NS2 channel must never retain a stale
DmaPusher engine pointer. Legacy NS1 invalid-class behavior is unchanged.
This is a source-executed host test, not proof of hardware execution.
"""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
PULLER = ROOT/'vendor/encore-active/ns2-runtime/gpu_dispatch/video_core/engines/puller.cpp'
DMA = ROOT/'vendor/encore-active/eden-core/src/video_core/dma_pusher.cpp'
DMA_DEV = ROOT/'vendor/encore-active/eden-core/src/video_core/dma_pusher_dev.cpp'
START = 'void Puller::ProcessBindMethod(DmaPusher& dma_pusher, const MethodCall& method_call) {'
END = '\nvoid Puller::ProcessFenceActionMethod('
source=PULLER.read_text()
assert source.count(START)==1 and source.count(END)==1
method=START+source.split(START,1)[1].split(END,1)[0]
assert method.count('dma_pusher.BindSubchannel(nullptr, method_call.subchannel,')==1
assert method.count('retire_native_3d();')==3
assert method.count('retire_native_compute();')==3
assert 'throw std::runtime_error("Native GPFIFO SET_OBJECT class unsupported")' in method
assert method.index('dma_pusher.BindSubchannel(nullptr, method_call.subchannel,') < method.index(
    'throw std::runtime_error("Native GPFIFO SET_OBJECT class unsupported")')
for path in (DMA,DMA_DEV):
    text=path.read_text()
    assert text.count('if (!subchannel) {')==2, 'Unbound native class requires safe shared DMA'

cpp=r'''
#include <array>
#include <atomic>
#include <cassert>
#include <cstdint>
#include <cstdio>
#include <memory>
#include <stdexcept>
using u32 = std::uint32_t;
static unsigned rejected{};
#define HW_GPU 0
#define LOG_DEBUG(...) ((void)0)
#define UNIMPLEMENTED_MSG(...) (++rejected)
struct Engine {};
namespace Tegra {
struct NativeAmpereMacroState {};
enum class EngineID : u32 {
    NV01_TIMER=0x0004, FERMI_TWOD_A=0x902d, MAXWELL_B=0xb197,
    KEPLER_COMPUTE_B=0xb1c0, KEPLER_INLINE_TO_MEMORY_B=0xa140,
    MAXWELL_DMA_COPY_A=0xb0b5,
};
namespace Control {
struct Payload {
    Engine fermi_2d, maxwell_3d, kepler_compute, maxwell_dma, kepler_memory, nv01_timer;
};
struct ChannelState {
    std::shared_ptr<Payload> payload = std::make_shared<Payload>();
};
}
namespace Engines {
enum class EngineTypes : u32 {
    Nv01Timer, KeplerCompute, Maxwell3D, Fermi2D, MaxwellDMA, KeplerMemory
};
}
struct DmaPusher {
    Control::ChannelState channel_state;
    std::array<Engine*,8> subchannels{};
    std::array<Engines::EngineTypes,8> kinds{};
    void BindSubchannel(Engine* engine,u32 index, Engines::EngineTypes kind) {
        assert(index<8);
        subchannels[index]=engine;
        kinds[index]=kind;
    }
};
}
namespace Service::Nvidia::Devices {
struct NativeGpuChannelRegistry {
    bool native=true, allow_graphics=true, allow_compute=true;
    unsigned retired_graphics=0, retired_compute=0, bound_graphics=0, bound_compute=0;
    static NativeGpuChannelRegistry& Instance() {
        static NativeGpuChannelRegistry r;
        return r;
    }
    bool IsNative(const Tegra::Control::ChannelState*) const { return native; }
    bool BindGraphicsEngine(const Tegra::Control::ChannelState*, Engine*, u32) {
        if (!allow_graphics || !native) return false;
        ++bound_graphics;
        return true;
    }
    bool BindComputeEngine(const Tegra::Control::ChannelState*, Engine*,u32) {
        if (!allow_compute || !native) return false;
        ++bound_compute;
        return true;
    }
    void UnbindGraphicsSubchannel(const Tegra::Control::ChannelState*,Engine*,u32) {
        ++retired_graphics;
    }
    void UnbindComputeSubchannel(const Tegra::Control::ChannelState*,Engine*,u32) {
        ++retired_compute;
    }
};
}
namespace Tegra::Engines {
constexpr u32 Gf100BindClassMask = 0xffff;
constexpr u32 Gf100BindValidMask = 0x1f0000 | Gf100BindClassMask;
class Puller {
public:
    struct MethodCall { u32 method{},argument{},subchannel{},method_count{}; };
    std::array<EngineID,8> bound_engines{};
    std::unique_ptr<Tegra::NativeAmpereMacroState> native_3d{};
    u32 native_macro_method{};
    bool native_3d_failed{};
    void ProcessBindMethod(DmaPusher&,const MethodCall&);
};
__REAL_METHOD__
}
int main() {
    using namespace Tegra;
    Engines::Puller puller;
    DmaPusher dma;
    auto& registry=Service::Nvidia::Devices::NativeGpuChannelRegistry::Instance();
    unsigned native_faults{};
    const auto bind=[&](u32 klass) {
        try {
            puller.ProcessBindMethod(dma, {0,klass,2,0});
        } catch (const std::runtime_error&) {
            ++native_faults;
        }
    };
    // Existing ordinary GPU binding; native rejected class revokes pointer.
    bind(static_cast<u32>(EngineID::MAXWELL_B));
    assert(dma.subchannels[2] == &dma.channel_state.payload->maxwell_3d);
    bind(0xdead);
    assert(dma.subchannels[2] == nullptr && rejected==1);
    bind(static_cast<u32>(EngineID::KEPLER_COMPUTE_B));
    assert(dma.subchannels[2] == &dma.channel_state.payload->kepler_compute);
    bind(0xc797);
    assert(dma.subchannels[2] == &dma.channel_state.payload->maxwell_3d);
    assert(registry.bound_graphics==1);
    bind(0x5678);
    assert(dma.subchannels[2] == nullptr && registry.retired_graphics==1);
    bind(0xc7c0);
    assert(dma.subchannels[2] == &dma.channel_state.payload->kepler_compute);
    assert(registry.bound_compute==1);
    bind(0xfff1);
    assert(dma.subchannels[2] == nullptr && registry.retired_compute==1);
    bind(0xc7b5);
    assert(dma.subchannels[2] == &dma.channel_state.payload->maxwell_dma);
    bind(0xfff1);
    assert(dma.subchannels[2] == nullptr);
#ifdef PS5_NATIVE
    assert(native_faults==4 &&
           "native SET_OBJECT unsupported class must fault before queue completion");
#else
    assert(native_faults==0);
#endif
    // Invalid class and forbidden Ampere bind must not alter old NS1 behavior.
    registry.native=false;
    bind(static_cast<u32>(EngineID::MAXWELL_B));
    assert(dma.subchannels[2] == &dma.channel_state.payload->maxwell_3d);
    bind(0x5678);
    assert(dma.subchannels[2] == &dma.channel_state.payload->maxwell_3d);
    bind(0xc797);
    assert(dma.subchannels[2] == &dma.channel_state.payload->maxwell_3d);
#ifdef PS5_NATIVE
    assert(native_faults==4 && "NS1 must not inherit native fatal binding policy");
#endif
    // An invalid owner/failed native 3D bind must not disturb current owner.
    registry.native=true;
    registry.allow_graphics=false;
    bind(0xc797);
    assert(dma.subchannels[2] == &dma.channel_state.payload->maxwell_3d);
    std::puts("P2_7_NATIVE_GPU_INVALID_CLASS_FAIL_CLOSED_PASS");
}
'''


def main() -> None:
    env=os.environ.copy()
    sdk=Path('/Library/Developer/CommandLineTools/SDKs/MacOSX15.4.sdk')
    if sdk.is_dir(): env['SDKROOT']=str(sdk)
    compilers=list(dict.fromkeys(x for x in (shutil.which('clang++'),shutil.which('g++')) if x))
    assert compilers
    with tempfile.TemporaryDirectory(prefix='encore-native-class-') as folder:
        src=Path(folder)/'class.cpp'
        src.write_text(cpp.replace('__REAL_METHOD__',method))
        for compiler in compilers:
            for opt in (0,2):
                for ps5 in (False,True):
                    exe=Path(folder)/f'{Path(compiler).name}-{opt}-{int(ps5)}'
                    cmd=[compiler,'-std=c++20',f'-O{opt}','-Wall','-Wextra',
                         '-Werror','-fsanitize=undefined','-fno-sanitize-recover=all']
                    if ps5:cmd.append('-DPS5_NATIVE=1')
                    cmd.extend((str(src),'-o',str(exe)))
                    build=subprocess.run(cmd,env=env,text=True,capture_output=True,timeout=45)
                    assert build.returncode==0,build.stderr[-3500:]
                    run=subprocess.run([str(exe)],env=env,text=True,capture_output=True,timeout=15)
                    assert run.returncode==0,run.stderr[-3500:]
                    assert 'P2_7_NATIVE_GPU_INVALID_CLASS_FAIL_CLOSED_PASS' in run.stdout
                    print('P2_7_NATIVE_INVALID_CLASS_HOST_PASS',Path(compiler).name,
                          f'O{opt}', 'PS5' if ps5 else 'host',flush=True)


if __name__=='__main__':
    main()
