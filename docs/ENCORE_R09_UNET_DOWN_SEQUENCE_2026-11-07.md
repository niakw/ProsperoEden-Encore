# R09 — Descente U-Net Vulkan native (7 novembre 2026)

**Statut : enregistrement des quatre niveaux descendants intégré en source ; validation hôte à vérifier après la CI. Ce n'est pas un rendu DLSS-NR complet.**

Le vendor expose `NrRdna2UNetDownSequence`. Il consomme un raster FP8 C32 **à demi-résolution**, produit par un futur prébloc natif (le proxy C32 pleine résolution actuel n'est pas équivalent), et ordonnance sur un scheduler Vulkan commun :

1. FSwin C32, export skip 32 canaux et downsample appris vers C64.
2. FSwin C64, export skip 64 canaux et downsample appris vers C128.
3. FSwin C128, export skip 128 canaux et downsample appris vers C256.
4. FSwin C256, export skip 256 canaux et downsample appris vers un raster C512 destiné au bottleneck Split-Swin.

Trois `NrRdna2FSwinLevelLink` préparent les transitions intermédiaires. `NrRdna2UNetSkipCache` exporte les quatre skips, sans faire enregistrer les FSwin deux fois. Les dimensions, axes raster transposés du plan natif, limites 256 Mio, canaux, ordre des blocs et buffers font l'objet d'un contrat hôte testé sur les plans Original et Compact. La couche de pilotage n'enregistre qu'une fois l'ensemble ; les échecs partiels de `RecordProducer` et des upsample links ne sont plus silencieusement rejouables.

**Non intégré :** prébloc Swin + premier downsample 1920×1080 → C32 960×540 (raster canonique 540×960), connexion C512 → Split-Swin / ViT, reconstruction U-Net ascendante, gains de modèle, postbloc, compositing couleur et présentateur. Pas de chargement automatique des poids ni de rendu console. Cette étape ne rend aucun DLSS-NR activable par défaut.

**Validation attendue :** GCC/Clang+UBSan du contrat pur et compilation syntaxique Clang des propriétaires C++ réels (sans SDK PS5). Ce résultat ne peut pas remplacer P5.
