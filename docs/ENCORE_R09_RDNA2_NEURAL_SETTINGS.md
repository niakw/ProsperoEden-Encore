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

## Dynamically checked dependencies and honest labels (6 Nov 2026)

Neural Rendering (NR) and Frame Generation both default to **Off**.
NR is not official NVIDIA DLSS: it is a separate RDNA2 port being implemented.
The global Video dialog shows Off — not available, and grays NR model/intensity
until a validated NR backend is explicitly selected.

In Game settings, NR preset model and NR preset intensity remain editable while
NR is OFF, with a clear Preset label. The values are persisted per title without
activating any shaders. They do not modify the Recommended/High/Ultra profiles.

The single policy headless/neural_video_policy.h distinguishes incomplete engine,
unsupported OpenGL, competing upscaling reconstruction, unqualified forced MSAA
and unqualified NR+Frame Generation. It is conservative, not a claim that those
combinations are fundamentally impossible. It does not silently alter FG or AA.

The JSON selector video.neural_rendering is off by default. Explicit per-game off
remains possible; missing per-game keys mean inheritance. Load and save refuse
manual attempts to activate the unfinished NR backend.

Host regression tests cover defaults, invalid modes, model/intensity persistence
and the compatibility decision table. No PS5 graphics validation is claimed.
