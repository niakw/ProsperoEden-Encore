# Installer et mettre à jour Encore — Français

[← README français](README.fr.md) · [Toutes les langues](../../LANGUAGES.md) · [Installation détaillée (anglais)](../../INSTALL.md)

**Firmware PS5 testé avec Encore : 13.60 uniquement.** Les versions antérieures pourraient fonctionner, mais ne sont pas validées. Aucun minimum n'est établi ; ce guide n'est pas une invitation à mettre à jour la console.

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

- **Toujours en anglais** : choisir Settings → Language et vérifier les **29 catalogues** dans `PPSA99008/ui/lang/`. Le menu propose **18 choix de langue/région**, correspondant à 13 langues.
- **Bibliothèque vide** : vérifier la racine active et le dossier `roms/`.
- **Configuration incomplète** : vérifier les dossiers `keys/` et `firmware/` avec des fichiers légalement obtenus.
- **Jeu devenu instable après modification des réglages** : essayer **Safe Launch**, sans supprimer les sauvegardes.
- **Saccades, retard HUD ou gel à la pause** : problèmes pouvant encore survenir, même si les tests hôtes sont verts.

[Dépannage complet (anglais)](../../TROUBLESHOOTING.md) · [Support](../../SUPPORT.md).

Encore ne fournit ni jeu, ni clé propriétaire, ni firmware.
