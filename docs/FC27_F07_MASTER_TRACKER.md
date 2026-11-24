# Eden Encore — suivi maître F07 et exploitation PS5

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
