#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Host-only NS2 shader archive inventory.

Adapted from zortos293/Lichii tools/nx2/shader_archive.py at
6b34d6ee1398e27080bda6b64cc7b790e30c579e (Git blob
89f2afc5eeda1f6429984391ae8100148ac72fe2).

Phase 1 recognizes bounded SARC, BFSHA/FSHA and NVN2 BNSH containers.
It emits only hashes, sizes, stages, offsets and container provenance:
never shader/control bytes, GPU addresses, guest addresses, keys or driver
pipeline blobs. It is developer tooling and is not part of the PS5 runtime.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
from typing import Iterable

UPSTREAM_COMMIT = "6b34d6ee1398e27080bda6b64cc7b790e30c579e"
UPSTREAM_BLOB = "89f2afc5eeda1f6429984391ae8100148ac72fe2"
MAX_INPUT_BYTES = 256 * 1024 * 1024
MAX_DEPTH = 12
SUPPORTED_BNSH_VERSIONS = {(0, 4, 2, 0), (1, 3, 2, 0), (1, 4, 2, 0)}
SUPPORTED_NVN_API = (4, 200)


class ArchiveError(ValueError):
    """Malformed, unsupported or out-of-bounds shader container."""


def _range(data: bytes, offset: int, size: int) -> bytes:
    if offset < 0 or size < 0 or offset > len(data) or size > len(data) - offset:
        raise ArchiveError(f"out-of-range data at {offset:#x}, size {size:#x}")
    return data[offset : offset + size]


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def parse_sarc(data: bytes) -> list[dict]:
    """Return bounded named SARC members and their container-relative offsets."""
    _range(data, 0, 0x20)
    if data[:4] != b"SARC":
        raise ArchiveError("not a SARC archive")
    if data[6:8] == b"\xff\xfe":
        endian = "<"
    elif data[6:8] == b"\xfe\xff":
        endian = ">"
    else:
        raise ArchiveError("invalid SARC byte order")

    def u16(offset: int) -> int:
        return struct.unpack(endian + "H", _range(data, offset, 2))[0]

    def u32(offset: int) -> int:
        return struct.unpack(endian + "I", _range(data, offset, 4))[0]

    header_size, file_size, data_offset = u16(4), u32(8), u32(12)
    if header_size < 0x14 or file_size != len(data) or data_offset > file_size:
        raise ArchiveError("invalid SARC header or file size")
    sfat = header_size
    if _range(data, sfat, 4) != b"SFAT" or u16(sfat + 4) < 0x0C:
        raise ArchiveError("invalid SFAT header")
    count = u16(sfat + 6)
    nodes = sfat + u16(sfat + 4)
    _range(data, nodes, count * 0x10)
    sfnt = nodes + count * 0x10
    if _range(data, sfnt, 4) != b"SFNT" or u16(sfnt + 4) < 8:
        raise ArchiveError("invalid SFNT header")
    names = sfnt + u16(sfnt + 4)
    if names > data_offset:
        raise ArchiveError("SARC names overlap file data")

    result = []
    for index in range(count):
        node = nodes + index * 0x10
        flags, start, end = u32(node + 4), u32(node + 8), u32(node + 12)
        if flags >> 24 != 1:
            raise ArchiveError("SARC member has no supported name")
        name_offset = names + (flags & 0xFFFFFF) * 4
        if name_offset >= data_offset:
            raise ArchiveError("SARC name outside string table")
        terminator = data.find(b"\0", name_offset, data_offset)
        if terminator < 0:
            raise ArchiveError("unterminated SARC name")
        try:
            name = data[name_offset:terminator].decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ArchiveError("invalid SARC name") from exc
        if end < start or end > file_size - data_offset:
            raise ArchiveError("invalid SARC member range")
        absolute = data_offset + start
        result.append({
            "name": name,
            "offset": absolute,
            "size": end - start,
            "_payload": _range(data, absolute, end - start),
        })
    return result


def parse_bnsh_inventory(data: bytes) -> list[dict]:
    """Validate one BNSH and return metadata/hashes only, never shader bytes."""
    _range(data, 0, 0x98)
    if data[:8] != b"BNSH\0\0\0\0" or data[0x60:0x64] != b"grsc":
        raise ArchiveError("invalid BNSH header")
    if data[0xC:0xE] != b"\xff\xfe":
        raise ArchiveError("unsupported BNSH byte order")

    def u16(offset: int) -> int:
        return struct.unpack("<H", _range(data, offset, 2))[0]

    def u32(offset: int) -> int:
        return struct.unpack("<I", _range(data, offset, 4))[0]

    def u64(offset: int) -> int:
        return struct.unpack("<Q", _range(data, offset, 8))[0]

    if u32(0x1C) != len(data):
        raise ArchiveError("invalid BNSH file size")
    version = tuple(data[8:12])
    if version not in SUPPORTED_BNSH_VERSIONS:
        raise ArchiveError(f"unsupported BNSH version {version}")
    api = (u16(0x70), u16(0x72))
    if api != SUPPORTED_NVN_API:
        raise ArchiveError(f"unsupported BNSH API {api[0]}/{api[1]}")

    count, variations = u32(0x7C), u64(0x80)
    if count and not variations:
        raise ArchiveError("missing BNSH variation table")
    _range(data, variations, count * 0x40)

    stages = ("vertex", "tess-control", "tess-eval", "geometry", "fragment", "compute")
    result = []
    for variation in range(count):
        program = u64(variations + variation * 0x40 + 0x10)
        if not program:
            raise ArchiveError("missing BNSH variation program")
        _range(data, program, 0x38)
        slots = list(zip(range(8, 0x38, 8), stages))
        if version == (1, 4, 2, 0) and u64(program) == 2:
            _range(data, program, 0x50)
            slots.extend(((0x40, "task"), (0x48, "mesh")))

        for index, (slot, stage) in enumerate(slots):
            record = u64(program + slot)
            if not record:
                continue
            _range(data, record, 0x40)
            control_offset, code_offset = u64(record + 8), u64(record + 16)
            code_size, control_size = u32(record + 24), u32(record + 28)
            if not code_offset or not code_size or (control_size and not control_offset):
                raise ArchiveError("invalid BNSH stage data pointer or size")
            code = _range(data, code_offset, code_size)
            control = _range(data, control_offset, control_size)

            if stage != "compute":
                if len(code) <= 128 or (len(code) - 128) % 16:
                    raise ArchiveError("invalid native graphics code size")
                header_type = (struct.unpack_from("<I", code)[0] >> 10) & 15
                if stage in ("task", "mesh"):
                    expected = 6 if stage == "task" else 7
                    if (
                        len(control) < 88
                        or control[:8] != bytes.fromhex("34127698c9000000")
                        or u32(control_offset + 84) >> 16 != expected
                        or header_type not in ((1,) if stage == "task" else (1, 3))
                    ):
                        raise ArchiveError("invalid BNSH task/mesh stage metadata")
                elif header_type != index + 1:
                    raise ArchiveError("BNSH graphics stage disagrees with native header")

            result.append({
                "variation": variation,
                "stage": stage,
                "code_offset": code_offset,
                "code_size": code_size,
                "code_sha256": _sha256(code),
                "control_offset": control_offset if control_size else None,
                "control_size": control_size,
                "control_sha256": _sha256(control),
                "bnsh_version": list(version),
                "api_type": api[0],
                "api_version": api[1],
            })
    return result


def find_embedded_bnsh(data: bytes) -> list[tuple[int, bytes]]:
    """Return bounded BNSH allocations embedded in a known outer container."""
    result = []
    offset = 0
    while True:
        offset = data.find(b"BNSH\0\0\0\0", offset)
        if offset < 0:
            break
        header = _range(data, offset, 0x20)
        size = struct.unpack_from("<I", header, 0x1C)[0]
        if size < 0x98:
            raise ArchiveError("invalid embedded BNSH size")
        bnsh = _range(data, offset, size)
        parse_bnsh_inventory(bnsh)
        result.append((offset, bnsh))
        offset += size
    if not result:
        raise ArchiveError("container contains no supported BNSH")
    return result


def find_bnsh(data: bytes) -> list[tuple[int, bytes]]:
    """Validate BFSHA/FSHA framing, then return embedded BNSH allocations."""
    if len(data) < 0x20 or data[:4] != b"FSHA":
        raise ArchiveError("not a BFSHA archive")
    if data[0xC:0xE] != b"\xff\xfe" or struct.unpack_from("<I", data, 0x1C)[0] != len(data):
        raise ArchiveError("invalid BFSHA byte order or size")
    return find_embedded_bnsh(data)


def _scan_container(data: bytes, origin: str, depth: int = 0) -> tuple[list[dict], list[dict]]:
    if depth > MAX_DEPTH:
        raise ArchiveError("excessive container nesting")
    if data[:8] == b"BNSH\0\0\0\0":
        records = parse_bnsh_inventory(data)
        for record in records:
            record["origin"] = origin
        return records, []

    magic = data[:4]
    if magic == b"FSHA":
        programs = []
        for offset, bnsh in find_bnsh(data):
            nested, errors = _scan_container(bnsh, f"{origin}!BNSH@{offset:x}", depth + 1)
            if errors:
                raise ArchiveError(errors[0]["error"])
            programs.extend(nested)
        return programs, []

    if magic == b"SARC":
        programs = []
        errors = []
        for member in parse_sarc(data):
            member_origin = f"{origin}!{member['name']}"
            try:
                nested, nested_errors = _scan_container(member["_payload"], member_origin, depth + 1)
                programs.extend(nested)
                errors.extend(nested_errors)
            except ArchiveError as exc:
                errors.append({
                    "origin": member_origin,
                    "offset": member["offset"],
                    "size": member["size"],
                    "error": str(exc),
                })
        return programs, errors

    raise ArchiveError(f"unsupported container magic {magic.hex()}")


def inventory_sources(
    sources: Iterable[tuple[str, Path]], max_input_bytes: int = MAX_INPUT_BYTES
) -> dict:
    """Inventory explicit local files without persisting code/control bytes."""
    if max_input_bytes <= 0 or max_input_bytes > 512 * 1024 * 1024:
        raise ValueError("max_input_bytes must be in (0, 512 MiB]")

    archives = []
    programs = {}
    errors = []

    for title_id, path in sources:
        title_id = title_id.upper()
        if not re.fullmatch(r"[0-9A-F]{16}", title_id):
            raise ValueError(f"invalid title id {title_id!r}")
        before = path.stat()
        if before.st_size > max_input_bytes:
            raise ArchiveError(
                f"{path.name}: input size {before.st_size} exceeds {max_input_bytes} byte limit"
            )
        data = path.read_bytes()
        after = path.stat()
        if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
            raise ArchiveError(f"{path.name}: source changed during read")

        source_name = path.name
        source_programs = []
        source_errors = []
        try:
            source_programs, source_errors = _scan_container(data, source_name)
        except ArchiveError as exc:
            source_errors.append({"origin": source_name, "error": str(exc)})

        archives.append({
            "title_id": title_id,
            "source_name": source_name,
            "size": len(data),
            "sha256": _sha256(data),
            "records": len(source_programs),
            "errors": len(source_errors),
        })
        errors.extend({"title_id": title_id, **error} for error in source_errors)

        for record in source_programs:
            key = (
                title_id,
                record["stage"],
                record["code_sha256"],
                record["control_sha256"],
                tuple(record["bnsh_version"]),
                record["api_type"],
                record["api_version"],
            )
            origin = {
                "source_name": source_name,
                "container": record["origin"],
                "variation": record["variation"],
                "code_offset": record["code_offset"],
                "control_offset": record["control_offset"],
            }
            if key not in programs:
                programs[key] = {
                    "title_id": title_id,
                    "stage": record["stage"],
                    "code_size": record["code_size"],
                    "code_sha256": record["code_sha256"],
                    "control_size": record["control_size"],
                    "control_sha256": record["control_sha256"],
                    "bnsh_version": record["bnsh_version"],
                    "api_type": record["api_type"],
                    "api_version": record["api_version"],
                    "origins": [],
                }
            programs[key]["origins"].append(origin)

    ordered = sorted(
        programs.values(),
        key=lambda item: (
            item["title_id"],
            item["stage"],
            item["code_sha256"],
            item["control_sha256"],
        ),
    )
    return {
        "schema_version": 1,
        "mode": "manifest-only",
        "upstream": {
            "repository": "zortos293/Lichii",
            "commit": UPSTREAM_COMMIT,
            "blob": UPSTREAM_BLOB,
        },
        "archives": archives,
        "programs": ordered,
        "errors": errors,
    }


def _source_spec(value: str) -> tuple[str, Path]:
    if "=" not in value:
        raise argparse.ArgumentTypeError("source must be TITLE_ID=PATH")
    title_id, raw_path = value.split("=", 1)
    title_id = title_id.upper()
    if not re.fullmatch(r"[0-9A-F]{16}", title_id):
        raise argparse.ArgumentTypeError("title id must be 16 hexadecimal characters")
    path = Path(raw_path)
    if not path.is_file():
        raise argparse.ArgumentTypeError(f"source is not a file: {path}")
    return title_id, path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source", action="append", required=True, type=_source_spec, metavar="TITLE_ID=PATH",
        help="explicit user-owned shader archive/container",
    )
    parser.add_argument("--output", type=Path, help="JSON manifest path; stdout when omitted")
    parser.add_argument(
        "--max-input-mib", type=int, default=MAX_INPUT_BYTES // (1024 * 1024),
        help="per-file read bound, 1..512 MiB (default: 256)",
    )
    args = parser.parse_args()
    if args.max_input_mib < 1 or args.max_input_mib > 512:
        parser.error("--max-input-mib must be between 1 and 512")

    manifest = inventory_sources(args.source, args.max_input_mib * 1024 * 1024)
    payload = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    if args.output:
        output = args.output.resolve()
        sources = {path.resolve() for _, path in args.source}
        if output in sources:
            parser.error("--output must not replace a source archive")
        temporary = output.with_name(output.name + ".tmp")
        temporary.write_text(payload)
        temporary.replace(output)
    else:
        print(payload, end="")


if __name__ == "__main__":
    main()
