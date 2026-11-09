# Eden Encore — Paramètres · Français (Canada)

[Présentation](README.fr-CA.md) · [Installation et mise à jour](INSTALL.fr-CA.md) · [Paramètres](SETTINGS.fr-CA.md) · [Dépannage](TROUBLESHOOTING.fr-CA.md) · [Assistance](SUPPORT.fr-CA.md) · [Accessibilité](ACCESSIBILITY.fr-CA.md) · [Languages](../../LANGUAGES.md)

Le profil recommandé utilise Vulkan, une sortie télé 1440p, une résolution interne 1.25x, FSR 1 spatial à 50 % de netteté, FXAA et 60 Hz. La sortie du téléviseur et la résolution de rendu du jeu sont distinctes. La génération d’images n’accélère pas la simulation du jeu.

## Vulkan · 1440p · 1.25x · FSR 1

| Video preset | Renderer | TV output | Game resolution | Upscaling | Sharpening | AA | Refresh |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Minimum | Vulkan | 1080p | 1x | Bilinear | — | None | 60 Hz |
| Recommended | Vulkan | 1440p | 1.25x | FSR 1 | 50% | FXAA | 60 Hz |
| High | Vulkan | 2160p | 1.5x | Bicubic | 50% | FXAA | 60 Hz |

**Neural Rendering: Off · Frame Generation: Off.** Le profil recommandé utilise Vulkan, une sortie télé 1440p, une résolution interne 1.25x, FSR 1 spatial à 50 % de netteté, FXAA et 60 Hz. La sortie du téléviseur et la résolution de rendu du jeu sont distinctes. La génération d’images n’accélère pas la simulation du jeu.

## Controller · Touchpad · Language

`Touchpad` (short press) opens the Encore in-game quick settings overlay; the central PS system button is reserved by the console. FPS, mapping, graphics and logs are grouped in that overlay. Settings that cannot be changed during an active game require a game restart. Choose `Settings → Language` in the launcher; some catalog languages are not exposed as a menu option.

## Accessibilité

L’agrandissement du texte, le contraste élevé et la réduction des mouvements peuvent être activés séparément dans Accessibilité; ils sont désactivés par défaut. L’accessibilité du lanceur ne garantit pas celle de chaque jeu.

## Dépannage

Si l’application ne démarre pas, vérifiez eboot.bin, sce_sys et ui/lang. Si des jeux manquent, vérifiez roms à la racine de stockage sélectionnée. Si les menus restent en anglais, contrôlez les fichiers de traduction. Safe Launch rétablit les paramètres d’un jeu sans effacer les sauvegardes.

Ne supprimez jamais /data/prosperoeden/ : ce dossier peut contenir des sauvegardes, paramètres et clés. Sauvegardez aussi les données externes.

---

La dernière compilation publique authentique PS5 date du 15 octobre 2026; celle publiée le 30 octobre était une copie. La nouvelle préversion en brouillon ne contient aucun binaire ni jeu de deuxième génération validé sur console.

[Detailed English settings reference](../../SETTINGS.md) · [English installation](../../INSTALL.md) · [Eden Encore Releases](https://github.com/niakw/ProsperoEden-Encore/releases)