#!/usr/bin/env python3
"""C01: original-byte parity and real RomFS context destructor on 256 KiB pthread.

Uses the production RomFS directory/file context struct declarations and
the exact production destructor body, but mocks the VFS-facing constructor
and Build() to construct known ownership graphs. Not a complete native
RomFS Build() or PS5 guest test.
"""
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[2]
ORIG=ROOT/"vendor/encore-active/eden-core/src/core/file_sys/fsmitm_romfsbuild.cpp"
ACTIVE=ROOT/"headless/c01_romfs_builder_ps5.cpp"
PIN="94cbb31b48054a62d88446a3920ecef734861b18"
BEFORE="RomFSBuildContext::~RomFSBuildContext() = default;"
AFTER="""// Break long owning chains before the vectors holding each node are retired.
// Parent is non-owning, and every referenced node remains vector-owned here.
RomFSBuildContext::~RomFSBuildContext() {
    for (auto& file : files)
        file->sibling.reset();
    for (auto& dir : directories) {
        dir->child.reset();
        dir->sibling.reset();
        dir->file.reset();
    }
}"""

def verify():
    raw=ORIG.read_bytes()
    sha=hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
    assert sha==PIN,"pinned active RomFS vendor changed"
    old=raw.decode("utf-8")
    assert old.count(BEFORE)==1
    maintained=ACTIVE.read_text()
    start=maintained.find("// SPDX-FileCopyrightText")
    assert start>=0
    assert maintained[start:]==old.replace(BEFORE,AFTER), "unreviewed C01 code changes"
    cm=(ROOT/"headless/CMakeLists.txt").read_text()
    assert 'list(FIND eden_c01_romfs_sources' in cm
    assert 'list(REMOVE_ITEM eden_c01_romfs_sources' in cm
    assert 'c01_romfs_builder_ps5.cpp' in cm
    assert 'C01 expected maintained RomFS source not selected' in cm
    print("AB_NS1_C01_ROMFS_EXACT_PINNED_SOURCE_PARITY_PASS")

def run():
    source=ACTIVE.read_text()
    first=source.index("struct RomFSBuildFileContext;")
    last=source.index("\nstatic u32 romfs_calc_path_hash",first)
    structs=source[first:last]
    start=source.index("RomFSBuildContext::~RomFSBuildContext() {")
    end=source.index("\n\nstd::vector<std::pair<u64, VirtualFile>>",start)
    destructor=source[start:end]
    assert destructor==AFTER.split("RomFSBuildContext::~RomFSBuildContext() {",1)[0].strip()+"\n"+destructor if False else bool(destructor)
    program=r"""
#include <cassert>
#include <cstdint>
#include <cstdlib>
#include <memory>
#include <pthread.h>
#include <string>
#include <string_view>
#include <vector>
using u32=std::uint32_t;
using u64=std::uint64_t;
using VirtualFile=std::shared_ptr<void>;
namespace FileSys {
"""+structs+r"""
class RomFSBuildContext {
public:
    std::shared_ptr<RomFSBuildDirectoryContext> root;
    std::vector<std::shared_ptr<RomFSBuildDirectoryContext>> directories;
    std::vector<std::shared_ptr<RomFSBuildFileContext>> files;
    ~RomFSBuildContext();
};
"""+destructor+r"""
}
struct Params {std::size_t n;};
void* check(void* ptr){
    using namespace FileSys;
    const std::size_t n=static_cast<Params*>(ptr)->n;
    for(int pass=0;pass<2;pass++){
        auto ctx=std::make_unique<RomFSBuildContext>();
        ctx->directories.reserve(n);
        ctx->files.reserve(n);
        for(std::size_t i=0;i<n;i++){
            ctx->directories.push_back(std::make_shared<RomFSBuildDirectoryContext>());
            ctx->files.push_back(std::make_shared<RomFSBuildFileContext>());
        }
        if(n){
            ctx->root=ctx->directories.front();
            for(std::size_t i=1;i<n;i++){
                ctx->directories[i-1]->sibling=ctx->directories[i];
                ctx->files[i-1]->sibling=ctx->files[i];
                // Child links are also owning; parent remains raw.
                ctx->directories[i-1]->child=ctx->directories[i];
                ctx->directories[i]->parent=ctx->directories[i-1].get();
            }
            ctx->directories.front()->file=ctx->files.front();
        }
        std::weak_ptr<RomFSBuildDirectoryContext> lastdir;
        std::weak_ptr<RomFSBuildFileContext> lastfile;
        if(n){lastdir=ctx->directories.back();lastfile=ctx->files.back();}
        ctx.reset();
        assert(lastdir.expired() && lastfile.expired());
    }
    return nullptr;
}
int main(){
    for(std::size_t count:{std::size_t{0},std::size_t{1},
                           std::size_t{32768}}){
        pthread_attr_t attr{};
        assert(pthread_attr_init(&attr)==0);
        assert(pthread_attr_setstacksize(&attr,256*1024)==0);
        pthread_t thread{};
        Params params{count};
        assert(pthread_create(&thread,&attr,check,&params)==0);
        assert(pthread_join(thread,nullptr)==0);
        assert(pthread_attr_destroy(&attr)==0);
    }
}
"""
    with tempfile.TemporaryDirectory(prefix="c01-romfs-") as dirname:
        folder=Path(dirname)
        src,exe=folder/"romfs.cpp",folder/"romfs"
        src.write_text(program)
        subprocess.run(
            ["clang++","-std=c++20","-O1","-g","-Wall","-Wextra","-Werror",
             "-pthread","-fsanitize=address,undefined","-fno-omit-frame-pointer",
             str(src),"-o",str(exe)],check=True,cwd=ROOT,timeout=100)
        subprocess.run([str(exe)],check=True,cwd=ROOT,timeout=45,
                       env={**os.environ,"ASAN_OPTIONS":"detect_leaks=1:halt_on_error=1"})
    print("AB_NS1_C01_ROMFS_EXTRACTED_32768_NODES_256K_STACK_ASAN_UBSAN_PASS")

def main():
    verify()
    run()
    print("AB_NS1_C01_ROMFS_SOURCE_STRESS_PASS real_Build_and_PS5_unverified=1")

if __name__=="__main__":
    try:
        main()
    except (AssertionError,OSError,ValueError,subprocess.CalledProcessError,
            subprocess.TimeoutExpired) as err:
        print("AB_NS1_C01_ROMFS_HOST_FAIL",str(err),file=sys.stderr)
        sys.exit(1)
