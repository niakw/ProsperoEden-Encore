# Eden Encore — suivi maître F07 et exploitation PS5

> **26/11 — correction P0/P1 du propriétaire GPU réellement sélectionné :** le profil PS5 impose Vulkan/RADV **et** le launcher OpenGL ; le sélecteur G21 compile donc `gpu_gl_native.cpp` et non `gpu_vulkan.cpp`. Vendor `93e3259c7aea3a88a7fd5f80cf706903fac6ccc9` : retraite FIFO bloquante des channels, registre protégé, pointeur initialisé, capture applet à propriétaire partagé, fast path sans mutex pour ticks vides avec drain borné conservé, fast path dirty GPU et horloge invitée NS2 réintégrés dans le propriétaire actif. Le teardown OpenGL conditionnel, Stop/clear/wake, ordre FIFO et parcours Maxwell NS1 sont préservés. Contrats hôtes et empreintes exactes actualisés ; CI, graphe Ninja PS5 complet et console non qualifiés. Aucun gain FPS ou démarrage revendiqué.

> **26/11 — P0 GPU, NS1/NS2 :** vendor `ad713526cb573d2051a945badfd3bea71b39565b`. Le retrait d'un channel via `RequestSyncOperation` pouvait être exécuté dans `TickWork` à la fin d'un draw, alors que Scheduler::Push/ResumePendingNative détenaient encore des verrous nécessaires à RetireChannel. Le correctif sélectionne une commande FIFO bloquante de retraite hors dispatch dans le worker natif ; le registre GPU::Impl est protégé par son propre mutex sans emboîter scheduler/renderer. Le sélecteur worker/headers CMake était sous EDEN_PS5_OPENGL, déplacé au niveau commun natif pour Vulkan ; qualification du graphe Ninja complet encore requise. Modèle local C++ O0/O2 ASan/UBSan : 10 000 conflits de verrou d'époque simulés, 20 000 draws suivis de 10 000 retraites FIFO correctes, par profil. Ce modèle n'exécute pas le scheduler ou renderer PS5 réel. P0 console ouvert, aucun build natif déclenché. Les corrections de reçus historiques préservent les blobs exacts et la base F07 littérale.

> **FC27 — 26/11, synchronisation GPU et durée de vie de capture :** vendor `4f9ea0c9e401ef3d025ed1676ac9a20a201455eb`, moteur `2863a4589818064273c9b4b504e82a6c6ff14855`. Le CMake sélectionne `encore-active/eden-core/src/video_core/gpu_vulkan.cpp`. Lichii (propriétaire `src/video_core/gpu.cpp`, blob `254bf54d61edd09797354bed6d94515c1d83fc1d`) confirme le fast path de `TickWork` par compteurs de requêtes et de complétions. Adaptation Encore : compteur publié seulement après insertion réussie, acquire sur lecture de complétion, conservation de l'ordre FIFO et du verrou RAII pendant les exceptions. La capture applet transmet désormais son résultat par propriétaire partagé au callback ; une attente annulée ne peut lire un vecteur en cours d'écriture. Fixture locale C++ O0/O2 ASan+UBSan : 1 000 000 ticks vides sans verrou, 50 000 callbacks FIFO avec producteur concurrent, capture normale, annulée et attente en exception ; callbacks retardés exécutés sans erreur de durée de vie. Fixture simulée, pas de GPU réel. Test hôte source-extrait étendu ; CI de la nouvelle paire en cours, QA vendor et CPU-write readback race verts, build PS5 ignoré. Les échecs historiques de provenance launcher restent à traiter ; aucune amélioration FPS ni résolution HUD/Pause/NS2 revendiquée sans console.

> **FC27 — 26/11, cohérence des plages de lecture CPU Vulkan :** le propriétaire actif `encore-active/eden-vulkan/vulkan_rasterizer.cpp` pouvait retourner une plage texture préemptive large après avoir interrogé BufferCache uniquement sur la lecture initiale (ou sa page). Les deux propriétaires mémoire natifs mémorisent cette plage et n'interrogent plus le GPU pour les lectures suivantes incluses. Le vendor `0fa6924891050f7cea9b196dff0a760ad154993d` contrôle désormais toute la plage effectivement retournée, sans emboîter les mutex, conserve l'absence de verrou pour les plages jamais enregistrées et déclenche le chemin FlushRegion déjà ordonné si un buffer contient des octets GPU plus récents. Lichii maintient également une coordination des plages de lecture et des read traps, avec une autre ABI ; pas de backport de son chemin NX2. Modèle C++ O0/O2 UBSan local (bitmap/cache simulés) : 10 000 faux résultats propres avant, 0 après, 10 000 cas réellement propres conservés par optimisation. Le test hôte existant compile la méthode active avec un cas de page voisine ; son résultat CI reste à confirmer. Vendor `6fff7df3b34d2aead3e7de86b1c5919b45c7f0f9` conserve le reçu historique de protection synchrone par inversion exacte du seul delta de lecture. Pas de build natif ni de preuve de correction du HUD en jeu. Les échecs CI historiques launcher/provenance restent distincts.

> **FC27 — 26/11, regroupement des copies de readback :** captures PS5 du 25/11, moteurs `8a71802b` (frame 6006, 89 images/5,005 s, 17,782 FPS, 40 109 contentions BufferCache / 961,242 ms cumulées) et `a54c7cc3` (frame 9207, 138 images/5,008 s, 27,556 FPS, 32 938 contentions / 972,008 ms cumulées). Aucune attente individuelle >=1 ms ni contention TextureCache dans ces deux fenêtres ; pas de comparaison A/B à scène contrôlée. Le vendor `637edccbbf9dc403008192eaf04b14615b0500e2`, épinglé par le moteur `d470d5d9`, regroupe les régions consécutives d'un même buffer dans `CommitAsyncFlushesHigh` (maximum 8, capacité inline Vulkan), sans réordonner ni retarder la publication. Modèle C++20 O2 UBSan hôte, 10 000 cas : 637 923 commandes individuelles contre 282 335 groupées, ordre des régions, plages async, offsets normalisés et usages identiques. Ce modèle n'exécute ni Vulkan ni le runtime PS5. Gates vendor RangeSet ABI / race CPU-write readback / QA vertes ; CI moteur du couple en cours ; natif non déclenché. Les captures ne prouvent pas que ce chemin explique tout le retard HUD/Pause. Le bouton Plus est publié par l'émulateur, consommation invitée non établie. P0 fermeture et P1 fluidité/fidélité restent ouverts console.

> **FC27 NS1 — récupération WSI, 24/11 :** le présentateur natif sélectionné par `headless/vulkan.cmake` pouvait relancer `CopyToSwapchainImpl` sur `VK_ERROR_SURFACE_LOST_KHR` même après un `vkQueueSubmit` réussi. La frame avait déjà consommé `render_ready` et engagé `present_done`. [Spécification Vulkan WSI](https://docs.vulkan.org/refpages/latest/refpages/source/vkQueuePresentKHR.html) : les attentes de présentation peuvent être mises en file malgré la perte de surface. Le correctif conserve les reprises avant soumission, propage la faute après soumission via le latch GPU existant, sans réutilisation ni achèvement fictif. Modèle local O0/O2 UBSan : 3 000 cas par optimisation, 300 doubles attentes invalides avant, 0 après. Contrat source-extrait ajouté au test de drain natif existant (CI à confirmer). Cas d'erreur prouvé statiquement, **non observé dans la capture FC27** ; aucun gain FPS revendiqué, pas de build natif.

> **FC27 NS1 — replay 24/11, capture du 23/11 15:16 :** source journal `d2bfe34d3c75d5df20319eeeaa5360a06ddc1e83`, gitlink `a6240909b823492d9ff20070c09387a732d83007`, [build d'origine 45182794183](https://github.com/niakw/ProsperoEden-Encore/actions/runs/45182794183), ELF non strippe de l'artefact 14823836660 : SHA-256 `b9e477c5416a18d03d2978d0880ebdece5389203838878fe08fa0d71613936ee`, .text 0x27d6b40 conforme au rapport. Pile symbolisée en offsets ELF (pas d'ajout du load bias) : 0x41f55 terminate, 0x5b4ebf nvhost_as_gpu::~nvhost_as_gpu, 0x306d05 table NVDRV, 0x305a62 Module::~Module, 0x5fafc8 NVDRV::~NVDRV, 0x521331 factory, 0x2d6cee map factories, 0x2d393e ServiceManager::~ServiceManager, 0x29c43f ShutdownMainProcess après ShutdownCores (désassemblage confirme). Adresses stack non vérifiées par l'outil de crash ; pas de hash eboot console, mutex individuel non attribué. Le vendor `44540549` libère les factories après CloseServices/services.reset et avant ShutdownCores, hors mutex SM ; nvhost_as_gpu propriétaire commun confirmé CMake. Replay hôte O0/O2 UBSan du corps SM actuel avec objets kernel simulés : 600/600 anciennes destructions après retraite vs 0/600 nouvelles, par optimisation ; ce n'est pas une exécution réelle du kernel PS5. P0 fermeture reste ouvert console. 82 fenêtres FC27 uniquement, 260 misses uniques (196 graphics, 64 compute), 29 pauses >100 ms, dont trois fenêtres lentes sans miss/wait journalisé. Pic 40504 contentions/1209.669 ms cumulées, aucune attente >=1 ms dans cette fenêtre ; ne pas assimiler à un gel de 1.2 s. Source `2bc05d2e` élimine le double préwarm (128+128, 740+599 ms observés). Pas de simulation NS2, pas de nouveau build natif, pas de gain FPS revendiqué.

> **Fermeture FC27 — candidat runtime 23/11 :** vendor runtime `603e0d5c` (gitlink candidat `593bc9ee`, correction test-only) conserve l'ordre de teardown corrigé et ajoute deux protections causales : `ServerManager::LoopProcess()` joint ses workers additionnels avant destruction de l'état de service porté par l'appelant, et `ServiceManager::RegisterService` respecte le `max_sessions` demandé au lieu d'une capacité fixe. Source qualifiée par blobs exacts ; **validation PS5 encore requise** avant de classer le crash manuel résolu.

> **Essais FC27 PS5 du 23/11 (binaire moteur `25f12c02`, vendor `716e069f`) :** 2 arrêts natifs à la fermeture manuelle, `recursive_mutex lock failed: Invalid argument`, thread main (250 s / 342 s). Journal : `gpu_core.reset`, `kernel.CloseServices`, `services.reset` achevés avant exception. Correctif de durée de vie SM [vendor `09ce0af1`](https://github.com/niakw/Prospero.Eden-Encore-vendor/commit/09ce0af1ccf20a1f9278ed4ab401729768b1f925) intégré **sans validation console**. FC27 a 43 fenêtres de ~5 s, médiane 30 FPS, minimum 16,747 FPS, pire frame 1 422,896 ms, 9 fenêtres sous 29 FPS et 24 événements >100 ms ; une fenêtre a BufferCache 7 552 contentions / 206,239 ms d'attentes cumulées ; `surface.cpp format=0` et Fermi2D volume-slice non résolus. P0 fermeture et P1 fidélité/frame pacing **ouverts**. Voir [architecture mémoire invitée](EDEN_ENCORE_GUEST_MEMORY_NS1_NS2_PS5_ARCHITECTURE.md).

**Suivi exécutable des optimisations restantes :** [F07_REMAINING_OPTIMIZATION_CHECKLIST.md](F07_REMAINING_OPTIMIZATION_CHECKLIST.md) — une case par contrôle, séparant décisions pré-build et preuves console post-build. Ne pas confondre nombre de cases et nombre de patchs nécessaires.

**Date de référence historique :** 28 octobre 2026. **Branche actuelle : `main`** depuis le 30 octobre 2026. L'ancienne branche `dev/ps5-sparse-jit` n'est plus éditée ; ses cinq derniers correctifs ont été fusionnés via PR #5. Les résultats historiques liés à cette branche ne prouvent pas les CI récentes de `main`.
**Source relue :** `3ca07a442d1fd85aa0cc5de08eb02099c46f2bac` (avant création de ce suivi).
**Priorité produit :** fluidité réelle de FC 27, HUD/maillots/textures corrects, commandes réactives et absence de gel. **F07 ouvert.**

> Ce fichier est le point d'entrée des priorités. Les documents d'audit référencés plus bas contiennent le détail technique. Aucun test hôte ni build PS5 ne permet, seul, de conclure à un correctif visible en jeu. Les mesures console restent privées.

## Référence CI native figée — 28 octobre 2026

**Dernier SHA source 4/4 vert :** `d2c3713a44e30e0be2e55a308d55d55a74b0e660` (branche unique `dev/ps5-sparse-jit`). Vérification des statuts GitHub effectuée après achèvement, et non extrapolée depuis la file d'attente.

| Validation sur ce même SHA | Exécution | Résultat |
| --- | --- | --- |
| Core fast gate (hôte) | [40639033832](https://github.com/niakw/Prospero.Eden-Encore/actions/runs/40639033832) | **SUCCESS** |
| Source preflight (hôte) | [40639033849](https://github.com/niakw/Prospero.Eden-Encore/actions/runs/40639033849) | **SUCCESS** |
| Build/package natif PS5 | [40639033809](https://github.com/niakw/Prospero.Eden-Encore/actions/runs/40639033809) | **SUCCESS** |
| CodeQL, C++/Python/workflows | [40639033748](https://github.com/niakw/Prospero.Eden-Encore/actions/runs/40639033748) | **SUCCESS** |

**Livrables de la même compilation :**
- [Archive FTP PPSA99008](https://github.com/niakw/Prospero.Eden-Encore/actions/runs/40639033809/artifacts/12794798659) — 38 037 087 octets (archive GitHub) ; empreinte GitHub `sha256:b785766e317271ffc9b3d4d9675f56c5a9e71e1125531d0bcb5661b2ec8ad09a`.
- [Bundle release compilé](https://github.com/niakw/Prospero.Eden-Encore/actions/runs/40639033809/artifacts/12795117950) — 190 398 563 octets ; empreinte GitHub `sha256:7dd3249a4c43c245fcb40bd96a97a3203f8ecd5da3d5f8dada9864773836e780`.

**F07 depuis la dernière mesure console :** le mode fast-first est actif par défaut dans le paquet natif ; option de comparaison par titre `fast-pipelines.txt` contenant `off`, lue depuis `Eden::ConfigDir()`. Les tests O0/O2 ont confirmé les chemins compilés du profil. P0.4 : échec de conversion **après admission** rattrapé par une publication de décodage invalide, suppression du contexte et conservation de `CpuModified`; les pixels partiels ne sont pas publiés. P0.3 : un décodage encore incomplet est sondé via `complete.load(acquire)` sans prendre le mutex du worker sur chaque frame ; le verrou est conservé pour lire le résultat terminé. Générateur d'overlay natif et tests source-extraits mis à jour ensemble.

**Ce que les quatre succès ne prouvent PAS :** le temps réel de première traduction guest CFG/IR/SPIR-V (**P0.1 toujours ouvert**), les attentes Vulkan au premier pipeline (**P0.2 ouvert**), la réduction de contention du HUD sur console (**P0.3 ouvert côté mesure**), la fraîcheur effective des textures/HUD à l'écran (**P0.4 ouvert côté console**), et les freezes guest IPC/pause/mi-temps. Le résultat `F01–F06 = 6/6` reste une preuve **hôte**, pas console.

**Décision de stabilisation :** conserver le commit `d2c3713` comme base binaire PS5 qualifiée CI. Aucune nouvelle modification opportuniste du moteur, ni test console demandé automatiquement : mesurer en campagne groupée lorsqu'elle sera autorisée, plutôt que casser la seule preuve 4/4 obtenue en multipliant les commits.

## États et règle de preuve

- **INTÉGRÉ (SOURCE)** : le chemin sélectionné est présent dans la branche ; pas de certification de son exécution sur PS5.
- **HÔTE** : test reproductible C++/Python/source sur le périmètre annoncé (souvent O0/O2 ou GPU simulé).
- **CI/BIN** : prévalidation complète, fast gate et vrai paquet PS5 réussis **sur le même SHA**, non « skipped ».
- **CONSOLE** : firmware 13.60, jeu, scène, paramètres et résultats réels comparables ; exigé pour déclarer jouabilité et gain de FPS.
- **OUVERT** : défaut observé non levé ou explication causale non démontrée, même lorsqu'un correctif partiel est intégré.

### Priorités fonctionnelles (ordre de traitement)

| Priorité | Sous-système et sources actives | État établi au 26/10 | Travail vérifiable pour fermer |
| --- | --- | --- | --- |
| **P0.1** | Première utilisation des shaders — `vk_pipeline_cache_cost.cpp::CurrentGraphicsPipelineSlowPath / CreateGraphicsPipeline` | **OUVERT**. Construction Vulkan parallèle et préchauffage borné à 8 entrées présents ; traduction guest IR → SPIR-V encore **synchrone au premier cache miss**. Tests hôte sur préchauffage/persistance, pas de réduction mesurée des à-coups PS5. | Isoler coût CPU de traduction vs création Vulkan sans écrire à chaque draw ; reproduire un problème exact, corriger sans shader invalide ni ordre de draw cassé. |
| **P0.2** | Attente des pipelines — `vk_graphics_pipeline_cost.cpp::ConfigureDraw`, scheduler/worker Vulkan | **OUVERT**. Chemin ready avec acquire et court-circuit ; une compilation non terminée pose toujours une **attente ordonnée** dans le worker. Correctifs de publication et callbacks testés sur hôte. | Mesurer l'attente réelle par fenêtre de frame et séparer compilations froides/attentes ; conserver les dépendances et fences, ne jamais réutiliser un pipeline non prêt. |
| **P0.3** | Contention caches buffer/texture — `vulkan_rasterizer.cpp::PrepareDraw/OnCPUWrite`, `vk_graphics_pipeline_cost.cpp`, `vk_texture_cache_cost.cpp` | **OUVERT**. Preflight, réutilisation sampler et exclusions de chemins chauds déjà intégrés. Les journaux montrent des attentes corrélées en partie aux retards, mais pas la causalité complète. | Identifier propriétaire et durée **sous verrou**, phase upload/désentrelacement, soumissions et attente GPU ; test régression avant toute réduction de verrou. |
| **P0.4** | Fraîcheur HUD, textures et transition blit → pipeline → present | **OUVERT**. Fix `DrawTexture` → `Scheduler::InvalidateState`, reprise TIC/TSC, barrières et tests hôte présents. Les bandeaux noirs / textes retardés restent observés sur console dans la version testée du 25/10. | Prouver que la **révision d'image/pixels** change bien jusqu'à la présentation, distinguer absence de draw, mauvais descripteur et ancienne image présentée ; confirmer sur PS5. |
| **P1.1** | JIT A32/A64, compilation/invalidation, progression guest | **PARTIEL / NON QUALIFIÉ CONSOLE**. Un seul sparse JIT natif est sélectionné, voir le tableau dédié. Les pauses longues et la progression CPU invité pendant les à-coups ne sont pas attribuées. | Mesurer compile/invalidation/états de threads et relier à l'image produite, tester cycle lancement → invalidation totale → recompilation → retour bibliothèque. |
| **P1.2** | HLE/NvDisp/Host1x/BufferQueue → renderer → présentation, manette → NPad | **HÔTE 6/6 F01–F06, CONSOLE OUVERTE**. Chaînes F05/F06 testées avec adaptateurs/WSI simulés ; 30 callbacks/s ne prouvent pas un match qui avance. | Distinguer jeu bloqué, guest éveillé sans progrès, nouveau rendu non présenté, HUD stale et commande retardée. |
| **P2.1** | VRAM, GC, mémoire directe, 4× OOM | **PARTIEL**. Budgets/limites prudents, observabilité de l'OOM, pas d'arbitrage dynamique JIT↔GPU↔guest intégral prouvé. | Gérer le 4× séparément du 1× ; suivre direct-mem libre/plus grand bloc, allocations VMA, scans et relance, sans agrandir aveuglément les caches. |

### Sparse JIT PS5 : ce qui est réellement fait

| Composant | État source/hôte | Ce qui **n'est pas terminé** |
| --- | --- | --- |
| **Unique allocator natif** | **INTÉGRÉ** : `headless/jit-allocator.h` réserve deux vues RX/RW et ne retombe plus sur le JIT dense en PS5 natif ; `main.cpp` impose `ProbeSparseJitAlias()` avant démarrage du titre. Sélecteur release natif contrôlé par `check-native-sparse-jit-release-selector-host.py`. | Validation de l'alias avec firmware 13.60 et capture d'un lancement effectif ; si l'alias échoue, démarrage refusé (aucun fallback dense). |
| **RAM physique à la demande** | **INTÉGRÉ + témoins HÔTE** : `BlockOfCode::EnsureMemoryCommitted` et `src/memory_pages.cpp` engagent par blocs physiques de 2 Mio au lieu de réserver tout le physique à la création ; taille d'arène virtuelle fixe pour préserver les adresses relatives. | Prouver l'engagement progressif, les plafonds et la résilience mémoire dans FC27 et BOTW sur longue session. Une vraie saturation peut encore provoquer `bad_alloc`/arrêt du titre. |
| **Retour de RAM JIT** | **INTÉGRÉ + témoin HÔTE** : `TrimSparseJitCode` peut décommitter la queue uniquement après invalidation **complète et quiescente**, protéger les deux alias puis libérer le backing ; `check-native-sparse-jit-trim-host.py` valide un modèle natif extrait. | Ni récupération fine à chaque invalidation partielle, ni arbitrage continu pression RAM JIT/GPU/guest, ni preuve de cycles réels d'arrêt/reprise PS5. |
| **A32/A64 code lifetime** | **SOURCE / HÔTE partiel** : plans d'arènes et gardes de capacité, alias memo/invalidation générationnelle ; plan physique distinct du virtuel. | Corréler les longs ralentissements aux compilations réelles, confirmer invalidations concurrentes/quiescence sur matériel. |
| **Répartition CPU/compilation shaders** | **POLITIQUE INTÉGRÉE / CONSOLE NON MESURÉE** : le nombre de workers est limité par le masque d'affinité effectivement exposé et les réservations pour workers primaires ; la présence de CPU logiques ≠ cœurs physiques distincts. | Aucune preuve que l'émulateur exploite « 100 % » du CPU ni que davantage de workers améliore les latences. Démontrer temps CPU, contention, GPU idle/busy par phase avant adaptation. |
| **Vulkan, RADV et VRAM partagée** | **ADAPTATIONS INTÉGRÉES / PARTIEL** : compilations de pipelines asynchrones, caches persistés, textures/barrières synchronisées et mesures de pression ; préchauffage de **8** pipelines, pas précompilation totale. | Premier usage synchrone restant, attente pipeline worker, contenu HUD, contrôle effectif pression mémoire GPU et cadence stable. |
| **Robustesse livrable** | **CI/BIN 4/4 VERT au `d2c3713`** : profil release natif unique et ID `PPSA99008`, artefacts GitHub récupérables, fast gate + preflight + build/package + sécurité réussis sur le même SHA. | Campagne console groupée non effectuée : firmware, mémoire native, fluidité, HUD et redémarrage restent à qualifier. |

**Attention :** « sparse JIT intégré » ne signifie **ni** « JIT terminé », **ni** « GPU/CPU utilisés au maximum », **ni** « FC27 jouable sans saccades ». La console réserve des ressources au système et les temps de synchronisation réels comptent davantage que la saturation CPU/GPU. Les anciennes notes « sparse DEV seulement » de documents historiques ne décrivent plus la sélection `PS5_NATIVE` actuelle.

## P0.4 — sélection d'une image réellement fraîche à la présentation

Correctif du 27/10 : le framebuffer accéléré ne doit pas sélectionner un
`ImageView` dont le backing est `Remapped` ou dont les pixels invités ont
été modifiés (`CpuModified`) sans rafraîchissement de l'image Vulkan.
Dans `TryFindFramebufferImageView`, ces candidats sont désormais exclus
**uniquement sur PS5**. Sans vue accélérée admissible,
`RasterizerVulkan::AccelerateDisplay` laisse `Layer::ConfigureDraw`
utiliser `UpdateRawImage`, qui lit et charge le framebuffer invité actuel.
Les vues GPU propres continuent d'utiliser le chemin zéro-copie habituel.
En complément, `RasterizerVulkan::AccelerateDisplay` exécute maintenant
`gpu_memory->FlushCaching()` **avant** la prise du mutex texture ;
ainsi un remappage invité en attente ne peut pas faire sélectionner
un ancien framebuffer accéléré après le changement de mapping.
La source active, le générateur d'archives pinnées et le témoin C++ -O0/-O2
sont modifiés ensemble. Cela ferme un chemin de réutilisation périmée,
**pas** la validation finale des pixels/HUD sur l'écran de la console.

## Référence console et critères d'acceptation

- Baseline réellement observée et **non remplacée par des hypothèses** : `cd4857c8` (25/10), à 1440p/1× : 204 fenêtres de 5 s, FPS médian 29,56, minimum 14,48, frame la plus lente 689,834 ms et 142 retards >100 ms ; à 2160p/1,25×, pire frame 977,578 ms. Ces sessions **ne sont pas** des A/B contrôlés. Les latences des menus et le HUD tardif subsistent.
- Baseline ressentie la plus jouable : **cache vidé + journalisation détaillée désactivée**, sans constituer une preuve que les logs ou caches sont la cause.
- **Avant test PS5** : échec-before/réussite-after hôte (si bug nouveau), source propriétaire effective et ses gardes, fast/preflight verts et ZIP PS5 de **même commit**. Pas de multiplication des microtests console.
- **Test final groupé** : même scène FC27 1440p/1×, mêmes options, cache défini, logging OFF, comparer retards >50/>100 ms et pire intervalle, nouveaux pixels HUD, maillots/terrain, latence pause/manette, stabilité/retour à l'accueil et réouverture. Tests BOTW de compatibilité et de redémarrage ensuite. Des FPS affichés ≠ fraîcheur d'image ni simulation invitée.
- **Clôture F07** uniquement après disparition vérifiée des saccades bloquantes et HUD retardé/absent sur PS5 réelle. **F01–F06 : 6/6 hôte ; pas 6/6 jeu.**

## CI — point de capture

À l'instant du contrôle du SHA `3ca07a442`, les workflows suivants **n'avaient pas encore de résultat de succès final** :
- [Prévalidation #40398310462](https://github.com/niakw/Prospero.Eden-Encore/actions/runs/40398310462) : en attente.
- [Compilation native #40398310477](https://github.com/niakw/Prospero.Eden-Encore/actions/runs/40398310477) : en cours.
- [Sécurité #40398310506](https://github.com/niakw/Prospero.Eden-Encore/actions/runs/40398310506) : en cours.
- Les anciens échecs au `bbc097f` portaient notamment sur deux défauts indépendants : commentaires `//` dans `headless/CMakeLists.txt`, et harnais dense qui ne compilait plus contre l'unique sparse JIT. Correctifs commits `f386d8c`, `93bb6d0`, `3ca07a4`. **Les correctifs ne constituent pas un CI vert.**
- Tout commit ultérieur (y compris ce document) exige de consulter **ses propres** résultats CI, pas ceux d'un commit précédent.

## Règle anti-boucle et prochain ordre concret

1. **Stabiliser le build :** fast gate, prévalidation, build natif, sécurité sur le même commit, réparer seulement les échecs prouvés. Une doc ou un harnais de test réparé n'est pas un gain FPS.
2. **P0.1 + P0.2** : première traduction de shader et éventuel `wait` du pipeline dans le worker Vulkan ; révéler précisément où le frame est retenu. Ne pas désactiver les fences ou forcer la publication d'un pipeline inexécutable.
3. **P0.3 + P0.4** : retrouver l'origine exacte de la contention et du HUD obsolète ; préserver cohérence TIC/TSC, DMA, barrières et ordre de présentation.
4. **P1.1 + P1.2** : après stabilité P0, qualifier mémoire sparse JIT sur vraie PS5, progression A32/A64 et relation commandes → guest → image.
5. **P2** : pression VRAM/direct-mem et OOM extrême, puis réglages visuels seulement quand le chemin principal est stable.
6. **Une campagne console**, une fois le paquet complètement vert et le lot P0 testable. Aucun nouveau « 7/7 » tant que la jouabilité n'est pas prouvée.

## Réutilisation ciblée depuis la branche expérimentale — 26 octobre

Le lot **R01** a été adapté dans les sources natives de production : compteurs
séparés des composites Vulkan, images réelles/générées mises en file, images
ignorées, écrans de chargement et retours d'appel `Present`. La mesure n'est
active qu'en profil de diagnostic détaillé ; les tests C++ natifs, analyseur
hors-ligne, replay F03/F05 et contrôle de parité du générateur sont intégrés.
**État : SOURCE INTÉGRÉE, CI ET CONSOLE NON QUALIFIÉES** ; aucun gain FPS/HUD ne
peut encore être revendiqué. R03 RADV/SPIR-V, R04 AudioIn/RomFS et R06
frame generation restent hors de ce lot (pas de fusion globale). Détails :
[FC27_R01_SOURCE_TELEMETRY_PORT_2026-10-26.md](FC27_R01_SOURCE_TELEMETRY_PORT_2026-10-26.md).

## P0.1 — temps de traduction des shaders, détail RELEASE

Une première création de pipeline appelle déjà des phases CPU distinctes
qui restaient masquées par les anciens timers Vulkan DEV. Le chemin natif
sélectionné mesure maintenant en **diagnostic détaillé uniquement** :
`shader_pool_reset`, `shader_cfg`, `shader_ir`, `shader_spirv`,
`shader_module`. Les durées, sous-phases de `graphics_pipeline_create`,
ne doivent pas être additionnées comme une seule frame si plusieurs workers
les rapportent. Aucun shader, fence ni ordre de dessin ne change.
**F07 reste ouvert :** c'est une attribution, pas un gain FPS démontré.
Le chemin silencieux ne prend aucun chronométrage supplémentaire.

## P0.2 — coût des attentes de pipeline Vulkan

Le chemin graphique et compute conservent leur vérification de disponibilité
acquire avant d'enregistrer et d'exécuter la callback du scheduler. Si la
compilation est encore en cours **au moment réel de la callback**, la section
bloquante signale maintenant respectivement `graphics_pipeline_wait`
ou `compute_pipeline_wait` dans `EDEN_GPU_CACHE_PHASE`, uniquement lorsque
la journalisation détaillée est activée. Cela mesure mutex + condition
d'attente, et non du temps GPU. Les tests extraient la callback C++ et couvrent
pipeline prêt en avance, construction inachevée, profil silencieux, et échec
de pipeline compute. Aucun `wait`, fence ou ordre de commande n'est supprimé.
**Ce changement apporte une attribution des blocages, sans gain FPS revendiqué.**
Les coûts agrégés des différents threads ne valent pas durée d'une frame.

## P0.2 — préservation des workers shader après annulation

Le générateur Vulkan et la source active dissocient l'annulation du lecteur
de cache de celle du pool de compilation PS5.
`StatefulThreadWorker::WaitForRequests(stop_token)` appelle
`request_stop()` sur **tous** les workers lorsque le jeton de chargement
est annulé. Un retour au lanceur pendant un chargement pouvait ainsi
rendre les compilateurs indisponibles pour les nouveaux shaders.

Sur PS5, `workers.WaitForRequests()` attend seulement la fin des
huit jobs de préchauffage au maximum, sans stopper les workers.
Les autres plateformes conservent `WaitForRequests(stop_loading)`.
Le test hôte reproduit une annulation après admission des jobs puis
l'acceptation d'un nouveau shader. Il n'y a aucune nouvelle attente
dans la boucle de dessin. Le gain FPS et le HUD restent à qualifier
sur matériel.

## Dossiers de preuves existants

- [F07 — priorités et mesures](FC27_F07_STUTTER_HUD_PRIORITY_2026-10-26.md)
- [F07 — audit transversal et sparse JIT](FC27_F07_CROSS_SYSTEM_OPTIMIZATION_AUDIT_2026-10-26.md)
- [F01–F06 — critères de sortie, traces et historique CI](FC27_EXIT_GATES_2026-10-22.md)
- [Une seule version PS5 livrable](EDEN_ONE_SHIPPING_PROFILE_2026-10-26.md)
- [Tableau à deux axes — historique des fichiers examinés](EDEN_TWO_AXIS_PROGRESS_2026-10-20.md)
- [Architecture native et contraintes PS5](PS5_NATIVE_ARCHITECTURE.md)

**Ne pas réutiliser les compteurs documentaires « fichiers restants » comme nombre de corrections requises :** inventaire, optimisation et qualification sont trois axes différents.

## P0.2 — vie des compilations optimisées en attente (27 octobre)

Le chemin « fast-first » maintenait `OptimizeState::running=false` entre
`QueueWork` et le début effectif du worker : le destructeur pouvait alors
libérer un `GraphicsPipeline` encore capturé par un job en file. La correction
marque le travail **en attente avant publication**, puis libère cet état pour
toutes les sorties (annulation avant démarrage, exceptions, fin normale et
échec de l'admission dans la file). Elle ne publie plus un pipeline optimisé
si le pilote retourne un handle Vulkan nul. Le témoin C++ natif vérifie les
cycles annulation/fermeture, pipeline manquant et refus de file, tandis que la
reproduction du générateur Vulkan conserve la parité avec la source sélectionnée.

C'est un correctif de **durée de vie et de validité des pipelines**, sans preuve
de réduction des saccades, ni levée du F07 sur console.

## Dernière base CI pleinement vérifiée

Sur `d76fc53a9ae553eef61e0898195d5ea374b1b2b0`, les quatre jobs
(native build, fast gate, preflight complet, analyse de sécurité) sont
`SUCCESS`. Toute modification après ce commit doit faire ses propres
contrôles CI au même SHA ; un résultat antérieur n'est pas transférable.

## P0.1 — rattrapage borné des shaders compute (27/10)

Une traduction compute retournant un pointeur nul demeurait en cache sans
nouvelle tentative. Le chemin natif PS5 permet maintenant **une seule reprise
après deux secondes**, bornée à **32 clés échouées**, sans lecture d'horloge ni
compilation supplémentaire pour les compute pipelines déjà valides. Un échec
persistant ne provoque aucune boucle. La source native et sa reproduction
Vulkan sont synchronisées ; un test C++ extrait la vraie politique et couvre
O0/O2 et le budget de retries. Le défaut distinct d'un handle Vulkan qui
échoue après création asynchrone n'est pas traité ici. **F07 et la preuve
HUD/FPS console restent ouverts.**

## P0.2 — fermeture du compteur de compilation compute

En production native, la notification shader-building du constructeur
compute précède les opérations d'initialisation du layout et l'admission
au worker. Une exception sur ces chemins pouvait garder le compteur en état
« compilation en cours ». La garde RAII native retourne maintenant la
notification avant le transfert ; après transfert, le SCOPE_EXIT existant de
la callback reste son unique propriétaire. Le test hôte reproduit la fuite
sur l'ancienne route et vérifie préparation échouée, file fermée, compilation
inline et worker différé en -O0/-O2. Aucun changement de synchronisation
des ressources invitées ni d'attente GPU. F07 console non qualifié.

## P0.4 — restauration de texture après erreur d'upload

TextureCache::RefreshContents efface CpuModified avant staging, copie et barrière Vulkan. Une exception sur ces étapes laissait une image considérée propre sans upload terminé. La source PS5 restaure maintenant CpuModified et annule le suivi de pages si cet upload synchrone échoue. Un upload et sa barrière terminés conservent l'état propre. Le générateur, l'en-tête actif et le témoin hôte O0/O2 sont synchronisés. Pas de modification aux branches de retour MSAA/async. Pas de preuve de correction du HUD/FC27 sur console.

## P0.3 — attribution compute du verrou buffer/texture

`DispatchCompute` acquiert la paire de mutex buffer/texture puis exécute `Configure` et la préparation des commandes. Jusqu'ici ses coûts ne contribuaient pas aux phases `pair_wait/pair_held` réservées aux draws graphiques. Trois phases spécifiques `compute_pair_wait`, `compute_pair_held`, `compute_configure` distinguent désormais sur le chemin PS5 l'attente de la paire, la durée sous verrou et la configuration du shader compute, avec le même échantillonnage 1/16 exclusivement en Detailed Logging. Aucun nouveau verrou, barrière, drainage ni appel d'horloge en mode silencieux. Le test hôte verrouille la parité entre enum/rapport, vrai chemin source et générateur; ce lot est un instrument de diagnostic, pas encore une optimisation FPS.

## F07 — réutilisation du quota des reprises de shaders échoués (27 octobre)

Les budgets natifs de métadonnées de reprise (64 clés graphiques et 32 compute)
comptaient encore les tentatives **déjà consommées mais toujours en échec**.
Après saturation, un nouveau shader transitoirement indisponible pouvait
rester définitivement nul, sans accès à son unique reprise différée. Le suivi
est désormais libéré après chaque tentative, réussie ou non : l'entrée nulle
du cache de pipeline continue à interdire toute nouvelle tentative pour cette
même clé. Aucun travail supplémentaire sur les shaders valides ni dans la
boucle chaude. Témoins source-extraits O0/O2 : épuisement initial du quota,
réutilisation, absence de seconde reprise et conservation du délai de 2 s.
**Correctif source/hôte à qualifier en CI ; pas de gain FPS/HUD démontré.**

## F07 P0.4 — rollback texture avant enregistrement (27 octobre)

Sur PS5, `CpuModified` était effacé avant `TrackImage`, alors que le
rollback n'était installé qu'après les chemins asynchrones et MSAA.
Une exception lors du suivi pouvait donc laisser une texture non rafraîchie
considérée propre. La garde couvre désormais l'enregistrement ; les retours
MSAA et asynchrones réussis marquent la prise en charge comme terminée.
Le test F04 source-extrait reproduit une exception après suivi partiel,
vérifie l'annulation du suivi et la publication à la prochaine tentative.
**Validation hôte/CI et résultat console encore nécessaires.**

## F07 P0.4 — admission des décodages asynchrones (27 octobre)

Dans le chemin natif, `QueueAsyncDecode` positionnait `IsDecoding` et
inscrivait le contexte avant la préparation des pixels puis `QueueWork`.
Une exception pendant la préparation ou un refus d'admission pouvait laisser
un contexte incomplet sans worker et une image bloquée en décodage. Le
rollback restaure l'ancien état `IsDecoding` et supprime uniquement le
contexte **non admis** ; le décodage précédent reste intact s'il existe.
`QueueAsyncUnswizzle` n'active désormais `IsDecoding` qu'après
l'insertion effective de sa tâche. Témoins C++ `-O0`/`-O2` avec
refus d'enqueue, préparation interrompue et décodage antérieur.
**CI complète et comportement console encore à confirmer ; pas de preuve
de gain FPS.**

## F07 P0.4 — durée de vie des contextes de décodage asynchrone (27 octobre)

Le chemin de consommation des décodages terminés détenait un
`std::unique_lock` sur le mutex du contexte pendant
`async_decodes.erase(i)`. Cet effacement détruit le contexte et son
mutex **avant** que le verrou soit détruit : durée de vie invalide.
Le port natif déverrouille explicitement avant les deux effacements.
Il vérifie également que la longueur décodée correspond à la taille
**actuelle** de l'image avant copie vers le staging. En cas de révision
obsolète, aucun octet n'est copié : l'image est requalifiée
`CpuModified`, désenregistrée si suivie, puis éligible à un nouvel
upload. Le témoin C++ reproduit exactement le `TickAsyncDecode`
actif en `-O0` et `-O2`, avec mutex instrumenté et contrôle de taille.
**Source et témoin intégrés, CI/native/console à qualifier.**

## F07 P0.4 — écriture CPU pendant un décodage en cours (27 octobre)

`RefreshContents` effaçait `CpuModified` puis pouvait placer un deuxième
`QueueAsyncDecode` alors qu'un décodage plus ancien détenait `IsDecoding`.
Une nouvelle révision HUD était ainsi susceptible d'être effacée ou
supplantée par une image obsolète. Le chemin PS5 quitte maintenant
`RefreshContents` **avant** d'effacer `CpuModified` si `IsDecoding`
est déjà actif. Après achèvement de l'ancienne opération, la révision
reste candidate au rafraîchissement normal. Le témoin F04 source-extrait
couvre les écritures concurrentes, l'absence de deuxième admission et
la reprise après achèvement. Tests CI / console encore à confirmer.

### F07 P0.4 — rejet d'une révision décodée obsolète à taille inchangée

Si le CPU modifie l'image pendant l'opération, le décodage antérieur est
également rejeté dans `TickAsyncDecode` même si le nombre d'octets est
identique. Cela empêche les anciennes données du HUD d'être publiées
après une nouvelle écriture ; la révision CPU reste sale et sera reprise.
Témoin source-extrait étendu avec texture de même taille, décodage
terminé, écriture CPU concurrente et contrôle de l'absence d'upload.
Qualification CI/native/console toujours requise.

## F07 P0.2 — laisser les pipelines compute de premier usage prioritaires

Le worker facultatif d'optimisation graphique attendait les builds graphiques
froids, mais ignorait les compilations compute en attente. Un nouveau
`DispatchCompute` pouvait donc subir la concurrence du compilateur
spéculatif. Le port natif compte maintenant les builds compute acceptés
dès l'admission en file, puis libère ce compteur sur achèvement et refus.
`VkPipelineOptimize` patiente tant que graphics **ou** compute reste en cours,
sans attente additionnelle sur le thread GPU. La sortie anticipée lors de
l'arrêt du jeu reste active. Qualification CI et résultat console à confirmer.

## F07 P0.1/P0.2 — priorité compute pendant CFG/IR/SPIR-V

La priorité introduite pour les builds compute ne commençait qu'au moment
de `QueueWork` dans le constructeur du pipeline, tandis que CFG, IR et
SPIR-V avaient **déjà été traduits synchroniquement** sur le thread GPU.
L'optimiseur graphique facultatif pouvait donc continuer à utiliser les
ressources CPU/Vulkan pendant ce travail nécessaire au dispatch courant.
Sur PS5, un scope RAII compte maintenant cette phase **avant** la traduction
compute, uniquement si `build_in_parallel` est activé. Le constructeur
garde sa propre réservation jusqu'à la fin du build driver. L'exception,
le retour anticipé et l'échec d'une traduction décrémentent le compteur
via le destructeur, sans nouveau verrou ni attente sur le thread graphique.
Le préchauffage synchrone du cache disque ne participe pas à ce compteur.
**Contrats hôte et build natif requis avant toute validation de performance.**

## F07 P0.4 — annulation des uploads GPU unswizzle devenus obsolètes (27 octobre)

Une opération `TickAsyncUnswizzle` peut s'étendre sur plusieurs images,
avec un buffer différé et des tranches déjà soumises au GPU. Une écriture CPU
ou un remappage intervenant entre deux tranches rend ce contenu ancien.
Le chemin PS5 annule désormais la tâche **avant** la tranche suivante si
`CpuModified` ou `Remapped` est présent. Si le staging a été créé, il
est rendu via `FreeDeferredStagingBuffer` et **jamais** libéré immédiatement.
Le suivi ancien est invalidé, `IsDecoding` est retiré et `CpuModified`
reste actif pour une nouvelle prise en charge sans cooldown artificiel.
La branche normale et le comportement hors PS5 restent inchangés.
Tests hôte et validation native/console encore nécessaires.

L'annulation remet également `current_unswizzle_frame` à zéro : la
prochaine tâche n'hérite pas de la temporisation de quatre images d'un lot
abandonné. Les tâches propres conservent leur temporisation normale.

## F07 P0.4 — validité des tranches BCn 3D GPU (27 octobre)

Le chemin `TickAsyncUnswizzle` calculait `stride` en u32 puis divisait
plusieurs fois par `bytes_per_slice` sans vérifier une valeur nulle ou
une taille de staging divisible en tranches complètes. Un dépassement du
stride u32 ou un dernier lot incomplet risquait une division par zéro ou
une copie de tranche au-delà de l'allocation GPU. Sur PS5, le stride est
élargi avant multiplication, le produit est borné et les dimensions
incohérentes annulent le lot avant tout transfert, en libérant le staging
de manière différée et en conservant `CpuModified`. Le chemin desktop
n'est pas modifié. Qualification CI/native et résultat console à confirmer.

### F07 P0.4 — tranches excédentaires et profondeur nulle

La validation des uploads GPU BCn 3D exige désormais **exactement** autant
de tranches complètes que la profondeur de la texture (voie accélérée mono-
niveau et mono-couche). Une profondeur nulle ou des tranches excédentaires
sont rejetées avec libération différée du staging. Sans cela,
`image.info.size.depth - z_start` pouvait sous-déborder pendant les lots
suivants malgré le premier contrôle de taille. Tests hôte élargis ;
CI et console encore à qualifier.

Le staging PS5 de ce chemin est désormais demandé **après** la validation
des tranches : les dimensions invalides sont rejetées avant toute
allocation GPU différée, évitant des réservations lourdes inutiles. Le
chemin desktop garde l'ordre historique de ses allocations.

## F07 P0.1/P0.2 — priorité de la traduction des shaders graphiques

Comme pour le compute, la traduction CFG/IR/SPIR-V des shaders graphiques
première utilisation est dorénavant comptée dans les réservations de travail
au premier plan **avant** l'admission du pipeline Vulkan sur son worker. Le
worker d'optimisation graphique facultatif attend donc la fin de cette étape,
puis celle du build Vulkan réel. L'ajout PS5 est activé uniquement quand
`fast_first_pipelines` et `build_in_parallel` le sont ; le préchauffage
synchrone des caches disque n'est pas compté. La garde RAII libère la
réservation après succès, retour anticipé ou exception, sans bloquer le GPU.
Pas de preuve de réduction des stutters FC27 sans mesures console.

## F07 P0.2 — période de repos du worker d'optimisation (27 octobre)

Le worker facultatif `VkPipelineOptimize` attendait la fin des travaux
graphiques/compute froids mais pouvait reprendre entre deux vagues de
compilations à quelques millisecondes d'intervalle. Il attend maintenant
**16 ms continus sans traduction ni build de premier usage** avant de
lancer `MakePipeline`. Chaque travail froid nouvellement observé réinitialise
le délai. La vérification de `cancelled` reste effectuée toutes les 2 ms :
la fermeture du jeu n'attend pas la fin de ce repos. Il n'y a ni nouveau
verrou ni délai sur le thread GPU, et les pipelines de premier usage ne
sont pas ralentis par ce garde-fou. Témoin hôte R444 étendu aux vagues
de travail compute qui démarrent après une première période vide.
**CI et effets console à confirmer ; aucune promesse de FPS.**

## F07 P0.1 — correction du lien natif du compteur de compilation (27 octobre)

Le build PS5 du commit `5245190` a échoué à l'édition de liens :
`undefined symbol: Vulkan::pending_first_use_graphics_builds`. La variable
était dans un namespace anonyme, tandis que le cache de shaders cherchait
le symbole externe `Vulkan::`. Sa définition unique est déplacée au bon
niveau ; les réservations, shaders et fences ne changent pas. La source,
le générateur et le témoin hôte sont corrigés de concert.
**À confirmer :** build natif du nouveau SHA puis résultats console.

## F07 P0.4 — rejet des décodages obsolètes après remappage (27 octobre)

Le rejet des décodages asynchrones périmés couvrait `CpuModified` et les
changements de taille, mais pas `Remapped` à taille identique. Sur PS5, le
remappage invalide maintenant aussi l'ancien résultat **avant le staging**,
restaure `CpuModified`, retire le suivi obsolète et évite de republier les
pixels de l'ancienne adresse. Le comportement hors PS5 n'est pas modifié.
Le test C++ source-extrait couvre désormais un remappage de même taille.
**CI/native et effet FC27 sur console restent à confirmer.**

## F07 P0.1/P0.2 — priorité shader dès l'environnement invité (27 octobre)

La réservation de premier usage débutait dans les surcharges de traduction
`CreateGraphicsPipeline(pools, …)` / `CreateComputePipeline(pools, …)` :
l'acquisition synchrone de l'environnement et le recyclage des pools étaient
encore exposés au worker Vulkan d'optimisation facultative. Les deux entrées
runtime réservent désormais la priorité **avant** ces opérations. Les scopes
RAII imbriqués maintiennent la réservation jusqu'au build Vulkan, sans délai
sur le thread propriétaire et sans changer le préchauffage disque.
**Le coût synchrone reste présent ; gain FPS console non prouvé.**

## F07 P0.2 — file des reconstructions Vulkan facultatives bornée (27 octobre)

`VkPipelineOptimize` utilise un seul worker, mais chaque nouveau pipeline
pouvait ajouter une reconstruction spéculative sans limite de file. Les
changements de HUD avec de nombreuses premières utilisations pouvaient donc
laisser un long arriéré, même si le chemin indispensable `MakePipeline`
rapide était déjà disponible. Sur PS5, l'admission facultative est désormais
bornée à **16 travaux en attente ou actifs**, avec compteur atomique sans
mutex GPU. Les travaux excédentaires conservent le pipeline de premier usage
valide sans allocation ni attente facultative. Les places sont restituées
après achèvement, annulation, échec de compilation ou refus de `QueueWork` ;
les exceptions avant transfert de propriété sont couvertes par RAII. Le
chemin desktop et les builds de préchauffage disque ne changent pas.
**Validation CI/native, mesures de latence et absence de régression console
restent nécessaires.**

## F07 P0.3 — écriture DMA inline sans mutex buffer inutile (27 octobre)

`RasterizerVulkan::AccelerateInlineToMemory` bloquait systématiquement
sur `buffer_cache.mutex`, même si **aucun buffer GPU n'avait jamais été
registré sur les pages CPU ciblées**. Sur la source native PS5 et son pont
DEV, le témoin monotone `BufferPages::NeverRegistered` permet maintenant
d'éviter dans ce cas l'appel inutile `InlineMemory`/`WriteMemory` et la
prise du mutex. La copie vers la mémoire invitée précède toujours le test ;
les invalidations textures, pipeline et requêtes suivent comme auparavant.
Les régions inconnues, les tailles supérieures à 256 Kio, les anciennes
occupations et les chevauchements restent dans le chemin verrouillé.
Le premier enregistrement d'un buffer démarre CPU-dirty : une écriture
DMA antérieure à son existence n'a pas d'ancienne version GPU à invalider.
Un harnais extrait le vrai C++ et vérifie cas connus, jamais possédés,
textures seules, chevauchements, grandes plages et adresses sans mapping.
**Effet FPS/HUD et tests console non prouvés.**

## F07 P0.3 — même TIC répété dans plusieurs stages, sous verrou cache

Le précédent raccourci `FillImageViews` ne réutilisait que le TIC
immédiatement précédent. Dans un draw, la séquence A–B–A refaisait donc la
résolution complète de A tout en tenant les mutex textures/buffers. Le
correctif natif PS5 utilise 16 entrées directes **locales à chaque passe**,
sans allocation et sans cache persistant. Les collisions remplacent une
entrée, les identifiants NULL sont relus, et la réutilisation est désactivée
durant suppression/retry ou blacklist/rescale. La méthode épinglée hors PS5
reste inchangée. Le générateur étend désormais le raccourci consécutif fourni par les
**backports Eden actifs** ; la reconstruction ne repart pas de l'archive vierge.

La prévalidation du SHA précédent a échoué sur un **ancien test inline DMA**
qui n'incluait pas `buffer_pages.h` et supposait toujours une entrée dans le
cache buffer. Le témoin est ajusté pour les pages vraiment jamais enregistrées
et pour les buffers enregistrés, sans toucher au contrat runtime.
**Preuves C++ / CI et amélioration FC 27 console restent à valider.**

**Précision CI :** la première ancre de génération ciblait par erreur
l'archive Eden vierge. La source d'entrée réelle est le backport actif.
L'ancre stricte est recalée sur ce dernier, sans modifier le comportement
natif compilé.

### F07 P0.3 — revalidation des hits TIC et de la fraîcheur HUD

Le mémo conserve uniquement la résolution du descripteur. Un hit effectue
encore `PrepareImageView` afin de rafraîchir les pixels modifiés, traiter
les alias et mettre à jour le LRU. De plus, un view `Remapped` déclenche
`VisitImageView` au lieu de réutiliser son ID : un TIC B rencontré entre
A et A peut avoir invalidé l'adresse GPU de la première vue. Le témoin
C++ vérifie les deux scénarios A–B–A (alias devenu dirty et remappage).

## F07 P0.3 — compute sans images : optimisation retirée après audit

La tentative d'éviter `FillImageViews` pour une liste vide a été **retirée** :
même sans vue, cette fonction remet `has_deleted_images` à zéro avant de
poursuivre. Sauter cet appel laissait un indicateur de suppression/retry
potentiellement ancien après des changements de textures. Le coût d'un
passage vide est négligeable devant le risque de manquer une mise à jour.
L'appel inconditionnel d'origine a été restauré en natif PS5 et dans le
générateur. Le test de la vraie fonction C++ démontre que les listes vides,
y compris en mode blacklist, effacent le latch au lieu de le conserver.

## F07 P0.3 — parcours des render targets propres limité aux images présentes

Sur les draws où `Dirty::RenderTargets` est déjà faux, les IDs des huit
attachements couleur et de la profondeur sont stables, et `rt_active_mask`
représente leur présence. Le chemin PS5 parcourt uniquement les bits actifs
avec `std::countr_zero`, préserve l'ordre des slots puis la profondeur, et
appelle `PrepareImageView` pour chaque image réelle avec les mêmes paramètres.
Les vues nulles n'appellent plus la préparation. La branche dirty,
`RescaleRenderTargets`, le rendu desktop et la gestion des clears restent
inchangés. Le témoin C++ extrait la condition et teste le cas vide, les
attachments clairsemés, la profondeur, les clears, la répétition des draws
et le passage par la branche dirty aux optimisations `-O0` et `-O2`.
**Cette réduction de travail sous mutex ne démontre pas encore un gain FPS
réel sur PS5.**

## F07 P0.3 — copie buffer Vulkan vide sans barrière (27 octobre)

`BufferCacheRuntime::CopyBuffer` continuait à construire le vecteur de
`VkBufferCopy` et à appeler le scheduler lorsqu'il recevait **0 copie** et
`barrier == false`. Le chemin natif PS5 retourne désormais avant ces
opérations : aucun transfert, aucune barrière et aucune soumission ne sont
requis dans ce cas. Les handles nuls conservent leur garde initiale, les
copies réelles et les demandes de barrière conservent exactement leur voie
et le desktop n'est pas modifié. Le harnais source-extrait l'amorce C++
réelle et teste handles invalides, copies nulles, barrière seule, 1 et
plusieurs copies, en modes natif/desktop et `-O0`/`-O2`.
**Ce raccourci évite des soumissions inutiles mais n'est pas une mesure
réelle des FPS console.**

## F07 P0.3 — rejet anticipé d'une plage vertex invalide

`BufferCacheRuntime::BindVertexBuffers` calculait une plage vide, inversée
ou hors limites **après** avoir résolu tous les handles et éventuellement
réservé les buffers NULL de remplacement. En PS5 natif la validation de
`GetMaxVertexInputBindings()` passe avant le tableau local et les appels
`Handle()` ; les plages admises conservent leur chemin Vulkan exact. Le
contrôle existant de non-débordement demeure ; un témoin C++ supplémentaire
exécute la nouvelle amorce de méthode avec de vraies résolutions simulées,
prouvant l'absence de lectures/réservations pour les rejets et leur présence
sur une plage valide, à `-O0`/`-O2`. Les sources Eden/backports restent
inchangées ; l'override est reproduit par le générateur Vulkan strict.
**Aucun effet mesuré sur FC 27 console à ce stade.**

## F07 — empreinte historique des copies Vulkan et patches successifs

Le fast gate de `5dc2e7fc` a échoué sur une empreinte SHA-1 du module
`vk_buffer_cache_cost.cpp` **avant** l'optimisation des captures de copies.
La reconstruction du fichier historique annulait déjà les changements
de captures différées et le snapshot de tick, mais pas les deux nouvelles
transformations F07 indépendantes (copies vides sans barrière et validation
précoce de la plage vertex). Le témoin annule désormais ces deux
transformations dans l'ordre inverse directement depuis les ancrages stricts
du générateur, puis conserve la comparaison avec **l'empreinte historique
inchangée**. Un déplacement ou une divergence des blocs natifs fait échouer
le témoin, plutôt que d'actualiser artificiellement le SHA.

## F07 P0.3 — éviter les handles vertex exclus par le plafond Vulkan (27 octobre)

Après validation précoce des plages, `BindVertexBuffers` continuait à
résoudre les handles de toutes les entrées invitées, même lorsque la limite
`GetMaxVertexInputBindings()` tronquait une plage par ailleurs valide.
La branche PS5 prépare désormais seulement les `binding_count` handles
transmis à Vulkan ; les tableaux hôtes trop courts sont rejetés avant
tout accès ou enregistrement différé. Le chemin desktop et l'ordre des
bindings admis restent inchangés. La reproduction strictement épinglée
et les témoins O0/O2 sont mis à jour, y compris la reconstruction de
l'empreinte historique des copies différées. Ce changement ne prouve
aucun gain de FPS ou de fraîcheur HUD sur console.

## F07 P0.4 — exclusion d'un framebuffer en décodage asynchrone (28 octobre)

Le filtre de présentation accélérée écartait déjà les images remappées ou
marquées `CpuModified`. Or cette marque est effacée dès la mise en file d'un
décodage asynchrone : l'image Vulkan précédente pouvait alors être sélectionnée
pendant que le nouveau contenu restait `IsDecoding`. Le chemin PS5 exclut
aussi les candidats en cours de décodage et emploie le téléchargement normal
du framebuffer invité jusqu'à la disponibilité de l'image. Les images GPU
propres restent accélérées ; aucune attente ni lecture d'horloge ajoutée.
La source sélectionnée, la régénération stricte et le témoin C++ O0/O2
couvrent ce passage. **À vérifier par CI sur le même SHA, puis en jeu :**
ce correctif ne constitue pas une preuve de disparition du HUD retardé.


## F07 P0.4 — aliases concurrents de framebuffer (28 octobre)

Audit complémentaire du chemin de présentation accélérée : si plusieurs
images correspondent à la même adresse invitée, écarter seulement l'image
avec `IsDecoding` laisse une autre vue « propre » potentiellement ancienne.
Le chemin PS5 interdit désormais **toute** sélection accélérée pour cette
adresse tant qu'au moins une image correspondante décode de nouveaux pixels ;
il prend la voie existante de chargement des octets invités. Les vues
`Remapped` et `CpuModified` continuent à être filtrées individuellement.
Le témoin source-extrait couvre le cas où la vue propre apparaît avant ou
après celle en décodage, ainsi que la reprise de l'accélération après
publication. Cela garantit un choix conservateur, **pas** la fraîcheur
observée du HUD ni un gain de performances sur console.


## F07 P0.3/P0.4 — sélection framebuffer sans allocation sous mutex (28 octobre)

Sur PS5, la sélection des vues de présentation conservait toutes les images
admissibles dans un `small_vector<4>`, puis lançait un second parcours pour
retrouver la dernière modification. Avec plus de quatre alias simultanés,
le vecteur pouvait allouer sous `texture_cache.mutex`. La branche native
conserve maintenant uniquement l'identifiant et le tick du candidat le plus
récent pendant le premier parcours : **pas d'allocation de liste ni de second
balayage**, à condition qu'une vue soit admissible. Les ticks identiques
conservent le premier candidat, comme `std::ranges::max_element`. Tout
`IsDecoding` correspondant continue d'imposer le repli vers les pixels
invités, même après la rencontre d'une vue propre. Le desktop conserve
strictement son ancienne sélection. Le témoin source-extrait C++ couvre
l'ordre inversé, les égalités, les vues sales/absentes et sept alias en
`-O0`/`-O2`. Optimisation structurelle, **gain de latence/FPS PS5 non mesuré**.


## F07 P0.4 — alias CPU modifié/remappé et ancien framebuffer propre (28 octobre)

Le filtrage précédent rejetait tout `IsDecoding` présent à la même adresse
invitée, mais utilisait encore `continue` pour une autre image marquée
`CpuModified` ou `Remapped`. Lorsqu'un framebuffer possédait plusieurs
images associées à la **même** adresse, une vue plus ancienne mais propre
pouvait donc rester candidate, même après écriture CPU ou remappage d'un
alias. Sur PS5, ces états imposent maintenant le même **repli sûr vers
`UpdateRawImage`** pour l'adresse entière. Le chemin accéléré mono-parcours
reste disponible après rafraîchissement de tous les alias. La comparaison
C++ source-extrait `-O0`/`-O2` exige échec de l'ancien garde et succès
du nouveau, y compris avec un alias sale sans vue. Le desktop conserve
son comportement. Aucun résultat de fraîcheur HUD ni de FPS **console**
n'est revendiqué ; le correctif peut ajouter des uploads quand des alias
sales coexistent avec un framebuffer GPU plus récent, à qualifier en jeu.


## F07 P0.3 — compute descriptor-buffer reuse, 28 octobre

La source compute allouait un nouveau bloc de descripteurs à **chaque** dispatch, même à contenu identique. PS5 réutilise maintenant le précédent offset/chunk seulement si son contenu, sa taille et la génération du ring correspondent ; `TouchFrame` conserve la durée de vie de la soumission. Le contenu est comparé après acquisition des caches, avec capacité réservée avant les deux mutex. Un changement de valeur/génération ou un échec d'allocation conserve la voie normale. La prévalidation fait un `Finish` anticipé seulement en cas de nouvelle allocation **garantie** ; une modification non prévisible suit l'ancien fallback. Desktop inchangé. Témoin source-extrait C++ O0/O2 : réutilisation native, desktop original, échec attendu du chemin précédent et reprise après allocation refusée. Aucun gain FC27 sur console revendiqué.

### F07 — relevé matériel FC27, 1er novembre 2026 (diagnostic détaillé)

Sur le binaire **`6271928eb7b5d50687fccc730ae706986f3d6108`**, FW13.60, 89 fenêtres de `heap(20261101-071933).log` totalisent 13 060 frames, 129 retards >50 ms et 6 >500 ms (pic 617,308 ms). Les **359 shaders froids uniques** (304 graphics, 55 compute) totalisent 2 513,541 ms de CPU, dont **2 083,282 ms en IR (82,9 %)**. Les 89 mesures JIT rapportent 0 ms ; les attentes de cache cumulent 1 098,514 ms. Ces durées de fenêtre ne se convertissent pas en coût d'une frame et les événements shader ne contiennent pas de frame ID. **P0.1 reste une cible mesurée**, mais les gels de présentation/IPC ne sont pas attribués ; ne pas déclarer les 30 FPS stables. Le vendor plus récent a déjà porté le préchauffage global à 32 (ancien binaire : 8), sans qualification console sur ce relevé. Preuve détaillée et limites : [registre F07](F07_BATCH_EXECUTION_REGISTER.md#f07--trace-matérielle-fc27--coût-des-shaders-froids-1er-novembre-2026). Aucun changement moteur ou lancement natif par ce relevé.

### 21 novembre 2026 — FC27 NS1 : déduplication du budget des tableaux de textures (branche isolée)

- **Preuve spécifique titre** : `0100C49025D3E000`, étude `seedds/nxnative/dm/games/0100C49025D3E000/README.md` et `docs/reference/shaders.md` : le shader pixel `dc446d7f52c14ea6` utilise la table `c2[0x168+8*i]` et un sampler séparé `c2[0x570]`; l'amont signale aussi des shaders de skinning avec `<<4` perdu. Leur backend Metal/Ryujinx est différent du recompiler Eden/Vulkan, donc l'équivalence du bug n'est **pas** présumée.
- **Défaut autonome prouvé dans la source PS5 compilée** : `DynamicSampledTextureArrayCount` comptait chaque instruction d'échantillonnage dynamique, tandis que `Descriptors::Add(TextureDescriptor)` fusionne les instructions réutilisant une identité identique. Le budget partagé pouvait être divisé à tort puis imposer `UMin(..., count-1)` sur les indices de handles authentiques. Correction générale dans `vendor/encore-active/eden-shader/src/shader_recompiler/ir_opt/texture_pass.cpp` : compter les **identités distinctes** (type/depth, CBUF principal et secondaire, count, stride), sans changer l'ordre des lectures ni les limites Vulkan.
- **Provenance** : vendor correctif `f710080ff1c827c1ae3c5ee2a1e0a588264ff9bc`; vendor branche `908ba2928b8b7aca75b2baeaedeebc9fb21ad282` (inclut les deux correctifs de durée de vie builder antérieurs et l'alignement de tests existants); moteur gitlink mis à jour sur `94a577ec4917321e6261d0dc3a54c00966a6ec66`, branche `opt/ns1-fc27-runtime-20261121`. `main` inchangé.
- **Qualification** : témoin C++ d'identité/budget compilé et exécuté Clang/GCC × O0/O2 avec UBSan : **4/4 PASS** sur environnement hôte ; tests GitHub/CI complets, compilation native PS5, première image FC27 et correctifs visibles **non validés**. Ce correctif ne démontre **ni** la résolution des maillots **ni** des pauses de pipeline et ne justifie pas un test console isolé.
- **Écarts non confondus** : `GlobalMemoryToStorageBufferPass::StorageOffset` soustrait le CBUF de l'adresse calculée sans supprimer le décalage `<<4`, donc le bug spécifique de nxnative ne se transpose pas directement ; les deux bindings Vulkan actifs gardent `secondary_cbuf_offset` fixe pour le sampler séparé ; le RADV sélectionné déclare `dualSrcBlend=true`, `maxFragmentDualSrcAttachments=1`, et le SPIR-V publie les deux sorties à location 0 / index 0 et 1. Ces conformités source ne prouvent pas les pixels PS5.


### 21 novembre 2026 — FC27 NS1 : copie Vulkan du plan D32S8/D32

- **Retour nxnative examiné :** [copies du plan de profondeur EA SPORTS FC27](https://github.com/seedds/nxnative/blob/main/docs/reference/rendering.md#depth-plane-copies-between-depth-formats) — format D32+stencil vers profondeur D32 et sens inverse. Le chemin Vulkan Encore actif refusait les deux formats dans `ReinterpretImage`, et sa conversion largeur utilisait les 8 octets packed D32S8 au lieu des 4 octets du plan profondeur.
- **Correctif runtime général :** vendor [`9203bd8`](https://github.com/niakw/Prospero.Eden-Encore-vendor/commit/9203bd82636e0d4e2c68d8fc169bdd7a1a11a5d0) copie via l'intermédiaire Vulkan existant uniquement le plan 32-bit DEPTH, sans modifier le stencil et sans requalifier les autres mélanges de formats. [`f93d595`](https://github.com/niakw/Prospero.Eden-Encore-vendor/commit/f93d595495bb7a029040fb574cb977e8283a2971) alloue le scratch à 4 B/texel sur ces deux transferts (1920×1080 : 8 294 400 octets utiles au lieu de 16 588 800 lorsque la destination est packed D32S8).
- **Chaîne source :** moteur gitlink [`825ab577`](https://github.com/niakw/ProsperoEden-Encore/commit/825ab5779d30f1c26833c49c3da850c5d2d11edb) → vendor `f93d595`. `tools/prepare-vulkan-port.py` contient trois deltas stricts de reconstruction et les témoins source coordonnée/region/aspect existants ont été étendus ; contrôle de concordance exacte des trois blocs C++ passé. Test numérique autonome Clang C++20 ASan/UBSan de taille scratch passé. **Aucun run complet de ces témoins, compilation native Vulkan, CI, build PS5 ou comparaison de pixels FC27 exécuté ici.** Les maillots, textures, HUD et pauses longues restent des symptômes ouverts ; pas de gain FC27 mesuré.

### 21 novembre 2026 — FC27 : mesure réelle des pauses et garde DMA image GPU-22 (branche NS1 isolée)

- **Source console de référence, non retestée :** `heap(20261120-231706).log` et `boot-trace(20261120-231706).txt`, binaire `98ef8a8ec7329a769cb0598c74dc04cf43b95e1d` (**antérieur** au couple NS1 actuel). Le journal contient deux sessions, **700** lignes `EDEN_VULKAN_SHADER_MISS` et **45** `EDEN_VULKAN_PIPELINE_WAIT`, dont une attente graphics de **241,576 ms** (`wait_ns=241575616`, `usable=1`). Des premières traductions shader ont atteint environ **188,54 ms**, et des fenêtres de 5 s montrent des intervalles maximaux de **639,350**, **716,387** et **641,039 ms**. D'autres fenêtres restent à 30 FPS avec un pire intervalle autour de 33–35 ms. **Les longues pauses sont avérées et ne se résument pas au FPS moyen.** Les métriques ne démontrent pas que toutes les pauses ont une cause unique ; plusieurs fenêtres lentes ne comptent pas de nouveau shader. Les politiques workers (souvent un seul worker shader confirmé sur le masque secondaire) et le préwarm 32 déjà actifs ne doivent pas être augmentés sans preuve CPU/GPU supplémentaire.
- **Correctif C++ générique nouveau, GPU-22 :** [vendor `5ec4f2b`](https://github.com/niakw/Prospero.Eden-Encore-vendor/commit/5ec4f2b00b4d2b6bed1e226abd244871beb3fd48) sélectionné par `headless/vulkan.cmake` : le transfert DMA accéléré buffer↔image ne peut plus traduire une plage GMMU **non contiguë** comme un seul `BufferCache::ObtainBuffer` physique. `AccelerateDMA` suit le **canal courant** via référence au pointeur rasterizer ; refus précoce avant lookup image et effets de bord, retour au fallback MaxwellDMA page-aware. [Moteur gitlink `6199ccb`](https://github.com/niakw/ProsperoEden-Encore/commit/6199ccb30c244f8e156825b0858b069cde082654).
- **Qualification** : 10 vérifications de source/provenance passées, différentiel image-méthode exact de 601 caractères contre le miroir historique, recette de reconstruction à cinq deltas ; test du fichier `tools/check-ps5-f07-dma-image-prelock-span-host.py` étendu aux deux directions et au rebind. Modèle C++20 indépendant Clang/ASan/UBSan : PASS. **Pas d'exécution des oracles complets du dépôt, pas de compilation native PS5, CI finale, ELF ni pixels/frametimes FC27 du nouveau couple SHAs.** L'issue SH-13 (shader/pipeline stalls), les maillots, le HUD et la pause manette restent **ouverts**.


### 2026-11-24 — AM observer lifetime and stabilization host gates

- Vendor `b5c6f089a6aecd321d08a40238f3cd502f505b26`, engine integration `816624a9acfb4dfe10d526e3210a0ec2f87b91fb`: shared AM observer retains the applet and exact KProcess across asynchronous wait; stale signals cannot mutate replacement processes; null waits are guarded. Eden upstream PR #4709 is relevant to the lifetime defect. This is not yet proof of the FC27 exit-crash root cause.
- Isolated C++ lifetime model passed Clang O0/O2 with ASan/UBSan; not a full emulator compile or console test. Final FC27/P0 host gate passed on engine `c0ea4f06d7e846bf80dc1dc167a3f01cdd40fb52` with the same vendor. Vulkan reconstruction passed; further host gates were under repair/revalidation. No native PS5 build triggered. Six-lot closure and FC27 hardware qualification remain open.

### 2026-11-24 — active renderer stabilization (lots 5/6)

- Engine `11fb79d83f02f9e68680d1c33f84d9810d27f6bd`: host renderer handoff fixture now mirrors `game_frame_presents`, seeds reused slots and asserts reset to one. Prior Fast Gate job 138153131530 failed because the fixture lacked this field.
- Engine `1abdce4770f46d679a1f1dc3db35ce2453e9b346`, vendor `b5c6f089a6aecd321d08a40238f3cd502f505b26`: CMake selects `headless/vulkan_renderer_r08.cpp`; LSFG uses the same generation-mode snapshot as the other generators. Destructor drains the independent presenter after the scheduler and before session destruction/device idle; presenter exceptions are recorded via the existing GPU failure path. This does not establish the console crash root cause. Existing wiring checks assert selection and ordering.
- Preflight audit job 138155307794 failed on a known GPU dirty-manager blob because the exact vendor cohort list ended at 887bf44. Compared 887bf44..b5c6f089: only shader drain, AM lifetime and tests changed; admit the three exact successors while preserving all owner hashes and historical receipts. Revalidation pending. R457 run 45306991419 passed on engine 99a21e9c, same vendor. No native PS5 build or console test triggered; all six lots remain open pending qualification.

### 2026-11-24 — NS1 parallel shader retry and host gate repair (lot 1)

- Active vendor `dc9f5f95b1f784bb358d6480e53de7247d61d777`, engine integration `9dc91cfc4e0f166f54b4b955e13b9bc1bd60df2f`: separate parallel environments, drain accepted jobs on exceptional exit, retry snapshot read/allocation failure once on untouched serial environments and serialize the successful environment. NS2 translation path unchanged. Prior source receipts reconstructed byte-for-byte; historical hashes unchanged.
- Engine `2388e1e11562f183a694b076fb75d6016756fa03`: repair dirty-memory test anchor ordering, SM exact owner cohort, launcher helper extraction and preflight whitespace. Engine `642e556a7df2e79f08e65b2eec9fcf8efa18b735`: retain exact shader retry reconstruction in both native and generated source oracles. Source-extracted retry caller host witness covers successful parallel/serial, failed parallel, copy allocation refusal and unrelated exception propagation; execution remains pending.
- GitHub run 45308862936 (Final FC27/P0), 45308862867 (R457 NS1/NS2), 45308862949 (NS2 baseline), vendor 45308859614 (CPU-write readback race) completed successfully for the new vendor. Fast Gate 45308973193 failed on pre-retry generator block anchor, fixed in 642e556a; latest gates still require revalidation. No native PS5 build or console validation. Six-lot closure remains open; no FPS, texture, HUD, pause or exit-crash improvement asserted.

- Additional runtime correction: vendor `a441295022b23834f8531c54d2b0965f84023278` gates all Maxwell register reads for snapshot preparation behind live parallel translation admission. Disk prewarm uses FileEnvironment and explicitly passes build_in_parallel=false, so prior unconditional register reads could dereference an absent/stale channel. No change to admitted live snapshot content; NS1/NS2 serial prewarm no longer needs this live state. Source exact reverse updated. No console or native build validation.

### 2026-11-24 — Vulkan submit callback lifetime (lot 6)

- Vendor `7c5d5220dd4df4a531418458ab623ef86c41348c`: the active PS5 scheduler replaces `on_submit` under the same `execution_mutex` that protects worker execution. Renderer construction/teardown are its only registration owners; the worker can no longer invoke a concurrently replaced `std::function`. No additional lock per submission. Exact generator parity and historical reverse receipt retained; existing worker host test extended for registration blocking. Native build, CI and console outcome not yet qualified. This is not proof that the FC27 exit crash is resolved.

### 2026-11-24 — native disk prewarm worker exception handoff (lot 1/6)

- Vendor `44540549ee9a65eb8078e271f43ccded0e8e984f`: the active bounded prewarm jobs capture their first exception under the existing state mutex and relay it on the loading owner only after the non-cancelling drain. Neither NS1 nor NS2 may terminate the process from an escaping prewarm worker exception; the failed load is not advertised as successful. No new queue, hot-path lock or draw policy. Host/source and console qualification tracked separately.

### 2026-11-24 — renderer shutdown ownership (source)

- Active R08 renderer: drain the recording worker before the last synchronous submission, drain the independent presenter, check the actual device-idle result before releasing FSR3/Mihawk sessions. On an exception without quiescence proof, latch the cause and retain the existing fail-closed policy. No gameplay-path wait added.
- Outstanding: a failure of the final submitted tick can still strand the timeline waiter; complete recoverable shutdown after fatal GPU failure requires failure-aware semaphore and fence-worker handling. No assertion of successful PS5 exit or native build.

### 2026-11-24 — shared native fatal GPU wait propagation

- Select the full native master semaphore TU and matched generic/Vulkan fence headers in `headless/vulkan.cmake`, removing the pristine master semaphore TU from the native source list. Preserve exact original Eden sources and the pinned vendor gitlink.
- A pending timeline or fallback fence wait observes the persistent failure latch. The polling interval is not a GPU execution deadline. Failed host fence waits neither reset/recycle a pending fence nor advance the completed tick. Keep the pending fence owned by the queue until safe teardown.
- Forced guest-fence waits own their callback completion state; a worker failure propagates without a dangling stack callback. Queue publication unlocks on exceptions, the worker reports fatal errors, and Vulkan stops the fence worker before derived destruction. Source-extracted ASan/UBSan witness is wired into existing CI. Console behavior is not qualified; no native build requested.

- Fence-emulation submission allocates its queue node before calling Vulkan and latches a rejected submit under the same queue mutex. The fallback completion CV wakes immediately on real tick completion (10 ms polling is only for observing an unrelated fatal latch). No fabricated GPU completion or fence reuse after an error.

- Native scheduler now destroys all remaining command captures after exceptional execution, observes fatal state before further dispatch and bounds the missed-notify window without reversing queue/execution locks. Native presenter checks discarded-frame submits and present-fence waits, observes external fatal state when the free queue is empty and joins before member destruction. The six selected native owners are classified separately from the immutable F07 catalogue. Fatal device retirement remains distinct from propagation; no native build or console qualification.

- Device-lost teardown: stop fence callbacks, scheduler and independent presenter in producer order before calling `vkDeviceWaitIdle`. Only success or device lost authorizes resource retirement (Vulkan Lost Device: https://docs.vulkan.org/spec/latest/chapters/devsandqueues.html#devsandqueues-lost-device). Never mark failed guest work as complete. Unexecuted command captures and retained deleted buffers are released only after retirement proof. All remaining owner lifetimes and real console recovery still require native qualification. No native build requested.

### 2026-11-24 — Selected NS1 TextureCache HUD parity

- Vendor `d63d82dfb9c2afbacac4c9dc1491f743fb083d52`: four reviewed hunks in the PS5-selected `ns2-astc` header: missing sampler recovery, valid-to-NULL generation publication, zero-view retirement guards for channel views and framebuffers. No new synchronization policy.
- NS1 host mock O0/O2 UBSan: 2,000 missing sampler cases recovered; 1,000 remap-generation misses eliminated; 512,000 empty retirement scan visits and 1,000 mock flushes eliminated. Counts are synthetic, not FC27 event frequency or FPS.
- Existing texture/mapping/retirement/F03 source-extraction guards now read the selected header. Historical vendor TIR audit reverses the exact four hunks on its audit copy only. Native PS5 and guest HUD freshness remain unverified.
- FC27 trace: Options-to-Plus host edge between 163.56 and 168.72 s after first frame callback; 58,750 subsequent polls (~242.4 s). No guest NPad LIFO trace in those files. No evidence of guest consumption latency; no mapping changes.

### 2026-11-24 — Native R08 compositor layer retention (lots 3/5/6)

- CMake's shipping `headless/vulkan_blit_screen_r08.cpp` and matched header had missed vendor F07 C04 append-only layer retention. Integrate its bounded reuse in the actual PS5 owner; R08 also covers Anime4K Details/Soft/Denoise constructor extents. The active window adapter consumes exactly the active config count, so retained layers are not drawn.
- Finish the scheduler before draining the independent present queue, and check actual device idle before destroying resources. Clamp MaxExtraFrames to the actual allocated frame pool, not just the recreated swapchain count. No added per-frame global wait.
- Local C++20 O0/O2 UBSan model: 240 compositions alternating 1/3 layers, 239 hypothetical old global idle requests vs zero new; six filter resize cases, 88 pool-capacity pairs, failure retains previous layer owners. The workload is synthetic NS1, not reconstructed FC27 layer events or real GPU performance. Existing C04 host witness now extracts the active engine source; native/console validation pending.
- Vendor synchronous page-protection witness updated to accept only reviewed TextureCache blobs and keep semantic guards. R437 audit reverses exact multi-channel buffer deletion delta; whitespace fixed. No new native build.

### 2026-11-24 — R08 loading and generated-frame callback publication

- Active R08 `PresentLoading()` and LSFG loop now dispatch the scheduler chunk containing the present callback directly after recording it; do not wait for a later guest draw/flush to publish the frame. No extra GPU submission is requested by `DispatchWork()` itself. Preserve real-frame FIFO and the single existing render flush. The local C++ mock of deferred scheduler callbacks passed O0/O2 UBSan for 1,000 loading sequences per optimization, with one flush each. Existing host handoff test adds source-extracted loading/LSFG tails; CI and native PS5 outcome pending. No claim that the previous FC27 gameplay pauses were caused by loading publication.


### 24/11 — retest PS5 ee5d6d57 : P0 sortie + P1 cache chaud
- Title 0100C49025D3E000, source console ee5d6d57d7d433b8406d1411d348ca60d304e2eb : deux arrêts identiques « guest wait after device retirement » (eboot+0x42125), 3850/4120 MiB libres, aucun watchdog/accès mémoire invalide. Le correctif R24 de destruction après retraite est déjà intégré mais reste à qualifier sur console.
- Mesure détaillée : 10234 intervalles / 351,36 s, 29,13 FPS, 30 intervalles >100 ms, 3 >500 ms, maximum 619,819 ms ; la contention BufferCache n'explique pas toutes les pauses. Préchargement chaud 128/650 enregistrements, 2413 ms. 242 marqueurs de compilation en jeu.
- Vendor `7e3565e51c6ee048a040796b63a144a2e9354c9d` : LoadDiskResources sélectionne les clés complètes compute/graphics distinctes les plus récentes, au lieu de dépenser le quota 128 en doublons d'enregistrements append-only. Pas de changement de quota, clés, ordre des draws, fences ni invalidations. Test hôte extrait du bloc actif (clés typées, remplacement dernier, éviction, jobs move-only) intégré ; CI et bénéfice console à confirmer. Aucun build PS5 lancé.

- FC27 BufferCache native successor `752b92033610b294a36254d5747c317aca51c1d5`: one-pass retirement of completed overlapping GPU downloads (Lichii range_sets.inc), preserving zero-count callback order and positive reference counts. Restore both move-assignment return references, self-move safety and valid empty moved-from owners following Lichii 8cd5c6a44b. Local Boost.ICL differential model, Clang C++20 O0/O2 ASan/UBSan: 100,000 operations per build, identical maps and callback sequences. Existing vendor host witness reverses only the five new hunks. No full native compile, FC27 performance or hardware claim. No PS5 build requested.

- FC27 shader-cache reader `1b5256d72072e05a62fb734bc9ef790fc81c1573`: selected CMake shader_environment.cpp includes the maintained reader. A caught std::bad_alloc during deserialization or prewarm callback previously truncated the valid suffix as though it were damaged; retain the complete file on allocation failure. Exact source blob 5d652ca -> 4ae7312; isolated C++20 source fixture O0/O2 ASan/UBSan passed six injected failures with byte-identical cache and successful retry, while the old reader failed. Corrupt-tail repair and stop remain unchanged. No evidence that FC27 had this particular allocation failure in the last session; no native or hardware performance qualification. No PS5 build requested.

- FC27 disk graphics prewarm vendor `628d01bdc4368e9ad661d749515f788ef7c03802`: validate exact Maxwell stage order/count against the nonzero key slots, then allocate all six guest program pointer slots (VertexA/B plus TC/TE/G/F), not five Vulkan stages. Eden mirror retains the historical five-pointer capacity. Local C++20 model using identical admission statements and actual Boost static_vector: 63 accepted nonempty masks, 375 malformed counts/orders rejected at each of O0/O2 ASan/UBSan; original capacity throws on six. No title-specific occurrence, full native compiler or hardware performance claim. No PS5 build requested.

- 24/11 FC27 — attribution du pire gel et lot BufferCache collecté : le log `crash-20261124-122139-heap(1).log` montre 242 shader misses mais une seule attente pipeline (22,612 µs). La fenêtre la plus lente atteint 619,819 ms ; sur ses 5,02685 s, les attentes de caches totalisent 381,169 ms, dont 307,979 ms BufferCache et 73,190 ms TextureCache, avec JIT nul et aucun draw-drop. Le runtime avait déjà le filtre `GPUDirtyMemoryManager::MayHavePending`, mais `OnCacheInvalidations` prenait encore BufferCache deux fois : une fois pour `ClaimCpuWrites`, puis une fois pour appliquer le batch. Vendor `191dd458c68de13f0f71659e3b4a9598af7de561` adapte Lichii `5e428570` / `f5edeab` : texture une fois, puis claim + toutes les écritures buffer sous une seule acquisition, puis shader, en conservant les filtres de pages Encore. Le test FC27 existant compile la méthode sélectionnée et exige désormais 1 acquisition buffer/1 texture par batch. Pas de gain FPS ni de résolution console revendiqué ; build PS5 non demandé.

- Vendor `b743e9c7ec9832832711fc0ea34e03a25c973557` est un successeur **test-only** de `191dd458c68de13f0f71659e3b4a9598af7de561` : runtime C++ inchangé (rasterizer `e4948333`). Le témoin historique de protection synchrone inverse explicitement le delta de batching avant de rejouer son reçu. Gitlink moteur synchronisé, sans build PS5.

- FC27 BufferCache UsageTracker vendor `4c8f72f8ba3db320af55cea0f53cac16366c3ea0` : le header PS5 réellement sélectionné conserve la granularité 64 octets qualifiée mais `Reset()` efface uniquement l’étendue de mots touchée depuis le reset précédent (`set_begin/set_end`), adaptation de Lichii 5e428570/7a5e5357. Le test exact-source conserve les 16 000 opérations oracle, les cas sous-64/page/multi-page/overflow et ajoute reset vide + extrêmes distants. Rasterizer/batching et ordre GPU inchangés ; bénéfice console non mesuré, build PS5 non demandé.

- FC27 collected invalidation preflight vendor `6affc4ad869a3eaab9d1bed1e65de8872d93363b`: `OnCacheInvalidations` décide désormais la participation TextureCache/BufferCache en un seul parcours monotone des ranges et s'arrête dès que les deux domaines sont connus. Rasterizer `fcd174ed`; verrouillage, ClaimCpuWrites, rechecks sous verrou et invalidation shader inchangés. Le reçu historique `4e10cd67` inverse ce delta puis le batching précédent. Aucun build PS5 ni gain console revendiqué.

- FC27/NS2 active TextureCache vendor `b92d4183cec69e65216162cf61e451eff643caa0`: CMake selects ns2-astc, which lacked the historical Vulkan readback batching and dirty rollback. Reinstate ordered 40-image/32 MiB batches, keep staging deferred until guest publication (including unwind), restore GPU dirty state on failure and reset traversal Picked flags on exceptions. Exact readback method copied from commit, local C++20 Clang O0/O2 ASan/UBSan: seven batch cases, five injected failure phases, ordered pixels and balanced staging lifetime. Traversal guard source-reviewed, not separately compiled. No title occurrence or FPS gain demonstrated. Native PS5 build not requested.

- 24/11 — FC27 selected TextureCache readback exception retirement, vendor `84d3b0398ae7db1618899815bc1f98894453fbf6`: in PS5-selected ns2-astc `DownloadMemory`, a failure after recording GPU readbacks now attempts `runtime.Finish()` before returning deferred staging to the pool; if retirement fails, staging stays deferred to prevent unsafe reuse. No additional wait on the success path. Host historical witnesses were updated for this exact delta. Native PS5 and real frame pacing **not validated**; no PS5 build requested.

- 24/11 — FC27 readback publication: vendor `1949a57c930d3ebd32bdd93093763ae22681a4a4` from `84d3b039`; selected `eden-core/src/video_core/buffer_cache/buffer_cache.h` adds a PS5-only `RangeSet::Intersects` fast path before constructing the temporary write-protection interval set. CPU-overlap downloads preserve the original subtraction and byte ownership. Existing CPU-write/readback host regression extended for disjoint, empty and protected spans; GPU/PS5 frametimes remain **unverified**, native build intentionally not triggered.

- 24/11 — **FC27 NS1, ID `0100C49025D3E000`, DMA block-linear 3D** : les logs PS5 du 24/11 à `+455.492s` montrent des appels répétés à `MaxwellDMA::CopyPitchToBlockLinear` refusés après les premières soumissions GPU invitées. Vendor `2ecccebce83cd169f1820d9c4674698f6353fa48` : autorisation des volumes/profondeurs de GOB que `SwizzleSubrect` sait parcourir, enveloppe complète 3D vérifiée en 64 bits avec budget de 64 Mio et vérification des lignes sources inter-tranches ; largeur de bloc non nulle/couche de destination non nulle toujours refusées. Test de conversion des tranches Z ajouté à la suite publique GOB existante (Clang/GCC ASan/UBSan). **Ne démontre pas que les appels du journal utilisaient cette géométrie, ni une amélioration FPS, une première frame, ou une validation console sur ce couple de SHAs.** Aucun build natif PS5 déclenché.

- 24/11 — **NS2 MaxwellDMA / pavage natif GOB** : Lichii `nx2` transmet `memory_manager.UsesNativeTiling()` aux transferts block-linear ; les mêmes API étaient déjà correctes dans `engine_upload` et le blitter, mais les neuf chemins actifs MaxwellDMA utilisaient encore le pavage NS1 implicite. Vendor `d40e212b2c8124225ff8d6adc06f459955e42a6a` : propagation du drapeau du canal NS2 authentifié à 9 conversions/remaps/alias, en conservant `false` pour NS1 et toutes les protections de tailles/mapping. Test hôte vendor R3 vert (comparaison des octets de pavage NS2, tranches Z, Clang/GCC ASan/UBSan). **Non qualifié sur PS5 : aucune première frame invitée ni gain de textures ou de FPS démontré.**

- 24/11 — **NS2 TextureCache central / GOB natif** : vendor `b3458252ec923444b3add94ff50a4a76e2bc4570` : les deux conversions `SwizzleTexture` / `UnswizzleTexture` de `encore-active/eden-core/src/video_core/texture_cache/util.cpp`, unité CMake active, utilisent maintenant `gpu_memory.UsesNativeTiling()` uniquement sur PS5 native. Le pavage NS1 et la signature desktop restent inchangés ; validation hôte R3 GOB Clang/GCC verte. Le moteur reprend le gitlink exact et les SHA arbres historiques sans prétendre une frame PS5 obtenue.

- 24/11 — **Fermi2D software nearest-neighbor NS1/NS2** : vendor `f3322eb09b8b4bbf1c589d1e96ff454cd5fb2c5d`, active blitter blob `6a18c9825936bd72b9919335ce5f8c2590183ab9`. Eden mirror and Lichii nx2 share the defective combined 32.32 X/Y addressing. Independent integer rows and exact remainder stepping of columns now drive both packed and float samplers. Local C++20 reproduction of the replacement helpers passed 20,736 geometries per O0/O2 ASan/UBSan build against an integer oracle; existing source-extraction witness extended. Native GOB flags, memory bounds and GPU ordering unchanged. No specific FC27 occurrence, FPS gain, native build or console qualification demonstrated.

- 24/11 — **FC27 NS1 Fermi2D / destination 3D `DST_LAYER`** : la capture console `crash-20261123-014819-eden_log.txt` contient 65 occurrences de `Unresolved Fermi2D volume-slice copy`, notamment une rafale à ~117,64 s après les avertissements `surface.cpp format=0`. Nouveau/Mesa `nv50_surface.c` distingue le cas matériel : une destination depth-tiled 3D conserve son adresse de base et sélectionne Z par `DST_LAYER`, tandis qu'une source depth-tiled 3D n'est pas admise dans ce chemin 2D. Vendor `bc94e99cbedd19b3f6bc75aff02a9b5b914d5189` ajoute donc un overload explicite `origin_z` en conservant l'ancienne ABI z=0, et l'utilise uniquement pour une destination block-linear 3D avec `block_depth>0`, `0<layer<depth`, source layer 0 et clip désactivé. Les sources block-linear non-zéro, arrays block-linear 2D et géométries ambiguës restent refusés. Le témoin R3 exact-source valide les tranches non-zéro en pavage NS1 et NS2 ; CI vendor R3/qualité verte. **Le journal ancien ne donne pas les registres de chaque refus : occurrence FC27 du sous-cas corrigé et bénéfice visuel/FPS restent à confirmer sur PS5. Aucun build natif lancé.**

- 24/11 — **FC27 NS1 / vertex-attribute texture handles, index-buffer hotpath** : la chaîne de fidélité des maillots conserve `CollectAttributeHandleRuns` sous `buffer_cache.mutex` + `texture_cache.mutex`, car le chemin PS5 appelle `GPU().OnCPUWrite` avant le `memcpy` invité ; déplacer le scan hors verrou pourrait donc lire des index/attributs en course avec le CPU. Vendor `f337bb8c0484fef5b9a2d763b9775566ff797eef`, rasterizer actif `f79943f596b8a95cdcb05ce74a964a2141ae10ac` : PS5 NS1 précharge au plus 256 octets d'index uniquement si toute la plage est déjà mappée, puis décode les index échantillonnés depuis ce scratch sous le même verrou. Canaux NS2 authentifiés et plages non entièrement mappées conservent les lectures unitaires historiques. Modèle d'équivalence hôte O0/O2 UBSan sur index 8/16/32 bits ; cas synthétique 4 096 index 32 bits : 1 365 lectures bloc théoriques → 64 (63 préchargements + 1 lecture unitaire conservatrice pour le triangle partiel final). Les CI vendor qualité, page-protection synchrone et course CPU-write/readback sont vertes sur ce SHA ; les workflows dédiés R23/MSAA ne sont pas des triggers push-main. **Aucun gain FPS, aucune fidélité maillot console ni build PS5 revendiqués.**

- 24/11 — **Qualification exacte du batch d'index** : vendor `da339b1393d1386bc6af667d243e97860a40d096` est un successeur test-only de `f337bb8c` ; runtime C++ identique. Le harness R23 compile désormais le scratch natif (`u8`) et exerce aussi les index 8/16/32 bits, le repli non mappé et le chemin NS2 inchangé. L'oracle 4 096 index est corrigé à **64** lectures bloc. Aucun gain console supplémentaire revendiqué.

- 25/11 — **MaxwellDMA 3D GOB, lecture/écriture par tranche Z (runtime actif)** : les deux fallbacks logiciels `CopyPitchToBlockLinear` et `CopyBlockLinearToPitch` utilisent désormais l'overload `origin_z` déjà qualifié du décodeur GOB pour les volumes depth-tiled (`block_depth > 0`, `depth > 1`, `layer < depth`), y compris pour les alias GPU/CPU. Les tableaux 2D block-linear et largeurs GOB non prises en charge restent refusés. Le contrôle de borne logicielle conserve 64 Mio, la taille est calculée sur le volume complet, et les lignes écrites ne peuvent franchir la dernière tranche Z. Vendor `94d352bdc9b2ee8e6ea0881d85f4673585b98bf4`, source `maxwell_dma.cpp` blob `a2979cc01cdd7679e71af373d187d08302355b9b`, contrat actif `tests/ns2_native_tiling_activation_source.py` blob `d887e9d21d5a2bc6427948f7075a340e651a4344`. Tests hôtes décodeur R3, qualité et dépendances vendor verts ; build natif PS5 non déclenché. Les anciens 129 refus `Unsupported destination block-linear DMA geometry` dans la capture FC27 ne donnent pas les registres des surfaces : ne **pas** les déclarer réparés avant comparaison console même scène/réglages/cache et couple exact de SHAs.

- 25/11 — **MaxwellDMA 3D GOB : troisième voie complète (block-linear → block-linear)**. Le lot vendor `be9e46213070e5cb57a7dbd8a184ffb480106b4f` étend le même contrôle de tranche Z aux deux surfaces. Le volume source et le volume destination ont chacun leur profondeur et leur offset Z explicitement bornés avant calcul des tailles GOB ; les copies passent par le scratch linéaire borné avant écriture destination. Les arrays 2D sans vrai depth tiling, le bloc GOB largeur non nulle et les régions non mappées restent refusés. Source C++ active : blob `3eb6d0462cde2cdcef613b2bf89d74574c18ea01` ; témoin sélectionné `e66f3161c735a15eb5dac0c97afa1e741802cda9`. Les contrôles vendor R3/qualité/dépendances sont verts sur ce commit. **Pas de build ni de test console PS5** ; aucun statut de texture/maillot ou FPS « résolu » revendiqué.

- 25/11 — **MaxwellDMA B0B5 : volumes 3D avec remappage de composantes**. Le vendor `096761112103fac069b56a22c77f07492001e26e` ajoute la tranche Z explicite au chemin actif `CopyBlockLinearRemap()` : lecture source, lecture destination si `NO_WRITE` et écriture swizzle finale utilisent le même décodeur GOB déjà validé. L'intégralité des GOBs source/destination est prévalidée et bornée à **16 Mio**, avec capture de toutes les données avant la première écriture pour préserver les alias et toutes les couches non sélectionnées. Arrays 2D non depth-tiled toujours refusés. Source runtime `d083d3298b3fb11373d7a7fc164a42ba92bdb2b5`, témoin `b802bbaaa6bf98e4dc55cc5ec7c2c3581b13a117`. Contrôles vendor R3 et qualité verts ; tests hôtes du moteur et comparaison console restent distincts, aucun build PS5 lancé.

### 2026-11-26 — R457 : GPU worker 211 avant import NVDRV

Console moteur fe31b789b382 : MKW 0400C3F00006E000, Bananza 040074A01BF12000 et Pokopia 0400A3A01EE4C000 : GSV 434, worker 101 succès, puis 211 0xFA01, zéro soumission. L'ordre exact des ioctl NVDRV n'est pas tracé : hypothèse pré-import solide, non confirmée sur console. Lichii nx2 enregistre les mappings avant la création de l'AS puis les rejoue. Vendor 5e44c12abda7 : staging par VM enregistrée, replay GMMU avant publication, contrôle chevauchements/ownership, annulation/rollback. Vendor sélectionné a383ab6f52da989c2c5cd756e62165f0763e8e72. Test hôte source-extrait en qualification ; aucun build ni test PS5 du correctif. FC27 : HUD retardé malgré les entrées Options livrées ; 31 frames >100 ms sur le dernier log, aucun nouveau correctif HUD dans ce lot. Crash fermeture : correctif précédent d16f50dc4da4, non validé console.

- 26/11 — **PS5 GPU FIFO saturation / blocage CPU–GPU, runtime actif** : le worker PS5 `gpu_thread_quiet.cpp` utilise une SPSC 256. Un producteur attendait une case libre en détenant `write_lock`; la notification d’une commande bloquante terminée demandait ce même mutex, empêchant le prochain retrait FIFO. Vendor `aece4f82a123a7bd1f4046237a82a0faecbee450` : `completion_lock` séparé et libération de `write_lock` avant l’attente de fence, sans changer capacité, ordre des commandes ou publication release/acquire. Sources natives : quiet `e8279342f4a50a4f2eaa53355f1ed29a62bf5f9a`, header `ec56a3b284d628852342635ada045a907758c310` ; test de file saturée branché dans `check-native-gpu-queue-stop-fastpath-host.py`. Pas de build PS5 ni preuve que ce cas explique le HUD FC27, le chargement Z-A ou le premier draw NS2.


26/11 — **PS5 : retraite effective des fences forcées et dépendances GPFIFO explicites NS2**. `headless/vulkan.cmake` sélectionne `headless/fence_manager_ps5.h`, qui passait `WaitPendingFences(true)` par la politique ordinaire Fast/Immediate et pouvait exécuter son callback sans attendre le tick Vulkan réel, y compris avec une fence stub. Le chemin forcé demande désormais une fence réelle et retarde son callback indépendamment des réglages ; les fences ordinaires gardent la politique existante. Vendor `ca3fddeadc37eb1df96d00e5e1506299bef83d82` : le `dma_pusher.cpp` actif utilise ce drain uniquement pour les dépendances inter-listes explicites des channels NS2 authentifiés, au lieu d'un callback potentiellement immédiat. Le chemin NS1 des fences ordinaires n'est pas modifié. Référence backend `vk_fence_manager_cost.cpp::InnerFence::Queue/Wait` (flush puis tick). Les tests existants vérifient le contrat forcé et le réveil sur échec ; résultats CI/console non confirmés. Correction de cohérence, pas de gain de FPS ni de première frame revendiqués. Aucun build PS5 déclenché.


26/11 — **FC27/NS2 : readback synchrone multi-buffer borné par propriétaire**. Lichii nx2 `src/video_core/buffer_cache/buffer_cache.h::DownloadMemory` intersecte la requête avec chaque allocation. Le propriétaire actif Encore transmettait toute la plage à chaque buffer alors que le MemoryTracker et les intervalles GPU sont partagés. Le premier pouvait donc soustraire les plages des suivants et calculer un offset hors allocation. Vendor `f104b06916cf231504ff7f4919cd4a491e526668`, blob `0ecca19b38d4d40ce03e4f9392c5b6ef042e1e86` : intersection avant toute opération destructive, validation des 16 Gio de table physique, pas de modification de la protection CPU-write/readback ni des barrières. Modèle local avec le corps C++ corrigé : Clang/GCC O0/O2, UBSan, 8 514 géométries par exécution et cas limites, 4/4 PASS ; test source-extrait ajouté à la suite existante. CMake sélectionne le header actif ; pas de preuve que le sous-cas soit effectivement rencontré par FC27, aucun gain FPS/HUD revendiqué. CI et build PS5 non confirmés, aucun build déclenché.


26/11 — **FC27 / GC BufferCache : regroupement des readbacks synchrones natifs**. Lichii nx2 `src/video_core/buffer_cache/buffer_cache.h::RunGarbageCollector/DownloadBuffersMemory` groupe les buffers évincés derrière un seul Finish, alors que le propriétaire actif Encore faisait un Finish pour chaque buffer dirty. Vendor `105187759ed6b9d4ef1254d999fe4ca7263ad664` (blob `4577de4f63bc0393a1e14e89534d6f8aedf50d67`) : regroupement Vulkan PS5 par lot de 16 Mio de staging et 4 096 régions, paquets de 8 copies au maximum par même propriétaire ; seuils et limites LRU 32/64 inchangés. Planification sans effacer le suivi GPU, publication après Finish et protection des écritures CPU échantillonnée après l'attente. Un bad_alloc de staging conserve les buffers du lot ; l'échec de retraite est propagé. Un lot hors budget conserve le chemin individuel historique, dont les limites préexistantes ne sont pas corrigées. Desktop inchangé. Modèle local avec le corps C++ corrigé, caches et runtime simulés, Clang/GCC × O0/O2 × natif/desktop avec UBSan : 8/8 PASS, incluant 3 buffers sales/1 Finish, 3 buffers propres/0 Finish, allocation refusée et retry, échec GPU, protection CPU, séparation des lots, fallback et budgets LRU. Suite vendor existante étendue avec extraction du propriétaire. Aucun résultat CI, build natif ou gain de frametime console revendiqué ; occurrence exacte des GC dirty dans les pauses FC27 non attestée.


26/11 — **FC27 / première traduction graphique NS1 : participation du thread GPU propriétaire**. Le propriétaire actif `vk_pipeline_cache_cost.cpp` dispose déjà de deux workers de traduction et de snapshots TIC/CBUF immuables, mais déléguait tous les stages puis attendait. Le vendor `a82e561698e07f666be4c85973dc4304c0e37030` (blob `61450e8b8c5e76a59660649ed13941eb50e089cb`) exécute le dernier stage actif sur le thread propriétaire pendant que les précédents sont en file ; mêmes pools séparés, même capture d'exceptions, restauration du TLS de coût, drain RAII et ordre d'émission SPIR-V inchangés. Aucun nouveau worker, aucun changement du chemin NS2 ni du cache disque. Lichii nx2 confirme la stratégie de traduction parallèle, cette participation du propriétaire est une adaptation locale et non un backport exact. Modèle C++ indépendant du runtime compilé Clang/GCC O0/O2 UBSan : 4/4 PASS, 399 combinaisons masques/échecs par configuration, un handoff évité, chaque stage exécuté une fois et TLS restauré. Pas de mesure de durée de compilation réelle, de validation Vulkan ni de gain console revendiqué. CI et build PS5 non confirmés ; aucun build natif déclenché.


26/11 — **FC27 / R08 : séparation des ressources du compositeur et des slots de présentation.** Le propriétaire réellement sélectionné par `headless/vulkan.cmake` est `headless/vulkan_blit_screen_r08.cpp` (et `vulkan_present_manager_ps5.cpp` + `vk_present_manager_r08.h`), non le BlitScreen vendor. Une différence d'étendue d'un seul slot déclenchait `SetWindowAdaptPass`, l'effacement de toutes les couches et la remise à zéro d'image_index. De plus, le format de vue du slot n'était pas mémorisé, donc les slots suivants de même taille pouvaient conserver le format précédent après une transition. Désormais les changements de filtre, format global et nombre d'images seuls reconstruisent le compositeur ; chaque slot est recréé selon sa propre taille et ses formats image/vue, avec publication des formats après création réussie du framebuffer. Lichii nx2 `vk_blit_screen.cpp` vérifie aussi séparément les deux formats. Les réservations synthétiques ignorent un slot de format périmé. La vidange GPU existante est conservée avant destruction et mutualisée avec une éventuelle reconstruction des couches. Le témoin source-extrait existant est étendu aux trois slots, redimensionnement, changement de format et retour stable. Adaptation locale du propriétaire R08 ; pas de preuve d'occurrence exacte en match FC27, ni de gain HUD/FPS. CI et build PS5 non confirmés ; aucun build lancé. Vendor inchangé `a82e561698e07f666be4c85973dc4304c0e37030`.


26/11 — **FC27 / présentation accélérée : compatibilité de format de l’alias le plus récent.** `TryFindFramebufferImageView` des deux propriétaires maintenus (`ns2-astc` et `eden-vulkan/vulkan-cache`) choisissait l’image la plus récente à la même adresse sans vérifier la compatibilité avec le format de vue demandé. Lichii nx2 vérifie `IsViewCompatible` avant création de vue ; Encore conserve les refus de siblings sales/remappés/décodage, la sélection monotone et les égalités de ticks, puis refuse la vue incompatible avec les capacités réelles du runtime. Le repli raw historique est conservé sans promouvoir une image plus ancienne. Vendor `2ad69ee0c3eeff604134072db622f512292d7efa`, blobs `709ee61bc3a620654fa9c66eafa6482aab382d12` et `469092ca2a7348b6382d42823d4561e2e1890498`. Modèle C++ local Clang/GCC O0/O2 UBSan : 768 combinaisons de formats simulés, ordre et capacités par configuration, 4/4 PASS ; témoin source-extrait existant étendu. CMake et génération inspectés statiquement ; compilation native, contenu du fallback GPU/CPU, occurrence FC27 et gain HUD non attestés. Les CI moteur précédentes sont rouges sur des reçus historiques BufferCache et qualification du pin, non corrigés par ce lot. Aucun build PS5 déclenché.


26/11 — **FC27 / R24 : lecture cohérente du framebuffer brut.** Le compositeur actif `headless/vulkan_present_layer_r24.cpp` (sélection CMake native) lisait le pointeur de la première page sans readback des caches GPU et supposait contiguë toute la plage tuilée. Sur PS5, la voie raw vérifie maintenant `GetSpan`, utilise `RasterizerVulkan::FlushRegion` avant lecture de la plage contiguë, puis revalide le span. Le chemin fragmenté utilise `DeviceMemoryManager::ReadBlock`, qui appelle le même flush et parcourt les mappings réels ; les octets de pages absentes sont mis à zéro selon le contrat existant. Aucun scratch pleine image sur la voie contiguë, aucune modification des vues accélérées, des barrières d'upload, ni de la politique de format. Le cas première page absente conserve l'effacement existant. Lichii nx2 `present/layer.cpp` conserve une lecture directe similaire ; adaptation locale fondée sur les primitives natives Encore, non un backport. Modèle C++ local Clang/GCC O0/O2 UBSan : 4/4 PASS, 2 048 cas par configuration (bytes CPU/GPU, contiguïté, remap, page initiale absente). Le témoin F07 existant extrait le nouveau fragment ; CI, native et occurrence FC27 non attestées. Le repli peut attendre une vraie retraite GPU si pixels sales et allouer un scratch si fragmenté ; aucun gain FPS revendiqué. Vendor inchangé `2ad69ee0c3eeff604134072db622f512292d7efa`. Aucun build PS5 déclenché.


26/11 — **FC27 / texture alias : restauration du correctif de publication dans le propriétaire réellement sélectionné.** Le reçu `PS5_F07_ALIAS_COPY_COMMIT_ROLLBACK_2026-11-01.md` et le header shadow Vulkan prouvent que la publication du tick devait suivre les appels de copie. `headless/CMakeLists.txt` ajoute `ns2-astc/include` en BEFORE après `vulkan.cmake` ; le header effectif conservait pourtant la publication anticipée. Vendor `9fe18cf26cb08cea8bf0fad3eddac96e4a7fb2f3`, blob `bfd98bca9204d06da8a828c9dba6d8eab7bafb63` : déplacement exact de la publication tick/GpuModified après la boucle de copie sous PS5_NATIVE, desktop et ordre de copie inchangés. Lichii nx2 conserve une publication anticipée ; la protection est une restauration du correctif local et non un backport Lichii. Modèle C++ local (copie simulée, corps de décision transcrit) Clang/GCC O0/O2 UBSan : 6 144 scénarios par configuration ; 4 096 scénarios avec exception échouent avant, zéro après ; ordre et retry vérifiés. Le témoin F04 existant compile désormais aussi la méthode du header sélectionné, résultat CI non confirmé. Aucun gain FPS ni correction HUD prouvée console ; la protection ne couvre pas les rejets silencieux ou l’échec GPU post-enregistrement. Aucun build natif déclenché.


26/11 — **FC27/NS2 : restauration de la transaction de readback et des bornes d’upload dans le TextureCache sélectionné.** La sélection native CMake est `ns2-astc/include`, `IMPLEMENTS_ASYNC_DOWNLOADS=true` dans son `vk_texture_cache.h`. Les quatre méthodes `DownloadImageIntoBuffer`, `CommitAsyncFlushes`, `PopAsyncFlushes`, `UploadImageContents` conservaient les anciens chemins malgré les protections du shadow Vulkan déjà revues. Vendor `b1d53873f6db36ad410dc1cbbf0f541cf2d3bfc2`, blob `4076fb27d78e6be2893d6a09d3f9d5493e6bab59` : rollback DMA/handle deferred en cas d’échec, publication conjointe des deux files avec garde de débordement, consommation retryable (offsets locaux, conservation des handles et slots jusqu’au succès, libération d’un batch vide), lecture accélérée bornée à `MapSizeBytes(image)` et non à la capacité arrondie du staging. La projection desktop des quatre méthodes a été comparée exactement au propriétaire précédent ; pas de changement de comportement desktop ni timer importé. Le pool `FreeDeferred` conserve le tick GPU courant avant réutilisation. Lichii nx2 a une logique de niveaux/mips différente ; pas de backport aveugle. Les trois témoins F07 de readback visent maintenant le propriétaire sélectionné ; le témoin d’upload contrôle la parité et une capacité supérieure au payload. Modèle local de lecture (branche C++ reproduite, mémoire/staging simulés), Clang/GCC O0/O2 UBSan, native et desktop : 8/8 exécutions, 1 024 tailles chacune ; la branche native ne lit jamais le tail. Les tests complets des transactions et la compilation native restent à qualifier par CI ; aucune mesure PS5 ni gain FPS revendiqué. Aucun build natif lancé manuellement.


26/11 — **FC27/NS2 : GC du TextureCache sélectionné, readback invalide et comptabilité mémoire.** Le propriétaire effectif `ns2-astc/include` conservait un GC non protégé : allocation de staging nulle/courte ou régions de copie vides avant éviction, soustraction non saturante d’une estimation locale à une utilisation mémoire rééchantillonnée par le pilote, et âge soustrait avant seuil. Vendor `3096bafc0e95ddb7bce3a82a7ecbd9cdff29c970`, blob `85c2514267ca38fc0b88d1442a464cc0299aa2d8`. Protection PS5 : laisser l’image sale résidente si allocation/refus ou régions absentes ; vérifier le mapping avant tout download ; ne parcourir le LRU qu’après l’âge admissible ; saturer les deux débits mémoire (scaled et taille réelle/transcodée) à zéro. Les règles de pression, ordre DownloadMemory → Finish → SwizzleImage → éviction, retirement GPU et comportement desktop sont conservés. Lichii nx2 implémente un writeback asynchrone d’overlaps avec des contrats différents ; pas de transfert aveugle. Test local du corps GC reproduit depuis le blob et modèle LRU/mémoire : Clang/GCC -O0/-O2 UBSan, 8/8 exécutions, 3 088 cas par configuration native et 100 par desktop, soit 12 752 cas cumulés ; arithmétique saturante comprise. Témoin F07 existant étendu au propriétaire sélectionné. Ni driver réel, ni baisse FPS/frametime, ni NS2 boot validés. Le batching dirty GC, les BadOverlap et le coût de TickFrame restent distincts. Aucun build natif déclenché manuellement.


26/11 — **FC27/NS2 : regroupement borné des readbacks dirty GC du propriétaire sélectionné.** Vendor `618e2ed9d8428270b6d67e65061bf01e84fbfe36`, blob `ab226987e5e20829d156c8edb917fd4851cf478d`. Le propriétaire natif `ns2-astc/include` appelait Finish pour chaque image sale évincée. Adaptation du mécanisme déjà présent dans le cache Vulkan maintenu : prélecture d'un préfixe LRU de candidats indépendants (hors overlap, alias, sparse, remap, MSAA, rescale, régions vides), au plus 40 handles et 32 Mio de capacités arrondies ET de mappings réels. Le budget de visites et la projection saturante de pression bornent l'admission ; la publication guest et les évictions restent dans le Cleanup original et son ordre. Un lot de moins de deux candidats garde le repli individuel. Les réservations différées restent détenues jusqu'au readback et à l'écriture guest ; en cas d'exception, drainage avant libération, sinon conservation des réservations si la retraite GPU est indémontrable. Local : corps GC reproduit du blob + modèle C++ LRU/staging/driver, Clang/GCC O0/O2 UBSan natif et desktop, 8/8 configurations PASS (881 scénarios natifs et 249 desktop par configuration, 4 520 cumulés). Vingt images indépendantes éligibles : 1 Finish au lieu de 20 dans le modèle. OOM, mapping court, échec de commande/drainage, alias, chevauchement, seuil et plafond vérifiés. Témoin F07 existant adapté au nouveau repli et aux gardes. Pas de validation RADV/PS5, ni de mesure de latence FC27 ; le repli individuel reste nécessaire pour les candidats exclus. Aucun build PS5 déclenché.


26/11 — **FC27/NS2 : recherche de texture en un parcours et admission du readback GPU ordinaire.** Vendor `135400e67678dfd54f6a227ed26b86988d283e4f`, blob `014b8a25cf34391965f7f465c372e7673596e86b`. Le header effectivement sélectionné `ns2-astc/include` réutilise désormais les corps déjà revus du shadow Vulkan pour FindImage (sélection du premier tick maximal sans vector ni seconde lecture des slots ; early exit conservé) et PrepareDmaImage (suppression d'un second Touch LRU, déjà réalisé par PrepareImage). FindDMAImage conserve sa logique actuelle : le parcours effectif s'arrête au premier match et une modification de cette priorité ne serait pas une simple optimisation. Le DownloadMemory natif Vulkan refuse les readbacks sans région, de taille nulle ou avec handle/mapping invalide avant Record ; une réservation courte mais valide est rendue au pool avant exception, et les gardes existantes restaurent les flags GPU-dirty et drainent les commandes déjà enregistrées. Le chemin desktop des recherches reste identique. Tests locaux effectivement exécutés : corps FindImage et fragment d'admission copiés dans un modèle hôte, Clang/GCC O0/O2 UBSan avec/sans PS5_NATIVE, 8/8 exécutions, 2048 recherches et 96 admissions chacune (17152 cas cumulés). Témoin F07 FindImage redirigé sur le header sélectionné ; témoin batch existant étendu aux rejets et à la retraite (CI non encore exécutée). Le hash X8D24 oublié au lot GC précédent est également réconcilié sans retirer les assertions. BadOverlap : Lichii nx2 possède un suivi des plages écrites, ticks et writebacks différés absent de ce propriétaire ; aucun writeback aveugle ni pin permanent introduit. Ce risque reste ouvert. Les readbacks invalides remontent une exception, pas une récupération transparente du device. Pas de compilation PS5 ni preuve FPS/HUD/boot console.


26/11 — **FC27/NS2 : réconciliation du chemin draw, attachments clairsemés et feedback.** Vendor `ac6cd16bcb3caa2e88b86917d90fb9323e197e0a`, blob `655dcfc936c0157a5e5910942d44d1f21ff028d7`. Les méthodes `UpdateRenderTargets` et `CheckFeedbackLoop` du propriétaire natif `ns2-astc/include` sont désormais identiques aux méthodes déjà revues du shadow Vulkan. Sur un draw sans reselection, seules les vues présentes du masque sont préparées, ordre couleur puis profondeur conservé ; aucun saut du refresh des vues actives, ni modification du chemin dirty/full clear. Les comparaisons des vues et images couleur en feedback parcourent seulement les bits actifs et s'arrêtent au premier match. La décision de barrière, les serials et le cache des IDs restent inchangés. Projection desktop comparée octet pour octet aux deux méthodes précédentes, reverse exact du blob. Lichii nx2 utilise encore le parcours complet et une autre politique de barrière liée aux écritures profondeur ; pas de backport de cette politique. Test local réellement exécuté dans un modèle C++ transcrit des boucles, Clang/GCC O0/O2 UBSan -Wall -Wextra -Werror : 4/4 exécutions, 1024 cas de refresh et 98304 comparaisons feedback par exécution (397312 cas cumulés). Les deux témoins F07 existants extraient maintenant le propriétaire actif et vérifient la parité shadow ; CI non confirmée. Les anciens échecs Fast Gate (BufferCache DMA blob 4577de4f63bc0393a1e14e89534d6f8aedf50d67), SSBO, R457 et graphe final sont localisés aux assertions de provenance ; aucune qualification des étapes masquées par ces assertions. TickFrame natif dispose déjà d'un échantillon externe hors mutex, donc pas de reprise du throttling shadow sans analyser l'appelant. Aucun build PS5 ni résultat FPS/console.


26/11 — **FC27/NS2 : budget de parcours du GC TextureCache natif séparé du budget d'éviction.** Vendor `806252e96253489c18d11551bf2dcfd668502719`, blob `c0312be09d81afb0064479179db794d2648560b9`. Le propriétaire sélectionné `ns2-astc/include` facturait chaque visite à son plafond de 10/20/40, même quand les images étaient en décodage ou protégées par la politique de pression. Le shadow Vulkan possède déjà un budget distinct ; adaptation locale du Cleanup et du prefetch conservateur actif : visites bornées à 8192 par parcours, tentative facturée seulement après les exclusions (les readbacks invalides consomment toujours une tentative), reset à chaque passe, ordre LRU, seuils et retraite GPU inchangés. La voie desktop conserve le comptage de chaque visite. Modèle local C++ transcrit des décisions de Cleanup, GCC/Clang O0/O2 UBSan, natif/desktop, 8/8 exécutions après correction d'un avertissement de variable inutilisée dans le modèle desktop : 4608 cas générés par configuration, 36864 cumulés hors cas limites. Exemple 180 textures protégées puis 24 évictables : 0 vs 10 évictions en 10 vs 190 visites dans le modèle. Le prefetch n'a pas été compilé localement : témoins source et modèle Python ajoutés au test existant, CI à qualifier. Le plafond de visites peut augmenter le temps d'un parcours très défavorable ; aucun gain FPS ni démarrage NS2 attesté. TickFrame conserve l'échantillon commun hors mutex vérifié dans `encore-active/eden-vulkan/vulkan_rasterizer.cpp`. Les gates de provenance moteur restent rouges ; aucun build PS5 déclenché.


26/11 — **Qualification bloquée : reprise des reçus BufferCache et SSBO/R457, sans modification C++ ni repin.** Vendor `806252e96253489c18d11551bf2dcfd668502719`, arbre `dcf463b5cd23ca8fa4c7899c5efd8c8f75f5b869`. Les contrôles SSBO/R457 admettaient f104b069, 10518775 et a82e5616 sans entrée d'arbre correspondante ; les quatre arbres exacts (dont le pin actuel) sont renseignés, 26 clés d'admission = 26 clés d'arbre. Comparaison GitHub a82e5616→806252e9 : 8 commits, 4 fichiers modifiés, exclusivement les deux headers TextureCache et deux témoins. Les sources GPU worker, identité NVDRV, PTE/sparse, shader et allocation conservent leurs empreintes exactes ; les trois témoins shader ont évolué dans a82e5616 (réversion de la traduction du dernier stage sur copie historique) et leurs nouvelles empreintes sont contrôlées uniquement pour cette révision et le pin actuel. Fast Gate : réversion des corps RunGarbageCollector et DownloadMemory uniquement sur la copie d'audit, égalité intégrale vérifiée contre les blobs `0ecca19b38d4d40ce03e4f9392c5b6ef042e1e86` puis `24323ea00c4088d45d5357a6df5382a7447669ab` ; aucune modification des owners runtime. Les assertions historiques restent en place. Vérification locale limitée aux comparaisons de sources et d'arbres par API, pas d'exécution complète des scripts ni de compilation native. Le graphe final global reste à réconcilier ; les étapes postérieures aux assertions initiales peuvent révéler d'autres écarts. Aucun gain de jouabilité ni nouveau test console déclaré.
