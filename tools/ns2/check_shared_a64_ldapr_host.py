#!/usr/bin/env python3
"""P0.2: qualify production-selected ARMv8.1-v8.5 A64 coverage.

Vendor #192 is an exact backport of Lichii 11aac324 on the pinned Dynarmic
parent. This gate stages the exact maintained files selected by native CMake,
compiles the real maintained A64 translator with the production macro and
executes decoder probes for the major instruction families. It is a host
source/ABI proof, not PS5 gameplay proof.
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
ACTIVE = ROOT / "vendor/encore-active/ns2-runtime/ldapr/maintained" / REL
SELECTED_TRANSLATOR = (
    ROOT / "vendor/encore-active/eden-core/src/dynarmic/frontend/A64/translate/a64_translate.cpp"
)
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

assert "set(EDEN_SHARED_NS2_A64_V81_V85 ON)" in CMAKE
assert "if(PS5_NATIVE AND EDEN_REVIEWED_DUAL_NPDM)" in CMAKE
assert 'include("${CMAKE_CURRENT_LIST_DIR}/shared_a64_ldapr.cmake")' in CMAKE
assert 'target_include_directories(dynarmic BEFORE PRIVATE "${EDEN_A64_V81_V85_OUTPUT_ROOT}")' in CMAKE
assert "target_compile_definitions(dynarmic PRIVATE EDEN_NS2_A64_V81_V85=1)" in CMAKE
assert "EDEN_NS2_A64_EXPERIMENTAL" not in CMAKE
assert all((ACTIVE / f).is_file() for f in FILES), "vendor #192 maintained A64 files missing"
assert SELECTED_TRANSLATOR.is_file()

# Reuse the vendor's exact Lichii-parent/output blob provenance contract first.
vendor_source = subprocess.run(
    [sys.executable, "-B", str(ROOT / "vendor/tests/ns2_a64_v81_v85_source.py")],
    cwd=ROOT, capture_output=True, text=True, timeout=30
)
assert vendor_source.returncode == 0, vendor_source.stderr[-5000:]
assert "NS2_A64_V81_V85_SOURCE_PASS" in vendor_source.stdout

TEST_CPP = r"""
#include <cassert>
#include <cstdio>
#include <string_view>
#include "dynarmic/frontend/A64/decoder/a64.h"
#include "dynarmic/frontend/A64/translate/impl/impl.h"

int main() {
    using Dynarmic::A64::TranslatorVisitor;
    const auto has = [](unsigned instruction, std::string_view token) {
        const auto name = Dynarmic::A64::GetName<TranslatorVisitor>(instruction);
        assert(name && name->find(token) != std::string_view::npos);
    };
    // Constants are from the reviewed upstream encodings/Lichii coverage tools.
    has(0xF8BFC000U, "LDAPR");
    has(0xF8E00000U, "LDADD");
    has(0xC8A07C00U, "CAS");
    has(0x08207C00U, "CASP");
    has(0x9AC33041U, "PACGA");
    has(0xD65F0BFFU, "RETAA");
    std::puts("NS2_A64_V81_V85_DECODER_RUNTIME_PASS families=6");
}
"""

def transform(source: Path, output: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            "cmake",
            f"-DEDEN_A64_V81_V85_SOURCE_ROOT={source}",
            f"-DEDEN_A64_V81_V85_OUTPUT_ROOT={output}",
            "-P",
            str(SCRIPT),
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )

def compiler_and_platform_flags():
    compiler = (shutil.which("g++") if sys.platform == "linux" else shutil.which("clang++"))
    compiler = compiler or shutil.which("clang++") or shutil.which("g++")
    assert compiler, "C++20 compiler required"
    flags = []
    env = os.environ.copy()
    if sys.platform == "darwin":
        sdk15 = Path("/Library/Developer/CommandLineTools/SDKs/MacOSX15.4.sdk")
        sdk26 = Path("/Library/Developer/CommandLineTools/SDKs/MacOSX26.5.sdk")
        if sdk15.is_dir():
            env["SDKROOT"] = str(sdk15)
        if sdk26.is_dir():
            flags += [
                "-target", "arm64-apple-macos15", "-nostdinc++",
                "-isystem", str(sdk26 / "usr/include/c++/v1"),
            ]
    return compiler, flags, env

with tempfile.TemporaryDirectory(prefix="encore-a64-v81-v85-") as td:
    temp = Path(td)
    generated = temp / "include"
    configured = transform(BASE, generated)
    assert configured.returncode == 0, configured.stderr

    actual = {str(p.relative_to(generated)) for p in generated.rglob("*") if p.is_file()}
    expected = {str(REL / f) for f in FILES}
    assert actual == expected, (sorted(actual), sorted(expected))
    for relative in FILES:
        staged = generated / REL / relative
        maintained = ACTIVE / relative
        assert staged.read_bytes() == maintained.read_bytes(), relative

    decoder = (generated / REL / "decoder/a64.inc").read_text()
    for marker in (
        'INST(LDAPR_sz, "LDAPRB, LDAPRH, LDAPR"',
        'INST(AtomicMemOp, "LDADD/LDCLR/LDEOR/LDSET/LDSMAX/LDSMIN/LDUMAX/LDUMIN/SWP"',
        'INST(CompareAndSwap, "CASB, CASH, CAS"',
        'INST(CompareAndSwapPair, "CASP"',
        'INST(PACGA, "PACGA"',
        'INST(RETA, "RETAA, RETAB"',
        'INST(STG_family, "STG/STZG/ST2G/STZ2G/LDG"',
    ):
        assert decoder.count(marker) == 1, marker

    translator = SELECTED_TRANSLATOR.read_text()
    guard = "#if defined(EDEN_NS2_A64_V81_V85)"
    assert translator.count(guard) == 1
    guarded = translator.split(guard, 1)[1].split("#endif", 1)[0]
    for unit in ("load_store_atomic.cpp", "memory_tagging.cpp", "pointer_authentication.cpp"):
        assert guarded.count(unit) == 1, unit

    compiler, platform_flags, env = compiler_and_platform_flags()
    deps = ROOT / "vendor/sources/eden-cpm"
    include_roots = [
        generated,
        BASE,
        ROOT / "vendor/sources/eden/src",
        deps / "fmt/12.1.0/include",
    ] + list((deps / "boost/boost-1.90.0/libs").glob("*/include"))
    includes = ["-I" + str(p) for p in include_roots if p.is_dir()]

    # Compile the exact CMake-selected maintained translator with all new
    # implementation units enabled. This catches missing declarations,
    # duplicate definitions and source-overlay drift.
    syntax = subprocess.run(
        [
            compiler, "-std=c++20", "-O0", "-fsyntax-only",
            "-Wno-unused-parameter", "-DFMT_HEADER_ONLY",
            "-DEDEN_NS2_A64_V81_V85=1",
            *platform_flags, *includes, str(SELECTED_TRANSLATOR),
        ],
        capture_output=True, text=True, env=env, timeout=120,
    )
    assert syntax.returncode == 0, syntax.stderr[-7000:]
    print("NS2_A64_V81_V85_REAL_TRANSLATOR_PASS macro=1 selected_owner=1", flush=True)

    probe = temp / "decoder.cpp"
    probe.write_text(TEST_CPP)
    for opt in ("-O0", "-O2"):
        exe = temp / ("decoder-" + opt[1:])
        built = subprocess.run(
            [
                compiler, "-std=c++20", opt,
                "-fsanitize=undefined", "-fno-sanitize-recover=all",
                *platform_flags, *includes, str(probe), "-o", str(exe),
            ],
            capture_output=True, text=True, env=env, timeout=90,
        )
        assert built.returncode == 0, built.stderr[-6000:]
        executed = subprocess.run(
            [str(exe)], capture_output=True, text=True, env=env, timeout=20
        )
        assert executed.returncode == 0, executed.stderr[-3000:]
        assert "NS2_A64_V81_V85_DECODER_RUNTIME_PASS" in executed.stdout
        print(executed.stdout.strip(), opt, flush=True)

print("P0_2_SHARED_A64_V81_V85_PASS files=8 upstream=Lichii-11aac324 PS5_runtime=unverified")
