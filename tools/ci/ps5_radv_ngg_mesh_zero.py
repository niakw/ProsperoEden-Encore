#!/usr/bin/env python3
"""Exact PS5 RADV owned-stage Mesa NGG mesh early-return safety transform.

Do not touch vendor/sources/ps5-mesa (immutable). Source owner is the Mesa
AMD NGG mesh lowering in the PS5 RADV static driver, NOT guest emulator
Vulkan translation. Upstream: mihawk-99/PS5_Mesa issue 8.
"""
from __future__ import annotations

import hashlib

RELATIVE = "src/amd/common/nir/ac_nir_lower_ngg_mesh.c"
PINNED_GIT_BLOB = "1809ccb1538e1ccfaabbd4d55968b5b82206121c"
ANCHOR = (
    b"   nir_builder builder = nir_builder_at(nir_before_impl(impl));\n"
    b"   nir_builder *b = &builder; /* This is to avoid the & */\n\n"
    b"   handle_smaller_ms_api_workgroup(b, &state);"
)
PATCH = (
    b"   nir_builder builder = nir_builder_at(nir_before_impl(impl));\n"
    b"   nir_builder *b = &builder; /* This is to avoid the & */\n\n"
    b"   /* Upstream PS5_Mesa #8: a valid mesh shader can return before\n"
    b"    * SetMeshOutputsEXT. Its finale must never read uninitialized\n"
    b"    * vertex/primitive counts or request an absurd GS_ALLOC_REQ.\n"
    b"    */\n"
    b"   nir_store_var(b, state.vertex_count_var, nir_imm_int(b, 0), 0x1);\n"
    b"   nir_store_var(b, state.primitive_count_var, nir_imm_int(b, 0), 0x1);\n\n"
    b"   handle_smaller_ms_api_workgroup(b, &state);"
)

def git_blob(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()

def patched_bytes(raw: bytes) -> bytes:
    """Fail closed unless this is the exact old pinned PS5 Mesa input."""
    assert git_blob(raw) == PINNED_GIT_BLOB, (
        "Unreviewed PS5 Mesa NGG source. Refuse patch/rebase by guess.")
    assert raw.count(ANCHOR) == 1 and PATCH not in raw
    assert raw.count(b'nir_local_variable_create(impl, glsl_uint_type(), "vertex_count_var")') == 1
    assert raw.count(b'nir_local_variable_create(impl, glsl_uint_type(), "primitive_count_var")') == 1
    assert b"set_ms_final_output_counts(b, s, &num_prm, &num_vtx);" in raw
    new = raw.replace(ANCHOR, PATCH, 1)
    assert new.count(PATCH) == 1 and new.count(ANCHOR) == 0
    assert new.replace(PATCH, ANCHOR, 1) == raw
    assert git_blob(new) != PINNED_GIT_BLOB
    return new

def verify_reviewed_output(raw: bytes) -> None:
    """Require exactly our approved patch and exact historical reversibility."""
    assert raw.count(PATCH) == 1, "Missing approved mesh-zero staging insertion"
    old = raw.replace(PATCH, ANCHOR, 1)
    assert git_blob(old) == PINNED_GIT_BLOB, (
        "Unexpected native Mesa source drift outside two mesh output defaults")
    assert patched_bytes(old) == raw
