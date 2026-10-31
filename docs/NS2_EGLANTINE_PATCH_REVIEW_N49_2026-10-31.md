# NSW2 N49 — Eglantine game-tested fix triage (2026-10-31)

Branch: `research/ns2-ps5-compatibility` only. `main` and immutable vendor unmodified.
Upstream observed at `Djihads80/Eglantine@b40ad217ab829226841cb71f6e4c5cb05977a225` (`nx2`).
Eglantine is an Eden-derived PC emulator with public gameplay feedback, not a PS5 validation environment.

## Integrated in the isolated research branch

- **Vulkan image 3D/2D mismatch**, upstream
  [ca524c9](https://github.com/Djihads80/Eglantine/commit/ca524c9aa883abc4d1c5aeb8aa4d2f9eb0b4225c).
  The shader-declared dimensionality may disagree with the underlying
  image dimensionality; requesting a cross-dimensional Vulkan image
  view is invalid. A faithful, full-source overlay of the **active PS5 Vulkan fork**
  `vendor/encore-active/eden-vulkan/vk_texture_cache_cost.cpp` now uses the pure
  `CrossDimensionView` guard before `ImageView::MakeView` selects its
  `texture_type`, keeps the base image view type only in the 3D mismatch
  case, and emits a diagnostic. Other 1D/2D/array view selection is unchanged.
  **OFF by default** via `EDEN_NS2_EGLANTINE_VIEW_EXPERIMENTAL`;
  native PS5, Vulkan, and experimental NS2 metadata required; forbidden
  under `EDEN_FINAL_RELEASE_PROFILE`. Host tests use both Clang and GCC.
  A parity tool rejects any unexpected drift from the *actual PS5 renderer* TU.
  No PS5 Vulkan render validated.
- **Mario Kart World R0/RET**, upstream
  [PR #56](https://github.com/Djihads80/Eglantine/pull/56):
  the current Encore Ampere lowering already implements the semantic
  exclusion via `writes_link` for opcode `0x950`, so copying the
  upstream conditional would **regress** its broader register-write
  accounting. Instead the Eglantine public R0/R55/copy/overwrite
  opcode fixtures are now an active host regression of our *real*
  maintained shader lowerer. No game asset is redistributed.

## Next up, not blindly applied

- [PR #48](https://github.com/Djihads80/Eglantine/pull/48)
  documents missing Splatoon Raiders dialogue glyphs after an unmapped
  page was counted in a previous `DeviceMemoryManager` continuity run.
  This is highly relevant to PS5 texture/HUD correctness. Adapt
  `CutContinuityAt` and Map/Unmap resets to the **actual** Encore
  device-memory owner only after checking memory-run semantics and
  conducting remap/unmap readback and concurrent cache invalidation tests.
- [ddd367a](https://github.com/Djihads80/Eglantine/commit/ddd367a8152f1c37bfc972475b40afece2da31ac):
  same continuity fix, already included in PR #48; avoid double-port.
- [ea33ad1](https://github.com/Djihads80/Eglantine/commit/ea33ad1865970ee731e5f74dbcc26ca472798afe):
  atomic Vulkan cache write + truncated-file detection. Useful PS5
  durability optimization, but native PS5 filesystem rename and cache
  ownership need a dedicated test before transplant.
- [d4ee7fc](https://github.com/Djihads80/Eglantine/commit/d4ee7fcd5129e7ee32ff38a5a756de)
  / [97ce27a](https://github.com/Djihads80/Eglantine/commit/97ce27ab35153884d2fd05c278433928e429cd91):
  sparse layered terrain allocation and selective ASTC re-decode.
  Require GPU mapping budget and synchronization tests before PS5 integration.
- [f9fc1e1](https://github.com/Djihads80/Eglantine/commit/f9fc1e10fd7ed0a1c4664d48d2f095ce8826d87b):
  page-range invalidation batching; validate invalidation happens
  after every contiguous run and preserves correctness under remapping.
- FSR3/frame generation is lower priority than correctness and smooth frame pacing.
- Frontend game-list sidecars and desktop packaging are not PS5 GPU fixes.

**Evidence limitation:** public PC gameplay fixes and host C++ checks
do not establish PS5 or complete Switch 2 game support. Full
`Core::System::Load`, real kernel scheduling, HLE and PS5 RADV
output still require qualification. No console test is requested.

## PS5 source-owner correction

The native CMake path `headless/vulkan.cmake` replaces upstream
`renderer_vulkan/vk_texture_cache.cpp` with the checked-in optimized
`vk_texture_cache_cost.cpp` before later source selection. N49 therefore
must replace **that** source and preserve its existing PS5 texture/upload
optimizations. The earlier direct pinned-owner path was not selected in native
CMake. Corrected before claiming native compilation or validation.

## N50 — Splatoon Raiders device-page continuity

The direct PS5 maintained owner has already implemented atomic store/reset
of continuity for every touched GPU page. It was still missing the PR #48
boundary rule: pages **before** the changed Map/Unmap range retained a
continuity count that crossed into the invalidated range. A bounded prefix
walk under the existing `mapping_guard` now clamps these counts before
the existing page loop executes. It uses the unchanged PS5
`AtomicLoadContinuity`/`AtomicStoreContinuity` helpers; all existing
physical reverse mapping, GPU cache invalidation, remap validation and
scheduler behavior stay in the maintained `.inc`.

Experimental selection:
`EDEN_NS2_EGLANTINE_CONTINUITY_EXPERIMENTAL=ON` with `PS5_NATIVE`
and `EDEN_NS2_METADATA_EXPERIMENTAL`, otherwise OFF; forbidden under
`EDEN_FINAL_RELEASE_PROFILE`. The full `.inc` is derived **only** from
`vendor/encore-active/eden-core/overrides/core/device_memory_manager.inc`,
not from old upstream device memory. The parity check rejects any drift.
Clang/GCC+UBSan host tests cover mapped/unmapped prefix cuts,
unchanged old runs, zero/end boundaries, and deterministic long-run cases.

Eglantine gameplay proof: PR #48 reported that an unmapped page previously
included in a device-memory run zeroed the uniform data used for dialogue
glyphs in *Splatoon Raiders*. The test here proves only local run-count
correctness; **it does not prove real GPU vertex buffers, console output
or successful Switch 2 game boot**.
