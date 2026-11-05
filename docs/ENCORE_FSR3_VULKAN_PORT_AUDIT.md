# Eden Encore — AMD FSR 3 Frame Generation (PS5, étude de port)

## Séparation des fonctions

**FSR 1 (EASU + RCAS)** est déjà utilisé par l'émulateur comme
**upscaling spatial**. Il ne touche pas au nombre de frames produites.

**FSR 3.1 Frame Generation** est un moteur d'interpolation distinct,
susceptible de s'associer à un autre upscaler. Le sélecteur du menu
**Fluidité améliorée** le propose comme méthode à implémenter,
mais il ne doit pas déclarer un boost de FPS lorsque le backend ne
produit aucune vraie frame synthétique.

## Sources AMD pertinentes au 5 novembre 2026

- SDK FidelityFX 1.1.4 (FSR 3.1.4), sources C++ / HLSL et backend
  Vulkan, MIT : https://github.com/GPUOpen-LibrariesAndSDKs/FidelityFX-SDK/releases/tag/v1.1.4
- AMD FSR SDK 2.4 : implémentation analytique de Frame Generation
  3.1.6 et gestion de présentation 3.1.7 avec un mode Vulkan ;
  les API 2.x exigent cependant des DLL AMD précompilées et signées,
  impossibles à charger directement comme bibliothèques natives PS5.
  Références : https://gpuopen.com/amd-fsr-sdk/ et
  https://gpuopen.com/manuals/fsr_sdk/techniques/frame-interpolation-swap-chain/
- Exigences publiques de données :
  https://gpuopen.com/manuals/fsr_sdk/techniques/super-resolution-upscaler/
  et https://gpuopen.com/amd-fsr-framegeneration/

Le SDK 1.x est le point de départ **adaptable à la compilation native**.
Le SDK 2.x moderne n'est **pas** un raccourci : une DLL Windows x64 ne
devient pas une bibliothèque PS5 en la renommant. Une adaptation des
sources 1.x ne garantit aucune compatibilité avec les shaders/runtimes
RADV et l'ABI du port PS5.

## Écart technique réel dans le renderer

Le composite PS5 possède aujourd'hui une succession de vraies images,
leurs horodatages, la surface Vulkan et la cadence du PresentManager.
Ces ressources suffisent à étudier des moteurs **sans mouvement invité**
comme MihawkGen et LSFG, mais **pas à alimenter fidèlement FSR 3**.

Pour FSR3, il faut raccorder au minimum :
- Les vecteurs de mouvement **par pixel**, correctement dimensionnés,
  avec la bonne convention de direction et la durée entre frames.
- La **profondeur** associée au rendu et ses conventions (inversée,
  infinie, plans proche/lointain).
- Le **jitter temporel**, la projection de caméra et les resets d'historique.
- Le moteur d'optical flow analytique et sa préparation des ressources.
- La présentation et le pacing des images interpolées avec composition
  du HUD natif **après** génération et synchronisation GPU/fences.

Le guest Switch NS1 ou NS2 ne remet pas directement ces données au
composite de l'hôte : il envoie des commandes GPU, des surfaces
composées et des shaders invités. Le depth de l'hôte peut être réutilisé
par plusieurs passes et ne garantit pas qu'une texture de profondeur
récupérable corresponde à l'image finalement affichée. **Ne pas
remplacer tous les mouvements par des zéros, ni recycler un depth
aléatoire, ni convertir le shader EASU/RCAS de FSR 1 en « FSR 3 ».**

Ordre d'intégration réaliste et réutilisable pour tous les jeux :
1. Observer dans le rasterizer les attachments depth et les ressources
   temporelles qui survivent jusqu'au vrai frame handoff.
2. Identifier les conventions et leur correspondance à la frame affichée,
   sans code spécial FC27/BOTW/NS2.
3. Ajouter une capture générique conservatrice des buffers valides,
   et mesurer mémoire/timing sans les copier au CPU.
4. Porter le contexte FSR3 1.x Vulkan, compiler ses shaders SPIR-V,
   vérifier les capacités PS5 et la mémoire.
5. Relier la génération au même présenter réel/synthétique
   propriétaire que MihawkGen, avec fallback sans attendre les frames
   du jeu, puis tests PS5 réels.

Les ressources indiquées par AMD pour la seule interpolation atteignent
environ 124 Mio en 1080p, 214 Mio en 1440p, 457 Mio en 4K sur une
configuration PC de référence. Elles **n'incluent pas** la surcharge du
swapchain et **ne constituent pas une mesure de VRAM PS5**.

AMD recommande une cadence source d'au moins 60 FPS pour une meilleure
qualité et déconseille particulièrement les sources sous 30 FPS.
Ainsi une capture 30->60 sera utile seulement si artifacts/latence
restent raisonnables sur la console.

## Verdict actuel

**R07 / FSR 1 spatial : présent.**
**R08 / FSR 3 Frame Generation complet et officiel : aucun backend
intégré ; les entrées du jeu (motion/depth/jitter) restent à démontrer.**

**R08 / alternative FSR3 optical flow : code natif désormais intégré en
PR #21**, via Swordpdf/ps5-framegen à SHA 6436210 et 10 shaders SPIR-V
validés. C'est une adaptation du flux optique AMD FSR 3, utilisant
les deux images compositées successives sans prétendre posséder des
vecteurs de mouvement invités. La génération est enregistrée dans le
Composite Vulkan, les images sont soumises synthétique puis réelle,
et les historiques privés sont protégés par ticks GPU. L'ordre d'UI
conserve MihawkGen puis FSR3 puis Lossless (DLL utilisateur dernier).

**Validation :** code source, compilation des objets C++ hôtes,
13/13 tests CTest (dont 911 cas pacing), 10 SPIR-V valides.
**Ne pas déclarer de résultat PS5 ni de gains de FPS mesurés.**
Le port reste à vérifier sur console et le pacing réel de l'émulateur
est conservateur tant qu'un compteur VI fiable n'est pas raccordé.
