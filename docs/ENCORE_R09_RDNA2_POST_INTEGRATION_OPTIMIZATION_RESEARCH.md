# Eden Encore — audit de pistes d'optimisation DLSS Neural Rendering RDNA2 (APRÈS intégration)

> État : **backlog de recherche uniquement** — 06/11/2026.
> Ce document **ne change pas** l'ordre des travaux de la PR #24.
> Priorité actuelle : intégrer le réseau fonctionnel, charger le modèle, lier les ressources Vulkan, puis obtenir une première image correcte.
> Benchmarks/qualité, spécialisation RDNA2 et choix de profils **ensuite**.
> Aucun chiffre de performance provenant de matériel NVIDIA n'est transposable automatiquement à la PS5.

## Critères de succès et ordre de travail

1. **Intégrité fonctionnelle** : graphe complet, poids exacts, entrée couleur/profondeur/mouvement, sorties plausibles, pas de corruption ou de régression du chemin NS1.
2. **Référence qualité** : mêmes séquences fixes avec modèle de référence, identiques pour tous les profils. Séparer exactitude numérique des kernels, qualité perceptuelle et stabilité temporelle.
3. **Budget matériel fixe PS5/RDNA2** : temps GPU médian et p95/p99, mémoire VRAM et bande passante, synchronisations GPU, latence de présentation, GPU partagé entre le jeu et la passe neuronale. Conserver de la marge pour le renderer du jeu.
4. **Optimisations algorithmiques mesurées** avant les micro-optimisations : pixels réellement inférés, résolution d'entrée, découpe spatiale, cadence temporelle, réutilisation de résidu.
5. **Micro-optimisations RDNA2** ensuite : tuilage GEMM/FFWD/QKV, coalescence mémoire, barrières, LDS, réduction de traffic mémoire et conversion/quantification FP8, occupation de wavefronts. Ne pas introduire HIP PC ou les instructions RDNA4 impossibles sur PS5.
6. Ne présenter aux utilisateurs que des modes validés visuellement et en stabilité temporelle. Conserver un retour au rendu standard lorsque les prérequis (guides depth/motion, modèle compatible, budget VRAM) sont absents.

## Sources initiales (non exhaustives)

### 1. neural-upstream — haute priorité

Source : https://github.com/matiasLombo/neural-upstream  
Notes et limites : https://github.com/matiasLombo/neural-upstream/blob/main/FINDINGS.md  
Licence du code propre au dépôt : MIT.

Idée principale : déplacer le Neural Rendering à la **résolution interne du jeu**, puis confier la reconstruction à l'upscaler déjà présent. L'effet est normalement évalué à la résolution de sortie ; réduire l'aire de calcul peut donc supprimer une grande partie des multiplications et accès mémoire. Le dépôt utilise une implémentation Windows/NGX/D3D12, **non directement portable à Prospero/Vulkan**.

À évaluer sur Eden :
- Choisir explicitement l'espace de couleur d'entrée et restaurer la luminosité HDR sans altérer teinte/saturation ; le dépôt décrit une normalisation/tonemapping réversible par gain de luminance.
- Vérifier la cohérence des motion vectors, du jitter, de l'exposition, de la profondeur et des subrects dans le chemin FSR déjà existant.
- Référence qualité : edges très fins, éléments transparents, HUD, alpha, haute fréquence, hallucinations temporelles ; comparer rendu neuronal à la résolution interne **vs** résolution finale.
- Pour une cadence inférieure à une image sur une, réutiliser **l'effet** (delta entre entrée et sortie neuronale), non l'image précédente, reprojecté avec guides et rejet des disocclusions.
- L'auteur note des à-coups de cadence lorsque Neural Rendering intermittent et frame generation se combinent : étudier seulement une fois le fonctionnement stable, ne pas promettre la compatibilité.

### 2. optimizer-fps-dlss5 — haute priorité

Source : https://github.com/BeliyG3/optimizer-fps-dlss5  
Limitations : https://github.com/BeliyG3/optimizer-fps-dlss5/blob/main/docs/LIMITATIONS.md  
Checklist de port : https://github.com/BeliyG3/optimizer-fps-dlss5/blob/main/docs/PORTING_CHECKLIST.md  
Licence du code propre au dépôt : MIT.

Idées algorithmiques :
- **Compression spatiale périphérique** : conserver une zone centrale à pleine densité, comprimer de manière non linéaire les côtés du domaine traité, puis reconstruire l'image. Considérer également le **transfert de détail** : conserver la couleur native et reconstruire surtout la contribution du modèle.
- **NR intermittent** : calcul du modèle toutes les N vraies images ; reprojecter le **résidu neuronal** sur les images intermédiaires. Validation par profondeur/couleur, trous de disocclusion, vecteurs de mouvement, TTL de l'historique et composition à résolution native.
- **Exécution asynchrone** seulement si les files/événements Vulkan et la durée de vie des ressources permettent réellement la superposition sans pénaliser le jeu.
- Qualité d'abord : transition au bord de la zone centrale, déformation de la périphérie, texte/HUD, feuilles/cheveux, transparence, particules, objets proches des bords, occlusions.

Le produit actuel exige ReShade, D3D12, un consommateur NR NVIDIA et un runtime NGX/NVIDIA : **n'intégrer ni hooks Windows ni DLL dans le port PS5**. Les chiffres de sa README ne sont pas des prédictions RDNA2.

### 3. NVIDIA-RTX/RTXNTC — recherche distincte, priorité moindre

Source : https://github.com/NVIDIA-RTX/RTXNTC  
README et documentation : https://github.com/NVIDIA-RTX/RTXNTC  
Licence : **NVIDIA RTX SDKs LICENSE**, spécifique/restrictive ; analyse juridique de chaque composant avant réutilisation.

NTC vise principalement **la compression des matériaux/textures PBR**, avec données latentes et petit décodeur neuronal. Il ne remplace pas un moteur DLSS Neural Rendering et **ne réduit pas directement ses FLOPs**. Deux modes documentés sont pertinents à comparer :
- Décodage à chargement de texture, puis transcodage en formats BCn : peut réduire stockage et transferts, au coût d'un chargement plus cher.
- Décodage à la demande : réduit la pression mémoire dans certaines conditions, mais ajoute du coût shader et des besoins de feedback/résidence.

Sur PS5, tester d'abord les chemins matériels de textures et la gestion VRAM existants. Ne pas combiner le projet NTC et le portage DLSS-NR avant d'avoir **un cas d'usage de réduction mémoire prouvé**. Éviter d'ajouter du calcul neuronal pour corriger un problème inexistant. La bibliothèque NVIDIA n'est pas présumée directement compatible RDNA2.

## Méthode d'évaluation après validation du premier rendu

Établir un jeu de scènes répétables couvrant les cas suivants : image fixe détaillée, déplacement latéral rapide, travelling de caméra, mouvements de personnages, contours en subpixel, végétation/cheveux, transparence/particules, HUD/texte, changement d'exposition, transitions et disocclusions. Tester notamment des contenus comparables aux jeux NS1 et NS2 visés par Eden Encore, sans codes spécifiques par titre.

Pour chaque variante :
- **Qualité** : comparaison A/B visuelle aveugle, SSIM/PSNR pour la fidélité, métrique perceptuelle adaptée si disponible, ghosting, scintillement, halo, dérive HDR et disocclusions. Les métriques statiques seules ne suffisent pas.
- **Coût** : GPU ms par étape, temps GPU total p50/p95/p99, VRAM pic, volumes lus/écrits, barrières et attente de synchronisation, latence effective, impact sur les FPS réels du jeu.
- **Robustesse** : image stable sur mouvement/resize, changement de profil, résolution, absence de guides, scènes très chargées, cache/historique invalidé ; aucun accès mémoire hors limites.
- **Décision** : garder une modification uniquement si la dégradation visuelle est comprise, bornée et compensée par un gain significatif et mesuré. Une sortie sans NR reste un fallback valide.

Ordre expérimental suggéré : **résolution interne + chaîne HDR → réduction périphérique → fréquence des passages et reprojection de l'effet → scheduling GPU → spécialisation des kernels RDNA2 → compression de textures (si besoin mémoire démontré)**. Ces expériences ne démarrent qu'après la couverture fonctionnelle du graphe et un test de précision sur console.

## Notes de maintenance

- Les trois dépôts sont des **pistes**, non une bibliographie complète. Étendre l'audit à GPUOpen, au matériel PS5/Vulkan disponible, aux méthodes de reprojection temporelle et aux implémentations ouvertes autorisées lorsqu'il sera temps d'optimiser.
- Conserver les licences et attributions si du code MIT est repris. Ne pas importer automatiquement les SDK NVIDIA/NGX ni des modèles non redistribuables.
- Toute optimisation éventuelle reste sous tests et dans le **vendor** si elle appartient au moteur graphique réutilisable.
- Ne pas promettre un débit temps réel sur PS5 avant mesure. La conclusion peut être : mode neuronal de moindre qualité mais utilisable, mode intermittent très contrôlé, ou **désactivation lorsque le compromis qualité/coût est insuffisant**.
