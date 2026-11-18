# Eden Encore — quoi intégrer, quoi vérifier, quoi ignorer (audit NS1/NS2)

**Édition : 18 novembre 2026 · nature : recherche / décision · aucune correction de production**

> **But.** Répondre simplement à : **faut-il intégrer cette évolution dans Encore PS5 ?** Le document compare les deux dépôts, les symptômes console et les projets upstream pour éviter les backports en double. **Une piste non validée n'est pas un bug confirmé.**
>
> **Règle de protection.** Ce rapport est rédigé sur une branche documentaire dédiée ; ne pas arrêter, relancer, repinner ni modifier le build PS5 en cours. Aucun jeu NS1/NS2 n’est déclaré corrigé par la seule présence d’un correctif dans Git.

## À lire d'abord — décision pratique

**Les couleurs sont des recommandations de travail, pas des niveaux de sévérité techniques.** Sur GitHub, les pastilles emoji donnent une lecture immédiate.

| Couleur | Décision | Ce qu'on fait |
|---|---|---|
| 🟢 **INDISPENSABLE** | Correction nécessaire pour atteindre les objectifs actuels du projet. **Rare : 5 chantiers sur 47.** | Diagnostiquer et résoudre. **Cela ne signifie pas qu'il faut obligatoirement importer le patch d'un fork.** |
| 🟠 **OPTIONNEL / NON PRIORITAIRE** | Amélioration utile, manquement partiel ou compatibilité à étendre. | À laisser au registre tant qu'un jeu ou un log ne justifie pas l'intégration. |
| 🔵 **DÉJÀ PRÉSENT / À VALIDER** | Code, équivalent ou correctif candidat déjà chez nous ; efficacité console encore inconnue. | Vérifier les sources *compilées* et le test PS5 avant d'ajouter du code. |
| 🔴 **NE PAS PORTER TEL QUEL** | Incompatible avec notre architecture, dépendance matérielle différente, duplicata inutile ou contournement fragile. | Ne pas intégrer directement ; éventuellement réutiliser l'idée ou les tests. |

### Les 5 chantiers 🟢 qui méritent réellement notre énergie

| Chantier | Pourquoi c'est indispensable | Correction exacte connue ? | Charge de travail **avec ChatGPT** |
|---|---|---|---|
| 🟢 **P01 — sortie console sans crash** | Une sortie qui provoque un SIGSEGV ou un redémarrage système n'est pas acceptable. | **Non** ; plusieurs correctifs de teardown sont déjà présents. | **M à L** : remonter le premier crash, puis patch ciblé et tests |
| 🟢 **P02 — Bananza, faute invitée PC=4** | Le démarrage NS2 ne doit pas sauter à une adresse invalide. | **Non** ; il faut identifier la première faute, pas la dernière adresse. | **M à XL** selon la couche réellement fautive |
| 🟢 **P03 — MKW, première image invitée** | Écran de chargement ≠ rendu d'un jeu NS2. | **Non** ; voie IPC/GPU/présentation encore non qualifiée. | **L à XL** si plusieurs contrats bloquent |
| 🟢 **F01 — saccades importantes FC27** | Jouabilité actuellement insuffisante malgré des optimisations source. | **Partiellement** ; compilation/cache/contention identifiés, pas le gain console. | **M à L** pour une cause ciblée |
| 🟢 **F02 — pause/HUD retardés FC27** | 5–10 s pour un menu ou un nom de joueur est un problème fonctionnel majeur. | **Non** ; file d'entrée, scheduler et publication GPU à départager. | **M à L** pour une cause ciblée |

**Attention :** 🟢 signifie « résoudre ce comportement », **pas « ajouter automatiquement une évolution upstream »**. Les correctifs déjà présents doivent d'abord être évalués sur les vrais chemins PS5.

### Ce qui ne mérite PAS un nouveau backport maintenant

| Verdict | Exemples | Pourquoi |
|---|---|---|
| 🔵 **Conserver et tester** | Host1x shim, native tiling, correction de destruction du processus, cache Vulkan statique | Déjà intégrés/équivalents ; inutile de les appliquer une seconde fois |
| 🟠 **Reporter** | ISA Cyberpunk spécifique, nouveau préchauffage shader, options UI, cache CI, extensions de compatibilité non requises par nos jeux tests | Potentiellement intéressant, mais ne justifie pas de modifier le build NS1/NS2 en qualification |
| 🔴 **Écarter le port direct** | Backend Metal et recompilation ARM64 de nxnative, budgets PS5 Pro, import entier de Lichii/Eglantine, astuces par Title ID | Non transposable tel quel, fragile ou contraire à nos contraintes PS5 |

### « Temps » de travail avec IA — méthode corrigée

L'ancienne version donnait des **journées d'ingénieur humain** (parfois plusieurs dizaines) : **ces nombres étaient inadaptés et sont retirés**. ChatGPT peut écrire, comparer et tester une modification ciblée bien plus vite qu'un développement humain manuel. Mais un patch écrit ne prouve pas qu'il compile, et un build réussi ne prouve pas qu'il fonctionne sur console.

On évalue désormais **l'ampleur concrète des actions et des boucles de validation**, pas un calendrier imaginaire :

| Charge IA | Travail typique | Volume de vérifications |
|---|---|---|
| **S — simple** | Test documentaire, assertion, petite adaptation isolée | 1 modification ciblée + contrôle positif/négatif |
| **M — modérée** | Correctif limité à quelques fichiers/ABI simples | Comparaison upstream, tests hôtes, CI et revue |
| **L — complexe** | Plusieurs propriétaires C++/GPU/mémoire ou régression transversale | Plusieurs passes source et CI, puis validation PS5 |
| **XL — structurante / inconnue** | Nouveau comportement GPU Task/Mesh, refonte mémoire ou cause encore introuvable | Investigation jusqu'à identifier un défaut précis, puis découpage en lots séparés |

**Ce qui peut prendre le plus de temps n'est pas l'édition de code par l'IA** : les builds PS5 complets, l'incertitude des bugs matériels, les artefacts de symboles et les tests sur ta console. Les charges ci-dessous sont comparatives et **n'indiquent pas un temps de livraison garanti**.

---

## 1. État de référence, sources et limites de l’exhaustivité

| Élément | Référence utilisée | Sens exact |
|---|---|---|
| Moteur | [main cd840a7689cd](https://github.com/niakw/ProsperoEden-Encore/commit/cd840a7689cdeef4e379bb34b35200be602f2f05) | Dernier HEAD contrôlé au début de cet audit ; dernier changement de registre CI |
| Build natif demandé | [moteur 902d52e78d3](https://github.com/niakw/ProsperoEden-Encore/commit/902d52e78d36e7f7b5494c1a67a79bdf5f261a4c) | Désigne explicitement le vendor ci-dessous ; ce commit **ne prouve pas** le succès du build |
| Vendor épinglé par ce build | [cd476e6e93e](https://github.com/niakw/Prospero.Eden-Encore-vendor/commit/cd476e6e93e8a786bef6260006baec134f5df71f) | Sources moteur/vendeur à qualifier en couple, non les HEAD mobiles |
| Vendor main après ce pin | [161070eedf7](https://github.com/niakw/Prospero.Eden-Encore-vendor/commit/161070eedf74b2d10f2580d7848466fd89549b8a) | Suivi sécurité picomatch ; ne pas supposer que ce SHA était utilisé par le build |
| Audit A/B de référence | [registre NS1 du 10–12/11](ENCORE_AB_NS1_MASTER_EXIT_REGISTER_2026-11-10.md) | 155/155 commits Eden **classés** à un snapshot, mais **NS2 Ampere/QMD3/H01/H05/G10 explicitement hors du périmètre** |
| Audit NS2 initial | [boot](../NS2_UPSTREAM_BOOT_GAP_AUDIT.md), [shader/texture](../NS2_SHADER_TEXTURE_UPSTREAM_AUDIT_2026-11-01.md), [nxnative](../AUDIT_INDEPENDANT_NXNATIVE_EDEN_ENCORE_NS1_NS2_2026-11-06.md) | Dossiers de recherche figés, pas une liste de correctifs encore absents |
| Preuves console | [FC27 #100](https://github.com/niakw/ProsperoEden-Encore/issues/100), [NS2 #123](https://github.com/niakw/ProsperoEden-Encore/issues/123), [sortie #97](https://github.com/niakw/ProsperoEden-Encore/issues/97), [registre R457](NS1_NS2_R457_REGRESSION_REGISTER_2026-11-18.md) | Les builds testés sont historiques : recontrôler SHA moteur, gitlink vendor, artefact et logs de chaque session |

### Méthode et ce qui n’a PAS été fait

1. Réconcilier les inventaires d’Eden, Eglantine, Lichii, nxnative, variantes PS5 et dépendances ; identifier les cas déjà présents, adaptés ou volontairement non transposés.
2. Pour les assertions déterminantes, chercher les chaînes et propriétaires maintenus dans **les deux dépôts**, pas seulement dans \`vendor/sources/eden\` immuable ; noter les flags CMake/includes dont dépend réellement la sélection.
3. Conserver la séparation **source repérée → tests hôtes → unité C++ native compilée → liaison/package → installation → jeu/console**.
4. Réviser la criticité selon les symptômes FC27/Bananza/MKW réels, et non selon la seule nouveauté d’une PR upstream.
5. **Limite matérielle :** cet audit n’exécute pas de build PS5, de jeu console ni de diff calculé de *tous* les commits/fichiers de *tous* les forks au 18 novembre. Les grands arbres upstream et les nouvelles PR après le snapshot ne peuvent donc être réputés « tous couverts ». Les chemins cités comme « propriétaires à examiner » ne sont pas tous des fichiers prouvés actifs à ce SHA.
6. **Limite historique :** les 33 « écarts source » R23, les 17 headers et les 7 lots C00–C06 comptaient des catégories **différentes**, sur un ancien couple de SHA. Leur nombre **ne doit pas être additionné** aux lignes ci-dessous, ni repris comme nombre actuel de bugs.

### Légende technique des preuves

Ces lettres **ne sont pas les couleurs** : M = limitation de source constatée ; Q = comportement à qualifier ; I = déjà intégré ; E = équivalent possible ; N = non transposable. Une entrée classée **I/Q** demande des tests, pas un second import. Le code 🟢/🟠/🔵/🔴 ci-dessus est la **décision de priorité**.

**Charge IA S / M / L / XL :** voir la grille en tête de document. On ne convertit plus les lignes en jours d'ingénierie humaine.

## 2. Vue d’ensemble / décisions rapides

| Groupe | Diagnostic raisonnable au snapshot | Ce qu’il ne faut pas faire |
|---|---|---|
| P0 NS1 + NS2 | Durée de vie kernel/process, black screens, RAM invitée, GPU submit et première image sont **en cours de qualification**, malgré plusieurs corrections déjà dans vendor | Porter de nouveaux patchs sans reproduire un défaut dans le chemin shipping |
| NS2 GPU/shaders | QMD3, GPU session, Ampere, NVN/Host1x et ASTC ont des propriétaires ; *certaines formes* et transitions restent incomplètes ou non validées | Déclarer « NS2 GPU absent » ou copier tout le backend Lichii |
| FC27 P1 | Saccades début match, HUD/Options retardés, textes/vidéo/textures ont des symptômes documentés ; la cause peut différer par scène | Affirmer qu’un gain hôte de scheduler prouve le FPS console |
| UI / médias P2 | Plusieurs écarts remontés portent sur le launcher (jaquettes, langues, overlay, réglages) et non sur le GPU invité | Tout traiter comme un bug de shader |
| Build/CI/sécurité P3 | Outillage réinstallé, cache et 5 alertes picomatch déclarées ; qualité des contrôles source à maintenir | « Corriger » en supprimant les vérifications ou en modifiant les snapshots épinglés |

## 2 bis. Catalogue NS2 machine-readable : six capacités « non implémentées » et quatre statuts upstream périmés

La source actuelle [\`NS2_PS5_COMPATIBILITY_CATALOG.json\`](NS2_PS5_COMPATIBILITY_CATALOG.json) (\`schema_version=2\`) définit **25 capacités**, dont **19 \`implemented=true\` et 6 \`implemented=false\`**. Son [contrôle](../../tools/ns2/check_ns2_ps5_compatibility_catalog.py) exige des propriétaires source/chaînes pour les capacités \`true\` : **ce booléen ne signifie ni succès de compilation PS5 ni compatibilité du jeu**. MKW et Bananza n’exigent que des capacités classées \`true\` dans le catalogue, **alors que la première image MKW et le démarrage Bananza restent des incidents ouverts**.

| ID du catalogue (\`false\`) | État upstream réellement vérifié le 18/11 | Transposition PS5 | Effort si écart shipping démontré | Décision |
|---|---|---|---:|---|
| \`gamefile_shader_warm_extract\` | Références Lichii \`shader_warm_builder\`, \`shader_archives\`, \`warm_records\` ; registre local uniquement statique | **Moyenne** : importer le mécanisme, pas les shaders du jeu ou le cache driver | **L (charge IA)** | Comparer \`FileEnvironment\`, format des clés, annulabilité et budget avant implémentation |
| \`shared_store_warp_order\` | [Lichii #2082](https://github.com/zortos293/Lichii/pull/2082) **ouverte**, tête \`5fcc5329\` | **Faible/moyenne** : ordre mémoire entre lanes, SPIR-V et barrières GPU | **L (charge IA)** | Candidat non fusionné : tests sémantiques et driver PS5 avant toute adoption |
| \`nvn2_root_tables_1_7\` | [Lichii #2089](https://github.com/zortos293/Lichii/pull/2089) **fusionnée le 17/11** (\`f9e03df9\`) | **Moyenne** : root table banque 17 / constantes 25–31, ABI CBUF native | **L (charge IA)** | Source amont devenue stable, mais **pas preuve d’absence locale** ; comparer les banques sélectionnées |
| \`tld_ll_txq_uniform_handle\` | [Lichii #2090](https://github.com/zortos293/Lichii/pull/2090) **fusionnée le 17/11** (\`04593ac9\`) | **Moyenne** : descripteur et lowering TLD.B.LL/TXQ | **M (charge IA)** | Vérifier modes supportés et tests de formats/handle avant port |
| \`surface_register_handle_ops\` | [Lichii #2093](https://github.com/zortos293/Lichii/pull/2093) **fusionnée le 17/11** (\`1a12decc\`) | **Moyenne/faible** : SUATOM/SURED/SULD/SUST, mémoire GPU/atomiques | **L (charge IA)** | Sémantique d’accès, bornes et durée de vie des surfaces à qualifier |
| \`ampere_ushf_redux_strong_gpu\` | [Lichii #2094](https://github.com/zortos293/Lichii/pull/2094) **fusionnée le 17/11** (\`187a90bf\`) | **Moyenne/faible** : USHF, REDUX et ordre fort LDG sur PS5 | **L (charge IA)** | Tests vérité ISA + mémoire/cohérence ; aucun NOP approximatif |

**Écart documentaire concret :** les quatre entrées Cyberpunk ci-dessus sont toujours décrites comme « Open Cyberpunk candidate » dans le JSON de référence alors que les PR upstream sont fusionnées depuis le 17/11. **Le statut local \`implemented=false\` reste valide tant qu’on n’a pas prouvé l’équivalent ou l’intégration dans notre build ; seul le statut de la PR upstream est périmé.** Il faudra corriger le *texte* du catalogue à une étape documentaire dédiée, sans basculer \`implemented\` à \`true\` sans sources et tests.

Les 19 entrées \`true\` comprennent notamment CPU6, backing sparse, GMMU 4 KiB, QMD3, 32 storage buffers, mapping 49 bits, pont ASTC et inventaire statique des shaders. Elles prouvent **des témoins de source** ; leur exactitude runtime et leur suffisance pour un titre restent à démontrer. Les profils supplémentaires (Orbitals/Cyberpunk/Xenoblade) présents dans le JSON sont des **fixtures de compatibilité**, pas des tests console Encore.

**Conséquence sur l’estimation :** ne pas additionner ces six lignes au coût G01–G14 lorsque les causes se recouvrent (warm-up G10, ISA G01/G02/G04, mémoire G05/G06). Les candidats fusionnés ne sont pas automatiquement P0 pour les jeux actuellement testés : examiner d’abord les signatures et les shaders réellement rencontrés.

## 3. Matrice P0 — démarrage, vie des objets, mémoire et services

| ID / état | Écart potentiel, source/raison, preuve | Adaptabilité PS5 / risque NS1 | Charge IA | Acceptation indispensable |
|---|---|---|---|---|
| 🔵 **P00 · I** | **3 échecs de \`Core::System::Load\`** : le vendor sélectionné possède désormais 3 \`process.reset(); ShutdownMainProcess();\` dans \`encore-active/eden-core/src/core/core_native.cpp\`, \`core_standard.cpp\` et \`ns2-runtime/process/core/core.cpp\` ; voir [Lichii #1932](https://github.com/zortos293/Lichii/pull/1932). | **Forte**, mais invariant commun NS1/NS2 ; ne jamais supprimer le 3e guard. | S (charge IA) validation | Tester les trois retours en erreur avec destruction avant kernel, source native et console sur arrêt |
| 🟢 **P01 · Q** | **Crash natif de sortie / bouton Cercle / CE-108262-9** : [#97](https://github.com/niakw/ProsperoEden-Encore/issues/97). Correctifs Lichii #1952 (cheat VM), #1957 (thread) et #1932 (general_channel) sont intégrés ou équivalents ; crash exact Encore non confirmé résolu. | **Moyenne** : ordonnancement GPU, JIT, services, restarter, mémoire et ABI PS5. | L (charge IA) si la pile confirme la même cause ; XL (charge IA) si distincte | ELF et \`link.map\` du SHA installé, sortie après NS1/NS2, absence de redémarrage système |
| 🟢 **P02 · Q** | **Bananza PC=0x4, LR=0, pile inattendue**. L’issue [#123](https://github.com/niakw/ProsperoEden-Encore/issues/123) précise que certaines traces MKW avaient **un préfixe Bananza** : ne pas attribuer par erreur le même PC4 aux deux jeux. | **Moyenne/faible** : guest A64, NPDM/ExeFS, SVC, mapping main stack, branche invitée. | L (charge IA) selon le premier événement fautif | Relier le **premier** accès/retour erroné au vrai NSO + build ID, test négatif hôte, sortie d’erreur contrôlée |
| 🟢 **P03 · Q** | **MKW reste sans première image invitée** sur plusieurs baselines : GPU/IPC progress et \`guest_frame_handoff\` à requalifier ; ne pas confondre chargeur OpenGL, écran de chargement et frame invitée. | **Moyenne à faible** : nécessite croiser VI2, NVDRV, TSG, GPFIFO, GMMU, QMD3, surfaces Vulkan. | XL (charge IA) *si une seule cause* ; plusieurs causes peuvent s’additionner | Une vraie frame MKW identifiée dans le journal et affichée sur PS5 ; pas un simple present de chargement |
| 🔵 **P04 · I/Q** | **Backing sparse et GPU native worker 214/216** déjà partiellement implémentés ; la cohérence VA 40 bits, slot/FD, page group, release et GMMU reste à prouver en PS5. Rapports [NS2 boot](../NS2_UPSTREAM_BOOT_GAP_AUDIT.md) et [mémoire 17/11](NS2_PS5_MEMORY_SHADER_REFERENCE_AND_MINIMAL_CONSOLE_GATE_2026-11-17.md). | **Moyenne/faible** : mémoire virtuelle/physique PS5 diffère d’un PC, attention à NS1. | L (charge IA) pour un écart ciblé ; XL (charge IA) si refonte | Transactions réversibles (échec/rollback), pas de mapping détruit encore utilisé par GPU, budgets matériels mesurés |
| 🔵 **P05 · Q** | **Mémoire invitée NS2 12 GiB / heap/JIT/sparse VA** : des guards et restauration du profil NS1 ont été ajoutés, mais épuisement backing vu historiquement. Ne pas importer un allocateur desktop ni considérer 12 GiB « réellement disponibles ». | **Moyenne/faible** ; risque élevé de famine RADV/FFmpeg et d’effet sur FC27 NS1. | L (charge IA) | Comptabilité VA/PA distincte, plus grand bloc libre, restauration NS1, échecs d’allocation sans corruption |
| 🔵 **P06 · I/Q** | **Host1x syncpoint shim + tiling natif shipping** : vendor [#185](https://github.com/niakw/Prospero.Eden-Encore-vendor/pull/185) et [#187](https://github.com/niakw/Prospero.Eden-Encore-vendor/pull/187) fusionnées ; la API \`SetNativeSyncpointShim\` et son type concret sont présents. Le problème précédent était le **mauvais header sélectionné**, pas l’absence totale de code. | **Forte** pour revue ABI, **moyenne** en runtime ; protéger NS1/Maxwell par défaut. | S (charge IA) qualification, M (charge IA) si parcours ABI défaillant | Vraies unités C++ natives, mapping NVDRV shim, valeurs syncpoints et rendu NS2 sur console |
| 🔵 **P07 · I/Q** | **VI2 cmd 31/32, vblank et cmd 229** : des implémentations ont été étudiées/intégrées, mais les fences et le handoff image restent à confirmer. [Registre boot NS2](../NS2_UPSTREAM_BOOT_GAP_AUDIT.md). | **Moyenne** ; rythmes vidéo PS5, événements noyau, présentateur. | L (charge IA) | Vblank invité réellement déclenché, fence signalé à la bonne image, pas de faux progrès |
| 🔵 **P08 · Q** | **KProcess/AM/NPDM et ROM décomposée** : sélection des ressources exécutées (base + update + DLC) et fermeture sur échec doivent être cohérentes ; des correctifs vendor et registres existent. Réf. [audit NUP/ExeFS](../NS2_EGLANTINE_NX2_NUP_REVIEW_2026-11-03.md). | **Moyenne** ; risque de charger mauvais NSO avec bonne jaquette. | L (charge IA) | Identité NPDM/NSO/ExeFS/RomFS/Update et Title ID contrôlée avant entrée guest, rejets négatifs |
| 🟠 **P09 · Q** | **A64 JIT / RETAA/RETAB/LSE / page sizes / SVC GetInfo** : des backports spécifiques sont maintenus, mais impossible de déduire l’exactitude guest d’une source seule. | **Moyenne** ; partager uniquement les parties A64/Horizon compatibles, jamais substituer Dynarmic entier. | M (charge IA) par famille de fonctions manquantes | Exécuter instructions et IPC réels avec états/erreurs attendus, 6 cœurs et régressions NS1 |
| 🔵 **P10 · Q** | **Arrêt et reprise après erreur de chargement, threads GPU et événements** : plusieurs corrections récentes #1932/#1952/#1957, mais la régression de stop watchdog et les sorties longues restent sujettes à test. | **Moyenne**, transversal. | M (charge IA) | Multiple starts/stops, échec loader, retour launcher, pas de deadlock/objets restants |
| 🔵 **P11 · I/Q** | **Régression écran noir GL→Vulkan avant \`guest_run_begin\`**, issue [#263](https://github.com/niakw/ProsperoEden-Encore/issues/263) close après correction du fragment HUD monolithique. Ne pas la confondre avec le blocage *après* démarrage guest NS2. | **Forte** pour maintenir le patch ; toujours à tester en nouvelle combinaison de sources/atlas. | S (charge IA) non-régression | Loading → guest-run FC27 et MKW, création device/swapchain/preload sans écran noir infini |

## 4. Matrice P1 — GPU Ampere/Maxwell, shaders, textures, RADV et FPS

| ID / état | Écart et propriétaire candidat | Adaptabilité PS5 / risque | Charge IA | Preuve requise avant import |
|---|---|---|---|---|
| 🟠 **G01 · M/Q** | **\`ISBEWR\` task/mesh** : le vendor a un opcode *reconnu* dans \`encore-active/ns2-runtime/ampere/shader_recompiler/frontend/ampere/probe.cpp\`, mais reconnaissance de bits ≠ lowering exécuté pour toutes régions/SKEW/largeurs. | **Faible/moyenne** : modèle NVN2 Ampere et IR/SPIR-V vers Vulkan/RADV RDNA2. | **XL (charge IA)** | Capture autorisée synthétique opcode/operands → IR → SPIR-V validé → sorties mesh comparées |
| 🟠 **G02 · M/Q** | **\`CSMTEST\`** : le probe admet uniquement forme « predicate-only » sans sortie observable ; autres modes déclarés non supportés jusqu’à authentification de l’état shading. | **Moyenne/faible** : conditions de prédicat et sémantique shader. | **L (charge IA)** | Tests vérité prédicats + mode état + pas de faux NOP si écriture guest observable |
| 🟠 **G03 · Q** | **Task/Mesh et fallback compute** : l’ISA ou la génération SPIR-V n’implique pas que le driver PS5 supporte la feature Vulkan correspondante ; voir [Lichii #569](https://github.com/zortos293/Lichii/pull/569) et [#1801](https://github.com/zortos293/Lichii/issues/1801). | **Faible**, architecture sensible : traduire en compute selon capacités réelles et limites RADV. | **XL (charge IA)** | Capability query réelle, compilations mesurées, barrières/indirects, test rendu MKW/Bananza sur console |
| 🟠 **G04 · Q** | **LEPC/ATEXIT, geometry OUT, branches dynamiques, écriture mémoire physique** : quelques formes ont été étudiées ; leur exhaustivité et le chemin de production restent incertains. [Audit shader](../NS2_SHADER_TEXTURE_UPSTREAM_AUDIT_2026-11-01.md). | **Moyenne/faible** | **XL (charge IA)** | Jeux de fixtures sémantiques, environnement guest vérifié, intégration par opcode |
| 🔵 **G05 · I/Q** | **QMD3 Compute / MME RAM partagée 3D+Compute** : sources sélectionnées et corrections de RAM de canal existent ; confirmer ordonnancement, cross-channel, descripteurs, rejets/release. | **Moyenne**, fort risque concurrence. | **L (charge IA)** si dysfonctionnement confirmé | Vraies commandes QMD3, file de soumission, fin de dispatch et ressources libérées même sur erreur |
| 🔵 **G06 · Q** | **32 storage buffers, Generic31 XYZW, arrays de texture buffers et ressources QMD3** : des headers/adaptations expérimentales existent, mais ne prouvent pas l’exposition au chemin shipping. | **Moyenne** ; ABI CMake + SPIR-V et descripteurs RADV. | **L (charge IA)** | Établir propriétaire sélectionné par CDB, tests d'index 0–31, validation des stages |
| 🔵 **G07 · I/Q** | **Tiling natif, blitter Fermi2D, I2M, GOB, formats ASTC/BC7, array/mip/sparse** : voir [Lichii #2042](https://github.com/zortos293/Lichii/issues/2042), [#2121](https://github.com/zortos293/Lichii/pull/2121). Le chemin blitter a été backporté, mais textures correctes non prouvées. | **Moyenne/faible**, coût élevé si copies GPU/CPU et residency divergent. | **L (charge IA)** par sous-cas | Roundtrip layouts, couches/mips, invalidation écriture GPU, aucune texture sans backing validé |
| 🟠 **G08 · M/Q** | **Sémaphore GPU \`acquire_timeout\`** : TODO observé dans les propriétaires maintenus \`encore-active/eden-core/src/video_core/engines/puller.cpp\` et \`puller_dev.cpp\` ainsi que source Eden ; ne prouve pas que le blocage MKW en résulte. | **Moyenne** ; éviter un timeout inventé sans sémantique matérielle. | **M (charge IA)** | Tests timeout/égalité/signal différé, FIFO et GPU progress, vraies traces de wait |
| 🔵 **G09 · Q** | **Persistance de cache pipeline Vulkan** : [Lichii #2100](https://github.com/zortos293/Lichii/pull/2100) déjà adapté (écriture \`.tmp\` + rename, fallback cache vide). Caches drivers, invalidation version/context et permissions PS5 restent non prouvés. | **Forte** pour contrôle de fichier, moyenne pour driver. | **S (charge IA)** qualification, **L (charge IA)** si cache systématiquement vide | Hash/versions exactes, corruption interrompue, relance froide/chaude, aucun hit fictif |
| 🟠 **G10 · Q** | **Warm-up shaders compute/graphics, cache négatif et eviction** : FC27 \`queued=0 completed=0\` à certains builds ; upstream [Lichii #747](https://github.com/zortos293/Lichii/issues/747) et [#1217](https://github.com/zortos293/Lichii/issues/1217) montrent des reconstructions et des stalls d’autres environnements. Ne pas précharger shaders propriétaires dans le dépôt. | **Moyenne**, coûts CPU/VRAM/latence, formats cache par driver. | **XL (charge IA)** | Cold/warm **même version du jeu**, histogrammes jobs/progress, temps frame, cache persistant et invalidation correcte |
| 🔵 **G11 · Q** | **GPU invalidation BufferCache/TextureCache** : FC27 HUD/textures retardés et rendu corrompu peuvent provenir d'une publication tardive, d'un ring GPU, de vues remappées ou de clocks ; plusieurs correctifs source ont déjà été adaptés. | **Moyenne/faible**, concurrence multi-thread ; ne pas inférer cause unique. | **L (charge IA)** | Trace corrélée guest-write → invalidation → upload → draw → present, tests négatifs UAF |
| 🔵 **G12 · Q** | **RADV/Mesa PS5 (meshes, depth, indirect draw, barriers, DMA)** : les snapshots vendor et overrides sont distincts d’un Mesa/Linux récent. Ne pas importer un commit RADV PC sans différentiel exact des TUs copiés. | **Faible à moyenne**, driver/ABI/SDK et firmware. | **L (charge IA)** par correctif | Meson CDB, source byte receipt, pipeline/spv valide, pas de GPU hang PS5 |
| 🔴 **G13 · N/E** | **nxnative backend Metal / recompilation NSO Apple Silicon** : utile pour capacités NVN2, formes de shader et diagnostics de jeu, **pas** un moteur Vulkan PS5 transposable. [Comparatif du 6/11](../AUDIT_INDEPENDANT_NXNATIVE_EDEN_ENCORE_NS1_NS2_2026-11-06.md). | **Très faible** pour le code, **moyenne** pour tests d’invariants. | S (charge IA) audit ciblé ; port direct non recommandé | Réutiliser uniquement preuves de contrats GPU/IPC/fichiers, pas de binaires ou configs par TitleID |
| 🔴 **G14 · N/E** | **Budgets PS5 Pro, AMD PC, swap SSD, driver Metal ou shader cache Vulkan externes** : les chiffres ne sont pas un budget de PS5 standard FW 13.60. | **Faible** | S (charge IA) mesure locale ; aucun port direct | Mesure mémoire propre : heap, largest block, driver, VRAM réelle sans double comptage |

## 5. Matrice P1 NS1/FC27, médias, affichage et latency

| ID / état | Symptôme / candidat | Adaptabilité / risques | Charge IA indicative | Preuve minimale |
|---|---|---|---|---|
| 🟢 **F01 · Q** | **Saccades au début des matches FC27 après cache vidé**, puis amélioration partielle. Shader miss, pipeline waits et contention de caches ont été mesurés ; le même frame peut avoir plusieurs causes. [#100](https://github.com/niakw/ProsperoEden-Encore/issues/100). | **Moyenne** ; cache, GPU jobs, CPU/JIT et RADV sur PS5. | **L (charge IA)** après identification du plus gros responsable | Replay de 415 fenêtres + capture froide/chaude comparables, percentiles frametime et non seulement FPS moyen |
| 🟢 **F02 · Q** | **Options/pause 5–10 s, joueur HUD actualisé plus de 10 s après** : traiter la file de demandes, puis publication texture/texte et priorité GPU ; ne pas assimiler à un bug d'entrée DualSense sans preuve. | **Moyenne**, scheduler/HLE/UI invité ; faux gains possibles si on saute des frames. | **L (charge IA)** | Horodatage bouton → guest sample → réponse menu → draw → present ; absence de requêtes perdues |
| 🔵 **F03 · Q** | **Texte HUD isolé/manquant, numéros/accents et noms de maillots** : glyphes, atlas, rejet de draw, invalidation ou alias texture, MSAA, format de sortie. | **Moyenne** ; le lancement moderne de l’UI Encore est séparé du HUD invité. | **L (charge IA)** | Comparaison contrôlée AA off/x4, cache froid/chaud, contenu atlas et pixels de rendu réellement identifiables |
| 🟠 **F04 · Q** | **Textures/vêtements/corps/alpha/visuels corrompus** : regarder upload partiel, layout, descripteurs, cache, shaders et fences avant de modifier les textures elles-mêmes. | **Moyenne/faible** | **L (charge IA)** | Captures scène + journaux d'invalidation et ownership au même SHA |
| 🔵 **F05 · I/Q** | **Intro vidéo noire/FFmpeg EAGAIN, NVDEC/VIC, EOS** : certaines sessions plus récentes ont une intro visible, mais cela n’établit pas l’absence de bug au cold start ou pour tous les codecs. | **Moyenne** ; FFmpeg natif, copie YUV, surfaces du présentateur. | **L (charge IA)** | Frames décodées, séquence timestamps, surfaces réellement présentées, audio-sync, sorties/seek et EOS |
| 🟠 **F06 · Q** | **30 FPS vs pacing 60 Hz** : un jeu peut être limité à 30 FPS et néanmoins avoir une cadence incohérente. | **Moyenne** ; présentation VideoOut, guest timing et GPU queue. | **M (charge IA)** | Histogrammes 33,3 ms et 16,7 ms selon les modes, missed frames, test sans déverrouiller les FPS |
| 🔵 **F07 · I/Q** | **R457 worker callbacks first-use** : tests A/B de code historique et maintenu ont montré une amélioration du mécanisme sur hôte, pas des gains FC27 console. Voir [registre du 18/11](NS1_NS2_R457_REGRESSION_REGISTER_2026-11-18.md). | **Forte** pour test, moyenne pour bénéfice runtime. | **S (charge IA)** qualification, puis ciblage F01/F02 si échec | Mesures avant/après, 1 seul SHA candidat en console |
| 🔵 **F08 · Q** | **Nettoyage/sortie après freeze** : la latence de l’arrêt et le restarter peuvent être une seconde panne distincte des saccades. | **Moyenne** | **M (charge IA)** | Sortie console normale, rejet du double stop, absence de CE-108262-9 |

## 6. Matrice P2/P3 — launcher, UX, outils, dépendances et sécurité

| ID / état | Besoin / preuve historique | Adaptabilité | Charge IA indicative (hors retours console) | Qualification |
|---|---|---|---|---|
| 🟠 **U01 · Q** | Icônes NS2 carrées, ExeFS, chargement tardif seulement au focus, jaquette recto/verso MKW, images coupées ; historique [réconciliation R457](PS5_R457_FULL_RECONCILIATION_2026-11-14.md). | **Forte** | **M (charge IA)** | Vérifier ordre de sélection images et cache, test multi-tailles et première ouverture |
| 🟠 **U02 · Q** | Accueil non vide, 5 vignettes min, dernier joué, scan de bibliothèque au démarrage. | **Forte** | **M (charge IA)** | Timeline scan sans blocage UI, tests bibliothèque vide/non vide et ordre déterministe |
| 🟠 **U03 · Q** | Fr-FR vs \`fr\`, 31 langues, Montserrat et fallback glyphes, traductions de catégories/options. | **Forte/moyenne** | **M (charge IA)** | Tests de couverture Unicode et locales réelles (RTL/CJK/diacritiques), pas seulement PO |
| 🟠 **U04 · Q** | Overlay, textes verticalement désaxés, polices, contraste light, opacité 100 %, pages et raccourcis L1/R1. | **Forte** | **M (charge IA)** | Snapshots et véritables captures PS5 720/1080/1440, focus/contraste/états |
| 🟠 **U05 · Q** | Options vidéo AA/MSAA x4/x8 et textes explicatifs, options rapides ≠ générales, sous-menu triangle. | **Forte/moyenne** | **M (charge IA)** | Matrice des valeurs supportées par backend ; UI cohérente sans activer mode inexistant |
| 🟠 **U06 · Q** | Fond d’écran, captures PS5 système et de l’app, JXR/WebP, préférence utilisateur et recadrage, titres/sources. | **Forte/moyenne** | **M (charge IA)** | Provenance et formats permis, désérialisation robuste, tri, décodage sécurisé et tailles |
| 🟠 **U07 · Q** | Journalisation avancée/standard anonymisée, événement crash/sortie et envoi contrôlé ; aucune télémétrie ne doit être activée implicitement. | **Moyenne** | **L (charge IA)** | Opt-in, pas de secrets/données de jeu, taille bornée, consentement, sortie sûre sans réseau |
| 🟠 **T01 · Q** | **Installations d’outils longues et répétées** : \`apt-get\`/Meson avant restauration du cache principal. Voir [issue #274](https://github.com/niakw/ProsperoEden-Encore/issues/274). | **Forte/moyenne** | **M (charge IA)** | Image builder épinglée par digest, cache froid/chaud, mesure avant/après, retrait simple |
| 🔵 **T02 · Q** | **CI/sondes de source fragiles aux backports** : changement de forme déjà corrigée qui invalide un count de texte. Exemple [\`check-load-failure.py\`](../../tools/check-load-failure.py), désormais trois chemins par Lichii #1932. | **Forte** | **S (charge IA)** par gate | Test de mutation positive/négative et compile de véritables TU ; ne pas supprimer de sécurité |
| 🟠 **T03 · Q** | Ancien audit R18 : provenance des dépendances, archives, composants SDK et notices ; certaines vérifications bloquées par origins indisponibles. | **Moyenne** | **L (charge IA)** | SHA256/SBOM/ABI/licences au pin installé, sans repin aveugle |
| 🟠 **T04 · M (sécurité docs)** | **5 alertes vendor picomatch** (#569/#567/#566/#565/#564) : snapshot Boost documentation Antora ; [note vendor](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/main/docs/BOOST_PICOMATCH_CVE_2026_112366_2026_11_18.md) = **inventaire, pas correctif**. | **Forte** pour confinement, version corrigée upstream requise pour suppression du risque. | **S (charge IA)** lorsque solution amont publiée ; attente non chiffrable | Update ciblé + hash/lockfiles + analyses, aucune suppression trompeuse des alertes |
| 🟠 **T05 · Q** | Warnings LLVM/Meson/FFmpeg/SPIR-V, symboles et archives FTP/PFS, CodeQL/dependabot moteur/vendor. | **Forte/moyenne** | **M (charge IA)** par catégorie | Vérifier jobs, package installable, symbole lié à SHA et absence de regressions |
| 🟠 **T06 · Q** | Branches/PR/issues historiques sur les **deux** dépôts, source immuable vs overlays, audit de \`compile_commands.json\` et gitlink exact. | **Forte** | **M (charge IA)** | PR merger uniquement avec preuve de sélection native, ne pas fermer incident console sur CI verte |

## 7. Exclusions, équivalences et ports à ne PAS recommander en boucle

| Référence / prétendu « manque » | Position actuelle | Justification / décision |
|---|---|---|
| **Shim Host1x manquant partout** | **Faux** | Présent dans vendor shipping après #185 ; le problème ancien concernait le choix de header |
| **Native tiling absent partout** | **Faux/partiel** | Des propriétaires I2M/Fermi2D et un flag NS2 sont présents ; validation visuelle reste due |
| **QMD3 entièrement absent** | **Faux** | Ressources et dispatch existent ; exactitude de chaque sous-commande et résultat à tester |
| **VI2 31/32 totalement absent** | **Historique, à retirer de liste de port** | Implémentation étudiée/ajoutée ; vérifier son exécution sur PS5 avant correction |
| **Correctif cache statique Vulkan Lichii #2100** | **Déjà backporté** | Audit de comportement/cache seulement |
| **Retour \`process.reset()\` avant kernel** | **Déjà backporté** | Trois chemins ; corriger le *test* historique et conserver la sécurité |
| **Patch complet Eglantine / Lichii / Eden-NS2** | **Non** | Branches, ABI, code original maintenu, historique des changements PS5 et licences différents |
| **nxnative : recompilation ARM64 native Apple et Metal** | **Non** | Emprunter tables d’invariants, tests, diagnostics, jamais copier backend/mémoire entière |
| **Budgets PS5 Pro / AMD desktop / RX/MoltenVK** | **Non** | Mesurer PS5 standard firmware 13.60 et driver propre |
| **Contournement par Title ID pour Bananza/MKW** | **Non** | Les problèmes portent sur capacités génériques invitées, pas sur un mode par jeu |
| **Sources archive R23 « 33 écarts »** | **À réconcilier avant nouvelle liste** | Nombre d’actions candidates à l’ancien SHA, pas 33 bugs encore présents aujourd’hui |
| **Open upstream PR non fusionnée** | **Aucune admission automatique** | Vérifier status, retour des testeurs, transposition, licence, et sémantique source par version |

## 8. Scénarios de travail avec ChatGPT et ordre de priorité

On ne présente **plus** un chiffrage de dizaines de journées de développeur. Le vrai problème est le nombre de couches à comprendre et le nombre de validations requises. Plusieurs anomalies peuvent avoir une même cause, donc **ne pas additionner** les lignes du tableau.

| Scénario | Décision | Charge IA | Facteur limitant |
|---|---|---|---|
| **Débloquer la CI de `check-load-failure.py`** | 🔵 Correction ciblée du test déjà fusionnée en [#275](https://github.com/niakw/ProsperoEden-Encore/pull/275) | **S** | Résultat final du run natif et éventuelle prochaine erreur |
| **Rendre la sortie PS5 sûre** | 🟢 Indispensable | **M → L** si le vrai crash est identifié ; **XL** si non localisé | Symbolisation de l'ELF exact et arrêt sur console |
| **Premier rendu / démarrage NS2** | 🟢 Indispensable pour MKW/Bananza | **L → XL** | Plusieurs chemins GPU, mémoire et services peuvent être nécessaires |
| **Fluidité et réponse FC27** | 🟢 Indispensable pour la qualité NS1 | **M → L** par cause isolée | Temps de frame mesuré, scénario froid/chaud reproduit |
| **Extension ISA/Task-Mesh, autres jeux** | 🟠 À différer sauf log démontrant la nécessité | **L → XL** | Compatibilité SPIR-V/RADV réelle |
| **Launcher, langues, photos, cache CI** | 🟠 Maintenance/UX | **S → M**, parfois L | Vérification finale sur l'interface PS5 |
| **Portage de Metal, PS5 Pro ou code complet d'un fork** | 🔴 Non pertinent tel quel | **Pas de chiffrage : ne pas engager le port** | Architecture différente |

**Méthode adaptée à l'IA :** rechercher le patch upstream → comparer la fonction active → produire un changement minimal → auto-tests positifs et négatifs → CI → **un test console groupé seulement si nécessaire**. Ne pas multiplier les aller-retours matériels sur chaque micro-correction.

### Ordre recommandé pour éviter 150 campagnes console

1. **Geler le couple moteur/vendor déjà demandé au build.** Fixer uniquement les contrôles obsolètes ou erreurs démontrées ; pas de nouvelle série de fonctionnalités pendant sa qualification.
2. **Faire passer les unités natives et les negative tests** des principaux chemins \`KProcess\`/Host1x/memory/shader avant tout essai matériel.
3. **Une campagne PS5 regroupée** et horodatée : retour launcher/sortie ; FC27 froid puis chaud et pause/HUD/texture ; MKW lancement et premier framebuffer ; Bananza uniquement pour discriminer le PC4 ou l’actualisation de contenu.
4. **Ouvrir une seule piste à la fois par signature** : aucun backport upstream si équivalent déjà présent ; documenter la forme d’opcode/service/ressource rejetée.
5. **Restituer les résultats dans le registre commun** : symptôme → Title ID/build ID → première anomalie log → propriétaire source *compilé* → upstream SHA/PR → patch candidat → host CI → build → PS5 → verdict. Ne fermer une issue gameplay qu’à la validation console adéquate.

## 9. Index de références vérifiées / à suivre

### Sources de notre projet
- [Registre R457 du 18 novembre](NS1_NS2_R457_REGRESSION_REGISTER_2026-11-18.md), [matrice de diagnostic mémoire/shaders](NS2_PS5_MEMORY_SHADER_REFERENCE_AND_MINIMAL_CONSOLE_GATE_2026-11-17.md), [R457 black screen](PS5_R457_2026-11-17_BLACK_SCREEN.md), [réconciliation fonctionnalités](PS5_R457_FULL_RECONCILIATION_2026-11-14.md).
- [NS1 A/B freeze](ENCORE_AB_NS1_MASTER_EXIT_REGISTER_2026-11-10.md) ; [nxnative audit](../AUDIT_INDEPENDANT_NXNATIVE_EDEN_ENCORE_NS1_NS2_2026-11-06.md) ; [NS2 boot audit](../NS2_UPSTREAM_BOOT_GAP_AUDIT.md), [shader audit](../NS2_SHADER_TEXTURE_UPSTREAM_AUDIT_2026-11-01.md).
- [Vendor PR #185](https://github.com/niakw/Prospero.Eden-Encore-vendor/pull/185), [vendor PR #187](https://github.com/niakw/Prospero.Eden-Encore-vendor/pull/187), [moteur #273](https://github.com/niakw/ProsperoEden-Encore/pull/273), [issues moteur #97](https://github.com/niakw/ProsperoEden-Encore/issues/97), [#100](https://github.com/niakw/ProsperoEden-Encore/issues/100), [#123](https://github.com/niakw/ProsperoEden-Encore/issues/123), [#263](https://github.com/niakw/ProsperoEden-Encore/issues/263), [#274](https://github.com/niakw/ProsperoEden-Encore/issues/274).

### Upstream exploitables, avec limites
- [Lichii NX2_NOTES](https://github.com/zortos293/Lichii/blob/nx2/NX2_NOTES.md), [#1932](https://github.com/zortos293/Lichii/pull/1932) (objets kernel et échec loader), [#1952](https://github.com/zortos293/Lichii/pull/1952) (cheat VM), [#1957](https://github.com/zortos293/Lichii/pull/1957) (threads), [#2042](https://github.com/zortos293/Lichii/issues/2042), [#2121](https://github.com/zortos293/Lichii/pull/2121) (tiling), [#2100](https://github.com/zortos293/Lichii/pull/2100) (cache statique).
- [Lichii #747](https://github.com/zortos293/Lichii/issues/747), [#1217](https://github.com/zortos293/Lichii/issues/1217), [#328](https://github.com/zortos293/Lichii/issues/328) (shader/prewarm), [#1801](https://github.com/zortos293/Lichii/issues/1801) et [PR #569](https://github.com/zortos293/Lichii/pull/569) (mesh/ASTC/RADV) : résultats sur d’autres appareils, **pas preuves PS5 Encore**.
- [Eglantine issues #335](https://github.com/Eglantine-Community/Eglantine/issues/335), [#350](https://github.com/Eglantine-Community/Eglantine/issues/350), [#504](https://github.com/Eglantine-Community/Eglantine/issues/504) : ExeFS/RomFS, mémoire et chargements.
- [nxnative](https://github.com/seedds/nxnative), [PS5_Lichii](https://github.com/mihawk-99/PS5_Lichii), [EglantinePS5](https://github.com/heydemoura/EglantinePS5), [Eglantine-PS5-](https://github.com/viejunerd/Eglantine-PS5-) : **comparaisons**, pas dépendances à installer directement.
- [Mesa](https://gitlab.freedesktop.org/mesa/mesa), [Vulkan](https://docs.vulkan.org/) et [SPIR-V Tools](https://github.com/KhronosGroup/SPIRV-Tools) : valider les capacités réelles PS5/RADV et compatibilité de version avant transposition.
- [CVE picomatch vendor](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/main/docs/BOOST_PICOMATCH_CVE_2026_112366_2026_11_18.md) : état **ouvert**, lié aux docs Boost, sans correctif upstream réputé livré à cette date.

## 10. Décision de clôture de **cet audit** (distincte des issues de jeu)

Cet inventaire **documentaire** est utilisable si les lignes sont classées et référencées, mais son statut demeure **non exhaustif au sens d’une preuve de parité universelle** tant qu’on n’a pas : (1) comparé byte-for-byte les ensembles de commits upstream pertinents au pin courant ; (2) relié chaque propriétaire au CDB du *dernier* build PS5 ; (3) inspecté tests et ABI exacts ; (4) confronté les fonctions au premier défaut des logs PS5. La veille upstream postérieure au snapshot crée de nouveaux candidats : **une arrivée de patch n’est pas automatiquement une lacune locale**.

**Résultat clé :** il est incorrect de traiter tous ces éléments comme autant de fonctionnalités « manquantes ». Le plus gros travail à court terme consiste à prouver **quelle partie déjà intégrée est réellement exécutée et correcte**, puis à corriger seulement les écarts établis.
