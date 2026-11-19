#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Qualify the production-selected reviewed Switch 2 A64 v8.1-v8.5 owner set.

Vendor #192 carries exact reviewed Lichii 11aac324 sources. This host gate proves
that the release CMake stages all of them, enables EDEN_NS2_A64_V81_V85 only on
Encore's maintained A64 translation unit, compiles that real translation unit,
and exposes the expected decoder families. It does not claim PS5/game success.
"""
from pathlib import Path
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
CMAKE = (ROOT / "headless/CMakeLists.txt").read_text()
SCRIPT = ROOT / "headless/shared_a64_ldapr.cmake"
BASE = ROOT / "vendor/sources/eden/src/dynarmic/src"
REL = Path("dynarmic/frontend/A64")
STATIC = ROOT / "vendor/encore-active/ns2-runtime/ldapr/maintained" / REL
TRANSLATOR = ROOT / "vendor/encore-active/eden-core/src/dynarmic/frontend/A64/translate/a64_translate.cpp"
FILES = (
    "decoder/a64.h",
    "decoder/a64.inc",
    "translate/impl/impl.h",
    "translate/impl/load_store_exclusive.cpp",
    "translate/impl/a64_branch.cpp",
    "translate/impl/load_store_atomic.cpp",
    "translate/impl/memory_tagging.cpp",
    "translate/impl/pointer_authentication.cpp",
)

assert 'set(EDEN_SHARED_NS2_A64_V81_V85 ON)' in CMAKE
assert 'if(PS5_NATIVE AND EDEN_REVIEWED_DUAL_NPDM)' in CMAKE
assert 'include("${CMAKE_CURRENT_LIST_DIR}/shared_a64_ldapr.cmake")' in CMAKE
assert 'target_include_directories(dynarmic BEFORE PRIVATE "${EDEN_A64_LDAPR_OUTPUT_ROOT}")' in CMAKE
source_guard = '''set_property(SOURCE "${EDEN_MAINTAINED_SCALAR_TRANSLATOR}"
        TARGET_DIRECTORY dynarmic APPEND PROPERTY
        COMPILE_DEFINITIONS "EDEN_NS2_A64_V81_V85=1")'''
assert CMAKE.count(source_guard) == 1
assert "target_compile_definitions(dynarmic PRIVATE EDEN_NS2_A64_V81_V85" not in CMAKE
assert "target_compile_definitions(core PRIVATE EDEN_NS2_A64_V81_V85" not in CMAKE
assert "EDEN_NS2_A64_EXPERIMENTAL" not in CMAKE
assert all((STATIC / f).is_file() for f in FILES), "vendor #192 files not pinned by engine"
assert TRANSLATOR.is_file()

decoder = (STATIC / "decoder/a64.inc").read_text()
for marker in (
    'INST(LDAPR_sz, "LDAPRB, LDAPRH, LDAPR"',
    'INST(AtomicMemOp, "LDADD/LDCLR/LDEOR/LDSET/LDSMAX/LDSMIN/LDUMAX/LDUMIN/SWP"',
    'INST(CompareAndSwap, "CASB, CASH, CAS"',
    'INST(CompareAndSwapPair, "CASP"',
    'INST(PACAUT_reg, "PACIA/PACIB/PACDA/PACDB/AUTIA/AUTIB/AUTDA/AUTDB"',
    'INST(RETA, "RETAA, RETAB"',
    'INST(BRA_BLRA, "BRAA/BRAB/BLRAA/BLRAB (+Z)"',
    'INST(LDRA, "LDRAA, LDRAB"',
    'INST(STG_family, "STG/STZG/ST2G/STZ2G/LDG"',
    'INST(ADDG, "ADDG"',
):
    assert decoder.count(marker) == 1, marker

translator = TRANSLATOR.read_text()
guard = "#if defined(EDEN_NS2_A64_V81_V85)"
assert translator.count(guard) == 1
guarded = translator.split(guard, 1)[1].split("#endif", 1)[0]
for name in ("load_store_atomic.cpp", "memory_tagging.cpp", "pointer_authentication.cpp"):
    assert guarded.count(name) == 1

def transform(base: Path, out: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["cmake", f"-DEDEN_A64_LDAPR_SOURCE_ROOT={base}",
         f"-DEDEN_A64_LDAPR_OUTPUT_ROOT={out}", "-P", str(SCRIPT)],
        capture_output=True, text=True, timeout=30,
    )

TEST_CPP = r'''
#include <cassert>
#include <cstdint>
#include <string_view>
#include "dynarmic/frontend/A64/decoder/a64.h"
#include "dynarmic/frontend/A64/translate/impl/impl.h"

static void contains(std::uint32_t instruction, std::string_view needle) {
    using Dynarmic::A64::TranslatorVisitor;
    const auto op = Dynarmic::A64::GetName<TranslatorVisitor>(instruction);
    assert(op);
    assert(std::string_view{*op}.find(needle) != std::string_view::npos);
}

int main() {
    contains(0xF8BFC000U, "LDAPR");
    contains(0xC8A07C00U, "CAS");
    contains(0xF8200000U, "LDADD");
    contains(0xD65F0BFFU, "RETAA");
}
'''

def main() -> int:
    compiler = shutil.which("clang++") or shutil.which("g++")
    assert compiler, "C++20 compiler required"
    env = os.environ.copy()
    sdk15 = Path("/Library/Developer/CommandLineTools/SDKs/MacOSX15.4.sdk")
    sdk26 = Path("/Library/Developer/CommandLineTools/SDKs/MacOSX26.5.sdk")
    if sdk15.is_dir():
        env["SDKROOT"] = str(sdk15)
    target = []
    if sys.platform == "darwin" and sdk26.is_dir():
        target = ["-target", "arm64-apple-macos15", "-nostdinc++",
                  "-isystem", str(sdk26 / "usr/include/c++/v1")]

    deps = ROOT / "vendor/sources/eden-cpm"
    additional = [
        BASE,
        ROOT / "vendor/sources/eden/src",
        ROOT / "vendor/sources/fmt/include",
    ] + list((deps / "boost/boost-1.90.0/libs").glob("*/include"))

    with tempfile.TemporaryDirectory(prefix="encore-a64-v81-v85-") as td:
        temp = Path(td)
        generated = temp / "include"
        staged = transform(BASE, generated)
        assert staged.returncode == 0, staged.stderr

        actual = {str(p.relative_to(generated)) for p in generated.rglob("*") if p.is_file()}
        expected = {str(REL / f) for f in FILES}
        assert actual == expected, (sorted(actual), sorted(expected))
        for relative in FILES:
            assert (generated / REL / relative).read_bytes() == (STATIC / relative).read_bytes(), relative
        print("P0_NS2_A64_V81_V85_STAGED_EXACT_PASS files=8", flush=True)

        include_args = ["-I" + str(generated)] + [
            "-I" + str(p) for p in additional if p.is_dir()
        ]
        syntax = subprocess.run(
            [compiler, "-std=c++20", "-O0", "-fsyntax-only",
             "-Wno-unused-parameter", "-DFMT_HEADER_ONLY",
             "-DEDEN_NS2_A64_V81_V85=1", *target, *include_args, str(TRANSLATOR)],
            capture_output=True, text=True, env=env, timeout=120,
        )
        assert syntax.returncode == 0, syntax.stderr[-7000:]
        print("P0_NS2_A64_V81_V85_REAL_TRANSLATOR_PASS macro=source_scoped", flush=True)

        decoder_test = temp / "decoder.cpp"
        decoder_test.write_text(TEST_CPP)
        for opt in ("-O0", "-O2"):
            exe = temp / ("decoder" + opt)
            built = subprocess.run(
                [compiler, "-std=c++20", opt, "-Wall", "-Wextra", "-Werror",
                 "-fsanitize=undefined", "-fno-sanitize-recover=all",
                 *target, *include_args, str(decoder_test), "-o", str(exe)],
                capture_output=True, text=True, env=env, timeout=100,
            )
            assert built.returncode == 0, built.stderr[-6000:]
            run = subprocess.run([str(exe)], capture_output=True, text=True, env=env, timeout=20)
            assert run.returncode == 0, (run.stdout, run.stderr)
            print("P0_NS2_A64_V81_V85_REAL_DECODER_PASS", opt, flush=True)

    print("Host/source qualified only; native PS5 package and MKW/Bananza remain unverified")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
