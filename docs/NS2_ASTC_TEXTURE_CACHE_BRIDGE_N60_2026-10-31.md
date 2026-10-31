# NSW2 N60 — native PS5 ASTC texture-cache layer bridge

Experimental `EDEN_NS2_ASTC_TEXTURE_CACHE_BRIDGE_EXPERIMENTAL=ON`, OFF by default; requires PS5-native Vulkan, NS2 metadata and N57 ASTC layer decoder. Forbidden in final release. Only `research/ns2-ps5-compatibility`.

N60 now integrates directly into a single versioned vendor texture-cache owner, with opt-in `ImageBase`/`TextureCacheBase` definitions under `EDEN_NS2_ASTC_CACHE_BRIDGE`. No engine file is generated at CMake configure and the shipping patched PS5 texture cache remains the baseline. After a successful full ASTC array upload, each image can retain an N55 per-layer planner. Real `TextureCache<P>::WriteMemory` marks guest-written layers, and actual `RefreshContents` calls the N59 staging transaction and N57 Vulkan layer decode under strict eligibility checks. On unmap, alias, sparse, GPU-modified, converted, rescaled, async or other unsupported images the unchanged full upload remains available. With N54 enabled its prepared scratch-trimmed texture cache is the source, so the two research changes compose without wholesale upstream replacement.

**Status**: code-path source integration, not validated native execution. CI checks the source-owner insertions and preserved full fallback; Clang/GCC host tests cover N55/N57/N59 separately. Production PS5 compiler, true Vulkan GPU readback and concurrency validation remain outstanding, so not enabled for users. ImageBase layout changes are research-only and must be compiled consistently across video_core/core. No console testing requested.


## N60 vendor source consolidation (31 October)
- `vendor/encore-active/ns2-astc/include/video_core/texture_cache/texture_cache.h` contains both the N54 and N60 changes behind independent compile definitions; no second texture-cache translation unit or full-cache copy is generated.
- The matching `image_base.h`, `texture_cache_base.h`, and small `ns2_astc_texture_cache_bridge.inc` live in the same vendor owner root. N55/N59 helpers remain in `vendor/encore-active/ns2-helpers/include`.
- `core` and `video_core` now select the same image-layout header and both receive the N60 compile definition, preventing different `ImageBase` layouts.
- N60 remains OFF by default and requires N57 and the PS5 experimental metadata profile. The full-image upload fallback is preserved.
- The partial path calls `runtime.Finish()` before releasing staged bytes. This deliberately introduces a synchronous GPU completion cost while correctness is unproven; replacing it requires a verified fence-owned staging lifetime. It is not evidence of PS5 performance.

Exact vendor owner bytes are pinned by the host gate; N54's CPU scratch regression is compiled from the actual versioned header. The old N60 source-generating script has been removed. Native compilation/GPU readback and race validation remain outstanding.
