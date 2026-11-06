# Eden Encore — R07 FSR 3.1 temporel et R24 MSAA : état technique

**06/11/2026 — backend Vulkan, garde-fous et sortie framebuffer vérifiés syntaxiquement ; aucun build PS5 complet ni preuve console.**

## FSR 3.1 temporel : moteur AMD natif compilable, entrée invité manquante

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
Le vendor maintenant épinglé sur `a8a6bdf6a` contient un **vrai moteur
AMD FSR 3.1.4 multi-passes Vulkan**, adapté depuis Lichii,
avec la copie source du SDK AMD v1.1.4 sous licence MIT.
Les **11 passes GPU** produisent toutes du SPIR-V 1.3 valide ;
le port C++ du scheduler et ses descripteurs SAMPLED_IMAGE /
SAMPLER séparés passent la compilation syntaxique hôte.
Le CMake PS5 ajoute ces unités au video_core sans build
conditionnel expérimental.

Le pont natif refuse désormais les formats d'entrée non reconnus et
vérifie un budget mémoire FSR 3.1 nominal avant allocation (contrôle
conservateur, sans preuve de capacité PS5). Il vide les deux jeux
ping-pong d'historique lors d'une réinitialisation temporelle.

Le pont R07 compare désormais les identités réelles VkImage/VkImageView des
trois entrées GPU invitées aux identités de provenance déclarées. Un
handle absent, substitué ou une vue commune aux entrées couleur,
profondeur et mouvement invalide la continuité temporelle. Les formats
d'entrée doivent également avoir la capacité Vulkan SAMPLED_IMAGE du
GPU hôte. Le test natif test_fsr31_native_resource_contract couvre ces
cas. Cette vérification ne remplace pas le producteur GPU invité encore
absent ni la validation console.


Le pont natif possède maintenant `TryRecordToGuest` : sur un
**framebuffer invité réellement validé** (une seule cible couleur
1×, taille de sortie identique), il enchaîne les passes FSR 3.1,
une copie via le blit Vulkan réel, puis la transition de l'image
résultat de `SHADER_READ_ONLY_OPTIMAL` vers `GENERAL` afin de
permettre la prochaine écriture compute. Il ne s'exécute pas sans
producteur d'entrées invitées et ne remplace pas le chemin de
présentation du jeu de manière automatique.

Sur une réinitialisation temporelle, les dimensions de référence
et le jitter précédent sont désormais synchronisés avec la frame
courante, même lorsque les allocations Vulkan sont réutilisées.
Le moteur bloque une tentative répétée après une défaillance
d'allocation Vulkan récupérable (fallback sûr). Les erreurs
`VK_ERROR_DEVICE_LOST` restent fatales : elles ne sont pas
masquées par un choix d'upscaler.
L'audit ABI contrôle aussi que **chaque** binding de shader,
dont les deux samplers, est effectivement présent et typé ;
les ressources manquantes ne peuvent plus passer silencieusement.

Le pont natif exige couleur, profondeur reversed-Z, mouvement
en pixels, vrai jitter, vraie projection du jeu, frames cohérentes,
GPU synchronisé et HUD invité/natif séparé. Il réinitialise
l'historique si des frames manquent ou la scène change.
L'ancien FOV 60 degrés par défaut du port externe a été supprimé.

La réserve VRAM du moteur FSR 3.1 est vérifiée avant la création
ou le redimensionnement des images intermédiaires : taille calculée
à partir des formats réels, plafond strict de 512 MiB et contrôle
sur le budget local disponible. La profondeur et les vecteurs de
mouvement acceptés sont désormais limités aux formats réellement
attendus par les shaders. La mise à zéro des deux historiques
ping-pong est imposée lors d'un changement de scène pour éviter
un ghosting venant des ressources de la scène précédente.

**Blocage vérifié : le GPU invité actuel d'Encore ne fournit pas
de source générique complète de ces données pour tous les jeux**.
Le moteur FSR3.1 est donc compilable et raccordé comme composant
native Vulkan, **mais sans dispatch en jeu ni présentation de
frames temporelles PS5**. Ne pas créer un bouton fonctionnel fictif.



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

**Prochaine réalisation vérifiable** : raccorder un véritable
producteur GPU invité générique de depth/motion/jitter/projection
au moteur FSR 3.1 désormais compilable, puis raccorder sa sortie
au framebuffer invité, avec séparateur HUD et repli FSR 1. Les tests sans image
GPU ne suffisent pas à conclure à la qualité. Ne pas ajouter de
bouton « FSR 3.1 » tant que le backend ne reconstruit pas de frames.

## MSAA invité 2×/4×/8×/16× : DÉJÀ présent, forçage ouvert

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

Pour le forçage volontaire Auto / 2× / 4× / 8× / 16×,
le code extras/graphics/msaa_force_policy.h vérifie la
compatibilité Vulkan **par format**, les dimensions,
le budget mémoire, les alias/lectures invitées ainsi que
l'existence d'un attachement multisample hôte dédié et des
resolves couleur/profondeur vers le vrai framebuffer invité.

Le garde-fou reste conservateur : `ShadowRendererNotImplemented`
reste le résultat tant que le moteur de rendu complet n'est pas
raccordé. Le vendor `1068722ab` apporte le **composant natif
Vulkan couleur** : une image multisample temporaire, une image view,
un framebuffer avec render pass et resolve couleur vers la surface
1× originale, sous conditions strictes (un seul attachement couleur,
clear intégral, aucune profondeur, aucun aliasing/lecture incompatible,
formats et budgets contrôlés). Le composant invalide son framebuffer
si l'image **ou la vue** invitée change.
Le renderer vérifie désormais les capacités d'échantillonnage du
format, du type d'image, de son usage (attachement couleur transient)
et de ses dimensions via `vkGetPhysicalDeviceImageFormatProperties`.
Le seul masque global de samples ne suffit donc plus à autoriser 16×.
L'extension `VK_EXT_multisampled_render_to_single_sampled` nécessite
notamment un flag de création spécifique pour les images invitées 1×,
et ne peut pas être activée aveuglément sur les textures existantes.

Le composant shadow exige maintenant également la **vraie
couleur de clear du GPU invité**, passée au render pass Vulkan :
un clear complet n'implique pas un clear noir. Les erreurs de
mémoire GPU sont distinguées des formats incompatibles ; une
perte de périphérique Vulkan ne doit pas être déguisée en
simple désactivation d'anti-aliasing.

L'audit du pilote PS5 `encore-active/ps5-mesa` montre que la
fonction `radv_msrtss_enabled` de l'extension
`VK_EXT_multisampled_render_to_single_sampled` ne s'active
que sur Android ou avec `RADV_EXPERIMENTAL_MSRTSS`.
Par conséquent, cette extension **n'est pas adoptée** comme
chemin général : elle n'est pas une solution de production
disponible par défaut sur notre PS5. Le chemin à attachements
MSAA séparés conserve ses propres exigences de sauvegarde/
rechargement des contenus en cas de draws multiples et de
lectures/écritures invitées.

Le scheduler natif possède désormais RequestNativeColorResolveRenderpass
et FinishNativeColorResolveRenderpass : vrai renderpass Vulkan avec image
shadow MSAA + attachement de resolve invité 1x, et barrières de visibilité
de ces deux images après fermeture. Plusieurs draws consécutifs gardent
le pass actif sans nouveau clear intempestif. Le composant vérifie
explicitement que VkRenderPass et rasterizationSamples du pipeline
correspondent au pass shadow, que les textures lues ne sont pas
aliasées avec le RT, et que le clear invité est réellement connu.
La fermeture du pass vérifie son identité et ne termine jamais par
erreur un autre renderpass invité. Cette partie compile sur hôte
avec les vraies sources Vulkan et passe les tests de politique.
Le pipeline guest doit encore être construit dans sa variante
multisample ET sélectionné au draw : ce code ne l'active pas seul.

**Ce composant n'est pas appelé par le chemin des draws invités** : la
sélection du pipeline rasterisationSamples, les clears, l'ordre des
barrières/lifetimes et les attachments depth/stencil ne sont pas
raccordés ni validés sur console. Il n'existe donc toujours aucun
MSAA forcé utilisable par l'utilisateur. Il serait dangereux de
modifier directement le champ samples des textures invitées ;
aucun mode forcé n'est présenté comme effectif dans l'interface.

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

**Prochaine réalisation vérifiable** : relier la préparation de l'image
couleur multisample au pipeline guest, avec un pipeline Vulkan du même
sample count et l'enregistrement réel d'un render pass complet ; ajouter
ensuite les attachements profondeur/stencil et les formats/draws pris en
charge. Auditer les cibles NS1/NS2, les transitions et le budget,
puis tester une scène dont le résultat guest reste identique. Ne pas
exposer un menu de ratios avant l'existence de ces surfaces.

## Décision et acceptation

R07 temporel reste **OUVERT**. Le MSAA demandé par le guest est déjà implanté en Vulkan et son audit source est contrôlé, mais le forçage MSAA indépendant et la qualification PS5 demeurent **OUVERTS**. Aucune date ni
promesse de support n'est retenue. Le gain n'est pas démontré sur
FC 27, BOTW ni les jeux NS2. Aucun bouton factice, aucune
correction propre à un titre, aucune modification des versions de
référence. Le vrai pipeline doit passer validation des données,
compilation PS5, absence de régressions NS1, mesures qualité/VRAM/
frametime console, puis validation par titre.
