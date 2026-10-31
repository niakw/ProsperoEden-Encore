# NSW2 — shared engine and mainline synchronization (31 October 2026)

The NS2 research branch is a **compatibility extension of the existing Encore emulator**, not a separate cloned emulator. It retains the entire existing PS5 CPU, memory, Dynarmic, shader cache, texture cache, rendering and scheduling optimizations from main.

## Mainline ancestry

- Git merge parent main: `50d260fca0f3fd8a56999ce91d51e3e43bfd2314` (all 146 commits formerly missing, including the newer F07 delta).
- Research-only implementation stays in `research/ns2-ps5-compatibility`; never merge it into production `main` until the full integration and release gates have passed.
- Vendor branch `niakw/Prospero.Eden-Encore-vendor:research/ns2-shared-core`: parent includes mainline vendor `cb244e3f4ab8f834e254663fb8bf4b34c66079b9`, with N58/N62/N64/N65 additions. The app submodule pins the exact merge commit `8927f89c445ab1101381c7af454fa66c2eead2ca`.

## Single maintained source owner

| Feature | Maintained engine owner | Applicability |
| --- | --- | --- |
| N58 sparse residency feature/queue admission | `vendor/sources/eden/src/video_core/vulkan_common/vulkan_device.h` | Any Vulkan image with sparse requirements |
| N62 VMA sparse memory chunks and rollback | `vendor/encore-active/eden-vulkan/vulkan_memory_allocator.cpp` and shared header | All qualifying 2D arrays, not game-specific |
| N64 sparse VkImage creation | Same native VMA allocator owner | Any supported Vulkan 2D array |
| N65 Vulkan sparse memory requirement query | `vendor/encore-active/eden-vulkan/vulkan_wrapper.cpp` and companion header | Generic Vulkan requirements |
| N63 sparse budget planner | Research-only pure helper with host tests | Generic dimension/layer/mip-tail arithmetic |

The four historical `prepare_egl_sparse_*` build-time source rewrite generators are removed. Existing Clang/GCC host tests validate the **real vendor methods** instead of generating copies of maintained engine files. Mainline PS5 native Vulkan source preparation and performance backports are preserved.

## Scope and remaining migration

Names such as FC27 in tests, traces and synthetic workloads indicate **stress profiles**, not runtime compatibility branches. Do not introduce Title IDs/game names into core optimization predicates. Regressions should be fixed by GPU command, texture format, memory, CPU instruction or service semantics and reused across Switch 1 and Switch 2.

N54 scratch, N57 decoder, N60 texture cache and other older NS2 overlays are **not yet fully migrated** into the shared vendor source owners. Their default is OFF. These still require a separate exact native API/compile audit before promotion; synthetic host oracle success is not PS5 execution proof. Vulkan queue sparse binding, fence lifetime and complete NS2 user titles remain unimplemented. No console testing requested.

## Verification

The strict `check-vendored-vulkan-fork.py` and F07 allocator OOM oracles continue to compare all generated native source files byte-for-byte apart from the **exact audited additive N65 sparse methods**, with N65 separately exercised by Clang/GCC source extraction. Do not simply disable a parity assertion to accommodate a new feature.
