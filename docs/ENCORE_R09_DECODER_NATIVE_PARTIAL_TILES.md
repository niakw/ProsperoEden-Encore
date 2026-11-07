# R09 — décodeur neuronal RDNA2 sur les dimensions natives (7 novembre 2026)

Le `CCDecInputUpsample` de la source MIT `Overclockers/DLSSNR-AMD` utilise, au niveau goulot 1080p, les constantes `IW=prev.H=33`, `OW=s.H=33`, `OH=s.W=60`. Le code de Prospero Eden n'acceptait que `IW×2=OW`, `IW` multiple de 4 et `OW/OH` multiples de 8. Il était donc **inexécutable pour le vrai plan Original ou Compact**, indépendamment du fait que les shaders compilent.

## Changement de la primitive partagée

- Le prévol `CanDecoderUpsample` admet la largeur native **33→33** ou le cas antérieur **4→8**, sans accepter d'autres rapports d'échelle ; l'algorithme continue à prélever `floor(x/2),floor(y/2)` comme le shader de référence.
- Le mapping de token utilise `ceil(width/4)` comme vraie ligne de tuiles. À `33×60`, cela donne **9×15 tuiles = 2160 tokens**, dont **1980 valides et 180 de padding**. Sans ce ceil, les tokens de la dernière colonne et de la ligne suivante s'aliasaient.
- Le shader exécute toutes les positions de tuiles, **écrit zéro dans les 180 tokens inutilisés** sur chaque passe, et lit les résidus uniquement pour les pixels valides. Il n'envoie jamais un canal dupliqué à deux adresses identiques dans la même invocation.
- Les bornes hôte couvrent la source FP16 tuilée, l'entrée skip et la sortie E4M3FN **avec padding**, les gains, les offsets 32 bits, les limites de 256 Mio et les risques de recouvrement du même buffer.
- Le test C++ couvre les deux géométries, les buffers tronqués et énumère les **2160 indices GPU** du cas natif pour prouver leur unicité et leurs accès source bornés.

Le fichier shader reste **Vulkan 1.1 / RDNA2**, avec les mêmes trois bindings storage et sept valeurs push. Le SPIR-V est généré et validé par le script préexistant `tools/graphics/test-rdna2-decoder-spv.py`, auquel le test hôte est déjà lié dans CTest.

**Limite honnête :** il s'agit de la primitive décodeur compatible avec les données natives, pas encore du raccord complet du GEMM appris 1024→512, du skip extérieur ni du rendu PS5. Les résultats CI, la parité numérique avec la capture de référence et la première image restent à démontrer.
