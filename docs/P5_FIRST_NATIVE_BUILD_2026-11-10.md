# P5 — premier build natif PS5 après sortie P1/P2 (10 novembre 2026)

## Déclenchement explicite et limites

Ce fichier accompagne le **premier build natif de qualification P5**, sans publication automatique de release et sans affirmation de compatibilité console.

- Base fonctionnelle avant le build : `main` moteur `7154be1e727437e264609b805d80a2d1a17d82e2`.
- Sous-module vendor réellement épinglé par ce moteur : `0b0265079139622b759167c9d10a9a31aba1ea88`. Les travaux de documentation/triage ajoutés ensuite sur vendor `main` ne sont **pas** intégrés à ce build.
- Contrats P1/P2 : **17/17 preuves hôtes qualifiées** ; [sortie manuelle #42842249702](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42842249702) **verte** au SHA exact de base ; six autres CI obligatoires vertes au même SHA.
- Le workflow natif [`build-040-zbic.yml`](../.github/workflows/build-040-zbic.yml) est volontairement déclenché par le marqueur de commit `[full-build]`; **aucun** marqueur `[release]` ne demande de publier un binaire.
- Le commit qui contient ce document est nouveau par rapport au SHA des six CI : il n'ajoute que de la documentation de lancement de P5. Le vrai build et sa propre recette peuvent **échouer** et doivent être jugés sur leurs logs et artefacts, jamais sur le seul feu vert P1/P2.

## Critères d'analyse du premier run

1. Contrôles préalables de provenance, cache et configuration native. Si un contrôle échoue, corriger l'owner ou le script à l'origine, **ne pas désactiver le contrôle**.
2. Installation et restauration du toolchain, caches et dépendances épinglés; conserver le cache existant et les stages réutilisables.
3. Compilation/lien PS5, puis validation du package complet (assets, langues, légal, symboles, checksums) sur le **SHA exact** du run.
4. P5 reste **non validé sur console** jusqu'aux essais du framebuffer/IPC/Vulkan : FC27, Zelda BOTW, Mario Kart World et Donkey Kong Bananza. Un binaire compilé seul ne prouve pas l'exécution de ces jeux.
5. Ne pas écraser la dernière release publique ni déplacer le pointeur vendor sans validation distincte.

Le suivi est dans [l'issue #15](https://github.com/niakw/ProsperoEden-Encore/issues/15) et [la roadmap](ROADMAP_NS1_NS2_UNIFIED.md).

## GitHub Actions run créé

[**Run #42846319389**](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42846319389) est la première exécution native de P5, déclenchée automatiquement après le commit volontaire `6fcfe545` ([commit](https://github.com/niakw/ProsperoEden-Encore/commit/6fcfe5454a20f600f092e51bdda331a0796b8220)). Il doit être évalué selon ses propres étapes, artefacts et éventuelles erreurs. Les modifications **documentaires ultérieures** sur `main` n'entrent pas rétroactivement dans ce checkout et ne doivent pas annuler ce run.

## Premier retour P5 et correction isolée

[Premier run #42846319389](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42846319389) : **échec dans les contrôles source, avant tout build natif lourd**. Les logs ont identifié exactement deux assertions héritées du CMake et des scanners ROM plus anciens :

1. `tools/check-jit-stability.py` attendait des options `EDEN_SHARED_JIT` / `EDEN_JIT_COMPILE_BATCH` et des branches de source expérimentales retirées. Le vrai `headless/CMakeLists.txt` sélectionne **sans condition** `a64_emit_x64_standard.cpp` et `a64_interface_standard.cpp`, avec les deux disponibilités JIT à **0**. Le témoin vérifie désormais ces propriétaires et refuse tout rétablissement expérimental.
2. `tools/check-nlib-ui-recovery.py` attendait **deux** garde-fous `game_storage_available()`; le code maintenu en a **trois** : rollback en fin du scan initial, contrôle avant le batch de présence et contrôle après le batch avec `missing.clear()`. Le témoin contrôle maintenant explicitement les trois chemins, au lieu d'en supprimer un.
3. `tools/package-headless-native.sh` vérifiait la présence de `:BOOL=OFF` pour des anciennes options CMake **supprimées**. La validation du package rejette désormais explicitement les valeurs `:BOOL=ON` et `:UNINITIALIZED=ON`, tandis que la configuration CMake et les unités standard sont attestées par le contrôle JIT source.

Ces corrections de **tests devenus périmés**, sans changement moteur ni vendor, sont intégrées dans [`879cbddedcd16453406c5754e3ce338e233a50ea`](https://github.com/niakw/ProsperoEden-Encore/commit/879cbddedcd16453406c5754e3ce338e233a50ea).

[**Second build #42848349739**](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42848349739) lancé volontairement sur ce commit : contrôles toolchain/NCZ/langues/cache/métadonnées passés au début de son exécution ; résultat final natif/packaging **à juger sur le run**. Aucun marqueur de publication, aucun déplacement du gitlink vendor, aucune prétendue validation console.

## Requalification ciblée préalable au troisième build (10 novembre 2026)

Le [second build #42848349739](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42848349739) a encore échoué **avant la compilation PS5**, exclusivement sur deux assertions source obsolètes : le témoin JIT testait une écriture littérale alors que le package refuse correctement les anciens sélecteurs expérimentaux via une boucle, et Nlib testait un ancien cache TGA seulement tandis que le propriétaire réel valide WebP avec repli TGA vérifié. L'archivage historique de l'issue #15 a également eu sa ligne blanche finale corrigée pour la CI source-baseline.

Les deux scripts ont été synchronisés avec leurs sources réelles, en conservant les contrôles de refus et la sélection JIT standard, dans `6f414f4de5d93ad8fd74be98e3ad4234910cb0a1`. Le [workflow ciblé P5 #42850549825](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42850549825) a **réussi** les contrôles JIT et Nlib sur ce SHA, **sans build natif**. Ce feu vert autorise uniquement une nouvelle tentative de compilation PS5, pas une release.

Le troisième lancement est déclenché par le présent commit avec le marqueur explicite `[full-build]`, **sans** `[release]`. L'application reste épinglée sur vendor `0b0265079139622b759167c9d10a9a31aba1ea88` et la publication est désactivée.

## Troisième build : première compilation de dépendances natives observée

Le [run #42850915181](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42850915181), déclenché par le commit moteur `1c9b6bea09638152781ba1843e97ea6950b9cfe1` avec vendor `0b026507`, a **effectivement réussi** les étapes de contrat source/cache, toolchain, NCZ, contrôle de la langue du launcher, restauration de cache, métadonnées/légal, lancement/stockage et préflight packaging. Les anciens blocages JIT/Nlib des tentatives #1/#2 n'ont donc pas réapparu pendant ces étapes.

La tâche `Prepare native build inputs` (`make prepare JOBS=4`) a commencé. Son journal montrait la **compilation effective de Mesa/OpenGL** avec le compteur Ninja `[655/905]` lors de l'observation (messages Clang `-Wunreachable-code-generic-assoc` dans les macros du SDK `math.h`, sans échec démontré à ce stade). Ce compteur porte sur **une dépendance de préparation**, pas sur le nombre total d'unités du binaire Encore.

**Ce constat est un jalon intermédiaire, pas une qualification P5 :** `make prepare`, `Build and stage native release`, la validation du ZIP et les tests PS5 restent à vérifier sur les résultats finaux du run. Ne ni déplacer le gitlink vendor ni relancer un build natif pour de simples modifications documentaires. Aucun `[release]` n'a été demandé.

## Troisième build : échec de configuration et quatrième tentative contrôlée

Le [troisième build #42850915181](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42850915181) a **réussi `make prepare` et l'index de jaquettes**, puis échoué dans `Build and stage native release`, à la configuration CMake — **avant compilation du binaire Encore**, malgré la préparation effective et coûteuse des dépendances Mesa/OpenGL. Deux diagnostics distincts apparaissent dans le même journal :

1. `headless/CMakeLists.txt:1800` : `add_subdirectory(libwebp)` a été invoqué dans le callback `cmake_language(DEFER)`, ce que CMake interdit. Le dossier source upstream demeure épinglé sous `vendor/sources/libwebp`. La création du target WebP a été déplacée dans l'injection `CMAKE_PROJECT_yuzu_INCLUDE` **non différée**, et le callback ne fait plus que vérifier puis lier le target. Correctifs `c943d344` et `1f289cca`.
2. `headless/CMakeLists.txt:2003` : le sélecteur du noyau commun NS1/NS2 attendait le nom relatif `hle/kernel/k_address_arbiter.cpp` (ou une variante absolue écrite depuis `PORT_ROOT`) alors que le module threading vendor avait déjà sélectionné son propriétaire maintenu avec un autre chemin absolu. Le rapprochement utilise désormais `REALPATH` avant de **remplacer l'unique source**, pour les deux TUs d'arbitrage, sans dupliquer les propriétaires ni modifier le vendor.

Le contrôle source hôte et le test local léger de mécanisme CMake vérifient la nouvelle séparation « registration avant DEFER / lien après DEFER » et la normalisation des chemins. Le [préflight ciblé #42856202269](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42856202269) est **vert** sur `824d26e4538bab497ace1183dac14b98b168278a`, y compris les validations JIT, Nlib et le nouveau garde-fou `tools/check-active-cmake-source-boundary.py`. Il **ne remplace pas** un vrai configure natif ni les tests PS5.

Le workflow principal conserve désormais ses caches de dépendances après un `make prepare` réussi même si les étapes natives suivantes échouent (`0e951b37`); pas de reprise d'un binaire non validé. **La quatrième tentative native est déclenchée par ce commit `[full-build]`, sans `[release]`**, moteur sur `main` et sous-module vendor immuable `0b026507`. Aucun ZIP/binaire ou essai console n'est validé d'avance.

## Quatrième build : garde CI cache obsolète, cinquième tentative

Le [run #42856587272](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42856587272), moteur `067842fd`, vendor `0b026507`, a échoué **avant `make prepare`**, dans `Validate startup, elevation and storage contracts`. Toutes les autres vérifications du groupe ont continué et le seul échec rapporté est `tools/check-ci-cache.py:113` : l'assertion cherchait encore le nom d'étape supprimé `Save build caches after verified artifact uploads`. Le workflow utilise désormais `Save caches after successful native preparation` avec le garde conditionnel `!cancelled() && steps.prepare_native.outcome == 'success'` et `continue-on-error: true`. Ce n'est **pas** un échec de CMake ni une régression du moteur.

Le contrôle a été réaligné sur le vrai nom, l'ordre des étapes et la condition stricte d'une préparation réussie dans `a2e7f0f`; les invariants cache ont été revérifiés sur les fichiers de `main` (9 contrôles ciblés réussis). La cinquième tentative est demandée par ce commit `[full-build]`, sans `[release]` ni changement du vendor épinglé. Les deux correctifs de configuration WebP/Wait64 restent à confirmer sur un configure natif réellement exécuté.

## Cinquième build : source CPU6 après G11, conservation des optimisations et préflight natif renforcé

Le [cinquième build #42858138767](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42858138767) a réussi les contrats source/packaging et `make prepare`, puis a échoué à la configuration CMake avec `Pinned CPU6 scheduler/tick owner changed: arm/dynarmic/arm_dynarmic_32.cpp`. Les correctifs WebP/Wait64 des builds précédents ont franchi ce point. Les dépendances préparées ont été sauvegardées dans un cache GitHub de **3,55 Go** (pas de stage binaire prêt à diffuser).

**Diagnostic :** la sélection native G11 retire d'abord l'owner A32 relatif et ajoute `vendor/encore-active/eden-core/src/core/arm/dynarmic/g11/arm_dynarmic_32_native_normal.cpp`. Le bloc CPU6 cherchait ensuite l'ancien chemin relatif. Une simple substitution par l'ancienne source CPU6 aurait également perdu les optimisations JIT G11 côté A32. Pour préserver NS1 et le moteur commun, le mainteneur CPU6 A32 est désormais issu exactement de la variante **G11 native normal**, avec la seule modification vérifiée du diviseur de ticks à partir du masque de cœurs physiques.

- Moteur : sélecteur réel corrigé dans `41763ebb`, refus explicite si G11 A32 manque, sans second propriétaire compilé.
- Vendor : source CPU6 A32 complétée dans `22b69d6` ; nouveau gitlink effectif `22b69d6` via `dac4757` (les cinq premières tentatives restent historiquement liées à `0b026507`).
- Reproduction hôte : `tools/ns2/check_cpu6_scheduler_tick_host.py` teste désormais la sélection réelle de G11 A32 et A64, les quatre combinaisons console/NPDM, la stricte parité avec les sources maintenues et la correction des ticks.
- [Préflight CMake rapide #42863829705](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42863829705) : **SUCCESS** sur l'épingle mise à jour.
- [Préflight complet #42864115771](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42864115771) : **SUCCESS** sur `ab988c31`, avec compilation réelle des unités A32/A64 sur hôte et tests UBSan. Ces preuves sont une protection préalable ; elles ne constituent ni un configure PS5 complet ni une recette console.

**Politique avant la sixième tentative :** examiner les validations hôtes P0–P4 sur le **nouveau** gitlink, et ne déclencher un nouveau `[full-build]` qu'après ces garde-fous. Aucune publication automatique, aucun essai sur console déclaré réussi par anticipation.

## Sixième build — préflight complet CPU6 réussi, tentative sans release

Les contrôles préalables sur le nouveau vendor `22b69d6` sont verts : [préflight P5 complet CMake/G11/C++/UBSan #42864115771](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42864115771), [matrice P0–P4 #42863731769](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42863731769) (quatre shards et Task/Mesh), [core fast gate #42863731486](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42863731486), [préflight CMake rapide #42863829705](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42863829705). L'audit des 12 autres sélecteurs relatifs post-CPU6 n'a trouvé aucune source supprimée avant sa sélection ; il ne remplace cependant pas le vrai configure PS5. Le grand source preflight [#42863731617](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42863731617) était encore en cours lors de cette vérification et ne doit pas être présumé vert.

Le présent commit demande **une seule sixième tentative** de compilation native avec `[full-build]`, **sans publication de release**. Les dépendances du cinquième run ont été sauvegardées, mais un cache existant ne garantit pas son réemploi total. Analyser le premier éventuel échec à son stade réel, ne pas masquer de garde-fou et ne pas publier le ZIP avant les vérifications d'artefacts et console. Les changements documentaires ou la qualification hôte n'attestent aucun résultat PS5.

## Septième build : qualification C++ native ciblée, sans release

Le sixième run [#42865547895](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42865547895) a passé `make prepare`, CMake WebP/Wait64/CPU6 et le staging initial avant d'échouer sur le précontrôle **syntaxique natif**. Les quatre sources UI concernées sont corrigées depuis `dd9f2b9` : espaces de noms `Eden::EncoreOverrides` / `Eden::EncoreTextureProfiles`, initialisations complètes de `AppUpdateInfo` et suppression de la variable inutilisée `base_filter`. Le préflight rapide [#42870528718](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42870528718) valide notamment les initialisations C++ avec `-Werror`. Le registre post-F07 des deux sources modifiées a été révisé sans réécrire les 518 empreintes historiques ; il est vérifié **avant la toolchain**.

[Qualification P0–P4 #42870528636](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42870528636) : **SUCCESS**, vérification finale incluse sur `e4f6a825`. [Préflight P5 #42870528718](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42870528718) : **SUCCESS**. [Audit source #42870528816](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42870528816) : cinq jobs réussis sur six, `source-audit` long encore actif à l'instant du lancement, donc **ne pas le présenter comme vert**.

Ce commit lance **une seule septième compilation native** par `[full-build]` sur `main`, vendor conservé `22b69d6053db41b74edac2633c012f925b84f69e`, `[release]` absent. La compilation se fait en parallèle de l'audit long pour ne pas bloquer le progrès, avec les vérifications de provenance/cache et les contrôles de syntaxe toujours actifs. Aucun binaire, package ou essai console n'est prévalidé ; l'échec d'un contrôle bloquant doit être corrigé avant une tentative supplémentaire.

## Huitième tentative — garde JIT production actualisée

Le [septième run #42873646669](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42873646669), moteur `4dd28c7`, vendor `22b69d6`, a passé la configuration CMake et **23/23 contrôles de syntaxe C/C++ de sources PS5** (launcher, GPU, JIT et propriétaires communs). Il a ensuite échoué **avant toute compilation complète du binaire**, à l'assertion `tools/check-performance.py:110` demandant encore les anciennes options CMake `EDEN_SHARED_JIT` et `EDEN_JIT_COMPILE_BATCH` avec `OFF` littéral. Ces options ont été supprimées de la configuration unifiée et le vrai JIT standard est déjà garanti par le sélecteur CMake. Ce refus était un contrôle hôte périmé, pas une défaillance du runtime JIT. Le cache de dépendances a de nouveau été conservé (~3,54 Go).

Le garde performance est corrigé depuis `93225b7` : il vérifie dorénavant le propriétaire JIT standard, l'absence des options expérimentales et le refus d'un CMakeCache qui les activerait. Un mode `--source-only` conserve les mêmes contraintes sans dépendre du SDK : il est maintenant exécuté par [P5 native preflight #42876155761](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42876155761) **SUCCESS** et dès le contrôle source au début du workflow natif (`bbd4d227`). Les scripts qui suivent dans `build-headless-native.sh` ont été relus pour détecter d'autres assertions obsolètes sur ces mêmes sélecteurs : aucune autre occurrence de même nature dans les 18 scripts. Les fichiers moteur C++ et le gitlink vendor sont inchangés depuis la septième tentative.

[Audit source #42870528816](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42870528816) : **SUCCESS (6/6)**. [Matrice hôte P0–P4 #42870528636](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42870528636) : **SUCCESS**. Le présent commit demande **une unique huitième compilation PS5** par `[full-build]`, **sans** `[release]`. Aucun artefact ni rendu console n'est réputé qualifié avant leurs résultats réels.

## Huitième build — blocage du contrôle GPU, correctifs anticipés sans release

Le [run natif #42876772744](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42876772744), moteur `795289c9` et vendor `22b69d6`, a passé la préparation native et 18 étapes du workflow avant d'échouer dans `Build and stage native release`, **avant la compilation complète**. Le journal désigne `tools/check-native-gpu-thread.py:65` : l'ancienne chaîne `LoadingTick` ne normalisait pas le nouveau chemin maintenu `scheduler.HasPendingNativeChannels()` / `scheduler.ResumePendingNative(system.GPU())` du worker GPU natif. Il ne s'agit pas d'une erreur de compilation du moteur.

Le contrôle GPU est maintenant ajusté en distinguant le chemin de production natif du profil DEV, sans supprimer le réveil des canaux ou la comparaison au corps amont. Une vérification `--source-only` a été ajoutée à la CI P5 rapide et au début du workflow natif, pour refuser cette régression *avant* les dépendances coûteuses. Le préflight P5 [#42879764399](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42879764399) est vert (12/12 étapes), sans prétendre être un build PS5.

Le validateur de stage possédait aussi un inventaire périmé : `self-updater.elf`, `encore-release.json` et `mihawkgen/network.fgw` sont produits par le vrai packager, mais n'étaient pas acceptés par `check-staged-app.py`. L'inventaire a été corrigé sur `main` dans `98b9bb5` ; aucune archive n'est donc réputée validée par avance. Enfin, l'audit de référence a mis en évidence un espace final isolé dans ce document, corrigé ici.

**Politique :** ne déclencher une neuvième compilation explicite `[full-build]`, sans `[release]`, qu'après qualification des contrôles rapides sur le nouveau SHA ; ne pas représenter un code corrigé ou une CI hôte verte comme un binaire PS5 compilé ou testé en console.

## Neuvième build — tentative native unique après correction GPU

Le préflight P5 [#42879764399](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42879764399) a réussi ses 12 étapes sur le correctif du GPU maintenu. La comparaison de la boucle worker quiet avec le corps amont, après retrait strict des traces et de l'arbitrage natif des canaux, a également été vérifiée. Les premiers jobs P0–P4 sont verts, les autres se poursuivent sans échec confirmé lors du déclenchement. L'échec de source-baseline sur un ancien SHA était uniquement un espace final dans ce document, supprimé dans `2b8208f`.

Ce commit demande **une seule neuvième exécution** `[full-build]` sur `main`, **sans** `[release]`. Conserver le vendor `22b69d6`, les caches et les garde-fous. Avant de conclure au succès, exiger une compilation et un link natifs terminés, la validation de stage, les ZIP vérifiés, leurs SHA et les artefacts téléchargeables. Aucun test sur console n'est déduit de cette CI.

## Dixième build — Ninja reconfiguré et contrôlé avant compilation

Le neuvième build [#42880572712](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42880572712) a réussi la préparation native ainsi que tous ses contrôles GPU/JIT/hôtes, mais a échoué **au lancement de Ninja** : `build.ninja:33673` déclare deux fois `vendor/encore-active/eden-vulkan/fsr31_temporal_upscaler.h` comme sortie de reconfiguration CMake. La cause résidait dans la combinaison de `file(GLOB_RECURSE ... CONFIGURE_DEPENDS)`, de `configure_file` et de l'enregistrement explicite de l'ensemble des fichiers Vulkan comme `CMAKE_CONFIGURE_DEPENDS`. Le correctif `a992f8c` supprime ce dernier enregistrement redondant sans supprimer le suivi de nouveaux fichiers.

Le garde `ninja -t targets all` ajouté au lancement du moteur (`2c1783a`) valide désormais **le graphe PS5 réel immédiatement après CMake, avant les tests longs**, sans exécuter de compilation. La preuve hôte [#42886401919](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42886401919) a restauré le cache exact du neuvième run, isolé l'archive RADV, reconstruit le véritable SDK OpenGL vérifié, reconfiguré CMake et obtenu `CURRENT_MAIN_NATIVE_NINJA_GRAPH_PASS`. Cette preuve est une validation du graphe, pas une compilation ELF.

Sur la base de cette validation positive et de la matrice P0–P4 [#42884551271](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42884551271) **6/6 verte**, ce commit déclenche **une seule dixième compilation PS5** sur `main` avec `[full-build]`, **sans** `[release]`. Vendor conservé `22b69d6`. Le build doit encore prouver compilation, lien, staging, vérification d'inventaire, archive ZIP et SHA. Aucun succès console n'est présumé.

## Après le dixième build — qualification C++ ciblée et élargie (sans nouveau build complet)

**Dixième build natif : échec confirmé.** Le run [#42887138500](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42887138500) a passé la génération CMake, l'analyse Ninja, les contrôles préalables et a atteint environ **881/1870 objets C++**. Le compilateur a refusé deux sources : `vk_graphics_pipeline.h:97` accédait à `FixedPipelineState::forced_color_resolve` absent du header sélectionné ; `ns2-astc/texture_cache.h:668,707` utilisait `SCOPE_EXIT` sans dépendance explicite. **Aucun ELF ni ZIP natif issu de ce run.**

La sélection CMake a été corrigée sans modifier les pins de `vendor` : `headless/vulkan.cmake` installe le header ABI maintenu et une mince façade d'inclusion pour `scope_exit`. Les premières vérifications syntaxiques sur le véritable compilateur PS5 ont ensuite mis en évidence la mutation illégale d'une capture `const` dans `vulkan_renderer_r08.cpp` et la construction inline d'un `unique_ptr` vers un type FSR3 incomplet. Les commits `2f26b2b`, `7e60ff8` et `f53abc2` résolvent ces écarts en respectant l'API du scheduler et la durée de vie FSR3. La liste `video_sources` a par ailleurs été corrigée (`66920e7`) : les unités FSR3/LSFG et les objets Mihawk ne doivent pas disparaître sous un `set_property(TARGET video_core PROPERTY SOURCES ...)`.

**Contrôle intermédiaire [#42899308180](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42899308180) :** 9 unités C++ ciblées validées ; graph Ninja et sélection des sources graphiques validés ; **162/163** unités au balayage C++ — seul `vulkan_present_manager.cpp` échouait avec `free_waiters`, `present_waiters` et `present_ready_cv` absents du header PS5 choisi. Le correctif `a686176` et l'alignement `f3680d3` rendent ce header compatible avec l'implémentation Vulkan épinglée, tout en conservant les méthodes de réservation non bloquante Encore. Un garde source-only `tools/check-ps5-present-header-contract.py` compare désormais ce header avec son propriétaire maintenu **avant l'installation de la toolchain**.

**Contrôle [#42901950697](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42901950697) : SUCCESS 7/7.** Génération CMake native et lecture Ninja vertes ; les 10 unités prioritaires, dont PresentManager, compilent avec `clang++-18 --target=x86_64-sie-ps5 -fsyntax-only` ; **163/163** autres unités sélectionnées passent ; le raccordement des composants FSR3, LSFG et Mihawk au graphe d'archives a été vérifié. Ce contrôle n'a produit **ni fichier objet PS5, ni édition des liens, ni packaging, ni validation console**.

Avant le onzième build complet, le contrôle [#42903605335](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42903605335) élargit le préflight à **jusqu'à 400 unités C++ réelles** du graphe PS5, incluant les chemins `video_core`, `core`, `audio_core` et `common`. Sur une future tentative native, la commande Ninja utilise `-k 0` pour récolter les éventuelles **erreurs indépendantes en un seul run**, avec échec obligatoire et sans packaging si la compilation échoue. Aucun build complet ni publication n'a été demandé par cette mise à jour documentaire. Conserver la séparation entre syntaxe, compilation/édition des liens et validation matérielle.
