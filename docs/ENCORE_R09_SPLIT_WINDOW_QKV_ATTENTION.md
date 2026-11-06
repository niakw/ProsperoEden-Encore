# Eden Encore — R09 Split-Swin : raccord QKV → attention RDNA2

6 novembre 2026 — PR #24, hors `main`. **Raccord de deux dispatchs**, non un réseau DLSS-NR terminé.

## Code intégré

Le vendor fournit `NrRdna2SplitWindowLink`, qui instancie deux kernels Vulkan déjà portés :
- `NrRdna2QkvProjection` produit Q, K, V E4M3FN par fenêtre (64 tokens, 32 canaux/tête, 1/2/4/8/16 têtes) ;
- `NrRdna2WindowAttention` lit les **mêmes** buffers et calcule softmax + produit P×V sur la fenêtre.

Le raccord détient ses deux jeux de descripteurs `STORAGE_BUFFER`, écrit les 11 bindings Vulkan avec les mêmes handles Q/K/V aux deux extrémités (attention : biais en binding 3, sortie en binding 4) et vérifie les huit buffers physiques, leur indépendance, leurs plages et la limite de descripteur du périphérique. Les `Record` existants enregistrent les deux dispatchs sur le scheduler commun avec barrière compute → compute. Le propriétaire externe doit garder vivants les buffers jusqu'à la fin de la soumission GPU.

`CanSplitWindowLink` refuse les différences de fenêtre, nombre de têtes, offsets Q/K/V, capacités ou strides/alignements malformés. Le test hôte `test_rdna2_nr_split_window_link` est ajouté et la nouvelle unité C++ inscrite dans `video_sources` PS5. **Compilation/CTest/CI non encore confirmés au moment de la publication.**

## Ce que ce lot ne couvre pas

Ce raccord n'est pas le chaînage complet des **65 opérations Split-Swin Original / 17 Compact**. Il manque notamment le chargement correct des poids/échelles/biais par bloc, les opérations de FFWD/projection/pooling/final-head, l'ordonnancement interblocs, les résidus, la liaison avec les 40 ViT de chaque modèle et les conversions image/renderer. Le graphe entier reste volontairement non activable. Aucune hypothèse de 60 FPS ni de compatibilité console n'est avancée.

Source de vérité : `nr_rdna2_native_graph_schedule.h` (décodage intégral) et `nr_rdna2_split_window_link_policy.h` (liaison QKV/attention effectivement enregistrable).

## ViT — correction de dimension du contrat (même lot R09)

Le manifeste natif 1920×1080 indique **2560 tokens** pour le tronc ViT, mais la primitive d'attention globale RDNA2 limitait son contrat hôte à 2048. La borne passe à **4096 tokens** ; la mémoire adressée reste vérifiée en 64 bits et la géométrie des dispatchs Vulkan reste à 32 têtes, ceil(tokens/32). Le shader source était déjà paramétrique et ne nécessite pas de contournement. Tests ajoutés pour 2560 (positif) / 4096 (borne) / 4097 (refus), et capacité insuffisante. Cela élargit la **couverture dimensionnelle**, pas encore l'assemblage des 40 opérations ViT ni la validation GPU.

## Modèle local Split-Swin et upload GPU

Le nouveau `nr_rdna2_split_window_weight_loader.h` importe les données canoniques de `unpacked-splitswin/blockN.layerM.layer` dans NRMODEL1 :
- `.qkv.bin` E4M3FN [1536,512], réordonné dans le vrai format attendu par le shader RDNA2 **[head16][Q32,K32,V32][512]** ;
- `.attn_pos_bias.bin` FP16 [16,64,64], décodé en FP32 puis désentrelacé par `NeuralDeswizzleBias64` ;
- `.tail.bin` 64 octets = 16 facteurs de température FP32, avec refus des NaN/infini.

`NrRdna2SplitWindowModelBuffers` effectue trois uploads distincts via **l'allocateur GPU commun** `NrRdna2GpuWeights` et garde les allocations pendant la vie du raccord. `NrRdna2SplitWindowLink::InitializeWithModel` lie ces trois ressources à QKV + attention sur le même scheduler. Le plan doit demander **16 têtes logiques** : le champ `heads=4/8` du manifeste natif représente des groupes de dispatch, pas le nombre de têtes du modèle. Les tenseurs d'activation, Q/K/V et sortie demeurent à fournir par le renderer.

Test hôte `test_rdna2_nr_split_window_weight_loader` : permutation des trois projections, cas 16 têtes, 64 octets de températures, NaN, tailles invalides et biais 16×4096. Compilation CTest/PS5 et exécution shader **non confirmées** à la publication. Le portage intégral Split-Swin 65/17 opérations reste ouvert.
