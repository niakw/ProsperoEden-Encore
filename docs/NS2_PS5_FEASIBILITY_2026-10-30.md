# Nintendo Switch 2 (NS2) sur PS5 — étude de faisabilité, branche isolée

**Date : 30 octobre 2026** · **État : RECHERCHE / NON INTÉGRÉ / NON TESTÉ SUR PS5**  
**Branche :** `research/ns2-ps5-compatibility`, initialement issue de l’ancienne branche de développement puis resynchronisée sur `main` le 30 octobre 2026.  
**Protection :** aucune modification du chemin de compilation/release F07, aucune PR vers la branche de production, aucun build PS5 de jeu NS2 autorisé à ce stade.

## 0. Début concret du portage expérimental — 30/10/2026

- **Socle :** branche de recherche resynchronisée avec `main` (conservation du sous-module `vendor` et du travail F07), sans modifier `main` ni publier de release.
- **Premier composant adapté :** `headless/ns2/overrides/core/file_sys/program_metadata.{h,cpp}`, issu d'Eden-NS2 (fichiers `4682cf7ab52e7509802885d63dfc2498613e305f` et `074c6f7908b367e20a7d0c59eb2289aeccee5fec`, licences conservées), avec vérification explicite des bornes, des offsets relatifs FAC/FAH et détection ACID `0x200` (Switch 1) / `0x300` (Switch 2).
- **Intégration CMake :** seul `EDEN_NS2_METADATA_EXPERIMENTAL=ON` sélectionne la source maintenue et son header ; **OFF par défaut**, aucune modification du snapshot `vendor/sources/eden`.
- **Test reproductible :** `python3 tools/check-ns2-npdm-host.py` compile le helper exact `headless/ns2/npdm_layout.h` en C++20 `-O0` et `-O2` avec UBSan ; teste les deux dispositions, la priorité Switch 1, les données tronquées et les dépassements d'entiers.
- **Limite :** le test vérifie le helper de sélection et la présence du câblage source ; la compilation réelle de `core`, les changements loader/HLE/JIT/GPU et tout lancement sur PS5 **restent à faire**. Ce chantier ne suffit pas à prendre en charge un jeu NS2.
- **Prochain lot :** détection contrôlée ExeFS `main` et activation Dynarmic compatible avec ACID étendu, suivis d'une compilation hôte du chemin réellement sélectionné, avant les services et la traduction GPU.

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

## 4. Plan d'intégration isolé — ordre d'exécution

| Étape | Livraison et contrôle | État |
| --- | --- | --- |
| **N0 — provenance / audit** | Geler les SHAs upstream, inventorier les 154/166 fichiers et licences ; catégoriser patches exploitables vs desktop-only | **En cours** : sources et volumes identifiés |
| **N1 — compatibilité de sources** | Comparer `NS2.patch` puis `eden-ns2-dkb.patch` à l'archive Eden épinglée, et aux propriétaires *compilés* dans `vendor/encore-active` ; isoler chaque conflit JIT/Vulkan/HLE | **À faire**, pas de `git apply` de masse |
| **N2 — prototype CPU/mémoire hôte** | Tests Dynarmic LSE, PAC/returns, noyau 6 cœurs, NPDM/ACID ; évaluation sparse et budget PS5 avec échec propre | **À faire** |
| **N3 — prototype GPU hôte** | Shader tests SM86/Maxwell, geometry/compute, FIFO, QMD, GPU worker, syncpoint ; sécurité de cohérence et tests des échecs | **À faire** |
| **N4 — services et contenu** | HLE réel vs stubs, audio/vidéo, identification de l'exécutable NS2 ; lancement d'un test homebrew/fixture non propriétaire avant jeu commercial | **À faire** |
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
- **Patch porté dans l'exécutable Encore : non**.
- **Tests de compilation NS2 sur PS5 : aucun**.
- **Jeu NS2 démarré sur PS5 : aucun**.
- **Verdict : premier composant adapté en recherche, sans intégration dans le binaire public ; exécution PS5 non démontrée.**

En parallèle, un audit statique reproductible peut être lancé avec `python3 tools/ns2_patch_inventory.py --patch /chemin/eden-ns2-dkb.patch --root .` : il inspecte uniquement les chemins source et ne modifie pas le code.
