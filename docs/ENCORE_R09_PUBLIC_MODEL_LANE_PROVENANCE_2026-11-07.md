# R09 — Contrat des 16 canaux image : preuve indépendante et compatibilité à vérifier

**Référence MIT** : [OpenDLSS-NR `docs/network.md`](https://github.com/maanHimself/OpenDLSS-NR/blob/main/docs/network.md),
[`docs/frame.md`](https://github.com/maanHimself/OpenDLSS-NR/blob/main/docs/frame.md) et
[`demo/shaders/nr_preprocess.comp`](https://github.com/maanHimself/OpenDLSS-NR/blob/main/demo/shaders/nr_preprocess.comp).

Ce projet tiers a une implémentation Vulkan et WebGPU du réseau de 71 blocs
et affirme une parité octet par octet sur des captures indépendantes.
C'est une **source de spécification à confronter**, pas une preuve
de compatibilité des plans Original/Compact d'Eden Encore.

## Spécification image documentée

| Canaux | Encodage |
| --- | --- |
| 0–2 | Trois composantes gaussiennes depuis un hash dépendant des coordonnées **padding** et de la seed |
| 3 | Constante 1 |
| 4–6 | Proxy couleur sRGB d'un HDR normalisé à `paperWhite`, avec épaule hautes lumières, centré par arrondis FP16 successifs |
| 7–9 | Proxy historique reprojeté dans le même encodage ; à la première frame / sans historique, recopier 4–6 |
| 10 | Style / 128 |
| 11 | Conditionnement tonal local |
| 12–14 | Structure, peau et auto-mask conditionnels, avec sentinelles négatives |
| 15 | Zéro |

La sortie finale de cette autre implémentation est **4 canaux F32** :
trois résidus RGB du proxy de l'image et un logit de mélange temporel.
Le mélange de l'historique inclut un gain `blendScale` appris ; il ne
faut pas traiter le quatrième canal comme alpha graphique ordinaire.

Le halo HDR utilise une normalisation paper-white et une épaule
non linéaire ; l'historique est reprojeté avec les vecteurs de
mouvement de la scène et rejeté lorsqu'il n'est pas visible.
La source décrit la conservation de la lumière HDR au compositing.
Ne pas réutiliser l'image précédente sans compensation de mouvement
et sans rejet de disocclusion.

## Incompatibilité géométrique non encore résolue

Dans OpenDLSS-NR, une image **1920×1080** est paddée
**1920×1152** ; le dernier niveau annoncé est **32×20**.
Les deux fichiers de plans R09 d'Eden Encore enregistrent quant à eux
le passage Split/ViT natif en **33×60** avec 1 980 positions actives
et 2 160 tokens tuilés.

La sortie et le nombre de blocs peuvent se ressembler, mais ces
géométries **ne sont pas interchangeables**. Avant de lier un shader
de prétraitement de l'autre projet à notre moteur il faudra prouver
le mapping de chaque opération, du padding, du décalage de fenêtre et
des données correspondantes pour nos deux modèles. Un simple swap
de largeur/hauteur ou l'insertion silencieuse de zéros ne le prouverait
pas. Notre correctif Split→ViT 33×60 reste celui du plan de test R09.

Le primitive ajoutée dans `nr_rdna2_image_feature_stage.cpp`
attend une entrée **déjà préparée** FP16[16], à alimenter après une
conversion/arrondi défini. Le projet tiers part de caractéristiques
F32[16] avant conversion. Leur concordance numérique doit être
mesurée sur un modèle local et un corpus de référence.

## Reprise de l'intégration

1. Établir l'identité des modèles et du nombre réel de halving, sans
   présumer que 71 blocs impliquent la même grille.
2. Construire la texture proxy HDR→SDR bornée sur le runtime Vulkan
   natif de la PS5, avec des guides valides, sans injecter NGX.
3. Générer les 16 caractéristiques et comparer les bytes de référence,
   **sans** exposer NR aux utilisateurs avant la chaîne complète.
4. Relier les poids de PreBlock/PostBlock, les gains U-Net restant et le
   compositing final 4 canaux après parité.

Pas de poids NVIDIA ou binaires tiers distribués. Pas de FPS PS5
revendiqués ; ne pas activer l'option par défaut.
