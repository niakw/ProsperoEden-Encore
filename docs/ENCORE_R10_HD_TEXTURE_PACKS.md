# R10 — Textures HD par IA : périmètre réel et distinction des mods
**ARCHIVÉ / ABANDONNÉ le 6 novembre 2026 à la demande du projet.**
Aucune génération de packs textures HD par IA ne doit être développée
sur la base de cette étude. Le chargement normal des mods RomFS reste intact.
Le dernier chantier graphique est **R09 — Neural Rendering et upscaling IA
temps réel**, indépendant des textures stockées sur disque.


**Roadmap R10 — étude et spécification, non implémenté.**
Revue initiale du 5 novembre 2026 ; faisabilité approfondie le 6 novembre 2026. La PR graphique #24 ne fournit pas de
moteur de génération des fichiers de textures par IA.

## Les quatre familles graphiques

- **R07 — Upscaling :** agrandir chaque image rendue avec FSR 1,
  SGSR, Lanczos, etc. Ne modifie pas les fichiers de textures du jeu.
  FSR 3.1 temporel possède un backend Vulkan natif mais n’est pas raccordé au rendu invité.
- **R08 — Génération de frames :** MihawkGen, FSR3 FG optical flow,
  LSFG. Créer des images supplémentaires pour la présentation,
  sans générer de nouveaux fichiers de texture.
- **R09 — Neural Rendering AMD/Vulkan :** améliorer l'aspect visuel
  des visages, des matériaux ou de la lumière dans l'image rendue,
  **sans remplacer les fichiers de textures invités**. Recherche,
  aucun moteur runtime PS5 qualifié.
- **R10 — Textures HD IA :** créer de nouvelles versions haute résolution
  des **ressources de texture** du jeu avec un modèle autorisé
  (Real-ESRGAN ou équivalent), potentiellement hors console,
  puis les remettre dans le format réellement lu par le jeu.

## Pourquoi ne PAS inventer un autre dossier ou menu

**Les mods RomFS existants gèrent déjà le remplacement des textures
lorsqu'elles ont été converties au format attendu par le jeu.**

Exemple, dans les fichiers de jeux utilisés par Encore :

    mods/
      <TitleID>/
        Pack textures HD/
          romfs/
            <chemin identique au jeu>/
              <texture native au format du jeu>

L'activation se fait dans la fiche du jeu, **Mods**.
Aucune raison technique de réimplémenter un deuxième chargeur
de fichiers RomFS, un dossier textures/ ou une deuxième liste
d'activation juste pour des packs déjà compatibles.
Le code redondant précédemment ajouté a été **retiré de la branche
PR #24** et le sous-module vendor ré-épinglé à son état précédent.
Aucun mod installé n'a été supprimé ni modifié. La branche vendor
expérimentale n'est plus référencée dans cette PR.

## Ce qu'exige réellement la réalisation R10

1. **Sources autorisées** : l'utilisateur fournit ses textures
   légalement ; aucune redistribution de textures de jeux protégés.
2. **Upscaling de ressources par IA** : modèle ouvert à licence
   vérifiée, traitement de textures sur ordinateur si la PS5
   manque de marge compute/mémoire. Ce n'est ni du frame generation,
   ni un filtre de netteté de l'image finale.
3. **Conversion vers le format du jeu** : BNTX/BFRES lorsque
   appropriés, ASTC/BCn, dimensions, mipmaps, normales, alpha,
   sRGB, chemins exacts, version du jeu. Un PNG produit par l'IA
   n'est généralement pas utilisable directement comme texture.
4. **Packaging compatible RomFS** : l'export crée un
   **mod RomFS ordinaire**, découvert par le gestionnaire
   déjà intégré ; vérification des tailles, hachages et fallback.
5. **Validation** : coût mémoire, performances et qualité dans
   FC 27 et BOTW, sans régression NS1/NS2 ni artefact HUD.
   Ne pas activer un modèle de textures IA tant que ces points
   ne sont pas prouvés.

Un remplacement dynamique de textures dans le cache GPU
peut être une piste ultérieure, mais n'est pas nécessaire à
l'installation des packs RomFS et ne saurait se substituer à
la conversion sûre des ressources.

## Verdict de faisabilité — 6 novembre 2026

**Oui pour générer des textures HD par IA hors console et les charger
comme mods**, mais **non pour promettre un bouton « générer toutes les
textures du jeu en HD » directement sur PS5**. Les conteneurs et formats
du jeu sont le verrou principal, pas le modèle IA. Un mod RomFS qui
remplace un fichier ne garantit pas qu'une texture de dimensions
supérieures soit acceptée par les tables internes ou le moteur du jeu.

| Cas | Faisabilité | Technique prévue |
| --- | --- | --- |
| Diffuse/albedo/sprites isolés avec outil d'extraction et repack éprouvé | **Bonne**, sous tests | Upscale IA local + restauration alpha + mipmaps + repack du conteneur |
| Images en atlas / tableaux / couches / textures swizzlées | **Conditionnelle** | Métadonnées atlas/UV, niveaux et alignement doivent rester valides |
| Normal maps, roughness, metallic, AO, masques binaires | **Ne PAS passer au modèle photo générique** | Upsampling déterministe adapté aux données, renormalisation des normales ; seuils et alpha exacts |
| HUD, glyphes, cartes, textes, pixel art | **Au cas par cas** | Vectorisation/dessin spécifique ou nearest ; l'IA peut inventer des caractères |
| Ressource propriétaire / chiffrée / non re-packable | **Bloquée** | Aucun pack exporté sans preuve de round-trip exact |
| Génération dynamique en jeu sur PS5 | **Non qualifiée** | Compute/VRAM/latence imprévisibles, aucune promesse de FPS |

### Pipeline technique retenu (outil hôte, pas un deuxième chargeur)

1. **Inventaire après dump autorisé** : déterminer Title ID + version,
   fichier RomFS exact, conteneur (BNTX/BFRES ou autre), format GPU
   (ASTC, BCn, etc.), dimension, mipmaps, array layers, cubemaps, sRGB
   et usage (couleur/normale/masque/UI). Ne jamais inférer le type de
   texture à partir de la seule extension.
2. **Round-trip conservateur obligatoire** : extraction → conversion
   *sans IA* → repack → décodage/contrôle du résultat. Si le convertisseur
   ne préserve pas le conteneur, les indices, l'alignement, l'alpha, les
   dimensions imposées ou les métadonnées, **arrêt**.
3. **Upscaling local sur Mac/PC** : démarrer avec Real-ESRGAN
   (BSD-3-Clause pour le dépôt ; vérifier séparément la licence des
   poids téléchargés), modèle général pour photos/albedo ou modèle
   anime pour textures peintes. Traitement par tuiles possible mais
   comparer les coutures ; ne pas appliquer de débruitage agressif
   aux détails de gameplay, palettes ou glyphes. Les traitements des
   canaux alpha, normales et masques restent **séparés et déterministes**.
4. **Reconstruction complète** : mipmaps gamma/sRGB corrects,
   conservation des canaux, compression native compatible ASTC/BCn,
   repack par format avec taille et version supportées. Vérifier
   l'image décompressée après recompression ; éviter la conversion
   globale de tous les assets en RGBA8 décompressé.
5. **Livraison contrôlée** : manifest avec hash SHA-256 de l'original
   et du remplaçant, modèle/poids et paramètres, format, dimensions
   et taille estimée ; export en
   `mods/<TitleID>/<NomPack>/romfs/<chemin jeu>`.
   Activation et désactivation **uniquement dans Mods**.
6. **Qualification PS5** : comparer un même plan en jeu avec/sans
   pack, captures fixes et caméra mobile, RAM/VRAM, chargement et
   frametime. Retour instantané au mod désactivé si artefacts,
   stutter, corruptions ou crash. Aucun remplacement de texture
   shader/CPU à la volée dans ce premier périmètre.

### Budget VRAM (ordre de grandeur indépendant de la compression)

Une texture carrée **1024² RGBA8** consomme environ **4 Mio** sans
mipmaps ; en **4096² (x4 largeur et hauteur)**, elle monte à **64 Mio**
sans mipmaps et environ **85,3 Mio** avec une chaîne complète de
mipmaps (≈4/3 du niveau principal). L'aire et donc la mémoire brute
augmentent de **16×**, pas de 4×. Les formats blocs ASTC/BCn réduisent
fortement la taille, mais le ratio d'augmentation reste proche de
16× à format et nombre de niveaux comparables. Il faudra un
**plafond de budget total par pack et par session**, pas seulement
un plafond par texture ; l'impact réel du texture cache varie selon
la scène et le moteur. Les détails ajoutés peuvent être à peine
visibles à l'écran : sélection de textures prioritaires plutôt
que tout traiter en 4×.

### Pistes consultées

- Real-ESRGAN : `https://github.com/xinntao/Real-ESRGAN` ;
  modèles général et anime, exécution hors ligne avec
  `Real-ESRGAN-ncnn-vulkan`, gestion des images avec alpha
  dans le pipeline Python.
- Outils de conteneurs Switch : `https://github.com/quatric/nintoolbox`
  documente des formats comme BNTX et ASTC ; **leur capacité
  d'extraction ne prouve pas le repack compatible avec chaque jeu**.
- Aucun de ces projets ne prouve pour le moment un remplacement
  universel NS1/NS2, ni les performances PS5 ; ce sont des pistes
  d'outillage hôte, pas des dépendances du renderer.

**Décision : R10 faisable de manière ciblée avec packs RomFS et
conversion prouvée, pas de génération IA automatique en jeu pour
l'instant.** R10 reste ouvert (pas de pipeline fonctionnel ajouté
dans cette PR). Les essais de génération et de conversion se font
hors du chemin NS1/NS2 stable.

**État :** installation de packs RomFS déjà disponible via Mods ;
**pipeline IA + conversion/validation des ressources R10 à faire.**
