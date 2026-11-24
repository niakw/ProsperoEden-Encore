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
assert "struct BlockingBoundaryTrace" in source and "EDEN_NS2_BLOCKING_BOUNDARY" in source
def extract(begin,end):
    assert source.count(begin)==source.count(end)==1,(begin,end)
    return begin+source.split(begin,1)[1].split(end,1)[0]
translate=extract("Result TranslateMappingStatus(", "} // namespace\n\nvoid IGpuWorker::NormalMapGpuMemory4K(")
sparse=extract("void IGpuWorker::CreateSparseRegion(", "void IGpuWorker::DestroySparseRegion(")
remap=extract("void IGpuWorker::ExecuteSparseMapRequests(", "Result IGpuWorker::RegisterMemory(")
release=extract("Result IGpuWorker::ReleaseMemory(", "void IGpuWorker::CreateGpuAccessibleMemory(")
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
for symbol in ("auto staged_entry = *entry;", "m_dense_regions.upper_bound(",
               "staged_entry.handle = region.nvmap_handle;",
               "staged_entry.source_pages ="):
    assert symbol in remap,symbol
for symbol in ("SnapshotNativeSparseHandle(id, ranges)",
               "m_mappings.SparsePageShift(", "sparse_restore",
               "EDEN_NS2_GPU_102_SPARSE_RESTORE"):
    assert symbol in release or symbol in source,symbol
assert release.index("SnapshotNativeSparseHandle(id, ranges)") < release.index("system.GPU().WaitForIdle()")
assert release.index("system.GPU().WaitForIdle()") < release.index("batch.owner->RemapNativeSparse(batch.entries)")
assert release.index("batch.owner->RemapNativeSparse(batch.entries)") < release.index("nvmap.FreeHandleIfUnpinned(id)")
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
    u32 last_handle{};
    u64 last_source_pages{}, last_reserve_size{}, last_release_size{};
    NvResult ReserveNativeSparse4K(u64 begin,u64 size,u8 shift) {
        assert(begin==0x20000 && size>=0x1000 && (size&0xfff)==0 && shift==12);
        ++reserves;last_reserve_size=size;return reserve_result;
    }
    NvResult ReleaseNativeSparse4K(u64 begin,u64 size) {
        assert(begin==0x20000 && size>=0x1000 && (size&0xfff)==0);
        ++releases;last_release_size=size;return release_result;
    }
    template<class V> NvResult RemapNativeSparse(const V& entries) {
        assert(entries.size()==1);
        assert(u64{entries.front().destination_pages}==0x20);
        last_handle=u32{entries.front().handle};
        last_source_pages=u64{entries.front().source_pages};
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
// The real selected owner has a PS5-only timing trace. These fixtures test IPC/ledger
// behavior, so provide its no-op host shape while separately asserting the production trace above.
struct BlockingBoundaryTrace { BlockingBoundaryTrace(const char*, u32, u64, u64) {} };
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
    struct Dense {
        u64 address{}, size{}, alias{};
        u32 nvmap_handle{};
        bool gmmu_released{}, nvmap_released{};
    };
    std::map<std::pair<u32,u64>,Dense> m_dense_regions{};
    System system{};
    Kernel::KernelCore kernel{};
    bool back_fail{};
    unsigned backs{}, dense_retires{};
    Result BackGpuOnlyRegion(u32 as,u64 begin,u64 size,u8 shift) {
        assert(as==7 && begin==0x20000 && size>=0x1000 &&
               (size&0xfff)==0 && shift==12);
        ++backs;
        if (back_fail) return Kernel::ResultOutOfResource;
        m_dense_regions.emplace(std::make_pair(as,begin),
                                Dense{begin,size,0,91,false,false});
        return ResultSuccess;
    }
    bool RetireGpuOnlyRegion(u32 as,u64 begin) {
        auto it=m_dense_regions.find({as,begin});
        if (it==m_dense_regions.end()) return false;
        ++dense_retires;
        m_dense_regions.erase(it);
        return true;
    }
    void CreateSparseRegion(HLERequestContext&);
    void ExecuteSparseMapRequests(HLERequestContext&);
};
__TRANSLATE__
__SPARSE__
__REMAP__
}
static HLERequestContext region(u32 mode=1,u32 notification=3,u64 size=0x2000) {
    assert(size>=0x1000 && (size&0xfff)==0);
    HLERequestContext c{};
    c.command=214;
    const u64 end=0x20000+size-1;
    c.packet={0xe6,10,7,0x20000,0,u32(end),u32(end>>32),12,mode,1,0,notification};
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
    Service::AM::IGpuWorker growing;
    Kernel::KEvent grown_event{};
    setup(growing,grown_event);
    auto first_generation=region();
    growing.CreateSparseRegion(first_generation);
    assert(first_generation.reply[0]==0);
    auto second_generation=region(1,3,0x4000);
    growing.CreateSparseRegion(second_generation);
    auto& growing_gpu=*growing.m_shared->owner;
    assert(second_generation.reply[0]==0 && grown_event.signals==2);
    assert(growing_gpu.reserves==2 && growing_gpu.releases==1);
    assert(growing_gpu.last_release_size==0x2000 &&
           growing_gpu.last_reserve_size==0x4000);
    assert(growing.system.gpu.waits==1 && growing.m_mappings.Count()==1);
    assert(growing.m_mappings.ContainsSparse(7,0x20000,0x4000));

    Service::AM::IGpuWorker blocked;
    Kernel::KEvent blocked_event{};
    setup(blocked,blocked_event);
    auto blocked_first=region();
    blocked.CreateSparseRegion(blocked_first);
    assert(blocked_first.reply[0]==0);
    assert(blocked.m_mappings.RecordSparse(7,1,0x23000,0x1000)==
           Service::AM::GW::LedgerStatus::Success);
    auto blocked_growth=region(1,3,0x4000);
    blocked.CreateSparseRegion(blocked_growth);
    auto& blocked_gpu=*blocked.m_shared->owner;
    assert(blocked_growth.reply[0]==Kernel::ResultInvalidState.raw);
    assert(blocked_gpu.reserves==1 && blocked_gpu.releases==0);
    assert(blocked.system.gpu.waits==0 && blocked_event.signals==1);
    assert(blocked.m_mappings.Count()==2);

    Service::AM::IGpuWorker rejected;
    Kernel::KEvent rejected_event{};
    setup(rejected,rejected_event);
    auto rejected_first=region();
    rejected.CreateSparseRegion(rejected_first);
    assert(rejected_first.reply[0]==0);
    rejected.m_shared->owner->reserve_result=Service::Nvidia::NvResult::InvalidState;
    auto rejected_growth=region(1,3,0x4000);
    rejected.CreateSparseRegion(rejected_growth);
    auto& rejected_gpu=*rejected.m_shared->owner;
    assert(rejected_growth.reply[0]==Kernel::ResultInvalidState.raw);
    assert(rejected_gpu.reserves==2 && rejected_gpu.releases==1);
    assert(rejected.system.gpu.waits==1 && rejected_event.signals==1);
    assert(rejected.m_mappings.Count()==0);

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
    assert(gpu.remaps==2 && gpu.last_handle==27);
    assert(event.signals==2 && worker.system.gpu.waits==2);
    assert(worker.m_mappings.Count()==1);

    // Mode-1 sparse VA has no private 214 backing: handle 0 must stay sparse/zero.
    auto sparse_unmap=batch(false);
    worker.ExecuteSparseMapRequests(sparse_unmap);
    assert(sparse_unmap.reply[0]==0 && sparse_unmap.reply[1]==1);
    assert(gpu.remaps==3 && gpu.last_handle==0 && gpu.last_source_pages==0);
    assert(event.signals==3 && worker.system.gpu.waits==3);

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
    assert(dense.m_mappings.Count()==1 && dense.m_dense_regions.size()==1 &&
           ready.signals==1);

    // Dense 214 VA owns backing handle 91. A guest 216 "unmap" must reveal
    // that backing again instead of publishing sparse zero pages.
    auto dense_unmap=batch(false);
    dense.ExecuteSparseMapRequests(dense_unmap);
    assert(dense_unmap.reply[0]==0 && dense_unmap.reply[1]==1);
    assert(dense.m_shared->owner->last_handle==91);
    assert(dense.m_shared->owner->last_source_pages==0);
    assert(dense.system.gpu.waits==1 && ready.signals==2);
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
                  "reserve=real ledger remap=real owner fail_closed=1 oom=rollback sparse_zero=1 dense_restore=1 output=exact",
                  flush=True)


# Execute the ACTUAL selected worker's failed dense-214 cleanup and NVDRV
# CloseSession guard; source-token checks alone cannot detect a GPU UAF.
# The fake AS models an OOM after a prefix of PTEs was installed. A poisoned
# guest GMMU must retain its NVMap owner, CPU page alias and session, whereas
# an ordinary pre-mutation OOM must release all resources on the same path.
dense_begin=source.index("Result IGpuWorker::BackGpuOnlyRegion(")
cleanup_begin=source.index("    if (!committed) {",dense_begin)
cleanup_end=source.index("    // Do not retain the preflight shared_ptr:",cleanup_begin)
selected_cleanup=source[cleanup_begin:cleanup_end]
destructor_begin=source.index("IGpuWorker::~IGpuWorker()")
close_begin=source.index("    if (m_nv_session && !m_quarantined_nv_session)",destructor_begin)
close_end=source.index("    // GpuWorkerSharedState owns",close_begin)
selected_close=source[close_begin:close_end]
assert "mapping_as->IsNativeSparsePoisoned()" in selected_cleanup
assert "m_quarantined_nv_session = true;" in selected_cleanup
assert "nvmap.FreeHandle(id, false);" in selected_cleanup
assert selected_cleanup.index("mapping_as->IsNativeSparsePoisoned()") < selected_cleanup.index(
    "nvmap.FreeHandle(id, false)")
fixture_poison=r"""
#include <cassert>
#include <cstdint>
#include <memory>
#include <optional>
#include <utility>
#define LOG_ERROR(...) ((void)0)
using u32=std::uint32_t;
using u64=std::uint64_t;
struct Result { u32 raw{}; constexpr bool IsError() const { return raw!=0; } };
inline constexpr Result ResultSuccess{};
namespace Kernel {
inline constexpr Result ResultInvalidState{4}, ResultOutOfResource{5};
enum class KMemoryState { IoMemory };
struct KernelCore {};
}
namespace Nvidia::NvCore { struct SessionId { std::size_t id{}; }; }
struct NativeAS {
    bool poisoned{};
    [[nodiscard]] bool IsNativeSparsePoisoned() const { return poisoned; }
};
struct Handle { u32 id{91}; };
struct Pages {
    int* destroyed{};
    int* closed{};
    explicit Pages(int* d,int* c):destroyed(d),closed(c){}
    ~Pages(){++*destroyed;}
    void Close(Kernel::KernelCore&){++*closed;}
};
struct NvMap {
    unsigned frees{};
    void FreeHandle(u32 id,bool internal) {
        assert(id==91 && !internal); ++frees;
    }
};
struct Table {
    bool unmap_fails{};
    unsigned unmaps{};
    Result UnmapPageGroup(u64 alias,Pages&,Kernel::KMemoryState) {
        assert(alias==0x4000); ++unmaps;
        return unmap_fails ? Result{9} : ResultSuccess;
    }
};
struct Container {
    unsigned closes{};
    void CloseSession(Nvidia::NvCore::SessionId id) {
        assert(id.id==33); ++closes;
    }
};
struct Module {
    Container c{};
    Container& GetContainer(){return c;}
};
struct Fixture {
    bool m_quarantined_nv_session{};
    std::optional<std::size_t> m_nv_session{33};
    std::shared_ptr<Module> m_module{std::make_shared<Module>()};
    std::shared_ptr<NativeAS> mapping_as{std::make_shared<NativeAS>()};
    std::shared_ptr<Handle> handle{std::make_shared<Handle>()};
    NvMap nvmap{};
    bool nvmap_oom{},committed{};
    int destroyed{},closed{};
    std::unique_ptr<Pages> pages{std::make_unique<Pages>(&destroyed,&closed)};
    Table table{};
    u64 alias{0x4000},address{0x20000},size{0x2000};
    u32 address_space{7};
    Kernel::KernelCore kernel{};
    Result ApplyCleanup() {
__SELECTED_CLEANUP__
        return ResultSuccess;
    }
    void CloseIfSafe() {
__SELECTED_CLOSE__
    }
};
int main() {
    // Emulate a partial GMMU write followed by page-table OOM. No physical
    // owner, CPU alias or final NvCore session may be released.
    {
        Fixture f{};
        f.mapping_as->poisoned=true;
        Pages* pending=f.pages.get();
        const Result result=f.ApplyCleanup();
        assert(result.raw==Kernel::ResultOutOfResource.raw && f.m_quarantined_nv_session);
        assert(f.nvmap.frees==0 && f.table.unmaps==0 && f.closed==0 && f.destroyed==0);
        assert(f.handle && !f.pages);
        f.CloseIfSafe();
        assert(f.m_module->GetContainer().closes==0);
        delete pending; // stand-in for later process and GMMU teardown
        assert(f.destroyed==1);
    }
    // Pre-mutation failure: do not quarantine or leak ordinary backing.
    {
        Fixture f{};
        assert(f.ApplyCleanup().raw==Kernel::ResultInvalidState.raw);
        assert(!f.handle && f.nvmap.frees==1 && f.table.unmaps==1 && f.closed==1);
        assert(!f.m_quarantined_nv_session && f.pages);
        f.CloseIfSafe();
        assert(f.m_module->GetContainer().closes==1);
    }
    // Native NvMap allocation OOM: guest sees out-of-resource and cleans up.
    {
        Fixture f{};
        f.nvmap_oom=true;
        assert(f.ApplyCleanup().raw==Kernel::ResultOutOfResource.raw);
        assert(f.nvmap.frees==1 && f.table.unmaps==1 && f.closed==1);
        f.CloseIfSafe();
        assert(f.m_module->GetContainer().closes==1);
    }
    // Failed CPU alias unmap must retain its KPageGroup, not close live pages.
    {
        Fixture f{};
        f.table.unmap_fails=true;
        Pages* pending=f.pages.get();
        assert(f.ApplyCleanup().raw==Kernel::ResultInvalidState.raw);
        assert(f.nvmap.frees==1 && f.table.unmaps==1 && f.closed==0 && !f.pages);
        f.CloseIfSafe();
        assert(f.m_module->GetContainer().closes==1);
        delete pending;
    }
    // Successful remap bypasses failure cleanup; normal session closes.
    {
        Fixture f{};
        f.committed=true;
        assert(f.ApplyCleanup().raw==0 && f.nvmap.frees==0 && f.table.unmaps==0);
        f.CloseIfSafe();
        assert(f.m_module->GetContainer().closes==1);
    }
}
"""
fixture_poison=fixture_poison.replace("__SELECTED_CLEANUP__",selected_cleanup).replace(
    "__SELECTED_CLOSE__",selected_close)
with tempfile.TemporaryDirectory(prefix="eden-h06-dense-poison-") as directory:
    cpp=Path(directory)/"selected_dense_cleanup.cpp"
    cpp.write_text(fixture_poison)
    for cc in compilers:
        for opt in ("-O0","-O2"):
            exe=Path(directory)/(Path(cc).name+opt)
            args=[cc,"-std=c++20",opt,"-Wall","-Wextra","-Werror",
                  "-fsanitize=undefined","-fno-sanitize-recover=all",
                  str(cpp),"-o",str(exe)]
            built=subprocess.run(args,capture_output=True,text=True,timeout=45,env=os.environ.copy())
            assert built.returncode==0,built.stderr[-6500:]
            done=subprocess.run([str(exe)],capture_output=True,text=True,timeout=25)
            assert done.returncode==0,done.stderr[-6500:]
            print("H06_REAL_DENSE_POISON_CLEANUP_PASS",Path(cc).name,opt,
                  "poison_retains=pages,handle,session",
                  "normal_oom=cleaned", "alias_unmap_fail=retained",
                  "success=untouched",flush=True)


# A guest GMMU can become poisoned by 215/216 AFTER a successful dense 214.
# Execute the ACTUAL selected destructor's address-space poison preflight so
# the kernel cannot silently retire a live NVMap backing on worker close.
worker_destructor=source.split("IGpuWorker::~IGpuWorker() {",1)[1].split(
    "Result IGpuWorker::BackGpuOnlyRegion(",1)[0]
teardown_begin=worker_destructor.index("    if (!m_quarantined_nv_session) {")
teardown_end=worker_destructor.index(
    "    if (!m_quarantined_nv_session)\n    for (const auto& [key, mapping]",
    teardown_begin)
teardown_guard=worker_destructor[teardown_begin:teardown_end]
assert "m_shared->address_spaces.OwnedIds()" in teardown_guard
assert "m_shared->FindOwnedAddressSpace(*id)" in teardown_guard
assert "as->IsNativeSparsePoisoned()" in teardown_guard
for condition in (
    "if (!m_quarantined_nv_session)\n    for (const auto& [key, mapping]",
    "if (!m_quarantined_nv_session)\n    for (const u32 memory_id",
    "if (!m_quarantined_nv_session)\n    while (!m_dense_regions.empty())",
    "if (!m_quarantined_nv_session)\n    for (const u32 id : m_memory)",
    "if (m_nv_session && !m_quarantined_nv_session)",
):
    assert condition in worker_destructor,condition
teardown_fixture=r"""
#include <cassert>
#include <memory>
#include <mutex>
#include <optional>
#include <vector>
#define LOG_ERROR(...) ((void)0)
namespace Nvidia::Devices {
struct nvhost_as_gpu {
    bool poisoned{};
    [[nodiscard]] bool IsNativeSparsePoisoned() const {return poisoned;}
};
}
struct SpaceSlots {
    std::vector<std::optional<unsigned>> slots{std::optional<unsigned>{7}};
    auto OwnedIds() const {return slots;}
};
struct Shared {
    std::mutex mutex{};
    SpaceSlots address_spaces{};
    std::shared_ptr<Nvidia::Devices::nvhost_as_gpu> active=
        std::make_shared<Nvidia::Devices::nvhost_as_gpu>();
    auto FindOwnedAddressSpace(unsigned id) {
        return id==7 ? active : std::shared_ptr<Nvidia::Devices::nvhost_as_gpu>{};
    }
};
struct Worker {
    bool m_quarantined_nv_session{};
    std::shared_ptr<Shared> m_shared=std::make_shared<Shared>();
    unsigned backing_retires{},session_closes{};
    void Close() {
__EXACT_DESTRUCTOR_POISON_GUARD__
        // Existing teardown stage guards are separately tied to the
        // extracted selected source. These counters represent the real
        // FreeHandle/CloseSession actions whose guards were reviewed above.
    if (!m_quarantined_nv_session) ++backing_retires;
    if (!m_quarantined_nv_session) ++session_closes;
    }
};
int main() {
    Worker unpoisoned{};
    unpoisoned.Close();
    assert(!unpoisoned.m_quarantined_nv_session);
    assert(unpoisoned.backing_retires==1 && unpoisoned.session_closes==1);

    Worker poisoned{};
    poisoned.m_shared->active->poisoned=true;
    poisoned.Close();
    assert(poisoned.m_quarantined_nv_session);
    assert(poisoned.backing_retires==0 && poisoned.session_closes==0);

    Worker retained{};
    retained.m_quarantined_nv_session=true;
    retained.Close();
    assert(retained.backing_retires==0 && retained.session_closes==0);

    Worker no_as{};
    no_as.m_shared->address_spaces.slots.clear();
    no_as.Close();
    assert(no_as.backing_retires==1 && no_as.session_closes==1);

    Worker missing_fd{};
    missing_fd.m_shared->address_spaces.slots={std::nullopt};
    missing_fd.Close();
    assert(missing_fd.backing_retires==1 && missing_fd.session_closes==1);
}
""".replace("__EXACT_DESTRUCTOR_POISON_GUARD__",teardown_guard)
with tempfile.TemporaryDirectory(prefix="eden-h06-poisoned-teardown-") as directory:
    cpp=Path(directory)/"poisoned_worker_close.cpp";cpp.write_text(teardown_fixture)
    for cc in compilers:
        for opt in ("-O0","-O2"):
            exe=Path(directory)/(Path(cc).name+opt)
            built=subprocess.run(
                [cc,"-std=c++20",opt,"-Wall","-Wextra","-Werror",
                 "-fsanitize=undefined","-fno-sanitize-recover=all",str(cpp),"-o",str(exe)],
                capture_output=True,text=True,timeout=45,env=os.environ.copy())
            assert built.returncode==0,built.stderr[-6500:]
            done=subprocess.run([str(exe)],capture_output=True,text=True,timeout=25)
            assert done.returncode==0,done.stderr[-6500:]
            print("H06_REAL_POISONED_215_216_TEARDOWN_PASS",Path(cc).name,opt,
                  "preflight=real_cpp", "poison=quarantine",
                  "normal=cleanup", "stale_fd=skipped",flush=True)
