#!/usr/bin/env python3
"""P1.1: real pre-kernel NPDM reader, for extracted, NSP, XCI and NCA.

Extract the shipping C++ owner intact; use synthetic stand-in content objects
(no actual game, keys or console); cover malformed/absent metadata and NS1.
"""
from pathlib import Path
import os, shutil, subprocess, tempfile

ROOT=Path(__file__).resolve().parents[2]
source=(ROOT/"vendor/encore-active/ns2-runtime/process/core/core.cpp").read_text()
begin="[[nodiscard]] bool IsSwitch2LaunchProgram("
end="\n} // namespace"
assert source.count(begin)==1
helper=begin+source.split(begin,1)[1].split(end,1)[0]
for required in ("Loader::FileType::NSP","Loader::FileType::XCI",
                 "Loader::FileType::NCA","metadata.Load(npdm)",
                 "GetSecurePartitionNSP()","GetExeFS()"):
    assert required in helper

cpp=r"""
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <memory>
#include <stdexcept>
#include <string>
#include <utility>
using u64=std::uint64_t;
namespace Loader {
enum class ResultStatus { Success, Error };
enum class FileType { Unknown, NSP, XCI, NCA };
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
    bool valid{true},is_second{},throwing{};
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
        return Loader::ResultStatus::Success;
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
}
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
    auto extracted=std::make_shared<File>();extracted->directory=dir2;
    assert(IsSwitch2LaunchProgram(extracted,0,0));
    assert(IsSwitch2LaunchProgram(prog,0,0));
    assert(IsSwitch2LaunchProgram(pkg,0x200,0));
    assert(IsSwitch2LaunchProgram(card,0x200,0));
    auto old=std::make_shared<File>();old->directory=dir1;
    assert(!IsSwitch2LaunchProgram(old,0,0));
    prog->exefs=dir1;
    assert(!IsSwitch2LaunchProgram(pkg,0x200,0));
    assert(!IsSwitch2LaunchProgram(card,0x200,0));
    prog->exefs=dir2;
    npdm2->valid=false;
    assert(!IsSwitch2LaunchProgram(pkg,0x200,0));
    npdm2->valid=true;
    pkg->valid=false;
    assert(!IsSwitch2LaunchProgram(card,0x200,0));
    pkg->valid=true;
    pkg->throwing=true;
    assert(!IsSwitch2LaunchProgram(pkg,0x200,0));
    pkg->throwing=false;
    auto missing=std::make_shared<File>(*pkg);missing->program.reset();
    assert(!IsSwitch2LaunchProgram(missing,0x200,0));
    assert(!IsSwitch2LaunchProgram({},0,0));
    assert(IsSwitch2LaunchProgram(card,0x200,0));
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
