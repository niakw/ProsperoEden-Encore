# NSW2 N69 — native Vulkan sparse VMA binding transaction

Research-only vendor component, not enabled in any production renderer.

The new maintained helper lives in
`vendor/encore-active/ns2-helpers/include/video_core/renderer_vulkan/ns2_sparse_bind_transaction.h`
and is templated on the **existing** Vulkan `MemoryAllocator`, `vk::Queue`,
`vk::Fence` and logical device types. It does not fork or replace the renderer.

- Rejects unsupported sparse aspects, granularity, memory alignment, memory types,
  layout mismatches, stale N63 plans and an already-signalled completion fence.
- Converts the N68 real tile / mip-tail rectangles to native
  `VkSparseImageMemoryBind` and `VkSparseMemoryBind`.
- Allocates a single bounded, VMA-owned device-local region via the established
  N62 `AllocateSparseMemory` per transaction and computes aligned memory offsets
  for every submitted sparse page.
- Calls N67's **real** `vk::Queue::BindSparseImage`, optionally passing wait /
  signal semaphores to enforce queue dependency.
- Calls `fence.Wait` before `SparseLayerBudget::Commit`. An error or timeout
  poisons the logical image and **retains** all possibly-in-flight VMA tokens;
  memory is never freed on an uncertain Vulkan submission.
- `RetireAfterDeviceIdle` checks actual `Device::WaitIdle`, then invokes the
  caller's image/view destruction callback, releases all allocations through N62,
  and resets N63's budget. A device-lost/failed idle keeps memory retained.

`tools/ns2/check_sparse_vma_bind.py` compiles and executes the *exact pinned
vendor helper* under both GCC and Clang UBSan. A minimal fake Vulkan driver
simulates successful tile/tail binding, memory offsets, multi-submit ownership,
allocation failure, malformed requirements, failed queue submission, timeout,
shared mip tails and failed recovery. N66 tests separately compile the actual
native queue dispatch.

**Not yet integrated into the PS5 texture cache or Ampere rendering.** The caller
must schedule all prior image uses and wait correctly before using or destroying
the VkImage, and must validate actual driver residency and readback. This is not
a console test, a Switch 2 game boot, or evidence of frame-rate improvements.
N69 remains opt-in research and cannot be used in a shipping build.

## N70 — fail closed on multi-aspect sparse requirements

The vendor transaction now consumes the **complete** `std::vector<VkSparseImageMemoryRequirements>` produced by the maintained Vulkan device wrapper. It only admits a single color-aspect requirement. Extra metadata/depth/stencil aspects are refused before VMA allocation, because silently ignoring one would yield invalid GPU image residency. The Clang/GCC UBSan host test now exercises a synthetic second metadata aspect. Full Vulkan image readback and a real PS5 graphics capability check remain outstanding.
