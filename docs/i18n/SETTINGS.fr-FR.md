# Eden Encore — Paramètres · Français (France)

[Présentation](README.fr.md) · [Installation et mise à jour](INSTALL.fr-FR.md) · [Paramètres](SETTINGS.fr-FR.md) · [Dépannage](TROUBLESHOOTING.fr-FR.md) · [Assistance](SUPPORT.fr-FR.md) · [Accessibilité](ACCESSIBILITY.fr-FR.md) · [Languages](../../LANGUAGES.md)

Le profil conseillé utilise Vulkan, une sortie TV 1440p, une résolution interne 1.25x, FSR 1 spatial avec 50 % de netteté, FXAA et 60 Hz. La sortie TV ne correspond pas à la résolution interne du jeu. La génération d’images ne change pas la vitesse de simulation du jeu.

## Vulkan · 1440p · 1.25x · FSR 1

| Video preset | Renderer | TV output | Game resolution | Upscaling | Sharpening | AA | Refresh |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Minimum | Vulkan | 1080p | 1x | Bilinear | — | None | 60 Hz |
| Recommended | Vulkan | 1440p | 1.25x | FSR 1 | 50% | FXAA | 60 Hz |
| High | Vulkan | 2160p | 1.5x | Bicubic | 50% | FXAA | 60 Hz |

**Neural Rendering: Off · Frame Generation: Off.** Le profil conseillé utilise Vulkan, une sortie TV 1440p, une résolution interne 1.25x, FSR 1 spatial avec 50 % de netteté, FXAA et 60 Hz. La sortie TV ne correspond pas à la résolution interne du jeu. La génération d’images ne change pas la vitesse de simulation du jeu.

## Controller · Touchpad · Language

`Touchpad` (short press) opens the Encore in-game quick settings overlay; the central PS system button is reserved by the console. FPS, mapping, graphics and logs are grouped in that overlay. Settings that cannot be changed during an active game require a game restart. Choose `Settings → Language` in the launcher; some catalog languages are not exposed as a menu option.

## Accessibilité

Les options Texte agrandi, Contraste élevé et Réduire les animations sont indépendantes et désactivées par défaut. Elles concernent le lanceur et ne garantissent pas l’accessibilité des jeux exécutés.

## Dépannage

Si l’application ne démarre pas, vérifie eboot.bin, sce_sys et ui/lang. Si des jeux manquent, contrôle roms dans la racine de stockage sélectionnée. Si l’interface reste en anglais, vérifie les catalogues de traduction. Safe Launch restaure les paramètres d’un jeu sans supprimer les sauvegardes.

Ne supprime jamais /data/prosperoeden/ : ce dossier peut contenir tes sauvegardes, paramètres et clés. Sauvegarde aussi le stockage externe.

---

Le dernier paquet PS5 réellement compilé et publié date du 15 octobre 2026. La publication du 30 octobre en était une copie. Le brouillon de prérelease ne contient aucun binaire ni compatibilité Switch 2 confirmée sur console.

[Detailed English settings reference](../../SETTINGS.md) · [English installation](../../INSTALL.md) · [Eden Encore Releases](https://github.com/niakw/ProsperoEden-Encore/releases)