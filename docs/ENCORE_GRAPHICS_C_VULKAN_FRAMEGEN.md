# C / R08 — Vulkan frame generation (état vérifiable)

Branche : `feat/encore-c-vulkan-framegen`. Ne pas fusionner `main` ni modifier le vendor pour de simples contrats.

## Priorités et choix d'intégration

| Ordre | Méthode | Source / licence | État concret | Prochaine preuve |
|---|---|---|---|---|
| 1 | MihawkGen natif PS5 | `mihawk-99/PS5_MihawkGen` @ `c57232a`, module `framegen/` GPL-3.0-or-later, outillage PS5 MIT ; modèle `network.fgw` à auditer avec notices | Source épinglée en sous-module, **aucun code de génération branché dans le renderer Encore** | Construire module et modèle sur la toolchain PS5, vérifier Vulkan/RADV, layouts/barrières/fences et premier couple d'images |
| 2 | FSR 3.1 Frame Generation | AMD FidelityFX SDK, code MIT ; nécessite flux temporal/motion/depth et swapchain Vulkan qualifiés | Contrat R06 seulement | Prouver depth/motion/jitter invités, HUD distinct, profil de latence ; comparer aux mêmes images |
| 3 | LSFG / Lossless Scaling | Intégration amont ProsperoEden pouvant dépendre d'une DLL Windows non redistribuable | Non intégré à Encore ; aucune DLL embarquée | Confirmer droits de distribution et backend **natif PS5** ; sinon refuser cette option |

Le sous-module MihawkGen, pas les fichiers de son `external/` en bloc, constitue la provenance. Avant diffusion de tout modèle, confirmer séparément code, poids et notices. Selon le README MihawkGen, le réseau fourni a été entraîné sur des clips privés, avec certaines cibles distillées de modèles publics sous licences permissives : l’attribution et les conditions des poids sont à vérifier avant packaging. La présence du fichier dans le sous-module ne constitue pas une autorisation de redistribution dans les Releases Encore.

## Premier garde-fou exécuté

`extras/graphics/framegen_present_gate.h` et son test sont **hôte uniquement**, sans branchement d'un backend. Il ne produit pas de fausses frames ; il n'autorise qu'une demande de frame synthétique si :

- le moteur Vulkan, les fonctions requises et les poids/conditions du fournisseur sont prouvés ;
- le taux de la sortie a été **négocié**, le jeu est à au moins 30 FPS réels et la sortie a de la marge ;
- les deux frames sources sont consécutives, les timestamps monotones et la cadence stable ;
- pas de pause/menu, changement de résolution/TV, changement d'overlay ni interruption ;
- un seul intermédiaire maximum, pas de prétendu 30→120 en première itération.

Les FPS réels du jeu restent distincts de la fréquence affichée. Les appels aux commandes Vulkan et la gestion de lifetime des images/fences **restent à intégrer**. Les états de l'application ne doivent pas laisser croire que MihawkGen/FSR3/LSFG fonctionne avant le branchement effectif.

Test hôte : `SDKROOT=/Library/Developer/CommandLineTools/SDKs/MacOSX15.4.sdk clang++ -std=c++20 -Wall -Wextra -Werror -fsanitize=undefined extras/graphics/test_framegen_present_gate.cpp -o /tmp/test_framegen_present_gate && /tmp/test_framegen_present_gate`.

## Jalons à clôturer

1. **C1, présent :** sources/version/licence sélectionnées et garde de cadence prouvé sur hôte ; aucun test PS5.
2. **C2, ouvert :** les 4 unités C++ Mihawk passent la syntaxe hôte et les 21 shaders SPIR-V passent `spirv-val --target-env vulkan1.3`; le modèle `network.fgw` (1 757 240 octets) est épinglé à SHA-256 `31ecc7d69af1e9defd62b9abad71bc3430cd8a0a4d2f4eafcabaafa48c34bf6b`. La cible CMake `EDEN_BUILD_MIHAWKGEN_CORE=ON` prépare une compilation des sources natives **isolée**, sans les ajouter au renderer. Compilation/toolchain GPU PS5 et chargement autorisé du modèle restent à prouver. Ne pas activer le mode dans l'UI tant qu'inexécutable.
3. **C3, ouvert :** enchaînement réel frames précédent/courant/synthétique avec mémoire, ownership, layouts, barrières, fences et timing PS5 ; repli sans régression NS1/NS2.
4. **C4, partiel :** la catégorie **Paramètres > Vidéo** affiche « Génération d'images : Désactivé » avec explication MihawkGen / FSR3 / LSFG. Cette ligne refuse toute activation tant que le runtime PS5 n'est pas validé. Les 29 catalogues ont été mis à jour, y compris le fallback français embarqué ; contrôles de couverture : 477/477 clés. Les sélecteurs opérationnels, la sérialisation et les profils par jeu restent ouverts.
5. **C5, ouvert :** A/B visuel et latence PS5 ; comparer FSR 3 sur même scène, accepter/refuser LSFG selon la faisabilité native et la licence.

## Point de sécurité découvert dans le port amont ProsperoEden

Le wrapper d'exemple `mihawkgen.cpp` de ProsperoEden applique `VK_IMAGE_LAYOUT_UNDEFINED` aux images couleur source. Cela peut invalider leur contenu ; l'exemple n'établit pas, à lui seul, l'ownership de plusieurs frames en vol ni les fences nécessaires. **Ne pas copier le bloc tel quel en production.** Avant d'activer l'option, relever les layouts réels, attendre les fences des buffers relus et ajouter une passe de présentation des images générées sans écraser les images encore lues par Vulkan.

## C2 — source native Vulkan et sécurité des images (vendor c62ecbb)

L'analyse du renderer réellement copié par headless/vulkan.cmake et
du PresentManager a établi le chemin suivant :

1. BlitScreen::DrawToFrame compose la frame source; le renderpass termine
   en layout GENERAL. PresentManager::CopyToSwapchainImpl suppose GENERAL,
   utilise un transfert puis restaure GENERAL.
2. Les Frame* acquis par GetRenderFrame retournent dans free_queue
   après présentation : **il est dangereux de conserver Frame* comme
   historique d'une interpolation**. Deux images privées stables sont nécessaires
   pour les entrées précédentes/courantes.
3. Le chemin de génération historique du renderer est derrière
   HAS_LSFG. Sa présence n'atteste **pas** d'un backend MihawkGen PS5.
4. Sans HAS_LSFG, CanStoreToFrame refuse le stockage direct dans les
   images de présentation. Le modèle Mihawk exige un output **RGBA8 storage**;
   sur swapchain BGRA8, une image RGBA8 distincte et un vkCmdBlitImage
   avec formats/usage vérifiés sont requis.
5. Le composite actuel passe draw_hud=true. Le **HUD n'est pas isolé**
   du chemin de présentation ; un effet temporel actif pourrait produire
   du ghosting sur le score/menu.

### Code ajouté dans le lot de sécurité

- mihawk_native_surface_contract.h refuse les chemins sans propriétaire
  des images d'historique, slots/fences, format, conversion, HUD isolé et
  synchronisation du presenter prouvés. Le mode non qualifié reste OFF.
- mihawk_vulkan_history_barriers.h définit les transitions exactes
  GENERAL → TRANSFER_SRC → GENERAL de la vraie frame, les transitions
  des snapshots privés et celles de l'output RGBA8.
- mihawk_vulkan_stage.cpp **enregistre réellement** les commandes Vulkan
  vkCmdPipelineBarrier, vkCmdCopyImage, fg_record_generate et vkCmdBlitImage
  vers une image synthétique **uniquement si un appelant fournit toutes
  les ressources et préconditions**.
- headless/vulkan.cmake ajoute cette unité à la cible de validation
  EDEN_BUILD_MIHAWKGEN_CORE=ON, encore **OFF par défaut** et non liée au
  binaire de production.
- tools/graphics/check-r08-host.sh exécute quatre tests de règles,
  barrières et séquence de commandes. Le dernier module utilise des
  mocks de commandes Vulkan : preuve de l'ordre, des paramètres et du refus
  avant enregistrement, **pas** d'exécution GPU PS5.

**Travail restant :** allocateur avec budget VRAM, propriété des deux
snapshots, fences jusqu'à la fin des lectures GPU, frames/timestamps réels,
séparation HUD, réinitialisation après pause/jeu/changement de sortie,
branchement sur le renderer actif, qualification modèle et RADV/PS5, benchmark
sur console. Ne jamais coder les booléens de preuve à true artificiellement.
