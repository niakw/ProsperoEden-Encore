# C / R08 — Vulkan frame generation (état vérifiable)

Branche : `feat/encore-c-vulkan-framegen`. Ne pas fusionner `main` ni modifier le vendor pour de simples contrats.

## Priorités et choix d'intégration

| Ordre | Méthode | Source / licence | État concret | Prochaine preuve |
|---|---|---|---|---|
| 1 | MihawkGen natif PS5 | `mihawk-99/PS5_MihawkGen` @ `c57232a`, module `framegen/` GPL-3.0-or-later, outillage PS5 MIT ; modèle `network.fgw` à auditer avec notices | Source épinglée en sous-module, **aucun code de génération branché dans le renderer Encore** | Construire module et modèle sur la toolchain PS5, vérifier Vulkan/RADV, layouts/barrières/fences et premier couple d'images |
| 2 | FSR 3.1 Frame Generation | AMD FidelityFX SDK, code MIT ; nécessite flux temporal/motion/depth et swapchain Vulkan qualifiés | Contrat R06 seulement | Prouver depth/motion/jitter invités, HUD distinct, profil de latence ; comparer aux mêmes images |
| 3 | LSFG / Lossless Scaling | Intégration amont ProsperoEden pouvant dépendre d'une DLL Windows non redistribuable | Non intégré à Encore ; aucune DLL embarquée | Confirmer droits de distribution et backend **natif PS5** ; sinon refuser cette option |

Le sous-module MihawkGen, pas les fichiers de son `external/` en bloc, constitue la provenance. Avant diffusion de tout modèle, confirmer séparément code, poids et notices. Selon le README MihawkGen, le réseau fourni a été entraîné sur des clips privés, avec certaines cibles distillées de modèles publics sous licences permissives : l’attribution et les conditions des poids sont à vérifier avant packaging. La présence du fichier dans le sous-module ne constitue pas une autorisation de redistribution dans les Releases Encore.

## Premier garde-fou exécuté

`extras/graphics/framegen_present_gate.h` et son test sont **hôte uniquement**, sans branchement d'un backend. Il ne produit pas de fausses frames ; il n'autorise qu'une demande de frame synthétique si :

- le moteur Vulkan, les fonctions requises et les poids/conditions du fournisseur sont prouvés ;
- le taux de la sortie a été **négocié**, le jeu est à au moins 30 FPS réels et la sortie a de la marge ;
- les deux frames sources sont consécutives, les timestamps monotones et la cadence stable ;
- pas de pause/menu, changement de résolution/TV, changement d'overlay ni interruption ;
- un seul intermédiaire maximum, pas de prétendu 30→120 en première itération.

Les FPS réels du jeu restent distincts de la fréquence affichée. Les appels aux commandes Vulkan et la gestion de lifetime des images/fences **restent à intégrer**. Les états de l'application ne doivent pas laisser croire que MihawkGen/FSR3/LSFG fonctionne avant le branchement effectif.

Test hôte : `SDKROOT=/Library/Developer/CommandLineTools/SDKs/MacOSX15.4.sdk clang++ -std=c++20 -Wall -Wextra -Werror -fsanitize=undefined extras/graphics/test_framegen_present_gate.cpp -o /tmp/test_framegen_present_gate && /tmp/test_framegen_present_gate`.

## Jalons à clôturer

1. **C1, présent :** sources/version/licence sélectionnées et garde de cadence prouvé sur hôte ; aucun test PS5.
2. **C2, ouvert :** les 4 unités C++ Mihawk passent la syntaxe hôte et les 21 shaders SPIR-V passent `spirv-val --target-env vulkan1.3`; le modèle `network.fgw` (1 757 240 octets) est épinglé à SHA-256 `31ecc7d69af1e9defd62b9abad71bc3430cd8a0a4d2f4eafcabaafa48c34bf6b`. La cible de production `eden-mihawkgen-native` compile les objets du moteur, avec des symboles Volk distincts, dans `video_core`. Le renderer doit encore les appeler avant de pouvoir générer des frames. Compilation/toolchain GPU PS5 et chargement autorisé du modèle restent à prouver. Ne pas activer le mode dans l'UI tant qu'inexécutable.
3. **C3, ouvert :** enchaînement réel frames précédent/courant/synthétique avec mémoire, ownership, layouts, barrières, fences et timing PS5 ; repli sans régression NS1/NS2.
4. **C4, partiel :** la catégorie **Paramètres > Vidéo** affiche « Génération d'images : Désactivé » avec explication MihawkGen / FSR3 / LSFG. Cette ligne refuse toute activation tant que le runtime PS5 n'est pas validé. Les 29 catalogues ont été mis à jour, y compris le fallback français embarqué ; contrôles de couverture : 477/477 clés. Les sélecteurs opérationnels, la sérialisation et les profils par jeu restent ouverts.
5. **C5, ouvert :** A/B visuel et latence PS5 ; comparer FSR 3 sur même scène, accepter/refuser LSFG selon la faisabilité native et la licence.

## Point de sécurité découvert dans le port amont ProsperoEden

Le wrapper d'exemple `mihawkgen.cpp` de ProsperoEden applique `VK_IMAGE_LAYOUT_UNDEFINED` aux images couleur source. Cela peut invalider leur contenu ; l'exemple n'établit pas, à lui seul, l'ownership de plusieurs frames en vol ni les fences nécessaires. **Ne pas copier le bloc tel quel en production.** Avant d'activer l'option, relever les layouts réels, attendre les fences des buffers relus et ajouter une passe de présentation des images générées sans écraser les images encore lues par Vulkan.

## C2 — source native Vulkan et sécurité des images (vendor c62ecbb)

L'analyse du renderer réellement copié par headless/vulkan.cmake et
du PresentManager a établi le chemin suivant :

1. BlitScreen::DrawToFrame compose la frame source; le renderpass termine
   en layout GENERAL. PresentManager::CopyToSwapchainImpl suppose GENERAL,
   utilise un transfert puis restaure GENERAL.
2. Les Frame* acquis par GetRenderFrame retournent dans free_queue
   après présentation : **il est dangereux de conserver Frame* comme
   historique d'une interpolation**. Deux images privées stables sont nécessaires
   pour les entrées précédentes/courantes.
3. Le chemin de génération historique du renderer est derrière
   HAS_LSFG. Sa présence n'atteste **pas** d'un backend MihawkGen PS5.
4. Sans HAS_LSFG, CanStoreToFrame refuse le stockage direct dans les
   images de présentation. Le modèle Mihawk exige un output **RGBA8 storage**;
   sur swapchain BGRA8, une image RGBA8 distincte et un vkCmdBlitImage
   avec formats/usage vérifiés sont requis.
5. Le composite actuel passe draw_hud=true. Le **HUD n'est pas isolé**
   du chemin de présentation ; un effet temporel actif pourrait produire
   du ghosting sur le score/menu.

### Code ajouté dans le lot de sécurité

- mihawk_native_surface_contract.h refuse les chemins sans propriétaire
  des images d'historique, slots/fences, format, conversion, HUD isolé et
  synchronisation du presenter prouvés. Le mode non qualifié reste OFF.
- mihawk_vulkan_history_barriers.h définit les transitions exactes
  GENERAL → TRANSFER_SRC → GENERAL de la vraie frame, les transitions
  des snapshots privés et celles de l'output RGBA8.
- mihawk_vulkan_stage.cpp **enregistre réellement** les commandes Vulkan
  vkCmdPipelineBarrier, vkCmdCopyImage, fg_record_generate et vkCmdBlitImage
  vers une image synthétique **uniquement si un appelant fournit toutes
  les ressources et préconditions**.
- headless/vulkan.cmake ajoute cette unité à la cible de validation
  EDEN_BUILD_MIHAWKGEN_CORE=ON, encore **OFF par défaut** et non liée au
  binaire de production.
- tools/graphics/check-r08-host.sh exécute quatre tests de règles,
  barrières et séquence de commandes. Le dernier module utilise des
  mocks de commandes Vulkan : preuve de l'ordre, des paramètres et du refus
  avant enregistrement, **pas** d'exécution GPU PS5.

**Travail restant :** allocateur avec budget VRAM, propriété des deux
snapshots, fences jusqu'à la fin des lectures GPU, frames/timestamps réels,
séparation HUD, réinitialisation après pause/jeu/changement de sortie,
branchement sur le renderer actif, qualification modèle et RADV/PS5, benchmark
sur console. Ne jamais coder les booléens de preuve à true artificiellement.

### C2.1 — allocations GPU privées (source fonctionnelle, tests hôtes)

L'implémentation isolée mihawk_vulkan_resources.cpp ajoute :

- Deux textures d'historique au **format de la source compositée**, avec
  VK_IMAGE_USAGE_SAMPLED_BIT et TRANSFER_DST, séparées des Frame* recyclés.
- Une troisième texture de sortie **RGBA8 storage + TRANSFER_SRC**, propriété
  du module, avant la conversion éventuelle vers une frame BGRA8.
- Vérification préalable des capacités Vulkan (sample/transfer/blit/storage),
  choix d'un type mémoire DEVICE_LOCAL, allocation/bind/views distincts.
- Plafond configurable par défaut à 128 Mio; validation du coût **réel**
  renvoyé par vkGetImageMemoryRequirements, limite initiale 3840 x 2160.
- Repli intégral si format, mémoire, allocation, bind ou vue échoue :
  aucun état « prêt » sur une allocation partielle.
- Destruction avec vkDeviceWaitIdle **uniquement à l'arrêt ou au reset de
  ressources**, et jamais au fil des frames. L'objet doit mourir avant VkDevice.

Le test sans GPU simule les appels Vulkan de création, destruction et erreurs
de mémoire/images/views; exécution ASan/UBSan positive. Il ne mesure pas la
VRAM ni la vitesse d'un pilote PS5. Il reste à brancher l'allocation à un
RendererVulkan réel, à surveiller les fences/descripteurs et à isoler le HUD.
L'allocation ne rend donc pas MihawkGen utilisable dans l'application.


## C — comparaison FSR 3 / LSFG et limites de licence

L'audit du dépôt Swordpdf/ProsperoEden (branche publique au 05/11/2026)
confirme que LSFG est activé via ENABLE_LSFG/HAS_LSFG, mais son chemin
utilisateur s'appuie sur une copie personnelle de Lossless.dll et
ProsperoEden précise ne pas pouvoir distribuer cette bibliothèque.
**Ne pas copier, demander ni redistribuer la DLL sous Encore.**
Une solution compatible ne peut être affichée que si un moteur PS5
natif/portable légalement redistribuable est démontré, puis testé.

Le SDK officiel FidelityFX d'AMD expose une interface Vulkan FSR 3 pour
la génération d'images, y compris un callback de composition de l'UI
et une gestion propre de la présentation. Le chemin Encore actuel ne
dispose pas d'un jeu prouvé de motion vectors/depth/jitter invités.
La présence des API AMD **ne signifie pas** qu'un fallback FSR 3 est
disponible ou que les méthodes sont interchangeables. MihawkGen reste
le premier candidat natif; comparaison métrique FSR 3 ensuite.

Les modes par titre ou globaux (MihawkGen, FSR 3, LSFG) ne doivent
apparaître comme sélectionnables que lorsque le backend correspondant
possède une preuve du rendu natif PS5. La ligne UI désactivée actuelle
reste un état honnête.

## C2.2 — HUD de jeu distinct du HUD d'Encore

WindowAdaptPass::Draw se termine par le dessin du HUD **Encore** après
les surfaces invitées, dans le même render pass. Ce HUD spécifique peut
en principe être déplacé après l'interpolation par un passe séparée
sous feature flag, mais **les scores, menus et glyphes du jeu sont déjà
dans les surfaces compositées invitées**. Retirer le HUD d'Encore avec
draw_hud=false ne sépare donc pas le HUD *du jeu*. Il faut refuser
d'appeler cette modification une « séparation HUD » complète. Prévoir
un masque/historique du jeu ou un repli lorsque les overlays invités
rendent la génération visuellement inacceptable. Validation FC27/BOTW
nécessaire avant activation générale.

### C2.3 — suivi des soumissions et fences GPU (hôte)

Le nouveau `MihawkSubmissionTimeline` décrit un protocole
`Prepare / Commit / Abort`. Il consomme des **numéros de soumission et
d'achèvement GPU réels**, pas des indices de frame côté CPU :

- Le slot de capture 0/1 est bloqué tant que son dernier accès n'est pas
  confirmé achevé par un vrai fence/timeline Vulkan.
- Lorsqu'une interpolation utilise les deux historiques, **les deux**
  slots et la sortie RGBA8 deviennent indisponibles jusqu'à la fin
  de la soumission correspondante.
- Un décrochage, une pause, un overlay ou une discontinuité annule
  l'historique logique, **mais pas les réservations GPU encore en vol**.
- Si le GPU est en retard, seule la génération synthétique est perdue :
  la présentation de la vraie frame reste prioritaire.
- Les soumissions GPU non liées à Mihawk peuvent faire progresser la timeline
  globale. Un compteur CPU de frames ne doit pas simuler une complétion.
- `Commit` n'est autorisé que lorsque l'appelant a réellement soumis
  la commande associée ; en cas d'`Abort`, le command buffer enregistré
  doit être abandonné, jamais soumis ultérieurement.

Test hôte : refus des slots in-flight, réamorçage, overlays, resets,
numéros invalides, sortie GPU occupée, sérialisation du cycle Prepare/Commit.

**Limite :** Encore doit encore exposer son vrai fence/timeline de scheduler
et appeler le protocole depuis le chemin `Composite`. Aucun système de
fence PS5 n'est artificiellement déclaré fonctionnel ici.

### C2.4 — protocole de raccordement au renderer (code hôte qualifié)

L'encodeur `mihawk_vulkan_encoder.cpp` regroupe les contrats R08 :
`MihawkSubmissionTimeline → ValidateOwnedSnapshot/ValidateNativeMihawkPair
→ RecordOwnedSnapshot → RecordNativeMihawkPair → Commit`.

Il valide **toutes** les préconditions avant le premier appel GPU, refuse une
deuxième préparation en attente, et réinitialise automatiquement les layouts
et références quand le groupe d'images change (y compris lorsqu'un handle
opaque Vulkan est réutilisé avec un nouveau numéro de génération d'allocation).

Le scheduler actif possède des API `Scheduler::CurrentTick()`,
`Scheduler::IsFree(tick)` et `Scheduler::Flush()` renvoyant la valeur de
soumission GPU. Le protocole autorise une réservation minimale avant
l'enregistrement, puis exige **le tick réellement renvoyé par Flush** pour
`Commit`; un tick inférieur à la réservation met les images en quarantaine,
jusqu'à `vkDeviceWaitIdle` + recréation. `PollCompleted` accepte seulement
une preuve `IsFree` appliquée aux ticks en vol, sans blocage de l'affichage.

Cette compatibilité d'interface **ne vaut pas intégration dans le jeu** :
l'appel direct depuis `RendererVulkan::Composite`, l'obtention non bloquante
des frames synthétiques du PresentManager, l'ordre réel d'affichage,
l'isolation du HUD et le budget GPU sont toujours à vérifier.

Les 7 unités de source C++ (4 MihawkGen + stage + allocation + encodeur)
compilent sur hôte avec un projet CMake dédié :
`cmake -S tools/graphics -B /tmp/eden-r08-host && cmake --build /tmp/eden-r08-host`.
`ctest --test-dir /tmp/eden-r08-host --output-on-failure` exécute **6 tests**
host-only. Le script `tools/graphics/check-r08-host.sh` ajoute les validations
de la licence/empreinte source, les 21 shaders SPIR-V et les sanitizers.
Ni ces objets macOS ni CTest ne constituent une compilation sur PS5.


### C4 — réglages par titre sans fausse activation

La fenêtre **Bibliothèque > Paramètres du jeu** possède désormais la même
ligne « Génération d'images : Désactivé » que Paramètres > Vidéo.
Croix / gauche / droite affichent une explication de non-disponibilité,
sans sauvegarder de configuration mensongère ni modifier les profils NS1/NS2.
La ligne désactivée ne dessine pas de flèches de sélection. Elle partage
une chaîne traduite avec les 29 catalogues et les textes embarqués FR.
Le contrôle check-r08-not-enabled.py protège la présence de cette garde
ainsi que l'absence de linkage production video_core/Mihawk.

### C4.1 — sélection persistante globale et par titre

Les préférences JSON incluent désormais le choix ordonné
off / mihawkgen / fsr3 / lsfg, avec une surcharge par jeu (-1 hérite du
global). Le launcher ne confond plus réglage demandé et cadence générée.
Avant chaque session, main.cpp résout ce choix et le renderer natif peut
le consulter via Display::frame_generation_method ; la valeur vaut
toujours Off en mode OpenGL ou lancement de sécurité. La sérialisation
reste rétrocompatible : les anciennes configurations héritent de Off.

Les sélecteurs de Paramètres > Vidéo et de Bibliothèque > Paramètres du
jeu conservent les méthodes dans le profil, mais avertissent qu'elles
ne sont pas encore effectivement disponibles dans le pipeline PS5.
Les préférences FSR sharpness et anti-aliasing restent désormais intactes
lors des modifications du menu.


### C2.5 — compilation de production unique, sans profil de release

Le moteur MihawkGen est désormais compilé dans un objet C++ de production
avec des pointeurs Vulkan distincts, placés dans l'espace de noms Volk.
Cela évite de confondre le vrai symbole vkGetInstanceProcAddr du RADV
d'Encore et la variable du chargeur Volk. La dépendance est ajoutée au
video_core natif sans option conditionnelle de build ou de release ;
elle ne modifie pas main ni le gitlink vendor.

La présence des objets compilés n'est toutefois **pas une preuve de
raccordement au RendererVulkan::Composite**. Le chemin effectif de
génération d'image reste à intégrer et à valider sur PS5. Les huit tests
CMake sur hôte passent et la compilation native Mac utilise les
symboles Volk isolés ; aucune compilation complète PS5 n'a été lancée.


### C2.6 — vrai renderer : captures privées et tick réel

`vulkan_renderer_r08.cpp` et son en-tête sont versionnés dans
Encore. Le CMake natif remplace la source originale du fork par cette unité,
sans modifier le gitlink `vendor` ni injecter des substitutions
textuelles au build. La session `mihawk_native_session.cpp`
utilise le même VkInstance/VkDevice qu'Encore ; le modèle réseau est copié
dans le packaging depuis le sous-module MihawkGen avec notices légales.

Quand MihawkGen est sélectionné, le composite de la vraie frame est copié
dans un snapshot GPU privé AVANT Scheduler::Flush. Le composite original
est toujours présenté. Les ticks réels Scheduler::Flush et IsFree protègent
la réutilisation des deux textures. Un tick nul ou non monotone interdit
toute capture suivante. Scheduler::Finish draine l'enregistrement différé
avant la libération des images à l'arrêt du renderer.

**Limite :** ce chemin ne crée pas encore de frame synthétique.
RecordNativeMihawkPair et la FIFO du PresentManager, le HUD invité,
la validation native PS5 et les performances console restent ouverts.
Choisir MihawkGen charge son contexte et amorce l'historique sans encore
doubler les frames affichées. FSR 3 et LSFG sont enregistrés comme
préférences, mais ne disposent pas d'un backend PS5 qualifié.

Le test `check-r08-renderer-wiring.py` vérifie
composite -> capture -> Flush -> présentation, ressources du packaging
et l'absence de faux compteur de frames synthétiques. Le ring de fences
dispose aussi de tests hôtes dédiés.


### C2.7 — frames synthétiques mises dans la FIFO du vrai renderer (lot courant)

Le Composite de l'émulateur crée désormais les vrais enregistrements GPU
d'une interpolation neurale avec RecordNativeMihawkPair, puis planifie
deux présentations dans cet ordre : **interpolée d'abord, vraie ensuite**.
Ces deux appels passent par le PresentManager du renderer natif existant,
et un unique état FrameMetrics distingue frames réelles et générées.
Les frames invitées ne sont pas réinjectées dans le VI ou le CPU du jeu.

La nouvelle méthode TryReserveRenderFrame vérifie la disponibilité de la
file et la clôture du fence, **sans attendre**. Aucun buffer synthétique
ne force le renderer à attendre un slot libre ; en cas de panne de modèle,
de retard GPU, de fréquence de sortie non vérifiée ou de HUD natif visible,
l'image réelle suit le pipeline habituel.

MihawkCaptureFences retient désormais les deux slots d'historique et
la texture RGBA8 de sortie jusqu'à la fin du tick qui a lu ou écrit ces
ressources. Les paires de frames source ne traversent pas un saut de
numéro, et les timestamps utilisés proviennent des vrais appels
Composite mesurés par steady_clock ; on ne prend pas le souhait de FPS
du guest pour une mesure de progression réelle.

**Périmètre de validation :** CMake 9/9 tests hôtes et contrôle de source
de la FIFO synthétique puis réelle, mais aucun résultat de rendu obtenu
sur PS5. Le backend doit encore être compilé avec le SDK PS5, exécuté
avec les shaders de MihawkGen et observé sur écran. Le HUD de l'application
est bloquant lorsqu'il est visible ; les scores, menus et glyphes *du jeu*
restent inclus dans la source et peuvent subir du ghosting. Le moteur
n'est donc pas certifié « 30→60 » ni validé pour une release.


### C2.8 — HUD natif séparé du contenu neural

Pour un titre utilisant MihawkGen, le composite du jeu est enregistré
sans le HUD natif d'Encore. Les copies d'historique et les passes
neuronales lisent donc l'image *sans* l'overlay natif. Une passe graphique
distincte DrawHudOverlay dessine ensuite le HUD sur l'image synthétique
puis sur l'image réelle, avant leur présentation.

La passe supplémentaire a son propre renderpass compatible avec le
framebuffer original, avec initialLayout GENERAL, finalLayout GENERAL
et loadOp LOAD, pour ne pas effacer le rendu du jeu ou la frame générée.
Les barrières après copie d'historique et conversion RGBA vers swapchain
préparent explicitement les accès COLOR_ATTACHMENT_READ/WRITE.
Un mode sans génération garde lui aussi le HUD natif visible ; aucun
masquage permanent du compteur de FPS n'est demandé.

C'est une séparation du HUD **de l'application**. L'interface dessinée
dans les pixels du jeu invité (score de football, menus, éléments 2D)
reste dans la texture source, sans moyen générique de l'isoler sans
métadonnées ou vecteurs de mouvement fournis par le jeu.

Les sources versionnées dans le dépôt sont :
vulkan_window_adapt_r08.cpp, vulkan_blit_screen_r08.cpp et leurs en-têtes.
La validation hôte passe à 10/10 tests CTest, avec un test des
transitions/bandes de synchronisation nécessaires au post-HUD.
La compilation complète et le rendu effectif sur PS5 restent à vérifier.


### C2.9 — renouvellement de session lors d'un changement de format

Le renderer détecte maintenant les transitions de résolution ou de
format de composition avec ChooseMihawkSessionAction. Le cas inchangé
n'a aucune attente GPU ; sur changement effectif, Scheduler::Finish
termine les commandes enregistrées, PresentManager::WaitPresent clôt
le précédent affichage et la session recrée ses images privées et son
contexte neural. Les captures et la cadence sont réinitialisées après
GPU idle, sans garder des handles Vulkan de l'ancienne résolution.

Cette régénération ne modifie pas le sous-module vendor et reste dans
le pipeline normal de l'application. Les surfaces invalides, dont une
dimension zéro ou supérieure à 3840x2160, ne déclenchent pas de
chargement du modèle. Le test hôte couvre le redimensionnement,
le basculement RGBA/BGRA, l'absence de changement et les formats
invalides. Aucun comportement console PS5 n'est revendiqué.


### C / FSR spatial et LSFG — audit de source

Le filtre AMD FSR existant est un **upscaler spatial FSR 1 (EASU/RCAS)** :
la méthode ScalingFilter::Fsr du launcher sélectionne les passes FSR de
Layer::ConfigureDraw dans le fork Vulkan versionné. BlitScreen effectue
ensuite un simple affichage bilinéaire de l'image déjà reconstituée. Ce
n'est **ni FSR 3 temporel ni FSR 3 Frame Generation** ; ces deux pipelines
n'ont toujours pas de vecteurs de mouvement/profondeur/jitter invités
fiables et leur sélection ne démarre aucun vrai backend FSR3.

Le code LSFG existant dans Eden comprend déjà un lecteur des ressources
shaders d'un fichier Lossless.dll, un traducteur SPIR-V, les passes
Alpha/Beta/Gamma/Delta et le pacer. Mais upstream ne les compile que
sur Android. Encore inclut désormais ces unités GPL dans video_core
pour PS5, avec HAS_LSFG activé sur la cible et synchronisation du choix
global/par jeu avec Settings::values.frame_gen au lancement.

Le fichier personnel de l'utilisateur est recherché via le répertoire
EdenPath::LosslessDir à
/data/prosperoeden/user/lossless/Lossless.dll
(sandbox du jeu : dossier utilisateur équivalent). **Aucune DLL n'est
incorporée aux livrables, exécutée ou téléchargée** ; seules ses données
shaders sont lues. Le lecteur natif refuse les liens symboliques, les
fichiers non réguliers et une taille nulle ou supérieure à 256 Mio.
Sans fichier valide, LsfgShaders refuse l'activation et la présentation
du jeu reste normale.

Le HUD natif est recomposé après interpolation sur les sorties MihawkGen
et LSFG. Ce raccordement LSFG est **en source et contrôlé statiquement** ;
aucune compilation complète PS5, validation des pipelines par le pilote
PS5, latence ou affichage 30->60 sur console n'est encore démontré.
