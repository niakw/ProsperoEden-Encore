# R10 — Textures HD par IA : périmètre réel et distinction des mods

**Roadmap R10 — étude et spécification, non implémenté.**
Revue du 5 novembre 2026. La PR graphique #24 ne fournit pas de
moteur de génération des fichiers de textures par IA.

## Les quatre familles graphiques

- **R07 — Upscaling :** agrandir chaque image rendue avec FSR 1,
  SGSR, Lanczos, etc. Ne modifie pas les fichiers de textures du jeu.
  FSR 3.1 temporel reste non intégré.
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

**État :** installation de packs RomFS déjà disponible via Mods ;
**pipeline IA + conversion/validation des ressources R10 à faire.**
