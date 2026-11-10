# NS2 production-owner commit queue — R4 started, R2/R3 scoped

## LIVE UPDATE — R2/R3/R4 source branches (supersedes historical entries below)

| Point | Source committed | Remaining source integration | Validation |
| --- | --- | --- | --- |
| R4 3D slices | [Vendor PR #36](https://github.com/niakw/Prospero.Eden-Encore-vendor/pull/36), current main parity restored | 0 new source files; existing active file must compile | Not done on actual owner / PS5 |
| R2 upload batch | [Vendor PR #38](https://github.com/niakw/Prospero.Eden-Encore-vendor/pull/38), bounded 64-copy, epoch/owner-aware helper | **2 files identified:** scheduler header and buffer-copy runtime; allocation provenance may require more | Helper not wired or compiled against true owner |
| R3 GOB16 | [Vendor PR #37](https://github.com/niakw/Prospero.Eden-Encore-vendor/pull/37), complete maintained decoder with 32-entry table | **1 file identified:** Encore native CMake translation-unit selection | Maintained source not yet selected/compiled |

**COUNT: 3/3 code tracks have real isolated source commits; 3/3 still require actual source/runtime qualification; at least 3 integration files remain (2 R2 + 1 R3).** Counts do not include future test fixtures or additional allocation-owner changes.

Old [vendor PR #35](https://github.com/niakw/Prospero.Eden-Encore-vendor/pull/35) was closed without merge after an unrelated pin-parity change conflicted in the R4 source file. Its replacement **#36** preserves that new Vulkan/OpenGL pin-parity code and is mergeable. The current vendor `main` and Encore `main` gitlink are `90c9c8a203a27181e23349a889a8f2a7d1cd9dd2`; **no main, pins, releases or PS5 builds changed**.

**The sections below document the historical first R4 draft and original R2/R3 plan; use this live update for current PR numbers and progress.**

---

**Updated:** 2026-11-10. Source audit is CLOSED for the frozen upstream snapshot; this document tracks **code preparation**, which is NOT complete.

## Commit 1 — R4 native Fermi2D 3D volume slice copy

**Actual active vendor source committed, not merely a model.**

- Branch: [`research/ns2-r4-safe-volume-slice-20261110`](https://github.com/niakw/Prospero.Eden-Encore-vendor/tree/research/ns2-r4-safe-volume-slice-20261110)
- Draft [vendor PR #35](https://github.com/niakw/Prospero.Eden-Encore-vendor/pull/35).
- Only changed active code: `encore-active/eden-vulkan/vulkan-cache/video_core/texture_cache/texture_cache.h`.
- Guards: `PS5_NATIVE`, native graphics-engine process generation ticket, matching active cache/graphics pointer, genuine Fermi2D SrcCopy/Point, complete 3D BlockLinear slice, compatible pixel formats/width/height/depth, distinct cached images and level-zero slice, bounded `gpu_addr` offset, no stale Remapped/Sparse image, pre-copy channel ticket recheck. If any check fails: existing general blit path.
- Uses the maintained `PrepareImage`, `FlushDeferredClear`, `CopyImage`, `ForEachImageInRegionGPU` and cache tracker. No game-ID special cases or new cache owner. NS1 lacks a native graphics ticket and cannot take this path.
- Initial commit `3f0add18`, then source-flag compatibility and owner/dimension hardening `81375105`, `c806e3de`.

**R4 not signed off:** full PS5-native source compile, actual Fermi2D guest command replay, negative Blend/ROP/Bilinear run in real cache, source/destination 3D image Vk handles, overlap/remap/alias and fence retirement, PS5 pixels and NS1 regression all pending. No release or merge permitted. The 50-case host policy fixture in this Encore audit is NOT the same as compiling the active vendor patch.

## Commit 2 — R2 in-order Vulkan upload batching (not yet written)

**Real integration owners verified:**

- `encore-active/eden-vulkan/vk_buffer_cache_cost.cpp::BufferCacheRuntime::CopyBuffer`: two existing paths, an explicitly synchronized in-order `scheduler.Record` path, and a separate `can_reorder_upload` path. The existing zero-copy handling and pre/post Vulkan barriers must be retained.
- `encore-active/eden-vulkan/include/video_core/renderer_vulkan/vk_scheduler.h::RecordWithUploadBuffer`: current command-serial, dispatch chunk rollover, error invalidation and outside-renderpass semantics. The upstream `RecordUpload` API is **not** already present in Encore.

**Next source commit only after:** actual allocation-bound `VkBufferCopy` preflight (no zero/overflow/out-of-buffer); preserve all WAR/RAW/destination-overlap exclusions (max 64); flush pending upload copies on every non-upload recording/command-buffer submission, renderpass transition, tick and exception path; record barriers around the whole batch with correct read/write scopes; real scheduler tick, error injection and NS1 order tests. No assumptions of safe reordered copies.

## Commit 3 — R3 GOB 16-byte block-linear swizzle (not yet written)

**Real source owner verified:** `sources/eden/src/video_core/textures/decoders.cpp`, currently compiled from the pinned Eden source set. Its public API uses normal tiling and includes the BPP cases 1/2/3/4/6/8/12/16. Unlike Lichii's newer signature, the pinned Encore API does not pass a `native_tiling` flag.

**Next source commit only after:** choose an explicit `encore-active` overlay/override CMake source route rather than silently modifying or fork-replacing the pinned upstream `sources/` tree; preserve the full public decoder interface. Compare the actual maintained `SwizzleImpl` and `SwizzleSubrectImpl` owner against a new 16-byte path with the current public API. Admit 16-byte fast full-frame copies and power-of-two BPP subrect runs only; fallback for 3/6/12. Run current decoder API regression vectors on NS1 and NS2, including 3D, partial edge and padding, then measure on PS5.

## Version/race discipline

- Main Encore and its vendor gitlink are owned by the ongoing P5 native build effort. Do **not** change gitlinks, pins, source inventory, PS5 workflows, releases or main branches here.
- R4 vendor draft began at the audit-pinned vendor `22b69d60`. The vendor `main` subsequently advanced to `f9f08786` by one unrelated `encore-active/ns2-astc` edit. No rebase, merge or pin change done here.
- Host-only source audit evidence in [the closeout](NS2_UPSTREAM_REFRESH_AND_CLOSEOUT_2026-11-10.md) does not establish PS5 gameplay or production safety. Treat the vendor PR #35 as an **uncompiled draft**, not a finished feature.

**Status:** frozen upstream source audit complete; **R4 actual source draft created**; R2 and R3 implementation commits pending their real-owner integration/qualification gates; PS5/NS1 and vendor full build validation outstanding.
