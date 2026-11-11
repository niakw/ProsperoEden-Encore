# NS1 / R23 — 26 upstream runtime-semantic decisions still requiring real proof

**Freeze:** 11 November 2026. **Audit only** [PR #45](https://github.com/niakw/ProsperoEden-Encore/pull/45), canonical immutable register `r23/R23_EDEN_155_APPLICABILITY_2026-11-11.json`. Updated after pass21 #120/#149 moved to verified source gaps; generated from the exact 155-row catalogue with a manually reviewed priority / acceptance route per outstanding case. **No native source correction, no compiler/header or PS5 device attestation is inferred.**

## Every remaining case (no orphan or implicit close)

| # | Risk / owner | Official upstream change | Required source and behavioral exit |
|---:|---|---|---|
| 2 | P0 GPU Vulkan | `6a767ac43a08` [vulkan]EDS3 Depth Clamp Fixes and Async Shader Fixes (#4639) | Déterminer la vraie version de fixed_pipeline_state/renderer, comparer EDS3 et async shader, valider pipeline state cache + depth-clamp sur RADV |
| 3 | P1 ABI/toolchain | `d3ee883e538b` [*] fmt -> std::format, initial C++26 migration (#4677) | Comparer C++20 SDK vs C++26, fmt/format et conversions sur les vrais TU actifs; ne pas migrer en masse sans syntax/ABI |
| 6 | P0 mémoire/GPU | `bfa72a22a345` [core, video_core] Preserve GPU writes during NCE fault handling (#4604) | Comparer dirty page CPU/GPU et protections sur buffer_cache/word_manager réels, tests partial-page et écriture GPU simultanée; NCE ARM séparé |
| 7 | P1 dépendances/API | `83fde0738cc8` [common] nlohmann -> jacinth, httplib -> hydrocarbon, rework auto-updater UX (#4412) | Tracer les consommateurs JSON/HTTP/auto-update sélectionnés et SBOM, qualifier API/ABI avant remplacement nlohmann/httplib |
| 10 | P1 JIT debug | `656cdd948e09` [dynarmic] Fix guest debugging with gdb-stub (#4620) | Tester x64 Dynarmic invalidation et gdbstub/watchpoints guest, comparer contexte en exécution |
| 11 | P0 JIT | `35f0dd7c1ca0` [dynarmic] fix seven A32 and x64 defects (#4598) | Sept défauts A32/x64 indépendants, exacts emitters réellement compilés, tests instruction positifs/négatifs sous Zen2 |
| 18 | P1 Vulkan TIR | `d85005b2b27e` Fixed Civilization VII - added TIR mixed samples support (#4553) | Comparer mixed samples dans TextureCache et pipeline, image/MSAA Vulkan natif et tests depth/mixed |
| 19 | P1 HID/OSD | `873fde41d037` [common, controller] [AI] Controller assignment modes, Controllers tab, Steam Gamemode/Gamescope fixes (gyroscope, controller) (#4583) | Séparer Steam/SDL/Qt des vrais HID, réglages NPAD et fenêtre/renderer PS5; tester manettes, gyro, reconnexion |
| 32 | P1 Dynarmic ABI | `2bec66c09226` [dynarmic] Remove redundant configure struct (#4485) | Contrôler suppression de config struct sur x64 et API callbacks, sources et headers sélectionnés, JIT/ABI |
| 35 | P1 shader/Vulkan | `3d3ed4b7d15b` [shader_recompiler, renderer_vulkan] draw sprites whose texture handle comes from a vertex attribute (#4566) | Valider propagation texture handle via vertex attribute, shader_info, IR Phi, Vk pipeline et golden shader |
| 41 | P1 CMake/JIT | `a845100bf098` [cmake] Cleanup dynarmic's CMake (#4365) | Comparer macros hôtes et liste exactes des objets x64; conserver W^X et détection de fonctionnalités CPU, prévenir sélection double |
| 46 | P1 HLE triche | `69665063a9b1` [cheats] add runtime cheats toggles with master code support (#4334) | Examiner le loader de cheats NS1/master code et ses écritures mémoire sur core, conformité comportementale positive/négative |
| 54 | P0 vidéo/gel | `cbd4cf2d8ce9` [hle][core] Hang Freeze Fix - Video Fixes - Revert Microsleep (#4316) (#4525) | Tracer NVDEC, FS storage, microsleep et scheduler guest, tester boot/freezes et video decode |
| 58 | P1 shader IR | `0689f73147eb` [ir] resolve conditional Phi inputs when tracking bindless texture handles (#4551) | Tester résolution Phi bindless et chemins non dominants du graphe IR, compilation SPIR-V réelle |
| 68 | P0 RO/mémoire | `aaa0bcb9bf56` [patcher, ro, settings] runtime tls patch (#4492) optimization and nuke toggle (#4502) (#4523) | Tester SetNroPerms inconditionnel et permissions LoadNro/UnmapNro sous x64, indépendamment du TLS patch NCE ARM |
| 72 | P1 GPU subgroup | `a594c8d60ef7` [shader_recompiler, vulkan, qcom, tu] Provide handling to missing shader subgroups on QCOM (#4508) | Séparer options QCOM/Turnip d'IR/SPIR-V partagé sur RADV, exiger caps Vulkan et SPIR-V validate |
| 80 | P1 shader GPU | `67bada77f8a4` [video_core] Skip fragment shaders with known issues on non-NVIDIA drivers (#4503) | Classifier la suppression conditionnelle de fragment shaders non-NVIDIA et ses risques de trous de rendu; artefact radar |
| 94 | P0 sync GPU | `f273423b2b83` [buffer_cache] Simplify GPU fence synchronization and remove GPU buffer readback (#4477) | Protéger fences/invalidations, éviter readback supprimé, tester synchronisation GPU-CPU sur cache de buffers natif |
| 97 | P0 AM/présentation | `99bf8cf51afb` [am, renderer_vulkan] Fix overlay darkening and SGSR black screen on applets (#4475) | Comparer window system/NPAD/present layer; tests overlay applets, écran noir, blending/SGSR |
| 98 | P0 GPU uploads | `dbeb73ee0114` [video_core] cpu buffer fix + kepler uploads / maxwell macro dirty tracking fixes (#4473) | Comparer macro dirty Kepler/Maxwell, DMA pusher et invalidation buffer; tests uploads+relecture |
| 111 | P1 JIT callbacks | `9a30172e45fc` [dynarmic] Coalesce non-exclusive Write/Read fallback functions (#4158) | Qualifier changement API MemoryRead/MemoryWrite non-exclusive A32/A64 et interface C++/x64, tests tailles/watchpoints/exclusifs |
| 112 | P0 HID/AM IPC | `07f40d5cac63` [npad,hid,am] npad WriteEmptyEntry fix, hid function 551 stub, and applet PopOutData rework (#4442) | Tester WriteEmptyEntry, HID commande 551, PopOutData, ABI/handles et régression manette |
| 113 | P0 FS multicontenu | `3c38afad74c7` [fs] share parent resources with bundled programs (#4319) | Tester montage bundled programs et ressources parent/SaveDataFactory, permissions et title launch |
| 144 | P1 FG/présentation | `099547b3f457` [android] Add LSFG UI to quick settings (#4393) | Séparer UI Android et code Vulkan/LSFG partagé; comparer avec R09/FG propriétaire, tests combos et fallback |
| 154 | P0 HLE FW23 | `e7a96c7907fb` [hle] Firmware 23.0.0 (#4390) | Vérifier system_version, SVC et signatures IPC FW23 sur code réellement choisi, tests anciens et nouveaux FW |
| 155 | P1 postprocessing | `ed566919f468` [vulkan, android] Add feature of post-processing shaders on Android (#4348) | Séparer ReShade/Qt/Android des modifications partagées path_util/renderer Vulkan, vérifier pipeline natif sans dupliquer les shaders |

## Strict accounting and non-overlap

- **26/26** generic semantic cases have a concrete owner/test route above; this is **not 26/26 completed reviews**, because the required source owner comparisons/tests are still missing. An inventory row or code title cannot close a case.
- Separate ledgers: **24** verified native source gaps (not counted in 26), **8** PS5-specific scope/refactor/policy gates (not counted in 26), **17** changed header include receipts (not counted in 26), **7** C00–C06 release batches (0/7 PS5-qualified), and **26** vendor family provenance / archive / SBOM obligations.
- Baseline NS1 guest runtime shared with NS2 requires positive/negative NS1 test even if upstream issue was introduced for NS2 or Android. Non-PS5 backends are excluded only by actual current compiled owner and preprocessor/source evidence, never by commit title.
- PR #55 AM/HID, PR #54 FW23 cmd23, PR #52 CPU6/launcher and PR #46 old corrective candidates are **implementation candidates**, not proof of shipped fixes. The master audit must retain unchanged release gates until native ELF/PS5 testing passes.
- No new experimental mode or duplicate branch was created. No merge/rebase/vendor repin or production modification.
