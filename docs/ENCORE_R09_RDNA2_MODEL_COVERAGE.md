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
