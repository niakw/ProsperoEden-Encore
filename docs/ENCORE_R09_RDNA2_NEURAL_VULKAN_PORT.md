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
| fswin_t.comp | **Partiel** : phases denses (expansion, middle groupé, contraction, projection) ; restent QKV, chaînage des passes, entrées image et down/up |
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


## Adaptateur de poids — tuiles 16×16 vers row-major (06/11)

Le code partagé dans le vendor ajoute un convertisseur
**déterministe et sans quantification supplémentaire**
entre le format des blocs 16×16 E4M3FN de l'amont et le format
row-major attendu par les nouveaux shaders QKV/FFWD3.

La formule d'index tuilé, en éléments, est :
((row / 16) * (columns / 16) + col / 16) * 256 +
(row % 16) * 16 + col % 16.

Ce format correspond aux tuiles du shader MIT coopmm.glsl et
ffwd3_t.comp. Il **ne déduit pas** les autres formats INT4,
les métadonnées des modèles ou les textures d'entrée.
Sur des matrices E4M3FN déjà décompressées/décodées, la conversion
est byte-à-byte et bidirectionnelle.

- QKV : matrice [1536,512] ; FFWD3 : [512,512], [2048,64]
  et [512,256].
- Contrat C++ : dimensions multiples de 16, jusqu'à 256 Mio,
  capacités source/cible et rejet des plages aliasées.
  Aucune destination modifiée si la validation échoue.
- Tests CPU : aller/retour bit-exact, indexation des coins de
  tuiles et cas limites sur QKV, FFWD3 et un tenseur ViT.

Aucune conversion de poids n'est **encore invoquée au runtime** :
un importeur de modèles doit la déclencher avant l'inférence GPU.
Le convertisseur ne rend pas à lui seul les modèles NVIDIA compatibles.


## Dixième primitive — noyau dense FSwin RDNA2

Le shader fswin_dense_rdna2.comp porte quatre étapes denses
de fswin_t.comp MIT en Vulkan 1.1 sans matrices FP8 : expansion
C→4C avec activation cubique, produit block-diagonal par tête
128→32, contraction C→C avec résidu pondéré rs[C], et projection
post-attention avec résidu ars[C].

C=32/64/128/256, 64 tokens par fenêtre, matrices E4M3FN
row-major. Quatre dispatchs distincts, barrières compute→compute,
5 buffers et 32 octets de constantes. Contrat hôte
FSwinDense et wrapper NrRdna2FSwinDense.

Les shaders et wrappers ont passé SPIR-V, ABI, test CPU et syntaxe
C++ sur hôte avant publication. **Ce n'est pas fswin_t complet** :
QKV, variantes image, downsample/upsample, import de modèles
et planificateur du réseau restent à relier. Pas de performance
PS5 ou de rendu DLSS revendiqués.


## Onzième primitive — QKV FSwin à largeur variable

Un nouveau shader fswin_qkv_rdna2.comp réutilise les formules
de la projection Q/K/V déjà présente et accepte désormais
C=32/64/128/256, avec C/32 têtes de 32 caractéristiques.
L'entrée row-major est [window,token,C], les poids E4M3FN
sont [head,Q/K/V,32,C] et les sorties Q/K/V restent au format
[window,head,token,32] du shader window_attention_rdna2.comp.

Le port exige des bornes mémoire et des buffers distincts,
ainsi qu'une mise à l'échelle par tête. Contrat validé
CanFSwinQkv et dispatch (windows,heads,64), wrapper Vulkan
NrRdna2FSwinQkv. Cette variante doit être compilée et
validée numériquement sur GPU avant intégration finale.


## Six passes FSwin — enregistrement ordonné côté renderer (06/11)

Le nouveau wrapper NrRdna2FSwinGraph enregistre jusqu'à six passes
via le scheduler Vulkan, avec une barrière compute→compute
après chacune :

1. FSwinDense stage 0 — expand et activation.
2. FSwinDense stage 1 — middle groupé.
3. FSwinDense stage 2 — contract et résidu.
4. FSwinQkv — projections Q/K/V normalisées.
5. WindowAttention — logits, biais, Softmax, P×V.
6. FSwinDense stage 3 — projection finale et résidu.

Le contrat FSwinGraph vérifie avant le premier enregistrement
les 4 demandes denses, les dimensions partagées (fenêtres,
canaux, têtes), les tailles QKV/attention et les limites.
Record rejette tout descriptor set nul avant d'émettre une commande.

**Limite d'intégration** : le renderer doit fournir les ressources
réelles, les poids, leurs constantes, leur durée de vie et les
bindings producteurs-consommateurs corrects. Le wrapper n'alloue
pas encore les tenseurs et ne lit pas les conteneurs de modèles.
Ce chemin constitue l'orchestration interne d'un bloc FSwin,
pas le graph neural complet ni un mode DLSS actif.


## Lecteur de paquets de modèle NRMODEL1

Le fichier header partagé nr_rdna2_model_pack.h lit l'index
du format documenté par pack_model.py (projet MIT DLSSNR-AMD) :
8 octets NRMODEL1, compte u32, réservé u32, puis par entrée
longueur de nom, nom relatif UTF-8, offset u64, taille u64.
Les payloads sont alignés sur 256 octets.

Le parseur accepte un **index partiel** fourni séparément de la
taille totale du fichier. Il vérifie le magic, les bornes,
les noms relatifs, les doublons, l'alignement, les chevauchements
et le dépassement de capacité. Il n'ouvre aucun fichier arbitraire,
ne charge pas les poids en mémoire, ne décompresse pas INT4 ou FP8,
et ne distribue pas les poids NVIDIA.

Test C++ dédié : paquet synthétique à deux matrices, corruption
de l'en-tête, doublons, traversal, offsets non alignés et hors limites.
Cette étape rend possible un futur chargeur réel, sans être déjà
ce chargeur. Aucune activation automatique de DLSS.


## Import local des poids NRMODEL1

Le header vendor nr_rdna2_model_file.h complète l'index sécurisé :
NeuralModelFile::Open lit uniquement un préfixe d'index limité,
NeuralModelFile::LoadRaw charge à la demande le poids nommé en
vérifiant l'étendue, et LoadModelMatrix conserve une matrice E4M3FN
**déjà row-major**, exactement comme dans NRMODEL1. LoadTiledMatrix
ne convertit que des données explicitement tuilées.

Le modèle doit être fourni **localement et légalement** : aucun
poids NVIDIA n'est inclus ou distribué. Un chargement n'est pas
possible lorsque le paquet manque ou lorsque la taille de fichier
a changé après l'indexation.

Test d'intégration : génération d'un paquet temporaire NRMODEL1,
lecture exacte d'une matrice row-major synthétique 16×32,
fichier, refus de matrices mal dimensionnées, chemins absents et
troncature après ouverture. L'étape upload Vulkan, la vérification
SHA-256 des poids et la connexion automatique au graphe restent à
implémenter.


## Arène d'upload des poids (préparation mémoire CPU)

Le module vendor nr_rdna2_weight_arena.h associe au chargeur
NRMODEL1 un espace contigu de poids lus à la demande et
convertis, avec offsets alignés à 256 octets et budget 256 Mio.
AppendModelMatrix conserve les matrices NRMODEL1 row-major ;
AppendTiled sert aux sources qui sont explicitement tuilées, et
AppendRaw conserve les constantes et poids non matriciels.
Les offsets/longueurs sont conservés en u32 pour la future
création des buffers Vulkan. Les noms dupliqués sont rejetés.

Test intégré : paquet temporaire, conversion 16×32 exacte,
contrôle des offsets et de l'absence de doublons, test RAW,
remise à zéro. Le matériel PS5 ne reçoit encore aucun buffer ;
cette arène est uniquement la préparation CPU. Le chargeur
actif de modèle et les descripteurs GPU restent à finaliser.


## Audit d'intégration : format réel des poids et FSwin C32

La lecture du code amont MIT nr_graph.cpp montre que les fichiers
NRMODEL1 contiennent les matrices E4M3FN **en lignes originales** :
le host d'origine appelle tin::tile_blocked seulement après
lecture, pour son propre stockage GPU. Pour notre chemin RDNA2
row-major, cette transformation ne doit pas être appliquée.
LoadModelMatrix et AppendModelMatrix assurent maintenant une
lecture byte-identique et contrôlent la forme.

Autre différence fonctionnelle importante : au niveau C=32,
FSwin a une seule tête et **aucune couche middle**. Son
contraction lit les 4C=128 canaux cachés directement
après l'expansion. Pour C>=64 le middle groupé 128→32
reste nécessaire. Le graph recorder saute donc le stage 1
à C32 : cinq dispatchs au lieu de six.
Les contrats, tailles, tests et documentation sont alignés.

L'ordre des poids QKV amont reste [head, Q/K/V, 32, C],
cohérent avec les accès du port FSwin QKV. Les conversions
FP16 originales des biais/scales et les formats de pré/post
image restent à valider sur des poids réels.


## Conversion FP16 des paramètres du modèle

Le header vendor nr_rdna2_weight_decode.h adapte les poids
aux paramètres réellement utilisés par les shaders RDNA2 :

- Décodage little-endian FP16 vers FP32, avec rejet des NaN
  et valeurs infinies dans les buffers de paramètres.
- Désentrelacement du biais d'attention 64×64 par tête suivant
  la permutation NVIDIA documentée dans le code MIT amont
  nr_graph.cpp (fonction deswizzle_bias). La sortie correspond
  directement aux indices bias[head][query][key] du shader RDNA2.
- Extraction des C coefficients résiduels : détection des huit
  zéros de padding facultatifs et prise en charge des régions
  non paddées, dont l'alternative de lecture finale.

Ces opérations sont des conversions de données, **pas des
optimisations de performance**. Les tests hôte couvrent les
valeurs FP16 normales/subnormales, les cas non finis, la
permutation complète des 4096 éléments et les échelles C32/C64.
Les valeurs en FP32 sont encore à placer dans l'arène d'upload
et à associer aux descripteurs Vulkan du graphe.


## Correction QKV et raccordement des poids (06/11)

Le modèle NRMODEL1 contient QKV dans l'ordre de lignes
[Q(C),K(C),V(C)], alors que le kernel FSwin RDNA2 lit les poids
dans l'ordre [head,Q(32),K(32),V(32)]. Le chargeur FSwin applique
maintenant cette permutation, sans modifier les valeurs E4M3FN.
Le test de permutation a été compilé et exécuté localement pour
C=32, 64, 128 et 256.

BindFSwinGraphWeights relie les offsets de l'arène de poids
aux constantes du graphe FSwin : expand, middle éventuel,
contract, QKV, projection, biais, résidus et échelles Q/K.
Il contrôle les tailles exactes, les alignements 256 octets,
les limites mémoire et les chevauchements des plages. En cas
d'échec, le plan d'entrée n'est pas modifié.

Les tests de contrat sont enregistrés en CMake. Cette étape
prépare la lecture des bons poids sur le GPU, mais elle ne
crée pas les buffers Vulkan, ne les peuple pas et ne branche
pas encore les descripteurs. Le rendu DLSS de bout en bout
reste non validé, sans priorité donnée aux performances.


## Premier buffer GPU de poids initialisable

NrRdna2GpuWeights crée désormais, via l'allocateur VMA natif
d'Eden, un buffer Vulkan STORAGE_BUFFER depuis les octets
de l'arène CPU. La copie est synchrone vers une zone
host-visible avec Flush(), avant la première soumission GPU.
La taille est contrôlée (alignement 4, limite 256 Mio,
et maxStorageBufferRange du périphérique).

Le buffer ne peut être initialisé qu'une fois et fournit
un VkDescriptorBufferInfo. Cette première implémentation
utilise MemoryUsage::Upload ; son efficacité n'est pas
encore à examiner. Un test de compilation et exécution
avec doublures Vulkan vérifie le contrat du wrapper,
mais ce n'est pas un test PS5 ou pilote réel.

**Restent** l'allocation et l'écriture des six descripteurs
FSwin, les buffers de tenseurs d'activation, les entrées
image, les modèles complets et le graphe réseau global.
Le buffer de poids doit rester vivant jusqu'à la fin
des commandes GPU qui le lisent.


## Descripteurs Vulkan du bloc FSwin

NrRdna2FSwinDescriptors alloue désormais six ensembles de
descripteurs de stockage via le pool Vulkan natif d'Eden :
quatre ensembles pour les stages denses, un pour QKV et un
pour l'attention fenêtrée. Le stage 1 C32 est volontairement
omis et ne reçoit aucune écriture de descripteurs.

Les entrées/sorties sont reliées dans l'ordre :
input -> expanded -> middle (C>=64) -> contracted -> Q/K/V ->
context -> output. Le buffer de poids fourni par
NrRdna2GpuWeights est partagé en lecture seule par les
projections, les échelles et les biais, avec les offsets
validés par BindFSwinGraphWeights.

Les contrôles refusent les handles nuls, les aliasings entre
tenseurs, les offsets de descripteur non nuls, les plages
hors capacités et les dimensions incorrectes. La fonction
Initialize écrit effectivement les VkWriteDescriptorSet
dans le contexte du VkDevice existant.

**Limite :** les buffers d'activation sont encore fournis
par le moteur appelant et aucun passage PS5 complet
n'a été exécuté. Les nouveaux wrappers Vulkan n'ont
pas encore été compilés contre un SDK PS5 lors de ce lot.


## Allocation des tenseurs intermédiaires FSwin sur Vulkan

Le nouveau composant NrRdna2FSwinGpuTensors alloue, avec
l'allocateur VMA d'Eden, les buffers GPU nécessaires à un
bloc FSwin : entrée, expansion, middle facultatif (C>=64),
contraction, Q, K, V, contexte d'attention et sortie.

L'entrée est host-visible et accepte les tokens E4M3FN via
UploadInput(), avec Flush() avant la soumission GPU. Les
intermédiaires sont en mémoire locale du périphérique,
avec des tailles dérivées du contrat FSwinGraph. Chaque
allocation respecte maxStorageBufferRange et le budget
global de 512 Mio fixé pour cette étape.

Views() construit les VkDescriptorBufferInfo réels et
peut les transmettre à NrRdna2FSwinDescriptors en lui
fournissant le buffer poids. Les ressources doivent
survivre aux commandes GPU qui les emploient.

Il manque toujours le pilotage automatique d'une
couche par le renderer, le prétraitement image vers
tokens FP8 et le plan global des blocs. Il n'y a
encore aucune validation de frame DLSS sur console.


## Exécution intégrée d'une couche FSwin

NrRdna2FSwinLayerRuntime regroupe maintenant les opérations
auparavant isolées :
- MakeFSwinGraphPlan calcule les formes des buffers
  et le plan des 5 passes (C32) ou 6 passes (C>=64).
- PrepareFSwinLayerWeights lit les matrices et constantes
  d'un NRMODEL1 fourni localement.
- BindFSwinGraphWeights valide et affecte les offsets
  de l'arène de poids aux passes.
- NrRdna2GpuWeights copie la mémoire CPU vers un buffer VMA.
- NrRdna2FSwinGpuTensors alloue les tenseurs GPU.
- NrRdna2FSwinDescriptors relie les buffers aux pipelines.
- UploadInput et Record permettent ensuite de soumettre
  une couche FSwin complète sur le scheduler Vulkan.

Le test de génération du plan couvrant C=32/64/128/256
et 1/16/256 fenêtres est enregistré. Une version pure
du générateur a été compilée et exécutée en test hôte.

L'entrée acceptée reste un **tenseur E4M3FN déjà
prétraité en fenêtres de 64 tokens**. Le code ne
convertit pas encore une image source en ce tenseur et
n'enchaîne pas les couches du graphe global. Le nouveau
chemin n'a pas encore produit de frame sur GPU PS5 ;
la performance sera étudiée seulement après cette
intégration complète.


## Enchaînement de plusieurs couches FSwin compatibles

NrRdna2FSwinLayerRuntime::LinkInputFrom enregistre une
copie Vulkan TRANSFER de la sortie du bloc précédent vers
l'entrée du suivant, avec barrières COMPUTE->TRANSFER
et TRANSFER->COMPUTE. Les formats de tenseur doivent
coïncider et les deux blocs partager le même scheduler.

NrRdna2FSwinChain instancie plusieurs runtimes FSwin
successifs à partir d'un paquet NRMODEL1 fourni par
l'utilisateur et de préfixes de couches. Il ne permet
que des couches de **mêmes canaux et mêmes fenêtres**
pour ne pas déduire incorrectement une transition de
résolution. Les ressources restent sur GPU entre passes.

**Ce n'est pas encore le graphe complet du modèle** :
les fenêtres décalées, les changements de résolution,
les blocs ViT, les opérations pré/post image, les
branches U-Net et le planificateur global restent
à raccorder. L'implémentation n'a pas été exercée
sur GPU PS5 ; on reporte la performance jusqu'à
la fin de l'intégration fonctionnelle.


## Requantification des poids E4M3FN à l'import

Dans le projet amont MIT, le chargement des matrices
applique f_to_e4m3(e4m3_to_f(code)) avant leur stockage.
L'audit exhaustif des 256 codes montre deux exceptions
à l'identité : 0x00 devient 0x80 (zéro négatif), et 0xff
devient 0x7f (NaN canonique positif).

Le chargeur FSwin applique désormais exactement cette
normalisation sur expand, middle, contract, QKV et projection,
avant la permutation des têtes QKV et avant l'upload Vulkan.
Les matrices NRMODEL1 restent en row-major à la lecture.

Le test de correspondance exhaustive des 256 codes a été
compilé et exécuté localement ; il est inscrit à CTest.
La parité numérique des kernels GPU et le rendu console
restent à vérifier lors de la validation fonctionnelle.


## Port du changement de fenêtre FSwin

Le noyau fswin_window_repack_rdna2.comp adapte les fenêtres
8×8 tokens E4M3FN entre décalages de 4×4 pixels sur X et Y,
en conservant les tenseurs sur GPU. Chaque fenêtre se compose
de quatre tuiles 4×4. Les régions hors du raster sont remplies
avec des zéros E4M3. Les offsets suivent les coordonnées du
shader MIT amont fswin_body.glsl.

Contrat GPU : 2 buffers storage, 28 octets de constantes,
local_size_x=64 et un dispatch borné. Contrat hôte : jusqu'à
256 fenêtres, C32/C64/C128/C256, offsets de shifts -1 à +1,
sorties disjointes. Référence de test CPU : identité sans
décalage, cycle shift aller-retour à l'intérieur du raster.

Le wrapper Vulkan est ajouté au build. Il reste à raccorder
sa ressource de descriptor set et ses appels dans la chaîne
multi-couches en fonction des décalages réels du plan source.
Aucune performance n'a été évaluée.

## Chaînage FSwin avec fenêtres décalées — 06/11/2026

La chaîne `NrRdna2FSwinChain` intègre désormais le shader Vulkan
`fswin_window_repack_rdna2.comp` entre **deux couches consécutives
de même résolution et même nombre de canaux**, lorsque leur disposition
de fenêtres (décalage X/Y) diffère.

- Chaque `FSwinLayerSpec` peut spécifier `layout={windows_x,windows_y,
  shift_x,shift_y}`, avec les décalages mesurés en tuiles de 4×4
  tokens (plage -1 à 1).
- Pour un chemin purement non décalé, l'ancien appel avec `layout={}`
  reste accepté ; la copie TRANSFER précédente est conservée.
- En cas de décalage, une paire de descripteurs storage est allouée
  par transition. Le shader lit le buffer de sortie de la couche
  précédente et écrit directement dans le buffer d'entrée de la
  couche suivante ; il insère sa barrière compute→compute.
- Le nouveau contrat `CanFSwinChainWindowLayouts` vérifie
  avant l'allocation GPU l'homogénéité des dimensions de grille,
  le produit `windows_x×windows_y=windows`, les décalages supportés
  et la limite de 160 couches.
- Les passages `LinkInputFromShifted` conservent les contrôles
  de durée de vie, de scheduler commun, de taille d'entrée/sortie
  et d'absence d'alias. Les états `input_loaded` et
  `output_recorded` restent liés à la réussite de l'enregistrement.
- La validation host ajoute un test de géométrie des séquences
  de layouts alternés, des cas 1×1/16×16 et des refus hors bornes.
  Le shader de décalage possédait déjà son test de correspondance
  de tokens et son validateur SPIR-V.

**Limites fonctionnelles :** le chargeur externe doit toujours
fournir le plan de fenêtres réel de chaque couche ; les dimensions
doivent rester identiques d'un bout à l'autre de la chaîne. Cette
étape ne porte ni les changements de résolution, ni les branches
U-Net, ni les blocs ViT du réseau global, ni les entrées/sorties
d'images. Les nouveaux appels Vulkan n'ont pas été exécutés sur PS5
et aucun chiffre de performance n'est revendiqué.


## Conversion réversible d'un raster de caractéristiques en fenêtres FSwin (06/11)

Le shader Vulkan fswin_raster_layout_rdna2.comp passe entre
un raster E4M3FN [H,W,C] et les fenêtres 8×8 du réseau
[fenêtre,quadrant 4×4,token,C], sans toucher aux valeurs FP8.

- Mode pack : lecture raster, remplissage zéro des pixels
  hors image dans les fenêtres de bord.
- Mode unpack : restitution des pixels valides, padding ignoré.
- Contrat C32/64/128/256, max 256 fenêtres, descripteurs
  storage non aliasés, étendues CPU vérifiées avant Record.
- Wrapper Vulkan NrRdna2FSwinRasterLayout, 24 octets de
  push constants et compilation/validation SPIR-V au build.
- Test CPU aller-retour exact sur 24 géométries/canaux et
  vérifications de bornes des buffers.

Cette passerelle attend toujours un **raster de caractéristiques
E4M3FN déjà encodées** et non des pixels RGB(A) directement.
La transformation n'est pas encore branchée automatiquement à
l'entrée/sortie globale du modèle. Prétraitement couleur,
U-Net/ViT, transitions de résolution et validation console
restent nécessaires. Aucun benchmark n'a été effectué.


## Entrée raster de caractéristiques vers la chaîne FSwin

La méthode `NrRdna2FSwinChain::UploadRasterFeatures`
permet maintenant de transmettre à la première couche FSwin un
raster `[H,W,C]` **déjà encodé en E4M3FN**. Une conversion CPU
exacte range les pixels en fenêtres 8×8, remplit les frontières
incomplètes avec zéro, puis réutilise le chemin d'upload existant
`UploadInput`.

- Le contrat impose les dimensions de fenêtre déclarées dans
  `FSwinLayerSpec::layout` pour la première couche ; ce layout
  doit avoir un décalage initial nul. Les grilles implicites
  ne sont pas acceptées pour cette nouvelle API.
- L'utilitaire `nr_rdna2_fswin_raster_host.h` propose aussi
  `UnpackFSwinFeatureRaster`, réversible pour tous les pixels
  valides, sans ré-quantification des octets.
- Tests hôte : 24 géométries/canaux, bords hors raster,
  équivalence octet-à-octet, source/destination éventuellement
  aliasées, erreurs de forme et de longueur.

Ce chemin privilégie la **fonctionnalité**. Il n'est pas une
optimisation : il effectue un pack CPU pour l'upload de features
déjà produites. La fabrication de ces features à partir de la
couleur réelle du jeu, la reconstruction finale en pixels et le
graphe complet du réseau restent non intégrés.
