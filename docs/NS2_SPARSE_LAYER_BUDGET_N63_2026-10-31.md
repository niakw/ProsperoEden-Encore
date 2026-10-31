# NSW2 N63 — sparse image tile/mip-tail admission and GPU retirement

Research-only pure C++ owner `SparseLayerBudget`, used before the future native Vulkan sparse binder. Depends conceptually on N58's strict 2D sparse residency feature gate and N62's real VMA allocator entrypoint. Does not enable sparse binding in production.

Inputs are validated image dimensions, levels, array layers, VkSparseImageMemoryRequirements tile geometry, backing alignment and mip-tail layout **in consistent texel units** (compressed-format conversion is caller's duty). N63 computes all mip tile bytes with checked 64-bit arithmetic and handles both independent per-layer mip tails and Vulkan's `SINGLE_MIPTAIL` policy. Device memory below 7 GiB caps per-image backing at 384 MiB; 7 GiB or more caps at 768 MiB. Reject malformed requirements rather than wrapping arithmetic or over-allocating.

`Plan()` calculates only missing layers and shared-tail cost, rejects duplicate/out-of-range layers or over-budget requests as an **entire transaction** without partially committing. `Commit()` requires unchanged generation and identical budget/layer proposal, and is called **only after successful vkQueueBindSparse+fence retirement**. `Poison()` prevents unsafe reuse after failed/in-doubt GPU submission, and `ResetAfterGpuRetire()` is forbidden until all GPU use of the Vulkan image is complete.

Clang/GCC UBSan tests cover per-layer tails, shared tails, bad dimensions/granularity, overflowing tile counts, stale plan reuse, poison/restart and 5000 deterministic randomized binding requests. This is not an actual sparse VkImage, real PS5 driver feature detection, image readback or game FPS benchmark. No console test requested.
