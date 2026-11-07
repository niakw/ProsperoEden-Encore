# R09 — modèle complet en session first-frame

Date : 7 novembre 2026. Travaux sur les deux `main`.

`NrRdna2FrameSession` possède maintenant le pack utilisateur
`NRMODEL1`, le plan natif exact Original (152 instructions) ou
Compact (76), ainsi que les ressources GPU de son **premier passage**.
Il instancie les huit segments FSwin en identifiant leurs frontières
plutôt qu'en codant leurs index de blocs, puis initialise quatre
profondeurs U-Net, les deux runs Split-Swin, huit ViT, le décodeur
C1024→C512, la montée U-Net et le postbloc appris.

Cette classe alloue les tampons typés dans le même `MemoryAllocator`
et prépare en amont la lecture d'une véritable texture image
du jeu, sa projection en 16 caractéristiques FP16 et sa sortie
normalisée vers une image RGBA32F Vulkan à échantillonner dans le
moteur de présentation.

**Limites et règles de sûreté** : le modèle n'est pas inclus,
la source et l'image cible restent détenues par le renderer ; format,
orientation, taille, budget mémoire (3 GiB d'allocations
externes), maxima de buffers et aliasages sont vérifiés. Aucun
dispatch n'est fait pendant `Initialize`. `Record` est à usage
unique : le renderer doit conserver les ressources jusqu'au tick
GPU complété, surtout après un échec partiel.

Cette classe est une **tentative d'assemblage du réseau en source**.
Le passage de compilation Clang doit confirmer son intégration ;
l'exécution modèle réelle sur GPU n'est pas démontrée sans un
véritable pack utilisateur. La copie vers le présentateur
`Layer::ConfigureDraw`, la gestion multi-frame (l'objet étant
single-use), la conservation des historiques et les données de
mouvement sont encore **à intégrer**. Ne pas activer le réglage
DLSS-NR par défaut ni qualifier la fonctionnalité de terminée
avant ces preuves.

Pas de build PS5 global, branche ou PR.
