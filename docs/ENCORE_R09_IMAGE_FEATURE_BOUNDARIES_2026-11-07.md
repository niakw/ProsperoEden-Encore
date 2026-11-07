# R09 — frontières pré/post image : poids locaux et tenseurs de caractéristiques

*7 novembre 2026 · statut : primitive GPU intégrée en source, aucune preuve
d'image PS5, pas un pipeline HDR prêt à présenter.*

## Deux matrices apprises identifiées dans l'amont MIT

Source : [unpack_preblock.py](https://github.com/Overclockers/DLSSNR-AMD/blob/main/linux/package/model-tools/unpack_preblock.py)
et [unpack_postblock.py](https://github.com/Overclockers/DLSSNR-AMD/blob/main/linux/package/model-tools/unpack_postblock.py).

- **Pré-image** : `block0.layer0.layer.input_lift.bin` importe
  précisément **FP16 [32,16] = 1 024 octets** depuis
  `unpacked-preblock/` dans un modèle NRMODEL1 local.
- **Post-image** : `block70.layer0.layer.out_project.bin` pour
  Original et `block30` pour Compact importent exactement
  **FP16 [16,32] = 1 024 octets** depuis `unpacked-postblock/`.
- Les 512 coefficients doivent tous être FP16 finis et non tronqués.
  Le loader `PrepareImageFeatureWeights` refuse nom, bloc, taille et
  valeur illégaux sans laisser de données partiellement valides.

## Primitive Vulkan RDNA2

Le même shader `image_feature_rdna2.comp` exécute :

1. **Lift** : raster FP16 à 16 caractéristiques par pixel →
   projection [32,16] → raster E4M3FN à 32 canaux, pour le
   corps Swin pré-image.
2. **Project** : raster E4M3FN à 32 caractéristiques par pixel →
   projection [16,32] → raster FP16 à 16 canaux, pour le
   compositing post-image.

Chaque pixel dispose de 32 octets d'entrée et 32 octets de sortie.
Le calcul utilise FP32 pour l'accumulation et les conversions FP16/FP8
explicitement. Le host refuse les dimensions invalides, les buffers
aliasés, les entrées tronquées et plus de 256 Mio par ressource ;
les dispatchs se font par ligne pour éviter une limite globale de
workgroups en X. Trois bindings STORAGE, 3 uints push ; compilation
et contrôle SPIR-V Vulkan 1.1 automatiques, sans HIP, RTX ou D3D12.

## Frontière critique toujours non résolue

**Ces 16 caractéristiques ne sont PAS assimilables arbitrairement
à une texture RGBA, au depth buffer ni à des vecteurs de mouvement.**
L'extraction des modèles identifie les matrices, mais ni le schéma
d'encodage des 16 entrées du prébloc ni la composition HDR/RGB
complète des 16 sorties après le postbloc ne sont prouvés. De plus,
les deux blocs Swin fusionnés pré/post contiennent d'autres poids,
gains et opérations à intégrer et à vérifier numériquement.

Cette primitive rapproche le socle fonctionnel de la couverture des
152/76 couches ; elle **ne rend pas DLSS-NR activable**. Les autres
bloquants demeurent : gains C64/C128/C256 de l'U-Net, orchestration
globale, guide couleur/profondeur/mouvement fiable, exécution GPU
testée et validation P5. Aucun modèle propriétaire redistribué.
