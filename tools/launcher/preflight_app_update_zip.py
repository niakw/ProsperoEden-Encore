#!/usr/bin/env python3
"""Offline R21 preflight for a SHA-256-pinned, directory-style PS5 app ZIP.

Preflight is NOT a native installer. It neither extracts ZIP entries nor
modifies the installed app. Run only after obtaining a digest from the
expected official release channel (not from the archive itself).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import stat
import sys
import zipfile
from pathlib import Path

TITLE = "PPSA99008"
CONTENT_ID = "UP9000-PPSA99008_00-PROSPEROEDEN0001"
MAX_ZIP = 1024 * 1024 * 1024
MAX_FILES = 8192
MAX_UNPACKED = 2 * 1024 * 1024 * 1024
MAX_FILE = 512 * 1024 * 1024
MAX_PARAM = 65536
# Installation may preserve user state; a remote archive must never replace it.
PROTECTED = (
    "roms/", "keys/", "firmware/", "updates/", "dlc/", "saves/",
    "userdata/", "data/", "wallpapers/", "savedata/", "user/",
    "mods/", "assets/keys/", "assets/firmware/", "assets/roms/",
    "assets/updates/", "assets/dlc/", "assets/mods/", "assets/saves/",
    "language.txt", "prosperoeden.json",
)
REQUIRED = {
    "eboot.bin", "sce_sys/param.json", "sce_module/libc.prx",
}


class UnsafeUpdate(ValueError):
    pass


def version_tuple(value: str) -> tuple[int, int, int]:
    if not isinstance(value, str) or not re.fullmatch(r"\d{2}\.\d{3}\.\d{3}", value):
        raise UnsafeUpdate("invalid PS5 contentVersion")
    return tuple(int(piece) for piece in value.split("."))


def verify_digest(path: Path, expected: str) -> int:
    if not isinstance(expected, str) or not re.fullmatch(r"[a-f0-9]{64}", expected):
        raise UnsafeUpdate("a lowercase SHA-256 from the official release is required")
    if path.is_symlink() or not path.is_file():
        raise UnsafeUpdate("archive must be a regular file")
    size = path.stat().st_size
    if not 1024 <= size <= MAX_ZIP:
        raise UnsafeUpdate("archive outside bounded byte budget")
    actual = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            actual.update(chunk)
    if actual.hexdigest() != expected:
        raise UnsafeUpdate("release SHA-256 mismatch")
    return size


def checked_name(raw: str) -> str:
    if not raw or raw.startswith("/") or "\\" in raw or "\x00" in raw or ":" in raw:
        raise UnsafeUpdate("unsafe absolute/escaped ZIP name")
    if any(part in ("", ".", "..") for part in raw.rstrip("/").split("/")):
        raise UnsafeUpdate("unsafe ZIP traversal or empty segment")
    if raw.startswith(f"{TITLE}/"):
        raw = raw[len(TITLE) + 1:]
    elif raw == TITLE or raw == f"{TITLE}/":
        return ""
    if not raw:
        return ""
    if raw.casefold().startswith(PROTECTED):
        raise UnsafeUpdate("archive attempts to replace user-owned state")
    if len(raw.encode("utf-8", "replace")) > 260:
        raise UnsafeUpdate("unreasonably long ZIP path")
    return raw.rstrip("/")


def inspect_zip(path: Path, expected_sha256: str, installed_version: str) -> dict:
    """Return metadata only. Never extract/mutate an application."""
    verify_digest(path, expected_sha256)
    old_version = version_tuple(installed_version)
    try:
        with zipfile.ZipFile(path, "r", allowZip64=False) as archive:
            items = archive.infolist()
            if len(items) > MAX_FILES:
                raise UnsafeUpdate("too many ZIP entries")
            files: set[str] = set()
            lower: set[str] = set()
            total = 0
            param = None
            for item in items:
                name = checked_name(item.filename)
                mode = item.external_attr >> 16
                kind = stat.S_IFMT(mode)
                if item.flag_bits & 1:
                    raise UnsafeUpdate("encrypted ZIP entry")
                if item.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED):
                    raise UnsafeUpdate("unsupported ZIP compression")
                if kind not in (0, stat.S_IFREG, stat.S_IFDIR):
                    raise UnsafeUpdate("symlink or special file in ZIP")
                if not name:
                    if not item.is_dir():
                        raise UnsafeUpdate("unexpected archive root file")
                    continue
                if name.casefold() in lower:
                    raise UnsafeUpdate("duplicate or case-colliding archive path")
                lower.add(name.casefold())
                if item.is_dir():
                    if kind not in (0, stat.S_IFDIR):
                        raise UnsafeUpdate("directory has non-directory mode")
                    continue
                if kind == stat.S_IFDIR:
                    raise UnsafeUpdate("file masquerading as directory")
                if item.file_size > MAX_FILE:
                    raise UnsafeUpdate("ZIP entry exceeds file budget")
                if name in REQUIRED and item.file_size == 0:
                    raise UnsafeUpdate("empty required native app file")
                if name == "eboot.bin" and item.file_size < 1024:
                    raise UnsafeUpdate("native executable is too small")
                total += item.file_size
                if total > MAX_UNPACKED:
                    raise UnsafeUpdate("ZIP expands beyond total budget")
                if item.file_size > 1024 * 1024 and (
                    item.compress_size <= 0 or item.file_size > item.compress_size * 1000
                ):
                    raise UnsafeUpdate("suspicious ZIP compression ratio")
                files.add(name)
                if name == "sce_sys/param.json":
                    if item.file_size > MAX_PARAM:
                        raise UnsafeUpdate("oversized param.json")
                    with archive.open(item, "r") as stream:
                        raw = stream.read(MAX_PARAM + 1)
                    if len(raw) > MAX_PARAM:
                        raise UnsafeUpdate("oversized decoded param.json")
                    try:
                        param = json.loads(raw)
                    except (UnicodeError, ValueError) as ex:
                        raise UnsafeUpdate("invalid param.json") from ex
            if not REQUIRED.issubset(files) or not isinstance(param, dict):
                raise UnsafeUpdate("missing required native app files")
            if param.get("titleId") != TITLE or param.get("contentId") != CONTENT_ID:
                raise UnsafeUpdate("wrong PS5 title/content identity")
            new_version = version_tuple(param.get("contentVersion"))
            if new_version <= old_version:
                raise UnsafeUpdate("PS5 package version is not newer")
            return {
                "ok": True, "title_id": TITLE,
                "content_version": param["contentVersion"],
                "files": len(files), "uncompressed_bytes": total,
                "note": "Host preflight only: no native install is authorized",
            }
    except (OSError, zipfile.BadZipFile, zipfile.LargeZipFile, RuntimeError) as ex:
        raise UnsafeUpdate("invalid or unreadable ZIP archive") from ex


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("--sha256", required=True,
                        help="trusted lowercase SHA-256 from official release")
    parser.add_argument("--installed-version", required=True,
                        help="installed sce_sys/param.json contentVersion (NN.NNN.NNN)")
    args = parser.parse_args()
    try:
        report = inspect_zip(args.archive, args.sha256, args.installed_version)
    except UnsafeUpdate as ex:
        print(json.dumps({"ok": False, "reason": str(ex)}), file=sys.stderr)
        return 2
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
