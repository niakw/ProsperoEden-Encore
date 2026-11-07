# Eden Encore R09 — entrée proxy vers 16 canaux (7 novembre 2026)

**Statut : primitive RDNA2 ajoutée, non branchée au renderer PS5 ; aucune
preuve de frame NR ni de parité numérique GPU.**

Référence indépendante MIT :
[OpenDLSS-NR shaders/preprocess.comp](https://github.com/maanHimself/OpenDLSS-NR/blob/main/shaders/preprocess.comp)
et [docs/network.md](https://github.com/maanHimself/OpenDLSS-NR/blob/main/docs/network.md).

La génération suit l'ordre connu des 16 canaux : bruit gaussien
déterministe en 0–2, constante 1 en 3, trois valeurs couleur centrées
sur le proxy sRGB en 4–6, copie du proxy **sans historique** en 7–9,
style/ton/structure/peau/masque en 10–14, zéro en 15.

Le shader `proxy_features_rdna2.comp` lit un buffer `RGBA32F`
**déjà normalisé display-referred**, applique la géométrie miroir
pour la zone paddée, puis produit un buffer `FP16[16]` par pixel.
Il se raccordera à `NrRdna2ImageFeatureStage` (matrice locale
apprise FP16[32×16] → E4M3FN[32]) sans copier les poids NVIDIA.

Le réseau public produit initialement des f32[16] : le stockage
intermédiaire FP16 de ce port doit encore être comparé à la
référence avant d'être qualifié exact. Les bornes hôte vérifient
dimensions, miroir unique, tailles de buffers, valeurs de
conditionnement, limite 256 Mio et descripteurs STORAGE distincts.
Les en-têtes SPIR-V Vulkan 1.1 sont générés et vérifiés en CI.

**Manquent toujours :** production du proxy depuis la couleur HDR
réelle du jeu et son exposition, historique/profondeur/mouvement,
le prébloc Swin+downsample, les gains U-Net C64/C128/C256,
le réseau complet et le compositing postbloc. Aucune de ces étapes
n'est remplacée par une approximation cachée.
