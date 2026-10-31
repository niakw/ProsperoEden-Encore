# NSW2 N62 — native PS5 sparse VMA allocation API

Opt-in `EDEN_NS2_SPARSE_VMA_ALLOCATOR_EXPERIMENTAL=ON`, depends on N58 sparse feature selector, native PS5 Vulkan and NS2 metadata; OFF by default and forbidden in final release. All files remain on `research/ns2-ps5-compatibility`; no vendor/main edits.

N62 injects two **real allocator methods** into the maintained native PS5 Vulkan `MemoryAllocator`:
- `AllocateSparseMemory(requirements, SparseMemoryAllocation& out)` uses **VMA device-local, within-budget allocation**, preserves the Vulkan returned device-memory handle/offset and rejects zero, non-power-of-two alignment, missing memory-type bits, or already-owned output tokens.
- Any failed allocation or missing VkDeviceMemory frees a partial allocation; no leaked/overwritten tokens.
- `ReleaseSparseMemory(token)` frees once and clears the token. **The caller must first await sparse-bind/GPU retirement before freeing**, which will be enforced in the forthcoming sparse image binder.

CMake selects only the *native* PS5 Vulkan `vulkan_memory_allocator.cpp` and its pinned header; the existing full memory allocator code and VMA failure/OOM handling remain intact. CI regenerates the exact maintained owner and compiles/executes the **actual injected allocation/free methods** with simulated VMA success, out-of-memory, missing handle, partial allocation and double-release under Clang/GCC UBSan.

This is the allocator foundation, **not a sparse VkImage, queue bind, residency implementation or confirmed PS5 driver feature**. The next work is image tile/mip-tail plans, per-image budget, bind synchronization, rollback and GPU-lifetime handling. No console test requested.
