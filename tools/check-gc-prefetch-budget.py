#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""R442: GC staging budget must mirror the actual eviction budget."""
from pathlib import Path
root = Path(__file__).resolve().parents[1]
included = (root / "vendor/tests/oracles/vulkan/vulkan_gc_downloads.inc").read_text()
active = (root / "vendor/encore-active/eden-vulkan/vulkan-cache/video_core/texture_cache/texture_cache.h").read_text()
port = (root / "tools/prepare-vulkan-port.py").read_text()
gc_begin = active.index("void TextureCache<P>::RunGarbageCollector() {")
gc_end = active.index("\ntemplate <class P>", gc_begin)
gc = active[gc_begin:gc_end]
# The historical oracle remains tracked under encore-active, whereas the
# maintained Vulkan texture cache is the actual compiled source. Check both.
assert "(vulkan_oracle / 'vulkan_gc_downloads.inc').read_text()" in port
for statement in (
    "size_t remaining = num_iterations;",
    "size_t scanned = 0;",
    "const bool count_visits = ::Eden::Performance::gc_count_visits.load(std::memory_order_relaxed);",
    "if (remaining == 0 || scanned >= max_scanned) return true;",
    "if (count_visits) --remaining;",
    "if (!count_visits) --remaining;",
):
    assert statement in included and statement in gc, statement
assert gc.count("if (remaining == 0 || scanned >= max_scanned) return true;") == 1
assert gc.count("num_scanned >= max_scanned") == 1

def visit(candidates, budget=10, cap=8192, old=False):
    """Model the shared scan decisions; statuses 0=decoding, 1=costly, 2=evictable."""
    scanned = removed = 0
    for status in candidates:
        if budget == 0 or scanned >= cap:
            break
        scanned += 1
        if old:
            budget -= 1
        if status != 2:
            continue
        if not old:
            budget -= 1
        removed += 1
    return scanned, removed

# Previously the prefetch loop spent its 10 slots on decoding textures.
items = [0] * 120 + [1] * 60 + [2] * 24
assert visit(items) == (190, 10)
assert visit(items, old=True) == (10, 0)
# The 8192 cap bounds the scan even under memory pressure.
assert visit([0] * 20000) == (8192, 0)
for stop in (10, 20, 40):
    for skipped in (0, 1, 99, 8192):
        items = [0, 1] * (skipped // 2) + ([0] if skipped % 2 else []) + [2] * 60
        visits, deleted = visit(items, budget=stop)
        assert visits <= 8192 and deleted <= stop
        if skipped < 8192:
            assert deleted == stop
print("R442: prefetch/GC scan budget parity source + behavioral model PASS")

# The native NS1/NS2 CMake overlay has its own GC implementation.
selected = (root / "vendor/encore-active/ns2-astc/include/video_core/texture_cache/texture_cache.h").read_text()
begin = selected.index("void TextureCache<P>::RunGarbageCollector()")
end = selected.index("\ntemplate <class P>", begin)
active_gc = selected[begin:end]
prefetch = active_gc[active_gc.index("const auto PrefetchGc"):active_gc.index("const auto UseGcPrefetch")]
cleanup = active_gc[active_gc.index("const auto Cleanup"):active_gc.index("const auto CollectEligible")]
assert "constexpr size_t gc_scan_limit = 8192;" in active_gc
assert "scanned >= gc_scan_limit" in prefetch
assert "gc_scanned >= gc_scan_limit" in cleanup
assert prefetch.index("++scanned;") < prefetch.index("ImageFlagBits::IsDecoding") < prefetch.index("--remaining;")
assert cleanup.index("++gc_scanned;") < cleanup.index("ImageFlagBits::IsDecoding")
assert cleanup.index("(!high_priority_mode && must_download)") < cleanup.index("--num_iterations;", cleanup.index("(!high_priority_mode && must_download)"))
assert "gc_scanned = 0;\n        PrefetchGc();" in active_gc
assert "num_iterations = aggressive_mode ? 40 : (high_priority_mode ? 20 : 10);" in active_gc
# Both real and speculative traversals spend the scan budget on every visit.
# Only eligible attempts consume the separate eviction budget, even if
# staging later rejects them. This conservative prefix stops at a clean or
# unsupported candidate rather than reading across an ordinary eviction.
def active_scan(items, budget, prefetch=False, high=True, aggressive=False):
    scanned = attempts = removed = 0
    candidates = []
    for i, (decoding, costly, dirty, invalid) in enumerate(items):
        if attempts == budget or scanned >= 8192:
            break
        scanned += 1
        if decoding or (costly and not aggressive) or (dirty and not high):
            continue
        if prefetch and (not dirty or invalid):
            break
        attempts += 1
        if not invalid:
            removed += 1
            candidates.append(i)
    return scanned, attempts, removed, candidates
protected = [(True, False, False, False)] * 120 + [(False, True, False, False)] * 60
clean = [(False, False, False, False)] * 24
dirty = [(False, False, True, False)] * 40
assert active_scan(protected + clean, 10, high=False)[:3] == (190, 10, 10)
assert active_scan(protected + dirty, 20, prefetch=True) == active_scan(protected + dirty, 20)
assert active_scan([(True, False, False, False)] * 8192 + clean, 40)[:3] == (8192, 0, 0)
assert active_scan([(False, False, True, True)] * 100, 40)[:3] == (40, 40, 0)
assert active_scan(protected + clean + dirty, 20, prefetch=True)[3] == []
print("SELECTED_GC_SCAN_BUDGET_PASS")
