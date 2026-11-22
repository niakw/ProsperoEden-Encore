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
