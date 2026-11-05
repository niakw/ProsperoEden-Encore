# Eden Encore — migration des sélecteurs de recherche NS2 vers un moteur commun

**Inventaire revu le 04/11/2026**, dérivé de `headless/CMakeLists.txt`. Voir la [roadmap vivante #15](https://github.com/niakw/ProsperoEden-Encore/issues/15) (P0.2). **Les 9 commutateurs encore utiles à la recherche sont OFF par défaut ; N1, N3b, N49, N50, N51, N52, N54, N56, N57, N60 et N76 sont désormais sélectionnés automatiquement par leur propriétaire commun.** Leur existence ne prouve pas que les fonctionnalités NS2 soient intégrées au produit distribué.

| Domaine et destination de production | Flags `EDEN_NS2_…_EXPERIMENTAL` à résorber | Critère de promotion/suppression |
| --- | --- | --- |
| Boot, CPU, architecture et fréquence | `EDEN_NS2_EXEFS_EXPERIMENTAL`, `EDEN_NS2_A64_EXPERIMENTAL`, `EDEN_NS2_CPU6_EXPERIMENTAL` | Une sélection automatique vérifiée par NPDM/HOS/CPU, progression invitée réelle, 6 cœurs NS2 et absence de régression NS1 |
| Services HOS, IPC et GPU session | `EDEN_NS2_NVDRV_EXPERIMENTAL`, `EDEN_NS2_GPU_SESSION_EXPERIMENTAL`, `EDEN_NS2_GRAPHICS_SUPERVISOR_EXPERIMENTAL` | Implémentation commune des protocoles + adaptateurs de commandes spécifiques, replies/handles/fences exacts; aucun retour factice de succès |
| Adressage / résidence / scheduler | `EDEN_NS2_SPARSE_CACHE_PROBE_EXPERIMENTAL` | Adresses natives contrôlées, réservation physique et remise à zéro atomique, un scheduler Vulkan, rollback fiable, budgets et limites de périphérique |
| Shader / GPU | `EDEN_NS2_AMPERE_PROBE_EXPERIMENTAL`, `EDEN_NS2_VULKAN_SHADER_BRIDGE_EXPERIMENTAL` | Une API shader/pipeline canonique, Maxwell/Ampere décodés par leur frontend matériel, vertex/fragment/compute validés, pas de pipeline de « probe » dans le produit |
| Cache texture, ASTC, images | **N54 promu : scratch CPU borné partagé** | Deux buffers temporaires CPU >64 MiB relâchés au TickFrame sans affecter les ressources GPU et la mémoire NS1 habituelle ; N57/N60 communs |
| Boot / identité invitée | **N1 promu : NPDM 2048/3072 bits sélectionné automatiquement sur PS5** | Un seul parseur source/ABI ; le contenu du NPDM détermine NS1 ou NS2, sans activer le GPU/HOS expérimental ni modifier la sélection NS1 |
| ASTC / Vulkan partagé | **N57 promu : vues de layers et Compute ASTC ; N60 promu : uploads incrémentiels sécurisés** | ABI `ImageBase` unique pour `core`/`video_core`, admissibilité selon format/tailles/flags, fallback image complète, staging retenu jusqu'à `runtime.Finish()` ; qualification GPU PS5 P5 |
| Services AM | **N3b promu : commande 320 authentique** | Lit les permissions capture/recording existantes sous verrou ; intégration automatique au service natif PS5 partagé, GPU supervisor reste recherche ; échelle graphique factice retirée |
| Processus HOS | **N52 promu : `KProcess::Run` NS2 ne revendique plus de démarrage après un échec** | Sélection exclusivement sur le PID effectivement inscrit par l'ExeFS partagé ; chemin NS1 historique inchangé |
| Mapping GPU | **N51 promu : notifications PTE regroupées** | Coalescence des pages adjacentes réellement changées sous le propriétaire commun, remap physique P1.2 conservé, aucun changement d'adresse client et refus des débordements |
| Mapping GPU | **N50 promu : coupure des runs physiques obsolètes lors de Map/Unmap, NS1/NS2** | Un seul propriétaire mémoire PS5, sous le même verrou ; aucun parcours de pages de commandes parallèle |
| Image views Vulkan | **N49 promu : garde de dimensions 2D/3D commune NS1/NS2** | Empêche les vues 3D incompatibles du cache Vulkan PS5, sans option expérimentale |
| Cache Vulkan | **N56 promu : garde commune PS5/Vulkan** | Une implémentation cache driver robuste et versionnée, pas de changement de schéma pendant le jeu, invalidations et durées de vie contrôlées |

**Décision d'épuration du 04/11 :** 9 options conservées parce qu'elles
sélectionnent effectivement des propriétaires de code différents dans
le mode de recherche. Huit sont des prérequis techniques actifs du futur
runtime NS2 : ExeFS/SVC, A64, CPU6, NVDRV, GPU session, supervisor,
Ampere et Vulkan/SPIR-V. La dernière option, N73, active aussi N72 : deux bancs
de validation réels pour le scheduler sparse et le cache image sparse
sur Vulkan ; elles ne sont **pas** appelées automatiquement pendant le rendu
et ne doivent pas être présentées comme un support GPU opérationnel.
Ces neuf options sont nécessaires **à la recherche**, pas aux livrables NS1.

**P0.2b — compilateur SPIR-V NS2 admis dans la source
PS5 finale (05/11, sans activation GPU) :**
le même profil PS5 final qui inclut le décodeur
Ampere sélectionne désormais les quatre vrais
propriétaires de compilation SPIR-V NS2 :
deux unités natives de shader/Compute QMD3,
plus deux remplacements complets de fonctions
SPIR-V pour l'indirection CBUF et les bornes
des accès mémoire. Les deux compilateurs
desktop et PS5 restent dans un seul moteur.

Le point de compatibilité critique est
l'émission des CBUF indirects Maxwell. La
branche sans NativeSpirvCbufBoundsScope
reproduit maintenant mot pour mot le vrai
sélecteur de 14 banques du propriétaire Eden
épinglé, même si son masque de métadonnées
est partiel. La branche NS2 n'est choisie
que depuis un scope thread-local authentifié,
avec les 8 banques QMD3 réelles et leurs
limites, et sans injecter d'en-tête BufferCache
modifiant l'ABI NS1.

**Preuves :** configuration CMake réelle
de deux projets hôte éphémères, source release
(4 unités remplacées/sélectionnées, aucun
macro GPU de recherche) et source desktop
inchangée ; quatre compilations syntaxiques
Clang C++20 de vrais TUs, parité du corps
Maxwell original, gardes de source et
régressions CBUF. Aucune compilation PS5
ou liaison finale n'est prétendue.
**L'exécution GPU native reste verrouillée**
sur NVDRV 4 KiB, GPFIFO, GPU Session et
RasterizerVulkan::DispatchNativeCompute.
Les neuf options expérimentales restent OFF.

**P0.2/P2.3 — clarification 32 SSBO Compute (05/11) :**
le rendu Compute natif a déjà son propriétaire QMD3
qui reflète et valide jusqu'à 32 enregistrements,
puis appelle StageVulkanBufferBindings et
BufferCache::ObtainBuffer pour chaque ressource
sans passer par l'état Kepler historique
BufferCacheChannelInfo::compute_storage_buffers[16].
Le test du vrai IR/plan/CBUF propriétaire couvre
les 32 slots (y compris le slot 31), refus des
33 slots, dernière page GMMU absente et rollback
à la dernière liaison, sous Clang/GCC UBSan O0/O2.
**Il n'est pas justifié de remplacer l'en-tête
BufferCache NS1 ni de modifier ses signatures
pour faire fonctionner cette voie Compute.**
Le support des 32 SSBO dans le rendu graphique
Ampere et le GPU physique reste distinct,
non validé et toujours en P2.4/P5.

**P0.2 — promotion partielle du coeur ISA Ampere (05/11) :**
le profil PS5 final avec NPDM commun et Vulkan compile désormais les
huit vraies unités de capture/traduction Ampere (frontend, GMMU,
Maxwell lowering, cache de traduction, environnement et pont IR)
**sans activer la session GPU NS2 ni le pont de rendu**.
Le mode recherche explicite continue d'utiliser la même sélection
source, et ses neuf options restent toutes OFF par défaut.

La migration sépare surtout les deux variantes de l'overlay
shader_resource : le classificateur IR Generic31Y/Z/W est un
correctif générique sans changement de layout, copié dans
l'arbre d'en-têtes commun ; en revanche l'en-tête
buffer_cache_base.h de recherche change NUM_STORAGE_BUFFERS
de 16 à 32 **et** des signatures C++ de méthodes. Ce dernier
n'est **pas** sélectionné dans le profil commun, faute de
migration de son implémentation et preuve d'ABI NS1.
Le garde hôte exécute le vrai sélecteur CMake dans cinq profils,
compile les huit unités de traduction avec les en-têtes Eden
d'origine et vérifie l'absence d'injection du cache expérimental.

Ce jalon rend le coeur Ampere **compilable** depuis le produit
commun, mais ne revendique ni son activation au dispatch,
ni la prise en charge des 32 SSBO par le cache commun,
ni les premières images PS5. Le sélecteur
EDEN_NS2_AMPERE_PROBE_EXPERIMENTAL reste utile pour
tester le chemin complet de recherche et ne peut pas être
supprimé avant la migration du GPU. Le blocage P0.2
GPU/session/CPU6 et la validation P5 restent ouverts.

**Une option et quatre sources supprimées :** l'ancien proxy AM Graphics
Scale rendait une réponse synthétique échelle 10, ratio 1/1, sans état
écran réel ni événement. Le supprimer, ainsi que sa sélection native et
son test de compilation, évite de livrer un comportement trompeur. Le
proxy Eden original et la commande 320 partagée restent seuls sélectionnés.
Le contrôle source vérifie désormais que tout opt-in conservé possède un
propriétaire d'implémentation réel et n'est pas un interrupteur mort.

**État du 04/11 :** 22 commutateurs initiaux recensés ; **9 restent OFF par défaut ; un prototype inutile a été supprimé et deux options sparse fusionnées** ; **N1 (NPDM 2048/3072), N3b (AM320), N49 (vues), N50 (continuité), N51 (notifications PTE), N52 (HOS), N54 (scratch CPU), N56 (cache Vulkan), N57 (décodage ASTC), N60 (cache/layers ASTC) et N76 (horloge NPDM) sont promus sans flag de recherche**. Le coeur compilable d'Ampere est désormais promu en source,
mais aucun des 9 chemins de recherche complets n'est activé
en production. Certains comportements ont déjà des propriétaires partagés `EDEN_SHARED_NS2_*` — cela ne suffit pas à certifier les chemins verrouillés ici.

## Règles de migration

1. **Conserver une seule responsabilité maintenue** pour JIT, buffers, cache texture, shaders, renderer, services et UI; n'admettre des adaptations qu'aux frontières matérielles (ISA/QMD, formats/ABI/services). Pas de fork parallèle du moteur.
2. Remplacer chaque flag de recherche **après validation** par sélection automatique selon le programme invité/la capacité matérielle, ou supprimer le code devenu redondant. Ne pas remplacer un mode OFF par un « succès » artificiel.
3. Faire passer les tests hôte négatifs, la parité source, la CI commune et la non-régression NS1 **sur le même couple SHA main/vendor** avant P5. **Aucun build PS5 ni test console en P0–P4** : la qualification matérielle s'effectuera exclusivement en P5 après autorisation explicite.
4. L'inventaire est contrôlé par `tools/check-ns2-production-flags-host.py`. L'ajout, le renommage ou le retrait d'un flag doit mettre ce document et les tests à jour dans le même commit.
5. Les workflows de build PS5 restent verrouillés **pendant tout P4**. Leur premier déverrouillage et la validation console appartiennent à **P5 uniquement**, après clôture des prérequis hôte et autorisation explicite.

Ce document est un **inventaire des travaux restants**, pas une garantie de fonctionnement des 9 chemins de recherche encore désactivés.
