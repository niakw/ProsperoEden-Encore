#!/usr/bin/env python3
"""Read-only R23 x64 page-table lookup source guard, not JIT/device proof."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
VENDOR = ROOT / "vendor"
ORIGINAL = VENDOR / "sources/eden/src/dynarmic/src/dynarmic/backend/x64/emit_x64_memory.h"
SELECTED = VENDOR / "encore-active/eden-core/src/dynarmic/backend/x64/emit_x64_memory.h"
ORIGINAL_SHA = "9686e4fc047f78d0863df3ccb5149c8ecc9dc484"
SELECTED_SHA = "c34906cc34a7b9576025520f1eb7f6416543ef33"
PIN = "22b69d6053db41b74edac2633c012f925b84f69e"


def git_blob(path: Path) -> str:
    h = hashlib.sha1(b"blob " + str(path.stat().st_size).encode() + b"\0")
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def classify(code: str) -> dict:
    a32_symbol = "EmitVAddrLookup<A32EmitContext>"
    a64_symbol = "EmitVAddrLookup<A64EmitContext>"
    if code.count(a32_symbol) != 1 or code.count(a64_symbol) != 1:
        raise ValueError("unexpected lookup function count")
    a32, a64 = code.split(a32_symbol, 1)[1].split(a64_symbol, 1)
    scale = "tmp * (1 << ctx.conf.page_table_log2_stride)"
    fallback = "code.shl(tmp, int(ctx.conf.page_table_log2_stride));"
    shift = "code.shl(page, *ctx.conf.page_table_sign_extension);"
    sar = "code.sar(page, *ctx.conf.page_table_sign_extension);"
    for name, section in (("A32", a32), ("A64", a64)):
        if (section.count(scale) != 1 or section.count(fallback) != 1
                or shift not in section or sar not in section
                or "page_table_log2_stride <= 3" not in section):
            raise ValueError(name + ": Xbyak LEA scale or sign-extension source changed")
    if ("0x00fffffffffff000ULL" not in a32
            or "code.shl(page, 8)" not in a32):
        raise ValueError("maintained A32 packed pointer-mask guard changed")
    return {
        "117_A64_sign_extension_final": "source-equivalent-E1",
        "122_A64_scaled_lookup": "source-equivalent-E1",
        "125_A32_LEA_stride": "source-equivalent-E1",
        "136_A32_upstream_sign_extension": "still-divergent-test-required",
        "compiler_header_depfile_proven": False,
        "native_JIT_executed": False,
        "PS5_runtime_verified": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    a = parser.parse_args()
    actual_pin = subprocess.check_output(
        ["git", "-C", str(VENDOR), "rev-parse", "HEAD"], text=True
    ).strip()
    if actual_pin != PIN:
        raise ValueError(f"expected historical vendor {PIN}, got {actual_pin}")
    if git_blob(ORIGINAL) != ORIGINAL_SHA or git_blob(SELECTED) != SELECTED_SHA:
        raise ValueError("header source Git blob drift")
    cmake = (ROOT / "headless/CMakeLists.txt").read_text()
    expected_cmake = (
        '"$' + '{PORT_ROOT}/vendor/encore-active/eden-core/src/dynarmic/backend/x64/emit_x64_memory.h"',
        '"$' + '{PORT_BUILD_DIR}/include/dynarmic/backend/x64/emit_x64_memory.h" COPYONLY',
        'target_include_directories(dynarmic BEFORE PUBLIC "$' + '{PORT_BUILD_DIR}/include")',
    )
    if not all(k in cmake for k in expected_cmake):
        raise ValueError("actual Dynarmic CMake maintained-header selector drift")
    source = SELECTED.read_text()
    result = classify(source)
    if a.self_test:
        invalid_scale = source.replace(
            "tmp * (1 << ctx.conf.page_table_log2_stride)",
            "tmp * ctx.conf.page_table_log2_stride", 1)
        invalid_sign = source.replace(
            "code.shl(page, *ctx.conf.page_table_sign_extension);",
            "code.shl(page, 63 - int(*ctx.conf.page_table_sign_extension));", 1)
        for mutated in (invalid_scale, invalid_sign):
            try:
                classify(mutated)
            except ValueError:
                pass
            else:
                raise AssertionError("unreviewed JIT addressing change was accepted")
        print("AB_R23_X64_MEMORY_SOURCE_GUARD_SELFTEST_PASS")
        return
    print(json.dumps({
        "vendor_pin": actual_pin,
        "original_git_blob": ORIGINAL_SHA,
        "maintained_git_blob": SELECTED_SHA,
        "upstream_final_blob": "102d451bde6197e46e08cdc9d372755bfe3bce82",
        "intended_CMake_header_owner_qualified": True,
        "cases": result,
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
