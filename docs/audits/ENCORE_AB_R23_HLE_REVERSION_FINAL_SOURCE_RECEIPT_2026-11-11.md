# R23 — fermeture source-sémantique du couple HLE #74 / #69

**Date : 11 novembre 2026.** Audit PR #45, aucun changement `main`, `vendor` ou compilation native. [Contrôle Git lecture seule #42949170234](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42949170234). Le script versionné est [`verify-r23-hle-restore-license-only.py`](../../tools/audit/verify-r23-hle-restore-license-only.py).

## Ce qui a été comparé effectivement

- **Avant #74 :** parent exact `4dc69c06f764a235bccd01afbfc765d9ddbebc9f` du commit [#74](https://github.com/eden-emulator/mirror/commit/218c6705d950635bc18f8458d738a1996fb592b6) (« handler dispatch maps »).
- **Après #69 :** commit [#69](https://github.com/eden-emulator/mirror/commit/e255c20db4111485d228c10478bda63aabcfdde5) de revert, `e255c20db4111485d228c10478bda63aabcfdde5`.
- **Sous-arbre couvert :** `src/core/hle/service/` **entier**, 741 fichiers dans chacun des deux arbres Git. Même arborescence, **392 SHA de blob différents**.
- **339/392** fichiers portent uniquement l'ajout de **trois lignes de copyright/licence SPDX**.
- **53/392** ne respectent pas cet ajout strict : **46** sont des changements d'année des notices `2025 → 2026`; les **7 autres** concernent des réarrangements de notices, lignes blanches et un alignement dans `nvdrv/devices/nvhost_gpu.cpp`. La première passe a conservé ces 53 comme « résidu à vérifier », sans les appeler régression.
- La passe indépendante `git diff --ignore-all-space --ignore-blank-lines -I '^([[:space:]]*// SPDX-.*|[[:space:]]*)$'` constate **0 différence source non cosmétique** pour tout le sous-arbre HLE.
- Le fichier `src/core/CMakeLists.txt` a **exactement le même SHA Git** avant #74 et après #69.

## Disposition

**Deux commits (#74, #69) classés « source HLE restaurée, pas de portage comportemental ».** Les 392 changements d'octets ne sont donc **pas 392 changements exécutables**. Préserver les notices d'attribution et comparer les licences lors de la redistribution ; la normalisation Git n'est **pas** un moyen de supprimer les obligations de copyright.

Ce résultat ne compare **pas** tout l'émulateur entre ces dates, ne qualifie pas tous les autres commits intercalés (leurs propriétaires restent suivis individuellement), ne prouve pas que la version anciennement épinglée ou le PS5 reprend le même chemin natif et **ne constitue ni compilation E3, ni test console E4**. Il clôt seulement la décision sémantique du grand aller-retour IPC/HLE de l'amont. La revue runtime R23 passe de **86 à 84 commits encore ouverts**.

**Pièces :** [registre exhaustif des 155 commits](r23/R23_EDEN_155_APPLICABILITY_2026-11-11.json), [diff HLE et source-script](../../tools/audit/verify-r23-hle-restore-license-only.py), [CI #42949170234](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42949170234).
