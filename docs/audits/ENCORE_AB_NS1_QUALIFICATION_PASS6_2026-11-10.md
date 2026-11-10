# Eden Encore A/B NS1 — pass 6: native graph witness vs source-owner proof

**2026-11-10 · PR #45 only · research / no changes to main, vendor, CMake, CI, or native binaries.**
This supplements [pass 3](ENCORE_AB_NS1_QUALIFICATION_PASS3_2026-11-10.md). A green *diagnostic* must not be presented as a valid compiled PS5 graph.

## R00 — refreshed live refs (snapshot, not a rebase)

- Isolated audit branch: `audit/ab-ns1-upstream-2026-11-10`; prior HEAD `6886ba9399a84cbbcc877c3251794737bb91fff8`.
- Main observed at `e73327c93c144807adfc07589849b498a4fdaf25`, **17 commits ahead** of original `e4f6a8253e1f6204a6f99d3b3d29abad1800f4c7`. Changed paths in that comparison: `.github/workflows/build-040-zbic.yml`, `.github/workflows/p5-native-ninja-graph-inspect.yml`, `.github/workflows/p5-native-preflight-host.yml`, `docs/P5_FIRST_NATIVE_BUILD_2026-11-10.md`, `headless/vulkan.cmake`, `tools/build-headless-native.sh`, `tools/check-native-gpu-thread.py`, `tools/check-performance.py`, `tools/ci/check-staged-app.py`.
- **No vendor gitlink change** in that comparison; maintained and pinned inputs audited for AB-01..04 remain the same as the original audit snapshot.
- `headless/vulkan.cmake` changed blob `ebf94c85` → `465e67b1`. Its added lines at 985–990 are a Ninja/CMake dependency-registration comment, **not a substitute shader compiler**. Still inspect actual cached build owner before asserting NS1 path selection.
- The two PR-head runs for `6886ba9` completed successfully: Encore security analysis `42884368087` and sharded P0–P4 host qualification `42884359702`. The latter's five tiny artifacts are qualification reports (1.8–6.4 KiB), not a native `compile_commands.json` or PS5 executable.

## R05 / AB-05 — CMake source-owner trap, now narrowed

- `headless/inject.cmake:5` includes `headless/CMakeLists.txt`. The inspected CMakeLists directly includes `dynarmic/reg_alloc.cmake` (:58) and `jit-alias.cmake` (:253), but **does not directly include** `scalar-memory.cmake`. Direct includes were also not found in inspected `headless/ps5.cmake` or `jit-alias.cmake`.
- The **unreferenced-looking** `headless/scalar-memory.cmake` contains a complete source-list replacement for `emit_x64_vector.cpp` and `emit_x64_data_processing.cpp`. Its presence and comments do not prove execution by configured CMake. Dynamic includes/indirect target mutation still require checking before declaring it definitively dead.
- The pinned `emit_x64_floating_point.cpp` remains a separate owner question; it has no matching replacement in this selector. Preserve the two semantic candidates from Eden `35f0dd7` (division-by-zero result and rounding thunk argument shifts) until a **real compiled** JIT path + instruction tests are supplied.
- The PS5 build's `tools/build-headless-native.sh` explicitly configures with `CMAKE_EXPORT_COMPILE_COMMANDS=ON`; the expected existing-build database is `$scratch/native-local/compile_commands.json`. This file was **not attached as a PR artifact**.

## Existing cache diagnostics: do not mistake green for compiled provenance

| Workflow / evidence | Result | What it does and does not prove |
|---|---|---|
| [42880572712](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42880572712) | Native ninth run: **failure** | No successful binary witness for PR #45's source gaps |
| [42883943523](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42883943523) | Cached Ninja inspection: **success** | Restore of ninth-run cache succeeded; its log emits **`CACHED_NINJA_GRAPH_PARSE_REJECTED_EXPECTED`**. The green job is a *successful diagnosis of an invalid cached graph*, not a valid Ninja graph |
| [42884829914](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42884829914) | Current-main cache reconfigure: **failure** | Did not produce a validated refreshed graph |
| [42885574132](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42885574132) | Current-main cache reconfigure: **failure** at `headless/CMakeLists.txt:1756` | Log reports `Missing audited PS5 OpenGL SDK` under `.local/ps5-opengl-sdk-ad2807d`. This is an environment prerequisite in the diagnostic workflow, not proof of a new NS1 defect |

The cached graph was captured from native source SHA `af106ca4431557246bc1db6d47ac5da562231bb3`. Its `CMAKE_VERIFY_GLOBS` output was examined, but it was **not a valid parsed Ninja build graph**. The later CMake attempt did not finish; neither result establishes which Dynarmic C++ translation unit was actually compiled and linked. Do not use the green cached-graph run to close AB-05.

## Zero-build provenance procedure (next existing artifact, not a CI dispatch)

When an existing checkout/cache with `native-local/compile_commands.json` is **already available**, execute:

```sh
python3 tools/audit/verify-ab-ns1-compile-owners.py --self-test
python3 tools/audit/verify-ab-ns1-compile-owners.py \
  /existing/scratch/native-local/compile_commands.json \
  --require jit_data --require jit_fp --require romfs_builder --require audio_adapter
```

Interpret the results strictly:
1. `one-source-path`: CMake/compilation **scheduled a source path**. It does not certify successful compilation, linked code, exact source bytes, or runtime reachability.
2. `not-in-database`: **unknown** for that database, not absence from all builds (RADV can have a separate Meson database).
3. `ambiguous-multiple-source-paths`: inspect target identity, generated copy, and physical SHA256 before making a patch.
4. For RADV, check the separate Meson compile receipt plus the **actual copied source SHA256** against `tools/install-vendored-radv.py`; both `meta/radv_meta_buffer.c` and `meta/radv_meta_copy.c` are outside its maintained 12-entry override list.

The cached ninth-run compile database, if later extracted, is **historical SHA-specific provenance**; it cannot by itself attest `e73327c` or a successful PS5 binary.

## Remaining acceptance gates (unchanged)

- **AB-04 AudioIn:** positive silence sample count, negative invalid guest address/size, input routing before sink creation and session teardown; test actual compiled `DeviceSession` and source path. Highest memory-safety triage priority when AudioIn is reached.
- **AB-03 RomFS:** actual maintained builder compiled with constrained-stack wide sibling directories and files; repeated destruction, malformed input, ASan/UBSan. Structural model alone is insufficient.
- **AB-02 RADV:** real native copied-source receipt and barrier-only / transfer-only pressure streams; both meta TUs and helper visibility are in scope.
- **AB-01 shared SPIR-V:** configured conditional source ownership, emitted SPIR-V validated for NaN/Inf/finite float and preserved integer semantics.
- **AB-05 JIT:** compiled-source owner and signed-div/rounding positive and negative instruction tests, without importing AVX-512-only changes for PS5 Zen 2.

**Decision:** keep PR #45 draft, do not merge/rebase, no vendor repin, no PS5 build, no source or workflow patches from this audit. All four source gaps and the Dynarmic lead remain *candidates*, not console-proven regressions.
