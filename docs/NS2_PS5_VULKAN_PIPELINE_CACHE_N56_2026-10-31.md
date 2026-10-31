# NSW2 N56 — safe PS5 Vulkan driver cache load (Eglantine)

Branch: `research/ns2-ps5-compatibility`. No default, release, vendor or main changes.

Upstream [Eglantine ea33ad1](https://github.com/Djihads80/Eglantine/commit/ea33ad1865970ee731e5f74dbcc26ca472798afe) adds atomic save and short-header detection. The **maintained PS5 native owner already has an atomic .new/rename/save-lock writer**: never copy that change over it. A remaining read-side risk is `static_cast<size_t>(end) - header_size` when the file is shorter than the 12-byte magic+version header, which can underflow and produce a very large allocation request.

N56 adds only the missing **header-size admission before any read or subtraction**, closes and removes corrupt cache, and lets the existing Vulkan path create a fresh empty cache. The full generated translation unit comes from native `vk_pipeline_cache_cost.cpp` and is checked for exact owner parity and retained atomic save. This is available only under `EDEN_NS2_EGLANTINE_PIPELINE_CACHE_EXPERIMENTAL=ON`, with PS5 native Vulkan + NS2 metadata; OFF by default, forbidden under final release.

The host harness extracts the actual added guard and tests every file length 0..24 bytes with Clang/GCC UBSan; only lengths below 12 are discarded. This proves local header admission, not driver-specific behavior, improved FPS, or successful NSW2 game boot. No console test requested.
