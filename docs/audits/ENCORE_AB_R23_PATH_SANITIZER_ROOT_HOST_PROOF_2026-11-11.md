# R23 — pass 6 : SanitizePath, A/B de deux vraies fonctions

**11 novembre 2026, PR #45 d'audit isolée**. Source originale : vendor `22b69d6053db41b74edac2633c012f925b84f69e`, fichier `sources/eden/src/common/fs/path_util.cpp` (blob Git `b4c7eae343df49eaae5327c5efa04a8d13dc4e19`). Amont : [Eden #123 / c3f1e6562](https://github.com/eden-emulator/mirror/commit/c3f1e6562b6cb5aefcb9edd490b303867917f25e), source `src/common/fs/path_util.cpp` (blob `82ea8f6cb2b3d365b0e3a96457694a81bb0bec7f`).

## Test positif et négatif E1

La [CI hôte #42995344113](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42995344113) est **verte** : elle compile sous Clang C++20 ASan/UBSan les **corps exacts** `Common::FS::SanitizePath` de l'original épinglé et de l'amont, avec les fonctions auxiliaires source d'origine, sans générer de source de production. [Corpus exact](../../tests/audit_r23_path_sanitizer_host.cpp).

| Entrée sur hôte POSIX | Eden épinglé | Eden amont | Différence |
|---|---|---|---|
| `/` | chaîne vide | `/` | Oui : racine perdue |
| `/a/..` | chaîne vide | `/` | Oui : retour à la racine |
| `/../etc` | `/etc` | `/etc` | Non : `..` hors racine déjà supprimé |
| `/a/../../etc` | `/etc` | `/etc` | Non |
| `../a` | `a` | `a` | Non |
| `a/../../etc` | `etc` | `etc` | Non |
| `a/../b` | `b` | `b` | Non |
| `a//b` | `a/b` | `a/b` | Non |
| Vide | Vide | Vide | Non |

La première version du corpus a échoué parce qu'elle supposait à tort que l'original conservait les `..` initiaux. Les **corps de code exécutés ont invalidé cette hypothèse**. Le corpus corrigé est vert. **Aucune vulnérabilité de traversée de répertoire n'a été prouvée** ; le différentiel établi est la représentation de la racine en sortie.

## Ce que cette preuve ne clôt pas

La fonction `src/common/fs/path_util.cpp` est une **candidate partagée**. Ni la correspondance de son objet final dans `eboot.bin` ni sa sémantique sous les appels PS5 (chargement ROM, montages, chemins relatifs, sauvegardes) n'ont été attestées. Aucune migration du nouvel algorithme (y compris UNC/drive Windows) n'est autorisée aveuglément. Pour clore ce cas : analyse des usages sur PS5, preuve de source effective, tests natives E3 sur chemins relatifs/racines et tests console E4 ciblés avant tout portage.

**Décision R23 : #123 sort de la catégorie « sémantique non examinée », mais reste un écart E1 ouvert pour décision et preuve PS5.** La liste des 155 changements reste intégrale ; aucun déplacement ou correction de source de production.

## Compteurs de ce sous-lot

- **155/155** commits Eden classés au niveau provenance.
- **67** sémantiques runtime encore à examiner (−1 par preuve source testée).
- **1** nouvelle catégorie « différence racine du SanitizePath prouvée hôte ; décision PS5 restante ».
- **5** cas build/dépendances, **5** corrections hôte préparées, **17** en-têtes divergents sans provenance native, **7** lots à valider sur console.
