# R09 — audit de couverture des plans neuraux Original et Small

Corpus structurels MIT, issus de [Overclockers/DLSSNR-AMD](https://github.com/Overclockers/DLSSNR-AMD) : `nr_native_plan_data.hpp` (152 lignes) et `nr_native_plan_data_small.hpp` (76 lignes). Les fichiers `extras/graphics/fixtures/r09_nr_*_1920x1080.txt` contiennent des descriptions de couches et décalages, **aucun poids du modèle**.

| Famille / branche | Original | Small |
|---|---:|---:|
| FSwin classique sans frontière de vue | 28 | 0 |
| FSwin `inpview` | 4 | 4 |
| FSwin `outview` | 4 | 4 |
| FSwin `ds` | 4 | 4 |
| FSwin `upsample` | 4 | 4 |
| Split-Swin (y compris FFWD, QKV et projections) | 65 | 17 |
| ViT | 40 | 40 |
| Pré-image / post-image / décodage | 1 / 1 / 1 | 1 / 1 / 1 |
| Non classés | 0 | 0 |
| FSwin vues à calcul canonique + adaptateurs explicites | 8 | 8 |
| Segments FSwin homogènes extraits avec vues | 8 | 8 |

**Importance :** la taille réduite du plan Small n’implique pas une couverture facile. Ses 16 couches FSwin sont toutes des variantes de vue ou de résolution. Les familles `inpview` et `outview` partagent les calculs FSwin mais nécessitent leurs contrats spécifiques de mémoire et de disposition ; les variantes `ds` et `upsample` ajoutent des opérations de résolution et de skips. Le wrapper actuel n'en exécute aucune comme un bloc standard.

Le nouveau `nr_rdna2_native_plan_coverage.h` (vendor) classe chaque étape sans la compter comme fonctionnelle. `test_rdna2_nr_native_plan_corpus.cpp` vérifie intégralement la lecture des 228 lignes, les totaux, les 8 segments de l’original, et l'absence de faux segments sur Small ; ce test est enregistré dans CTest.

La présence d'un kernel ou d'une entrée de plan **ne constitue pas une preuve d'exécution sur PS5**. Les conversions de vues, la pyramide multi-résolution, le graphe des skips U-Net, l'entrée/sortie image et la connexion des branches ViT/Split-Swin restent à finaliser. La performance est reportée après l'intégration et la validation du premier rendu.


## Frontières FSwin InputView et OutputView

Les variantes inpview/outview utilisent le même calcul FSwin que les couches
ordinaires, mais changent de disposition au bord des niveaux. Elles entrent
désormais dans les segments canoniques E4M3FN sous les conditions suivantes :

- InputView doit être la première couche. UploadRasterFeatures transforme un
  raster de caractéristiques déjà E4M3FN en fenêtres ; UploadInput direct est
  interdit pour cette entrée.
- OutputView doit être la dernière couche. BindRasterOutput exige un buffer
  de sortie distinct et assez grand avant Record, faute de quoi la chaîne
  refuse de lancer le calcul.
- NrRdna2FSwinOutputView annule les décalages de fenêtres (notamment (0,-1))
  par shader de repack, puis reconstruit le raster de caractéristiques sur GPU.
- Les dimensions XY doivent être fournies explicitement selon le plan source ;
  le code ne devine aucune rotation. Un raster de caractéristiques n'est pas
  une image RGB : pré/post-image et DS/UPS restent ouverts.

L'éligibilité FSwin devient Original 36/152 (28 plain + 8 vues) et Small 8/76
(8 vues), avec 8 segments homogènes dans chaque cas. Il reste à valider
la compilation C++/SPIR-V et la parité GPU et à raccorder le graphe entier.


## Nouveau calcul FSwin DS — pool 2×2 et projection 2C × C

Le shader Vulkan 1.1 FSwinDownsample prend la sortie d'un bloc FSwin
sous forme de fenêtres E4M3FN décalées en tuiles 4×4, réduit chaque
quadruplet de pixels 2×2 (arithmétique FP16 scalaire de référence,
quantification FP8), puis applique la matrice apprise row-major de
forme [2C,C] à chaque pixel de demi-résolution. Résultat : raster
E4M3FN [ceil(W/2),ceil(H/2),2C].

- Le poids resample.bin est lu uniquement depuis un NRMODEL1 fourni
  localement via PrepareFSwinDownsampleWeights, avec requantification
  E4M3FN du modèle comme pour les autres couches.
- Dispatch 3D : (C/8, fenêtres_x, fenêtres_y), source et destination
  distinctes, au plus 256 MiB par buffer et offsets u32 bornés.
- Les dimensions XY et offsets sont explicites ; les bords hors image
  sont considérés à zéro. Aucun hook Windows/NVIDIA.
- Il reste à brancher le shader et les buffers au runtime de couche FSwin
  pour les variantes ds, et à convertir la sortie projetée vers les
  fenêtres d'entrée du niveau C→2C suivant. La parité numérique réelle
  avec le kernel amont ainsi que la compilation/CI restent à vérifier.

Aucun chiffre de performance ni frame DLSS PS5 n'est revendiqué.


## Calcul autonome FSwin UPS — projection et skip

Le nouveau shader FSwinUpsample RDNA2 porte le prologue de la branche
upsample : projection [C,2C] d'un raster de caractéristiques demi-résolution
E4M3FN, expansion plus proche voisin 2x, puis ajout de la branche de saut
U-Net pondérée par un gain FP32 propre à chaque canal. Sortie : raster
E4M3FN pleine résolution C, destiné au FSwin normal suivant.

Les poids proviennent du paquet NRMODEL1 local. Le chargeur
PrepareFSwinUpsampleWeights exige un tableau de gains COMPLET, sans
padding de zéros arbitraires. L'amont signale 16 coefficients manquants
pour les largeurs C64/128/256 : ces modèles sont refusés tant que le
raccord de l'archive et la parité numérique ne sont pas établis. C32,
avec un tableau complet, constitue la référence initiale.

Les préconditions incluent dimensions et formats low/skip identifiés,
buffers séparés, échelles vérifiées, limite 256 MiB par stockage et
workgroups 3D. Le shader autonome est raccordé au build, mais pas encore
aux allocations/transitions du graphe multi-résolution. Tests host et
SPIR-V enregistrés, sans exécution confirmée de CI ni résultat PS5.


## GPU raster-to-windows à l'entrée des segments InputView

NrRdna2FSwinChain::BindRasterInput peut désormais recevoir le buffer
Vulkan STORAGE contenant le raster E4M3FN du niveau précédent. Il valide
la dimension complète, la disposition non décalée, les étendues source
et destination et le non-aliasing, puis alloue les descripteurs du shader
fswin_raster_layout_rdna2.comp en mode raster→fenêtres. Record insère ce
calcul juste avant le premier bloc FSwin, avec sa barrière compute→compute,
puis rend l'entrée disponible au runtime ; aucun readback CPU n'est requis.

Les chemins BindRasterInput et UploadRasterFeatures sont exclusifs pour
une même chaîne. La source doit rester vivante et exploitable pendant la
soumission GPU ; aucune étape n'essaie de récupérer directement les pixels
RGB d'un jeu. Ce lien rend possible le raccord de la sortie de downsample
vers un InputView de même dimension/canaux, sans constituer à lui seul
l'orchestration U-Net ni une preuve de rendu PS5.


## Étapes terminales FSwin `ds` — branche GPU raccordée

Les quatre étapes `_ds_fp8` par variante conservent le corps FSwin
ordinaire C canaux, suivi d'un pool 2×2 et de la projection apprise
`[2C,C]`. Le plan natif les identifie maintenant comme un terminal
spécifique, sans les confondre avec un FSwin classique.

`NrRdna2FSwinDownsampleOutput` récupère la sortie GPU du corps
FSwin, charge la matrice `resample.bin` fournie localement dans
NRMODEL1, la transfère dans un buffer Vulkan persistant, lie les
trois descripteurs et enregistre le shader de réduction.

`NrRdna2FSwinChain::BindDownsampleOutput(model,destination,W,H)`
exige un raster E4M3FN de sortie `ceil(W/2) × ceil(H/2) × 2C`.
`ResultRaster()` expose sa description de buffer à l'orchestrateur,
qui doit ordonner la passe et attendre sa fin avant consommation.
Le niveau suivant peut en principe utiliser `BindRasterInput()`.

**Sécurité** : `Record()` refuse une chaîne DS dont le modèle ou la
destination n'a pas été correctement lié. `_ds` doit être terminal.
Dimensions, limites GPU, matrices et alias de buffers sont vérifiés.
Le raster ne constitue pas une image RGB.

Couverture **structurelle, pas preuve GPU** : Original **40/152**
(28 plain + 8 vues + 4 DS), Small **12/76** (8 vues + 4 DS).
Les 8 sections de chaque plan restent en cours d'assemblage ;
`upsample`, transitions U-Net/skip, ViT, Split-Swin,
pré/post-image et validation console sont encore à terminer.


## Liaison GPU entre deux niveaux U-Net (DS → InputView)

Le composant vendor `NrRdna2FSwinLevelLink` raccorde maintenant deux
chaînes distinctes sur **le même scheduler Vulkan**. `Prepare()`
vérifie les buffers et géométries, puis :
1. Lie la sortie `ds` de la chaîne amont au raster E4M3FN externe.
2. Lie ce raster à l'entrée GPU `inpview` du niveau suivant,
   après contrôle de la résolution et de l'augmentation C→2C.
3. `Record()` enregistre les deux chaînes dans cet ordre, sans
   readback et avec les barrières compute existantes.

Le contrat `CanFSwinLevelLink` exige les grilles explicites,
un input-view non décalé, des dimensions `ceil(W/2)×ceil(H/2)`,
des capacités réelles et un budget de 256 Mio par ressource.
Exemple vérifié par les assertions hôte ajoutées :
`540×960, C32, 68×120 fenêtres` → `270×480, C64, 34×60`.
C64→128 et C128→256 sont également couverts.
La transition C256→512 est rejetée car elle appartient
au Split-Swin et ne relève pas de ce raccordement FSwin.

Le buffer externe et les deux chaînes doivent vivre jusqu'à la
fin de la soumission. L'échec d'une préparation n'entraîne pas
de dispatch partiel ; l'appelant peut reconstruire les deux
chaînes. La connexion du réseau complet avec skips/ViT/Split-Swin
reste à faire. Aucune image PS5 ni mesure de performance annoncée.


## Préservation du skip U-Net au moment du downsample

La chaîne FSwin terminée par `_ds` expose désormais **deux sorties
GPU distinctes** lorsqu'elles sont liées explicitement :

1. `BindDownsampleOutput()` : le raster réduit
   `ceil(W/2) × ceil(H/2) × 2C` destiné à la résolution suivante.
2. `BindSkipRasterOutput()` : le raster **avant réduction**
   `W × H × C`, reconstitué depuis les fenêtres avec annulation du
   décalage 4×4, pour le futur skip de l'upsample.

`Record()` enregistre le shader de conversion du skip et celui de
downsample **après** les couches FSwin. La source est la même, les
destinations sont distinctes et leurs buffers appartiennent à
l'appelant ; `ResultSkipRaster()` et `ResultRaster()` exposent les
descripteurs qui pourront être conservés par le graphe U-Net.
Aucun téléchargement CPU n'est requis.

Les protections rejettent des buffers source/destination
aliasés et toute sortie skip dont les dimensions ou le budget
VRAM sont incompatibles. Les liens entre les indices de blocs
du plan natif et la durée de vie du cache de skip restent à
implémenter : **le cache et le scheduler U-Net complets ne sont
pas encore construits**.

Le port ne dispose toujours pas d'une preuve de première image
Neural Rendering sur console. Aucun travail de performance n'a
été engagé.


## Routage exact des quatre branches de saut U-Net

Nouveau classificateur vendor `nr_rdna2_unet_skip_map.h`,
testé sur les deux corpus natifs de 152 et 76 couches.
Il associe une réduction `FSwin _ds` à son consommateur
`FSwin _upsample` **via `input1` du plan**, et non par ordre
d'apparition ou supposition sur la taille du raster.

| Niveau, canaux | Original (DS → UPS) | Compact/Small (DS → UPS) |
|---|---|---|
| C256 | 22 → 48 | 8 → 22 |
| C128 | 14 → 56 | 6 → 24 |
| C64 | 8 → 62 | 4 → 26 |
| C32 | 4 → 66 | 2 → 28 |

Contrôles : 4 producteurs/4 consommateurs, références présentes,
C et 2C cohérents, relations de dépendance, niveaux inversés,
écarts d'un pixel maximum aux divisions par deux, refus des
doublons/références invalides et **absence de résultat partiel**.
Le test `test_rdna2_nr_unet_skip_map` couvre les deux
corpus et plusieurs mutations négatives.

**Limite fonctionnelle explicite :** les liens du graphe sont
maintenant **identifiés**, mais l'allocation et la durée de vie
des quatre buffers skip, le raccord aux descripteurs du prologue
`upsample`, les gains incomplets C≥64 et la traversée
Split-Swin / ViT restent à implémenter. Ne pas compter cette
classification comme une image NR calculée sur PS5.


## Cache GPU propriétaire des quatre skips U-Net

`NrRdna2UNetSkipCache` (vendor) alloue et conserve les
**quatre rasters E4M3FN des branches de saut** avec VMA DeviceLocal,
sans passer par le CPU. `Initialize()` reçoit la carte de saut
issue du plan natif et les dimensions raster exactes dans l'ordre
des consommateurs UPS. Le cache refuse toute géométrie ambiguë.

Pour les deux corpus de référence, les tailles sont :

| Provenance du skip | Format de sortie GPU | Taille |
|---|---|---:|
| C256 | 67 × 120 × 256 | 2 058 240 octets |
| C128 | 135 × 240 × 128 | 4 147 200 octets |
| C64 | 270 × 480 × 64 | 8 294 400 octets |
| C32 | 540 × 960 × 32 | 16 588 800 octets |

Le total est **31 088 640 octets** (< 128 Mio autorisés par le
cache). `BindProducer(down_block,chain)` branche le raster de saut
sur la sortie pré-downsample de la bonne chaîne, sous contrainte
de même scheduler Vulkan. `ForUpsample(up_block)` retrouve le
descripteur du skip par l'indice de bloc natif.

**Important :** un buffer lié ne prouve pas que son écriture GPU
est achevée. Le graphe global doit enregistrer tous les producteurs
avant les consommateurs, conserver le cache et ses allocations tant
que des commandes sont en vol et gérer leurs fences. Cette gestion
des submissions reste nécessaire avant la validation d'un rendu NR.

Test host `test_rdna2_nr_unet_skip_cache_policy.cpp` :
quatre dimensions réelles, octets exacts, limite de capacité,
erreurs de dimension, doublons de blocs et comptage incomplet,
sur Original et Small. Le cache ne contient aucun code par jeu.
