#!/usr/bin/env python3
"""H03: execute native worker OpenSession OOM guards with real CPU-alias rollback.

Both native BackGpuOnlyRegion and RegisterMemory owners supply the source
bodies; mock injected NVDRV OOM cannot leave a dangling mapped alias or a
published GPU memory handle. Host proof only, no PS5 execution.
"""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[2]
source=(ROOT/"vendor/encore-active/ns2-runtime/gpu_session/core/hle/service/am/service/gpu_worker.cpp").read_text()
sparse=source.split("Result IGpuWorker::BackGpuOnlyRegion(",1)[1].split(
    "bool IGpuWorker::RetireGpuOnlyRegion(",1)[0]
registered=source.split("Result IGpuWorker::RegisterMemory(",1)[1].split(
    "Result IGpuWorker::ReleaseMemory(",1)[0]
def stage(src,begin,end):
    assert src.count(begin)==src.count(end)==1,(begin,end)
    return begin+src.split(begin,1)[1].split(end,1)[0]
a=stage(sparse,"    // Native sparse pages already have a CPU alias at this point.","    auto& nvmap =")
b=stage(registered,"    // A session allocation failure happens before any NVMap handle","    auto& nvmap =")
assert a.index("table.UnmapPageGroup(") < a.index("pages->Close(kernel)")
assert "pages.release()" in a and "return undone;" in a
assert "catch (const std::bad_alloc&)" in a and "catch (const std::bad_alloc&)" in b
assert "return Kernel::ResultOutOfResource;" in a and "return Kernel::ResultOutOfResource;" in b
harness=r"""
#include <cassert>
#include <cstdint>
#include <memory>
#include <new>
#include <optional>
struct Result {
    int raw{};
    bool IsError() const { return raw!=0; }
};
inline constexpr Result ResultSuccess{0};
namespace Kernel {
inline constexpr Result ResultOutOfResource{1}, ResultInvalidState{2};
enum class KMemoryState { IoMemory };
}
struct CoreKernel {};
struct Pages {
    static inline int closed{},destroyed{};
    void Close(CoreKernel&) { ++closed; }
    ~Pages(){ ++destroyed; }
};
struct PageTable {
    bool fail_unmap{};
    unsigned unmap_calls{};
    Result UnmapPageGroup(unsigned,Pages&,Kernel::KMemoryState state) {
        assert(state==Kernel::KMemoryState::IoMemory);
        ++unmap_calls;
        return fail_unmap ? Kernel::ResultInvalidState : ResultSuccess;
    }
};
struct Container {
    bool fail_open{};
    unsigned calls{};
    struct Session {unsigned id;};
    Session OpenSession(void* process) {
        assert(process);
        ++calls;
        if(fail_open)throw std::bad_alloc{};
        return {37};
    }
};
struct Module {
    Container container{};
    Container& GetContainer(){return container;}
};
#define LOG_ERROR(...) ((void)0)
struct Worker {
    CoreKernel kernel{};
    PageTable table{};
    Module module{};
    Module* m_module{&module};
    void* m_process{this};
    std::optional<unsigned> m_nv_session{};
    std::unique_ptr<Pages> pages{std::make_unique<Pages>()};
    unsigned alias{0x1000};
    Result Sparse(){
__SPARSE__
        return ResultSuccess;
    }
    Result Register(){
__REGISTER__
        return ResultSuccess;
    }
};
int main(){
    {
        Worker worker;
        worker.module.container.fail_open=true;
        const auto result=worker.Sparse();
        assert(result.raw==Kernel::ResultOutOfResource.raw);
        assert(worker.table.unmap_calls==1 && Pages::closed==1);
        assert(!worker.m_nv_session && !worker.pages);
    }
    {
        Worker worker;
        worker.module.container.fail_open=true;
        worker.table.fail_unmap=true;
        Pages* held=worker.pages.get();
        auto result=worker.Sparse();
        assert(result.raw==Kernel::ResultInvalidState.raw);
        assert(worker.table.unmap_calls==1 && !worker.pages);
        assert(Pages::closed==1); // do NOT free a still-mapped alias
        delete held; // fixture reclaims simulated kernel-owned object
    }
    {
        Worker worker;
        worker.module.container.fail_open=true;
        auto result=worker.Register();
        assert(result.raw==Kernel::ResultOutOfResource.raw);
        assert(worker.module.container.calls==1 && !worker.m_nv_session);
    }
    {
        Worker worker;
        assert(worker.Register().raw==0 && worker.m_nv_session==37);
        assert(worker.Register().raw==0 && worker.module.container.calls==1);
    }
    {
        Worker worker;
        assert(worker.Sparse().raw==0 && worker.m_nv_session==37);
        assert(worker.Sparse().raw==0 && worker.module.container.calls==1);
        assert(worker.table.unmap_calls==0);
    }
}
""".replace("__SPARSE__",a).replace("__REGISTER__",b)
compilers=list(dict.fromkeys(x for x in (shutil.which("clang++"),shutil.which("g++")) if x))
assert compilers,"Clang/GCC required"
with tempfile.TemporaryDirectory(prefix="encore-h03-session-oom-") as temp:
    code=Path(temp)/"owner.cpp";code.write_text(harness)
    for cc in compilers:
        for opt in ("-O0","-O2"):
            exe=Path(temp)/(Path(cc).name+opt)
            argv=[cc,"-std=c++20",opt,"-Wall","-Wextra","-Werror",
                  "-fsanitize=undefined","-fno-sanitize-recover=all",
                  str(code),"-o",str(exe)]
            built=subprocess.run(argv,capture_output=True,text=True,timeout=60,env=os.environ.copy())
            assert built.returncode==0,built.stderr[-4500:]
            run=subprocess.run([str(exe)],capture_output=True,text=True,timeout=25)
            assert run.returncode==0,run.stderr[-4500:]
            print("H03_REAL_WORKER_SESSION_OOM_PASS",Path(cc).name,opt,
                  "alias_rollback=1 unresolved_alias_retained=1"
                  " register_no_lock=1 existing_session_reused=1",flush=True)
