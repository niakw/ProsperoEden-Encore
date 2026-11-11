#!/usr/bin/env python3
"""R3 isolated native CMake source, syntax, codegen and single-object LTO probe.

Never invokes Ninja targets, links the application, packages or runs a PS5.
The maintained GOB16 decoder is shared by NS1 and NS2: this gate does NOT
replace console regression testing or prove a performance improvement.
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

VENDOR = "4f08b9c9dd2f34deecc9c9fa0d8196dcd6575c2e"
BLOB = "cc8bb22035f306e45389b6a7efbceeddb45dd6d0"
SOURCE = "vendor/encore-active/eden-core/src/video_core/textures/decoders.cpp"

def run(argv, cwd=None, env=None, timeout=210):
    result = subprocess.run(argv, cwd=cwd, env=env, text=True,
                            capture_output=True, timeout=timeout)
    if result.returncode:
        raise RuntimeError("cmd failed (" + str(result.returncode) + "): " +
                           " ".join(map(str, argv[:4])) + "\n" + result.stderr[-9500:])
    return result

def check_elf(path: Path):
    data = path.read_bytes()[:64]
    if len(data) != 64 or data[:4] != b"\x7fELF" or data[4] != 2 or data[5] not in (1, 2):
        raise RuntimeError("R3 is not ELF64")
    endian = "little" if data[5] == 1 else "big"
    if int.from_bytes(data[16:18], endian) != 1 or int.from_bytes(data[18:20], endian) != 62:
        raise RuntimeError("R3 is not x86-64 ELF ET_REL")

def main():
    if len(sys.argv) != 2:
        raise RuntimeError("usage: check_r3_real_native.py <PS5 native CMake build dir>")
    native = Path(sys.argv[1]).resolve()
    root = Path(__file__).resolve().parents[2]
    cache = (native / "CMakeCache.txt").read_text()
    if "EDEN_RESEARCH_NS2_GOB16:BOOL=ON" not in cache:
        raise RuntimeError("R3 opt-in not enabled by real CMake")
    if "EDEN_PS5_VULKAN:BOOL=ON" not in cache:
        raise RuntimeError("PS5 Vulkan not enabled")
    selected = root / SOURCE
    if not selected.is_file() or run(["git","hash-object",str(selected)]).stdout.strip() != BLOB:
        raise RuntimeError("R3 exact maintained decoder source drift")
    if run(["git","rev-parse","HEAD:vendor"],cwd=root).stdout.strip() != VENDOR:
        raise RuntimeError("R3 vendor pin mismatch")
    commands = json.loads((native / "compile_commands.json").read_text())
    matches = [record for record in commands if Path(record["file"]).name == "decoders.cpp"]
    if len(matches) != 1 or Path(matches[0]["file"]).resolve() != selected.resolve():
        raise RuntimeError("R3 maintained decoder must be selected exactly once, no legacy TU")
    record = matches[0]
    flags = list(record["arguments"]) if "arguments" in record else shlex.split(record["command"])
    if "-c" not in flags or "-o" not in flags or str(record["file"]) not in flags:
        raise RuntimeError("R3 native CMake command is not a compile-only source")
    if not any(f == "-DPS5_NATIVE" or f.startswith("-DPS5_NATIVE=") for f in flags):
        raise RuntimeError("R3 PS5_NATIVE compiler definition absent")
    if flags.count(str(record["file"])) != 1:
        raise RuntimeError("R3 source selected multiple times in compiler argv")
    idx = flags.index("-o")
    del flags[idx:idx+2]
    i = 0
    while i < len(flags):
        if flags[i] in ("-MF", "-MT", "-MQ"):
            del flags[i:i+2]
        elif flags[i] in ("-MD", "-MMD", "-MP"):
            del flags[i]
        else:
            i += 1
    env = os.environ.copy()
    env["CCACHE_DISABLE"] = "1"
    run([*flags, "-fsyntax-only"], cwd=record["directory"], env=env)
    print("R3_NATIVE_GOB16_SYNTAX_PASS exact maintained CMake TU", flush=True)
    with tempfile.TemporaryDirectory(prefix="r3-native-gob16-") as td:
        out = Path(td)
        bitcode = out / "r3-decoder-lto.o"
        run([*flags, "-o", str(bitcode)], cwd=record["directory"], env=env)
        data = bitcode.read_bytes()
        if len(data) < 128 or data[:4] != bytes((0x42,0x43,0xc0,0xde)):
            raise RuntimeError("R3 expected real Clang LTO bitcode object")
        print(f"R3_NATIVE_GOB16_BITCODE_PASS bytes={len(data)}", flush=True)
        nonlto = out / "r3-decoder-nonlto.o"
        run([*flags, "-fno-lto", "-o", str(nonlto)],
            cwd=record["directory"], env=env)
        check_elf(nonlto)
        print(f"R3_NATIVE_GOB16_ELF_PASS bytes={nonlto.stat().st_size}", flush=True)
        linker = shutil.which("ld.lld-18") or shutil.which("ld.lld")
        if not linker:
            raise RuntimeError("lld required for R3 partial LTO")
        combined = out / "r3-decoder-partial-lto.o"
        run([linker, "-r", "--lto-O0", str(bitcode), "-o", str(combined)], timeout=180)
        check_elf(combined)
        print(f"R3_NATIVE_GOB16_PARTIAL_LTO_PASS bytes={combined.stat().st_size}", flush=True)
    print("R3_NATIVE_GOB16_GATE_PASS: actual PS5 source/objects; no app link, console or FPS",flush=True)

if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as exc:
        print("R3_NATIVE_GOB16_GATE_FAIL "+str(exc), file=sys.stderr, flush=True)
        sys.exit(1)
