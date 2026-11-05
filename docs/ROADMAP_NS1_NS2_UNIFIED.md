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
(task/mesh, LEPC hors Geometry sans provenance PC et autres opcodes non traduits ; Geometry et la
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
acceptés ; LEPC hors Geometry sans adresse GMMU vérifiée et task/mesh restent refusés.
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
Task/mesh et les usages de LEPC non couverts par l'origine PC Geometry vérifiée restent des manques de code P2.4.

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
PS5, task/mesh et LEPC hors Geometry sans PC attesté restent
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
dynamiques tant que l'émetteur SPIR-V partagé ne possède pas de
garde de plage exécutable. À la sortie de BuildResourcePlan, le
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
**Les atomiques dynamiques ne sont pas implémentés par ce lot** :
ils sont explicitement refusés, sans imiter une exécution réussie.
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
