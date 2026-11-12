#!/usr/bin/env python3
"""N60: exact vendor-owned ASTC cache bridge parity; no native header generator."""
from pathlib import Path
import subprocess
from native_astc_vendor_parity import reverse_r23_checked_astc

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
# P2.2b extends the ASTC texture-cache owner with exactly the same gated
# Vulkan native channel/pin ABI as the canonical Vulkan owner. Do NOT accept
# arbitrary ASTC rewrites or update the historical N60 baseline hash: strip
# only those reviewed additions and compare the legacy owner byte-for-byte.
VULKAN = ROOT / "vendor/encore-active/eden-vulkan/vulkan-cache/video_core/texture_cache"
gate = "#ifdef PS5_NATIVE"

def native_block(text: str, following: str) -> str:
    # The shared PS5 compilation guard also surrounds unrelated code; only
    # the exact QMD image-view/sampler declaration or implementation block
    # may be stripped for legacy NS1 ASTC source parity.
    signature = ("    // An already authenticated native TIC/TSC record" if
                 "Fill image_view_ids" in following else
                 "// NS2 and NS1 use one TextureCache channel map")
    start = gate + "\n" + signature
    assert text.count(start) == 1, "N60 native ABI gate drift"
    tail = text.split(start, 1)[1]
    assert tail.count(following) == 1, "N60 native ABI footer drift"
    result = start + tail.split(following, 1)[0]
    assert result.endswith("#endif\n"), "N60 native ABI block not closed"
    return result

base_owned = (OWNER / "texture_cache_base.h").read_text()
base_footer = "\n    /// Fill image_view_ids"
base_native = native_block(base_owned, base_footer)
assert base_native == native_block(
    (VULKAN / "texture_cache_base.h").read_text(), base_footer
), "N60 ASTC native declaration ABI diverged from shared Vulkan owner"
owner_marker = """// Host ABI witness: when the ASTC profile is selected, the active
// TextureCache header must be THIS maintained variant, not Vulkan's
// similarly named cache base or the historical Eden owner.
#if defined(EDEN_NS2_ASTC_CACHE_BRIDGE)
#define EDEN_NS2_ASTC_TEXTURE_CACHE_OWNER_SELECTED 1
#endif

"""
assert base_owned.count(owner_marker) == 1, "N60 ASTC owner provenance drift"
assert base_owned.count("#include <memory>\n") == 1
legacy_base = base_owned.replace(owner_marker, "", 1).replace(
    "#include <memory>\n", "", 1
).replace("\n" + base_native, "", 1)
assert legacy_base == base, "N60 patched CacheBase owner drift after native ABI isolation"

tex = (OWNER / "texture_cache.h").read_text()
impl_footer = "\ntemplate <class P>\nImageViewId TextureCache<P>::VisitImageView"
impl_native = native_block(tex, impl_footer)
assert impl_native == native_block(
    (VULKAN / "texture_cache.h").read_text(), impl_footer
), "N60 ASTC native implementation ABI diverged from shared Vulkan owner"
legacy_tex = reverse_r23_checked_astc(ROOT, "texture_cache.h", tex).replace(
    impl_native + "\n", "", 1)
legacy_sha = subprocess.run(
    ["git", "hash-object", "--stdin"], input=legacy_tex,
    text=True, check=True, capture_output=True
).stdout.strip()
# The original N60 baseline was fc3125dc... before R4's independently
# reviewed native volume-copy path. Require the exact integrated R4 owner and
# its guarded source, rather than treating R4 as a source-parity regression.
owner_full_sha = subprocess.check_output([
    "git", "hash-object", str(OWNER / "texture_cache.h")
], text=True).strip()
assert owner_full_sha == "da6ab6dcea2a1c02fcb2e862d111dc410b025d66", (
    "N60/R4 ASTC selected source owner drift", owner_full_sha
)
assert legacy_sha == "77f6051ea65933df920669ad61499f5847ad7516", (
    "N60/R4 normalized selected ASTC implementation changed", legacy_sha
)
assert tex.count("#if defined(PS5_NATIVE) && defined(EDEN_NS2_VOLUME_COPY)") == 2
assert tex.count("copy_native_volume_slice") == 2
assert "registry.IsGraphicsCurrent(maxwell3d, *ticket)" in tex
assert "if (copy_native_volume_slice()) {\n        return true;" in tex
bridge_sha = subprocess.check_output([
    "git", "hash-object", str(OWNER / "ns2_astc_texture_cache_bridge.inc")
], text=True).strip()
assert bridge_sha == "62f07399ee09c5ba10dc2f9cf5b962e0108bbd4b", (
    "N60 ASTC bridge owner bytes changed", bridge_sha
)
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
assert "option(EDEN_NS2_ASTC_TEXTURE_CACHE_BRIDGE_EXPERIMENTAL" not in CMAKE
assert "# N60: one shared PS5 Vulkan texture-cache/ImageBase ABI" in CMAKE
assert "if(PS5_NATIVE AND EDEN_PS5_VULKAN)" in CMAKE
assert "prepare_egl_astc_texture_cache.py" not in CMAKE
assert "ns2-astc-cache/include" not in CMAKE
assert "EDEN_NS2_ASTC_SCRATCH_TRIM=1" in CMAKE
print("N60_VENDOR_ASTC_CACHE_OWNER_GPU_STAGING_LIFETIME_AND_FULL_FALLBACK_PASS")
