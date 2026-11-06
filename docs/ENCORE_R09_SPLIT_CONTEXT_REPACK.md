# Eden Encore R09 — sortie attention Split-Swin : réagencement GPU

La primitive `NrRdna2WindowAttention` renvoie du FP8 sous la forme réelle `[fenêtre][tête16][token64][canal32]`. La `NrRdna2Projection` suivante exige `[fenêtre][token64][tête16][canal32]`, c'est-à-dire des vecteurs de **512 canaux contigus par token**. Injecter directement le premier buffer dans la seconde GEMM serait **mathématiquement faux** malgré des tailles égales.

Nouveau kernel `split_context_repack_rdna2.comp` et wrapper `NrRdna2SplitContextRepack` :

- Transposition exacte de mots FP8 empaquetés, sans conversion et sans retour CPU.
- Deux descripteurs STORAGE_BUFFER et 16 octets de constantes `windows / heads / src / dst` ; 256 threads par groupe, 16 têtes et 64 tokens par fenêtre.
- `CanSplitContextRepack` refuse toutes tailles, offsets ou fenêtres incohérents et les indexages qui dépasseraient les capacités. Le wrapper refuse également l'aliasing source/destination.
- La passe se termine par une barrière GPU compute→compute avant la projection.

Tests ajoutés : oracle CPU avec deux fenêtres et identification unique de chaque mot FP8, limites mémoire et géométrie, plus contrôle glslang/spirv-val/dis pour l'ABI SPIR-V Vulkan 1.1.

**Important :** ce raccord est une condition nécessaire pour assembler `QKV → attention → projection`. Il ne prouve pas encore qu'un bloc complet Split-Swin ait été exécuté ni que la topologie U-Net et les dépendances soient raccordées.
