#!/usr/bin/env python3
"""Compile only the four R2 Vulkan objects from the actual PS5 CMake graph.

This is a research-only, object-level code-generation gate. It never invokes
Ninja build targets, links an ELF, packages PS5 files, or modifies main.
Compiler output lives exclusively in a temporary directory (not the cache).
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tempfile

TARGETS = (
    "vk_staging_buffer_pool.cpp",
    "vk_buffer_cache_cost.cpp",
    "vulkan_rasterizer.cpp",
    "vulkan_scheduler.cpp",
)

def validate_elf_object(path: Path, name: str) -> None:
    with path.open("rb") as obj_file:
        header = obj_file.read(64)
    if len(header) < 64 or header[:4] != bytes((0x7f, 0x45, 0x4c, 0x46)):
        raise RuntimeError(f"{name}: not ELF (magic={header[:8].hex()})")
    if header[4] != 2 or header[5] not in (1, 2):
        raise RuntimeError(f"{name}: not a 64-bit ELF with valid endianness")
    byteorder = "little" if header[5] == 1 else "big"
    elf_type = int.from_bytes(header[16:18], byteorder)
    machine = int.from_bytes(header[18:20], byteorder)
    if elf_type != 1 or machine != 62:
        raise RuntimeError(
            f"{name}: not x86-64 ET_REL (type={elf_type}, machine={machine})")

def compile_object(name: str, row: dict, native: Path, output: Path) -> None:
    expected_source = (native / "headless" / name).resolve()
    if Path(row["file"]).resolve() != expected_source:
        raise RuntimeError(f"{name}: unexpected compiler source owner")
    argv = (list(row["arguments"]) if "arguments" in row
            else shlex.split(row["command"]))
    if argv.count("-c") != 1 or argv.count("-o") != 1:
        raise RuntimeError(f"{name}: not an unambiguous -c/-o CMake command")
    if not any(x == "-DPS5_NATIVE" or x.startswith("-DPS5_NATIVE=")
               for x in argv):
        raise RuntimeError(f"{name}: PS5_NATIVE missing")
    if "-DEDEN_RESEARCH_NS2_STAGE_BACKING=1" not in argv:
        raise RuntimeError(f"{name}: R2 feature gate missing")
    if any(x == "-fsyntax-only" for x in argv):
        raise RuntimeError(f"{name}: syntax-only command cannot emit an object")
    if argv.count(str(row["file"])) != 1:
        raise RuntimeError(f"{name}: recorded source must appear exactly once")
    index = argv.index("-o")
    if index + 1 >= len(argv):
        raise RuntimeError(f"{name}: missing -o argument")
    del argv[index:index + 2]
    # Never write CMake's dependency files or original object destination.
    i = 0
    while i < len(argv):
        if argv[i] in ("-MF", "-MT", "-MQ"):
            if i + 1 >= len(argv):
                raise RuntimeError(f"{name}: dangling dependency flag")
            del argv[i:i + 2]
        elif argv[i] in ("-MD", "-MMD", "-MP"):
            del argv[i]
        else:
            i += 1
    argv.extend(["-o", str(output)])
    env = os.environ.copy()
    # A cache hit is not evidence of this R2 translation unit being generated.
    env["CCACHE_DISABLE"] = "1"
    result = subprocess.run(
        argv, cwd=row["directory"], env=env,
        text=True, capture_output=True, timeout=780)
    if result.returncode:
        raise RuntimeError(
            f"{name}: native object compile failed (rc={result.returncode})\n"
            + result.stderr[-14000:])
    if not output.is_file() or output.stat().st_size < 128:
        raise RuntimeError(f"{name}: no nonempty native object generated")
    with output.open("rb") as obj_file:
        header = obj_file.read(8)
    if header[:4] == bytes((0x42, 0x43, 0xc0, 0xde)):
        # The exact PS5 CMake command uses LLVM LTO. The .o output is a
        # legitimate bitcode module; its machine code is generated at link.
        print(f"R2_NATIVE_LTO_BITCODE_EMITTED {name} "
              f"bytes={output.stat().st_size}", flush=True)
        # Disassembly is an additional check, never a substitute for exact
        # compiler success and separate native ELF code generation. Writing
        # /dev/null failed on the cached PS5 SDK runner, so use only our
        # private scratch directory. An external tool permission error is
        # reported as unqualified IR disassembly, not a source-code failure.
        llvm_dis = shutil.which("llvm-dis-18") or shutil.which("llvm-dis")
        if llvm_dis:
            ir_dump = output.with_suffix(".ll")
            verified = subprocess.run(
                [llvm_dis, str(output), "-o", str(ir_dump)],
                capture_output=True, text=True, timeout=90)
            if verified.returncode == 0 and ir_dump.is_file() and ir_dump.stat().st_size > 0:
                print(f"R2_NATIVE_LTO_IR_DISASSEMBLY_PASS {name}", flush=True)
            else:
                print(f"R2_NATIVE_LTO_IR_DISASSEMBLY_UNQUALIFIED {name}: "
                      f"{verified.stderr[-300:].strip()}", flush=True)
        else:
            print(f"R2_NATIVE_LTO_IR_DISASSEMBLY_UNQUALIFIED {name}: tool unavailable",
                  flush=True)
        # Separate diagnostic: exercise native machine-code generation with
        # every original flag except disabling LTO. This is NOT evidence of
        # the final application link-time optimizer or native ELF link.
        plain = output.with_suffix(".nonlto.o")
        plain_argv = list(argv)
        plain_argv[plain_argv.index("-o") + 1] = str(plain)
        plain_argv.append("-fno-lto")
        native = subprocess.run(
            plain_argv, cwd=row["directory"], env=env, capture_output=True,
            text=True, timeout=780)
        if native.returncode:
            raise RuntimeError(
                f"{name}: non-LTO diagnostic native codegen failed "
                f"(rc={native.returncode})\n" + native.stderr[-14000:])
        validate_elf_object(plain, name)
        print(f"R2_NATIVE_NONLTO_ELF_PASS {name} "
              f"bytes={plain.stat().st_size}", flush=True)
    else:
        validate_elf_object(output, name)
        print(f"R2_NATIVE_ELF_PASS {name} bytes={output.stat().st_size}",
              flush=True)
    digest = hashlib.sha256(output.read_bytes()).hexdigest()[:16]
    print(f"R2_NATIVE_OBJECT_PASS {name} exact_cmake_sha256_prefix={digest}",
          flush=True)
    return output

def main() -> int:
    if len(sys.argv) != 2:
        print("usage: check_r2_native_graph_objects.py <native-dir>", file=sys.stderr)
        return 2
    native = Path(sys.argv[1]).resolve()
    try:
        cache = (native / "CMakeCache.txt").read_text()
        if "EDEN_RESEARCH_NS2_STAGE_BACKING:BOOL=ON" not in cache:
            raise RuntimeError("R2 CMake feature is not ON")
        records = json.loads((native / "compile_commands.json").read_text())
        selected = {}
        for name in TARGETS:
            matches = [row for row in records
                       if Path(row["file"]).name == name]
            if len(matches) != 1:
                raise RuntimeError(f"{name}: expected exactly one native owner")
            selected[name] = matches[0]
        with tempfile.TemporaryDirectory(prefix="r2-native-objects-") as tmp:
            exact_objects = []
            for name in TARGETS:
                exact_objects.append(
                    compile_object(name, selected[name], native,
                                   Path(tmp) / (name + ".o")))
            # Targeted LLVM LTO partial link. The compiler's exact CMake -c
            # output is an LTO bitcode module; ld.lld -r runs the actual LTO
            # merger/code generator for these FOUR inputs only. Other engine
            # symbols remain unresolved by design. Never claim an app link.
            linker = shutil.which("ld.lld-18") or shutil.which("ld.lld")
            if not linker:
                raise RuntimeError("native LTO partial linker unavailable")
            merged = Path(tmp) / "r2-four-vulkan-partial-lto.o"
            link_argv = [linker, "-r", "--lto-O0", *map(str, exact_objects),
                         "-o", str(merged)]
            result = subprocess.run(
                link_argv, text=True, capture_output=True, timeout=240)
            if result.returncode:
                raise RuntimeError(
                    f"four-object LTO partial link failed rc={result.returncode}\\n"
                    + result.stderr[-14000:])
            validate_elf_object(merged, "R2 FOUR-source LTO partial link")
            print(f"R2_NATIVE_PARTIAL_LTO_LINK_PASS inputs=4 "
                  f"elf_bytes={merged.stat().st_size}", flush=True)
        print("R2_NATIVE_OBJECTS_PASS 4/4 and four-input partial LTO link; "
              "no full-application LTO symbol resolution, global build, "
              "application ELF, package or console test", flush=True)
        return 0
    except (OSError, RuntimeError, ValueError, subprocess.TimeoutExpired) as exc:
        print("R2_NATIVE_OBJECTS_FAIL " + str(exc), file=sys.stderr, flush=True)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
