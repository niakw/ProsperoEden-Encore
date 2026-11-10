# NS2 upstream optimization watch — isolated development audit (2026-11-10)

## Critical native owner reconciliation — 10 November 2026 (supersedes prior O1/O3 guesses)

**The native NS2 path does not use the legacy `BindComputeStorageBuffer` size heuristic.** This is source-verified on the pinned vendor SHA `22b69d60`: 

- [`vk_compute_pipeline_cost.cpp`](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/22b69d6053db41b74edac2633c012f925b84f69e/encore-active/eden-vulkan/vk_compute_pipeline_cost.cpp): legacy `Configure()` uses `BindComputeStorageBuffer`, while NS2 `ConfigureNative()` calls `NativeQmdResourcePlan::StageVulkanBufferBindings` and `ObtainBuffer` directly, using an authenticated GMMU span.
- [`native_qmd_compute_environment.h`](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/22b69d6053db41b74edac2633c012f925b84f69e/encore-active/ns2-runtime/ampere/shader_recompiler/frontend/ampere/native_qmd_compute_environment.h): `BuildResourcePlan` reads four u32 words (target low/high, `bytes`, `tag`) and sets `known_size = tag == 0 && bytes != 0`; otherwise `requires_memory_layout` becomes true and `HasResolvedGpuBufferBindings()` rejects the plan. A bare pointer whose next word looks like a small size *could* be misread if the tag matches, but actual guest input and resulting pixels have not been demonstrated. More likely another legal no-size form may simply be rejected; both demand ABI evidence.
- [`vulkan_rasterizer.cpp`](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/22b69d6053db41b74edac2633c012f925b84f69e/encore-active/eden-vulkan/vulkan_rasterizer.cpp): physical mapping snapshots are captured and matched again after staging and at native dispatch commit. These anti-remap protections must remain intact.

**O10 — potential CPU optimization, not yet a measured bottleneck:** `NativeQmdContiguousGpuSpan` checks every 4 KiB boundary and the final byte, up to 256 MiB. One contiguous aligned **32 MiB** buffer causes **8,193 mapping lookups** under the current algorithm. The real successful native dispatch call graph performs **six full-span checks** on each CBUF/SSBO (`NativeQmdPhysicalBufferSnapshot::Capture`, two `ConfigureNative::ValidateGpuBufferMappings`, one `StageVulkanBufferBindings` preflight, and two `Snapshot::Matches` checks). For a single aligned 32 MiB SSBO, these account for **at least 49,158 map lookups** before additional endpoint probes and Vulkan work. This was checked against the pinned source owners, not benchmarked on a PS5. The algorithm is intentionally conservative; never remove its safety scans without a proven equivalent process-epoch/revision guard. First instrument per-dispatch lookup counts and timings under live PS5 NS2 sessions.

**Added source-linked witness:** [`research/ns2/check_native_qmd_owners.py`](../research/ns2/check_native_qmd_owners.py) extracts the exact native mapped-span C++ function from the pinned vendor and compiles it with synthetic maps under Clang and GCC UBSan. The pinned native mapping body and native known-size expression were reproduced in an isolated C++ fixture and **24/24 assertions passed with each of Clang and GCC under UBSan**; the repository script itself has not yet run against a complete pinned vendor checkout or GitHub CI. No PS5 performance claim.

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

**O1 — high: native QMD3 unknown-size descriptor admission.**  
[Lichii's native bare-pointer implementation](https://github.com/zortos293/Lichii/commit/e8be28e5d6a7) distinguishes native read-only buffers, whose adjacent word may not describe a size. Encore's **native** [`NativeQmdResourcePlan`](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/22b69d6053db41b74edac2633c012f925b84f69e/encore-active/ns2-runtime/ampere/shader_recompiler/frontend/ampere/native_qmd_compute_environment.h) reads four 32-bit descriptor words and currently admits `tag == 0 && bytes != 0`; unknown-size records are rejected. This is a verified compatibility-policy difference, **not** proof of incorrect PS5 pixels or an 8 MiB native clamp. **Next:** obtain authentic QMD3 ABI evidence of a legal native bare/unknown-size descriptor, prove shader access direction and bounded GMMU span, and only then propose native-only read admission; preserve write/fence/epoch checks.
**O2 — high: GPU-memory destruction/re-registration and stale cached SMMU backing.**  
[Lichii destruction/unmap commit](https://github.com/zortos293/Lichii/commit/bcb37c49f75b) and [reused device-range refresh](https://github.com/zortos293/Lichii/commit/9d90f25bfe29) address mappings that survive destruction of a CPU-backed region and later reuse old host pages at the same address. Encore already has maintained `encore-active/ns2-runtime/gpu_session/core/hle/service/am/service/gpu_worker.cpp` owners for commands 101/102/211–216, plus `encore-active/ns2-runtime/nvdrv_as/core/hle/service/nvdrv/devices/nvhost_as_gpu.cpp`; do **not** infer that 102 cleanup is absent. The named upstream `ReleaseBacking` mechanism was not found in the indexed pinned vendor, which is **not proof** of missing equivalent behavior. **Next:** source-trace 101→211→102→remap into new pages, multiple GPU aliases, partial overlaps, in-flight fences, and allocator-generation ownership. Require an executable hostile-reuse test before any modification.

**O3 — high: distinguish genuine length fields from data words.**  
[Eglantine-PS5's descriptor-size case](https://github.com/viejunerd/Eglantine-PS5-/commit/15cde68e7ef1) highlights risks of treating adjacent data as a length. Encore's **legacy** `StorageBufferBinding` uses a low-word size heuristic, but native QMD3 takes `record[2]` as bytes **only if** `record[3] == 0` and the length is nonzero. Consequently the current native rule would accept a plausible-looking **266-byte** length with tag zero; whether that record is ever a genuine bare pointer is unproven. **Next:** verify the descriptor ABI, reject forged/malformed records, and distinguish read-only native pointers from writable SSBOs. Do not modify legacy NS1 merely to resolve native hypotheses.
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
2. [Shared `BufferCache::StorageBufferBinding`](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/22b69d6053db41b74edac2633c012f925b84f69e/encore-active/eden-core/src/video_core/buffer_cache/buffer_cache.h) reads `ssbo_addr+8` and takes its low 32 bits as length when high bits are zero, the value nonzero, and it fits `GetMemoryLayoutSize`; otherwise it uses `min(layout, 8 MiB)`. This source fact is reproduced in the test as `CurrentVendorSizeHeuristic`. In the **legacy** function, a hypothetical native bare pointer followed by `266` would become a **266-byte binding** under the heuristic, and a non-size word with nonzero high bits falls back to **8 MiB**. **The native QMD3 path does not use this function** and must instead be assessed through its four-word `known_size` gate. Neither scenario proves a PS5 symptom.
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

### Offline source-witness status (10 Nov)

The research source-bound validator now also checks the six-pass call graph, extracts the real `tag == 0 && bytes != 0` expression, and refuses to run against an unrecognized vendor SHA. A small local compilation using the inspected native GMMU function body and size expression passed **24/24 assertions on Clang and GCC, UBSan**. The **exact repository script** was not run end-to-end against a real pinned vendor checkout in this environment. Do not misinterpret these results as proof of native gameplay, benchmark wins, or CI success.

Local `run_host_checks.sh` successfully repeated the two standalone model suites: **19 + 23** assertions with Clang and GCC, but reported `SKIP` for the exact-source validator because the vendor checkout was unavailable locally. This skip is a real validation gap.


## O10 — safe cache gate: real owner constraint (10 November)

A candidate 16-slot, process-generation-and-revision-keyed GMMU span memo
has been implemented only in [research/ns2/test_epoch_guarded_gmmu_memo.cpp](../research/ns2/test_epoch_guarded_gmmu_memo.cpp).
Its 30 C++ assertions pass on Clang 17 and GCC 14 with UBSan.
For six unchanged 32 MiB spans **under one explicit shared mapping lease**
the model uses 8,193 translations instead of 49,158.
That is a deterministic **83.3% fewer calls in the model**, NOT PS5 throughput.

**Production blocker, confirmed by maintained source:**
[`MemoryManager::GpuToCpuAddress`](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/22b69d6053db41b74edac2633c012f925b84f69e/encore-active/eden-core/src/video_core/memory_manager.cpp)
reads the mapped GPU PTEs directly, with no read lease exposed to
`ComputePipeline::ConfigureNative` across capture/staging/fence commit.
The already-maintained global page-table revision invalidates the
`MaxContinuousRange` thread cache, but **is not equivalent** to a read
lease covering a Vulkan dispatch. Its pre/post mutation increments alone
do not authenticate an uninterrupted interval when multiple writers
may overlap. Therefore **no change to active memory cache, renderer or
vendor is authorized based on the model**. Next technical prerequisite:
design and prove a short-lived mapping owner/snapshot protocol that
keeps writer/remap ownership correct and never holds a page-table lock
across scheduler/driver waits. Measure actual PS5 scan times before
assuming the CPU cost affects framerate.

**Current offline execution:** the single host runner passes **19 + 23 + 30
= 72 distinct assertions on each of Clang and GCC**, while the exact
vendor source validator reports **SKIP** without a real pinned checkout.

### O5 — pipeline miss-cache crossover

Encore's pinned native Vulkan pipeline owner already keeps a **12-entry positive Ampere Compute LRU**, keyed by process and channel generation and exact SPIR-V words, in [`vk_pipeline_cache_cost.cpp`](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/22b69d6053db41b74edac2633c012f925b84f69e/encore-active/eden-vulkan/vk_pipeline_cache_cost.cpp). The same maintained file uses a generation-aware negative lookup memo for *attributeless graphics shader detection*, and a 64-key delayed graphics-pipeline retry gate exists in its header. These existing mechanisms are not equivalent to caching failed **native** compute pipeline creation.

Do **not** blindly import nxnative's negative archive lookup memo into native compute pipeline creation: a failure there can be transient (pipeline build, guest generation, driver state, OOM). Measure repeat identical failures by exact shader/process/driver/epoch and validate all invalidation epochs before adding a negative cache. Native positive pipeline reuse is already present, so O5 is now **investigate-only**, not an easy missing optimization.

### O11 — Vulkan maximum storage-buffer range preflight (requires device check)

The shared Vulkan [`Device::GetMaxStorageBufferRange()`](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/22b69d6053db41b74edac2633c012f925b84f69e/encore-active/eden-vulkan/include/video_core/vulkan_common/vulkan_device.h) exposes the runtime `maxStorageBufferRange`. The native QMD3 `NativeQmdContiguousGpuSpan` separately admits up to **256 MiB** of contiguous guest memory, while the current [`ConfigureNative`](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/22b69d6053db41b74edac2633c012f925b84f69e/encore-active/eden-vulkan/vk_compute_pipeline_cost.cpp) and [`UpdateDescriptorQueue::AddBuffer`](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/22b69d6053db41b74edac2633c012f925b84f69e/encore-active/eden-vulkan/include/video_core/renderer_vulkan/vk_update_descriptor.h) carry the raw guest byte length into a Vulkan storage descriptor without a *visible explicit* comparison to that device limit at those call sites. This is a **potential gap in admission** if a real PS5 Vulkan device advertises a lower maximum; do not claim a validation error without the device's queried limit and the complete downstream binding audit.

Proposed native-only evidence: capture the real `maxStorageBufferRange`, test equal-to-limit, just-above-limit, different base/offset alignment and correctly rejected buffer writes. A silently truncated buffer is not a correct alternative to refusing a genuinely unsupported shader access. No code change until a failing exact-owner/device test exists.


### Exact source equivalence check (local harness ↔ pinned vendor)

The previously executed 24-case host harness was checked against the fetched
`NativeQmdContiguousGpuSpan` body in pinned vendor `22b69d60` rather than
assumed equivalent. Removing C++ comments and whitespace from both function
bodies yields the same normalized **460-byte code**, with matching FNV-1a
fingerprint `1556815272`. The local normalized source has SHA-256
`90c871905ad8c6d5a193acea84a457816cf1bc432d71c06de6f6ab68e0f9b7a2`.
The native `known_size = tag == 0 && bytes != 0` condition also matches
(normalized FNV-1a `4224985686`). The research script now pins the
normalized guard SHA-256 in addition to the vendor commit SHA, so later
code drift requires a new audit. This strengthens **host-only source
equivalence**; it is not an actual Vulkan/PS5 dispatch.

### O11 — local positive/negative contract now implemented (research-only)

Created [`research/ns2/native_vk_range_contract.hpp`](../research/ns2/native_vk_range_contract.hpp)
and [`test_native_vk_range_contract.cpp`](../research/ns2/test_native_vk_range_contract.cpp).
**33/33 positive and negative tests on each Clang 17 and GCC 14 with UBSan.**
The two-stage policy checks, before expensive GMMU staging, guest 49-bit
range, current QMD3 256 MiB policy, actual supplied Vulkan uniform/storage
range limits, and the QMD3 64 KiB uniform cap. After `ObtainBuffer`, it
checks the real offset against device alignment, the allocated backing
length, and descriptor-buffer address overflow. It never clips an SSBO
to a shorter length, which would silently change shader behavior.

The *actual* PS5 Vulkan `maxStorageBufferRange`, `maxUniformBufferRange`
and alignment must be read from `Device::GetPhysical().GetProperties().limits`
before promoting this into the real native Vulkan owner. The currently
maintained `Device::GetMaxStorageBufferRange()` is also available.
On adoption, stage all resources only after complete preflight and
retain every current QMD3/GMMU/snapshot/write/fence barrier. No vendor
or `main` changes have been made.

**Updated local runner:** 19 + 23 + 30 + 33 = **105 distinct research
assertions per compiler, 210 across Clang/GCC**, plus a separate
24-case source-expression reproduction per compiler. See
[local test receipt](../research/ns2/LOCAL_TEST_RECEIPT_2026-11-10.md).

### O11 priority correction — the packaged PS5 renderer uses RADV

Source-verified on the current Encore main:
[`tools/build-package.sh`](https://github.com/niakw/ProsperoEden-Encore/blob/main/tools/build-package.sh)
explicitly exports `EDEN_PS5_VULKAN=ON EDEN_VULKAN_DRIVER=RADV`.
The pinned maintained [RADV physical device](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/22b69d6053db41b74edac2633c012f925b84f69e/encore-active/ps5-mesa/src/amd/vulkan/radv_physical_device.c)
advertises `maxStorageBufferRange=UINT32_MAX` and
`maxUniformBufferRange=UINT32_MAX`. Meanwhile the *different* source
[PS5VK physical device](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/22b69d6053db41b74edac2633c012f925b84f69e/sources/ps5-vulkan-tools/driver/ps5vk_physical_device.c)
has `maxStorageBufferRange=128 MiB` and `maxUniformBufferRange=16 KiB`.
PS5VK **is not the selected main-package driver**. A hypothetical 128 MiB
driver/storage conflict does **not** substantiate an issue on today's
packaged Encore RADV path; de-prioritize O11 to preventive robustness,
not confirmed correctness/performance regression.

The 33-case range contract now checks both source-advertised profiles.
Even so, the PS5 runtime's effective reported limits have not been
queried on-console, and an actual `ConfigureNative`+RADV test has not
been executed. The original QMD3 256 MiB GMMU admission cap remains.
