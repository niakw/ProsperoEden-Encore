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
legacy_tex = tex.replace(impl_native + "\n", "", 1)
# R4 research deliberately modifies the real N60 TextureCache. Preserve the
# immutable N60 SHA gate by removing ONLY the exact, SHA-pinned R4 additions
# before replaying the historical parity test. Other edits still fail.
r4_pin = "99fc3e73c97c99b48ed870fb26105e20f6cae944"
current_vendor = subprocess.check_output([
    "git", "-C", str(ROOT / "vendor"), "rev-parse", "HEAD"
], text=True).strip()
if current_vendor == r4_pin:
    assert "EDEN_RESEARCH_NS2_R4_VOLUME" in CMAKE
    assert "option(EDEN_RESEARCH_NS2_R4_VOLUME" in CMAKE
    r4_sha = subprocess.check_output([
        "git", "hash-object", str(OWNER / "texture_cache.h")
    ], text=True).strip()
    assert r4_sha == "dccf7eab3485f69ce6bb31c0ea96a473349639e6", (
        "R4 modified N60 owner outside reviewed native candidate", r4_sha
    )
    for addition in (
        "#include <algorithm>\n",
        "#include <iterator>\n",
        "#include <span>\n",
        "#include <type_traits>\n",
        '#if defined(PS5_NATIVE) && defined(EDEN_RESEARCH_NS2_R4_VOLUME)\n'
        '#include "core/hle/service/nvdrv/devices/native_gpu_channel_registry.h"\n'
        '#endif\n',
        "namespace Vulkan { class TextureCacheRuntime; }\n\n",
    ):
        assert legacy_tex.count(addition) == 1, ("R4 preamble drift", addition)
        legacy_tex = legacy_tex.replace(addition, "", 1)
    start = ("#if defined(PS5_NATIVE) && defined(EDEN_RESEARCH_NS2_R4_VOLUME)\n"
             "    // Vulkan-only candidate, isolated from shared NS1 and OpenGL template instantiations.\n")
    stop = "\n#endif\n    const auto result = GetBlitImages(dst, src, copy);"
    assert legacy_tex.count(start) == legacy_tex.count(stop) == 1, "R4 BlitImage block drift"
    before, rest = legacy_tex.split(start, 1)
    candidate, after = rest.split(stop, 1)
    assert "copy_native_volume_slice" in candidate and "IsGraphicsCurrent" in candidate
    legacy_tex = before + "    const auto result = GetBlitImages(dst, src, copy);" + after
legacy_sha = subprocess.run(
    ["git", "hash-object", "--stdin"], input=legacy_tex,
    text=True, check=True, capture_output=True
).stdout.strip()
assert legacy_sha == "fc3125dc06e288b122cee6f11ed750f14068fbb8", (
    "N60 maintained ASTC implementation changed outside reviewed native ABI",
    legacy_sha
)
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
