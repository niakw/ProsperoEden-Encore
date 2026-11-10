# Eden Encore A/B — qualification pass 2 (NS1 + shared platform)

Date: **2026-11-10**. Follow-up to [baseline](ENCORE_AB_NS1_SOURCE_AND_DEPENDENCY_AUDIT_2026-11-10.md) and [21-lead matrix](ENCORE_AB_NS1_UPSTREAM_MATRIX_2026-11-10.md). The other NS2 research branch owns NS2-specific optimizations.

**Read-only research.** No vendor/source/compiler/CI/packaging change; no PS5 build or merge. The separate on-demand checker is not wired to any CI.

## R00: baseline freshness and separation

Audit branch started at engine e4f6a8253e1f6204a6f99d3b3d29abad1800f4c7 with vendor gitlink 22b69d6053db41b74edac2633c012f925b84f69e. At this second-pass check, main was 795289c9c30ef00172df1c9a572ad42fc735d039. GitHub compare: five commits ahead changing only four paths:

- .github/workflows/build-040-zbic.yml
- .github/workflows/p5-native-preflight-host.yml
- docs/P5_FIRST_NATIVE_BUILD_2026-11-10.md
- tools/check-performance.py

The vendor gitlink was **identical** at both refs. None of the four source-gap input files changed in this main delta; do not rebase this audit while the native build is being qualified. This is a dated snapshot, not permanent main freshness. The vendor recursive GitHub tree API also returned truncated=true at 49,755 entries; this API listing does not justify a claim of exhaustive bytewise coverage.

## Four high-priority leads, refined by exact source path

| ID | Active source and pinned blob | Verified evidence / scope limit |
|---|---|---|
| **AB-01 R03 shader** | vendor/encore-active/ns2-runtime/ampere/shader_recompiler/backend/spirv/emit_spirv_context_get_set.cpp, blob f768235d | EmitSetFragColor stores the original float value, without NaN guard. headless/CMakeLists.txt:2566–2626 replaces the single shared emitter **conditionally** when the native shared SPIR-V compiler is enabled. Applies to NS1 only if that condition is true in the final build; require compiler-command provenance. Do not duplicate NS2 optimization work. |
| **AB-02 R03 RADV** | vendor/encore-active/ps5-mesa/src/amd/vulkan/radv_cmd_buffer.c, blob 9dd12c19 | Direct split calls exist before draw/taskmesh/dispatch, not the inspected transfer/barrier operations. Historical Swordpdf change 1862764 also modifies meta/radv_meta_buffer.c and meta/radv_meta_copy.c and the split helper's visibility. **Neither meta unit is in the 12-entry maintained RADV override list.** Fixing only radv_cmd_buffer.c is insufficient. |
| **AB-03 R04 RomFS** | vendor/encore-active/eden-core/src/core/file_sys/fsmitm_romfsbuild.cpp, blob 94cbb31b | Selected by headless/CMakeLists.txt:764–772. Destructor remains default while Build links owning shared-pointer sibling/child/file chains; parent is nonowning. Prior 32,768-entry / 256 KiB reproducer was a structural model, **not a test of this compiled source**. |
| **AB-04 R04 AudioIn** | headless/audio.cpp a927dcc5, vendor/sources/eden/src/audio_core/sink/null_sink.h b6b43c93, vendor/sources/eden/src/audio_core/device/device_session.cpp 2e9da787 | PS5 adapter selects NullSinkStreamImpl for StreamType::In, ReleaseBuffer returns empty vector, and DeviceSession::ReleaseBuffer asks for samples then calls WriteBlockUnsafe with the original positive buffer.size. **Possible invalid source read if that guest path is reached**; not a confirmed console crash. |

### AB-04: a missing dependency in the earlier audit

At main 795289c, headless/main.cpp (blob 5899f132), line 2005, sets the **output** device to "ps5". No corresponding setting of audio_input_device_id to "ps5" was found in that file. Source change [Swordpdf 01e81e1](https://github.com/Swordpdf/ProsperoEden/commit/01e81e1bae5b61b5b3d65b463b21c2d9e1d77a41) addressed **both** selection of the PS5 input device and a silent input stream returning exactly the requested number of zero-filled samples. The pinned device-session caller does a guest write based on buffer.size, not the returned vector's actual size.

The correct repair contract therefore includes input routing, requested sample count, zero fill, guest-memory bounds, session close/teardown, and non-regression of AudioOut. Concrete positive sample case from the historical patch: 0xF00 / sizeof(s16) samples, all zero. Negative cases: zero/invalid lengths and invalid guest pointer, plus successful disposal of an input session. An instrumented real source-compiled host case must establish whether the invalid source read can execute; the static comparison alone cannot.

### AB-02: multi-translation-unit native driver guard

[Swordpdf 1862764](https://github.com/Swordpdf/ProsperoEden/commit/18627649ca7f72fcc7e3959bdac8d27d8f68fcf9) inserts split checks at buffer fill/copy/update, image transfers and PipelineBarrier2, with helper visibility changes needed for cross-unit calls. Our native install recipe, tools/install-vendored-radv.py, lists only 12 maintained translations and omits the two transfer-meta units. A proposed replacement must be based on actual Mihawk Mesa ABI/function signatures and source provenance, not an upstream copy or CMake-time patch. Test **transfer-only** and **barrier-only** long streams, query/state recovery, and no duplicate split, not just draw-heavy scenes.

### AB-01 and AB-03 acceptance gates

- Shader: compare float finite, NaN and Inf output; integer outputs must stay intact. Compile and validate the emitted SPIR-V, capture pixel and downstream temporal-effect behavior. Historical expected workaround is [Swordpdf e34338d](https://github.com/Swordpdf/ProsperoEden/commit/e34338dd6a538b37b32fd596c496abc15df4418a). Do not claim the historical visual issue is reproduced on PS5.
- RomFS: compile and run the **maintained builder**, not a parallel ownership model, for 32,768 file siblings and 32,768 directory siblings separately on a 256 KiB pthread stack. Test CreateRomFS / ExtractRomFS, readback of final item, allocation lifetime, 64-bit size overflow, ASan/UBSan O0/O2 and negative malformed paths. Historical expected change is [Swordpdf 4f813a3](https://github.com/Swordpdf/ProsperoEden/commit/4f813a352816662fb86183bb1d108425a507881f).

## R18: additional official/upstream dependency owners

The 22 entries in tools/deps.json are fetch **items**, not necessarily 22 linked runtime libraries. The following pinned transitive OpenGL source families deserve explicit SBOM traceability alongside WebP, HarfBuzz, LLVM, Mesa, FFmpeg and SDK:

| Manifest item | Upstream source and pin | Qualification required |
|---|---|---|
| opengl-opengnm-psbc | PS4-OpenGNM/opengnm-psbc a92a1228 | Source/ABI/license and final linked reachability |
| opengl-opengnm | PS4-OpenGNM/opengnm 4b295ca5 | Same, especially under Vulkan-only PS5 profile |
| opengl-spirv-headers | KhronosGroup/SPIRV-Headers 0d25db97 | Official headers; actual compile version and notice |
| opengl-vulkan-headers | KhronosGroup/Vulkan-Headers b51f6b86 | ABI compatibility with PS5 SDK and Mesa headers |
| opengl-imgui | ocornut/imgui f5befd2d | UI source presence versus real launcher linkage |

**No upgrades proposed** on this evidence. Upstream visibility is not a safe release recommendation, nor evidence of a reachable vulnerability. Review actual binary objects, license notices, archive checksums and the pinned transitive graph. Track libwebp v1.6.0 and HarfBuzz 12.3.2 as first-class launcher audit items. Avoid double counting runtime libraries from fetched source trees.

## Reproducible diagnostics, without CI dispatch

Run after checkout of this PR branch with its existing pinned vendor submodule initialized:

~~~sh
python3 tools/audit/check-ab-ns1-source-gaps.py --self-test
python3 tools/audit/check-ab-ns1-source-gaps.py
# Optional non-CI debt gate; expected nonzero when gaps are detected:
python3 tools/audit/check-ab-ns1-source-gaps.py --fail-on-gap
~~~

The checker emits JSON and never modifies source. Missing files produce an incomplete-inputs error instead of a false green. It is deliberately a **static direct-call/signature check**; indirect guards, compile-time feature selection, final linking and reachable runtime behavior remain separate. The checker has **not** been run on a complete initialized repository checkout in this pass, and there are no new host-runtime or PS5 test results.

## Next gates / open work

1. From the **existing** successful main build, inspect compile_commands, link map and RADV source receipt; do not spawn another expensive build.
2. Prioritize actual-source AudioIn and RomFS memory-safety positive/negative host tests.
3. Inspect shader and multi-TU transfer guard, then prototype narrowly in correct maintained owners **outside this documentation PR** with explicit rollback and no NS2-specific imports.
4. Review current Eden A32/A64 Dynarmic fixes such as 35f0dd7 against actual maintained overrides (not just source snapshot) and prove instruction semantics before any JIT change.
5. Inventory the full linked SBOM, version, official maintained source, attribution and toolchain ABI; preserve immutable source snapshots.
6. No PR merge until proof of compiled owner, host test, existing native PS5 CI artifact and non-regression. R22 remains research only.

**Pass-2 result: four unclosed source-level high-priority leads, an additional AudioIn routing dependency, and five more explicit upstream dependency families; zero PS5 gameplay or FPS claims.**


## R05/R23 follow-up: upstream Dynarmic 35f0dd7 — source-owner trap

The recent [Eden 35f0dd7](https://github.com/eden-emulator/mirror/commit/35f0dd7c1ca064ec95ab7efd9981b00f8dcfb989) contains several **distinct** x64 and A32 changes; do not label the whole multi-file commit "missing" or import it wholesale.

- **Division-by-zero:** pinned source vendor/sources/eden/src/dynarmic/src/dynarmic/backend/x64/emit_x64_data_processing.cpp (blob d05d4aa0) and tracked encore-active source (3dd13ebc) both go from code.test(divisor, divisor) to code.jz(end) without Eden's recent code.cmovz(eax, divisor) zero-result step. On the affected x64 IR path the division-by-zero result is therefore a concrete **semantic gap candidate**; test the exact JIT result for positive/negative dividend, divisor=0, divisor=-1, and signed INT_MIN/-1.
- **Floating-point rounding:** pinned source emit_x64_floating_point.cpp (blob 756a6f0a) documents extra arguments at bits 0–7 (rounding mode) and 8–15 (exact), yet EmitFPRoundThunk reads bit shifts **8 and 16**. Eden 35f0dd7 corrects them to **0 and 8**. Test fallback thunk plus SSE4.1 fast path with exact, rounding mode and FPSR/FPCR; do not conflate code presence with executed path.
- **Vector count-leading-zeros:** maintained active emit_x64_vector.cpp (blob 4afc50c7) and original pinned emitter (blob 1165abb0) have the old AVX-512 CLZ16 upper-lane pack. The amending vextracti128 is useful to host feature-variant tests, but AVX-512 is **not a priority for the PS5's Zen 2 CPU**. Do not spend the console build gate on an unreachable host-feature variant.
- **Important CMake reachability uncertainty:** headless/scalar-memory.cmake (blob 1de54e87) contains source selection for active data-processing and vector units; however an explicit include of this file was **not found** in the inspected headless/CMakeLists.txt or other returned GitHub code search matches. The pinned Dynarmic CMakeLists.txt itself lists both original x64 units. A maintained file or policy test that checks its contents does not establish the source was included in CMake. Require native compile_commands and build-tree target sources before selecting the actual patch owner. Floating-point unit has no corresponding override found in the inspected headless CMake.
- **No test claim:** no full native configure, compiled JIT instruction test, PS5 device trace or FPS comparison was run. These are additional, separately triaged AB-05 lead details, not a fifth gameplay bug.

The existing tools/check-maintained-scalar-emitters.py validates parity with retired CMake edits and mentions two compiled units, but it reads the selector file directly; it does **not** itself prove the selector was included in the real native target. Its scope must be kept explicit.
