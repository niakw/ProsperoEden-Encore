#!/usr/bin/env python3
"""Compile both Ampere ISA/address-map and decoder probes from the ONE renderer-selected owner."""
from pathlib import Path
import subprocess
import shutil
import tempfile
import sys

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "tools/ns2/test_ampere_isa.cpp"
PROBE_TEST = ROOT / "tools/ns2/test_ampere_isa_probe.cpp"
OVERLAY=ROOT/"headless/ns2/ampere"
PROBE = OVERLAY / "shader_recompiler/frontend/ampere/probe.cpp"
EDEN=ROOT/"vendor/sources/eden/src"

def main()->int:
    compiler=shutil.which("clang++") or shutil.which("g++")
    if compiler is None:
        print("Missing compiler",file=sys.stderr)
        return 2
    with tempfile.TemporaryDirectory(prefix="encore-ampere-") as tmp:
        for opt in ("-O0","-O2"):
            for name, source in (("isa-address-map", SOURCE), ("isa-probe", PROBE_TEST)):
                binary=Path(tmp)/(name+opt)
                subprocess.run([compiler,"-std=c++20",opt,"-Wall","-Wextra","-Werror",
                                "-pedantic","-fsanitize=undefined","-fno-sanitize-recover=all",
                                "-I",str(OVERLAY),"-I",str(EDEN),
                                "-I",str(ROOT/"build-ns2-a64/fmt/include"),
                                str(source),str(PROBE),"-o",str(binary)],check=True)
                subprocess.run([str(binary)],check=True)
                print(f"Canonical Ampere {name} {opt}: PASS")
    print("Host ISA/address-map only; no shader rendering, Vulkan, or PS5 runtime proof.")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
