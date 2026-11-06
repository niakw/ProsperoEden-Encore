# R09 — Trois profils A4K et DLL NVIDIA fournies par l'utilisateur

**6 novembre 2026 | PR #24 DRAFT | aucune validation PS5 console**

## Première implémentation : véritable réseau neuronal spatial

Le vendor contient désormais la source MIT du réseau
[bloc97/Anime4K](https://github.com/bloc97/Anime4K),
**Anime4K v4.0 3DGraphics Upscale CNN x2 US**, spécialement entraîné
pour les graphismes 3D plutôt que le filtre animé générique.
Révision 7684e9586f8dcc738af08a1cdceb024cc184f426, SHA-256 du
modèle source ccfd16fa65908fbafe27114cf65ddc043bc746d4086716c2a85e97a283d9fe5e.

Le convertisseur dans vendor/encore-active/eden-vulkan/r09_anime4k_3d
conserve exactement les poids MIT, produit quatre kernels compute :
trois convolutions et une reconstruction subpixel x2. Source épinglée
par SHA-256. glslangValidator, spirv-val et spirv-dis valident les
quatre SPIR-V et leurs bindings Vulkan au moment du build sur hôte.

Le backend anime4k_3d.cpp effectue les quatre dispatchs, crée deux
surfaces intermédiaires RGBA16F réutilisables et une sortie x2 par
frame en vol. Les descripteurs et barrières sont enregistrés dans le
scheduler Vulkan déjà existant. L'alpha du jeu reste intact.
Aucune DLL Windows, modèle distant ni modification des textures ROM.

Trois profils réels sont proposés dans le même réglage Upscaling,
global et par jeu, avec des noms simples précédés de A4K :

| Indice persisté | Libellé utilisateur | Moteur Vulkan |
|---|---|---|
| 7 | **A4K — Détails améliorés** | CNN v4 3D ×2, 4 passes |
| 8 | **A4K — Image adoucie** | CNN Restore Soft 4 passes puis CNN 3D ×2 4 passes, soit 8 |
| 9 | **A4K — Image nettoyée** | CNN Upscale+Denoise v3.2 ×2, 5 passes |

Les identifiants historiques 0-6 sont inchangés. Le moteur
Anime4K3D sélectionne trois graphes de traitement distincts,
conserve une sortie et des surfaces de convolution séparées,
préserve le canal alpha et traite des images GPU indépendantes
par frame en vol. Les modèles MIT supplémentaires sont épinglés
par SHA-256 ; 13 shaders SPIR-V sont compilés sur hôte et validés
par glslangValidator, spirv-val et une vérification des bindings.
Un test vérifie les trois graphes, les sources épinglées et les
libellés identiques dans les paramètres du launcher.

Vulkan uniquement, avec repli Bilinear sur OpenGL, ratio différent
de ×2, crop partiel, format incompatible ou budget mémoire dépassant
384 Mio. La préférence utilisateur est conservée lors du repli.

**Validation** : shaders compilés, ABI vérifiée, backend et
présentateur compilés syntaxiquement sur hôte ; test de graphes passé.
**Pas encore de build PS5 complet, de capture A/B ni de mesure VRAM ou
temps GPU : aucun des trois profils n'est qualifié sur console.**

## Alternatives récentes à analyser après A/B

- [TianZerL/Anime4KCPP](https://github.com/TianZerL/Anime4KCPP) :
  v3.2, modèles ACNet et ARNet modernisés, ArtCNN et FSRCNNX.
  Backend CPU/OpenCL/CUDA ; un port Vulkan PS5 resterait nécessaire.
- [igv/FSRCNN-TensorFlow](https://github.com/igv/FSRCNN-TensorFlow) :
  modèles FSRCNNX x2 RGBA16F. Comparer coût/qualité/licences.
- ArtCNN intégré à Anime4KCPP : comparer la fidélité des détails 3D,
  le rendu du texte, l'anime et les scènes réalistes, sans promettre
  qu'un CNN orienté animation améliore toujours les visages ou l'HDR.

## Proposition de l'utilisateur : fournir le fichier NVIDIA

La démarche existe dans
[mochizuki0323/DLSSNR-AMD](https://github.com/mochizuki0323/DLSSNR-AMD) :
l'installeur accepte une DLL possédée par l'utilisateur au lieu de
redistribuer les poids NVIDIA. Différence décisive :
- nvngx_dlss.dll : DLSS Super Resolution (SR).
- nvngx_dlssnr.dll : DLSS Neural Rendering (NR), versions 310.8.0
  et 310.9.16 reconnues par les portages AMD consultés.

**Architecture envisagée, non intégrée** : import local facultatif,
reconnaissance de version et empreintes, contrôle du droit d'usage ;
ni inclusion du binaire/propriétés NVIDIA dans nos releases,
ni exécution de DLL Windows sur PS5. Après vérification juridique
et matérielle seulement, un noyau Vulkan RDNA2/PS5 distinct pourrait
exploiter des modèles légalement utilisables. Un simple modèle fourni
par le client ne transforme pas une DLL en moteur GPU compatible.

**Apporter soi-même la DLL n'est pas une immunité juridique.**
La [licence NVIDIA DLSS/NGX](https://github.com/NVIDIA/DLSS/blob/main/LICENSE.txt)
restreint l'ingénierie inverse et les usages sous SDK aux systèmes
NVIDIA GPU. Aucun contournement, extraction de poids NVIDIA, ni
émulation d'exécution Windows n'est implanté dans Eden Encore.
Les portages NR Vulkan publics testés sur RDNA4 avec FP8/cooperative
matrix ne démontrent pas leur fonctionnement sur la PS5 RDNA2.

**Priorité finale** : qualifier Anime4K 3D sur PS5, garder FSR3.1
temporel ouvert tant que depth/motion/jitter/projection ne sont pas
fournis de manière générique par le GPU invité. Le MSAA forcé est
raccordé en code, mais demande également qualification console.

**Mise à jour du 06/11 : première primitive GEMM Vulkan compatible RDNA2
intégrée en code, sans modèle ni sortie DLSS opérationnelle.** Voir
[ENCORE_R09_RDNA2_NEURAL_VULKAN_PORT.md](ENCORE_R09_RDNA2_NEURAL_VULKAN_PORT.md)
pour la progression vérifiable, les ABI et les autres familles de kernels.

## Évaluation RDNA2 HIP 7.2 et sources Vulkan (6 novembre 2026)

L'utilisateur signale la release
[danielblnc/DLSS-NR-on-AMD](https://github.com/danielblnc/DLSS-NR-on-AMD/releases)
v0.6.0 (3 octobre 2026), qui annonce explicitement la série RX 6000
(RDNA2) et demande le runtime **AMD HIP 7.2**. Le README actuel du
projet mentionne également 0.8.0, avec RDNA2 **encore en test et NR
seulement**, les autres fonctions DLSS visant surtout RDNA3/RDNA4.
L'environnement ciblé reste **Windows 11, DirectX 12**, avec
interface Vulkan seulement annoncée pour plus tard.

Il ne s'agit PAS d'un dépôt de sources directement réutilisables :
la racine publique contient README, LICENSE, THIRD_PARTY et les
workflows GitHub, **pas les noyaux HIP ni le moteur**. La licence
Daniel Blanco (© 2026) autorise un usage personnel non commercial,
mais interdit la redistribution, la modification et le reverse
engineering sauf exceptions légales obligatoires. **Ne pas intégrer
ou redistribuer ces binaires dans Eden Encore**, même si l'utilisateur
fournit une bibliothèque NVIDIA différente de ce logiciel.
Source : https://github.com/danielblnc/DLSS-NR-on-AMD/blob/master/LICENSE

La [documentation officielle du HIP SDK 7.2 pour Windows]
(https://rocm.docs.amd.com/projects/install-on-windows/en/latest/reference/system-requirements.html)
marque les GPU RX 6000 RDNA2 comme non officiellement pris en charge
par ce SDK. Un contournement communautaire dans le mod Windows,
si fonctionnel, ne rend **pas** ce runtime portable vers le noyau
hôte **PS5** ; ni le pilote Adrenalin, ni les DLL HIP Windows ne
s'y exécutent. Le support RDNA2 annoncé est donc un **signal de
faisabilité**, pas une preuve console.

Source de moteur Vulkan réellement consultable :
[Overclockers/DLSSNR-AMD]
(https://github.com/Overclockers/DLSSNR-AMD).
Le dépôt publie du code Vulkan compute sous MIT, une documentation
d'architecture, des composants Linux et Windows et des procédures
de vérification des modèles utilisateur. Le backend testé ne cible
**que RDNA4 RX 9000** (instructions matricielles FP8 avec
VK_KHR_cooperative_matrix). **RDNA2 PS5 ne fournit pas ce chemin** :
il faudrait un autre noyau de multiplication/accumulation,
un format de poids compatible, des mesures de coût GPU, un
contrôle indépendant des droits des modèles et une alimentation
réelle en données jeu (notamment mouvements/profondeur/exposition).
Ne pas importer des poids, DLL ou shaders propriétaires à partir
d'une simple preuve de concept.

**Décision R09** : les trois filtres A4K libres, compilés sur hôte
et non encore qualifiés PS5, constituent la seule implémentation
neuronale raccordée dans la PR #24. Conserver le port DLSSNR-AMD
Vulkan/MIT comme **référence de recherche RDNA2**, non comme
fonctionnalité annoncée ou dépendance nécessaire au lancement.
