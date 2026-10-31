# NSW2 — shared engine and mainline synchronization (31 October 2026)

The NS2 research branch is a **compatibility extension of the existing Encore emulator**, not a separate cloned emulator. It retains the entire existing PS5 CPU, memory, Dynarmic, shader cache, texture cache, rendering and scheduling optimizations from main.

## Mainline ancestry

- Git merge parent main: `c3acdc0f6ea48061ceca67b40bb32c518588bbec` (includes latest F07 sparse bind coalescing with its exact source and test oracles).
- Research-only implementation stays in `research/ns2-ps5-compatibility`; never merge it into production `main` until the full integration and release gates have passed.
- Vendor branch `niakw/Prospero.Eden-Encore-vendor:research/ns2-shared-core`: parent includes mainline vendor `2281ef2780179febb927662c3ce4a83b09f252a6`, with N58/N62/N64/N65 additions. The research app submodule pins the merged vendor research owner (latest shared F07 PS5 changes + N54 + sparse API); see the gitlink for the exact commit.

## Single maintained source owner

| Feature | Maintained engine owner | Applicability |
| --- | --- | --- |
| N58 sparse residency feature/queue admission | `vendor/sources/eden/src/video_core/vulkan_common/vulkan_device.h` | Any Vulkan image with sparse requirements |
| N62 VMA sparse memory chunks and rollback | `vendor/encore-active/eden-vulkan/vulkan_memory_allocator.cpp` and shared header | All qualifying 2D arrays, not game-specific |
| N64 sparse VkImage creation | Same native VMA allocator owner | Any supported Vulkan 2D array |
| N65 Vulkan sparse memory requirement query | `vendor/encore-active/eden-vulkan/vulkan_wrapper.cpp` and companion header | Generic Vulkan requirements |
| N63 sparse budget planner | `vendor/encore-active/ns2-helpers/include/video_core/renderer_vulkan/ns2_sparse_layer_budget.h` | Generic dimension/layer/mip-tail arithmetic |

The four historical `prepare_egl_sparse_*` build-time source rewrite generators and N54's `prepare_astc_scratch_owner.cmake` have been removed. Existing Clang/GCC host tests validate the **real vendor methods** instead of generating copies of maintained engine files. Mainline PS5 native Vulkan source preparation and performance backports are preserved.

## Scope and remaining migration

Names such as FC27 in tests, traces and synthetic workloads indicate **stress profiles**, not runtime compatibility branches. Do not introduce Title IDs/game names into core optimization predicates. Regressions should be fixed by GPU command, texture format, memory, CPU instruction or service semantics and reused across Switch 1 and Switch 2.

N54 scratch and its frame trim are now maintained in the single vendor root `encore-active/ns2-astc/include` (upstream scratch + shipping patched texture cache parity). N54 no longer generates source headers. N56's native driver pipeline cache guard now also lives directly in the versioned vendor Vulkan source (opt-in compile macro; no generated TU). N55/N59 ASTC staging and N63 sparse budget helpers have moved unchanged to `vendor/encore-active/ns2-helpers/include`; their old `headless/ns2` copies are deleted and the host test include roots point at vendor. N60's image bookkeeping and dirty-layer upload integration now share the exact N54-maintained PS5 texture-cache owner in vendor, with compile-time opt-in gates and retained full fallback; the old N60 header generator is removed. N57 Vulkan per-layer decode and storage-image views now reside in the existing versioned native Vulkan source owners, with two header owners and a small compute-method fragment in `vendor/encore-active/ns2-astc/include`. The old build-time N57 source rewrite has been deleted. Older NSW2 kernel and remaining experimental overlays still need migration. Their default is OFF. These still require a separate exact native API/compile audit before promotion; synthetic host oracle success is not PS5 execution proof. Vulkan queue sparse binding, fence lifetime and complete NS2 user titles remain unimplemented. No console testing requested.

## Verification

The strict `check-vendored-vulkan-fork.py` and F07 allocator OOM oracles continue to compare all generated native source files byte-for-byte apart from the **exact audited additive N65 sparse methods**, with N65 separately exercised by Clang/GCC source extraction. Do not simply disable a parity assertion to accommodate a new feature.

N60's temporary buffers now wait for Vulkan completion via `runtime.Finish()` before release. This is a safety gate, not a frame-time optimization; an asynchronous fence lifecycle and real GPU validation are still required before activation.

## Kernel SVC owner (N3v)

N3v now compiles in the **real** `vendor/sources/eden/src/core/hle/kernel/svc.cpp` behind `EDEN_NS2_SVC_TRACE`; the bounded trace helper lives under `vendor/encore-active/ns2-helpers/include/core/loader/ns2_svc_trace.h`. The CMake-generated duplicate SVC translation unit and its generator are removed. The host workflow syntax-checks that production source with the research macro. Runtime success and PS5 validation are not claimed.

## N49 consolidated Vulkan dimensionality guard

The Eglantine 2D/3D view-mismatch safety check now runs behind `EDEN_NS2_VIEW_DIMENSION_GUARD` inside the **same maintained native PS5 Vulkan `vk_texture_cache_cost.cpp`** as N57. Its generic helper lives in `vendor/encore-active/ns2-helpers/include/video_core/renderer_vulkan/ns2_view_type_guard.h`. The obsolete complete translation-unit copy in `headless/ns2/eglantine/` is deleted. Host checks reconstruct and verify the pre-N49 and pre-N57 Git source hashes without accepting unrelated differences.
