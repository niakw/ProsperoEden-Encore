#!/usr/bin/env python3
"""P0 NS2: qualify the production ARMv8.1-ARMv8.5 Dynarmic overlay.

The test stages the exact versioned vendor owners, syntax-compiles the real
maintained A64 translator selected by Encore, and executes Dynarmic's real
decoder at O0/O2 for instruction families observed in Switch 2 titles.
No PS5 execution or gameplay result is inferred.
"""
from pathlib import Path
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
CMAKE = (ROOT / "headless/CMakeLists.txt").read_text()
SCRIPT = ROOT / "headless/shared_a64_v81_v85.cmake"
BASE = ROOT / "vendor/sources/eden/src/dynarmic/src"
REL = Path("dynarmic/frontend/A64")
ACTIVE = ROOT / "vendor/encore-active/ns2-runtime/ldapr/maintained" / REL
TRANSLATOR = ROOT / "vendor/encore-active/eden-core/src/dynarmic/frontend/A64/translate/a64_translate.cpp"
EXPECTED_VENDOR = "435d49bd2a37439340b640443190d87893052347"
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

assert SCRIPT.is_file()
assert TRANSLATOR.is_file()
assert subprocess.check_output(
    ["git", "rev-parse", "HEAD:vendor"], cwd=ROOT, text=True
).strip() == EXPECTED_VENDOR
assert 'set(EDEN_SHARED_NS2_A64_V81_V85 ON)' in CMAKE
assert 'if(PS5_NATIVE AND EDEN_REVIEWED_DUAL_NPDM)' in CMAKE
assert 'include("${CMAKE_CURRENT_LIST_DIR}/shared_a64_v81_v85.cmake")' in CMAKE
assert 'target_compile_definitions(dynarmic PRIVATE EDEN_NS2_A64_V81_V85=1)' in CMAKE
assert 'target_include_directories(dynarmic BEFORE PRIVATE "${EDEN_A64_V81_V85_OUTPUT_ROOT}")' in CMAKE
assert "EDEN_NS2_A64_EXPERIMENTAL" not in CMAKE
assert "encore-active/ns2-a64" not in CMAKE

for f in FILES:
    assert (ACTIVE / f).is_file(), f

atomic = (ACTIVE / "translate/impl/load_store_atomic.cpp").read_text()
pointer = (ACTIVE / "translate/impl/pointer_authentication.cpp").read_text()
mte = (ACTIVE / "translate/impl/memory_tagging.cpp").read_text()
assert "IR::Term::CheckBit" in atomic and "ExclusiveMem(address, 16" in atomic
assert "TranslatorVisitor::CompareAndSwapPair" in atomic
assert "TranslatorVisitor::RETA" in pointer and "TranslatorVisitor::PACGA" in pointer
assert "TranslatorVisitor::STG_family" in mte and "TranslatorVisitor::ADDG" in mte
translator = TRANSLATOR.read_text()
guard = '#if defined(EDEN_NS2_A64_V81_V85)'
assert translator.count(guard) == 1
guarded = translator.split(guard, 1)[1].split("#endif", 1)[0]
for name in ("load_store_atomic.cpp", "memory_tagging.cpp", "pointer_authentication.cpp"):
    assert guarded.count(name) == 1, name

def transform(base: Path, out: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            "cmake",
            f"-DEDEN_A64_V81_V85_SOURCE_ROOT={base}",
            f"-DEDEN_A64_V81_V85_OUTPUT_ROOT={out}",
            "-P",
            str(SCRIPT),
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )

TEST_CPP = r'''
#include <cassert>
#include <cstdio>
#include <string_view>
#include "dynarmic/frontend/A64/decoder/a64.h"
#include "dynarmic/frontend/A64/translate/impl/impl.h"

int main() {
    using Dynarmic::A64::TranslatorVisitor;
    const auto has = [](unsigned instruction, std::string_view needle) {
        const auto op = Dynarmic::A64::GetName<TranslatorVisitor>(instruction);
        return op && std::string_view{*op}.find(needle) != std::string_view::npos;
    };
    assert(has(0xF8BFC000U, "LDAPR"));
    assert(has(0xF8200000U, "LDADD"));
    assert(has(0xF8208000U, "SWP"));
    assert(has(0xC8A07C00U, "CAS"));
    assert(has(0x48207C00U, "CASP"));
    assert(has(0xD65F0BFFU, "RETAA"));
    assert(has(0xD61F0800U, "BRAA"));
    assert(has(0xF8200400U, "LDRAA"));
    assert(has(0xDAC10000U, "PACIA"));
    assert(has(0xDAC143E0U, "XPACI"));
    assert(has(0x9AC03000U, "PACGA"));
    assert(has(0xD9200000U, "STG"));
    assert(has(0x68000000U, "STGP"));
    std::puts("NS2_A64_V81_V85_REAL_DECODER_PASS families=13");
}
'''

def main() -> None:
    candidates = list(dict.fromkeys(
        c for c in (shutil.which("clang++"), shutil.which("g++")) if c
    ))
    assert candidates
    compilers = []
    signatures = set()
    for candidate in candidates:
        info = subprocess.run(
            [candidate, "--version"], capture_output=True, text=True, timeout=30
        )
        assert info.returncode == 0
        signature = info.stdout.splitlines()[0]
        if signature in signatures:
            continue
        signatures.add(signature)
        compilers.append(candidate)

    env = os.environ.copy()
    sdk15 = Path("/Library/Developer/CommandLineTools/SDKs/MacOSX15.4.sdk")
    sdk26 = Path("/Library/Developer/CommandLineTools/SDKs/MacOSX26.5.sdk")
    if sdk15.is_dir():
        env["SDKROOT"] = str(sdk15)
    platform = []
    if sys.platform == "darwin" and sdk26.is_dir():
        platform = [
            "-target", "arm64-apple-macos15", "-nostdinc++",
            "-isystem", str(sdk26 / "usr/include/c++/v1"),
        ]

    deps = ROOT / "vendor/sources/eden-cpm"
    additional = [
        BASE,
        ROOT / "vendor/sources/eden/src",
        deps / "fmt/12.1.0/include",
    ] + list((deps / "boost/boost-1.90.0/libs").glob("*/include"))

    with tempfile.TemporaryDirectory(prefix="encore-a64-v81-v85-") as td:
        temp = Path(td)
        generated = temp / "include"
        result = transform(BASE, generated)
        assert result.returncode == 0, result.stderr
        actual = {str(p.relative_to(generated)) for p in generated.rglob("*") if p.is_file()}
        expected = {str(REL / f) for f in FILES}
        assert actual == expected, (sorted(actual), sorted(expected))
        for f in FILES:
            assert (generated / REL / f).read_bytes() == (ACTIVE / f).read_bytes(), f

        decoder = temp / "decoder.cpp"
        decoder.write_text(TEST_CPP)
        incs = ["-I" + str(generated)] + [
            "-I" + str(p) for p in additional if p.exists()
        ]
        for compiler in compilers:
            syntax = subprocess.run(
                [
                    compiler, "-std=c++20", "-O0", "-fsyntax-only",
                    "-DEDEN_NS2_A64_V81_V85=1",
                    *platform, *incs, str(TRANSLATOR),
                ],
                capture_output=True, text=True, env=env, timeout=120,
            )
            assert syntax.returncode == 0, (compiler, syntax.stderr[-7000:])
            print("NS2_A64_V81_V85_REAL_TRANSLATOR_PASS", Path(compiler).name, flush=True)

            for opt in (0, 2):
                output = temp / f"{Path(compiler).name}-O{opt}"
                build = subprocess.run(
                    [
                        compiler, "-std=c++20", f"-O{opt}",
                        "-fsanitize=undefined", "-fno-sanitize-recover=all",
                        *platform, *incs, str(decoder), "-o", str(output),
                    ],
                    capture_output=True, text=True, env=env, timeout=100,
                )
                assert build.returncode == 0, (compiler, opt, build.stderr[-5000:])
                run = subprocess.run(
                    [str(output)], capture_output=True, text=True, env=env, timeout=20
                )
                assert run.returncode == 0, (compiler, opt, run.stderr[-2500:])
                assert "NS2_A64_V81_V85_REAL_DECODER_PASS" in run.stdout
                print(
                    "NS2_A64_V81_V85_REAL_DECODER_PASS",
                    Path(compiler).name, f"O{opt}", flush=True,
                )

if __name__ == "__main__":
    main()
