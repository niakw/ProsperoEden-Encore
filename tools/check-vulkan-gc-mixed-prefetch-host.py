#!/usr/bin/env python3
"""Mixed-state behavioral model bound to the selected native GC source."""
from pathlib import Path

root = Path(__file__).resolve().parents[1]
active = (root / "vendor/encore-active/eden/src/video_core/texture_cache/texture_cache.h").read_text()
a = active.index("void TextureCache<P>::RunGarbageCollector() {")
b = active.index("\ntemplate <class P>", a)
gc = active[a:b]
prefetch = gc[gc.index("const auto PrefetchGc"):gc.index("const auto UseGcPrefetch")]
for marker in (
    "ImageFlagBits::IsDecoding",
    "ImageFlagBits::CostlyLoad",
    "ImageFlagBits::BadOverlap",
    "ImageFlagBits::Sparse",
    "ImageFlagBits::Remapped",
    "!image.aliased_images.empty()",
    "!image.overlapping_images.empty()",
    "image.info.num_samples != 1",
    "image.HasScaled()",
    "FullDownloadCopies(image.info).empty()",
):
    assert marker in prefetch, marker
assert "if (candidates.size() < 2) return;" in prefetch
assert "projected_usage -= (std::min)(projected_usage, reclaimed);" in prefetch

def scan(states, budget=40, cap=8192):
    scanned = attempts = 0
    accepted = []
    for i, state in enumerate(states):
        if attempts == budget or scanned >= cap:
            break
        scanned += 1
        if state in {"decoding", "costly"}:
            continue
        if state in {"overlap", "sparse", "remapped", "scaled", "no-copies"}:
            break
        attempts += 1
        accepted.append(i)
    return scanned, attempts, accepted

states=["decoding"]*120+["costly"]*60+["dirty"]*5
assert scan(states,10)==(185,5,list(range(180,185)))
assert scan(["decoding"]*9000,40)[:2]==(8192,0)
assert scan(["dirty","overlap","dirty"],40)==(2,1,[0])
print("VULKAN_GC_MIXED_SELECTED_PASS protected_skip=1 unsafe_prefix_stop=1 scan_cap=8192")
