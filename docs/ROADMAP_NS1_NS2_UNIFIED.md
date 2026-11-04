# Eden Encore — roadmap suivable pour un moteur PS5 commun NS1 / NS2

**Mise à jour : 2026-11-04 · branche unique : `main`**

> **Suivi vivant à cases cochables : [GitHub Issue #15 — ROADMAP](https://github.com/niakw/ProsperoEden-Encore/issues/15)**
> **Audit technique et preuves de boot : [GitHub Issue #14](https://github.com/niakw/ProsperoEden-Encore/issues/14)**
> **Réconciliation des cases ouvertes (04/11) : [audit source/hôte](NS1_NS2_ROADMAP_RECONCILIATION_2026-11-04.md)**
> Le document présent explique les dépendances et critères de sortie; c'est l'issue #15 qu'il faut mettre à jour après chaque lot.

## Objectif et règles

Une seule application PS5 et un seul socle de moteur Vulkan, CPU/JIT, HLE, cache shaders, cache textures, buffer cache, ordonnanceur, services communs et UI. Les détails intrinsèquement différents (instructions Maxwell/Ampere, descripteurs QMD, capacités GPU, fréquences, services et formats firmware) sont sélectionnés automatiquement et vérifiés; **aucun réglage « expérimental » dans le profil final**. Cela ne signifie pas supprimer les contrôles de sécurité ni prétendre qu'une instruction Ampere est du Maxwell.

**Verrou P5 imposé par le propriétaire : aucun build PS5 et aucun test console avant l'entrée formelle en P5, après traitement des jalons P0 à P4.** Jusqu'à cette frontière, seuls les changements source, contrôles Clang/GCC, tests host, analyses de parité et previews hors console sont permis. Les workflows natifs restent désactivés; leur réactivation et la qualification de vrais jeux requièrent une autorisation explicite en P5. Aucun jalon P0-P4 ne doit être maintenu artificiellement ouvert parce qu'il manque un essai console réservé à P5.

## État technique vérifié au départ

| Domaine | État au 02/11/2026 | Limite de la preuve |
| --- | --- | --- |
| Moteur NS1 | Base fonctionnelle historiquement sur BOTW; FC27 a encore crashs/saccades et HUD à contrôler | Pas de succès FC27 vérifié pour le nouveau code |
| Boot NS2 | Parsing, TitleID, chemins extraits, capacités, partie HLE en place | MKW/Bananza restent sans première image invitée confirmée |
| GPU buffers communs | SSBO array walker unique NS1/NS2 avec 32 slots, générateur et vendor cohérents | CI hôte du dernier SHA à confirmer; textures Ampere non terminées |
| Compute NS2 | Capture QMD3 → SPIR-V → VkComputePipeline buffer-only; LRU natif borné à 12 avec vie GPU protégée (source/hôte) | Images TIC/TSC Vulkan, global memory, CBUF indirect et qualification PS5 manquants |
| GPU 3D NS2 | Sous-composants Ampere / MME présents | Rendu réel, task/mesh, stages et synchronisation non prouvés |
| Mémoire et VRAM | GMMU, NVMap, sparse/ASTC et contrôles hôte partiels | Résidence physique 12 GiB et premières images sur PS5 non prouvées |
| HLE / synchronisation | Nombreux services et correctifs IPC, VI2, scheduler | Pas de chemin complet invités → VI2 → frame certifié |
| UI et jaquettes | Index LaunchBox Switch 2, cache fronts/backs/spines, opacité et conservation d'inventaire corrigés; preview hôte verte | Jaquettes réellement récupérées sur console et transition GL→Vulkan sans flash à valider |
| Release | Builds natifs verrouillés | Pas de qualification console de cette révision |

## Séquence des jalons

| Ordre | Jalon | Livrable observable | Déblocage |
| --- | --- | --- | --- |
| **P0** | CI, propriété des sources et dé-expérimentalisation | Tous tests obligatoires verts au même SHA, inventaire des `EDEN_NS2_*_EXPERIMENTAL` + plan de promotion/suppression | Précondition à tout nouveau port moteur |
| **P1** | Boot / mémoire / HLE communs | Progression du PC invité traçable, 49-bit GMMU, NVMap/rollback, IPC exact, addons/keys/firmwares flexibles | Entrée GPU authentifiée et stable |
| **P2** | GPU Vulkan source/hôte partagé | TIC/TSC, texel-buffers et images, UBO/SSBO, caches, graphics/compute Ampere, ASTC/sparse/VRAM et synchronisations **dans le code** | Le premier framebuffer et les capacités du pilote réel sont qualifiés en P5; les instructions/stages non codés restent de vrais manques P2 |
| **P3** | UI / rendu partagé sans régression de source | Jaquettes, navigation sans rescan, chargement unique et transitions vérifiables sans PS5 | Récupération des jaquettes et FC27/BOTW réels réservés à P5 |
| **P4** | Préqualification strictement hôte | Contrats ciblés C++ Clang/GCC, mémoire/fences simulées, parité des sources et recette de release sans faux succès | Qualification de toutes les CI au dernier SHA faite à la frontière P5, sans bloquer le traitement du code |
| **P5** | Build PS5 contrôlé, qualification console et stabilisation | Autorisation explicite du build, puis MKW + Bananza première image invitée, FC27 match sans crash, BOTW, ressources et performances | Release seulement si critères console remplis |

Ces jalons ne sont **pas** des estimations de délais; chacun se ferme uniquement sur preuve. Un test de traduction shader, une preview OpenGL ou une compilation native réussie ne remplace pas une image issue du GPU invité.

## Points à suivre à chaque livraison

1. Commit **main** complet et commit **vendor** épinglé.
2. CI : `encore-core-fast-gate`, `encore-core-preflight`, `ns2-research-host`, `check-vendored-vulkan-fork`, `launcher render preview`. Lister tous les échecs restant et les skips explicites.
3. Preuves : **source intégrée**, **hôte validé**, **PS5 validé**, séparément.
4. Corrections génériques transférables aux deux générations, tests NS1/NS2 avant fermeture du jalon.
5. Prochain verrou en cause et actions exactes sans introduire de hack par TitleID.

## Références du premier point de contrôle

- Dernière révision stable de l'architecture SSBO partagée : [main `8df7bff`](https://github.com/niakw/ProsperoEden-Encore/commit/8df7bff70a7d23a3394544f9377e02836cd9c30a), [vendor `5612c96`](https://github.com/niakw/Prospero.Eden-Encore-vendor/commit/5612c96a6ce181186987e3fcb7ca291bfc6fd7c9).
- [Tests hôte NS2 #41433008853](https://github.com/niakw/ProsperoEden-Encore/actions/runs/41433008853) et [preview #41433008821](https://github.com/niakw/ProsperoEden-Encore/actions/runs/41433008821) : réussis pour cette révision; [core fast gate #41433008785](https://github.com/niakw/ProsperoEden-Encore/actions/runs/41433008785) : échec d'inventaire F07, **pas** un PASS moteur.
- Correctif de classement du composant loader hors inventaire historique : [`2963bea`](https://github.com/niakw/ProsperoEden-Encore/commit/2963bea8ad537cb56d92b9a876f9054684055d9f), [nouveau core gate #41434852822](https://github.com/niakw/ProsperoEden-Encore/actions/runs/41434852822) en cours lors de la création de ce document.

**Historique du 02/11 (non priorités courantes) :** P0.1, cartographie P0.3, TIC/TSC, mémoire et VI2 figuraient dans le plan initial. L'audit du 04/11 distingue désormais les parties source prouvées, les véritables manques d'implémentation et les validations console transférées à P5.

## P2.6a — Réutilisation native Compute revue (2026-11-02)

Le fournisseur Vulkan conserve désormais au plus **12 pipelines Compute Ampere** compilés sous leur propriétaire `PipelineCache`, avec clef comprenant **processus + génération du processus + époque du canal + hash et comparaison complète du SPIR-V**. Les dispatchs ont des `shared_ptr` indépendants retenus jusqu'au retrait GPU ; l'éviction LRU ne libère jamais une ressource encore retenue par une commande. Les shaders dépassant 65 536 mots SPIR-V restent sans cache. Les échecs de création ne sont jamais mémorisés, et une saturation mémoire du cache ne doit pas faire échouer un dispatch valide. Ce changement ne touche pas le cache Maxwell/NS1. Le générateur Vulkan est synchronisé avec les sources du vendor, sans supprimer la comparaison intégrale. **Qualification PS5 encore manquante.**

## Micro-jalons vérifiés sans build PS5 (2026-11-02)

- **P2.6a — hôte validé :** l'implémentation LRU Compute et le garde de provenance N56/U92 sont validés sur [`43f595b`](https://github.com/niakw/ProsperoEden-Encore/commit/43f595bd51f665f240e4cf17f29b56e34715ee63) / vendor [`32a0ac1`](https://github.com/niakw/Prospero.Eden-Encore-vendor/commit/32a0ac1bbdea56c5daa19c077c0bd6792844f935) par [NS2 host #41521143542](https://github.com/niakw/ProsperoEden-Encore/actions/runs/41521143542). La mesure NS1/NS2 et les essais GPU réels restent ouverts.
- **P3.4a/b — preview/source validées :** la navigation entre onglets conserve les derniers jeux et l'illustration. Les protections de volumes absents au premier scan sont intégrées ; [preview #41524761665](https://github.com/niakw/ProsperoEden-Encore/actions/runs/41524761665) verte sur `664b7f0`. L'indisponibilité d'un **fichier** (EIO, EACCES, ENODEV) ne doit plus cacher les autres titres : source [`f31a1bc`](https://github.com/niakw/ProsperoEden-Encore/commit/f31a1bc21c37977e977d34073c4de1509e5e71aa). Le témoin de refus exact en O0/O2 a été activé dans le preflight [`329b2b8`](https://github.com/niakw/ProsperoEden-Encore/commit/329b2b80d9b99bdb855f96b894fed32cfe092f06) ; résultats CI encore à qualifier sur ce SHA. P3.4 global attend toujours la console.
- **P4.2a — hôte validé :** nouveaux cas négatifs GMMU 49 bits, pages 4 KiB et translation physique disjointe [`155f633`](https://github.com/niakw/ProsperoEden-Encore/commit/155f633cb5b4ecce0115e3b5ad127dac48444bdf), [NS2 host #41525695461](https://github.com/niakw/ProsperoEden-Encore/actions/runs/41525695461) réussi en Clang/GCC. OOM GPU, fences et consoles restent ouverts.

**Dernier code observé lors de ce relevé :** parent `329b2b80d9b99bdb855f96b894fed32cfe092f06`, gitlink vendor `32a0ac1bbdea56c5daa19c077c0bd6792844f935`. Aucun build PS5 activé. Pour les statuts de CI et la checklist opposable, conserver l'[issue #15](https://github.com/niakw/ProsperoEden-Encore/issues/15) comme source vivante.


## Frontière P2.2b/P2.2c et verrou P5 — 2026-11-03

- **P2.2b (intégration source)** : l'acquisition réelle des vues TIC/TSC, des samplers et la rétention des ressources Vulkan doivent être cohérentes dans les deux variantes maintenues du cache commun. Les chemins NS1 et NUP ne doivent pas être modifiés pour déclarer le jalon terminé.
- **P2.2c (qualification avant P5)** : finir les cas positifs/négatifs Clang/GCC, les vérifications de provenance et d'ABI C++ avec ASTC/Vulkan, et obtenir les CI hôte pertinentes vertes au même couple SHA main/vendor. Une CI en file d'attente n'est pas une preuve.
- **P5 (qualification console uniquement après P0–P4)** : compilation native PS5 autorisée explicitement, installation, tests FC27/BOTW/MKW/Bananza, métriques GPU/CPU, première vraie image invitée et régressions console. Ces éléments ne sont **pas** des conditions de fermeture de P2.2c avant P5.
- **État de source à ce jalon** : l'interface native ASTC/Vulkan a été alignée au [vendor `d213ec7`](https://github.com/niakw/Prospero.Eden-Encore-vendor/commit/d213ec7630d7fb4f3e4795f711da4c8359ec544c), épinglé depuis [main `b7a7ebe`](https://github.com/niakw/ProsperoEden-Encore/commit/b7a7ebe88ed144081587a9336db6cf01d080a5a5), et les contrôles Clang/GCC ASTC-prioritaires sont ajoutés au [`34007d5`](https://github.com/niakw/ProsperoEden-Encore/commit/34007d5a8e92b92d349f34a338e613d08b4577cf). La [CI #41579773499](https://github.com/niakw/ProsperoEden-Encore/actions/runs/41579773499) était en attente lors du dernier contrôle; **P2.2b/P2.2c non encore fermés**.


## Répartition effective source ↔ console — décision du 4 novembre 2026

**Ne plus bloquer P0–P4 parce qu'un témoin exige une PS5.** Pour chaque jalon, cocher séparément « code présent », « vérifié sur hôte » et « qualifié sur console ». Un résultat PS5 absent ne réouvre pas une étape de source déjà réalisée; inversement, transférer un essai en P5 ne permet pas de qualifier une fonctionnalité **non implémentée**.

| Transféré en P5 (pas un blocage P0–P4) | Preuve attendue en P5 |
| --- | --- |
| Boot réel MKW/Bananza, progression PC invité, première commande écran | Journal console, progression CPU/GPU, vrai guest_frame_handoff non nul et image du jeu |
| Vulkan PS5 : capacité des formats, shaders/pipelines, texel views, timeline fences, ASTC/sparse et pression VRAM | Build instrumenté PS5 et capture du premier framebuffer, sans surface factice |
| NS1 FC27 (match, HUD, pauses/crashs), BOTW, régression entre jeux | Exécutions contrôlées sur PS5 et diagnostics de crash sans dégrader NS1 |
| UI réelle : jaquettes Switch 2, écrans de chargement, transitions sans flash, « Aucune ROM » | Tests console des assets, de la détection et de la transition GL/Vulkan |
| CI complète au même couple SHA et recette de packaging finale | Vérification de la provenance, des workflows et du paquet avant toute diffusion |

**Restes P0–P4 qui exigent du CODE (non requalifiables par un simple essai PS5)** :
la promotion des commutateurs de recherche vers la sélection automatique de production,
les instructions/stages graphiques Ampere encore explicitement refusés
(tessellation, task/mesh non pris en charge; géométrie liée au pipeline désormais intégrée en source avec opcodes inconnus refusés), les liaisons HLE ou
synchronisations non implémentées, et tout descripteur GPU dont l'ABI ne peut
être authentifiée. Ces manques se ferment seulement par une implémentation
générique contrôlée; aucun patch par TitleID et aucun faux « PASS ».

**P2.2 — extension source de ce lot :** les TIC 1D de texture-buffer et
image-buffer utilisent désormais les vues VkBufferView du **BufferCache
Vulkan commun** (y compris les descripteurs stockages lecture seule), avec
ordre de réflexion CBUF/SSBO/texel/images, GMMU 49 bits, revalidation
des snapshots TIC/TSC/physiques, usage de buffer suivi et marquage des
écritures reporté après l'admission finale. Les rendus NS1 et les sources
Maxwell restent sélectionnés séparément. Les limitations du pilote et la
rétention effective en conditions de charge sont à qualifier en **P5**.
Ce paragraphe est une preuve d'intégration source, pas un premier rendu PS5.

**P2.4 — Geometry (intégration source) :** un stage Ampere Geometry peut
maintenant être capturé et traduit dans la **pipeline Vulkan graphique complète**,
avec ses CBUF de stage 3 et la liaison inter-stage créée par le même
GraphicsPipeline commun. Seuls les opcodes déjà revus par le lowerer sont
acceptés; LEPC dynamique, tessellation et task/mesh restent refusés.
Cette prise en charge n'est **pas** une preuve de géométrie correcte sur PS5.
**P2.4 — relecture après compilation :** la création du pipeline graphique
réauthentifie désormais la configuration des stages, leurs offsets et les
instructions Ampere/branches CBUF d'origine **après** traduction CFG/IR/SPIR-V.
Un changement invité sans changement d'époque GPU refuse le pipeline avant
publication. La preuve de stabilité en conditions réelles reste en P5.

**P0.2 / P2.5 — N54 scratch CPU commun :**
Les allocations temporaires de swizzle/décode dépassant 64 MiB sont
libérées à la prochaine frontière `TickFrame()` pour les deux générations,
sans affecter les surfaces GPU ni le cache ordinaire de taille inférieure.
Le header unique `ScratchBuffer` conserve ses copies/redimensionnements.
La compilation du vrai `TickFrame()` extrait et les tests Clang/GCC avec
ASan/UBSan passent. Les performances et le comportement matériel PS5
restent P5 ; aucun mode expérimental ne commande cette politique.

**P0.2 / P1.1 — NPDM source commun N1 sélectionné automatiquement :**
Le parser maintenu reconnaît ACID 2048 bits (NS1) et 3072 bits (NS2)
à partir des octets réels, pour tous les profils natifs PS5.
`EDEN_NS2_METADATA_EXPERIMENTAL` est supprimé, mais aucun des chemins
ExeFS/A64/CPU6/HLE/GPU restant en recherche n'est activé pour autant.
Le vrai `ProgramMetadata::Load` a été compilé et exécuté sur Mac avec
Clang ASan/UBSan, en plus des témoins du helper O0/O2 ; fichiers valides,
ambigus et tronqués sont traités selon la politique NS1-conservatrice.
Tests des sélecteurs CMake recherche/release et du chemin renderer négatif
réussis ; aucun build PS5. Les 12 autres flags restent OFF par défaut.

**P2.5 / P0.2 — N57 + N60 intégrés au Vulkan PS5 commun (source/hôte) :**
Le décodage ASTC par layer et ses vues Vulkan (N57), puis la gestion
incrémentielle des layers sales avec staging/fences (N60), ne nécessitent
plus de flags de recherche : `video_core` et `core` sélectionnent les
mêmes headers ABI `ImageBase` depuis le fournisseur maintenu. Le chemin
original d'upload image complète reste la voie de secours si l'image n'a
pas toutes les propriétés admissibles (taille/layers/état/format). Aucune
variante spécifique à un jeu, aucun faux décodage et aucune fusion du fork
amont. N57/N59/N60 : contrats sources C++ Clang/GCC + UBSan passés ; N61 :
2 400 images simulées avec écritures/races/fallback. L'ASTC réel de
Bananza/MKW, le GPU RADV et les frames PS5 restent P5. Les modes sparse
expérimentaux et les ressources Compute non couvertes restent sous P2.

**P1.2 — correction du remap GMMU sans changement de statut :**
Le propriétaire partagé `MemoryManager` invalidait les caches texture/buffer
seulement quand la catégorie du PTE passait de `Mapped` à un autre état.
Un remap `Mapped → Mapped` vers un autre backing physique conservait donc
un cache potentiellement périmé. Les tables 4 KiB et big-page comparent
maintenant **l'ancienne page physique à la nouvelle avant remplacement**,
et appellent la même notification existante si le backing a changé, sans
notification supplémentaire pour une remap identique. Le chemin N51 de
coalescence optionnelle reçoit le même prédicat; aucune nouvelle file GPU.
Le test `check_native_gpu_pte_remap_host.py` extrait les vraies méthodes
C++ de production et valide NS1, NS2, N51 ON/OFF en Clang/GCC O0/O2,
ainsi que les transitions Mapped/Reserved/Free.
Le contrôle de parité retire *exactement* ces ajouts avant de vérifier
l'empreinte antérieure, et non en élargissant aveuglément la liste des hashes.
L'exécution GPU PS5 réelle est réservée à P5.

**P4.2b — témoins négatifs source/hôte revérifiés le 04/11 :**
[preuves détaillées et commandes testées](NS1_NS2_P4_HOST_NEGATIVE_EVIDENCE_2026-11-04.md).
GMMU/VRAM, NVMap, files VI2, fencing, descriptions Vulkan, mémoire dirty,
record de commandes et DMA ont passé les cas OOM/rollback ciblés sous
Clang/GCC O0/O2 lorsque le test le propose. Le témoin scheduler a retrouvé
sa compilation hôte grâce à l'inclusion C++ standard `initializer_list`.
La régression NS1 globale sur le SHA définitif et les vraies files GPU
restent respectivement P4.2 et P5 ; aucune CI PS5 n'est déclenchée.

**P3.3 — transition jaquette OpenGL → Vulkan qualifiée source/hôte le 04/11 :**
`check-ps5-vulkan-loading-stages-host.py` confirme la boîte aux lettres de
jaquette unique et bornée et l'absence d'effacement lors du passage Vulkan;
`check-native-vulkan-renderer-handoff-host.py` exécute les véritables
méthodes de rendu et de présentation sous Clang C++20 O0/O2 (241 frames),
avec l'ordre des notifications, la durée de vie des images et la queue de
présentation. `check-ps5-vulkan-present-frame-lifetime.py`,
`check-ps5-present-framebuffer-freshness-host.py`,
`check-vulkan-present-wait-host.py`,
`check-ps5-vulkan-swapchain-snapshot.py`,
`check-vulkan-present-missing-guest-host.py` et
`check-ps5-f07-present-layer-growth-host.py` passent également sur hôte.
Le test C++20 utilise uniquement pour cet hôte macOS la combinaison
libc++ headers CLT 26.5 / SDK de liaison 15.4, sans modifier le moteur.
**Pas de preuve d'absence de flash sur l'écran PS5 : P5.**

**P2.7c — source/hôte du fetch GPFIFO validée le 04/11 :** les deux
`DmaPusher` authentifient le canal NS2 et imposent `SafeRead` avant de lire
les mots invités, y compris sur pages physiques disjointes. Le cache Vulkan
rapatrie les buffers GPU modifiés et `scheduler.Finish()` assure l'ordre de
lecture CPU. Les fences GPFIFO restent obligatoires pour NS2, sans changer
leur politique NS1. Témoins hôte de 16 combinaisons, O0/O2 et Clang/GCC
passés. La première image, les vraies écritures GPU et les éventuels hazards
matériels restent des critères **P5**, jamais une preuve de boot réussie.

**Règle d'avancement :** ne pas relancer les mêmes batteries hôte à chaque
micro-correctif. Un contrôle ciblé vérifie la modification; les vérifications
exhaustives et les scénarios de jeux s'exécutent une seule fois au jalon P5
sur un SHA figé. Les tests console ne sont pas lancés ici.
