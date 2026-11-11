# R23 pass 7 — selected frontend CLI and shared-source hazard review (11 November 2026)

**Audit PR #45 only; no production source or vendor change.** Frozen audit vendor `22b69d6053db41b74edac2633c012f925b84f69e`; the 155-commit file register is unchanged. **Evidence E1 only.** Do not infer a full PS5 executable test, compile DB, gameplay or confirmed startup fix.

## #100 — Qt/SDL CLI unification excluded from frozen PS5 headless runtime

- Official Eden source commit [`278f411dad6e8a52747994888f8778b277f6d953`](https://github.com/eden-emulator/mirror/commit/278f411dad6e8a52747994888f8778b277f6d953) modifies **exactly seven paths**: `docs/user/CommandLine.md`, `src/core/CMakeLists.txt`, new `src/core/launch_params.{cpp,h}`, `src/yuzu/main_window.cpp`, and `src/yuzu_cmd/{CMakeLists.txt,yuzu.cpp}`. The upstream core CMake newly adds `launch_params.{cpp,h}`; Qt and SDL command-line entrypoints are the consumers.
- Actual pinned vendor `sources/eden/src/core/CMakeLists.txt` at frozen audit pin has blob **`508ace350173f5068bd7531f37e70199134fde3a`**, without `launch_params.cpp`/`launch_params.h`. The upstream new `sources/eden/src/core/launch_params.cpp` path is **404** at this vendor pin.
- Frozen native recipe `tools/build-headless-native.sh` explicitly passes `-DENABLE_QT=OFF -DYUZU_CMD=OFF`; the independent PS5 entry `headless/main.cpp` defines its own `int main(int argc, char** argv)` and contains **no** `ParseLaunchParams` call.
- **Decision:** `reviewed-frontend-cli-only-no-current-headless-PS5-port`. No behavioral runtime patch for the current PS5 launch owner. Reopen if the native recipe begins selecting Qt/SDL, if a new launcher consumes `Core::ParseLaunchParams`, or if `launch_params.cpp` is added to native core; then test argument options, selected user, guest/game boot and error handling. No claim the real PS5 boot succeeds.

## #29 — Unicode conversions: keep runtime decision OPEN

- Official [`c6fa5c1f77ba40bcb091b1a53492230f40d97ded`](https://github.com/eden-emulator/mirror/commit/c6fa5c1f77ba40bcb091b1a53492230f40d97ded) changes only `src/common/string_util.cpp`, replacing the three `std::wstring_convert<std::codecvt_*>` methods with handwritten UTF conversions. Pinned vendor file blob **`9543a6234376dc4e85ce035a653b41805b8aa072`** still uses the standard converters.
- This is **not demonstrated semantic equivalence**: upstream UTF-8 decode accepts some otherwise invalid leading sequences, with no overlong-codepoint/Unicode scalar checks. For example, the source bit logic for bytes `C0 80` decodes code point zero; a strict UTF-8 validator rejects the overlong NUL encoding. A dangling UTF-16 high surrogate is also emitted rather than explicitly rejected by its encoder. The upstream author marks the change untested.
- **Disposition unchanged:** `runtime-semantic-review-pending`. Do not transplant a warning-suppression refactor without real compiled valid/invalid UTF-8 and UTF-16 differential tests (especially overlongs, isolated surrogates, embedded NUL, boundaries and policy for malformed input).

## #52 — asynchronous Vulkan pipeline depth guard: keep runtime decision OPEN

- Official [`26a03d2473787abf3223b2d0e65b291eee00c1e1`](https://github.com/eden-emulator/mirror/commit/26a03d2473787abf3223b2d0e65b291eee00c1e1) changes exactly two graphics cache functions, including Vulkan `PipelineCache::BuiltPipeline`, adding an early `return nullptr` if `maxwell3d->regs.zeta_enable` and asynchronous shader compilation is enabled.
- Pinned vendor Vulkan `sources/eden/src/video_core/renderer_vulkan/vk_pipeline_cache.cpp` blob **`642b9fa2236f9d66ba0b9144edab6a15b87fc4d6`** has the asynchronous-shader switch and index/vertex-count guard, but **not** the new depth early-return. It is an observable *pipeline selection policy difference*, not an automatically safe optimization.
- **Disposition unchanged:** `runtime-semantic-review-pending`. Before changing native Vulkan behavior, establish active maintained shader/cache owner and actual async option, test depth-enabled draws and single-use quads with async on/off, then visual correctness and perf on a PS5 title. OpenGL is not a substitute for Vulkan.
  
## Counts and scope

**58 semantic cases remain** after excluding **only #100** from the old 59. **0 current-profile upstream build candidates**, **11 source gaps**, **17 native header include receipts**, **7 C00–C06 full corrective gates**, and **5 staged host fixes** are distinct. #29/#52 are still among the 58; no change to the underlying 155-commit/2,376-file source inventory. No PS5 build dispatched, vendor repin, binary release, merge or `main` change by this pass.
