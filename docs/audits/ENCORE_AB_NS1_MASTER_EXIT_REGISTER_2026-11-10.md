# Eden Encore — A/B and Switch 1 master exit register

**Freeze:** 10 November 2026. **PR:** [#45, isolated draft](https://github.com/niakw/ProsperoEden-Encore/pull/45). **Engine audit baseline:** `e4f6a8253e1f6204a6f99d3b3d29abad1800f4c7`. **Vendor immutable pin at baseline:** `22b69d6053db41b74edac2633c012f925b84f69e`. **Updated R00 (11 Nov):** native cache replay [#42942150990](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42942150990) **SUCCESS** at `main@ec8b519182532d3864c5a67dd27aa41aa9d43ff3` with linked and signed `eboot.bin`, SHA-256 `438fdf4398c9238d5696e925d35b7af6ce8a5a7cc1985a8ce7cde4f5a8b20f4f`, full FTP/distribution artifacts. [Exact audit receipt](ENCORE_AB_R00_P5_RECOVERED_PACKAGE_2026-11-11.md). Earlier 11th build errors remain historic, not the current artifact verdict. **No PS5 console run proof.**

**Purpose:** one durable, reviewable source of truth for **what was checked, what is disproved, what cannot yet be proved, the accepted next evidence and the responsible stream**. Do not reinterpret a green source checker, cached CMake graph or filename match as compiled/link/device proof. No merge or source fixes from this audit-only PR.

## Evidence levels

| Level | Meaning | Current evidence |
|---|---|---|
| **E0** | Exact pinned Git/blob/version & intended owner | Main/vendor SHAs, 26 vendor source families, R18 manifests |
| **E1** | Source semantic delta, static analysis, unit tests of the checker | Four AB gaps, seven Dynarmic cases, independent tools with self-tests |
| **E2** | Existing native **configured** graph and real scheduled input SHA | [Native graph #42886401919](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42886401919); [R18 historic compile SHA source witness #42894073292](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42894073292) |
| **E3** | Actual source-compiled positive **and negative** tests and actual object linkage | **Insufficient** for the four AB gaps, JIT repairs, native header/inclusion paths |
| **E4** | Successful final native PS5 binary **and** device/runtime evidence with NS1 non-regression | Native linked/staged binary now **available** on `main@ec8b519` ([#42942150990](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42942150990)), but **device/gameplay E4 not proven**; no verified FC27/HUD/FPS/PS5 behavior claim |

## A — audit global, sources, dependencies, provenance

| Roadmap | Current evidence | What exactly closes the audit (not necessarily repair) | Status |
|---|---|---|---|
| **R00 — baseline/build provenance** | Historical 11th run failed, but later [#42942150990](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42942150990) **successfully linked, signed and staged** `ec8b519` from cached objects with targeted recompile, ZIP SHA receipts, native map and FTP bundle; [exact link/package audit](ENCORE_AB_R00_P5_RECOVERED_PACKAGE_2026-11-11.md). | Capture and crosswalk artifact `link.map`/native compile DB, exact vendor/SDK source/headers and `eboot.bin` SHA against **real PS5 device binary**, followed by gameplay and ABI tests; do not repeat old failed-build status as current. | **Partial — native link/package proven, E4 PS5 hardware open** |
| **R05 — engine and selected owners** | Historic 9th-run native CDB now attests **all 18 C/C++ source owners** from the 35 modified Eden snapshots: 7 scheduled official Eden bytes, 6 maintained Encore source bytes and **5/5 exact renamed/replacement owners** ([read-only CI #42897861675](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42897861675)). Three Dynarmic x64 emitters still originate from the pinned original. **17 changed headers cannot be certified from CDB alone**; the later read-only [Ninja ledger check #42898452687](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42898452687) passed its analyzer but confirmed **no .ninja_deps ledger is present** in the historical cache (17/17 unqualified). | Real compiler -H/preprocessor/depfile provenance for 17 headers, cross-target ABI, current main build/link owners, and positive/negative native JIT tests. Do not treat analyzer pass as header proof. | **Open — E2 for 18 TUs, E0 only for 17 headers** |
| **R18 — full dependency/licence/security inventory** | All **26 vendor source-family roots** identified in [full family report](ENCORE_AB_R18_26_SOURCE_FAMILY_PROVENANCE_2026-11-10.md); of 15 Git pins, **12 upstream commit trees compared**: 9 differ by origin manifest only, 2 by manifest+CRLF normalization, 1 by manifest+docs requirement. **3 Git pins blocked by inaccessible blackbearreloaded repositories (404).** Three additional non-fetch roots (libwebp, ps5-framegen, PS5_MihawkGen) are exact official tree SHA matches; eden-cpm carries 22 declared lock entries. The 35 modified original Eden blobs remain a separate source-policy conflict. | Resolve 3 inaccessible upstream pins; rehash 6 archive fetches, 8 compiler-rt files and 22 CPM entries against bytes; verify actual staged/linked SBOM, licence notices, ABI, security alerts and the 35 original-source mutations. | **Open — family identities catalogued, provenance/distribution incomplete** |
| **R23 — actual upstream changes & dedupe** | All **155/155** upstream changed-file lists and **2,376** file receipts are recorded in [the exact 155-entry applicability register](r23/R23_EDEN_155_APPLICABILITY_2026-11-11.json). Latest classified distribution (11 Nov): **52 runtime semantic reviews pending, 1 reviewed mixed-backend policy awaiting OpenGL device proof, 1 Unicode migration deliberately deferred after source-derived host divergence, 0 pending current-profile build/dependency reviews, 13 confirmed source gaps**, 5 staged host fixes, plus other individually scoped conditional exclusions/equivalences. New source-diff receipts: [NS/OLSC FW23 command gaps #1/#132/#137](ENCORE_AB_R23_FW23_NS_OLSC_SOURCE_GAPS_2026-11-11.md) and [conditional glslang/Clang23 #13/#101](ENCORE_AB_R23_FINAL_TWO_BUILD_CASES_2026-11-11.md). Two build cases are **current-profile scoped**, not universally fixed on other build paths. | For each of the **52** generic open semantic cases plus **2** scoped policy/host gates, prove exact compiled owner / equivalent / missing / excluded using source semantic and relevant host tests. **13** verified code gaps require a coordinated repair decision, actual compilation and console regression where appropriate. Maintain **17** unresolved native header inclusion receipts, the 7 corrective-batch gates and R18 source/ABI/licence work as distinct counts. | **OPEN — 52 generic semantic + 2 scoped policies + 0 current-profile build + 13 source gaps; 17 header receipts; 7 corrective batches** |
| **R02 — PS5 SDK/renderer/drivers** | Mihawk PS5 Mesa pin is on a **diverged** branch; native Vulkan/Mesa own source tree and 12 maintained RADV overrides; transfer meta TUs outside override list; two tenth-run header errors. | Actual Meson CDB + copied RADV SHA, native shader/driver ABI, transfer/barrier stress, compiler include owner provenance, no ELF linkage assumptions. | **Open — E1/E2 partial** |
| **R17 — external PS5 forks** | Relevant PS5/Windows/C# family differences mapped; NS2 ecosystem explicitly excluded. | Document source-level evidence/rationale for excluding incompatible runtime ports rather than inventing compatible C++ patches. | **Research scope documented; no import authorised** |
| **R01 — operational metrics** | Host and telemetry CI verify counter formatting/host contracts. | PS5 guest frame handoff, GPU queue, VRAM, jitter/HUD, audio and CPU stalls correlated with actual device sessions; zero invented FPS. | **Open — E1, no device** |

## B — NS1 CPU/GPU/HLE correctness (priority by risk, not by hype)

| Case | Verified issue | Mandatory positive/negative evidence before closing |
|---|---|---|
| **AB-04 AudioIn — P0 memory safety** | `NullSinkStreamImpl::ReleaseBuffer` may return empty while `DeviceSession` copies requested positive bytes; input device route defaults to `auto`, not PS5 `ps5`. Conditional path, not a reproduced crash. | Real compiled source + ASan/UBSan invalid guest pointer/length, exact zero-filled samples, correct input route, teardown, unchanged AudioOut. |
| **AB-03 RomFS — P0 lifetime** | Maintained builder destructor is default despite linked owning shared_ptr chains; prior 32k structural model is **not** maintained builder test. | Actual builder + deep/wide-file/dir creation and destruction under 256KiB pthread stack, repeated lifecycle, allocation/overflow/malformed paths, ASan O0/O2. |
| **AB-02 RADV — P0 multi-TU transfer** | Active command buffer stream-split guard omits inspected transfer/barrier-only paths; historical remedy spans `radv_cmd_buffer.c` and `meta` buffer/copy. | Real copied-source Meson receipt, ABI/API visibility, transfer-only and barrier-only pressure, active queries, driver recovery, no double split. |
| **AB-01 shader NaN — P0/P1** | Shared active SPIR-V fragment output stores unguarded float; compiled under conditional shared runtime profile. | Current actual CMake option/linked source, SPIR-V validation, NaN/Inf/finite float and integer semantics, correct temporal behavior, PS5 visuals if needed. |
| **AB-05 Dynarmic seven fixes — P0/P1** | Selected historical original x64 source misses SDIV32 div0, FRINT fallback and SQSHLU corrections. Additional pinned candidates: SM4 PIE codegen, A32 SHA1 decode, FCVT #64 SSE2 fallback, AVX512 CLZ16 upper lanes. | Individual actual JIT instruction truth tests on current selected sources at normal and constrained host features; no entire commit cherry-pick; prioritize PS5 Zen2 path, not AVX512/ARM64 host branch. |
| **AB-06 ARM64 vs x64 shared — P2** | Eden c769b33 ARM64-native deferred branches are **not** PS5 x64 host JIT. Shared page table sign bit may apply. | Prove exact included shared header & ABI bit semantics; exclude ARM64-backend-only code with rationale. |
| **R03/R04 shared ancillary** | GPU sync, memory fences, audio, HLE/IPC, kernel teardown, ROM formats and shader cache source checks are in existing audits; no universal runtime-proof claim. | Keep deduplicated by actual compiled source and runtime tests; no cross-NS2 experimental patch. |
| **R22 static recompiler** | Research concept, no safe production static recompiler implemented or tested. | Mark **excluded from operational release**; if research is later authorised, a separate test/rollback contract is mandatory, not implied by this A/B source audit. |

## Counted exit gates (10 Nov, source proof vs runtime qualification)

| Exact count | Verified/complete | Pending | Meaning |
|---|---:|---:|---|
| A/B source drift **C/C++ owners** | **18/18** | **0** | Historical native compile database and source Git blob identities; not final linked ELF |
| A/B divergent **header inclusions** | **0/17** | **17** | Historic native cache has no applicable Ninja dep ledger; exact include dependency receipts missing |
| Corrective batches **C00–C06 fully release-qualified** | **0/7** | **7** | C00 host implementation tested, C01/C02 staged source patches, C03 owner contract, C04–C06 pending source/behavioral gates |
| C01/C02 source-patch **applicability** | **2/2** | **0** | PR #46 run #42912086261 read-only `git apply --check`, **not** compiled/applied vendor patches |
| Post-F07 source-delta **register rows** | **33/33 recorded** | **0 unregistered on frozen PR-head check** | A dedicated row for C00 `headless/audio.cpp`; 518 historical F07 owners remain immutable. Do not extrapolate to moving-main merge CI |

These denominators describe **distinct categories** and are not additive. Unknown numbers of semantic parity tests across 155 upstream commits, actual current `main` linked owners and external 404 Git origins are tracked by R18/R23 and **not falsely counted as zero**.

## AB-04 additional release gate: real AudioIn timing and buffer retirement

**Updated from the former source-only failure** after [isolated corrective PR #46](https://github.com/niakw/ProsperoEden-Encore/pull/46) SHA `5f07b1c2683488d3256ad32c47167489f3c76d33`:

1. Prior C00 AudioIn used a `NullSinkStreamImpl` that returned zero bytes for positive microphone sample requests, while `DeviceSession::ReleaseBuffer` copied the requested byte count. C00 now uses a bounded **2 MiB** silent PCM16 helper, PS5 input routing and correct input channel metadata. The actual `SilentAudioInputStream` class has a single **10 ms interruptible worker**, calling the pinned `SinkStream::ProcessAudioIn` with 480 two-channel zero frames per tick; it uses controlled Start/Stop/Finalize and performs **no busy-loop capture**.
2. [Actual-class host extractor / ASan/UBSan #42912086254](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42912086254) **passed** for 1/2/6 guest input channels, capture counter progress, Stop, resume, Finalize and bounded zero PCM output. This is a source-extracted real class with **mock** SinkStream/System; no compiled `DeviceSession`, native audio API, Console RAM or real guest event sequencing was tested.
3. The previous source-derived **no-progress capture** condition is now **addressed in the draft adapter**, but cannot yet be labelled fixed in an actual PS5 title. The original `audio_core/device/device_session.cpp` still has incomplete validation: `buffer.size` odd bytes can lead to `ReleaseBuffer(buffer.size / 2)` providing fewer bytes than subsequently copied, oversized input allocations occur in `AppendBuffers`, and validity of `buffer.samples` in guest address space has not been proved at the unsafe write. The original `AudioBuffers::ReleaseBuffers` requires `IsBufferConsumed` for timed retirement, which an isolated mock cannot certify.
4. **Remaining AB-04 runtime gate:** source-compiled `DeviceSession` with invalid/odd guest byte lengths, invalid guest addresses and zero/oversized requests; multi-buffer timeout/ordering/events, 48 kHz monotonic retired timestamps, pause/resume/teardown, no audio-out regression; then real native PS5 build/guest validation under a fixed `main` pin. Avoid adding unreviewed guest memory access to production until this gate has positive and negative evidence.

The corrective branch's **actual Git submodule pin** is the original `22b69d6053db41b74edac2633c012f925b84f69e`. PR workflows that had checked a moving temporary merge tree previously appeared to use `f9f08786` or `90c9c8a2` from concurrent `main`; the isolated tests now explicitly checkout the PR **head SHA**. Neither PR changed production `main` or `vendor`.

**10 Nov C00 follow-up at corrective commit `c142519076fc9d588a468f25328e40f3cb3d203c`:** an explicitly selected PS5-only full-source `audio_core` owner now resides in `headless/audio_device_session_ps5.cpp` and validates whole PCM16 frame sizes, 2 MiB capture maximum, mapped guest memory ranges and exact sink vector sample counts before `WriteBlockUnsafe`. The [host #42914078454](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42914078454) source-extracted function passes ASan/UBSan negative tests for odd/misaligned byte lengths, invalid guest spans, short samples and Output no-op. It does **not** compile or link the complete `audio_core` C++ translation unit, and is **not** a real PS5 guest memory or device lifecycle proof. Frozen F07 baseline remains 518; the two added C00 headless paths (helper + device owner) have separate path accounting. Audit still requires actual source-compiled integration and device tests.

**Current classification: C00 partially implemented with green host tests; AB-04 remains OPEN at E3/E4.**

### 11 November — R18 / R23 finite evidence checkpoint

- [R18 22-tree CPM reconciliation](ENCORE_AB_R18_CPM_BOOST_BYTE_DRIFT_2026-11-11.md): **21/22** regular-file count/size trees match the lock; MoltenVK/zstd are 3 symlinks properly excluded. Only Boost remains: **59,798 files**, checkout **1,527 bytes shorter than lock**. Git blob accounting localizes **689 checkout-vs-Git bytes to five Windows batch scripts**, but does **not** reconcile the underlying 2,216-byte lock-vs-Git aggregate difference. Official archive hashes and provenance remain open.
- [R23 historical source-compilation crosswalk](ENCORE_AB_R23_HISTORICAL_NATIVE_TU_CROSSWALK_2026-11-11.md): 155/155 commits against 1,985 historical CMake native inputs; **749 source-TU change occurrences** map to a scheduled source, **311** remain without exact path mapping (possible maintained names), and **83 commits** changed headers whose effective inclusion is not proven. This is scheduled-input evidence, not a link/PS5 runtime attestation.
- [R23 155-commit actionability](ENCORE_AB_R23_155_APPLICABILITY_2026-11-11.md) now has **105 runtime semantic reviews pending**, **5 staged host fixes still awaiting native/device qualification**, **8 asset/distribution decisions** and **4 native build/dependency reviews**; **23** explicit native-runtime non-applicable paths, **4** ARM-only non-transposable entries and **1** test-only reference. Counts sum to **155**, but categories are **not** a completed runtime parity audit.
- [Corrective PR #46](https://github.com/niakw/ProsperoEden-Encore/pull/46) remains draft. No member of C00–C06 has complete native PS5 console qualification. Its host gates are **not** substitutes for source-compiled full units or guest proof, and the last P0–P4 aggregation needs a green matching corrective SHA before any merge.

- [R23 upstream Joycon and SDL3 closure](ENCORE_AB_R23_155_APPLICABILITY_2026-11-11.md): **#65/#70** negate each other in `Joycons::ScanThread()` exactly (full-file difference is copyright year); **#150** modifies only the SDL3 sink excluded from PS5 `audio_core`. These remove **3** semantic cases without pretending to port or run a PS5 game. Pending runtime semantic reviews: **105**, in addition to 5 staged fixes requiring native/device proof.

## Audit-branch tools and immutable proof index

- [Baseline & dependency source inventory](ENCORE_AB_NS1_SOURCE_AND_DEPENDENCY_AUDIT_2026-11-10.md)
- [21-lead upstream matrix](ENCORE_AB_NS1_UPSTREAM_MATRIX_2026-11-10.md)
- [Pass 7: native JIT source-owner proof and seven cases](ENCORE_AB_NS1_QUALIFICATION_PASS7_2026-11-10.md)
- [Pass 8: original source divergence, native compile errors and 35-path classification](ENCORE_AB_NS1_QUALIFICATION_PASS8_2026-11-10.md)
- [Exact 35-file Git blob manifest](R18_VENDOR_EDEN_35_SOURCE_MUTATIONS_2026-11-10.json)
- [R18/R23 26 source families and upstream lineages](ENCORE_AB_R18_R23_SOURCE_FAMILIES_AND_LINEAGES_2026-11-10.md)
- [R18 complete 26-source-family provenance — 12 verified Git roots / 3 blocked 404](ENCORE_AB_R18_26_SOURCE_FAMILY_PROVENANCE_2026-11-10.md)
- [All 155 official Eden commit SHAs/titles](R23_EDEN_ALL_155_COMMITS_2026-11-10.json)
- [R23 exact source-extracted FS root sanitizer host test](ENCORE_AB_R23_PATH_SANITIZER_ROOT_HOST_PROOF_2026-11-11.md) — #123 E1 differential, no PS5-path signoff.
- [R23 pass 5: include-only C++ and FFmpeg-CI no-native-port decisions](ENCORE_AB_R23_SEMANTIC_SOURCE_PASS5_2026-11-11.md); guarded #144 LSFG Vulkan and #123 shared FS paths remain open.
- [All 155 paginated per-commit changed-file lists](r23/R23_EDEN_COMPLETE_155_COMMIT_PATH_REGISTER.json) and [R23 exact path/semantic boundaries](ENCORE_AB_R23_COMPLETE_COMMIT_PATH_AUDIT_2026-11-10.md)
- [R23 155-per-commit applicability decisions](r23/R23_EDEN_155_APPLICABILITY_2026-11-11.json) and [human-readable applicability and pending-test ledger](ENCORE_AB_R23_155_APPLICABILITY_2026-11-11.md); 115 runtime semantic cases, 12 build/assets and 3 staged native gates; no blanket sign-off.
- [Eleventh failed PS5 native build: exact two-class error triage](ENCORE_AB_R00_11TH_NATIVE_BUILD_FAILURE_2026-11-10.md)
- [Read-only native build source ownership workflow](../../.github/workflows/audit-ab-ns1-readonly.yml) and [static tools](../../tools/audit/)

**Stop/go rule:** This is **NOT a final all-green sign-off**. Do not mark the audit complete solely from CI tests of the analyzers. Source audit closure means every R00/R05/R18/R23/R02/R17/R01/R03/R04/R22 item has either a justified `verified`, `not applicable`, or precise `blocked` disposition with artifacts and owner; to claim PS5 functional readiness additionally requires E3 and E4. The user should only be told `audit intégralement terminé` after **no unreviewed source/family/comparator remains**, and `PS5 validé` only after device evidence. On this dated snapshot, **both claims would be false**.

### 10 Nov evening delta (read-only audit, after pass 8)

- New [5-source replacement checker](../../tools/audit/qualify-r18-replaced-source-paths.py) with synthetic positive/negative tests; native cached-CDB [#42897861675](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42897861675) attests **5 exact maintained replacements** — no remaining unspecified C++ path among the 35 modified Eden sources. Not proof of final ELF linkage.
- New [17-header historical Ninja-deps checker](../../tools/audit/attest-r18-ninja-deps-headers.py) with synthetic tests; [#42898452687](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42898452687) **passed without finding a dependency ledger**. Its verdict is *17 not attested*, never *17 headers correct*. A new **targeted existing-build -H/preprocessor capture** under the build owner's control is required; do not misstate the result.
- Expanded [R18 all 26 roots](ENCORE_AB_R18_26_SOURCE_FAMILY_PROVENANCE_2026-11-10.md), with 12 exact upstream Git commit-tree comparisons, 3 unverified 404 roots, 3 extra exact Git trees and 22 CPM lock entries. No archive-byte or installed-link proof implied.
- Separately, `main` advanced to `89c5c77d29d9a437cb1b0e33a153c6c93b7ee541`; the [cached native graph/syntax check #42895554457](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42895554457) **failed**, and the associated full native build was skipped. This audit has not written to or rebuilt main.


### R18 orphan-pin bundle attestation (10 November, audit read-only)

- The three historically unreachable Git commit sources (`blackbearreloaded` boilerplate `dd44bbd`, native OpenGL boilerplate `4f531c4`, PS5 OpenGL `ad2807d`) have **valid, internally SHA-256-consistent archived chunks** in the pinned vendor checkout. [Audit-only CI #42901485007](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42901485007) validated all three complete bundles: `d38bca60...`, `17b6bb63...`, `c939d4dd...`; full digests and sizes are in [R18 26-family provenance](ENCORE_AB_R18_26_SOURCE_FAMILY_PROVENANCE_2026-11-10.md).
- This **closes the vendor-archive corruption question for these three current bundles**, not the external upstream commit/tree identity: the historical GitHub repos still return 404; never substitute a mirror without a verifiable matching official commit/tree proof. The independent origin-verification gate remains **blocked**.
- Audit-source CI is green for the deterministic 18 C/C++ original/maintained source owners and orphan archive SHA receipts. A green analyzer **does not** qualify the missing 17 header dependency receipts, source-compiled positive/negative runtime tests, final PS5 ELF, or upstream semantic sweep.


### R23 exact semantic triage addendum, 11 November

- Upstream #53 `b7c1ded` is **diagnostic-only**: one `LOG_ERROR` added before the unchanged NCA missing-key status and return. No change to guest decrypt/error semantics; no code import required. `runtime-semantic-review-pending` is now **106** of 155. Upstream #30 has FreeBSD host code and #93 has non-Windows sparse-memory header semantics: both **remain open** despite titles suggesting Mac/Win32-only.


### R23 #20/#66 — LZ4 conditional mode byte receipts

The [source and CMakeCache review](ENCORE_AB_R23_NATIVE_LZ4_MODE_2026-11-11.md) uses audit #43012467528 (native cache **present**, `YUZU_STATIC_BUILD=OFF`) to exclude two upstream changes that only affect static configurations **for that historical native profile**, not for latest main. Build/dependency reviews still open: **3**; 17 header inclusion receipts and real PS5 linked ELF proof remain open.

### R23 #95 — native HID source connection branch is divergent

The [HID source policy report](ENCORE_AB_R23_HID_CONNECTION_POLICY_2026-11-11.md) records a real upstream change in button-triggered Connect() conditions which is absent from the maintained native PS5 HID unit. A 48-state source-model test is checked in read-only CI. This is **not** proof that new Connect logic is correct for PS5 or that a game fails. R23 general semantic cases **66**, explicit source gaps **8**; no imports.

### R23 second exact source exclusion — #5 Nightly updater

- #5 `ae60f8e7` changes only the `#ifdef NIGHTLY_BUILD` automatic release asset parser in `src/common/net/net.cpp`; not a PS5 guest-emulation fix. Runtime-port status `not-applicable` (25), unresolved runtime-semantic cases **105**. If future NIGHTLY builds enable that parser, it requires a dedicated distro test. **#123** shared path sanitation and **#141** common service constructor remain unresolved, despite Windows/MSVC titles.


### R23 pass 6 — exact source decisions #91/#129/#134 (11 Nov)

[Evidence](ENCORE_AB_R23_SEMANTIC_SOURCE_PASS6_2026-11-11.md): two runtime candidates removed from open semantic queue by source-only, non-native decisions (Qt applet Disabled picker not selected, NS async-result zero-line rename); one optional upstream Boost repin reviewed and explicitly deferred. **64 runtime semantic cases + 2 build/dependency upstream candidates** remain. This does not close the **17** native changed headers, **8** verified NS1 source gaps, **7** PS5 corrective batch runtime gates, or R18 source/licence/linked-artifact proof. No source applied to main/vendor.

### R23 newest source receipts and CI baseline (11 Nov afternoon)

- [Firmware 23.x–23.5 NS/OLSC source comparison](ENCORE_AB_R23_FW23_NS_OLSC_SOURCE_GAPS_2026-11-11.md): #1/#132/#137 move from unreviewed to **confirmed source gaps** only; no generic `R_SUCCEED` stubs imported or native ABI proof claimed.
- [Final two current-profile build cases](ENCORE_AB_R23_FINAL_TWO_BUILD_CASES_2026-11-11.md): #13 glslang include quoting is conditional on paths with spaces; #101 Clang 23 GLSL cleanup is not required by the recovered native Clang **18.1.3** Vulkan/PS5 toolchain. Both retain explicit reopen triggers rather than an unsafe transplant.
- **Current R23 counts:** 61 runtime semantic comparisons pending, 0 conditional native-build decisions pending, **11** confirmed upstream source gaps. These are *separate* from the **17** header dependency receipts, **7** full corrective-batch qualifications, and R18 licence/ABI/link-map gates. The historical intermediate pass counts above remain dated evidence, not current tallies.
- The read-only R23 checker and its CI are pinned to this reviewed source evidence and updated category counts; a green result only attests the register, not native functional parity.

### R23 native-input selection decisions (#71 / #143)

[Source-owner evidence](ENCORE_AB_R23_NATIVE_PAD_MOUSE_FRONTEND_EXCLUSIONS_2026-11-11.md): native PS5 pad rumble is dispatched via `scePadSetVibration`, not SDL's vibration worker; desktop mouse drift fixes depend on Qt/SDL timer owners absent from the current native launcher. These are **two current frontend source decisions**, not proof that SDL/mouse TUs are absent from compilation. Remaining R23 runtime semantic cases: **59**; other open counts: 11 source gaps, 17 native header receipts, 7 corrective batches and R18 linkage/licence/ABI gates. Reopen on future native SDL/mouse support.

### R23 pass 7 — current scoped frontend CLI source decision (11 Nov)

[Exact #100 source/owner receipt](ENCORE_AB_R23_SEMANTIC_SOURCE_PASS7_2026-11-11.md): upstream unifies Qt/SDL command-line parsing by adding `Core::ParseLaunchParams`, but native PS5 selects neither frontend and the pinned core does not contain its new source TU. This is a **source-scope exclusion only**, not a PS5 command-line/boot test. R23 now has **58 runtime semantic comparisons pending, 0 current-profile build decisions, 11 confirmed source gaps**. The 17 header inclusion receipts and seven C00–C06 full qualification gates are unchanged. #29 UTF handling and #52 Vulkan asynchronous shader selection remain open; do not import them blindly. Historical counts above are not current totals.

### R23 pass 8 — #52 selected Vulkan versus OpenGL depth policy (11 Nov)

[Exact source comparison](ENCORE_AB_R23_SEMANTIC_SOURCE_PASS8_2026-11-11.md): current PS5 Vulkan pipeline owner `vk_pipeline_cache_cost.cpp` returns an unbuilt pipeline before the upstream asynchronous depth-skip branch; importing #52's `zeta_enable` check directly would not change that PS5 behavior. However, the **native OpenGL fallback remains selectable** and its pinned `gl_shader_cache.cpp` still lacks the upstream depth guard. Therefore **1 conditional backend policy gate is explicitly OPEN** for real OpenGL title/device testing, not claimed repaired. Count **57 generic R23 semantic comparisons + 1 reviewed backend-specific behavior gate**, 11 separate source gaps, 17 headers and 7 corrective batches. No `main`/`vendor` changes.

### R23 pass 9 — #147 NS cmd 23 and overlay disentanglement (11 Nov)

[Source-evidenced FW23 case #147](ENCORE_AB_R23_SEMANTIC_SOURCE_PASS9_2026-11-11.md): original selected NS dispatch offers `GetApplicationControlData3` on command **19** but not **23**. Upstream routes command 23 to the existing handler. The same upstream commit modifies AM overlay-layer behavior, whose ABI/VI dependencies must be qualified **separately**; ARM64-only JIT changes do not apply to PS5's x64 host. This is a **new confirmed source gap**, not a reproduced boot failure or approved patch. Current R23: **56 generic semantic pending, 1 backend-specific OpenGL behavior gate, 12 source gaps, 0 build-candidate decisions**; 17 headers and 7 C00–C06 qualification gates remain.

### R23 pass 10 — #29 source-extracted UTF differential (11 Nov)

[Actual C++ host differential report](ENCORE_AB_R23_SEMANTIC_SOURCE_PASS10_2026-11-11.md) and [tiny sanitizer-backed test](../../tests/audit_r23_utf_conversion_host.cpp) compare the pinned `std::wstring_convert` decoder with upstream's handwritten UTF-8 loop. Overlong `C0 80` fails in the pinned converter but decodes to U+0000 in upstream code; valid Euro/emoji round-trip matches. **Defer the upstream conversion port** pending strict Unicode invalid-input policy and native source/title tests; no assertion that the original C++ API will remain available forever. Current R23: **55 generic semantic cases + 2 scoped backend/Unicode policy gates**, **12** confirmed source gaps, **17** headers and **7** corrective batches.

### R23 pass 11 — #75 Boost ADL + #131 controller fallback (11 Nov)

[Exact source decision record](ENCORE_AB_R23_SEMANTIC_SOURCE_PASS11_2026-11-11.md): pinned Boost 1.90.0 makes #75's GCC12 ADL helper retain the same boost::container vector type; **no native optimizer benefit claimed** and no cleanup port authorized. In contrast, original #131 fallback unconditionally disconnects all controllers, even when `keep_controllers_connected` requests preservation; upstream counts valid connected controllers before filling. This is a **source-proven behavioral gap**, not yet a PS5 pad test. Current **53 unreviewed runtime semantics**, **13 source gaps**, **2 scoped backend/UTF gates**, **17 header receipts**, **7 corrective batches**. No `main` or vendor changes.

### R23 pass 12 — #30 native FreeBSD getifaddrs selected versus upstream macOS routing (11 Nov)

[Exact owner+preprocessor source receipt](ENCORE_AB_R23_SEMANTIC_SOURCE_PASS12_2026-11-11.md): our native PS5 CMake chooses the maintained network interface unit rather than the original. That source selects `getifaddrs` for FreeBSD before its legacy `#elif __FreeBSD__` route-socket branch. Eden #30 primarily enables macOS enumeration and changes the **unselected** old FreeBSD route API. Current-profile **source-only exclusion**, not proof of PS5 gateway enumeration or multiplayer. **52** generic semantic cases remain, 13 code gaps, 2 open policy gates, 17 header receipts, 7 corrective lots.
