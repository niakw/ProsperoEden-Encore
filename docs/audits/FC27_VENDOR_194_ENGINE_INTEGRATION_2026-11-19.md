# FC27 NS1: exact vendor #194 integration with engine main, 19 Nov 2026

## Evidence and correction

The **last FC27 console archive** on PS5 firmware 13.60 is from compiled engine `2b0975f7`, with 117 five-second windows, 624,280 contended cache acquisitions and 15,414.493 ms aggregate buffer-cache lock waiting across threads. The last native artifact **did not** include vendor PR #194. Relevant issue: [FC27 #100](https://github.com/niakw/ProsperoEden-Encore/issues/100).

This integration selects exact vendor Git commit [`8153654a2f1fe809fb2caa28dcadca90a7661446`](https://github.com/niakw/Prospero.Eden-Encore-vendor/commit/8153654a2f1fe809fb2caa28dcadca90a7661446), descendant of prior pinned `d0246caf58a3127597bba1edfc1f8dcbe0c5cfdc`. Vendor [PR #194](https://github.com/niakw/Prospero.Eden-Encore-vendor/pull/194) introduced **real NS1 memory synchronization logic**:
- `encore-active/eden-vulkan/vulkan_rasterizer.cpp`: releases buffer cache lock before publishing the batched page-protection decrements.
- `encore-active/eden-core/overrides/core/device_memory_manager.inc`: keeps unmap and remap lifetimes ordered with post-lock publication, and flushes prior batches before conflicting updates.
- `encore-active/eden-core/overrides/core/deferred_cached_updates.h`: new, separately classified **post-F07** production header; raw Git blob pinned `33262f511777cdd1b4a74ac0cd6dc39caa12c9d0`.
- New rasterizer raw blob `38d5630570675088a0620ef533112bb314a40ae8`; new device manager raw blob `852a0272696c7ce182bc05aee92bc7cbb195446b`.

Host validation uses vendor's own `tests/fc27_deferred_page_protection_host.py` and exact-content receipts rather than blanket SHA allowlisting or weakening historical checks. Older F07 source-owner totals **337** and **518** remain frozen; the new header is separately excluded after its exact SHA and presence check. Vulkan history audit reverses only the exact new method hunk and include **on a temporary copy**, then applies the original R23/P24 oracle. No other upstream source snapshot is modified.

**Required next gates:** full engine host source/sanitizer/CodeQL checks, genuine native PS5 SDK compile/link, package CRC/SELF/symbol SHA integrity, and PS5 13.60 FC27 A/B: frame pacing, HUD responsiveness, pause latency, same-process relaunch, shutdown. Host pass is **not** proof of improved gameplay, and NS2 `PC=0x4` remains P0 and independent.

Upstream comparison: [Lichii #1518](https://github.com/zortos293/Lichii/pull/1518) (page protection deferred past buffer mutex) and [Lichii #413](https://github.com/zortos293/Lichii/pull/413) (Ampere-only fastpath not applicable to FC27 NS1). Source adapted and reviewed for PS5, never blindly copied.
