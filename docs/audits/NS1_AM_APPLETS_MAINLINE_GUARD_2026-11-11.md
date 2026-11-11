# NS1 AM/HID mainline isolated audit — corrected native source owners, 11 November 2026

This draft branch originates from `main@ce175860d6a1692967ddf50702af72d430766826`, retains `vendor@90c9c8a203a27181e23349a889a8f2a7d1cd9dd2` and does **not** merge/rebase or alter production. It protects main's WebP SSE2 ABI and shader CAS changes.

## Correct current PS5 source owner proof

`tools/prepare-build.sh` materializes **83** complete, versioned files from `vendor/encore-active/eden-backports/` before PS5 native CMake; those are not the pristine `vendor/sources/eden` bytes. Source selection must follow prepared sources.

- Upstream **#131** controller preservation is already in installed `src/core/frontend/applets/controller.cpp` with exact Git blob **`e535866855cb3b87b95efdc5369d7fdb5752b235`**. The old separate `headless/r23_controller_applet_ps5.cpp` was **byte-for-byte identical**. It is deleted and no CMake override selects a duplicate.
- Upstream **#109** applet creator locks and dynamic firmware selection are already in the installed `src/core/hle/service/am/service/library_applet_creator.cpp`, blob **`4ee92908b539c2ee1aad04b38523a297689ce016`**. The discarded `headless/r23_am_library_applet_creator_ps5.cpp` kept a *hard-coded FW22 upper bound*, which could have regressed firmware 23. It is deleted, not compiled.
- Upstream **#84** `AppletId::None` case is **not** in the installed frontend, so `headless/r23_am_frontend_applets_ps5.cpp` remains the *only* PS5-specific AM full-TU override. It includes existing #109 frontend cleanup plus None handling. CMake checks the prepared #131 retention and FW23 dynamic creator text before selecting it.
- Host ASan/UBSan tests now extract the *installed* controller and library creator source alongside the true #84 frontend. No second controller, library-creator or stale vendor source should be selected in the native compile graph.

## Native graph and release exit

`.github/workflows/ns1-am-mainline-native-graph.yml` requires **one** compile owner for each installed backport `src/core/frontend/applets/controller.cpp`, `src/core/hle/service/am/service/library_applet_creator.cpp`, **zero** original frontend TU and **one** maintained `headless/r23_am_frontend_applets_ps5.cpp`. It requests exact PS5 compiler syntax tests, **not a full native link or game boot**. A missing native dependency cache or temporary Ubuntu package DNS outage is an infrastructure failure, not permission to assert success.

Firmware 19/22/23, dual-controller applet, callback lifetime, NS1 boot and shared NS2 HLE smoke tests still need physical-console proof. Audit [PR #45](https://github.com/niakw/ProsperoEden-Encore/pull/45) classified #109/#131 as already shipping; the remaining #84 is an actual selected source gap until this candidate is integrated and proven. This PR stays draft, with no `main` merge, vendor change or branch consolidation.
