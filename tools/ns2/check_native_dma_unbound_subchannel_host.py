#!/usr/bin/env python3
"""Exercise the real maintained DmaPusher method paths with an unbound engine.

An invalid guest GPFIFO must not dereference a null subchannel in either the
shipping or DEV owner. The normal bound and puller paths must still dispatch.
This is source-executed host validation, NOT proof of GPU execution on PS5.
"""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
OWNERS = ROOT / 'vendor/encore-active/eden-core/src/video_core'
START = 'void DmaPusher::CallMethod(u32 argument) {'
END = '\nvoid DmaPusher::BindRasterizer('

cpp = r'''
#include <array>
#include <bitset>
#include <cassert>
#include <cstdint>
#include <cstdio>
#include <stdexcept>
#include <utility>
#include <vector>
using u32 = std::uint32_t;
using u64 = std::uint64_t;
static unsigned errors{};
#define HW_GPU 0
#define LOG_ERROR(...) (++errors)
namespace Core { struct System {}; }
namespace Service::Nvidia::Devices {
struct NativeGpuChannelRegistry {
    bool native{};
    static NativeGpuChannelRegistry& Instance() {
        static NativeGpuChannelRegistry registry;
        return registry;
    }
    bool IsNative(const void*) const { return native; }
};
}
class DmaPusher;
namespace Engines {
struct Puller {
    struct MethodCall {u32 method, argument, subchannel, count;};
    unsigned calls{}, multi_calls{};
    void CallPullerMethod(DmaPusher&, MethodCall) { ++calls; }
    void CallMultiMethod(DmaPusher&, u32, u32, const u32*, u32, u32) { ++multi_calls; }
};
}
struct Engine {
    std::bitset<65536> execution_mask{};
    std::vector<std::pair<u32,u32>> method_sink{};
    u64 current_dma_segment{};
    unsigned consumed{}, singles{}, multiples{};
    void ConsumeSink(Core::System&) { ++consumed; method_sink.clear(); }
    void CallMethod(Core::System&, u32 method, u32 arg, bool last) {
        assert(method == 0x100 && arg == 0xab && last);
        ++singles;
    }
    void CallMultiMethod(Core::System&, u32 method, const u32* src, u32 count, u32 pending) {
        assert(method == 0x100 && src && count == 2 && pending == 2);
        ++multiples;
    }
};
class DmaPusher {
public:
    struct State {u32 method{}, subchannel{}, method_count{}; u64 dma_get{}, dma_word_offset{}; bool is_last_call{};};
    static constexpr u32 non_puller_methods = 0x40;
    State dma_state{};
    Core::System system{};
    Engines::Puller puller{};
    std::array<Engine*,8> subchannels{};
    u32 channel_state{};
    void CallMethod(u32 argument);
    void CallMultiMethod(const u32* start, u32 num_methods);
};
__REAL_METHODS__
int main() {
    DmaPusher dma;
    dma.dma_state.method = 0x100;
    dma.dma_state.subchannel = 7;
    dma.dma_state.method_count = 2;
    dma.dma_state.is_last_call = true;
    dma.dma_state.dma_get = 100;
    dma.dma_state.dma_word_offset = 12;
    const u32 words[] = {0xab, 0xbb};
    dma.CallMethod(words[0]);
    dma.CallMultiMethod(words, 2);
    assert(errors == 2 && dma.puller.calls == 0 && dma.puller.multi_calls == 0);
#ifdef PS5_NATIVE
    // The ACTUAL native method owners must RETIRE the bad GPFIFO, not
    // merely log a missing bound engine and let a guest fence complete.
    auto& native=Service::Nvidia::Devices::NativeGpuChannelRegistry::Instance();
    native.native=true;
    unsigned retired{};
    try { dma.CallMethod(words[0]); }
    catch (const std::runtime_error&) { ++retired; }
    try { dma.CallMultiMethod(words,2); }
    catch (const std::runtime_error&) { ++retired; }
    assert(retired==2 && errors==4);
    native.native=false; // same source still preserves the Maxwell path.
#endif
    Engine engine;
    dma.subchannels[7] = &engine;
    dma.CallMethod(words[0]);
    assert(engine.method_sink.size() == 1 && engine.singles == 0);
    engine.execution_mask[0x100] = true;
    dma.CallMethod(words[0]);
    assert(engine.consumed == 1 && engine.singles == 1);
    assert(engine.current_dma_segment == 112);
    dma.CallMultiMethod(words, 2);
    assert(engine.multiples == 1 && engine.consumed == 2);
    dma.dma_state.method = 0x20;
    dma.CallMethod(words[0]);
    dma.CallMultiMethod(words, 2);
#ifdef PS5_NATIVE
    constexpr unsigned expected_errors=4;
#else
    constexpr unsigned expected_errors=2;
#endif
    assert(dma.puller.calls == 1 && dma.puller.multi_calls == 1 &&
           errors == expected_errors);
    std::puts("P2_7_DMA_UNBOUND_GUEST_METHOD_GUARD_PASS");
}
'''


def source_methods(name: str) -> str:
    source = (OWNERS / name).read_text()
    assert source.count(START) == 1 and source.count(END) == 1
    methods = source.split(START, 1)[1].split(END, 1)[0]
    methods = START + methods
    assert methods.count('if (!subchannel) {') == 2, name
    assert methods.count('LOG_ERROR(HW_GPU,') == 2, name
    assert methods.count('throw std::runtime_error("Native GPFIFO method on unbound subchannel")') == 2, name
    assert methods.count('subchannel->ConsumeSink(system);') == 2, name
    return methods


def main() -> None:
    # Both the normal and DEV owners must implement the same dispatch safety.
    normal = source_methods('dma_pusher.cpp')
    dev = source_methods('dma_pusher_dev.cpp')
    assert normal == dev, 'Normal and DEV DMA method owners diverged'
    compilers = [p for p in (shutil.which('clang++'), shutil.which('g++')) if p]
    assert compilers, 'host C++20 compiler missing'
    env = os.environ.copy()
    sdk = Path('/Library/Developer/CommandLineTools/SDKs/MacOSX15.4.sdk')
    if sdk.is_dir():
        env['SDKROOT'] = str(sdk)
    with tempfile.TemporaryDirectory(prefix='encore-native-unbound-') as temp:
        test_src = Path(temp) / 'test.cpp'
        test_src.write_text(cpp.replace('__REAL_METHODS__', normal))
        for compiler in dict.fromkeys(compilers):
            for opt in (0, 2):
                for ps5 in (False, True):
                    exe = Path(temp) / f'test-{Path(compiler).name}-{opt}-{int(ps5)}'
                    cmd = [compiler, '-std=c++20', f'-O{opt}', '-Wall', '-Wextra',
                           '-Werror', '-fsanitize=undefined', '-fno-sanitize-recover=all']
                    if ps5:
                        cmd.append('-DPS5_NATIVE=1')
                    cmd.extend((str(test_src), '-o', str(exe)))
                    build = subprocess.run(cmd, capture_output=True, text=True,
                                           env=env, timeout=45)
                    assert build.returncode == 0, build.stderr[-2800:]
                    run = subprocess.run([str(exe)], capture_output=True,
                                         text=True, env=env, timeout=15)
                    assert run.returncode == 0, run.stderr[-2800:]
                    assert 'P2_7_DMA_UNBOUND_GUEST_METHOD_GUARD_PASS' in run.stdout
                    print('P2_7_DMA_UNBOUND_GUARD_HOST_PASS', Path(compiler).name,
                          'O'+str(opt), 'PS5_NATIVE' if ps5 else 'NS1',
                          'real_methods=2 variants=2', flush=True)


if __name__ == '__main__':
    main()
