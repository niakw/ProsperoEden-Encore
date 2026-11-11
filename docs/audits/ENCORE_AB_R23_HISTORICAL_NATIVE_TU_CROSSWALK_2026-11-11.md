# R23 — correspondance des 155 commits Eden avec la compilation PS5 historique

**Preuve :** [audit hôte en lecture seule #42932868839](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42932868839), artefact `ab-ns1-historical-compile-witness/r23-native-TU-owners.json`, base de compilation CMake/Ninja native **historique de 1 985 entrées**. Source inspectée = `audit/ab-ns1-upstream-2026-11-10`, vendor figé. Aucun nouveau build natif.

| Mesure | Résultat | Portée |
|---|---:|---|
| Commits Eden traversés | **155/155** | Liste de fichiers exhaustive à ce pin |
| Occurrences de fichiers C/C++ changés dont un chemin de compilation est retrouvé | **749** | Par commit, pas des fichiers uniques, ni des objets linkés |
| Occurrences de fichiers C/C++ sans suffixe exact de chemin compilé | **311** | Owner possiblement renommé/override, **pas une preuve d'absence** |
| Commits avec au moins une unité de compilation directement reconnue | **73** | Programmé dans le CDB historique, pas testé PS5 |
| Commits modifiant au moins un en-tête sans preuve d'inclusion | **83** | L'absence de `.ninja_deps` empêche toute qualification des en-têtes |
| Traduction du code Qt/desktop non sélectionné | **3 commits exclus** | #25, #133, #135, selon chemins uniquement Qt et historique CDB |

Le recensement de 155 commits identifie **2 376 changements de fichiers**, dont les 749/311 chiffres ci-dessus sont les occurrences de **seules unités de traduction C/C++**. Ils ne se somment pas avec les en-têtes, CMake, dépendances et ressources.

**Règle de qualification :** un chemin retrouvé dans `compile_commands.json` prouve la programmation d'une compilation, **pas** le succès de la compilation, la liaison à l'ELF ni la présence dans le binaire PS5 final. Un chemin absent peut être remplacé par un fichier renommé dans `headless/native-local` et exige une recherche du vrai propriétaire. Le groupe spécifique des **17 en-têtes divergents** n'est toujours pas qualifié sans reçu d'inclusion. La revue sémantique et les tests restent obligatoires pour les **110 candidats runtime** et les **5 correctifs déjà préparés** en PR #46.

Aucun changement sur `main` ni sur le sous-module `vendor`. Un futur build validé doit lier ses propres chemins et SHA aux mêmes dossiers de preuves, sans répéter le balayage complet des 155 commits.
