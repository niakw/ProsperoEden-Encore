#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Selected native texture-GC scan contract; source + behavioral model only."""
from pathlib import Path

root = Path(__file__).resolve().parents[1]
active = (root / "vendor/encore-active/eden/src/video_core/texture_cache/texture_cache.h").read_text()
start = active.index("void TextureCache<P>::RunGarbageCollector() {")
end = active.index("\ntemplate <class P>", start)
gc = active[start:end]

for marker in (
    "constexpr size_t gc_scan_limit = 8192;",
    "constexpr size_t gc_batch_count = 40;",
    "constexpr size_t gc_batch_bytes = 32_MiB;",
    "const auto PrefetchGc = [&] {",
    "size_t remaining = num_iterations;",
    "size_t scanned = 0;",
    "if (remaining == 0 || scanned >= gc_scan_limit ||",
    "++scanned;",
    "--remaining;",
    "|| gc_scanned >= gc_scan_limit",
    "++gc_scanned;",
    "--num_iterations;",
    "gc_scanned = 0;",
    "PrefetchGc();",
):
    assert marker in gc, marker

prefetch = gc[gc.index("const auto PrefetchGc"):gc.index("const auto UseGcPrefetch")]
assert prefetch.index("++scanned;") < prefetch.index("ImageFlagBits::IsDecoding")
assert prefetch.index("ImageFlagBits::IsDecoding") < prefetch.index("--remaining;")
cleanup = gc[gc.index("const auto Cleanup"):gc.index("const auto CollectEligible")]
assert cleanup.index("++gc_scanned;") < cleanup.index("ImageFlagBits::IsDecoding")
assert cleanup.index("ImageFlagBits::IsDecoding") < cleanup.rindex("--num_iterations;")
collect = gc[gc.index("const auto CollectEligible"):gc.index("Configure(false);")]
assert collect.index("gc_scanned = 0;") < collect.index("PrefetchGc();")
assert collect.index("PrefetchGc();") < collect.index("lru_cache.ForEachItemBelow")

def model(statuses, budget=10, cap=8192):
    scanned = attempts = 0
    for protected in statuses:
        if attempts == budget or scanned >= cap:
            break
        scanned += 1
        if protected:
            continue
        attempts += 1
    return scanned, attempts

assert model([True] * 200 + [False] * 15) == (210, 10)
assert model([True] * 10000) == (8192, 0)
assert model([False] * 100) == (10, 10)
print("SELECTED_GC_SCAN_CONTRACT_PASS scan_limit=8192 eviction_budget_independent=1")
