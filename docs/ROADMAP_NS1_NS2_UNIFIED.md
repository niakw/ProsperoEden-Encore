# Eden Encore — roadmap suivable pour un moteur PS5 commun NS1 / NS2

**Mise à jour : 2026-11-05 · branche unique : `main`**

> **Suivi vivant à cases cochables : [GitHub Issue #15 — ROADMAP](https://github.com/niakw/ProsperoEden-Encore/issues/15)**
> **Audit technique et preuves de boot : [GitHub Issue #14](https://github.com/niakw/ProsperoEden-Encore/issues/14)**
> **Réconciliation des cases ouvertes (04/11) : [audit source/hôte](NS1_NS2_ROADMAP_RECONCILIATION_2026-11-04.md)**
> Le document présent explique les dépendances et critères de sortie; c'est l'issue #15 qu'il faut mettre à jour après chaque lot.

## Objectif et règles

Une seule application PS5 et un seul socle de moteur Vulkan, CPU/JIT, HLE, cache shaders, cache textures, buffer cache, ordonnanceur, services communs et UI. Les détails intrinsèquement différents (instructions Maxwell/Ampere, descripteurs QMD, capacités GPU, fréquences, services et formats firmware) sont sélectionnés automatiquement et vérifiés; **aucun réglage « expérimental » dans le profil final**. Cela ne signifie pas supprimer les contrôles de sécurité ni prétendre qu'une instruction Ampere est du Maxwell.

**Règle corrigée le 5 novembre 2026 : aucune condition P5, DEV, expérimentation ou « release » ne sélectionne une autre application dans le code.** Le build natif PS5 unique peut être lancé **volontairement** depuis GitHub Actions (`workflow_dispatch` ou marqueur explicite `[full-build]` sur `main`). Une compilation n'autorise **jamais** à elle seule une publication : l'opérateur choisit séparément `publish`, et la sortie publique exige les critères P5 de validation console. Les tests source/hôte P0–P4 n'affirment ni premier rendu invité ni compatibilité des jeux. Les anciennes références à un « verrou P5 du build » plus bas dans l'historique sont obsolètes.

## Audit d’intégration du 5 novembre 2026 — P0 → P1 → P2 → P4

**Production / branches — actualisation du 5 novembre :** la
[PR #22](https://github.com/niakw/ProsperoEden-Encore/pull/22)
est **fusionnée sur `main`** par le commit `9a030641`.
Le moteur PS5 natif unique contient désormais les propriétaires NS1/NS2
NPDM/ExeFS, CPU/JIT, NVDRV, GPU session/VI2, Ampere et Vulkan/SPIR-V,
sans sélecteur de produit DEV, expérimental ou « release ».
NUP demeure inclus. Couple revu : `main a347fad7` /
vendor épinglé `ecb4d987`. Ce couple est **intégré, pas encore
qualifié dans toutes les CI** : Core fast gate réussi sur `b3455d6`,
tests historiques CodeQL, diagnostic de version, A64 et propriétaires
ExeFS remis en conformité dans les commits suivants ; Source preflight
et NS2 research host guards du dernier SHA restent à confirmer.
La preview launcher du merge `9a030641` a échoué sur une différence
de pixels nulle entre focus et zoom. Aucun framebuffer GPU invité ou
résultat console n’est démontré : **P0–P4 non clôturés globalement**.

- **P0.2 — raccordement source fusionné sur `main`, pas encore clôture du
  jalon dans l’issue #15 :** inventaires 337 sources vendored historiques,
  193 sources `headless` et 518 éléments de revue F07 réconciliés. Quatre
  unités NPDM/ExeFS ont été déplacées sans modification de contenu ; la
  politique JIT renommée dispose de nouveaux tests CPU6 bornés. Le vrai
  graphe natif NVDRV/GPU session/SPIR-V est vérifié par configure-only.
- **P1 — préqualification source/hôte partielle :** 32/32 témoins exécutés
  sur la copie de travail pour firmwares, NUP, CPU6, SVC, mémoire, NVDRV,
  audio/Sysmix, VFS. P1.3 demeure ouvert lorsque des IPC ou commandes
  matérielles restent sans implémentation fidèle ; pas de progression de PC
  invité prouvée sur console.
- **P1.3 — NVDRV `CloseSession` vérifié (source/hôte) :** le propriétaire
  `NvCore::Container` refuse une session hors plage, inactive, déjà libérée
  ou sans processus avant la décrémentation, le `NvMap::UnmapAllHandles`
  et la désinscription SMMU/ASID. Le chemin valide, le verrou existant et
  le `process->Close` différé restent inchangés. Le test compile le préambule
  C++ exact sous UBSan O0/O2 avec table `std::deque`, fermeture double et
  identifiants invalides. Vendor `ecb4d9877`, avec contrôle de reconstruction
  historique N07 complet. **N'affirme ni sécurité de concurrence globale
  `GetSession`, ni exécution PS5, ni fermeture complète de P1.3.**
- **P2 — état réel :** P2.3 CBUF/SSBO à formes dynamiques et P2.4 ISA/3D
  Ampere, task/mesh et instructions non couvertes restent ouverts. Une
  compilation de shaders et un test Vulkan hôte ne prouvent ni image ni
  synchronisation GPU réelle. Aucune fonctionnalité inconnue n’est remplacée
  par un succès fictif.
- **Reçu hôte vérifiable avant ce correctif :** 36/36 tests P4 à
  `main 8383d64a4b78b067f4b2e847ee8b3d212bbe643c` / vendor
  `a7790471c0544613cf59df8f5926f866d6a46560`, et 32/32 témoins P1
  sur le même couple de sources. Le générateur Vulkan a été remis en
  conformité avec les gardes PS5 uniques : 45 fichiers régénérés égaux aux
  propriétaires versionnés ; les additions P2.5 sont normalisées avec
  empreintes exactes pour conserver la preuve historique N57. Les quatre
  témoins CI Vulkan/ASTC/texture/selector font désormais partie de la
  qualification SHA-épinglée P4 ; celle du nouveau commit reste à effectuer.
- **P4 — requalification en cours :** l’ancien lot de tests cherchait les
  flags supprimés. Les tests conservent leurs témoins C++/UBSan, mais
  vérifient désormais le véritable CMake commun. **La fermeture exige un
  reçu `qualify_host_batch.py` sur le SHA commité du main et du vendor**, et
  pas seulement des succès locaux avec sources non commitées.

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
| Build / diffusion | Compilation native uniquement sur demande ; publication séparée | Pas de qualification console de cette révision |

## Séquence des jalons

| Ordre | Jalon | Livrable observable | Déblocage |
| --- | --- | --- | --- |
| **P0** | CI, propriété des sources et dé-expérimentalisation | Tous tests obligatoires verts au même SHA, inventaire des `EDEN_NS2_*_EXPERIMENTAL` + plan de promotion/suppression | Précondition à tout nouveau port moteur |
| **P1** | Boot / mémoire / HLE communs | Progression du PC invité traçable, 49-bit GMMU, NVMap/rollback, IPC exact, addons/keys/firmwares flexibles | Entrée GPU authentifiée et stable |
| **P2** | GPU Vulkan source/hôte partagé | TIC/TSC, texel-buffers et images, UBO/SSBO, caches, graphics/compute Ampere, ASTC/sparse/VRAM et synchronisations **dans le code** | Le premier framebuffer et les capacités du pilote réel sont qualifiés en P5; les instructions/stages non codés restent de vrais manques P2 |
| **P3** | UI / rendu partagé sans régression de source | Jaquettes, navigation sans rescan, chargement unique et transitions vérifiables sans PS5 | Récupération des jaquettes et FC27/BOTW réels réservés à P5 |
| **P4** | Préqualification strictement hôte | Contrats ciblés C++ Clang/GCC, mémoire/fences simulées, parité des sources et recette de release sans faux succès | Qualification de toutes les CI au dernier SHA faite à la frontière P5, sans bloquer le traitement du code |
| **P5** | Qualification console et stabilisation | MKW + Bananza première image invitée, FC27 match sans crash, BOTW, ressources et performances | Release seulement si critères console remplis, indépendamment de la compilation |

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
(task/mesh, LEPC en mode inconnu ou sans PC attesté et autres opcodes non traduits ; Geometry et la
paire TessControl/TessEval sont liées en source, sans preuve GPU PS5),
les liaisons HLE ou
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
acceptés ; LEPC sans provenance PC native vérifiée et task/mesh restent refusés.
Cette prise en charge n'est **pas** une preuve de géométrie correcte sur PS5.
**P2.4 — relecture après compilation :** la création du pipeline graphique
réauthentifie désormais la configuration des stages, leurs offsets et les
instructions Ampere/branches CBUF d'origine **après** traduction CFG/IR/SPIR-V.
Un changement invité sans changement d'époque GPU refuse le pipeline avant
publication. La preuve de stabilité en conditions réelles reste en P5.

**P2.4 — tessellation native liée (source/hôte, sans test console) :**
La paire **TessellationControl + TessellationEval** est maintenant admise
par le vrai pipeline graphique Vulkan commun, jamais par les compilateurs
SPIR-V autonomes. Un seul stage tessellation, ou un pipeline sans VertexB,
reste refusé avant la première lecture GPU. Les banques CBUF sont vérifiées
avec une même fonction : VertexA/B=0, TessControl=1, TessEval=2, Geometry=3,
Fragment=4. Les trois chemins (capture, construction, replay après compilation)
se réfèrent au même propriétaire; aucune fausse donnée CBUF. Source C++
hôte (Clang, politique de stages et ISA) et parité intégrale du fork Vulkan
testées ; les instructions Ampere non prises en charge restent bloquées.
**Cela n'établit pas le bon fonctionnement de la tessellation sur PS5** :
validation d'un véritable patch tessellé et des capacités RADV en P5.
Task/mesh et les usages LEPC non reconnus ou sans PC GMMU authentifié restent des manques de code P2.4.

**P2.2/P2.3 — handles de textures dynamiques avec sampler statique :**
Dans le planificateur natif QMD3, une texture échantillonnée à
`count > 1` pouvait fournir sa table TIC à un index dynamique mais
la seconde source CBUF (sampler constant) avançait également de
`index << size_shift`. Le propriétaire commun `TexturePass` encode
pourtant la source secondaire comme un **seul** mot statique dans
les formes `has_secondary` reconnues. Le planificateur NS2 conserve
désormais la banque et le mot de sampler identiques sur tous les éléments,
sans réinterpréter le handle comme un registre TIC NS1.
Test du vrai lecteur QMD3 : deux TIC distinctes, sampler partagé,
rejet des banques/offsets illégaux, détection de mutation d'une
entrée secondaire, Clang/GCC UBSan. Cela répare l'ABI d'admission
native, **pas encore toutes les détections IR de tableaux dynamiques**
(la prise en charge complète reste ouverte). Aucun code NS1 modifié.

**P2.4 — registres hauts Ampere, fusion sélective Lichii #65 :**
Les instructions déjà traduites pouvaient être refusées ou écraser les
registres temporaires Maxwell quand des GPRs élevés apparaissaient dans
LDG/STG, FFMA, FMUL, FADD/FSEL, I2FP, IMNMX, S2R et FSETP.
Le propriétaire Ampere `PrepareRegisterPressure` répertorie désormais
16 familles réellement traduites, dont FMUL registre 0x220 et leurs champs d'opérande exacts,
y compris la paire adresse 64 bits en mémoire globale, les tailles
vectorielles et le troisième opérande FFMA. Le détecteur du lowerer
reconnaît les vrais champs à bit 32 même hors mode générique.
Il copie les quartets de GPR vers une zone temporaire, exécute
l'instruction et restaure les registres d'origine. Les formes que
le lowerer ou le budget de registres ne peuvent représenter restent
refusées. Les tests Clang/GCC UBSan vérifient les champs immuables,
le rejet des vecteurs débordants et la traduction d'un LDG capturé.
**Ce correctif ne change ni Maxwell NS1 ni la limite console P5.**

**P2.2/P2.5 — copie Vulkan multirégion avec préservation du
stencil (05/11, source/hôte) :** le premier correctif avait
supprimé deux usages Vulkan incorrects : une région
VkBufferImageCopy ne peut porter DEPTH|STENCIL
simultanément (VUID-09103), et CopyBufferToImage doit
nommer le layout réellement établi par sa barrière,
ici TRANSFER_DST_OPTIMAL (VUID-00180).

Le contrôle suivant a identifié un défaut plus large :
MakeBufferImageCopy initialisait **tous** les bufferOffset
à zéro ; des copies multiples dans un même batch
écrasaient le même tampon temporaire. Le propriétaire
Vulkan PS5 répartit désormais chaque région dans un
**intervalle scratch distinct et aligné**, avec budget
calculé par couche, volume et format, vérification
des multiplications, de la limite d'allocation native
et de l'égalité exacte des octets des lignes source
et destination. Il refuse tout ratio qui aurait été
arrondi par troncature.

Pour les images Depth/Stencil combinées de **même
format**, il enregistre maintenant deux régions
Vulkan indépendantes par zone : un plan Depth et
un plan Stencil, séparés dans le tampon et couverts
par les barrières complètes. Cela évite la perte
systématique du stencil du correctif initial.
**Les réinterprétations entre formats Depth/Stencil
différents ou entre D/S et Color restent refusées**,
car leurs octets stencil n'ont pas de correspondance
prouvée. Le chemin desktop non PS5 n'est pas modifié.

Le vrai planificateur scratch du propriétaire est
extrait et exécuté sous Clang/GCC UBSan O0/O2 :
deux régions, D24S8/D32S8, deux plans séparés,
multicouches, offsets, ratio non entier, absence
de dépassement et cas négatifs. Les preuves F07
historiques coordonnées, tailles, layout et
générateur de portage restent vertes, avec aller-retour
des sept patches Vulkan épinglés.
**Aucune compilation GPU/PS5 ni préservation stencil
sur console encore validée** (P5).

**P2.2c — vraie compilation syntaxique du propriétaire Vulkan
(05/11, hôte, sans build PS5) :** contrairement aux oracles
extraits des anciennes sections F07, le nouveau contrôle
compile **le vrai fichier vk_texture_cache_cost.cpp**
avec les overlays actifs, en-têtes C++20 et dépendances
Vulkan/Boost/fmt/Sirit épinglées. Trois profils sont
vérifiés : desktop/NS1, PS5_NATIVE commun et interface
de recherche NS2 (ASTC/sparse/view, avec N72+N73
couplés conformément à la configuration). La variante
de recherche est **compilée seulement**, jamais activée
dans le profil release.

Sur Mac arm64, la compilation syntaxique utilise le
libc++ du SDK CLT 26.5 et un shim purement hôte pour
l'instruction pause x86 du fichier performance.h.
Aucune production n'est modifiée par ce shim, et aucun
objet/binaire ELF n'est produit. Les trois passes
Clang syntax-only réussissent, sans erreur, avec
l'avertissement historique nodiscard sur une fonction
void du dépôt amont. Les workflows host core source
et fast-gate référencent désormais cette vérification.
**Ce contrôle ferme le sous-objectif de compilation
du vrai owner**, pas l'ensemble P2.2c : parité
CI du même SHA, rendu Vulkan matériel et P5
restent à qualifier.

**P2.4 — LEPC avec PC GMMU dans les six stages graphiques
(05/11, source/hôte) :** le premier garde LEPC ne
transmettait l'adresse de code 64 bits qu'en Geometry.
Le même chemin de capture authentifie pourtant
chaque mot GPU invité pour VertexA, VertexB,
TessControl, TessEval, Geometry et Fragment.
Le constructeur d'image Maxwell vérifie maintenant
l'appartenance à ces six stages et reçoit leur PC
**seulement si le programme natif contient un vrai
opcode LEPC**. Compute, les IDs de stages inconnus,
les prédicats/champs LEPC non prouvés et l'adresse
GMMU absente continuent à être refusés.

Le cache de traduction conserve une identité
distincte pour deux programmes LEPC byte-identiques
à des adresses GPU différentes, et pour leurs
stages différents. En revanche, deux programmes
**sans** LEPC peuvent réutiliser la même traduction,
quelle que soit leur base GPU : pas de multiplication
injustifiée des shaders Vertex/Fragment. La capture
recontrôle toujours ses octets et son header après
la traduction et avant publication.

Tests source-exécutés du vrai CaptureNativeGraphicsShader,
BuildMaxwellShaderImage, LowerToMaxwell et du cache LRU :
six stages, deux VAs 64 bits, identités de stages,
refus Compute/inconnu, codes avec/sans LEPC,
capture source remappée, Clang/GCC UBSan O0/O2.
**Ce travail élargit l'admission LEPC source/hôte**,
mais ne valide ni la liaison inter-stage GPU,
ni les formes LEPC non reconnues, ni task/mesh
ou le premier rendu NS2 PS5 (P2.4/P5 ouverts).

**P2.4 — LEPC dynamique en Geometry avec provenance GMMU (05/11,
source/hôte) :** l'adresse d'une instruction LEPC hors du prologue
statique ne pouvait pas être reconstruite depuis les adresses
Maxwell traduites : les instructions Ampere ont 16 octets,
le code Maxwell utilise 8 octets et des mots d'ordonnancement.
Le chemin de capture graphique transmet maintenant
l'**adresse GPU invitée authentifiée de la première instruction
native** exclusivement au stage Geometry. Le lowerer LEPC
matérialise alors ses deux mots de PC 64 bits depuis cette
origine plus index × 16, avec validation de la plage GMMU
49 bits, du format ISA et des deux registres de destination.
Sans adresse réelle, hors Geometry, ou en mode de LEPC
non reconnu, la traduction reste refusée. Le prologue
ATEXIT vérifié antérieurement conserve sa compatibilité.

L'origine native parcourt le vrai pont d'ISA, l'image
Maxwell et le cache LRU ; l'identité de cache inclut désormais
l'adresse source **en plus des octets complets**, empêchant
de réutiliser la mauvaise constante PC pour deux shaders
identiques à des adresses GPU différentes. Les captures
GMMU sont recontrôlées sur chaque réutilisation ; les races
d'invalidation conservent leur garde d'époque.
**Tests hôte réels :** CaptureNativeGraphicsShader,
BuildMaxwellShaderImage, LowerReviewedToMaxwell, LowerToMaxwell,
GetOrTranslate, relecture GMMU, deux VAs 64 bits, LRU,
refus VertexB, LEPC prédicat illégal, registre haut,
GMMU hors plage et disparition de mapping, Clang/GCC UBSan
O0/O2 ; ancien cache et son test de race PASS. Aucune
modification de Maxwell/NS1 ni de Vulkan.
Cette avancée clôt la **voie LEPC Geometry avec PC attesté**,
pas les transferts de contrôle par adresses
calculées non prouvées, ni task/mesh, ni le premier
frame PS5 (P2.4/P5 ouverts).

**P2.4 — REDUX warp signé et XOR (05/11, source/hôte) :**
le lowerer Ampere reconnaît désormais les modes de réduction
REDUX.MIN.S32, REDUX.MAX.S32 et REDUX.XOR.U32
en plus des modes de somme, OR, minimum et maximum non signés.
Pour le tri signé, chaque valeur active est transformée par
XOR du bit de signe, le minimum/maximum est effectué sur les
entiers ainsi ordonnés, puis le bit de signe est restauré
au résultat. Les masques de lanes inactives restent appliqués
avant la réduction ; les modes signés d'addition/OR/XOR
et les champs inconnus continuent à être refusés.
La source GPR du REDUX est désormais enregistrée dans
PrepareRegisterPressure, pour éviter de lire les registres
temporaires de l'émulation U.

Tests du **vrai LowerToMaxwell** et de son spilleur :
7 modes valides, 2 modes d'ordre signé (32 bascules de
lane + restauration), XOR distinct du OR, source GPR
haute avec copie/restauration, huit modes invalides,
Clang/GCC UBSan O0/O2. Maxwell NS1 n'est pas modifié.
La preuve d'exécution de shaders sur GPU PS5 reste P5.

**P2.4 — RED global natif, réduction 32 bits et adresse sûre
(05/11, source/hôte) :** le lowerer Ampere ne repérait pas la
vraie source GPR à bit 32 de RED 0x98e et ne protégeait pas
sa paire d'adresse 64 bits (bits 24–31) lorsque l'un des
registres traversait la limite des scratch Maxwell.
La forme avec pointeur uniforme n'activait pas non plus
systématiquement la réservation du banc U. Désormais les
deux modes utilisent le **spill/restauration des vrais GPR**,
rejettent les paires non contiguës et interdisent U62/U63
comme faux pointeur 64 bits.

La réduction 32 bits reconnaît les types entier non signé
et signé, et les offsets natifs signés de 24 bits ne sont
émis comme immédiats Maxwell de 20 bits **que si** la
valeur entière tient dans la plage -0x80000 à 0x7ffff.
Les modes inconnus et les offsets tronquables sont refusés.
Aucun contournement propre à un jeu ni modification Maxwell
NS1. Tests du vrai lowerer et de PrepareRegisterPressure :
haut GPR et uniforme, copie/restauration exacte, 20
encodages de décalages/type, refus sous/débordement et
pointeurs irréguliers, Clang/GCC O0/O2 UBSan.
**Pas d'exécution Vulkan/PS5 prouvée : P2.4/P5 restent ouverts.**

**P2.4 — atomiques globaux Ampere et préservation des GPR hauts (04/11,
source/hôte) :** deux opérations natives ATOMG U32 déjà reconnues
pouvaient malgré tout corrompre les résultats. Pour l'adresse GPR
0x3a8, le spill ne déclarait ni la destination/valeur ni la paire
d'adresse 64 bits ; pour le pointeur uniforme 0x9a8, le lowerer ne
reconnaissait pas le véritable registre de valeur au bit 32 et le
traitait comme le scratch Maxwell. PrepareRegisterPressure protège
désormais les vraies sources et destinations, préserve la contiguïté
de la paire GPR et restaure tous les quartets empruntés, même à la
limite de l'espace scratch. Le pointeur uniforme U62 est refusé :
son mot supérieur U63 est le registre zéro, **pas** un voisin GPR
valide à lire comme la seconde moitié d'une adresse 64 bits.

Témoins C++ exécutant les vrais PrepareRegisterPressure et
LowerToMaxwell des deux formes (18 familles de registres hauts au
total) : mot atomique Maxwell, copie/restauration exacte, séparation
des registres de données et d'adresse, refus sans spill autorisé,
pointeurs pairs/impairs et U62/U63, UBSan Clang/GCC. Pas de
contournement par titre, ni modification du compilateur Maxwell NS1.
L'accès global atomique via un SSBO dont la provenance n'est pas
authentifiée reste **un manque P2.3 distinct** ; les GPU physiques PS5
et les shaders complets restent à qualifier en P5.

**P2.4 — F2F.F16.F32 avec les quatre sources natives (06/11, source/hôte) :**
La conversion canonique F32→F16 conserve la forme GPR `0x304` et prend
désormais en charge les formes immédiate 32 bits `0x904`, CBUF `0xb04` et
uniforme `0xd04` dans le même lowerer Maxwell : `F2F` registre (`0x5ca8`)
ou sa version CBUF directe (`0x4ca8`). Le NaN et le signe négatif conservent
leur représentation IEEE-754 complète dans le GPR intermédiaire ; les UR
passent par le banc réservé et les banques CBUF sont contrôlées 0–17 avec
alignement octet. Les modes F2F non examinés restent rejetés ; aucun
changement du frontend NS1 ni d'exception par titre.
Validation sur le vrai `LowerReviewedToMaxwell` : 0, +1, −1, NaN,
CBUF 0 et 17, UR bas/haut/63, refus des adresses et UR invalides.
Hôte Clang/GCC O0/O2 UBSan ; la validation PS5 reste P5.

**P2.4 — sources immédiates et uniformes FRND/F2I (06/11, source/hôte) :**
Le lowerer Ampere commun traite désormais `FRND.F32` avec un immédiat 32 bits
(`0x907`) ou une source uniforme (`0xd07`), et `F2I` avec immédiat 32 bits
(`0x905`), par le même backend Maxwell que les formes registre/CBUF déjà
admises. Les constantes sont matérialisées **bit à bit** dans un GPR, sans
conversion par le CPU hôte ; leur bit de signe n'est jamais interprété
comme un modificateur `abs` ou `neg`. Les UR 0–62 et UR63=RZ utilisent
la réservation du banc partagé, avec refus des collisions GPR et champs
de format non reconnus. Le moteur NS1 n'est pas modifié.
Validation `check_ampere_scalar_alu_sources_host.py` sur le vrai
`LowerReviewedToMaxwell` : 0, +1, −1 et NaN pour FRND/F2I, UR bas/hauts/63,
cas de rejet ; **Clang/GCC UBSan O0/O2, 4/4 PASS**. P2.4 reste ouvert
pour les familles ISA et stages non implémentés ; test PS5 en P5.

**P2.4 — FLO multi-sources (06/11, source/hôte) :**
L'instruction de recherche du bit de tête `FLO` ajoute les formes immédiate
32 bits (`0x900`) et CBUF (`0xb00`) aux variantes GPR et UR existantes.
Le vrai lowerer conserve le mot signé complet, les bits de mode FLO et la
lecture de banque CBUF vérifiée (0–17, offset aligné). Le bit 31 d'un
littéral n'est pas le drapeau d'inversion de la forme registre.
Tests d'admission ISA et de mots Maxwell, positifs et refus, dans la suite
unifiée `check_ampere_scalar_alu_sources_host.py` Clang/GCC UBSan O0/O2.
Pas d'adaptation par jeu ni de rendu PS5 prouvé ; P2.4 reste ouvert.

**P2.4 — BREV/POPC multi-sources et IABS immédiat (06/11, source/hôte) :**
Le lowerer commun traduit désormais les formes nouvelles `BREV` immédiat
32 bits (`0x901`), CBUF (`0xb01`) et uniforme (`0xd01`), et `POPC`
immédiat (`0x909`) et CBUF (`0xb09`), aux côtés des variantes GPR/uniforme
existantes. `IABS.S32` admet également son immédiat complet (`0x813`),
y compris `INT32_MIN` sans conversion via l'`abs()` hôte.
Les accès CBUF réutilisent la lecture Maxwell exacte de banque et offset
alignés, avec bornage du banc 0–17 ; les UR restent soumis au banc réservé
partagé. Pour POPC immédiat, le bit 31 du littéral reste une **donnée**,
jamais le bit d'inversion de la forme registre. Les champs/modes non prouvés
sont rejetés avant émission. Aucun hack par jeu et aucun changement NS1.
Témoin réel `check_ampere_scalar_alu_sources_host.py` : admission ISA,
`LowerReviewedToMaxwell`, mots BREV/POPC/IABS Maxwell, sources entières
et erreurs de mode/CBUF/UR ; **Clang/GCC UBSan O0/O2, 4/4 PASS**.
Ce lot augmente la couverture fonctionnelle mais **ne clôt pas P2.4** ni la
validation console.

**P2.4 — plage complète de capture shader Ampere (06/11, source/hôte) :**
Le plafond de **65536 instructions** du compilateur est maintenant commun
au bridge `LowerReviewedToMaxwell`, au lecteur GMMU `CaptureNativeShader`,
à la validation de `MaxwellShaderImage`, au cache de traductions et à
l'authentification des branches indirectes CBUF. L'ancienne limite de 4096
interdisait des shaders légitimes avant traduction. La taille Maxwell reste
bornée à 131072 mots et le cache reste borné par son budget mémoire.
La capture n'alloue que 4096 instructions initialement et grandit au besoin,
sans réserver systématiquement 1 MiB pour les petits shaders. Les pages GMMU,
les CBUF des BRX et les octets Compute sont toujours revalidés avant de publier
l'image et avant le dispatch.
Le prologue `StaticAtExitTarget` reconnaît une cible future alignée dès
ses cinq premiers mots (même au-delà de 4096), afin que le lecteur GMMU
poursuive réellement la capture ; le lowering `BMOV 0x357` exige ensuite
la présence de cette cible dans le code effectivement authentifié.
Le témoin `test_native_shader_texture_semantics.cpp` valide cette distinction
et la conservation du handler ATEXIT historique. Témoins du vrai moteur :
`test_ampere_lower_bridge.cpp` (4097 acceptées, 65537 refusées),
`test_ampere_gpu_capture.cpp` (4097 instructions Compute, replay jusqu'au
dernier octet, refus sans EXIT à 65536 et BRX 4097 authentifié) et
`test_ampere_translation_cache.cpp` (entrée de 4097 instructions réutilisée
sans fausse collision). **Apple Clang O1 : PASS** pour ces témoins ; la
qualification GCC/Linux des derniers commits reste à établir en CI.
**P2.4 reste ouvert** pour les opcodes/chemins task/mesh et LEPC non prouvés,
et pour la validation GPU console. Aucune modification du compilateur NS1.

**P2.4 — audit Lichii/nx2 du 04/11, correctifs ISA génériques :**
l'authentification ISA puis la traduction vers Maxwell admettent désormais
USHF 0x499 (mot immédiat et shift uniforme), BRA.U 0x947 (bits de mode distincts de l'offset signé), SULD/SUST 0x998/0x99c
(handles en registre, images 2D/array/3D), SURED 0x59f (réduction 1D buffer
ou 2D) et IMNMX 0x817 (immédiats signés et 32 bits). Aucun chemin n'est
sélectionné par titre ou ROM. Les champs non prouvés et les ressources non
admissibles restent refusés avant l'envoi à Vulkan.
Tests du vrai décodeur et du vrai lowerer Clang/GCC UBSan verts, négatifs
inclus ; l'ancienne suite du bridge passe et le fork Vulkan reste inchangé.
[Revue différenciée des commits nx2](NS2_LICHII_NX2_DIFF_AUDIT_2026-11-04.md) :
les optimisations de GpuSplit, les fences amont annulées et les services
HLE sans propriétaire correspondant ne sont pas fusionnés aveuglément.
Le GPU matériel et les shader pipelines complets ne sont qualifiés qu'en P5.

**P2.4 — prédicats uniformes Ampere protégés (04/11, source/hôte) :**
le lowerer natif `UISETP` (formes registre et immédiat `0x28c/0x88c`)
sauvegardait et restaurait auparavant **les sept lanes UP0–UP6**,
y compris celles qu'il ne lisait ni n'écrivait. Cela pouvait écraser
l'état des prédicats uniformes d'instructions voisines. La traduction
Maxwell utilise désormais uniquement le masque du prédicat de résultat
et, lorsque présent, du prédicat d'accumulation ; le cas `UPT` ne crée
plus de masque fantôme. Le raccourci `USEL` vers un clamp entier
(`0x887`) exige maintenant **la condition canonique zéro**, plutôt que
de transformer une sélection d'une autre condition en simple min/max.
Aucune forme de shader ou de titre spécifique ajoutée.

Régression exécutée directement sur `LowerToMaxwell` réel :
UISETP immédiat/registre × accumulation réelle/PT, contrôle des masques
P2R/R2P, refus d'un prédicat de sortie interdit, puis `USEL`
canonique et conditions non nulles (renvoyées au chemin général).
Compilation/exécution Mac Apple Clang O0/O2 avec UBSan, plus tests
d'ISA/BRX, capture du shader et lot des correctifs génériques nx2
réussis. Le compilateur Maxwell NS1, la file Vulkan et les sélecteurs
de recherche ne sont pas modifiés. L'exécution des shaders sur GPU
PS5, task/mesh et LEPC non reconnu ou sans PC attesté restent
**non prouvés**.

**P2.3 — écritures globales Compute NS2 sans lecture globale (source/hôte) :**
Le collecteur NVN commun ne construit ses descripteurs globaux que lorsque
`uses_global_memory` est vrai. Un shader qui écrit seulement dans la
mémoire globale (`stores_global_memory`) pouvait donc être accepté comme
plan QMD mais rester sans aucun SSBO dans le compilateur SPIR-V.
Le bridge Compute Ampere normalise désormais ce cas **avant** la compilation,
uniquement lorsque la banque CBUF0 existe réellement et est activée en QMD,
et que les bits de buffers NVN forment un préfixe contigu sans autre
descripteur ambigu. Les enregistrements restent à l'ABI NVN réelle
CBUF0 + 0x310 + index × 16 ; leur taille et leur mapping sont toujours
lus puis authentifiés par le propriétaire QMD3. Aucun accès à une adresse
non mappée, aucune taille SSBO supposée, aucune modification Maxwell/NS1.
Tests Clang/GCC UBSan du vrai IR CBUF et de l'environnement QMD3,
y compris refus des masques incomplets, trous, banques absentes et collisions.
Le témoin réel de validation avant marquage GPU-dirty couvre désormais
les **SSBO et texel buffers** sans régression de transaction.
**Ce résultat ne valide pas l'exécution GPU PS5**, reportée à P5.

**P2.3 — index de tableau par extraction de champ
binaire non signé (05/11, source/hôte) :**
le backend SPIR-V partagé émet
OpBitFieldUExtract(base, offset, count). Lorsque
les deux paramètres de champ sont de **vrais
U32 immédiats**, avec offset dans [0,31],
count dans [1,32-offset] et aucune condition
d'indice variable, le résultat appartient
nécessairement à [0,2^count-1]. Le collecteur
d'atomiques Compute natif démontre alors
l'alignement d'un éventuel décalage gauche
constant et l'absence de perte de bits en U32.
Il peut accepter une unique base constante
alignée, contrôlée contre le débordement.
Le maximum plus la largeur atomique est
authentifié sur la taille réelle du SSBO QMD3
et sa VA GPU de 49 bits avant publication.

Les paramètres d'extraction dynamiques,
count nul, offset + count hors 32 bits,
shift variable, somme débordante ou
alignement insuffisant sont refusés.
**Tests hôte :** vrais blocs IR
GetRegister→BitFieldUExtract→ShiftLeftLogical32
→IAdd32→StorageAtomic, tailles de buffers
juste suffisantes/insuffisantes, extraction
à l'extrémité du registre, cas négatifs,
Clang/GCC UBSan O0/O2. Aucun patch du
backend SPIR-V commun, aucun patch NS1,
et **aucune exécution GPU PS5 revendiquée**.
P2.3 global/P5 restent ouverts.

**P2.3 — index atomique de tableau avec décalage gauche
constant (05/11, source/hôte) :** les expressions
d'index en éléments (registre AND masque) << shift
sont désormais authentifiables quand l'IR contient
exactement BitwiseAnd32 suivi de ShiftLeftLogical32
avec un décalage **immédiat de 0 à 31**. Le compilateur
prouve que le masque ne perd aucun bit sur 32 bits,
que le résultat est aligné sur la largeur atomique
(4 ou 8 octets) pour **toutes** les valeurs du registre,
puis calcule sa borne supérieure exacte. Une base
constante alignée peut suivre, avec le même contrôle
de somme sans débordement que P2.3j.

Cela couvre le cas générique de tableaux de
32/64-bit indexés en unités d'élément, sans
confondre offset invité et offset de stockage SPIR-V.
La borne supérieure est vérifiée sur les **octets
réels du SSBO QMD3**, avec adresse GPU de base alignée
et span dans la plage GMMU de 49 bits. L'offset
dynamique d'origine est toujours celui émis par
l'IR du shader.

Les décalages dynamiques, décalages >=32, masques
qui perdraient des bits, sous-alignement,
index SSBO inconnus et additions supplémentaires
non bornées restent refusés. Témoin du vrai IR
GetRegister → AND → ShiftLeftLogical32 → IAdd32
→ StorageAtomic, Clang/GCC UBSan O0/O2,
cas positifs/négatifs, tailles QMD3 insuffisantes,
compilation des vrais propriétaires et garde-fous
de sélection NS1/NS2. **Ce n'est pas une
validation GPU ni la clôture intégrale de P2.3/P5.**

**P2.3 — accès atomiques base + (index AND masque) et base
GMMU alignée (05/11, source/hôte) :** nouvelle forme
décodable depuis l'IR Compute réel :
IAdd32(BitwiseAnd32(registre, masque_constant),
base_constante), avec permutation des opérandes des
deux opérations et identités SSA. Le masque doit
conserver les bits bas à zéro selon les 4/8 octets
de l'atomique, et la base doit être alignée.
Le compilateur démontre en 32 bits **sans
débordement** que l'offset final appartient à
[base, base + masque] ; il authentifie sa valeur
maximum plus la largeur contre le SSBO QMD3
capturé avant de publier le shader. Le shader
SPIR-V conserve l'expression dynamique réelle,
sans transformer le maximum en index d'écriture.

La même validation vérifie désormais que l'adresse
GMMU **de base** du SSBO est alignée pour la
largeur atomique et que le span complet tient dans
la plage GPU native de 49 bits. Les offsets seuls
alignés sur une base incorrecte ne sont plus
qualifiés à tort. Refus conservés sur additions
dynamiques supplémentaires, bases/masques
sous-alignés, sommes 32 bits débordantes, index
SSBO dynamiques, formes U32x2 non atomiques
et absence de résidence/mapping prouvé.

Tests du vrai IR GetRegister/BitwiseAnd32/IAdd32,
plusieurs masques et bases, deux ordres de
constantes, négatifs et mutations de tailles,
validation de la base GPU, Clang/GCC UBSan O0/O2,
compilation syntaxique des propriétaires
Compute et garde-fous NS1/NS2. Le modèle
de preuve est conservateur, pas un émulateur
d'atomiques illimités. **P2.3 global et P5
restent ouverts ; pas de validation PS5.**

**P2.3 — offsets atomiques dynamiques bornés par masque AND
(05/11, source/hôte) :** l'absence de garde SPIR-V
dans le backend commun imposait jusque-là le refus de
**tous** les offsets SSBO dynamiques. Pour les formes
exactes BitwiseAnd32(registre, masque_const),
le code post-traduction peut toutefois démontrer
**sans supposition** que chaque offset envoyé au SPIR-V
est compris entre zéro et la valeur du masque, et
que ses bits bas garantissent un alignement de 4 ou
8 octets. Le collecteur de l'IR natif conserve donc
le **maximum prouvé**, puis le propriétaire QMD3
compare ce maximum plus la largeur exacte à la
longueur réelle du SSBO au moment du plan de
ressources. Un buffer trop court fait échouer la
publication du shader. La preuve fonctionne pour les
deux ordres du AND et les identités IR, sans rajouter
de voie au compilateur Maxwell NS1.

Les additions non bornées, PHI, masques mal alignés,
masques débordants, index de liaison SSBO dynamiques et
fallbacks atomiques U32x2 restent **refusés**.
L'émetteur de stockage conserve le **même offset
réel** : il n'utilise pas la borne pour calculer
les écritures, seulement pour vérifier le plan
QMD3. Tests du vrai IR Compute avec registre R12,
AND 32/64 bits, bords de buffer, mutation du
descripteur, positives et négatives, UBSan
Clang/GCC O0/O2 ; tests de syntaxe propriétaires
et garde-fous NS1/NS2. Les offsets dynamiques
arbitraires nécessitent toujours le vrai prédicat
SPIR-V ou une autre preuve complète.
**Aucune instruction GPU PS5 n'a été exécutée :
P2.3 global/P5 ouverts.**

**P2.3 — correspondance stricte SSBO ↔ descripteur CBUF/NVN
(05/11, source/hôte) :** un masque CBUF actif ne suffit pas à
authentifier la provenance d'une écriture atomique. Le garde
du vrai bridge Compute exige maintenant également un
descripteur CBUF qui **couvre réellement** la banque
matérielle, une taille réfléchie suffisante pour le
record NVN de 16 octets, et la correspondance exacte
entre l'indice SSBO aplati et l'enregistrement
NVN base + 16 × slot. Une métadonnée décalée,
un slot inversé ou un descripteur absent conduisent à
un **refus**, jamais à un atomique dans un autre buffer.

Témoin source-exécuté avec le vrai IR du compilateur :
cas positifs et négatifs, banques sans descripteur,
tailles absentes, base NVN incorrecte, deux slots
corrects puis inversés, Clang/GCC. Le chemin Maxwell
NS1 n'est pas modifié. Le test hôte vérifie la
provenance statique mais ne démontre **pas** la
résidence GPU de l'adresse atomique dynamique,
ni le premier rendu NS2 sur PS5 : P2.3/P5
restent ouverts.

**P2.3 — vérification des plages atomiques contre le buffer QMD3
réel (05/11, source/hôte) :** l'authentification de l'emplacement SSBO
ne prouvait pas que chaque offset atomique serait présent dans les
**octets effectivement alloués** au moment où le QMD3 publie son
plan de ressources. Le nouveau passage natif capture, depuis
l'IR réel, la banque SSBO aplatie, l'offset et la largeur de chaque
StorageAtomic (4/8 octets), puis refuse les offsets atomiques
dynamiques non bornés tant que l'émetteur SPIR-V partagé ne
possède pas de garde de plage exécutable. Le cas du
masque AND aligné prouvé est ajouté ci-dessus. À la sortie de BuildResourcePlan, le
chemin GPU QMD3 compare chaque plage constante à la taille réelle
lue depuis son descripteur guest et refuse **avant publication**
tout dépassement, buffer non inscriptible, taille inconnue, alias
ou décalage non aligné. Aucun accès hors plage ne peut être
sécurisé en le ramenant au premier mot du buffer.

Preuve hôte : extraction des vrais Opcode/IR::Block, tests d'offsets
4/8 octets, bords extrêmes u32, descripteurs réduits ou modifiés,
offsets dynamiques et absence de taille ; Clang/GCC UBSan O0/O2 ;
compilation syntaxique O0/O2 des deux vrais propriétaires
renderer_spirv_bridge.cpp et ns2_shader_spirv_compile.cpp.
**Les atomiques dynamiques arbitraires ne sont pas implémentés** :
ils sont refusés, sauf la forme AND alignée et bornée ajoutée
ci-dessus, sans imiter une exécution réussie.
Il n'y a toujours pas de preuve Vulkan/PS5 ni de chemin Maxwell NS1
modifié.

**P2.3 — admission des atomiques Compute sous véritable SSBO
(04/11, source/hôte) :** le compilateur NS2 Compute passe désormais
le vrai IR post-traduction par une vérification *avant* l'émission
SPIR-V. Un GlobalAtomic dont le pointeur invité n'a pas pu être
relié à une liaison SSBO ne peut plus atteindre le backend comme
une opération exécutable : refus explicite de compilation.
Les StorageAtomic conservés doivent référencer un emplacement
immédiat présent parmi les descripteurs QMD3 reflétés, activé dans
NVN, inscriptible, soutenu par une véritable banque CBUF et un
enregistrement de descripteur aligné. Les décalages statiques ne
peuvent pas être arrondis à un mot voisin : alignement 4 octets
pour les opérations 32 bits, 8 pour les opérations 64 bits.

La voie commune SPIR-V substitue parfois des lectures/écritures
**non atomiques** aux StorageAtomic 64 bits si Vulkan n'expose pas
les atomiques 64 bits, et le repli U32x2 est toujours non atomique.
NS2 refuse désormais ces formes plutôt que de prétendre les avoir
exécutées atomiquement. Les vrais atomiques 64 bits exigent
support_int64, support_int64_atomics et support_descriptor_aliasing.
Le code Maxwell NS1 reste inchangé.

**Preuve :** tests IR C++ créant de vraies instructions GlobalAtomic
et StorageAtomic, avec positifs/négatifs sur registres de liaison,
propriétaires CBUF, drapeaux d'écriture, décalages, capacités 64 bits
et repli U32x2 ; Clang/GCC UBSan hôte ; compilation syntaxique du
propriétaire renderer_spirv_bridge.cpp O0/O2 sur headers épinglés.
Cette admission valide les métadonnées et les instructions, **pas**
la résidence de chaque pointeur atomique dynamique à l'exécution.
Le contrôle effectif de l'adresse/du buffer dans un dispatch Vulkan,
les indexations dynamiques et les opérations non prouvées demeurent
ouverts en P2.3/P5. Aucun GPU PS5 testé.

**P2.3 — U32x2 CBUF entre vecteurs SPIR-V voisins (04/11,
source/hôte) :** les accès de 64 bits Ampere en CBUF ne peuvent
pas être correctement représentés en arrondissant simplement
le décalage invité au multiple de huit. Un U32x2 à 4, 12 ou
0xfff4 doit lire deux mots voisins, alors que la voie Vulkan à
aliasing de descripteurs chargeait jusqu'ici une seule paire U32x2
arrondie. Le backend natif assemble maintenant les mots à partir
de **deux vecteurs U32x2 voisins** (8 octets chacun) quand
l'aliasing est disponible, et de deux vecteurs U32x4 voisins
(16 octets) lorsqu'il ne l'est pas. Les indices d'éléments sont
ramenés à leur vecteur réel, sans extraction du composant 2/4
hors plage. La réflexion statique compte jusqu'au dernier mot de
l'accès, puis arrondit à l'alignement de 16 octets : à offset 12,
la présence de 32 octets est requise plutôt que 16.

Le contrôle natif conserve la plage totale de **8 octets invités**
et un alignement minimal **4 octets**. Les offsets non alignés
au mot et les lectures traversant la fin des 64 Kio ne sont pas
émulés : ils sont refusés à l'admission QMD3 (statique) ou
ramenés à zéro par le garde SPIR-V (dynamique). Les chargements
U8/U16/U32 et le chemin Maxwell/NS1 ne changent pas.

Tests : compilation syntaxique du vrai TU SPIR-V O0/O2 avec ses
headers épinglés ; oracle C++/UBSan Clang/GCC O0/O2 comparant
**tous les mots alignés sur 4 octets** des deux chemins de
vecteurs à la paire de mots attendue, y compris offsets
4, 8, 12, 0xfff4, 0xfff8 et refus 0xfffc ;
admission IR QMD3 réelle et fenêtre complète de 64 Kio
pour les offsets dynamiques ; fixture QMD3 entière
compilée et exécutée sur hôte.
**Ce n'est pas une preuve d'exécution GPU Vulkan/PS5** :
les pointeurs atomiques SSBO non authentifiés et les autres
formes CBUF indirectes restent ouverts en P2.3.

**P2.3 — accès dynamiques CBUF : largeur d'origine et traversée des lignes SPIR-V
(04/11, source/hôte) :** le backend CBUF Ampere vérifie désormais la
**plage d'octets invités entière**, avant de convertir le décalage en
index SPIR-V arrondi. Auparavant une lecture U32x2 (8 octets) depuis
0xfffc pouvait être relue à tort comme le dernier vecteur valide
0xfff8–0xffff ; les lectures de 1/2/4 octets ont maintenant également
leur vrai seuil, même si le compilateur émet une lecture U32x4 alignée.
Les décalages invalides sont envoyés vers le sélecteur d'index invalide
des CBUF dynamiques QMD3, ou le pointeur sûr suivi du zéro côté banque
immédiate. Il n'y a ni alias vers une autre banque ni adresse modulo 64 Kio.

Lorsque Vulkan ne permet pas l'aliasing de descripteurs, une lecture
**U32x2** traversant la limite interne d'une ligne U32x4 de 16 octets
sélectionne maintenant la ligne suivante pour son second mot et
ramène l'index de composant dans [0,3] : une extraction du composant 4
ne pouvait pas représenter correctement ce cas. Les voies NS1 sont
byte-for-byte inchangées quand la portée Ampere n'est pas activée.
Validation : parsing C++20 des sources réelles du backend SPIR-V sous
O0/O2 avec headers épinglés, oracle sémantique compilé et exécuté UBSan
O0/O2 (4 largeurs, limites 0xfff8/0xfffc/0xffff, franchissements de
lignes), plus gardes directs QMD3 et CBUF graphiques. Pas de pipeline
Vulkan complet ni de GPU matériel PS5 validé ; les CBUF indirects
hors formes connues et pointeurs atomiques restent ouverts.

**P2.3 — boucles CAS F32x2 à stockage atomique U32 (06/11, source/hôte) :**
Les trois opérateurs `f32x2_add/min/max_cas` du propriétaire SPIR-V
maintenu utilisent désormais le type mémoire `U32[1]` correspondant à
l'élément SSBO, avec une valeur de calcul `F32[2]`. Leur lecture est un
`OpLoad` U32 puis `OpUnpackHalf2x16`; la recomposition passe par
`OpPackHalf2x16` et un seul `OpAtomicCompareExchange` U32. Les versions
précédentes passaient `F32[2]` comme type mémoire pour un pointeur U32,
ce qui pouvait invalider le module. Le contrôle source inspecte les six
boucles float2 et le propriétaire CMake réel ; la compilation hôte et
`spirv-val` de modules générés restent des preuves distinctes. NS1 intact.

**P2.3 — correction du backend CAS SPIR-V F16x2 (06/11, source/hôte) :**
La source SPIR-V maintenue `spirv_emit_context.cpp` passe maintenant le type
mémoire **U32[1]** aux trois boucles CAS `f16x2_add/min/max_cas`, sans
modifier leur type d'opérande mathématique **F16[2]**. Leurs pointeurs de
storage sont des éléments U32 et `OpAtomicCompareExchange` compare et écrit
un **seul mot de 32 bits**. L'ancien `F16[2]` comme type de chargement et
de comparaison ne correspondait pas au pointeur et pouvait produire un
SPIR-V non valide. Le bitcast s'effectue seulement autour de l'opération
mathématique, tandis que la lecture/écriture et le résultat atomique
conservent une représentation 32 bits. Les trois variantes utilisent le
même propriétaire actif `vendor`, épinglé par CMake ; le backend NS1 n'est
pas modifié. Le contrôle `check_shared_ns2_spirv_compiler_host.py` vérifie
ce contrat et compile la vraie unité C++ ; la validation d'un module
produit via `spirv-val` et l'exécution console restent distinctes.

**P2.3 — atomiques flottantes authentifiées avec CAS réel (06/11, source/hôte) :**
Le backend commun possède déjà des boucles atomiques comparées-échangées
(`CAS`) SPIR-V pour `StorageAtomicAddF32`, ainsi que les six variantes
add/min/max `StorageAtomic*F16x2` et `StorageAtomic*F32x2` : **sept formes**
flottantes au total. Le convertisseur natif QMD3 raccorde désormais les sept
variantes `GlobalAtomic*` correspondantes
**uniquement lorsque leur pointeur est relié à un vrai slot SSBO writable**.
La valeur flottante F32 est conservée avec son type et sa représentation ;
le F16x2 empaqueté reste U32. Les variantes F32x2 sont converties par
`OpPackHalf2x16`/`OpUnpackHalf2x16` de la boucle CAS existante, qui met à jour
**un seul mot atomique de 32 bits**, pas une écriture 64 bits non protégée.
Les offsets sont authentifiés à 4 octets, comme ceux du backend effectif.
Les adresses arbitraires restent refusées. Aucune hypothèse sur un jeu particulier,
aucun fallback en écriture non atomique, aucun changement NS1.
`test_native_qmd_direct_cbuf.cpp` vérifie les sept opcodes sur de vrais
blocs IR, les opérandes F32 et F32x2, les spans atomiques et les offsets
immédiats/dynamiques. La chaîne de validation va jusqu'au plan de liaison
GMMU réel (`NativeQmdAtomicSpansFitBindings`) : refus d'un SSBO raccourci
d'un octet, en lecture seule, sans taille certaine ou à base mal alignée,
y compris pour le second slot. L'IR conserve aussi le retour de l'opération
atomique lorsqu'un calcul invité dépend de sa valeur précédente. Cette validation hôte n'est pas un dispatch Vulkan PS5.

**P2.3 — reconstruction des pointeurs atomiques CBUF scalaires (06/11, source/hôte) :**
Le traducteur accepte désormais les deux représentations exactes de l'adresse
SSBO QMD3 : `PackUint2x32(GetCbufU32x2)` et
`PackUint2x32(CompositeConstructU32x2(GetCbufU32(low),GetCbufU32(high)))`.
La seconde forme doit lire les octets contigus `base` et `base+4` **dans la
même banque** ; une seconde lecture différente ou un dépassement U32 est
refusé. Le calcul `IAdd64` accepte le descripteur à gauche ou à droite,
avec un décalage U64 constant ou un `ConvertU64U32` d'offset dynamique
préalablement borné et aligné. Les deux parcours utilisent exactement les
mêmes preuves de liaison SSBO réelle, de plage d'accès atomique et de
capacités Vulkan. Une table NVN à plusieurs SSBO conserve l'index du
**slot aplati** : l'entrée n° 1 à CBUF0+0x320 n'est jamais confondue avec
la n° 0 à CBUF0+0x310, et une table permutée est rejetée.
Suite IR réelle `check_native_qmd_direct_cbuf_host.py` : deux mots CBUF,
calcul commutatif, masque dynamique, second slot, adresses décalées ou
non contiguës et refus d'adressages arbitraires. P2.3 n'est pas clos :
les accès atomiques non liés à un pointeur QMD3 prouvé restent refusés,
et aucun framebuffer PS5 n'est revendiqué.

**P2.3 — atomiques Global→Storage depuis pointeur QMD3 authentifié (06/11, source/hôte) :**
Le compilateur Compute NS2 utilise désormais `NativeAtomic::Rewrite` après
`ConvertLegacyToGeneric` et le normaliseur CBUF QMD3. Les atomiques 32 bits
dont l'adresse provient d'un **vrai `GetCbufU32x2` QMD3**, empaqueté
`PackUint2x32` et éventuellement augmenté d'un décalage U64 constant,
sont réécrites en `StorageAtomic*32`; les opérations 64 bits
(`IAdd/SMin/UMin/SMax/UMax/And/Or/Xor/Exchange`) utilisent les vraies
`StorageAtomic*64` du backend SPIR-V avec les capacités `int64_atomics`
et `descriptor_aliasing` obligatoires. Aucun fallback non atomique n'est
accepté. Les sorties conservent l'index SSBO réel et l'offset
byte exact. Aucune adresse globale arbitraire n'est traitée comme un SSBO.
L'admission exige : banque CBUF réellement déclarée, descripteur SSBO
writable, utilisé, unique, au bon rang `nvn_buffer_base + slot*16` et
intégralement couvert par la taille CBUF reflétée ; l'offset de 32 bits
est aligné et sans débordement. Les offsets **dynamiques** sont également
admis lorsqu'ils proviennent de `ConvertU64U32` (zéro-extension) d'un
`BitwiseAnd32`/extraction/shift authentifié et borné par le collecteur
`NativeQmdAtomicMaximumByteOffset` ; la taille réelle de la ressource
reste contrôlée par le plan de dispatch Vulkan. `CollectNativeQmdAtomicSpans` et le plan
GPU Vulkan contrôlent ensuite la plage complète contre la taille et l'VA
GMMU réellement liées. Les opérations/pointeurs non prouvés restent refusés.
Témoin réel `test_native_qmd_direct_cbuf.cpp` : conversion des IAdd/Exchange,
refus des banques, slots inversés, décalages non alignés ou U64 débordants,
descripteurs absents/lecture seule et pointeurs dynamiques non authentifiés.
Clang/GCC UBSan PASS, **sans preuve d'exécution PS5**. Le frontend NS1 reste
inchangé. P2.3 est encore ouvert pour les adressages dynamiques généraux.

**P2.3 — largeur des opérandes IR Compute native (06/11, source/hôte) :**
Le normaliseur Ampere `GetCbuf` admet uniquement un index de banque U32 et un
offset octet U32, qu'ils soient immédiats ou construits à partir d'un registre.
Les anciens appels `Value::U32()` sur un immédiat U64 pouvaient provoquer
une exception pendant le lancement Compute. Le garde opère avant la lecture
de l'immédiat dans les deux modes : CBUF direct (8 banques QMD3) et
remappage indirect (14 banques Maxwell vers les 8 bancs QMD3).
La même règle refuse les offsets atomiques SSBO calculés en U64, même lorsqu'ils
ne sont **pas** immédiats : le chemin SPIR-V aval attend un index U32.
Témoin IR réel `test_native_qmd_direct_cbuf.cpp` : GetCbuf U8/U32/U32x2,
bank U64, offset U64 immédiat et offset U64 dynamique, et StorageAtomic IAdd32/
IAdd64 avec offset U64 dynamique ; Clang/GCC sous UBSan PASS. **Le P2.3 global
reste ouvert**, et aucun rendu GPU PS5 n'a été mesuré. Le moteur NS1 reste inchangé.

**P2.3 — accès complets SSBO globaux (source/hôte, 04/11) :**
Le backend SPIR-V partagé NVN vérifiait seulement
`base <= addr < base + size` avant chaque `OpAccessChain`. Un chargement,
stockage ou atomique global de 8/16 octets pouvait donc franchir la
frontière de la mémoire authentifiée ; une adresse non alignée était
tronquée vers le précédent élément. Le propriétaire d'émission **NS2
uniquement**, pendant `NativeSpirvCbufBoundsScope`, impose désormais
`size >= largeur`, `addr >= base`,
`addr - base <= size - largeur`, et l'alignement de l'offset.
Ces tests ont lieu avant la création du pointeur SPIR-V ; le chemin
Maxwell/NS1 conserve sa condition historique inchangée.
Tests de limites 49 bits et 4/8/16 octets exécutés avec le vrai IR QMD3,
contrôle structurel de l'émetteur et compilation syntaxique réelle de
`spirv_emit_context.cpp` Clang/GCC. Aucun shader GPU PS5 revendiqué.

**P1.2 — garde de durée de vie GMMU native 4 KiB
(05/11, source/hôte) :** le chemin NVDRV natif
de recherche possédait des opérations de map,
unmap, réserve sparse et modification PTE
qui vérifiaient vm.initialised mais pas
l'existence du propriétaire gmmu.
Cinq méthodes exigent maintenant les deux
sous le mutex d'address space AVANT tout
pin NvMap, allocation VA, mise à jour
d'adresse ou dé-référencement du GMMU ;
MapNativeImage et RemapNativeSparse avaient
déjà le garde complet. Le test hôte vérifie
les sept propriétaires et l'ordre admission
puis effets, puis la suite de plages GPU
49 bits compilée et exécutée sous Clang/GCC
ASan+UBSan O0/O2. La source NVDRV 4 KiB
reste isolée aux sessions de recherche NS2,
sans bascule du pilote NS1 en production.
Ce lot ne rend pas GPFIFO/Compute disponible
sur console : validation du vrai runtime P5.

**P1.2 / P1.3 — remaps NVDRV bornés et sans fuite de pin :**
Deux recherches de réservations GPU dans `nvhost_as_gpu` décrémentaient
`upper_bound()` même à `begin()` : une table vide ou une adresse avant
la première allocation déclenchait un comportement indéfini.
Le propriétaire NS2 utilise désormais une recherche commune bornée à
49 bits, avec vérification du sous-intervalle et des tailles sans overflow.
Dans MapBufferEx, les contrôles de destination sont exécutés avant
PinHandle ; un échec d'allocation après pin effectue aussi UnpinHandle.
Les remaps partiels hors du mapping et les longueurs nulles sont refusés.
Le test hôte Clang/GCC O0/O2 sous ASan/UBSan valide les recherches
contre un oracle linéaire et les chemins exacts de l'ioctl.
Qualification de mémoire GPU physique PS5 conservée en P5.

**P1.2 / N51 — invalidation GPU avant remapping physique :**
Dans le chemin N51, les notifications précédentes étaient émises après la
mutation du backing physique. Les caches GPU-dirty pouvaient alors évacuer
des données vers la nouvelle page plutôt que vers l'ancienne.
Le propriétaire GMMU commun notifie maintenant les pages modifiées avant
de remplacer toute PTE (4 Kio et big pages), avec ou sans coalescence.
Le test C++ extrait les deux méthodes réelles, observe les vieilles PTE
pendant les callbacks et couvre Clang/GCC O0/O2, N51 activé/désactivé,
Mapped→Mapped et les transitions d'état. Le replay inverse exact retrouve
le blob vendor précédent ; preuve GPU sur PS5 conservée en P5.

**P0.2 / P1.2 — N51 notifications des pages GPU regroupées :**
La source partagée P1.2 identifie les vraies pages modifiées, y compris
un nouveau backing physique sur un PTE encore mappé. La protection N51
regroupe uniquement leurs notifications adjacentes, préserve les trous
et bloque les débordements. Le témoin du `MemoryManager` vérifie les
méthodes `PageTableOp`/`BigPageTableOp` sous Clang/GCC, O0/O2, avec
et sans N51 ; l'oracle indépendant exécute 2 000 patrons aléatoires
par granularité et un run de 380 108 pages. Aucun changement des
caches ou du dispatch rasterizer NS1, qualification PS5 conservée en P5.

**P0.2 / P2.5 — N54 scratch CPU commun :**
Les allocations temporaires de swizzle/décode dépassant 64 MiB sont
libérées à la prochaine frontière `TickFrame()` pour les deux générations,
sans affecter les surfaces GPU ni le cache ordinaire de taille inférieure.
Le header unique `ScratchBuffer` conserve ses copies/redimensionnements.
La compilation du vrai `TickFrame()` extrait et les tests Clang/GCC avec
ASan/UBSan passent. Les performances et le comportement matériel PS5
restent P5 ; aucun mode expérimental ne commande cette politique.

**P4.1 — qualification hôte accélérée, figée au couple SHA :
** une commande locale unique de tests vérifiés
(tools/ns2/qualify_host_batch.py) exécute en parallèle,
avec un plafond de 3 travaux par défaut, 17 témoins
pertinents pour les sélecteurs source/release,
Ampere, QMD3/CUBF/atomiques, SPIR-V, Sysmix/audio,
Vulkan et l'inventaire historique NS1.
Le mode smoke ne relance que 6 gardes rapides
lors de petites modifications. Le runner
vérifie que main et le gitlink vendor pointent
au même commit qu'au début et à la fin,
refuse les arbres de code suivis modifiés
et écrit un reçu JSON sous .build-local,
**sans CI ni compilation console**.
Ce dispositif réduit les reprises redondantes ;
il ne constitue **pas** la matrice P0–P4
exhaustive ni une preuve d'une frame PS5.

**P2.7/P1.2 — lot natif GPFIFO et mémoire sparse (05/11, source/hôte) :**
le vrai owner NVDRV natif vérifie dorénavant les drapeaux et
la quantité des fences QMD AVANT toute initialisation GPU
ou liaison au registre de processus, puis rejette un FD
étranger sans initialiser le canal. La réservation des
syncpoints natifs se base exactement sur
NativeSubmissionPlan::increment_total et non sur
une seconde recomposition indépendante. Le chemin
NVDRV Maxwell/NS1 conserve son admission et son
calcul historiques. Le témoin extrait le préfixe
C++ réellement compilé de SubmitGPFIFOImpl et prouve
les refus de flags invalides, de 65 incréments,
de FD étranger ou expiré, sans effet sur canal,
et accepte 64 incréments (66 avec la fence normale).
Clang/GCC O0/O2 UBSan : PASS.

En parallèle, le propriétaire commun
SparseLargeVector::DecommitPage utilise
maintenant un nombre de pages std::size_t
plutôt que de comparer une expression u64
avec un std::size_t incompatible sur macOS
ARM64. Les gardes de parité historique et
les tests de remise à zéro/sparse passent,
et le fichier réel nvhost_gpu.cpp a passé
la compilation syntaxique Clang C++20 avec
ses vrais en-têtes maintenus. Cette correction
est commune NS1/NS2 et n'active aucun GPU.
**Qualification PS5 matérielle et GPU/GPFIFO
dans la release restent ouvertes** en P0.2/P5.

**P0.2b — compilation partagée du shader SPIR-V NS2
(05/11, source/hôte) :** les propriétaires du
compilateur GPU Ampere déjà existants sont
désormais inclus dans le graphe source
du profil PS5 final : frontend Ampere
(progression précédente), bridge SPIR-V
graphics/Compute QMD3, et les deux TUs
d'émission SPIR-V CBUF/globale avec les
contrôles natifs. CMake remplace exactement
les deux sources SPIR-V épinglées,
sans compiler deux symboles concurrents.
La configuration desktop garde les TUs
Maxwell d'origine.

**Protection NS1 :** pour une émission
Maxwell sans NativeSpirvCbufBoundsScope,
le bloc complet du sélecteur indirect à
14 banques est strictement identique
à celui du vendor Eden épinglé, et
indépendant de la présence ou non de
banques dans un masque partiel. La voie
NS2 utilise le scope thread-local
uniquement quand le caller réel du
bridge l'établit ; elle conserve les
refus des CBUF et accès GPU non prouvés.

**Preuves :** deux configurations CMake
réelles de graphes de cibles factices
release/native et desktop (aucun build
PS5), quatre vraies unités C++20
Clang syntax-only, contrat d'identité
du CBUF Maxwell d'origine, tests CBUF
native et garde-fous source.
**Ne signifie pas GPU rendu actif :**
GPFIFO/NVDRV 4 KiB, GPU Session, dispatch
Vulkan et scène invitée attendent le
raccordement et la qualification P5.
P0.2/P2.3 globaux restent ouverts.

**P0.2/P2.3 — 32 SSBO Compute NS2 sans modifier
l'ABI du cache NS1 (05/11, vrai propriétaire source/hôte) :**
le chemin Compute natif possède déjà un plan
QMD3 vectorisé allant jusqu'à 32 SSBO, puis
ComputePipeline::ConfigureNative les achemine
en ordre de réflexion par StageVulkanBufferBindings
vers le propriétaire BufferCache::ObtainBuffer
et les descripteurs Vulkan réels. Il n'appelle
pas BindComputeStorageBuffer de Kepler/NS1,
dont le tableau dans BufferCacheChannelInfo
reste volontairement limité à 16.
Modifier cet en-tête pour élargir l'ABI commune
serait une régression inutile à ce stade.
Le test du vrai NativeQmdComputeEnvironment
construit et lit 32 enregistrements CBUF
QMD3 de 16 octets, authentifie les 32 plages
GMMU puis vérifie l'ordre des 32 liaisons
du vrai StageVulkanBufferBindings : index 16
et 31 inclus. Il refuse la 33e entrée,
la corruption d'un plan détaché, le
démapping du seul dernier SSBO avant
tout staging et le refus de la dernière
liaison avec rollback exactement une fois.
Tests Clang/GCC O0/O2 UBSan sur Mac, guard
source démontrant le vrai appel ObtainBuffer
et l'absence du chemin Kepler.
**P2.3/P0.2 globaux ouverts** : ce test
ne démontre ni les shaders graphiques à
32 SSBO ni le dispatch GPU PS5, et
n'active aucun runtime expérimental.

**P0.2 — coeur Ampere intégré à la compilation du produit
commun (05/11, source/hôte) :** sélection automatique du
frontend natif lors d'un profil PS5 final avec NPDM
commun et Vulkan, sans activer les neuf options
EXPERIMENTAL. Les huit vraies unités de compilation
Ampere (capture GMMU, code 128 bits, lowering Maxwell,
environnement, pont IR et cache) sont indépendantes
de l'overlay de cache NS2. Cette séparation est
essentielle : le header de cache recherché modifie
à la fois 16→32 emplacements SSBO et les signatures
de fonctions C++ ; il ne doit jamais entrer dans
la construction NS1 sans propriétaire d'implémentation
complet et preuve ABI. Seul le header IR corrigeant
Generic31Y/Z/W est sélectionné depuis l'overlay,
sans changer les layouts des buffers.

**Preuves :** sélecteur CMake réel exécuté sur cinq
combinaisons (release/desktop/NPDM/Vulkan), syntaxe
Clang C++20 des huit unités de traduction sous
en-têtes Eden épinglés, contrôles source/production.
Ce lot Ampere n'activait aucun GPU. Le compilateur
SPIR-V est ensuite promu séparément en P0.2b,
mais la GPU session, GPFIFO, NVDRV et le dispatch
restent des dépendances ouvertes
et la première image NS2 reste P5.

**P0.2 — décision sur les modes de recherche (04/11) :**
L'ancien Graphics Scale AM command 60 renvoyait une valeur de résolution
prototype sans source d'état écran et sans événement 1050. Il était
inutilisé par le programme distribué : option, override du proxy,
quatre sources vendor et faux test de réussite supprimés. La commande
AM 320 commune et le proxy original restent inchangés.
De même, N72 sparse-queue n'avait aucun consommateur indépendant
de N73 sparse-cache. N72 est donc désormais activé automatiquement
avec l'unique option de recherche N73 : impossible de construire
un demi-chemin sparse. **9 options restent, toutes OFF par défaut**.
Chacune conserve un vrai propriétaire de code sélectionnable ; cela
ne valide ni leur activation automatique ni le rendu NS2 PS5.
Les contrôles hôte vérifient la liste exacte, les dépendances,
les options obsolètes refusées et le verrou final release/P5.

**P0.2 / P1.1 — NPDM source commun N1 sélectionné automatiquement :**
Le parser maintenu reconnaît ACID 2048 bits (NS1) et 3072 bits (NS2)
à partir des octets réels, pour tous les profils natifs PS5.
`EDEN_NS2_METADATA_EXPERIMENTAL` est supprimé, mais aucun des chemins
ExeFS/A64/CPU6/HLE/GPU restant en recherche n'est activé pour autant.
Le vrai `ProgramMetadata::Load` a été compilé et exécuté sur Mac avec
Clang ASan/UBSan, en plus des témoins du helper O0/O2 ; fichiers valides,
ambigus et tronqués sont traités selon la politique NS1-conservatrice.
Tests des sélecteurs CMake recherche/release et du chemin renderer négatif
réussis ; aucun build PS5. Les 9 flags de recherche conservés restent OFF par défaut ; le prototype Graphics Scale sans source réelle a été supprimé et la queue sparse N72 est maintenant toujours couplée au cache N73.

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

**P2.7 — horloge des rapports GPU native Ampere (04/11, source/hôte) :**
le propriétaire Vulkan GPU gpu_vulkan.cpp, partagé entre les titres
NS1 et NS2, produit désormais des timestamps en nanosecondes non
mis à l'échelle seulement si le vrai loader ExeFS a sélectionné
la génération NS2 depuis le NPDM (compteur invité 31,25 MHz).
La voie Maxwell NS1 préexistante conserve exactement les ticks GPU
divisés par 1/256/512 selon le profil, y compris après retour NS2→NS1.
CMake transmet à video_core la même définition de génération N76
que le JIT et le loader. Source adaptée de Lichii
[#84](https://github.com/zortos293/Lichii/commit/2940d9fab0)
sans règles par jeu ni changement du GPU non natif.
Témoin compilant et exécutant le vrai membre C++ GetTicks en UBSan,
O0/O2, modes natif et sans flag, profils normal/boost/overclock,
calibration à 5 ms et délai VI de 200 µs. L'oracle G21 vérifie
toujours la parité octet par octet des cinq variantes hormis cette
unique addition connue et contrôlée.
**Pas de GPU PS5 prouvé :** P2.7 garde les GPU-writes→lectures CPU
des commandes comme blocage et les essais matériels sont P5.

**P2.7c — source/hôte du fetch GPFIFO validée le 04/11 :** les deux
`DmaPusher` authentifient le canal NS2 et imposent `SafeRead` avant de lire
les mots invités, y compris sur pages physiques disjointes. Le cache Vulkan
rapatrie les buffers GPU modifiés et `scheduler.Finish()` assure l'ordre de
lecture CPU. Les fences GPFIFO restent obligatoires pour NS2, sans changer
leur politique NS1. Témoins hôte de 16 combinaisons, O0/O2 et Clang/GCC
passés. La première image, les vraies écritures GPU et les éventuels hazards
matériels restent des critères **P5**, jamais une preuve de boot réussie.

**P2.4 — cohérence des vecteurs GPR Ampere (04/11) :** la réécriture
des registres hauts vérifie désormais que tous les composants implicites
d'une paire ou d'un quartet restent contigus après emprunt de registres
Maxwell. Le détecteur natif voit aussi les vecteurs dont le registre de
départ est sous la limite scratch mais dont une composante la franchit.
Une forme impossible est rejetée, jamais compilée avec des registres
silencieusement incorrects. Cas positifs/négatifs sur le véritable
`LowerToMaxwell` et `PrepareRegisterPressure`, dont les limites
216 et 248 ; aucune modification du chemin NS1. Cela ne règle pas les
instructions Ampere non encore traduites et ne prouve aucun rendu PS5.

**P1.1 — archives de firmware multiples, choix reproductible (04/11) :**
les archives NS1/NS2 reconnues sont importées dans un ordre lexical stable,
indépendant de l'ordre non garanti de `getdents` PS5 / des répertoires
macOS. Quand plusieurs imports sont valides dans une même famille,
`ResolveFirmwarePath` choisit également le même dossier importé au
redémarrage. Une première archive invalide n'implique jamais un faux boot ;
il n'y a **aucune inférence d'une version firmware la plus récente** à partir
du seul nom. Le vrai `AutoImportFirmwareArchives` et le résolveur passent
une fixture à deux firmwares NS2 créés dans l'ordre inverse, plus les matrices
NS1/NS2 NCA/extraits, les ZIP bornés et le contrôle du manifeste NS2JB.
Les parcours restent bornés ; preuve de sélection/installation console P5.

**P1.1/P3.4 — isolation des bases et add-ons aux frontières ROMS (04/11) :**
les sélections extraites, les chemins de paquets imbriqués et le scanner
du répertoire titre rejettent maintenant les *dossiers* d'updates/DLC/AOC
dont le nom commence par `update_`, `patch-`, `dlc_`, `aoc-`, etc.,
et pas seulement les noms exacts `updates` ou `dlc`. Les paquets
autonomes manifestement réservés (ex. `Update_001.nsp`) ne sont plus
enregistrés en faux jeux de base par le launcher. Le lecteur des
add-ons reste responsable de leur identification par métadonnées ;
aucun changement de lancement du jeu réel ni de l'émulateur NS1.
Le vrai propriétaire `game_files.h` et le validateur de noms
`settings_store.h` passent les fixtures positives/négatives du scanner,
les chemins sauvegardés et l'extraction des vignettes en O0/O2/UBSan.
Le contenu cryptographique, le boot réel, les jaquettes et l'UX PS5
demeurent à prouver en P5.

**P0.2/P1.2/P4.1 — registres de source réconciliés (04/11) :**
la suppression précédente du prototype AM Graphics Scale avait laissé
quatre chemins inexistants dans le manifeste de recherche, et trois
nouveaux propriétaires NS2 (BRX, CBUF, NVDRV) n'y figuraient pas. La source partagée
du remapping physique GMMU restait aussi hors du registre F07.
Ces propriétaires ont été classés individuellement, sans inventer
d'implémentations ni rouvrir des prototypes supprimés : **120 sources de
recherche présentes**, **337 sources catalogue historiquement figées**,
**518 propriétaires de revue F07** toujours distincts. Les cinq autres
empreintes source périmées (FIFO GPU, sélection de média, thème Switch,
import de firmware et AOC) ont été comparées aux blobs historiques
récupérés sur GitHub et revues sur les vraies unités du dépôt. Le
contrôle d'inventaire et celui de couverture F07 sont désormais
**verts localement**, avec tests hôte ciblés sur les chemins corrigés.
Voir [preuves et limites](NS1_NS2_HOST_SOURCE_RECONCILIATION_2026-11-04.md).

**Ce résultat ferme la divergence du registre, pas P4.1 global** :
compilation complète des interfaces et CI du couple SHA final, profils
indépendants des compilers, P2 manquant et P5 console restent ouverts.

**P1.3 — vrai résultat IPC pour \`stpl:u\` 300 (04/11) :**
le propriétaire NS2 déjà sélectionné \`nx2_streamplay.h\` ne fabrique plus
un événement noyau pour une commande qui doit renvoyer une mémoire partagée
HID invitée. Elle fournit désormais une allocation \`KSharedMemory\` de
0x9b000 octets, permissions ReadWrite côté propriétaire / Read invité,
structure IPC (taille, décalage zéro) et copy handle réel ; refus explicite
si création ou initialisation échouent et fermeture équilibrée de l'objet.
Test hôte compilant **le vrai header** avec un noyau/IPC simulé, O0/O2,
création unique, relecture, deux pannes et libération, raccordé au preflight.
Portée uniquement NS2 et hors code NS1 ; le protocole de communication
avec des invités distants, l'ABI intégrale PS5 et la compatibilité des titres
restent non prouvés. Correctif générique repris conceptuellement de
\`Lichii nx2 #64\`, sans fusion massive ni prise en compte d'un jeu particulier.

**P1.1 — déterminisme des firmwares en dossier encombré (04/11) :**
la limite d'import reste à huit ZIP par racine, mais est appliquée aux
**huit noms ZIP réguliers les plus petits sur tout le niveau direct**,
et non aux ZIP trouvés parmi les 128 premiers noms renvoyés par le
filesystem. Le résolveur prend le premier import réellement valide
dans l'ordre lexical, sans limite de 128 entrées ni déduction de version.
Test d'intégration de l'importeur C++ avec 160 fichiers distracteurs,
12 archives NS2 dont huit admises, NS1/NS2 isolées, symlinks rejetés
et relance idempotente. Les chemins NS1 historiques ne changent pas.
Revue de source F07 remise à jour sur le blob exact.

**P1.4/P4.2 — deux lots source/hôte relancés localement (04/11) :**
26 témoins NS2/GPU/VI2/HLE et 22 témoins NS1/JIT/presentation/Vulkan
ont été exécutés en groupes de trois pour éviter les grands builds :
les 48 cas passent après correction de quatre problèmes **dans les
harnais hôte**, pas dans les jeux. Le témoin du mutex de pipeline
n'invoque plus récursivement son propre callback de publication sur
`std::function` déplacée; les témoins F03/F05 compilent la véritable
API `std::jthread` avec les headers libc++ CLT adaptés sur Mac; le
témoin de mapping JIT remplace `memfd_create` (Linux uniquement)
par un fichier POSIX privé immédiatement supprimé sur Mac, en
conservant les deux vraies vues mémoire RX/RW et les tests ASan/UBSan.
La bibliothèque Boost maintenue est utilisée pour le témoin F05,
sans substitution de `small_vector`. Ces adaptations concernent
**uniquement les contrôles hôte** ; aucun FPS, HOS NS2, WSI réel,
rendu GPU PS5, ni CI du couple SHA final n'est revendiqué.
P1.4/P4.1/P4.2 restent ouverts pour les suites et preuves restantes.

**P1.3 — service `auddmg:u` : découverte native des sorties virtuelles (04/11) :**
le service NS2 additif est maintenant enregistré par le propriétaire audio
de production déjà sélectionné. La commande 0 ouvre un objet IPC,
les commandes 0/100 de cet objet listent une sortie virtuelle
`AudioVirtualOutput0` et son nom par défaut, et la commande 401 rend un
bloc de propriétés de 0x228 octets strictement borné (stéréo, 48 kHz,
index périphérique, nom physique ; **aucune latence inventée**).
Noms inconnus et petits buffers sont refusés sans publication.
**Historique de ce premier sous-jalon :** les commandes 300/700/800
étaient initialement refusées faute de propriétaire `audsmx:u`. Le lot
suivant ci-dessous ajoute désormais le vrai ring, les contrôles IPC
et le sink. La commande 500 d'événement de changement d'état
périphérique reste absente plutôt que d'inventer un événement
jamais déclenché. Aucun fichier ni service NS1 remplacé, aucun
code jeu/TITLEID. **La qualification audio sur console reste P5.**

**P1.3 — fermeture des courses de sessions Sysmix (04/11, source/hôte) :**
la limite de 32 flux est désormais un contrat atomique d'attribution
sous le verrou du registre, au lieu d'une vérification suivie d'une
création non protégée. Le dernier ID utilisé n'est pas réattribué après
débordement ni consommé si le constructeur échoue. Les commandes
de groupe valident en bloc les IDs, leurs propriétés d'appartenance
et l'état avant tout effet sur les sinks ; doublons et liste hors limite
sont refusés, avec tentative de restauration de l'état précédent si
un stream échoue pendant la transition. Ce correctif **ne simule
aucun succès audio** et ne remplace pas les propriétaires NS1.
Le témoin hôte extrait les trois méthodes réelles du service, exécute
96 créations parallèles (exactement 32 admises) et les cas de
rollback/propriétaire/erreur sous Clang/GCC UBSan O0/O2.
La validité de la transition audio réelle sur PS5 reste P5.

**P1.3 — Sysmix PCM natif NS2 branché sur le sink partagé (04/11) :**
le service `audsmx:u` ouvre des sessions basées sur un véritable
`KProcess` invité ; `auddmg:u` utilise le même registre pour
valider le format PCM16/float stéréo 48 kHz et attacher/détacher les
flux identifiés et appartenant au processus. Le propriétaire
`nx2_sysmix.cpp` lit le ring invité, convertit des blocs PCM,
gère le bouclage, le gain, la pression de la file hôte, les événements
et les erreurs mémoire, puis valide l'avancée du curseur via
`WriteExclusive32`. Le sink et les services NS1 restent les
implémentations maintenues ; aucun moteur audio parallèle ni succès
factice sur les commandes non prises en charge. Les trois nouveaux
propriétaires Sysmix sont répertoriés séparément des 337 unités
historiques et des 120 sources de recherche (518 revues F07 inchangées).
Témoins C++ source/hôte : deux unités d'implémentation compilées en
syntaxe C++20, anneau PCM réel exécuté Clang/GCC UBSan O0/O2,
validation IPC des formats/IDs/processus O0/O2. Pas de validation du
sink sonore PS5, d'horloge HOS en jeu ni de compilation native complète :
ces preuves restent P5 et P4.1. L'ancien sous-jalon « discovery sans
Sysmix » est remplacé, sans clore automatiquement tous les services P1.3.

**Règle d'avancement :** ne pas relancer les mêmes batteries hôte à chaque
micro-correctif. Un contrôle ciblé vérifie la modification; les vérifications
exhaustives et les scénarios de jeux s'exécutent une seule fois au jalon P5
sur un SHA figé. Les tests console ne sont pas lancés ici.


**P2.7 — correction d’attente sémaphore dans le puller NS2 (05/11, source/hôte) :**
le puller Ampere de recherche conservait une boucle `SemaphoreAcquire`
sans les deux garde-fous déjà actifs dans le puller NS1 maintenu :
sortie sur `System::IsShuttingDown` et propagation de la défaillance du
worker GPU PS5 (sondage borné à un appel tous les 64 tours).
Le propriétaire NS2 reprend **le même corps de méthode** que le puller NS1 ;
le code NS1 n'est pas modifié. L'égalité de sémaphore reste obligatoire
lors d'une exécution normale, sans accusé de réussite synthétique.
Le témoin hôte exécute la vraie méthode des deux variantes, sous
Clang/GCC, UBSan O0/O2 et profils PS5/desktop : succès différé, arrêt
initial/en cours et erreur GPU immédiate/différée, **8 configurations PASS**.
Il est ajouté au preflight et à la batterie P4, sans build PS5.
Cette correction garantit une issue aux attentes arrêtées/échouées en
source ; l'exécution et la cohérence des vraies fences GPU restent P5.


**P2.7 — refus des classes GPU inconnues après rebind natif (05/11, source/hôte) :**
le puller Ampere retirait correctement l’identité du moteur précédent
mais conservait son pointeur `DmaPusher::subchannels` lorsqu’une classe
de moteur non reconnue était sélectionnée ; des commandes suivantes
pouvaient alors exécuter l'ancien moteur malgré un ID désormais invalide.
Les canaux natifs NS2 effacent ce pointeur après retrait des propriétaires
3D/Compute ; le pusher commun, déjà protégé contre les moteurs nuls,
refuse alors les commandes jusqu'au prochain bind reconnu.
Les binds rejetés avant modification de la propriété ne touchent pas
à l'état ancien. L'attitude historique NS1 en cas de classe inconnue est
préservée, sans changement du moteur commun. Test hôte de la **vraie méthode**
avec classes Maxwell, Ampere 3D/Compute/DMA, classes invalides, échec de
propriété et retour en NS1 : Clang/GCC O0/O2, profils host/PS5 simulés,
UBSan, huit configurations réussies. La GPU réelle reste à qualifier en P5.


**P2.4 — instruction générale `FRND.F32` avec opérande CBUF natif (05/11, source/hôte) :**
le frontend Ampere reconnaissait déjà `0xb07` dans la table ISA maintenue,
mais le lowerer Maxwell refusait cette forme faute de cas de traduction.
La forme CBUF est désormais émise en un véritable `FRND` Maxwell
(`0x4ca8…`) avec encodage de la banque et conversion de l'offset CBUF
octets → mots ; seule une banque existante **0–17**, une adresse alignée
sur 4 octets et des modes de format/rondi admis sont acceptés. Aucun
`TitleID`, source factice ni shader de repli. La forme registre `0x307`
reste inchangée et les autres variantes non prises en charge restent
refusées. Le test C++ exécute le vrai `LowerToMaxwell`, le classificateur
ISA et le **pont `LowerReviewedToMaxwell` utilisé par le renderer**,
avec les cas positifs, la conformité du mot Maxwell, les banques
invalides, l'adresse non alignée et le mode non reconnu : Clang/GCC,
O0/O2, UBSan **4/4 PASS** sur hôte. Ce sous-jalon ajoute une instruction
traduite mais ne valide ni les autres opcodes, ni les stages task/mesh,
ni un vrai rendu graphique PS5 (P5).


**P2.4 — `SEL` avec registre uniforme B (05/11, source/hôte) :**
le décodeur reconnaissait la forme `0xc07`, mais elle n'était pas
acheminée vers le sélecteur Maxwell déjà partagé par `SEL/FSEL`.
Le frontend Ampere l'admet maintenant en calculant le registre uniforme
à partir du B natif, avec **réservation du banc UR avant traduction** :
les sorties GPR hautes qui le chevaucheraient sont refusées. Les UR
0–15, UR étendus et UR63 (zéro) sont contrôlés par le même propriétaire.
La forme registre `0x207` reste fonctionnelle, sans changement à NS1
ni à la politique opt-in FSEL existante. Le banc UR absent/invalide
ne produit jamais un faux shader. Test regroupé des deux nouvelles formes
Ampere **FRND-CBUF + SEL-UR** sur les vraies fonctions
`ProbeProgram`, `LowerReviewedToMaxwell` et `LowerToMaxwell` :
Clang/GCC, O0/O2, UBSan **4/4 PASS** ; aucune preuve de rendu PS5.


**P2.4 — `FSET.BF` avec source uniforme (05/11, source/hôte) :**
la forme Ampere `0xc0a` était reconnue dans la table ISA mais non traduite,
alors que le propriétaire partagé possède déjà le `FSET` Maxwell et
son accès au banc UR. Elle rejoint le même lowerer, sans introduire
de pipeline parallèle : le registre uniforme B est découvert avant
l'allocation du banc protégé et son numéro est mappé dans l'ABI Maxwell.
Les comparaisons avec registres ou immédiats restent identiques ; les
combinaisons de mode hors contrat, les UR invalides et les collisions
avec les GPR de sortie restent refusées. Le test combiné
`check_ampere_scalar_alu_sources_host.py` exécute les vrais propriétaires
`ProbeProgram`, `LowerToMaxwell`, `LowerReviewedToMaxwell` pour
`FRND-CBUF`, `SEL-UR` et `FSET-UR`, sous Clang/GCC UBSan O0/O2 :
**4/4 PASS**. Aucun framebuffer PS5 ou support complet de stages
Ampere n'en découle : P2.4/P5 restent ouverts.


**P2.4 — `MUFU` à immédiat 32 bits (05/11, source/hôte) :**
la forme Ampere `0x908`, déjà recensée par l'ISA officielle du vendor,
utilise le même compilateur que MUFU registre/uniforme mais sa source
est directement le mot immédiat natif. Le sélecteur du véritable lowerer
la matérialise dans un GPR temporaire et émet l'instruction Maxwell,
en conservant la conversion en radians déjà revue pour SIN/COS. La forme
refuse les champs de source A et modificateurs incompatibles, les
fonctions matérielles non traduites et les champs inconnus ; aucun
mode graphique arbitraire n'est « rendu compatible » par défaut.
Le témoin commun exécute les véritables classificateur, lowerer et
pont `LowerReviewedToMaxwell`, vérifie l'encodage MUFU, l'identité
de la constante, les mutations rejetées, et les chemins historiques
`FRND-CBUF`/`SEL-UR`/`FSET-UR`. Clang/GCC UBSan O0/O2 : **4/4 PASS**.
Le runtime Vulkan/PS5 et les autres instructions/stages non traduits
restent une limite réelle P2.4 et nécessitent P5 pour la console.


**P2.4 — `UPOPC` Ampere, comptage de bits dans les registres uniformes (05/11, source/hôte) :**
le décodeur ISA 128 bits connaissait déjà l’opcode `0x2bf`, mais
le lowerer n’offrait pas de traduction. `UPOPC` passe désormais par
le même propriétaire `LowerToMaxwell` et émet un vrai POPC Maxwell
vers le banc de GPR réservé aux uniformes, avec source et destination
UR explicitement vérifiées. La réservation du banc intervient avant
l’abaissement de l’instruction et inclut les UR étendus ; UR63 peut
servir de source zéro, jamais de destination. Les formes prédicatées
non représentables, registres UR hors domaine et champs de mode non
prouvés sont refusés, sans fallback silencieux. Le témoin C++ hôte
`test_ampere_scalar_alu_sources.cpp` teste les mots Maxwell réellement
émis (UR bas, UR étendus, UR63, bit d'inversion) et les échecs par le
pont réel `LowerReviewedToMaxwell`, aux côtés des régressions FRND/SEL/
FSET/MUFU ; **Clang/GCC, UBSan O0/O2 : 4/4 PASS**. P2.4 demeure
ouvert pour les autres opcodes/stages et le rendu physique PS5 reste P5.


**P1.3 — Kernel WaitIfEqual64 (type d’arbitrage 3), 05/11/2026, source/hôte :**
la voie SVC NS2 issue des derniers correctifs amont nécessitait un
`WaitForAddress64` comparant **les 64 bits**. L’ancienne table refuserait
le type 3 par `InvalidEnumValue`, et son wrapper tronquait la valeur
d’attente à `s32`. Un propriétaire d’arbitrage unique pour la release
PS5 dual-NPDM prend désormais en charge ce type, avec vérification
d’alignement sur 8 octets, accès 64 bits à la mémoire invitée *après*
validation du mapping, et conservation des arbitrages 32 bits types 0–2
(alignement 4, comparaison signée 32 bits, attente/notification existantes).
Les deux dispatchers SVC maintenus transportent la valeur LP64 complète
mais le wrapper 32-from-32 demeure à 32 bits.

Source isolée : `kernel_wait64/` comprend les deux unités du noyau
`k_address_arbiter.cpp` et `svc/svc_address_arbiter.cpp` ainsi que les
headers ABI partagés `k_address_arbiter.h`, `k_process.h`, `svc.h`,
sélectionnés uniquement quand le SVC GPU-access dual-NPDM est actif.
C’est un **correctif de boot générique**, et non un contournement par jeu.
Le témoin réel exécute les comparaisons extraites du véritable kernel
(4/4 Clang/GCC UBSan O0/O2, 32/64 bits, valeur supérieure, négative et
mémoire invalide) ; trois unités C++ entières du noyau et du SVC réel
passent aussi `clang++ -fsyntax-only` avec libc++ macOS compatible.
Ce test **ne valide pas** l'ordonnanceur entier, les SVC sur PS5, les
CPU invités ou le lancement des jeux : qualification en P5 seulement.


**P1.3 — audit propriétaire source et sélection CMake (05/11) :**
la sélection a été testée en vrais projets `cmake -S/-B` avec et sans
GPU-access dual-NPDM : le couple `k_address_arbiter.cpp` /
`svc_address_arbiter.cpp` bascule ensemble, jamais partiellement. Les
cinq sources/header ajoutés **après F07** sont consignés séparément et
conservent l’inventaire historique F07 immuable de **518/518**.
Le `check_shared_kernel_wait64_host.py` contrôle cette bascule et
l'alignement, les deux variantes 32/64 bits et les unités C++ réelles.
P1.3 reste soumis à la validation du scheduler complet et de la console.


**P4.1 — conservation des catalogues F07 (05/11) :** les cinq unités
`kernel_wait64` sont enregistrées explicitement comme source/hôte
post-F07 dans *les deux* validateurs de manifest, sans changer les
contreparties immuables **518/518** (code optimisé audité) et
**337** (catalogue physique historique). Les deux contrôles réels
`check-eden-optimization-coverage.py` et
`check-active-source-inventory.py` passent à nouveau.


**P2.4 — UIMAD 32 bits avec addend immédiat (opcode Ampere `0x4a4`, 05/11/2026) :**
le décodeur ISA connaissait l’opcode uniforme mais pas le chemin de
traduction du moteur GPU PS5. Le lowerer partagé prend désormais ses
**deux multiplicandes UR** et la destination UR dans le banc réservé
Maxwell, tout en préservant l’**immédiat 32 bits** indépendant de ces
registres (abaissement canonique via IMAD `0x424`). L’occupation des UR
étendus est détectée avant la conversion. La forme à prédicat non
authentifiée reste volontairement refusée. Test exécutant le réel
`LowerReviewedToMaxwell` : UR bas/hauts, UR63=source zéro, changement
de l’immédiat, refus de registres hors domaine et de modes inconnus ;
**4/4 Clang/GCC UBSan, O0/O2 PASS**, avec régression FRND/SEL/FSET/
MUFU/UPOPC dans les mêmes binaires. Ce lot améliore la couverture ISA
générique et ne ferme **ni P2.4 ni le rendu GPU NS2 sur PS5**.


**P2.7 — admission stricte des segments GPFIFO natifs (05/11/2026) :**
l’ioctl de commande possède deux frontières distinctes : la liste
`CommandListHeader` lue dans la mémoire **CPU invitée**, puis les
`entry.addr/size` de chaque tampon de commandes dans la **GMMU**.
Le contrôle existant n’authentifiait que la première. Le propriétaire
`nvhost_gpu::SubmitGPFIFOImpl` vérifie désormais que **chaque** segment
non vide est entièrement mappé dans la GMMU native avant
`InitChannel`, la liaison du propriétaire ou la réservation de fence.
La vérification utilise la vraie `MemoryManager::IsFullyMappedRange`
(avec gardes de limite d’adressage et pages 4 KiB) et le format de
`Tegra::CommandHeader` du moteur ; aucun comportement NS1 n’est changé.
Le témoin hôte exécute l’admission extraite de ce propriétaire, y
compris trou de page, liste mixte, frontière 49 bits, zéro octet,
VA nulle et chemin Maxwell ; **Clang/GCC UBSan O0/O2 : 4/4 PASS**.
Ce garde supprime une possibilité d’acquittement d’une commande
initialement non mappée ; il ne constitue pas une preuve d’absence de
courses si le guest modifie la GMMU après l’admission.


**P4.1 — séparation des contrôles NVDRV (05/11) :** le témoin de
pré-initialisation `check_native_gpfifo_preinit_host.py` reste dédié aux
flags et à la propriété des FD, en s’arrêtant à la nouvelle frontière
GMMU. Le contrôle `check_native_gpfifo_command_spans_host.py` exécute
indépendamment **le bloc réel de vérification des commandes GPU**. Les
deux batteries de 4 configurations Clang/GCC UBSan passent ; le
périmètre additionnel n’est pas interprété comme un résultat console.


**P0.2 — promotion bornée ARM64 `LDAPR` (05/11/2026, source/hôte) :**
au lieu d’activer l’overlay A64 recherche entier, le profil PS5 final
génère quatre sources Dynarmic à partir du propriétaire commun épinglé
et n’y ajoute **que LDAPR** (RCpc acquire → LDAR acquire plus fort).
Le vrai `a64_translate.cpp` passe la compilation syntaxique
Apple Clang ; le vrai décodeur exécute les quatre variantes avec UBSan
O0/O2 **2/2 PASS** (le `g++` macOS est le même compilateur, pas GCC). Les sources d’origine ne sont pas modifiées.
`RETAA/RETAB` sans PAC, CAS/LSE et CPU6 restent hors du profil final,
sans contourner les neuf commutateurs de recherche OFF. Ce progrès
ne clôt ni P0.2 global, ni P1.1, ni les essais console P5.


**P0.2 — qualification hôte de six unités réelles du chaînage GPU
(05/11/2026) :** `check_native_gpu_boot_source_tus_host.py` compile en
parallèle avec le même frontend C++20 les propriétaires de sources
`nvhost_as_gpu`, `nvhost_gpu`, `puller Ampere`, `gpu_session`,
`gpu_worker` et `graphics_supervisor` depuis l’overlay vendor courant.
**6/6 compilations syntaxiques hôte PASS**, avec interfaces partagées
NVDRV/GMMU/HLE et le vrai jeu de headers. Ce témoin est désormais
branché à la préqualification P4 et au Core fast gate. **Limite :** il
ni ne lie l’ensemble ni ne définit `PS5_NATIVE` ; aucun GPU/VI2 n’est
activé et aucune commande n’est soumise au matériel PS5. Le profil
final garde les neuf chemins de recherche désactivés tant que les
contrats runtime/process GPU et P5 ne sont pas établis.


**P2.7 — état QMD3 sous pression mémoire (05/11, source/hôte) :**
le scheduler `NativeQmdScheduler` est alimenté par des adresses PCAS
invitées ; une nouvelle adresse peut provoquer une allocation
`std::unordered_map::try_emplace`. Le propriétaire native traite
désormais `std::bad_alloc` **à ce point précis avant tout dispatch ou
publication de semaphore**, renvoie une erreur de transaction reconnue
(`QMD state allocation failed`) et laisse l’état précédent inchangé.
Un nouvel essai peut créer le QMD sans dispatch fictif. Le test
`test_native_qmd_allocation.cpp` force réellement l’échec d’une
allocation hôte et vérifie refus, absence de mutation GPU et reprise,
tandis que `test_native_qmd_scheduler.cpp` revalide dépendances,
semáphores et absence de dispatch dupliqué ; **4/4 compilations/exécutions
Clang/UBSan O0/O2 PASS**. P2.7 et la validation console restent ouverts.


**P0.2 CPU6 — correction de blocages de préemption et de ticks (05/11) :**
le mode six cœurs research utilisait un `std::array` de six priorités
avec seulement quatre initialiseurs (`59,59,59,63`) : les cœurs 4 et 5
recevaient implicitement la priorité `0`. Le CMake génère désormais
un scheduler cohérent `59,59,59,63,59,59` depuis le propriétaire Eden.
Les callbacks Dynarmic 32/64 conservent **4** comme diviseur de ticks
pour tout `KProcess` sans affinité réelle sur les cœurs physiques 4/5 ;
les processus disposant de ces nouveaux cœurs utilisent **6**. Le
propriétaire A64 est la vraie unité G11 optimisée, avec N76 conservé,
**jamais** le vieil `arm_dynarmic_64.cpp`. Tests : CMake réel ON/OFF
avec prérequis/refus, dérive d’ancre refusée, 3 vrais TUs C++20
syntaxiques, logique de préemption et diviseur extraite de la source
exécutée UBSan O0/O2. La variante G11 dev ne passe qu’en x86 hôte ;
aucun support PS5 de cette variante n’est revendiqué. **CPU6 reste
désactivé en production**, pas de preuve de 6 cores sur console ;
NS1 ne change pas hors sélection explicite research. P0.2/P5 ouverts.


**P0.2 — admission atomique des propriétaires GPU (05/11, source/hôte) :**
`NativeGpuProcessRegistry::Register`, les Bind du canal, du moteur
3D et du moteur Compute, la session native `NativeQmdSession` ainsi que
les deux caches Ampere retournent un refus/une absence de ressource
contrôlés si l’allocateur hôte échoue. Cela évite les exceptions
`std::bad_alloc` lors de l’authentification GPU invitée. Le compteur de
génération du canal n’est **plus consommé** si la création du nœud map
échoue. Deux témoins hôte exécutent les vrais registres C++ et les
méthodes originales de session/cache extraites des propriétaires ;
injection déterministe d’allocations impossibles, conservation des
tickets, reprise et invalidation après `Unbind`, ainsi que séparation
3D/Compute prouvées sous Clang/UBSan O0/O2. Le profil de production
reste inchangé : aucun rendu Ampere/NS2 n’est déduit de ces succès.


**P2.7 — double validation des commandes GPFIFO natives lors du fetch
(05/11/2026, source/hôte) :** le contrôle d'adresse GMMU à l'instant
`nvhost_gpu::SubmitGPFIFOImpl` ne suffit pas : un processus peut démapper
sa plage entre le ioctl et `DmaPusher::Step`. Les deux vrais propriétaires
G20 (normal/DEV) appellent `NativeGpfifoFetchMapped` après l'attente
du fence précédent, avant la lecture des mots invités et le cache GPU.
Un paquet non mappé est rejeté **avant ProcessCommands**, sans valider
le paquet ni sa séquence de sémaphore ; le profil PS5 notifie l'erreur
GPU persistante sans lancer d'exception sur le thread GPU. Le code reste
isolé derrière `EDEN_NS2_NATIVE_GPU_DISPATCH`, conservant le chemin NS1.
Test `test_native_gpu_fetch_admission.cpp` : plages vides, 49 bits,
limites de pages 4 KiB, mappings révoqués ou recréés, contrôle des
dépassements **Clang UBSan O0/O2 PASS**. Sept vraies TUs propriétaires
passent la compilation source sous macros `PS5_NATIVE`,
`EDEN_NS2_NATIVE_GPU_DISPATCH`, et bridge shader NS2 sur Mac : GMMU,
NVDRV/GPU, puller, capture shader, capture SPIR-V, DMA normal ; le DMA
DEV reste syntaxiquement vérifié **x86 uniquement** car son profiler
emploie des intrinsics x86 hors du périmètre release. Cela atteste
la cohérence source des chemins natifs, pas une liaison ou une exécution
matérielle PS5. P2.7/P5 restent ouverts pour le cycle de vie GPU
réel, les fences et le premier framebuffer.


**P2.7 — correction du faux acquittement après refus GPFIFO
(05/11/2026, source/hôte) :** le premier recheck de la mémoire au
fetch interrompait seulement `DmaPusher::Step` (`return false`) en
enregistrant une erreur. Or `Scheduler::Push` revenait alors
normalement, et `GPUThread::RunWorker` pouvait publier le fence
**comme si les commandes avaient été exécutées** et traiter les
complétions futures. Les deux sources DMA maintenues normal/DEV
propagent désormais l'échec natif PS5 par `std::runtime_error` :
la vraie entrée `pthread` des deux workers GPU intercepte l'exception,
publie l'échec persistant et demande l'arrêt avant la publication du
queue-fence. Le code est compilé uniquement avec
`EDEN_NS2_NATIVE_GPU_DISPATCH` et lève l'exception uniquement en
`PS5_NATIVE`, sans changer le flux NS1 normal. Témoin source réel des
deux workers et simulation exécutable avec **les vrais
`gpu_failure.h` et `native_gpu_fetch_admission.h`**, vérification du
fence non acquitté, du stop et de la notification persistante après
consommation UI, UBSan O0/O2. Limitations : pas de preuve des cycles
réels NVIDIA/RADV, de l'exclusion concurrente Unmap/Read ni de la fin
du GPU NS2 sur console ; P2.7/P5 restent ouverts.


**P0.2 — vérification FD avant initialisation GPFIFO/3D/Compute
(05/11/2026, source/hôte) :** les ioctl `AllocGPFIFOEx` et
`AllocGPFIFOEx2` pouvaient utiliser `sessions[fd]` avec un FD inconnu,
puis déréférencer un `session->process` nul. `ValidateChannelOwner`
partage désormais une seule règle pour les deux ioctl et
`AllocateObjectContext`, avant `InitChannel`, `program_id` et
`ctxObjs`. Un FD NS2 ne peut pas initialiser un canal partagé avec
un processus étranger ; le contrôle inverse interdit qu’un FD NS1
prenne la main sur un canal avec un propriétaire NS2. Les FD NS1
valides seuls conservent leur comportement. Tests : vrai corps C++
extrait de l’unité NVDRV maintenue, exécuté Clang UBSan O0/O2 sur
les scénarios absents, nuls, recyclés, natifs/legacy et multi-FD ;
la compilation syntaxique du propriétaire source est aussi contrôlée.
**Ne valide ni la session GPU runtime ni la production NS2 ; P0.2/P5
restent ouverts.**
