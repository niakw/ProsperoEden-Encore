# R09 — parcours Split-Swin natifs Vulkan : 8/2 blocs

Le nouvel orchestrateur `NrRdna2SplitSwinRun` enchaîne sur le **même scheduler Vulkan** l'intégralité d'un parcours Split-Swin : **8 blocs** pour un parcours Original, **2 blocs** pour un parcours Compact. Chaque modèle comprend exactement deux parcours, séparés par le goulot ViT et sa branche de décodage.

À l'initialisation, il reçoit les `NativeSplitRoutes` reconstruits depuis le plan 152/76 étapes, le NRMODEL1 fourni localement et les descriptors VMA des buffers des blocs. Il refuse une chaîne qui n'a pas le bon nombre de couches, un source0 incorrect, un buffer de sortie qui n'est pas identiquement le buffer d'entrée suivant (handle, offset et taille), une projection poolée au milieu du parcours, ou un bloc dont les poids ne sont pas disponibles. Les modèles et les descripteurs de tous les sous-blocs sont retenus par la même instance ; aucun parcours incomplet n'est publié.

`Record()` enregistre séquentiellement les blocs et leurs barrières GPU, avec les transformations de fenêtre QKV désormais internes, y compris `ProjPool` et `FinalHead` si présents. `Result()` donne le buffer GPU du dernier bloc : la sortie FinalHead pour le premier parcours, la sortie Proj pour le second.

**Frontières non fermées par ce seul composant :** le premier parcours requiert une entrée issue d'`InputView` au format fenêtre FP8 déjà converti ; le dernier parcours produit des fenêtres qui doivent encore être exportées en raster `OutputView`. `RequiresInputView()` et `RequiresOutputView()` signalent ces obligations, sans prétendre que le chargement du modèle et le dispatch constituent une image NR. La transition ViT, le stockage tampon/résidu global, la sortie renderer et les tests GPU restent à faire.

Aucune activation dans l'interface, aucune variante par jeu, pas de build PS5 complet avant P5.

## Entrée et sortie raster natives raccordées

`NrRdna2SplitSwinRun::InitializeWithModel` accepte désormais deux buffers raster optionnels, obligatoires lorsqu'une frontière native le requiert. Les marqueurs `InputView` et `OutputView` extraits du plan contrôlent directement ces contrats (pas de sélecteur de jeu) :

- Pour le premier parcours, l'entrée raster E4M3FN 33×60×512 est convertie sur GPU en 5×8 fenêtres × 64 tokens × 512 canaux avant le premier FFWD3. Les colonnes et lignes hors image sont explicitement remplies de zéro.
- Pour le second parcours, les fenêtres du dernier bloc sont converties vers le raster E4M3FN 33×60×512 après sa projection résiduelle. L'API `Result()` renvoie alors ce raster exporté.
- Deux descriptor sets (STORAGE_BUFFER) utilisent le `NrRdna2FSwinRasterLayout` commun, sans shader dupliqué ; la création vérifie tailles, dimensions natales, buffers non aliasés et limites de plage. `Record()` insère les passes aux frontières requises avec les barrières compute→compute existantes.

Les blocs internes conservent les 16/4 poids et les décalages d'attention de chaque étape du modèle. Cela ferme **les frontières locales** d'entrée/sortie des parcours Split-Swin, mais pas les connexions entre le premier parcours, la ViT, le décodeur et le second parcours ni le pipeline image complet. Aucune démonstration GPU/PS5 n'est revendiquée.
