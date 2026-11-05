#!/usr/bin/env python3
"""Exercise the actual C++ native-helper ZIP parser against disposable host archives.

Calls a precompiled helper_archive_check executable. No console paths or live
network requests are used.
"""
import json
import os
import pathlib
import stat
import subprocess
import sys
import tempfile
import zipfile

if len(sys.argv) != 2:
    raise SystemExit("Usage: test_native_helper_archive.py compiled-helper-check")

binary = pathlib.Path(sys.argv[1]).resolve()
assert binary.is_file(), binary

data = {
    "titleId": "PPSA99008",
    "contentId": "UP9000-PPSA99008_00-PROSPEROEDEN0001",
    "contentVersion": "01.400.323",
}
base_files = {
    "PPSA99008/eboot.bin": b"E" * 4096,
    "PPSA99008/sce_sys/param.json": json.dumps(data).encode(),
    "PPSA99008/sce_module/libc.prx": b"L" * 1200,
    "PPSA99008/ui/icon0.tga": b"TGA_IMAGE",
}


def run_case(folder: pathlib.Path, name: str, files: dict, mode: str,
             extra=None):
    path = folder / f"{name}.zip"
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        for entry, payload in files.items():
            z.writestr(entry, payload)
        if extra:
            extra(z)
    dest = folder / f"out-{name}"
    result = subprocess.run([str(binary), mode, str(path), str(dest)],
                            capture_output=True, text=True, timeout=15)
    if result.returncode:
        raise AssertionError(f"{name}: rc={result.returncode} "
                             f"stdout={result.stdout} stderr={result.stderr}")
    if mode == "valid" and not (dest / "eboot.bin").is_file():
        raise AssertionError(f"{name}: no executable extracted")
    if name == "extra-app" and (dest / "OTHERAPP").exists():
        raise AssertionError("Unrelated app was extracted")
    if mode == "reject" and dest.exists():
        raise AssertionError(f"{name}: rejected archive created a destination")


with tempfile.TemporaryDirectory(prefix="encore-native-helper-") as tmp:
    folder = pathlib.Path(tmp)
    run_case(folder, "valid", base_files, "valid")
    run_case(folder, "path-traversal",
             {**base_files, "PPSA99008/../escape.txt": b"ESCAPE"}, "reject")
    run_case(folder, "protected-keys",
             {**base_files, "PPSA99008/assets/keys/prod.keys": b"SECRET"}, "reject")
    run_case(folder, "protected-roms",
             {**base_files, "PPSA99008/roms/game.nsp": b"SECRET"}, "reject")
    run_case(folder, "no-eboot",
             {k: v for k, v in base_files.items() if not k.endswith("/eboot.bin")},
             "reject")
    run_case(folder, "no-metadata",
             {k: v for k, v in base_files.items() if not k.endswith("param.json")},
             "reject")
    run_case(folder, "duplicate", base_files, "reject",
             extra=lambda z: z.writestr("PPSA99008/eboot.bin", b"duplicate"))

    def symlink(z):
        link = zipfile.ZipInfo("PPSA99008/linked")
        link.create_system = 3
        link.external_attr = (stat.S_IFLNK | 0o777) << 16
        z.writestr(link, "eboot.bin")
    run_case(folder, "symlink", base_files, "reject", extra=symlink)

    def extra_app(z):
        z.writestr("OTHERAPP/sce_sys/param.json", json.dumps(data))
    run_case(folder, "extra-app", base_files, "valid", extra=extra_app)

print("R21 native C++ helper: 2 safe extraction cases and 7 unsafe ZIP cases PASS")
