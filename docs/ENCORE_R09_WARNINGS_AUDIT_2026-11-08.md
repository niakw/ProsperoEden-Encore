# Eden Encore — R09 host artifact and compiler-warning audit (2026-11-08)

## Provenance and current validation

- Last **linked and smoke-launched** host binary: engine `756e80c18d3159e7ae214402b363e850729967f6`, vendor `dfd6f3f0a958e55714fc4984b9a1ab1bf306a95b`.
- GitHub workflow [#42465459699](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42465459699): completed successfully, including command-line argument refusal, forged model refusal and artifact publication.
- Public-only artifact **r09-public-host-vulkan-runner**, GitHub artifact ID `13611788160`; its ZIP contains one ELF x86-64 PIE named `r09-full-gpu-host` (28,801,824 bytes unpacked).
- ELF SHA-256: `7f41403249b594ea6ad9d3a00127384845bab3f0940e6ae275c87a8877e6fbe5`.
- Linked runtime requires host dynamic libraries such as `libavcodec.so.60`, `libavutil.so.58`, OpenSSL, LZ4, zstd and opus. It is a **Linux binary**, not a native macOS app or static all-platform release.
- This **is not** 152 real-GPU-operation completion evidence. No authenticated 1080p DLSS-NR Original output, independent oracle or validated per-operation GPU trace was produced by this public-only CI.

## Warning inventory from successful GitHub host link log

Across the successful run, **903 warning-bearing log lines** were recorded, including the shader-tool warning and an Actions Node.js deprecation warning. Most occurrences are repeated includes of the same pinned source headers.

| Count | Warning origin | Status / treatment |
| ---: | --- | --- |
| 594 | `common/page_table.h`: `-Winvalid-constexpr` on `std::atomic` operations | Host-only overlay removes invalid `constexpr` on three atomic writers; pristine vendored Eden remains unchanged. Reduction not yet recompilation-verified. |
| 293 | `core/hle/kernel/k_address_arbiter.h`: `-Wswitch` for ABI tag 3 | Host-only overlay decodes ABI tag 3 before the `switch`, preserving the native call without modifying pinned `svc_types.h`. Not yet recompiled. |
| 1 | `video_core/macro.h`: `[[nodiscard]]` on a `void` setter | Host-only overlay removes invalid attribute; pinned source unmodified. Not yet recompiled. |
| 5 | Dynarmic: unused parameters | Existing third-party code; no behavior-changing edits without dedicated tests. |
| 3 | Dynarmic: excessive stack usage | Needs stack-budget/performance investigation, not a no-op patch. |
| 3 | GCC/libstdc++ `std::variant`: maybe-uninitialized in cheat VM | Investigate initialization and compiler sensitivity; do not suppress or claim fixed. |
| 1 | Cubeb pinned dependency: `-Wreturn-type` in `bytes_per_sample` | Potential missing exhaustive return; requires independent third-party source patch and tests. |
| 1 | Generated `scm_rev.cpp`: `BUILD_ID` redefined | Generated build-system warning, no runtime failure identified. |
| 1 | Shader compiler: unsupported `GL_NV_gpu_shader5` extension | Separate upstream OpenGL shader warning; not a neural Vulkan crash. |
| 1 | Actions Node.js 20 deprecation | Existing pinned checkout and upload-artifact actions; requires reviewed version updates. |

**Do not treat warning count reduction as proven until another build actually runs.**
The three host-only overlays target the sources of **888 repeated warning occurrences**. An exact new count is unavailable because **no long full-Eden build has been launched** after these modifications. Upstream sources remain pristine, as required by the integrity gates.

## Workflow policy

To honor the no-long-build instruction, `.github/workflows/r09-host-link.yml`
is temporarily **manual-only** (`workflow_dispatch`), while the faster
`r09-vit-boundary-qualification.yml` continues to run for vendor changes.
Before claiming the warning-patched main build is fully qualified for release,
manually repeat the full host-link workflow when a long build is authorized.
Do not mask warnings globally or reclassify the original build as a DLSS-NR
full-network execution.

No NVIDIA DLL, extracted model or private capture is stored on GitHub.

## Native HUD shader integrity discovered by the post-commit gates

The 2026-11-07 palette-aware GLSL had a source hash newer than the baked
Vulkan HUD fragment bytecode. A short isolated glslang/Vulkan 1.1 build
[#42468523352](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42468523352)
compiled and validated the real shader. The new validated SPIR-V is pinned
in the vendor, without rebuilding PS5 or the full Eden runtime.

- GLSL SHA-256: `3f5287326b7554164449f5f849f46aae3d2f69ff3a0b4c5c822055bd1877c6d6`
- SPIR-V SHA-256: `029a4bb7c594cc3beadefc731a67768e9f80987ae10a2cb20a5a197a8ebea10b`
- SPIR-V size: 58,092 bytes; compiled with `glslangValidator -V --target-env vulkan1.1`, validated by `spirv-val`.
- The strict native generator now checks **both** source and compiled bytecode digests.
- The original 72-source neural Vulkan host checks continue separately; no 152-operation authentic GPU inference has been established.
