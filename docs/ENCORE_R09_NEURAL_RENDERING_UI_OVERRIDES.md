# Eden Encore — architecture visuelle Graphics / NR

## Écran des paramètres globaux

```text
┌───────────────────────────────────────────────────────┐
│ ENCORE • PARAMÈTRES GRAPHIQUES                       │
├───────────────────────────────────────────────────────┤
│ RENDU / IMAGE                                         │
│   Moteur graphique          ◀ Vulkan ▶                │
│   Profil vidéo              ◀ Recommandé ▶            │
│   Résolution de sortie      ◀ 1440p ▶                  │
│   Résolution interne        ◀ 1,25x ▶                  │
│   Upscaling                 ◀ Bilinéaire ▶            │
│   Netteté                   [ 50 % ] (selon filtre)   │
│   Anticrénelage             ◀ FXAA ▶                  │
│   Filtrage textures         ◀ 4x ▶                    │
├───────────────────────────────────────────────────────┤
│ NEURAL RENDERING            ◀ Désactivé ▶ (DÉFAUT)    │
│   Choix successifs dans LE MÊME sélecteur :            │
│     Désactivé                                         │
│     A4K — Détails améliorés                           │
│     A4K — Image adoucie                               │
│     A4K — Image nettoyée                              │
│     DLSS-NR — Original                                │
│     DLSS-NR — Compact                                 │
│   Intensité DLSS-NR         [ 65 % ] [grisé si ≠ DLSS]│
├───────────────────────────────────────────────────────┤
│ FRAME GENERATION           ◀ Désactivé ▶ (DÉFAUT)     │
│   MihawkGen • FSR 3 • LSFG si compatibles             │
│   Taux de rafraîchissement ◀ 60 Hz ▶                  │
│   Compteur FPS             ◀ Désactivé ▶              │
├───────────────────────────────────────────────────────┤
│ AIDE CONTEXTUELLE                                     │
│   Description du mode, format image, limites GPU,     │
│   conflits explicites et paramètres non applicables. │
└───────────────────────────────────────────────────────┘
```

## Par jeu / Encore Override

Même architecture, mais chaque valeur peut **hériter du global**.
L'utilisateur garde le dernier mot ; aucun preset de jeu
ne lui impose Neural Rendering ou Frame Generation.

Exemple **illustratif du format cible enrichi** d'un fichier
`games/0100C49025D3E000.json` (EA SPORTS FC 27) :

```json
{
  "schema_version": 2,
  "title_id": "0100C49025D3E000",
  "name": "EA SPORTS FC 27",
  "source_console": "Nintendo Switch 1",
  "target_hardware": "PS5 standard",
  "auto_apply": true,
  "default_profile": "recommended",
  "gameplay_target_fps": 30,
  "profiles": {
    "recommended": {
      "name": "Recommandé",
      "settings": {
        "renderer": "vulkan",
        "console_mode": "docked",
        "game_resolution": 1.25,
        "tv_output": "1440p",
        "upscaling_filter": "bilinear",
        "fsr_sharpness": 50,
        "anti_aliasing": "fxaa",
        "texture_anisotropy": "4x",
        "refresh_rate_hz": 60,
        "neural_rendering": "off",
        "neural_strength": 65,
        "frame_generation": "off",
        "fps_overlay": false
      }
    }
  }
}
```

**Important :** ce JSON `schema_version:2` est une proposition
d'extension de l'architecture Encore Overrides, **pas encore un
manifest v2 accepté par le parseur v1**. Le `65 %` est une
valeur fictive de préconfiguration, non issue d'une mesure de FC27.
Dans la configuration utilisateur `prosperoeden.json`,
les champs `neural_rendering`, `neural_strength` et
`frame_generation` sont déjà persistés. Le port de ces champs
dans le générateur et le manifest versionné est à finaliser.

## Contrats techniques

- NR désactivé : tous les upscalers spatiaux éligibles restent accessibles.
- A4K : choix NR 1/2/3, mode Vulkan calculé avec les pipelines A4K existants.
- DLSS-NR : choix NR 4/5, intensité disponible 0–100 %.
- Tous les NR : composition exclusive avec le filtre spatial Bilinéaire
  tant que l'assemblage GPU n'a pas prouvé d'autres combinaisons.
- Frame Generation : Off lorsque NR ≠ Off.
- MSAA forcé : non associé aux modes NR tant que la compatibilité console
  n'est pas validée ; None/FXAA/SMAA possibles selon le renderer.
- Les valeurs invalides sont refusées et accompagnées d'une aide descriptive.
- Les paramètres à dépendance sont grisés, sans suppression des
  préférences sauvegardées.
