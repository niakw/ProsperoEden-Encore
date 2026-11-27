# Eden Encore — architecture technique, composants, sources et recherche

> **Dossier mémoire invité NS1/NS2 — 23 novembre :** [architecture détaillée, sources publiques/propriétaires, ressources PS5 et P0 FC27/MKW/Bananza](EDEN_ENCORE_GUEST_MEMORY_NS1_NS2_PS5_ARCHITECTURE.md). Ce dossier complète la section 5.3, sans certifier le boot ni la fluidité.

> **Complément ciblé NS2/PS5 du 23 novembre 2026 :** la section [5.3](#53-cas-ns2--architecture-mémoire-sur-ps5-état-du-23112026) décrit l'écart réel entre notre backing sparse pré-engagé et le `demand-zero` d'EglantinePS5. Couple étudié : moteur `3349171e` / vendor `7bf93eb2`. Les crashs ExeFS MKW/Bananza restent P0 et aucune première frame invitée n'est validée. La photographie historique du 19 novembre ci-dessous n'est pas réécrite.

> **Actualisation du 19 novembre (sans modifier l'architecture de référence) :** le correctif historique de table A64 PS5 réduite à 64K entrées ne fait **plus partie du chemin natif validé à la compilation**. Il a été retiré après un défaut de disposition C++ entre unités de traduction ; vendor `8e564f61` puis `67759611` conservent la table uniforme 16 MiB. Le build natif moteur `4a5b8cc` l'atteste en ELF ; le test PS5 FC27/MKW/Bananza atteint l'entrée invitée sans garantir les premières frames NS2. Les sections JIT doivent être lues avec le [registre de l'incident](audits/PS5_R457_CC8044CE_P0_CROSS_TITLE_A64_JIT_SIGSEGV_2026-11-19.md) et le [suivi du 19 novembre](audits/PS5_R457_2026-11-19_FC27_NS2_POST_TEST.md). Le correctif upstream Lichii #159 sur l'index RomFS zéro est dorénavant intégré aux deux sources sélectionnées, mais la réussite du boot NS2 n'est pas prouvée.


> **Document de référence — 19 novembre 2026.** Architecture commune Nintendo Switch 1 / Nintendo Switch 2 portée sur PlayStation 5 (firmware de test 13.60).
> **Moteur :** [niakw/ProsperoEden-Encore](https://github.com/niakw/ProsperoEden-Encore) ; **vendor :** [niakw/Prospero.Eden-Encore-vendor](https://github.com/niakw/Prospero.Eden-Encore-vendor).
> **Instantané examiné :** moteur <code>cc8044cee42ad0e74af4edadaac6595de9128c31</code> ; gitlink vendor / vendor main <code>6c38328fbef33de747f5c31ea30d13541a513a4a</code>. Les pointeurs évoluent après publication de ce document ; vérifier les Gitlinks et CMake avant chaque diagnostic.
>
> **Objet :** expliquer les couches, la circulation des données, les composants et leurs responsabilités, leurs chemins dans les DEUX dépôts, les risques de correction/optimisation, les sources officielles et la littérature académique pertinente.
>
> **Limite :** une présence de fichiers, de déclarations ou de tests hôtes n'est pas une preuve d'exécution PS5. Une compilation native n'est ni un boot NS1/NS2, ni une image invitée, ni une réduction de saccades. Ce document est une **carte de référence**, non une certification d'implémentation exhaustive ni un changelog des états CI.

**Registre opérationnel NS2 (actualisé au 23/11) :** [complétude SwitchBrew et parité structurelle Lichii](audits/EDEN_ENCORE_NS2_IMPLEMENTATION_COMPLETENESS_REGISTER_2026-11-21.md). Le document architectural ci-dessous est une photographie historique ; pour l'état des commandes, stubs et écarts Lichii, consulter les compteurs séparés de ce registre, à SHAs datés.

## Sommaire

1. [Convention et périmètre](#1-convention-et-périmètre)
2. [Vue d'ensemble et flux d'exécution](#2-vue-densemble-et-flux-dexécution)
3. [Inventaire des composants centraux](#3-inventaire-des-composants-centraux)
4. [Architecture CPU, Dynarmic et JIT](#4-architecture-cpu-dynarmic-et-jit)
5. [Mémoire, allocations et cohérence](#5-mémoire-allocations-et-cohérence)
6. [Architecture GPU invitée Maxwell / Ampere](#6-architecture-gpu-invitée-maxwell--ampere)
7. [Recompilation des shaders et pilotes hôtes](#7-recompilation-des-shaders-et-pilotes-hôtes)
8. [Caches textures, rendu, synchronisation et présentation](#8-caches-textures-rendu-synchronisation-et-présentation)
9. [HLE, kernel, fichiers, services et formats](#9-hle-kernel-fichiers-services-et-formats)
10. [Audio, vidéo, interfaces et fonctions annexes](#10-audio-vidéo-interfaces-et-fonctions-annexes)
11. [Architecture des dépôts et de la compilation native](#11-architecture-des-dépôts-et-de-la-compilation-native)
12. [Contrats transversaux et observabilité](#12-contrats-transversaux-et-observabilité)
13. [Guide de diagnostic par symptôme](#13-guide-de-diagnostic-par-symptôme)
14. [Documentation primaire et officielle](#14-documentation-primaire-et-officielle)
15. [Recherches scientifiques et analyses externes](#15-recherches-scientifiques-et-analyses-externes)
16. [Programme d'investigation et de validation](#16-programme-dinvestigation-et-de-validation)
17. [Autres documents internes, glossaire et maintenance](#17-autres-documents-internes-glossaire-et-maintenance)

## 1. Convention et périmètre

- **S = source constatée** : arborescence ou fichier retrouvé sur le couple de révisions indiqué. Cela n'affirme pas que le code est sélectionné par le build.
- **I = implémentation intégrée à vérifier** : code/override associé à l'exécution, dont la sélection exacte doit être démontrée par CMake, symboles et tests.
- **A = architecture invitée / norme** : propriétés du matériel Nintendo ou du modèle d'exécution à émuler ; pas nécessairement une bibliothèque compilée.
- **R = référence de recherche** : document, projet ou technique pouvant guider le développement, mais ne prouvant aucune intégration.
- **H = preuve hôte** : test C++/Python, émulateur ou Vulkan hôte ; **N = build natif PS5** ; **C = validation réelle en console**.
- **P0** : crash, OOM, deadlock, non-démarrage NS1/NS2 et mémoire ; **P1** : shaders, latence, GPU, HUD, audio/vidéo et performances ; **P2** : launcher, UX, métadonnées ; **P3** : maintenance et hygiène.

Racines utilisées ci-dessous :

- <code>E/</code> = racine du dépôt moteur ;
- <code>V/</code> = racine du dépôt vendor épinglé (sous-module <code>E/vendor</code>) ;
- <code>V/sources/eden/</code> = photographie amont Eden ;
- <code>V/encore-active/</code> = sources/adaptations maintenues d'Encore ;
- <code>E/headless/</code> et <code>E/src/</code> = adaptation applicative/host PS5 ;
- <code>E/encore-overrides</code> = sous-module séparé de profils/données, **pas** l'endroit où modifier les C++ du moteur.

### Principes non négociables

1. **Une application PS5, un seul moteur de production/test** : pas de variante utilisateur gouvernée par un sélecteur « EXPERIMENTAL » ; les protections de validité, les backends nécessaires et les tests peuvent rester distincts.
2. **Deux architectures invitées réellement distinctes** : mutualiser les contrats CPU/HLE/cache/mémoire sans prétendre que les instructions, descripteurs QMD ou services spécifiques Ampere sont Maxwell.
3. **Upstream avant patch** : pour tout défaut, rechercher commits/PR/issues ouverts et fermés chez Eden, Eglantine, Lichii, nxnative, ports PS5, Yuzu/Ryujinx/Citron/Sudachi/Suyu et dépendances officielles. Vérifier la licence et la parité causale.
4. **Un seul propriétaire source maintenu** par adaptation : garder les snapshots tiers épinglés ; sélectionner explicitement les fichiers dans le build ; pas de correction cachée dans une substitution de chaîne CMake.
5. **Mesurer le chemin critique** plutôt que d'optimiser sur le pourcentage CPU/GPU, la taille d'un cache ou le seul FPS moyen.
6. **Aucun état de succès inventé** : source intégrée, hôte, build natif, installation, démarrage, première image et gameplay mesuré sont sept faits différents.

## 2. Vue d'ensemble et flux d'exécution

~~~mermaid
flowchart TB
  UI["Application native PS5<br/>Launcher, jeux, profils, HID, logs"] --> BOOT["Chargement NSP/XCI/NCA/ExeFS<br/>NRO/NSO, NPDM, clés/firmware"]
  BOOT --> GUEST["Processus invité NS1 ou NS2<br/>CPU ARM et services Horizon"]
  GUEST --> CPU["Dynarmic / JIT A64-A32<br/>vers x86-64 Zen 2"]
  GUEST --> HLE["HLE / SVC / IPC / kernel / FS<br/>AM, HID, NVDRV, VI, Audio"]
  GUEST --> GPU["Moteur GPU invité<br/>Maxwell NS1 / Ampere NS2"]
  GPU --> SH["Recompiler shader<br/>frontend ISA -> IR -> SPIR-V"]
  GPU --> RESOURCE["Buffers / textures / DMA<br/>GMMU, ASTC, cohérence"]
  SH --> VK["Vulkan PS5 / RADV / Mesa<br/>NIR / ACO et commandes AMD"]
  RESOURCE --> VK
  VK --> PRESENT["Swapchain / present / timing<br/>FSR / AA / frame metrics"]
  HLE --> AUDIO["AudioCore / Opus / décodage vidéo<br/>FFmpeg, sinks et surfaces"]
  CPU --> HOST["Runtime PS5 / SDK<br/>threads, mémoire, CRT"]
  HLE --> HOST
  VK --> HOST
  PRESENT --> UI
~~~

### Parcours de démarrage

1. Le launcher ouvre le contenu, détermine l'identité du jeu, les capacités, la génération NS1/NS2, la configuration, le firmware et les éventuelles données de profils.
2. Le loader lit les en-têtes, segments ExeFS/NSO/NRO et métadonnées ; le kernel émulé crée le processus et ses threads ; les cartes mémoire invitées sont initialisées.
3. Dynarmic traduit les blocs ARM et les exécute sur le CPU x86-64 de la PS5. Les appels SVC/IPC passent par le kernel et les services HLE. Les appels de GPU produisent des commandes et accès mémoire invités.
4. Le sous-système GPU interprète la génération NVIDIA appropriée, traduit l'état et les programmes shaders, construit les buffers/images/pipelines Vulkan ou OpenGL, puis présente la frame.
5. Audio, vidéo et HID opèrent en parallèle. Le temps d'affichage n'est pas un témoin suffisant de progression réelle du CPU invité ou de la fraîcheur du HUD.

### Frontières à ne pas confondre

| Frontière | Invariant à respecter | Exemple d'échec |
|---|---|---|
| Loader → mémoire invité | Adresse, taille, droits et segments corrects | Écran noir avant toute commande GPU |
| ARM invité → Dynarmic | Sémantique ISA et atomiques identique | Blocage du jeu, crash tardif |
| Guest CPU ↔ HLE/IPC | Réponse IPC et réveil de thread corrects | Pause à retardement / chargement infini |
| GPU invité → recompiler | Décodage exact des instructions/stages | « Stage not implemented », shader faux |
| Shader IR → SPIR-V | Validation, capacités, layout et décorations exactes | Échec de création pipeline |
| Cache GPU ↔ mémoire invitée | Version des données et ordre des invalidations | HUD/texte ancien ou partiellement affiché |
| Vulkan → RADV/PS5 | Extensions réellement disponibles, synchronisations et allocations | GPU perdu, stale present, deadlock |
| GPU present → launcher | Pas de présentation d'une ancienne frame comme preuve de progrès | Animation de chargement active, jeu figé |

## 3. Inventaire des composants centraux

### 3.1 CPU et système

| Composant | Nature | Rôle et emplacement d'entrée |
|---|---|---|
| ARMv8-A / AArch64 | A | ISA des processus invités ; <code>V/sources/eden/src/core/arm/</code> |
| AArch32 | A/S | Compatibilité ARM 32 bits ; <code>src/dynarmic/</code>, fastmem |
| Dynarmic | S/I | JIT ARM → hôte ; <code>V/sources/eden/src/dynarmic/</code> |
| Dynarmic IR / frontend | S | Décodage et transformation de blocs ; sous-arbre <code>src/dynarmic/src/dynarmic/</code> |
| Backend x64 | S | Émission native PS5, allocation de registres ; <code>V/encore-active/eden-core/src/dynarmic/backend/x64/</code> |
| Xbyak | S | Encodeur JIT x86-64 ; <code>V/encore-active/eden-build/third_party/xbyak/</code> |
| JIT cache / code invalidation | S/I | Durée de vie des blocs, alias RX/RW ; <code>E/headless/jit-*</code> |
| CPU manager / core timing | S | Ordonnancement et horloge invités ; <code>src/core/cpu_manager.*</code>, <code>core_timing.*</code> |
| Kernel HLE / SVC | S | Threads, processus, waits, sémaphores ; <code>src/core/hle/kernel/</code> |
| IPC / CMIF / services | S | Messages système Horizon ; <code>src/core/hle/service/</code> |
| HID | S | Contrôleurs invités ; <code>src/hid_core/</code> et <code>E/headless/</code> |
| NPDM / ExeFS / NSO loader | S | Initialisation, caps, segments ; <code>src/core/loader/</code> |
| Crypto / clés / NCA | S | Déchiffrement et reconnaissance du contenu légalement fourni ; <code>src/core/crypto/</code>, <code>file_sys/</code> |

### 3.2 GPU et présentation

| Composant | Nature | Rôle et emplacement d'entrée |
|---|---|---|
| NVIDIA Maxwell / Tegra X1 | A | GPU invité NS1 ; <code>src/video_core/engines/</code> |
| NVIDIA Ampere / T239 | A/S | GPU invité NS2 ; <code>V/encore-active/ns2-runtime/ampere/</code> |
| Fermi 2D | S | Moteur de copie et blit ; <code>engines/fermi_2d.*</code> |
| Maxwell 3D | S | Registres, draws, état 3D ; <code>engines/maxwell_3d.*</code> |
| Maxwell DMA | S | Copies GPU / transfert mémoire ; <code>engines/maxwell_dma.*</code> |
| Kepler compute / memory | S | Moteurs issus des dénominations NVIDIA ; <code>engines/kepler_compute.*</code>, <code>kepler_memory.*</code> |
| host1x / CDMA / pusher | S | Canal de commandes, FIFOs, synchronisation ; <code>video_core/host1x</code>, <code>dma_pusher.*</code> |
| GPU scheduler / GPU thread | S | Ordre de travail et réveils ; <code>video_core/gpu_thread.*</code> |
| GMMU / GPU memory manager | S | Traduction d'adresses et mappages GPU ; <code>video_core/memory_manager.*</code> |
| Shader Recompiler | S | Traduction programmes GPU ; <code>src/shader_recompiler/</code> |
| SASS / instructions Maxwell | A/R | ISA NVIDIA à analyser ; le format réel du shader invité n'est **pas** PTX |
| SPIR-V / GLSL / GLASM | S | Langages/intermédiaires backend ; <code>src/shader_recompiler/backend/</code> |
| Vulkan | S | Backend graphique PS5 ; <code>src/video_core/renderer_vulkan/</code> |
| OpenGL | S | Route graphique indépendante ; <code>src/video_core/renderer_opengl/</code> |
| Mesa / RADV | S | Pilote Vulkan AMD adapté ; <code>V/sources/ps5-mesa/</code> |
| NIR / ACO / LLVM AMD | S/R | IR et compilateurs Mesa ; <code>V/sources/ps5-mesa/src/amd/</code> |
| Vulkan pipeline / descriptors | S | Pipeline cache, descriptors, shader objects ; <code>renderer_vulkan/vk_*pipeline*</code> |
| TextureCache / BufferCache | S | Résidence images et buffers, invalidations ; <code>video_core/texture_cache/</code>, <code>buffer_cache/</code> |
| ASTC / BCn / swizzle | S | Formats et chargements de textures ; <code>video_core/textures/</code>, <code>V/encore-active/ns2-astc/</code> |
| Fences / timeline / swapchain | S | Publication et affichage ; <code>renderer_vulkan/vk_fence_manager.*</code>, <code>vk_swapchain.*</code> |
| Frame generation / FSR / SGSR | S/R | Reconstruction et interpolation ; <code>video_core/frame_gen/</code>, <code>V/encore-active/eden-vulkan/</code> |
| Anime4K / R09 neural | S/I | Chaînes de reconstruction IA ; <code>V/encore-active/eden-vulkan/nr_rdna2_*</code> |
| CUDA / PTX / Tensor Cores NVIDIA | R/A | Documentation invitée et modèles de calcul ; **pas** une dépendance CUDA native PS5 |

### 3.3 Services, UI et outils

| Composant | Nature | Emplacement / rôle |
|---|---|---|
| AudioCore / ADSP / Opus / sink | S | <code>V/sources/eden/src/audio_core/</code>, audio HLE et restitution |
| NVDEC / vidéo décodée | A/S | <code>V/encore-active/ns2-runtime/video_decoder/</code>, surfaces et FFmpeg |
| FFmpeg | S | <code>V/sources/ffmpeg/</code>, codecs et décodage |
| AM / VI / NVDRV / NVMap | S | <code>src/core/hle/service/{am,vi,nvdrv,nvnflinger}/</code> |
| RomFS / ExeFS / NCA / VFS | S | <code>src/core/file_sys/</code>, <code>src/core/loader/</code> |
| Zstandard / LZ4 / ZBIC | S/R | Formats et codecs pris en charge selon voie de lecture ; <code>V/sources/zbic</code> et dépendances |
| DualSense / HID / overlay | S | <code>E/headless/</code>, <code>src/hid_core/</code> |
| Launcher / bibliothèque / profils | S | <code>E/headless/prosperoeden/</code>, <code>E/encore-overrides</code> |
| HarfBuzz / fontes / glyphes | S | <code>V/sources/harfbuzz</code>, <code>E/third_party/fonts</code> |
| WebP / JXR | S | <code>V/sources/libwebp</code>, <code>jxrlib</code>, <code>V/encore-active/jxrlib/</code> |
| PS5 Payload SDK / CRT | S | <code>V/sources/ps5-payload-sdk-fork/</code>, <code>E/headless</code> |
| Clang / LLD / compiler-rt | S/R | Toolchain et runtime natif ; <code>V/sources/compiler-rt</code>, overrides |
| CMake / Ninja / CI | S | <code>E/headless/CMakeLists.txt</code>, <code>E/Makefile</code>, <code>.github/workflows/</code> |
| Tests / fixtures / CodeQL | S | <code>E/tests/</code>, <code>E/tools/verify/</code>, <code>E/.github/</code>, <code>V/tests/</code> |

**Ne pas assimiler les noms hérités des générations NVIDIA** (Fermi/Kepler/Maxwell) à plusieurs cartes graphiques physiques dans la console : ce sont des familles de moteurs/instructions historiquement nommées dans l'implémentation.

## 4. Architecture CPU, Dynarmic et JIT

### 4.1 Chaîne de traduction

~~~mermaid
flowchart LR
  ARM["Instructions ARM A64/A32"] --> DEC["Décodage frontend<br/>Dynarmic"]
  DEC --> IR["IR / passes<br/>optimisation"]
  IR --> X64["Backend x86-64<br/>Xbyak"]
  X64 --> CACHE["Cache code natif<br/>RX/RW et invalidation"]
  CACHE --> ZEN["CPU Zen 2 PS5"]
  ARM --> SVC["SVC / IPC invités"]
  SVC --> HLE["Kernel HLE"]
~~~

Fonctions critiques à inspecter : création/destruction des blocs, invalidation par pages, allocateur de registres, backend A64/A32, gestion de TLS, code executable, interruptions et transitions SVC. La bonne stratégie dépend de la correction de la traduction et des barrières mémoire, non d'un nombre arbitraire de threads.

### 4.2 Contrats de correction

- **ISA et ABI** : registres, flags, NEON, division, arrondis, exceptions, PC/SP, convention d'appel et A32 ne peuvent pas être approximés silencieusement.
- **Atomiques** : comparer acquire/release, exclusives ARM, accès alignés, mémoire partagée avec le GPU et ordering hôte x86-64.
- **Code auto-modifié** : une écriture invitée invalidant du code doit invalider les traductions correspondantes ; aucune exécution d'un bloc libéré.
- **Alias W^X** : les deux vues virtuelles RX/RW et la mémoire physiquement engagée doivent conserver la sécurité et la validité des pointeurs.
- **Invalidation concurrente** : ne récupérer le backing qu'après quiescence, absence de lecteurs actifs et retrait de références.
- **Sparse allocation** : capacité virtuelle, pages engagées et mémoire disponible du processus PS5 sont des grandeurs différentes.
- **Affinité CPU** : distinguer identifiants logiques, cœurs physiques et droits réels du processus, puis mesurer les files et la latence.

### 4.3 Sources locales à ouvrir

- [Dynarmic upstream incorporé](https://github.com/niakw/Prospero.Eden-Encore-vendor/tree/main/sources/eden/src/dynarmic)
- [Dynarmic overrides](https://github.com/niakw/Prospero.Eden-Encore-vendor/tree/main/encore-active/eden-core/src/dynarmic)
- [JIT natif](https://github.com/niakw/ProsperoEden-Encore/tree/main/headless)
- [Mémoire fastmem](https://github.com/niakw/ProsperoEden-Encore/tree/main/src)
- [Architecture JIT différée](DEFERRED_JIT_QUIESCENCE_ARCHITECTURE_2026-10-17.md)
- [Cartographie CPU/JIT](EDEN_CPU_JIT_G11_G12_MIGRATION_MAP.md)
- [Revue CPU/GPU/JIT](INTEGRATION_AUDIT_CPU_GPU_JIT_2026-10-14.md)

**Optimisations envisageables seulement sous preuve** : lookup de traduction moins coûteux, réduction de contention par page, emplacement des workers sur le chemin critique, cache dimensionné sur traces, réduction du nombre de recompilations. **À ne pas activer par intuition** : traduction spéculative, JIT partagé inter-cœurs, invalidation différée sans protocole prouvé.

## 5. Mémoire, allocations et cohérence

### 5.1 Domaines distincts

| Domaine | Propriétaire | Risque concret |
|---|---|---|
| RAM physique processus PS5 | SDK / allocateur hôte | Échec de réservation/engagement ; fragmentation |
| Adresse virtuelle PS5 | OS/ABI | Réservation réussie mais backing absent |
| RAM invitée NS1/NS2 | Core memory / sparse guest | Pages invisibles, faux OOM, mauvais droits |
| Code JIT | Dynarmic + alias RX/RW | RX/RW incohérents, invalidation et corruption |
| GMMU / NVMap GPU | GPU memory / NVDRV | Traduction d'adresses, durée de vie des mappings |
| Allocations Vulkan | RADV / Vulkan memory | Heap exhaustion, staging et images |
| Cache textures/buffers | VideoCore | Rétention, duplication, éviction trop tôt |
| Readback / uploads | Staging pools | Allocations temporaires et fences in-flight |
| Audio/vidéo | Buffers décodés | Pics de mémoire et buffers bloqués |
| UI / jaquettes | Launcher / assets | Fuites ou chargements en pointe |

### 5.2 Pipeline mémoire à suivre

~~~mermaid
flowchart LR
  GH["RAM invitée"] --> GM["GMMU / NVMap"]
  GH --> JIT["CPU / Dynarmic"]
  GM --> BC["BufferCache / TextureCache"]
  BC --> ST["Upload / staging"]
  ST --> VK["VkBuffer / VkImage / RADV"]
  VK --> PR["GPU queue / fence / present"]
  PR --> RET["Retirement / eviction"]
~~~

**Erreur fréquente** : un compteur de mémoire libre important n'exclut pas un échec d'allocation dû à la taille continue exigée, aux droits, aux quotas, à un pool dédié ou à la fragmentation.

**Mesures minimales** : committed guest, reserved guest, committed JIT, maximum contiguous block, GPU heap budget/usage, nombre et somme des buffers persistants, staging in-flight, point de retraite GPU, nombre/tailles des allocs échouées et première erreur causale.

### 5.3 Cas NS2 — architecture mémoire sur PS5, état du 23/11/2026

**Révision opérationnelle distincte de l'instantané du 19/11 :** moteur `3349171e46d7bbf0545edfa75532e3eafaeb1d34`, gitlink/vendor `7bf93eb2da720281a09edd8f7d823fb2558ad937`. Comparaison PS5 : [heydemoura/EglantinePS5 `5eb70367ffde039f237b3b828856f4b4247ea09e`](https://github.com/heydemoura/EglantinePS5/tree/5eb70367ffde039f237b3b828856f4b4247ea09e), 20/11/2026. Référence de *structure* et protocoles NS2 : Lichii, à distinguer de cette référence de *gestion des ressources PS5*. **Statut : problème P0 ouvert, pas de boot NS2 ni de première frame validés par ce complément.** Les SHAs datés sont des références de comparaison, pas une instruction de revenir dessus.

#### 5.3.1 Propriétaires C++ réellement compilés

| Domaine | Source exacte / sélection | Garantie existante et limite |
|---|---|---|
| Choix du layout | `vendor/encore-active/ns2-runtime/process/core/core.cpp` | Détection NPDM NS2 avant création du noyau ; sélection du layout invité **12 Gio** sur les programmes détectés, y compris NUP lisible. Un NUP rejeté au parseur n'atteint pas nécessairement cette détection |
| RAM invitée PS5 | `src/host_memory.cpp`, `Common::HostMemory::Impl` | Pour `requested == 12ull << 30`, réserve **12 Gio d'adresses virtuelles** via `Eden::PS5::GuestBacking::Runtime`, avec budget physique actuel **6 Gio**. Le layout 12 Gio n'est **pas** une allocation physique dense |
| Plan/ownership | `headless/ps5_ns2_guest_backing_plan.h`, `src/ns2_sparse_guest.cpp` | Granules physiques de **2 Mio**, admission et publication sous verrou, rollback des granules nouvellement mappés en cas d'échec ; conservation jusqu'à destruction du runtime. Pas de libération générale des granules lorsque le noyau invité rend ses pages |
| Clear mémoire | `src/host_memory.cpp::HostMemory::ClearBackingRegion` | Vérifie les bornes, exécute `sparse->Commit(offset,length)`, puis `memset`. **Même un remplissage à zéro engage les granules** : il n'existe pas encore de véritable état `Zero` physique partagé |
| Noyau physique NS2 | `vendor/encore-active/ns2-runtime/sparse-residency/core/hle/kernel/k_memory_manager.cpp` | Les écritures hors PTE passent par `EdenNs2CommitGuestBacking` ; `AllocateForProcess` intercepte désormais le `bad_alloc` provenant du `ClearBackingRegion` non optimisé, rend ses pages non référencées aux pools et renvoie `ResultOutOfMemory` |
| Shared/slab et publication | `vendor/encore-active/ns2-runtime/sparse-residency/core/hle/kernel/k_shared_memory.cpp` et `init/init_slab_setup.cpp` | Pré-engagement avant les écritures directes historiques ; ce n'est pas une implémentation demand-zero |
| Accès invité/vidéo | `vendor/encore-active/ns2-runtime/nvdrv_as/`, `nvdrv_gpu/`, `gpu_session/` et `vendor/encore-active/eden-gpu/` | Mappings GPU, alias, caches et fences à vérifier **avant** toute dépublication/libération physique ; aucune preuve de cohérence zéro-partagé/écriture différée dans le runtime courant |

Le graphe `headless/CMakeLists.txt` place `src/ns2_sparse_guest.cpp` dans `common`, définit `EDEN_NS2_SPARSE_BACKING=1` pour `common` et `core` lorsque `PS5_NATIVE && EDEN_REVIEWED_DUAL_NPDM`, puis remplace **une seule fois** `hle/kernel/k_memory_manager.cpp` par l'owner `encore-active/ns2-runtime/sparse-residency/`. C'est ce chemin maintenu qu'il faut corriger, **pas** `vendor/sources/eden/src/common/host_memory.cpp` ni une copie historique hors build. Vérifier cette condition et le gitlink sur toute révision nouvelle ; la présence d'une source dans l'arbre ne certifie pas son lien ELF.

#### 5.3.2 P0 Mario Kart World / Donkey Kong Bananza — observations et diagnostic différentiel

Les essais PS5 ExeFS du **23/11**, compilés avec moteur `25f12c020eb69ea9b7b29aac35dadcfe8b38f918` et vendor `716e069f212b89b6fd13af56b0677343cf41ba07`, indiquent :

| Jeu | Signal observé sur la version testée | Limite de preuve |
|---|---|---|
| Mario Kart World, `0400C3F00006E000` | `std::bad_alloc` sur `CPUCore_0`, ~54 s après lancement, **zéro soumission GPU invitée mesurée** ; plus grand bloc direct libre ~5 194 Mio | La présence de mémoire libre n'annule pas un refus par **budget logique de 6 Gio**, ni un échec d'une allocation de 2 Mio. Le binaire non symbolisé impose de distinguer une adresse de terminaison d'une vraie pile d'appels |
| Donkey Kong Bananza (ExeFS) | `std::bad_alloc` sur `CPUCore_0`, ~25 s après lancement, **zéro soumission GPU invitée mesurée** ; plus grand bloc direct libre ~5 416 Mio | Signature commune compatible avec le chemin de pré-engagement guest, pas preuve de la même plage exacte ou d'une cause exclusive |
| Pokémon Legends: Z-A (NUP) | Entrée invitée atteinte ; `guest_frame_handoff=0`, `gpu_submit_sample=0` après 10 et 30 s | Blocage **après acceptation initiale du conteneur** ; le correctif ExeFS/NUP n'est pas une preuve de progrès GPU |
| Pokémon Pokopia (NUP) | `EDEN_NUP_REJECT stage=archive reason=metadata exceeds file`, `Core initialization failed (2)` | Rejet **avant le processus invité** : contrôler métadonnées, taille réelle du fichier et offsets ; ne pas attribuer ce cas au budget sparse |

Les traces ExeFS montrent `EDEN_NS2_SHARED_CLEAR begin` **puis** `done` sur une plage de 17 Mio : cette opération a fini, et le `bad_alloc` survient ailleurs dans la suite. Le C++ de `HostMemory::ClearBackingRegion` produit explicitement `std::bad_alloc` si `Runtime::Commit` échoue ; `KMemoryManager::AllocateForProcess` passe par cette fonction. Il s'agit du **chemin causal prioritaire** à requalifier avec symboles exacts et marqueur d'échec, pas d'une preuve que tout `std::bad_alloc` du jeu émane nécessairement du même appel.

**Révisions déjà intégrées mais non validées sur console :**

- Vendor [`7bf93eb2`](https://github.com/niakw/Prospero.Eden-Encore-vendor/commit/7bf93eb2da720281a09edd8f7d823fb2558ad937) : en cas de `bad_alloc` sur le clear **non optimisé** de `AllocateForProcess`, retour des pages invitées **non encore `OpenFirst`** vers chaque pool/manager, destruction des descripteurs et `ResultOutOfMemory` normal. Cela protège cette sortie ; cela **n'augmente pas la mémoire disponible**, ne couvre pas automatiquement les autres écritures kernel, et n'empêche pas le jeu invité d'échouer faute de RAM.
- Moteur [`3349171e`](https://github.com/niakw/ProsperoEden-Encore/commit/3349171e46d7bbf0545edfa75532e3eafaeb1d34) : gitlink sur le vendor ci-dessus ; `EDEN_NS2_SPARSE_COMMIT_DENIED` à la **première** défaillance, avec `stage=range|admission|native_physical_map|ownership_stage`, offset, longueur, résidence et budget. Les logs du 23/11 proviennent de l'**ancien binaire** et n'ont pas ce marqueur. Sans ce résultat du nouveau binaire, `admission` (quota) et `native_physical_map` (PS5) restent **à départager**.

#### 5.3.3 Écart avéré avec EglantinePS5 : résidence *demand-zero*, pas seulement « sparse »

[Source PS5 `src/guest_memory_service.inc`](https://github.com/heydemoura/EglantinePS5/blob/5eb70367ffde039f237b3b828856f4b4247ea09e/src/guest_memory_service.inc) (intégrée à `src/memory_pages.cpp`) et [`src/host_memory.cpp`](https://github.com/heydemoura/EglantinePS5/blob/5eb70367ffde039f237b3b828856f4b4247ea09e/src/host_memory.cpp) :

| Opération | Encore actuel | EglantinePS5, code examiné |
|---|---|---|
| Noyau invité réserve/initialise une plage | `Commit` sur tous les granules touchés par `ClearBackingRegion`, avant `memset` | `ClearGuestMemory` conserve ou restaure les blocs vierges sur une vue **zéro partagée** ; une initialisation ne signifie pas « RAM physique privée pour chaque bloc » |
| Première lecture d'un bloc vierge | Nécessite le granule physique privé pré-engagé | L'état **`SlotZero`** expose des zéros lisibles |
| Première écriture d'un bloc vierge | Déjà en `Resident` | Écriture interceptée, promotion vers **`SlotOwn`** puis reprise de l'accès, avec verrou et ownership |
| Fin de vie/réutilisation | Les granules demeurent résidents jusqu'à la fin du titre | Des pages libérées ou complètement remises à zéro peuvent restituer leur mémoire ; les alias sont révoqués avant retour des blocs |
| Mémoire froide et fragmentation | Pas de compression/partage équivalent au runtime NS2 courant | États supplémentaires `SlotShared`, `SlotFine`, `SlotPacked`, récupération et hooks de pression ; **ne pas importer ces optimisations comme prérequis** |

La [mesure console Mario Kart World d'EglantinePS5](https://github.com/heydemoura/EglantinePS5/blob/5eb70367ffde039f237b3b828856f4b4247ea09e/docs/MKW-MEMORY-LEAK.md) rapporte ~9,5 Go **mappés par le noyau invité** mais une résidence effective croissant d'environ 1,5 à 6,1 Go suivant la scène et la durée. Les chiffres proviennent de **leur** PS5 et de **leurs** révisions : ce ne sont ni nos mesures ni une prévision de FPS. EglantinePS5 atteint des scènes de jeu sur MKW et Bananza ; il rencontre lui-même des limites de pool GPU/RAM à plus longue durée.

Leur [analyse du budget MKW](https://github.com/heydemoura/EglantinePS5/blob/5eb70367ffde039f237b3b828856f4b4247ea09e/docs/MKW-MEMORY-BUDGET.md) rapporte qu'abaisser le layout invité à **8/10 Go empêche MKW de démarrer**. **Ne pas** modifier le layout 12 Gio, monter arbitrairement notre plafond physique de 6 Gio ou prétendre résoudre la pression de RADV en augmentant l'allocation guest. **Ne pas** backporter automatiquement `SlotPacked`/LZ4 : EglantinePS5 a désactivé par défaut la compression froide après des anomalies GPU/commandes et des hangs lors de tests MKW.

Autre piste PS5 distincte : [`src/direct_memory.c`](https://github.com/heydemoura/EglantinePS5/blob/5eb70367ffde039f237b3b828856f4b4247ea09e/src/direct_memory.c) attribue certaines ressources persistantes en haut du pool direct pour réduire la fragmentation des allocations transitoires. Cela exige une comparaison réelle des wrappers de link, ownership et zones CPU/RADV avant toute transposition : les chiffres de mémoire libre du crash Encore **ne prouvent pas** une fragmentation fatale de blocs de 2 Mio.

#### 5.3.4 Contrat architectural pour la correction fonctionnelle

Objectif initial : **états `ZERO` et `OWN` seulement**, sans nouvelle option expérimentale ni chemin mort. Le mécanisme doit couvrir le runtime natif PS5 sélectionné, les écritures hors PTE et les chemins CPU/GPU réellement actifs ; il ne peut pas être réduit à « ne plus appeler `memset` ».

~~~mermaid
stateDiagram-v2
    [*] --> NonPublie
    NonPublie --> Zero : range initialisé sans PA privée
    Zero --> Own : avant première écriture, admission + mapping + publication
    Own --> Zero : clear/libération intégrale, tous alias retirés et GPU retiré
    Own --> Own : écriture / lecture sans changement de propriétaire
    Zero --> NonPublie : retrait de mapping après quiescence
    Own --> NonPublie : destruction après quiescence et retrait de tous les alias
~~~

**Invariants impératifs :**

1. **Zéro fidèle :** toute lecture CPU invitée, accès HLE/IPC, readback GPU et accès par pointeur direct à une page logique vierge renvoie des zéros, sans SIGSEGV, page arbitraire ni donnée d'une session précédente. Aucun mapping ne doit être publié tant que cette propriété n'est pas vraie.
2. **Première écriture sûre :** obtenir une PA réellement possédée et writable **avant** d'autoriser l'écriture, copier les données précédentes si nécessaire, puis publier l'alias après les barrières. Définir le chemin exact pour Dynarmic, accès natifs du core, DMA/GMMU et worker GPU. Le callback de faute ne peut pas utiliser un allocateur réentrant ou se bloquer sous un verrou du heap.
3. **Propriétaire unique, alias multiples :** conserver la correspondance `guest range -> slot -> PA` et un état/génération sous verrou ; retirer toute vue JIT/CPU, GPU/NvMap, cache de textures/buffers et ancienne entrée de table avant de libérer une PA. Aucune promotion ou éviction ne doit exposer une PA libérée.
4. **Synchronisation GPU :** une page dont des commandes invitées ou hôtes en cours peuvent lire l'ancienne PA ne peut être rendue ni réattribuée avant retraite confirmée des fences correspondants ; les invalidations CPU/GPU et readbacks restent ordonnés. Éviter les chemins de promotion à mi-soumission et le risque de publication différée du BufferCache déjà documenté.
5. **Fail closed et retry :** distinguer `admission` (quota logique), `native_physical_map` (alloc/mapping direct PS5), absence de réservation et violation d'ownership. Un échec ne publie **aucun** PTE/alias partiel ; les ressources nouvellement prises sont restaurées exactement une fois. Retourner le `Result` noyau approprié seulement lorsque les invariants d'état sont préservés.
6. **NS1 inchangé :** activer la sémantique uniquement après identification fiable de la génération/layout, conserver l'ABI Dynarmic et les configurations CPU6 réellement sélectionnées. Ne pas restaurer le dispatch JIT 64K supprimé pour écart ABI ; ne pas changer les règles de mémoire NS1 par effet de bord.

**Séquence de réalisation vérifiable, sans nouvel interrupteur de production :** (a) identifier tous les accès directs avant publication de PTE et les alias GPU, (b) proposer un seul owner `ZERO/OWN` avec tests d'accès croisés et admission atomique, (c) raccorder les clears/allocations et la libération après quiescence **dans les unités natives déjà sélectionnées**, (d) valider la première soumission GPU et la première frame sur MKW et Bananza, (e) seulement ensuite considérer la récupération de pages froides, la fragmentation RADV et les effets sur les frametimes. Un test hôte de modèle d'états n'est **pas** une preuve d'absence de corruption sur PS5.

**Critère P0 matériel :** même couple moteur/vendor et même contenu ExeFS, session froide puis chaude, pas de `std::bad_alloc` natif, pas de SIGSEGV ou heap invité artificiellement réduit, `guest_run_begin` puis **soumission GPU invitée non nulle**, première frame invitée vérifiée, puis gameplay stable. Enregistrer résidence guest, plus grande plage directe libre, commits/refus `EDEN_NS2_SPARSE_COMMIT_DENIED`, allocations RADV, alias et fences. Le compteur de présentations de l'écran de chargement hôte ne peut pas satisfaire ce critère.

**État de réalisation au 23/11 :** rollback d'un sous-chemin OOM + diagnostic au premier refus intégrés et gitlink synchronisé ; **owner ZERO/OWN, libération physique à la restitution guest, promotion sécurisée et qualification console non implémentés ou non prouvés**. Ce complément ne certifie donc ni parité runtime avec EglantinePS5, ni chargement des NUP, ni complétude fonctionnelle NS2.

## 6. Architecture GPU invitée Maxwell / Ampere

### 6.1 NS1 — NVIDIA Maxwell

La Switch 1 expose une architecture Tegra X1/Maxwell invitée. Elle ne se pilote pas comme une application CUDA standard. Le moteur interprète commandes, moteurs DMA/2D/3D, états de textures et programmes shaders invités.

**Chemins observés** :

- <code>V/sources/eden/src/video_core/engines/maxwell_3d.*</code>
- <code>.../engines/maxwell_dma.*</code>, <code>fermi_2d.*</code>, <code>kepler_compute.*</code>, <code>kepler_memory.*</code>
- <code>.../video_core/host1x/</code>, <code>dma_pusher.*</code>, <code>gpu_thread.*</code>
- <code>.../shader_recompiler/frontend/maxwell/</code>
- <code>V/encore-active/eden-gpu/</code> et <code>eden-core/src/video_core/</code> pour les adaptations maintenues.

**Vocabulaire à distinguer** : SASS/encodage réel des programmes invités, PTX comme ISA virtuelle CUDA documentée, commande GPFIFO, état des descripteurs TIC/TSC, macros GPU, DMA, mémoire GMMU. Les manuels PTX sont une **aide conceptuelle**, pas une spécification suffisante pour décoder les shaders Nintendo.

### 6.2 NS2 — NVIDIA Ampere

Ampere/T239 est un autre invité. Les instructions, tâches GPU, capacités, layouts, descripteurs QMD et interfaces système ne doivent pas être supposés équivalents à Maxwell.

**Sous-arbres constatés** dans <code>V/encore-active/ns2-runtime/</code> :

| Famille | Sous-dossiers |
|---|---|
| CPU / processus | <code>cpu6/</code>, <code>process/</code>, <code>kernel/</code>, <code>kernel_wait64/</code>, <code>ldapr/</code>, <code>ns2-a64/</code> (module voisin) |
| GPU programmation | <code>ampere/</code>, <code>gpu_dispatch/</code>, <code>gpu_session/</code>, <code>graphics_supervisor/</code> |
| Mémoire et driver | <code>nvdrv/</code>, <code>nvdrv_as/</code>, <code>nvdrv_gpu/</code>, <code>gpu_access_svc/</code>, <code>sparse-residency/</code> |
| Shaders et interfaces | <code>shader_resource/</code>, <code>vulkan_abi/</code> |
| HLE et médias | <code>hle/</code>, <code>am/</code>, <code>self_controller/</code>, <code>audio/</code>, <code>video_decoder/</code>, <code>font_service/</code>, <code>metadata/</code> |

### 6.3 Critères d'équivalence GPU

- Une commande reconnue ne prouve pas l'exécution du shader.
- Un module SPIR-V valide ne prouve pas l'équivalence visuelle, l'ordre mémoire ni la présence d'un framebuffer.
- Une frame présentée ne prouve pas la progression des commandes guest.
- Ne jamais remplacer silencieusement un stage inconnu par une opération vide réussie.
- Pour NS2 : journaliser stage, QMD/descripteur, registres, constantes, capacités et erreur de traduction avec limites de volume et anonymisation.

## 7. Recompilation des shaders et pilotes hôtes

### 7.1 Chemins de traduction

~~~mermaid
flowchart TB
  G["Programme shader NVIDIA invité"] --> D["Décodeur frontend Maxwell / NS2"]
  D --> IR["IR shader + passes d'optimisation"]
  IR --> SP["Backend SPIR-V"]
  IR --> GL["Backend GLSL / GLASM"]
  SP --> VULKAN["Vulkan pipeline + descriptors"]
  VULKAN --> RADV["Mesa RADV"]
  RADV --> NIR["NIR"]
  NIR --> ACO["ACO / backend choisi par la configuration"]
  ACO --> AMD["Code GPU AMD RDNA 2"]
  GL --> OGL["Backend OpenGL PS5"]
~~~

**Précision** : NIR et ACO dépendent du pipeline de compilation réellement configuré dans la version Mesa/RADV épinglée ; LLVM AMD peut intervenir suivant le chemin et la configuration. Le schéma n'est pas un reçu d'exécution du portage.

### 7.2 Sous-systèmes réels

- Recompiler frontend : <code>V/sources/eden/src/shader_recompiler/frontend/maxwell</code>, <code>frontend/ir</code>.
- Optimisations IR : <code>.../shader_recompiler/ir_opt/</code>.
- Backends : <code>.../shader_recompiler/backend/{spirv,glsl,glasm}</code>.
- Vulkan : <code>.../video_core/renderer_vulkan/</code> (pipeline caches, descriptor pools, command pools, scheduler, rasterizer, sync).
- OpenGL : <code>.../video_core/renderer_opengl/</code>.
- Driver Mesa : <code>V/sources/ps5-mesa/src/amd/{vulkan,compiler}</code> et <code>V/encore-active/ps5-mesa/</code>.

### 7.3 Quatre temps différents

1. **Décodage shader invité** : décoder le code NVIDIA et construire une IR.
2. **Conversion de l'IR** : optimisations + émission SPIR-V.
3. **Compilation Vulkan/RADV** : création de pipeline/compilation GPU et recherche en cache.
4. **Attente d'usage** : blocage effectif du worker ou d'un draw jusqu'à ce que la version correcte soit disponible.

Un compte de « cache hit » ne prouve pas l'absence d'un des trois autres coûts. Les traces doivent lier l'identité du shader, la clé du pipeline, la durée de chaque phase, les invalidations et la frame concernée.

### 7.4 Optimisation sans triche sur le rendu

- Mettre en cache uniquement les identités complètes : hash shader, layout, état raster, format, MSAA, device/driver et options significatives.
- Précompiler lorsque les données déterminant **réellement** le pipeline sont connues ; une précompilation spéculative générant un état incomplet est incorrecte.
- Publier un pipeline seulement après état prêt avec les bonnes garanties de synchronisation.
- Réduire locks / allocs et duplicate work sur le chemin chaud.
- Ne jamais afficher « pipeline prêt » lorsqu'il manque une compilation requise.
- Évaluer les stratégies de pipeline libraries uniquement après vérification de l'extension dans RADV PS5.

## 8. Caches textures, rendu, synchronisation et présentation

### 8.1 Composants

| Composant | Source à inspecter | Contrat |
|---|---|---|
| Rasterizer Vulkan | <code>renderer_vulkan/vk_rasterizer.*</code> | Construction fidèle des draws |
| Pipeline cache | <code>vk_pipeline_cache.*</code>, <code>vk_graphics_pipeline.*</code> | Clés de variantes et complétude |
| BufferCache | <code>video_core/buffer_cache/</code>, <code>vk_buffer_cache.*</code> | Données CPU/GPU synchronisées |
| TextureCache | <code>video_core/texture_cache/</code>, <code>vk_texture_cache.*</code> | Versions des images, alias et évictions |
| Descriptor cache/pools | <code>vk_descriptor_pool.*</code>, <code>vk_descriptor_buffer.*</code> | Ressources et durée de vie |
| DMA / blit | <code>engines/maxwell_dma.*</code>, <code>renderer_vulkan/blit_image.*</code> | Copies ordonnées et extents exacts |
| Queries / fences | <code>vk_query_cache.*</code>, <code>vk_fence_manager.*</code> | Résultat terminé vs soumis |
| Presenter / swapchain | <code>vk_present_manager.*</code>, <code>vk_swapchain.*</code> | Nouvelle image réellement présentée |
| Staging pool | <code>vk_staging_buffer_pool.*</code> | Réutilisation après achèvement GPU |
| NS2 ASTC | <code>V/encore-active/ns2-astc/</code> | Décodage et trafic mémoire corrects |

### 8.2 Cohérence et fraîcheur du HUD

Le GPU peut continuer à présenter des images alors que le CPU invité, les services HLE ou un verrou du cache sont bloqués. Un HUD dont la texture est présente mais dont le texte ou le nom de joueur se met à jour tardivement peut dépendre d'un service de texte, d'une mise à jour de buffer, d'une invalidation manquée, d'une commande DMA ou d'un readback sans complétion.

**Instrumentation causale** : associer pour une ressource un identifiant, génération/dirty epoch, dernière écriture invitée, invalidation, upload, draw consommateur, tick de soumission et tick de complétion. L'absence d'une transition identifie mieux la cause qu'un compteur FPS.

### 8.3 Frame pacing

Mesurer au moins :

- horodatage input, SVC/IPC, avancement guest, enqueue GPU, fin traduction/compilation, début draw, submit, fence et present ;
- moyenne **et** p50/p95/p99/p99.9 des frametimes, intervalles >50/100/250 ms, nombre de frames identiques, budget temporel de chaque worker ;
- warm run et cold run, cache valide, même scène, même profil vidéo, mêmes versions et logs activés/désactivés ;
- consommation RAM/VRAM, temps de verrou, backlog DMA, créations et invalidations pipeline.

**Interdit** : supprimer une dépendance GPU/CPU simplement pour réduire une attente ; accepter des images obsolètes comme amélioration de fluidité.

## 9. HLE, kernel, fichiers, services et formats

### 9.1 Horizon et services

Le moteur utilise la HLE (High-Level Emulation) pour les appels système et services. <code>V/sources/eden/src/core/hle/</code> est la racine principale ; <code>V/encore-active/eden-threading</code>, <code>eden-sync</code>, <code>eden-core</code> et <code>ns2-runtime</code> portent des adaptations.

| Groupe | Exemples et symptômes |
|---|---|
| Kernel / SVC / scheduler | Création processus, thread, waits, atomiques, arbitrage, deadlocks, exit |
| AM / applets | Menus, lancement, pause, contrôleurs et cycle de vie |
| VI / NVNFlinger | Layers, buffers affichés, présentation et events |
| NVDRV / NVMap | Sessions GPU, mappings, handles, allocation/fermeture |
| HID | Entrées, vibrations, options, gestion des contrôleurs |
| FS / FSP / RomFS | Chemins, ouverture fichiers, latences I/O, mauvais montages |
| LDR / RO / ES / SPL | Exécutables, modules et certaines interfaces de sécurité |
| NCM / NS / NIFM / sockets | Contenu installé, informations réseau et gestion titres |
| Audio services | AudioOut, AudioIn, AudioRenderer, événements |
| NS2 services spécifiques | CPU6, GPU access, supervisor, nouveaux IPC, fonts, métadonnées |

### 9.2 Formats

| Famille | Formats / rôle |
|---|---|
| Packaging jeux | NSP, XCI, NSZ, XCZ selon implémentation/chemin |
| Contenu | NCA, RomFS, ExeFS, NAX et archives associées |
| Exécutables | NSO, NRO, NPDM, KIP |
| Compression | LZ4, Zstandard, ZBIC et mécanismes du lecteur effectivement compilé |
| Profils et overlays | Overrides de jeu, mods, mises à jour, données de glyphes |
| Métadonnées | Title ID, icônes/jaquettes/captures, langues et capacités |

**Les formats supportés ne prouvent pas la compatibilité complète d'un jeu** : chaque jeu peut dépendre de services, extensions GPU, shader stages ou particularités de firmware non reproduites.

## 10. Audio, vidéo, interfaces et fonctions annexes

### 10.1 Audio

**Chemin conceptuel :** service audio invité → AudioCore / AudioRenderer / ADSP / Opus → file PCM → sink hôte → sortie PS5. Sources : <code>V/sources/eden/src/audio_core/</code>, <code>src/core/hle/service/audio/</code>, <code>E/headless/audio.cpp</code> et <code>V/encore-active/eden-core/src/audio_core/</code>.

Éléments de validation : absence de débordement, compteur d'underruns, fréquence/canaux cohérents, fin de lecture, buffers de silence, déclenchement des events, pas de blocage lors du stop/restart.

### 10.2 Vidéo

La vidéo invitée peut provenir d'un chemin de décodage matériel émulé, de buffers de jeu ou d'une bibliothèque logicielle comme FFmpeg. Sources : <code>V/sources/ffmpeg</code>, <code>V/encore-active/ns2-runtime/video_decoder/</code> et parties VideoCore.

Vérifier profil codec, timestamps PTS/DTS, ordre des frames, formats NV12/YUV, colorimétrie, transfert vers textures GPU, synchronisation A/V et durée de vie des surfaces. **NVDEC NVIDIA est une interface/référence invitée, pas un décodeur NVIDIA physique disponible sur PS5.**

### 10.3 Launcher, langue et médias

Sources : <code>E/headless/prosperoeden/</code>, <code>E/assets/</code>, <code>E/data/</code>, <code>E/third_party/fonts/</code>, <code>V/sources/harfbuzz/</code>, <code>V/sources/libwebp</code>, <code>V/sources/jxrlib</code>.

Exigences : 31 choix de langue système PS5, distinction en-US/en-GB et fr-FR/fr-CA, fallback de fontes complet, forme des caractères par HarfBuzz, contraste, alignement, événements HID, gestion des captures, WebP, JXR et cohérence du cache d'images.

**UI et rendu invité sont distincts** : une vignette de launcher réussie ne démontre pas un rendu de jeu et un rendu de jeu ne prouve pas que tous les overlays sont corrects.

### 10.4 Upscaling, AA, frame generation, neural

Chaînes identifiées dans l'arbre : FSR1, intégration FSR3.1, SGSR, MSAA/SMAA/FXAA, Anime4K, chemins R09 RDNA2 et optical flow. Un module existant ne démontre ni l'équivalence à DLSS NVIDIA, ni un résultat image PS5, ni une amélioration des fps.

Conditions de validation : image source authentique, motion vectors/depth/temporal history disponibles si requis, formats et résolutions vérifiés, hors historique et scènes de transition testés, jitter mesuré et aucune allocation mémoire incontrôlée.

## 11. Architecture des dépôts et de la compilation native

~~~mermaid
flowchart TB
  E["Moteur main<br/>headless, src, tools, docs, CI"] --> CM["Makefile + CMake / Ninja<br/>contrat de sélection"]
  V0["Vendor sources/<br/>snapshots tiers épinglés"] --> PRE["Préparation / copie vérifiée"]
  V1["Vendor encore-active/<br/>adaptations maintenues"] --> PRE
  PRE --> CM
  SDK["SDK PS5 + compiler-rt + libc<br/>toolchain hôte"] --> CM
  OVR["encore-overrides<br/>profils et données"] --> CM
  CM --> BIN["Binaire natif PS5 + package<br/>symboles et artefacts"]
  BIN --> CON["Test console FW 13.60"]
  E --> TEST["Tests source / hôte / CI"]
  PRE --> TEST
  TEST --> BIN
~~~

### 11.1 Organisation vérifiée

**Moteur** : <code>headless/</code> (port PS5, application et build), <code>src/</code> (host memory / sparse guest), <code>docs/</code>, <code>tools/</code>, <code>tests/</code>, <code>assets/</code>, <code>data/</code>, <code>.github/</code>, <code>sce_sys/</code> et <code>third_party/</code>.

**Vendor — upstreams** : <code>sources/eden</code>, <code>eden-cpm</code>, <code>ps5-mesa</code>, <code>opengl-mesa-26-2</code>, <code>ps5-payload-sdk-fork</code>, <code>ffmpeg</code>, <code>fmt</code>, <code>harfbuzz</code>, <code>libwebp</code>, <code>jxrlib</code>, <code>compiler-rt</code>, <code>zbic</code>, <code>ps5-fsr3-optical-flow</code>, <code>ps5-mihawkgen</code>, <code>ps5-vulkan-tools</code>, divers composants OpenGL et headers.

**Vendor — adaptations** : <code>encore-active/eden-core</code>, <code>eden-gpu</code>, <code>eden-shader</code>, <code>eden-threading</code>, <code>eden-sync</code>, <code>eden-surface-lifecycle</code>, <code>eden-vulkan</code>, <code>eden-vulkan-oracles</code>, <code>eden-backports</code>, <code>eden-build</code>, <code>eden-header-hygiene</code>, <code>ns2-runtime</code>, <code>ns2-a64</code>, <code>ns2-astc</code>, <code>ns2-helpers</code>, <code>ps5-mesa</code>, <code>ps5-jxr</code>, <code>amd-fsr31</code>, <code>compiler-rt</code>.

Ces répertoires incluent du code tiers, du code maintenu, des aides et parfois des pistes de recherche. La liste des composants effectivement **liés au binaire** est déterminée par les sources sélectionnées à la révision exacte, pas par cette énumération.

### 11.2 Contrat source unique

- <code>V/sources/*</code> = source amont immuable à révision/empreinte connues.
- <code>V/encore-active/*</code> = code tiers maintenu et adapté.
- <code>E/headless/*</code>, <code>E/src/*</code> = code propre au port/runtime.
- CMake **sélectionne** des unités ; il ne doit pas synthétiser un autre corps C++ caché par <code>string(REPLACE)</code>.
- Le gitlink <code>E/vendor</code> fixe la révision du vendor ; consulter son SHA avant toute preuve de build.
- Changer le vendor seul n'affecte pas immédiatement le moteur si le gitlink n'est pas mis à jour ; vérifier les deux dépôts, licences, ABI, fonctions exportées et archive finale.
- Une dépendance maintenue peut contenir plusieurs variantes historiques : le graphe de build doit sélectionner exactement la variante voulue.

### 11.3 Chaîne de validation

| Niveau | Preuve acceptable |
|---|---|
| Source | Diff et chemins de compilation exacts, SHA moteur + gitlink vendor |
| Hôte | Tests reproductibles, assertions et traces, O0/O2, sanitizers quand applicables |
| CI | Jobs au bon SHA, statuts réels y compris skipped/failed, warnings inspectés |
| Natif | Link PS5, package, symbole, dépendances, empreintes, artefacts inspectés |
| Installation | Package installé sur PS5 de firmware connu |
| Démarrage | Processus invité en cours, PC/progression, HLE/IPC et GPU |
| Première image | Framebuffer invité authentique et nouvellement rendu |
| Gameplay | Scène comparable, stabilité, entrée/sortie, A/V, frametimes et mémoire |

## 12. Contrats transversaux et observabilité

### 12.1 Journalisation avancée

Le mode de logs ne doit **jamais** changer la logique de jeu ou détruire l'historique lorsqu'on active/désactive un niveau de détail. Il doit permettre de diagnostiquer sans imposer une charge non bornée.

- Identité session : version binaire, SHA moteur, gitlink vendor, firmware PS5, Title ID, backend, paramètres vidéo, profil de logs.
- Temps : horloge monotone hôte et repères de frames ; identifiants de threads, ordre des événements et corrélation guest/host.
- CPU/JIT : guest PC, dernière instruction supportée, compilation et invalidation, temps des locks, arrêt/redémarrage.
- HLE : service, commande IPC, latences, queue/waits, timeout, sans exposer les données personnelles des jeux.
- GPU : command ID, stage, pipeline key, cache miss, submit, complete tick, swapchain events, timeout.
- Textures : resource ID, dirty epoch, transfert, readback, eviction, frame de consommation.
- Mémoire : réservations, committed pages, plus gros bloc disponible, heap/pool et erreur première.
- Interface : toggles de diagnostic, temps du launcher et overlay, conservation rotation des logs.
- Confidentialité : anonymisation des chemins, IP, identifiants utilisateurs, clés et données de contenus.

### 12.2 Contrats de performance

Définir pour chaque jeu et scène les mêmes conditions : *cold cache*, *warm cache*, durée, angle/état caméra, profil AA/upscale, logs, runtime SHA. Mesurer les mêmes segments du pipeline ; utiliser traces/counters avant une hypothèse de correctif.

Un système peut atteindre 30 FPS moyens tout en présentant des pauses de plusieurs secondes. Les valeurs p95/p99, pires pauses, input-to-present et durée de propagation des HUD sont donc indispensables.

### 12.3 Gestion des incidents et registre

Conserver sous GitHub un enregistrement :

| Champ obligatoire | Contenu |
|---|---|
| Symptôme | Description reproductible et gravité |
| Titre | Jeu, Title ID, génération NS1/NS2 |
| Environnement | Firmware, SHA moteur+vendor, backend, profil |
| Traces | Logs, fenêtres temporelles, commandes, PC et erreurs |
| Sous-système | Owner, fonctions, causes candidates |
| Upstream | Issues, PR, commits, versions et différences |
| Correctif | Diff exact, raison, dépendances et licence |
| Validation | Test host, CI, build PS5, image, gameplay |
| Statut | Ouvert, hypothèse, source intégré, hôte validé, console validée |

## 13. Guide de diagnostic par symptôme

| Symptôme | Priorité | Points d'entrée | Références utiles |
|---|---|---|---|
| NS1 ne démarre plus / écran noir | P0 | loader, memory, HLE/SVC, GPU progress, presenter | Arm ARM, Dynarmic, Vulkan sync |
| NS2 écran noir / aucun framebuffer | P0 | <code>ns2-runtime/{ampere,gpu_session,shader_resource,vulkan_abi}</code> | Ampere guide, SPIR-V, Vulkan |
| « Cannot allocate memory » | P0 | sparse guest, JIT commit, memory managers, Vulkan allocation | Vulkan memory, SDK, W^X |
| Crash app à la sortie | P0 | kernel finalizers, GPU worker, sinks et in-flight fences | C++ threading, Vulkan sync |
| Changement de logs → freeze | P0 | log sinks/rotation, lifecycle, thread stop, cache ownership | Threading, filesystem, traces |
| Shader stage non implémenté | P0 | frontend shaders, NS2 stage dispatcher, IR/SPIR-V | SPIR-V spec, GPU architectures |
| Saccades début de match | P1 | <code>vk_pipeline_cache</code>, <code>vk_graphics_pipeline</code>, JIT, disk cache | Vulkan cache, Godot, DXVK |
| Retard HUD/texte après une passe | P1 | cache buffers/textures, dirty epoch, DMA, UI/HLE fonts | Vulkan memory, ASTC, HarfBuzz |
| Menu pause après plusieurs secondes | P1 | HID → IPC/AM → guest scheduling → GPU | Arm, HLE, thread contention |
| Audio en retard / crash | P1 | AudioRenderer, sink PCM, Opus, buffers, shutdown | Opus, FFmpeg |
| Cinématique noire ou désynchronisée | P1 | decoder, formats, surfaces, PTS, uploads et presents | FFmpeg, NVDEC |
| Débit faible / attente GPU | P1 | RADV, pipeline compile, descriptors, fences, scheduling | Mesa RADV, GPUOpen |
| Textures incorrectes NS2 | P1 | ASTC, GMMU, TIC/TSC, aliases, buffer cache | ASTC, SPIR-V, Vulkan |
| Problème de MSAA/upscale | P1/P2 | render pass / MSAA, FSR, SGSR, temporal resources | Vulkan rasterization, FidelityFX |
| Icônes/captures/langues | P2 | launcher, WebP/JXR, metadata, glyphs | HarfBuzz, Unicode, WebP |

Liens internes de suivi : [F07 FC27](FC27_F07_MASTER_TRACKER.md), [checklist restante](F07_REMAINING_OPTIMIZATION_CHECKLIST.md), [roadmap NS1/NS2](ROADMAP_NS1_NS2_UNIFIED.md), [catalogue actif](EDEN_ACTIVE_SOURCE_CATALOG.md), [audit dépendances](EDEN_CORE_AUDIT_DEPENDENCIES.md).

## 14. Documentation primaire et officielle

**Classification des sources :**
- **[OFF]** publication officielle d'un standard/éditeur/fournisseur ;
- **[UP]** documentation source ou dépôt du projet amont ;
- **[HIST]** historique lié à l'ancienne génération plutôt qu'au silicium exact ;
- **[R]** analogie méthodologique, non spécification exacte du matériel émulé.

Les spécifications publiques NVIDIA, AMD ou Sony ne décrivent **pas** nécessairement la configuration Nintendo T239 ni l'API privée de la PS5. Citer la section et la version consultées avant de conclure.

### 14.1 Nintendo, NVIDIA, Maxwell, Ampere

| Classe | Référence | Application Encore |
|---|---|---|
| OFF/HIST | [NVIDIA Maxwell Tuning Guide](https://docs.nvidia.com/cuda/maxwell-tuning-guide/) | SM, mémoire/cache et comportement Maxwell général |
| OFF/HIST | [NVIDIA Maxwell Compatibility Guide](https://docs.nvidia.com/cuda/maxwell-compatibility-guide/) | Versions et compatibilité du code GPU |
| OFF/HIST | [NVIDIA Jetson TX1](https://developer.nvidia.com/embedded/jetson-tx1) | SoC Tegra X1 apparenté à NS1 |
| OFF/HIST | [NVIDIA Ampere Tuning Guide](https://docs.nvidia.com/cuda/ampere-tuning-guide/) | Modèles de latence, mémoire, exécution Ampere |
| OFF/HIST | [NVIDIA Ampere Compatibility Guide](https://docs.nvidia.com/cuda/ampere-compatibility-guide/) | Évolution ISA et compatibilité |
| OFF/R | [NVIDIA CUDA Programming Guide](https://docs.nvidia.com/cuda/cuda-programming-guide/) | Ordonnancement et mémoire abstraits |
| OFF/R | [NVIDIA PTX ISA](https://docs.nvidia.com/cuda/parallel-thread-execution/) | Instruction virtuelle CUDA ; **pas** un décodeur SASS Nintendo |
| OFF/R | [NVIDIA CUDA Best Practices](https://docs.nvidia.com/cuda/cuda-c-best-practices-guide/) | Méthode de benchmark et accès mémoire |
| OFF/HIST | [NVIDIA Switch 2 & DLSS announcement](https://blogs.nvidia.com/blog/nintendo-switch-2-leveled-up-with-nvidia-ai-powered-dlss-and-4k-gaming/) | Caractéristiques publiquement annoncées |
| OFF/HIST | [NVIDIA Ampere GA102 whitepaper](https://www.nvidia.com/content/PDF/nvidia-ampere-ga-102-gpu-architecture-whitepaper-v2.pdf) | Analogie Ampere de bureau, pas plan T239 |

### 14.2 CPU, ARM, JIT, ABI, LLVM

| Classe | Référence | Application |
|---|---|---|
| OFF | [Arm Architecture Reference Manual (A-profile)](https://developer.arm.com/documentation/ddi0487/latest) | Sémantique instructions A64/A32 et mémoire |
| OFF | [Arm A-profile architecture guides](https://www.arm.com/architecture/learn-the-architecture/a-profile) | Explications ARM |
| OFF | [ARM ABI source](https://github.com/ARM-software/abi-aa) | Convention d'appel et types binaires |
| UP | [Dynarmic](https://github.com/merryhime/dynarmic) | Source et API du moteur JIT |
| UP | [Xbyak](https://github.com/herumi/xbyak) | Assembleur JIT x86-64 |
| OFF | [LLVM documentation](https://llvm.org/docs/) | IR, optimisations, toolchain |
| OFF | [Clang documentation](https://clang.llvm.org/docs/) | Codegen et diagnostics |
| OFF | [LLD](https://lld.llvm.org/) | Link natif |
| OFF | [compiler-rt](https://compiler-rt.llvm.org/) | Runtime, builtins et TLS |
| OFF | [AMD64 manuals](https://www.amd.com/en/search/documentation/hub.html) | ISA hôte, ordering et mémoire |

### 14.3 Vulkan, SPIR-V, Mesa, OpenGL, AMD RDNA 2

| Classe | Référence | Application |
|---|---|---|
| OFF | [Vulkan specification](https://docs.vulkan.org/spec/latest/) | Contrat Vulkan complet |
| OFF | [Vulkan Guide](https://docs.vulkan.org/guide/latest/) | Conception robuste |
| OFF | [Vulkan synchronization](https://docs.vulkan.org/spec/latest/chapters/synchronization.html) | Dépendances et visibilité |
| OFF | [Vulkan synchronization examples](https://docs.vulkan.org/guide/latest/synchronization_examples.html) | Exemples de barrières |
| OFF | [Vulkan memory](https://docs.vulkan.org/spec/latest/chapters/memory.html) | Allocations et cohérence |
| OFF | [Vulkan pipelines](https://docs.vulkan.org/spec/latest/chapters/pipelines.html) | Compilation et états |
| OFF | [Vulkan Memory Model](https://docs.vulkan.org/spec/latest/appendices/memorymodel.html) | Ordering shader/host |
| OFF | [Khronos Vulkan Registry](https://registry.khronos.org/vulkan/) | Extensions et versions |
| OFF | [SPIR-V specification](https://registry.khronos.org/SPIR-V/specs/unified1/SPIRV.html) | Validité du shader intermédiaire |
| UP | [SPIRV-Tools](https://github.com/KhronosGroup/SPIRV-Tools) | Validator / optimizer / disassembler |
| UP | [SPIRV-Headers](https://github.com/KhronosGroup/SPIRV-Headers) | Définition opcodes/spirv |
| UP | [Mesa documentation](https://docs.mesa3d.org/) | Architecture du pilote |
| UP | [Mesa RADV](https://docs.mesa3d.org/drivers/radv.html) | Vulkan AMD |
| UP | [Mesa source tree](https://docs.mesa3d.org/sourcetree.html) | NIR, ACO et modules |
| UP | [Mesa GitLab](https://gitlab.freedesktop.org/mesa/mesa) | Commits/PR et correctifs upstream |
| OFF | [OpenGL Registry](https://registry.khronos.org/OpenGL/) | Backend OpenGL |
| OFF | [AMD GPU Architecture Documentation](https://gpuopen.com/amd-gpu-architecture-programming-documentation/) | ISA, matériels et compilers |
| OFF | [AMD RDNA 2](https://gpuopen.com/rdna2/) | Famille GPU hôte |
| OFF | [AMD RDNA Performance Guide](https://gpuopen.com/learn/rdna-performance-guide/) | Caches, bande passante, occupations |
| OFF | [Radeon GPU Analyzer](https://gpuopen.com/rga/) | Analyse des shaders sur hôte compatible |
| OFF | [Radeon GPU Profiler](https://gpuopen.com/rgp/) | Trace GPU, à utiliser comme référence méthodologique |
| OFF | [Radeon Memory Visualizer](https://gpuopen.com/rmv/) | Allocations et mémoire GPU |

### 14.4 Images, compression, audio, vidéo, UI

| Classe | Référence | Application |
|---|---|---|
| OFF | [Khronos ASTC format](https://github.com/KhronosGroup/DataFormat/blob/main/astc.txt) | Textures compressées |
| OFF | [Khronos Data Format Registry](https://registry.khronos.org/DataFormat/) | Formats, conversion pixels |
| OFF | [KTX registry](https://registry.khronos.org/KTX/) | Formats de textures, comparaison |
| UP | [Zstandard](https://github.com/facebook/zstd) | Décompression |
| UP | [LZ4](https://github.com/lz4/lz4) | Décompression |
| OFF | [FFmpeg documentation](https://ffmpeg.org/documentation.html) | APIs audio/vidéo |
| OFF | [FFmpeg Doxygen](https://ffmpeg.org/doxygen/trunk/) | Codecs et buffers |
| OFF | [FFmpeg libavcodec](https://ffmpeg.org/libavcodec.html) | Décodage |
| OFF/R | [NVIDIA NVDEC Guide](https://docs.nvidia.com/video-technologies/video-codec-sdk/13.1/nvdec-video-decoder-api-prog-guide/index.html) | Sémantique générale NVDEC |
| UP | [Opus documentation](https://opus-codec.org/docs/) | Audio codec |
| UP | [HarfBuzz manual](https://harfbuzz.github.io/) | Shaping multilingue |
| OFF | [Unicode technical reports](https://www.unicode.org/reports/) | Script, graphemes et fallback |
| UP | [FreeType documentation](https://freetype.org/freetype2/docs/) | Rasterisation des fontes |
| UP | [SDL3 wiki](https://wiki.libsdl.org/SDL3/FrontPage) | API d'entrées et surfaces |
| OFF | [WebP](https://developers.google.com/speed/webp) | Compression des images UI |

### 14.5 FSR, reconstructions et plateforme PS5

| Classe | Référence | Application |
|---|---|---|
| OFF | [AMD FidelityFX Super Resolution](https://gpuopen.com/fidelityfx-superresolution/) | FSR1 |
| OFF | [AMD FSR3](https://gpuopen.com/fidelityfx-super-resolution-3/) | Reconstruction temporelle / framegen |
| OFF | [FidelityFX SDK docs](https://gpuopen.com/manuals/fidelityfx_sdk/getting-started/) | Intégration des passes |
| UP | [Snapdragon GSR](https://github.com/SnapdragonGameStudios/snapdragon-gsr) | SGSR spatial/temporel |
| OFF | [Sony PS5 technical specs](https://blog.playstation.com/2020/03/18/unveiling-new-details-of-playstation-5-hardware-technical-specs/) | CPU/GPU/mémoire PS5 |
| UP | [PS5 homebrew SDK fork utilisé](https://github.com/niakw/Prospero.Eden-Encore-vendor/tree/main/sources/ps5-payload-sdk-fork) | Implémentation SDK communautaire, non SDK Sony |
| OFF | [CMake documentation](https://cmake.org/documentation/) | Build reproductible |
| UP | [Ninja manual](https://ninja-build.org/manual.html) | Exécution compilation |
| OFF | [Clang AddressSanitizer](https://clang.llvm.org/docs/AddressSanitizer.html) | Détection de corruption hôte |
| OFF | [Clang UBSan](https://clang.llvm.org/docs/UndefinedBehaviorSanitizer.html) | UB et contrat d'optimisation |
| OFF | [GitHub Actions docs](https://docs.github.com/en/actions) | CI |
| UP | [CodeQL docs](https://codeql.github.com/docs/) | Analyse sécurité |

## 15. Recherches scientifiques et analyses externes

**Sélection vérifiée par titre / identifiant arXiv ; elles présentent des idées, et non des correctifs déjà validés dans Encore.** Chaque étude doit être convertie en hypothèse instrumentée, test de non-régression et comparaison PS5 avant adoption.

### 15.1 Architecture GPU et mémoire

| Priorité | Publication | Apport et limites |
|---|---|---|
| P1 | [Mei & Chu (2015), *Dissecting GPU Memory Hierarchy through Microbenchmarking* — arXiv:1509.02308](https://arxiv.org/abs/1509.02308) | Mesures fines Fermi/Kepler/Maxwell, caches L1/L2, TLB et texture ; méthode, pas relevé Tegra exact |
| P0/P1 NS2 | [Abdelkhalik et al. (2022), *Demystifying the Nvidia Ampere Architecture through Microbenchmarking and Instruction-level Analysis* — arXiv:2208.11174](https://arxiv.org/abs/2208.11174) | Latences PTX/SASS Ampere ; GPU de recherche non identique au T239 |
| P1 | [Huerta et al. (2025), *Analyzing Modern NVIDIA GPU Cores* — arXiv:2503.20481](https://arxiv.org/abs/2503.20481) | Modèle microarchitectural des cœurs GPU ; comparaison et choix de tests |
| P1 | [Wang et al. (2026), *Uncovering the Memory Hierarchy of Modern NVIDIA GPUs for Accurate Simulation* — arXiv:2611.13860](https://arxiv.org/abs/2611.13860) | Méthodes SASS microbench et reverse engineering des caches ; ne prouve pas le comportement NS2 |

### 15.2 CPU, JIT et traduction binaire

| Priorité | Publication | Application |
|---|---|---|
| P0 | [Chakraborty (2020), *On Architecture to Architecture Mapping for Concurrency* — arXiv:2009.03846](https://arxiv.org/abs/2009.03846) | Traduction des comportements de concurrence et modèles mémoire entre ISA |
| P1 | [Jiang et al. (2024), *A System-Level Dynamic Binary Translator using Automatically-Learned Translation Rules* — arXiv:2402.09688](https://arxiv.org/abs/2402.09688) | Réduction des coûts DBT / règles de traduction : approche QEMU, pas patch Dynarmic |
| P2/R | [Parker (2025), *Boosting Cross-Architectural Emulation Performance by Foregoing the Intermediate Representation Model* — arXiv:2501.03427](https://arxiv.org/abs/2501.03427) | Comparaison coût/bénéfice d'IR ; **ne justifie pas** le retrait de l'IR Dynarmic |
| P2/R | [*Partial Cross-Compilation and Mixed Execution for Accelerating Dynamic Binary Translation* — arXiv:2512.00487](https://arxiv.org/abs/2512.00487) | Techniques hybrides ; exploration longue durée et contraintes de fidélité |

### 15.3 Publications techniques complémentaires non-arXiv

| Priorité | Source | Intérêt |
|---|---|---|
| P0/P1 | [Google Research — *Optimizing Binary Translation of Dynamically Generated Code*](https://research.google/pubs/optimizing-binary-translation-for-dynamically-generated-code/) | Détection des modifications de code et cohérence du cache traduit |
| P1 | [USENIX ATC'16 — *A General Persistent Code Caching Framework for Dynamic Binary Translation*](https://www.usenix.org/conference/atc16/technical-sessions/presentation/wang) | Persistance du code traduit et coût des helper threads |
| P1 | [Godot — *Reducing stutter from shader (pipeline) compilations*](https://docs.godotengine.org/en/stable/tutorials/performance/pipeline_compilations.html) | Shader baking/ubershaders/precompilation, avec limites |
| P1 | [DXVK — Developer Guidelines](https://github.com/doitsujin/dxvk/wiki/Developer-guidelines) | Création de pipelines et threads de compilation, attention aux dépendances |
| P1 | [Unreal Engine — Shader Stuttering](https://www.unrealengine.com/tech-blog/game-engines-and-shader-stuttering-unreal-engines-solution-to-the-problem) | PSO precaching et rapport de latence |
| P1 | [Vulkan Samples — Pipeline Cache](https://docs.vulkan.org/samples/latest/samples/performance/pipeline_cache/README.html) | Exemple concret d'optimisation cache |

**Ordre utile** : Arm ABI/memory & paper concurrence pour crash/latence CPU ; Vulkan synchronization/Mesa + Godot/DXVK pour stutter ; Maxwell/Ampere microbenchmarks pour définitions d'opérations GPU ; autres publications seulement après identification du coût dominant. Les techniques PC/Android ne se transposent pas automatiquement au runtime PS5.

## 16. Programme d'investigation et de validation

### 16.1 Checklist par correction

1. Reproduire le symptôme exact sur SHA et jeu identifiés.
2. Établir le premier événement anormal dans les traces, pas simplement le dernier crash.
3. Identifier owner, fonctions, cache et frontière de synchronisation.
4. Chercher des causes et correctifs upstream précis (issues ouvertes/fermées, commits, PR fusionnées, releases, forks).
5. Comparer le chemin de code, les hypothèses, versions, ABI, architectures hôte, licence et risques.
6. Écrire un changement minimal dans la source maintenue unique ; pas de branche supplémentaire pour une correction validée de production, pas de bifurcation « EXPERIMENTAL ».
7. Créer un test de reproduction **avant/après** : positif/négatif, O0/O2, UBSan/ASan selon support.
8. Inspecter graphe CMake, source effective, warnings, symbols et lien vendor.
9. Vérifier les CI hôtes au bon couple de SHA, puis build natif et package.
10. Valider sur console si le défaut est runtime : crash, démarrage, HUD, stutter, temps de pause, allocation, vidéo.
11. Documenter limites et non-régressions dans le registre, garder ouvert si validation console manquante.
12. Auditer moteur ET vendor, sans écraser une modification amont ni casser les licences.

### 16.2 Priorité d'application recommandée

| Lot | Objectif | Critère de sortie |
|---|---|---|
| P0-CPU | JIT, fastmem, A64/A32, thread lifetime | Plus d'UB/d'invalidation fautive dans tests, console stable |
| P0-MEM | OOM et backing NS1/NS2 | Cartographie des allocations + disparition de l'échec dans la scène |
| P0-BOOT | Premier boot NS1/NS2 sans écran noir | PC invité + HLE + framebuffer **authentique** |
| P1-GPU | Shaders/stages, cache textures, DMA, fences | Image correcte, pas de resource stale |
| P1-LAT | FC27 cold shaders, pauses, HUD | Frametime p99 et input/HUD latency améliorés sur scène comparable |
| P1-MEDIA | Audio et cinématiques | A/V synchronisés, aucun crash de buffer/codec |
| P2-UX | Launcher, jaquettes, textes, langues | Tests visuels/interaction et QA console |
| P3-SUPPLY | ABI, build, sécurité, licences et dépendances | CI propre, provenance attestée, pas de régression |

### 16.3 Critères pour affirmer un résultat

**Exemple valide :** « Code source du shader corrigé au SHA X, test SPIR-V Y vert, build natif Z, aucune validation de gameplay PS5 ; défaut encore ouvert côté console. »

**Exemple non valide :** « Crash NS2 résolu » après un simple test de compilation.

## 17. Autres documents internes, glossaire et maintenance

### 17.1 Index des registres internes à consulter

| Ressource | But |
|---|---|
| [Architecture du dépôt](EDEN_ARCHITECTURE.md) | Source unique et décisions structurelles |
| [Architecture PS5 native](PS5_NATIVE_ARCHITECTURE.md) | Politique CPU/JIT/mémoire, mesures |
| [Catalogue exact des overrides](EDEN_ACTIVE_SOURCE_CATALOG.md) | Source maintenue et propriétaire |
| [Inventaire de migration](EDEN_OVERRIDE_MIGRATION_INVENTORY.md) | Dette de générateurs / patches |
| [Audit moteur et dépendances](EDEN_CORE_AUDIT_DEPENDENCIES.md) | Graphe des sous-systèmes |
| [Roadmap NS1/NS2](ROADMAP_NS1_NS2_UNIFIED.md) | Contrats et limites hôtes/natifs |
| [Tracker FC27 F07](FC27_F07_MASTER_TRACKER.md) | Sources du chemin critique du match |
| [Optimisations restantes](F07_REMAINING_OPTIMIZATION_CHECKLIST.md) | Actions de vérification réelles |
| [Audit Mesa/Vulkan](EDEN_OPTIMIZATION_REVIEW_MESA_VULKAN_2026-10-20.md) | Pistes graphiques |
| [Architecture JIT différée](DEFERRED_JIT_QUIESCENCE_ARCHITECTURE_2026-10-17.md) | Quiescence et reclaim |
| [README vendor active](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/main/encore-active/README.md) | Source propriétaire des adaptations |
| [Vendor source pinned](https://github.com/niakw/Prospero.Eden-Encore-vendor/tree/main/sources) | Dépendances initiales |

### 17.2 Glossaire

| Terme | Définition opérationnelle |
|---|---|
| ARM A64/A32 | Exécution invitée 64/32 bits |
| ACO | Compilateur de shaders AMD dans Mesa |
| ADSP | Sous-système de traitement audio invité |
| ASTC / BCn | Compression de textures en blocs |
| CPU6 | Famille/chemin de compatibilité CPU NS2 dans le projet |
| Dynarmic | Recompilateur dynamique ARM |
| FSR / SGSR | Reconstruction de résolution (selon version, spatiale/temporelle) |
| GMMU | Traduction mémoire pour GPU invité |
| HLE | Émulation haut niveau des services système |
| IPC / SVC | Communication inter-processus / appels système |
| JIT | Just-in-time compilation d'instructions invitées |
| Maxwell / Ampere | Architectures GPU invitées NS1 / NS2 |
| Mesa / RADV | Stack GPU hôte Vulkan AMD |
| NIR | Représentation intermédiaire de Mesa |
| NVDEC | Famille d'interfaces de décodage vidéo NVIDIA |
| NVDRV / NVMap | Driver et gestion des mappings GPU invités |
| PTX / SASS | Langage virtuel CUDA / ISA machine NVIDIA ; à ne pas assimiler |
| PSO / pipeline | Objet d'état graphique compilé |
| RX/RW alias | Deux vues mémoire avec droits de lecture-exécution et lecture-écriture |
| Shader Recompiler | Traduction des programmes GPU invités vers des backends hôtes |
| SPIR-V | Format shader intermédiaire Khronos |
| TIC/TSC | Structures NVIDIA de texture et sampler |
| VI / NVNFlinger | Services/chaîne de composition et présentation Nintendo |
| Vulkan | API graphique utilisée pour exécuter le rendu sur la PS5 |

### 17.3 Politique d'actualisation

- À chaque évolution de la topologie NS1/NS2, mettre à jour les owners et les chemins de ce document en même temps que le code.
- Changer les documents historiques seulement lorsqu'un historique est explicitement corrigé ; pour le statut **actuel**, privilégier le registre vivant, les commits et les CI au bon SHA.
- Actualiser le pointeur gitlink vendor et le SHA source de l'analyse dans une nouvelle révision datée ; ne pas réécrire silencieusement les conclusions techniques historiques.
- Vérifier les URL officielles et arXiv lorsqu'elles sont utilisées dans une décision d'optimisation ; la présence d'une référence n'est pas une validation de l'hypothèse.
- Toute amélioration de performance doit conserver une preuve de fidélité CPU/GPU, d'absence de régression et — si visée PS5 runtime — de résultat matériel.

---

**Portée du document :** inventaire raisonné des composants centraux observés et des dépendances majeures au 19/11/2026. L'exhaustivité au niveau de chaque fonction, du graphe CMake exact et des versions transitives relève des catalogues de sources / tests CI, pas de cette synthèse. Aucun code source, correctif, binaire ou paramètre runtime n'a été modifié pour sa rédaction.
