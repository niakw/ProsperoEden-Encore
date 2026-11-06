# R09 — liaison GPU des frontières raster Split-Swin

Les plans `NativeSplitBlockRoute` conservent désormais les dimensions raster exactes (`raster_width=s.height`, `raster_height=s.width`). Pour 1080p, elles valent **33×60×512 FP8**, distinctes de l'enveloppe 5×8 fenêtres (2560 tokens). Elles serviront au convertisseur commun `NrRdna2FSwinRasterLayout` dans `NrRdna2SplitSwinRun` pour traiter l'entrée `*_inpview` avant le premier bloc et la sortie `*_outview` après le dernier bloc.

La carte entière est reconstruite depuis les données structurelles, sans changement de poids, sans identité de jeu et sans inférence d'axes au runtime. Les deux traversées correspondent aux 8+8 blocs Original et 2+2 Compact. Une conversion raster ne fait ni prétraitement RGB ni décodage de l'image de sortie du modèle.

**Validation requise :** compilation du composant d'orchestration, ABI Vulkan, buffers réellement alimentés par FSwin et décodeur, comparaison des tenseurs avec le modèle de référence. Aucun rendu PS5 n'est revendiqué.
