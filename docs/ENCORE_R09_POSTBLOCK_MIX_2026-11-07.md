# R09 — postbloc C32, priorité à la première inférence complète

7 novembre 2026. Sans optimisation et sans build global PS5.

**En source** : le shader Vulkan 1.1 `postblock_mix_rdna2.comp` exécute
l'upsample nearest 2× de la remontée C32 et le mélange avec le skip C32
pleine résolution du prébloc, avec deux gains FP16 appris distincts.
Le wrapper `NrRdna2PostblockMix` charge strictement ces gains depuis
un NRMODEL1 local (Original 70 / Compact 30), vérifie trois ressources
distinctes et publie un raster E4M3FN 32 canaux, non une image.
Le contrat vérifie les dimensions exactes des plans natifs, et la CI
hôte compile/valide l'ABI shader et la syntaxe C++.

**Non prouvé** : parité numérique/FP16 sur modèle réel, chaîne de pixels
du prébloc, sortie Swin finale, projection vers les caractéristiques de
sortie, compositing HDR, rendu PS5. Rien n'est activé par défaut.
Aucun poids incomplet n'est complété par des zéros ou gains inventés.
Les gains U-Net C64/C128/C256 manquants restent bloquants.

Les dimensions logiques du plan sont transposées dans le raster GPU :
entrée basse 540×960, sortie/skip 1080×1920 pour le plan 1920×1080.
Le contrôle hôte valide cette convention sans permuter les octets.

## Nouveau chaînage GPU du postbloc
`NrRdna2PostblockRun` crée maintenant, à partir d'un NRMODEL1
local et du plan complet, une chaîne préparable et enregistrable :
1. mélange C32 appris (remontée demi-résolution + skip plein raster) ;
2. bloc FSwin C32 pleine résolution, avec les poids appris
   `unpacked-postblock/block70` ou `block30` et repack des fenêtres ;
3. projection finale FP16 [16,32] par shader Vulkan existant.

Les étapes partagent un seul scheduler Vulkan. Tous les buffers doivent être
distincts, et chaque propriétaire refuse l'absence de poids ou un nouveau
Record après une tentative. L'instance est non réutilisable après échec.

Il s'agit d'une **sortie de 16 caractéristiques FP16**, pas encore d'un
RGB final. La parité du corps Swin fusionné et du résiduel FP16 devra être
comparée aux captures de référence ; aucun rendu PS5 validé.

## Projection postbloc sans quantification FP8 intermédiaire

Le vendor inclut désormais un chemin explicite
`NrRdna2PostblockRun::PrepareWithRawProjection` qui conserve l'ancien
`Prepare` FP8 pour compatibilité. Le dernier FSwin C32 produit aussi un
raster **FP16[32] brut** avant quantification (passe dense-3 raw) ; la
projection apprise `out_project` [16,32] lit directement ces 64 octets par
pixel, puis émet FP16[16]. Le nouveau mode `ImageFeatureShape.direction=2`
contrôle séparément sa capacité (entrée double, sortie inchangée) et
les mêmes poids locaux. Les six ressources externes sont distinctes,
et le même scheduler ordonne la passe raw et le projecteur.

Ce raccord lève une perte FP8 artificielle à l'extrémité de la chaîne,
mais n'établit ni la parité FP16 sur un vrai modèle, ni la signification
des 16 sorties, ni le compositing RGB/HDR et temporel. Tests hôte
C++/SPIR-V requis ; aucune présentation PS5 ou activation automatique.
