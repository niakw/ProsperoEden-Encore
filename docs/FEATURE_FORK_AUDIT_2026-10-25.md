# Eden Encore — isolated feature branch audit (2026-10-25)

Branch: `feat/graphics-network-achievements`, forked at `366104db3360018eeeee3605ec60eeb1fd4bf31b`.
The acceptance branch `dev/ps5-sparse-jit` remains authoritative for F01–F06/F07.
**Nothing in this branch is an accepted gameplay or firmware-13.60 feature.**

## Rules before enabling any feature

- Every feature is opt-in, off by default, with safe one-session fallback.
- Do not transplant another fork's entire `headless/CMakeLists.txt`, generated Vulkan unit, PS5 privilege or networking setup. Preserve Encore's selected sources/overrides, provenance checks and F01–F06 exit evidence.
- Bench native memory, startup time, CPU/GPU frametime, displayed FPS, real emulation FPS, HDR/HUD correctness and controller latency separately. A synthetic frame must never be counted as emulated guest progress.
- Do not download opaque executable DLLs or proprietary model weights into a PS5 package. Check licences for source, model weights, shaders and bundled upstream dependencies independently.
- Release/build integration only after native PS5 link, sanitizer test, fast gate, full source preflight, package provenance, and on-device feature-specific checks.

## Source review / cherry-pick candidates

| Priority | Repository/commit | Relevance | Required adaptation / go-no-go |
| --- | --- | --- | --- |
| P0 | [Swordpdf/ProsperoEden `e34338d`](https://github.com/Swordpdf/ProsperoEden/commit/e34338dd6a538b37b32fd596c496abc15df4418a) | guard non-finite pixel shader colour | actual change only in CMake selection: audit owned dependency source and existing Encore coverage; do not import CMake wholesale |
| P0 | [Swordpdf `1862764`](https://github.com/Swordpdf/ProsperoEden/commit/18627649ca7f72fcc7e3959bdac8d27d8f68fcf9) | split long RADV command streams around transfers/barriers | compare against Encore's pinned Mesa/RADV build patches; validate command ordering, barriers and frame pacing |
| P1 | [Swordpdf `1390bf5`](https://github.com/Swordpdf/ProsperoEden/commit/1390bf51fef17554863e53d28b62ad684fb3c1ab) | sparse GPU address-table reservation | test overlap with Encore's sparse guest address logic and PS5 commit budget before adoption |
| P1 | [Swordpdf `650306c`](https://github.com/Swordpdf/ProsperoEden/commit/650306c9fd4b309720e87b58b2e5f8311f02badc) | Vulkan MihawkGen experimental neural frame generation | real PS5-native compute candidate; requires weights licence, API/device capability, storage layout, retirement/fences, shader/HUD separation, latency & A/B |
| P1 | [Swordpdf `23e0424`](https://github.com/Swordpdf/ProsperoEden/commit/23e0424149c72984fcf61e83aa9928a21fac0a7f) | per-game speed limiter | distinguish emulation speed (game clock) vs visual frame-rate cap; preserve audio/HID cadence |
| P2 | [Swordpdf `47cce6b`](https://github.com/Swordpdf/ProsperoEden/commit/47cce6bb7f081fb634bc6db85e792b1804a6bafa) and [`da39bc4`](https://github.com/Swordpdf/ProsperoEden/commit/da39bc4fdcaa88b3b02a223aec756555e3be2cf0) | game folder/updates/DLC and mods/cheats | verify no regression to Encore's compressed-container, ExeFS and safe-storage paths |
| P2 | [PS5SX2 `969cf71`](https://github.com/Swordpdf/PS5SX2/commit/969cf716104e1e5c5da0a0e6b6ab69f6b2b6f624) | parallel glyph atlas + boot-time profiling | profile Encore launcher actual text shaping/gl context before porting; unrelated PS2 code is not drop-in |
| P2 | [PS5SX2 `2b533b1`](https://github.com/Swordpdf/PS5SX2/commit/2b533b1e10e7fe32146a9cb4ab4a9aca0bcfb969) | cached box covers, asynchronous prefetch, texture packs | compare with LaunchBox selection-only/persistent cache to prevent redundant downloads, memory spikes or slow navigation |

Do not infer a fix from a commit title: inspect patch, current owner, build selection and replacement provenance. Keep upstream commits in a review ledger, not merged blindly.

## Graphics feasibility

- **FSR 3.1/3.1.6**: primary open, Vulkan-capable research option; spatial upscale and frame interpolation must be independently toggleable. AMD's API needs consistent frame pacing, history and for high-quality frame generation depth/motion inputs. It is NOT a plug-in replacement for FXAA/FSR1, and 30-to-60 *displayed* FPS does not fix a stalled guest CPU or 30 Hz input cadence. Reference: https://gpuopen.com/fidelityfx-super-resolution-3/ and https://github.com/GPUOpen-LibrariesAndSDKs/FidelityFX-SDK.
- **MihawkGen**: already PS5-adapted in Swordpdf through `mihawkgen.cpp`, `mihawkgen_bridge.h`, `vulkan_mihawkgen.inc`, but remains unqualified in Encore; ensure no collisions with Vulkan frame-present ownership and no generated frames overwrite HUD freshness.
- **Lossless Scaling/LSFG**: existing fork candidate may depend on a proprietary user-supplied library. No shipping of third-party proprietary binaries; benchmark realistically.
- **NVIDIA/DLSS5 PC tools are NOT PS5 native DLSS**. `Swervegod1/dlss5-for-ps5` explicitly processes Remote Play video on a PC browser; `maanHimself/OpenDLSS-NR` uses NVIDIA PTX/FP8 for its fast Vulkan path and user-supplied weights, and states it is not an upscaler; `jlrouzies-fr/DLSS5-Feeder` depends on PC ReShade/NVIDIA NGX/RTX. `rakanki911/DLSS5-Swapper` was not accessible via the connected GitHub API at audit time (404). `Nukem9/dlssg-to-fsr3` is a compatibility path for PC DLSS frame generation calls, not native PS5 guest Vulkan integration.
- **Three displayed counters**: guest/emulated FPS, original presented FPS, interpolated displayed FPS. Keep real game speed and latency visible, otherwise disable frame generation.

## Private multiplayer architecture

Swordpdf source: [guide](https://github.com/Swordpdf/ProsperoEden/blob/main/docs/MULTIPLAYER.md),
[implementation log](https://github.com/Swordpdf/ProsperoEden/blob/main/docs/MULTIPLAYER_IMPLEMENTATION.md),
`headless/multiplayer.*`, `multiplayer_validation.h`, packet/sockets/LDN bridges.

- Start with **opt-in private-room client** to independently operated Eden `eden-room` server, default offline; game must have a Local Wireless mode. Not Nintendo Online or universal LAN.
- Import only network/LDN plumbing with bounded protocol lengths, 1 MiB packet limit, bounded queues, safe teardown, no network calls on render thread and explicit offline fallback.
- Existing Swordpdf evidence: PS5 firmware 6.02 guest wireless lobby, host peer discovery/connect/sync and UDP traffic, not a complete two-game match. PS5 DNS hostname lookup failed in one case while numeric IPv4 passed; do not promise all firmware or Tailscale support.
- Threats before merging: Saved room password is documented as **plain text** by upstream; do not copy that default. Prefer session-only secrets, optional explicit persistent opt-in with secure storage if available; never log endpoints, passwords or raw packets.
- Keep diagnostics, timeouts, network disconnect and shader/game progress independent. Require test with two actual game instances before advertising multiplayer support.

## Switch local trophy service

- `cyork95/achievtrack` is MIT-licensed, browser-based **manual** progress tracking with AI-authored Switch achievements. It is not a source of objective in-game unlock signals and cannot certify game events.
- Proposed separate module/repository: import a per-title catalog keyed by **16-hex-character Switch title ID** with locale, trophy identifier, goal description, evidence type, image and version. Never treat an automatically generated description as an earned trophy.
- Two separate milestones: (1) optional **manual/local-only** progress in Encore with explicit attribution; (2) reliable **event-driven unlocks** only for titles for which safe HLE/game observation is validated (e.g. title-specific memory watcher and stable version-bound address; never assume universal offsets). Unverified games stay manual.
- Generate a skeleton list for an installed game library using title IDs. A universal game catalog must come from a licensed and versioned metadata source, not fictional objectives; prefer a separate `switch-trophies` repository so emulator native code remains lean.
- The linked [community Badges spreadsheet](https://docs.google.com/spreadsheets/d/1t_XAcUTusrkPl6ln2mabd6MznbIHQGA9FfrzXcQESzc/edit) is a **contribution template** (GTA III example plus a blank GAME tab), not a complete machine-readable database. It requests title ID, game name and game version. Preserve version per trophy ruleset; do not scrape or publish its user submissions without permission.
- [NinBadges discussion](https://gbatemp.net/threads/ninbadges-nintendo-switch-achievements-system.671476/) and community notes describe an offline-oriented project, not an approved emulator integration contract. Avoid assuming its memory watchers work across game versions.
- Use local persistent storage under the user's data root, atomic saves, no cloud account requirement, opt-in popup sounds and rate limits. Never present this as official Nintendo or PSN trophies.

## Cleanliness / source consistency audit steps

1. Re-run existing `tools/ci/check-repo-hygiene.py`, `check-active-source-inventory.py`, `check-vendor-consolidation-debt.py`, `check-eden-optimization-coverage.py` on **a separate feature SHA**.
2. Audit CMake compilation ownership, vendor overrides and generator output for duplicated compiled units, orphaned source and stale pin/checksum; do not flatten or delete vendor trees without dependency proof.
3. Check UI/media fallback layering, controlled WebP decoding, source URL quotas, cache eviction and allocator bounds with selection-only LaunchBox downloads.
4. Check no personal data/tokens/test PS5 IPs in tracked files and logging; preserve legal attribution.
5. Benchmark/validate each opt-in independently before merge; base FC27 firmware-13.60 session results govern F07 only, not speculative feature acceptance.

## Exit gate per feature

A design or source audit is **not** an implemented feature.
For each candidate record its upstream SHA, exact target files, licence, code owner, feature toggle, reproducible native build, host/sanitizer witnesses, PS5 performance/latency/fidelity comparison and rollback decision.
