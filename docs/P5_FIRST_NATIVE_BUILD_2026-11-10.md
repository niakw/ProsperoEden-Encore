# P5 — premier build natif PS5 après sortie P1/P2 (10 novembre 2026)

## Déclenchement explicite et limites

Ce fichier accompagne le **premier build natif de qualification P5**, sans publication automatique de release et sans affirmation de compatibilité console.

- Base fonctionnelle avant le build : `main` moteur `7154be1e727437e264609b805d80a2d1a17d82e2`.
- Sous-module vendor réellement épinglé par ce moteur : `0b0265079139622b759167c9d10a9a31aba1ea88`. Les travaux de documentation/triage ajoutés ensuite sur vendor `main` ne sont **pas** intégrés à ce build.
- Contrats P1/P2 : **17/17 preuves hôtes qualifiées** ; [sortie manuelle #42842249702](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42842249702) **verte** au SHA exact de base ; six autres CI obligatoires vertes au même SHA.
- Le workflow natif [`build-040-zbic.yml`](../.github/workflows/build-040-zbic.yml) est volontairement déclenché par le marqueur de commit `[full-build]`; **aucun** marqueur `[release]` ne demande de publier un binaire.
- Le commit qui contient ce document est nouveau par rapport au SHA des six CI : il n'ajoute que de la documentation de lancement de P5. Le vrai build et sa propre recette peuvent **échouer** et doivent être jugés sur leurs logs et artefacts, jamais sur le seul feu vert P1/P2.

## Critères d'analyse du premier run

1. Contrôles préalables de provenance, cache et configuration native. Si un contrôle échoue, corriger l'owner ou le script à l'origine, **ne pas désactiver le contrôle**.
2. Installation et restauration du toolchain, caches et dépendances épinglés; conserver le cache existant et les stages réutilisables.
3. Compilation/lien PS5, puis validation du package complet (assets, langues, légal, symboles, checksums) sur le **SHA exact** du run.
4. P5 reste **non validé sur console** jusqu'aux essais du framebuffer/IPC/Vulkan : FC27, Zelda BOTW, Mario Kart World et Donkey Kong Bananza. Un binaire compilé seul ne prouve pas l'exécution de ces jeux.
5. Ne pas écraser la dernière release publique ni déplacer le pointeur vendor sans validation distincte.

Le suivi est dans [l'issue #15](https://github.com/niakw/ProsperoEden-Encore/issues/15) et [la roadmap](ROADMAP_NS1_NS2_UNIFIED.md).

## GitHub Actions run créé

[**Run #42846319389**](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42846319389) est la première exécution native de P5, déclenchée automatiquement après le commit volontaire `6fcfe545` ([commit](https://github.com/niakw/ProsperoEden-Encore/commit/6fcfe5454a20f600f092e51bdda331a0796b8220)). Il doit être évalué selon ses propres étapes, artefacts et éventuelles erreurs. Les modifications **documentaires ultérieures** sur `main` n'entrent pas rétroactivement dans ce checkout et ne doivent pas annuler ce run.

## Premier retour P5 et correction isolée

[Premier run #42846319389](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42846319389) : **échec dans les contrôles source, avant tout build natif lourd**. Les logs ont identifié exactement deux assertions héritées du CMake et des scanners ROM plus anciens :

1. `tools/check-jit-stability.py` attendait des options `EDEN_SHARED_JIT` / `EDEN_JIT_COMPILE_BATCH` et des branches de source expérimentales retirées. Le vrai `headless/CMakeLists.txt` sélectionne **sans condition** `a64_emit_x64_standard.cpp` et `a64_interface_standard.cpp`, avec les deux disponibilités JIT à **0**. Le témoin vérifie désormais ces propriétaires et refuse tout rétablissement expérimental.
2. `tools/check-nlib-ui-recovery.py` attendait **deux** garde-fous `game_storage_available()`; le code maintenu en a **trois** : rollback en fin du scan initial, contrôle avant le batch de présence et contrôle après le batch avec `missing.clear()`. Le témoin contrôle maintenant explicitement les trois chemins, au lieu d'en supprimer un.
3. `tools/package-headless-native.sh` vérifiait la présence de `:BOOL=OFF` pour des anciennes options CMake **supprimées**. La validation du package rejette désormais explicitement les valeurs `:BOOL=ON` et `:UNINITIALIZED=ON`, tandis que la configuration CMake et les unités standard sont attestées par le contrôle JIT source.

Ces corrections de **tests devenus périmés**, sans changement moteur ni vendor, sont intégrées dans [`879cbddedcd16453406c5754e3ce338e233a50ea`](https://github.com/niakw/ProsperoEden-Encore/commit/879cbddedcd16453406c5754e3ce338e233a50ea).

[**Second build #42848349739**](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42848349739) lancé volontairement sur ce commit : contrôles toolchain/NCZ/langues/cache/métadonnées passés au début de son exécution ; résultat final natif/packaging **à juger sur le run**. Aucun marqueur de publication, aucun déplacement du gitlink vendor, aucune prétendue validation console.

## Requalification ciblée préalable au troisième build (10 novembre 2026)

Le [second build #42848349739](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42848349739) a encore échoué **avant la compilation PS5**, exclusivement sur deux assertions source obsolètes : le témoin JIT testait une écriture littérale alors que le package refuse correctement les anciens sélecteurs expérimentaux via une boucle, et Nlib testait un ancien cache TGA seulement tandis que le propriétaire réel valide WebP avec repli TGA vérifié. L'archivage historique de l'issue #15 a également eu sa ligne blanche finale corrigée pour la CI source-baseline.

Les deux scripts ont été synchronisés avec leurs sources réelles, en conservant les contrôles de refus et la sélection JIT standard, dans `6f414f4de5d93ad8fd74be98e3ad4234910cb0a1`. Le [workflow ciblé P5 #42850549825](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42850549825) a **réussi** les contrôles JIT et Nlib sur ce SHA, **sans build natif**. Ce feu vert autorise uniquement une nouvelle tentative de compilation PS5, pas une release.

Le troisième lancement est déclenché par le présent commit avec le marqueur explicite `[full-build]`, **sans** `[release]`. L'application reste épinglée sur vendor `0b0265079139622b759167c9d10a9a31aba1ea88` et la publication est désactivée.

## Troisième build : première compilation de dépendances natives observée

Le [run #42850915181](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42850915181), déclenché par le commit moteur `1c9b6bea09638152781ba1843e97ea6950b9cfe1` avec vendor `0b026507`, a **effectivement réussi** les étapes de contrat source/cache, toolchain, NCZ, contrôle de la langue du launcher, restauration de cache, métadonnées/légal, lancement/stockage et préflight packaging. Les anciens blocages JIT/Nlib des tentatives #1/#2 n'ont donc pas réapparu pendant ces étapes.

La tâche `Prepare native build inputs` (`make prepare JOBS=4`) a commencé. Son journal montrait la **compilation effective de Mesa/OpenGL** avec le compteur Ninja `[655/905]` lors de l'observation (messages Clang `-Wunreachable-code-generic-assoc` dans les macros du SDK `math.h`, sans échec démontré à ce stade). Ce compteur porte sur **une dépendance de préparation**, pas sur le nombre total d'unités du binaire Encore.

**Ce constat est un jalon intermédiaire, pas une qualification P5 :** `make prepare`, `Build and stage native release`, la validation du ZIP et les tests PS5 restent à vérifier sur les résultats finaux du run. Ne ni déplacer le gitlink vendor ni relancer un build natif pour de simples modifications documentaires. Aucun `[release]` n'a été demandé.

## Troisième build : échec de configuration et quatrième tentative contrôlée

Le [troisième build #42850915181](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42850915181) a **réussi `make prepare` et l'index de jaquettes**, puis échoué dans `Build and stage native release`, à la configuration CMake — **avant compilation du binaire Encore**, malgré la préparation effective et coûteuse des dépendances Mesa/OpenGL. Deux diagnostics distincts apparaissent dans le même journal :

1. `headless/CMakeLists.txt:1800` : `add_subdirectory(libwebp)` a été invoqué dans le callback `cmake_language(DEFER)`, ce que CMake interdit. Le dossier source upstream demeure épinglé sous `vendor/sources/libwebp`. La création du target WebP a été déplacée dans l'injection `CMAKE_PROJECT_yuzu_INCLUDE` **non différée**, et le callback ne fait plus que vérifier puis lier le target. Correctifs `c943d344` et `1f289cca`.
2. `headless/CMakeLists.txt:2003` : le sélecteur du noyau commun NS1/NS2 attendait le nom relatif `hle/kernel/k_address_arbiter.cpp` (ou une variante absolue écrite depuis `PORT_ROOT`) alors que le module threading vendor avait déjà sélectionné son propriétaire maintenu avec un autre chemin absolu. Le rapprochement utilise désormais `REALPATH` avant de **remplacer l'unique source**, pour les deux TUs d'arbitrage, sans dupliquer les propriétaires ni modifier le vendor.

Le contrôle source hôte et le test local léger de mécanisme CMake vérifient la nouvelle séparation « registration avant DEFER / lien après DEFER » et la normalisation des chemins. Le [préflight ciblé #42856202269](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42856202269) est **vert** sur `824d26e4538bab497ace1183dac14b98b168278a`, y compris les validations JIT, Nlib et le nouveau garde-fou `tools/check-active-cmake-source-boundary.py`. Il **ne remplace pas** un vrai configure natif ni les tests PS5.

Le workflow principal conserve désormais ses caches de dépendances après un `make prepare` réussi même si les étapes natives suivantes échouent (`0e951b37`); pas de reprise d'un binaire non validé. **La quatrième tentative native est déclenchée par ce commit `[full-build]`, sans `[release]`**, moteur sur `main` et sous-module vendor immuable `0b026507`. Aucun ZIP/binaire ou essai console n'est validé d'avance.

## Quatrième build : garde CI cache obsolète, cinquième tentative

Le [run #42856587272](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42856587272), moteur `067842fd`, vendor `0b026507`, a échoué **avant `make prepare`**, dans `Validate startup, elevation and storage contracts`. Toutes les autres vérifications du groupe ont continué et le seul échec rapporté est `tools/check-ci-cache.py:113` : l'assertion cherchait encore le nom d'étape supprimé `Save build caches after verified artifact uploads`. Le workflow utilise désormais `Save caches after successful native preparation` avec le garde conditionnel `!cancelled() && steps.prepare_native.outcome == 'success'` et `continue-on-error: true`. Ce n'est **pas** un échec de CMake ni une régression du moteur.

Le contrôle a été réaligné sur le vrai nom, l'ordre des étapes et la condition stricte d'une préparation réussie dans `a2e7f0f`; les invariants cache ont été revérifiés sur les fichiers de `main` (9 contrôles ciblés réussis). La cinquième tentative est demandée par ce commit `[full-build]`, sans `[release]` ni changement du vendor épinglé. Les deux correctifs de configuration WebP/Wait64 restent à confirmer sur un configure natif réellement exécuté.

## Cinquième build : source CPU6 après G11, conservation des optimisations et préflight natif renforcé

Le [cinquième build #42858138767](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42858138767) a réussi les contrats source/packaging et `make prepare`, puis a échoué à la configuration CMake avec `Pinned CPU6 scheduler/tick owner changed: arm/dynarmic/arm_dynarmic_32.cpp`. Les correctifs WebP/Wait64 des builds précédents ont franchi ce point. Les dépendances préparées ont été sauvegardées dans un cache GitHub de **3,55 Go** (pas de stage binaire prêt à diffuser).

**Diagnostic :** la sélection native G11 retire d'abord l'owner A32 relatif et ajoute `vendor/encore-active/eden-core/src/core/arm/dynarmic/g11/arm_dynarmic_32_native_normal.cpp`. Le bloc CPU6 cherchait ensuite l'ancien chemin relatif. Une simple substitution par l'ancienne source CPU6 aurait également perdu les optimisations JIT G11 côté A32. Pour préserver NS1 et le moteur commun, le mainteneur CPU6 A32 est désormais issu exactement de la variante **G11 native normal**, avec la seule modification vérifiée du diviseur de ticks à partir du masque de cœurs physiques.

- Moteur : sélecteur réel corrigé dans `41763ebb`, refus explicite si G11 A32 manque, sans second propriétaire compilé.
- Vendor : source CPU6 A32 complétée dans `22b69d6` ; nouveau gitlink effectif `22b69d6` via `dac4757` (les cinq premières tentatives restent historiquement liées à `0b026507`).
- Reproduction hôte : `tools/ns2/check_cpu6_scheduler_tick_host.py` teste désormais la sélection réelle de G11 A32 et A64, les quatre combinaisons console/NPDM, la stricte parité avec les sources maintenues et la correction des ticks.
- [Préflight CMake rapide #42863829705](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42863829705) : **SUCCESS** sur l'épingle mise à jour.
- [Préflight complet #42864115771](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42864115771) : **SUCCESS** sur `ab988c31`, avec compilation réelle des unités A32/A64 sur hôte et tests UBSan. Ces preuves sont une protection préalable ; elles ne constituent ni un configure PS5 complet ni une recette console.

**Politique avant la sixième tentative :** examiner les validations hôtes P0–P4 sur le **nouveau** gitlink, et ne déclencher un nouveau `[full-build]` qu'après ces garde-fous. Aucune publication automatique, aucun essai sur console déclaré réussi par anticipation.
