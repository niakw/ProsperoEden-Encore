#!/usr/bin/env python3
"""Compile the real pinned Eden Maxwell frontend and IR passes, with no spies."""
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import os
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "vendor/sources/eden/src"
SHADER = SRC / "shader_recompiler"
OUT = ROOT / "build-ns2-real-ir"
def run(args):
    p = subprocess.run(args,cwd=ROOT,capture_output=True,text=True)
    if p.returncode:
        print("FAILED:"," ".join(map(str,args)),file=sys.stderr)
        print(p.stdout[-5000:],p.stderr[-15000:],file=sys.stderr)
        raise RuntimeError("real IR build or run failed")
    return p
def main():
    cxx = shutil.which(os.environ.get("CXX","g++"))
    if not cxx: raise RuntimeError("missing C++ compiler")
    fmt = ROOT / "build-ns2-a64/fmt/include"
    cmake = SHADER / "CMakeLists.txt"
    if not cmake.is_file() or not (fmt / "fmt/format.h").is_file():
        raise RuntimeError("missing pinned submodules or fmt")
    listing = cmake.read_text().split("add_library(shader_recompiler STATIC",1)[1].split("\n)",1)[0]
    names = re.findall(r"^\s*((?:frontend|ir_opt)/[^\s()]+\.cpp)\s*$",listing,re.M)
    if len(names)<100 or "frontend/maxwell/translate_program.cpp" not in names:
        raise RuntimeError("unexpected pinned CMake shader source list")
    overlay = ROOT / "headless/ns2/ampere/shader_recompiler/frontend/ampere"
    sources = [SHADER / name for name in names] + [
        overlay / (name+".cpp") for name in
        ("ir_bridge","maxwell_environment","maxwell_image","lower_bridge","probe")
    ] + [SRC / "common/settings_common.cpp",
        ROOT / "tools/ns2/jit-host/common_shim.cpp",
         ROOT / "tools/ns2/test_ampere_real_ir.cpp"]
    if any(not x.is_file() for x in sources):
        raise RuntimeError("missing pinned shader source")
    OUT.mkdir(parents=True,exist_ok=True)
    flags = [cxx,"-std=c++20","-O0","-g0","-DFMT_HEADER_ONLY",
             "-ffunction-sections","-fdata-sections","-Wno-unused-parameter",
             "-pthread","-I"+str(fmt),"-I"+str(ROOT/"headless/ns2/ampere"),
             "-I"+str(SRC),"-I"+str(SRC/"dynarmic/src")]
    jobs = [(s,OUT/("%03d.o"%i)) for i,s in enumerate(sources)]
    print("Compile true Eden Maxwell/IR sources:",len(jobs),flush=True)
    with ThreadPoolExecutor(max_workers=2) as pool:
        future = {pool.submit(run,flags+["-c",str(src),"-o",str(obj)]):src for src,obj in jobs}
        for f in as_completed(future):
            try: f.result()
            except Exception:
                print("Source:",future[f],file=sys.stderr)
                for other in future: other.cancel()
                raise
    exe=OUT/"ns2-real-ir"
    run([cxx,"-pthread","-Wl,--gc-sections","-o",str(exe)]+
        [str(obj) for _,obj in jobs]+["-latomic"])
    print(run([str(exe)]).stdout,end="")
if __name__=="__main__":
    try: main()
    except Exception as exc:
        print(exc,file=sys.stderr)
        sys.exit(1)
