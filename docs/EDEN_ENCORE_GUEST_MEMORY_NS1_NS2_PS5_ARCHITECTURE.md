# Eden Encore — architecture de la mémoire invitée NS1 / NS2 sur PS5

**Dossier d'architecture, mécanismes et bibliographie — 23 novembre 2026.**
**Périmètre :** PS5 firmware 13.60, moteur [ProsperoEden-Encore](https://github.com/niakw/ProsperoEden-Encore), vendor [Prospero.Eden-Encore-vendor](https://github.com/niakw/Prospero.Eden-Encore-vendor).
**Base de comparaison vérifiée :** moteur `f3aa58ac65fed99d56151ed59a4ff61b3b899e89`, vendor/gitlink précédent `7bf93eb2da720281a09edd8f7d823fb2558ad937` ; correctif de fermeture vendor `09ce0af1ccf20a1f9278ed4ab401729768b1f925` intégré ensuite.
**Version console des traces étudiées :** moteur `25f12c020eb69ea9b7b29aac35dadcfe8b38f918`, vendor `716e069f212b89b6fd13af56b0677343cf41ba07`, binaire construit le 23/11/2026 à 00:24:33. **Ce dernier binaire ne contient pas les commits ci-dessus.**
**Statut :** architecture cible, diagnostic fondé sur logs et code sélectionné, correctifs partiels explicitement distingués. **Ni gestion demand-zero complète, ni boot NS2, ni réparation du crash de fermeture ne sont certifiés sur console.**

## 1. Décision et priorités

La mémoire physique PS5 est une ressource **commune** à l'hôte, au processus invité, au JIT, aux buffers/images RADV, aux stacks, aux caches et aux services. Une grande adresse invitée mappée n'est pas une grande allocation physique. La solution pérenne doit partager des **contrats d'ownership** entre NS1 et NS2, sans leur imposer des politiques identiques.

- **P0 — NS2 :** préserver les 12 Gio d'espace logique requis par les titres et ne payer que les plages **réellement écrites**, à la demande. La réservation sparse actuelle n'est pas une implémentation demand-zero, et un `ResultOutOfMemory` renvoyé proprement ne suffit pas à faire démarrer un jeu.
- **P0 — sortie FC27 :** la destruction des services et objets noyau doit respecter leurs références croisées ; les rapports `recursive_mutex lock failed: Invalid argument` sur fermeture manuelle sont de vraies anomalies du runtime, pas des faux positifs de journalisation.
- **P1 — FC27 NS1 :** optimiser seulement les coûts démontrés de cohérence, accès mémoire, upload, invalidations, contention BufferCache/TextureCache, pipelines et synchronisation ; les changements de résidence invités ne prouvent **aucun** gain de FPS en soi.
- **Garantie générale :** pas de désactivation de barriers GPU, pas de suppression de `memset` sans zéro observable, pas de libération de PA encore accessible par un alias, pas de changement du layout NS2 pour maquiller l'OOM.

## 2. Propriétaires natifs et chaîne des dépendances

| Sous-système | Source maintenue sélectionnée / configuration | Fonction et règle |
|---|---|---|
| Sélection source PS5 | [moteur `headless/CMakeLists.txt`](../headless/CMakeLists.txt) | Pour `PS5_NATIVE && EDEN_REVIEWED_DUAL_NPDM`, sélectionne la variante NS2 du `Core::System`, le backing sparse et les variantes kernel ; le graphe CMake est plus probant que l'arbre |
| Mémoire hôte | [`src/host_memory.cpp`](../src/host_memory.cpp), `Common::HostMemory` | Branches NS1/denses vs NS2 réservé ; `ClearBackingRegion`, map/unmap et fastmem |
| Plan de résidence | [`headless/ps5_ns2_guest_backing_plan.h`](../headless/ps5_ns2_guest_backing_plan.h) | Admission transactionnelle et comptabilité du budget 6 Gio actuel |
| Allocation NS2 PS5 | [`src/ns2_sparse_guest.cpp`](../src/ns2_sparse_guest.cpp) | Réserve VA 12 Gio, unités 2 Mio, alloc/maps DirectMemory, journalise le premier refus avec stage ; retient les blocs jusqu'au teardown |
| Process/layout NS2 | [`encore-active/ns2-runtime/process/core/core.cpp`](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/main/encore-active/ns2-runtime/process/core/core.cpp) | NPDM/ExeFS, 12 Gio, démarrage, ordre de sortie shared NS1/NS2 |
| Noyau invité PS5 | [`sparse-residency/k_memory_manager.cpp`](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/main/encore-active/ns2-runtime/sparse-residency/core/hle/kernel/k_memory_manager.cpp) | `AllocateForProcess` et `ClearBackingRegion`, précommit avant écriture directe ; rollback d'un cas d'échec avant `OpenFirst` |
| Slabs / mémoire partagée | [`sparse-residency` vendor](https://github.com/niakw/Prospero.Eden-Encore-vendor/tree/main/encore-active/ns2-runtime/sparse-residency) | Écriture dans des buffers kernel avant existence éventuelle de PTE processus |
| Scheduler / processus | [kernel_standard.cpp](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/main/encore-active/eden-core/src/core/hle/kernel/kernel_standard.cpp), [`k_process.cpp`](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/main/encore-active/ns2-runtime/process/core/hle/kernel/k_process.cpp) | Références, processus, arrêt CPU, verrous de scheduler et destruction |
| GPU / mémoire invitée | [vendor `eden-gpu`](https://github.com/niakw/Prospero.Eden-Encore-vendor/tree/main/encore-active/eden-gpu), `nvdrv_as`, `nvdrv_gpu`, `gpu_session` | Adresse GPU/GMMU, pages physiques, buffers, mappings dynamiques, DMA et fences |
| Vulkan / RADV | [vendor `eden-vulkan`](https://github.com/niakw/Prospero.Eden-Encore-vendor/tree/main/encore-active/eden-vulkan), [Mesa PS5](https://github.com/niakw/Prospero.Eden-Encore-vendor/tree/main/encore-active/ps5-mesa) | VkMemory, BufferCache/TextureCache, ressource encore en vol, cohérence hôte |
| JIT / Dynarmic | [`src/host_memory.cpp`](../src/host_memory.cpp), [architecture JIT](PS5_NATIVE_ARCHITECTURE.md) | VA réservée versus pages JIT physiques, alias RX/RW, invalidation et stabilité du code invité |

**Budget :** sur Encore, `HostMemory::Impl` traite le cas exact `requested == 12ull<<30` avec 12 Gio de VA et `PhysicalBudget = 6ull<<30`. Cette constante est un **plafond logique courant**, **pas** la quantité de mémoire réellement libre pour Vulkan. En NS1, ce branchement NS2 ne s'applique pas ; le JIT sparse 64 bits observé en logs est **un autre allocateur**.

## 3. Flux mémoire et états à construire

~~~mermaid
flowchart LR
  NPDM["NPDM / NS1-NS2 layout"] --> K["Guest kernel KMemoryManager"]
  K --> PT["CPU page tables / direct pointers"]
  K --> SLOT["PS5 backing owner: slot + generation + refcount"]
  SLOT --> Z["ZERO read-only / shared"]
  SLOT --> PA["OWN writable direct-memory PA"]
  PT --> JIT["Dynarmic / HLE / CPU access"]
  PA --> GMMU["NVMap / GMMU / GPU guest VA"]
  GMMU --> BC["BufferCache / TextureCache"]
  BC --> VK["RADV / VkBuffer / VkImage"]
  VK --> FENCE["Fence retirement / coherence"]
  FENCE --> SLOT
~~~

État minimal par bloc `2 Mio` (les 16 Kio ou autres tailles de page invités ne sont pas nécessairement de même granularité) :

| État | Lectures | Écritures | Mémoire physique | Transition admise |
|---|---|---|---|---|
| `UNMAPPED` | Interdites | Interdites | Aucune | Admission initiale vers `ZERO` |
| `ZERO` | Zéros corrects pour **tous** les clients | Fault/promotion, jamais écrire sur bloc partagé | Page zéro commune ou mapping équivalent matériellement garanti | `ZERO -> OWN` sous verrou |
| `OWN` | Valeurs dernières écrites, cohérentes CPU/GPU | Autorisées dans l'ownership correct | PA privée, refs de mappings et fences explicites | `OWN -> ZERO` seulement après clear complet, invalidation et retraite GPU |
| `RETIRING` | Pas de nouvelle publication | Pas de nouvelle écriture | Ancienne PA conservée tant que GPU/JIT/HLE l'utilise | Retrait de tous alias, puis release |
| `FAILED` | État antérieur inchangé | Interdites | Pas de PA partiellement publiée | `ResultOutOfMemory` uniquement après rollback intégral |

**Contrat concret :**
1. Valider offset, longueur, overflow, alignement et rôle CPU/GPU avant admission.
2. Publier les maps et métadonnées avec génération monotone et release/acquire sous mutex ; capturer les références existantes avant tout switch.
3. Sur une première écriture `ZERO`, allouer **une** PA, la remettre à zéro, la mapper avec droits corrects, publier puis reprendre la faute/écriture. Toute copie de donnée partagée préalable s'effectue **avant** publication.
4. Sur `ClearBackingRegion(fill=0)`, une plage intégrale vierge peut rester ou redevenir `ZERO` **seulement** si les lecteurs directs kernel, DMA, CPU et GPU voient les zéros. Une zone partielle exige conservation des octets non modifiés.
5. Sur `OWN -> ZERO` ou decommit, retirer alias fastmem, traductions GMMU, références NVMap, cache writeback et anciennes vues de shader ; attendre les fences en vol. Jamais d'`Unmap` physique sur une ressource GPU non retirée.
6. Le gestionnaire de défauts doit éviter malloc/locks réentrants et ne pas traiter un défaut d'accès hors région comme demande de promotion. Prévoir un chemin explicite pour les écritures C++ du kernel hors PTE.
7. Remise à zéro des identités/mappings entre titres et à la sortie ; conservez les SHAs et les générations pour empêcher une PA d'un ancien jeu de devenir le backing d'un nouveau sans réinitialisation.
8. Conserver l'ABI NS1, la table JIT 16 Mio, et les rollbacks BufferCache connus. Le layout NS2 12 Gio doit rester identique indépendamment du niveau de résidence.

**Ce qui ne suffit pas :** sauter `memset`, cacher le `bad_alloc`, relever le plafond physique, augmenter le cache JIT, compter les frames de l'écran de chargement, ni importer un COW Linux sans respecter les API PS5.

## 4. Sources et différences avec EglantinePS5

**Référence PS5 analysée :** [heydemoura/EglantinePS5, `5eb70367`](https://github.com/heydemoura/EglantinePS5/tree/5eb70367ffde039f237b3b828856f4b4247ea09e) (20/11/2026). **Référence NS2 HOS/GPU structurelle :** [zortos293/Lichii](https://github.com/zortos293/Lichii) ; le choix de référence dépend de la question, les deux ne sont pas interchangeables.

| Piste vérifiée | EglantinePS5 | Applicabilité Encore |
|---|---|---|
| Demand-zero | [`src/guest_memory_service.inc`](https://github.com/heydemoura/EglantinePS5/blob/5eb70367ffde039f237b3b828856f4b4247ea09e/src/guest_memory_service.inc) et [`src/memory_pages.cpp`](https://github.com/heydemoura/EglantinePS5/blob/5eb70367ffde039f237b3b828856f4b4247ea09e/src/memory_pages.cpp) | États `SlotZero`, `SlotOwn` ; défaut d'écriture, promotion, locks, alias. **Écart majeur démontré** : Encore pré-engage ses plages au `ClearBackingRegion` |
| API HostMemory | [`src/host_memory.cpp`](https://github.com/heydemoura/EglantinePS5/blob/5eb70367ffde039f237b3b828856f4b4247ea09e/src/host_memory.cpp) | `ClearGuestMemory` et `CommitGuestMemory` remplacent `memset` de plein backing ; ne pas transposer sans les callbacks sur accès hors PTE |
| Pression et ressource cold | [`docs/MKW-MEMORY-LEAK.md`](https://github.com/heydemoura/EglantinePS5/blob/5eb70367ffde039f237b3b828856f4b4247ea09e/docs/MKW-MEMORY-LEAK.md) | Mesures PS5 Eglantine : pages noyau mappées ~9,5 Go, vrai contenu physique variable ; pas de revendication d'une mesure Encore |
| Budget PS5 partagé | [`docs/MKW-MEMORY-BUDGET.md`](https://github.com/heydemoura/EglantinePS5/blob/5eb70367ffde039f237b3b828856f4b4247ea09e/docs/MKW-MEMORY-BUDGET.md) | Le budget partagé invité+driver+heap+stacks explique pourquoi une hausse naïve de RAM ou 8/10 Gio de layout n'est pas une solution |
| Fragmentation directe | [`src/direct_memory.c`](https://github.com/heydemoura/EglantinePS5/blob/5eb70367ffde039f237b3b828856f4b4247ea09e/src/direct_memory.c) | Classer allocations durables / temporaires avant placement haut/bas. Aucune preuve que la fragmentation cause notre refus sparse |
| Compression de RAM | états `SlotPacked` dans `guest_memory_service.inc` | **Non retenue au P0** : activation/retrait historiques liés à corruptions/hangs GPU ; pas de compression froide avant cohérence démontrée |
| Couverture GPU NS2 | [Lichii — code, issues, PR](https://github.com/zortos293/Lichii) | Comparer HOS, NVDRV, Ampere, textures, synchronisation, **sans traiter un stub Lichii comme preuve de fonctionnement PS5** |
| Cohérence de ressources | [Lichii PR #2452](https://github.com/zortos293/Lichii/pull/2452) — uploads et writeback de pages/texels recyclés | Indice récent (23/11) que rendre le backing avant le writeback et la publication de données fraîches peut provoquer des textures périmées ; vérifier les buffers et images Encore réellement sélectionnés |

Le service Eglantine possède aussi `SlotShared`, `SlotFine`, `SlotPacked`, `DropSlotAliases` et un récupérateur de blocs. **P0 retenu : `ZERO/OWN` correctement synchronisés.** Éviter de copier le fichier de ~116 Ko comme une correction isolée : il s'appuie sur les VM wrappers, gestionnaires de faute, wrappers de vues et contrats de GPU de cet autre projet. Les licences exactes et dépendances doivent être comparées avant reprise de code.

## 5. Références officielles, études et documents propriétaires

### 5.1 Références publiques techniques vérifiées

- [Linux Kernel — Page Tables](https://docs.kernel.org/next/mm/page_tables.html) : traduction, fautes, différence entre mapping, demande et page physique.
- [Linux Kernel — ZERO_PAGE, pagemap](https://docs.kernel.org/admin-guide/mm/pagemap.html) et [HMM](https://docs.kernel.org/mm/hmm.html) : page zéro, accès avec faute, invalidations des mappings GPU/device privé ; **principes**, pas ABI directement applicable à PS5.
- [Linux Kernel — nommu/mmap guide](https://docs.kernel.org/next/admin-guide/mm/nommu-mmap.html) : exemple de zéro partagé et copie physique au premier write dans la section MMU.
- [Khronos Vulkan — Sparse Resources](https://docs.vulkan.org/spec/latest/chapters/sparsemem.html) : binding/sparse residency et synchronisation **explicite** requise ; distinct du sparse guest CPU.
- [Khronos Vulkan — Synchronization and Cache Control](https://docs.vulkan.org/spec/latest/chapters/synchronization.html), [Memory Model](https://docs.vulkan.org/spec/latest/appendices/memorymodel.html) : ordonner publication, writes, reads et `vkFreeMemory` après fence.
- [Khronos Vulkan Guide — Sparse Resources](https://docs.vulkan.org/guide/latest/sparse_resources.html) : vpages, `vkQueueBindSparse`, propriétaires de queue ; une queue prenant en charge sparse binding n'implique pas automatiquement sparse image residency 2D.
- [Arm — Armv8-A memory model guide](https://developer.arm.com/-/media/Arm%20Developer%20Community/PDF/Learn%20the%20Architecture/Armv8-A%20memory%20model%20guide.pdf) : acquire/release/barrières **conceptuels** pour les programmes invités ; le CPU hôte PS5 reste x86-64.
- [SwitchBrew](https://switchbrew.org/wiki/Main_Page), [libnx](https://github.com/switchbrew/libnx), [Atmosphère](https://github.com/Atmosphere-NX/Atmosphere) : propriétés invités NS1/HOS et API ; ne documentent pas l'API d'allocation mémoire PS5.
- [Mesa RADV](https://docs.mesa3d.org/drivers/radv.html), [Vulkan Memory Allocator](https://github.com/GPUOpen-LibrariesAndSDKs/VulkanMemoryAllocator) : stratégie de mémoires/allocations Vulkan, distinctes du backing des pages invitées.
- [NVIDIA open-gpu-doc](https://github.com/NVIDIA/open-gpu-doc), [envytools](https://github.com/envytools/envytools) : unités de traduction GPU, caches et notions Maxwell/Ampere ; compatibilité avec la Switch 2 non garantie par ces documents génériques.
- [Dynarmic](https://github.com/merryhime/dynarmic) : interface de recompilation CPU ; les alias RX/RW et l'ABI concrète sont ceux du vendor sélectionné.

### 5.2 Documents PS5 internes et API propriétaires : niveau de confiance

| Domaine | API/owner observé | Ce qui doit être vérifié |
|---|---|---|
| Allocateur physique PS5 | `sceKernelAllocateDirectMemory`, `sceKernelReleaseDirectMemory` dans `src/ns2_sparse_guest.cpp` | Taille 2 Mio, alignement, fragmentation, droits, ownership et erreurs natives |
| Mapping VA PS5 | `sceKernelMapDirectMemory` / `sceKernelMunmap` et wrappers `Common::ReserveMemoryPages` | Réservation VA stable, adresses, droits, rollback, réentrance des fautes |
| Framebuffer et pool AGC | `headless` et drivers PS5 sélectionnés | Allocations physiques partagées, mémoire GPU in-flight, retraite de fences |
| Abstraction RADV native | `vendor/encore-active/ps5-mesa` et `eden-vulkan` | Budget mémoire affiché, budget réellement disponible, fragmentation et flush |
| JIT PS5 | `src/host_memory.cpp`, politiques JIT existantes | RX/RW et résidences, précommits, concurrence ; rollback historique du dispatch 64K |
| Observabilité et logs | crash report / heap / stderr PS5 | Corréler version installée, marqueur de refus, code natif et résultat console |

Les **headers/SDK propriétaires PlayStation** ne sont pas publiés dans ce dossier et **aucun contrat d'ABI supplémentaire n'est présumé**. Pour chaque adaptation, consulter les déclarations exactes de l'outillage PS5 utilisé et le code sélectionné ; ne pas présenter les pages Linux/FreeBSD comme spécifications PS5.

### 5.3 Documents internes à conserver comme registres, sans refaire leurs études

- [Architecture technique commune](ENCORE_TECHNICAL_ARCHITECTURE_AND_RESEARCH.md), section 5.3 et section 11 (propriétaires compilés).
- [Architecture native PS5 et JIT](PS5_NATIVE_ARCHITECTURE.md).
- [Catalogue des sources actives](EDEN_ACTIVE_SOURCE_CATALOG.md).
- [Bibliothèque technique NS1/NS2, 20/11](EDEN_ENCORE_BIBLIOTHEQUE_TECHNIQUE_NS1_NS2_2026-11-20.md).
- [Analyse des écarts NS2 puis NS1, 20/11](audits/EDEN_ENCORE_GAP_ANALYSIS_NS2_THEN_NS1_2026-11-20.md) : **instantané historique** moteur `58297357` / vendor `082cd1b7`, 96 points de statuts différents, **pas 96 bugs certifiés**.
- [Registre vivant de complétude NS2](audits/EDEN_ENCORE_NS2_IMPLEMENTATION_COMPLETENESS_REGISTER_2026-11-21.md), [FC27 F07](FC27_F07_MASTER_TRACKER.md), registres de tests PS5.

## 6. Nouvelles preuves console FC27, 23/11/2026 — ne pas mélanger les causes

**Même binaire installé** `25f12c02` : FC27 NS1 `0100C49025D3E000`, docked, Vulkan/RADV 26.2.0, rendu interne 1,25x, bilinéaire, **MSAA x4**, sortie 1440p à 60 Hz. Les jeux NS2 du même build ont un problème de mémoire distinct.

- **Crash fermeture réel et reproductible deux fois :** rapport PS5 01:48:19 (250 s) et 01:54:08 (342 s), `recursive_mutex lock failed: Invalid argument`, thread main, `eboot+0x41f55` (point de terminaison, pas origine symbolisée). Aucun watchdog ni accès guest invalide mesuré.
- **Fermeture avant exception :** `gpu_core.reset()` terminé, `kernel.CloseServices()` terminé, `services.reset()` terminé ; l'instruction suivante du core sélectionné est `service_manager.reset()`, puis `kernel.ShutdownCores()`. La source ne permet pas de choisir entre destructor SM et arrêt noyau sans pile native fiable. **Hypothèse ciblée intégrée dans vendor `09ce0af1` : garder SM vivant jusqu'à `ShutdownCores()`, sans reculer la libération de NVDRV** ; succès PS5 non validé.
- **Première fermeture déjà coûteuse :** un premier appel `SuspendEmulation(true)` a pris ~37,9 s dans la session ; le dernier passage de fermeture est beaucoup plus court. Ce symptôme ne se résout pas en neutralisant le détecteur de crash.
- **Frame pacing réellement irrégulier, ensemble du `crash-20261123-014819-heap.log` :** 43 fenêtres `EDEN_VULKAN_FRAME` d'environ cinq secondes, médiane **30,000 FPS**, minimum **16,747 FPS**, pire frame **1 422,896 ms**, **9/43** fenêtres sous 29 FPS, **3/43** sous 25 FPS, **24** événements `late100` et **5** événements `late500`. Une fenêtre à 25,517 FPS / 628,770 ms présente aussi **7 552** contentions BufferCache et **206,239 ms** d'attente cumulée. Les compteurs se recouvrent entre threads : **ne pas additionner comme temps d'une frame, ni imputer chaque pause au seul BufferCache**.
- **Fidélité encore ouverte :** `video_core/surface.cpp: Unimplemented format=0` récurrent et `fermi_2d_observed.cpp: Unresolved Fermi2D volume-slice copy`. Diagnostiquer identifiants de ressource, formats et copies de couches avant de prétendre optimiser l'upload.
- **Ressources :** environ 2,2 Gio de VA JIT réservée mais seulement ~36 Mio engagés à `game_loaded`; cette donnée exclut l'hypothèse simpliste « les ~2,2 Gio JIT sont 2,2 Gio de RAM physique consommée ». Le ralentissement tardif ne coïncide pas avec une compilation JIT dominante dans les fenêtres rapportées.
- **Attention :** le 30 FPS proche de la limite et les textures/HUD ne prouvent pas que l'absence d'un gestionnaire `ZERO/OWN` est leur cause. Prioriser contention BufferCache, invalidations, shader/pipelines, copies et présentation sur la même scène/réglages.

## 7. Validation et statut P0 — ordre d'exécution

| Étape | Preuve requise | État au 23/11 |
|---|---|---|
| Sources moteur/vendor/gitlink, unités natives | CMake + SHA exact et gitlink épinglé | Vérifiés pour `f3aa58ac` / `7bf93eb2` avant nouveau patch |
| Premier refus backing NS2 | `EDEN_NS2_SPARSE_COMMIT_DENIED stage=admission/native_physical_map/...` sur binaire nouveau | **Non mesuré** avec dernier binaire PS5, ancien SHA |
| Interception OOM kernel | Aucune exception native non contrôlée dans `AllocateForProcess` | Correctif source `7bf93eb2`, **console non testée** |
| Demand-zero `ZERO/OWN` | Accès CPU/HLE/IPC/GMMU, protection, défaut de première écriture, libération après fences | **À implémenter**, bloqué par preuve d'intégration de tous les accès directs |
| Crash de sortie FC27 | Quitter et relancer 2 fois sans exception, test de durée de vie mutex | Vendor `09ce0af1` intégré, **console non testée** |
| NS2 MKW / Bananza | `guest_run_begin`, première vraie soumission GPU invitée, première frame invitée, gameplay | **Ouvert**, zéro soumission invité confirmé sur ancien build |
| NS1 FC27 fidélité et perfs | Même scène/cache, p50/p95/p99 frametimes, frames >100 ms, HUD, texture et manette | **Ouvert**, pas de gain mesuré |

**Protocole de non-régression :** ne pas relancer un build PS5 pendant un autre ; vérifier le job, warnings, ELF, artefact, version installée, SHA moteur **et** vendor, puis rejouer FC27 entrée/sortie + deux titres NS2. À chaque résultat : symptôme → Title ID → logs → code/upstream → commit couple SHAs → tests/CI → résultat console → statut. Le prochain patch fonctionnel NS2 ne devra pas être une étude additionnelle : il doit intégrer le propriétaire `ZERO/OWN` dans le chemin C++ actif, avec garanties GPU vérifiées.

## 8. Ce qui n'est pas revendiqué

Ce document ne prouve pas que toutes les API firmware NS2 sont couvertes, que le vendor PS5 est interchangeable avec EglantinePS5, que la compression mémoire est sûre, que le crash FC27 est définitivement résolu, ni que la première frame NS2 est atteinte. La solution de mémoire invité devra être qualifiée par tests de cohérence, suivis d'un test PS5, **pas** par une simple augmentation de commits ou de la documentation.
