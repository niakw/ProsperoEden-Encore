# Eden Encore R09 — trois références consommation / optimisation (07-11-2026)

**État réel : phase d'audit et critères d'admission. Aucun gain de FPS,
watts, VRAM ou temps GPU n'est revendiqué sur la PS5.**

Priorité absolue : une première inférence complète, reproductible et
numériquement plausible, puis optimisation des ressources **après** la
validation de la base. Le moteur DLSS-NR reste désactivé par défaut,
sans raccourci ni paramètre caché qui activerait du calcul.

## Sources vérifiées le 07/11/2026

### A. matiasLombo/neural-upstream (MIT)

- Source : https://github.com/matiasLombo/neural-upstream
- Constat principal : exécuter NR **avant l'upscaler, à la résolution de
  rendu interne**, peut diminuer le nombre de pixels inférés, puis
  confier la reconstruction à un upscaler déjà présent.
- Contrainte immédiate Encore : nos jeux de plans natifs et les tenseurs
  Original/Compact ont été extraits pour **1920×1080**. Il ne suffit
  PAS de baisser la résolution du framebuffer en conservant les grilles
  de fenêtres et le nombre de tokens du plan ; il faut régénérer,
  revérifier et retester chaque dimension du graphe.
- Autre idée : normaliser une image HDR avec l'exposition réelle,
  appliquer le réseau dans son espace valide, puis reconstruire son
  **effet sur la luminance** plutôt que réinjecter les couleurs de la
  frame précédente. Cela ne dispense pas de connaître l'espace couleur.
- Observation d'amont : NR intermittent + frame generation a causé des
  à-coups de frame pacing ; garder la cadence 1 image réelle / 1
  évaluation tant que cette compatibilité n'est pas prouvée.
- Ne jamais importer NGX/ReShade/MinHook/D3D12/PTX ni leurs binaires.

### B. BeliyG3/optimizer-fps-dlss5 (MIT)

- Source : https://github.com/BeliyG3/optimizer-fps-dlss5
- Idée : comprimer non linéairement **la périphérie spatiale** en
  conservant le centre en pleine densité, puis reconstruire l'image
  finale en préservant le détail de la couleur originale.
- Contrainte Encore : le réseau utilise des fenêtres 8×8, des tuiles
  4×4 et de l'attention globale ViT. Une déformation spatiale sans
  transformation cohérente des textures depth/motion, des offsets
  de fenêtres et des masques HUD casserait le graphe. À évaluer
  uniquement sous des images A/B avec contours et périphérie.
- Variante temporelle : calculer le modèle toutes les N frames
  **réelles** et reprojecter le *delta neuronal* avec des guides de
  mouvement et profondeur validés. Aucun de ces guides n'est encore
  garanti génériquement côté GPU invité NS1/NS2.
- Aucun frame skipping, reprojection ni compression périphérique ne
  doit être activé sans preuve d'entrée, taux d'historique et rejet
  des disocclusions.
- Ne pas copier les hooks ReShade/D3D12/NVIDIA.

### C. NVIDIA-RTX/RTXNTC (licence SDK NVIDIA, non MIT)

- Source : https://github.com/NVIDIA-RTX/RTXNTC
- **Ce n'est pas un accélérateur du graphe DLSS-NR**. C'est de la
  compression neuronale des textures et des matériaux de jeux.
- Son coût de décompression (Vulkan, coop vector ou fallback DP4a)
  et ses droits spécifiques exigent une analyse séparée.
- Ne pas charger ses poids ni ses shaders dans le runtime NR. Pas de
  gain de consommation déductible pour notre inférence simplement
  parce qu'une texture compressée est plus petite.
- Décision : **hors périmètre du socle**, recherche ultérieure seulement
  si la consommation VRAM des textures de jeux est effectivement un
  goulot prouvé.

## Admission des optimisations après la base

| Ordre | Mesure / modification | Conditions impératives |
| --- | --- | --- |
| 0 | Référence sans NR | Même scène, mêmes vrais FPS, consommation et temps p50/p95/p99 GPU |
| 1 | Première frame NR correcte | NRMODEL1 conforme, aucune opération sautée, bindings et barrières audités |
| 2 | Résolution interne avant upscale | Graphe entièrement régénéré et vérifié pour les nouvelles grilles 8×8 / 4×4 |
| 3 | Tuilage GEMM/FFWD/attention | A/B numérique avant/après ; aucune dégradation mémoire ou race |
| 4 | Compression périphérique | Depth/motion/HDR et HUD reprojetés correctement, scènes de bords qualifiées |
| 5 | NR à cadence intermittente | Guides fiables, TTL et disocclusion ; **interdit avec FrameGen sans preuve** |
| 6 | RTXNTC | Projet texture séparé, licence et budget mesurés indépendamment |

Tout réglage optionnel doit rester **OFF par défaut**, même s'il
est visible dans les overrides. Les trois profils A4K du projet ne
sont pas de l'upscaling DLSS-NR et ne doivent pas être présentés comme
une accélération de ce réseau.

## Reste fonctionnel R09 (comptage de familles, non pourcentage de réussite)

Sur le plan 1080p Original, les **152 opérations** se décomposent en
65 Split-Swin, 40 ViT, 1 décodeur appris, 44 FSwin/U-Net,
et 2 adaptateurs d'image. Le plan Compact a **76 opérations** :
17 Split, 40 ViT, 1 décodeur, 16 FSwin/U-Net et 2 adaptateurs.

Le chemin GPU central Split→ViT→décodeur→Split existe en source,
mais la preuve d'exécution d'un réseau **global** reste absente.
Les 4 raccords montants U-Net existent à l'échelle d'une transition,
**trois gains** C64/C128/C256 sont encore non prouvés.
Les pré/post-réseaux fusionnés et la conversion RGB/HDR↔16 canaux
sont encore incomplets, de même que l'intégration au présentateur.

**Ne pas convertir des opérations reconnues dans le schedule en
« opérations exécutées » tant qu'aucun véritable chemin GPU complet
et sa référence d'image ne le prouvent.**
