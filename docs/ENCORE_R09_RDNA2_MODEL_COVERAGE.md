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
