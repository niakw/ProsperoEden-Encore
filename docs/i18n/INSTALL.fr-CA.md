<!-- Encore user guide crosslinks 2026-11-09 -->
> **Paramètres:** [Paramètres](SETTINGS.fr-CA.md) · [Dépannage](TROUBLESHOOTING.fr-CA.md) · [Assistance](SUPPORT.fr-CA.md) · [Accessibilité](ACCESSIBILITY.fr-CA.md) · [Languages](../../LANGUAGES.md)
>
> La dernière compilation publique authentique PS5 date du 15 octobre 2026; celle publiée le 30 octobre était une copie. La nouvelle préversion en brouillon ne contient aucun binaire ni jeu de deuxième génération validé sur console.

# Prospero.Eden Encore — Migration depuis le projet d’origine (Français (Canada))

[← Français (Canada)](README.fr-CA.md) · [Guide complet en anglais](../../INSTALL.md) · [Toutes les langues](../../LANGUAGES.md)

**Dernière release PS5 réellement compilée :** [R1 du 15 octobre 2026](https://github.com/niakw/Prospero.Eden-Encore/releases/tag/encore-R1-56293953), avec l'archive FTP `Eden-Encore-56293953-FTP-PPSA99008.zip` et son `SHA256SUMS`. La version recopiée le 30 octobre n'est pas une nouvelle compilation, et les changements récents de `main` ne sont pas intégrés à ce binaire. [Audit](../../docs/RELEASE_BASELINE_WORKFLOW_AUDIT_2026-11-09.md).

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
