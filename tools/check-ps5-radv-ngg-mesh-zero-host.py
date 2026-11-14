#!/usr/bin/env python3
"""Host-only exact-source PS5 Mesa NGG mesh early-return safety receipt.

This tests the selected pinned C source transformation, not an actual
on-console SPIR-V shader or native RADV compilation. Upstream Mesa #8.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from ci.ps5_radv_ngg_mesh_zero import (
    RELATIVE, PINNED_GIT_BLOB, ANCHOR, PATCH, git_blob,
    patched_bytes, verify_reviewed_output,
)

raw_file = ROOT / "vendor/sources/ps5-mesa" / RELATIVE
raw = raw_file.read_bytes()
assert git_blob(raw) == PINNED_GIT_BLOB
fixed = patched_bytes(raw)
verify_reviewed_output(fixed)
assert fixed.replace(PATCH, ANCHOR, 1) == raw
assert b"nir_store_var(b, state.vertex_count_var, nir_imm_int(b, 0), 0x1)" in fixed
assert b"nir_store_var(b, state.primitive_count_var, nir_imm_int(b, 0), 0x1)" in fixed
assert fixed.index(PATCH) > fixed.index(
    b"nir_local_variable_create(impl, glsl_uint_type(), \"primitive_count_var\")")
assert fixed.index(PATCH) < fixed.index(b"lower_ms_intrinsics(shader, &state);")
assert fixed.index(PATCH) < fixed.index(b"emit_ms_finale(b, &state);")
for bad in (
    raw + b"\n/* unexpected vendor source */\n",
    raw.replace(b"glsl_uint_type()", b"glsl_int_type()", 1),
    fixed,
    raw.replace(ANCHOR, b"   handle_smaller_ms_api_workgroup(b, &state);", 1),
):
    try:
        patched_bytes(bad)
    except AssertionError:
        pass
    else:
        raise AssertionError("unreviewed Mesa source modified or patch repeated")

# No additional shader/descriptor read after a skipped SetMeshOutputs
# is permitted to observe undefined counts: the candidate defaults are
# defined before the original API shader and finale reads them.
code = r"""
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
struct Counts { uint32_t vertex, primitive; };
static struct Counts lower_early_exit(int sets, uint32_t vertices, uint32_t primitives) {
    struct Counts c = {0u, 0u}; /* two inserted nir_store_var defaults */
    if (sets) {c.vertex = vertices; c.primitive = primitives;}
    return c;
}
int main(void) {
    for (uint32_t n = 0; n < 64; ++n) {
        struct Counts no_set = lower_early_exit(0, UINT32_MAX, n);
        assert(no_set.vertex == 0 && no_set.primitive == 0);
        struct Counts explicit_zero = lower_early_exit(1, 0, 0);
        assert(explicit_zero.vertex == 0 && explicit_zero.primitive == 0);
        struct Counts normal = lower_early_exit(1, 32, n);
        assert(normal.vertex == 32 && normal.primitive == n);
    }
}
"""
compilers = [c for c in ("cc", "clang") if shutil.which(c)]
assert compilers, "C compiler missing"
with tempfile.TemporaryDirectory(prefix="radv-ngg-early-exit-") as td:
    src = Path(td) / "counts.c"
    src.write_text(code)
    for cc in compilers:
        exe = Path(td) / (cc + "-fixture")
        subprocess.run([cc, "-std=c11", "-Wall", "-Wextra", "-Werror",
                        "-fsanitize=undefined", "-fno-sanitize-recover=all",
                        str(src), "-o", str(exe)], check=True, timeout=35)
        subprocess.run([str(exe)], check=True, timeout=20)
installer = (ROOT / "tools/install-vendored-radv.py").read_text()
stamper = (ROOT / "tools/radv-active-inputs.py").read_text()
radv = (ROOT / "tools/build-radv-dependencies.sh").read_text()
assert "installed[NGG_MESH]" in installer
assert "verify_ngg_mesh(mesh_staged.read_bytes())" in installer
assert "changed = True" in installer
assert "PATHS = MAINTAINED + (NGG_MESH,)" in stamper
assert "len(PATHS) == len(set(PATHS)) == 15" in stamper
assert "fingerprint(stage)" in stamper
assert 'radv-active-inputs.py" --stamp' in radv
assert 'bash "$vulkan/tools/build-radv.sh" release' in radv
assert raw_file.read_bytes() == raw, "Original Mesa tree mutated"
print("PS5_RADV_NGG_MESH_EARLY_RETURN_HOST_PASS "
      "raw_mesa_immutable=1 staged=only reviewed=15 sources=1 "
      "normal_shader_nonregression=model_only ps5_gpu=unverified")
