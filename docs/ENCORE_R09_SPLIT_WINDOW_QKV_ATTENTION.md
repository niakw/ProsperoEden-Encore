# Eden Encore — R09 Split-Swin : raccord QKV → attention RDNA2

6 novembre 2026 — PR #24, hors `main`. **Raccord de deux dispatchs**, non un réseau DLSS-NR terminé.

## Code intégré

Le vendor fournit `NrRdna2SplitWindowLink`, qui instancie deux kernels Vulkan déjà portés :
- `NrRdna2QkvProjection` produit Q, K, V E4M3FN par fenêtre (64 tokens, 32 canaux/tête, 1/2/4/8/16 têtes) ;
- `NrRdna2WindowAttention` lit les **mêmes** buffers et calcule softmax + produit P×V sur la fenêtre.

Le raccord détient ses deux jeux de descripteurs `STORAGE_BUFFER`, écrit les 11 bindings Vulkan avec les mêmes handles Q/K/V aux deux extrémités et vérifie les huit buffers physiques, leur indépendance, leurs plages et la limite de descripteur du périphérique. Les `Record` existants enregistrent les deux dispatchs sur le scheduler commun avec barrière compute → compute. Le propriétaire externe doit garder vivants les buffers jusqu'à la fin de la soumission GPU.

`CanSplitWindowLink` refuse les différences de fenêtre, nombre de têtes, offsets Q/K/V, capacités ou strides/alignements malformés. Le test hôte `test_rdna2_nr_split_window_link` est ajouté et la nouvelle unité C++ inscrite dans `video_sources` PS5. **Compilation/CTest/CI non encore confirmés au moment de la publication.**

## Ce que ce lot ne couvre pas

Ce raccord n'est pas le chaînage complet des **65 opérations Split-Swin Original / 17 Compact**. Il manque notamment le chargement correct des poids/échelles/biais par bloc, les opérations de FFWD/projection/pooling/final-head, l'ordonnancement interblocs, les résidus, la liaison avec les 40 ViT de chaque modèle et les conversions image/renderer. Le graphe entier reste volontairement non activable. Aucune hypothèse de 60 FPS ni de compatibilité console n'est avancée.

Source de vérité : `nr_rdna2_native_graph_schedule.h` (décodage intégral) et `nr_rdna2_split_window_link_policy.h` (liaison QKV/attention effectivement enregistrable).
