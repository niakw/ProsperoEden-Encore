# Eden Encore — Dépannage · Français (Canada)

[Présentation](README.fr-CA.md) · [Installation et mise à jour](INSTALL.fr-CA.md) · [Paramètres](SETTINGS.fr-CA.md) · [Dépannage](TROUBLESHOOTING.fr-CA.md) · [Assistance](SUPPORT.fr-CA.md) · [Accessibilité](ACCESSIBILITY.fr-CA.md) · [🌐](../../LANGUAGES.md)

Si l’application ne démarre pas, vérifiez eboot.bin, sce_sys et ui/lang. Si des jeux manquent, vérifiez roms à la racine de stockage sélectionnée. Si les menus restent en anglais, contrôlez les fichiers de traduction. Safe Launch rétablit les paramètres d’un jeu sans effacer les sauvegardes.

## Installation et mise à jour

Téléchargez une version réellement publiée dans Releases, après avoir sauvegardé l’application et vos données. Pour ZIP/FTP, copiez le dossier PPSA99008 entier dans /data/homebrew/PPSA99008/. Ne mélangez pas ZIP/FTP et FFPFSC/ShadowMountPlus; vérifiez le SHA-256 s’il est fourni.

```text
/data/homebrew/PPSA99008/
/data/prosperoeden/
/data/prosperoeden/roms/
/data/prosperoeden/keys/
/data/prosperoeden/firmware/
```

## Paramètres

Le profil recommandé utilise Vulkan, une sortie télé 1440p, une résolution interne 1.25x, FSR 1 spatial à 50 % de netteté, FXAA et 60 Hz. La sortie du téléviseur et la résolution de rendu du jeu sont distinctes. La génération d’images n’accélère pas la simulation du jeu.

## Assistance

Dans GitHub Issues, indiquez la version d’Encore, le micrologiciel PS5, les étapes pour reproduire le problème, les paramètres concernés et des journaux anonymisés. Ne partagez jamais de clés, de sauvegardes ou de données privées.

Ne supprimez jamais /data/prosperoeden/ : ce dossier peut contenir des sauvegardes, paramètres et clés. Sauvegardez aussi les données externes.

---

La dernière compilation publique authentique PS5 date du 15 octobre 2026; celle publiée le 30 octobre était une copie. La nouvelle préversion en brouillon ne contient aucun binaire ni jeu de deuxième génération validé sur console.

[English](../../TROUBLESHOOTING.md) · [Installation et mise à jour](INSTALL.fr-CA.md) · [Releases](https://github.com/niakw/ProsperoEden-Encore/releases)
