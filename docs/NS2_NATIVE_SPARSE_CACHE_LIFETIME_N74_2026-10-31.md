# NSW2 N74 — VkImageView lifetime and GPU-loss quarantine

Research-only PS5 Vulkan work. The regular dense texture cache and the final
release have not been changed; no NS2 game rendering is claimed.

## Native code

- The existing `TextureCacheRuntime::ProbeSparseImage` in the maintained
  `vendor/encore-active/eden-vulkan/vk_texture_cache_cost.cpp` now creates a
  real `VK_IMAGE_VIEW_TYPE_2D_ARRAY` view **only after** N69 reports complete
  sparse residency, covering all mip levels and array layers.
- The same N69 owner still performs VMA allocation and N72 synchronized Vulkan
  submission. The view is not published to the game's descriptor set.
- N74 introduces `RetireSparseCacheProbe` in the existing vendor transaction
  helper. On successful `Device::WaitIdle`, it destroys the **view, then the
  image, then its fence** and only afterward releases the VMA allocations.
- If idle fails after queue submission, all three Vulkan RAII handles remain
  quarantined and N69 retains the VMA tokens, avoiding destruction of handles
  referenced by an unresolved GPU submission. The intentional process-lifetime
  leak is a last-resort safety tradeoff on device failure; a sticky atomic flag
  rejects further probes so failures do not allocate an unbounded series of
  quarantined resources.
- Failed VkImageView creation is caught. The same device-idle retirement path
  runs before return; no early image teardown after a potential GPU submission.

## Tests

The actual vendor `RetireSparseCacheProbe` is compiled in the existing
`tools/ns2/test_sparse_vma_bind.cpp` Clang/GCC UBSan harness. It asserts the
view → image → fence → VMA order on successful idle, and verifies that an
unsuccessful idle retains both GPU handles and VMA backing without invoking
destructors. The cache source guard checks the genuine Vulkan view creation and
complete-residency precondition.

The strict N57 vendor parity witness strips only the N73/N74 opt-in cache
probe and confirms that the base PS5 Vulkan implementation is unchanged.

## Remaining blocker

An independently owned sparse `Image::original_image` is not yet safe to
enable. Normal image views are shared among the texture cache, descriptors,
framebuffers and queued command buffers; retiring a live texture needs real
generation/tick tracking and command buffer fencing. The N74 probe does not
sample pixels and does not demonstrate NSW2 gameplay.
