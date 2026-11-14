#!/usr/bin/env python3
"""Real configured PS5 native CMake graph and syntax; no ELF, link, gameplay."""
from __future__ import annotations
import json
from pathlib import Path
import shlex
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
REVIEWED_VENDORS={
    "1ec7b429238d1175a76dc94b7c0a7f1c2eb62864",
    "fe9edd661d6f0824c7339865d50aa9cf99cab150",
    "c339fd06f02e42e67d5416ae82194ba619b7ee68",
    "47568425c71d534b72cc966d1500412c9ae4fc16",
    "447e08718c9b6625508da6ce63796ed1f4285d2f",
    "97fdc316fcf5b42e08c26845887f298feac2a424",
    "99ca67babe955398e157c6b28b22a79cbb88967e",
    "7bd7a85e6c1886035c75395c86b05b231375bbf5",
    "7b42e7f4ba6887fe6d7b539a1d2c50e6782603f6",
    "0267753219c4b6a6f3fa086a356b698cd5295f78",
}
OWNERS=(ROOT/"src/ns2_sparse_guest.cpp",
        ROOT/"src/host_memory.cpp")
NATIVE_GUEST=(ROOT/"vendor/encore-active/eden-core/src/core/memory_native_a32.cpp",
              ROOT/"vendor/encore-active/eden-core/src/core/memory_native_standard.cpp")
NATIVE_SHARED=ROOT/"vendor/encore-active/ns2-runtime/sparse-residency/core/hle/kernel/k_shared_memory.cpp"
NATIVE_KERNEL=ROOT/"vendor/encore-active/ns2-runtime/sparse-residency/core/hle/kernel/k_memory_manager.cpp"
NATIVE_SLAB=ROOT/"vendor/encore-active/ns2-runtime/sparse-residency/core/hle/kernel/init/init_slab_setup.cpp"

def args(row):
    return list(row["arguments"]) if "arguments" in row else shlex.split(row["command"])

def main():
    native=Path(sys.argv[1]).resolve()
    sha=subprocess.check_output(["git","rev-parse","HEAD:vendor"],cwd=ROOT,text=True).strip()
    actual=subprocess.check_output(["git","-C",str(ROOT/"vendor"),"rev-parse","HEAD"],
                                   text=True).strip()
    if sha!=actual or sha not in REVIEWED_VENDORS:
        raise RuntimeError("Wrong vendor physical owner: "+sha)
    # These selected sparse page table, KSharedMemory, kernel/slab and
    # publisher sources are byte-identical in both reviewed vendor graphs.
    import hashlib
    def gitblob(path):
        raw=path.read_bytes()
        return hashlib.sha1(b"blob "+str(len(raw)).encode()+bytes([0])+raw).hexdigest()
    for owner,expected in (
        (NATIVE_GUEST[0],"1b506bac747a3c492d4393016ca2b7dc29bfcc57"),
        (NATIVE_GUEST[1],"c8f197810af244c3f2d66413352533734d031620"),
        (NATIVE_SHARED,"9b47d62a6b8503c7a3cdff053888ea47a799cbed"),
        (NATIVE_KERNEL,"88f3e2c9220ee03fd6600ef12441d7ece7527c9d"),
        (NATIVE_SLAB,"130eb7bd53e29b816bb81fec3fa053a584cd4b6e"),
    ):
        if gitblob(owner)!=expected:
            raise RuntimeError("Unreviewed native sparse owner "+str(owner))
    cache=(native/"CMakeCache.txt").read_text()
    if "set(EDEN_NS2_SPARSE_BACKING ON)" not in (ROOT/"headless/CMakeLists.txt").read_text():
        raise RuntimeError("Production sparse PS5 backing not selected")
    if "EDEN_PS5_VULKAN:BOOL=ON" not in cache:
        raise RuntimeError("Real PS5 Vulkan not enabled")
    db=json.loads((native/"compile_commands.json").read_text())
    selected=[]
    for path in OWNERS:
        matches=[r for r in db if Path(r["file"]).resolve()==path.resolve()]
        if len(matches)!=1: raise RuntimeError(f"Expected one {path}; got {len(matches)}")
        selected.append((path.name,matches[0]))
    variants={x.resolve() for x in NATIVE_GUEST}
    vendor_rows=[r for r in db if Path(r["file"]).resolve() in variants]
    if len(vendor_rows)!=1: raise RuntimeError(f"Expected one real PTE TU, got {len(vendor_rows)}")
    selected.append(("native_guest_pte",vendor_rows[0]))
    shared_rows=[r for r in db if Path(r["file"]).resolve()==NATIVE_SHARED.resolve()]
    if len(shared_rows)!=1: raise RuntimeError(
        f"Expected exactly one sparse KSharedMemory TU, got {len(shared_rows)}")
    selected.append(("native_kernel_shared_clear",shared_rows[0]))
    kernel_rows=[r for r in db if Path(r["file"]).resolve()==NATIVE_KERNEL.resolve()]
    if len(kernel_rows)!=1: raise RuntimeError(f"Expected exactly one real native kernel direct owner, got {len(kernel_rows)}")
    selected.append(("native_kernel_direct",kernel_rows[0]))
    slab_rows=[r for r in db if Path(r["file"]).resolve()==NATIVE_SLAB.resolve()]
    if len(slab_rows)!=1:
        raise RuntimeError(f"Expected one real native KPort/KPageBuffer slab owner, got {len(slab_rows)}")
    selected.append(("native_kernel_slabs",slab_rows[0]))
    # R457 storage follow-up: the new six maintained readers were previously
    # tested through source-derived mocks and a script-mode selector. Prove
    # they are each the sole real CMake native compilation owner, then compile
    # the full TUs with the exact SDK command (not replacement mock headers).
    storage_labels = set()
    if sha in {"7bd7a85e6c1886035c75395c86b05b231375bbf5", "7b42e7f4ba6887fe6d7b539a1d2c50e6782603f6", "0267753219c4b6a6f3fa086a356b698cd5295f78"}:
        storage_receipts = {
            "file_sys/vfs/vfs.cpp": "70926039977f56c87558270d7655f8de26d1e446",
            "file_sys/vfs/vfs_vector.cpp": "5f9c99b7ed5227c403ceca1d2e04d6c8dafc26cb",
            "file_sys/partition_filesystem.cpp": "350af05f831fe89a05158350f8c8aded988980dd",
            "file_sys/fssystem/fssystem_nca_file_system_driver.cpp": "f6ceeb8d18b88b850c19b86cc3823e40ce5b9afa",
            "file_sys/fssystem/fssystem_integrity_verification_storage.cpp": "5afc754433f6276ffd80bc0af418d31cf5cf496c",
            "file_sys/romfs.cpp": "51eb401e5f2e3a0deefc5fc0e4cc30b0f4b8e4a3",
        }
        for relative, expected in storage_receipts.items():
            path = ROOT/"vendor/encore-active/eden-core/src/core"/relative
            if gitblob(path) != expected:
                raise RuntimeError("Unreviewed real storage owner "+relative)
            suffix = Path("src/core")/relative
            rows = [r for r in db if Path(r["file"]).parts[-len(suffix.parts):] == suffix.parts]
            if len(rows) != 1 or Path(rows[0]["file"]).resolve() != path.resolve():
                raise RuntimeError("Missing, duplicate or wrong native storage TU "+relative)
            label = "storage_"+Path(relative).stem
            storage_labels.add(label)
            selected.append((label, rows[0]))
        print("R457_NATIVE_STORAGE_6_OWNER_GRAPH_PASS exact_receipts=6",flush=True)

    shader_labels = set()
    bfs_header = None
    if sha in {"7b42e7f4ba6887fe6d7b539a1d2c50e6782603f6", "0267753219c4b6a6f3fa086a356b698cd5295f78"}:
        relative = Path("shader_recompiler/frontend/ir/breadth_first_search.h")
        bfs_header = native/"headless/r23-shader-phi/include"/relative
        vendor_header = ROOT/"vendor/encore-active/eden-shader/include"/relative
        if gitblob(bfs_header) != "194476705f21bd1c27f532fdd5cc04d99a3cd620" or gitblob(vendor_header) != "194476705f21bd1c27f532fdd5cc04d99a3cd620":
            raise RuntimeError("Wrong native adaptive BFS staged header")
        texture = ROOT/"vendor/encore-active/eden-shader/src/shader_recompiler/ir_opt/texture_pass.cpp"
        if gitblob(texture) != "85c523e435ee8803ef3d2087567aa1a4b5d09369":
            raise RuntimeError("Unexpected conditional Phi texture pass owner")
        rows = [r for r in db if Path(r["file"]).parts[-3:] == ("shader_recompiler","ir_opt","texture_pass.cpp")]
        if len(rows) != 1 or Path(rows[0]["file"]).resolve() != texture.resolve():
            raise RuntimeError("Wrong or duplicate selected texture pass")
        label = "shader_texture_phi_bfs"
        shader_labels.add(label)
        selected.append((label, rows[0]))
        print("R457_NATIVE_BFS_STAGE_GRAPH_PASS exact_header=1 texture_owner=1",flush=True)

    if sha == "0267753219c4b6a6f3fa086a356b698cd5295f78":
        env = ROOT/"vendor/encore-active/eden-core/src/video_core/shader_environment.cpp"
        if gitblob(env) != "8b4e883aaad5507652e13be211581e4965b7fe89":
            raise RuntimeError("Unreviewed null-TIC shader environment owner")
        rows = [r for r in db if Path(r["file"]).parts[-2:] == ("video_core","shader_environment.cpp")]
        if len(rows) != 1 or Path(rows[0]["file"]).resolve() != env.resolve():
            raise RuntimeError("Wrong or duplicate shader environment owner")
        shader_labels.add("shader_environment_null_tic")
        selected.append(("shader_environment_null_tic", rows[0]))
        print("R457_NATIVE_NULL_TIC_GRAPH_PASS exact_owner=1",flush=True)

    # Qualify existing source owners first even when the new sparse TU has a
    # target-SDK header problem; never stop before recording their verdict.
    selected.sort(key=lambda pair: pair[0] == "ns2_sparse_guest.cpp")
    subprocess.run(["ninja","-C",str(native),"-t","targets","all"],
                   check=True,stdout=subprocess.DEVNULL,timeout=30)
    for label,row in selected:
        command=args(row)
        native_definition = any(x=="-DPS5_NATIVE" or x.startswith("-DPS5_NATIVE=") for x in command)
        if label in storage_labels:
            # CMake deliberately scopes PS5_NATIVE to the platform-specific
            # sparse owners. The six common storage TUs have no such guard.
            # Assert the genuine cross target instead of injecting a definition
            # that production core does not use.
            if native_definition:
                raise RuntimeError(label+" unexpected PS5_NATIVE on common storage TU")
            if not any(x=="--target=x86_64-sie-ps5" or
                       (x in ("-target","--target") and i+1<len(command) and
                        command[i+1]=="x86_64-sie-ps5") for i,x in enumerate(command)):
                raise RuntimeError(label+" missing real PS5 compiler target")
        elif label in shader_labels:
            if not any(x=="--target=x86_64-sie-ps5" or
                       (x in ("-target","--target") and i+1<len(command) and
                        command[i+1]=="x86_64-sie-ps5") for i,x in enumerate(command)):
                raise RuntimeError(label+" missing real PS5 compiler target")
        elif not native_definition:
            raise RuntimeError(label+" missing PS5_NATIVE")
        if label not in shader_labels and not any(x.startswith("-DEDEN_NS2_SPARSE_BACKING") for x in command):
            raise RuntimeError(label+" missing production sparse backing")
        print("R457_NS2_SPARSE_NATIVE_GRAPH_PASS",label,row["file"],flush=True)
        cleaned=[]
        i=0
        while i<len(command):
            if command[i] in ("-o","-MF","-MT","-MQ"):
                if i+1>=len(command): raise RuntimeError(label+" dangling compile flag")
                i+=2;continue
            if command[i] in ("-c","-MD","-MMD","-MP"):
                i+=1;continue
            cleaned.append(command[i]);i+=1
        # The native graph may have PS5_NATIVE defined yet still inherit
        # incomplete C-header search paths. Record the *real* compiler
        # target/sysroot without silently introducing Linux libc into the
        # purported PS5 ABI. A separate non-accepting diagnostic can show
        # whether the C++ changes themselves then have syntax errors.
        markers=[flag for flag in cleaned if
                 flag.startswith(("--target","-target","--sysroot","-isysroot",
                                  "-nostdinc","-stdlib","-isystem"))]
        print("R457_NS2_SPARSE_NATIVE_TOOLCHAIN",label,
              "compiler="+cleaned[0], "flags="+repr(markers[:20]),flush=True)
        # The native PS5 SDK C headers must be the only C-library headers.
        # Clang's implicit Linux search path cannot establish PS5 syntax,
        # even with a PS5 target triple. Keep every CMake-selected include
        # and definition, add only Clang's target builtin headers explicitly.
        import os
        sdk=Path(os.environ["PS5_PAYLOAD_SDK"]).resolve()
        c_root=sdk/"target/include"
        assert (c_root/"stdlib.h").is_file() and (c_root/"sys/cdefs.h").is_file(), (
            "Incomplete native PS5 FreeBSD C header distribution")
        compiler=Path(cleaned[0])
        resource_dir=Path(subprocess.check_output(
            [str(compiler), "-print-resource-dir"],text=True).strip())/"include"
        assert resource_dir.is_dir(), "Native Clang compiler resource headers missing"
        # A configured target must not silently pick any Linux libc header.
        # Show the exact contaminated search flags, not just an opaque failure.
        host_includes=[]
        for pos,flag in enumerate(cleaned):
            if flag in ("-isystem","-I","-idirafter","-iquote") and pos+1<len(cleaned):
                path=cleaned[pos+1]
                if path.startswith(("/usr/include","/usr/local/include")):
                    host_includes.append((flag,path))
            elif flag.startswith(("-I/usr/include","-isystem/usr/include",
                                  "-I/usr/local/include","-isystem/usr/local/include")):
                host_includes.append(("inline",flag))
        print("R457_NS2_NATIVE_INCLUDE_PROVENANCE", label,
              "host_include_flags="+repr(host_includes),
              "sdk_c_headers="+str(c_root),
              "sdk_stdlib="+str((c_root/"stdlib.h").is_file()),flush=True)
        if host_includes:
            raise RuntimeError(label+" configured PS5 native graph contains host libc "+repr(host_includes))
        strict=cleaned+["-nostdinc","-isystem",str(resource_dir),"-fsyntax-only"]
        if label == "shader_texture_phi_bfs":
            strict.append("-H") # record which real header Clang actually includes
        p=subprocess.run(strict,cwd=row["directory"],
                         capture_output=True,text=True,timeout=210)
        if p.returncode:
            if "bits/libc-header-start.h" in p.stderr:
                # Host-only header-path experiment, never accepted as a
                # native SDK success. Continue the strict gate after it.
                mixed=cleaned+["-isystem","/usr/include/x86_64-linux-gnu",
                               "-fsyntax-only"]
                diagnostic=subprocess.run(mixed,cwd=row["directory"],
                           capture_output=True,text=True,timeout=210)
                print("R457_NS2_SPARSE_HOST_LIBC_DIAGNOSTIC",label,
                      "status="+str(diagnostic.returncode),
                      "NOT_REAL_PS5_ABI",flush=True)
                if diagnostic.returncode:
                    print(diagnostic.stderr[-3500:],file=sys.stderr,flush=True)
            raise RuntimeError(label+" genuine SDK syntax: "+p.stderr[-8500:])
        if label == "shader_texture_phi_bfs":
            if not any(str(bfs_header) in line and line.lstrip().startswith(".")
                       for line in p.stderr.splitlines()):
                raise RuntimeError("Actual compiler did not include the staged adaptive BFS header")
            print("R457_NATIVE_BFS_ACTUAL_HEADER_PASS",bfs_header,flush=True)
        # Do not discard diagnostics from successful syntax compiles.
        warnings = [line for line in p.stderr.splitlines() if "warning:" in line]
        for line in warnings:
            print("R457_NATIVE_SYNTAX_WARNING", label, line, flush=True)
        print("R457_NATIVE_SYNTAX_WARNING_COUNT", label, len(warnings),flush=True)
        print("R457_NS2_SPARSE_NATIVE_SYNTAX_PASS",label,flush=True)
        if label in storage_labels:
            print("R457_NATIVE_STORAGE_SYNTAX_PASS",label,flush=True)
    print("R457_NS2_SPARSE_ACTUAL_PS5_CMAKE_AND_6_TUS_PASS no link/gameplay",flush=True)
    if storage_labels:
        print("R457_NATIVE_STORAGE_ACTUAL_PS5_CMAKE_AND_6_TUS_PASS no link/gameplay",flush=True)

if __name__=="__main__":
    try: main()
    except Exception as e:
        print("R457_NS2_SPARSE_NATIVE_FAIL",e,file=sys.stderr,flush=True)
        raise SystemExit(1)
