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
