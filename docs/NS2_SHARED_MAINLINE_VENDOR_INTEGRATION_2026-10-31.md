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

## ExeFS and NPDM helper ownership

Eight unchanged loader/metadata/NSO admission headers have moved from `headless/ns2/overrides` to `vendor/encore-active/ns2-helpers/include` as the single research source owner. The CMake source selector still uses the **existing** core loader implementation; includes for metadata, ExeFS and host tests now resolve from vendor. These are generic, host-tested admission checks, **not proof of Switch 2 game execution**. Remaining whole-translation-unit loader/process research overlays are still isolated; no release promotion is implied.

## N52 source owner

Experimental `Service::Process::Run` return-code checking is now compiled from the original `vendor/sources/eden/src/core/hle/service/os/process.cpp` under `EDEN_NS2_PROCESS_RUN_GUARD`. Its old cloned C++ translation unit in `headless/ns2/overrides` has been removed; default Switch 1 behavior is unchanged. Host regressions extract the real vendor method with Clang/GCC.

## Versioned NSW2 loader sources

The four research-only translation units (`ProgramMetadata`, `AppLoader`, `DeconstructedRomDirectory`, `NSO`) have now been relocated **without byte changes** from `headless/ns2/overrides` into `vendor/encore-active/ns2-experimental/src/core`. Original PS5 optimized engine source selection is preserved when experimental switches are OFF. These are still **separate opt-in implementations**, not yet additive changes merged into the shipping owners; a full native build and Switch 2 guest runtime must be validated before claiming production-grade support.

## N50/N51 GPU-memory source consolidation

The PS5 device-memory continuity guard N50 and changed-page GPU PTE notification batcher N51 are now conditionally compiled in their original optimized vendor C++/include owners, not in copies under `headless/ns2/eglantine`. Both feature macros are OFF by default, forbidden for final release, and preserve the pre-research PS5 owners byte-for-byte after exact reversal; helper headers have one vendor location. Clang/GCC host oracle tests remain, but native PS5 GPU validation is outstanding.

## Experimental A64 translation ownership

The five immutable research decoder/translator sources for LDAPR, RETAA/RETAB and exclusive atomics are now versioned under `vendor/encore-active/ns2-a64/dynarmic`, with the exact old Git object IDs retained. Host and native research build selectors use that vendor source; no `headless/ns2/dynarmic` override remains. These remain experimental decoder implementations and are not evidence of complete NSW2 execution or PS5 compatibility.

## Research feature naming and PS5 test gate

Eglantine is an **external Eden-derived emulator**, reviewed only as an attributed upstream source of patches and public fixtures. It is not Encore's application identity. Four research-only native CMake selectors are named `EDEN_NS2_{GPU_RANGE_BATCH,PIPELINE_CACHE,VIEW,CONTINUITY}_EXPERIMENTAL`; the source-owner test rejects upstream branding leaking into the CMake binary configuration. Historical review documents and `check_egl_*` test filenames deliberately preserve attribution.

**Console test gate:** host CI is green on the prior branch head, but no NS2-ready PS5 artifact, complete `Core::System::Load`/real kernel boot, nor Vulkan sparse-queue/fence lifetime validation has yet been established. A synthetic NSP or host shader smoke test is not proof of Switch 2 game compatibility. Keep `main` and release selectors unchanged until an isolated native PS5 research build can be produced and documented without claiming working commercial games.

N50/N51 shared C++ helper namespaces were normalized to `Eden::NS2::GpuMemory` in vendor research commit `fec05dadfb59`, without changing helper algorithms, compilation gates or Switch 1 source paths. The original Eglantine patch attribution remains explicitly documented.
