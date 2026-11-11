# R23 — pass 5 : deux exclusions bornées, deux pièges préservés

**Audit seul, 11 novembre 2026.** Base Eden `5f142c79` → `89d1a1cd`. S'appuie sur les **155 listes complètes de fichiers** et l'examen des diffs réels des commits ciblés, non sur leurs titres. Aucune modification de `main`, du sous-module `vendor`, ni de binaire PS5.

## Deux décisions de source E1

| Commit | Preuve et décision | Ce qui reste ouvert |
|---|---|---|
| **#79 — [c74698220](https://github.com/eden-emulator/mirror/commit/c746982201a60958193f0678fff1f39417aaaf1e)** | Quatre chemins : `bcat/backend/backend.h`, `npad_types.h`, `joycon_types.h`, `joycon_protocol/poller.cpp`. Le diff complet change uniquement des `#include` (+`<vector>`, suppressions d'en-têtes inutilisés et une année de copyright) ; **aucun corps de fonction ni déclaration opérationnelle n'a changé**. Aucun portage comportemental NS1 justifié. | Validation de la compilation de l'ensemble des en-têtes et de leurs dépendances transitives dans le compilateur PS5 ; cette décision E1 n'est pas une preuve d'ABI ou de réussite de compilation. |
| **#86 — [963119e7c](https://github.com/eden-emulator/mirror/commit/963119e7cc3851007252c9981e4fae3e88b7687f)** | Unique changement dans `cpmfile.json` : version `ffmpeg-ci` de `crueter-ci/FFmpeg` `9.0.1-1788120736-bf1b838f2a` → `9.0.2-1790726865-946fcce07b`. **N'est pas** une modification du bloc `ffmpeg` natif. L'inventaire `tools/deps.json` sélectionne indépendamment `FFmpeg/FFmpeg@c7b5f1537d` pour le décodeur PS5. Pas de transposition de l'artéfact CI amont au runtime PS5. | Ne pas prétendre que FFmpeg a été mis à jour, qu'une correction de décodage existe ou que le SBOM complet est qualifié. Réouvrir si le résolveur natif adopte `ffmpeg-ci`. |

## Deux changements à ne surtout pas exclure par le titre

- **#144 — [099547b3f](https://github.com/eden-emulator/mirror/commit/099547b3f4578bf1fc0b39988aefbe2d54b540cc)** : intitulé Android LSFG UI, mais les 26 chemins incluent `src/common/settings.h`, `src/video_core/frame_gen/lossless_dll.cpp`, `renderer_vulkan/present/frame_gen.cpp`, `lsfg_shaders.cpp`, `vk_blit_screen.cpp`, `vk_present_manager.{cpp,h}`. Ce commit modifie de **vraies sources partagées Vulkan / frame generation** ; comparaison sémantique avec l'upscaling/FG Encore et tests restent requis. Aucun simple « Android only ».
- **#123 — [c3f1e6562](https://github.com/eden-emulator/mirror/commit/c3f1e6562b6cb5aefcb9edd490b303867917f25e)** : contient bien des branches Windows, mais change également le traitement commun des `..`, racines et séparateurs dans `Common::FS::SanitizePath` **hors `_WIN32`**. Tests réels de chemin Posix/PS5 et traitement des traversées requis ; non exclu.

## Exact nouveau compteur

**155/155 commits identifiés et classés** ; **68 revues sémantiques runtime** non terminées (−1), **5 cas build/dépendances** non qualifiés (−1), **5 correctifs hôte préparés**, **17 reçus d'en-têtes divergents** à obtenir, **7 lots correctifs** non qualifiés sur console. Les **8 changements de traductions/ressources Qt ou Android** ont déjà une preuve distincte d'exclusion du package PS5 et ne sont pas comptés ici comme une nouvelle avancée.

**Cinq cas build encore à traiter sans conclusion abusive** : #13 (`glslangValidator -I`), #20 et #66 (LZ4 statique/bundlé), #101 (GLSL, non sélectionné en profil Vulkan mais parcours OpenGL potentiel), #134 (Boost et CPM, audit R18 de provenance nécessaire). Pour chacun, une modification d'API/ABI ou de l'outil de build peut rendre le correctif pertinent ; ne jamais importer en bloc.

Sources de vérité machine : [registre 155](r23/R23_EDEN_155_APPLICABILITY_2026-11-11.json), [validateur de catégories](../../tools/audit/verify-r23-155-applicability.py), [CI de vérification](../../.github/workflows/audit-r23-all-155-files.yml).
