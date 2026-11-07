#!/usr/bin/env python3
"""Verify a user-supplied NRMODEL1 against pinned upstream per-tensor SHA-256.

Only public hashes are distributed here, never NVIDIA model weights.
No GPU or PS5 build is performed. Any missing, corrupted, substituted,
truncated, overlapping or misnamed tensor fails closed.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import hmac
from pathlib import Path
import re
import struct
import sys


ROOT = Path(__file__).resolve().parents[2]
REFERENCE = {
    "original": (599, 147756560, "r09_weights_original.sha256", "R09OriginalManifest"),
    "compact": (255, 113917248, "r09_weights_compact.sha256", "R09CompactManifest"),
}


class ModelRejected(ValueError):
    pass


@dataclass(frozen=True)
class ModelPolicy:
    count: int
    file_bytes: int
    hashes: dict[str, str]


def load_hashes(path: Path) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for line in path.read_text(encoding="ascii").splitlines():
        match = re.fullmatch(r"([0-9a-f]{64})  ([^\s]+)", line)
        if not match or match[2] in hashes:
            raise ModelRejected("invalid or duplicated reference SHA-256 metadata")
        hashes[match[2]] = match[1]
    if not hashes:
        raise ModelRejected("empty reference SHA-256 metadata")
    return hashes


def policy_for(variant: str) -> ModelPolicy:
    count, length, name, _ = REFERENCE[variant]
    hashes = load_hashes(Path(__file__).with_name(name))
    if len(hashes) != count:
        raise ModelRejected(f"{variant}: expected {count} distinct reference hashes")
    return ModelPolicy(count, length, hashes)


def check_reference_manifest() -> None:
    manifest = ROOT / "vendor/encore-active/eden-vulkan/include/video_core/renderer_vulkan/nr_rdna2_model_manifest.h"
    text = manifest.read_text(encoding="utf-8")
    for variant, (count, _, _, symbol) in REFERENCE.items():
        block = re.search(
            rf"\b{symbol}\s*=\s*\{{(.*?)\}};", text, flags=re.DOTALL)
        if block is None:
            raise ModelRejected(f"model manifest missing: {symbol}")
        names = re.findall(r'"([^"]+\.bin)"', block[1])
        expected = policy_for(variant).hashes
        if len(names) != count or set(names) != set(expected):
            raise ModelRejected(f"{variant}: source manifest differs from pinned upstream reference")
        print(f"R09_{variant.upper()}_REFERENCE_NAMES_PASS {count}/{count}")


def valid_name(name: str) -> bool:
    if (not name or name.startswith("/") or name.endswith("/") or
            "\\" in name or ":" in name or
            any(ord(c) < 32 or ord(c) == 127 for c in name)):
        return False
    return all(piece not in ("", ".", "..") for piece in name.split("/"))


def read_exact(file, size: int) -> bytes:
    raw = file.read(size)
    if len(raw) != size:
        raise ModelRejected("truncated NRMODEL1 index or tensor")
    return raw


def verify_model(path: Path, policy: ModelPolicy) -> None:
    if not path.is_file():
        raise ModelRejected("model pack not found")
    if path.stat().st_size != policy.file_bytes:
        raise ModelRejected(f"unexpected model pack size (wanted {policy.file_bytes})")
    with path.open("rb") as file:
        if read_exact(file, 8) != b"NRMODEL1":
            raise ModelRejected("invalid NRMODEL1 magic")
        count, reserved = struct.unpack("<II", read_exact(file, 8))
        if count != policy.count or reserved != 0:
            raise ModelRejected("wrong model variant/count or invalid header")
        entries: list[tuple[str, int, int]] = []
        seen: set[str] = set()
        for _ in range(count):
            (length,) = struct.unpack("<I", read_exact(file, 4))
            if not 1 <= length <= 4096:
                raise ModelRejected("invalid tensor name size")
            try:
                name = read_exact(file, length).decode("utf-8")
            except UnicodeDecodeError as exc:
                raise ModelRejected("invalid UTF-8 weight name") from exc
            offset, size = struct.unpack("<QQ", read_exact(file, 16))
            if not valid_name(name) or name not in policy.hashes or name in seen:
                raise ModelRejected("unlisted, duplicated or unsafe weight name")
            seen.add(name)
            entries.append((name, offset, size))
        index_end = file.tell()
        first_payload = (index_end + 255) & ~255
        if seen != policy.hashes.keys():
            raise ModelRejected("incomplete canonical tensor inventory")
        ordered = sorted(entries, key=lambda e: e[1])
        previous_end = first_payload
        for name, offset, length in ordered:
            if (offset % 256 != 0 or length == 0 or length > (256 << 20) or
                    offset < previous_end or length > policy.file_bytes - offset):
                raise ModelRejected(f"overlapping, out-of-range or misaligned tensor: {name}")
            previous_end = offset + length
        # The index has been checked completely before any content digest.
        for name, offset, length in entries:
            file.seek(offset)
            digest = hashlib.sha256()
            pending = length
            while pending:
                piece = read_exact(file, min(pending, 1 << 20))
                digest.update(piece)
                pending -= len(piece)
            if not hmac.compare_digest(digest.hexdigest(), policy.hashes[name]):
                raise ModelRejected(f"incorrect canonical SHA-256 for {name}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-reference", action="store_true",
                        help="check that both pinned upstream SHA inventories match the current vendor model manifest")
    parser.add_argument("--model", type=Path, help="user-owned extracted NRMODEL1 model")
    parser.add_argument("--variant", choices=tuple(REFERENCE))
    args = parser.parse_args()
    try:
        if args.check_reference:
            check_reference_manifest()
            if args.model is None:
                return 0
        if args.model is None or args.variant is None:
            parser.error("--model and --variant are required together")
        policy = policy_for(args.variant)
        verify_model(args.model, policy)
        print(f"R09_{args.variant.upper()}_AUTHENTIC_PACK_SHA256_PASS "
              f"{policy.count}/{policy.count} files, {policy.file_bytes} bytes")
        return 0
    except (ModelRejected, OSError) as error:
        print(f"R09_AUTHENTIC_PACK_REJECTED: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
