# R09 — audit de couverture des plans neuraux Original et Small

Corpus structurels MIT, issus de [Overclockers/DLSSNR-AMD](https://github.com/Overclockers/DLSSNR-AMD) : `nr_native_plan_data.hpp` (152 lignes) et `nr_native_plan_data_small.hpp` (76 lignes). Les fichiers `extras/graphics/fixtures/r09_nr_*_1920x1080.txt` contiennent des descriptions de couches et décalages, **aucun poids du modèle**.

| Famille / branche | Original | Small |
|---|---:|---:|
| FSwin classique (éligible à la chaîne actuelle) | 28 | 0 |
| FSwin `inpview` | 4 | 4 |
| FSwin `outview` | 4 | 4 |
| FSwin `ds` | 4 | 4 |
| FSwin `upsample` | 4 | 4 |
| Split-Swin (y compris FFWD, QKV et projections) | 65 | 17 |
| ViT | 40 | 40 |
| Pré-image / post-image / décodage | 1 / 1 / 1 | 1 / 1 / 1 |
| Non classés | 0 | 0 |
| Segments FSwin standard extraits | 8 | 0 |

**Importance :** la taille réduite du plan Small n’implique pas une couverture facile. Ses 16 couches FSwin sont toutes des variantes de vue ou de résolution. Les familles `inpview` et `outview` partagent les calculs FSwin mais nécessitent leurs contrats spécifiques de mémoire et de disposition ; les variantes `ds` et `upsample` ajoutent des opérations de résolution et de skips. Le wrapper actuel n'en exécute aucune comme un bloc standard.

Le nouveau `nr_rdna2_native_plan_coverage.h` (vendor) classe chaque étape sans la compter comme fonctionnelle. `test_rdna2_nr_native_plan_corpus.cpp` vérifie intégralement la lecture des 228 lignes, les totaux, les 8 segments de l’original, et l'absence de faux segments sur Small ; ce test est enregistré dans CTest.

La présence d'un kernel ou d'une entrée de plan **ne constitue pas une preuve d'exécution sur PS5**. Les conversions de vues, la pyramide multi-résolution, le graphe des skips U-Net, l'entrée/sortie image et la connexion des branches ViT/Split-Swin restent à finaliser. La performance est reportée après l'intégration et la validation du premier rendu.
