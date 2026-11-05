#!/usr/bin/env python3
"""Prepare a game-compatible, user-supplied HD texture ROMFS mod for Eden Encore.

No AI model, game assets, executable patches, or texture format conversions
are bundled. The source contains already game-compatible replacement files.
The destination is the existing Mods loader's standard title-scoped ROMFS
layout; the launcher already lets the user enable/disable each pack.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import stat
import tempfile
from pathlib import Path

_CHUNK = 1 << 20
_MAX_FILES = 10000
_MAX_TOTAL_MIB = 8192
_MAX_FILE_MIB = 2048


class PackError(ValueError):
    pass


def _title_id(text: str) -> str:
    if not re.fullmatch(r"[0-9a-fA-F]{16}", text) or int(text, 16) == 0:
        raise PackError("Title ID must be exactly sixteen hexadecimal digits and nonzero")
    return text.upper()


def _pack_name(text: str) -> str:
    stripped = text.strip()
    if not (1 <= len(stripped) <= 48) or stripped in (".", ".."):
        raise PackError("Pack name must contain 1–48 characters")
    if stripped.startswith(".") or ".." in stripped or any(
        not (c.isalnum() or c in " -_.") for c in stripped
    ):
        raise PackError("Pack name contains unsafe characters")
    return "HD Textures - " + stripped


def _is_safe_dir(path: Path) -> bool:
    return path.is_dir() and not path.is_symlink()


def _files(source: Path, max_total_bytes: int, max_file_bytes: int):
    if not _is_safe_dir(source):
        raise PackError("Source ROMFS must be a real directory, not a symlink")
    total = 0
    files = []
    for directory, dirnames, filenames in os.walk(source, followlinks=False):
        base = Path(directory)
        for name in dirnames:
            candidate = base / name
            if candidate.is_symlink():
                raise PackError(f"Symlink directory refused: {candidate}")
        for filename in filenames:
            path = base / filename
            info = path.lstat()
            if not stat.S_ISREG(info.st_mode) or path.is_symlink():
                raise PackError(f"Only regular texture files may be packaged: {path}")
            relative = path.relative_to(source)
            if any(part in (".", "..") for part in relative.parts):
                raise PackError("Unsafe relative path")
            if len(relative.parts) > 20 or len(relative.as_posix()) > 512:
                raise PackError("Texture path exceeds safe package limits")
            size = info.st_size
            if size == 0 or size > max_file_bytes:
                raise PackError(f"Empty or oversized game file: {relative}")
            total += size
            if total > max_total_bytes or len(files) >= _MAX_FILES:
                raise PackError("Texture pack exceeds file count or total disk budget")
            files.append((relative, path, size))
    if not files:
        raise PackError("The source ROMFS directory contains no replacement files")
    # The mod manager resolves ROMFS paths case-insensitively in some contexts.
    # Do not permit two differently-cased replacements to collide.
    lowered = [relative.as_posix().casefold() for relative, _, _ in files]
    if len(lowered) != len(set(lowered)):
        raise PackError("Conflicting case-insensitive ROMFS paths")
    files.sort(key=lambda item: item[0].as_posix())
    return files, total


def _target_root(mods_root: Path, title_id: str) -> Path:
    if mods_root.is_symlink():
        raise PackError("Mods root cannot be a symbolic link")
    mods_root.mkdir(parents=True, exist_ok=True)
    if not _is_safe_dir(mods_root):
        raise PackError("Mods root is not a normal directory")
    matches = [
        entry for entry in mods_root.iterdir()
        if entry.name.casefold() == title_id.casefold()
    ]
    if len(matches) > 1:
        raise PackError("Multiple conflicting title folders exist")
    if matches:
        if not _is_safe_dir(matches[0]):
            raise PackError("Existing title folder is not a normal directory")
        return matches[0]
    title_dir = mods_root / title_id
    title_dir.mkdir()
    return title_dir


def package(source: Path, mods_root: Path, title: str, name: str,
            max_total_mib: int = 2048, max_file_mib: int = 512) -> Path:
    title_id = _title_id(title)
    folder = _pack_name(name)
    if not 1 <= max_total_mib <= _MAX_TOTAL_MIB or not 1 <= max_file_mib <= _MAX_FILE_MIB:
        raise PackError("Configured disk budgets exceed safe limits")
    files, total = _files(source, max_total_mib << 20, max_file_mib << 20)
    if mods_root.exists() and not _is_safe_dir(mods_root):
        raise PackError("Mods root cannot be a symlink or a file")
    title_dir = _target_root(mods_root, title_id)
    destination = title_dir / folder
    if os.path.lexists(destination):
        raise PackError(f"Texture pack already exists; refusing overwrite: {destination}")
    if shutil.disk_usage(mods_root).free < total + (32 << 20):
        raise PackError("Not enough free space for this texture pack")
    with tempfile.TemporaryDirectory(dir=mods_root, prefix=".encore-hd-stage-") as staging:
        pack = Path(staging) / folder
        game_romfs = pack / "romfs"
        game_romfs.mkdir(parents=True)
        entries = []
        for relative, path, original_size in files:
            output = game_romfs / relative
            output.parent.mkdir(parents=True, exist_ok=True)
            digest = hashlib.sha256()
            written = 0
            with path.open("rb") as incoming, output.open("xb") as outgoing:
                while True:
                    data = incoming.read(_CHUNK)
                    if not data:
                        break
                    written += len(data)
                    if written > original_size:
                        raise PackError(f"File changed while copying: {relative}")
                    digest.update(data)
                    outgoing.write(data)
                outgoing.flush()
                os.fsync(outgoing.fileno())
            if written != original_size or path.stat().st_size != original_size:
                raise PackError(f"File changed while copying: {relative}")
            entries.append({
                "path": relative.as_posix(), "bytes": written,
                "sha256": digest.hexdigest()
            })
        manifest = {
            "schema": "eden-encore-hd-romfs-v1", "title_id": title_id,
            "pack_name": name.strip(), "source": "user-supplied",
            "replacement_mode": "game-compatible-romfs",
            "file_count": len(entries), "total_bytes": total,
            "files": entries,
        }
        (pack / "encore-hd-textures.json").write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        # Stage outside the title folder: the existing mod scanner must not
        # see a half-written pack. Final rename is same-filesystem atomic.
        if os.path.lexists(destination):
            raise PackError("Destination appeared while staging; refusing overwrite")
        os.rename(pack, destination)
    return destination


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--title-id", required=True, help="16-hex-digit Switch Title ID")
    parser.add_argument("--source-romfs", type=Path, required=True,
                        help="User-owned, game-compatible ROMFS replacement files")
    parser.add_argument("--mods-root", type=Path, required=True,
                        help="Eden Encore game files' existing mods directory")
    parser.add_argument("--name", required=True, help="Visible game-specific HD texture mod name")
    parser.add_argument("--max-total-mib", type=int, default=2048)
    parser.add_argument("--max-file-mib", type=int, default=512)
    args = parser.parse_args()
    try:
        result = package(args.source_romfs, args.mods_root, args.title_id, args.name,
                         args.max_total_mib, args.max_file_mib)
    except (PackError, OSError) as error:
        parser.exit(2, f"HD_TEXTURE_PACK_REFUSED: {error}\n")
    print(f"HD_TEXTURE_PACK_READY: {result}")
    print("Copy the mods directory to your Eden game files; enable the pack in each game's Mods menu.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
