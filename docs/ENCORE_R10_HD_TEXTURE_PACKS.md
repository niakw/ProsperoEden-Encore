# Eden Encore — R10 : packs de textures HD compatibles RomFS

**État au 5 novembre 2026 : premier parcours fonctionnel basé sur le gestionnaire
de mods existant ; R10 n'est pas clos.** Aucun modèle IA, aucune texture
protégée, aucun binaire Windows et aucun remplacement dynamique GPU ne sont
embarqués dans Eden Encore.

## Ce qui fonctionne sans toucher au renderer PS5

Le gestionnaire de mods d'Eden sait déjà appliquer les fichiers RomFS fournis
par jeu, via le même Title ID 16 chiffres hexadécimaux que les ROMs.
Le launcher sait afficher ces mods et activer ou désactiver chacun d'eux,
avec application au prochain lancement. Une texture HD **déjà reconvertie
dans le format RomFS attendu par son jeu** peut donc être fournie comme
mod standard. Le nouveau préparateur ne remplace pas une texture inconnue
dans le cache Vulkan : il transforme un dossier de fichiers de jeu
compatibles en pack RomFS que l'émulateur sait réellement appliquer.

## Préparer un pack sur Mac ou PC

1. Préparer vous-même, légalement, des fichiers RomFS de remplacement.
   La simple sortie PNG/WebP d'un réseau IA ne suffit généralement pas :
   les jeux Switch utilisent des conteneurs et des formats de textures
   spécifiques (BNTX/BFRES/etc.). La reconversion compatible avec le
   titre est indispensable, en dehors de la PS5.
2. Placer ces fichiers dans un dossier dont l'arborescence **reproduit
   exactement** les chemins de RomFS du jeu (par exemple
   `source-romfs/Model/grass.bntx`).
3. Depuis un checkout d'Eden Encore, exécuter :

```bash
python3 tools/graphics/package-hd-textures.py \
  --title-id 0100ABCD00001000 \
  --source-romfs /chemin/vers/source-romfs \
  --mods-root /chemin/vers/fichiers-jeux/mods \
  --name "Terrain HD"
```

Le résultat est un dossier prêt à être découvert par le gestionnaire
de mods, sans toucher au contenu original :

```text
mods/
  0100ABCD00001000/
    HD Textures - Terrain HD/
      encore-hd-textures.json
      romfs/
        Model/
          grass.bntx
```

Le manifeste contient le Title ID, la liste exacte des fichiers,
leur taille et leur SHA-256. Il sert à l'inspection et la reproductibilité ;
**Eden n'interprète pas ce manifeste comme une garantie de format valide**.
L'application lit les données de `romfs/` via le patch manager existant.

Dans le launcher, ouvrir la fiche du jeu → **Mods** → sélectionner
`HD Textures - Terrain HD` → activer. La désactivation d'un mod retire
son overlay lors du prochain lancement, sans effacer les originaux.
Les mods fonctionnent au cas par cas : un pack fait pour une autre
version de jeu peut être incompatible ou inutilisable.

## Contrôles réalisés par l'outil

- Identifiant Title ID obligatoire et nom de pack contrôlé.
- Refus des liens symboliques, des chemins excessivement profonds,
  des fichiers vides, du dépassement des budgets disque et des
  noms de fichiers en collision insensible à la casse.
- Refus d'écraser un pack déjà présent. Le travail s'effectue
  dans une zone temporaire hors du Title ID, avant publication
  atomique, afin que l'interface ne découvre pas un pack partiel.
- Copie par blocs bornés ; SHA-256 et taille consignés et vérifiés.
- Cinq scénarios de tests hôtes, incluant la compilation du vrai
  lecteur de dossier `Eden::Mods::List` et sa reconnaissance
  du dossier produit comme mod `kFiles`.

Le budget par défaut est de 2 Gio pour un pack et 512 Mio par
fichier (bornes maximales limitées à 8 Gio et 2 Gio).
Ces limites concernent **l'espace disque**, pas la mémoire GPU.

## Ce que R10 ne fait pas encore

- **Aucun upscale IA automatique sur PS5** : Real-ESRGAN ou autre
  devrait être utilisé hors console, avec modèles et images autorisés.
- **Pas de remplacement universel des textures GPU** : aucun
  identifiant de texture/TIC/TSC, cache GPU, quantification ASTC/BCn
  ou signature de surface n'est intercepté ici.
- **Pas de validation générale des dimensions/formats GPU** :
  elles dépendent du titre et des conteneurs du jeu.
- **Pas de promesse de qualité ou de performances** sans essais
  FC27/BOTW et mesures mémoire ; les packs massifs peuvent alourdir
  les accès disque et la mémoire invitée.

R10 reste ouvert pour la conversion vérifiée des formats spécifiques,
le budget GPU/caches et une éventuelle substitution dynamique
uniquement si elle est sémantiquement sûre pour NS1 et NS2.
