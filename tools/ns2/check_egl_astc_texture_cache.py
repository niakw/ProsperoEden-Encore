#!/usr/bin/env python3
"""N60: exact vendor-owned ASTC cache bridge parity; no native header generator."""
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
PIN = ROOT / "vendor/sources/eden/src/video_core/texture_cache"
ACTIVE = ROOT / "vendor/encore-active/eden-backports/src/video_core/texture_cache"
OWNER = ROOT / "vendor/encore-active/ns2-astc/include/video_core/texture_cache"
CMAKE = (ROOT / "headless/CMakeLists.txt").read_text()

def once(src, old, new):
    assert src.count(old) == 1, ("N60 source owner changed", old[:75])
    return src.replace(old, new)

image = once((PIN / "image_base.h").read_text(),
    '#include "video_core/texture_cache/image_info.h"',
    '''#include "video_core/texture_cache/image_info.h"
#ifdef EDEN_NS2_ASTC_CACHE_BRIDGE
#include <optional>
#include "video_core/texture_cache/ns2_astc_layer_plan.h"
#endif''')
image = once(image, "    u32 guest_size_bytes = 0;",
    '''    u32 guest_size_bytes = 0;
#ifdef EDEN_NS2_ASTC_CACHE_BRIDGE
    // A real cached image tracks guest dirty layers, not a per-title override.
    std::optional<Eden::NS2::Eglantine::AstcDirtyLayerPlanner> ns2_astc_dirty;
#endif''')
assert (OWNER / "image_base.h").read_text() == image, "N60 ImageBase owner/parity drift"

base = once((ACTIVE / "texture_cache_base.h").read_text(),
    "    struct PendingUnswizzle {",
    '''#ifdef EDEN_NS2_ASTC_CACHE_BRIDGE
    bool Ns2AstcEligible(const ImageBase&) const noexcept;
    bool Ns2UploadDirtyLayers(Image&);
#endif

    struct PendingUnswizzle {''')
assert (OWNER / "texture_cache_base.h").read_text() == base, "N60 patched CacheBase owner drift"

# Fix both maintained full sources by their exact git object identities.
# A native change to these files must have a reviewed new baseline; never
# automatically accept an updated hash or silently disable this assertion.
fixed = {
    "texture_cache.h": "fc3125dc06e288b122cee6f11ed750f14068fbb8",
    "ns2_astc_texture_cache_bridge.inc": "62f07399ee09c5ba10dc2f9cf5b962e0108bbd4b",
}
for name, expected in fixed.items():
    actual = subprocess.check_output(["git", "hash-object", str(OWNER / name)],
                                     text=True).strip()
    assert actual == expected, ("N60 maintained vendor owner bytes changed", name, actual)

tex = (OWNER / "texture_cache.h").read_text()
bridge = (OWNER / "ns2_astc_texture_cache_bridge.inc").read_text()
upstream = (ACTIVE / "texture_cache.h").read_text()
needle = "runtime.AccelerateImageUpload(image, staging, FixSmallVectorADL(uploads), 0, 0);"
assert upstream.count(needle) == tex.count(needle) == 1, "full ASTC upload fallback lost"
assert upstream.count("UploadImageContents(image, staging);") == tex.count(
    "UploadImageContents(image, staging);"), "full image upload call count changed"
for marker in ("#ifdef EDEN_NS2_ASTC_CACHE_BRIDGE",
               "ns2_astc_dirty->MarkWrite(cpu_addr, size)",
               "image.ns2_astc_dirty.reset()",
               "if (Ns2UploadDirtyLayers(image))",
               '#include "video_core/texture_cache/ns2_astc_texture_cache_bridge.inc"'):
    assert marker in tex, ("N60 integration owner contract missing", marker)
for marker in ("Ns2AstcEligible(", "Ns2UploadDirtyLayers(",
               "UploadAstcDirtyLayerBatches(", "runtime.AccelerateImageUploadLayers(",
               "runtime.Finish();", "staging.reset();"):
    assert marker in bridge, ("N60 method owner contract missing", marker)
assert bridge.index("runtime.AccelerateImageUploadLayers(") < bridge.index(
    "runtime.Finish();") < bridge.index("staging.reset();"), "unsafe GPU staging lifetime"

assert "EDEN_NS2_ASTC_CACHE_BRIDGE=1" in CMAKE
assert "target_compile_definitions(core PUBLIC EDEN_NS2_ASTC_CACHE_BRIDGE=1)" in CMAKE
assert "target_compile_definitions(video_core PUBLIC EDEN_NS2_ASTC_CACHE_BRIDGE=1)" in CMAKE
assert "NOT EDEN_NS2_ASTC_LAYER_DECODE_EXPERIMENTAL OR EDEN_FINAL_RELEASE_PROFILE" in CMAKE
assert "prepare_egl_astc_texture_cache.py" not in CMAKE
assert "ns2-astc-cache/include" not in CMAKE
assert "EDEN_NS2_ASTC_SCRATCH_TRIM=1" in CMAKE
print("N60_VENDOR_ASTC_CACHE_OWNER_GPU_STAGING_LIFETIME_AND_FULL_FALLBACK_PASS")
