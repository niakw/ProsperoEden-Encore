# Eden Encore — fresh A/B baseline audit (NS1 + shared runtime), 10 November 2026

> **Status: read-only source audit / first pass. Not a native build, device validation, or authorization to merge.**
> This is an independent replacement for relying on the old October A/B status table. It is intentionally scoped to NS1 and the complete surrounding PS5 platform/dependency graph. The separate NS2 optimization research PR owns NS2-specific upstream comparisons.

## Immutable audit inputs (R00)

| Input | Pinned state inspected |
|---|---|
| Engine | `niakw/ProsperoEden-Encore` `main` at `e4f6a8253e1f6204a6f99d3b3d29abad1800f4c7` |
| Gitlink | `vendor` at `22b69d6053db41b74edac2633c012f925b84f69e` |
| Audit branch | `audit/ab-ns1-upstream-2026-11-10`, forked from the above engine SHA |
| Legacy roadmap | `docs/ROADMAP_ENCORE_COLLAB_2026-10-25.md` (last title update: 5 Nov) |
| Historical comparison | `docs/INTEGRATION_AUDIT_CPU_GPU_JIT_2026-10-14.md`, `docs/UPSTREAM_GAP_REGISTER_2026-10-14.md`, `docs/EXTERNAL_PS5_EMULATOR_ECOSYSTEM_AUDIT_R438.md` |

The audited `.gitmodules` has **one** submodule (`vendor`), not three. The pinned vendor tree has **26** top-level upstream snapshot families under `sources/` and **18** maintained override/module families under `encore-active/`. These are *repository-family counts*, not 26/18 linked native libraries. `objects/` stores immutable inputs. `sources/encore-overrides/` is a frozen upstream snapshot, not the active override directory. **No vendor gitlink, manifest, source, CMake, build, workflow or release configuration has been edited by this audit.**

## Scope and boundaries

**In:** NS1 CPU A32/A64 and ordinary Dynarmic, HLE/SVC/IPC and scheduler, Maxwell/NVN GPU, shader/texture/buffer caches, RAM and PS5 GPU budgets, Vulkan/RADV/WSI, guest writes and synchronization, RomFS/NSP/NSZ/AoC/mods, audio, input, launcher dependencies, toolchain, provenance, CI/packaging, UI/font/asset codecs, and officially maintained upstream alternatives.

**Outside:** NS2 Ampere/QMD3/compute-specific optimization, NS2 boot milestones H01/H05/G10, firmware/keys, automatic dependency upgrades, enabling optional JIT experiments, CI dispatch, PS5 native builds and main merges. Shared sources touched by NS2 are **in scope only to establish NS1 ownership/parity and regression risk**. R09/FSR/FG rendering is inventoried as a dependency/budget interaction; its dedicated feature work is not duplicated.

**Evidence vocabulary:** `source-selected` = CMake/recipe points at maintained code; `host-verified` = test result bound to exact SHA; `device-verified` = matching real PS5 run and user observation. This snapshot has **no new host/device test result**. Merely existing in `vendor` does not mean linked or enabled.

## A — Re-audit results

| ID | Verified from current pinned inputs | Still open / next proof |
|---|---|---|
| **R00** | This branch is based exactly on the build's engine SHA and gitlink, not the former `dev/ps5-sparse-jit`/feature HEAD. | Any later changes to `main` require a new snapshot and rebase *after* the main build completes. No automatic rebase. |
| **R05** | `headless/CMakeLists.txt` selects maintained Dynarmic source copies, per-core production JIT, threading/kernel, sparse-memory guards, maintained shader and GPU owners. `headless/vulkan.cmake` copies the checked-in `vendor/encore-active/eden-vulkan` fork to generated native compilation inputs. `tools/install-vendored-radv.py` installs a **12-entry** checked-in RADV/WSI/disk-cache override set; immutable original is `vendor/sources/ps5-mesa`. | Derive compiler-command/object/link-map ownership from a successful native build and check shadowed headers/duplicate TUs; CMake selection alone does not establish final binary provenance. |
| **R18** | `tools/deps.json` has **22 dependency items** (archive, files, Git pins). Archive hash fields, Git commit pins and compiler-rt individual hashes are visible. `UPSTREAM.json` pins Eden, Mesa, SDK fork and Vulkan toolchain. Source split `sources/` vs `encore-active/` is confirmed in the pinned vendor README. | Transitive BOM and every embedded binary hash/ABI/license/actual reachability still require complete artifact, link map and license inventory. The 22 manifest entries are not 22 active runtime components. |
| **R23** | Upstream comparisons and changed-file sets were refreshed; see [decision matrix](ENCORE_AB_NS1_UPSTREAM_MATRIX_2026-11-10.md). Search must use source owner + semantic behavior, not commit presence or popularity. | Eden compare returns **300 changed files max**, so not an exhaustive full diff; item-level equivalence and benchmarks remain unproven. |
| **R02** | Current PS5 owner paths are separated across `vendor/encore-active/ps5-mesa`, `vendor/encore-active/eden-vulkan` and launcher code. Swordpdf's older integration patches cannot be imported based on commit title alone. | Check individual competing PS5 fixes against these exact owners and pin ancestry; no direct re-cherry-picks. |
| **R17** | PS5SX2 and `mpereiraesaa/prospero-win` supply *architectural/reference* ideas (frame correlations, thread fairness, atlas/UX) but not a compatible Switch source transplant. Historical R438 observations are not November gameplay proof. | Keep hypotheses only; measure existing PS5 thread-pinning, queue latency and cache hit/miss before a conceptual prototype. |
| **R01** | `headless/frame_metrics.h` includes opt-in per-session counters for composites, real/generated queued frames and successful Present API return. No physical display or guest FPS is asserted. | Real guest cadence, GPU timestamps, full frametimes, input-to-photon latency, audio/HUD freshness and memory peak remain unmeasured on matching hardware. Do not derive from synthetic counters. |

### Native-source ownership / compilation candidates (R05)

| Surface | Proven current source/selector | Important distinction |
|---|---|---|
| Guest CPU | `headless/CMakeLists.txt` and `vendor/encore-active/eden-core/src/dynarmic/` | Ordinary per-core JIT; `EDEN_SHARED_JIT_AVAILABLE=0` and `EDEN_JIT_COMPILE_BATCH_AVAILABLE=0` in native settings; do not resurrect October experimental profiles |
| HLE / threads | `vendor/encore-active/eden-threading/native-hle-overrides.cmake` and `src/core/hle/kernel/` | Shared owner can affect NS1 even where a change was motivated by NS2 |
| Maxwell graphics | `vendor/encore-active/eden-vulkan`, `headless/vulkan.cmake`, `headless/CMakeLists.txt` | Check actual shader and cache generated units, not `vendor/sources/eden` alone |
| Driver/WSI | `tools/install-vendored-radv.py` and `vendor/encore-active/ps5-mesa` | 12 current override units, built library provenance still needs proof |
| PS5 launcher | `headless/prosperoeden/`, `vendor/sources/libwebp` and pinned HarfBuzz | `webp` is registered during non-deferred project injection; later native launcher target only links it; no unqualified upstream bump |
| Content | maintained `fsmitm_romfsbuild.cpp`, `romfs_factory.cpp`, `submission_package.cpp`, `card_image.cpp`, `loader/nsp.cpp` | CMake selects maintained RomFS/AoC/NCZ units; need replayable stress/corruption and savedata regression |
| Package | `tools/package-headless-native.sh` and `headless/ps5.cmake` | Packaging checks compiled source SHA against checkout and rejects production experimental JIT toggles; only actual artifact attests success |

### Dependency/provenance triage (R18)

1. **Engine:** pinned Eden `5f142c7926d0c7fcbbd0ce30794d72f638a43b2a`. Its official mirror head inspected `89d1a1cd7015ebd05ac1bb6a97d1a472bf28701b` on 10 Nov: 155 commits ahead, **300 changed files returned (API cap)**. Investigate **NS1** HLE/audio/filesystem/JIT/texture semantics in batches, never merge entire head.
2. **RADV:** pinned Mihawk Mesa `0b2d6d1a61d9bbf89cf8beb88a696144f67c61f8`; official fork head `7bd4aac55d8c235626028b08b2c76509098f2be7` on 9 Nov is **diverged** (128 commits ahead, 103 behind relative to old pin). A straight fast-forward/rebase **would be unsafe**; compare compiled driver and existing Encore WSI overrides individually.
3. **PS5 Vulkan tools:** pinned `3f3ee69607013b345d2baa6d6a37c86745649a08`; upstream head `7f492b4c6f67a4e8c8c67a4272cfeef22abea9cc` on 10 Nov is 81 commits ahead. Inspect changed WSI deployment/smoke tests and in-buffer descriptors for NS1 relevance; not all are runtime production features.
4. **PS5 SDK/toolchain:** `tools/deps.json` pins the native boilerplate `dd44bbd`, pinned Mihawk SDK fork `95c08f2`, `pacbrew` v0.40.2 and SDK v0.42 packaged input. Official `ps5-payload-dev/sdk` head `8816aee4cd88fc47b07819d2b6f4769c095a074b` (8 Nov) is a **candidate** for build-script comparison, not a binary drop-in or proof of ABI compatibility.
5. **WebP (new first-class source):** `vendor/sources/libwebp` is pinned to original v1.6.0 tree `3a7830b9713d9187cf1211862d4571ff58b0d507` (upstream commit `4fa21912`). Upstream dev head `c3fe5bb655e99ede84f7b2766fc75a8f1d8bbf9e` has 383 additional commits, with decoder changes. Review security/release advisories and **incremental decode / hostile input bounds**, but do not treat development head as a safe release upgrade.
6. **Other official owners:** FFmpeg (`c7b5f153`), LLVM compiler-rt 18.1.8, HarfBuzz 12.3.2, fmt 12.1.0, Boost 1.90, zlib 1.3.2, ZBIC `11b08f27`, Khronos SPIR-V-Headers, libwebp. Each requires an **ABI, version, license, source-selected and relevant test** decision before replacement. Avoid adding a second library for a feature already supplied by vendor.
7. **Licensing / security:** reconcile `THIRD_PARTY_NOTICES.md`, `vendor/docs/`, actual redistributed model/archives and CI archive receipts; `vendor` Dependabot/CodeQL open-alert records are not all confirmed reachable in the PS5 binary. No alert was dismissed or upgraded by this audit.

## B — NS1 engine reassessment

| ID | Current evidence | Decision / remaining work |
|---|---|---|
| **R03** shader NaN + RADV transfer | Renderer/shader source and 12 RADV patched units are selected by build recipes, but the roadmap's old positive tests are not replayed here. | **UNDECIDED**, reconcile shader NaN semantics in compiled shader owner and RADV transfers/barriers with current overrides; then host O0/O2/sanitizer + native test. No duplicate patch. |
| **R04** RomFS + AudioIn | Current CMake explicitly replaces `core/file_sys/fsmitm_romfsbuild.cpp` with the maintained `vendor/encore-active/eden-core/src/core/file_sys/fsmitm_romfsbuild.cpp`. The maintained `RomFSBuildContext::~RomFSBuildContext() = default` exists; the historical blanket assertion of missing RomFS repair is obsolete. NCZ/AoC owners have also changed. | **SOURCE-SELECTED, NOT DEVICE-VERIFIED** for RomFS. Repeat 32,768-entry/256 KiB hash-table/stress/sanitizer tests. For AudioIn, trace selected sink owner and silence buffer length/bytes on the current snapshot before any new fix; do not infer from pristine `sources/eden`. |
| **R22** Switch 1 static AArch64-to-x86-64 recompilation | No actual static compiler implementation found in the audited selection metadata; ordinary Dynarmic remains the native design. | **RESEARCH ONLY.** Indirect branches/relocations, code mutation, SVC/HLE, memory aliasing and the NVN→Vulkan path make a generic retrofit expensive. Only a legally synthetic test module could justify further experimentation, after current NS1 bugs/benchmarks are measured. |

### Prioritized next evidence, without altering main

1. **P0 provenance:** native `compile_commands.json` / link-map selector proof and archive SHA of RADV, OpenGL, LLVM runtime, ZBIC and libwebp; positive/no-shadow check for identical NS1 symbols. Use artifacts from a completed main run when available; do **not** launch another expensive build.
2. **P0 NS1 correctness:** compare only current upstream Eden changes in HLE service waits, audio Opus/AudioIn, filesystem and texture/cache/fence paths with exact maintained owners. Host correctness before speed optimization. NS2-specific changes are excluded.
3. **P1 PS5 driver:** investigate specific Mesa/Vulkan divergences and geometry/WSI/descriptor paths against the 12 patched RADV inputs, with negative-path tests and rollback.
4. **P1 freshness:** libwebp official decoder fixes; SDK official build wrapper; CMake cache/reproducibility/permissions; model rights and transitive notices.
5. **P1 metrics:** one low-overhead, source-bounded benchmark suite for guest simulation, frame queues, shader cache hits and shader warm/cold frame latency; report unknowns without synthetic FPS claims.
6. **P2 R22:** retain a design note; no prototype on the production branch.

## Exit gate

No automatic PR merge, submodule repin, branch cleanup, production build, release, or console test. A later candidate needs exact upstream SHA and license, current **compiled** owner with positive/negative behavior tests, safe PS5 budget/ABI, no NS1 regression, native artifact evidence and user device approval. If a maintainer changes `main` or `vendor`, re-run the source-ownership comparison against the new gitlink before classifying gaps.

**Audit limitations:** repository trees/manifests, CMake source paths and GitHub compare metadata were inspected; no checkout-dependent CMake configure, compiler/link-map, actual firmware execution, OSS license scanner, CVE triage, FPS experiment or full bytewise compare of all 300+ upstream changes was run. This document is a **fresh baseline and actionable audit register**, not a falsely closed full-code review.
