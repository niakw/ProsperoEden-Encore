# R23 pass 8 — #52 shader async depth policy on the REAL PS5 owners

**Audit-only, 11 November 2026.** Upstream commit [`26a03d2473787abf3223b2d0e65b291eee00c1e1`](https://github.com/eden-emulator/mirror/commit/26a03d2473787abf3223b2d0e65b291eee00c1e1) changed exactly **two** files: `src/video_core/renderer_vulkan/vk_pipeline_cache.cpp` and `src/video_core/renderer_opengl/gl_shader_cache.cpp`. The same five added lines in each file return `nullptr` for `maxwell3d->regs.zeta_enable` when the shader is still building, after the `!use_asynchronous_shaders` guard. No code is imported into production.

## Source-owner E1 receipts

| Owner | Exact pinned Git blob | Source fact |
|---|---|---|
| Original Eden Vulkan `sources/eden/.../vk_pipeline_cache.cpp` | `642b9fa2236f9d66ba0b9144edab6a15b87fc4d6` | No new depth early-return, but **not** the PS5-selected owner |
| Selected maintained PS5 Vulkan `encore-active/eden-vulkan/vk_pipeline_cache_cost.cpp` | `9358b81ab6b8d43e1ae524a159fd5082d4a8cab2` | `PipelineCache::BuiltPipeline` returns `pipeline` under `#ifdef PS5_NATIVE` before `if (!use_asynchronous_shaders)` and any desktop guard |
| Original Eden OpenGL `sources/eden/.../gl_shader_cache.cpp` | `df69eb97f5fc8f440465d698123ea00e274ee671` | `ShaderCache::BuiltPipeline` retains async/index-count policy without upstream `zeta_enable` guard; unlike Vulkan, no PS5 early-return |

The frozen vendor gitlink is **`22b69d6053db41b74edac2633c012f925b84f69e`**. Native recipe sets `-DEDEN_PS5_VULKAN=ON` and `-DENABLE_OPENGL=ON -DEDEN_PS5_OPENGL=ON` in the graphics build; `headless/vulkan.cmake` copies the maintained tree then replaces `renderer_vulkan/vk_pipeline_cache.cpp` with generated-build-path `vk_pipeline_cache_cost.cpp` through its `foreach` owner selector. Original Eden `src/video_core/CMakeLists.txt` includes `renderer_opengl/gl_shader_cache.cpp`; native `headless/CMakeLists.txt` does **not** replace that source path. The PS5 launcher `headless/main.cpp` can select `OpenGL_GLSL` in normal/safe launch and sets `recovery_opengl = true` for the development recovery path.

## Exact semantic interpretation (no runtime proof)

When `pipeline->IsBuilt()` is true, both policies return the pipeline. For **an unbuilt pipeline on PS5 Vulkan**, its maintained `PS5_NATIVE` branch returns the pending pipeline without evaluating the desktop async/depth/index-count code. The source comment says `ConfigureDraw` orders a worker wait; a PS5 device trace is still required to prove the actual wait, absence of lost draws, and no deadlock. The new upstream `zeta_enable` early skip cannot change this current PS5 Vulkan branch unless the branch/compile selection changes.

For **PS5 OpenGL**, async building may be enabled, and the original `ShaderCache::BuiltPipeline` has no depth conditional. The upstream would return `nullptr` earlier for **unbuilt depth-enabled draws**; the pinned path instead applies only small-vertex/index checks. This is a genuine conditional policy difference, **not yet proven a bug** and not safely fixed merely by adding five lines.

**Decision**: `reviewed-PS5-Vulkan-early-return-GL-depth-policy-open`. Close the upstream #52 *generic unreviewed semantic triage* while keeping the separate **OpenGL depth async behavioral gate** open. **OpenGL remains open** until actual selected-source/full-target and title/driver positive+negative tests, depth on/off and asynchronous on/off, draw-count/visual output and first-use stutter/correctness. If native CMake/vendor pin changes, reopen the Vulkan selection too. No blind patch to Vulkan or OpenGL, no compile, PS5 build or game test, merge or vendor change.

**Counts after #52**: 155/155 file receipts intact, **57 generic semantic cases**, **1 reviewed backend-conditional OpenGL gate**, **0 current-profile build cases**, **11 other verified source gaps**, **17 unresolved native header includes**, **7 corrective batches without complete release qualification**. These represent different evidence categories.
