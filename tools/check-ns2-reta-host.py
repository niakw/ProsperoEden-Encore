#!/usr/bin/env python3
"""Source-linked A64 RETAA/RETAB experimental decoder + owner test."""
from __future__ import annotations
from pathlib import Path
import os
import shutil
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parent.parent
BASE=ROOT/"headless/ns2/dynarmic"
CMAKE=(ROOT/"headless/CMakeLists.txt").read_text()
BRANCH=(BASE/"dynarmic/frontend/A64/translate/impl/a64_branch.cpp").read_text()
DEC=(BASE/"dynarmic/frontend/A64/decoder/a64.inc").read_text()
HEADER=(BASE/"dynarmic/frontend/A64/decoder/a64.h").read_text()

def main() -> int:
    if ('option(EDEN_NS2_RETA_EXPERIMENTAL' not in CMAKE
        or 'EDEN_NS2_RETA_EXPERIMENTAL OR' not in CMAKE
        or 'target_compile_definitions(dynarmic PRIVATE EDEN_NS2_RETA_EXPERIMENTAL=1)' not in CMAKE
        or '#include "./a64.inc"' not in HEADER
        or 'INST(RETA, "RETA", "110101100101111100001M1111111111")' not in DEC
        or 'bool TranslatorVisitor::RETA(' not in BRANCH
        or 'return RET(Reg::R30);' not in BRANCH
        or '#if defined(EDEN_NS2_RETA_EXPERIMENTAL)' not in BRANCH):
        print("RETA decoder/translation or experimental CMake ownership missing",file=sys.stderr)
        return 2
    compiler=shutil.which("clang++") or shutil.which("g++")
    if not compiler:
        print("Missing C++20 compiler",file=sys.stderr)
        return 2
    with tempfile.TemporaryDirectory(prefix="ns2-reta-") as tmp:
        for opt in ("-O0","-O2"):
            target=str(Path(tmp)/("test"+opt))
            cmd=[compiler,"-std=c++20","-Wall","-Wextra","-Werror","-pedantic",
                 "-fsanitize=undefined","-fno-sanitize-recover=all",
                 opt,"-I",str(BASE),
                 str(ROOT/"tools/ns2/test_reta_decode.cpp"),"-o",target]
            subprocess.run(cmd,check=True)
            subprocess.run([target],check=True,env={**os.environ,"UBSAN_OPTIONS":"halt_on_error=1"})
            print(f"NS2 RETAA/RETAB decoder table {opt}: PASS")
    print("Not full Dynarmic JIT/PS5 compilation or PAUTH verification")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
