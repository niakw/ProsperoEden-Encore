# Eden Encore — correction fonctionnelle des fenêtres Split-Swin décalées

Le plan natif contient des couches `CCSplitSwin16HQKVAttn` dont les champs `shift_x,shift_y` valent `-1,0,+1` **en unités de tuile 4×4**. QKV+attention seul sur la même grille 8×8 échangerait alors les mauvais tokens entre fenêtres. Ce défaut ne provoque pas nécessairement de crash mais invalide le résultat de l'inférence.

Le contrat `SplitBlockPlan` expose maintenant la grille réelle de fenêtres et les deux shifts. Un bloc décalé exige **deux buffers supplémentaires** : (1) sortie FFWDProj → entrée QKV, reconditionnée en fenêtres décalées ; (2) contexte sorti de l'attention et transposé en tokens → fenêtres de projection rétablies. Les deux déplacements utilisent le shader existant `fswin_window_repack_rdna2.comp`, sans nouveau kernel spécifique et sans aucun retour CPU. Le contrat `CanSplitBlock` prévalide les deux chemins avec `CanFSwinWindowRepack`, refuse les écarts hors ±1, dimensions discordantes et buffers incomplets avant le premier dispatch.

`CanFSwinWindowRepack` autorise maintenant **C512**, contre C32/C64/C128/C256 auparavant ; le test hôte passe sur C512 et la grille native 8×5, avec oracles d'aller-retour et de bord. Cela concerne les 16 blocs Original et les 4 Compact, avec décalages variables par couche QKV ; il faut lire le champ de plan, pas inférer le shift depuis le numéro du bloc.

**Attention :** le contrat hôte et son couplage Vulkan doivent rester cohérents. Cette opération ne valide pas la précision de l'attention native, la transformation complète `*_inpview/outview`, les sauts U-Net ni un rendu. Aucun build PS5 / CI n'est revendiqué.

## Implémentation Vulkan du chaînage

Le composant `NrRdna2SplitSwinBlock` possède maintenant une instance `NrRdna2FSwinWindowRepack`, un pool de **deux** descriptor sets et deux buffer-paires. Pour les blocs marqués `attention_shift_x/y != 0` dans leur `SplitBlockPlan`, `Record()` enchaîne :

`FFWD3 → FFWDProj → repack(0→shift) → QKV → attention → contexte head→token → repack(shift→0) → projection résiduelle → ProjPool éventuel → FinalHead éventuel`.

Les barrières compute→compute existantes de chaque wrapper protègent les transitions ; le prévol `CanSplitBlock` refuse les shifts hors ±1, grilles incompatibles et volumes GPU insuffisants. `ValidResources` exige désormais des **ressources non aliasantes** pour les deux nouveaux buffers et tous les intermediates, ainsi que pool/final lorsqu'ils sont présents. Le chemin sans shift ne crée ni jeu de descripteurs ni dispatchs additionnels.

**Validation restante :** tests hôte enregistrés, mais compilation complète Vulkan/PS5 et comparaison avec une capture de référence non confirmées. La lecture automatique de chaque shift depuis le `NativeNrSchedule` reste à relier à l'instanciation des blocs ; aucun réglage par jeu ou activation anticipée.
