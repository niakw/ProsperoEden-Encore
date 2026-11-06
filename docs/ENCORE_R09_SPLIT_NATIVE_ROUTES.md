# R09 — cartographie native des blocs Split-Swin, Original et Compact

Le composant **`BuildNativeSplitRoutes`** déduit les `SplitBlockPlan` directement des fichiers de plan 152/76 couches, sans indice de jeu et sans traiter le simple décodage comme une preuve d'inférence.

Pour chaque bloc, il exige exactement `FFWD → FFWDProj → QKV/attention → Proj/ProjPool → FinalHead éventuel`, les relations source `input0`, les quatre numéros de couches, les tailles et les décalages QKV explicites. Il refuse une entrée manquante, une colonne de grille inversée, un shift non fourni, un pool sans FinalHead ou une couche inconnue ; la sortie reste entièrement vide en cas d'erreur.

Deux parcours sont extraits pour chaque modèle :
- **Original :** 8 blocs 23–30 (le dernier contient ProjPool/FinalHead) puis 8 blocs 40–47 (le dernier expose `outview`). Total **16 blocs**, 65 opérations.
- **Compact :** 2 blocs 9–10, puis 2 blocs 20–21. Total **4 blocs**, 17 opérations.

Le plan QKV de référence 1080p indique **5×8 fenêtres**, et non 8×5 dans l'ordre natif : le champ `W=60, H=33` de la description est utilisé par `gemmpool` avec `p.W=s.H` et `p.rows=s.W`. La projection poolée reçoit donc **33 colonnes × 60 lignes**, avec un résultat utile de **20×32 = 640 tokens** après padding 4×4. Les projections matricielles Split-Swin de l'amont calculent `ceil(60/4)*ceil(33/4)*16 = 2160` tokens, pas les 2560 tokens des 40 fenêtres paddées. Le pool doit effacer les **1520 tokens** supplémentaires lus par FinalHead ; le builder demande un buffer de 2160×512, puis une sortie FinalHead 2160×1024.

Le classificateur calcule les décalages de QKV depuis les colonnes `shift_x/shift_y`, puis les transmet au composant Vulkan Split-Swin qui vient de recevoir les deux passes de repack GPU. Le test `test_rdna2_nr_split_native_routes` couvre les 20 blocs des deux corpus, les deux parcours, ProjPool/FinalHead, les shifts et les erreurs injectées ; chaque plan obtenu passe `CanSplitBlock` avec des capacités modèles exactes.

**Garde-fous :** aucun bloc n'est automatiquement exécuté par le simple fait de créer ce plan. Le passage automatique des buffers réels FSwin/ViT et le travail sur les 2160 tokens actifs restent à relier. La parité d'image, la CI et l'exécution Vulkan restent à démontrer.
