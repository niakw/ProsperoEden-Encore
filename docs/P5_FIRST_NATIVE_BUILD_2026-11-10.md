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
