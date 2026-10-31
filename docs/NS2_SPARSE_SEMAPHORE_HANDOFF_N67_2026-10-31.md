# NSW2 N67 — native Vulkan sparse queue / renderer handoff

Research-only; does not enable sparse textures in the shipping emulator.

The existing **vendor-owned** `vk::Queue::BindSparseImage` now accepts optional
`VkSemaphore wait_semaphore` and `VkSemaphore signal_semaphore` after its
mandatory `VkFence completion`. Existing N66 call sites remain source-compatible,
because both extra arguments default to `VK_NULL_HANDLE`.

This allows the sparse-binding queue to wait on completion of earlier Vulkan
work and allows the graphics consumer to wait on sparse residency **without**
assuming that two different queue submissions are ordered. The native
`VkBindSparseInfo` sets the exact counts and pointer fields for zero, one or
both semaphores; the wrapper rejects reusing the same binary semaphore as both
wait and signal. Driver error codes still propagate unchanged. Semaphores and
fence are **caller-owned** until their GPU use has retired.

The host regression `tools/ns2/check_native_sparse_bind.py` compiles the
**actual vendor wrapper methods** with Clang and GCC under UBSan and validates
zero/one/two semaphore configurations, field ownership, invalid same-semaphore
input, absent dispatch and device-lost propagation. The source-equivalence
guard also checks N67 while preserving the pre-experiment Vulkan baseline
comparison.

## Remaining integration

1. Translate each real `VkSparseImageMemoryRequirements` (aspect, granularity,
   mip-tail offset/stride and single/per-layer tails) into bounded page plans;
   respect N63 budget and N62 VMA allocation constraints.
2. Keep the sparse image, all VMA page tokens, semaphores and completion fence
   alive through `vkQueueBindSparse`, fence wait and GPU sampling. Commit N63
   only after confirmed bind completion; poison/retire safely on errors.
3. In the existing texture-cache image owner, use N64 sparse images only after
   that transaction is valid, then coordinate N57/N60 ASTC layer uploads and
   graphics/compute submissions using real queue waits or an explicit completed
   fence. Preserve the dense `MakeImage` fallback.
4. Validate with Vulkan validation layers, real image readback, memory churn
   and PS5 device tests before enabling sparse textures. Neither PS5 sparse
   capabilities nor Switch 2 game rendering have been proven.

No game-specific overrides, no separate renderer and no modifications to `main`.
