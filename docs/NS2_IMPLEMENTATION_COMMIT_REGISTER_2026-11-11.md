# NS2 — source commit checkpoint (2026-11-11)


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


## Live counts

| Scope | Done | Still open |
| --- | --- | --- |
| Upstream source audit, fixed 10 Nov snapshot | **Complete** | New upstream changes would be a new audit |
| Isolated implementation branches with real code | **3/3 prepared**: R2, R3, R4 | **3/3 full integration / PS5 + NS1 validation tracks** |
| R2 authentic staging backing/selection | **3 vendor owner files prepared** and **1 Encore CMake owner prepared**, plus host gate | At least **4 production call-chain owners**: BufferCache caller, runtime API, CopyBuffer implementation, Scheduler; possibly more for lifetime/allocator |
| R3 GOB16 source and CMake | Complete maintained source file + isolated CMake replacement | Full native engine build, PS5 performance, NS1 regression |
| R4 Vulkan 3D volume-copy path | Maintained TextureCache owner committed | Actual-source compile, image copy, alias/fence tests, PS5/NS1 |

## Active branches, commits and proofs

**R2:** [vendor draft PR #38](https://github.com/niakw/Prospero.Eden-Encore-vendor/pull/38), head `9f0eed3e` (10 draft commits, 6 changed files). New passive provenance-owner commits:

- `545e3766`: `encore-active/eden-vulkan/include/video_core/renderer_vulkan/vk_buffer_cache.h` adds read-only `Buffer::GetNativeBackingSnapshot()` using the original `vk::Buffer::Location()` and `SizeBytes()`. **Not** a scheduling/lifetime lease.
- `d68f14ae`: paired maintained `vk_staging_buffer_pool.h` adds `PS5_NATIVE`-only physical memory location and actual backing capacity to `StagingBufferRef`, populated from its real `vk::Buffer` in `StagingBuffer::Ref()`.
- `9f0eed3e`: paired maintained `vk_staging_buffer_pool.cpp` populates this metadata for the stream-buffer allocator, without changing copies or submission.

**R2 exact-source host code [CI #42924901299](https://github.com/niakw/Prospero.Eden-Encore-vendor/actions/runs/42924901299): GREEN**, 110 fail-closed alias/range/epoch checks per compiler/optimization binary, 660 successful tests across Clang/GCC O0/O1/O2 ASan/UBSan. The 110 checks exercise the **header-only admission algorithm**, not any submitted Vulkan commands.

**R2 source/CMake research-only branch:** [`research/ns2-r2-stage-backing-cmake-20261111`](https://github.com/niakw/ProsperoEden-Encore/tree/research/ns2-r2-stage-backing-cmake-20261111) on Encore. `c37f30fc` adds `EDEN_RESEARCH_NS2_STAGE_BACKING=OFF` default with paired owner/header selection and explicit removal of the optional overlay header when OFF. `5a4dd5b7` pins vendor `9f0eed3e` on this branch **only**. `40a6b6c2` adds 8-case exact-block CMake host test; `7adac6b3` created host workflow; `7dc8b407` fixed a shell variable typo in the workflow.

**[R2 paired-source CMake CI #42929102514](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42929102514): GREEN, 8/8 cases**, authenticates the three vendor source blob hashes, verifies OFF legacy behavior, ON paired owner selection, and negative cases for missing files, wrong platform and moved original source. First attempt #42928901267 failed due to malformed *workflow* `RUNNER_TEMP` substitution; that was fixed in workflow code, no emulator source was changed. The full staging-owner C++ translation unit has **not** been compiled in a full Encore graph.

**R3:** [vendor draft PR #37](https://github.com/niakw/Prospero.Eden-Encore-vendor/pull/37), maintained `decoders.cpp` GOB16 source. [Vendor CI #42926795620](https://github.com/niakw/Prospero.Eden-Encore-vendor/actions/runs/42926795620): GREEN, compiled both full old/new decoders against the real public API under Clang/GCC O1/O2 ASan/UBSan, 1280 whole textures + 96 subrectangles in each of 4 pairs, exactly identical output digest `7430280414279798289`. [Encore CI #42925529798](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42925529798): GREEN, 7/7 CMake owner-selection tests on separate R3 branch pinning code commit `7389c327`, while `main` stays on `90c9c8a2`.

**R4:** [vendor draft PR #36](https://github.com/niakw/Prospero.Eden-Encore-vendor/pull/36), maintained native NS2 `TextureCache<P>::BlitImage` implementation, source-guarded by native graphics ticket, SrcCopy/Point and valid cached 3D slices. Only source-model qualification (50 host policy cases) at this point; **no actual native owner compile, no GPU pixels, no NS1/PS5 test**.

## Exact completion criteria before closing all implementation work

1. **R2:** authenticate destination `Buffer` and staging ring physical memory **and** lifetime lease, preserve channel and queue generation across the whole batch; implement scheduler flush on every RAW/WAR/WAW/barrier/tick/renderpass/exception/retirement boundary. Compile and test the **actual calling source units**, then NS1 regression and PS5 perf. Do not derive identity by hashing a naked VkBuffer handle or assume different VMA allocation IDs mean disjoint physical memory.
2. **R3:** link maintained decoder into the real, isolated PS5-native build with flag ON; verify public API on main host and regression on NS1/NS2 console; measure GPU/CPU gain. No change to production feature default without proof.
3. **R4:** compile the actual active TextureCache/NativeGpuChannelRegistry path, test real positive 3D slice copies and negative Blend/ROP, mip, remap, alias, fence lifetime cases, then NS1/PS5.

**Safety state:** none of the vendor drafts #36/#37/#38 or Encore audit #44 is merged. The real Encore `main` vendor gitlink remains `90c9c8a203a27181e23349a889a8f2a7d1cd9dd2`. The R2 and R3 vendor gitlink changes exist **only** on their respective Encore research branches. No native PS5 build or release launched by these changes.
