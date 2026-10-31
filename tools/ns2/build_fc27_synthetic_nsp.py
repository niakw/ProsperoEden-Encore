#!/usr/bin/env python3
"""PFS0 .nsp stress DATA corpus, source-verified, unsigned and copyright-clean; native boot unproven."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import struct
from fc27_stress_replay import capture, SHA

HEAD = struct.Struct("<4sIII")
ENTRY = struct.Struct("<QQII")


def procedural_bytes(label: str, length: int) -> bytes:
    seed = hashlib.sha256(label.encode()).digest()
    block = b"".join(hashlib.sha256(seed + i.to_bytes(4, "little")).digest()
                     for i in range(2048))
    return (block * (length // len(block) + 1))[:length]


def pack(files: dict[str, bytes]) -> bytes:
    if not files or any(not n or not n.isascii() or "/" in n or "\0" in n for n in files):
        raise ValueError("bad PFS0 member names")
    table = bytearray()
    strings = bytearray()
    bodies = bytearray()
    for name, body in files.items():
        table.extend(ENTRY.pack(len(bodies), len(body), len(strings), 0))
        strings.extend(name.encode() + b"\0")
        bodies.extend(body)
    return HEAD.pack(b"PFS0", len(files), len(strings), 0) + table + strings + bodies


def unpack(blob: bytes) -> dict[str, bytes]:
    if len(blob) < HEAD.size:
        raise ValueError("truncated PFS0")
    magic, count, n_strings, reserved = HEAD.unpack_from(blob)
    if magic != b"PFS0" or reserved or not 0 < count <= 32 or n_strings > 4096:
        raise ValueError("invalid PFS0")
    start = HEAD.size + count * ENTRY.size + n_strings
    if start > len(blob):
        raise ValueError("PFS0 table overflow")
    names = blob[HEAD.size + count * ENTRY.size:start]
    result = {}
    for i in range(count):
        off, size, name_off, flags = ENTRY.unpack_from(blob, HEAD.size + i * ENTRY.size)
        if flags or name_off >= len(names):
            raise ValueError("bad PFS0 member")
        end = names.find(b"\0", name_off)
        if end == -1:
            raise ValueError("PFS0 name unterminated")
        name = names[name_off:end].decode("ascii")
        if not name or name in result or off > len(blob) - start or size > len(blob) - start - off:
            raise ValueError("PFS0 member out of range")
        result[name] = blob[start + off:start + off + size]
    return result


def build(exefs: Path, output: Path, mib: int) -> dict:
    if not 1 <= mib <= 32:
        raise ValueError("texture MiB outside safe range 1..32")
    nso = (exefs / "main").read_bytes()
    npdm = (exefs / "main.npdm").read_bytes()
    if nso[:4] != b"NSO0" or npdm[:4] != b"META":
        raise ValueError("Source-verified public ExeFS missing")
    n = len(capture())
    size = mib * (1 << 20)
    hud, pitch = size // 4, size // 2
    manifest = {
        "kind": "Unsigned extracted-ExeFS NSP research input, not an EA FC27 game",
        "source": SHA, "historical_windows": n, "stress": [1, 4, 8],
        "texture_bytes": size, "valid_nca_count": 0,
        "extracted_exefs_route_expected": True, "native_boot_verified": False,
    }
    files = {
        "main": nso,
        "main.npdm": npdm,
        "stress.json": json.dumps(manifest, sort_keys=True).encode(),
        "hud.rgba": procedural_bytes("HUD Remap and glyph", hud),
        "pitch.rgba": procedural_bytes("Pitch cache churn", pitch),
        "kits.rgba": procedural_bytes("Player jersey variants", size - hud - pitch),
    }
    blob = pack(files)
    actual = unpack(blob)
    if list(actual) != list(files) or any(
        hashlib.sha256(actual[k]).digest() != hashlib.sha256(v).digest()
        for k, v in files.items()):
        raise AssertionError("PFS0 roundtrip differs")
    for corrupt in (blob[:-1], b"BAD0" + blob[4:]):
        try:
            unpack(corrupt)
        except ValueError:
            continue
        raise AssertionError("Corrupted PFS0 accepted")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(blob)
    return {"members": list(files), "bytes": len(blob),
            "sha256": hashlib.sha256(blob).hexdigest(),
            "extracted_exefs_route_expected": True, "native_boot_verified": False}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--exefs", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--texture-mib", type=int, default=8)
    a = ap.parse_args()
    print("FC27_SYNTHETIC_PFS0_PASS", json.dumps(build(a.exefs, a.out, a.texture_mib)))


if __name__ == "__main__":
    main()
