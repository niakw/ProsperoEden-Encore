#!/usr/bin/env python3
"""H01 joined maintained-owner witness: authentic public NPDM/NSO through
KProcess::LoadFromMetadata -> Initialize -> LoadModule -> OS Process::Initialize
and Process::Run/Finalize on the SAME KProcess/guest pages.

Kernel allocations, page backing and RomFS registration are controlled host
stand-ins; no complete SDK update/DLC loading, console boot or PS5 claim.
"""
from pathlib import Path
import os
import shutil
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(Path(__file__).resolve().parent))
import test_real_kprocess_init_guest_rollback as kernel_host

PROCESS_SOURCE=(ROOT/"vendor/encore-active/ns2-runtime/process/core/hle/service/os/process.cpp").read_text()

def extract_owner(start,stop):
    assert PROCESS_SOURCE.count(start)==1 and stop in PROCESS_SOURCE.split(start,1)[1]
    return start+PROCESS_SOURCE.split(start,1)[1].split(stop,1)[0]

real_os_initialize=extract_owner("bool Process::Initialize(", "\nvoid Process::Finalize()")
register_after_load=(real_os_initialize.index("Kernel::KProcess::Register(") >
                     real_os_initialize.index("if (!load_parameters)"))
real_os_finalize=extract_owner("void Process::Finalize() {","\nbool Process::Run()")
real_os_run=extract_owner("bool Process::Run() {","\nvoid Process::Terminate()")
real_os_terminate=extract_owner("void Process::Terminate() {","\nvoid Process::ResetSignal()")
for snippet in (real_os_initialize,real_os_finalize,real_os_run):
    assert "m_process" in snippet and "Finalize()" in snippet

base=kernel_host.PREFIX
def replace_once(old,new):
    global base
    assert base.count(old)==1,("KProcess host fixture drift",old[:80],base.count(old))
    base=base.replace(old,new)

replace_once("#include <array>", "#include <array>\n#include <atomic>\n#include <memory>\n#include <new>\n#include <optional>\n#include <cstdio>")
replace_once("struct KernelCore;\nstruct KSystemResource", "struct KernelCore;\nstruct KProcess;\nstruct KSystemResource")
replace_once("    u64 next_pid{200};",
             """    u64 next_pid{200};
    bool fail_append{};
    unsigned registers{},appends{},removes{};
    KProcess* latest{};
    void AppendNewProcess(KProcess*);
    void RemoveProcess(KProcess*);""")
replace_once("struct KProcess {\n    bool m_is_application=false;",
             """struct KProcess {
    unsigned references{1},opens{},closes{},terminations{},runs{};
    bool fail_run{};
    static KProcess* Create(KernelCore&);
    static void Register(KernelCore&,KProcess*);
    void Open(KernelCore&);
    void Close(KernelCore&);
    Result Run(KernelCore&,int,std::size_t);
    Result Terminate(KernelCore&);
    u64 GetProcessId()const{return m_process_id;}
    bool m_is_application=false;""")
kernel_addons=r"""
inline KProcess* KProcess::Create(KernelCore& kernel) {
    auto* process=new(std::nothrow) KProcess{};
    kernel.latest=process;
    return process;
}
inline void KProcess::Register(KernelCore& kernel,KProcess* process) {
    assert(process==kernel.latest);
    ++kernel.registers;
}
inline void KProcess::Open(KernelCore&) {
    assert(references==1);
    ++references;++opens;
}
inline void KProcess::Close(KernelCore&) {
    assert(references);
    --references;++closes;
    if(!references) {
        m_page_table.Finalize();
        m_memory.image.clear();
    }
}
inline Result KProcess::Run(KernelCore&,int,std::size_t) {
    ++runs;
    return fail_run?Result{88}:Result{};
}
inline Result KProcess::Terminate(KernelCore&) {
    ++terminations;return {};
}
inline void KernelCore::AppendNewProcess(KProcess* p) {
    assert(p==latest && p->m_memory.writes==1);
    if(fail_append)throw std::bad_alloc{};
    ++appends;
}
inline void KernelCore::RemoveProcess(KProcess* p) {
    assert(p==latest && !p->references && !p->m_page_table.mapped_pages);
    ++removes;
}
"""
os_prefix=r"""
namespace Eden::NS2 {
struct SvcTrace {
    static inline std::atomic<u64> active_pid{0};
    static unsigned registrations,retirements;
    static void Register(u64 pid){active_pid=pid;++registrations;}
    static void Unregister(u64 pid){
        if(active_pid.load()==pid){active_pid=0;++retirements;}
    }
};
unsigned SvcTrace::registrations=0, SvcTrace::retirements=0;
}
namespace Core {
struct FakeFilesystem {
    std::optional<u64> owner{};
    unsigned registered{},unregistered{};
    void RegisterProcess(u64 pid){assert(!owner);owner=pid;++registered;}
    void UnregisterProcessIfPresent(u64 pid){
        if(owner==pid){owner.reset();++unregistered;}
    }
};
struct System {
    Kernel::KernelCore& kernel;
    FakeFilesystem filesystem;
    Kernel::KernelCore& Kernel(){return kernel;}
    FakeFilesystem& GetFileSystemController(){return filesystem;}
};
}
namespace Loader {
enum class ResultStatus {
    Success,ErrorNotInitialized,ErrorUnableToParseKernelMetadata,ErrorLoadingNSO
};
struct LoadParameters{
    int main_thread_priority{};
    std::size_t main_thread_stack_size{};
};
struct AppLoader {
    const std::vector<u8>& npdm;
    const std::vector<u8>& nso;
    bool malformed_npdm{},malformed_nso{},fail_late{},missing_params{};
    std::pair<ResultStatus,std::optional<LoadParameters>>
    Load(Kernel::KProcess&,Core::System&);
};
}
#define LOG_ERROR(...) ((void)0)
constexpr int Service_LDR=0;
#define R_FAILED(result) ((result).IsError())
#define HOST_CONCAT2(a,b) a##b
#define HOST_CONCAT(a,b) HOST_CONCAT2(a,b)
#undef SCOPE_EXIT
#define SCOPE_EXIT auto HOST_CONCAT(h01_scope_,__COUNTER__) = HostScopeMaker{} + [&]()
namespace Service {
struct Process {
    Core::System& m_system;
    Kernel::KProcess* m_process{};
    int m_main_thread_priority{};
    std::size_t m_main_thread_stack_size{};
    bool m_process_started{};
    bool Initialize(Loader::AppLoader&,Loader::ResultStatus&);
    void Finalize();
    bool Run();
    void Terminate();
};
#define EDEN_NS2_PROCESS_RUN_GUARD 1
"""
os_tail=r"""
} // namespace Service
std::pair<Loader::ResultStatus,std::optional<Loader::LoadParameters>>
Loader::AppLoader::Load(Kernel::KProcess& process,Core::System& system) {
    if(malformed_npdm || malformed_nso)
        return {ResultStatus::ErrorLoadingNSO,{}};
    FileSys::ProgramMetadata metadata;
    Kernel::CodeSet image;
    std::size_t bytes{};
    try {
        metadata=ParseKnownPublicFixture(npdm);
        bytes=CodeBytesFromKnownNso(nso);
        image=PrepareGuestImage(nso,bytes);
    }catch(const std::runtime_error&) {
        return {ResultStatus::ErrorLoadingNSO,{}};
    }
    Kernel::h01_init_succeeded=false;
    auto result=process.LoadFromMetadata(system.Kernel(),metadata,bytes,
                                         0x200000,0x4000);
    if(result.IsError())return {ResultStatus::ErrorUnableToParseKernelMetadata,{}};
    // Exact maintained LoadModule writes public NSO segments after the
    // real KProcess page-table owner admitted its mapping and KAC.
    process.LoadModule(system.Kernel(),image,process.captured.code_address);
    system.filesystem.RegisterProcess(process.GetProcessId());
    Eden::NS2::SvcTrace::Register(process.GetProcessId());
    if(fail_late)return {ResultStatus::ErrorLoadingNSO,{}};
    if(missing_params)return {ResultStatus::Success,{}};
    return {ResultStatus::Success,Loader::LoadParameters{44,0x8000}};
}
static void ResetTrace() {
    Eden::NS2::SvcTrace::active_pid=0;
    Eden::NS2::SvcTrace::registrations=0;
    Eden::NS2::SvcTrace::retirements=0;
}
static void JoinedCase(const std::vector<u8>& npdm,
                       const std::vector<u8>& nso,unsigned mode) {
    Kernel::KernelCore kernel;
    Core::System sys{kernel,{}};
    Service::Process service{sys};
    Loader::AppLoader loader{npdm,nso};
    loader.malformed_npdm=mode==1;
    loader.malformed_nso=mode==2;
    loader.fail_late=mode==3;
    loader.missing_params=mode==4;
    kernel.fail_append=mode==5;
    ResetTrace();
    Loader::ResultStatus status=Loader::ResultStatus::Success;
    bool initialized=false,appended_failure=false;
    try {
        initialized=service.Initialize(loader,status);
    }catch(const std::bad_alloc&) {
        appended_failure=true;
    }
    auto* p=kernel.latest;
    Require(p && kernel.registers==__EXPECTED_REGISTERED__,
            "KProcess register-before-success lifetime regression");
    if(mode==0 || mode==6) {
        Require(initialized && status==Loader::ResultStatus::Success &&
                service.m_process==p && p->references==1 &&
                p->m_page_table.mapped_pages==4 && p->m_memory.writes==1 &&
                p->m_memory.image==PrepareGuestImage(nso,0x4000).memory &&
                kernel.appends==1 &&
                sys.filesystem.owner==p->GetProcessId(),
                "real joined KProcess not published with original guest NSO");
        if(mode==6)p->fail_run=true;
        if(mode==0) {
            Require(service.Run() && !service.Run() && p->runs==1,
                    "real OS Process::Run changed successful NS2 lifecycle");
            service.Finalize();
        }else {
            Require(!service.Run() && !service.Run() && p->runs==1 &&
                    service.m_process_started && !service.m_process,
                    "real OS Process::Run did not rollback failed guest launch");
        }
        Require(kernel.removes==1 && !sys.filesystem.owner &&
                !p->references && p->m_page_table.mapped_pages==0 &&
                p->m_memory.image.empty() &&
                Eden::NS2::SvcTrace::active_pid==0,
                "valid or late failing OS process did not retire guest pages");
    }else {
        Require(!initialized && !service.m_process && kernel.appends==0 &&
                !p->references && p->m_page_table.mapped_pages==0 &&
                p->m_memory.image.empty() && !sys.filesystem.owner &&
                Eden::NS2::SvcTrace::active_pid==0,
                "rejected process left guest pages, trace or RomFS behind");
        Require(appended_failure==(mode==5),
                "late OS process append OOM did not hit expected boundary");
        if(mode==1 || mode==2)Require(p->m_memory.writes==0,
                "malformed NPDM/NSO already wrote untrusted guest pages");
        if(mode==3 || mode==4 || mode==5)
            Require(p->m_memory.writes==1,
                    "late failure did not exercise REAL guest code write");
    }
    Require(p->closes>=1 && Eden::NS2::SvcTrace::active_pid==0 &&
            sys.filesystem.registered==sys.filesystem.unregistered,
            "joined resource ownership leaked after complete failure");
    delete p;
}
int main(int argc,char** argv) {
    try {
        Require(argc==3,"H01 expected public main.npdm and NSO");
        auto npdm=Bytes(argv[1]),nso=Bytes(argv[2]);
        Require(CodeBytesFromKnownNso(nso)==0x4000,
                "wrong independently built public NSO");
        for(unsigned mode=0;mode<=6;++mode)JoinedCase(npdm,nso,mode);
        std::puts("H01_JOINED_REAL_KPROCESS_OS_PROCESS_HANDOFF_PASS"
                  " KProcess_metadata=real KProcess_init=real"
                  " KProcess_LoadModule=real OS_Process_Initialize=real"
                  " OS_Process_Run_Finalize=real public_npdm_nso=1"
                  " guest_bytes=exact guest_page_late_rollback=1"
                  " failed_append_oom=rolled_back missing_params=refused"
                  " malformed_nso_npdm=refused launch_fail=rolled_back"
                  " host_page_and_loader_shims=1 PS5=not_exercised");
        return 0;
    }catch(const std::exception& e) {
        std::fprintf(stderr,"H01_JOINED_OWNER_FAIL: %s\n",e.what());
        return 1;
    }
}
"""
os_tail=os_tail.replace("__EXPECTED_REGISTERED__",
    "((mode==0 || mode==5 || mode==6) ? 1u : 0u)" if register_after_load else "1u")
main_helpers=kernel_host.TEST.split("static void VerifyCase(",1)[0]
assert "ParseKnownPublicFixture" in main_helpers and "PrepareGuestImage" in main_helpers
with tempfile.TemporaryDirectory(prefix="eden-h01-joined-kernel-os-") as tmp:
    for name,owner_path in [kernel_host.OWNERS[1]]:
        source=owner_path.read_text()
        code=base+"\n"+kernel_host.actual_initializer(source)+"\n"
        code+=kernel_host.unchanged_member(source)+"\n"
        code+=kernel_host.actual_module(source)+"\n"
        code+=kernel_addons+"\n"+main_helpers+"\n"+os_prefix
        code+=real_os_initialize+"\n"+real_os_finalize+"\n"
        code+=real_os_run+"\n"+real_os_terminate+"\n"+os_tail
        path=Path(tmp)/"joined.cpp"
        path.write_text(code)
        for compiler in (shutil.which("clang++"),shutil.which("g++")):
            assert compiler,"both compilers required"
            for opt in ("-O0","-O2"):
                exe=Path(tmp)/(Path(compiler).name.replace("+","p")+opt)
                cmd=[compiler,"-std=c++20",opt,"-Wall","-Wextra","-Werror",
                     "-Wno-unused-parameter","-Wno-unused-variable",
                     "-fsanitize=undefined","-fno-sanitize-recover=all",
                     str(path),"-o",str(exe)]
                build=subprocess.run(cmd,text=True,capture_output=True,timeout=90,env=os.environ.copy())
                assert build.returncode==0,(cmd,build.stderr[-7000:])
                run=subprocess.run([str(exe),*sys.argv[1:]],text=True,capture_output=True,
                                   timeout=30,env=os.environ.copy())
                assert run.returncode==0,(compiler,run.stdout[-1500:],run.stderr[-6000:])
                print(Path(compiler).name,opt,run.stdout.strip(),flush=True)
