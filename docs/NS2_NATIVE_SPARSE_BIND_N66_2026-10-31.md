# NSW2 N66 — native Vulkan sparse binding submission

The Encore PS5 Vulkan `vk::Queue` now exposes `BindSparseImage`, which builds genuine `VkSparseImageMemoryBindInfo` (tiles) and optional `VkSparseImageOpaqueMemoryBindInfo` (mip tails), and invokes the existing `vkQueueBindSparse` dispatch. The submission requires a non-null completion fence and rejects missing driver functions, invalid image, empty data and invalid memory binds before calling the driver. Driver errors propagate unchanged. No game/title special cases or separate renderer.

The caller still must query N65 requirements, reserve N62 memory with N63 budget, submit through N66, wait for the fence and only then `SparseLayerBudget::Commit`. On errors/timeout, poison the image and retire any pending Vulkan memory safely. This commit adds the **real queue submission entrypoint**, not an integrated texture-cache caller or console proof.

Host test `tools/ns2/check_native_sparse_bind.py` compiles and executes the **exact vendored Queue methods** with both GCC and Clang under UBSan, validating the marshalled bind arrays, fence propagation, fail-closed cases and VK_ERROR_DEVICE_LOST. Experimental branch only.
