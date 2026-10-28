# Eden Encore — Roadmap collaborative par familles de fonctions (révision 28 octobre 2026)

**Source de vérité du laboratoire fonctionnalités :** `feat/graphics-network-achievements`.  
**Branche console distincte :** `dev/ps5-sparse-jit` ; F01–F06 ont des contrats hôte, **F07 reste ouvert jusqu'à preuve sur console**.  
**Règle de séparation :** aucun merge ni activation expérimentale implicite sur la branche console. R00 avait fusionné historiquement la PR #18 ; l'écart entre les **HEAD actuels** doit être revérifié avant chaque import. Les nombres/SHAs des journaux anciens sont des **photos datées**, non des résultats CI actuels.

**Lecture :** les identifiants R00–R23 restent stables et R24 ajoute le chantier d'anti-aliasing perceptible ; **leur ordre dans le document suit désormais la famille fonctionnelle et ses checks globaux**, pas le numéro ni l'ordre des demandes. La section A est le point de départ obligatoire. Chaque jalon est inscrit une seule fois dans les tableaux de suivi ; le détail technique, les historiques et les références restent sous sa famille.

## Convention de suivi : pas de faux progrès

- Statuts : **À faire**, **Audit**, **Prototype host**, **Intégré natif**, **CI verte**, **Validé console**, **Reporté**. Un document ou un test de politique ne vaut pas intégration fonctionnelle.
- Responsable **Assistant** : investigation, sélection/licences, codes sources, correctifs, compilation, tests hôtes, workflows, nettoyage, documentation, package reproductible et matrice de preuve.
- Responsable **Utilisateur** : choix perceptifs (qualité/style/ergonomie), fourniture de deux PS5 si test multi-console exigé, test console **uniquement après** publication d'un build vert qualifié, retours visuels et logs. Ne pas faire du test console un substitut aux tests d'intégration hôte.
- **Droit de refus** technique : si coût GPU, licence, sérialisation, sécurité ou gameplay insuffisants, garder une option désactivée et tracer la raison. Pas de promesses de 30→60 FPS « natifs ».
- Les **tableaux uniques par catégorie ci-dessous** font foi ; un jalon apparaît dans une seule famille. Pour chaque livraison, enregistrer SHA, sources compilées, preuves, test et décision. Les détails historiques n'ajoutent pas de second état.

## Ordre de travail et contrôles transversaux

| Ordre | Famille fonctionnelle | Jalons regroupés | Check de sortie avant étape suivante |
|---|---|---|---|
| **A — d'abord** | Base et audits de l'émulateur, dépendances, forks et mesures | R00 · R05 · R18 · R23 · R02 · R17 · R01 | Sources réellement compilées + inventaire dépendances/licences + matrice d'écarts + référence mesurable |
| **B** | Moteur, stabilité, architecture CPU | R03 · R04 · R22 | Sémantique CPU/HLE/GPU préservée, tests de régression, recomp séparée |
| **C** | Graphismes et qualité d'image | R06 · R07 · R24 · R08 · R09 · R10 | Une seule interface Vulkan sûre, AA réellement perceptible et modes/performances mesurés séparément |
| **D** | Formats, bibliothèque, interface et mises à jour | R13 · R11 · R12 · R21 | Navigation/stockage/installation sûrs et testables |
| **E** | Réseau et multijoueur privé | R14 | Sessions et sécurité réseau isolées du rendu |
| **F** | Trophées et suivi de progression | R15 · R16 | Versionnement/événements fiables, pas de faux déblocages |
| **G — à la fin** | Intégration, CI/PS5, publication | R19 · R20 | Gates natifs, jeux tests, sûreté, preuve console et décision explicite |

**Règle de travail :** les audits A peuvent être conduits ensemble par sous-systèmes, mais chaque changement candidat est vérifié **sur le chemin natif effectivement sélectionné**. Les blocs B–F peuvent ensuite avancer en parallèle selon leurs dépendances, et G reprend les checks globaux A + régressions de toutes les fonctionnalités retenues. La logique n'impose pas d'attendre une recherche sans débouché (R22) pour avancer les graphismes ou l'UX.


## A — Référence technique, audits globaux et dépendances

Faire les vérifications **une seule fois à l'échelle de l'émulateur entier** avant de concevoir des correctifs. Le résultat n'est pas une liste de forks populaires, mais une cartographie des sources réellement compilées et des écarts utiles.

**Checks globaux A :** état exact de la branche feature vs console ; inventaire moteur et modules actifs ; BOM/dépendances avec versions SHA et licences ; comparatif des émulateurs/forks avec filtre anti-doublon ; conformité toolchain PS5, CMake/vendor, packaging, sécurité et CI ; mesures de référence. Si un correctif est déjà présent ou équivalent, ne pas le réimplémenter.

| ID | Livrable / périmètre | Assistant — travail et preuves | Utilisateur — intervention | État au suivi |
|---|---|---|---|---|
| **R00** | Synchroniser la branche laboratoire avec la baseline console, comparer les HEAD et préserver F01–F07 sans modifier la branche de validation | Vérifier les commits réellement inclus (PR #18 historique), comparer les HEAD actuels, résoudre la divergence seulement si nécessaire, figer le SHA d'essai et les sources compilées | Aucun test demandé | PR #18 historiquement intégrée ; fraîcheur avec la branche console actuelle à revérifier |
| **R05** | **Audit initial de l'émulateur Encore** : CPU A32/A64, Dynarmic/JIT, HLE/IPC, NVN/Maxwell, Vulkan, caches, threads, mémoire et allocations PS5 | Cataloguer les unités natives sélectionnées, overrides/générateurs, flags et chemins OFF ; relire les travaux existants, contrôler parité/risques, pins et preuves ; inclure GPU page table `1390bf5` et autres écarts sans les déclarer manquants | Aucun | Audit |
| **R18** | **Audit global des dépendances et de la qualité** : manifests/pins, SDK, Mesa/RADV/PS5_Vulkan, toolchain, bibliothèques, vendor/CMake, licences, sécurité et CI | Inventaire BOM + versions/SHA/licences/transitivité, intégrité des archives/binaires réellement embarqués, ABI/WSI/allocations, source owners, source scanning, secrets, artefacts et provenance ; tests d'hygiène maintenant et avant release | Aucun | Contrôles host déjà verts ; audit manuel restant |
| **R23** | **Audit systématique des émulateurs Switch** : fonctionnalités, correctifs et optimisations absents/équivalents dans Encore | Auditer Eden, Citron Neo, ProsperoEden, Ryubing/Ryujinx, Kenji-NX, Sudachi et forks Yuzu utiles ; comparer **commits/fonctions aux sources réellement compilées dans Encore**, qualifier licences, PS5/RADV, tests et gains mesurables ; dédoublonner R02/R05/R07–R10/R13/R17 | Aucun test utilisateur avant candidat compilé et qualifié ; arbitrer les seules nouveautés perceptives | **À faire — audit transversal planifié, aucune intégration déclarée** |
| **R02** | **Audit des forks PS5 proches** : ProsperoEden, Swordpdf/ProsperoEden, leurs patchs Mesa/Vulkan et composants réutilisables | Comparer patches aux **sources compilées** vendor/overrides, numéro SHA, licences, régression host | Aucun | Audit en cours |
| **R17** | **Audit des autres émulateurs PS5 (PS5SX2)** : atlas, préchargement, caches, packs, UX et apprentissages du runtime natif | Comparer propriétaires et contraintes mémoire, porter concepts uniquement avec preuves | Aucun avant prototype console | Audit |
| **R01** | Banc de mesures commun : guest FPS, present FPS, displayed FPS, CPU/GPU frametime, latence pad, RAM/VRAM, caches, qualité HUD, audio, pause/mi-temps | Instrumentation bornée, test de non-régression des compteurs, export d'un rapport JSON | Choix des scènes FC27/BOTW, validation A/B seulement au jalon console | Source composites/queue/generated/Present API branchés + analyse JSON, hôte vert ; GPU vrai/latence et console non mesurés |

### R23 — Audit transversal des émulateurs Switch : correctifs, optimisations et fonctionnalités (spécification)

**Objectif.** Faire l'inventaire systématique des améliorations disponibles dans d'autres moteurs/forks Switch **sans supposer qu'elles manquent dans Encore**. L'audit R02 traite les forks PS5 et les correctifs directs, R05 les optimisations internes, R17 PS5SX2 ; **R23 est la matrice inter-émulateurs** qui relie ces travaux aux sources compilées, sans re-cherry-pick. Il ne clôt **pas** le F07 de la branche console par simple comparaison de commits.

**Dépôts et lignées à inventorier (état, licence, HEAD/SHA de référence, activité et origine réels à revérifier à la date de l'audit) :**
- [Eden](https://github.com/eden-emulator/mirror) : base de l'émulateur, HLE, Dynarmic, shaders, GPU Vulkan, outils et interface ;
- [Citron Neo](https://github.com/citron-neo/emulator) : optimisations de buffers, fences, workers, textures, compilation shader et correctifs de synchronisation ;
- [ProsperoEden](https://github.com/blackbearreloaded/ProsperoEden) et forks PS5 pertinents dont [Swordpdf/ProsperoEden](https://github.com/Swordpdf/ProsperoEden) : backend PS5/RADV, drivers, mémoire, manette, packaging, fonctions graphiques ;
- [Ryubing](https://github.com/Leuconoe/Ryubing) / lignée Ryujinx et [Kenji-NX](https://github.com/Kenji-NX) : **références comportementales/architecturales**, portage direct C# → C++ **non présumé** ;
- [Sudachi](https://github.com/Synoptikon/Sudachi), Suyu, Torzu et autres dérivés Yuzu **uniquement s'ils apportent un diff fonctionnel vérifiable**, pas un inventaire de clones identiques.
- Vérifier si chaque dépôt est encore actif, accessible, maintenu et autorisé à être réutilisé ; les liens/lignées ci-dessus sont des **candidats de recherche**, non une garantie de statut/qualité.

**Premiers commits à comparer, pas à importer automatiquement (28 octobre 2026) :**

| Priorité de revue | Source / commit amont | Hypothèse utile | Point de comparaison Encore |
| --- | --- | --- | --- |
| P0 | [Citron `92960d1`](https://github.com/citron-neo/emulator/commit/92960d1f62500074df7a01d5c32a940e2c410c0c) | Regrouper les copies de téléchargement par buffer | F07 P0.3, fences/readback et ordre des écritures |
| P0 | [Citron `3a32975`](https://github.com/citron-neo/emulator/commit/3a32975538bf452062563537c8e3f83fe02cec7a) | Éviter une soumission/flush GPU redondant après fence | F07 P0.2/P0.3, barrières et dépendances de frame |
| P0 | [Citron `1aebfbd`](https://github.com/citron-neo/emulator/commit/1aebfbd6002f05436b797b485ded1ec6763bd4ac) | Réveils Vulkan moins fréquents, solution initialement **Android seulement** | Ordonnanceur et fréquence réelle PS5, pas de copie des seuils Android |
| P1 | [Citron `a8ef09e`](https://github.com/citron-neo/emulator/commit/a8ef09ef61210e38166aa2f809aee149a5fb2f91) | Streaming de buffers uniformes réutilisés, sans uploads redondants | Buffer cache actif, cohérence CPU↔GPU et réutilisation |
| P1 | [Citron `8a59863`](https://github.com/citron-neo/emulator/commit/8a598630a1dd1349a04b199c4a71fb413e26ac87) | Réutilisation de render targets avec padding | Texture cache, alias, taille, correction HUD et fences |
| P1 (refonte risquée) | [Citron `db66e38`](https://github.com/citron-neo/emulator/commit/db66e3819d7b14498b6f4b46a1b26a32ed79b53e) | Stockage d'instructions IR par pipeline et indexation compacte | P0.1 : temps IR→SPIR-V, coût mémoire, parité des shaders ; bench avant refonte |
| P1 compatibilité | [Eden `0689f73`](https://github.com/eden-emulator/mirror/commit/0689f73147ebeddb9ac5fb8b0edf2625425f8d71) | Résolution conditionnelle des handles de textures bindless | P0.4, shaders et fraîcheur des textures ; pas de diagnostic FC27 présumé |
| P1 risque/régression | [Eden `26a03d2`](https://github.com/eden-emulator/mirror/commit/26a03d2473787abf3223b2d0e65b291eee00c1e1) | Retour arrière d'une amélioration async shader pour performances | Examiner la raison du revert, les artefacts graphiques et les attentes ordonnées |
| P1 HLE/audio | [Citron `f07609c`](https://github.com/citron-neo/emulator/commit/f07609c52033797205de85826d5eb2b3d62c442a) / [`21813e8`](https://github.com/citron-neo/emulator/commit/21813e8cb3ea8194a5bcd8acc05b69e885f4d5c2) | ServiceManager host wait et initialisation audio différée | **Déjà retenus comme backports expérimentaux OFF** ; ne pas les compter intégrés au binaire normal |

**Inventaire fonctionnel distinct des optimisations CPU/GPU :**
1. Graphismes : post-traitement [Eden `ed56691`](https://github.com/eden-emulator/mirror/commit/ed566919f468e45ecb56e4e61185d98142a2cd1c), comparaison des AA, filtres de netteté, FSR spatial/temporel, colorimétrie, séparation HUD/scene ; raccorder aux jalons R06–R10, pas de bascule implicite dans le profil release.
2. Gameplay/compatibilité : gestion de mods/cheats, mises à jour/DLC, correctifs par Title ID/version, profils par jeu, possibilités 60 FPS **natives au jeu seulement si timing/physics/audio restent corrects** ; raccorder à R13 et au travail de compatibilité.
3. Fiabilité : shader/pipeline caches, thread scheduler, HLE/IPC, états mémoire, traitement du shutdown, sauvegardes, compatibilité manette ; comparer les **sémantiques** entre Ryujinx/Ryubing et l'architecture C++ de l'émulateur.
4. Fonctionnalités graphiques avancées : frame generation, textures HD, packs et capture/profiling, uniquement comme **fonctionnalités optionnelles** séparées des FPS simulés ; raccorder aux travaux R07–R10 et R17.

**Livrable obligatoire : une matrice versionnée par changement, et non un simple classement de projets.** Pour chaque entrée : projet/URL/commit, date et maintenance vérifiées, licence et attribution, fonction(s)/fichiers amont, source compilée Encore (et overrides/générateurs), preuve d'équivalence éventuelle, problème traité, dépendances PS5/RADV, risque de régression, résultat de test/benchmark, décision et propriétaire. Statuts exclusifs :
- **Déjà intégré** (avec SHA et chemin compilé) ;
- **Équivalent dans Encore** (avec test démontrant la parité) ;
- **Absent et pertinent** (candidat à prototyper avec preuve) ;
- **Incompatible / non transposable PS5** (raison documentée) ;
- **À mesurer / non tranché** (pas de promesse de gains).
Un patch ayant déjà son équivalent ne devient **pas** un nouveau travail ; une simple citation ou un titre de commit ne suffit jamais à conclure à son absence.

**Ordre et portes de sortie :** (1) figer refs, licences, ancêtres communs et diffs ; (2) rechercher la fonction dans le **profil natif sélectionné** de la branche R23, pas seulement `vendor/sources` ; (3) éliminer doublons et changements spécifiques Android/PC ; (4) établir tests comportementaux et microbenchmarks à coût comparable ; (5) uniquement pour les candidats retenus, implémenter une adaptation isolée **dans la branche feature**, opt-in ou rollback sûr, provenance et tests O0/O2/sanitizers ; (6) build PS5 + CI et A/B console regroupé **après** qualification, jamais de validation FPS sur tests hôtes ; (7) décision explicite reprendre / reporter / rejeter. Pour FC27 comparer P0.1–P0.4, HUD/pixels, >50/>100 ms, FPS guest/present, latence manette et freezes ; ne jamais confondre FPS affichés et FPS du jeu.

**Frontière stricte :** R23 reste **recherche/spec et éventuellement prototypes indépendants** sur `feat/graphics-network-achievements`. Aucun merge, changement de pins, activation expérimentale ni correctif F07 déclaré validé sur `dev/ps5-sparse-jit` sans passage distinct des contrats d'intégration, CI, build PS5 et tests matériels. **Statut : À faire ; cette inscription à la roadmap n'est pas un audit exhaustif exécuté ni une fonctionnalité livrée.**

### R02/R23 — Correctifs des forks : éviter les re-cherry-picks

- **Déjà vérifiés chez Encore (ne pas recopier)** : fix vertex dynamique [`1b6ffb8`](https://github.com/Swordpdf/ProsperoEden/commit/1b6ffb887), limite 512 draws [`0dd9dd0`](https://github.com/Swordpdf/ProsperoEden/commit/0dd9dd0fd), caches pipeline atomiques [`207e77f`](https://github.com/Swordpdf/ProsperoEden/commit/207e77fe4), locks pipeline mutualisés [`737152f`](https://github.com/Swordpdf/ProsperoEden/commit/737152f6f).
- **Candidats historiques ensuite adaptés dans la branche feature** : NaN shader `e34338d`, transferts RADV `1862764`, RomFS wide-tree `4f813a3`, AudioIn silence `01e81e1`. Les phrases de l'audit initial sur le destructeur RomFS par défaut et `NullSinkStreamImpl` sont antérieures à la livraison R04 documentée plus bas ; **vérifier les sources au HEAD** avant d'en déduire qu'un patch manque.
- **À auditer et non activer directement** : sparse address `1390bf5`, vitesse par jeu `23e0424`, packs/update/cheats `47cce6b`/`da39bc4`.
- **PS5SX2** : préchargement des ressources, polices/atlas et notifications trophées sont des inspirations UX, pas un code exécutable Switch transposable.

### R01 — télémétrie reliée au vrai Vulkan (sans déductions trompeuses)

- `headless/frame_metrics.h` définit un compteur opt-in **par session**, remis à zéro après l'arrêt de l'ancien titre par `headless/main.cpp`, sans aucune allocation/horloge/log sur le chemin rapide désactivé.
- Le **vrai** `vulkan_renderer.cpp` publie le nombre de callbacks de composition source, vraies images mises en queue, éventuelles images générées et frames sautées ; `vulkan_present_manager.cpp` compte les retours d'API `swapchain.Present` après succès. Une image générée n'est jamais décrite comme un FPS simulé.
- `headless/performance.cpp` ajoute uniquement au reporting de 5 secondes (logs détaillés) une ligne `EDEN_R01_FRAME_METRICS` avec intervalle temporel réel et taux séparés ; **aucun benchmark synthétique n'est présenté comme jeu réel**.
- `tools/check-feature-r01-native-frame-metrics-host.py` compile en C++20/UBSan `-O0/-O2` le header réellement inclus par le renderer, vérifie l'ordre des événements, la concurrence et les remises à zéro entre titres.
- `tools/analyze-r01-frame-metrics.py --json boot-trace.txt` analyse des vraies lignes de logs et produit un JSON par session, en distinguant les FPS de callbacks des FPS queue/Present API. `tools/test-analyze-r01-frame-metrics.py` teste données pondérées, corruption, reset et l'interdiction d'inventer `actual_guest_fps`, `input_to_photon_latency` ou `gpu_render_time_ms`.
- **R01 n'est pas complet** : la vitesse réelle de simulation guest, timestamps GPU, délais bout-en-bout manette-écran, qualité temporelle, et mesure sur PS5 13.60 sont distincts et restent ouverts.
- **R03 qualification** : premier build R03 [#40240190354](https://github.com/niakw/Prospero.Eden-Encore/actions/runs/40240190354) a bloqué sur deux contrôles de provenance non actualisés (`radv-active-inputs.py` 12→14 et `check-radv-official-indirect-draw.py` ancienne équivalence). Les audits ont été mis à jour **sans désactivation**, et la comptabilité du registre V109/R24/R25/U86 réconciliée. Ne pas déclarer le build PS5 vert avant une nouvelle exécution complète.

## B — Moteur, robustesse et recherche d'architecture CPU

Intervenir sur les **fonctions cœur** déjà identifiées après l'audit A, sans mélanger une correction de sémantique avec une nouvelle architecture hypothétique.

**Checks globaux B :** guest CPU/JIT et HLE, timing, audio, système de fichiers, GPU/RADV et buffers ; tests de cohérence mémoire, ordering/fences, démarrage, arrêt et sauvegardes. R22 reste une étude séparée (recompilation statique), jamais une substitution automatique de Dynarmic.

| ID | Livrable / périmètre | Assistant — travail et preuves | Utilisateur — intervention | État au suivi |
|---|---|---|---|---|
| **R03** | Patches ciblés : shader NaN `e34338d`, transferts RADV `1862764` | Modifier la vraie source propriétaire/patch RADV, tests shaders, stress barrières/transferts et rebuild complet | Validation visuelle FC27 uniquement si build global vert | Correctifs sources déjà décrits dans la branche feature ; tests/CI natifs et état au HEAD à confirmer |
| **R04** | RomFS vaste arborescence `4f813a3`, AudioIn buffer silencieux `01e81e1`, durée de vie et arrêt corrects | Tests sanitizer à 256 KiB/32768 entrées, AudioIn longueur/données et zéro régression AudioOut | Aucun | Correctifs sources déjà décrits dans la branche feature ; tests/CI natifs et état au HEAD à confirmer |
| **R22** | **Question : une recompilation statique optionnelle de jeux Switch 1 ARM64 vers x86-64 PS5 peut-elle compléter Eden Encore ?** | Étude comparative JIT Dynarmic vs chaîne AArch64 → C/C++/LLVM → binaire PS5 ; analyse des barrières NSO/NRO, relocations, JIT/dynamiques, ABI, SVC/HLE, GPU Maxwell/NVN, licences et maintenance ; preuve de concept sur programme synthétique autorisé, puis A/B limité si faisable | Aucun test console avant prototype qualifié ; choix ultérieur seulement après preuves | **À étudier — question ouverte, aucune implémentation** |

### R22 — Étude de faisabilité : recompilation statique Switch 1 → PS5 (question ouverte)

**Question de recherche :** une chaîne de recompilation statique, inspirée des approches type ReXGlue mais **non transposable telle quelle** à la Switch, pourrait-elle exécuter certains jeux Switch 1 sur PS5 plus efficacement que le JIT Dynarmic, **en complément de l'émulation classique et sans sacrifier la compatibilité** ?

**Périmètre de l'étude, sans engagement d'implémentation :**
1. Comparer les architectures (Switch 1 : AArch64 / ARMv8 ; PS5 : x86-64), la faisabilité d'une traduction statique du code NSO/NRO vers IR/C/C++/LLVM ou code natif, le traitement des relocations, branches indirectes, modules liés, données exécutables et génération dynamique de code. Établir explicitement les limites par titre et versions.
2. Identifier les composants **qui resteraient émulés ou adaptés** : services Horizon/SVC/HLE, synchronisation, mémoire, entrées, audio et surtout API GPU NVN/Maxwell → Vulkan/RADV. Une recompilation CPU ne corrige pas automatiquement les shaders, le HUD, les textures ou les problèmes de synchronisation graphique.
3. Évaluer les coûts de développement, maintenance, compilation, taille des binaires, cache, fiabilité et compatibilité ; comparer avec le JIT existant et les optimisations actuelles. Examiner les projets open source réutilisables, leurs licences, leur état réel, les contraintes d'outillage PS5 et le droit applicable ; ne pas redistribuer de jeux, clés, firmware ni code propriétaire.
4. Si les obstacles précédents sont franchis, produire d'abord un **POC synthétique légal** avec tests d'instructions et d'appels HLE, puis un protocole d'évaluation ciblé (FC27 / BOTW uniquement si titres et droits disponibles) avec mêmes scènes, guest FPS, 1 % low, frametimes, HUD, stabilité, latence et usage RAM. Distinguer le coût de compilation hors ligne du coût d'exécution.
5. Documenter une décision explicite : **abandon / recherche supplémentaire / prototype expérimental par jeu**. Aucun mode recomp n'est proposé dans la release ni fusionné avec `dev/ps5-sparse-jit` sans validation technique, CI et tests console.

**Graphismes :** la recompilation seule n'améliore ni résolution, ni textures, ni éclairage, ni anticrénelage. Elle peut éventuellement libérer un budget CPU pour les fonctions graphiques déjà prévues en R06–R10 ; toute amélioration visuelle devra être développée, mesurée et validée séparément.

**Statut : À étudier.** Ne pas annoncer de gain de FPS, de compatibilité générale, de portage automatique ou d'intégration IA avant démonstration.

## C — Graphismes et qualité d'image (pipeline Vulkan)

Construire **une seule base graphique vérifiable**, puis ajouter les familles de traitement sans recoder les mêmes hooks, buffers et fonctions de présentation.

**Checks globaux C :** origine scene/HUD, images et ownership, layouts/barrières, fences/present, depth/motion/jitter, allocations et coûts GPU ; comparer les modes d'anti-aliasing sur images fixes **et en mouvement**, avec les mêmes résolutions internes/sorties ; comparer vraie fréquence guest, fréquence présentée et fréquence synthétique. Refuser les filtres qui masquent un HUD périmé ou augmentent la latence.

| ID | Livrable / périmètre | Assistant — travail et preuves | Utilisateur — intervention | État au suivi |
|---|---|---|---|---|
| **R06** | **Architecture graphique modulaire** : résolution/AA, génération d'images, rendu neuronal et textures HD comme quatre familles indépendantes | Points d'insertion Vulkan (avant/après HUD), images/queues/fences, copie zero-copy si possible, toggles opt-in, recovery/fallback, profil par jeu | Choix des libellés et défauts | Contrat de sélection des 4 familles et tests hôtes verts ; aucun backend installé |
| **R07** | Upscaling : Natif / FSR spatial / FSR temporel 3.1 si infos validées ; AA/FSR et HUD séparé | Vérifier depth, jitter et motion vectors issus du rendu émulé ; calcul du coût GPU et A/B fidélité | Retour sur netteté et textures de FC27/BOTW | À faire |
| **R24** | **Anti-aliasing réellement efficace et réglable** : audit de l'efficacité actuelle None/FXAA/SMAA, paliers de qualité AA, examen du MSAA ×2/×4/×8 et des alternatives temporelles/SSAA, UI globale + par jeu | Vérifier les vrais passes Vulkan actifs et leur ordre par rapport à FSR/HUD ; comparer images fixes et mouvement, aliasing/shimmer, flou/ghosting, coût GPU/VRAM et latence ; n'afficher que des paliers réellement implémentés | Valider l'amélioration visible sur FC27 (pelouse/tribunes/HUD) et BOTW après build qualifié | **À faire — retour console : réglages actuels peu perceptibles ; aucune nouvelle méthode livrée** |
| **R08** | MihawkGen (priorité native PS5), comparaison FSR 3 frame generation, LSFG facultatif si juridiquement/native viable | Porter petites unités isolées, poids + licence, pipeline de présentation, 30→60 *affichés* avec FPS du jeu constants, reset à la pause/menu | Test visuel et ressenti input après CI | À faire |
| **R09** | **Neural Rendering AMD/Vulkan** : visages/peau/matériaux/lumière, sans modifier les vraies textures jeu | POC Vulkan natif SPIR-V, analyser RDNA2, budget mémoire+compute, pré-upscale vs post-upscale, alpha/UI, couleur HDR/gamma, scènes statiques et mouvement | Qualité artistique et artefacts visage, comparaison captures A/B | Recherche ; pas de runtime |
| **R10** | **Textures HD IA** séparées du rendu neuronal : packs optionnels par Title ID, prétraitement hors PS5 si nécessaire | Pipeline autorisé modèles ouverts (Real-ESRGAN ou équivalent), validation dims/formats/quantification, ram budget, cache, fallback GPU | Choix éventuel des packs / style ; aucun fichier protégé demandé | À faire |

### R06 — première abstraction de modes graphiques, **sans moteur factice**

- `extras/graphics/graphics_pipeline_policy.h` définit séparément les choix de résolution, frame generation, rendu neuronal AMD/Vulkan, textures HD et 60/120 Hz.
- Chaque choix reste **off par défaut** tant que shader/binaire Vulkan, masques HUD, motion/depth, modèle autorisé et fréquence négociée ne sont pas prouvés. Les causes de refus `resolution_reason`, `generation_reason`, `neural_reason`, `texture_reason` et `display_reason` sont indépendantes.
- `extras/graphics/test_graphics_pipeline_policy.cpp` teste avec UBSan les modes incompatibles, 30 FPS → FG **potentielle**, données temporelles, séparation UI et licence modèle ; la CI [Feature Lab](https://github.com/niakw/Prospero.Eden-Encore/actions/runs/40242290098) est verte. `runtime_qualified=false` reste obligatoire : **aucun MihawkGen, FSR temporel ou Neural AMD réellement branché par ce prototype**.
- Les retours à l'upscaling spatial ou natif, et le repli 120→60 Hz, ne doivent jamais être confondus avec un gain d'images simulées. Le vrai pont Vulkan scene/depth/motion/UI et la gestion des images/fences sont toujours à coder.

### R24 — Anti-aliasing : contrôle de qualité et résultat visible (nouvelle demande du 29/10/2026)

**Problème observé sur console.** Dans les tests actuels, passer de **Aucun à FXAA/SMAA** a eu **très peu d'effet perceptible**. L'option ne doit pas être considérée satisfaisante au seul motif qu'elle existe dans l'interface ou qu'un shader est exécuté. Il faut vérifier en priorité le **chemin Vulkan natif effectivement compilé**, les dimensions source/cible, le pass AA sélectionné, le traitement du swapchain, les formats et l'ordre AA ↔ upscale ↔ HUD, ainsi que la persistance du réglage global/par jeu. Les anomalies de textures/HUD ou le shimmer dû au jeu lui-même ne se résolvent pas systématiquement par du post-AA.

**Spécification fonctionnelle et nomenclature (éviter les faux ×2/×4/×8) :**

1. **Audit de l'existant** : photographier pour les mêmes scènes les modes `None / FXAA / SMAA` actuellement disponibles, vérifier que chaque réglage modifie réellement le traitement en jeu et que le passage entre eux n'est ni neutralisé ni écrasé par un preset, le mode TV, FSR ou un override par titre. Contrôler le contraste visuel à échelle 1:1 et les artefacts en mouvement.
2. **Paliers de qualité** : proposer une UX claire `Désactivé / FXAA (standard, qualité renforcée si algorithme réel) / SMAA (standard, qualité renforcée si algorithme réel)`, avec choix par défaut raisonnable et réglages globaux/par titre. Un niveau `Élevé` ou `Ultra` **n'apparaît que si** la variante technique est codée, réellement différenciée, compatible PS5 et validée ; éviter les sélecteurs décoratifs ou un simple `FXAA ×4`.
3. **MSAA ×2 / ×4 / ×8 — étude de faisabilité distincte** : ces nombres désignent des **échantillons de rasterisation**, pas l'intensité FXAA/SMAA. Auditer les render targets du jeu émulé, le support des sample counts/formats, l'architecture de présentation et les coûts GPU/VRAM PS5. Ne proposer un vrai menu `MSAA : 2× / 4× / 8×` que si le moteur peut produire et résoudre des surfaces multisample **sans altérer la sémantique guest** ; sinon documenter explicitement l'impossibilité et ne pas simuler de faux MSAA en post-traitement.
4. **Alternatives modernes** : évaluer un AA temporel (TAA ou équivalent compatible), seulement si les motion vectors, depth, jitter et données d'historique sont fiables ; vérifier le ghosting, les contours mobiles, l'herbe et les textes. Comparer au **supersampling** via l'option existante `Game resolution 1.25× / 1.5× / 2×` : ce sont des **facteurs de résolution**, non du MSAA ni des taux de FPS. Ne pas dupliquer artificiellement cette option sous un faux libellé AA ×2.
5. **Composition** : appliquer l'AA au bon stade (scène avant composition du HUD quand séparables), préserver textes/glyphes/menu, ne pas rendre les textures manquantes « floues mais présentes ». Définir explicitement les combinaisons permises avec le scaler bilinéaire/bicubique, FSR spatial, FSR temporel et modes de génération d'images ; fallback vers une méthode légère ou `None` quand les préconditions manquent.

**Preuves de sortie obligatoires (avant intégration console) :**
- **Captures A/B reproductibles** de la même scène/résolution, sans et avec AA, sur FC27 (lignes du terrain, pelouse, tribunes, joueurs, HUD) et BOTW (végétation, arêtes fines, mouvement de caméra). Vérifier le résultat à 100 % sans confondre amélioration de netteté et diminution de l'aliasing.
- **Séquences mobiles** : scintillement temporel, fourmillement, ghosting, flou de mouvement et stabilité des objets/overlays ; régressions du HUD, pause, mi-temps, changement de résolution, relance de jeu et overrides.
- **Coût mesuré** : frametime CPU/GPU, cadence guest/present, latence si mesurable, consommation VRAM, allocations, stalls/caches ; éviter de sacrifier la fluidité de FC27 à une qualité peu visible. Les valeurs doivent provenir de mesures PS5, pas d'une estimation desktop.
- **Gates** : audit du chemin compilé → prototype isolé sur branche feature → tests hôtes + sécurité/lifetime des ressources AA → CI/build PS5 vert → comparatif console → acceptation/rejet de chaque variante. Ne pas fusionner vers `dev/ps5-sparse-jit` par simple ajout documentaire.

**Critère d'acceptation :** plusieurs paliers uniquement s'ils correspondent à des traitements et résultats **objectivement distincts**, avec gain de qualité visible sur scènes de référence et coût rendu acceptable ; aucune promesse que MSAA ×8 ou TAA sera réalisable sur le rendu émulé. **Statut R24 : À faire (spécification seulement, aucun correctif ni test exécuté ici).**

### R09 — Registre de recherche — IA « DLSS 5-like » sur AMD (état au 25/10/2026)

Ne pas confondre **RDNA2 PC**, **Vulkan PC** et **PS5 native**. Aucune des implémentations NR suivantes n'a été qualifiée par nous sur la PS5 13.60 ; ne pas expédier d'exécutables DLL Windows, de modèles propriétaires ou de poids extraits d'un runtime NVIDIA.

| Référence | Pourquoi | Blocage / preuve à demander | Classement |
|---|---|---|---|
| [mochizuki0323/DLSSNR-AMD](https://github.com/mochizuki0323/DLSSNR-AMD) | Réimplémentation compute Vulkan SPIR-V, sélection de petits modèles ; c'est la piste la plus proche d'un module natif | Testé publiquement sur RX 9070 XT RDNA4 et Mesa Linux, modèles obtenus séparément d'une DLL NVIDIA ; RDNA2 sans validation | **R09-A** : étude prioritaire du scheduler/compute et des licences |
| [shakhbazian/OptiScaler-RDNA2NR](https://github.com/shakhbazian/OptiScaler-RDNA2NR) | Travail GPU `gfx1030` RDNA2 et traitement détails/couleurs avant ou après upscale | RX 6900 XT PC HIP/DirectX12 ≠ PS5, prix GPU fortement sensible à résolution ; modèles non librement distribuables | **R09-B** : algorithmes/quantification RDNA2 |
| [danielblnc/DLSS-NR-on-AMD](https://github.com/danielblnc/DLSS-NR-on-AMD) | Port NR AMD incluant RDNA2 expérimental et réglages de structure/peau/teinte | HIP 7, Windows/DX12, modèles utilisateur ; code/livrables/propriété intellectuelle à auditer | **R09-C** : référence fonctionnelle, pas binaire embarqué |
| [zmodelerlover/OpenNR-ReShade](https://github.com/zmodelerlover/OpenNR-ReShade) et [kibblerz/DLSS5-Reshade-AIO](https://github.com/kibblerz/DLSS5-Reshade-AIO) | Hooks rendu, mouvement estimé et interface des effets | ReShade/injection Windows ; port PS5 nul à ce jour | **R09-D** : idées d'intégration seulement |
| [Overclockers/DLSSNR-AMD-upstream](https://github.com/Overclockers/DLSSNR-AMD-upstream) | Optimisations Vulkan et comparaison quantitative au modèle original | Bibliothèque modèle, RDNA4 uniquement validé | **R09-E** : vérification mathématique/visuelle |
| [3zwr1/AMD-NR---OptiScaler](https://github.com/3zwr1/AMD-NR---OptiScaler) | Masque personnage, profils de teinte, mise à l'échelle du modèle, réduction charge, parallélisme | Ecosystème Windows/HIP, nombreuses dépendances/licences | **R09-F** : UX, stylisation et scheduler |
| [maanHimself/OpenDLSS-NR](https://github.com/maanHimself/OpenDLSS-NR) | Topologie 71 blocs et version browser/WebGPU sans Tensor Cores | Modèle ~141 MiB, coût et droits des poids, GPU RDNA2 | **R09-G** : portabilité algorithmique |
| [bloc97/Anime4K](https://github.com/bloc97/Anime4K) | Mode netteté/ligne stylisée à faible coût et shaders portables | Favorise dessin/anime, pas reconstruction de visage photoréaliste | **R09-Lite** : solution sûre si gros NR trop lent |
| [eFMann/shadPS4-Bloodborne-DLSS-FSR](https://github.com/eFMann/shadPS4-Bloodborne-DLSS-FSR) | Vraie stratégie d'émulateur : profondeur + mouvement caméra/personnage, jitter, UI après upscale, FSR FG | Code shadPS4 PC/PS4 spécifique non drop-in et statut licence à confirmer | **R07/R08** : design d'interface |
| [mihawk-99/PS5_MihawkGen](https://github.com/mihawk-99/PS5_MihawkGen) et [Swordpdf/ProsperoEden `650306c`](https://github.com/Swordpdf/ProsperoEden/commit/650306c9fd4b309720e87b58b2e5f8311f02badc) | Petite interpolation par réseau GPU PS5 avec source, shaders, outils et tests | Vérifier mesures réelles sur 13.60, licence et compat backend | **R08-A** : cible FG prioritaire |
| [GPUOpen FidelityFX SDK](https://github.com/GPUOpen-LibrariesAndSDKs/FidelityFX-SDK) | FSR 3.1, FG et APIs publiques | Ne pas confondre AMD Redstone FSR4/ML DX12/RDNA4 et anciens chemins FSR3 compatibles PS5 ; motion/depth difficiles | **R07/R08-B** |

**NR = transformation des pixels** (matériaux/peau/éclairage) ; **textures HD = ressources GPU modifiées**, éventuellement produites par IA en amont ; **FG = interpolation d'images** ; **SR = reconstruction/résolution**. Ces fonctions sont composables, mais multiplient potentiellement la latence et le coût.

### Contrat de validation graphique

1. A/B de la **même frame source** : fidélité couleur, rendu personnage, tissus, visage, texte, HUD, textures et déformations.
2. Séries animées : stabilité temporelle, occlusions, doubles contours, entrées manette, pause/reprise, mi-temps, cache shader, changement de résolution, retour menu.
3. Chiffres séparés : `guest_fps`, `present_real_fps`, `displayed_fps`, `framegen_ms`, `neural_ms`, `gpu_frame_ms`, `input_to_photon` ou proxy clairement étiqueté, RAM/VRAM.
4. Aucune option ne peut changer la sémantique des JIT/sync/audio ou se présenter comme « 60 FPS de gameplay » si le jeu reste à 30 FPS.
5. Retour au mode normal sans perte de données si pilote ne supporte pas un mode, mémoire insuffisante, échec shader, mauvais modèle ou latence insupportable.
6. Vérifier licences **source, poids, datasets et binaires** séparément ; noms « AMD Neural Rendering » ou « Encore Neural » en interface, jamais fausse appellation DLSS NVIDIA natif.

## D — Jeux, bibliothèque, interface et mise à jour applicative

Regrouper les **fonctionnalités utilisateur et l'expérience launcher** : fichiers, mods/updates/DLC, artwork, navigation, paramètres et mise à jour de l'application.

**Checks globaux D :** formats/parsers avec corpus synthétique légal, séparation des données utilisateur et fichiers d'installation, cache/quotas, WebP 80 %, manette/FR-EN, compatibilité firmware, installation/reprise/échec sans perte de sauvegardes. R21 ne télécharge ni n'installe silencieusement.

| ID | Livrable / périmètre | Assistant — travail et preuves | Utilisateur — intervention | État au suivi |
|---|---|---|---|---|
| **R13** | Formats Switch NSP/XCI/NSZ/XCZ, ZBIC/ZSTD et NRO/NSO/NCA/NAX/KIP, LZ4 selon contenu, mods/DLC/updates sans extraction fragile | Inventaire matrice **par forme d'entrée**, parsers concrets, corpus légal synthétique, fuzz/quotas, chemin happy+failure, pas d'affirmation sans lancement | Essais finaux uniquement des formats que l'utilisateur possède légalement | Audit/À faire |
| **R11** | Jaquettes Switch 3D front/back recomposées : couche support plastique, vraie composition `cover`, haut du back complet, pas de double tranche ; logo et description GameDB | Cas réels sans box images, chargement LaunchBox **à la sélection uniquement**, placeholder opaque, WebP 80% avec décodeur natif, cache/quotas | Validation visuelle sur maquettes et photos une fois testable | À faire |
| **R12** | Launcher : navigation L1/R1 des tâches de fond, profil/avatar si PS5 l'autorise, FR/EN, formats Go, focus/manette, 3D L2/R2, description README capture réelle | Tests hors console de génération/rendu et snapshots de composition, compat bibliothèque et mémoire | Validation ergonomie, seulement sur build de qualification | À faire |
| **R21** | **Mise à jour de l'application Eden Encore depuis les GitHub Releases** dans Paramètres : vérification manuelle forcée et recherche automatique au lancement du launcher (opt-in), proposition par pop-up puis installation uniquement après accord | Comparateur de versions et canal release stable, client GitHub borné, vérification du paquet PS5 et SHA-256, installateur natif sûr selon capacités réelles, tests hors console puis CI/PS5, préservation des données utilisateur | Choix d'activer la recherche au démarrage ; confirmation/refus de la mise à jour lorsqu'elle est proposée ; essai final sur build qualifié | **À faire — spécification uniquement** |

### R21 — Mise à jour intégrée d'Eden Encore (spécification, non implémentée)

**Cible** : ajouter à `Paramètres → Application → Mises à jour` une fonction de mise à jour **de l'application native Eden Encore** depuis les releases GitHub officielles de [`niakw/Prospero.Eden-Encore`](https://github.com/niakw/Prospero.Eden-Encore/releases). Ne pas confondre cette fonction avec la mise à jour des jeux Switch, des DLC ou du firmware émulé.

**UX à livrer** :
1. **« Vérifier / mettre à jour maintenant »** : action manuelle disponible même si l'automatisme est désactivé. Elle force une **nouvelle consultation** de GitHub (pas seulement un cache) et, si une version compatible plus récente existe, permet de la télécharger et installer après confirmation. En l'absence de nouveauté, afficher clairement « Déjà à jour ». Ne jamais rétrograder ni réinstaller silencieusement la version courante.
2. **« Rechercher les mises à jour au démarrage »** : interrupteur persistant, **désactivé par défaut**. À chaque entrée dans le launcher (une vérification par démarrage, et non par rafraîchissement d'écran), effectuer la détection **en arrière-plan sans bloquer l'affichage ni le lancement d'un jeu**. Si une release éligible est disponible, ouvrir une **pop-up à l'entrée** avec version installée, version proposée, résumé/changelog et boutons **« Mettre à jour » / « Plus tard »**. Aucune installation ni téléchargement intégral sans validation explicite. Si le joueur est déjà en jeu, différer la pop-up jusqu'au retour au launcher.
3. Après acceptation : état de téléchargement/vérification/installation lisible à la manette ; en cas de succès, inviter à **redémarrer l'application** si nécessaire. Annulation ou « Plus tard » préserve la version existante et les préférences ; toute erreur réseau se traduit par une indication non bloquante et ne boucle pas sur des pop-ups.

**Source et validation des releases** :
- Canal **stable uniquement** : consulter les releases publiées du dépôt officiel (`GET https://api.github.com/repos/niakw/Prospero.Eden-Encore/releases/latest` ou équivalent API vérifié) ; rejeter les drafts, préreleases, branches expérimentales, assets non correspondants, paquets FTP et réponses inattendues. Ne jamais télécharger un exécutable depuis une URL dictée par un changelog ou une redirection non approuvée.
- Comparer la version **réellement installée** à la version annoncée (version + identifiant de build lorsque nécessaire), sans comparer naïvement des chaînes lexicales ; ne proposer une version qu'en présence d'un **asset de release destiné à l'app PS5** et compatible avec l'identifiant de l'application, le format de paquet et les prérequis installateur/firmware. Ne pas présumer que le contenu d'une release GitHub est automatiquement installable sur la console.
- Télécharger dans un emplacement temporaire avec quotas, limites de taille et timeouts ; contrôler l'origine HTTPS, les métadonnées du paquet et un **SHA-256 publié et fiable** avant toute installation. En l'absence de hash exploitable, d'asset compatible ou de privilèges/API d'installation prouvés : refuser l'installation automatique et expliquer l'indisponibilité, plutôt que tenter une copie hasardeuse.
- **Ne jamais écraser l'exécutable en cours à chaud.** Vérifier l'API/mécanisme natif PS5 d'installation/upgrade, la possibilité de relancer l'app et le retour sur échec. Préserver `/data`, configurations, sauvegardes, caches utiles et bibliothèque ; aucune suppression implicite, aucune réinitialisation. Prévoir une stratégie de récupération réaliste plutôt que promettre un rollback système non démontré.
- Éviter vérifications concurrentes, pop-ups doublons, notifications répétées après refus pendant la même session, ou requêtes réseau à chaque navigation. Le mode hors ligne et les erreurs GitHub/rate limit doivent laisser le launcher pleinement fonctionnel.

**Preuves avant validation R21** : tests hôtes avec réponses GitHub simulées (aucune release, déjà à jour, version supérieure, prerelease/draft, asset manquant, manifest/hash altéré, réseau lent/absent, annulation, refus, reprise), tests de versionnement, non-régression boot/menus/manette, tests de sûreté de l'installateur réel, build PS5 et CI. Vérifier sur console seulement après qualification complète, et **uniquement sur la branche laboratoire** jusqu'à décision R20. **Statut : À faire ; aucun updater livré aujourd'hui.**

## E — Réseau et multijoueur local privé

Garder le protocole LDN indépendant du GPU, des mises à jour de l'application et du système de trophées.

**Checks globaux E :** chemin offline, secret/session, paquets bornés, DNS/IPv4, expiration/reconnexion, interruption propre et essai avec deux instances réelles. Pas de revendication Nintendo Online.

| ID | Livrable / périmètre | Assistant — travail et preuves | Utilisateur — intervention | État au suivi |
|---|---|---|---|---|
| **R14** | Multijoueur privé LDN `eden-room` compatible mode local wireless des jeux Switch | Adapter Swordpdf multiplayer et pont HLE LDN, chiffrement/auth réseau privé, mot de passe session (pas plaintext disque), UDP borné, DNS/IPv4, reconnection, nettoyage | Fournir si possible seconde instance/console, test partie complète | Audit ; non intégré |

## F — Trophées communautaires et progression

Séparer la progression manuelle, possible sans instrumentation, des déblocages automatiques conditionnés par des événements fiables par jeu/version.

**Checks globaux F :** Title ID et version, licence du catalogue, persistance atomique, aucune invention de trophées gagnés, détecteurs HLE validés et zéro faux positif. Les jeux sans preuve restent manuels.

| ID | Livrable / périmètre | Assistant — travail et preuves | Utilisateur — intervention | État au suivi |
|---|---|---|---|---|
| **R15** | Dépôt isolé de catalogues Switch 1 avec IDs/versions + licences/curation ; progression **manuelle** locale | Extraire module `extras/switch-trophies` quand API/version stable, persistance atomique, UI, notifications, aucun faux déblocage | Définition des règles de trophées souhaitées et visuels | Prototype host partiel |
| **R16** | Déblocage automatique seulement si évènement fiable HLE/observation versionnée ; jamais « tous les jeux » automatiquement sans preuve | APIs d'événements, détecteurs tests, invalidation après mise à jour et faux positifs, mode manuel pour les jeux inconnus | Validation sur jeux pilotes ; autoriser notifications | À faire |

## G — Intégration, qualification native et publication

Consolider **les modules terminés**, pas toutes les idées, dans un paquet testable et une décision explicite de livraison.

**Checks globaux G :** chaque fonctionnalité a un SHA, une preuve host, une compilation native, des tests sécurité et un rollback ; campagnes PS5 regroupées, comparaison FC27/BOTW, HUD/latence/VRAM. R18 est rejoué à la fin ; la branche console F07 ne reçoit rien par implication.

| ID | Livrable / périmètre | Assistant — travail et preuves | Utilisateur — intervention | État au suivi |
|---|---|---|---|---|
| **R19** | Builds indépendants par fonctionnalité avec désactivation sûre + scénarios concurrents (NR+FG, FSR+FG, HUD) | CI hôte/sanitizers, bundle PS5, A/B baseline FC27/BOTW, latence GPU/cache, tableaux comparatifs | Un seul cycle de qualification consolidé, pas un test à chaque commit | À faire |
| **R20** | Décision de fusion, release notes FR/EN, guide sécurité/limites, suivi par fonctionnalité | Merge seulement des modules validés, changelog/permissions et rollback, package avec SHA | Acceptation console matérielle par l'utilisateur | À faire |

## Dépendances réelles et recontrôles globaux

**Portes de vérification (ne pas les confondre avec la numérotation) :**

1. **Gate A0 — cartographie initiale :** R00 compare les deux branches ; R05 établit l'état réel du moteur, R18 établit le BOM complet (dépendances directes et transitives, pins, checksums, licence, ABI et sources réellement embarquées), R23/R02/R17 recensent les écarts **par fonction**, R01 permet de mesurer sans inventer de FPS. Si le code est déjà intégré/équivalent, fermer le doublon avec preuve plutôt que reprogrammer.
2. **Gate B0 — correctifs du moteur :** R03/R04 n'acceptent de nouveau code qu'après le résultat de A0 pertinent et un test reproduisant le défaut. R22 est une étude indépendante de recompilation, non un préalable à la release ni une amélioration graphique.
3. **Gate C0 — architecture graphique :** R06 d'abord (ownership, images, barrières, renderer, UI) puis R07/R08/R09/R10 selon la capacité matérielle et les mesures. Aucun moteur de frame generation ou NR n'est activé dans le profil de référence par la seule présence du code.
4. **Gate D0 — fonctionnalités utilisateur :** R13 vérifie les fichiers et données, puis R11/R12 traitent médias et interaction. R21 peut développer UX/détection sans attendre la publication, **mais l'installation native doit disposer du format de release, de l'installateur et du mécanisme de reprise validés par R19/R20** ; pas de cycle de dépendance imposant une release avant le simple développement de l'interface.
5. **Gate E/F — services indépendants :** R14 et R15→R16 ont leurs tests propres ; aucun prérequis de frame generation, d'IA ou de recomp.
6. **Gate G0 — régression totale :** R19 rassemble uniquement les modifications qualifiées et **rejoue l'audit R18** (licences, binaires, SDK/Mesa, sécurité, tests et provenance) sur le même SHA, puis R20 décide de publier ou de reporter. Comparer une build console stable, avec métriques HUD/latence/frames et compatibilité, jamais une suite de commits non compilés.

**Livrable de la famille A :** un registre unique avec `catégorie → projet/dépendance → commit/version → sources natives propriétaires → statut (présent / équivalent / absent pertinent / incompatible / à mesurer) → risque → test → décision`. Distinction obligatoire entre **audit accompli**, **correctif intégré**, **CI native verte**, **mesure console confirmée** et **fonctionnalité effectivement livrée**. Le registre des forks de R23 complète la carte d'audit du dépôt ; il ne remplace ni les notices légales ni la preuve du binaire produit.


## Historique de l'exécution et preuves datées — ne pas confondre avec le plan cible

## Journal d'exécution — chantier R00/R04

- **R00 code fusionné** : [PR #18](https://github.com/niakw/Prospero.Eden-Encore/pull/18), commit `925661f`. La branche feature possède désormais les huit commits F06 validés. La branche principale n'a pas été modifiée.
- **R04 implémenté sur la branche feature uniquement** : AudioIn PS5 ouvre un `SilentInputStream` qui produit un vrai tableau de samples à zéro, `main.cpp` route les sessions AudioIn vers l'adaptateur, `devices_check.cpp` vérifie les tailles et les échantillons. Le destructeur natif RomFS détache les chaînes `sibling/child/file`; `romfs_check.cpp` teste 32768 voisins fichiers puis répertoires sur pile de 256 KiB.
- **Preuve complémentaire source-extracted** : `tools/check-feature-r04-native-boundary-host.py`, compile les corps *exacts* du C++ AudioIn et RomFS avec UBSan, en `-O0` et `-O2`. Ne remplace pas le test intégré `eden-romfs-check` ou `eden-devices-check`.
- **Première exécution réelle** : le test source-extracted AudioIn/RomFS est passé sur [GitHub Actions #40237741910](https://github.com/niakw/Prospero.Eden-Encore/actions/runs/40237741910), job `source-extracted-native-r04`. L'audit de cohérence a ensuite signalé qu'il comparait encore RomFS à l'ancienne version. Le contrôleur `tools/check-vendor-consolidation-debt.py` a été **adapté pour vérifier exactement la nouvelle destruction non récursive** ; correctif natif non désactivé.
- **Validation non anticipée** : les contrôles de propriété de sources, la prévalidation complète, CodeQL et la compilation PS5 sont en cours de requalification sur le nouveau SHA. R04 n'est pas considéré terminé avant les résultats correspondants.
- **F07** : toujours réservé au test de base FC27 sur `cd4857c8`, sans ces changements.

### Première livraison de code (25 octobre 2026)

- **R00** : synchronisation base de référence F01–F06 de `dev/ps5-sparse-jit` dans la branche laboratoire [PR #18](https://github.com/niakw/Prospero.Eden-Encore/pull/18).
- **R04** : AudioIn produit des échantillons silencieux à longueur demandée ; RomFS libère des arbres très larges sans chaîne de destruction récursive ; tests source-extracted `-O0`/`-O2` et audit de source réussis.
- **R03 shader** : nouvelle unité entière `vendor/encore-active/eden-shader/src/shader_recompiler/backend/spirv/emit_spirv_context_get_set.cpp`, sélection unique par `headless/CMakeLists.txt`, sortie NaN flottante remplacée par zéro. Pinned Eden conservé ; autres sorties non modifiées. Contrat V109, revue du registre 329 sources, tests [Feature Lab](https://github.com/niakw/Prospero.Eden-Encore/actions/runs/40239451247) verts.
- **R03 RADV intégré dans la branche feature** : extension de la séparation des commandes PS5 avant barrières et six fonctions de transferts, modification de `radv_cmd_buffer.c` et deux unités maintenues `radv_meta_buffer.c` / `radv_meta_copy.c`. `tools/install-vendored-radv.py` installe **14 sources** vérifiées, `tools/patch-radv-wsi.py --oracle` reconstruit leur contenu depuis le Mesa épinglé, contrôle de propriété et de cache via `tools/check-vendored-radv-fork.py`. GPU réel et résistance aux pertes de périphérique encore **non prouvés**.
- **Validation native** : build PS5 et prévalidation intégrale requis avant de qualifier R03/R04 ; pas de test utilisateur demandé. Aucun moteur NR/FSR FG/LDN réel ajouté dans ce lot.

### Compatibilité avec les anciennes validations FC27

- Le nouveau header `headless/frame_metrics.h` exige que les harnais extrayant les fonctions Vulkan incluent également la vraie source. Les tests F03/F05 `check-fc27-f03-native-present-freshness-host.py`, `check-native-vulkan-renderer-handoff-host.py` et `check-fc27-f05-native-nvdisp-vulkan-present-chain-host.py` chargent maintenant l'en-tête réel, sans masquer les nouveaux appels.
- Le contrôle de provenance `tools/check-vendored-vulkan-fork.py` reproduit **exactement** les cinq événements du renderer et l'événement PresentManager dans la copie jetable de l'oracle Vulkan puis compare **les fichiers entiers**, sans réduire les assertions.
- Une prévalidation incomplète ou un build bloqué par ces contrôles ne prouve aucune régression de gameplay et ne clôt aucun jalon ; publication native et test PS5 séparés.


## Porte de sortie : qui fait quoi et quand on teste

**Assistant publie un paquet de preuves avant toute demande de test** :
- SHA stable + liste exacte des fichiers modifiés + état des conflits avec F01–F06 ;
- build PS5 + CI fast/full + CodeQL + tests host propres à chaque fonctionnalité ;
- modifications visuelles documentées et paramètres de rollback ;
- journal technique : correctifs validés, refusés, raisons, et **compteurs « reste à intégrer » distincts de « reste à qualifier »**.

**Utilisateur ne teste la console qu'à trois points utiles** :
1. **F07 baseline** : FC27 avec `dev/ps5-sparse-jit` code validé `cd4857c8`, enregistrer jeu/firmware/réglages, freeze/HUD/texture/frametime/input ; cela ne valide aucune feature branch.
2. **RC Graphics** : version native stabilisée de R03/R06/R07/R08/R09, A/B en conditions identiques, qualité/cadence/manette/HUD.
3. **RC fonctionnalités** : R11–R17 et R21 réunis (R21 seulement si installateur/asset release qualifiés), puis test deux instances pour LDN et trophées réels par jeux pilotes.

Pas de durée chiffrée inventée : la fin d'une phase dépend de ses **preuves** et de la disponibilité réelle des outils/hardware.

## Compteur de référence et limites de la roadmap (historique du 25 au 28 octobre)

- **F01–F06 pré-console** : 6/6 prouvés sur tests host, build PS5 et sécurité GitHub sur `cd4857c8`.
- **F07** : demeure ouvert ; sa situation actuelle se lit d'abord dans `docs/FC27_F07_MASTER_TRACKER.md` sur la branche console, et pas dans le SHA historique cité ici.
- **Branche feature** : audit en cours, `framegen_capabilities.h` (contrat de choix, pas moteur), catalogues de trophées vides + tests CI hôtes ; pas de FG/NR/FSR temporel/LDN natif intégré.
- **R00–R23** : les sept tableaux de catégories couvrent **24 jalons distincts** (pas 24/24 validations). Les jalons R22/R23 restent des études ; les statuts d'implémentation et les preuves des autres jalons sont suivis séparément. Le présent document n'accorde aucune qualification console.
