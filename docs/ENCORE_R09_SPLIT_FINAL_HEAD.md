# R09 — Split-Swin FinalHead 512→1024 RDNA2/Vulkan (06/11/2026)

Le dernier opérateur `CCSplitSwin16HFinalHead` est maintenant un composant natif `NrRdna2SplitFinalHead` dans le vendor. Il lit la matrice canonique NRMODEL1 `unpacked-splitswin/blockN.layer4.layer.weight.bin` de taille [1024,512] E4M3FN (refus de taille invalide / NaN), la transfère avec `NrRdna2GpuWeights`, puis utilise **les kernels communs existants** `NrRdna2ProjectionQuantized` : GEMM FP8→FP32 suivi de quantification FP32→FP8, sur le même scheduler Vulkan et sans lecture CPU. Il n'y a pas de branche résiduelle pour cette couche ; le tail brut de 16 octets du record amont n'est pas utilisé comme coefficient fictif.

Le code valide les buffers non aliasants et le plan complet `PrepareQuantizedProjection` avant enregistrement. Les tests hôte `test_rdna2_nr_split_final_head_weights` couvrent les tailles, rejets FP8, domaine natif par défaut **1920 tokens** (`floor(60/4)*floor(33/4)*16`) et domaine intégral paddé **2560 tokens**. Le second mode est mathématiquement équivalent pour les tokens ajoutés si **toute la queue d'entrée est préalablement mise à zéro**, puisqu'il s'agit d'une multiplication linéaire sans biais ; il utilise davantage de GPU, ce n'est pas un mode optimisé.

Ce raccord fournit une sortie FP8 [tokens,1024] en ordre de tokens 4x4. Le passage final à la disposition raster/ViT, les cinq sous-étapes de chaque bloc ViT et l'ordonnancement du réseau complet restent à faire. Tests inscrits dans CMake, compilation Vulkan/CI et exécution console non attestées. Pas d'activation prématurée du DLSS-NR.


## Chaînage direct du bloc terminal

`NrRdna2SplitSwinBlock::InitializeWithModel` accepte désormais `final_head_tokens` dans le plan et deux buffers externes `final_fp32` et `final_output`. Quand la sortie secondaire `ProjPool` est demandée, le bloc importe également la couche 4 du même record (`blockN.layer4.layer.weight.bin`) et garde le composant `NrRdna2SplitFinalHead` jusqu'à la fin des commandes GPU. `Record()` enchaîne `Proj` → `ProjPool` → `FinalHead` ; aucun résultat primaire n'est substitué au pool. La taille déclarée des tokens de pool doit couvrir les tokens de `FinalHead`; tailles, aliasing et modèle sont vérifiés avant de publier le bloc. Le résultat sort en FP8 1024 canaux, encore à transposer au format ViT exigé par les étapes suivantes.
