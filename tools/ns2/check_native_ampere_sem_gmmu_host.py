#!/usr/bin/env python3
"""G10: run the actual native Ampere SEM_EXECUTE owner on real host C++.

A 49-bit aligned VA must also belong to a live GMMU mapping before RELEASE
can enqueue a Vulkan-backed fence write or ACQUIRE may park a channel.
This executes the production C++ method, not an independently copied policy.
"""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[2]
vendor=ROOT/"vendor/encore-active/ns2-runtime/gpu_dispatch"
source=(vendor/"video_core/engines/puller.cpp").read_text()
begin="void Puller::ProcessNativeSemaphoreExecute("
end="void Puller::ProcessSemaphoreAcquire("
assert source.count(begin)==source.count(end)==1
owner=begin+source.split(begin,1)[1].split(end,1)[0]
assert "memory_manager.IsFullyMappedRange(address, sizeof(u32))" in owner
assert owner.index("IsFullyMappedRange(")<owner.index("rasterizer->Query(")
assert owner.index("IsFullyMappedRange(")<owner.index("rasterizer->ReleaseFences()")
fixture=r"""
#include <array>
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <stdexcept>
#include <utility>
#include "video_core/engines/native_ampere_semaphore.h"
using u32=std::uint32_t;
using GPUVAddr=std::uint64_t;
using namespace Tegra::Engines;
namespace VideoCommon {
enum class QueryType { Payload };
enum class QueryPropertiesFlags { IsAFence };
}
struct MemoryManager {
    bool mapped{true};
    u32 word{7};
    unsigned admission_checks{};
    bool IsFullyMappedRange(GPUVAddr address, std::size_t bytes) {
        ++admission_checks;
        assert(bytes==4);
        return mapped && address==0x1000;
    }
};
struct Rasterizer {
    int releases{}, queries{};
    GPUVAddr last_address{};
    u32 last_payload{};
    void Query(GPUVAddr a, VideoCommon::QueryType type,
               VideoCommon::QueryPropertiesFlags flags, u32 value, u32) {
        assert(type==VideoCommon::QueryType::Payload);
        assert(flags==VideoCommon::QueryPropertiesFlags::IsAFence);
        ++queries;last_address=a;last_payload=value;
    }
    void ReleaseFences() {++releases;}
};
struct DmaPusher {
    MemoryManager memory_manager{};
    Rasterizer* rasterizer{};
};
static u32 ReadCoherentNativeSemaphore(DmaPusher& pusher, GPUVAddr addr) {
    if(!pusher.memory_manager.IsFullyMappedRange(addr,sizeof(u32)))
        throw std::runtime_error("coherent read not mapped");
    return pusher.memory_manager.word;
}
struct Puller {
    struct Regs {
        std::array<u32,64> reg_array{};
    } regs;
    struct PendingNativeAcquire { GPUVAddr address; u32 value; u32 operation; };
    std::optional<PendingNativeAcquire> pending_native_acquire{};
    void ProcessNativeSemaphoreExecute(DmaPusher&,u32);
};
__REAL_OWNER__
int main() {
    Puller owner;
    Rasterizer rasterizer;
    DmaPusher pusher;
    pusher.rasterizer=&rasterizer;
    owner.regs.reg_array[0x17]=0x1000;
    owner.regs.reg_array[0x18]=0;
    owner.regs.reg_array[0x19]=7;
    auto rejected=[&](u32 control) {
        try { owner.ProcessNativeSemaphoreExecute(pusher,control); }
        catch(const std::runtime_error&) {return true;}
        return false;
    };
    pusher.memory_manager.mapped=false;
    assert(rejected(1)); // release to unmapped memory never produces a fence
    assert(rasterizer.queries==0 && rasterizer.releases==0);
    assert(rejected(0)); // unmapped wait must not park a completed queue
    assert(!owner.pending_native_acquire);
    assert(rasterizer.queries==0 && rasterizer.releases==0);
    pusher.memory_manager.mapped=true;
    owner.regs.reg_array[0x17]=0x2000;
    assert(rejected(1));
    assert(!owner.pending_native_acquire && rasterizer.queries==0);
    owner.regs.reg_array[0x17]=0x1000;
    owner.ProcessNativeSemaphoreExecute(pusher,1);
    assert(rasterizer.queries==1 && rasterizer.last_address==0x1000);
    assert(rasterizer.last_payload==7 && !owner.pending_native_acquire);
    owner.ProcessNativeSemaphoreExecute(pusher,0);
    assert(rasterizer.releases==1 && !owner.pending_native_acquire);
    pusher.memory_manager.word=6;
    owner.ProcessNativeSemaphoreExecute(pusher,2);
    assert(rasterizer.releases==2 && owner.pending_native_acquire);
    assert(owner.pending_native_acquire->operation==2 &&
           owner.pending_native_acquire->address==0x1000);
    owner.pending_native_acquire.reset();
    assert(rejected(6));
    assert(!owner.pending_native_acquire && rasterizer.queries==1);
    assert(pusher.memory_manager.admission_checks>=6);
}
""".replace("__REAL_OWNER__",owner)
compilers=list(dict.fromkeys(x for x in (shutil.which("clang++"),shutil.which("g++")) if x))
assert compilers,"C++20 host compiler required"
with tempfile.TemporaryDirectory(prefix="eden-g10-real-gmmu-") as folder:
    file=Path(folder)/"owner.cpp";file.write_text(fixture)
    for cc in compilers:
        for opt in ("-O0","-O2"):
            exe=Path(folder)/(Path(cc).name+opt)
            argv=[cc,"-std=c++20",opt,"-Wall","-Wextra","-Werror",
                  "-fsanitize=undefined","-fno-sanitize-recover=all",
                  "-I"+str(vendor),str(file),"-o",str(exe)]
            built=subprocess.run(argv,capture_output=True,text=True,timeout=55,
                                 env=os.environ.copy())
            assert built.returncode==0,built.stderr[-5000:]
            run=subprocess.run([str(exe)],capture_output=True,text=True,timeout=15)
            assert run.returncode==0,run.stderr[-5000:]
            print("G10_REAL_NATIVE_SEM_GMMU_ADMISSION_PASS",Path(cc).name,opt,
                  "mapped_release=1 invalid_release=refused no_fake_fence=1",flush=True)
