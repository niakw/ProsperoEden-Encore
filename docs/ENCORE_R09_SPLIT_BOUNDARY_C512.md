# Eden Encore R09 — frontière 512 canaux FSwin ↔ Split-Swin

Le shader Vulkan commun `fswin_raster_layout_rdna2.comp` sait déjà déplacer exactement des mots E4M3FN entre raster et fenêtres (quadrants de 4×4 dans une fenêtre 8×8). Sa politique hôte n'autorisait que C32/C64/C128/C256, alors que l'entrée et la sortie du Split-Swin natif sont à **512 canaux**.

Le contrat `CanFSwinRasterLayout` accepte désormais C512 **avec les mêmes limites GPU et sans passe de conversion supplémentaire**. Pour les deux plans à 1080p, la frontière bottleneck est un raster de caractéristiques 60×33×512 octets, conditionné en 8×5 fenêtres de 64 tokens chacune. Le dépaquetage inverse reconstitue uniquement les 60×33 pixels valides. Les pixels hors bord sont zéro-remplis lors du paquetage, comme pour les couches FSwin.

Le test de l'aller-retour vérifie C512 (dimensions impaires, frontières et raster 60×33), les capacités exactes et les deux directions, en conservant tous les tests C32…C256. Le kernel existant `NrRdna2FSwinRasterLayout` sert aux deux familles.

**Ce qui n'est pas prouvé par ce correctif :** l'ordonnancement global et la correspondance des sources des couches `*_inpview` / `*_outview`; le prochain raccord doit appeler cette primitive sur le même scheduler que les blocs Split-Swin et réserver des buffers distincts. L'entrée demeure un raster FP8 de caractéristiques, pas un RGB jeu. Compilation Vulkan, CI et PS5 non vérifiées.
