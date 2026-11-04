# Eden Encore — réconciliation réelle des propriétaires source, 4 novembre 2026

Contrôle local du projet et du vendor versionnés, sans CI ni build PS5. Les anciens blobs historiques ont été récupérés depuis l'API GitHub pour les trois objets absents du cache Git local ; chaque différence a été comparée au fichier de production. Le présent journal atteste une revue source et les tests hôte indiqués, **pas** un résultat console.

## Inventaire expérimental P0.2 et mémoire commune P1.2

Quatre anciens fichiers du prototype AM Graphics Scale ont été supprimés du vendor avant cette revue : application_proxy.cpp/h et graphics_scaling_parameters_functions.cpp/h sous ns2-runtime/am. Ils donnaient une réponse d'échelle factice et ne sont plus des sources actuelles. L'inventaire de 121 anciennes entrées est recomposé sans elles, avec trois véritables sources Ampere/BRX, CBUF 49 bits et bornes NVDRV, soit **120 propriétaires recherche encore existants**. L'ajout récent de eden-core/src/video_core/native_gpu_page_remap.h est répertorié séparément comme correctif de mémoire GPU partagée P1.2 (Mapped vers Mapped, backing physique changé). Aucun de ces quatre propriétaires nouvellement recensés n'est une prétendue source F07 historique.

Contrôles : check-active-source-inventory.py, check-eden-optimization-coverage.py et check_retired_am_graphics_scale.py imposent l'absence des 4 sources retirées, la présence des 4 sources nouvelles et les empreintes de l'inventaire ; les **337 sources historiques** et **518 propriétaires F07** restent inchangés.

## Écarts de blobs effectivement relus

| Fichier | Ancien blob | Blob courant | Delta réel et garde |
| --- | --- | --- | --- |
| headless/gpu_deferred_write_queue.h | 5abb7fa8 | bf831798 | Recyclage de la capacité FIFO seulement quand aucune queue plus récente n'existe ; check-gpu-deferred-queue-host.py (4 producteurs, 1280 plages) |
| headless/metadata_bridge.cpp | dfc42553 | 539ff998 | Tri des imports ZIP avant l'admission bornée ; check-firmware-auto-import-host.py, check-firmware-matrix-host.py |
| headless/prosperoeden/pe/ui/case_media_selection.hpp | 59f1f95c | 1e97d6e9 | Scènes indexées prioritaires et repli dédupliqué en un passage ; check-encore-case-media-selection-host.py |
| headless/prosperoeden/pe/ui/switch_theme.cpp | f852926a | 996adb5c | État « bibliothèque en chargement » plutôt que zéro ROM prématuré ; check-switch-theme-layout.py et check-launcher-atomic-scan-host.py |
| vendor/encore-active/eden-core/src/core/hle/service/aoc/addon_content_manager.cpp | c329c6ba | 874172cc | Refus d'un contenu NCA disparu, borne de buffer de réponse, validation d'ID avant PrepareAOC ; check-extracted-aoc-layout-host.py |
| headless/game_files.h | 9729ca93 | 9fd32a34 | Isolation des dossiers préfixés update/DLC/AOC à la découverte et dans les sélections |
| headless/settings_store.h | e49667c2 | e8760e57 | Revalidation des noms réservés des packages racine ; NRO/NSO restent des entrées directes distinctes |

Les deux derniers chemins sont vérifiés sur les propriétaires réels par check-exefs-directory-host.py : parcours des dossiers et sélections sauvegardées, source C++ sous O0/O2 et UBSan. Les pilotes « g++ » de ce Mac correspondent à Apple Clang : **ce n'est pas une validation GCC indépendante**.

L'ancien audit F07 qualifiait les changements de performance et de sources à sa date ; les anciennes empreintes ne sont remplacées dans le registre qu'après la comparaison ci-dessus. Les preuves de compilation intégrale PS5, de scènes invitées et de GPU/VRAM restent en P5. Les jalons P0-P4 ne sont pas automatiquement fermés par ce lot.
