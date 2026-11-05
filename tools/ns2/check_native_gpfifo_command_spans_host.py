#!/usr/bin/env python3
"""P2.7: execute real NVDRV native GPFIFO command-span admission on host.

A readable ioctl array does not prove each nested command VA is mapped.
Tests the actual owner guard before InitChannel/Bind/fence mutations, including
partial page holes, 49-bit overflow, and legacy NS1 unchanged.
"""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
OWNER = ROOT/'vendor/encore-active/ns2-runtime/nvdrv_gpu/core/hle/service/nvdrv/devices/nvhost_gpu.cpp'
source = OWNER.read_text()
submit_begin = 'NvResult nvhost_gpu::SubmitGPFIFOImpl('
submit_end = '\nCore::Memory::Memory& nvhost_gpu::GetSessionMemory('
assert source.count(submit_begin) == source.count(submit_end) == 1
impl = source[source.index(submit_begin):source.index(submit_end)]
start = '    // P2.7: every native GPFIFO entry must refer to a fully mapped GMMU'
end = '    // Lazily initialize channel when address space is available'
assert impl.count(start) == impl.count(end) == 1
real = impl[impl.index(start):impl.index(end)]
assert 'if (native && channel_state->memory_manager)' in real
assert 'if (command.size == 0) continue;' in real
assert 'static_cast<u64>(command.size) * sizeof(Tegra::CommandHeader)' in real
assert 'IsFullyMappedRange(address, bytes)' in real
assert 'return NvResult::InvalidSize;' in real
assert impl.index(start) < impl.index('system.GPU().InitChannel(')
assert impl.index(start) < impl.index('NativeGpuChannelRegistry::Instance().Bind(')
assert impl.index(start) < impl.index('IncrementSyncpointMaxExt(')
assert '#include "video_core/memory_manager.h"' in source

cpp = r'''
#include <algorithm>
#include <cassert>
#include <cstdint>
#include <cstdio>
#include <memory>
#include <set>
#include <vector>
using u32 = std::uint32_t;
using u64 = std::uint64_t;
namespace Tegra {
struct CommandHeader { u32 argument{}; };
static_assert(sizeof(CommandHeader)==4);
struct CommandListHeader { u64 addr{}; u32 size{}; };
struct CommandList { std::vector<CommandListHeader> command_lists; };
}
constexpr u64 GpuLimit = u64{1} << 49;
struct MappedMemory {
    std::set<u64> physical_pages{};
    mutable unsigned reads{};
    bool IsFullyMappedRange(u64 address,u64 bytes) const {
        ++reads;
        if (!bytes || address >= GpuLimit || bytes > GpuLimit - address) return false;
        const u64 first=address & ~u64{4095};
        const u64 last=(address+bytes-1) & ~u64{4095};
        for (u64 page=first;page<=last;page+=4096) {
            if (!physical_pages.contains(page)) return false;
        }
        return true;
    }
};
struct Channel { MappedMemory* memory_manager{}; };
enum class NvResult { Success, InvalidSize, InvalidState };
static unsigned failures{};
#define Service_NVDRV 0
#define LOG_ERROR(...) (++failures)
struct Submission {
    Channel channel{};
    Channel* channel_state{&channel};
    bool is_native{true};
    unsigned init{},bind{},fences{};
    NvResult Submit(Tegra::CommandList entries) {
        const bool native=is_native;
__REAL_GUARD__
        if (native && !channel_state->memory_manager) return NvResult::InvalidState;
        ++init; ++bind; ++fences;
        return NvResult::Success;
    }
};
int main() {
    MappedMemory memory;
    memory.physical_pages={0x1000,0x2000,0x4000,GpuLimit-4096};
    Submission engine;
    engine.channel.memory_manager=&memory;
    auto reject=[&](Tegra::CommandList entries) {
        const unsigned before=memory.reads;
        assert(engine.Submit(std::move(entries))==NvResult::InvalidSize);
        assert(memory.reads>before);
        assert(engine.init==0 && engine.bind==0 && engine.fences==0);
    };
    // One mapped page does not make the second page mapped.
    reject({{{0x2ffc,2}}});
    reject({{{0x2000,1},{0x3000,1}}});
    reject({{{0,1}}});
    reject({{{GpuLimit-4096,2048}}});
    reject({{{GpuLimit,1}}});
    assert(failures==5);
    // Every page must be mapped, including unaligned range endpoints.
    assert(engine.Submit({{{0x1000,1},{0x1ffc,2}}})==NvResult::Success);
    assert(engine.init==1 && engine.bind==1 && engine.fences==1);
    // A zero-word header is legitimate and must not spuriously read GPU RAM.
    const unsigned before=memory.reads;
    assert(engine.Submit({{{0,0},{0x2000,0}}})==NvResult::Success);
    assert(memory.reads==before);
    engine.is_native=false;
    const unsigned legacy_reads=memory.reads;
    assert(engine.Submit({{{0x3000,1}}})==NvResult::Success);
    assert(memory.reads==legacy_reads);
    engine.is_native=true;
    engine.channel.memory_manager=nullptr;
    assert(engine.Submit({{{0x1000,1}}})==NvResult::InvalidState);
    assert(engine.init==3 && engine.bind==3 && engine.fences==3);
    std::puts("P2_7_NATIVE_GPFIFO_NESTED_MAPPED_SPANS_PASS");
}
'''.replace('__REAL_GUARD__',real)


def main() -> None:
    env=os.environ.copy()
    sdk=Path('/Library/Developer/CommandLineTools/SDKs/MacOSX15.4.sdk')
    if sdk.is_dir():env['SDKROOT']=str(sdk)
    compilers=list(dict.fromkeys(c for c in (shutil.which('clang++'),shutil.which('g++')) if c))
    assert compilers
    with tempfile.TemporaryDirectory(prefix='encore-gpfifo-spans-') as temp:
        source_file=Path(temp)/'actual_guard.cpp'
        source_file.write_text(cpp)
        for compiler in compilers:
            for opt in (0,2):
                exe=Path(temp)/f'{Path(compiler).name}-O{opt}'
                build=subprocess.run([compiler,'-std=c++20',f'-O{opt}','-Wall','-Wextra',
                                      '-Werror','-fsanitize=undefined','-fno-sanitize-recover=all',
                                      str(source_file),'-o',str(exe)],
                                     capture_output=True,text=True,env=env,timeout=50)
                assert build.returncode==0,build.stderr[-4500:]
                executed=subprocess.run([str(exe)],capture_output=True,text=True,env=env,timeout=15)
                assert executed.returncode==0,executed.stderr[-4500:]
                assert 'P2_7_NATIVE_GPFIFO_NESTED_MAPPED_SPANS_PASS' in executed.stdout
                print('P2_7_GPFIFO_NESTED_GMMU_SPAN_HOST_PASS',Path(compiler).name,f'O{opt}',flush=True)

if __name__=='__main__':main()
