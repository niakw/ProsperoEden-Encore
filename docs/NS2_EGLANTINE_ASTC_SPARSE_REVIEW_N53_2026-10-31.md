# NSW2 N53 — Eglantine selective ASTC and sparse Vulkan acceptance review (2026-10-31)

Research-only audit. Branch `research/ns2-ps5-compatibility`; `main` and pinned vendor remain unchanged. No ASTC/sparse Vulkan optimization is claimed to have been ported by N53.

## Public tested fixes and actual Encore source owners

1. [Eglantine 97ce27a](https://github.com/Djihads80/Eglantine/commit/97ce27ab35153884d2fd05c278433928e429cd91) introduces selective ASTC dirty-layer uploads/decode. It modifies `texture_cache.h`, `texture_cache_base.h`, `image_base.h`, `vk_compute_pass.cpp/.h`, Vulkan image storage views and scratch ownership together. Porting only the shader dispatch would read the wrong staging slices or write the wrong layers.
2. [Eglantine 940d44c](https://github.com/Djihads80/Eglantine/commit/940d44ca25628288f1b5f64c25c022b3a4ae5ce2) identifies unwritten sparse blocks. [Eglantine d4ee7fc](https://github.com/Djihads80/Eglantine/commit/d4ee7fcd5129e7ee32ff38a5aef9b449d5a756de) binds terrain arrays' sparse image memory by layer and introduces Vulkan allocator, dispatch and scheduler synchronization. This depends on `sparseBinding`, `sparseResidencyImage2D` and graphics-queue sparse binding; never infer residency support merely from `IsSparseBindingSupported()`.
3. The *native PS5* Vulkan texture-cache owner is `vendor/encore-active/eden-vulkan/vk_texture_cache_cost.cpp`; native CMake copies it to `vk_texture_cache_cost.cpp`. It has `Image::StorageImageView` and the optimized native `AccelerateImageUpload`, but **not** `StorageImageLayerView` / `AccelerateImageUploadLayers`. The pinned `vendor/sources/eden/src/video_core/renderer_vulkan/vk_compute_pass.cpp` has only the full-image ASTC `Assemble`, not `AssembleLayers`. Native R428 already selects a maintained `texture_cache/util.cpp` one-layer scratch optimization; preserve it rather than overwrite from generic upstream.
4. `vendor/sources/eden/src/video_core/vulkan_common/vulkan_device.h` currently exposes `IsSparseBindingSupported()` (binding + queue family). Eglantine's image-residency-dependent sparse allocator and queue-bound fences have no verified native PS5 equivalent. No host or source check proves PS5 RADV's sparse image residency features or driver behavior.

## Required implementation sequence (no partial shipping)

- Reconcile native PS5 image-storage views and ASTC compute pass against Eglantine's full source and preserve PS5 custom texture cache optimizations.
- Add a bounded dirty-layer index/offset helper: reject empty/invalid layers, zero stride, out-of-range host mip level, offset beyond stride, span/total-size overflow and staging allocation beyond an explicit device budget. Do not let `cpu_addr+size` wrap when computing dirty layers. Compare partial layer decode to full decode in deterministic image readback fixtures.
- Gate sparse binding separately on both Vulkan sparse feature bits, actual queue support, resource memory requirements and available budget. Bind before dispatch, synchronize by the native queue scheduler, and release memory strictly after the last use. Prefer a correct full-image fallback when any check fails.
- Exercise the real maintained shader/texture source owners under Clang/GCC, sanitizer-based randomized mapping/dirty-write tests, Vulkan validation layers with an image-capable host device, and large (multi-gigabyte virtual image) stress with bounded physical allocations.
- Keep N49/N50/N51 experimental fixes OFF in final releases. No console tests requested. Full native PS5 graphics output and Switch 2 title boot remain unproven.

## N52 interaction

N52's `KProcess::Run` result check improves boot failure reporting; it is **not** ASTC validation. N51's GPU PTE invalidation batching is independent from sparse Vulkan memory residency. Do not enable both merely on the basis of independent green host tests.
