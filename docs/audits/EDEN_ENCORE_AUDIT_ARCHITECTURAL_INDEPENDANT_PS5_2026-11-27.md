# Eden Encore — Audit architectural indépendant PS5 / PS5 Pro

**Date : 27 novembre 2026**  
**Nature : revue statique indépendante des principaux chemins de production ; analyse uniquement.**  
**Périmètre : NS1 + NS2, PS5 standard comme cible minimale, PS5 Pro comme cible complémentaire.**

## 1. Méthode et limites

L'objectif est d'évaluer les choix techniques d'Encore au regard des contraintes réelles du matériel hôte et des recommandations publiques des fabricants et organismes de normalisation. Une implémentation existante, une sélection CMake, un test hôte et une qualification sur console constituent quatre niveaux de preuve distincts. Aucun compteur documentaire ne démontre à lui seul la correction ou les performances.

Instantanés examinés :
- Moteur : [fc042affb26e2a67dddf0ff52f022f1f9486d835](https://github.com/niakw/ProsperoEden-Encore/commit/fc042affb26e2a67dddf0ff52f022f1f9486d835).
- Vendor : [ea1d6736b9e83b5d037a7ecb36140ae4378f90b2](https://github.com/niakw/Prospero.Eden-Encore-vendor/commit/ea1d6736b9e83b5d037a7ecb36140ae4378f90b2).

Le gitlink exact reliant ces deux instantanés n'a pas pu être confirmé lors de cette revue. Les conclusions croisées moteur/vendor restent donc conditionnelles à la vérification de cette provenance. Aucun SDK propriétaire Sony n'a été examiné ; il ne s'agit pas d'une certification officielle PS5. Aucun nouveau test console, build, merge ou correctif runtime n'a été réalisé. Les sources listées ci-dessous ont été examinées par sections pertinentes, non dans leur intégralité. Les chiffres de gains potentiels ne sont pas des mesures.

Convention : **présent** = preuve dans le code examiné ; **sélectionné** = preuve de sélection de compilation ; **partiel** = mécanisme présent mais non généralisé ou non qualifié ; **non vérifié** = preuve insuffisante, et non preuve d'absence. La qualification matérielle reste séparée.

## 2. Référentiel matériel et priorités

| Ressource | PS5 standard | Conséquence architecturale |
|---|---|---|
| CPU | AMD Zen 2, 8 cœurs/16 threads, jusqu'à 3,5 GHz | Localité des caches, affinité vérifiée, contention SMT et coût du JIT |
| GPU | AMD RDNA 2, 10,3 TFLOPS théoriques | Optimisation RADV, dépendances fines, occupation et bande passante |
| RAM | 16 Go GDDR6 unifiée au total | Ne pas assimiler mémoire physique totale et budget accessible au processus |
| Bande passante | 448 Go/s théoriques | Réduire copies, transferts redondants et pression des textures |

La PS5 Pro doit être mesurée séparément ; ne pas supposer que sa capacité GPU supplémentaire résout les limitations CPU, mémoire ou fonctionnelles. Les guides AMD sont prioritaires pour optimiser le GPU **hôte**. Les documents NVIDIA Maxwell/Ampere sont utiles pour la sémantique du GPU **invité** ; leurs recommandations d'optimisation matérielle ne se transposent pas automatiquement à RDNA.

## 3. Sources de preuve (instantanés immuables)

| ID | Source | Zone pertinente |
|---|---|---|
| E01 | [CMake](https://github.com/niakw/ProsperoEden-Encore/blob/fc042affb26e2a67dddf0ff52f022f1f9486d835/headless/CMakeLists.txt) | 282–296 : compilation Zen 2 ; 400–446 : sparse invité ; 491–495 et sélection A64 : JIT ; 2763–2865 : ASTC ; 4547–4549 : RADV |
| E02 | [Packaging](https://github.com/niakw/ProsperoEden-Encore/blob/fc042affb26e2a67dddf0ff52f022f1f9486d835/tools/build-package.sh) | 14 : EDEN_PS5_VULKAN=ON, EDEN_VULKAN_DRIVER=RADV |
| E03 | [JIT allocator](https://github.com/niakw/ProsperoEden-Encore/blob/fc042affb26e2a67dddf0ff52f022f1f9486d835/headless/jit-allocator.h) | Alias RX/RW, granularité, génération de cache |
| E04 | [Memory pages](https://github.com/niakw/ProsperoEden-Encore/blob/fc042affb26e2a67dddf0ff52f022f1f9486d835/src/memory_pages.cpp) | Allocation directe, vérification des alias, engagement et restitution |
| E05 | [Politique mémoire JIT](https://github.com/niakw/ProsperoEden-Encore/blob/fc042affb26e2a67dddf0ff52f022f1f9486d835/headless/jit_memory_policy.h) | Budgets, limites par arène, réserve hôte |
| E06 | [Démarrage](https://github.com/niakw/ProsperoEden-Encore/blob/fc042affb26e2a67dddf0ff52f022f1f9486d835/headless/main.cpp#L1061-L1114) | Choix du plan sparse, préflight des alias |
| E07 | [Sparse invité](https://github.com/niakw/ProsperoEden-Encore/blob/fc042affb26e2a67dddf0ff52f022f1f9486d835/src/ns2_sparse_guest.cpp#L139-L240) | ZERO/OWN, allocation, admission, rollback |
| E08 | [Host memory](https://github.com/niakw/ProsperoEden-Encore/blob/fc042affb26e2a67dddf0ff52f022f1f9486d835/src/host_memory.cpp) | Fastmem, réservations, sondes d'accès |
| E09 | [Performance/topologie](https://github.com/niakw/ProsperoEden-Encore/blob/fc042affb26e2a67dddf0ff52f022f1f9486d835/headless/performance.cpp#L202-L350) | CPUID, masques CPU, sondes SMT |
| E10 | [Topologie PS5](https://github.com/niakw/ProsperoEden-Encore/blob/fc042affb26e2a67dddf0ff52f022f1f9486d835/headless/ps5_cpu_topology.h) | Analyse des groupes SMT |
| E11 | [Compositeur R08](https://github.com/niakw/ProsperoEden-Encore/blob/fc042affb26e2a67dddf0ff52f022f1f9486d835/headless/vulkan_renderer_r08.cpp) | Présentation, retrait des ressources, options de génération d'images |
| E12 | [Contrat de provenance des sources](https://github.com/niakw/ProsperoEden-Encore/blob/fc042affb26e2a67dddf0ff52f022f1f9486d835/tools/check-active-cmake-source-boundary.py) | Gitlink, séparation sources/overrides |
| V01 | [Scheduler Vulkan](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/ea1d6736b9e83b5d037a7ecb36140ae4378f90b2/encore-active/eden-vulkan/vulkan_scheduler.cpp#L565-L706) | Worker central, recording, soumission, barrière upload |
| V02 | [Pipeline cache](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/ea1d6736b9e83b5d037a7ecb36140ae4378f90b2/encore-active/eden-vulkan/vk_pipeline_cache_cost.cpp) | 235 : identité du cache ; 506–617 : workers ; 832–846 : drainage/sérialisation |
| V03 | [TextureCache Vulkan](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/ea1d6736b9e83b5d037a7ecb36140ae4378f90b2/encore-active/eden-vulkan/vk_texture_cache_cost.cpp) | 171–181 : ASTC ; 183–255 : images denses ; 970–1055 : probe sparse ; 2464 : image normale |
| V04 | [Rasterizer Vulkan](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/ea1d6736b9e83b5d037a7ecb36140ae4378f90b2/encore-active/eden-vulkan/vulkan_rasterizer.cpp#L450-L565) | Préflight descripteurs et attentes du scheduler |
| V05 | [GPU Thread](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/ea1d6736b9e83b5d037a7ecb36140ae4378f90b2/encore-active/eden/src/video_core/gpu_thread.cpp) | Traitement des commandes invitées et progression FIFO |
| V06 | [BufferCache](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/ea1d6736b9e83b5d037a7ecb36140ae4378f90b2/encore-active/eden/src/video_core/buffer_cache/buffer_cache.h) | Verrous, invalidation, uploads, multi-range sparse |
| V07 | [BufferCache Vulkan](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/ea1d6736b9e83b5d037a7ecb36140ae4378f90b2/encore-active/eden/src/video_core/renderer_vulkan/vk_buffer_cache.cpp) | Staging, mapping hôte, barrières ciblées |
| V08 | [TextureCache commun](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/ea1d6736b9e83b5d037a7ecb36140ae4378f90b2/encore-active/eden/src/video_core/texture_cache/texture_cache.h) | Verrous, identité des ressources, invalidations |
| V09 | [Present manager](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/ea1d6736b9e83b5d037a7ecb36140ae4378f90b2/encore-active/eden-vulkan/vulkan_present_manager.cpp) | Présentation asynchrone, fences, copies/blits |
| V10 | [Macro JIT](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/ea1d6736b9e83b5d037a7ecb36140ae4378f90b2/encore-active/eden/src/video_core/macro.cpp#L716-L1171) | JIT Xbyak et interpréteur Maxwell |
| V11 | [JIT natif](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/e5a7e2fb5c9b759bad4345a5092e6262448132e5/encore-active/eden/src/dynarmic/src/dynarmic/backend/x64/block_of_code_native.cpp) | Engagement/trim sparse ; instantané antérieur, à reconfirmer au gitlink exact |

## 4. CPU, JIT et compilation

**Constat : spécialisation PS5 réelle.** E01 sélectionne notamment -march=znver2 pour video_core, audio_core et shader_recompiler, -mtune=znver2 pour des composants CPU, ThinLTO pour Dynarmic et video_core et -ffp-contract=off sur certains composants sensibles. Ce ciblage est cohérent avec Zen 2. Il ne prouve pas un optimum global ; PGO et comparaisons de code généré restent à étudier avec des profils représentatifs.

E03–E06 démontrent une architecture JIT à réservation virtuelle stable et engagement physique progressif par blocs de 2 Mio, alias RW/RX, cache d'alias invalidé par génération et restitution de pages. Le préflight natif refuse un contrat d'alias incompatible. Conserver cette fondation. Une granularité de 2 Mio peut aider la couverture TLB mais son bénéfice effectif dépend des mappings ; mesurer fragmentation interne et coût des engagements.

La sélection A64 de production reste a64_interface_standard.cpp (JIT par cœur). Le code de mutualisation historique n'est pas une preuve d'activation. Le sparse répond au gaspillage d'allocation physique ; un cache de blocs partagé répond à la duplication des traductions. Les deux mécanismes sont complémentaires. Une future mutualisation doit préserver les clés de contexte, le modèle d'exclusifs, les invalidations de code automodifiant, la durée de vie des blocs, les permissions et le drainage des workers.

La politique mémoire contient un calcul par jeu et des limites d'arène ; distinguer capacité virtuelle et budget physique. Vérifier la pression réelle en cours de jeu, la mémoire directe disponible, le plus grand bloc libre, les pics concurrents GPU et les évictions. Ne pas déduire une fuite d'une seule mesure de réservation.

## 5. Mémoire invitée et fastmem

E07 montre une page zéro physique partagée, lue sans engagement individuel des régions intactes, avec promotion vers OWN lors d'une écriture et restauration en cas d'échec. E01 sélectionne le propriétaire sparse invité sous conditions. E08 contient des mécanismes de fastmem et des sondes ; la fenêtre A32 explicitement documentée est de 4 Gio, ce qui ne démontre pas une fenêtre équivalente A64.

Architecture à conserver, sous réserve de validation de la cohérence CPU/GPU/DMA, des alias, des permissions, de la transition ZERO→OWN→ZERO et de la libération après achèvement des utilisateurs GPU. La preuve critique est la lecture de données correctes à travers toutes les vues, y compris pendant les remaps, le teardown et les échecs partiels. Une mémoire sparse ne doit jamais devenir un faux succès d'allocation.

## 6. Topologie Zen 2, SMT et CCX

E09/E10 démontrent une interrogation des masques autorisés, CPUID et des informations du scheduler FreeBSD, des sondes d'affinité et une logique de groupes SMT. V02 adapte la taille du pool de compilation au masque disponible et à la réservation de workers prioritaires (jusqu'à six). Deux workers de traduction shader et un worker de sérialisation sont également présents.

Ne pas assimiler un CPU logique à un cœur physique distinct. La localité inter-CCX et la politique optimale de placement ne sont pas démontrées. Mesurer migrations, contention SMT, charge par thread, latence des échanges, travail utile et conséquences sur les frametimes. Ne pas augmenter arbitrairement la priorité ou le nombre de workers.

## 7. Vulkan/RADV et organisation du travail GPU

E02 et E01 établissent la sélection RADV native dans le package PS5. V02 montre la compilation parallèle, la persistance du cache et la validation de son identité. V04 montre un chemin Descriptor Buffer avec contrôle de capacité et fallback conditionné par les capacités. V01/V05/V09 montrent des chemins asynchrones pour le traitement invité, le recording et la présentation.

Le recording Vulkan demeure largement centralisé autour d'un worker principal (V01), même si la compilation des shaders est parallèle. Khronos et AMD recommandent le recording multithread lorsque le coût CPU le justifie. Le nombre de threads optimal dépend des dépendances, du coût des command buffers, des command pools et de la charge du driver. Une future architecture doit distribuer uniquement le travail indépendant, garder l'ordre invité et établir les durées de vie des objets avant soumission. Elle ne doit pas confondre files logicielles et véritables moteurs GPU indépendants.

## 8. Synchronisations et barrières : priorité d'étude

V01, lignes 661–683 : SubmitExecution ajoute une barrière upload avec TRANSFER → ALL_COMMANDS et MEMORY_READ | MEMORY_WRITE. Elle est conservatrice ; son existence ne démontre ni une violation Vulkan ni un coût mesuré. Étudier les dépendances réelles avant de réduire ses masques. V04, lignes 450–565, contient des drains WaitWorker lors des préflights de descripteurs ; plusieurs attentes sont explicitement déplacées hors des verrous de caches. Cette évolution est saine, mais les drains eux-mêmes subsistent.

À mesurer : durée et fréquence des drains, attente des fences, chevauchement upload/rendu, occupation des threads, temps d'exécution GPU, lots soumis et latence de publication. Utiliser des scopes et accès précis quand les dépendances le permettent, conserver les barrières nécessaires aux hazards RAW/WAR/WAW, à la disponibilité/visibilité et à la durée de vie. Synchronization2 et sémaphores timeline sont à qualifier sur le driver exact ; ne pas déclarer une optimisation uniquement en raison de leur présence.

## 9. BufferCache et TextureCache

V06/V07/V08 montrent un cache de buffers évolué (multi-range, staging, sources sparse compatibles, réduction de scans et invalidations) et une gestion explicite des verrous/identités des images. La complexité des relations entre invalidation invitée, données écrites par le GPU et ressources hôtes reste une source de risque.

V03 démontre que le chemin ordinaire de création d'images reste dense (MakeImage), tandis que ProbeSparseImage est conditionné par EDEN_NS2_SPARSE_CACHE_PROBE. Ne pas compter cette sonde comme résidence sparse généralisée dans les jeux. Distinguer clairement sparse JIT, sparse invité, buffers sparse compatibles et sparse images Vulkan.

Étudier une politique hybride dense/sparse : petites images denses, grandes ressources compatibles et réellement partielles comme candidates. Vérifier sparseBinding/sparseResidencyImage2D, exigences de granularité/aspects, mip tails, bind/unbind, synchronisations, budgets et repli correct. Le sparse n'est pas systématiquement plus rapide : il apporte surtout un contrôle de résidence, avec des coûts de gestion propres.

## 10. ASTC et fidélité des formats

V03, lignes 171–181, conditionne le chemin d'accélération GPU examiné à AstcDecodeMode::Gpu, à l'absence de support ASTC optimal du device, à la recompression Uncompressed et à depth==1. E01 montre des chemins de traitement par couches et de limitation du scratch. Cela ne démontre pas un transcode ASTC→BCn généralisé sur GPU.

Empreinte théorique d'une texture 4096 × 4096 sans mipmaps, alignements ni scratch :

| Format | Taille |
|---|---:|
| RGBA8 | 64 Mio |
| BC3 / BC7 | 16 Mio |
| BC1 | 8 Mio |
| ASTC 6×6 | ~7,12 Mio |

Le calcul ASTC utilise l'arrondi au bloc entier (683×683×16 octets). La recompression BCn peut dégrader la fidélité ; préserver alpha, formats sRGB, normales, précision et usages spécifiques. Mesurer VRAM résidente, scratch maximal, coût de transcodage et qualité visuelle. Ne pas généraliser une recompression destructive comme optimisation transparente.

## 11. Shaders, caches et pipelines

V02 : traduction parallèle, pool de compilation des pipelines, cache Vulkan persistant, identité du cache (pipelineCacheUUID) et drainage des workers avant destruction. Le système est déjà avancé. À qualifier : miss/hit sur caches froids et chauds, temps de traduction vs driver, invalidation de cache en cas de changement de driver, exactitude des clés et reproductibilité.

Fossilize, Graphics Pipeline Library, Dynamic Rendering généralisé, extended dynamic state, éventuel recours à des caches de pipeline indépendants et PGO : non vérifiés exhaustivement dans cette revue. Les considérer comme options à comparer, pas comme obligations ni comme absences établies. Fossilize peut faciliter l'enregistrement/rejeu d'objets et le préchauffage ; un cache existant correct peut déjà répondre à une partie de ce besoin.

## 12. MME et sémantique GPU invitée

V10 montre un JIT x86-64 de macros Maxwell utilisant Xbyak, un interpréteur et des optimisations de génération de code. Cela ne prouve pas la couverture MME64 Ampere/NS2. Auditer séparément le décodage, les instructions, les effets sur l'état GPU, les dépendances et les exceptions. Construire des tests différentiels interpréteur/recompilateur, puis profiler les macros chaudes. La fidélité précède l'optimisation.

## 13. Présentation, frame pacing et latence

V09 : présentation asynchrone, files, fences, sémaphores, gestion des images disponibles ; chemins de copie/blit présents. E11 : compositeur natif et mécanismes de génération d'images. Un zero-copy de bout en bout n'est pas démontré ; éliminer uniquement les copies réellement évitables sans violer les layouts, l'ownership, les conversions de format et la durée de vie.

Budgets par image : 30 FPS = 33,33 ms ; 60 FPS = 16,67 ms ; 120 FPS = 8,33 ms. Distinguer images invitées nouvelles, images présentées, interpolation et répétitions. Pour FC27, viser d'abord un 30 FPS réel et stable avec HUD et pause réactifs. Mesurer la chaîne HID → invité → production du draw → soumission → affichage, les frametimes p50/p95/p99/p99.9, les frames >50/100 ms et les délais de mise à jour du HUD. La génération d'images ne doit jamais masquer un défaut fonctionnel ou de cadence.

## 14. Matrice de maturité

| Domaine | Appréciation statique | Réserve principale |
|---|---|---|
| Ciblage natif PS5 / Zen 2 | Solide | Mesures PGO et console |
| JIT sparse | Solide | Fragmentation, pression réelle, invalidations |
| Sparse invité NS2 | Prometteur | Cohérence CPU/GPU/DMA et qualification |
| Topologie / SMT | Avancée | CCX et placement mesuré |
| JIT partagé | Non sélectionné dans la production examinée | Stabilité et identité des blocs |
| RADV | Sélectionné | Capacités et comportement réels du driver |
| Compilation shaders | Avancée | Latences et caches froids/chauds |
| Descriptor Buffer | Présent sous conditions | Usage effectif et drains |
| Recording GPU multithread | Limité dans les chemins inspectés | Dépendances et coût CPU |
| Barrières | Conservatrices sur certains chemins | Scopes et causalité mesurée |
| BufferCache / TextureCache | Avancés, complexes | Contention et cohérence |
| Sparse textures | Non généralisées | Résidence réelle et synchronisation |
| ASTC GPU | Partiel | Transcodage et fidélité |
| MME64 | Non qualifié exhaustivement | Parité fonctionnelle |
| Présentation | Asynchrone, perfectible | Copies et latence |
| Qualification NS2 | Non acquise sur les derniers retours disponibles | Démarrage et gameplay |
| Performances FC27 | Non acquises sur les derniers retours disponibles | Stabilité, HUD, pause, sortie |

Les appréciations sont qualitatives ; aucun score global ou pourcentage d'optimalité n'est calculé.

## 15. Ordre des études après stabilisation

Terminer d'abord les blocages NS2, les défauts FC27 et la fermeture propre. Pas de refonte parallèle du runtime pendant cette phase. Les priorités suivantes sont des hypothèses d'impact, non des résultats. Elles sont conditionnelles, non obligatoires (voir la règle d'arrêt de la section 19) :

| ID | Chantier | Impact potentiel | Critère de décision |
|---|---|---|---|
| A01 | Barrières et drains GPU | Très élevé | Profil causal démontré ; synchronisations correctes et p99 amélioré |
| A02 | Recording Vulkan parallèle | Très élevé si CPU-limité | Coût recording mesuré, dépendances préservées, gain reproductible |
| A03 | JIT sparse mutualisé | Élevé | Réduction mesurée des blocs dupliqués et de la RAM, aucune régression |
| A04 | TextureCache hybride dense/sparse | Élevé sous pression mémoire | Baisse de résidence et absence de défaut d'image |
| A05 | ASTC→BCn accéléré | Élevé sous pression textures | Gain mémoire/temps à qualité acceptable |
| A06 | MME64 spécialisé | À mesurer | Couverture différentielle puis coût des macros |
| A07 | Présentation zero-copy | À mesurer | Réduction des copies et de la latence réelles |
| A08 | CCX, PGO, options pipeline | À mesurer | Profil représentatif et comparaison à configuration identique |

Garder un chemin de production unique ; ne pas réintroduire de profils expérimentaux livrés. Respecter la séparation vendor/sources (dépendances figées) et vendor/encore-active (overrides maintenus), ainsi que le gitlink exact. Les correctifs futurs devront conserver les contrats et les fallbacks nécessaires ; un stub ne doit pas être supprimé simplement pour améliorer un compteur.

## 16. Protocole de qualification recommandé

1. Identifier moteur, gitlink vendor, driver, firmware, PS5 standard/Pro, configuration, cache froid/chaud et titre/version.
2. Vérifier la sélection de chaque propriétaire C++ et le graphe exact de compilation ; ne pas confondre un fichier présent et un fichier compilé.
3. Établir une référence fonctionnelle et mesurable : premier frame, gameplay, sauvegarde/reprise, menus/HUD, fermeture propre ; comparer plusieurs titres NS1/NS2.
4. Collecter CPU par thread, temps JIT, cache hits/misses, blocs dupliqués, pages réservées/engagées, budget physique, mémoire GPU, scratch, évictions, temps GPU, waits, drains, uploads, bytes copiés, frametimes et latence input.
5. Comparer des parcours reproductibles à résolution, scènes, version et réglages identiques ; répéter et publier dispersion et percentiles, non uniquement FPS moyen.
6. Valider les contrats (tests différentiels et hôtes), les capacités Vulkan réellement exposées et les résultats console. Préserver la fidélité et la compatibilité avant d'accepter un gain.
7. N'accepter un changement architectural que si la mesure établit son utilité et l'absence de régression pertinente.

## 17. Références publiques

- Sony : [spécifications PS5](https://sonyinteractive.com/en/press-releases/playstation-5-launches-this-november-at-399-for-ps5-digital-edition--and-499-for-ps5-with-ultra-hd-blu-ray-disc-drive/).
- AMD GPUOpen : [RDNA Performance Guide](https://gpuopen.com/learn/rdna-performance-guide/).
- AMD : Software Optimization Guide for AMD Family 17h Processors, publication 56305 (vérifier la révision applicable).
- Khronos : [Command buffer usage et multithreading](https://docs.vulkan.org/samples/latest/samples/performance/command_buffer_usage/README.html).
- Khronos : [Sparse resources](https://docs.vulkan.org/guide/latest/sparse_resources.html).
- Khronos : [Synchronization examples](https://docs.vulkan.org/guide/latest/synchronization_examples.html).
- Khronos : [Descriptor Buffer](https://www.khronos.org/blog/vk-ext-descriptor-buffer).
- Khronos : [Pipeline cache](https://docs.vulkan.org/samples/latest/samples/performance/pipeline_cache/README.html).
- Khronos : [Graphics pipeline library](https://docs.vulkan.org/samples/latest/samples/extensions/graphics_pipeline_library/README.html).
- NVIDIA : [Vulkan Dos and Don'ts](https://developer.nvidia.com/blog/vulkan-dos-donts/) (distinguer principes généraux et spécificités matérielles).
- Valve : [Fossilize](https://github.com/ValveSoftware/Fossilize).

Ces références constituent le référentiel public de travail ; elles ne certifient pas le comportement du driver PS5 adapté ni l'optimalité de chaque choix.

## 18. Conclusion et reste de l'audit

Encore est une architecture réellement spécialisée PS5 : sparse JIT, mémoire invitée à résidence progressive, politique de topologie, RADV, compilation parallèle et mécanismes de caches/synchronisation natifs. La fondation sparse doit être conservée. Les marges principales portent sur la coordination CPU/GPU, les dépendances et les copies, la mutualisation du JIT et la résidence des images.

La complexité accumulée et l'écart entre couverture du code et résultats fonctionnels constituent un risque plus concret que l'absence d'une technologie à la mode. Aucune supériorité absolue ni conformité officielle Sony ne peut être déduite de cette revue.

Restent explicitement hors couverture exhaustive : kernel/SVC/HLE, audio, stockage/I/O, loader, réseau, ABI GPU NS2 complète, shaders méthode par méthode, couverture MME64, capacités exactes RADV et PS5 Pro, qualification runtime sur les révisions examinées. Le prochain audit indépendant devra vérifier ces domaines ainsi que le couple moteur/vendor exact et les preuves matérielles.

**Décision de cette revue : aucune modification runtime ; stabiliser d'abord, puis mesurer les pistes d'évolution.**

## 19. Addendum — 27 novembre 2026 : rendement décroissant et risque de sur-ingénierie

**Une architecture déjà avancée ne doit pas être refondue pour le seul bénéfice théorique d'une méthode supplémentaire.** Les pistes A01–A08 sont une réserve d'études conditionnelles, non une feuille de route obligatoire ni un registre de défauts à clôturer. L'architecture actuelle pourrait déjà être proche d'un optimum pratique pour certains titres ; ce n'est pas encore démontré.

FC27 est un indicateur exigeant du runtime NS1 : JIT, GPU, shaders, mémoire, caches, synchronisations et présentation. Atteindre durablement 30 FPS réels (33,33 ms/image), sans micro-saccades, avec HUD et pause réactifs, fidélité visuelle, mémoire stable et fermeture propre constituerait une réussite majeure. Son plafond de 30 FPS ne démontre toutefois pas la proximité du maximum matériel ni l'optimalité de NS2. Mesurer la marge CPU/GPU, les percentiles de frametime, les scènes lourdes et plusieurs titres NS1/NS2 ; distinguer images invitées, répétitions et interpolation.

| Piste | Décision conditionnelle | Risque sans preuve |
|---|---|---|
| JIT sparse actuel | Conserver | Régression mémoire/stabilité |
| A01 — Barrières et drains | Corriger seulement les attentes coûteuses démontrées | Hazards et corruption graphique |
| A02 — Recording GPU parallèle | Différer sauf saturation CPU/recording mesurée | Coordination et contention |
| A03 — JIT sparse mutualisé | Différer sauf duplication coûteuse ou pression mémoire démontrée | Invalidations inter-cœurs, durée de vie des blocs |
| A04 — Textures sparse | Étudier si résidence dense réellement limitante | Coût de gestion de résidence |
| A05 — ASTC→BCn | Étudier si mémoire/bande passante limitantes | Perte de fidélité, coût du transcodage |
| A06 — MME64 | Compléter les contrats nécessaires ; optimiser sur profil | Régression sémantique |
| A07 — Zero-copy | Différer sauf copies significatives évitables | Layouts, ownership et durée de vie |
| A08 — CCX, PGO, pipelines | Différer sauf bénéfice reproductible | Déséquilibre de charge |

Ordre de décision : terminer la compatibilité NS2 et FC27 ; qualifier stabilité, fidélité et performances NS1/NS2 sur PS5 standard puis Pro ; mesurer la marge restante ; privilégier la simplification et la fiabilisation de l'existant. Ne rouvrir un chantier que sur preuve d'un besoin concret, avec référence avant/après, objectif mesurable, tests de non-régression et critère d'arrêt. Si le gain est négligeable, non reproductible ou obtenu au détriment de la fidélité, stabilité ou maintenabilité, conserver la solution actuelle.

**Règle d'arrêt : lorsque les objectifs fonctionnels et de performances sont atteints, aucune optimisation spéculative n'est requise pour déclarer le chantier terminé.** La correction d'un contrat manquant ou d'un défaut de sécurité mémoire reste nécessaire indépendamment des FPS. Préserver un seul chemin de production et éviter les mécanismes redondants. Le meilleur choix est celui qui apporte un résultat vérifiable sur le matériel cible au moindre coût raisonnable de complexité.

Cet addendum est une décision de stratégie technique, pas un nouveau résultat console. Aucun changement runtime n'en découle automatiquement.
