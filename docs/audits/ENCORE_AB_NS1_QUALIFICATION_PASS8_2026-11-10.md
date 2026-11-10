# A/B NS1 — pass 8: full original-source Merkle compare and first native compiler failure

**Date:** 2026-11-10. **Scope:** PR #45 draft audit only; no `main`/vendor changes, no native build trigger, source patch, dependency repin or merge. Supplements [pass 7](ENCORE_AB_NS1_QUALIFICATION_PASS7_2026-11-10.md) and the [R18 exact-blob manifest](R18_VENDOR_EDEN_35_SOURCE_MUTATIONS_2026-11-10.json).

## R18 — important verified source-of-truth divergence

**The current vendor `sources/eden/` is not byte-identical to its declared original upstream `eden-emulator/mirror@5f142c79`.**

- The pinned vendor Gitlink is `22b69d6053db41b74edac2633c012f925b84f69e`. Its `sources/eden` tree is `b7a1d7c41e9ae0f3a7379e04809d16bffd74da8b`; its `src` subtree is `2ce268b372cb34b3cefd35557bed09930cc2732e`.
- Official upstream Eden `5f142c7926d0c7fcbbd0ce30794d72f638a43b2a` has `src` tree `6af25b0ad9bb2b0cb30c446b269a2784ff53a471`.
- A Git Merkle-tree walk of the two roots found differences **only** in `src/core`, `src/shader_recompiler`, and `src/video_core`. All other `src` top-level subtrees matched without byte-by-byte re-fetch.
- Recursive blob enumeration of the five changing nested subtrees (core HLE; shader backend/frontend/IR optimization; Vulkan renderer) returned `truncated=false` on both sides. Together with three direct-root source blobs, it identified **exactly 35 modified paths** and **zero extra/missing paths**: 9 kernel/HLE, 19 shader, 7 GPU/Vulkan.
- The complete table of paths, official Git blob SHA and vendored blob SHA is [R18_VENDOR_EDEN_35_SOURCE_MUTATIONS_2026-11-10.json](R18_VENDOR_EDEN_35_SOURCE_MUTATIONS_2026-11-10.json). Git blob IDs are cryptographic identity markers for these Git objects, **not** a host/toolchain linking receipt or a runtime equivalence test.

**This conflicts with the source layout contract** in `docs/EDEN_OVERRIDE_SOURCE_OF_TRUTH.md` and the vendor README, both of which state that original `sources/` remain immutable, with maintained project changes under `encore-active/`. A notably concrete case is `src/video_core/renderer_vulkan/fixed_pipeline_state.h`: the official pinned header has no `forced_color_resolve`; the vendored `sources/eden` header has **three Encore-specific added lines**, including `BitField<22, 1, u32> forced_color_resolve`. The PS5 native CMake actively copies this modified header from `vendor/sources/eden` into the generated native include directory. Its relocation and future exact provenance **require a separate, coordinated migration after P5**, not a silent patch/rewrite while the main build runs.

**Caveat:** this source-policy discrepancy does not prove a compiler/link bug in each of 35 files; some may be maintained historical copies used intentionally by particular selectors, others may be dead source. Before a migration, create a per-path ownership map: official snapshot, current used override, actual build selected bytes and non-regression test. Do not simply delete/revert the 35 files without preserving their behavior.

## P5 native compilation — tenth run is a genuine new diagnostic, not a successful build

The independent `main` tenth native build [#42887138500](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42887138500) on engine `89e0f8c2bc378fedb849d90dade1e99f3cf8697c`, same vendor `22b69d6`, **failed** in `Build and stage native release`, after Ninja progressed to approximately `[880/1870]`. The actual compile diagnostics are:

1. `vk_turbo_mode.cpp.o` includes active [`vk_graphics_pipeline.h:97`](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/22b69d6053db41b74edac2633c012f925b84f69e/encore-active/eden-vulkan/include/video_core/renderer_vulkan/vk_graphics_pipeline.h#L97). It accesses `key.state.forced_color_resolve`, but the **FixedPipelineState seen by Clang in that unit lacks the field**. The official pinned Eden header also lacks the member; the separately modified vendor `sources/eden` header has it. `headless/vulkan.cmake:17-25` already tries to shadow/copy that vendor header to `$PORT_BUILD_DIR/include`. Its mere existence did **not** guarantee that this unit saw the intended definition; inspect the specific preprocessor include trace and compile command priority before changing source or ABI.
2. `vk_texture_cache_base.cpp.o` includes active [`ns2-astc/.../texture_cache.h:668,707`](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/22b69d6053db41b74edac2633c012f925b84f69e/encore-active/ns2-astc/include/video_core/texture_cache/texture_cache.h#L668) and reports `use of undeclared identifier 'SCOPE_EXIT'` twice. Pinned Eden `common/scope_exit.h` defines the macro. A bridge already exists at `headless/ns2_astc_texture_cache_scope_bridge.h` and is configured by `headless/vulkan.cmake:26-30`; its effective inclusion/precedence **is not confirmed** by the compiler error log.
3. Main's [cached native Ninja graph run #42886401919](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42886401919) **was successful** after reconstructing the audited PS5 OpenGL SDK, but success of CMake/Ninja graph parsing does **not** attest the dependent header's C++ semantics or actual compile.
4. No native ELF or ZIP was produced from the tenth run; there are no release artifacts or device measurements to attribute a fix to. The build's failures are **native compile regressions**, unlike AB-01..AB-04 which remain **source-level runtime risk candidates**.

**Precise next inspection (owned by main build workstream, NOT this audit branch):** for the two failing units only, capture `clang++ -H` or a preprocessor dependency trace on the **existing** native compile command, record the paths and SHA256 of the resolved `fixed_pipeline_state.h`, `texture_cache.h` and `scope_exit.h`, ensure one canonical owner of each header, and rerun narrowly *before* another expensive all-target build. Verify both NS1 and NS2 common include behavior and no header-class layout split. The A/B audit should only consume the resulting evidence, not perform repairs in `main`/vendor.


## R18 — actual native source-file owner disposition for the 35 differences

The independent [read-only compile-path/byte witness #42894073292](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42894073292) ran successfully against the cached ninth native compilation database (generated for `af106ca`, not latest main). The full `r18-original-owners.json` JSON is retained in the workflow's `ab-ns1-historical-compile-witness` artifact.

| File type/selection | Count | Verified interpretation |
|---|---:|---|
| Scheduled original Eden SHA | **7** | Selected bytes match the *official* pinned upstream source, **not** the modified `vendor/sources/eden` copy. |
| Scheduled maintained Encore override SHA | **6** | Initially grouped as "neither original nor altered snapshot", but all six were separately matched **by exact Git blob hash and real source path** to `vendor/encore-active/eden-shader` (five units) or `vendor/encore-active/eden-core` (one unit). Legitimate maintained third variants, not unknown input. |
| Not scheduled by the same source relative filename | **5** | No compile database owner using the exact `src/...` filename; **does not prove functionality absent**, e.g. renamed/maintained owner may replace it. |
| Header-only mutation | **17** | A `compile_commands.json` records translation units, **not selected header bytes**. Requires compiler `-H`, depfile or preprocessor trace to verify inclusion and ABI consistency. |

The five nonscheduled path candidates are `core/hle/kernel/k_address_arbiter.cpp`, `core/hle/kernel/svc.cpp`, `core/hle/kernel/svc/svc_address_arbiter.cpp`, `shader_recompiler/backend/spirv/spirv_emit_context.cpp`, and `video_core/renderer_vulkan/vk_texture_cache.cpp` (all below `src/`).

**Consequence:** the 35 divergences are now **fully enumerated** and their *historical translation-unit selections* sorted into non-overlapping classes; the main unresolved source provenance is **17 headers, possible renamed owners for five source names, and current-main/link outputs**. This is progress in ownership triage, **not** 35 repaired bugs or completion of the full R18 legal/ABI/SBOM gate.

After discovering the six legitimate maintained SHA matches, `tools/audit/attest-r18-vendored-original-compile-owners.py` was refined to label them `scheduled-maintained-override` only when **the recorded scheduled path and actual bytes** both match an initialized `encore-active` candidate. All other unexpected paths remain `scheduled-unrecognized-source`. This is conservative and does not infer source semantics.

## Reconciliation with A/B completion criteria

| Row | Update | Status |
|---|---|---|
| **R00 current build** | Tenth native build SHA checked; step failure and source-vs-executable proof now separated | Open, no native linker success |
| **R05 source selection** | Historical compile DB proves pinned Dynarmic owners; tenth run exposes header include selection divergence | Open, exact header include receipts missing |
| **R18 source policy** | 35 mutated original-source paths fully accounted for with Merkle/blob SHAs | **Confirmed structural debt**, remediation/test ownership open |
| **R23 upstream comparison** | Complete 155 Eden commit metadata, segmented file windows and 21 triaged leads, but capped mega-changes and semantic parity remain | In progress |
| **R02 native driver** | Vendor pinned Mesa not updated; no Meson compile database in A/B snapshot | Open |
| **R03/R04** | 4 source gaps remain; no real compiled positive/negative behavior proof | Open |

**Decision:** no claim that the *full audit* is complete. A data-rich inventory is not the same as proof of every active compiled file, checked security alert, or runtime correctness. PR #45 stays draft, separately reviewable, and must remain isolated from build work.
