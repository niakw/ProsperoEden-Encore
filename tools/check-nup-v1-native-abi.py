#!/usr/bin/env python3
"""Compile native NUP FileSys/VFS adapters against pinned vendor headers (host only).

Only the native file, RomFS and loader API headers are fetched at the gitlink SHA.
This is a C++ ABI/source-signature preflight, NOT a full vendor/core/PS5 build.
"""
from __future__ import annotations

import os
from pathlib import Path
import subprocess
import tempfile
from urllib.request import Request, urlopen
import sys

ROOT = Path(__file__).resolve().parent.parent
FILES = (
    "common/common_funcs.h",
    "common/common_types.h",
    "core/file_sys/fs_filesystem.h",
    "core/file_sys/common_funcs.h",
    "core/file_sys/romfs.h",
    "core/file_sys/vfs/vfs.h",
    "core/file_sys/vfs/vfs_types.h",
    "core/file_sys/vfs/vfs_vector.h",
    "core/file_sys/vfs/vfs_layered.h",
    "common/bit_field.h",
    "common/swap.h",
    "core/file_sys/control_metadata.h",
    "core/file_sys/program_metadata.h",
    "core/loader/loader.h",
    "core/loader/deconstructed_rom_directory.h",
)

def main() -> None:
    # The pinned C++ source must prefer an NPDM-verified embedded Switch 2
    # program before a valid legacy update ExeFS, including with full RomFS.
    content = (ROOT / "headless/nup_v1_native_content.cpp").read_text()
    exefs = content.split("FileSys::VirtualDir ContentSet::ExeFS() const {", 1)[1].split(
        "FileSys::VirtualFile ContentSet::CreateRomFS(", 1)[0]
    assert exefs.index("FindEmbeddedSwitch2Program(*mount_)") < exefs.index("if (newest_update)")
    assert "metadata.IsSwitch2()" in content
    assert "(packages[*newest].title_id >> 56) != 0x01" in content
    embedded = content.split("std::optional<EmbeddedSwitch2Program> FindEmbeddedSwitch2Program", 1)[1].split("} // namespace", 1)[0]
    assert "if (p.kind == 0) return std::nullopt" not in embedded
    assert "base ? mount.PackageView(*base, ContentView::ExeFS)" in embedded
    assert "!newest || base_exefs ||" in embedded
    assert "standalone_update" not in embedded
    loader = (ROOT / "headless/nup_v1_native_loader.cpp").read_text()
    identity = loader.split("const bool matching_embedded_edition =", 1)[1].split("if ((declared->kind == 0", 1)[0]
    assert "declared->kind == 1 && metadata.IsSwitch2()" in identity
    assert "standalone_update" not in identity
    assert "embedded->program_id != *caller_program_id" in content
    romfs = content.split("FileSys::VirtualFile ContentSet::CreateRomFS(bool allow_upgrade_pack) const {", 1)[1].split(
        "FileSys::VirtualFile ContentSet::CreateAddOnRomFS(", 1)[0]
    assert "FileSys::LayeredVfsDirectory::MakeLayeredDirectory(" in romfs
    assert "{embedded->romfs, std::move(directory)}" in romfs
    assert "CreateRomFS(std::move(directory), nullptr)" in romfs
    pinned = subprocess.check_output(
        ["git", "-C", str(ROOT), "rev-parse", "HEAD:vendor"], text=True
    ).strip()
    assert len(pinned) == 40 and all(c in "0123456789abcdef" for c in pinned), pinned
    urlbase = ("https://raw.githubusercontent.com/niakw/"
               "Prospero.Eden-Encore-vendor/" + pinned + "/")
    # A locally mounted vendor submodule at the exact gitlink SHA is a
    # stronger and much faster source of truth than repeated HTTP downloads.
    # If absent in a CI sandbox, retain the original pinned-URL fallback.
    local_vendor = ROOT / "vendor"
    local_sha = subprocess.run(
        ["git", "-C", str(ROOT / "vendor"), "rev-parse", "HEAD"],
        capture_output=True, text=True, check=False)
    local_verified = (
        local_sha.returncode == 0 and local_sha.stdout.strip() == pinned)

    with tempfile.TemporaryDirectory() as folder:
        includes = Path(folder)
        for path in FILES:
            # The PS5-selected NS2 loader uses the maintained, versioned
            # program-metadata header, not the stale upstream Eden header.
            # Fetch the exact selected owner under the immutable gitlink.
            source_path = (
                "encore-active/ns2-helpers/include/" + path
                if path == "core/file_sys/program_metadata.h"
                else "sources/eden/src/" + path
            )
            request = Request(urlbase + source_path,
                              headers={"User-Agent": "EdenEncore-NUP-ABI-CI"})
            local_path = local_vendor / source_path
            if local_verified and local_path.is_file():
                data = local_path.read_bytes()
            else:
                with urlopen(request, timeout=20) as response:
                    data = response.read(128 * 1024 + 1)
            if len(data) > 128 * 1024 or not data.startswith(b"// SPDX-"):
                raise ValueError(f"Invalid pinned vendor header: {source_path}")
            if path == "core/file_sys/program_metadata.h" and b"IsSwitch2() const" not in data:
                raise ValueError("PS5-selected NS2 ProgramMetadata interface missing")
            target = includes / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        # Apple Clang diagnoses anonymous vendor ABI structs differently
        # from GCC. Suppress only this known extension diagnostic on macOS.
        vendor_abi_flags = ["-Wno-nested-anon-types"] if sys.platform == "darwin" else []
        subprocess.run([
            os.environ.get("CXX", "g++"), "-std=c++20", "-fsyntax-only",
            *vendor_abi_flags,
            # The actual vendor AppLoader header intentionally names unused
            # virtual-function parameters. Keep all other warnings fatal.
            "-Wall", "-Wextra", "-Werror", "-Wno-unused-parameter", "-pedantic",
            "-I", str(includes),
            "-I", str(ROOT / "headless"),
            str(ROOT / "headless/nup_v1_native_vfs.cpp"),
            str(ROOT / "headless/nup_v1_native_content.cpp"),
            str(ROOT / "headless/nup_v1_native_aoc.cpp"),
            # The real AppLoader requires the complete core, kernel, service
            # and FS build graph. It is compiled in the separate native
            # profile; the existing executable NUP host fixture covers its
            # selected code path against the host ABI. This pinned-header
            # check qualifies the changed VFS/ContentSet owners directly.
        ], check=True)
    print(f"NUP native adapter compiles against pinned vendor VFS headers {pinned[:12]}")

if __name__ == "__main__":
    main()
