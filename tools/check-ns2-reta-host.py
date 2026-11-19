#!/usr/bin/env python3
"""Retain the archived A64 oracle while production uses reviewed vendor #192 coverage."""
from __future__ import annotations
from pathlib import Path
import os
import shutil
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parent.parent
BASE=ROOT/"vendor/encore-active/ns2-a64"
CMAKE=(ROOT/"headless/CMakeLists.txt").read_text()
BRANCH=(BASE/"dynarmic/frontend/A64/translate/impl/a64_branch.cpp").read_text()
DEC=(BASE/"dynarmic/frontend/A64/decoder/a64.inc").read_text()
HEADER=(BASE/"dynarmic/frontend/A64/decoder/a64.h").read_text()
PROD=ROOT/"vendor/encore-active/ns2-runtime/ldapr/maintained/dynarmic/frontend/A64"
PROD_DEC=(PROD/"decoder/a64.inc").read_text()
PROD_BRANCH=(PROD/"translate/impl/a64_branch.cpp").read_text()

def main() -> int:
    if ('EDEN_NS2_A64_EXPERIMENTAL' in CMAKE
        or 'set(EDEN_SHARED_NS2_A64_V81_V85 ON)' not in CMAKE
        or 'target_include_directories(dynarmic BEFORE PRIVATE "${EDEN_A64_LDAPR_OUTPUT_ROOT}")' not in CMAKE
        or not (ROOT/"tools/ns2/check_shared_a64_ldapr_host.py").is_file()
        or 'EDEN_NS2_A64_V81_V85=1' not in CMAKE
        or '#include "./a64.inc"' not in HEADER
        or 'INST(RETA, "RETA", "110101100101111100001M1111111111")' not in DEC
        or 'INST(LDAPR, "LDAPR", "ss11100010111111110000nnnnnttttt")' not in DEC
        or any(('INST('+opcode+',') not in DEC for opcode in ('CAS','LDADD','LDCLR','LDEOR','LDSET','SWP','SWPB','SWPH'))
        or 'bool TranslatorVisitor::CAS(Imm<2> sz' not in (BASE/"dynarmic/frontend/A64/translate/impl/load_store_exclusive.cpp").read_text()
        or 'bool TranslatorVisitor::LDAPR(Imm<2> size, Reg Rn, Reg Rt)' not in (BASE/"dynarmic/frontend/A64/translate/impl/load_store_exclusive.cpp").read_text()
        or 'bool TranslatorVisitor::RETA(' not in BRANCH
        or 'return RET(Reg::R30);' not in BRANCH
        or '#if defined(EDEN_NS2_A64_EXPERIMENTAL)' not in BRANCH
        or 'INST(RETA, "RETAA, RETAB", "110101100101111100001M1111111111")' not in PROD_DEC
        or 'INST(CompareAndSwap, "CASB, CASH, CAS"' not in PROD_DEC
        or 'INST(AtomicMemOp, "LDADD/LDCLR/LDEOR/LDSET/LDSMAX/LDSMIN/LDUMAX/LDUMIN/SWP"' not in PROD_DEC
        or 'INST(PACAUT_reg, "PACIA/PACIB/PACDA/PACDB/AUTIA/AUTIB/AUTDA/AUTDB"' not in PROD_DEC
        or 'INST(STG_family, "STG/STZG/ST2G/STZ2G/LDG"' not in PROD_DEC
        or not (PROD/"translate/impl/load_store_atomic.cpp").is_file()
        or not (PROD/"translate/impl/pointer_authentication.cpp").is_file()
        or not (PROD/"translate/impl/memory_tagging.cpp").is_file()
        or 'EDEN_NS2_A64_EXPERIMENTAL' in PROD_BRANCH):
        print("Archived oracle or reviewed production A64 v8.1-v8.5 ownership missing",file=sys.stderr)
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
            print(f"NS2 A64 RETA/LDAPR/LSE opcode decoder table {opt}: PASS")
    print("Archived RETAA/LDAPR/LSE oracle retained; production selects reviewed vendor #192 A64 v8.1-v8.5 owners. No PS5 execution proof.")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
