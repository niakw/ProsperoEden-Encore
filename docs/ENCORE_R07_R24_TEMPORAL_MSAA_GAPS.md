# Eden Encore — R07 FSR 3.1 temporel et R24 MSAA : état technique

**05/11/2026 — audit d'architecture et contrat C++ testé, sans build PS5 ni preuve console.**

## FSR 3.1 temporel : backend réel identifié, non intégré

Lichii nx2 propose un vrai backend GPU multi-passes
src/video_core/renderer_vulkan/vk_fsr3_upscaler.cpp avec
PrepareInputs, LumaPyramid, ShadingChange, Reactivity,
LumaInstability, Accumulate et RCAS ; les entrées sont typées
(color/depth/motion/jitter/frame_time). **Ce n'est pas** son
present/fsr3.cpp, qui n'est qu'un FSR spatial EASU/RCAS.

Lichii acquiert vecteurs de mouvement et profondeur depuis un
chemin invité de type DLSS NS2 (KeplerCompute, RasterizerVulkan,
TextureCacheRuntime). Ce chemin dépend de la détection d'une
chaîne de calcul donnée et ne prouve **pas** une acquisition
universelle sur BOTW, FC27 ni tous les jeux NS2.

Le contrat générique compilé dans
extras/graphics/fsr31_temporal_contract.h est vérifié par
test_fsr31_temporal_contract (ASan/UBSan). Il refuse
ressources manquantes, identité ou provenance estimée,
mélange de frames, conventions profondeur/motion inconnues,
jitter et timing invalides, HUD non séparé, work GPU non terminé,
historique discontinu et changement de scène.
**Ce contrat n'est pas encore un moteur FSR 3.1.**



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

## MSAA invité 2×/4×/8× : DÉJÀ présent, pas de forçage global

Le renderer Eden Vulkan accepte le **vrai MSAA demandé par le GPU
invité** : MaxwellToVK::MsaaMode convertit Msaa2x1, Msaa2x2 et
Msaa4x2 en VK_SAMPLE_COUNT_2/4/8_BIT, et prend aussi en charge 16×.
vk_graphics_pipeline.cpp utilise ces counts dans rasterizationSamples.
Le cache texture crée des images multisamples ; le render pass
prépare les resolves couleur et, lorsque disponibles, profondeur /
stencil ; blit_image.cpp gère les conversions entre samples.
tools/graphics/check-r24-msaa-native.py en audite le code hôte.

**Ce MSAA est natif et automatique quand le jeu le demande**.
Un réglage forcé 2×/4×/8× sur des surfaces invitées 1× pourrait
casser les résolutions, aliasing et lectures du jeu. Il n'existe
pas actuellement et ne doit pas être affiché comme livré.
La prise en charge PS5 précise reste à qualifier par format et
par jeu ; certains formats ou resolves peuvent être limités.

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

R07 temporel reste **OUVERT**. Le MSAA demandé par le guest est déjà implanté en Vulkan et son audit source est contrôlé, mais le forçage MSAA indépendant et la qualification PS5 demeurent **OUVERTS**. Aucune date ni
promesse de support n'est retenue. Le gain n'est pas démontré sur
FC 27, BOTW ni les jeux NS2. Aucun bouton factice, aucune
correction propre à un titre, aucune modification des versions de
référence. Le vrai pipeline doit passer validation des données,
compilation PS5, absence de régressions NS1, mesures qualité/VRAM/
frametime console, puis validation par titre.
