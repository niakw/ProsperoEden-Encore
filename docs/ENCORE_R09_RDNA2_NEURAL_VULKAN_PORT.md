# Eden Encore — R09 : portage DLSS Neural Rendering vers RDNA2

**6 novembre 2026 — PR #24 en brouillon — aucun DLSS opérationnel en jeu.**

## Sources vérifiées

Le dépôt MIT [Overclockers/DLSSNR-AMD](https://github.com/Overclockers/DLSSNR-AMD) publie les sources Vulkan (architecture et manifeste de pipelines). Son réseau comprend environ **150 couches successives** et **9 familles de shaders**. Le backend existant dépend des matrices coopératives FP8 de RDNA4, indisponibles sur la PS5 RDNA2.

Le mod [danielblnc/DLSS-NR-on-AMD](https://github.com/danielblnc/DLSS-NR-on-AMD) annonce un fonctionnement expérimental sur RX 6000 avec HIP 7.2 sous Windows/D3D12. Il ne publie pas les noyaux HIP utilisés et interdit leur redistribution/modification sans autorisation. Le runtime HIP Windows ne se charge pas sur PS5.

## Primitive RDNA2 effectivement développée

Le vendor contient désormais le shader Vulkan 1.1 fp8_proj_rdna2.comp et le wrapper C++ NrRdna2Projection. Il calcule une projection matricielle **C[M,N] = A[M,K] × W[N,K] transposé**, avec deux entrées E4M3FN octet packé, accumulation FP32 et sortie FP32. Il utilise des tuiles de mémoire partagée 16×16 et ne demande ni CUDA/HIP, ni instructions FP8, ni matrices coopératives.

- Le compilateur hôte génère un module SPIR-V et un tableau de code C++ ; l'ABI vérifie les trois bindings storage-buffer, 32 octets de constantes et les seules capacités SPIR-V Shader.
- Un contrat C++ indépendant valide les dimensions, les pas de ligne, les tailles des buffers, la mémoire temporaire, les limites de dispatch et l'absence de dépassement d'adresse uint32.
- Le wrapper C++ sait préparer le pipeline Vulkan et enregistrer un dispatch dans le scheduler du moteur avec barrière mémoire de sortie. Il exige un jeu de descripteurs dont un futur planificateur assure la validité et la durée de vie.
- Tests hôte effectués : compilation GLSL, spirv-val, interface SPIR-V, compilation syntaxique C++ native, calcul de référence CPU E4M3FN et cas limites mémoire.

**Ce n'est pas encore la totalité de la famille de kernels GEMM.** Les opérations résiduelles, activations, quantification/format de sortie du vrai graphe et variantes d'architecture ne sont pas raccordées. Aucun modèle neuronal NVIDIA ni ses poids ne sont inclus. Aucun nouveau mode DLSS n'apparaît dans le menu.

## Couverture réelle : 9 familles du manifeste Vulkan amont

| Famille d'origine | État du port RDNA2 |
|---|---|
| gemm1x1.comp | Produit matriciel de base Vulkan RDNA2 développé ; famille complète non terminée |
| fswin_t.comp | Non porté |
| attn.comp | Non porté |
| vit_attn.comp | Non porté |
| ffwd3_t.comp | Non porté |
| decoder_upsample.comp | Non porté |
| repack_tokens.comp | Non porté |
| upsample_view.comp | Non porté |
| noise_field.comp | Non porté |

Le portage du graphe complet devra encore démontrer la validité des paramètres, la synchronisation des buffers GPU, les poids/modèles utilisables légalement et les entrées réelles couleur/profondeur/mouvement du jeu. Des centaines de calculs non matriciels par frame risquent de dépasser les budgets 30/60 FPS sur RDNA2. Seule une mesure sur la console peut trancher.

**État vérifiable : une primitive GPU de projection intégrée en source et compilée/validée sur hôte ; aucune frame DLSS exécutée sur PS5.** Les trois modes A4K libres précédemment intégrés restent indépendants et ne sont pas remplacés.
