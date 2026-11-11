#!/usr/bin/env python3
"""Real configured PS5 native CMake graph and syntax; no ELF, link, gameplay."""
from __future__ import annotations
import json
from pathlib import Path
import shlex
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
VENDOR="0940d6ef9d120fb3a39afadad5de690b0f0f4133"
OWNERS=(ROOT/"src/ns2_sparse_guest.cpp",
        ROOT/"src/host_memory.cpp")
NATIVE_GUEST=(ROOT/"vendor/encore-active/eden-core/src/core/memory_native_a32.cpp",
              ROOT/"vendor/encore-active/eden-core/src/core/memory_native_standard.cpp")

def args(row):
    return list(row["arguments"]) if "arguments" in row else shlex.split(row["command"])

def main():
    native=Path(sys.argv[1]).resolve()
    sha=subprocess.check_output(["git","rev-parse","HEAD:vendor"],cwd=ROOT,text=True).strip()
    if sha!=VENDOR: raise RuntimeError("Wrong vendor physical owner: "+sha)
    cache=(native/"CMakeCache.txt").read_text()
    if "EDEN_RESEARCH_NS2_SPARSE_GUEST_BACKING:BOOL=ON" not in cache:
        raise RuntimeError("CMake sparse opt-in not enabled")
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
    subprocess.run(["ninja","-C",str(native),"-t","targets","all"],
                   check=True,stdout=subprocess.DEVNULL,timeout=30)
    for label,row in selected:
        command=args(row)
        if not any(x=="-DPS5_NATIVE" or x.startswith("-DPS5_NATIVE=") for x in command):
            raise RuntimeError(label+" missing PS5_NATIVE")
        if not any(x.startswith("-DEDEN_RESEARCH_NS2_SPARSE_GUEST_BACKING") for x in command):
            raise RuntimeError(label+" missing sparse opt-in")
        print("R457_NS2_SPARSE_NATIVE_GRAPH_PASS",label,row["file"],flush=True)
        cleaned=[]
        i=0
        while i<len(command):
            if command[i]=="-o": i+=2;continue
            if command[i]=="-c": i+=1;continue
            cleaned.append(command[i]);i+=1
        p=subprocess.run(cleaned+["-fsyntax-only"],cwd=row["directory"],
                         capture_output=True,text=True,timeout=210)
        if p.returncode: raise RuntimeError(label+" syntax: "+p.stderr[-8500:])
        print("R457_NS2_SPARSE_NATIVE_SYNTAX_PASS",label,flush=True)
    print("R457_NS2_SPARSE_ACTUAL_PS5_CMAKE_AND_3_TUS_PASS no link/gameplay",flush=True)

if __name__=="__main__":
    try: main()
    except Exception as e:
        print("R457_NS2_SPARSE_NATIVE_FAIL",e,file=sys.stderr,flush=True)
        raise SystemExit(1)
