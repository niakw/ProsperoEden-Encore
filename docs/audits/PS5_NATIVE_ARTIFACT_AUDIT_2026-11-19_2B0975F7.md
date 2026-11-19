# Eden Encore R457 — native artifact audit, 19 November 2026

## Scope and provenance

- **Compiled engine/source:** [`2b0975f7c02f1cb663dd9ecd8c148ea1c4eea10e`](https://github.com/niakw/ProsperoEden-Encore/commit/2b0975f7c02f1cb663dd9ecd8c148ea1c4eea10e), merged fix [#289](https://github.com/niakw/ProsperoEden-Encore/pull/289).
- **Exact pinned vendor submodule:** [`9a83a6ba1cb464c9e5d14457cab18ad511c1104b`](https://github.com/niakw/Prospero.Eden-Encore-vendor/commit/9a83a6ba1cb464c9e5d14457cab18ad511c1104b), confirmed through the engine's `vendor` gitlink at the compiled SHA, not assumed from its current main.
- **Native PS5 build:** [#44423348645](https://github.com/niakw/ProsperoEden-Encore/actions/runs/44423348645) — **success**, actual native C++ compile/link and compiled package staging, FTP download/integrity check, release/symbol packaging and artifact publication.
- **Shipping title:** `PPSA99008`, `01.400.457` / R457, `en-US` default, 320 MiB flexibleMemorySize (`335544320` bytes).
- **Validation boundary:** Sony firmware 13.60 installation, launch, gameplay, title memory, GPU behavior, FC27 HUD/pause, same-process relaunch and NS2 first frame are **not** established by the GitHub run. The user is separately conducting console tests.

## Genuine downloaded artifacts (not inferred from workflow labels)

| Artifact | GitHub ID | Archive bytes | SHA-256 |
|---|---:|---:|---|
| [Standalone FTP title folder](https://github.com/niakw/ProsperoEden-Encore/actions/runs/44423348645/artifacts/14485342647) | `14485342647` | `41,167,501` | `36e314da2e409870a3b3a992a09568034ecaeed0f581fca2187633fbc81213fb` |
| [Full release and symbols](https://github.com/niakw/ProsperoEden-Encore/actions/runs/44423348645/artifacts/14485108654) | `14485108654` | `163,299,149` | `d817ae04aa60e3908747f1ad5902ad4590ed929c47d667decef9fc062b814c8d` |

Both authentic ZIP archives were downloaded and SHA-256 validated against GitHub's metadata. All ZIP and nested ZIP members passed full CRC, and no unsafe path, duplicate, symlink or case-insensitive filename collision was found.

- Standalone FTP Actions archive: **200 title files**, `115,519,564` uncompressed bytes, only one `PPSA99008/` root.
- Full release Actions archive: **7 members**, including the unstripped crash ELF, link map, `crash-provenance.json`, both distribution ZIPs, `SHA256SUMS`, release notes.
- Inner `Prospero.Eden-Encore-R457.zip`: **279 members**, the full `PPSA99008/` app subtree (200 files) plus 79 top-level documentation/license files. Every one of those **200** app files was byte-for-byte compared against the standalone FTP Actions archive: **identical**.
- Inner `Eden-Encore-R457-2b0975f7-FTP-PPSA99008.zip`: **87 members**, all byte-for-byte equal to the same entries in the standalone FTP artifact. The 113 deliberately omitted entries are 82 `legal/` files and 31 `ui/lang/*.txt` ShadowMount companions. `tools/ci/make-dist.py` explicitly documents this reduced FTP distribution; it is **not ZIP corruption**. Distribute the full 200-file artifact or full release where installed notices are desired. The 31 `.po` files remain in the minimal FTP ZIP.
- Internal `dist/SHA256SUMS` matches both inner ZIPs, which passed decompression and CRC checks.

## Binary and crash-symbol checks

| Component | Actual bytes | SHA-256 |
|---|---:|---|
| `PPSA99008/eboot.bin` | `79,947,727` | `90ede60739ab441beefb80093ba5a2dbcd65c3fb82604787db0ecebceb2d34fd` |
| `build/symbols/Prospero.Eden-Encore-R457.elf` | `202,735,280` | `032571c4212cb03f7ab6c1dfd9aac1ce4ec26483ce1e87c20c45014477392f5b` |
| `build/symbols/link.map` | `55,278,820` | `089bda29a0552af923a26ed7e4e232becbef55b8b6bf5d93661d9f092a9e3be4` |

- The three hashes exactly match the downloaded `crash-provenance.json` and the `eboot.bin` hash agrees in **all three** installable variants. Crash receipt embeds `source_commit=2b0975f...` and `workflow_run=44423348645`.
- `eboot.bin` Sony SELF prefix `4f153d1d`; debug ELF is **ELF64 PIE x86-64**, `.symtab`, `.debug_info`, `.eh_frame` present. `readelf` lists **12** target `libSce*/libkernel` PRX/SPRX dependencies and **no** host Linux `.so` dependency. This is a static import check, not a runtime library-resolution proof.
- Debug ELF contains build-runner paths in `DT_RUNPATH`; the checked full path is **absent in the packaged SELF**. Do not treat the debug ELF runpath alone as an on-console loader bug.
- `tools/link-headless-native.sh` intentionally resolves **5,719 weak optional Mesa dispatch imports to null** and checks no undefined weak imports survive the final link. It is a reviewed native-link strategy, not automatically a missing-dependency failure; any subsequent null-hook call still requires runtime evidence.
- The provenance receipt correctly sets `confirmed_same_console_binary=false` and `native_ps5_execution_verified=false` until an actual PS5 runtime receipt is correlated.

## Packaged resource checks

- **13/13** images (PNG/DDS/WebP) parsed/verified, including 512×512 icon and 3840×2160 pic DDS.
- **20/20** WAV files parsed, all at 48 kHz. Native `snd0.at9` present; proprietary playback on PS5 **not** tested by this host audit.
- **8/8** TrueType fallback fonts parsed with valid character maps (Montserrat and Greek/Arabic/Japanese/Korean/SC/TC/Thai).
- **31/31** `.po` language catalogs and **31/31** corresponding `.txt` companion catalogs in the 200-file standalone artifact; all paired file bytes match.
- Source build reports **615 keys × 31 catalogs**, zero missing entries, but **3,789 English fallbacks** across all locales (`fr-FR=73`). English fallback is **not equivalent** to complete human translation.

## Complete build warnings, dependencies and residual gates

### Real diagnostics (not native-link failures)

1. **Vendor C++ compiler warning:** `encore-active/ns2-runtime/gpu_session/core/hle/service/am/service/gpu_worker.cpp:1164`, `restored_sparse_ranges` **set but not used**, `-Wunused-but-set-variable`. The variable is read only under `#ifdef PS5_NATIVE`.
2. **Verified silent NS2 GPU telemetry gap:** The selected GPU worker is compiled as part of `core`, but its `PS5_NATIVE` diagnostic branch is not enabled in this build. **None** of `EDEN_NS2_BLOCKING_BOUNDARY`, `EDEN_NS2_GPU_WORKER_RESULT`, `EDEN_NS2_GPU_214`, `EDEN_NS2_GPU_216` or `EDEN_NS2_GPU_102_SPARSE_RESTORE` is present in either the downloaded SELF or debug ELF. In `headless/CMakeLists.txt`, the three GPU session source TUs are selected at ~3692, without the per-source `PS5_NATIVE=1` definition used for other native `core` TUs. In contrast, `EDEN_NS2_GUEST_FAULT_V1` **is** present: the new strong guest-fault receipt is compiled. **Diagnostic wiring defect, not evidence of a failed GPU mapping or NS2 gameplay fix.** A narrowly scoped CMake definition and build-artifact string witness require a separate reviewed PR; do not globally enable `PS5_NATIVE` across the entire `core` library without evaluating side effects.
3. **Mesa 26.2.0 / Meson:** `cannot auto-detect -mtls-dialect when cross-compiling, using compiler default`. The corresponding Mesa upstream Meson code deliberately skips a host-execution TLS optimization probe when cross binaries cannot execute; the native link succeeded. Mesa also emitted a per-application configuration compatibility `#pragma message` note. Track but do not invent a performance impact.
4. **GitHub Actions JS tooling:** `[DEP0005] Buffer() is deprecated` during `actions/download-artifact`; documented upstream in `actions/toolkit#2003` and **not emitted by the packaged application**.
5. **Optional CMake capability/dependency probes:** RenderDoc include not found; libinotify not found; libusb not found; two compiler-option tests returned `Failed` as capability checks. Native application compilation/linking did not fail. SDL3 bundled `release-3.4.8` reports `SDL-3.4.8-HEAD-HASH-NOTFOUND` for metadata; not a fatal dependency failure.
6. **NS2 system-code host test fixture:** `runtime_ready=NO`, one missing `main` program, no firmware NCA/crypto keys. This is a **deliberately incomplete host fixture**, not proof that the user's PS5-installed NS2 firmware is missing.
7. **Separate engine source preflight was not fully green:** [run #44423348578](https://github.com/niakw/ProsperoEden-Encore/actions/runs/44423348578) ended **cancelled**. Five of its six source shards passed, but `source-audit` was interrupted after ~25 minutes at `Audit generic graphics, JIT, runtime and filtered game networking`; dependent `core-tests` aggregation reported failure. This must be tracked as a **CI qualification/time-budget gap** even though the independent native package run succeeded. [Core fast gate](https://github.com/niakw/ProsperoEden-Encore/actions/runs/44423348514) and [CodeQL workflow](https://github.com/niakw/ProsperoEden-Encore/actions/runs/44423348558) both succeeded. Green CodeQL workflow status does **not** imply zero outstanding security alerts.
8. **Release job skipped:** the native `build` job completed successfully with its own artifact uploads; no additional tagged-release job executed. Do not confuse a skipped GitHub release job with missing `dist/` files.

Dependency versions observed in actual CMake logs: Mesa **26.2.0**, SDL3 **3.4.8**, Boost **1.90.0**, OpenSSL **3.6.2**, Vulkan-Headers and Vulkan Utility Libraries **1.4.345**, SPIRV-Headers **1.4.341.0**, VulkanMemoryAllocator **3.3.0**, fmt **12.1.0**, Opus bundled by source SHA.

## Qualification and next actions

- **Passed:** exact engine/vendor provenance, true native x86-64 PS5 toolchain compile/link, `eboot.bin`/SELF staging, metadata and legal bundle, both actual artifact hashes, nested ZIP CRC and layout, matching full runtime file set, archive symbol/ELF/map matching, 31 locales' file presence, asset parsing.
- **Not passed/unfinished:** separate `source-audit` time budget, missing native NS2 GPU diagnostic branches, some English fallback translations, optional third-party build warnings/metadata.
- **Must await console:** PS5 FW 13.60 install/launch, FC27 frame pacing/HUD/pause/relaunch memory, logs ON/OFF transitions, Bananza/MKW guest PC/first frame, error receipt survival after crash, safe game close and application exit.
- **Priority:** P1 observability gap in NS2 GPU worker (especially if console still black-screens); P2 source-audit timeout and localization; P3 optional dependency/deprecation warnings. Keep runtime tickets open. No native executable changed by this audit.

This file is a documentary receipt for **the exact tested commit**. A future docs-only repository commit does not rebind the original compiled artifact or its crash-symbol hash.
