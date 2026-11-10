# R18/R23 — vendor provenance and external maintainers: bounded snapshot

**Date:** 10 November 2026. **Audited pin:** Encore `e4f6a825` (baseline), vendor `22b69d6053db41b74edac2633c012f925b84f69e`. **Only owner/source evidence, no upstream upgrade, no vendor change.**

## Source family boundaries: actual inventory

The pinned vendor root `sources/` contains **26 top-level source families**: boilerplate-setup-0, boilerplate, compiler-rt, eden-cpm, eden, encore-overrides, ffmpeg, fmt, harfbuzz, libwebp, opengl-imgui, opengl-mesa-26-2, opengl-nanovg, opengl-native-boilerplate, opengl-opengnm-psbc, opengl-opengnm, opengl-sokol, opengl-source, opengl-spirv-headers, opengl-vulkan-headers, ps5-fsr3-optical-flow, ps5-mesa, ps5-mihawkgen, ps5-payload-sdk-fork, ps5-vulkan-tools, zbic.

These are **source subtrees**, not 26 linked runtime libraries, not a cryptographic supply-chain validation of all downloaded packages. `tools/deps.json` has **22 fetch entries**; do not merge these two counts. The parallel `encore-active/` contains maintained adaptations and should be the only project-owned override location according to `docs/EDEN_OVERRIDE_SOURCE_OF_TRUTH.md`.

## Critical source-root comparison (Git SHA/Merkle, no download)

| Source root | Official pinned original | Vendor source tree | Result |
|---|---|---|---|
| Eden | [eden-emulator/mirror `5f142c79`](https://github.com/eden-emulator/mirror/tree/5f142c7926d0c7fcbbd0ce30794d72f638a43b2a) | `vendor/sources/eden` root `b7a1d7c4`; `src` tree `2ce268b3` | **35 modified source blobs** (9 kernel/HLE, 19 shader, 7 GPU/Vulkan), no added/deleted sources in scanned differing subtrees; exact paths [manifest](R18_VENDOR_EDEN_35_SOURCE_MUTATIONS_2026-11-10.json). Provenance/policy debt. |
| PS5 Mesa | [mihawk-99/PS5_Mesa `0b2d6d1`](https://github.com/mihawk-99/PS5_Mesa/tree/0b2d6d1a61d9bbf89cf8beb88a696144f67c61f8) | `vendor/sources/ps5-mesa` root `af7fd126` | Git tree roots differ **only by vendor-side `VENDOR-ORIGIN.json` added**. All same-name upstream source-tree entries have identical Git tree SHA. No detected Mesa source-file byte changes relative to that pinned commit. Native build **still** overlays 12 maintained RADV units separately and source copy provenance must be confirmed. |
| 24 other source roots | Source-specific pins, archives and dedicated installation scripts | Corresponding `vendor/sources/` subtrees | **Not all Merkle/linked checks completed** here. Manifest pin syntax and presence are not final object licence/SBOM proof. |

For Eden the full upstream `src` root differs **only** in the above three top-level directories (`core`, `shader_recompiler`, `video_core`), and all changed nested source directories were enumerated recursively without API truncation. This is a stronger and more precise provenance finding than a code search.

## Upstream/fork relevance register (no blind merge)

| Lineage | Verified public origin/status on 2026-11-10 | Use for Encore A/B |
|---|---|---|
| [Eden official mirror](https://github.com/eden-emulator/mirror) | Active; reference head `89d1a1cd` compared to pinned `5f142c79`, **155 commits ahead** | Primary C++ NS1 core/JIT/HLE/renderer upstream. [All titles](R23_EDEN_ALL_155_COMMITS_2026-11-10.json) and [file-diff snapshots](R23_EDEN_SEGMENTED_155_COMMITS_FILES_2026-11-10.json). Full semantic parity remains unqualified for bulk commits. |
| [Swordpdf/ProsperoEden](https://github.com/Swordpdf/ProsperoEden) | PS5 experimental fork, latest push seen 2026-10-18 | Highly relevant historical PS5 fixes: AudioIn `01e81e1`, RomFS `4f813a3`, RADV `1862764`, shader NaN `e34338d`. Each must be adapted to **actual** pinned/maintained source ABI, not imported wholesale. |
| [mihawk-99/PS5_Mesa](https://github.com/mihawk-99/PS5_Mesa) | Active, pushed Nov 9; pinned `0b2d6d1` and newer `7bd4aac` are **diverged** (128 newer-only vs 103 pinned-only commits in inspected comparison) | Driver-specific ABI/WSI/transfer and compiler review. **Never fast-forward** a diverged fork without per-unit tests, licence and PS5 device proof. |
| [mihawk-99/PS5_Vulkan](https://github.com/mihawk-99/PS5_Vulkan) | Active, pushed Nov 10; pinned `3f3ee69` vs newer `7f492b4`, **81 commits newer** in inspected comparison | Driver test harness and cross-subsystem evidence; do not confuse test-tool repo updates with a ready PS5 renderer update. |
| [Leuconoe/Ryubing](https://github.com/Leuconoe/Ryubing) | Ryubing mirror updated Nov 5 | C# Ryujinx-family architecture: conceptual HLE/IPC or behavior comparisons, **not** direct C++ source replacement. |
| [Synoptikon/Sudachi](https://github.com/Synoptikon/Sudachi) | Pushed May 2024 in inspected public metadata | Historical comparison only; not evidence of a currently maintained security fix stream. |
| [mpereiraesaa/prospero-win](https://github.com/mpereiraesaa/prospero-win) | Windows native-PS5-homebrew compatibility runtime, active | Conceptual platform/ABI observations only; different OS/runtime and unrelated to NS1 instruction correctness. |
| Citron / other Yuzu descendants | Original `citron-neo/emulator` lookup currently unavailable (404). Search returned `LeVonikke/Citron-NeoNex`, but lineage/official maintenance not verified | **Do not fabricate an official Citron comparator.** Record verifiable repository, license/commit and provenance before using candidate changes. |
| [zortos293/Lichii](https://github.com/zortos293/Lichii) and other NS2 implementations | Active NS2 emulation; separate NS2 optimization audit already owns them | **Explicitly excluded** from this NS1-specific upstream migration, except shared code reachability relevant to NS1 regressions. |

## Outstanding R18/R23 source and distribution gates

- Enumerate byte-drift and official source origin for the other 24 vendor source subtrees when their exact matching pins are established. Disambiguate wrapper-generated archives from immutable upstream trees.
- Review **actual staged/linked PS5 files and library names**, dependency ABI, source distributions and licences. The lack of explicit `nanovg`, `sokol`, `imgui`, `opengnm` names in `THIRD_PARTY_NOTICES.md` is an attribution **triage item**, **not** a proven legal violation; it depends on what is distributed/linked.
- For Mesa, obtain actual Meson command database and copied-source SHA attestation (`tools/install-vendored-radv.py`). A clean original Mesa snapshot does not imply correct upstream/maintained ABI once local overrides are applied.
- For Eden, resolve the **35 original-source mutations** by audited ownership, never delete active fixes silently or mutate `main`/`vendor` under an audit PR.
- For the 155 Eden commits, file-change lists are still capped for some big refactor windows; no assertion of exhaustive per-file behavior parity.

**Decision:** useful source-provenance and maintainer register, **not** a closed all-component compliance, runtime/security or full A/B audit. No code changes or PS5 build triggered by this research.
