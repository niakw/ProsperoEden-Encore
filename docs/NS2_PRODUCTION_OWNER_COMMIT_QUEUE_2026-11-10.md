# NS2 production-owner commit queue — implementation and qualification


## Latest R2 production-owner milestone — verified *in-call* contiguous-region fusion (11 November 2026)

**Vendor draft PR #38: 21 commits, HEAD [`0dc6c724`](https://github.com/niakw/Prospero.Eden-Encore-vendor/commit/0dc6c724c794b7dad04c6995c02e3550fa114117).** [`e86e4e28`](https://github.com/niakw/Prospero.Eden-Encore-vendor/commit/e86e4e283eb6cdf602b4eca82ed077e98e718062) adds an actual bounded `StagingRegionCoalescer<64>` in the maintained R2-only `BufferCacheRuntime::CopyStagingUpload`: sequential copies within the *same existing command* can collapse into one region **only when source and destination offsets are both contiguous**, combined physical-memory backing is proved, and the merged span is in bounds. No buffer handles, GPU queue, barrier conditions or command order are changed; failed admission/full capacity preserves the original copy array. [`74ebd925`](https://github.com/niakw/Prospero.Eden-Encore-vendor/commit/74ebd9258926e90cca38d5bb5d2b0924505daeb8) restores the original 0/1-region fast path without constructing the 64-entry accumulator. Source-derived proof fixture [`0dc6c724`](https://github.com/niakw/Prospero.Eden-Encore-vendor/commit/0dc6c724c794b7dad04c6995c02e3550fa114117) mirrors the existing zero-size filtering; [`53f3c64c`](https://github.com/niakw/Prospero.Eden-Encore-vendor/commit/53f3c64cb8561f0e844f5ece864e91dfad0dc994) adds 64 deterministic CPU byte-equivalence scenarios.

**Exact successful tests:** [vendor host CI #42939907061](https://github.com/niakw/Prospero.Eden-Encore-vendor/actions/runs/42939907061) **PASS**: 282 admission/alias/epoch/fusion assertions in each of six C++20 Clang/GCC O0/O1/O2 ASan+UBSan variants (1,692 test assertions), and 37 source-derived Scheduler/Staging/CopyStagingUpload checks in each of four Clang/GCC O0/O2 ASan+UBSan variants (148). Total **1,840 executed host assertions**, not 1,840 independent GPU tests. The real runtime method is compiled into a bounded mock owner shell, **not** the full Vulkan include graph.

**Encore R2 branch pin [`20109792`](https://github.com/niakw/ProsperoEden-Encore/commit/2010979296e775998cda503024a246ff3eb4419a)** references exactly vendor `0dc6c724` and keeps the native `EDEN_RESEARCH_NS2_STAGE_BACKING` flag **OFF by default**. [CMake selection CI #42940137606](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42940137606) **PASS 9/9**; [strict vendor/Vulkan source parity CI #42940137601](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42940137601) **PASS**, with branch-only exact SHA normalization. `main` vendor gitlink remains `90c9c8a2`.

**Safety/qualification boundary:** This optimization fuses **regions within one `vkCmdCopyBuffer`**, NOT multiple Vulkan commands, barriers, submissions, or host staging allocations. The original `barrier=true` remains at both mapped upload sites. Do not claim improved FPS or actual PS5 GPU qualification. The official [Vulkan copy-command usage rules](https://docs.vulkan.org/refpages/latest/refpages/source/vkCmdCopyBuffer.html) additionally prohibit union source-vs-destination memory overlap and repeated destination writes **across all regions in one command**. The current R2 check verifies individual regions and the span of each proposed fusion; a full union-wide cross-region validation still needs explicit proof before accepting *general* cross-command batches. Also missing: authenticated NS2 channel/queue identity, real Buffer+Staging GPU-retirement leases, scheduler flush at all interleavings/errors, native full include-graph build and NS1/PS5 console benchmarking.

**Remaining qualification tracks:** R2 cross-command batching and GPU lifetime **OPEN**; R3 engine/native/console validation **OPEN**; R4 native GPU/console validation **OPEN**. **3 tracks open / 3.** Keep all PRs draft; no merge, production PS5 build, release or main pointer change.



## LATEST R2 checkpoint — active scheduler chunk rollover (supersedes earlier R2 status)

**Source commit:** vendor [`e74c7175`](https://github.com/niakw/Prospero.Eden-Encore-vendor/commit/e74c7175ce868d8e687c456a5150209dd9018c76) adds a **real guarded `vulkan_scheduler.cpp::DispatchWork` generation increment** on every nonempty command-chunk transfer to the worker. Maintained `vk_scheduler.h` snapshots and checks that generation together with recording serial, submission tick and renderpass/deferred-clear ownership. A work-queue rollover invalidates stale recording tickets even without a new `Record()` command. No executable R2 copy batch was introduced.

**Final isolated Encore R2 branch:** [`fd94caf1`](https://github.com/niakw/ProsperoEden-Encore/commit/fd94caf17fba560a636f5ea7e20a520b1f424bb5), research vendor gitlink `e74c7175`. [Source-paired CMake CI #42936346549](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42936346549) **PASS (9/9)**; [strict vendor/Vulkan oracle CI #42936512141](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42936512141) **PASS**. Early research-only parity normalizer removes precisely two header R2 additions and one scheduler TU addition before applying historical N72/P04 source receipts; original production baseline is not relaxed.

**Host test evidence:** [vendor CI #42936094837](https://github.com/niakw/Prospero.Eden-Encore-vendor/actions/runs/42936094837) **PASS**, 128 bounded upload/alias/epoch cases × six compiler/optimization/sanitizer variants = **768**, plus 23 exact-method host cases × four Clang/GCC O0/O2 ASan+UBSan binaries = **92**. These source-derived method tests compile the real extracted `DispatchWork`, staging `Request` and scheduler recording-snapshot bodies in host doubles; they are **not** complete actual Vulkan source-graph or PS5 compiles. [Vendor quality #42936094772](https://github.com/niakw/Prospero.Eden-Encore-vendor/actions/runs/42936094772) **PASS**.

**Current counters:** R2 draft vendor PR #38 has **15 commits**, four real R2 runtime/cache/scheduler owner files from prior stages now augmented by the active scheduler `.cpp` and two maintained staging owner files. **3/3 R2/R3/R4 runtime/console qualification tracks remain open.** Remaining R2 work includes authenticated guest channel/queue generations, true owner lease/retirement across command-buffer submit and ring reuse, a safe cross-command append/flush execution path with genuine Vulkan barriers (including renderpass/tick/error), then native full-graph compile and PS5/NS1 correctness and throughput. **No batching, no merge, no production PS5 build.** This checkpoint supersedes historical statements below that `vulkan_scheduler.cpp` is untouched.



## R2 scheduler/staging request epoch — verified research checkpoint (11 Nov)

**Code commits:** [vendor `29d283b3`](https://github.com/niakw/Prospero.Eden-Encore-vendor/commit/29d283b3d1c48c5bd561b5d3f62e5b1ff00755ec) adds request generation/submission tick to the maintained staging owner and an actual `vk_scheduler.h` recording snapshot, plus fail-closed fallback to the original ordered `CopyBuffer` when the request context has changed. [Vendor `d11ace99`](https://github.com/niakw/Prospero.Eden-Encore-vendor/commit/d11ace9922585e8a6c878c47a2cfa263cc4ca6c8) creates the exact-method host compiler test. [Vendor `0700cab1`](https://github.com/niakw/Prospero.Eden-Encore-vendor/commit/0700cab1cf17eb9528dc59642c448d7acbeb0222) asserts both production typed upload call sites still request their barriers and the PS5 upload reordering path continues to require `!barrier`.

**Final research-only Encore pin:** [`ad157030`](https://github.com/niakw/ProsperoEden-Encore/commit/ad157030626a772d579cc8c19575bd6fbf4c5ec5). Historical vendor oracle now normalizes the exact additional scheduler method *before* N73/P04 MSAA SHA comparison and still rejects all other source differences. The normalizer fixes and ref pin are ONLY on the R2 branch.

**Verified host CI:**
- [Vendor #42935241845](https://github.com/niakw/Prospero.Eden-Encore-vendor/actions/runs/42935241845) **PASS**: 128 actual admission checks × six Clang/GCC optimizer+ASan/UBSan binaries (**768**), plus 15 source-derived scheduler/staging `Request` epoch cases × four binaries (**60**). The source-derived test compiles copied exact method bodies inside mock ownership shells; it is NOT a full native Vulkan translation-unit compile.
- [Encore CMake #42935383810](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42935383810) **PASS 9/9** source-selection gates, matching research vendor SHA.
- [Encore vendor verifier #42935383816](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42935383816) **PASS** with SHA-locked additive inventory and historical generated/native Vulkan parity. [Vendor Security & Quality #42935241840](https://github.com/niakw/Prospero.Eden-Encore-vendor/actions/runs/42935241840) source checks also run on this revision.

**What remains genuinely open:** Cross-command upload batching is **NOT enabled**. Both typed callers pass `barrier=true`, whereas PS5's old reordered upload queue only accepts `!barrier`. A future patch must explicitly prove which command groups can omit/interleave barriers, propagate authenticated native channel/queue generations, retain strong Buffer/staging owners until the real GPU retirement fence, and flush every pending group at record/renderpass/tick/submit/exception/allocator-reuse boundaries. `vulkan_scheduler.cpp` batch dispatch is still untouched. No full Encore include-graph native compile, no console NS1 regression, no PS5 pixels/benchmark, no release or merge.

**Counts:** vendor R2 draft **14 research commits** through `0700cab1`, 4 core/runtime/scheduler source-owner files now have R2 code, plus staging pool source/header. R2/R3/R4 remain **3/3 runtime/console qualification tracks open**. The final number of source edits for batching is not yet established, but at least scheduler dispatch and resource retirement owners remain.


## Latest R2 source-owner implementation — 11 November 2026

**Research-only commits pushed, not merged:** vendor [`e03b6ccf`](https://github.com/niakw/Prospero.Eden-Encore-vendor/commit/e03b6ccf61278a549ffe6f02381effc5c2ea03f2) on [draft PR #38](https://github.com/niakw/Prospero.Eden-Encore-vendor/pull/38), and Encore CMake/vendor-gitlink [`52b35aad`](https://github.com/niakw/ProsperoEden-Encore/commit/52b35aad55a22a2ff4c1afeec980924f245230dc) on the independent R2 branch. Follow-up CI-only inventory guard [`de70dacb`](https://github.com/niakw/ProsperoEden-Encore/commit/de70dacb3df9c10dffc571b1da6eda74780de9dc) is intentionally limited to that research branch.

- R2 now touches **three real source-owner files** in vendor: generic `buffer_cache.h` (both upload call sites), Vulkan `vk_buffer_cache.h` and `vk_buffer_cache_cost.cpp`; a pure C++ range helper and exact host fixture make five files total.
- Under **`PS5_NATIVE && EDEN_RESEARCH_NS2_STAGE_BACKING`**, a typed `CopyStagingUpload(Buffer&,StagingBufferRef&, ...)` path verifies source/destination logical bounds, mapped region, physical binding offsets and same-VkDeviceMemory alias before delegating to the **unchanged** `CopyBuffer` path. All legacy paths and their upload queue/barrier semantics remain intact. This is **not** actual multi-command batching and proves no memory retirement lease.
- [Vendor source CI #42931416245](https://github.com/niakw/Prospero.Eden-Encore-vendor/actions/runs/42931416245) **PASS**, 120 host assertions × six Clang/GCC O0/O1/O2 ASan/UBSan variants = **720 checks** (including 10 additional typed-bounds checks). [Vendor quality CI #42931416214](https://github.com/niakw/Prospero.Eden-Encore-vendor/actions/runs/42931416214) PASS. Neither compiles the full real Vulkan runtime.
- [Encore R2 CMake CI #42931693349](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42931693349) **PASS, 9/9** source selection/admission cases. Only the R2 branch pins vendor `e03b6ccf`; OFF remains default, and ON sets the matching C++ gate.
- The ordinary Encore vendor verifier initially rejected the five *new research-only* additive paths. Its [first run #42931693456](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42931693456) is **red** for this inventoried difference; a branch/pin/SHA-exact normalizer was corrected in [`acbe0ccf`](https://github.com/niakw/ProsperoEden-Encore/commit/acbe0ccfc4d34b612caadda4914f763eb8a7d5d8). Final [Encore vendor verifier #42932624802](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42932624802) **PASS**: all maintained Vulkan owners and the exact research-only additive manifest are accepted without changing the production 238-path allowlist.
- **Remaining R2 source owner**: the Vulkan Scheduler (header and potentially implementation), plus genuine buffer/staging lifetime leases and retirement/flush/barrier proofs; actual batching is still **not implemented**. This is **one known untouched owner area, potentially 2+ source files**, *not* a claim of only one final edit.
- R3 and R4 remain unchanged: no full native owner compile, PS5 measurements, NS1 console regression or merge. The production Encore `main` gitlink remains `90c9c8a2`.


## Latest verified host CI — 11 November 2026

| Candidate | New real-source proof | Integration remaining |
| --- | --- | --- |
| **R2** | [Vendor CI #42924901299](https://github.com/niakw/Prospero.Eden-Encore-vendor/actions/runs/42924901299) **PASS**: exact bounded-upload header, **110 checks × 6 Clang/GCC O0/O1/O2 ASan/UBSan = 660 checks**; rejects shared VkDeviceMemory aliases even with distinct VMA allocation IDs | **4+ production-owner source files**, then real Vulkan/PS5 and NS1 tests |
| **R3** | [Encore CI #42925529798](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42925529798) **PASS**: pinned exact R3 code vendor gitlink on *research branch only*, 7/7 CMake owner gates. [Vendor CI #42926795620](https://github.com/niakw/Prospero.Eden-Encore-vendor/actions/runs/42926795620) **PASS**: complete real old/new decoder C++ translation units linked against real public API, **1280 full textures + 96 subrectangles per run**, Clang/GCC O1/O2 and ASan/UBSan, identical digest `7430280414279798289` | **0 CMake source files**; full engine/console compile and NS1/PS5 benchmarks still open |
| **R4** | [Vendor PR #36](https://github.com/niakw/Prospero.Eden-Encore-vendor/pull/36) retains guarded source-owner implementation, but only previous 50-case policy-model tests | **0 new known integration files**; actual maintained-source compile, image-copy readback, NS1/PS5 tests open |

**COUNT: 3/3 research tracks have real source commits; 3/3 still await runtime/console qualification; 4+ R2 production source files remain to be wired.** R2/R3 host CI no longer counted as pending. Do not count the R3 minimal-header host compiler check as a full PS5 or NS1 console validation.

**Important pin distinction:** on branch `research/ns2-r3-gob16-cmake-selection-20261110` only, the `vendor` gitlink is deliberately pinned to R3 *code-bearing* commit `7389c327`; newer vendor PR #37 commits only add targeted tests/workflow. **Encore `main` vendor remains `90c9c8a2`.** No main/release/native-build changes. All vendor PRs #36/#37/#38 remain drafts.

---

## LIVE CHECKPOINT — R3 wired in isolated Encore branch; R2 exact header compiled

| Item | Implementation / proof | Unclosed owner files |
| --- | --- | ---: |
| **R4** | [Vendor PR #36](https://github.com/niakw/Prospero.Eden-Encore-vendor/pull/36) source reconciled with live native pin parity | 0 additional known; actual native compile + GPU/NS1 tests pending |
| **R3** | [Vendor PR #37](https://github.com/niakw/Prospero.Eden-Encore-vendor/pull/37) decoder source plus separate Encore branch [`research/ns2-r3-gob16-cmake-selection-20261110`](https://github.com/niakw/ProsperoEden-Encore/tree/research/ns2-r3-gob16-cmake-selection-20261110) containing CMake selection + host gate | **0** CMake integration files left to prepare; real decoder compile/NS1 parity pending |
| **R2** | [Vendor PR #38](https://github.com/niakw/Prospero.Eden-Encore-vendor/pull/38) helper compiled from **exact GitHub bytes** (7578 chars/FNV32 `3110636912`) on Clang17/GCC14; [104-check host fixture](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/research/ns2-r2-verified-upload-batching-20261110/encore-active/eden-vulkan/tests/test_ns2_verified_upload_batch.cpp) passes 6 compiler/optimization ASan+UBSan runs, 624 checks | **At least 2:** buffer runtime + Vulkan scheduler, possibly additional allocation owner/provenance files |

**COUNT: 3/3 tracks have source commits, 3/3 tracks still need true runtime qualification, and at least 2 R2 integration owner files remain.** Test files are counted separately from integration files.

### R3 CMake host evidence

Encore isolated CMake commit `eb864b61` selects the exact maintained `decoders.cpp` only if `EDEN_RESEARCH_NS2_GOB16=ON`, native PS5 Vulkan, source exists, original pinned TU remains located and the candidate is not already present. OFF is the default. A **7-case mini CMake target** using the exact GitHub CMake block (1369 characters, FNV32 `2313840989`) passes: OFF, missing decoder, wrong platform, no Vulkan, valid selection, changed original, and duplicate decoder. Reproducible source test committed as [`tools/ns2/check_gob16_cmake_selection_host.py`](https://github.com/niakw/ProsperoEden-Encore/blob/research/ns2-r3-gob16-cmake-selection-20261110/tools/ns2/check_gob16_cmake_selection_host.py), local bytes = 4431 characters, FNV32 `1053993644`. **Not a full Encore CMake configure with vendor #37 pinned; no PS5/native build.**

R3 selection branch intentionally has no PR yet because PRs changing `headless/**` trigger the expensive CodeQL pull-request analysis. No vendor gitlink or main changes were made. To qualify actual decoder build, use a temporary worktree with vendor #37 pinned, only after owner review; do not touch the running P5 build.

### R2 source-owner limitation

The existing `BufferCacheRuntime::CopyBuffer(VkBuffer,VkBuffer,std::span<BufferCopy>,...)` accepts raw Vulkan handles and has no authenticated backing allocation ID / buffer size / native queue generation at that API boundary. The standalone R2 helper correctly rejects missing provenance; **do not wire it by manufacturing IDs from a handle or GPU address**. R2 remaining files may increase when the true allocation owner is identified. Keep upload barrier, `RecordWithUploadBuffer`, renderpass rollover, tick submission, CPU/GPU alias and NS1 ordering unchanged until an actual-source test can prove the batch-safe scheduling contract.

---

## LIVE UPDATE — R2/R3/R4 source branches (supersedes historical entries below)

| Point | Source committed | Remaining source integration | Validation |
| --- | --- | --- | --- |
| R4 3D slices | [Vendor PR #36](https://github.com/niakw/Prospero.Eden-Encore-vendor/pull/36), current main parity restored | 0 new source files; existing active file must compile | Not done on actual owner / PS5 |
| R2 upload batch | [Vendor PR #38](https://github.com/niakw/Prospero.Eden-Encore-vendor/pull/38), bounded 64-copy, epoch/owner-aware helper | **2 files identified:** scheduler header and buffer-copy runtime; allocation provenance may require more | Helper not wired or compiled against true owner |
| R3 GOB16 | [Vendor PR #37](https://github.com/niakw/Prospero.Eden-Encore-vendor/pull/37), complete maintained decoder with 32-entry table | **1 file identified:** Encore native CMake translation-unit selection | Maintained source not yet selected/compiled |

**COUNT: 3/3 code tracks have real isolated source commits; 3/3 still require actual source/runtime qualification; at least 3 integration files remain (2 R2 + 1 R3).** Counts do not include future test fixtures or additional allocation-owner changes.

Old [vendor PR #35](https://github.com/niakw/Prospero.Eden-Encore-vendor/pull/35) was closed without merge after an unrelated pin-parity change conflicted in the R4 source file. Its replacement **#36** preserves that new Vulkan/OpenGL pin-parity code and is mergeable. The current vendor `main` and Encore `main` gitlink are `90c9c8a203a27181e23349a889a8f2a7d1cd9dd2`; **no main, pins, releases or PS5 builds changed**.

**The sections below document the historical first R4 draft and original R2/R3 plan; use this live update for current PR numbers and progress.**

---

**Updated:** 2026-11-10. Source audit is CLOSED for the frozen upstream snapshot; this document tracks **code preparation**, which is NOT complete.

## Commit 1 — R4 native Fermi2D 3D volume slice copy

**Actual active vendor source committed, not merely a model.**

- Branch: [`research/ns2-r4-safe-volume-slice-20261110`](https://github.com/niakw/Prospero.Eden-Encore-vendor/tree/research/ns2-r4-safe-volume-slice-20261110)
- Draft [vendor PR #35](https://github.com/niakw/Prospero.Eden-Encore-vendor/pull/35).
- Only changed active code: `encore-active/eden-vulkan/vulkan-cache/video_core/texture_cache/texture_cache.h`.
- Guards: `PS5_NATIVE`, native graphics-engine process generation ticket, matching active cache/graphics pointer, genuine Fermi2D SrcCopy/Point, complete 3D BlockLinear slice, compatible pixel formats/width/height/depth, distinct cached images and level-zero slice, bounded `gpu_addr` offset, no stale Remapped/Sparse image, pre-copy channel ticket recheck. If any check fails: existing general blit path.
- Uses the maintained `PrepareImage`, `FlushDeferredClear`, `CopyImage`, `ForEachImageInRegionGPU` and cache tracker. No game-ID special cases or new cache owner. NS1 lacks a native graphics ticket and cannot take this path.
- Initial commit `3f0add18`, then source-flag compatibility and owner/dimension hardening `81375105`, `c806e3de`.

**R4 not signed off:** full PS5-native source compile, actual Fermi2D guest command replay, negative Blend/ROP/Bilinear run in real cache, source/destination 3D image Vk handles, overlap/remap/alias and fence retirement, PS5 pixels and NS1 regression all pending. No release or merge permitted. The 50-case host policy fixture in this Encore audit is NOT the same as compiling the active vendor patch.

## Commit 2 — R2 in-order Vulkan upload batching (not yet written)

**Real integration owners verified:**

- `encore-active/eden-vulkan/vk_buffer_cache_cost.cpp::BufferCacheRuntime::CopyBuffer`: two existing paths, an explicitly synchronized in-order `scheduler.Record` path, and a separate `can_reorder_upload` path. The existing zero-copy handling and pre/post Vulkan barriers must be retained.
- `encore-active/eden-vulkan/include/video_core/renderer_vulkan/vk_scheduler.h::RecordWithUploadBuffer`: current command-serial, dispatch chunk rollover, error invalidation and outside-renderpass semantics. The upstream `RecordUpload` API is **not** already present in Encore.

**Next source commit only after:** actual allocation-bound `VkBufferCopy` preflight (no zero/overflow/out-of-buffer); preserve all WAR/RAW/destination-overlap exclusions (max 64); flush pending upload copies on every non-upload recording/command-buffer submission, renderpass transition, tick and exception path; record barriers around the whole batch with correct read/write scopes; real scheduler tick, error injection and NS1 order tests. No assumptions of safe reordered copies.

## Commit 3 — R3 GOB 16-byte block-linear swizzle (not yet written)

**Real source owner verified:** `sources/eden/src/video_core/textures/decoders.cpp`, currently compiled from the pinned Eden source set. Its public API uses normal tiling and includes the BPP cases 1/2/3/4/6/8/12/16. Unlike Lichii's newer signature, the pinned Encore API does not pass a `native_tiling` flag.

**Next source commit only after:** choose an explicit `encore-active` overlay/override CMake source route rather than silently modifying or fork-replacing the pinned upstream `sources/` tree; preserve the full public decoder interface. Compare the actual maintained `SwizzleImpl` and `SwizzleSubrectImpl` owner against a new 16-byte path with the current public API. Admit 16-byte fast full-frame copies and power-of-two BPP subrect runs only; fallback for 3/6/12. Run current decoder API regression vectors on NS1 and NS2, including 3D, partial edge and padding, then measure on PS5.

## Version/race discipline

- Main Encore and its vendor gitlink are owned by the ongoing P5 native build effort. Do **not** change gitlinks, pins, source inventory, PS5 workflows, releases or main branches here.
- R4 vendor draft began at the audit-pinned vendor `22b69d60`. The vendor `main` subsequently advanced to `f9f08786` by one unrelated `encore-active/ns2-astc` edit. No rebase, merge or pin change done here.
- Host-only source audit evidence in [the closeout](NS2_UPSTREAM_REFRESH_AND_CLOSEOUT_2026-11-10.md) does not establish PS5 gameplay or production safety. Treat the vendor PR #35 as an **uncompiled draft**, not a finished feature.

**Status:** frozen upstream source audit complete; **R4 actual source draft created**; R2 and R3 implementation commits pending their real-owner integration/qualification gates; PS5/NS1 and vendor full build validation outstanding.

### R2 owner provenance: precise source boundary (next integration stage)

At vendor main `90c9c8a2`,
`encore-active/eden-core/src/video_core/buffer_cache/buffer_cache.h`
calls `runtime.CopyBuffer(dest_buffer,src_buffer,...)` with strong
`Buffer` owners in some cases, but with a `StagingBufferRef.buffer`
raw handle on uploads/downloads. The existing
`encore-active/eden-vulkan/include/video_core/renderer_vulkan/vk_buffer_cache.h`
exports `CopyBuffer(VkBuffer,VkBuffer,span<BufferCopy>,bool,bool)`,
losing the buffer's `SizeBytes()` and provenance at the Vulkan runtime
boundary. `BufferCacheRuntime::CanReorderUpload(const Buffer&,...)`
only checks destination region usage; it does not authenticate source
VMA allocation IDs or channel generation.

The upcoming R2 work therefore needs **three source ownership levels**:
the BufferCache caller (`buffer_cache.h`) for strong owner and staging
lifetime, the Vulkan runtime (`vk_buffer_cache.h` and
`vk_buffer_cache_cost.cpp`) for typed provenance and range semantics,
and Scheduler (`vk_scheduler.h`, and possibly scheduler implementation)
for command flush/retirement. **Two-file earlier estimate is a lower
bound; a credible implementation likely touches at least four
production source files**, depending on whether an existing owner
adapter can carry the required data. Do not forge owner IDs from
raw VkBuffer bit patterns or assume VMA allocations are unaliased.

Research R2 `ns2_verified_upload_batch.h` has now been compiled from
**byte-identical GitHub content** using Clang17 and GCC14 with UBSan
and -Werror, and its new exact-header host fixture passes
**104 assertions per run across six ASan+UBSan compiler/optimization
runs (624 in total)**. These are not an integrated Vulkan queue proof.
