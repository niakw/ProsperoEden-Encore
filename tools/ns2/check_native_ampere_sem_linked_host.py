#!/usr/bin/env python3
"""G10: execute REAL native Ampere puller acquire/release/resume C++ owners.

Two channel owners share a mapped guest semaphore. The mock rasterizer keeps
the real GPU fence write PENDING until an explicit GPU-completion event.
Neither this mock nor the host proves a real Vulkan QMD3 completion: G10
remains open until that linked execution is qualified.
"""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[2]
NATIVE=ROOT/"vendor/encore-active/ns2-runtime/gpu_dispatch"
source=(NATIVE/"video_core/engines/puller.cpp").read_text()
begin="struct CoherentNativeSemaphoreValue {"
end="void Puller::ProcessSemaphoreAcquire("
assert source.count(begin)==source.count(end)==1
owner=begin+source.split(begin,1)[1].split(end,1)[0]
for required in ("ReadCoherentNativeSemaphore", "bool Puller::ResumeNativeAcquire(",
                 "void Puller::ProcessNativeSemaphoreExecute(",
                 "parked acquire backing remapped",
                 "acquire page remapped during read"):
    assert required in owner,required
header=(NATIVE/"video_core/engines/puller.h").read_text()
assert "u64 cpu_address{};" in header

fixture=r"""
#include <array>
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <optional>
#include <stdexcept>
#include <utility>
#include "video_core/engines/native_ampere_semaphore.h"
using u32=std::uint32_t;
using u64=std::uint64_t;
using GPUVAddr=u64;
using namespace Tegra::Engines;
namespace VideoCommon {
enum class QueryType {Payload};
enum class QueryPropertiesFlags {IsAFence};
enum class CacheType {BufferCache};
}
struct MemoryManager {
    bool mapped{true};
    bool cpu_alias{true};
    bool remap_during_read{};
    u64 cpu_address{0x9000};
    u32 word{2};
    unsigned gpu_lookups{}, guest_reads{};
    bool IsFullyMappedRange(GPUVAddr addr,std::size_t count) const {
        return mapped && addr==0x1000 && count==sizeof(u32);
    }
    std::optional<u64> GpuToCpuAddress(GPUVAddr addr,std::size_t count) {
        ++gpu_lookups;
        if(!IsFullyMappedRange(addr,count) || !cpu_alias)return {};
        return cpu_address;
    }
    template<typename T> T Read(GPUVAddr addr) {
        assert(addr==0x1000 && mapped);
        ++guest_reads;
        if(remap_during_read){
            cpu_address+=0x1000;
            remap_during_read=false;
        }
        return static_cast<T>(word);
    }
};
struct Rasterizer {
    MemoryManager* memory{};
    std::optional<u32> pending_gpu_release{};
    int queries{}, releases{}, buffer_flushes{};
    bool buffer_dirty{};
    void Query(GPUVAddr addr,VideoCommon::QueryType type,
               VideoCommon::QueryPropertiesFlags flags,u32 value,u32) {
        assert(addr==0x1000 && type==VideoCommon::QueryType::Payload &&
               flags==VideoCommon::QueryPropertiesFlags::IsAFence);
        ++queries;
        pending_gpu_release=value;
    }
    void CompleteGpuFence() {
        assert(pending_gpu_release.has_value() && memory);
        memory->word=*pending_gpu_release;
        pending_gpu_release.reset();
        buffer_dirty=true;
    }
    bool MustFlushRegion(u64 address,std::size_t bytes,VideoCommon::CacheType cache) {
        assert(bytes==4 && cache==VideoCommon::CacheType::BufferCache);
        assert(address==memory->cpu_address);
        return buffer_dirty;
    }
    void FlushRegion(u64 address,std::size_t bytes,VideoCommon::CacheType cache) {
        assert(address==memory->cpu_address && bytes==4 &&
               cache==VideoCommon::CacheType::BufferCache);
        ++buffer_flushes;
        buffer_dirty=false;
    }
    void ReleaseFences(){++releases;}
};
struct DmaPusher {
    MemoryManager& memory_manager;
    Rasterizer* rasterizer{};
};
struct Puller {
    struct Regs {std::array<u32,64> reg_array{};} regs;
    struct PendingNativeAcquire {
        GPUVAddr address{};
        u32 value{},operation{};
        u64 cpu_address{};
    };
    std::optional<PendingNativeAcquire> pending_native_acquire{};
    bool ResumeNativeAcquire(DmaPusher&);
    void ProcessNativeSemaphoreExecute(DmaPusher&,u32);
};
__REAL_OWNER__
int main(){
    // A is suspended. B can release while A's later commands must not run.
    MemoryManager memory;
    Rasterizer gpu{&memory};
    DmaPusher a_push{memory,&gpu},b_push{memory,&gpu};
    Puller channel_a,channel_b;
    channel_a.regs.reg_array[0x17]=0x1000;
    channel_a.regs.reg_array[0x19]=17;
    channel_b.regs.reg_array[0x17]=0x1000;
    channel_b.regs.reg_array[0x19]=17;
    channel_a.ProcessNativeSemaphoreExecute(a_push,0);
    assert(channel_a.pending_native_acquire);
    assert(channel_a.pending_native_acquire->cpu_address==0x9000);
    assert(!channel_a.ResumeNativeAcquire(a_push));
    channel_b.ProcessNativeSemaphoreExecute(b_push,1);
    assert(gpu.queries==1 && gpu.pending_gpu_release==17 && memory.word==2);
    assert(!channel_a.ResumeNativeAcquire(a_push)); // queued release is not GPU completion
    assert(channel_a.pending_native_acquire && memory.word==2);
    gpu.CompleteGpuFence();
    assert(memory.word==17);
    assert(channel_a.ResumeNativeAcquire(a_push));
    assert(!channel_a.pending_native_acquire && gpu.buffer_flushes==1);
    assert(channel_a.ResumeNativeAcquire(a_push));

    // A parked wait cannot consume an unrelated physical page under the
    // SAME mapped GPU VA, even when the new page has its expected value.
    memory.word=2;
    channel_a.regs.reg_array[0x19]=50;
    channel_a.ProcessNativeSemaphoreExecute(a_push,2);
    assert(channel_a.pending_native_acquire);
    const int released_before_stale=gpu.releases;
    memory.cpu_address=0xa000;memory.word=50;
    bool refused=false;
    try{(void)channel_a.ResumeNativeAcquire(a_push);}
    catch(const std::runtime_error&){refused=true;}
    assert(refused && channel_a.pending_native_acquire &&
           gpu.releases==released_before_stale);
    memory.cpu_address=0x9000;
    assert(channel_a.ResumeNativeAcquire(a_push));
    assert(!channel_a.pending_native_acquire);

    // A remap during a supposedly coherent CPU-side semaphore read must
    // reject the value even if its numeric payload accidentally matches.
    memory.word=77;
    channel_a.regs.reg_array[0x19]=77;
    memory.remap_during_read=true;
    refused=false;
    try{channel_a.ProcessNativeSemaphoreExecute(a_push,0);}
    catch(const std::runtime_error&){refused=true;}
    assert(refused && !channel_a.pending_native_acquire);
    memory.cpu_address=0x9000;

    // Unsupported methods and revoked GMMU addresses do not create real
    // GPU write queries or falsely complete a parked queue.
    auto invalid=[&](u32 control){
        try{channel_b.ProcessNativeSemaphoreExecute(b_push,control);}
        catch(const std::runtime_error&){return true;}
        return false;
    };
    const int writes_before=gpu.queries, flush_before=gpu.releases;
    memory.cpu_alias=false;
    assert(invalid(1)); // Resident GMMU, no CPU view for QueryCache
    assert(gpu.queries==writes_before && !channel_b.pending_native_acquire);
    memory.cpu_alias=true;
    assert(invalid(6) && invalid(7));
    assert(gpu.queries==writes_before && gpu.releases==flush_before);
    memory.mapped=false;
    assert(invalid(1) && invalid(0));
    assert(gpu.queries==writes_before && !channel_b.pending_native_acquire);
    std::puts("G10_REAL_PARKED_SEMAPHORE_OWNER_PASS channels=2 "
              "release_before_gpu_retire=not_completed resume_after_gpu_retire=1 "
              "page_rebind=refused mid_read_rebind=refused cpu_alias_missing=refused"
              " invalid=refused "
              "Vulkan_gpu_dispatch=not_exercised");
}
""".replace("__REAL_OWNER__",owner)
compilers=list(dict.fromkeys(filter(None,(shutil.which("clang++"),shutil.which("g++")))))
assert compilers
with tempfile.TemporaryDirectory(prefix="eden-g10-two-channel-") as temp:
    src=Path(temp)/"real_puller.cpp"
    src.write_text(fixture)
    for cc in compilers:
        for opt in ("-O0","-O2"):
            exe=Path(temp)/(Path(cc).name+opt)
            cmd=[cc,"-std=c++20",opt,"-Wall","-Wextra","-Werror",
                 "-fsanitize=undefined","-fno-sanitize-recover=all",
                 "-I"+str(NATIVE),str(src),"-o",str(exe)]
            build=subprocess.run(cmd,capture_output=True,text=True,timeout=60,
                                 env=os.environ.copy())
            assert build.returncode==0,(cc,build.stderr[-6000:])
            test=subprocess.run([str(exe)],capture_output=True,text=True,
                                timeout=15,env=os.environ.copy())
            assert test.returncode==0,(cc,test.stderr[-6000:])
            print(Path(cc).name,opt,test.stdout.strip(),flush=True)
