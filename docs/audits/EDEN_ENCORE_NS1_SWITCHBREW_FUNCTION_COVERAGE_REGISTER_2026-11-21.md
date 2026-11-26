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

## Lot STUB périphériques IRS / prepo / news — 22/11/2026

Couple moteur → vendor final `229ebbc5b25776604c061ebdb93ca31330fa5745` (commit IRS intermédiaire `569c8e2ae6fe3dfaecb578be4c104381329f53df`). Les cinq stubs matériels IRS sont maintenant des NOOP intentionnels et le garde d'index processeur utilise `processors.size()`. `SaveSystemReportOld` est devenu une vraie sauvegarde `Core::Reporter`; trois commandes de transport prepo restent NOOP car aucun transport Nintendo n'existe. `ClearStorage` news est une vraie mutation de `NewsStorage`; huit opérations backend/abonnement/texte sont NOOP documentées.

**Compteur courant : 1 240 IMPL-SRC / 77 PARTIEL / 329 STUB / 27 NOOP / 2 311 NULL / 68 D / 191 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 6 HORS-VERSION / 0 ABSENT / 285 ABI-DIFF / 12 AMBIGU / 1 E = 4 853.** Aucun gain console n'est déclaré sans test PS5.

## Lot FSP P0 patch-data / cache reader — 22/11/2026

Vendor `8e387b641aa5c227db2d14d06b0457a91be043fc` (au-dessus des lots concurrents IRS/News/Prepo) : `OpenPatchDataStorageByCurrentProcess` passe **STUB → IMPL-SRC** avec ABI libnx cmd203 sans entrée et storage issu du RomFS courant patché. `OpenSaveDataInfoReaderOnlyCacheStorage` passe **STUB → PARTIEL** : il filtre maintenant le cache du programme courant au lieu d'énumérer le Temporary.

Le reader est matérialisé dans `encore-active/eden-backports` avec son header et ajouté au manifeste d'intégrité ; le build PS5 recevra donc ces sources, pas une modification dormante de `sources/eden`.

**Compteur courant : 1 241 IMPL-SRC / 78 PARTIEL / 327 STUB / 27 NOOP / 2 311 NULL / 68 D / 191 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 6 HORS-VERSION / 0 ABSENT / 285 ABI-DIFF / 12 AMBIGU / 1 E = 4 853.** Le palier précédent `fb52cdf1` était vert sur X8D24 + provenance ; ce nouveau couple n'est pas encore validé PS5.

## Lot FSP save/cache — 22/11/2026

Vendor `e2da4886884f9dec2c6753db1de6e1048cfa095b` : `GetCacheStorageSize` passe **STUB → PARTIEL** et lit les tailles persistées du cache courant après validation d'existence ; `ExtendSaveDataFileSystem` passe **STUB → D**, car aucun indexeur ne permet de résoudre un `save_data_id` et un succès sans extension serait incorrect.

**Compteur courant : 1 241 IMPL-SRC / 79 PARTIEL / 325 STUB / 27 NOOP / 2 311 NULL / 69 D / 191 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 6 HORS-VERSION / 0 ABSENT / 285 ABI-DIFF / 12 AMBIGU / 1 E = 4 853.** Aucun test PS5 n'est déduit de cette qualification.

## Lot STUB friend / Palma / mm:u — 22/11/2026

Couple repointé vers vendor `51e5cbde026b62038ac7f3b2845d3d00d95eeff6`. `friend:*` est explicitement offline avec sorties ABI-correctes. Palma est séparé entre 13 commandes réellement adossées au ResourceManager et 15 opérations de matériel Poké Ball Plus volontairement NOOP ; les erreurs de handle sont propagées sur les chemins raccordés. `mm:u` conserve son état de session réel et corrige la réponse `GetOld`.

**Compteur courant : 1 262 IMPL-SRC / 79 PARTIEL / 276 STUB / 55 NOOP / 2 311 NULL / 69 D / 191 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 6 HORS-VERSION / 0 ABSENT / 285 ABI-DIFF / 12 AMBIGU / 1 E = 4 853.** Validation hôte/CI à refaire sur ce HEAD ; aucun résultat PS5 n'est déduit de ce classement.

## Lot BLE / hidbus / erpt / pctl — 22/11/2026

Couple moteur repointé vers vendor `61e8993c8057ca9536f8997185118d072130497f`. BTM expose quatre vrais événements BLE ; le sélecteur hidbus physique est NOOP explicite. ERPT reste local-only. Le propriétaire PCTL PS5 est le backport `encore-active/eden-backports`, dont le manifeste a été mis à jour avec les empreintes des sources actives. Deux commandes PCTL utilisent l'état local réel, huit sont des fallbacks neutres documentés et cinq commandes de play timer passent en PARTIEL avec cycle Start/Stop local, sans faux décompte temporel.

**Compteur courant : 1 268 IMPL-SRC / 84 PARTIEL / 254 STUB / 66 NOOP / 2 311 NULL / 69 D / 191 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 6 HORS-VERSION / 0 ABSENT / 285 ABI-DIFF / 12 AMBIGU / 1 E = 4 853.** Aucune validation PS5 n'est déduite de ce classement.

## Lot matériel BTM / LBL / PSM / TS — 22/11/2026

Vendor `4936c5528e0641e2176fc77a376cfb8d2da2d1b5` : radio BTM et snapshot LBL sont raccordés à un état réel ; pairing/capteur ambiant restent NOOP. Le fallback PSM corrige un faux état critique batterie (`NeedsShutdown` -> `Normal`) et l'âge batterie 1.0 -> 100.0 %. PSM/TS sont conservés PARTIELS car les mesures sont synthétiques.

**Compteur courant : 1 271 IMPL-SRC / 88 PARTIEL / 244 STUB / 69 NOOP / 2 311 NULL / 69 D / 191 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 6 HORS-VERSION / 0 ABSENT / 285 ABI-DIFF / 12 AMBIGU / 1 E = 4 853.** Pas de validation console déduite.

## Lot set:sys / ntc — 22/11/2026

Vendor `be7f995c13675eeb3af8c1addac536876ed1e90b` : `PlatformRegion` est maintenant persisté dans `PrivateSettings`; les sorties produit/HOME restent synthétiques et donc PARTIELLES. Le service NTC confirme un modèle de tâche synchrone avec événement de fin réel ; Suspend/Resume sont des NOOP explicites faute de worker autonome.

**Compteur courant : 1 276 IMPL-SRC / 91 PARTIEL / 233 STUB / 72 NOOP / 2 311 NULL / 69 D / 191 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 6 HORS-VERSION / 0 ABSENT / 285 ABI-DIFF / 12 AMBIGU / 1 E = 4 853.** Pas de validation PS5 déduite.

## Lot FSP save-data réel — 22/11/2026

Couple : moteur repointé vers vendor `c3c3b6d23925dbe287e5a239663b9a04db6a0d21`. `OpenReadOnlySaveDataFileSystem` ne délègue plus au FS writable : le wrapper actif `fs_i_filesystem/fs_i_file` bloque toutes les mutations avec `ResultWriteNotPermitted`. `FindSaveDataWithFilter` ne retourne plus systématiquement `TargetNotFound` : il applique le filtre Horizon aux `SaveDataInfo` réels et renvoie count 0/1 avec un buffer 0x60 exact.

Le scanner `ISaveDataInfoReader` inclut désormais les caches User/SD et conserve la variante cache-only du programme courant. Référence comportementale : LibHac/Ryujinx pour `SaveDataInfoFilter` et cmd67.

**Compteur courant : 1 278 IMPL-SRC / 91 PARTIEL / 231 STUB / 72 NOOP / 2 311 NULL / 69 D / 191 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 6 HORS-VERSION / 0 ABSENT / 285 ABI-DIFF / 12 AMBIGU / 1 E = 4 853.** Validation console PS5 non revendiquée ; le précédent HEAD moteur `c92ded2c` → vendor `be7f995c` était vert X8D24 + provenance.

## Lot FSP SaveDataExtraData host-directory — 22/11/2026

Couple : moteur repointé vers vendor `61ab696e00da26fca41e899323acb480e1770d15`. LibHac confirme que les directory saves n'ont pas d'ExtraData physique : lecture = structure par défaut, écriture = succès sans mutation. Encore applique désormais cette règle seulement après validation du buffer 0x200 et de l'existence réelle du save.

Cmd69 passe PARTIEL → IMPL-SRC ; cmd70 STUB → NOOP. Cmd57/58/59 passent STUB → PARTIEL car le scan Eden peut retrouver les IDs système/non nuls, mais ne remplace pas encore l'indexer Horizon pour les IDs Account/Device. Cmd71 masqué a aussi été corrigé dans le runtime actif même s'il n'est pas une ligne distincte du miroir historique du catalogue.

**Compteur courant : 1 279 IMPL-SRC / 93 PARTIEL / 227 STUB / 73 NOOP / 2 311 NULL / 69 D / 191 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 6 HORS-VERSION / 0 ABSENT / 285 ABI-DIFF / 12 AMBIGU / 1 E = 4 853.** Le HEAD précédent `854e7785` → `c3c3b6d2` est vert X8D24 + provenance ; aucune validation PS5 n'est revendiquée.

## Lot FSP SD + NS application-record — 22/11/2026

Couple : moteur repointé vers vendor `a691b5535f9c69539b466a926359d805d734acce`. FSP : accessibilité SD issue de `OpenSDMC`, exFAT explicitement non modélisé. NS : présence d'application et existence de records dérivées du `ContentProviderUnion`; ProgramId courant lu du processus application; event de records corrigé pour ne plus être signalé lors de l'ouverture du handle.

`IsApplicationUpdateRequested` et `CheckApplicationLaunchVersion` sont reclassés NOOP plutôt que STUB : l'émulateur n'a pas de version-list/requête NS distante à reproduire et l'amont Ryujinx adopte les mêmes valeurs permissives. `ResolveApplicationContentPath` reste ouvert : Atmosphère délègue cette commande au service Nintendo, sauf exemptions HBL/manual HTML, donc une implémentation locale basée uniquement sur « contenu installé » ne serait pas prouvée.

**Compteur courant : 1 286 IMPL-SRC / 93 PARTIEL / 215 STUB / 78 NOOP / 2 311 NULL / 69 D / 191 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 6 HORS-VERSION / 0 ABSENT / 285 ABI-DIFF / 12 AMBIGU / 1 E = 4 853.** Le HEAD précédent `77477e94` → `61ab696e` est vert X8D24 + provenance ; aucun test PS5 n'est encore revendiqué pour ce nouveau lot.

## Lot filesystem commit / multi-commit — 22/11/2026

Vendor `f6deaab8efa7a0c86e70d816a66792d7ce1811c3` (arbre `0a2a081d41bc7400a25ff833b08d085826345478`) : l'owner actif overlay `IFileSystem` et le source actif `IMultiCommitManager` sont corrigés.

- `IFileSystem::Commit` : **STUB → NOOP** ; le backend host-directory écrit immédiatement et le `Fsa::DoCommit` générique est `NotImplemented`, donc le forwarding serait incorrect.
- `IMultiCommitManager::Add` : **STUB → IMPL-SRC** ; stockage réel des participants, limite 10, rejet null/doublons.
- `IMultiCommitManager::Commit` : **STUB → PARTIEL** ; commit séquentiel des participants puis clear, sans atomicité/provisional/rollback LibHac.

**Compteur courant : 1 287 IMPL-SRC / 94 PARTIEL / 212 STUB / 79 NOOP / 2 311 NULL / 69 D / 191 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 6 HORS-VERSION / 0 ABSENT / 285 ABI-DIFF / 12 AMBIGU / 1 E = 4 853.** Le couple précédent `c864a213` → `a691b553` est vert X8D24 + provenance ; aucune validation PS5 n'est déduite.

## Lot FSP program-index / access-log + NS vulnerability — 22/11/2026

Vendor `ad27e09c7135c3c92ef0202b58ee35423fe74300` (arbre `e6ddae9ffeaca9bc0319e056b7fd38ffb35eb056`) au-dessus du couple vert `f6deaab8`.

- `NeedsUpdateVulnerability` : **3 lignes STUB → NOOP**, `false` explicite faute de base safe-system-version/vulnérabilité Nintendo.
- `OpenSaveDataTransferProhibiter` : **STUB → NOOP**, puisque le transfert de saves n'existe pas dans Encore et qu'aucun état dormant n'est ajouté.
- `RegisterProgramIndexMapInfo` cmd810 : **NULL → IMPL-SRC**, structure 0x20 (`ProgramId`, `MainProgramId`, `ProgramIndex`, reserved) et map réellement conservée.
- `GetProgramIndexForAccessLog` cmd1011 : **STUB → IMPL-SRC**, ABI moderne `u32 index + u32 count`; index cherché avec le `program_id` courant, count égal au nombre d'entrées enregistrées, conformément à LibHac.

**Compteur courant : 1 289 IMPL-SRC / 94 PARTIEL / 207 STUB / 83 NOOP / 2 310 NULL / 69 D / 191 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 6 HORS-VERSION / 0 ABSENT / 285 ABI-DIFF / 12 AMBIGU / 1 E = 4 853.** Le couple précédent `b04bdf55` → `f6deaab8` est vert X8D24 + provenance. Aucun build PS5 ni validation console n'est revendiqué.

## Lot NS lifecycle / état GameCard / faux stubs FS — 22/11/2026

Vendor `0432fba8303ec9ad523c683e728046996cd48dfa`, puis `4483c6a35526d9dc8fc77c70b140ff2358d76dc9` (arbre `7ac58de8cc59a33b21de52fae13371d4f85801fa`).

- `GetGameCardMountFailureEvent`, les deux surfaces `GetSdCardMountStatusChangedEvent`, les deux surfaces `GetGameCardUpdateDetectionEvent` et `ResumeAll` : **6 lignes STUB → NOOP**. Les handles sont réels mais aucun producteur matériel/NS séparé n'est modélisé.
- `TouchApplication` sur ses deux surfaces : **2 lignes STUB → PARTIEL**. Le Title ID doit désormais exister dans le `ContentProviderUnion`, mais Encore ne conserve pas encore la date/metadata de « touch » NS.
- `GetApplicationTerminateResult` : **STUB → IMPL-SRC**. Le service valide le ProgramId de l'applet principale, prend son verrou et renvoie son `terminate_result` réel.
- `IsGameCardApplicationRunning` : le faux `false` constant est remplacé par une requête sur l'applet principale et le `RegisteredCache` GameCard réel. Cette méthode n'est pas une entrée distincte du miroir historique 4 853, donc elle n'augmente pas le compteur.
- `OpenFileSystemWithPatch` reste **PARTIEL** : l'ancien libellé STUBBED était trompeur, mais seuls les Manual RomFS sont réellement ouverts. `FlushAccessLogOnSdCard` est un NOOP local explicite hors catalogue.

**Compteur courant : 1 290 IMPL-SRC / 96 PARTIEL / 198 STUB / 89 NOOP / 2 310 NULL / 69 D / 191 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 6 HORS-VERSION / 0 ABSENT / 285 ABI-DIFF / 12 AMBIGU / 1 E = 4 853.** Ce lot est qualifié au niveau source/provenance uniquement ; aucune validation PS5 n'est revendiquée.

## Lot AM applet stateful / launchable event — 22/11/2026

Vendor `6fc24667f81ce27d07979ad25c0e4743e331f7d0` (arbre `28da2f872d33edf2ad11947991a0cf6c4e592475`).

- `GetLibraryAppletLaunchableEvent` : **STUB → IMPL-SRC** et correction runtime ; récupérer le handle ne signale plus l'événement. `ILibraryAppletCreator::CreateLibraryApplet{,Ex}` reste le producteur après création réussie.
- `GetPreviousProgramIndex` : **STUB → IMPL-SRC**, valeur issue de `AppletManager`.
- `BeginVrModeEx` / `EndVrModeEx` : **2 STUB → IMPL-SRC**, même état `vr_mode_enabled` que les commandes 50/51 déjà classées IMPL-SRC.
- `SetMediaPlaybackStateForApplication`, `SetMediaPlaybackState`, `SetIdleTimeDetectionExtension`, `GetIdleTimeDetectionExtension`, `RequestToAcquireSleepLock`, `ReleaseSleepLock`, `ReleaseSleepLockTransiently` : **7 STUB → PARTIEL**. Les mutations/événements sont réels, mais il manque encore les consommateurs système média/idle/sleep et la réacquisition transitoire.

**Compteur courant : 1 294 IMPL-SRC / 103 PARTIEL / 187 STUB / 89 NOOP / 2 310 NULL / 69 D / 191 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 6 HORS-VERSION / 0 ABSENT / 285 ABI-DIFF / 12 AMBIGU / 1 E = 4 853.** Le couple précédent moteur `35f52e80` → vendor `4483c6a3` est vert X8D24 + provenance. Pas de validation PS5 revendiquée pour `6fc24667`.

## Lot NS update policy + main applet réel — 22/11/2026

Vendor `57081e124b4b7cb6e5ee3226ca3283d94de73021`, puis `1b5b609d3022c5a54a4e3c72613435491c7f9e24` (arbre `a7c6437660846d69a4b049de5641561bd08b96cb`).

- Download task `EnableAutoCommit` / `DisableAutoCommit`, `GetBackgroundNetworkUpdateState` et `GetSystemUpdateNotificationEventForContentDelivery` : **4 STUB → NOOP**, faute de backend Nintendo de téléchargement/update. `OpenSystemUpdateControl` reste STUB car ses commandes enfants sont toutes NULL.
- `GetMainAppletIdentityInfo`, `GetCurrentApplicationId`, `GetMainAppletStorageId` et `SetAutoSleepTimeAndDimmingTimeEnabled` : **4 STUB → IMPL-SRC**.
- `GetMainAppletApplicationControlProperty` : **PARTIEL → IMPL-SRC**. L'identité/NACP ne sont plus lus sur le caller, et le StorageId n'est plus forcé à NAND user : GameCard, SD, NAND user/system sont testés sur les caches réels.

**Compteur courant : 1 299 IMPL-SRC / 102 PARTIEL / 179 STUB / 93 NOOP / 2 310 NULL / 69 D / 191 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 6 HORS-VERSION / 0 ABSENT / 285 ABI-DIFF / 12 AMBIGU / 1 E = 4 853.** Le couple précédent moteur `0c11653f` → vendor `6fc24667` est vert X8D24 + provenance. Pas de validation PS5 revendiquée pour ce lot.

## Lot Home Button + HID policy — 22/11/2026

Vendor `3f8249a2e587a7aa12f93e3ca3546c90eeedbb4e`, puis `2faf00b1d44881bdaebb24e27ecf08938eb83144` (arbre `18e76d6b282831c59c343950fac922d0130d1e09`).

- Home Button : `Begin/EndBlockingHomeButtonShortAndLongPressed` et `EndBlockingHomeButton` passent **3 STUB → IMPL-SRC** ; les flags short/long sont effectivement lus par `WindowSystem` lors des messages Home.
- `Set/GetHomeButtonDoubleClickEnabled` et `BeginBlockingHomeButton` passent **3 STUB → PARTIEL** : état réel, mais double-click sans consommateur et timeout automatique non modélisé.
- HID : **13 STUB → NOOP** pour les deux commandes Npad explicitement neutres côté Horizon et les politiques firmware Nintendo / USB full-key / bouton handheld non applicables au backend PS5.
- Aucun six-axis, event de connexion, Joy-Con rail ou unique-pad n'est fermé artificiellement.

**Compteur courant : 1 302 IMPL-SRC / 105 PARTIEL / 160 STUB / 106 NOOP / 2 310 NULL / 69 D / 191 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 6 HORS-VERSION / 0 ABSENT / 285 ABI-DIFF / 12 AMBIGU / 1 E = 4 853.** Le couple moteur `b9b3e700` → vendor `1b5b609d` est vert X8D24 + provenance. Pas de validation PS5 revendiquée pour ce nouveau lot.

## Lot IApplicationAccessor actif — 22/11/2026

Vendor `b3afcf993cb72713d24a6287dec9334103021179`, puis `dff1bdb769d9d92738ff424aa3f0fe24f92016a2` (arbre `8cc006223327f14da5664476491da0ea364fabf6`). Upstream ciblé : `zortos293/Lichii@9eab742493ba1fe33f60c0f6762dcfcbdb504e96`.

- `GetCurrentLibraryApplet` et `SetHandlesRequestToDisplay` : **2 STUB → PARTIEL**, raccordés à `child_applets` et `handles_request_to_display` réels.
- `TerminateAllLibraryApplets` ID 110, `AreAnyLibraryAppletsLeft` ID 111, `GetApplicationId` ID 120, `GetApplicationLaunchProperty` ID 123 : **4 NULL → IMPL-SRC**.
- `TerminateAllLibraryApplets` adapte l'upstream pour ne pas conserver le verrou parent pendant la terminaison des enfants.
- `IsCompleted` est désormais implémenté aussi sur `IApplicationAccessor`, sans changement de compteur car la ligne dédupliquée était déjà IMPL-SRC via `ILibraryAppletAccessor`.
- `ILibraryAppletCreator` IDs 1/2 restent NULL ; `GetDesirableUids`, `SetApplicationAttribute` et `HasSaveDataAccessPermission` n'ont pas été importés car leur upstream reste un succès minimal.

**Compteur courant : 1 306 IMPL-SRC / 107 PARTIEL / 158 STUB / 106 NOOP / 2 306 NULL / 69 D / 191 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 6 HORS-VERSION / 0 ABSENT / 285 ABI-DIFF / 12 AMBIGU / 1 E = 4 853.** Le couple moteur `422120c8` → vendor `2faf00b1` est vert X8D24 + provenance. Pas de validation PS5 revendiquée pour le nouveau lot.

## Lot NIFM IRequest + scan legacy — 22/11/2026

Vendor `084983e07dd79fb0276dad03a342554628cdb7e0`, puis `76de6f60e3a3e3982bac17ca45b34fa646388a89` (arbre `5508124e6fbc16279e5870434b331154cb7f62b6`).

- `IRequest::{GetRequestState,GetResult,GetSystemEventReadableHandles,Cancel,Submit}` : **5 STUB → IMPL-SRC**. `OnHold` devient un état observable mais transitoire ; la disponibilité réseau hôte tranche ensuite `Accepted/Invalid`, avec événement signalé et accès sérialisé par mutex.
- `GetScanDataOld` ID 11 : **STUB → PARTIEL**. Le buffer historique 0x34 reçoit les SSID/force/connectabilité du vrai cache de scan. Canal/auth/cipher restent à zéro faute de données hôte fiables.
- Preuve ABI : SwIPC distingue `AccessPointDataOld` pour l'ID 11 à partir du changement 4.0.0, avec une taille de 0x34 ; aucun layout 19+ n'est réutilisé aveuglément.
- Preuve comportementale : le modèle de résolution après un `OnHold` observable est cohérent avec les implémentations récentes qui évitent les boucles de polling NIFM offline ; l'adaptation locale utilise le backend réseau Encore, pas Nextendo.

**Compteur courant : 1 311 IMPL-SRC / 108 PARTIEL / 152 STUB / 106 NOOP / 2 306 NULL / 69 D / 191 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 6 HORS-VERSION / 0 ABSENT / 285 ABI-DIFF / 12 AMBIGU / 1 E = 4 853.** Le couple moteur `55e6ed38` → vendor `dff1bdb7` est vert X8D24 + provenance. Pas de validation PS5 revendiquée pour ce nouveau lot.

## Réouverture du statut NULL + NIFM ClientId / creator lifecycle — 22/11/2026

Vendor `50f086881d16f4c6fb89e710ee1e4c6ce6336a04` (arbre `4f015ccf16419403354a03463a79edb4856b501f`).

- **Doctrine corrigée : NULL n'est plus un statut “fermé”.** Un handler NULL signifie désormais qu'aucun handler n'est raccordé dans la source active ; il reste dans le pool de revue jusqu'à justification individuelle ou implémentation.
- `GetClientId` : **STUB → IMPL-SRC**, ABI corrigée en ClientId u32 via buffer type 0x1A, valeur non nulle propre à l'instance.
- `IsAnyInternetRequestAccepted` : **PARTIEL → IMPL-SRC**, désormais indexé par ClientId et alimenté par les IRequest réellement acceptées.
- `IsAnyForegroundRequestAccepted` : **STUB → IMPL-SRC**, compteur global des IRequest acceptées.
- `GetCurrentAccessPointOld` : **NULL → PARTIEL**, layout 0x34 historique et données réseau réelles ; canal/auth/cipher restent inconnus.
- `ILibraryAppletCreator::TerminateAllLibraryApplets` et `AreAnyLibraryAppletsLeft` : **2 NULL → IMPL-SRC** avec le vrai graphe `child_applets`.
- Le couple moteur précédent `a0d12cfc` → vendor `76de6f60` est vert X8D24 + provenance.

**Compteur courant : 1 316 IMPL-SRC / 108 PARTIEL / 150 STUB / 106 NOOP / 2 303 NULL / 69 D / 191 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 6 HORS-VERSION / 0 ABSENT / 285 ABI-DIFF / 12 AMBIGU / 1 E = 4 853.**

**Pool restant à examiner = 2 859 entrées** : 2 303 NULL + 150 STUB + 108 PARTIEL + 285 ABI-DIFF + 12 AMBIGU + 1 SVC. Il ne s'agit pas d'un nombre de bugs prouvés ; les NULL doivent maintenant être triés par firmware, exposition réelle, backend matériel et disponibilité d'un état local/upstream.

## Lot applet common/accessor — NULL runtime actifs — 22/11/2026

Vendor `e58cfc55155e1373758a58e847b5f3de669bd667`, puis `c8b1acd969db74a8250c49bf84dd480e5cd4f7c4` (arbre `30ada5ee51cd74e474250c3132e7a48eb82f3b1d`).

- `IAppletCommonFunctions::SetTerminateResult` : **NULL → IMPL-SRC**, mutation du `terminate_result` réel sous verrou.
- `ILibraryAppletAccessor::SetOutOfFocusApplicationSuspendingEnabled` : **NULL → IMPL-SRC**, appel au `LifecycleManager::SetOutOfFocusSuspendingEnabled` réellement utilisé par la décision de suspension/focus.
- `IsHomeButtonShortPressedBlocked` est aussi raccordé au flag réel consommé par `WindowSystem`, mais ne possède pas de ligne distincte dans le miroir 4 853 : aucun +1 artificiel.
- Le couple moteur précédent `33073f67` → vendor `50f08688` a X8D24 vert et le job de provenance `validate` vert.

**Compteur courant : 1 318 IMPL-SRC / 108 PARTIEL / 150 STUB / 106 NOOP / 2 301 NULL / 69 D / 191 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 6 HORS-VERSION / 0 ABSENT / 285 ABI-DIFF / 12 AMBIGU / 1 E = 4 853.**

**Pool restant à examiner = 2 857 entrées** : 2 301 NULL + 150 STUB + 108 PARTIEL + 285 ABI-DIFF + 12 AMBIGU + 1 SVC.

## Lot performance applet + ApplicationRecord NS — 22/11/2026

Vendor `3bd1221552398a2221035698dd8ef8b6129e19c8`, `b1b3d6e90d6cb81b08c62cfafed0450517192659`, puis correction de staging `6f797482091484fcf3c926ed287ee4afd7618598` (arbre `12879f10b2d866ba5b4536e62bedfcc0c28bb34e`).

- Applet IDs 90/91 : **2 NULL → IMPL-SRC** via LifecycleManager et APM Controller.
- NS `GenerateApplicationRecordCount` : **2 NULL → IMPL-SRC** sur les deux surfaces.
- NS `GetApplicationRecord` : **2 NULL → IMPL-SRC** sur les deux surfaces.
- NS `HasApplicationRecord` ID 910 : **NULL → IMPL-SRC**.
- Le run moteur `2c6c2b70` avait X8D24 vert mais provenance rouge : l'overlay actif `library_applet_accessor.cpp` n'avait pas reçu le handler source. `6f797482` porte désormais le même handler dans `eden-backports` et met à jour les reçus `upstream` + `active`. Aucune validation PS5 n'est revendiquée avant les nouveaux checks.

**Compteur courant : 1 325 IMPL-SRC / 108 PARTIEL / 150 STUB / 106 NOOP / 2 294 NULL / 69 D / 191 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 6 HORS-VERSION / 0 ABSENT / 285 ABI-DIFF / 12 AMBIGU / 1 E = 4 853.**

**Pool restant à examiner = 2 850 entrées** : 2 294 NULL + 150 STUB + 108 PARTIEL + 285 ABI-DIFF + 12 AMBIGU + 1 SVC.

## Lot firmware contrôleur + layout clavier — 22/11/2026

Vendor `0d21ded69e049ee9716a376f6d1730d2ca54303f`, puis correction de staging NS `aea996472c7c7146795f3bbbb9e04e9bc0895a47` (arbre `b3b59fda00af67a52aa5bf5b8125df90ae312c26`).

- `SetControllerFirmwareUpdateSection` : **NULL → IMPL-SRC**.
- `SetDesirableKeyboardLayout` : **NULL → IMPL-SRC**.
- `GetDesirableKeyboardLayout` : **STUB → IMPL-SRC**.
- `IsInControllerFirmwareUpdateSection`, déjà IMPL-SRC au compteur, passe d'un `false` constant à la vraie valeur applet.
- La provenance NS est corrigée : les déclarations `GenerateApplicationRecordCount`, `GetApplicationRecord`, `HasApplicationRecord` existent désormais aussi dans le header overlay actif et le manifeste a les nouveaux reçus `upstream` + `active`.

**Compteur courant : 1 328 IMPL-SRC / 108 PARTIEL / 149 STUB / 106 NOOP / 2 292 NULL / 69 D / 191 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 6 HORS-VERSION / 0 ABSENT / 285 ABI-DIFF / 12 AMBIGU / 1 E = 4 853.**

**Pool restant à examiner = 2 847 entrées** : 2 292 NULL + 149 STUB + 108 PARTIEL + 285 ABI-DIFF + 12 AMBIGU + 1 SVC.

## Recheck NULL — System NAND + NIFM default IP — 22/11/2026

Vendor `40596a94e35789a57e9ee8236e0e6c4362cd1765` (arbre `b6631a93395622feea9f86abdbb0b79dd6c4993d`).

- `IsSystemProgramInstalled` ID63 : **2 NULL → IMPL-SRC** car les deux surfaces catalogue partagent le même `IApplicationManagerInterface`, qui consulte le cache System NAND réel.
- `GetDefaultIpSetting` ID27 et `SetDefaultIpSetting` ID28 : **2 NULL → IMPL-SRC**. ABI vérifiée dans SwIPC : `IpSettingData`, buffer 0x1A/0x19, taille **0xC2**. État partagé initialisé depuis le backend réseau Encore, proxy off et MTU 1500, puis round-trip complet du setter.
- Le rouge provenance de `d84b0ff3` était uniquement un hash actif périmé de `self_controller.h`; `fe0ccc13` le corrige et est ancêtre du vendor final.
- X8D24 du couple précédent était vert ; le présent couple doit passer ses propres checks. Aucune validation PS5 revendiquée.

**Compteur courant : 1 332 IMPL-SRC / 108 PARTIEL / 149 STUB / 106 NOOP / 2 288 NULL / 69 D / 191 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 6 HORS-VERSION / 0 ABSENT / 285 ABI-DIFF / 12 AMBIGU / 1 E = 4 853.**

**Pool restant à examiner = 2 843 entrées** : 2 288 NULL + 149 STUB + 108 PARTIEL + 285 ABI-DIFF + 12 AMBIGU + 1 SVC.

## Recheck NULL — terminate-result NS + NIFM controls — 22/11/2026

Vendor `bc3d538f2c413489b2d881259b57a4c44b6698f9` (arbre `8307e210806b858beea5f87c49434685fe93831d`).

- NS IDs 56/57 : **4 NULL → IMPL-SRC** sur les deux surfaces catalogue ; `terminate_result` du main applet devient la source de vérité après validation du ProgramId.
- NIFM IDs 29/30 : **2 NULL → IMPL-SRC**, alias directs des setters actifs radio/Ethernet.
- NIFM ID12 `GetCurrentIpAddress` et ID20 `IsEthernetCommunicationEnabled` : **2 PARTIEL → IMPL-SRC** ; état hôte/room et état Ethernet réel.
- `IsWiredConnectionAvailable` est ajouté au runtime mais hors des 4 853 lignes, donc non compté.
- Baseline précédente `5b5bcfc3` → `40596a94` : X8D24 + provenance verts. Aucun test PS5 pour ce lot.

**Compteur courant : 1 340 IMPL-SRC / 106 PARTIEL / 149 STUB / 106 NOOP / 2 282 NULL / 69 D / 191 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 6 HORS-VERSION / 0 ABSENT / 285 ABI-DIFF / 12 AMBIGU / 1 E = 4 853.**

**Pool restant à examiner = 2 835 entrées** : 2 282 NULL + 149 STUB + 106 PARTIEL + 285 ABI-DIFF + 12 AMBIGU + 1 SVC.

## Recheck NULL — conversions langue NS — 22/11/2026

Vendor `0897a295624827e95d9248d85ea8274e75584693` (arbre `06e36212834c87b6d464f5349bf26851e336362f`).

- `ConvertLanguageCodeToApplicationLanguage` : **3 NULL → IMPL-SRC** sur les deux surfaces application-manager et l'interface read-only propriétaire.
- `SelectApplicationDesiredLanguage` : **1 NULL → IMPL-SRC**, en réutilisant `GetApplicationDesiredLanguage`.
- Une seule source de vérité : `ConvertToApplicationLanguage` / les priorités existantes de `language.cpp`. Aucun mapping parallèle inventé.
- Baseline précédente `4b9861f8` → `bc3d538f` : X8D24 + provenance verts. Aucun test PS5 pour ce lot.

**Compteur courant : 1 344 IMPL-SRC / 106 PARTIEL / 149 STUB / 106 NOOP / 2 278 NULL / 69 D / 191 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 6 HORS-VERSION / 0 ABSENT / 285 ABI-DIFF / 12 AMBIGU / 1 E = 4 853.**

**Pool restant à examiner = 2 831 entrées** : 2 278 NULL + 149 STUB + 106 PARTIEL + 285 ABI-DIFF + 12 AMBIGU + 1 SVC.

## Recheck NULL — GameCard NS + FSP data/save reader — 22/11/2026

Vendor `a7c2afb34048ff001b9ff80aad4ec6aa32aff703` (arbre `9b7cefd10652c20bdd3c0a62599e42e35e40c568`), chaîne 8f842b50 → 00a7d197 → a7c2afb3.

- **3 NULL → IMPL-SRC** côté NS pour l'état GameCard réel.
- FSP `OpenDataStorageByProgramId` ID201 : **NULL → IMPL-SRC**, via le chemin Data NCA actif.
- FSP `OpenSaveDataInfoReader` ID60 : **NULL → PARTIEL** ; agrégation des backings `System/User/Temporary`, sans inventer les espaces que `SaveDataFactory` ne représente pas.
- Baseline précédente `3a5e6121` → `0897a295` : X8D24 + provenance verts. Aucun test PS5 revendiqué pour le nouveau lot.

**Compteur courant : 1 348 IMPL-SRC / 107 PARTIEL / 149 STUB / 106 NOOP / 2 273 NULL / 69 D / 191 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 6 HORS-VERSION / 0 ABSENT / 285 ABI-DIFF / 12 AMBIGU / 1 E = 4 853.**

**Pool restant à examiner = 2 827 entrées** : 2 273 NULL + 149 STUB + 107 PARTIEL + 285 ABI-DIFF + 12 AMBIGU + 1 SVC.

## Recheck NULL — stubs Horizon officiels + NIFM sleep/wake — 22/11/2026

Vendor `36100c1740ad18d53949761846f21ffeb8a0f472` (arbre `c9042596bcfece3250e1574ab44061c182ff54ee`).

- `PutToSleep` / `WakeUp` : **2 NULL → NOOP**, commandes NIFM sans I/O et sans équivalent de daemon réseau suspendu dans Encore.
- **15 NULL appletAE → D** : SwitchBrew les documente comme stubs Horizon retournant une erreur. Elles ne constituent donc pas un backlog d'implémentation fonctionnelle pour Encore.
- `NeedsToExitProcess` a été testé localement contre le flag lifecycle puis revert avant pin, la documentation firmware prouvant que ce raccord aurait divergé de l'OS.
- Baseline précédente `22df8a22` → `a7c2afb3` : X8D24 + provenance verts. Aucun test PS5 revendiqué pour ce nouveau lot.

**Compteur courant : 1 348 IMPL-SRC / 107 PARTIEL / 149 STUB / 108 NOOP / 2 256 NULL / 84 D / 191 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 6 HORS-VERSION / 0 ABSENT / 285 ABI-DIFF / 12 AMBIGU / 1 E = 4 853.**

**Pool restant à examiner = 2 810 entrées** : 2 256 NULL + 149 STUB + 107 PARTIEL + 285 ABI-DIFF + 12 AMBIGU + 1 SVC.

## Recheck NULL — ExtraStorage applet — 22/11/2026

Vendor `ebc5a68a9b5ac4316aa8c7ba3f6bebeab5817e5c` (arbre `7a96cbc2af79a866e194c28fa33e438d9c897712`).

- `PushExtraStorage`, `PopExtraStorage`, `GetPopExtraStorageEvent`, `UnpopExtraStorage` : **4 NULL → IMPL-SRC**.
- Implémentation causale : ajout du canal `extra_storage` au `AppletDataBroker`, réutilisant la sémantique réelle `AppletStorageChannel` et son événement kernel.
- Baseline précédente moteur `ce2a1673` → vendor `36100c17` : X8D24 + provenance verts. Aucun test PS5 revendiqué pour ce nouveau lot.

**Compteur courant : 1 352 IMPL-SRC / 107 PARTIEL / 149 STUB / 108 NOOP / 2 252 NULL / 84 D / 191 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 6 HORS-VERSION / 0 ABSENT / 285 ABI-DIFF / 12 AMBIGU / 1 E = 4 853.**

**Pool restant à examiner = 2 806 entrées** : 2 252 NULL + 149 STUB + 107 PARTIEL + 285 ABI-DIFF + 12 AMBIGU + 1 SVC.

## Recheck NULL — politiques NIFM — 22/11/2026

Vendor `05784b605535c987e1619c9b28e36f7752ba735b` (arbre `7502d3834222f5e3b35e4cb13f48d2755ab79bfe`).

- `SetExclusiveClient` : **NULL → PARTIEL**, `ClientId` 4 octets lu depuis le buffer ABI 0x19 et conservé.
- `Set/GetAcceptableNetworkTypeFlag` : **2 NULL → PARTIEL**, round-trip d'état réel.
- `Shutdown` : **NULL → NOOP**, aucun processus NIFM indépendant à stopper dans Encore.
- Les effets d'exclusivité et de filtrage réseau restent ouverts jusqu'à raccordement à la sélection/acceptation des requêtes.
- Baseline précédente moteur `04ebfb45` → vendor `ebc5a68a` : X8D24 + provenance verts.

**Compteur courant : 1 352 IMPL-SRC / 110 PARTIEL / 149 STUB / 109 NOOP / 2 248 NULL / 84 D / 191 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 6 HORS-VERSION / 0 ABSENT / 285 ABI-DIFF / 12 AMBIGU / 1 E = 4 853.**

**Pool restant à examiner = 2 805 entrées** : 2 248 NULL + 149 STUB + 110 PARTIEL + 285 ABI-DIFF + 12 AMBIGU + 1 SVC.

## Recheck NULL — canaux Friend Invitation / Notification — 22/11/2026

Vendor `d1e41151f5e23b1ff2653c937b04ff5e344e29b0` (arbre `34dbfc91c0b5b086ef220eaee856627e37ac20e3`).

- `PushToFriendInvitationStorageChannel`, `PushToNotificationStorageChannel`, `TryPopFromNotificationStorageChannel` : **3 NULL → IMPL-SRC**.
- Owner actif vérifié : accessor + `Applet` depuis `sources/eden`; `application_functions.cpp` est remplacé explicitement par le maintained owner `encore-active/eden-core` dans `headless/CMakeLists.txt`.
- Les deux pushes copient les données du vrai `IStorage`, publient sous verrou puis signalent l'événement du canal ; le pop Notification reproduit le contrat déjà utilisé par Friend Invitation.
- Baseline précédente moteur `efe0693e` → vendor `05784b60` : X8D24 + provenance verts. Aucun test PS5 revendiqué pour ce lot.

**Compteur courant : 1 355 IMPL-SRC / 110 PARTIEL / 149 STUB / 109 NOOP / 2 245 NULL / 84 D / 191 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 6 HORS-VERSION / 0 ABSENT / 285 ABI-DIFF / 12 AMBIGU / 1 E = 4 853.**

**Pool restant à examiner = 2 802 entrées** : 2 245 NULL + 149 STUB + 110 PARTIEL + 285 ABI-DIFF + 12 AMBIGU + 1 SVC.

## Recheck NULL — AppletBoundChannel — 22/11/2026

Vendor `b217369d3f01b2958eae58815f190080a8b77296` (arbre `d788055b10aa228029f24699acd653609c972baa`).

- `PushToAppletBoundChannel` et `TryPopFromAppletBoundChannel` : **2 NULL → IMPL-SRC**.
- Contrat `IStorage` confirmé par libnx/FewFW ; file réelle dans l'état `Applet`, verrouillée, avec `ResultNoDataInChannel` sur canal vide.
- Baseline précédente moteur `e89ca072` → vendor `d1e41151` : X8D24 + provenance verts. Aucun test PS5 revendiqué.

**Compteur courant : 1 357 IMPL-SRC / 110 PARTIEL / 149 STUB / 109 NOOP / 2 243 NULL / 84 D / 191 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 6 HORS-VERSION / 0 ABSENT / 285 ABI-DIFF / 12 AMBIGU / 1 E = 4 853.**

**Pool restant à examiner = 2 800 entrées** : 2 243 NULL + 149 STUB + 110 PARTIEL + 285 ABI-DIFF + 12 AMBIGU + 1 SVC.

## Recheck NULL — huit paires `set:sys` persistantes — 22/11/2026

Vendor `694becfbf6a27cecb907d8be5b0315c269654fa7` (arbre `ba9035d2e9289d05d89a611c19477b91f3243d1f`) ; moteur épinglé par le présent lot.

- **16 NULL → IMPL-SRC** : `Get/SetLdnChannel`, `Get/SetExternalRtcResetFlag`, `Get/SetUsbFullKeyEnableFlag`, `Get/SetHeadphoneVolumeWarningCount`, `Get/SetBluetoothAfhEnableFlag`, `Get/SetBluetoothBoostEnableFlag`, `Get/SetHeadphoneVolumeUpdateFlag`, `Get/SetPctlReadyFlag`.
- Les champs existent dans `SystemSettings` ; lecture et écriture sont raccordées à son mécanisme de persistance existant `SetSaveNeeded()`. Un flag matériel reste une configuration invitée, non une preuve que le matériel Nintendo est émulé.
- L'ABI des 7 couples booléens/entiers a été recroisée avec les descriptions IPC historiques, signatures 1 ou 4 octets ; unités source natives et chemin de compilation vérifiés sur CMake, sans build PS5.
- Les deux checks attendus de ce nouveau couple doivent être vérifiés avant de le déclarer qualifié sur hôte.

**Compteur courant : 1 373 IMPL-SRC / 110 PARTIEL / 149 STUB / 109 NOOP / 2 227 NULL / 84 D / 191 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 6 HORS-VERSION / 0 ABSENT / 285 ABI-DIFF / 12 AMBIGU / 1 E = 4 853.**

**Pool restant à examiner = 2 784 entrées** : 2 227 NULL + 149 STUB + 110 PARTIEL + 285 ABI-DIFF + 12 AMBIGU + 1 SVC.

## Recheck NULL — configuration PTM, RTC, applets, calibration et USB — 22/11/2026

Vendor `0aa3af72`, puis `9aa3b2568b3f74bd124f3923e88116a52c1c589a` (arbre `fbd04c1ab3bc6858e873e48fb6c32c17db7a335e`).

- **20 NULL → IMPL-SRC** : `Get/SetDataDeletionSettings`, `GetInitialSystemAppletProgramId`, `GetOverlayDispProgramId`, `Get/SetPtmBatteryLot`, `Get/SetPtmFuelGaugeParameter`, `Set/GetShutdownRtcValue`, `Get/SetAnalogStickUserCalibrationL/R`, `Get/SetPtmBatteryVersion` et `Get/SetUsb30HostEnableFlag`, `Get/SetUsb30DeviceEnableFlag`.
- Les structures et champs SystemSettings, PrivateSettings et DeviceSettings existaient. Réponses liées à leur état persistant, sans inventer de périphérique Nintendo sur PS5. ABI IPC confirmée contre libnx et les définitions générées.
- Moteur repointé sur `9aa3b2568b3f74bd124f3923e88116a52c1c589a`, source sélectionnée par CMake. Aucun build PS5 ni test gameplay revendiqué ; attendre les contrôles CI du nouveau couple avant qualification hôte.

**Compteur courant : 1 393 IMPL-SRC / 110 PARTIEL / 149 STUB / 109 NOOP / 2 207 NULL / 84 D / 191 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 6 HORS-VERSION / 0 ABSENT / 285 ABI-DIFF / 12 AMBIGU / 1 E = 4 853.**

**Pool restant à examiner = 2 764 entrées** : 2 207 NULL + 149 STUB + 110 PARTIEL + 285 ABI-DIFF + 12 AMBIGU + 1 SVC.

## Recheck NULL — thème / zoom / flags et PTM — 22/11/2026

Vendor `407b42a985c1d8558a516d41d5c03a216f4da433` (arbre `d49fdafca026f9a973a84ad42cf0981a0ead8b10`). **9 NULL → IMPL-SRC** pour `GetWebInspectorFlag`, `SetChineseTraditionalInputMethod`, `Get/SetPtmCycleCountReliability`, `Get/SetThemeSettings`, `Get/SetZoomFlag`, `GetMemoryUsageRateFlag`. `SetFieldTestingFlag` est aussi implémentée en C++, sans nouvelle ligne du miroir à reclasser : **10 méthodes source, +9 au compteur**. États existants et persistance via `SetSaveNeeded()` ; compatibilité de contrat IPC source vérifiée, aucun effet matériel ou test PS5 revendiqué. Couple précédent `caeb314e` → `9aa3b256` vert X8D24 et provenance ; nouveau couple à valider.

**Compteur courant : 1 402 IMPL-SRC / 110 PARTIEL / 149 STUB / 109 NOOP / 2 198 NULL / 84 D / 191 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 6 HORS-VERSION / 0 ABSENT / 285 ABI-DIFF / 12 AMBIGU / 1 E = 4 853.**

**Pool restant à examiner = 2 755 entrées** : 2 198 NULL + 149 STUB + 110 PARTIEL + 285 ABI-DIFF + 12 AMBIGU + 1 SVC.

## Lot `set:sys` RTC et protection auditive — 23/11/2026

**Vendor `b0228bfc2c634ee3b7c61bec56d513b1c4673601`**, sur la branche secondaire NS1, et gitlink moteur repointé dans le même lot.

- `GetRequiresRunRepairTimeReviser` (141) / `SetRequiresRunRepairTimeReviser` (142) : **2 NULL → IMPL-SRC** ; booléen d'état Horizon déjà présent dans `SystemSettings`, lecture / écriture et `SetSaveNeeded()`. La signature bool est corroborée par les API libnx et les IDs par SwitchBrew.
- `Get/SetHearingProtectionSafeguardFlag` (207/208) et `Get/SetHearingProtectionSafeguardRemainingTime` (209/210) : **4 handlers source supplémentaires**, réutilisant les champs persistants bool et s64. SwitchBrew documente ces commandes NS1 à partir de 14.0.0. **Elles sont absentes des 4 853 lignes du miroir historique et ne modifient donc pas artificiellement le dénominateur ni IMPL-SRC de ce miroir.** Cette lacune du miroir doit être conservée comme réserve d'exhaustivité.
- Source réellement compilable : `sources/eden/src/core/hle/service/set/system_settings_server.{cpp,h}` listée dans `encore-active/eden-backports/src/core/CMakeLists.txt` ; aucun remplacement de ces deux fichiers dans le répertoire de backports de service Set. Champs natifs vérifiés dans `setting_formats/system_settings.h`.
- Vérification immédiate : cohérence des 6 enregistrements IPC, déclarations et définitions, sans compilation hôte ni PS5 à ce stade. Ne pas assimiler les états de settings à une émulation des périphériques Nintendo.

**Compteur du miroir NS1 : 1 404 IMPL-SRC / 110 PARTIEL / 149 STUB / 109 NOOP / 2 196 NULL / 84 D / 191 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 6 HORS-VERSION / 0 ABSENT / 285 ABI-DIFF / 12 AMBIGU / 1 E = 4 853.**

**Pool restant à examiner = 2 753 entrées** : 2 196 NULL + 149 STUB + 110 PARTIEL + 285 ABI-DIFF + 12 AMBIGU + 1 SVC. Aucun gain FPS ni résultat console revendiqué.

## Lot `set:sys` calibration six axes persistante — 23/11/2026

**Vendor `0aa309cfbc3489073cc5586b5745be41c2d23e19`**, moteur secondaire repointé vers ce SHA.

- **12 NULL → IMPL-SRC** : commandes 128–135 et 145–148, six paires Get/Set de biais et gains d'accélération et de vitesse angulaire, biais temporel et accélération angulaire.
- Les commandes enregistrées utilisent les champs déjà persistants de `SystemSettings` : `Common::Vec<f32, 3>` (12 octets) et `std::array<u8, 0x24>` (36 octets). Chaque Set déclenche `SetSaveNeeded()`. Le libnx courant corrobore les IDs 128–135/145–148 ainsi que le passage direct de leurs structures en données IPC (pas de tampon alias inventé).
- **Portée réelle : configuration invitée persistante**, pas simulation du capteur inertiel ni garantie de calibration physique, et pas de progrès GPU attribué à ces fonctions.
- Propriétaire C++ : `sources/eden/src/core/hle/service/set/system_settings_server.{cpp,h}` listé par `encore-active/eden-backports/src/core/CMakeLists.txt`, sans remplacement correspondant dans le répertoire de backports. Contrôle statique des 12 enregistrements / déclarations / définitions ; hôte/PS5 à vérifier sur ce nouveau couple.

**Compteur du miroir NS1 : 1 416 IMPL-SRC / 110 PARTIEL / 149 STUB / 109 NOOP / 2 184 NULL / 84 D / 191 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 6 HORS-VERSION / 0 ABSENT / 285 ABI-DIFF / 12 AMBIGU / 1 E = 4 853.**

**Pool restant à examiner = 2 741 entrées** : 2 184 NULL + 149 STUB + 110 PARTIEL + 285 ABI-DIFF + 12 AMBIGU + 1 SVC. Les quatre commandes NS1 207–210 déjà raccordées hors du miroir restent une réserve d'exhaustivité, non un gain chiffré supplémentaire.

**Réconciliation de l'index physique (23/11/2026) :** le catalogue Markdown contient actuellement **117 lignes SVC + 4 777 lignes IPC**, dont **23 META** et **27 DUP** ; le total déduplicable physiquement est donc **4 844 références**, alors que le dénominateur historique documenté reste **4 853**. Les **9 références d'écart** se répartissent, par soustraction des statuts, en **3 IMPL-SRC, 1 PARTIEL et 5 NOOP**, sans identification ligne par ligne. Sur les lignes physiquement présentes, le pool de revue est **2 738** (2 182 NULL + 149 STUB + 109 PARTIEL, dont 3 SVC, + 285 ABI-DIFF + 12 AMBIGU + 1 E). Le pool historique conservé est **2 739** en incluant la ligne PARTIEL non matérialisée. **Ne pas annoncer le catalogue exhaustif ni supprimer neuf références arbitrairement** ; réconcilier ces identités avec les sources de l'import avant tout changement du dénominateur.

## Correctif ABI ThemeId — 23/11/2026

**Vendor `c8688e83435eb085285a18b581cea39b701ad266`** : les deux commandes `GetThemeId` et `SetThemeId` conservent leur statut **IMPL-SRC** mais utilisent désormais un payload `std::array<u64, 0x10>` (0x80 octets, alignement 8) conformément à `SetSysThemeId` de libnx. Le sérialiseur `cmif_serialization.h` impose `PrevAlign <= ArgAlign` et place l'argument après `s32 type` à l'offset 8 ; l'ancien `std::array<u8, 0x80>` aurait échoué à la compilation (alignement 1). Le stockage persistant existant reste un tableau d'octets, converti par `memcpy` à taille vérifiée. Exact vendor SHA/arbre consignés dans les deux gardes de provenance. **Aucun +2 additionnel au compteur**, ni compilation PS5 revendiquée.

## Lot `set:sys` ThemeId typé — 23/11/2026

**Vendor `b84e58810ccd509acfbd00a8dda6ada8c0dcdabc`**, gitlink moteur secondaire aligné sur cet objet Git exact.

- `GetThemeId` (168) et `SetThemeId` (169) : **2 NULL → IMPL-SRC**. Le type `s32` 0/1 sélectionne `theme_id_type0` ou `theme_id_type1`, chacun de 0x80 octets, déjà persistés par `SystemSettings`. Les autres types sont rejetés ; `SetThemeId` marque la sauvegarde.
- ABI recroisée avec libnx (GET type en entrée + `ThemeId[0x80]` en retour ; SET type puis `ThemeId` en entrée) et SwitchBrew pour l'ID firmware 7.0.0+. Aucune ressource de thème Nintendo n'est inventée et ce raccord ne valide pas le rendu de thème sur PS5.
- CI : la révision moteur précédente `b688366c` a X8D24 vert mais provenance rouge sur la whitelist ancienne ; le suivi exact de SHA/arbre des commits RTC et six axes a été corrigé au moteur `6c030259`. Le présent commit ajoute également l'empreinte Git du nouveau vendor dans la même table stricte.

**Compteur du miroir NS1 : 1 418 IMPL-SRC / 110 PARTIEL / 149 STUB / 109 NOOP / 2 182 NULL / 84 D / 191 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 6 HORS-VERSION / 0 ABSENT / 285 ABI-DIFF / 12 AMBIGU / 1 E = 4 853.**

**Pool restant à examiner = 2 739 entrées** : 2 182 NULL + 149 STUB + 110 PARTIEL + 285 ABI-DIFF + 12 AMBIGU + 1 SVC. Qualification hôte et console du nouveau couple non encore acquise.

## Lot `set:sys` réparation / discovery / ThemeKey — 23/11/2026

**Vendor `33858387c023030896e649c84e1df806a3352889`** (arbre `8bfc545041776e2c88592fb5561020aaed20fc82`) sélectionné par le gitlink de la branche NS1 secondaire.

- **6 NULL → IMPL-SRC** : `Get/SetInRepairProcessEnableFlag` (115/116), `Get/SetServiceDiscoveryControlSettings` (122/123), `Get/SetThemeKey` (177/178).
- Les deux premiers couples réutilisent les champs persistants de `ApplnSettings` (`bool` et `u32`) ; `ThemeKey` réutilise les 16 octets `theme_key` de `SystemSettings`. Chaque setter marque la sauvegarde via `SetSaveNeeded()`.
- ABI recroisée avec libnx : bool brut pour 115/116, u32 brut pour 122/123, `FsArchiveMacKey { u8 key[0x10] }` pour 177/178. Aucun backend matériel supplémentaire ni valeur synthétique n'est introduit.
- Les fichiers `system_settings_server.{cpp,h}` restent les propriétaires réellement listés par `encore-active/eden-backports/src/core/CMakeLists.txt` sans remplacement du même chemin.
- Le couple code précédent moteur `28b75cca` → vendor `c8688e83` a **X8D24 + Verify pinned vendor verts**. Le présent couple nécessite ses propres contrôles ; aucun build PS5 ni gameplay n'est revendiqué.

**Compteur historique : 1 424 IMPL-SRC / 110 PARTIEL / 149 STUB / 109 NOOP / 2 176 NULL / 84 D / 191 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 6 HORS-VERSION / 0 ABSENT / 285 ABI-DIFF / 12 AMBIGU / 1 E = 4 853.**

**Pool historique restant à examiner = 2 733** : 2 176 NULL + 149 STUB + 110 PARTIEL + 285 ABI-DIFF + 12 AMBIGU + 1 SVC.

## Lot `set:sys` BLE pairing / Account Online Storage — 23/11/2026

**Vendor `3b564c2d141b94fecc78e3f68753e00aea009180`** (arbre `46f035e4e6a40dee8cb751651f9c4f2c0a307a8b`) sur la branche secondaire NS1.

- **4 NULL → IMPL-SRC** : `Set/GetBlePairingSettings` (143/144) et `Get/SetAccountOnlineStorageSettings` (154/155).
- BLE utilise le buffer MapAlias documenté par libnx, entrées de **0x80 octets**, capacité persistante **10** ; Account Online Storage utilise des entrées **0x40**, capacité **8**. Les getters bornent le nombre copié à la fois par le compteur persistant, la capacité locale et le buffer IPC fourni.
- Les setters refusent explicitement un tableau plus grand que le stockage local au lieu de déclencher l'`ASSERT` utilisé par certains handlers historiques ; les compteurs et données sont ensuite persistés via `SetSaveNeeded()`.
- Aucun service réseau Nintendo n'est simulé : ce lot implémente seulement le contrat de stockage/récupération des settings.
- Le couple précédent est en CI ; le présent couple doit avoir ses propres contrôles. Aucun build PS5 ni validation gameplay revendiqué.

**Compteur historique : 1 428 IMPL-SRC / 110 PARTIEL / 149 STUB / 109 NOOP / 2 172 NULL / 84 D / 191 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 6 HORS-VERSION / 0 ABSENT / 285 ABI-DIFF / 12 AMBIGU / 1 E = 4 853.**

**Pool historique restant à examiner = 2 729** : 2 172 NULL + 149 STUB + 110 PARTIEL + 285 ABI-DIFF + 12 AMBIGU + 1 SVC.

## Lot `set:sys` EDID / SSL hosts / HostFS mount — 23/11/2026

**Vendor `29b1cb6de394dc0ecc168481a8059e8f70a1b92d`** (arbre `449492017d849f1669f327d9ca8dd06b6f78daf0`) sur la branche secondaire NS1.

- **4 NULL → IMPL-SRC** : `Get/SetEdid` (41/42), `GetAllowedSslHosts` (139), `GetHostFsMountPoint` (140).
- `EDID` utilise le buffer HIPC Pointer fixe de **0x100 octets** attendu par libnx et le champ persistant `SystemSettings::edid`.
- `AllowedSslHosts` renvoie jusqu'à **8 entrées de 0x100 octets** via MapAlias, bornées par le buffer de sortie ; `HostFsMountPoint` renvoie le bloc persistant fixe de **0x100 octets** via MapAlias.
- Ce sont des contrats de lecture/écriture de settings ; aucun certificat SSL, montage HostFS ou écran physique PS5 n'est inventé.
- Le couple précédent doit être qualifié séparément ; aucun build PS5 ni validation gameplay revendiqué.

**Compteur historique : 1 432 IMPL-SRC / 110 PARTIEL / 149 STUB / 109 NOOP / 2 168 NULL / 84 D / 191 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 6 HORS-VERSION / 0 ABSENT / 285 ABI-DIFF / 12 AMBIGU / 1 E = 4 853.**

**Pool historique restant à examiner = 2 725** : 2 168 NULL + 149 STUB + 110 PARTIEL + 285 ABI-DIFF + 12 AMBIGU + 1 SVC.

## Lot `set:sys` BacklightSettingsEx — 23/11/2026

**Vendor `131cb5828f196fcd46f78a217eec43953e0bd083`** (arbre `e193ac362ae443d8e96fb575fd199df38aea83be`) sur la branche secondaire NS1.

- **2 NULL → IMPL-SRC** : `GetBacklightSettingsEx` (107) et `SetBacklightSettingsEx` (108).
- Libnx décrit `SetSysBacklightSettingsEx` sur **0x2C octets**, exactement la taille du bloc persistant `backlight_settings_mixed_up`. Le handler effectue donc un round-trip brut de ce bloc et persiste les écritures.
- Les commandes historiques 9/10 restent NULL : leur structure fait **0x28** et une conversion 0x28↔0x2C n'est pas prouvée. Aucun raccourci n'est pris pour gagner deux lignes supplémentaires.
- Aucun contrôle matériel de rétroéclairage PS5 n'est revendiqué ; ce lot couvre uniquement le contrat de settings.

**Compteur historique : 1 434 IMPL-SRC / 110 PARTIEL / 149 STUB / 109 NOOP / 2 166 NULL / 84 D / 191 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 6 HORS-VERSION / 0 ABSENT / 285 ABI-DIFF / 12 AMBIGU / 1 E = 4 853.**

**Pool historique restant à examiner = 2 723** : 2 166 NULL + 149 STUB + 110 PARTIEL + 285 ABI-DIFF + 12 AMBIGU + 1 SVC.

## Lot `set:sys` Bluetooth / NX controller settings — 23/11/2026

**Vendor `032e41924a3d82f654ebbab15601eb609dbf4fcf`** (arbre `e1e916b5e51b17b542eea5010889dacc850077fb`) sur la branche secondaire NS1.

- **4 NULL → IMPL-SRC dans le miroir** : `Set/GetBluetoothDevicesSettings` (11/12) et `Get/SetNxControllerSettings` (97/98).
- **2 handlers runtime supplémentaires hors miroir 4 853** : `Get/SetNxControllerSettingsEx` (205/206), présents dans libnx pour 13.0.0+ mais absents de l'index historique Markdown ; aucun +2 artificiel au compteur.
- Bluetooth : structure libnx exactement **0x200 octets**, stockage local **10×0x200** ; compteur persistant lu/écrit sur ses 4 octets.
- NX legacy : payload ABI **0x29 octets** dans un slot persistant 0x40 ; seuls les octets contractuels sont exposés et le padding local est remis à zéro sur Set.
- NX Ex : payload ABI **0x42C octets** dans un slot persistant 0x800, même séparation entre données invitées et padding réservé.
- Les buffers sont MapAlias, bornés à la capacité locale. Aucun backend Bluetooth/HID matériel n'est simulé.

**Compteur historique : 1 438 IMPL-SRC / 110 PARTIEL / 149 STUB / 109 NOOP / 2 162 NULL / 84 D / 191 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 6 HORS-VERSION / 0 ABSENT / 285 ABI-DIFF / 12 AMBIGU / 1 E = 4 853.**

**Pool historique restant à examiner = 2 719** : 2 162 NULL + 149 STUB + 110 PARTIEL + 285 ABI-DIFF + 12 AMBIGU + 1 SVC.

## Lot `set:sys` NetworkSettings + borne SSL — 23/11/2026

**Vendor `3d97ca836c8825fedfc23de76a0c3295a93469fb`** (arbre `1971dc01df3359a0dc74df18be6ef1e90d60937b`) sur la branche secondaire NS1.

- **2 NULL → IMPL-SRC** : `SetNetworkSettings` (1) et `GetNetworkSettings` (2).
- Libnx décrit une entrée `SetSysNetworkSettings` de **0x1B0 octets** ; Eden conserve jusqu'à **32 slots de 0x400**. Les handlers n'exposent que les 0x1B0 octets ABI et remettent à zéro le padding réservé lors des écritures.
- Le compteur `network_setting_count` est borné par la capacité locale et le buffer IPC MapAlias.
- Correctif sans changement de compteur : `GetAllowedSslHosts` utilise désormais `allowed_ssl_host_count` au lieu de renvoyer automatiquement les 8 slots persistants.
- Le couple moteur précédent `595e6100` → vendor `131cb582` est **X8D24 + provenance vert**. Le présent couple requiert ses propres contrôles ; aucun build PS5 n'est revendiqué.

**Compteur historique : 1 440 IMPL-SRC / 110 PARTIEL / 149 STUB / 109 NOOP / 2 160 NULL / 84 D / 191 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 6 HORS-VERSION / 0 ABSENT / 285 ABI-DIFF / 12 AMBIGU / 1 E = 4 853.**

**Pool historique restant à examiner = 2 717** : 2 160 NULL + 149 STUB + 110 PARTIEL + 285 ABI-DIFF + 12 AMBIGU + 1 SVC.

## Lot Location Resolver manager — 23/11/2026

**Vendor `682f74ead16c33caff0da4d9e89d025a4cb85ea5`** (arbre `51965f0e80d8c18df8c5f829276daed7089ca0e1`) sur la branche secondaire NS1.

- `OpenLocationResolver` (0), `OpenRegisteredLocationResolver` (1) et `OpenAddOnContentLocationResolver` (3) : **3 NULL → IMPL-SRC**, avec retour des vrais objets IPC déjà présents dans `ncm.cpp`.
- `RefreshLocationResolver` (2) : **NULL → NOOP documenté**. Les resolvers Encore sont actuellement sans cache manager de redirections ; la commande consomme le `StorageId` et réussit sans inventer une mutation de chemin.
- ABI recroisée avec libnx et Atmosphère : cmd0 prend un `StorageId`, cmd1/cmd3 ouvrent un objet sans entrée, cmd2 prend un `StorageId`.
- Les sous-commandes de résolution/redirect restent ouvertes : ce lot rend la hiérarchie IPC utilisable mais ne prétend pas résoudre les chemins Horizon.

**Compteur historique : 1 443 IMPL-SRC / 110 PARTIEL / 149 STUB / 110 NOOP / 2 156 NULL / 84 D / 191 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 6 HORS-VERSION / 0 ABSENT / 285 ABI-DIFF / 12 AMBIGU / 1 E = 4 853.**

**Pool historique restant à examiner = 2 713** : 2 156 NULL + 149 STUB + 110 PARTIEL + 285 ABI-DIFF + 12 AMBIGU + 1 SVC.

## Lot NCM racine — vérification caches et lifecycle — 23/11/2026

**Vendor `67db89c1195d79ee731fc783088ec38083804050`** (arbre `a477fa09a667ba6144e31aaf59921386067ce4ee`) sur la branche secondaire NS1.

- `VerifyContentStorage` (2) et `VerifyContentMetaDatabase` (3) : **2 NULL → IMPL-SRC**. Le premier exige `RegisteredCache + PlaceholderCache`, le second le `RegisteredCache` réellement utilisé par `IContentMetaDatabase`.
- `CloseContentStorageForcibly` (6), `CloseContentMetaDatabaseForcibly` (7), `Activate/InactivateContentStorage` (9/10) et `Activate/InactivateContentMetaDatabase` (11/12) : **6 NULL → NOOP documentés**. Encore conserve ces caches sous `FileSystemController` pendant la session et ne possède pas de daemon NCM séparé à activer/inactiver.
- Les six commandes lifecycle valident tout de même le `StorageId` par présence du backend correspondant et échouent sur un stockage inexistant ; aucun succès aveugle.
- ABI vérifiée avec libnx : les huit commandes prennent un `NcmStorageId` brut.

**Compteur historique : 1 445 IMPL-SRC / 110 PARTIEL / 149 STUB / 116 NOOP / 2 148 NULL / 84 D / 191 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 6 HORS-VERSION / 0 ABSENT / 285 ABI-DIFF / 12 AMBIGU / 1 E = 4 853.**

**Pool historique restant à examiner = 2 705** : 2 148 NULL + 149 STUB + 110 PARTIEL + 285 ABI-DIFF + 12 AMBIGU + 1 SVC.

## Lot NCM racine — création sur backends préprovisionnés — 23/11/2026

**Vendor `400974b505e47e85952469aeceb959bbbee41948`** (arbre `6fda5c117836e91b18c76796121f9e58b4fe17a0`) sur la branche secondaire NS1.

- `CreateContentStorage` (0) et `CreateContentMetaDatabase` (1) : **2 NULL → NOOP documentés avec post-condition vérifiée**.
- Encore préprovisionne respectivement `RegisteredCache + PlaceholderCache` et `RegisteredCache` avant le démarrage NCM. Les commandes réussissent seulement lorsque ces backends existent ; un `StorageId` sans backing renvoie une erreur.
- Aucun chemin hôte ni stockage fictif n'est créé. Le comportement couvre le cas où la création Horizon demande simplement d'assurer l'existence d'un backend déjà provisionné.
- `CleanupContentMetaDatabase` reste NULL faute de primitive locale équivalente.

**Compteur historique : 1 445 IMPL-SRC / 110 PARTIEL / 149 STUB / 118 NOOP / 2 146 NULL / 84 D / 191 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 6 HORS-VERSION / 0 ABSENT / 285 ABI-DIFF / 12 AMBIGU / 1 E = 4 853.**

**Pool historique restant à examiner = 2 703** : 2 146 NULL + 149 STUB + 110 PARTIEL + 285 ABI-DIFF + 12 AMBIGU + 1 SVC.

## Lot SSL — getters d'état de connexion — 23/11/2026

**Vendor `6b477c04581797bc3a5677c6c849b297f3a4587f`** (arbre `9f16c143a040213aa2429acbceaf5b2250ce5b30`) au-dessus du vendor NCM `400974b505e47e85952469aeceb959bbbee41948`.

- **4 NULL → IMPL-SRC** dans `ISslConnection` : `GetSocketDescriptor` (4), `GetHostName` (5), `GetVerifyOption` (6), `GetIoMode` (7).
- Le socket conserve désormais le fd invité d'origine et sa référence vivante après duplication ; le hostname validé est mémorisé après `SetHostName`; `SetIoMode` mémorise le mode uniquement après succès du backend ; `GetVerifyOption` retourne l'état effectivement appliqué par le setter.
- Le destructeur ferme correctement le fd dupliqué conservé ; un échec de récupération du socket dupliqué ferme immédiatement ce fd.
- Le fichier actif est `encore-active/eden-core/src/core/hle/service/ssl/ssl.cpp`, avec test R23 #120 mis à jour. Ce lot ne prétend pas couvrir DTLS/SRTP/cipher info/timeouts et ne constitue pas une validation réseau PS5.

**Compteur historique : 1 449 IMPL-SRC / 110 PARTIEL / 149 STUB / 118 NOOP / 2 142 NULL / 84 D / 191 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 6 HORS-VERSION / 0 ABSENT / 285 ABI-DIFF / 12 AMBIGU / 1 E = 4 853.**

**Pool historique restant à examiner = 2 699** : 2 142 NULL + 149 STUB + 110 PARTIEL + 285 ABI-DIFF + 12 AMBIGU + 1 SVC.

## Recheck SSL R23 — faux NULL déjà raccordés — 23/11/2026

- `Peek` (13) : **NULL → IMPL-SRC** ; le chemin actif appelle `SSL_peek`, borne la taille `int`, remet la taille de sortie à zéro avant l'appel et propage le résultat backend. Le test R23 #120 couvre lecture courte/erreur/zero-length.
- `SetRenegotiationMode` (20) et `GetRenegotiationMode` (21) : **2 NULL → IMPL-SRC** ; le backend OpenSSL applique les options de renégociation et lit le support de renégociation sécurisée.
- `Poll`, `GetVerifyCertError`, `GetNeededServerCertBufferSize`, `GetSessionCacheMode` et `FlushSessionCache` restent des stubs malgré leurs handlers : aucun gain de compteur n'est revendiqué pour eux.

**Compteur historique : 1 452 IMPL-SRC / 110 PARTIEL / 149 STUB / 118 NOOP / 2 139 NULL / 84 D / 191 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 6 HORS-VERSION / 0 ABSENT / 285 ABI-DIFF / 12 AMBIGU / 1 E = 4 853.**

**Pool historique restant à examiner = 2 696** : 2 139 NULL + 149 STUB + 110 PARTIEL + 285 ABI-DIFF + 12 AMBIGU + 1 SVC.

## Lot runtime hors miroir — ButtonConfig 189–200 — 23/11/2026

**Vendor `5fdfa239cb6e148abac1ef2d6393b8950132bc2b`** (arbre `dbfc5e1a0e5ff72834206bb4cbe066ce1ab85246`).

- Les **12 commandes `set:sys` 189–200** sont maintenant implémentées sur le stockage persistant Eden : Full/Embedded/Left/Right en 0x5A8, RegisteredEmbedded/Registered en 0x5C8, avec compteurs et bornage IPC.
- Libnx confirme les tailles et modes MapAlias. Aucun format propriétaire n'est reconstruit : les payloads sont conservés octet pour octet.
- **Ces 12 commandes sont absentes du miroir historique 4 853**, donc elles ne réduisent pas artificiellement le compteur historique. Elles augmentent la couverture runtime réelle et renforcent la preuve que le miroir n'est pas exhaustif des versions récentes de SwitchBrew.
- Le compteur historique reste **1 452 IMPL-SRC / 2 139 NULL**, pool **2 696**, tant qu'une réconciliation formelle du dénominateur n'est pas faite.


## Lot `set:sys` Backlight legacy 0x28 — 23/11/2026

**Vendor `9a5401c93d9c87bc0fcb3f955f35bd54744046a4`** (arbre `e4da559826dccca47deb8d35a4fdfb0882404733`).

- `GetBacklightSettings` (9) et `SetBacklightSettings` (10) : **2 NULL → IMPL-SRC**.
- Libnx montre que le layout legacy fait **0x28** et que `BacklightSettingsEx` fait **0x2C** en insérant uniquement `current_brightness_for_vr_mode` à l'offset 0x8.
- Le getter legacy copie 0x00–0x07 puis 0x0C–0x2B du bloc persistant Ex. Le setter fait l'inverse et **préserve** les 4 octets Ex-only à 0x08–0x0B ; aucun champ n'est synthétisé.
- Cela complète le round-trip de settings, sans prétendre contrôler physiquement la luminosité de la PS5.

**Compteur historique : 1 454 IMPL-SRC / 110 PARTIEL / 149 STUB / 118 NOOP / 2 137 NULL / 84 D / 191 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 6 HORS-VERSION / 0 ABSENT / 285 ABI-DIFF / 12 AMBIGU / 1 E = 4 853.**

**Pool historique restant à examiner = 2 694** : 2 137 NULL + 149 STUB + 110 PARTIEL + 285 ABI-DIFF + 12 AMBIGU + 1 SVC.

## Lot `set:sys` Terra compatibility flag — 23/11/2026

**Vendor `bb450eb2e61d2e28856c5beb9fcc6fa1afc8adab`** (arbre `8b5f9570428f539fb4a414659eb2afefc5c9fe70`).

- `GetT` (181) et `SetT` (182) : **2 NULL → IMPL-SRC**.
- Libnx documente ces commandes comme wrappers de `PlatformRegion` : Terra si région 2 ; setter équivalent à `1 + (flag & 1)`.
- Eden possède déjà `PrivateSettings::platform_region` avec `Global=1` et `Terra=2`. Les deux commandes réutilisent donc le même état persistant que 183/184, avec normalisation vers Global si la valeur stockée est invalide.

**Compteur historique : 1 456 IMPL-SRC / 110 PARTIEL / 149 STUB / 118 NOOP / 2 135 NULL / 84 D / 191 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 6 HORS-VERSION / 0 ABSENT / 285 ABI-DIFF / 12 AMBIGU / 1 E = 4 853.**

**Pool historique restant à examiner = 2 692** : 2 135 NULL + 149 STUB + 110 PARTIEL + 285 ABI-DIFF + 12 AMBIGU + 1 SVC.

## Lot FSP — accessibilité SD — 23/11/2026

**Vendor `be00691dcb6abbf888cc00a4a5dcbf10b377fac5`** (arbre `982c71474dbabaa0b4829af66c5c6c59847004ec`).

- `SetSdCardAccessibility` (630) : **NULL → IMPL-SRC**. LibHac/SwitchForge confirme que cette commande mémorise une politique booléenne dans le service ; elle ne monte ni ne démonte physiquement le média.
- `IsSdCardAccessible` (631), déjà actif, renvoie désormais **politique autorisée ET SDMC réellement ouvrable**. L'état est initialisé à accessible, comme le comportement normal du proxy lorsqu'aucune restriction n'a été appliquée.
- Aucun formatage ou mutation du contenu SD n'est effectué.

**Compteur historique : 1 457 IMPL-SRC / 110 PARTIEL / 149 STUB / 118 NOOP / 2 134 NULL / 84 D / 191 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 6 HORS-VERSION / 0 ABSENT / 285 ABI-DIFF / 12 AMBIGU / 1 E = 4 853.**

**Pool historique restant à examiner = 2 691** : 2 134 NULL + 149 STUB + 110 PARTIEL + 285 ABI-DIFF + 12 AMBIGU + 1 SVC.

## Lot PCTL — stockage PIN et événement de changement — 23/11/2026

**Vendor `6f487f76b88c2ca12f81c189fddcc2a8f083c74c`** (arbre `34ca4655b3822ed3ba9d47622d4399bae9f3ff3b`) sur le runtime PCTL réellement compilé.

- `SetPinCode` (1203), `GetPinCodeChangedEvent` (1207) et `GetPinCode` (1208) : **3 NULL → IMPL-SRC**.
- La référence SDK-like `nn::pctl::detail::IParentalControlService` confirme : 1203 reçoit un buffer Pointer entrant ; 1207 retourne un handle natif ; 1208 retourne la longueur et un buffer Pointer sortant.
- Eden possédait déjà `pin_code[8]` et `GetPinCodeLength` (1206). Le setter alimente maintenant ce même état, signale un événement `pin_code_changed_event` dédié, et le getter renvoie les octets réellement stockés.
- Le buffer entrant est borné à 8 octets afin d'éviter toute corruption ; les appels SDK normaux restent dans cette capacité. Aucun code d'erreur PCTL non documenté n'est inventé.
- Aucun jumelage Nintendo, master key ou persistance disque du PIN n'est revendiqué.

**Compteur historique : 1 460 IMPL-SRC / 110 PARTIEL / 149 STUB / 118 NOOP / 2 131 NULL / 84 D / 191 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 6 HORS-VERSION / 0 ABSENT / 285 ABI-DIFF / 12 AMBIGU / 1 E = 4 853.**

**Pool historique restant à examiner = 2 688** : 2 131 NULL + 149 STUB + 110 PARTIEL + 285 ABI-DIFF + 12 AMBIGU + 1 SVC.

## Lot PCTL — unlock / restricted-settings / unlinked event — 23/11/2026

**Vendor `6a4ef643a90629e005844cd7be6ea7d8f3cb3c6e`** (arbre `f24749580d8cf74dfacee33dd11ebce7836c8629`).

- **6 NULL → IMPL-SRC** : `RevertRestrictionTemporaryUnlocked` (1007), `EnterRestrictedSystemSettings` (1008), `LeaveRestrictedSystemSettings` (1009), `RevertRestrictedSystemSettingsEntered` (1011), `UnlockRestrictionTemporarily` (1201) et `ClearUnlinkedEvent` (1474).
- 1201 suit l'ABI SDK (buffer PIN Pointer), compare le PIN au même état que 1203/1206/1208 et renvoie **PCTL 221** en cas de PIN invalide, code déjà utilisé par l'applet système Eden et les upstreams.
- 1007 pilote l'état `temporary_unlocked` déjà consommé par les vérifications de permission ; 1008/1009/1011 pilotent un état de session désormais lu par 1010 `IsRestrictedSystemSettingsEntered`.
- 1474 appelle réellement `unlinked_event.Clear()`, symétrique de 1473 `GetUnlinkedEvent`.
- Les commandes 1601–1603 restent ouvertes : des preuves console indiquent qu'elles peuvent renvoyer une erreur PCTL sur console normale ; aucune émulation arbitraire n'est ajoutée.

**Compteur historique : 1 466 IMPL-SRC / 110 PARTIEL / 149 STUB / 118 NOOP / 2 125 NULL / 84 D / 191 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 6 HORS-VERSION / 0 ABSENT / 285 ABI-DIFF / 12 AMBIGU / 1 E = 4 853.**

**Pool historique restant à examiner = 2 682** : 2 125 NULL + 149 STUB + 110 PARTIEL + 285 ABI-DIFF + 12 AMBIGU + 1 SVC.

## Lot NCM — cleanup metadata / activation FS content — 23/11/2026

**Vendor `1a2a614892cde741adb10ba7dfc23dfee4d8ff06`** (arbre `e6e631075d5e4ffbd8895fcfc6741363ae4b2bf8`) sur la branche secondaire NS1.

- `CleanupContentMetaDatabase` (8) : **NULL → NOOP documenté**. `IContentMetaDatabase` lit directement le `RegisteredCache` vivant ; Encore n'a pas de base NCM séparée à compacter. La commande ne réussit que si le backend demandé existe.
- `ActivateFsContentStorage` (15, HOS 16+) : handler runtime ajouté hors miroir historique. Les IDs FS System/User/SD/System0 sont mappés vers les backends déjà provisionnés et l'appel réussit seulement si le `RegisteredCache` correspondant existe.
- Aucun répertoire hôte ni contenu n'est créé, aucun montage artificiel n'est simulé.
- **Impact miroir : +1 NOOP, -1 NULL**. Le handler cmd15 reste hors dénominateur 4 853.

**Compteur historique : 1 466 IMPL-SRC / 110 PARTIEL / 149 STUB / 119 NOOP / 2 124 NULL / 84 D / 191 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 6 HORS-VERSION / 0 ABSENT / 285 ABI-DIFF / 12 AMBIGU / 1 E = 4 853.**

**Pool historique restant à examiner = 2 681** : 2 124 NULL + 149 STUB + 110 PARTIEL + 285 ABI-DIFF + 12 AMBIGU + 1 SVC.

## Recheck NULL — commandes retirées avant HOS 23 — 23/11/2026

- **30 NULL → HORS-VERSION** sans modification runtime.
- **29 lignes** du miroir indiquaient déjà une fenêtre fermée entre HOS 1.x et 8.1.0 : anciennes commandes Account, HID debug, SPSM, AOC, NS, BT, CAPS, VI, ES, FSP et PSC.
- `NeedsToUpdateHeadphoneVolume` (set:sys 119) est corrigée de `3.0.0+` vers **3.0.0–14.1.2** : libnx documente explicitement sa suppression en 15.0.0. Sur la cible **HOS 23**, elle ne doit pas être exposée.
- Cette requalification suit la même règle que les six anciennes commandes Time déjà classées HORS-VERSION : aucune fonction disparue du firmware cible n'est remplacée par un faux succès.

**Compteur historique : 1 466 IMPL-SRC / 110 PARTIEL / 149 STUB / 119 NOOP / 2 094 NULL / 84 D / 191 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 36 HORS-VERSION / 0 ABSENT / 285 ABI-DIFF / 12 AMBIGU / 1 E = 4 853.**

**Pool historique restant à examiner = 2 651** : 2 094 NULL + 149 STUB + 110 PARTIEL + 285 ABI-DIFF + 12 AMBIGU + 1 SVC.

## Recheck ABI-DIFF — anciennes surfaces Time — 23/11/2026

- Les trois lignes `SetInternalOffset` (cmd201) exposées sur les anciennes surfaces Time sont limitées à **HOS 3.0.0–3.0.2** dans le miroir.
- **3 ABI-DIFF → HORS-VERSION** pour la cible HOS 23. Aucune adaptation de l'ABI moderne n'est nécessaire pour ces commandes retirées.

**Compteur historique : 1 466 IMPL-SRC / 110 PARTIEL / 149 STUB / 119 NOOP / 2 094 NULL / 84 D / 191 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 39 HORS-VERSION / 0 ABSENT / 282 ABI-DIFF / 12 AMBIGU / 1 E = 4 853.**

**Pool historique restant à examiner = 2 648** : 2 094 NULL + 149 STUB + 110 PARTIEL + 282 ABI-DIFF + 12 AMBIGU + 1 SVC.

## Lot PCTL + surface PDM HOS23 — 23/11/2026

**Vendor `70829977dbe1e534887c4baa2ddd6c9a1252acc5`** (arbre `7dc7ba8a5ecbc75cf37f2f54efeb0cdbd04f24f8`) sur la branche secondaire NS1.

- PCTL `SetCustomSafetyLevelSettings` (1036) : **NULL → IMPL-SRC** ; l'état `restriction_settings` réellement utilisé par le service est mis à jour.
- PCTL `GetFreeCommunicationApplicationList` (1044) : **NULL → IMPL-SRC** ; le service renvoie la liste locale réellement vide, cohérente avec le compteur déjà ramené à zéro.
- `pdm:qry::QueryRecentlyPlayedApplication` (14) et `GetRecentlyPlayedApplicationUpdateEvent` (15) : **2 NULL → HORS-VERSION** et suppression des deux entrées de la table runtime. Libnx documente leur retrait en **HOS 15.0.0** ; elles ne doivent pas être exposées sur HOS 23.
- Aucun historique de jeu fictif ni événement PDM synthétique n'est ajouté.

**Compteur historique : 1 468 IMPL-SRC / 110 PARTIEL / 149 STUB / 119 NOOP / 2 090 NULL / 84 D / 191 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 41 HORS-VERSION / 0 ABSENT / 282 ABI-DIFF / 12 AMBIGU / 1 E = 4 853.**

**Pool historique restant à examiner = 2 644** : 2 090 NULL + 149 STUB + 110 PARTIEL + 282 ABI-DIFF + 12 AMBIGU + 1 SVC.

## Lot `set:sys` AudioVolume — 23/11/2026

**Vendor `73fea5e303c074b8c8d16d096f4245f8cfa5c15c`** (arbre `e016ea5e3aa9d92d3477a258487745658420c425`) sur la branche secondaire NS1.

- `GetAudioVolume` (19) et `SetAudioVolume` (20) : **2 NULL → IMPL-SRC**.
- Libnx définit `SetSysAudioDevice` : Console=0, Headphone=1, Tv=2, et `SetSysAudioVolume` occupe 8 octets. Le format Eden contient exactement trois blocs persistants `audio_volume_type0/type1/type2`, chacun de 8 octets.
- Les cibles 0/1/2 sont mappées directement aux trois blocs ; toute autre valeur est rejetée. Le setter marque la sauvegarde.
- Aucun volume hôte PS5 n'est modifié : il s'agit du contrat de settings invité, pas du mixeur SDL/PS5.

**Compteur historique : 1 470 IMPL-SRC / 110 PARTIEL / 149 STUB / 119 NOOP / 2 088 NULL / 84 D / 191 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 41 HORS-VERSION / 0 ABSENT / 282 ABI-DIFF / 12 AMBIGU / 1 E = 4 853.**

**Pool historique restant à examiner = 2 642** : 2 088 NULL + 149 STUB + 110 PARTIEL + 282 ABI-DIFF + 12 AMBIGU + 1 SVC.

## Lot `set:sys` dirty flags Telemetry / Fatal — 23/11/2026

**Vendor `d833c0f790973b53be9abf24df8d328377557494`** (arbre `53e0136353a64f4cfaa86e24541d634764d8e318`) sur la branche secondaire NS1.

- `AcquireTelemetryDirtyFlagEventHandle` (82), `GetTelemetryDirtyFlags` (83), `AcquireFatalDirtyFlagEventHandle` (93) et `GetFatalDirtyFlags` (94) : **4 NULL → NOOP documentés**.
- Les deux Acquire retournent de vrais `KReadableEvent` détenus par un `ServiceContext`; ils ne sont jamais signalés car Encore ne possède aucun producteur Telemetry/Fatal.
- Les getters renvoient les deux masques 64 bits à zéro, cohérents avec l'absence de modification locale dans ces domaines. Aucun changement de settings n'est inventé pour provoquer un événement.
- ABI recroisée avec libnx : événements non auto-clear et deux `u64` de sortie pour chaque getter.

**Compteur historique : 1 470 IMPL-SRC / 110 PARTIEL / 149 STUB / 123 NOOP / 2 084 NULL / 84 D / 191 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 41 HORS-VERSION / 0 ABSENT / 282 ABI-DIFF / 12 AMBIGU / 1 E = 4 853.**

**Pool historique restant à examiner = 2 638** : 2 084 NULL + 149 STUB + 110 PARTIEL + 282 ABI-DIFF + 12 AMBIGU + 1 SVC.

## Recheck HOS23 — GetFirmwareVersionDigest retiré — 23/11/2026

**Vendor `c1b7768aa16f8a731de420783cd1e31ca2f58104`** (arbre `ae8748e568d9ad38d40e32ae95bb342a3a08daa6`).

- `set:sys::GetFirmwareVersionDigest` (cmd5) : **NULL → HORS-VERSION**.
- SwitchBrew courant borne cette commande S1 à **HOS 5.0.0–22.5.0**. La table runtime HOS23 n'expose donc plus cmd5.
- Aucun digest synthétique n'est dérivé de `version_hash` : sur la cible actuelle, ce contrat n'existe simplement plus.

**Compteur historique : 1 470 IMPL-SRC / 110 PARTIEL / 149 STUB / 123 NOOP / 2 083 NULL / 84 D / 191 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 42 HORS-VERSION / 0 ABSENT / 282 ABI-DIFF / 12 AMBIGU / 1 E = 4 853.**

**Pool historique restant à examiner = 2 637** : 2 083 NULL + 149 STUB + 110 PARTIEL + 282 ABI-DIFF + 12 AMBIGU + 1 SVC.

## Retrait HOS23 des services AHID historiques — 23/11/2026

**Vendor `d6b9b3ff6dc8ffc8898fcc286569e6fc77750277`** (arbre `dad2460f1464a2a98122be21d9389d579af75a94`) sur la branche secondaire NS1.

- `ahid:cd` et `ahid:hdr` ne sont plus enregistrés par le runtime actif. SwitchBrew borne les deux services S1 à **HOS 1.0.0–8.1.0**.
- **25 lignes → HORS-VERSION** : 10 étaient NULL et 15 INACCESSIBLE. Les sous-interfaces `ICtrlSession` / read / write disparaissent avec leur service parent.
- `ahid:cd::Write` est borné 3.0.0–8.1.0 et `ahid:hdr::SetDeviceFilter` 6.0.0–8.1.0 ; les autres lignes héritent de la fenêtre 1.0.0–8.1.0 du service.
- Source réellement compilée : `sources/eden/src/core/hle/service/hid/hid.cpp`, listée par `encore-active/eden-backports/src/core/CMakeLists.txt`. Aucun faux backend USB HID n'est ajouté.

**Compteur historique : 1 470 IMPL-SRC / 110 PARTIEL / 149 STUB / 123 NOOP / 2 073 NULL / 84 D / 176 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 67 HORS-VERSION / 0 ABSENT / 282 ABI-DIFF / 12 AMBIGU / 1 E = 4 853.**

**Pool historique restant à examiner = 2 627** : 2 073 NULL + 149 STUB + 110 PARTIEL + 282 ABI-DIFF + 12 AMBIGU + 1 SVC.

## Retrait HOS23 des anciennes surfaces Account `acc:u0` / `acc:u1` — 23/11/2026

**Vendor `b4297d22a50b391540e3b89f9c9a5afd1f9f1985`** (arbre `c192126108c3780633116955500f3f25c406c825`) sur la branche secondaire NS1.

- Les registrations `acc:u0` et `acc:u1` ont été retirées de l'owner actif `encore-active/eden-backports/src/core/hle/service/acc/acc.cpp`.
- SwitchBrew borne ces deux services S1 à **HOS 1.0.0–12.1.0** ; HOS 13+ expose `acc:e`, `acc:e:u1` et `acc:e:u2`.
- **82 lignes historiques → HORS-VERSION** : 22 IMPL-SRC, 46 NULL, 2 PARTIEL, 3 STUB, 6 ABI-DIFF et 3 AMBIGU. Les corps partagés peuvent rester utiles aux nouvelles surfaces Account, mais les anciennes routes `acc:u0/u1` ne sont plus des contrats HOS23.
- **Impact sur le pool actif : -60** entrées. Aucun comportement réseau Nintendo ni profil fictif n'est ajouté.

**Compteur historique : 1 448 IMPL-SRC / 108 PARTIEL / 146 STUB / 123 NOOP / 2 027 NULL / 84 D / 176 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 149 HORS-VERSION / 0 ABSENT / 276 ABI-DIFF / 9 AMBIGU / 1 E = 4 853.**

**Pool historique restant à examiner = 2 567** : 2 027 NULL + 146 STUB + 108 PARTIEL + 276 ABI-DIFF + 9 AMBIGU + 1 SVC.

## Lot Account — miniatures de sauvegarde persistantes — 23/11/2026

**Vendor `2990b313b00f739b7a8863e3b3d896aede75f712`** (arbre `a2c8c7999086be1afad86466c4f9a5c867671ff7`), incluant le runtime Account `3fec6fd63c962266a82026f67c5ff7960238e7ac` et la remise en cohérence des manifestes actifs FSP/PCTL.

- `StoreSaveDataThumbnail` (110) : **STUB → IMPL-SRC**. Les **0x24000 octets** exigés sont maintenant persistés par `Uid + ApplicationId` dans le system-save Account local, après validation de l'utilisateur et de l'ApplicationId.
- `ClearSaveDataThumbnail` (111) et `GetSaveDataThumbnailExistence` (113) : **2 NULL → IMPL-SRC**, sur le même état réellement persisté.
- `LoadSaveDataThumbnail` (112) : **NULL → PARTIEL**. Le fichier réel est relu avec taille et buffer bornés ; en absence de fichier, Encore renvoie actuellement succès + taille 0. Les dumps HOS 22.5/23.0.1 prouvent l'ABI `Uid(0x10)+ApplicationId(0x8)`, le `u32` de sortie et le buffer, mais pas le Result exact du cas absent.
- Ryujinx documente que le service Nintendo passe par `nn::fs::WriteSaveDataThumbnailFile()` dans le system-save Account `0x8000000000000010`. Les upstreams Eden/Lichii classiques ne faisaient jusque-là qu'un succès sans stockage ; ce lot ne reprend pas ce faux succès.
- Les empreintes `eden-backports/manifest.json` sont synchronisées avec les owners actifs Account, FSP et PCTL. Le contrôle de provenance précédent `541be9be` avait d'abord échoué sur `acc.cpp`, puis sur `fsp_srv.cpp`; le présent couple doit être requalifié par CI.
- **Aucun build PS5 ni validation console** n'est revendiqué.

**Compteur historique : 1 451 IMPL-SRC / 109 PARTIEL / 145 STUB / 123 NOOP / 2 024 NULL / 84 D / 176 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 149 HORS-VERSION / 0 ABSENT / 276 ABI-DIFF / 9 AMBIGU / 1 E = 4 853.**

**Pool historique restant à examiner = 2 564** : 2 024 NULL + 145 STUB + 109 PARTIEL + 276 ABI-DIFF + 9 AMBIGU + 1 SVC.

## Lot Friend — contrats offline explicites — 23/11/2026

**Vendor `f5ae5e2073add91752d510195a6f2d9f454b92de`** (arbre `c4eb1151a2007ff263b547be5d09fce431064c97`) sur la source active `sources/eden/src/core/hle/service/friend/friend.cpp`.

- `GetFriendListIds` (10100) et `GetFriendCandidateList` (20300) : **2 NULL → IMPL-SRC**. Encore n'a aucun backend social Nintendo ; les ensembles réels locaux sont donc vides et les commandes renvoient `count=0` sans toucher aux buffers de sortie.
- `DeclareOpenOnlinePlaySession` (10600), `SyncFriendList` (20103), `SyncBlockedUserList` (20401) et `SyncUserSetting` (20801) : **4 NULL → NOOP documentés**. Ce sont des publications/synchronisations distantes sans état distant à muter ; elles sont cohérentes avec `DeclareCloseOnlinePlaySession`, `RequestSyncFriendList` et les listes vides déjà actives.
- ABI recroisée avec le dump HOS **23.0.1** : 10100 sort un `u32` + buffer type 0xA ; 20300 sort un `u32` + buffer type 0x6 ; les quatre autres n'ont aucune sortie de données. Aucun ami, profil ou présence fictive n'est synthétisé.
- Le palier précédent moteur `fe5f4f9e` → vendor `2990b313` est **X8D24 + Verify pinned vendor vert**. Le présent couple doit être qualifié séparément.
- **Aucun build PS5 ni validation console** n'est revendiqué.

**Compteur historique : 1 453 IMPL-SRC / 109 PARTIEL / 145 STUB / 127 NOOP / 2 018 NULL / 84 D / 176 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 149 HORS-VERSION / 0 ABSENT / 276 ABI-DIFF / 9 AMBIGU / 1 E = 4 853.**

**Pool historique restant à examiner = 2 558** : 2 018 NULL + 145 STUB + 109 PARTIEL + 276 ABI-DIFF + 9 AMBIGU + 1 SVC.

## Lot LR — RegisteredLocationResolver stateful — 23/11/2026

**Vendor `0e261f9ce092ade8243443175ffc3b977772616c`** (arbre `8dd9abffeab8f3e2c75ec39806570881c7d30b12`) dans la source active `sources/eden/src/core/hle/service/ncm/ncm.cpp`.

- Les **10 commandes** de `IRegisteredLocationResolver` (0–9) disposent maintenant d'un runtime stateful : chemins Program/HTML enregistrés, redirections prioritaires, `owner_id` HOS9+, unregister et refresh sélectif.
- Les chemins sont des `ContentPath` fixes de **0x301 octets** avec terminaison NUL obligatoire. Les codes d'échec utilisent le module LR Horizon : `ProgramNotFound` (8/2), `HtmlDocumentNotFound` (8/6) et `InvalidPath` (8/140).
- Le comportement suit Atmosphère : capacité enregistrée **0x20** sur HOS9+, remplacement par clé, clear+register si le registre est plein ; `Refresh()` conserve les fallbacks enregistrés mais efface les redirections ; `RefreshExcluding` conserve uniquement les entrées/redirections dont l'**owner-id** figure dans la liste d'exclusion.
- Le dump HOS **23.0.1** confirme les ABI : Resolve = u64 + buffer sortant fixe ; Register/Redirect = u64 ProgramId + u64 owner-id + buffer entrant 0x301 ; RefreshExcluding = tableau de ProgramId.
- Le miroir 4 853 fusionne `ResolveProgramPath` du resolver normal et du resolver enregistré en une seule ligne. Comme le resolver normal reste NULL, cette ligne passe **NULL → PARTIEL** au lieu d'être faussement déclarée complète. Les **9 autres lignes** de l'interface passent **NULL → IMPL-SRC**.
- Le palier précédent moteur `8e508017` → vendor `f5ae5e20` est **X8D24 + provenance vert**. Aucun build PS5 ni test console n'est revendiqué pour le présent lot.

**Compteur historique : 1 462 IMPL-SRC / 110 PARTIEL / 145 STUB / 127 NOOP / 2 008 NULL / 84 D / 176 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 149 HORS-VERSION / 0 ABSENT / 276 ABI-DIFF / 9 AMBIGU / 1 E = 4 853.**

**Pool historique restant à examiner = 2 549** : 2 008 NULL + 145 STUB + 110 PARTIEL + 276 ABI-DIFF + 9 AMBIGU + 1 SVC.

## Lot LR — gestion AddOnContent enregistrée — 23/11/2026

**Vendor `da41c660c92a9d8cfddeac29ec30e2148203aa27`** (arbre `bfcb971ca0c7c6fdff2fb5732b594c1259c14e2d`) dans `sources/eden/src/core/hle/service/ncm/ncm.cpp`.

- `RegisterAddOnContentStorage` (1), `UnregisterAllAddOnContentPath` (2), `RefreshApplicationAddOnContent` (3) et `UnregisterApplicationAddOnContent` (4) : **4 NULL → IMPL-SRC**.
- HOS23/Atmosphère associe `DataId → StorageId + ApplicationId owner`. La capacité est **8 entrées** sur HOS12+, une réinscription du même DataId remplace son stockage/owner, et un neuvième DataId renvoie LR `TooManyRegisteredPaths` (module 8, description 90).
- `RefreshApplicationAddOnContent` conserve uniquement les entrées dont l'owner figure dans le tableau d'ApplicationId ; `UnregisterApplicationAddOnContent` retire toutes les entrées de cet owner.
- `ResolveAddOnContentPath` (0) reste **NULL** : Atmosphère résout ensuite via ContentMetaDatabase + ContentStorage::GetPath, alors qu'Encore refuse encore de substituer un chemin hôte PS5 au `ContentPath` Horizon. Aucun faux chemin n'est introduit.
- ABI HOS **23.0.1** : Register = 0x18 octets (`DataId, ApplicationId, StorageId` sérialisés CMIF), Refresh = tableau entrant, Unregister = u64.
- X8D24 du palier précédent `850ea68c → 0e261f9c` est vert ; sa provenance était encore en cours au moment du repointage. Aucun build PS5 ni résultat console revendiqué.

**Compteur historique : 1 466 IMPL-SRC / 110 PARTIEL / 145 STUB / 127 NOOP / 2 004 NULL / 84 D / 176 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 149 HORS-VERSION / 0 ABSENT / 276 ABI-DIFF / 9 AMBIGU / 1 E = 4 853.**

**Pool historique restant à examiner = 2 545** : 2 004 NULL + 145 STUB + 110 PARTIEL + 276 ABI-DIFF + 9 AMBIGU + 1 SVC.

## Lot LR — redirections du LocationResolver normal — 23/11/2026

**Vendor `9b1c483eea8e013f1907ede3c235fe7a8216a6b6`** (arbre `bfd2db62ed954aefa1c6b50ee7ea4e48db7f6f08`) dans `sources/eden/src/core/hle/service/ncm/ncm.cpp`.

- **14 NULL → IMPL-SRC** : Redirect Program/Control/HTML/Legal, Refresh, RedirectApplicationProgram, ClearApplicationRedirection, quatre Erase, et les trois opérations debug de redirection/erase.
- **4 NULL → PARTIEL** : `ResolveApplicationControlPath`, `ResolveApplicationHtmlDocumentPath`, `ResolveApplicationLegalInformationPath` et `ResolveProgramPathForDebug`. Ils résolvent réellement les redirections invitées, mais le fallback vers le contenu installé n'est pas encore modélisé.
- `ResolveProgramPath` était déjà PARTIEL dans le miroir fusionné à cause du resolver enregistré ; le resolver normal couvre désormais ses redirections mais ne justifie pas un passage à IMPL-SRC.
- `ResolveDataPath` (4) reste **NULL**. Aucun chemin hôte PS5 n'est substitué à un `ContentPath` Horizon.
- Les chemins sont des buffers fixes 0x301 avec NUL obligatoire ; owner-id et opérations Clear/Erase suivent le modèle HOS9+/Atmosphère. Les erreurs LR restent explicites.
- Le HEAD précédent moteur `1d470f4f` → vendor/gitlink `da41c660` est **X8D24 + Verify pinned vendor vert**. Le présent couple doit être qualifié séparément ; aucun build PS5 n'est revendiqué.

**Compteur historique : 1 480 IMPL-SRC / 114 PARTIEL / 145 STUB / 127 NOOP / 1 986 NULL / 84 D / 176 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 149 HORS-VERSION / 0 ABSENT / 276 ABI-DIFF / 9 AMBIGU / 1 E = 4 853.**

**Pool historique restant à examiner = 2 531** : 1 986 NULL + 145 STUB + 114 PARTIEL + 276 ABI-DIFF + 9 AMBIGU + 1 SVC.

## Lot PCTL — organisation de classification par défaut — 23/11/2026

**Vendor `909c764d244ac0cd80ec2930085dbf672504ff84`** (arbre `d95cd18c5a0156428f8e09be246a4bcca13b3cdc`) sur l'owner PCTL actif et son manifeste d'intégrité.

- `GetDefaultRatingOrganization` (1037) et `SetDefaultRatingOrganization` (1038) : **2 NULL → IMPL-SRC**.
- L'ABI HOS23 est un entier brut 32 bits dans les deux sens. Encore conserve désormais la valeur dans l'état de session PCTL et le getter renvoie exactement la dernière valeur appliquée.
- Aucun mapping arbitraire vers ESRB/CERO/PEGI n'est inventé : la valeur reste opaque comme dans l'ABI.
- Le manifeste `eden-backports/manifest.json` est mis à jour dans le même commit vendor pour `parental_control_service.{cpp,h}`.
- Le palier précédent moteur `e899a218` → vendor/gitlink `9b1c483e` est **X8D24 + Verify pinned vendor vert**. Aucun build PS5 ni validation console revendiqué.

**Compteur historique : 1 482 IMPL-SRC / 114 PARTIEL / 145 STUB / 127 NOOP / 1 984 NULL / 84 D / 176 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 149 HORS-VERSION / 0 ABSENT / 276 ABI-DIFF / 9 AMBIGU / 1 E = 4 853.**

**Pool historique restant à examiner = 2 529** : 1 984 NULL + 145 STUB + 114 PARTIEL + 276 ABI-DIFF + 9 AMBIGU + 1 SVC.

## Lot PCTL — liste FreeCommunication stateful — 23/11/2026

**Vendor `0baa3af3f57d883be26587f11ab7bc586e4f79d5`** (arbre `6ea443768cb417cace310e087f52b4250d14f3a2`) sur le backport PCTL actif, manifeste synchronisé dans le même commit.

- **4 NULL → IMPL-SRC** : `AddToFreeCommunicationApplicationList` (1042), `UpdateFreeCommunicationApplicationList` (1045), `DeleteFromFreeCommunicationApplicationListForDebug` (1901), `ClearFreeCommunicationApplicationListForDebug` (1902).
- `GetFreeCommunicationApplicationListCount` (1039) passe **NOOP → IMPL-SRC** ; `GetFreeCommunicationApplicationList` (1044) reste IMPL-SRC mais renvoie désormais le vrai état local, avec offset et capacité du buffer.
- **Runtime récent hors miroir** : 1049 Reset et 1050 Add sont raccordés au même état sans gonfler le dénominateur historique.
- Une entrée est conservée **octet pour octet sur 0x10** : ApplicationId dans les 8 premiers octets, drapeau de restriction à l'octet 8 et sept octets réservés. Add est idempotent par ApplicationId ; Update remplace/ajoute l'entrée correspondante ; les commandes debug suppriment ou vident la même liste.
- L'ABI est recroisée avec le dump HOS 23.0.1 et le SDK-like : 1042/1050 prennent un u64, 1044 prend un offset u32 et un buffer sortant type 6, 1045 un buffer entrant type 5, 1901 un u64, 1902 aucune donnée.
- Le palier précédent moteur `ec310dfd` → vendor/gitlink `909c764d` est **X8D24 + Verify pinned vendor vert**. Aucun build PS5 ni validation console n'est revendiqué.

**Compteur historique : 1 487 IMPL-SRC / 114 PARTIEL / 145 STUB / 126 NOOP / 1 980 NULL / 84 D / 176 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 149 HORS-VERSION / 0 ABSENT / 276 ABI-DIFF / 9 AMBIGU / 1 E = 4 853.**

**Pool historique restant à examiner = 2 525** : 1 980 NULL + 145 STUB + 114 PARTIEL + 276 ABI-DIFF + 9 AMBIGU + 1 SVC.

## Recheck Friend — surfaces SNS retirées avant HOS23 — 23/11/2026

- **5 NULL → HORS-VERSION** : `GetSnsAccountLinkage` (20302), `GetSnsAccountProfile` (20303), `GetSnsAccountFriendList` (20304), `GetSnsAccountLinkPageUrl` (30300) et `UnlinkSnsAccount` (30301).
- La table active `IFriendService` documente explicitement ces cinq commandes sur **HOS 5.0.0–19.0.1**. La cible NS1 Encore est HOS23 : elles ne doivent pas être complétées par un faux backend SNS.
- Aucun runtime n'est modifié par ce lot documentaire ; il retire seulement des obligations obsolètes du pool actif.

**Compteur historique : 1 487 IMPL-SRC / 114 PARTIEL / 145 STUB / 126 NOOP / 1 975 NULL / 84 D / 176 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 154 HORS-VERSION / 0 ABSENT / 276 ABI-DIFF / 9 AMBIGU / 1 E = 4 853.**

**Pool historique restant à examiner = 2 520** : 1 975 NULL + 145 STUB + 114 PARTIEL + 276 ABI-DIFF + 9 AMBIGU + 1 SVC.

## Lot APM — politique guest CPU overclock explicite — 23/11/2026

**Vendor `cff675360f1985a856a91f587565c79b79567818`** (arbre `1ca6e84c217e6a85bf9a686e378f05192b44c68c`) dans le propriétaire réellement compilé `sources/eden/src/core/hle/service/apm/apm_interface.cpp` ; le CMake actif liste ce chemin et aucun fichier de remplacement APM n'existe dans `eden-backports`.

- `apm::IsCpuOverclockEnabled` (6), sa surface `apm:am` (6) et `ISession::SetCpuOverclockEnabled` (2) : **3 STUB → NOOP documentés**.
- Encore ne possède pas de domaine de fréquence CPU invité à muter sur PS5. Le setter accepte donc explicitement la requête sans modifier les clocks hôtes ; le getter renvoie `false`, cohérent avec cette politique.
- Le code n'émet plus `(STUBBED)` pour ces chemins. Aucun overclock physique PS5, gain FPS ou validation gameplay n'est revendiqué.
- Le palier précédent moteur `ec310dfd` → vendor `909c764d` est vert X8D24 + provenance ; le lot FreeCommunication `3e1385fe` a X8D24 vert, sa provenance était encore en cours au dernier relevé.

**Compteur historique : 1 487 IMPL-SRC / 114 PARTIEL / 142 STUB / 129 NOOP / 1 975 NULL / 84 D / 176 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 154 HORS-VERSION / 0 ABSENT / 276 ABI-DIFF / 9 AMBIGU / 1 E = 4 853.**

**Pool historique restant à examiner = 2 517** : 1 975 NULL + 142 STUB + 114 PARTIEL + 276 ABI-DIFF + 9 AMBIGU + 1 SVC.

## Lot NIFM — politiques locales sans daemon séparé — 23/11/2026

**Vendor `f918ebdbae5c375ab2eb5887031f26d14bec5976`** (arbre `c52752f61475b9ac2e2e4e7ff2374106b989ced0`) sur le propriétaire actif `encore-active/eden-backports/src/core/hle/service/nifm/nifm.cpp`, avec manifeste d'intégrité mis à jour dans le même commit.

- `GetSsidListVersion` (25), `ConfirmSystemAvailability` (33) et `SetBackgroundRequestEnabled` (34) : **3 STUB → NOOP documentés**.
- Encore ne conserve pas de liste SSID Horizon persistante : la version locale est explicitement 0. La disponibilité système est acquise lorsque l'interface NIFM locale est créée. Les requêtes réseau sont évaluées par les chemins Encore existants, sans daemon NIFM autonome à mettre en arrière-plan.
- `SetBackgroundRequestEnabled` consomme désormais réellement son booléen ABI et documente l'absence de scheduler séparé ; les logs `(STUBBED)` et TODO associés à ces trois commandes sont retirés.
- Les setters de requirement/profil restent ouverts tant que leur effet contractuel n'est pas raccordé ; aucune connectivité fictive n'est ajoutée.
- Le lot FreeCommunication moteur `3e1385fe` est désormais **X8D24 + provenance vert**. Le lot APM `1a3d1a84` a X8D24 vert ; sa provenance était encore en cours au dernier relevé.

**Compteur historique : 1 487 IMPL-SRC / 114 PARTIEL / 139 STUB / 132 NOOP / 1 975 NULL / 84 D / 176 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 154 HORS-VERSION / 0 ABSENT / 276 ABI-DIFF / 9 AMBIGU / 1 E = 4 853.**

**Pool historique restant à examiner = 2 514** : 1 975 NULL + 139 STUB + 114 PARTIEL + 276 ABI-DIFF + 9 AMBIGU + 1 SVC.

## Clôture du dernier SVC ouvert — 0x5B hors HOS23 — 23/11/2026

- `svcMapDeviceAddressSpace` (**0x5B**) passe **E → HORS-VERSION**.
- libnx documente explicitement ce syscall sur **HOS 1.0.0–12.1.0**. Sur les kernels modernes, Atmosphère/libmesosphere expose `0x59 MapDeviceAddressSpaceByForce`, `0x5A MapDeviceAddressSpaceAligned`, puis `0x5C UnmapDeviceAddressSpace` ; `0x5B` n'est plus une obligation HOS23.
- Eden possède déjà les chemins DAS modernes ; ajouter artificiellement 0x5B à son générateur aurait réintroduit une ABI legacy sans utilité pour la cible firmware.
- **E = 0** : il ne reste plus de SVC non classé dans ce registre.

**Compteur historique : 1 487 IMPL-SRC / 114 PARTIEL / 139 STUB / 132 NOOP / 1 975 NULL / 84 D / 176 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 155 HORS-VERSION / 0 ABSENT / 276 ABI-DIFF / 9 AMBIGU / 0 E = 4 853.**

**Pool historique restant à examiner = 2 513** : 1 975 NULL + 139 STUB + 114 PARTIEL + 276 ABI-DIFF + 9 AMBIGU.

## Lot CAPS — ShimLibraryVersion comme hint de compatibilité — 23/11/2026

**Vendor `7dfbe3cc1409cc4b5f3bba145ba7fd4134cf271f`** (arbre `4a8902e36b4c0d429b0bf1071fedc8f7f85c0109`).

- `caps:su::SetShimLibraryVersion` (32) et `caps:u::SetShimLibraryVersion` (32) : **2 STUB → NOOP documentés** dans le miroir.
- La même politique est appliquée à `caps:c` côté runtime, hors ligne distincte du miroir historique.
- Encore ne possède aucune branche Album/Screenshot dépendante de `ShimLibraryVersion`. Les commandes consomment déjà `library_version + aruid`; elles sont désormais explicitement traitées comme hints sans effet, plutôt que journalisées `(STUBBED)`.
- Aucun comportement de capture/album n'est revendiqué comme ajouté par ce lot.
- Le palier NIFM moteur `5cc56c00` → vendor `f918ebdb` est **X8D24 + Verify pinned vendor vert**.

**Compteur historique : 1 487 IMPL-SRC / 114 PARTIEL / 137 STUB / 134 NOOP / 1 975 NULL / 84 D / 176 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 155 HORS-VERSION / 0 ABSENT / 276 ABI-DIFF / 9 AMBIGU / 0 E = 4 853.**

**Pool historique restant à examiner = 2 511** : 1 975 NULL + 137 STUB + 114 PARTIEL + 276 ABI-DIFF + 9 AMBIGU.

## Lot NIFM — UUID de profil et suppression locale réelle — 23/11/2026

**Vendor `d1524eb55acb905c694a46cdb1333e32c0e4bdbf`** (arbre `b4b65ea5bffc675c996d4e8eae4b7dc530a6ea53`) sur le backport NIFM actif, manifeste d'intégrité synchronisé dans le même commit.

- `RemoveNetworkProfile` (10) : **STUB → IMPL-SRC**. `SetNetworkProfile` conserve désormais l'UUID 0x10 du profil pending et la commande 10 supprime réellement le profil local qui porte l'UUID demandé.
- `IRequest::SetNetworkProfileId` (9) : **STUB → PARTIEL**. Le bug ABI est corrigé : l'ancien code lisait un `u32` comme une longueur SSID et pouvait même répondre avec une valeur brute incorrecte ; il lit maintenant le `util::Uuid` 0x10 attendu et le mémorise dans la requête.
- Le statut 9 reste PARTIEL : l'UUID sélectionné n'est pas encore utilisé pour contraindre le routage/choix de l'interface lors de `Submit`. Aucun faux effet réseau n'est revendiqué.
- Le stockage de profil demeure local à la session Encore ; ce lot ne simule pas la base de profils système Nintendo.
- Le palier précédent moteur `6ce8ea0a` → vendor `7dfbe3cc` a X8D24 vert ; Verify pinned vendor était encore en cours au dernier relevé avant ce repointage.

**Compteur historique : 1 488 IMPL-SRC / 115 PARTIEL / 135 STUB / 134 NOOP / 1 975 NULL / 84 D / 176 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 155 HORS-VERSION / 0 ABSENT / 276 ABI-DIFF / 9 AMBIGU / 0 E = 4 853.**

**Pool historique restant à examiner = 2 510** : 1 975 NULL + 135 STUB + 115 PARTIEL + 276 ABI-DIFF + 9 AMBIGU.

## Lot `set:sys` — certificat Wi-Fi réel depuis PRODINFOF — 23/11/2026

**Vendor `822662c72f38324e1f6eb56eeb4e0f55f3bc45d0`** (arbre `7a9fe224d54a0c73e014a0e6f32f0229dfbb2dce`) sur la branche secondaire NS1.

- `GetWirelessCertificationFileSize` (55) et `GetWirelessCertificationFile` (56) : **2 NULL → IMPL-SRC**.
- SwitchBrew documente la source réelle dans **PRODINFOF / `Certifications/WirelessCertification.png`** ; Eden expose déjà la partition BIS `CalibrationFile` via `FileSystemController::OpenBISPartition`.
- Le getter de taille renvoie la taille réelle du fichier. Le getter de données utilise le buffer HIPC MapAlias de libnx, refuse un buffer trop petit et propage les erreurs BIS/fichier au lieu de fabriquer ou tronquer un certificat.
- Aucun certificat Nintendo n'est embarqué dans Encore et aucun fichier hôte arbitraire n'est substitué. Si l'utilisateur n'a pas le fichier PRODINFOF attendu, l'appel échoue explicitement.
- **`set:sys` atteint 0 NULL dans le miroir historique** après ce lot. Cela ne signifie pas que toutes ses commandes sont validées sur PS5 ni que les entrées hors miroir sont exhaustives.

**Compteur historique : 1 490 IMPL-SRC / 115 PARTIEL / 135 STUB / 134 NOOP / 1 973 NULL / 84 D / 176 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 155 HORS-VERSION / 0 ABSENT / 276 ABI-DIFF / 9 AMBIGU / 0 E = 4 853.**

**Pool historique restant à examiner = 2 508** : 1 973 NULL + 135 STUB + 115 PARTIEL + 276 ABI-DIFF + 9 AMBIGU.

## Lot `set:cal` — champs CAL0 non secrets — 23/11/2026

**Vendor `8b62686225121d894e40e7853083f636ac344c3c`** (arbre `b52c35e5b39352a3a86c44c45f0ee17892fbb066`) sur la branche secondaire NS1.

- **11 NULL → IMPL-SRC** : Bluetooth BD address (0), ConfigurationId1 (1), offsets/scales accéléromètre (2/3), offsets/scales gyroscope (4/5), WLAN MAC (6), nombre/liste de pays WLAN (7/8), SerialNumber (9), BatteryLot (12).
- Les valeurs viennent du vrai **CalibrationBinary / PRODINFO (CAL0)** via `OpenBISPartitionStorage(CalibrationBinary)`. Le lecteur vérifie le magic `CAL0`, la taille du fichier et les bornes avant toute copie.
- Les offsets suivent la table SwitchBrew : ConfigurationId1 0x40/0x1E, pays 0x80/0x88, WLAN MAC 0x210, BD 0x220, IMU 0x230–0x248, SerialNumber 0x250, BatteryLot 0x2CE0.
- La liste de pays est bornée à 0x80 entrées de 3 octets et à la taille du buffer HIPC Pointer fourni.
- **Aucune clé privée ni certificat** n'est exposé dans ce lot : les commandes 14–21 et 24–31 restent ouvertes jusqu'à validation séparée du contrat et des implications de sécurité.

**Compteur historique : 1 501 IMPL-SRC / 115 PARTIEL / 135 STUB / 134 NOOP / 1 962 NULL / 84 D / 176 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 155 HORS-VERSION / 0 ABSENT / 276 ABI-DIFF / 9 AMBIGU / 0 E = 4 853.**

**Pool historique restant à examiner = 2 497** : 1 962 NULL + 135 STUB + 115 PARTIEL + 276 ABI-DIFF + 9 AMBIGU.

## Lot `set:cal` — champs matériels CAL0 non secrets — 23/11/2026

**Vendor `5e77bf80aacb96088b281487525e5c73d7884d22`** (arbre `94d3a154d9b897032cc75da54b62fb33a870e89a`).

- **12 NULL → IMPL-SRC** : SpeakerParameter (22), LcdVendorId (23), UsbTypeCPowerSourceCircuitVersion (32), AnalogStick module/model/factory L (33–35), mêmes champs R (36–38), ConsoleSixAxisSensorModuleType (39), HorizontalOffset (40), BatteryVersion (41).
- Tous les getters lisent les octets réels du CAL0 validé ; les scalaires gardent leur alignement ABI natif (`u32` ou `u8`) et les structures opaques restent des tableaux de taille documentée.
- Offsets SwitchBrew utilisés : Speaker 0x2D00/0x5A, LCD 0x3D60/4, USB-C 0x4210/1, sticks 0x4270–0x42E8, six-axis 0x42F0/0x4300, batterie 0x4310.
- Aucune donnée secrète n'est ajoutée : clés/certificats restent hors de ce lot.

**Compteur historique : 1 513 IMPL-SRC / 115 PARTIEL / 135 STUB / 134 NOOP / 1 950 NULL / 84 D / 176 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 155 HORS-VERSION / 0 ABSENT / 276 ABI-DIFF / 9 AMBIGU / 0 E = 4 853.**

**Pool historique restant à examiner = 2 485** : 1 950 NULL + 135 STUB + 115 PARTIEL + 276 ABI-DIFF + 9 AMBIGU.

## Lot Friend — détail et relation offline ABI-corrects — 23/11/2026

**Vendor `a12fa5d6eec6350470374088e011bc93684e5763`** (arbre `855c15d239a1cd44547a3cda8de29cace9bee328`).

- `GetFriendDetailedInfo` (20102) : **NULL → IMPL-SRC** ; consomme `Uid + NetworkServiceAccountId` et renvoie le buffer Pointer fixe **0x800** entièrement initialisé à zéro lorsqu'aucun backend social Nintendo n'est connecté.
- `GetRelationship` (20501) : **NULL → IMPL-SRC** ; même entrée `Uid + NetworkServiceAccountId`, sortie brute **8 octets** avec la valeur `Relationship` par défaut.
- Les ABI sont recroisées avec SwIPC et le comportement offline avec Ryujinx, qui renvoie respectivement `FriendDetailedInfoImpl = default` et `Relationship = default`.
- Aucune relation, profil ou donnée réseau fictive n'est créée. Les mutations Friend restent ouvertes.

**Compteur historique : 1 515 IMPL-SRC / 115 PARTIEL / 135 STUB / 134 NOOP / 1 948 NULL / 84 D / 176 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 155 HORS-VERSION / 0 ABSENT / 276 ABI-DIFF / 9 AMBIGU / 0 E = 4 853.**

**Pool historique restant à examiner = 2 483** : 1 948 NULL + 135 STUB + 115 PARTIEL + 276 ABI-DIFF + 9 AMBIGU.

## Lot Friend — profils / clé NSAID / URL offline — 23/11/2026

**Vendor `b5bdec17c65914db77f8dac4a6eb4f740c8bb1f0`** (arbre `ee52c1bb868bc0e1bf28566bb7bae0c9a314c768`).

- `GetProfileList` (10500) : **NULL → IMPL-SRC** ; l'UID est consommé et le buffer MapAlias de profils demandé est entièrement initialisé à zéro, ce qui représente des profils invalides/absents sans backend social.
- `GetPlayHistoryRegistrationKeyWithNetworkServiceAccountId` (10701) : **NULL → IMPL-SRC** ; même contrat 0x40 que 10700 avec `bool + NetworkServiceAccountId`, sortie zéro en mode offline, conforme à SwIPC et Ryujinx.
- `GetProfileImageUrl` (11000) : **NULL → IMPL-SRC** ; `nn::friends::Url` fait **0xA0 octets**, l'entrée `Url + u32 ImageSize` est consommée et une URL vide ABI-correcte est renvoyée comme chez Ryujinx.
- Aucun appel réseau Nintendo, faux profil ou image factice n'est créé.

**Compteur historique : 1 518 IMPL-SRC / 115 PARTIEL / 135 STUB / 134 NOOP / 1 945 NULL / 84 D / 176 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 155 HORS-VERSION / 0 ABSENT / 276 ABI-DIFF / 9 AMBIGU / 0 E = 4 853.**

**Pool historique restant à examiner = 2 480** : 1 945 NULL + 135 STUB + 115 PARTIEL + 276 ABI-DIFF + 9 AMBIGU.

## Lot Friend — image / NNID / catalogue offline — 23/11/2026

**Vendor `e15f20df4dd3765b1c3df3ee3fcfc4ab3e155590`** (arbre `ef8803c118f902adac0ed1edd6aa914371317ad6`).

- `GetFriendProfileImage` (10110) : **NULL → IMPL-SRC** ; `Uid + NetworkServiceAccountId`, taille retournée 0 en l'absence d'image réseau, conformément à Ryujinx/SwIPC.
- `GetNintendoNetworkIdInfo` (20301) : **NULL → IMPL-SRC** ; consomme `u32 + Uid`, initialise le buffer Pointer fixe **0x38**, initialise la liste MapAlias et retourne count 0.
- `GetExternalApplicationCatalog` (21000) : **NULL → IMPL-SRC** ; consomme `LanguageCode` + identifiant catalogue 0x10, renvoie le buffer Pointer fixe **0x4B8** par défaut.
- Toutes les sorties sont explicitement initialisées ; aucune donnée Nintendo ou relation fictive n'est créée.

**Compteur historique : 1 521 IMPL-SRC / 115 PARTIEL / 135 STUB / 134 NOOP / 1 942 NULL / 84 D / 176 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 155 HORS-VERSION / 0 ABSENT / 276 ABI-DIFF / 9 AMBIGU / 0 E = 4 853.**

**Pool historique restant à examiner = 2 477** : 1 942 NULL + 135 STUB + 115 PARTIEL + 276 ABI-DIFF + 9 AMBIGU.

## Lot Friend — daemon suspend session / refresh offline — 23/11/2026

**Vendor `c1ae766d44a4871387232eefdeefd47a2dc00ff0`** (arbre `b20ef68916315f21a52e2b76b637f3bd9b04d717`).

- `CreateDaemonSuspendSessionService` (2) : **NULL → IMPL-SRC** ; retourne un véritable objet IPC `IDaemonSuspendSessionService`. L'interface n'expose pas de commandes supplémentaires dans Ryujinx et les runtimes recomp de référence.
- `UpdateFriendInfo` (10102) : **NULL → IMPL-SRC** ; consomme `Uid + pid placeholder`, initialise tout le tableau MapAlias de `FriendImpl` à l'état invalide/défaut en l'absence de backend social.
- Aucun daemon réseau ou profil distant fictif n'est créé.

**Compteur historique : 1 523 IMPL-SRC / 115 PARTIEL / 135 STUB / 134 NOOP / 1 940 NULL / 84 D / 176 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 155 HORS-VERSION / 0 ABSENT / 276 ABI-DIFF / 9 AMBIGU / 0 E = 4 853.**

**Pool historique restant à examiner = 2 475** : 1 940 NULL + 135 STUB + 115 PARTIEL + 276 ABI-DIFF + 9 AMBIGU.

## Lot Friend — quatre listes V1 ABI réconciliées — 23/11/2026

**Vendor `de2daec43b71d2f13e00b154f96e39770c4bd8c9`** (arbre `5b4f442159c08643686b78fc5dd82146c4141f2a`).

- `GetFriendRequestList` (20201), `GetBlockedUserList` (20400), `GetPlayHistoryList` (20700) et `GetReceivedFriendInvitationList` (22000) : **4 ABI-DIFF → IMPL-SRC**.
- SwIPC confirme les IDs et les formes V1 : paramètres `u32/Uid` selon la commande, sortie count `u32` + tableau MapAlias. Ryujinx renvoie count 0 pour chacune en mode sans données sociales.
- Encore consomme les entrées, initialise explicitement les buffers de sortie et renvoie count 0. Les anciens suffixes `V1` ne masquent donc plus un écart de contrat pour ces quatre IDs.
- Aucun historique, blocage, demande ou invitation fictifs ne sont produits.

**Compteur historique : 1 527 IMPL-SRC / 115 PARTIEL / 135 STUB / 134 NOOP / 1 940 NULL / 84 D / 176 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 155 HORS-VERSION / 0 ABSENT / 272 ABI-DIFF / 9 AMBIGU / 0 E = 4 853.**

**Pool historique restant à examiner = 2 471** : 1 940 NULL + 135 STUB + 115 PARTIEL + 272 ABI-DIFF + 9 AMBIGU.

## Requalification firmware — nd:app / nd:sys retirés depuis HOS 6 — 23/11/2026

SwitchBrew documente `nd:app` et `nd:sys` comme services introduits en **HOS 5.0.0** puis retirés en **HOS 6.0.0**. Les **39 commandes** encore classées NULL dans le miroir historique (2 `nd:app` + 37 `nd:sys`) passent donc **NULL → HORS-VERSION** pour la cible NS1/HOS 23. Aucun handler factice n'est ajouté et aucun gain gameplay n'est revendiqué.

**Compteur historique : 1 527 IMPL-SRC / 115 PARTIEL / 135 STUB / 134 NOOP / 1 901 NULL / 84 D / 176 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 194 HORS-VERSION / 0 ABSENT / 272 ABI-DIFF / 9 AMBIGU / 0 E = 4 853.**

**Pool historique restant à examiner = 2 432** : 1 901 NULL + 135 STUB + 115 PARTIEL + 272 ABI-DIFF + 9 AMBIGU.

## Lot Friend — effacements idempotents sur état offline — 23/11/2026

**Vendor `ab4f28f4d8f3b118c1d64d2f6744598860c388b6`** (arbre `ee3b73db16643181b54d520d98cf2cb0fbc60533`).

- `DropFriendNewlyFlags` (30100), `DropFriendNewlyFlag` (30110), `DeletePlayHistory` (30700), `ClearPlayLog` (30830) et `DeleteNetworkServiceAccountCache` (49900) : **5 NULL → NOOP documentés**.
- Les signatures sont recroisées avec l'interface IPC Ryujinx/Ryubing : `Uid` seul, sauf 30110 qui consomme aussi le `NetworkServiceAccountId`.
- Encore n'entretient actuellement ni liste Friend persistante avec flag `newly`, ni play-history/play-log Friend, ni cache de compte réseau à invalider. Les cinq opérations sont donc idempotentes et n'inventent aucun état distant.
- Les mutations observables `DeleteFriend`, `BlockUser`, demandes d'ami et changements de préférences restent ouvertes : aucun faux succès n'a été ajouté.

**Compteur historique : 1 527 IMPL-SRC / 115 PARTIEL / 135 STUB / 139 NOOP / 1 896 NULL / 84 D / 176 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 194 HORS-VERSION / 0 ABSENT / 272 ABI-DIFF / 9 AMBIGU / 0 E = 4 853.**

**Pool historique restant à examiner = 2 427** : 1 896 NULL + 135 STUB + 115 PARTIEL + 272 ABI-DIFF + 9 AMBIGU.

## Requalification firmware — omm et xcd:sys hors cible HOS 23 — 23/11/2026

- `omm` : SwitchBrew borne le service à **HOS 1.0.0–13.2.1** ; ses **28 commandes NULL** passent en **HORS-VERSION**.
- `xcd:sys` : SwitchBrew indique que le service a été **retiré en HOS 19.0.0+** ; ses **19 commandes NULL** passent en **HORS-VERSION**.
- Total : **47 NULL → HORS-VERSION**, sans ajout de handler ni faux succès runtime.

**Compteur historique : 1 527 IMPL-SRC / 115 PARTIEL / 135 STUB / 139 NOOP / 1 849 NULL / 84 D / 176 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 241 HORS-VERSION / 0 ABSENT / 272 ABI-DIFF / 9 AMBIGU / 0 E = 4 853.**

**Pool historique restant à examiner = 2 380** : 1 849 NULL + 135 STUB + 115 PARTIEL + 272 ABI-DIFF + 9 AMBIGU.

## Requalification firmware — hid:tmp / idle:sys / spsm — 23/11/2026

La liste officielle des services borne `hid:tmp` à **HOS 3.0.0–7.0.1**, et `idle:sys` / `spsm` à **HOS 1.0.0–13.2.1**. Les lignes encore NULL de ces services sont donc hors cible HOS23 : **15 NULL → HORS-VERSION** (1 + 4 + 10). Les entrées déjà classées autrement ne sont pas modifiées.

**Compteur historique : 1 527 IMPL-SRC / 115 PARTIEL / 135 STUB / 139 NOOP / 1 834 NULL / 84 D / 176 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 256 HORS-VERSION / 0 ABSENT / 272 ABI-DIFF / 9 AMBIGU / 0 E = 4 853.**

**Pool historique restant à examiner = 2 365** : 1 834 NULL + 135 STUB + 115 PARTIEL + 272 ABI-DIFF + 9 AMBIGU.

## Requalification firmware — WLAN local / Ethernet legacy / fgm:dbg — 23/11/2026

SwitchBrew borne ou retire avant HOS23 les services suivants : `wlan:lcl` (supprimé en 15.0.0+), `ethc:c` et `ethc:i` (1.0.0–14.1.2), `fgm:dbg` (1.0.0–8.1.0). Les **33 lignes encore NULL** passent **HORS-VERSION** : 19 + 6 + 5 + 3. Aucun runtime fictif n'est ajouté.

**Compteur historique : 1 527 IMPL-SRC / 115 PARTIEL / 135 STUB / 139 NOOP / 1 801 NULL / 84 D / 176 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 289 HORS-VERSION / 0 ABSENT / 272 ABI-DIFF / 9 AMBIGU / 0 E = 4 853.**

**Pool historique restant à examiner = 2 332** : 1 801 NULL + 135 STUB + 115 PARTIEL + 272 ABI-DIFF + 9 AMBIGU.

## Lot Friend HOS19/20+ — complétude runtime hors miroir historique — 23/11/2026

**Vendor `8e8e29be0c571686ca9852b6a968d440e20cd88e`** (arbre `6e41aa672a4f4098b982204ad00c8060b2e846dc`).

Six commandes présentes sur les firmwares modernes mais non matérialisées comme lignes distinctes dans l'ancien miroir historique sont maintenant raccordées dans le C++ actif : `EnsureFriendListAvailable` (10121), `EnsureBlockedUserListAvailable` (10421), `GetFriendRequestListV2` (20202), `GetBlockedUserListV2` (20402), `GetPlayHistoryListV2` (20702) et `GetReceivedFriendInvitationListV2` (22002).

Les deux commandes `Ensure*` consomment le `Uid` et confirment la disponibilité des listes locales. Les quatre listes V2 initialisent explicitement leur buffer de sortie, renvoient `count=0` et ne fabriquent aucune donnée sociale. Les sorties sont cohérentes avec les implémentations offline observées dans Den2/Citron ; aucun backend Nintendo/Nextendo n'est introduit.

**Ces six handlers améliorent la couverture HOS23 mais ne modifient pas le compteur historique 4 853**, puisque le miroir ancien ne leur attribue pas six entrées distinctes. Le compteur historique reste donc : **1 527 IMPL-SRC / 115 PARTIEL / 135 STUB / 139 NOOP / 1 801 NULL / 84 D / 176 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 289 HORS-VERSION / 0 ABSENT / 272 ABI-DIFF / 9 AMBIGU / 0 E = 4 853**, pool **2 332**.

Aucun build natif PS5 ni test console n'est revendiqué pour ce lot.

## Lot Friend moderne + requalification HOS23 ciblée — 23/11/2026

**Moteur parent validé `41280af8` :** NS1 X8D24 Vulkan et Verify pinned vendor verts. **Nouveau vendor `4ce41124344107322445092db240e74fa824dbc6`** (arbre `620e78545ee2775dbdfa0716fff9a64f789a3812`) : `GetProfileListV2` (10501) et `GetProfileExtraListV2` (20502) renvoient des listes offline initialisées et vides ; `GetFriendDetailedInfoV2` (20107) réutilise le handler 20102, son contrat ayant été recroisé avec Ryujinx-Nextendo (sortie 0x800, Uid, NSAID). Cela porte à **9 commandes Friend modernes HOS18+ raccordées hors lignes distinctes du vieux miroir** depuis le début de cette reprise.

Requalification firmware du miroir : **36 entrées → HORS-VERSION** sur preuve SwitchBrew actuelle : 7 BPC, 11 NIM shop, 2 hid:dbg, 1 hid:sys, 11 anciennes commandes HID racine (10 STUB + 1 IMPL-SRC), l'ancien `OpenSystemAppletProxy` cmd100, l'ancien `OpenLibraryAppletProxy` cmd200, `acc:su` cmd51 deprecated et cmd60. Aucun handler n'est supprimé du C++ : seule leur exigibilité sur la cible HOS23 est corrigée dans le catalogue.

**Compteur historique : 1 524 IMPL-SRC / 114 PARTIEL / 125 STUB / 139 NOOP / 1 780 NULL / 84 D / 176 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 325 HORS-VERSION / 0 ABSENT / 271 ABI-DIFF / 9 AMBIGU / 0 E = 4 853.**

**Pool historique restant à examiner = 2 299** : 1 780 NULL + 125 STUB + 114 PARTIEL + 271 ABI-DIFF + 9 AMBIGU.

Le nouveau vendor `4ce41124344107322445092db240e74fa824dbc6` n'est pas encore qualifié par les CI du moteur au moment de ce commit et aucun build natif/essai PS5 n'est revendiqué.

## Lot FSP runtime — montages programme / save / capacité — 23/11/2026

**Vendor `fca87f6aed972e9326a1b2e616649c9cbd884ee6`** (arbre `31ae4572584d1216be8bdc81a446a6f8110e94dc`), après palier moteur `ae310e43` validé par **NS1 X8D24 Vulkan** et **Verify pinned vendor**.

- cmd9 `OpenDataFileSystemByProgramId` : **NULL → IMPL-SRC**, montage du RomFS Program patché par `ProgramId` via le `ContentProvider` actif ;
- cmd204 `OpenDataFileSystemWithProgramIndex` : **NULL → IMPL-SRC**, variante filesystem du chemin déjà utilisé par le cmd205 storage ;
- cmd612 `GetFreeSpaceSizeForSaveData` : **NULL → IMPL-SRC**, ABI `Out<s64> + SaveDataSpaceId`, capacité réelle NAND/SD via `FileSystemController` ;
- cmd13 `InvalidateBisCache` : **NULL → NOOP documenté** ; Encore expose le BIS via VFS et ne maintient pas le cache MBR/GPT de FS-module que la commande Horizon invalide ;
- cmd35 `CreateSaveDataFileSystemWithHashSalt` : **NULL → PARTIEL** ; l’ABI complète 0xB0 est consommée et le save est réellement créé au `space_id`, mais le backend host-directory ne matérialise pas le hash salt ni les métadonnées d’intégrité.

**Compteur historique : 1 527 IMPL-SRC / 115 PARTIEL / 125 STUB / 140 NOOP / 1 775 NULL / 84 D / 176 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 325 HORS-VERSION / 0 ABSENT / 271 ABI-DIFF / 9 AMBIGU / 0 E = 4 853.**

**Pool historique restant à examiner = 2 295** : 1 775 NULL + 125 STUB + 115 PARTIEL + 271 ABI-DIFF + 9 AMBIGU.

Aucun build natif PS5 ni résultat console n’est revendiqué pour ce nouveau vendor à ce stade.

## Lot Friend — aliases modernes HOS18/22+ prouvés — 23/11/2026

**Vendor `170c613138dfa7d8740459239f2ee9cb54a936b1`** (arbre `006b451ddc375575b35ec37778356243273f01e5`).

Trois handlers modernes supplémentaires sont raccordés sans nouveau backend : `GetFriendProfileImageWithImageSize` (10111) réutilise `GetFriendProfileImage`, et `UpdateFriendInfoForViewerV1` / `V2` (20106/20109) réutilisent `GetFriendDetailedInfo`. Lichii emploie exactement ces mêmes routes pour ces IDs. Les sorties Encore restent offline/default et aucune donnée sociale fictive n'est créée.

Ces commandes ne sont pas matérialisées comme entrées distinctes dans le miroir historique 4 853 ; **le compteur historique reste inchangé à 1 775 NULL et pool 2 295**, tandis que la couverture runtime HOS23 progresse.

Aucun build natif PS5 ni test console n'est revendiqué pour ce lot.

## Lot FSP — suppression réelle du cache programme — 23/11/2026

**Vendor `3234390c8fa29100b3d64b637ed1abf822e6b223`** (arbre `24772de52fe6c3837ff71231e2121b5bcebd47a0`).

`fsp-srv::DeleteCacheStorage` (cmd 33) passe **NULL → IMPL-SRC**. Le contrat HOS est `u16 index -> ()`; Encore supporte déjà un seul slot de cache par programme dans `GetCacheStorageSize`, donc la suppression accepte uniquement l'index 0. Le handler ouvre le vrai espace User via `SaveDataController`, cible `save/cache/<program_id>`, vérifie l'existence puis utilise la suppression récursive VFS existante. Aucun chemin hôte absolu n'est exposé et aucun succès n'est renvoyé si le cache est absent.

Le manifeste `eden-backports` et le pin du test hôte existant ont été rafraîchis dans le même commit. `QuerySaveDataTotalSize` (601) reste volontairement NULL : LibHac calcule des overheads JournalIntegrity et un simple `data+journal` serait faux.

**Compteur historique : 1 528 IMPL-SRC / 115 PARTIEL / 125 STUB / 140 NOOP / 1 774 NULL / 84 D / 176 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 325 HORS-VERSION / 0 ABSENT / 271 ABI-DIFF / 9 AMBIGU / 0 E = 4 853.**

**Pool historique restant à examiner = 2 294** : 1 774 NULL + 125 STUB + 115 PARTIEL + 271 ABI-DIFF + 9 AMBIGU.

Aucun build natif PS5 ni test console n'est revendiqué pour ce lot.

## Lot FSP — lecteur SaveData filtré multi-résultats — 23/11/2026

**Vendor `9f4f9bef141c33a3bce353f68cf5b58bd94603e5`** (arbre `bf9097bdaf82c025fc15f2a4cd9e1541adbdb152`).

`fsp-srv::OpenSaveDataInfoReaderWithFilter` (cmd 68) passe **NULL → IMPL-SRC**. L'ABI recroisée avec Ryujinx/LibHac est `SaveDataSpaceId + SaveDataFilter -> ISaveDataInfoReader`. Le nouveau constructeur du reader énumère d'abord le vrai backing Encore, puis conserve **toutes** les entrées satisfaisant les drapeaux de filtre (program id, type, user id, save id, index et rank). Il ne réutilise pas le lookup mono-résultat de cmd67.

Le manifeste `eden-backports` couvre les quatre unités modifiées et le test hôte existant vérifie le raccordement cmd68 et les critères du filtre.

**Compteur historique : 1 529 IMPL-SRC / 115 PARTIEL / 125 STUB / 140 NOOP / 1 773 NULL / 84 D / 176 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 325 HORS-VERSION / 0 ABSENT / 271 ABI-DIFF / 9 AMBIGU / 0 E = 4 853.**

**Pool historique restant à examiner = 2 293** : 1 773 NULL + 125 STUB + 115 PARTIEL + 271 ABI-DIFF + 9 AMBIGU.

Aucun build natif PS5 ni test console n'est revendiqué pour ce lot.

## Lot FSP — écriture ExtraData masquée — 23/11/2026

**Vendor `8a721e38520792fdc1e0f474ec2ef07d7c16a665`** (arbre `72e68b086fb0911c6211d0550c753f87feb3f966`).

`fsp-srv::WriteSaveDataFileSystemExtraDataWithMask` (cmd 66) passe **NULL → PARTIEL**. L'ABI HOS recroisée est `SaveDataSpaceId + saveDataId + deux buffers SaveDataExtraData`. Encore valide les deux buffers 0x200 et résout la cible réelle via le reader save-data ; sur le backend directory-save sans ExtraData physique, l'écriture reste ensuite un no-op cohérent avec les autres chemins ExtraData. Ce statut reste PARTIEL car la métadonnée n'est pas persistée.

**Compteur historique : 1 529 IMPL-SRC / 116 PARTIEL / 125 STUB / 140 NOOP / 1 772 NULL / 84 D / 176 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 325 HORS-VERSION / 0 ABSENT / 271 ABI-DIFF / 9 AMBIGU / 0 E = 4 853.**

**Pool historique restant à examiner = 2 293** : 1 772 NULL + 125 STUB + 116 PARTIEL + 271 ABI-DIFF + 9 AMBIGU.

Aucun build natif PS5 ni test console n'est revendiqué.

## Lot NIFM IRequest — Requirement HOS23 byte-exact — 23/11/2026

**Vendor `62660c058f2a76353dba6bc208f165857460000e`** (arbre `1b4a906b11137ad31c9b45a3063e70d6686a0eeb`).

`SetRequirement` (5) et `GetRequirement` (19) passent **2 NULL → IMPL-SRC**. Le dump reverse NS1 **23.0.1** confirme exactement 0x24 octets en entrée/sortie ; SwIPC confirme `nn::nifm::Requirement = bytes<0x24, align 4>`. Encore conserve donc les 0x24 octets opaques dans l'objet `IRequest` et les restitue sans interprétation ni perte. Aucun champ interne non documenté n'est inventé.

`SetRequirementByRevision` (18) et `GetRevision` (20) restent ouverts : une simple mémorisation du numéro de révision ne suffirait pas à reproduire la transformation firmware vers un Requirement.

**Compteur historique : 1 531 IMPL-SRC / 116 PARTIEL / 125 STUB / 140 NOOP / 1 770 NULL / 84 D / 176 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 325 HORS-VERSION / 0 ABSENT / 271 ABI-DIFF / 9 AMBIGU / 0 E = 4 853.**

**Pool historique restant à examiner = 2 291** : 1 770 NULL + 125 STUB + 116 PARTIEL + 271 ABI-DIFF + 9 AMBIGU.

Pas de build natif PS5 ni de validation console revendiqués pour ce lot.

## Lot NIFM IRequest — requête persistante — 23/11/2026

**Vendor `2a7dfec8c6e31b4ba004501a666a4836443d3787`** (arbre `463636f6351a0b366b0e226fc88e3f0ad91f0f1b`).

`SetPersistent` (cmd 12) passe **NULL → IMPL-SRC**. L'ABI amont est un booléen/byte. Le flag agit réellement sur la machine d'état d'`IRequest` : si la connectivité disparaît, une requête persistante repasse en `OnHold` au lieu de devenir `Invalid`, puis revient en `Accepted` lorsque la connectivité revient. Les requêtes non persistantes gardent le comportement précédent.

**Compteur historique : 1 532 IMPL-SRC / 116 PARTIEL / 125 STUB / 140 NOOP / 1 769 NULL / 84 D / 176 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 325 HORS-VERSION / 0 ABSENT / 271 ABI-DIFF / 9 AMBIGU / 0 E = 4 853.**

**Pool historique restant à examiner = 2 290** : 1 769 NULL + 125 STUB + 116 PARTIEL + 271 ABI-DIFF + 9 AMBIGU.

Aucun build natif PS5 ni test console n'est revendiqué pour ce lot.

## Lot SSL — contexte système réel + CreateConnectionEx — 23/11/2026

**Vendor `d449cce2968bd306801b4ecbb5f3756134a540ae`** (arbre `cb9fd5e6168e4134898c5e9b4516a5c9f55a1c53`).

Le chemin PS5 natif sélectionne explicitement `encore-active/eden-core/src/core/hle/service/ssl` via `headless/CMakeLists.txt` (R23 #120). `ssl:s` cmd0/cmd100 ne renvoient plus un succès vide : ils créent un vrai `ISslContext`. Le contexte créé par cmd100 est marqué système et expose `ISslContext::CreateConnectionEx` (cmd100) en alias du backend `CreateConnection` existant ; le contexte utilisateur n'expose pas cet alias. Le test hôte SSL existant a été étendu pour verrouiller ce graphe.

Le miroir historique 4 853 ne matérialise pas `CreateConnectionEx` comme entrée distincte et le cmd0 existant était déjà PARTIEL : **compteur historique inchangé à 1 532 IMPL-SRC / 116 PARTIEL / 125 STUB / 140 NOOP / 1 769 NULL / 84 D / 176 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 325 HORS-VERSION / 0 ABSENT / 271 ABI-DIFF / 9 AMBIGU / 0 E = 4 853 ; pool 2 290.**

Aucun build natif PS5 ni test console n'est revendiqué pour ce lot.

## Lot NIFM IRequest — état de politique et descripteurs — 23/11/2026

**Vendor `1e7f7911c5601714733c53e3b5b73a15ec44c9b7`** (arbre `f7cdef676a8b47790971e20c2b6ba03e0d66cb81`).

Douze commandes `IRequest` passent **NULL → PARTIEL** avec leurs signatures SwIPC exactes : `SetPriority(u8)`, `SetRejectable(b8)`, `SetInstant(b8)`, `SetSustainable(b8,u8)`, `SetRawPriority(u8)`, `SetGreedy(b8)`, `SetSharable(b8)`, `SetRequirementByRevision(u32)`, `GetRevision()->u32`, `SetKeptInSleep(b8)`, `RegisterSocketDescriptor(u32)` et `UnregisterSocketDescriptor(u32)`.

L'état est conservé dans l'objet `IRequest` sous le verrou existant ; les descripteurs sont enregistrés dans un ensemble réel, et la révision est relue par `GetRevision`. Ces commandes restent **PARTIELLES** parce que priorité, greedy/sustainable, sleep et sockets ne pilotent pas encore toutes les politiques/arbitrages réseau Horizon.

**Compteur historique : 1 532 IMPL-SRC / 128 PARTIEL / 125 STUB / 140 NOOP / 1 757 NULL / 84 D / 176 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 325 HORS-VERSION / 0 ABSENT / 271 ABI-DIFF / 9 AMBIGU / 0 E = 4 853.**

**Pool historique restant à examiner = 2 290** : 1 757 NULL + 125 STUB + 128 PARTIEL + 271 ABI-DIFF + 9 AMBIGU. Le pool ne baisse pas sur ce lot : douze inconnues NULL deviennent douze comportements partiels qualifiés.

Aucun build natif PS5 ni test console n'est revendiqué pour ce lot.

## Lot NIFM — notification live et délai WoWLAN — 23/11/2026

**Vendor `0e9652b4f19ca998fe7d60d34460bd4bbdb1be30`** (arbre `d8fcbce6d134cdcd8716060d7817c94cf5f89df7`).

- `NotifyConnectionStateChanged` (42) : **NULL → NOOP**. Encore n'entretient pas de cache NIFM séparé ; les requêtes réseau relisent `EmuNetState` / rafraîchissent l'hôte, donc la notification n'a aucun état interne à invalider.
- `SetWowlDelayedWakeTime(s32)` (43) : **NULL → PARTIEL**. La valeur Horizon est réellement consommée et conservée dans `IGeneralService`; Encore n'a pas encore de daemon wake-on-wireless PS5 qui applique ce délai.

**Compteur historique : 1 532 IMPL-SRC / 129 PARTIEL / 125 STUB / 141 NOOP / 1 755 NULL / 84 D / 176 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 325 HORS-VERSION / 0 ABSENT / 271 ABI-DIFF / 9 AMBIGU / 0 E = 4 853.**

**Pool historique restant à examiner = 2 289** : 1 755 NULL + 125 STUB + 129 PARTIEL + 271 ABI-DIFF + 9 AMBIGU.

Aucun build natif PS5 ni test console n'est revendiqué pour ce lot.

## Requalification PCIe — session impossible à obtenir — 23/11/2026

Le service racine `pcie` est bien exposé, mais ses deux commandes racine `RegisterClassDriver` et `QueryFunctionsUnregistered` restent NULL et **aucun code Encore ne construit ni ne retourne `ISession`** (`make_shared<ISession>` / `PushIpcInterface<ISession>` absents).

Les **20 commandes de session** présentes dans le miroir historique, de `QueryFunctions` à `SetIrqEnable`, passent donc **NULL → INACCESSIBLE**. Les deux commandes racine restent NULL ; l'entrée ID20 `SetAspmEnable` reste ABI-DIFF car la table actuelle utilise ID20 pour `GetIrqEvent`.

**Compteur historique : 1 532 IMPL-SRC / 129 PARTIEL / 125 STUB / 141 NOOP / 1 735 NULL / 84 D / 196 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 325 HORS-VERSION / 0 ABSENT / 271 ABI-DIFF / 9 AMBIGU / 0 E = 4 853.**

**Pool historique restant à examiner = 2 269** : 1 735 NULL + 125 STUB + 129 PARTIEL + 271 ABI-DIFF + 9 AMBIGU.

## Lot PSM — état d'alimentation hôte et correction ABI HOS17+ — 23/11/2026

**Vendor `5f7e92ebb9600809d81ee6fbb898c7011b95c719`** (arbre `faf1ab63c88c0c408b42c74735e2072d90818c84`).

Onze commandes PSM quittent NULL. `GetRawBatteryChargePercentage` (13) passe **IMPL-SRC** avec l'ABI `f64` confirmée par libnx/SwIPC et lit `Common::PowerStatus` quand l'hôte expose une batterie, sinon 100.0. Les commandes 2/3/4, 5/6, 8/9, 10/11 et `IsEnoughPowerSupplied` (14) passent **PARTIEL** : leurs états sont réellement conservés dans `PSM`, et fast-charge / controller-supply / battery-charging sont reflétés dans `GetBatteryChargeInfoFields`, mais ils ne pilotent évidemment pas physiquement l'alimentation PS5.

Le même patch corrige une divergence ABI existante de `BatteryChargeInfoFields` HOS17+ : `battery_charge_percentage` et `battery_age_percentage` sont des **u32 per-cent-mille**, pas des `f32`. Le fallback 100 % devient donc 100000. Les événements 16/18 restent NULL : aucun watcher de batterie hôte ne peut actuellement les signaler correctement.

**Compteur historique : 1 533 IMPL-SRC / 139 PARTIEL / 125 STUB / 141 NOOP / 1 724 NULL / 84 D / 196 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 325 HORS-VERSION / 0 ABSENT / 271 ABI-DIFF / 9 AMBIGU / 0 E = 4 853.**

**Pool historique restant à examiner = 2 268** : 1 724 NULL + 125 STUB + 139 PARTIEL + 271 ABI-DIFF + 9 AMBIGU.

Aucun build natif PS5 ni test console n'est revendiqué pour ce lot.

## Lot audctl — cible audio, play-report et tri firmware — 23/11/2026

**Vendor `c67f77d5b33e71ca70621ab4637f559a420d998d`** (arbre `9e60f3bc7e6a85b5f6c5fb6d4ce79ece460be73e`), propriétaire actif `encore-active/eden-core/src/core/hle/service/audio/audio_controller.cpp`.

- `Set/GetDefaultTarget` (7/8), `SetOutputTarget` (15), `SetInputTargetForceEnabled` (16), `GetAudioOutputTargetForPlayReport` (21) et `Set/GetSystemOutputMasterVolume` (23/24) sont raccordés. La cible active applique le volume/mute déjà maintenu et signale `AcquireTargetNotification`.
- 7, 16 et 23 restent **PARTIELS** : les temps de fade, le routage d'entrée forcé et le gain master ne sont pas encore appliqués de bout en bout. 8, 15, 21 et 24 sont classés **IMPL-SRC**.
- libnx confirme que `IsTargetConnected` (6) s'arrête à 17.0.1, `Set/GetForceMutePolicy` (11/12) à 13.2.1, et les événements play-report 19/20 à 13.2.1 : **5 entrées → HORS-VERSION** pour HOS23.
- Le conflit de nomenclature entre `AudioTarget` libnx et `AudioOutputModeTarget` historique Eden/Lichii-rust reste explicitement ouvert ; aucune remap numérique spéculative n'a été introduite.

**Compteur historique : 1 537 IMPL-SRC / 142 PARTIEL / 124 STUB / 141 NOOP / 1 713 NULL / 84 D / 196 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 330 HORS-VERSION / 0 ABSENT / 271 ABI-DIFF / 9 AMBIGU / 0 E = 4 853.**

**Pool historique restant à examiner = 2 259** : 1 713 NULL + 124 STUB + 142 PARTIEL + 271 ABI-DIFF + 9 AMBIGU.

Aucun build natif PS5 ni test console n'est revendiqué pour ce lot.

## Lot audctl — modes de sortie et casque persistants — 23/11/2026

**Vendor `d23a6e5bbb235f4b277e523baeac668330eb5982`** (arbre `3c893de47856e787abf50ca4b0b86429b243225b`).

`GetOutputModeSetting` (13) et `SetHeadphoneOutputLevelMode` (17) quittent **STUB → IMPL-SRC** : les réglages sont désormais conservés, et leurs getters (13/18) relisent l'état réel de la session. `NotifyHeadphoneVolumeWarningDisplayedEvent` (22) passe **STUB → NOOP** : Encore ne maintient aucune latch d'avertissement casque distincte à acquitter.

**Compteur historique : 1 539 IMPL-SRC / 142 PARTIEL / 121 STUB / 142 NOOP / 1 713 NULL / 84 D / 196 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 330 HORS-VERSION / 0 ABSENT / 271 ABI-DIFF / 9 AMBIGU / 0 E = 4 853.**

**Pool historique restant à examiner = 2 256** : 1 713 NULL + 121 STUB + 142 PARTIEL + 271 ABI-DIFF + 9 AMBIGU.

## Lot FSP — RightsId réel du NCA Program — 23/11/2026

**Vendor `83acc5124b1cdb62ba4b65ed8607968c832757a4`** (arbre `b7bf7c18140e7af806bccb2aab1ee99733a09937`).

`fsp-srv::GetRightsId` (cmd 606) passe **NULL → IMPL-SRC**. L'ABI recroisée avec Ryubing/LibHac est `StorageId + ProgramId -> RightsId[0x10]`. Le handler ouvre le NCA Program réel via `RomFsController::OpenBaseNca`, renvoie `TargetNotFound` si l'entrée n'existe pas et copie directement `NCA::GetRightsId()`. Aucun RightsId synthétique n'est fabriqué.

Les variantes par chemin 609/610 restent ouvertes : elles exigent une résolution sûre du `FspPath` vers l'archive NCA et ne sont pas aliasées à 606.

**Compteur historique : 1 540 IMPL-SRC / 142 PARTIEL / 121 STUB / 142 NOOP / 1 712 NULL / 84 D / 176 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 325 HORS-VERSION / 0 ABSENT / 271 ABI-DIFF / 9 AMBIGU / 0 E = 4 853.**

**Pool historique restant à examiner = 2 255** : 1 712 NULL + 121 STUB + 142 PARTIEL + 271 ABI-DIFF + 9 AMBIGU.

Aucun build natif PS5 ni test console n'est revendiqué pour ce lot.

## Lot FSP — clés externes transitoires sans pollution de title.keys — 23/11/2026

**Vendor `0d4246090dac222c344cb3bed912728c56d79c7b`** (arbre `181d4d1a18dedf20c4e28fb4c1a48a8fde2be1d9`).

Les commandes `RegisterExternalKey` (607), `UnregisterAllExternalKey` (608) et `UnregisterExternalKey` (617) passent **NULL → IMPL-SRC**. L'ABI est recroisée avec Ryubing/LibHac : `RightsId[0x10] + AccessKey[0x10]` pour 607, aucun argument pour 608, `RightsId[0x10]` pour 617.

Le correctif ajoute dans le `KeyManager` actif un overlay `external_title_keys` distinct de `s128_keys`. `HasKey/GetKey` consultent l'overlay en priorité uniquement pour `S128KeyType::Titlekey`. Enregistrement d'un doublon identique réussit ; une valeur différente pour le même RightsId renvoie **FS 6452 / NcaExternalKeyInconsistent**. Les unregister ne peuvent jamais effacer une clé chargée depuis `title.keys`.

Les deux unités `key_manager.cpp/.h` sont ajoutées comme backports complets avec empreinte upstream et active dans le manifeste, plutôt que de modifier le socle `sources/eden`.

**Compteur historique : 1 543 IMPL-SRC / 142 PARTIEL / 121 STUB / 142 NOOP / 1 709 NULL / 84 D / 176 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 325 HORS-VERSION / 0 ABSENT / 271 ABI-DIFF / 9 AMBIGU / 0 E = 4 853.**

**Pool historique restant à examiner = 2 252** : 1 709 NULL + 121 STUB + 142 PARTIEL + 271 ABI-DIFF + 9 AMBIGU.

Aucun build natif PS5 ni test console n'est revendiqué pour ce lot.

## Lot BTM legacy — état radio partagé avec set:sys — 23/11/2026

**Vendor `0fcec5e76502b0def90d946bffdc29ff3e19000f`** (arbre `562294e7a9742631cdaab84d2924f6454486a4a3`).

`btm::EnableRadio` (14) et `btm::DisableRadio` (15) passent **NULL → IMPL-SRC**. SwIPC confirme que les deux commandes legacy n'ont ni entrée ni sortie. Le backport résout `set:sys` une seule fois et appelle les mêmes `SetBluetoothEnableFlag(true/false)` que `IBtmSystemCore`, de sorte que les interfaces legacy et moderne partagent un état unique.

`btm::GetState` (0) reste ouvert : SwIPC ne documente que quatre octets de sortie inconnus et aucun enum fiable n'a été trouvé ; aucune valeur synthétique n'est ajoutée.

**Compteur historique : 1 545 IMPL-SRC / 142 PARTIEL / 121 STUB / 142 NOOP / 1 707 NULL / 84 D / 176 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 325 HORS-VERSION / 0 ABSENT / 271 ABI-DIFF / 9 AMBIGU / 0 E = 4 853.**

**Pool historique restant à examiner = 2 250** : 1 707 NULL + 121 STUB + 142 PARTIEL + 271 ABI-DIFF + 9 AMBIGU.

Aucun build natif PS5 ni test console n'est revendiqué pour ce lot.


## Lot HID debug — désactivation des contrôleurs réels — 23/11/2026

**Vendor `a243ecb09ad7853c9be5f1d9d192c5206c1ef3cc`** (arbre `f53f4750d84de2bbb941984508a885241e7e6f41`).

Neuf handlers runtime `hid:dbg` sont désormais raccordés : `DeactivateDebugPad` (0), `DeactivateMouse` (20), `DeactivateKeyboard` (30), `DeactivateHomeButton` (110), `DeactivateSleepButton` (120), `DeactivateCaptureButton` (130), `DeactivateConsoleSixAxisSensor` (140), `DeactivateSevenSixAxisSensor` (142) et `DeactivateDigitizer` (2000).

Le handler résout le périphérique déjà détenu par le `ResourceManager` actif et appelle `ControllerBase::DeactivateController()`. Aucun état HID synthétique, aucune sortie inventée et aucun alias de commande ne sont ajoutés. La table `hid:dbg` réellement compilée est celle de `sources/eden/src/core/hle/service/hid/hid_debug_server.cpp`, listée par le CMake actif ; aucun overlay homonyme `encore-active/eden-backports` ne la remplace.

Le catalogue canonique SwitchBrew utilisé par ce registre contient huit de ces neuf commandes : elles passent **NULL → IMPL-SRC**. `DeactivateDigitizer` (2000) n'est pas présent dans ce dénominateur physique et ne fait donc pas baisser artificiellement le compteur.

**Compteur historique : 1 553 IMPL-SRC / 142 PARTIEL / 121 STUB / 142 NOOP / 1 699 NULL / 84 D / 176 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 325 HORS-VERSION / 0 ABSENT / 271 ABI-DIFF / 9 AMBIGU / 0 E = 4 853.**

**Pool historique restant à examiner = 2 242** : 1 699 NULL + 121 STUB + 142 PARTIEL + 271 ABI-DIFF + 9 AMBIGU.

Aucun build natif PS5 ni test console n'est revendiqué pour ce lot.


## Lot AM stateful + HID policy HOS 23 — 23/11/2026

**Vendor `f20f6736b79259cb325f6a44b7b994749e458bec`** (arbre `c467583c2cc4dd86e59461792c31a0d43f6f82cc`).

Le dump IPC NS1 **HOS 23.0.1** de `borntohonk/Switch-Ghidra-Guides` confirme pour `hid:dbg` cmd 60 `ClearNpadSystemCommonPolicy` un payload **0x8 + PID, sortie 0**. Le runtime raccorde cette commande au backend déjà présent `NPad::ClearNpadSystemCommonPolicy(system.Kernel(), aruid.pid)`. La cmd 3000 `ReloadFirmwareDebugSettings` est aussi raccordée à `HidFirmwareSettings::Reload()`, mais elle n'est pas matérialisée dans le dénominateur SwitchBrew historique et ne modifie donc pas le compteur.

La revue des **STUB appletAE** a identifié neuf faux positifs : leurs corps modifient déjà un état applet réel ou retournent un objet réel. Ils passent **STUB → IMPL-SRC** : `SetDisplayMagnification`, `GetGpuErrorDetectedSystemEvent`, `IsGamePlayRecordingSupported`, `SetGamePlayRecordingState`, `EnableApplicationCrashReport`, `PrepareForJit`, `SetScreenShotAppletIdentityInfo`, `SetAlbumImageOrientation`, `SetAlbumImageTakenNotificationEnabled`. Les marqueurs de log `(STUBBED)` trompeurs ont été retirés du C++ actif.

Les trois `Release*CaptureSharedBuffer` passent **STUB → NOOP** avec justification runtime : `WriteAppletCaptureBuffer` effectue une copie synchrone sous `SharedBufferManager::m_guard` puis libère ce verrou avant le retour ; aucun ownership persistant n'existe à relâcher.

**Compteur historique : 1 563 IMPL-SRC / 142 PARTIEL / 109 STUB / 145 NOOP / 1 698 NULL / 84 D / 196 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 330 HORS-VERSION / 0 ABSENT / 271 ABI-DIFF / 9 AMBIGU / 0 E = 4 853.**

**Pool historique restant à examiner = 2 229** : 1 698 NULL + 109 STUB + 142 PARTIEL + 271 ABI-DIFF + 9 AMBIGU.

Aucun build natif PS5 ni test console n'est revendiqué pour ce lot.


## Lot HID system handles + AOC factories — 23/11/2026

**Vendor `ecb8ae0e177cf5ac2015b26bff722f70a147f6cd`** (arbre `f54da66c6c41185383dcf9df07f0211aee96df5c`) ; moteur de la branche repointé sur ce gitlink.

Sept entrées sortent du pool de revue. `hid` cmd51 `ActivateXpad` passe **STUB → NOOP** : le commentaire source confirme le comportement de compatibilité sans effet depuis Horizon 10.0.0+, donc applicable à la cible HOS 23.x. Côté `hid:sys`, `IsJoyConRailEnabled` passe **STUB → IMPL-SRC** en lisant `HidFirmwareSettings::IsRailEnabled()` au lieu de renvoyer `true` en dur.

Trois acquisitions d'événements `hid:sys` passent **STUB → IMPL-SRC** parce qu'elles retournent des `KEvent` réellement créés et détenus par `IHidSystemServer`. Le lot corrige en plus un bug concret : cmd544 `AcquireConnectionTriggerTimeoutEvent` renvoyait auparavant `acquire_device_registered_event`; elle retourne désormais `acquire_connection_trigger_timeout_event`. La source de signalisation de ces événements reste à qualifier séparément ; aucune réactivité console n'est déduite de la seule validité du handle.

Enfin, `aoc:u` cmd100/101 passent **STUB → IMPL-SRC** : les deux factories construisent et retournent effectivement `IPurchaseEventManager`. Le propriétaire maintenu est `vendor/encore-active/eden-core/src/core/hle/service/aoc/addon_content_manager.cpp`, mais le build unifié retire ce TU puis sélectionne `headless/nup_v1_aoc_service.cpp` via `headless/nup_v1_runtime.cmake`; les deux propriétaires sont donc gardés cohérents. `GetAddOnContentListChangedEvent` reste ouvert/partiel : un `KEvent` existe mais sa signalisation n'est pas prouvée.

**Compteur historique : 1 569 IMPL-SRC / 142 PARTIEL / 102 STUB / 146 NOOP / 1 698 NULL / 84 D / 196 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 330 HORS-VERSION / 0 ABSENT / 271 ABI-DIFF / 9 AMBIGU / 0 E = 4 853.**

**Pool historique restant à examiner = 2 222** : 1 698 NULL + 102 STUB + 142 PARTIEL + 271 ABI-DIFF + 9 AMBIGU.

Aucun build natif PS5 ni test console n'est revendiqué pour ce lot.


## Lot factories/stateful services — 23/11/2026

**Vendor `81cf89d58b0b4081ea3e276668368040a6a75355`** (arbre `147ec9af95f283aad866c61ed853cb76be98c270`).

Onze entrées sortent du pool sans succès factice. `clkrst` cmd7/8 passent **STUB → IMPL-SRC** : le setter conserve la fréquence dans l'état de session et le getter relit exactement cette valeur. Les factories NIM ECA `CreateServerInterface` / `CreateAccessorInterface` et LP2P `CreateNetworkService` / `CreateNetworkServiceMonitor` passent **STUB → IMPL-SRC** car elles construisent et renvoient leurs interfaces IPC concrètes.

NPNS `GetReceiveEvent` retourne son `KEvent` réel et `GetState` expose explicitement l'état offline du backend local : **STUB → IMPL-SRC**. `ListenTo` devient **NOOP documenté** : Encore n'a pas de connexion Nintendo Push et accepte localement l'abonnement sans prétendre avoir créé un abonnement distant. NSD `GetEnvironmentIdentifier` retourne le profil local stable `lp1` avec le changement d'environnement Nintendo volontairement désactivé. CAPS `GetAutoSavingStorage` délègue au `AlbumManager` et expose la capacité actuelle au lieu d'être un corps vide.

Les six unités concernées sont bien listées dans `encore-active/eden-backports/src/core/CMakeLists.txt`. Les autres STUB proches qui renvoient des constantes arbitraires, ignorent un payload utile ou n'ont pas de backend (I2C data path, SSL PKI, AM copyright/capture, etc.) restent ouverts.

**Compteur historique : 1 579 IMPL-SRC / 142 PARTIEL / 91 STUB / 147 NOOP / 1 698 NULL / 84 D / 196 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 330 HORS-VERSION / 0 ABSENT / 271 ABI-DIFF / 9 AMBIGU / 0 E = 4 853.**

**Pool historique restant à examiner = 2 211** : 1 698 NULL + 91 STUB + 142 PARTIEL + 271 ABI-DIFF + 9 AMBIGU.

Aucun build natif PS5 ni test console n'est revendiqué pour ce lot.


## Lot handles/events/stateful options — 23/11/2026

**Vendor `2f294bbfaa54440eaf9dafe9cabd2c104ba3a439`** (arbre `0675e1f32d05e13c3ae0c8bbf0c20d841be03ecf`).

Douze entrées sortent du pool. Neuf passent **STUB → IMPL-SRC** : Bluetooth `RegisterBleEvent`, NS `OpenSystemUpdateControl`, OLSC `GetNativeHandle`, NFC Mifare `Write`, Audio `QueryAudioDeviceSystemEvent` / `GetActiveChannelCount`, SSL `SetOption` / `GetOption`, et NSD `SetChangeEnvironmentIdentifierDisabled`. Elles retournent des objets/events réels, atteignent un backend réel ou conservent/relisent un état de contexte observable.

Trois passent **STUB → NOOP** avec justification contractuelle : VI `SetDisplayEnabled` est commenté dans la source comme une commande qui ne fait littéralement rien dans le service réel ; `notif:a Initialize` n'a aucune persistance externe à restaurer parce que le backend d'alarmes est déjà en mémoire ; `IAsyncValue::Cancel` s'applique à un objet synchrone dont l'événement de complétion est signalé dès le constructeur, et le dump IPC HOS 23 confirme une cmd2 sans sortie.

La source SSL réellement compilée sur PS5 a été vérifiée dans `headless/CMakeLists.txt` : le build retire les deux TUs SSL de base et sélectionne exactement `vendor/encore-active/eden-core/src/core/hle/service/ssl/ssl.cpp` + backend OpenSSL assorti. Les TUs VI/BT/NS/OLSC/NFC/Audio/notif/NSD sont listés dans le CMake core actif.

Important : `GetUniquePadIds` reste STUB. L'ABI demande un buffer de `UniquePadId`, mais le backend Encore ne conserve pas d'identifiant matériel unique ; aucun ID n'a été inventé à partir des Npad IDs.

**Compteur historique : 1 588 IMPL-SRC / 142 PARTIEL / 79 STUB / 150 NOOP / 1 698 NULL / 84 D / 196 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 330 HORS-VERSION / 0 ABSENT / 271 ABI-DIFF / 9 AMBIGU / 0 E = 4 853.**

**Pool historique restant à examiner = 2 199** : 1 698 NULL + 79 STUB + 142 PARTIEL + 271 ABI-DIFF + 9 AMBIGU.

Aucun build natif PS5 ni test console n'est revendiqué pour ce lot.

## Lot HID user — batterie / interface / USB full-key — 23/11/2026

**Vendor `20d0c7bb01d31c80f090abec811f2d920b96240c`**, sélectionné par le nouveau gitlink moteur de cette branche.

Les commandes HID user **401–406** passent **NULL → IMPL-SRC**. Les commandes 403–406 exploitent les handlers NPad déjà présents pour les batteries et types d'interface, au lieu de renvoyer des constantes. Les ABI ont été recroisées : libnx confirme 400–402 et 405 ; les signatures 403/404/406 sont recoupées avec la table CMIF Ryujinx/SwIPC. La commande **400** passe **NOOP → IMPL-SRC** et son ancienne ABI erronée avec ARUID est corrigée : l'état enable/disable est maintenant conservé par le service.

Le runtime PS5 utilise bien l'overlay `encore-active/eden-backports/src/hid_core/resources/npad/npad.cpp`; la copie de base a reçu la même ABI pour préserver les builds/replays sans overlay, et l'empreinte du manifeste a été mise à jour.

**Compteur historique : 1 595 IMPL-SRC / 142 PARTIEL / 79 STUB / 149 NOOP / 1 692 NULL / 84 D / 196 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 330 HORS-VERSION / 0 ABSENT / 271 ABI-DIFF / 9 AMBIGU / 0 E = 4 853.**

**Pool historique restant à examiner = 2 193** : 1 692 NULL + 79 STUB + 142 PARTIEL + 271 ABI-DIFF + 9 AMBIGU.

Aucun build natif PS5 ni test console n'est revendiqué pour ce lot.

## Requalification du service historique `ns:am` — 23/11/2026

SwitchBrew documente explicitement que le service direct **`ns:am` a été remplacé par `ns:am2` à partir de HOS 3.0.0**. La cible NS1 Encore est HOS 23.x. Le propriétaire réellement compilé `encore-active/eden-backports/src/core/hle/service/ns/ns.cpp`, listé dans le CMake backports, enregistre `ns:am2`, `ns:ec`, `ns:rid`, `ns:rt`, `ns:web`, `ns:ro`, etc., mais **pas `ns:am`**. L'interface d'application moderne reste accessible via `IServiceGetterInterface::GetApplicationManagerInterface` (cmd 7996) et est suivie séparément dans le catalogue moderne.

Les **113 lignes historiques `ns:am`** sont donc reclassées **HORS-VERSION** pour la cible HOS 23.x. Avant reclassement, elles comprenaient 20 IMPL-SRC, 85 NULL, 2 PARTIEL, 1 STUB, 4 NOOP et 1 ABI-DIFF. Ce changement ne prétend pas implémenter 89 fonctions ; il retire correctement du pool courant une surface de service directe qui n'existe plus sur le firmware cible, sans masquer la dette de `ns:am2`.

**Compteur courant : 1 575 IMPL-SRC / 140 PARTIEL / 78 STUB / 145 NOOP / 1 607 NULL / 84 D / 196 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 443 HORS-VERSION / 0 ABSENT / 270 ABI-DIFF / 9 AMBIGU / 0 E = 4 853.**

**Pool restant à examiner = 2 104** : 1 607 NULL + 78 STUB + 140 PARTIEL + 270 ABI-DIFF + 9 AMBIGU.

La CI X8D24 du lot HID précédent est verte ; aucune validation gameplay PS5 n'est déduite de ce reclassement documentaire/source.

## Lot BSD `Read` — 23/11/2026

**Vendor `8c6c57ecded4a650ba575f8e937543a363a3d680`**, sélectionné par le nouveau gitlink moteur.

La commande BSD **25 `Read`** passe **STUB → IMPL-SRC**. L'ancien handler retournait systématiquement une lecture de longueur zéro avec errno zéro. Le nouveau handler réutilise le `RecvWork` déjà actif avec `flags=0`, ce qui correspond à la sémantique socket de `read()` et conserve le même chemin de descripteur, errno, blocage et copie du buffer que `Recv`. La copie de base et l'overlay backports réellement compilé ont été mis à jour ensemble, avec empreinte manifeste actualisée.

**Compteur courant : 1 576 IMPL-SRC / 140 PARTIEL / 77 STUB / 145 NOOP / 1 607 NULL / 84 D / 196 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 443 HORS-VERSION / 0 ABSENT / 270 ABI-DIFF / 9 AMBIGU / 0 E = 4 853.**

**Pool restant à examiner = 2 103** : 1 607 NULL + 77 STUB + 140 PARTIEL + 270 ABI-DIFF + 9 AMBIGU.

Pas de build natif PS5 ni de validation console revendiqués pour ce lot.

## Requalification BCAT 30300 — 23/11/2026

Le scan systématique des **77 STUB** contre leurs corps C++ actuels a trouvé une seule entrée déjà sortie du statut stub sans mise à jour du catalogue : `IBcatService::RegisterSystemApplicationDeliveryTasks` (30300). Le corps actif explique explicitement qu'Encore ne possède pas de scheduler Horizon de livraison BCAT en arrière-plan et que l'enregistrement des tâches système est donc un **NOOP intentionnel** ; les synchronisations BCAT réelles restent déclenchées par les requêtes explicites du backend.

**Compteur courant : 1 576 IMPL-SRC / 140 PARTIEL / 76 STUB / 146 NOOP / 1 607 NULL / 84 D / 196 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 443 HORS-VERSION / 0 ABSENT / 270 ABI-DIFF / 9 AMBIGU / 0 E = 4 853.**

**Pool restant à examiner = 2 102** : 1 607 NULL + 76 STUB + 140 PARTIEL + 270 ABI-DIFF + 9 AMBIGU.

Les 76 autres STUB conservent au moins un marqueur explicite de stub/TODO/UNIMPLEMENTED dans leur propriétaire courant ; ils ne sont pas requalifiés automatiquement.

## Requalification PCV legacy — 23/11/2026

SwitchBrew borne explicitement **`pcv:arb`** et **`pcv:imm`** à HOS **1.0.0–7.0.1**. Aucune réapparition ultérieure des mêmes noms de service n'est listée ; la cible Encore est HOS 23.x. Les deux commandes cataloguées (`ReleaseControl` et `SetClockRate`) passent donc **NULL → HORS-VERSION**. Les services PCV/clock actuels restent suivis séparément et ne sont pas masqués par ce reclassement.

**Compteur courant : 1 576 IMPL-SRC / 140 PARTIEL / 76 STUB / 146 NOOP / 1 605 NULL / 84 D / 196 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 445 HORS-VERSION / 0 ABSENT / 270 ABI-DIFF / 9 AMBIGU / 0 E = 4 853.**

**Pool restant à examiner = 2 100** : 1 605 NULL + 76 STUB + 140 PARTIEL + 270 ABI-DIFF + 9 AMBIGU.

## Réconciliation ABI simple — BTM / NFC / AOC / ES — 23/11/2026

Sept lignes classées ABI-DIFF dans le snapshot étaient des écarts de libellé/version, pas des trous de contrat : BTM System cmd6 lit le vrai flag radio partagé ; les trois managers NFC cmd0 retournent les interfaces attendues ; AOC PurchaseEvent cmd2 retourne son event lisible ; ES cmd11/12 correspondent aux variantes HOS6+ documentées par SwitchBrew et parcourent les tickets réels pour écrire les Rights IDs.

Elles passent **ABI-DIFF → IMPL-SRC**. Aucun C++ n'est modifié dans ce lot : il s'agit d'une réconciliation du catalogue avec le runtime déjà actif.

**Compteur courant : 1 583 IMPL-SRC / 140 PARTIEL / 76 STUB / 146 NOOP / 1 605 NULL / 84 D / 196 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 445 HORS-VERSION / 0 ABSENT / 263 ABI-DIFF / 9 AMBIGU / 0 E = 4 853.**

**Pool restant à examiner = 2 093** : 1 605 NULL + 76 STUB + 140 PARTIEL + 263 ABI-DIFF + 9 AMBIGU.

## Réconciliation ABI Time Manager / set:sys — 23/11/2026

Huit commandes `time:m` (0, 5, 6, 11, 13, 15, 60, 100) ont été recroisées avec les signatures SwitchBrew et leurs corps actifs : les suffixes `AsUser/Core/Updated/BaseTime` sont des noms internes, tandis que les interfaces, entrées/sorties et états manipulés correspondent au contrat documenté. Les slots 10/12/14/200/201 restent volontairement ABI-DIFF car l'ordre/type ou la sémantique n'est pas suffisamment équivalent pour les fermer par simple renommage.

Les commandes `set:sys` 45/46 sont également équivalentes : les handlers nommés `SpeakerAutoMuteFlag` lisent/écrivent directement le champ interne `force_mute_on_headphone_removed` documenté par SwitchBrew.

Ces **10 lignes passent ABI-DIFF → IMPL-SRC**, sans modification C++.

**Compteur courant : 1 593 IMPL-SRC / 140 PARTIEL / 76 STUB / 146 NOOP / 1 605 NULL / 84 D / 196 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 445 HORS-VERSION / 0 ABSENT / 253 ABI-DIFF / 9 AMBIGU / 0 E = 4 853.**

**Pool restant à examiner = 2 083** : 1 605 NULL + 76 STUB + 140 PARTIEL + 253 ABI-DIFF + 9 AMBIGU.

## Réconciliation ABI NFC system — 23/11/2026

Cinq lignes `nfc:sys` ont été recroisées avec SwitchBrew et les corps actifs. Le manager cmd0 renvoie réellement `ISystem`. Les commandes ISystem 0/1 et leurs variantes HOS4+ 400/401 utilisent le même backend réel `NfcInterface::Initialize/Finalize` : initialisation/finalisation du manager NFC, transition d'état et nettoyage du device manager. Les différences `CreateSystemNfcInterface`, `InitializeOld`, `InitializeSystem` et `FinalizeSystem` sont ici des libellés/versionnements, pas des fonctions manquantes.

Ces **5 lignes passent ABI-DIFF → IMPL-SRC**, sans modification C++. SPL cmd1 `ExpMod` reste volontairement ouvert : malgré son handler enregistré `ModularExponentiate`, le corps courant est encore `UNIMPLEMENTED` et renvoie `ResultSecureMonitorNotImplemented`.

**Compteur courant : 1 598 IMPL-SRC / 140 PARTIEL / 76 STUB / 146 NOOP / 1 605 NULL / 84 D / 196 INACCESSIBLE / 306 SERVICE-NON-EXPOSÉ / 445 HORS-VERSION / 0 ABSENT / 248 ABI-DIFF / 9 AMBIGU / 0 E = 4 853.**

**Pool restant à examiner = 2 078** : 1 605 NULL + 76 STUB + 140 PARTIEL + 248 ABI-DIFF + 9 AMBIGU.

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


## Requalification `mig:usr` — service non exposé (23/11/2026)

Sur le vendor/gitlink `8c6c57ecded4a650ba575f8e937543a363a3d680`, la classe `MIG_USR` conserve le nom interne `mig:usr`, mais `LoopProcess` enregistre uniquement **`mig:user`** auprès du `ServerManager`. Aucune entrée SM `mig:usr` n'est exposée. Les **19 lignes encore ABI-DIFF** rejoignent donc les 17 lignes déjà classées **SERVICE-NON-EXPOSÉ**. Ce lot est une correction de classification/accessibilité, **pas une implémentation de migration**.

**Compteur courant : 1 598 IMPL-SRC / 140 PARTIEL / 76 STUB / 146 NOOP / 1 605 NULL / 84 D / 196 INACCESSIBLE / 325 SERVICE-NON-EXPOSÉ / 445 HORS-VERSION / 0 ABSENT / 229 ABI-DIFF / 9 AMBIGU / 0 E = 4 853.**

**Pool restant à examiner = 2 059** : 1 605 NULL + 76 STUB + 140 PARTIEL + 229 ABI-DIFF + 9 AMBIGU.


## AOC — événement de changement d'inventaire raccordé (23/11/2026)

Vendor `ee971276a3254c0eb003f1e6f34cd10988874f1b` → gitlink moteur `df976b8722f7de250f7207b71183de559053e809`. `GetAddOnContentListChangedEvent` expose le `KEvent` réel existant ; `NotifyMountAddOnContent` et `NotifyUnmountAddOnContent` recalculent désormais la liste AOC depuis les providers actifs puis signalent l'événement. Le cmd8 passe **STUB → IMPL-SRC**. Les quatre stubs `IPurchaseEventManager` restent ouverts : aucune file d'achat eShop n'est inventée.

**Compteur courant : 1 599 IMPL-SRC / 140 PARTIEL / 75 STUB / 146 NOOP / 1 605 NULL / 84 D / 196 INACCESSIBLE / 325 SERVICE-NON-EXPOSÉ / 445 HORS-VERSION / 0 ABSENT / 229 ABI-DIFF / 9 AMBIGU / 0 E = 4 853.**

**Pool restant à examiner = 2 058** : 1 605 NULL + 75 STUB + 140 PARTIEL + 229 ABI-DIFF + 9 AMBIGU.


## AudioIn — alias historiques recroisés (23/11/2026)

Les commandes `audin:u` 1, 2, 5, 9, 12 et 13 correspondent en ID et signature aux handlers actifs `Start`, `Stop`, `GetReleasedAudioInBuffers`, `GetReleasedAudioInBuffersAuto`, `SetDeviceGain` et `GetDeviceGain`. Elles passent **ABI-DIFF → IMPL-SRC**. Les IDs 7/10 restent ABI-DIFF car l'ABI UAC de référence inclut un `NativeHandle` absent de la signature Encore.

**Compteur courant : 1 605 IMPL-SRC / 140 PARTIEL / 75 STUB / 146 NOOP / 1 605 NULL / 84 D / 196 INACCESSIBLE / 325 SERVICE-NON-EXPOSÉ / 445 HORS-VERSION / 0 ABSENT / 223 ABI-DIFF / 9 AMBIGU / 0 E = 4 853.**

**Pool restant à examiner = 2 052** : 1 605 NULL + 75 STUB + 140 PARTIEL + 223 ABI-DIFF + 9 AMBIGU.


## AudioOut — alias historiques recroisés (23/11/2026)

Les commandes `audout:u` 1, 2, 5 et 8 correspondent en ID et signature aux handlers actifs `Start`, `Stop`, `GetReleasedAudioOutBuffers` et `GetReleasedAudioOutBuffersAuto`. Elles passent **ABI-DIFF → IMPL-SRC**.

**Compteur courant : 1 609 IMPL-SRC / 140 PARTIEL / 75 STUB / 146 NOOP / 1 605 NULL / 84 D / 196 INACCESSIBLE / 325 SERVICE-NON-EXPOSÉ / 445 HORS-VERSION / 0 ABSENT / 219 ABI-DIFF / 9 AMBIGU / 0 E = 4 853.**

**Pool restant à examiner = 2 048** : 1 605 NULL + 75 STUB + 140 PARTIEL + 219 ABI-DIFF + 9 AMBIGU.


## HOS 23 — fermeture de quatre ABI historiques (23/11/2026)

Recroisement avec les dumps NS1 23.0.1 et les propriétaires actifs : `SPL` ID 1 `ExpMod` est l'alias historique de `ModularExponentiate` et passe **ABI-DIFF → IMPL-SRC**. `audren:u` ID 13 `GetAudioSystemMasterVolumeSetting`, `nvdrv` ID 13 `FinishInitialize` et `pl` ID 101 `RequestApplicationFunctionAuthorizationForSystem` sont des contrats historiques remplacés sur HOS 23 et passent **ABI-DIFF → HORS-VERSION**.

**Compteur courant : 1 610 IMPL-SRC / 140 PARTIEL / 75 STUB / 146 NOOP / 1 605 NULL / 84 D / 196 INACCESSIBLE / 325 SERVICE-NON-EXPOSÉ / 448 HORS-VERSION / 0 ABSENT / 215 ABI-DIFF / 9 AMBIGU / 0 E = 4 853.**

**Pool restant à examiner = 2 044** : 1 605 NULL + 75 STUB + 140 PARTIEL + 215 ABI-DIFF + 9 AMBIGU.


## HOS 23 — RO/HID/PDM historiques retirés du pool (23/11/2026)

Les dumps NS1 23.0.1 confirment la réaffectation des IDs de six anciennes commandes `ldr:ro`, de `hid:sys` 322/323 et des anciens PDM 7/13/16. Ces **11 lignes historiques** passent **ABI-DIFF → HORS-VERSION**. Les commandes HOS 23 qui occupent désormais ces IDs restent suivies séparément ; aucune implémentation runtime n'est inventée.

**Compteur courant : 1 610 IMPL-SRC / 140 PARTIEL / 75 STUB / 146 NOOP / 1 605 NULL / 84 D / 196 INACCESSIBLE / 325 SERVICE-NON-EXPOSÉ / 459 HORS-VERSION / 0 ABSENT / 204 ABI-DIFF / 9 AMBIGU / 0 E = 4 853.**

**Pool restant à examiner = 2 033** : 1 605 NULL + 75 STUB + 140 PARTIEL + 204 ABI-DIFF + 9 AMBIGU.


## Rattrapage compteur + HID debug fail-closed (23/11/2026)

Depuis le dernier compteur canonique à 2 033, les lots suivants ont été intégrés sur la branche secondaire : requalifications HOS23 WLAN/CLKRST/PCIe/Applet, lifecycle BTM pairing, handlers PM shell, puis rejet explicite de la surface HID debug non supportée. Le dernier couple runtime est moteur `56e9033f41079a26db2e2b626c2743f81fc74482` → vendor `0c533eecab77160f347c860e494db7a062ea9319`.

Pour `hid:dbg`, les 138 slots `nullptr` du propriétaire actif ont été remplacés par `RejectUnsupportedDebugCommand`, qui retourne `Kernel::ResultNotImplemented` même si `auto_stub` est activé. Les **85 lignes historiques** du catalogue qui correspondent à ces slots passent **NULL → D**. Il s'agit d'un rejet explicite de fonctions debug/dev non supportées, **pas** d'une implémentation HID debug.

**Compteur courant : 1 617 IMPL-SRC / 141 PARTIEL / 75 STUB / 145 NOOP / 1 513 NULL / 169 D / 196 INACCESSIBLE / 325 SERVICE-NON-EXPOSÉ / 473 HORS-VERSION / 0 ABSENT / 190 ABI-DIFF / 9 AMBIGU / 0 E = 4 853.**

**Pool restant à examiner = 1 928** : 1 513 NULL + 75 STUB + 141 PARTIEL + 190 ABI-DIFF + 9 AMBIGU.


## BTM debug + NS develop — surfaces non retail fail-closed (23/11/2026)

Vendor `3d3b80ecb9cbe6e5bd230a12460ec859d70f33f3` → moteur `4369aaba82949cc748528d95130e392d69e2614c`. Les 18 slots `nullptr` de `btm:dbg` et 19 slots `nullptr` de `ns:dev` sont désormais reliés à des handlers de rejet explicite `Kernel::ResultNotImplemented`, indépendants de `auto_stub`. Le catalogue historique contient 13 commandes `btm:dbg` et 12 commandes `ns:dev` correspondantes, soit **25 NULL → D**. Ce lot qualifie explicitement des fonctions debug/development non prises en charge ; il ne les implémente pas.

**Compteur courant : 1 617 IMPL-SRC / 141 PARTIEL / 75 STUB / 145 NOOP / 1 488 NULL / 194 D / 196 INACCESSIBLE / 325 SERVICE-NON-EXPOSÉ / 473 HORS-VERSION / 0 ABSENT / 190 ABI-DIFF / 9 AMBIGU / 0 E = 4 853.**

**Pool restant à examiner = 1 903** : 1 488 NULL + 75 STUB + 141 PARTIEL + 190 ABI-DIFF + 9 AMBIGU.


## Applet common — résolution logique raccordée (23/11/2026)

Couple moteur `b4a3615b1a71f68108382db3488f2bfc7dd8913b` → vendor `ab32ad62ded46a623e265e257b30d692baf9c53c`. `IAppletCommonFunctions::GetDisplayLogicalResolution` utilise désormais le même état docked/portable et les mêmes constantes `VI::DisplayResolution` que `ICommonStateGetter::GetDefaultDisplayResolution`. Le wire ABI HOS 23.0.1 (8 octets de sortie) est respecté. **1 NULL → IMPL-SRC**. Ce lot n'est pas encore validé sur PS5.

**Compteur courant : 1 622 IMPL-SRC / 141 PARTIEL / 75 STUB / 145 NOOP / 1 480 NULL / 197 D / 196 INACCESSIBLE / 325 SERVICE-NON-EXPOSÉ / 473 HORS-VERSION / 0 ABSENT / 190 ABI-DIFF / 9 AMBIGU / 0 E = 4 853.**

**Pool restant à examiner = 1 895** : 1 480 NULL + 75 STUB + 141 PARTIEL + 190 ABI-DIFF + 9 AMBIGU.


## Applet — thème + Capture-short synchronisés (23/11/2026)

Depuis le dernier compteur registre à 1 895, `ReadThemeStorage` et `WriteThemeStorage` ont été requalifiés **NULL → IMPL-SRC** car les handlers actifs manipulent réellement `Applet::theme_storage`. Le couple moteur `d30f3aaab2e6ca2165161d88384346ad756ebc26` → vendor `4ab4481d7572d3dd7589837f65b7baee5519d80d` ajoute ensuite le cmd18 `SetRequiresCaptureButtonShortPressedMessage` avec consommation réelle du flag dans `WindowSystem::SendButtonAppletMessageLocked`. Aucun de ces trois gains n'est encore qualifié sur PS5.

**Compteur courant : 1 625 IMPL-SRC / 141 PARTIEL / 75 STUB / 145 NOOP / 1 477 NULL / 197 D / 196 INACCESSIBLE / 325 SERVICE-NON-EXPOSÉ / 473 HORS-VERSION / 0 ABSENT / 190 ABI-DIFF / 9 AMBIGU / 0 E = 4 853.**

**Pool restant à examiner = 1 892** : 1 477 NULL + 75 STUB + 141 PARTIEL + 190 ABI-DIFF + 9 AMBIGU.


## NS/PCTL debug — surfaces fail-closed synchronisées (23/11/2026)

Le couple moteur `36fe443ac608d71f911ce164b86d645d30689d80` → vendor `8580856ac4ba06f7e83723f5e2eaed20ed68e200` contient désormais 7 rejets explicites NS debug et 8 rejets explicites PCTL debug. Ces commandes n'exécutent aucune action destructive ou état debug simulé ; elles renvoient `ResultUnknown` au runtime release au lieu de rester `nullptr`. Depuis le dernier compteur registre à 1 892, **15 NULL → D**.

**Compteur courant : 1 625 IMPL-SRC / 141 PARTIEL / 75 STUB / 145 NOOP / 1 462 NULL / 212 D / 196 INACCESSIBLE / 325 SERVICE-NON-EXPOSÉ / 473 HORS-VERSION / 0 ABSENT / 190 ABI-DIFF / 9 AMBIGU / 0 E = 4 853.**

**Pool restant à examiner = 1 877** : 1 462 NULL + 75 STUB + 141 PARTIEL + 190 ABI-DIFF + 9 AMBIGU.


## VI system display — requêtes de base raccordées (23/11/2026)

Vendor `e347b4949305f1f57de94713437218459697bee0` → gitlink moteur `b8879fd60961b285d3b52c428e5a788a7a76b795`. `ISystemDisplayService` cmd1200 `GetZOrderCountMin`, cmd1202 `GetZOrderCountMax` et cmd1203 `GetDisplayLogicalResolution` sont désormais des handlers actifs, avec ABI HOS 23.0.1 recroisée. Les bornes Z exposées sont 0/15 et la résolution logique réutilise `Settings::IsDockedMode()` + `VI::DisplayResolution`. **3 NULL → IMPL-SRC**. Position/taille/alpha restent ouverts car le compositor Encore ne stocke pas encore ces propriétés.

**Compteur courant : 1 628 IMPL-SRC / 141 PARTIEL / 75 STUB / 145 NOOP / 1 453 NULL / 218 D / 196 INACCESSIBLE / 325 SERVICE-NON-EXPOSÉ / 473 HORS-VERSION / 0 ABSENT / 190 ABI-DIFF / 9 AMBIGU / 0 E = 4 853.**

**Pool restant à examiner = 1 868** : 1 453 NULL + 75 STUB + 141 PARTIEL + 190 ABI-DIFF + 9 AMBIGU.


## NS Factory Reset — rejet explicite release (23/11/2026)

Vendor `4d8e9da8463ba452f6f3ab8b7119079e18a1c541` → gitlink moteur `7c021841caa80226534cb29bf48bd19e6b618b69`. Les 7 slots de `IFactoryResetInterface` sont désormais fail-closed. Les trois commandes présentes dans le catalogue historique (100–102) passent **NULL → D**. Aucun effacement de save/NAND ni reset de données hôte/PS5 n'est exécuté.

**Compteur courant : 1 628 IMPL-SRC / 141 PARTIEL / 75 STUB / 145 NOOP / 1 450 NULL / 221 D / 196 INACCESSIBLE / 325 SERVICE-NON-EXPOSÉ / 473 HORS-VERSION / 0 ABSENT / 190 ABI-DIFF / 9 AMBIGU / 0 E = 4 853.**

**Pool restant à examiner = 1 865** : 1 450 NULL + 75 STUB + 141 PARTIEL + 190 ABI-DIFF + 9 AMBIGU.


## AppletAE — surface debug/develop fail-closed (23/11/2026)

Vendor `4834515326ac41e679413970783baaf304fb5705` → gitlink moteur `e271ed8ef7d0dd1d9a4bf13d378051164f41ee5f`. Trois commandes debug/develop de `IAllSystemAppletProxiesService`, deux de `IHomeMenuFunctions`, et tous les slots de `IDebugFunctions` sont désormais explicitement rejetés sur le runtime release. **19 lignes du catalogue passent NULL → D**. Aucun comportement debug n'est simulé.

**Compteur courant : 1 628 IMPL-SRC / 141 PARTIEL / 75 STUB / 145 NOOP / 1 431 NULL / 240 D / 196 INACCESSIBLE / 325 SERVICE-NON-EXPOSÉ / 473 HORS-VERSION / 0 ABSENT / 190 ABI-DIFF / 9 AMBIGU / 0 E = 4 853.**

**Pool restant à examiner = 1 846** : 1 431 NULL + 75 STUB + 141 PARTIEL + 190 ABI-DIFF + 9 AMBIGU.


## AppletAE — commandes develop/debug résiduelles rejetées (23/11/2026)

Vendor `d1f92eee4c7557bd281ec481de521c178f0c6645` → gitlink moteur `e0990b2f7358c9dc622c1ca05d31286b13b5c03b`. `PopFloatingApplicationForDevelopment`, `GetDebugStorageChannel` et `BeginToObserveHidInputForDevelop` passent **NULL → D** via des handlers fail-closed actifs.

**Compteur courant : 1 628 IMPL-SRC / 141 PARTIEL / 75 STUB / 145 NOOP / 1 428 NULL / 243 D / 196 INACCESSIBLE / 325 SERVICE-NON-EXPOSÉ / 473 HORS-VERSION / 0 ABSENT / 190 ABI-DIFF / 9 AMBIGU / 0 E = 4 853.**

**Pool restant à examiner = 1 843** : 1 428 NULL + 75 STUB + 141 PARTIEL + 190 ABI-DIFF + 9 AMBIGU.


## AppletAE — derniers chemins capture/launch debug fail-closed (23/11/2026)

Vendor `fd389efbe1b51743aa630243fe00074f873dfb8a` → gitlink moteur `efc5f412feb680dc9ac462c3cd8dbd771a61dfdf`. Deux variantes `GetLaunchStorageInfoForDebug`, `RequestFlushGamePlayingMovieForDebug` et `StartContinuousRecordingFlushForDebug` passent **NULL → D** via des handlers actifs fail-closed.

**Compteur courant : 1 628 IMPL-SRC / 141 PARTIEL / 75 STUB / 145 NOOP / 1 424 NULL / 247 D / 196 INACCESSIBLE / 325 SERVICE-NON-EXPOSÉ / 473 HORS-VERSION / 0 ABSENT / 190 ABI-DIFF / 9 AMBIGU / 0 E = 4 853.**

**Pool restant à examiner = 1 839** : 1 424 NULL + 75 STUB + 141 PARTIEL + 190 ABI-DIFF + 9 AMBIGU.


## AppletAE — NotifyRunning raccordé au lifecycle réel (23/11/2026)

Vendor `4b8110b70ae05698b4c8db1354b87ff0c7b1f4a1` → gitlink moteur `3a72dfbae25c130f856da4c17992a76514d25157`. `NotifyRunning` met désormais `Applet::is_process_running` à jour sous verrou, renvoie si la transition vient d'avoir lieu et appelle `WindowSystem::RequestUpdate()`. Cet état est consommé par le calcul de visibilité, focus et input. **1 STUB → IMPL-SRC**.

**Compteur courant : 1 629 IMPL-SRC / 141 PARTIEL / 74 STUB / 145 NOOP / 1 424 NULL / 247 D / 196 INACCESSIBLE / 325 SERVICE-NON-EXPOSÉ / 473 HORS-VERSION / 0 ABSENT / 190 ABI-DIFF / 9 AMBIGU / 0 E = 4 853.**

**Pool restant à examiner = 1 838** : 1 424 NULL + 74 STUB + 141 PARTIEL + 190 ABI-DIFF + 9 AMBIGU.


## AppletAE — capacités écran PS5 qualifiées (23/11/2026)

Vendor `3e8effa0b3dc8184d46228e8bc82fa7c626d08bb` → gitlink moteur `1bb6cfcb49ea4af12095eafd312f9ab38e83bb5c`. `SetLcdBacklighOffEnabled` conserve le flag invité mais est explicitement qualifié **NOOP matériel PS5** ; `IsIlluminanceAvailable` retourne `false` comme capacité réelle car aucun capteur ambiant n'est exposé. Avec `NotifyRunning` déjà raccordé, le bloc Applet retire trois STUB au total.

**Compteur courant : 1 630 IMPL-SRC / 141 PARTIEL / 72 STUB / 146 NOOP / 1 424 NULL / 247 D / 196 INACCESSIBLE / 325 SERVICE-NON-EXPOSÉ / 473 HORS-VERSION / 0 ABSENT / 190 ABI-DIFF / 9 AMBIGU / 0 E = 4 853.**

**Pool restant à examiner = 1 836** : 1 424 NULL + 72 STUB + 141 PARTIEL + 190 ABI-DIFF + 9 AMBIGU.


## Lot rapide STUB — ACC / AOC / miiimg (23/11/2026)

Vendor `d527dc85bf42ec57f150fd02c6612c86042ff0bb` → gitlink moteur `d210bcd07be4a7468c35d0790d05dd50cc9d9937`. Les chemins actifs CMake ont été vérifiés : ACC utilise l'overlay backport ; AOC et `miiimg` utilisent les sources Eden de base. **7 STUB sortent du pool : 4 → IMPL-SRC, 3 → NOOP.** Aucun backend Nintendo Account/eShop n'est inventé ; les pop AOC restent fail-closed avec `ResultNoPurchasedProductInfoAvailable`, et la base d'images Mii reste explicitement vide. Pas de validation PS5 revendiquée.

**Compteur courant : 1 634 IMPL-SRC / 141 PARTIEL / 65 STUB / 149 NOOP / 1 424 NULL / 247 D / 196 INACCESSIBLE / 325 SERVICE-NON-EXPOSÉ / 473 HORS-VERSION / 0 ABSENT / 190 ABI-DIFF / 9 AMBIGU / 0 E = 4 853.**

**Pool restant à examiner = 1 829** : 1 424 NULL + 65 STUB + 141 PARTIEL + 190 ABI-DIFF + 9 AMBIGU.


## AppletAE — politique idle invitée neutralisée côté PS5 (23/11/2026)

Vendor `55be5734cb4f820eebfb05e43449b45b7bdf23ad` → gitlink moteur `e9228efbfae8534713604b78d64c566f08d2fb64`. `LoadAndApplyIdlePolicySettings`, `OverrideAutoSleepTimeAndDimmingTime` et `ReportUserIsActive` ne sont plus présentés comme des effets Horizon simulés : Encore n'expose pas de scheduler invité `idle:sys` et ne transmet pas ces politiques de veille/atténuation au système PS5 hôte. **3 STUB → NOOP**. Le changement est limité aux chemins actifs et à l'overlay `self_controller` avec manifeste régénéré ; aucune validation PS5 n'est revendiquée.

**Compteur courant : 1 634 IMPL-SRC / 141 PARTIEL / 62 STUB / 152 NOOP / 1 424 NULL / 247 D / 196 INACCESSIBLE / 325 SERVICE-NON-EXPOSÉ / 473 HORS-VERSION / 0 ABSENT / 190 ABI-DIFF / 9 AMBIGU / 0 E = 4 853.**

**Pool restant à examiner = 1 826** : 1 424 NULL + 62 STUB + 141 PARTIEL + 190 ABI-DIFF + 9 AMBIGU.


## AppletAE — gameplay recording non exposé (23/11/2026)

Vendor `06ce1025d8f1e2a6074527b35e54acc7d3570699` → gitlink moteur `d576d3e7f746c3bf4dcef7352dda4278d358e6b4`. `InitializeGamePlayRecording` passe de **STUB → NOOP** : la capacité d'enregistrement reste désactivée sans backend Horizon, et la commande conserve le succès attendu par les titres qui l'appellent sans mapper le transfer-memory vers un backend PS5 fictif. Pas de validation console revendiquée.

**Compteur courant : 1 634 IMPL-SRC / 141 PARTIEL / 61 STUB / 153 NOOP / 1 424 NULL / 247 D / 196 INACCESSIBLE / 325 SERVICE-NON-EXPOSÉ / 473 HORS-VERSION / 0 ABSENT / 190 ABI-DIFF / 9 AMBIGU / 0 E = 4 853.**

**Pool restant à examiner = 1 825** : 1 424 NULL + 61 STUB + 141 PARTIEL + 190 ABI-DIFF + 9 AMBIGU.


## BSD — Select réel + réparation Read + borne FD (23/11/2026)

Vendor `77ec007d1b9cc66487cc6bbf94a1a9231d2b4117` (inclut `8cf1727e6ce48acf1d3d36ffa580c2542df2b2af`) → gitlink moteur `441e5741343e0e77c0277ddb7f6f86881d98973c`. Le propriétaire actif `encore-active/eden-core/src/core/hle/service/sockets/bsd.cpp` a été modifié directement. `Select` n'est plus un succès zéro : ABI 0x20, fd_sets read/write/except, timeout, `BADF/EINVAL`, poll réel et sortie des bits prêts. Deux bornes `> MAX_FD` deviennent `>= MAX_FD`, supprimant l'index hors limites `file_descriptors[128]`. Enfin `Read`, déjà classé IMPL-SRC mais perdu dans le chemin CMake actif, est restauré avec `RecvImpl(fd, 0)` et une copie limitée à `ret` octets. **Baisse du pool : 1 seulement**, `Read` étant déjà comptabilisé comme implémenté. Aucun résultat PS5 n'est revendiqué.

**Compteur courant : 1 635 IMPL-SRC / 141 PARTIEL / 60 STUB / 153 NOOP / 1 424 NULL / 247 D / 196 INACCESSIBLE / 325 SERVICE-NON-EXPOSÉ / 473 HORS-VERSION / 0 ABSENT / 190 ABI-DIFF / 9 AMBIGU / 0 E = 4 853.**

**Pool restant à examiner = 1 824** : 1 424 NULL + 60 STUB + 141 PARTIEL + 190 ABI-DIFF + 9 AMBIGU.


## ACC — cycle d'inscription utilisateur local (23/11/2026)

Vendor `90bf581546e467daf19ac091cb301c5271df3f94` → gitlink moteur `2fded1df7b7c0f3f1e49bc85183e9bfaf4f48568`. Cmd202 et cmd206 utilisent l'UUID 0x10 confirmé par les dumps NS1 22.5/23.0.1. Un état `pending_registration_user` empêche `CancelUserRegistration` de supprimer un utilisateur déjà enregistré : seule l'inscription provisoire créée par cmd200 peut être annulée. Cmd206 réutilise la persistance du chemin normal, Encore ne modélisant pas les restrictions qu'il contourne sur Horizon. **2 NULL → IMPL-SRC**. Les équivalents `acc:e` sont raccordés pour le runtime moderne sans modifier le compteur distinct. Pas de validation PS5 revendiquée.

**Compteur courant : 1 637 IMPL-SRC / 141 PARTIEL / 60 STUB / 153 NOOP / 1 422 NULL / 247 D / 196 INACCESSIBLE / 325 SERVICE-NON-EXPOSÉ / 473 HORS-VERSION / 0 ABSENT / 190 ABI-DIFF / 9 AMBIGU / 0 E = 4 853.**

**Pool restant à examiner = 1 822** : 1 422 NULL + 60 STUB + 141 PARTIEL + 190 ABI-DIFF + 9 AMBIGU.


## AppletAE — releases des buffers de capture legacy (23/11/2026)

Vendor `f48b517270481dffb1a47a8e76c68035b73baedf` → gitlink moteur `52973e885b296e55a1615dab463f511289172aa5`. Cmd11/13/15 sont confirmées sans entrée/sortie dans les dumps NS1 22.5/23.0.1. Le backend Encore capture les snapshots de façon synchrone et ne garde aucun ownership après retour ; les releases legacy sont donc des handlers explicites cohérents avec 23/25/27. Les acquisitions avec handles restent ouvertes. **3 NULL → IMPL-SRC.** Pas de validation PS5 revendiquée.

**Compteur courant : 1 640 IMPL-SRC / 141 PARTIEL / 60 STUB / 153 NOOP / 1 419 NULL / 247 D / 196 INACCESSIBLE / 325 SERVICE-NON-EXPOSÉ / 473 HORS-VERSION / 0 ABSENT / 190 ABI-DIFF / 9 AMBIGU / 0 E = 4 853.**

**Pool restant à examiner = 1 819** : 1 419 NULL + 60 STUB + 141 PARTIEL + 190 ABI-DIFF + 9 AMBIGU.


## LDN system — backend LANDiscovery partagé (23/11/2026)

Vendor `1d8b6c8ad8ba3ac57c0e17a827afd3e86fb74b22` → gitlink moteur `9322d949c9fcfc0ecdb00e6609eed4d06c2c6d88`. **22 NULL → IMPL-SRC** sur `ldn:s` : GetState/NetworkInfo/IPv4/disconnect/security/config, event + latest update + scans, AP/station, create/destroy network, advertise, connect/disconnect et initialize/finalize utilisent le backend `LANDiscovery` déjà actif pour `ldn:u`. Les huit commandes à sémantique distincte/non prouvée restent ouvertes. Pas de validation PS5 revendiquée.

**Compteur courant : 1 662 IMPL-SRC / 141 PARTIEL / 60 STUB / 153 NOOP / 1 397 NULL / 247 D / 196 INACCESSIBLE / 325 SERVICE-NON-EXPOSÉ / 473 HORS-VERSION / 0 ABSENT / 190 ABI-DIFF / 9 AMBIGU / 0 E = 4 853.**

**Pool restant à examiner = 1 797** : 1 397 NULL + 60 STUB + 141 PARTIEL + 190 ABI-DIFF + 9 AMBIGU.


## Lot accéléré HID + Applet self-controller + PCTL (23/11/2026)

Vendor `5f548ff51dcc14a71758944a35476e26fec2916e` → `7ce1c67ccaaa5a1e75d9f129ad9ae2234e000fae` → `1c9bc1840eb211b86aeaec7d648bcbbd96206b26`, gitlink moteur `be89a76a42f3820e29554db1161c66230b80256c`. Le lot ferme **8 NULL HID** (accéléromètre + force de fusion SevenSixAxis), **6 NULL + 1 STUB AppletAE** (états input/illumination/WLAN + notifications hôte), puis **14 NULL PCTL** (permissions, reset, disable/enable, unlock, notifications et unlink). Les no-op retenus correspondent uniquement à des notifications/politiques sans backend Horizon sur PS5 ; les getters/setters conservent un état local explicite. Le commit LDN concurrent `1d8b6c8a` est préservé. Pas de validation console PS5 revendiquée.

**Compteur courant : 1 685 IMPL-SRC / 141 PARTIEL / 59 STUB / 159 NOOP / 1 369 NULL / 247 D / 196 INACCESSIBLE / 325 SERVICE-NON-EXPOSÉ / 473 HORS-VERSION / 0 ABSENT / 190 ABI-DIFF / 9 AMBIGU / 0 E = 4 853.**

**Pool restant à examiner = 1 768** : 1 369 NULL + 59 STUB + 141 PARTIEL + 190 ABI-DIFF + 9 AMBIGU.


## NS system update — notifications locales sans firmware hôte (23/11/2026)

Vendor `1effcd1413a458f58db476d6ffd37c63c7550eee` → gitlink moteur `dfffa79e463e189866c90e4bece6d29c4b904428`. **8 NULL sortent du pool** : sept notifications/commandes de coordination deviennent des no-op explicites car Encore ne doit jamais piloter une mise à jour firmware de la PS5 ; `NotifySystemUpdateForContentDelivery` signale réellement l'événement déjà retourné par cmd9. Les commandes 17/18 de transfert/progression restent ouvertes plutôt que de simuler un transfert inexistant. Pas de validation PS5 revendiquée.

**Compteur courant : 1 686 IMPL-SRC / 141 PARTIEL / 59 STUB / 166 NOOP / 1 361 NULL / 247 D / 196 INACCESSIBLE / 325 SERVICE-NON-EXPOSÉ / 473 HORS-VERSION / 0 ABSENT / 190 ABI-DIFF / 9 AMBIGU / 0 E = 4 853.**

**Pool restant à examiner = 1 760** : 1 361 NULL + 59 STUB + 141 PARTIEL + 190 ABI-DIFF + 9 AMBIGU.


## MiiImg + NPNS + Friend — état local/offline (23/11/2026)

Vendor `6eae21258ac6bae5db93c4b7d70935c5f9eaa032` → gitlink moteur `0f2f00236fd7ce2e8f8a33c824caac30d4810abd`. **8 NULL sortent du pool** : 3 MiiImg, 2 NPNS user et 3 préférences Friend. Les ABI MiiImg sont celles de libnx ; les trois commandes Friend ont une entrée 0x18 confirmée sur NS1 22.5/23.0.1. L'état Friend est conservé en mémoire par UUID et reflété dans `LoadUserSetting`. Pas de validation console PS5 revendiquée.

**Compteur courant : 1 692 IMPL-SRC / 141 PARTIEL / 59 STUB / 168 NOOP / 1 353 NULL / 247 D / 196 INACCESSIBLE / 325 SERVICE-NON-EXPOSÉ / 473 HORS-VERSION / 0 ABSENT / 190 ABI-DIFF / 9 AMBIGU / 0 E = 4 853.**

**Pool restant à examiner = 1 752** : 1 353 NULL + 59 STUB + 141 PARTIEL + 190 ABI-DIFF + 9 AMBIGU.


## PREPO — état local et transport offline (23/11/2026)

Vendor `7b75ebb71f440f046f7f3e1819435de43e58f87d` → gitlink moteur `8ae25ce272ea89a05f6aa5ea85be691c3f46da59`. **12 handlers runtime ajoutés, 9 entrées de catalogue sorties du pool** : 7 IMPL-SRC + 2 NOOP. L'usage/statistiques/throughput/upload reflètent l'absence de transport Nintendo ; les fichiers `Core::Reporter` restent des diagnostics hôte et ne sont pas assimilés au stockage PREPO invité. Pas de validation console PS5 revendiquée.

**Compteur courant : 1 699 IMPL-SRC / 141 PARTIEL / 59 STUB / 170 NOOP / 1 344 NULL / 247 D / 196 INACCESSIBLE / 325 SERVICE-NON-EXPOSÉ / 473 HORS-VERSION / 0 ABSENT / 190 ABI-DIFF / 9 AMBIGU / 0 E = 4 853.**

**Pool restant à examiner = 1 743** : 1 344 NULL + 59 STUB + 141 PARTIEL + 190 ABI-DIFF + 9 AMBIGU.


## CLKRST — état module clock/reset/power (23/11/2026)

Vendor `41446c0476dc0b6b5aa9091c8d9b022d215679ea` → gitlink moteur `aaa0a4d94c3251565b6b953d9b90ed9cdc2e99d8`. **12 NULL → IMPL-SRC** : six toggles clock/reset/power, `GetState` 0xC, min-V clock, possible clock rates, DVFS table, température et seuils. ABI vérifiée sur le dump PCV NS1 23.0.1 ; aucune tension Switch fictive n'est fabriquée. Pas de validation console PS5 revendiquée.

**Compteur courant : 1 711 IMPL-SRC / 141 PARTIEL / 59 STUB / 170 NOOP / 1 332 NULL / 247 D / 196 INACCESSIBLE / 325 SERVICE-NON-EXPOSÉ / 473 HORS-VERSION / 0 ABSENT / 190 ABI-DIFF / 9 AMBIGU / 0 E = 4 853.**

**Pool restant à examiner = 1 731** : 1 332 NULL + 59 STUB + 141 PARTIEL + 190 ABI-DIFF + 9 AMBIGU.


## BSDCFG — contrôle réseau hôte neutralisé (23/11/2026)

Vendor `0264621817f4d7e2a98c2a123194e9eebbbf7efd` → gitlink moteur `23446811296ebff339f8e1b7219521b421646691`. **13 NULL → NOOP** : SetIfUp/Down, CancelIf, GetIfState, DhcpRenew et opérations ARP 6-12 répondent avec une IPC valide sans modifier l'interface réseau de la PS5. ABI recroisée sur le dump Sockets NS1 23.0.1. Pas de validation console PS5 revendiquée.

**Compteur courant : 1 711 IMPL-SRC / 141 PARTIEL / 59 STUB / 183 NOOP / 1 319 NULL / 247 D / 196 INACCESSIBLE / 325 SERVICE-NON-EXPOSÉ / 473 HORS-VERSION / 0 ABSENT / 190 ABI-DIFF / 9 AMBIGU / 0 E = 4 853.**

**Pool restant à examiner = 1 718** : 1 319 NULL + 59 STUB + 141 PARTIEL + 190 ABI-DIFF + 9 AMBIGU.


## LDN — politiques simples + InitializeSystem2 (23/11/2026)

Vendor `beb30c7a2de729e582472c106abe03f50cc01542` → gitlink moteur `b7cf2d189392b069514492043a35de960630d073`. **10 entrées sortent du pool** : cmd104/207/208/209 côté `ldn:u` et `ldn:s` deviennent des NOOP de compatibilité documentés, cmd402 système devient NOOP, et cmd403 système devient IMPL-SRC avec ABI version+PID réelle. `Reject` et `ConnectPrivate` restent ouverts. Pas de validation console revendiquée.

**Compteur courant : 1 712 IMPL-SRC / 141 PARTIEL / 52 STUB / 192 NOOP / 1 316 NULL / 247 D / 196 INACCESSIBLE / 325 SERVICE-NON-EXPOSÉ / 473 HORS-VERSION / 0 ABSENT / 190 ABI-DIFF / 9 AMBIGU / 0 E = 4 853.**

**Pool restant à examiner = 1 708** : 1 316 NULL + 52 STUB + 141 PARTIEL + 190 ABI-DIFF + 9 AMBIGU.


## CAPS:C — stockage album + registre ARUID/ApplicationId (23/11/2026)

Vendor `9c8dd143c5fd54dd51c88e96d15a8e4cba8f8674` → gitlink moteur `cc0cd9f042f41ce77a05988f0770879243cd1b6d`. **5 NULL → IMPL-SRC** : notifications de disponibilité stockage, registration/unregistration ARUID et lookup ApplicationId. Les ABI sont celles du dump NS1 23.0.1/libnx. Cmd2014 reste ouvert. Pas de validation console revendiquée.

**Compteur courant : 1 717 IMPL-SRC / 141 PARTIEL / 52 STUB / 192 NOOP / 1 311 NULL / 247 D / 196 INACCESSIBLE / 325 SERVICE-NON-EXPOSÉ / 473 HORS-VERSION / 0 ABSENT / 190 ABI-DIFF / 9 AMBIGU / 0 E = 4 853.**

**Pool restant à examiner = 1 703** : 1 311 NULL + 52 STUB + 141 PARTIEL + 190 ABI-DIFF + 9 AMBIGU.


## CAPS:A — wrappers AlbumManager (23/11/2026)

Vendor `486fd09dcd10c3c59c85bc67024b09d19e6f5d19` (inclut `7428d50144fe527fe136211823491dd82e40156b`) → gitlink moteur `9c1df636ca461b59a6f845779169d506c29d8790`. **11 NULL → IMPL-SRC** : fonctions de comptage/taille/montage/cache et chargement screenshot/thumbnail réutilisent le backend AlbumManager existant. Pas de validation console revendiquée.

**Compteur courant : 1 728 IMPL-SRC / 141 PARTIEL / 52 STUB / 192 NOOP / 1 300 NULL / 247 D / 196 INACCESSIBLE / 325 SERVICE-NON-EXPOSÉ / 473 HORS-VERSION / 0 ABSENT / 190 ABI-DIFF / 9 AMBIGU / 0 E = 4 853.**

**Pool restant à examiner = 1 692** : 1 300 NULL + 52 STUB + 141 PARTIEL + 190 ABI-DIFF + 9 AMBIGU.


## CAPS:A — fin des wrappers déterministes (23/11/2026)

Vendor `bdab8fc1a8d31305f63412305d577011d07cf3fe` → gitlink moteur `6c99a252ab483565883746b0c163e362698e42e9`. **2 NULL → IMPL-SRC** : `LoadAlbumScreenShotImageEx0` et `GetRequiredStorageSpaceSizeToCopyAll`. Les ABI sont recroisées libnx/dump NS1 23.0.1 ; Usage/Cache restent ouverts plutôt que d'inventer les champs inconnus. Pas de validation console revendiquée.

**Compteur courant : 1 730 IMPL-SRC / 141 PARTIEL / 52 STUB / 192 NOOP / 1 298 NULL / 247 D / 196 INACCESSIBLE / 325 SERVICE-NON-EXPOSÉ / 473 HORS-VERSION / 0 ABSENT / 190 ABI-DIFF / 9 AMBIGU / 0 E = 4 853.**

**Pool restant à examiner = 1 690** : 1 298 NULL + 52 STUB + 141 PARTIEL + 190 ABI-DIFF + 9 AMBIGU.


## NPNS — commandes locales offline (23/11/2026)

Vendor `1bbeb625af292945d60f98e91c4fc55a9ee4f4e0` → gitlink moteur `ed3e7c9a12a464061dd433f640b5e72a330501a7`. **10 NULL sortent du pool** sur `npns:u/s` : deux événements d'état réels et huit commandes de souscription/suspend/resume documentées comme no-op offline. Les commandes token restent ouvertes car leur payload 0x28 n'est pas simulé. Pas de validation console revendiquée.

**Compteur courant : 1 732 IMPL-SRC / 141 PARTIEL / 52 STUB / 200 NOOP / 1 288 NULL / 247 D / 196 INACCESSIBLE / 325 SERVICE-NON-EXPOSÉ / 473 HORS-VERSION / 0 ABSENT / 190 ABI-DIFF / 9 AMBIGU / 0 E = 4 853.**

**Pool restant à examiner = 1 680** : 1 288 NULL + 52 STUB + 141 PARTIEL + 190 ABI-DIFF + 9 AMBIGU.


## NPNS — topics offline + handover (23/11/2026)

Vendor `3cda4d41066c22a4873019206b1f5e2da139892e` → gitlink moteur `1dbb774b0d226f16e0b50621a93dfc6f04098525`. **9 entrées du catalogue sortent du pool** : six variantes handover réellement raccordées et trois commandes topic/offline documentées. Deux handlers account 18.0+ ont aussi été ajoutés en C++ mais ne sont pas présents dans le catalogue, donc pas comptés. Pas de validation console revendiquée.

**Compteur courant : 1 738 IMPL-SRC / 141 PARTIEL / 52 STUB / 203 NOOP / 1 279 NULL / 247 D / 196 INACCESSIBLE / 325 SERVICE-NON-EXPOSÉ / 473 HORS-VERSION / 0 ABSENT / 190 ABI-DIFF / 9 AMBIGU / 0 E = 4 853.**

**Pool restant à examiner = 1 671** : 1 279 NULL + 52 STUB + 141 PARTIEL + 190 ABI-DIFF + 9 AMBIGU.


## LDN + FSP — batch runtime direct (23/11/2026)

Vendor `98ea6932ee52d0c7b6ad4de5776a05df3316f32d` → gitlink moteur `8e2cbafa5992d7eecd9cac2694c93375a23dd97a`. Deux `Reject` LDN sont raccordés avec ABI `u32 node_id` et comportement offline no-op documenté. FSP gagne les ouvertures BIS filesystem/storage, GameCard filesystem, image directory et content storage via les backends déjà actifs. `OpenGameCardStorage` ouvre Normal/Secure raw mais reste PARTIEL faute de racine write-only dans le modèle XCI read-only. **8 NULL reclassés, baisse nette du pool = 7.** Aucun build PS5 ni résultat gameplay n'est revendiqué.

**Compteur courant : 1 743 IMPL-SRC / 142 PARTIEL / 52 STUB / 205 NOOP / 1 271 NULL / 247 D / 196 INACCESSIBLE / 325 SERVICE-NON-EXPOSÉ / 473 HORS-VERSION / 0 ABSENT / 190 ABI-DIFF / 9 AMBIGU / 0 E = 4 853.**

**Pool restant à examiner = 1 664** : 1 271 NULL + 52 STUB + 142 PARTIEL + 190 ABI-DIFF + 9 AMBIGU.


## CAPS — album application wrappers (23/11/2026)

Vendor `71ead3c34a782580ad52770fbfbcb87de83da416` → gitlink moteur `d3ef1ddd30f0570bb75285b0f216d58c409062a2`. Les wrappers caps:u 103/104/105/110/120/140/141/143 utilisent désormais AlbumManager ; caps:c 2014 vérifie la table d'applications enregistrées avec le code officiel ControlNotOpened (2206-822). **9 NULL reclassés : 4 IMPL-SRC + 5 PARTIEL ; baisse nette du pool = 4.** Aucun build PS5 ni résultat console revendiqué.

**Compteur courant : 1 747 IMPL-SRC / 147 PARTIEL / 52 STUB / 205 NOOP / 1 262 NULL / 247 D / 196 INACCESSIBLE / 325 SERVICE-NON-EXPOSÉ / 473 HORS-VERSION / 0 ABSENT / 190 ABI-DIFF / 9 AMBIGU / 0 E = 4 853.**

**Pool restant à examiner = 1 660** : 1 262 NULL + 52 STUB + 147 PARTIEL + 190 ABI-DIFF + 9 AMBIGU.


## NPNS — lot runtime offline (24/11/2026)

Vendor `487fcd316fc8c63d95c97b40d1b4b8438508092a` → moteur `72b761e16280ccee6362dc72afd035bb93dc7d19`. **12 NULL → IMPL-SRC** : token lifecycle `npns:u` (21/23/25), `npns:s` (21/22/23/24/25), statistiques cmd104 des deux services, event cmd105 système et transition d'état cmd202. Le token est local/opaque et n'authentifie aucun service Nintendo ; les commandes BaaS restent ouvertes. **Pool restant = 1 648** (1 250 NULL + 52 STUB + 147 PARTIEL + 190 ABI-DIFF + 9 AMBIGU).


## NSD — lot environnement/test (24/11/2026)

Vendor `a8927dbd3cf2840021a8adee1f42d701a001c564`. **6 NULL sortent du pool** : cmd63 → IMPL-SRC, cmd51/52/60/61/62 → D car déjà raccordées au rejet explicite production. **Pool restant = 1 642** (1 244 NULL + 52 STUB + 147 PARTIEL + 190 ABI-DIFF + 9 AMBIGU).


## BTM utilisateur — contrat BLE sans radio invitée (24/11/2026)

Vendor `5c16e26b1c6ff11145e47a0e7a810eb76d0541a4`. ABI vérifiée avec libnx btmu.c et btdrv_types.h. **8 NULL sortent du pool** : cmd5/10/20/21/25 → IMPL-SRC (listes vides cohérentes avec le backend BLE invité absent et événement pairing dédié) ; cmd4/7/9 → NOOP (arrêt idempotent d'un scan inactif). Les opérations radio, pairing et GATT restent ouvertes. En parallèle NSD corrige l'initialisation du tampon ResolveEx et le nombre de mots de réponse du setter. Aucun résultat console revendiqué.

**Pool restant = 1 634** (1 236 NULL + 52 STUB + 147 PARTIEL + 190 ABI-DIFF + 9 AMBIGU).


## NPNS — correction de compilation du lot token (24/11/2026)

Vendor `dd88a95f547dd1fa7f7a2536a41846d73203b213` : les trois handlers `CreateToken`, `DestroyToken`, `QueryIsTokenValid` destinés à `INpnsUser` étaient dupliqués dans `INpnsSystem`, alors que la table utilisateur les référençait. Déplacement des trois définitions vers leur propriétaire réel, sans changement ABI ni nouveau succès factice. Le TU `npns.cpp` est sélectionné par le CMake backports sans overlay manifeste. Vérification structurelle des trois méthodes par classe ; compilation native non effectuée. Le manifeste HID corrigé (`67f68874018169305ebdd44ea06dd32855cb3667`) et ce nouveau vendor sont autorisés par SHA et arbre exact dans le garde SSBO, sans retrait des contrôles de blobs GPU.

**Pool restant inchangé = 1 634** (1 236 NULL + 52 STUB + 147 PARTIEL + 190 ABI-DIFF + 9 AMBIGU).


## NPNS — ABI ListenTo et variantes firmware historiques (24/11/2026)

Vendor `c6e0b135e0aa565fe596298971c7e38add0ca3d3` : les deux handlers `ListenTo` (cmd2 `npns:u/s`) prennent désormais un `u64` ProgramId conforme à [SwIPC](https://reswitched.github.io/SwIPC/ifaces.html) (8 octets) et au [correctif Lichii](https://git.nite07.com/nite/Lichii/commit/8f933d5d99720d63665f5d63512331e26550f6e2?files=src). Le comportement offline NOOP demeure inchangé. En outre, deux lignes du catalogue sont reclassées NULL → HORS-VERSION (et non IMPL-SRC) : `QueryIsTopicExist` cmd13, HOS 1.0.0–17.0.1 ; `SetBaasDeviceAccountIdList` cmd34, HOS 7.0.0–19.0.1, selon [SwitchBrew](https://switchbrew.org/wiki/NPNS_services). Le catalogue garde les lignes historiques. Pas de build PS5 ni validation console.

**Pool restant = 1 632** (1 234 NULL + 52 STUB + 147 PARTIEL + 190 ABI-DIFF + 9 AMBIGU). Baisse de deux entrées par qualification firmware, aucune nouvelle implémentation comptabilisée.


## NS debug + audren notification NX — lot natif (24/11/2026)

Vendor `44160f78fda728f3720cbad26bcd56fe41dd41aa` : la CI [#45305528479](https://github.com/niakw/ProsperoEden-Encore/actions/runs/45305528479) franchit désormais le garde SSBO, puis échoue sur le hash upstream de `ns.cpp`. Les deux rejets debug (`pdm:ntfy` cmd5, `ns:vm` cmd1201) sont transférés dans l'overlay natif maintenu en préservant les changements existants (notamment les limites de sessions). La copie source upstream retrouve son blob original dont le SHA-256 correspond au manifeste ; hash actif et taille recalculés. Deux lignes NULL → D, pas de fausse implémentation. Vendor `ffb2182af7f137179cd2f68792d4b00c2a54cef5` : `IAudioDevice` cmd15–18 (acquire/release input/output notification) sont raccordées à un rejet explicite `Audio::ResultNotSupported`, avec ABI u64 et type de handle des acquires, conformément au comportement d'échec NX documenté dans [SwitchBrew Audio services](https://switchbrew.org/wiki/Audio_services). Code d'erreur exact Horizon non établi. Ces quatre commandes récentes ne figurent pas dans le catalogue historique et ne sont pas ajoutées au compteur. Le CMake liste `audio_device.cpp/.h` et aucun overlay backports ne les remplace. Pas de build PS5, validation console ou verdict CI du nouveau couple revendiqués.

**Pool restant = 1 630** (1 232 NULL + 52 STUB + 147 PARTIEL + 190 ABI-DIFF + 9 AMBIGU).


## HID — événements clavier lock et ABI (24/11/2026)

Vendor `be709442d734683ffd9725c7035a932a73bf5c87` : `hid` cmd32 (STUB) et `hid:sys` cmd31 (NULL) utilisent désormais `EmulatedDevices::ApplyKeyboardLockKeyEvents`, qui modifie sous le mutex existant les valeurs Num/Caps/Scroll Lock et leur `KeyboardModifier` réellement consommé par le sampler de mémoire partagée. Notification frontend après libération du verrou, seulement si changement. Les neuf bits On/Off/Toggle sont ceux de [libnx hid.h](https://github.com/switchbrew/libnx/blob/master/nx/include/switch/services/hid.h). Le contrat public `hid` prend le u32 + AppletResourceUserId/PID, `hid:sys` le u32 seul, selon [libnx hid.c](https://github.com/switchbrew/libnx/blob/master/nx/source/services/hid.c) et [SwitchBrew HID](https://switchbrew.org/wiki/HID_services). Correction appliquée aux deux propriétaires `hid_server` dont le propriétaire partagé réellement choisi par CMake, plus `hid_system_server` maintenu. La LED physique hôte n'est pas pilotée et aucun comportement de bouton système n'est inventé. Le digest de l'overlay HID est recalculé. Pas de validation de compilation native ou console revendiquée.

**Pool restant = 1 628** (1 231 NULL + 51 STUB + 147 PARTIEL + 190 ABI-DIFF + 9 AMBIGU).


### 2026-11-24 — PM provenance correction

- Vendor `4534ccde306a715d0fe61698be23522ac5b2d44e`: PM active overlay already contained the reviewed runtime changes; corrected its manifest SHA-256 and byte size (12308). No new runtime coverage credited.
- Remaining: **1628**. Six AM baseline/overlay provenance mismatches remain under review; do not change upstream digests to hide them.
- No native PS5 build or console validation performed.

### 2026-11-24 — AM : transfert des handlers vers les propriétaires maintenus

Vendor `fd43ea21e70e2f16a76d7723b4578813cb28468c` : six fichiers upstream AM restaurés à leurs SHA-256 originaux du manifeste, sans modifier les empreintes upstream. Sept fichiers backports actifs reçoivent les changements existants (IApplicationFunctions cmd124/170, ILibraryAppletSelfAccessor cmd80/101/102, IOverlayFunctions cmd3/6/30, ICommonStateGetter cmd7/40/64). Le header commun de ICommonStateGetter reste fourni par sources/eden ; les deux copies maintenues de application_functions.cpp sont cohérentes pour les commandes transférées. Les rejets debug et correctifs lifecycle précédents sont conservés. Empreintes actives et tailles recalculées pour les sept fichiers. Les 11 commandes avaient déjà été comptabilisées ; **pool inchangé = 1 628**. Qualification statique du transfert et des empreintes ; compilation native et console non validées.

### 2026-11-24 — AM : annulation CPU boost, rejets legacy et réconciliation du catalogue

Vendor `bdb10101b495c52d14a4afe17a30d52fcbcf32d6` : ICommonStateGetter cmd67 restaure le mode Normal via le contrôleur APM existant ; cmd2/3/4 et IGlobalStateController cmd0/1 retournent une erreur explicite (code exact Horizon non établi) conformément à [SwitchBrew AM](https://switchbrew.org/wiki/AM_services). Pas de faux succès ni modification de la politique hôte. Les cinq commandes étaient déjà classées D et cmd67 est hors du catalogue historique. Le catalogue a ensuite été revérifié ligne par ligne : contrairement à la note précédente, 18 commandes AM de lots déjà committés y restaient NULL, dont les 11 du transfert. Elles passent à 5 IMPL-SRC, 5 NOOP, 7 PARTIEL et 1 STUB, selon leur comportement réel. **Pool restant = 1 618** (1 213 NULL + 52 STUB + 154 PARTIEL + 190 ABI-DIFF + 9 AMBIGU). La baisse de 10 provient de la réconciliation, pas de dix nouvelles implémentations. Pas de build natif ni de validation console.

### 2026-11-24 — VI : add/remove layer stack

Vendor `15b31ec775aea551bd126188c8e6e03987474bd2` : IManagerDisplayService cmd6000/6001 modifient réellement le masque de pile existant dans SurfaceFlinger, sous le même verrou Container que la composition. Pas de remplacement du masque entier, pas de décalage non borné ; les IDs connus 0–6 et 10 sont acceptés, les couches absentes/arrêtées rejetées. ABI u32 stack_id/u64 layer_id recroisée avec [SwIPC](https://reswitched.github.io/SwIPC/ifaces.html). CMake backports sélectionne les six fichiers sources et aucun overlay correspondant ne les remplace. **Pool restant = 1 616** (1 212 NULL + 52 STUB + 153 PARTIEL + 190 ABI-DIFF + 9 AMBIGU). Compteur : 1 PARTIEL et 1 NULL vers IMPL-SRC. Qualification statique seulement ; compilation et console non validées.

### 2026-11-24 — BTM : requêtes hors ligne et découverte audio

Vendor `18c93c2e711cc8477156176f051874f8473497ef` : 12 commandes btm legacy raccordées à des requêtes déterministes et arrêts idempotents (cmd3/9/20/27/28/30/32/33/38/44/110/115). Les listes de profils utilisent u32 + compteur s32 + buffer pointer (HOS >=13), scan compteur u8 + map alias, connexions/paired compteur u8 + pointer. Cinq commandes btm:sys Core (10/11/12/16/19) ajoutent l'état de découverte audio invité, l'absence de connexion et un événement de pairing audio distinct ; cmd13 corrige l'ABI (pas de count inline) et initialise le compteur. Aucune connexion ou périphérique fictif. Référence [libnx btm.c](https://github.com/switchbrew/libnx/blob/master/nx/source/services/btm.c) et [btmsys.c](https://github.com/switchbrew/libnx/blob/master/nx/source/services/btmsys.c). CMake et overlay contrôlés, digest actif BTM actualisé. 10 lignes historiques NULL requalifiées (7 IMPL-SRC, 3 NOOP), huit autres interventions hors catalogue historique. **Pool restant = 1 606** (1 202 NULL + 52 STUB + 153 PARTIEL + 190 ABI-DIFF + 9 AMBIGU). Tests console non effectués.

### 2026-11-24 — BTM : événements legacy hors ligne

Vendor `4bf2174fa0aa6649efad1130a8b69a127a69f83b` : neuf commandes btm legacy (2/8/18/19/23/34/40/45/52) renvoient chacune un KReadableEvent distinct, détenu par ServiceContext et libéré dans le destructeur. Bool de disponibilité et copy handle conformes au helper libnx _btmCmdGetEventOutFlag. Pas de signal artificiel de scan, connexion, appairage ou découverte : aucun backend radio invité ne produit ces événements. Couverture source des acquisitions uniquement, pas de couverture des opérations radio. **Pool restant = 1 597** (1 193 NULL + 52 STUB + 153 PARTIEL + 190 ABI-DIFF + 9 AMBIGU). Neuf entrées NULL deviennent IMPL-SRC ; console non validée.

### 2026-11-24 — BGTC / NS : état invité et lifecycle

Vendor `9bddf300fbfe814a48f57adc5dee6197afd34ad9` : BGTC cmd4/6 exposent le mode éveillé de l'invité ; cmd102/103 restent PARTIEL car aucune transition veille invitée n'est modélisée. Pas de scheduler fictif. ABI bool 1 octet recroisée [SwIPC](https://reswitched.github.io/SwIPC/ifaces.html) et noms [SwitchBrew Glue](https://switchbrew.org/wiki/Glue_services). NS IContentManagementInterface cmd607 lit l'applet principal existant et son état is_process_running / is_completed sous verrou, réponse bool conformément à [SwitchBrew NS](https://switchbrew.org/wiki/NS_services#IsAnyApplicationRunning). Quatre fichiers actifs CMake sans overlay. 5 NULL traités, 3 IMPL-SRC et 2 PARTIEL. **Pool restant = 1 594** (1 188 NULL + 52 STUB + 155 PARTIEL + 190 ABI-DIFF + 9 AMBIGU). Console non validée.

### 2026-11-24 — HID : durée de vie SevenSixAxis

Vendor `b1a597f87c6de6f473cc533a0668f4d7d27ee092` : cmd304/305/307 auparavant STUB contrôlent désormais le sampler réel et libèrent les deux KTransferMemory retenues. Cmd306 valide les tailles et handles au lieu de provoquer des assertions et initialise la session ; l'écriture et l'arrêt sont sérialisés, l'ARUID propriétaire est vérifié ; les deux propriétaires ResourceManager (source et eden-core natif) finalisent à la libération de l'applet. Les références empêchent la destruction prématurée de l'objet de transfert ; la finalisation retire les pointeurs avant de les fermer. ABI recroisée [libnx hid.c](https://github.com/switchbrew/libnx/blob/master/nx/source/services/hid.c) : le client libère ses deux handles et son buffer après cmd307. Les commandes 301/302 restent ouvertes, pas de correction de la fidélité motion revendiquée. Trois STUB vers IMPL-SRC. **Pool restant = 1 591** (1 188 NULL + 49 STUB + 155 PARTIEL + 190 ABI-DIFF + 9 AMBIGU). Compilation et console non validées.

### 2026-11-24 — LDN monitor : lifecycle réel

Vendor `8597725202341eb5bf2086977c4d7d60b89e976b` : `InitializeMonitor` place désormais le service en `State::Initialized`, `FinalizeMonitor` le remet à `State::None`, et `GetStateForMonitor` renvoie cet état au lieu d'une constante. ABI cmd0 u32 recroisée avec libnx `ldnmGetState`; aucun réseau local fictif n'est créé. **Pool restant = 1 590** (1 188 NULL + 48 STUB + 155 PARTIEL + 190 ABI-DIFF + 9 AMBIGU). Console non validée.

### 2026-11-24 — AM : statistiques de jeu réelles

Vendor `d12a06afee1436debb6d691cc098513daed0cd24` : `IApplicationFunctions` cmd110/111 réutilisent désormais les mêmes sources de vérité déjà actives dans `pdm:qry` : `PlayTimeManager` pour le temps de jeu persistant et `LaunchTimestampCache` pour le compteur de lancements. La variante UID ne fabrique pas de données par utilisateur : Encore n'a qu'une base de temps de jeu pour le profil actif, elle expose donc ces données réelles. Le manifeste de l'overlay AM est recalculé. `GetCradleFwVersion` cmd40 est aussi reclassé NOOP : le C++ actif retourne explicitement 0/0/0/0 car la PS5 n'a pas de firmware cradle Horizon. **Pool restant = 1 587** (1 188 NULL + 45 STUB + 155 PARTIEL + 190 ABI-DIFF + 9 AMBIGU). Build PS5 et console non lancés.

### 2026-11-24 — AudioDevice : périphérique actif et événement input

Vendor `fe95e74d1c59f5a064ee81d98d630446bddd508d` : cmd10 expose explicitement le périphérique Horizon virtuel `AudioTvOutput`, déjà utilisé par les chemins de volume et adossé au sink AudioCore actif ; cmd11 retourne le KReadableEvent ServiceContext réellement détenu par IAudioDevice, comme le chemin output. Le modèle d'événement partagé et le nom `AudioTvOutput` ont été recroisés avec l'implémentation indépendante Strato. Deux STUB deviennent IMPL-SRC. **Pool restant = 1 585** (1 188 NULL + 43 STUB + 155 PARTIEL + 190 ABI-DIFF + 9 AMBIGU). Console non validée.

### 2026-11-24 — nvdrv GetStatus : ABI et état d'initialisation

Vendor `f828515505b9dcc6b5571d45815c6bca1ce62a9a` : cmd6 ne répond plus toujours Success sans payload. Avant Initialize il renvoie `NvResult::NotInitialized`; après Initialize il renvoie le bloc d'état de 0x20 octets puis `NvResult::Success`, conformément au contrat recroisé Ryujinx. Les quatre compteurs mémoire internes du work-buffer ne sont pas modélisés dans Encore et restent à zéro, donc le statut reste **PARTIEL**, pas IMPL-SRC. **Pool inchangé = 1 585** (1 188 NULL + 42 STUB + 156 PARTIEL + 190 ABI-DIFF + 9 AMBIGU). Console non validée.

### 2026-11-24 — SSL SetInterfaceVersion

Vendor `1a42d4aed7974212294424c370f9e4e9e47ff08a` : cmd5 est explicitement documenté comme no-op HLE. libnx utilise les valeurs 1/2/3 pour sélectionner les générations d'interface HOS 3/5/6+, tandis qu'Encore expose déjà le superset IPC compatible ; Strato et Ryujinx appliquent également ce setter sans état backend. **Pool restant = 1 584** (1 188 NULL + 41 STUB + 156 PARTIEL + 190 ABI-DIFF + 9 AMBIGU). Console non validée.

### 2026-11-24 — AM DisplayController : capture tuilée réelle

Vendor `99879eef9fb743cf2757b2d76f765487db70e337` : IDisplayController cmd5/6/7 lisent désormais les trois slots de capture Horizon et convertissent le block-linear 1280x768 interne en sortie linéaire RGBA8 1280x720 (0x384000) via `UnswizzleTexture`. Cmd8 respecte `isScreenShotPermitted` et copie la capture GPU tuilée courante vers le slot LastApplication/LastForeground/CallerApplet demandé. Cmd9 copie les slots tuilés sans conversion et propage leur état de validité. Les écritures CPU continuent d'invalider le cache GPU ; les lectures passent par `OnCPURead` avant copie. L'ABI et la signification du bool cmd8 ont été recroisées avec libnx/SwitchBrew et l'interface SDK fefw. Cmd28 `TakeScreenShotOfOwnLayerEx` reste NULL : son mode `isImmediate=false` exige un chemin différé qui n'est pas modélisé, donc aucun faux succès ajouté. 3 STUB + 2 NULL deviennent IMPL-SRC. **Pool restant = 1 579** (1 186 NULL + 38 STUB + 156 PARTIEL + 190 ABI-DIFF + 9 AMBIGU). Compilation/CI à qualifier ; console PS5 non validée.

### 2026-11-24 — I2C : suppression des sessions matérielles factices

Vendor `3b25cbfba01518d17cf27e4869db986c70d70b82` : `OpenSessionForDev` (0), `OpenSession` (1) et `OpenSession2` (4) ne créent plus un `I2CSession` fictif alors que `HasDevice` / `HasDeviceForDev` annoncent déjà l'absence de matériel. Sans backend I2C Switch sur PS5, ces ouvertures échouent explicitement par `ResultUnknown`; aucune transaction n'est présentée comme exécutée. Les commandes session 10/11/12 deviennent INACCESSIBLE plutôt qu'ABI-DIFF puisque l'interface enfant ne peut plus être obtenue. **Pool restant = 1 573** (1 186 NULL + 35 STUB + 156 PARTIEL + 187 ABI-DIFF + 9 AMBIGU). Build natif et console non lancés.

### 2026-11-24 — HID console six-axis : Start/Stop effectifs

Vendor `a68dd1eb50cc71bffe385baaa54da5dddb0926aa` : cmd301/302 ne sont plus des succès sans effet. `ConsoleSixAxis` conserve maintenant l'ARUID du sampler actif ; `OnUpdate` n'écrit la shared memory que lorsque le contrôleur est activé **et** le sampling démarré pour l'ARUID courant. Stop désactive ce flux, et Unregister/FreeAppletResourceId l'arrête avant de libérer l'applet. Le handle console 4 octets reste opaque dans la documentation publique et n'est pas interprété comme une identité matérielle supplémentaire ; Encore ne possède qu'un capteur console. **Pool restant = 1 571** (1 186 NULL + 33 STUB + 156 PARTIEL + 187 ABI-DIFF + 9 AMBIGU). Build natif/console non lancés.

### 2026-11-24 — AM : ReportVisibleError raccordé au frontend réel

Vendor `a0c5a3beb7ab54a67a6d463002ab94e6d838f435` : les commandes ILibraryAppletSelfAccessor 50/51 ne sont plus des succès silencieux. L'ErrorCode Horizon (catégorie = module+2000, nombre = description) est validé puis converti en `Result`; le rapport est sauvegardé par `Reporter` et le `Core::Frontend::ErrorApplet` réellement configuré est invoqué. Cmd50 devient IMPL-SRC. Cmd51 devient PARTIEL : le dialogue et le rapport de base sont réels et le type/result du `ErrorContext` sont tracés, mais les champs ERPT spécifiques aux types 1..4 ne sont pas encore sérialisés vers le service de rapport. **Pool restant = 1 570** (1 186 NULL + 31 STUB + 157 PARTIEL + 187 ABI-DIFF + 9 AMBIGU). Aucun build natif PS5 lancé.

### 2026-11-24 — PDM HOS23 + EventFd actif

Vendor `175b4f2d6c9511f01aee10757a6255d84d16aab0` : `PdmPlayStatistics` cmd5 est corrigé du layout V1 0x28 vers le layout HOS16+/HOS23 0x48. La réponse utilise le temps de jeu persistant (ns), le compteur de lancements et le dernier timestamp POSIX réels ; les indices du journal PDM global et le premier timestamp restent indisponibles, donc statut **PARTIEL**. Le cmd31 BSD `EventFd` était encore classé STUB alors que le runtime actif possède `EventFdState`, `EventFdImpl`, flags semaphore/nonblock, read/write et intégration Select/Poll : reclassé **IMPL-SRC** sans changement de comportement. Le catalogue est recalculé depuis ses lignes : **pool 1 565** (1 186 NULL + 29 STUB + 154 PARTIEL + 187 ABI-DIFF + 9 AMBIGU). Console PS5 non validée.

### 2026-11-24 — IAsyncValue ErrorContext

Vendor `05646df19d6ec2db27c54ebff88fa2db9775d409` : cmd3 `GetErrorContext` respecte désormais l'ABI libnx (buffer map-alias de 0x200 octets). L'AsyncValue de ListApplicationTitle est déjà achevé avec succès, donc un `ErrorContext` nul est le contexte déterministe correct ; l'ancien handler renvoyait succès sans initialiser le buffer. **STUB → IMPL-SRC. Pool recalculé : 1 564** (1 186 NULL + 28 STUB + 154 PARTIEL + 187 ABI-DIFF + 9 AMBIGU). Console non validée.

### 2026-11-24 — AM rights environment : suppression des faux succès

Vendor `9248992c51c0c446e47e6cdb03e407d20c2a69dd` : `IApplicationAccessor::CheckRightsEnvironmentAvailable` ne prétend plus qu'un environnement de droits inexistant est disponible, et cmd132 ne renvoie plus le handle factice `0xDEADBEEF`. Cmd131 retourne `false`; cmd132 initialise la sortie à zéro puis échoue explicitement par `ResultUnknown`. Aucun objet `ns:rt` ou état de licence n'est fabriqué. Les deux STUB deviennent D ; le code d'erreur Horizon exact reste à déterminer. **Pool restant = 1 562** (1 186 NULL + 26 STUB + 154 PARTIEL + 187 ABI-DIFF + 9 AMBIGU). Build natif et console non lancés.

### 2026-11-24 — NIFM : durée de vie des événements de scan

Vendor `b2c0a25ec04f0e90668bf1d1a4b85948aa844c52` : dans l'overlay NS1 actif, `IScanRequest::~IScanRequest` attend la fin du worker avant de fermer les deux KEvent. Le worker pouvait auparavant signaler `evt_scan_complete` après fermeture. Le manifeste d'overlay est actualisé. Le gitlink inclut aussi les deux commits SSL parallèles `f87903de` et `e8889866` ; aucune modification de leur C++ dans ce lot. Le diff depuis `9248992c` ne touche que NIFM/SSL et le test SSL ; les blobs rasterizer et receipt MSAA restent identiques. Pas de reclassement du catalogue pour le correctif de durée de vie ni de validation console. Compilation native non déclenchée.

### 2026-11-24 — AM/FSP : cache storage indexé

Vendor `670673aff581924cc430d600f07ebfeea5559e07` : `IApplicationFunctions::CreateCacheStorage` ne renvoie plus un succès factice. Le handler valide l'index et la taille totale contre le NACP (FS 6070/6069), refuse les doublons (FS 3003), crée réellement le cache et persiste ses tailles. L'index 0 conserve exactement `save/cache/<program_id>` ; les index >0 utilisent des voisins `<program_id>_<index>`, donc aucune sauvegarde/cache existant n'est déplacé et supprimer l'index 0 ne supprime pas les autres. `GetCacheStorageSize`, `DeleteCacheStorage` et le lecteur `SaveDataInfo` utilisent le même index. Le backend PS5 n'expose qu'un stockage persistant de save-data, donc la cible déclarée reste NAND plutôt que de simuler un média SD distinct. Référence comportementale : LibHac/Ryujinx ; Lichii et Eglantine conservent encore le stub historique. `CreateCacheStorage` passe **STUB → IMPL-SRC** et `GetCacheStorageSize` **PARTIEL → IMPL-SRC** ; `DeleteCacheStorage` reste IMPL-SRC avec son ancienne limitation index-0 supprimée. **Pool restant = 1 560** (1 186 NULL + 25 STUB + 153 PARTIEL + 187 ABI-DIFF + 9 AMBIGU). Qualification source/host à effectuer par CI ; aucune validation console PS5 revendiquée.

### 2026-11-24 — SPL général : RSA mod-exp et boot reason

Vendor `594eacbef099b3f97f7975e19b5b64d57910ae77` : `ModularExponentiate` applique désormais le contrat libnx/Atmosphère (buffers RSA-2048 bornés à 0x100, exposant variable borné, calcul big-endian par OpenSSL `BN_mod_exp`, rejet du module nul et des tailles invalides) au lieu de `ResultSecureMonitorNotImplemented`. `SetBootReason` et `GetBootReason` partagent maintenant l'état du module SPL entre interfaces, avec `ResultBootReasonAlreadySet` / `ResultBootReasonNotSet` comme Atmosphère. `SetConfig`, `IsDevelopment` et les dérivations AES restent volontairement ouverts : aucune constante/clé factice n'a été ajoutée. L'ancien reclassement HOS23 avait déjà sorti `ExpMod` du pool sur la seule équivalence d'alias malgré son corps UNIMPLEMENTED ; ce correctif rend enfin ce statut vrai mais **ne retranche pas artificiellement une seconde fois le compteur canonique**. Pool conservé à **1 560** tant qu'une ligne de snapshot distincte pour Set/GetBootReason n'est pas prouvée.

### 2026-11-24 — NS : classification réelle des corruptions FS

Vendor `25d561a0fd182584da68d53bca65f5ec6dbee3c8` : `IReadOnlyApplicationRecordInterface::IsDataCorruptedResult` ne renvoie plus `false` pour tous les résultats. Le contrat LibHac `ResultFs.DataCorrupted` couvre exactement le module FS et les descriptions 4000–4999 ; le handler utilise désormais `Result::GetModule()` et `GetDescription()` pour cette plage, sans heuristique par code brut. **STUB → IMPL-SRC.**

**Pool restant = 1 559** : 1 186 NULL + 24 STUB + 153 PARTIEL + 187 ABI-DIFF + 9 AMBIGU. Qualification source/CI en cours ; aucune validation console PS5 revendiquée.

### 2026-11-24 — NPNS système : ABI par nom, timestamp et event

Vendor `b882a41e0b35a91051fb362cdf2082175d433748` : le dump NS1 23.0.1 confirme que `npns:s` cmd8 `ListenToByName` consomme un buffer d'entrée type 9 ; le handler système adopte maintenant cette ABI et conserve le comportement offline explicite, au lieu d'un succès sans même lire la requête. Cmd106/107 `Get/SetLastNotifiedTime` exposent désormais un état `s64` local cohérent. Cmd161 `GetRequestChangeStateCancelEvent` retourne le `KEvent` de service déjà vivant et n'est plus présenté comme stub. **3 STUB + 1 NULL → hors pool** (cmd8 NOOP offline ; cmd106/107/cmd161 IMPL-SRC).

**Pool restant = 1 555** : 1 185 NULL + 21 STUB + 153 PARTIEL + 187 ABI-DIFF + 9 AMBIGU. Build natif PS5 non déclenché ; validation console non revendiquée.

### 2026-11-24 — NVDEC : SET_SUBMIT_TIMEOUT

Vendor `a11b70417f1c981580a86bf5391b4a24fe0890e9` : le propriétaire réellement sélectionné par le CMake PS5, `encore-active/eden-core/.../nvhost_nvdec_common.cpp`, ne jette plus la valeur de `NVHOST_IOCTL_CHANNEL_SET_SUBMIT_TIMEOUT`. Le champ `submit_timeout` existait déjà dans la classe ; le setter le renseigne maintenant, conformément au comportement Ryujinx. Aucun timeout scheduler artificiel n'est ajouté : il s'agit de l'état du canal demandé par le guest. **STUB → IMPL-SRC**. Le garde GPU-36 épingle le nouveau blob actif.

**Pool restant = 1 554** : 1 185 NULL + 20 STUB + 153 PARTIEL + 187 ABI-DIFF + 9 AMBIGU. Build natif PS5 non déclenché ; validation console non revendiquée.

### 2026-11-24 — AM : maxima save-data depuis le NACP

Vendor `afac75c2d5e4e494335bbc48f18cbf8a9a3e17a3` : cmd28 `GetSaveDataSizeMax` ne renvoie plus deux constantes `0x0FFFFFFF`; il lit `user_account_save_data_max_size` et `user_account_save_data_max_journal_size` du NACP actif. Cmd35 `GetDeviceSaveDataSizeMax`, ABI NS1 23.0.1 confirmée à 0x10 octets de sortie, est raccordée aux champs `device_save_data_max_size` / `device_save_data_max_journal_size`. **1 STUB + 1 NULL → IMPL-SRC**.

**Pool restant = 1 552** : 1 184 NULL + 19 STUB + 153 PARTIEL + 187 ABI-DIFF + 9 AMBIGU. Build natif PS5 non déclenché ; validation console non revendiquée.

### 2026-11-24 — LBL : état de luminosité appliquée invité

Vendor `c24bcfa3fb9da644d31689ae4d16f2745f240227` : cmd4 `ApplyCurrentBrightnessSettingToBacklight` copie maintenant le réglage invité courant vers un état `applied_brightness`, et cmd5 `GetBrightnessSettingAppliedToBacklight` relit cette valeur avec la même protection contre les flottants non finis que les getters existants. Cmd6/7 `SwitchBacklightOn/Off` maintenaient déjà `backlight_enabled`; leurs marqueurs STUB ont été retirés et le `fade_time` est explicitement traité comme un **NOOP matériel PS5** : aucune luminosité système hôte n'est modifiée. Le dump NS1 23.0.1 confirme les ABI cmd4/5 sans entrée puis sortie `float`, et cmd6/7 avec `u64 fade_time`. **2 NULL + 2 STUB → hors pool**.

**Pool restant = 1 548** : 1 182 NULL + 17 STUB + 153 PARTIEL + 187 ABI-DIFF + 9 AMBIGU. Build natif PS5 non déclenché ; validation console non revendiquée.

### 2026-11-24 — AM : état HDCP cohérent entre ApplicationFunctions et CommonStateGetter

Vendor `67219c2d7f5b88e3c20f148fbfab7c9bba3f087c` : cmd170 `SetHdcpAuthenticationActivated`, déjà présent dans l'overlay actif mais encore NULL dans le snapshot canonique, met à jour `m_applet->hdcp_authentication_activated`. Le getter cmd62 ne renvoie plus la constante `1` : il relit le même état sous verrou. Une transition signale `GetHDCPStateChangedEvent()`, sans toucher à la configuration HDCP de la PS5 hôte. Le dump NS1 23.0.1 confirme cmd170 = entrée bool 1 octet et cmd62 = sortie s32. **1 NULL → IMPL-SRC**.

**Pool restant = 1 547** : 1 181 NULL + 17 STUB + 153 PARTIEL + 187 ABI-DIFF + 9 AMBIGU. Build natif PS5 non déclenché ; validation console non revendiquée.


### 2026-11-24 — NIFM : politique IRequest et applet de connexion

Vendor `100be854211d10cb02b96e8f0059e1d924fa09c3` : dans l'overlay NIFM réellement compilé, cmd6 `SetRequirementPreset` et cmd11 `SetConnectionConfirmationOption` ne sont plus présentés comme des stubs. Les deux entrées sont consommées avec leur ABI (u32 / u8) et deviennent des **NOOP explicites** sur PS5 : Encore évalue directement l'état réseau hôte et ne possède pas le daemon de politique ni l'applet de confirmation Horizon. Ce comportement est cohérent avec Strato/Ryujinx pour ces setters. Cmd21 `GetAppletInfo` ne fabrique plus un applet id/mode/taille à zéro ni un buffer vide : en l'absence d'applet réseau Horizon, il renvoie le résultat NIFM **AppletLaunchNotRequired (module 110, description 180)** observé chez Strato et Ryujinx. Le manifeste de l'overlay est recalculé (`54346de56e89098daaa15917d919f01efb75dbc008e37776de73160e5ee789e7`, 59 453 octets). **3 STUB → hors pool**.

**Pool restant = 1 544** : 1 181 NULL + 14 STUB + 153 PARTIEL + 187 ABI-DIFF + 9 AMBIGU. Build natif PS5 non déclenché ; validation console non revendiquée.


### 2026-11-24 — AM : ApproveToDisplay publie la visibilité réelle

Vendor `0837393bd5c8c3c48f5681dea1ac1dba76a6d6c8` : `ISelfController::ApproveToDisplay` n'est plus un succès vide. La commande passe désormais par le `WindowSystem` actif et appelle `RequestAppletVisibilityState(*m_applet, true)`, qui met à jour `window_visible` sous verrou puis réveille l'observateur AM afin que le scheduling/foreground soit réévalué. Si le `WindowSystem` est momentanément absent pendant création/destruction, seul l'état invité est conservé sous verrou, sans déréférencement nul. Cette sémantique recoupe l'implémentation Napple (ApproveToDisplay rend la fenêtre visible) tout en réutilisant le chemin de visibilité déjà employé par `IWindowController` dans Encore. Le manifeste de l'overlay actif est recalculé (`1f9b071508fa6aa62167ce855ff02bf5d1d35149b77e1b94a0486fd4a92ab333`, 21 318 octets). **1 STUB → IMPL-SRC**.

**Pool restant = 1 543** : 1 181 NULL + 13 STUB + 153 PARTIEL + 187 ABI-DIFF + 9 AMBIGU. Build natif PS5 non déclenché ; validation console non revendiquée.


### 2026-11-24 — SPL : état retail et IsDevelopment réel

Vendor `dab56d88cbbe166575546fff3346feb4727afbf4` : `spl:` cmd11 `IsDevelopment` ne renvoie plus `ResultSecureMonitorNotImplemented`. Le handler suit le contrat libnx/SwitchBrew (aucune entrée, sortie bool u8) et dérive sa réponse du même `ConfigItem::HardwareState` que `GetConfig`. Encore expose explicitement une unité retail/production (`HardwareState::Production`), donc `IsDevelopment` renvoie false sans fabriquer un mode dev. **Correction de comptage : cmd11 était déjà classé D dans le catalogue détaillé, pas STUB ; ce correctif runtime ne réduit donc pas le pool canonique.**

**Pool restant = 1 543** : 1 181 NULL + 13 STUB + 153 PARTIEL + 187 ABI-DIFF + 9 AMBIGU. Build natif PS5 non déclenché ; validation console non revendiquée.


### 2026-11-24 — SPL : suppression des faux succès AES

Vendor `94c61421e27d837e28b7331690305a72baad4d93` : `GenerateAesKek` (cmd2) et `GenerateAesKey` (cmd4) ne renvoient plus `Success` avec respectivement une `AccessKey` et une `AesKey` entièrement nulles. Sans backend Secure Monitor/keyslot authentique dans Encore, ces deux dérivations échouent désormais explicitement par `ResultSecureMonitorNotImplemented`, comme les autres opérations SPL impossibles à reproduire sans secrets matériels. Les payloads d'entrée restent consommés et aucune clé fictive n'est publiée. **2 STUB → D.**

**Pool restant = 1 541** : 1 181 NULL + 11 STUB + 153 PARTIEL + 187 ABI-DIFF + 9 AMBIGU. Build natif PS5 non déclenché ; validation console non revendiquée.


### 2026-11-24 — SFDNSRES : contrat ResolverSetOptionRequest

Vendor `65cffbdeed0bf25fe1bf5b840450a426e1f3b255` : cmd14 `ResolverSetOptionRequest` ne répond plus avec une IPC tronquée. Le handler consomme désormais le `u64` d'entrée et le buffer opaque d'options, puis renvoie les deux mots attendus par le contrat HOS/Ryujinx (`i32 ret`, `u32 bsd_errno`) au lieu du seul errno. Les options restent non interprétées par le resolver hôte, donc la commande est classée **PARTIEL** et non IMPL-SRC. **1 STUB → PARTIEL ; pool total inchangé.**

**Pool restant = 1 541** : 1 181 NULL + 10 STUB + 154 PARTIEL + 187 ABI-DIFF + 9 AMBIGU. Build natif PS5 non déclenché ; validation console non revendiquée.


### 2026-11-24 — BSD : StartMonitoring conforme libnx

Vendor `4ee2d58ce739af8e91d78794d6859b4662f8cb86` : cmd1 `StartMonitoring` consomme désormais le `u64 client_pid` envoyé par libnx (avec le PID descriptor géré par l'IPC) au lieu d'ignorer entièrement la requête. Libnx n'attend aucun payload de réponse. Encore n'a pas de scheduler de monitoring socket séparé : le backend BSD vivant est déjà attaché à la durée de vie du service, donc l'enregistrement est un **NOOP contractuel** et non un faux monitoring. Référence croisée : libnx `_bsdStartMonitoring`, Ryujinx et implémentations HOS indépendantes. **1 STUB → NOOP.**

**Pool restant = 1 540** : 1 181 NULL + 9 STUB + 154 PARTIEL + 187 ABI-DIFF + 9 AMBIGU. Build natif PS5 non déclenché ; validation console non revendiquée.


### 2026-11-24 — AM : suppression du faux handle indirect-layer

Vendor `301c0bda4d9e5d81320361ea5ca24ab5a8cffcd2` : `ILibraryAppletAccessor::GetIndirectLayerConsumerHandle` (cmd160) ne renvoie plus `Success + 0xDEADBEEF`. Encore n'a actuellement aucun backend VI indirect-layer complet : les créations/destructions/endpoints VI correspondants restent absents et `GetIndirectLayerImageMap` ne produit pas d'image. Le handler initialise donc la sortie à zéro puis échoue explicitement par `ResultUnknown`, au lieu de publier un handle impossible à consommer. Ryujinx montre qu'une implémentation complète exige un registre de handles lié à l'applet ; ce registre n'est pas fabriqué tant que le backend VI n'existe pas. **1 STUB → D.**

**Pool restant = 1 539** : 1 181 NULL + 8 STUB + 154 PARTIEL + 187 ABI-DIFF + 9 AMBIGU. Build natif PS5 non déclenché ; validation console non revendiquée.


### 2026-11-24 — HID : UniquePad raccordé aux contrôleurs réellement connectés

Vendor `aa6c39c16c8229d322869a70e7be7a71e1237d5b` : `IHidSystemServer::GetUniquePadIds` (cmd703) ne renvoie plus systématiquement zéro. Les IDs sont stables par slot émulé, **P1–P8 = 1–8, Handheld = 9**, et le pseudo-slot `Other` est exclu. Un pad n'est publié que si son `EmulatedController` est connecté et possède un style Npad actif ; le nombre retourné est limité à la capacité réelle du buffer invité. `GetUniquePadsFromNpad` (cmd321) est corrigé en parallèle pour exposer la même topologie et renvoyer le **compte u64** exigé par l'ABI NS1 23.0.1, au lieu d'un u32. Le dump NS1 23.0.1 confirme cmd321 = entrée 0x4 + buffer type 10 + sortie 0x8 et cmd703 = buffer type 10 + sortie 0x8. Le modèle d'IDs par slot connecté recoupe Ryujinx/Nextendo. Aucun numéro matériel ou série fictif n'est inventé. Manifeste actif : SHA-256 `ae35541b5666f8c5c75efcccf2c688002366d182b0101f5e9e703eef122ddb78`, 43 664 octets. **1 STUB → IMPL-SRC** ; la correction cmd321 est une correction ABI/runtime hors delta du pool canonique.

**Pool restant = 1 538** : 1 181 NULL + 7 STUB + 154 PARTIEL + 187 ABI-DIFF + 9 AMBIGU. Build natif PS5 non déclenché ; validation console non revendiquée.


### 2026-11-24 — OVLN sender : ABI libounce + queue locale

Vendor `69e90bc940df1cfefcd9e3f6d0d7b5a5d7984413` : la famille `ovln:snd` n'utilise plus les formes approximatives historiques. `SourceName` est corrigé à 0x10 octets et `QueueAttribute` à 0x8, conformément à libounce/libnx. `OpenSender` consomme ces deux structures et construit un `ISender` concret avec la capacité demandée. `Send` consomme désormais l'ordre HOS exact `SendOption(0x8) -> RawMessage(0x80)`, maintient une file locale par sender, applique front/back et les politiques RemoveFront/RemoveBack, et refuse explicitement les cas Error/Block qu'Encore ne peut pas faire progresser sans receiver connecté. Cmd1 `GetUnreceivedMessageCount` expose la profondeur réelle de cette file. Le pont sender→`ovln:rcv` n'est pas encore partagé, donc `Send` reste **PARTIEL** ; `OpenSender` sort du statut stub puisqu'il rend l'objet IPC réel attendu par qlaunch. La correction de taille `SourceName` s'applique aussi au receiver déjà actif.

**Delta canonique : OpenSender STUB → IMPL-SRC ; Send STUB → PARTIEL. Pool restant = 1 537** : 1 181 NULL + 5 STUB + 155 PARTIEL + 187 ABI-DIFF + 9 AMBIGU. Build natif PS5 non déclenché ; validation console non revendiquée.


### 2026-11-24 — NIFM : SetChannels conserve le contrat invité

Vendor `945a4a0a9c4b535fa509f1ffed992d41632ddab7` : `IScanRequest::SetChannels` (cmd4, HOS 6+) consomme désormais le buffer `s16[]` documenté par l'ABI et conserve la liste demandée dans l'objet de scan, au lieu d'ignorer entièrement la requête. Le scanner natif Encore ne publie actuellement que SSID/qualité/flags et aucune métadonnée de canal ; sur PS5 il n'expose pas de radio Wi-Fi invitée. Aucun filtrage fictif n'est donc ajouté. La commande devient **PARTIEL** jusqu'à ce que le backend de scan transporte réellement les canaux. Référence croisée : Ryujinx-Nextendo confirme cmd4 `SetChannels(buffer<s16>)`. Le garde moteur corrige aussi la valeur tree tronquée (39 caractères) laissée pour le prédécesseur OVLN `69e90bc940df1cfefcd9e3f6d0d7b5a5d7984413`, sans changer ce prédécesseur.

**Delta canonique : 1 STUB → PARTIEL ; pool total inchangé = 1 537** : 1 181 NULL + 4 STUB + 156 PARTIEL + 187 ABI-DIFF + 9 AMBIGU. Build natif PS5 non déclenché ; validation console non revendiquée.


### 2026-11-24 — AM : état copyright validé

Vendor `08f3042aecf16bf086d5463c55c1c9a150603d0f` : les trois commandes copyright d'`IApplicationFunctions` ne sont plus des succès vides. Cmd100 valide le framebuffer HOS (dimensions 1..1280 × 1..720, taille RGBA8 minimale et alignement transfer-memory 0x40000) puis conserve le contrat validé. Cmd101 valide origine, rectangle et taille RGBA8, puis mémorise l'image courante ; cmd102 conserve réellement la visibilité, initialement vraie comme sur HOS. Les validations sont recroisées avec SwitchBrew, Strato et Ryujinx. Encore ne compose pas encore cette image dans le pipeline de capture/screenshot GPU : les trois commandes sont donc **PARTIEL**, pas IMPL-SRC.

**Delta canonique : 3 STUB → PARTIEL ; pool total inchangé = 1 537** : 1 181 NULL + 1 STUB + 159 PARTIEL + 187 ABI-DIFF + 9 AMBIGU. Build natif PS5 non déclenché ; validation console non revendiquée.


### 2026-11-24 — AM GPU time-slice + NS dynamic-rights fail-closed

Vendor `d2e93fb0fa67548d2ae500f1bde6c19c941ecb7a` (successeur direct du lot copyright) contient deux corrections runtime supplémentaires :

- `IWindowController::SetAppletGpuTimeSlice` (cmd21) conserve maintenant le `s64` demandé dans l'état de l'applet sous verrou, conformément à l'ABI libnx et au modèle Strato. La valeur Horizon **n'est pas** transformée en réglage du scheduler GPU hôte PS5 : elle reste une politique invitée, ce qui évite une optimisation hôte inventée.
- `IDynamicRightsInterface::GetRunningApplicationStatus` et `VerifyActivatedRightsOwners` ne renvoient plus `Success` lorsqu'Encore ne possède aucun environnement de droits Nintendo. La sortie status est initialisée à zéro puis la requête échoue explicitement par `ResultUnknown`, cohérent avec le précédent fail-closed AM rights-environment. Le code d'erreur Horizon exact reste non établi.

**Correction du suivi :** le précédent agrégat « 1 STUB » ne doit plus être utilisé comme compteur global. Le catalogue annexe conserve des statuts historiques qui n'ont pas tous été réconciliés avec les owners actifs. Une revue directe du runtime courant confirme encore au moins quatre vrais stubs du résidu historique : `CanUseApplicationCore`, `GetOperationModeSystemInfo`, `ImportServerPki` et `ImportClientPki`. Les deux premiers manquent de sémantique suffisamment documentée ; les deux SSL restent isolés du présent lot pour ne pas empiéter sur le travail SSL parallèle. **Aucun nouveau total global n'est revendiqué avant réconciliation ligne par ligne.**

Build natif PS5 non déclenché ; aucune validation console revendiquée.


### 2026-11-24 — SSL : suppression des faux succès PKI

Vendor `b57ce2770c82aef425bc34e2fed2492f63adfe4d` : `ISslContext::ImportServerPki` (cmd4) et `ImportClientPki` (cmd5) consomment toujours leurs paramètres/buffers et conservent la forme de réponse avec ID `u64`, mais ne renvoient plus `Success + id 0`. Le backend TLS actif Encore ne possède ni registre PKI context-local, ni `SSLTrustStore`/décodage PKCS#12 raccordé aux connexions ; les deux commandes échouent donc explicitement par `IPC::ResultNotSupported` avec ID initialisé à zéro.

Un fork Eglantine récent possède un vrai `ImportServerPki`, mais il dépend d'une couche entière `DecodeServerPki + SSLTrustStore + cache de trust-store` absente d'Encore ; ce WIP n'est pas backporté à l'aveugle. `ImportClientPki` y reste d'ailleurs encore un stub. Le travail SSL NS1 historique du 11/11 est bien ancêtre du vendor courant et aucune branche SSL active n'est présente, donc ce correctif ne remplace pas un travail parallèle vivant.

**Résidu historique désormais prouvé ouvert dans cette famille STUB :** `CanUseApplicationCore` et `GetOperationModeSystemInfo` seulement. Libounce/SwitchBrew confirment leurs ABI, mais pas la sémantique nécessaire pour produire une valeur fidèle ; Encore n'implémente pas davantage `omm` cmd26. Ils restent ouverts plutôt que d'être figés sur des constantes supposées.

Build natif PS5 non déclenché ; aucune validation console revendiquée.


### 2026-11-24 — Réconciliation du résidu STUB historique

Les 26 lignes encore marquées STUB dans l'annexe SwitchBrew ont été recroisées avec le runtime actif au vendor `b57ce2770c82aef425bc34e2fed2492f63adfe4d`. 24 étaient des statuts historiques déjà dépassés par les correctifs de la branche : **4 → IMPL-SRC, 7 → PARTIEL, 4 → NOOP, 1 → NULL, 8 → D**. Le résidu STUB réellement prouvé est donc limité à **`CanUseApplicationCore`** et **`GetOperationModeSystemInfo`**. Le premier est bloqué par la règle firmware NPDM→ApplicationCore non documentée ; le second par la sémantique inconnue du `u32` OMM cmd26. Aucun bit/retour supposé n'est introduit. NIM `IShopServiceAsync::Prepare` est reclassé NOOP : les implémentations de compatibilité sans eShop (notamment S2Arm/Ryujinx) acceptent cette préparation sans état distant, tandis que `Request` reste PARTIEL avec son corps JSON de compatibilité.

Cette opération répare le suivi du lot STUB ; elle **ne prétend pas recalculer exhaustivement le pool NULL/PARTIEL/ABI-DIFF**. Build natif PS5 non déclenché ; validation console non revendiquée.


### 2026-11-24 — AM HomeMenu : writer lock accessors raccordés

Vendor `95089b809f5eb4d3621eaddec92638e8c82f7fa4` : l'owner réellement compilé `encore-active/eden-backports/.../home_menu_functions.cpp` raccorde désormais IHomeMenuFunctions cmd30 `GetHomeButtonWriterLockAccessor` et cmd31 `GetWriterLockAccessorEx`. Les deux retournent un objet IPC `ILockAccessor` concret, déjà utilisé côté ICommonStateGetter ; cmd31 rejette les types hors plage 0..3 conformément au contrat libnx. Le modèle `ILockAccessor` actuel garde toutefois son état par objet et ne partage pas encore un arbitre reader/writer global entre accessors : **2 NULL → PARTIEL**, pas IMPL-SRC complet. Manifeste overlay recalculé ; copie base non modifiée.

Aucun build natif PS5 déclenché ; validation console non revendiquée.


### 2026-11-24 — AM Overlay : terminaison application et transitions shutdown/reboot

Vendor `3260a2ecf296b08d923e2cfe1205689b652cb9f1` : l'owner actif `encore-active/eden-backports/.../overlay_functions.cpp` raccorde trois commandes lifecycle jusque-là NULL. Cmd5 `TerminateApplicationAndSetReason` récupère l'application principale via le `WindowSystem`, conserve le `Result` Horizon dans `terminate_result`, termine son processus puis demande une mise à jour de la fenêtre. Cmd10/11 `StartShutdownSequenceForOverlay` / `StartRebootSequenceForOverlay` utilisent la même transition `system.Exit()` que les commandes déjà actives de `IGlobalStateController`; cette sortie concerne le système invité Encore et ne demande pas l'arrêt ou le reboot de la PS5 hôte. Libnx confirme cmd5 = u32 reason et cmd10/11 = no-input/no-output, avec boucle de sommeil côté client après succès.

**3 NULL → IMPL-SRC.** Manifeste overlay recalculé. Build natif PS5 non déclenché ; console non validée.


### 2026-11-24 — AM application : requêtes shutdown/reboot raccordées

Vendor `1bd95def9ee03b841171924716280f6d5ccb3a09` : `IApplicationFunctions` cmd70 `RequestToShutdown` et cmd71 `RequestToReboot` ne sont plus NULL. Libnx confirme deux commandes sans payload, réservées aux applications HOS 3.0+. Elles utilisent la même transition `system.Exit()` que `IGlobalStateController` et les commandes Overlay déjà raccordées. Cela termine le système invité Encore et **ne commande ni arrêt ni reboot de la PS5 hôte**.

**2 NULL → IMPL-SRC.** Manifeste overlay recalculé. Build natif PS5 non déclenché ; validation console non revendiquée.


### 2026-11-24 — AM application : push-and-request-to-start

Vendor `54f03c30bac3ebd4d1b3bb04ab2df298bc565a87` : cmd10 `CreateApplicationAndPushAndRequestToStart` suit désormais le contrat SwitchBrew : le `IStorage` d'entrée est poussé dans le user channel de l'applet puis le lancement délègue à cmd12 `CreateApplicationAndRequestToStart`, déjà raccordé au relaunch/program-index Encore. Si cmd12 échoue (par exemple lancement d'une autre application encore non pris en charge), le storage ajouté est retiré afin de ne pas contaminer un lancement suivant.

**1 NULL → IMPL-SRC.** Les variantes Quest cmd11/13/14/15 restent ouvertes tant que leurs `ApplicationAttribute` ne sont pas réellement appliqués. Build natif PS5 non déclenché ; validation console non revendiquée.


### 2026-11-24 — AM : producer indirect-layer fail-closed

Vendor `3ae8cda53774da47ad69bdb4f91ef2434acf1fb5` : `ILibraryAppletSelfAccessor::GetIndirectLayerProducerHandle` (cmd40) est désormais raccordé sur l'owner backport actif. Comme pour le consumer cmd160 déjà corrigé, Encore ne dispose pas encore du backend VI indirect-layer / `IHOSBinderDriverIndirect` nécessaire pour produire un handle utilisable. La sortie est explicitement initialisée à zéro puis la commande retourne `ResultUnknown`, au lieu de rester NULL ou de publier un handle fictif. **1 NULL → D.** Manifeste overlay recalculé. Build natif PS5 non déclenché ; validation console non revendiquée.


### 2026-11-24 — AM application : permission save-data self prouvée

Vendor `695b49c4255c816f8212d2c8a17fe81daa6e4a77` : `IApplicationAccessor::HasSaveDataAccessPermission` (cmd170) n'est plus NULL. SwitchBrew documente explicitement que lorsque l'ApplicationId demandé correspond à l'application courante, Horizon retourne immédiatement succès avec `flag=1`. Encore applique désormais cette règle depuis le vrai `m_applet->program_id`. Pour un autre title ID, Encore retourne `false` plutôt que d'accorder un droit inter-title fictif, car aucune matrice ACL Horizon complète n'est encore modélisée. **1 NULL → PARTIEL.**

Le TU concerné reste `sources/eden/src/core/hle/service/am/service/application_accessor.cpp` : le CMake actif de l'overlay le référence mais aucun override de ce fichier n'existe dans le manifeste, donc la base `sources/eden` est bien l'owner fourni au build fusionné. Aucun build natif PS5 ni résultat console revendiqué.


### 2026-11-24 — AM DisplayController : screenshot Ex raccordé au backend réel

Vendor `e7137658964ed0ed011be58939a71519fb543b9a` : `IDisplayController::TakeScreenShotOfOwnLayerEx` (cmd28) est désormais raccordé au même chemin de capture réel que cmd8. SwitchBrew documente que cmd28 appelle la même fonction interne que `TakeScreenShotOfOwnLayer`, avec un booléen supplémentaire indiquant le mode immédiat. Encore consomme donc les deux booléens et le slot `s32`, respecte la permission de capture et écrit la capture GPU courante via `WriteAppletCaptureBufferToSlot`. Le backend PS5 est actuellement synchrone : `immediately=false` et `true` convergent encore vers la même capture immédiate. **1 NULL → PARTIEL**, sans prétendre implémenter une file différée inexistante.

Le TU est la base active `sources/eden/src/core/hle/service/am/service/display_controller.cpp` (aucun override de ce fichier dans l'overlay backports). Aucun build natif PS5 ni résultat console revendiqué.


### 2026-11-24 — AM DisplayController : rejets legacy matérialisés dans le runtime

Vendor `ab5fa3bd3d8e4e2a90b43379d40760203c7520da` : les commandes 0/2/3 `GetLastForegroundCaptureImage`, `GetLastApplicationCaptureImage` et `GetCallerAppletCaptureImage` ne sont plus des slots `nullptr`. SwitchBrew documente ces trois anciennes commandes Horizon comme stubbées avec retour erreur ; les implémentations Yuzu historiques utilisent `ResultUnknown`. Encore consomme maintenant le buffer type-0x6 puis renvoie explicitement `ResultUnknown`, au lieu de laisser le dispatcher traiter la commande comme inconnue. Leur statut canonique était déjà **D**, donc **aucun changement de compteur** : ce commit aligne le C++ actif sur le classement déjà établi.

Les cmd5/6/7 `*Ex` restent les seuls getters de capture fonctionnels et ne sont volontairement pas réutilisés pour les commandes legacy. Aucun build natif PS5 ni résultat console revendiqué.


### 2026-11-24 — AM DisplayController : acquisitions capture legacy fermées pour HOS 23

Vendor `9ff0457f18f3d06771f450a665f75c454dae2f61` : les six commandes d'acquisition legacy 10/12/14/16/17/18 sont maintenant raccordées à un rejet explicite `ResultUnknown`. SwitchBrew documente 10/12/14 comme stubs Horizon. Pour 16/17/18, la TransferMemory RW 0x384000 n'est fournie que sur les anciens sysvers ; sur les firmwares récents, l'appel interne échoue systématiquement. La cible Encore HOS 23 ne doit donc pas recréer ce chemin historique. Les trois commandes 10/12/14 étaient déjà classées **D** ; **16/17/18 passent NULL → D**, soit **3 NULL → D** au compteur.

Les acquisitions shared-buffer modernes 22/24/26 restent le chemin fonctionnel Encore. Aucun build natif PS5 ni résultat console revendiqué.


### 2026-11-24 — AM DisplayController : release legacy ne renvoie plus un faux succès

Vendor `f48a197733474dd1b12400eec775a88e9f89828f` : les commandes 11/13/15 `Release*CaptureBuffer` renvoyaient `Success` alors que, sur HOS 23, les acquisitions legacy 10/12/14/16/17/18 échouent et aucun état « acquired » ne peut être établi. SwitchBrew documente que la release échoue lorsque son état est déjà nul ; Ryujinx identifie le résultat comme **AM description 504, BufferNotAcquired**. Encore définit désormais `ResultBufferNotAcquired{ErrorModule::AM, 504}` et l'utilise pour ces trois releases. **3 IMPL-SRC → D.**

Les commandes shared-buffer modernes 22–27 restent indépendantes et ne sont pas affectées. Aucun build natif PS5 ni résultat console revendiqué.


### 2026-11-24 — AM application : variantes Quest raccordées au launcher actif

Vendor `230caf1fd48d5f03c9dbdab77178a12c6738a65e` : les commandes 11/13/14/15 de `IApplicationFunctions` ne sont plus NULL. Libnx confirme leurs ABI : 11/13 ajoutent deux champs Quest `u32`; 14/15 utilisent un buffer `AppletApplicationAttribute` de 0x20 octets, et 11/14 transportent aussi le `IStorage` user-channel. Encore réutilise désormais les chemins réels cmd10/cmd12 : le storage est réellement empilé et rollbacké si le relaunch échoue, et l'ApplicationId suit les mêmes vérifications de base-title/program-index. Les attributs Quest (timers inconnus et volume) sont consommés mais ne pilotent pas encore une politique kiosk/audio du frontend PS5. **4 NULL → PARTIEL.**

Le correctif vise l'overlay réellement sélectionné `encore-active/eden-backports/src/core/hle/service/am/service/application_functions.*` et son manifeste a été recalculé. Aucun build natif PS5 ni résultat console revendiqué.


### 2026-11-24 — AM CommonStateGetter : politique sleep HOS23

Vendor `85b37ea44ef1ca0d8c3c001ee4186aa42bd051d5` : les commandes 500–503 ne sont plus NULL. `DisableSleepTillShutdown` conserve l'interdiction de sleep jusqu'à destruction du contexte invité ; `SuppressDisablingSleepTemporarily` consomme la durée libnx en nanosecondes et mémorise un deadline monotone saturé ; `IsSleepEnabled` et `IsDisablingSleepSuppressed` relisent ce même état sous verrou. Ce modèle reste séparé de `auto_sleep_disabled`, qui concerne l'auto-sleep. Aucun thread timer et aucune action de mise en veille de la PS5 hôte ne sont introduits. ABI recoupée avec libnx et les interfaces nn::am publiées. **4 NULL → PARTIEL** : l'état Horizon est cohérent, mais Encore ne possède pas de gestionnaire de veille matérielle Switch/PS5 à piloter.

Aucun build natif PS5 déclenché ; validation console non revendiquée.


### 2026-11-24 — AM OverlayFunctions : politiques GPU HOS23

Vendor `ea322a8365ee7190757a7389c8538971e467b9a6` : cmd50 `SetGpuTimeSliceBoostForApplication` et cmd90 `SetRequiresGpuResourceUse` ne sont plus NULL. Le dump HOS23 confirme respectivement une entrée u64 et une entrée bool u8, sans sortie. SwitchBrew documente cmd90 comme un setter qui « just returns 0 » ; Ryujinx accepte également les deux commandes sans backend de politique GPU distinct. Encore consomme donc les payloads avec leur ABI exacte et les traite comme **NOOP de politique explicites**, sans modifier artificiellement le scheduler Vulkan/PS5 ni le time-slice déjà exposé par les autres commandes AM. **2 NULL → NOOP.**

Aucun build natif PS5 déclenché ; validation console non revendiquée.


### 2026-11-24 — AM CommonStateGetter : rejets explicites des backends absents

Vendor `114aafbd10411faa65d0194775fd93f4a358fc21` : quatre slots jusque-là NULL sont désormais raccordés à un rejet AM explicite commun : cmd59 `SetVrPositionForDebug`, cmd110 `OpenMyGpuErrorHandler`, cmd400 `ActivateMigrationService` et cmd401 `DeactivateMigrationService`. Encore ne possède ni backend VR debug positionnel, ni objet GPU-error AM dédié, ni service de migration Horizon ; aucun objet, état ou succès fictif n'est créé. **4 NULL → D.**

Aucun build natif PS5 déclenché ; validation console non revendiquée.

### 2026-11-24 — AM HomeMenu : lancement réel du Starter + portée HOS23

Vendor `a6c0444213541f747a85bd7936b1f5046ca0023f` : `IHomeMenuFunctions::LaunchStarter` (cmd51, HOS 16+) n'est plus un slot NULL. L'owner réellement compilé `encore-active/eden-backports/.../home_menu_functions.cpp` utilise le ProgramId `AppletProgramId::Starter = 0x0100000000001012`, crée le processus invité via `CreateProcess`, matérialise un `AppletId::Starter` de type `LibraryApplet`, l'enregistre dans le `WindowSystem` puis démarre réellement son processus. Cette séquence réutilise les primitives AM déjà actives ; elle ne renvoie pas un succès fictif. **1 NULL → IMPL-SRC.**

`LaunchSystemApplet` (cmd50) reste volontairement NULL : Horizon le résout via l'état NS et `ns.applet!system_applet_id`, état qu'Encore ne modélise pas encore fidèlement. `SelectApplicationLicense` (IApplicationFunctions cmd34) est documenté uniquement pour HOS 10.0.0–15.0.1 ; pour la cible NS1/HOS23 d'Encore il est donc **HORS-VERSION** et reste `nullptr` sans constituer un trou runtime HOS23. **1 NULL → HORS-VERSION** au classement cible, sans prétendre à une implémentation.

Référence : SwitchBrew Applet Manager services / IHomeMenuFunctions et IApplicationFunctions. Par rapport au dernier pool réconcilié de cette reprise (**1 559**), ces deux décisions donnent **1 557 / 4 853 restant** : un vrai correctif runtime et une requalification de version. Sur les quatre owners AM ciblés, il reste **13 slots `nullptr` physiques**, dont **12 pertinents HOS23**. Aucun build natif PS5 ni résultat console revendiqué.

### 2026-11-24 — AM application : événement d’upgrade de licence matérialisé

Vendor `3c0eec8055735d537ca4cc59c57961ddc049caf5` : `IApplicationFunctions::GetLimitedApplicationLicenseUpgradableEvent` (cmd37) ne laisse plus le dispatcher sur un slot NULL. Le service possède désormais un `Event` réel, attaché à un `ServiceContext`, et retourne son `KReadableEvent` par copy-handle. Dans le modèle actuel Encore, `GetLimitedApplicationLicense` expose explicitement l’absence de licence limitée/trial et aucun backend de dynamic-rights ne peut produire une transition d’upgrade ; l’événement reste donc valide mais non signalé. **NULL → PARTIEL**, pas IMPL-SRC complet : le signalement firmware reste à raccorder lorsqu’un vrai état de licence/droits existe.

Le **pool global reste 1 557 / 4 853** car PARTIEL reste dans le pool. Sur les quatre owners AM ciblés, il reste **12 slots `nullptr` physiques**, dont **11 pertinents HOS23** après exclusion de `SelectApplicationLicense`. Aucun build natif PS5 ni validation console revendiqués.

### 2026-11-24 — AM application : cmd320 capture-state backport ciblé

Vendor `1c35f384381a9ef52e3d8055186f3e30f7495bde` : le slot HOS20+ cmd320 est raccordé au handler `GetScreenShotAndContinuousRecordingInitiallyEnabled`, backporté isolément depuis le chemin Lichii/NS2 déjà présent dans Encore. Le handler retourne deux booléens depuis l’état AM réel sous verrou : permission screenshot et enregistrement gameplay supporté+actif. Aucun stub générique ni valeur constante n’est utilisé. SwitchBrew confirme l’existence du cmd320 sur HOS20+ mais ne documente pas encore publiquement son nom/ABI ; classement conservateur **NULL → PARTIEL** jusqu’à preuve indépendante firmware/libnx plus forte.

Le **pool reste 1 557 / 4 853**. Les quatre owners AM ont désormais **11 slots `nullptr` physiques**, dont **10 pertinents HOS23** après `SelectApplicationLicense` hors-version. Aucun build PS5 ni validation console revendiqués.

### 2026-11-24 — AM common state : cmd15 HOS19 retourne un événement persistant

Vendor `6693426e3aca6318b7305a001205c14f216d9658` : `ICommonStateGetter` cmd15 (HOS19+) n'est plus un slot NULL. Les différences d'interface firmware prouvent zéro octet d'entrée, zéro octet de sortie et un handle de sortie. Lichii/Eglantine le classe comme réponse événement. Encore retourne désormais le `KReadableEvent` persistant `Applet::unknown_event`, déjà utilisé par les placeholders AM à contrat événementiel, sans le signaler artificiellement. **NULL → PARTIEL** : l'ABI/forme IPC est respectée, mais la condition firmware de signalement reste inconnue.

Un overlay `common_state_getter.h` est ajouté au manifest plutôt que de modifier implicitement la copie upstream. Le **pool reste 1 557 / 4 853** car PARTIEL reste dans le pool. Les quatre owners AM ont désormais **10 slots `nullptr` physiques**, dont **9 pertinents HOS23** après `SelectApplicationLicense` hors-version. Aucun build PS5 ni validation console revendiqués.

### 2026-11-24 — AM Starter lifecycle + ContentActionTable

Vendor `5fa1a189b96500929514986a86d2926fe2ff9f5c`.

**Starter lifecycle.** Le handler `IHomeMenuFunctions::LaunchStarter` est aligné sur le chemin `IApplicationCreator::CreateSystemApplication` réellement actif : l'`Applet` Starter est construit avec `is_application=true` et enregistré via `WindowSystem::TrackApplet(..., true)`. Cette correction est nécessaire parce que l'AppletId 0x04 est le **SystemApplication / starter**, pas un simple child library applet. Le champ `AppletType` existant n'est pas réinterprété ici : on corrige uniquement les deux marqueurs de lifecycle démontrés.

**CommonStateGetter cmd65.** `GetApplicationIdByContentActionName` n'est plus NULL. L'ABI libnx est respectée : buffer MapAlias d'entrée NUL-terminé et `u64` de sortie. Le handler refuse les callers autres que `AppletId::Starter`, ouvre le SystemData `0100000000000827` (`ContentActionTable`) depuis le NAND firmware, extrait son RomFS, cherche `table/<ContentActionName>/ApplicationId`, puis parse strictement l'ApplicationId ASCII hexadécimal. Les composants de chemin sont filtrés pour éviter toute traversée VFS. SwitchBrew documente que ContentActionTable est utilisé par AM et montre ce layout avec un exemple YouTube. Comme aucune seconde source publique ne décrit explicitement l'algorithme de sélection du sous-répertoire, classement conservateur **NULL → PARTIEL** jusqu'à preuve/validation complémentaire.

Le **pool global reste 1 557 / 4 853**. Les quatre owners AM ciblés ont maintenant **9 slots `nullptr` physiques**, dont **8 pertinents HOS23** après `SelectApplicationLicense` hors-version. Aucun build natif PS5 ni validation console revendiqués.

### 2026-11-24 — AM Overlay : Nintendo logo + startup movie depuis la partition Logo réelle

Vendor `694561edac085c49be40022a574d9e6481bb5448` : les commandes HOS18+ `IOverlayFunctions::GetApplicationNintendoLogo` (cmd40) et `GetApplicationStartupMovie` (cmd41) sont raccordées au contenu installé réel. Le dump IPC NS1 23.0.1 confirme pour chacune **0 entrée + buffer out type 6 + sortie u64 taille**. Encore résout l'ApplicationId avec la même identité que `GetApplicationIdForLogo`, ouvre le Program NCA via le `ContentProviderUnion` (avec repli base-title si nécessaire), puis lit respectivement `NintendoLogo.png` et `StartupMovie.gif` dans la partition Logo. Le buffer invité est borné avant copie ; absence de programme, partition, fichier ou capacité suffisante retourne une erreur au lieu d'un succès vide.

Ces ressources sont déjà les sources de vérité utilisées par `AppLoader_NCA::ReadLogo` / `ReadBanner` et par NS `GetApplicationLogoData`. **2 NULL → IMPL-SRC.**

**Pool restant = 1 555 / 4 853.** Dans les quatre owners AM ciblés, il reste **7 slots `nullptr` physiques**, dont **6 pertinents HOS23** après `SelectApplicationLicense` hors-version. Aucun build natif PS5 ni validation console revendiqués.

### 2026-11-24 — AM/NS : LaunchSystemApplet raccordé au backend qlaunch

Vendor `61637939907bcc513b7869936144ad083e712856` : NS `IApplicationManagerInterface::LaunchSystemApplet` (cmd304) et AM `IHomeMenuFunctions::LaunchSystemApplet` (cmd50) ne sont plus des slots NULL. Le backend NS utilise le ProgramId qlaunch standard `0100000000001000`, crée le processus invité via `CreateProcess`, matérialise un `AppletId::QLaunch` de type `SystemApplet`, applique les règles de focus qlaunch déjà utilisées par `AppletManager`, l'enregistre comme HomeMenu puis démarre le processus. Le PID réel est retourné par NS ; le wrapper AM l'ignore conformément au contrat firmware. Avant création, la liste des processus interdit un second qlaunch afin de ne pas déclencher l'assert de `WindowSystem::TrackApplet`.

SwitchBrew documente pour HOS20+ le défaut `ns.applet!system_applet_id_gen2 = 0100000000001000` et précise que HomeMenu cmd50 wrappe NS cmd304. **NULL → PARTIEL** pour les deux contrats : l'état NS qui sélectionne MaintenanceMenu et les overrides non-default de `system_applet_id_gen2` ne sont pas encore modélisés. Le **pool global reste 1 555 / 4 853**. Dans les quatre gros owners AM ciblés, il reste **6 slots `nullptr` physiques**, dont **5 pertinents HOS23** après `SelectApplicationLicense` hors-version. Aucun build natif PS5 ni validation console revendiqués.

### 2026-11-24 — AM SelfController : ProgramId screenshot relu depuis l’identité active

Vendor `b6d4bdf90dbce6fe685a09a578e064a77f6293c7` : `ISelfController::GetScreenShotProgramId` (cmd21) n'est plus NULL. Le dump IPC NS1 23.0.1 confirme zéro entrée et une sortie `u64`. Le handler relit sous le verrou de l'applet `screen_shot_identity.application_id`, valeur persistée par cmd15 `SetScreenShotAppletIdentityInfo`; lorsque cette identité n'a pas encore été surchargée, il retombe sur le `program_id` réel de l'applet. Cette règle est identique à celle déjà utilisée par le chemin Overlay logo/movie pour sélectionner la ressource de capture.

**1 NULL → IMPL-SRC. Pool restant = 1 554 / 4 853.** L'owner SelfController actif ne conserve plus que cmd45 `SetManagedDisplayLayerSeparationMode` et cmd46 `SetRecordingLayerCompositionEnabled` à NULL ; ils restent ouverts faute de backend VI de séparation/composition démontré. Aucun build natif PS5 ni validation console revendiqués.

### 2026-11-24 — AM AppletCommon : messages capture, Home Menu et core-usage guest

Vendor `aea632e0144cb4721a6469300fbdfda7d8d2f3eb` : quatre NULL de l'owner actif `IAppletCommonFunctions` sont raccordés avec l'ABI HOS23 confirmée par le dump 23.0.1.

- Cmd80/81 `SetHandlingCaptureButtonShort/LongPressedMessageEnabledForApplet` conservent les deux booléens dans l'état de l'applet. Ce ne sont pas des valeurs dormantes : `ICommonStateGetter::PerformSystemButtonPressingIfInFocus` relit exactement ces champs pour publier `DetectShortPressingCaptureButton` / `DetectLongPressingCaptureButton`. **2 NULL → IMPL-SRC.**
- Cmd310 `IsSystemAppletHomeMenu` retourne si l'applet courant est `AppletId::QLaunch`, l'identité Home Menu déjà utilisée par le `WindowSystem`. ABI HOS19+ : zéro entrée, bool u8 en sortie. **1 NULL → IMPL-SRC.**
- Cmd100 `SetApplicationCoreUsageMode` conserve le `u32` demandé dans `applet->application_core_usage_mode`. Encore ne raccorde pas encore cette politique au scheduler CPU invité/hôte : **NULL → PARTIEL**, sans modifier artificiellement l'ordonnancement PS5.

Références croisées : dump firmware NS1 23.0.1, Citron/Eden pour l'état core-usage et la détection QLaunch. **Pool restant = 1 551 / 4 853.** Aucun build natif PS5 ni validation console revendiqués.

### 2026-11-24 — AM LibraryAppletAccessor : enfant courant + sortie process réelle

Vendor `0ca719fa2b0c93e5cd77ec2e181f588bef34bc65` : deux slots HOS23 d'`ILibraryAppletAccessor` sont maintenant raccordés au runtime actif.

- Cmd110 `NeedsToExitProcess` suit l'ABI firmware (zéro entrée, bool u8) et retourne l'état réel `LifecycleManager::GetExitRequested() || Process::IsTerminated()`. Cette sémantique recoupe Napple et les chemins `RequestExit`/`Terminate` déjà actifs dans Encore. **1 NULL → IMPL-SRC.**
- Cmd81 `GetCurrentChildLibraryApplet` suit l'ABI HOS19+ (zéro entrée, interface `IAppletAccessor` en sortie). Encore relit le dernier `child_applets` réel de l'applet, puis l'expose via `IApplicationAccessor`, dont le sous-ensemble de commandes 0/1/10/20/25/30 correspond à l'interface firmware `IAppletAccessor`. En l'absence d'enfant, Encore renvoie provisoirement `ResultUnknown` car le résultat Horizon exact n'est pas documenté : **NULL → PARTIEL**, pas IMPL-SRC complet.

Le header réellement consommé reste `sources/eden/src/core/hle/service/am/service/library_applet_accessor.h` (aucun override header dans le manifeste), tandis que le CPP actif est l'overlay `encore-active/eden-backports`. **Pool restant = 1 550 / 4 853.** Aucun build natif PS5 ni validation console revendiqués.

### 2026-11-24 — AM ApplicationFunctions cmd310 : sortie application réelle, routage Lhub conservateur

Vendor `aaf3aaed779d10df89128073a9a3b304a69422a6` : HOS20+ cmd310 est nommé `RequestExitApplicationAndTryPopMessage` conformément à SwitchBrew et au SDK reconstruit. Le contrat HOS23 est consommé avec le payload 0x18 (`request_message_type` + UID) et l'objet `IStorage`. Le handler vérifie l'objet puis réutilise exactement le mécanisme de sortie déjà actif de `IApplicationAccessor::RequestExit` : si l'exit est verrouillé, publication `ExitRequested` + mise à jour de suspension ; sinon terminaison du processus invité.

Le routage du message vers Lhub/qlaunch n'est pas inventé : la forme interne de cette remise n'est pas documentée suffisamment pour sérialiser le storage dans le GeneralChannel sans risque. **NULL → PARTIEL**. Le **pool reste 1 549 / 4 853**, tandis que les quatre owners AM ciblés n'ont plus que **5 slots nullptr physiques**, dont **4 pertinents HOS23** après `SelectApplicationLicense` hors-version. Aucun build natif PS5 ni validation console revendiqués.

### 2026-11-24 — AM LibraryAppletSelfAccessor : événement GPU-error partagé

Vendor `80f4972be4e5bf4a16247a8393ccbf0420bfd96c` : `ILibraryAppletSelfAccessor::GetGpuErrorDetectedSystemEvent` (cmd130) retourne désormais le `KReadableEvent` réel `Applet::gpu_error_detected_event`, déjà utilisé par `IApplicationFunctions::GetGpuErrorDetectedSystemEvent`. Il n'y a ni nouvel événement parallèle ni signal artificiel : les deux interfaces observent la même source d'état GPU de l'applet. **1 NULL → IMPL-SRC.**

**Pool restant = 1 548 / 4 853.** Aucun build natif PS5 ni validation console revendiqués.

### 2026-11-24 — AM LibraryAppletAccessor : alignement des stubs firmware cmd110/cmd150

Vendor `eedfedbd8513a047ba393d48287c37dd196566cd` : la documentation firmware actuelle confirme que `NeedsToExitProcess` (cmd110) et `RequestForAppletToGetForeground` (cmd150) sont des stubs Horizon qui retournent une erreur. Le précédent cmd110 Encore, qui exposait avec succès l'état interne `ExitRequested/IsTerminated`, était donc trop permissif et est corrigé : il retourne maintenant `ResultUnknown` comme le firmware. Cmd150 passe de slot NULL au même rejet explicite, sans modifier le `WindowSystem`.

**Cmd110 : divergence corrigée, sans gain de compteur. Cmd150 : NULL → D. Pool restant = 1 547 / 4 853.** Aucun build natif PS5 ni validation console revendiqués.

### 2026-11-24 — AM AppletCommon : états VR curtain / température / batterie exposés

Vendor `b322c48fce30b49df1d49bfae041535bd60bb307` : `IAppletCommonFunctions` cmd60 `IsVrModeCurtainRequired`, cmd61 `IsSleepRequiredByHighTemperature` et cmd62 `IsSleepRequiredByLowBattery` ne sont plus des slots NULL. Les trois handlers relisent sous `Applet::lock` les états AM déjà présents (`vr_mode_curtain_required`, `sleep_required_by_high_temperature`, `sleep_required_by_low_battery`) et renvoient leur booléen réel.

Encore ne possède pas encore de producteur complet reliant ces états à un backend matériel PS5/thermique/batterie ni de gestion complète du rideau VR Horizon ; aucun faux capteur ni valeur forcée n'est ajouté. **3 NULL → PARTIEL.** Le **pool reste 1 547 / 4 853** car PARTIEL reste une dette. Aucun build natif PS5 ni validation console revendiqués.

### 2026-11-24 — AM AppletCommon cmd321 : hint GPU application accepté sans altérer le host

Vendor `43ccd9f0ad4d9563ed7a2cd9a4d36a29322ee48c` : `SetGpuTimeSliceBoostDueToApplication` (cmd321, HOS19+) est raccordé avec son ABI HOS23 réelle, un unique `u64` sans sortie. Comme `SetGpuTimeSliceBoost` et les autres hints AM déjà traités, ce réglage cible la politique de scheduling GPU Horizon ; Encore exécute le GPU invité via RADV/PS5 et ne doit pas traduire ce nombre en changement arbitraire du scheduler hôte. Le payload est donc consommé et accepté comme politique invitée sans effet host. **1 NULL → NOOP.**

**Pool restant = 1 546 / 4 853.** Aucun build natif PS5 ni validation console revendiqués.

### 2026-11-24 — AM LibraryAppletSelfAccessor : MovieTrimmer indisponible rejeté explicitement

Vendor `1bf7529e72295266f92beb180ae602ec9a954db4` : `CreateGameMovieTrimmer` (cmd100) n'est plus un slot NULL. Le contrat HOS23 réel est consommé (`u64` taille + copy-handle TransferMemory), puis Encore retourne une erreur AM explicite. Ce choix est causal : SwitchBrew documente que cmd100 est un wrapper de GRC `OpenGameMovieTrimmer`, et le runtime actif Encore conserve précisément `grc:c` cmd2 `OpenGameMovieTrimmer` à NULL, sans `IGameMovieTrimmer` ni encodeur/trimmer exposable. Aucun objet factice n'est créé.

**1 NULL → D. Pool restant = 1 545 / 4 853.** Aucun build natif PS5 ni validation console revendiqués.

### 2026-11-24 — AM AppletCommon : NamedChannels sans backend rejetés explicitement

Vendor `224bac056b368bf4edf3f0575de187d40d4edb76` : `OpenNamedChannelAsParent` (cmd90) et `OpenNamedChannelAsChild` (cmd91) ne sont plus des slots NULL. Le dump firmware NS1 23.0.1 confirme pour chacun **0x10 octets d'entrée** et une interface `IStorageChannel` en sortie. Encore consomme désormais exactement ces 16 octets via le dispatcher CMIF puis retourne une erreur explicite.

Ce rejet est volontaire : le runtime actif ne contient ni service IPC `IStorageChannel`, ni registre partagé de named channels parent/enfant. Réutiliser `AppletStorageChannel` local sans identité partagée fabriquerait une sémantique différente de Horizon. **2 NULL → D.**

**Pool restant = 1 543 / 4 853.** Aucun build natif PS5 ni validation console revendiqués.

### 2026-11-24 — AM SelfController : contrôles recording-layer rejetés tant que cmd44 reste partiel

Vendor `6a593a4466bf9b98220dfc0139239ae5d52c5437` : `SetManagedDisplayLayerSeparationMode` (cmd45) et `SetRecordingLayerCompositionEnabled` (cmd46) ne sont plus des slots NULL. Les handlers consomment leur ABI réelle (`u32 mode`, limité à 0/1 pour cmd45 ; booléen pour cmd46), puis retournent une erreur explicite.

Ce choix évite un faux succès : `DisplayLayerManager::CreateManagedDisplaySeparableLayer` (cmd44) retourne encore `recording_layer_id = 0` et ne crée qu'un managed layer normal. Le VI actuel sait gérer plusieurs layers, mais le chemin de présentation Vulkan PS5 compose encore la liste complète sans filtrer le stack `Default`; matérialiser naïvement une recording layer pourrait donc la rendre visible à l'écran. **2 NULL → D** jusqu'au correctif causal cmd44 + filtrage de présentation.

**Pool restant = 1 541 / 4 853.** Aucun build natif PS5 ni validation console revendiqués.

### 2026-11-24 — AM ApplicationCreator : absence de launch-request queue traitée explicitement

Vendor `8aeb5a99bc36d5a01a1cd409bb24d8bed990ab05` : `IApplicationCreator::PopLaunchRequestedApplication` (cmd1) ne reste plus un slot NULL. L'ABI réelle ne prend aucune entrée et doit retourner un `IApplicationAccessor`. Encore ne possède toutefois aucune file AM correspondante : `AppletManager::m_pending_process` est exclusivement le processus injecté par le frontend au bootstrap et `SetWindowSystem()` le consomme immédiatement pour créer l'applet initial ; le réutiliser ici exposerait à tort l'application courante ou un objet déjà consommé.

Le handler retourne donc une erreur explicite sans fabriquer d'accessor. **1 NULL → D. Pool restant = 1 540 / 4 853.** Aucun build natif PS5 ni validation console revendiqués.

### 2026-11-24 — AM LibraryAppletAccessor : foreground request raccordé au lifecycle réel

Vendor `829c7964df4ea7dd6e16cb666e139561d920f737` : `RequestForLibraryAppletToGetForeground` (cmd80, HOS19+) n'est plus NULL. Encore réutilise l'état déjà actif du child library applet : le handler vérifie le `WindowSystem`, passe `window_visible=true` via `RequestAppletVisibilityState`, puis l'update récursif existant de `WindowSystem::UpdateAppletStateLocked` recalcule visibilité, foreground hérité du caller, suspension, HID et z-order. Ce chemin couvre notamment `AllForegroundInitiallyHidden`, créé avec `window_visible=false`.

Une implémentation indépendante (Napple) modélise elle aussi cmd80 comme une demande de foreground sur l'applet existant, sans création d'un nouveau root. **1 NULL → IMPL-SRC. Pool restant = 1 539 / 4 853.** Aucun build natif PS5 ni validation console revendiqués.

### 2026-11-24 — AM WindowController : CreateWindow aligné sur le stub firmware

Vendor `f1e8c0b32320e6c08dd662b9e5f5d1ac71808226` : `IWindowController::CreateWindow` (cmd0) ne reste plus un slot NULL. SwitchBrew documente le contrat comme **entrée u32 + sortie IWindow**, mais indique que le firmware le stubbe et retourne une erreur. L'overlay actif consomme donc le `u32 window_flags` et retourne `ResultUnknown`, sans créer d'interface vide factice ni modifier VI/WindowSystem. **1 NULL → D.**

**Pool restant = 1 538 / 4 853.** Aucun build natif PS5 ni validation console revendiqués.

### 2026-11-24 — correction de provenance WindowController

Vendor `a12ddefce7725faeeb98495ceb8ccb8cf3cd5f8f` : aucune modification runtime. Les SHA256 du nouvel overlay `window_controller.{cpp,h}` ajoutés avec le correctif `CreateWindow` ont été recalculés avec l'algorithme SHA-256 de référence et corrigés dans `encore-active/eden-backports/manifest.json`, y compris les empreintes upstream. Vérification croisée sur `library_applet_accessor.cpp` : l'empreinte recalculée correspond exactement à celle déjà enregistrée. **Pool inchangé : 1 538 / 4 853.**

### 2026-11-24 — AM ApplicationAccessor : ApplicationLaunchRequestInfo réel

Vendor `001fea6ade91e82ec360e5bb2197f130680d6d6a` : `IApplicationAccessor::GetApplicationLaunchRequestInfo` (cmd124, HOS6+) est raccordé avec le struct `nn::applet::ApplicationLaunchRequestInfo` de **0x10 octets**. SwitchBrew établit les valeurs initiales Horizon : `{3,3,0}` pour `CreateApplication`, `{0,0,0}` pour `CreateSystemApplication`. Encore ne fabrique des `IApplicationAccessor` que dans ces deux chemins ; le handler lit donc l'`AppletId` conservé par l'objet, retourne les valeurs correspondantes et rejette explicitement tout type inattendu.

Les nouveaux overlays `application_accessor.{cpp,h}` ont leurs empreintes active/upstream recalculées et revérifiées contre le manifeste. **1 NULL → IMPL-SRC. Pool restant = 1 537 / 4 853.** Aucun build natif PS5 ni validation console revendiqués.

### 2026-11-24 — AM CradleFirmwareUpdater : contrats HOS23 indisponibles rejetés explicitement

Vendor `a06bccfd645add1c7d06063f5abfa8e1ba525c04` : le dump Applet_Manager 23.0.1 montre que les anciennes étiquettes Eden des cmd4/cmd5 ne correspondent plus au contrat HOS23. Cmd4 est `GetUpdateDeviceStatusChangeEvent` avec **0x10 octets de sortie** ; cmd5 est `GetUpdateProgress2` sans entrée/sortie. Encore cible HOS23 et ne possède aucun firmware/backend de dock Switch sur PS5 : les deux commandes consomment désormais leur ABI réelle puis retournent une erreur AM explicite, sans inventer progression, état ou événement.

Les overlays `cradle_firmware_updater.{cpp,h}` sont épinglés avec empreintes active/upstream revérifiées. **2 NULL → D. Pool restant = 1 535 / 4 853.** Aucun build natif PS5 ni validation console revendiqués.

### 2026-11-24 — AM DisplayController : transition buffer absent rejeté sans alias capture

Vendor `a520a7e9c054b25f02dfb2d0887bca127cb871ef` : `IDisplayController::ClearAppletTransitionBuffer` (cmd21) consomme désormais son ABI Horizon réelle, un `u32` RGBA8, puis retourne une erreur explicite. Le backend VI actif possède trois slots de capture et des slots de présentation, mais aucun AppletTransitionBuffer dédié ; réutiliser un slot capture aurait corrompu la sémantique observable et potentiellement l'image. **1 NULL → D. Pool restant = 1 534 / 4 853.** Aucun build natif PS5 ni validation console revendiqués.

### 2026-11-24 — AM LibraryAppletSelfAccessor cmd90 : launch same-title + UserChannel réel

Vendor `21bf94d43f07fcf66b37a6be82fb16b1099adaff` : `CreateApplicationAndPushAndRequestToLaunch` (cmd90) n'est plus un slot NULL. SwitchBrew le décrit comme **ApplicationId + IStorage**, similaire à `CreateApplicationAndPushAndRequestToStart`. Le chemin actif récupère l'application principale, valide l'ApplicationId contre son base-title, préserve les launch parameters existants de la library applet, y pousse le storage reçu, publie le UserChannel système puis appelle le callback `ExecuteProgram(program_index)` déjà utilisé par les transitions ApplicationInitiated.

Le cross-title reste explicitement rejeté : créer directement un second Applet Application violerait l'invariant `WindowSystem::TrackApplet` (`m_application == nullptr`). **NULL → PARTIEL** ; pool global **inchangé à 1 534 / 4 853**. Aucun build natif PS5 ni validation console revendiqués.

### 2026-11-24 — AM LibraryAppletSelfAccessor cmd140 : réservation mémoire conservée

Vendor `76b7356cbc63eae67ff7e73a66fc655ce1896b6d` : `SetApplicationMemoryReservation` (cmd140) n'est plus NULL. Le contrat vérifie qu'une Application principale existe et que son processus est vivant, refuse les valeurs non alignées sur `0x1000`, puis conserve la réservation demandée sur l'état de l'Applet principal. Aucun effet n'est appliqué à l'allocateur PS5 tant qu'un backend de réservation Horizon fidèle n'existe pas. **NULL → PARTIEL** ; pool global **inchangé à 1 534 / 4 853**. Aucun build natif PS5 ni validation console revendiqués.

### 2026-11-24 — AM LibraryAppletSelfAccessor cmd18 : destination de retour réelle

Vendor `d1b05d1e94eed35bc6d35f5f9db5d99156f4e5b5` : `GetNextReturnDestinationAppletIdentityInfo` (cmd18, HOS4+) ne reste plus NULL. Le dump firmware NS1 23.0.1 confirme **0 entrée + 0x10 octets de sortie** (`AppletIdentityInfo`). SwitchBrew décrit `ExitProcessAndReturn` comme un retour vers le titre qui a lancé la LibraryApplet ; Encore conserve exactement cette relation via `Applet::caller_applet`, déjà utilisée par `GetCallerAppletIdentityInfo` et la caller stack. Cmd18 réutilise donc cette même identité, avec le fallback qlaunch déjà établi quand aucun caller n'existe.

**1 NULL → IMPL-SRC. Pool restant = 1 533 / 4 853.** Dans les overlays AM actifs il reste **6 slots `nullptr` physiques**, dont **5 pertinents HOS23** après `SelectApplicationLicense` hors-version. Aucun build natif PS5 ni validation console revendiqués.

### 2026-11-24 — AM ApplicationAccessor cmd200 : soft reset non supporté rejeté explicitement

Vendor `72b6186f2d1248a332d580b7727e6161a930ca09` : `RequestApplicationSoftReset` (cmd200, HOS10+) ne reste plus NULL. Le contrat firmware est sans entrée/sortie. Encore ne possède toutefois aucun backend AM de soft reset : `WindowSystem::RestartAppletProcessLocked` est une primitive privée réservée au winding/unwind et réinitialise des états spécifiques de ce protocole. La réutiliser ici ferait passer un relaunch différent pour un soft reset Horizon.

Le handler consomme donc la commande et retourne une erreur explicite sans modifier le processus invité. **1 NULL → D. Pool restant = 1 532 / 4 853.** Dans les overlays AM actifs il reste **5 slots `nullptr` physiques**, dont **4 pertinents HOS23** après `SelectApplicationLicense` hors-version. Aucun build natif PS5 ni validation console revendiqués.

### 2026-11-24 — AM Overlay : contrats HOS23 cmd60/71/75 enregistrés

Vendor `c9e6af612c60b047ed43de57d2465fe18b8df7cf` : le dump Applet_Manager 23.0.1 expose trois contrats Overlay non documentés sémantiquement : cmd60 (**bool u8 → void**), cmd71 (**void → void**) et cmd75 (**void → u64**). Cmd60 était encore un slot NULL ; cmd71 et cmd75 n'étaient même pas enregistrées dans la table active. Les trois commandes sont maintenant dispatchées avec leur ABI exacte et retournent une erreur explicite, sans modifier d'état invité ni prétendre connaître leur effet firmware. Cmd75 initialise la sortie à zéro uniquement par sûreté de sérialisation avant le retour d'erreur.

**Cmd60 : 1 NULL → D. Cmd71/cmd75 : commandes HOS23 absentes de table → rejets explicites hors lignes distinctes du catalogue historique. Pool restant = 1 531 / 4 853.** Il ne reste plus que **3 slots `nullptr` HOS23 pertinents** dans les overlays AM actifs : `GetWakeupCount`, `SetHidInputMagnificationForApplication`, `GetLaunchRequiredTick`. Aucun build natif PS5 ni validation console revendiqués.

### 2026-11-24 — FSP IFile/IFileSystem : range IPC + QueryEntry dispatch

Vendor `285b0c8646cfc8d7331ca63758c4d34161460bac` : les trois slots FSP compacts `IFile::OperateRange` (cmd5), `OperateRangeWithBuffer` (cmd6) et `IFileSystem::QueryEntry` (cmd15) ne tombent plus dans le dispatcher inconnu.

- **OperateRange** suit le contrat Atmosphère `FileInterfaceAdapter` pour un fichier local : sortie `FileQueryRangeInfo` 0x40 initialisée, `Invalidate` est un no-op valide sur le VFS hôte sans cache bloc invité, et `QueryRange` valide l'offset/taille puis retourne une information neutre (aucun AES-CTR/speed-emulation sur le fichier hôte). Les autres op-id de cmd5 suivent le comportement de l'adapter Horizon et ne sont pas forwardés. **NULL → IMPL-SRC.**
- **OperateRangeWithBuffer** consomme l'ABI HOS12+ exacte (buffers non-secure + op-id/offset/taille), couvre `Invalidate` et `QueryRange`, mais rejette explicitement les opérations lazy-load/unprepared qu'Encore ne modélise pas. **NULL → PARTIEL.**
- **QueryEntry** consomme l'ABI complète (path pointer + in/out buffers + `QueryId`) et délègue au backend FSA existant, lequel retourne actuellement `FS::ResultNotImplemented` plutôt que de fabriquer un résultat. **NULL → D.**

Références : Horizon IPC definitions et Atmosphère `fssrv_filesystem_interface_adapter.cpp` / local filesystem. **Pool restant = 1 529 / 4 853.** Aucun build natif PS5 ni validation console revendiqués.

### 2026-11-24 — NIFM HOS18 : network emulation / rewrite désactivés explicitement

Vendor `64fe70db980b3f60dd9fce1175a13f0ce3435b52` : cinq slots HOS18+ de `IGeneralService` ne restent plus NULL. Encore ne possède aucun moteur NIFM d'émulation réseau, aucun profil d'émulation actif et aucun moteur de rewrite de paquets : `IsNetworkEmulationFeatureEnabled` (cmd45) et `IsRewriteFeatureEnabled` (cmd50) retournent donc **false avec succès**, ce qui reflète l'état réel du runtime. `SelectActiveNetworkEmulationProfileIdForDebug` (cmd46), `CreateRewriteRule` (cmd51) et `DestroyRewriteRule` (cmd52) consomment leur ABI HOS23 puis retournent une erreur explicite, sans installer de règle ni modifier la pile réseau.

Le contrat HOS23 de cmd51 reste respecté : bool en entrée + buffer de règle, avec taille observée mais contenu non interprété puisque la feature est désactivée. Le manifest actif a été contrôlé après correction de provenance : `nifm.cpp` porte l'empreinte `8e475728...` / 62075 octets et l'ancienne empreinte FSP a été restaurée.

**5 NULL → 2 IMPL-SRC/NOOP + 3 D. Pool restant = 1 524 / 4 853.** `GetNetworkAccessStatus` reste volontairement NULL : le payload 0x100 est connu mais les valeurs sémantiques du champ `status` ne sont pas suffisamment prouvées pour assimiler le zéro SDK à un état connecté. Aucun build natif PS5 ni validation console revendiqués.

### 2026-11-24 — NIFM : contrats sans backend rejetés explicitement

Vendor `2493221582e7a41528c53546bed61180035fec4e` : cinq slots NIFM supplémentaires ne tombent plus sur `nullptr`. `IRequest::GetAdditionalInfo` (cmd22) consomme le contrat HOS23 mais rejette l'opaque 0x410 faute de modèle. Côté `IGeneralService`, `GetTelemetorySystemEventReadableHandle` (31), `GetTelemetryInfo` (32) et `GetAllowedChannels` (38) retournent une erreur explicite : Encore n'a ni producteur de télémétrie NIFM ni source réglementaire fiable des canaux Wi-Fi. `NotifyApplicationSuspended` (39) consomme le PID u64 puis rejette l'opération, faute de backend NIFM par application/sleep.

Aucune valeur de télémétrie, aucun canal et aucun signal d'événement ne sont fabriqués. **5 NULL → D. Pool restant = 1 519 / 4 853.** Aucun build natif PS5 ni validation console revendiqués.

### 2026-11-24 — HID System Server : lot matériel/admin Switch rejeté explicitement

Vendor `2c0ff436b2798f6c028b504b56d15a158794aa40` : **146 slots `nullptr` physiques** de `hid:sys` sont désormais dispatchés vers un rejet commun explicite pour les familles sans backend PS5 applicable : NFC/IR/MCU bas niveau, calibrations six-axis/analog stick, firmware contrôleur/USB, `hidbus` système, button-config/custom mapping système, maintenance touchscreen et surfaces de support associées. Le chemin d'entrée manette normal, les ressources Npad actives, vibration, HID registration et les handlers déjà fonctionnels ne sont pas redirigés.

Le handler renvoie une erreur au lieu d'un succès factice ; aucune configuration Switch n'est appliquée au matériel PS5. L'ID 230 est également renommé `AcquireIrSensorEventHandle`, corrigeant l'écart de nom historique. Croisement avec l'annexe 4 853 : **52 lignes NULL + 1 ABI-DIFF** sont réellement dans le pool historique ; les **93 autres commandes physiques** ne figurent pas comme lignes distinctes du miroir historique et n'altèrent donc pas artificiellement le dénominateur.

**Pool restant = 1 466 / 4 853.** Aucun build natif PS5 ni validation console revendiqués.

### 2026-11-24 — NS ApplicationManager : delivery/update Nintendo non disponibles rejetés en lot

Vendor `8f2137659278d52c71825939501b7aad466edc3e` : **57 slots `nullptr` physiques** de `IApplicationManagerInterface` sont dispatchés vers une erreur explicite lorsqu'ils dépendent d'infrastructures absentes d'Encore PS5 : demandes de mise à jour/téléchargement, enregistrement GameCard/gold points, system/application delivery, background-update/download tasks, promotions et eLicense/availability. Aucun téléchargement, droit, livraison ou promotion Nintendo n'est simulé et aucun état local d'installation n'est modifié.

Le chemin de chargement local des contenus, les records d'application, NCA/FSP, GameCard local et les fonctions déjà implémentées ne sont pas redirigés. Croisement avec le catalogue historique : **34 lignes NULL** sont réellement dans le pool ; 10 anciennes lignes directes `ns:am` sont déjà HORS-VERSION pour HOS23 et 13 commandes physiques récentes ne sont pas des lignes distinctes du miroir 4 853.

**Pool restant = 1 432 / 4 853.** Aucun build natif PS5 ni validation console revendiqués.

### 2026-11-24 — PCTL : pairing/account/synchronisation non disponibles rejetés en lot

Vendor `b162bfe9925eba2e1a11a4bee4acad1218a62876` : les **43 slots `nullptr` physiques** restants de l'overlay `IParentalControlService` sont désormais dispatchés vers une erreur explicite pour les surfaces administratives sans backend Encore : restricted-features/safety settings avancés, inquiry/master-key, pairing-account/post-events, pairing/synchronisation asynchrones Nintendo, alarmes/événements système et commandes HOS récentes associées. Les contrôles de permission déjà implémentés et utilisés par les jeux, les états de restriction et les play-timer handlers existants ne sont pas remplacés.

Croisement avec le catalogue 4 853 : **26 lignes NULL** sont réellement dans le pool historique ; 17 commandes physiques récentes n'y sont pas des lignes distinctes. Aucun compte Nintendo, pairing distant ou synchronisation n'est simulé.

**Pool restant = 1 406 / 4 853.** Aucun build natif PS5 ni validation console revendiqués.

### 2026-11-24 — ACC : Nintendo Account / OAuth / device-auth rejetés en lot

Vendor `993a5e9ae75aa37f92527cc99d2d26bdcae54dfb` : **191 slots `nullptr` physiques** sont fermés dans 14 sous-interfaces exclusivement réseau/authentification Nintendo : managers BAAS système/admin, floating/guest registration, authorization/OAuth/linkage/user-registration, network-service-license async, `dauth:0`/`dauth:o`, `acc:aa` et leurs résultats async. Chaque commande reçoit une erreur explicite lorsque le backend Nintendo Account, OAuth, licence réseau ou device-auth n'existe pas.

Les surfaces locales critiques `GetUserCount`, `ListAllUsers`, `GetProfile`, sélection d'utilisateur, thumbnails et profil local restent intactes. Croisement conservateur avec le catalogue 4 853 : **80 lignes NULL** sortent du pool ; **27 lignes** correspondantes étaient déjà HORS-VERSION et **3 AMBIGU** restent volontairement dans le pool.

**Pool restant = 1 326 / 4 853.** Aucun build natif PS5 ni validation console revendiqués.

### 2026-11-24 — FSP : maintenance/transfert système indisponibles rejetés en lot

Vendor `d1b965f49a76649392576551be724c0ee642d809` : **43 slots `nullptr` physiques** de `fsp-srv` sont raccordés au handler production `UnsupportedDebugCommand` pour les surfaces hors chemin normal des jeux : format/repair SD/save, save-data transfer/cloud, device/detection notifiers, corruption/padding, access-failure recovery, racines host/debug, update partitions, diagnostics/log/debug et BIS wipe. Le handler renvoie `ResultNotSupported`.

Les chemins `OpenFileSystem`, `OpenSaveDataFileSystem`, `OpenDataStorage*`, GameCard local et opérations save normales restent intacts. Croisement avec le catalogue 4 853 : **32 lignes NULL** sortent du pool.

**Pool restant = 1 294 / 4 853.** Aucun build natif PS5 ni validation console revendiqués.

### 2026-11-24 — HID System Server : résidu système entièrement fermé

Vendor `ef32954266481977a0c9c5eef2ff52f637fa45bb` : les **39 derniers slots `nullptr`** de `hid:sys` sont raccordés au rejet matériel explicite déjà utilisé pour les familles Switch sans backend PS5. Cela couvre les événements Home/Sleep/Capture système, Npad system/UI, unique/abstracted-pad, Joy-Con rail/handheld, play-report, connexion Bluetooth/USB et propriétés système restantes. Le service applicatif `hid`, l'entrée jeu, vibration et Npad runtime restent inchangés.

Croisement catalogue 4 853 : **21 lignes NULL** sortent du pool. `hid:sys` ne contient plus de slot `nullptr` actif dans l'overlay NS1.

**Pool restant = 1 273 / 4 853.** Aucun build natif PS5 ni validation console revendiqués.

### 2026-11-24 — NS : administration destructive système rejetée en lot

Vendor `3a1bbc0ffb3e3b8b4472997fb2f45e05908ee5de` : **54 slots `nullptr` physiques** supplémentaires de `IApplicationManagerInterface` sont fermés sur des surfaces d'administration système hors gameplay : factory-reset, suppression/cleanup d'entités et saves système, vérification/maintenance d'applications, format/gestion SD, event-log, cleanup de tâches, qualification debug, device-lock, visibilité icône/titre et bascules GameCard/local-share. Le handler renvoie explicitement une erreur lorsque le backend système Nintendo correspondant n'existe pas.

Les commandes de lancement d'applications/applets, records/control data, contenus installés et chemins locaux de boot restent inchangés. Croisement catalogue 4 853 : **19 lignes NULL** sortent du pool ; les autres lignes correspondantes étaient déjà HORS-VERSION ou D.

**Pool restant = 1 254 / 4 853.** Aucun build natif PS5 ni validation console revendiqués.

### 2026-11-24 — BTM + USB : backends matériels Switch absents rejetés en bloc

Vendor `5a0460f5a51a239ed0a9d9db806cb8bae88f645d` : **64 slots `nullptr` BTM** et **69 slots USB** sont remplacés par des rejets explicites lorsque l'invité demande le matériel Bluetooth/BLE/GATT ou USB device/host/power-delivery propre à la Switch. BTM conserve ses événements offline, listes vides et bascules radio déjà modélisés ; les commandes sans backend matériel retournent désormais une erreur. USB conserve ses managers de session, mais les opérations endpoint/interface/cradle/power/quirk sans périphérique invité retournent une erreur explicite. L'include IPC BTM est déclaré directement, sans dépendance transitive.

Aucun service `hid` de gameplay, socket BSD/DNS ou audio n'est modifié. Croisement catalogue 4 853 : **38 NULL BTM + 16 NULL USB = 54 lignes** sortent du pool ; une ligne BTM était déjà HORS-VERSION.

**Pool restant = 1 200 / 4 853.** Aucun build natif PS5 ni validation console revendiqués.

### 2026-11-24 — NS : résidu download/apply-delta/version-list rejeté

Vendor `1f2e5c4d2a5243d850b855969474786e281d08d2` : **31 slots `nullptr` physiques** supplémentaires de `IApplicationManagerInterface` sont raccordés au rejet de backend plateforme pour les opérations de téléchargement/application-delta/version-list, tâches background, auto-update, notification-task et droits préachetés. Les chemins locaux de contenu installés, tickets locaux, launch-rights, records, GameCard et lancement d'application restent inchangés.

Croisement catalogue 4 853 : **30 lignes NULL** sortent du pool ; 15 anciennes lignes `ns:am` homologues sont déjà HORS-VERSION.

**Pool restant = 1 170 / 4 853.** Aucun build natif PS5 ni validation console revendiqués.

### 2026-11-24 — NS/FSP : maintenance locale résiduelle rejetée

Vendor `a64bcf8c38473234474aca49b4013ed3617e0dec` : **30 slots NS** de maintenance/admin locale (entity cleanup/move, SD cleanup, auto-delete, crash-report/thread-dump, network-account unregister, application-control cache administration, task-status cleanup, preinstalled/visibility flags, shutdown/system-seed, notifications et rights-cache invalidation) plus **5 slots FSP** host/save-delete sont raccordés aux rejets explicites existants. Les lectures/écritures SaveData normales, OpenFileSystem, rights lookup, content metadata, tickets et lancement d'application restent inchangés.

Croisement catalogue 4 853 : **35 lignes NULL** sortent du pool.

**Pool restant = 1 135 / 4 853.** Aucun build natif PS5 ni validation console revendiqués.

### 2026-11-24 — services online Nintendo : NIM/Friends/ERPT/NPNS/EUPLD fermés avec provenance réversible

Vendor `dc460d59824f532705781f8df8e72d951ebbd446` : cinq nouveaux overlays shipping couvrent uniquement les slots `nullptr` des backends réseau Nintendo absents, en conservant tous les handlers déjà implémentés. Le lot remplace **412 slots physiques** : NIM **253**, Friends **90**, ERPT **15**, NPNS **43**, EUPLD **11**. Chaque slot rejeté retourne une erreur explicite via un handler local commun ; aucun téléchargement, friend/social backend, télémétrie distante, push Nintendo ou upload d'erreur n'est simulé.

Le moteur ajoute `tools/fixtures/ns1-online-service-backports-reverse.json` et étend `install-vendored-eden-backports.py --replay` : pour les cinq sources, le replay vérifie les tailles/hashes avant-après, le nombre exact de remplacements par classe, retire les méthodes/includes ajoutés puis exige une égalité **octet pour octet** avec Eden épinglé. Le pin Eden n'est pas modifié et aucune dérive arbitraire n'est autorisée.

Croisement catalogue 4 853 : NIM **56 NULL**, Friends **23 NULL**, ERPT **11 NULL**, NPNS **15 NULL**, EUPLD **11 NULL**, soit **116 lignes** sorties du pool. Les lignes déjà HORS-VERSION ne sont pas décomptées.

**Pool restant = 1 019 / 4 853.** Aucun build natif PS5 ni validation console revendiqués.

### 2026-11-24 — BPC : matériel power/RTC Switch absent rejeté explicitement

Vendor `95313ec1089b64f884abe3106eb2996ff74a5f90` : l'overlay actif `bpc.cpp` ne contient plus aucun slot `nullptr`. Les **34 slots physiques** des interfaces `bpc`, `bpc:r`, `bpc:c`, `bpc:b`, `bpc:w` et `bpc:ams` sont dispatchés vers un rejet explicite commun. Encore ne relaie pas un shutdown/reboot Horizon vers la PS5, ne fabrique pas d'état AC/wakeup/power-button et n'émule pas le RTC matériel ou les timers de réveil Switch.

Croisement avec l'annexe 4 853 et la cible HOS23 : **12 lignes NULL** restent réellement comptées dans le pool (7 `bpc` + 5 `bpc:r`) ; les anciens wakeup-timer/sleep-button sont déjà HORS-VERSION et ne sont pas redécomptés. **12 NULL → D. Pool restant = 1 007 / 4 853.** Aucun build natif PS5 ni validation console revendiqués.


### 2026-11-24 — SET:CAL : owner shipping restauré et commandes factory non qualifiées fermées

Vendor `9b2333d972bca1fd03814d58fcc7ae9f4834820e` : `factory_settings_server.cpp/.h` sont désormais des owners explicites de `encore-active/eden-backports`. Les copies `sources/eden` ont été remises aux blobs Eden épinglés ; les lectures CAL0 non sensibles déjà développées sont conservées dans l'overlay réellement installé par `install-vendored-eden-backports.py`. Cela supprime le risque qu'un changement uniquement présent dans la copie de référence soit dormant au build natif.

Les **20 slots `nullptr` physiques** restants de `IFactorySettingsServer` sont dispatchés vers `RejectUnsupportedFactoryCommand`, qui renvoie une erreur explicite. Les deux setters factory 10/11 et les getters 14–21/24–31 de certificats/clefs ECI, eTicket, SSL, GameCard et amiibo ne fabriquent donc aucune donnée et n'exposent aucun layout non qualifié. Les deux slots physiques 42/43 sont fermés par la même politique mais ne constituent pas des lignes distinctes dans le miroir historique 4 853.

Le replay moteur vérifie les hashes SHA-256 et tailles exactes avant/après des deux owners, exige **20** raccords au handler de rejet et garde le pin Eden immuable. Croisement catalogue : **18 NULL → D. Pool restant = 989 / 4 853.** Aucun build natif PS5 ni validation console revendiqués.

### 2026-11-24 — SET:FD : surface firmware-debug fail-closed

Vendor `fb8384b5673beeeed268ee38fa021421ac51061f` : les **11 slots `nullptr` physiques** de `IFirmwareDebugSettingsServer` sont désormais dans un owner `eden-backports` shipping et dispatchés vers `RejectUnavailableDebugSetting`. Horizon n'expose `set:fd` qu'en mode développement ; Encore ne simule donc ni Web Inspector, ni hostfs debug, ni listes d'hôtes SSL, ni configuration HTTP auth, ni mutation des réglages firmware debug sur le matériel PS5.

Le replay vérifie les deux blobs CPP/header avant/après et exige exactement 11 raccords au rejet. Croisement du miroir historique 4 853 : **9 NULL → D** (cmd2/3/4/10/11/20/21/22/23). Les cmd24 et 27, ajoutées en HOS20+/21+, sont couvertes physiquement mais ne sont pas des lignes distinctes de l'annexe historique. **Pool restant = 980 / 4 853.** Aucun build natif PS5 ni validation console revendiqués.

### 2026-11-24 — BGTC : owner shipping restauré, scheduler/sleep absents fail-closed

Vendor `6e2212b52d96463d74d17e90e260e372eee7aa80` : `bgtc.cpp/.h` deviennent des owners explicites de `encore-active/eden-backports` et les copies `sources/eden` sont remises aux blobs Eden épinglés. Cette correction de provenance rend réellement shipping les quatre handlers déjà écrits auparavant : `IsInHalfAwake=false`, `IsInFullAwake=true`, et les deux politiques de sommeil réseau à `false`. Les statuts historiques cmd4/cmd6 (IMPL-SRC) et cmd102/cmd103 (PARTIEL) ne sont donc pas redécomptés.

Les **17 slots `nullptr` physiques** restants sont fermés explicitement : **12** dans `ITaskService` et **5** dans `bgtc:sc`. Encore ne possède ni scheduler de tâches Horizon, ni événements de planification, ni transition half-awake, ni contrôle du sommeil PS5 par BGTC ; ces commandes renvoient donc une erreur au lieu d'un succès ou événement fictif. Les cmd16 et 200 sont couverts physiquement mais n'existent pas comme lignes distinctes dans le miroir historique.

Croisement 4 853 : `bgtc:t` **10 NULL → D** et `bgtc:sc` **5 NULL → D**, soit **15 lignes** sorties du pool. **Pool restant = 965 / 4 853.** Aucun build natif PS5 ni validation console revendiqués.

### 2026-11-24 — BCAT : cache local shipping, scheduler/push absents fail-closed

Vendor `c2063ba7d1a8acc7596fff3bbde994e9de9bb4be` : `bcat_service.cpp/.h` sont désormais des owners `eden-backports` explicites. La copie `sources/eden` est remise aux blobs Eden épinglés, ce qui rend réellement shipping le NOOP documenté de `RegisterSystemApplicationDeliveryTasks` déjà comptabilisé auparavant. Les chemins locaux existants restent intacts : `RequestSyncDeliveryCache`, `RequestSyncDeliveryCacheWithDirectoryName`, `SetPassphrase` et `ClearDeliveryCacheStorage`.

**19 slots physiques** sans backend sont raccordés à un rejet explicite : annulation non supportée, notifiers/suspension, enregistrement/gestion de delivery tasks, listes de tâches/livraisons, subscription status et push log. Les noms 30200/30201 sont corrigés vers `RegisterDeliveryTask` / `UnregisterDeliveryTask`, conformément à SwitchBrew. Les commandes 20410/30101/30102/30210/90101/90301 sont aussi fermées physiquement mais ne comptent pas comme lignes historiques distinctes.

Les commandes **20100/20101 restent volontairement NULL** : le backend sait synchroniser un titre, mais le contrat HOS3+ ajoute 8 octets dont la sémantique n'est pas encore qualifiée ; elles ne sont donc pas rejetées artificiellement. Croisement 4 853 : **11 NULL → D + 2 ABI-DIFF → D**, soit **13 entrées sorties du pool. Pool restant = 952 / 4 853.** Aucun build natif PS5 ni validation console revendiqués.

### 2026-11-24 — MiiImg : base vide réellement shipping, backend fichier fail-closed

Vendor `6bcf1cb61b190766a459334ee462fb74f978e5f2` : `mii.cpp` devient un owner `eden-backports` explicite et sa copie `sources/eden` revient au blob Eden épinglé. Les handlers déjà écrits `Reload`, `GetCount=0`, `IsEmpty=true` et `IsFull=false` rejoignent ainsi le runtime natif au lieu de rester dans une copie de référence. `Initialize` reste un NOOP cohérent avec une base d'images vide.

Les **9 commandes fichier/image** encore à `nullptr` — GetAttribute, LoadImage, AddOrUpdateImage, DeleteImages, DeleteFile, DestroyFile, ImportFile, ExportFile, ForceInitialize — sont raccordées à un rejet explicite tant qu'Encore n'a pas de backend fichier Mii Horizon. Les deux NULL du service Mii principal (`Import`/`Export`) restent volontairement intacts : ils ne font pas partie de `miiimg`.

Croisement 4 853 : **9 NULL → D**. **Pool restant = 943 / 4 853.** Aucun build natif PS5 ni validation console revendiqués.

### 2026-11-24 — PDM notify : journal d'activité absent, notifications locales explicites

Vendor `506bcfd7c74cf131029abeba02a3e37e793dd8c7` : dans l'owner shipping existant `src/core/hle/service/ns/ns.cpp`, les commandes historiques `pdm:ntfy` **0/2/3/4/6/7** sont raccordées à `AcceptLocalPlayLogNotification`. Encore ne persiste pas le journal PDM Horizon ; ces notifications sans payload invité sont donc acquittées localement sans fabriquer de `PlayEvent`, statistique ou historique. La commande debug 5 conserve son rejet explicite existant.

Les commandes plus récentes **8/9/20/30/100/101** restent volontairement `nullptr` : elles ne sont pas utilisées pour gonfler le compteur sans qualification ABI. Le replay moteur exige exactement le predecessor généré `a127ff1b…` (5478 octets), le successor `4af9b510…` (6151 octets), six raccords au NOOP local et les six slots plus récents encore ouverts.

Croisement du miroir 4 853 : **6 NULL → NOOP**. **Pool restant = 937 / 4 853.** Aucun build natif PS5 ni validation console revendiqués.

### 2026-11-24 — NSD : résolution locale shipping, réglages Nintendo fail-closed

Vendor `fc4894a72071fcabf7ad7363d5783f6c0d0bf609` : `nsd.cpp/.h` deviennent des owners explicites de `encore-active/eden-backports` et les copies `sources/eden` reviennent aux blobs Eden épinglés. Les comportements locaux déjà développés — `GetEnvironmentIdentifier=lp1`, verrouillage du changement d'environnement, `Resolve/ResolveEx`, type serveur `Lp` et rejets des commandes test — atteignent ainsi réellement le build natif.

Les **11 commandes historiques** encore ouvertes qui dépendent de réglages/FQDN NAS Nintendo (10, 12–14, 30–31, 40–43, 50) sont raccordées à `RejectUnavailableNintendoSetting` avec `ResultNotSupported`. Les slots physiques 5/64/101/102 restent volontairement `nullptr` car ils ne sont pas des lignes qualifiées du miroir utilisé pour le compteur.

Croisement 4 853 : **11 NULL → D**. **Pool restant = 926 / 4 853.** Aucun build natif PS5 ni validation console revendiqués.

### 2026-11-24 — NS:SU : politique offline shipping, transferts/update firmware fail-closed

Vendor `4915afc7bebe87da64c5eeb64843a24727a887dd` : les quatre owners `system_update_interface.cpp/.h` et `system_update_control.cpp/.h` sont désormais installés par `eden-backports`. Les comportements offline déjà développés (état réseau `None`, vrai `ISystemUpdateControl`, événement content-delivery local, notifications exFAT/background et shutdown sans tâche hôte) ne dépendent plus de copies `sources/eden` dormantes.

Les commandes historiques `RequestSendSystemUpdate` / `GetSendSystemUpdateProgress` et les **23 commandes** de `ISystemUpdateControl` sont raccordées à un rejet explicite : Encore ne télécharge, ne prépare, n'applique, ne transmet et ne reçoit aucun firmware/card-update Horizon, et ne touche jamais au firmware PS5. Les quatre slots physiques `Unknown12–15` restent volontairement `nullptr`.

Croisement 4 853 : **25 NULL → D**. **Pool restant = 901 / 4 853.** Aucun build natif PS5 ni validation console revendiqués.

### 2026-11-24 — PDM query : statistiques Eden shipping, journal brut fail-closed

Vendor `04f219188c2c187e5bda6e462d871e5a9ff0b841` : `query_service.cpp/.h` deviennent des owners `eden-backports` explicites. Les statistiques déjà développées (`PlayTimeManager`, nombre de lancements, dernier timestamp, ABI `PlayStatistics` HOS16+/23 en 0x48) atteignent désormais le runtime natif.

La cmd4 `QueryPlayStatisticsByApplicationId` est **implémentée réellement** à partir des mêmes données persistées que cmd5. Les cmd0 et 8–12 sont raccordées à `RejectUnavailablePlayLogQuery` : elles exigent les événements bruts PDM/account que nous ne persistons pas. Le catalogue HOS23 corrige aussi l'ancien faux ABI-DIFF de cmd0 : le nom moderne est bien `QueryAppletEvent` ; `QueryApplicationEvent` ne concernait que HOS 1.0.0–7.0.1.

Croisement 4 853 : cmd0 **ABI-DIFF → D**, cmd4 **NULL → IMPL-SRC**, cmd8–12 **5 NULL → D**, soit **7 entrées sorties du pool. Pool restant = 894 / 4 853.** Aucun build natif PS5 ni validation console revendiqués.

### 2026-11-24 — BTDRV + bt : backend Bluetooth Switch absent fermé en bloc

Vendor `8b0b3b8b8622bb00f72b411ae324446ccaf22935` : `btdrv.cpp` devient un owner explicite `eden-backports`; la copie `sources/eden` revient au blob Eden épinglé. Les **138 slots `nullptr` physiques** sont fermés : **129** commandes du driver `btdrv` et **9** opérations GATT utilisateur `bt`. `RegisterBleEvent` conserve son vrai `KReadableEvent`, `EmulateBluetoothCrash` conserve son rejet production et `EnableRadio` devient un NOOP explicite sans accès au Bluetooth PS5.

SwitchBrew confirme que `btdrv` est le driver matériel Bluetooth de la Switch, utilisé par HID/BTM et implémenté au-dessus de la pile UART/Broadcom BSA. Il confirme aussi les noms modernes HOS (FinalizeBluetooth, StartInquiry/StopInquiry, OpenHidConnection, GATT/BLE, etc.) : les anciens noms du miroir qui produisaient des `ABI-DIFF` sont des variantes historiques et ne constituent pas des contrats HOS23 distincts.

Croisement 4 853 : `btdrv` **17 NULL + 61 ABI-DIFF → D/NOOP**, `bt` **9 NULL → D**, soit **87 entrées sorties du pool**. La ligne btdrv cmd97 était déjà HORS-VERSION. **Pool restant = 807 / 4 853.** Aucun build natif PS5 ni validation console revendiqués.

### 2026-11-24 — CAPS:SC : contrôle screenshot sans backend fermé explicitement

Vendor `11bdd31265db39c90a67b92c923e97bd9960968c` : `caps_sc.cpp/.h` deviennent des owners `eden-backports` explicites et les copies `sources/eden` reviennent aux blobs Eden épinglés. Les **20 slots `nullptr` physiques** de `IScreenShotControlService` sont raccordés à `RejectUnavailableScreenShotControl`.

Ce service contrôle le module de screenshot Switch (raw framebuffer, shared-buffer capture, demandes/cancel screenshot, metadata overlay/movie et raw screenshot stream), pas le rendu VI invité normal ni les services AlbumManager déjà implémentés. SwitchBrew indique notamment que 1101/1106/1107 sont les seules commandes `caps:sc` utilisées par GRC et que 1201–1203 correspondent au raw screenshot stream debug.

Croisement 4 853 : **16 NULL → D**. Les quatre slots physiques historiques 1001/1002/1003/1204 ne sont pas des lignes distinctes du pool HOS23 utilisé ici. **Pool restant = 791 / 4 853.** Aucun build natif PS5 ni validation console revendiqués.

### 2026-11-24 — CAPS:C : owner album shipping, movie streams absents fail-closed

Vendor `683af96eb36362e89c0e0faecfa49cd9e6ab8059` : `caps_c.cpp/.h` deviennent des owners `eden-backports` explicites. Les handlers déjà développés de disponibilité stockage et registre ARUID/ApplicationId atteignent désormais le runtime natif au lieu de rester dans `sources/eden`.

**22 slots physiques** sans backend movie sont raccordés à `RejectUnavailableMovieBackend` : lectures album-movie 2003–2008, thumbnail movie 2302, write streams 2401–2405/2411–2414/2421–2422/2424/2431/2433–2434. Les opérations screenshot/fichier potentiellement implémentables restent volontairement ouvertes : 2101/2102, 2202, 2301 et 60001 (ainsi que les anciennes commandes physiques hors miroir).

SwitchBrew HOS moderne expose 2001/2002 comme `NotifyAlbumStorageIsAvailable/Unavailable`, exactement les handlers actifs ; les anciens noms movie-read du miroir sont donc des variantes historiques et non des contrats HOS23 distincts.

Croisement 4 853 : **22 NULL → D + 2 ABI-DIFF → IMPL-SRC**, soit **24 entrées sorties du pool. Pool restant = 767 / 4 853.** Aucun build natif PS5 ni validation console revendiqués.

### 2026-11-24 — ACC:SU : authentification Nintendo Account fermée sans toucher aux profils locaux

Vendor `8d14c398fd604733cfcc05d4dcd1d612ee53a921` : dans l'owner shipping ACC existant, **11 slots** de `ACC_SU` exclusivement dépendants du backend Nintendo Account/réseau sont raccordés à `RejectUnavailableNintendoAccount` : disponibilité réseau, authentification application/service, cache d'identifiant signé Nintendo, floating registration, procédures register/resume Nintendo Account, guest/floating login et suspension du daemon réseau.

Les profils locaux, `GetUserCount/ListAllUsers/GetProfile`, sélection utilisateur, thumbnails, inscription locale, notifiers, open-context et les commandes PIN restent inchangés. Le replay moteur inverse exactement les 11 raccords et la méthode ajoutée puis exige le predecessor ACC `f4f16cb5…` / 90909 octets.

Croisement 4 853 : **11 NULL → D. Pool restant = 756 / 4 853.** Aucun build natif PS5 ni validation console revendiqués.

### 2026-11-24 — CAPS:A : accessors album shipping + thumbnail Ex0 réel

Vendor `4df98ff0a70343fca54c12146303ac84e0337546` : `caps_a.cpp/.h` deviennent des owners shipping. Les accessors AlbumManager déjà développés ne restent plus dépendants de `sources/eden`. `LoadAlbumScreenShotThumbnailImageEx0` est implémenté avec le vrai décodeur thumbnail AlbumManager, en renvoyant attribut/dimensions et en initialisant le buffer annexe.

Les 8 commandes movie-read 2001–2008 et `GetLastOverlayMovieThumbnail` (302) sont raccordées à un rejet explicite faute de backend movie. Les usages/cache/fichiers et sessions encore non qualifiés restent ouverts.

Croisement 4 853 : **9 NULL → D + 1 NULL → IMPL-SRC**, soit **10 entrées sorties du pool. Pool restant = 746 / 4 853.** Aucun build PS5 ni validation console revendiqués.

### 2026-11-24 — CAPS:U : accessors application album shipping, movie/session fail-closed

Vendor `f8e15a9c11ed569facf06edce7ca1b77c9c1fd3d` : `caps_u.cpp/.h` deviennent des owners shipping. Les lectures/listes/suppressions par ARUID et décodages screenshot/thumbnail déjà branchés à AlbumManager atteignent réellement le runtime natif.

Les movie-read streams 2001–2005 et `OpenAccessorSessionForApplication` sont rejetés explicitement. `PrecheckToCreateContentsByAruid` et `GetAllAlbumFileList3AaeAruid` restent ouverts pour une vraie implémentation.

Croisement 4 853 : **6 NULL → D. Pool restant = 740 / 4 853.** Aucun build PS5 ni validation console revendiqués.

### 2026-11-24 — NOTIF : paramètres d'alarme réellement conservés

Vendor `f9856b407eebd3533ea4687089849887c769240b` : `notif.cpp/.h` deviennent des owners shipping. `NotificationServiceImpl` conserve désormais pour chaque `AlarmSettingId` les octets `application_parameter` et leur taille réelle, les remplace lors d'un update, les restitue lors de `LoadApplicationParameter` et les supprime avec l'alarme. La limite de 8 alarmes corrige aussi l'off-by-one `> MaxAlarms` en `>= MaxAlarms`. L'include `<iterator>` est explicite pour l'indexation par `std::distance`.

Le changement ne prétend pas persister les alarmes entre redémarrages et ne modifie pas le scheduler système encore absent. Il complète strictement le CRUD mémoire déjà exposé par `notif:a` et `notif:s`.

Croisement 4 853 : les commandes 500/510/530 des deux services passent **6 PARTIEL → IMPL-SRC**. **Pool restant = 734 / 4 853.** Aucun build PS5 ni validation console revendiqués.

### 2026-11-25 — GRC + OLSC : film Switch et transfert cloud indisponibles

Vendor `7ea2306eee8d69671336252a2018697b98f46112` : les owners natifs `grc/grc.cpp` et `olsc/transfer_task_list_controller.cpp/.h` restent sélectionnés par `eden-backports/src/core/CMakeLists.txt`. **8 slots physiques GRC** (enregistrement, trimmer, movie-maker, service debug) et **24 slots physiques OLSC** (transfert de tâches Horizon Ocean/cloud et réparation) passent de `nullptr` à un rejet IPC explicite `ResultUnknown` quand aucun backend réel n'est disponible. Cela ne modifie ni VI/render/presentation ni les handlers OLSC existants d'événements, stopper local et compteurs.

La vérification de provenance moteur reconstruit les **trois fichiers prédécesseurs octet pour octet**, puis compare SHA-256, tailles et manifeste shipping, sans toucher aux sources Eden épinglées. Ce raccordement ne réalise ni capture vidéo ni sauvegarde distante : il empêche une réponse de succès factice.

**Croisement catalogue 4 853 : seulement 2 lignes GRC `grc:c` (cmd1/2) sont physiquement présentes et encore classées NULL dans l'index ; elles passent NULL → D.** Les 6 autres slots GRC et 24 slots OLSC ne sont pas comptés arbitrairement comme 30 lignes supplémentaires du catalogue historique. **Pool restant = 732 / 4 853** sous réserve de réconciliation ultérieure des identités de l'index, dont l'écart physique historique subsiste. **Aucun build PS5 ni validation console revendiqués.**

### 2026-11-25 — ACC entity HOS13+ : profils et miniatures locaux réellement actifs

Vendor `aca5aba40ab556d32a2ae9aec25c2fbd6f783f00` : le TU shipping `src/core/hle/service/acc/acc.cpp` était déjà installé, mais les trois services actuels `acc:e`, `acc:e:u1`, `acc:e:u2` laissaient **45 slots physiques NULL** malgré les handlers hérités implémentés dans `Module::Interface`. Les connexions sont désormais effectives : **15 + 14 + 16**, couvrant dénombrement/existence/liste d'utilisateurs, dernier utilisateur, ouverture de profils, sélection sans interaction, autorisation d'enregistrement local, accès à l'administrateur de compte déjà existant, CRUD des miniatures de sauvegarde sur disque, utilisateurs qualifiés et édition de profil (cmd205 sur `acc:e:u2`). Les chemins Nintendo Account/token restent inchangés ; les fonctions à contrat ABI incertain (`GetProfileDigest`, PIN, notificateurs réseau) restent ouverts.

**Provenance réversible :** moteur reconstruit l'ancien `acc.cpp` exact en remplaçant seulement les 45 pointeurs révisés, compare SHA-256 et tailles au patch replay et au manifeste. D'après [SwitchBrew Services API](https://switchbrew.org/wiki/Services_API), `acc:e*` remplace les anciens `acc:u0/u1` dès HOS 13.0.0. Le catalogue historique des 4 853 n'indexe pas ces 45 slots : **aucun retrait artificiel supplémentaire du pool 732 / 4 853**. **Pas de build PS5 ni de gameplay PS5 validé.**

### 2026-11-25 — AM : deux empreintes shipping corrigées sans altération C++

Vendor `518176771ae50589313b7dc5955fe118f9f2c0d1` : les deux sources maintenues `am/service/common_state_getter.cpp` et `.h` sont restées octet pour octet identiques au commit `aca5aba4`, mais leur manifeste annonçait des SHA-256 différents, introduits au plus tard avec le lot AM `5fa1a189`. Les 35 entrées AM du manifeste ont été confrontées à leurs propriétaires réellement shipping ; seules ces deux entrées divergeaient. Le manifeste a été réconcilié sur les empreintes effectivement calculées : cpp `09a7076177ee1cee…`, header `0e0d85897649d0f6…`. Le contrôle `verify()` peut donc reconnaître les sources AM réellement installées ; **aucune fonctionnalité C++, compilation PS5 ou validation console n'est revendiquée**. Le registre canonique reste **732 / 4 853**.

### 2026-11-25 — ACC entity HOS13+ : rejet explicite des backends Nintendo/debug absents

Vendor `1c1f244beddb9e1620830a352e6b4c0adb9424f9`, moteur companion : les trois owners shipping `ACC_E`, `ACC_E_U1`, `ACC_E_U2` exposent désormais **52 rejets IPC explicites** : 32/10/10 slots physiques `nullptr` des procédures Nintendo Account, synchronisation/authentification réseau, migration cloud, jetons et commandes de debug. Cette correction ne transforme pas les opérations locales de profils/miniatures en rejets : les 45 raccordements précédents sont maintenus. Le contrôleur de replay inverse exactement le nouveau groupe, puis le groupe local précédent ; aucune copie non contrôlée de `sources/eden`.

Croisement [SwitchBrew Account services](https://switchbrew.org/wiki/Account_services), notamment `acc:e:u1/u2` et les procédures BAAS. Les 52 slots ne sont pas indexés individuellement dans les 4 853 entrées du miroir historique : **pool canonique inchangé : 732 / 4 853**. Compilation native PS5, gameplay et tests console non validés.

### 2026-11-25 — BTM provenance : réception de la totalité des divergences au prochain contrôle

Vendor `0e5f7b03f26bae7f950e9293d632b6bd7b80d280` : `btm/btm.cpp`, 12 377 octets, n'avait pas l'empreinte du manifeste après les lots Bluetooth précédents. C++ inchangé ; SHA-256 shipping actuel `fb866c889578be7356ac6205aa404d4b0b3951532f55933ccd5fc90c3077dd5f` inscrit. Le vérificateur strict moteur `verify()` remonte désormais **tous** les mismatches actifs/pinnés en une passe, afin de corriger le groupe restant sans cycles CI un-à-un. Aucune validation console ou progrès du pool historique n'est associé à la réparation. Pool = **732 / 4 853**.

### 2026-11-25 — Lot groupé de quatre empreintes de provenance natives

La CI épinglée précédente a exposé en **une seule passe** les quatre dernières discordances d’empreintes entre manifeste vendor et fichiers C++ actifs : `filesystem/fsp/fsp_srv.cpp` (52 179 octets), `hid/hid_system_server.cpp` (51 896), `ns/application_manager_interface.cpp` (68 229) et `usb/usb.cpp` (15 416). Le vendor `ee53db178e3bb04fb41792602d5d47e68b3f0b21` aligne les quatre SHA-256 sur les octets réellement présents, sans aucune modification C++ et sans altérer les SHA `upstream` de la source Eden épinglée. Moteur compagnon : nouveau gitlink et whitelists/tree exactes. Les contrôles de provenance ne sont pas désactivés. **Pool restant : 732 / 4 853.** Aucune qualification console.

### 2026-11-25 — NS droits/entitlements HOS23 : lot runtime ciblé

Vendor `727d6de6ab259ce3103f5f244985fb1632e1202b` : le TU shipping `ns/application_manager_interface.cpp` ferme **14 commandes physiques** de gestion d’environnements de droits et extension de licences HOS23 (`2150–2155`, `2160/2161`, `2170/2171`, `2180–2182`, `2190`) sur `RejectUnavailablePlatformCommand`, qui retourne une erreur IPC explicite en l’absence du backend de licences Nintendo. Aucun handle, événement, état d’activation, résultat d’extension ou succès fictif n’est produit. Source `ns:am2` réellement sélectionnée ; callbacks locaux de contenu/records, lancement invité, GameCard et add-on content non touchés. [SwitchBrew NS Services](https://switchbrew.org/wiki/NS_services) confirme ces commandes HOS6+ et les deux libellés historiques 2180/2181 qui restent **ABI-DIFF** sans preuve suffisante pour les assimiler à l’ABI maintenue.

**Croisement réel 4 853 : 12 lignes NULL → D ; les deux anciennes lignes 2180/2181 demeurent ABI-DIFF, donc toujours dans le pool. Nouveau pool restant = 720 / 4 853.** Le moteur vérifie l’inverse exact des 14 pointeurs contre le source précédent (68 229 octets) ; aucune compilation/validation console PS5 revendiquée.

### 2026-11-25 — ES : mutations de tickets et préachats offline explicitement rejetés

Vendor `b3f8efa1d434a1d5d1568302f83ed18d4e33e9f1` : nouveau propriétaire natif explicite `eden-backports/src/core/hle/service/es/es.cpp` (sélectionné par le CMake et le manifeste) au lieu de laisser un changement dans une copie non prioritaire. **19 slots NULL physiques** d’import de certificats, suppression/gestion de tickets, préachats et données chiffrées sans backend Nintendo deviennent `RejectUnavailableTicketManagement` avec réponse d’erreur. Les lectures de tickets locaux `GetTitleKey`, `ListCommonTicketRightsIds`, `GetCommonTicketData`, `CountCommonTicket` et les interrogations d’ownership encore non qualifiées ne sont pas redirigées. Le script moteur vérifie un reverse exact de l’overlay de **16 737** octets sur le source épinglé de **15 733** octets et n’altère pas les receipts upstream.

[SwitchBrew ETicket](https://switchbrew.org/wiki/ETicket_services) : deux commandes héritées `es` 4 `DeletePersonalizedTicket` (1.0.0–13.2.1) et 36 `DeleteAllInactiveELicenseRequiredPersonalizedTicket` (6.0.0–12.1.0) ne sont plus applicables à l’interface HOS23 ; leur `nullptr` physique historique reste non exécuté. Les anciennes cmd21 et 33 sont également hors firmware, mais elles n’avaient pas de lignes NULL propres dans le miroir et ne sont **pas** retranchées.

**Croisement catalogue canonique : 17 NULL → D dans le code shipping + 2 NULL → HORS-VERSION pour HOS23 = 19 entrées sorties du pool. Pool restant = 701 / 4 853.** Les slots physiques 39/40 sont déjà HOS13+ mais absents du miroir, pas soustraits deux fois. Aucune validation console PS5 ni gains de gameplay revendiqués.

### 2026-11-25 — ES : correction mémoire P0 et deux commandes locales réellement implémentées

Vendor `69c1c7adda95aaa854f311011a50552d3036ebd8` : dans les deux sources réellement compilées `es/es.cpp` et `crypto/key_manager.cpp`, **trois branches de parsing de tickets** ne lisent plus les octets au-delà de l’`std::span` invité ; les tickets importés sont validés contre la taille physique de la signature choisie, et non `sizeof(std::variant<Ticket>)` qui rejetait des tickets valides. Les **quatre accès `map::at`** aux tickets sont remplacés par des recherches dont l’absence retourne `ERROR_INVALID_RIGHTS_ID` sans exception C++ non maîtrisée. Les **deux réponses Get*TicketData** sérialisent désormais la structure de ticket physique sélectionnée dans `std::variant`, et non l’adresse du wrapper C++ `Ticket`.

`es` cmd30 `CountTicket` et cmd31 `ListTicketRightsIds` interrogent les tickets réellement présents dans les maps KeyManager, avec borne par buffer IPC et type de sortie u32 utilisé dans les commandes voisines. **2 entrées NULL → IMPL-SRC**, pool canonique restant **699 / 4 853**. Les commandes 18/19/20/37/38 restent ouvertes jusqu’au contrat complet ; aucune preuve console PS5 ni build PS5. L’inverse strict des deux nouveaux blobs maintenus est épinglé dans le moteur, sans suppression des corrections eTicket précédentes.

### 2026-11-25 — NDRM : 59 commandes HOS13+ réellement présentes mais hors catalogue

Vendor `f5a1d9b7e439084203d901bfddd4371d2fe33718` : les classes actives `NDRM_LU` et `NDRM_LA` enregistrent les services `ndrm:lu` et `ndrm:la` lorsque HOS ≥ 13. Le catalogue historique de 4 853 commandes ne contient **aucune ligne `ndrm:*`**, alors que le C++ sélectionné par CMake contient **5 + 54 = 59 slots NULL physiques**. Les 59 slots sont maintenant raccordés à `RejectUnavailableNdrm`, avec résultat d’erreur explicite faute de backend de licences/entitlements Nintendo. Il ne s’agit **pas d’une émulation de licence** ; les consultations de tickets eTicket précédemment corrigées restent intactes.

Le nouveau replay conserve un inverse exact des 59 pointeurs et des deux méthodes de rejet, puis inverse les deux lots eTicket précédents. **État physique de cette unité : 153 commandes enregistrées, 63 NULL restantes** (122 au début du lot). **Le pool historique reste 699 / 4 853**, sans double comptage des 59 commandes absentes de son index. Ces 59 commandes sont suivies séparément comme `UNSUPPORTED` explicite tant que leur backend n’existe pas ; aucune CI/PS5 console qualifiée à ce couple.

### 2026-11-25 — NS cmd92 : correction réelle d'une couverture historique faussement déclarée

Vendor `e964a6879a29531bcad73ac219225fb065ee2d81` : le propriétaire CMake PS5 `ns/application_manager_interface.cpp/.h` déclare désormais le vrai handler HOS5+ cmd92 `GetRunningApplicationProgramId` par `D<&IApplicationManagerInterface::GetRunningApplicationProgramId>`. La valeur `u64 ProgramId` est lue dans le `WindowSystem::GetMainApplet()` actif ; en absence d'application/main applet, l'erreur existante `AM::ResultApplicationRecordNotFound` est renvoyée, sans inventer un Title ID. Le contrat a été comparé à [SwitchBrew NS services](https://switchbrew.org/wiki/NS_services) (cmd92 HOS5+) et aux getters déjà présents dans cette TU.

**Le catalogue de 4 853 classait auparavant cmd92 IMPL-SRC malgré le slot réel `nullptr`** : cette erreur de correspondance est désormais réparée **dans le runtime**. Elle ne retire pas de ligne du pool historique qui la considérait déjà couverte. Le comptage physique CMake validé à vendor `f5a1d9b7` était **1 697 NULL sur 6 385 slots** ; ce correctif enlève **1 NULL physique**, soit **1 696** au nouveau HEAD si CMake n'a pas changé. **Pool canonique historique = 699 / 4 853**, inchangé. Exact reverse CPP/header contrôlé, provenance moteur/vendor épinglée. CI de ce HEAD et console PS5 à qualifier.

### 2026-11-25 — WLAN HOS23 : sélectionner le service réellement existant, pas les anciennes interfaces

Vendor `cf2237b8d710536a5c75ce1e36b62eeccb2e6c53` : `wlan.cpp` était bien dans le CMake natif, mais le serveur enregistrait toujours **six ports historiques** `wlan:lcl`, `wlan:lg`, `wlan:lga`, `wlan:sg`, `wlan:soc`, `wlan:dtc`, tous retirés depuis HOS15. Sur HOS15+ (cible NS1 HOS23), le moteur enregistre désormais le **vrai port `wlan`**, dont cmd0 `CreateWirelessCommunicationService` crée une interface IPC valide. Les **61 slots de la nouvelle interface HOS15–23** sont raccordés à une erreur explicite de backend radio indisponible sur PS5, sans inventer Wi-Fi local ni casser les sockets BSD réseau. Les six anciens ports ne sont enregistrés que si HOS inférieur à 15 ; leurs **144 `nullptr` physiques demeurent dans la source** par compatibilité ancienne. `wlan:p` et `wlan:nd` sont conservés dans leur table de services séparée.

Sources officielles : [SwitchBrew WLAN](https://switchbrew.org/wiki/WLAN_services), [service manager list](https://switchbrew.org/wiki/Services_API). Le propriétaire natif est strictement réversible jusqu’au précédent blob de 10 653 octets. Cette intégration **améliore la correspondance de service moderne, pas l’émulation des circuits radio Switch**. Le pool historique reste **699 / 4 853** ; le total des **1 696 `nullptr` physiques** demeure inchangé car les six tables anciennes restent compilées, mais **leurs 144 slots ne sont plus exposés sur HOS23**. CI et test console de ce nouveau couple non encore validés.

### 2026-11-25 — Version HOS23 : sept anciennes entrées ne sont plus exécutables

Croisement simultané des commandes du catalogue physique 4 853, des valeurs d'owner NS1 sélectionnées et des tables de versions [SwitchBrew NS](https://switchbrew.org/wiki/NS_services) / [WLAN](https://switchbrew.org/wiki/WLAN_services) : **sept lignes déjà dans le pool de 699** ne correspondent plus à des commandes accessibles en HOS23 :
- `wlan:soc` cmd6 (ABI-DIFF) et cmd7 (NULL) : service supprimé dès HOS15, et désormais non enregistré par le runtime natif HOS23 ;
- `ns:am2` cmd406 `GetApplicationControlProperty` (NULL, HOS6–18.1), cmd1900 `IsActiveAccount` (NULL, HOS3–12.1), cmd2156 `CreateRightsEnvironmentForMicroApplication/Preomia` (ABI-DIFF, HOS9–12.1), cmd2200 `GetGameCardApplicationCopyIdentifier` (NULL, HOS6–9.2) et cmd2201 `GetInstalledApplicationCopyIdentifier` (NULL, HOS6–9.2).

**7 entrées quittent le pool par HORS-VERSION**, sans remplacement artificiel par une implémentation. Les anciens slots physiques toujours présents dans le C++ restent comptés dans l'inventaire des **1 696 `nullptr`**, qui n'est pas un inventaire de reachabilité HOS23. Les nouvelles interfaces WLAN modernes exposées par le runtime continuent à être inventoriées indépendamment de l'ancien miroir. **Compteur canonique de revue NS1 HOS23 restant = 692 / 4 853 (14,3 %).** Aucun gain PS5 n'est déduit de cette requalification.

### 2026-11-25 — OLSC : 100 commandes cloud enregistrées explicitement, sans backend fictif

Vendor `535e1ee030ff343554f5c8b194f3b869a00b6894` : les sources natives réellement sélectionnées pour `IOlscServiceForSystemService`, `IRemoteStorageController`, `IOlscServiceForApplication` (six fichiers CPP/header backport) raccordent **55 + 26 + 19 = 100 slots NULL physiques** à `RejectUnavailableCloudBackend` avec une réponse d'erreur `ResultUnknown`. Il s'agit des interfaces de sauvegarde distante, transfert, archive, réparation et audit Nintendo Online ; aucun transfert cloud réel ni faux succès n'est déclaré. **Les 13 commandes OLSC déjà raccordées** des trois propriétaires ne sont pas modifiées : ouverture des contrôleurs, événements/état local, GetDataInfo et préférences d'application restent telles qu'avant.

Le CMake natif conservé installe ces six overlays depuis le manifeste avec sha256, tailles et chemin `upstream` exacts. Le moteur vérifie par inverse précis **100 pointeurs et 3 méthodes de rejet**, les trois includes et les trois headers, et exige l'égalité octet-pour-octet aux sources Eden épinglées. Le catalogue historique de 4 853 ne dispose pas de ces 100 lignes sous les bonnes interfaces : **pool historique maintenu = 692 / 4 853** ; inventaire physique **1 696 → 1 596 NULL restants** au même CMake. Pas de build ni de validation console PS5 ; nouvelles CI à vérifier sur ce couple.

### 2026-11-25 — MIG / PCIe / NS droits dynamiques : lot backend absent HOS23

Vendor `3411fc67c3c5bce5947fb5561c43ea44bb53e377` : **89 slots `nullptr` physiques** supplémentaires ont un rejet IPC explicite `ResultUnknown` dans les sources shipping réellement listées par le CMake : `mig/mig.cpp` **36**, `pcie/pcie.cpp` **28** (session matériel, service racine, journal IRQ), et `ns/dynamic_rights_interface.cpp/.h` **25** (autorisation dynamique Nintendo, licence, entitlement, async). Les **4 handlers locaux préexistants** de `IDynamicRightsInterface` restent inchangés. Aucun handle DMA PCIe de la PS5 n'est exposé à l'invité, ni aucune migration Nintendo réelle déclarée.

Le replay moteur inverse exactement les pointeurs, trois méthodes inline PCIe, une méthode inline MIG et une méthode externe NS, puis vérifie quatre fichiers contre la base Eden immuable. Sur le catalogue historique : `pcie` racine cmd0 `RegisterClassDriver` et cmd1 `QueryFunctionsUnregistered` passent **2 NULL → D**. Les slots `ISession` PCIe restaient déjà **INACCESSIBLE** : aucune interface de session n'est créée. L'unique ancienne commande `mig:usr` cmd10 `TryGetLastMigrationInfo` était historiquement NULL, mais le service réellement publié s'appelle `mig:user` ; elle passe **NULL → SERVICE-NON-EXPOSÉ** sans déclarer une migration implémentée. Les 25 commandes dynamiques et autres slots MIG non indexés ne sont pas soustraits arbitrairement.

**Compteur historique restant = 689 / 4 853. Compteur brut CMake des `nullptr` = 1 596 → 1 507.** Les traitements fail-closed ne valent ni services pleinement implémentés ni validation PS5. Build PS5 non lancé, CI du couple à vérifier.

### 2026-11-25 — Correctif concret : enregistrement du vrai service `mig:usr`

SwitchBrew [Services API](https://switchbrew.org/wiki/Services_API) confirme que NS1 Horizon 4+ expose le port **`mig:usr`** et non `mig:user`. L'ancien service `mig:user` était un défaut du runtime sélectionné malgré la classe `MIG_USR` correctement nommée en interne. Vendor `34c62dbcf8d5b1ffedc4931b447fd52077866625` modifie uniquement la déclaration `RegisterNamedService`, désormais alignée avec les appels SM invités HOS23. Les 36 commandes de transfert sans backend PS5 restent des rejets explicites, sans émulation cloud fictive.

Le catalogue historique `mig:usr` cmd10 `TryGetLastMigrationInfo` est en réalité **NULL → D**, et non NULL → SERVICE-NON-EXPOSÉ, suite à ce fix. Les autres lignes `mig:usr` précédemment dites `SERVICE-NON-EXPOSÉ` sont exposées mais explicitement refusées. Elles n'étaient déjà pas dans le pool : aucun retrait en double. **Compteurs inchangés : 689 / 4 853 restants historiques ; 1 507 `nullptr` physiques.** Le moteur vérifie la réversibilité exacte du nom de service et de l'overlay précédent avant installation. CI/PS5 non validés pour ce nouveau couple.

### 2026-11-25 — eTicket : lecture sûre et cohérente au premier accès

Vendor `157de42f41e8574d699da4a077c93b314ab7e293` (sources natives `es/es.cpp` et `crypto/key_manager.cpp`) : huit handlers eTicket (compte, liste, taille et lecture common/personalized) chargent désormais la base `PopulateTickets` avant d'accéder aux maps locales. Le parseur de bases de tickets refuse les signatures de fin de fichier sans structure complète et corrige le saut d'un octet qui ignorait un ticket contigu. Le manifeste enregistre les SHA-256 et tailles exactes ; l'installateur moteur inverse les mutations et retrouve les sources précédentes. CMake et ABI IPC inchangés.

**Compteurs inchangés : 689 / 4 853 restants historiques ; 1 507 `nullptr` physiques CMake.** La sûreté et la cohérence des handlers déjà enregistrés ont été corrigées ; aucun succès fonctionnel additionnel n'est revendiqué. Validation pré-commit : transformation inverse exacte et cohérence des hashes. Build natif PS5 et tests console : non exécutés.

### 2026-11-25 — OMM/SPSM : état docké partagé et refus des commandes de puissance non émulées

Vendor `ad021a102fbb7edeadb5356c098b8625f5f8d44f` : `omm` cmd0 `GetOperationMode`, cmd5 `GetCradleStatus` et cmd11 `GetDefaultDisplayResolution` utilisent `Settings::IsDockedMode()` et les résolutions VI déjà utilisées par le chemin AM actif. Ces **3 handlers locaux** renvoient les états et dimensions invités existants plutôt que des valeurs arbitraires. Les **26 autres commandes OMM** (HDCP/CEC/veille/cradle sans backend) et les **12 commandes SPSM** (veille, arrêt, bouton Home, journal matériel) sont raccordées à un rejet explicite ; elles ne manipulent jamais le système hôte PS5 et ne deviennent pas des fonctionnalités matérielles.

Deux unités CMake natives `omm/operation_mode_manager.cpp` et `omm/power_state_interface.cpp` plus leurs headers sont installées via quatre overlays et quatre empreintes SHA-256 actives/pristines ; la recette moteur vérifie les quatre couples et la sélection CMake. **Compteur physique calculé : 1 507 → 1 466 `nullptr`** (3 handlers utiles + 38 refus). **Compteur historique : dernière base qualifiée 689 / 4 853, à rapprocher des 41 slots de ce lot**, sans soustraction automatique. CI hôte / build PS5 / console : à qualifier pour le nouveau couple.

### 2026-11-25 — lot PCV + PSC/INS/HSHL + audrec, sans backend matériel fictif

Vendor `8b8227178f5e8062d95e7692e087d7fb0ac37abb` ; quatre overlays natifs sélectionnés par `eden-backports/src/core/CMakeLists.txt` (trois CPP et le header du gestionnaire audio), avec manifestes SHA-256 des sources primitives et maintenues. **79 slots physiques** précédemment `nullptr` sont raccordés à un rejet explicite : **36 PCV/CLKRST**, **30 PSC/INS/HSHL**, **13 audrec:u / IFinalOutputRecorder**. Aucun de ces 79 rejets n'est compté comme backend fonctionnel ; les clock sessions `clkrst`, les services PSC réels existants et la lecture audio restent inchangés. **8 nouvelles commandes HSHL HOS23** (16–21 et 6–7) absentes des anciennes tables sont enregistrées en erreur explicite sans inventer de réponse batterie/voltage. `pcv:arb` et `pcv:imm` ne sont enregistrés que sous HOS inférieur à 8 ; `clkrst` et `clkrst:i/a` sont exposés à partir de HOS8. Les sources originales `sources/eden` restent intactes.

Provenance : contrôles de tailles, de hashes, de sources CMake et de transformation inverse exacte prévus dans le replay moteur. **NULL physiques attendus : 1 466 → 1 387** (à confirmer en CI). **Pool canonique historique maintenu à 689 / 4 853** tant que la correspondance commandes/HOS23 du catalogue n'est pas recalculée ; aucun chiffre historique arbitrairement soustrait. Ce lot est un traitement fail-closed de matériel absent, pas une amélioration mesurée du gameplay PS5. Test console et build PS5 non effectués.

### 2026-11-25 — lot massif cloud/debug/réseau/matériel : 51 NULL physiques retirés

Vendor `202667f02b0ebe909bf0e5c93af15f8966fc5814` (arbre `6961f669459cab8f90a98c5356fcb71be18f5839`). Six nouveaux overlays et un successeur NGC sont sélectionnés par le CMake natif et couverts par le replay moteur exact.

- **MNPP sys/web : 11 NULL → erreur explicite**. Les handlers application déjà présents restent inchangés ; aucun upload Nintendo mission/reporting n'est simulé.
- **FGM debug : 3 NULL physiques supprimés** avec la classe et le service `fgm:dbg`, déjà hors-version sur HOS23. Les services `fgm`, `fgm:0`, `fgm:9` restent inchangés.
- **PTM manufacture : 4 NULL physiques supprimés** en retirant `psm:manu` et `powctl`, absents des unités retail. Les services `psm` et `ts` restent inchangés.
- **I2C : 6 NULL → erreur explicite** dans l'interface enfant déjà inaccessible puisque les ouvertures de session échouent sans matériel I2C Switch.
- **LDN SF : 18 NULL → erreur explicite**. Aucun backend local-wireless PS5 n'est inventé.
- **NGCT management : 9 NULL → erreur explicite** sur l'interface legacy ; `ngct:s` n'est plus enregistré à partir de HOS21, tandis que les chemins NGC/STPL existants sont préservés.

Le replay moteur reconstruit chaque fichier bit-à-bit depuis les sources post-backport, vérifie tailles/SHA-256, sélection CMake et manifeste. **NULL physiques attendus : 1 387 → 1 336.** Le compteur historique reste **689 / 4 853** jusqu'au rapprochement ligne-à-ligne : plusieurs entrées de ce lot étaient déjà HORS-VERSION ou INACCESSIBLE et ne doivent pas être soustraites une seconde fois.

Build PS5 et test console : non exécutés.

### 2026-11-25 — accélération WLAN/STPL/FGM/BCAT : 30 NULL physiques supplémentaires

Vendor final de ce palier : `84a8db4464e4989a067779b86605905e0f52ca52` (arbre `05343b44eaee0433f61e95c433b9d3c4e433e437`).

Après le lot 51-slots précédent, quatre successeurs ciblés retirent **30 `nullptr` physiques supplémentaires** sans transformer un backend absent en succès :

- **WLAN moderne : 3** — les créateurs `wlan:p` / `wlan:nd` sont HOS15+ et répondent explicitement en erreur sans radio Switch privée/driver. Les 141 slots physiques des six interfaces WLAN legacy restent compilés pour les firmwares <15 mais ne sont pas atteignables sur HOS23 ; le service moderne `wlan` et son interface de 61 commandes restent inchangés.
- **STPL/NGC : 12** — cinq commandes de save-data shim et sept commandes system shim renvoient `IPC::ResultNotSupported`, cohérent avec les méthodes voisines déjà non supportées. Les lectures/écritures locales NGC existantes ne sont pas redirigées.
- **FGM IRequest : 4** — l'interface de requête horloge retournée par `fgm` échoue explicitement sur Initialize/Set/Get/Cancel plutôt que de laisser quatre dispatch inconnus. Le retrait précédent de `fgm:dbg` demeure.
- **BCAT/News : 11** — deux variantes de sync par ApplicationId rejoignent le rejet delivery-task existant ; deux créateurs de progress service autonomes échouent faute de backend de téléchargement Nintendo ; sept commandes réception/subscription/archive News échouent explicitement. Les services DeliveryCacheStorage/Directory/File, ClearStorage, TopicList et autres chemins de cache/news local déjà implémentés restent actifs.

Le manifeste shipping porte les SHA-256 exacts des successeurs ; le replay moteur vérifie tailles, SHA, CMake et propriétaires avant de les accepter. **Inventaire physique attendu : 1 336 → 1 306 `nullptr`**. Le pool historique reste **689 / 4 853** jusqu'au rapprochement ligne-à-ligne : WLAN legacy, FGM debug, PTM manufacture et plusieurs interfaces modernes ne doivent pas être retranchés deux fois d'un index qui les classait déjà hors-version/inaccessibles ou ne les contenait pas.

Build PS5 et test console : non exécutés.

### 2026-11-25 — NS cmd3 : raccordement fonctionnel réel

Vendor `b57110e18a26f3a4e518765a02726579866d02c4` : `IApplicationManagerInterface` cmd3 `GetApplicationViewDeprecated` passe du dispatch `nullptr` à la méthode CMIF déjà implémentée dans le même propriétaire shipping. L'ABI (buffers ApplicationId → ApplicationViewDeprecated) correspond au service HOS courant ; aucune nouvelle valeur synthétique ni backend réseau n'est ajouté. Le replay moteur inverse uniquement ce pointeur, retrouve exactement le propriétaire précédent `1c0af884...`, puis poursuit les preuves NS existantes.

**Inventaire physique attendu : 1 306 → 1 305.** Ce slot est un handler fonctionnel, pas un NOOP/rejet. Le compteur historique reste à rapprocher avant modification afin d'éviter un double comptage d'une entrée précédemment classée IMPL-SRC par analyse de méthode.

Build PS5 et validation console : non exécutés.

### 2026-11-25 — LDN ConnectPrivate : 2 handlers fonctionnels réels

Vendor `9aeb0c4c87c3776318378084eb1803f627b0d694` (arbre `743adac5cc038ec8fb10e66777addfcec4ba3656`). Les cmd303 `ConnectPrivate` de `IUserLocalCommunicationService` et `ISystemLocalCommunicationService` passent de `nullptr` à des handlers CMIF réels.

L'ABI suit HOS : `SecurityConfig + SecurityParameter + UserConfig + s32 LocalCommunicationVersion + ConnectOption + NetworkConfig`. Le nouveau `LANDiscovery::ConnectPrivate` recherche dans les résultats de scan une entrée correspondant au `SessionId`, à l'`IntentId` (LocalCommunicationId + SceneId), au paramètre/mode de sécurité et au canal demandé ; aucun IP hôte n'est fabriqué. En cas de match, le chemin appelle le même `LANDiscovery::Connect` utilisé par cmd302 ; en l'absence de réseau réellement découvert, il renvoie `ResultConnectionFailed`. La version signée est bornée avant conversion `u16`.

Six overlays natifs (LANDiscovery cpp/h + user cpp/h + system cpp/h) ont des couples SHA-256 upstream/active exacts. Le replay moteur reconstruit les six fichiers bit-à-bit, vérifie la sélection CMake et les deux bindings cmd303. Références croisées : SwitchBrew décrit l'ABI ConnectPrivate actuelle ; Ryujinx expose la même requête 0xBC.

**Inventaire physique attendu : 1 305 → 1 303 `nullptr`.** Ces deux entrées sont des handlers fonctionnels, pas des NOOP/rejets. Le compteur historique reste à rapprocher ligne-à-ligne avant décrément.

Build PS5 et validation console : non exécutés.

### 2026-11-25 — idle:sys : politique d'auto-extinction invitée neutre

Vendor `f1c2e246ffbfa0327ad49aeff10d6541cffefe87` (arbre `6288cb14b8de7a5e6494ad795c3e58836be08054`). Les 6 commandes de `IPolicyManagerSystem` ne sont plus `nullptr`.

- cmd0 fournit un vrai Event Horizon lisible, non signalé tant qu'Encore ne modélise pas de demande d'auto-extinction invitée ;
- cmd1 retourne `false` pour `IsAutoPowerDownRequested`;
- cmd3/4/5 acceptent le contexte/politiques/activité utilisateur sans piloter le sleep de la PS5 : l'émulateur n'exécute pas le timer d'auto-extinction Horizon ;
- cmd2 HOS23 reste sémantiquement inconnu et renvoie explicitement `ResultUnknown`.

Deux overlays CMake actifs (cpp/h) sont couverts par SHA-256 upstream/active et replay bit-à-bit. **Inventaire physique attendu : 1 303 → 1 297 `nullptr`.** Cinq commandes ont un comportement invité cohérent ; la sixième est un rejet explicite. Aucun résultat console n'est revendiqué.

Build PS5 et test console : non exécutés.

### 2026-11-25 — pdm:qry : LastPlayTime HOS courant + 3 wrappers V0, table sans NULL

Vendor `2a1baf9350e04b1d973c7f751e59098b192dccdc` (arbre `2644ebafcdba94a3da5932c00c874bd5af768b90`). Le propriétaire actif `ns/query_service.cpp` passe de 13 `nullptr` à 0.

Correctifs fonctionnels :
- `LastPlayTime` n'est plus une structure vide : ABI **0x18**, ApplicationId u64, timestamps user/network u32 au format minutes Horizon depuis 1999-12-31, minutes depuis dernière exécution et flag de validité ;
- cmd17 `QueryLastPlayTime` écrit désormais jusqu'au nombre d'ApplicationId réellement demandé, à partir de `LaunchTimestampCache`, sans inventer une exécution lorsque le launch-count est nul ;
- cmd7 `QueryLastPlayTimeV0` appelle cmd17 avec flag=0 ;
- cmd13 `QueryApplicationPlayStatisticsForSystemV0` appelle cmd18 avec flag=0 ;
- cmd16 `QueryApplicationPlayStatisticsByUserAccountIdForSystemV0` appelle cmd19 avec flag=0.

Les cmd1/2/3/6, retirées après HOS6.2, et les six slots 30/31/100/110/118/119 dont la sémantique moderne n'est pas qualifiée sont raccordés à `ResultNotSupported` via le propriétaire existant ; ils ne sont pas présentés comme implémentés. Le contrat moteur exige `sizeof(LastPlayTime)==0x18`, les trois wrappers V0, 16 pointeurs de rejet contrôlés et zéro `nullptr` dans la table.

**Inventaire physique attendu : 1 297 → 1 284 `nullptr`** après le lot idle:sys. Sur ces 13 slots, **3 sont des bindings fonctionnels** et 10 sont fail-closed. Le pool historique reste **689 / 4 853** jusqu'au rapprochement exact des commandes legacy/V0.

Build PS5 et test console : non exécutés.

### 2026-11-25 — PSM cmd16/18 : événements batterie réels

Vendor `4a68cca38b2622d2250931b74ac524a7fe580d2d` (arbre `14d126aff067eace98f8fb9c8823109ed10b491a`). Les commandes `GetBatteryChargeInfoEvent` et `GetBatteryChargeCalibratedEvent` passent de `nullptr` à deux Event handles Horizon stables.

`BatteryChargeInfoEvent` est signalé uniquement lorsque les politiques déjà émulées modifient réellement un champ de `BatteryChargeInfoFields` : activation/désactivation de la charge, alimentation contrôleur et charge rapide. `BatteryChargeCalibratedEvent` reste valide mais non signalé, faute de producteur matériel de calibration Switch. Les deux événements sont créés/fermés par le ServiceContext PSM ; aucun événement de batterie PS5 n'est fabriqué.

Le replay moteur vérifie les SHA-256 source/active, le CMake, les deux bindings, les deux créations/fermetures et six sites de signal charge-info. **Inventaire physique attendu : 1 284 → 1 282 `nullptr`.** Les deux slots sont des handlers fonctionnels.

Build PS5 et validation console : non exécutés.

### 2026-11-25 — palier accéléré sous 1 200 NULL physiques

Base **CI confirmée** avant ce palier : vendor `4a68cca38b2622d2250931b74ac524a7fe580d2d`, **1 282 NULL / 6 448 slots**.

Vendor final du palier : `7a0047acd3329a10ae4162ec7feff4e6a32bc1aa` (arbre `d4f5ebae406fc9997a2b1c1753c6f7bd9502630d`).

**84 slots physiques** supplémentaires sont retirés :
- PREPO/LM/NFC : **14** — PREPO réutilise 3 handlers statistiques existants, 2 commandes modernes inconnues sont fail-closed ; LM 2 commandes modernes suivent la sémantique retail locale ; NFC complète 7 opérations session/app lifecycle sans inventer de périphérique.
- OLSC/MII/NCM/CAPS : **32** — OLSC 3, MII import/export 2, retrait `ncm:v` non-retail 1, CAPS 26 commandes capture/album sans backend en erreur explicite. Les chemins album/cache déjà implémentés restent inchangés.
- BTM/FATAL/APM/PTM/NIFM : **38** — Bluetooth Switch 23, fatal:p 2, politique APM 5, contrôle thermique TS 4, mutations/statut NIFM non qualifiés 4. Les handlers réseau, température, événements batterie, radio offline et performance déjà présents restent sélectionnés.

Les deux lots sont couverts par manifestes SHA-256 actifs/upstream, vérification CMake et contrats moteur sémantiques. Aucun de ces rejets n'est présenté comme backend fonctionnel.

**Inventaire physique attendu : 1 282 → 1 198 NULL**. Validation CI de ce nouveau couple encore requise avant de considérer 1 198 comme confirmé. Le pool historique reste séparé jusqu'au rapprochement ligne-à-ligne.

Build PS5 et test console : non exécutés.

### 2026-11-25 — CAPS restant + PSC : palier 1 172 attendu

Vendor final : `107de63757c661e3084fcd7acc4c3c1fabca536e` (arbre `48bb2d967c876ed188e25fa63d4a81f00872ed38`).

À partir du palier **1 198 attendu**, **26 NULL physiques** supplémentaires sont retirés :
- CAPS : **12** — contrôle JPEG 3, screenshot service 5, screenshot application 2, album application 2. Les chemins de sauvegarde/listage/image déjà implémentés ne sont pas remplacés ; seules les variantes sans backend sont fail-closed.
- PSC : **14** — `psc:c` 9 et `IPmModule` 5. Ces commandes de power-state management n'ont pas de backend invité PS5 ; elles renvoient explicitement `ResultNotSupported` sans piloter l'alimentation hôte.

Manifestes SHA-256 et sélection CMake sont verrouillés ; le moteur vérifie le nombre exact de bindings et l'absence de `nullptr` dans ces propriétaires.

**Inventaire physique attendu : 1 198 → 1 172 NULL / 6 448 slots.** Validation CI du couple final requise avant de considérer 1 172 comme confirmé.

Build PS5 et test console : non exécutés.

### 2026-11-25 — GLUE + SET : palier 1 131 attendu

Base **CI confirmée** : vendor `107de63757c661e3084fcd7acc4c3c1fabca536e`, **1 172 NULL / 6 447 slots**.

Vendor successeur : `c499a3118340dc899091f9c98a2d03da584fceda` (arbre `fbe0b68dd71f404db49d090add4f8d89dd0b9d03`).

**41 NULL physiques** supplémentaires sont retirés :
- GLUE **26** : ARP 7 commandes sans backend complémentaire fail-closed ; ECTX 7, dont `ectx:w::CreateContextRegistrar` raccordé au vrai `IContextRegistrar` existant et 6 opérations de stockage/lecture non modélisées fail-closed ; NOTIF 12 extensions inbox/presentation modernes fail-closed, tout en préservant le CRUD AlarmSetting et les paramètres d'application déjà stockés.
- SET **15** : `Get/SetForceMonauralOutputFlag` sont deux handlers fonctionnels HOS17+ avec état invité ; les 13 commandes modernes restantes sans ABI/backend local qualifié renvoient explicitement `ResultNotSupported`.

Le contrat moteur exige zéro `nullptr` dans ARP/ECTX/NOTIF/SET, les nombres exacts de bindings, les hashes actifs/upstream et la sélection CMake. Les fonctions existantes de notification et settings ne sont pas remplacées.

**Inventaire physique attendu : 1 172 → 1 131 NULL.** Validation CI du couple requise avant confirmation.

Build PS5 et test console : non exécutés.

### 2026-11-25 — PM debug/boost + PSC wake lock + TMA : palier 1 117 attendu

Base **CI confirmée** : vendor `c499a3118340dc899091f9c98a2d03da584fceda`, **1 131 NULL / 6 447 slots**, 5 316 handlers.

Vendor successeur : `f1d3c7f2cfc23836b1fe4020ba989b440da0fe62` (arbre `218870603571d269f9dc06d9cc44c1ba92188a12`).

**14 NULL physiques** supplémentaires sont retirés :
- PM **11** : 8 commandes `pm:dmnt` / Atmosphère debug en `ResultNotSupported`; 3 boosts de resource-limit `pm:shell` sont des succès neutres puisque ces quotas Horizon ne sont pas modélisés. `LaunchProgram`, `GetProcessEventHandle` et `GetProcessEventInfo` restent intacts/non traités.
- PSC time **2** : `CreateWakeLock` / `DestroyWakeLock` deviennent des succès neutres ; aucun état d'alimentation PS5 n'est modifié.
- TMA **1** : `htc:tenv::GetServiceInterface` fail-closed faute d'environnement host de kit de développement.

**Inventaire physique attendu : 1 131 → 1 117 NULL.** CI requise pour confirmation.

Build PS5 et test console : non exécutés.

### 2026-11-25 — LDN monitor + NCM memory : palier 1 099 attendu

Base précédente : **1 117 NULL attendus** après PM/PSC/TMA.

Vendor successeur : `a1ae39a3ef6e56c88d47a6425a26ad71cf40f502` (arbre `e7060657a66ae43d2891ab8dc902f2aeb8318e41`).

**18 NULL physiques** supplémentaires sont retirés :
- LDN monitor **17** : `IMonitorService` 5, `ISfMonitorService` 1, `ISfServiceMonitor` 11. Ces interfaces de monitoring sans backend indépendant renvoient explicitement `ResultNotSupported`. Les services user/system, LANDiscovery, scan, create-network et connect/private-connect restent inchangés.
- NCM **1** : `GetMemoryReport` fail-closed. `ResolveDataPath` et `ResolveAddOnContentPath` restent volontairement non traités car ils peuvent affecter le chargement de contenu.

Hashes actifs/upstream, CMake et nombres de bindings sont verrouillés par le moteur.

**Inventaire physique attendu : 1 117 → 1 099 NULL / 6 447 slots.** CI requise pour confirmation.

Build PS5 et test console : non exécutés.

### 2026-11-25 — ACC + AOC : palier sous 1 000, 996 attendu

Base **CI confirmée** : vendor `a1ae39a3ef6e56c88d47a6425a26ad71cf40f502`, **1 099 NULL / 6 447 slots**, 5 348 handlers.

Vendor successeur : `5db9e6dd27b777b28867a1add277e3fba2c0d821` (arbre `2fad6e874bb443b74dac303284072b8b7ec3c444`).

**103 NULL physiques** supplémentaires sont retirés :
- ACC **92** : les centaines de handlers locaux profil/utilisateur déjà présents restent inchangés. `ISessionObject::Dummy` devient un succès de compatibilité explicite ; les **91 autres** entrées encore inconnues (Nintendo Account, notifiers, PIN policy, debug, thumbnails/extensions firmware) passent en `ResultNotSupported`. Elles ne sont pas comptées comme implémentations fonctionnelles.
- AOC **11** : les extensions application-id/debug/host/cache sans backend passent en `ResultNotSupported`. Les chemins DLC locaux existants `CountAddOnContent`, `ListAddOnContent`, `GetAddOnContentBaseId`, `PrepareAddOnContent` ainsi que l'événement de changement restent actifs.

Le replay moteur inverse d'abord exactement la nouvelle couche ACC **102 756 → 95 439 octets** et retrouve bit-à-bit le blob précédemment accepté avant de rejouer toute la provenance ACC historique. AOC vérifie les deux hashes upstream/active, la sélection CMake, les 11 bindings de rejet et la présence des quatre handlers DLC locaux.

**Inventaire physique attendu : 1 099 → 996 NULL / 6 447 slots.** Validation CI requise avant confirmation.

Build PS5 et test console : non exécutés.

### 2026-11-25 — WLAN legacy pré-HOS15 : palier 855 attendu

Base précédente : **996 NULL attendus** après ACC + AOC.

Vendor successeur : `7cbc3897ac97ddcd0c2bb3915e56a09e6e589d1e` (arbre `8d28a58ff0cf2e275f1ffb76ca496e63f90ce9bb`).

**141 NULL physiques** supplémentaires sont retirés des six interfaces WLAN legacy, déjà enregistrées uniquement lorsque le firmware invité est **< HOS15** :
- `ILocalManager` : 97 ;
- `ILocalGetFrame` : 1 ;
- `ILocalGetActionFrame` : 1 ;
- `ISocketGetFrame` : 1 ;
- `ISocketManager` : 13 ;
- `IDetectManager` : 28.

Tous passent à un même rejet explicite `ResultNotSupported`. Pour HOS15+ / HOS23, ces interfaces ne sont jamais enregistrées : le service moderne `wlan`, `wlan:p`, `wlan:nd` et leurs handlers existants restent byte-for-byte indépendants de cette couche.

Le replay moteur inverse exactement les 141 pointeurs et 6 méthodes puis retrouve **bit-à-bit** l'ancien propriétaire WLAN de 18 713 octets avant de poursuivre le replay HOS15 déjà validé.

**Inventaire physique attendu : 996 → 855 NULL / 6 447 slots.** Ce gain est uniquement fail-closed legacy ; il ne représente pas 141 nouvelles fonctionnalités HOS23.

Build PS5 et test console : non exécutés.

### 2026-11-25 — NS secondaires version/platform : palier 833 attendu

Base précédente : **855 NULL attendus** après fermeture fail-closed des interfaces WLAN pré-HOS15.

Vendor successeur : `a1d47a90e418d3bd12e20f6151bcb31a34d0c594` (arbre `24212c303b767d3fc31e60044382f972bc8e6551`).

**22 NULL physiques** supplémentaires sont retirés sans toucher à `IApplicationManagerInterface` :
- `IApplicationVersionInterface` **13** : version-list, required-version et auto-update Nintendo sans backend renvoient explicitement `ResultNotSupported`;
- `IPlatformServiceManager` **9** : authorization blacklist / debug / China NG-word data fail-closed.

Les six handlers shared-font déjà réels restent présents et vérifiés ; aucun chemin de lancement d'application n'est modifié.

**Inventaire physique attendu : 855 → 833 NULL / 6 447 slots.** CI requise pour confirmation.

Build PS5 et test console : non exécutés.

### 2026-11-25 — LDR/RO/AM/NCM : palier 817 attendu

Base CI confirmée : vendor `a1d47a90e418d3bd12e20f6151bcb31a34d0c594`, **833 NULL / 6 447 slots**.

Vendor final : `1452e213198f1dfbf508fe37fd1b548d6186ca2c` (arbre `06883df88d6b0d7366ffbf28d0b897102cbd3a8d`).

**16 NULL physiques** sont retirés :
- **LDR 10** : les trois tables `ldr:dmnt`, `ldr:pm`, `ldr:shel` n'exposent plus de dispatch inconnu. Les commandes loader/process-manager non modélisées sont fail-closed ; aucun second chemin de lancement hôte n'est inventé.
- **RO 1** : `ro:dmnt GetProcessModuleInfo` devient une erreur explicite, sans toucher au chargement NRO réel.
- **AM 3** : `GetWakeupCount` est implémenté avec un `u64=0` tant qu'Encore ne simule aucun cycle veille/réveil invité ; `SetHidInputMagnificationForApplication` et `GetLaunchRequiredTick` restent fail-closed.
- **NCM 2** : `ResolveDataPath` et `ResolveAddOnContentPath` échouent explicitement tant qu'Encore ne modélise pas un chemin Horizon fs-common ; aucun chemin PS5 hôte n'est exposé.

Contrats moteur : SHA-256 upstream/active, sélection CMake, bindings exacts, absence de `nullptr` dans ces propriétaires et maintien des chemins de chargement/album/contenu existants.

**Inventaire physique attendu : 833 → 817 NULL / 6 447 slots.** Validation CI encore requise avant de considérer 817 comme confirmé.

Build PS5 et test console : non exécutés.

### 2026-11-25 — SM CopyFromCurrentDomain fonctionnel : palier 816 attendu

Vendor `d461fda9a65f10e409ec50eb6b92396990bbac9c` (arbre `3b4f899dc57739e68b74d9bbb08db6e3081f8dda`).

Le dernier `nullptr` physique de la famille SM, `IpcController::CopyFromCurrentDomain` cmd1, est remplacé par une implémentation réelle : validation du domaine et de l'ObjectId, récupération du `DomainHandler` existant puis création d'une nouvelle session via `HLERequestContext::AddMoveInterface`. Les ObjectId invalides échouent sans créer de session. La sémantique suit le gestionnaire HIPC amont : le même objet de domaine est exposé via un nouveau handle de session.

Contrats moteur : SHA-256 upstream/active, sélection CMake, binding cmd1 exact, présence des contrôles ObjectId/DomainHandler/AddMoveInterface et absence de `nullptr` dans le propriétaire.

**Inventaire physique attendu : 817 → 816 NULL / 6 447 slots.** Ce slot est fonctionnel, pas fail-closed. Validation CI du couple final encore requise.

Build PS5 et validation console : non exécutés.

### 2026-11-25 — NS réseau/update secondaire : palier 788 attendu

Base : **816 NULL attendus** après le raccordement fonctionnel SM. Vendor final de ce lot : `4751b7f1fec2920f77913706423b0abe5b6e51c8` (arbre `953cc4946aedbd19c2341b5516f4d68416734646`).

**28 NULL physiques** supplémentaires sont retirés sans toucher à `IApplicationManagerInterface` ni aux quatre commandes ContentManagement encore non qualifiées :
- `pdm:ntfy/ns:vm` : 8 — `NotifyLibraryAppletEvent` rejoint le no-op local de notification sans play-log ; 7 commandes inconnues/safe-version réseau sont fail-closed.
- `IDownloadTaskInterface` : 7 — aucun backend de téléchargement Nintendo n'est simulé.
- `IECommerceInterface` : 7 — link-device, sync-rights et e-license réseau échouent explicitement.
- `ISystemUpdateInterface` : 4 — les extensions 12–15 non qualifiées utilisent le rejet de transfert système existant.
- `IAsyncResult` : 2 — payload/error-context non modélisés échouent explicitement ; `Cancel` reste fonctionnel.

Le replay moteur verrouille SHA-256, CMake, compte exact des bindings et absence de `nullptr` dans ces cinq propriétaires.

**Inventaire physique attendu : 816 → 788 NULL / 6 447 slots.** Validation CI requise avant confirmation.

Build PS5 et validation console : non exécutés.

### 2026-11-25 — sockets hors data-path : palier 734 attendu

Base : **788 NULL attendus** après le lot NS réseau/update. Vendor final : `21df36e8ef5963b50765cbafb9428a744940c419` (arbre `6c784562a3a0c8a62512fdea4d4fdb8e47ce662e`).

**54 NULL physiques** sont retirés sans modifier le data-path BSD réel ni SFDNSRES :
- **BSD 37** : 20 extensions/statistiques modernes, 16 commandes `bsdcfg/ifcfg` de contrôle interface/ARP/DHCP et le factory `bsd:nu` non qualifié deviennent fail-closed. Les handlers `Socket/Select/Poll/Recv/Send/Accept/Bind/Connect/GetSockOpt/SetSockOpt/Shutdown/Close` restent inchangés.
- **Ethernet matériel 13** : `ethc:c`, `ethc:i`, `eth:nd` échouent explicitement ; Encore conserve son abstraction réseau hôte sans exposer de contrôleur Ethernet Switch.
- **NSD 4** : les derniers réglages/environnements Nintendo non modélisés rejoignent le rejet existant. `Resolve/ResolveEx` restent actifs.
- **SFDNSRES 13** restent ouverts volontairement pour une implémentation DNS réelle ultérieure.

**Inventaire physique attendu : 788 → 734 NULL / 6 447 slots.** Validation CI requise.

Build PS5 et validation console : non exécutés.

### 2026-11-25 — SFDNSRES : famille sockets à zéro NULL, palier 721 attendu

Vendor final : `50009086f7a428c11ff75f4cbac9567a8bcb8df5` (arbre `3c3259177c211d2c5c94f39553c64b62bf49036c`).

Les **13 NULL SFDNSRES** restants sont traités :
- **3 fonctionnels** : `GetHostStringErrorRequest`, génération de cancel handle monotone, `CancelRequest` idempotent pour le resolver synchrone Encore.
- **10 fail-closed** : reverse DNS, DNS privé Switch et options opaques non modélisés.
- Les chemins réels `GetHostByNameRequest`, `GetAddrInfoRequest` et variantes avec options restent raccordés à `Network::GetAddressInfo`.

Avec le lot sockets précédent, la famille sockets passe à **0 NULL physique** sans neutraliser le forward DNS ni le data-path BSD.

**Inventaire physique attendu : 734 → 721 NULL / 6 447 slots.** Validation CI requise.

Build PS5 et validation console : non exécutés.

### 2026-11-25 — SPL common AES : palier 713 attendu

Base CI confirmée : vendor `50009086f7a428c11ff75f4cbac9567a8bcb8df5`, **721 NULL / 6 447 slots**.

Vendor final : `94ae95f0a556ff8b79cb54e9cb1c9bc8b05ec8b2` (arbre `074b6e3a4c5b420c0c8c2bfb3f0a483a6265789d`).

Les quatre tables dérivées SPL FS/SSL/ES/MANU raccordent désormais leurs commandes `GenerateAesKek` et `GenerateAesKey` aux handlers communs déjà présents dans `Module::Interface`, comme `spl:mig` le faisait déjà. **8 NULL physiques** sont retirés.

Ces handlers consomment l'ABI attendue mais retournent explicitement `ResultSecureMonitorNotImplemented` faute de backend secure-monitor de dérivation de clés. Aucun succès crypto fictif n'est introduit.

**Inventaire physique attendu : 721 → 713 NULL / 6 447 slots.** Validation CI requise.

Build PS5 et validation console : non exécutés.

### 2026-11-26 — rapprochement du reliquat global et de l'inventaire physique

Dernier bilan opérationnel rapporté (moteur `8777873e`, vendor `4a807c67`) : **689 / 4 853 entrées historiques à revoir = 392 NULL + 17 STUB + 153 PARTIEL + 118 ABI-DIFF + 9 AMBIGU** ; inventaire physique rapporté : **343 NULL / 6 670 slots**. Ce bilan reste un jalon historique, pas une certification de l'état courant.

Au moteur `d36638114f70d4acdd58c4d0b079cf71b4441ad3`, gitlink `7be1675e767f5b41e1462dade2b8900ccf7e0706`, le comparatif Git des 33 commits vendor depuis ce jalon ne change pas les listes CMake ; le script d'inventaire moteur ne change que deux sentinelles. Les tables FunctionInfo des propriétaires modifiés ont été recomptées directement sur les deux révisions (IRS : source originale puis overlay du manifeste ; application_functions : propriétaire final partagé) :

| Propriétaire | NULL avant | NULL après | Delta slots |
|---|---:|---:|---:|
| NS application manager | 156 | 12 | +22 |
| NS content management | 1 | 0 | +1 |
| VI application display | 1 | 0 | 0 |
| PM | 3 | 0 | 0 |
| Audio controller | 5 | 0 | 0 |
| IRS | 1 | 0 | 0 |
| AM application functions | 3 | 0 | 0 |

LibraryAppletAccessor, HID system et PCTL : delta nul ; le self_controller backport n'est pas le propriétaire final. **Delta statique : -158 NULL, +23 slots. Projection physique sur le jalon rapporté : 185 / 6 693 (6 508 handlers raccordés).** Il s'agit d'un recomptage différentiel, pas d'une exécution complète de la gate ; aucune validation CI de ce nouveau chiffre n'est revendiquée.

**Le catalogue détaillé n'est pas synchronisé avec ce jalon** : ses lignes portent encore 1 169 NULL, 172 PARTIEL, 2 STUB, 187 ABI-DIFF et 9 AMBIGU, soit 1 539 lignes ouvertes selon leurs étiquettes actuelles. Ce total documentaire obsolète ne remplace pas le bilan opérationnel historique de 689. Ne pas soustraire les 158 slots physiques au pool historique : les deux ensembles ne sont pas bijectifs, et les rejets explicites ne constituent pas automatiquement des implémentations. Le nouveau total fonctionnel exact requiert la réconciliation par service/interface/ID/version et classification des corps actifs, y compris les partiels, stubs et ABI.

HEAD vendor de branche observé : `fb19607934561712877d3e00a45e2188cae9c4c3` (deux commits après le gitlink, PCTL et AM self-controller). Non repinné dans ce contrôle ; aucun changement C++ ni build PS5. Maintenir le suivi dans ce registre existant et ne pas remplacer un chiffre non qualifié par une estimation présentée comme exacte.

### 2026-11-26 — Recalcul global conservateur du catalogue matérialisé

**Nouveau pool de revue : 631 lignes ouvertes**, sur le catalogue physiquement présent, au couple moteur `b4173b4b9472588f77bbaccab28388a7f29d759e` / gitlink vendor `7be1675e767f5b41e1462dade2b8900ccf7e0706`. Base catalogue blob `158ebed45188c9ce1f1bc3ec94ab6286038d071d`.

Recomptage des statuts de lignes IPC/SVC : 1 539 lignes initialement ouvertes (1 169 NULL, 172 PARTIEL, 187 ABI-DIFF, 2 STUB, 9 AMBIGU). Rapprochement des lignes NULL via propriétaire historique, manifeste backports, overrides natifs de `tools/ns1/active_ipc_source_inventory.py`, identifiant décimal et nom exact de FunctionInfo, puis vérification des handlers de rejet et de leur corps (résultat d'erreur explicite, pas de succès). Lecture directe des fichiers au gitlink, complétée par les lignes ajoutées et corps de rejet du diff Git `230caf1fd48d5f03c9dbdab77178a12c6738a65e...7be1675e767f5b41e1462dade2b8900ccf7e0706`. En cas de correspondances multiples contradictoires, d'ABI inconnue ou de corps non qualifié, conserver l'entrée ouverte. Les raccordements non qualifiés ne sont pas des implémentations closes.

| Groupe de rapprochement | Rejet explicite D | Raccordé à qualifier |
|---|---:|---:|
| NS app manager, ACC, HID sys, NIM, FSP srv, BTM, VI sys, PCTL | 457 | 26 |
| Autres propriétaires avec patch et corps de rejet explicite (hors groupes directs) | 216 | 16 |
| NS system update control, friend, SET factory, SSL, NPNS, USB, SPL, NSD | 111 | 26 |
| NS droits dynamiques, SFDNSRES, SET debug, NFC, NIFM, NS download/ecommerce/ns | 40 | 21 |
| BSD, PSC, NS query, FSP storage, PM (LDR déjà compté, aucun delta) | 24 | 9 |
| CAPS vidéo sans référence initiale, NS cmd23, content/version, PCV, PL | 43 | 4 |
| VI manager, FSP pr, AM application functions, NS system update/async, PSM/TS/LBL | 7 | 5 |
| NCM, NVDRV, PCIe, HID, NS account/document, audio renderer manager, PREPO | 6 | 4 |
| Audio debug natif, TMA, OVLN, SET, WLAN, VI application display | 4 | 3 |
| **Total** | **908** | **114** |

| Statut restant | Lignes |
|---|---:|
| NULL historique / correspondance non résolue | 147 |
| RACCORDÉ à qualifier (ancien NULL) | 114 |
| PARTIEL (statut historique conservé) | 172 |
| ABI-DIFF (statut historique conservé) | 187 |
| AMBIGU (statut historique conservé) | 9 |
| STUB (statut historique conservé) | 2 |
| **Total global de revue recalculé** | **631** |

Arithmétique : 1 539 - 908 = 631. Les 114 raccordements restent dans le pool. Les 908 exclusions D suivent la convention historique : elles attestent d'un traitement explicite de l'appel, pas d'une implémentation fonctionnelle du service. Le chiffre de 689 précédemment rapporté n'était pas accompagné d'une réconciliation complète des lignes et n'est pas utilisé comme base de soustraction.

**Limites :** pool conservateur, pas certification exhaustive HOS23 ni nouveau comptage de tous les corps PARTIEL/ABI-DIFF/STUB/AMBIGU. Les 370 lignes de ces quatre statuts restent ouvertes par prudence ; elles n'ont pas toutes été requalifiées individuellement à ce gitlink. Les 147 NULL historiques incluent les correspondances non résolues et ne sont pas un compteur physique. Le catalogue matérialisé conserve l'écart de neuf références vis-à-vis du dénominateur historique de 4 853 ; ces références non identifiées ne sont pas inventées. Ce bilan remplace l'ancien compteur de revue rapporté pour les lignes effectivement matérialisées, mais ne prétend pas donner le nombre exact des fonctionnalités non implémentées de l'intégralité du firmware. Le catalogue annexe lui-même reste à synchroniser ligne par ligne. Aucun patch C++, changement de gitlink ni build PS5 dans cette passe.

### 2026-11-26 — requalification des 370 statuts non-NULL historiques

Base : palier global précédent **631 lignes ouvertes** = 147 NULL/correspondances non résolues + 114 raccordements à qualifier + **370 PARTIEL/ABI-DIFF/STUB/AMBIGU**. Couple examiné : moteur `673ffd05fcb5274e48826c332c55bb2ad6977b06` → gitlink vendor `7be1675e767f5b41e1462dade2b8900ccf7e0706`.

Le second passage a requalifié les propriétaires CMake/overlays déjà parcourus au lieu de conserver leurs étiquettes historiques par inertie. Les critères restent stricts : identité service/interface/ID/version, handler actif, corps observé, et maintien dans le pool dès qu'une limitation fonctionnelle ou une ambiguïté réelle subsiste.

- **ABI-DIFF : 187 → 23 ouvertes.** **164** lignes quittent le pool : nomenclatures historiques maintenant résolues, commandes HOS anciennes hors version pour la cible HOS23, handlers fonctionnels dont l'ABI actuelle est identifiée, ou backend explicitement indisponible avec rejet invité. Gros lots : BTDRV 60, audio app/debug + final recorder, USB, Friend, SPL, NOTIF, fontes partagées, PREPO, NFP, time:m, HID, NS, HWOpus, SFDNSRES, PCTL, ACC, ARP, ERPT, TS, PDM, CAPS.
- **PARTIEL : 16 lignes quittent le pool.** IRS **9** : lifecycle et processors virtuels réellement implémentés, y compris stop async observable et firmware virtuel ; VI ApplicationDisplayService **7** : relay/system/manager/indirect binder, display list, stray-layer teardown et rejet explicite du backend image indirect absent.
- Les PARTIEL NIFM, PSM, NCM, FSP, SVC et plusieurs politiques AM restent ouverts : leurs limitations décrites sont encore visibles dans le code actif.
- Les **2 STUB** historiques ne sont pas effacés artificiellement : `CanUseApplicationCore` reste sans règle firmware publiée permettant de dériver le booléen depuis le core-mask NPDM ; `GetOperationModeSystemInfo` dépend toujours d'une sémantique OMM non qualifiée.
- Plusieurs AMBIGU ont désormais un propriétaire identifié (notamment ACC et VI), mais restent dans le pool sous PARTIEL/STUB quand le comportement actuel n'est pas complet. Une résolution d'étiquette n'est pas comptée comme une fermeture.

**Nouveau compteur global de revue : 451 lignes ouvertes.** Arithmétique : **631 - 164 - 16 = 451**. Composition opérationnelle : **147** anciennes lignes NULL/correspondances non résolues + **114** handlers raccordés à qualifier + **190** lignes non-NULL encore réellement ouvertes après requalification.

Ce palier remplace le compteur 631 pour le suivi. Il reste conservateur : aucune ligne n'est retirée uniquement parce qu'un pointeur n'est plus `nullptr`. Aucun patch C++, changement de gitlink, build natif PS5 ou validation console n'est revendiqué dans cette requalification.

### 2026-11-26 — qualification des handlers raccordés et second passage PARTIEL : palier 341

Base : **451 lignes ouvertes** après requalification des 370 statuts non-NULL historiques.

Les **114 anciens NULL devenus handlers raccordés mais non encore qualifiés** ont été relus par propriétaire actif et corps, sans assimiler automatiquement « non-null » à « implémenté ». **100 quittent maintenant le pool** :

- eTicket (compte/liste Rights ID/title key), FSP Rights ID/path, FS QueryEntry/IStorage, AM launch-request rejeté proprement, Overlay no-op contractuel, content-action resolver, audio manual rendering, CAPS thumbnail ;
- SPL : 13 commandes consomment leur ABI et renvoient explicitement `ResultSecureMonitorNotImplemented` faute de secure monitor ; elles sont classées D, pas succès crypto ;
- SSL : 13 anciens NULL de contexte/connexion sont soit implémentés, soit explicitement rejetés par les extensions PKI/connexion non supportées ; les 5 rejets root déjà sortis au passage précédent ne sont pas recomptés ;
- NFC : lifecycle applet, pass-through session bookkeeping et debug hardware ont désormais un comportement explicite ; PM shell : event/info + resource-limit no-op ; IStorage : Write/Flush/SetSize/OperateRange ;
- NS ApplicationManager : 21/23 raccordements sont de vrais chemins runtime (records/content, terminate/launch, launch info, applet launch/terminate, control data, game-card consistency, AOC et terminate result). `GetApplicationViewDeprecated` synthétique et `PopApplicationShellEventInfo` neutre restent ouverts ;
- NIFM 5 : requêtes telemetry/channel/suspend/additional-info fail-closed ; IRS:sys 2 : ARUID actif réellement publié ; PDM notify 6 : no-op local documenté sans faux historique ; ContentManagement 3, SFDNSRES 2 et PDM query 1 sont fonctionnels ;
- second groupe : Thanks-message no-op, LBL apply/read brightness, document content path, audio manual renderer, OVLN queue count, firmware debug, VI indirect crop fail-closed.

Le second passage PARTIEL retire ensuite **10 lignes** supplémentaires : SixAxis firmware réel, HID FullKey grip color, AM `SetTerminateResult` / `ExecuteProgram`, NS `CalculateApplicationOccupiedSize`, CAPS listes album 102/142, NFC `WriteMifare` user+sys, et NVDRV `Initialize` (session NvCore réelle ; le work-buffer guest est inutile au HLE). Les lignes dont le backend reste visiblement incomplet — Palma wave, HIDBus générique, NFC raw pass-through, NIFM arbitration, PSM hardware, SVC debug, FSP integrity, etc. — restent ouvertes.

**Nouveau compteur global : 341 lignes ouvertes.**

Composition opérationnelle : **147 NULL/correspondances non résolues + 14 raccordements encore à qualifier + 180 non-NULL réellement ouverts = 341**.

Arithmétique depuis le palier précédent : **451 - 100 - 10 = 341**. Depuis le recalcul 631 : **290 lignes fermées par requalification/qualification ciblée**.

Aucun patch C++ runtime, changement de gitlink, build PS5 ou validation console dans cette étape. Les rejets explicites restent classés D/unsupported et ne sont jamais présentés comme une fonctionnalité émulée.


### 2026-11-26 — clôture ciblée des ABI-DIFF HOS23 et correctifs runtime : palier 323

Base : **341 lignes ouvertes** au couple moteur `13466a3e1439665edf8be5f5d175bd4bb3029ea5` / gitlink vendor `7be1675e767f5b41e1462dade2b8900ccf7e0706`.

Les **23 ABI-DIFF** encore conservées ont été recroisées avec les tables HOS 23.0.1, les propriétaires réellement sélectionnés et les corps actifs. **18 quittent le pool** ; **5 restent ouvertes** car leur comportement est encore réellement partiel : NS `GetApplicationView`, NS `BoostSystemMemoryResourceLimit` (ancienne ligne mal indexée, commande courante à suivre sur son ID HOS23), NOTIF `GetNotificationPresentationSetting`, Friend `GetUserPresenceViewV1` et `LoadUserSettingV1`.

Sorties de pool démontrées : doublon historique AM `GetDebugStorageChannel` (HOS23 ID 1000, pas 2), SPSM `GetCurrentState`, NS `LaunchMicroApplication`, ancienne ligne NS ServiceGetter `Attach`, NS-dev `LaunchApplicationFromHost`, les deux commandes audrec:a suspend/resume déjà fail-closed dans l'owner audio natif, NEWS 30500 fail-closed, BTDRV 34 `EnableRadio`, CAPS movie session 2001/2002, NPNS 1/2 désormais qualifiés en mode offline, NVDRV 7/8, NVMEMP `GetPid`, time:al `CreateWakeupAlarm`/child `GetAlarmEvent`, et l'ancienne nomenclature SPL cmd31 désormais résolue par interface.

Correctifs C++ runtime vendor :
- `9b4cb108c84c2209781befc3ab404d2925e5c06d` : SPSM cmd0 expose `GetCurrentState` et renvoie l'état Awake sans contrôler la PS5 ; NVMEMP remplace ses `UNIMPLEMENTED` par un rejet invité propre avec le nom HOS23 `GetPid` ; CAPS `OpenControlSession` retourne une vraie `IAlbumControlSession` dont les commandes movie-read/write HOS23 échouent explicitement faute de backend capture.
- `6f91d4c31ebbf2d6583a9dee41cbec3f26cfe2c1` : NVDRV cmd7/cmd8 deviennent `SetAruidWithoutCheck` / `SetAruid`, le second vérifie le PID-descriptor avant publication de l'ARUID ; NS cmd2513 `LaunchMicroApplication` n'est plus `nullptr` et échoue explicitement quand le backend plateforme est indisponible.

Le moteur est repinné dans ce commit sur le vendor **`6f91d4c31ebbf2d6583a9dee41cbec3f26cfe2c1`**.

**Nouveau compteur global : 323 lignes ouvertes.**

Composition opérationnelle : **147 NULL/correspondances historiques non résolues + 14 raccordements encore à qualifier + 162 non-NULL réellement ouverts = 323**.

Arithmétique : **341 - 18 = 323**. Depuis le recalcul 631 : **308 lignes sorties du pool** par requalification ou correction ciblée.

Statut validation : correctifs C++ intégrés et gitlink mis à jour ; **pas de build natif PS5 ni validation console revendiqués dans cette passe**. Les cinq cas encore partiels restent volontairement ouverts.


### 2026-11-26 — repin HOS23 ACC/HID/NIM/NS/VI et palier global 250

Base : **323 lignes ouvertes** au moteur `93b1f8dddfaa40e3f492b5caf6e975c94ef676c8` / gitlink vendor `6f91d4c31ebbf2d6583a9dee41cbec3f26cfe2c1`.

Cinq commits vendor consécutifs ont été relus avant repin, sans écraser les chemins fonctionnels existants :
- `6b8beb126b3123bc62cf3250fe166c57ede02f11` : derniers `nullptr` HOS23 de NS ApplicationManager traités ; `BoostSystemMemoryResourceLimit` devient un no-op explicite de ressource système, les commandes sans backend plateforme échouent proprement ;
- `f67cd526c76ce7111ad9126a941f075ffa06b714` : couverture des commandes réseau Account manquantes, toutes fail-closed faute de Nintendo Account backend ;
- `e26f13821c91c8ac1ec307e3a96cb97d7351ed11` : complétion HOS23 de la table HID system, avec publication ARUID réelle pour cmd500 et rejets matériels explicites pour le reste ;
- `adf29a064a09fb0a04ca636bcfa64e3201d03ea0` : commandes HOS23 NIM manquantes ajoutées en rejet Nintendo-online explicite ;
- `b3e6e3f8c5583a3e4c16e9241b5e392e70b5df02` : 75 `nullptr` physiques de VI ManagerDisplay remplacés par un rejet invité explicite, sans toucher aux handlers déjà fonctionnels.

Rapprochement du **pool global**, sans soustraire aveuglément les slots physiques :
- **64** anciennes lignes NULL du catalogue correspondent exactement, par fichier/ID/nom, aux slots VI ManagerDisplay maintenant explicitement traités ;
- **8** anciennes lignes NULL correspondent exactement aux transitions NS ApplicationManager (`DeleteApplicationRecord`, `DeprecatedLaunchApplication`, `GetContentMetaStorage`, `GetApplicationRecordProperty`, `ListApplicationRecordInstalledContentMeta`, `CreateApplicationResource`, `GetApplicationResource`, `GetApplicationIdOfPreomia`) ;
- **1** ligne non-NULL encore ouverte, `BoostSystemMemoryResourceLimit`, quitte le pool : son ID HOS23 courant est maintenant traité explicitement ;
- les commandes ajoutées ACC/HID/NIM qui n'avaient pas de ligne matérialisée dans le catalogue historique améliorent la couverture HOS23 mais **ne sont pas comptées comme réduction artificielle** du pool.

**Nouveau compteur global : 250 lignes ouvertes.**

Arithmétique : **323 - 64 - 8 - 1 = 250**. Depuis le recalcul 631 : **381 lignes sorties du pool** par requalification ou correction ciblée.

Le gitlink moteur est repinné sur le vendor **`b3e6e3f8c5583a3e4c16e9241b5e392e70b5df02`**. Aucun build natif PS5 ni validation console n'est revendiqué dans cette étape.


### 2026-11-26 — SystemDisplay + NS HOS23 : palier global 221

Base : **250 lignes ouvertes** au moteur `5552d35609db137571a398a2df9b6aece76b133d` / vendor `b3e6e3f8c5583a3e4c16e9241b5e392e70b5df02`.

Vendor `4b849800dba674e945c69097a883b149c20271b9` traite deux groupes encore matérialisés dans le pool :
- **VI SystemDisplay** : les 30 `nullptr` restants de la table active sont remplacés par un rejet invité `ResultNotSupported` explicite. Les handlers déjà fonctionnels (Z-order, visibilité, display modes, shared framebuffer) restent inchangés. **25** de ces slots correspondent exactement à des lignes NULL du catalogue historique encore ouvertes ;
- **NS ApplicationManager** : les commandes HOS23 **604 RegisterContentsExternalKey**, **1900 IsActiveAccount**, **2200 GetGameCardApplicationCopyIdentifier** et **2201 GetInstalledApplicationCopyIdentifier**, absentes de la table active et également non implémentées dans Lichii, sont désormais enregistrées avec le rejet plateforme existant. **4** lignes du pool sont closes.

Les cinq autres NULL physiques SystemDisplay non matérialisés dans le catalogue historique améliorent la table HOS23 mais ne sont pas soustraits au compteur global.

**Nouveau compteur global : 221 lignes ouvertes.**

Arithmétique : **250 - 25 - 4 = 221**. Depuis le recalcul 631 : **410 lignes sorties du pool**.

Le gitlink moteur est repinné sur le vendor **`4b849800dba674e945c69097a883b149c20271b9`**. Aucun build PS5 ni validation console revendiqués dans cette étape.


### 2026-11-26 — FSP loader/program-registry : palier global 214

Base : **221 lignes ouvertes** au moteur `377194c0c88e58bb70dbc3780c0ba3682b40af31` / gitlink vendor `4b849800dba674e945c69097a883b149c20271b9`.

Le lot vendor `ff529bc4` puis corrections ABI `79a9e5cb` / **`f4cba5fab9559a61386a018e0b10acc38c119e0a`** traite les services FSP secondaires sans inventer de backend :
- `fsp:ldr` : `OpenCodeFileSystem` consomme désormais son ABI et échoue explicitement avec `ResultTargetNotFound` tant qu'aucun CodeFS backend n'est disponible ; `IsArchivedProgram` renvoie l'état local non archivé ; `SetCurrentProcess` conserve le PID ;
- `fsp:pr` : les mutations de registre programme non modélisées échouent avec `ResultNotSupported`, tandis que `SetCurrentProcess` et `SetEnabledProgramVerification` conservent réellement leur état local.

Les signatures CMIF de `fsp:ldr` ont été alignées sur l'upstream Citron avant repin. Aucune ouverture de filesystem réelle n'est remplacée par un succès fictif.

**7 lignes historiques du pool** sont ainsi closes : 4 lignes rattachées au propriétaire `fsp_ldr.cpp` et 3 lignes `fsp_pr.cpp`.

**Nouveau compteur global : 214 lignes ouvertes.**

Arithmétique : **221 - 7 = 214**. Depuis le recalcul 631 : **417 lignes sorties du pool**.

Le gitlink moteur est repinné sur le vendor **`f4cba5fab9559a61386a018e0b10acc38c119e0a`**. Aucun build PS5 ni validation console n'est revendiqué.


### 2026-11-26 — réconciliation exhaustive des anciens NULL : palier global 184

Base : **214 lignes ouvertes** après le lot `fsp:ldr` / `fsp:pr`.

Le reliquat historique « NULL/correspondances non résolues » a été repris sur **l'ensemble des propriétaires actifs matérialisés** : 93 chemins C++ distincts, sélectionnés via manifeste `eden-backports` et overrides finaux PS5 connus, puis rapprochés par service/ID/nom avec les tables `FunctionInfo` du vendor `f4cba5fab9559a61386a018e0b10acc38c119e0a`.

Le balayage par lots confirme :
- avant le correctif FSP loader/program-registry, seulement **16 correspondances exactes** restaient réellement NULL/missing dans les propriétaires actifs ;
- **7** de ces lignes ont été traitées par le lot FSP déjà compté au palier 214 ;
- il reste donc **9 correspondances exactes**, toutes dans `fsp-srv` : cmd 0, 64, 80, 84, 130, 601, 611, 615 et 616 ;
- les autres anciennes lignes classées « correspondance non résolue » sont désormais démontrées comme noms/version/owner historiques déjà raccordés ou explicitement rejetés. Les 35 lignes sans chemin source extractible (principalement CAPS movie streams et NS cmd23) avaient déjà été sorties lors du rapprochement initial et ne sont pas recomptées.

Cela retire **30 lignes historiques supplémentaires** du pool sans modifier le runtime.

**Nouveau compteur global : 184 lignes ouvertes.**

Composition opérationnelle : **9 NULL exacts + 14 raccordements encore à qualifier + 161 non-NULL réellement ouverts = 184**.

Arithmétique : **214 - 30 = 184**. Depuis le recalcul 631 : **447 lignes sorties du pool**.

Aucun nouveau patch C++ dans cette requalification, aucun build PS5 ni validation console revendiqués.


### 2026-11-26 — FSP proxy : zéro NULL exact dans le pool, palier global 175

Base : **184 lignes ouvertes** au moteur `7b369874bf4035de7b05572d96e5ff75ecd30c1d` / gitlink vendor `f4cba5fab9559a61386a018e0b10acc38c119e0a`.

Vendor **`ab8f5da7f62d0f7de6f9d840ef5d6eb3ac12319e`** traite les **9 dernières correspondances NULL exactes** de `fsp-srv` :
- **fonctionnel** : cmd0 `OpenFileSystem` réutilise `OpenFileSystemWithIdImpl` avec le programme courant ; cmd64 `OpenSaveDataInternalStorageFileSystem` retrouve le save par ID puis ouvre réellement son répertoire via `SaveDataController` ; cmd615 `QuerySaveDataInternalStorageTotalSize` retourne la taille réelle du save directory ;
- **fail-closed explicite** : cmds 80, 84, 130, 601, 611 et 616 retournent `ResultNotSupported` faute de backend qualifié, plutôt qu'un succès synthétique.

Aucun des chemins de montage existants `OpenDataFileSystem*`, `OpenSaveDataFileSystem*`, GameCard, SD, BIS ou NCA n'est remplacé. Le cmd0 réutilise le résolveur NCA déjà actif.

**Nouveau compteur global : 175 lignes ouvertes.**

Composition opérationnelle : **0 NULL exact + 14 raccordements encore à qualifier + 161 non-NULL réellement ouverts = 175**.

Arithmétique : **184 - 9 = 175**. Depuis le recalcul 631 : **456 lignes sorties du pool**.

Le gitlink moteur est repinné sur **`ab8f5da7f62d0f7de6f9d840ef5d6eb3ac12319e`**. Statut : code intégré, pas de build PS5 ni validation console ; aucune CI automatique n'était encore publiée au moment du repin.


### 2026-11-26 — Friend V1/V2 offline : palier global 173

Base : **175 lignes ouvertes**.

Vendor **`5c5ec7af23bd26eee80be789850cee65ace8fd48`** remplace les réponses succès synthétiques de `GetUserPresenceViewV1/V2` et `LoadUserSettingV1/V2` par le rejet `RejectUnavailableNintendoOnline` déjà utilisé par les autres opérations Friend dépendantes du backend Nintendo. Le runtime ne fabrique donc plus de présence `0xe0` vide ni de friend-code `0000-0000-0000`.

Le pool historique contenait encore **2 lignes** correspondantes (V1).

**Nouveau compteur global : 173 lignes ouvertes.**

Arithmétique : **175 - 2 = 173**. Depuis le recalcul 631 : **458 lignes sorties du pool**.

Gitlink repinné sur `5c5ec7af23bd26eee80be789850cee65ace8fd48`. Aucun build PS5 ni validation console revendiqués.


### 2026-11-26 — ApplicationView basé sur le contenu installé : palier global 171

Base : **173 lignes ouvertes**.

Vendor **`2d389c95320c072349231755b9b4c3feb00042bb`** supprime la version synthétique `0x70000` des vues d'application V19/V20. Les deux chemins utilisent désormais `ContentProviderUnion::GetEntryVersion` : version de l'update `GetUpdateTitleID(application_id)` prioritaire, version de base en fallback. Les flags `0x401f17` sont conservés : ils correspondent au cas titre local entièrement présent/lançable utilisé également par Ryujinx.

Cela qualifie les deux lignes historiques encore ouvertes autour de `GetApplicationViewDeprecated` / `GetApplicationView`.

**Nouveau compteur global : 171 lignes ouvertes.**

Arithmétique : **173 - 2 = 171**. Depuis le recalcul 631 : **460 lignes sorties du pool**.

Gitlink repinné sur `2d389c95320c072349231755b9b4c3feb00042bb`. Aucun build PS5 ni validation console revendiqués.


### 2026-11-26 — requalification PSM invité : palier global 161

Base : **171 lignes ouvertes**.

Les PARTIEL historiques PSM **2–6, 8–11 et 14** ont été relus dans le propriétaire actif `encore-active/eden-backports/src/core/hle/service/ptm/psm.cpp`. Ils ne dépendent plus d'un effet physique PS5 pour remplir leur contrat invité :
- enable/disable/is-enabled de charge conservent l'état et signalent l'événement de charge ;
- acquire/release controller power supply conservent l'état invité ;
- enough-power emulation et fast-charge sont persistants et observables ;
- `IsEnoughPowerSupplied` dérive une réponse cohérente de l'état virtualisé et du power-status hôte.

L'absence volontaire de contrôle de l'alimentation physique PS5 **n'est pas une lacune HLE** : l'invité doit voir une politique de batterie/charge virtualisée, pas piloter l'hôte.

**10 lignes PARTIEL quittent le pool.** `GetBatteryChargeInfoFields` (cmd17) reste ouvert : plusieurs champs électriques sont encore des valeurs virtuelles neutres et doivent rester explicitement qualifiés comme tels.

**Nouveau compteur global : 161 lignes ouvertes.**

Arithmétique : **171 - 10 = 161**. Aucun patch C++ dans cette requalification ; aucun build PS5 ni validation console revendiqués.


### 2026-11-26 — requalification capteurs/backlight virtualisés : palier global 155

Base : **161 lignes ouvertes**.

Six PARTIEL historiques étaient encore classés comme incomplets uniquement parce qu'ils ne pilotent pas le matériel PS5 :
- PSM cmd12 `GetBatteryVoltageState` : état virtuel stable `Normal(3)` ;
- PSM cmd15 `GetBatteryAgePercentage` : batterie virtuelle saine à 100 % ;
- TS cmd1 / cmd3 : températures Switch virtuelles stables, volontairement indépendantes des thermiques PS5 ;
- LBL cmd6 / cmd7 : état backlight invité réellement modifié, conservé et relu par `GetBacklightSwitchStatus`.

Pour ces interfaces matérielles virtualisées, l'absence d'effet physique sur la PS5/TV est volontaire et correcte : l'invité observe un périphérique Switch virtuel cohérent.

**6 lignes PARTIEL quittent le pool.**

**Nouveau compteur global : 155 lignes ouvertes.**

Arithmétique : **161 - 6 = 155**. Aucun patch runtime dans cette requalification ; aucun build PS5 ni validation console revendiqués.


### 2026-11-26 — ACC / applet proxies / audctl : palier global 149

Base : **155 lignes ouvertes**.

Vendor **`e254d8d1b14eaf95de2ad3da9cefa215d99bfc5b`** qualifie les chemins Account/Applet :
- ACC cmd50 `IsUserRegistrationRequestPermitted` retourne réellement `ProfileManager::CanSystemRegisterUser()` ; l'ancien label `STUBBED` était trompeur et est supprimé ;
- `OpenLibraryAppletProxy`, `OpenOverlayAppletProxy` et `OpenSystemApplicationProxy` créent déjà leurs proxies réels pour un PID enregistré ; leur branche PID non encore enregistré utilise désormais le résultat AM 201 de retry, comme `OpenApplicationProxy`, au lieu d'un `UNIMPLEMENTED + ResultUnknown` ;
- `OpenApplicationProxy` lui-même est déjà complet dans l'owner actif NS2-runtime sélectionné par le CMake PS5 : résolution PID, proxy réel et contrat retry AM 201.

Audctl cmd7 `SetDefaultTarget` est également requalifié : cible + fade-in/fade-out sont conservés et `GetDefaultTarget` relit la cible. Aucune action matérielle hôte n'est requise par ce contrat.

**6 lignes PARTIEL quittent le pool.**

**Nouveau compteur global : 149 lignes ouvertes.**

Arithmétique : **155 - 6 = 149**. Depuis le recalcul 631 : **482 lignes sorties du pool**.

Gitlink repinné sur `e254d8d1b14eaf95de2ad3da9cefa215d99bfc5b`. Aucun build PS5 ni validation console revendiqués.


### 2026-11-26 — requalification SET virtualisé : palier global 146

Base : **149 lignes ouvertes**.

Trois PARTIEL `set:sys` sont requalifiés :
- cmd79 `GetProductModel` retourne le modèle virtuel **1 = Erista**, valeur valide confirmée par les définitions libnx ;
- cmd174 `GetHomeMenuScheme` retourne une palette HOME virtuelle stable et ABI-complete ;
- cmd185 `GetHomeMenuSchemeModel` retourne le modèle cohérent avec cette palette virtuelle.

Ces commandes interrogent l'identité/configuration **du matériel Switch émulé** ; elles ne doivent pas refléter le modèle physique PS5. Une valeur virtuelle stable et valide remplit donc le contrat HLE.

**3 lignes PARTIEL quittent le pool.**

**Nouveau compteur global : 146 lignes ouvertes.**

Arithmétique : **149 - 3 = 146**. Aucun patch runtime dans cette requalification ; aucun build PS5 ni validation console revendiqués.


### 2026-11-26 — SSL CreateContext + NIM async fail-closed : palier global 144

Base : **146 lignes ouvertes**.

Vendor **`5f4203040ee5febbc61dc99ed3433e6fb6929474`** traite deux anciens PARTIEL :
- SSL cmd0 `CreateContext` : le handler consomme l'ABI, la version SSL et renvoie un vrai `ISslContext` raccordé au backend de connexion/PKI ; l'ancien label `STUBBED` était trompeur et est retiré ;
- NIM `IShopServiceAsync::Request` : suppression de la fausse réponse réseau `"{}"` réussie. En l'absence de backend Nintendo Shop, la requête retourne désormais `IPC::ResultNotSupported` immédiatement.

**2 lignes PARTIEL quittent le pool.**

**Nouveau compteur global : 144 lignes ouvertes.**

Arithmétique : **146 - 2 = 144**. Gitlink repinné sur `5f4203040ee5febbc61dc99ed3433e6fb6929474`. Aucun build PS5 ni validation console revendiqués.


### 2026-11-26 — SPL GetConfig : réponse d'erreur unique, compteur inchangé

Vendor **`574c1e18e4fc5951022e6d00ba4be76e3ef8f673`** corrige le chemin actif `Module::Interface::GetConfig` : lorsqu'un `ConfigItem` nécessite le secure monitor et retourne une erreur, le handler termine désormais immédiatement après la réponse d'erreur. Il ne construit plus une seconde réponse CMIF dans le même appel.

Le service SPL reste PARTIEL : plusieurs ConfigItem légitimes dépendent encore d'un secure monitor non disponible. **Compteur global inchangé : 144 lignes ouvertes.**

Gitlink repinné sur `574c1e18e4fc5951022e6d00ba4be76e3ef8f673`. Aucun build PS5 ni validation console revendiqués.


### 2026-11-26 — BGTC politique de veille virtualisée : palier global 142

Base : **144 lignes ouvertes**.

Les deux PARTIEL `bgtc:t` cmds 102/103 sont requalifiés dans l'owner actif `encore-active/eden-backports/src/core/hle/service/glue/bgtc.cpp` :
- `WillDisconnectNetworkWhenEnteringSleep = false` ;
- `WillStayHalfAwakeInsteadSleep = false`.

Encore ne place pas l'invité en half-awake/suspend et `IsInHalfAwake=false` / `IsInFullAwake=true` exposent la même politique. Le fait de ne pas piloter la veille ou le réseau **physiques** de la PS5 est volontaire : BGTC décrit l'état du système Switch virtualisé.

**2 lignes PARTIEL quittent le pool. Nouveau compteur global : 142 lignes ouvertes.**

Arithmétique : **144 - 2 = 142**. Aucun patch runtime ni build PS5 dans cette requalification.


### 2026-11-26 — HDCP + sleep-locks invités : palier global 138

Base : **142 lignes ouvertes**.

Quatre PARTIEL AM sont désormais qualifiés sur les propriétaires réellement sélectionnés :
- `SetHdcpAuthenticationActivated` conserve l'état dans l'Applet sous verrou ; `GetHdcpAuthenticationState` le relit et le changement signale le vrai `HDCPStateChangedEvent` ;
- `RequestToAcquireSleepLock` signale immédiatement le vrai événement de lock, cohérent avec l'absence d'arbitre de sommeil hôte ;
- `ReleaseSleepLock` efface cet événement ;
- vendor **`6a0b05125438a8509d5baddf87e8cb638aac80b1`** complète `ReleaseSleepLockTransiently` : release puis réacquisition immédiate, cohérente avec le même arbitre virtuel toujours disponible.

La PS5 physique n'est ni mise en veille ni soumise à HDCP par ces commandes : elles modélisent l'état du système Switch invité.

**4 lignes PARTIEL quittent le pool. Nouveau compteur global : 138 lignes ouvertes.**

Arithmétique : **142 - 4 = 138**. Gitlink repinné sur `6a0b05125438a8509d5baddf87e8cb638aac80b1`. Aucun build PS5 ni validation console revendiqués.


### 2026-11-26 — capture applet cmd28 : palier global 137

Base : **138 lignes ouvertes**.

`IDisplayController::TakeScreenShotOfOwnLayerEx` est requalifié dans le propriétaire actif `eden-backports` : le handler cmd28 utilise le même chemin de capture réel que cmd8 et écrit effectivement le slot demandé via `DisplayLayerManager::WriteAppletCaptureBufferToSlot`, en respectant la permission capture. Le bit immediate/deferred n'introduit pas de résultat différent sur le backend PS5 synchrone.

**1 ligne PARTIEL quitte le pool. Nouveau compteur global : 137 lignes ouvertes.**

Aucun patch runtime, build PS5 ou validation console dans cette requalification.


### 2026-11-26 — GlobalState StartSleepSequence : palier global 136

Base : **137 lignes ouvertes**.

Le propriétaire actif `IGlobalStateController` expose déjà cmd2 `StartSleepSequence(bool)` avec un comportement explicite : la transition de politique invité est acceptée et ne suspend jamais l'hôte PS5. Les cmds legacy `RequestToEnterSleep` / `EnterSleep` restent explicitement rejetées au lieu de simuler un sommeil réussi.

Pour Encore, la PS5 hôte ne doit pas être mise en veille par un titre Switch ; le no-op réussi de cmd2 est donc une politique HLE volontaire, pas un backend manquant.

**1 ligne PARTIEL quitte le pool. Nouveau compteur global : 136 lignes ouvertes.**


### 2026-11-26 — health-warning virtualisé : palier global 135

Base : **136 lignes ouvertes**.

`IOverlayFunctions::SetHealthWarningShowingState` est requalifié : Encore n'expose volontairement aucun overlay de warning Horizon sur l'hôte PS5, `IsHealthWarningRequired` retourne donc `false`, et le passage `showing=false` signale le vrai `health_warning_disappeared_system_event` attendu par les waiters invités.

Cette politique est cohérente et observable côté invité ; l'absence d'une UI physique PS5 n'est pas un backend manquant.

**1 ligne PARTIEL quitte le pool. Nouveau compteur global : 135 lignes ouvertes.**


### 2026-11-26 — media playback + idle policy applet : palier global 131

Base : **135 lignes ouvertes**.

Vendor **`16e161492b4929e2123627ad2b458a53cbbed409`** aligne le propriétaire final `SelfController` sur l'état Applet déjà utilisé par `ApplicationFunctions` :
- `SetMediaPlaybackState` écrit désormais réellement `m_applet->media_playback_state` sous verrou, comme `SetMediaPlaybackStateForApplication` ;
- `SetIdleTimeDetectionExtension` et `GetIdleTimeDetectionExtension` stockent/restituent déjà l'extension dans l'Applet ; leurs anciens logs `STUBBED` sont supprimés.

Encore ne déclenche pas l'auto-sleep/dimming de l'hôte PS5 depuis l'état Switch invité ; c'est la même politique explicitement documentée par `SetAutoSleepDisabled`. Dans ce modèle, la persistance/lecture cohérente de l'état invité remplit le contrat de ces setters/getter.

**4 lignes PARTIEL quittent le pool** : les deux surfaces media-playback et le couple set/get idle-extension.

**Nouveau compteur global : 131 lignes ouvertes.**

Arithmétique : **135 - 4 = 131**. Gitlink repinné sur `16e161492b4929e2123627ad2b458a53cbbed409`. Aucun build PS5 ni validation console revendiqués.


### 2026-11-26 — PSM cmd17 ABI HOS17+ corrigée : palier global 130

Base : **131 lignes ouvertes** au moteur `692726b2bdb6780999d892ff0848905a3af23bc3` / vendor `16e161492b4929e2123627ad2b458a53cbbed409`.

Vendor `7d2bde9f953bfc0baf7c430b294de53e0e12b675`, puis provenance `8a8416ddb781022acae2f30449dfe1e60c8414f0`, corrige `psm` cmd17 `GetBatteryChargeInfoFields` :
- layout HOS 17+ 0x54 aligné sur libnx : restauration du champ 0x2c miroir de `charger_input_voltage_limit` et padding final 0x10 ;
- correction de `charger_input_current_limit`, auparavant jamais initialisé, et suppression de la double écriture de `charger_input_voltage_limit` ;
- valeurs virtuelles cohérentes : 100000 = 100 %, 4200 mV batterie, 5000 mV / 3000 mA chargeur quand l'hôte expose une charge, 25000 milli-C ; état charging/fast-charge/controller-supply reste dérivé des politiques invitées déjà persistées ;
- le `ResponseBuilder` couvre désormais les 0x54 octets de sortie au lieu du compteur court historique.

Références de contrat : libnx `PsmBatteryChargeInfoFields` HOS17+ (commit `b156b4774fb2df7b93402169509266da7547fc4c`) et comparaison ciblée nxemu `f2b45f5fb0a32830bc0ac53ec4052e2da8f7f9a7`. Aucune donnée électrique de la PS5 n'est présentée comme une batterie Switch réelle : il s'agit d'un périphérique invité virtualisé stable.

**1 ligne PARTIEL quitte le pool. Nouveau compteur global : 130 lignes ouvertes.**

Gitlink repinné sur `8a8416ddb781022acae2f30449dfe1e60c8414f0`. Aucun build PS5 ni validation console revendiqués.


### 2026-11-26 — SSL connection fail-closed : palier global 125

Base : **130 lignes ouvertes** au moteur `4376a75e46d663945817ceaced6f0e6bf8a800ee` / vendor `8a8416ddb781022acae2f30449dfe1e60c8414f0`.

Vendor `cbfb2a24f2f243ce9bb7953b1cc54e6b53823db0` ferme les cinq handlers `ISslConnection` explicitement laissés STUB dans le registre R23 : `Poll`, `GetVerifyCertError`, `GetNeededServerCertBufferSize`, `GetSessionCacheMode` et `FlushSessionCache`.

Ces commandes ne renvoient plus `ResultSuccess` avec des sorties non initialisées ou sans effet. Le backend actif ne fournit pas le contrat correspondant ; Encore renvoie donc `IPC::ResultNotSupported`, en conservant le garde pré-handshake existant pour le cache de session. Les chemins TLS fonctionnels `Peek`, socket/hostname/options et `Set/GetRenegotiationMode` sont inchangés.

**5 lignes raccordées/STUB quittent le pool. Nouveau compteur global : 125 lignes ouvertes.**

Gitlink repinné sur `cbfb2a24f2f243ce9bb7953b1cc54e6b53823db0`. Aucun build PS5 ni validation console revendiqués.


### 2026-11-26 — NOTIF presentation fail-closed : palier global 124

Base : **125 lignes ouvertes**.

Vendor `fec1cb94f73e0c5c0cd40280a1e33341c9a58db6`, provenance `de1be3646aadd33caf2fdb3cc70dbe0db2b9e8d0`, corrige `notif:s` cmd1510 `GetNotificationPresentationSetting`. Le setter cmd1500 était déjà explicitement unsupported et aucun propriétaire Encore/Lichii/Eglantine/nxemu n'a de stockage de présentation réel ; le getter ne renvoie donc plus un succès avec une structure zéro inventée, mais `IPC::ResultNotSupported`.

**1 ligne PARTIEL/ABI-DIFF quitte le pool. Nouveau compteur global : 124 lignes ouvertes.**

Gitlink repinné sur `de1be3646aadd33caf2fdb3cc70dbe0db2b9e8d0`. Aucun build PS5 ni validation console revendiqués.


### 2026-11-26 — NCM LocationResolver : trois faux PARTIEL retirés, palier global 121

Base : **124 lignes ouvertes**.

Relecture ciblée du propriétaire actif `encore-active/eden-backports/src/core/hle/service/ncm/ncm.cpp` contre Atmosphère `ContentLocationResolverImpl` (`Atmosphere-NX/Atmosphere-libs@75c688910baf76c0f5e62a3a7fe90bc0dc7f70a1`) :
- `ResolveApplicationControlPath`, `ResolveApplicationHtmlDocumentPath` et `ResolveApplicationLegalInformationPath` sont, comme dans Atmosphère/Horizon, **strictement redirection-only** ; l'absence de fallback vers le contenu installé n'est donc pas une lacune ;
- `ResolveProgramPath` reste ouvert : Horizon retombe sur le dernier Program content NCM quand aucune redirection n'existe ;
- `ResolveProgramPathForDebug` reste ouvert car Horizon retombe ensuite sur `ResolveProgramPath`.

**3 lignes PARTIEL quittent le pool par requalification prouvée. Nouveau compteur global : 121 lignes ouvertes.**

Aucun patch C++, changement de gitlink, build PS5 ou validation console dans cette requalification.


### 2026-11-26 — NCM Program path fallback installé : palier global 119

Base : **121 lignes ouvertes**.

Vendor `d2fcc456722f2f5a1a6e1d5c9a2f103a0e712ed2`, provenance `25111bacd0aa9e7746e6e6534fcd4865b189f251`, complète les deux vrais PARTIEL restants du Location Resolver :
- `ResolveProgramPath` conserve la priorité des redirections puis utilise `RegisteredCache::GetRegisteredContentPath(program_id, Program)` pour renvoyer le chemin NCM invité `registered/...nca` du storage sélectionné ;
- `ResolveProgramPathForDebug` conserve debug-redirection puis redirection normale, avant le même fallback installé avec `ResultDebugProgramNotFound` en absence de contenu.

Ce comportement suit Atmosphère `ContentLocationResolverImpl` : redirection prioritaire, puis Program content du ContentStorage. Aucun chemin hôte PS5/VFS n'est exposé.

**2 lignes PARTIEL quittent le pool. Nouveau compteur global : 119 lignes ouvertes.**

Gitlink repinné sur `25111bacd0aa9e7746e6e6534fcd4865b189f251`. Aucun build PS5 ni validation console revendiqués.


### 2026-11-26 — PCTL play timer HOS23 : palier global 114

Base : **119 lignes ouvertes** au moteur `c4e90f57b90ad25bc42394c9cf18c34056111732` / vendor `25111bacd0aa9e7746e6e6534fcd4865b189f251`.

Vendor `f26e81dcf7f0d67de46bc098520e5cc6078fda3e`, finalisé par `de705230a87dfe20bfe796a3e2ebfc9ea76d256c`, ferme les cinq PARTIEL `StartPlayTimer`, `StopPlayTimer`, `IsPlayTimerEnabled`, `GetPlayTimerRemainingTime` et `IsRestrictedByPlayTimer` :
- ABI cmd1454 corrigée de `s32` vers `u64 nn::TimeSpanType` en nanosecondes ;
- layout HOS21+ 0x44 décodé selon le reverse fw22.5 : mode daily/weekly, Sunday..Saturday et `limitTime` u16 en minutes ;
- jour courant obtenu depuis `time:u` + timezone invité, pas depuis l'horloge locale PS5 ;
- countdown accumulé avec `steady_clock`, Start/Stop réels durant la session et budget nul = restriction immédiate ;
- séparation entre timer configuré et countdown en cours ; `SetPlayTimerSettingsForDebug` re-dérive l'enabled à partir des règles et remet le compteur à zéro ;
- en mode forced-termination, les requêtes qui constatent l'expiration signalent le vrai `request_suspension_event` déjà exposé par cmd1457 ;
- cmd1459 est synchronisé avec le même état mais conserve son ABI HOS23 0x18, confirmée par les dumps IPC.

Références : `tailiang2008/NX-Pctl-Manager@7cfbe45d7206ea26e6123cdf811a8cad643a42cf` (reverse fw22.5 + layout 0x44) et dumps HOS23 `borntohonk/Switch-Ghidra-Guides`. La persistance inter-redémarrages du sysmodule pctl n'est pas revendiquée ; le contrat IPC/runtime de la session est désormais cohérent.

**5 lignes PARTIEL quittent le pool. Nouveau compteur global : 114 lignes ouvertes.**

Gitlink repinné sur `de705230a87dfe20bfe796a3e2ebfc9ea76d256c`. Aucun build PS5 ni validation console revendiqués.


### 2026-11-26 — PSM politiques batterie virtualisées : palier global 104

Base : **114 lignes ouvertes**.

Requalification des dix PARTIEL PSM cmd2/3/4, 5/6, 8/9, 10/11 et 14 contre le runtime actif et libnx :
- `Enable/DisableBatteryCharging` et `IsBatteryChargingEnabled` partagent un état atomique réel ;
- `Acquire/ReleaseControllerPowerSupply` et `Enable/DisableFastBatteryCharging` mettent à jour l'état invité et signalent `BatteryChargeInfoChanged` ;
- `Enable/DisableEnoughPowerChargeEmulation` alimente directement `IsEnoughPowerSupplied` ;
- cmd14 combine cet override invité avec le power-status disponible ;
- le cmd17 HOS17+ corrigé au palier 130 expose désormais `battery_charging`, `fast_battery_charging` et `controller_power_supply` dans son ABI 0x54.

Les wrappers libnx confirment qu'il s'agit de commandes PSM sans entrée/sortie matérielle cachée supplémentaire, hormis les booléens explicitement exposés. Exiger que ces commandes pilotent la batterie/alimentation **physique PS5** était un mauvais critère de complétude : le matériel Switch est virtualisé, et les observables invités sont maintenant cohérents.

**10 lignes PARTIEL quittent le pool. Nouveau compteur global : 104 lignes ouvertes.**

Aucun nouveau patch C++, changement de gitlink, build PS5 ou validation console dans cette requalification.


### 2026-11-26 — correction de comptage : PSM déjà requalifié, retour au palier global 114

Le palier précédent **104** est annulé : les dix lignes PSM cmd2/3/4, 5/6, 8/9, 10/11 et 14 avaient **déjà été retirées** au palier `171 → 161` (« requalification PSM invité »). Leur relecture reste valide techniquement, mais ne constitue pas dix fermetures nouvelles.

**Compteur global corrigé : 114 lignes ouvertes.** Aucun changement runtime ni gitlink dans cette correction. Les prochains décréments doivent être vérifiés contre l'historique des paliers afin d'éviter tout double comptage.


### 2026-11-26 — NFC/NFP raw operations fail-closed : palier global 111

Base corrigée : **114 lignes ouvertes**.

Vendor `a911924beb0d8adf35e3ca40c29b3b5f6b6136e4`, finalisé par `6eb9ce055566750abd07e0fcfdf9beb22881dac1`, supprime trois faux succès sur des backends absents :
- `nfc:user` cmd1300 `SendCommandByPassThrough` ;
- `nfc:sys` cmd1300 `SendCommandByPassThrough` ;
- `nfp:dbg` cmd206 `WriteNtf`.

Le raw NFC pass-through fabriquait un octet de sortie et `ResultSuccess` alors que `NfcDevice::SendCommandByPassThrough` n'a aucune implémentation. `WriteNtf` atteignait de même un `NfcDevice::WriteNtf` sans écriture réelle. Les trois chemins retournent désormais explicitement `IPC::ResultNotSupported`, sans affecter les chemins Mifare/Amiibo fonctionnels.

`nfp:dbg::BreakTag` reste ouvert : `BreakType::Normal` est réellement implémenté via `FlushWithBreak`, mais les deux autres variantes restent non prises en charge.

**3 lignes PARTIEL quittent le pool. Nouveau compteur global : 111 lignes ouvertes.**

Gitlink repinné sur `6eb9ce055566750abd07e0fcfdf9beb22881dac1`. Aucun build PS5 ni validation console revendiqués.


### 2026-11-26 — BTM pairing database virtualisée : palier global 110

Base : **111 lignes ouvertes**.

Requalification de `btm:sys` cmd3 `GetPairedGamepadCount` contre l'owner actif `encore-active/eden-backports/src/core/hle/service/btm/btm_system_core.cpp`. Le service BTM maintient déjà un lifecycle invité cohérent (`Start/CancelGamepadPairing`, event réel, état `IsGamepadPairingStarted`, clear database). Encore n'expose volontairement **aucune base de pairing Bluetooth Switch** : les manettes PS5/USB sont des périphériques HID hôte et ne doivent pas être fabriquées comme appareils Bluetooth Switch persistants. Dans ce modèle, une base vide et `count=0` est l'état virtuel exact, pas un manque de lecture du matériel PS5.

**1 ligne PARTIEL quitte le pool. Nouveau compteur global : 110 lignes ouvertes.**

Aucun patch runtime, changement de gitlink, build PS5 ou validation console dans cette requalification.


### 2026-11-26 — AUDCTL master volume réellement appliqué : palier global 109

Base : **110 lignes ouvertes**.

Vendor `0bb36bc586e3b26462191a1be3143d0a67d4a7db`, provenance `309d1457511f554971cd19683b3c8b3813aa7598`, ferme `audctl` cmd23 `SetSystemOutputMasterVolume`. Le master 0.0–1.0 ne reste plus un simple champ local :
- il est appliqué immédiatement au sink actif et aux sessions `audout:u` ;
- `SetTargetVolume`, `SetTargetMute` et `SetOutputTarget` calculent désormais le volume effectif `target × master × mute`, donc un changement de cible ne perd plus le master ;
- `GetSystemOutputMasterVolume` continue à relire le même état.

**1 ligne PARTIEL quitte le pool. Nouveau compteur global : 109 lignes ouvertes.**

Gitlink repinné sur `309d1457511f554971cd19683b3c8b3813aa7598`. `SetInputTargetForceEnabled` reste ouvert : aucun consommateur de routage input n'est encore démontré. Aucun build PS5 ni validation console revendiqués.


### 2026-11-26 — AUDCTL propriétaire final corrigé + input target forcé : palier global 108

Base documentée : **109 lignes ouvertes**.

La vérification de la matérialisation native a identifié une erreur de sélection qui invalidait la preuve du dernier palier sans créer une nouvelle ligne fonctionnelle : `prepare-build.sh` installe d'abord `eden-backports`, puis `install-active-core-backports.py`. Or le patch historique `eden-sm-host-wait.patch` réinstallait encore `audio_controller.cpp/.h` depuis `encore-active/eden-core` après le backport. Les améliorations AUDCTL HOS23 et le master-volume du palier 109 pouvaient donc être écrasés dans la source finale de build.

Correction de propriétaire :
- `eden-sm-host-wait.patch` ne possède désormais plus que `sm.h`; le lazy `set:sys` est intégré directement dans l'owner AUDCTL shipping `encore-active/eden-backports/src/core/hle/service/audio/audio_controller.{cpp,h}`;
- `install-active-core-backports.py` matérialise maintenant **3** sources seulement : SM + les deux unités Dynarmic I-cache ; il ne réécrit plus AUDCTL ;
- le contrôle `check-sm-host-wait.py` vérifie séparément le patch SM et l'owner AUDCTL final. Cette correction **ne décrémente pas** le compteur : elle restaure la validité runtime du palier 109 déjà compté.

Vendor `0809e3c8c1e5d2df1505541fb1b7116df312a0d0` ferme ensuite réellement `audctl` cmd16 `SetInputTargetForceEnabled` :
- le booléen est publié dans `AudioCore` par un `atomic_bool` partagé ;
- `audin:u` consulte ce même état dans `AudioIn::Manager::GetDeviceNames` ;
- quand la force est active, le périphérique invité `Uac` reste découvrable même sans périphérique micro hôte ; le chemin PS5 AudioIn dispose déjà du fallback silencieux/validation de buffers, donc aucun périphérique physique Switch n'est inventé ni déréférencé ;
- ABI HOS23 recroisée : un booléen d'entrée, aucune sortie.

**1 ligne PARTIEL quitte le pool : nouveau compteur global = 108 lignes ouvertes.**

Gitlink vendor attendu : `0809e3c8c1e5d2df1505541fb1b7116df312a0d0`. Aucun build PS5 ni validation console revendiqués. La correction de propriétaire est un correctif de sélection runtime ; le décrément 109 → 108 correspond uniquement à `SetInputTargetForceEnabled`.


### 2026-11-26 — NFP BreakTag variantes non qualifiées fail-closed : palier global 107

Base : **108 lignes ouvertes**.

Vendor `ace1fe766114a97ff78b4401c65120fe1c4d3863` ferme le dernier PARTIEL `nfp:dbg` cmd203 `BreakTag` sans modifier le chemin Amiibo fonctionnel :
- `BreakType::Normal` continue à passer par l'implémentation existante `Interface::BreakTag → DeviceManager::BreakTag → NfcDevice::FlushWithBreak`, qui écrit réellement le tag/backup quand l'état et les clés le permettent ;
- les deux autres valeurs de `BreakType`, toujours sans sémantique qualifiée dans les références publiques et non prises en charge par le backend, sont interceptées dans l'owner shipping `eden-backports/src/core/hle/service/nfp/nfp.cpp` et retournent désormais `IPC::ResultNotSupported`;
- elles ne sont donc plus maquillées en `ResultWrongDeviceState`, qui confondait une fonctionnalité non implémentée avec l'état du périphérique.

Aucun nouveau backend NFC, aucune écriture synthétique et aucun changement du chemin `Normal`.

**1 ligne PARTIEL quitte le pool : nouveau compteur global = 107 lignes ouvertes.**

Gitlink vendor attendu : `ace1fe766114a97ff78b4401c65120fe1c4d3863`. Aucun build PS5 ni validation console revendiqués.


### 2026-11-26 — AM save-data permission fail-closed : palier global 106

Base : **107 lignes ouvertes**.

Requalification de `IApplicationAccessor::HasSaveDataAccessPermission` (cmd170) sur l'owner shipping actuel `encore-active/eden-backports/src/core/hle/service/am/service/application_accessor.cpp` :
- le titre courant obtient l'accès à son propre save (`application_id == m_applet->program_id`) ;
- toute demande cross-title est refusée tant qu'Encore ne possède pas de modèle ACL inter-title qualifié ;
- le refus par défaut est la politique de sécurité correcte : l'absence de base ACL ne doit jamais élargir les droits de l'invité.

La limitation historique « ACL inter-title non modélisées » ne rend donc plus la commande PARTIELLE : le contrat de permission reste déterministe et fail-closed.

**1 ligne PARTIEL quitte le pool : nouveau compteur global = 106 lignes ouvertes.**

Aucun patch C++, changement de gitlink, build PS5 ou validation console dans cette requalification.


### 2026-11-26 — NCM RightsId cache conforme au contrat : palier global 105

Base : **106 lignes ouvertes**.

Vendor `54e031bb4a27a01b97b11e3b566425260929355d` complète `IContentStorage` cmd27 `GetRightsIdFromPlaceHolderIdWithCache` en suivant le comportement d'Atmosphère `ContentStorageImpl` :
- lookup prioritaire par `cache_content_id` ;
- au miss, lecture du placeholder réel et extraction `RightsId + key_generation` ;
- stockage du résultat pour les appels suivants ;
- cache borné par `StorageId + ContentId`, comme un cache propre à chaque ContentStorage, pour éviter toute collision entre storages ;
- `ncm` cmd13 `InvalidateRightsIdCache` vide réellement le cache ;
- les `ContentAttributes` non nuls, que le VFS Encore ne sait pas encore interpréter, restent fail-closed avec `IPC::ResultNotSupported` au lieu d'un succès fictif.

La ligne n'est donc plus seulement « résultat exact sans optimisation cache » : le chemin cache fait désormais partie du comportement observable et est réellement représenté.

**1 ligne PARTIEL quitte le pool : nouveau compteur global = 105 lignes ouvertes.**

Gitlink vendor attendu : `54e031bb4a27a01b97b11e3b566425260929355d`. Aucun build PS5 ni validation console revendiqués.


### 2026-11-26 — SFDNSRES owner final resynchronisé + cmd14 qualifié : palier global 104

Base : **105 lignes ouvertes**.

La vérification du propriétaire final a trouvé une dérive de sélection : `headless/CMakeLists.txt` compile directement `encore-active/eden-core/src/core/hle/service/sockets/sfdnsres.cpp`, alors que les corrections récentes étaient présentes dans le backport canonique. La gate N21 définit déjà la dérivation exacte `eden-backports/sfdnsres.cpp → eden-core/sfdnsres.cpp` avec seulement les transformations d'audit réseau.

Vendor `83e0306d0b0e8b7903488458227f4b89411668b0` régénère l'owner final selon cette dérivation existante. Cela restaure notamment les handlers resolver récents, `DNS_PRIV`, cancel-handle et les formes HOS23 déjà comptées ; **aucun de ces éléments n'est recompté**.

Pour cmd14 `ResolverSetOptionRequest` :
- l'owner final consomme désormais l'`option_id` et le buffer opaque ;
- il renvoie la forme ABI complète `ret=0 + bsd_errno=0` ;
- le reverse SDK et Ryujinx confirment que les options connues du SDK sont traitées en amont et que le setter module est un no-op réussi pour le reste ; ne pas interpréter ces options dans le resolver hôte n'est donc plus une absence fonctionnelle.

**1 ligne PARTIEL quitte le pool : nouveau compteur global = 104 lignes ouvertes.**

Gitlink vendor attendu : `83e0306d0b0e8b7903488458227f4b89411668b0`. Aucun build PS5 ni validation console revendiqués.


### 2026-11-26 — LBL backlight invité + TS thermiques virtuelles requalifiés : palier global 100

Base : **104 lignes ouvertes**.

Quatre anciennes lignes PARTIEL sont requalifiées sur leurs propriétaires shipping, sans modification C++ :

- `lbl` cmd6 `SwitchBacklightOn` et cmd7 `SwitchBacklightOff` modifient réellement `backlight_enabled`; cmd8 `GetBacklightSwitchStatus` relit cet état, et `SaveCurrentSetting/LoadCurrentSetting` le préservent avec le reste de l'état LBL. Le `fade_time` est consommé mais la transition visuelle n'est volontairement pas appliquée au matériel PS5. Un HLE Switch ne doit pas piloter le rétroéclairage physique de l'hôte : l'état invité observable est bien représenté.
- `ts` cmd1 `GetTemperature` et cmd3 `GetTemperatureMilliC` renvoient des valeurs nominales cohérentes pour les deux locations Switch (`Internal=35°C`, `External=20°C`) et leur équivalent exact en milli-degrés. Exposer les thermiques PS5 comme thermiques Switch serait incorrect ; la sonde virtuelle stable constitue la politique HLE attendue pour un matériel invité absent.

Ces quatre commandes ne sont donc plus ouvertes au seul motif qu'elles ne contrôlent/mesurent pas le matériel physique PS5.

**4 lignes PARTIEL quittent le pool : nouveau compteur global = 100 lignes ouvertes.**

Aucun patch C++, changement de gitlink, build PS5 ou validation console dans cette requalification.


### 2026-11-26 — AM health-warning policy cohérente : palier global 99

Base : **100 lignes ouvertes**.

Requalification de `IOverlayFunctions::SetHealthWarningShowingState` (cmd30) contre l'owner shipping :
- `IsHealthWarningRequired` retourne explicitement `false` : Encore ne présente pas de warning santé Switch fictif sur la PS5 ;
- dans cette politique invitée, `showing=true` n'a aucun overlay à matérialiser ;
- `showing=false` signale `health_warning_disappeared_system_event`, ce qui libère correctement les waiters au lieu de les bloquer sur une UI inexistante.

La limitation historique « signal disparition seulement » est donc cohérente avec la décision HLE « warning jamais requis », et non une fonctionnalité matérielle manquante.

**1 ligne PARTIEL quitte le pool : nouveau compteur global = 99 lignes ouvertes.**

Aucun patch C++, changement de gitlink, build PS5 ou validation console dans cette requalification.


### 2026-11-26 — NOTIF alarmes/paramètres partagés : palier global 93

Base : **99 lignes ouvertes**.

Le propriétaire shipping NOTIF avait déjà dépassé l'état du snapshot historique : `NotificationServiceImpl` stocke réellement, pour chaque `AlarmSettingId`, le buffer application (taille exacte ≤ 0x400), le remplace lors d'un update, le restitue dans `LoadApplicationParameter` et le supprime avec l'alarme.

Le défaut restant était structurel : `notif:a` et `notif:s` construisaient chacun leur propre `NotificationServiceImpl`, donc une alarme enregistrée via une façade n'existait pas pour l'autre.

Vendor `e189aaf08aff79a15aa6272e57ce3bdcd9b7af9c` :
- construit un seul `NotificationServiceImpl` dans `glue.cpp` ;
- injecte le même `shared_ptr` dans `INotificationServicesForApplication` et `INotificationServices` ;
- conserve les méthodes Register/Update/Load/Delete existantes et leur stockage réel ; aucun faux backend persistant disque n'est ajouté.

Les trois contrats historiques PARTIEL `RegisterAlarmSetting`, `UpdateAlarmSetting` et `LoadApplicationParameter` sont donc cohérents sur **les deux façades** `notif:a` / `notif:s`.

**6 lignes PARTIEL quittent le pool : nouveau compteur global = 93 lignes ouvertes.**

Gitlink vendor attendu : `e189aaf08aff79a15aa6272e57ce3bdcd9b7af9c`. Aucun build PS5 ni validation console revendiqués.


### 2026-11-26 — NIFM legacy scan/access-point hors HOS23 : palier global 91

Base : **93 lignes ouvertes**.

Deux lignes historiques NIFM avaient conservé leur statut PARTIEL malgré une fenêtre firmware fermée :
- cmd11 `GetScanDataOld` : **HOS 1.0.0–3.0.2** ;
- cmd13 `GetCurrentAccessPointOld` : **HOS 1.0.0–3.0.2**.

La cible NS1 actuelle est HOS23 ; ces anciens layouts `AccessPointDataOld` 0x34 ne font donc pas partie du contrat runtime cible. Elles n'étaient pas comprises dans la précédente requalification firmware qui avait traité d'autres familles legacy.

**2 lignes PARTIEL → HORS-VERSION : nouveau compteur global = 91 lignes ouvertes.**

Aucun patch C++, changement de gitlink, build PS5 ou validation console.


### 2026-11-26 — Time cmd50 permissions HOS23 qualifiées : palier global 90

Base : **91 lignes ouvertes**.

Requalification de `time:u/time:a/time:s` cmd50 `SetStandardSteadyClockInternalOffset` :
- SwitchBrew confirme que `time:s` reste un `IStaticService` HOS23 et que `time:u/time:a` sont les façades Glue ;
- `time:u` et `time:a` sont créés avec `can_write_steady_clock=false` ;
- le `time:s` HOS23 est créé par le service manager avec uniquement `can_write_network_clock=true`, donc lui aussi `can_write_steady_clock=false`;
- le PSC `StaticService::SetStandardSteadyClockInternalOffset` vérifie cette permission **avant** son fallback `ResultNotImplemented` et renvoie donc `ResultPermissionDenied` sur les trois services concernés ;
- la façade repair `time:r`, hors de cette ligne historique, possède `can_write_steady_clock=true` et son wrapper Glue applique réellement l'offset via `set:sys`.

Le chemin observé par les services de la ligne est donc déterministe et conforme à leurs permissions ; le code `ResultNotImplemented` n'est pas atteignable pour eux.

**1 ligne PARTIEL quitte le pool : nouveau compteur global = 90 lignes ouvertes.**

Cmd102 `GetStandardUserSystemClockInitialYear` reste ouvert : la façade PSC `time:s` renvoie encore `ResultNotImplemented`, contrairement au wrapper Glue qui lit `set:sys`.

Aucun patch C++, changement de gitlink, build PS5 ou validation console.


### 2026-11-26 — Time cmd102 PSC aligné sur set:sys : palier global 89

Base : **90 lignes ouvertes**.

Correctif vendor `60d87a82acdd1c385ba2525eec7bed15642e418b` sur le propriétaire PSC actif `sources/eden/src/core/hle/service/psc/time/static.cpp` :
- cmd102 `GetStandardUserSystemClockInitialYear` ne renvoie plus `ResultNotImplemented` ;
- il lit désormais `time / standard_user_clock_initial_year` via `set:sys`, exactement comme la façade Glue déjà qualifiée ;
- aucun fallback synthétique ni constante firmware n'est introduit.

**1 ligne PARTIEL quitte le pool : nouveau compteur global = 89 lignes ouvertes.**

Gitlink vendor repinné sur `60d87a82acdd1c385ba2525eec7bed15642e418b`. Aucun build PS5 ni validation console revendiqués.


### 2026-11-26 — HomeMenu LockAccessor requalifiés : palier global 87

Base : **89 lignes ouvertes**.

Les deux PARTIEL historiques `IHomeMenuFunctions` cmd30 `GetHomeButtonWriterLockAccessor` et cmd31 `GetWriterLockAccessorEx` ont été recroisés avec HOS23 et libnx :
- HOS23 confirme que les deux commandes retournent `ILockAccessor` ; cmd31 prend un `u32` button type ;
- libnx traite l'objet uniquement via son event non-autoclear, `TryLock`, `Unlock` et la répétition de `TryLock` après attente ; aucun état reader/writer global n'est exposé par l'ABI ;
- l'owner Encore actif retourne des `ILockAccessor` concrets dont l'event est signalé à la création et à l'unlock, et dont `TryLock`/`IsLocked` conservent l'état ;
- une implémentation indépendante récente (Recompia) emploie le même modèle de verrou par accessor. Cela ne prouve pas l'algorithme interne Horizon, mais invalide l'ancien motif « arbitre reader/writer global obligatoire » comme défaut fonctionnel démontré.

**2 lignes PARTIEL quittent le pool : nouveau compteur global = 87 lignes ouvertes.**

Aucun patch C++, changement de gitlink, build PS5 ou validation console. Le comportement interne exact d'Horizon n'est pas revendiqué ; seule la conformité observable de l'interface est requalifiée.


### 2026-11-26 — Home-button double-click state qualifié : palier global 85

Base : **87 lignes ouvertes**.

Les deux PARTIEL historiques `IAppletCommonFunctions` cmd50 `SetHomeButtonDoubleClickEnabled` et cmd51 `GetHomeButtonDoubleClickEnabled` sont requalifiés :
- HOS23 et libnx confirment un setter bool sans sortie et un getter bool ;
- l'owner actif Encore conserve le booléen dans `Applet::home_button_double_click_enabled` sous `applet->lock` et le getter relit exactement le même état ;
- aucun effet hôte PS5 ni backend Nintendo externe n'est requis par le contrat IPC observable de ces deux commandes.

**2 lignes PARTIEL quittent le pool : nouveau compteur global = 85 lignes ouvertes.**

Aucun patch C++, changement de gitlink, build PS5 ou validation console.


### 2026-11-26 — NIFM getters d'état requalifiés : palier global 83

Base : **85 lignes ouvertes**.

Deux lignes PARTIEL NIFM sont séparées des setters/politiques d'arbitrage qui restent réellement incomplets :
- cmd41 `GetAcceptableNetworkTypeFlag` : HOS23 attend un `u32`; Encore relit exactement le `u32` conservé par cmd40 ;
- cmd20 `GetRevision` de `IRequest` : HOS23 attend un `u32`; Encore relit exactement `requirement_revision` conservé par cmd18.

Le fait que les setters associés ne pilotent pas encore toute la sélection/arbitrage réseau ne rend pas ces **getters** partiels : leur contrat observable propre est rempli. Les setters cmd40/cmd18 restent dans le pool.

**2 lignes PARTIEL quittent le pool : nouveau compteur global = 83 lignes ouvertes.**

Aucun patch C++, changement de gitlink, build PS5 ou validation console.


### 2026-11-26 — FSP cache index requalifié : palier global 82

Base : **83 lignes ouvertes**.

Le PARTIEL historique `fsp-srv` cmd34 `GetCacheStorageSize` reposait sur une limitation « index 0 uniquement ». Elle n'existe plus dans l'owner actif :
- l'ABI accepte l'index et renvoie les deux tailles data/journal ;
- Encore valide désormais tout index `0..0xFFFF` ;
- `GetCacheStorageDirectoryName(program_id, index)` distingue l'index 0 et encode explicitement les autres en suffixe `_XXXX` ;
- le handler ouvre le répertoire correspondant et relit le vrai `.yuzu_save_size` pour retourner `normal` et `journal`.

La limitation historique sur les index multiples est donc obsolète. Les autres lignes FSP ExtraData/reader restent ouvertes lorsque l'identité SdUser, l'intégrité/hash-salt ou les métadonnées ExtraData ne sont pas réellement reproduites.

**1 ligne PARTIEL quitte le pool : nouveau compteur global = 82 lignes ouvertes.**

Aucun patch C++, changement de gitlink, build PS5 ou validation console.


### 2026-11-26 — CAPS liste deprecated ARUID requalifiée : palier global 81

Base : **82 lignes ouvertes**.

Le PARTIEL historique `caps:u` cmd140 `GetAlbumFileList1AafeAruidDeprecated` est requalifié :
- il ne possède pas de paramètre UID utilisateur à filtrer ;
- l'owner actif appelle le même `AlbumManager::GetAlbumFileList` réel avec type, plage de dates et ARUID que cmd142 déjà qualifié ;
- il convertit ensuite chaque `ApplicationAlbumEntry` vers `ApplicationAlbumFileEntry` (entrée, datetime et champ réservé) pour l'ABI deprecated.

Le motif historique « mêmes limites que cmd142 » est donc obsolète depuis la qualification de cmd142. Les cmd141/143 restent PARTIEL : leur `user_id` est encore explicitement ignoré.

**1 ligne PARTIEL quitte le pool : nouveau compteur global = 81 lignes ouvertes.**

Aucun patch C++, changement de gitlink, build PS5 ou validation console.


### 2026-11-26 — VI résolution/modes d'affichage requalifiés : palier global 78

Base : **81 lignes ouvertes**.

Lot VI sur le propriétaire actif :
- vendor `d7b956dab1027876f62cfa7d9af6912ab4f4990c` corrige `IApplicationDisplayService` cmd1102 `GetDisplayResolution` : HOS23/libnx confirment le propriétaire et l'ABI `display_id -> s64 width, s64 height`; Encore ne force plus 1280x720 et retourne désormais la résolution virtuelle dockée/portable cohérente avec les autres services VI ;
- cmd3000 `ListDisplayModes` est requalifié : le backend d'émulation expose volontairement un mode virtuel unique, avec dimensions dockées/portables et fréquence d'affichage 60 Hz ;
- cmd3200 `GetDisplayMode` retourne le même mode virtuel courant. Le commentaire historique « 60 Hz incorrect pour un jeu 30 FPS » ne constitue pas une divergence : cadence de rendu du titre et fréquence du display sont distinctes.

Les dumps HOS23 confirment cmd3000 (liste de `DisplayMode`) et cmd3200 (structure 0x10), et une implémentation indépendante récente emploie également un mode virtuel 60 Hz ; EglantinePS5 applique le même principe. Les cmd8250/8252 shared-layer restent ouverts : leurs transitions restent des succès sans état explicite tandis que close/disconnect sont encore unsupported.

**3 lignes quittent le pool : nouveau compteur global = 78 lignes ouvertes.**

Gitlink vendor repinné sur `d7b956dab1027876f62cfa7d9af6912ab4f4990c`. Aucun build PS5 ni validation console.


### 2026-11-26 — ACC IManagerForSystemService désambiguïsé : palier global 75

Base : **78 lignes ouvertes**.

Les trois AMBIGU historiques `acc:su` cmd0/1/2 sont désormais rattachés sans ambiguïté :
- les dumps HOS23 montrent que `GetBaasAccountManagerForSystemService` retourne explicitement `nn::account::baas::IManagerForSystemService`, dont les commandes 0/1/2 sont `CheckAvailability`, `GetAccountId` et `EnsureIdTokenCacheAsync` ;
- Encore retourne un identifiant de compte local stable pour cmd1 à partir du UUID du profil ;
- cmd2 est fail-closed via le rejet Nintendo Account existant, faute de backend réseau correspondant ;
- vendor `5bdf4cef1f47b00beda4e6597fd3d2222de0a305` raccorde également cmd0 `CheckAvailability` à ce rejet explicite au lieu du précédent `R_SUCCEED()` STUB qui simulait une disponibilité inexistante.

**3 lignes AMBIGU quittent le pool : nouveau compteur global = 75 lignes ouvertes.**

Gitlink vendor repinné sur `5bdf4cef1f47b00beda4e6597fd3d2222de0a305`. Aucun build PS5 ni validation console.


### 2026-11-26 — ES objets opaques fail-closed : palier global 72

Base : **75 lignes ouvertes**.

Les trois AMBIGU historiques du service eTicket principal sont désormais résolus :
- SwitchBrew rattache bien cmd1003 au service `es` et documente un retour `EsAsyncValue` depuis HOS 6 ;
- cmd2000 (HOS 6+) et cmd2001 (HOS 9+) retournent chacun un `EsSubinterface2000` ;
- les interfaces enfants restent elles-mêmes opaques/non documentées et Encore ne possède pas le backend Horizon/eTicket permettant de les reproduire correctement.

Vendor `e823d1cae61b893688e66809c8d2dbe682ebda53` raccorde donc cmd1003/2000/2001 à `RejectUnavailableTicketManagement` au lieu de laisser des pointeurs `nullptr`. Aucun objet asynchrone ou sous-interface fictive n'est créé.

**3 lignes AMBIGU quittent le pool : nouveau compteur global = 72 lignes ouvertes.**

Gitlink vendor repinné sur `e823d1cae61b893688e66809c8d2dbe682ebda53`. Aucun build PS5 ni validation console.


### 2026-11-26 — ABI historiques BTDRV/NPNS/SPL hors contrat HOS23 : palier global 68

Base : **72 lignes ouvertes**.

Quatre ABI-DIFF historiques sont requalifiés **HORS-VERSION / ancien rattachement**, après comparaison directe aux tables HOS23 et aux owners Encore actifs :
- BTDRV cmd34 : ancien libellé `ExtSetRadio`; HOS23 expose `EnableRadio`, et l'owner actif Encore expose exactement `EnableRadio` au même ID ;
- NPNS ancien cmd1 `ListenTo` : HOS23 cmd1 = `ListenAll` ;
- NPNS ancien cmd2 `ListenToMyApplicationId` : HOS23 cmd2 = `ListenTo`, tandis que `ListenToMyApplicationId` est cmd26 ; Encore expose la même table 1/2/26 ;
- SPL ancien cmd31 agrégé `UnwrapElicenseKey` : HOS23 `IGeneralInterface` cmd31 = `GetPackage2Hash`; l'interface ES dérivée emploie cmd31 pour `PrepareEsArchiveKey`. L'ancienne ligne agrégée n'est donc pas un contrat HOS23 valide.

Aucune de ces quatre lignes ne représente un défaut runtime actuel de la cible HOS23.

**4 lignes ABI-DIFF quittent le pool : nouveau compteur global = 68 lignes ouvertes.**

Aucun patch C++, changement de gitlink, build PS5 ou validation console.


### 2026-11-26 — Friend V1 / time:al / nvmemp requalifiés : palier global 64

Base : **68 lignes ouvertes**.

Quatre lignes historiques quittent le pool :
- Friend cmd20600 : HOS23 nomme explicitement `GetUserPresenceViewV1`; Encore expose exactement ce nom et fail-closed faute de backend Nintendo Online ;
- Friend cmd20800 : HOS23 nomme explicitement `LoadUserSettingV1`; Encore expose exactement ce nom et fail-closed pour la même raison. Les deux anciens ABI-DIFF étaient dus à l'absence du suffixe V1 dans le catalogue historique ;
- `time:al` cmd0 `GetWakeUpEvent` était mal rattaché : HOS23 définit le service racine `IAlarmService` cmd0 comme `CreateWakeupAlarm`; l'event appartient à l'objet enfant `ISteadyClockAlarm`. L'ancienne ligne n'est pas un contrat du service racine ;
- `nvmemp` cmd1 `GetPid` : l'owner shipping courant expose désormais le bon nom HOS23 et `RejectUnavailableMemoryProfiler`. Le service NVIDIA memory-profiler est optionnel/non disponible sur retail ; Encore échoue explicitement au lieu de trapper sur `UNIMPLEMENTED`.

**4 lignes quittent le pool : nouveau compteur global = 64 lignes ouvertes.**

Aucun nouveau patch C++ dans cette étape, aucun changement de gitlink, build PS5 ou validation console.


### 2026-11-26 — SPSM HOS23 + ABI NS historiques : palier global 61

Base : **64 lignes ouvertes**.

Trois lignes historiques quittent le pool, et la table SPSM HOS23 est complétée :
- SPSM cmd0 `GetCurrentState` : l'owner shipping courant expose déjà le nom HOS23 exact et retourne le `u32 0` (état virtuel Awake) avec succès ; l'ancien ABI-DIFF `GetState` est obsolète ;
- les dumps HOS23 montrent aussi que SPSM reste présent (contrairement à l'ancien classement « hors-version après HOS13 »). Vendor `7ce2ff553b8ee272612b66b10537716f3d2f1330` ajoute les commandes HOS17/18+ 12–16 (`EmulatePowerButtonPressedBriefly`, `EmulatePowerButtonPressedFor7Sec`, `SetAlwaysRebootFlag`, `SetWakeReasonOverride`, `SetWakeupAlarm`) au rejet matériel explicite existant. Les commandes 1–10 déjà raccordées restent fail-closed lorsque leur effet contrôlerait la PS5 ;
- NS ApplicationManager cmd2513 : HOS23 nomme désormais `LaunchMicroApplication`; Encore expose ce nom et rejette explicitement le backend platform non disponible. L'ancien `LaunchPreomia` est un libellé historique ;
- `IDevelopInterface` HOS23 ne contient plus de cmd8 : l'ancienne ligne `LaunchApplicationForDevelop` est hors contrat HOS23.

**3 lignes quittent le pool : nouveau compteur global = 61 lignes ouvertes.**

Gitlink vendor repinné sur `7ce2ff553b8ee272612b66b10537716f3d2f1330`. Aucun build PS5 ni validation console.

### 2026-11-26 — ABI historiques AM/NS/NVDRV requalifiées : palier global 56

Base : **61 lignes ouvertes**.

Cinq ABI-DIFF historiques quittent le pool après recroisement avec les tables HOS23 et les propriétaires actifs :
- `ISelfController` : l'ancienne ligne `GetDebugStorageChannel` au cmd2 est mal rattachée. HOS22.5/HOS23 exposent cette commande au **cmd1000**, avec retour `IStorageChannel`; Encore expose également cmd1000. La ligne cmd2 ne décrit donc pas un contrat HOS23 ;
- racine `IServiceGetterInterface` des services `ns:am2/ns:ec/ns:rid/ns:rt/ns:web` : l'ancienne ligne cmd0 `Attach` est hors table courante. Les getters HOS actuels sont dans la plage 7988–7999 ;
- l'ancienne ligne root NS cmd1 `BoostSystemMemoryResourceLimit` est elle aussi mal rattachée : ce n'est pas le cmd1 de `IServiceGetterInterface`. Le nom existe par ailleurs sur des interfaces dédiées (notamment PM shell cmd7 et NS ApplicationManager dans sa propre table), qui restent suivies par leurs vrais propriétaires ; aucune fonctionnalité n'est déclarée complète par cette suppression ;
- NVDRV cmd7 : HOS23 nomme `SetAruidWithoutCheck`, pas l'ancien `SetAruid`/forme de test ; l'owner actuel expose ce cmd7 ;
- NVDRV cmd8 : HOS23 nomme `SetAruid` avec PID, pas l'ancien `SetAruidByPID`; l'owner actuel expose ce cmd8.

Ces cinq lignes sont supprimées uniquement comme **anciens contrats de catalogue incorrects/obsolètes**. Les implémentations réelles des propriétaires correspondants restent qualifiées séparément lorsqu'elles sont partielles ou fail-closed.

**5 lignes ABI-DIFF quittent le pool : nouveau compteur global = 56 lignes ouvertes.**

Aucun patch C++ runtime, changement de gitlink, build PS5 ou validation console dans cette étape.

### 2026-11-26 — CAPS session + NOTIF HOS23 requalifiés : palier global 53

Base : **56 lignes ouvertes**.

Trois lignes quittent le pool :
- CAPS `IAlbumControlSession` cmd2001 `OpenAlbumMovieReadStream` et cmd2002 `CloseAlbumMovieReadStream` : le vendor actif `7ce2ff553b8ee272612b66b10537716f3d2f1330` expose déjà `OpenControlSession` cmd60001, retourne un objet `IAlbumControlSession` concret et y enregistre cmd2001/2002 (ainsi que les autres commandes movie-read/write HOS23) vers un rejet explicite `ResultNotSupported` faute de backend movie. Les anciennes ABI-DIFF provenaient du propriétaire parent `caps:c`, pas de la sous-interface active ;
- NOTIF cmd1510 : les dumps HOS22.5/HOS23 nomment `GetNotificationPresentationSetting`; l'owner actif expose exactement ce nom et son handler. L'ancien libellé `GetPresentationSetting` est historique.

**3 lignes ABI-DIFF quittent le pool : nouveau compteur global = 53 lignes ouvertes.**

Aucun nouveau patch C++, changement de gitlink, build PS5 ou validation console dans cette étape.

### 2026-11-26 — audrec:a suspend/resume fail-closed : palier global 51

Base : **53 lignes ouvertes**.

Les deux ABI-DIFF `audrec:a` cmd0/cmd1 sont traitées sur le propriétaire réellement compilé :
- SwIPC documente `IFinalOutputRecorderManagerForApplet` cmd0 `RequestSuspendFinalOutputRecorders` et cmd1 `RequestResumeFinalOutputRecorders`; à partir de HOS4 les deux commandes conservent leur entrée mais ne retournent plus le handle historique HOS1–3 ;
- l'owner Eden utilisait les noms courts `RequestSuspend` / `RequestResume` mais laissait encore les deux slots `nullptr` ;
- vendor `f27f79c3cbcbbdfd16530ba22bb170a34fe425fa` raccorde désormais cmd0/cmd1 à `RejectUnavailableFinalOutputRecorderControl`, qui renvoie `ResultNotSupported` au guest faute de backend final-output-recorder, sans toucher à `audout:u`, `audin:u`, `audren:u` ni au rendu audio normal.

**2 lignes quittent le pool : nouveau compteur global = 51 lignes ouvertes.**

Gitlink vendor repinné sur `f27f79c3cbcbbdfd16530ba22bb170a34fe425fa`. Aucun build PS5 ni validation console.

### 2026-11-26 — NEWS cmd30500 HOS23 qualifié : palier global 50

Base : **51 lignes ouvertes**.

L'ABI-DIFF historique `INewsService` cmd30500 est requalifié contre le dump HOS23 :
- HOS23 rattache bien cmd30500 à `nn::news::detail::ipc::INewsService`, sous le nom opaque `Cmd30500`, avec 8 octets d'entrée, un buffer d'entrée, un handle d'entrée et un objet `IDownloadContext` en sortie ;
- l'ancien catalogue décrivait ce slot par une phrase spéculative plutôt que par un nom ABI stable ;
- l'owner actif Encore enregistre déjà cmd30500 comme `Unknown30500` et le route vers `RejectUnavailableNewsBackend`, donc l'appel est traité explicitement sans inventer un backend News.

**1 ligne ABI-DIFF quitte le pool : nouveau compteur global = 50 lignes ouvertes.**

Aucun patch C++, changement de gitlink, build PS5 ou validation console dans cette étape.

### 2026-11-26 — debug-handle SVC fail-closed : palier global 48

Base : **50 lignes ouvertes**.

Vendor `f439f76906f1267a172fc72df82f4b1dbb1ea52d` ferme les deux PARTIEL SVC dus au debugger non implémenté :
- `svcGetProcessId` (0x24) conserve les chemins process/thread réels ; un objet d'un autre type ne déclenche plus `UNIMPLEMENTED_MSG`, mais retourne `ResultInvalidHandle`. Horizon accepte également un `Handle<Debug>` sur ce SVC, mais Encore n'expose aucun objet debug ;
- `svcGetThreadList` (0x66) conserve le chemin `InvalidHandle` utilisé par Encore pour le processus courant ; tout handle debugger, impossible à produire dans ce runtime, retourne désormais `ResultInvalidHandle` au lieu de traverser `UNIMPLEMENTED_IF` puis d'énumérer silencieusement le mauvais processus.

Cette correction élimine deux chemins host-side `UNIMPLEMENTED` sans inventer de debugger et sans modifier les listes process/thread ordinaires.

**2 lignes PARTIEL quittent le pool : nouveau compteur global = 48 lignes ouvertes.**

Gitlink vendor repinné sur `f439f76906f1267a172fc72df82f4b1dbb1ea52d`. Aucun build PS5 ni validation console.

### 2026-11-26 — SVC GetInfo HOS14/HOS23 : correction du runtime actif, compteur global 48 inchangé

Sur la branche NS1, le dispatch `GetInfo` réellement compilé est l'overlay vendor `encore-active/eden-backports/src/core/hle/kernel/svc/svc_info.cpp` ; son enum `svc_types.h` est également sélectionné par le manifeste de backports. Ces fichiers sont repinnés par le moteur et leurs deux empreintes SHA-256/tailles dans `encore-active/eden-backports/manifest.json` ont été mises à jour transactionnellement.

**Corrections C++ runtime :**
- HOS23 `InfoType::AddressSpaceSize = 36` ajouté au dispatch. Retour de la taille réelle d'espace d'adressage de la page table du **processus référencé par le handle** (contrat libnx/svcGetInfo), pas une constante inventée.
- `InfoType::AliasRegionExtraSize` utilisait auparavant `GetCurrentProcessPointer()` malgré un handle de processus validé : lecture corrigée sur le `KProcess` du handle.
- HOS14+ `InfoType::IsSvcPermitted = 26` lit désormais les capacités NPDM du `KProcess` via `GetSvcPermissions()` pour l'unique SVC interrogeable `SynchronizePreemptionState (0x36)`, au lieu de `ResultInvalidEnumValue` systématique.
- `DebuggerAttached` contrôle désormais le handle nul et le sous-identifiant 0 avant de répondre que le debugger est absent. Aucun objet debugger ni accès étendu n'est simulé.

**Provenance :** vendor `7592ffcbf76077d6ad4083e988354827aeeb7ecc` puis `7ef6cacf8a6f415fb0bdea8f712be0773250c03b`, moteur/gitlink final `f4dc1bd7d70da4d18cae85ffeaa2dff0f86da7fe`. Les règles HOS14/23 sont recoupées avec SwitchBrew/libnx ; aucune modification des autres SVC, du CPU/JIT ou GPU. Le correctif ne prétend pas fournir les régions shadow-stack 37/38 ni les autres propriétés encore synthétiques.

**Compteur global de revue : 48, inchangé.** La ligne `svcGetInfo` (0x29) reste PARTIEL tant que l'ensemble des cas qui lui appartiennent n'est pas qualifié. Aucun build PS5 ni test console réalisé. Contrôle de cohérence par diff des C++ actifs, emplacement CMake/manifeste et empreintes ; CI/native à qualifier séparément.

### 2026-11-26 — FSP SaveDataExtraData persistant : correction du modèle directory-save, compteur global 48 inchangé

Base : **48 lignes ouvertes**.

La conclusion historique du 22/11 selon laquelle un directory-save ne possède pas d'ExtraData physique est corrigée après recroisement avec l'implémentation LibHac récente : `DirectorySaveDataFileSystem` lit et écrit réellement `SaveDataExtraData`, et l'implémentation étendue ajoute une gestion transactionnelle. Le vendor NS1 **`43606c6334a3e3e07c75ea3f89e9a87229a04424`** remplace donc les succès vides / sorties zéro du propriétaire actif `fsp_srv.cpp` par un état persistant de 0x200 octets.

Adaptation Encore :
- le sidecar est stocké à côté du répertoire de save, hors de la racine montée au guest, afin de ne pas exposer un fichier de métadonnées Horizon dans le filesystem du jeu ;
- les créations cmd22/23/35/37 initialisent `attribute`, `owner_id`, `flags`, `size` et `journal_size` depuis les structures de création déjà reçues ;
- cmd66/cmd70 appliquent le masque octet par octet avec la règle `(new & mask) | (old & ~mask)` ; cmd71 applique le masque de lecture ;
- cmd59 suit le contrat LibHac et ne modifie que `flags` via un masque `0xFFFFFFFF` sur ce champ ;
- cmd57/58/69 relisent les données persistées ; les saves antérieures sans sidecar restent lisibles avec un ExtraData initial reconstruit depuis leur `SaveDataAttribute`.

Le manifeste `eden-backports` est synchronisé (`fsp_srv.cpp` SHA-256 `f54b6d0fbd0f80067682daa5c3383c6fcf585cff2b74b9ee313ef96ad5af4175`, 77 404 octets), et le CMake actif sélectionne bien cette unité. Le patch moteur `headless/backports/eden-fw23-services.patch` ne contient pas les lots FSP accumulés depuis cette ancienne base et n'est donc pas modifié artificiellement ; le runtime shipping est l'overlay vendor épinglé.

**Compteur global : 48, inchangé.** Les cmds 57/58/59/66 restent PARTIEL dans le pool pour une raison distincte : Encore n'a pas encore l'indexer Horizon attribuant des `save_data_id` non nuls/stables aux saves Account/Device, de sorte que la résolution par ID n'est pas complète. Cmd69/70/71 bénéficient du correctif runtime mais n'ajoutent pas de ligne à soustraire au pool actuel. Aucun build PS5 ni test console revendiqué à ce stade.

### 2026-11-26 — SaveDataId Horizon persistant + filtre ID corrigé : 48 → 44

Base précédente : **48 lignes ouvertes**.

Le reliquat FSP cmd57/cmd58/cmd59/cmd66 était maintenu PARTIEL parce que les saves Account/Device/Cache étaient encore exposées avec `SaveDataId=0` et parce que la recherche par ID ne disposait pas d'un indexer Horizon persistant. Le vendor NS1 **`13a627a254d7b1c51f55fd1b8ff98a5d41ef17f7`** ferme ce motif fonctionnel après recroisement avec LibHac :
- les saves non statiques reçoivent un ID monotone persistant à partir de 1 ; le compteur est partagé par la racine `EdenPath::SaveDir` réellement configurée ;
- les saves système à ID statique conservent cet ID comme `SaveDataId` public ;
- les anciennes saves sans sidecar sont migrées au premier scan, sans réutiliser un ID déjà publié ;
- le filtre HOS utilise bien `SaveDataInfo.SaveDataId` (premier champ de l'ABI 0x60), et non `StaticSaveDataId` ;
- cmd57/58 relisent désormais l'ExtraData 0x200 persistant ; cmd59 met à jour `flags` conformément au masque legacy ; cmd66 applique le masque byte-for-byte puis persiste l'état.

Le même candidat corrige la provenance du vendor : `sources/eden` SPL/audrec est revenu au miroir exact `eden-emulator/mirror@5f142c7926d0c7fcbbd0ce30794d72f638a43b2a`, la sémantique audrec NS1 reste dans `encore-active/eden-backports`, et les hashes des overlays HID/NIM/NS/VI/OMM revus sont synchronisés. Les unités SPL, audrec et FSP sont bien sélectionnées par le CMake actif.

**Compteur global de revue : 44 lignes ouvertes.** Ce décrément qualifie les quatre lignes cmd57/58/59/66 sur preuve statique/runtime active ; il ne constitue pas une validation PS5. CI hôte, build natif et console restent des niveaux de preuve séparés.
### 2026-11-26 — NIFM IRequest revision qualifiée : 44 → 43

Base précédente : **44 lignes ouvertes**.

Le PARTIEL `IRequest` cmd18 `SetRequirementByRevision` est requalifié sur le propriétaire NIFM actif :
- l'ABI HOS23/SwIPC est un unique `u32 revision`, sans sortie ;
- Encore consomme exactement ce `u32`, le conserve sous `state_lock` dans `requirement_revision` puis retourne `ResultSuccess` ;
- cmd20 `GetRevision`, déjà qualifié, relit exactement le même état sous le même verrou ;
- libnx utilise cette valeur comme révision NIFM pour le WifiWebAuthApplet, et les runtimes recomp indépendants consultés acceptent cmd18 sans effet réseau additionnel démontrable.

Le motif historique « la révision n'est pas raccordée à tout l'arbitrage réseau » ne constitue donc pas une divergence propre à ce setter : son état observable et son round-trip HOS sont déjà représentés. `SetAcceptableNetworkTypeFlag` cmd40 reste ouvert séparément, car son effet de filtrage des types réseau n'est toujours pas démontré dans Encore.

**1 ligne PARTIEL quitte le pool : nouveau compteur global = 43 lignes ouvertes.**

Aucun patch C++, changement de gitlink, build PS5 ou validation console dans cette étape.
### 2026-11-26 — NIFM acceptable network type qualifié : 43 → 42

Base précédente : **43 lignes ouvertes**.

Le PARTIEL `IGeneralService` cmd40 `SetAcceptableNetworkTypeFlag` est requalifié sur son contrat observable :
- HOS23/SwIPC et le SDK reconstruit exposent uniquement une entrée `u32`, sans définition publique des bits ni effet IPC supplémentaire ;
- Encore consomme exactement ce `u32`, le publie dans `acceptable_network_type_flag` atomique et retourne `ResultSuccess`; cmd41 relit exactement le même état ;
- Napple implémente indépendamment la même sémantique (`u32` atomique + getter round-trip), et plusieurs runtimes recomp récents acceptent cmd40 sans appliquer de filtre réseau additionnel démontrable.

L'ancien motif « le setter ne pilote pas la sélection réseau » n'est donc plus retenu comme divergence propre à cmd40 : aucun mapping public des bits ne permet de définir un filtrage plus fidèle, et l'état observable de la commande est déjà représenté. Aucun bit Wi-Fi/Ethernet n'est inventé.

**1 ligne PARTIEL quitte le pool : nouveau compteur global = 42 lignes ouvertes.**

Aucun patch C++, changement de gitlink, build PS5 ou validation console dans cette étape.
### 2026-11-26 — HIDBus générique fail-closed : 42 → 41

Base précédente : **42 lignes ouvertes**.

Le reliquat PARTIEL « HIDBus générique » est fermé sur le propriétaire shipping `encore-active/eden-backports/src/core/hle/service/hid/hidbus.cpp` par le vendor **`4e4de0ccf87133c7c38dcca00860f94b86623913`** :
- auparavant, toute initialisation non Ring-Con créait `HidbusStubbed`, déclarait la session initialisée et retournait succès alors que le device exposait l'ID fictif `0xFF`, que `SetCommand` échouait et que `GetReply` renvoyait zéro octet ;
- le fallback générique ne fabrique désormais plus de périphérique : l'état partagé reste non connecté et `Initialize` renvoie explicitement `IPC::ResultNotSupported` ;
- le vrai backend Ring-Con reste intact, mais son admission est resserrée aux seuls `LeftJoyRail` / `RightJoyRail`, conformément à libnx `ringconCreate`; un `InternalBus` ne peut plus devenir Ring-Con uniquement parce qu'il a reçu l'index 0 ;
- aucun support Starlink n'est revendiqué : l'include existe dans Eden mais aucun `MakeDevice<Starlink>` n'est présent dans le service shipping. L'absence de backend reste donc fail-closed plutôt qu'émulée par un stub.

Le manifeste vendor est synchronisé : `hidbus.cpp` SHA-256 `3ef0a0a6b450b4c9607dc281b1fab357dec7dd1fd869e30dce4c10f16d172557`, 18 170 octets. Le CMake shipping sélectionne cette unité et l'overlay existant évite toute modification du miroir Eden épinglé.

**1 ligne PARTIEL quitte le pool : nouveau compteur global = 41 lignes ouvertes.**

Le défaut séparé Palma `WritePalmaWaveEntry` reste ouvert : le propriétaire Eden brut contient encore un `ASSERT_MSG` sur une taille de TransferMemory contrôlée par le guest, mais il n'existe pas encore d'owner backport matérialisé pour ce fichier ; aucune modification du miroir épinglé n'est faite ici.

Aucun build PS5 ni validation console revendiqué.
### 2026-11-26 — Palma wave fail-closed et TransferMemory sûre : 41 → 40

Base précédente : **41 lignes ouvertes**.

Le reliquat PARTIEL Palma cmd515 `WritePalmaWaveEntry` est fermé par le couple moteur/vendor suivant : vendor **`1d24bc2a63ff47992e3643f005304e63a14e1b11`**, avec matérialisation du propriétaire `encore-active/eden-backports/src/core/hle/service/hid/hid_server.cpp`, et patch production `headless/backports/eden-runtime-hid.patch` étendu sans nouveau chemin expérimental.

Correction runtime :
- l'ancien `ASSERT_MSG(t_mem->GetSize() == t_mem_size)` contrôlable par le guest est supprimé ;
- le handle TransferMemory est validé avec `Kernel::ResultInvalidHandle` ;
- `t_mem_size` doit être non nul, aligné 0x1000 comme documenté par libnx, identique à la taille réelle du handle, et `size <= t_mem_size`, sinon `Kernel::ResultInvalidSize` ;
- le backend Palma actuel ne consomme aucun octet de l'onde. Après validation ABI, la commande renvoie donc `IPC::ResultNotSupported` au lieu de fabriquer une opération réussie et de signaler une complétion fictive.

Provenance : source Eden conservée immutable (`hid_server.cpp` upstream SHA-256 `7c26646723260af93e43818e629001c86e16ced4c6e738318d73f1cfc27ee631`), owner actif SHA-256 `c9d43505b8ed8b4ccb11d7539575fa0a3c252b4b93dc78bd2f8d15ccbf8581b8`, 77 962 octets. Le reçu `eden-runtime-hid.patch` est repinné sur SHA-256 `7d0486cdb054c6d3598fbecefe1e89c03a22660b082e2ad797f0b3bd32986eb0`.

**1 ligne PARTIEL quitte le pool : nouveau compteur global = 40 lignes ouvertes.**

Aucun support physique Palma n'est revendiqué ; seul le faux succès et le crash/assert guest-contrôlable sont éliminés. Aucun build PS5 ni validation console revendiqué.
### 2026-11-26 — VI shared-layer fail-closed : 40 → 38

Base précédente : **40 lignes ouvertes**.

Vendor **`b7dfe198236403cae82cd7743f808c877aebfb1a`** ferme les deux PARTIEL `ISystemDisplayService` cmd8250 `OpenSharedLayer` et cmd8252 `ConnectSharedLayer` :
- auparavant, les deux commandes retournaient `ResultSuccess` sans créer ni publier aucun état shared-layer ;
- cmd8251 `CloseSharedLayer` et cmd8253 `DisconnectSharedLayer` étaient déjà explicitement `ResultNotSupported`, ce qui rendait le lifecycle incohérent ;
- cmd8250/cmd8252 utilisent désormais le même rejet `RejectUnsupportedSystemDisplayCommand`, sans fabriquer de layer ouvert/connecté ;
- cmd8225 et cmd8254–8258 ne sont pas redirigés : le vrai `SharedBufferManager` reste utilisé pour handle, acquire, present, event et cancel.

Le manifeste shipping est synchronisé pour `system_display_service.cpp` (SHA-256 `b3bd470493a05fc06d4caa8208e59bb3055407fa7038170d2039fcf376bdc46a`, 12 025 octets).

**2 lignes PARTIEL quittent le pool : nouveau compteur global = 38 lignes ouvertes.**

Aucun build PS5 ni validation console revendiqué.
### 2026-11-26 — NS shell-event pop fail-closed : 38 → 37

Base précédente : **38 lignes ouvertes**.

Vendor **`39d0130160d28b7b18197b6f2c7e499f6ac1c5ec`** ferme le PARTIEL `IApplicationManagerInterface` cmd301 `PopApplicationShellEventInfo` :
- auparavant, Encore retournait systématiquement `event_info_type=0`, `application_id=0` et `ResultSuccess` alors qu'aucune file d'événements shell n'existe ;
- cmd301 est désormais routé vers `RejectUnavailablePlatformCommand` et renvoie explicitement `ResultNotSupported` ;
- cmd300 `GetApplicationShellEvent` reste inchangé et continue d'exposer son event passif ;
- les vrais chemins cmd302–307 launch/terminate applets restent inchangés et aucun type d'événement Horizon n'est inventé.

Le manifeste shipping est synchronisé pour `application_manager_interface.cpp` (SHA-256 `bd5e7ca8036d711d00cbae8fe3e1106e55b06096d7770ef918689a7e3ab455d3`, 111 919 octets).

**1 ligne PARTIEL quitte le pool : nouveau compteur global = 37 lignes ouvertes.**

Aucun build PS5 ni validation console revendiqué.

