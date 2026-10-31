# NSW2 — shared engine and mainline synchronization (31 October 2026)

The NS2 research branch is a **compatibility extension of the existing Encore emulator**, not a separate cloned emulator. It retains the entire existing PS5 CPU, memory, Dynarmic, shader cache, texture cache, rendering and scheduling optimizations from main.

## Mainline ancestry

- Git merge parent main: `86ef6f2d1acc9471205d0f9c006369a2a4c1057a` (includes latest F07 contiguous multirange copy work).
- Research-only implementation stays in `research/ns2-ps5-compatibility`; never merge it into production `main` until the full integration and release gates have passed.
- Vendor branch `niakw/Prospero.Eden-Encore-vendor:research/ns2-shared-core`: parent includes mainline vendor `cb244e3f4ab8f834e254663fb8bf4b34c66079b9`, with N58/N62/N64/N65 additions. The research app submodule pins the merged vendor research owner (latest shared F07 PS5 changes + N54 + sparse API); see the gitlink for the exact commit.

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

N54 scratch and its frame trim are now maintained in the single vendor root `encore-active/ns2-astc/include` (upstream scratch + shipping patched texture cache parity). N54 no longer generates source headers. N56's native driver pipeline cache guard now also lives directly in the versioned vendor Vulkan source (opt-in compile macro; no generated TU). N55/N59 ASTC staging and N63 sparse budget helpers have moved unchanged to `vendor/encore-active/ns2-helpers/include`; their old `headless/ns2` copies are deleted and the host test include roots point at vendor. N57 decoder, N60 texture cache and other older NS2 overlays are **not yet fully migrated** into shared vendor owners. Their default is OFF. These still require a separate exact native API/compile audit before promotion; synthetic host oracle success is not PS5 execution proof. Vulkan queue sparse binding, fence lifetime and complete NS2 user titles remain unimplemented. No console testing requested.

## Verification

The strict `check-vendored-vulkan-fork.py` and F07 allocator OOM oracles continue to compare all generated native source files byte-for-byte apart from the **exact audited additive N65 sparse methods**, with N65 separately exercised by Clang/GCC source extraction. Do not simply disable a parity assertion to accommodate a new feature.
