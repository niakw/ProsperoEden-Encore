# PS5 R457 — shared Vulkan startup regression (2026-11-17)

Status: P0, console reproduction confirmed; candidate pending qualification. No raw user logs included.

## Reproduction

- PS5 firmware 13.60, executable source `42eb93692779a0e7a50c5dbdb8bad1e3d815c1da`, vendor `ffa519db0f68fb0d5d2acf791e381c898a34a175`, native run [43974660874](https://github.com/niakw/ProsperoEden-Encore/actions/runs/43974660874).
- FC27 NS1 `0100C49025D3E000`: loading cover, then persistent black screen; GL loader stops after 59 frames.
- Mario Kart World NS2 `0400C3F00006E000`: longer loading with moving dots, then persistent black screen; GL loader stops after 2452 frames.
- Both: core initialization and NSO loading reached; EGL scanout released; Vulkan surface creation returns success, including final `vkCreateDisplayPlaneSurfaceKHR`; no `core_loaded`, `game_loaded` or `guest_run_begin`. Input polls continue. Exit request during loading triggers the existing ten-second stop watchdog, and the next launch confirms an exhausted stop timeout. No new crash report. Do not classify as a guest GPU failure or prove a particular blocked Vulkan call from these logs alone.

## Investigation and candidate

Reviewed the pinned vendor renderer initialization and storage buffer descriptor helpers against the engine renderer. Upstream Eden issues #150 (initialization error), #414 (instance-extension race), #161 (EDS device loss) do not establish an identical cause. See also [Khronos constant data sample](https://docs.vulkan.org/samples/latest/samples/performance/constant_data/README.html). No vendor change justified by current evidence.

The previous Unicode implementation embeds 4931 raster glyphs in the same fragment shader first compiled by loading presentation: 641640 SPIR-V words (2566560 bytes), even when the quick menu is hidden. This is a strong regression candidate, not a proven hardware root cause. [P0 issue #263](https://github.com/niakw/ProsperoEden-Encore/issues/263); [candidate PR #264](https://github.com/niakw/ProsperoEden-Encore/pull/264): split loading/FPS and Unicode menu pipelines, keep glyph atlas in immutable storage buffer data, lazily create menu resources only when shown outside loading, cap shader size, add exact startup/first-present phase markers. Preserve watchdog. Preserve language coverage and historical shader oracle.

## Evidence

Host [run 43981461896](https://github.com/niakw/ProsperoEden-Encore/actions/runs/43981461896), job 133698714850: successful real Vulkan pipeline creation on llvmpipe, LLVM 20.1.2, cache disabled. Boot fragment 7499 words (29996 bytes), quick menu 8831 words (35324 bytes), 4931 slots, atlas 2209088 bytes as separate data. Host timings: 3 ms boot, 5 ms quick menu. This proves host pipeline creation, not rendered glyph correctness or PS5 timing. Touchpad host run 43981461973 passed. These runs precede the final trace-only adjustments; final PR head `5097e40b0e0c5df5e842f9892d1b5bb81cad558f` needs its own CI qualification. Native build and console retest pending. Check both games reach first guest frame and can return to the launcher normally; verify menu rendering afterwards.

## Other findings

`EDEN_CASE_FALLBACK status=missing added=0` on tested installation, although the inspected validated FTP archive contains `ui/box-art-fallback.tsv` and the nine typography resources. Resource deployment/visibility discrepancy tracked in #124; do not infer a missing archive entry or silently replace assets. NS2 size starts deferred; completion unobserved in short logs. Keep prior gameplay, performance, rendering and launcher issues open until actual validation.
