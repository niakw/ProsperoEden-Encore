<!-- Encore user guide crosslinks 2026-11-09 -->
> **Paramètres:** [Paramètres](SETTINGS.fr-FR.md) · [Dépannage](TROUBLESHOOTING.fr-FR.md) · [Assistance](SUPPORT.fr-FR.md) · [Accessibilité](ACCESSIBILITY.fr-FR.md) · [Languages](../../LANGUAGES.md)
>
> Le dernier paquet PS5 réellement compilé et publié date du 15 octobre 2026. La publication du 30 octobre en était une copie. Le brouillon de prérelease ne contient aucun binaire ni compatibilité Switch 2 confirmée sur console.

# Installer et mettre à jour Encore — Français

[← README français](README.fr.md) · [Toutes les langues](../../LANGUAGES.md) · [Installation détaillée (anglais)](../../INSTALL.md)

**Firmware PS5 testé avec Encore : 13.60 uniquement.** Les versions antérieures pourraient fonctionner, mais ne sont pas validées. Aucun minimum n'est établi ; ce guide n'est pas une invitation à mettre à jour la console.

**Référence historique à télécharger :** la vraie [R1 FTP du 15 octobre 2026](https://github.com/niakw/Prospero.Eden-Encore/releases/tag/encore-R1-56293953) contient `Eden-Encore-56293953-FTP-PPSA99008.zip` et `SHA256SUMS`. L'importation de la release sur le nouveau dépôt le 30 octobre n'a **pas** recompilé l'application. Les fonctions ajoutées depuis à `main` ne sont pas dans cette archive. [Audit des builds](../../docs/RELEASE_BASELINE_WORKFLOW_AUDIT_2026-11-09.md).

## Installer en quatre étapes

1. Télécharger un paquet **complet** des [Releases Encore](https://github.com/niakw/ProsperoEden-Encore/releases), en vérifiant les informations de version et les empreintes fournies. Un build CI vert n'est pas une preuve de jouabilité.
2. **Sauvegarder** l'application actuelle `/data/homebrew/PPSA99008/`, les données `/data/prosperoeden/` et la racine de stockage externe si elle existe.
3. Pour **ZIP/FTP**, copier tout le dossier `PPSA99008/`, comprenant `eboot.bin`, `sce_sys/` et `ui/lang/`, dans `/data/homebrew/PPSA99008/`. Ne pas créer un double dossier `PPSA99008/PPSA99008/`. Pour **FFPFSC/ShadowMountPlus**, suivre [la méthode image](../../INSTALL.md#method-2--ffpfsc-with-shadowmountplus), sans mélanger ZIP et image.
4. Démarrer Encore, contrôler **Settings → Storage / Language**, la bibliothèque et les sauvegardes avant de supprimer toute ancienne copie.

## Mise à jour depuis ProsperoEden natif

**ProsperoEden d'origine et Encore partagent le même identifiant `PPSA99008`.** On met donc à jour l'application existante, pas une deuxième application indépendante.

- **Ne pas effacer `/data/prosperoeden/`** : il contient des paramètres, sauvegardes, jeux, clés et autres données utilisateur.
- Si l'ancienne application stockait des fichiers sous `PPSA99008/assets/`, **sauvegarder ce dossier avant le remplacement** et le conserver jusqu'à la fin de la migration.
- Conserver la racine externe sélectionnée. Une copie incomplète ou un conflit de destination ne justifie jamais d'écraser les sauvegardes.
- Pour **Encore → Encore**, installer la nouvelle application complète depuis les Releases **Encore** et vérifier les données au redémarrage.
- La mise à jour automatique **R21 est prévue, mais pas encore publiée**.

## Dossiers importants

```text
/data/homebrew/PPSA99008/     # application
/data/prosperoeden/           # données persistantes
/data/prosperoeden/keys/      # vos propres clés
/data/prosperoeden/firmware/  # firmware compatible
/data/prosperoeden/roms/      # jeux
/data/prosperoeden/updates/   # mises à jour de jeux
/data/prosperoeden/logs/      # diagnostics
```

En stockage externe, la structure reste identique sous la racine choisie. Les jeux ne sont pas inclus.

## Dépannage

- **Toujours en anglais** : choisir Settings → Language et vérifier les **31 catalogues** dans `PPSA99008/ui/lang/`. Le menu propose **exactement les 31 choix officiels de langue/région système PS5**, ni plus ni moins, selon la [liste Sony](https://www.playstation.com/fr-fr/legal/language-support/).
- **Bibliothèque vide** : vérifier la racine active et le dossier `roms/`.
- **Configuration incomplète** : vérifier les dossiers `keys/` et `firmware/` avec des fichiers légalement obtenus.
- **Jeu devenu instable après modification des réglages** : essayer **Safe Launch**, sans supprimer les sauvegardes.
- **Saccades, retard HUD ou gel à la pause** : problèmes pouvant encore survenir, même si les tests hôtes sont verts.

[Dépannage complet (anglais)](../../TROUBLESHOOTING.md) · [Support](../../SUPPORT.md).

Encore ne fournit ni jeu, ni clé propriétaire, ni firmware.
