# Eden Encore — Comparatif runtime restant, ligne par ligne — NS2 puis NS1

**Document 2/2 — complément complet du comparatif principal du 26 novembre 2026**

Ce document complète, sans le remplacer :

- [EDEN_ENCORE_COMPARATIF_RUNTIME_LIGNE_PAR_LIGNE_NS2_NS1_2026-11-26.md](./EDEN_ENCORE_COMPARATIF_RUNTIME_LIGNE_PAR_LIGNE_NS2_NS1_2026-11-26.md)

Il reprend les huit zones volontairement laissées hors du premier document et les traite selon la même méthode : **source réellement compilée → fonction/contrat → Encore ↔ Lichii ↔ EglantinePS5 ↔ référence indépendante lorsque pertinente → écart exact → portée causale**.

Ce document **n'est pas** une liste de huit bugs démontrés. Une différence de code peut être :
- une correction/hardening Encore ;
- une stratégie différente mais cohérente ;
- une divergence ABI réelle ;
- une divergence de compatibilité plausible ;
- ou un défaut causal seulement si une trace console l'établit.

---

# 0. Photographie exacte et dépôts comparés

## 0.1 Révisions de livraison Encore

Contrôles effectués le **26 novembre 2026** :

- 🟢 **2026-11-26 — moteur `main` contrôlé :** `64e1a743e889739bd76eb545e24da00fb6ced8d2`.
- 🟢 **2026-11-26 — gitlink `vendor` contrôlé :** `9de08e4f4bbb903e25f330dde7b8185e19e078a1`.
- 🟢 **2026-11-26 — vendor `main` contrôlé :** `9de08e4f4bbb903e25f330dde7b8185e19e078a1`.
- 🟢 **2026-11-26 — cohérence gitlink/vendor contrôlée :** le moteur épingle exactement le HEAD vendor comparé.

Les conclusions de ce document sont donc rattachées au couple :

> **Encore moteur `64e1a743` + vendor `9de08e4f`**

## 0.2 Révisions upstream réellement lues

| Dépôt | Branche / SHA comparé | Rôle |
|---|---|---|
| **Lichii** | `nx2@0288882f36692a94b56fa85177abdad0ec8be59d` | référence émulation NS2 principale |
| **EglantinePS5** | `main@75a552ff945521eb31adf34f34ccb73a003809dc` | référence PS5 + arbre Eglantine embarqué |
| **nxnative** | `main@96f1f0766344ed01b54dab8b61a6d2758985aafc` | oracle indépendant ciblé pour codec/audio/SDK NS2 |
| **Eden vendor source** | inclus dans `9de08e4f` | baseline NS1 et propriétaires non remplacés |

🟢 **2026-11-26 — contrôle des HEAD upstream effectué.**

EglantinePS5 embarque son code émulateur sous `Eglantine/`; les chemins ci-dessous l'indiquent explicitement.

## 0.3 Signification des marques

| Marque | Signification |
|---|---|
| 🟢 **date** | contrôle de code/contrat réellement effectué à cette date |
| **PARITÉ** | même contrat utile, même si les commentaires/instrumentations diffèrent |
| **HARDENING ENCORE** | Encore est plus strict ou plus sûr que l'upstream comparé |
| **DIVERGENCE CONFIRMÉE** | comportement/code/ABI différents ; causalité console non présumée |
| **CANDIDAT P0/P1** | divergence qui mérite d'être testée si la signature correspond au log |
| **NON CAUSAL À CE STADE** | aucune preuve console ne relie encore l'écart au symptôme |
| 🔴 | réservé à une causalité démontrée par trace/test représentatif ; **aucun nouvel item de ce document n'est marqué rouge sans cette preuve** |

---

# 1. Sources réellement sélectionnées avant comparaison

Le premier risque d'un comparatif multi-repos est de comparer un fichier qui n'est jamais compilé. La sélection native PS5 a donc été recontrôlée avant le diff.

## 1.1 CMake / overlays Encore

🟢 **2026-11-26 — `headless/CMakeLists.txt` contrôlé au moteur `64e1a743`.**

Le fichier actif a le blob Git `036767a2859ce7cb1944673682ac8229da0b2c4e` et sélectionne notamment :

| Domaine | Propriétaire réellement sélectionné |
|---|---|
| NS2 GPU puller | `vendor/encore-active/ns2-runtime/gpu_dispatch/video_core/engines/puller.cpp` |
| NS2 Graphics Supervisor | arbre `vendor/encore-active/ns2-runtime/graphics_supervisor/` |
| NS2 kernel wait64 | arbre `vendor/encore-active/ns2-runtime/kernel_wait64/` pour les propriétaires remplacés |
| Early HLE NS2 | overlays `vendor/encore-active/ns2-runtime/hle/` |
| TextureCache NS2/PS5 | propriétaire `vendor/encore-active/ns2-astc/` sélectionné par la chaîne Vulkan |
| shader Maxwell maintenu | plusieurs TU/headers `vendor/encore-active/eden-shader/` substitués explicitement |
| pipeline Vulkan PS5 | `vendor/encore-active/eden-vulkan/vk_pipeline_cache_cost.cpp` |

🟢 **2026-11-26 — `headless/gpu_native_observability.cmake` contrôlé**, blob `213721354b8d986f15355397dd7a36af2a067908`.

Il sélectionne **`fermi_2d_observed.cpp`** et ne sélectionne pas un `fermi_2d_experimental.cpp`.

🟢 **2026-11-26 — `headless/vulkan.cmake` contrôlé**, blob `a597985b716fe4340157c7e717f04e2bd08641d5`, avec sélection du propriétaire TextureCache NS2/ASTC.

## 1.2 Cas particulier audio

🟢 **2026-11-26 — propriétaire audio final contrôlé.**

La chaîne est en deux temps :

1. le graphe NS2 apporte `nx2_audio_user_client.h`, Sysmix et les interfaces NS2 depuis le vendor ;
2. sur PS5, `headless/CMakeLists.txt` retire le TU audio partagé et le remplace par **`headless/r23_audren_debug_ps5.cpp`**.

Le TU final a le blob `0fff4af935ad9b1b8afa34c953e70a16fb0310ad`. Il conserve les enregistrements NS2 et inclut le header `core/hle/service/audio/nx2_audio_user_client.h`. Les différences de `INx2AudioUserClient` analysées en R-06 sont donc bien visibles par le runtime compilé.

---

# 2. Résumé des huit zones après comparaison

| ID | Zone | Contrôle effectué | Verdict source | Causalité actuelle |
|---|---|---|---|---|
| R-01 | Host1x VIC/NVDEC/CDMA | 🟢 2026-11-26 | surtout **HARDENING ENCORE** ; VIC diffère sur validation/format | pas de cause P0 démontrée |
| R-02 | C797/C7C0/C7B5 / Maxwell3D | 🟢 2026-11-26 | **DIVERGENCE ARCHITECTURALE CONFIRMÉE** : alias legacy upstream vs identité Ampere native Encore | P0 conditionnel à la méthode/attente observée |
| R-03 | formats/tiling/swizzle/Fermi2D | 🟢 2026-11-26 | Encore couvre plus de copies, mais **fail-closed format inconnu incomplet** vs upstream | candidat P1 si format non nul inconnu/copie fautive observé |
| R-04 | KProcess/KThread/SVC/scheduler | 🟢 2026-11-26 | **PARITÉ** principale + saturation timeout Encore | non causal sans wait/deadlock de log |
| R-05 | video pools 991/911/912 | 🟢 2026-11-26 | **DIVERGENCE ABI/LAYOUT CONFIRMÉE** | candidat P0 fort si 991/911 est atteint |
| R-06 | audio | 🟢 2026-11-26 | **DIVERGENCE DE CONTRAT CONFIRMÉE** dans `aud:u` | P0 conditionnel si le boot/stall passe par aud:u |
| R-07 | SM/LM/NIFM/ACC/AM | 🟢 2026-11-26 | tables largement alignées ; cmd 40 AM volontairement plus riche ; cmd 60 **parité ABI** | seulement par commande exacte de log |
| R-08 | FC27 shader Maxwell | 🟢 2026-11-26 | architecture pipeline/cache très divergente ; Encore possède ses correctifs PS5 | P1 seulement avec hash/scène A/B |

---

# 3. R-01 — Host1x au-delà des syncpoints : CDMA / Control / NVDEC / VIC

## 3.1 Fichiers comparés

| Composant | Encore | Lichii | EglantinePS5 |
|---|---|---|---|
| CDMA | `encore-active/eden-core/src/video_core/cdma_pusher.cpp` — blob `91ace41154430a718cd163ceacd45b9607b63d43` | `src/video_core/cdma_pusher.cpp` — `d04b73877936b207fd5b8bd8b49ce41bbce67b0a` | `Eglantine/src/video_core/cdma_pusher.cpp` — **même blob `d04b738...`** |
| Host1x Control | `encore-active/eden-core/src/video_core/host1x/control.cpp` — `fcbf4e092f054724b9fd4731c8dfec9917cea27a` | `src/video_core/host1x/control.cpp` — `c65e8a...` | `Eglantine/src/video_core/host1x/control.cpp` — `494a100...` |
| NVDEC classique | `encore-active/eden-core/src/video_core/host1x/nvdec.cpp` — `c83ac982...` | `src/video_core/host1x/nvdec.cpp` — `2d293de...` | `Eglantine/src/video_core/host1x/nvdec.cpp` — `5dbc6a...` |
| VIC | `encore-active/eden-core/src/video_core/host1x/vic.cpp` — `178d361...` | `src/video_core/host1x/vic.cpp` — `71ba8ef...` | `Eglantine/src/video_core/host1x/vic.cpp` — `1a89f3d...` |

🟢 **2026-11-26 — les quatre familles ont été lues et comparées au niveau de leurs fonctions de dispatch/exécution.**

## 3.2 `CDmaPusher::ExecuteCommand`

### Lichii / Eglantine

Les deux fichiers sont byte-identiques. Le chemin :
- décode la commande Host1x ;
- écrit la méthode dans le tableau de registres ;
- route vers Control/NVDEC/VIC ;
- traite les incréments de syncpoint et les séquences SetMethod/Mask/Immediate.

### Encore

Encore conserve cette logique mais ajoute deux protections visibles :

1. la commande Control reçoit un **`std::stop_token`** et peut donc interrompre proprement une attente pendant la fermeture ;
2. une méthode au-delà de `ThiRegisters::NUM_REGS` est refusée avant l'écriture de registre.

**Verdict : HARDENING ENCORE.**  
Aucun manque fonctionnel Lichii/Eglantine n'est identifié ici. Le stop token est au contraire cohérent avec l'objectif de ne pas laisser un worker Host1x bloqué pendant le teardown.

## 3.3 `Control::ProcessMethod`

Le différentiel utile est le même : Encore propage le stop token vers la primitive d'exécution/attente, Lichii et Eglantine utilisent la signature historique.

**Verdict : HARDENING ENCORE / PARITÉ fonctionnelle hors teardown.**

## 3.4 `Nvdec::Execute`

Les corps utiles sont fonctionnellement équivalents pour le **NVDEC classique** :
- moteur désactivé → temporisation courte ;
- H.264 / VP8 / VP9 → decode ;
- codec inconnu → erreur.

Le support NS2 récent ne doit pas être déduit de ce seul fichier : Encore possède par ailleurs sa chaîne de décodeur NS2 native, tout comme les références NS2 ont des chemins supplémentaires.

**Verdict : aucun écart P0 démontré dans `Nvdec::Execute` classique.**

## 3.5 `Vic::Execute`

Encore est sensiblement plus défensif :

| Contrat | Encore | Lichii/Eglantine |
|---|---|---|
| taille de surface | plafond pixels/octets avant allocation | validation plus légère |
| dimensions/fields | validation avant conversion | moins de gardes |
| format pixel inconnu | saute la surface non décodable | le chemin historique peut continuer plus loin |
| YUV420P/NV12 supportés | oui | oui |
| diagnostics bornés | oui | différents/absents |

**Verdict : HARDENING ENCORE**, avec une différence sémantique possible pour un format VIC non pris en charge. Elle ne devient candidate que si un log de DK/MKW/Pokopia/Z-A montre précisément ce format/moteur.

## 3.6 Conclusion R-01

🟢 **2026-11-26 — R-01 contrôlé.**

Le reste Host1x n'est plus un « trou inconnu » général : le dispatch CDMA, Control, NVDEC classique et VIC ont été comparés. La prochaine comparaison doit être déclenchée **par une méthode Host1x précise du log**, pas par un nouvel audit intégral.

---

# 4. R-02 — C797 / C7C0 / C7B5 et méthodes GPU Ampere

C'est la plus forte divergence d'architecture observée dans ce document.

## 4.1 Propriétaires

| Dépôt | Fichier | Blob |
|---|---|---|
| Encore | `encore-active/ns2-runtime/gpu_dispatch/video_core/engines/puller.cpp` | `576a9d697da398aa6f42901b1764aa7574155411` |
| Lichii | `src/video_core/engines/puller.cpp` | `94409941ec81cac7e2fbf6ec0c0011e84e6b8e64` |
| EglantinePS5 | `Eglantine/src/video_core/engines/puller.cpp` | `3349deabc3a0e5908303c22a0651c16ea5bd6aa5` |

🟢 **2026-11-26 — `ProcessBindMethod`, `CallEngineMethod` et sémaphores comparés.**

## 4.2 Bind des classes

### Lichii / Eglantine

Les classes Ampere sont converties immédiatement vers les propriétaires historiques :

| Classe invitée | Alias |
|---|---|
| `0xC797` AMPERE_B | `MAXWELL_B` |
| `0xC7C0` AMPERE_COMPUTE_B | `KEPLER_COMPUTE_B` |
| `0xC7B5` AMPERE_DMA_COPY_B | `MAXWELL_DMA_COPY_A` |

Après le bind, le `bound_engine` contient donc l'identité legacy et les méthodes passent essentiellement dans les moteurs existants.

### Encore

Encore **ne détruit pas l'identité de classe Ampere** :

- `C797` reste C797 dans `bound_engines` ;
- `C7C0` reste C7C0 ;
- `C7B5` reste C7B5 ;
- le registre `NativeGpuChannelRegistry` vérifie que le canal appartient réellement au contexte NS2 natif ;
- les binds graphics/compute sont enregistrés avant exposition au GPFIFO ;
- une classe native invalide retire/refuse le canal au lieu de continuer dans l'ancien propriétaire.

**DIVERGENCE CONFIRMÉE :** upstream = **alias de compatibilité**, Encore = **identité Ampere authentifiée + propriétaire legacy sous-jacent**.

Cette divergence est volontaire et permet à Encore de ne pas appliquer aveuglément des méthodes Maxwell lorsque les sémantiques Ampere diffèrent.

## 4.3 C797 : `CallNative3D`

Encore possède une fonction absente de Lichii/Eglantine :

- upload/bind du MME Ampere ;
- conservation de RAM MME ;
- FIFO macros `0xE00..0xEFF` ;
- validation des adresses de lecture GMMU ;
- staging des écritures de registres ;
- refus du macro/canal en cas de séquence invalide ;
- fallback vers `Maxwell3D::CallMethod` seulement pour les méthodes dans la plage compatible.

Lichii/Eglantine n'ont pas cette couche : C797 ayant été aliasé en Maxwell, la méthode part directement vers le moteur Maxwell.

**Verdict : DIVERGENCE ARCHITECTURALE CONFIRMÉE, causalité non déterminée.**

## 4.4 C7C0 : compute

Encore sépare explicitement certains contrats Ampere :

- méthodes de lancement/QMD autour de `0xAE / 0xAF / 0xB0` ;
- `0x107` inline QMD ;
- `0x6C3` report semaphore ;
- le commentaire/code refuse d'interpréter automatiquement le PCAS Ampere comme le lancement QMD Maxwell historique.

Lichii/Eglantine aliasent C7C0 vers KeplerCompute puis utilisent le chemin legacy.

**Verdict : DIVERGENCE CONFIRMÉE.**  
Un diff méthode par méthode devient causal seulement si le log donne la dernière méthode C7C0 exécutée avant le gel.

## 4.5 C7B5 : DMA

Les deux stratégies convergent davantage : le moteur sous-jacent est MaxwellDMA. Encore ajoute cependant la condition de canal natif vivant avant le dispatch.

**Verdict : parité de moteur + contrôle d'ownership Encore.**

## 4.6 Sémaphores : différence de progression majeure

### Lichii / Eglantine

Leur `ProcessSemaphoreExecute` :
- RELEASE → programme l'écriture/fence ;
- ACQUIRE → vide les fences nécessaires, lit la valeur ;
- si la condition n'est pas satisfaite, loggue un warning borné puis **continue**.

### Encore

`ProcessNativeSemaphoreExecute` :
- valide que l'adresse GPU est réellement mappée ;
- exige un backing CPU lorsqu'il est nécessaire à la publication ;
- capture génération processus + génération canal ;
- après retirement GPU, refuse de publier dans une nouvelle allocation réutilisant la même VA ;
- pour un ACQUIRE non satisfait, conserve un **`pending_native_acquire`** et ne traite pas la suite comme si l'attente avait réussi.

**DIVERGENCE CONFIRMÉE ET IMPORTANTE :**
- Lichii/Eglantine privilégient la progression/compatibilité ;
- Encore modélise une vraie attente et interdit un faux succès.

Cela **ne signifie pas** qu'Encore doit copier le « continue » upstream : cela pourrait masquer une synchronisation réellement manquante et produire corruption/fences contrefaites. En revanche, si un jeu reste figé sur un `pending_native_acquire`, il faut immédiatement rechercher **le producteur attendu, l'adresse et la valeur de release**.

## 4.7 Conclusion R-02

🟢 **2026-11-26 — R-02 contrôlé au niveau bind + dispatch + sémaphore.**

**Action causale recommandée à partir des logs :**
- dernier engine/method = C797 → comparer cette méthode dans `CallNative3D` ;
- dernier engine/method = C7C0 → comparer QMD/PCAS précis ;
- dernier événement = native acquire → retrouver le release/producteur, ne pas neutraliser l'attente au hasard.

---

# 5. R-03 — Formats image, tiling, swizzle, TextureCache et Fermi2D

## 5.1 Propriétaires comparés

| Domaine | Encore | Lichii | EglantinePS5 |
|---|---|---|---|
| Fermi2D | `encore-active/eden-core/src/video_core/engines/fermi_2d_observed.cpp` blob `4be53f7b3ec2daf06b54dacc4d77dc4b75e9db05` | `src/video_core/engines/fermi_2d.cpp` blob `406e41d6a20221f1221d86d2a20eafcb9ca1a206` | `Eglantine/src/video_core/engines/fermi_2d.cpp` blob `5e29f954a6eb1f036891488224fe425f51ef90c6` |
| software blitter | `encore-active/eden-core/src/video_core/engines/sw_blitter/blitter.cpp` blob `d5a5436cdc2414c53834a886cdaa4578b4dc8a94` | `src/video_core/engines/sw_blitter/blitter.cpp` blob `e43a4e9f6b75494a25cbeab992701e553b9fd8f3` | `Eglantine/.../sw_blitter/blitter.cpp` blob `e72284d3f84fc3d84e738e00738b9982087cb702` |
| surface format | vendor `sources/eden/src/video_core/surface.cpp` blob `4603870bfa292f1ccbb678712d344cd44452b11e` | `src/video_core/surface.cpp` blob `9ce8bec55d378344a962c70252354c08983ab8ec` | `Eglantine/src/video_core/surface.cpp` blob `da57da6917774e44167129fd03ac8233e97d9b43` |

🟢 **2026-11-26 — Fermi2D, software blitter et conversion de formats contrôlés.**

## 5.2 Fermi2D : Encore n'est pas simplement « en retard »

Lichii/Eglantine refusent encore plusieurs formes dans leur chemin direct :
- layers source/destination non nuls ;
- clipping dans certaines formes ;
- opérations autres que SrcCopy.

Encore traite déjà davantage de cas :
- layers pitch-linear validés ;
- certaines tranches de volumes block-linear ;
- clipping destination avec recalcul des coordonnées source ;
- contrôles d'overflow/adresses/tailles ;
- garde spécifique contre `RenderTargetFormat::NONE`.

**Verdict : Encore a une couverture de copie plus large sur plusieurs contrats.**

## 5.3 Différence importante : format inconnu « fail closed »

Lichii et Eglantine ont introduit `TryPixelFormatFromRenderTargetFormat` :
- un format reconnu → PixelFormat ;
- un format non reconnu → absence de valeur ;
- Fermi2D/software blitter peuvent alors **refuser la copie** au lieu d'inventer une interprétation.

Encore, dans le `surface.cpp` actuellement épinglé :
- n'a pas cette API optionnelle ;
- le chemin historique signale le format non implémenté puis retourne encore `A8B8G8R8_UNORM` comme fallback générique.

Encore protège déjà explicitement le cas `NONE/0` dans `fermi_2d_observed.cpp`, mais **un autre format non nul non reconnu** peut encore tomber sur le fallback générique.

Le software blitter confirme le différentiel :
- Encore blob `d5a543...` : pas de `TryPixelFormatFromRenderTargetFormat`;
- Lichii blob `e43a4e...` : API `Try...` présente ;
- Eglantine blob `e72284...` : API `Try...` présente.

**DIVERGENCE CONFIRMÉE — candidat P1.**

Elle ne devient une correction prioritaire que si une trace identifie :
- un format non nul inconnu ;
- utilisé par Fermi2D/software blit/TextureCache ;
- et relié à l'image/HUD/textures fautifs.

Le `format=0` déjà observé historiquement ne suffit pas à prouver cette cause, car le Fermi2D maintenu d'Encore possède désormais une garde dédiée pour `NONE`.

## 5.4 Native tiling / block depth

Le software blitter Encore conserve le traitement `UsesNativeTiling` et les champs de block depth. Lichii possède également cette propagation ; Eglantine au SHA comparé n'expose pas exactement le même marqueur dans ce fichier.

**Verdict : pas de manque global « native tiling absent » dans Encore.**

## 5.5 TextureCache

Le propriétaire PS5/NS2 est le fork maintenu `encore-active/ns2-astc`, et non le seul fichier Eden source. Les correctifs déjà présents couvrent notamment les tranches block-linear qualifiées et des copies cross-format multi-couches.

Ce document ne transforme pas les autres formes non qualifiées en bugs :
- aliases complexes ;
- 3D partielles/scalées/filtrées ;
- formats non observés ;
- publication d'une image dont la ressource exacte n'a pas été suivie.

## 5.6 Conclusion R-03

🟢 **2026-11-26 — R-03 contrôlé.**

Le point concret restant n'est pas « Fermi2D manque tout » ; c'est surtout **le traitement fail-closed des formats non reconnus**, plus les formes de copies qui devront être ouvertes seulement quand une frame/ressource précise les désigne.

---

# 6. R-04 — KProcess / KThread / SVC / scheduling

## 6.1 `KThread::FinishTermination`

| Dépôt | Fichier / blob |
|---|---|
| Encore | `encore-active/eden-threading/src/core/hle/kernel/k_thread.cpp` — `d9cdbc92c12e1d1c67a5267cb5fa77f4f042ec18` |
| Lichii | `src/core/hle/kernel/k_thread.cpp` — `d6c12e150aa977d7f81f502bb3b70687743d8fb7` |
| Eglantine | `Eglantine/src/core/hle/kernel/k_thread.cpp` — `6d2d3380508a308df49ce9f4548fefc636e90690` |

Les trois :
1. vérifient que le thread n'est plus en exécution ;
2. signalent l'objet sous scheduler lock ;
3. notifient les waiters ;
4. exécutent le dernier `Close` **hors scheduler lock**.

Lichii a un commentaire plus détaillé sur les light locks processus ; Encore/Eglantine expriment la même contrainte sous une forme plus courte.

**Verdict : PARITÉ de contrat.**

## 6.2 `KScheduler::SwitchThread`

Blobs :
- Encore `6bf49c0165ecac602628679adbb8cee8d8407190`;
- Lichii `e008823a96dd04ee95cae93cd433529d2206bdf1`;
- Eglantine `8ee1d6f53e1316ae420281037332768dc838492e`.

Le changement de thread, l'accounting CPU, le previous-thread et le TLS suivent la même logique. Lichii/Eglantine ajoutent `Nx2ThreadStats::OnSwitch` pour l'observabilité.

**Verdict : PARITÉ runtime principale ; instrumentation upstream supplémentaire.**

## 6.3 `WaitSynchronization`

Blobs :
- Encore `15937d31e8cf9aa531f0fb95bf0ca991d239c85c`;
- Lichii `fe1b28a3adb9fabf777342ce2d11e53b581a1071`;
- Eglantine `2b019c52d1ed8a62f1d7b4b823b6294cadb40059`.

Les trois :
- valident le nombre de handles ;
- traduisent les handles en objets de synchronisation ;
- ferment les références au retour ;
- appellent `KSynchronizationObject::Wait`;
- convertissent `ResultSessionClosed` en succès comme prévu par ce chemin.

Différence :
- Lichii/Eglantine additionnent les ticks avec des additions simples ;
- Encore détecte les overflows et **sature au maximum signé**.

**Verdict : HARDENING ENCORE.**

## 6.4 Conclusion R-04

🟢 **2026-11-26 — R-04 contrôlé.**

Aucune divergence générale de scheduling ne justifie une correction aveugle. R-04 ne redevient P0 que si le log montre un thread guest, un SVC wait, un timeout ou un teardown précisément bloqué.

---

# 7. R-05 — Video decode pools 991 / 911 / 912

C'est le **plus gros écart ABI chiffrable** trouvé dans cette passe.

## 7.1 Propriétaires

Encore :
- `encore-active/ns2-runtime/graphics_supervisor/core/hle/service/am/service/graphics_supervisor.cpp`;
- helper `encore-active/ns2-runtime/hle/core/hle/service/am/service/native_image_layout.h` — blob `84217f9b62f64e9a48305c29cae7f320f5332d19`.

Lichii :
- `src/core/hle/service/nx2_gsv.h` — blob de la révision contrôlée `7321dfd01092ac717db0b1a289119ce17db1ae9d`.

Eglantine :
- `Eglantine/src/core/hle/service/nx2_gsv.h` — `15c425ab929059119915a4e615bba55fb8f05ca6`.

## 7.2 Table des commandes

| Cmd | Encore | Lichii/Eglantine |
|---:|---|---|
| 991 | `CalculateDecoderImagePoolBuffer` | calcul du layout decoder |
| 911 | `CreateVideoImagePool` | `CreateDecoderImage` |
| 912 | `DestroyVideoImagePool` | `DestroyNativeImage` pour le decoder |
| 961 | chaîne descriptor/query associée | `GetCpuUserImageDescriptor` et helpers associés |

🟢 **2026-11-26 — commandes 991/911/912 et helper de layout contrôlés.**

## 7.3 Layout 991 : formules différentes

### Encore

Pour NV12 :
- codes 1/4 ;
- dimensions paires requises ;
- pitch aligné à **256 octets** ;
- hauteur luma/chroma arrondie sur un petit multiple de lignes ;
- taille minimale et contrôles overflow ;
- total calculé à partir du nombre d'images.

Pour RGBA/BGRA :
- pitch aligné par pixels ;
- hauteur alignée à 128 ;
- stride d'image aligné à 8192.

### Lichii / Eglantine

Pour le layout decoder :
- NV12 codes 1/4 ;
- BGRA codes 2/5 ;
- autres codes courants → RGBA ;
- pitch aligné à **64 octets** ;
- plans alignés sur **128 lignes** ;
- le chroma NV12 commence après le plan luma aligné 128 lignes.

## 7.4 Exemple reproductible : NV12 1920×1080, count=1

| Valeur | Encore | Lichii/Eglantine |
|---|---:|---:|
| pitch | `0x800` = 2048 | `0x780` = 1920 |
| chroma offset | `0x21C000` | `0x21C000` |
| taille totale | **`0x32A000` = 3 317 760** | **`0x348000` = 3 440 640** |

**DIVERGENCE ABI/LAYOUT CONFIRMÉE.**

Le même chroma offset dans cet exemple est une coïncidence des deux alignements ; la taille de la seconde plane et le pitch restent différents.

Cela ne permet pas encore d'affirmer que l'une des formules est fausse pour le firmware/titre testé : il faut l'oracle de la requête réelle ou la taille attendue par le client. Mais si un des quatre titres atteint 991/911 juste avant le blocage, cette divergence passe immédiatement en tête de la liste P0.

## 7.5 911 / 912 : durée de vie

Encore ajoute une politique nettement plus stricte :
- contexte GPU prêt ;
- validation ownership du process ;
- validation NVMap/GMMU/backing ;
- pin de l'allocation ;
- IDs bornés et ledger ;
- destruction refusée si un mapping/ownership incompatible subsiste.

Lichii/Eglantine ont un registre decoder/native-image plus direct et une convention d'IDs partagée avec leur chaîne vidéo.

**Verdict : stratégies de durée de vie différentes ; aucun faux succès ne doit être ajouté uniquement pour imiter l'upstream.**

## 7.6 Référence indépendante nxnative

🟢 **2026-11-26 — nxnative `96f1f076` recontrôlé après changement de HEAD.**

`dm/host/hle_codec_video.c` blob `9b57466fd2a029c856c77d9a9cff7ced3aa1b28c` documente, à partir d'un SDK NS2 observé, la séquence :

**MakeDecodeImagePreference → CalculateDecoderImagePoolBuffer → InitializeDecoderImagePool → RegisterDecoderBuffer → Acquire/Release + sync handle.**

Il documente également un chemin CPU de lecture des images de decoder utilisé par un scénario de **Donkey Kong Bananza** plus tard dans le jeu.

Cette référence :
- **confirme la nature et la durée de vie du protocole** ;
- ne fournit pas à elle seule la preuve que le pitch Encore ou Lichii est le bon pour notre requête actuelle ;
- ne prouve pas que le freeze de boot actuel de DK est déjà dans cette chaîne vidéo.

## 7.7 Conclusion R-05

🟢 **2026-11-26 — R-05 contrôlé.**

**Candidat P0 très fort si le prochain log contient 991/911/912.**  
Le premier contrôle doit alors enregistrer les 16 mots de préférence, width/height/code/count et comparer la réponse calculée au comportement attendu du client.

---

# 8. R-06 — Audio NS2

La comparaison montre qu'il ne faut pas classer l'audio « P2 par principe ». Il reste non prioritaire **tant qu'aucun log ne l'implique**, mais contient une divergence capable de bloquer un thread de titre.

## 8.1 Propriétaire final et headers

Encore PS5 final :
- TU : `headless/r23_audren_debug_ps5.cpp` — blob `0fff4af935ad9b1b8afa34c953e70a16fb0310ad`;
- interface NS2 : `vendor/encore-active/ns2-runtime/audio/core/hle/service/audio/nx2_audio_user_client.h` — blob `18b5c47cc85fe803fe7540c1824bd49c59bf853d`.

Lichii :
- `src/core/hle/service/audio/audio.cpp` — `9d9e1e6093bf55bd686f42290575093299a79b7f`;
- `nx2_audio_user_client.h` — `cde05e5576315b87d06ade179bce3f56dcb3825d`.

Eglantine :
- `Eglantine/src/core/hle/service/audio/audio.cpp` — `b4c6b69c11bb5c48f4bd64c12d1e6243317525e4`;
- `nx2_audio_user_client.h` — **même blob que Lichii `cde05e...`**.

## 8.2 `aud:u` : table de commandes

| Commande | Encore | Lichii/Eglantine |
|---:|---|---|
| 0 | **absente** | `GetAudioInManager` |
| 1 | `GetAudioOutManager` | `GetAudioOutManager` |
| 2 | `GetAudioRendererManager` | `GetAudioRendererManager` |

**DIVERGENCE DE COUVERTURE CONFIRMÉE : cmd 0.**

## 8.3 Managers privés vs managers enregistrés

Lichii/Eglantine résolvent les managers `audin:u`, `audout:u`, `audren:u` déjà enregistrés dans le ServiceManager et renvoient ces objets partagés.

Leur code documente la raison : un second manager AudioOut peut posséder un autre `AudioCore::AudioOut::Manager`, alors que le callback de libération de buffers n'est pas prévu pour plusieurs propriétaires concurrents ; une session ouverte sur le mauvais manager peut donc ne plus recevoir les libérations attendues.

Encore, dans le header actif, crée de nouvelles interfaces `IAudioOutManager` / `IAudioRendererManager` avec `system` au lieu de rechercher systématiquement les instances déjà enregistrées.

**DIVERGENCE DE DURÉE DE VIE CONFIRMÉE — candidat P0 conditionnel.**

Il faut la traiter si les logs montrent :
- `aud:u` cmd 0 → Encore ne couvre pas le contrat ;
- cmd 1/2 puis queue de buffers qui ne se libère plus ;
- thread audio devenu le dernier progrès avant le freeze.

## 8.4 Sysmix / services

Encore possède bien :
- `aud:u`;
- `auddmg:u`;
- `audsmx:u`;
- Sysmix partagé ;
- `stpl:u`;
- services audio NS1 standards.

Il n'y a donc pas d'absence générale du sous-système audio.

## 8.5 Référence nxnative

La recherche sur nxnative HEAD confirme qu'un SDK moderne peut ouvrir `aud:u` **dès le démarrage d'un thread audio** pour certaines notifications de sortie. Une absence de service y a déjà produit un abort dans un autre titre/SDK.

Cette référence justifie de ne pas ignorer `aud:u` lorsqu'il apparaît dans un boot log, mais ne prouve pas que DK/MKW/Pokopia/Z-A utilisent actuellement la même commande.

## 8.6 Conclusion R-06

🟢 **2026-11-26 — R-06 contrôlé.**

Statut recommandé :
- **P0 conditionnel aux logs**, pas P2 automatique ;
- aucun patch audio aveugle tant que la trace du titre ne montre pas le chemin.

---

# 9. R-07 — HLE secondaires : LM / NIFM / ACC / AM / SM

Cette zone est comparée au niveau des tables de commandes et des contrats NS2 qui diffèrent réellement. Les milliers de lignes de comportement standard ne sont pas transformées en audit général sans signature.

## 9.1 LM

Blobs :
- Encore `9136cf19b1176e96fb17609fd401e4592028d1e2`;
- Lichii `06767375f5edd29dfea0296649b6770e7faab5da`;
- Eglantine `a7d6d6e707a2ca0598929777003833735bb28733`.

Les trois exposent :
- 0 Log ;
- 1 SetDestination ;
- 2 TransmitHashedLog ;
- 3 DevNotify ;
- 11 Unknown11 ;
- puis les interfaces de contrôle/logger associées.

Encore a désormais un handler explicite pour `TransmitHashedLog` au lieu du slot nul historique.

**Verdict : PARITÉ de couverture utile.**

## 9.2 NIFM

Blobs :
- Encore `8933817310ed1d3988e9ff418390a8b3e7e71a41`;
- Lichii `16f4b4cd31897e3c1b77407d38f103cc4a9e85e4`;
- Eglantine `d481e4a4b5d34600e2e7c2a09243e259c2082773`.

Les tables de commandes visibles sont alignées pour les familles principales :
- Request 0..26 ;
- GeneralService incluant IP, profils, wireless/ethernet, scan, télémétrie, disponibilité, emulation/rewrite ;
- création GeneralService 4/5.

Les corps diffèrent sur les politiques réseau/host, mais **aucun ID manquant général n'est démontré par cette comparaison**.

**Verdict : tables alignées ; ouvrir uniquement la commande exacte d'un log.**

## 9.3 ACC

Blobs :
- Encore `bda184c54aa81a037f7ff064554fe9557fff47bb`;
- Lichii `aec08c4d3171a96d70f95b4fd12490a76f3540de`;
- Eglantine `772da97ef6df84709bb14122ba333a7a34e5c133`.

Les grandes tables account/network-service couvrent les mêmes familles standard aux IDs comparés. Lichii contient des fonctions supplémentaires liées à son environnement de compte/redirect qui ne doivent pas être importées comme prérequis de boot Encore.

**Verdict : pas de manque générique ACC démontré.**

## 9.4 SM

Blobs :
- Encore `2ef914e3f1b24442e1fa0130d5f8175111e7d316`;
- Lichii `64bb27bf078816f650f8b6ce440cccb8755d9175`;
- Eglantine `406d6c902865e98ff174031ad080160877ed06f0`.

Les commandes fondamentales sont alignées :
- Initialize ;
- GetService ;
- Register/UnregisterService ;
- DetachClient ;
- commandes Atmosphère 65000..65101.

Les différences sont surtout les politiques de services/stubs NS2.

**Verdict : aucune divergence de table P0 générale.**

## 9.5 AM — `IApplicationProxy`

### Tables

Encore :
- 40 → **`GetPerformanceFunctions`** ;
- 50/70/80/90 → interfaces NS2 ;
- 60 → `GetGraphicsScalingParametersFunctions`.

Lichii/Eglantine :
- 40 → interface générique NS2 stub ;
- 50/70/80/90 → interfaces NS2 ;
- 60 → `GetGraphicsScaleController`.

### Cmd 40

Encore fournit une vraie interface `IPerformanceFunctions` avec au moins :
- 0 IsCpuOverclockEnabled ;
- 1 SetCpuOverclockEnabled.

Lichii/Eglantine renvoient leur interface générique.

**DIVERGENCE CONFIRMÉE, mais Encore est ici plus spécifique.**  
Ne pas la supprimer pour « ressembler » à l'upstream sans une requête incompatible observée.

### Cmd 60 / interface cmd 10

Le nom de classe diffère, mais le contrat a été vérifié :

Encore `graphics_scaling_parameters_functions.h` blob `bded1f902ac1a0995d71ffc3f425f33ba781b198`.

Lichii/Eglantine `graphics_scale_controller.h` : blob commun `61cb11df99c429fadc1415f0a460f8efcae0b5f8`.

Les trois :
- exposent cmd 10 ;
- renvoient **trois u32** ;
- valeur = `10, 0, 0`;
- exposent cmd 1050 pour l'activation de notification de changement.

**Verdict : PARITÉ ABI malgré le nom de classe différent.**

## 9.6 Conclusion R-07

🟢 **2026-11-26 — R-07 contrôlé sur les cinq familles demandées.**

Il n'y a pas de justification pour un nouvel audit HLE général. Les différences exploitables sont désormais localisées ; la suite se fait par **service + command ID du log**.

---

# 10. R-08 — FC27 : Maxwell shader / pipeline détaillé

Le but ici n'est pas de prétendre que toutes les saccades FC27 viennent des shaders, mais de comparer la chaîne réellement utilisée.

## 10.1 Propriétaires Vulkan comparés

| Dépôt | Pipeline cache | Blob |
|---|---|---|
| Encore | `encore-active/eden-vulkan/vk_pipeline_cache_cost.cpp` | `61450e8b8c5e76a59660649ed13941eb50e089cb` |
| Lichii | `src/video_core/renderer_vulkan/vk_pipeline_cache.cpp` | `6d05f1e86b22e4432c562bcff5c488e7583e5323` |
| Eglantine | `Eglantine/src/video_core/renderer_vulkan/vk_pipeline_cache.cpp` | `19356e9ef9a21b3ba902c11d2c2ae80d28f0ebd4` |

🟢 **2026-11-26 — slow path et création de graphics pipeline comparés.**

## 10.2 `CurrentGraphicsPipelineSlowPath`

### Encore

Encore :
- insère la clé à la première utilisation ;
- traduit le shader invité/SPIR-V au cold miss ;
- mesure explicitement les coûts PS5 ;
- conserve une politique de retry unique et retardé pour un pipeline ayant échoué ;
- borne les métadonnées de retry ;
- trace la première utilisation par hash lorsque l'observabilité est active.

### Eglantine

Eglantine possède :
- scheduled prebuild ;
- classification stutter trace ;
- récupération de pointeur d'une entrée évincée ;
- sauvegarde des pipelines utilisés ;
- `MarkUsed(frame_count)`.

### Lichii actuel

Lichii va plus loin :
- prebuild prêt / attente mesurée ;
- skip de certains mesh draws en attente ;
- récupération/rebuild depuis stages conservés ;
- suivi des évictions et retranslations ;
- sauvegarde et cycle de vie plus développés.

**DIVERGENCE ARCHITECTURALE CONFIRMÉE.**

Ce n'est pas un backport automatique : Encore a des contraintes PS5 et de snapshots guest spécifiques.

## 10.3 Traduction parallèle

Encore a une adaptation propre :
- snapshot immuable du TIC ;
- snapshot des CBUFs nécessaires ;
- pools privés par stage ;
- worker translation puis join contrôlé ;
- repli séquentiel si le snapshot n'est pas admissible ;
- la chaîne NS2 native reste séparée lorsque l'authentification/GMMU l'impose.

Lichii/Eglantine utilisent leur infrastructure `StageTranslation` / jobs shader plus générale.

**Verdict : stratégies différentes ; comparer les temps/hash, pas seulement le nombre de workers.**

## 10.4 Fragment shader « broken pattern »

Les trois arbres connaissent `HasBrokenPattern`.

Lichii/Eglantine au SHA comparé peuvent **sauter le pipeline** sur un driver non NVIDIA lorsqu'un motif connu est détecté.

Encore PS5 a explicitement modifié ce comportement dans le pipeline maintenu : au lieu de supprimer silencieusement le draw, il active un fallback SPIR-V ciblé pour les motifs concernés.

**Verdict : HARDENING fidélité Encore / divergence volontaire.**

## 10.5 Maxwell translator

La fonction `TranslateProgram` existe dans les trois chaînes et normalise les capacités hôte avant les passes.

Différence notable de génération actuelle :
- Lichii/Eglantine ont fait évoluer `MergeDualVertexPrograms` avec un `HostTranslateInfo` supplémentaire et utilisent leur infrastructure de translation parallèle ;
- Encore conserve son fork `eden-shader` et installe sélectivement des TU/headers maintenus via CMake afin de garder l'ABI cohérente avec le pipeline PS5 ;
- le moteur Encore sélectionne également un TU F2I R23 PS5 spécifique et un `vendor_workaround_pass.cpp` maintenu.

Cela confirme qu'un diff « copier tout `shader_recompiler/` depuis Lichii » serait dangereux : les interfaces et les propriétaires actifs ne sont plus identiques.

## 10.6 Ce qu'il faut pour relier cela à FC27

Pour passer de « divergence » à « cause P1 » il faut au moins :

| Preuve | Nécessaire |
|---|---|
| même scène FC27 | oui |
| mêmes SHAs moteur/vendor | oui |
| pipeline hash / shader hash | oui ou signature équivalente précise |
| cold/warm cache | oui |
| frametime associé | oui |
| résultat visuel/HUD associé si défaut d'image | oui |
| fonction de traduction/création identifiée | oui |

Sans cela, le différentiel shader reste une **carte de navigation**, pas une correction.

## 10.7 Conclusion R-08

🟢 **2026-11-26 — R-08 contrôlé au niveau architecture pipeline/cache/translation.**

Lichii actuel a davantage de mécanismes de prebuild/eviction/rebuild ; Encore possède en contrepartie des snapshots PS5, des fallbacks fidélité et des substitutions ABI spécifiques. Le prochain travail doit être **hash-ciblé**.

---

# 11. Matrice des divergences confirmées

Cette section sépare les différences réellement trouvées des simples zones ouvertes.

| Réf | Divergence confirmée | Niveau | Ce qui la rend causale |
|---|---|---|---|
| D-01 | C797/C7C0/C7B5 : upstream alias legacy, Encore conserve identité Ampere + registry native | architecture GPU | méthode/engine du log se bloque dans le chemin Encore |
| D-02 | Sémaphore Ampere : upstream continue sur acquire non satisfait, Encore parque/refuse la progression | synchronisation GPU | pending acquire observé + producer/release absent ou faux |
| D-03 | formats inconnus : Lichii/Eglantine ont `TryPixelFormat...` fail-closed pour blits ; Encore fallback générique hors garde NONE | fidélité/copie | format non nul inconnu effectivement utilisé par la ressource fautive |
| D-04 | GSV decoder layout 991 : pitch/alignements/taille différents | ABI vidéo | 991/911 atteint et client rejette/écrit selon autre layout |
| D-05 | `aud:u` cmd0 absent dans Encore | HLE audio | titre appelle cmd0 |
| D-06 | `aud:u` cmd1/2 : managers privés Encore vs managers enregistrés Lichii/Eglantine | durée de vie audio | buffers/session se bloquent après ouverture |
| D-07 | AM cmd40 : vraie interface performance Encore vs stub générique upstream | HLE AM | commande interne incompatible observée |
| D-08 | pipeline/cache Maxwell : politiques prebuild/eviction/rebuild différentes | performance P1 | hash/scène FC27 montre le stall dans ce chemin |

Aucune ligne de cette table ne signifie « bug résolu » ni « bug démontré sur PS5 ».

---

# 12. Parités/hardenings confirmés — à ne pas re-auditer sans nouvel indice

| Réf | Contrat | Résultat |
|---|---|---|
| P-01 | Host1x CDMA dispatch principal | parité + bornage méthodes Encore |
| P-02 | Host1x Control teardown | stop token Encore supplémentaire |
| P-03 | NVDEC classique H264/VP8/VP9 | parité fonctionnelle principale |
| P-04 | KThread FinishTermination | parité : Close hors scheduler lock |
| P-05 | KScheduler SwitchThread | parité runtime ; stats upstream seulement |
| P-06 | WaitSynchronization | parité + overflow saturation Encore |
| P-07 | LM command table | parité utile |
| P-08 | NIFM command table principale | parité de couverture |
| P-09 | SM command table fondamentale | parité |
| P-10 | AM graphics scale cmd60→cmd10 | parité ABI `10,0,0` |
| P-11 | native tiling général software blitter Encore | présent ; pas un trou global |

Ces contrôles doivent éviter de refaire les mêmes études au prochain cycle.

---

# 13. Ordre de diagnostic dérivé de cette comparaison

Pour les quatre titres NS2 actuellement sans première frame stable, l'ordre n'est plus « auditer les huit zones » mais :

1. **Lire le dernier progrès réel dans le log.**
2. Si `C797/C7C0/C7B5` ou SEM_EXECUTE apparaît : ouvrir **R-02** à la méthode exacte.
3. Si `gsv 991/911/912` apparaît : ouvrir **R-05** immédiatement et comparer les 16 mots de préférence/layout.
4. Si `aud:u` apparaît : ouvrir **R-06**, surtout cmd 0/1/2 et ownership du manager.
5. Si un SVC wait domine : ouvrir **R-04** avec l'objet attendu, pas le scheduler en entier.
6. Si première frame mais image incorrecte : ouvrir **R-03** sur le format/copie exacte.
7. Si service HLE secondaire : ouvrir **R-07** uniquement avec service + cmd.
8. Pour FC27 : ouvrir **R-08** seulement avec pipeline/shader hash ou scène A/B.

---

# 14. Contrôles datés inscrits dans ce document

| Date | Zone | Contrôle réellement réalisé | Révisions |
|---|---|---|---|
| 🟢 2026-11-26 | BASE | HEAD moteur, gitlink vendor, vendor/main | moteur `64e1a743`, vendor `9de08e4f` |
| 🟢 2026-11-26 | SOURCES | CMake/overlays GPU, Fermi2D, Vulkan, audio R23 | moteur `64e1a743` |
| 🟢 2026-11-26 | R-01 | CDMA, Control, NVDEC, VIC | vendor `9de08e4f`, Lichii `0288882f`, Eglantine `75a552ff` |
| 🟢 2026-11-26 | R-02 | bind C797/C7C0/C7B5, dispatch, sémaphores | mêmes SHAs |
| 🟢 2026-11-26 | R-03 | Fermi2D, software blitter, surface formats | mêmes SHAs |
| 🟢 2026-11-26 | R-04 | KThread, KScheduler, WaitSynchronization | mêmes SHAs |
| 🟢 2026-11-26 | R-05 | 991/911/912 + layout + nxnative codec protocol | + nxnative `96f1f076` |
| 🟢 2026-11-26 | R-06 | audio owner final, aud:u, managers + référence nxnative | mêmes SHAs |
| 🟢 2026-11-26 | R-07 | LM/NIFM/ACC/SM/AM tables + graphics scale ABI | mêmes SHAs |
| 🟢 2026-11-26 | R-08 | pipeline cache, slow path, translation Maxwell | mêmes SHAs |

**La pastille verte certifie le contrôle de source/contrat, pas une validation CI/build/console.**

---

# 15. État de validation

## A — Correctifs C++ runtime

**Aucun correctif C++ n'est introduit par ce document.**

Les divergences D-01 à D-08 sont maintenant suffisamment localisées pour guider un correctif ultérieur, mais aucune n'est corrigée « par ressemblance » sans trace causale.

## B — Tests / CI / build / console

- Aucun test hôte nouveau lancé pour cette passe documentaire.
- Aucun build natif PS5 déclenché.
- Aucune nouvelle installation console.
- Aucune première frame NS2 revendiquée.
- Aucun gain FC27 revendiqué.

## C — Anomalies réellement ouvertes après comparaison

Priorité conditionnelle la plus élevée :

1. **GSV 991/911 layout decoder** si ces commandes apparaissent dans les logs.
2. **Ampere semaphore / C797 / C7C0** si le dernier progrès GPU se situe là.
3. **`aud:u` cmd0 ou manager privé** si la chaîne audio intervient avant le blocage.
4. **format non nul inconnu en blit** si une ressource fautive le montre.
5. **pipeline/shader FC27** uniquement par hash/scène.

## D — Travail périphérique

La documentation seule ne vaut aucun progrès gameplay. Son utilité est de fermer les faux « trous généraux » et de réduire le prochain diagnostic à quelques divergences concrètes, vérifiables sur la trace PS5.

---

# 16. Règle de continuité

À chaque nouveau test console :

- inscrire Title ID + SHA moteur/vendor ;
- rattacher le dernier progrès à R-01..R-08 ou au comparatif principal ;
- ajouter 🟢 + date uniquement après contrôle réel du contrat ;
- si une divergence devient causale, documenter **symptôme → log → fonction → upstream → patch → tests → build → résultat console** ;
- ne jamais remplacer une attente GPU par un succès silencieux, un layout par une supposition ou un manager par un stub uniquement pour « passer plus loin ».

**Objectif final : première soumission GPU puis première frame invitée réelle pour NS2, et pour FC27 une cadence/fidélité mesurées — pas un score de complétude documentaire.**
