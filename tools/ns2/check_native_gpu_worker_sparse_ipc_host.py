#!/usr/bin/env python3
"""H06: execute original worker 214 sparse reservation then 216 guest remap.

The real TIPC methods, native packet decoders and sparse MappingLedger run
under Clang/GCC/UBSan. Injectable NVDRV and memory services cover invalid
buffers, unowned handles, driver OOM, rollback and successful selected-kind
outputs without asserting PS5 GPU execution or a fabricated guest frame.
"""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[2]
vendor=ROOT/"vendor"
source=(vendor/"encore-active/ns2-runtime/gpu_session/core/hle/service/am/service/gpu_worker.cpp").read_text()
def extract(begin,end):
    assert source.count(begin)==source.count(end)==1,(begin,end)
    return begin+source.split(begin,1)[1].split(end,1)[0]
translate=extract("Result TranslateMappingStatus(", "} // namespace\n\nvoid IGpuWorker::NormalMapGpuMemory4K(")
sparse=extract("void IGpuWorker::CreateSparseRegion(", "void IGpuWorker::DestroySparseRegion(")
remap=extract("void IGpuWorker::ExecuteSparseMapRequests(", "Result IGpuWorker::RegisterMemory(")
for symbol in ("m_mappings.PrepareSparse(", "as->ReserveNativeSparse4K(",
               "m_mappings.CommitPrepared(", "as->ReleaseNativeSparse4K(",
               "BackGpuOnlyRegion(", "m_shared->events[request->notification]->Signal(kernel)"):
    assert symbol in sparse,symbol
for symbol in ("GW::DecodeSparseBatch(command)", "ctx.GetReadBufferSize() == bytes",
               "ctx.GetWriteBufferSize() >= request->count",
               "DecodeGpuSparseMap(element, *page_shift)",
               "m_mappings.ContainsSparse(", "std::find(m_memory.begin(), m_memory.end()",
               "as->RemapNativeSparse(staged)", "ctx.WriteBuffer(selected)",
               "result = Kernel::ResultOutOfResource;"):
    assert symbol in remap,symbol
fixture=r"""
#include <algorithm>
#include <array>
#include <cassert>
#include <cstdint>
#include <cstring>
#include <map>
#include <memory>
#include <mutex>
#include <optional>
#include <span>
#include <vector>
#include "core/hle/service/am/service/gpu_memory_registration.h"
#include "core/hle/service/am/service/gpu_worker_protocol.h"
#include "core/hle/service/am/service/gpu_session_protocol.h"
#define LOG_ERROR(...) ((void)0)
using u32=std::uint32_t;
using u64=std::uint64_t;
using u8=std::uint8_t;
struct Result {
    u32 raw{};
    constexpr bool IsSuccess() const noexcept {return raw==0;}
};
inline constexpr Result ResultSuccess{0};
namespace Kernel {
inline constexpr Result ResultInvalidCombination{1},ResultNotImplemented{2},
    ResultNotFound{3},ResultInvalidState{4},ResultOutOfResource{5},
    ResultInvalidSize{6},ResultInvalidCurrentMemory{7};
struct KernelCore {};
struct KEvent {
    unsigned signals{};
    void Signal(KernelCore&) {++signals;}
};
}
namespace Service::Nvidia {
using DeviceFD=int;
enum class NvResult {Success,InvalidState,InsufficientMemory};
struct FakeHandle {
    bool allocated{true};
    u64 orig_size{0x4000};
};
struct NvMapFile {
    std::shared_ptr<FakeHandle> handle=std::make_shared<FakeHandle>();
    std::shared_ptr<FakeHandle> GetHandle(u32 id) {
        return id==27 ? handle : nullptr;
    }
};
struct Container {
    NvMapFile nvmap{};
    NvMapFile& GetNvMapFile() {return nvmap;}
};
struct Module {
    Container container{};
    Container& GetContainer() {return container;}
};
namespace Devices {
struct NativeAS {
    NvResult reserve_result{NvResult::Success};
    NvResult release_result{NvResult::Success};
    NvResult remap_result{NvResult::Success};
    unsigned reserves{}, releases{}, remaps{};
    NvResult ReserveNativeSparse4K(u64 begin,u64 size,u8 shift) {
        assert(begin==0x20000 && size==0x2000 && shift==12);
        ++reserves;return reserve_result;
    }
    NvResult ReleaseNativeSparse4K(u64 begin,u64 size) {
        assert(begin==0x20000 && size==0x2000);
        ++releases;return release_result;
    }
    template<class V> NvResult RemapNativeSparse(const V& entries) {
        assert(entries.size()==1);
        assert(u64{entries.front().destination_pages}==0x20);
        assert(u32{entries.front().handle}==27);
        ++remaps;return remap_result;
    }
};
}
}
struct HLERequestContext {
    std::array<u32,15> packet{};
    u32 command{};
    std::vector<u8> input{},output{};
    unsigned response_words{};
    std::vector<u64> reply{};
    u64 output_capacity{1};
    const u32* CommandBuffer() const {return packet.data();}
    u32 GetCommand() const {return command;}
    std::size_t GetReadBufferSize() const {return input.size();}
    u64 GetWriteBufferSize() const {return output_capacity;}
    std::span<const u8> ReadBuffer() const {return input;}
    void WriteBuffer(const std::vector<u8>& selected) {output=selected;}
};
namespace IPC {
struct ResponseBuilder {
    HLERequestContext& ctx;
    ResponseBuilder(HLERequestContext& c,unsigned words):ctx(c) {
        ctx.response_words=words;ctx.reply.clear();
    }
    template<class T> void Push(T v) {ctx.reply.push_back(u64(v));}
};
}
namespace Service::AM {
namespace GW=GpuWorkerProtocol;
inline void TraceNs2WorkerResult(unsigned,u32){}
template<class T> void TraceNs2GpuRegion214(const u32*,const T&,u32,bool){}
inline void TraceNs2GpuSparse216(u64,u64,u64,u32){}
struct FakeGPU {
    unsigned waits{};
    void WaitForIdle() {++waits;}
};
struct System {
    FakeGPU gpu{};
    FakeGPU& GPU() {return gpu;}
};
struct Shared {
    std::mutex mutex{};
    GpuSessionProtocol::AddressSpaceSlots address_spaces{};
    GpuSessionProtocol::DeviceSlots devices{};
    std::array<Kernel::KEvent*,GW::MaxNotifications> events{};
    std::shared_ptr<Nvidia::Devices::NativeAS> owner=
        std::make_shared<Nvidia::Devices::NativeAS>();
    std::shared_ptr<Nvidia::Devices::NativeAS> FindOwnedAddressSpace(Nvidia::DeviceFD id) {
        return address_spaces.Owns(u32(id)) ? owner : nullptr;
    }
};
struct IGpuWorker {
    std::mutex m_mutex{};
    std::shared_ptr<Shared> m_shared=std::make_shared<Shared>();
    std::shared_ptr<Nvidia::Module> m_module=std::make_shared<Nvidia::Module>();
    std::vector<u32> m_memory{27};
    GW::MappingLedger m_mappings{};
    System system{};
    Kernel::KernelCore kernel{};
    bool back_fail{};
    unsigned backs{};
    Result BackGpuOnlyRegion(u32 as,u64 begin,u64 size,u8 shift) {
        assert(as==7 && begin==0x20000 && size==0x2000 && shift==12);
        ++backs;
        return back_fail ? Kernel::ResultOutOfResource : ResultSuccess;
    }
    void CreateSparseRegion(HLERequestContext&);
    void ExecuteSparseMapRequests(HLERequestContext&);
};
__TRANSLATE__
__SPARSE__
__REMAP__
}
static HLERequestContext region(u32 mode=1,u32 notification=3) {
    HLERequestContext c{};
    c.command=214;
    c.packet={0xe6,10,7,0x20000,0,0x21fff,0,12,mode,1,0,notification};
    return c;
}
static HLERequestContext batch(bool with_handle=true) {
    HLERequestContext c{};
    c.command=216;
    c.packet[0]=0x011000e8;
    c.packet[1]=7;
    c.packet[8]=1;
    c.packet[10]=7;
    c.packet[11]=40;
    c.packet[14]=3;
    Service::AM::GpuSparseMapRequest entry{};
    entry.address=0x20000;
    entry.size=0x1000;
    entry.memory=with_handle ? 27 : 0;
    entry.kind=0;
    entry.fallback_kind=0;
    c.input.resize(sizeof(entry));
    std::memcpy(c.input.data(),&entry,sizeof(entry));
    return c;
}
static void setup(Service::AM::IGpuWorker& worker,Kernel::KEvent& event) {
    using Service::AM::GpuSessionProtocol::Status;
    assert(worker.m_shared->address_spaces.Add(7)==Status::Success);
    const std::array<u32,8> device{0x39,6,1,0,0,0,2,0};
    assert(worker.m_shared->devices.Create(device).status==Status::Success);
    worker.m_shared->events[3]=&event;
}
int main() {
    Service::AM::IGpuWorker worker;
    Kernel::KEvent event{};
    setup(worker,event);
    auto& gpu=*worker.m_shared->owner;
    auto invalid=region();invalid.packet[7]=9;
    worker.CreateSparseRegion(invalid);
    assert(invalid.reply.size()==1 && invalid.reply[0]==Kernel::ResultNotImplemented.raw);
    assert(gpu.reserves==0 && event.signals==0);
    auto missing=region(1,4);
    worker.CreateSparseRegion(missing);
    assert(missing.reply[0]==Kernel::ResultNotFound.raw && gpu.reserves==0);
    gpu.reserve_result=Service::Nvidia::NvResult::InsufficientMemory;
    auto oom=region();
    worker.CreateSparseRegion(oom);
    assert(oom.reply[0]==Kernel::ResultOutOfResource.raw);
    assert(gpu.reserves==1 && worker.m_mappings.Count()==0 && event.signals==0);
    gpu.reserve_result=Service::Nvidia::NvResult::Success;
    auto accepted=region();
    worker.CreateSparseRegion(accepted);
    assert(accepted.response_words==2 && accepted.reply[0]==0);
    assert(gpu.reserves==2 && worker.m_mappings.Count()==1 && event.signals==1);
    auto duplicate=region();
    worker.CreateSparseRegion(duplicate);
    assert(duplicate.reply[0]==Kernel::ResultInvalidState.raw);
    assert(gpu.reserves==2 && event.signals==1);

    auto no_output=batch();no_output.output_capacity=0;
    worker.ExecuteSparseMapRequests(no_output);
    assert(no_output.reply[0]==Kernel::ResultInvalidSize.raw);
    assert(gpu.remaps==0 && worker.system.gpu.waits==0);
    auto invalid_entry=batch();
    Service::AM::GpuSparseMapRequest bad{};
    std::memcpy(&bad,invalid_entry.input.data(),sizeof(bad));
    bad.size=0;
    std::memcpy(invalid_entry.input.data(),&bad,sizeof(bad));
    worker.ExecuteSparseMapRequests(invalid_entry);
    assert(invalid_entry.reply[0]==Kernel::ResultInvalidCurrentMemory.raw);
    assert(gpu.remaps==0 && event.signals==1);
    worker.m_memory.clear();
    auto foreign=batch();
    worker.ExecuteSparseMapRequests(foreign);
    assert(foreign.reply[0]==Kernel::ResultNotFound.raw && gpu.remaps==0);
    worker.m_memory.push_back(27);
    gpu.remap_result=Service::Nvidia::NvResult::InsufficientMemory;
    auto remap_oom=batch();
    worker.ExecuteSparseMapRequests(remap_oom);
    assert(remap_oom.reply[0]==Kernel::ResultOutOfResource.raw);
    assert(remap_oom.reply[1]==0 && remap_oom.output.empty());
    assert(gpu.remaps==1 && worker.system.gpu.waits==1 && event.signals==1);
    gpu.remap_result=Service::Nvidia::NvResult::Success;
    auto good=batch();
    worker.ExecuteSparseMapRequests(good);
    assert(good.response_words==4 && good.reply.size()==2);
    assert(good.reply[0]==0 && good.reply[1]==1);
    assert(good.output.size()==1 && good.output[0]==0);
    assert(gpu.remaps==2 && event.signals==2 && worker.system.gpu.waits==2);
    assert(worker.m_mappings.Count()==1);

    Service::AM::IGpuWorker dense;
    Kernel::KEvent ready{};
    setup(dense,ready);
    dense.back_fail=true;
    auto failed_back=region(0);
    dense.CreateSparseRegion(failed_back);
    assert(failed_back.reply[0]==Kernel::ResultOutOfResource.raw);
    assert(dense.m_shared->owner->releases==1 && dense.m_mappings.Count()==0);
    assert(ready.signals==0);
    dense.back_fail=false;
    auto good_back=region(0);
    dense.CreateSparseRegion(good_back);
    assert(good_back.reply[0]==0 && dense.backs==2);
    assert(dense.m_mappings.Count()==1 && ready.signals==1);
}
""".replace("__TRANSLATE__",translate).replace("__SPARSE__",sparse).replace("__REMAP__",remap)
compilers=list(dict.fromkeys(x for x in (shutil.which("clang++"),shutil.which("g++")) if x))
assert compilers,"Host C++20 compiler required"
with tempfile.TemporaryDirectory(prefix="eden-h06-worker214-216-") as directory:
    cpp=Path(directory)/"owner.cpp";cpp.write_text(fixture)
    for cc in compilers:
        for opt in ("-O0","-O2"):
            exe=Path(directory)/(Path(cc).name+opt)
            args=[cc,"-std=c++20",opt,"-Wall","-Wextra","-Werror",
                  "-fsanitize=undefined","-fno-sanitize-recover=all",
                  "-I"+str(vendor/"encore-active/ns2-runtime/hle"),
                  "-I"+str(vendor/"encore-active/ns2-runtime/nvdrv"),
                  "-I"+str(vendor/"sources/eden/src"),
                  str(cpp),"-o",str(exe)]
            built=subprocess.run(args,capture_output=True,text=True,timeout=65,env=os.environ.copy())
            assert built.returncode==0,built.stderr[-6500:]
            done=subprocess.run([str(exe)],capture_output=True,text=True,timeout=25)
            assert done.returncode==0,done.stderr[-6500:]
            print("H06_REAL_WORKER_214_216_PASS",Path(cc).name,opt,
                  "reserve=real ledger remap=real owner fail_closed=1 oom=rollback output=exact",
                  flush=True)
