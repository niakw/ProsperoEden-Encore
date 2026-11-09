#!/usr/bin/env python3
"""H01: execute the maintained ExeFS commit tail against real registration outcomes.

RomFSFactory queries the loader during construction. An NS2 process must not
retain is_loaded or publish its SVC trace if standalone filesystem admission
fails or allocates unsuccessfully. The extracted owner also tests NS1 parity.
This does not claim complete NPDM/NSO parsing or a PS5 launch.
"""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
OWNER = ROOT / "vendor/encore-active/ns2-runtime/metadata/core/loader/deconstructed_rom_directory.cpp"
source = OWNER.read_text()
start = "    // RomFSFactory invokes ReadRomFS in its constructor"
end = "\n}\n\nResultStatus AppLoader_DeconstructedRomDirectory::ReadRomFS("
assert source.count(start) == source.count(end) == 1
tail = source.split(start, 1)[1].split(end, 1)[0]
owner = start + tail
assert owner.index("is_loaded = true;") < owner.index("RegisterProcess(")
assert owner.index("RegisterProcess(") < owner.index("Eden::NS2::SvcTrace::Register(")
assert owner.count("is_loaded = false;") == 2
assert "if (!metadata.IsSwitch2()) throw;" in owner
assert "if (metadata.IsSwitch2() && registered.IsError())" in owner

cpp = r"""
#include <cassert>
#include <cstdint>
#include <cstdio>
#include <memory>
#include <new>
#include <optional>
#include <utility>
#include <vector>
using u64=std::uint64_t;
#define LOG_INFO(...) ((void)0)
namespace Eden::NS2 {
struct SvcTrace {
    static inline u64 active{};
    static inline int registered{};
    static void Register(u64 pid) { active=pid; ++registered; }
};
}
namespace Loader { struct AppLoader_DeconstructedRomDirectory; }
struct FakeFS;
namespace FileSys {
struct RomFSFactory {
    RomFSFactory(Loader::AppLoader_DeconstructedRomDirectory&, int&, FakeFS&);
};
}
struct RegistrationResult {
    bool rejected{};
    bool IsError() const { return rejected; }
};
struct ProgramId {};
struct FakeFS {
    bool return_error{}, throw_alloc{};
    int attempts{}, commits{};
    RegistrationResult RegisterProcess(u64 id, ProgramId,
                                      std::shared_ptr<FileSys::RomFSFactory>&& factory) {
        assert(id == 17 && factory);
        ++attempts;
        if (throw_alloc) throw std::bad_alloc{};
        if (return_error) return {true};
        ++commits;
        return {false};
    }
};
struct FakeSystem {
    int provider{};
    FakeFS fs;
    FakeFS& GetFileSystemController(){ return fs; }
    int& GetContentProvider(){ return provider; }
};
struct FakeProcess {
    u64 GetProcessId() const { return 17; }
};
namespace Loader {
enum class ResultStatus { Success, ErrorLoadingNSO };
struct LoadParameters { int priority{}, stack{}; };
struct Metadata {
    bool ns2{true};
    bool IsSwitch2() const { return ns2; }
    u64 GetTitleID() const { return 0x123; }
    int GetMainThreadPriority() const { return 23; }
    int GetMainThreadStackSize() const { return 0x9000; }
};
struct AppLoader_DeconstructedRomDirectory {
    using LoadResult = std::pair<ResultStatus,std::optional<LoadParameters>>;
    bool is_loaded{};
    bool standalone{true};
    u64 title_id{};
    Metadata metadata{};
    FakeSystem system{};
    LoadResult Commit(FakeProcess& process) {
        [[maybe_unused]] const u64 base_address{0x1000};
        [[maybe_unused]] const std::vector<int> modules{1};
__REAL_COMMIT_TAIL__
    }
};
}
FileSys::RomFSFactory::RomFSFactory(
    Loader::AppLoader_DeconstructedRomDirectory& loader, int&, FakeFS&) {
    // Production factory's ReadRomFS requires a temporarily loaded owner.
    assert(loader.is_loaded);
}
static void reset() {
    Eden::NS2::SvcTrace::active=0;
    Eden::NS2::SvcTrace::registered=0;
}
int main() {
    FakeProcess process;
    {
        reset();
        Loader::AppLoader_DeconstructedRomDirectory loader;
        const auto [result,params]=loader.Commit(process);
        assert(result==Loader::ResultStatus::Success && params);
        assert(params->priority==23 && params->stack==0x9000);
        assert(loader.is_loaded && loader.title_id==0x123);
        assert(loader.system.fs.attempts==1 && loader.system.fs.commits==1);
        assert(Eden::NS2::SvcTrace::active==17 && Eden::NS2::SvcTrace::registered==1);
    }
    {
        reset();
        Loader::AppLoader_DeconstructedRomDirectory loader;
        loader.system.fs.return_error=true;
        const auto [result,params]=loader.Commit(process);
        assert(result==Loader::ResultStatus::ErrorLoadingNSO && !params);
        assert(!loader.is_loaded && loader.system.fs.commits==0);
        assert(Eden::NS2::SvcTrace::active==0 && Eden::NS2::SvcTrace::registered==0);
    }
    {
        reset();
        Loader::AppLoader_DeconstructedRomDirectory loader;
        loader.system.fs.throw_alloc=true;
        const auto [result,params]=loader.Commit(process);
        assert(result==Loader::ResultStatus::ErrorLoadingNSO && !params);
        assert(!loader.is_loaded && loader.system.fs.attempts==1);
        assert(Eden::NS2::SvcTrace::active==0 && Eden::NS2::SvcTrace::registered==0);
    }
    {
        reset();
        Loader::AppLoader_DeconstructedRomDirectory loader;
        loader.standalone=false;
        const auto [result,params]=loader.Commit(process);
        assert(result==Loader::ResultStatus::Success && params);
        assert(loader.is_loaded && loader.system.fs.attempts==0);
        assert(Eden::NS2::SvcTrace::active==17);
    }
    {
        reset();
        Loader::AppLoader_DeconstructedRomDirectory loader;
        loader.metadata.ns2=false;
        loader.system.fs.return_error=true;
        const auto [result,params]=loader.Commit(process);
        assert(result==Loader::ResultStatus::Success && params);
        assert(loader.is_loaded && loader.system.fs.attempts==1);
        assert(Eden::NS2::SvcTrace::active==0);
    }
    {
        reset();
        Loader::AppLoader_DeconstructedRomDirectory loader;
        loader.metadata.ns2=false;
        loader.system.fs.throw_alloc=true;
        bool refused=false;
        try { (void)loader.Commit(process); }
        catch (const std::bad_alloc&) { refused=true; }
        assert(refused && loader.is_loaded && Eden::NS2::SvcTrace::active==0);
    }
    std::puts("H01_NS2_EXEFS_FS_REGISTRATION_REAL_OWNER_PASS"
              " ns2_commit=1 fs_error_rollback=1 oom_rollback=1"
              " svc_trace_after_fs_commit=1 ns1_semantics_preserved=1"
              " full_nso_npdm_process=not_exercised");
}
""".replace("__REAL_COMMIT_TAIL__", owner)
compilers=list(dict.fromkeys(x for x in (shutil.which("clang++"),shutil.which("g++")) if x))
assert compilers
with tempfile.TemporaryDirectory(prefix="eden-h01-real-exefs-fs-") as tmp:
    file=Path(tmp)/"owner.cpp"
    file.write_text(cpp)
    for compiler in compilers:
        for opt in ("-O0","-O2"):
            binary=Path(tmp)/(Path(compiler).name+opt)
            command=[compiler,"-std=c++20",opt,"-Wall","-Wextra","-Werror",
                     "-fsanitize=undefined","-fno-sanitize-recover=all",
                     str(file),"-o",str(binary)]
            built=subprocess.run(command,env=os.environ.copy(),capture_output=True,
                                 text=True,timeout=60)
            assert built.returncode==0,(command,built.stderr[-5000:])
            executed=subprocess.run([str(binary)],capture_output=True,text=True,timeout=15)
            assert executed.returncode==0,(command,executed.stderr[-5000:])
            print(Path(compiler).name,opt,executed.stdout.strip(),flush=True)
