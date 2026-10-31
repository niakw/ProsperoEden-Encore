#!/usr/bin/env python3
"""Create a disposable, source-auditable ExeFS *research* fixture.

The NSO0 comes from build_public_nso_fixture.py, which verifies the upstream
AArch64 source Git blob. main.npdm is deliberately synthetic and unsigned.
NOT Nintendo Switch 2 content; NOT evidence of a boot or valid signed firmware.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import struct


def synthetic_npdm() -> bytes:
    npdm = bytearray(0x600)
    npdm[:4] = b"META"
    # Real FileSys::ProgramMetadata Header ABI: AArch64 plus 39-bit VA.
    npdm[0x0C] = 0x07
    npdm[0x0E] = 0x2C  # main-thread priority
    npdm[0x0F] = 0     # core 0
    struct.pack_into("<I", npdm, 0x1C, 0x100000)  # stack
    npdm[0x20:0x2B] = b"NS2-HOST-HB"
    # ACI is enlarged to keep the real KAC bytes outside the FAH data and
    # avoid overlapping the signed-ACID container (which is unsigned here).
    struct.pack_into("<IIII", npdm, 0x70,
                     0x80, 0xC0, 0x140, 0x400)  # ACI, ACID
    npdm[0x80:0x84] = b"ACI0"
    struct.pack_into("<Q", npdm, 0x90, 0x0100000000000420)
    struct.pack_into("<IIII", npdm, 0xA0,
                     0x40, 0x40, 0, 0)  # ACI FAH, SAC
    struct.pack_into("<II", npdm, 0xB0, 0x80, 12)  # ACI0 KAC offset/size at +0x30/+0x34
    # KCapabilities::InitializeForUser requires core/priority permissions.
    # Core 0, thread priorities 16..63, and ONLY the HOS hello SVCs:
    # 0x07 ExitProcess, 0x0B SleepThread, 0x1E GetSystemTick,
    # 0x26 Break, and 0x27 OutputDebugString.
    core_priority = 0x7 | (63 << 4) | (16 << 10)
    svc_mask0 = 0xF | ((1 << 7 | 1 << 11) << 5)
    svc_mask1 = 0xF | ((1 << 6 | 1 << 14 | 1 << 15) << 5) | (1 << 29)
    struct.pack_into("<III", npdm, 0x100,
                     core_priority, svc_mask0, svc_mask1)
    npdm[0xC0] = 1  # FAH version
    struct.pack_into("<Q", npdm, 0xC4, 0xDEADBEEF)

    # The experimental NS2 parser uses an ACID body at +0x300; a
    # deliberately empty legacy ACID position forces the extended path.
    acid = 0x440  # ACID container + 0x300 (extended body)
    npdm[acid:acid + 4] = b"ACID"
    # Application pool = 0. Neither a signed ACID nor retail metadata.
    struct.pack_into("<QQ", npdm, acid + 0x10,
                     0x0100000000000420, 0x0100000000000420)
    struct.pack_into("<IIII", npdm, acid + 0x20,
                     0x340, 0x40, 0, 0)
    npdm[0x480] = 1  # FAC version
    struct.pack_into("<Q", npdm, 0x484, 0x4321)
    return bytes(npdm)


def validate_nso(image: bytes) -> None:
    if not 0x100 <= len(image) <= 1024 * 1024 or image[:4] != b"NSO0":
        raise ValueError("Expected a bounded, independently generated NSO0")
    flags, = struct.unpack_from("<I", image, 0x0C)
    if flags != 0:
        raise ValueError("Fixture requires uncompressed NSO0 segments")
    prev_end = 0
    for index in range(3):
        offset, virtual, length = struct.unpack_from(
            "<III", image, 0x10 + index * 0x10)
        stored, = struct.unpack_from("<I", image, 0x60 + 4 * index)
        if (stored != length or offset < 0x100 or
                offset > len(image) or length > len(image) - offset or
                virtual < prev_end or virtual > 0x100000 or
                length > 0x100000 - virtual):
            raise ValueError("Inconsistent NSO0 file/virtual layout")
        prev_end = virtual + length
    if b"hello from HOS\n" not in image:
        raise ValueError("Missing verified public AArch64 test message")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--nso", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    image = args.nso.read_bytes()
    validate_nso(image)
    out_dir = args.output_dir
    if out_dir.exists() and any(out_dir.iterdir()):
        raise ValueError("Refusing to overwrite an existing ExeFS directory")
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "main").write_bytes(image)
    (out_dir / "main.npdm").write_bytes(synthetic_npdm())
    print(f"Unsigned research ExeFS generated: {out_dir}")
    print("NOT a Nintendo Switch 2 game. No emulator, KProcess or HLE boot tested.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
