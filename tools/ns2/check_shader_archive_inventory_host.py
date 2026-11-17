#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Synthetic host qualification for the manifest-only NS2 shader archive inventory."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "ns2"))
import shader_archive_inventory as inventory  # noqa: E402


def u16(buf: bytearray, off: int, value: int) -> None:
    struct.pack_into("<H", buf, off, value)


def u32(buf: bytearray, off: int, value: int) -> None:
    struct.pack_into("<I", buf, off, value)


def u64(buf: bytearray, off: int, value: int) -> None:
    struct.pack_into("<Q", buf, off, value)


def make_bnsh() -> bytes:
    size = 0x4C0
    data = bytearray(size)
    data[:8] = b"BNSH\0\0\0\0"
    data[8:12] = bytes((1, 4, 2, 0))
    data[0xC:0xE] = b"\xff\xfe"
    u32(data, 0x1C, size)
    data[0x60:0x64] = b"grsc"
    u16(data, 0x70, 4)
    u16(data, 0x72, 200)
    u32(data, 0x7C, 1)
    u64(data, 0x80, 0x98)

    program = 0xD8
    u64(data, 0x98 + 0x10, program)
    u64(data, program, 2)

    vertex_record, compute_record, task_record, mesh_record = 0x128, 0x168, 0x1A8, 0x1E8
    u64(data, program + 0x08, vertex_record)
    u64(data, program + 0x30, compute_record)
    u64(data, program + 0x40, task_record)
    u64(data, program + 0x48, mesh_record)

    vertex_code, compute_code = 0x230, 0x2C0
    task_code, task_control = 0x2E0, 0x370
    mesh_code, mesh_control = 0x3D0, 0x460

    def record(off: int, code_off: int, code_size: int, control_off: int = 0,
               control_size: int = 0) -> None:
        u64(data, off + 8, control_off)
        u64(data, off + 16, code_off)
        u32(data, off + 24, code_size)
        u32(data, off + 28, control_size)

    record(vertex_record, vertex_code, 144)
    record(compute_record, compute_code, 32)
    record(task_record, task_code, 144, task_control, 88)
    record(mesh_record, mesh_code, 144, mesh_control, 88)

    u32(data, vertex_code, 1 << 10)
    data[vertex_code + 4 : vertex_code + 144] = bytes([0xA1]) * 140
    data[compute_code : compute_code + 32] = bytes(range(32))
    u32(data, task_code, 1 << 10)
    data[task_code + 4 : task_code + 144] = bytes([0xB2]) * 140
    u32(data, mesh_code, 3 << 10)
    data[mesh_code + 4 : mesh_code + 144] = bytes([0xC3]) * 140

    for off, expected in ((task_control, 6), (mesh_control, 7)):
        data[off : off + 8] = bytes.fromhex("34127698c9000000")
        data[off + 8 : off + 84] = bytes([0x5A]) * 76
        u32(data, off + 84, expected << 16)
    return bytes(data)


def make_bfsha(payload: bytes) -> bytes:
    data = bytearray(0x20 + len(payload))
    data[:4] = b"FSHA"
    data[0xC:0xE] = b"\xff\xfe"
    u32(data, 0x1C, len(data))
    data[0x20:] = payload
    return bytes(data)


def make_sarc(name: str, payload: bytes) -> bytes:
    data_offset = 0x60
    data = bytearray(data_offset + len(payload))
    data[:4] = b"SARC"
    u16(data, 4, 0x14)
    data[6:8] = b"\xff\xfe"
    u32(data, 8, len(data))
    u32(data, 12, data_offset)
    data[0x14:0x18] = b"SFAT"
    u16(data, 0x18, 0x0C)
    u16(data, 0x1A, 1)
    u32(data, 0x24, 1 << 24)
    u32(data, 0x28, 0)
    u32(data, 0x2C, len(payload))
    data[0x30:0x34] = b"SFNT"
    u16(data, 0x34, 8)
    encoded = name.encode() + b"\0"
    assert len(encoded) <= data_offset - 0x38
    data[0x38 : 0x38 + len(encoded)] = encoded
    data[data_offset:] = payload
    return bytes(data)


bnsh = make_bnsh()
records = inventory.parse_bnsh_inventory(bnsh)
assert {record["stage"] for record in records} == {"vertex", "compute", "task", "mesh"}
assert all("code" not in record and "control" not in record for record in records)
assert next(r for r in records if r["stage"] == "compute")["code_sha256"] == hashlib.sha256(
    bytes(range(32))
).hexdigest()

bfsha = make_bfsha(bnsh)
embedded = inventory.find_bnsh(bfsha)
assert len(embedded) == 1 and embedded[0][0] == 0x20 and embedded[0][1] == bnsh

sarc = make_sarc("shader.bnsh", bnsh)
members = inventory.parse_sarc(sarc)
assert len(members) == 1 and members[0]["name"] == "shader.bnsh"
assert members[0]["_payload"] == bnsh

for broken in (
    bnsh[:-1],
    bnsh[:0x80],
    bytes(bytearray(bnsh[:0x1C]) + b"\0\0\0\0" + bytearray(bnsh[0x20:])),
):
    try:
        inventory.parse_bnsh_inventory(broken)
    except inventory.ArchiveError:
        pass
    else:
        raise AssertionError("malformed BNSH was accepted")

with tempfile.TemporaryDirectory(prefix="encore-ns2-shader-inventory-") as td:
    root = Path(td)
    direct = root / "direct.bnsh"
    wrapped = root / "wrapped.sarc"
    direct.write_bytes(bnsh)
    wrapped.write_bytes(sarc)

    manifest = inventory.inventory_sources([
        ("04003F40232DE000", direct),
        ("04003F40232DE000", wrapped),
    ])
    assert manifest["mode"] == "manifest-only"
    assert len(manifest["archives"]) == 2
    assert len(manifest["programs"]) == 4
    assert all(len(program["origins"]) == 2 for program in manifest["programs"])
    assert {program["stage"] for program in manifest["programs"]} == {
        "vertex", "compute", "task", "mesh"
    }

    payload = json.dumps(manifest, sort_keys=True)
    assert str(root) not in payload
    assert '"code":' not in payload and '"control":' not in payload
    assert inventory.UPSTREAM_COMMIT in payload
    assert inventory.UPSTREAM_BLOB in payload

    output = root / "manifest.json"
    proc = subprocess.run([
        sys.executable, "-B", str(ROOT / "tools" / "ns2" / "shader_archive_inventory.py"),
        "--source", f"04003F40232DE000={wrapped}",
        "--output", str(output),
    ], text=True, capture_output=True, timeout=30)
    if proc.returncode:
        raise AssertionError(proc.stdout + proc.stderr)
    loaded = json.loads(output.read_text())
    assert loaded["mode"] == "manifest-only"
    assert len(loaded["programs"]) == 4
    assert str(root) not in output.read_text()

    too_big = root / "too-big.bin"
    too_big.write_bytes(b"x" * 4097)
    try:
        inventory.inventory_sources([("04003F40232DE000", too_big)], max_input_bytes=4096)
    except inventory.ArchiveError as exc:
        assert "exceeds" in str(exc)
    else:
        raise AssertionError("input bound was not enforced")

print(
    "NS2_SHADER_ARCHIVE_INVENTORY_HOST_PASS",
    "formats=BNSH,BFSHA,SARC",
    "stages=vertex,compute,task,mesh",
    "manifest_only=1",
    "raw_shader_bytes=0",
    "ps5=unverified",
)
