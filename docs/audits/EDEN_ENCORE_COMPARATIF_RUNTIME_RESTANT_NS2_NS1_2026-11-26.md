# Eden Encore — Comparatif runtime restant à couvrir, ligne par ligne — NS2 puis NS1

**Document 2/2 — registre du restant après le comparatif principal du 26 novembre 2026**

Ce document complète, sans le remplacer, le comparatif principal :

- [EDEN_ENCORE_COMPARATIF_RUNTIME_LIGNE_PAR_LIGNE_NS2_NS1_2026-11-26.md](./EDEN_ENCORE_COMPARATIF_RUNTIME_LIGNE_PAR_LIGNE_NS2_NS1_2026-11-26.md)

Il ne constitue **ni une liste de bugs démontrés, ni une validation console**. Son but est de garder un périmètre fermé pour les zones qui n'ont pas encore été couvertes ligne par ligne, et d'éviter de repartir dans un audit général sans signature de log.

## 0. Référence exacte de cette photographie

Contrôles effectués le **26 novembre 2026** :

- 🟢 **2026-11-26 — moteur `main` contrôlé :** `5d397aa9f6c31835c9172f7ba977d377597f31d0`.
- 🟢 **2026-11-26 — gitlink `vendor` contrôlé :** `9de08e4f4bbb903e25f330dde7b8185e19e078a1`.
- 🟢 **2026-11-26 — cohérence gitlink/vendor contrôlée :** le gitlink du moteur pointe sur le même SHA que `niakw/Prospero.Eden-Encore-vendor@main`, soit `9de08e4f4bbb903e25f330dde7b8185e19e078a1`.

Toute conclusion future doit être réévaluée si le moteur ou le gitlink vendor change.

### Signification des statuts

| Marque | Signification |
|---|---|
| 🟢 + date | Contrôle réellement effectué sur le code/contrat correspondant. Ce n'est **pas** une validation CI, build ou PS5. |
| 🟡 | Zone identifiée mais contrôle ligne par ligne non terminé ou non déclenché faute de signature causale. |
| 🔴 | Divergence prouvée et directement pertinente pour un symptôme observé. |
| ⚪ | Hors priorité actuelle / à ne pas ouvrir sans nouvelle preuve. |

## 1. Règle de travail

Pour chaque zone ci-dessous :

1. partir du **dernier log PS5 du titre concerné** ;
2. relever la signature exacte : méthode, service, SVC, moteur GPU, PC, shader/pipeline hash ou attente ;
3. retrouver le **C++ réellement sélectionné** par CMake, overlays et générateurs ;
4. comparer d'abord Encore au chemin actif correspondant de Lichii/EglantinePS5, puis aux références pertinentes (Eden/Yuzu/Ryujinx, nxnative, Ounce/libounce, Atmosphère/libnx/SwitchBrew/SwIPC, NVIDIA, Vulkan/Mesa) ;
5. documenter la comparaison ligne par ligne et dater le contrôle ;
6. ne corriger le runtime qu'après identification d'une divergence causale ou d'une hypothèse suffisamment solide ;
7. ne jamais transformer une absence de couverture en « bug confirmé ».

Aucun nouveau build natif PS5 n'est justifié par la seule mise à jour de ce document.

---

# 2. Tableau maître du restant

| ID | Zone | Priorité | Déclencheur obligatoire | État |
|---|---|---:|---|---|
| R-01 | Host1x engines au-delà des syncpoints : VIC / NVDEC / CDMA | P0 conditionnel | log désignant explicitement un moteur, une méthode, un pushbuffer ou un blocage Host1x | 🟡 |
| R-02 | Maxwell3D / C797 / C7C0 méthode par méthode | P0 conditionnel | méthode/engine ID observé dans le log ou première soumission GPU atteinte puis bloquée | 🟡 |
| R-03 | Formats texture/image, tiling, swizzle, copies 2D / Fermi2D | P1 | première frame obtenue mais image incorrecte, texture/HUD corrompu ou copie explicitement fautive | 🟡 |
| R-04 | KProcess / KThread / SVC / scheduling | P0 conditionnel | blocage CPU invité, wait SVC, deadlock, timeout ou thread guest qui n'avance plus | 🟡 |
| R-05 | Video decode pools 991 / 911 / 912 | P0 conditionnel | DK/Pokopia/MKW atteint explicitement la chaîne vidéo et bloque à cet endroit | 🟡 |
| R-06 | Audio NS2/NS1 | P2 actuel | première frame stable atteinte ou log audio bloquant causalement le boot | ⚪ |
| R-07 | HLE secondaires SM / LM / NIFM / ACC / AM | P0/P1 conditionnel | signature exacte de service/commande dans les logs | 🟡 |
| R-08 | FC27 shader Maxwell détaillé | P1 conditionnel | pipeline/shader hash ou scène A/B reliant traduction/stall à un défaut précis | 🟡 |

---

# 3. R-01 — Host1x engines : VIC / NVDEC / CDMA au-delà des syncpoints

**État : 🟡 non couvert exhaustivement.**

Le comparatif principal couvre déjà les contrats de syncpoints utiles au boot. Le restant concerne l'exécution réelle des moteurs Host1x lorsqu'un titre atteint ces chemins.

## Déclencheurs acceptés

- méthode VIC/NVDEC explicitement loggée ;
- pushbuffer CDMA qui n'avance plus ;
- incrément attendu mais jamais produit par le moteur ;
- attente sur sortie vidéo liée à une commande Host1x précise ;
- exception ou rejet de méthode avec offset/engine identifiable.

## Points de départ Encore à résoudre vers les unités réellement compilées

- `encore-active/eden-core/src/video_core/host1x/vic.cpp`
- `encore-active/eden-core/src/video_core/host1x/host1x.cpp`
- `encore-active/eden-core/overrides/video_core/host1x/host1x.h`
- `encore-active/eden-core/overrides/video_core/cdma_pusher.h`
- propriétaires NVDEC/FFmpeg sélectionnés par le build actif au moment du contrôle.

Ces chemins sont des **points de départ** ; le contrôle doit encore prouver leur sélection CMake/overlay au SHA étudié avant toute conclusion.

## Comparaison minimale à consigner

| Contrat | Encore | Lichii | EglantinePS5 / autre | Verdict |
|---|---|---|---|---|
| décodage des méthodes CDMA | à faire | à faire | à faire | 🟡 |
| ordre des méthodes / gather | à faire | à faire | à faire | 🟡 |
| signalement syncpoint par moteur | partiellement couvert ailleurs ; à rattacher au moteur | à faire | à faire | 🟡 |
| validation adresses / tailles | à faire | à faire | à faire | 🟡 |
| erreurs invité vs succès silencieux | à faire | à faire | à faire | 🟡 |
| cycle de vie frames/queues NVDEC/VIC | à faire | à faire | à faire | 🟡 |

### Critère de sortie

R-01 est clos seulement lorsque la signature observée dans le log est reliée à une méthode précise et que le chemin Encore actif est comparé au(x) upstream(s) pertinents. Pas d'audit exhaustif de tout Host1x sans signal.

---

# 4. R-02 — Maxwell3D / C797 / C7C0 méthode par méthode

**État : 🟡 non couvert exhaustivement.**

Le but n'est pas de produire un diff géant de toutes les méthodes GPU. La comparaison est déclenchée par les méthodes réellement observées sur DK, MKW, Pokopia, Pokémon Z-A ou FC27.

## Point d'entrée NS2 déjà visible

- `encore-active/ns2-runtime/gpu_dispatch/video_core/engines/puller.cpp` contient la sélection d'engines, dont le traitement du chemin `0xC7C0`.

Le contrôle ligne par ligne doit ensuite suivre **l'engine réellement bindé** et les méthodes effectivement consommées.

## Pour chaque signature observée

Documenter exactement :

| Champ | Valeur |
|---|---|
| Titre / Title ID | |
| SHA moteur / vendor | |
| engine ID | |
| subchannel | |
| méthode | |
| argument(s) | |
| PC / pushbuffer si disponible | |
| propriétaire C++ Encore réellement compilé | |
| comportement Lichii | |
| comportement EglantinePS5 | |
| autre upstream pertinent | |
| divergence | |
| causalité | |
| statut | 🟡 |

### Cibles particulières

- `C797` : uniquement si la trace confirme son emploi ;
- `C7C0` : suivre bind, admission native, état d'address space et dispatch méthode ;
- Maxwell3D classique : comparer seulement les méthodes observées ;
- aucune méthode non observée ne doit être marquée « manquante » par simple absence dans Encore.

### Critère de sortie

Pour un titre donné : toutes les méthodes présentes entre le dernier point connu sain et le blocage doivent être classées **équivalentes / divergence expliquée / divergence causale / non pertinente**.

---

# 5. R-03 — Texture/image formats, tiling, swizzle et Fermi2D

**État : 🟡 différé jusqu'à première frame ou preuve visuelle causale.**

Cette zone devient prioritaire dès qu'un titre produit une frame invitée mais avec image incorrecte, ou pour un défaut FC27 reproductible relié à une ressource précise.

## Points de départ Encore

- `encore-active/eden-core/src/video_core/engines/fermi_2d_observed.cpp`
- `encore-active/eden-core/src/video_core/engines/sw_blitter/blitter.cpp`
- `encore-active/eden-vulkan/vk_texture_cache_cost.cpp`
- `encore-active/eden-vulkan/vulkan_rasterizer.cpp`
- overlays TextureCache/ASTC réellement sélectionnés par CMake au SHA contrôlé.

## Matrice de comparaison

| Sujet | À vérifier |
|---|---|
| format invité → format Vulkan | taille, type, SRGB/UNORM/SNORM, depth/stencil |
| pitch / block-linear | pitch, block width/height/depth, layer |
| tiling | mode, alignements, mip offsets |
| swizzle / unswizzle | adresse, taille, ordre, volume, couches |
| Fermi2D source/destination | format, layout, rectangle, scaling |
| copies buffer↔image / image↔image | offsets, row length, slice, barriers |
| invalidation TextureCache | fraîcheur CPU/GPU, alias, ownership |
| ASTC | uniquement si le format observé l'exige |

### Critère de sortie

Une divergence n'est P1 que si elle correspond à une ressource ou une copie effectivement utilisée dans la scène fautive.

---

# 6. R-04 — KProcess / KThread / SVC de scheduling et attentes

**État : 🟡 conditionnel aux logs CPU/kernel.**

À ne pas ouvrir comme audit exhaustif tant que le blocage principal reste GPU/boot sans preuve kernel.

## Points de départ Encore à qualifier

- `encore-active/ns2-runtime/kernel_wait64/core/hle/kernel/k_process.h`
- `encore-active/eden-threading/src/core/hle/kernel/k_thread.cpp`
- `encore-active/eden-threading/src/core/hle/kernel/k_scheduler.cpp`
- `encore-active/eden-threading/src/core/hle/kernel/svc/svc_synchronization.cpp`
- `encore-active/ns2-runtime/gpu_access_svc/core/hle/kernel/svc.cpp`
- `encore-active/eden-core/src/core/hle/kernel/svc/svc_ipc.cpp`
- `encore-active/eden-core/src/core/hle/kernel/svc/svc_ipc_standard.cpp`

Le contrôle doit d'abord déterminer quel overlay est réellement actif pour la fonction concernée.

## Signatures qui déclenchent le diff

- `WaitSynchronization`, `WaitForAddress`, `ReplyAndReceive` ou timeout anormal ;
- thread guest bloqué sans événement attendu ;
- priorité/affinité/scheduling incohérent ;
- objet de synchronisation détruit ou signalé dans un ordre différent ;
- deadlock reproductible ;
- fermeture qui expulse l'application à cause d'un thread/process teardown précis.

### Critère de sortie

La chaîne **SVC → objet kernel → état thread → scheduler → réveil/timeout** doit être suivie entièrement pour la signature observée.

---

# 7. R-05 — Video decode pools 991 / 911 / 912

**État : 🟡 à déclencher seulement si le titre atteint explicitement ce chemin.**

## Propriétaire Encore identifié

- `encore-active/ns2-runtime/graphics_supervisor/core/hle/service/am/service/graphics_supervisor.cpp`
- `encore-active/ns2-runtime/graphics_supervisor/core/hle/service/am/service/graphics_supervisor.h`

Commandes à isoler :

- **991** — `CalculateDecoderImagePoolBuffer`
- **911** — `CreateVideoImagePool`
- **912** — `DestroyVideoImagePool`

## Contrats à comparer

| Contrat | État |
|---|---|
| parsing IPC / TIPC exact | 🟡 |
| tailles et alignements calculés | 🟡 |
| nombre d'images / surfaces | 🟡 |
| ownership et durée de vie | 🟡 |
| mapping GPU des images vidéo | 🟡 |
| destruction / teardown | 🟡 |
| résultats d'erreur guest | 🟡 |
| parité Lichii / EglantinePS5 / référence disponible | 🟡 |

### Critère de sortie

Ne pas conclure que ces commandes bloquent DK/Pokopia/MKW tant qu'une trace ne montre pas qu'elles sont atteintes juste avant le gel.

---

# 8. R-06 — Audio

**État : ⚪ non prioritaire actuellement.**

L'audio ne doit pas détourner du P0 NS2 tant que les titres n'atteignent pas une première frame stable, sauf si une trace démontre qu'un service audio bloque directement l'initialisation.

## Points de départ si déclenché

- `encore-active/ns2-runtime/audio/core/hle/service/audio/audio.cpp`
- `encore-active/ns2-runtime/audio/core/hle/service/audio/nx2_audio_user_client.h`
- managers `audren:u`, `audout:u`, `audin:u` réellement sélectionnés.

### Critère d'activation

Une commande audio doit apparaître comme dernier progrès causal avant le blocage, ou provoquer une attente/erreur fatale reproductible.

---

# 9. R-07 — Services HLE secondaires : SM / LM / NIFM / ACC / AM

**État : 🟡 uniquement par signature exacte.**

Pas de nouvelle revue générale des services. Les registres NS1/NS2 existants restent la source canonique pour la complétude de service.

## Règle

Pour chaque commande observée :

1. relever le service exact ;
2. relever l'ID de commande, version HOS/NS2 et forme IPC ;
3. identifier l'implémentation Encore réellement routée ;
4. comparer seulement ce contrat ;
5. dater la pastille lorsque le contrôle est fini.

## Points de départ déjà présents dans l'arbre

- NIFM : `encore-active/ns2-runtime/hle/core/hle/service/nifm/nifm.cpp`
- AM/Graphics Supervisor : `encore-active/ns2-runtime/graphics_supervisor/core/hle/service/am/service/graphics_supervisor.cpp`
- SM, LM et ACC : résoudre le propriétaire actif depuis la signature avant comparaison.

### Critère de sortie

Une commande HLE secondaire ne passe en P0/P1 que si son contrat explique directement le boot bloqué, le crash, la sortie cassée ou une attente critique.

---

# 10. R-08 — FC27 : shader Maxwell détaillé

**État : 🟡 différé jusqu'à preuve par hash/scène.**

Le comparatif détaillé Maxwell/shader n'est utile que si les traces de FC27 isolent un pipeline ou shader précis, ou si une scène A/B stable relie un défaut visuel/stall à la traduction.

## Points de départ

- cache pipeline Vulkan actif et clé de cache ;
- environnement shader Maxwell actif ;
- traduction Shader Recompiler ;
- dump/identité par `pipeline_hash` et `shader_hash` lorsqu'ils existent ;
- pour NS2 Ampere seulement si la trace du titre le requiert : `encore-active/ns2-runtime/ampere/shader_recompiler/frontend/ampere/`.

## Données minimales avant diff

| Donnée | Requise |
|---|---|
| scène FC27 reproductible | oui |
| SHA moteur/vendor | oui |
| pipeline hash ou shader hash | oui, sauf preuve équivalente très précise |
| temps de traduction/création pipeline | oui pour un stall |
| cache cold/warm | oui |
| résultat visuel ou frametime associé | oui |
| comparaison upstream ciblée | oui |

### Critère de sortie

Classer le pipeline/shader observé : **traduction équivalente**, **divergence non causale**, **divergence causale**, ou **preuve insuffisante**.

---

# 11. Ordre recommandé avec les quatre titres NS2 encore bloqués

Tant qu'aucune première frame stable n'existe :

1. **R-01 Host1x** uniquement si les logs montrent VIC/NVDEC/CDMA ;
2. **R-02 Maxwell3D/C797/C7C0** dès qu'une méthode/engine devient le dernier progrès observé ;
3. **R-04 kernel/SVC** si le guest attend côté CPU ;
4. **R-05 video pools** si 991/911/912 sont atteints ;
5. **R-07 HLE secondaires** uniquement pour la commande exacte qui bloque ;
6. R-03 devient prioritaire après première frame ou corruption image ;
7. R-06 reste différé ;
8. R-08 reste FC27/P1 et ne doit pas retarder le P0 NS2.

Cette priorité est **dynamique** : le dernier log console décide quelle zone devient active.

---

# 12. Journal de contrôles du document 2

| Date | ID | Titre / trace | Contrôle | SHA moteur | SHA vendor | Résultat |
|---|---|---|---|---|---|---|
| 2026-11-26 | BASE | — | 🟢 HEAD moteur, gitlink vendor et égalité avec vendor/main | `5d397aa9f6c31835c9172f7ba977d377597f31d0` | `9de08e4f4bbb903e25f330dde7b8185e19e078a1` | référence du document fixée |

Les futurs contrôles doivent être ajoutés ici **et** dans la section concernée. Une pastille verte certifie uniquement que le contrôle de code/contrat a été réalisé à la date indiquée.

---

# 13. Ce que ce document n'autorise pas

- aucun correctif « par parité » sans cause ;
- aucun backport massif de Lichii/EglantinePS5 ;
- aucun succès silencieux ajouté pour faire avancer artificiellement le boot ;
- aucun nouveau flag `EXPERIMENTAL` ni chemin dormant ;
- aucun changement de texture/buffer qui sacrifie fidélité ou sécurité mémoire ;
- aucun build natif déclenché seulement parce qu'une comparaison documentaire est terminée ;
- aucune déclaration « résolu » sans validation PS5 représentative.

**But final :** transformer seulement les signatures réelles des logs en comparaisons ciblées, puis en corrections runtime mesurables sur PS5.
