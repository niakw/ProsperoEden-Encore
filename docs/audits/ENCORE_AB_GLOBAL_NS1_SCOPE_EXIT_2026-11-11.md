# Eden Encore — final NS1/global A/B scope coverage and evidence gate (11 Nov 2026)

**Owner:** audit-only PR [#45](https://github.com/niakw/ProsperoEden-Encore/pull/45). **Frozen production comparison:** engine `6456590a2b5764412798e2effdfa061c17b4359e`, vendor `f8f5d8ee3a94a4202886a40badb5c0203d05da30`. No merging, vendor mutation or release from this audit. All underlying previous receipts remain available and must not be restated as current binary proof.

## 1. Exhaustive *defined scope* and audited evidence by subsystem

| Domain | Audited owner/source proof | Remaining release evidence / remediation |
|---|---|---|
| Source origin and licence | 26/26 vendor family roots, 15 Git fetch entries, 22 fetch types, 22 CPM locks; Git Merkle `sources@99ffa030` unchanged on current main | External original source for 3 inaccessible historical pins, 22 official CPM archive digests, Boost size drift, actual linked notices/SBOM and legal source attributions |
| Vendored original discipline | 35 modified pristine Eden source blobs identified by exact file and Git blob. 18/18 changed C++ effective historical source owners identified | **17** modified header actual compiler include receipts and current-pin effective owners; source drift policy resolution |
| Main and shared vendor drift | Current `main` uses vendor `f8f5d8e`, not old `22b69d6`; 23 maintained files changed in 4 commits, originals unchanged; native source-gate review in [current-pin proof](ENCORE_AB_R18_CURRENT_MAIN_VENDOR_DRIFT_2026-11-11.md) | Current native compile DB + link map, cross-guest memory / staging / ASTC / decoder / GPU retirement and ABI tests |
| SDK and toolchain | PS5 FreeBSD/Clang, linker, RADV and runtime dependency routes identified; native recovered artifact `ec8b519` historical | Exact current `6456590` target compiler/link receipt, PS5 firmware compatibility, SDK headers and staged signing symbols |
| Native CMake/CI | Existing P0–P4 tests, native source owner and R23 full inventory workflows; [155 files CI](https://github.com/niakw/ProsperoEden-Encore/actions/runs/43056154589) green at audit `04f64d47` | Confirm all required workflows on *same final SHA*, no stale PR merge-ref or missing-cache false pass; current console build |
| CPU A32/A64 JIT / Dynarmic | Seven x64/A32 semantic leads, signbit 55 and x64 lookup 63-bit patches, selected original x64 TU proven in historical CDB | Real x64 JIT instruction truth, watchpoints, feature flags (Zen2), ABI, headers; C04 **unapplied** |
| Guest memory / CPU6 ABI | CPU6 offset mismatch `m_memory` proved on older R457; #52 has targeted source repair and unit checks; new dual NPDM/sparse core owner traced | Current core/audio/video/hid compile coherence, fastmem/no-fastmem, guest page writes and PS5 FC27 boot |
| Audio capture/output | AB-04 source overread and silent PCM defects; #46 C00 full selected AudioIn/DeviceSession candidate and host sanitizer tests | Full source-native `audio_core` TU and real IPC guest lifecycle, invalid/odd buffers, audio-out nonregression |
| RomFS/FS/loader/storage | AB-03 recursive ownership, patched IPS native owner, path-root sanitizer, F2I/BCAT/registered-cache/file-shares source differences | Full iterative destructor and malformed RomFS stress, title/firmware/savedata/NSO/NSZ/NRO guest tests |
| GPU/Maxwell NVN, Vulkan shaders | AB-01 shared SPIR-V NaN, #46 conditional maintained source; revised Vulkan presenter already maintained; 155 Eden commits fully file-inventoried | SPIR-V float/finite/NaN validation, shader cache and async compilations, Vulkan pipeline/depth/texture, K/V DMA and negative GPU-page tests |
| Mesa RADV / WSI / Vulkan driver | Diverged PS5 Mesa fork, 12 RADV overlay owners, AB-02 transfer split issue and C03 three-source contract | Meson CDB + copied blobs + ABI, transfer/barrier-only command-buffer splits, fences/device-loss and PS5 RDNA2 tests |
| HID/AM/HLE/IPC/FW23 | #55 isolated #131/#84/#109 controller/AM applet candidates and #54 FW23 NS cmd23 alias, #46 audren debug, 29 verified broader source gaps | Real full native TUs, IPC command/handle/service semantics, NPAD, max_sessions, AM overlay, title boot old/new firmware |
| Presentation, AA, upscaling, NR/FG | Shared renderer chain and service selector surfaces identified; R09 and AA/NR/FG research separately owned | **Every valid enabled/disabled combination** of AA + scaler + neural NR + frame generation, Vulkan queue/VRAM/latency and visual proof must be qualified in graphics integration; this A/B audit does not implement R09 |
| UI/launcher, locales, cover art, assets | R457 #52 includes launcher UX/CPU6 candidate, 31 system language matrix and packaging tests; current CI source routes available | Console textures/case/cover/WebP image lifetime, L1/R1 navigation, settings, input, 31 real language translations (English fallback not translation), FTP ZIP/checksums |
| Diagnostics, power, security | Host counter and smoke checks; archive bytes 6/6, compiler-rt 8/8; [security triage](ENCORE_AB_R18_2026_SECURITY_ADVISORY_TRIAGE_2026-11-11.md) covers HarfBuzz/FFmpeg/Mesa exposure | FPS/frametime/audio/GPU real session tracing, exact binary SBOM, licence notices, CVE-to-compiled-feature reachability; no invented performance claims |

## 2. Exact independent counts (do not sum as a percentage)

- Upstream Eden: **155/155** commit/file receipts, **2,376** changed-file occurrences. **20 runtime semantic comparisons remain unqualified** in a [20-row owner/test crosswalk](ENCORE_AB_R23_20_RUNTIME_EXIT_CROSSWALK_2026-11-11.md).
- **29** verified upstream source gaps needing production owner or native proof; **8** distinct policy/refactor decisions; **17** historical changed-header inclusion receipts missing; **7** release batches C00–C06 still **0/7** fully PS5 qualified. These categories are not additive.
- Dependencies: **26/26 inventoried**, **6/6** local archived download hashes and **8/8** compiler-rt hashes, **21/22** CPM *counts/sizes* reconciled; **0/22** official CPM original tar stream digests verified independently; **3** upstream unavailable historical pins with *local* archived custody proven but not official origin.
- Main has moved beyond audit and all five draft heads. Avoid a false positive from old `ec8b519` build or `ce175860` native graph on the current main/vendor. No new P5 console proof.

## 3. The five open streams are **not** redundant

| PR | Strict scope / branch | Verdict and transfer boundary |
|---|---|---|
| [#45 audit](https://github.com/niakw/ProsperoEden-Encore/pull/45) | `audit/ab-ns1-upstream-2026-11-10` | Complete inventory, current vendor drift and CVE exposure register; **20 semantic + 17 headers + R18 linkage/official hashes remain unproven**, so do NOT label exhaustive semantic audit signed off |
| [#46 corrections](https://github.com/niakw/ProsperoEden-Encore/pull/46) | `dev/ab-ns1-corrective-batches-2026-11-10` | C00/C01/C02 selected maintained host-reviewed candidates; C03 RADV contract and C04 unapplied patches. **Conflicts with main**. Do not repin old vendor or merge wholesale |
| [#52 R457 integration](https://github.com/niakw/ProsperoEden-Encore/pull/52) | `integration/r457-ns1-abi-launcher-20261111` | NS1 CPU6 ABI and launcher candidate; older full native workflow failed source UI contract at `cbe7e6f`, later branch code/test corrections exist; latest head native and console not qualified |
| [#54 FW23 NS](https://github.com/niakw/ProsperoEden-Encore/pull/54) | `research/r457-ns-fw23-command23-20261111` | One alias command 23→existing 19 handler, host parity green; native IPC and real FW23 launch still open |
| [#55 AM/HID](https://github.com/niakw/ProsperoEden-Encore/pull/55) | `research/ns1-am-applets-mainline-20261111` | Isolated maintained controller + AM applet source; mock host tests green, native graph cache key corrected; full native C++ and console proof not established |

## 4. Unambiguous acceptance decision

**Coverage inventory is finite and documented, but an exhaustive completed *semantic/security/release* audit is NOT proven.** In particular 20 direct upstream semantic cases remain; claiming the audit 100% completed today would hide known work. The corrective owner can now implement from this frozen ledger instead of restarting initial discovery, but **closing #45 as technically fully finished is not justified** until each pending case is independently proven, explicitly excluded with exact compiled source, or accepted as a documented non-port policy. Defer major source migrations rather than introduce duplicate experimental modes into the sole production engine.

**No merge, branch deletion, vendor change, new PS5 build or release was executed from this A/B audit.** Actual PS5 hardware/device validation is separately mandatory and never simulated by host checkers.


### Pass21 addendum (same calendar date)

[Explicit pinned HLE source comparison](ENCORE_AB_R23_SEMANTIC_SOURCE_PASS21_2026-11-11.md) closes generic semantic triage for upstream #120 SSL CMIF/three-unit OpenSSL backend and #149 BPC/max_sessions by classifying **two new real unported source gaps**, **not implemented fixes**. Exact immutable ledger and CI now require 26 generic pending / 24 code gaps, while 8 scoped policy decisions, 17 native header receipts and 0/7 full PS5 release gates remain. [New 26-item owner/test map](ENCORE_AB_R23_26_RUNTIME_EXIT_CROSSWALK_2026-11-11.md) replaces the historical pass20 28-item list for current tracking.


## R23 pass22 update — native shader and LSFG owner proof (11 November)

The [exact source comparison](ENCORE_AB_R23_SEMANTIC_SOURCE_PASS22_2026-11-11.md) reclassifies upstream #80 (non-NVIDIA shader fragment workaround missing from selected RADV shader/Vulkan path) and #144 (Android-marketed LSFG UI commit with real PS5-selected native backend/presentation changes) as **source-verified E1 gaps, not implemented fixes**. The [new 24-case crosswalk](ENCORE_AB_R23_24_RUNTIME_EXIT_CROSSWALK_2026-11-11.md) and CI validator must be used going forward; the preceding 26-case document remains a historic pass21 snapshot. Generic reviews **24**, verified gaps **26**, policy/refactor gates **8**, header receipts **17**, PS5-qualified C00–C06 **0/7**. Current tests and actual device results have not been inferred.


## R23 pass23 source owner proof (11 November)

[Pass23](ENCORE_AB_R23_SEMANTIC_SOURCE_PASS23_2026-11-11.md) identifies two additional real E1 source differences: **#32** Dynarmic A64 `TranslationOptions::hook_hint_instructions=true` is not semantically equal to full `UserConfig::hook_hint_instructions=false` on the selected G11 x64 owner; **#46** native CheatEngine `ExtractName` can access beyond the bounds of a malformed `string_view`. Neither gap is fixed or device-tested. [Exact 22 generic cases still awaiting source decisions](ENCORE_AB_R23_22_RUNTIME_EXIT_CROSSWALK_2026-11-11.md). **22** generic semantic cases pending, **28** source-verified gaps, **8** policy/refactor gates, **17** header include receipts and **0/7** complete PS5 release batches. No vendor/main edits and no fusion of branches.


## R23 pass24 — only the selected native owners (11 November)

[Pass24](ENCORE_AB_R23_SEMANTIC_SOURCE_PASS24_2026-11-11.md) closes two more generic decisions without making production changes: **#10** current G11 native A32/A64 already resets guest code cache, but shared A32 debugger optimizer still lacks upstream `check_halt_on_memory_access` guard (**partial source gap**); **#68** ARM64 NCE runtime TLS/RO patching is not selected on the PS5 x64 target, whose RO source already enforces native permissions (**no-port scope decision**). [20 remaining source-owner cases](ENCORE_AB_R23_20_RUNTIME_EXIT_CROSSWALK_2026-11-11.md). **20** generic reviews pending, **29** verified source gaps, **8** separate backend policy/refactor decisions, **17** missing native header receipts, **0/7** full release lots PS5-qualified. These counts distinguish investigation from implemented fixes.
