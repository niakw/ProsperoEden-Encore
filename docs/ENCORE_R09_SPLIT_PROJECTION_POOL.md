# Eden Encore — R09 : Split-Swin ProjPool avec seconde sortie GPU

6 novembre 2026 — PR #24, portage fonctionnel sans optimisation.

## Source et calcul des valeurs

La couche native `CCSplitSwin16HProjPool` exige **deux sorties distinctes** :
1. La projection résiduelle E4M3FN normale (déjà calculée par `NrRdna2SplitResidualProjection`).
2. Une sortie demi-résolution produite par **pooling 2×2 sur les résultats FP16 de la projection résiduelle, AVANT quantification E4M3FN**, et non sur la sortie quantifiée.

Le second résultat est maintenant généré par `NrRdna2SplitProjectionPool`, utilisant **le scratch GEMM FP32 existant**, la branche résiduelle FP8 et les **mêmes 512 coefficients FP16** de la projection principale. Pour chaque canal et chaque source valide : `v = half(half(gemm_fp32) + half(gain_fp16 × residual_fp8))`. Pour le 2×2 : `pool = half(half(half(v00 + v01) + half(v10 + v11)) × 0.25)`, puis conversion en E4M3FN. Aucun GPU→CPU, aucun poids supplémentaire, aucun opérateur fictif.

La disposition des fenêtres RDNA2 existante est `[window8×8][quadrant TL/TR/BL/BR][slot4×4][512]` : elle est dérivée du kernel `fswin_raster_layout_rdna2.comp`. La sortie poolée suit le véritable ordre **4×4 tile-major**, avec géométrie `pad4(ceil(width/2)) × pad4(ceil(height/2))`. Le shader écrit aussi **zéro** dans tous les pixels paddés, puis dans les tokens de fin explicitement demandés par le consommateur ; il ne laisse aucune ancienne valeur de la mémoire GPU.

### Cas natif 1080p

- Entrée valide : 60×33 pixels de 512 canaux, stockée dans 8×5 fenêtres de 8×8 (40 fenêtres et 2 560 tokens).
- Sortie demi-résolution valide : 30×17 pixels.
- Allocation 4×4 paddée : **32×20 = 640 tokens**.
- Le `FinalHead` natif 1080p, sur le chemin amont par défaut sans `--tiles-up` ni `--tiles-win`, demande **1 920 tokens** : les 1 280 tokens supplémentaires sont explicitement écrits à zéro si l'appelant indique `output_tokens=768`.

### Code et qualification

- `nr_rdna2_split_projection_pool.cpp` enregistre le shader Vulkan 1.1, 4 STORAGE_BUFFER, 36 octets de push constants, dispatch par token de sortie, et barrière compute→compute.
- `NrRdna2SplitSwinBlock` accepte maintenant `has_pooled_projection=true` avec `pool_width,height,windows_x,y,output_tokens` et un 11ᵉ buffer `pooled`, dont la capacité et l'absence d'alias sont vérifiées. Le bloc enregistre exactement `Proj` puis `ProjPool` sur le même scheduler.
- `CanSplitProjectionPool` valide les dimensions, les arrondis, les limites 32 bits, les capacités et les éventuels tokens supplémentaires.
- `test_rdna2_nr_split_projection_pool_policy` vérifie la bijection du mapping source 64×40→fenêtres, la bijection de 32×20→tuiles, les pixels de bord, le zéro de remplissage et toutes les capacités. `test_rdna2_nr_split_block_policy` vérifie aussi le ProjPool complet.
- `test-rdna2-split-projection-pool-spv.py` est raccordé à la génération native : validation SPIR-V Vulkan 1.1, bindings 0/1/2/3 et 9 push constants.

## Ce que ce lot ne valide pas

Il ne constitue pas encore une traversée des **65 opérations Split-Swin Original / 17 Compact**, car il manque l'ordonnancement multi-blocs, les relations inter-étages FSwin/U-Net, la synchronisation des fenêtres déplacées et la sortie renderer. Aucune compilation Vulkan ni exécution sur GPU/PS5 n'est prouvée par la présence des fichiers CMake. L'égalité numérique avec la capture amont doit être mesurée ; les détails de réduction et de conversion peuvent encore différer.

Références MIT : `Overclockers/DLSSNR-AMD/linux/shaders/rdna4/gemm1x1.comp` (`NR_POOL`), `linux/src/core/nr_graph.cpp` (`CCSplitSwin16HProjPool`).


### Correction de domaine (même journée)

Les plans capturés peuvent afficher 2 560 tokens de fenêtres, alors que le `FinalHead` amont exécute par défaut sur les tuiles **tronquées** : `tiles_of(60)=15`, `tiles_of(33)=8` et `M=15×8×16=1 920`. La projection poolée écrit 640 tokens, puis le buffer doit contenir **1 280 tokens à zéro** pour garantir les lectures suivantes dans cette variante. Le commentaire historique de l'amont mentionnant «768 at 1080p» n'est pas cohérent avec cette géométrie courante ; on retient les expressions réellement exécutées dans `nr_graph.cpp`. Les autres résolutions se calculent depuis leurs dimensions, **jamais avec une constante 1 920 codée en dur**. Le contrat `output_tokens` reste paramétrique.
