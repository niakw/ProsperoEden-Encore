#!/usr/bin/env python3
"""Exercise the real NVDRV H:0x18/0x1a/ctx owner guard under host UBSan.

The method body is extracted byte-for-byte from the maintained nvhost_gpu
source; only Core, KProcess and FD interfaces are supplied as host mocks.
The original native/legacy identity registry and exact source structure are
checked without a PS5 build or enabling the experimental native driver.
"""
from pathlib import Path
import os
import shutil
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[2]
CPP=ROOT/'vendor/encore-active/ns2-runtime/nvdrv_gpu/core/hle/service/nvdrv/devices/nvhost_gpu.cpp'
HEADER=ROOT/'vendor/encore-active/ns2-runtime/nvdrv_gpu/core/hle/service/nvdrv/devices/nvhost_gpu.h'
code=CPP.read_text()
name='NvResult nvhost_gpu::ValidateChannelOwner(DeviceFD fd, u64& program_id) const'
assert code.count(name)==1
start=code.index(name)
brace=code.index('{',start)
depth=1
end=brace+1
while depth:
    if code[end]=='{':depth+=1
    elif code[end]=='}':depth-=1
    end+=1
body=code[start:end]
assert 'sessions.find(fd)' in body
assert 'sessions[fd]' not in body
assert 'program_id = process->GetProgramId();' in body
assert 'const bool native =' in body
assert 'NativeGpuProcessRegistry::Instance().Contains(opened->process)' in body
assert body.index('sessions.find(fd)') < body.index('program_id = process->GetProgramId();')
assert '[[nodiscard]] NvResult ValidateChannelOwner(DeviceFD fd, u64& program_id) const;' in HEADER.read_text()
for method in ('AllocGPFIFOEx','AllocGPFIFOEx2'):
    segment=code.split(f'NvResult nvhost_gpu::{method}(',1)[1].split('return NvResult::Success;\n}',1)[0]
    assert 'sessions[fd]' not in segment
    assert 'std::scoped_lock lk(channel_mutex);' in segment
    assert segment.count('ValidateChannelOwner(fd, program_id)')==1
    assert segment.index('ValidateChannelOwner(fd, program_id)') < segment.index('channel_state->initialized')
    assert segment.index('ValidateChannelOwner(fd, program_id)') < segment.index('channel_state->program_id = program_id;')
    assert segment.index('ValidateChannelOwner(fd, program_id)') < segment.index('InitChannel(')
context=code.split('NvResult nvhost_gpu::AllocateObjectContext(',1)[1].split('return NvResult::Success;\n}',1)[0]
assert 'ValidateChannelOwner(fd, verified_program_id)' in context
assert context.index('ValidateChannelOwner(') < context.index('params.flags = allowed_mask;')
assert context.index('ValidateChannelOwner(') < context.index('ctxObjs[ctx_class_number_index] = params;')
# SubmitGPFIFOImpl's original per-native-owner gate remains in place.
submission=code.split('NvResult nvhost_gpu::SubmitGPFIFOImpl(',1)[1].split('Core::Memory::Memory& nvhost_gpu::GetSessionMemory(',1)[0]
assert 'for (const auto& [other_fd, session_id] : sessions)' in submission
assert submission.index('if (native && !native_plan)') < submission.index('gpu.PushGPUEntries(bind_id, std::move(entries));')

fixture=r'''
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <unordered_map>
#include <unordered_set>
#include <optional>
#include <cstdio>
namespace Service::Nvidia::Devices {
using u64=std::uint64_t;
using DeviceFD=int;
enum class NvResult { Success, InvalidState };
struct FakeProcess {
    u64 id{};
    u64 GetProgramId() const {return id;}
};
struct FakeSession { FakeProcess* process{}; };
struct FakeCore {
    std::unordered_map<int,FakeSession> pool;
    const FakeSession* GetSession(int id) const {
        auto it=pool.find(id);
        return it==pool.end()?nullptr:&it->second;
    }
};
class NativeGpuProcessRegistry {
    std::unordered_set<const FakeProcess*> owners;
public:
    static NativeGpuProcessRegistry& Instance() {static NativeGpuProcessRegistry one;return one;}
    bool Contains(const FakeProcess* process) const {return owners.contains(process);}
    void Register(const FakeProcess* process) {owners.insert(process);}
    void Unregister(const FakeProcess* process) {owners.erase(process);}
};
class nvhost_gpu {
public:
    explicit nvhost_gpu(FakeCore& core_):core(core_){}
    NvResult ValidateChannelOwner(DeviceFD fd,u64& program_id) const;
    FakeCore& core;
    std::unordered_map<DeviceFD,int> sessions;
};
__OWNER_BODY__
}
int main() {
    using namespace Service::Nvidia::Devices;
    FakeCore core;
    FakeProcess legacy{1001},legacy2{1002}, native{2001},native2{2002};
    core.pool.emplace(10,FakeSession{&legacy});
    core.pool.emplace(11,FakeSession{&legacy2});
    core.pool.emplace(20,FakeSession{&native});
    core.pool.emplace(21,FakeSession{&native});
    core.pool.emplace(22,FakeSession{&native2});
    core.pool.emplace(30,FakeSession{nullptr});
    nvhost_gpu gpu(core);
    auto& native_registry=NativeGpuProcessRegistry::Instance();
    constexpr u64 sentinel=0xdeadbeef;
    u64 program=sentinel;
    // Missing FD must not insert ghost key or modify program identity.
    assert(gpu.ValidateChannelOwner(9,program)==NvResult::InvalidState);
    assert(gpu.sessions.empty() && program==sentinel);
    // Stale session ID and null process fail without modifying caller output.
    gpu.sessions.emplace(3,777);
    assert(gpu.ValidateChannelOwner(3,program)==NvResult::InvalidState);
    assert(program==sentinel && gpu.sessions.size()==1);
    gpu.sessions.clear();
    gpu.sessions.emplace(4,30);
    assert(gpu.ValidateChannelOwner(4,program)==NvResult::InvalidState);
    assert(program==sentinel);
    gpu.sessions.clear();
    // Two unrelated LEGACY FDs preserve historical Maxwell compatibility.
    gpu.sessions.emplace(5,10);
    gpu.sessions.emplace(6,11);
    assert(gpu.ValidateChannelOwner(5,program)==NvResult::Success && program==1001);
    assert(gpu.ValidateChannelOwner(6,program)==NvResult::Success && program==1002);
    // A native FD may never initialise a shared channel from a foreign
    // legacy session, and a legacy FD must refuse the same native channel.
    native_registry.Register(&native);
    gpu.sessions.emplace(7,20);
    program=sentinel;
    assert(gpu.ValidateChannelOwner(7,program)==NvResult::InvalidState);
    assert(program==sentinel);
    assert(gpu.ValidateChannelOwner(5,program)==NvResult::InvalidState);
    assert(program==sentinel);
    gpu.sessions.clear();
    gpu.sessions.emplace(7,20);
    gpu.sessions.emplace(8,21);
    assert(gpu.ValidateChannelOwner(7,program)==NvResult::Success && program==2001);
    assert(gpu.ValidateChannelOwner(8,program)==NvResult::Success && program==2001);
    gpu.sessions.emplace(9,22);
    program=sentinel;
    assert(gpu.ValidateChannelOwner(7,program)==NvResult::InvalidState && program==sentinel);
    native_registry.Register(&native2);
    assert(gpu.ValidateChannelOwner(9,program)==NvResult::InvalidState && program==sentinel);
    native_registry.Unregister(&native2);
    gpu.sessions.erase(9);
    // Even a stale non-owner session blocks authentic native allocation.
    gpu.sessions.emplace(9,999);
    assert(gpu.ValidateChannelOwner(7,program)==NvResult::InvalidState && program==sentinel);
    gpu.sessions.erase(9);
    assert(gpu.ValidateChannelOwner(7,program)==NvResult::Success && program==2001);
    // After native teardown a remaining pair of legacy sessions works.
    native_registry.Unregister(&native);
    gpu.sessions.clear();
    gpu.sessions.emplace(5,10);
    gpu.sessions.emplace(6,11);
    assert(gpu.ValidateChannelOwner(5,program)==NvResult::Success && program==1001);
    assert(gpu.sessions.size()==2);
    std::puts("P0_2_NATIVE_GPU_ALLOC_FD_OWNER_RECOVERY_PASS");
}
'''.replace('__OWNER_BODY__',body)
compiler=shutil.which('clang++') or shutil.which('g++')
assert compiler
sdk=Path('/Library/Developer/CommandLineTools/SDKs/MacOSX15.4.sdk')
env=os.environ.copy()
if sdk.is_dir():env['SDKROOT']=str(sdk)
with tempfile.TemporaryDirectory(prefix='encore-gpu-alloc-owner-') as temp:
    path=Path(temp)/'real-alloc-owner.cpp'
    path.write_text(fixture)
    for opt in (0,2):
        exe=Path(temp)/f'alloc-owner-O{opt}'
        cc=[compiler,'-std=c++20',f'-O{opt}','-Wall','-Wextra',
            '-Werror','-fsanitize=undefined','-fno-sanitize-recover=all',
            str(path),'-o',str(exe)]
        compiled=subprocess.run(cc,capture_output=True,text=True,env=env,timeout=65)
        assert compiled.returncode==0,compiled.stderr[-4400:]
        ran=subprocess.run([str(exe)],capture_output=True,text=True,env=env,timeout=20)
        assert ran.returncode==0,ran.stderr[-4400:]
        assert 'P0_2_NATIVE_GPU_ALLOC_FD_OWNER_RECOVERY_PASS' in ran.stdout
        print('P0_2_NATIVE_GPU_ALLOC_FD_UBSAN_PASS',f'O{opt}',flush=True)
