#!/usr/bin/env python3
"""P0.2: qualify the production-selected ARMv8.1-8.5 A64 frontend.

The vendor owns exact reviewed Lichii 11aac324 blobs. This engine test proves
that the final PS5 source graph copies those owners, applies the compile macro
only to the maintained A64 translator, and compiles that real translator.
It is host/source qualification, never a PS5 gameplay claim.
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
TRANSLATOR = ROOT / "vendor/encore-active/eden-core/src/dynarmic/frontend/A64/translate/a64_translate.cpp"
FILES = (
    "decoder/a64.h",
    "decoder/a64.inc",
    "translate/impl/impl.h",
    "translate/impl/load_store_exclusive.cpp",
    "translate/impl/a64_branch.cpp",
    "translate/impl/load_store_atomic.cpp",
    "translate/impl/pointer_authentication.cpp",
    "translate/impl/memory_tagging.cpp",
)

assert 'set(EDEN_SHARED_NS2_A64_LDAPR ON)' in CMAKE
assert 'if(PS5_NATIVE AND EDEN_REVIEWED_DUAL_NPDM)' in CMAKE
assert 'include("${CMAKE_CURRENT_LIST_DIR}/shared_a64_ldapr.cmake")' in CMAKE
assert 'target_include_directories(dynarmic BEFORE PRIVATE "${EDEN_A64_LDAPR_OUTPUT_ROOT}")' in CMAKE
scoped = CMAKE.split('set_property(SOURCE "${EDEN_MAINTAINED_SCALAR_TRANSLATOR}"', 1)[1].split(')', 1)[0]
assert '"EDEN_NS2_A64_V81_V85=1"' in scoped
assert 'target_compile_definitions(dynarmic PRIVATE EDEN_NS2_A64_V81_V85' not in CMAKE
assert 'EDEN_NS2_A64_EXPERIMENTAL' not in CMAKE
assert all((BASE / REL / f).is_file() for f in FILES)
assert all((ACTIVE / f).is_file() for f in FILES)
assert TRANSLATOR.is_file()

def transform(base: Path, out: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["cmake", f"-DEDEN_A64_LDAPR_SOURCE_ROOT={base}",
         f"-DEDEN_A64_LDAPR_OUTPUT_ROOT={out}", "-P", str(SCRIPT)],
        capture_output=True, text=True, timeout=30,
    )

DECODER = r"""
#include <cassert>
#include <cstdio>
#include <string_view>
#include "dynarmic/frontend/A64/decoder/a64.h"
#include "dynarmic/frontend/A64/translate/impl/impl.h"
int main() {
    using Dynarmic::A64::TranslatorVisitor;
    for (auto instruction : {0x38BFC000U, 0x78BFC000U, 0xB8BFC000U, 0xF8BFC000U}) {
        const auto op = Dynarmic::A64::GetName<TranslatorVisitor>(instruction);
        assert(op && op->find("LDAPR") != std::string_view::npos);
    }
    const auto cas = Dynarmic::A64::GetName<TranslatorVisitor>(0xC8A07C00U);
    const auto ldadd = Dynarmic::A64::GetName<TranslatorVisitor>(0xF8200000U);
    const auto reta = Dynarmic::A64::GetName<TranslatorVisitor>(0xD65F0BFFU);
    const auto retb = Dynarmic::A64::GetName<TranslatorVisitor>(0xD65F0FFFU);
    assert(cas && cas->find("CAS") != std::string_view::npos);
    assert(ldadd && ldadd->find("LDADD") != std::string_view::npos);
    assert(reta && *reta == "RETAA, RETAB");
    assert(retb && *retb == "RETAA, RETAB");
    std::puts("SHARED_A64_V81_V85_REAL_DECODER_PASS");
}
"""

def main() -> None:
    # Reuse the vendor's immutable upstream/blob provenance contract first.
    vendor = subprocess.run(
        [sys.executable, str(ROOT / "vendor/tests/ns2_a64_v81_v85_source.py")],
        cwd=ROOT, capture_output=True, text=True, timeout=30,
    )
    assert vendor.returncode == 0, vendor.stderr[-5000:]
    assert "NS2_A64_V81_V85_SOURCE_PASS" in vendor.stdout

    candidates = list(dict.fromkeys(
        c for c in (shutil.which("clang++"), shutil.which("g++")) if c
    ))
    assert candidates
    env = os.environ.copy()
    sdk15 = Path("/Library/Developer/CommandLineTools/SDKs/MacOSX15.4.sdk")
    sdk26 = Path("/Library/Developer/CommandLineTools/SDKs/MacOSX26.5.sdk")
    if sdk15.is_dir():
        env["SDKROOT"] = str(sdk15)
    target_flags = []
    if sys.platform == "darwin" and sdk26.is_dir():
        target_flags = ["-target", "arm64-apple-macos15", "-nostdinc++",
                        "-isystem", str(sdk26 / "usr/include/c++/v1")]
    deps = ROOT / "vendor/sources/eden-cpm"
    extra = [
        BASE,
        ROOT / "vendor/sources/eden/src",
        deps / "fmt/12.1.0/include",
        *list((deps / "boost/boost-1.90.0/libs").glob("*/include")),
    ]

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
        decoder.write_text(DECODER)
        incs = ["-I" + str(generated)] + ["-I" + str(p) for p in extra if p.is_dir()]
        seen = set()
        for compiler in candidates:
            version = subprocess.run([compiler, "--version"], capture_output=True,
                                     text=True, timeout=30)
            assert version.returncode == 0
            sig = version.stdout.splitlines()[0]
            if sig in seen:
                continue
            seen.add(sig)

            syntax = subprocess.run(
                [compiler, "-std=c++20", "-O0", "-fsyntax-only",
                 "-DEDEN_NS2_A64_V81_V85=1", *target_flags, *incs, str(TRANSLATOR)],
                capture_output=True, text=True, env=env, timeout=120,
            )
            assert syntax.returncode == 0, (compiler, syntax.stderr[-6000:])
            print("P0_2_SHARED_A64_V81_V85_REAL_TRANSLATOR_PASS", Path(compiler).name)

            for opt in (0, 2):
                output = temp / f"{Path(compiler).name}-O{opt}"
                build = subprocess.run(
                    [compiler, "-std=c++20", f"-O{opt}", "-fsanitize=undefined",
                     "-fno-sanitize-recover=all", *target_flags, *incs,
                     str(decoder), "-o", str(output)],
                    capture_output=True, text=True, env=env, timeout=100,
                )
                assert build.returncode == 0, (compiler, opt, build.stderr[-5000:])
                run = subprocess.run([str(output)], capture_output=True, text=True,
                                     env=env, timeout=20)
                assert run.returncode == 0, (compiler, opt, run.stderr[-2500:])
                assert "SHARED_A64_V81_V85_REAL_DECODER_PASS" in run.stdout
                print("P0_2_SHARED_A64_V81_V85_REAL_DECODER_PASS",
                      Path(compiler).name, f"O{opt}")

    print("P0_2_SHARED_A64_V81_V85_PRODUCTION_GRAPH_PASS files=8 source_scoped=1")
    print("Host/source proof only; native PS5 execution remains unverified")

if __name__ == "__main__":
    main()
