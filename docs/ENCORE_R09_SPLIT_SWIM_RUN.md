# R09 — parcours Split-Swin natifs Vulkan : 8/2 blocs

Le nouvel orchestrateur `NrRdna2SplitSwinRun` enchaîne sur le **même scheduler Vulkan** l'intégralité d'un parcours Split-Swin : **8 blocs** pour un parcours Original, **2 blocs** pour un parcours Compact. Chaque modèle comprend exactement deux parcours, séparés par le goulot ViT et sa branche de décodage.

À l'initialisation, il reçoit les `NativeSplitRoutes` reconstruits depuis le plan 152/76 étapes, le NRMODEL1 fourni localement et les descriptors VMA des buffers des blocs. Il refuse une chaîne qui n'a pas le bon nombre de couches, un source0 incorrect, un buffer de sortie qui n'est pas identiquement le buffer d'entrée suivant (handle, offset et taille), une projection poolée au milieu du parcours, ou un bloc dont les poids ne sont pas disponibles. Les modèles et les descripteurs de tous les sous-blocs sont retenus par la même instance ; aucun parcours incomplet n'est publié.

`Record()` enregistre séquentiellement les blocs et leurs barrières GPU, avec les transformations de fenêtre QKV désormais internes, y compris `ProjPool` et `FinalHead` si présents. `Result()` donne le buffer GPU du dernier bloc : la sortie FinalHead pour le premier parcours, la sortie Proj pour le second.

**Frontières non fermées par ce seul composant :** le premier parcours requiert une entrée issue d'`InputView` au format fenêtre FP8 déjà converti ; le dernier parcours produit des fenêtres qui doivent encore être exportées en raster `OutputView`. `RequiresInputView()` et `RequiresOutputView()` signalent ces obligations, sans prétendre que le chargement du modèle et le dispatch constituent une image NR. La transition ViT, le stockage tampon/résidu global, la sortie renderer et les tests GPU restent à faire.

Aucune activation dans l'interface, aucune variante par jeu, pas de build PS5 complet avant P5.
