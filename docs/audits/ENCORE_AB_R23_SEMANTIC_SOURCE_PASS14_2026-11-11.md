# R23 pass 14 — #50 #64 #99 #151 exact native selected-owner triage

**11 Nov 2026, PR #45 audit-only, E1 evidence.** No native compiled PS5 objects, console title execution or change to `main`/`vendor`.

## #50 — Android bloom compensation only

Eden [`d89e02d3ac9b769046f5472f0361d5adb2596bab`](https://github.com/eden-emulator/mirror/commit/d89e02d3ac9b769046f5472f0361d5adb2596bab) drops the `Settings::values.fix_bloom_effects` conditional `OpVectorTimesScalar(...0.98f)` in `src/shader_recompiler/backend/spirv/emit_spirv_image.cpp`, and updates an Android UI string. Pinned image emitter Git blob **`5d4983b9f7be52e607029239cb0f85ff1db066f0`** still contains the code, but **inside `#ifdef __ANDROID__`**. Current PS5 target is native FreeBSD/x64, not Android. This is a source-only non-applicable branch for current PS5. Reopen if compile macros unexpectedly change; no SPIR-V shader execution was tested.

## #64 — original NVNflinger HWC buffer release lifecycle differs

Eden [`989768aa46720e3fcab9e2111e3ddd70819c382b`](https://github.com/eden-emulator/mirror/commit/989768aa46720e3fcab9e2111e3ddd70819c382b) changes `src/core/hle/service/nvnflinger/hardware_composer.cpp` only. It skips composition if every layer is invisible and **moves `ReleaseFramebuffersLocked(display)` from immediately after `nvdisp.WaitForComposite()` to after the current composite has been handed off**. Pinned source Git blob **`5decb791e1bb1ab2420f386e3fdbdd2b8628a324`** still has the old release order and no invisible-layer skip. CMake selected original HWC owner, while native VI conductor is separately patched. The upstream author cautions that releasing buffers without release fences can tear. **Decision:** confirmed source divergence requiring guest stack / Vulkan framebuffer + queue/fence tests, not a patch safe to cherry-pick blindly. No claim this is the PS5 launch crash root cause.

## #99 — ReShade layer pass outside selected PS5 renderer

Eden [`cb73a4dcc7710a7fea1643797b17e39858f4ae6a`](https://github.com/eden-emulator/mirror/commit/cb73a4dcc7710a7fea1643797b17e39858f4ae6a) modifies `renderer_vulkan/present/layer.{cpp,h}` inside `#ifdef HAS_RESHADE`; it clears post-process pass for applet layers with no Recording stack bit. **Actual PS5 Vulkan source** is `headless/vulkan_present_layer_r24.cpp`, Git blob **`dea657ef3911828b9437aced16ec9863aeb3b30a`**, selected in `headless/vulkan.cmake`; that file has **no `HAS_RESHADE` or `SetPostProcessPass` path** and implements its own frame presentation stack. Not a missing ReShade branch in this current PS5 profile. Future native ReShade enablement must reopen it and test overlay, applets and SGSR/NR output.

## #151 — native PS5 already stops/joins GPU worker at shutdown

Eden [`c95ad020fb529d47f9c3106a53553bec955c1586`](https://github.com/eden-emulator/mirror/commit/c95ad020fb529d47f9c3106a53553bec955c1586) adds `ThreadManager::NotifyShutdown` with `request_stop`/`join`, calls it from `GPU::Impl::NotifyShutdown`, and moves `system` earlier than the GPU worker in the member order. The actual PS5 `G21` complete GPU source `encore-active/eden-core/src/video_core/gpu_gl_native.cpp`, Git blob **`51e21613c1e23b0f5aefef0dd78ed9d9b13806e7`**, already uses `GPU::Impl::NotifyShutdown` to signal `sync_cv`, then calls `gpu_thread.Stop()`, and the `Core::System& system;` field is ordered before GPU worker state. Selected maintained GPU worker `encore-active/eden-gpu/gpu_thread_quiet.cpp`, Git blob **`28eab249dc8eefdcadb27ccfdb308743a95580ad`**, implements `Stop` with `stop_source.request_stop()`, `pthread_join` and draining stale queued commands; its header Git blob **`f9c5f72a17867f40e47416e12c62076c9b011e6d`** declares `Stop`. `headless/CMakeLists.txt` selects these sources for PS5 graphics. These are source-equivalent **shutdown lifecycle intents**, not byte-identical, linked ELF proof or a real repeated title shutdown stress test. A crash can still exist elsewhere.

## Current audit counts

155/155 immutable upstream commit/file receipts unchanged; **44 generic runtime semantic reviews remain, 15 code gaps, 2 separately scoped GL/UTF policy tests, 0 current-profile build-only candidates, 17 native header receipts and 7 C00–C06 PS5 release gates**. Keep PR #45 independent from #46; no automatic port, vendor repin or main merge.
