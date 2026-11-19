# Encore — audit statique transversal du code, de l'architecture et des optimisations (19 novembre 2026)

> **Mise à jour du 19 novembre — correction d'une conclusion devenue obsolète.** L'instantané de cet audit (vendor `6c38328f`) décrit une table JIT A64 PS5 de **64K** entrées. Cette variante a provoqué sur PS5 un décalage de disposition de classe entre unités de compilation portant et ne portant pas `PS5_NATIVE`, puis trois SIGSEGV au démarrage des titres. Elle a été annulée par [vendor `8e564f61`](https://github.com/niakw/Prospero.Eden-Encore-vendor/commit/8e564f61e6c8b86149ce0a0d6d2aa323a268dda6), conservée dans `67759611`. Le binaire natif R457 `4a5b8cc` [run #44538202373](https://github.com/niakw/ProsperoEden-Encore/actions/runs/44538202373) confirme en désassemblage l'allocation **16 MiB** et les constructeurs correspondants ; l'archive console `logs19111615.zip` atteint `guest_run_begin` sur FC27 et deux titres NS2 sans reproduire les SIGSEGV. Les observations **F-03 / D-02 / JIT 64K** restent des faits historiques du snapshot, pas une optimisation active ni une recommandation de réactivation. [Registre P0](PS5_R457_CC8044CE_P0_CROSS_TITLE_A64_JIT_SIGSEGV_2026-11-19.md).


> **AUDIT DOCUMENTAIRE UNIQUEMENT — aucune correction, aucun test exécuté, aucun build, aucun changement du vendor ni du binaire.**
>
> **Périmètre :** [moteur Encore](https://github.com/niakw/ProsperoEden-Encore) et [vendor Encore](https://github.com/niakw/Prospero.Eden-Encore-vendor), architecture NS1/NS2 sur PS5 firmware 13.60.
>
> **Révisions effectivement consultées :** moteur [<code>6b9763fa2170496fd316611e9a4bb28e20bb26fc</code>](https://github.com/niakw/ProsperoEden-Encore/commit/6b9763fa2170496fd316611e9a4bb28e20bb26fc) ; Gitlink <code>vendor</code> et vendor [<code>6c38328fbef33de747f5c31ea30d13541a513a4a</code>](https://github.com/niakw/Prospero.Eden-Encore-vendor/commit/6c38328fbef33de747f5c31ea30d13541a513a4a). Les sources ci-dessous utilisent des liens **épinglés**, pas le <code>main</code> mouvant.
>
> **Document parent :** [Architecture technique, composants, documentations et études](../ENCORE_TECHNICAL_ARCHITECTURE_AND_RESEARCH.md).
>
> **Objet :** offrir une visibilité globale fiable des contrats, de la structure, des candidats d'optimisation, des écarts documentaires et des preuves manquantes. Les observations sont distinctes des hypothèses, des anomalies prouvées et des gains mesurés.
>
> **Protection du chantier :** le build natif [#44520885201](https://github.com/niakw/ProsperoEden-Encore/actions/runs/44520885201) était <code>in_progress</code> au moment du relevé de CI, sur **un autre commit** (<code>cc8044ce…</code>). Ce rapport ne demande aucune relance, ne change pas son code et ne requalifie pas ce binaire. Le workflow natif possède un groupe de concurrence spécifique aux pushes *non buildables*, ainsi qu'un déclenchement explicitement limité aux sujets de commit commençant par <code>[full-build]</code>, <code>[build-only]</code> ou le marqueur de reprise autorisé. Un ajout purement documentaire au présent chemin ne demande **pas** de compilation native.

## Sommaire

1. [Méthode et limites](#1-méthode-et-limites)
2. [Synthèse de l'audit par sous-système](#2-synthèse-de-laudit-par-sous-système)
3. [Constats positifs vérifiés dans le code](#3-constats-positifs-vérifiés-dans-le-code)
4. [Écarts prouvés et cohérence des documents](#4-écarts-prouvés-et-cohérence-des-documents)
5. [Revue CPU, Dynarmic et JIT](#5-revue-cpu-dynarmic-et-jit)
6. [Revue mémoire NS1/NS2 et GPU MMU](#6-revue-mémoire-ns1ns2-et-gpu-mmu)
7. [Revue Maxwell, Ampere et shaders](#7-revue-maxwell-ampere-et-shaders)
8. [Revue Vulkan, RADV, caches et frame pacing](#8-revue-vulkan-radv-caches-et-frame-pacing)
9. [Revue HLE, threads, IPC et cycle de vie](#9-revue-hle-threads-ipc-et-cycle-de-vie)
10. [Revue audio, vidéo, launcher et logs](#10-revue-audio-vidéo-launcher-et-logs)
11. [Revue de la structure des dépôts et du build](#11-revue-de-la-structure-des-dépôts-et-du-build)
12. [Comparaison exigences officielles et études](#12-comparaison-exigences-officielles-et-études)
13. [Registre consolidé des opportunités et risques](#13-registre-consolidé-des-opportunités-et-risques)
14. [Plan de validation futur, sans action](#14-plan-de-validation-futur-sans-action)
15. [Couverture et vérifications documentaires](#15-couverture-et-vérifications-documentaires)

## 1. Méthode et limites

### 1.1 Corpus effectivement inspecté

Lecture via l'API GitHub des structures de <code>headless/</code>, <code>src/</code>, <code>docs/</code>, workflows, <code>vendor/sources/eden/src/</code>, <code>vendor/encore-active/</code>, <code>sources/ps5-mesa/src/amd/vulkan/</code> et de **fichiers représentatifs de code** dans chacune des familles majeures.

Échantillon de **sources effectivement ouvertes et parcourues** (inventaire des principaux points d'entrée, non un nombre de lignes C++ exhaustivement auditées) :

| Famille | Fichiers source ou artefacts inspectés |
|---|---|
| Native memory | <code>src/host_memory.cpp</code>, <code>src/memory_pages.cpp</code>, <code>src/ns2_sparse_guest.cpp</code>, <code>src/ns2_sparse_guest.h</code>, <code>headless/ps5_ns2_guest_backing_plan.h</code> |
| Dynarmic / JIT | <code>headless/jit-sparse-commit.h</code>, <code>vendor/encore-active/eden-core/src/dynarmic/backend/x64/reg_alloc.cpp</code>, <code>a64_emit_x64_standard.h</code> |
| GPU MMU / buffers | <code>vendor/encore-active/eden-core/src/video_core/memory_manager.cpp</code>, <code>vendor/encore-active/eden-vulkan/vk_buffer_cache_cost.cpp</code>, <code>vulkan_rasterizer.cpp</code> |
| GPU pipelines | <code>vendor/encore-active/eden-vulkan/vk_pipeline_cache_cost.cpp</code>, <code>vk_graphics_pipeline_cost.cpp</code>, <code>vulkan_device.cpp</code> |
| Ampere / NS2 | <code>vendor/encore-active/ns2-runtime/ampere/video_core/ns2_shader_spirv_compile.cpp</code>, <code>ampere/shader_recompiler/frontend/ampere/lower_to_maxwell.h</code>, <code>translation_cache.cpp</code> |
| HLE | <code>vendor/encore-active/eden-threading/src/core/hle/kernel/k_condition_variable.cpp</code>, <code>k_thread.cpp</code>, <code>vendor/encore-active/eden-core/src/core/memory_native_standard.cpp</code> |
| Média | <code>vendor/encore-active/eden-core/src/audio_core/sink/sink_stream.cpp</code>, <code>src/video_core/host1x/ffmpeg.cpp</code> |
| Diagnostics / UI | <code>headless/log_pipe.h</code>, <code>boot_trace.h</code>, <code>prosperoeden/eden_services.cpp</code>, <code>prosperoeden/pe/core/strings.cpp</code>, <code>encore_performance_policy.h</code> |
| Build / Mesa | <code>headless/CMakeLists.txt</code>, <code>headless/vulkan.cmake</code> (sélection repérée), <code>vendor/encore-active/ps5-mesa/src/util/disk_cache_os.c</code>, arborescence RADV et plusieurs workflows |
| Contrats documentaires | Architecture mère, [profil PS5 unique](ONE_NATIVE_BUILD_PROFILE_2026-11-19.md), [audit GPU NVIDIA](NVIDIA_GPU_ARCHITECTURE_REFERENCE_REGISTER_2026-11-19.md), [récente comparaison Eglantine](EGLANTINEPS5_NS2_FUNCTIONAL_UPSTREAM_PARITY_2026-11-19.md), [FC27 vendor](FC27_VENDOR_194_ENGINE_INTEGRATION_2026-11-19.md), [logs console R457](PS5_R457_2026-11-19_FC27_NS2_LAST_SESSION.md), [artefact antérieur](PS5_NATIVE_ARTIFACT_AUDIT_2026-11-19_2B0975F7.md) |

Les fichiers de 4 000 lignes comme <code>headless/CMakeLists.txt</code>, les compilateurs Mesa et le snapshot complet Eden n'ont **pas** subi une revue exhaustive ligne par ligne ; le présent audit n'a pas exécuté de recherche de couverture instrumentée, de compilateur, de benchmark ni de tests. Les chemins sélectionnés ont été **observés dans les recettes** ; il faudrait le <code>compile_commands.json</code>, le mapfile et les symboles du build correspondant pour confirmer toutes les unités intégrées.

### 1.2 Grille d'évidence

| Code | Signification | Peut-on écrire « corrigé » ? |
|---|---|---|
| **F** | Fait source constaté à SHA précis | Non, sauf pour une pure cohérence du texte source |
| **D** | Incohérence documentaire ou documentaire/source **prouvée** | Oui, pour qualifier le décalage, pas pour dire bug console |
| **H** | Hypothèse de risque ou d'optimisation à tester | Non |
| **U** | Propriété/limite provenant de l'upstream ou d'une spécification | Non |
| **P** | Résultat historique de test PS5 cité dans les anciens rapports | Seulement pour le binaire réellement testé, pas pour HEAD |
| **N/V** | Validation natif/console à refaire | Non |

**Sévérités** : P0/P1/P2/P3 signalent la conséquence *potentielle* si l'hypothèse se confirmait, **pas** la présence automatiquement avérée d'une régression.

### 1.3 Binaire historique et HEAD ne sont pas interchangeables

- Console R457 décrite dans les journaux du 19/11 : **moteur** <code>2b0975f7…</code>, **vendor** <code>9a83a6ba…</code>, [build #44423348645](https://github.com/niakw/ProsperoEden-Encore/actions/runs/44423348645).
- Instantané du présent audit : **moteur** <code>6b9763fa…</code>, **vendor** <code>6c38328f…</code>.
- Build natif en cours lors de l'inventaire : **moteur** <code>cc8044ce…</code>, vendor gitlink <code>6c38328f…</code>.

Un correctif ou une protection du vendor courant ne doit jamais être déclaré testé par les journaux d'un précédent binaire ayant embarqué un autre vendor.

## 2. Synthèse de l'audit par sous-système

| Sous-système | Structure/source | Points positifs vus | Réserve centrale | État du jugement |
|---|---|---|---|---|
| ARM/Dynarmic | Présent, fichiers distincts A32/A64 et x64 | Cache JIT, gestion d'alias, dispatch PS5 réduit | Sémantique mémoire, sélection backend et coût console non mesurés ici | F + H |
| JIT sparse | Chemin natif identifiable | Réservations RX/RW, commit 2 MiB, comptage distinct, trim borné | Quiescence et lifetime cross-thread à prouver sur console | F + H |
| NS2 sparse backing | Runtime natif et plan d'admission | Budget explicite, rollback d'allocations nouvelles | 12 GiB VA / 6 GiB budget, GPU aliases et commentaires historiques | F + D + H |
| GPU MMU | <code>MemoryManager</code> et PTE | Bounds et invalidations ordonnées visibles | Tables encore dimensionnées selon espace d'adressage | F + H |
| Maxwell NS1 | 2D, 3D, DMA, compute, host1x | Maintien des sous-moteurs et chemins distincts | Causalité FC27 HUD / pause / command ticks non close | F + P + H |
| Ampere NS2 | 23 familles NS2 + lowering | Captures, session tickets, génération cache, refus d'opcodes | Portions ISA et première image console non démontrées | F + H |
| Shader recompiler | Frontend, IR, SPIR-V/GLSL/GLASM | Validation de session et cache invalidable | Correspondance ISA/stages et fidélité visuelle | F + H |
| Vulkan pipeline | Cache, worker, async first-use | Instrumentation CPU miss et waiters, drain à la destruction | Longue chaîne de contention et coûts au premier usage | F + P + H |
| Buffer/Texture cache | Owners séparés, dirty/invalidation | Chemin de publication différée déjà sélectionnable | Ordre CPU write/GPU owner et gains FC27 à confirmer | F + P + H |
| RADV/Mesa PS5 | Sources épinglées et overrides | Séparation upstream/driver actif, disk cache | Driver réel, extensions, warnings, budget VRAM à certifier par artefact | F + H |
| Kernel/HLE | Thread, condition variable, services | Sync, waits et fermeture traités explicitement | Pause latente, exit et erreurs de réveil doivent être corrélés | F + H |
| Audio/NVDEC/FFmpeg | Sinks + décodage maintenus | Buffer guard, EAGAIN drain/retry | A/V/teardown PS5 à valider | F + H |
| Logs / diagnostic | Pipe asynchrone, rotation, boot trace | Toggle OFF/ON sans recréer le pipe, retention conçue | Preuve sur console, débit en charge, recherche du premier fault | F + H |
| Launcher / i18n | Catalogues, fallback, UI natives | Fallbacks régionaux explicites | QA des 31 langues, shaping et glyphes par écran | F + H |
| Build et qualité | CMake, catalogues, nombreux workflows | Source unique, SHA vendor, guards CI | Graphe CMake dense, historique de tests obsolètes, preuve au bon SHA | F + D + H |

**Conclusion statique provisoire** : il existe des optimisations et protections déjà codées que les audits plus anciens ne reflètent plus. Les vrais déficits de visibilité sont (a) la provenance *source sélectionnée → binaire*, (b) la correspondance *logs console → couple de SHA*, (c) la mesure *cause → effet* des optimisations et (d) les contrats d'ordre mémoire. Pas de pourcentage de conformité inventé.

## 3. Constats positifs vérifiés dans le code

### F-01 — Backing NS2 : véritable propriétaire physique et rollback

- [<code>src/ns2_sparse_guest.cpp</code> L24–L105](https://github.com/niakw/ProsperoEden-Encore/blob/6b9763fa2170496fd316611e9a4bb28e20bb26fc/src/ns2_sparse_guest.cpp#L24-L105) : admission sous mutex, <code>Plan::Begin</code>, commit réel par blocs <code>kGranule</code>, publication après staging, retrait des nouveaux blocs sur échec et abort fail-closed si ownership inconnu.
- [<code>ps5_ns2_guest_backing_plan.h</code> L14–L116](https://github.com/niakw/ProsperoEden-Encore/blob/6b9763fa2170496fd316611e9a4bb28e20bb26fc/headless/ps5_ns2_guest_backing_plan.h#L14-L116) : 2 MiB/granule, droits des leases, budget réservé avant syscalls, état staging/résident, numéro de génération.
- [<code>src/host_memory.cpp</code> L562–L599](https://github.com/niakw/ProsperoEden-Encore/blob/6b9763fa2170496fd316611e9a4bb28e20bb26fc/src/host_memory.cpp#L562-L599) : réservation virtuelle NS2 de 12 GiB, plafond de mémoire engagée de 6 GiB ; refus explicite d'une allocation dense NS2 si le propriétaire sparse est absent.

**Lecture** : conception plus robuste qu'une seule grosse allocation physique NS2. **Ce que cela ne prouve pas** : que le firmware dispose de 6 GiB allocables dans les pools attendus, que chaque alias GPU est quiescé et que MKW/ Bananza passent le boot.

### F-02 — JIT : correction de coût sans changement d'ISA

- [<code>headless/jit-sparse-commit.h</code> L17–L61](https://github.com/niakw/ProsperoEden-Encore/blob/6b9763fa2170496fd316611e9a4bb28e20bb26fc/headless/jit-sparse-commit.h#L17-L61) : clamp du précommit à la capacité réelle et calcul borné du trim.
- [<code>headless/jit-sparse-commit.h</code> L64–L118](https://github.com/niakw/ProsperoEden-Encore/blob/6b9763fa2170496fd316611e9a4bb28e20bb26fc/headless/jit-sparse-commit.h#L64-L118) : cache positif à quatre entrées, lookup évitant l'écriture TLS sur hits fréquents et invalidation par génération.
- [<code>src/memory_pages.cpp</code> L356–L374](https://github.com/niakw/ProsperoEden-Encore/blob/6b9763fa2170496fd316611e9a4bb28e20bb26fc/src/memory_pages.cpp#L356-L374) : owner verrouillé et métriques virtuelles/physiques atomiques séparées.
- [<code>src/memory_pages.cpp</code> L458–L480](https://github.com/niakw/ProsperoEden-Encore/blob/6b9763fa2170496fd316611e9a4bb28e20bb26fc/src/memory_pages.cpp#L458-L480) : snapshot léger sans prise du mutex du JIT sur la télémétrie de frame.

**Lecture** : effort réel sur l'accès à froid / chemins chauds et contrôle de propriété. **Pas de gain chiffré déductible de ces seules lignes.**

### F-03 — A64 fast dispatch : optimisation upstream déjà incorporée sur PS5

[<code>a64_emit_x64_standard.h</code> L62–L76](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/6c38328fbef33de747f5c31ea30d13541a513a4a/encore-active/eden-core/src/dynarmic/backend/x64/a64_emit_x64_standard.h#L62-L76) prévoit **64K** entrées (<code>0x10000</code>) sous <code>PS5_NATIVE</code> et **1M** pour le profil non PS5 ; <code>FastDispatchEntry</code> vaut 16 octets. C'est l'adaptation déjà envisagée par [EglantinePS5 #104](https://github.com/heydemoura/EglantinePS5/pull/104). Le code est là ; la preuve de compilation dans l'objet JIT PS5 exact et les économies résidentes réelles ne font pas partie de cet audit.

### F-04 — NS2 : capture shader liée au bon processus

[<code>ns2_shader_spirv_compile.cpp</code> L14–L50](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/6c38328fbef33de747f5c31ea30d13541a513a4a/encore-active/ns2-runtime/ampere/video_core/ns2_shader_spirv_compile.cpp#L14-L50) vérifie le ticket de session avant capture et après compilation ; l'absence de session, un stage différent de Compute ou une capture invalide produisent des statuts explicites. Les ressources de la capture QMD sont remises à zéro avant un nouvel essai et la génération de session est réévaluée.

[<code>translation_cache.cpp</code> L33–L109](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/6c38328fbef33de747f5c31ea30d13541a513a4a/encore-active/ns2-runtime/ampere/shader_recompiler/frontend/ampere/translation_cache.cpp#L33-L109) vérifie la génération après traduction coûteuse avant insertion en cache. **Positif pour la durée de vie de session ; non suffisant pour une image SPIR-V/PS5 correcte.**

### F-05 — Vulkan : coût CPU et temps de construction séparés

[<code>vk_pipeline_cache_cost.cpp</code> L100–L180](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/6c38328fbef33de747f5c31ea30d13541a513a4a/encore-active/eden-vulkan/vk_pipeline_cache_cost.cpp#L100-L180) définit des traces pour les misses CPU et des compteurs de first-use compute/graphics. [<code>vk_graphics_pipeline_cost.cpp</code> L433–L505](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/6c38328fbef33de747f5c31ea30d13541a513a4a/encore-active/eden-vulkan/vk_graphics_pipeline_cost.cpp#L433-L505) publie l'état « build terminé » même sur exception et réveille les waiters ; la sélection du pipeline nul reste un scénario à rejeter.

[<code>vk_pipeline_cache_cost.cpp</code> L793–L808](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/6c38328fbef33de747f5c31ea30d13541a513a4a/encore-active/eden-vulkan/vk_pipeline_cache_cost.cpp#L793-L808) draine explicitement les builders et écritures de cache à la destruction de <code>PipelineCache</code>. C'est une protection de lifetime, pas la preuve que tous les stops de jeux PS5 sont sans blocage.

### F-06 — FC27 : le correctif de publication différée est déjà en source

[<code>vulkan_rasterizer.cpp</code> L2425–L2513](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/6c38328fbef33de747f5c31ea30d13541a513a4a/encore-active/eden-vulkan/vulkan_rasterizer.cpp#L2425-L2513) introduit un collecteur de mises à jour sous verrou, publie une barrière d'ownership avant libération du mutex et **flush** les opérations différées après la zone critique ; fallback synchronous sur exception.

Cela rejoint la stratégie de [Lichii #1518](https://github.com/zortos293/Lichii/pull/1518) et [vendor #194](https://github.com/niakw/Prospero.Eden-Encore-vendor/pull/194). **Les 624 280 acquisitions contentieuses mesurées sur le binaire R457 précédent ne constituent pas un A/B de ce correctif.**

### F-07 — Décodage NVDEC/FFmpeg : prise en compte d'EAGAIN

[<code>ffmpeg.cpp</code> L445–L479](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/6c38328fbef33de747f5c31ea30d13541a513a4a/encore-active/eden-core/src/video_core/host1x/ffmpeg.cpp#L445-L479) comporte un cycle borné drain/retry en cas de <code>AVERROR(EAGAIN)</code>, au lieu de traiter un non-consommation du paquet comme un succès ou un échec définitif. Une capture vidéo correcte reste nécessaire pour contrôler EOS, A/V, textures et décodage.

### F-08 — Journaux : architecture asynchrone et rotation explicite

[<code>headless/log_pipe.h</code> L30–L99](https://github.com/niakw/ProsperoEden-Encore/blob/6b9763fa2170496fd316611e9a4bb28e20bb26fc/headless/log_pipe.h#L30-L99) utilise un pipe avec thread de drain et maintient le lecteur en vie quand les logs détaillés sont désactivés. [L121–L179](https://github.com/niakw/ProsperoEden-Encore/blob/6b9763fa2170496fd316611e9a4bb28e20bb26fc/headless/log_pipe.h#L121-L179) borne deux segments de logs et recycle le segment courant. [<code>boot_trace.h</code> L119–L151](https://github.com/niakw/ProsperoEden-Encore/blob/6b9763fa2170496fd316611e9a4bb28e20bb26fc/headless/boot_trace.h#L119-L151) traite quiet/resume. Le code vise la conservation de preuves et l'absence de blocage producteur ; la conservation au fil de multiples boots et la fluidité des changements OFF/ON ne sont pas confirmées ici sur PS5.

## 4. Écarts prouvés et cohérence des documents

### D-01 — **Incohérence textuelle confirmée** : sparse NS2 présenté comme « non activé »

- [<code>headless/CMakeLists.txt</code> L355–L376](https://github.com/niakw/ProsperoEden-Encore/blob/6b9763fa2170496fd316611e9a4bb28e20bb26fc/headless/CMakeLists.txt#L355-L376) : commentaire « NOT included by default / do not turn this on in production », puis <code>set(EDEN_NS2_SPARSE_BACKING OFF)</code> suivi de <code>ON</code> si <code>PS5_NATIVE AND EDEN_REVIEWED_DUAL_NPDM</code>.
- [<code>headless/CMakeLists.txt</code> L14–L17](https://github.com/niakw/ProsperoEden-Encore/blob/6b9763fa2170496fd316611e9a4bb28e20bb26fc/headless/CMakeLists.txt#L14-L17) : <code>EDEN_REVIEWED_DUAL_NPDM</code> passe lui-même à <code>ON</code> lorsque <code>PS5_NATIVE</code> est actif.
- [<code>src/ns2_sparse_guest.h</code> L7–L11](https://github.com/niakw/ProsperoEden-Encore/blob/6b9763fa2170496fd316611e9a4bb28e20bb26fc/src/ns2_sparse_guest.h#L7-L11) appelle encore ce runtime « experimental ».
- [<code>ps5_ns2_guest_backing_plan.h</code> L3–L6](https://github.com/niakw/ProsperoEden-Encore/blob/6b9763fa2170496fd316611e9a4bb28e20bb26fc/headless/ps5_ns2_guest_backing_plan.h#L3-L6) se décrit « research-only accounting model » bien que le plan soit utilisé par <code>src/ns2_sparse_guest.cpp</code>.

**Diagnostic D confirmé** : les commentaires ne reflètent plus la sélection prévue par CMake. Ne pas déduire un défaut d'exécution. **Action documentaire ultérieure possible** : clarifier « algorithme de plan vérifié séparément, backend natif présent, qualification PS5 nécessaire » sans réintroduire de flag utilisateur ni modifier une ligne exécutable.

### D-02 — Ancien audit Eglantine dépassé sur le JIT A64

Le document [comparatif Eglantine](EGLANTINEPS5_NS2_FUNCTIONAL_UPSTREAM_PARITY_2026-11-19.md) cite le <code>0x100000</code> comme restant sur Encore. **Cette affirmation était pertinente pour sa révision de référence**, mais ne s'applique plus au SHA vendor de ce rapport : [le fichier maintenu PS5 a désormais <code>0x10000</code>](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/6c38328fbef33de747f5c31ea30d13541a513a4a/encore-active/eden-core/src/dynarmic/backend/x64/a64_emit_x64_standard.h#L67-L76). Ne pas ajouter une seconde fois le patch #104 sur le JIT sans vérifier la variante réellement liée.

### D-03 — Ancien audit de l'artefact dépassé sur le define GPU worker

L'[audit de l'artefact R457 antérieur](PS5_NATIVE_ARTIFACT_AUDIT_2026-11-19_2B0975F7.md) constatait un worker NS2 présent sans son define local <code>PS5_NATIVE</code> dans le binaire <code>2b0975f7</code>. Depuis, le [CMake courant L3694–L3700](https://github.com/niakw/ProsperoEden-Encore/blob/6b9763fa2170496fd316611e9a4bb28e20bb26fc/headless/CMakeLists.txt#L3694-L3700) ajoute le define uniquement à <code>EDEN_NS2_GPU_WORKER_SOURCE</code>. Le [contrôle source](https://github.com/niakw/ProsperoEden-Encore/blob/6b9763fa2170496fd316611e9a4bb28e20bb26fc/tools/ns2/check_gpu_worker_native_guard_host.py) vérifie la forme exacte, sans extension globale de la macro à <code>core</code>.

**Diagnostic D confirmé** : ne pas reprendre tel quel « manque toujours PS5_NATIVE sur gpu_worker » pour le code courant. **Limite** : l'ELF plus ancien ne se transforme pas ; exiger de vrais strings/symbols dans le prochain artefact natif.

### D-04 — Un seul build PS5 : conserver les limitations visibles sans faux sélecteurs

[Décision de profil unique](ONE_NATIVE_BUILD_PROFILE_2026-11-19.md) : l'ancien choix Fermi2D non qualifié a été retiré du sélecteur de produit ; une variante source historique peut subsister comme oracle inactif. [<code>headless/CMakeLists.txt</code>](https://github.com/niakw/ProsperoEden-Encore/blob/6b9763fa2170496fd316611e9a4bb28e20bb26fc/headless/CMakeLists.txt) fixe les disponibilités <code>EDEN_SHARED_JIT_AVAILABLE=0</code> et <code>EDEN_JIT_COMPILE_BATCH_AVAILABLE=0</code> dans le binaire frontal.

**Principe de cohérence** : ne pas confondre terme « expérimenté par le passé » dans un commentaire, <code>_LIBCPP_ENABLE_EXPERIMENTAL</code> imposé par une API tierce, un test oracle conservé et un **véritable flag runtime/build alternatif**. L'audit doit viser des chemins de code sélectionnables, pas faire une suppression textuelle aveugle.

## 5. Revue CPU, Dynarmic et JIT

| Point | Fait source | Risque/mesure non prouvé | Référence |
|---|---|---|---|
| ISA A64/A32 | Sources Dynarmic, frontend/backends et variantes x64 séparées | Contrôles host A32/NEON, flags et atomiques sur vrais chemins | [Arm ARM](https://developer.arm.com/documentation/ddi0487/latest), [ABI AA](https://github.com/ARM-software/abi-aa) |
| Fast-dispatch PS5 | Table 64K définie sous <code>PS5_NATIVE</code> | Collision rate, memory resident/JIT et efficacité console | [Eglantine #104](https://github.com/heydemoura/EglantinePS5/pull/104) |
| Reg allocation | <code>reg_alloc.cpp</code> maintenu et ses chemins spill | Les commentaires <code>TODO</code> historiques sur spills ne prouvent pas une régression FC27 | [Dynarmic](https://github.com/merryhime/dynarmic) |
| Cache JIT | Invalidation/génération et trim par pages présents | Quiescence effective lors de fin de titre, exception et code self-modifying | [JIT architecture](../DEFERRED_JIT_QUIESCENCE_ARCHITECTURE_2026-10-17.md) |
| Mémoire ARM/x86 | Alias RX/RW et barriers | Garanties ordering guest/hôte, LL/SC, load-acquire et write release | [arXiv:2009.03846](https://arxiv.org/abs/2009.03846) |
| Cœurs CPU PS5 | Affinité et instrumentation matérielle distinctes | Débit utile, migration logique/physique, latence sans profiler | [PS5 architecture](../PS5_NATIVE_ARCHITECTURE.md) |

**Candidat P0 structurel, pas bug prouvé** : produire une matrice de quiescence pour chaque transition (stop guest, stop GPU, fin d'un process, invalidation JIT, libération RX/RW, relance même processus). Une libération de backing alors qu'un worker exécute du code traduit a une conséquence de sécurité/fiabilité plus forte qu'un simple miss de cache.

**Optimisation P1** : comparer hit/miss d'accès à la table 64K, rebuilds, temps de compilation de blocs, nombre de pages physiquement engagées et impact p99. Ne pas supposer que la diminution théorique de taille d'une table donne directement le même gain FPS.

## 6. Revue mémoire NS1/NS2 et GPU MMU

### 6.1 Admission NS2 et limite réelle

Le plafond **6 GiB de backing** est codé dans [<code>host_memory.cpp</code> L562–L577](https://github.com/niakw/ProsperoEden-Encore/blob/6b9763fa2170496fd316611e9a4bb28e20bb26fc/src/host_memory.cpp#L562-L577), pour **12 GiB d'espace virtuel invité**. Ce budget est une politique logicielle, **pas** une démonstration que les allocations système peuvent réellement atteindre 6 GiB. Le modèle explicite <code>Unmapped → Staging → Resident → Retiring</code> ; la destruction mentionne explicitement la nécessité de quiescer les alias GPU.

**H-P0** : mesurer le pic des engagements durant la création du processus, les slabs, les objets KSharedMemory, les heaps, les GPU mappings et la relance d'un deuxième titre dans le même processus. En cas de refus du <code>Plan::Begin</code>, distinguer « budget local atteint » d'une défaillance native de <code>CommitMemoryRange</code>.

### 6.2 Gestion des owners et callbacks

[<code>ns2_sparse_guest.cpp</code> L128–L150](https://github.com/niakw/ProsperoEden-Encore/blob/6b9763fa2170496fd316611e9a4bb28e20bb26fc/src/ns2_sparse_guest.cpp#L128-L150) protège le registre actif avec mutex. Le callback retourne <code>true</code> lorsqu'aucun owner n'est installé : c'est décrit [dans le header](https://github.com/niakw/ProsperoEden-Encore/blob/6b9763fa2170496fd316611e9a4bb28e20bb26fc/src/ns2_sparse_guest.h) comme un no-op NS1 attendu. **À vérifier** : aucun appel NS2 ne doit utiliser ce no-op lors d'un boot partiellement initialisé ou après la désinstallation de son owner.

[<code>memory_native_standard.cpp</code> L97–L114](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/6c38328fbef33de747f5c31ea30d13541a513a4a/encore-active/eden-core/src/core/memory_native_standard.cpp#L97-L114) admet le backing avant de publier une PTE. Les chemins particuliers slab/shared memory doivent conserver cette propriété, et leurs tests sont des preuves indépendantes, pas une couverture garantie de tous les appels.

### 6.3 GPU MMU : source encore dimensionnée selon un grand VA

[<code>MemoryManager</code> L43–L66](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/6c38328fbef33de747f5c31ea30d13541a513a4a/encore-active/eden-core/src/video_core/memory_manager.cpp#L43-L66) dimensionne <code>entries</code>, <code>big_entries</code> et <code>big_page_continuous</code> en fonction de l'espace d'adressage, avec des <code>resize</code> visibles. L'upstream [EglantinePS5 #104](https://github.com/heydemoura/EglantinePS5/pull/104) propose une variante plus sparse dans un autre arbre.

**H-P1** : mesurer volume alloué réellement resident et temps d'initialisation GMMU ; comparer l'impact d'une structure sparse contre l'overhead des lookup. Le nombre d'entrées calculées n'est pas égal au RSS réel, et le passage à un vecteur sparse a des effets possibles sur lifetime, invalidation et cache locality.

### 6.4 Allocateur / Vulkan heap

[<code>src/memory_pages.cpp</code> L65–L128](https://github.com/niakw/ProsperoEden-Encore/blob/6b9763fa2170496fd316611e9a4bb28e20bb26fc/src/memory_pages.cpp#L65-L128) expose des codes d'échec d'allocation native ; ce relevé doit être relié aux mesures de heap Vulkan, taille max contiguë et cache staging. Le bon compteur pour un « Cannot allocate memory » est **la première admission rejetée**, pas le résumé de mémoire libre plusieurs secondes plus tard.

## 7. Revue Maxwell, Ampere et shaders

### 7.1 Maxwell NS1

Sources : [engines Maxwell, Fermi2D, DMA et Kepler](https://github.com/niakw/Prospero.Eden-Encore-vendor/tree/6c38328fbef33de747f5c31ea30d13541a513a4a/sources/eden/src/video_core/engines), [shader frontend Maxwell](https://github.com/niakw/Prospero.Eden-Encore-vendor/tree/6c38328fbef33de747f5c31ea30d13541a513a4a/sources/eden/src/shader_recompiler/frontend/maxwell), [GPU overrides](https://github.com/niakw/Prospero.Eden-Encore-vendor/tree/6c38328fbef33de747f5c31ea30d13541a513a4a/encore-active/eden-gpu).

**Contrats** : exécuter chaque GPU command exactement une fois, préserver FIFO/copy ordering, respecter TIC/TSC, les dirty epochs et la disponibilité du framebuffer. Un GPU idle ne démontre pas que le guest n'attend rien. **Optimisation candidate** : mesurer l'effet des commandes DMA coalescées, des uploads buffer et des réveils GPU seulement après preuve d'ordre des ressources.

### 7.2 Ampere NS2

Le [lowerer <code>lower_to_maxwell.h</code>](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/6c38328fbef33de747f5c31ea30d13541a513a4a/encore-active/ns2-runtime/ampere/shader_recompiler/frontend/ampere/lower_to_maxwell.h) est une implémentation conséquente avec sous-formes reconnues, contraintes de modes et rejets explicites. Exemples visibles :

- <code>0x23c</code> HMMA, [lignes ~950](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/6c38328fbef33de747f5c31ea30d13541a513a4a/encore-active/ns2-runtime/ampere/shader_recompiler/frontend/ampere/lower_to_maxwell.h#L950-L980).
- <code>0x992</code> MEMBAR et scopes, [lignes ~2017](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/6c38328fbef33de747f5c31ea30d13541a513a4a/encore-active/ns2-runtime/ampere/shader_recompiler/frontend/ampere/lower_to_maxwell.h#L2017-L2030).
- <code>0x9af</code> copy-group, <code>0x91a</code> scoreboard waits, [lignes ~2755](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/6c38328fbef33de747f5c31ea30d13541a513a4a/encore-active/ns2-runtime/ampere/shader_recompiler/frontend/ampere/lower_to_maxwell.h#L2755-L2790).
- <code>0x948</code> WARPSYNC avec validation d'un contexte de reconvergence, [lignes ~4522](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/6c38328fbef33de747f5c31ea30d13541a513a4a/encore-active/ns2-runtime/ampere/shader_recompiler/frontend/ampere/lower_to_maxwell.h#L4522-L4555).

**H-P1** : le tableau ISA mentionne également la famille <code>IMMA</code> dans les audits précédents ; aucune branche <code>case 0x237</code> n'a été trouvée dans **ce lowerer consulté**. Ce constat local n'est ni un inventaire exhaustif de toute l'implémentation shader ni la preuve que MKW/Bananza exécutent cet opcode. Ne développer une traduction nouvelle qu'après capture d'une variante exacte, validation du masque de prédication, mappage lanes et résultat numérique.

### 7.3 Synchronisation shader et cache

Le cache NS2 est lié à une génération ; un <code>Clear</code> invalide la traduction en cours avant sa publication. Cette stratégie répond à un vrai invariant de lifetime, mais ne prouve pas les valeurs calculées. Respecter [SPIR-V](https://registry.khronos.org/SPIR-V/specs/unified1/SPIRV.html) et le [Vulkan Memory Model](https://docs.vulkan.org/spec/latest/appendices/memorymodel.html) pour les atomiques/visibilités.

**Différence fondamentale :** le PTX CUDA officiel documente un modèle virtuel, tandis que le guest Switch fournit des programmes GPU encodés dans son environnement. Les microbenchmarks A100 et GTX980 ne fournissent **ni** les latences T239 exactes **ni** des constantes à utiliser sur le GPU AMD PS5.

## 8. Revue Vulkan, RADV, caches et frame pacing

### 8.1 Caches Vulkan et files de construction

| Point | Constat sur source | Condition de qualification |
|---|---|---|
| First-use shader | Traduction CPU par cache miss et compteurs distincts | Tracer stage CFG/IR/SPIR-V, temps driver, wait worker, association frame |
| Build asynchrone | <code>RunBuild</code> et publication <code>is_built</code> | Ne pas consommer de pipeline nul ou invalide |
| Pipeline cache | Logiciel guest + cache driver Vulkan distincts | Identifier keys, version/UUID, reopen/reject, cold/warm |
| Shutdown cache | Drain builders + serialization worker avant destruction | Stop/relaunch console et non-fuite |
| Driver blob | <code>vulkan_device.cpp</code> écrit un fichier temporaire puis renomme | Atomicité sur filesystem PS5, échec/rollback, CRC/validité |
| Compute / task/mesh | <code>StageFlag</code> reconnaît Task et Mesh | Extension déclarée + shader SPIR-V réellement accepté par RADV |

### 8.2 Cache textures et écriture CPU

[<code>RasterizerVulkan::OnCPUWrite</code>](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/6c38328fbef33de747f5c31ea30d13541a513a4a/encore-active/eden-vulkan/vulkan_rasterizer.cpp#L2425-L2513) sépare buffer cache, texture cache et invalidation shader ; il relâche le mutex avant le flush différé sous marqueur de publication. Le flux a des tests d'ownership, mais **une nouvelle trace PS5** doit séparer temps d'attente sur mutex, temps détenu, délais d'invalidation, shader miss et âge du buffer consommé par le HUD.

**Référence de conformité** : [Vulkan Synchronization](https://docs.vulkan.org/spec/latest/chapters/synchronization.html) sépare l'**ordre d'exécution**, la **disponibilité** et la **visibilité** mémoire. Déplacer une opération hors mutex n'est sûr que si l'autre thread ne peut ni démapper ni remplacer sa ressource avant publication.

### 8.3 Longues copies GPU NS2 / limites de soumission

[<code>vk_buffer_cache_cost.cpp</code> L599–L708](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/6c38328fbef33de747f5c31ea30d13541a513a4a/encore-active/eden-vulkan/vk_buffer_cache_cost.cpp#L599-L708) filtre les copies nulles, valide les plages, coalesce certains segments sous un constructeur de 64 slots et émet ensuite un <code>CopyBuffer</code>. **Cette voie consultée n'exhibe pas une stratégie équivalente à un découpage borné des énormes listes en soumissions successives**, comme [EglantinePS5 #102](https://github.com/heydemoura/EglantinePS5/pull/102) l'a étudié pour un cas Bananza à fortes copies.

**H-P1 (après boot)** : vérifier les autres sites de batching/scheduling avant de parler de manque global ; instrumenter nombre de régions et barrières **par soumission**, avec bornes de validité et strict respect des fences. Ne pas confondre ce candidat post-boot avec le crash NS2 ancien à <code>PC=0x4</code>.

### 8.4 RADV / Mesa PS5

Sources et provenance : [Mesa épinglé](https://github.com/niakw/Prospero.Eden-Encore-vendor/tree/6c38328fbef33de747f5c31ea30d13541a513a4a/sources/ps5-mesa), [overrides PS5](https://github.com/niakw/Prospero.Eden-Encore-vendor/tree/6c38328fbef33de747f5c31ea30d13541a513a4a/encore-active/ps5-mesa). Le [cache disque Mesa maintenu](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/6c38328fbef33de747f5c31ea30d13541a513a4a/encore-active/ps5-mesa/src/util/disk_cache_os.c) contient des adaptations filesystem.

**Vérifications futures** : capabilities RADV réellement exposées, occupation mémoire heap, pipeline create, NIR → ACO, exactes extensions, source SHA vs bibliothèque compilée. Un cache créé sur disque ne démontre pas un hit. [RADV](https://docs.mesa3d.org/drivers/radv.html) utilise NIR et ACO selon ses chemins principaux ; cette description générale n'est pas un certificat de configuration de l'exécutable Encore.

### 8.5 Base de comparaison FC27 (historique, pas preuve des nouveaux commits)

[Audit des logs console R457](PS5_R457_2026-11-19_FC27_NS2_LAST_SESSION.md) : moyenne des fenêtres **28,6658 FPS**, **14/117** fenêtres sous 25 FPS, pire intervalle présenté **726,260 ms**, **624 280** acquisitions cache contentieuses, **15 414,493 ms** d'attente buffer cumulée **sur plusieurs threads** ; **357** shader misses et **2 320,752 ms** CPU cumulés. Ces grandeurs ne s'additionnent pas comme du temps mural d'une seule frame.

**Objectif futur** : A/B même scène / même paramètres / cold-warm, p50/p95/p99 et worst gaps, input latency, HUD age, guest progress et memory pressure ; comparer le binaire *avec* le patch de publication différée au binaire R457 historique.

## 9. Revue HLE, threads, IPC et cycle de vie

### 9.1 Kernel et condition variables

[<code>k_condition_variable.cpp</code>](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/6c38328fbef33de747f5c31ea30d13541a513a4a/encore-active/eden-threading/src/core/hle/kernel/k_condition_variable.cpp) implémente les changements de waiters sous scheduler lock et des fences <code>seq_cst</code>. La source contient encore un commentaire local <code>TODO(bunnei): We should call CanAccessAtomic(..) here.</code> dans <code>SignalImpl</code>.

**H-P1/P0 selon symptôme** : comparer le chemin avec l'upstream exact ; vérifier si l'accès atomique fautif est déjà borné par les wrappers appelés, la validité du handle et la durée de vie de la page. Un TODO historique n'est pas une preuve que le chemin est exploitable, ni un prétexte à changer l'ordre mémoire sans oracles.

### 9.2 Arrêt/relance

[<code>k_thread.cpp</code>](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/6c38328fbef33de747f5c31ea30d13541a513a4a/encore-active/eden-threading/src/core/hle/kernel/k_thread.cpp) traite finalisation, file de waiters et terminaison ; les sources <code>eden-threading</code>, <code>eden-sync</code> et <code>eden-core</code> possèdent des propriétaires différents. Aucun arrêt correct ne doit libérer les pages JIT, GPU buffers, pages invitées ou sinks audio avant extinction des utilisateurs associés.

### 9.3 Pause et menus

Ne pas attribuer automatiquement une pause de 5–10 s au GPU : l'input est capturé via HID puis le menu est traité par le guest, souvent via IPC/AM, avant rendu. **Instrumentation causale à exiger** : événement contrôleur → délivrance guest HID → attente kernel/IPC → mise à jour guest → draw HUD/menu → present. Seul un tel graphe peut établir le blocage principal.

## 10. Revue audio, vidéo, launcher et logs

### 10.1 Audio

[<code>sink_stream.cpp</code>](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/6c38328fbef33de747f5c31ea30d13541a513a4a/encore-active/eden-core/src/audio_core/sink/sink_stream.cpp) contient un garde de taille de ring buffer lors de <code>AppendBuffer</code> et un chemin d'underrun. Vérifier source/mix 48 kHz, nombre de canaux, propagation d'erreur et ordre de stop avec les threads invités, mais **aucune déficience audio nouvelle n'est déclarée sur cette seule lecture**.

### 10.2 Vidéo

La [source NVDEC FFmpeg](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/6c38328fbef33de747f5c31ea30d13541a513a4a/encore-active/eden-core/src/video_core/host1x/ffmpeg.cpp#L320-L350) appelle <code>avcodec_receive_frame</code> et gère les retours <code>EAGAIN</code> ; un [retry borné](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/6c38328fbef33de747f5c31ea30d13541a513a4a/encore-active/eden-core/src/video_core/host1x/ffmpeg.cpp#L445-L479) existe. Examiner côté runtime PS5 PTS, EOS, reprofilage YUV → GPU, backpressure, vidéoframe/swapchain et fin de titre, sans inventer un crash déjà corrigé.

### 10.3 Launcher et 31 langues

[<code>strings.cpp</code> L~100–140](https://github.com/niakw/ProsperoEden-Encore/blob/6b9763fa2170496fd316611e9a4bb28e20bb26fc/headless/prosperoeden/pe/core/strings.cpp#L95-L145) inclut des correspondances régionales telles que <code>fr-CA → fr-FR</code> et <code>en-GB</code> explicite avant fallback. [<code>eden_services.cpp</code> L~3020](https://github.com/niakw/ProsperoEden-Encore/blob/6b9763fa2170496fd316611e9a4bb28e20bb26fc/headless/prosperoeden/eden_services.cpp#L3010-L3032) transmet le réglage de logs détaillés au service natif.

**H-P2** : comparer les 31 catalogues et la chaîne de fallbacks avec [HarfBuzz](https://harfbuzz.github.io/) et [Unicode](https://www.unicode.org/reports/). Les 31 catalogues présents n'établissent pas la couverture de Montserrat seul, ni l'absence de glyphes de remplacement incorrects sur les textes du jeu.

### 10.4 Logs et préservation

Le pipe de journalisation conserve un descripteur producteur actif quand on passe au mode silencieux. Toutefois, [<code>LogPipe::Rotate</code>](https://github.com/niakw/ProsperoEden-Encore/blob/6b9763fa2170496fd316611e9a4bb28e20bb26fc/headless/log_pipe.h#L121-L153) retire un éventuel ancien fichier <code>first_path</code> au premier dépassement : vérifier la politique de conservation **inter-sessions**, séparément de la conservation OFF/ON **intra-session**. Ce choix de rotation peut être intentionnel ; ne pas le qualifier de perte abusive sans reproduire le scénario requis.

Scénarios futurs : démarrage avec logs ON ; ON→OFF→ON ; arrêt sans crash ; crash ; redémarrage ; relecture des deux segments ; espace disque saturé ; bascule pendant fermeture d'un jeu ; comparaison fps/frametime du mode ON contre OFF. Ne lancer aucune de ces expériences dans le présent audit.

## 11. Revue de la structure des dépôts et du build

### 11.1 Points solides

- Séparation source upstream <code>vendor/sources/</code> versus sources maintenues <code>vendor/encore-active/</code>, avec snapshots et manifestes.
- CMake sélectionne explicitement plusieurs fichiers maintenus en remplaçant des unités originales et fait des <code>FATAL_ERROR</code> quand les couples source/header attendus manquent.
- Séparation <code>src/</code>, <code>headless/</code>, données et tests. Les backups historiques ne doivent pas devenir une seconde implémentation compilée.
- Workflows dédiés aux critères source, host, PS5 natif, CodeQL, logs, NS2 et compatibilité, avec déclencheurs par chemin pour éviter les builds natifs implicites.
- Le workflow natif refuse par condition de job les pushes ordinaires ; un commit documentaire sans marqueur native ne lance pas la compilation.

### 11.2 Structure à surveiller

[<code>headless/CMakeLists.txt</code>](https://github.com/niakw/ProsperoEden-Encore/blob/6b9763fa2170496fd316611e9a4bb28e20bb26fc/headless/CMakeLists.txt) compte **environ 4 351 lignes** à la révision examinée. Ce volume n'est pas un bug mais signifie que l'audit de source active ne peut pas se limiter au nom d'un fichier. Les <code>if(EXISTS)</code> de plusieurs backports peuvent sélectionner volontairement un ancien chemin quand un overlay est absent. Il faut classifier chaque fallback comme « autorisé et neutre » ou « interdit sans propriétaire ».

Les arbres de versions <code>a64_emit_x64_{shared,standard}</code>, <code>memory_native_{standard,a32}</code> et Vulkan/OpenGL ne représentent pas automatiquement du code dupliqué compilé : il faut produire un **registre de sélection** (CMake target → TU/headers → source hash → motif du choix). C'est l'outil de base pour identifier le code mort et les variantes historiques sans nettoyage destructif.

### 11.3 Friction documentation / code

- Les commentaires historiques liés à des flags expérimentaux peuvent survivre après suppression des sélecteurs : priorité à la cohérence du contrat **effectif**.
- Les rapports datés parlent de différents commits ; un « encore manquant » dans une note antérieure peut être aujourd'hui intégré (A64 64K, GPU worker define).
- Ne jamais changer le registre historique afin de faire croire qu'un ancien build compilait une modification plus récente ; ajouter une note de succession avec SHA.
- Les résultats upstream (Eglantine/Lichii) ne s'appliquent qu'après comparaison d'ABI, de propriétaire de source, de la version Mesa et du même appelant dans Encore.

### 11.4 Sécurité et dépendances

Portée : vérifier SBOM/manifestes, sous-modules, toolchain, licences, avis de vulnérabilités npm/Boost/Mesa/FFmpeg et alertes CodeQL **dans les deux dépôts**. Aucun accès aux vues privées Dependabot/CodeQL d'alerte n'a été exploité dans cet audit : **ne pas inscrire un nombre de vulnérabilités comme résultat courant**.

Les sources vendored constituent une base de provenance, pas une liste de bibliothèques chargées. Classifier la vulnérabilité en <code>compile/runtime</code>, <code>outil CI uniquement</code>, <code>documentation</code> et <code>transitive inutilisée</code> avant une mise à jour, sans affaiblir la reproduction du build.

### 11.5 CI en cours et non-interférence

Le workflow [<code>build-040-zbic.yml</code>](https://github.com/niakw/ProsperoEden-Encore/blob/6b9763fa2170496fd316611e9a4bb28e20bb26fc/.github/workflows/build-040-zbic.yml#L1-L49) isole explicitement les commits <code>skip-only</code> de ceux <code>build-capable</code>. Les workflows de préflight/fast-gate et de sécurité sont filtrés sur le code, les outils, les contrats exécutables et quelques documents précis : ce **nouveau fichier d'audit** n'est pas leur cible déclarée. Ne pas toucher aux workflows, au README, au gitlink ou à un contrat JSON pour publier cet audit.

## 12. Comparaison exigences officielles et études

**Méthode de notation :** « mécanisme constaté » signifie une preuve statique ; « conformité à démontrer » veut dire qu'un test/artefact manque, et **pas** qu'une violation est prouvée.

| Référence normative ou scientifique | Contrat utile pour Encore | Observation dans code | Niveau restant |
|---|---|---|---|
| [Arm A-profile ARM](https://developer.arm.com/documentation/ddi0487/latest) | Instructions A64/A32, exclusives, exceptions | Dynarmic, code natif, SVC et mémoire présents | Oracles différentiel ARM/PS5 pour cas limites |
| [Arm ABI AA](https://github.com/ARM-software/abi-aa) | Appel et registres | Couche CPU6/loader, backend x64 | Tests exacts A64/A32, ABI PS5 |
| [Concurrency mapping, arXiv:2009.03846](https://arxiv.org/abs/2009.03846) | Atomiques et ordre ARM→x64 | Barrières, owner locks, alias RX/RW | Séquences concurrentes et traces causales |
| [Maxwell tuning guide](https://docs.nvidia.com/cuda/maxwell-tuning-guide/) | Limites architecturales invitées | Maxwell3D/2D, DMA, compute | Ne pas importer tailles/cycles de GTX desktop |
| [Mei & Chu, arXiv:1509.02308](https://arxiv.org/abs/1509.02308) | Méthode pour distinguer caches/TLB et latences | Mécanismes cache/GMMU existants | Microbenchmarks adaptés, pas constantes Maxwell desktop |
| [Ampere tuning guide](https://docs.nvidia.com/cuda/ampere-tuning-guide/) | Barrières/compute et synchronisation | Lowerer Ampere, refus modes et scoreboard | Capture par opcode/formes authentiques |
| [Ampere study, arXiv:2208.11174](https://arxiv.org/abs/2208.11174) | SASS, dépendances et instruction forms | HMMA/MEMBAR/DEPBAR reconnus partiellement | Tests mathématiques/lane et mode réel T239 |
| [Khronos SPIR-V](https://registry.khronos.org/SPIR-V/specs/unified1/SPIRV.html) | Validité et capacités shader | Backend SPIR-V et statuts de compilation | Validation d'étapes couvertes et image finale |
| [Vulkan sync](https://docs.vulkan.org/spec/latest/chapters/synchronization.html) | Exécution vs visibilité des écritures | Fences, deferred flush, cache invalidation | Interleavings et durées de vie PS5 |
| [Vulkan Memory Model](https://docs.vulkan.org/spec/latest/appendices/memorymodel.html) | Ordre des scopes et barrières GPU | Modes MEMBAR, shaders et stage flags | Tests formels/contrôles de publication |
| [Vulkan pipelines](https://docs.vulkan.org/spec/latest/chapters/pipelines.html) | Pipeline complet et usage valide | Workers async, waiters et cache | Vraies clés et coûts CPU/GPU sur console |
| [Mesa RADV](https://docs.mesa3d.org/drivers/radv.html) | NIR/ACO, pipeline compiler AMD | Mesa vendored et PS5 overrides | Profil runtime des extensions, ISA et allocation |
| [AMD RDNA perf guide](https://gpuopen.com/learn/rdna-performance-guide/) | Occupation, bande passante, caches | Présence shader/allocs GPU | Télémétrie sans supposer RGP utilisable sur console |
| [ASTC specification](https://github.com/KhronosGroup/DataFormat/blob/main/astc.txt) | Décompression fidèle | Module NS2 ASTC et textures VideoCore | Fuzz textures, parité pixels |
| [FFmpeg libavcodec](https://ffmpeg.org/libavcodec.html) | Send/receive, EAGAIN/EOS | Retry borné présent | Timeline PTS/DTS et sortie |
| [Opus](https://opus-codec.org/docs/) | Codec et buffers PCM | AudioCore / Opus / sink | Resync/underruns |
| [HarfBuzz](https://harfbuzz.github.io/) | Shaping Unicode | Dépendance et fallback i18n | Vérification réelle des polices de 31 langues |
| [FSR3 SDK](https://gpuopen.com/fidelityfx-super-resolution-3/) | Motion vectors et temporal history | FSR31/SGSR/R09 présents en source | Aucune garantie de temporal fidelity sans image |
| [DBT rules, arXiv:2402.09688](https://arxiv.org/abs/2402.09688) | Stratégies de traduction DBT | Dynarmic possède déjà sa propre IR | Recherche longue durée, pas remplacement gratuit |
| [GPU mémoire, arXiv:2611.13860](https://arxiv.org/abs/2611.13860) | Méthode de caractérisation empirique | Mémoire NVIDIA invitée et AMD hôte distinctes | Une analogie n'autorise pas des paramètres matériels non mesurés |

### Critères de « respect des docs »

Le respect d'une norme a deux niveaux : **(1)** le code vise explicitement le modèle et protège ses invariants ; **(2)** un oracle fonctionnel teste son comportement aux frontières. Exemple : des barrières présentes **ne prouvent pas** l'ordre Vulkan de toutes les ressources ; une source utilisant HarfBuzz **ne garantit pas** que tous les écrans possèdent les glyphes adaptés.

Les publications arXiv sont des **guides de protocole expérimental**, pas des spécifications de la Switch ni de la PS5. Ne pas convertir une latence d'A100 en temps attendu RDNA 2, ou une expérience sur QEMU en suppression de l'IR Dynarmic.

## 13. Registre consolidé des opportunités et risques

Le statut de chaque entrée est **« analyse/qualification à faire »**, sauf les lignes purement documentaires explicitement établies. Les tâches ne sont **pas** affectées, pas lancées et ne justifient pas un build.

| ID | Priorité | Constat / opportunité | État | Preuve minimale avant décision |
|---|---|---|---|---|
| AR-01 | P0 | NS2 GPU/guest boot <code>PC=0x4</code> historique | H + P | Première instruction fautive, identité NSO/patch, mapping, pile, HLE avant shader |
| AR-02 | P0 | NS2 12 GiB VA, plafond 6 GiB backing et releases GPU | F + H | Budget par pool, pages commit/fail et quiescence avant free |
| AR-03 | P0 | Arrêt/restart source JIT, GPU worker, audio, logs | F + H | Graphe de durée de vie et reproduction console |
| AR-04 | P1 | BufferCache FC27 lock contention / deferred page updates | F + P | A/B vendor #194, p99 frametimes + HUD/pause latencies |
| AR-05 | P1 | GMMU page-state vector dimensionné selon VA | F + H | RSS réel/constructor time, test sparse diff et erreurs |
| AR-06 | P1 | Longues listes de copies GPU en une soumission | F + H | Capturer max regions/barriers/submit et comparer Eglantine #102 |
| AR-07 | P1 | Cold shader misses et first-use pipeline wait | F + P | CFG/IR/SPIR-V vs build RADV vs wait, cold/warm contrôlé |
| AR-08 | P1 | Ampere ISA/instructions encore non traitées pour certaines formes | F + H | Captures d'opcodes et tables de résultats, shader stages |
| AR-09 | P1 | Cache shader/driver persistance | F + H | Réouverture même title/driver, hit ratio, invalidation UUID |
| AR-10 | P1 | Textures/HUD vieillissants | H + P | Dirty epoch → upload → draw → fence → scanout et font service |
| AR-11 | P1 | Pause tardive | H + P | HID → IPC/AM → guest → GPU → present, latence segmentée |
| AR-12 | P1 | NVDEC EAGAIN/EOS et vidéo A/V | F + H | Séquences réelles de décodage et PTS sur console |
| AR-13 | P1 | R09/FSR3.1/SGSR/MSAA reconfiguration et VRAM | F + H | Stage/format/AA, image output, coût et budget par passe |
| AR-14 | P2 | Log ON/OFF/ON, rotation, rétention inter-boots | F + H | Reproduction avec traces segmentées et coût en profil OFF |
| AR-15 | P2 | 31 langues, fallback, menus et HUD textes | F + H | Tests glyphes, shaping et captures sur vrais écrans |
| AR-16 | P2 | Source unique et source owner selection | F + H | compile_commands + Gitlink + symboles et abis par TU |
| AR-17 | P2 | Commentaires NS2 sparse « non-activé/expérimental » | **D confirmé** | Clarification documentaire sans code runtime |
| AR-18 | P2 | Ancien audit A64 1M et définition worker GPU | **D confirmé** | Note de succession des SHAs, sans réécrire archives |
| AR-19 | P3 | Maintenance CMake ~4 351 lignes | F + H | Répertoire des décisions/targets et fallback autorisés |
| AR-20 | P3 | CodeQL, toolchain, transitive vendor et SBOM | Non vérifié en direct | Inventaire alertes privées, reachability, versions, licence |

### Écueils à éviter

- **Ne pas corriger deux fois** A64 fast-dispatch ou worker GPU uniquement sur la foi d'un audit historique.
- **Ne pas accélérer** un shader en l'ignorant, une texture en omettant son invalidation, ou un pipeline en le déclarant prêt trop tôt.
- **Ne pas masquer** l'origine d'un OOM par un fallback dense silencieux.
- **Ne pas importer** une PR Eglantine/Lichii sans comparaison des variantes Mesa, de la génération GPU et des sources maintenues.
- **Ne pas nettoyer** des fichiers de source historique ou branches dans une opération documentaire : provenance et capacité de reproduction doivent être conservées.

## 14. Plan de validation futur, sans action

Ce plan est un **backlog de vérifications suggérées**, pas une exécution.

### Étape A — Provenance et cohérence (sans build)

1. Extraire au SHA courant la carte CMake target/TU, chemins d'include et macros par unité, puis comparer aux manifestes <code>EDEN_ACTIVE_SOURCE_CATALOG</code>.
2. Vérifier les <code>if(EXISTS)</code> et chemins de repli autorisés ; relever les codepaths de recherche jamais sélectionnés par le binaire natif.
3. Réconcilier les audits passés : date, couple moteur/vendor, correctifs maintenant sélectionnés, correctifs invalidés, validations manquantes.
4. Associer à chaque candidat arXiv la métrique qu'on entend mesurer et un protocole de fidélité.
5. Faire un inventaire sécurité des dépendances **moteur + vendor** avec preuve d'usage runtime.

### Étape B — Tests host source (à une future fenêtre de développement)

Pour chaque candidat, établir un oracle de correction (interleavings atomiques, format ASTC, GPU copy ordering, JIT lifetime, shader stage), produire tests positifs/négatifs, configurations ciblées et sanitizers. Des tests hôtes réussis closent seulement le niveau **H**.

### Étape C — Validation native et PS5 (décision distincte)

Vérifier CI au SHA commun, compiler uniquement lorsqu'un opérateur déclenche un build dans le chantier habituel, inspecter artefact/SELF/symboles, puis reproduire sur PS5 firmware 13.60 : NS1 FC27 (initial/warm match, HUD/pause, stop/relaunch) et NS2 MKW/Bananza (premier PC invité, processus, première image, mémoire, A/V et rendu). Aucun changement de code n'a été entrepris dans le présent audit.

### Étape D — Fermer les constats avec preuve

Associer chaque ligne AR-xx à un état : **documenté**, **candidat**, **code intégré**, **host vert**, **natif vert**, **console prouvé**, **rejeté**. Une note « source d'amélioration intégrée » ne devient pas « FPS mieux » sans comparaison PS5.

## 15. Couverture et vérifications documentaires

| Objet de contrôle | Résultat de cette lecture |
|---|---|
| Revue des deux dépôts | Oui : moteur et vendor épinglé |
| Code source représentatif consulté | Oui, familles CPU/JIT/mémoire/GPU/Vulkan/NS2/HLE/média/UI |
| Documentation mère relue | Oui : architecture de référence à SHA cité |
| Comparaison documentation / code | Oui : trois écarts/obsolescences de conclusions documentés |
| Références officielles / arXiv | Oui : matrice d'applicabilité, aucune hypothèse chiffrée dérivée sans test |
| Inventaire exhaustif de tous les fichiers et toutes fonctions | **Non** : hors portée d'une lecture ciblée sans extraction statique complète |
| Compilation/CI lancée par cet audit | **Non** |
| Mesures console lancées par cet audit | **Non** |
| Bugs runtime nouvellement démontrés | **Non** : risques, écarts et validations à exiger sont distingués |
| Modification code moteur, vendor ou build | **Aucune** |
| Impact sur build natif en cours | Aucun build demandé, aucune révision de source ni de Gitlink déplacée ; push documentaire ordinaire traité comme <code>skip-only</code> par le workflow natif |

### Sources de départ et registres permanents

- [Architecture mère](../ENCORE_TECHNICAL_ARCHITECTURE_AND_RESEARCH.md)
- [Structure et contrat de source unique](../EDEN_ARCHITECTURE.md)
- [Architecture PS5 native](../PS5_NATIVE_ARCHITECTURE.md)
- [Propriétaires de sources actives](../EDEN_ACTIVE_SOURCE_CATALOG.md)
- [Audit du graphe de dépendances](../EDEN_CORE_AUDIT_DEPENDENCIES.md)
- [Inventaire de migration](../EDEN_OVERRIDE_MIGRATION_INVENTORY.md)
- [Roadmap NS1/NS2](../ROADMAP_NS1_NS2_UNIFIED.md)
- [Tracker FC27](../FC27_F07_MASTER_TRACKER.md)
- [Comparaison Eglantine sur source plus ancienne](EGLANTINEPS5_NS2_FUNCTIONAL_UPSTREAM_PARITY_2026-11-19.md)
- [Référence technique NVIDIA](NVIDIA_GPU_ARCHITECTURE_REFERENCE_REGISTER_2026-11-19.md)
- [Archives et métriques R457](PS5_R457_2026-11-19_FC27_NS2_LAST_SESSION.md)
- [État d'intégration vendor FC27](FC27_VENDOR_194_ENGINE_INTEGRATION_2026-11-19.md)
- [Profil PS5 unique](ONE_NATIVE_BUILD_PROFILE_2026-11-19.md)
- [Historique de provenance d'artefact](PS5_NATIVE_ARTIFACT_AUDIT_2026-11-19_2B0975F7.md)

---

**Conclusion :** cet audit est une base documentaire versionnée pour prioriser les futures investigations. **Aucune recommandation ici n'est un ordre de patch, de migration, de suppression, de test ou de build**. La règle de clôture reste : bonne source réellement compilée → test host exact → artefact PS5 → validation comportementale sur console. Toute conclusion de conformité globale ou de gain FPS exigerait des preuves complémentaires.
