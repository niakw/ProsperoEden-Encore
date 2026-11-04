# Eden Encore — P4.2b : témoins négatifs source/hôte du 4 novembre 2026

**Couple examiné :** main `bc68ad2` avant ajout du seul en-tête manquant d'un témoin hôte, vendor `1a6caf4e2f64012aaae07a2aa26790f1040ac5be`. Les tests décrits ci-dessous ne déclenchent ni CI GitHub ni compilation PS5. Mac ARM, SDK hôte CLT 15.4 pour les exécutables. Les sources natives PS5 demeurent inchangées.

| Contrat négatif vérifié | Test exécuté et résultat observé |
| --- | --- |
| GMMU bornes 40/49 bits et lecture commande invalide | `tools/ns2/check_native_gpu_memory_walker_bounds_host.py` : O0/O2, ASan/UBSan ; invalid_ranges=6, read_zero=2, cached_write_guard=4 (déjà revérifié dans la séquence précédente) |
| Backing physique image après remap | `tools/ns2/check_native_image_physical_backing_host.py` : Clang/GCC O0/O2, tous les mapping pages, deux propriétaires |
| OOM des pages GPU et rollback sans état partiellement publié | `tools/ns2/check_native_dense_ledger_oom_host.py` : Clang/GCC O0/O2, precommit OOM refusé ; `tools/ns2/check_gpu_worker_registered_handles_oom_host.py` : quatre configurations, 4 096 handles préalloués, aucune allocation nouvelle post-NVMap |
| VI2, NVMap, minuterie et queue sous OOM | `tools/ns2/check_native_vi2_oom_host.py` : Clang/GCC O0/O2, leases 2 échecs et ledger rollback ; `tools/ns2/check_native_vi2_vsync_oom_host.py` : Clang/GCC O0/O2, les deux réservations, création timer, planification/réessai et 32 événements |
| Fences et publication mémoire | `tools/check-native-gpu-fence-release-publication-host.py` : 32 768 commandes par mode ; publication release/acquire |
| Scheduler : record refusé / flush refusé | `tools/check-ps5-f07-scheduler-record-rollback-host.py` : retour refusé, dispatch/record exception, invalidation mémo, retry, ancien chemin desktop, O0/O2 UBSan ; **témoin réparé en ajoutant `<initializer_list>` à son seul C++ embarqué**. `tools/check-ps5-f07-async-flush-staging-rollback-host.py` : natif/desktop O0/O2 |
| Descripteurs, upload images et texture en cas d'échec | `tools/check-ps5-f07-graphics-descriptor-record-rollback-host.py`, `tools/check-ps5-f07-texture-upload-rollback-host.py`, `tools/check-ps5-f07-image-upload-record-rollback-host.py` : refus sans cache/publication, staging court/nul, O0/O2 |
| DMA, lecture GPU et GC | `tools/check-ps5-f07-async-dma-rollback-host.py`, `tools/check-ps5-f07-readback-dirty-rollback-host.py`, `tools/check-ps5-f07-gc-dirty-eviction-rollback-host.py` : sources natives/desktop O0/O2, refus et nouvelles tentatives sûrs |
| Rapport d'erreur GPU VMA | `tools/check-ps5-vulkan-oom-source.py` : preuve source de diagnostic OOM heap/image avant exception |

**Décision :** P4.2b peut être clos pour ces témoins négatifs hôte uniquement, sans attendre un GPU ou une console. Le jalon P4.2 reste ouvert pour le lot de régression NS1 complet au même SHA final ; P4.1/P4.3 conservent la qualification globale de source/interfaces. Les OOM physiques, l'arbitrage réel des files Vulkan, les crashs MKW/Bananza et le premier framebuffer restent exclusivement P5. Ne pas inférer une stabilité PS5 des exécutables simulés.
