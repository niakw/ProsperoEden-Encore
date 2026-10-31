# NSW2 N54 — release huge ASTC/texture scratch at frame boundaries

Commit scope: `research/ns2-ps5-compatibility` only. `main`, pinned vendor, default native build, final release unchanged.

Eglantine [97ce27a](https://github.com/Djihads80/Eglantine/commit/97ce27ab35153884d2fd05c278433928e429cd91) observed temporary texture processing buffers retained after huge layered terrain uploads, including 341 MiB-class intermediate allocations. Native PS5 Encore still uses the pinned `Common::ScratchBuffer` without `release()`, and its generic `TextureCache<P>::TickFrame` does not trim these CPU scratch allocations.

N54 implements an **experimental actual source overlay**, not an inert planner:

- The CMake-only owner generator derives the full `common/scratch_buffer.h` and `video_core/texture_cache/texture_cache.h` headers from the *prepared* build source, avoiding vendored 110-KB duplicates and preserving all PS5 backports.
- `release()` frees the scratch allocation and resets capacity/size. The existing `resize()` path now skips a zero-byte `memcpy` after release.
- At the start of `TextureCache<P>::TickFrame`, both swizzle and unswizzle scratch buffers drop allocations **larger than** 64 MiB. Exactly 64 MiB stays cached. It does not modify GPU residency, decode scheduling, dispatch or buffer-cache invalidation.
- Explicit CMake gate `EDEN_NS2_ASTC_SCRATCH_RELEASE_EXPERIMENTAL=ON` requires native PS5+NS2 metadata, is OFF by default and forbidden in `EDEN_FINAL_RELEASE_PROFILE`.
- Parity script reconstructs exact original headers and the altered span, then compiles/runs the **extracted actual frame-trim snippet** against real `ScratchBuffer` under Clang/GCC with ASan/UBSan. Exercises >64 MiB release, 64 MiB preservation, post-release allocation, preserved resize data and repeated releases.

This trims retained CPU scratch, **not** selective ASTC per-layer upload or sparse Vulkan binding. Those still need complete image/mip/queue integration and native PS5 validation. A green host test does not measure PS5 memory usage or FPS, and no console test is requested.
