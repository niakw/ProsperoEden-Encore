#!/usr/bin/env python3
"""Keep the historical A64 research decoder oracle while production uses vendor #192.

The old research table remains a useful independent decode witness. Production
is no longer intentionally limited to LDAPR/RETAA: the reviewed Lichii
11aac324 ARMv8.1-v8.5 set is selected by the native dual-NPDM build.
"""
from pathlib import Path
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent
RESEARCH = ROOT / "vendor/encore-active/ns2-a64"
CMAKE = (ROOT / "headless/CMakeLists.txt").read_text()
DEC = (RESEARCH / "dynarmic/frontend/A64/decoder/a64.inc").read_text()
HEADER = (RESEARCH / "dynarmic/frontend/A64/decoder/a64.h").read_text()
PROD = ROOT / "vendor/encore-active/ns2-runtime/ldapr/maintained/dynarmic/frontend/A64"
PROD_DEC = (PROD / "decoder/a64.inc").read_text()
PROD_POINTER = (PROD / "translate/impl/pointer_authentication.cpp").read_text()
PROD_ATOMIC = (PROD / "translate/impl/load_store_atomic.cpp").read_text()
PROD_MTE = (PROD / "translate/impl/memory_tagging.cpp").read_text()

def main() -> int:
    required_cmake = (
        "set(EDEN_SHARED_NS2_A64_V81_V85 ON)",
        "target_compile_definitions(dynarmic PRIVATE EDEN_NS2_A64_V81_V85=1)",
        'target_include_directories(dynarmic BEFORE PRIVATE "${EDEN_A64_V81_V85_OUTPUT_ROOT}")',
    )
    if ("EDEN_NS2_A64_EXPERIMENTAL" in CMAKE or
            any(marker not in CMAKE for marker in required_cmake) or
            '#include "./a64.inc"' not in HEADER):
        print("Production A64 v8.1-v8.5 selection missing or research flag leaked", file=sys.stderr)
        return 2

    # Retain the old, separately authored decoder as an independent oracle.
    for opcode in ("CAS", "LDADD", "LDCLR", "LDEOR", "LDSET", "SWP", "SWPB", "SWPH"):
        if f"INST({opcode}," not in DEC:
            print(f"Archived A64 oracle lost {opcode}", file=sys.stderr)
            return 2

    # Production must now contain the exact grouped upstream instruction families,
    # not the former five-file LDAPR-only overlay.
    for marker in (
        'INST(LDAPR_sz, "LDAPRB, LDAPRH, LDAPR"',
        'INST(AtomicMemOp, "LDADD/LDCLR/LDEOR/LDSET/LDSMAX/LDSMIN/LDUMAX/LDUMIN/SWP"',
        'INST(CompareAndSwap, "CASB, CASH, CAS"',
        'INST(CompareAndSwapPair, "CASP"',
        'INST(PACGA, "PACGA"',
        'INST(RETA, "RETAA, RETAB"',
        'INST(STG_family, "STG/STZG/ST2G/STZ2G/LDG"',
    ):
        if PROD_DEC.count(marker) != 1:
            print(f"Production A64 decoder missing {marker}", file=sys.stderr)
            return 2
    if "TranslatorVisitor::RETA" not in PROD_POINTER or "TranslatorVisitor::PACGA" not in PROD_POINTER:
        return 2
    if "TranslatorVisitor::CompareAndSwapPair" not in PROD_ATOMIC or "AtomicFinish(*this, status)" not in PROD_ATOMIC:
        return 2
    if "TranslatorVisitor::STG_family" not in PROD_MTE or "TranslatorVisitor::ADDG" not in PROD_MTE:
        return 2

    provenance = subprocess.run(
        [sys.executable, "-B", str(ROOT / "vendor/tests/ns2_a64_v81_v85_source.py")],
        cwd=ROOT, capture_output=True, text=True, timeout=30,
    )
    if provenance.returncode != 0:
        print(provenance.stderr[-5000:], file=sys.stderr)
        return provenance.returncode

    compiler = shutil.which("clang++") or shutil.which("g++")
    if not compiler:
        print("Missing C++20 compiler", file=sys.stderr)
        return 2
    with tempfile.TemporaryDirectory(prefix="ns2-reta-oracle-") as tmp:
        for opt in ("-O0", "-O2"):
            target = str(Path(tmp) / ("test" + opt))
            cmd = [
                compiler, "-std=c++20", "-Wall", "-Wextra", "-Werror", "-pedantic",
                "-fsanitize=undefined", "-fno-sanitize-recover=all",
                opt, "-I", str(RESEARCH),
                str(ROOT / "tools/ns2/test_reta_decode.cpp"), "-o", target,
            ]
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            subprocess.run(
                [target], check=True,
                env={**os.environ, "UBSAN_OPTIONS": "halt_on_error=1"},
                capture_output=True, text=True,
            )
            print(f"NS2_A64_ARCHIVED_DECODER_ORACLE_PASS {opt}")
    print("NS2_A64_PRODUCTION_V81_V85_SOURCE_PASS upstream=Lichii-11aac324 runtime_ps5=unverified")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
