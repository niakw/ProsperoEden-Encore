#!/usr/bin/env python3
"""P0 NS2: qualify the production ARMv8.1-8.5 Dynarmic frontend overlay.

Vendor #192 is an exact reviewed Lichii 11aac324 promotion on the same
Dynarmic base. Vendor #193 separately restores current nx2 64 GiB alias /
32 GiB VAMM geometry. This host gate verifies both the exact source pair and
that the engine actually enables the new translator methods. It is not PS5
runtime/gameplay proof.
"""
from pathlib import Path
import os
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
VENDOR = ROOT / "vendor"
CMAKE = (ROOT / "headless/CMakeLists.txt").read_text(encoding="utf-8")
SCRIPT = ROOT / "headless/shared_a64_ldapr.cmake"
BASE = VENDOR / "sources/eden/src/dynarmic/src"
REL = Path("dynarmic/frontend/A64")
STATIC = VENDOR / "encore-active/ns2-runtime/ldapr/maintained" / REL
PROD_TRANSLATOR = (
    VENDOR / "encore-active/eden-core/src/dynarmic/frontend/A64/translate/a64_translate.cpp"
)
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
EXPECTED_VENDOR = "d0246caf58a3127597bba1edfc1f8dcbe0c5cfdc"

selected = subprocess.check_output(
    ["git", "rev-parse", "HEAD:vendor"], cwd=ROOT, text=True
).strip()
checked = subprocess.check_output(
    ["git", "-C", str(VENDOR), "rev-parse", "HEAD"], text=True
).strip()
assert selected == checked == EXPECTED_VENDOR, (selected, checked)

assert "if(PS5_NATIVE AND EDEN_REVIEWED_DUAL_NPDM)" in CMAKE
assert "set(EDEN_SHARED_NS2_A64_LDAPR ON)" in CMAKE
assert 'include("${CMAKE_CURRENT_LIST_DIR}/shared_a64_ldapr.cmake")' in CMAKE
assert 'target_include_directories(dynarmic BEFORE PRIVATE "${EDEN_A64_LDAPR_OUTPUT_ROOT}")' in CMAKE
assert "target_compile_definitions(dynarmic PRIVATE EDEN_NS2_A64_V81_V85=1)" in CMAKE
assert "EDEN_NS2_A64_EXPERIMENTAL" not in CMAKE
assert all((STATIC / f).is_file() for f in FILES)
assert PROD_TRANSLATOR.is_file()

# Reuse the vendor's exact upstream provenance and VAMM parity oracles.
for check in (
    VENDOR / "tests/ns2_a64_v81_v85_source.py",
    VENDOR / "tests/ns2_alias_64g_upstream_parity_host.py",
):
    run = subprocess.run(
        [sys.executable, "-B", str(check)],
        cwd=VENDOR,
        capture_output=True,
        text=True,
        timeout=120,
    )
    if run.returncode:
        print(run.stdout[-3000:], file=sys.stderr)
        print(run.stderr[-5000:], file=sys.stderr)
        raise SystemExit(run.returncode)
    print(run.stdout.strip(), flush=True)


def transform(base: Path, out: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            "cmake",
            f"-DEDEN_A64_LDAPR_SOURCE_ROOT={base}",
            f"-DEDEN_A64_LDAPR_OUTPUT_ROOT={out}",
            "-P",
            str(SCRIPT),
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )


def representative(pattern: str) -> int:
    """Return one decoder-table value; variable and '-' bits become zero."""
    assert len(pattern) == 32, pattern
    value = 0
    for bit in pattern:
        value <<= 1
        if bit == "1":
            value |= 1
        elif bit != "0":
            # Decoder metavariables and don't-care characters are zero here.
            assert bit.isalpha() or bit == "-", (pattern, bit)
    return value


def compiler_list():
    candidates = list(dict.fromkeys(
        c for c in (shutil.which("clang++"), shutil.which("g++")) if c
    ))
    result = []
    signatures = set()
    for compiler in candidates:
        info = subprocess.run(
            [compiler, "--version"], capture_output=True, text=True, timeout=30
        )
        assert info.returncode == 0
        signature = info.stdout.splitlines()[0]
        if signature in signatures:
            continue
        signatures.add(signature)
        result.append(compiler)
    assert result
    return result


def main() -> None:
    env = os.environ.copy()
    sdk15 = Path("/Library/Developer/CommandLineTools/SDKs/MacOSX15.4.sdk")
    sdk26 = Path("/Library/Developer/CommandLineTools/SDKs/MacOSX26.5.sdk")
    if sdk15.is_dir():
        env["SDKROOT"] = str(sdk15)
    platform_flags = []
    if sys.platform == "darwin" and sdk26.is_dir():
        platform_flags = [
            "-target", "arm64-apple-macos15", "-nostdinc++",
            "-isystem", str(sdk26 / "usr/include/c++/v1"),
        ]

    deps = VENDOR / "sources/eden-cpm"
    include_roots = [
        BASE,
        VENDOR / "sources/eden/src",
        deps / "fmt/12.1.0/include",
        *list((deps / "boost/boost-1.90.0/libs").glob("*/include")),
    ]

    with tempfile.TemporaryDirectory(prefix="encore-ns2-a64-v81-v85-") as td:
        temp = Path(td)
        generated = temp / "include"
        staged = transform(BASE, generated)
        assert staged.returncode == 0, staged.stderr

        actual = {
            str(p.relative_to(generated))
            for p in generated.rglob("*")
            if p.is_file()
        }
        expected = {str(REL / f) for f in FILES}
        assert actual == expected, (sorted(actual), sorted(expected))
        for f in FILES:
            assert (generated / REL / f).read_bytes() == (STATIC / f).read_bytes(), f
        print("P0_NS2_A64_V81_V85_COPYONLY_PARITY_PASS files=8", flush=True)

        # Build executable decoder witnesses from the production decoder rows
        # themselves. This rejects a source that exists but loses precedence or
        # cannot instantiate TranslatorVisitor's new declarations.
        table = (generated / REL / "decoder/a64.inc").read_text(encoding="utf-8")
        required = (
            "LDAPR_sz", "AtomicMemOp", "CompareAndSwap", "CompareAndSwapPair",
            "PACAUT_reg", "XPAC_1", "PACGA", "RETA", "BRA_BLRA", "LDRA",
            "STG_family", "STGP", "IRG", "GMI", "ADDG", "SUBG",
        )
        rows = {}
        for symbol, label, pattern in re.findall(
            r'^INST\(([^,]+),\s*"([^"]+)",\s*"([^"]+)"\)',
            table,
            flags=re.MULTILINE,
        ):
            if symbol in required:
                rows[symbol] = (label, pattern)
        assert set(rows) == set(required), (set(required) - set(rows))

        cases = []
        for symbol in required:
            label, pattern = rows[symbol]
            cases.append((representative(pattern), label))

        cpp = temp / "decoder.cpp"
        checks = "\n".join(
            f'    check(0x{value:08x}U, {label!r});'
            .replace("'", '"')
            for value, label in cases
        )
        cpp.write_text(
            r'''#include <cassert>
#include <cstdio>
#include <string_view>
#include "dynarmic/frontend/A64/decoder/a64.h"
#include "dynarmic/frontend/A64/translate/impl/impl.h"
int main() {
    using Dynarmic::A64::TranslatorVisitor;
    auto check=[](unsigned insn, std::string_view expected) {
        auto got=Dynarmic::A64::GetName<TranslatorVisitor>(insn);
        assert(got && *got == expected);
    };
''' + checks + r'''
    std::puts("P0_NS2_A64_V81_V85_REAL_DECODER_PASS");
}
''',
            encoding="utf-8",
        )

        include_flags = ["-I" + str(generated)] + [
            "-I" + str(p) for p in include_roots if p.is_dir()
        ]
        for compiler in compiler_list():
            # Crucial: compile the same maintained translator that CMake
            # selects, with the actual production macro. The old gate compiled
            # pinned a64_translate.cpp and could not prove the promoted units.
            syntax = subprocess.run(
                [
                    compiler, "-std=c++20", "-O0", "-fsyntax-only",
                    "-DEDEN_NS2_A64_V81_V85=1",
                    *platform_flags, *include_flags, str(PROD_TRANSLATOR),
                ],
                capture_output=True,
                text=True,
                env=env,
                timeout=140,
            )
            assert syntax.returncode == 0, (
                compiler, syntax.stdout[-2000:], syntax.stderr[-7000:]
            )
            print(
                "P0_NS2_A64_V81_V85_REAL_TRANSLATOR_PASS",
                Path(compiler).name,
                flush=True,
            )

            for opt in (0, 2):
                output = temp / f"{Path(compiler).name}-decoder-O{opt}"
                build = subprocess.run(
                    [
                        compiler, "-std=c++20", f"-O{opt}",
                        "-fsanitize=undefined", "-fno-sanitize-recover=all",
                        *platform_flags, *include_flags, str(cpp), "-o", str(output),
                    ],
                    capture_output=True,
                    text=True,
                    env=env,
                    timeout=120,
                )
                assert build.returncode == 0, (
                    compiler, opt, build.stdout[-1500:], build.stderr[-5000:]
                )
                execute = subprocess.run(
                    [str(output)], capture_output=True, text=True, env=env, timeout=20
                )
                assert execute.returncode == 0, (
                    compiler, opt, execute.stdout, execute.stderr
                )
                assert "P0_NS2_A64_V81_V85_REAL_DECODER_PASS" in execute.stdout
                print(
                    "P0_NS2_A64_V81_V85_DECODER_UBSAN_PASS",
                    Path(compiler).name, f"O{opt}", flush=True,
                )

    print(
        "P0_NS2_A64_V81_V85_HOST_PASS vendor=d0246caf "
        "vamm=32GiB console_runtime=UNVERIFIED"
    )


if __name__ == "__main__":
    main()
