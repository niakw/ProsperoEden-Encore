# R23 pass30 — current shipping fix ownership, three further false positives
**11 November 2026. Source-level E1 only; no PS5 ELF or guest runtime proof.**

The immutable pass28 [shipping manifest](ENCORE_AB_R23_SEMANTIC_SOURCE_PASS28_2026-11-11.md) proved the complete 83-source/50-receipt backport materialized by `tools/prepare-build.sh` before CMake. A second audit of the **actually installed** source finds three more historical false-positive missing-gap classifications. The original pinned Eden files are **not** the native source for these paths.

## #109 — applet child teardown and lifetime (already patched)

Upstream [`847e91c3a8ca`](https://github.com/eden-emulator/mirror/commit/847e91c3a8ca) changes `frontend/applets.cpp` and `library_applet_creator.cpp`. Installed `vendor/encore-active/eden-backports/src/core/hle/service/am/frontend/applets.cpp`, blob **`d622c7b7a790c4422febb406898cafc198fb3235`**, already unlocks the applet before parent-child cleanup, performs `std::erase(caller_applet->child_applets, applet_)` under caller lock, and calls `window_system->RequestUpdate()`. Installed `vendor/encore-active/eden-backports/src/core/hle/service/am/service/library_applet_creator.cpp`, blob **`4ee92908b539c2ee1aad04b38523a297689ce016`**, encloses both new child insertions in parent mutex lock. **No absent source fix**; real applet scheduling, repeated lifecycle and native release tests remain necessary.

## #128 — read-only NS ListApplicationIcon null-control regression (already patched)

Upstream [`d76f8f91c423`](https://github.com/eden-emulator/mirror/commit/d76f8f91c423) avoids dereferencing optional missing `control.second` in both icon length and contents passes. Installed `vendor/encore-active/eden-backports/src/core/hle/service/ns/read_only_application_control_data_interface.cpp`, blob **`1359cdbb9507fb7c22ca57459a0a03ab95e58f2f`**, contains **both** `if (const auto control = pm.GetControlMetadata(); control.second)` guards and extra transfer-memory bounds assertions. **Native code gap is resolved at selected-source E1**, but guest IPC transfer-memory capacity, null icon, malformed title and real NS1 launch tests remain required. Avoid duplicate null guard patch.

## #147 — qlaunch FW23 cmd23 and AM display-layer source (already patched)

Upstream [`5d150cac5c66`](https://github.com/eden-emulator/mirror/commit/5d150cac5c66) contains four paths: Android Game.kt (not selected on PS5), ARM64 backend NCE bit test (not selected on PS5 x64), `am/display_layer_manager.cpp` and `ns/read_only_application_control_data_interface.cpp` (selected guest HLE). Installed `vendor/encore-active/eden-backports/src/core/hle/service/am/display_layer_manager.cpp`, blob **`cd9e26e8999b2b056d52304dc4ed9b1134beb794`**, already sets visibility, `SetLayerStackMask`, Z-index and blending. The installed read-only NS source blob `1359cdbb9507fb7c22ca57459a0a03ab95e58f2f` explicitly registers `{23, D<&IReadOnlyApplicationControlDataInterface::GetApplicationControlData3>}`, alongside cmd19. Actual native `headless/CMakeLists.txt` does not override either of these service files (it overrides distinct AM `application_functions` and SelfController). This is **E1 source-covered**, not missing. Separate research PR #54's standalone cmd23 alias must be reconciled with current installed source before any merge, to avoid double registration; still test actual firmware 22/23 guest control transfer and layer presentation.

## Important exclusions
- **#84** AM `AppletId::None` is **still missing** from installed `frontend/applets.cpp`, so remains an actual candidate gap, despite #109 Exit being already covered.
- **#1** 23.5.0 NS `Unknown3250`..3262, `present_event` are **absent** from installed `application_manager_interface.cpp` blob `348649917e9f1cf1bfb67c77bd461e434731ced5`. Do not confuse with shipping FW23.0 cmds936/4042.
- **#154** FW23 native SelfController remains partial: CMake shadows installed original via maintained `vendor/encore-active/ns2-runtime/self_controller/.../self_controller.cpp` blob `ad2b043f972170651b61d2d33aea4082e95c47cf`, missing command 240.
- No evidence that `ListApplicationIcon` is fully guest-safe or firmware behavior complete from source presence alone.

## Accounting
Source-gaps **36→33**; already-covered shipping source cases **8→11**; generic undecided **0** remains. **8** separate policy/refactor gates, **17** compiler include receipts, **0/7** PS5-qualified corrective lots and R18 security/provenance remain unchanged. This is exact current source classification, **not** implementation or console validation. No main or vendor edits, no PR merges.
