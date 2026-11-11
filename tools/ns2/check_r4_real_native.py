#!/usr/bin/env python3
"""R4 real native PS5 include/translation-unit gate, NOT a console test.

Fails if the active N60 ASTC TextureCache.h is not the compiler-selected
header, even if an inactive duplicate contains the candidate. Output objects
are in a scratch temporary directory, not in the PS5 application cache.
"""
from __future__ import annotations
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tempfile

VENDOR = "4c2a56676ed2cc7b8b923b10b5c0c0fe39817b2d"
HEADER_BLOB = "6b5b9084aeb63aa05b0061d6bcfbd2b4f99312f9"
LIVE_HEADER = ("vendor/encore-active/ns2-astc/include/"
               "video_core/texture_cache/texture_cache.h")
INACTIVE_HEADER = ("vendor/encore-active/eden-vulkan/vulkan-cache/"
                   "video_core/texture_cache/texture_cache.h")
TU = "vk_texture_cache_cost.cpp"

def run(argv, cwd=None, env=None, timeout=900):
    p = subprocess.run(argv, cwd=cwd, env=env, text=True,
                       capture_output=True, timeout=timeout)
    if p.returncode:
        raise RuntimeError("command failed rc=" + str(p.returncode) + ":\n"
                           + " ".join(map(str, argv[:5])) + "\n" + p.stderr[-14000:])
    return p

def elf(path):
    hdr = path.read_bytes()[:64]
    if len(hdr)<64 or hdr[:4] != b"\x7fELF" or hdr[4] != 2 or hdr[5] not in (1,2):
        raise RuntimeError("R4 expected ELF64 output, not "+hdr[:8].hex())
    end = "little" if hdr[5]==1 else "big"
    if int.from_bytes(hdr[16:18],end)!=1 or int.from_bytes(hdr[18:20],end)!=62:
        raise RuntimeError("R4 expected x86-64 ELF ET_REL")

def main():
    if len(sys.argv)!=2:
        raise RuntimeError("usage: check_r4_real_native.py <configured-cmake-build-dir>")
    native = Path(sys.argv[1]).resolve()
    repo = Path(__file__).resolve().parents[2]
    cache=(native/"CMakeCache.txt").read_text()
    if "EDEN_RESEARCH_NS2_R4_VOLUME:BOOL=ON" not in cache or \
       "EDEN_PS5_VULKAN:BOOL=ON" not in cache:
        raise RuntimeError("R4 native CMake research opt-in not selected")
    if run(["git","rev-parse","HEAD:vendor"],cwd=repo).stdout.strip()!=VENDOR:
        raise RuntimeError("R4 vendor research gitlink changed")
    h=repo/LIVE_HEADER
    if run(["git","hash-object",str(h)]).stdout.strip()!=HEADER_BLOB:
        raise RuntimeError("R4 active ASTC owner digest changed")
    live=h.read_text()
    inactive=(repo/INACTIVE_HEADER).read_text()
    if "copy_native_volume_slice" not in live or "copy_native_volume_slice" in inactive:
        raise RuntimeError("R4 candidate absent from actual owner or still in inactive copy")
    cc=json.loads((native/"compile_commands.json").read_text())
    matches=[r for r in cc if Path(r["file"]).name==TU]
    expected=(native/"headless"/TU).resolve()
    if len(matches)!=1 or Path(matches[0]["file"]).resolve()!=expected:
        raise RuntimeError("R4 real native VkTextureCache consumer missing/duplicated")
    record=matches[0]
    flags=list(record["arguments"]) if "arguments" in record else shlex.split(record["command"])
    if "-c" not in flags or "-o" not in flags or flags.count(str(record["file"]))!=1:
        raise RuntimeError("R4 compile command not exact unique source")
    for req in ("-DEDEN_RESEARCH_NS2_R4_VOLUME=1", "-DEDEN_NS2_ASTC_CACHE_BRIDGE=1"):
        if req not in flags:
            raise RuntimeError("R4 active source missing compile definition "+req)
    if not any(s=="-DPS5_NATIVE" or s.startswith("-DPS5_NATIVE=") for s in flags):
        raise RuntimeError("R4 PS5_NATIVE compiler definition absent")
    index=flags.index("-o")
    del flags[index:index+2]
    i=0
    while i<len(flags):
        if flags[i] in ("-MF","-MT","-MQ"):
            del flags[i:i+2]
        elif flags[i] in ("-MD","-MMD","-MP"):
            del flags[i]
        else:
            i+=1
    env=os.environ.copy()
    env["CCACHE_DISABLE"]="1"
    # -H prints real header resolution to compiler stderr. The candidate
    # must come through the live ns2-astc source after include_next bridge.
    probe=run([*flags,"-H","-fsyntax-only"], cwd=record["directory"],env=env,timeout=900)
    include_tree=probe.stderr
    if str(h.resolve()) not in include_tree and \
       str(h.absolute()) not in include_tree:
        raise RuntimeError("R4 compiler did NOT include actual N60 ASTC owner")
    if INACTIVE_HEADER in include_tree:
        raise RuntimeError("R4 compiler selected inactive shadow TextureCache")
    print("R4_NATIVE_ACTIVE_HEADER_PASS: exact N60 ASTC header in real -H compiler graph",flush=True)
    print("R4_NATIVE_SYNTAX_PASS: active full vk_texture_cache_cost.cpp",flush=True)
    with tempfile.TemporaryDirectory(prefix="r4-active-native-") as td:
        out=Path(td)
        bc=out/"r4-texture-cache-lto.o"
        run([*flags,"-o",str(bc)],cwd=record["directory"],env=env,timeout=1200)
        binary=bc.read_bytes()
        if binary[:4]!=bytes((0x42,0x43,0xc0,0xde)) or len(binary)<128:
            raise RuntimeError("R4 expected authentic LTO bitcode object")
        print(f"R4_NATIVE_BITCODE_PASS bytes={len(binary)}",flush=True)
        native_obj=out/"r4-texture-cache-nonlto.o"
        run([*flags,"-fno-lto","-o",str(native_obj)],
            cwd=record["directory"],env=env,timeout=1200)
        elf(native_obj)
        print(f"R4_NATIVE_ELF_PASS bytes={native_obj.stat().st_size}",flush=True)
        linker=shutil.which("ld.lld-18") or shutil.which("ld.lld")
        if not linker: raise RuntimeError("R4 requires LLD")
        linked=out/"r4-partial-lto.o"
        run([linker,"-r","--lto-O0",str(bc),"-o",str(linked)],timeout=300)
        elf(linked)
        print(f"R4_NATIVE_PARTIAL_LTO_PASS bytes={linked.stat().st_size}",flush=True)
    print("R4_NATIVE_SOURCE_GATE_PASS: selected real active source, no app link or PS5 run",flush=True)

if __name__=="__main__":
    try:
        main()
    except (OSError,ValueError,RuntimeError,subprocess.TimeoutExpired) as e:
        print("R4_NATIVE_SOURCE_GATE_FAIL: "+str(e),file=sys.stderr,flush=True)
        sys.exit(1)
