# Eden Encore R09 — projection résiduelle native Split-Swin

Le vendor contient `NrRdna2SplitResidualProjection`, un raccord fonctionnel pour les couches `CCSplitSwin16HFfwdProj` et `CCSplitSwin16HProj` à **512 canaux** :

- Importe depuis NRMODEL1 le couple `unpacked-splitswin/blockN.layerM.layer.weight.bin` (matrice E4M3FN row-major 512×512) et `.skip_weight.bin` (512 scalaires FP16).
- Valide la taille exacte, les coefficients FP16 finis et les poids FP8 non-NaN. Utilise deux `NrRdna2GpuWeights` VMA immuables. Les buffers externes d'entrée FP8, de résidu FP8, de sortie FP8 et de scratch FP32 sont vérifiés et non aliasants vis-à-vis des sorties.
- Enregistre la `NrRdna2Projection` FP8→FP32 puis l'épilogue commun `NrRdna2VitEpilogue::RecordResidual`, avec barrière compute→compute. Le modèle et ses buffers sont conservés par le raccord jusqu'à sa destruction. Aucun poids tiers n'est intégré au code.

Cela permet d'utiliser exactement le même chemin 512×512 sur les deux classes de projections Split-Swin, **sans** inventer de kernel de résidu spécifique. Le test hôte `test_rdna2_nr_split_residual_weights` vérifie matrices, gains, NaN, capacités GPU et les limites du contrat. La variante `ProjPool` réclame encore son **deuxième résultat poolé**, qui n'est pas implicitement équivalent à la projection simple.

**Encore à assembler :** FFWD3 → FFWDProj → QKV+attention → Proj, ainsi que leur gestion des tenseurs de fenêtre, des résidus exacts, du pooling, des poids par bloc, de l'ordonnancement global et du renderer. La présence des primitives ne prouve aucune frame ni performance DLSS-NR. Compilation/CI et exécution console toujours non confirmées.
