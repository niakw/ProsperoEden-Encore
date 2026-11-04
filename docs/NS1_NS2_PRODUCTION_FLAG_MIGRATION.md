# Eden Encore — migration des sélecteurs de recherche NS2 vers un moteur commun

**Inventaire effectif du 02/11/2026**, dérivé de `headless/CMakeLists.txt`. Voir la [roadmap vivante #15](https://github.com/niakw/ProsperoEden-Encore/issues/15) (P0.2). **Les 17 commutateurs restants sont OFF par défaut ; N49, N50, N52, N56 et N76 sont désormais sélectionnés automatiquement par leur propriétaire commun.** Leur existence ne prouve pas que les fonctionnalités NS2 soient intégrées au produit distribué.

| Domaine et destination de production | Flags `EDEN_NS2_…_EXPERIMENTAL` à résorber | Critère de promotion/suppression |
| --- | --- | --- |
| Boot, CPU, architecture et fréquence | `EDEN_NS2_METADATA_EXPERIMENTAL`, `EDEN_NS2_EXEFS_EXPERIMENTAL`, `EDEN_NS2_A64_EXPERIMENTAL`, `EDEN_NS2_CPU6_EXPERIMENTAL` | Une sélection automatique vérifiée par NPDM/HOS/CPU, progression invitée réelle, 6 cœurs NS2 et absence de régression NS1 |
| Services HOS, IPC et GPU session | `EDEN_NS2_AM_EXPERIMENTAL`, `EDEN_NS2_GRAPHICS_SCALE_EXPERIMENTAL`, `EDEN_NS2_NVDRV_EXPERIMENTAL`, `EDEN_NS2_GPU_SESSION_EXPERIMENTAL`, `EDEN_NS2_GRAPHICS_SUPERVISOR_EXPERIMENTAL` | Implémentation commune des protocoles + adaptateurs de commandes spécifiques, replies/handles/fences exacts; aucun retour factice de succès |
| Adressage / résidence / scheduler | `EDEN_NS2_GPU_RANGE_BATCH_EXPERIMENTAL`, `EDEN_NS2_SPARSE_QUEUE_EXPERIMENTAL`, `EDEN_NS2_SPARSE_CACHE_PROBE_EXPERIMENTAL` | Adresses natives contrôlées, réservation physique et remise à zéro atomique, un scheduler Vulkan, rollback fiable, budgets et limites de périphérique |
| Shader / GPU | `EDEN_NS2_AMPERE_PROBE_EXPERIMENTAL`, `EDEN_NS2_VULKAN_SHADER_BRIDGE_EXPERIMENTAL` | Une API shader/pipeline canonique, Maxwell/Ampere décodés par leur frontend matériel, vertex/fragment/compute validés, pas de pipeline de « probe » dans le produit |
| Cache texture, ASTC, images | `EDEN_NS2_ASTC_SCRATCH_RELEASE_EXPERIMENTAL`, `EDEN_NS2_ASTC_LAYER_DECODE_EXPERIMENTAL`, `EDEN_NS2_ASTC_TEXTURE_CACHE_BRIDGE_EXPERIMENTAL` | Texture/cache unique, formats ASTC, vues 3D/layers, GOB, synchronisation et contrôles de bornes testés sur NS1 et NS2 |
| Processus HOS | **N52 promu : `KProcess::Run` NS2 ne revendique plus de démarrage après un échec** | Sélection exclusivement sur le PID effectivement inscrit par l'ExeFS partagé ; chemin NS1 historique inchangé |
| Mapping GPU | **N50 promu : coupure des runs physiques obsolètes lors de Map/Unmap, NS1/NS2** | Un seul propriétaire mémoire PS5, sous le même verrou ; aucun parcours de pages de commandes parallèle |
| Image views Vulkan | **N49 promu : garde de dimensions 2D/3D commune NS1/NS2** | Empêche les vues 3D incompatibles du cache Vulkan PS5, sans option expérimentale |
| Cache Vulkan | **N56 promu : garde commune PS5/Vulkan** | Une implémentation cache driver robuste et versionnée, pas de changement de schéma pendant le jeu, invalidations et durées de vie contrôlées |

**État du 04/11 :** 22 commutateurs initiaux recensés ; **17 restent OFF par défaut** ; **N49 (vues), N50 (continuité mémoire), N52 (admission HOS), N56 (cache Vulkan) et N76 (horloge NPDM) sont promus sans flag de recherche**. Aucun des 17 autres n'est promu. Certains comportements ont déjà des propriétaires partagés `EDEN_SHARED_NS2_*` — cela ne suffit pas à certifier les chemins verrouillés ici.

## Règles de migration

1. **Conserver une seule responsabilité maintenue** pour JIT, buffers, cache texture, shaders, renderer, services et UI; n'admettre des adaptations qu'aux frontières matérielles (ISA/QMD, formats/ABI/services). Pas de fork parallèle du moteur.
2. Remplacer chaque flag de recherche **après validation** par sélection automatique selon le programme invité/la capacité matérielle, ou supprimer le code devenu redondant. Ne pas remplacer un mode OFF par un « succès » artificiel.
3. Faire passer les tests hôte négatifs, la parité source, la CI commune et la non-régression NS1 **sur le même couple SHA main/vendor** avant P5. **Aucun build PS5 ni test console en P0–P4** : la qualification matérielle s'effectuera exclusivement en P5 après autorisation explicite.
4. L'inventaire est contrôlé par `tools/check-ns2-production-flags-host.py`. L'ajout, le renommage ou le retrait d'un flag doit mettre ce document et les tests à jour dans le même commit.
5. Les workflows de build PS5 restent verrouillés **pendant tout P4**. Leur premier déverrouillage et la validation console appartiennent à **P5 uniquement**, après clôture des prérequis hôte et autorisation explicite.

Ce document est un **inventaire des travaux restants**, pas une garantie de fonctionnement des 17 chemins de recherche encore désactivés.
