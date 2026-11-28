#!/usr/bin/env python3
"""P1.1: real pre-kernel NPDM reader, for extracted, NSP, XCI and NCA.

Extract the shipping C++ owner intact; use synthetic stand-in content objects
(no actual game, keys or console); cover malformed/absent metadata and NS1.
"""
from pathlib import Path
import os, shutil, subprocess, tempfile

ROOT=Path(__file__).resolve().parents[2]
source=(ROOT/"vendor/encore-active/eden/src/core/core.cpp").read_text()
begin="[[nodiscard]] bool IsSwitch2LaunchProgram("
end="\n} // namespace"
assert source.count(begin)==1
helper=begin+source.split(begin,1)[1].split(end,1)[0]
# PS5 library launches loose ExeFS by ".../exefs/main". Generation detection
# must resolve main.npdm from that launched file's VFS parent before the kernel.
assert 'Common::SplitPath(filepath, &launch_dir, &launch_filename, nullptr);' in source
assert 'launch_filename == "main" ? launch_dir' in source
assert 'virtual_filesystem->OpenDirectory(npdm_dir, FileSys::OpenMode::Read)' in source
assert source.index('exefs_dir->GetFile("main.npdm")') < source.index("InitializeKernel(system)")
for required in ("Loader::FileType::NSP","Loader::FileType::XCI",
                 "Loader::FileType::NCA","metadata.Load(npdm)",
                 "metadata.IsSwitch2()", "EDEN_NS2_PREKERNEL_NPDM",
                 "GetSecurePartitionNSP()","GetExeFS()", "direct_extracted_npdm"):
    assert required in helper

cpp=r"""
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <memory>
#include <optional>
#include <stdexcept>
#include <string>
#include <utility>
using u64=std::uint64_t;
using u8=std::uint8_t;
namespace Loader {
enum class ResultStatus { Success, Error };
enum class FileType { Error, Unknown, NSP, XCI, NCA, NX };
}
namespace FileSys {
struct Dir; struct File;
using VirtualFile=std::shared_ptr<File>;
using VirtualDir=std::shared_ptr<Dir>;
enum class ContentRecordType { Program };
struct File {
    Loader::FileType kind{Loader::FileType::Unknown};
    VirtualDir directory{},exefs{};
    VirtualFile program{},secure{};
    bool valid{true},is_second{},throwing{},late_error{},nup{},nup_mounted{true},nx{};
    u8 nx_platform{};
    std::size_t GetSize() const { return 256; }
    u64 title{0x100};
    VirtualDir GetContainingDirectory() const { return directory; }
};
struct Dir {
    VirtualFile npdm;
    VirtualFile GetFile(const std::string& key) const {
        return key=="main.npdm" ? npdm : nullptr;
    }
};
struct ProgramMetadata {
    bool second{};
    Loader::ResultStatus Load(const VirtualFile& npdm) {
        if (!npdm || !npdm->valid) return Loader::ResultStatus::Error;
        second=npdm->is_second;
        return npdm->late_error ? Loader::ResultStatus::Error : Loader::ResultStatus::Success;
    }
    bool IsSwitch2() const { return second; }
};
struct NCA {
    VirtualFile file;
    explicit NCA(VirtualFile f) : file(std::move(f)) {}
    Loader::ResultStatus GetStatus() const {
        return file && file->valid ? Loader::ResultStatus::Success : Loader::ResultStatus::Error;
    }
    VirtualDir GetExeFS() const { return file ? file->exefs : nullptr; }
};
struct NSP {
    VirtualFile file;
    NSP(VirtualFile f,u64,std::size_t) : file(std::move(f)) {}
    Loader::ResultStatus GetStatus() const {
        return file && file->valid ? Loader::ResultStatus::Success : Loader::ResultStatus::Error;
    }
    u64 GetProgramTitleID() const { return file->title; }
    std::shared_ptr<NCA> GetNCA(u64 id,ContentRecordType type) const {
        assert(type==ContentRecordType::Program);
        if (!file->program || id!=file->title) return {};
        return std::make_shared<NCA>(file->program);
    }
};
struct XCI {
    VirtualFile file;
    u64 id{};
    std::size_t index{};
    XCI(VirtualFile f,u64 program,std::size_t i):file(std::move(f)),id(program),index(i){}
    Loader::ResultStatus GetStatus() const {
        return file && file->valid ? Loader::ResultStatus::Success : Loader::ResultStatus::Error;
    }
    std::shared_ptr<NSP> GetSecurePartitionNSP() const {
        return file->secure ? std::make_shared<NSP>(file->secure,id,index) : nullptr;
    }
    u64 GetProgramTitleID() const { return file->secure?file->secure->title:0; }
};
}
namespace Loader {
FileType IdentifyFile(const FileSys::VirtualFile& file) {
    if (file->throwing) throw std::runtime_error("bad container");
    return file->kind;
}
struct AppLoader_NX {
    struct ProgramPlatform { u64 program_id; u8 platform; };
    static FileType IdentifyType(const FileSys::VirtualFile& file) {
        return file && file->nx ? FileType::NX : FileType::Error;
    }
    static std::optional<ProgramPlatform> ReadProgramPlatform(
        const FileSys::VirtualFile& file, u64 program_id) {
        if (!file || !file->nx || (file->nx_platform != 1 && file->nx_platform != 2))
            return std::nullopt;
        return ProgramPlatform{program_id, file->nx_platform};
    }
};
}
// NUP follows the source-selected native bridge, not an extension heuristic.
namespace Eden::NupV1::Native {
bool HasNupV1Header(const FileSys::VirtualFile& file) {
    return file && file->nup;
}
struct Mount {
    FileSys::VirtualFile file;
    static std::shared_ptr<Mount> Open(const FileSys::VirtualFile& source) {
        return source && source->nup_mounted
            ? std::make_shared<Mount>(Mount{source}) : nullptr;
    }
};
struct ContentSet {
    explicit ContentSet(std::shared_ptr<Mount> mount_) : mount(std::move(mount_)) {}
    FileSys::VirtualDir ExeFS() const { return mount ? mount->file->exefs : nullptr; }
    std::shared_ptr<Mount> mount;
};
}
// The production logger is tested in the SDK syntax gate. This isolated
// source-extracted fixture must evaluate the real arguments, without needing
// the full Core logging category implementation.
template<typename... Args> void CheckLogArgs(Args&&...) {}
#define LOG_INFO(category, ...) CheckLogArgs(__VA_ARGS__)
__HELPER__
int main() {
    using namespace FileSys;
    auto npdm2=std::make_shared<File>(); npdm2->is_second=true;
    auto npdm1=std::make_shared<File>();
    auto dir2=std::make_shared<Dir>();dir2->npdm=npdm2;
    auto dir1=std::make_shared<Dir>();dir1->npdm=npdm1;
    auto prog=std::make_shared<File>();prog->kind=Loader::FileType::NCA;prog->exefs=dir2;
    auto pkg=std::make_shared<File>();pkg->kind=Loader::FileType::NSP;pkg->title=0x200;pkg->program=prog;
    auto card=std::make_shared<File>();card->kind=Loader::FileType::XCI;card->secure=pkg;
    auto extracted=std::make_shared<File>();
    // Reproduce the PS5 extracted-ExeFS boundary: a bootable main file can
    // arrive without a preserved containing-directory owner. The direct NPDM
    // resolved from the launch directory must still select Switch 2.
    assert(IsSwitch2LaunchProgram(extracted,npdm2,0,0));
    assert(IsSwitch2LaunchProgram(prog,{},0,0));
    assert(IsSwitch2LaunchProgram(pkg,{},0x200,0));
    assert(IsSwitch2LaunchProgram(card,{},0x200,0));
    auto nup=std::make_shared<File>();nup->nup=true;nup->exefs=dir2;
    assert(IsSwitch2LaunchProgram(nup,{},0,0));
    nup->nup_mounted=false;
    assert(!IsSwitch2LaunchProgram(nup,{},0,0));
    nup->nup_mounted=true;
    nup->exefs=dir1;
    assert(!IsSwitch2LaunchProgram(nup,{},0,0));
    nup->exefs=dir2;
    auto nx=std::make_shared<File>();nx->nx=true;nx->nx_platform=2;
    assert(IsSwitch2LaunchProgram(nx,{},0x400,0));
    nx->nx_platform=1;
    assert(!IsSwitch2LaunchProgram(nx,{},0x100,0));
    nx->nx_platform=0;
    assert(!IsSwitch2LaunchProgram(nx,{},0x400,0));
    nx->nx=false;
    assert(!IsSwitch2LaunchProgram(nx,{},0x400,0));
    auto old=std::make_shared<File>();old->directory=dir1;
    assert(!IsSwitch2LaunchProgram(old,{},0,0));
    prog->exefs=dir1;
    assert(!IsSwitch2LaunchProgram(pkg,{},0x200,0));
    assert(!IsSwitch2LaunchProgram(card,{},0x200,0));
    prog->exefs=dir2;
    npdm2->valid=false;
    assert(!IsSwitch2LaunchProgram(pkg,{},0x200,0));
    npdm2->valid=true;
    // The extended ACID already establishes generation. A later NPDM
    // validation failure must not silently switch to a 4 GiB NS1 layout.
    npdm2->late_error=true;
    assert(IsSwitch2LaunchProgram(extracted,npdm2,0,0));
    assert(IsSwitch2LaunchProgram(pkg,{},0x200,0));
    assert(IsSwitch2LaunchProgram(card,{},0x200,0));
    npdm2->late_error=false;
    npdm1->late_error=true;
    assert(!IsSwitch2LaunchProgram(old,{},0,0));
    npdm1->late_error=false;
    pkg->valid=false;
    assert(!IsSwitch2LaunchProgram(card,{},0x200,0));
    pkg->valid=true;
    pkg->throwing=true;
    assert(!IsSwitch2LaunchProgram(pkg,{},0x200,0));
    pkg->throwing=false;
    auto missing=std::make_shared<File>(*pkg);missing->program.reset();
    assert(!IsSwitch2LaunchProgram(missing,{},0x200,0));
    assert(!IsSwitch2LaunchProgram({}, {},0,0));
    assert(IsSwitch2LaunchProgram(card,{},0x200,0));
    std::puts("P1_1_NS2_PREKERNEL_CONTAINER_NPDM_PASS");
}
""".replace("__HELPER__",helper)
env=os.environ.copy()
sdk=Path("/Library/Developer/CommandLineTools/SDKs/MacOSX15.4.sdk")
if sdk.is_dir():env["SDKROOT"]=str(sdk)
compilers=list(dict.fromkeys(filter(None,(shutil.which("clang++"),shutil.which("g++")))))
assert compilers
with tempfile.TemporaryDirectory(prefix="eden-ns2-npdm-") as temp:
    src=Path(temp)/"fixture.cpp";src.write_text(cpp)
    for compiler in compilers:
        for opt in ("-O0","-O2"):
            exe=Path(temp)/(Path(compiler).name.replace("+","p")+opt)
            build=subprocess.run([compiler,"-std=c++20",opt,"-Wall","-Wextra","-Werror",
                "-fsanitize=undefined","-fno-sanitize-recover=all",
                str(src),"-o",str(exe)],capture_output=True,text=True,env=env,timeout=50)
            assert build.returncode==0,(compiler,build.stderr[-2800:])
            run=subprocess.run([str(exe)],capture_output=True,text=True,env=env,timeout=15)
            assert run.returncode==0,(compiler,run.stderr[-2500:])
            assert "P1_1_NS2_PREKERNEL_CONTAINER_NPDM_PASS" in run.stdout
            print("P1_1_PREKERNEL_NPDM_SOURCE_PASS",Path(compiler).name,opt,flush=True)
