# R23 pass 19 — #81 default policy and native Vulkan swapchain parity

**11 November 2026 — E1 source qualification of official Eden commit [3cdd2ce141](https://github.com/eden-emulator/mirror/commit/3cdd2ce141); audit PR #45.** PS5 x64 profile only. No runtime modification, vendor repin, PS5 compile, release or device result.

## Native Vulkan presenter: substantive code already exists on the selected path

Official #81 changes `vk_present_manager.cpp/.h` to enforce `MAX_PRESENT_ATTEMPTS=3`, provide `DiscardFrame` after exhausted retries, track swapchain image count/format as atomics, and change `renderer_vulkan.cpp` to ask the presenter for those values rather than reading the swapchain directly.

Pinned vendor `22b69d6053db41b74edac2633c012f925b84f69e` already carries in its **maintained** `encore-active/eden-vulkan/vulkan_present_manager.cpp` (Git blob `5194b6b183cba24f7ab966c16437884ac75d284f`) the three-attempt guard, `DiscardFrame`, atomic image count/format stores, plus a bounded `AcquireNextImage` recreation loop. These are not added here; no duplicate patch should be ported.

`headless/vulkan.cmake` explicitly removes the original `renderer_vulkan/vk_present_manager.cpp` and appends `${PORT_BUILD_DIR}/vulkan_present_manager.cpp` after copying the maintained vendor `eden-vulkan` tree. It copies the maintained `headless/vk_present_manager_r08.h` (blob `87db5264c4d29b19c8e94319e124a10b3e20e6aa`), which exposes atomic `SwapchainImageCount()`, `SwapchainImageFormat()`, and `SwapchainImageViewFormat()`. The selected `headless/vulkan_renderer_r08.cpp` (blob `05bf73dc361af36f11f554c60befb80e4b125e51`) calls these accessors for both direct composition and frame generation. This is explicit source graph intent and E1 maintainer provenance; the exact current native compiler and PS5 GPU behavior have not been independently attested.

## Global default settings: product-policy differences, not universal improvements

The same upstream commit changes default `NvdecEmulation::Gpu` to `Cpu`, `airplane_mode` false to true, and Android-only audio/async presentation options. In pinned `sources/eden/src/common/settings.h` Git blob `d45f0b7bbca982f133dcabcd0621e40cff4f74e5`, NVDEC still defaults to GPU and airplane mode false; `use_asynchronous_gpu_emulation` is **already true on non-Android**, and Android-specific SDL3/async presentation defaults are not native PS5 defaults. Unconditionally copying these settings would change video decode GPU/CPU load and guest networking behavior, potentially masking genuine launch defects. Preserve existing chosen defaults until explicit PS5 NVDEC decode, connectivity and applet regression tests justify changes. No hidden experimental flag is warranted.

**Disposition for upstream #81:** `reviewed-PS5-Vulkan-presenter-maintained-defaults-policy-deferred`. Semantic source review complete, presenter changes already present in intended maintained source, native defaults intentionally not changed pending measurable device policy. This is **not** an E3/E4 assertion of compiled parity or performance.

## Unchanged release gates

After #82 pass18, generic pending cases: **30 → 29**. Scoped policy/refactor gates: **7 → 8** (including #81's NVDEC/network defaults). Confirmed source gaps remain **22**; native changed-header compile receipts **17**; corrective release batch gates **7**. No main, vendor, NS2 audit, build or release changes.
