# R00/R02/R18 — eleventh full PS5 native build failure, log-based root grouping

**Run:** [#42911552038](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42911552038), [build job #130163208858](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42911552038/job/130163208858), `main@e76e9e24f4a997825b4765d80eed559895e3a749`. **Observed:** complete FAILED 2026-11-10 22:43:13 UTC; release skipped; **no PS5 ELF/package can be claimed**. Vendor gitlink from main Git tree: `90c9c8a203a27181e23349a889a8f2a7d1cd9dd2`. This is separate from the audit/corrective branch pin `22b69d6`.

The job log groups observed compiler diagnostics into **10 distinct (filename,error) signatures**, all of which belong to **two independent classes**. Repeated compilation messages are not distinct product regressions.

## Build failure class 1 — pinned libwebp SIMD / PS5 toolchain mismatch

Nine affected distinct C files under `vendor/sources/libwebp`: `sharpyuv_gamma.c`, `filter_enc.c`, `picture_psnr_enc.c`, `webp_enc.c`, `ssim.c`, `quant_enc.c`, `frame_enc.c`, `picture_csp_enc.c`, `lossless_enc.c`. Representative compiler error: **`SSE2 register return with SSE2 disabled`** (many occurrences). The files are in `sharpyuv`, `encoder` and `dsp` (not merely decoder).

**Source-level apparent contradiction:** `headless/inject.cmake` already sets `WEBP_ENABLE_SIMD OFF CACHE BOOL ... FORCE` before adding the pinned libwebp subdirectory. The log nevertheless shows intrinsics or SSE2 return signatures being encountered under compiler flags with SSE2 disabled. **The exact compile command/preprocessor macro origin has not yet been extracted, so do not assert that toggling a CMake option alone fixes it.**

Required controlled **preflight before a full build**: inspect `compile_commands.json` for one failing libwebp TU (e.g. `src/enc/filter_enc.c`) and one `sharpyuv` TU; record `-mno-sse2` and any `-msse2` flags, actual `WEBP_USE_SSE2/WEBP_HAVE_SSE2` macro values and selected `WEBP_ENABLE_SIMD` cache; run **syntax/preprocess only** on representative owner units after changing the build integration (never pristine `vendor/sources`). Only expand to an overall native run once those representative TUs compile.

## Build failure class 2 — abandoned diagnostic namespace in active graphics

`headless/graphics.cpp` compiler emits `use of undeclared identifier 'Experimental'` at approx. **lines 778 and 820**, on unconditionally compiled diagnostic histogram/report sites. The same file has `Experimental::vulkan_frame_probe` under `#ifdef EDEN_DEV_PROFILE`, but those usages were not the two reported ordinary release failures.

The actual active variable is `Eden::JitMemory::vulkan_frame_probe` in `headless/jit_memory_policy.h` (already included by `headless/graphics.cpp`). `headless/main.cpp` stores the runtime selector to `Eden::JitMemory::vulkan_frame_probe`. **This is a verified source-name mismatch**; replace the two release-path uses with the effective, qualified namespace and audit the optional DEV uses separately. Do not turn on the experimental feature in production just to fix compilation. A targeted `graphics.cpp` syntax compile plus both normal release / DEV preprocessor modes is required before running the next full native build.

## Exact interpretation / ownership

- Both failures are independently supported by compiler diagnostics from the *failed* build, not speculative missing API warnings.
- These are **compilation blockers**, not runtime crashes, and the build made **no qualifying ELF or gameplay proof**. The previous tenth build had different blocking include errors; avoid reopening them unless the exact compiler input is still present.
- The audit PR #45 **does not patch main, vendor, source flags or schedule any PS5 build**. The independently active main/P5 build owner is responsible for applying and testing these changes on `main`; this document is a fail-closed preflight handoff.
- Compiler error families remaining after this log analysis: **2** (libwebp SIMD and graphics symbol); source files with direct error diagnostics: **10** (9 libwebp + 1 graphics); no assertion that all other compile/link issues have been excluded, because the compiler halted on these errors.
