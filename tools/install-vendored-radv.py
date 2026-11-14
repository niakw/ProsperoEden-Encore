#!/usr/bin/env python3
"""Install complete checked-in, PS5-patched RADV translation units into Meson's staging tree.

Does NOT mutate the source-controlled upstream Mesa snapshot, and never executes
old replacement expressions as part of the production PS5 build.
"""
from __future__ import annotations
import hashlib
from pathlib import Path
import argparse
import json
import os
import shutil
from ci.ps5_radv_ngg_mesh_zero import (
    RELATIVE as NGG_MESH, patched_bytes as patched_ngg_mesh,
    verify_reviewed_output as verify_ngg_mesh,
)

ROOT = Path(__file__).resolve().parents[1]
ORIGINAL = ROOT / 'vendor/sources/ps5-mesa'
ACTIVE = ROOT / 'vendor/encore-active/ps5-mesa'
PATHS = (
    'src/vulkan/wsi/wsi_common_videoout.c',
    'src/amd/vulkan/radv_cmd_buffer.c',
    'src/amd/vulkan/cl/radv_gs_compute.cl',
    'src/amd/vulkan/radv_pipeline.c',
    'src/amd/vulkan/radv_descriptor_update_template.c',
    'src/amd/vulkan/radv_descriptor_update_template.h',
    'src/amd/vulkan/radv_physical_device.c',
    'src/amd/vulkan/meta/radv_meta_clear.c',
    'src/amd/vulkan/meta/radv_meta_resolve.c',
    # C03: preserve complete maintained Mesa transfer compiler inputs.
    'src/amd/vulkan/meta/radv_meta_buffer.c',
    'src/amd/vulkan/meta/radv_meta_copy.c',
    'src/amd/vulkan/winsys/ps5/radv_ps5_winsys.c',
    'src/amd/vulkan/winsys/ps5/radv_ps5_platform.c',
    'src/util/disk_cache_os.c',
)

# Only exact, Git-verified prior Encore build inputs are accepted.
# A cache restored from an old Actions run can contain complete R343 active
# RADV units mixed with R398 WSI. Each historical byte stream is archived in
# tools/fixtures and checked against its SHA256 in check-vendored-radv-fork.py.
# Never accept arbitrary native cache edits and never mutate immutable Mesa.
# R343 source commit: 1c874ff951b02cf6ea8cef7ce4b110258727575c
# R398 WSI was byte-identical to the R343 WSI.
LEGACY_COMPILER_SHA256 = {
    'src/vulkan/wsi/wsi_common_videoout.c': frozenset({
        '6d54b8d68cc383faa9bbd910e327824689b5315e7ee5617d8981f582c47c2eaa',
    }),
    'src/amd/vulkan/radv_cmd_buffer.c': frozenset({
        '27e4953853887778ca9fae7ef4114ec42e275b550754d6f6b2d218a692e867f5',
    }),
    'src/amd/vulkan/radv_physical_device.c': frozenset({
        '56aed8905eea35687a7e263375ad216843eb5cc4c474f4eb791addaa2599341d',
    }),
    'src/amd/vulkan/winsys/ps5/radv_ps5_winsys.c': frozenset({
        '0aa478ae4c4d3331177185e7a42386c0dc23fc9ff3869333c34ffaafe5e213b0',
    }),
    'src/amd/vulkan/winsys/ps5/radv_ps5_platform.c': frozenset({
        '8112c2b41a600043d3096a0198c4e3c2d7dcf6b56e8f738f6ce8eb537943725c',
    }),
}


# The last successfully pinned pre-R440 WSI is NOT the old R398 fixture:
# R400..R439 legitimately modified this file. R446 restored it from cache.
# Verify the exact original bytes in a checked-in R439 fixture, not a wildcard.
PRE_R440_COMPILER_SHA256 = {
    'src/vulkan/wsi/wsi_common_videoout.c': frozenset({
        '4175fad06454b5c14a2be8045d791deb33fc6034959a7d58b733ed27b22d23b2',
    }),
}

def approved_compiler_input(relative: str, compiled_sha: str, raw_sha: str, active_sha: str) -> bool:
    return (compiled_sha in (raw_sha, active_sha) or
            compiled_sha in LEGACY_COMPILER_SHA256.get(relative, ()) or
            compiled_sha in PRE_R440_COMPILER_SHA256.get(relative, ()))


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def is_owned_disposable_stage(destination: Path) -> bool:
    """Allow a cache-only reset exclusively in the pinned sibling RADV worktree."""
    expected = ROOT.parent / 'mihawk-vulkan-review/.deps/work/radv-src'
    return (
        destination.absolute() == expected.absolute()
        and destination.is_dir()
        and not destination.is_symlink()
        and not destination.parent.is_symlink()
    )


def quarantine_and_reset_stale_input(compiled: Path, original: Path,
                                     relative: str, stale_sha: str) -> None:
    """Save unknown cache bytes, then restore immutable pinned bytes atomically.

    This does not approve the unknown source. The subsequent installation
    must still replace the pinned bytes with the exact versioned active fork.
    """
    if compiled.is_symlink() or original.is_symlink() or not compiled.is_file():
        raise RuntimeError(f'Unsafe RADV staging path: {relative}')
    quarantine = ROOT / 'build/radv-tools/stale-staged-radv-sources'
    quarantine.mkdir(parents=True, exist_ok=True)
    backup = quarantine / (stale_sha + '.c' if compiled.suffix == '.c'
                           else stale_sha + compiled.suffix)
    if backup.exists():
        if digest(backup) != stale_sha:
            raise RuntimeError(f'Corrupt retained RADV cache snapshot: {relative}')
    else:
        temp_backup = backup.with_name(backup.name + f'.tmp-{os.getpid()}')
        try:
            shutil.copy2(compiled, temp_backup)
            if digest(temp_backup) != stale_sha:
                raise RuntimeError(f'RADV stale input changed during quarantine: {relative}')
            temp_backup.replace(backup)
        finally:
            temp_backup.unlink(missing_ok=True)
    temporary = compiled.with_name(compiled.name + f'.pinned-{os.getpid()}')
    try:
        shutil.copy2(original, temporary)
        if digest(temporary) != digest(original):
            raise RuntimeError(f'RADV pinned source copy mismatch: {relative}')
        temporary.replace(compiled)
        os.utime(compiled, None)
    finally:
        temporary.unlink(missing_ok=True)
    print(f'RADV_UNKNOWN_STAGED_SOURCE_QUARANTINED relative={relative} '
          f'stale_sha256={stale_sha} reset_to=immutable_pinned')


def install(destination: Path, provenance: Path | None,
            *, repair_owned_stage: bool = False) -> None:
    if repair_owned_stage and not is_owned_disposable_stage(destination):
        raise RuntimeError('RADV repair permitted only inside owned sibling build staging')
    installed = {}
    changed = False
    for relative in PATHS:
        original = ORIGINAL / relative
        canonical = ACTIVE / relative
        compiled = destination / relative
        if not original.is_file() or not canonical.is_file() or not compiled.is_file():
            raise RuntimeError(f'RADV source missing before installation: {relative}')
        before = digest(compiled)
        raw_sha = digest(original)
        fork_sha = digest(canonical)
        if not approved_compiler_input(relative, before, raw_sha, fork_sha):
            if not repair_owned_stage:
                raise RuntimeError(f'Unrecognized RADV compiler input (refusing to clobber): {relative}, sha256={before}')
            # The initial pinned builder has already run. Quarantine unknown
            # bytes from its disposable stage; never allow their compilation.
            quarantine_and_reset_stale_input(compiled, original, relative, before)
            before = digest(compiled)
            if before != raw_sha:
                raise RuntimeError(f'RADV owned source reset failed: {relative}')
        if before != fork_sha:
            # Atomic replacement allows incremental Ninja to detect only the
            # translated units whose behavior actually differs from upstream.
            temporary = compiled.with_name(compiled.name + f'.active-{os.getpid()}')
            try:
                shutil.copy2(canonical, temporary)
                temporary.replace(compiled)
                # copy2 preserves the checkout mtime, which may predate the
                # first Ninja build's object file. Mark replaced source NEW
                # so the second build recompiles the maintained translation
                # unit instead of silently reusing stale object code.
                os.utime(compiled, None)
            finally:
                temporary.unlink(missing_ok=True)
            changed = True
        installed[relative] = fork_sha

    # A valid SPIR-V mesh shader can exit before SetMeshOutputsEXT. The
    # exact pinned Mesa lowerer reads undefined vertex/primitive counts on
    # that path (mihawk-99/PS5_Mesa #8, device-lost on console).
    # Keep vendor/sources untouched; write ONLY the owned RADV staging
    # compiler unit, following the same two-pass rebuild as the 14 maintained
    # overrides. The 15th source must be included in the archive receipt.
    mesh_original = ORIGINAL / NGG_MESH
    mesh_staged = destination / NGG_MESH
    if (not mesh_original.is_file() or mesh_original.is_symlink() or
        not mesh_staged.is_file() or mesh_staged.is_symlink()):
        raise RuntimeError('Pinned PS5 mesh lowering owner missing/symlinked')
    expected_mesh = patched_ngg_mesh(mesh_original.read_bytes())
    prior_mesh = mesh_staged.read_bytes()
    if prior_mesh not in (mesh_original.read_bytes(), expected_mesh):
        # The previous build may have installed some other patch, which
        # cannot be certified by this exact source hash contract.
        raise RuntimeError('Unreviewed PS5 Mesa mesh compiler source staged')
    if prior_mesh != expected_mesh:
        tmp_mesh = mesh_staged.with_name(mesh_staged.name + f'.reviewed-{os.getpid()}')
        try:
            tmp_mesh.write_bytes(expected_mesh)
            tmp_mesh.replace(mesh_staged)
            os.utime(mesh_staged, None)
        finally:
            tmp_mesh.unlink(missing_ok=True)
        changed = True
    verify_ngg_mesh(mesh_staged.read_bytes())
    installed[NGG_MESH] = hashlib.sha256(expected_mesh).hexdigest()
    if changed and provenance is not None and provenance.exists():
        provenance.replace(provenance.with_suffix('.base.txt'))
    # Always check the final bytes, independently of the chosen source path.
    for relative, expected in installed.items():
        if digest(destination / relative) != expected:
            raise RuntimeError(f'RADV built source changed after active install: {relative}')
    print(f'VENDORED_RADV_INSTALLED changed={changed} files={len(installed)} wsi_sha256={installed[PATHS[0]]}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('destination', type=Path, help='Existing mihawk-vulkan-review/.deps/work/radv-src')
    parser.add_argument('--provenance', type=Path)
    parser.add_argument('--repair-owned-stage', action='store_true',
                        help='Quarantine unknown cached RADV inputs only in the pinned sibling build stage')
    args = parser.parse_args()
    install(args.destination, args.provenance,
            repair_owned_stage=args.repair_owned_stage)
