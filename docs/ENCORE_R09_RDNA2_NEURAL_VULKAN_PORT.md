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
| attn.comp | Calcul du contexte d’attention 64×32 préprojeté RDNA2 ; QKV fusionnés manquants, famille **partielle** |
| vit_attn.comp | Première passe globale Q·K/P·V pour 32 têtes préprojetées, jusqu’à 2 048 tokens, précision différente de l’amont et non optimisée |
| ffwd3_t.comp | Première variante groupée 512→64→256→64 en trois étapes FP8 ; port de calcul de base, non équivalent aux variantes tuilées de production |
| decoder_upsample.comp | Première variante 2× à 512 canaux, projection FP16 + skip FP8 + gain FP16, sortie E4M3FN ; validée sur hôte, sans graphe |
| repack_tokens.comp | Primitive de permutation aller-retour RDNA2 intégrée en code et validée sur hôte ; pas encore de graphe de réseau |
| upsample_view.comp | Primitive RDNA2 de changement de vue intégrée en code et validée sur hôte, grille complète seulement |
| noise_field.comp | Port RDNA2 du générateur PCG/Box-Muller et empaquetage FP16 ; pas de graphe |

Le portage du graphe complet devra encore démontrer la validité des paramètres, la synchronisation des buffers GPU, les poids/modèles utilisables légalement et les entrées réelles couleur/profondeur/mouvement du jeu. Des centaines de calculs non matriciels par frame risquent de dépasser les budgets 30/60 FPS sur RDNA2. Seule une mesure sur la console peut trancher.

**État vérifiable : neuf primitives GPU Vulkan RDNA2 (projection 1×1, permutation des tokens, conversion de vue agrandie, bruit FP16, décodeur ×2 et contexte d’attention 64×32 préprojeté, projection QKV, FFWD3 groupé et contexte ViT global) intégrées en source et compilées/validées sur hôte ; aucune frame DLSS exécutée sur PS5.** Les trois modes A4K libres précédemment intégrés restent indépendants et ne sont pas remplacés.

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


## Quatrième primitive — champ de bruit pré-calculé RDNA2 (06/11)

Le shader `noise_field_rdna2.comp` porte le flux de bruit PCG +
Box–Muller MIT du pré-bloc `noise_field.comp` / `image_noise.glsl`.
Il calcule **trois caractéristiques par pixel**, avec le quatrième
canal à zéro, dans deux mots `uint32` empaquetant quatre FP16.

- Vulkan 1.1 de base : `packHalf2x16` remplace la dépendance
  `GL_EXT_shader_explicit_arithmetic_types_float16` du shader amont.
- Contrat host : dimensions de grille paddées 8×8, borne mémoire
  de 256 Mio, offsets en mots non débordants, amplitude finie,
  tailles exactes du descripteur et limite de dispatch.
- Wrapper C++ : pipeline, push constants 20 octets, enregistrement
  hors renderpass avec barrière `compute -> compute`.
- Précision : l'algorithme produit les mêmes échantillons théoriques ;
  l'égalité bit-à-bit sur GPU RDNA2 *n'est pas prouvée*, notamment
  à cause de l'implémentation des fonctions transcendantes.
- **Aucun passage réseau** n'appelle cette primitive pour le moment.
  Elle ne constitue pas une implémentation de l'attention, ni une
  preuve d'exécution DLSS PS5. Pas de poids NVIDIA intégrés.

Les familles `fswin_t`, `attn`, `vit_attn`, `ffwd3_t` restent non
portées. Le décodeur ×2 ajouté dans le lot suivant ne remplace pas
les autres variantes du réseau ; chaque primitive reste indépendante.


## Cinquième primitive — décodeur neuronal ×2 (06/11)

Le shader `decoder_upsample_rdna2.comp` reproduit la variante scalaire
MIT `decoder_upsample.comp` pour **512 canaux**, avec entrée projection
FP16, entrée résiduelle E4M3FN, gain FP16 et sortie quantifiée E4M3FN.
Les coordonnées utilisent les mêmes groupes de tokens 4×4 que l'amont.

- Pas de dépendance `shaderFloat8`, matrices coopératives ou
  `shaderFloat16` : lecture/arrondi FP16 via
  `unpackHalf2x16` / `packHalf2x16`, décodage et quantification FP8
  E4M3FN par calcul GLSL standard ; saturation à ±448.
- Un thread traite **4 canaux contigus** et écrit un mot `uint32`
  entier, évitant les courses de sous-octets. Dispatch 2D par pixel
  et par groupe de 4 canaux (128 groupes Y).
- Restriction vérifiée côté hôte : agrandissement **exactement ×2**,
  dimensions alignées 8 en sortie, tailles correctes de **3 buffers**
  distincts par contrat, sources skip/dst disjointes dans l'arène,
  adresses 32 bits et budget de 256 Mio.
- Wrapper Vulkan et branchement CMake natif compilables. Contrats
  et tests de référence des adresses/quantification exécutés sur hôte,
  validation SPIR-V/ABI exigée à la compilation.

**Non encore qualifié** : différences de précision GPU (arrondis FP16,
FP8 et fonctions mathématiques), coût GPU, modèles/poids, exécution de
la chaîne entière, mesures sur PS5. Les couches d'attention et FFWD
restent non portées ; aucun mode DLSS activé dans l'interface.


## Sixième primitive — attention fenêtrée 64×32 non fusionnée (06/11)

La première passe `window_attention_rdna2.comp` adapte les opérations
de contexte du shader MIT `attn.comp` :
- 64 tokens par fenêtre, 32 canaux par tête, 1/2/4/8/16 têtes.
- Trois flux E4M3FN **déjà projetés** Q/K/V ; Q/K supposés
  **déjà normalisés et pondérés**. Aucun calcul fusionné QKV.
- Produits scalaires Q·K en FP32, biais relatif `64×64` par tête,
  softmax stable (soustraction du maximum), quantification E4M3FN
  des probabilités, produit P·V en FP32, sortie E4M3FN.
- Buffer partagé (LDS) K et V de **16 Kio par groupe**, 64 lanes
  pour 64 queries ; chaque lane écrit 32 canaux et aucun octet
  de sortie ne partage son mot `uint32` avec une autre lane.
- 5 buffers storage + 28 octets de push constants. Dispatch
  `(1, têtes, fenêtres)` et barrière `compute→compute`.
- Contrat hôte : taille de chaque arène et des biais, offsets,
  budget max 256 Mio par tenseur, indexation `uint32`, nombre de
  têtes autorisé et limites des dimensions du dispatch.
- Tests : shader Vulkan 1.1 `spirv-val` + descripteurs ABI,
  référence C++ (probabilités 1/64, biais focalisé ±100, scores
  Q/K et saturation/arrondis FP8), syntaxe du wrapper Vulkan hôte.

**Limites importantes** : ce n'est pas encore le port complet de
`attn.comp` car la projection QKV (responsable de la majeure partie
de ses calculs) n'est pas fusionnée ni planifiée ; les biais/poids
ne sont pas fournis, la conversion de précision diffère de l'amont
(fast_exp/FP16), et aucun résultat/performance PS5 n'a été mesuré.
Un enregistrement de pipeline n'est pas une inférence complète.


## Septième primitive — projection QKV en Vulkan RDNA2 (6 novembre)

qkv_projection_rdna2.comp réalise le triplet des projections Q/K/V
du modèle MIT amont attn.comp sur les fenêtres de 64 tokens, en
FP32 FMA avec lecture E4M3FN logicielle, 512 canaux d'entrée,
32 par tête et jusqu'à 16 têtes.

- Q et K sont normalisés en norme L2 par token ; Q reçoit son facteur
  d'échelle par tête, puis les deux sont quantifiés E4M3FN après
  arrondis FP16 via packHalf2x16 / unpackHalf2x16.
- V passe par un arrondi FP16 suivi d'une quantification E4M3FN.
- Entrées explicitement **row-major** (pas le tiling amont), à
  adapter par un importeur de poids : activations [windows,64,512],
  poids [heads,3,32,512]. Sorties [windows,heads,64,32].
- 6 buffers storage, 32 octets de push constants, dispatch
  (windows,heads,64), contrôle des adresses 32 bits, mémoire et
  bornes de dispatch. Shader et wrapper C++ dans le vendor.
- Tests GPU hôte : compilation / validation SPIR-V, ABI ; référence
  CPU sur données synthétiques ; syntaxe du wrapper.

**Important :** QKV + attention sont encore deux dispatchs séparés
et ne reproduisent pas le kernel fusionné du réseau. Le regroupement
des poids au format correct, les modèles, le graphe et la qualification
des performances GPU PS5 sont non réalisés. Le coût scalaire de QKV
peut rendre le rendu temps réel impraticable sans optimisation.


## Huitième primitive — FFWD3 groupé RDNA2 (06/11)

ffwd3_group_rdna2.comp adapte le graphe mathématique de la famille
ffwd3_t.comp, en **un workgroup par token et groupe** :
- 8 groupes indépendants, avec 64 canaux de sortie par groupe.
- Étape 1 : projection FP8 512→64, accumulation FP32 et quantification.
- Étape 2 : projection 64→256 et activation cubique issue de
  swin_math.glsl, avec arrondis FP16 explicites et sortie FP8.
- Étape 3 : projection 256→64 et quantification FP8.
- Barrières entre les trois étapes ; mémoire locale des 64+256
  sorties intermédiaires. Aucun usage des matrices coopératives
  RDNA4 ni des extensions Vulkan FP8.
- Entrée/sortie 512 canaux **row-major** ; trois buffers de poids
  row-major distincts, incompatibles directement avec les poids
  tuilés amont sans import/repack fiable.
- Contrat d'allocation, offsets 32 bits, 5 bindings storage,
  24 octets de constantes, dispatch (tokens,8,1).
- Validation : SPIR-V Vulkan 1.1 et ABI, calcul CPU de référence
  avec trois poids non nuls et vecteur clairsemé, tests des
  limites et compilation syntaxique C++ du wrapper.

La version RDNA2 **n'est pas** le kernel WMMA fusionné exact :
les ordres d'opérations et arrondis ne sont pas tous équivalents,
les poids/modèles ne sont pas importés, et aucune mesure PS5 ne
démontre le temps réel. Il reste à porter fswin_t et vit_attn
et à concevoir le planificateur complet avec passes synchronisées.


## Neuvième primitive — ViT attention globale 32 têtes (06/11)

vit_attention_rdna2.comp adapte le cœur mathématique de
vit_attn.comp du réseau MIT : une attention globale non fenêtrée,
32 têtes de 32 dimensions (total 1 024 canaux). Entrées déjà
projetées, normalisées et pondérées Q/K, plus V, chacune en
row-major E4M3FN [tokens,heads,32] ; la sortie a la même structure.

- Un workgroup de 32 invocations traite 32 queries par tête
  dans un seul dispatch ; chaque invocation parcourt tous les tokens.
- Q·K accumule en FP32, puis applique la transformation exponentielle
  dérivée du demi-précision nr_vit_exp de swin_math.glsl.
- Le **dénominateur** somme l'exponentielle avant quantification ;
  le **numérateur** P·V reçoit les probabilités déjà quantifiées FP8.
  La sortie multiplie par 1/max(den, seuil) avec arrondis FP16.
- Quatre buffers storage, 20 octets de push constants.
  Contrôle hôte des allocations, offsets 32 bits/alignment,
  sortie non aliasée et **maximum de 2 048 tokens**. Dimensions de
  dispatch bornées, aucune extension coopérative ou shaderFloat8.
- Vérification : compilation Vulkan 1.1, validation SPIR-V/ABI,
  tests CPU de référence sur distribution uniforme, sélection par
  Q·K et cas mémoire, syntaxe C++ du wrapper.

**Limites :** ce port est un baseline scalaire en O(32 × T² × 32).
La réduction FP32 et les arrondis ne sont pas bit-identiques à
la réduction FP16 de l'amont. Les poids et tenseurs tuilés ne sont
pas importés, aucune frame DLSS n'est calculée sur console et
la faisabilité du temps réel n'a pas été démontrée. Une optimisation
par tuiles sera nécessaire avant d'envisager une activation runtime.
