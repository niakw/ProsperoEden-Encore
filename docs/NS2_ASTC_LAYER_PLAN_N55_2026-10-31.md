# NSW2 N55 — bounded ASTC dirty-layer staging planner

Isolated pure C++ research component, not yet selected by the renderer. Scope: `research/ns2-ps5-compatibility`, no `main`, vendor, release or Vulkan dispatch change.

The [Eglantine 97ce27a](https://github.com/Djihads80/Eglantine/commit/97ce27ab35153884d2fd05c278433928e429cd91) selective ASTC fix requires correctness across CPU write tracking, mip offsets, staging chunks, Vulkan image views and compute synchronization. N55 isolates the first correctness boundary:

- Initial images require a successful **full upload** before selective writes are eligible. Remap/unmap/alias or lost GPU state invalidates this proof.
- Bounds checks reject invalid layer counts, GPU address overflow, zero strides, mip offset outside layer and per-layer staging exceeding the configured budget.
- Dirty CPU writes are clamped without uint64 wrap; only overlapping layers are marked. More than 64 layers are supported by a bitset.
- Snapshot builds per-layer `guest_offset`, `staging_offset`, byte size and bounded `batch` index. A 68-layer, 21-MiB/layer virtual image with 7 modified layers needs three staging batches of at most 63 MiB each, not a 1.4-GiB staging image.
- Commit requires an unchanged generation token after all batches succeed; concurrent new writes cannot be lost.
- Source-owner guard verifies the current PS5 native Vulkan upload owner and pinned generic texture/image metadata. Clang/GCC UBSan tests exercise boundaries, stale snapshots and deterministic randomized dirty ranges.

**Evidence limit:** this is a tested upload *planner*, not an enabled partial ASTC decoder. There is no claim of PS5 GPU residency, sparse allocation, game boot, frame-time gain or visible rendering. Next integration is to adapt native `ASTCDecoderPass`, per-layer views and the texture-cache upload path together, then validate GPU synchronization. No console test requested.

## Maintained vendor source

The single maintained N55 source is now `vendor/encore-active/ns2-helpers/include/video_core/texture_cache/ns2_astc_layer_plan.h`. The planner remains research-only.
