# Prospero.Eden Encore — Migration depuis le projet d’origine (Français (Canada))

[← Français (Canada)](../../README.fr-CA.md) · [Guide complet en anglais](../../INSTALL.md) · [Toutes les langues](../../LANGUAGES.md)

## Bien démarrer

1. Téléchargez l’archive complète dans Encore Releases et vérifiez son empreinte.
2. Sauvegardez le dossier PPSA99008 existant, les données /data/prosperoeden et votre stockage externe.
3. Installez le dossier PPSA99008 complet dans /data/homebrew/PPSA99008/; ne copiez pas seulement eboot.bin.
4. Lancez Encore, vérifiez Settings → Storage et Language, puis utilisez vos propres fichiers obtenus légalement.

## Application / PPSA99008

```text
/data/homebrew/PPSA99008/         # complete application
/data/prosperoeden/               # persistent user files
/data/prosperoeden/keys/          # legally obtained keys
/data/prosperoeden/firmware/      # compatible firmware files
/data/prosperoeden/roms/          # games
/data/prosperoeden/updates/       # game updates
/data/prosperoeden/config/        # settings
/data/prosperoeden/logs/          # diagnostics
```

## Migration depuis le projet d’origine

Encore et ProsperoEden natif partagent le même identifiant PPSA99008 : ils ne s’installent pas indépendamment. Remplacez les fichiers de l’application au complet, sans supprimer les sauvegardes, préférences, jeux ou clés dans /data/prosperoeden. Sauvegardez tout ancien dossier assets/ avant la migration.

**Important :** ne jamais supprimer `/data/prosperoeden/` ni formater le stockage externe pendant une mise à jour. Sauvegarder d’abord et ne pas écraser les données existantes.

## Compatibilité et limites actuelles

Seul le micrologiciel PS5 13.60 a été testé sur une console réelle avec Encore. Les versions antérieures pourraient fonctionner, mais aucun minimum n’a été vérifié. Des saccades, retards du HUD, problèmes de commandes et blocages à la pause restent possibles. Une CI verte n’est pas un test matériel.

## Questions fréquentes

Si l’interface demeure en anglais, choisissez Settings → Language et vérifiez l’installation complète de ui/lang/.

Si un jeu ne démarre plus après un changement de réglage, essayer **Safe Launch** pour cette session, sans effacer les sauvegardes. Voir l’[installation ZIP/FFPFSC](../../INSTALL.md), le [dépannage](../../TROUBLESHOOTING.md) et le [support](../../SUPPORT.md).

Encore ne fournit aucun jeu, aucune clé et aucun micrologiciel propriétaire. Ne publiez pas de données privées dans les signalements.
