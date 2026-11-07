# Eden Encore R09 — ViT 8×5 opérations, chargement local et Vulkan

## Bloc ViT désormais assemblé en code

Le vendor contient désormais les composants réutilisables :

- `nr_rdna2_vit_ffn_weight_loader.h` / `nr_rdna2_vit_projection_layer_weight_loader.h` : import depuis NRMODEL1 local des matrices **Expansion [4096,1024]**, **Contraction [1024,4096]**, **Projection [1024,1024]** au format E4M3FN canonique du décodeur MIT ; deux vecteurs de gain **FP16×1024** pour contraction et projection. Toute matrice tronquée, facteur non fini ou NaN FP8 est refusé sans exposer d'état partiel. Aucune donnée propriétaire incluse.
- `NrRdna2VitProjectionStage` : utilise **le GEMM commun `NrRdna2Projection`** puis **`NrRdna2VitEpilogue`**, activation cubique et quantification pour expansion ou gain résiduel FP16 pour contraction/projection. Chaque opérateur est découpé en lots de tokens **≤1024** et prévalidé selon le scratch, les volumes et le plafond de calcul avant le premier dispatch. Le scratch FP32 est réutilisé après la barrière compute→compute.
- `NrRdna2VitBlock` : enchaîne les cinq couches **L0 Expand → L1 Contract (résidu=entrée du bloc) → L2 QKV → L3 attention globale → L4 Projection (résidu=sortie Contract)**. Le chemin QKV/attention GPU RDNA2 antérieur est réutilisé. Toutes les allocations, poids, descripteurs et buffers externes sont détenus par les propriétaires correspondants ; aucune sortie partielle n'est publiée à l'initialisation.
- `NrRdna2VitRun` : prépare et enregistre **8 blocs ViT consécutifs**, en refusant un bloc dont l'entrée ne correspond pas exactement (handle/offset/range) à la sortie du précédent. Résultat : tenseur de sortie FP8 1024 canaux pour le décodeur.

## Plan natif indépendant Original / Compact

`BuildNativeVitRoute` (host) valide les **40 opérations ViT** de chacun des corpus natifs 152/76, groupées en 8×5, avec toutes les dépendances et tous les canaux. Le premier bloc doit lire le **FinalHead du premier parcours Split-Swin** (Original 30→31, Compact 10→11) ; la dernière projection doit alimenter le décodeur (Original 38→39, Compact 18→19), qui référence en deuxième entrée le même bloc Split de saut. Deux familles de tests C++ s'ajoutent au CTest : le chargement d'un NRMODEL1 **synthétique** couvrant poids/FP16/NaN/troncature, et le routage des 8 blocs sur les deux corpus avec mutations négatives. Un autre test porte sur les six dimensions de projection 2560 et 4096 et les rejets de plan incomplet.

## Frontière FinalHead ↔ ViT : primitive disponible, géométrie corrigée

La PR vendor [#8](https://github.com/niakw/Prospero.Eden-Encore-vendor/pull/8) a depuis intégré `NrRdna2VitBoundaryRepack`, un kernel Vulkan natif de conversion des **2 160 tokens tuilés 4×4** en **2 560 tokens ViT** avec zéro explicite en padding, et la conversion inverse avant le décodeur.

**Correction après fusion sur main (7 novembre 2026) :** la première version du routeur `BuildNativeVitRoute` transmettait directement `W=60,H=33` depuis les colonnes de plan, alors que le `FinalHead` amont transpose ces deux axes : **33 colonnes × 60 lignes**. Les deux orientations occupent 2 160 tokens et passaient les contrôles de taille, mais la permutation des tuiles était incorrecte. Le routeur reprend maintenant `raster_width=s.height`, `raster_height=s.width` et vérifie la cohérence avec le premier parcours Split-Swin. Les tests hôtes vérifient la même géométrie côté Split/ViT pour Original et Compact et différencient les deux ordres de tuiles.

Ce correctif **ne signifie pas** que le graphe entier est exécuté : le chaînage complet FSwin/ViT/décodeur, le raccord renderer et la parité d'image restent à démontrer.

Les huit blocs et leurs poids sont publiés en source, mais **aucune compilation Vulkan complète, aucune CI native ni exécution GPU/PS5 ne sont confirmées** à ce stade. La parité numérique, les chemins pré/post, le passage vers le décodeur et la preuve de première image restent ouverts. Ni activation dans l'UI ni build PS5 avant P5.
