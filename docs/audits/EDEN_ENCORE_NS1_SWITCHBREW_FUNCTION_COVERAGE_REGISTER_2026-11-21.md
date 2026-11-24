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
