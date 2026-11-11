# NS1 / R23 — 17 upstream runtime-semantic decisions still requiring real proof

**Freeze:** 11 November 2026. **Audit only** [PR #45](https://github.com/niakw/ProsperoEden-Encore/pull/45), canonical immutable register `r23/R23_EDEN_155_APPLICABILITY_2026-11-11.json`. Updated after pass26 #97 and #154 active native applet/FW23 gaps (ENCORE_AB_R23_SEMANTIC_SOURCE_PASS26_2026-11-11.md); previous passes are historical; generated from the exact 155-row catalogue with a manually reviewed priority / acceptance route per outstanding case. **No native source correction, no compiler/header or PS5 device attestation is inferred.**

## Every remaining case (no orphan or implicit close)

| # | Risk / owner | Official upstream change | Required source and behavioral exit |
|---:|---|---|---|
| 2 | P0 GPU Vulkan | `6a767ac43a08` [vulkan]EDS3 Depth Clamp Fixes and Async Shader Fixes (#4639) | Déterminer la vraie version de fixed_pipeline_state/renderer, comparer EDS3 et async shader, valider pipeline state cache + depth-clamp sur RADV |
| 3 | P1 ABI/toolchain | `d3ee883e538b` [*] fmt -> std::format, initial C++26 migration (#4677) | Comparer C++20 SDK vs C++26, fmt/format et conversions sur les vrais TU actifs; ne pas migrer en masse sans syntax/ABI |
| 6 | P0 mémoire/GPU | `bfa72a22a345` [core, video_core] Preserve GPU writes during NCE fault handling (#4604) | Comparer dirty page CPU/GPU et protections sur buffer_cache/word_manager réels, tests partial-page et écriture GPU simultanée; NCE ARM séparé |
| 7 | P1 dépendances/API | `83fde0738cc8` [common] nlohmann -> jacinth, httplib -> hydrocarbon, rework auto-updater UX (#4412) | Tracer les consommateurs JSON/HTTP/auto-update sélectionnés et SBOM, qualifier API/ABI avant remplacement nlohmann/httplib |
| 11 | P0 JIT | `35f0dd7c1ca0` [dynarmic] fix seven A32 and x64 defects (#4598) | Sept défauts A32/x64 indépendants, exacts emitters réellement compilés, tests instruction positifs/négatifs sous Zen2 |
| 18 | P1 Vulkan TIR | `d85005b2b27e` Fixed Civilization VII - added TIR mixed samples support (#4553) | Comparer mixed samples dans TextureCache et pipeline, image/MSAA Vulkan natif et tests depth/mixed |
| 19 | P1 HID/OSD | `873fde41d037` [common, controller] [AI] Controller assignment modes, Controllers tab, Steam Gamemode/Gamescope fixes (gyroscope, controller) (#4583) | Séparer Steam/SDL/Qt des vrais HID, réglages NPAD et fenêtre/renderer PS5; tester manettes, gyro, reconnexion |
| 35 | P1 shader/Vulkan | `3d3ed4b7d15b` [shader_recompiler, renderer_vulkan] draw sprites whose texture handle comes from a vertex attribute (#4566) | Valider propagation texture handle via vertex attribute, shader_info, IR Phi, Vk pipeline et golden shader |
| 41 | P1 CMake/JIT | `a845100bf098` [cmake] Cleanup dynarmic's CMake (#4365) | Comparer macros hôtes et liste exactes des objets x64; conserver W^X et détection de fonctionnalités CPU, prévenir sélection double |
| 54 | P0 vidéo/gel | `cbd4cf2d8ce9` [hle][core] Hang Freeze Fix - Video Fixes - Revert Microsleep (#4316) (#4525) | Tracer NVDEC, FS storage, microsleep et scheduler guest, tester boot/freezes et video decode |
| 58 | P1 shader IR | `0689f73147eb` [ir] resolve conditional Phi inputs when tracking bindless texture handles (#4551) | Tester résolution Phi bindless et chemins non dominants du graphe IR, compilation SPIR-V réelle |
| 72 | P1 GPU subgroup | `a594c8d60ef7` [shader_recompiler, vulkan, qcom, tu] Provide handling to missing shader subgroups on QCOM (#4508) | Séparer options QCOM/Turnip d'IR/SPIR-V partagé sur RADV, exiger caps Vulkan et SPIR-V validate |
| 94 | P0 sync GPU | `f273423b2b83` [buffer_cache] Simplify GPU fence synchronization and remove GPU buffer readback (#4477) | Protéger fences/invalidations, éviter readback supprimé, tester synchronisation GPU-CPU sur cache de buffers natif |
| 98 | P0 GPU uploads | `dbeb73ee0114` [video_core] cpu buffer fix + kepler uploads / maxwell macro dirty tracking fixes (#4473) | Comparer macro dirty Kepler/Maxwell, DMA pusher et invalidation buffer; tests uploads+relecture |
| 111 | P1 JIT callbacks | `9a30172e45fc` [dynarmic] Coalesce non-exclusive Write/Read fallback functions (#4158) | Qualifier changement API MemoryRead/MemoryWrite non-exclusive A32/A64 et interface C++/x64, tests tailles/watchpoints/exclusifs |
| 112 | P0 HID/AM IPC | `07f40d5cac63` [npad,hid,am] npad WriteEmptyEntry fix, hid function 551 stub, and applet PopOutData rework (#4442) | Tester WriteEmptyEntry, HID commande 551, PopOutData, ABI/handles et régression manette |
| 113 | P0 FS multicontenu | `3c38afad74c7` [fs] share parent resources with bundled programs (#4319) | Tester montage bundled programs et ressources parent/SaveDataFactory, permissions et title launch |

## Strict accounting and non-overlap

- **17/17** generic semantic cases have a concrete owner/test route above; this is **not 17/17 completed reviews**, because the required source owner comparisons/tests are still missing. An inventory row or code title cannot close a case.
- Separate ledgers: **31** verified native source gaps (including the confirmed **SSL** guest-facing HLE command omissions in pass21; these are not part of the 17 generic reviews) (not counted in 17), **8** PS5-specific scope/refactor/policy gates (not counted in 17), **17** changed header include receipts (not counted in 17), **7** C00–C06 release batches (0/7 PS5-qualified), and **26** vendor family provenance / archive / SBOM obligations.
- Baseline NS1 guest runtime shared with NS2 requires positive/negative NS1 test even if upstream issue was introduced for NS2 or Android. Non-PS5 backends are excluded only by actual current compiled owner and preprocessor/source evidence, never by commit title.
- PR #55 AM/HID, PR #54 FW23 cmd23, PR #52 CPU6/launcher and PR #46 old corrective candidates are **implementation candidates**, not proof of shipped fixes. The master audit must retain unchanged release gates until native ELF/PS5 testing passes.
- No new experimental mode or duplicate branch was created. No merge/rebase/vendor repin or production modification.
