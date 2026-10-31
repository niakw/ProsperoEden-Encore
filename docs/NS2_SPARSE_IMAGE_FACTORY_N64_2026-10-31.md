# NSW2 N64 — native sparse VkImage factory without full-image allocation

**Research only, OFF by default**: `EDEN_NS2_SPARSE_IMAGE_FACTORY_EXPERIMENTAL=ON` requires N58 sparse 2D residency feature gate and N62 native PS5 sparse VMA allocation backend, plus native PS5 Vulkan/NS2 metadata; final releases forbid it.

Adds `MemoryAllocator::CreateSparseImage(ci)` to the maintained native PS5 Vulkan allocator via a second source-derived overlay layered on N62. Enforces 2D array, >1 layer, single sample, optimal tiling and valid extent/mip count. Without support from the *selected graphics queue*, returns an empty image. Uses `vkCreateImage` with `SPARSE_BINDING|SPARSE_RESIDENCY` and **does not allocate backing for the full image**. Returns the existing `vk::Image` RAII wrapper with a null VMA allocation; VMA explicitly documents that `vmaDestroyImage` accepts a null allocation and still destroys the VkImage. A driver error with an unexpectedly nonnull handle is cleaned up.

The native source-owner test regenerates N62 followed by N64, enforces preservation of the existing full-backed `CreateImage` and sparse allocation methods, and compiles the *actual injected image factory body* with a mocked Vulkan driver under Clang/GCC UBSan, covering invalid/supported features, bad dimensions, failed create and partial returned handle.

**Remaining before sparse images can be used**: validate real PS5 sparse memory requirements, derive N63's tiled mip/tail binding plan, allocate pages with N62, submit VkSparseImageMemoryBind via the graphics queue and fence, then connect to the image/texture lifetime and partial ASTC uploads. No sparse image is yet bound or sampled on actual PS5 hardware. No console test requested.
