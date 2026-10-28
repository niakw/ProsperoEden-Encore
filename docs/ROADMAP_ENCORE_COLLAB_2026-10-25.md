# Eden Encore — Roadmap collaborative (2026-10-25)

**Source de vérité du chantier expérimental**, branche `feat/graphics-network-achievements`.  
**Branche de référence console** : `dev/ps5-sparse-jit` (validation technique F01–F06 = 6/6, F07 = test réel FC27 toujours ouvert).  
**Attention au décalage de branches** : la branche expérimentale a été créée depuis `366104d` et **n'intègre pas encore** les huit commits ultérieurs de la branche principale (dont F06). Aucune fusion dans la branche console avant rebase/merge contrôlé, tests complets et qualification matérielle.

## Journal d'exécution — chantier R00/R04

- **R00 code fusionné** : [PR #18](https://github.com/niakw/Prospero.Eden-Encore/pull/18), commit `925661f`. La branche feature possède désormais les huit commits F06 validés. La branche principale n'a pas été modifiée.
- **R04 implémenté sur la branche feature uniquement** : AudioIn PS5 ouvre un `SilentInputStream` qui produit un vrai tableau de samples à zéro, `main.cpp` route les sessions AudioIn vers l'adaptateur, `devices_check.cpp` vérifie les tailles et les échantillons. Le destructeur natif RomFS détache les chaînes `sibling/child/file`; `romfs_check.cpp` teste 32768 voisins fichiers puis répertoires sur pile de 256 KiB.
- **Preuve complémentaire source-extracted** : `tools/check-feature-r04-native-boundary-host.py`, compile les corps *exacts* du C++ AudioIn et RomFS avec UBSan, en `-O0` et `-O2`. Ne remplace pas le test intégré `eden-romfs-check` ou `eden-devices-check`.
- **Première exécution réelle** : le test source-extracted AudioIn/RomFS est passé sur [GitHub Actions #40237741910](https://github.com/niakw/Prospero.Eden-Encore/actions/runs/40237741910), job `source-extracted-native-r04`. L'audit de cohérence a ensuite signalé qu'il comparait encore RomFS à l'ancienne version. Le contrôleur `tools/check-vendor-consolidation-debt.py` a été **adapté pour vérifier exactement la nouvelle destruction non récursive** ; correctif natif non désactivé.
- **Validation non anticipée** : les contrôles de propriété de sources, la prévalidation complète, CodeQL et la compilation PS5 sont en cours de requalification sur le nouveau SHA. R04 n'est pas considéré terminé avant les résultats correspondants.
- **F07** : toujours réservé au test de base FC27 sur `cd4857c8`, sans ces changements.

## Convention de suivi : pas de faux progrès

- Statuts : **À faire**, **Audit**, **Prototype host**, **Intégré natif**, **CI verte**, **Validé console**, **Reporté**. Un document ou un test de politique ne vaut pas intégration fonctionnelle.
- Responsable **Assistant** : investigation, sélection/licences, codes sources, correctifs, compilation, tests hôtes, workflows, nettoyage, documentation, package reproductible et matrice de preuve.
- Responsable **Utilisateur** : choix perceptifs (qualité/style/ergonomie), fourniture de deux PS5 si test multi-console exigé, test console **uniquement après** publication d'un build vert qualifié, retours visuels et logs. Ne pas faire du test console un substitut aux tests d'intégration hôte.
- **Droit de refus** technique : si coût GPU, licence, sérialisation, sécurité ou gameplay insuffisants, garder une option désactivée et tracer la raison. Pas de promesses de 30→60 FPS « natifs ».
- Un seul tableau ci-dessous fait foi ; enregistrer SHA, preuves, test et décision pour chaque livraison.

## Ordre global des jalons et séparation des rôles

| Phase | ID | Livrable réellement attendu | Assistant — exécution/preuve | Utilisateur — intervention | État |
|---|---|---|---|---|---|
| 0 — garde-fous | R00 | Remettre à niveau la branche feature sans détériorer la validation F01–F06 ; verrouiller baseline F07 | Comparaison commits, résolution des conflits, diff natif, gates host, PS5 build, CodeQL | Aucun test demandé | Code fusionné, CI feature en cours |
| 0 — mesure | R01 | Banc de mesures commun : guest FPS, present FPS, displayed FPS, CPU/GPU frametime, latence pad, RAM/VRAM, caches, qualité HUD, audio, pause/mi-temps | Instrumentation bornée, test de non-régression des compteurs, export d'un rapport JSON | Choix des scènes FC27/BOTW, validation A/B seulement au jalon console | Source composites/queue/generated/Present API branchés + analyse JSON, hôte vert ; GPU vrai/latence et console non mesurés |
| 1 — correctifs | R02 | Audit des corrections Swordpdf/ProsperoEden et forks directs : classifications déjà présent/pertinent/incompatible | Comparer patches aux **sources compilées** vendor/overrides, numéro SHA, licences, régression host | Aucun | Audit en cours |
| 1 — correctifs | R03 | Patches ciblés : shader NaN `e34338d`, transferts RADV `1862764` | Modifier la vraie source propriétaire/patch RADV, tests shaders, stress barrières/transferts et rebuild complet | Validation visuelle FC27 uniquement si build global vert | Shaders NaN + RADV transferts/barrières intégrés ; source CI/PS5 à qualifier |
| 1 — robustesse | R04 | RomFS vaste arborescence `4f813a3`, AudioIn buffer silencieux `01e81e1`, durée de vie et arrêt corrects | Tests sanitizer à 256 KiB/32768 entrées, AudioIn longueur/données et zéro régression AudioOut | Aucun | Correctifs natifs intégrés ; CI en cours |
| 1 — opportunités | R05 | GPU page table `1390bf5`, RAM allocation, source pins, JIT, locks/pipelines, cache sérialisé et suppression des doubles correctifs | Comparer à Encore : vertex input, 512 draws, striped waits, écriture atomique déjà présents ; n'importer que les écarts | Aucun | Audit |
| 2 — interface de rendu | R06 | **Rendu graphique modulaire** sous trois familles indépendantes : résolution améliorée, fluidité améliorée, rendu neuronal IA | Points d'insertion Vulkan (avant/après HUD), images/queues/fences, copie zero-copy si possible, toggles opt-in, recovery/fallback, profil par jeu | Choix des libellés et défauts | Contrat de sélection des 4 familles et tests hôtes verts ; aucun backend installé |
| 2 — résolution | R07 | Upscaling : Natif / FSR spatial / FSR temporel 3.1 si infos validées ; AA/FSR et HUD séparé | Vérifier depth, jitter et motion vectors issus du rendu émulé ; calcul du coût GPU et A/B fidélité | Retour sur netteté et textures de FC27/BOTW | À faire |
| 2 — fluidité | R08 | MihawkGen (priorité native PS5), comparaison FSR 3 frame generation, LSFG facultatif si juridiquement/native viable | Porter petites unités isolées, poids + licence, pipeline de présentation, 30→60 *affichés* avec FPS du jeu constants, reset à la pause/menu | Test visuel et ressenti input après CI | À faire |
| 2 — neurones | R09 | **Neural Rendering AMD/Vulkan** : visages/peau/matériaux/lumière, sans modifier les vraies textures jeu | POC Vulkan natif SPIR-V, analyser RDNA2, budget mémoire+compute, pré-upscale vs post-upscale, alpha/UI, couleur HDR/gamma, scènes statiques et mouvement | Qualité artistique et artefacts visage, comparaison captures A/B | Recherche ; pas de runtime |
| 2 — textures | R10 | **Textures HD IA** séparées du rendu neuronal : packs optionnels par Title ID, prétraitement hors PS5 si nécessaire | Pipeline autorisé modèles ouverts (Real-ESRGAN ou équivalent), validation dims/formats/quantification, ram budget, cache, fallback GPU | Choix éventuel des packs / style ; aucun fichier protégé demandé | À faire |
| 3 — multimédia launcher | R11 | Jaquettes Switch 3D front/back recomposées : couche support plastique, vraie composition `cover`, haut du back complet, pas de double tranche ; logo et description GameDB | Cas réels sans box images, chargement LaunchBox **à la sélection uniquement**, placeholder opaque, WebP 80% avec décodeur natif, cache/quotas | Validation visuelle sur maquettes et photos une fois testable | À faire |
| 3 — UI | R12 | Launcher : navigation L1/R1 des tâches de fond, profil/avatar si PS5 l'autorise, FR/EN, formats Go, focus/manette, 3D L2/R2, description README capture réelle | Tests hors console de génération/rendu et snapshots de composition, compat bibliothèque et mémoire | Validation ergonomie, seulement sur build de qualification | À faire |
| 3 — containers | R13 | Formats Switch NSP/XCI/NSZ/XCZ, ZBIC/ZSTD et NRO/NSO/NCA/NAX/KIP, LZ4 selon contenu, mods/DLC/updates sans extraction fragile | Inventaire matrice **par forme d'entrée**, parsers concrets, corpus légal synthétique, fuzz/quotas, chemin happy+failure, pas d'affirmation sans lancement | Essais finaux uniquement des formats que l'utilisateur possède légalement | Audit/À faire |
| 4 — réseau | R14 | Multijoueur privé LDN `eden-room` compatible mode local wireless des jeux Switch | Adapter Swordpdf multiplayer et pont HLE LDN, chiffrement/auth réseau privé, mot de passe session (pas plaintext disque), UDP borné, DNS/IPv4, reconnection, nettoyage | Fournir si possible seconde instance/console, test partie complète | Audit ; non intégré |
| 5 — trophées | R15 | Dépôt isolé de catalogues Switch 1 avec IDs/versions + licences/curation ; progression **manuelle** locale | Extraire module `extras/switch-trophies` quand API/version stable, persistance atomique, UI, notifications, aucun faux déblocage | Définition des règles de trophées souhaitées et visuels | Prototype host partiel |
| 5 — trophées auto | R16 | Déblocage automatique seulement si évènement fiable HLE/observation versionnée ; jamais « tous les jeux » automatiquement sans preuve | APIs d'événements, détecteurs tests, invalidation après mise à jour et faux positifs, mode manuel pour les jeux inconnus | Validation sur jeux pilotes ; autoriser notifications | À faire |
| 6 — PS5SX2 | R17 | Audit technique PS5SX2 : préchargement atlas/jaquettes, packs HD, cache, UX notifications, processus de démarrage | Comparer propriétaires et contraintes mémoire, porter concepts uniquement avec preuves | Aucun avant prototype console | Audit |
| 6 — hygiène | R18 | Nettoyage source/vendor/CMake/tools/test/README, permissions CI, code scanning, secrets/IP, licences, formats, fichiers morts | Rejouer `check-repo-hygiene.py`, `check-active-source-inventory.py`, `check-vendor-consolidation-debt.py`, `check-eden-optimization-coverage.py`, scan de fuites + builds | Aucun | Contrôles host déjà verts ; audit manuel restant |
| 7 — intégration | R19 | Builds indépendants par fonctionnalité avec désactivation sûre + scénarios concurrents (NR+FG, FSR+FG, HUD) | CI hôte/sanitizers, bundle PS5, A/B baseline FC27/BOTW, latence GPU/cache, tableaux comparatifs | Un seul cycle de qualification consolidé, pas un test à chaque commit | À faire |
| 7 — produit | R20 | Décision de fusion, release notes FR/EN, guide sécurité/limites, suivi par fonctionnalité | Merge seulement des modules validés, changelog/permissions et rollback, package avec SHA | Acceptation console matérielle par l'utilisateur | À faire |
| 7 — distribution / maintenance | R21 | **Mise à jour de l'application Eden Encore depuis les GitHub Releases** dans Paramètres : vérification manuelle forcée et recherche automatique au lancement du launcher (opt-in), proposition par pop-up puis installation uniquement après accord | Comparateur de versions et canal release stable, client GitHub borné, vérification du paquet PS5 et SHA-256, installateur natif sûr selon capacités réelles, tests hors console puis CI/PS5, préservation des données utilisateur | Choix d'activer la recherche au démarrage ; confirmation/refus de la mise à jour lorsqu'elle est proposée ; essai final sur build qualifié | **À faire — spécification uniquement** |
| 8 — recherche / architecture | R22 | **Question : une recompilation statique optionnelle de jeux Switch 1 ARM64 vers x86-64 PS5 peut-elle compléter Eden Encore ?** | Étude comparative JIT Dynarmic vs chaîne AArch64 → C/C++/LLVM → binaire PS5 ; analyse des barrières NSO/NRO, relocations, JIT/dynamiques, ABI, SVC/HLE, GPU Maxwell/NVN, licences et maintenance ; preuve de concept sur programme synthétique autorisé, puis A/B limité si faisable | Aucun test console avant prototype qualifié ; choix ultérieur seulement après preuves | **À étudier — question ouverte, aucune implémentation** |

### R21 — Mise à jour intégrée d'Eden Encore (spécification, non implémentée)

**Cible** : ajouter à `Paramètres → Application → Mises à jour` une fonction de mise à jour **de l'application native Eden Encore** depuis les releases GitHub officielles de [`niakw/Prospero.Eden-Encore`](https://github.com/niakw/Prospero.Eden-Encore/releases). Ne pas confondre cette fonction avec la mise à jour des jeux Switch, des DLC ou du firmware émulé.

**UX à livrer** :
1. **« Vérifier / mettre à jour maintenant »** : action manuelle disponible même si l'automatisme est désactivé. Elle force une **nouvelle consultation** de GitHub (pas seulement un cache) et, si une version compatible plus récente existe, permet de la télécharger et installer après confirmation. En l'absence de nouveauté, afficher clairement « Déjà à jour ». Ne jamais rétrograder ni réinstaller silencieusement la version courante.
2. **« Rechercher les mises à jour au démarrage »** : interrupteur persistant, **désactivé par défaut**. À chaque entrée dans le launcher (une vérification par démarrage, et non par rafraîchissement d'écran), effectuer la détection **en arrière-plan sans bloquer l'affichage ni le lancement d'un jeu**. Si une release éligible est disponible, ouvrir une **pop-up à l'entrée** avec version installée, version proposée, résumé/changelog et boutons **« Mettre à jour » / « Plus tard »**. Aucune installation ni téléchargement intégral sans validation explicite. Si le joueur est déjà en jeu, différer la pop-up jusqu'au retour au launcher.
3. Après acceptation : état de téléchargement/vérification/installation lisible à la manette ; en cas de succès, inviter à **redémarrer l'application** si nécessaire. Annulation ou « Plus tard » préserve la version existante et les préférences ; toute erreur réseau se traduit par une indication non bloquante et ne boucle pas sur des pop-ups.

**Source et validation des releases** :
- Canal **stable uniquement** : consulter les releases publiées du dépôt officiel (`GET https://api.github.com/repos/niakw/Prospero.Eden-Encore/releases/latest` ou équivalent API vérifié) ; rejeter les drafts, préreleases, branches expérimentales, assets non correspondants, paquets FTP et réponses inattendues. Ne jamais télécharger un exécutable depuis une URL dictée par un changelog ou une redirection non approuvée.
- Comparer la version **réellement installée** à la version annoncée (version + identifiant de build lorsque nécessaire), sans comparer naïvement des chaînes lexicales ; ne proposer une version qu'en présence d'un **asset de release destiné à l'app PS5** et compatible avec l'identifiant de l'application, le format de paquet et les prérequis installateur/firmware. Ne pas présumer que le contenu d'une release GitHub est automatiquement installable sur la console.
- Télécharger dans un emplacement temporaire avec quotas, limites de taille et timeouts ; contrôler l'origine HTTPS, les métadonnées du paquet et un **SHA-256 publié et fiable** avant toute installation. En l'absence de hash exploitable, d'asset compatible ou de privilèges/API d'installation prouvés : refuser l'installation automatique et expliquer l'indisponibilité, plutôt que tenter une copie hasardeuse.
- **Ne jamais écraser l'exécutable en cours à chaud.** Vérifier l'API/mécanisme natif PS5 d'installation/upgrade, la possibilité de relancer l'app et le retour sur échec. Préserver `/data`, configurations, sauvegardes, caches utiles et bibliothèque ; aucune suppression implicite, aucune réinitialisation. Prévoir une stratégie de récupération réaliste plutôt que promettre un rollback système non démontré.
- Éviter vérifications concurrentes, pop-ups doublons, notifications répétées après refus pendant la même session, ou requêtes réseau à chaque navigation. Le mode hors ligne et les erreurs GitHub/rate limit doivent laisser le launcher pleinement fonctionnel.

**Preuves avant validation R21** : tests hôtes avec réponses GitHub simulées (aucune release, déjà à jour, version supérieure, prerelease/draft, asset manquant, manifest/hash altéré, réseau lent/absent, annulation, refus, reprise), tests de versionnement, non-régression boot/menus/manette, tests de sûreté de l'installateur réel, build PS5 et CI. Vérifier sur console seulement après qualification complète, et **uniquement sur la branche laboratoire** jusqu'à décision R20. **Statut : À faire ; aucun updater livré aujourd'hui.**

### R22 — Étude de faisabilité : recompilation statique Switch 1 → PS5 (question ouverte)

**Question de recherche :** une chaîne de recompilation statique, inspirée des approches type ReXGlue mais **non transposable telle quelle** à la Switch, pourrait-elle exécuter certains jeux Switch 1 sur PS5 plus efficacement que le JIT Dynarmic, **en complément de l'émulation classique et sans sacrifier la compatibilité** ?

**Périmètre de l'étude, sans engagement d'implémentation :**
1. Comparer les architectures (Switch 1 : AArch64 / ARMv8 ; PS5 : x86-64), la faisabilité d'une traduction statique du code NSO/NRO vers IR/C/C++/LLVM ou code natif, le traitement des relocations, branches indirectes, modules liés, données exécutables et génération dynamique de code. Établir explicitement les limites par titre et versions.
2. Identifier les composants **qui resteraient émulés ou adaptés** : services Horizon/SVC/HLE, synchronisation, mémoire, entrées, audio et surtout API GPU NVN/Maxwell → Vulkan/RADV. Une recompilation CPU ne corrige pas automatiquement les shaders, le HUD, les textures ou les problèmes de synchronisation graphique.
3. Évaluer les coûts de développement, maintenance, compilation, taille des binaires, cache, fiabilité et compatibilité ; comparer avec le JIT existant et les optimisations actuelles. Examiner les projets open source réutilisables, leurs licences, leur état réel, les contraintes d'outillage PS5 et le droit applicable ; ne pas redistribuer de jeux, clés, firmware ni code propriétaire.
4. Si les obstacles précédents sont franchis, produire d'abord un **POC synthétique légal** avec tests d'instructions et d'appels HLE, puis un protocole d'évaluation ciblé (FC27 / BOTW uniquement si titres et droits disponibles) avec mêmes scènes, guest FPS, 1 % low, frametimes, HUD, stabilité, latence et usage RAM. Distinguer le coût de compilation hors ligne du coût d'exécution.
5. Documenter une décision explicite : **abandon / recherche supplémentaire / prototype expérimental par jeu**. Aucun mode recomp n'est proposé dans la release ni fusionné avec `dev/ps5-sparse-jit` sans validation technique, CI et tests console.

**Graphismes :** la recompilation seule n'améliore ni résolution, ni textures, ni éclairage, ni anticrénelage. Elle peut éventuellement libérer un budget CPU pour les fonctions graphiques déjà prévues en R06–R10 ; toute amélioration visuelle devra être développée, mesurée et validée séparément.

**Statut : À étudier.** Ne pas annoncer de gain de FPS, de compatibilité générale, de portage automatique ou d'intégration IA avant démonstration.


### Première livraison de code (25 octobre 2026)

- **R00** : synchronisation base de référence F01–F06 de `dev/ps5-sparse-jit` dans la branche laboratoire [PR #18](https://github.com/niakw/Prospero.Eden-Encore/pull/18).
- **R04** : AudioIn produit des échantillons silencieux à longueur demandée ; RomFS libère des arbres très larges sans chaîne de destruction récursive ; tests source-extracted `-O0`/`-O2` et audit de source réussis.
- **R03 shader** : nouvelle unité entière `vendor/encore-active/eden-shader/src/shader_recompiler/backend/spirv/emit_spirv_context_get_set.cpp`, sélection unique par `headless/CMakeLists.txt`, sortie NaN flottante remplacée par zéro. Pinned Eden conservé ; autres sorties non modifiées. Contrat V109, revue du registre 329 sources, tests [Feature Lab](https://github.com/niakw/Prospero.Eden-Encore/actions/runs/40239451247) verts.
- **R03 RADV intégré dans la branche feature** : extension de la séparation des commandes PS5 avant barrières et six fonctions de transferts, modification de `radv_cmd_buffer.c` et deux unités maintenues `radv_meta_buffer.c` / `radv_meta_copy.c`. `tools/install-vendored-radv.py` installe **14 sources** vérifiées, `tools/patch-radv-wsi.py --oracle` reconstruit leur contenu depuis le Mesa épinglé, contrôle de propriété et de cache via `tools/check-vendored-radv-fork.py`. GPU réel et résistance aux pertes de périphérique encore **non prouvés**.
- **Validation native** : build PS5 et prévalidation intégrale requis avant de qualifier R03/R04 ; pas de test utilisateur demandé. Aucun moteur NR/FSR FG/LDN réel ajouté dans ce lot.

### R01 — télémétrie reliée au vrai Vulkan (sans déductions trompeuses)

- `headless/frame_metrics.h` définit un compteur opt-in **par session**, remis à zéro après l'arrêt de l'ancien titre par `headless/main.cpp`, sans aucune allocation/horloge/log sur le chemin rapide désactivé.
- Le **vrai** `vulkan_renderer.cpp` publie le nombre de callbacks de composition source, vraies images mises en queue, éventuelles images générées et frames sautées ; `vulkan_present_manager.cpp` compte les retours d'API `swapchain.Present` après succès. Une image générée n'est jamais décrite comme un FPS simulé.
- `headless/performance.cpp` ajoute uniquement au reporting de 5 secondes (logs détaillés) une ligne `EDEN_R01_FRAME_METRICS` avec intervalle temporel réel et taux séparés ; **aucun benchmark synthétique n'est présenté comme jeu réel**.
- `tools/check-feature-r01-native-frame-metrics-host.py` compile en C++20/UBSan `-O0/-O2` le header réellement inclus par le renderer, vérifie l'ordre des événements, la concurrence et les remises à zéro entre titres.
- `tools/analyze-r01-frame-metrics.py --json boot-trace.txt` analyse des vraies lignes de logs et produit un JSON par session, en distinguant les FPS de callbacks des FPS queue/Present API. `tools/test-analyze-r01-frame-metrics.py` teste données pondérées, corruption, reset et l'interdiction d'inventer `actual_guest_fps`, `input_to_photon_latency` ou `gpu_render_time_ms`.
- **R01 n'est pas complet** : la vitesse réelle de simulation guest, timestamps GPU, délais bout-en-bout manette-écran, qualité temporelle, et mesure sur PS5 13.60 sont distincts et restent ouverts.
- **R03 qualification** : premier build R03 [#40240190354](https://github.com/niakw/Prospero.Eden-Encore/actions/runs/40240190354) a bloqué sur deux contrôles de provenance non actualisés (`radv-active-inputs.py` 12→14 et `check-radv-official-indirect-draw.py` ancienne équivalence). Les audits ont été mis à jour **sans désactivation**, et la comptabilité du registre V109/R24/R25/U86 réconciliée. Ne pas déclarer le build PS5 vert avant une nouvelle exécution complète.

### R06 — première abstraction de modes graphiques, **sans moteur factice**

- `extras/graphics/graphics_pipeline_policy.h` définit séparément les choix de résolution, frame generation, rendu neuronal AMD/Vulkan, textures HD et 60/120 Hz.
- Chaque choix reste **off par défaut** tant que shader/binaire Vulkan, masques HUD, motion/depth, modèle autorisé et fréquence négociée ne sont pas prouvés. Les causes de refus `resolution_reason`, `generation_reason`, `neural_reason`, `texture_reason` et `display_reason` sont indépendantes.
- `extras/graphics/test_graphics_pipeline_policy.cpp` teste avec UBSan les modes incompatibles, 30 FPS → FG **potentielle**, données temporelles, séparation UI et licence modèle ; la CI [Feature Lab](https://github.com/niakw/Prospero.Eden-Encore/actions/runs/40242290098) est verte. `runtime_qualified=false` reste obligatoire : **aucun MihawkGen, FSR temporel ou Neural AMD réellement branché par ce prototype**.
- Les retours à l'upscaling spatial ou natif, et le repli 120→60 Hz, ne doivent jamais être confondus avec un gain d'images simulées. Le vrai pont Vulkan scene/depth/motion/UI et la gestion des images/fences sont toujours à coder.

### Compatibilité des anciennes validations FC27

- Le nouveau header `headless/frame_metrics.h` exige que les harnais extrayant les fonctions Vulkan incluent également la vraie source. Les tests F03/F05 `check-fc27-f03-native-present-freshness-host.py`, `check-native-vulkan-renderer-handoff-host.py` et `check-fc27-f05-native-nvdisp-vulkan-present-chain-host.py` chargent maintenant l'en-tête réel, sans masquer les nouveaux appels.
- Le contrôle de provenance `tools/check-vendored-vulkan-fork.py` reproduit **exactement** les cinq événements du renderer et l'événement PresentManager dans la copie jetable de l'oracle Vulkan puis compare **les fichiers entiers**, sans réduire les assertions.
- Une prévalidation incomplète ou un build bloqué par ces contrôles ne prouve aucune régression de gameplay et ne clôt aucun jalon ; publication native et test PS5 séparés.

### Séquence critique et dépendances

`R00 → R01 → R03/R04/R05 → R06 → {R07,R08,R09,R10} → R19 → R20`.

En parallèle sans modifier la branche F07 : `{R11,R12,R13,R21}`, `R14`, `{R15,R16}`, `R17/R18`. R21 dépend du format des paquets/release préparé pour R20 et des capacités d'installation PS5 réellement validées ; aucune installation automatique n'est permise en l'absence de ces preuves. LDN et trophées ont des tests indépendants de la frame generation.

**Point de départ le plus rationnel** : compiler et mesurer les fixes avérés puis construire une abstraction Vulkan commune aux modules de rendu. Sans ownership clair des images/fences/swapchain, MihawkGen+FSR+NR risque de recréer les défauts de HUD et les blocages de FC27.

## Registre de recherche — IA « DLSS 5-like » sur AMD (état au 25/10/2026)

Ne pas confondre **RDNA2 PC**, **Vulkan PC** et **PS5 native**. Aucune des implémentations NR suivantes n'a été qualifiée par nous sur la PS5 13.60 ; ne pas expédier d'exécutables DLL Windows, de modèles propriétaires ou de poids extraits d'un runtime NVIDIA.

| Référence | Pourquoi | Blocage / preuve à demander | Classement |
|---|---|---|---|
| [mochizuki0323/DLSSNR-AMD](https://github.com/mochizuki0323/DLSSNR-AMD) | Réimplémentation compute Vulkan SPIR-V, sélection de petits modèles ; c'est la piste la plus proche d'un module natif | Testé publiquement sur RX 9070 XT RDNA4 et Mesa Linux, modèles obtenus séparément d'une DLL NVIDIA ; RDNA2 sans validation | **R09-A** : étude prioritaire du scheduler/compute et des licences |
| [shakhbazian/OptiScaler-RDNA2NR](https://github.com/shakhbazian/OptiScaler-RDNA2NR) | Travail GPU `gfx1030` RDNA2 et traitement détails/couleurs avant ou après upscale | RX 6900 XT PC HIP/DirectX12 ≠ PS5, prix GPU fortement sensible à résolution ; modèles non librement distribuables | **R09-B** : algorithmes/quantification RDNA2 |
| [danielblnc/DLSS-NR-on-AMD](https://github.com/danielblnc/DLSS-NR-on-AMD) | Port NR AMD incluant RDNA2 expérimental et réglages de structure/peau/teinte | HIP 7, Windows/DX12, modèles utilisateur ; code/livrables/propriété intellectuelle à auditer | **R09-C** : référence fonctionnelle, pas binaire embarqué |
| [zmodelerlover/OpenNR-ReShade](https://github.com/zmodelerlover/OpenNR-ReShade) et [kibblerz/DLSS5-Reshade-AIO](https://github.com/kibblerz/DLSS5-Reshade-AIO) | Hooks rendu, mouvement estimé et interface des effets | ReShade/injection Windows ; port PS5 nul à ce jour | **R09-D** : idées d'intégration seulement |
| [Overclockers/DLSSNR-AMD-upstream](https://github.com/Overclockers/DLSSNR-AMD-upstream) | Optimisations Vulkan et comparaison quantitative au modèle original | Bibliothèque modèle, RDNA4 uniquement validé | **R09-E** : vérification mathématique/visuelle |
| [3zwr1/AMD-NR---OptiScaler](https://github.com/3zwr1/AMD-NR---OptiScaler) | Masque personnage, profils de teinte, mise à l'échelle du modèle, réduction charge, parallélisme | Ecosystème Windows/HIP, nombreuses dépendances/licences | **R09-F** : UX, stylisation et scheduler |
| [maanHimself/OpenDLSS-NR](https://github.com/maanHimself/OpenDLSS-NR) | Topologie 71 blocs et version browser/WebGPU sans Tensor Cores | Modèle ~141 MiB, coût et droits des poids, GPU RDNA2 | **R09-G** : portabilité algorithmique |
| [bloc97/Anime4K](https://github.com/bloc97/Anime4K) | Mode netteté/ligne stylisée à faible coût et shaders portables | Favorise dessin/anime, pas reconstruction de visage photoréaliste | **R09-Lite** : solution sûre si gros NR trop lent |
| [eFMann/shadPS4-Bloodborne-DLSS-FSR](https://github.com/eFMann/shadPS4-Bloodborne-DLSS-FSR) | Vraie stratégie d'émulateur : profondeur + mouvement caméra/personnage, jitter, UI après upscale, FSR FG | Code shadPS4 PC/PS4 spécifique non drop-in et statut licence à confirmer | **R07/R08** : design d'interface |
| [mihawk-99/PS5_MihawkGen](https://github.com/mihawk-99/PS5_MihawkGen) et [Swordpdf/ProsperoEden `650306c`](https://github.com/Swordpdf/ProsperoEden/commit/650306c9fd4b309720e87b58b2e5f8311f02badc) | Petite interpolation par réseau GPU PS5 avec source, shaders, outils et tests | Vérifier mesures réelles sur 13.60, licence et compat backend | **R08-A** : cible FG prioritaire |
| [GPUOpen FidelityFX SDK](https://github.com/GPUOpen-LibrariesAndSDKs/FidelityFX-SDK) | FSR 3.1, FG et APIs publiques | Ne pas confondre AMD Redstone FSR4/ML DX12/RDNA4 et anciens chemins FSR3 compatibles PS5 ; motion/depth difficiles | **R07/R08-B** |

**NR = transformation des pixels** (matériaux/peau/éclairage) ; **textures HD = ressources GPU modifiées**, éventuellement produites par IA en amont ; **FG = interpolation d'images** ; **SR = reconstruction/résolution**. Ces fonctions sont composables, mais multiplient potentiellement la latence et le coût.

### Contrat de validation graphique

1. A/B de la **même frame source** : fidélité couleur, rendu personnage, tissus, visage, texte, HUD, textures et déformations.
2. Séries animées : stabilité temporelle, occlusions, doubles contours, entrées manette, pause/reprise, mi-temps, cache shader, changement de résolution, retour menu.
3. Chiffres séparés : `guest_fps`, `present_real_fps`, `displayed_fps`, `framegen_ms`, `neural_ms`, `gpu_frame_ms`, `input_to_photon` ou proxy clairement étiqueté, RAM/VRAM.
4. Aucune option ne peut changer la sémantique des JIT/sync/audio ou se présenter comme « 60 FPS de gameplay » si le jeu reste à 30 FPS.
5. Retour au mode normal sans perte de données si pilote ne supporte pas un mode, mémoire insuffisante, échec shader, mauvais modèle ou latence insupportable.
6. Vérifier licences **source, poids, datasets et binaires** séparément ; noms « AMD Neural Rendering » ou « Encore Neural » en interface, jamais fausse appellation DLSS NVIDIA natif.

## Bons correctifs des forks : éviter les re-cherry-picks

- **Déjà vérifiés chez Encore (ne pas recopier)** : fix vertex dynamique [`1b6ffb8`](https://github.com/Swordpdf/ProsperoEden/commit/1b6ffb887), limite 512 draws [`0dd9dd0`](https://github.com/Swordpdf/ProsperoEden/commit/0dd9dd0fd), caches pipeline atomiques [`207e77f`](https://github.com/Swordpdf/ProsperoEden/commit/207e77fe4), locks pipeline mutualisés [`737152f`](https://github.com/Swordpdf/ProsperoEden/commit/737152f6f).
- **A développer sous tests** : NaN shader `e34338d`, transferts RADV `1862764`, RomFS wide-tree `4f813a3`, AudioIn silence `01e81e1`. Les sources maintenues Encore incluent actuellement un destructeur RomFS par défaut et `NullSinkStreamImpl` côté AudioIn.
- **À auditer et non activer directement** : sparse address `1390bf5`, vitesse par jeu `23e0424`, packs/update/cheats `47cce6b`/`da39bc4`.
- **PS5SX2** : préchargement des ressources, polices/atlas et notifications trophées sont des inspirations UX, pas un code exécutable Switch transposable.

## Porte de sortie : qui fait quoi et quand on teste

**Assistant publie un paquet de preuves avant toute demande de test** :
- SHA stable + liste exacte des fichiers modifiés + état des conflits avec F01–F06 ;
- build PS5 + CI fast/full + CodeQL + tests host propres à chaque fonctionnalité ;
- modifications visuelles documentées et paramètres de rollback ;
- journal technique : correctifs validés, refusés, raisons, et **compteurs « reste à intégrer » distincts de « reste à qualifier »**.

**Utilisateur ne teste la console qu'à trois points utiles** :
1. **F07 baseline** : FC27 avec `dev/ps5-sparse-jit` code validé `cd4857c8`, enregistrer jeu/firmware/réglages, freeze/HUD/texture/frametime/input ; cela ne valide aucune feature branch.
2. **RC Graphics** : version native stabilisée de R03/R06/R07/R08/R09, A/B en conditions identiques, qualité/cadence/manette/HUD.
3. **RC fonctionnalités** : R11–R17 et R21 réunis (R21 seulement si installateur/asset release qualifiés), puis test deux instances pour LDN et trophées réels par jeux pilotes.

Pas de durée chiffrée inventée : la fin d'une phase dépend de ses **preuves** et de la disponibilité réelle des outils/hardware.

## Compteur au moment de la création de ce document

- **F01–F06 pré-console** : 6/6 prouvés sur tests host, build PS5 et sécurité GitHub sur `cd4857c8`.
- **F07 vraie session de jeu** : pas encore réalisée.
- **Branche feature** : audit en cours, `framegen_capabilities.h` (contrat de choix, pas moteur), catalogues de trophées vides + tests CI hôtes ; pas de FG/NR/FSR temporel/LDN natif intégré.
- **R00–R21** : toutes les lignes sont un **backlog**, non un 22/22 validé. Le présent document accomplit uniquement la planification/traçabilité.
