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

## Deuxième primitive : réorganisation réversible des tokens

Le shader **repack_tokens_rdna2.comp** adapte la disposition des tokens
du shader MIT repack_tokens.comp de
[Overclockers/DLSSNR-AMD](https://github.com/Overclockers/DLSSNR-AMD).
Le vendor conserve la notice MIT complète. Le kernel déplace
sans calcul flottant les données E4M3FN par blocs uvec4 de 16 octets,
entre l'ordre raster et l'ordre des tuiles 4×4 du réseau.

- Contrat hôte : dimensions multiples de 4, canaux multiples de 16,
  offsets alignés, espaces sans chevauchement, transfert <=256 Mio
  et adresses validées en 64 bits.
- Test hôte : raster -> tuiles -> raster byte-identique, rejets
  des dimensions/offsets/plages invalides.
- SPIR-V Vulkan 1.1 validé, ABI 1 storage-buffer et 24 octets de
  push constants, capability Shader uniquement, aucune extension
  FP8, shaderInt8, ni matrice coopérative.
- Wrapper C++ NrRdna2TokenRepack connecté au scheduler Vulkan ;
  non appelé dans les jeux faute de planificateur des couches.

## Troisième primitive : changement de vue après agrandissement

Le shader **upsample_view_rdna2.comp** reprend les coordonnées et
les réinterprétations de tokens du shader MIT upsample_view.comp.
Les pixels du tenseur source sont lus par blocs de 16 octets, avec
un éventuel changement de plan de canaux dû au padding de la grille
raster. Une valeur nulle est écrite quand le plan source déborde.
La source est dans le vendor, avec la notice MIT amont.

La première version demande une **vue complète de la grille
agrandie** (nombre de tokens = largeur × hauteur agrandies, dimensions
multiples de quatre) et un espace source distinct de la destination,
aligné et borné à 256 Mio. Cette restriction conserve un contrat
d'accès prouvable sans deviner les sous-vues du planificateur futur.

Le module Vulkan 1.1 compile sans FP8 ni coopérative ; son ABI a un
storage buffer et 32 octets de push constants. Le test CPU contrôle
le transfert bit-à-bit pour une grille sans padding et le comportement
d'une grille paddée avec canaux traversants et zéros de bord, ainsi
que les refus d'offsets et dimensions dangereux. Le wrapper C++
**NrRdna2UpsampleView** utilise le scheduler GPU du moteur.
Pas de dispatch depuis les jeux faute de modèle complet.

## Couverture réelle : 9 familles du manifeste Vulkan amont

| Famille d'origine | État du port RDNA2 |
|---|---|
| gemm1x1.comp | Produit matriciel de base Vulkan RDNA2 développé ; famille complète non terminée |
| fswin_t.comp | Non porté |
| attn.comp | Non porté |
| vit_attn.comp | Non porté |
| ffwd3_t.comp | Non porté |
| decoder_upsample.comp | Non porté |
| repack_tokens.comp | Primitive de permutation aller-retour RDNA2 intégrée en code et validée sur hôte ; pas encore de graphe de réseau |
| upsample_view.comp | Primitive RDNA2 de changement de vue intégrée en code et validée sur hôte, grille complète seulement |
| noise_field.comp | Non porté |

Le portage du graphe complet devra encore démontrer la validité des paramètres, la synchronisation des buffers GPU, les poids/modèles utilisables légalement et les entrées réelles couleur/profondeur/mouvement du jeu. Des centaines de calculs non matriciels par frame risquent de dépasser les budgets 30/60 FPS sur RDNA2. Seule une mesure sur la console peut trancher.

**État vérifiable : trois primitives GPU Vulkan RDNA2 (projection 1×1, permutation des tokens, conversion de vue agrandie) intégrées en source et compilées/validées sur hôte ; aucune frame DLSS exécutée sur PS5.** Les trois modes A4K libres précédemment intégrés restent indépendants et ne sont pas remplacés.

## Nouveaux dépôts utiles, examinés le 6 novembre

- [Recol/DLSS-Updater V5.2.0](https://github.com/Recol/DLSS-Updater/releases/tag/V5.2.0)
  annonce FSR 4.1.2, FSR Frame Generation 4.0.2,
  chargeur Vulkan et RDNA2 ; projet utile pour la gestion des DLL,
  versions, sauvegardes et retours arrière. **Ce n'est pas un
  backend DLSS Neural Rendering** : rien à charger directement
  dans le moteur PS5.
- [artur-graniszewski/DLSS-Enabler](https://github.com/artur-graniszewski/DLSS-Enabler)
  se base sur OptiScaler et redirige des interfaces NGX DLSS vers
  FSR/XeSS sur DirectX. Utile pour la logique d'interface et
  de fallback, mais les DLL DirectX Windows ne sont pas portables
  sur PS5 et n'exécutent pas magiquement le modèle NR NVIDIA.

Aucun de ces deux dépôts ne rend disponible le graphe complet de
Neural Rendering sur RDNA2/PS5. Ne pas ajouter de fausse option DLSS.
