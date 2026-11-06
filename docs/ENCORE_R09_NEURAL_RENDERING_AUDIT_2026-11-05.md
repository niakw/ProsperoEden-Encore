# Eden Encore — R09 Neural Rendering : sélection de moteur et limites PS5
**Audit externe vérifié le 05/11/2026** · dépôt fonctions / PR #24 · état : RECHERCHE

## Directive du 6 novembre 2026

**R10, les textures HD générées par IA, est abandonné.** Le dernier
point graphique est désormais R09 : **upscaling et rendu neuronal**,
calculés sur l’image et les données du GPU invité, **sans toucher aux
fichiers de textures ni lancer un réseau IA pendant l’extraction de ROMS**.
Priorité à un modèle de super-résolution spatial à petit budget (ou
temporel si de vraies entrées motion/depth/projection sont disponibles),
avec poids légalement redistribuables et inference Vulkan RDNA2 native.
Ne pas confondre ce travail avec FSR 3.1 (reconstruction temporelle
non neurale) ou MihawkGen (interpolation de frames distincte).

Aucun des candidats précédemment audités ne remplit encore les
critères de licence des poids, port PS5 et évaluation visuelle.
Ce document est donc un **audit et non une annonce d’implémentation**.

## Objectif exact
R09 veut un traitement réellement neuronal des visages, de la peau,
des matériaux et de la lumière via Vulkan sur PS5, sans remplacer les
textures du jeu et sans toucher au rendu NS1/NS2 quand l'effet échoue.
Il ne faut pas appeler FSR 1, FXAA+, SGSR, MihawkGen frame generation
ou un shader de contraste « Neural Rendering » : ce sont d'autres
algorithmes, même s'ils utilisent parfois un réseau neuronal.

## Candidats comparés

| Implémentation | Ce qui est démontré par la source | Obstacles matériels / API / droits |
| --- | --- | --- |
| [mochizuki0323/DLSSNR-AMD](https://github.com/mochizuki0323/DLSSNR-AMD) | Vulkan compute; réseau NVIDIA exécuté sur AMD RX 9000, via FP8/cooperative matrix | **RDNA4 uniquement** (RX 9000), les RX 6000/7000 manquent les instructions matricielles FP8 ; modèle NVIDIA non distribué, extrait par l'utilisateur de son propre DLL |
| [shakhbazian/OptiScaler-RDNA2NR](https://github.com/shakhbazian/OptiScaler-RDNA2NR) | Backend RDNA2 HIP/INT8/FP16 testé RX 6900 XT, code GPL-3.0 | Windows, DirectX12, HIP, modèle externe NVIDIA ; ne partage pas automatiquement le device/queue Vulkan natif PS5 |
| [danielblnc/DLSS-NR-on-AMD](https://github.com/danielblnc/DLSS-NR-on-AMD) | Port de réseaux DLSS vers HIP sur Radeon, RDNA2 en tests | Windows 11/DirectX12 ; Vulkan annoncé mais pas livré dans le README ; modèles fournis par l'utilisateur ; licence de code non établie par le metadata GitHub |
| [zmodelerlover/OpenNR-ReShade](https://github.com/zmodelerlover/OpenNR-ReShade) | Add-on MIT alimentant un runtime DLSS-NR AMD, avec rééchantillonnage et optical flow selon API | ReShade/HIP/D3D sur Windows ; Vulkan/OpenGL expérimentaux ; modèles externes ; pas de port natif PS5 |
| [AMD FSR SDK 2.4](https://gpuopen.com/amd-fsr-sdk/) | FSR Upscaling 4.1.2, FSR3.1.6 fallback et ray regeneration, pilotes/hardware AMD PC | **Pas un moteur de neural materials/skin branchable à Encore** ; SDK récent basé sur les DLL précompilées/signées pour DX12/Vulkan PC, dépend des buffers guest depth/motion/jitter |

Les cartes PC RDNA2 et l'APU PS5 partagent certaines propriétés
architecturales, **pas** les runtimes Windows HIP/D3D12 ni les
extensions Vulkan propres à un pilote Mesa/RADV PC. La génération de
matériaux par IA demande en outre des entrées sémantiquement fiables :
espace couleur, exposition, profondeur/mouvement, masques HUD, images
d'historique et budget VRAM/compute.

## Conclusion technique (ne pas maquiller un prototype)

**Aucune des quatre options ne peut être intégrée au moteur PS5
aujourd'hui avec des poids dont la redistribution est autorisée,
un chemin Vulkan RDNA2 vérifié et des données d'entrée génériques
NS1/NS2.** Copier des shaders ne suffit pas à lancer un réseau et
ne constituerait pas une fonctionnalité opérationnelle.

Décision : **ne pas ajouter de « Neural Rendering » activable**,
ne pas importer les modèles NVIDIA, ne pas retirer les fallback du
rendu ordinaire. Étapes pour rouvrir : sélectionner un réseau avec
poids redistribuables ou précisément autorisés, vérifier la licence,
porter les kernels en SPIR-V sans API PC/DLL, qualifier les
entrées color/depth/motion de l'émulateur, budgéter explicitement la
mémoire et mesurer le vrai gain qualité/coût par cas d'usage.
Le traitement neuronal n'est pas substituable à R10 (packs de textures
du jeu), ni à R07 (upscale temporel).

## Vérification des versions FSR (rectification roadmap R07)

AMD précise que **FSR SDK 2.4 (octobre 2026)** est désormais la
gamme courante pour FSR Upscaling. Les anciennes sources
FidelityFX SDK 1.1.4 sont utiles pour étudier FSR 3.1, mais
l'API officielle actuelle utilise des **DLL signées** et attend
color, depth, motion vectors et camera jitter. Lichii comporte un
port compute FSR3.1 adossé à des entrées d'un traitement DLSS invité
sur certains jeux NX2 ; ceci ne prouve pas la présence universelle
des mêmes entrées dans Encore, et ne constitue pas un upscale FSR3
générique disponible sur PS5. Garder l'étiquette « FSR 1 » sur la
méthode spatiale réellement compilée.

## Preuves et références

- AMD, [AMD FSR SDK](https://gpuopen.com/amd-fsr-sdk/) et
  [FSR Upscaling — intégration](https://gpuopen.com/amd-fsr-upscaling/)
- GPUOpen, [FidelityFX-SDK / historique des releases](https://github.com/GPUOpen-LibrariesAndSDKs/FidelityFX-SDK/releases)
- Sources et READMEs des quatre projets GitHub ci-dessus consultés
  le 05/11/2026 ; leurs versions/tests peuvent évoluer.

**R09 : recherche active, pas de code natif livré, pas de build PS5
complet ni validation console.** Ne pas déclarer terminé.
