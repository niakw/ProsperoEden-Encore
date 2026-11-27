#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Selected GC prefetch and eviction budgets stay independent and bounded."""
from pathlib import Path

root = Path(__file__).resolve().parents[1]
active = (root / "vendor/encore-active/eden/src/video_core/texture_cache/texture_cache.h").read_text()
begin = active.index("void TextureCache<P>::RunGarbageCollector() {")
end = active.index("\ntemplate <class P>", begin)
gc = active[begin:end]
prefetch = gc[gc.index("const auto PrefetchGc"):gc.index("const auto UseGcPrefetch")]
cleanup = gc[gc.index("const auto Cleanup"):gc.index("const auto CollectEligible")]

for marker in (
    "constexpr size_t gc_scan_limit = 8192;",
    "constexpr size_t gc_batch_count = 40;",
    "constexpr size_t gc_batch_bytes = 32_MiB;",
    "size_t remaining = num_iterations;",
    "size_t scanned = 0;",
    "const size_t rounded = std::bit_ceil(bytes);",
    "if (rounded > gc_batch_bytes - capacity) return true;",
    "projected_usage -= (std::min)(projected_usage, reclaimed);",
):
    assert marker in gc, marker
assert prefetch.index("++scanned;") < prefetch.index("--remaining;")
assert prefetch.index("--remaining;") < prefetch.index("candidates.push_back(id);")
assert cleanup.index("++gc_scanned;") < cleanup.index("--num_iterations;")
assert "gc_scanned = 0;\n        PrefetchGc();" in gc
assert "num_iterations = aggressive_mode ? 40 : (high_priority_mode ? 20 : 10);" in gc

def visit(statuses, budget=10, cap=8192):
    scanned = attempts = 0
    for status in statuses:
        if attempts == budget or scanned >= cap:
            break
        scanned += 1
        if status in {"decoding", "costly"}:
            continue
        attempts += 1
    return scanned, attempts

mixed = ["decoding"] * 120 + ["costly"] * 60 + ["eligible"] * 24
assert visit(mixed) == (190, 10)
assert visit(["decoding"] * 20000, 40) == (8192, 0)
assert visit(["eligible"] * 100, 40) == (40, 40)
print("SELECTED_GC_PREFETCH_BUDGET_PASS scan=8192 batch=40 bytes=32MiB")
