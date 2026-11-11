#!/usr/bin/env python3
"""Real configured PS5 native CMake graph and syntax; no ELF, link, gameplay."""
from __future__ import annotations
import json
from pathlib import Path
import shlex
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
VENDOR="87ef285eae969388a7c9ad98467ff7fd6c314cba"
OWNERS=(ROOT/"src/ns2_sparse_guest.cpp",
        ROOT/"src/host_memory.cpp")
NATIVE_GUEST=(ROOT/"vendor/encore-active/eden-core/src/core/memory_native_a32.cpp",
              ROOT/"vendor/encore-active/eden-core/src/core/memory_native_standard.cpp")
NATIVE_KERNEL=ROOT/"vendor/encore-active/ns2-runtime/sparse-residency/core/hle/kernel/k_memory_manager.cpp"

def args(row):
    return list(row["arguments"]) if "arguments" in row else shlex.split(row["command"])

def main():
    native=Path(sys.argv[1]).resolve()
    sha=subprocess.check_output(["git","rev-parse","HEAD:vendor"],cwd=ROOT,text=True).strip()
    if sha!=VENDOR: raise RuntimeError("Wrong vendor physical owner: "+sha)
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
    kernel_rows=[r for r in db if Path(r["file"]).resolve()==NATIVE_KERNEL.resolve()]
    if len(kernel_rows)!=1: raise RuntimeError(f"Expected exactly one real native kernel direct owner, got {len(kernel_rows)}")
    selected.append(("native_kernel_direct",kernel_rows[0]))
    # Qualify existing source owners first even when the new sparse TU has a
    # target-SDK header problem; never stop before recording their verdict.
    selected.sort(key=lambda pair: pair[0] == "ns2_sparse_guest.cpp")
    subprocess.run(["ninja","-C",str(native),"-t","targets","all"],
                   check=True,stdout=subprocess.DEVNULL,timeout=30)
    for label,row in selected:
        command=args(row)
        if not any(x=="-DPS5_NATIVE" or x.startswith("-DPS5_NATIVE=") for x in command):
            raise RuntimeError(label+" missing PS5_NATIVE")
        if not any(x.startswith("-DEDEN_NS2_SPARSE_BACKING") for x in command):
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
        p=subprocess.run(cleaned+["-fsyntax-only"],cwd=row["directory"],
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
        print("R457_NS2_SPARSE_NATIVE_SYNTAX_PASS",label,flush=True)
    print("R457_NS2_SPARSE_ACTUAL_PS5_CMAKE_AND_3_TUS_PASS no link/gameplay",flush=True)

if __name__=="__main__":
    try: main()
    except Exception as e:
        print("R457_NS2_SPARSE_NATIVE_FAIL",e,file=sys.stderr,flush=True)
        raise SystemExit(1)
