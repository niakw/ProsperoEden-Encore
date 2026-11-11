# R23 pass 6 — three source-proven decisions, no native import (11 November 2026)

**Baseline:** Eden upstream 155-commit file-register \`5f142c79…89d1a1cd\`; Encore audit PR #45 isolated vendor pin \`22b69d6\`. A decision to *not import a particular change* is a source-scope review, not a claim that a current PS5 binary has been built or a service tested.

## #129 — NS async-result two pure renames (source E1)

Upstream [a7061eb4c8afc3a74bd983212131954671317f0b](https://github.com/eden-emulator/mirror/commit/a7061eb4c8afc3a74bd983212131954671317f0b) has exactly **four** changed paths:

- \`core/hle/service/ns/i_async_result.cpp → async_result.cpp\` — Git status \`renamed\`, **zero changed lines**, blob \`be04c162d32c15e685f6939c4b0a587db8206ee9\`.
- \`core/hle/service/ns/i_async_result.h → async_result.h\` — Git status \`renamed\`, **zero changed lines**, blob \`914ea5a42ce6846960edbbbe628b1c1ec462c5c4\`.
- \`src/core/CMakeLists.txt\`: removes and adds exactly the two filenames to the library target.
- \`application_manager_interface.h\`: replaces exactly the corresponding \`#include\` filename.

The pinned Encore vendor source has **neither** old \`i_async_result.{cpp,h}\` nor newer \`async_result.{cpp,h}\` under \`sources/eden/src/core/hle/service/ns/\`. There is no instruction-level algorithm change within this upstream commit to port to the pinned HLE service. **Decision:** \`reviewed-upstream-NS-async-result-pure-rename\`; **0 new behavioral PS5 patches**. Future new-firmware NS HLE implementations (\`#1/#132/#137\`) are **still open** and must select the corresponding source/header pair together. Do not infer they already work.

## #91 — Qt controller-applet picker only, stable native enum (source E1)

Upstream [a82f31a310c5dc7cae50c47b3306510a24cc36a6](https://github.com/eden-emulator/mirror/commit/a82f31a310c5dc7cae50c47b3306510a24cc36a6) touches six files: **five \`src/qt_common/\` or \`src/yuzu/\` files** for the Qt picker and **one** \`src/common/settings_enums.h\`. The latter **appends** \`Disabled\` to \`ENUM(AppletMode, HLE, LLE)\`, preserving the two original ordinal values. Pinned Encore sources retain \`ENUM(AppletMode, HLE, LLE);\`. PS5 headless target does not compile the Qt selector, and the upstream change makes no modification in any core applet executor; enabling a new disabled mode in a Qt form is not a PS5 gameplay correction to transplant.

**Decision:** \`reviewed-Qt-applet-picker-no-current-headless-port\`. The original HLE/LLE mode remains unchanged. It is **not** evidence that native controller applets are correct; \`#84/#112/#131\` remain separate functional candidates. If a future PS5 UI exposes \`AppletMode::Disabled\`, reopen with explicit frontend + guest applet tests.

## #134 — Boost 1.92 distro upgrade is not a runtime backport (E1)

Upstream [10c07d700c33fa1ff78d5f616c2da2872fc5d43f](https://github.com/eden-emulator/mirror/commit/10c07d700c33fa1ff78d5f616c2da2872fc5d43f) changes three metadata/build files only: the root CMake Boost v1 definition, one old clang-cl patch (removed) and \`cpmfile.json\`. In that manifest it switches \`boostorg/boost@boost-1.90.0\` to \`eden-emulator/ext-boost@1.92.0\`, \`boostorg/headers@boost-1.90.0\` to \`boostorg/headers@boost-1.91.0\`, and replaces the dist archive/hash. The actual Encore pinned \`vendor/sources/eden/cpmfile.json\` **still uses the original 1.90 pins and checksums**.

There is **no emulator source-level behavior fix** here. A boost distribution/version migration is a separate native dependency ABI and supply-chain operation and **must not** be smuggled into NS1 source fixes without an explicit coordinated pin change, license/BOM and PS5 compile/link proof.

**Decision:** \`reviewed-upstream-Boost-repin-deferred-native-dependency\`. The *upstream candidate decision* is closed — **do not import** into the current pinned build. General Boost provenance/license/ABI review remains **open under R18**, not reclassified as safe.

## Precisely updated R23 counters

- 155/155 upstream commit file lists retained, **no source discarded**.
- Runtime semantic cases not yet dispositioned: **64** (previously 66; #91 and #129 have explicit E1 source/scope decisions).
- Native dependency/build *upstream candidates* still undecided: **2** (previously 3; Boost migration #134 reviewed and deliberately deferred).
- **8 existing source gaps remain unintegrated**, **17 headers lack native include receipts**, **7 corrective batches lack complete PS5 validation**; these totals are unchanged.
- Exact source/byte/rename metadata, not gameplay or final native linker receipts. No vendor/main merge, no build dispatch.
