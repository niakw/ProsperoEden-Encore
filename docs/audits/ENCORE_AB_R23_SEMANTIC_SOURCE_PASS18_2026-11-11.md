# R23 pass 18 — source triage of NCE toggle #82, NRO TLS #68, GPU fault #6 and HLE sessions #149

**11 November 2026 · PR #45 source-only E1 · NS1 + shared infrastructure.** No production source, vendor, native target, release or hardware modification.

## #82 — upstream toggles do not constitute a PS5 x64 runtime fix

Official Eden [commit 10bcd2d849](https://github.com/eden-emulator/mirror/commit/10bcd2d849) has eight files: four Android UI/resources paths, `src/common/settings.h`, `src/core/hle/service/ro/ro.cpp`, Qt translation, and `src/video_core/gpu.cpp`.

- The `ro.cpp` change **only wraps existing NRO patch logic behind a new setting inside `#ifdef HAS_NCE`**. It introduces no x64 Dynarmic replacement.
- The `gpu.cpp` change **guards the prior GPU-readback behavior by `nce_invalidation_gpu_readback.GetValue()`**, a new setting whose default in this upstream patch is `false`. Adding that toggle without its NCE support does not improve PS5 correctness.
- Exact pinned vendor [Eden CMake source](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/22b69d6053db41b74edac2633c012f925b84f69e/sources/eden/CMakeLists.txt) Git blob `8b068b85b4de2a2a04fbf32875a79b4304c52294`, lines 299–305, enables `HAS_NCE` **only** on `ARCHITECTURE_arm64 AND (ANDROID OR LINUX)`; pinned [core CMake](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/22b69d6053db41b74edac2633c012f925b84f69e/sources/eden/src/core/CMakeLists.txt) blob `508ace350173f5068bd7531f37e70199134fde3a`, line 1227, includes `arm/nce` under that flag. PS5 uses x64 Dynarmic.
- The source-level decision is **exclude the added NCE toggles from PS5 native runtime parity**; do not introduce an unused/exposed experimental option. The earlier #88/#57 readback was explicitly rolled back in #47, documented separately in `ENCORE_AB_R23_NCE_GPU_REVERT_NET_PROOF_2026-11-11.md`.

**Disposition:** `reviewed-NCE-settings-toggle-no-PS5-x64-port`. This closes *only upstream semantic review #82* for current PS5 x64, not native compiler macro attestation, nor the other NCE/shared GPU commits.

## #68 — not an NCE-only file despite its title

Official [commit aaa0bcb9bf](https://github.com/eden-emulator/mirror/commit/aaa0bcb9bf) adds NCE TLS patcher logic in `src/core/arm/nce/patcher.cpp/.h`, but also changes `src/core/hle/service/ro/ro.cpp` **before** the `#ifdef HAS_NCE` region: `SetNroPerms(context->GetProcess(), ...)`. This unconditional guest memory permission change can affect NS1 x64 and must be reviewed independently from ARM64-only TLS. Check the currently selected RO owner, permission ordering, unwind/error paths, page alignment and native guest `LoadNro`/unload behavior before any port. **Remains pending.**

## #6 — shared GPU buffer behavior still requires review

Official [commit bfa72a22a3](https://github.com/eden-emulator/mirror/commit/bfa72a22a3) includes NCE fault retry decisions but *also* alters `buffer_cache.h`, `memory_tracker_base.h`, `word_manager.h` and GPU's flush-query interface. These are shared NS1/GPU paths rather than architecture-exclusive NCE files. Review CPU/GPU dirty-page ownership, partial GPU-write ranges, upload exclusions, and memory tracker lifetime in the actual native owners. **Remains pending; do not discard on NCE-title grounds.**

## #149 — service session limits are a distinct high-priority HLE contract

Official [commit 8a22f1845b](https://github.com/eden-emulator/mirror/commit/8a22f1845b) changes `ServerManager::RegisterNamedService` call sites across audio, BCAT, filesystem, BPC, ARP and other services, and adds `bpc:ams` stub service. Its `audio_render_manager.cpp` bounds/assert changes are not equivalent to merely adding a setting. This can affect title boot and resource exhaustion; audit exact selected `ServerManager` API and guest session limits, run positive/negative IPC tests before considering source migration. **Remains pending.**

## Verdict and boundaries

- Verified reviewed closure: **#82 only** (31 → **30** outstanding generic semantic reviews), E1 source disposition without code port.
- Priorities retained: #68 cross-boundary NRO permission change, #6 shared GPU partial dirty-page tracking, #149 HLE session limits.
- No runtime patch imported, no full C++ syntax, no native PS5 link or console proof. 22 confirmed source gaps, 17 native header receipts and seven corrective release batches stay separate.
