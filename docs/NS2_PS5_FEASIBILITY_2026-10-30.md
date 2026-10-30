# Nintendo Switch 2 (NS2) sur PS5 — étude de faisabilité, branche isolée

**Date : 30 octobre 2026** · **État : RECHERCHE / A64 FRONTEND SYNTAX CHECK VERT / NON TESTÉ SUR PS5**  
**Branche :** `research/ns2-ps5-compatibility`, initialement issue de l’ancienne branche de développement puis resynchronisée sur `main` le 30 octobre 2026.  
**Protection :** aucune modification du chemin de compilation/release F07, aucune PR vers la branche de production, aucun build PS5 de jeu NS2 autorisé à ce stade.

## 0. Début concret du portage expérimental — 30/10/2026

- **Socle :** branche de recherche resynchronisée avec `main` (conservation du sous-module `vendor` et du travail F07), sans modifier `main` ni publier de release.
- **Premier composant adapté :** `headless/ns2/overrides/core/file_sys/program_metadata.{h,cpp}`, issu d'Eden-NS2 (fichiers `4682cf7ab52e7509802885d63dfc2498613e305f` et `074c6f7908b367e20a7d0c59eb2289aeccee5fec`, licences conservées), avec vérification explicite des bornes, des offsets relatifs FAC/FAH et détection ACID `0x200` (Switch 1) / `0x300` (Switch 2).
- **Intégration CMake :** seul `EDEN_NS2_METADATA_EXPERIMENTAL=ON` sélectionne la source maintenue et son header ; **OFF par défaut**, aucune modification du snapshot `vendor/sources/eden`.
- **Test reproductible :** `python3 tools/check-ns2-npdm-host.py` compile le helper exact `headless/ns2/npdm_layout.h` en C++20 `-O0` et `-O2` avec UBSan ; teste les deux dispositions, la priorité Switch 1, les données tronquées et les dépassements d'entiers.
- **Limite :** le test vérifie le helper de sélection et la présence du câblage source ; la compilation réelle de `core`, les changements loader/HLE/JIT/GPU et tout lancement sur PS5 **restent à faire**. Ce chantier ne suffit pas à prendre en charge un jeu NS2.
- **Prochain lot :** détection contrôlée ExeFS `main` et activation Dynarmic compatible avec ACID étendu, suivis d'une compilation hôte du chemin réellement sélectionné, avant les services et la traduction GPU.

### N2a — LDAPR + RETAA/RETAB expérimentaux (frontend A64)

- Sources amont retenues : `0x2593/Eden-NS2` RETA mais intégrées dans **l'ancienne base Dynarmic épinglée d'Encore**, sous `headless/ns2/dynarmic/` et **pas** dans `vendor`.
- `EDEN_NS2_A64_EXPERIMENTAL=ON` (exige le profil metadata) copie `a64.h`, `a64.inc` et `a64_branch.cpp` dans l'overlay prioritaire de compilation Dynarmic. La table de décodage reconnaît RETAA/RETAB et les variantes LDAPR (RCpc). Le traducteur utilise `RET(X30)` pour les retours authentifiés (PAC désactivé) et **LDAR** pour LDAPR (acquire plus fort), uniquement en mode recherche.
- Cette traduction suppose les clés PAC désactivées. Elle ne simule pas la validation cryptographique, ne concerne pas encore les autres opcodes PAC et n'autorise pas à déclarer l'ARMv8.3 entièrement compatible.
- Témoin hôte source-lié : `python3 tools/check-ns2-reta-host.py` compile la table `a64.inc` réelle, teste RETAA/RETAB, RET normal, LDAPR W/X et les non-correspondances, sous `-O0/-O2` avec UBSan.
- Validation restant nécessaire : **compiler le vrai frontend Dynarmic avec l'option ON, puis tester les flux JIT sur PS5**, sans cette preuve la couverture reste au niveau source/decoder.

#### Qualification hôte du frontend A64 — 30/10/2026

- **Source expérimentale compilée :** `vendor/encore-active/eden-core/src/dynarmic/frontend/A64/translate/a64_translate.cpp` avec les cinq fichiers overlay sélectionnés de la famille A64, `EDEN_NS2_A64_EXPERIMENTAL=1`, `clang++ -std=c++20 -fsyntax-only`, et le sous-module épinglé. Aucun fichier de l'amont n'est altéré.
- **CI verte sur le code :** [`#41023251179`](https://github.com/niakw/ProsperoEden-Encore/actions/runs/41023251179), commit `7a778a04b88e519ed9e2dc3860d9d4b340b571b5` ; jobs `dynarmic-a64-syntax` et `research-host` **SUCCESS**.
- **Environnement exact :** `fmt 12.1.0` (commit `407c905e45ad75fc29bf0f9bb7c5c2fd3475976f`, correspondant à `vendor/sources/eden/cpmfile.json`). Le premier essai avec `libfmt-dev` Ubuntu a échoué sur `fmt::format_string::get()` ; échec de dépendance hôte, pas un défaut établi du traducteur.
- **Portée :** syntaxe/instanciation du vrai frontend et modèles de décodage avec UBSan O0/O2. Cela **ne vérifie pas** la compilation de tout Dynarmic, le fonctionnement du JIT A64 dans le runtime Encore, la mémoire NS2 ou des jeux PS5.
- **Étape suivante prioritaire :** portage sécurisé des instructions atomiques LSE/CAS/SWP, avec des tests de valeurs et concurrence, et compilation réelle du `core` quand les services et le gestionnaire de mémoire seront prêts.

### N2d — Six cœurs invités et moniteur exclusif (opt-in)

- **Blocage réel de la base Eden Switch 1 :** `Core::Hardware::NUM_CPU_CORES=4` et `Dynarmic::ExclusiveMonitor::MAX_NUM_CPU_CORES=4`. Eden-NS2 utilise **6** pour les cœurs applicatifs (avec 4 cœurs conservés pour les règles legacy et un remappage virtuel 6/7/63 vers le cœur système).
- **Portage isolé :** `headless/ns2/cpu6/core/hardware_properties.h` et `headless/ns2/cpu6/dynarmic/interface/exclusive_monitor.h`, repris du fork `0x2593/Eden-NS2` sous leurs licences respectives. Les en-têtes sont ajoutés aux chemins de compilation **uniquement** si `EDEN_NS2_CPU6_EXPERIMENTAL=ON`, avec exigences `EDEN_NS2_A64_EXPERIMENTAL` et `EDEN_NS2_METADATA_EXPERIMENTAL`.
- **Garde de release :** l'option à six cœurs reste **OFF par défaut** et est rejetée dans `EDEN_FINAL_RELEASE_PROFILE`. Aucun changement des limites globales pour les builds Switch 1 courants.
- **Validation hôte :** le vrai JIT x86-64 expérimental utilise désormais un `ExclusiveMonitor{6}` et teste six workers concurrents avec réservations/retries sur un même emplacement mémoire. **Cette validation doit passer en CI avant toute déclaration de multicœur qualifié.**
- **Limites :** les schedulers et services Switch 2, le chemin JIT PS5, les 6 cœurs invités réellement exécutés et le comportement mémoire console ne sont pas encore validés.

### N2b — CPU LSE atomique (recherche uniquement)

- Depuis `0x2593/Eden-NS2`, portage ciblé des premières familles LSE : `CAS`, `LDADD`, `LDCLR`, `LDEOR`, `LDSET`, `SWP`, y compris les sous-formes 8/16 bits annoncées par les variantes `B/H`. Les fonctions sont ajoutées à `load_store_exclusive.cpp` et à la table/déclarations du frontend A64.
- Modèle amont d'opérations atomiques : instructions traduites en lectures/écritures exclusives avec un chemin de réessai sur échec, sémantique d'ordre acquire/release spécifiée pour `A/R`. **La correction de ce modèle sous contention réelle n'est pas encore prouvée**.
- La sélection reste confinée à `EDEN_NS2_A64_EXPERIMENTAL=ON` ; aucun changement de `main`, de l'archive Eden épinglée ni de release.
- Témoins mis à jour pour les motifs du décodeur ; **le vrai frontend a été recompilé en vérification syntaxique sur le SHA de ce lot (deux jobs verts)**. Restent notamment CASP, autres LSE, PAC complet, GPU SM86, HLE et budget 12 Gio.

**Validation N2b sur le SHA `0f85999a52efeed594c364f56c45e56bd78e99b9` :** [CI #41023661808](https://github.com/niakw/ProsperoEden-Encore/actions/runs/41023661808), deux jobs **SUCCESS** : C++20/UBSan O0/O2 pour la table réelle, et syntax-check `clang++` du vrai `a64_translate.cpp` maintenu avec l'overlay NS2 et `fmt 12.1.0` épinglé. **Cela n'est pas un test du comportement atomique sous contention, ni un build PS5, ni un lancement de jeu.**

### N1b — ExeFS expérimental, chargement par étapes

- `EDEN_NS2_EXEFS_EXPERIMENTAL=ON` (exige `EDEN_NS2_METADATA_EXPERIMENTAL=ON`) remplace deux fichiers du loader uniquement dans la branche de recherche.
- Un fichier `main` doit être un vrai NSO dans un dossier ExeFS reconnu, et le loader de répertoire est examiné **avant** le loader NSO brut.
- Le chemin standalone enregistre son `RomFSFactory`, recherche un `.romfs` ou un répertoire `romfs` à proximité, et évite d'utiliser NCE avec un ACID étendu.
- Sources : portage ciblé de `0x2593/Eden-NS2` sur les sources maintenues du sous-module `vendor` épinglé à `92c5829174a1169c507b72438021d3dfa9e5dfa2` ; le chargeur NSZ/XCZ et l'alignement 16 Kio sont conservés.
- **Garde-fou :** `python3 tools/check-ns2-source-selection.py` contrôle la priorité CMake, le maintien NSZ/XCZ et l'alignement PS5.
- **État : CODE RECHERCHE, PAS ENCORE COMPILÉ.** Vérifier la propriété réelle des fichiers CMake, la compilation et les API de ce snapshot avec les options ON avant de prétendre que le bootstrap NS2 fonctionne.

### N2c — Tests NPDM réels et resynchronisation du socle F07

- **Test comportemental :** `tools/ns2/test_program_metadata.cpp` exécute réellement `ProgramMetadata::Load` sur des NPDM synthétiques Switch 1 et 2, vérifie `IsSwitch2()`, les titres et les formats invalides. Il ne fournit aucun firmware, clé ou jeu.
- **CI :** [#41024466016](https://github.com/niakw/ProsperoEden-Encore/actions/runs/41024466016), commit `c0c17243f56473556c72401a4fb313f986b745e9`, **2 jobs verts**, compilations réelles des sources (syntax-check), tests d'exécution sous ASan/UBSan.
- **Maintien du socle :** synchronisation de `main` **vers la branche de recherche seulement**, après contrôle de l'absence de chemins modifiés en commun (21 fichiers NS2 distincts des 8 fichiers F07 évolués). Aucun merge vers `main`.
- **Non validé :** JIT exécuté, comportement atomique sous contention, mémoire 12 Gio, GPU Ampere, services HLE et jeu NS2 sur PS5.

## 1. Conclusion provisoire

**Faisabilité technique : plausible à long terme, non démontrée pour Encore sur PS5.**
Le fork de 0x2593 revendique un vrai affichage 3D en jeu sous Windows (Donkey Kong Bananza), mais **5 à 8 FPS**, des vidéos non décodées et des défauts de synchronisation/mémoire. Cela **ne prouve pas** qu'Encore sur PS5 peut démarrer un jeu NS2. La PS5 n'est pas un PC Windows, et le port natif utilise ses propres chemins mémoire, JIT, GPU et Vulkan/RADV.

**Critère de succès cible :** un titre NS2 détenu par l'utilisateur, issu d'un dump personnel, peut charger, afficher des frames correctes, recevoir la manette, sauvegarder et reprendre sur PS5, avec métriques et sans régression du mode Switch 1. **Aucun de ces critères n'est encore validé sur PS5.**

## 2. Sources vérifiées (30/10/2026)

| Source | Résultat confirmé par inspection | Limite |
| --- | --- | --- |
| [0x2593/Eden-NS2](https://github.com/0x2593/Eden-NS2) · HEAD `de4f49702a381e3f01d7d9752643740d251e6be0` | Fork expérimental de [ShadyHero/Eden-NS2](https://github.com/ShadyHero/Eden-NS2), dérivé d'Eden, GPL-3.0-or-later ; README annonce menu Bananza 60 FPS, gameplay 3D 5–8 FPS sur Windows 11 et GPU NVIDIA Turing | Déclaration du mainteneur, sans validation PS5 ni reproduction indépendante |
| [README détaillé](https://github.com/0x2593/Eden-NS2/blob/main/README.md), [journal des correctifs](https://github.com/0x2593/Eden-NS2/blob/main/docs/ns2/NOTES.md) | Audio, nouvelles API HLE, GPU Ampere→Maxwell, shaders, GPU worker, atomiques ARMv8.1 LSE, mémoire et synchronisation | Nombreux stubs expérimentaux, dont service vidéo non fonctionnel |
| [NS2.patch](https://github.com/0x2593/Eden-NS2/blob/main/NS2.patch) | Patch de fondation : **154 chemins** `diff --git` (comptage de l'en-tête des diffs) | Patch d'origine attribué à un auteur inconnu dans le README ; provenance et licence du patch à réexaminer |
| [patches/eden-ns2-dkb.patch](https://github.com/0x2593/Eden-NS2/blob/main/patches/eden-ns2-dkb.patch) | Patch consolidé du fork : **166 chemins** ; dont 63 sous `src/core/hle/`, 10 sous `src/video_core/engines/`, 9 sous `src/dynarmic/src/`, 8 sous `src/shader_recompiler/frontend/` | Diff contre Eden **desktop upstream** ; **ne pas l'appliquer tel quel** aux sources PS5 |
| [ShadyHero release v0.0.1](https://github.com/ShadyHero/Eden-NS2/releases) | Première préversion annoncée **Linux uniquement**, avec avertissement explicite d'absence de validation | L'état récent de 0x2593 est plus avancé que cette ancienne préversion |
| [oboromi](https://github.com/0xNikilite/oboromi), [Pound](https://github.com/pound-emu/pound), [Ballistic](https://github.com/pound-emu/ballistic) | Recherches complémentaires CPU ARM et GPU SM86 | Pas de preuve exploitable de jeu commercial NS2 fonctionnel sur PS5 |
| [Switchbrew T239](https://switchbrew.org/wiki/Switch_2%3A_Tegra_T239) | Switch 2 : huit Cortex-A78C, GPU Ampere SM86, 12 Gio physiques | Matériel non identique à la PS5 |

La version vendue/décrite comme « jeux NS2 émulés » ne doit jamais être confondue avec un jeu **jouable** : un menu à 60 FPS et une scène à 5 FPS sont deux étapes distinctes. Les articles antérieurs au 29 octobre 2026 sur « aucun jeu NS2 ne démarre » sont dépassés par les *affirmations* du fork récent, pas remplacés par une validation générale.

## 3. Compatibilité de l'architecture Encore (état / risque)

| Famille | Existant Encore | Besoin NS2 | Risque, priorité |
| --- | --- | --- | --- |
| **CPU/JIT** | Dynarmic x86-64/PS5, JIT sparse et fastmem adaptés | LSE complet, instructions et contrôles ARMv8.1+, PAC/returns selon titres, six cœurs invités utilisables, synchronisation | **P0** : porter uniquement les instructions manquantes, tester sémantique/retry et éviter régressions |
| **Mémoire** | Pool direct natif PS5 partagé entre invité, shaders, JIT et GPU ; budget mesuré au démarrage | Adressage et layout NS2 **12 Gio**, maps GPU, applets ; admission réelle des pages | **P0 bloquant** : **12 Gio de mapping logique ≠ 12 Gio de RAM physique allouable**. Le mode PS5 de base n'offre pas un second pool direct illimité. Nécessité de réserve/commit sparse démontré, plafond et OOM propre |
| **GPU** | Backend Vulkan/RADV natif PS5 et support Maxwell/Turing partiel selon pipeline | Instructions Nvidia Ampere/SM86, géométrie, compute QMD, macro FIFO, surfaces et cohérence des caches | **P0 bloquant** : le chemin « Ampere → Maxwell » du fork puis vers Vulkan doit être adapté sans contourner les garanties RADV, barrières et ownership d'Encore |
| **HLE / IPC** | Services Switch 1 et adaptations maison | Services AM/VI2/NvRm/NvHost/IGpuWorker, plus récents SDK et handles | **P0** : catégoriser chaque commande du patch, refuser les stubs « success » susceptibles de cacher une corruption |
| **Formats / chargement** | NSP/XCI/etc et ExeFS ; profil Switch 1 | NPDM/ACID étendus, réservations GPU, métadonnées, updates & conteneurs NS2 | **P1** : distinguer détection du format et exécution ; ne promettre aucun format NS2 complet sans test |
| **Audio/vidéo** | Audio natif, décodeurs/sortie selon chemin de build | Nouvelle révision du comportement audio ; décodage vidéo NS2 absent dans le fork | **P1/P0 selon jeu** : ne pas traiter un stub codec comme une fonctionnalité prête |
| **UX** | Launcher PS5 et bibliothèque Switch 1 | Identification NS2, profil spécifique, message explicite d'incompatibilité | **P2** : n'afficher « NS2 pris en charge » qu'après validation réelle |
| **Provenance** | Sources immuables `vendor/sources/eden/` + modifications ciblées `vendor/encore-active/` | Port sélectif, versionnement par fichier et preuve de sélection compilée | **P0** : pas de vendorisation intégrale, pas de copie de 858 Ko de patch dans la branche, pas de deuxième implémentation moteur en parallèle |

Le dépôt Encore pointe aujourd'hui vers l'archive Eden **`5f142c7926d0c7fcbbd0ce30794d72f638a43b2a`** (`vendor/sources/eden/VENDOR-ORIGIN.json`). Le patch NS2 est issu d'une base Eden différente, et la correspondance contextuelle/ABI reste à établir. Un inventaire de fichiers existants ne suffit pas à prouver qu'un diff s'applique, encore moins qu'il sera compilé.

**Mémoire PS5 :** la base ProsperoEden documente environ **12 288 Mio de direct memory** sur une PS5 standard sous 13.60 (13 504 Mio en mode PS5 Pro décrit dans l'upstream), partagés entre l'émulation, Vulkan, caches et JIT ; ces chiffres sont des indications de source, **pas** un budget garanti pour Encore. D'abord mesurer la taille du pool, les allocations courantes, la fragmentation et la charge réelle du titre ; ne jamais allouer directement 12 Gio pour « simuler 12 Gio ».

### N3c — GPU/HLE et application-manager, 30/10/2026

- **Provenance :** `0x2593/Eden-NS2@5d2d3cf0a966293fc9ddeac33cf86830a5de206e` pour les trois en-têtes ABI graphiques; décodeur `GpuMemoryRegistration` réduit issu de `NS2.patch.txt` fourni dans la conversation. Les sources sont isolées dans `headless/ns2/hle`.
- **Tests :** `tools/check-ns2-graphics-hle-host.py` compile et exécute des fixtures TIPC, bootstrap, syncpoint, taille image et MMU kind en C++20 O0/O2 sous UBSan. Le [run #41031805494](https://github.com/niakw/ProsperoEden-Encore/actions/runs/41031805494) est **3/3 SUCCESS** sur `dd2555bc707fb70e5ef5afecade9a9a5d8c7815c`.
- **Intégration contrôlée :** `EDEN_NS2_AM_EXPERIMENTAL=ON` sélectionne le handler AM 320 provenant de l'implémentation *maintenue* d'Encore avec en-tête adapté. Il requiert le metadata mode et est refusé par `EDEN_FINAL_RELEASE_PROFILE`. La CI compile réellement le fichier de service, sans encore tester le chemin IPC d'un jeu.
- **Maintien des optimisations :** merge **de `main` vers recherche seulement**, SHA `f2d8e44deb459bd59742c2e23b474ba43b2e2b46` (0 conflit, 43 blobs de recherche conservés, 28 commits F07 récupérés). Le workflow n'a pas encore été exécuté sur ce SHA de fusion ; ne pas substituer la preuve du parent à celle du nouveau commit.
- **Portée :** GPU worker, submit, shaders Ampere→RADV, PS5 memory budget, VI2/display et titres NS2 restent à implémenter/qualifier.

### N3d — Pont shader Ampere → Maxwell CFG / IR, 30/10/2026

- Le décodeur d'instructions 128-bit et l'abaissement natif → Maxwell restent **strictement opt-in** avec `EDEN_NS2_AMPERE_PROBE_EXPERIMENTAL` ; seuls les opcodes/masques explicitement reconnus sont traduits.
- `NativeMaxwellEnvironment` possède désormais son environnement source pour les compilations différées. Son `StartAddress()` est ramené à **0** pour les shaders graphiques : le constructeur CFG Vulkan ajoute déjà les **0x50 octets** de `ProgramHeader`. L'ancienne valeur 0x50 aurait démarré le CFG à 0xA0.
- En-tête SPH et image native doivent être byte-identiques avant de transférer le contexte au traducteur. Les traductions en vol sont rejetées après `NativeTranslationCache::Clear()`, grâce à un numéro de génération.
- `ir_bridge.cpp` réutilise les vrais `Shader::Maxwell::Flow::CFG` et `Shader::Maxwell::TranslateProgram` du shader-recompiler maintenu. Ce fichier est compilé uniquement en recherche ; la CI vérifie sa syntaxe et son ABI côté Clang/GCC.
- **Limite impérative :** il n'existe pas encore de branchement effectif du GPU worker Switch 2 vers les clés de pipeline, l'émission SPIR-V, les modules Vulkan/RADV ou une image PS5 testable. La syntaxe hôte ne prouve ni l'exécution du traducteur complet ni un frame Switch 2 sur PS5.

### N3e — cohérence image/stage et protection du compilateur IR, 30/10/2026

- La CI du code N3d est verte : [run 41073909833](https://github.com/niakw/ProsperoEden-Encore/actions/runs/41073909833), SHA 47e8957.
- Avant d'instancier le Maxwell CFG, le stage source `Shader::Stage` doit correspondre au stage capturé pour l'image (valeur numérique explicite), et non uniquement à un hash de cache ou un flag `Ready`.
- Vérification de l'intégrité du stream, des limites, de la zone de padding et des adresses natives traduites. Tests host négatifs ajoutés pour map incohérente, stage divergent, extent falsifié.
- Ces tests restent distincts de l'exécution complète du compilateur IR, de SPIR-V et de Vulkan/RADV : **aucun titre NS2 sur PS5 n'est validé**.

## 4. Plan d'intégration isolé — ordre d'exécution

| Étape | Livraison et contrôle | État |
| --- | --- | --- |
| **N0 — provenance / audit** | Geler les SHAs upstream, inventorier les 154/166 fichiers et licences ; catégoriser patches exploitables vs desktop-only | **Inventaire réalisé** ; provenance complète et licence tierce encore à confirmer |
| **N1 — compatibilité de sources** | Comparer `NS2.patch` puis `eden-ns2-dkb.patch` à l'archive Eden épinglée, et aux propriétaires *compilés* dans `vendor/encore-active` ; isoler chaque conflit JIT/Vulkan/HLE | **Partiel** : loaders, A64, AM 320 et helpers GPU/HLE isolés ; portage global interdit |
| **N2 — prototype CPU/mémoire hôte** | Tests Dynarmic LSE, PAC/returns, noyau 6 cœurs, NPDM/ACID ; évaluation sparse et budget PS5 avec échec propre | **Tests hôte verts** : JIT x86-64 réel, atomiques/concurrence, parseur NPDM ; budget et exécution PS5 non validés |
| **N3 — prototype GPU hôte** | Shader tests SM86/Maxwell, geometry/compute, FIFO, QMD, GPU worker, syncpoint ; sécurité de cohérence et tests des échecs | **Partiel** : ISA Ampere, images et capture GPU bornées, pont vers le vrai CFG/IR Maxwell ajouté en recherche ; aucune pipeline Vulkan/commande GPU native validée |
| **N4 — services et contenu** | HLE réel vs stubs, audio/vidéo, identification de l'exécutable NS2 ; lancement d'un test homebrew/fixture non propriétaire avant jeu commercial | **AM 320 sélectionnable en build expérimental** + loader ExeFS ; HLE général, GPU supervisor et bootstrap non validés |
| **N5 — compilation native expérimentale** | Seulement après N1–N4 et preuves hôte ; aucun artefact final Switch 1 modifié et pas de fusion F07 | **Non autorisée à ce stade** |
| **N6 — qualification PS5** | Mémoire peak, logs, frames, input, sauvegarde, sortie, redémarrage, crash, régression BOTW/FC27 ; preuve titre/SHA/console | **À faire** |

## 5. Garde-fous et décisions

1. **Ne pas fusionner** cette branche avec `dev/ps5-sparse-jit` et **ne pas ouvrir de PR d'intégration** pendant la recherche. La demande « autre branche » constitue une exception explicite à l'ancienne politique de branche unique, uniquement pour cette investigation.
2. **Ne pas promettre** Donkey Kong Bananza, Mario Kart World ou un autre jeu NS2 jouable sur PS5. Le fork n'apporte aucune preuve PS5.
3. **Pas d'extraction de clés ni de firmware propriétaires dans ce dépôt**, ni de jeux, screenshots de dumps privés, ni de contournement de signature ; ne tester que les contenus détenus/dumpés par l'utilisateur.
4. **Ne pas déclencher un build de release**, une publication ou un package « NS2 » tant que la validation CPU/GPU/mémoire/servicing n'est pas enregistrée.
5. Les modifications tierces sont à porter sous un propriétaire unique `vendor/encore-active/`, avec manifestes de SHA et tests source/hôte/PS5. Les correctifs d'Encore en cours de développement F07 ne doivent pas être écrasés.
6. Toute optimisation future doit conserver les performances Switch 1 et les garanties de sécurité/mémoire, même si un jeu NS2 avance jusqu'au menu.

## 6. Mesure de progrès honnête

- **Branche créée et resynchronisée sur le socle de `main` : oui**.
- **Sources NS2 lues / patches quantifiés : oui**.
- **Patch porté dans l'exécutable Encore : fragments sélectionnables par CMake en builds de recherche, désactivés en release ; exécutable PS5 NS2 non validé**.
- **Tests de compilation NS2 sur PS5 : aucun**.
- **Jeu NS2 démarré sur PS5 : aucun**.
- **Verdict : CPU/JIT, parseur, sondes GPU et un handler HLE vérifiés sur hôte ; aucun binaire public NS2 ni jeu Switch 2 PS5 validé.**

En parallèle, un audit statique reproductible peut être lancé avec `python3 tools/ns2_patch_inventory.py --patch /chemin/eden-ns2-dkb.patch --root .` : il inspecte uniquement les chemins source et ne modifie pas le code.
