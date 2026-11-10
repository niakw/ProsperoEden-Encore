# NS2 upstream optimization watch — isolated development audit (2026-11-10)

## Critical native owner reconciliation — 10 November 2026 (supersedes prior O1/O3 guesses)

**The native NS2 path does not use the legacy `BindComputeStorageBuffer` size heuristic.** This is source-verified on the pinned vendor SHA `22b69d60`: 

- [`vk_compute_pipeline_cost.cpp`](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/22b69d6053db41b74edac2633c012f925b84f69e/encore-active/eden-vulkan/vk_compute_pipeline_cost.cpp): legacy `Configure()` uses `BindComputeStorageBuffer`, while NS2 `ConfigureNative()` calls `NativeQmdResourcePlan::StageVulkanBufferBindings` and `ObtainBuffer` directly, using an authenticated GMMU span.
- [`native_qmd_compute_environment.h`](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/22b69d6053db41b74edac2633c012f925b84f69e/encore-active/ns2-runtime/ampere/shader_recompiler/frontend/ampere/native_qmd_compute_environment.h): `BuildResourcePlan` reads four u32 words (target low/high, `bytes`, `tag`) and sets `known_size = tag == 0 && bytes != 0`; otherwise `requires_memory_layout` becomes true and `HasResolvedGpuBufferBindings()` rejects the plan. A bare pointer whose next word looks like a small size *could* be misread if the tag matches, but actual guest input and resulting pixels have not been demonstrated. More likely another legal no-size form may simply be rejected; both demand ABI evidence.
- [`vulkan_rasterizer.cpp`](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/22b69d6053db41b74edac2633c012f925b84f69e/encore-active/eden-vulkan/vulkan_rasterizer.cpp): physical mapping snapshots are captured and matched again after staging and at native dispatch commit. These anti-remap protections must remain intact.

**O10 — potential CPU optimization, not yet a measured bottleneck:** `NativeQmdContiguousGpuSpan` checks every 4 KiB boundary and the final byte, up to 256 MiB. One contiguous aligned **32 MiB** buffer causes **8,193 mapping lookups** under the current algorithm. QMD3 capture, staging and commit can repeatedly validate the same span. The algorithm is intentionally conservative; never remove its safety scans without a proven equivalent process-epoch/revision guard. First instrument per-dispatch lookup counts and timings under live PS5 NS2 sessions.

**Added source-linked witness:** [`research/ns2/check_native_qmd_owners.py`](../research/ns2/check_native_qmd_owners.py) extracts the exact native mapped-span C++ function from the pinned vendor and compiles it with synthetic maps under Clang and GCC UBSan. The same pinned function body and 17-case harness were reproduced locally and **17/17 assertions passed on each compiler**; the new repository script itself has not yet run on GitHub CI or a full checkout. No PS5 performance claim.

**Corrected priority:** (1) record actual QMD3 descriptor values and rejection reasons without private game data; (2) identify proven legal unknown/bare-size cases; (3) qualify safe native sizing plus mapping race barriers; (4) measure page-walk CPU cost before considering memoization. No legacy NS1 behavior should change.

---

**Status:** investigation / post-first-build backlog; **not** a PS5 compatibility claim or permission to merge optimizations.  
**Own snapshot:** Encore `dd9f2b96f46f77c1b895d7f4f259aa945971a412` / pinned vendor `22b69d6053db41b74edac2633c012f925b84f69e`.  
**Build protection:** research branch and draft PR only. No main, vendor, gitlink, workflows, release configuration, or active build modifications; no PS5 build or GPU test launched by this audit.

## Evidence rules and integration order

- **Observed source difference** is not proof of a console bug, FPS gain, or supported NS2 rendering. A source-level candidate must receive a bounded regression test (positive *and* negative), source-owner review, host validation, NS1/NS2 regression evidence, then P5 console timing/frames when available.
- **Never port by TitleID**, fabricated descriptor size, undefined opcode, unsafe memory relaxation, architecture-specific Metal/Apple behavior or another fork's claimed FPS. Source adaptations must be generic and compatible with the single native NS1/NS2 engine.
- Main's P5 native build is prioritized. Do **not** add pull-request CI fan-outs or change the pinned vendor until the initial PS5 build, packaging and baseline are finished. Do not merge this draft PR automatically.
- Compare *exact commit SHA + path + semantic behavior*, not stars, last-updated metadata or claims of running a game. Maintain rejection evidence alongside accepted code.
- Read upstream licenses before importing any implementation (the initial phase below is source analysis, not copying).

## Sources frozen for this pass

| Reference | Checked branch / SHA | Evaluation role |
| --- | --- | --- |
| [Lichii](https://github.com/zortos293/Lichii/tree/e8be28e5d6a7) | `zortos293/Lichii` `nx2` `e8be28e5d6a7` | **Primary** GPU, compute and memory upstream |
| [nxnative](https://github.com/seedds/nxnative/tree/a77c0ee8a6b6) | `seedds/nxnative` `main` `a77c0ee8a6b6` | **Primary** performance hypotheses and instrumented references; Apple/Metal != PS5/Vulkan |
| [PS5_Lichii](https://github.com/mihawk-99/PS5_Lichii/tree/549569a2b6f2) | `mihawk-99/PS5_Lichii` `main` `549569a2b6f2` | PS5-specific memory/heap/packaging observations; never infer Encore compatibility |
| [Eglantine-PS5-](https://github.com/viejunerd/Eglantine-PS5-/tree/6243701d6a95) | `viejunerd/Eglantine-PS5-` `main` `6243701d6a95` | PS5 experimental buffer/VRAM and task/mesh comparisons |
| [EglantinePS5](https://github.com/heydemoura/EglantinePS5/tree/095df4eb491b) | `heydemoura/EglantinePS5` `main` `095df4eb491b` | Ampere register decoding, memory lifecycle; reject game-ID shortcuts |
| [Eglantine community](https://github.com/Eglantine-Community/Eglantine/tree/78743f30c251) | `Eglantine-Community/Eglantine` `nx2` `78743f30c251` | Secondary upstream, compare semantic deltas to Lichii |
| [Eden-NS2](https://github.com/0x2593/Eden-NS2/tree/b2cef0c0f2e8) | `0x2593/Eden-NS2` `main` `b2cef0c0f2e8` | Historical reference; repository currently **archived**, not primary live source |
| [Eden-NS2 predecessor](https://github.com/ShadyHero/Eden-NS2/tree/edee9f728515) | `ShadyHero/Eden-NS2` `main` `edee9f728515` | Historical/reference only; also **archived**, points to 0x2593 |
| [oboromi](https://github.com/0xNikilite/oboromi/tree/c97664a8460e) | `0xNikilite/oboromi` `main` `c97664a8460e` | Independent ISA/negative-oracle reference; Rust PoC, not a PS5 backend |

These are observed branch heads on 10 November 2026; refresh snapshots before implementing. Previous internal audits are [Lichii diff (04 Nov)](NS2_LICHII_NX2_DIFF_AUDIT_2026-11-04.md) and [nxnative independent audit (06 Nov)](AUDIT_INDEPENDANT_NXNATIVE_EDEN_ENCORE_NS1_NS2_2026-11-06.md). This register tracks **new deltas** without reopening already closed H01–H07/G01–G10 host contracts (see [unified roadmap](ROADMAP_NS1_NS2_UNIFIED.md)).

## Prioritized delta register

**O1 — high: native NS2 read-only Compute storage-buffer extent, not a fixed arbitrary cap.**  
[Relevant Lichii commit #1231](https://github.com/zortos293/Lichii/commit/e8be28e5d6a7) differentiates native/bare-pointer **read-only compute** descriptors from writable SSBOs and avoids silently clipping valid read extent at 8 MiB. In Encore's pinned vendor, [`encore-active/eden-core/src/video_core/buffer_cache/buffer_cache.h`](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/22b69d6053db41b74edac2633c012f925b84f69e/encore-active/eden-core/src/video_core/buffer_cache/buffer_cache.h), `BindComputeStorageBuffer` passes only (`ssbo_addr, cbuf_index, is_written`) and `StorageBufferBinding` falls back to `min(memory_layout_size, 8_MiB)` when the next qword is not a valid declared size. This is a **verified legacy/shared Compute difference only**, not a measured Encore native NS2 rendering failure. `ConfigureNative` does not call that `StorageBufferBinding` heuristic. Native QMD3 instead validates four-word resource records and fails closed when the size is not known; see the critical owner reconciliation at the top of this document. The upstream itself says larger reads influenced lighting and that bare-pointer next words can be non-size fields. **Next:** prove precise native pointer provenance at the Ampere/QMD3 binding site, validate contiguous live GPU mapping and aligned [base,end), then add a read-only >=8 MiB *positive* and unmapped-gap, write, overflow, process lifetime *negative* tests. No universal cap removal.

**O2 — high: GPU-memory destruction/re-registration and stale cached SMMU backing.**  
[Lichii destruction/unmap commit](https://github.com/zortos293/Lichii/commit/bcb37c49f75b) and [reused device-range refresh](https://github.com/zortos293/Lichii/commit/9d90f25bfe29) address mappings that survive destruction of a CPU-backed region and later reuse old host pages at the same address. Encore already has maintained `encore-active/ns2-runtime/gpu_session/core/hle/service/am/service/gpu_worker.cpp` owners for commands 101/102/211–216, plus `encore-active/ns2-runtime/nvdrv_as/core/hle/service/nvdrv/devices/nvhost_as_gpu.cpp`; do **not** infer that 102 cleanup is absent. The named upstream `ReleaseBacking` mechanism was not found in the indexed pinned vendor, which is **not proof** of missing equivalent behavior. **Next:** source-trace 101→211→102→remap into new pages, multiple GPU aliases, partial overlaps, in-flight fences, and allocator-generation ownership. Require an executable hostile-reuse test before any modification.

**O3 — high: descriptor-size words that are actually another parameter.**  
[Eglantine-PS5- v1.219.029 change](https://github.com/viejunerd/Eglantine-PS5-/commit/15cde68e7ef1) discusses a non-size word being read as an immense storage-buffer length. Encore's pinned `StorageBufferBinding` currently regards a nonzero low 32-bit value as a size when the upper 32 bits are zero and it fits `GetMemoryLayoutSize`; a bare-pointer data word can potentially satisfy this condition. **Next:** authenticate descriptor type from shader/resource metadata, not an OoT-specific heuristic or a magic 256 MiB threshold; use guards for impossible sizes, alignment, valid mapped span, read versus write, and exact-width host tests. Coordinate O1 and O3 in **one** safe binding contract.

**O4 — medium: memory/texture-cache budgets and reclamation on the PS5 host.**  
[Lichii host commit headroom](https://github.com/zortos293/Lichii/commit/ddd19a170b45) addresses **Windows** commit limits, not the PS5's RAM accounting; do not copy Windows APIs. [PS5_Lichii heap investigation](https://github.com/mihawk-99/PS5_Lichii/commit/70b85df49d41) provides useful ownership/category evidence but no matching Encore measurements. **Next:** instrument alloc/commit, cache residency, JIT and texture scratch with bounded sampling; profile p50/p95/p99 + peak memory and collect events on actual PS5. Check existing source `headless/jit-allocator.h`, `vendor/encore-active/eden-core/src/video_core/texture_cache/`, and the native heap before proposing reclaim/eviction changes. Prioritize avoiding OOM without trashing shader/texture reuse.

**O5 — medium: pipeline negative-cache/search thrash.**  
[nxnative missed-archive search caching](https://github.com/seedds/nxnative/commit/2f131edc1b45) eliminates repeated negative archive probes under table pressure (upstream measurements are Mac, **not** PS5). Encore already has a PS5 Vulkan pipeline cache with persistent writes and guards; that is **not equivalent proof** of caching *negative lookups*. **Next:** collect negative lookups/cost, validate generation/invalidation on shader recompilation or changing guest resources, and only then compare a bounded miss memoization against the baseline.

**O6 — medium: synchronization/report timestamps and render cadence.**  
[nxnative segmented GPU timestamps](https://github.com/seedds/nxnative/commit/3304d6a0d7ed) and [exact counter-report shadow exclusion](https://github.com/seedds/nxnative/commit/4c574a6f0552) are semantic/range issues, not Metal code for PS5. Encore already has N76 GPU tick generation and VI2/fences. **Next:** prove report values and ordering per submission segment, 16-byte versus page-sized interference, fence completion, and instrumentation on current NS2 guest path. Never claim a performance gain based on Apple timing.

**O7 — medium-low: thread wake-up/backoff, after correctness baseline.**  
[nxnative short-sleep polling](https://github.com/seedds/nxnative/commit/fec8e1f26b42) documents a massive host-wakeup reduction on Apple hardware, but with a small observed change in dropped frames and different scheduler implementation. **Next:** identify actual Encore guest `SleepThread`/yield paths, measure wakeups, run a bounded escalation test with genuine short sleeps and interacting events; preserve guest timing, JIT dispatch, and NS1 stability. Do not import Apple-specific sleep behavior.

**O8 — correctness oracle: Ampere register predicates / task-mesh dependencies.**  
[oboromi IADD3 carry-out rejection](https://github.com/0xNikilite/oboromi/commit/77594cf0e1b8) demonstrates conservative negative decoding; [EglantinePS5 high uniform registers](https://github.com/heydemoura/EglantinePS5/commit/eab04ed6a7f0) discusses UR28+; [its game-specific mesh skip](https://github.com/heydemoura/EglantinePS5/commit/80afe48d22f2) is **not** an acceptable fix. Encore already has Ampere/QMD3/SPIR-V and tests. **Next:** check precise recognized ISA and UR operand coverage, reject unsupported carry-output encodings, then prove GPU-written task counts precede mesh consumer reads. Never suppress a title's mesh draws as a generic optimization.


## Additional fork discovery (10 Nov; not automatically adopted)

| Newly checked fork | Verifiable recent difference | Disposition |
| --- | --- | --- |
| [mucahidkambur/EglantinePS5](https://github.com/mucahidkambur/EglantinePS5/commit/588238a37e) (`dbadad075c`, 1 Nov) | Own [BCn array/mip handling](https://github.com/mucahidkambur/EglantinePS5/commit/588238a37e) and [Vulkan GC byte accounting](https://github.com/mucahidkambur/EglantinePS5/commit/dbadad075c) | **Secondary follow-up:** compare texture cache resource/accounting semantics against O4; verify image completeness and memory before porting |
| [exploitizm/EglantinePS5](https://github.com/exploitizm/EglantinePS5/commit/d1a8d529ad) (8 Nov) | Isolating cold paging, staging caps and stale image-upload skipping with diagnostic file switches | Useful **hypothesis isolation**, not a performance win; reject user-facing debug switches or changing release semantics without reproducible symptoms |
| [quatrixone/PS5_Lichii](https://github.com/quatrixone/PS5_Lichii/commit/8e90019d57) (9 Nov) | Frame cap and frame-generation Auto rate changes | Conditional only; presentation pacing must not conceal absent guest GPU frames, increase latency or regress NS1 |
| [PlayTendoh](https://github.com/premohq/PlayTendoh) / [Nightshade](https://github.com/Oliv3rmoon/Nightshade) | Separate multi-emulator frontend / PS5 fork work | Not elevated to NS2 core references without an identified and demonstrated generic CPU/GPU implementation difference |

### O9 — secondary texture/GC fork comparison

The BCn mip/array and Vulkan GC accounting changes above should be compared to Encore's **already existing** texture/image/eviction ownership, with positive multi-layer textures, negative malformed extents, exact device-memory accounting and a bounded VRAM-pressure fixture. These forks must not overtake Lichii as the primary source merely because they carry a recent patch. The task is to **test whether a source-level gap exists**, not to import their heuristics or launch another PS5 build.

## Research fixture 2026-11-10 — O1/O3 (prototype only, not vendor integration)

A standalone C++20 candidate contract is in [research/ns2/ssbo_extent_contract.hpp](../research/ns2/ssbo_extent_contract.hpp) with [positive/negative tests](../research/ns2/test_ssbo_extent_contract.cpp) and [offline reproduction instructions](../research/ns2/README.md). This is **not compiled into Encore** and cannot impact a native build. It is deliberately under a directory excluded by the examined active main source/PR validation path filters.

**Local offline results:** `clang++` and `g++`, `-std=c++20 -O1 -Wall -Wextra -Werror -fsanitize=undefined -fno-sanitize-recover=all`: **19/19 each** (38 individual assertions across the two binaries). Tests are a synthetic semantic harness, **not** direct execution of the production BufferCache template or a PS5 GPU.

Actual pinned vendor source audit:
1. [Vulkan Compute pipeline `vk_compute_pipeline_cost.cpp`](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/22b69d6053db41b74edac2633c012f925b84f69e/encore-active/eden-vulkan/vk_compute_pipeline_cost.cpp) validates the flattened `storage_buffers_descriptors` via `ComputeStorageLayout::ForEach` but passes only `(index, bank, offset, writable)` to `BindComputeStorageBuffer`. There is **no proven native-bare descriptor type at this binding call**. **Earlier finding superseded:** this `BindComputeStorageBuffer` call belongs to the legacy `Configure()` owner; NS2 uses separate `ConfigureNative()` and `NativeQmdResourcePlan`. Do not modify the legacy binder for this NS2 issue.
2. [Shared `BufferCache::StorageBufferBinding`](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/22b69d6053db41b74edac2633c012f925b84f69e/encore-active/eden-core/src/video_core/buffer_cache/buffer_cache.h) reads `ssbo_addr+8` and takes its low 32 bits as length when high bits are zero, the value nonzero, and it fits `GetMemoryLayoutSize`; otherwise it uses `min(layout, 8 MiB)`. This source fact is reproduced in the test as `CurrentVendorSizeHeuristic`. A native bare pointer followed by `266` becomes a **266-byte binding** under that heuristic; a non-size word with nonzero high bits falls back to **8 MiB**. Neither is evidence such input occurred on the PS5 yet.
3. [Active `MemoryManager::MaxContinuousRange`](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/22b69d6053db41b74edac2633c012f925b84f69e/encore-active/eden-core/src/video_core/memory_manager.cpp) **already implements a per-thread page-table-revision-keyed cache** for repeated contiguous GPU scans. Do not reinvent it or add an unchecked scan. Use its real result, bound by buffer limits and ownership epoch, when integrating a verified native read.
4. The [Ampere QMD3 IR code](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/22b69d6053db41b74edac2633c012f925b84f69e/encore-active/ns2-runtime/ampere/shader_recompiler/frontend/ampere/native_indirect_cbuf.h) validates SSBO/CBUF index, write access, 16-byte records and QMD bank provenance before some native atomics. A future fix must preserve this admission contract and must **not** promote every reflected Compute binding to `NativeBare`.

The prototype distinguishes `LegacySized`, authenticated `NativeBare`, authenticated `NativeTable`, and `Unproven` (rejected); it checks actual contiguous mapping, unaligned base, Vulkan `maxStorageBufferRange`, zero/null/overflow/invalid alignment, conservative writes, and NS1 fallback. It leaves production untouched.

**Required actual-source gate before integration:** establish the native four-word descriptor ABI and prove legal unknown/bare length semantics before implementing any bounded read-only resolution inside the existing `NativeQmdResourcePlan` and `ConfigureNative` owners. Preserve both current mapped-span and physical snapshot rechecks; test known-size, zero-size, tag mismatch, fake 266-byte size, all mapping gaps, writes, and NS1 regression on maintained source.

### O2 — hostile backing-epoch model (host-only)

The companion [23-case C++20 lifecycle fixture](../research/ns2/test_gpu_backing_lifetime.cpp) covers GPU aliases, overlapping mappings, unmapped gaps, pending fences, deferred destruction, stale generation rejection, reused CPU/GPU addresses, isolated backing lifetimes and integer overflow. Local Clang/GCC UBSan: **23/23 each**. This is a *synthetic model*, not execution of Encore NVDRV/GMMU code.

Actual [GPU worker `ReleaseMemory`](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/22b69d6053db41b74edac2633c012f925b84f69e/encore-active/ns2-runtime/gpu_session/core/hle/service/am/service/gpu_worker.cpp) already checks live NVMap references (`dupes`, `internal_dupes`, `pins`), retains a pending unlock owner on partial failure, and only signals completion after unlock. Do **not** label this missing or remove these protections. The unresolved cross-owner question is whether multiple GPU alias ranges still reference an old CPU backing after a successful 102 cleanup and later re-registration; compare the full NVDRV address-space mappings and their current process generation before claiming a bug. A real test must run those actual owners against each other.
## Working acceptance checklist

- [x] Research branch created from a pinned main SHA, vendor gitlink recorded.
- [x] Primary and secondary branch heads captured with exact links, stale archived sources classified.
- [x] Candidate O1 source-level mismatch verified in pinned Encore vendor.
- [x] O2/O3 associated with existing maintained owners rather than labelled as missing wholesale.
- [ ] Establish baseline console framebuffer + NS1/NS2 timing, peak VRAM/RAM and logs after the first P5 build.
- [x] Create a standalone *candidate-policy* host fixture with 19 assertions (Clang/GCC UBSan), **without vendor/main writes**; not yet actual-source verification.
- [ ] Build actual maintained-source positive/negative regression receipts for O1–O3 without altering main/vendor.
- [ ] Review any implementation in this branch against the then-current pinned vendor/source ownership and license.
- [ ] Run limited host CI deliberately when main's native build is no longer competing; record actual SHAs.
- [ ] Only after measurable non-regression: propose a separate reviewed integration PR for main. No auto-merge.

### Metrics for deciding whether an optimization is real

Per fixed route and same console/build: first guest framebuffer reached; functional frame count; frame time **p50/p95/p99**, CPU busy/wakeup count, GPU queue wait/fence latency, shader/pipeline miss count and build cost, read-only SSBO extent rejects, stale GMMU/SMMU reuse events, resident texture/JIT/heap peaks, crash/OOM counts. Repeat warm and cold runs and preserve Maxwell/NS1 oracles. An improvement with hidden wrong pixels, synchronization corruption or increased crash risk is rejected.

**Current classification:** development audit / candidate review only. No claims of benchmark wins or PS5 validation.
