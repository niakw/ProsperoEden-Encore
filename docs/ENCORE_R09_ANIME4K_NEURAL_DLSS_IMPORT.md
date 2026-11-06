# R09 — Anime4K 3D CNN et DLL NVIDIA fournies par l'utilisateur

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

Menu Upscaling : Anime4K 3D CNN x2, nouvel index 7. Les indices 0-6
restent inchangés. Vulkan uniquement. Sur OpenGL, l'option enregistrée
est conservée, avec retour au Bilinear. Si ratio différent de x2,
recadrage partiel, format non compatible ou images transitoires
dépassant 384 Mio, retour au présentateur d'origine. Aucun rendu
neural n'est déclenché sur le chemin de fallback.

Validation source : quatre kernels compilés et ABI vérifiée ;
syntaxe C++ du backend et du Layer avec les overlays PS5 : réussie.
**Pas encore de build PS5 complet, de capture A/B ni de mesure VRAM
ou GPU temps : ne pas annoncer R09 comme qualifié.**

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
