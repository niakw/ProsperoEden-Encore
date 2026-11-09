#!/usr/bin/env python3
"""H03: execute the real GPU-only backing owner NVMap failure rollback.

Extracts the maintained allocation/remap/CPU-alias rollback block unchanged.
Clang/GCC UBSan run host-injected OOM before and after NVMap handle creation,
success/failure remap, and failed alias-unmap preservation. No PS5 claim.
"""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[2]
source=(ROOT/"vendor/encore-active/ns2-runtime/gpu_session/core/hle/service/am/service/gpu_worker.cpp").read_text()
a="Result IGpuWorker::BackGpuOnlyRegion("
b="bool IGpuWorker::RetireGpuOnlyRegion("
assert source.count(a)==source.count(b)==1
method=a+source.split(a,1)[1].split(b,1)[0]
start="    auto& nvmap = m_module->GetContainer().GetNvMapFile();"
end="    // Do not retain the preflight shared_ptr:"
assert method.count(start)==method.count(end)==1
owner=start+method.split(start,1)[1].split(end,1)[0]
assert "nvmap.CreateHandle(size, handle)" in owner
assert "handle->Alloc(" in owner and "catch (const std::bad_alloc&)" in owner
assert "nvmap_oom = true;" in owner
assert owner.index("catch (const std::bad_alloc&)") < owner.index("bool committed = false;")
assert owner.index("nvmap.FreeHandle(id, false)") < owner.index("table.UnmapPageGroup(")
assert "return nvmap_oom ? Kernel::ResultOutOfResource : Kernel::ResultInvalidState;" in owner

harness=r"""
#include <cassert>
#include <cstdint>
#include <memory>
#include <new>
#include <optional>
#include <span>
#include <initializer_list>
using u8=std::uint8_t;
using u32=std::uint32_t;
using u64=std::uint64_t;
struct Result {int raw{};bool IsError() const {return raw!=0;}};
inline constexpr Result ResultSuccess{0};
namespace Kernel {
enum class KMemoryState {IoMemory};
inline constexpr Result ResultOutOfResource{1},ResultInvalidState{2};
inline constexpr u32 PageSize=4096;
}
struct CoreKernel {};
struct Pages {
    static inline unsigned closed{};
    void Close(CoreKernel&) {++closed;}
};
struct PageTable {
    bool fail_unmap{};
    unsigned unmaps{};
    Result UnmapPageGroup(u64,Pages&,Kernel::KMemoryState) {
        ++unmaps;
        return fail_unmap ? Kernel::ResultInvalidState : ResultSuccess;
    }
};
u64 GetInteger(u64 v){return v;}
namespace Nvidia {
enum class NvResult {Success,InvalidState,InsufficientMemory};
namespace NvCore {
struct SessionId {u32 id{};};
namespace NvMap {
struct Handle {
    u32 id{43};
    bool oom_alloc{},fail_alloc{};
    NvResult Alloc(std::initializer_list<int>,u32,u32,u64,SessionId session) {
        assert(session.id==12);
        if (oom_alloc)throw std::bad_alloc{};
        return fail_alloc ? NvResult::InvalidState : NvResult::Success;
    }
};
}
}
namespace Devices {
struct NativeSparseRemapEntry {
    u32 flags{},handle{};
    u64 destination_pages{},pages{};
};
struct AddressSpace {
    bool fail_remap{};
    unsigned calls{};
    NvResult RemapNativeSparse(std::span<const NativeSparseRemapEntry> entries) {
        assert(entries.size()==1 && entries.front().handle==43);
        ++calls;
        return fail_remap ? NvResult::InvalidState : NvResult::Success;
    }
};
}
struct NvMapFile {
    bool create_oom{},create_fail{},alloc_oom{},alloc_fail{};
    unsigned created{},freed{};
    NvResult CreateHandle(u64 size,std::shared_ptr<NvCore::NvMap::Handle>& out) {
        assert(size==4096);
        ++created;
        if(create_oom)throw std::bad_alloc{};
        if(create_fail)return NvResult::InvalidState;
        out=std::make_shared<NvCore::NvMap::Handle>();
        out->oom_alloc=alloc_oom;
        out->fail_alloc=alloc_fail;
        return NvResult::Success;
    }
    void FreeHandle(u32 id,bool should) {
        assert(id==43 && !should);
        ++freed;
    }
};
struct Container {
    NvMapFile file{};
    NvMapFile& GetNvMapFile(){return file;}
};
struct Module {
    Container container{};
    Container& GetContainer(){return container;}
};
}
struct Shared {
    std::shared_ptr<Nvidia::Devices::AddressSpace> as{
        std::make_shared<Nvidia::Devices::AddressSpace>()};
    auto FindOwnedAddressSpace(u32 id) {assert(id==7);return as;}
};
#define LOG_ERROR(...) ((void)0)
struct Worker {
    CoreKernel kernel{};
    PageTable table{};
    Nvidia::Module module{};
    Nvidia::Module* m_module{&module};
    Shared shared{};
    Shared* m_shared{&shared};
    std::optional<u32> m_nv_session{12};
    std::unique_ptr<Pages> pages{std::make_unique<Pages>()};
    u64 alias{0x1000},size{4096},address{0x6000};
    u8 page_shift{12};
    u32 address_space{7};
    Result Run(){
__REAL_OWNER__
        return ResultSuccess;
    }
};
int main(){
    {
        Worker w;
        w.module.container.file.create_oom=true;
        const auto prev=Pages::closed;
        assert(w.Run().raw==Kernel::ResultOutOfResource.raw);
        assert(w.table.unmaps==1 && Pages::closed==prev+1);
        assert(w.module.container.file.freed==0 && w.shared.as->calls==0);
    }
    {
        Worker w;
        w.module.container.file.alloc_oom=true;
        const auto prev=Pages::closed;
        assert(w.Run().raw==Kernel::ResultOutOfResource.raw);
        assert(w.table.unmaps==1 && Pages::closed==prev+1);
        assert(w.module.container.file.freed==1 && w.shared.as->calls==0);
    }
    {
        Worker w;
        w.module.container.file.alloc_fail=true;
        const auto prev=Pages::closed;
        assert(w.Run().raw==Kernel::ResultInvalidState.raw);
        assert(w.table.unmaps==1 && Pages::closed==prev+1);
        assert(w.module.container.file.freed==1);
    }
    {
        Worker w;
        w.shared.as->fail_remap=true;
        const auto prev=Pages::closed;
        assert(w.Run().raw==Kernel::ResultInvalidState.raw);
        assert(w.table.unmaps==1 && Pages::closed==prev+1);
        assert(w.module.container.file.freed==1);
    }
    {
        Worker w;
        const auto prev=Pages::closed;
        assert(w.Run().raw==0);
        assert(w.table.unmaps==0 && Pages::closed==prev);
        assert(w.module.container.file.freed==0 && w.shared.as->calls==1);
    }
    {
        Worker w;
        w.module.container.file.alloc_oom=true;
        w.table.fail_unmap=true;
        const auto prev=Pages::closed;
        Pages* preserved=w.pages.get();
        assert(w.Run().raw==Kernel::ResultOutOfResource.raw);
        assert(w.table.unmaps==1 && Pages::closed==prev && !w.pages);
        assert(w.module.container.file.freed==1);
        delete preserved; // fixture reclaims simulated still-mapped backing
    }
}
""".replace("__REAL_OWNER__",owner)
compilers=list(dict.fromkeys(x for x in (shutil.which("clang++"),shutil.which("g++")) if x))
assert compilers,"C++20 compiler required"
with tempfile.TemporaryDirectory(prefix="encore-h03-nvmap-rollback-") as work:
    cpp=Path(work)/"owner.cpp";cpp.write_text(harness)
    for cc in compilers:
        for opt in ("-O0","-O2"):
            exe=Path(work)/(Path(cc).name+opt)
            cmd=[cc,"-std=c++20",opt,"-Wall","-Wextra","-Werror",
                 "-fsanitize=undefined","-fno-sanitize-recover=all",
                 str(cpp),"-o",str(exe)]
            built=subprocess.run(cmd,capture_output=True,text=True,timeout=70,
                                 env=os.environ.copy())
            assert built.returncode==0,built.stderr[-5500:]
            run=subprocess.run([str(exe)],capture_output=True,text=True,timeout=25)
            assert run.returncode==0,run.stderr[-5500:]
            print("H03_NATIVE_NVMAP_ROLLBACK_OWNER_PASS",Path(cc).name,opt,
                  "create_oom=rollback alloc_oom=rollback"
                  " failed_remap=rollback guest_alias_preserved_if_unmap_fails",flush=True)
