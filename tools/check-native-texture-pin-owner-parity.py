#!/usr/bin/env python3
"""Fail fast if the pinned ASTC and Vulkan native GPU pin owners diverge.

Source-only ownership gate; real C++ instantiation is checked by the native
compiler preflight. Do not replace the shader/texture cache with a mock.
"""
from pathlib import Path

root = Path(__file__).resolve().parents[1]
vendor = root / "vendor/encore-active"
astc = (vendor / "ns2-astc/include/video_core/texture_cache/texture_cache.h").read_text()
vulkan = (vendor / "eden-vulkan/vulkan-cache/video_core/texture_cache/texture_cache.h").read_text()
start = "#ifdef PS5_NATIVE\n// NS2 and NS1 use one TextureCache channel map"
end = "\ntemplate <class P>\nImageViewId TextureCache<P>::VisitImageView("

def owner(text, path):
    assert text.count(start) == 1 and text.count(end) == 1, path
    return text.split(start, 1)[1].split(end, 1)[0].rstrip()

assert owner(astc, "ASTC") == owner(vulkan, "Vulkan"), (
    "ASTC and Vulkan cached native acquisition/lease owners diverged")
for name in ("Image& image, ImageView& view", "Sampler& sampler"):
    assert name in astc, f"GPU pin capability guard missing: {name}"
for text in (astc, vulkan):
    assert text.count("PinNativeGpu();") == 5
    assert "if constexpr (!(requires(Image& image, ImageView& view)" in text
    assert "if constexpr (!(requires(Sampler& sampler)" in text
print("PS5_NATIVE_ASTC_VULKAN_PIN_PARITY_PASS")
