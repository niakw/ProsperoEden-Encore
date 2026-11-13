#!/usr/bin/env python3
"""H01 joined maintained owner witness: real KProcess metadata, Initialize,
LoadModule, Process::Initialize and Process::Finalize in one transaction.

Cross-built public HOS NPDM/NSO fixture; host kernel/page table and FS stubs.
This is not native PS5 process execution or a game boot.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import os
import shutil
import subprocess
import tempfile
import test_real_kprocess_init_guest_rollback as k

ROOT=Path(__file__).resolve().parents[2]
P=ROOT/"vendor/encore-active/ns2-runtime/process/core/hle/service/os/process.cpp"
source=P.read_text()
def extract(begin:str,end:str)->str:
    assert source.count(begin)==source.count(end)==1,(begin,end)
    return begin+source.split(begin,1)[1].split(end,1)[0]
init=extract("bool Process::Initialize(Loader::AppLoader& loader, Loader::ResultStatus& out_load_result) {",
             "\nvoid Process::Finalize() {")
finalize=extract("void Process::Finalize() {","\nbool Process::Run() {")
assert "UnregisterProcessIfPresent(pid);" in init and "UnregisterProcessIfPresent(pid);" in finalize
register_after_load = init.index("Kernel::KProcess::Register(") > init.index("if (!load_parameters)")
assert (register_after_load or init.index("Kernel::KProcess::Register(") <
        init.index("loader.Load(*process, m_system)"))

def sub(original:str,old:str,new:str)->str:
    assert original.count(old)==1,(old,original.count(old))
    return original.replace(old,new)

prefix=k.PREFIX
prefix=sub(prefix,"#include <algorithm>","#include <algorithm>\n#include <atomic>\n#include <new>\n#include <optional>\n#include <memory>")
prefix=sub(prefix,"#define SCOPE_EXIT auto ns2_scope_exit_guard_ = HostScopeMaker{} + [&]()",
"""#define H01_JOIN2(a,b) a##b
#define H01_JOIN(a,b) H01_JOIN2(a,b)
#define SCOPE_EXIT auto H01_JOIN(ns2_scope_exit_guard_,__COUNTER__) = HostScopeMaker{} + [&]()""")
prefix=sub(prefix,"struct KernelCore {\n    DummySystem sys;","""struct KProcess;
struct KernelCore {
    KProcess* latest{};
    unsigned creations{},registrations{},appends{},removes{},releases{};
    bool fail_append{};
    void AppendNewProcess(KProcess*);
    void RemoveProcess(KProcess*);
    DummySystem sys;""")
prefix=sub(prefix,"struct KProcess {\n    bool m_is_application=false;","""struct KProcess {
    unsigned refs{1};
    bool released{};
    static KProcess* Create(KernelCore&);
    static void Register(KernelCore&,KProcess*);
    void Close(KernelCore&);
    void Open(KernelCore&){++refs;}
    void Terminate(KernelCore&){}
    u64 GetProcessId()const{return m_process_id;}
    bool m_is_application=false;""")

kernel_methods=r"""
inline KProcess* KProcess::Create(KernelCore& kernel) {
    auto* result=new KProcess;
    kernel.latest=result;++kernel.creations;
    return result;
}
inline void KProcess::Register(KernelCore& kernel,KProcess* p){
    assert(p && !p->released);++kernel.registrations;
}
inline void KProcess::Close(KernelCore& kernel){
    assert(refs>0);
    if(--refs==0){
        if(m_page_table.mapped_pages)m_page_table.Finalize();
        m_memory.image.clear();
        released=true;++kernel.releases;
    }
}
inline void KernelCore::AppendNewProcess(KProcess* p){
    assert(p && !p->released);
    if(fail_append)throw std::bad_alloc{};
    ++appends;
}
inline void KernelCore::RemoveProcess(KProcess* p){
    assert(p && p==latest);++removes;
}
"""
service_declarations=r"""
namespace Eden::NS2 {
struct SvcTrace {
    inline static std::atomic<u64> active_pid{};
    static void Register(u64 pid){active_pid.store(pid);}
    static void Unregister(u64 pid){
        u64 expected=pid;
        (void)active_pid.compare_exchange_strong(expected,0);
    }
};
}
namespace Core {
struct FileSystemController {
    std::optional<u64> pid;
    unsigned registration_count{},unregistration_count{};
    void RegisterProcess(u64 process){pid=process;++registration_count;}
    void UnregisterProcessIfPresent(u64 process){
        ++unregistration_count;
        if(pid==process)pid.reset();
    }
};
struct System {
    Kernel::KernelCore& kernel;
    FileSystemController fs;
    Kernel::KernelCore& Kernel(){return kernel;}
    FileSystemController& GetFileSystemController(){return fs;}
};
}
namespace Loader {
enum class ResultStatus {
    Success,ErrorNotInitialized,ErrorUnableToParseKernelMetadata,ErrorLoadingNSO
};
struct LoadParameters {
    int main_thread_priority{};
    std::size_t main_thread_stack_size{};
};
struct AppLoader {
    FileSys::ProgramMetadata metadata;
    const std::vector<u8>& nso;
    bool fail_late{},missing_parameters{},fail_before_kernel{};
    std::pair<ResultStatus,std::optional<LoadParameters>>
    Load(Kernel::KProcess&,Core::System&);
};
}
namespace Service {
struct Process {
    Core::System& m_system;
    Kernel::KProcess* m_process{};
    int m_main_thread_priority{};
    std::size_t m_main_thread_stack_size{};
    bool m_process_started{};
    void Terminate(){
        if(m_process)m_process->Terminate(m_system.Kernel());
    }
    bool Initialize(Loader::AppLoader&,Loader::ResultStatus&);
    void Finalize();
};
#define EDEN_NS2_PROCESS_RUN_GUARD 1
"""
test=k.TEST
test=sub(test,"} // namespace Kernel\nstatic void Require",
         "} // namespace Kernel\n"+service_declarations+init+"\n"+finalize+
         "\n} // namespace Service\nstatic void Require")
loader_method=r"""
std::pair<Loader::ResultStatus,std::optional<Loader::LoadParameters>>
Loader::AppLoader::Load(Kernel::KProcess& process,Core::System& system){
    if(fail_before_kernel)return {ResultStatus::ErrorLoadingNSO,{}};
    const auto code_bytes=CodeBytesFromKnownNso(nso);
    if(process.LoadFromMetadata(system.Kernel(),metadata,code_bytes,0x200000,0x4000).IsError())
        return {ResultStatus::ErrorUnableToParseKernelMetadata,{}};
    auto image=PrepareGuestImage(nso,code_bytes);
    process.LoadModule(system.Kernel(),std::move(image),process.captured.code_address);
    system.fs.RegisterProcess(process.GetProcessId());
    Eden::NS2::SvcTrace::Register(process.GetProcessId());
    if(fail_late)return {ResultStatus::ErrorLoadingNSO,{}};
    if(missing_parameters)return {ResultStatus::Success,{}};
    return {ResultStatus::Success,LoadParameters{44,0x8000}};
}
"""
test=sub(test,"static void VerifyCase(const FileSys::ProgramMetadata& metadata,",
         loader_method+"\nstatic void VerifyCase(const FileSys::ProgramMetadata& metadata,")
case=r"""
        // Cross-owner single transaction. The host's Close() fixture
        // models last KProcess reference and page-table ownership.
        for(unsigned fault=0;fault<5;++fault) {
            Kernel::KernelCore joined_kernel;
            Core::System joined_system{joined_kernel,{}};
            Service::Process process{joined_system};
            Loader::AppLoader loader{metadata,nso};
            loader.fail_late=fault==1;
            loader.missing_parameters=fault==2;
            loader.fail_before_kernel=fault==3;
            joined_kernel.fail_append=fault==4;
            Loader::ResultStatus result=Loader::ResultStatus::ErrorNotInitialized;
            bool succeeded{},caught_oom{};
            try{succeeded=process.Initialize(loader,result);}
            catch(const std::bad_alloc&){caught_oom=true;}
            auto* obj=joined_kernel.latest;
            Require(obj && joined_kernel.creations==1 &&
                    joined_kernel.registrations==__EXPECTED_REGISTRATIONS__,
                    "H01 real Process owner did not create/register KProcess");
            if(fault==0) {
                Require(succeeded && !caught_oom && process.m_process==obj &&
                        obj->refs==1 && obj->m_page_table.mapped_pages==4 &&
                        obj->m_memory.image==PrepareGuestImage(nso,code_bytes).memory &&
                        joined_kernel.appends==1 &&
                        joined_system.fs.pid==obj->GetProcessId() &&
                        Eden::NS2::SvcTrace::active_pid==obj->GetProcessId(),
                        "H01 actual Process owner did not publish real NSO/NPDM");
                process.Finalize();
                Require(!process.m_process && obj->released &&
                        obj->m_page_table.mapped_pages==0 &&
                        joined_kernel.removes==1 && joined_kernel.releases==1 &&
                        !joined_system.fs.pid && Eden::NS2::SvcTrace::active_pid==0,
                        "H01 success teardown leaked pages/RomFS/SVC");
            } else {
                Require(!succeeded && (caught_oom==(fault==4)) &&
                        !process.m_process && obj->released &&
                        obj->refs==0 && obj->m_page_table.mapped_pages==0 &&
                        joined_kernel.releases==1 && joined_kernel.appends==0 &&
                        !joined_system.fs.pid && Eden::NS2::SvcTrace::active_pid==0,
                        "H01 late rejection leaked KProcess, pages or RomFS");
                if(fault!=3)
                    Require(obj->m_memory.writes==1,
                            "H01 expected real guest NSO write before late failure");
                else
                    Require(obj->m_memory.writes==0,
                            "H01 early malformed ExeFS wrote guest code");
            }
            delete joined_kernel.latest;
            Eden::NS2::SvcTrace::active_pid=0;
        }
        std::cout << "H01_JOINED_KPROCESS_EXEFS_PROCESS_OWNER_PASS"
                  << " metadata_init_module=real process_initialize_finalize=real"
                  << " public_npdm_nso=1 guest_image_exact=1"
                  << " accepted_pid_romfs=1 late_faults=rolled_back"
                  << " guest_pages_and_trace=retired host_kernel_fs=stubs"
                  << " PS5=not_exercised\n";
"""
case=case.replace("__EXPECTED_REGISTRATIONS__",
    "((fault==0 || fault==4) ? 1u : 0u)" if register_after_load else "1u")
test=sub(test,"        // An OOM in the resource-limit allocator must return before",
         case+"\n        // An OOM in the resource-limit allocator must return before")

def main()->None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--npdm",type=Path,required=True)
    parser.add_argument("--nso",type=Path,required=True)
    args=parser.parse_args()
    for item in (args.npdm,args.nso):
        if not item.is_file():raise FileNotFoundError(item)
    kernel_source=k.OWNERS[1][1].read_text()
    cxx=(prefix+"\n"+k.actual_initializer(kernel_source)+"\n"+
         k.unchanged_member(kernel_source)+"\n"+
         k.actual_module(kernel_source)+"\n"+
         kernel_methods+"\n"+test)
    compilers=[v for v in ("clang++","g++") if shutil.which(v)]
    if len(compilers)!=2:raise RuntimeError("Both C++20 host compilers required")
    with tempfile.TemporaryDirectory(prefix="eden-h01-connected-") as tmp:
        f=Path(tmp)/"joined.cpp"
        f.write_text(cxx)
        for cc in compilers:
            executable=Path(tmp)/cc.replace("+","p")
            args_cc=[cc,"-std=c++20","-O1","-Wall","-Wextra","-Werror",
                     "-Wno-unused-parameter","-fsanitize=address,undefined",
                     "-fno-sanitize-recover=all","-fno-omit-frame-pointer",
                     str(f),"-o",str(executable)]
            result=subprocess.run(args_cc,text=True,capture_output=True,timeout=100)
            assert result.returncode==0,(cc,result.stderr[-8000:])
            completed=subprocess.run([str(executable),str(args.npdm.resolve()),
                                       str(args.nso.resolve())],text=True,
                                     capture_output=True,timeout=40,env=os.environ.copy())
            assert completed.returncode==0,(cc,completed.stdout[-2000:],completed.stderr[-8000:])
            print(cc,completed.stdout.strip(),flush=True)

if __name__=="__main__":
    main()
