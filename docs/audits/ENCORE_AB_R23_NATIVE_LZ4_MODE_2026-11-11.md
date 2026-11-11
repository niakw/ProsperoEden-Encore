# R23 #20/#66 — Historical native LZ4 option, source and cache attestation

**Evidence:** pinned Eden source vendor 22b69d6053db41b74edac2633c012f925b84f69e, source `tools/build-headless-native.sh`, read-only audit [#43012467528](https://github.com/niakw/ProsperoEden-Encore/actions/runs/43012467528).

Effective cached native CMake option: **`YUZU_STATIC_BUILD:BOOL=OFF`**; the ninth-run cache file was present. The recipe uses `-DPS5_NATIVE=ON` and does not set `-DYUZU_STATIC_BUILD`; pinned upstream Eden default is OFF. These are separate checks: the actual CMakeCache is decisive.

- Upstream **#20, `885b333c`**: adds `set(lz4_FORCE_BUNDLED ON)` exclusively inside `if (YUZU_STATIC_BUILD)` in Eden root CMake. Branch not executed with the observed cached OFF.
- Upstream **#66, `e0d47f279`**: modifies `Findlz4.cmake` from `if (TARGET LZ4::lz4_shared)` to `if (TARGET LZ4::lz4_shared AND NOT YUZU_STATIC_BUILD)`. With OFF, old/new predicates are equivalent; the static-target path is unaffected.
- Source checker `tools/audit/attest-r23-native-lz4-static-mode.py` parses the real cache and validates pinned source predicates. Audit workflow fails closed if the historical cache or OFF evidence disappears.

**Disposition:** no native build patch is needed for these two changes **under the recorded historical PS5 static flag**. Remaining LZ4 library selection/ABI, current main source version, CMakeCache and distribution linkage still require independent confirmation. Do not claim a current native ELF exists or that static mode is globally irrelevant.

R23 exact counts after this review: **66 generic runtime semantic cases, 3 native build/dependency cases, 8 verified source gaps pending PS5 tests, 155 total commits classified**.
