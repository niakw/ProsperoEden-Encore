# Eden Encore — pont de plan natif DLSSNR-AMD → chaînes FSwin RDNA2

État : **port partiel de l'ordonnancement**, sans activation graphique, sans mesures de performance ni image PS5.

## Objectif

Le dépôt MIT [Overclockers/DLSSNR-AMD](https://github.com/Overclockers/DLSSNR-AMD) dispose de tables décrivant le graphe global des modèles « original » et « small ». `nr_native_plan.cpp` produit un plan texte de 21 champs (19 historiques et deux décalages de fenêtres). `nr_graph.cpp` le transforme en étapes CPU/GPU.

Le nouveau header partagé `vendor/encore-active/eden-vulkan/include/video_core/renderer_vulkan/nr_rdna2_native_plan_bridge.h` **lit strictement** ces lignes et distingue les séquences FSwin classiques des étapes pré/post-image, des entrées/sorties de disposition, des transitions down/up, du split-Swin, du ViT et des branches du graphe. Aucune approximation ne convertit silencieusement ces dernières en une couche FSwin normale.

## Contrat et intégration effective

- Accepte les 19 ou 21 colonnes et garde les indices, dimensions, dispatchs, références d'entrée, types, noms de kernels et offsets signés.
- Limites d'entrée, contrôle de l'ordre `block/layer`, des dépendances simples et du nombre total de lignes. Un plan malformé renvoie un échec **sans plan partiel**.
- `ExtractNativeFSwinSegments` ne retient que les blocs `CCTinlayoutFusedSwin...` standards où les formats sont identiques : C=32/64/128/256, `heads=C/32`, dimensions de fenêtres identiques, offsets de fenêtre explicites entre -1 et +1.
- Les segments génèrent les préfixes de poids `unpacked/blockN.layerM.layer`, compatibles avec le lecteur NRMODEL1 et le runtime FSwin existant. `NrRdna2FSwinChain::InitializeNativeSegment(model,plan,index)` les raccorde réellement à l'initialisation des couches GPU.
- **Fail-closed** pour les fenêtres de plus de 256 ; cette limite actuelle du runtime empêche encore les sections FSwin haute résolution. Les indices de grille natifs `gx/gy` sont conservés sans inventer de permutation d'axes.
- Un segment ne constitue pas un modèle complet. L'appelant ne doit pas ignorer les étapes disjointes ; les transitions de résolution, les branches de skip U-Net, ViT et les opérations sur images doivent encore être orchestrées.

## Tests

`test_rdna2_nr_native_plan_bridge.cpp` vérifie plusieurs lignes représentatives des plans amont, les exclusions de familles incompatibles, deux segments FSwin extraits, les décalages, les préfixes de poids, le rejet des très grandes grilles, la rétrocompatibilité du format à 19 colonnes et les refus de parsing malformé/dépendance invalide/ordre invalide.

Statut de validation : **test C++ inscrit au CTest**, pas de succès de CI attribué tant que la nouvelle branche n'a pas été compilée. La cible PS5 et les FPS restent non testés. 

## Suivi fonctionnel avant optimisation

Reste à porter le graphe global (plans de résolution et de skips), la couverture ViT / split-Swin et les couches pré/post image en conservant les sources de données réellement fournies par le renderer. Les optimisations de matrice, latence, compression spatiale ou cadence temporelle sont reportées après un premier rendu complet correct.
