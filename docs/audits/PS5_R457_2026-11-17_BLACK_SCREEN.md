# PS5 R457 — shared Vulkan startup regression (2026-11-17)

Status: P0, console reproduction confirmed; candidate host/native qualification complete; PS5 retest pending. No raw user logs included.

## Reproduction

- PS5 firmware 13.60, executable source `42eb93692779a0e7a50c5dbdb8bad1e3d815c1da`, vendor `ffa519db0f68fb0d5d2acf791e381c898a34a175`, native run [43974660874](https://github.com/niakw/ProsperoEden-Encore/actions/runs/43974660874).
- FC27 NS1 `0100C49025D3E000`: loading cover, then persistent black screen; GL loader stops after 59 frames.
- Mario Kart World NS2 `0400C3F00006E000`: longer loading with moving dots, then persistent black screen; GL loader stops after 2452 frames.
- Both: core initialization and NSO loading reached; EGL scanout released; Vulkan surface creation returns success, including final `vkCreateDisplayPlaneSurfaceKHR`; no `core_loaded`, `game_loaded` or `guest_run_begin`. Input polls continue. Exit request during loading triggers the existing ten-second stop watchdog, and the next launch confirms an exhausted stop timeout. No new crash report. Do not classify as a guest GPU failure or prove a particular blocked Vulkan call from these logs alone.
- Both result TSVs are empty and both stop-limit files report one exhausted stop. At `core_initialized`, the largest free direct-memory block remains about 8 GiB, so this capture does not reproduce the earlier NS2 backing-allocation exhaustion.

## Regression boundary

- Hardware retest from 2026-11-14 at engine `cbfab557e1c8cd459d67c6afae7353ca20000ab3`, native run [43586398071](https://github.com/niakw/ProsperoEden-Encore/actions/runs/43586398071), reached `guest_run_begin` for MKW/Bananza; FC27 progressed into gameplay. The current failure is therefore an earlier shared-startup regression, not merely the historical NS2 first-frame stall.
- Typography PR [#257](https://github.com/niakw/ProsperoEden-Encore/pull/257) merged at `3963ba8e2e6e8c56df3b1c70bfd5ddaf1d763bb6` on 2026-11-16 21:24:55 UTC. Tested native run 43974660874 began at 22:55:48 UTC and contains that merge.
- Comparing #257's pre-merge base `b8c9194f5946ed7235321b193a59145d6c451ac7` to tested `42eb936...` yields 12 commits; relevant runtime deltas are overwhelmingly typography/quick-overlay/HUD. Comparing the #257 merge itself to `42eb936...` shows no subsequent Vulkan-renderer/HUD shader runtime change. This materially strengthens #257 as the primary regression candidate without proving the exact PS5 blocked call.

## Investigation and candidate

Reviewed the pinned vendor renderer initialization and storage buffer descriptor helpers against the engine renderer. Upstream Eden issues #150 (initialization error), #414 (instance-extension race), #161 (EDS device loss) do not establish an identical cause. Recent PS5 RADV traces also continue normally after the same `ac_compute_device_uuid's output is based on invalid pci bus info.` warning, so that message is not treated as the stop point. See also [Khronos constant data sample](https://docs.vulkan.org/samples/latest/samples/performance/constant_data/README.html). No vendor change is justified by current evidence; vendor main is one workflow/security-only commit ahead of the tested pin.

The previous Unicode implementation embeds 4931 raster glyphs in the same fragment shader first compiled by loading presentation: 641640 SPIR-V words (2566560 bytes), even when the quick menu is hidden. This is a strong regression candidate, not a proven hardware root cause. [P0 issue #263](https://github.com/niakw/ProsperoEden-Encore/issues/263); [candidate PR #264](https://github.com/niakw/ProsperoEden-Encore/pull/264): split loading/FPS and Unicode menu pipelines, keep glyph atlas in immutable storage buffer data, lazily create menu resources only when shown outside loading, cap shader size, add exact startup/first-present phase markers. Preserve watchdog. Preserve language coverage and historical shader oracle.

## Host qualification

Final candidate head is `f9da701114dd7dbb5a70c00535d061c390e050fc`. Eight exact-head workflows are green: vendor receipts, vendor pin, native MSAA host pair, touchpad overlay, isolated Vulkan HUD rebuild, internal dependencies, security analysis and sharded P0–P4 qualification.

The final isolated shader witness reports:

- 4931 slots and 2209088 bytes of immutable atlas data outside boot SPIR-V.
- `vert_words=275`, boot `frag_words=7499`, Unicode-menu `quick_words=8831`.
- Boot shader has no descriptor set; Unicode menu uses the bounded storage-buffer descriptor.
- Real llvmpipe pipeline creation: 2 ms boot and 4 ms Unicode menu on the final pre-native candidate.
- Native Vulkan Task/Mesh C++20 syntax gate passed.

A first native qualification attempt, run 43983921172, was correctly blocked before native build by the local neutral-CI-label policy because the isolated host workflow step used the human-facing word `Mesa`. No runtime code failed. Commit `f9da701...` changes only that label to `Vulkan`; the same aggregate gate then reports `CI_MESSAGES_NEUTRAL_PASS workflow_steps=488 core_test_messages=16`.

## Native PS5 build qualification

Full native run [43985261580](https://github.com/niakw/ProsperoEden-Encore/actions/runs/43985261580) completed successfully.

The run source SHA is `b4e99818ae53a95f7c3597771e7ed52750287261`. It is the exact candidate `f9da701...` plus one transient workflow-trigger line in `.github/workflows/build-040-zbic.yml`; compare shows no other changed file. The PR branch was reset to clean head `f9da701...` after checkout. Runtime engine/vendor source is therefore the candidate source; no trigger commit remains in the PR.

Native receipts:

- vendor submodule: `ffa519db0f68fb0d5d2acf791e381c898a34a175`
- unstripped linked `eboot.elf`: 81,917,056 bytes, SHA-256 `879727d7ed53bec9afc98b396d74d859410e9d6706fe48622e6591286872bfe8`
- staged `eboot.bin`: 79,835,455 bytes, SHA-256 `7a546c4e94f3c36a05c59310ec4dadf8e18a6a6b2094b18ab206e9839498e1bb`
- staged application: 200 files, current launcher/runtime markers present
- FTP artifact `Eden-Encore-PS5-FTP-PPSA99008`, artifact ID `14285118877`, artifact digest SHA-256 `3a119f4eb7ca7bbd531d36d9a72c22cec1bcde41f5b0dfe26e1714b757477e0e`
- release/symbol bundle `Prospero.Eden-Encore-release`, artifact ID `14285248735`, artifact digest SHA-256 `11c874644ef3b838481e8b7f223e8dc394377583aeb27bcaab6becbb2eda6807`
- deterministic release ZIP `Prospero.Eden-Encore-R457.zip`: SHA-256 `3fc9e555c1173024a147ab42077d037cec3ec000646b597a00a3629363aeebbd`
- deterministic FTP ZIP `Eden-Encore-R457-b4e99818-FTP-PPSA99008.zip`: SHA-256 `c6f258033a40714d7b61e03f7ede66780328e2dca8e4ff5a5f384213d1f6bfb5`
- crash provenance binds the same-run unstripped ELF, staged eboot and link map; it correctly leaves `confirmed_same_console_binary=false` and `native_ps5_execution_verified=false` until hardware test.

Both downloaded Actions artifacts were independently ZIP-tested after the run: no compressed-data errors, correct `PPSA99008/` root, matching staged eboot hash.

### Non-blocking native-build diagnostics

Do not hide these diagnostics:

1. Mesa emits `cannot auto-detect -mtls-dialect when cross-compiling, using compiler default`. Upstream Mesa deliberately skips this runtime probe when cross-building because it is an optimization, not a correctness prerequisite.
2. SDL3's FreeBSD-target configuration probes optional `libinotify` and reports it not found; configure, native build, link and staged validation all succeed without it.
3. GitHub's artifact download action emits Node `[DEP0005] Buffer() is deprecated`. This is an upstream `actions/download-artifact` / `@actions/artifact` issue, not Encore runtime code; the downloaded digest still matches exactly.
4. Mesa `u_process.c` emits a compile-time note that per-application configuration will not work for the target OS version. This is upstream/platform configuration behavior and did not prevent RADV build/link.
5. The numerous `PSBC ... failure`, JIT sparse allocation failures and `EXPECTED FAILURE` lines are negative-path harness cases followed by explicit PASS results; they are not native build failures.

Track 1–4 as maintenance warnings, but do not delay P0 hardware qualification on them.

## Hardware follow-up — 2026-11-17 00:44 capture

Tested installed source `b4e99818ae53a95f7c3597771e7ed52750287261` from native run 43985261580, vendor `ffa519db0f68fb0d5d2acf791e381c898a34a175`, firmware 13.60.

### FC27 NS1

The shared startup regression is no longer reproduced: FC27 reaches gameplay. User reports smoother overall behavior but remaining P1 failures are unchanged or only partially improved:

- EA intro: black picture, audio present;
- main menu: no guest text;
- first-match severe hitch, then stabilization;
- HUD text initially absent and appearing late;
- refreshed match-clock digits disappear;
- pause-menu text appears with missing letters;
- player-shirt names absent;
- stadium-seat texture can render green.

This hardware result qualifies #264 as a startup-regression repair candidate for NS1, not as a complete FC27 fix. R1 source `5629395324ff65c98b50c44f35f2142a4a92654a`, recalled by the tester to render FC27 text, uses the same authored FC27 profile tuples as current Encore and predates the selected Eden #4503 non-NVIDIA fragment-shader drop. Vendor #180 tests the newer Lichii/Eglantine broadcast/select fragment-shuffle fallback on PS5 instead of discarding the complete matching guest shader. Hardware effect remains unqualified. Intro video stays a separate NVDEC/VIC track; selected source already carries bounded `EDEN_NVDEC_STAGE` decode/VIC input/VIC output witnesses for the next FC27 log.

### NS2 memory gate

Both Bananza and MKW fail before the historical guest execution/first-frame paths:

`Direct allocation failed: rc=80020023 bytes=4297064448 limit=13019119616`

followed by `Backing allocation: Cannot allocate memory`. The requested direct allocation is 4098 MiB (4 GiB guest layout plus one 2 MiB span) while the immediately preceding native memory diagnostic reports the largest contiguous direct-memory extent as 3822 MiB. This is a contiguous-allocation mismatch, not proof of total PS5 RAM exhaustion.

Upstream ProsperoEden #156 / commit `9ce26e650e26112d958f6db4b20d93260de77825` demand-backs ordinary guest memory rather than taking the whole 4 GiB block at startup. Encore already had a stricter transactional 2 MiB sparse owner but admitted it only for exactly 12 GiB. Engine #265 adapts the upstream guest-backing principle to that existing owner for ordinary 4+ GiB non-fastmem layouts, with bounded physical residency and fail-closed dense fallback. Exact host/CMake/syntax/P0-P4 qualification is green; native build and console test remain required.

Integration #266 combines #264 + #265 + vendor #180 strictly for hardware validation. It must not be merged merely because CI/build is green.

## Required PS5 acceptance

Do not merge or close #263/#264 from the green build alone.

1. Install the FTP artifact from run 43985261580.
2. FC27 NS1 `0100C49025D3E000`: require transition through Vulkan loading to a real guest frame, then normal return to launcher.
3. MKW NS2 `0400C3F00006E000`: require progress at least to the historical `guest_run_begin` boundary and observe whether the existing first-guest-frame stall remains separately.
4. Open the touchpad quick menu once after successful startup to exercise lazy Unicode-atlas creation, then close it normally.
5. Exit the game and application normally; no ten-second stop timeout, SIGSEGV or forced restart.
6. If either title still blocks, preserve the new logs. The last `EDEN_VULKAN_BOOT stage=...` marker now distinguishes device enumeration/creation, allocator, swapchain, present-manager, renderer-member construction, loading-frame acquisition/blit/HUD flush and first present.

## Other findings

`EDEN_CASE_FALLBACK status=missing added=0` on the previously tested installation, although the inspected validated FTP archive contains `ui/box-art-fallback.tsv` and the nine typography resources. Resource deployment/visibility discrepancy tracked in #124; do not infer a missing archive entry or silently replace assets. NS2 size starts deferred; completion unobserved in short logs. Keep prior gameplay, performance, rendering and launcher issues open until actual validation.
