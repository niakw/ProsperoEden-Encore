#!/usr/bin/env python3
"""Compile real upstream Ampere ISA and native address-map logic with synthetic fixtures."""
from pathlib import Path
import subprocess
import shutil
import tempfile
import sys

ROOT=Path(__file__).resolve().parent.parent
SOURCE=ROOT/"tools/ns2/test_ampere_isa.cpp"
OVERLAY=ROOT/"headless/ns2/gpu"
EDEN=ROOT/"vendor/sources/eden/src"
def main()->int:
    compiler=shutil.which("clang++") or shutil.which("g++")
    if compiler is None:
        print("Missing compiler",file=sys.stderr)
        return 2
    with tempfile.TemporaryDirectory(prefix="encore-ampere-") as tmp:
        for opt in ("-O0","-O2"):
            binary=Path(tmp)/("test"+opt)
            subprocess.run([compiler,"-std=c++20",opt,"-Wall","-Wextra","-Werror",
                            "-pedantic","-fsanitize=undefined","-fno-sanitize-recover=all",
                            "-I",str(OVERLAY),"-I",str(EDEN),str(SOURCE),
                            "-o",str(binary)],check=True)
            subprocess.run([str(binary)],check=True)
            print(f"Ampere ISA/address map {opt}: PASS")
    print("Host ISA classification only; no shader translation, Vulkan or PS5 runtime.")
    return 0
if __name__=="__main__":
    raise SystemExit(main())
