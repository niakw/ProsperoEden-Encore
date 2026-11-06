# Eden Encore R09 — paramètres Neural Rendering, phase de préparation

**État du 6 novembre 2026 : stockage et interface préparés, moteur inactif.**

## Valeurs et noms

- « Neural rendering » : statut « In preparation », non activable.
- « NR model » : **Original** (plan complet 152 étapes) ou **Compact**
  (plan Small 76 étapes), valeurs stables `original`/`small`.
- « NR intensity » : entier **0 à 100 %**, défaut **100 %**,
  par pas de 5 % dans le launcher.
- Aucun sélecteur de qualité/performance supposée, de résolution interne
  ou de cadence temporelle tant que la précision et les FPS console
  n'ont pas été mesurés.

## Persistance et héritage

Les clés `/video/neural_model` et `/video/neural_strength`
sont sauvegardées dans le JSON de préférences existant ;
les mêmes clés par jeu sont conservées sous `/games/<title-id>/`.
Pour les jeux, `-1` en mémoire (clé absente en JSON) signifie
héritage. Cela ne modifie ni l'identité ni les contenus
des presets vidéo et ne change pas les préférences FSR/AA/A4K.

La validation de l'index modèle et de l'intensité s'exécute à la lecture
(fallback sûr) et à l'écriture (refus des valeurs invalides).
Les mappings `Eden::Preferences` ↔ `pe::ui::Preferences` et
`Eden::GameSettings` ↔ `pe::ui::GameSettings` sont mis à jour
pour éviter la perte de valeurs au passage par le launcher.

Test `tools/graphics/test_rdna2_nr_settings_store.cpp` :
aller-retour des clés globales et par jeu, héritage, invalidations,
préservation des autres valeurs et compatibilité ascendante.
Le gate hôte CMake ne construit ce test que si `nlohmann/json.hpp`
est présent ; il ne revendique pas de test réussi sans exécution.

## Sécurité de publication

**Aucune activation graphique** ne lit ces préférences pour lancer NR.
Le statut reste non sélectionnable dans le launcher jusqu'à ce que
les chemins complet Original/Compact, d'entrée image, de sortie image,
de poids et de lifetime des buffers soient qualifiés. Pas de
mise en release ni de changement des paramètres NS1.
