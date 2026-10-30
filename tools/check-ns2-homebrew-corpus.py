#!/usr/bin/env python3
"""Fetch an immutable, non-redistributed third-party GPU-app smoke corpus.

This is Vulkan GLSL/SPIR-V for the independent HBLauncher GPU-app ABI.
It is NOT a Nintendo NSO/NSP/XCI, native Ampere SM86 shader, or PS5 test.
Only download public original files; don't commit them or ship in a release.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import urllib.request

REPOSITORY = "CostelaCNX/blockfallns2"
REVISION = "a29ca2a16ace030499233a6fe8dfb1e6a73c614e"
# Git SHA-1 of original blobs, verified against the Git object prefix.
FILES = {
    "app.json": (410, "56b542037f2b68e88e70e3264a2576550b9bf39f"),
    "app.vert.spv": (852, "40018de425bc786553eaa8948e5072692958361f"),
    "app.frag.spv": (28252, "33a5297bbd898e5770d6456fc8534f9e2075a683"),
    "app.comp.spv": (56960, "95bf0c9412a291760a2d3495a28e27000aa26df1"),
}
# Explicit module type is checked both in the binary OpEntryPoint and by
# the Khronos SPIR-V validator; avoid treating any valid SPIR-V as a game.
STAGES = {"app.vert.spv": 0, "app.frag.spv": 4, "app.comp.spv": 5}

def git_blob_sha(data: bytes) -> str:
    prefix = b"blob " + str(len(data)).encode("ascii") + b"\0"
    return hashlib.sha1(prefix + data).hexdigest()

def parse_entrypoint_model(data: bytes) -> int:
    if len(data) < 20 or len(data) % 4 or len(data) > 1024 * 1024:
        raise ValueError("malformed SPIR-V module size")
    words = struct.unpack("<" + "I" * (len(data) // 4), data)
    if words[0] != 0x07230203 or words[3] == 0:
        raise ValueError("malformed SPIR-V header")
    index = 5
    entry = []
    while index < len(words):
        instruction = words[index]
        width, opcode = instruction >> 16, instruction & 0xFFFF
        if width < 1 or index + width > len(words):
            raise ValueError("malformed SPIR-V instruction span")
        if opcode == 15:  # OpEntryPoint
            if width < 4:
                raise ValueError("truncated SPIR-V entrypoint")
            entry.append(words[index + 1])
        index += width
    if len(entry) != 1:
        raise ValueError("expected exactly one shader entrypoint")
    return entry[0]

def fetch_exact(name: str, expected_size: int, expected_sha: str) -> bytes:
    uri = f"https://raw.githubusercontent.com/{REPOSITORY}/{REVISION}/{name}"
    request = urllib.request.Request(uri, headers={"User-Agent": "Eden-Encore-Research/1.0"})
    with urllib.request.urlopen(request, timeout=30) as response:
        data = response.read(expected_size + 1)
    if len(data) != expected_size or git_blob_sha(data) != expected_sha:
        raise ValueError(f"{name}: upstream asset differs from pinned Git blob")
    return data

def self_test() -> None:
    blob = b"sample"
    assert git_blob_sha(blob) == hashlib.sha1(b"blob 6\0sample").hexdigest()
    for invalid in (b"", b"\0" * 20, b"\x03\x02\x23\x07" + b"\0" * 16):
        try:
            parse_entrypoint_model(invalid)
        except ValueError:
            continue
        raise AssertionError("corrupt SPIR-V accepted")
    print("NS2 immutable homebrew corpus parser: PASS")

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--output", type=Path, default=Path("build-ns2-homebrew"))
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    args.output.mkdir(parents=True, exist_ok=True)
    for name, (size, sha) in FILES.items():
        data = fetch_exact(name, size, sha)
        if name.endswith(".spv"):
            model = parse_entrypoint_model(data)
            if model != STAGES[name]:
                raise ValueError(f"{name}: unexpected shader stage {model}")
        else:
            manifest = json.loads(data)
            assert manifest["format"] == "hblauncher.gpu-app"
            assert manifest["abi"] == 1 and manifest["id"] == "blockfall"
            assert manifest["shaders"] == {
                "vertex": "app.vert.spv",
                "fragment": "app.frag.spv",
                "compute": "app.comp.spv",
            }
        target = args.output / name
        target.write_bytes(data)
        if name.endswith(".spv"):
            subprocess.run(["spirv-val", "--target-env", "vulkan1.0", str(target)],
                           check=True)
        print(f"{name}: original Git blob and ABI/stage/validator PASS", flush=True)
    print("External Blockfall Vulkan corpus verified; NOT a Switch 2 executable")

if __name__ == "__main__":
    main()
