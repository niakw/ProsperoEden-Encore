# Eden Encore R09 — entrée proxy vers 16 canaux (7 novembre 2026)

**Statut : primitive RDNA2 ajoutée, non branchée au renderer PS5 ; aucune
preuve de frame NR ni de parité numérique GPU.**

Référence indépendante MIT :
[OpenDLSS-NR shaders/preprocess.comp](https://github.com/maanHimself/OpenDLSS-NR/blob/main/shaders/preprocess.comp)
et [docs/network.md](https://github.com/maanHimself/OpenDLSS-NR/blob/main/docs/network.md).

La génération suit l'ordre connu des 16 canaux : bruit gaussien
déterministe en 0–2, constante 1 en 3, trois valeurs couleur centrées
sur le proxy sRGB en 4–6, copie du proxy **sans historique** en 7–9,
style/ton/structure/peau/masque en 10–14, zéro en 15.

Le shader `proxy_features_rdna2.comp` lit un buffer `RGBA32F`
**déjà normalisé display-referred**, applique la géométrie miroir
pour la zone paddée, puis produit un buffer `FP16[16]` par pixel.
Il se raccordera à `NrRdna2ImageFeatureStage` (matrice locale
apprise FP16[32×16] → E4M3FN[32]) sans copier les poids NVIDIA.

Le réseau public produit initialement des f32[16] : le stockage
intermédiaire FP16 de ce port doit encore être comparé à la
référence avant d'être qualifié exact. Les bornes hôte vérifient
dimensions, miroir unique, tailles de buffers, valeurs de
conditionnement, limite 256 Mio et descripteurs STORAGE distincts.
Les en-têtes SPIR-V Vulkan 1.1 sont générés et vérifiés en CI.

**Manquent toujours :** production du proxy depuis la couleur HDR
réelle du jeu et son exposition, historique/profondeur/mouvement,
le prébloc Swin+downsample, les gains U-Net C64/C128/C256,
le réseau complet et le compositing postbloc. Aucune de ces étapes
n'est remplacée par une approximation cachée.

## Raccord GPU première image → input lift

`NrRdna2ProxyLiftLink` ordonne désormais deux passes, sur **le même
scheduler Vulkan** : proxy display-referred RGBA32F → FP16[16] →
projection apprise `input_lift` → FP8[32]. Le moteur contrôle que
les deux étages utilisent exactement **le même VkBuffer**, offset et
étendue pour le tampon intermédiaire, que le lift soit de direction
0 (pas la projection post-image), que les géométries soient égales,
et que ni le buffer source ni la sortie C32 ne soient aliasés.
Un échec partiel n'est pas relancé silencieusement.

Le test de politique vérifie l'Original 1920×1080 et le padding
1920×1152 (hors profil natif utilisé par nos fixtures), les formes
fausses, les modes incorrects et la capacité. Le compile-check R09
inclut ce nouveau vrai fichier C++.

**Reste à raccorder** le FSwin du prébloc et son downsample, les
niveaux U-Net, puis le postbloc et le compositing final. Ceci n'est
pas un pipeline NR complet et ne doit pas apparaître comme activable.

## Raccord GPU vers le premier FSwin C32 (7 novembre)

Le vendor ajoute `NrRdna2ProxyFSwinLink`, qui enregistre dans l'ordre
proxy display-referred RGBA32F → FP16[16] → input_lift local →
raster E4M3FN[32] → fenêtres FSwin C32 de 8×8 tokens → bloc(s) FSwin.
Le transfert raster→fenêtres utilise `NrRdna2FSwinChain::BindRasterInput`
sur le même scheduler Vulkan et les mêmes buffers GPU sans lecture CPU.
Le validateur vérifie les axes explicites (240×135 à 1920×1080),
le padding facultatif, le nombre de canaux, les vues de ressources,
les tailles minimales, les décalages de fenêtres, ainsi que les refus
de dimensions et de capacités incorrectes. Un chainage échoué ne peut
pas être rejoué implicitement ; un terminal raster/downsample est
nécessaire avant le Record si le segment l'exige.

**Qualification :** test de contrat hôte GCC/Clang+UBSan et syntaxe Clang
des deux nouveaux propriétaires C++ intégrés au workflow R09 ;
état réel des jobs à vérifier après publication.
**Toujours absent :** extraction de source HDR du renderer, modèle
et poids de prébloc étendus, liaisons U-Net, postbloc, compositing,
exécution intégrale et mesure GPU/PS5. Le raccord ne doit pas rendre
DLSS-NR activable par défaut.

### Ordonnancement avec les niveaux U-Net

Le raccord propose aussi `RecordEntryOnly()` : on peut enregistrer
le proxy et la projection C32 **sans** exécuter deux fois le premier
FSwin, puis confier ce segment au propriétaire d'arête U-Net
(`NrRdna2FSwinLevelLink` ou `NrRdna2UNetSkipCache`).
Les deux modes d'enregistrement sont mutuellement exclusifs et à usage
unique. Le raccord complet du réseau demeure non qualifié.
