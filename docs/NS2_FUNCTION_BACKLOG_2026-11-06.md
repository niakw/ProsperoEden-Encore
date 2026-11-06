# Eden Encore — fonctions restantes P0 à P4

**État audité le 6 novembre 2026 — `main a08d13a`, `vendor aa58e07`.** Liste opérationnelle complémentaire à la [roadmap #15](https://github.com/niakw/ProsperoEden-Encore/issues/15) et à la [matrice de clôture P0–P4](P0_P4_EXIT_MATRIX_2026-11-06.md). Les emplacements et les états ci-dessous sont des constats de source **sur cette paire de commits** ; les nouvelles CI et toute évolution de source demandent une requalification. **Aucune preuve sur console n'est requise ici : elle appartient exclusivement à P5.**

## Comment lire le backlog

- **Implémenté / à qualifier** : ne pas réécrire la fonction ; exécuter le test pertinent sur le SHA final.
- **Partiel prouvé** : chemin fonctionnel existant, mais certaines formes d'entrée sont refusées ou n'ont pas de preuve de bout en bout. Vérifier qu'elles sont effectivement dans l'ABI requise avant de développer.
- **Manque conditionnel avéré** : un chemin du code lance explicitement `NotImplementedException` ou `ResultNotImplemented`, sans preuve qu'un titre NS2 ait besoin de ce cas. Ne pas confondre **cas volontairement non pris en charge** et **fonction manquante obligatoire**.
- **Décision de périmètre** : manque de support possible, mais dépend des capacités NVN/du GPU émulé et des exigences réelles du titre. Ne pas simuler ni bricoler un fallback par jeu.
- **Clôture hôte** : seul un résultat reproductible et une CI verte sur la même paire `main` / `vendor` clôturent le critère ; les tests PS5 sont P5.

## P0 — architecture et CI

| ID | Élément exact | État et action vérifiable | Priorité |
|---|---|---|---|
| **O01** | `headless/CMakeLists.txt`, `headless/vulkan.cmake`, sources `encore-active` | **P0.2 : fermé côté architecture.** Moteur natif unique, CMake et rasterizer Vulkan maintenus. **P0 global :** vérifier Core fast gate, Source preflight, NS2 guards, compilation/validation SPIR-V, preview et sous-module sur le **même** SHA, corriger toute CI rouge. | P0 |

## P1 — boot, mémoire, IPC, régressions NS1

| ID | Fonction/propriétaire source | État de source ; action pour fermer le point | Priorité |
|---|---|---|---|
| **H01** | [`Process::Run`](../vendor/encore-active/ns2-runtime/process/core/hle/service/os/process.cpp), propriétaires [`loader.cpp`](../vendor/encore-active/ns2-runtime/metadata/core/loader/loader.cpp), [`nso.cpp`](../vendor/encore-active/ns2-runtime/metadata/core/loader/nso.cpp) | **Implémenté / audit de contrat P1.1.** Admission KProcess et propriétaires ExeFS/NSO présents. Consolider les tests hôte de parcours formats, NPDM, TitleID, updates, DLC, firmware/keys, échecs de chargement. **Ne pas exiger le PC invité mesuré sur PS5 avant P5.** Aucune fonction loader entière déclarée absente à partir de ces seuls fichiers. | Haute |
| **H02** | [`nvhost_as_gpu::MapNative4K`, `ReserveNativeSparse4K`, `RemapNativeSparse`, `ReleaseNativeSparse4K`, `UnmapNative4K`, `ModifyNativeKind`](../vendor/encore-active/ns2-runtime/nvdrv_as/core/hle/service/nvdrv/devices/nvhost_as_gpu.cpp) | **Implémentées / audit négatif P1.2.** GMMU 49 bits, pages 4 Kio, droits et rollback : vérifier les transactions multi-étapes, sources physiques, alignements, OOM et remaps disjoints, sans invoquer une VRAM réelle PS5. | Haute |
| **H03** | [`IGpuWorker::CreateSparseRegion`](../vendor/encore-active/ns2-runtime/gpu_session/core/hle/service/am/service/gpu_worker.cpp) et `IGpuWorker::Remap...` | **Partiel P1.2/P1.3.** Traitement de `page_shift=12`, modes d'allocation et réservations présentes, retour `ResultNotImplemented` sur d'autres entrées. Recenser les variantes **définies** par le protocole puis implémenter celles qui doivent fonctionner ; refus légitime pour les valeurs inconnues. | Haute |
| **H04** | [`GraphicsSupervisor::Encoding`, `MaxResolution`, endpoints`](../vendor/encore-active/ns2-runtime/graphics_supervisor/core/hle/service/am/service/graphics_supervisor.cpp) | **Révision sémantique P1.3.** `Encoding` accepte un cas précis `0x14` après validation d'un client ; auditer sa correspondance avec le protocole et les handles. `MaxResolution` utilise le vrai service VI et non un mode 720p fictif. Ne pas annoncer une prise en charge complète des commandes inconnues. | Haute |
| **H05** | [`IGraphicsVideoDecoderSession::Configure`](../vendor/encore-active/ns2-runtime/video_decoder/core/hle/service/am/service/graphics_video_decoder_session.cpp), `Nx2VideoDecoder` | **Partiel/conditionnel P1.3.** VP8/VP9/AVC/AV1/HEVC sont routés vers le décodeur réel s'il s'ouvre ; codecs inconnus refusés. Finaliser la matrice de commandes, handles, fin de flux, buffers et erreurs selon le SDK réellement requis. | Moyenne |
| **H06** | Services GPU/HLE `gpu_session.cpp`, `gpu_worker.cpp`, `graphics_supervisor.cpp` | **Audit IPC P1.3.** Plusieurs `ResultNotImplemented` demeurent. Classer par **commande, structure d'entrée, retour/handles, droit d'accès et besoin effectif**, puis implémenter les commandes obligatoires. Ne pas compter tous les retours négatifs comme autant de bugs. | Haute |
| **H07** | Tests conservant Maxwell/NS1 (`tools/ns2/qualify_host_batch.py`, suites JIT/ABI/Cache) | **Qualification P1.4.** Exécuter le lot complet de témoins NS1/source/mémoire/ABI sur un couple final propre ; pas de FC27/BOTW réel exigé avant P5. | Haute |

## P2 — GPU, mémoire globale, shaders et synchronisations

| ID | Fonction/propriétaire source | État de source ; action pour fermer le point | Priorité |
|---|---|---|---|
| **G01** | [`EmitContext::DefineTextureBuffers`](../vendor/encore-active/ns2-runtime/ampere/shader_recompiler/backend/spirv/spirv_emit_context.cpp) | **Manque conditionnel P2.2c :** exception explicite `"Array of texture buffers"`. Évaluer l'usage des tableaux de buffers-échantillonnés et l'ABI de leurs descripteurs ; implémenter et valider SPIR-V si requis. | Haute si utilisé |
| **G02** | [`EmitContext::DefineAttributeMemAccess`](../vendor/encore-active/ns2-runtime/ampere/shader_recompiler/backend/spirv/spirv_emit_context.cpp) | **Manque conditionnel P2.4 :** `"Physical stores and transform feedbacks"` non implémenté. Définir provenance de l'adresse et barrières avant d'émettre des écritures GPU ; pas de fausse réussite. | Haute si utilisé |
| **G03** | [`emit_spirv_context_get_set.cpp`](../vendor/encore-active/ns2-runtime/ampere/shader_recompiler/backend/spirv/emit_spirv_context_get_set.cpp) — lectures patch, attributs et instructions | **Manque conditionnel P2.4 :** `"Non-generic patch load"` et autres opérations SPIR-V explicitement non prises en charge. Trier par stage/usage invité, puis compléter ceux réellement nécessaires et les couvrir dans un module SPIR-V. | Haute si utilisé |
| **G04** | [`NormalizeNativeQmdIndirectCbufIR`](../vendor/encore-active/ns2-runtime/ampere/shader_recompiler/frontend/ampere/native_indirect_cbuf.h) | **Partiel P2.3 :** banques/offsets QMD3 authentifiés ; accès CBUF dynamiques dont la forme n'est pas prouvée rejetés. Inventorier les patterns IR réellement reconnus et les cas GPU non couverts ; ne pas détendre les bornes ni forcer le résultat. | Haute |
| **G05** | [`NativeAtomic::Rewrite`](../vendor/encore-active/ns2-runtime/ampere/shader_recompiler/frontend/ampere/native_global_atomic_binding.h) + [`NativeQmdAtomicSpansFitBindings`](../vendor/encore-active/ns2-runtime/ampere/shader_recompiler/frontend/ampere/native_atomic_span.h) | **Implémenté / à requalifier P2.3 :** entiers, flottants CAS et `ATOM.CAS` U32 utilisent les slots SSBO authentifiés ; contrôler résultats de retour et cas négatifs sous Linux, ne pas dupliquer ce code. | P0 CI |
| **G06** | [`EmitContext::DefineGlobalMemoryFunctions`](../vendor/encore-active/ns2-runtime/ampere/shader_recompiler/backend/spirv/spirv_emit_context.cpp) | **Correctif intégré / à requalifier P2.3 :** ABI `IR::Program` et `GlobalAtomicCompareExchange32` synchronisés avec le compilateur partagé au vendor `aa58e07`. Vérifier CI source + génération et validation `u32-cas` en Vulkan 1.2. | P0 CI |
| **G07** | [`NativeQmdTextureTables`](../vendor/encore-active/ns2-runtime/ampere/shader_recompiler/frontend/ampere/native_qmd_compute_environment.h) → [`RasterizerVulkan::DispatchNativeCompute`](../vendor/encore-active/eden-vulkan/vulkan_rasterizer.cpp) → `ComputePipeline::ConfigureNative` | **Implémenté / intégration P2.2c-P2.3 à compléter selon entrée :** tableaux TIC/TSC, ressources, SSBO 32 slots, rétention jusqu'aux fences et `vkCmdDispatch` déjà présents. Qualifier images et formats, droits, table variable, sampler, cache et refus/rollback dans la chaîne vraie ; **ne pas recréer un second dispatcher**. | Haute |
| **G08** | [`LowerReviewedToMaxwell`](../vendor/encore-active/ns2-runtime/ampere/shader_recompiler/frontend/ampere/lower_bridge.cpp), [`lower_to_maxwell.h`](../vendor/encore-active/ns2-runtime/ampere/shader_recompiler/frontend/ampere/lower_to_maxwell.h) | **Partiel P2.4 :** opcodes Ampere reconnus mais formes/sémantiques non traitées rejetés avec offset et raison. Extraire **les familles réellement manquantes par ISA et test**, prioriser celles du moteur générique, jamais une règle par TitleID. Le nombre de formes restantes n'est pas établi. | Haute, principale inconnue |
| **G09** | [`NativeGraphicsStageMaskSupported`](../vendor/encore-active/ns2-runtime/ampere/shader_recompiler/frontend/ampere/native_graphics_stage_policy.h), [`PipelineCache`](../vendor/encore-active/eden-vulkan/vk_pipeline_cache_cost.cpp) | **Décision P2.4 :** VertexA/B, fragment, Geometry et TessControl+TessEval liés sont déjà admis par le pipeline. Task/Mesh n'est pas supporté par cette politique et nécessite un contrat de stage/ABI + pipeline réel **si utilisé par le matériel invité** ; ne pas prétendre que cette paire a été testée sur PS5. | Haute si requis, inconnue majeure |
| **G10** | [`Puller::ProcessSemaphoreAcquire`](../vendor/encore-active/ns2-runtime/gpu_dispatch/video_core/engines/puller.cpp) | **Manque confirmé P2.7 :** `acquire_timeout` est encore `TODO`. Vérifier la sémantique native des attentes, l'abandon/shutdown et les réentrances, puis test de timeout sur hôte. Tester aussi l'ordre GPU-write → CPU-fetch des commandes GPFIFO avant la clôture de synchronisation. | Haute |

## P3 et P4 — ce qui est déjà clos et ce qui doit finir

| ID | Fonction ou test | Statut et sortie attendue | Priorité |
|---|---|---|---|
| **U01** | Launcher / UI, source et preview | **P3 : 15/15 sous-points déjà cochés côté source/hôte** dans #15. N'ajouter ici que d'éventuelles régressions découvertes dans le nouveau SHA. Jaquettes/transitions sur PS5 = P5. | Clos |
| **Q01** | [`tools/ns2/qualify_host_batch.py`](../tools/ns2/qualify_host_batch.py) | **P4.1–P4.2 : ouvert.** Exécuter les suites complètes `--scope core --jobs 3`, négatifs GMMU/NVMap/texture/IPC/atomiques, JIT/NS1, CI GitHub même paire ; produire le reçu, corriger les rouges **avant** de compter le lot comme terminé. | Haute |
| **Q02** | [Roadmap #15](https://github.com/niakw/ProsperoEden-Encore/issues/15), [matrice de sortie](P0_P4_EXIT_MATRIX_2026-11-06.md) | **P4.3 : ouvert.** Clôturer uniquement les catégories implémentées et qualifiées, associer commits/test/CI, écrire la décision d'entrée en P5. Aucun build console pendant P4. | Fin |

## Pilotage accéléré avec ChatGPT : lots mesurables, pas journées humaines

L'estimation humaine initiale de **17–46 journées** a été retirée : elle ne mesure pas les opérations menées par ChatGPT, qui peut analyser des sources, modifier plusieurs fonctions et lancer des suites en parallèle. Inversement, elle ne doit pas être remplacée par une promesse de livraison en quelques heures sans avoir identifié les opcodes et commandes réellement indispensables.

| Lot ChatGPT | Contenu regroupé | Condition de fin (automatisable sur hôte) |
|---|---|---|
| **A — CI P0** | Réparer tous les échecs source/vendor/CI actuels en une série de correctifs de provenance et compilation | Toutes les CI obligatoires vertes sur une paire `main/vendor` |
| **B — IPC P1** | Établir une matrice par commande de `ResultNotImplemented`, vérifier structures et provenance, corriger seulement les ABI nécessaires | Témoins positifs/négatifs et aucune commande obligatoire non couverte |
| **C — mémoire P1/P2.3** | Tests transactions NVMap/GMMU/sparse, CBUF/SSBO dynamiques, ressources TIC/TSC, retour des atomiques | Scénarios hôte négatifs + shader SPIR-V valide ; refus explicites |
| **D — GPU P2.4** | Audit couverture instruction par instruction, pipeline multi-stages et synchronisation GPFIFO | Couverture réelle des familles nécessaires ; aucun faux succès pour instructions inconnues |
| **E — P4** | Lot `qualify_host_batch.py`, puis suites CI Linux réelles et rapports SHA | Recette complète sur SHA figé, décision P5 documentée |

**Estimation honnête propre au travail assisté par ChatGPT :** les lots A et E sont principalement des opérations automatisables et leur charge est mesurable par les durées des suites CI. Les lots B–D contiennent une inconnue de **fonctionnalités réelles à écrire** : ils ne se déduisent ni du nombre de fichiers, ni du nombre de tests, ni du débit de rédaction de ChatGPT. Il est possible de traiter plusieurs corrections en une seule intervention, mais pas de garantir la clôture complète de P0–P4 en quelques heures tant que les exigences Task/Mesh, GMMU et IPC ne sont pas qualifiées.

**Accélération concrète :** lancer des contrôles indépendants en parallèle ; travailler par familles de fonctions ; publier le sous-module `vendor` puis le gitlink `main` ; supprimer les doublons déjà couverts et transférer **uniquement** la preuve console en P5. Ne jamais cocher une fonction absente pour tenir un délai.

## Ordre et règles de clôture

1. **CI d'abord** : au dernier SHA, aucun préflight cassé après l'ABI CAS ; fixer avant d'ajouter des opcodes.
2. **P1 ciblé** : liste des commandes `ResultNotImplemented` **par protocole réel**, issues des services `gpu_worker`, `graphics_supervisor`, vidéo ; fermer les lacunes prouvées, pas les refus légitimes.
3. **P2.2c/P2.3** : compléter les familles de ressources et d'adressage réellement requises, tests de shaders et ressources effectives sans GPU PS5.
4. **P2.4/P2.7** : opcodes et stages réellement manquants, attentes et barrières génériques ; aucun correctif par jeu.
5. **P4** : matrice des cas négatifs et CI au **couple SHA figé**, puis décision P5. **Aucune preuve console n'est exigée pour clore les quatre premiers jalons.**

> Le backlog est volontairement un inventaire **des propriétaires et chemins auditables**, pas une affirmation que tous les cas `NotImplemented` doivent être implémentés. Au prochain audit, changer l'état des lignes sur des preuves de source/test et réduire l'estimation seulement après fermeture effective d'un groupe.

### Lot Lichii nx2 — 6 novembre 2026 (validation groupée en attente)

Portage GPL-3.0-or-later depuis [Lichii nx2 `55532f2d81`](https://github.com/zortos293/Lichii/commit/55532f2d814215aaf32a76c214cf129f2cb6282b). Neuf encodages dans huit familles : `F2IP 0x243`, `F2FP 0xc3e`, `SUATOM 0x593`, `SUST byte 0xb9d`, `TLD bindless 0x367`, `TXD uniform 0xf6c`, `ST local 0x987`, `TMML 0x36a/0xf69`. Adaptations génériques : protection des registres invités, réserve des registres synthétiques, admission des sources uniformes, non-recouvrement des sorties, unicité du slot TIC/TSC, et masques du probe pour quatre encodages absents de la table NAK. Source intégrée dans le propriétaire actif ; **compilation, tests hôte et CI à valider en lot** avant de cocher P2.4. `0x2a5` possède déjà une voie de réécriture spécifique à auditer ; `ISBEWR 0x927` demande le frontend Task/Mesh complet ; `CSMTEST 0x80d` n'est pas simulé par un résultat arbitraire. Aucune validation PS5 nécessaire avant P5.

### Adaptations Lichii après l’import ISA (06/11 — code intégré, tests de lot non clos)

Le compilateur Ampere préserve désormais les deux mots de destination de `UIMAD.WIDE 0x2a5` (`vendor a2ac864`), au lieu de l’admettre dans le cas scalaire `IMAD 0x225`. Côté services communs, les `Gather` concurrents de mémoire sale GPU sont sérialisés (correction de course avec le décodeur vidéo), et `WaitIfEqual64` est porté sur les **8 propriétaires SVC/kernel/générateur**, tout en conservant la valeur 32 bits des appels AArch32. Ces adaptations ne sont pas la clôture globale de P1/P2/P4 ; un lot complet de compilations et contrôles doit encore les qualifier.
