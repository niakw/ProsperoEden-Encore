# R23 — 155/155 commits Eden, triage de pertinence NS1 avec restant exact

**État : audit PR #45, en lecture seule.** L'inventaire des 155 diffs par commit est complet; ce registre applique maintenant une catégorie explicite à **chaque** commit et n'importe aucun code. Un commit classé *runtime à examiner* n'est pas déclaré intégré ou absent sans vraie preuve; un fix testé sur hôte n'est pas validé PS5.

| Catégorie vérifiée au 11 novembre | Commits | État / suite |
|---|---:|---|
| Revue sémantique runtime NS1 ou partagé encore ouverte | **84** | Vérifier vrai propriétaire/équivalence/test ; ne pas importer en masse |
| Changement build/dépendance à qualifier | **6** | Compiler/versions et liens natifs à vérifier |
| Correctif source préparé avec tests hôte | **5** | E3 native, E4 console requis |
| Écart de code source établi mais non validé natif | **7** | Effectivité propriétaire et négatifs requis |
| Non applicable au runtime natif par source | **27** | Ne pas importer ; pas de prétendue preuve PS5 |
| Spécifique host ARM64/NCE non exécutable sur Zen2 | **6** | Exclure backend, conserver tests communs si nécessaires |
| Langues/assets non embarqués | **8** | Pas de portage runtime |
| Test amont de référence seulement | **1** | Corpus utile, pas de correctif binaire |
| Affinité GPU nécessitant mesure PS5 | **1** | Source identifiée, trace console requise |
| Observabilité/log sans changement guest | **2** | Aucun portage comportemental |
| Couple Joycon aller/retour, source restaurée | **2** | Exclusion vérifiée |
| Couple HLE #74/#69, code restauré après normalisation | **2** | [Preuve Git complète](ENCORE_AB_R23_HLE_REVERSION_FINAL_SOURCE_RECEIPT_2026-11-11.md) ; droit/licence conservés |
| Savedata source identique après retour | **1** | Exclusion vérifiée |
| Configuration native OpenSSL équivalente | **1** | Ne pas importer fallback inutilisé |
| Migration Opus/FFmpeg annulée | **2** | Pas de portage de migration annulée |
| **Total audité par SHA** | **155** | 0 commit manquant, **84** décisions runtime encore ouvertes |

## Cinq modifications ciblées déjà préparées (aucune fusion)

- **#9 — F2I** `6e24dcb` : `BitField<45>` = `neg`, `BitField<49>` = `abs`, source `headless/r23_f2i_conversion_ps5.cpp`, propriétaire `shader_recompiler` avec remplacement CMake fail-closed. Test hôte à lier au SHA exact.
- **#22 — BCAT** `07677aa` : `VerifyNameValidFile(file_name_raw)` au lieu de `VerifyNameValidDir`, source `headless/r23_bcat_delivery_cache_file_ps5.cpp`, propriétaire `core`. Test des vrais validateurs de noms sous ASan/UBSan.
- **#44 — viewport** `035f461` : correction du flip Y pour `scale_y` négatif dans le rasterizer Vulkan généré depuis le code amont épinglé (`tools/prepare-vulkan-port.py`). Test mathématique extrait, pas de rendu Vulkan/PS5 validé.
- **#102 — `audren:d`** `a25e326` : utilisation de `IAudioRendererManagerForDebugger` dans `headless/r23_audren_debug_ps5.cpp`, propriétaire cible `core`, test d'enregistrement du service extrait sous ASan/UBSan.
- **#104 — IPS** `3266c20` : magic depuis le fichier patch, fin `EOF`/`EEOF` exacte et garde entrée vide dans `headless/r23_ips_layer_ps5.cpp`, propriétaire `core`, tests de fragments réels sous ASan/UBSan.

## Exclusions de backend x64 prouvables à partir des chemins

- **#12** [`63a94c0ca`](https://github.com/eden-emulator/mirror/commit/63a94c0caae0bd4f1d74f1098f3f1bd8e8a7f465) — Arm NCE interpreter only; non-x64 host backend; `src/core/arm/nce/interpreter_visitor.cpp`.
- **#56** [`5239cbe2a`](https://github.com/eden-emulator/mirror/commit/5239cbe2a78d6533e3541a71c4d3c723818dcb6e) — Arm NCE backend only; PS5 uses x86-64 Dynarmic; `src/core/arm/nce/arm_nce.cpp`.
- **#63** [`305f40100`](https://github.com/eden-emulator/mirror/commit/305f40100d76ec57b13c2f03eafd490db83691cb) — Android Gradle and Arm NCE definitions only; `src/android/app/build.gradle.kts`, `src/core/arm/nce/arm_nce_asm_definitions.h`.
- **#108** [`908b1e9a3`](https://github.com/eden-emulator/mirror/commit/908b1e9a3701f142de51e133d910aa058d4b071c) — Dynarmic backend/arm64 source only, not PS5 x64 JIT; `src/dynarmic/src/dynarmic/backend/arm64/a32_address_space.cpp`, `src/dynarmic/src/dynarmic/backend/arm64/a64_address_space.cpp`, `src/dynarmic/src/dynarmic/backend/arm64/address_space.cpp`, `src/dynarmic/src/dynarmic/backend/arm64/address_space.h`.
- **#40** : commit limité à `src/dynarmic/tests/A64/a64.cpp` ; conserve une valeur comme jeu de tests, ne change pas le code JIT distribué.

## Trois exclusions Qt supplémentaires prouvées par la compilation historique

Les commits **#25** (`9c3bdef`, X11/Wayland), **#133** (`c540525`, interfaces de shaders FX PC) et **#135** (`505b157`, traduction Qt) modifient exclusivement `src/qt_common/` et `src/yuzu/`. Ils avaient été rangés parmi les 123 candidats par un classificateur de chemins trop large. Le [contrôle exact des 155 commits sur la base de compilation native historique #42932868839](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42932868839) ne retrouve **aucune unité de compilation de ces trois commits** parmi les 1 985 entrées, ce qui est cohérent avec le launcher PS5 headless indépendant du frontend Qt.

**Décision : 3 changements de code exclus du portage du runtime PS5**, sans déclarer que leurs idées d'interface ou leurs licences sont auditées. Le compteur `runtime-semantic-review-pending` passe de **113 à 110**, le compteur `not-applicable-to-native-runtime-source` de **20 à 23**. Aucun portage de source ni merge.

## Trois décisions sémantiques supplémentaires : Joycon revert et SDL3 exclu

**#70** (`14da4482a4668928bad43bb67ef12f96b9c9d972`) a introduit un compteur SDL de changement des périphériques dans `Joycons::ScanThread()`. **#65** (`de7e6e01d43e8cf2ec193d74fa053b0d7949955f`) l'a supprimé après régression de gestion des contrôleurs Windows. Le corps entier de `ScanThread()` avant #70 (parent `fb51a1253447a2655382d3cf952c4c470a1d96c6`) et après #65 a été comparé **octet pour octet : strictement identique**. Les fichiers entiers diffèrent cependant par le millésime de la notice de copyright (2025→2026). Les deux commits sont donc **clos pour l'absence de différence comportementale finale de cette méthode**, sans inférer une identité des fichiers ni une compatibilité SDL/PS5.

**#150** (`301da63a15de8cfbe752ac44784db9b58cdd2d87`) ne modifie que `src/audio_core/sink/sdl3_sink.cpp` : le PS5 `headless/CMakeLists.txt` exclut explicitement cette unité du target `audio_core` et utilise le sink PS5 natif. La base CMake historique n'a pas cette unité. **Exclu du portage runtime PS5**, sans nier les changements SDL3 de la version amont.

Ces décisions ne dispensent pas d'auditer les composants Qt/Android et SDL3 si de nouvelles cibles les utilisent. Il reste **105** commits en attente d'un avis sémantique, **5** corrections source hôte préparées, **8** assets et **4** changements de dépendances/build à qualifier.

## Point de vigilance : introduction puis retour arrière HLE

Les commits **#74 (`218c6705d`)** et **#69 (`e255c20db`)** concernent une introduction de tables de dispatch HLE puis son revert. La comparaison par arbres Git entre le parent de #74 et le commit de revert #69 montre que le fichier `src/core/CMakeLists.txt` est revenu au même blob, **mais que le sous-arbre `src/core/hle/service` diffère encore**. Il serait donc faux de supprimer ces deux entrées sans contrôle sémantique par unité sélectionnée. Les 392 et 588 chemins archivés restent tracés et non importés en masse.

## Vérification sémantique supplémentaire — #53 NCA

**#53** [`b7c1ded1593c3c2dc58625824a04e30a63fe80c7`](https://github.com/eden-emulator/mirror/commit/b7c1ded1593c3c2dc58625824a04e30a63fe80c7) modifie une seule ligne de `src/core/file_sys/content_archive.cpp`: ajoute `LOG_ERROR(Loader, ...)` dans le cas où la clé NCA manque, **avant** l'affectation inchangée `status = Loader::ResultStatus::ErrorMissingKeyAreaKey;` suivie du même `return`. Le fichier Eden original épinglé, blob Git `b47b9437d0dfbc3f3adf40a45873d774f36b57f0`, a été comparé à ce diff exact. **Décision : diagnostic utile mais aucun changement d'algorithme de déchiffrement ni du statut rendu.** Aucun patch fonctionnel PS5 nécessaire ; l'amélioration des journaux reste facultative. Aucune exécution console affirmée.

Deux contre-exemples de triage hâtif restent ouverts :
- **#30** [`2c40328`](https://github.com/eden-emulator/mirror/commit/2c40328a23630353f4dd20778eb587e586cd83a5) paraît consacré à macOS, mais son diff comporte aussi un chemin `__FreeBSD__` et une condition de version FreeBSD `< 15`. Sans preuve d'ABI de la libc PS5, ne pas l'exclure.
- **#93** [`37fe911`](https://github.com/eden-emulator/mirror/commit/37fe9119526c03ca064166130cc983c55b9a9e86) corrige le gestionnaire Win32 **mais aussi** `sparse_large_vector.h` avec `CommitPage` booléen et contrôle `mprotect` non-Windows. Il est pertinent pour la mémoire PS5 ; ne pas l'exclure sur le titre.

**Catégories restantes :** 105 changements runtime à décider par propriétaire/équivalence, cinq changements testés/préparés (dont viewport uniquement proposé), 12 modifications assets/dépendances à qualifier, 17 en-têtes de la divergence Eden sans reçu d'inclusion, sept lots correctifs sans preuve console complète.

## Décision supplémentaire — #5 updater Nightly uniquement

Le commit **#5** [`ae60f8e7f85915a2b79d98b49e3134bbdbeca471`](https://github.com/eden-emulator/mirror/commit/ae60f8e7f85915a2b79d98b49e3134bbdbeca471) change exactement `boost::algorithm::split(result, tag, ...)` en `boost::algorithm::split(result, r.tag_name, ...)` dans `src/common/net/net.cpp`, à l'intérieur de **`#ifdef NIGHTLY_BUILD`** du parseur des assets d'auto-mise-à-jour. Le fichier source épinglé, blob `5c45e1370184f72dc68dd5b6400177d48aef778d`, confirme cette condition. Il ne change aucune instruction de déchiffrement, CPU/GPU, HLE ou lancement de jeux Switch. **Exclu du portage du runtime PS5**, sans affirmer qu'une future distribution compilée en mode `NIGHTLY_BUILD` puisse l'ignorer : ce scénario devra avoir son propre test d'updater.

**Deux vérifications conservatrices maintenues ouvertes** : **#123** (*Windows path roots*) réécrit aussi l'algorithme commun de `SanitizePath`, donc pas exclusivement Windows ; **#141** (*MSVC handler tables*) retire `constexpr` d'un constructeur de service commun, donc peut modifier l'initialisation sur d'autres compilateurs. Un titre ne suffit pas pour les exclure.

## Ce qui manque encore

Les **105** entrées `runtime-semantic-review-pending` demandent une décision **unité compilée réellement sélectionnée + équivalence/régression**. Les **5** fixs hôte doivent recevoir un vrai CMake/compilateur natif puis une validation console. Les **12** assets et dépendances sont ouverts, tout comme les **17** en-têtes issus des 35 écarts Eden sans reçu d'inclusion native. Les **7** lots C00–C06 ne sont pas qualifiés de bout en bout.

**Tests des cinq correctifs :** [CI hôte R23 #42929157123](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42929157123) — compilation de fonctions/structures extraites, pas des cinq unités natives PS5 complètes, ni de rendu ou service invité réel.

**Preuves :** [liste exacte des 155 commits](r23/R23_EDEN_COMPLETE_155_COMMIT_PATH_REGISTER.json), [32 dispositions frontend/build/asset](r23/R23_EDEN_NON_RUNTIME_32_DECISIONS.json), [registre machine-readable de 155 catégories](r23/R23_EDEN_155_APPLICABILITY_2026-11-11.json). Aucune modification à `main` ou au submodule `vendor` depuis cette PR.

## Passe sémantique 4 — 4 décisions supplémentaires, sans portage aveugle

**Sources à l'appui :** [#138 SSL](https://github.com/eden-emulator/mirror/commit/ee73920d288586103491d3e2af003b5c40bf4a1c), [#142 revert Opus](https://github.com/eden-emulator/mirror/commit/2b4184dd2bb33da081702263d59c3eadb299e673), [#148 introduction Opus](https://github.com/eden-emulator/mirror/commit/ff8368c6066faf3962e2f77af7da4954e2ff6a43), [#146 GPU null pointer](https://github.com/eden-emulator/mirror/commit/9b649444803bc95423035eba335a1e11c1871793).

- **#142 + #148 : retour arrière prouvé du remplacement libopus → FFmpeg.** Comparaison exacte du parent de #148 `8a22f1845b8b7ec19fbb518b696513e36d42b317` avec #142 : les fichiers `CMakeLists.txt`, `cpmfile.json` et `src/audio_core/adsp/apps/opus/opus_decoder.cpp` sont des blobs Git strictement identiques. Quatre autres fichiers `src/audio_core/adsp/apps/opus/` diffèrent **uniquement** par la notice préfixée Eden GPL-3.0 (suppression exacte des trois lignes de préfixe, comparaison octet-à-octet positive). Des modifications de sink indépendantes dans les 7 commits intermédiaires sont **hors** du couple d'annulation et restent auditées séparément. **Décision comportementale : aucun portage de la migration Opus/FFmpeg annulée**, sans ignorer ses obligations de licence.
- **#138 : SSL.** L'ancien `src/core/CMakeLists.txt` épinglé (`508ace350173f5068bd7531f37e70199134fde3a`) sélectionne sans condition `ssl_backend_openssl.cpp` et lie `OpenSSL::SSL` / `OpenSSL::Crypto`. La nouveauté amont sélectionne le **même backend** lorsque la cible OpenSSL existe, et offre seulement un fallback sans OpenSSL. **Décision : équivalent pour la configuration native figée exigeant OpenSSL**. La gestion d'un build futur sans OpenSSL reste une question de dépendance, pas un correctif de runtime Switch à importer.
- **#146 : GPU Maxwell.** L'amont corrige dans `video_core/control/channel_state_cache.h` un pointeur non initialisé `P* channel_state;` en `P* channel_state = nullptr;`. Le fichier Eden épinglé (`6d70e9be559cc74d88e1204cea909168b4b2d686`) a **encore l'ancienne déclaration**. **Décision : changement pertinent manquant dans la source**, à préparer pour un propriétaire maintenu ; il faut établir l'en-tête vraiment inclus et tester l'initialisation native avant toute affirmation de correction PS5.

**Nouveau compteur R23 : 101 commits runtime encore sans disposition sémantique, 5 correctifs hôte préparés, 1 nouveau candidat GPU #146 à intégrer/vérifier, 12 assets/build à qualifier.** Les 17 en-têtes divergents sans reçu natif, 7 lots correctifs de bout en bout et preuves console restent ouverts. Cette passe clôt **4 avis sémantiques E1**, pas 4 tests PS5.

## Passe sémantique 5 — quatre décisions de périmètre

- **#78 Vulkan Android uniquement** ([source](https://github.com/eden-emulator/mirror/commit/fecc1b4ee32bc06f736f2d138680ec948cf13ab1)). Le diff retire la fausse identité `PUBGMobile`/`UnrealEngine` sous `#ifdef __ANDROID__`, et conserve pour le chemin non-Android exactement les identifiants de `VkApplicationInfo` déjà présents dans la source épinglée (blob `5044881598bc775187b9a957bce563ec31c8f23b`). Aucun portage de cette branche Android pour PS5.
- **#39 OpenSSL wasm + Dynarmic RISC-V** ([source](https://github.com/eden-emulator/mirror/commit/802531c4578e88947a1bcfabfe7a5646d8ed2ce3)). L'ensemble des 5 chemins modifiés couvre l'outillage Emscripten/wasm, un émetteur RISC-V64 et de la documentation de compilation croisée. Pas d'effet direct sur le backend JIT x64 PS5 ; exclusion du portage runtime, sans dispense d'audit de la toolchain OpenSSL.
- **#127 include async_result** ([source](https://github.com/eden-emulator/mirror/commit/fd34024f0e1ffca0aa813698d2552a1dea2b5b17)). Le chemin `src/core/hle/service/ns/async_result.cpp` et ses deux noms d'en-têtes n'existent pas dans les 40 entrées du dossier NS épinglé ; aucun remplacement de ce TU n'est demandé dans notre CMake. Ce renommage ne se transplante pas sans la nouvelle structure HLE en amont.
- **#13 glslangValidator** ([source](https://github.com/eden-emulator/mirror/commit/895d8ede2c69f5f8061b04afaf247c2c5e04c08d)). Les deux changements concernent uniquement le quoting de l'argument `-I` dans les commandes CMake des shaders hôte. **Transféré dans la file de vérification de build** (pas déclaré non pertinent), où il faut comparer le vrai argument et le SPIR-V produit sur la toolchain PS5.

**Compteur : 97 commits runtime encore en examen sémantique, 5 correctifs hôte préparés, 5 dépendances/build dont #13, 8 assets, 1 garde GPU #146 manquante à qualifier.** Les 17 en-têtes et les 7 lots de validation console sont des compteurs séparés. Aucune modification de la branche principale ou du vendor.

## Qualification CI des décisions R23 — 11 novembre, révision synchronisée

Le registre JSON compte désormais **155/155** décisions de triage et **97** changements runtime dont l'analyse sémantique reste ouverte, plus **5** corrections préparées dont l'intégration PS5 reste non prouvée. Les **13** cas de packaging / build / dépendances comprennent 8 assets et 5 dépendances. Les comparaisons #138 (SSL source déjà équivalente), #142/#148 (migration Opus/FFmpeg suivie de son revert) et #146 (initialisation GPU nulle absente, correctif candidat) ont des classes explicites et des preuves conservées dans le JSON. Elles ne valent pas homologation console. L'ancienne assertion CI à 105/12 a été remplacée par les comptes exacts, sans effacer les garde-fous sur #30, #53, #93, #123, #141 ou les ports C++ encore ouverts.

## Exclusion prouvée des huit lots de ressources Qt/Android (PS5 native)

Les huit commits amont **#4, #26, #34, #76, #83, #89, #105 et #140** ne touchent que `dist/`, les ressources Android `src/android/app/src/main/res/`, de la documentation ou `tools/optimize-assets.sh`. La recette réelle de packaging Encore `tools/package-headless-native.sh` copie **`headless/prosperoeden/ui`**, ses propres catalogues `ui/lang/*.po` et les ressources `assets/` ; elle n'importe ni `dist/languages`, ni `dist/icons`, ni les ressources Android, ni le script d'optimisation des visuels upstream. **Décision de portage : 8/8 exclus pour la construction et la distribution PS5 native actuelle**, sans supprimer les fichiers originaux ni prétendre auditer l'application Android/Qt. Une évolution du packaging imposera de réouvrir ce verdict et est vérifiée par l'outil de qualification R23.

**Nouveaux compteurs : 155/155 décisions explicites, 97 sémantiques runtime encore ouvertes, 5 correctifs hôte préparés, 5 cas de build/dépendances encore ouverts et 8 ressources amont hors packaging PS5.** L'absence de nouvelles ressources Qt ne prouve ni un ELF ni la couverture de traduction de l'interface Encore.

## Passe sémantique 6 — trois anomalies source réelles en attente de validation PS5

- **#114 — conversion RDTSC** : l'amont sépare le facteur entier et la fraction de fréquence. Le propriétaire maintenu **effectivement choisi par CMake** `vendor/encore-active/eden-core/src/common/cpu_features.cpp` (blob `f00fba4d5`) et son en-tête maintenu `include/common/cpu_features.h` (blob `4c3c975e`) n'ont ni `rdtsc_ns_integer` ni la nouvelle conversion. **Absence source confirmée.** La politique N76/G11 de cadence 19,2 MHz/31,25 MHz est un contrat distinct : l'amont doit être adapté, pas recopié. Nécessite tests de fréquence 2–4 GHz, guest clock et ABI native.
- **#128 — HLE NS icônes** : le fichier épinglé `read_only_application_control_data_interface.cpp` (blob `c7606a83`) accède à `control.second->GetSize()` dans `ListApplicationIcon` sans garde de nullité. L'amont protège la récupération de métadonnées et contrôle les bornes de sortie. **Absence source confirmée** ; avant un correctif, prouver l'unique unité `core` réellement choisie et tester icônes manquantes et taille malformée.
- **#153 — quotas décodeurs Opus** : le fichier épinglé `audio_core/opus/hardware_opus.h` (blob `caa74684`) ne contient pas le registre des 24 décodeurs et les erreurs `ResultOutOfOpusDecoders` introduits en amont. **Absence source confirmée** ; portage HLE audio avec tests positif/négatif (25e refus, rollback init) et licence/ABI avant toute fusion.

Ces trois écarts sont **des décisions source E1**, pas des crashs PS5 prouvés ni des correctifs actifs. Ils sont déplacés de la file d'analyse sémantique vers une file **correctif identifié — intégration/test à effectuer**. Le total passe à **94 commits runtime sans décision, 4 écarts source identifiés (dont #146 GPU), 5 correctifs déjà préparés**, 13 cas assets/build, 17 en-têtes non attestés et 7 lots sans clôture native/console.

## Deux revues de code fermées sur la cible PS5 native

- **#24, version minimum Qt :** le `find_package(Qt6 6.5)` modifié est sous `if(ENABLE_QT)`. Les autres modifications touchent `src/qt_common/`, `src/yuzu/` et la documentation Qt. `tools/build-headless-native.sh` configure explicitement `-DENABLE_QT=OFF -DYUZU_CMD=OFF`, et la distribution PS5 fournit sa propre interface. **Pas de portage de code nécessaire pour PS5 native** (le frontend Qt reste une cible distincte).
- **#110, `NativeErrorToString` :** le code Eden original épinglé `vendor/sources/eden/src/common/error.cpp` (blob Git `070c9a5c7eb6a444c08e4e23c20f55351ae8f3ee`) traite déjà la libc FreeBSD avec `int second_err = strerror_r(...)` ; l'amont applique un template `HandleStrerrorR(int,char*)` qui renvoie le même texte sur succès et le même fallback sur échec. **Équivalent fonctionnel au niveau source pour la branche FreeBSD/XSI**, pas d'altération de guest IPC/JIT/GPU. Une vérification ABI sera requise si la libc de l'outil PS5 change.

**Comptage actualisé : 95 revues sémantiques runtime ouvertes, 5 vérifications build/dépendances, 5 correctifs hôte préparés, 17 en-têtes à attester, 7 lots C00–C06 sans preuve console complète.**

## Mise à jour des trois divergences source vérifiées (pas des correctifs fusionnés)

Les audits de code ont qualifié **#114** (conversion RDTSC vers nanosecondes au-delà de 1 GHz), **#128** (`ListApplicationIcon` avec pointeur de métadonnées nul) et **#153** (plafond des décodeurs Opus et rollback des échecs). Ils passent de « à analyser » à **« écart source vérifié, test natif requis »**. Il faut encore préparer/tester les correctifs spécifiques, sans prétendre que le simple changement de catégorie a corrigé ces risques.

**Compte R23 courant : 92 changements runtime dont la sémantique reste à trancher, 3 écarts source positivement identifiés à corriger/valider, 5 correctifs hôte préparés, 5 changements build/dépendances encore ouverts et 8 lots de ressources PS5 hors packaging.** La clôture globale NS1 nécessite toujours 17 preuves d'inclusion des en-têtes et 7 lots correctifs validés sur PS5.

## Passe sémantique 7 — compilation GLSL optionnelle

**#101** ([commit source](https://github.com/eden-emulator/mirror/commit/3d37a816c6adc2708a7be70f5a7fbe0af36b8227)) concerne exclusivement `src/shader_recompiler/backend/glsl/emit_glsl.cpp` ; le CMake `shader_recompiler` épinglé n'ajoute cette unité que dans `if(ENABLE_OPENGL)`. Le build hôte headless a `ENABLE_OPENGL=OFF`, mais `tools/build-headless-native.sh` permet explicitement un profil PS5 OpenGL. Il ne s'agit **pas** d'un correctif du compilateur Vulkan/SPIR-V : revue runtime Vulkan fermée, **compilation Clang 23 et compatibilité de l'émetteur GLSL du profil OpenGL encore ouvertes** dans la file build. Aucun import de code ni attestation console. **Compteurs : 91 cas runtime sémantiques, 6 build/dépendances, 8 ressources hors package PS5, 4 écarts source vérifiés et 5 correctifs hôte préparés.**

## Passe de clôture sémantique — cinq décisions vérifiées sans build PS5

| Commit | Constat source épinglé | Décision à ce stade |
|---|---|---|
| **#42** | Le worker natif réellement sélectionné `encore-active/eden-gpu/gpu_thread_quiet.cpp` (blob `28eab249...`) appelle encore `SetCurrentThreadToPerformanceCores()`; amont `943f1fc` supprime cet appel après une régression BOTW | **Différence vérifiée**, pas une régression PS5 prouvée ; mesurer l'ordonnanceur PS5 avant changement |
| **#49** | Le header maintenu Vulkan `eden-vulkan/include/video_core/renderer_vulkan/vk_buffer_cache.h` (blob `64fc796c...`) appelle encore `TexelBufferFormat` sans branche `UsesDescriptorBuffer()`; l'amont corrige le cas format inconnu 255 | **Écart E1 identifié**, recibo d'inclusion du header et tests Vulkan/PS5 requis |
| **#107** | Le `SaveDataFactory` épinglé (blobs `0ba839ec...`, `15dd4ec...`) a déjà `GetFullPath` directement pour Create/Open/Read/Write et aucun `GetSaveDataPath`, comme après le revert amont | **Équivalent pour les fonctions du factory**, pas de revert à importer. Le commit #113 sur d'autres unités reste ouvert |
| **#126** | Les sources épinglées `common/uuid.cpp` (`51fe0abaa...`) et `application_functions.cpp` (`215d204...`) gardent `span<u8,20>` et le déréférencement non gardé du NACP absent | **Écart E1 pertinent**, corriger la signature UUID et le service AM ensemble, valider l'ABI |
| **#139** | Le fichier épinglé `core/hle/service/nfp/nfp.cpp` (blob `b9922ce...`) ne déclare pas les trois commandes 25 `StartDetectionWithFilter`; l'amont les mappe à `StartDetection` | **Écart E1 pertinent**, 3 tables IPC à tester, pas de console confirmée |

Ces décisions sont **source-review completed**, jamais des correctifs homologués. Le compteur devient **86 autres commits runtime à analyser**, **6 écarts source qualifiés avec intégration PS5 restante**, **1 cas d'affinité GPU à mesurer**, **5 correctifs hôte préparés**, **6 cas build/dépendances**, **17 en-têtes sans preuve native** et **7 lots C00–C06 à valider sur console**.
