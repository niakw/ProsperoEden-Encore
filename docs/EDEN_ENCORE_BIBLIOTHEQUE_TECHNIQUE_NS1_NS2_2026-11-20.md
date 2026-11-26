# EDEN ENCORE — Bibliothèque technique NS1 / NS2

**Catalogue de référence pour le portage sur PS5 (firmware 13.60)**
**Édition : 20 novembre 2026 · Langue : français · Format : Markdown autonome**
**Statut : catalogue documentaire publié sur `main` ; aucun correctif C++ ni build PS5 n'est requis par ce document.**

> **But.** Disposer d'un point d'entrée pérenne vers les connaissances publiques sur Nintendo Switch 1 (NS1), Nintendo Switch 2 (NS2), Horizon OS, les services IPC, les SVC, les fichiers de jeux, les GPU NVIDIA, les shaders, Vulkan/RADV et les implémentations de référence. Ce document **n'est pas** un audit du code d'Eden Encore et ne doit pas remplacer les registres d'incidents ni les preuves console.
>
> **Attention.** Les API homebrew (`libnx`, `libounce`, `drako3d`) décrivent d'abord des clients ou environnements alternatifs ; elles ne prouvent pas, seules, les commandes ni la sémantique interne du firmware Nintendo. Les spécifications et dumps communautaires sont partiels ; chaque hypothèse dépend de la **génération, du firmware et des paramètres de service**.

## Sommaire

1. [Mode d'emploi et niveaux de confiance](#1-mode-demploi-et-niveaux-de-confiance)
2. [Les 15 entrées à connaître en priorité](#2-les-15-entrées-à-connaître-en-priorité)
3. [SwitchBrew : répertoire central NS1 + NS2](#3-switchbrew--répertoire-central-ns1--ns2)
4. [IPC, SVC, kernel et Horizon OS](#4-ipc-svc-kernel-et-horizon-os)
5. [Switch 2 : sources et implémentations spécialisées](#5-switch-2--sources-et-implémentations-spécialisées)
6. [GPU NVIDIA : Maxwell, GA10F, mémoire et commandes](#6-gpu-nvidia--maxwell-ga10f-mémoire-et-commandes)
7. [Shaders, traductions et pipeline Vulkan/RADV](#7-shaders-traductions-et-pipeline-vulkanradv)
8. [BufferCache, TextureCache, DMA et frame pacing](#8-buffercache-texturecache-dma-et-frame-pacing)
9. [Fichiers, loader, RomFS, ExeFS, NCA/NSO/NPDM](#9-fichiers-loader-romfs-exefs-ncansonpdm)
10. [Émulateurs et code de comparaison](#10-émulateurs-et-code-de-comparaison)
11. [Parcours de diagnostic par symptôme Eden Encore](#11-parcours-de-diagnostic-par-symptôme-eden-encore)
12. [Règles de veille, vérification et réutilisation](#12-règles-de-veille-vérification-et-réutilisation)
13. [Index thématique condensé](#13-index-thématique-condensé)

---

## 1. Mode d'emploi et niveaux de confiance

### Couverture

- **NS1** : Switch originale, SoC Tegra X1 et GPU GM20B / famille Maxwell, environnement Horizon historiquement mieux documenté.
- **NS2** : Switch 2, environnement Horizon et GPU GA10F documentés progressivement ; les pages communes de SwitchBrew peuvent désormais indiquer « S1/S2 ».
- **Hôte PS5** : Vulkan, RADV, synchronisation, compilation SPIR-V et performance du pilote AMD ; il ne faut pas confondre documentation du GPU *invité* Nintendo/NVIDIA et celle du GPU *hôte* AMD.

### Légende des fiches

| Marqueur | Signification |
|---|---|
| **P0** | Ressource prioritaire pour l'absence de démarrage / première frame NS2, loader, kernel, IPC, mémoire ou GPU |
| **P1** | Ressource prioritaire pour FC27 NS1 : textures, shaders, BufferCache, latence, rendu, frame pacing |
| **S** | Spécification ou wiki technique communautaire : information directement documentée, à comparer aux firmwares |
| **I** | Code d'implémentation consultable ; référence comportementale **non automatiquement identique** à Horizon officiel |
| **D** | Documentation fournisseur ou standard (NVIDIA, ARM, Khronos, AMD, Mesa) |
| **H** | Archive ou ressource historique pouvant être périmée |
| **R** | Recherche émergente / communauté : confirmer l'origine, la méthode, la date et les preuves |

**Méthode de lecture conseillée :** (1) trouver le contrat sur SwitchBrew/SwIPC ; (2) comparer son évolution entre NS1 et NS2 ; (3) regarder le code client (`libnx`/`libounce`) et, si disponible, une réimplémentation ; (4) vérifier une autre implémentation indépendante ; (5) confronter avec les logs/SHAs et le chemin *effectivement compilé* par Eden Encore. Une analogie ne suffit jamais à déclarer une cause démontrée.

---

## 2. Les 15 entrées à connaître en priorité

| Priorité | Ressource | NS1 / NS2 | Ce qu'il faut chercher |
|---|---|---|---|
| 1 · P0 | [SwitchBrew — accueil](https://switchbrew.org/wiki/Main_Page) | NS1 + NS2 | Index du système, firmwares, hardware, kernel, services et formats |
| 2 · P0 | [SwitchBrew — Services API](https://switchbrew.org/wiki/Services_API) | NS1 + NS2 | Colonnes de disponibilité S1/S2, `sm:`, noms de services, suppressions, ajouts |
| 3 · P0 | [SwitchBrew — SVC](https://switchbrew.org/wiki/SVC) | NS1 + NS2 | ABI kernel, maps, objets, droits, états mémoire et synchronisation |
| 4 · P0 | [SwitchBrew — HIPC](https://switchbrew.org/wiki/IPC_Marshalling) | NS1 + NS2 | En-têtes IPC, descripteurs X/A/B/C, handles, PID, erreurs |
| 5 · P0 | [SwitchBrew — GSV services](https://switchbrew.org/wiki/Switch_2:_GSV_services) | NS2 | Services graphiques, session `nvdrv2`, ordonnanceur/syncpoints |
| 6 · P0 | [SwitchBrew — Compatibility Mode](https://switchbrew.org/wiki/Switch_2:_Compatibility_Mode) | NS1 sur NS2 | Substitutions et différences de comportement liées à la rétrocompatibilité |
| 7 · P0 | [SwIPC](https://reswitched.github.io/SwIPC/) | NS1 historique | Command ID, objets, tailles/handles/buffers, versions ; ne pas extrapoler NS2 |
| 8 · P0 | [libnx](https://github.com/switchbrew/libnx) | NS1 | Client IPC/SVC concret, initialisation des services, structures C |
| 9 · P0 | [Atmosphère](https://github.com/Atmosphere-NX/Atmosphere) | NS1 | Comportement kernel/loader/services par réimplémentation partielle |
| 10 · P0 | [ounce-devkit / libounce](https://github.com/ouncebrew/ounce-devkit) | NS2 | API Switch 2, compatibilité libnx, exemples système |
| 11 · P0/P1 | [drako3d](https://github.com/ouncebrew/drako3d) | NS2 (et NS1 via architecture sélectionnée) | GPU GA10F, commandes NVN2, transferts, MSAA, synchronisation |
| 12 · P1 | [deko3d](https://github.com/devkitPro/deko3d) | NS1 | Maxwell, classes GPU, structures et commandes matérielles |
| 13 · P1 | [Yuzu — Buffer Cache Rewrite](https://yuzu-mirror.github.io/entry/yuzu-bcr/) | NS1 / principes | Suivi GPU-dirty, pages, uploads, lectures GPU→CPU, coût des invalidations |
| 14 · P1 | [Khronos — Synchronization Examples](https://docs.vulkan.org/guide/latest/synchronization_examples.html) | PS5 hôte | Barrières, disponibilité/visibilité, synchronisation transfert↔dessin |
| 15 · P1 | [Mesa — RADV](https://docs.mesa3d.org/drivers/radv.html) | PS5 hôte | Pilote AMD, compilateur, paramètres et spécificités Vulkan |

**Ce tableau est une liste de lecture, pas un classement de qualité scientifique.** La compatibilité réelle se prouve sur le couple moteur/vendor/firmware et sur console.

---

## 3. SwitchBrew : répertoire central NS1 + NS2

SwitchBrew a intégré les informations de l'ancien wiki `switch2brew.org`, lequel annonce explicitement sa fusion. **Utiliser SwitchBrew comme lien canonique et `switch2brew` comme archive**, non comme deuxième source indépendante.

### 3.1 Architecture, kernel, versions et compatibilité

| Page | Rôle et application pratique | Couverture / statut |
|---|---|---|
| [Main Page](https://switchbrew.org/wiki/Main_Page) | Carte du système ; accès aux index Hardware, Horizon et Switch 2 | NS1 + NS2 · S |
| [Glossary](https://switchbrew.org/wiki/Glossary) | Définition de GPU, GMMU, NCA, NCM, NPDM, NVDEC, SVC, TSEC, etc. | NS1 + NS2 · S |
| [Services API](https://switchbrew.org/wiki/Services_API) | La page comparative *S1 / S2* à lire avant tout stub de service | NS1 + NS2 · **P0** · S |
| [SVC](https://switchbrew.org/wiki/SVC) | Identifiants et contrats de syscalls, objets, threads, memory types, permissions | NS1 + NS2 · **P0** · S |
| [HIPC / IPC Marshalling](https://switchbrew.org/wiki/IPC_Marshalling) | Transport IPC, descripteurs et structure des requêtes/réponses | NS1 + NS2 · **P0** · S |
| [Memory layout](https://switchbrew.org/wiki/Memory_layout) | Mémoire système, régions réservées et mémoire matérielle | NS1, extensions à vérifier · P0 · S |
| [Security Mitigations](https://switchbrew.org/wiki/Security_Mitigations) | Changements de protections et contraintes d'exécution, mention de cas NS2 | NS1 + NS2 · S |
| [System Versions](https://switchbrew.org/wiki/System_Versions) | Historique des versions du système NS1 | NS1 · S |
| [Switch 2: System Versions](https://switchbrew.org/wiki/Switch_2:_System_Versions) | Versions NS2, dates, versions SDK | NS2 · **P0** · S |
| [Title list](https://switchbrew.org/wiki/Title_list) | Program IDs et modules de NS1 | NS1 · S |
| [Switch 2: Title list](https://switchbrew.org/wiki/Switch_2:_Title_list) | Program IDs et modules NS2 ; liens entre services et sysmodules | NS2 · **P0** · S |
| [Switch 2: Title list / Games](https://switchbrew.org/wiki/Switch_2:_Title_list/Games) | Inventaire communautaire de jeux/Title IDs, couverture non garantie | NS2 · S |
| [Switch 2: Compatibility Mode](https://switchbrew.org/wiki/Switch_2:_Compatibility_Mode) | Différences d'exécution et de rétrocompatibilité, modules/paramètres associés | NS1 sur NS2 · **P0** · S |
| [System Settings](https://switchbrew.org/wiki/System_Settings) | Réglages système NS1 susceptibles d'influer sur le comportement observé | NS1 · S |
| [Switch 2: System Settings](https://switchbrew.org/wiki/Switch_2:_System_Settings) | Paramètres/flags NS2 et leurs versions | NS2 · **P0** · S |
| [System Version Title](https://switchbrew.org/wiki/System_Version_Title) | Format du module de version et différences NS2 décrites | NS1 + NS2 · S |

**À retenir :** la disponibilité d'un *nom* de service n'établit pas l'identité de ses **commandes**, ni de leurs structures, privilèges, buffers ou chemins de sérialisation. Un service peut être renommé, déplacé ou partiellement compatible.

### 3.2 Services et moteurs système

| Page | Données principales | Usage Eden Encore |
|---|---|---|
| [Filesystem services](https://switchbrew.org/wiki/Filesystem_services) | `fsp-srv`, opérations fichiers, RomFS, sauvegardes, erreurs | Loader/RomFS NS1/NS2 · P0 |
| [Applet Manager / AM services](https://switchbrew.org/wiki/AM_services) | Application proxies, lifecycle, applets, événements | Écrans de chargement, démarrage, pause · P0/P1 |
| [HID services](https://switchbrew.org/wiki/HID_services) | NPAD, événements, shared memory, capteurs, commandes selon version | Latence manette/menus FC27 · P1 |
| [Audio services](https://switchbrew.org/wiki/Audio_services) | AudioIn, AudioOut, AudioRenderer, codecs/services associés | Audio/vidéo NS1/NS2 · P1 |
| [VI services](https://switchbrew.org/wiki/VI_services) | Display, layers, événements VSync, présentation | Première frame et frame pacing · P0/P1 |
| [NV services](https://switchbrew.org/wiki/NV_services) | `nvdrv`, ioctls, channels, NVMAP, syncpoints | GPU Maxwell NS1 · P0/P1 |
| [Switch 2: GSV services](https://switchbrew.org/wiki/Switch_2:_GSV_services) | Nouveaux échanges GPU/`nvdrv2`, handles, contextes | Initialisation GPU NS2 · **P0** |
| [GPU](https://switchbrew.org/wiki/GPU) | Mémoire GPU, macros, mappings, fence/report semaphore | Cache GPU, DMA, barrières · P1 |
| [GPU Classes](https://switchbrew.org/wiki/GPU_Classes) | Méthodes et classes des moteurs du GPU invité | Maxwell/engines/methods · P1 |
| [GPU Shaders](https://switchbrew.org/wiki/GPU_Shaders) | Formats et ISA shaders Maxwell, types de pipeline | Shader recompiler NS1 · P1 |
| [NS services](https://switchbrew.org/wiki/NS_services) | Gestion des applications et contenus | NS1/NS2 launch · P0 |
| [Settings services](https://switchbrew.org/wiki/Settings_services) | Valeurs `set:*`, région, langues, paramètres | HLE/launcher · P2, mais P0 si un boot dépend d'un flag |
| [Shared Database services](https://switchbrew.org/wiki/Shared_Database_services) | Données partagées / compatibilité NS2 | Comportements par jeu · P0 |
| [Category: Services](https://switchbrew.org/wiki/Category:Services) | Répertoire des sous-pages dont *Switch 2: Nvkernel* et *VI2* | Recherche NS2 à partir de l'index · P0 |

### 3.3 Fichiers, formats et logiciels

| Page | Apport |
|---|---|
| [NCA / NCA Format](https://switchbrew.org/wiki/NCA) | Nintendo Content Archive, partitions, patching, RomFS et métadonnées |
| [ExeFS](https://switchbrew.org/wiki/ExeFS) | Contenu de la partition exécutable et ses modules |
| [NSO0](https://switchbrew.org/wiki/NSO0) | Format des modules exécutables NSO, segments, compression, relations au loader |
| [NRO0](https://switchbrew.org/wiki/NRO) | Format homebrew NRO, assets et éventuel RomFS |
| [NPDM](https://switchbrew.org/wiki/NPDM) | Métadonnées, ACL, permissions et différences observées NS2 |
| [Homebrew ABI](https://switchbrew.org/wiki/Homebrew_ABI) | Contrat ABI homebrew (ne pas confondre avec ABI des jeux officiels) |
| [Title list / Games](https://switchbrew.org/wiki/Title_list/Games) | Table communautaire des jeux NS1 et Title IDs |
| [Flash Filesystem](https://switchbrew.org/wiki/Flash_Filesystem) | Organisation mémoire persistante / partitions système |

**Piège de version :** comparer également les notes firmware [22.0.0](https://switchbrew.org/wiki/22.0.0) (évolution de la compression NSO signalée) et [23.5.0](https://switchbrew.org/wiki/23.5.0) si une incompatibilité n'apparaît qu'avec un firmware récent. Une documentation de format NS1 ne suffit pas à affirmer que chaque variante NS2 est déjà gérée.

---

## 4. IPC, SVC, kernel et Horizon OS

### 4.1 Définitions et clients

| Ressource | Statut | Contenu / précaution |
|---|---|---|
| [SwIPC — interface web](https://reswitched.github.io/SwIPC/) | NS1 · **H**, **P0** | Catalogue lisible des interfaces, `Command ID`, types, buffers, handles, conditions historiques `@version` |
| [SwIPC — dépôt](https://github.com/reswitched/SwIPC) | NS1 · **H**, **P0** | Déclarations `.id` et scripts. Le README décrit les définitions « as of version 3.0 » ; ne pas le considérer comme base firmware moderne/NS2 |
| [SwIPC — interfaces](https://reswitched.github.io/SwIPC/ifaces.html) | NS1 · **H** | Accès direct à la liste des interfaces IPC |
| [libnx — dépôt](https://github.com/switchbrew/libnx) | NS1 · **I**, **P0** | Appels `svc*`, `serviceDispatch*`, clients `am`, `fs`, `hid`, `nvdrv` ; références d'usage |
| [libnx — documentation Doxygen](https://switchbrew.github.io/libnx/) | NS1 · **I** | Structures et signatures publiques de la bibliothèque |
| [libnx — SVC headers](https://github.com/switchbrew/libnx/blob/master/nx/include/switch/kernel/svc.h) | NS1 · **I**, **P0** | Signatures concrètes des appels SVC et types mémoire |
| [libnx — historique des changements](https://github.com/switchbrew/libnx/blob/master/Changelog.md) | NS1 · **I** | Changements par version de service et découverte de correctifs clients |
| [Atmosphère](https://github.com/Atmosphere-NX/Atmosphere) | NS1 · **I**, **P0** | Mesosphère/kernel, loader, gestion de processus, réimplémentations de composants Horizon |
| [Atmosphère — mesosphère](https://github.com/Atmosphere-NX/Atmosphere/tree/master/mesosphere) | NS1 · **I**, **P0** | Source d'une implémentation alternative du kernel ; vérifier ABI et licence |
| [Atmosphère — notes de version](https://github.com/Atmosphere-NX/Atmosphere/blob/master/docs/changelog.md) | NS1 · **I** | Comportements changés avec les firmwares, éléments corrigés/contournés |
| [ReSwitched — Awesome Switch](https://reswitched.github.io/awesome/) | NS1 · **H** | Ancien index de documentation, conférences et reverse engineering ; non actualisé substantiellement depuis 2019 |
| [Switch Security — 34C3](https://switchbrew.github.io/34c3-slides/) | NS1 · **H** | Présentation historique de la pile matérielle et système Switch |

### 4.2 Questions concrètes à résoudre avec ces sources

1. **Un IPC échoue** : quelle combinaison `service name / commande / firmware / descripteur / handle` est demandée ? Est-elle présente sur NS2 ?
2. **Un SVC est invalide** : numéro, paramètres AArch64, état des objets, permissions NPDM et taille mémoire attendue sont-ils identiques ?
3. **Le jeu stagne avant le GPU** : quel thread invité attend une réponse de service, un événement, un thread, une session ou un handle ?
4. **Erreur de retour mais pas de crash** : le HLE émule-t-il un code d'erreur qui fait entrer le jeu dans une boucle de retry ?
5. **Différence NS1/NS2** : le client libnx ou libounce utilise-t-il un chemin alternatif plutôt qu'une API identique ?

**Hiérarchie de preuve pour une commande IPC :** page SwitchBrew actualisée et versionnée → code client avec arguments effectivement sérialisés → observation comportementale sur la bonne génération → implémentation indépendante → code local. SwIPC seul n'est jamais une preuve pour NS2.

---

## 5. Switch 2 : sources et implémentations spécialisées

| Ressource | Apport précis | Portée et précautions |
|---|---|---|
| [SwitchBrew — Switch 2: System Versions](https://switchbrew.org/wiki/Switch_2:_System_Versions) | Matrice firmware/SDK NS2 | **S**, P0, à consulter avant toute interprétation de service |
| [SwitchBrew — Switch 2: Title list](https://switchbrew.org/wiki/Switch_2:_Title_list) | Modules système, Program IDs, versions | **S**, P0 ; couverture communautaire évolutive |
| [SwitchBrew — Switch 2: Compatibility Mode](https://switchbrew.org/wiki/Switch_2:_Compatibility_Mode) | Rétrocompatibilité NS1, chemins spéciaux | **S**, P0 ; n'impose pas que l'émulateur reproduise la rétrocompatibilité matérielle |
| [SwitchBrew — Switch 2: System Settings](https://switchbrew.org/wiki/Switch_2:_System_Settings) | Flags/valeurs/versions | **S**, P0 ; vérifier les valeurs réellement utilisées par les titres |
| [SwitchBrew — Switch 2: GSV services](https://switchbrew.org/wiki/Switch_2:_GSV_services) | Service graphics, sessions, synchronisations | **S**, **P0** |
| [ounce-devkit](https://github.com/ouncebrew/ounce-devkit) | Intégration de libounce, OunceVK, libkaihen, exemples, toolchain | **I**, **P0** ; kit **homebrew**, pas SDK officiel des jeux |
| [kaiHEN](https://github.com/ouncebrew/kaihen) | `ldr:ro`, sessions, processus, JIT pour homebrew Switch 2 | **I**, P0 ; sa stratégie loader n'est pas le loader Horizon officiel |
| [drako3d](https://github.com/ouncebrew/drako3d) | GPU GA10F, API bas niveau inspirée du reverse engineering NVN2 | **I**, **P0/P1** ; pas un clone de NVN2 et pas un interpréteur des jeux commerciaux |
| [Switch2 Homebrew Documentation](https://github.com/SwitchFW-Tools/switch2-homebrew-docs) | Notes matérielles et recherche système NS2 | **R** ; vérifier auteurs, sources et validation indépendante |
| [Switch 2 NPDM Explorer](https://tasenjo80.github.io/switch2-npdm-explorer/index.html) | Exploration des permissions/services des sysmodules NS2 | **R** ; outil d'orientation, non preuve définitive d'ABI |
| [switch2brew.org](https://switch2brew.org/wiki/Main_Page) | Ancien wiki NS2 | **H**, **fusionné dans SwitchBrew**, pas source canonique |

### Ouncebrew — référence prioritaire pour les contrats clients NS2 (24 novembre 2026)

[Organisation et liste complète des dépôts Ouncebrew](https://github.com/orgs/ouncebrew/repositories). Écosystème homebrew Switch 2 complémentaire de SwitchBrew, et non synonyme de l'ancien wiki switch2brew.org. Examiner le code client et les exemples avant de conclure qu'une commande inconnue est optionnelle.

| Dépôt | Usage Eden Encore |
|---|---|
| [libounce](https://github.com/ouncebrew/libounce) | **P0** : client IPC/SVC NS2, séquences de bootstrap, tailles, handles MOVE/COPY, événements, NVDRV, GSV, vidéo. [gsv.c, révision 32e7ac41](https://github.com/ouncebrew/libounce/blob/32e7ac414ee1cd98922f66a059be5a85e99feea5/nx/source/switch2/services/gsv.c) : référence déjà exploitée pour GSV 126, Syncpt 21/103/201. README : ISC (libnx/libounce), vérifier chaque fichier. |
| [ouncevk](https://github.com/ouncebrew/ouncevk) | **P0/P1** : Vulkan/EGL/GL côté invité, backend NVIDIA, VA/GMMU, soumission et synchronisation ; vérifier le fichier et la licence exacts avant réutilisation. |
| [drako3d](https://github.com/ouncebrew/drako3d) | **P0/P1** : API GPU bas niveau Tegra T239, commandes, queues, mémoire, formats et shaders. |
| [uam2](https://github.com/ouncebrew/uam2) | **P0/P1** : compilateur drako3d, Mesa NAK, SM 8.6, DKSH, SPIR-V/GLSL et ABI shader NS2. Référence pour des fixtures indépendantes, pas remplacement du recompiler Encore. |
| [ounce-examples](https://github.com/ouncebrew/ounce-examples) | **P0** : exemples clients homebrew, scénarios minimaux reproductibles indépendamment des titres commerciaux. |
| [ounce-devkit](https://github.com/ouncebrew/ounce-devkit) | Intégration toolchain, libounce, OunceVK et libkaihen ; environnement invité, pas SDK PS5. |

Les résultats de la comparaison sont consignés dans le [registre fonctionnel NS2](audits/EDEN_ENCORE_NS2_IMPLEMENTATION_COMPLETENESS_REGISTER_2026-11-21.md). Pour toute divergence, relever le SHA amont, comparer firmware/ABI/effets et le propriétaire C++ actif ; ne jamais transformer une réussite homebrew en preuve de gameplay commercial sur PS5.

### Ce que ces sources ne prouvent pas

- Une méthode `libounce` réussissant sur du homebrew **n'implique pas** que tous les titres NS2 utilisent la même séquence IPC.
- Une commande GPU drako3d documentée **n'implique pas** que toute la sémantique NVN2 est connue.
- Une page SwitchBrew peut décrire une version de firmware précise ou un cas observé, sans couvrir toutes les versions.
- Les exemples OunceVK concernent l'environnement Switch 2 ; le GPU hôte du portage Eden Encore reste celui de la PS5 avec RADV et ses contraintes.

---

## 6. GPU NVIDIA : Maxwell, GA10F, mémoire et commandes

### 6.1 Sources invité NS1/NS2

| Ressource | Architecture / sujet | Application |
|---|---|---|
| [SwitchBrew — GPU](https://switchbrew.org/wiki/GPU) | Mappings GMMU, NV services, macros, fences | Comprendre les registres et les transferts invités NS1 |
| [SwitchBrew — GPU Classes](https://switchbrew.org/wiki/GPU_Classes) | Classes et méthodes des moteurs | Comparer `Maxwell3D`, DMA, Fermi2D, compute, syncpoints |
| [SwitchBrew — GPU Shaders](https://switchbrew.org/wiki/GPU_Shaders) | Instructions, stages et format Maxwell | Vérifier les hypothèses du shader recompiler NS1 |
| [deko3d](https://github.com/devkitPro/deko3d) | API et registres bas niveau Tegra X1 / Maxwell | Contrepoint public aux structures du moteur Eden |
| [deko3d — Primer](https://github.com/devkitPro/deko3d/blob/master/Primer.md) | Tutoriel de commandes GPU, mémoire, barrières, fences, shaders | Lecture prioritaire pour `RasterizerVulkan`, BufferCache et sync |
| [devkitPro/uam](https://github.com/devkitPro/uam) | Compilateur shaders pour deko3d (Maxwell, Mesa/Nouveau) | Comprendre la chaîne shader NS1, ne pas importer sans comparaison |
| [drako3d](https://github.com/ouncebrew/drako3d) | API bas niveau GA10F / commandes NVN2 | Référence phare pour la génération NS2 |
| [NVIDIA Open GPU Documentation](https://nvidia.github.io/open-gpu-doc/) | Interfaces matérielles NVIDIA publiées | Comparaison par **classe et architecture exacte**, pas extrapolation PC→Tegra |
| [NVIDIA — dépôt open-gpu-doc](https://github.com/NVIDIA/open-gpu-doc) | Headers, classes, ISA, moteurs, architecture Maxwell/Turing/Ampere | Recherches par nom de classe, registre et format |
| [envytools — documentation](https://envytools.readthedocs.io/en/latest/index.html) | Matériel NVIDIA, envydis/envyas, moteurs graphiques | Reverse engineering et nomenclature des registres |
| [envytools — Hardware](https://envytools.readthedocs.io/en/latest/hw/index.html) | GPU, moteur 2D/3D, transferts, mémoire | Comprendre les ordres et mécanismes non documentés ailleurs |
| [envytools — dépôt](https://github.com/envytools/envytools) | Source des outils et des données matérielles | Recherches de champs et générations de GPU |

### 6.2 Questions utiles pour le GPU

- Les adresses sont-elles des **GPU virtual addresses** ou des adresses CPU physiques/émulées ? Quelle page GMMU en possède la version récente ?
- Une copie DMA source→destination traverse-t-elle plusieurs mappings ou un trou ? Les segments physiques sont-ils contigus ?
- Quand la mémoire invitée est GPU-dirty, le BufferCache/TextureCache publie-t-il les writes *avant* un readback CPU ?
- Les barrières assurent-elles **l'ordre** et **la visibilité mémoire**, pas seulement l'ordre des commandes ?
- Un buffer remplacé reste-t-il vivant tant que les commandes GPU précédentes le référencent ?
- NS2 émet-il une classe/méthode incompatible avec la table Maxwell NS1 ?

**Attention aux architectures :** GM20B/Maxwell (NS1) et GA10F (NS2) ne partagent pas automatiquement le même ISA shader, les mêmes descripteurs, les mêmes formats de ressources ou les mêmes méthodes de classes. De même, les documents NVIDIA pour GPU de PC sont une **aide par analogie**, pas une spécification matérielle complète du Tegra concerné.

---

## 7. Shaders, traductions et pipeline Vulkan/RADV

| Ressource | Type | Intérêt pour Eden Encore |
|---|---|---|
| [Khronos — Vulkan Guide](https://docs.vulkan.org/guide/latest/) | **D** | Vue d'ensemble des contrats Vulkan sur l'hôte |
| [Khronos — Synchronization Examples](https://docs.vulkan.org/guide/latest/synchronization_examples.html) | **D** | Exemples host write→transfer, copy→shader, queue/barrier/fence |
| [Khronos — Profiling](https://docs.vulkan.org/guide/latest/profiling.html) | **D** | Bulles GPU, barrières trop générales, stalls, pipeline/submit |
| [Khronos — Wait Idle sample](https://docs.vulkan.org/samples/latest/samples/performance/wait_idle/README.html) | **D** | Coûts des attentes GPU globales et alternatives par frames en vol |
| [Khronos — Vulkan-Docs](https://github.com/KhronosGroup/Vulkan-Docs) | **D** | Spécification et modèle formel de synchronisation |
| [Khronos — SPIR-V Registry](https://registry.khronos.org/SPIR-V/) | **D** | Format et instruction set SPIR-V, extensions, versions |
| [Khronos — SPIRV-Tools](https://github.com/KhronosGroup/SPIRV-Tools) | **D** | `spirv-val`, `spirv-opt`, `spirv-dis`, réduction de modules fautifs |
| [Khronos — What is SPIR-V](https://docs.vulkan.org/guide/latest/what_is_spirv.html) | **D** | Traduction, validation et diagnostic des shaders |
| [Mesa — RADV](https://docs.mesa3d.org/drivers/radv.html) | **D** | Backend AMD Vulkan de la PS5, limites du pilote, configuration |
| [Mesa — RADV hang debugging](https://docs.mesa3d.org/drivers/amd/hang-debugging.html) | **D** | Méthode de diagnostic GPU hangs — options exactes à vérifier sur le port PS5 |
| [Mesa — GPU hangs and misrenderings](https://docs.mesa3d.org/graphics-debugging/debugging-misrenderings-crashes.html) | **D** | Localiser draw/dispatch fautif, distinguer crash de rendu et driver |
| [Mesa — Environment variables](https://docs.mesa3d.org/envvars.html) | **D** | Options de debugging, statistiques caches/pipelines ; **pas** toutes prises en charge sur PS5 |
| [AMD — RDNA Performance Guide](https://gpuopen.com/learn/rdna-performance-guide/) | **D** | Synchronisation, queues, barrières, CPU overhead et gestion mémoire |
| [AMD — Radeon GPU Profiler](https://gpuopen.com/manuals/rgp_manual/) | **D** | Comprendre queues, fences, événements GPU ; compatibilité PS5 à vérifier |
| [devkitPro/uam](https://github.com/devkitPro/uam) | **I** | Référence de compilation Maxwell de shaders maison |

**Protocole de comparaison utile :** shader invité original → IR du recompiler → SPIR-V avant/après transformation → validation SPIR-V → pipeline créé → ressources/descripteurs liés → commande GPU soumise → présentation. Si la frame reste absente, chercher d'abord **le premier maillon qui ne progresse pas**, plutôt qu'ajouter des logs dans tous les suivants.

---

## 8. BufferCache, TextureCache, DMA et frame pacing

### 8.1 Études historiques d'émulateurs

| Étude | Ce qu'elle explique |
|---|---|
| [Yuzu — Buffer Cache Rewrite](https://yuzu-mirror.github.io/entry/yuzu-bcr/) | Pourquoi mettre en cache les buffers GPU, comment suivre les régions modifiées, comment limiter les copies |
| [Yuzu — Texture Cache Rewrite](https://yuzu-mirror.github.io/entry/yuzu-tcr/) | Réutilisation, invalidation et ownership des textures, réécritures structurelles historiques |
| [Yuzu — Vulkan Feature](https://yuzu-mirror.github.io/entry/yuzu-vulkan/) | Architecture originale du backend Vulkan et du buffer cache |
| [Yuzu — Progress Report May 2023](https://yuzu-mirror.github.io/entry/yuzu-progress-report-may-2023/) | Cache des buffers, mémoire, invalidations et corrections liées au rendu |
| [Yuzu — Progress Report February 2023](https://yuzu-mirror.github.io/entry/yuzu-progress-report-feb-2023/) | GPU texture decoding, compute et coûts CPU |
| [Yuzu — Progress Report August 2023](https://yuzu-mirror.github.io/entry/yuzu-progress-report-aug-2023/) | QueryCache, rendu conditionnel et attentes/synchronisation |
| [Lichii — correctifs comparables (recherche PR)](https://github.com/zortos293/Lichii/pulls?q=is%3Apr+buffer+cache) | Prendre les **diffs exacts** liés au symptôme et leur justification, pas importer en bloc |
| [Lichii #414 — quad index buffers](https://github.com/zortos293/Lichii/pull/414) | Remplacer un `scheduler.Finish()` lors de la croissance par retraite à tick GPU |
| [Lichii #1518 — page protections](https://github.com/zortos293/Lichii/pull/1518) | Contention des verrous et ordre de publication des protections (attention aux rollbacks) |
| [Lichii #191 — readbacks](https://github.com/zortos293/Lichii/issues/191) | Coût/correction des téléchargements GPU→CPU et risques de cohérence |

### 8.2 Questions indispensables avant de changer un cache

1. **Ownership :** quelle copie est la plus récente pour chaque octet (CPU invité, buffer GPU hôte, image GPU hôte) ?
2. **Aliases :** une adresse GPU fragmentée ou remappée pointe-t-elle vers plusieurs pages CPU, éventuellement sous plusieurs GPU VAs ?
3. **Granularité :** marque-t-on une sous-plage, une page, une image entière ? Une copie partielle invalide-t-elle trop ou pas assez ?
4. **GPU→CPU :** un readback se déclenche-t-il sous `std::recursive_mutex` ou un verrou texture et appelle-t-il `runtime.Finish()` ?
5. **CPU→GPU :** une écriture CPU doit-elle être publiée avant `DMA Clear`, un draw, un upload ou l'accès shader ?
6. **Ordre :** le lock protège-t-il seulement les structures du cache ou également un transfert GPU en attente ?
7. **Durée de vie :** les buffers/images anciens sont-ils conservés jusqu'au tick de consommation GPU ?
8. **Performance réelle :** la réduction des opérations sous mutex affecte-t-elle la frame critique ou seulement un microbenchmark hôte ?

**Règle de sûreté :** ne jamais éliminer un `Finish`, déplacer une protection de page ou simplifier une invalidation sans démontrer la conservation des données GPU voisines, des alias et des règles de synchronisation. Les rollbacks historiques d'Eden Encore rendent cela prioritaire.

### 8.3 Comprendre les « 30 FPS saccadés »

À 30 FPS, l'intervalle idéal est d'environ **33,33 ms** par nouvelle image. Le compteur FPS peut rester proche de 30 alors que des frames arrivent irrégulièrement ; il faut mesurer les intervalles réels, p50/p95/p99, les pauses >100 ms, le nombre d'images *nouvelles* et la latence entre entrée et image. Les ressources recommandées pour cette question sont :

- [Khronos — Profiling](https://docs.vulkan.org/guide/latest/profiling.html) : identifier les bulles CPU/GPU et les attentes induites par les barrières.
- [Khronos — Wait Idle](https://docs.vulkan.org/samples/latest/samples/performance/wait_idle/README.html) : reconnaître une attente de complétion GPU qui bloque tout le pipeline.
- [AMD — RDNA Performance Guide](https://gpuopen.com/learn/rdna-performance-guide/) : stratégies de soumission/synchronisation.
- [Mesa — RADV](https://docs.mesa3d.org/drivers/radv.html) : ce que fait le backend d'exécution sur l'hôte AMD.
- [Yuzu — Buffer Cache Rewrite](https://yuzu-mirror.github.io/entry/yuzu-bcr/) : comment les invalidations et uploads peuvent peser sur l'émulation.

**À ne pas conclure :** une forte attente cumulée des verrous sur plusieurs threads n'est pas directement convertible en nombre de millisecondes perdues *par frame*. De même, des shader misses cumulés n'expliquent pas automatiquement toutes les pauses. Les événements doivent être corrélés temporellement.

---

## 9. Fichiers, loader, RomFS, ExeFS, NCA/NSO/NPDM

| Ressource | Utilité / limites |
|---|---|
| [SwitchBrew — NCA](https://switchbrew.org/wiki/NCA) | Sections de contenu, chiffrement, partition exécutable, patchs et RomFS |
| [SwitchBrew — ExeFS](https://switchbrew.org/wiki/ExeFS) | Arborescence exécutable, modules présents / `main.npdm` |
| [SwitchBrew — NSO0](https://switchbrew.org/wiki/NSO0) | Segments du binaire, compression, chargement et relocation selon versions |
| [SwitchBrew — NRO0](https://switchbrew.org/wiki/NRO) | ABI/format homebrew, différent du package titre officiel |
| [SwitchBrew — NPDM](https://switchbrew.org/wiki/NPDM) | ACL/services/permissions/capabilities ; changements NS2 |
| [SwitchBrew — Filesystem services](https://switchbrew.org/wiki/Filesystem_services) | `fsp-srv` et opérations de montage et métadonnées |
| [NSTool](https://github.com/jakcron/nstool) | Parseur/extracteur de nombreux formats Switch ; lire le code source de décodage |
| [SciresM/hactool](https://github.com/SciresM/hactool) | Parseur des conteneurs Nintendo, sections NCA et informations formats |
| [Ghidra Switch Loader](https://github.com/Adubbz/Ghidra-Switch-Loader) | Analyse statique de modules NSO/NPDM ; vérifier support des extensions NS2 |
| [Switch-Toolbox](https://github.com/KillzXGaming/Switch-Toolbox) | Recherche de formats assets/ressources, modèles et textures ; utile surtout pour visualiser |
| [ReSwitched — Awesome](https://reswitched.github.io/awesome/) | Anciennes références sur les formats et outils, ne pas utiliser comme index à jour |

**Exemple d'analyse du lancement :** vérifier séparément l'archive NCA, le patch/update effectivement appliqué, les sections ExeFS/RomFS, l'ABI des NSO, les permissions NPDM, le service FS et le loader du firmware ciblé. Un format « reconnu » ne garantit ni un montage juste, ni l'exécution correcte d'un processus NS2.

**Cadre juridique :** cette bibliothèque documente des formats et des interfaces. Elle n'héberge ni fichiers de jeux, ni firmware, ni clés privées. Respecter les droits sur les contenus, les licences des outils et la législation applicable.

---

## 10. Émulateurs et code de comparaison

**But : trouver une implémentation indépendante d'un comportement, pas copier aveuglément des patchs conçus pour un autre système.** Conserver les recherches par signatures et les raisons de non-applicabilité.

| Projet | À regarder pour | Limite |
|---|---|---|
| [Eden Encore — moteur](https://github.com/niakw/ProsperoEden-Encore) | Source active et chemin de build PS5 | Le gitlink doit sélectionner le vendor étudié |
| [Eden Encore — vendor](https://github.com/niakw/Prospero.Eden-Encore-vendor) | BufferCache, TextureCache, rasterizer, runtime et overrides | Source présente ≠ source sélectionnée par CMake |
| [Lichii](https://github.com/zortos293/Lichii) | GPU, kernels, DMA, synchronisation, NS1/NS2 | Certaines hypothèses sont spécifiques à une branche GPU ou au backend PC |
| [Eden — dépôt miroir GitHub](https://github.com/eden-emulator/mirror) | Travaux upstream et historique du moteur Eden | Le miroir GitHub peut différer du dépôt de développement canonique |
| [Eden — documentation Debug](https://github.com/eden-emulator/mirror/blob/master/docs/Debug.md) | Méthodes historiques d'investigation dans Eden | Adapter les diagnostics à la PS5 et aux outils disponibles |
| [Eden — Issue Reports](https://github.com/eden-emulator/Issue-Reports) | Signatures de bugs jeu et logs collectés par upstream | Fermer une issue ne valide pas la PS5 |
| [Eden Issue Reports](https://github.com/eden-emulator/Issue-Reports) | Signatures de jeux/Title IDs, crashs et comparaisons | Le bug peut être lié à un firmware ou à un pilote autre que PS5 |
| [Yuzu — documentation historique](https://yuzu-mirror.github.io/) | Approfondissements historiques sur les caches et Vulkan | Historique ; performances et architecture non identiques à Encore |
| [Ryubing / Ryujinx docs](https://docs.ryujinx.app/) | Conception d'une émulation GPU/HLE indépendante en C# | Projet communautaire différent, comportements à vérifier |
| [Dynarmic](https://github.com/lioncash/dynarmic) | JIT ARM, traduction et backend | Vérifier la provenance/licence/version du fork utilisé |
| [Dynarmic — Design (archive)](https://github.com/yuzu-mirror/dynarmic/blob/master/docs/Design.md) | Traduction en IR, compilation de blocs, état du CPU | Document historique, APIs susceptibles d'avoir changé |
| [libnx](https://github.com/switchbrew/libnx) | Observations sur les services client plutôt que HLE | Client homebrew, non équivalent à un service système officiel |
| [Atmosphère](https://github.com/Atmosphere-NX/Atmosphere) | Référence pour des mécanismes kernel / processus | Réimplémentation sous contraintes et licences propres |

**Comparaison rigoureuse par correctif :** fichier/fonction identifiés → version upstream/commit → test d'origine → invariant mémoire ou ABI → diff PS5 → licence → risque de régression → preuve console nécessaire. Ne jamais considérer un « issue closed » comme preuve de correction sur la PS5.

---

## 11. Parcours de diagnostic par symptôme Eden Encore

### P0 — NS2 : jeu lancé, chargement infini, zéro première frame

**Objectif : établir à quel maillon la progression cesse, sans supposer d'emblée une panne Vulkan.**

1. **Titre, loader et firmware :** [NS2 Title list](https://switchbrew.org/wiki/Switch_2:_Title_list), [NS2 System Versions](https://switchbrew.org/wiki/Switch_2:_System_Versions), [NCA](https://switchbrew.org/wiki/NCA), [NPDM](https://switchbrew.org/wiki/NPDM), [ExeFS](https://switchbrew.org/wiki/ExeFS).
2. **Services/HLE :** [Services API S1/S2](https://switchbrew.org/wiki/Services_API), [HIPC](https://switchbrew.org/wiki/IPC_Marshalling), [SwIPC historique](https://reswitched.github.io/SwIPC/), [libounce](https://github.com/ouncebrew/libounce).
3. **Kernel/JIT :** [SVC](https://switchbrew.org/wiki/SVC), [Atmosphère/mesosphère](https://github.com/Atmosphere-NX/Atmosphere/tree/master/mesosphere), [Dynarmic](https://github.com/lioncash/dynarmic).
4. **Commandes GPU :** [GSV services](https://switchbrew.org/wiki/Switch_2:_GSV_services), [drako3d](https://github.com/ouncebrew/drako3d), [GPU Classes](https://switchbrew.org/wiki/GPU_Classes).
5. **Sortie GPU hôte :** [Khronos sync](https://docs.vulkan.org/guide/latest/synchronization_examples.html), [RADV](https://docs.mesa3d.org/drivers/radv.html).

**À relever dans le registre existant :** moteur SHA, vendor SHA, Title ID, firmware simulé, dernier PC/IPC/SVC guest progressant, commande GPU émise ou non, premier `vkQueueSubmit` attendu, première présentation et résultat PS5. Pas de conclusion « shader bug » si aucune commande GPU invitée n'est arrivée.

### P1 — FC27 NS1 : maillots incorrects ou textures périmées

**Lectures :** [deko3d Primer](https://github.com/devkitPro/deko3d/blob/master/Primer.md), [Yuzu Texture Cache](https://yuzu-mirror.github.io/entry/yuzu-tcr/), [Yuzu Buffer Cache](https://yuzu-mirror.github.io/entry/yuzu-bcr/), [GPU de SwitchBrew](https://switchbrew.org/wiki/GPU), [Vulkan synchronization](https://docs.vulkan.org/guide/latest/synchronization_examples.html).

**Hypothèses à distinguer :** rendu de texture invalide, upload depuis une copie CPU périmée, DMA fragmenté, invalidation manquante, protection d'image annulée trop tôt, mapping GMMU, image encore GPU-dirty, shader de décompression ou format ASTC. Ne pas « optimiser » en supprimant la copie correcte.

### P1 — FC27 NS1 : HUD/pause retardés, manette non réactive

**Lectures :** [HID services](https://switchbrew.org/wiki/HID_services), [AM services](https://switchbrew.org/wiki/AM_services), [SVC](https://switchbrew.org/wiki/SVC), [libnx](https://github.com/switchbrew/libnx), [Vulkan Profiling](https://docs.vulkan.org/guide/latest/profiling.html).

**Hypothèses à départager :** l'entrée arrive mais le thread de jeu est bloqué ; l'HUD est mis à jour tardivement ; une requête IPC/sync ralentit l'événement ; la dernière image est répétée faute de nouvelle présentation ; un verrou cache retarde la disponibilité de la ressource d'interface. Chronologie input → guest update → GPU draw HUD → present indispensable.

### P1 — FC27 NS1 : compteur ~30 FPS mais grosses saccades

**Lectures :** [Khronos Wait Idle](https://docs.vulkan.org/samples/latest/samples/performance/wait_idle/README.html), [Khronos Profiling](https://docs.vulkan.org/guide/latest/profiling.html), [AMD RDNA Performance](https://gpuopen.com/learn/rdna-performance-guide/), [Yuzu BCR](https://yuzu-mirror.github.io/entry/yuzu-bcr/), [Mesa RADV](https://docs.mesa3d.org/drivers/radv.html).

**Mesures requises :** p50/p95/p99 frametimes, pauses >100/500 ms, shader first-use, pipeline build/lookup, temps d'acquisition **par frame et par thread**, GPU fence, submit→present, répétition de frames, cache froid/chaud. Des FPS moyens élevés ne prouvent pas une distribution régulière.

### P0/P1 — OOM, corruption, SIGSEGV et fermeture impossible

**Lectures :** [SVC memory](https://switchbrew.org/wiki/SVC), [Memory layout](https://switchbrew.org/wiki/Memory_layout), [Dynarmic Design](https://github.com/yuzu-mirror/dynarmic/blob/master/docs/Design.md), [Mesa hangs](https://docs.mesa3d.org/drivers/amd/hang-debugging.html), [Vulkan synchronization](https://docs.vulkan.org/guide/latest/synchronization_examples.html).

**Contrats à examiner :** durée de vie des allocations invitées et hôtes, protection/déprotection, barrières, ownership d'objets Vulkan, cache invalidé après unmap, nettoyage asynchrone et ordre de destruction. Ne pas assimiler un test hôte vert à une validation PS5.

### P1 — Shader stage manquant / première compilation très longue

**Lectures :** [GPU Shaders](https://switchbrew.org/wiki/GPU_Shaders), [NVIDIA Open GPU Docs](https://nvidia.github.io/open-gpu-doc/), [drako3d](https://github.com/ouncebrew/drako3d), [SPIR-V](https://registry.khronos.org/SPIR-V/), [SPIRV-Tools](https://github.com/KhronosGroup/SPIRV-Tools), [Mesa RADV](https://docs.mesa3d.org/drivers/radv.html).

**Distinguer :** instruction GPU invitée inconnue, mauvais décodage, mauvaise traduction en IR, SPIR-V invalide, erreur de création pipeline, synchronisation des workers et premier usage du shader.

### P0 — RomFS/ExeFS / chargement de contenu NS1 ou NS2

**Lectures :** [NCA](https://switchbrew.org/wiki/NCA), [ExeFS](https://switchbrew.org/wiki/ExeFS), [NSO0](https://switchbrew.org/wiki/NSO0), [NPDM](https://switchbrew.org/wiki/NPDM), [Filesystem services](https://switchbrew.org/wiki/Filesystem_services), [hactool](https://github.com/SciresM/hactool), [nstool](https://github.com/jakcron/nstool).

**Distinguer :** archive/layer incorrect, programme indexé erroné, NSP/NCA de mise à jour manquant, invalid NPDM, compression NSO propre au firmware, montage FS inadapté, IPC FS refusé, ROM patching incorrect.

---

## 12. Règles de veille, vérification et réutilisation

### 12.1 Fiche minimale pour une nouvelle source

```text
Titre :
URL canonique :
Catégorie : kernel / IPC / GPU / FS / audio / firmware / JIT / hôte Vulkan / outil
Couverture : NS1 / NS2 / les deux / hôte PS5
Statut : S / I / D / H / R
Date de consultation :
Version / révision / commit concerné :
Information démontrée (citation courte + contexte) :
Ce que la source NE démontre PAS :
Anomalie Eden Encore associée (Title ID, signature, fonction) :
Chemin moteur/vendor effectivement compilé :
Invariants, ABI et licence :
Décision technique envisageable / raison de non-applicabilité :
```

### 12.2 Ordre de consultation sans tourner en rond

1. **Symptôme exact + révision console** : chercher d'abord dans les documents existants du projet.
2. **Matrice système** : choisir SwitchBrew NS1/NS2, firmware et service/format précis.
3. **Code référence** : un client (`libnx`, `libounce`) puis une implémentation (`Atmosphère`, `drako3d`, fork d'émulateur).
4. **Amont ciblé** : issues/PR/commit par signature, en vérifiant les rollbacks.
5. **Source active PS5** : confirmer CMake, overrides, vendor gitlink et chemin vraiment exécuté.
6. **Correctif fonctionnel justifié** si cause suffisante, puis tests proportionnés et PS5 ultérieurement — jamais de promesse de performance sans mesure.

### 12.3 Veille conseillée

| Fréquence | Sources | Motif |
|---|---|---|
| À chaque nouveau symptôme NS2 | SwitchBrew S2 Services, GSV, SVC, versions ; drako3d ; libounce | Interfaces et classes GPU évoluent vite |
| À chaque régression de cache | Lichii PR/commits ; Yuzu historiques ; deko3d ; Khronos | Préserver ownership et barrières |
| À chaque anomalie de formats | SwitchBrew NCA/NPDM/NSO ; hactool/nstool ; notes firmware | Éviter de confondre structure et variante de firmware |
| Lors de changement Mesa/vendeur | Mesa RADV release/debug ; Vulkan Guide ; GPUOpen | Nouveau comportement compilateur, barrières ou mémoire |
| Périodiquement, hors P0/P1 | ReSwitched Awesome, notes tierces, anciens dépôts | Patrimoine de recherche ; ne pas relancer d'audit général |

### 12.4 Références internes Eden Encore à conserver comme contexte, non comme nouvelles sources externes

- `docs/ENCORE_TECHNICAL_ARCHITECTURE_AND_RESEARCH.md`
- `docs/audits/ENCORE_STATIC_CODE_ARCHITECTURE_OPTIMIZATION_AUDIT_2026-11-19.md`
- `docs/FC27_F07_MASTER_TRACKER.md`
- Registres d'incidents PS5, NS1/NS2, couples de SHAs, logs console.

**La bibliothèque ne remplace pas ces registres.** Elle doit orienter vers les bons travaux amont lorsque le symptôme exige une correction, sans créer de nouveaux chemins `EXPERIMENTAL` ni détourner les chantiers prioritaires.

### 12.5 Licence et provenance

- Liens vers la documentation ≠ autorisation de copier intégralement son code. Vérifier la licence **du fichier et du commit exact** ; Atmosphère, libnx, deko3d, drako3d, kaiHEN et les émulateurs peuvent utiliser des licences différentes.
- Éviter les forks anonymes présentant des affirmations techniques sans tests ou preuves.
- Les textes et dumps communautaires peuvent omettre des variantes NS2. Une documentation plus récente n'est pas nécessairement plus exacte.
- La « première frame GPU invitée » ne se démontre pas par le seul lancement du programme, pas plus que 30 FPS moyens ne démontrent une fluidité stable.
- **Ce document est volontairement extérieur à GitHub `main`.** Son intégration ultérieure dans `docs/` est une décision distincte, à coordonner avec l'autre conversation de développement ; elle ne doit déclencher aucun build par surprise.

---

## 13. Index thématique condensé

Cet index est destiné à la recherche rapide, y compris lors d'une nouvelle conversation.

| Sujet | Premières sources |
|---|---|
| Services IPC NS1 | [SwIPC](https://reswitched.github.io/SwIPC/) · [libnx](https://github.com/switchbrew/libnx) · [Services API](https://switchbrew.org/wiki/Services_API) |
| Services IPC NS2 | [Services API](https://switchbrew.org/wiki/Services_API) · [GSV](https://switchbrew.org/wiki/Switch_2:_GSV_services) · [libounce](https://github.com/ouncebrew/libounce) |
| Kernel, SVC, MMU | [SVC](https://switchbrew.org/wiki/SVC) · [mesosphère](https://github.com/Atmosphere-NX/Atmosphere/tree/master/mesosphere) · [Memory layout](https://switchbrew.org/wiki/Memory_layout) |
| Démarrage, AM | [AM services](https://switchbrew.org/wiki/AM_services) · [NPDM](https://switchbrew.org/wiki/NPDM) · [NS services](https://switchbrew.org/wiki/NS_services) |
| Manette/latence | [HID](https://switchbrew.org/wiki/HID_services) · [AM](https://switchbrew.org/wiki/AM_services) · [Vulkan Profiling](https://docs.vulkan.org/guide/latest/profiling.html) |
| Première frame NS2 | [GSV](https://switchbrew.org/wiki/Switch_2:_GSV_services) · [drako3d](https://github.com/ouncebrew/drako3d) · [Vulkan Guide](https://docs.vulkan.org/guide/latest/) |
| GPU Maxwell | [GPU Classes](https://switchbrew.org/wiki/GPU_Classes) · [deko3d](https://github.com/devkitPro/deko3d) · [UAM](https://github.com/devkitPro/uam) |
| GPU GA10F | [drako3d](https://github.com/ouncebrew/drako3d) · [NVIDIA Open GPU](https://nvidia.github.io/open-gpu-doc/) |
| GPU DMA / GMMU | [SwitchBrew GPU](https://switchbrew.org/wiki/GPU) · [deko3d Primer](https://github.com/devkitPro/deko3d/blob/master/Primer.md) · [Khronos Sync](https://docs.vulkan.org/guide/latest/synchronization_examples.html) |
| BufferCache | [Yuzu BCR](https://yuzu-mirror.github.io/entry/yuzu-bcr/) · [Lichii PR](https://github.com/zortos293/Lichii/pulls?q=is%3Apr+buffer+cache) |
| TextureCache | [Yuzu TCR](https://yuzu-mirror.github.io/entry/yuzu-tcr/) · [Yuzu 2023](https://yuzu-mirror.github.io/entry/yuzu-progress-report-feb-2023/) |
| Shaders Maxwell | [GPU Shaders](https://switchbrew.org/wiki/GPU_Shaders) · [UAM](https://github.com/devkitPro/uam) · [envytools](https://envytools.readthedocs.io/en/latest/index.html) |
| SPIR-V et pipelines | [SPIR-V registry](https://registry.khronos.org/SPIR-V/) · [SPIRV-Tools](https://github.com/KhronosGroup/SPIRV-Tools) · [RADV](https://docs.mesa3d.org/drivers/radv.html) |
| Present / 30 FPS | [Wait Idle](https://docs.vulkan.org/samples/latest/samples/performance/wait_idle/README.html) · [Vulkan Profiling](https://docs.vulkan.org/guide/latest/profiling.html) · [GPUOpen RDNA](https://gpuopen.com/learn/rdna-performance-guide/) |
| GPU hangs | [RADV hang debugging](https://docs.mesa3d.org/drivers/amd/hang-debugging.html) · [Mesa misrenderings](https://docs.mesa3d.org/graphics-debugging/debugging-misrenderings-crashes.html) |
| Loader et archives | [NCA](https://switchbrew.org/wiki/NCA) · [NSO0](https://switchbrew.org/wiki/NSO0) · [ExeFS](https://switchbrew.org/wiki/ExeFS) · [nstool](https://github.com/jakcron/nstool) |
| Permissions de processus | [NPDM](https://switchbrew.org/wiki/NPDM) · [Switch 2 NPDM explorer](https://tasenjo80.github.io/switch2-npdm-explorer/index.html) |
| JIT AArch64 | [Dynarmic](https://github.com/lioncash/dynarmic) · [Design](https://github.com/yuzu-mirror/dynarmic/blob/master/docs/Design.md) · [SVC](https://switchbrew.org/wiki/SVC) |
| Rétrocompatibilité NS1/NS2 | [Compatibility Mode](https://switchbrew.org/wiki/Switch_2:_Compatibility_Mode) · [Services S1/S2](https://switchbrew.org/wiki/Services_API) |
| Audio / vidéo | [Audio services](https://switchbrew.org/wiki/Audio_services) · [VI services](https://switchbrew.org/wiki/VI_services) · [NV services](https://switchbrew.org/wiki/NV_services) |

**Maintenance documentaire :** compléter uniquement avec des sources nouvelles réellement pertinentes, une nouvelle information vérifiée ou un changement majeur de firmware. En cas de lien mort, conserver l'URL d'origine, ajouter une archive ou le successeur explicitement identifié et indiquer la date de vérification. Aucune réécriture automatique des registres P0/P1.

---

### Notes de provenance de cette édition

La recherche de cette édition a consulté principalement : les pages SwitchBrew indiquant explicitement les générations S1/S2 ; le dépôt officiel de SwIPC et son README précisant la couverture historique ; les dépôts et READMEs de `switchbrew/libnx`, `Atmosphere-NX/Atmosphere`, `ouncebrew/ounce-devkit`, `ouncebrew/kaihen`, `ouncebrew/drako3d`, `devkitPro/deko3d`, `NVIDIA/open-gpu-doc`, `envytools/envytools`, les pages de référence Khronos/Mesa et les articles historiques de Yuzu. Les liens thématiques constituent un **catalogue d'orientation**, pas une affirmation que tous les dépôts ont été compilés ni que leurs API sont compatibles avec le build PS5.

**Fin du document — version autonome intégrée à `docs/` ; voir aussi [l'analyse des écarts NS2 puis NS1](audits/EDEN_ENCORE_GAP_ANALYSIS_NS2_THEN_NS1_2026-11-20.md).**