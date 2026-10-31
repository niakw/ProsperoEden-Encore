# NSW2 N65 — native PS5 Vulkan sparse image requirements query

Experimental `EDEN_NS2_SPARSE_IMAGE_REQUIREMENTS_EXPERIMENTAL=ON` (OFF by default). Requires N58 sparse residency feature gate, N62 native VMA, N64 unbacked sparse image factory, PS5-native Vulkan + NS2 metadata; final release rejects it.

**Actual native PS5 wrapper owner**, not a desktop emulator transplant: a source-derived alternative `vulkan_wrapper.cpp` and `vulkan_wrapper.h` adds `vk::Device::GetSparseImageMemoryRequirements(VkImage)`. It obtains Vulkan's real `vkGetImageSparseMemoryRequirements` through the existing `vkGetDeviceProcAddr` at call time. It does **not** extend `DeviceDispatch`, preventing an ABI layout mismatch with PS5 Vulkan archives.

Unbound optional Vulkan function pointers, null images, zero/oversized requirement counts (>64), and count inconsistencies are rejected. A successful query provides the driver-dependent image tile granularity, mip tail mode and offset/stride metadata for N63's budget planner. Source-owner guard proves no unrelated rewrite; host tests compile the **actual injected method** with Clang/GCC UBSan against a fake Vulkan driver simulating missing entrypoints, malformed counts and successful queries.

Next required stage is a real `VkSparseImageMemoryBind` planner using N63+N65 requirements followed by graphics-queue `vkQueueBindSparse`, fence wait/rollback, and image/ASTC integration. No actual PS5 sparse binding, texture readback or game FPS validation has yet occurred.
