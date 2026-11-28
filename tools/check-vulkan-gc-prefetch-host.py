#!/usr/bin/env python3
"""Source/behavior contract for the selected native GC prefetch batch."""
from pathlib import Path

root = Path(__file__).resolve().parents[1]
active = (root / "vendor/encore-active/eden/src/video_core/texture_cache/texture_cache.h").read_text()
begin = active.index("void TextureCache<P>::RunGarbageCollector() {")
end = active.index("\ntemplate <class P>", begin)
gc = active[begin:end]
prefetch = gc[gc.index("const auto PrefetchGc"):gc.index("const auto UseGcPrefetch")]

for marker in (
    "using GcMap = decltype(runtime.DownloadStagingBuffer(size_t{}));",
    "constexpr size_t gc_batch_count = 40;",
    "constexpr size_t gc_batch_bytes = 32_MiB;",
    "boost::container::small_vector<std::pair<ImageId, GcMap>, gc_batch_count> gc_maps;",
    "const size_t rounded = std::bit_ceil(bytes);",
    "if (rounded > gc_batch_bytes - capacity) return true;",
    "runtime.DownloadStagingBuffer(image.unswizzled_size_bytes, true)",
    "runtime.Finish();",
    "runtime.FreeDeferredStagingBuffer",
):
    assert marker in gc or marker in prefetch, marker
assert prefetch.index("++scanned;") < prefetch.index("--remaining;")
assert prefetch.index("--remaining;") < prefetch.index("candidates.push_back(id);")

def admit(sizes, limit=40, cap=32 * 1024 * 1024):
    used = count = 0
    for size in sizes:
        rounded = 1 if size == 0 else 1 << (size - 1).bit_length()
        if count == limit or rounded > cap - used:
            break
        count += 1
        used += rounded
    return count, used

assert admit([1024] * 41)[0] == 40
assert admit([2 * 1024 * 1024] * 40)[0] == 16
assert admit([32 * 1024 * 1024, 1])[0] == 1
print("VULKAN_GC_PREFETCH_SELECTED_PASS batch=40 rounded_cap=32MiB deferred_retirement=1")
