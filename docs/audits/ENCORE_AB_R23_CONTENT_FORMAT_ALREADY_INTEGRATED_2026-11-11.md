# R23 — les formats ZBIC / NCZBLOCK étaient déjà pris en charge sur PS5

**11 novembre 2026.** Comparaison source de l'amont Eden avec le code réellement sélectionné d'Eden Encore. Aucune modification `main`, `vendor`, aucun build. Une équivalence **de fonctionnalité au niveau source ne constitue pas un test runtime**.

## #92 — ZBIC, compression NSO Switch 22+

- Commit [Eden `815325cce`](https://github.com/eden-emulator/mirror/commit/815325cceca948030cf476dce7c46d901e4e4df5) : nouveaux `zbic_compression.cpp/.h`, ajout de la dépendance ZBIC et de la détection du flag NSO bit 7.
- **Déjà présent dans Encore :** `headless/zbic_compression.cpp` (blob `b980c2b53bf188e6607e1ecb2d5d7fdb45e6a0d4`) et `.h` (blob `b2cbdf73a2d7b4e540d193a8011801e9f7e19ef2`) implémentent `IsZBIC` et `DecompressDataZBIC`, avec `ZSTD_ZBIC_SUPPORT=1`. Le composant vendor `zbic-11b08f27/src` est sélectionné par `headless/CMakeLists.txt` pour la cible `common`.
- **Vrai NSO natif :** `vendor/encore-active/eden-core/src/core/loader/nso.cpp` (blob `e938e0175222a839e649100a14a1554fa9f78022`) examine `(nso_header.flags >> 7) & 1`, appelle `DecompressDataZBIC` pour ces segments et garde LZ4 dans l'autre cas. CMake substitue ce propriétaire intégral à `loader/nso.cpp` pour `PS5_NATIVE` et le copie en `native-local/nso.cpp`.
- **Décision :** besoin fonctionnel source déjà implémenté. Ne pas dupliquer le décodeur ni importer aveuglément tout le commit. Le bon décodage de vrais dumps et l'isolation du retour d'erreur nécessitent toujours des tests hôte/PS5 E3/E4.

## #60 — NCZBLOCK, NSZ et XCZ

- Commit [Eden `58968bd12`](https://github.com/eden-emulator/mirror/commit/58968bd12) : prise en charge des archives compressées par blocs.
- **Déjà présent dans Encore :** `headless/ncz.h` (blob `85ced3460d83be2a8011f189c0df406b4dd32b8c`) reconnaît `NCZBLOCK`, valide exposant, compte et dimensions, entretient les offsets de blocs et fournit lecture aléatoire des blocs. `headless/ncz.cpp` (blob `7deff2ea1a82574b9e756ad9c2f0d869aa94612b`) transforme l'archive en vue NCA VFS ; un flux solide dispose d'un déballage contrôlé.
- `headless/CMakeLists.txt` exige les fichiers NCZ propriétaires maintenus dans `vendor/encore-active/eden-core`, remplace les TU `core` correspondantes par ces fichiers complets, ajoute `headless/ncz.cpp` et réutilise Zstd déjà épinglé.
- **Décision :** fonctionnalité source déjà intégrée. Ne pas ajouter un deuxième chemin NCZ. Les vérifications console sur fichiers malformés, chiffrement, DLC/update, seek aléatoire et gros blocs restent distinctes.

**R23 : 82 → 80 revues runtime encore ouvertes, 2 commits entièrement classés pour la pertinence source.** Aucune affirmation de performance, de stabilité console ou de compile/link final.
