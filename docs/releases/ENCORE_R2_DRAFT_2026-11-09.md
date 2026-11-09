# Eden Encore R2 Preview — développement depuis R1 (15 octobre – 9 novembre 2026)

> **PRÉRELEASE EN BROUILLON — PAS DE BINAIRE JOINT, PAS DE NOUVELLE COMPILATION PS5.** Ce document présente la candidate de développement depuis la vraie release R1 du 15 octobre. Les étapes P0–P4 sont considérées comme achevées dans le périmètre éditorial de cette candidate ; les justificatifs de clôture définitifs doivent être associés à leurs SHA/CI et **la qualification PS5 P5 reste distincte**. Aucune compatibilité universelle, aucun gain FPS chiffré et aucun premier rendu NS2 réel sur console ne sont promis.

**Référence du dernier binaire public :** [Eden Encore R1 FTP du 15 octobre 2026](https://github.com/niakw/Prospero.Eden-Encore/releases/tag/encore-R1-56293953) · source binaire `5629395324ff65c98b50c44f35f2142a4a92654a` · [CI native #38752177232](https://github.com/niakw/Prospero.Eden-Encore/actions/runs/38752177232) · commit historique du tag `f037a78`. La publication du 30 octobre dans le [dépôt actuel](https://github.com/niakw/ProsperoEden-Encore) est une **copie sans recompilation**.

**Candidate source documentée :** moteur `7baca525c8939ca9eb960895b5770dc5a034a6ea` · sous-module vendor `e933d8838604224eca32aa175340efb9e6cd9742`. Ce n'est **pas** un identifiant de build PS5.

## Ce qui change depuis la R1

### 1. Moteur commun NS1/NS2 et architecture
- Réunification du traitement NS1 et NS2 dans le moteur actif de `main`, plutôt que deux applications, profils de release ou implémentations parallèles.
- Révision des chemins CPU, GPU, HLE, contenus, mémoire et rendu pour réutiliser les composants communs, avec admissions précises et refus explicites des cas inconnus.
- Consolidation des propriétaires natifs et du sous-module vendor épinglé à un commit exact ; contrôle des sources effectivement sélectionnées et compilables.
- Politique de non-régression NS1 et séparation stricte des validations code/hôte, build natif et vraie console.

### 2. Chargement des jeux, mises à jour, DLC et fichiers système
- Découverte des jeux `NSP`, `XCI`, `NSZ`, `XCZ` et contenus extraits `ExeFS/RomFS` ; prise en compte des chargements directs `NRO`, `NSO`, `NCA`, `NAX`, `KIP` selon les conditions du format et du contenu disponible.
- Lecture NCZ avec contrôles de taille, intégrité, blocs compressés, cache/extraction bornés et annulation sûre ; préservation des chemins existants LZ4 et ZBIC/zstd pour les segments NSO.
- Organisation souple des répertoires `roms/`, `updates/`, `dlc/`, `keys/ns1`, `keys/ns2`, `firmware/ns1`, `firmware/ns2` ainsi que les imports de firmware nommés, sans deviner la génération à partir d'une simple extension.
- Travail sur le conteneur NUP : VFS native, métadonnées TOC, SHA-256, UUID, validation des chemins, flux raw/zstd, montage et liaison RomFS/AoC.
- Gestion plus stricte des erreurs : contenus incomplets, chemins dangereux, tailles incohérentes, partitions et références non autorisées.

### 3. CPU invité, JIT, mémoire et services HLE
- Intégration des chemins d'admission de processus et de métadonnées NPDM/ACID/ACI, ExeFS et services système des deux générations.
- Correctifs sur le cycle de vie des processus, sessions, workers, poignées, IPC/TIPC, commandes conditionnelles, SVC et synchronisation des tâches.
- Gestion des limites GPU/GMMU, NVMap, remapping, rollback mémoire après échec, alias JIT, partitions d'adresse 49 bits et granularités adaptées.
- Ajustements des atomiques, attentes, fences, invalidations de caches, timers et ordonnancement avec témoins hôte positifs et négatifs.
- VI/VI2, affichage, audio et décodage vidéo : contrôles de protocoles, files de surfaces, fences, cadence et libération des ressources.
- Améliorations de fiabilité autour de la mémoire clairsemée, de l'isolation par jeu et des états d'échec conservateurs.

### 4. GPU : traduction, Compute, textures et Vulkan
- Décodage et abaissement des formes GPU Ampere vers les représentations communes Maxwell/IR et le backend SPIR-V/Vulkan ; registres élevés, branchements, instructions arithmétiques et comparaisons.
- QMD3 Compute : banques CBUF, SSBO, accès indirects, extensions de registres, spans, alignements, écritures globales, atomiques, suivi des ressources et dépendances de dispatch.
- Adaptations GPFIFO/GMMU, DMA, sémaphores, accès par canal, processus et fences ; refus des instructions ou ressources non démontrées plutôt que faux succès.
- Stages Vertex, Fragment, Geometry, Tessellation et Task/Mesh : source native, limites d'admission et contrôles de génération SPIR-V ; pas de promesse de rendu complet pour un jeu donné.
- Textures TIC/TSC, ASTC, vues d'images, tableaux, sparse, invalidation et durée de vie sous fence ; synchronisation GPU/CPU, cache de pipelines et sécurité des buffers.
- Correctifs de compatibilité, cohérence de présentation et protection contre les blocages et destructions prématurées du renderer commun.

### 5. Image, upscaling, anti-aliasing et rendu optionnel
- **FSR 1 spatial préservé**, avec EASU/RCAS, réglage de netteté et profils vidéo ; il ne doit pas disparaître lors du nettoyage des traductions ou de l'UI.
- Revue des choix de mise à l'échelle, de netteté, de résolutions internes, des filtres bilinéaires/Lanczos et des variantes d'upscaling/AA, avec compatibilité et coût GPU à qualifier par titre.
- Préparation des chemins optionnels de génération d'images et de composition temporelle ; ces choix restent distincts des FPS réellement simulés par le jeu.
- Travail R09 sur l'amélioration neurale : profils A4K, choix Original/Compact, inventaire du modèle utilisateur privé, contrôles de poids, scheduler et graphe, ABI SPIR-V, exécution et lectures d'images côté hôte.
- Séparation stricte entre import authentique, test GPU logiciel, exécutable lié et inférence complète : **aucune image réellement produite par le réseau Original entier sur PS5 n'est revendiquée**. Aucune DLL ou aucun poids propriétaire n'est distribué.

### 6. Lanceur PS5, bibliothèque et commandes
- Interface pensée pour la manette : accueil, bibliothèque, récents, options par jeu, choix de langue, préférences d'affichage et animations.
- Travail sur les jaquettes NS1/NS2, boîtiers 3D, faces avant/arrière reconstruites à partir de médias existants, gestion des titres longs et affichage des cas sans jaquette.
- Harmonisation des thèmes, palettes, aperçu haute définition et contrôles d'accessibilité.
- Menu rapide **par appui court sur le pavé tactile**, et **non** par le bouton système central ; sections jeu, graphismes, mapping et diagnostics, avec messages lorsque certains changements demandent un relancement.
- Réglages personnalisés, mappage manette, raccourci FPS retiré au profit de l'option du menu, et garde-fous contre l'effacement des préférences/sauvegardes.
- Revue des catalogues multilingues (29 catalogues), traductions, chaînes obsolètes et présentation homogène des fonctions.

### 7. Fiabilité, sécurité, packaging et outils GitHub
- Correctifs sur freezes, qualité des présentations Vulkan, cadence, HUD, opérations graphiques et durées de vie des ressources : **travaux source/hôte**, pas mesure de performances PS5 certifiée.
- Contrôles de sécurité, chemins de fichiers, lectures bornées, validation des métadonnées et restrictions d'import réseau ; CodeQL et alertes triées séparément.
- CI hôte Clang/GCC/UBSan, contrôles SPIR-V, validations Vulkan, previews du lanceur, source preflight, core fast gate et matrice de qualification P0–P4 par SHA.
- Contrats finis P1/P2 **H01–H07 / G01–G10** avec témoins positifs/négatifs et décision `--enforce` distincte d'un simple audit structurel.
- Alignement des README, guides d'installation, documents techniques, traçabilité de la vraie R1, provenance des artefacts, avertissements de compilation et séparation source/hôte/matériel.
- Neutralisation des libellés d'Actions et des commentaires du code appartenant au projet lorsqu'ils utilisaient des marques inutiles ; les noms d'API, références techniques, licences et crédits tiers sont conservés.

## État des jalons et limites à connaître

| Périmètre | Présentation de cette candidate |
| --- | --- |
| **P0** architecture, provenance, CI | **Terminé dans la roadmap de développement de la candidate** |
| **P1** chargement, CPU/HLE, mémoire et services | **Terminé dans le périmètre de développement de la candidate** |
| **P2** GPU, Compute, SPIR-V et compatibilité des chemins communs | **Terminé dans le périmètre de développement de la candidate** |
| **P3** lanceur, contrôles et ergonomie | **Terminé côté développement** |
| **P4** contrôles et qualification hôte | **Terminé côté développement** ; l'état opposable dépend du reçu final et du couple SHA exact |
| **P5** compilation, installation, vrais jeux et validation PS5 | **Pas couvert par ce brouillon**, à qualifier avant livraison d'un nouvel ZIP/FTP/FFPFSC |

**Important :** « terminé » ci-dessus reflète la consigne éditoriale de préparation de cette prérelease. Le tracker technique [#15](https://github.com/niakw/ProsperoEden-Encore/issues/15) et les [critères de sortie](https://github.com/niakw/ProsperoEden-Encore/blob/main/docs/P0_P4_EXIT_MATRIX_2026-11-06.md) restent les sources de preuve : **ne pas transformer cette rédaction en attestation automatique du validateur `--enforce`**.

## Compatibilité et distribution

- Firmware console matériellement testé jusqu'ici : **13.60**. Aucune nouvelle qualification 13.60 pour cette candidate source ; autres firmwares non certifiés.
- Switch 1 : préserver les comportements historiquement testés, sans déduire de la CI que les problèmes de gels/HUD et les régressions sont résolus sur appareil.
- Switch 2 : pas de première image invitée réelle confirmée pour Mario Kart World ou Donkey Kong Bananza sur PS5 ; ne pas annoncer de liste de jeux jouables.
- R09, interpolation, rendu neuronal et optimisations avancées : intégration ou vérification hôte ne signifie pas disponibilité fonctionnelle dans le binaire du 15 octobre.
- **Aucun fichier joint.** Cette entrée est une prérelease **draft**, à conserver privée jusqu'à la compilation volontaire P5, contrôle du ZIP/ELF/symboles et tests console.
- L'ancienne R1 reste le dernier paquet FTP public identifié : [version originale](https://github.com/niakw/Prospero.Eden-Encore/releases/tag/encore-R1-56293953). Les utilisateurs ne doivent pas remplacer leur installation par de simples artefacts source/hôte.

## Pour suivre l'évolution

- [Code actuel et commits](https://github.com/niakw/ProsperoEden-Encore/commits/main/)
- [Roadmap NS1/NS2](https://github.com/niakw/ProsperoEden-Encore/blob/main/docs/ROADMAP_NS1_NS2_UNIFIED.md) · [Issue de suivi #15](https://github.com/niakw/ProsperoEden-Encore/issues/15)
- [Audit de la R1 et des workflows](https://github.com/niakw/ProsperoEden-Encore/blob/main/docs/RELEASE_BASELINE_WORKFLOW_AUDIT_2026-11-09.md)
- [Guide d'installation](https://github.com/niakw/ProsperoEden-Encore/blob/main/INSTALL.md) · [README](https://github.com/niakw/ProsperoEden-Encore/blob/main/README.md)

---

## English summary

This **unpublished draft prerelease** records the work since the last genuinely compiled public PS5 R1 build of **15 October 2026**, not the unchanged 30 October mirror. Development milestones P0–P4 are treated as complete for this candidate's changelog, while final same-SHA receipts remain the source of technical proof and **P5 hardware/build qualification is separate**. Areas covered: unified Switch-generation engine architecture, game/file loaders and NUP, memory and HLE/IPC services, GPU/Compute/graphics translation, texture and Vulkan safeguards, preserved FSR 1, optional neural rendering research, controller-touchpad quick overlay, launcher artwork/locales, testing and documentation. **No PS5 binary, no downloadable attachments, no confirmed real NS2 game frame, and no guaranteed FPS improvement are implied.**