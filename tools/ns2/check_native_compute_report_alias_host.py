#!/usr/bin/env python3
"""G10: replay the actual Ampere Compute semaphore-report admission and retire owner.

A resident GMMU mapping WITHOUT the CPU alias required by QueryCache may
not queue a guest semaphore completion. Exercise 4- and 16-byte reports,
reduction, unmap and revoked-owner paths with the real owner C++ method.
GPU completion is deliberately controlled by a mock, not a Vulkan claim.
"""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[2]
NATIVE=ROOT/"vendor/encore-active/ns2-runtime/gpu_dispatch"
source=(NATIVE/"video_core/engines/puller.cpp").read_text()
begin="void Puller::ProcessNativeComputeReportSemaphore("
end="\n// Native QMD3 PCAS:"
assert source.count(begin)==source.count(end)==1
owner=begin+source.split(begin,1)[1].split(end,1)[0]
assert owner.index("IsFullyMappedRange(address, write_bytes)") < owner.index(
    "GpuToCpuAddress(address, write_bytes)")
assert owner.index("GpuToCpuAddress(address, write_bytes)") < owner.index(
    "if (reduction_enabled) {")
assert owner.index("GpuToCpuAddress(address, write_bytes)") < owner.index(
    "pusher.rasterizer->Query(")
assert "Native Compute report semaphore missing CPU backing" in owner
harness=r"""
#include <algorithm>
#include <array>
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <functional>
#include <memory>
#include <optional>
#include <stdexcept>
#include <utility>
#include "video_core/native_qmd.h"
using u32=std::uint32_t;
using u64=std::uint64_t;
using GPUVAddr=u64;
#define LOG_ERROR(...) ((void)0)
[[maybe_unused]] constexpr int HW_GPU=1;
namespace VideoCommon {
enum class QueryType {Payload};
enum class QueryPropertiesFlags {IsAFence,HasTimeout};
}
struct ComputeEngine {
    struct {std::array<u32,0x700> reg_array{};} regs;
};
struct Payload {ComputeEngine kepler_compute;};
struct Channel {
    std::shared_ptr<Payload> payload=std::make_shared<Payload>();
};
namespace Service::Nvidia::Devices {
class NativeGpuChannelRegistry {
public:
    struct Ticket {int process{1},generation{2},channel_generation{3};};
    bool alive{true};
    static NativeGpuChannelRegistry& Instance() {
        static NativeGpuChannelRegistry r; return r;
    }
    std::optional<Ticket> CaptureTicket(const Channel*) {
        return alive?std::optional<Ticket>{Ticket{}}:std::nullopt;
    }
    std::optional<Ticket> CaptureComputeTicket(const ComputeEngine*) {
        return alive?std::optional<Ticket>{Ticket{}}:std::nullopt;
    }
    bool IsComputeCurrent(const ComputeEngine*,const Ticket&)const{return alive;}
    bool IsCurrent(const Channel*,const Ticket&)const{return alive;}
};
}
struct MemoryManager {
    bool mapped{true},cpu_alias{true};
    u32 word{5};
    unsigned writes{};
    bool IsFullyMappedRange(GPUVAddr address,std::size_t bytes)const{
        return mapped && address==0x1000 && (bytes==4 || bytes==16);
    }
    std::optional<u64> GpuToCpuAddress(GPUVAddr address,std::size_t bytes)const{
        if (!cpu_alias || !IsFullyMappedRange(address,bytes))return std::nullopt;
        return 0x9000;
    }
    template<class T> T Read(GPUVAddr a)const{
        assert(mapped&&a==0x1000);return static_cast<T>(word);
    }
    template<class T> void Write(GPUVAddr a,T val){
        assert(mapped&&a==0x1000);word=val;++writes;
    }
};
struct Rasterizer {
    unsigned queries{},fences{};
    std::optional<u32> pending_payload{};
    std::function<void()> pending_fence{};
    void Query(GPUVAddr a,VideoCommon::QueryType type,
               VideoCommon::QueryPropertiesFlags flag,u32 payload,u32) {
        assert(a==0x1000&&type==VideoCommon::QueryType::Payload);
        assert(flag==VideoCommon::QueryPropertiesFlags::IsAFence ||
               flag==VideoCommon::QueryPropertiesFlags::HasTimeout);
        ++queries;pending_payload=payload;
    }
    void SignalFence(std::function<void()> callback) {
        ++fences;pending_fence=std::move(callback);
    }
    void CompleteGpu(MemoryManager& mem){
        if(pending_fence){auto callback=std::move(pending_fence);
            pending_fence={};callback();}
        if(pending_payload){mem.word=*pending_payload;pending_payload.reset();++mem.writes;}
    }
};
struct DmaPusher {
    Channel channel_state;
    MemoryManager memory_manager;
    Rasterizer* rasterizer{};
};
namespace Tegra::Engines {
struct Puller {
    void ProcessNativeComputeReportSemaphore(DmaPusher&,u32);
};
__ACTUAL_OWNER__
}
int main(){
    using namespace Service::Nvidia::Devices;
    DmaPusher pusher;
    Rasterizer gpu;
    pusher.rasterizer=&gpu;
    auto& regs=pusher.channel_state.payload->kepler_compute.regs.reg_array;
    regs[0x6c0]=0;regs[0x6c1]=0x1000;regs[0x6c2]=17;
    Tegra::Engines::Puller puller;
    auto denied=[&](u32 control){
        try {puller.ProcessNativeComputeReportSemaphore(pusher,control);}
        catch(const std::runtime_error&){return true;}
        return false;
    };
    const u32 one=1U<<28;
    const u32 reduce=1U<<3;
    pusher.memory_manager.cpu_alias=false;
    assert(denied(one)&&denied(0)&&denied(reduce|one));
    assert(gpu.queries==0&&gpu.fences==0&&pusher.memory_manager.writes==0);
    pusher.memory_manager.cpu_alias=true;
    pusher.memory_manager.mapped=false;
    assert(denied(one)&&denied(reduce|one));
    pusher.memory_manager.mapped=true;
    assert(denied(3|one)); // invalid native operation (control & 3)
    assert(gpu.queries==0&&gpu.fences==0);
    // Release must not become a guest-visible value until host GPU retires.
    puller.ProcessNativeComputeReportSemaphore(pusher,one);
    assert(gpu.queries==1&&gpu.pending_payload==17);
    assert(pusher.memory_manager.word==5);
    gpu.CompleteGpu(pusher.memory_manager);
    assert(pusher.memory_manager.word==17&&pusher.memory_manager.writes==1);
    // Reduction is registered after admission, never written synchronously.
    regs[0x6c2]=2;
    puller.ProcessNativeComputeReportSemaphore(pusher,reduce|one);
    assert(gpu.fences==1&&pusher.memory_manager.word==17);
    gpu.CompleteGpu(pusher.memory_manager);
    assert(pusher.memory_manager.word==19&&pusher.memory_manager.writes==2);
    // Revoked authenticated GPU epoch: pending completion cannot write guest.
    puller.ProcessNativeComputeReportSemaphore(pusher,reduce|one);
    assert(gpu.fences==2);
    NativeGpuChannelRegistry::Instance().alive=false;
    gpu.CompleteGpu(pusher.memory_manager);
    assert(pusher.memory_manager.word==19&&pusher.memory_manager.writes==2);
    assert(denied(one));
    std::puts("G10_NATIVE_COMPUTE_REPORT_REAL_OWNER_PASS"
              " no_cpu_alias=refused unmapped=refused invalid=refused"
              " release_after_retirement=1 reduction_after_retirement=1"
              " revoked_epoch_no_write=1 real_vulkan_qmd=not_exercised");
}
""".replace("__ACTUAL_OWNER__",owner)
compilers=list(dict.fromkeys(x for x in
    (shutil.which("clang++"),shutil.which("g++")) if x))
assert compilers
with tempfile.TemporaryDirectory(prefix="eden-g10-report-") as temp:
    src=Path(temp)/"owner.cpp";src.write_text(harness)
    for cc in compilers:
        for opt in ("-O0","-O2"):
            exe=Path(temp)/(Path(cc).name.replace("+","p")+opt)
            cmd=[cc,"-std=c++20",opt,"-Wall","-Wextra","-Werror",
                 "-fsanitize=undefined","-fno-sanitize-recover=all",
                 "-I"+str(NATIVE),str(src),"-o",str(exe)]
            built=subprocess.run(cmd,capture_output=True,text=True,
                                 timeout=60,env=os.environ.copy())
            assert built.returncode==0,(cc,built.stderr[-6000:])
            result=subprocess.run([str(exe)],capture_output=True,text=True,
                                  timeout=20,env=os.environ.copy())
            assert result.returncode==0,(cc,result.stderr[-6000:])
            print(Path(cc).name,opt,result.stdout.strip(),flush=True)
