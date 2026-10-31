# NSW2 N73 — cache-side Vulkan sparse image probe (2026-10-31)

Research only; OFF by default. This is NOT an enabled Switch 2 rendering
path or a demonstrated boot. It uses the existing vendor native PS5 Vulkan
texture-cache translation unit and the existing scheduler/allocator.

## Real components

- The vendor ns2_sparse_cache_admission.h examines VkImageCreateInfo, the
  actual driver memory requirements and complete sparse aspect list. Rejects
  unsupported usages, image types, multisampling, mutable/aliasing views,
  extra metadata aspects and nonstandard tiling.
- Requires a complete N63 budget plan for every array layer and mip.
  Partial residency is explicitly forbidden when a texture could be sampled.
- TextureCacheRuntime::ProbeSparseImage creates a real unbacked 2D array
  through MemoryAllocator::CreateSparseImage, reads actual Vulkan memory/tile
  requirements, allocates page backing through VMA using N69, submits via
  N72 synchronized graphics queue, waits for completion and frees backing
  only after GPU idle and image destruction.
- Normal guest textures still use allocator.CreateImage(image_ci) in
  MakeImage, so normal Switch 1 and retail builds cannot accidentally
  sample partially resident sparse textures.

## Gating and verification

EDEN_NS2_SPARSE_CACHE_PROBE_EXPERIMENTAL=OFF by default. If enabled, requires
PS5 native research + Vulkan + N57 ASTC cache header + N72 queue bridge; final
release and non-native builds fail closed. The probe is explicitly callable by a
future research diagnostics owner but is never called from an automatic
per-frame texture upload.

tools/ns2/check_sparse_cache_admission.py compiles and executes the pinned
vendor helper with Clang/GCC UBSan using synthetic driver descriptors, and
guards the true native cache ownership handoff. The strict N57 parity oracle
normalizes only the annotated N73 addition, retaining its exact previous
source identity and preventing unnoticed engine forks.

## Still blocked

This does not yet replace Image::original_image with an owned sparse texture.
That requires a safe Vulkan image-view/destruction lifetime, resident region
updates, ASTC layout/format support, and console GPU sampling/readback.
Sparseness unsupported by the PS5 driver must continue to fall back to dense.
