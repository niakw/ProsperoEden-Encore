# Eden Encore — R09 host artifact and compiler-warning audit (2026-11-08)

## Provenance and current validation

- Last **linked and smoke-launched** host binary: engine `756e80c18d3159e7ae214402b363e850729967f6`, vendor `dfd6f3f0a958e55714fc4984b9a1ab1bf306a95b`.
- GitHub workflow [#42465459699](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42465459699): completed successfully, including command-line argument refusal, forged model refusal and artifact publication.
- Public-only artifact **r09-public-host-vulkan-runner**, GitHub artifact ID `13611788160`; its ZIP contains one ELF x86-64 PIE named `r09-full-gpu-host` (28,801,824 bytes unpacked).
- ELF SHA-256: `7f41403249b594ea6ad9d3a00127384845bab3f0940e6ae275c87a8877e6fbe5`.
- Linked runtime requires host dynamic libraries such as `libavcodec.so.60`, `libavutil.so.58`, OpenSSL, LZ4, zstd and opus. It is a **Linux binary**, not a native macOS app or static all-platform release.
- This **is not** 152 real-GPU-operation completion evidence. No authenticated 1080p DLSS-NR Original output, independent oracle or validated per-operation GPU trace was produced by this public-only CI.

## Warning inventory from successful GitHub host link log

A total of **903 compiler warnings**, plus one shader warning and a final Node.js action deprecation warning (counting warning-bearing log lines as recorded, with script warnings varying by format). Most occurrences are repeated includes of the same pinned source headers.

| Count | Warning origin | Status after targeted source patch |
| ---: | --- | --- |
| 594 | `common/page_table.h`: `-Winvalid-constexpr` on `std::atomic` operations | Removed incorrect `constexpr` from `Store`, `MarkRasterizerCached`, `MarkDebug`. Atomic behavior unchanged; not yet recompiled under the latest vendor. |
| 293 | `core/hle/kernel/k_address_arbiter.h`: `-Wswitch` for ABI tag 3 | Moved the existing `WaitIfEqual64` ABI dispatch before `switch`, with identical value and call; upstream enum untouched. Not yet recompiled. |
| 1 | `video_core/macro.h`: `[[nodiscard]]` on a `void` setter | Removed invalid attribute. Not yet recompiled. |
| 5 | Dynarmic: unused parameters | Existing third-party code; no behavior-changing edits without dedicated tests. |
| 3 | Dynarmic: excessive stack usage | Needs stack-budget/performance investigation, not a no-op patch. |
| 3 | GCC/libstdc++ `std::variant`: maybe-uninitialized in cheat VM | Investigate initialization and compiler sensitivity; do not suppress or claim fixed. |
| 1 | Cubeb pinned dependency: `-Wreturn-type` in `bytes_per_sample` | Potential missing exhaustive return; requires independent third-party source patch and tests. |
| 1 | Generated `scm_rev.cpp`: `BUILD_ID` redefined | Generated build-system warning, no runtime failure identified. |
| 1 | Shader compiler: unsupported `GL_NV_gpu_shader5` extension | Separate upstream OpenGL shader warning; not a neural Vulkan crash. |
| 1 | Actions Node.js 20 deprecation | Existing pinned checkout and upload-artifact actions; requires reviewed version updates. |

**Do not treat warning count reduction as proven until another build actually runs.**
The three first fixes address the sources of **888 repeated warning occurrences**. An exact new count is unavailable because **no long full-Eden build was launched** after this vendor change.

## Workflow policy

To honor the no-long-build instruction, `.github/workflows/r09-host-link.yml`
is temporarily **manual-only** (`workflow_dispatch`), while the faster
`r09-vit-boundary-qualification.yml` continues to run for vendor changes.
Before claiming the warning-patched main build is fully qualified for release,
manually repeat the full host-link workflow when a long build is authorized.
Do not mask warnings globally or reclassify the original build as a DLSS-NR
full-network execution.

No NVIDIA DLL, extracted model or private capture is stored on GitHub.
