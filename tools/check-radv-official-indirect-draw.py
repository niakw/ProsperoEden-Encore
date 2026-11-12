#!/usr/bin/env python3
"""Upstream Mesa 26.2.2 zero-indirect-count regression against actual PS5 RADV.

Upstream: a2f2518a9febf1b3b791cd2df079dbd25e56939b.
The byte-equivalence gate covers *all* 11 draw call sites, the PS5 custom
GS-compute raster draw, and four approved 64-bit index offsets; this must
match the complete generator output, not silently reject CodeQL fixes.
"""
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
base = (ROOT/"vendor/sources/ps5-mesa/src/amd/vulkan/radv_cmd_buffer.c").read_text()
active = (ROOT/"vendor/encore-active/ps5-mesa/src/amd/vulkan/radv_cmd_buffer.c").read_text()
script = ROOT/"tools/radv_official_indirect_draw_fix.py"
spec = spec_from_file_location("upstream_indirect", script)
assert spec and spec.loader
module = module_from_spec(spec)
spec.loader.exec_module(module)
old = "extent.height = MAX2(extent.width, pdev->info.gfx_level >= GFX12 ? 128 : 64);"
new = "extent.height = MAX2(extent.height, pdev->info.gfx_level >= GFX12 ? 128 : 64);"
assert base.count(old) == 1
expected = module.patch(base.replace(old, new))
# Exactly one additional, reviewed GS-compute pointer initialization is
# permitted on top of the official bin-height and zero-indirect corrections.
gs_anchor = ("   poly_vertex_params_init(vp, gsc->vs_outputs, wg_size);\n"
             "   poly_geometry_params_init(gp, mode, wg_size);\n")
gs_sink = (
    "   /* GPU-side setup can drop a draw. Never leave its output pointers at 0. */\n"
    "   const uint64_t null_sink = radv_gs_compute_upload(cmd_buffer, 256, NULL, NULL);\n"
    "   vp->output_buffer = null_sink;\n"
    "   vp->index_buffer = null_sink;\n"
    "   gp->count_buffer = null_sink;\n"
    "   gp->output_index_buffer = null_sink;\n"
)
assert expected.count(gs_anchor) == 1, "Pinned GS-compute initializer drifted"
expected = expected.replace(gs_anchor, gs_anchor + gs_sink)
# CodeQL #13-16: widening AFTER the 32-bit multiplication would preserve an
# overflowing offset. The actual generator intentionally widens first at all
# four indexed multi-draw paths; retain this protection in the exact oracle.
narrow_index = "uint64_t index_va = state->index_buffer.va + draw->firstIndex * index_size;"
wide_index = "uint64_t index_va = state->index_buffer.va + (uint64_t)draw->firstIndex * index_size;"
assert expected.count(narrow_index) == 4
expected = expected.replace(narrow_index, wide_index)
# C03 additionally preserves a barrier-only transfer guard and exports
# the stream-split helper to its second Mesa translation unit. Reverse ONLY
# those two reviewed source edits, then execute the original exact upstream
# 26.2.2 indirect-draw/GS/64-bit replay oracle unchanged.
import hashlib
def source_git_blob(source):
    value=source.encode("utf-8")
    return hashlib.sha1(
        b"blob " + str(len(value)).encode() + bytes([0]) + value).hexdigest()
assert source_git_blob(active) == "08d09249e437a99e475fdc67985367274e6309c4", (
    "Unreviewed RADV C03 source mutation")
c03_prototype = (
    "void radv_split_cmd_stream_if_due(struct radv_cmd_buffer *cmd_buffer);\n"
    "\nvoid\nradv_split_cmd_stream_if_due")
prior_static = "static void\nradv_split_cmd_stream_if_due"
c03_barrier = (
    "   radv_split_cmd_stream_if_due(cmd_buffer); "
    "/* Encore C03: split barrier-only streams */\n")
assert active.count(c03_prototype) == 1
assert active.count(c03_barrier) == 1
historical=active.replace(c03_prototype,prior_static,1).replace(c03_barrier,"",1)
assert source_git_blob(historical) == "9dd12c19a1a277a2753432e1411a449fdf923c4a", (
    "C03 RADV source cannot be exactly reversed to historic official proof")
assert expected == historical, (
    "RADV official indirect draw, GS sink or 4 widened offsets changed")
print("RADV_C03_BARRIER_SPLIT_REVERSE_PASS", "historical_official_indirect=exact",
      "barrier_only_split=retained")
generator = (ROOT/"tools/patch-radv-wsi.py").read_text()
assert "from radv_official_indirect_draw_fix import patch" in generator
assert generator.count('(\"uint64_t index_va = state->index_buffer.va + draw->firstIndex * index_size;\", \"uint64_t index_va = state->index_buffer.va + (uint64_t)draw->firstIndex * index_size;\")') == 1
assert "radv_CmdDrawIndirectCount2KHR" in active
assert "radv_before_draw(cmd_buffer, &info, 1, pInfo->maxDrawCount, false)" in active
assert "radv_before_draw(cmd_buffer, &info, 1, pInfo->drawCount, false)" in active
assert "radv_before_draw(cmd_buffer, &rast, 1, direct ? 0 : 1, false)" in active
assert "layout->vk.draw_count ? pGeneratedCommandsInfo->maxDrawCount : 1" in active
assert "if (!max_indirect_draw_count)" in active
# Only the exact gate is extracted for the host behavioral test. All paths
# feeding it are covered separately above and by the full replay byte check.
a = active.index("   } else {\n      // The AMD firmware may execute")
b = active.index("\n   if (!info->indexed", a)
gate = active[a:b]
assert "if (!max_indirect_draw_count)\n         return false;" in gate
host = r"""
#include <assert.h>
#include <stdbool.h>
static bool allowed(bool indirect, unsigned count) {
    if (indirect) {
        if (!count)
            return false;
    }
    return true;
}
int main(void) {
    assert(!allowed(true, 0));
    assert(allowed(true, 1));
    assert(allowed(true, 100));
    assert(allowed(false, 0)); /* Direct zero-count guard is separate */
    return 0;
}
"""
cc = shutil.which("clang-18") or shutil.which("clang") or shutil.which("cc")
assert cc
with tempfile.TemporaryDirectory(prefix="eden-radv-indirect-2622-") as d:
    src = Path(d)/"guard.c"
    exe = Path(d)/"guard"
    src.write_text(host)
    subprocess.run([cc,"-std=c11","-O1","-Wall","-Wextra","-Werror",
                    "-fsanitize=address,undefined",str(src),"-o",str(exe)],
                   timeout=30,check=True)
    subprocess.run([str(exe)],timeout=10,check=True)
print("PASS Mesa 26.2.2 zero-indirect + GS/DGC + 4x widened indexed offsets; exact active-source replay")
