# NS2 / PS5 — catalogue de compatibilité mémoire, shaders et stratégie de validation (2026-11-17)

> État : recherche upstream + correctif instrumental candidat sur branche dédiée. Aucun démarrage NS2, rendu, performance ni succès de compilation PS5 n'est revendiqué par ce document. Les résultats d'autres forks ne constituent pas une preuve pour Encore.

## 1. Invariants à qualifier, sans table d'adresses codées en dur

- **Identité du contenu** : une génération NS2 détectée doit correspondre au NPDM, au NSO/ExeFS réellement exécuté, à la RomFS effective après mises à jour et aux DLC montés. Version du titre et build ID du programme sont distincts du seul Title ID.
- **Mémoire CPU invitée** : conserver séparés l'adresse virtuelle invitée, la page-table/état de mapping, l'engagement physique PS5 et la durée de vie de la réservation. Un `PC=0x4` final n'identifie pas la première faute. Garder le dimensionnement dynamique via NPDM/resource limit, heap et alias region ; ne pas recopier des adresses absolues observées sur un autre jeu ou fork.
- **Mémoire GPU** : les adresses GPU virtuelles passent par les GMMU mappings (dont granularité 4 KiB côté invité), les propriétaires de canal/FD et la traduction vers le backing PS5. Ne pas assimiler GPU VA, guest CPU VA, adresse hôte et adresse de shader.
- **Shader** : identité par code/étape/contexte invité, compilateur/lowering, format de cache, pilote RADV, appareil et paramètres de rendu. Les programmes NS2 Ampere, QMD/compute, task/mesh, textures et descripteurs ne se résument pas à un tableau de PC ou GPU VA. Les données d'un autre driver ne forment pas un pipeline Vulkan PS5 réutilisable tel quel.
- **Textures** : les bases et dimensions proviennent des descripteurs/surfaces et du contexte GMMU à l'exécution. L'index de compatibilité peut répertorier les formats/opcodes et limitations ; la cohérence CPU-write → invalidation → upload/descriptor est une propriété générique du moteur.
- **Sécurité et origine** : n'enregistrer ni clés, ni données jeu, ni code de shader extrait protégé dans ce dépôt ; le catalogue contient seulement versions, empreintes dérivées, capacités et preuves de tests.

## 2. Références upstream prioritaires

| Projet / preuve | Ce que nous pouvons étudier | Limite / précaution |
|---|---|---|
| [Lichii — builder shader warm](https://github.com/zortos293/Lichii/blob/main/src/video_core/shader_warm/shader_warm_builder.h), [pipeline precache](https://github.com/zortos293/Lichii/blob/main/src/video_core/renderer_vulkan/vk_pipeline_cache.cpp), [tests](https://github.com/zortos293/Lichii/blob/main/src/tests/video_core/shader_precache.cpp) | Découverte de programmes compute dans les fichiers du titre, cache `warm-compute.bin`, marqueur de version incluant contenu, device, driver, version de cache et hash du générateur SPIR-V, annulation et budget de workers | Précompiler les compute accessibles ne prédit pas toutes les combinaisons de pipelines graphiques d'une zone encore inconnue ; l'intégration au port PS5 n'est pas acquise |
| [Lichii — issue #601](https://github.com/zortos293/Lichii/issues/601), [#899](https://github.com/zortos293/Lichii/issues/899) | Distinction entre précache des shaders découverts, compilation graphique après apparition et limite de cache | Examiner les versions et commits fusionnés ; ne pas importer les PR #579/#741 fermées comme si elles étaient shipping |
| [Eglantine — #335](https://github.com/Eglantine-Community/Eglantine/issues/335), [#350](https://github.com/Eglantine-Community/Eglantine/issues/350), [#504](https://github.com/Eglantine-Community/Eglantine/issues/504) | ExeFS/NPDM/RomFS d'une mise à jour, premier unmapped write avant PC=4 | Certains crashs persistent après correction RomFS ; trace précoce nécessaire |
| [viejunerd/Eglantine-PS5- README](https://github.com/viejunerd/Eglantine-PS5-), [mémoire/CPU](https://github.com/viejunerd/Eglantine-PS5-/blob/main/docs/MEMORY-CPU-EXPERIMENTS.md) | Mesures console PS5 13.60, allocation GPU par lots, correction race unmap/reserve, batching ASTC, task/mesh via compute | Pas de gain confirmé via swap SSD ou mimalloc ; game runs ne garantissent pas stabilité d'Encore |
| [heydemoura/EglantinePS5](https://github.com/heydemoura/EglantinePS5), [budget MKW](https://github.com/heydemoura/EglantinePS5/blob/main/docs/MKW-MEMORY-BUDGET.md) | Cache driver sur PS5, mémoire invitée/driver/heap, compression du backing froid, stutters et pression VRAM | Compter une seule fois les allocations du driver ; mesurer selon la version de Mesa utilisée par Encore |
| [Portablelle/EdGlantine-PS5](https://github.com/Portablelle/EdGlantine-PS5) | Revue des séparations surface/texture, DMA/query, cohérence mémoire et ASTC ; cas visuels de shaders absents | Comparer les implémentations et ABI avec nos sources sélectionnées avant backport |
| [mihawk-99/PS5_Lichii](https://github.com/mihawk-99/PS5_Lichii), [PS5_Vulkan](https://github.com/mihawk-99/PS5_Vulkan) | Variante Fritchii native et comportement RADV/cache pilote PS5 | Différences de matériel/driver/snapshots ; ne jamais copier un cache driver brut |
| [Lichii mesh compute](https://github.com/zortos293/Lichii/pull/569), [Lichii #1801](https://github.com/zortos293/Lichii/issues/1801) | Compatibilité mesh/task sur RADV RDNA2, fallback compute et cas de blocage GPU | Exige tests de fonctionnalités réelles du pilote et sortie des shaders ; un simple feature flag n'est pas une validation |

## 3. Compatibilité de référence (observations **des autres ports**, non Encore)

| Jeu | Identité connue dans les logs Encore | Preuves externes à croiser | Ce que la couverture moteur doit garantir |
|---|---|---|---|
| Mario Kart World | `0400C3F00006E000` | Port PS5 viejunerd : courses atteintes, pression mémoire importante (environ 5.4–5.9 Go de mémoire invitée suivant session), allocations terrain groupées ; persistance des OOM | Admission NPDM/ExeFS/RomFS, GMMU/GPU submit, budget driver/guest/JIT, texture/ASTC, task/mesh, sortie sans corruption |
| Donkey Kong Bananza | `040074A01BF12000` | Eglantine #335/#350 : sélection de la RomFS d'update et PC=4 ; PS5 viejunerd : gameplay documenté | Premier défaut mémoire/IPC, cohérence update, sparse commit, shader/compute, update DLC, compositing |
| Ocarina of Time (NS2) | Title ID/build ID non confirmé ici | PS5 viejunerd : shader task/mesh fallback compute et gros buffers storage ; mémoire invitée observée ~4.7 Go sur expérimentation | Interdire les requêtes storage absurdes dues à des tailles mal lues ; budget GPU, lowering Ampere et matériel |
| Nouveau jeu NS2 | Détection par NPDM + programme réellement chargé | Pas de succès présumé | Validation automatique des contrats génériques ; profil de compatibilité ajouté seulement sur observation fiable |

Les adresses absolues de shader, texture, pile ou GMMU ne peuvent pas être présaisies en sûreté pour les futures versions des jeux ; elles se découvrent à partir du programme et de l'état réellement chargé.

## 4. Source graph Encore et observabilité

- Moteur : `headless/CMakeLists.txt` sélectionne `vendor/encore-active/ns2-runtime/process/core/hle/kernel/k_process.cpp` dans la cible `core`, puis active `EDEN_NS2_PROCESS_RUN_GUARD=1`.
- Vendor : ce KProcess contient `EDEN_MAIN_STACK_MAP` immédiatement après `MapPages()` et `EDEN_MAIN_THREAD_CONTEXT` après initialisation du thread, tous deux sous `#if defined(PS5_NATIVE)`.
- Correctif du 17 novembre : définition `PS5_NATIVE=1` **sur cette unité uniquement** (sans macro globale ABI) et contrôle d'inventaire pour empêcher la disparition silencieuse des témoins.
- Tracer la séquence `content/NPDM/NSO` → `KProcess::Run/MapPages` → `SVC` → `NVDRV/GPFIFO` → `GPU submit` → `frame present` en une seule session. Séparer les propriétaires des événements et limiter les échantillons.
- Pour FC27 NS1, analyser indépendamment cache shader froid/chaud, `OnCPUWrite`, chevauchements buffer/texture, commandes OPTIONS, invalidations, rebind descripteurs et `present` ; aucune hypothèse de cause unique du HUD.

## 5. Format du futur catalogue alimenté automatiquement

Une entrée se clé sur `{title_id, build_id, update_version, content_hash, source_ref}`, et contient :

- `program_generation`, `npdm_identity`, `exefs_romfs_coherent`, `loader_status` ;
- `guest_virtual_regions` (plages **mesurées** et états, pas prescriptions), `resident_guest_bytes`, `ps5_host_backing_bytes`, `driver_allocated_bytes`, `peak_largest_free_block` ;
- `gpu_va_mapping_status`, `gpfifo_route`, `submit_count`, `completed_count` ;
- `shader_stage_fingerprint`, `shader_ir_emission_stamp`, `cache_version`, `radv_driver_version`, `device_id`, `warm_compute_count`, `graphics_pipeline_count`, `compile_failures` ;
- `texture_formats_seen`, `astc_residency`, `sparse_tile_failures`, `storage_descriptor_failures` ;
- `upstream_commit`, `engine_sha`, `vendor_sha`, `host_test_results`, `native_build_sha`, `console_result` et `status`.

**Aucune adresse ou valeur mesurée n'est inventée** : `unknown` reste `unknown`. Réutiliser le même schéma pour le premier jeu d'une nouvelle famille shader/mémoire ; les jeux suivants héritent des tests des **fonctions** communes, pas d'un prétendu statut « playable ».

## 6. Portes de validation — minimiser les tests matériels

1. **Sans PS5** : source graph et macros dans les TUs réels, ABI 6 cœurs, scripts de diagnostic, tests hôtes NPDM/NSO, mapping 4KiB/alias/sparse, cohérence ExeFS/RomFS, QMD, shader stage emit/SPIR-V `spirv-val`, texture invalidate, cache version/hash/driver et worker-budgets ; Clang/GCC/ASan/UBSan selon disponibilité.
2. **Build unique une fois les lots stabilisés** : versions moteur + vendor épinglées, compile_commands prouvant les macros, compilation/link native, warnings, symboles non strippés, artefact et package validés. CI verte ≠ gameplay.
3. **Trois scénarios console maximum pour cette campagne** : FC27 NS1 (entrée en match à froid puis retour/relance à chaud, changement HUD, OPTIONS, sortie), MKW NS2 (lancement puis course courte), Bananza NS2 (lancement puis première scène et sortie). Les deux jeux NS2 couvrent des chemins différents, sans tester toute la ludothèque.
4. **Escalade conditionnelle** : s'il manque encore une preuve décisive (par exemple `gpu_submit=0`), garder l'anomalie P0 ouverte et n'ajouter qu'un test causal après correction ciblée, pas 100 tests de jeux.

## 7. Statut au 17 novembre

- **Confirmé par lecture des sources** : défaut de définition PS5_NATIVE sur l'unité KProcess du graphe natif ; patch source écrit sur branche moteur.
- **Sources externes examinées** : portages PS5 et Lichii, avec mécanisme de warm-compute et exemples memory/ASTC/task-mesh.
- **En attente** : qualification complète du patch via CI/source et native compile ; comparaison détaillée par fonctions avec les chemins Encore shader warm et texture GPU ; intégration d'un builder de precache adapté à la mémoire/driver PS5.
- **Non effectué** : build PS5, test de jeu console, adoption de caches ou adresses issus d'autres forks, prétention de boot NS2 résolu.
