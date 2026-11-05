# Eden Encore — R10 : bibliothèque indépendante de textures HD

**5 novembre 2026 — PR #24 et branche vendor dédiée.**
**État : fonctionnalité RomFS HD intégrée en source, vérifiée sur hôte ; non validée sur PS5.**

## Une distinction technique réelle par rapport aux mods

Les textures HD possèdent désormais une racine séparée sous le dossier des
fichiers de jeu sélectionné. Elles ne doivent **plus** être installées dans
mods/, ni activées depuis le menu Mods.

    <racine-des-jeux>/
      roms/
      mods/
        0100ABCD00001000/
          Patch 60 FPS/
            exefs/...
      textures/
        0100ABCD00001000/
          Terrain HD/
            encore-hd-textures.json
            romfs/
              Model/
                grass.bntx

Le chargeur PS5 maintenu dans vendor/encore-active/eden-core lit directement
textures/<TitleID>/<pack>/romfs, pour les fichiers de données des jeux.
**Aucune copie, aucun lien symbolique et aucune insertion physique dans
mods/.** Le backend de remplacement reste un overlay RomFS, ce qui
évite d'ajouter un second moteur inutile pour les fichiers natifs.
Les mods ordinaires peuvent toujours appliquer des patches ExeFS,
des cheats et des remplacements RomFS ; les textures HD, elles,
**n'injectent jamais de code ExeFS ni de cheats**.

Chaque pack HD doit avoir un manifeste v1 correspondant au vrai Title ID.
Le chargeur ne le traite que pour les enregistrements RomFS Program/Data.
Les mods ordinaires ont priorité en cas de conflit de fichiers.
Les dossiers absents/malformés sont ignorés ; le jeu original demeure
la source de secours.

## Activation par jeu, séparée de Mods

Dans le launcher : **Fiche du jeu → HD textures → pack → Activer**.
Le menu affiche le nombre de fichiers, la taille et l'état individuel.
Les nouveaux packs sont **désactivés par défaut**. Leur activation
est mémorisée par Title ID dans le réglage indépendant
hd_textures_on ; mods_off et l'interrupteur Mods n'y changent rien.
Le mode Safe Launch désactive aussi les textures HD uniquement
pour la session, sans effacer les choix.

Lorsque le dossier n'existe pas, dans le menu HD textures, Carré
peut créer le dossier textures/<TitleID>/. Il est également possible
de copier manuellement un pack déjà préparé dans ce dossier.
Les changements prennent effet au **prochain lancement du jeu**.

## Préparer un pack sur Mac ou PC

Préparer légalement un ensemble de fichiers **déjà reconvertis au format
attendu par les chemins RomFS du jeu**. Un PNG généré par Real-ESRGAN
n'est pas automatiquement un BNTX/BFRES compatible : la conversion
et l'édition des ressources spécifiques au jeu doivent se faire
hors PS5.

Exemple (Title ID fictif, à remplacer) :

    python3 tools/graphics/package-hd-textures.py
      --title-id 0100ABCD00001000
      --source-romfs /chemin/romfs-compatible
      --textures-root /chemin/fichiers-jeux/textures
      --name "Terrain HD"

L'outil n'accepte **que** une racine nommée textures. Il refusera
expressément mods/. Il écrit le manifeste (SHA-256 et tailles),
copie par blocs dans un dossier temporaire, puis publie le pack
atomiquement. Un pack préexistant ne sera jamais écrasé.
Budgets par défaut : 2 Gio par pack et 512 Mio par fichier.
Les limites portent sur le disque, pas sur la VRAM.

Les PNG/JPEG/WebP intermédiaires sont refusés. L'option
--allow-native-images est réservée aux rares jeux qui lisent
réellement ces formats depuis leur RomFS. Elle ne convertit rien.

## Contrôles et limites

- Six tests du préparateur, dont refus de fichiers malformés,
  liens symboliques et écrasement.
- Compilation du lecteur C++ de textures HD + test par Title ID
  et de la liste indépendante hd_textures_on ; le scanner de Mods
  n'énumère pas ces packs.
- Audit statique du point d'insertion du patch manager maintenu
  dans le vendor, avec priorité des mods, protection contre les
  manifestes invalides et filtrage des répertoires.
- Pas de build PS5 qualifié ni de mesure de VRAM ou FPS sur console.

### Ce que R10 ne fait PAS encore

Aucun upscale IA automatique sur PS5, aucune génération ni conversion
des formats natifs de jeu, aucune interception de signatures de
textures dans le cache Vulkan, aucun téléchargement de packs tiers.
Le mécanisme traite **uniquement des remplacements RomFS déjà valides**.
Le moteur de substitution directe des textures GPU, s'il devient
nécessaire, devra être conçu avec garde-fous NS1/NS2, budgets de
cache et preuves console distinctes. Cela ne se résume pas au
changement de dossier.

**Anciens packs déjà rangés dans mods/ :** ils restent des mods
ordinaires. Aucune migration automatique destructrice. Reconditionner
avec l'outil ci-dessus pour profiter de la gestion HD indépendante.
