# A/B global + Switch 1 — pass 7: actual selected JIT bytes, full Eden commit register and honest exit gates

**Date:** 10 November 2026. **Scope:** independent draft PR #45, production NS1/common runtime and full A/B architecture/dependencies. No new PS5 build, merge, rebase, vendor repin, production source or workflow changes from this audit. This report **does not certify completion of the full A/B audit**.

## Exact snapshots and proof classes

- Audit baseline: Encore `e4f6a8253e1f6204a6f99d3b3d29abad1800f4c7` and `vendor` gitlink `22b69d6053db41b74edac2633c012f925b84f69e`. The native ninth-run cached compilation graph was originally generated for engine `af106ca4431557246bc1db6d47ac5da562231bb3` with the **same vendor gitlink**.
- Main advanced independently to `89e0f8c2bc378fedb849d90dade1e99f3cf8697c` when checked, **without a `vendor` change** relative to the A/B starting point. Main's tenth native PS5 workflow [#42887138500](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42887138500) was running at the observation; no release or PS5 gameplay success is inferred.
- **Corrected previous chronology:** cached-graph diagnostic [#42883943523](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42883943523) succeeded by detecting the *old invalid* Ninja graph. Later [#42886401919](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42886401919) **successfully reconstructed the pinned OpenGL SDK**, completed native CMake configure and generated a **parsable current native Ninja graph** (`CURRENT_MAIN_NATIVE_NINJA_GRAPH_PASS`). This is a valid **configure/graph proof**, not a completed native link.
- The isolated [A/B read-only compiled-source workflow #42890783117](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42890783117) restored **3.38 GiB** of the existing ninth-run cache, initialized the **pinned vendor** and ran the static-source checker, its synthetic tests, owner classifier, and SHA-256 source-byte matcher. All tools executed successfully; this job **did not compile, link or run a PS5 game**.

## AB-05: real JIT scheduled owners — stronger than static CMake search

The read-only workflow output identifies the **specific original-source bytes scheduled by native CMake** in the historical ninth-run `compile_commands.json`:

| Owner | Scheduled source path | SHA-256 matched to exact canonical owner | Classification |
|---|---|---|---|
| JIT signed division | `$scratch/source/src/dynarmic/src/dynarmic/backend/x64/emit_x64_data_processing.cpp` | `vendor/sources/eden/src/dynarmic/src/dynarmic/backend/x64/emit_x64_data_processing.cpp` | **Pinned ORIGINAL**; maintained override **not selected** |
| JIT float rounding | `$scratch/source/src/dynarmic/src/dynarmic/backend/x64/emit_x64_floating_point.cpp` | `vendor/sources/eden/src/dynarmic/src/dynarmic/backend/x64/emit_x64_floating_point.cpp` | **Pinned ORIGINAL** |
| JIT vector | `$scratch/source/src/dynarmic/src/dynarmic/backend/x64/emit_x64_vector.cpp` | `vendor/sources/eden/src/dynarmic/src/dynarmic/backend/x64/emit_x64_vector.cpp` | **Pinned ORIGINAL**; maintained override **not selected** |
| AudioIn adapter | `headless/audio.cpp` | `headless/audio.cpp` | Project selected |
| RomFS builder | `vendor/encore-active/eden-core/src/core/file_sys/fsmitm_romfsbuild.cpp` | Same maintained source | Maintained selected |
| Shared shader emitter | `vendor/encore-active/ns2-runtime/ampere/shader_recompiler/backend/spirv/emit_spirv_context_get_set.cpp` | Same maintained source | Maintained selected, *conditionally enabled profile* |

Three RADV families (`radv_cmd_buffer.c`, `meta/radv_meta_buffer.c`, `meta/radv_meta_copy.c`) are **not in the restored CMake compilation database**. RADV uses its own Meson build and copied-source pipeline. Missing here is **not** evidence of absent RADV.

**Specific error in older tests/claims:** `headless/scalar-memory.cmake` declares replacement of x64 vector and data-processing TUs with two maintained sources, but this module has no confirmed inclusion from the inspected CMake graph. `tools/check-maintained-scalar-emitters.py` compares its content and prints `2 compiled units` **without consulting the actual compilation database**. Its source-parity assertion does not prove binary selection. The historical native database now affirmatively shows **original Eden bytes** for both, so do not claim the maintained emitters were compiled. Proof of a linked executable remains separate.

### Seven distinct semantics in Eden upstream 35f0dd7, not just two

The pinned baseline predates [Eden `35f0dd7`](https://github.com/eden-emulator/mirror/commit/35f0dd7c1ca064ec95ab7efd9981b00f8dcfb989). The upstream commit **itself contains seven corrections**, each with tests, plus an optional host-feature mask for test builds:

| Subcase | Pin-source discrepancy verified / qualification |
|---|---|
| **JIT-1 SDIV32 by zero** | Selected pinned `emit_x64_data_processing.cpp` lacks upstream `cmovz(eax, divisor)` before `jz`. Test A32/A64 dividend ±, divisor=0, -1 and INT_MIN/-1. **High priority.** |
| **JIT-2 FRINT fallback** | Selected pinned `emit_x64_floating_point.cpp` reads rounding at `>>8` and exact at `>>16`; upstream corrects to `>>0` and `>>8`. Test rounding modes, inexact FPSR and fast/slow paths. **High priority.** |
| **JIT-3 SM4 x64 codegen** | Pinned `emit_x64_sm4.cpp:56` retains absolute S-box `code.lea(...std::addressof(substitution_box))`, where upstream uses an absolute `mov` for PIE/Xbyak safety. Requires a native codegen/PIE test; precise compile-owner not yet attested. **High priority for crash avoidance if SM4 used.** |
| **JIT-4 A32 SHA1 instruction decode** | Pinned A32 ASIMD decoder still marks SHA1H/SU1 unallocated and lacks new SHA1C/P/M/SU0 decoder entries; upstream adds their translators. Requires A32 guest ISA/illegal-instruction tests; existing full translator ownership not proven. **Compatibility candidate.** |
| **JIT-5 SQSHLU vector saturation** | Pinned x64 vector emitter's `VectorSignedSaturatedShiftLeftUnsigned` retains pre-fix unsigned-shift computation and untyped `result`; upstream fixes narrow lane sizing/sign semantics. Selected *pinned* vector TU confirmed in historical native DB. Test signed 8/16/64 lanes, overflow and FPSR QC. **High priority for semantic fidelity.** |
| **JIT-6 vector FCVT #64 SSE2 fallback** | Pinned `emit_x64_vector_floating_point.cpp` macro covers only `0x00..0x3f`; upstream adds `0x40`, avoiding null thunk in the no-SSE4.1 path. Needs a constrained host-feature test; on PS5 Zen 2 the fallback may not be reachable normally. |
| **JIT-7 AVX-512 CLZ16 upper lanes** | Pinned/maintained `emit_x64_vector.cpp` has no `vextracti128` in the AVX-512 CLZ16 section, unlike upstream. **Low PS5-specific priority:** Zen 2 lacks AVX-512, but test for portable host correctness where relevant. |

These are **source semantic differences**, **not seven PS5-proven game bugs**. Do not cherry-pick a large Dynarmic commit or add experimental host-feature knobs to production. Verify exact selected owner, reproduce positive/negative behavior, then patch only the correct maintained source in a separately authorized implementation change.

## Complete upstream *commit-title inventory*, not completed behavior comparison

- New [155-commit register](R23_EDEN_ALL_155_COMMITS_2026-11-10.json): exactly **155 upstream commits** between the pinned Eden `5f142c79` (exclusive) and inspected mirror `89d1a1cd` (inclusive), with full SHA, date and title. All titles accounted for; automated title categories are explicitly **not** a semantic assessment.
- [Five 31-commit comparison windows](R23_EDEN_SEGMENTED_155_COMMITS_FILES_2026-11-10.json) were fetched to avoid the single combined comparison's **300 changed-file limit**. Windows 1/2/4 returned 238/128/146 files without the cap; windows 3/5 still reached 300.
- [Second-pass windows](R23_EDEN_UNCAPPED_SUBWINDOWS_2026-11-10.json) and [third-pass windows](R23_EDEN_DIFF_SUBWINDOWS_PASS3_2026-11-10.json) isolate bulk changes; several remain capped even within 3–8 commits. These include broad HLE API/dispatch changes, translation migrations, and newer common/formatter refactoring. **Do not claim all changed files or all semantics have been reviewed.** File-list cap requires per-commit pagination or narrower windows.
- [21 source-specific leads and upstream families](ENCORE_AB_NS1_UPSTREAM_MATRIX_2026-11-10.md) remain separately triaged against pin and maintained-owner information. This is focused review, not full semantic equivalence for all 155 commits. No fixes or SDK updates are imported by the audit.

### Scope correction: Eden c769b33

[Eden `c769b33`](https://github.com/eden-emulator/mirror/commit/c769b33e01882a04375c24406150097a2e124ece) modifies an **ARM64-native Dynarmic backend** (`backend/arm64/address_space.cpp`, `emit_arm64.cpp/.h`) and **common** `src/common/page_table.h`. PS5 Zen 2 executes x64 host Dynarmic, not the ARM64 backend. **ARM64 backend branch-range adaptation is non-transposable as such**; only the shared page-table sign-bit contract merits a separate x64 selected-header equivalence check. Reclassify AB-06 from generic P0 native JIT lead to *non-transposable ARM64 subpart + conditional shared-header candidate*, avoiding a false PS5 crash claim.

## A/B gate matrix — actual status, NOT a promise of full completion

| Roadmap ID | Evidence completed | Still required to close |
|---|---|---|
| **R00 baseline** | Exact branch/gitlink/HEAD split and main drift checked; no rebase | Freeze actual current packaged main/vendor SHA and existing compiled artifact when available |
| **R05 engine selection** | Six CMake source-byte matches; Dynarmic pinned-owner regression exposed; maintained / pinned distinction | Source graph for other TUs, link-map, selected header provenance, actual JIT/IPC/GPU semantic tests |
| **R18 dep/BOM/licences** | 22 `tools/deps.json` fetch entries, 10 OpenGL transitive items, vendor family separation, hashes pin syntax | Real linked/distributed SBOM, cryptographic archive checks, ABI, licence/notice and open security alerts disposition |
| **R23 upstream comparison** | All 155 Eden commit titles inventoried, 21 high-signal source leads, segmented file diff | Uncapped file diffs for bulk commits, behavior parity/duplicates for each relevant change; other fork lineages |
| **R02 PS5 forks** | Exact Mihawk/Swordpdf pins and high-risk RADV memory/pipeline candidates tracked | Meson actual compiled-input bytes, 12 maintained overrides vs transfer-meta files, native WSI and sync tests |
| **R17 other PS5 runtime** | Architectural-only leads documented; no borrowed incompatible native code | Only measured/applicable ideas warrant a separate prototype, not a completion prerequisite for source research |
| **R01 metrics** | Session frame queue/Present API counters and host analysis covered by separate tests | Actual guest FPS, GPU timestamps, latency and PS5 HDR/HUD/VRAM evidence |
| **R03 shader/RADV** | NaN emitter and RADV transfer/barrier source differences confirmed | SPIR-V validity, driver transfer-only/barrier-only pressure tests, replay and PS5 behavior |
| **R04 RomFS/AudioIn** | Maintained builder selected; AudioIn buffer underfill path and input routing risk source-confirmed | Actual source-compiled RomFS wide-tree sanitizer and AudioIn silence/bounds/teardown tests |
| **R22 static recompiler** | Research scope defined and architecture risks documented | A generic safe static recompiler is **not implemented**; no prototype or production activation authorized |

**Completion rule:** report `audit terminé` only once every **source-audit** row has explicit `closed with evidence / excluded with reason / blocked with specific missing proof`, no silent skipped lineage, all required test receipts match the frozen source graph, and uncertainty is correctly segregated from console P5 evidence. A/B research completion is different from implementation and device sign-off. This pass remains **IN PROGRESS**; do not claim exhaustive code review.

**PR #45 remains draft, audit-only. Do not merge or rebase while main's native build is being qualified.**
