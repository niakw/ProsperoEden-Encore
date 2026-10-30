#!/usr/bin/env python3
"""Build a lawful HOS NSO0 loader fixture from pinned open-source AArch64 code.

Source: ctj01/switch2pc examples/hello/hello.S at a fixed source commit.
Packaging is independently authored: this is NOT a Switch 2 eShop title and
this script does not run the resulting guest program under Encore.
"""
import argparse
import hashlib
from pathlib import Path
import struct
import subprocess
import urllib.request

SOURCE_REPOSITORY = "ctj01/switch2pc"
SOURCE_REVISION = "f1d25d5f92f62f46c4dcf92556757bdf72d5b073"
SOURCE_BLOB = "dff85100e23fe38ccde75d2034dd2a45ff89a54c"

def checked_download() -> bytes:
    address = (f"https://raw.githubusercontent.com/{SOURCE_REPOSITORY}/"
               f"{SOURCE_REVISION}/examples/hello/hello.S")
    req = urllib.request.Request(address, headers={"User-Agent": "Encore-NS2-research"})
    with urllib.request.urlopen(req, timeout=30) as response:
        data = response.read(16 * 1024)
    git_sha = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
    if git_sha != SOURCE_BLOB or b"hello from HOS" not in data:
        raise ValueError("Unrecognized upstream public AArch64 source blob")
    return data

def package_nso(text: bytes) -> bytes:
    if len(text) < 32 or len(text) > 0x8000 or b"hello from HOS\n" not in text:
        raise ValueError("Cross-assembled AArch64 hello text was not the expected fixture")
    # This fixture has the real original .text, a synthetic read-only marker,
    # and one synthetic data word. No synthetic bytes are executed.
    segments = (text, b"open-source-loader-test\0", b"\0" * 16)
    offsets = (0, 0x1000, 0x2000)
    header = bytearray(0x100)
    struct.pack_into("<4sIII", header, 0, b"NSO0", 0, 0, 0)
    file_bytes = bytearray(header)
    for i, (payload, virtual_offset) in enumerate(zip(segments, offsets)):
        # Header layout matches the true Encore Loader::NSOHeader:
        # NSOSegmentHeader 0x10, 0x20, 0x30; compressed sizes at 0x60.
        off = len(file_bytes)
        struct.pack_into("<IIII", file_bytes, 0x10 + i * 0x10,
                         off, virtual_offset, len(payload),
                         0x1000 if i == 2 else 0x10)
        struct.pack_into("<I", file_bytes, 0x60 + i * 4, len(payload))
        file_bytes.extend(payload)
    return bytes(file_bytes)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("build-ns2-homebrew/hello.nso"))
    args = parser.parse_args()
    out = args.output.resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    source = out.with_suffix(".S")
    source.write_bytes(checked_download())
    binary = out.with_suffix(".elf")
    subprocess.run(["aarch64-linux-gnu-gcc", "-nostdlib", "-static",
                    "-Wl,-Ttext=0", "-Wl,--build-id=none",
                    "-o", str(binary), str(source)], check=True)
    code_bin = out.with_suffix(".bin")
    subprocess.run(["aarch64-linux-gnu-objcopy", "-O", "binary", "-j",
                    ".text", str(binary), str(code_bin)], check=True)
    out.write_bytes(package_nso(code_bin.read_bytes()))
    assert out.read_bytes()[:4] == b"NSO0"
    print(f"Independent HOS hello NSO0 built: {out} ({out.stat().st_size} bytes)")
    print("SOURCE PIN VERIFIED; NSO0 PACKAGING ONLY; NO SWITCH 2 GAME BOOT")

if __name__ == "__main__":
    main()
