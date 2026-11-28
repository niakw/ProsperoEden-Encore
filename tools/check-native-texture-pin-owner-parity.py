#!/usr/bin/env python3
"""Fail fast if the canonical native texture pin owner loses GPU pin contracts.

Source-only ownership gate; real C++ instantiation is checked by the native
compiler preflight. The consolidated Encore tree has one maintained
TextureCache owner for ASTC and Vulkan paths.
"""
from pathlib import Path

root = Path(__file__).resolve().parents[1]
owner_path = root / "vendor/encore-active/eden/src/video_core/texture_cache/texture_cache.h"
text = owner_path.read_text()
start = "#ifdef PS5_NATIVE\n// NS2 and NS1 use one TextureCache channel map"
end = "\ntemplate <class P>\nImageViewId TextureCache<P>::VisitImageView("

assert text.count(start) == 1 and text.count(end) == 1, owner_path
block = text.split(start, 1)[1].split(end, 1)[0].rstrip()
for name in ("Image& image, ImageView& view", "Sampler& sampler"):
    assert name in block, f"GPU pin capability guard missing: {name}"
assert block.count("PinNativeGpu();") == 6
assert "if constexpr (!(requires(Image& image, ImageView& view)" in block
assert "if constexpr (!(requires(Sampler& sampler)" in block
print("PS5_NATIVE_TEXTURE_PIN_OWNER_PASS owner=canonical")
