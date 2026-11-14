#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Insert exact PSBC compile-window hooks after upstream source verification.

The original tracked scripts are backed up and restored by build-opengl-sdk.sh.
No upstream verifier or Git index is altered. Only the named make invocation
may run with a temporary change to the NIR diagnostic printer.
"""
from pathlib import Path
import hashlib
import sys

HOOKS = {
    "build-opengnm-psbc.sh": (
        "9ecdbba37aebaae96ffb8dfb29e494f9f53c4a41",
        'make -B -j"$jobs" CONFIG="$config_file" CCACHE="$ccache_launcher"',
        'python3 -B "$ENCORE_PSBC_NIR_PATCHER" --compile '
        '"$psbc_dir/src/compiler/nir/nir_print.c" ',
    ),
    "build-opengnm-psbc-ps5.sh": (
        "18e02a428619ea0e0d46471d3fae158fe361fcaa",
        'make -C "$source_dir" -f "$makefile" -B -j"$jobs"',
        'python3 -B "$ENCORE_PSBC_NIR_PATCHER" --compile '
        '"$source_dir/src/compiler/nir/nir_print.c" ',
    ),
}

def gitblob(raw):
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()

def patched_script(path: Path):
    if path.is_symlink() or not path.is_file() or path.name not in HOOKS:
        raise ValueError("Unknown or unsafe PSBC build script")
    digest, anchor, prefix = HOOKS[path.name]
    raw = path.read_bytes()
    if gitblob(raw) != digest:
        raise ValueError("Unexpected PSBC build script preimage")
    source = raw.decode("utf-8")
    assert source.count(anchor) == 1
    assert source.index("--verify-psbc") < source.index(anchor)
    path.write_text(source.replace(anchor, prefix + anchor, 1))

if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: patch-psbc-nir-build-hooks.py script")
    patched_script(Path(sys.argv[1]))
