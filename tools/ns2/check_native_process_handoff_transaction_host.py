#!/usr/bin/env python3
"""H01: execute the maintained Process::Initialize C++ owner, not a copied stub.

Reject a failed KProcess allocation and a loader returning Success with
missing NPDM-derived parameters before publishing a process. This covers the
transaction boundary only, not complete ExeFS/NSO/NPDM admission.
"""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
VENDOR = ROOT / "vendor"
PATH = VENDOR / "encore-active/ns2-runtime/process/core/hle/service/os/process.cpp"
source = PATH.read_text()
begin = "bool Process::Initialize(Loader::AppLoader& loader, Loader::ResultStatus& out_load_result) {"
end = "\nvoid Process::Finalize() {"
assert source.count(begin) == source.count(end) == 1
method = begin + source.split(begin, 1)[1].split(end, 1)[0]
assert method.index("if (!process)") < method.index("KProcess::Register(")
register_after_load = method.index("KProcess::Register(") > method.index("if (!load_parameters)")
if register_after_load:
    assert method.index("KProcess::Register(") < method.index("AppendNewProcess(")
else:
    assert method.index("KProcess::Register(") < method.index("loader.Load(*process, m_system)")
failed_register_count = 0 if register_after_load else 1
assert method.index("if (!load_parameters)") < method.index("AppendNewProcess(")
assert "out_load_result = Loader::ResultStatus::ErrorNotInitialized;" in method
assert "out_load_result = Loader::ResultStatus::ErrorUnableToParseKernelMetadata;" in method
assert "SCOPE_EXIT {" in method
assert "SvcTrace::Unregister(pid);" in method
rollback = method.split("if (!process_committed) {", 1)[1].split(
    "SvcTrace::Unregister(pid);", 1)[0]
assert "m_system.GetFileSystemController().UnregisterProcessIfPresent(pid);" in rollback
assert "if (Eden::NS2::SvcTrace::active_pid.load" not in rollback
assert "m_system.GetFileSystemController().UnregisterProcessIfPresent(pid);" in method
assert method.index("SvcTrace::Unregister(pid);") < method.index("m_process->Open(")
assert "process_committed = true;" in method
finalize="void Process::Finalize() {"+source.split("void Process::Finalize() {",1)[1].split("\nbool Process::Run()",1)[0]
assert finalize.index("UnregisterProcessIfPresent") < finalize.index(
    "if (Eden::NS2::SvcTrace::active_pid.load")
assert finalize.index("SvcTrace::Unregister(pid);") < finalize.index("m_process->Close(")
assert "UnregisterProcessIfPresent(pid);" in finalize

harness = r"""
#include <cassert>
#include <atomic>
#include <cstddef>
#include <cstdint>
#include <new>
#include <optional>
#include <utility>
#include <stdexcept>
#include "common/scope_exit.h"

namespace Kernel {
struct KProcess;
struct KernelCore {
    bool fail_create{}, fail_append{};
    int creates{}, registers{}, closes{}, opens{}, appends{}, removes{};
    KProcess* latest{};
    void AppendNewProcess(KProcess* p);
    void RemoveProcess(KProcess* p);
};
struct KProcess {
    KernelCore* owner{};
    explicit KProcess(KernelCore* k) : owner{k} {}
    static KProcess* Create(KernelCore& kernel) {
        if (kernel.fail_create) return nullptr;
        ++kernel.creates;
        return kernel.latest = new KProcess(&kernel);
    }
    static void Register(KernelCore& k, KProcess* process) {
        assert(process && process->owner == &k);
        ++k.registers;
    }
    std::uint64_t GetProcessId() const { return 81; }
    void Close(KernelCore& k) { assert(owner == &k); ++k.closes; }
    void Open(KernelCore& k) { assert(owner == &k); ++k.opens; }
};
inline void KernelCore::AppendNewProcess(KProcess* p) {
    assert(p && p->owner == this);
    if(fail_append)throw std::bad_alloc{};
    ++appends;
}
inline void KernelCore::RemoveProcess(KProcess* p) {
    assert(p && p->owner == this);
    ++removes;
}
}
namespace Eden::NS2 {
struct SvcTrace {
    static inline std::atomic<std::uint64_t> active_pid{};
    static inline unsigned registered{}, unregistered{};
    static void Register(std::uint64_t pid){ active_pid=pid; ++registered; }
    static void Unregister(std::uint64_t pid){
        if(active_pid==pid){ active_pid=0; ++unregistered; }
    }
};
}
namespace Core {
struct FakeFilesystem {
    unsigned unregister_calls{};
    std::optional<std::uint64_t> registered_pid{};
    void RegisterProcess(std::uint64_t pid) {
        assert(pid==81 && !registered_pid);
        registered_pid=pid;
    }
    void UnregisterProcessIfPresent(std::uint64_t pid){
        assert(pid==81);
        ++unregister_calls;
        if (registered_pid==pid) registered_pid.reset();
    }
};
struct System {
    Kernel::KernelCore& kernel;
    FakeFilesystem filesystem;
    Kernel::KernelCore& Kernel() { return kernel; }
    FakeFilesystem& GetFileSystemController(){return filesystem;}
};
}
namespace Loader {
enum class ResultStatus {
    Success, ErrorNotInitialized, ErrorUnableToParseKernelMetadata, ErrorLoadingNSO
};
struct LoadParameters {
    int main_thread_priority{};
    std::size_t main_thread_stack_size{};
};
struct AppLoader {
    ResultStatus status{};
    std::optional<LoadParameters> parameters{};
    bool trace_register{}, throw_after_trace{}, register_romfs{};
    std::pair<ResultStatus, std::optional<LoadParameters>>
    Load(Kernel::KProcess& p, Core::System& system) {
        assert(p.owner);
        // The real ExeFS loader installs RomFS before trace publication.
        if(register_romfs) system.filesystem.RegisterProcess(p.GetProcessId());
        if(trace_register) Eden::NS2::SvcTrace::Register(p.GetProcessId());
        if(throw_after_trace)throw std::bad_alloc{};
        return {status, parameters};
    }
};
}
namespace Service {
struct Process {
    Core::System& m_system;
    Kernel::KProcess* m_process{};
    int m_main_thread_priority{};
    std::size_t m_main_thread_stack_size{};
    bool m_process_started{};
    void Terminate() {}
    void Finalize();
    bool Initialize(Loader::AppLoader&, Loader::ResultStatus&);
};
#define EDEN_NS2_PROCESS_RUN_GUARD 1
__REAL_OWNER__
__REAL_FINALIZE__
}
static void dispose(Kernel::KernelCore& k) {
    delete k.latest;
    k.latest = nullptr;
    Eden::NS2::SvcTrace::active_pid=0;
    Eden::NS2::SvcTrace::registered=0;
    Eden::NS2::SvcTrace::unregistered=0;
}
int main() {
    {
        Kernel::KernelCore k; k.fail_create = true;
        Core::System system{k,{}};
        Service::Process process{system};
        Loader::AppLoader loader{Loader::ResultStatus::Success, Loader::LoadParameters{4, 8192}};
        auto result = Loader::ResultStatus::Success;
        assert(!process.Initialize(loader, result));
        assert(result == Loader::ResultStatus::ErrorNotInitialized);
        assert(k.creates == 0 && k.registers == 0 && k.appends == 0);
        assert(k.closes == 0 && k.opens == 0 && !process.m_process);
    }
    {
        Kernel::KernelCore k;
        Core::System system{k,{}};
        Service::Process process{system};
        Loader::AppLoader loader{Loader::ResultStatus::ErrorLoadingNSO, std::nullopt,true};
        auto result = Loader::ResultStatus::Success;
        assert(!process.Initialize(loader, result));
        assert(result == Loader::ResultStatus::ErrorLoadingNSO);
        assert(k.registers == __FAILED_REGISTER_COUNT__ && k.closes == 1 && k.appends == 0);
        assert(k.opens == 0 && !process.m_process);
        assert(Eden::NS2::SvcTrace::active_pid==0 && Eden::NS2::SvcTrace::unregistered==1);
        dispose(k);
    }
    {
        Kernel::KernelCore k;
        Core::System system{k,{}};
        Service::Process process{system};
        Loader::AppLoader loader{Loader::ResultStatus::Success, std::nullopt,true};
        auto result = Loader::ResultStatus::Success;
        assert(!process.Initialize(loader, result));
        assert(result == Loader::ResultStatus::ErrorUnableToParseKernelMetadata);
        assert(k.registers == __FAILED_REGISTER_COUNT__ && k.closes == 1 && k.appends == 0);
        assert(k.opens == 0 && !process.m_process);
        assert(Eden::NS2::SvcTrace::active_pid==0 && Eden::NS2::SvcTrace::unregistered==1);
        dispose(k);
    }
    {
        // Negative H01: RomFS registered, no SVC trace yet. Even a malformed
        // ExeFS load must drop its process-owned filesystem registration.
        Kernel::KernelCore k;
        Core::System system{k,{}};
        Service::Process process{system};
        Loader::AppLoader loader{Loader::ResultStatus::ErrorLoadingNSO,
                                 std::nullopt,false,false,true};
        auto result=Loader::ResultStatus::Success;
        assert(!process.Initialize(loader,result));
        assert(result==Loader::ResultStatus::ErrorLoadingNSO &&
               !system.filesystem.registered_pid &&
               system.filesystem.unregister_calls==1 &&
               Eden::NS2::SvcTrace::active_pid==0);
        assert(k.registers==__FAILED_REGISTER_COUNT__ && k.closes==1 && k.appends==0 && k.opens==0);
        dispose(k);
    }
    {
        // A Success code without NPDM parameters must take the same path.
        Kernel::KernelCore k;
        Core::System system{k,{}};
        Service::Process process{system};
        Loader::AppLoader loader{Loader::ResultStatus::Success,
                                 std::nullopt,false,false,true};
        auto result=Loader::ResultStatus::Success;
        assert(!process.Initialize(loader,result));
        assert(result==Loader::ResultStatus::ErrorUnableToParseKernelMetadata &&
               !system.filesystem.registered_pid &&
               system.filesystem.unregister_calls==1 &&
               Eden::NS2::SvcTrace::active_pid==0);
        assert(k.registers==__FAILED_REGISTER_COUNT__ && k.closes==1 && k.appends==0 && k.opens==0);
        dispose(k);
    }
    {
        Kernel::KernelCore k; k.fail_append=true;
        Core::System system{k,{}};
        Service::Process process{system};
        Loader::AppLoader loader{Loader::ResultStatus::Success,Loader::LoadParameters{1,4096},true};
        auto result=Loader::ResultStatus::Success;
        bool failed=false;
        try { (void)process.Initialize(loader,result); }
        catch(const std::bad_alloc&){failed=true;}
        assert(failed && k.registers==1 && k.closes==1 && k.opens==0 && k.appends==0);
        assert(!process.m_process && Eden::NS2::SvcTrace::active_pid==0);
        assert(Eden::NS2::SvcTrace::unregistered==1);
        dispose(k);
    }
    {
        Kernel::KernelCore k;
        Core::System system{k,{}};
        Service::Process process{system};
        Loader::AppLoader loader{Loader::ResultStatus::Success, Loader::LoadParameters{42, 0x8000},true};
        auto result = Loader::ResultStatus::ErrorLoadingNSO;
        assert(process.Initialize(loader, result));
        assert(result == Loader::ResultStatus::Success);
        assert(k.registers == 1 && k.closes == 1 && k.appends == 1 && k.opens == 1);
        assert(process.m_process == k.latest && process.m_main_thread_priority == 42);
        assert(process.m_main_thread_stack_size == 0x8000 && !process.m_process_started);
        assert(Eden::NS2::SvcTrace::active_pid==81 && Eden::NS2::SvcTrace::unregistered==0);
        dispose(k);
    }
    {
        // H01: normal teardown retires both RomFS record and SVC trace.
        Kernel::KernelCore k;
        Core::System system{k,{}};
        Service::Process process{system};
        Loader::AppLoader loader{Loader::ResultStatus::Success,
                                 Loader::LoadParameters{42,8192},true,false,true};
        auto result=Loader::ResultStatus::ErrorLoadingNSO;
        assert(process.Initialize(loader,result));
        assert(system.filesystem.registered_pid==81);
        process.Finalize();
        assert(!system.filesystem.registered_pid && system.filesystem.unregister_calls==1);
        assert(Eden::NS2::SvcTrace::active_pid==0 && Eden::NS2::SvcTrace::unregistered==1);
        assert(k.removes==1 && k.closes==2 && k.opens==1 && !process.m_process);
        dispose(k);
    }
    {
        // H01: a newer SVC trace must survive teardown of the older PID.
        Kernel::KernelCore k;
        Core::System system{k,{}};
        Service::Process process{system};
        Loader::AppLoader loader{Loader::ResultStatus::Success,
                                 Loader::LoadParameters{42,8192},true,false,true};
        auto result=Loader::ResultStatus::ErrorLoadingNSO;
        assert(process.Initialize(loader,result));
        Eden::NS2::SvcTrace::active_pid=777;
        process.Finalize();
        assert(!system.filesystem.registered_pid && system.filesystem.unregister_calls==1);
        assert(Eden::NS2::SvcTrace::active_pid==777 && Eden::NS2::SvcTrace::unregistered==0);
        assert(k.removes==1 && k.closes==2 && !process.m_process);
        dispose(k);
    }
}
""".replace("__REAL_OWNER__", method).replace("__REAL_FINALIZE__", finalize)

compilers = list(dict.fromkeys(
    compiler for compiler in (shutil.which("clang++"), shutil.which("g++")) if compiler
))
assert compilers, "C++20 compiler required"
with tempfile.TemporaryDirectory(prefix="eden-h01-process-owner-") as temp:
    source_file = Path(temp) / "process_owner.cpp"
    source_file.write_text(harness.replace("__FAILED_REGISTER_COUNT__", str(failed_register_count)))
    for compiler in compilers:
        for opt in ("-O0", "-O2"):
            exe = Path(temp) / (Path(compiler).name + opt)
            args = [compiler, "-std=c++20", opt, "-Wall", "-Wextra", "-Werror",
                    "-fsanitize=undefined", "-fno-sanitize-recover=all",
                    "-I" + str(VENDOR / "sources/eden/src"),
                    str(source_file), "-o", str(exe)]
            build = subprocess.run(args, capture_output=True, text=True,
                                   timeout=55, env=os.environ.copy())
            assert build.returncode == 0, build.stderr[-4000:]
            run = subprocess.run([str(exe)], capture_output=True, text=True, timeout=20)
            assert run.returncode == 0, run.stderr[-4000:]
            print("H01_PROCESS_OWNER_HANDOFF_PASS", Path(compiler).name, opt,
                  "null_allocation=refused absent_npdm=refused"
                  " malformed_load=refused trace_rollback=1 append_oom_rollback=1"
                  " valid_process=published romfs_pretrace_rollback=1 finalization_romfs_cleanup=1 preserve_foreign_trace=1"
                  " ns1_macro_isolated=1", flush=True)
