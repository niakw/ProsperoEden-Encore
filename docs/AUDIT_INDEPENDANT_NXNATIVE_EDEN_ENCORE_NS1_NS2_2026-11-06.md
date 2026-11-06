# Audit indépendant — `seedds/nxnative` face à Eden Encore (NS1 / NS2)

**Date :** 6 novembre 2026
**Nature :** revue indépendante de sources publiques, de relevés par jeu, des fichiers et des écarts architecturaux ; **aucune modification de code**, aucun démarrage de jeu, aucun build PS5.
**Focalisation :** [`dm/games/040074A01BF12000`](https://github.com/seedds/nxnative/tree/b4318c7a4d0bcbd16e7873ce63f33d344d1acbfb/dm/games/040074A01BF12000), **Donkey Kong Bananza**.
**Objectif :** extraire les invariants matériels/protocolaires et les constats reproductibles de `nxnative`, les confronter à nos sources **NS1 et NS2**, puis définir des corrections **génériques** et des qualifications hôte compatibles avec la roadmap **P0 → P1 → P2 → P4**, sans déplacer la validation PS5 hors de **P5**.

## Statut : référence différée pour les optimisations après P5

> **DOCUMENT DE RÉFÉRENCE — NON BLOQUANT.** Cet audit est conservé pour la phase d'**optimisation et d'amélioration du moteur commun NS1/NS2**, **après le premier build PS5 fonctionnel du jalon P5**. Il ne constitue ni une liste de nouvelles conditions de sortie P0–P4, ni une autorisation de modifier le rendu avant ce premier build.
>
> Les priorités P1/P2/P4 ci-dessous décrivent l'état **historique du snapshot du 6 novembre 2026** ; elles ne doivent pas être réinjectées automatiquement dans la roadmap active. Au début de la phase d'optimisation, recontrôler chaque écart sur les SHA courants de `main` et `vendor`, éliminer les éléments déjà corrigés, puis mesurer l'impact réel sur NS1 et NS2 avant intégration.

**Ordre de réutilisation prévu :** première version P5 fonctionnelle → baseline de stabilité et performances → réconciliation des observations `nxnative` avec le code courant → choix des optimisations génériques prioritaires → tests de non-régression NS1/NS2 et mesures comparatives. Aucun réglage ou correctif spécifique par TitleID ne doit être introduit à partir des seuls relevés de `nxnative`.

## 0. Sources figées et limites de preuve

| Source | SHA consulté | Portée |
| --- | --- | --- |
| [`seedds/nxnative`](https://github.com/seedds/nxnative/tree/b4318c7a4d0bcbd16e7873ce63f33d344d1acbfb) | `b4318c7a4d0bcbd16e7873ce63f33d344d1acbfb` | Arborescence, README, profils NS1/NS2, code et notes techniques sélectionnés |
| [`niakw/ProsperoEden-Encore`](https://github.com/niakw/ProsperoEden-Encore/tree/84c18e8cc70f1240a80d648bba5feaaafa0188fc) | `84c18e8cc70f1240a80d648bba5feaaafa0188fc` | Source `main`, roadmap, HLE, loader NUP, historique des tests |
| [`niakw/Prospero.Eden-Encore-vendor`](https://github.com/niakw/Prospero.Eden-Encore-vendor/tree/5fdbd61707b49cfa1fbdce220e0b96054610fd94) | `5fdbd61707b49cfa1fbdce220e0b96054610fd94` | Sources maintenues `encore-active`, frontend Ampere, GPU, GPU session, Vulkan |

**Vérification de cohérence :** le sous-module `vendor` pointé par le `main` Eden audité est bien `5fdbd617...`. Les documents de roadmap contiennent parfois des SHA antérieurs ; leurs conclusions sont utiles, mais ne remplacent pas l'inspection du code au couple ci-dessus.

**Niveaux de preuve employés :**

- **[NX-F]** fait déclaré/documenté par `nxnative` ou contenu directement inspecté dans son dépôt. Une session Mac décrite par les mainteneurs n'est pas un résultat PS5.
- **[EE-S]** présence ou défaut repéré dans une fonction/fichier du snapshot Eden/vendor ; ne signifie pas que le comportement GPU a été validé.
- **[À QUALIFIER]** hypothèse ou chemin à comparer aux contrats/ABI, sans preuve suffisante de bug en jeu.
- **[LIMITE]** fichier trop volumineux pour lecture intégrale via le connecteur GitHub, test non exécuté ou distinction architecturale empêchant une transplantation directe.

**Limitation importante sur les gros TSV :** le connecteur GitHub a fourni le nom, la taille, le SHA blob et l'existence de `pso_manifest.tsv` et `shader_map.tsv`, mais la lecture intégrale de leurs ~1,83 et ~2,84 Mo a échoué à cause de la limite de récupération. Leur *structure générale et leurs agrégats* proviennent donc du README de `nxnative` et non d'un recomptage de toutes les lignes. Les autres petits fichiers et des extraits des tables de paires ont pu être inspectés. **Aucune analyse ligne à ligne de ces deux gros TSV n'est revendiquée.**

**Principe de sécurité :** ne pas publier de ROM, dump, clés, firmware, morceaux de shader propriétaires ou données extraites d'un jeu. La documentation des mécanismes est utilisable ; l'import d'un code doit respecter sa licence propre et les licences tierces.

---

## 1. Verdict synthétique

**Intérêt : très élevé comme corpus de diagnostics et d'oracles ; faible comme backend directement transplantable.** `nxnative` n'est pas un émulateur Switch complet : le code ARM du jeu est réécrit pour exécution native Apple Silicon, les services Horizon sont substitués, NVN/NVN2 est traduit en opérations Metal. Eden Encore émule les chemins invité CPU/HLE/GPU et produit du **Vulkan sur PS5/RDNA2**. On ne copie ni son scheduling Apple, ni MetalFX, ni son GPU Metal comme s'ils étaient un moteur Vulkan.

Les enseignements les plus utiles pour Eden Encore sont, dans l'ordre :

1. **La chaîne causale « image absente » de Bananza.** Elle est documentée bien plus finement qu'un simple « écran noir » : initialisation du SDK/NVN2, shaders compute, conditions de clear, textures block-linear, géométrie, écritures mémoire globales et indirect draws.
2. **La séparation des vrais mécanismes de la logique par titre.** `game.tsv` contient des faits mesurés sur une version et un hôte ; le bon portage Eden consiste à comprendre NPDM, commandes GPU, attributs de shader, tables de textures et synchronisation, pas à forcer un mode spécial par TitleID.
3. **Des lacunes source vérifiables chez nous existent encore**, par exemple `ISBEWR 0x927`, `CSMTEST 0x80d`, les stages Task/Mesh, certaines formes de texture-buffer arrays et de sorties physiques, et le timeout d'acquisition de sémaphore. Mais il serait **faux** de prétendre que QMD3, le bridge Ampere, les atomiques, la mémoire NS2 ou NUP sont absents : ils ont déjà des propriétaires dans le code.
4. **Le catalogue des 148 répertoires de jeux** et les multiples documents par symptôme offrent un excellent modèle de couverture : comparer des preuves multi-titres et multi-versions plutôt que conduire le portage au rythme des écrans noirs d'un seul jeu.
5. **L'atteinte du premier framebuffer NS2 sur PS5 ne peut pas être déduite de ces preuves.** Dans notre dernier test console documenté, `guest_frame_handoff=0` sur Bananza/Mario Kart World, alors que l'initialisation Vulkan et le CPU invité démarraient. La qualification console reste **P5** ; le travail code/ABI/test hôte pour P0–P4 ne doit pas l'attendre.

### Priorités actionnables après comparaison

| Priorité technique | Cible précise | Pourquoi / qualification attendue | Etat au snapshot |
| --- | --- | --- | --- |
| **Critique P2.4** | `ISBEWR 0x927`, `CSMTEST 0x80d`, instructions Task/Mesh et géométrie | `ISBEWR` est nommé en table ISA sans voie correspondante repérée dans `lower_to_maxwell.h`; `CSMTEST` sans abaissement repéré ; MKW prouve l'intérêt des shaders Task/Mesh | **Manque à traiter, ABI exact encore à établir** |
| **Haute P2.3/P2.4** | écritures GPU via pointeurs chargés, `GlobalMemoryToStorageBuffer`, mémoire de sortie physique | Bananza avait des comptes indirects incorrects lorsque les stores étaient supprimés ; notre SPIR-V contient un refus de certaines sorties physiques | **Partiel ; risque réel mais non rattaché à une capture PS5 actuelle** |
| **Haute P2.2c/P2.3** | TIC/TSC, SSBO/CBUF QMD3, texture-buffer arrays, lifetime image | Notre chemin existe mais le shader SPIR-V refuse explicitement les tableaux de texture buffers | **Chemin existant, formes restantes à qualifier** |
| **Haute P2.7** | `Puller::ProcessSemaphoreAcquire` | Un `TODO` sur `acquire_timeout` subsiste ; les attentes sont sensibles à la cohérence GPU/CPU | **Manque source confirmé** |
| **Haute P1.3** | réponses `GetInfo` NS2, Graphical Supervisor/VI2, nvdrv, vidéo | Bananza répertorie les valeurs attendues par SDK20 ; plusieurs IPC Eden sont encore conditionnels | **À vérifier commande par commande, sans inventer de succès** |
| **Moyenne P2.4** | texture GOB NS2, BC7/ASTC, niveaux mip et barrières | Défauts amont causant trous, texels NaN, cible noire | **À confronter au vrai cache de textures partagé NS1/NS2** |
| **Moyenne P4** | fixtures de shaders/opcodes et couverture par versions | Les TSV peuvent fournir clés, couples et formes contrôlées sans embarquer de données de jeu | **Outillage de qualification à construire, pas port de backend** |

---

## 2. Pourquoi l'architecture de `nxnative` est différente

| Sujet | `nxnative` | Eden Encore sur PS5 | Conséquence |
| --- | --- | --- | --- |
| Exécution CPU | NSO transformé ; ARM invité exécuté directement sur puce Apple, substitutions spécifiques | CPU/JIT émulation, gestion du processus invité et ABI Horizon | Les patchs du réécrivain NSO ne sont pas des correctifs génériques Dynarmic |
| Système | HLE native liée aux fonctions de jeu/SDK ; `dm/host/hle_*` | Kernel/HLE + services IPC/TIPC, NVDRV, KProcess, VI2 | Réutiliser les **contrats** et les séquences, pas les stubs Apple |
| GPU | NVN/NVN2 vers Metal ; composants du jeu prétransformés en SPIR-V/MSL et bibliothèques Apple | Méthodes GPU NVIDIA → pipeline Ampere/Maxwell → SPIR-V → Vulkan/RADV | Les métadonnées NVN2 et les sémantiques shaders sont transférables, pas les PSO Metal compilés |
| Mémoire | Pools Apple Silicon, texture Metal, allocations propre à l'app créée | GMMU/NVMap, mémoire et textures partagées du moteur PS5 | Respecter adresses/aliases/tuilage du **matériel invité**, pas l'allocateur Apple |
| Upscaling | NDSR de jeu, converti ou remplacé par MetalFX | NDSR/DLSS invités à interpréter, puis options graphiques PS5 Vulkan | Ne pas assimiler NDSR à DLSS Neural Rendering natif PS5 ou à FSR3.1 |
| Distribution | Une app Mac/iOS dérivée du jeu à partir d'un dump/NSP/NUP | Une app PS5 unique, bibliothèque multi-jeux NS1/NS2 | `game.tsv` doit rester une base de diagnostics, pas devenir une configuration obligatoire par titre |

**Convergence réelle :** les deux projets rencontrent les mêmes instructions Ampere, les mêmes sorties de culling, les mêmes registres de GPU, les mêmes formats de textures et les mêmes interactions de SDK. C'est à cette couche qu'il faut comparer.

### Organisation documentaire de `nxnative`

À la révision consultée, `dm/games` affiche **148 répertoires par TitleID**, dont **11 commençant par `040`** ; la présence d'un répertoire ne constitue pas une preuve que le jeu fonctionne intégralement. Cinq fichiers de contrôle complètent ce dossier : `README.md`, `game.py`, `profile_guess.py`, `settings.py`, `settings.tsv`.

- `dm/games/<titleid>/README.md` : version testée, symptôme, cause, correctif, validation et limites.
- `dm/games/<titleid>/game.tsv` : identité, modules, ressources, formats, paramètres observés, clés de shader.
- `shader_map.tsv`, `shader_facts.tsv`, `shader_pairs.tsv`, `pso_*` : *données d'évidence* produites/consommées par outils.
- `docs/reference/{shaders,rendering,nvn-objects,services,memory,movies,frame-rate,packing}.md` : index transversal **symptôme → cause → correction → jeux touchés**.
- `dm/gfx/tools/shader_split.py`, `dmsh_ampere.py`, `dmsh_xlate`, `dmsh_mesh.py` : extraction, décodage, conversion, sélection de shaders ; références **algorithmiques**, pas modules PS5 prêts à compiler.
- `dm/gfx/nvn/hle_nvn.c`, `nvn_mtl.m`, `dm/host/hle_svc.c`, `hle_codec_video.c`, `hle_oe.c`, `dm/gfx/hle_vi.c` : sources pour recouper la sémantique réelle.
- `dm/games/game.py` : matérialisation et validation du profil ; `dm/tools/impact_map.tsv` et les outils d'analyse peuvent inspirer des matrices de régression.

Un point fort est la **provenance multi-jeux** : la même cause peut être observée dans Bananza, MKW, Splatoon ou BOTW, ce qui évite de prendre une coïncidence de profil pour une exigence de l'architecture.

---

## 3. Audit détaillé des neuf fichiers de Donkey Kong Bananza

Dossier : [`dm/games/040074A01BF12000/`](https://github.com/seedds/nxnative/tree/b4318c7a4d0bcbd16e7873ce63f33d344d1acbfb/dm/games/040074A01BF12000) ; environ **5 406 181 octets** de documents et d'index.

| Fichier | Taille du blob GitHub | Contenu et apport | Transfert recommandé vers Eden |
| --- | ---: | --- | --- |
| [`README.md`](https://github.com/seedds/nxnative/blob/b4318c7a4d0bcbd16e7873ce63f33d344d1acbfb/dm/games/040074A01BF12000/README.md) | 21 321 B | Rapport de sessions Mac, boot, API/HLE, shaders, mémoire, rendu, formats, causes d'images absentes, risques ouverts. **Lu.** | **Priorité maximale** comme matrice causale et source de cas de tests |
| [`game.tsv`](https://github.com/seedds/nxnative/blob/b4318c7a4d0bcbd16e7873ce63f33d344d1acbfb/dm/games/040074A01BF12000/game.tsv) | 2 516 B | TitleID, version/modules, marqueur RomFS, disposition mémoire, `render_cond`, timestamps. **Lu.** | Oracles de **metadata/ABI** et d'analyse, pas overrides forcés |
| [`geo_mesh.tsv`](https://github.com/seedds/nxnative/blob/b4318c7a4d0bcbd16e7873ce63f33d344d1acbfb/dm/games/040074A01BF12000/geo_mesh.tsv) | 557 B | **Une paire** vertex/geometry, `f9c807930abd1234` / `5d537f7630ec3671`; commentaire sur ~600 draws géométrie/trame et les limitations de la bibliothèque Metal. **Lu.** | Fixture géométrie et contrat d'écriture GPU ; ne pas copier un shader Metal |
| [`pso_manifest.tsv`](https://github.com/seedds/nxnative/blob/b4318c7a4d0bcbd16e7873ce63f33d344d1acbfb/dm/games/040074A01BF12000/pso_manifest.tsv) | 1 833 428 B | Liste de préchauffage **déclarée** à 3 793 entrées : 1 726 shaders, 2 030 PSO raster, 37 compute. Lue **indirectement** via README. | Inventaire de **couverture**, mais PSO Metal **non réutilisables** en Vulkan et route de test non exhaustive |
| [`pso_pairs.tsv`](https://github.com/seedds/nxnative/blob/b4318c7a4d0bcbd16e7873ce63f33d344d1acbfb/dm/games/040074A01BF12000/pso_pairs.tsv) | 172 671 B | Paires vertex/pixel supplémentaires provenant entre autres de variations BAHS ; commentaires et début inspectés. | Fixtures de liaison vertex-fragment, sous contrôle des versions et interfaces |
| [`shader_facts.tsv`](https://github.com/seedds/nxnative/blob/b4318c7a4d0bcbd16e7873ce63f33d344d1acbfb/dm/games/040074A01BF12000/shader_facts.tsv) | 10 044 B | Faits JSON par clé compute : tailles locales `[x,y,z]`, mémoire partagée `shared`. **Lu.** | Rejouer décodeur QMD3/sizes/barrières, ne pas considérer ces faits comme du code de jeu |
| [`shader_map.tsv`](https://github.com/seedds/nxnative/blob/b4318c7a4d0bcbd16e7873ce63f33d344d1acbfb/dm/games/040074A01BF12000/shader_map.tsv) | 2 835 796 B | Table de correspondance des **22 852 shaders annoncés** par le README. **Lecture intégrale impossible** via connecteur. | Audit de couverture par clé/version/étage à faire localement si un accès aux octets devient disponible ; ne pas annoncer `22 852/22 852` pour Eden |
| [`shader_map.tsv.conflicts.tsv`](https://github.com/seedds/nxnative/blob/b4318c7a4d0bcbd16e7873ce63f33d344d1acbfb/dm/games/040074A01BF12000/shader_map.tsv.conflicts.tsv) | 110 B | En-tête uniquement : **aucun conflit enregistré dans cette table** au snapshot. **Lu.** | Contrôle du déterminisme des clés, sans prétendre absence d'autres défauts |
| [`shader_pairs.tsv`](https://github.com/seedds/nxnative/blob/b4318c7a4d0bcbd16e7873ce63f33d344d1acbfb/dm/games/040074A01BF12000/shader_pairs.tsv) | 529 738 B | Correspondances vertex/pixel BNSH, en-tête et premiers exemples lus. | Contrôler l'interface shader pair/pipeline, pipeline-cache et refus corrects |

**Règle pour ces tables :** un hash de shader ne prouve ni l'existence du shader dans notre dump, ni que le frontend Eden le traduit, ni qu'un `vkCmdDispatch` ou un dessin l'utilise. Il faut une chaîne : **version + octets d'entrée autorisés + décodage exact + IR valide + SPIR-V validé + pipeline Vulkan + exécution**, l'exécution réelle étant prouvée à P5.

### 3.1. Identité, version, modules, conteneurs

**[NX-F]** Titre `040074A01BF12000`, update **v458752**, SDK **20.5.19**, spécification **Ounce**, API **NVN2 231.30**, modules `main` et `sdk`, architecture shader Ampere/Volta **128 bits** (non Maxwell). Les builds de modules du profil sont associés à :

- `main=e25c90c1c136638885659fd55bf8a03b`
- `sdk=18265daea2105b31f25346adfbbd09b5`

Le contenu décrit est un dump `base/`, `updates/458752/`, `dlc/040074a01bf13001/`. Le RomFS **déjà patché** de l'update compte 80 273 fichiers (~8,6 Go) ; le DLC ~8 000 fichiers (~0,9 Go) est monté comme `EmeraldRush`. La mise à jour remplace des fichiers de base : **ne pas supposer** qu'un dossier `updates` ne contient que des deltas à empiler aveuglément. Un `romfs_marker` observé sert seulement de repère pour cette version.

**[EE-S]** Le socle Eden contient déjà ExeFS/NSO/NPDM NS2 et la prise en charge NUP V1 :

- [`headless/nup_v1_vfs.cpp`](https://github.com/niakw/ProsperoEden-Encore/blob/84c18e8cc70f1240a80d648bba5feaaafa0188fc/headless/nup_v1_vfs.cpp) vérifie l'en-tête NUP, les bornes TOC, la structure, le hachage SHA-256, des noms UTF-8, les fichiers raw/zstd, les limites d'accès et le bit `standalone_update`.
- [`headless/nup_v1_native_loader.cpp`](https://github.com/niakw/ProsperoEden-Encore/blob/84c18e8cc70f1240a80d648bba5feaaafa0188fc/headless/nup_v1_native_loader.cpp) et `nup_v1_native_aoc.cpp` couvrent le raccordement NUP/NACP/updates/AOC en code.
- [`vendor/encore-active/ns2-runtime/metadata/core/file_sys/program_metadata.cpp`](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/5fdbd61707b49cfa1fbdce220e0b96054610fd94/encore-active/ns2-runtime/metadata/core/file_sys/program_metadata.cpp) traite l'ACID étendu et `system_resource_size`.

**Écart réel à qualifier (P1.1) :** correspondance **version sélectionnée → modules ExeFS → RomFS complet de cette version → AOC → droits/NPDM**. Tester en positif et négatif avec fixtures synthétiques ; pas besoin de copier le packer `nxnative`, ni de déclarer NUP absent.

### 3.2. Mémoire et SDK `GetInfo`

| Donnée Bananza (`game.tsv`) | Valeur | Interprétation prudente |
| --- | --- | --- |
| `sys_resource` | `0x0` | NPDM sans ressource système déclarée ; le comportement du mode de mémoire virtuelle dépend du SDK invité |
| `app_pool` | `0x240000000` = **9 Gio** | Taille choisie pour la mémoire de jeu sur l'hôte natif, pas mesure automatique de la RAM PS5 disponible |
| `mem_reserve` | `0x270000000` = **9,75 Gio** | Réservation virtuelle du profil natif ; pas nécessairement une réservation identique pour l'émulateur |
| `mem_alias` | `0x10000000` = **256 Mio** | Zone d'alias hôte du profil |
| `mem_stack` | `0x10000000` = **256 Mio** | Zone stack du profil |
| `GetInfo` type `0x21` | Réponse `0x1000` sur l'hôte | Page size attendue dans le chemin `nn::ro::ProtectRelro` pour son masque d'alignement |
| `GetInfo` types `28–32` | AliasRegionExtraSize / régions distantes | Des valeurs dépendent de la gestion mémoire GPU substituée par `nxnative`; **ne pas reprendre des zéros sans prouver l'ABI d'Eden** |

**[NX-F]** Avec une réserve type NS1 (~3,2 Gio), la création `AudioSystemHeap` renvoyait `null` (`main+0x564b48`). Un `GetInfo 0x21` incorrect pouvait casser le RELRO et le démarrage bien avant la première commande graphique.

**[EE-S]** `program_metadata.cpp` stocke la taille `system_resource_size` et le noyau fournit une disposition mémoire NS2 12 Gio dans [`k_address_space_info.cpp`](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/5fdbd61707b49cfa1fbdce220e0b96054610fd94/encore-active/ns2-runtime/kernel/core/hle/kernel/k_address_space_info.cpp). Les wrappers [`svc.cpp`](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/5fdbd61707b49cfa1fbdce220e0b96054610fd94/encore-active/ns2-runtime/kernel/core/hle/kernel/svc.cpp) routent `GetInfo64` : leur présence **ne démontre pas** à elle seule la réponse du *cas type 0x21*. Le propriétaire réel de la résolution `InfoType` doit être suivi, puis testé.

**Action P1.2/P1.3 :** établir la matrice `InfoType × HOS × NPDM (sys_resource) × processus`, avec 0x21 et 28–32, vérifier réponse et échec, effet sur RELRO/remote memory, et conserver la sémantique NS1. Aucun `SetHeapSize` fictif ni augmentation automatique de la RAM physique PS5.

### 3.3. NVN2, identifiants de shader et format de contrôle

**[NX-F]** Les shaders sont dans `Shader/*.Nin_Ounce_NVN2.bfsha.zs` (BNSH), `Project.Nin_Ounce_NVN2.release.sarc.zs`, BAHS `agl` et le pack NDSR. Le format de section NVN2 observé comprend :

| Champ | Constat `nxnative` | Utilité chez nous |
| --- | --- | --- |
| En-tête contrôle | magic `0x98761234`, version `0xc9` | Identifier le décodeur correct, rejeter des paquets d'une autre version |
| `+0x38` | longueur instructions, SPH incluse | Taille réelle à capturer/traduire |
| `+0x40` | longueur arrondie à `0x100` | Contrôle d'alignement, ne pas confondre code et padding |
| `+0x44` | adresse/position de zone de code | Tracer le shader chargé à son adresse GPU exacte |
| `+0x4c` | nombre de registres | Pression registres / allègement / admission |
| `+0x58` | groupe de threads compute | Comparer aux métadonnées QMD3, vérifier dispatch |
| `+0x30` | longueur supplémentaire dans BNSH ; non universelle | Attention à la stabilité du hash : `nxnative` neutralise ce champ avant son propre calcul |

Le calcul de **clé** dans `nxnative` hash les premiers `0x48` octets (avec `+0x30` à zéro) puis le code ; ce schéma est un **index de son outil**, pas une autorité qui doit remplacer automatiquement la clé des caches Eden. Utile pour les rapprochements d'ISA à partir de dumps autorisés.

**[EE-S]** Notre décodage Ampere et le pont SPIR-V ont des propriétaires explicites dans `vendor/encore-active/ns2-runtime/ampere/`. Le blocage n'est plus « aucun compilateur Ampere », mais **la couverture des formes d'instruction et leur ABI sur le véritable pipeline**.

### 3.4. NDSR, réseau tensoriel, upscaling

**[NX-F]** `agl_ndsr.pck` regroupe **30 shaders** (3 vertex, 3 fragment, 24 compute), avec des instructions **HMMA, LDSM, MOVM** de réseau tensoriel. `nxnative` sait extraire les variantes et, selon l'étape et le format, remplacer le passage par une mise à l'échelle MetalFX ou exécuter certaines variantes tensoriellement accélérées via `simdgroup_matrix`.

**À ne pas conclure :** cette prise en charge **ne signifie pas** que « DLSS Neural Rendering sur RDNA2 » est intégré, que les sources du réseau peuvent être reproduites légalement, ou qu'un shader Metal est portable tel quel vers Vulkan. Les entrées/sorties de NDSR, espaces colorimétriques, history, buffers, synchronisations et sémantique du modèle doivent être audités séparément.

**Action P2 :** mesurer en fixtures *format + résolution source/destination + couches/rectangles + chaîne de barrières*, puis vérifier que les shaders invités sont traduits ou qu'un fallback **générique et fidèle** est explicitement déclaré. Les choix de performance/qualité sont des travaux ultérieurs, distincts de la complétude du socle.

---

## 4. Le plus utile : les sept causes d'absence ou de corruption d'image Bananza

La chronologie ci-dessous est **celle du rapport `nxnative` sur Mac**, **pas** un diagnostic direct d'une capture PS5 actuelle. Elle fournit cependant des **symptômes discriminants** et des chemins de code à auditer.

| Étape | Symptôme / cause remontée | Mécanisme général | Confrontation et action Eden |
| --- | --- | --- | --- |
| **R1** | Après l'échec du réseau upscaler, l'écran garde la couleur de clear bleue | Shaders tensoriels ou compute absents ; aucun passage final écrit la texture | **P2.4 :** traduction HMMA/LDSM/MOVM et liaison des ressources de sortie ; distinguer clear sans draw d'un `vkCmdDispatch` absent |
| **R2** | Six compute effects refusés | Adresse storage = base `c[0]` **plus** offset tiré de `c[1]`, mais l'ancien traducteur choisissait le mauvais opérande comme base | **P2.3 :** contrôler la provenance des deux termes, CBUF indirect, SSBO authentifiés, offset borné ; `GlobalMemoryToStorageBuffer` sans association inventée |
| **R3** | **Frame noire** : clear du composite exécuté alors qu'il devait être conditionnel | `SetRenderEnableConditional(RENDER_IF_NOT_EQUAL)` précédait `ClearColor` (`main+0x12798c` / `+0x1279d4`) | **P2.4 :** comparer la sémantique des render conditions **du moteur commun** ; ne pas ajouter un `render_cond on` spécial Bananza ; créer test « clear interdit conserve rendu antérieur » |
| **R4** | Taches noires/blanches, texels NaN | Lecture d'un mip de cube environnement au sein de sa chaîne de production, hazards image/subresource | **P2.2c :** barriers `layout/access`, aliases, suivi par sous-ressource, lecture/écriture mip, R11G11B10F ; refuser un patch qui cache les NaN sans régler les dépendances |
| **R5** | Rochers tissés et trous de géométrie | **Ordre des adresses à l'intérieur des GOB Switch 2** différent de l'hypothèse Tegra X1 ; BC7 normal map erronée, ASTC albedo de contrôle correcte | **P1.2/P2.2c :** fixtures block-linear NS1 et NS2, bpp, ASTC/BC7, mip/layer, adressage et cache. Ne pas changer globalement l'untile NS1 |
| **R6** | Géométrie/culling et ActionLibraryPass incomplets | `LEPC`, `OUT`, `ISBERD` nécessaires à shader géométrie `5d537f7630ec3671`; `MATCH` dans compute `7529699c7b7e49c0` | **P2.4 :** classes d'instruction + contrôle flux + émission de primitifs + programme/PC authentifié ; `LEPC` existe déjà de manière bornée chez nous, `ISBEWR` / Task-Mesh restent à couvrir |
| **R7** | Terrain absent : quelques pierres et personnage, mais murs/sol noirs | 400 draws indirects utilisent un record dont `instance_count=0`; shader vertex `c9a56f796ea4a4cd` doit écrire par pointeur **chargé depuis la mémoire** un record `{count=0, instance=1}`. Les stores perdus font gonfler le count et annulent la couleur | **P2.3/P2.4 très haut levier :** preuve que les stores à destination adressée indirectement atteignent **la mémoire GPU effective**, que leurs écritures sont publiées **avant** le lecteur indirect ; test « zéro instance ne dessine rien » + reset chaque trame |

### 4.1. Pourquoi R7 est un signal fort pour notre architecture

Un GPU peut être correctement initialisé, les shaders peuvent compiler, les textures peuvent être correctes, et **le terrain peut quand même ne jamais apparaître** si l'écriture qui remet l'instance count à `1` est perdue. C'est un bug d'**effet mémoire et de cohérence** ; un simple « augmenter la couverture opcode » ne suffit pas.

Sur le snapshot Eden :

- [`native_global_atomic_binding.h`](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/5fdbd61707b49cfa1fbdce220e0b96054610fd94/encore-active/ns2-runtime/ampere/shader_recompiler/frontend/ampere/native_global_atomic_binding.h) contient une réécriture de plusieurs atomiques globales **déjà implémentée** sous contraintes de descripteur et offset. **Ne pas la réécrire inutilement.**
- [`native_indirect_cbuf.h`](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/5fdbd61707b49cfa1fbdce220e0b96054610fd94/encore-active/ns2-runtime/ampere/shader_recompiler/frontend/ampere/native_indirect_cbuf.h) authentifie les **huit** banques Compute QMD3 réelles ; le collecteur Maxwell peut en avoir quatorze. **Ne jamais convertir 14 en 8 sur NS1.**
- [`spirv_emit_context.cpp`](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/5fdbd61707b49cfa1fbdce220e0b96054610fd94/encore-active/ns2-runtime/ampere/shader_recompiler/backend/spirv/spirv_emit_context.cpp) conserve un `NotImplementedException("Physical stores and transform feedbacks")` dans certaines formes de `DefineAttributeMemAccess`. Ce refus **ne prouve pas** à lui seul la cause de Bananza, mais constitue une frontière claire à documenter/tester.

**Tests hôte proposés** : un shader de vertex/geometry synthétique écrit un record de dessin indirect via un pointeur chargé en buffer ; le shader compute ou le draw suivant doit lire les octets attendus à la même adresse GPU, sous aliasing et invalidation ; les scénarios d'offset hors bornes échouent avant publication. Couvrir interqueue, barriers et lifetime. **Rendu PS5 et efficacité du terrain = P5.**

### 4.2. `render_cond` n'est pas un réglage « pour Bananza seulement »

Bananza, Mario Kart World et Splatoon Raiders décrivent tous une condition de rendu autour de certains clears, alors que le profil Fire Emblem Fortune's Weave n'en réclame pas dans son parcours. Cette comparaison soutient un **traitement sémantique des commandes de clear conditionnel** pour tous les jeux qui les émettent ; elle ne justifie ni un booléen forcé pour tous les NS2, ni le contournement des conditions d'un seul titre.

### 4.3. Le GOB NS2 ne doit pas casser NS1

`nxnative` a identifié son problème en comparant une texture ASTC 8×8 qui semblait correcte et une normale BC7 (`BaseRock000_Pnrm`) incorrecte, puis en essayant les permutations d'adressage **dans le GOB**. Ce résultat montre surtout qu'un shader se terminant correctement peut afficher du bruit de terrain à cause du *layout* de la texture. Il faut vérifier cette permutation contre le format, les octets et la génération du GMMU/tiling invités. **Ne pas remplacer sans preuve l'algorithme commun utilisé historiquement pour BOTW et FC27.**

---

## 5. Écarts de fonctions vérifiés dans le vendor actuel

La matrice suivante utilise les **chemins réellement présents**, et ne transforme pas un `NotImplemented` conditionnel en « tout le GPU manque ».

| Domaine et source Eden | Observation vérifiée | Conclusion audit | Qualification attendue |
| --- | --- | --- | --- |
| [`ampere_isa_table.h`](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/5fdbd61707b49cfa1fbdce220e0b96054610fd94/encore-active/ns2-runtime/ampere/shader_recompiler/frontend/ampere/ampere_isa_table.h) | entrée nommée **`0x927 Isbewr`** ; `0x593 SUATOM` ; `0x2a5 IMad64` | **Reconnaissance ISA ≠ sémantique exécutée** ; `ISBEWR` priorité forte | Identifier stage, masques et écritures, générer fixtures positives/négatives |
| [`lower_to_maxwell.h`](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/5fdbd61707b49cfa1fbdce220e0b96054610fd94/encore-active/ns2-runtime/ampere/shader_recompiler/frontend/ampere/lower_to_maxwell.h) | `0x593` traité (`SUATOM`) vers ~1734 ; `LEPC 0x34e` vers ~2044 ; `OUT 0x924` vers ~2086 ; aucune voie `0x927` ou `0x80d` repérée lors de l'inspection | **SUATOM/LEPC/OUT : ne pas compter absents.** `ISBEWR` et `CSMTEST` : lacunes à traiter, sans inventer résultat arbitraire | Vrais parcours IR, register/predicate/branch, `spirv-val`, tests des faux positifs |
| Même source, `LEPC 0x34e` | accepte prologue statique ATEXIT ou source PC authentifiée ; rejette PC dynamique non justifié | **Implémentation partielle prudente**, pas LEPC « inexistant » | Vérifier forme Bananza, adresses GPU et motifs du code ; pas de PC fabriqué |
| [`native_graphics_stage_policy.h`](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/5fdbd61707b49cfa1fbdce220e0b96054610fd94/encore-active/ns2-runtime/ampere/shader_recompiler/frontend/ampere/native_graphics_stage_policy.h) | admet VertexA/B, Fragment, Geometry, TessControl+TessEval liés ; **pas Task/Mesh** | **Gap stage réel**, critique pour les titres NVN2 qui l'utilisent (ex. MKW) | ABI task/mesh, payload, ressources, pipeline Vulkan et capabilities du GPU invité ; refus explicite tant qu'absent |
| [`native_qmd_compute_environment.h`](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/5fdbd61707b49cfa1fbdce220e0b96054610fd94/encore-active/ns2-runtime/ampere/shader_recompiler/frontend/ampere/native_qmd_compute_environment.h) | `NativeQmdResourcePlan` avec UBO/SSBO/images, `requires_tic_tsc`, validation mapping, staging/rollback ; commentaire sur vues TextureCache épinglées | **Infrastructure QMD3 présente**, source seulement ; formes d'images/SSBO à qualifier | Cas réels descripteurs TIC/TSC et SPIR-V, rights/strides/bounds/lifetime ; ne pas lancer dispatch si image non authentifiée |
| [`spirv_emit_context.cpp`](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/5fdbd61707b49cfa1fbdce220e0b96054610fd94/encore-active/ns2-runtime/ampere/shader_recompiler/backend/spirv/spirv_emit_context.cpp) | `DefineTextureBuffers` refuse `desc.count != 1` : **"Array of texture buffers"** | **Manque conditionnel confirmé**, potentiellement transversal | Test array count 1/2/N, indices dynamiques, type image, layouts SPIR-V, refus atomique si non supporté |
| Même source | `DefineAttributeMemAccess` peut lever **"Physical stores and transform feedbacks"** | **Manque conditionnel confirmé**, compatible avec risque de géométrie physique | Définir espaces mémoire/récepteur/ordering avant implémentation |
| [`gpu_dispatch/.../puller.cpp`](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/5fdbd61707b49cfa1fbdce220e0b96054610fd94/encore-active/ns2-runtime/gpu_dispatch/video_core/engines/puller.cpp) | `ProcessSemaphoreAcquire` porte le `TODO` **`acquire_timeout`** | **Manque source explicite** | Scénarios d'attente réussie, timeout, arrêt worker, fault et contention ; sûreté du thread GPU |
| [`native_ampere_macro_state.h`](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/5fdbd61707b49cfa1fbdce220e0b96054610fd94/encore-active/ns2-runtime/gpu_dispatch/video_core/native_ampere_macro_state.h) | MME Turing 96-bit, DRAM 0xC00, `ExecuteStaged`, validation/commit transactionnels | **MME existe**, ne pas faire une copie Maxwell aveugle | Test macro indirect + état de canal + rollback/failure poisoning |
| [`gpu_worker.cpp`](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/5fdbd61707b49cfa1fbdce220e0b96054610fd94/encore-active/ns2-runtime/gpu_session/core/hle/service/am/service/gpu_worker.cpp) | `CreateSparseRegion` traite `page_shift=12`, modes 0/1, et refuse certains cas `ResultNotImplemented` ; IPC 214/215/216 présents | **Partiellement implémenté, pas absent** | Matrice par commande/structure/handle, modes et codes d'erreur exacts, suite négative |
| [`k_address_space_info.cpp`](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/5fdbd61707b49cfa1fbdce220e0b96054610fd94/encore-active/ns2-runtime/kernel/core/hle/kernel/k_address_space_info.cpp) | mode de mémoire 12GB | **Propriété mémoire disponible en code** | Correspondance runtime au profil NPDM, budget réel, OOM/alias |
| [`headless/nup_v1_vfs.cpp`](https://github.com/niakw/ProsperoEden-Encore/blob/84c18e8cc70f1240a80d648bba5feaaafa0188fc/headless/nup_v1_vfs.cpp) | lecture NUP v1, contrôle des octets et du `standalone_update` | **NUP existe** | Tests version/base/update/DLC et VFS, pas ajouter second loader |

**Mise en garde sur le terme « compilé » :** le fichier peut appartenir au vendor actif sans que l'exécution guest d'une forme précise ait été prouvée sur console. Les garanties sont respectivement *source*, *tests hôte* puis *preuve PS5 P5*.

### 5.1. À ne pas repartir de zéro

- **QMD3 8 banques / 32 SSBO** : propriétaire actif déjà présent ; notre backlog du 06/11 décrit le raccordement `RasterizerVulkan::DispatchNativeCompute` et `vkCmdDispatch` en code. Le travail porte sur les variantes exactes et leur qualification.
- **Atomiques globaux et SUATOM** : voies présentes et contraintes ; vérifier compilation IR et tests source du lot Lichii, sans dupliquer de dispatcher.
- **LEPC et OUT** : traitement déjà présent mais restreint ; le vrai besoin est l'extension fondée sur des preuves, particulièrement pour Geometry et Task/Mesh.
- **NPDM/ExeFS et NUP** : présents ; comparer les cas spécifiques versions/fichiers/ABI.
- **GPU GMMU/NVMap et sparse** : base déjà présente ; renforcer les transactions, les barrières et le bout en bout, sans affirmer des résultats matériels non observés.
- **Counter NS1/NS2** : la roadmap décrit une sélection à **19,2 MHz NS1 / 31,25 MHz NS2** ; vérifier le SHA final plutôt que réimplémenter cette distinction.

---

## 6. Comparaison multi-jeux pour éviter le surapprentissage Bananza

| Jeu, version testée chez `nxnative` | Enseignements documentés | Intérêt / différence Eden |
| --- | --- | --- |
| [**Bananza**](https://github.com/seedds/nxnative/blob/b4318c7a4d0bcbd16e7873ce63f33d344d1acbfb/dm/games/040074A01BF12000/README.md), update `458752`, SDK 20.5.19, NVN2 231.30 | Clears conditionnels, 9Gio de pool profil, géométrie passthrough, store indirect → draw count, NDSR tensoriel | **Premier corpus de causalité de l'écran noir et de l'absence de terrain**. Ne vaut pas preuve PS5 |
| [**Mario Kart World**](https://github.com/seedds/nxnative/blob/b4318c7a4d0bcbd16e7873ce63f33d344d1acbfb/dm/games/0400C3F00006E000/README.md), base v0, SDK 19.3.3, NVN2 231.16 | **11 561 shaders**, dont **25 Task/Mesh (7+18)** ; **168 compute shaders à 48Kio shared memory** ; textures sparse de plusieurs Go ; race de stores et scène qui disparaît | **Task/Mesh** est plus qu'une possibilité théorique ; ressources GPU/sparse + synchronisation doivent être pris au sérieux. Version 1.8.0 **non testée en jeu** sur l'hôte rapporté |
| [**Splatoon Raiders**](https://github.com/seedds/nxnative/blob/b4318c7a4d0bcbd16e7873ce63f33d344d1acbfb/dm/games/0400380020056000/README.md), update `65536`, SDK 21.4.4, NVN2 231.39 | **27 195 shaders**, dont 27 192 compilent sur la chaîne citée ; alias virtuel 16Gio ; clears conditionnels ; ink targets, occlusion queries, coût copies/snapshots | Valide le caractère **transversal** du clear conditionnel et de la mémoire. Crash GPU non résolu sur une autre configuration Mac ; prudence sur « jouable » |
| [**Fire Emblem Fortune's Weave**](https://github.com/seedds/nxnative/blob/b4318c7a4d0bcbd16e7873ce63f33d344d1acbfb/dm/games/04007EF01F8AE000/README.md), v131072, SDK 22.2.0, NVN2 231.40 | **16 888 shaders** ; films AV1 ; compute histogram/tonemap et DLSS invité ; `sys_resource 64MiB` ; `render_cond` non retenu | Montre un autre mix services/graphisme, sans généraliser `render_cond` à toute NS2 ; matrices de codec et compute utiles |
| [**Zelda BOTW (NS1)**](https://github.com/seedds/nxnative/blob/b4318c7a4d0bcbd16e7873ce63f33d344d1acbfb/dm/games/01007EF00011E000/README.md), update 1.9.0 | Frame step, `gpu_timestamps segment`, tailles mémoire NS1, NVN Maxwell | **Témoin anti-régression** : conserver Maxwell/NS1 et vérifier les invariants temporels/texture/clear avant promotion d'un correctif partagé |

### Notes de fiabilité des sessions amont

- Le README Bananza annonce trois sessions d'environ cinq minutes et des parcours scriptés allant jusqu'à **15 900 frames** sur M4 Pro, dans les premières zones ; il **ne démontre pas** une compatibilité de tout le jeu ni d'iOS.
- MKW atteint une course 50cc dans le rapport, mais un [incident mémoire GPU #1193](https://github.com/seedds/nxnative/issues/1193) fait toujours l'objet d'un suivi : **un premier parcours n'est pas un soak test**.
- Les chiffres de performance Metal, délais de précompilation et VRAM Mac ne se transposent pas tels quels à la PS5 RDNA2.
- Certains paragraphes `Open` et les historiques de chaînes de traduction dans le README Bananza citent différentes révisions : par exemple un build complet annoncé **22 852/22 852** coexiste avec l'historique de **deux formes `0x593`** précédemment non traduites. Interpréter les chiffres avec leur **chaîne/version**, et ne pas écrire que les deux observations sont simultanément vraies au même commit.

---

## 7. Feuille de route d'exploitation des connaissances (sans chantier parallèle superflu)

**Ordre conservé : P0 → P1 → P2 → P4 ; preuve PS5 seulement P5.** La revue `nxnative` n'est pas un prétexte pour rouvrir P0.2, créer un autre renderer ou imposer un nouveau profil de build.

### Lot A — P0 : cohérence de la base et provenance

**But :** un couple `main/vendor` unique, une source moteur par responsabilité, validations reproductibles. Préserver les propriétaires existants.

- Épingler le SHA `nxnative` en **référence documentaire externe**, pas comme un sous-module exécutable nécessaire au runtime.
- Ajouter au dossier d'audit, hors binaires publics, une matrice *champ upstream → propriétaire Eden → test* ; ne pas embarquer les fichiers de jeu.
- Faire passer les checks obligatoires sur **le SHA final** : Core fast gate, Source preflight, NS2 host guards, tests de provenance et compatibilité NS1.

**Critère :** aucun test obsolète, pas de migration implicite de sources de `vendor`, état CI réellement consulté.

### Lot B — P1 : métadonnées, kernel, IPC, mémoire

**But :** dériver les contrats de SDK20 et SDK19/21/22 sans valeurs inventées.

| Sous-lot | Vérification hôte | Propriétaire présumé |
| --- | --- | --- |
| P1-NPDM | `sys_resource=0/32/64MiB` et validité metadata ACID, heap/alias selon titre ; NS1 inchangé | `metadata/program_metadata.cpp`, kernel memory |
| P1-SVC | `GetInfo 0x21` alignement RELRO, types 28–32, valeurs/handles/erreurs et combinaison avec processus NS1 | `kernel` + implémentation `GetInfo*` à localiser |
| P1-VFS | dossier `base/`, update complet, `standalone_update`, DLC et noms NACP ; pas de fuite entre titres | `headless/nup_v1_*`, loaders ExeFS |
| P1-IPC | boot `gpu_session/worker`, `graphics_supervisor`, VI2, nvdrv, audio et vidéo ; refuser commande hors ABI | `ns2-runtime/...`, HLE commun |
| P1-Memory | 4Kio pages GMMU, alias, backing GPU-only, OOM/rollback/sparse, droits d'accès | `nvdrv_as`, `gpu_worker`, cache GPU |

**Critère :** entrées valides et invalides testées, code d'erreur sans succès fictif, qualification HLE sur hôte ; **pas de PC invité PS5 exigé avant P5**.

### Lot C — P2.2c/P2.3 : shader ressources et cohérence indirecte

**But :** consolider ce qui existe plutôt que réécrire les composantes QMD3.

1. Revoir le schéma de stockage **`c[0] + c[1]`** identifié par Bananza dans les compute ; authenticité des deux sources, index de CBUF, registre, offsets et limites.
2. Tester **tableaux de texture buffers** et `desc.count>1` qui échouent actuellement en SPIR-V. Conserver le refus explicite tant que la représentation correcte n'existe pas.
3. Vérifier `Store Global` / `Atomic` / `Store Physical` et mise à jour de **draw indirect records** via pointeurs chargés ; rendre les writes visibles au consommateur au bon moment.
4. Rejouer le tuilage **GOB NS1/NS2** avec ASTC/BC7 et un test isolé de cube mip read-after-write, cohérent pour image+buffer.
5. Conserver/qualifier le dispatch déjà présent `QMD3 → SPIR-V → ComputePipeline → vkCmdDispatch` ; les ressources absentes doivent faire échouer le pipeline, jamais produire un succès de convenance.

**Critère :** tests du vrai code source, négatifs de GMMU/OOB/alias, modules validés par `spirv-val`, puis état de P2.3 réduit sur preuve. Les `shader_facts.tsv` peuvent servir d'**oracles de métadonnées**, si les octets du shader sont obtenus légalement.

### Lot D — P2.4/P2.7 : ISA, stages et synchronisation

**But :** clore les familles structurelles, indépendamment de Bananza.

- **D1 — ISA Ampere :** traiter `ISBEWR 0x927` et `CSMTEST 0x80d` en priorité, puis les formes restantes identifiées par recensement vrai. Le `0x593 SUATOM` est **déjà représenté en code**, mais sa compilation et ses tests du lot doivent être qualifiés avant « terminé ». Documenter pour chaque opcode bits décodés, contraintes de registre, predication, données et effets mémoire ; pas de « retour zéro » inventé.
- **D2 — Stages :** Task/Mesh est un vrai gap pour MKW, mais il requiert la spécification de ses liens, ressources, payloads et pipeline Vulkan. Geometry est **déjà admis** comme stage : concentrer l'analyse sur ses écritures physiques, culling et `ISBEWR/OUT/LEPC`.
- **D3 — MME et macro indirecte :** partir de `NativeAmpereMacroState::ExecuteStaged` et des handlers GPU réels, vérifier commandes, dépendances, transactions et rollback ; ne pas importer de backend Metal.
- **D4 — Sync :** combler la sémantique `acquire_timeout` dans `Puller::ProcessSemaphoreAcquire`, vérifier fences CPU/GPU, GPU writes avant lecture GPFIFO/indirect et arrêt worker propre.
- **D5 — Render conditions :** tester clear autorisé/refusé, z/stencil et passage shader qui consomme la target ; préserver comportement Maxwell.

**Critère :** chaque famille obligatoire a son décodeur, son IR validé, ses cas négatifs, son contrat de pipeline. *Une instruction inconnue reste refusée plutôt qu'acceptée faussement.*

### Lot E — P4 : préqualification et couverture source

- Exécuter `tools/ns2/qualify_host_batch.py --scope core --jobs 3` et les contrôles Clang/GCC/UBSan, NS1/NS2, Vulkan/SPIR-V, IPC/mémoire/loader, sur le couple final.
- Enregistrer le **résultat réel** et les SHA pour chaque test/CI ; éviter les anciennes matrices acquises sur un autre commit.
- Coupler les observations externes et les propriétaires testés, par exemple : `Bananza R7 / GlobalMemoryToStorageBuffer / indirect reset / test X` et `MKW task-mesh / stage pipeline / test Y`.
- Fermer P0/P1/P2/P4 selon la matrice propre à Eden, sans inventer une capture console.

**Critère :** reçus/CI du dernier SHA et suites négatives effectivement vertes ; seuls les problèmes matériel/jeux restent en P5.

### Séparément — P5 (ne conditionne pas la fermeture code des lots précédents)

Une fois le build console **explicitement autorisé**, classifier le pipeline invité de façon continue :

`ExeFS/NPDM → guest CPU/KProcess → SVC/GetInfo/IPC → NVDRV/GMMU/NVMap → GPFIFO + classe GPU → QMD3/3D → shaders/ressources → Vulkan draw/dispatch → VI2/present → guest_frame_handoff`.

La capture devrait distinguer :

| Observation | Ce qu'elle prouve | Ce qu'elle ne prouve pas |
| --- | --- | --- |
| Jeu identifié dans launcher | TitleID / métadonnées | CPU invité actif |
| NSO + `guest_run_begin` | Chargeur + lancement CPU | Commande GPU correcte |
| Vulkan initialisé | Backend disponible | Image invitée produite |
| GPFIFO / bind class 3D/Compute | Ordres envoyés et décodés | Pipeline exécuté et image écrite |
| `vkCmdDispatch` / draw soumis | Ordres Vulkan atteints | Ressources, barrières, contenu des pixels corrects |
| framebuffer invité + `guest_frame_handoff>0` | Premier rendu réellement repris par le front-end | Compatibilité de toute la partie, stabilité ou performances |
| Parcours/sessions réelles | Jeu capable de progresser | Absence de défauts des autres scènes |

**Baseline PS5 documentée avant cet audit :** NSO chargés, Vulkan et CPU invité initialisés sur Bananza/MKW ; `guest_frame_handoff=0` sur les essais précédents. Aucun nouvel essai console n'a été effectué dans cette revue, donc impossible de transformer ce constat historique en diagnostic du dernier code.

---

## 8. Proposition de corpus de diagnostics *sans* runtime par jeu

La meilleure imitation de `nxnative` pour Eden n'est pas `game.tsv` branché au launcher, mais un **corpus de preuve indépendant**, par exemple :

```text
# Proposition documentaire / outillage, non ajoutée dans les repos
research/upstream/nxnative/
  SOURCES.md                # SHA externe, licences, limites, liens
  title-cases.tsv           # TitleID, SDK, version, symptôme, invariants
  opcode-gap.tsv            # instruction, stage, forme, preuve, propriétaire Eden
  cases/
    040074A01BF12000.md    # Bananza : faits, R1..R7, preuves, tests hôte
    0400C3F00006E000.md    # MKW : Task/Mesh, sparse, 48 KiB shared
    01007EF00011E000.md    # BOTW : témoins de non-régression NS1
  coverage.md               # statut par famille de mécanismes, pas « support du jeu »
```

**Statuts recommandés :** `documenté amont`, `mappé sur source Eden`, `implémenté`, `test hôte passé`, `qualifié CI SHA`, `test console P5`. Cela évite la confusion actuelle entre intégration, compilation, compatibilité et optimisation.

**Exemple d'entrée :**

```tsv
titleid	mechanism	upstream_evidence	eden_owner	state	test_gate
040074A01BF12000	gpu_global_store_indirect_draw	README Rendering #7	ampere GlobalMemoryToStorageBuffer + Vulkan indirect	partiel	P2/P4 synthetic write-read-barrier
040074A01BF12000	conditional_clear	README Rendering #3	GPU render-condition + Vulkan pass	à qualifier	P2/P4 clear preserved on failed condition
0400C3F00006E000	task_mesh	README Shaders 25 stages	native_graphics_stage_policy + Vulkan pipeline	absent	P2/P4 stage and ABI
01007EF00011E000	legacy_maxwell	README + NS1 invariants	Maxwell renderer/CBUF	présent	P1/P4 no regression
```

Les tables de préwarm Mac ne doivent **pas** devenir une liste d'autorisation qui interdit un pipeline Vulkan absent de la liste. Elles représentent seulement les scènes observées et les shaders que l'outil a pu inventorier.

---

## 9. Recommandations de décisions, avec ce que l'audit ne démontre pas

### Décisions recommandées

1. **Ajouter `nxnative` aux références permanentes de veille technique NS2**, SHA figé dans les audits, avec comparaisons périodiques par familles et non fusion aveugle de commits.
2. **Réemployer immédiatement les faits Bananza dans les tests P2/P4** : global stores à adresses chargées et reset de draw indirect, clear conditionnel, cohérence GOB, `GetInfo 0x21`, NDSR et disposition compute.
3. **Traiter en priorité `ISBEWR 0x927` / `CSMTEST 0x80d`, puis les familles Task/Mesh**, en conservant les instructions déjà implémentées telles `SUATOM`/`LEPC` pour ne pas réintroduire de régressions.
4. **Faire vivre le comparatif sur le vrai couple main/vendor et les tests de cette paire**. Une issue ancienne indiquant « absent » peut être dépassée par une fonction réellement intégrée.
5. **Préserver le socle NS1** : les constantes 19,2 MHz, CBUF Maxwell à 14 banques virtuelles, NVN vs NVN2 et layout mémoire ne doivent pas subir une substitution globale.
6. **Séparer toute optimisation PS5/FSR/DLSS/MetalFX des déficits de correction du GPU invité** : le premier chantier est la sémantique, pas l'accélération.

### Ce que cette revue **ne** certifie **pas**

- Aucun passage du test Bananza/MKW sur la PS5, aucun framebuffer invité, aucune amélioration FPS, aucune consommation VRAM mesurée ; cela relève de P5.
- Aucun `22 852 / 22 852` de shaders convertis dans Eden, ni une compatibilité complète grâce à la seule existence des fichiers `shader_map.tsv`.
- Aucune validation exhaustive du code `nxnative` ou de tous les modules vendor : les fichiers retenus ont été **échantillonnés de façon ciblée**, pas compilés/benchés.
- Aucune raison d'intégrer un patch par jeu ou de coder une réponse HLE arbitraire si l'ABI ne la soutient pas.
- Aucun port direct du code Metal vers Vulkan, ni une justification suffisante pour distribuer des données propriétaires de jeux.

## 10. Sources principales pour vérification rapide

### `nxnative`

- [README / architecture](https://github.com/seedds/nxnative/blob/b4318c7a4d0bcbd16e7873ce63f33d344d1acbfb/README.md)
- [Bananza — README détaillé](https://github.com/seedds/nxnative/blob/b4318c7a4d0bcbd16e7873ce63f33d344d1acbfb/dm/games/040074A01BF12000/README.md)
- [Bananza — `game.tsv`](https://github.com/seedds/nxnative/blob/b4318c7a4d0bcbd16e7873ce63f33d344d1acbfb/dm/games/040074A01BF12000/game.tsv)
- [Bananza — `geo_mesh.tsv`](https://github.com/seedds/nxnative/blob/b4318c7a4d0bcbd16e7873ce63f33d344d1acbfb/dm/games/040074A01BF12000/geo_mesh.tsv)
- [Bananza — `shader_facts.tsv`](https://github.com/seedds/nxnative/blob/b4318c7a4d0bcbd16e7873ce63f33d344d1acbfb/dm/games/040074A01BF12000/shader_facts.tsv)
- [Recherche shaders, formats, Ampere, PSO](https://github.com/seedds/nxnative/blob/b4318c7a4d0bcbd16e7873ce63f33d344d1acbfb/docs/reference/shaders.md)
- [Objets NVN, GOB, sparse, buffers](https://github.com/seedds/nxnative/blob/b4318c7a4d0bcbd16e7873ce63f33d344d1acbfb/docs/reference/nvn-objects.md)
- [Rendu, barrières, conditions et passes](https://github.com/seedds/nxnative/blob/b4318c7a4d0bcbd16e7873ce63f33d344d1acbfb/docs/reference/rendering.md)
- [Services et API invités](https://github.com/seedds/nxnative/blob/b4318c7a4d0bcbd16e7873ce63f33d344d1acbfb/docs/reference/services.md)
- [Timing / compteur NS2](https://github.com/seedds/nxnative/blob/b4318c7a4d0bcbd16e7873ce63f33d344d1acbfb/docs/reference/frame-rate.md)
- [Vidéo / codecs](https://github.com/seedds/nxnative/blob/b4318c7a4d0bcbd16e7873ce63f33d344d1acbfb/docs/reference/movies.md)
- [Packer / NUP / RomFS](https://github.com/seedds/nxnative/blob/b4318c7a4d0bcbd16e7873ce63f33d344d1acbfb/docs/reference/packing.md)
- [Code du profil de jeu](https://github.com/seedds/nxnative/blob/b4318c7a4d0bcbd16e7873ce63f33d344d1acbfb/dm/games/game.py)
- [Licences des dépendances incluses](https://github.com/seedds/nxnative/blob/b4318c7a4d0bcbd16e7873ce63f33d344d1acbfb/dm/third_party/README.md)

### Eden Encore

- [Roadmap vivante #15](https://github.com/niakw/ProsperoEden-Encore/issues/15)
- [Backlog des fonctions P0–P4 (06/11)](https://github.com/niakw/ProsperoEden-Encore/blob/84c18e8cc70f1240a80d648bba5feaaafa0188fc/docs/NS2_FUNCTION_BACKLOG_2026-11-06.md)
- [Matrice P0–P4 / frontière P5](https://github.com/niakw/ProsperoEden-Encore/blob/84c18e8cc70f1240a80d648bba5feaaafa0188fc/docs/P0_P4_EXIT_MATRIX_2026-11-06.md)
- [Roadmap moteur unifié NS1/NS2](https://github.com/niakw/ProsperoEden-Encore/blob/84c18e8cc70f1240a80d648bba5feaaafa0188fc/docs/ROADMAP_NS1_NS2_UNIFIED.md)
- [Audit des boots historiques](https://github.com/niakw/ProsperoEden-Encore/blob/84c18e8cc70f1240a80d648bba5feaaafa0188fc/docs/NS2_UPSTREAM_BOOT_GAP_AUDIT.md)
- [Inventaire des sources actives dans vendor](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/5fdbd61707b49cfa1fbdce220e0b96054610fd94/encore-active/README.md)

---

**Conclusion :** `nxnative` est surtout **un corpus remarquable de preuves par jeu et de diagnostics GPU/SDK**. Pour Eden Encore, cette documentation est **conservée pour les optimisations après le premier build fonctionnel de P5** : les cas Bananza R2/R3/R5/R6/R7 et MKW Task/Mesh/sparse formeront des références à requalifier sur la version alors courante du moteur commun, sans dupliquer les éléments déjà intégrés. Le prochain décompte fiable doit être un **décompte de formes ISA/ABI obligatoires non couvertes**, et non simplement le nombre d'opcodes nommés ou de fichiers.
