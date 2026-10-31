<table width="100%">
  <tr><td align="center">
    <strong>🌐 LANGUAGES</strong> &nbsp; · &nbsp; <a href="README.md">English</a> &nbsp; · &nbsp; <a href="README.md">English UK</a> &nbsp; · &nbsp; <a href="README.zh-Hans.md">简体中文</a> &nbsp; · &nbsp; <a href="README.zh-Hant.md">繁體中文</a> &nbsp; · &nbsp; <a href="README.es-419.md">Español LatAm</a> &nbsp; · &nbsp; <a href="README.es.md">Español ES</a> &nbsp; · &nbsp; <a href="README.fr.md">Français</a> &nbsp; · &nbsp; <strong>Français CA</strong> &nbsp; · &nbsp; <a href="README.pt-BR.md">Português BR</a><br>
    <a href="README.pt-PT.md">Português PT</a> &nbsp; · &nbsp; <a href="README.ru.md">Русский</a> &nbsp; · &nbsp; <a href="README.de.md">Deutsch</a> &nbsp; · &nbsp; <a href="README.ja.md">日本語</a> &nbsp; · &nbsp; <a href="README.ko.md">한국어</a> &nbsp; · &nbsp; <a href="README.it.md">Italiano</a> &nbsp; · &nbsp; <a href="README.th.md">ไทย</a> &nbsp; · &nbsp; <a href="README.pl.md">Polski</a> &nbsp; · &nbsp; <a href="README.nl.md">Nederlands</a> &nbsp; · &nbsp; <a href="LANGUAGES.md"><strong>All languages</strong></a>
  </td></tr>
</table>

<table width="100%">
  <tr>
    <td width="21%" align="center" valign="middle"><a href="README.md"><img src="assets/icon0.png" alt="Prospero.Eden Encore logo" width="148"></a></td>
    <td width="79%" align="left" valign="middle">
      <h1>Prospero.Eden Encore</h1>
      <p><strong>L’émulation communautaire PS5 conçue pour le salon</strong></p>
      <p>Encore est une branche communautaire indépendante avec un lanceur à la manette, une bibliothèque de jeux, des réglages vidéo et des outils de diagnostic. Ce n’est pas un produit officiel de Sony ou de Nintendo.</p>
      <p><kbd>Firmware 13.60 · testé sur PS5</kbd> &nbsp; <kbd>Vulkan + OpenGL</kbd> &nbsp; <kbd>Interface TV</kbd> &nbsp; <kbd>Dynarmic</kbd></p>
    </td>
  </tr>
</table>

<table width="100%">
  <tr>
    <td align="center"><a href="https://github.com/niakw/ProsperoEden-Encore/releases"><strong>Télécharger</strong></a></td>
    <td align="center"><a href="docs/i18n/INSTALL.fr-CA.md"><strong>Installer</strong></a></td>
    <td align="center"><a href="#getting-started"><strong>Démarrer</strong></a></td>
    <td align="center"><a href="#compatibility"><strong>Compatibilité</strong></a></td>
    <td align="center"><a href="#faq"><strong>FAQ</strong></a></td>
    <td align="center"><a href="TROUBLESHOOTING.md"><strong>Aide</strong></a></td>
    <td align="center"><a href="https://github.com/niakw/ProsperoEden-Encore/blob/feat/graphics-network-achievements/docs/ROADMAP_ENCORE_COLLAB_2026-10-25.md"><strong>Roadmap</strong></a></td>
  </tr>
</table>

<a id="getting-started"></a>
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

<a id="compatibility"></a>
## Compatibilité et limites actuelles

Seul le micrologiciel PS5 13.60 a été testé sur une console réelle avec Encore. Les versions antérieures pourraient fonctionner, mais aucun minimum n’a été vérifié. Des saccades, retards du HUD, problèmes de commandes et blocages à la pause restent possibles. Une CI verte n’est pas un test matériel.

Le code en développement prend en charge les conteneurs NSP/XCI et expérimente NSZ/XCZ. Les chargeurs directs NRO/NSO/NCA/NAX/KIP exigent des fichiers complets; reconnaître une extension ne garantit pas le démarrage.

<a id="faq"></a>
## Questions fréquentes

La Switch 2 relève d’une branche de recherche distincte et n’est pas compatible avec la version PS5 actuelle. La génération de trames et les mises à jour automatiques sont prévues, pas encore livrées.

Si l’interface demeure en anglais, choisissez Settings → Language et vérifiez l’installation complète de ui/lang/.

## Communauté et crédits

[Complete English reference](README.md) · [Settings](SETTINGS.md) · [Accessibility](ACCESSIBILITY.md) · [Troubleshooting](TROUBLESHOOTING.md) · [Switch 2 research](https://github.com/niakw/ProsperoEden-Encore/tree/research/ns2-ps5-compatibility) · [Roadmap](https://github.com/niakw/ProsperoEden-Encore/blob/feat/graphics-network-achievements/docs/ROADMAP_ENCORE_COLLAB_2026-10-25.md) · [Original project credits](README.md#credits) · [GPL-3.0-or-later](LICENSE).

Encore ne fournit aucun jeu, aucune clé et aucun micrologiciel propriétaire. Ne publiez pas de données privées dans les signalements.

> Cette traduction résume les informations essentielles. Le README anglais demeure la référence technique complète; les tests hôtes ne prouvent pas les performances sur PS5.
