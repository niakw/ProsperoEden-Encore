#!/usr/bin/env python3
"""Retain the archived A64 research decoder while production uses reviewed v8.1-v8.5 owners."""
from __future__ import annotations
from pathlib import Path
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent
ARCHIVE = ROOT / "vendor/encore-active/ns2-a64"
PROD = ROOT / "vendor/encore-active/ns2-runtime/ldapr/maintained/dynarmic/frontend/A64"
CMAKE = (ROOT / "headless/CMakeLists.txt").read_text()
DEC = (ARCHIVE / "dynarmic/frontend/A64/decoder/a64.inc").read_text()
HEADER = (ARCHIVE / "dynarmic/frontend/A64/decoder/a64.h").read_text()
PROD_DEC = (PROD / "decoder/a64.inc").read_text()
PROD_ATOMIC = (PROD / "translate/impl/load_store_atomic.cpp").read_text()
PROD_POINTER = (PROD / "translate/impl/pointer_authentication.cpp").read_text()
PROD_MTE = (PROD / "translate/impl/memory_tagging.cpp").read_text()

def main() -> int:
    required_prod = (
        'INST(LDAPR_sz, "LDAPRB, LDAPRH, LDAPR"',
        'INST(AtomicMemOp, "LDADD/LDCLR/LDEOR/LDSET/LDSMAX/LDSMIN/LDUMAX/LDUMIN/SWP"',
        'INST(CompareAndSwap, "CASB, CASH, CAS"',
        'INST(CompareAndSwapPair, "CASP"',
        'INST(PACAUT_reg, "PACIA/PACIB/PACDA/PACDB/AUTIA/AUTIB/AUTDA/AUTDB"',
        'INST(RETA, "RETAA, RETAB"',
        'INST(STG_family, "STG/STZG/ST2G/STZ2G/LDG"',
    )
    if (
        "EDEN_NS2_A64_EXPERIMENTAL" in CMAKE
        or 'set(EDEN_SHARED_NS2_A64_V81_V85 ON)' not in CMAKE
        or 'target_compile_definitions(dynarmic PRIVATE EDEN_NS2_A64_V81_V85=1)' not in CMAKE
        or 'target_include_directories(dynarmic BEFORE PRIVATE "${EDEN_A64_V81_V85_OUTPUT_ROOT}")' not in CMAKE
        or not (ROOT / "tools/ns2/check_shared_a64_v81_v85_host.py").is_file()
        or '#include "./a64.inc"' not in HEADER
        or any(marker not in PROD_DEC for marker in required_prod)
        or 'INST(LDAPR, "LDAPR"' in PROD_DEC
        or "IR::Term::CheckBit" not in PROD_ATOMIC
        or "TranslatorVisitor::CompareAndSwapPair" not in PROD_ATOMIC
        or "TranslatorVisitor::RETA" not in PROD_POINTER
        or "TranslatorVisitor::PACGA" not in PROD_POINTER
        or "TranslatorVisitor::STG_family" not in PROD_MTE
        or "TranslatorVisitor::ADDG" not in PROD_MTE
    ):
        print("Production ARMv8.1-v8.5 ownership is incomplete", file=sys.stderr)
        return 2

    # Preserve the old research decoder only as a historical comparison oracle.
    # It must remain unselected by CMake.
    for opcode in ("CAS", "LDADD", "LDCLR", "LDEOR", "LDSET", "SWP", "SWPB", "SWPH"):
        if f"INST({opcode}," not in DEC:
            print(f"Archived A64 oracle lost {opcode}", file=sys.stderr)
            return 2

    compiler = shutil.which("clang++") or shutil.which("g++")
    if not compiler:
        print("Missing C++20 compiler", file=sys.stderr)
        return 2
    with tempfile.TemporaryDirectory(prefix="ns2-a64-archive-") as tmp:
        for opt in ("-O0", "-O2"):
            target = str(Path(tmp) / ("test" + opt))
            cmd = [
                compiler, "-std=c++20", "-Wall", "-Wextra", "-Werror", "-pedantic",
                "-fsanitize=undefined", "-fno-sanitize-recover=all", opt,
                "-I", str(ARCHIVE), str(ROOT / "tools/ns2/test_reta_decode.cpp"), "-o", target,
            ]
            subprocess.run(cmd, check=True)
            subprocess.run([target], check=True, env={**os.environ, "UBSAN_OPTIONS": "halt_on_error=1"})
            print(f"NS2 archived A64 decoder oracle {opt}: PASS")

    print("NS2_A64_PRODUCTION_PROMOTION_SOURCE_PASS archived_selector=off reviewed_v81_v85=on")
    print("No native PS5 execution or gameplay result inferred")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
