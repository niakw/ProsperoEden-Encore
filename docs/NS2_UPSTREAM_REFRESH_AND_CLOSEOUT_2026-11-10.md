# NS2 upstream optimization audit — refreshed delta and qualification decision (10 November 2026)

> **Scope:** source-level upstream comparison against the maintained pinned Encore vendor `22b69d6053db41b74edac2633c012f925b84f69e` and current Encore `main`. Research PR #44 only; **not a PS5 native build, guest replay, benchmark, production fix, or authorization to merge**. This addendum supersedes stale 10 November upstream branch heads in [the parent audit](NS2_UPSTREAM_OPTIMIZATION_WATCH_2026-11-10.md). The host test receipt is [here](../research/ns2/LOCAL_TEST_RECEIPT_2026-11-10.md).

## Upstream freshness gate

| Upstream / branch | Prior audited SHA | Newly checked head | New content to assess |
| --- | --- | --- | --- |
| [Lichii nx2](https://github.com/zortos293/Lichii/compare/e8be28e5d6a7...879b616b1b377bfd085bf20f440b895cf4b83ab8) | `e8be28e5d6a7` | `879b616b1b377bfd085bf20f440b895cf4b83ab8` | **17 commits**, source/CI/audio/fs/texture/Vulkan deltas |
| [nxnative](https://github.com/seedds/nxnative/compare/a77c0ee8a6b6...ced3612134b9e16b20a866bde990a1092fee7360) | `a77c0ee8a6b6` | `ced3612134b9e16b20a866bde990a1092fee7360` | **2 commits**, Metal MSAA initial content and Vulkan `DONT_CARE` emulation |
| [exploitizm/EglantinePS5](https://github.com/exploitizm/EglantinePS5/compare/d1a8d529ad...1cfb6b57f05f6b9c72539f5b3320dc5f6d3fc9c8) | `d1a8d529ad` | `1cfb6b57f05f6b9c72539f5b3320dc5f6d3fc9c8` | **5 merge commits**, GitHub compare reports **zero changed files** |
| [PS5_Lichii](https://github.com/mihawk-99/PS5_Lichii/tree/549569a2b6f2), [Eglantine-PS5-](https://github.com/viejunerd/Eglantine-PS5-/tree/6243701d6a95), [heydemoura/EglantinePS5](https://github.com/heydemoura/EglantinePS5/tree/095df4eb491b), [Eglantine Community](https://github.com/Eglantine-Community/Eglantine/tree/78743f30c251), [mucahidkambur/EglantinePS5](https://github.com/mucahidkambur/EglantinePS5/tree/dbadad075c), [quatrixone/PS5_Lichii](https://github.com/quatrixone/PS5_Lichii/tree/8e90019d57), [oboromi](https://github.com/0xNikilite/oboromi/tree/c97664a8460e) | Pins in parent audit | **No head change** detected | No fresh comparison required since last audit |

These are frozen snapshots, not a claim that upstream can no longer move. Historical archived Eden-NS2 forks remain historical references, not new live upstreams.

## Complete classification of newly observed source families

| Delta | Evidence from upstream | Encore real-source comparison | Research disposition |
| --- | --- | --- | --- |
| **R1 — Vulkan dispatch barrier proximity** | Lichii [#1246](https://github.com/zortos293/Lichii/commit/7fcfb64123) moves the input barrier into the dispatch command (or retains an early one for effects). | Encore native `vulkan_rasterizer.cpp` **already records a Compute input barrier and post-dispatch write barrier**; its native QMD3 path does not simply omit synchronization. | **Candidate / not duplicate-safe.** Test command-record interleaving, deferred effects, indirect arguments, task→mesh consumers, barriers and timeline ordering. No blind transplant. |
| **R2 — bounded in-order transfer upload batches** | Lichii [#1245](https://github.com/zortos293/Lichii/commit/4d7412ac7e) introduces `UploadBatch`, max 64 copies, read/write overlap and WAR/RAW exclusions, flush on dispatch/submit. | Encore `vk_buffer_cache_cost.cpp::CopyBuffer` already preserves ordering when explicit barriers are required and uses a separate reordered staging path; **no same `RecordUpload` batching owner** was found. | **Potential generic performance candidate, unmeasured.** Requires source-level dependency/overlap, empty-copy, multi-submit and fence-lifetime tests before changing common Vulkan scheduler. |
| **R3 — GOB 16-byte swizzle table** | Lichii [#784](https://github.com/zortos293/Lichii/commit/f5edb3578d) uses per-GOB offsets, whole 16-byte runs and a 260-line oracle test. | Pinned Encore `sources/eden/src/video_core/textures/decoders.cpp` still uses per-element `SwizzleImpl` / `SwizzleSubrectImpl`; no maintained `GobUnitOffsets` equivalent found. | **Generic optimization candidate.** Must pass 1/2/3/4/6/8/12/16 BPP, native/normal tiling, partial rectangles, edges, 3D, mip and NS1 fixtures; PS5 speed must be measured. |
| **R4 — 2D-engine copies between depth slices of cached 3D volumes** | Lichii [#853](https://github.com/zortos293/Lichii/commit/017c82c291) adds `CopyVolumeSlice` and detects compatible 3D cached source/destination slices. | Encore `encore-active/eden-vulkan/vulkan-cache/video_core/texture_cache/texture_cache.h::BlitImage` uses generic `GetBlitImages` and has no equivalent explicit slice owner. | **Potential correctness gap; investigate early.** Needs real Fermi2D command fixture, subresource origin/depth and no-copy/alias negative tests. Generic detection only, no game-ID workaround. |
| **R5 — allocator retry above VMA budget** | Lichii [#959](https://github.com/zortos293/Lichii/commit/80197189dd) retries a failed buffer allocation without WITHIN_BUDGET and records pressure. | Encore active `vulkan_memory_allocator.cpp::CreateBuffer` calls `vk::Check(vmaCreateBuffer(... WITHIN_BUDGET))`; PS5 fixed-memory pressure characteristics differ from integrated phone GPUs. | **Do not port without PS5 memory proof.** Retrying above budget can increase OOM or crash risk; first collect classified allocation failures, actual heap budget, host commit and cache pressure. |
| **R6 — host-audio sysmix callback queue sizing** | Lichii [#850](https://github.com/zortos293/Lichii/commit/fd1dbeccab) adapts the queue to PipeWire/host callback size. | No `SysmixQueueLimit` equivalent found in the pinned Encore overrides; **PipeWire callback width is not a PS5 audio measurement**. | **Conditional audio candidate** on real PS5 callback underruns; no unconditional queue expansion. |
| **R7 — NUP external add-on registration** | Lichii [#1257](https://github.com/zortos293/Lichii/commit/19deebbcf3) handles DLC inside a `NupContainer` through `ManualContentProvider`; [#1258](https://github.com/zortos293/Lichii/commit/142d4c713e) fixes UTF-8 path handling. | **Encore already has a separate active NUP v1 integration:** `headless/nup_v1_native_content.cpp` selects the highest DLC version by title, `nup_v1_native_aoc.cpp` scopes DLC to the caller and supplies RomFS, `nup_v1_aoc_service.cpp` exposes AOC service lookup. The vendor's generic `registered_cache.cpp` does **not** register NUP, but that is **not** proof of missing Encore DLC support. | **Already handled by alternate owner.** Compare title/version/standalone addon fixtures, but **do not** import a second content provider or break NCA/extracted-DLC priority. |
| **R8 — VI2/GSV duplicate service stub cleanup** | Lichii [#1252](https://github.com/zortos293/Lichii/commit/0e0fdbe852) removes duplicated registrations. | Encore has maintained NS2 VI2 / graphics-supervisor service owners. No evidence that the duplicate registration situation still exists in its different service framework. | **Source audit / no blindly applicable patch.** Require exact service resolver conflict before code change. |
| **R9 — DLSS out-of-VRAM warning** | Lichii [#941](https://github.com/zortos293/Lichii/commit/2aa201ac56) accepts an NVIDIA Streamline warning after DLSS output was written. | Encore PS5 uses AMD RADV; neural-rendering experiments and AMD upscalers are **not NVIDIA Streamline**. | **Not applicable** to native PS5 pipeline; do not port NVIDIA return codes. |
| **R10 — settings, kernel teardown, IPS, Qt, CI/archive, MSVC diagnostics** | Remaining Lichii 17-commit batch is source/host/platform/packaging-specific. | Encore PS5 is headless/native ELF, not Lichii desktop Qt/Linux archive; no matching NS2 GPU optimization proven. | **No NS2 core transplant.** Revisit individually only if an equivalent reproducible bug is reported. |
| **R11 — new nxnative MSAA zero-initialization** | [nxnative #1760](https://github.com/seedds/nxnative/commit/01de04fd56) clears *new* multisample color textures that Metal otherwise leaves undefined. | Encore's Vulkan cache and PS5 RADV obey different initialization and MSAA lifetimes; the Metal call must not be copied. | **Correctness oracle only**: test newly allocated MSAA images and intended guest zero-content with Vulkan readback, including array layers and clears. |
| **R12 — nxnative DONT_CARE kept as LOAD on Metal** | [nxnative #1500](https://github.com/seedds/nxnative/commit/ced3612134) maps Vulkan `LOAD_OP_DONT_CARE` to Metal Load for Switch-specific observable behavior. | Vulkan itself does **not** promise preserved contents for DONT_CARE. Encore has a Vulkan renderer, not a Metal translation layer. | **Semantic oracle, not an unconditional Vulkan change.** Reproduction must establish exact guest image/attachment lifetime and observed pixels; forcing LOAD could alter performance and ignore Vulkan-spec undefined contents. |

## Earlier O1–O11 audit: source inspection disposition

| Topic | Source audit | Unclosed validation / reason not to merge code |
| --- | --- | --- |
| **O1/O3 QMD3 size / descriptor ABI** | **Inspected** real four-word CBUF reader and `BuildResourcePlan` with `known_size = tag == 0 && bytes != 0`, separate native vs legacy binding. Host executes exact reader and exact GPU-read callback in artificial environment. | **OPEN / high:** obtain a real legal unknown-size record, provenance, access direction, full GMMU/fence proof; do not widen lengths without it. |
| **O1 read-status race** | **Source-backed conditional hazard:** `ReadNs2GpuShader` prechecks mapping, calls a void `ReadBlock`, then returns true; `ReadBlockImpl` may zero-fill unmapped memory. Artificial remap reproduces true + zeros. | **OPEN / high:** prove actual map/unmap can interleave (or source-prove serialization) and construct an actual-owner checked read without accepting valid zeros as failure. |
| **O2 memory teardown / aliases** | **Inspected** `gpu_worker.cpp` lifetime/pin guards and `nvhost_as_gpu.cpp` owner mutex, `FreeMappingLocked` unmap; no obvious missing upstream explicit-unmap fix. | **No transplant.** Still require hostile real-owner multi-alias/remap tests for regression qualification. |
| **O4/O9 texture budgets/BCn** | Existing `RunGarbageCollector`, `total_used_memory` thresholds, PS5 texture phase timers, BCn 3D slice constraints and upload guards. | **No baseline measurements**, so no global budget rewrite. New R3/R4 are separate, specific candidates. |
| **O5 native pipeline reuse** | Existing 12-entry positive Ampere pipeline LRU keyed by process/channel generation and full SPIR-V; negative caching on other graphics paths. | Do not cache failed native pipeline construction without classifying transient errors and invalidation. |
| **O6 native reports/fences** | `gpu_dispatch/.../puller.cpp` validates native semaphore write sizes (4/16 bytes), mapped GMMU, CPU backing, process ticket; `vk_fence_manager_cost.cpp` retains scheduler tick/fence wait ownership. | Segment and timestamp/oracle behavior still needs real guest report fixtures. |
| **O7 sleep/wakeup** | `eden-threading/.../svc_thread.cpp::SleepThread` has timeout and yield branches, not a missing call. | PS5 wakeup/latency and NS1 comparison missing. |
| **O8 Ampere IADD3/UR/task mesh** | `lower_to_maxwell.h` already handles several `IADD3` variants (including carry) with fail-closed unsupported modes and maps UR values to protected GPR bank; `classify.h` has Ampere op classification. | Do not import oboromi negative predicate unless an exact unsupported encoding incorrectly compiles. Task→mesh GPU-written count ordering still needs real shader/host fixtures. |
| **O10 GMMU 6-pass cost** | Six authenticated checks in successful native QMD3 path; 32 MiB × six full passes implies at least 49,158 translations. Experimental 16-entry lease memo passed host contracts. | **Unsafe to deploy** without actual mapping-read lease across stages, writer exclusion and real PS5 profiling. Keep remap barriers. |
| **O11 Vulkan buffer-range check** | Native-only two-stage range policy modeled and tested; actual packaged Encore driver uses **RADV** with source-advertised `maxStorageBufferRange=UINT32_MAX`, not alternate PS5VK's 128 MiB. | **Preventive, low priority.** Actual console properties and exact-owner tests absent; no known main-build 128 MiB mismatch. |

## Qualification ledger (do not conflate evidence classes)

- **PASS / host research fixtures:** six suites, 19+23+30+33+35+16 = **156 checks per compiler** at O1 under Clang/GCC + UBSan; **312 checks total**. Additional `-O0` and `-O2` matrix: 24 binaries / **624 checks**. Separate exact-source GMMU/size-expression excerpt: 24 checks per compiler. No PS5 execution in these results.
- **PASS / GitHub source comparisons:** pinned vendor source owners individually fetched and source-inspected for the above decisions; updated upstream heads and patch families enumerated here.
- **NOT DONE / pinned-vendor Python source extractor:** `check_native_qmd_owners.py` requires a real `vendor` git checkout at the exact reviewed SHA; the current offline local work directory lacks it, and its runner reports `SKIP`. Source-equivalent local excerpts are **not** a substitute for that end-to-end script.
- **NOT DONE / authentic guest:** no NS2 QMD3 16-byte descriptor trace, shader capture/replay, forced real-owner remap interleave, actual buffer-range properties, PS5 scheduler profile or a new successful game frame.
- **NOT DONE / integration:** no change to active Encore/vendor sources, no vendor research build, no PS5 CI build, no release and no merge. Main and vendor pins remain untouched.

## Closeout decision

**Source-review comparison of the declared pinned upstream set and new head deltas is complete for this snapshot. Overall NS2 optimization implementation and console validation are NOT complete.** Do not close PR #44 as integrated production work or infer NS2 rendering was fixed. Keep it isolated as an auditable register, prioritize real QMD3 descriptor semantics and reader/remap ownership, then R4 3D slice copy and R2 in-order upload batching if real guest evidence identifies symptoms. After evidence, work on a separately reviewed vendor research branch, test true owner source, and only promote fixes into `main` after NS1 regression / PS5 P5 release gates.
## Post-closeout validation — R3 swizzle and pinned native source gates

R3 moved from **unverified candidate** to **host-formula differential
candidate**, without production code. The new
[GOB16 differential suite](../research/ns2/test_blocklinear_gob16_differential.cpp)
passed **1536 layouts**, all 192 format/block/tiling combinations
with 8 geometries each, **23,578,183 address-oracle comparisons** and
whole/subrect output comparisons per run. Clang and GCC passed
`-O0`, `-O1`, `-O2` with ASan/UBSan. Full image copies use 16B
fast path only for BPP16; subrectangle fast path only for power-of-two
BPP. The code is independent model/host-only, not actual vendor decode.

Six pinned vendor file blobs were independently read at exact SHA
`22b69d60` and **26/26 direct source-owner invariants passed**,
with Git object hashes retained in
[pinned source witness](../research/ns2/PINNED_VENDOR_SOURCE_WITNESS_2026-11-10.md).
The full Python vendor-checkout execution still reports **SKIP**.
Live QMD3 guest ABI, real memory remap race, actual PS5 decoder
performance, NS1 regression and source-owner integration remain open.

**Revised R3 next gate:** compile the optimization against *actual*
maintained `decoders.cpp` in an isolated vendor research branch, test
the full current public API and subrect edge cases against the old
implementation, then benchmark on PS5 only after the native build P5
is stable. Do not generalize an NS2 optimization into NS1 while it
is only qualified on a mathematical model.

