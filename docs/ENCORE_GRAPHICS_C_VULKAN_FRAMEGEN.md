# C / R08 — Vulkan frame generation (état vérifiable)

Branche : `feat/encore-c-vulkan-framegen`. Ne pas fusionner `main` ni modifier le vendor pour de simples contrats.

## Priorités et choix d'intégration

| Ordre | Méthode | Source / licence | État concret | Prochaine preuve |
|---|---|---|---|---|
| 1 | MihawkGen natif PS5 | `mihawk-99/PS5_MihawkGen` @ `c57232a`, module `framegen/` GPL-3.0-or-later, outillage PS5 MIT ; modèle `network.fgw` à auditer avec notices | Source épinglée en sous-module, **aucun code de génération branché dans le renderer Encore** | Construire module et modèle sur la toolchain PS5, vérifier Vulkan/RADV, layouts/barrières/fences et premier couple d'images |
| 2 | FSR 3.1 Frame Generation | AMD FidelityFX SDK, code MIT ; nécessite flux temporal/motion/depth et swapchain Vulkan qualifiés | Contrat R06 seulement | Prouver depth/motion/jitter invités, HUD distinct, profil de latence ; comparer aux mêmes images |
| 3 | LSFG / Lossless Scaling | Intégration amont ProsperoEden pouvant dépendre d'une DLL Windows non redistribuable | Non intégré à Encore ; aucune DLL embarquée | Confirmer droits de distribution et backend **natif PS5** ; sinon refuser cette option |

Le sous-module MihawkGen, pas les fichiers de son `external/` en bloc, constitue la provenance. Avant diffusion de tout modèle, confirmer séparément code, poids et notices.

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
2. **C2, ouvert :** compilation GPU PS5 de Mihawk, vérification de son modèle et du chemin d'entrée Vulkan utilisé par Encore. Ne pas activer le mode dans l'UI tant qu'inexécutable.
3. **C3, ouvert :** enchaînement réel frames précédent/courant/synthétique avec mémoire, ownership, layouts, barrières, fences et timing PS5 ; repli sans régression NS1/NS2.
4. **C4, ouvert :** exposer les modes réellement disponibles en Paramètres > Vidéo et par titre, sérialisation et traductions, sans choix fictif.
5. **C5, ouvert :** A/B visuel et latence PS5 ; comparer FSR 3 sur même scène, accepter/refuser LSFG selon la faisabilité native et la licence.
