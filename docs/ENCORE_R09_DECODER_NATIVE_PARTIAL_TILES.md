# R09 — décodeur neuronal RDNA2 sur les dimensions natives (7 novembre 2026)

Le `CCDecInputUpsample` de la source MIT `Overclockers/DLSSNR-AMD` utilise, au niveau goulot 1080p, les constantes `IW=prev.H=33`, `OW=s.H=33`, `OH=s.W=60`. Le code de Prospero Eden n'acceptait que `IW×2=OW`, `IW` multiple de 4 et `OW/OH` multiples de 8. Il était donc **inexécutable pour le vrai plan Original ou Compact**, indépendamment du fait que les shaders compilent.

## Changement de la primitive partagée

- Le prévol `CanDecoderUpsample` admet la largeur native **33→33** ou le cas antérieur **4→8**, sans accepter d'autres rapports d'échelle ; l'algorithme continue à prélever `floor(x/2),floor(y/2)` comme le shader de référence.
- Le mapping de token utilise `ceil(width/4)` comme vraie ligne de tuiles. À `33×60`, cela donne **9×15 tuiles = 2160 tokens**, dont **1980 valides et 180 de padding**. Sans ce ceil, les tokens de la dernière colonne et de la ligne suivante s'aliasaient.
- Le shader exécute toutes les positions de tuiles, **écrit zéro dans les 180 tokens inutilisés** sur chaque passe, et lit les résidus uniquement pour les pixels valides. Il n'envoie jamais un canal dupliqué à deux adresses identiques dans la même invocation.
- Les bornes hôte couvrent la source FP16 tuilée, l'entrée skip et la sortie E4M3FN **avec padding**, les gains, les offsets 32 bits, les limites de 256 Mio et les risques de recouvrement du même buffer.
- Le test C++ couvre les deux géométries, les buffers tronqués et énumère les **2160 indices GPU** du cas natif pour prouver leur unicité et leurs accès source bornés.

Le fichier shader reste **Vulkan 1.1 / RDNA2**, avec quatre bindings storage (skip et destination séparés) et sept valeurs push. Le SPIR-V est généré et validé par le script préexistant `tools/graphics/test-rdna2-decoder-spv.py`, auquel le test hôte est déjà lié dans CTest.

**Limite honnête :** le décodeur est désormais couplé au GEMM appris et au skip via les passages décrits ci-dessous, mais pas encore intégré au réseau global ni validé par une image PS5. Les résultats CI, la parité numérique avec la capture de référence et la première image restent à démontrer.

## Lot complémentaire — décodeur appris, entrée et sortie séparées

Le vrai enchaînement est maintenant implémenté en source dans le vendor :
`NrRdna2NativeDecoderLink` charge la matrice NRMODEL1
`unpacked-splitswin/block39.layer0.layer.weight.bin` (Original) ou
`block19` (Compact), exactement **512×1024 E4M3FN**, et les **512 gains
FP16** `skip_weight.bin`. Le décodeur exécute sur le scheduler Vulkan
`NrRdna2Projection` → le nouveau `NrRdna2DecoderFp32ToFp16` →
`NrRdna2DecoderUpsample`, sans lecture CPU des activations.

À 33×60, **1980 tokens GEMM** sont calculés par deux lots de
**1024 + 956**, tandis que le flux FP8 source reste un raster de **2160
tokens tuilés** (dont 180 de padding). Le scratch FP32 est réutilisé et le
résultat FP16 possède sa propre allocation, puis le décodeur lit seulement
ses indices spatiaux nécessaires. La sortie GPU est un buffer E4M3FN
distinct du skip : **aucune allocation partagée ni recouvrement implicite**.

L'ancien shader avait trois bindings dont un arena `Activations`
commun skip/sortie. Il a été refactoré en **quatre** bindings
`projection(0),skip_features(1),output_features(2),gains(3)`, et le
wrapper, la politique mémoire et le validateur SPIR-V ont été alignés.
Les 7 constantes push restent inchangées. Le shader de conversion FP32
→ FP16 utilise `packHalf2x16` disponible avec Vulkan 1.1, sans
extension FP16/FP8 ni calcul coopératif.

Les trois nouveaux contrôles couvrent les tokens 1980/2160, les batches
et offsets, le shader SPIR-V, les tailles des buffers, le modèle synthétique
NRMODEL1 et les refus des gains non finis et poids invalides.

## Raccord réel du skip Split-Swin vers le décodeur

La passe GPU `NrRdna2SplitDecoderSkipRepack` a été ajoutée au vendor et
appelée directement par `NrRdna2NativeDecoderLink::Record()` **avant le
décodeur**. Elle accepte la sortie FP8 primaire de `ProjPool` (40 fenêtres
8×8 × 512 canaux), recompose le raster 33×60 et écrit les 2160 tokens
du skip au format `at(token,channel)` utilisé dans le décodeur :
tuiles spatiales 4×4 et sous-blocs de 16 tokens × 16 canaux.

La version native **33×60** lit jusqu'au token source 2508,
écrit le dernier token valide 2156 et **initialise à zéro les 180 tokens
de padding**, sans aliasing entre les buffers. Le test C++ valide
chaque index et chaque mot de 4 canaux pour 33×60 et cinq dimensions
de régression ; l'ABI SPIR-V conserve **2 buffers, 5 constantes push,
Vulkan 1.1**.

Le décodeur accepte désormais deux entrées distinctes
`source_split_skip_windows` et `tiled_split_skip` ; il détient
la passe GPU de repacking et enchaîne ensuite projection
1024→512, quantification FP16 et upsampling appris.

**Reste ouvert :** l'orchestrateur complet 152/76 couches, la tenue des
skips U-Net à tous les niveaux, les adaptateurs pré/post image et le
raccord au renderer. Les tests SPIR-V/C++ sont ajoutés mais
**aucune CI verte ni image PS5 n'est encore revendiquée**.
Aucun build complet PS5 avant P5.
