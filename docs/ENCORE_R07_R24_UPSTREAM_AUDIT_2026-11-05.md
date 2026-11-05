# Eden Encore — vérification R07/R24 et dépôts graphiques (05/11/2026)

**Périmètre :** PR graphique #24 empilée sur #21, sans toucher à main,
au vendor épinglé ni à la branche console. Référence fonctionnelle :
[ROADMAP_ENCORE_COLLAB_2026-10-25.md](https://github.com/niakw/ProsperoEden-Encore/blob/feat/graphics-network-achievements/docs/ROADMAP_ENCORE_COLLAB_2026-10-25.md),
section C, **R07** et **R24**. Les intitulés de fonctionnalités sont
des objectifs contractuels, pas des annonces de disponibilité sur PS5.

## R07 — Upscaling : distinguer les pipelines

| Méthode | Nature | État Encore | Véritable preuve requise |
|---|---|---|---|
| Natif / upscale classique | Bilinéaire, bicubique, nearest | Existant | Vérifier rendu/output/crop et fidélité A/B |
| **FSR 1** | **Spatial** : EASU puis RCAS | Existant ; nouvel override PS5 de la netteté sur cette PR | Contrôle live sur PS5 et mesures comparatives |
| **FSR 3.1 temporel** | Historique, depth, mouvement et jitter par frame, accumulation et reconstruction | **Non raccordé au pipeline générique de l'émulateur** | Trace guest réelle des entrées + bridge scheduler Vulkan + fallback + performance |
| FSR 3 Optical Flow FG | **Génération d'images**, pas upscale temporel AMD complet | Intégré source en #21, non qualifié console | Comparer frames affichées, cadence et ghosting |
| SSAA via Game resolution 1,25–2x | Suréchantillonnage de résolution, pas AA multisample | Contrôle de résolution déjà existant | Coût GPU/VRAM et image sur console |

**Correctif réel de la netteté FSR 1.** Le renderer upstream
fsr.cpp reçoit la valeur interne fsr_sharpening_slider
en stops RCAS (0 = fort, 2 = faible) ; FsrRcasCon calcule
exp2(-stops). Le launcher avait **déjà la bonne inversion** :
internal = 200 - 2 * pourcentage. Le problème n'était donc
**pas** une inversion globale du curseur. En revanche, **à 0 %,
la passe RCAS tournait encore** avec 2 stops, au lieu d'être désactivée.

La source PS5 maintenue headless/vulkan_fsr1_r07.cpp utilise
Fsr1SharpnessFromInternal en préservant l'inversion existante :
0 % renvoie EASU seul sans lancer RCAS ; 50 % = 1 stop ;
100 % = 0 stop (RCAS fort). Le test hôte vérifie les **101 valeurs**
du pourcentage public et prévient toute double inversion.
Hors FSR 1, l'option est visible mais grisée/non réglable.

## R24 — Anticrénelage perceptible (toujours ouvert)

- **None/FXAA/SMAA :** les passes existent réellement, SMAA
  `SMAA_PRESET_ULTRA` compilé dans
  `src/video_core/host_shaders/smaa_edge_detection.frag`.
  « SMAA Ultra » peut désigner **ce preset actuel**, mais n'est **pas**
  une amélioration nouvellement implémentée. Ni les FPS ni la différence
  perceptible ne sont établis sur PS5.
- **Correction R24 partielle :** `vulkan_present_layer_r24.cpp`
  utilise les dimensions **réelles** de la source raw/accélérée
  et recrée les surfaces AA sur resize ; host policy vérifiée.
  Cela répare un problème de dimensionnement sans ajouter de méthode.
- **Nouveau palier FXAA+ (native Vulkan, PR #24) :** source distincte
  headless/fxaa_quality.frag ; recherche de contours plus large
  (FXAA_SPAN_MAX : 8 vers 12), atténuation réduite
  (1/8 vers 1/16 ; 1/128 vers 1/256). Le CMake produit
  un vrai shader SPIR-V séparé, validé par spirv-val ; la source C++
  du pass choisit explicitement l'ancien shader ou ce nouveau module.
  La sélection globale/par jeu est conservée avec une nouvelle clé
  fxaa_quality (index 3) ; en OpenGL, aucun faux effet n'est promis.
  Cela n'est pas du MSAA ou du TAA. **Ce palier peut également
  accentuer le flou** selon la scène ; il faut encore un A/B réel
  pour démontrer son gain perceptuel sur FC27/BOTW.
- **Autres paliers :** Ryubing possède des variantes SMAA
  Low/Medium/High/Ultra ; Encore conserve SMAA Ultra existant.
  Les variantes supplémentaires nécessitent des shaders et pipelines
  distincts, pas un bouton décoratif, puis un comparatif qualité/coût.
  FXAA renforcé exige pareillement un vrai shader/preset différent.
- **MSAA 2x/4x/8x :** les surfaces multisample du guest sont connues
  du texture cache et des render passes, avec `num_samples`.
  Imposer un sample count dans l'image de présentation **ne produit
  pas du MSAA guest**, et le forcer sur les surfaces du jeu peut
  violer les résolves/mémoires/barrières. Ne pas créer de fausse
  option MSAA sans contrat GPU et compatibilité validés.
- **SSAA :** évaluer les échelles déjà présentes, **sans dupliquer**
  le réglage sous un libellé trompeur « AA 2x ».
- **TAA et AA temporel :** même précondition que FSR3 temporal :
  depth/motion/jitter stables, découpage HUD invité, historique,
  réinitialisation et ghosting. Inadéquat comme « méthode universelle »
  tant que ces données sont absentes.

### Comparaison ciblée des dépôts GitHub pertinents

| Référence vérifiée | Preuve source | Décision PS5 |
|---|---|---|
| [GPUOpen FidelityFX-SDK](https://github.com/GPUOpen-LibrariesAndSDKs/FidelityFX-SDK) | FSR 3.1 Vulkan, depth/motion vectors/jitter et ressources d'historique | **Candidat** de backend seulement après preuve des entrées guest |
| [Lichii](https://github.com/zortos293/Lichii/blob/nx2/src/video_core/renderer_vulkan/vk_fsr3_upscaler.cpp) | `vk_fsr3_upscaler.cpp` : vrais compute passes FSR3.1, `UpscaleWithFsr3` branché à `TemporalUpscale` lorsque depth et motion sont disponibles | **Piste prioritaire R07** : adapter le modèle des ressources, pas les hooks de jeu |
| [Lichii — présentateur « FSR3 »](https://github.com/zortos293/Lichii/blob/nx2/src/video_core/renderer_vulkan/present/fsr3.cpp) | Le fichier nommé FSR3 compile en pratique les shaders EASU et RCAS spatiaux ; le header décrit plus que ce que `Draw()` exécute | **Ne pas importer sous étiquette « FSR3 temporel »** |
| [Lichii — guest DLSS](https://github.com/zortos293/Lichii/blob/nx2/src/video_core/engines/kepler_compute.cpp) | Capture d'entrées de pipelines DLSS guest + refus/fallback ; contrat étroit lié à une famille de programmes NVIDIA NS2 | Rechercher extraction générique sans dégrader NS1 ; ne pas généraliser à tous les jeux |
| [Ryubing](https://github.com/Leuconoe/Ryubing/blob/main/src/Ryujinx.Common/Configuration/AntiAliasing.cs) | None/FXAA et SMAA Low, Medium, High, Ultra ; shader/renderer Vulkan C# | Référence R24 pour paliers réels, pas un patch C++ copiable directement |
| [Citron Neo](https://github.com/citron-neo/emulator) | Répertoire SMAA Vulkan présent ; pas de fichier fsr3 dans la recherche de code auditée | Comparaison AA, pas candidat FSR 3.1 démontré |
| [Sudachi](https://github.com/Synoptikon/Sudachi) | Aucun fichier fsr3 identifié dans la recherche ciblée | Pas de candidat FSR 3.1 démontré |
| [shadPS4 Bloodborne FSR](https://github.com/eFMann/shadPS4-Bloodborne-DLSS-FSR) | Vrai FSR3.1, depth/mouvement caméra et personnages, jitter, HUD après upscale | Architecture utile, **mais spécifique à Bloodborne/PC**, pas drop-in NS1/NS2/PS5 |
| Eden actif + vendor épinglé Encore | FXAA/SMAA, FSR1 EASU/RCAS, résolution/échantillons des render targets invités | Baseline : ne pas réécrire le déjà existant |

*Ce tableau couvre les dépôts pertinents identifiés dans la roadmap et
l'audit de code. Il ne prétend pas couvrir tous les dépôts GitHub ; tout
autre candidat exige un commit, une preuve source et un contrôle de
licence. Les branches et fichiers peuvent évoluer après le 05/11/2026.*

### Décision de clôture — sans reporter le travail au test PS5

**R07 : non clos.** Le correctif RCAS et son test host sont une avancée
indépendante. Il faut encore le chemin temporel générique, les entrées
et la gestion des ressources (pas seulement tester une console).

**R24 : intégré en source, non clos.** Le dimensionnement est corrigé et
FXAA+ est maintenant un véritable shader distinct, sélectionnable,
non un alias. Les tests hôtes vérifient sa compilation SPIR-V,
le routage, les ressources et la persistance. Le **gain de qualité
perceptible** et le coût GPU ne sont pas prouvés sur PS5 ;
MSAA 2/4/8, TAA temporel et paliers SMAA supplémentaires restent
des analyses non livrées. Aucun benchmark console n'est fabriqué.

**À ne pas faire :** inventer FSR3 spatial, simuler un MSAA via postprocess,
appeler le filtrage anisotrope une texture HD, assimiler « shader
chargé » à « amélioration perceptible » ou considérer des spécifications
comme un rendu validé.
