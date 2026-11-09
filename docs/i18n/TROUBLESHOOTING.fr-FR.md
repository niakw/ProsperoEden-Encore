# Eden Encore — Dépannage · Français (France)

[Présentation](README.fr.md) · [Installation et mise à jour](INSTALL.fr-FR.md) · [Paramètres](SETTINGS.fr-FR.md) · [Dépannage](TROUBLESHOOTING.fr-FR.md) · [Assistance](SUPPORT.fr-FR.md) · [Accessibilité](ACCESSIBILITY.fr-FR.md) · [🌐](../../LANGUAGES.md)

Si l’application ne démarre pas, vérifie eboot.bin, sce_sys et ui/lang. Si des jeux manquent, contrôle roms dans la racine de stockage sélectionnée. Si l’interface reste en anglais, vérifie les catalogues de traduction. Safe Launch restaure les paramètres d’un jeu sans supprimer les sauvegardes.

## Installation et mise à jour

Télécharge une version réellement publiée dans Releases après avoir sauvegardé l’application et tes données. Pour ZIP/FTP, copie le dossier PPSA99008 entier vers /data/homebrew/PPSA99008/. Ne mélange pas ZIP/FTP et FFPFSC/ShadowMountPlus et vérifie le SHA-256 lorsqu’il est fourni.

```text
/data/homebrew/PPSA99008/
/data/prosperoeden/
/data/prosperoeden/roms/
/data/prosperoeden/keys/
/data/prosperoeden/firmware/
```

## Paramètres

Le profil conseillé utilise Vulkan, une sortie TV 1440p, une résolution interne 1.25x, FSR 1 spatial avec 50 % de netteté, FXAA et 60 Hz. La sortie TV ne correspond pas à la résolution interne du jeu. La génération d’images ne change pas la vitesse de simulation du jeu.

## Assistance

Dans GitHub Issues, indique la version Encore, le firmware PS5, les étapes précises, les réglages concernés et des logs anonymisés. Ne publie jamais tes clés, sauvegardes ou données personnelles.

Ne supprime jamais /data/prosperoeden/ : ce dossier peut contenir tes sauvegardes, paramètres et clés. Sauvegarde aussi le stockage externe.

---

Le dernier paquet PS5 réellement compilé et publié date du 15 octobre 2026. La publication du 30 octobre en était une copie. Le brouillon de prérelease ne contient aucun binaire ni compatibilité Switch 2 confirmée sur console.

[English](../../TROUBLESHOOTING.md) · [Installation et mise à jour](INSTALL.fr-FR.md) · [Releases](https://github.com/niakw/ProsperoEden-Encore/releases)
