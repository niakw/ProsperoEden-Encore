# Eden Encore — Registre NS1 de couverture fonctionnelle SwitchBrew

> **Objet :** disposer d'un registre NS1 vivant, lisible comme les tables SwitchBrew, qui permette de répondre rapidement à : *cette fonction/commande existe-t-elle ? est-elle réellement implémentée ? seulement enregistrée ? stub ? partielle ? testée ? quand et sur quel propriétaire ?*
>
> **Dernière mise à jour : 22 novembre 2026 (qualification source ; snapshot historique du 21/11 conservé).**
>
> **Branche de qualification source actuelle :** `audit/ns1-switchbrew-main-coverage-20261122` (l'ancienne branche `opt/ns1-fc27-runtime-20261121` reste la provenance des snapshots du 21/11).
>
> **Annexe exhaustive d'indexation du miroir historique SwitchBrew :** [catalogue API NS1 (117 SVC + 4 786 lignes IPC)](./EDEN_ENCORE_NS1_SWITCHBREW_API_COVERAGE_2026-11-21.md). Le catalogue liste les identifiants pour recherche et fournit **33 D / 3 P / 80 Q / 1 E** pour les SVC examinés et **68 D / 19 P / 4 699 Q** pour les lignes IPC du snapshot. Ces codes sont des **constats de source de base non qualifiés PS5** : ils ne supplantent jamais les statuts d'owner actif/firmware/reçus du présent registre, qui reste la **source canonique unique**.
>
> **Snapshot initial :** moteur `5bef0df2b23f650b470659e928e3682cf2db3916` → vendor/gitlink `b8883667410054db189d00b3a5144088f47d3af9`.
>
> Ce document est un **registre de couverture**, pas une preuve de compatibilité console. Une ligne « implémentée source » ne devient « validée PS5 » qu'après un test représentatif.

> **Point source final du 22/11 — branche d’audit `audit/ns1-switchbrew-main-coverage-20261122` :** le [catalogue NS1 détaillé](./EDEN_ENCORE_NS1_SWITCHBREW_API_COVERAGE_2026-11-21.md) est désormais **entièrement classé au niveau documentaire/source sur le couple moteur `452fd7fe` → vendor/gitlink `224b05e6`** : **1 207 IMPL-SRC (1 127 IPC + 80 SVC) / 4 853 entrées distinctes**, **76 PARTIEL**, **347 STUB**, **6 NOOP**, **2 278 NULL**, **55 D**, **173 INACCESSIBLE**, **289 SERVICE-NON-EXPOSÉ**, **126 ABSENT**, **283 ABI-DIFF**, **12 AMBIGU**, **1 E**. **Q = 0 et RACCORDÉ = 0.** Cela signifie que chaque entrée possède maintenant une classification explicite ; cela ne signifie ni conformité ABI exhaustive, ni validation runtime, ni validation PS5. Aucun C++ runtime n'a été modifié pour obtenir ce compteur.

## Lot runtime secondaire NS1 — 22/11/2026

**Couple modifié sur `audit/ns1-switchbrew-main-coverage-20261122` :** moteur `89d7b406a6ee5429f985c1277eeb9653043e7c80` (gitlink) → vendor `fe5a389ac04fa3c26c1756fc18e73a962e196da4` (GPIO/NCM/SVC). Commit documentaire ultérieur : voir HEAD de branche.

| Catégorie du catalogue | Avant (snapshot) | Après ce lot | Changement justifié |
|---|---:|---:|---|
| IMPL-SRC | 1 207 | **1 213** | 6 handlers NCM `IContentStorage` avec `PlaceholderCache`, dont listing borné IPC et lecture du Rights ID |
| PARTIEL | 76 | **76** | `svcGetThreadList` refuse le handle debug au lieu de retourner les threads du mauvais processus, mais ne gère pas ce mode |
| STUB | 347 | **347** | Aucun stub existant n'est proclamé pleinement implémenté |
| NOOP | 6 | **6** | Politique inchangée |
| NULL | 2 278 | **2 278** | Aucune conversion aveugle en succès |
| D — rejet explicite | 55 | **65** | 10 commandes GPIO racine présentes et rejetées explicitement |
| INACCESSIBLE | 173 | **191** | 18 commandes `IPadSession` sans objet de session retournable |
| SERVICE-NON-EXPOSÉ | 289 | **289** | Inchangé |
| ABSENT | 126 | **92** | 6 NCM implémentées, 10 GPIO rejetées, 18 GPIO inaccessibles |
| ABI-DIFF | 283 | **283** | Non présumé résolu |
| AMBIGU | 12 | **12** | Non présumé résolu |
| ID SVC absent | 1 | **1** | Non présumé résolu |
| **Total** | **4 853** | **4 853** | **Zéro entrée non classée** |

**Code actif et contrat :** les sources `sources/eden/src/core/hle/service/gpio/gpio.cpp`, `sources/eden/src/core/hle/service/ncm/ncm.cpp` et `sources/eden/src/core/hle/kernel/svc/svc_thread.cpp` sont listées par `encore-active/eden-backports/src/core/CMakeLists.txt`, sans remplacement portant le même chemin dans le manifeste d'overlays. `GPIO` renvoie `Kernel::ResultNotImplemented` (aucun faux contrôleur). NCM utilise les opérations existantes `Exists`, `CleanAll`, `SetSize`, `Size`, avec erreur en l'absence du cache et protection contre une taille négative. La commande 19 lit `PlaceholderCache::GetRightsID` et rejette explicitement un NCA sans Rights ID exploitable. La commande 11 liste les placeholders réels via `List` en limitant les copies à la taille du buffer IPC. Dans `encore-active/eden-backports/src/core/hle/service/filesystem/fsp/fsp_srv.cpp` (owner natif listé par CMake), `OpenFileSystemWithPatch` retourne désormais des erreurs FS si type non supporté ou RomFS indisponible, plutôt que d'assert et terminer le processus ; le statut demeure PARTIEL. Les numéros/ABI NCM sont recroisés avec [SwitchBrew NCM](https://switchbrew.org/wiki/NCM_services).

**Validation :** uniquement inspection statique et rapprochement CMake/manifeste pour le premier lot ; **aucun build natif, installation ou validation PS5**. La CI de provenance du premier lot a ensuite signalé un écart de hash FSP, corrigé par vendor `e329e52f` et moteur `c3a0e0ff`, sans changement de sémantique FSP. Ne pas le présenter comme un progrès FC27 mesuré. Les 92 ABSENT restants comportent des interfaces utiles et des fonctions hors périmètre ; la réduction du nombre d'ABSENT ne remplace pas le tri par Title ID/log.

## Lot suivant — CAPS vidéo explicite et NCM sans cache Rights ID (22/11/2026)

**Vendor `ff0822695ec03ac7d9d2c75b4703adf12eec544f` sélectionné par le nouveau gitlink de la branche secondaire moteur.** Les trois unités `caps_a.cpp`, `caps_c.cpp` et `caps_u.cpp` de `sources/eden/src/core/hle/service/caps/` figurent dans `encore-active/eden-backports/src/core/CMakeLists.txt` et ne sont pas supplantées par le manifeste `eden-backports`. **34 fonctions de flux vidéo album** ont été enregistrées explicitement comme `nullptr` : l'émulateur ne propose pas cette fonction, et aucun succès factice n'est renvoyé. Cette politique est une exclusion fonctionnelle, **pas** une implémentation de lecture/écriture de films. En parallèle, le seul nouveau handler NCM `InvalidateRightsIdCache` (ID 13) est un **NOOP documenté** : les Rights IDs sont recalculés sur lecture du NCA, et ne possèdent actuellement aucun cache logiciel à invalider.

**Nouveau compteur sur 4 853 :** IMPL-SRC **1 213**, PARTIEL **76**, STUB **347**, NOOP **7**, NULL **2 311**, D **65**, INACCESSIBLE **191**, SERVICE-NON-EXPOSÉ **289**, ABSENT **58**, ABI-DIFF **283**, AMBIGU **12**, E **1**. Q et RACCORDÉ restent nuls. Les **34 ABSENT devenus NULL** et l'unique **NULL devenu NOOP** ne sont pas assimilés à des gains de jouabilité ni à une couverture fonctionnelle de capture.

**CI/console :** le [run #45036307129](https://github.com/niakw/ProsperoEden-Encore/actions/runs/45036307129) a échoué sur l'empreinte FSP ; la correction exacte du manifeste a été commise au vendor `e329e52f` et intégrée au moteur `c3a0e0ff`. Nouveau lot CAPS/NCM : code source inspecté et commits effectués ; les verdicts des nouveaux runs restent à relever. **Pas de compilation C++ de ce lot ni de validation PS5 annoncée.**

## Lot NCM content storage — 22/11/2026

**Couple : moteur repointé vers vendor `c3dc80c83d468e04c794b3d7d36bc1316b342bd4`.** Le chemin PS5 réellement sélectionné pour `registered_cache.cpp` est `encore-active/eden-core/src/core/file_sys/registered_cache.cpp`, avec `encore-active/eden-core/include` prioritaire pour le header. Les copies de base ont reçu la même ABI pour préserver les builds hôtes.

Cinq commandes `IContentStorage` passent **ABSENT → IMPL-SRC** : `Has` (7), `GetContentCount` (12), `ListContentId` (13), `GetSizeFromContentId` (14), `GetRightsIdFromContentId` (20). Deux passent **ABSENT → NOOP** : `FlushPlaceHolder` (24) et `RepairInvalidFileAttribute` (26), avec justification VFS explicite. `GetRightsIdFromPlaceHolderId` conserve son statut implémenté mais renvoie désormais les 24 octets HOS 3+ avec génération de clé réelle.

**Compteur courant : 1 218 IMPL-SRC / 76 PARTIEL / 347 STUB / 9 NOOP / 2 311 NULL / 65 D / 191 INACCESSIBLE / 289 SERVICE-NON-EXPOSÉ / 51 ABSENT / 283 ABI-DIFF / 12 AMBIGU / 1 E = 4 853.** Le run de provenance précédent `#45044777362` est vert sur `c287ac44`; ce nouveau lot devra être qualifié sur son propre HEAD. Pas de validation PS5 annoncée.


## Lot NCM capacité / lifecycle — 22/11/2026

Vendor `60bd03e6e5ad083ee050887028fa33d514a3050e` : `GetFreeSpaceSize` et `GetTotalSpaceSize` sont raccordés aux capacités du `FileSystemController`; `DisableForcibly` est NOOP documenté ; `GetRightsIdFromPlaceHolderIdWithCache` est PARTIEL car la donnée Rights ID/keygen est réelle mais le cache hint firmware est ignoré.

**Compteur courant : 1 220 IMPL-SRC / 77 PARTIEL / 347 STUB / 10 NOOP / 2 311 NULL / 65 D / 191 INACCESSIBLE / 289 SERVICE-NON-EXPOSÉ / 47 ABSENT / 283 ABI-DIFF / 12 AMBIGU / 1 E = 4 853.** Aucun résultat PS5 n'est déduit de ces handlers.


## Requalification finale des ABSENT non exécutables — 22/11/2026

Les 17 lignes migration passent à **SERVICE-NON-EXPOSÉ** (`mig:user` enregistré, pas `mig:usr`), l'ancien audio ID 13 passe à **ABI-DIFF**, et les 6 événements Time 30/31 passent à **HORS-VERSION** (6.0.0–8.1.0, cible HOS 23).

**Compteur courant : 1 220 IMPL-SRC / 77 PARTIEL / 347 STUB / 10 NOOP / 2 311 NULL / 65 D / 191 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 6 HORS-VERSION / 23 ABSENT / 284 ABI-DIFF / 12 AMBIGU / 1 E = 4 853. Les 23 ABSENT réels sont 22 NCM + 1 NS Attach.**

## Lot NCM lecture / revert — 22/11/2026

Vendor `488475c8c3867af07892a7f53cc6e15a54d09542` : `RevertToPlaceHolder` et `ReadContentIdFile` passent **ABSENT → IMPL-SRC** sur le stockage réel ; `WriteContentForDebug` passe **ABSENT → D** car réservé au matériel de développement et rejeté explicitement sur Encore.

**Compteur courant : 1 222 IMPL-SRC / 77 PARTIEL / 347 STUB / 10 NOOP / 2 311 NULL / 66 D / 191 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 6 HORS-VERSION / 20 ABSENT / 284 ABI-DIFF / 12 AMBIGU / 1 E = 4 853.** Les deux fonctions de chemins NCM restent ouvertes : un chemin hôte PS5 ne doit pas être présenté comme un chemin `fscommon` Horizon.

## Lot ContentMetaDatabase CNMT — 22/11/2026

Vendor `8d1d9eac331b2b8db218617edff7aa4425503a95` : huit commandes auparavant ABSENT interrogent maintenant les CNMT réels du cache enregistré ; `DisableForcibly` devient NOOP. `Has` vérifie désormais le ContentMetaKey complet (id/version/type/install type) au lieu d'un simple Meta NCA par title ID.

**Compteur courant : 1 230 IMPL-SRC / 77 PARTIEL / 347 STUB / 11 NOOP / 2 311 NULL / 66 D / 191 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 6 HORS-VERSION / 11 ABSENT / 284 ABI-DIFF / 12 AMBIGU / 1 E = 4 853.** Restent réellement ABSENT : NCM `GetPath`/`GetPlaceHolderPath`, huit commandes ContentMetaDatabase complexes (`Get`, `List`, latest/list application, size/versions/patch) et NS `Attach`.

## Lot ContentMetaDatabase complet / CNMT — 22/11/2026

Vendor `22e47d3b88d669048a4460b0e8b0a9d315f4ca22` : `Get`, `List`, latest key, application list, size, versions et Patch/DataPatch IDs utilisent désormais les valeurs ContentMeta réelles. `Set` conserve le buffer fourni et le chemin installé convertit le CNMT packagé vers le format ContentMeta normal (Meta NCA inclus).

Le parser `nca_metadata.cpp` conserve l'en-tête étendu complet et corrige le début des `MetaRecord` : `sizeof(CNMTHeader) + table_offset + content_count * sizeof(ContentRecord)`. Cette correction sert directement `ListContentMetaInfo` et les relations de métadonnées.

**Compteur courant : 1 238 IMPL-SRC / 77 PARTIEL / 347 STUB / 11 NOOP / 2 311 NULL / 66 D / 191 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 6 HORS-VERSION / 3 ABSENT / 284 ABI-DIFF / 12 AMBIGU / 1 E = 4 853.** Restent ABSENT : NCM `GetPath`, `GetPlaceHolderPath`, NS `Attach`. Validation PS5 toujours absente.

## Clôture du statut ABSENT — 22/11/2026

Vendor `b9e23460efcf82c3f3e86de303f9a27568004b24` : `GetPath` et `GetPlaceHolderPath` passent en **D / rejet explicite**, faute d'abstraction `fs-common path` Horizon ; aucun chemin hôte n'est substitué. Le supposé `NS IServiceGetterInterface::Attach` cmd 0 passe en **ABI-DIFF** : la référence SwitchBrew actuelle commence à 7988 et correspond à la table Eden 7988–7999.

**Compteur courant : 1 238 IMPL-SRC / 77 PARTIEL / 347 STUB / 11 NOOP / 2 311 NULL / 68 D / 191 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 6 HORS-VERSION / 0 ABSENT / 285 ABI-DIFF / 12 AMBIGU / 1 E = 4 853.** `ABSENT=0` clôt seulement la catégorie « commande non classée/non raccordée », pas la complétude fonctionnelle.

Le palier moteur `bec0f030` → vendor `22e47d3b` a passé NS1 X8D24 et `Verify pinned vendor` avant ce repointage. Le nouveau vendor doit encore être qualifié sur son propre HEAD ; aucune validation PS5 n'est revendiquée.

---

## 1. Références et règle de vérité

Référence fonctionnelle principale :

- SwitchBrew **Services API** : https://switchbrew.org/wiki/Services_API
- SwitchBrew **SVC** : https://switchbrew.org/wiki/SVC
- Catégorie des services : https://switchbrew.org/wiki/Category:Services
- SwIPC historique : https://github.com/reswitched/SwIPC — utile pour les signatures/IDs anciens, **mais figé autour des firmwares 3.x et jamais utilisé seul pour conclure sur 23.x**.
- libnx / Atmosphère servent de contre-vérification client/kernel lorsque SwitchBrew laisse une signature ou une évolution ambiguë.

Pour Eden Encore, la vérité n'est **jamais** « un fichier portant le bon nom existe ». L'ordre est :

1. source réellement sélectionnée par CMake pour le binaire natif PS5 ;
2. handler effectivement enregistré pour l'ID IPC/SVC ;
3. corps du handler : implémentation, valeur fixe, stub, fail-closed, objet/handle/event réellement retourné ;
4. version firmware à laquelle la commande s'applique ;
5. test hôte proportionné ;
6. validation PS5 représentative.

Les sources `vendor/sources/eden` sont l'entrée épinglée. Les remplacements `vendor/encore-active/*`, les backports R23 et les overlays générés par CMake peuvent devenir les propriétaires réellement compilés ; la colonne **Owner actif** doit donc être réévaluée à chaque changement de gitlink/CMake.

## 2. Légende de statut

| Code | Signification |
|---|---|
| **OK-PS5** | comportement validé sur console dans un scénario représentatif et couple de SHAs indiqué |
| **OK-HOST** | handler réel + test hôte/CI pertinent ; console non qualifiée |
| **SRC** | handler réel présent dans le propriétaire actif, sans preuve comportementale suffisante |
| **PARTIEL** | une partie du contrat est implémentée ; flags, variantes firmware, handles, buffers, erreurs ou états restent incomplets |
| **STUB** | handler existe mais renvoie une valeur fixe, succès factice, résultat minimal ou ne reproduit pas le contrat |
| **NULL** | commande enregistrée avec `nullptr` / explicitement non implémentée |
| **ABSENT** | commande/interface SwitchBrew connue mais non trouvée dans le propriétaire actif |
| **N/A** | commande hors NS1 retail / firmware hors périmètre |
| **?** | non qualifié : ne pas conclure |
| **SB-CURRENT** | ligne recroisée avec SwitchBrew actuel le 21/11/2026 |
| **SWIPC-HIST** | ligne issue de SwIPC historique ; vérifier SwitchBrew avant correction |

### Règle importante

`FunctionInfo { id, &Class::Method, "Name" }` signifie seulement **« handler raccordé »**. Cela ne suffit pas à classer **OK-HOST**. À l'inverse, un `nullptr` est un écart source explicite pour cette commande, sans prouver qu'un jeu l'appelle.

## 3. Métadonnées d'une ligne

Chaque ligne détaillée utilise :

| Champ | Contenu |
|---|---|
| Famille / service | nom SwitchBrew (`hid`, `fsp-srv`, `acc:u0`, etc.) |
| Interface | nom SDK/IPC si connu |
| Cmd/SVC | identifiant numérique |
| Fonction SwitchBrew | nom courant, avec plage firmware si nécessaire |
| Statut Encore | un code de la légende |
| Owner actif | fichier C++ réellement sélectionné ou propriétaire à qualifier |
| Handler Encore | méthode ou `nullptr` |
| Depuis / jusqu'à | versions HOS documentées |
| Dernière revalidation | date + SHAs moteur/vendor |
| Preuve | test/CI/console ou raison du statut |
| Notes | sémantique manquante, risque, jeu/log connu, upstream pertinent |

## 4. Référentiel actuel SwitchBrew à suivre

Ces pages sont les références de commande actuelles pour les familles les plus importantes au boot et au gameplay NS1 :

| Domaine | Référence |
|---|---|
| SM | https://switchbrew.org/wiki/Services_API#sm: |
| Kernel/SVC | https://switchbrew.org/wiki/SVC |
| Account | https://switchbrew.org/wiki/Account_services |
| HID/HIDBUS | https://switchbrew.org/wiki/HID_services |
| Applet Manager | https://switchbrew.org/wiki/Applet_Manager_services |
| Filesystem | https://switchbrew.org/wiki/Filesystem_services |
| NS/AOC | https://switchbrew.org/wiki/NS_services |
| Sockets/DNS | https://switchbrew.org/wiki/Sockets_services |
| SSL | https://switchbrew.org/wiki/SSL_services |
| Audio/Opus | https://switchbrew.org/wiki/Audio_services |
| Settings | https://switchbrew.org/wiki/Settings_services |
| Nvnflinger/VI | https://switchbrew.org/wiki/Nvnflinger_services ; https://switchbrew.org/wiki/VI_services |
| NVDRV | https://switchbrew.org/wiki/NV_services |
| LDN | https://switchbrew.org/wiki/LDN_services |
| NIFM | https://switchbrew.org/wiki/Network_Interface_services |
| NCM | https://switchbrew.org/wiki/NCM_services |
| NIM | https://switchbrew.org/wiki/NIM_services |
| NFC/NFP | https://switchbrew.org/wiki/NFC_services |
| Loader | https://switchbrew.org/wiki/Loader_services |
| Process Manager | https://switchbrew.org/wiki/Process_Manager_services |
| PTM/APM/PSM | https://switchbrew.org/wiki/PTM_services |
| USB | https://switchbrew.org/wiki/USB_services |
| BCAT | https://switchbrew.org/wiki/BCAT_services |
| Capture | https://switchbrew.org/wiki/Capture_services |
| Error report | https://switchbrew.org/wiki/Error_Report_services |
| Log | https://switchbrew.org/wiki/Log_services |
| Fatal | https://switchbrew.org/wiki/Fatal_services |
| NGC / StreamPlay | https://switchbrew.org/wiki/NGC_services |
| OLSC | https://switchbrew.org/wiki/OLSC_services |

## 5. Écarts firmware récents à ne pas perdre

Cette section évite qu'un inventaire historique SwIPC fasse croire à tort que la couverture est complète.

| Référence actuelle | Version | Constat Encore initial |
|---|---:|---|
| `stpl:u`, `stpl:sys` | NS1 **23.0.0+** | backport R23 sélectionné dans le graphe PS5 ; commandes détaillées à maintenir ci-dessous |
| NS application manager / qlaunch | **23.5.0+** | backport R23 FW23.5 sélectionné ; les nouveaux IDs doivent rester distingués des commandes historiques |
| HID/HIDBUS | jusqu'à **23.x** | plusieurs commandes 19–23.x n'existent pas dans SwIPC historique ; SwitchBrew actuel prime |
| AudioRenderer | NS1 **23.0.0+** | commande 14 `SetAsyncMemoryPoolControlEnabled` à vérifier séparément |
| Mii | NS1 **23.0.0+** | commandes 27/28 renommées/évoluées ; ne pas se fier aux noms SwIPC seuls |
| Error Report | **23.0.0+** | interfaces/namespaces et certaines commandes ont changé |
| SVC | 13.x–23.x | plusieurs SVC modernes ne figurent pas dans les vieilles matrices SwIPC ; utiliser la table SwitchBrew SVC courante |

## 6. Scorecard source — snapshot initial 21/11/2026

> Les nombres ci-dessous comptent les entrées `FunctionInfo` dans le **propriétaire inspecté**, pas nécessairement toutes les sous-interfaces d'une famille. Ils servent à localiser les trous, pas à calculer un « pourcentage de compatibilité jeu ».

| Famille / owner inspecté | Entrées | Handlers raccordés | `nullptr` | Dernière modif owner | Lecture immédiate |
|---|---:|---:|---:|---|---|
| HID system — `eden-backports/.../hid_system_server.cpp` | **240** | **54** | **186** | 30/10/2026 | couverture très fragmentaire ; nombreuses fonctions système/calibration/firmware absentes |
| HID user extra table — `sources/eden/.../hid_server.cpp` | **68** | **0** | **68** | 30/10/2026 | table d'extensions entièrement NULL ; ne pas confondre avec les autres owners HID |
| HIDBUS — table inspectée | **1** | **0** | **1** | 30/10/2026 | `GetPollingData` NULL dans cette table |
| FSP-SRV R23 — `eden-backports/.../fsp_srv.cpp` | **128** | **36** | **92** | **11/11/2026** | fonctions de base/save-data partiellement couvertes ; large surface admin/debug absente |
| IStorage | **6** | **2** | **4** | 30/10/2026 | Read/GetSize réels ; Write/Flush/SetSize/OperateRange NULL dans cet owner |
| IFile | **7** | **5** | **2** | 30/10/2026 | OperateRange et OperateRangeWithBuffer NULL |
| IDirectory | **2** | **2** | **0** | 30/10/2026 | Read/GetEntryCount raccordés |
| BSD sockets principal | **46** | **26** | **20** | 30/10/2026 | cœur socket largement présent ; stats/mmsg/NIF/commandes modernes incomplètes |
| SFDNSRES | **16** | **6** | **10** | 30/10/2026 | host/name/address principaux partiels ; cancel/name-info incomplets |
| SSL connection | **36** | **25** | **11** | **11/11/2026** | R23 #120 améliore fortement la couverture ; DTLS/SRTP/timeouts encore NULL |
| SSL context | **14** | **7** | **7** | **11/11/2026** | import/create présents ; remove/CRL/keygen partiels |
| SSL service utilisateur | **10** | **4** | **6** | **11/11/2026** | service système bien plus complet que service utilisateur |
| SSL service système | **14** | **14** | **0** | **11/11/2026** | handlers raccordés ; sémantique à qualifier séparément |
| AudioRenderer | **14** | **13** | **1** | 30/10/2026 | cmd 11 ExecuteAudioRendererRendering NULL ; cmd 14 HOS23 à recroiser |
| Hardware Opus manager | **10** | **10** | **0** | 30/10/2026 | manager raccordé ; décoder/ABI et HOS23 restent à qualifier |
| Audio control/service tables R23 inspectées | **54** | **0** | **54** | 30/10/2026 | plusieurs interfaces suspend/volume/debug sont entièrement NULL |
| SystemSettingsServer — table inspectée | **130** | **0** | **130** | 30/10/2026 | très grand trou source ; vérifier autres interfaces `set:sys` avant conclusion globale |
| LDN IUserLocalCommunicationService | **30** | **27** | **3** | 30/10/2026 | Reject, ClearAcceptFilter, ConnectPrivate NULL |
| NCM location resolver tables | **35** | **0** | **35** | 30/10/2026 | résolution/redirection de chemins largement NULL |
| NCM content storage/meta sous-interfaces inspectées | **26** | **12** | **14** | 30/10/2026 | création/activation/maintenance partielle |
| NIM system-update/network-install grande interface | **223** | **0** | **223** | 30/10/2026 | surface réseau/update volontairement quasi absente |
| NS IApplicationManagerInterface R23 | **459** | **52** | **407** | **11/11/2026** | énorme surface déclarée mais peu implémentée ; FW23.5 backport récent |
| AM IApplicationProxyService | **1** | **1** | **0** | 30/10/2026 | ouverture proxy raccordée ; sous-interfaces à suivre séparément |
| Error Report context | **13** | **1** | **12** | 30/10/2026 | UpdateAwakeTime seul handler réel dans cette table |
| LM ILogger + lm:get | **9** | **3** | **6** | 30/10/2026 | logging de base présent, getter/dev incomplets |
| Fatal user | **3** | **3** | **0** | 30/10/2026 | commandes historiques 0–2 raccordées |
| NFC user/system principal | **22–25** | **20–22** | **2–3** | 30/10/2026 | cœur NFC solide ; pass-through session 1301/1302 NULL |
| Loader R23 public tables | **10** | **0** | **10** | 30/10/2026 | à vérifier contre délégation interne avant classement P0 |
| PM shell | **10** | **1** | **9** | 30/10/2026 | seulement GetApplicationProcessIdForShell raccordé |

### Interprétation de la date

« Dernière modif owner » est la dernière modification de ce chemin dans la branche vendor, **pas** la date d'origine du code upstream. Les imports du 30/10/2026 peuvent encapsuler du code bien plus ancien. La colonne sert surtout à faire ressortir les backports récents (par exemple FSP/SSL/NS le 11/11) face aux surfaces restées inchangées.

## 7. Priorités de lecture

Le registre complet doit être trié par impact, pas seulement par numéro de commande :

- **P0 boot / progression :** SM, SVC, FS, Loader/PM, AM, NS, VI/Nvnflinger, NVDRV, HID, time, settings.
- **P1 gameplay / fidélité / réseau / média :** audio/hwopus, sockets/DNS/SSL/NIFM/LDN, Account, NCM/NIM, NFC/NFP, BCAT, capture.
- **P2/P3 :** debug/manufacturing, télémétrie, services non retail, fonctions non exercées et utilitaires.

Une fonction **ABSENT/NULL** reste un écart de couverture, mais ne passe devant un P0/P1 exercé que si un log, un Title ID, un PC invité ou une chaîne de dépendances montre qu'elle bloque réellement le runtime.

---

# PARTIE A — Couverture détaillée actuelle

Les sections suivantes sont progressivement remplies à partir des tables SwitchBrew actuelles et des `FunctionInfo` des propriétaires Encore. Les lignes marquées **SWIPC-HIST** sont un filet historique ; **SB-CURRENT** indique une recroisée actuelle.

## A.1 Service Manager `sm:` — SB-CURRENT

SwitchBrew documente quatre commandes principales. Elles sont critiques pour toute la chaîne HLE.

| Cmd | Fonction | Statut Encore | Owner/handler | Revalidation | Notes |
|---:|---|---|---|---|---|
| 0 | RegisterClient | ? | service SM à qualifier dans le graphe actif | 21/11/2026 | TIPC à partir de HOS 12 ; vérifier adaptation des IDs |
| 1 | GetServiceHandle | ? | idem | 21/11/2026 | P0 : acquisition réelle des services |
| 2 | RegisterService | ? | idem | 21/11/2026 | surtout services système |
| 3 | UnregisterService | ? | idem | 21/11/2026 | cycle de vie |

## A.2 Kernel SVC — SB-CURRENT

La table exhaustive de référence est SwitchBrew SVC. Le registre ne confond pas « dispatcher présent » et sémantique correcte. Les SVC déjà observés dans les logs FC27 (`WaitSynchronization`, `WaitProcessWideKeyAtomic`, `SignalProcessWideKey`) restent prioritaires pour la qualification comportementale.

| ID | Fonction | Statut Encore | Revalidation | Note |
|---:|---|---|---|---|
| 0x01 | SetHeapSize | ? | 21/11/2026 | vérifier limites/alignement et erreurs |
| 0x18 | WaitSynchronization | ? | 21/11/2026 | observé dans traces FC27 ; sampling ≠ preuve de blocage |
| 0x1C | WaitProcessWideKeyAtomic | ? | 21/11/2026 | observé dans traces FC27 |
| 0x1D | SignalProcessWideKey | ? | 21/11/2026 | observé dans traces FC27 |
| 0x45 | CreateEvent | ? | 21/11/2026 | table moderne SwitchBrew |
| 0x46 | MapIoRegion | ? | 21/11/2026 | HOS 13+ |
| 0x47 | UnmapIoRegion | ? | 21/11/2026 | HOS 13+ |

> La sous-table SVC complète sera tenue ici au même format lorsque la comparaison automatique du dispatcher actif sera terminée ; les entrées D/P du registre NS1 existant restent les preuves source jusque-là.

## A.3 Account — SB-CURRENT + source Eden

Le propriétaire Eden contient un grand nombre de commandes enregistrées mais encore `nullptr`. Cela doit rester visible : la présence du service ne signifie pas une couverture fonctionnelle complète.

| Service/interface | Cmd | Fonction | Statut source initial | Revalidation |
|---|---:|---|---|---|
| acc:su / IAccountServiceForAdministrator | 0 | GetUserCount | SRC | 21/11/2026 |
|  | 1 | GetUserExistence | SRC | 21/11/2026 |
|  | 2 | ListAllUsers | SRC | 21/11/2026 |
|  | 3 | ListOpenUsers | SRC | 21/11/2026 |
|  | 4 | GetLastOpenedUser | SRC | 21/11/2026 |
|  | 5 | GetProfile | SRC | 21/11/2026 |
|  | 6 | GetProfileDigest | **NULL** | 21/11/2026 |
|  | 50 | IsUserRegistrationRequestPermitted | SRC | 21/11/2026 |
|  | 51 | TrySelectUserWithoutInteractionDeprecated | SRC | 21/11/2026 |
|  | 52 | TrySelectUserWithoutInteraction | SRC | 21/11/2026 |
|  | 99 | DebugActivateOpenContextRetention | **NULL** | 21/11/2026 |
|  | 100 | GetUserRegistrationNotifier | **NULL** | 21/11/2026 |
|  | 101 | GetUserStateChangeNotifier | **NULL** | 21/11/2026 |
|  | 102 | GetBaasAccountManagerForSystemService | SRC | 21/11/2026 |
|  | 103 | GetBaasUserAvailabilityChangeNotifier | **NULL** | 21/11/2026 |

Le même audit doit être conservé pour `acc:u0`, `acc:u1`, `acc:aa` et les sous-interfaces Baas/Profile : plusieurs tables Eden sont majoritairement NULL malgré un service enregistré.

## A.4 NFC — SB-CURRENT + source Eden

| Interface | Cmd | Fonction | Statut source initial | Revalidation |
|---|---:|---|---|---|
| IUser/ISystem | 0–3 | Initialize/Finalize/GetState/IsNfcEnabled (legacy) | SRC | 21/11/2026 |
| IUser/ISystem | 400–412 | Initialize → GetDeactivateEventHandle | SRC | 21/11/2026 |
| IUser/ISystem | 1000 | ReadMifare | SRC | 21/11/2026 |
| IUser/ISystem | 1001 | WriteMifare | SRC | 21/11/2026 |
| IUser/ISystem | 1300 | SendCommandByPassThrough | SRC | 21/11/2026 |
| IUser/ISystem | 1301 | KeepPassThroughSession | **NULL** | 21/11/2026 |
| IUser/ISystem | 1302 | ReleasePassThroughSession | **NULL** | 21/11/2026 |
| nfc:am / IAm | 0 | Initialize | **NULL** dans l'interface AM retournée | 21/11/2026 |
| nfc:am / IAm | 1 | Finalize | **NULL** | 21/11/2026 |
| nfc:am / IAm | 2 | NotifyForegroundApplet | **NULL** | 21/11/2026 |

## A.5 Loader / Process Manager — SB-CURRENT + source active R23

### Loader

| Service | Cmd | Fonction SwitchBrew | Statut source initial | Revalidation |
|---|---:|---|---|---|
| ldr:shel | 0 | SetProgramArgument | **NULL** | 21/11/2026 |
| ldr:shel | 1 | FlushArguments | **NULL** | 21/11/2026 |
| ldr:dmnt | 0 | SetProgramArgument2 | **NULL** | 21/11/2026 |
| ldr:dmnt | 1 | FlushArguments2 | **NULL** | 21/11/2026 |
| ldr:dmnt | 2 | GetProcessModuleInfo | **NULL** | 21/11/2026 |
| ldr:pm | 0 | CreateProcess | **NULL** | 21/11/2026 |
| ldr:pm | 1 | GetProgramInfo | **NULL** | 21/11/2026 |
| ldr:pm | 2 | PinProgram | **NULL** | 21/11/2026 |
| ldr:pm | 3 | UnpinProgram | **NULL** | 21/11/2026 |
| ldr:pm | 4 | SetEnabledProgramVerification | **NULL** | 21/11/2026 |

Ces NULL sont importants : il faut vérifier si le runtime réel délègue ces fonctions à une autre couche avant de conclure à une absence comportementale.

### Process Manager

| Service | Cmd | Fonction | Statut source initial | Revalidation |
|---|---:|---|---|---|
| pm:bm | 0 | GetBootMode | SRC | 21/11/2026 |
| pm:bm | 1 | SetMaintenanceBoot | SRC | 21/11/2026 |
| pm:info | 0 | GetProgramId | SRC | 21/11/2026 |
| pm:shell | 0 | LaunchProgram | **NULL** | 21/11/2026 |
| pm:shell | 1 | TerminateProcess | **NULL** | 21/11/2026 |
| pm:shell | 2 | TerminateProgram | **NULL** | 21/11/2026 |
| pm:shell | 3 | GetProcessEventEvent/Handle | **NULL** | 21/11/2026 |
| pm:shell | 4 | GetProcessEventInfo | **NULL** | 21/11/2026 |
| pm:shell | 5 | NotifyBootFinished | **NULL** | 21/11/2026 |
| pm:shell | 6 | GetApplicationProcessIdForShell | SRC | 21/11/2026 |
| pm:shell | 7 | BoostSystemMemoryResourceLimit | **NULL** | 21/11/2026 |
| pm:shell | 8 | BoostApplicationThreadResourceLimit | **NULL** | 21/11/2026 |
| pm:shell | 9 | GetBootFinishedEvent | **NULL** | 21/11/2026 |

## A.6 Log / Fatal — SB-CURRENT

| Service/interface | Cmd | Fonction | Statut source initial | Revalidation |
|---|---:|---|---|---|
| lm | 0 | OpenLogger | SRC | 21/11/2026 |
| ILogger | 0 | Log | SRC | 21/11/2026 |
| ILogger | 1 | SetDestination | SRC | 21/11/2026 |
| ILogger | 2 | TransmitHashedLog | **STUB_NOOP** (`nullptr` table, dispatcher whitelist) | 21/11/2026 |
| ILogger | 3 | DevNotify | **STUB_NOOP** (`nullptr` table, dispatcher whitelist) | 21/11/2026 |
| lm:get | 0 | StartLogging | **NULL** | 21/11/2026 |
| lm:get | 1 | StopLogging | **NULL** | 21/11/2026 |
| lm:get | 2 | GetLog | **NULL** | 21/11/2026 |
| lm:get | 100 | CreateDevNotificationReceiver | **NULL** | 21/11/2026 |
| fatal:u | 0 | ThrowFatal | SRC | 21/11/2026 |
| fatal:u | 1 | ThrowFatalWithPolicy | SRC | 21/11/2026 |
| fatal:u | 2 | ThrowFatalWithCpuContext | SRC | 21/11/2026 |
| fatal:u | 3 | HOS 21+ commande supplémentaire | **ABSENT/à qualifier** | 21/11/2026 |

> **Politique de stubs NS1 (21/11, runtime `2df83d59` → vendor `ba3377a0`)** : le dispatcher maintenu distingue désormais trois états. Une commande `nullptr` connue reste `ResultNotImplemented` par défaut ; seules des commandes optionnelles sans sortie utile et non nécessaires au gameplay peuvent être `STUB_NOOP` (`pdm:ntfy` notifications, `ILogger` 20.0.0+, bookkeeping `erpt:c`, configuration `eupld:c`, setters applet ciblés). Les getters, handles, mappings mémoire/GPU, SVC, synchronisation et sécurité ne reçoivent jamais un faux succès. Les tables d'origine peuvent donc rester `nullptr` alors que le runtime actif fournit un no-op borné. L'IRS/caméra Joy-Con existante n'est pas supprimée ni remplacée par un stub.


## A.7 HID / HIDBUS — SB-CURRENT + owner R23

Le `IHidSystemServer` R23 inspecté contient **240 entrées : 54 handlers et 186 NULL**. Cette famille doit être lue par sous-surface ; la plupart des commandes de calibration, firmware, NFC système, custom button configuration et diagnostic ne sont pas implémentées.

| Surface / commandes | Statut initial | Exemples | Owner |
|---|---|---|---|
| politiques Npad système | **SRC/PARTIEL** | 303–306, 308–310, 312–319, 321–322 | `eden-backports/.../hid_system_server.cpp` |
| enregistrement Aruid/input | **SRC/PARTIEL** | 501–507 | même owner |
| vibration master/session | **SRC/PARTIEL** | 510–513 | même owner |
| firmware controller | **PARTIEL** | 1000 et 1004 raccordés ; 1001–1003, 1005–1012 NULL | même owner |
| USB firmware | **PARTIEL** | 1130–1132, 1135 raccordés ; 1133–1134 NULL | même owner |
| configuration boutons | **NULL majoritaire** | 1200–1290 largement NULL ; 1271/1272 font partie des rares handlers | même owner |
| NFC via HID system | **NULL** | 210–227 majoritairement NULL | même owner |
| HIDBUS | **NULL dans table inspectée** | cmd 13 GetPollingData | `sources/eden/.../hidbus.cpp` |

**Priorité :** ne pas implémenter les 186 NULL en vrac. Rechercher d'abord les IDs réellement exercés par les jeux/firmwares, puis appliquer le contrat SwitchBrew exact.

## A.8 Filesystem / FSP — SB-CURRENT + R23

Le `FSP_SRV` R23 inspecté possède **128 entrées : 36 handlers / 92 NULL**.

| Cmd | Fonction | Statut | Note |
|---:|---|---|---|
| 1 | SetCurrentProcess | SRC | handler réel |
| 2 | OpenDataFileSystemByCurrentProcess | SRC | handler réel |
| 7 | OpenFileSystemWithPatch | SRC | handler réel |
| 18 | OpenSdCardFileSystem | SRC | handler réel |
| 22/23 | CreateSaveDataFileSystem* | SRC | handlers réels |
| 30/31 | OpenGameCardStorage / OpenGameCardFileSystem | **NULL** | écart explicite dans cet owner |
| 51/52/53 | OpenSaveDataFileSystem* | SRC | handlers réels |
| 60 | OpenSaveDataInfoReader | **NULL** | variantes 61/62 sont raccordées |
| 200 | OpenDataStorageByCurrentProcess | SRC | handler réel |
| 201 | OpenDataStorageByProgramId | **NULL** | à qualifier si exercé |
| 202/203 | OpenDataStorageByDataId / OpenPatchDataStorageByCurrentProcess | SRC | handlers réels |
| 204 | OpenDataFileSystemByProgramIndex | **NULL** | à qualifier |
| 205 | OpenDataStorageWithProgramIndex | SRC | handler réel |
| 1200 | OpenMultiCommitManager | SRC | handler réel |

Sous-interfaces :

- `IStorage` : **Read** et **GetSize** raccordés ; Write/Flush/SetSize/OperateRange NULL.
- `IFile` : Read/Write/Flush/SetSize/GetSize raccordés ; OperateRange/OperateRangeWithBuffer NULL.
- `IDirectory` : Read/GetEntryCount raccordés.

Ces lignes sont particulièrement importantes pour les loaders, archives et save data : une interface « ouverte » peut tout de même échouer ensuite sur une sous-commande NULL.

## A.9 Sockets / DNS / SSL — SB-CURRENT

### BSD

Le propriétaire PS5 actif contient **46 commandes principales : 26 handlers / 20 NULL**. Les opérations socket courantes sont raccordées : Socket, Select, Poll, Recv/RecvFrom, Send/SendTo, Accept, Bind, Connect, GetPeerName/GetSockName, Get/SetSockOpt, Listen, Ioctl, Fcntl, Shutdown, Read/Write/Close, DuplicateSocket et EventFd.

Restent NULL notamment : Open(4), Sysctl(7), ShutdownAllSockets(23), GetResourceStatistics(28), RecvMMsg(29), SendMMsg(30), RegisterClientShared(33), GetSocketStatistics(34), NifIoctl(35), commandes 36–43 et thread-core mask 200/201.

### SFDNSRES

**6/16 handlers** : GetHostByName, GetGaiStringError, GetAddrInfo, leurs variantes principales avec options et ResolverSetOption. Les requêtes reverse/name-info, cancel et plusieurs options restent NULL.

### SSL R23 #120

| Interface | Handlers / total | Statut |
|---|---:|---|
| ISslConnection | **25/36** | PARTIEL |
| ISslContext | **7/14** | PARTIEL |
| ISslService utilisateur | **4/10** | PARTIEL |
| ISslServiceForSystem | **14/14** | SRC |

`Pending`, `Peek`, `Poll`, renegotiation et plusieurs options sont bien raccordés dans le owner R23 ; DTLS, SRTP, export keying material et timeout I/O restent NULL dans la connexion inspectée.

## A.10 Audio / Opus — SB-CURRENT

| Interface | Couverture source | Trous explicites |
|---|---|---|
| IAudioRenderer | **13/14 handlers** | cmd 11 ExecuteAudioRendererRendering NULL |
| IHardwareOpusDecoderManager | **10/10 handlers** | aucun NULL dans la table manager |
| tables de contrôle/suspend/volume inspectées dans `audio.cpp` R23 | **0/54 handlers** | toutes NULL dans les tableaux inspectés |

**Firmware 23.x :** SwitchBrew actuel doit rester la référence pour les commandes ajoutées après la baseline Eden/SwIPC, notamment les évolutions AudioRenderer. Un manager Opus 10/10 n'implique pas que chaque variante de décodage, work-buffer, erreur ou lifecycle est conforme.

## A.11 Settings — SB-CURRENT

La table `ISystemSettingsServer` inspectée expose **130 entrées et 130 NULL**. Exemples : NetworkSettings 1/2, FirmwareVersionDigest 5, audio volume 19/20, LDN channel 80/81, controller settings 97/98, USB flags 103/104, thèmes 168/169/175–178, button config 189–200, etc.

**Classement : PARTIEL/NULL selon sous-interface.** Il faut distinguer cette grande table des autres services/settings accessibles ailleurs dans Eden : ce résultat ne permet pas d'affirmer que « settings entier = 0 % », seulement que ce propriétaire précis ne fournit aucun handler pour ses 130 commandes déclarées.

## A.12 LDN — SB-CURRENT

`IUserLocalCommunicationService` : **27/30 handlers**.

Trous explicites :

| Cmd | Fonction | Statut |
|---:|---|---|
| 205 | Reject | **NULL** |
| 209 | ClearAcceptFilter | **NULL** |
| 303 | ConnectPrivate | **NULL** |

Les commandes état/réseau, scan, AP create/destroy, advertise, station open/connect/disconnect et Initialize/Finalize sont raccordées. **Raccordé ≠ réseau local PS5 validé**.

## A.13 NCM / NIM — SB-CURRENT

### NCM

Les trois grandes tables de résolution/redirection de chemins inspectées totalisent **35/35 NULL**. En revanche, certaines sous-interfaces de ContentStorage/ContentMeta ont des handlers réels : placeholder/content operations et ouverture de ContentStorage/ContentMetaDatabase sont partiellement présentes.

### NIM

La grande interface system-update/network-install inspectée contient **223 commandes et 223 NULL**. D'autres petites interfaces sont réelles (Async/Accessor, EnsureNetworkClockAvailability, NTC). Il faut donc classer **NIM update/install = NULL majeur**, pas « NIM entier absent ».

Ces surfaces sont P1/P2 tant qu'aucun boot/gameplay local ne montre qu'un titre exige une de ces commandes.

## A.14 NS / Application Manager — SB-CURRENT + FW23.5

Le owner R23 `IApplicationManagerInterface` sélectionné pour FW23.5 contient **459 commandes : 52 handlers / 407 NULL**. Il s'agit d'une des plus grosses surfaces de dette HLE explicite.

Handlers importants déjà raccordés comprennent notamment ListApplicationRecord (0), GetApplicationRecordUpdateSystemEvent (2), DeleteApplicationEntity/Completely (4/5), PushApplicationRecord (16), CheckApplicationLaunchVersion (38), GetApplicationLogoData (40), storage/free-space 47/48, GetApplicationDesiredLanguage (55), ConvertApplicationLanguageToLanguageCode (59), ResumeAll (70), GetStorageSize (71), GetApplicationControlData (400), ListApplicationTitle/Icon (407/408) et RequestDownloadApplicationControlDataInBackground (419).

Exemples de NULL à ne pas masquer : LaunchApplicationOld (19), TerminateApplication (22), ResolveApplicationContentPath (23), LaunchApplication (94), LaunchLibrary/System/OverlayApplet 302–307, de nombreuses opérations update/download et une grande partie des caches/maintenance.

**Important :** les nouvelles commandes FW23.5 ajoutées par le backport doivent être recroisées ligne par ligne avec SwitchBrew actuel ; les 459 entrées ne sont pas toutes pertinentes pour un jeu retail.

## A.15 AM / Error Report

- `IApplicationProxyService::OpenApplicationProxy` (cmd 0) est raccordé ; les nombreuses sous-interfaces AM doivent être suivies séparément.
- Error Report context inspecté : **1/13 handler** (`UpdateAwakeTime`) et **12 NULL** ; autre table OpenReport/OpenManager/OpenAttachment = 3/3 NULL.

Le service ERPT n'est pas prioritaire devant un blocage boot/GPU, mais ses trous doivent rester visibles pour la complétude firmware.


## A.16 VI / NVDRV — SB-CURRENT

### VI

Les root-service tables inspectées ont leurs variantes `GetDisplayServiceWithProxyNameExchange` NULL (application cmd 1 ; manager/system cmd 3). Les commandes fatal du manager root 100–103 sont également NULL.

**Ne pas conclure « VI absent »** : le vrai display service et Nvnflinger vivent dans d'autres propriétaires déjà actifs. Ces lignes signifient seulement que les variantes root/proxy-name correspondantes ne sont pas raccordées dans ces tables.

### NVDRV

`nvdrv_interface.cpp` principal : **11/14 handlers**.

| Cmd | Fonction | Statut |
|---:|---|---|
| 0 | Open | SRC |
| 1 | Ioctl | SRC |
| 2 | Close | SRC |
| 3 | Initialize | SRC |
| 4 | QueryEvent | SRC |
| 5 | MapSharedMem | **NULL** |
| 6 | GetStatus | SRC |
| 7 | SetAruidForTest | **NULL** |
| 8 | SetAruid | SRC |
| 9 | DumpGraphicsMemoryInfo | SRC |
| 10 | InitializeDevtools | **NULL** |
| 11/12 | Ioctl2 / Ioctl3 | SRC |
| 13 | SetGraphicsFirmwareMemoryMarginEnabled | SRC |

Les commandes `Ioctl*` ne prouvent pas la couverture des ioctls device : les tables nvmap/nvhost/as-gpu/gpu restent à qualifier séparément.

## A.17 Time — SB-CURRENT

La StaticService inspectée possède **19/19 handlers** : clocks user/network/steady/local, timezone, shared-memory handle, correction automatique, snapshots et calculs de différence/span.

**Statut : SRC**, pas OK-PS5. La couverture de fonctions ne prouve ni la précision du clock source PS5, ni le comportement de toutes les variantes firmware.

## A.18 NIFM — SB-CURRENT

| Sous-interface inspectée | Handlers / total | Lecture |
|---|---:|---|
| ScanRequest | **5/5** | SRC |
| Request | **9/26** | PARTIEL |
| profile update/persist table | **0/3** | NULL |
| GeneralService | **26/49** | PARTIEL |
| service factory | **2/2** | SRC |

Dans GeneralService, les fonctions courantes profil/interface/IP/Wi-Fi/Ethernet/status sont en grande partie raccordées. Restent notamment sleep/wakeup, telemetry, shutdown, allowed channels, wired availability et network-emulation/debug. **Le réseau PS5 et la politique d'isolation guest restent une couche distincte.**

## A.19 NFP / Mii — SB-CURRENT

### NFP

Les trois services créateurs inspectés (user/system/debug) raccordent leur commande 0 de création d'interface. Les interfaces retournées doivent être suivies séparément : **créateur présent ≠ toutes les opérations Amiibo présentes**.

### Mii

- DatabaseService principal : **25/27 handlers** ; Import(18) et Export(19) NULL.
- autre table database/image inspectée : **2/14 handlers**, le reste largement NULL.

Les renommages/ajouts HOS 23.x doivent être suivis via SwitchBrew courant, car les noms historiques peuvent diverger.

## A.20 BCAT — SB-CURRENT

`bcat_service.cpp` inspecté : **5/26 handlers**. Raccordés : RequestSyncDeliveryCache (10100), RequestSyncDeliveryCacheWithDirectoryName (10101), SetPassphrase (30100), RegisterSystemApplicationDeliveryTasks (30300), ClearDeliveryCacheStorage (90201). Les autres commandes de tâches/notifiers/listes/log sont majoritairement NULL.

**Statut : PARTIEL**, priorité seulement si un titre/log l'exerce.

## A.21 USB / PTM / PSM / APM — SB-CURRENT

### USB

La plupart des interfaces USB inspectées sont entièrement NULL : device-side endpoints/control, host interface/session, PD/notice/topology et manufacture. Deux petites factories raccordent seulement `OpenSession` / `OpenCradleSession`.

**Statut global : NULL/PARTIEL**. Faible priorité pour les jeux retail sauf preuve d'appel.

### PTM/PSM

- PTM Vdd50 : **0/3 handlers**, OpenSession table **0/1**.
- PSM state-change session : **5/5 handlers**.
- PSM service principal : **6/19 handlers** ; charge, charger type, session, voltage state, battery age/info présents ; charging control et plusieurs events restent NULL.

### APM

- session/performance configuration tables de base : **6/6 handlers** au total.
- autre interface APM inspectée : **3/8 handlers**, cinq commandes de mode/throttling/settings NULL.

## A.22 SM controller

Le contrôleur de domaine/service inspecté possède **5/6 handlers** : ConvertCurrentObjectToDomain, CloneCurrentObject, QueryPointerBufferSize, CloneCurrentObjectEx et SetPointerBufferSize sont raccordés ; CopyFromCurrentDomain (cmd 1) est NULL.

Cela complète la surface du contrôleur IPC, mais **pas encore** la qualification de la table `sm:` elle-même (RegisterClient/GetService/RegisterService/UnregisterService).

---

# PARTIE B — Inventaire automatisé Eden / baseline SwIPC historique

Cette partie sert de **filet exhaustif** pour les interfaces historiques : elle compare les IDs/noms de SwIPC aux tables `FunctionInfo` Eden. Elle ne remplace jamais les pages SwitchBrew actuelles pour les firmwares récents.

Les sections seront regroupées par famille avec les colonnes :

`Interface | Service | Cmd | Nom de référence | Eden | Handler | Owner | Référence | Revalidation`.

### Interprétation automatique

- entrée Eden avec `nullptr` → **NULL** ;
- handler non nul → **SRC** jusqu'à lecture du corps ;
- commande SwIPC sans entrée Eden correspondante → **ABSENT** ;
- entrée Eden sans équivalent SwIPC → **NOUVEAU/À RECROISER SWITCHBREW** ;
- les fonctions modernes 4.0.0–23.5.0 sont ajoutées à partir de SwitchBrew sous **SB-CURRENT**, pas déduites de SwIPC.

> **Important :** les comptes automatiques sont un outil de navigation. Les décisions P0/P1 sont prises sur le propriétaire C++ effectivement sélectionné, les logs et la console.

## B.1 Familles prioritaires à maintenir exhaustivement

- [ ] SM + SVC
- [ ] Account
- [ ] HID / HIDBUS / IRS
- [ ] AM / appletOE / appletAE
- [ ] Filesystem / fsp-srv / IStorage / IFile / IDirectory
- [ ] NS / AOC / NCM / NIM
- [ ] VI / Nvnflinger
- [ ] NVDRV / nvmap / nvhost
- [ ] Audio / hwopus
- [ ] Sockets / DNS / SSL / NIFM / LDN
- [ ] Settings / time
- [ ] Loader / PM / PGL
- [ ] NFC / NFP / Mii
- [ ] BCAT / OLSC / capture / erpt
- [ ] services firmware 23.x (`stpl:*`, nouveaux IDs NS/HID/audio/etc.)

---

# PARTIE C — File d'écarts explicites

Ce tableau ne contient que des trous/limites prouvés par la source ou la référence. Il évite de perdre les fonctions importantes au milieu des milliers de lignes.

| Priorité | Domaine | Fonction/commande | Statut | Pourquoi c'est ouvert | Action de fermeture |
|---|---|---|---|---|---|
| P0 | Loader | ldr:pm 0–4 | **NULL** | handlers R23 enregistrés mais nuls dans le propriétaire inspecté | vérifier délégation réelle/owner CMake puis implémenter le contrat requis |
| P0 | PM | pm:shell 0–5, 7–9 | **NULL** | couverture très faible de l'interface shell | vérifier chemin de lancement utilisé par Eden avant patch |
| P0/P1 | Account | plusieurs Baas/notifiers/cache | **NULL** | nombreuses commandes enregistrées sans handler | prioriser seulement celles exercées par logs/jeux |
| P1 | NFC | 1301/1302 | **NULL** | pass-through session incomplète | implémenter si Title ID/log l'exerce |
| P2 | LM | hashed/dev/getter récents | **NULL** | logging retail est largement stub côté HOS lui-même | ne pas détourner P0/P1 sans consommateur |
| P1/P2 | Firmware 23.x | commandes absentes de SwIPC historique | **?** | baseline historique insuffisante | recroiser SwitchBrew actuel et source active à chaque backport |

---

# PARTIE D — Politique de mise à jour

À chaque ajout/modification HLE/SVC :

1. modifier **la ligne existante** de ce registre ;
2. renseigner le nouveau statut, owner exact, SHA moteur + vendor et date ;
3. si le handler passe de NULL/ABSENT à SRC, ne pas écrire « résolu » ;
4. passer à OK-HOST uniquement avec un témoin réellement pertinent ;
5. passer à OK-PS5 uniquement avec une session console représentative ;
6. conserver l'historique concis dans la cellule Notes, pas dans un nouveau Markdown ;
7. recroiser SwitchBrew lorsqu'un firmware change l'ID, le nom, les buffers, les handles, le type IPC HIPC/TIPC ou les erreurs attendues.

## Contrôle périodique conseillé

Lors d'un changement de firmware invité, d'un backport HLE ou avant une grosse campagne console :

- comparer `Services_API` S1 avec les services enregistrés ;
- comparer les pages de famille pour les IDs nouveaux ;
- comparer la table SVC ;
- scanner les `FunctionInfo` pour `nullptr`;
- scanner les corps pour `UNIMPLEMENTED`, `Stubbed`, TODO, succès constant et objets factices ;
- vérifier les remplacements CMake/overlays ;
- mettre à jour **ce fichier uniquement**.

---

## État de ce premier snapshot

Le document est **créé et utilisable dès maintenant**, mais son but est d'être enrichi jusqu'à la matrice exhaustive. Les premières lignes montrent déjà un point important que le registre d'architecture ne rendait pas visible : plusieurs services existent et sont enregistrés alors qu'une part significative de leurs commandes reste NULL ou minimale. Cette distinction doit guider les futures recherches par signature exacte plutôt que d'assimiler « service présent » à « service complet ».
