# R23 — 155/155 commits Eden, triage de pertinence NS1 avec restant exact

**État : audit PR #45, en lecture seule.** L'inventaire des 155 diffs par commit est complet; ce registre applique maintenant une catégorie explicite à **chaque** commit et n'importe aucun code. Un commit classé *runtime à examiner* n'est pas déclaré intégré ou absent sans vraie preuve; un fix testé sur hôte n'est pas validé PS5.

| Catégorie | Commits | Action |
|---|---:|---|
| Aucune source d'émulation PS5/NS1 (Android/Qt/docs/SDL non sélectionné) | **24** | Exclusion du portage runtime; packaging/légal hors de cette décision |
| Assets et langues de la distribution | **8** | Vérifier les assets effectivement packagés |
| CMake / CPM / versions dépendances | **4** | Vérifier les pins et la compilation PS5 |
| NCE ARM / Dynarmic ARM64 host uniquement | **4** | Exclusion explicite du PS5 x64 |
| Commit modifiant uniquement un test Dynarmic | **1** | Conserver comme référence de tests, pas de patch runtime |
| Correctif de code NS1/partagé préparé sur PR #46 | **5** | F2I, BCAT, viewport, IPS, `audren:d` : hôte ciblé; compilation native/console en attente |
| Autres changements NS1/partagés | **107** | Révision sémantique à faire, pas seulement les chemins |
| Fonction Joycon modifiée puis intégralement rétablie | **2** | #70 et #65 : méthode `ScanThread()` byte-identique avant/après, aucun portage de l'essai SDL |
| **Total** | **155** | **0 commit manquant à l'inventaire** |

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

Ces décisions ne dispensent pas d'auditer les composants Qt/Android et SDL3 si de nouvelles cibles les utilisent. Il reste **107** commits en attente d'un avis sémantique, **5** corrections source hôte préparées, **8** assets et **4** changements de dépendances/build à qualifier.

## Point de vigilance : introduction puis retour arrière HLE

Les commits **#74 (`218c6705d`)** et **#69 (`e255c20db`)** concernent une introduction de tables de dispatch HLE puis son revert. La comparaison par arbres Git entre le parent de #74 et le commit de revert #69 montre que le fichier `src/core/CMakeLists.txt` est revenu au même blob, **mais que le sous-arbre `src/core/hle/service` diffère encore**. Il serait donc faux de supprimer ces deux entrées sans contrôle sémantique par unité sélectionnée. Les 392 et 588 chemins archivés restent tracés et non importés en masse.

## Ce qui manque encore

Les **107** entrées `runtime-semantic-review-pending` demandent une décision **unité compilée réellement sélectionnée + équivalence/régression**. Les **5** fixs hôte doivent recevoir un vrai CMake/compilateur natif puis une validation console. Les **12** assets et dépendances sont ouverts, tout comme les **17** en-têtes issus des 35 écarts Eden sans reçu d'inclusion native. Les **7** lots C00–C06 ne sont pas qualifiés de bout en bout.

**Tests des cinq correctifs :** [CI hôte R23 #42929157123](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42929157123) — compilation de fonctions/structures extraites, pas des cinq unités natives PS5 complètes, ni de rendu ou service invité réel.

**Preuves :** [liste exacte des 155 commits](r23/R23_EDEN_COMPLETE_155_COMMIT_PATH_REGISTER.json), [32 dispositions frontend/build/asset](r23/R23_EDEN_NON_RUNTIME_32_DECISIONS.json), [registre machine-readable de 155 catégories](r23/R23_EDEN_155_APPLICABILITY_2026-11-11.json). Aucune modification à `main` ou au submodule `vendor` depuis cette PR.
