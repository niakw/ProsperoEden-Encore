# R09 — reconstruction des gains U-Net à partir des régions FP16 réelles

Date : 7 novembre 2026. Chantier DLSS-NR indépendant de l'issue moteur #15.

## Provenance technique

Le découpage extrait par `Overclockers/DLSSNR-AMD` produit, pour les
étages `_upsample` C64/C128/C256, `residual_scale` de C+16 scalaires
FP16 et `upsample_gain` de C−16 scalaires. Dans son analyse du code
amont, la disposition est `[C residual][16 premier gain]` suivie
immédiatement du reste du vecteur de gain. Le modèle séparé
`OpenDLSS-NR` décrit la même structure de bloc natif :
`ffnCosSkip` C valeurs directement suivi de `transitionScale` C
valeurs, sans padding pour C≥64. Cette corroboration vaut pour la
disposition des données, **pas pour la parité d'une frame PS5**.

Références :
- https://github.com/Overclockers/DLSSNR-AMD/blob/main/linux/src/core/nr_graph.cpp
- https://github.com/Overclockers/DLSSNR-AMD/blob/main/linux/package/model-tools/unpack_swin_family.py
- https://github.com/maanHimself/OpenDLSS-NR/blob/main/src/nr_graph.cpp

## Contrat implémenté

- C32 : `upsample_gain` de 32 valeurs, inchangé.
- C64/C128/C256 : si la source contient C−16 valeurs de gain et C+16
  valeurs de résidu, reconstruire exactement
  `residual[C:C+16] + gain[0:C−16]`.
- Le poids résiduel de la couche large provient des **premiers C**
  scalaires de la région résiduelle ; les 16 suivants ne sont pas
  interprétés comme des résidus.
- Si un modèle indépendant apporte déjà un gain **complet C**, ne pas
  le reconstruire une deuxième fois.
- Refuser tailles non exactes, NaN/Inf, troncatures et modèles
  incomplets ; aucune valeur de repli, de zéro ou de gain inventé.
- Le précontrôle `NrRdna2CoreFeatureSequence` utilise exactement ce
  chargeur avant le premier enregistrement de commandes.

Le test hôte `test_rdna2_nr_upsample_gain_reconstruction` vérifie
les quatre largeurs, valeurs récupérées dans le bon ordre, résidus,
modèles pré-reconstruits et échecs transactionnels.

## Qualification à poursuivre

Le découpage fixe un blocage de chargement. Il ne démontre pas :
1. la parité numérique de chaque étage en exécutant un vrai modèle ;
2. une inférence GPU complète (séquence de première frame et textures) ;
3. le chemin temporel/HDR final, ni le rendu sur console.

Ces preuves restent explicitement ouvertes. Pas de build PS5 global.
