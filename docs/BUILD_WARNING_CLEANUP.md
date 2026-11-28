# CI warning remediation — 14 October 2026

Scope: `dev/ps5-sparse-jit`. Historical comparison: [successful native build 38460485028/job/115514057557](https://github.com/niakw/Prospero.Eden-Encore/actions/runs/38460485028/job/115514057557). A green build can still emit legitimate warnings; a completed job is not a clean build.

## Addressed as full, maintained sources

1. **Clang invalid option** `-Wno-error-all`: **78 repeated warnings** in the historical native build. Root: pinned `src/CMakeLists.txt` used a wrong option spelling in the `ENABLE_WERROR=OFF` branch. The **complete versioned** `vendor/encore-active/eden/src/CMakeLists.txt` now uses `-Wno-error=all`, an option supported by Clang. `tools/install-vendored-eden-build-flags.py` stages this exact file after the 43 backports. It refuses any unknown source revision; the original vendor/sources source is never overwritten.
2. **SCM BUILD_ID redefinition**: old `src/common/scm_rev.cpp.in` redefined a macro injected from `src/CMakeLists.txt`. Complete versioned `vendor/encore-active/eden/src/common/scm_rev.cpp.in` now explicitly `#undef BUILD_ID` before defining the intended configured value. This preserves output and removes the macro-redefinition warning rather than disabling the warning.
3. **French translation quality**: both French variants are covered and enforced; old overly long labels were shortened, embedded French regenerated. Missing resolution tiers (including `2x`, `3x`, `4x`) are translated in **all 29 catalogs**. `tools/check-launcher-translation-coverage.py` now fails if any of the nine resolution choices is untranslated in any language, including labels dynamically looked up from `kResolutionLabels`.
4. **Security URL handling**: the curl search parser now validates URL components, refuses unsafe schemes, credentials and nonstandard ports, rejects deceptive URL substring matches and does not follow HTTP redirects to unapproved origins. Adversarial host tests added for the CodeQL high alert. Await a fresh CodeQL scan to verify status.

Both maintained CMake/SCM files are exercised twice in `tools/check-native-build-recipe.py`; tests require byte-for-byte parity with the pinned source aside from the intended correction, idempotent staging and refusal of unknown revisions.

## Remaining real third-party warning debt

The earlier build log also contains **hundreds of NIR/Mesa diagnostics** from the upstream `NIR_PASS(_, ...) ` macros (`variable '_' set but not used`), multiple compiler reports of **missing returns or potentially uninitialized variables** in the Mesa sources, and two link warnings for an unsupported `-z nodynamic-undefined-weak` linker switch from the external toolchain. The Opus/SDL CMake scripts also emit configuration warnings, and a Node tool emits a deprecated `Buffer()` warning.

**These are not corrected by the fixes above.** The Mesa missing-return/uninitialized warnings require individual source review, not a blanket `-w` or suppression. The unsupported linker flag requires auditing the PS5 SDK's weak-symbol semantics before removing it; the warning must not be silenced without verifying the resulting executable's imports. The external toolchain and Node warnings require exact provenance and upgrade/targeted maintenance. Translation catalogs outside the two maintained French variants still have untranslated *non-resolution* strings and must not receive synthetic English translations merely to produce a clean warning count.

## Build/verification status

Historical failures [38481264063](https://github.com/niakw/Prospero.Eden-Encore/actions/runs/38481264063) and [38481264066](https://github.com/niakw/Prospero.Eden-Encore/actions/runs/38481264066) were a **single obsolete UX test assertion** after an intentionally shortened French exit string. The test now checks the current French translation and its embedded copy. Those red runs cannot become green retroactively.

New core/native build validation must confirm both stage-file equality and translated resolution keys. Do not declare the build warning-free, fully translated or a gameplay performance fix on the evidence of source edits alone.

Validation target: stage the two complete maintained native source files, require catalog coverage and safe URL regression, then execute a single All-On native compile. [build-check requested]

The first follow-up preflight at 18c1887f correctly rejected one outdated Yandex curl-search fixture: a relative DDG-specific /l/ route must not count as a valid Yandex search result. The fixture has now been corrected and expanded with adversarial URL and origin cases. Native build compilation and CodeQL classification remain gated by fresh CI evidence.

## 24 November 2026 — native build and warning follow-up

- [Native run 45377792698](https://github.com/niakw/ProsperoEden-Encore/actions/runs/45377792698), engine `ee5d6d57d7d433b8406d1411d348ca60d304e2eb`, vendor `d634b381d85dae30492dd6291fc4e6e96143f363`: native compile/link, signed stage, downloadable FTP ZIP layout and matching crash ELF passed. FTP artifact 14913580970; compiled release bundle 14911989495. Release publication skipped. Console qualification is separate.
- The native job emitted one C++ warning in the selected vendor `encore-active/ns2-runtime/nx/core/loader/nx.cpp:296`: the uint64_t versus SIZE_MAX overflow guard is tautologically false on 64-bit PS5. Vendor `8125086ddd529e7273488edb2bc5949ba8a797b0`, pinned by engine `26b91c5a7b6f1472867661cc5e7d2a3d9b48061d`, retains the narrower-host truncation rejection using an unsigned round-trip check; no warning suppression. Standalone Clang C++20 boundary model passed with -Werror and -Wtautological-type-limit-compare for 32/64-bit widths. Whole native TU and console requalification pending.
- Mesa configuration notes remain: per-application configuration unsupported for this OS and TLS dialect auto-detection unavailable for cross-compilation (compiler default). No evidence here of guest execution failure; do not override the TLS ABI merely to remove a message.
- 62 PSBC prepare failures are in host shader test suites (11 buffer array lowering, 10 compute metadata, 25 compute render, 16 tessellation link); these suites passed. They are not PS5 guest crash traces. 5719 weak imports resolved to NULL; native link/import checks passed, not proof of all runtime weak-call safety.
- No new native build requested while console tests the previous green artifact; host CI for the new gitlink is separate.
