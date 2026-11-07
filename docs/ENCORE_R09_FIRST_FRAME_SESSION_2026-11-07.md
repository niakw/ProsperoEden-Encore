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

## Raccord réel au renderer (7 novembre, `main`)

Le chemin `headless/vulkan_present_layer_r24.cpp::Layer::ConfigureDraw`
est désormais intégré : il charge un modèle utilisateur choisi
explicitement (`original.nrmodel`/`compact.nrmodel` ou les noms
issus de l'extracteur), utilise le plan natif correspondant, prépare une
image Vulkan RGBA32F dédiée, appelle `NrRdna2FrameSession::Record`,
puis présente le résultat **uniquement si** le réseau a accepté son
enregistrement. En cas de refus, l'image originale du jeu est conservée.

L'admission est actuellement limitée à une source effective **1920×1080**,
sans recadrage, AA ni autre upscaler simultané. Le rendu accéléré est
admis selon le contrat de capture ; la fidélité du format et des guides
neuronaux du jeu reste à établir. Les textures et propriétaires GPU
vivent jusqu'à la retraite du tick associé à leur slot. En particulier,
la vue de sortie est détruite avant son image, et une initialisation
refusée sans dispatch libère l'image provisoire.

La CI hôte R09 couvre le code C++ maintenu et le présentateur,
les contrats du graphe, les ABI SPIR-V et un vrai aller-retour
texture→composition→image sur Vulkan Lavapipe.

**Ce qui manque pour déclarer la base DLSS-NR fonctionnelle** :
une exécution GPU de la **totalité** des modèles Original et Compact
avec de vrais poids légalement fournis, la lecture et comparaison
numérique de leurs images à une référence indépendante, ainsi que la
validation de la sémantique des entrées 16 canaux. Le test Vulkan
actuel de composition isolée ne démontre pas cette inférence.
Le chemin source est conçu pour une première image sans historique ;
la persistance multi-frame, les vecteurs de mouvement et l'historique
temporel complet restent hors de la base validée. Aucun test PS5
utilisateur ni build global PS5 demandé. DLSS-NR reste **OFF par défaut**.

Le chantier R09 et la roadmap moteur P0–P4 (issue #15) sont distincts.
