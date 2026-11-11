# R23 pass22 — source-owner findings for #80 non-NVIDIA fragment shaders and #144 LSFG presentation

**Date:** 11 November 2026. **Scope:** E1 selected-source comparison only, on audit PR #45. This is **not** a PS5 build, shader execution trace, port, proof of performance, or GPU/device certification. Native production stays unchanged.

## #80 — AMD/RADV receives a different upstream shader policy, but it is NOT safely portable blindly

Upstream Eden [`67bada77f8a43a90da2e94e89b8e7da73c256989`](https://github.com/eden-emulator/mirror/commit/67bada77f8a43a90da2e94e89b8e7da73c256989) changes **seven** files. Beyond Qt/settings cleanup, it adds `Shader::Optimization::HasBrokenPattern` in `src/shader_recompiler/ir_opt/vendor_workaround_pass.cpp`, detecting fragment `ShuffleIndex/Up/Down/Butterfly` whose argument derives from a bitcast pattern. `vk_pipeline_cache.cpp` then **returns nullptr** rather than assembling the graphics pipeline if the device driver ID differs from `VK_DRIVER_ID_NVIDIA_PROPRIETARY` and the predicate is true. It also removes the old `rescale_hack` branch.

Exact pinned current vendor `f8f5d8ee3a94a4202886a40badb5c0203d05da30` still has:
- Original shader optimization implementation `sources/eden/src/shader_recompiler/ir_opt/vendor_workaround_pass.cpp`, blob **`08c658cb811e24e0a14181fe547ba94801c6a0b6`**, with `VendorWorkaroundPass` but **no** `HasBrokenPattern`.
- Original optimizer declaration `passes.h`, blob **`1e637cb23c8d052a94d4b3d818b7743fba093609`**, with no such declaration.
- Original Vulkan pipeline cache `vk_pipeline_cache.cpp`, blob **`642b9fa2236f9d66ba0b9144edab6a15b87fc4d6`**, lacking that filter; PS5's `headless/vulkan.cmake` selects the maintained pipeline cache `vendor/encore-active/eden-vulkan/vk_pipeline_cache_cost.cpp`, blob **`9358b81ab6b8d43e1ae524a159fd5082d4a8cab2`**, also lacking `HasBrokenPattern`.
- Original rescaling pass `src/shader_recompiler/ir_opt/rescaling_pass.cpp`, blob **`1e639096a82a3bc9b90725324aa2073b5aefa5c3`**, still using `rescale_hack`; `frontend/maxwell/translate_program.cpp`, blob **`ebc5a825dde7620d3137928efe8ff27a7136429a`**, still enables that option. The native `shader_recompiler` target overrides a specific Maxwell local-scratch TU, not the above optimizer policy.

**Verdict:** source-verified **missing upstream workaround** in current shared shader/Vulkan owners, not evidence that all non-NVIDIA shaders malfunction and not authorization to skip native shaders. PS5 RADV is a non-NVIDIA target but replacing a pipeline with `nullptr` may produce **invisible objects / blank fragments**. Owner must decide whether a capability- or pattern-specific fallback produces correct output; require good/bad shader fixtures (IR and SPIR-V validation), Vulkan pipeline results, PS5 RADV scenes with AA/upscaling/FG combinations, and negative no-regression. E1 gap OPEN for release.

## #144 — apparently Android UI actually changes the active native LSFG backend

Upstream Eden [`099547b3f4578bf1fc0b39988aefbe2d54b540cc`](https://github.com/eden-emulator/mirror/commit/099547b3f4578bf1fc0b39988aefbe2d54b540cc) changes 26 files. Its Kotlin QuickSettings work is Android-only, **but seven native shared-source modifications are not UI-only**. They change frame-gen queue default 1→0, shader cache format version 2→3 and FP16-only selection (remove FP32 fallback), require shaderFloat16 at shader loading, lazily initialize shaders even if feature inactive, avoid treating missing storage view as a permanent failure, and change offscreen frame storage allocation and presentation-frame recreation.

Current PS5 `headless/vulkan.cmake` **explicitly** adds `src/video_core/renderer_vulkan/present/frame_gen.cpp`, `lsfg_shaders.cpp` and the Encore-owned `headless/lossless_dll_r08.cpp` to target `video_core`, with `HAS_LSFG`; this is not an Android-excluded code path. Source receipts:
- Original pinned `present/frame_gen.cpp`, blob **`b0d16819e584c47a422c989a83c27cb27478c2d6`**, still does its availability/shader/storage checks in pre-upstream order.
- Original pinned `present/lsfg_shaders.cpp`, blob **`aafe0d64199df885eaebe80829c28f3339e9636e`**, still allows both `allow_fp16` and `prefer_fp16` and does not require float16 unconditionally.
- Active Encore-owned `headless/lossless_dll_r08.cpp`, blob **`1a20c33f73d95a6d240420e8248387cefdef5882`**, still provides two shader variants; compare original `lossless_dll.cpp`, blob **`5d2d08ffb31f046705bf4a0122b308720b5f7158`**.
- Active Encore-owned `headless/vulkan_blit_screen_r08.cpp`, blob **`51e5abe085f9a1ea645fc43e83c1b4f50acb89a6`**, still recreates frame only on extent mismatch in `PrepareFrame` and calls the old five-argument `RecreateFrame`.
- PS5 header overlay `headless/vk_present_manager_r08.h`, blob **`87db5264c4d29b19c8e94319e124a10b3e20e6aa`**, has no upstream `storage_capable`/new `NeedsStorage` contract; underlying selected maintained `vendor/encore-active/eden-vulkan/vulkan_present_manager.cpp`, blob **`5194b6b183cba24f7ab966c16437884ac75d284f`**, must be adapted jointly, not replaced with upstream default source. Native CMake removes original `vk_present_manager.cpp` and compiles generated maintained `vulkan_present_manager.cpp`; original `vk_present_manager.cpp` blob **`3491f8fb7563f2557a476fec8edb4f220f5d27fc`** is not the actual PS5 implementation owner.

**Verdict:** source-verified missing **backend/presentation state-transition changes** on an actively selected optional LSFG native path, E1 only. Do not copy the Android UI, make FP16-only mandatory on PS5, or replace native versioned class layouts. The native maintainer must explicitly compare cache version, FP32/FP16 fallback, dynamic enable/disable of frame-gen, storage view recreation after toggle/resizing, frame semaphore/fence ordering and the existing R09 graph for 0..N combinations. Test feature absent, activation, deactivation, resize, repeated launches, and successful/unsupported Vulkan caps with both modes. **No automatic feature enable or new experimental configuration**.

## Accounting and separation

Both entries move from generic `runtime-semantic-review-pending` into `verified-relevant-source-gap-awaiting-native-proof`, **not** into implemented/release-complete. Generic reviews **26 → 24**; verified source gaps **24 → 26**. The **8** independently scoped policy/refactor gates, **17** changed-header compile provenance receipts, **7** C00–C06 batches (**0/7** PS5-qualified), and all R18 provenance/security/licensing gates remain unchanged.

The official upstream commit and exact current original/maintained owner SHA references above are source-level evidence. Actual device regression, differential shader tests, and native object-symbol proof remain OPEN.
