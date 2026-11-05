# Eden Encore — R07 FSR 3.1 temporel et R24 MSAA : état technique

**05/11/2026 — audit d'architecture, pas de build PS5 ni preuve console.**

## FSR 3.1 temporel : non intégré

Le chemin actuel « FSR 1 » est EASU/RCAS, purement spatial ; SGSR et
SGSR Edge sont aussi spatiaux. Le moteur de génération d'images FSR 3
(optical flow) étudié dans R08 **ne constitue pas** le FSR 3.1
Super Resolution temporel.

Une vraie intégration générique exige au minimum, par frame :
- **Couleur courante** avant la composition du HUD, échelle/crop/exposition,
  espace couleur et conversions clairement définis.
- **Vecteurs de mouvement** réels du moteur invité, à l'échelle et au
  repère attendus (avec objets animés), pas simplement le mouvement
  de la caméra déduit du rendu final.
- **Profondeur**, convention de Z, jitter courant/précédent,
  matrices caméra/temps écoulé, masques des matériaux réactifs
  et resets (pause, menu, changement de scène/jeu, résolution).
- **Historique Vulkan** persistant, réutilisation seulement après
  confirmation de fin GPU, synchronisation des queues/frames,
  budget VRAM et repli sûr vers FSR 1 lorsque les entrées manquent.

Les jeux Nintendo Switch 1/2 n'exposent pas tous ces signaux via une
interface standard à l'émulateur. Intercepter une API particulière
de DLSS dans un jeu NS2 peut suffire à **ce jeu**, mais pas à une
implémentation générique. L'ordre des opérations AA/upscale/HUD doit
aussi être prouvé avant activation.

**Prochaine réalisation vérifiable** : tracer les vrais producteurs
de depth/motion/jitter côté GPU invité, définir une structure de données
versionnée par frame, écrire un garde-fou strict de cohérence des entrées,
puis raccorder un backend Vulkan temporel réel. Les tests sans image
GPU ne suffisent pas à conclure à la qualité. Ne pas ajouter de
bouton « FSR 3.1 » tant que le backend ne reconstruit pas de frames.

## MSAA ×2 / ×4 / ×8 : non intégré

Le MSAA augmente les échantillons **pendant la rasterisation** ;
aucun filtre FXAA/SMAA, même exécuté 2/4/8 fois, n'est du MSAA.
Le renderer doit prouver :
- un format image réellement créé avec sample count >= 2,
  framebuffer/render-pass ou dynamic rendering compatible ;
- les opérations de **resolve** correspondantes, y compris pour
  depth/stencil lorsque la sémantique invité l'exige ;
- l'équivalence des lectures/écritures, des layouts mémoire et
  des échantillonnages/aliasing du guest NS1/NS2 ;
- la compatibilité PS5/Vulkan et le budget VRAM/bande passante
  pour les sample counts par format/résolution utilisés.

Un MSAA imposé globalement à des textures invitées préexistantes
peut modifier la sémantique du jeu ou casser les render targets ;
ce n'est pas un simple réglage du post-traitement Vulkan. Sur une
image déjà rasterisée, le post-AA **SMAA Ultra** et un upscale spatial
restent les solutions vérifiées en source. Le SSAA accessible via
la résolution interne 1,25× / 1,5× / 2× est une autre technique ;
2× en largeur/hauteur coûte 4× les pixels, sans devenir du MSAA.

**Prochaine réalisation vérifiable** : inventaire des MSAA sample counts
par format Vulkan, des cibles NS1/NS2 et de leurs resolves, puis test
isolé sur une scène dont le résultat guest reste correct. Ne pas
exposer un menu de ratios avant l'existence de ces surfaces.

## Décision et acceptation

R07 temporel et R24 MSAA restent **OUVERTS**. Aucune date ni
promesse de support n'est retenue. Le gain n'est pas démontré sur
FC 27, BOTW ni les jeux NS2. Aucun bouton factice, aucune
correction propre à un titre, aucune modification des versions de
référence. Le vrai pipeline doit passer validation des données,
compilation PS5, absence de régressions NS1, mesures qualité/VRAM/
frametime console, puis validation par titre.
