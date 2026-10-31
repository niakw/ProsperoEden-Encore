# Prospero.Eden Encore — Français (Canada)

> L’émulation communautaire PS5 conçue pour le salon · [English (default)](README.md) · [Toutes les langues](LANGUAGES.md)

Encore est une branche communautaire indépendante avec un lanceur à la manette, une bibliothèque de jeux, des réglages vidéo et des outils de diagnostic. Ce n’est pas un produit officiel de Sony ou de Nintendo.

## Bien démarrer

1. Téléchargez l’archive complète dans Encore Releases et vérifiez son empreinte.
2. Sauvegardez le dossier PPSA99008 existant, les données /data/prosperoeden et votre stockage externe.
3. Installez le dossier PPSA99008 complet dans /data/homebrew/PPSA99008/; ne copiez pas seulement eboot.bin.
4. Lancez Encore, vérifiez Settings → Storage et Language, puis utilisez vos propres fichiers obtenus légalement.

[Migration depuis le projet d’origine](docs/i18n/INSTALL.fr-CA.md) · [Encore Releases](https://github.com/niakw/ProsperoEden-Encore/releases) · [Support](SUPPORT.md)

## Migration depuis le projet d’origine

Encore et ProsperoEden natif partagent le même identifiant PPSA99008 : ils ne s’installent pas indépendamment. Remplacez les fichiers de l’application au complet, sans supprimer les sauvegardes, préférences, jeux ou clés dans /data/prosperoeden. Sauvegardez tout ancien dossier assets/ avant la migration.

**Identifiant de l’application :** `PPSA99008`. **Application :** `/data/homebrew/PPSA99008/`. **Données persistantes :** `/data/prosperoeden/`.

[Migration depuis le projet d’origine — étapes détaillées](docs/i18n/INSTALL.fr-CA.md) · [Guide complet en anglais](INSTALL.md)

## Compatibilité et limites actuelles

Seul le micrologiciel PS5 13.60 a été testé sur une console réelle avec Encore. Les versions antérieures pourraient fonctionner, mais aucun minimum n’a été vérifié. Des saccades, retards du HUD, problèmes de commandes et blocages à la pause restent possibles. Une CI verte n’est pas un test matériel.

Le code en développement prend en charge les conteneurs NSP/XCI et expérimente NSZ/XCZ. Les chargeurs directs NRO/NSO/NCA/NAX/KIP exigent des fichiers complets; reconnaître une extension ne garantit pas le démarrage.

## Questions fréquentes

La Switch 2 relève d’une branche de recherche distincte et n’est pas compatible avec la version PS5 actuelle. La génération de trames et les mises à jour automatiques sont prévues, pas encore livrées.

Si l’interface demeure en anglais, choisissez Settings → Language et vérifiez l’installation complète de ui/lang/.

## Communauté et crédits

[Complete English reference](README.md) · [Settings](SETTINGS.md) · [Accessibility](ACCESSIBILITY.md) · [Troubleshooting](TROUBLESHOOTING.md) · [Switch 2 research](https://github.com/niakw/ProsperoEden-Encore/tree/research/ns2-ps5-compatibility) · [Roadmap](https://github.com/niakw/ProsperoEden-Encore/blob/feat/graphics-network-achievements/docs/ROADMAP_ENCORE_COLLAB_2026-10-25.md) · [Original project credits](README.md#credits) · [GPL-3.0-or-later](LICENSE).

Encore ne fournit aucun jeu, aucune clé et aucun micrologiciel propriétaire. Ne publiez pas de données privées dans les signalements.

> Cette traduction résume les informations essentielles. Le README anglais demeure la référence technique complète; les tests hôtes ne prouvent pas les performances sur PS5.
