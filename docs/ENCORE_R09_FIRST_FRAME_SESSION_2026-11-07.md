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
texture→composition→image sur Vulkan Lavapipe. Elle exécute aussi le
shader **réel** d'entrée 16 canaux FP16 avec comparaison GPU/CPU au pixel
sur un raster complet 1920×1080, puis deux projections **réellement
exécutées sur Vulkan** avec des matrices one-hot de contrôle sur les
rasters 4×3 et 80×45 : entrée FP16 C16→FP8 C32 et sortie brute
FP16 C32→FP16 C16. Sur ces petits rasters, le composeur consomme bien
la **sortie GPU du shader de projection C16**, pas un faux résultat
prérempli. Sur le raster complet 1080p, seule la tête de contrôle
synthétique est utilisée afin de garder le test de lecture de 2 073 600
pixels raisonnable. Un banc GPU supplémentaire
(`tools/graphics/r09_vulkan_fswin_smoke.cpp`) exécute également le
**vrai shader FSwin Dense3 C32**, sur 64 tokens x 32 canaux, dans ses
deux sorties E4M3FN et RAW FP16, avec une matrice identité contrôlée et
une comparaison octet-à-octet des 2 048 valeurs. Le test passe sur
Vulkan Lavapipe (CI R09 #42400649979). Ce sont des tests numériques
réels du shader FSwin, pas uniquement des vérifications SPIR-V.

Le présentateur refuse maintenant une allocation absente de l'image
RGBA32F ou de sa VkImageView avant toute initialisation de session,
avec retour conservateur à l'image originale du jeu.

**Cela ne démontre PAS l'inférence du réseau entier** : les blocs
FSwin, Split-Swin et ViT n'ont toujours pas été parcourus de bout en
bout avec des poids authentiques et un oracle d'image indépendant.

Le vérificateur hôte `tools/graphics/r09_verify_model_pack.py` apporte
un deuxième verrou indépendant : les empreintes publiques de **599**
tenseurs Original / **255** Compact sont conservées dans
`tools/graphics/r09_weights_{original,compact}.sha256`. La CI en
contrôle les noms contre le manifest C++, puis exerce le vérificateur
sur des paquets synthétiques valides, corrompus et incomplets.
L'outil n'impose **aucune taille totale inventée** au fichier :
l'extracteur amont aligne les offsets de tenseurs à 256 octets,
mais ce sont les noms, les bornes et les empreintes individuelles
qui prouvent l'intégrité. Les tests comprennent le dernier
tenseur de taille variable, la fin de fichier tronquée, l'inventaire
incomplet et le fichier comportant du bourrage final.

## Admission native précoce et intégrité du cache (7 novembre)

Le raccord `headless/nr_dll_launch_preflight.h` effectue la
conversion de la DLL personnelle, si nécessaire, **au lancement du
jeu et avant tout rendu Vulkan**. Le présentateur ne décompresse
plus la DLL pendant `ConfigureDraw`, ce qui élimine les interruptions
de rendu dues à la lecture de 165 Mo de PE et l'écriture du pack.

La réutilisation de `original.nrmodel` est autorisée seulement
après vérification des 599 empreintes SHA-256 publiques de ses
tenseurs. Le contrôle symétrique Compact inclut 255 empreintes,
mais la DLL utilisateur examinée ne contient pas les poids Compact.
Un cache synthétique avec 599 noms et tailles valides mais des
octets de poids incorrects doit être rejeté. Les fichiers privés
et les poids ne sont pas publiés dans la CI.

**Non qualifié** : l'exécution de la totalité des 152 opérations
Original sur GPU avec une image de sortie comparée à une référence
indépendante. Les captures R09 existantes proviennent d'une chaîne
de test avec poids de contrôle et ne doivent pas être présentées
comme « avant / après DLSS Original ».

## Alerte d'installation manquante (même comportement que LSFG)

Le menu global et la fiche vidéo par jeu affichent un message
d'erreur quand un mode DLSS-NR est sélectionné sans la DLL personnelle
`/data/prosperoeden/user/dlssnr/nvngx_dlssnr.dll`.
Ils conservent la préférence précédente. Les contrôles de
compatibilité Vulkan/AA/upscaling restent indépendants. Un DLSS
précédemment configuré ne s'active pas silencieusement lors
d'un lancement si la DLL a été supprimée : les diagnostics
signalent le manque et le renderer normal prend le relais.
Cf. `ENCORE_R09_MODEL_FILES_2026-11-07.md`.

## Contrat utilisateur prioritaire — une seule DLL, zéro extraction manuelle

La seule entrée à demander à l'utilisateur est **`nvngx_dlssnr.dll`**.
Eden Encore doit détecter et importer localement les ressources de
cette DLL, vérifier les tenseurs et maintenir les packs internes
sans intervention de l'utilisateur. Ne pas lui demander de
`dlssnr.bin`, `compact.nrmodel`, de scripts Python ni d'une autre DLL.
La DLL reçue contient `WEIGHTS_HT` et aucune ressource
`WEIGHTS_CC_SMALL_FP8` : valider Original, signaler Compact
indisponible plutôt que simuler ses poids. L'import natif Original depuis cette DLL est désormais raccordé :
le moteur crée automatiquement son propre cache `NRMODEL1`
s'il n'existe pas déjà. Voir le commit `2bfbeae`.
Cela ne certifie pas encore la fidélité d'une image calculée par
le graphe complet sur GPU.
Voir `ENCORE_R09_MODEL_FILES_2026-11-07.md`.

## Entrée requise pour la validation complète — DLL NVIDIA utilisateur

L'extracteur public `Overclockers/DLSSNR-AMD/linux/package/model-tools/extract_model.sh`
lit les ressources du PE Windows **sans charger ni exécuter la DLL** et
ne produit les modèles `NRMODEL1` que lorsque ses poids correspondent
à toutes les empreintes SHA-256 publiées.

- `nvngx_dlssnr.dll` **310.9.16.0**, SHA-256 complet du DLL
  `2bc19bc09a7b89dd44f73e2ac0108fcc586e2154bdd0830f242f4f040e28789f` :
  produit Original `dlssnr.bin` **et** Compact `dlssnr-small.bin`.
- `nvngx_dlssnr.dll` **310.8.0.0**, SHA-256 complet du DLL
  `e16bcf15e16e13f527491cdf7845b2fe6521a738d8f7c9c721866a8496e1fc8e` :
  produit **Original uniquement**.

Une DLL de nom ou de version identique mais de SHA différent n'est pas
automatiquement réputée authentique. Ne jamais la charger ni ignorer
les refus de l'extracteur. Conserver les DLL et poids hors des dépôts
publics et des artifacts GitHub Actions.

Après extraction dans un environnement hôte isolé, contrôler chacun
des packs avec les commandes ci-dessous. L'intégrité et l'inférence
sont deux preuves distinctes : ne pas déclarer le moteur terminé
sans exécution du graphe entier et sortie numérique indépendante.
Aucune manipulation de la console PS5 n'est requise pour ce lot.

Pour un paquet **réellement extrait et détenu par l'utilisateur** :

```sh
python3 tools/graphics/r09_verify_model_pack.py --check-reference
python3 tools/graphics/r09_verify_model_pack.py --variant original --model /chemin/vers/dlssnr.bin
python3 tools/graphics/r09_verify_model_pack.py --variant compact --model /chemin/vers/dlssnr-small.bin
```

Un statut `R09_*_AUTHENTIC_PACK_SHA256_PASS` prouve seulement
l'intégrité de ce paquet vis-à-vis des empreintes référencées ;
il ne prouve pas l'exécution GPU ni la fidélité des images produites.
**Aucun poids NVIDIA n'est embarqué ni publié.** Les références sont
les inventaires SHA-256 publics du dépôt
`Overclockers/DLSSNR-AMD`, répertoire `linux/package/model-tools`.
Ce vérificateur est un outil hôte distinct : l'émulateur ne l'exécute
pas automatiquement à chaque frame.

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
