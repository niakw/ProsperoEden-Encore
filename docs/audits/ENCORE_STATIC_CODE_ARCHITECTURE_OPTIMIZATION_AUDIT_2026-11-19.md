# Eden Encore — audit de conformité aux méthodes officielles et aux études de recherche

> [!IMPORTANT]
> **La question auditée :** « Est-ce que le code réellement sélectionné pour Encore NS1/NS2 sur PS5 suit les bonnes méthodes décrites dans les documentations officielles et les études (architecture, correction, mémoire, synchronisation, performance, caches) ? »
>
> **Réponse courte :** **oui pour plusieurs mécanismes de conception**, **partiellement ou sans preuve suffisante pour d'autres**, **non certifiable globalement** à ce stade. Les problèmes de console connus ne constituent pas automatiquement des violations de normes, et une bonne structure de code ne garantit ni un jeu fonctionnel ni des FPS élevés.
>
> **Périmètre documentaire uniquement :** aucune modification C/C++, CMake, vendor, submodule, workflow ou package ; aucun build ou test console déclenché par cette révision.

**Date :** 19 novembre 2026 · **Plateforme :** PS5 13.60 · **Moteur inspecté :** [15ea79bb23ca](https://github.com/niakw/ProsperoEden-Encore/commit/15ea79bb23cac7cec195306a76c9923b1a516d39) · **Vendor épinglé dans le moteur :** [c15cdfe96a3d](https://github.com/niakw/Prospero.Eden-Encore-vendor/commit/c15cdfe96a3d836bf32ba21b8070088add81cdc9). Les constats fondés sur des captures PS5 plus anciennes portent toujours les SHAs de ces captures, et **pas** ceux-ci.

**Document mère :** [Architecture, composants, sources officielles et publications](../ENCORE_TECHNICAL_ARCHITECTURE_AND_RESEARCH.md). **Ancien audit détaillé :** [version historique du rapport au premier instantané](https://github.com/niakw/ProsperoEden-Encore/blob/1e75d1431b93ae051e3a56b362aefd855d50431d/docs/audits/ENCORE_STATIC_CODE_ARCHITECTURE_OPTIMIZATION_AUDIT_2026-11-19.md). Il reste utile pour ses relevés, mais plusieurs conclusions initiales sont obsolètes après des retours arrière.

## Lecture rapide

| Ce que tu veux savoir | Conclusion |
|---|---|
| **Notre architecture suit-elle les bonnes méthodes ?** | **Globalement cohérente sur les mécanismes inspectés** : propriétaires mémoire, transactions d'allocation, caches par génération, publication des tâches, chemins de repli explicites, décodage borné. |
| **Est-elle intégralement conforme aux spécifications ?** | **Non démontré.** La conformité nécessite des oracles sémantiques et des preuves d'exécution des chemins sélectionnés. Il n'existe pas ici d'audit exhaustif de toutes les instructions ARM, Maxwell, Ampere et SPIR-V. |
| **Les meilleures optimisations des études sont-elles déjà appliquées ?** | **Certaines idées pertinentes oui ; certaines non ; d'autres sont inapplicables telles quelles.** Les études NVIDIA/A100/GTX et les articles DBT ne dictent pas des constantes ni des correctifs PS5 prêts à importer. |
| **Faut-il refactoriser tout le moteur ?** | **Non.** Les priorités sont l'intégrité et la mesure des chemins actuels, puis des changements ciblés si un gain est démontrable. |
| **Qu'est-ce qui est réellement bloquant ?** | **NS2 sans première frame** et **FC27 textures/HUD/latence**, auxquels s'ajoutent les contrats de durée de vie et de provenance des unités natives. |
| **Quels changements de code cet audit demande-t-il maintenant ?** | **Aucun.** Il propose un ordre d'analyse, avec des critères objectifs avant chaque éventuelle modification. |

### Les couleurs : ne pas confondre état et urgence

| Verdict sur le code | Signification | Priorité métier, indépendante du verdict |
|---|---|---|
| 🟩 **Bonne pratique présente** | Mécanisme vu dans le **chemin de code inspecté** ; la conformité comportementale complète peut rester ouverte | 🟥 **P0** : démarrage bloqué, mémoire/corruption, deadlock, sécurité d'exécution |
| 🟨 **Partiel / à prouver** | Conception plausible, mais condition, couverture, artefact ou oracle manque | 🟧 **P1** : image, textures, performances, latence, gameplay |
| 🟥 **Écart confirmé** | Contradiction effective ou défaut démontré **à une révision précise** ; préciser si déjà corrigé/retiré | 🟨 **P2** : validation d'une fonction, qualité, observabilité, UX |
| ⬜ **Non évalué** | Lecture insuffisante, aucun verdict de conformité autorisé | 🟦 **P3** : entretien, documentation, optimisation non bloquante |
| 🟦 **Étude exploratoire** | Piste de recherche ou protocole de mesure, **pas** un standard ni un bug | |

**Niveaux de preuve :** **S** = source observée au SHA cité ; **T** = test hôte ; **B** = ELF/build natif exact ; **C** = console au SHA exact ; **M** = mesure comparative reproductible. **S ne vaut pas C**, et **B ne vaut pas M**.

## 1. Tableau de conformité : méthodes → code → verdict

> [!NOTE]
> Une ligne 🟩 signifie « la **méthode identifiée** est présente », jamais « toutes les obligations du standard sont certifiées ». Les liens de code et documents normatifs sont rassemblés en fin de page ; tous les liens de source citent un SHA fixe.

| Domaine | Méthode attendue par les références | Ce qu'Encore fait réellement | Verdict | Priorité et décision |
|---|---|---|---|---|
| **CPU / ARM / Dynarmic** | ISA et ABI cohérentes, même définition de classe entre unités, traduction des atomiques fiable ([Arm][R-ARM], [ABI][R-ABI], [étude concurrence][R-ARX-CONCUR]) | JIT/A64/A32, mémoire RX/RW ; la disposition A64 **est redevenue uniforme** après le rollback de la table réduite ([S-JIT-A64], [registre incident][I-A64]) | 🟩 **Réparation ABI en source** ; 🟨 sémantique complète non prouvée | 🟥 P0 **si régression** ; ne pas réactiver la table 64K sans approche ABI homogène |
| **JIT / mémoire exécutable** | Allocation bornée, invalidation et absence de libération tant qu'un thread exécute du code ([ABI][R-ABI], [DBT][R-ARX-DBT]) | Précommit borné, cache positif par génération, trim réservé aux états arrêtés ([S-JIT-PLAN]) | 🟩 Méthode présente ; 🟨 quiescence globale non certifiée | 🟥 P0 durée de vie ; **aucun gain FPS déduit du code** |
| **Mémoire invitée NS2** | Séparer réservation VA et RAM effectivement engagée, admission avant publication, rollback complet | 12 GiB virtuels / budget logiciel 6 GiB, blocs 2 MiB, <code>Begin → Stage → Publish</code> et rollback ([S-HOST], [S-NS2-RUNTIME], [S-NS2-PLAN]) | 🟩 Méthode présente ; 🟨 aliases GPU et budget réel PS5 | 🟥 P0 fiabilité ; profiler **premier** refus d'allocation |
| **GMMU / tables GPU** | Équilibrer empreinte mémoire, TLB/cache et coût de lookup ; mesurer avant d'optimiser ([microbenchmark][R-ARX-MEM]) | Des vecteurs d'état sont encore dimensionnés selon l'espace virtuel invité ([S-GMMU]) | 🟨 Choix non disqualifié, coût réel inconnu | 🟦 P3 optimisation **conditionnelle au RSS et au temps d'init** |
| **GPU NS1 / Maxwell** | Respect des commandes, ordre DMA/copies, invalidation des textures et fraîcheur des ressources ([guide Maxwell][R-MAX], [Vulkan sync][R-VSYNC]) | Sous-moteurs Maxwell et chemins de cache distincts ; protections de pages présentes ([S-GPU-NS1], [S-RASTER]) | 🟨 Correction visuelle **non démontrée** | 🟧 P1 : maillots/textures FC27, HUD, pauses |
| **GPU NS2 / Ampere** | Traduction ISA et barrières fidèle à la forme **réellement rencontrée** ([guide Ampere][R-AMP], [étude][R-ARX-AMP]) | Lowering Ampere, statuts explicites, cache générationnel et capture liée à la session ([S-AMP], [S-TRANS], [S-NS2-SPV]) | 🟩 Protections de session ; 🟨 couverture ISA/stages | 🟥 P0 **première commande/frame** ; ISA à approfondir **après** preuve d'usage |
| **SPIR-V / shaders** | Générer un module valide, avec capacités, types, barrières et scopes adéquats ([SPIR-V][R-SPV], [memory model][R-VMEM]) | Backend de recompilation, compilation NS2 Compute contrôlée par ticket de session ([S-NS2-SPV]) | 🟨 Présence ne certifie pas le shader final sur RADV | 🟧 P1 quand un stage réellement exécuté échoue |
| **Vulkan / BufferCache / textures** | Distinguer exécution, disponibilité et visibilité ; conserver ownership avant déverrouillage ([Vulkan sync][R-VSYNC]) | Invalidation et locks visibles ; le **flush différé FC27 a été retiré** : chemin synchrone actuel ([S-RASTER]) | 🟨 Modèle prudent présent ; 🟥 latences et textures constatées en jeu | 🟧 P1 ; ne pas reposer un ancien correctif sans preuve de course |
| **Pipelines / cache Vulkan** | Publication complète et réveil des waiters ; arrêt après drain ; cache versionné ([pipelines][R-VPIPE], [RADV][R-RADV]) | <code>is_built</code> publié en sortie, travailleurs et sérialisation drainés au destructeur ([S-GFXPIPE], [S-PIPECACHE]) | 🟩 Mécanismes présents ; 🟨 performance/échec constructeur à qualifier | 🟧 P1 : coût cold/warm et p99, pas refactor par principe |
| **Copies et staging GPU** | Copier uniquement des régions valides et préserver l'ordre des barrières ([Vulkan sync][R-VSYNC]) | Validation des copies nulles, coalescence limitée de régions adjacentes dans un appel ([S-BUFCACHE]) | 🟩 Garde-fous vus ; 🟨 limites extrêmes non établies | 🟨 P2 **après boot** : mesurer grandes listes, pas importer #102 à l'aveugle |
| **RADV / Mesa / PS5** | Respect des capacités réelles, de l'allocateur et du pipeline NIR/ACO ([Mesa][R-RADV], [AMD][R-RDNA]) | Mesa vendor avec overrides PS5 et cache disque adapté ([S-MESA]) | 🟨 Présence source ≠ options/binaires/exécutés | 🟧 P1 si artefact/driver implique une anomalie ; sinon contrôle de provenance |
| **HLE / threads / IPC** | Ordonnancement, exclusifs, signalisation et fermeture correctement ordonnés ([ARM][R-ARM], [concurrence][R-ARX-CONCUR]) | Verrous/fences, finalisation thread et condition variable ([S-HLE]) | 🟨 Invariants transversaux non prouvés | 🟥 P0 arrêt/relaunch ; 🟧 P1 pause/HUD |
| **NVDEC / FFmpeg** | <code>EAGAIN</code> n'a pas consommé le paquet ; drainer la sortie puis réessayer ; EOF/PTS cohérents ([FFmpeg][R-FF]) | Retry borné et queue de frames ([S-FF]) | 🟩 Méthode de backpressure présente ; 🟨 EOS/A-V console | 🟨 P2 hors symptôme réel |
| **Logs / observabilité** | Écriture sans blocage, budget disque, conservation exploitable des traces | Drain asynchrone, deux segments, reprise de trace ; rotation supprimant un ancien segment initial ([S-LOG]) | 🟩 Architecture de base ; 🟨 conservation intersessions | 🟨 P2 ; tester OFF→ON sans effacer la preuve d'incident |
| **i18n / UI** | Fallback de langue, glyphes, graphemes, shaping et direction ([Unicode][R-UNIC], [HarfBuzz][R-HB]) | Fallbacks régionaux explicites, dont en-GB et fr-CA ([S-I18N]) | 🟩 Résolution de catalogues ; 🟨 **31 langues non certifiées** | 🟨 P2 QA visuelle et typographique |
| **Build / source unique** | Une seule définition par TU et ABI ; artefact traçable au bon vendor | Overlays sélectionnés par CMake, guards source et macro NS2 GPU worker locale ([S-CMAKE], [S-GPU-WORKER]) | 🟩 Garde-fous présents ; 🟨 couverture de toutes les TU non exhaustive | 🟥 P0 **si ODR/ABI revient** ; audit compile_commands / ELF |
| **Dépendances / sécurité** | Versions traçables, alertes évaluées selon présence dans le produit, licences | Arbres moteur et vendor présents ; vues privées Dependabot/CodeQL **non relues pour ce rapport** | ⬜ **Non évalué en direct** | 🟨 P2 : inventaire réel, sans nombre inventé |

**Réponse de conformité :** il n'y a **pas de violation généralisée démontrée des méthodes officielles**. Il existe des **propriétés locales vérifiables**, des **domaines non certifiés** et des **problèmes runtime réels** à isoler. Les colonnes « à prouver » ne doivent pas être comptées comme des défauts nouvellement découverts.

## 2. Les vraies priorités, séparées des idées de recherche

### 🟥 P0 — Correction d'exécution et intégrité, avant toute optimisation secondaire

| ID | Fait / difficulté connue | Référence de méthode | Preuve attendue pour fermer |
|---|---|---|---|
| **AR-01 — NS2 démarre sans première frame** | Sur l'archive console [R457 post-test][I-POST], Bananza et MKW atteignent <code>guest_run_begin</code> mais **0 commande GPU de jeu / 0 frame** aux points observés. Une autre archive [R457 antérieure][I-LAST] relève <code>PC=0x4</code> et stack sous borne : **ce sont deux captures distinctes**. | HLE/loader, mémoire, pipeline d'exécution ; comparaison upstream Lichii RomFS index 0 et Eglantine sans présumer cause identique | Premier SVC bloquant/retour guest, contenu ExeFS/RomFS, progression CPU, commande GPU de jeu puis première frame **dans le même binaire** |
| **AR-02 — Propriété mémoire NS2** | Le sparse est présent ; sa libération exige la quiescence des alias CPU/GPU. Le plafond 6 GiB n'est pas une mesure de RAM libre. | Admission transactionnelle, rollback, absence d'UAF | Graphe de ownership et preuve du premier refus réel, de release et de relance |
| **AR-03 — Arrêt, retour launcher, relance** | JIT, GPU workers, caches et audio ont des durées de vie différentes ; des incidents historiques existent. | Ordre de destruction / drain / mémoire exécutable | Séquences start → stop → restart console, aucun worker survivant, mémoire libérée seulement après quiescence |
| **AR-16 — Cohérence binaire/ABI** | Une **ancienne table dispatch 64K conditionnée par PS5_NATIVE** provoquait un **désaccord de taille C++ entre TU**, et des écritures hors allocation ont été **démontrées dans un ancien ELF**. Le code actuel est revenu à 1M entrées uniformes. | ODR/ABI, une définition de classe, compilation cohérente | Source guards + tailles/offsets dans l'ELF natif exact ; ne jamais requalifier la réduction 64K comme gain courant |

**Point crucial :** un P0 peut être un problème de fonctionnement déjà connu, **pas une conclusion que CUDA/Vulkan/Arm ne sont pas respectés**. L'incident JIT historique est une vraie erreur d'ABI ; le démarrage NS2 sans frame ne suffit pas à localiser un manque Ampere ou RADV.

### 🟧 P1 — Les améliorations qui peuvent changer l'expérience réelle

| ID | Symptôme / source | Ce qui est déjà fait | Ce qui justifierait un changement |
|---|---|---|---|
| **AR-04 — FC27 contention BufferCache** | Les journaux [R457 anciens][I-LAST] mesurent 624 280 acquisitions contentieuses et ~15,4 s de **temps d'attente cumulé entre threads**. La trace plus récente [post-test][I-POST] mesure ~665 847 acquisitions. | Fast-path « jamais propriétaire » et invalidation synchrone ; le correctif différé vendor #194 a été **retiré** du vendor actuel ([rollback][I-VENDOR-ROLLBACK]) | Profil intérieur/verrou, oracle de cohérence textures, puis A/B console. Le temps cumulé n'est **pas** un freeze de 15 s |
| **AR-07 — Premiers shaders/pipelines** | Shader misses réels et longueurs de frames atypiques dans les anciennes traces | Caches CPU et workers pipeline avec protections de lifetime | Attribution du p99 à compile CPU, RADV, fence, scheduler ou guest ; comparaison cold/warm |
| **AR-10 — Maillots et HUD FC27** | Régression visible de textures, apparition/actualisation retardée de composants HUD | Cache images/buffers distincts, invalidation et garde-fous | Trace par texture : guest write → epoch/owner → upload → draw → fence → present ; **ne pas sacrifier la fidélité à un gain FPS** |
| **AR-11 — Pause et menus FC27** | Menu de pause parfois très tardif | HID, HLE/IPC, kernel et GPU existent | Timeline contrôleur → HID guest → IPC → thread guest → draw → present, plutôt que blâmer arbitrairement Vulkan |
| **AR-08 — Couverture Ampere** | Certaines sous-formes ISA/stages ne sont pas garanties ; le lowerer a été échantillonné, pas intégralement certifié | Capture avec ticket et génération, garde-fous sur shader Compute | **Après premier accès GPU invité**, capture d'opcode précis, paramètres et oracle numérique, puis comparaison upstream |
| **AR-09 — Cache shader/driver** | Le coût des recompilations peut compter à froid et après relance | Worker de sérialisation drainé, cache logiciel/driver séparés | Taux de hit/miss, UUID et clés de version, cohérence des écritures, comparaison entre relances |

> [!WARNING]
> **Les deux « optimisations déjà intégrées » de l'audit initial qui ne sont plus acquises :**
>
> 1. **A64 dispatch 64K** : rollback après défaut ODR/ABI prouvé (ancienne source <code>6c38328f</code>, retrait vendor <code>8e564f61</code>). Source actuelle : <code>0x100000</code> entrées de 16 octets, donc **16 MiB**, uniformément.
> 2. **FC27 publication différée des protections de pages** : introduite avec vendor [#194][I-PR194] puis **retirée** dans le vendor courant ; <code>RasterizerVulkan::OnCPUWrite</code> protège à nouveau les opérations de cache sous mutex, de façon synchrone.
>
> Le statut correct est « **pistes historiques évaluées puis annulées** », et non 🟩 « optimisations actives ». Ne surtout pas les réappliquer juste pour cocher une étude.

### 🟨 P2 — Qualité et qualification ciblée, sans détourner les P0/P1

| ID | Sujet | Décision documentaire |
|---|---|---|
| **AR-06** | Limites des copies Vulkan et très grandes listes de régions | Étudier [Eglantine #102][U-COPY], **seulement après activité GPU NS2** et mesure des soumissions ; vérifier les batchers déjà en place |
| **AR-12** | FFmpeg / NVDEC EOS, PTS et synchronisation | Le traitement de <code>EAGAIN</code> est déjà codé ; ne corriger que les séquences vidéo réelles fautives |
| **AR-14** | Logs ON/OFF/ON et conservation inter-boots | Contrat de rotation, crash, fermeture du titre, disque saturé ; ne pas inventer une fuite depuis un commentaire |
| **AR-15** | 31 langues, glyphes et rendu typographique | Écrans et polices réellement compilés, shaping RTL, placeholders, fallback régional ; catalogues ≠ couverture glyphique |
| **AR-20** | CodeQL, Dependabot, SBOM, toolchain, licences | Audit des alertes **actuelles des deux dépôts** et de l'usage runtime effectif, pas d'alertes historiques recyclées |

### 🟦 P3 — Optimisation secondaire : uniquement avec un bénéfice mesurable

| ID | Proposition | Critère **avant** implémentation |
|---|---|---|
| **AR-05** | Structure sparse pour tables GMMU | Mesurer allocations résidentes / temps constructeur ; comparer lookup et coût d'invalidation. Un <code>resize</code> selon VA n'est pas automatiquement une mauvaise méthode |
| **AR-13** | Révision FSR3.1/SGSR/R09/MSAA et budget VRAM | Tester **uniquement les chemins réellement sélectionnés** ; preuve d'image et coût mémoire ; pas de chantier artificiel de fonctions dormantes |
| **AR-17** | Commentaires NS2 sparse évoquant un mode « non activé / experimental » | Synchroniser le texte avec CMake natif, sans modifier le contrat exécutable |
| **AR-18** | Rapports anciens décrivant le JIT 64K ou une macro worker absente | Ajouter la succession des SHAs ; conserver intactes les preuves historiques |
| **AR-19** | CMake et organisation (~4 351 lignes sur le snapshot initial) | Cartographier les sources/TU réellement sélectionnées ; ne refactoriser que si risque démontré, duplication compilée ou maintenance bloquante |

**Règle d'investissement :** on n'ouvre pas un chantier pour « appliquer l'article » ; on le fait quand une propriété de correction ou une métrique concrète le justifie. C'est précisément ce qui évite 20 nouvelles fausses tâches d'optimisation.

## 3. Lecture des documentations officielles : qu'appliquons-nous exactement ?

Les **spécifications et contrats API** sont normatifs pour les interfaces concernées. Les guides d'optimisation sont des recommandations **conditionnelles**. Cette différence est fondamentale.

| Document officiel | Ce qu'il impose / recommande | Correspondance Encore | Limite du verdict |
|---|---|---|---|
| [Arm ARM][R-ARM] et [ABI AA][R-ABI] | Sémantique A64/A32, exclusifs, exceptions, convention d'appel, layouts cohérents | Dynarmic, loaders, JIT, mémoire ; **le défaut ODR 64K est bien retiré** ([S-JIT-A64], [I-A64]) | Tests différentiels et code machine exact requis pour toutes les formes atomiques/ABI |
| [Vulkan Synchronization][R-VSYNC] | Ordre d'exécution **distinct** de disponibilité/visibilité mémoire et durée de vie des ressources | Locks, invalidations, barrières et caches ([S-RASTER], [S-BUFCACHE]) | La présence d'une fence ne prouve pas que la bonne ressource est visible à temps |
| [Vulkan Memory Model][R-VMEM] et [SPIR-V][R-SPV] | Scopes et sémantique des accès atomiques, capacités et conformité des modules | IR, backend SPIR-V, MEMBAR Ampere, session Compute ([S-AMP], [S-NS2-SPV]) | Pas de certification des programmes shader réellement émis/exécutés |
| [Vulkan Pipelines][R-VPIPE] et [Mesa RADV][R-RADV] | Création/usage valide des pipelines, extensions du pilote, cache et compilation | Publication de fin de construction, worker drain, Mesa/overrides PS5 ([S-GFXPIPE], [S-PIPECACHE]) | Inspecter l'ELF, le profil RADV, les erreurs shader et les frames, pas uniquement le C++ |
| [FFmpeg send/receive][R-FF] | <code>EAGAIN</code> : produire/drainer la sortie et réessayer une entrée non acceptée | Boucle bornée de retry, stockage des frames ([S-FF]) | Vérifier EOS, timestamps, ordre A/V, couleurs et fin de titre |
| [ASTC][R-ASTC] | Formats/blocs et reconstruction fidèle des texels | Cache textures et chemins ASTC NS1/NS2 | Comparaison images et corpus de formats nécessaires ; un bug de maillot n'est pas forcément ASTC |
| [Unicode][R-UNIC] / [HarfBuzz][R-HB] | Séquences de caractères, direction, shaping et couverture de polices | Catalogues/fallbacks régionaux ([S-I18N]) | Les 31 langues doivent être rendues dans l'UI réelle ; Montserrat seul ne suffit pas nécessairement |
| [Maxwell tuning][R-MAX] / [Ampere tuning][R-AMP] | Optimisations propres aux GPU NVIDIA étudiés, contraintes de mémoire, occupation et synchronisation | Modèle des GPU **invités** NS1/NS2 ; traduction vers Vulkan/RADV AMD | Ce sont des **guides de performance**, pas des spécifications exhaustives des GPU Switch ; ne pas copier leurs constantes |
| [AMD RDNA performance][R-RDNA] | Mesurer bande passante, occupation, caches et limites du **GPU hôte** | Allocation et compilation Mesa/RADV, choix de pipeline | Pas de preuve que les compteurs/outils GPUOpen PC sont exposés par la PS5 |
| [NVIDIA JIT caching][R-JIT] | Versionnement, invalidation, warm/cold et séparation traduction/cache | Caches dynamiques et persistants de l'émulateur | **Analogie méthodologique** : le cache CUDA fat-binary n'est pas directement le cache Vulkan/Dynarmic d'Encore |

**Ce qu'il serait incorrect d'écrire :** « le document Maxwell préconise X, donc notre implémentation doit utiliser X sur la PS5 ». Encore **émule** les commandes NVIDIA puis les exécute via un **GPU AMD** ; la conformité vise la **sémantique invitée**, et l'optimisation vise le **matériel hôte**, par des mesures séparées.

## 4. Les études scientifiques : que peut-on utilement en déduire ?

> [!TIP]
> Une publication arXiv ne fournit pas automatiquement une obligation de code. Elle peut fournir une **hypothèse**, un **protocole de mesure**, une **méthode de validation** ou une **structure alternative**. On ne l'importe que si elle résout le même problème dans le même contexte.

| Étude vérifiée | Apport scientifique utilisable | Application ou situation actuelle | Décision |
|---|---|---|---|
| [On Architecture to Architecture Mapping for Concurrency][R-ARX-CONCUR] — arXiv 2009.03846 | Traduction sémantiquement correcte des modèles de concurrence ARM/x86 | Dynarmic, fences, mutex, alias, durée de vie ; le défaut historique A64 était un **problème C++ ABI**, distinct | 🟧 **Pertinent** : oracle interleavings, atomicité/ordre ; aucune substitution aveugle de fence |
| [Dissecting GPU Memory Hierarchy through Microbenchmarking][R-ARX-MEM] — Mei & Chu, arXiv 1509.02308 | Mesurer caches, TLB, effets de hiérarchie plutôt que supposer les temps | GMMU, page tables, caches textures GPU, FPS | 🟦 **Méthode de profiling** ; pas de latence GTX980 utilisable comme constante PS5 |
| [Demystifying the Nvidia Ampere Architecture through Microbenchmarking and Instruction-level Analysis][R-ARX-AMP] — arXiv 2208.11174 | Comprendre formes d'instructions, dépendances et différences PTX/SASS sur les GPU **étudiés** | Lowerer invité Ampere, barrières, formes HMMA et scoreboard | 🟨 **Guide de construction d'oracles** ; pas de « support complet NS2 » déductible du papier |
| [A System-Level Dynamic Binary Translator using Automatically-Learned Translation Rules][R-ARX-DBT] — arXiv 2402.09688 | Comparer structures de DBT, règle de traduction, coût/justesse | Dynarmic possède déjà sa propre IR et son propre cache | 🟦 **Recherche de fond**, aucune raison vérifiée de remplacer Dynarmic ou de réécrire le JIT |
| [Uncovering the Memory Hierarchy of Modern NVIDIA GPUs for Accurate Simulation][R-ARX-MEM26] — arXiv 2611.13860 | Caractériser empiriquement une mémoire GPU pour améliorer un modèle | Méthodologie potentielle pour comparer memory pressure GPU invité/hôte | 🟦 **Analogique** ; n'atteste aucun paramètre du T239 ou du RADV PS5 |

**Verdict recherche :** plusieurs principes sont **déjà présents** (cache borné et générationnel, ownership explicite, travail asynchrone drainé, instrumentation des chemins coûteux). **Aucun gain supplémentaire ne peut être promis** sur la seule lecture d'une publication. Une étude qui suggère une autre structure n'invalide pas l'implémentation présente si son coût n'a pas été mesuré.

## 5. Structure du projet : cohérence moteur + vendor

| Question d'architecture | Preuve source | Verdict / limite |
|---|---|---|
| **Les deux dépôts appartiennent-ils au même produit ?** | Gitlink vendor courant <code>c15cdfe96a3d</code> dans moteur <code>15ea79bb23ca</code> ; overlays maintenus dans <code>encore-active/</code> et sources de référence dans <code>sources/</code> | 🟩 **Oui** ; ne jamais analyser/mettre à jour une source vendor sans vérifier la sélection côté moteur |
| **La source compilée est-elle forcément celle qui porte le meilleur correctif ?** | <code>headless/CMakeLists.txt</code> remplace plusieurs TU, vérifie certains fichiers par <code>FATAL_ERROR</code> ([S-CMAKE]) | 🟨 **Pas garanti globalement** sans <code>compile_commands.json</code>, mapfile et ELF exact |
| **Y a-t-il une variante native PS5 research/experimental distincte ?** | [Décision de profil unique][I-ONE] : même application test et production | 🟩 Un seul produit natif ; flags de plateforme et capacités matérielles restent légitimes |
| **Le JIT 64K a-t-il vraiment été une bonne optimisation ?** | Ancien header dépendant de <code>PS5_NATIVE</code> différent suivant la TU ; incident ELF documenté ([I-A64]) | 🟥 **Non dans la variante passée** : violation ODR réelle ; 🟩 rollback uniforme dans le header courant |
| **Le GPU worker NS2 voit-il sa macro native ?** | Définition <code>PS5_NATIVE=1</code> **locale à cette TU** dans CMake ([S-GPU-WORKER]) | 🟩 Source câblée ; ⚪ présence dans **chaque** artefact à démontrer par inspection |
| **Le sparse NS2 est-il « expérimental non activé » ?** | CMake l'active sous PS5 native, mais ses commentaires disent encore « NOT included by default » ([S-CMAKE], [S-NS2-PLAN]) | 🟥 **Contradiction documentaire confirmée**, pas preuve d'un bug mémoire |
| **CMake est-il trop grand ?** | CMake natif dense, approximativement 4 351 lignes au snapshot initial | 🟨 Complexité de maintenance, **pas** preuve d'un problème d'exécution ni motif de refactor immédiat |
| **Les alertes de sécurité des deux repos sont-elles à jour ?** | Aucun inventaire privé actualisé inclus ici | ⬜ **Non vérifié** ; ne pas promettre « zéro vulnérabilité » |

**Bonne pratique structurelle à généraliser lors d'un futur audit build :** pour toute fonction critique, conserver une chaîne vérifiable **contrat officiel → source propriétaire → TU retenue → macros ABI → tests hôtes → ELF natif → titre/Title ID → logs → résultat PS5**. C'est plus utile qu'un nettoyage massif de fichiers.

## 6. Ordre des vérifications suggérées, sans lancer de chantier

1. **P0 — Geler les faits par SHA** : suivre les incidents actuels NS2 et l'ABI JIT avec les registres existants ; distinguer les vieux <code>PC=0x4</code> des sessions récentes sans première frame et les correctifs annulés.
2. **P1 — Comprendre FC27 avant de réoptimiser** : textures/maillots, invalidation GPU, <code>BufferCache::OnCPUWrite</code>, durée du verrou, shader misses et latence HUD/pause. Le correctif différé étant retiré, sa simple réintroduction n'est pas une solution documentée.
3. **P1 — Vérifier où le temps est perdu** : mesures cold/warm, p50/p95/p99, travail CPU concurrent, premier appel RADV, attente GPU et latence de présentation ; même scène, mêmes paramètres, exact vendor.
4. **P2 — Faire les audits ciblés des fonctions réellement utilisées** : pipeline cache, logs ON/OFF, NVDEC, UI 31 langues, sécurité des deux dépôts ; aucune optimisation globale sans incident.
5. **P3 — Ne tester les variantes structurelles qu'après preuve d'un coût** : GMMU sparse, grands batches de copies, éventuel découpage du CMake, sources dormantes. Classer « rejeté / non pertinent » si l'expérience ne trouve pas de problème.

### Critères pour déclarer une méthode « respectée »

- **Norme API/ISA :** référence exacte + fonction active + oracle positif/négatif + preuve du chemin compilé ; pour les sujets PS5, **résultat console**.
- **Optimisation :** métrique de référence, correction fonctionnelle conservée, comparaison sur même scène et couple moteur/vendor, gain significatif **sans régression**.
- **Étude arXiv :** hypothèse et protocole transposables précisés ; constants/limites matérielles originales **non réutilisées sans validation**.
- **Incident :** Title ID, première anomalie causale, logs exacts, lien upstream, correctif vérifié en source, CI/build, validation console puis statut.
- **Non vérifié :** conserver le statut **⬜** ; ne jamais le transformer en « conforme », « non conforme » ou « corrigé » par supposition.

## 7. Portée, historique et références vérifiables

**Ce qui a été fait pour cette édition :** relecture de l'audit initial et de l'architecture mère ; comparaison du <code>main</code> moteur et du gitlink vendor au 19/11 ; relecture **ciblée** des sources mémoire, JIT, rasterizer, GMMU, Ampere Compute, traduction, pipeline, FFmpeg, logs, CMake et i18n ; confrontation aux rapports console existants ; vérification des titres des publications arXiv citées.

**Ce qui n'a PAS été fait :** revue exhaustive de chaque TU/lignes des arbres Mesa/Eden/Dynarmic, preuve universelle de conformité à toutes les normes, exécution de compile/tests host, analyse d'un nouvel ELF, accès au runtime console, inventaire privé CodeQL/Dependabot. **Aucune conclusion de gain FPS ni de correction de gameplay n'est tirée de cette rédaction.**

**Évolution à ne jamais masquer :**

- **Avant rollback ABI** : vendor <code>6c38328f</code>, fast dispatch A64 64K sous macro locale, défaut de disposition et écriture hors allocation démontrés sur l'ancien binaire [registre][I-A64].
- **Après rollback ABI** : vendor <code>8e564f61</code> puis descendants, table 1M homogène ; l'archive PS5 [post-test][I-POST] atteint <code>guest_run_begin</code>, mais FC27 reste affecté et NS2 n'affiche toujours pas de première frame.
- **Avant rollback FC27** : vendor [#194][I-PR194] publiait certains changements de protections après libération du mutex ; l'ancienne matrice d'audit le présentait positivement.
- **Au vendor de cet audit, <code>c15cdfe96a3d</code>** : <code>OnCPUWrite</code> synchrone de nouveau ; [commit de retrait][I-VENDOR-ROLLBACK]. **Aucun A/B console sur ce dernier SHA n'est revendiqué.**

### Sources de code épinglées — moteur et vendor

[S-HOST]: https://github.com/niakw/ProsperoEden-Encore/blob/15ea79bb23cac7cec195306a76c9923b1a516d39/src/host_memory.cpp#L562-L599
[S-NS2-RUNTIME]: https://github.com/niakw/ProsperoEden-Encore/blob/15ea79bb23cac7cec195306a76c9923b1a516d39/src/ns2_sparse_guest.cpp#L24-L108
[S-NS2-PLAN]: https://github.com/niakw/ProsperoEden-Encore/blob/15ea79bb23cac7cec195306a76c9923b1a516d39/headless/ps5_ns2_guest_backing_plan.h#L1-L105
[S-JIT-PLAN]: https://github.com/niakw/ProsperoEden-Encore/blob/15ea79bb23cac7cec195306a76c9923b1a516d39/headless/jit-sparse-commit.h#L17-L85
[S-JIT-A64]: https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/c15cdfe96a3d836bf32ba21b8070088add81cdc9/encore-active/eden-core/src/dynarmic/backend/x64/a64_emit_x64_standard.h#L60-L77
[S-GMMU]: https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/c15cdfe96a3d836bf32ba21b8070088add81cdc9/encore-active/eden-core/src/video_core/memory_manager.cpp#L43-L70
[S-GPU-NS1]: https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/c15cdfe96a3d836bf32ba21b8070088add81cdc9/sources/eden/src/video_core/engines/
[S-AMP]: https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/c15cdfe96a3d836bf32ba21b8070088add81cdc9/encore-active/ns2-runtime/ampere/shader_recompiler/frontend/ampere/lower_to_maxwell.h
[S-TRANS]: https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/c15cdfe96a3d836bf32ba21b8070088add81cdc9/encore-active/ns2-runtime/ampere/shader_recompiler/frontend/ampere/translation_cache.cpp#L35-L110
[S-NS2-SPV]: https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/c15cdfe96a3d836bf32ba21b8070088add81cdc9/encore-active/ns2-runtime/ampere/video_core/ns2_shader_spirv_compile.cpp#L14-L71
[S-RASTER]: https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/c15cdfe96a3d836bf32ba21b8070088add81cdc9/encore-active/eden-vulkan/vulkan_rasterizer.cpp#L2425-L2515
[S-BUFCACHE]: https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/c15cdfe96a3d836bf32ba21b8070088add81cdc9/encore-active/eden-vulkan/vk_buffer_cache_cost.cpp#L590-L700
[S-GFXPIPE]: https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/c15cdfe96a3d836bf32ba21b8070088add81cdc9/encore-active/eden-vulkan/vk_graphics_pipeline_cost.cpp#L430-L495
[S-PIPECACHE]: https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/c15cdfe96a3d836bf32ba21b8070088add81cdc9/encore-active/eden-vulkan/vk_pipeline_cache_cost.cpp#L785-L813
[S-MESA]: https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/c15cdfe96a3d836bf32ba21b8070088add81cdc9/encore-active/ps5-mesa/src/util/disk_cache_os.c
[S-HLE]: https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/c15cdfe96a3d836bf32ba21b8070088add81cdc9/encore-active/eden-threading/src/core/hle/kernel/k_condition_variable.cpp
[S-FF]: https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/c15cdfe96a3d836bf32ba21b8070088add81cdc9/encore-active/eden-core/src/video_core/host1x/ffmpeg.cpp#L445-L480
[S-LOG]: https://github.com/niakw/ProsperoEden-Encore/blob/15ea79bb23cac7cec195306a76c9923b1a516d39/headless/log_pipe.h#L115-L160
[S-I18N]: https://github.com/niakw/ProsperoEden-Encore/blob/15ea79bb23cac7cec195306a76c9923b1a516d39/headless/prosperoeden/pe/core/strings.cpp#L97-L146
[S-CMAKE]: https://github.com/niakw/ProsperoEden-Encore/blob/15ea79bb23cac7cec195306a76c9923b1a516d39/headless/CMakeLists.txt#L355-L385
[S-GPU-WORKER]: https://github.com/niakw/ProsperoEden-Encore/blob/15ea79bb23cac7cec195306a76c9923b1a516d39/headless/CMakeLists.txt#L3680-L3705

### Spécifications, guides officiels et travaux scientifiques

[R-ARM]: https://developer.arm.com/documentation/ddi0487/latest
[R-ABI]: https://github.com/ARM-software/abi-aa
[R-VSYNC]: https://docs.vulkan.org/spec/latest/chapters/synchronization.html
[R-VMEM]: https://docs.vulkan.org/spec/latest/appendices/memorymodel.html
[R-VPIPE]: https://docs.vulkan.org/spec/latest/chapters/pipelines.html
[R-SPV]: https://registry.khronos.org/SPIR-V/specs/unified1/SPIRV.html
[R-RADV]: https://docs.mesa3d.org/drivers/radv.html
[R-RDNA]: https://gpuopen.com/learn/rdna-performance-guide/
[R-MAX]: https://docs.nvidia.com/cuda/maxwell-tuning-guide/
[R-AMP]: https://docs.nvidia.com/cuda/ampere-tuning-guide/
[R-JIT]: https://developer.nvidia.com/blog/cuda-pro-tip-understand-fat-binaries-jit-caching/
[R-FF]: https://ffmpeg.org/doxygen/trunk/group__lavc__encdec.html
[R-ASTC]: https://github.com/KhronosGroup/DataFormat/blob/main/astc.txt
[R-UNIC]: https://www.unicode.org/reports/
[R-HB]: https://harfbuzz.github.io/
[R-ARX-CONCUR]: https://arxiv.org/abs/2009.03846
[R-ARX-MEM]: https://arxiv.org/abs/1509.02308
[R-ARX-AMP]: https://arxiv.org/abs/2208.11174
[R-ARX-DBT]: https://arxiv.org/abs/2402.09688
[R-ARX-MEM26]: https://arxiv.org/abs/2611.13860

### Incidents, décisions de profil et comparateurs upstream

[I-A64]: PS5_R457_CC8044CE_P0_CROSS_TITLE_A64_JIT_SIGSEGV_2026-11-19.md
[I-POST]: PS5_R457_2026-11-19_FC27_NS2_POST_TEST.md
[I-LAST]: PS5_R457_2026-11-19_FC27_NS2_LAST_SESSION.md
[I-ONE]: ONE_NATIVE_BUILD_PROFILE_2026-11-19.md
[I-PR194]: https://github.com/niakw/Prospero.Eden-Encore-vendor/pull/194
[I-VENDOR-ROLLBACK]: https://github.com/niakw/Prospero.Eden-Encore-vendor/commit/c15cdfe96a3d836bf32ba21b8070088add81cdc9
[U-COPY]: https://github.com/heydemoura/EglantinePS5/pull/102

---

**Conclusion :** la bonne feuille d'audit est **« référence → invariant → chemin actif → preuve → priorité »**, et **pas** « 20 optimisations encore à faire ». Plusieurs recommandations sont déjà appliquées, deux optimisations précédentes ont été volontairement annulées après investigation, et les vraies lacunes de conformité concernent surtout les **preuves de comportement** et les **contrats transversaux de durée de vie**. Le prochain correctif doit être dicté par un défaut reproduit, pas par la simple existence d'une étude.
