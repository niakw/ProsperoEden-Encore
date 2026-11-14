#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Repair a real Mesa NIR debug-location output buffer in an isolated PSBC build.

A uint32 location may print 10 decimal digits plus NUL. The pinned Mesa
26.2 source has two char[4] callers and snprintf(buf, 4, "%u", location).
Patch ONLY the staged PSBC working checkout, fail closed on source drift and
restore the exact original source before the next upstream verifier.
"""
from pathlib import Path
import hashlib
import subprocess
import sys

BEFORE = b'snprintf(buf, 4, "%u", location);'
AFTER = b'snprintf(buf, 11, "%u", location);'
SMALL = b'char buf[4];'
LARGE = b'char buf[11];'


def patched_bytes(raw: bytes) -> bytes:
    if (raw.count(BEFORE) != 1 or raw.count(SMALL) != 2 or
            AFTER in raw or LARGE in raw):
        raise ValueError("PSBC NIR location formatter drift: require one 4-byte printf and two callers")
    fixed = raw.replace(BEFORE, AFTER, 1).replace(SMALL, LARGE)
    assert fixed.count(AFTER) == 1 and fixed.count(LARGE) == 2
    return fixed


PINNED_PRINTER = "abc711758a37fd678a49c693f70d002b3f637c11"
PINNED_RADV_STUB = "34437d0216c5438d209b544accddb0030e7fae98"
RADV_STUB_ANCHOR = b"struct radv_instance {"
RADV_FORWARD = b"struct radv_physical_device;\n\n"


def gitblob(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()


def patched_radv_stub(raw: bytes) -> bytes:
    if gitblob(raw) != PINNED_RADV_STUB:
        raise ValueError("Unexpected pinned PSBC RADV stub bytes")
    if raw.count(RADV_STUB_ANCHOR) != 1 or RADV_FORWARD in raw:
        raise ValueError("PSBC RADV declaration drift")
    return raw.replace(RADV_STUB_ANCHOR, RADV_FORWARD + RADV_STUB_ANCHOR, 1)


# PSBC source owners start from upstream PS4-OpenGNM/opengnm-psbc. The PS5 OpenGL\n# staging path has one audited post-verification ACO transformation (a73de0a...);\n# accept only that exact preimage or the pristine upstream blob. Do not patch the\n# separate full Mesa/RADV driver snapshot.
ACO_PATH = "amd/compiler/instruction_selection/aco_select_nir_intrinsics.cpp"
NIR_MASK_PATH = "amd/common/nir/ac_nir_meta_cs_clear_copy_buffer.c"
PINNED_ACO = {"9479ba5f980f1e254801afd6a068282b7b571df8", "a73de0a574bea1cc6f421525047604bebe0be2e6"}
PINNED_NIR_MASK = "9702ce7e1d3fa5dc35118c6eff7a10fdf55f1cde"
ACO_BEFORE = b"ffs(const_offset) > req_lsb_zero"
ACO_AFTER = b"static_cast<unsigned>(ffs(const_offset)) > req_lsb_zero"
MASK_BEFORE = b"nir_channels(&b, value, BITFIELD_MASK(num_dwords))"
MASK_AFTER = b"nir_channels(&b, value, nir_component_mask(num_dwords))"


def patched_aco(raw: bytes) -> bytes:
    digest = gitblob(raw)
    before_count = raw.count(ACO_BEFORE)
    after_count = raw.count(ACO_AFTER)
    if digest not in PINNED_ACO or before_count != 2:
        raise ValueError(
            "Unexpected pinned PSBC ACO offset alignment source "
            f"blob={digest} before={before_count} after={after_count}"
        )
    return raw.replace(ACO_BEFORE, ACO_AFTER)


def patched_nir_mask(raw: bytes) -> bytes:
    digest = gitblob(raw)
    before_count = raw.count(MASK_BEFORE)
    after_count = raw.count(MASK_AFTER)
    if digest != PINNED_NIR_MASK or before_count != 1:
        raise ValueError(
            "Unexpected pinned PSBC NIR partial-store source "
            f"blob={digest} before={before_count} after={after_count}"
        )
    # The key generator computes remainder modulo 4*dwords_per_thread,
    # with 1..4 dwords/thread. The nonzero num_dwords here is 1..3.
    if (b"key->dwords_per_thread <= 4" not in raw or
            b"% (dwords_per_thread * 4)" not in raw):
        raise ValueError("PSBC partial-store domain changed")
    return raw.replace(MASK_BEFORE, MASK_AFTER, 1)



ASSERT_WARNING_OWNERS = {
    "amd/compiler/aco_lower_to_hw_instr.cpp": (
        "337e296ad310279b6aa8e8d96e355d9e049a2acd",
        b"               bool non_linear_vgpr = false;",
        b"               ASSERTED bool non_linear_vgpr = false;",
    ),
    "compiler/nir/nir_unlower_io_to_vars.c": (
        "50361427c7723e544378800f583394bd3024ac40",
        b"            unsigned component, decl_size;",
        b"            ASSERTED unsigned component;\n            unsigned decl_size;",
    ),
    "amd/compiler/aco_spill_preserved.cpp": (
        "80fa7a6ea2cd32785f8b6982666d5d734e3ed3e3",
        b"      bool found_reg = false;",
        b"      ASSERTED bool found_reg = false;",
    ),
    "amd/vulkan/nir/radv_nir_lower_descriptors.c": (
        "241288084c342b659be03e187de13fb0f3d29b0f",
        b"   bool indirect = false;",
        b"   ASSERTED bool indirect = false;",
    ),
}


def patched_assert_warning(path: str, raw: bytes) -> bytes:
    pin, before, after = ASSERT_WARNING_OWNERS[path]
    digest = gitblob(raw)
    if digest != pin or raw.count(before) != 1 or after in raw:
        raise ValueError(
            f"Unexpected PSBC assert-only warning source path={path} "
            f"blob={digest} before={raw.count(before)} after={raw.count(after)}"
        )
    return raw.replace(before, after, 1)

def compile_window(file: Path, command: list[str]) -> int:
    if not file.is_file() or file.is_symlink() or not command:
        raise ValueError("Unsafe PSBC compile-window input")
    original = file.read_bytes()
    digest = hashlib.sha1(b"blob " + str(len(original)).encode() + bytes([0]) + original).hexdigest()
    if digest != PINNED_PRINTER:
        raise ValueError("Unexpected pinned PSBC NIR printer original bytes")
    fixed = patched_bytes(original)
    # Resolve only the sibling stub in the same verified PSBC source tree.
    header = file.parent.parent.parent / "amd/vulkan/radv_instance.h"
    if not header.is_file() or header.is_symlink():
        raise ValueError("Unsafe or missing PSBC RADV stub")
    header_original = header.read_bytes()
    header_fixed = patched_radv_stub(header_original)
    src = file.parent.parent.parent
    aco = src / ACO_PATH
    mask = src / NIR_MASK_PATH
    assert_owners = {relative: src / relative for relative in ASSERT_WARNING_OWNERS}
    for owner in (aco, mask, *assert_owners.values()):
        if not owner.is_file() or owner.is_symlink():
            raise ValueError("Unsafe or missing PSBC compiler owner")
    aco_original = aco.read_bytes()
    mask_original = mask.read_bytes()
    assert_originals = {relative: owner.read_bytes() for relative, owner in assert_owners.items()}
    changes = (
        (file, original, fixed),
        (header, header_original, header_fixed),
        (aco, aco_original, patched_aco(aco_original)),
        (mask, mask_original, patched_nir_mask(mask_original)),
        *((assert_owners[relative], raw, patched_assert_warning(relative, raw))
          for relative, raw in assert_originals.items()),
    )
    try:
        for owner, _, replacement in changes:
            owner.write_bytes(replacement)
        print("PSBC_NIR_LOCATION_BUFFER_11_SAFE compile_window=1", flush=True)
        print("PSBC_RADV_STUB_FILE_SCOPE_PASS compile_window=1", flush=True)
        print("PSBC_ACO_OFFSET_NIR_COMPONENT_MASK_PASS compile_window=1", flush=True)
        print("PSBC_ASSERT_ONLY_WARNING_OWNERS_PASS count=4 compile_window=1", flush=True)
        return subprocess.run(command, check=False).returncode
    finally:
        # Restore each verified owner even if a different restore fails.
        errors = []
        for owner, prior, _ in reversed(changes):
            try:
                owner.write_bytes(prior)
                if owner.read_bytes() != prior:
                    raise RuntimeError(f"PSBC restoration mismatch: {owner}")
            except Exception as error:
                errors.append(str(error))
        if errors:
            raise RuntimeError("PSBC compiler source restoration failed: " + "; ".join(errors))

def main() -> int:
    if len(sys.argv) >= 4 and sys.argv[1] == "--compile":
        return compile_window(Path(sys.argv[2]), sys.argv[3:])
    if len(sys.argv) != 2:
        raise SystemExit("usage: patch-psbc-nir-location-print.py path/to/nir_print.c")
    file = Path(sys.argv[1])
    if not file.is_file() or file.is_symlink():
        raise SystemExit("refusing absent/symlinked PSBC NIR source")
    file.write_bytes(patched_bytes(file.read_bytes()))
    print("PSBC_NIR_LOCATION_BUFFER_11_SAFE", file.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
