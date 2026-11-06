# R09 — gains FSwin upsample : frontière des 16 coefficients (06/11/2026)

État : **problème de reconstruction de région**, pas démonstration que les 16 coefficients sont absents du modèle. Aucun déblocage artificiel dans l'inférence.

## Éléments vérifiés dans l'amont MIT

`Overclockers/DLSSNR-AMD`, `linux/package/model-tools/unpack_swin_family.py` et `linux/src/core/nr_graph.cpp` :

- Les fichiers `.upsample_gain.bin` sortent `C` éléments FP16 à C32, mais **C−16** à C64/C128/C256.
- Les fichiers `.residual_scale.bin` correspondants occupent `C+16` éléments FP16 lorsque l'upsample est non paddé.
- **Le compte total se ferme** : `(C−16)+(C+16)=2C`. La région adjacente peut contenir les 16 valeurs du gain que le découpage amont met dans `residual_scale`.
- L'amont teste plusieurs placements : les seize valeurs au début ou à la fin du gain, et deux choix de découpage du résidu. Ses propres commentaires précisent que la correspondance n'est **pas prouvée** par la simple comptabilité d'octets.
- Les comparaisons de la capture de référence sur une des couches rapportent des scores proches malgré différents placements (environ 0,1411 / 0,1462 / 0,1386) ; il manque un oracle du placement des canaux. Les écarts de géométrie des tuiles peuvent aussi dominer l'erreur.

## Règle d'intégration

`PrepareFSwinUpsampleWeights` du vendor continue d'exiger **C valeurs FP16 validées** et échoue sans modifier l'état si seulement `C−16` sont présentes. Ne pas remplacer les seize valeurs par zéro, ne pas adopter un placement par hypothèse, et ne pas faire passer le graphe complet en force.

**Prochaine preuve fonctionnelle à produire :** valider la frontière du résidu/gain et le repérage des tuiles contre un tenseur de référence (ou les sorties intermédiaires du modèle à statut légal compatible), sur C64/C128/C256. Lorsque ce placement est démontré, le loader pourra reconstruire un vecteur C à partir de deux régions déjà présentes dans le même NRMODEL1, de façon transactionnelle.

## État des autres raccords R09

- ViT : chemin par bloc `FP8 GEMM → FP32 QKV norm → E4M3 Q/K/V → attention`, avec import des poids [3072,1024] et 32 températures, puis allocations GPU distinctes. **Pas encore les cinq opérations ViT en séquence.**
- Split-Swin : QKV [1536,512], 16 têtes, biais [16,64,64] et températures tail FP32 : import, réorganisation, upload GPU, QKV + attention par bloc. **Pas encore les quatre opérations Split-Swin en séquence.**
- Pré-image, décodeur, post-image, branchements interblocs et sortie renderer : toujours incomplets.
- Une compilation statique et une inscription CMake ne prouvent pas une frame DLSS-NR sur console.

Sources : [nr_graph.cpp](https://github.com/Overclockers/DLSSNR-AMD/blob/main/linux/src/core/nr_graph.cpp), [unpack_swin_family.py](https://github.com/Overclockers/DLSSNR-AMD/blob/main/linux/package/model-tools/unpack_swin_family.py).
