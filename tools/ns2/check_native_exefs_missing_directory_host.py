#!/usr/bin/env python3
"""H01: execute the actual maintained ExeFS loader's early admission body.

A standalone NSO without a containing directory, missing main.npdm and a
failed layered update must fail before metadata, KProcess or guest memory.
This is a bounded entry proof; complete NPDM/NSO/KProcess remains open.
"""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[2]
OWNER=ROOT/"vendor/encore-active/ns2-runtime/metadata/core/loader/deconstructed_rom_directory.cpp"
code=OWNER.read_text()
start="AppLoader_DeconstructedRomDirectory::LoadResult AppLoader_DeconstructedRomDirectory::Load("
end="\n#ifdef EDEN_NS2_GUEST_COUNTER\n    // This is the real KProcess loader"
assert code.count(start)==code.count(end)==1
actual=start+code.split(start,1)[1].split(end,1)[0]
# This fixture exercises ONLY the real early null/NPDM/NSO admissions.
# Vendor #105 added a full extracted-update VFS overlay in the middle.
# That complete layer is qualified separately in its own exact-source
# suite; do not fake VFS methods or silently claim to execute it here.
import hashlib
raw=OWNER.read_bytes()
owner_blob=hashlib.sha1(b"blob "+str(len(raw)).encode()+bytes([0])+raw).hexdigest()
assert owner_blob == "e8c227b4420ebc38055e3e4c331f39fb6f755595", (
    "Unreviewed selected NS2 loader source; requalify executable fixture",owner_blob)
overlay_start=actual.index("    // Loose ExeFS content can have most of its RomFS")
overlay_end=actual.index("    // Read meta to determine title ID",overlay_start)
overlay=actual[overlay_start:overlay_end]
for required in ("if (standalone && file)", "launched_from_update",
                 "base_exefs=restored", "self_contained_update",
                 "source=selected_version", "CreateRomFS",
                 "selected_update_only", "ambiguous_version"):
    assert required in overlay,("Selected update overlay drift",required)
actual=actual[:overlay_start]+actual[overlay_end:]
# Identity logging below the admission check requires unrelated real VFS
# bytes/GetSize and renderer state. Exclude ONLY that later diagnostic,
# while retaining the actual missing-main guard and prior NPDM decisions.
identity=actual.index("    if (metadata.IsSwitch2()) {\n        // Upstream Eglantine #350")
actual=actual[:identity]
assert "if (!dir)" in actual and actual.count("if (!dir)")>=2
assert "return {ResultStatus::ErrorNullFile, {}};" in actual
assert "return {ResultStatus::ErrorMissingNPDM, {}};" in actual
assert actual.index("if (!dir)") < actual.index('dir->GetFile("main.npdm")')
assert actual.rindex("if (!dir)") < actual.rindex('dir->GetFile("main.npdm")')
assert "metadata.Load(npdm)" in actual and "metadata.Reload(npdm)" in actual
assert 'if (metadata.IsSwitch2() && !dir->GetFile("main"))' in actual
assert 'return {ResultStatus::ErrorLoadingNSO, {}};' in actual
assert actual.index('if (metadata.IsSwitch2() && !dir->GetFile("main"))') > actual.index(
    'metadata.Reload(npdm)')
assert "dir = patch_manager.PatchExeFS(dir);" in actual
# The actual file and directory constructors must also refuse bad parents
# before attempting metadata/icon access; Load alone cannot protect them.
ctor_file=code.split(
    "AppLoader_DeconstructedRomDirectory::AppLoader_DeconstructedRomDirectory(FileSys::VirtualFile",1
)[1].split(
    "AppLoader_DeconstructedRomDirectory::AppLoader_DeconstructedRomDirectory(\n    FileSys::VirtualDir",1
)[0]
assert "if (!file) return;" in ctor_file
assert "if (!file_dir) return;" in ctor_file
assert ctor_file.index("if (!file) return;") < ctor_file.index("file->GetContainingDirectory()")
assert ctor_file.index("if (!file_dir) return;") < ctor_file.index('file_dir->GetFile("main.npdm")')
ctor_dir=code.split(
    "AppLoader_DeconstructedRomDirectory::AppLoader_DeconstructedRomDirectory(\n    FileSys::VirtualDir",1
)[1].split("FileType AppLoader_DeconstructedRomDirectory::IdentifyType(",1)[0]
assert "directory ? directory->GetFile(\"main\") : FileSys::VirtualFile{}" in ctor_dir
# Only the genuine source segment is under test: return before deeper
# metadata/NSO code, whose separate owner-linked tests remain required.
actual+="\n    return {ResultStatus::Success, {}};\n}\n"
fixture=r"""
#include <cassert>
#include <cstdint>
#include <memory>
#include <optional>
#include <string_view>
#include <utility>
using u64=std::uint64_t;
namespace Kernel {struct KProcess {};}
namespace Core {
struct System {
    int value{};
    int& GetFileSystemController(){return value;}
    int& GetContentProvider(){return value;}
};
}
namespace FileSys {
struct VfsDir;
using VirtualDir=std::shared_ptr<VfsDir>;
struct VfsFile {
    VirtualDir parent{};
    VirtualDir GetContainingDirectory() const {return parent;}
};
using VirtualFile=std::shared_ptr<VfsFile>;
struct VfsDir {
    VirtualFile npdm{},executable{};
    VirtualFile GetFile(std::string_view name) const {
        if (name=="main") return executable;
        assert(name=="main.npdm");
        return npdm;
    }
};
struct PatchManager {
    static inline bool fail_patch{};
    PatchManager(u64,int&,int&){}
    VirtualDir PatchExeFS(VirtualDir dir) const {
        return fail_patch ? VirtualDir{} : std::move(dir);
    }
};
}
namespace Loader {
enum class ResultStatus {
    Success,ErrorAlreadyLoaded,ErrorNullFile,ErrorMissingNPDM,ErrorLoadingNSO
};
struct Meta {
    bool switch2{true};
    bool IsSwitch2() const {return switch2;}
    u64 GetTitleID() const {return 42;}
    ResultStatus Load(FileSys::VirtualFile npdm) const {
        return npdm ? ResultStatus::Success : ResultStatus::ErrorMissingNPDM;
    }
    ResultStatus Reload(FileSys::VirtualFile npdm) const {
        return Load(std::move(npdm));
    }
};
class AppLoader_DeconstructedRomDirectory {
public:
    using LoadResult=std::pair<ResultStatus,std::optional<int>>;
    bool is_loaded{};
    FileSys::VirtualFile file{};
    FileSys::VirtualDir dir{};
    bool override_update{};
    Meta metadata{};
    LoadResult Load(Kernel::KProcess&,Core::System&);
};
#define LOG_ERROR(...) ((void)0)
__REAL_ENTRY__
}
int main(){
    Core::System system;
    Kernel::KProcess process;
    using Loader::AppLoader_DeconstructedRomDirectory;
    using Loader::ResultStatus;
    {
        AppLoader_DeconstructedRomDirectory l;
        assert(l.Load(process,system).first==ResultStatus::ErrorNullFile);
    }
    {
        AppLoader_DeconstructedRomDirectory l;
        l.file=std::make_shared<FileSys::VfsFile>();
        assert(l.Load(process,system).first==ResultStatus::ErrorNullFile);
    }
    {
        AppLoader_DeconstructedRomDirectory l;
        l.dir=std::make_shared<FileSys::VfsDir>();
        assert(l.Load(process,system).first==ResultStatus::ErrorMissingNPDM);
    }
    auto good=std::make_shared<FileSys::VfsDir>();
    good->npdm=std::make_shared<FileSys::VfsFile>();
    good->executable=std::make_shared<FileSys::VfsFile>();
    // Native NS2 may not boot an NPDM-only application, even with
    // other auxiliary modules. NS1/Maxwell keeps its legacy admission.
    auto npdm_only=std::make_shared<FileSys::VfsDir>();
    npdm_only->npdm=good->npdm;
    {
        AppLoader_DeconstructedRomDirectory l;
        l.dir=npdm_only;
        assert(l.Load(process,system).first==ResultStatus::ErrorLoadingNSO);
    }
    {
        AppLoader_DeconstructedRomDirectory l;
        l.dir=npdm_only;
        l.metadata.switch2=false;
        assert(l.Load(process,system).first==ResultStatus::Success);
    }
    {
        AppLoader_DeconstructedRomDirectory l;
        l.dir=good;
        assert(l.Load(process,system).first==ResultStatus::Success);
    }
    {
        AppLoader_DeconstructedRomDirectory l;
        l.file=std::make_shared<FileSys::VfsFile>();
        l.file->parent=good;
        assert(l.Load(process,system).first==ResultStatus::Success);
    }
    {
        AppLoader_DeconstructedRomDirectory l;
        l.dir=good;l.override_update=true;
        FileSys::PatchManager::fail_patch=true;
        assert(l.Load(process,system).first==ResultStatus::ErrorMissingNPDM);
        FileSys::PatchManager::fail_patch=false;
    }
    {
        AppLoader_DeconstructedRomDirectory l;
        l.dir=good;l.override_update=true;
        assert(l.Load(process,system).first==ResultStatus::Success);
    }
    {
        AppLoader_DeconstructedRomDirectory l;
        l.is_loaded=true;
        assert(l.Load(process,system).first==ResultStatus::ErrorAlreadyLoaded);
    }
}
""".replace("__REAL_ENTRY__",actual)
compilers=list(dict.fromkeys(x for x in (shutil.which("clang++"),shutil.which("g++")) if x))
assert compilers
with tempfile.TemporaryDirectory(prefix="eden-h01-exefs-entry-") as tmp:
    cpp=Path(tmp)/"entry.cpp";cpp.write_text(fixture)
    for cc in compilers:
        for opt in ("-O0","-O2"):
            exe=Path(tmp)/(Path(cc).name+opt)
            command=[cc,"-std=c++20",opt,"-Wall","-Wextra","-Werror",
                     "-Wno-unused-parameter",
                     "-fsanitize=undefined","-fno-sanitize-recover=all",
                     str(cpp),"-o",str(exe)]
            built=subprocess.run(command,capture_output=True,text=True,timeout=60,
                                 env=os.environ.copy())
            assert built.returncode==0,(cc,built.stderr[-4500:])
            tested=subprocess.run([str(exe)],capture_output=True,text=True,timeout=20)
            assert tested.returncode==0,(cc,tested.stderr[-4500:])
            print("H01_REAL_EXEFS_DIR_ADMISSION_PASS",Path(cc).name,opt,
                  "null_parent=refused missing_npdm=refused failed_update=refused"
                  " base=accepted patched=accepted"
                  " native_missing_main=refused ns1_unaffected=1",flush=True)
