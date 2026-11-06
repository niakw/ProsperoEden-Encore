# Eden Encore — Split-Swin FFWD3 : reconstructeur canonique (6 novembre 2026)

## Raccord fonctionnel publié

Les deux matrices NRMODEL1 `unpacked-splitswin/blockN.layer0.layer.ffwd_a.bin` et `ffwd_b.bin` de 512×512 éléments E4M3FN ne correspondent **pas** directement aux trois buffers d'entrée de `ffwd3_group_rdna2.comp`.

Le code du MIT `Overclockers/DLSSNR-AMD` fournit deux transformations exactes :

1. `unpack_splitswin.py` désentrelace chaque fragment d'origine en matrice canonique [512,512], en tranches 16×32 N-fastest.
2. `nr_graph.cpp` documente trois indexations bit à bit `ff_a`, `ff_q0`, `ff_q2` pour les véritables W1/W2/W3 du bloc FFWD3.

Le nouveau `nr_rdna2_split_ffwd_weight_loader.h` applique **l'inverse** du premier ordonnancement pour les deux fichiers, puis les indexations `ff_a/q0/q2`, sans supposer qu'un découpage de colonnes représente directement les tenseurs du shader. Résultat :
- W1 : [8 groupes][64][512], 262 144 octets ;
- W2 : [8 groupes][256][64], 131 072 octets ;
- W3 : [8 groupes][64][256], 131 072 octets.

`NrRdna2SplitFfwdLayer` importe ces données depuis NRMODEL1 local et alloue trois buffers GPU immuables via `NrRdna2GpuWeights`. Il possède son jeu de descripteurs Vulkan, lie l'entrée/sortie FP8 externe et enregistre le kernel existant `NrRdna2FFWD3`. Échec transactionnel sur poids manquants, dimensions erronées ou NaN FP8 ; pas de poids propriétaire distribué.

Le test hôte `test_rdna2_nr_split_ffwd_weights` réalise un aller-retour intégral sur deux matrices synthétiques de 262 144 octets et vérifie **les 524 288 adresses** des trois matrices contre la cartographie d'origine. Les permutations complètes avaient également été vérifiées comme bijectives, sans collisions ni sorties hors plage.

**Limites :** cette étape fournit la famille FFWD3 réelle, mais elle n'est pas encore chaînée avec les projections résiduelles `FFWDProj`, QKV/attention et `Proj/ProjPool`. La taille active du domaine FFWD doit venir du plan des tuiles, pas être déduite du nombre de fenêtres paddées. La compilation native/CI et le rendu GPU restent à confirmer. Aucun build PS5 complet ni activation DLSS-NR.

Sources amont : `linux/package/model-tools/unpack_splitswin.py` et `linux/src/core/nr_graph.cpp` de `Overclockers/DLSSNR-AMD`.
