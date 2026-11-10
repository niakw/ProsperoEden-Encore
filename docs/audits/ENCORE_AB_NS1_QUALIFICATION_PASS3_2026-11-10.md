# Eden Encore A/B — qualification pass 3: compiled-owner evidence contract

**Date:** 2026-11-10. **Scope:** independent draft PR #45, NS1 and common PS5 runtime. **No changes to main, vendor gitlink, selected source, CMake, CI or release.** Supplements [pass 2](ENCORE_AB_NS1_QUALIFICATION_PASS2_2026-11-10.md), the [A/B baseline](ENCORE_AB_NS1_SOURCE_AND_DEPENDENCY_AUDIT_2026-11-10.md), and [upstream matrix](ENCORE_AB_NS1_UPSTREAM_MATRIX_2026-11-10.md).

## R00 — moving main and fixed input snapshot

- Audited PR HEAD before this pass: `33c914ef5c9fb7be40b45f050c70c75b2b91fa61`, base `e4f6a8253e1f6204a6f99d3b3d29abad1800f4c7`.
- Subsequent current main observed: `af106ca4431557246bc1db6d47ac5da562231bb3`, **11 commits ahead** of the audit base. Compare lists six changed paths: `.github/workflows/build-040-zbic.yml`, `.github/workflows/p5-native-preflight-host.yml`, `docs/P5_FIRST_NATIVE_BUILD_2026-11-10.md`, `tools/check-native-gpu-thread.py`, `tools/check-performance.py`, `tools/ci/check-staged-app.py`.
- The `vendor` gitlink at this main HEAD is still `22b69d6053db41b74edac2633c012f925b84f69e`, equal to the audit base. These main changes do not alter the four audited source inputs. **Do not rebase onto main during its native build.**

## P0 source findings: exact source evidence vs executable proof

| Lead | Verified at the pinned source | Compilation / runtime proof missing |
|---|---|---|
| **AB-04 AudioIn** | `headless/audio.cpp` branches `StreamType::In` to `NullSinkStreamImpl`; pinned `null_sink.h` returns an empty vector; `device_session.cpp:112-116` writes the originally requested byte count from `samples.data()`. `headless/main.cpp:2005` configures output only. Historical [Swordpdf 01e81e1](https://github.com/Swordpdf/ProsperoEden/commit/01e81e1bae5b61b5b3d65b463b21c2d9e1d77a41) changed **both** input routing and a zero-filled input stream; do not take one half. | Confirm which input sink name is actually acquired; compile the actual input stream/device session; positive PCM zero samples and cancellation/teardown, negative invalid guest address/size with sanitizer; no AudioOut change. There is a credible memory-read hazard, **not a reproduced PS5 crash**. |
| **AB-03 RomFS** | Maintained `fsmitm_romfsbuild.cpp:200` has default destructor; files and dirs use owning `shared_ptr` sibling/child chains (`:59-79, 248-268`). CMake selects this maintained translation unit at `:764-772`. | Compile this **actual builder** and run wide directory and file cases separately with constrained pthread stack, repeated lifecycle and malformed input. Earlier structural model is not native-source proof. |
| **AB-02 RADV** | The selected `radv_cmd_buffer.c` split helper is `static`, with direct calls at `:14005, 14091, 16308`; no direct barrier call at `radv_CmdPipelineBarrier2`. The **pinned** Mesa `meta/radv_meta_buffer.c` and `meta/radv_meta_copy.c` expose transfer entries but no direct split calls. Their paths are missing from `tools/install-vendored-radv.py`'s current maintained override tuple. [Swordpdf 1862764](https://github.com/Swordpdf/ProsperoEden/commit/18627649ca7f72fcc7e3959bdac8d27d8f68fcf9) is a **multi-TU** historical repair, not a safe drop-in patch for Mihawk Mesa. | Actual RADV build receipt, compiled two meta units and cmd unit, verified helper ABI/visibility, transfer-only and barrier-only pressure cases, active-query correctness and driver recovery. For generated/copied build inputs, compile paths alone cannot certify original bytes. |
| **AB-01 shader** | `EmitSetFragColor` in `vendor/encore-active/ns2-runtime/ampere/shader_recompiler/backend/spirv/emit_spirv_context_get_set.cpp:685-703` stores unguarded floats. CMake selects the maintained emitter **only inside** `EDEN_SHARED_NS2_SPIRV_COMPILER`; that variable is enabled by `EDEN_SHARED_NS2_AMPERE_CORE`, itself gated on `PS5_NATIVE && EDEN_REVIEWED_DUAL_NPDM && EDEN_PS5_VULKAN` (`headless/CMakeLists.txt:2466-2469, 2566-2616`). | Confirm final CMake cache, compile database and linked owner before claiming an NS1 executable gap; compile and validate emitted SPIR-V and compare finite/NaN/Inf and integer outputs. An Ampere-named shared source may participate in NS1 SPIR-V, but this does not authorize NS2-specific changes. |

## AB-05 Dynarmic — orphan-selector caution

`headless/scalar-memory.cmake` declares substitution of `emit_x64_vector.cpp` and `emit_x64_data_processing.cpp` with maintained copies, but **no direct include** of that selector appears in the inspected `headless/CMakeLists.txt`, `headless/ps5.cmake` or `headless/jit-alias.cmake`. A dynamic/indirect inclusion remains possible; only configured build target sources can settle this. Do not treat this file's existence as evidence that the maintained unit is compiled.

Both the pinned and maintained `EmitSignedDiv32` omit upstream [Eden 35f0dd7](https://github.com/eden-emulator/mirror/commit/35f0dd7c1ca064ec95ab7efd9981b00f8dcfb989)'s zero-divisor result assignment. Pinned `emit_x64_floating_point.cpp` decodes thunk fields at shifts 16 and 8, versus the documented/upstream corrected shifts 8 and 0. These are **semantic source candidates**, pending actual JIT owner and instruction results. AVX-512-only CLZ16 remains a low-priority PS5 path.

## Read-only existing-build provenance tool

`tools/audit/verify-ab-ns1-compile-owners.py` classifies up to nine translation-unit families from one or more **existing** `compile_commands.json` files; it does not build, change source, or assume that a copied RADV path has the same bytes as a checked-in override.

```sh
python3 tools/audit/verify-ab-ns1-compile-owners.py --self-test
python3 tools/audit/verify-ab-ns1-compile-owners.py /path/to/native/compile_commands.json
# Optional: when both databases already exist
python3 tools/audit/verify-ab-ns1-compile-owners.py /path/to/native/compile_commands.json /path/to/radv/compile_commands.json --require jit_data --require jit_fp --require romfs_builder
```

- `one-source-path` means exactly one **path** is recorded, not proof of linked object or correct version. Repeated commands for the same path are counted but not mistaken for multiple source owners.
- `ambiguous-multiple-source-paths` requires build investigation, particularly if pinned and maintained sources coexist.
- `not-in-database` means **unknown**, not absent from all builds (RADV may use a separate external build). Optional `--require` returns nonzero for owners without a unique path; incomplete/malformed JSON returns 2.
- Source classification is based only on paths, not a verifiable SHA. The **RADV copied-source receipt, CMake cache, final object/link map and executable SHA** are separate mandatory evidence.

## Decision and next proof

**Do not merge.** Four high-priority source-level leads plus AB-05 semantic candidates remain unqualified as PS5 runtime regressions. Review existing build artifacts first, then perform host compilation and targeted positive/negative tests against the actual maintained owners **on an isolated implementation branch after the main build gate**, not inside this audit-only PR. No NS2-only imports, blind RADV upstream cherry-picks, vendor repins or new PS5 build launches here.
