# Eden Encore R09 — retrait des limites artificielles de fenêtres FSwin

**État : correction de couverture fonctionnelle, sans optimisation de performance.**

## Problème initial

Les contrats du portage RDNA2 refusaient les FSwin dès 257 fenêtres. À 960×540 (caractéristiques C32), il faut **120×68=8 160 fenêtres**, sans changement de modèle. Cette restriction rendait impossible une partie du réseau même lorsque les allocations GPU respectaient leurs budgets.

De plus, le pont raster/fenêtres et le shader de déplacement de fenêtres utilisaient un dispatch linéaire `x = fenêtres × (C/4)`, qui dépassait les limites de workgroups d'une seule dimension.

## Correction

- Les contrats FSwin, QKV, plans, géométrie des chaînes, conversion raster et repack acceptent **jusqu'à 65 535 fenêtres**, sans déroger au plafond existant de **256 MiB par buffer** ni aux vérifications d'adresses 32 bits.
- La projection FSwin, particulièrement l'expansion **C→4C**, continue de refuser explicitement les ressources trop grandes. Le pool Vulkan garde son budget global de **512 MiB par couche** et la vérification `GetMaxStorageBufferRange()`.
- Les deux shaders de conversion sont désormais dispatchés en **3 dimensions** : X=C/4 groupes de 64 mots, Y=windows_x et Z=windows_y. L'index source/destination FP8 reste inchangé ; seuls les identifiants de workgroup qui le reconstruisent changent.
- Le pont de plan natif ne sélectionne des segments FSwin que si leur activation d'expansion `windows × 64 × 4C` reste sous 256 MiB. Aucun surdimensionnement implicite n'est considéré comme opérationnel.
- Des cas de test couvrent les anciennes petites grilles, **8 160 fenêtres C32**, un raster 1920×1080 C32, les nouvelles dimensions de dispatch et les rejets pour dépassement.

## Ce que cette correction ne prétend pas résoudre

- Ce n'est pas une preuve de rendu 1080p : le modèle, le prétraitement couleur, les transitions de résolution, le ViT et le post-traitement restent incomplets.
- Les très grandes résolutions ou certains canaux dépassent toujours les budgets par buffer/couche ; le graphe doit être traité par tuiles ou en streaming **après** validation du chemin fonctionnel, et sans compromettre les surfaces de jeux PS5.
- Les kernels dépendent toujours des limites Vulkan effectives du périphérique (vérifier `maxComputeWorkGroupCount` et `maxStorageBufferRange` au runtime). Le plafond spécifié ici n'est pas une promesse de compatibilité universelle GPU.
- Aucun benchmark PS5 n'est réalisé : la performance est reportée après l'intégration complète.
