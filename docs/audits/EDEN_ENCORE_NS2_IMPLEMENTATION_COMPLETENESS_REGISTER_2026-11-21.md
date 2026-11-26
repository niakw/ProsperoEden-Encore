# Eden Encore — registre de complétude NS2 : SwitchBrew et parité structurelle Lichii (ouvert le 21 novembre 2026)

> **Nature** : registre vivant de couverture **statique et hôte** pour Nintendo Switch 2. Il distingue le catalogue de commandes SwitchBrew (fonction F, dispatch R) et la couverture des tables de Lichii `nx2` (§17) ; ces deux nombres ne s'additionnent pas. Une ligne manquante n’est **pas** automatiquement un bug de Mario Kart World ou Donkey Kong Bananza ; une ligne implémentée n’est **pas** une preuve console.

**Issue maîtresse NS2 : [#123](https://github.com/niakw/ProsperoEden-Encore/issues/123).**
**Référence historique complémentaire : [analyse des écarts NS2 puis NS1 du 20/11](./EDEN_ENCORE_GAP_ANALYSIS_NS2_THEN_NS1_2026-11-20.md).**

## 0. Provenance et règle de mise à jour

| Élément | Révision / source |
| --- | --- |
| **Relevé 23/11 — moteur `main`** | [`1b772815a470008cc3bc80a3f97f65553569c649`](https://github.com/niakw/ProsperoEden-Encore/commit/1b772815a470008cc3bc80a3f97f65553569c649) — version avant cette mise à jour documentaire |
| **Relevé 23/11 — gitlink vendor `main`** | [`ee20b5a00e4fd96c02b5d12d6f4eaabee8623bf3`](https://github.com/niakw/Prospero.Eden-Encore-vendor/commit/ee20b5a00e4fd96c02b5d12d6f4eaabee8623bf3) — sous-module `vendor` mode `160000` vérifié dans l'arbre moteur |
| **Référence Lichii `nx2`** | [`66c555ad9a21b1caaf57a5d9f8f1fea6f90c2508`](https://github.com/zortos293/Lichii/tree/66c555ad9a21b1caaf57a5d9f8f1fea6f90c2508) — `src/core/hle/service/nx2_gsv.h` |
| **Build natif du couple relevé — résultat final** | [45084634419](https://github.com/niakw/ProsperoEden-Encore/actions/runs/45084634419) **ROUGE lors de la compilation native**, sans package : `nup_v1_native_content.cpp:50` (`Loader::ResultStatus` incomplet) et vendor `nifm.cpp:1111` (table `FunctionInfo` mal formée, erreur `RegisterHandlers`) |
| Moteur `main` à la création de ce registre | `a59cae85eb1dd7246f5648b46e6fddceb736a5a6` |
| Vendor gitlink sélectionné après intégration | `224b05e6f8b1a266b0d55d1ded5332f7a2eaed7c` |
| Moteur `main` avant intégration de cette branche | `814bc29918df3c1fc207229537c7d80dfa8c8891` |
| Vendor `main` fusionné + test de qualification | `224b05e6f8b1a266b0d55d1ded5332f7a2eaed7c` |
| Vendor `main` à la création | `546e1aa34d2ff183dd4c737f9da8fbf4a62be24e` |
| SwitchBrew GSV | https://www.switchbrew.org/wiki/Switch_2%3A_GSV_services — consultation 2026-11-21 |
| SwitchBrew NV services | https://www.switchbrew.org/wiki/NV_services — consultation 2026-11-21 |
| Client SDK recroisé | https://github.com/vexcited/fefw — notamment `src/nn/gpu/gpu_sdk_*.cpp` |
| Client libounce Switch 2 recroisé (24/11) | `ouncebrew/libounce` `32e7ac414ee1cd98922f66a059be5a85e99feea5` — `gsv.c`/`gsv.h` : cycle 901→906→close→903 et ABI Worker 211/212/213 |
| Validation console du présent couple | **Aucune** : pas de build PS5, pas de première soumission/frame revendiquée |

**Codes** : **C** = implémentation C++ active et cohérente au niveau source/CI hôte ; **P** = partielle, contrat fusionné ou divergence ABI/nomenclature à revoir ; **M** = fonctionnalité non implémentée, que le dispatcher ait un refus/stub explicite ou aucun handler renseigné ; **U** = ID connu mais nom/ABI/sémantique publique insuffisante ; **V** = variante de version non couverte intentionnellement tant que le firmware invité cible ne la requiert pas.
**Tous les C/P restent console-non-qualifiés** tant qu’un build PS5 représentatif ne les a pas exercés.

**Colonnes séparées pour chaque commande (§1–§12)** : F = comportement de la commande elle-même ; R = dispatch. Les deux lecteurs d'erreur H:0x16/H:0x17 sont C : ils exposent correctement le snapshot courant. **Le manque d'un producteur de faute GPU réel reste un blocage transversal distinct** et ne doit plus maintenir artificiellement les lecteurs en P.

### Politique des fonctions connues mais non implémentées

Une commande connue peut recevoir un **handler nommé** afin que la couverture soit explicite, avec un commentaire du type `// not implemented yet on Encore`, **mais elle ne doit jamais retourner un faux `Success`**. Tant que son effet réel n’est pas implémenté, elle doit répondre `NotImplemented`, `InvalidState` ou une erreur plus précise adaptée au contrat. Les commandes dont même le format d’entrée est inconnu restent sans lecture de payload plutôt que de deviner une ABI.

**Mise à jour fail-closed NVHOST (21/11)** : le vendor `f65ccc43` conserve l’ouverture des nodes `/dev/nvhost-*` inconnus nécessaire à la découverte NVN, mais leur fallback générique ne fabrique plus de sortie zéro/copiée ni de `Success`. Toute ioctl non couverte retourne désormais explicitement `NotImplemented` avec le marqueur `// not implemented yet on Encore`. Les handlers TSG authentifiés `BIND_CHANNEL`, `UNBIND_CHANNEL` et `BIND_CHANNEL_EX` restent actifs. **Aucune qualification PS5 n’est revendiquée.**

### Double compteur SwitchBrew : fonctions et dispatch (recalcul 23/11/2026)

> Périmètre **316 commandes NS2**. Couverture source ≠ build PS5 ≠ validation console.

- **F** : **C=176**, **P=3**, M=107, U=24, V=6. Seule requalification F : **VI2 53, U → C-source** ; le tick est produit après libération du buffer, mais l'ABI et le résultat console restent à qualifier.
- **R** : **316/316** disposent d'un dispatch explicite ou d'un refus/stub identifié.

| Statut fonctionnel | Total | Traitement indiqué | Sans traitement |
| --- | ---: | ---: | ---: |
| C — implémentation source | **176** | 176 | 0 |
| P — partielle | **3** | 3 | 0 |
| M — non implémenté | 107 | 107 | 0 |
| U — contrat insuffisant | 24 | 24 | 0 |
| V — ancienne variante firmware | 6 | 6 | 0 |
| **Total** | **316** | **316** | **0** |

**Lecteurs d'erreur qualifiés C** : H:0x16 copie la structure 128 B du snapshot courant ; H:0x17 copie la structure 16 B et force le status Switch `0xFFFF`. Les deux vérifient ABI native, owner et initialisation du notifier. **Ouvert séparément** : aucun producteur GPU ne remplit encore ces snapshots ni ne signale l'événement en cas de faute matérielle/émulée réelle.

**Restent 3 P** : CHANNEL_SETUP_BIND userspace USERD/doorbell, SET_RUNLIST_INTERLEAVE post-bind et SET_TIMESLICE post-bind.

**Compteur Lichii indépendant (§17)** : les IDs additionnels de Lichii, notamment GSV 1121 et les neuf stubs GPU opaques, ne gonflent pas les 316 commandes SwitchBrew.

**Statut de clôture de la branche** : le chantier demandé « traiter toute entrée non-C » est **terminé au sens dispatch/runtime borné** : aucune des 316 entrées n'est sans comportement explicite. Les trois P ne sont pas des oublis : leur chemin supporté fonctionne, et leur sous-mode non supporté retourne explicitement `NotImplemented` plutôt qu'un faux succès. Ils ne peuvent passer C complet sans ajouter respectivement (1) USERD + doorbell + mappings utilisateurs réels, (2) rechargement/preemption de runlist après bind pour interleave, (3) application de timeslice au scheduler après bind. Ces trois capacités ne sont pas simulées.

---

## 1. UserSession GSV — liste SwitchBrew complète

État courant de la table (24/11, `main`) : 142 commandes recensées ; C=56, P=0, M=69, U=17. État initial historique du 21/11 : C=27, P=26, M=72, U=17. Les divergences de nom sont volontairement visibles : elles signalent les endroits où la simple présence d’un handler ne suffit pas.

| Cmd | Interface | Nom SwitchBrew | Statut fonctionnel (F) | Traitement déclaré (R) | Handler Encore actif | Écart / raison |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Gsv | BootWithTransferMemory | C | HANDLER INDIQUÉ | InitializeWithTransferMemory | handler actif; boot transfert réel, console non qualifiée |
| 4 | Gsv | BootWithRemoteMemory | C | HANDLER INDIQUÉ | Initialize | handler actif; remote-memory |
| 11 |  | SetCurrentProcessHandle | C | HANDLER INDIQUÉ | BindProcess | processus natif authentifié |
| 12 |  | (nom inconnu SwitchBrew) | U | REFUS GÉNÉRIQUE EXPLICITE | IGraphicsSupervisor::HandleSyncRequest fallback | ID connu, ABI/sémantique insuffisamment documentées ; ID absent de la table spécifique, fallback TIPC actif → ResultNotImplemented sans décoder de payload inconnu |
| 101 |  | CreateContext | C | HANDLER INDIQUÉ | CompleteBootstrap | Contrat prouvé : TIPC 0x75 sans données, transition de bootstrap vers Ready ; simple différence de nom C++ (graphics_supervisor_bootstrap.h) |
| 111 | NativeMemory | CreateNativeMemory | C | HANDLER INDIQUÉ | CreateNativeMemory | actif |
| 112 | NativeMemory | DestroyNativeMemory | C | HANDLER INDIQUÉ | DestroyNativeMemory | actif |
| 113 | NativeMemory | CreateNativeMemoryBlockByTransferMemory | C | HANDLER INDIQUÉ | CreateNativeMemoryWithTransferMemory | actif |
| 114 | NativeMemory | CreateNativeMemoryBlock | C | HANDLER INDIQUÉ | BindNativeMemory | actif; nom Encore différent |
| 115 | NativeMemory | BootNativeMemoryManagement | C | HANDLER INDIQUÉ | BootNativeMemoryManagement | actif |
| 187 | NativeMemory | QueryNativeMemoryNvsNvRmMemIdForDebug | M | STUB NOMMÉ | UnavailableDocumentedFeature | aucun handler sélectionné; debug, non P0 ; handler TIPC explicite, NotImplemented sans objet ni handle (non fonctionnel) |
| 201 | Syncpt | CreateSyncptContext | C | HANDLER INDIQUÉ | CreateSyncptContext | actif |
| 202 | Syncpt | InitializeSyncptContext | C | HANDLER INDIQUÉ | OpenSyncptSession | Contrat prouvé : TIPC 202 sans entrée, validation de longueur avant allocation et retour d'une vraie session MOVE kernel ; pas seulement un alias |
| 211 | Syncpt | CreateDebugSyncDevice | M | STUB NOMMÉ | UnavailableDocumentedFeature | aucun handler ; handler TIPC explicite, NotImplemented sans objet ni handle (non fonctionnel) |
| 212 | Syncpt | DestroyDebugSyncDevice | M | STUB NOMMÉ | UnavailableDocumentedFeature | aucun handler ; handler TIPC explicite, NotImplemented sans objet ni handle (non fonctionnel) |
| 213 | Syncpt | CreateDebugSyncCounter | M | STUB NOMMÉ | UnavailableDocumentedFeature | aucun handler ; handler TIPC explicite, NotImplemented sans objet ni handle (non fonctionnel) |
| 214 | Syncpt | DestroyDebugSyncCounter | M | STUB NOMMÉ | UnavailableDocumentedFeature | aucun handler ; handler TIPC explicite, NotImplemented sans objet ni handle (non fonctionnel) |
| 215 | Syncpt | ReportDebugSyncCounterValue | M | STUB NOMMÉ | UnavailableDocumentedFeature | aucun handler ; handler TIPC explicite, NotImplemented sans objet ni handle (non fonctionnel) |
| 301 | Display | CreateDisplayContext | C | HANDLER INDIQUÉ | InitializeDisplayContext | Contrat prouvé : CreateDisplayContext sans entrée, état display_ready géré après bootstrap Ready ; nom interne différent seulement |
| 303 | Display | DestroyDisplayContext | C | HANDLER INDIQUÉ | FinalizeDisplayContext | actif |
| 305 | Display | InitializeDisplayContext | C | HANDLER INDIQUÉ | OpenDisplaySession | Contrat prouvé : u64 version contrôlée (19.0 + SDK ultérieurs), vraie IVi2Session et handle MOVE ; pas un stub |
| 311 | Display | (nom inconnu) | U | STUB NOMMÉ | IGraphicsSupervisor::UnavailableDocumentedFeature | ID Lichii « CreateFeatureImagePool311 » enregistré ; contrat fonctionnel non qualifié (U), réponse NotImplemented sans faux succès. |
| 312 | Display | (nom inconnu) | U | STUB NOMMÉ | IGraphicsSupervisor::UnavailableDocumentedFeature | ID Lichii « DestroyFeatureImagePool312 » enregistré ; contrat fonctionnel non qualifié (U), réponse NotImplemented sans faux succès. |
| 314 | Display | (nom inconnu) | C | HANDLER INDIQUÉ | ConfigureNativeWindowImagePool | Lichii : 314(first image) ; Encore retire exactement le groupe enregistré par 315, sans inférer la longueur depuis des IDs adjacents |
| 315 | Display | (nom inconnu) | C | HANDLER INDIQUÉ | ConfigureNativeWindowImagePool | Lichii : 315(first image,count) ; Encore mémorise le groupe exact, valide tous les IDs avant publication et marque chaque image alias |
| 321 | Display | (nom inconnu) | U | STUB NOMMÉ | IGraphicsSupervisor::UnavailableDocumentedFeature | ID Lichii « CreateFeatureImagePool321 » enregistré ; contrat fonctionnel non qualifié (U), réponse NotImplemented sans faux succès. |
| 327 | Display | (nom inconnu) | U | REFUS GÉNÉRIQUE EXPLICITE | IGraphicsSupervisor::HandleSyncRequest fallback | pas de handler / contrat insuffisant ; ID absent de la table spécifique, fallback TIPC actif → ResultNotImplemented sans décoder de payload inconnu |
| 361 | Display | (nom inconnu) | U | STUB NOMMÉ | IGraphicsSupervisor::UnavailableDocumentedFeature | ID Lichii « GetFeatureCpuImageDescriptor361 » enregistré ; contrat fonctionnel non qualifié (U), réponse NotImplemented sans faux succès. |
| 391 | Display | CalculateRequiredBufferMemory | C | HANDLER INDIQUÉ | CalculateFeatureImagePoolRequirements | Lichii common feature-image template: preference[16]+count → u64 size/alignment; formats 1/4/5 + observed MKW 0x38, no image creation side effect |
| 401 | Gpu | CreateGpuContext | C | HANDLER INDIQUÉ | InitializeGpuContext | actif; création état GPU |
| 402 | Gpu | InitializeGpuContext | C | HANDLER INDIQUÉ | ActivateGpuContext | actif |
| 403 | Gpu | DestroyGpuContext | C | HANDLER INDIQUÉ | DestroyGpuContext | actif |
| 423 | Gpu | (nom public incomplet) | C | HANDLER INDIQUÉ | BindNativeGpuMemory | Ounce/fefw envoie raw `0x1B7` (TIPC 423) pour le bind enfant NativeMemory → parent GPU/NVMap; ownership, adresse, taille et offset sont validés |
| 424 | Gpu | (nom inconnu) | U | STUB NOMMÉ | IGraphicsSupervisor::UnavailableDocumentedFeature | ID Lichii « Unknown424 » enregistré ; contrat fonctionnel non qualifié (U), réponse NotImplemented sans faux succès. |
| 425 | Gpu | (nom inconnu) | U | STUB NOMMÉ | IGraphicsSupervisor::UnavailableDocumentedFeature | ID Lichii « Unknown425 » enregistré ; contrat fonctionnel non qualifié (U), réponse NotImplemented sans faux succès. |
| 426 | Gpu | MapNativeImage | C | HANDLER INDIQUÉ | MapNativeGpuImage | actif |
| 427 | Gpu | UnmapNativeImage | C | HANDLER INDIQUÉ | UnmapNativeGpuImage | actif |
| 428 | Gpu | QueryNativeImage | C | HANDLER INDIQUÉ | QueryNativeGpuImage | actif |
| 429 | Gpu | CreateNativeImage | C | HANDLER INDIQUÉ | CreateNativeImage | actif |
| 430 | Gpu | DestroyNativeImage | C | HANDLER INDIQUÉ | DestroyNativeImage | actif |
| 434 | Gpu | ExistsAddressSpace (nom public) | C | HANDLER INDIQUÉ | RegisterGpuAddressSpace | Ounce/fefw envoie raw `0x1C2` avec un seul AS fd et attend un résultat; Encore enregistre exactement l'AS possédé par le process |
| 435 | Gpu | CalculateNativeImageSize | C | HANDLER INDIQUÉ | CalculateNativeImageSize | actif |
| 437 | Gpu | CreateNativeMemoryWithGpukMemHandle | U | REFUS GÉNÉRIQUE EXPLICITE | IGraphicsSupervisor::HandleSyncRequest fallback | nom/ID public connu, mais l'implémentation Ounce observée utilise raw `0x1B7` → TIPC 423; aucun contrat raw `0x1C5` prouvé, donc pas de doublon inventé ; ID absent de la table spécifique, fallback TIPC actif → ResultNotImplemented sans décoder de payload inconnu |
| 493 | Gpu | CreateUserlandDebuggerSession | M | STUB NOMMÉ | UnavailableDocumentedFeature | pas de handler; debug non P0 ; handler TIPC explicite, NotImplemented sans objet ni handle (non fonctionnel) |
| 494 | Gpu | (nom inconnu) | U | STUB NOMMÉ | IGraphicsSupervisor::UnavailableDocumentedFeature | ID Lichii « CheckPermission494 » enregistré ; contrat fonctionnel non qualifié (U), réponse NotImplemented sans faux succès. |
| 496 | Gpu | CreateGpuSessionWithTransferMemory | C | HANDLER INDIQUÉ | OpenGpuSessionWithTransferMemory | session GPU réelle |
| 497 | Gpu | CreateGpuSessionWithRemoteMemory | C | HANDLER INDIQUÉ | OpenGpuSession | session GPU réelle |
| 498 | Gpu | TryQueryDonatedTransferMemoryUsage | C | HANDLER INDIQUÉ | QueryDonatedTransferMemoryUsage | ABI Ounce exacte: aucune entrée, trois u64 total/used/peak; le cmd 1 conserve le vrai KTransferMemory donné, remote-memory échoue fermé |

**Réconciliation Ounce 21/11** : le SDK reconstruit par fefw appelle `CreateNativeMemoryWithGpukMemHandle` via `Invoke(0x1B7)`, soit TIPC **423** après retrait de `0x10`, et appelle l'enregistrement d'address-space via raw `0x1C2`, soit **434**. Pour **498**, il appelle raw `0x202` sans entrée et lit trois `u64`. Ces observations priment pour le runtime actif sur une simple attribution de nom non documentée; elles ne constituent pas une validation console PS5.
| 601 | Camera | CreateCameraContext | C | HANDLER INDIQUÉ | InitializeFeatureContext | SDK/Lichii : 601() admission caméra, aucun payload/objet retour ; validation TIPC exacte et succès sans état fictif |
| 602 | Camera | InitializeCameraContext | C | HANDLER INDIQUÉ | OpenCameraSession | SDK/Lichii : 602(u64 version=1), vraie CameraSession MOVE ; forme IPC, ownership et rollback OOM vérifiés |
| 603 | Camera | DestroyCameraContext | M | STUB NOMMÉ | UnavailableDocumentedFeature | pas de handler ; handler TIPC explicite, NotImplemented sans objet ni handle (non fonctionnel) |
| 612 | Camera | DestroyOutputBufferPool | M | STUB NOMMÉ | UnavailableDocumentedFeature | pas de handler ; handler TIPC explicite, NotImplemented sans objet ni handle (non fonctionnel) |
| 613 | Camera | CreateAliasOutputBufferPool | M | STUB NOMMÉ | UnavailableDocumentedFeature | pas de handler ; handler TIPC explicite, NotImplemented sans objet ni handle (non fonctionnel) |
| 614 | Camera | DestroyAliasOutputBufferPool | M | STUB NOMMÉ | UnavailableDocumentedFeature | pas de handler ; handler TIPC explicite, NotImplemented sans objet ni handle (non fonctionnel) |
| 615 | Camera | CreateOutputBufferPool | M | STUB NOMMÉ | UnavailableDocumentedFeature | pas de handler ; handler TIPC explicite, NotImplemented sans objet ni handle (non fonctionnel) |
| 616 | Camera | ReadFrameDataAsync | M | STUB NOMMÉ | UnavailableDocumentedFeature | pas de handler UserSession ; handler TIPC explicite, NotImplemented sans objet ni handle (non fonctionnel) |
| 620 | Camera | InitializeB | M | STUB NOMMÉ | UnavailableDocumentedFeature | pas de handler ; handler TIPC explicite, NotImplemented sans objet ni handle (non fonctionnel) |
| 621 | Camera | FinalizeB | M | STUB NOMMÉ | UnavailableDocumentedFeature | pas de handler ; handler TIPC explicite, NotImplemented sans objet ni handle (non fonctionnel) |
| 622 | Camera | ListCameras | M | STUB NOMMÉ | UnavailableDocumentedFeature | pas de handler ; handler TIPC explicite, NotImplemented sans objet ni handle (non fonctionnel) |
| 623 | Camera | OpenCamera | M | STUB NOMMÉ | UnavailableDocumentedFeature | pas de handler UserSession; sous-session caméra possède un OpenCamera séparé ; handler TIPC explicite, NotImplemented sans objet ni handle (non fonctionnel) |
| 624 | Camera | CloseCamera | M | STUB NOMMÉ | UnavailableDocumentedFeature | pas de handler ; handler TIPC explicite, NotImplemented sans objet ni handle (non fonctionnel) |
| 626 | Camera | ListSensorMode | M | STUB NOMMÉ | UnavailableDocumentedFeature | pas de handler ; handler TIPC explicite, NotImplemented sans objet ni handle (non fonctionnel) |
| 627 | Camera | SetSensorMode | M | STUB NOMMÉ | UnavailableDocumentedFeature | pas de handler ; handler TIPC explicite, NotImplemented sans objet ni handle (non fonctionnel) |
| 628 | Camera | GetAvailableStreams | M | STUB NOMMÉ | UnavailableDocumentedFeature | pas de handler ; handler TIPC explicite, NotImplemented sans objet ni handle (non fonctionnel) |
| 629 | Camera | GetRequiredWorkBufferSize | M | STUB NOMMÉ | UnavailableDocumentedFeature | pas de handler ; handler TIPC explicite, NotImplemented sans objet ni handle (non fonctionnel) |
| 630 | Camera | CreateStream | M | STUB NOMMÉ | UnavailableDocumentedFeature | pas de handler ; handler TIPC explicite, NotImplemented sans objet ni handle (non fonctionnel) |
| 632 | Camera | GetReadDoneEvent | M | STUB NOMMÉ | UnavailableDocumentedFeature | pas de handler ; handler TIPC explicite, NotImplemented sans objet ni handle (non fonctionnel) |
| 633 | Camera | GetStreamOutputSize | M | STUB NOMMÉ | UnavailableDocumentedFeature | pas de handler ; handler TIPC explicite, NotImplemented sans objet ni handle (non fonctionnel) |
| 634 | Camera | DestroyStream | M | STUB NOMMÉ | UnavailableDocumentedFeature | pas de handler ; handler TIPC explicite, NotImplemented sans objet ni handle (non fonctionnel) |
| 636 | Camera | ReadFrameDataAsync | M | STUB NOMMÉ | UnavailableDocumentedFeature | pas de handler ; handler TIPC explicite, NotImplemented sans objet ni handle (non fonctionnel) |
| 637 | Camera | GetAttachedEvent | M | STUB NOMMÉ | UnavailableDocumentedFeature | pas de handler ; handler TIPC explicite, NotImplemented sans objet ni handle (non fonctionnel) |
| 638 | Camera | GetDetachedEvent | M | STUB NOMMÉ | UnavailableDocumentedFeature | pas de handler ; handler TIPC explicite, NotImplemented sans objet ni handle (non fonctionnel) |
| 639 | Camera | GetFrameInfo | M | STUB NOMMÉ | UnavailableDocumentedFeature | pas de handler ; handler TIPC explicite, NotImplemented sans objet ni handle (non fonctionnel) |
| 640 | Camera | GetFrameInfo2 | M | STUB NOMMÉ | UnavailableDocumentedFeature | pas de handler ; handler TIPC explicite, NotImplemented sans objet ni handle (non fonctionnel) |
| 641 | Camera | GetConnectionChangedEvent | M | STUB NOMMÉ | UnavailableDocumentedFeature | pas de handler ; handler TIPC explicite, NotImplemented sans objet ni handle (non fonctionnel) |
| 650 | Camera | SetPictureQualityConfig | M | STUB NOMMÉ | UnavailableDocumentedFeature | pas de handler ; handler TIPC explicite, NotImplemented sans objet ni handle (non fonctionnel) |
| 651 | Camera | GetPictureQualityConfig | M | STUB NOMMÉ | UnavailableDocumentedFeature | pas de handler ; handler TIPC explicite, NotImplemented sans objet ni handle (non fonctionnel) |
| 652 | Camera | SetDigitalWindow | M | STUB NOMMÉ | UnavailableDocumentedFeature | pas de handler ; handler TIPC explicite, NotImplemented sans objet ni handle (non fonctionnel) |
| 653 | Camera | GetDigitalWindow | M | STUB NOMMÉ | UnavailableDocumentedFeature | pas de handler ; handler TIPC explicite, NotImplemented sans objet ni handle (non fonctionnel) |
| 654 | Camera | GetDigitalWindowCapability | M | STUB NOMMÉ | UnavailableDocumentedFeature | pas de handler ; handler TIPC explicite, NotImplemented sans objet ni handle (non fonctionnel) |
| 655 | Camera | GetSupportedFunctions | M | STUB NOMMÉ | UnavailableDocumentedFeature | pas de handler ; handler TIPC explicite, NotImplemented sans objet ni handle (non fonctionnel) |
| 656 | Camera | GetSupportedDebugFunctions | M | STUB NOMMÉ | UnavailableDocumentedFeature | pas de handler ; handler TIPC explicite, NotImplemented sans objet ni handle (non fonctionnel) |
| 657 | Camera | GetCameraPrivacyCoverStatus | M | STUB NOMMÉ | UnavailableDocumentedFeature | pas de handler ; handler TIPC explicite, NotImplemented sans objet ni handle (non fonctionnel) |
| 658 | Camera | GetCameraDeviceTemperature | M | STUB NOMMÉ | UnavailableDocumentedFeature | pas de handler ; handler TIPC explicite, NotImplemented sans objet ni handle (non fonctionnel) |
| 659 | Camera | GetDeviceUniqueId | M | STUB NOMMÉ | UnavailableDocumentedFeature | pas de handler ; handler TIPC explicite, NotImplemented sans objet ni handle (non fonctionnel) |
| 660 | Camera | GetSensorMode | M | STUB NOMMÉ | UnavailableDocumentedFeature | pas de handler ; handler TIPC explicite, NotImplemented sans objet ni handle (non fonctionnel) |
| 661 | Camera | GetStride | M | STUB NOMMÉ | UnavailableDocumentedFeature | pas de handler ; handler TIPC explicite, NotImplemented sans objet ni handle (non fonctionnel) |
| 662 | Camera | UnlinkSensor | M | STUB NOMMÉ | UnavailableDocumentedFeature | pas de handler ; handler TIPC explicite, NotImplemented sans objet ni handle (non fonctionnel) |
| 663 | Camera | GetDeviceModel | M | STUB NOMMÉ | UnavailableDocumentedFeature | pas de handler ; handler TIPC explicite, NotImplemented sans objet ni handle (non fonctionnel) |
| 664 | Camera | SetRawSensorMode | M | STUB NOMMÉ | UnavailableDocumentedFeature | pas de handler ; handler TIPC explicite, NotImplemented sans objet ni handle (non fonctionnel) |
| 665 | Camera | GetAccessAllowed | M | STUB NOMMÉ | UnavailableDocumentedFeature | pas de handler ; handler TIPC explicite, NotImplemented sans objet ni handle (non fonctionnel) |
| 666 | Camera | GetHostDrivenAeRegion | M | STUB NOMMÉ | UnavailableDocumentedFeature | pas de handler ; handler TIPC explicite, NotImplemented sans objet ni handle (non fonctionnel) |
| 667 | Camera | SetHostDrivenAeRegion | M | STUB NOMMÉ | UnavailableDocumentedFeature | pas de handler ; handler TIPC explicite, NotImplemented sans objet ni handle (non fonctionnel) |
| 691 | Camera | CalculateImageArraySize | C | HANDLER INDIQUÉ | CalculateFeatureImagePoolRequirements | Lichii common feature-image template; generic block geometry + format Bpp, includes observed MKW 0x38 and fails closed on unknown formats |
| 901 | VideoDecoder | CreateVideoDecoderContext | C | HANDLER INDIQUÉ | InitializeVideoCodecContext | Lichii SDK : 901 précède 902 et ne retourne pas d'objet ; Encore valide no-input + GPU context/NVDRV avant succès |
| 902 | VideoDecoder | InitializeVideoDecoderContext | C | HANDLER INDIQUÉ | OpenVideoDecoderSession | Lichii SDK : 902 retourne la session decoder MOVE ; Encore valide no-input, crée la vraie IGraphicsVideoDecoderSession et rollback OOM |
| 903 | VideoDecoder | DestroyVideoDecoderContext | C | HANDLER INDIQUÉ | ReleaseVideoDecoderAccess | libounce `32e7ac4` : 906 ouvre un unique creator par root ; le client ferme le MOVE handle puis 903 libère l’état racine. Encore conserve ce lease, refuse la réouverture avant 903 et ne libère qu’après fermeture effective du creator. Vendor `042204fd`, console non qualifiée. |
| 904 | VideoDecoderForSystem | InitializeVideoDecoderContextForSystem | M | STUB NOMMÉ | UnavailableDocumentedFeature | pas de handler ; handler TIPC explicite, NotImplemented sans objet ni handle (non fonctionnel) |
| 905 | VideoDecoder | InitializeVideoDecoderContext2 | C | HANDLER INDIQUÉ | OpenVideoDecoderSession | Lichii SDK : 905(u8) variante Initialize(bool), même session MOVE que 902 ; Encore borne la charge à un octet et conserve le vrai backend decoder |
| 911 | VideoDecoder | InitializeDecoderImagePool | C | HANDLER INDIQUÉ | CreateVideoImagePool | Lichii : preference[16] + u32 count + u32 memory id, retour first image id ; Encore valide 18 mots, backing owner/size, pin et pool réel |
| 912 | VideoDecoder | FinalizeDecoderImagePool | C | HANDLER INDIQUÉ | DestroyVideoImagePool | Lichii : 912(image id) retire un output decoder à la fois ; ledger actif suit les membres vivants et ne libère le backing partagé qu'au dernier |
| 921 | VideoDecoderForSystem | InitializeDecoderAliasImagePool | M | STUB NOMMÉ | UnavailableDocumentedFeature | pas de handler ; handler TIPC explicite, NotImplemented sans objet ni handle (non fonctionnel) |
| 922 | VideoDecoderForSystem | FinalizeDecoderAliasImagePool | M | STUB NOMMÉ | UnavailableDocumentedFeature | pas de handler ; handler TIPC explicite, NotImplemented sans objet ni handle (non fonctionnel) |
| 961 | VideoDecoder | (nom inconnu) | C | HANDLER INDIQUÉ | GetCpuVideoImageDescriptor | Lichii : CpuUserImageDescriptor 128 B pour image decoder ; Encore valide l'ID possédé et renvoie le descriptor réel du pool |
| 991 | VideoDecoder | (nom inconnu) | C | HANDLER INDIQUÉ | CalculateDecoderImagePoolBuffer | Lichii/SDK : preference[16]+count → u64 size + u64 alignment ; Encore calcule le layout decoder réel et alignment 0x2000 |
| 1001 | VideoEncoder | CreateVideoEncoderContext | M | STUB NOMMÉ | UnavailableVideoEncoder | stub nommé, commentaire not implemented yet on Encore, retourne NotImplemented ; encodeur non fourni |
| 1002 | VideoEncoder | InitializeVideoEncoderContext | M | STUB NOMMÉ | UnavailableVideoEncoder | stub nommé, commentaire not implemented yet on Encore, retourne NotImplemented ; aucune session décodeur créée |
| 1003 | VideoEncoder | DestroyVideoEncoderContext | M | STUB NOMMÉ | UnavailableDocumentedFeature | pas de handler ; handler TIPC explicite, NotImplemented sans objet ni handle (non fonctionnel) |
| 1004 | VideoEncoderForSystem | InitializeVideoEncoderContextForSystem | M | STUB NOMMÉ | UnavailableDocumentedFeature | pas de handler ; handler TIPC explicite, NotImplemented sans objet ni handle (non fonctionnel) |
| 1011 | VideoEncoder | InitializeEncoderImagePool | M | STUB NOMMÉ | UnavailableDocumentedFeature | pas de handler ; handler TIPC explicite, NotImplemented sans objet ni handle (non fonctionnel) |
| 1012 | VideoEncoder | FinalizeEncoderImagePool | M | STUB NOMMÉ | UnavailableDocumentedFeature | pas de handler ; handler TIPC explicite, NotImplemented sans objet ni handle (non fonctionnel) |
| 1021 | VideoEncoderForSystem | InitializeEncoderAliasImagePool | M | STUB NOMMÉ | UnavailableDocumentedFeature | pas de handler ; handler TIPC explicite, NotImplemented sans objet ni handle (non fonctionnel) |
| 1022 | VideoEncoderForSystem | FinalizeEncoderAliasImagePool | M | STUB NOMMÉ | UnavailableDocumentedFeature | pas de handler ; handler TIPC explicite, NotImplemented sans objet ni handle (non fonctionnel) |
| 1061 | VideoEncoder | (nom inconnu) | U | REFUS GÉNÉRIQUE EXPLICITE | IGraphicsSupervisor::HandleSyncRequest fallback | ID connu sans contrat public suffisant ; ID absent de la table spécifique, fallback TIPC actif → ResultNotImplemented sans décoder de payload inconnu |
| 1091 | VideoEncoder | (nom inconnu) | U | STUB NOMMÉ | IGraphicsSupervisor::UnavailableDocumentedFeature | ID Lichii « Unknown1091 » enregistré ; contrat fonctionnel non qualifié (U), réponse NotImplemented sans faux succès. |
| 1101 | GraphicsFrame | CreateGraphicsFrameContext | C | HANDLER INDIQUÉ | CreateGraphicsFrameContext | host qualifié |
| 1102 | GraphicsFrame | InitializeGraphicsFrameContext | C | HANDLER INDIQUÉ | InitializeGraphicsFrameContext | host qualifié |
| 1111 | GraphicsFrame | SetGraphicsFrameLengthMode | C | HANDLER INDIQUÉ | SetGraphicsFrameLengthMode | valeurs bornées, host qualifié |
| 1112 | GraphicsFrame | SetGraphicsFrameRestartMode | C | HANDLER INDIQUÉ | SetGraphicsFrameRestartMode | valeurs bornées, host qualifié |
| 1113 | GraphicsFrame | SetGraphicsFrameGpuTimesliceMode | C | HANDLER INDIQUÉ | SetGraphicsFrameGpuTimesliceMode | valeurs bornées, host qualifié |
| 1201 | Chat | CreateChatContext | C | HANDLER INDIQUÉ | InitializeFeatureContext | Lichii GameChat : 1201 puis 1202 ; 1201 est l'admission sans objet, forme TIPC zéro-input validée |
| 1202 | Chat | InitializeChatContext | C | HANDLER INDIQUÉ | OpenChatSession | Lichii GameChat : 1202 doit retourner une session ; Encore renvoie une vraie INativeChatGsvSession MOVE avec ownership/OOM correct |
| 1203 | Chat | DestroyChatContext | M | STUB NOMMÉ | UnavailableDocumentedFeature | pas de handler ; handler TIPC explicite, NotImplemented sans objet ni handle (non fonctionnel) |
| 1211 | Chat | CreateImagePool | C | HANDLER INDIQUÉ | CreateVideoImagePool | Lichii : même requête que pool image natif avec count ; Encore valide 16 préférences+count+backing, pin réel et réserve count IDs contigus |
| 1212 | Chat | DestroyImagePool | C | HANDLER INDIQUÉ | DestroyVideoImagePool | fefw GameChat DestroyImagePool envoie le handle de base une fois puis détruit séparément la mémoire native ; Encore retire le pool complet et son duplicate/pin |
| 1291 | Chat | CalculateRequiredBufferMemory | C | HANDLER INDIQUÉ | CalculateFeatureImagePoolRequirements | Lichii/SDK common feature-image requirements template; requirements-only size/alignment, actual GameChat pool creation remains separately bounded |
| 1301 | Adraw | CreateAdrawContext | M | STUB NOMMÉ | UnavailableDocumentedFeature | pas de handler ; handler TIPC explicite, NotImplemented sans objet ni handle (non fonctionnel) |
| 1302 | Adraw | InitializeAdrawContext | M | STUB NOMMÉ | UnavailableDocumentedFeature | pas de handler ; handler TIPC explicite, NotImplemented sans objet ni handle (non fonctionnel) |
| 1325 | Adraw | GetAdrawFrameBufferHandle | M | STUB NOMMÉ | UnavailableDocumentedFeature | pas de handler ; handler TIPC explicite, NotImplemented sans objet ni handle (non fonctionnel) |
| 1326 | Adraw | GetAdrawImageHandle | M | STUB NOMMÉ | UnavailableDocumentedFeature | pas de handler ; handler TIPC explicite, NotImplemented sans objet ni handle (non fonctionnel) |
| 1401 | NvDrv | CreateNvDrv2UserSessionWithTransferMemory | C | HANDLER INDIQUÉ | OpenNvsrvSession | DecodeNvDrvTransferSession vérifie COPY handle, taille alignée et mode ; KTransferMemory owner/size vérifiés, vraie session NVDRV MOVE et test hôte exact déjà présent |
| 1402 | NvDrv | CreateNvDrv2UserSessionWithRemoteMemory | C | HANDLER INDIQUÉ | OpenNvsrvSession | Lichii : 1402 retourne une session nvsrv/NVDRV ; Encore crée INvDrv2User réel lié au KProcess et publie un MOVE handle |
| 1411 | NvDrv | GetNvDrv2UserTransferMemoryUsage | M | STUB NOMMÉ | UnavailableDocumentedFeature | NotImplemented : allocation de NVDRV 1401 non mesurée ; les chiffres du bootstrap GSV 498 ne sont pas substituables |
| 1501 | InterModuleImage | CreateInterModuleImageContext | M | STUB NOMMÉ | UnavailableDocumentedFeature | NotImplemented : inter-module image context sans ownership/backing garanti |
| 1502 | InterModuleImage | InitializeInterModuleImageContext | M | STUB NOMMÉ | UnavailableDocumentedFeature | NotImplemented : impossible d'initialiser un contexte image intermodule fictif |
| 1510 | InterModuleImage | (nom inconnu) | C | HANDLER INDIQUÉ | CalculateNativeImageRequirements | Lichii : preference[16]+count → u64 size/alignment ; Encore utilise le helper natif borné et refuse les layouts inconnus |
| 1601 |  | (nom inconnu) | U | STUB NOMMÉ | IGraphicsSupervisor::UnavailableDocumentedFeature | ID Lichii « CheckPermission1601 » enregistré ; contrat fonctionnel non qualifié (U), réponse NotImplemented sans faux succès. |
| 1602 |  | (nom inconnu) | U | STUB NOMMÉ | IGraphicsSupervisor::UnavailableDocumentedFeature | ID Lichii « Unknown1602 » enregistré ; contrat fonctionnel non qualifié (U), réponse NotImplemented sans faux succès. |
| 1603 |  | (nom inconnu) | U | STUB NOMMÉ | IGraphicsSupervisor::UnavailableDocumentedFeature | ID Lichii « Unknown1603 » enregistré ; contrat fonctionnel non qualifié (U), réponse NotImplemented sans faux succès. |
| 1611 |  | (nom inconnu) | U | STUB NOMMÉ | IGraphicsSupervisor::UnavailableDocumentedFeature | ID Lichii « CreateFeatureImagePool1611 » enregistré ; contrat fonctionnel non qualifié (U), réponse NotImplemented sans faux succès. |
| 1612 |  | (nom inconnu) | U | STUB NOMMÉ | IGraphicsSupervisor::UnavailableDocumentedFeature | ID Lichii « DestroyFeatureImagePool1612 » enregistré ; contrat fonctionnel non qualifié (U), réponse NotImplemented sans faux succès. |
| 1691 |  | (nom inconnu) | C | HANDLER INDIQUÉ | CalculateFeatureImagePoolRequirements | Lichii identifies 1691 as the same feature-image requirements server template as 391/691/1291; same bounded requirements-only handler |


## 2. SyncptSession

SwitchBrew ne nomme publiquement que `Ping`; les autres IDs sont conservés comme inconnus au lieu d’inventer leur contrat.

| Cmd | Nom SwitchBrew | Statut fonctionnel (F) | Traitement déclaré (R) | Handler Encore | Écart / raison |
| --- | --- | --- | --- | --- | --- |
| 0 | Ping | C | HANDLER INDIQUÉ | Handshake | ping/handshake réel |
| 1 | (nom inconnu) | C | HANDLER INDIQUÉ | GetCount | ID couvert; sémantique publique incomplète |
| 21 | (nom inconnu) | U | STUB NOMMÉ | Unknown21 | SwitchBrew publie l'ID mais aucun nom/ABI ; refus ResultNotImplemented sans lecture de payload ni faux retour zéro |
| 22 | (nom inconnu) | C | HANDLER INDIQUÉ | GetSlotEvent | événement réel |
| 103 | (nom inconnu) | C | HANDLER INDIQUÉ | QueryCounter | compteur réel |
| 201 | (nom inconnu) | C | HANDLER INDIQUÉ | RequestSlotEvent | événement réel |
| 202 | (nom inconnu) | C | HANDLER INDIQUÉ | CancelSlotEvent | événement réel |


## 3. DisplaySession

| Cmd | Nom SwitchBrew | Statut fonctionnel (F) | Traitement déclaré (R) | Handler Encore | Écart / raison |
| --- | --- | --- | --- | --- | --- |
| 1 | (SwitchBrew non nommé) | C | HANDLER INDIQUÉ | GetNotificationLimit | handler sélectionné; console non qualifiée |
| 3 | (SwitchBrew non nommé) | C | HANDLER INDIQUÉ | GetSessionLimit | handler sélectionné; console non qualifiée |
| 5 | (SwitchBrew non nommé) | C | HANDLER INDIQUÉ | GetRequestGroupLimit | handler sélectionné; console non qualifiée |
| 11 | (SwitchBrew non nommé) | C | HANDLER INDIQUÉ | GetNotificationEvent | handler sélectionné; console non qualifiée |
| 13 | (SwitchBrew non nommé) | U | STUB NOMMÉ | IVi2Session::Unsupported | Commande Lichii nommée dans la table VI2 sélectionnée ; ABI/effet non qualifié (U), réponse NotImplemented. |
| 21 | (SwitchBrew non nommé) | C | HANDLER INDIQUÉ | GetNotifications | handler sélectionné; console non qualifiée |
| 31 | (SwitchBrew non nommé) | C | HANDLER INDIQUÉ | GetVsyncEvent | handler sélectionné; console non qualifiée |
| 32 | (SwitchBrew non nommé) | C | HANDLER INDIQUÉ | GetDisplayVsyncEvent | handler sélectionné; console non qualifiée |
| 51 | (SwitchBrew non nommé) | C | HANDLER INDIQUÉ | ConfigureRequestGroups | handler sélectionné; console non qualifiée |
| 53 | GetRecordedTimestamps (nom Lichii) | C | HANDLER INDIQUÉ | IVi2Session::GetRecordedTimestamps | TIPC 53 : recorder/checkpoints/maximum, B-buffer borné ; tick après libération du buffer côté compositeur, ABI exacte et PS5 non qualifiées |
| 101 | (SwitchBrew non nommé) | C | HANDLER INDIQUÉ | OpenDisplay | handler sélectionné; console non qualifiée |
| 102 | (SwitchBrew non nommé) | C | HANDLER INDIQUÉ | CloseDisplay | handler sélectionné; console non qualifiée |
| 103 | (SwitchBrew non nommé) | C | HANDLER INDIQUÉ | QueryDisplayRefreshRate | handler sélectionné; console non qualifiée |
| 104 | (SwitchBrew non nommé) | C | HANDLER INDIQUÉ | QueryDisplayHdrStatus | handler sélectionné; console non qualifiée |
| 105 | (SwitchBrew non nommé) | C | HANDLER INDIQUÉ | QueryDisplayHdrPaperWhite | handler sélectionné; console non qualifiée |
| 106 | (SwitchBrew non nommé) | C | HANDLER INDIQUÉ | GetBufferMaxResolution | handler sélectionné; console non qualifiée |
| 107 | (SwitchBrew non nommé) | U | STUB NOMMÉ | IVi2Session::Unsupported | Commande Lichii nommée dans la table VI2 sélectionnée ; ABI/effet non qualifié (U), réponse NotImplemented. |
| 111 | (SwitchBrew non nommé) | C | HANDLER INDIQUÉ | OpenEndpoint | handler sélectionné; console non qualifiée |
| 112 | (SwitchBrew non nommé) | C | HANDLER INDIQUÉ | CloseEndpoint | handler sélectionné; console non qualifiée |
| 113 | (SwitchBrew non nommé) | U | STUB NOMMÉ | IVi2Session::Unsupported | Commande Lichii nommée dans la table VI2 sélectionnée ; ABI/effet non qualifié (U), réponse NotImplemented. |
| 201 | (SwitchBrew non nommé) | C | HANDLER INDIQUÉ | RegisterClientState | handler sélectionné; console non qualifiée |
| 202 | (SwitchBrew non nommé) | C | HANDLER INDIQUÉ | UnregisterClientState | handler sélectionné; console non qualifiée |
| 212 | (SwitchBrew non nommé) | C | HANDLER INDIQUÉ | GetClientAvailability | handler sélectionné; console non qualifiée |
| 228 | (SwitchBrew non nommé) | C | HANDLER INDIQUÉ | CancelClientBuffer | handler sélectionné; console non qualifiée |
| 229 | (SwitchBrew non nommé) | C | HANDLER INDIQUÉ | PresentClientBuffer | handler sélectionné; console non qualifiée |
| 251 | (SwitchBrew non nommé) | C | HANDLER INDIQUÉ | BindClientDisplay | handler sélectionné; console non qualifiée |
| 252 | (SwitchBrew non nommé) | C | HANDLER INDIQUÉ | UnbindClientDisplay | handler sélectionné; console non qualifiée |
| 261 | (SwitchBrew non nommé) | C | HANDLER INDIQUÉ | BindDisplayVsyncEvent | handler sélectionné; console non qualifiée |
| 262 | (SwitchBrew non nommé) | C | HANDLER INDIQUÉ | UnbindDisplayVsyncEvent | handler sélectionné; console non qualifiée |
| 263 | (SwitchBrew non nommé) | C | HANDLER INDIQUÉ | BindDisplayRefreshRateEvent | handler sélectionné; console non qualifiée |
| 264 | (SwitchBrew non nommé) | C | HANDLER INDIQUÉ | UnbindDisplayRefreshRateEvent | handler sélectionné; console non qualifiée |
| 265 | (SwitchBrew non nommé) | C | HANDLER INDIQUÉ | BindDisplayHdrStatusEvent | handler sélectionné; console non qualifiée |
| 266 | (SwitchBrew non nommé) | C | HANDLER INDIQUÉ | UnbindDisplayHdrStatusEvent | handler sélectionné; console non qualifiée |
| 267 | (SwitchBrew non nommé) | C | HANDLER INDIQUÉ | BindDisplayHdrPaperWhiteEvent | handler sélectionné; console non qualifiée |
| 268 | (SwitchBrew non nommé) | C | HANDLER INDIQUÉ | UnbindDisplayHdrPaperWhiteEvent | handler sélectionné; console non qualifiée |
| 269 | (SwitchBrew non nommé) | C | HANDLER INDIQUÉ | BindDisplayBufferMaxResolutionEvent | handler sélectionné; console non qualifiée |
| 270 | (SwitchBrew non nommé) | C | HANDLER INDIQUÉ | UnbindDisplayBufferMaxResolutionEvent | handler sélectionné; console non qualifiée |
| 271 | (SwitchBrew non nommé) | C | HANDLER INDIQUÉ | BindDisplayModeCapabilityEvent | handler sélectionné; console non qualifiée |
| 272 | (SwitchBrew non nommé) | C | HANDLER INDIQUÉ | UnbindDisplayModeCapabilityEvent | handler sélectionné; console non qualifiée |
| 301 | (SwitchBrew non nommé) | U | STUB NOMMÉ | IVi2Session::Unsupported | Commande Lichii nommée dans la table VI2 sélectionnée ; ABI/effet non qualifié (U), réponse NotImplemented. |
| 302 | (SwitchBrew non nommé) | U | STUB NOMMÉ | IVi2Session::Unsupported | Commande Lichii nommée dans la table VI2 sélectionnée ; ABI/effet non qualifié (U), réponse NotImplemented. |
| 351 | (SwitchBrew non nommé) | C | HANDLER INDIQUÉ | SetClientOutputEncoding | handler sélectionné; console non qualifiée |


**DisplaySession — état au 23/11** : la commande `53` est C-source. Les cinq autres IDs `13`, `107`, `113`, `301`, `302` restent F=U, désormais avec stub **nommé** `IVi2Session::Unsupported`. Dix autres stubs opaques Lichii sont aussi nommés dans Encore : `108`, `230`–`232`, `353`–`356`, `358`, `359` ; voir §17.

## 4. VideoDecoderCreatorSession / VideoDecoderSession

Le runtime sélectionne `encore-active/ns2-runtime/video_decoder/.../graphics_video_decoder_session.cpp`. La couverture des IDs documentés est forte, mais la console reste non qualifiée.

| Cmd | Nom SwitchBrew | Statut fonctionnel (F) | Traitement déclaré (R) | Handler Encore | Écart / raison |
| --- | --- | --- | --- | --- | --- |
| 1 | CreateVideoDecoderSession | C | HANDLER INDIQUÉ | CreateDecoderService | creator/service actif |
| 3 | GetInputEvent | C | HANDLER INDIQUÉ | GetInputReadyEvent | event réel |
| 6 | Start | C | HANDLER INDIQUÉ | Start | actif |
| 8 | Flush | C | HANDLER INDIQUÉ | Stop/Flush | actif |
| 101 | Configure | C | HANDLER INDIQUÉ | Configure | actif |
| 109 | Decode | C | HANDLER INDIQUÉ | SubmitInput | FFmpeg/session réelle |
| 115 | FinalizeVideoDecoder | C | HANDLER INDIQUÉ | Finalize | actif |
| 200 | InitializeVideoDecoderWithTransferMemory | C | HANDLER INDIQUÉ | Initialize | actif |
| 207 | Stop | C | HANDLER INDIQUÉ | Stop | actif |
| 210 | InitializeVideoDecoderWithRemoteMemory | M | STUB NOMMÉ | RejectRemoteMemoryInitialization | handler TIPC 210 refuse le remote-memory decoder par NotImplemented sans initialisation fictive |
| 212 | UnbindFrame | C | HANDLER INDIQUÉ | UnregisterOutputImage | actif |
| 213 | GetFrame | C | HANDLER INDIQUÉ | GetOutputInfo | actif |
| 311 | BindFrame | C | HANDLER INDIQUÉ | RegisterOutputImage | actif |
| 314 | DestroyFrame | C | HANDLER INDIQUÉ | ReleaseOutputImage | actif |
| 400 | Decode2 | C | HANDLER INDIQUÉ | SubmitInputWithInfo | actif |


**Écart clair** : la commande `210 InitializeVideoDecoderWithRemoteMemory` n’a pas de handler correspondant dans la session active.

## 5. VideoEncoderCreatorSession / VideoEncoderSession

Aucune session encodeur NS2 équivalente n’est actuellement sélectionnée. Les IDs **UserSession 1001/1002** étaient dirigés vers le décodeur. Le vendor `1e513ae0` les sépare : handler minimal `UnavailableVideoEncoder`, résultat `NotImplemented`, aucune session décodeur créée. **M** reste la classification fonctionnelle (encodeur non fourni, hors P0).

| Cmd | Nom SwitchBrew | Statut fonctionnel (F) | Traitement déclaré (R) | Handler Encore | Écart / raison |
| --- | --- | --- | --- | --- | --- |
| 1 | CreateVideoEncoderSession | M | REFUS PARENT EXPLICITE | UnavailableVideoEncoder (GSV 1001/1002) | service encodeur non créé : le parent GSV refuse NotImplemented, donc cette commande de session est volontairement inatteignable sans faux handle |
| 4 | GetOutputEvent | M | REFUS PARENT EXPLICITE | UnavailableVideoEncoder (GSV 1001/1002) | service encodeur non créé : le parent GSV refuse NotImplemented, donc cette commande de session est volontairement inatteignable sans faux handle |
| 5 | Start | M | REFUS PARENT EXPLICITE | UnavailableVideoEncoder (GSV 1001/1002) | service encodeur non créé : le parent GSV refuse NotImplemented, donc cette commande de session est volontairement inatteignable sans faux handle |
| 100 | InitializeVideoEncoder | M | REFUS PARENT EXPLICITE | UnavailableVideoEncoder (GSV 1001/1002) | service encodeur non créé : le parent GSV refuse NotImplemented, donc cette commande de session est volontairement inatteignable sans faux handle |
| 101 | Configure | M | REFUS PARENT EXPLICITE | UnavailableVideoEncoder (GSV 1001/1002) | service encodeur non créé : le parent GSV refuse NotImplemented, donc cette commande de session est volontairement inatteignable sans faux handle |
| 102 | GetBufferSize | M | REFUS PARENT EXPLICITE | UnavailableVideoEncoder (GSV 1001/1002) | service encodeur non créé : le parent GSV refuse NotImplemented, donc cette commande de session est volontairement inatteignable sans faux handle |
| 108 | Encode | M | REFUS PARENT EXPLICITE | UnavailableVideoEncoder (GSV 1001/1002) | service encodeur non créé : le parent GSV refuse NotImplemented, donc cette commande de session est volontairement inatteignable sans faux handle |
| 110 | GetBuffer | M | REFUS PARENT EXPLICITE | UnavailableVideoEncoder (GSV 1001/1002) | service encodeur non créé : le parent GSV refuse NotImplemented, donc cette commande de session est volontairement inatteignable sans faux handle |
| 111 | SetParameters | M | REFUS PARENT EXPLICITE | UnavailableVideoEncoder (GSV 1001/1002) | service encodeur non créé : le parent GSV refuse NotImplemented, donc cette commande de session est volontairement inatteignable sans faux handle |
| 112 | FinalizeVideoEncoder | M | REFUS PARENT EXPLICITE | UnavailableVideoEncoder (GSV 1001/1002) | service encodeur non créé : le parent GSV refuse NotImplemented, donc cette commande de session est volontairement inatteignable sans faux handle |
| 206 | Stop | M | REFUS PARENT EXPLICITE | UnavailableVideoEncoder (GSV 1001/1002) | service encodeur non créé : le parent GSV refuse NotImplemented, donc cette commande de session est volontairement inatteignable sans faux handle |


## 6. GpuSession

| Cmd | Nom SwitchBrew | Statut fonctionnel (F) | Traitement déclaré (R) | Handler Encore | Écart / raison |
| --- | --- | --- | --- | --- | --- |
| 11 | GetEventIdRange | C | HANDLER INDIQUÉ | GetNotificationRange | actif |
| 12 | CreateEvent | C | HANDLER INDIQUÉ | GetNotificationEvent | libounce réel : handle HIPC MOVE ; référence de transfert distincte, event de service conservé |
| 21 | RequestKUserWorkerSession | C | HANDLER INDIQUÉ | RequestWorker | transport worker réel |
| 22 | GetKUserWorkerSession | C | HANDLER INDIQUÉ | AcquireWorker | libounce réel : KClientSession HIPC MOVE ; référence de service conservée |
| 33 | CreateGpuAddressSpace | C | HANDLER INDIQUÉ | CreateAddressSpace | AS réel |
| 41 | CreateGraphicsDevice | C | HANDLER INDIQUÉ | CreateGraphicsDevice | actif |
| 42 | DestroyGraphicsDevice | C | HANDLER INDIQUÉ | DestroyGraphicsDevice | actif |
| 102 | (nom inconnu) | U | REFUS GÉNÉRIQUE EXPLICITE | IGpuSession::HandleSyncRequest fallback | ID SwitchBrew sans contrat public suffisant ; ID absent de la table spécifique, fallback TIPC actif → ResultNotImplemented sans décoder de payload inconnu |
| 200 | SynchronizeGpuAddressSpace | C | HANDLER INDIQUÉ | SynchronizeGpuAddressSpace | ajouté et host qualifié |
| 201 | GetUserPartitionGpuAddress | C | HANDLER INDIQUÉ | GetUserPartition | actif |
| 202 | GetGsvPartitionGpuAddress | C | HANDLER INDIQUÉ | GetGsvPartition | ABI libounce 16 B `{first,last}` ; partition GSV vide = `UINT64_MAX,0` |
| 203 | GetVmUserRanges (libounce/Ounce) | C | HANDLER INDIQUÉ | GetVaRange | 72 B exacts : `count=1` + 4 ranges ; `[0x08000000,0xBFFFFFFFFF]` inclusif puis trois ranges nuls |


**Complétion Lichii hors catalogue SwitchBrew §6 (23/11)** : les neuf stubs opaques `23`, `24`, `25`, `34`, `51`, `8001`–`8004` sont désormais **nommés dans `IGpuSession`** et dispatchés vers `RejectOpaqueNx2Command` (vendor `716e069f`). Leur ABI reste inconnue : réponse `ResultNotImplemented`, contrairement aux réponses zéro de Lichii. Ils ne sont pas ajoutés aux 316 commandes SwitchBrew (détails §17).

**Recoupement client libounce/OunceVK** : cmd 203 est désormais qualifié par un consommateur réel : `gsvGpuGetVmUserRanges` lit `u64 count + GsvGpuVaRange[4]` (72 B), et OunceVK exige un unique range `[0x08000000,0xBFFFFFFFFF]` avant l’import AS.

**24/11 — caractéristiques GPU natives** : OunceVK `6a03fdb1` (`nvkmd_nvgpu_native_runtime.c`, `import_as`) refuse les mots de grandes pages non nuls à 0x28 et 0x34 avant import AS. Le vendor `53d0ad1f9d50b9f1a72cbecacdacdff7fb4e69eb` corrige uniquement la réponse native 0xD0/0xD8 ; géométrie interne AS, mappings 4 KiB et profil NS1 inchangés. Test de paquet adapté ; qualification CI et démarrage des jeux sur PS5 encore nécessaires. Ce contrat client ne démontre pas à lui seul la cause de l'écran noir NVN2.

## 7. KUserWorkerSession / nn::gpuk::impl::kuser

La numérotation SwitchBrew change entre 19.x et 20.0+. Le runtime actuel suit le bloc **20.0+ 209–216**. Le client SDK `vexcited/fefw` confirme notamment les requêtes TIPC brutes `0xE1/0xE2`, dont le framework retire l’enveloppe pour dispatcher **209/210**.

| Cmd | Nom SwitchBrew / version | Statut fonctionnel (F) | Traitement déclaré (R) | Handler Encore | Écart / raison |
| --- | --- | --- | --- | --- | --- |
| 101 | CreateGpuMemory | C | HANDLER INDIQUÉ | CreateGpuAccessibleMemory | mémoire réelle |
| 102 | DestroyGpuMemory | C | HANDLER INDIQUÉ | DestroyGpuAccessibleMemory | libération + event |
| 171 | EnsureGpuMemoryComptags | C | HANDLER INDIQUÉ | EnsureGpuMemoryComptags | actif |
| 172 | SetGpuMemoryUserDebugLabel | C | HANDLER INDIQUÉ | SetGpuMemoryUserDebugLabel | metadata bornée |
| 173 | SetGpuMemorySdkDebugLabel | C | HANDLER INDIQUÉ | SetGpuMemorySdkDebugLabel | metadata bornée |
| 201 | [19.0.0–19.1.0] NormalMapGpuMemory4K | V | REFUS GÉNÉRIQUE EXPLICITE | IGpuWorker::HandleSyncRequest fallback | ancienne numérotation; non requise pour chemin 20.0+ tant que firmware invité cible confirmé ; ID 19.x non enregistré dans la table 20+, fallback TIPC actif → ResultNotImplemented sans décoder le layout ancien |
| 202 | [19.0.0–19.1.0] NormalUnmapGpuMemory4K | V | REFUS GÉNÉRIQUE EXPLICITE | IGpuWorker::HandleSyncRequest fallback | ancienne numérotation ; ID 19.x non enregistré dans la table 20+, fallback TIPC actif → ResultNotImplemented sans décoder le layout ancien |
| 203 | [19.0.0–19.1.0] CreateSparseRegion | V | REFUS GÉNÉRIQUE EXPLICITE | IGpuWorker::HandleSyncRequest fallback | ancienne numérotation ; ID 19.x non enregistré dans la table 20+, fallback TIPC actif → ResultNotImplemented sans décoder le layout ancien |
| 204 | [19.0.0–19.1.0] DestroySparseRegion | V | REFUS GÉNÉRIQUE EXPLICITE | IGpuWorker::HandleSyncRequest fallback | ancienne numérotation ; ID 19.x non enregistré dans la table 20+, fallback TIPC actif → ResultNotImplemented sans décoder le layout ancien |
| 205 | [19.0.0–19.1.0] ExecuteSparseMapRequests | V | REFUS GÉNÉRIQUE EXPLICITE | IGpuWorker::HandleSyncRequest fallback | ancienne numérotation ; ID 19.x non enregistré dans la table 20+, fallback TIPC actif → ResultNotImplemented sans décoder le layout ancien |
| 207 | [19.0.0–19.1.0] NormalModifyMemoryKind4K | V | REFUS GÉNÉRIQUE EXPLICITE | IGpuWorker::HandleSyncRequest fallback | ancienne numérotation ; ID 19.x non enregistré dans la table 20+, fallback TIPC actif → ResultNotImplemented sans décoder le layout ancien |
| 209 | [20.0.0+] SetGpuSegmentUserDebugLabel | C | HANDLER INDIQUÉ | SetGpuSegmentUserDebugLabel | actif; ID corrigé après vérification enveloppe TIPC |
| 210 | [20.0.0+] SetGpuSegmentSdkDebugLabel | C | HANDLER INDIQUÉ | SetGpuSegmentSdkDebugLabel | actif |
| 211 | [20.0.0+] NormalMapGpuMemory4K | C | HANDLER INDIQUÉ | NormalMapGpuMemory4K | GMMU réel |
| 212 | [20.0.0+] NormalModifyMemoryKind4K | C | HANDLER INDIQUÉ | NormalModifyGpuMemory4K | actif |
| 213 | [20.0.0+] NormalUnmapGpuMemory4K | C | HANDLER INDIQUÉ | NormalUnmapGpuMemory4K | libounce/Lichii : notification par slot et réponse TIPC `Result` seule ; le `u64` de taille synthétique a été retiré dans vendor `042204fd` |
| 214 | [20.0.0+] CreateSparseRegion | C | HANDLER INDIQUÉ | CreateSparseRegion | sparse réel |
| 215 | [20.0.0+] DestroySparseRegion | C | HANDLER INDIQUÉ | DestroySparseRegion | actif |
| 216 | [20.0.0+] ExecuteSparseMapRequests | C | HANDLER INDIQUÉ | ExecuteSparseMapRequests | actif |


## 8. NVDRV — /dev/nvhost-as-gpu

| Ioctl | Nom SwitchBrew | Statut fonctionnel (F) | Traitement déclaré (R) | Handler Encore | Écart / raison |
| --- | --- | --- | --- | --- | --- |
| 0x40044101 | NVGPU_AS_IOCTL_BIND_CHANNEL | C | HANDLER INDIQUÉ | BindChannel | actif |
| 0xC0184102 | NVGPU_AS_IOCTL_ALLOC_SPACE | C | HANDLER INDIQUÉ | AllocateSpace | actif |
| 0xC0104103 | NVGPU_AS_IOCTL_FREE_SPACE | C | HANDLER INDIQUÉ | FreeSpace | actif |
| 0xC0184104 | NVGPU_AS_IOCTL_MAP_BUFFER | C | HANDLER INDIQUÉ | MapBuffer | actif |
| 0xC0084105 | NVGPU_AS_IOCTL_UNMAP_BUFFER | C | HANDLER INDIQUÉ | UnmapBuffer | actif |
| 0xC0284106 | NVGPU_AS_IOCTL_MAP_BUFFER_EX | C | HANDLER INDIQUÉ | MapBufferEx | actif |
| 0x40104107 | NVGPU_AS_IOCTL_ALLOC_AS | C | HANDLER INDIQUÉ | AllocateAs | actif |
| 0xC0404108 | NVGPU_AS_IOCTL_GET_VA_REGIONS | C | HANDLER INDIQUÉ | GetVARegions | actif |
| 0x40284109 | NVGPU_AS_IOCTL_ALLOC_AS_EX | C | HANDLER INDIQUÉ | AllocateAsEx | actif |
| 0xC038410A | NVGPU_AS_IOCTL_MAP_BUFFER_EX2 | C | HANDLER INDIQUÉ | MapBufferEx2 | actif |


## 9. NVDRV — /dev/nvhost-ctrl-gpu, points S2

| Ioctl | Nom SwitchBrew | Statut fonctionnel (F) | Traitement déclaré (R) | Handler Encore | Écart / raison |
| --- | --- | --- | --- | --- | --- |
| 0xC0E04705 | [S2] NVGPU_GPU_IOCTL_GET_CHARACTERISTICS | C | HANDLER INDIQUÉ | GetCharacteristics native | layout S2 224 octets pris en charge |
| 0xC0084710 | [S2] NVGPU_GPU_IOCTL_WAIT_FOR_PAUSE | M | REFUS EXPLICITE | nvhost_ctrl_gpu::Ioctl1 (fail-closed) | ioctl S2 exact refuse pause GPU sans frontière matérielle fiable |
| 0x80084712 | NVGPU_GPU_IOCTL_NUM_VSMS | C | HANDLER INDIQUÉ | NUM_VSMS | profil GA10F cohérent |
| 0xC0084713 | [S2] NVGPU_GPU_IOCTL_VSMS_MAPPING | C | HANDLER INDIQUÉ | VSMS_MAPPING | inline mapping GA10F |
| 0xC010471E | [S2] NVGPU_GPU_IOCTL_SET_DETERMINISTIC_OPTS | M | REFUS EXPLICITE | nvhost_ctrl_gpu::Ioctl1 (fail-closed) | ioctl S2 exact refuse options déterministes sans effet scheduler réel |
| 0xC010471F | [S2] NVGPU_GPU_IOCTL_GET_ENGINE_INFO | C | HANDLER INDIQUÉ | GET_ENGINE_INFO | runlists graphics/copy exposés |


Les autres ioctls de contrôle hérités de Switch 1 restent suivis par les audits existants ; ce tableau met en avant les formes S2 ou modifiées S2 directement pertinentes.

## 10. NVDRV — /dev/nvhost-gpu / channel

| Ioctl | Nom SwitchBrew | Statut fonctionnel (F) | Traitement déclaré (R) | Handler Encore | Écart / raison |
| --- | --- | --- | --- | --- | --- |
| 0xC0??0001 | NVHOST_IOCTL_CHANNEL_SUBMIT | M | REFUS GÉNÉRIQUE EXPLICITE | nvhost_gpu::Ioctl1 fallback | aucun case group 0/cmd 1 dans le runtime NS2 actif ; ioctl historique Maxwell refusé par NvResult::NotImplemented au lieu d'être présenté comme partiellement natif |
| 0xC0080002 | NVHOST_IOCTL_CHANNEL_GET_SYNCPOINT | C | HANDLER INDIQUÉ | GetSyncpoint | actif |
| 0xC0080003 | NVHOST_IOCTL_CHANNEL_GET_WAITBASE | C | HANDLER INDIQUÉ | GetWaitbase | actif |
| 0xC0080004 | NVHOST_IOCTL_CHANNEL_GET_MODMUTEX | M | REFUS EXPLICITE | nvhost_gpu::Ioctl1 (fail-closed) | ioctl exact 0xC0080004 : NotImplemented ; pas de module mutex matériel |
| 0x40040007 | NVHOST_IOCTL_CHANNEL_SET_SUBMIT_TIMEOUT | M | REFUS EXPLICITE | nvhost_gpu::Ioctl1 (fail-closed) | ioctl exact 0x40040007 : NotImplemented ; pas de timeout du scheduler promis |
| 0xC0080023 | NVHOST_IOCTL_CHANNEL_GET_CLK_RATE | M | REFUS EXPLICITE | nvhost_gpu::Ioctl1 (fail-closed) | ioctl exact 0xC0080023 : NotImplemented ; pas d'horloge GPU invitée inventée |
| 0xC018480C | NVGPU_IOCTL_CHANNEL_SET_ERROR_NOTIFIER | C | HANDLER INDIQUÉ | SetErrorNotifier | S2: état interne Switch; mem non nul initialise, mem=0 désinitialise; offset/size ignorés; aucun faux backing NvMap |
| 0x0000480E | NVGPU_IOCTL_CHANNEL_ENABLE | C | HANDLER INDIQUÉ | NativeChannelSetEnabled | état runnable natif partagé avec TSG |
| 0x0000480F | NVGPU_IOCTL_CHANNEL_DISABLE | C | HANDLER INDIQUÉ | NativeChannelSetEnabled | bloque réellement les submits natifs |
| 0x00004810 | NVGPU_IOCTL_CHANNEL_PREEMPT | M | REFUS EXPLICITE | fail-closed | préemption GPU réelle absente |
| 0x00004811 | NVGPU_IOCTL_CHANNEL_FORCE_RESET | M | REFUS EXPLICITE | fail-closed | reset GPU réel absent |
| 0x40104812 | [S2] NVGPU_IOCTL_CHANNEL_EVENT_ID_CONTROL | C | HANDLER INDIQUÉ | NativeEventIdControl | ABI 16 B exact; cmd 0/1/2; IDs bornés aux QueryEvent publics /dev/nvhost-gpu 1/2/3, KEvents réels et clear/enable/disable effectifs |
| 0xC0104813 | NVGPU_IOCTL_CHANNEL_CYCLE_STATS_SNAPSHOT | M | REFUS EXPLICITE | nvhost_gpu::Ioctl1 (fail-closed) | ioctl exact 0xC0104813 : NotImplemented ; pas de cycle stats fictives |
| 0x40084714 | NVGPU_IOCTL_CHANNEL_SET_USER_DATA | C | HANDLER INDIQUÉ | SetClientData | actif |
| 0x80084715 | NVGPU_IOCTL_CHANNEL_GET_USER_DATA | C | HANDLER INDIQUÉ | GetClientData | actif |
| 0x80804816 | NVGPU_IOCTL_CHANNEL_GET_ERROR_INFO | C | HANDLER INDIQUÉ | GetErrorInfo | ABI 128 B complète : renvoie le snapshot courant (type 0=no_error tant qu'aucune faute n'a été publiée). Le producteur de faute est un blocage GPU transversal, pas une absence de cet ioctl. |
| 0xC0104817 | NVGPU_IOCTL_CHANNEL_GET_ERROR_NOTIFICATION | C | HANDLER INDIQUÉ | GetErrorNotification | ABI 16 B complète : renvoie timestamp/info/status courant avec status 0xFFFF. Le producteur de faute est suivi séparément du lecteur. |
| 0x40204818 | NVGPU_IOCTL_CHANNEL_ALLOC_GPFIFO_EX | C | HANDLER INDIQUÉ | AllocGPFIFOEx | actif |
| 0xC0??4819 | NVGPU_IOCTL_CHANNEL_SUBMIT_GPFIFO_RETRY | C | HANDLER INDIQUÉ | SubmitGPFIFOBase1 (retry) | SwitchBrew : même ABI/flags/fence que H:0x08 ; direction et identifiant vérifiés, chemin WrapFixedVariable réel, backend SubmitGPFIFOImpl conservé ; console à qualifier |
| 0xC020481A | NVGPU_IOCTL_CHANNEL_ALLOC_GPFIFO_EX2 | C | HANDLER INDIQUÉ | AllocGPFIFOEx2 | actif |
| 0xC018481B | NVGPU_IOCTL_CHANNEL_SUBMIT_GPFIFO2 | C | HANDLER INDIQUÉ | SubmitGPFIFO | actif; S2 conserve les flags d'entrée dans la réponse Ioctl2 (Ounce utilise 6), NS1 conserve le zéro historique |
| 0xC018481C | NVGPU_IOCTL_CHANNEL_SUBMIT_GPFIFO2_RETRY | C | HANDLER INDIQUÉ | SubmitGPFIFOBase2 (retry) | SwitchBrew : même ABI/flags/fence que H:0x1B via Ioctl2 ; opcode 24 octets vérifié et même backend FD/GPFIFO/fence ; console à qualifier |
| 0xC004481D | NVGPU_IOCTL_CHANNEL_SET_TIMESLICE | C | HANDLER INDIQUÉ | SetChannelTimeslice | actif |
| 0xC010481E | [S2] NVGPU_IOCTL_CHANNEL_GET_USER_SYNCPOINT | C | HANDLER INDIQUÉ | GetUserSyncpoint | actif, valeur courante + shim GMMU |
| 0xC008481F | [S2] NVGPU_IOCTL_CHANNEL_SET_PREEMPTION_MODE | C | HANDLER INDIQUÉ | SetPreemptionMode | Ounce réel envoie {graphics=0, compute=2}; CTA bit1 NVIDIA accepté et retenu, autres modes non modélisés → NotImplemented |
| 0x40044820 | [S2] NVGPU_IOCTL_CHANNEL_OPEN | C | HANDLER INDIQUÉ | ChannelOpen | runlist authentifié |
| 0xC0504821 | [S2] NVGPU_IOCTL_CHANNEL_SETUP_BIND | P | HANDLER PARTIEL INDIQUÉ | ChannelSetupBind | kernel-submit implémenté; réponse ABI S2 80 B corrigée (`gpfifo_gpu_va`/`userd_gpu_va`/`usermode_mmio_gpu_va`/`hw_channel_id`); USERD/doorbell explicitement NotImplemented |


**P0 actuel** : le bootstrap Ounce est désormais couvert au niveau source depuis les handles GSV/VM jusqu’à `SUBMIT_GPFIFO2` : cmd 12/22 utilisent HIPC MOVE, cmd 203 renvoie le tableau VM 72 B exact, `flags=6` est conservé dans la réponse GPFIFO2 et l’état runnable reflète le bind Ampere réel. NVIDIA `nvgpu_channel_setup_bind → ga10b_channel_bind → nvgpu_channel_enable` confirme qu’Ounce n’a pas besoin d’un ENABLE explicite avant le premier submit ; les ENABLE/DISABLE explicites channel/TSG modifient ensuite ce même état. Pin actif : `a8c91708`. Le worker GSV vérifie également à la fermeture si une AS native a été empoisonnée par un remap/release sparse 215/216 ultérieur ; il cesse alors de retirer les mappings, NVMap, alias et session avant que les PTE partielles aient été invalidées. Ce comportement fail-closed retient exceptionnellement des ressources au lieu d'une UAF.  Quand 214 rencontre une GMMU poisoned, le worker conserve aussi sa session NvCore, car CloseSession déclencherait autrement UnmapAllHandles et pourrait détruire le backing encore référencé. Cette quarantaine exceptionnelle conserve des ressources jusqu'à la fin du processus au lieu de risquer une UAF ; les chemins normaux continuent à libérer leurs ressources. Une OOM pendant le remap dense 214 peut empoisonner les PTEs GMMU : le GPU worker conserve alors le NvMap et les pages aliasées en quarantaine au lieu de les libérer sous des PTEs encore vivantes. Le retour reste une erreur explicite ; seules les AS marquées poisoned déclenchent cette protection. MKW peut recréer un 214 sparse au même GPU VA sans 215 intermédiaire (upstream Lichii : croissance 300 MiB → 600 MiB → 1 GiB). Encore remplace désormais uniquement cette génération exacte : le successeur est préalloué côté ledger, l'ancien GMMU est drainé/libéré, les chevauchements étrangers restent rejetés et un échec de nouvelle réservation ne peut plus renvoyer un faux succès. Le chemin GPFIFO natif reprend aussi l'optimisation Lichii 46c3ee5010 : jusqu'à 512 headers d'ioctl restent en stockage inline et les listes copiées ne sont plus zéro-remplies avant écrasement, sans modifier les autres wrappers NVDRV ni la sémantique NS1. Les entrées GPFIFO natives héritées 0x18/0x1A refusent désormais les tailles nulles ou excessives avant toute initialisation GPU; les tailles non puissances de deux restent compatibles, et le chemin NS1 est inchangé. Le décodeur vidéo GSV 902/905/906 et son child TIPC 1 annoncent désormais des handles MOVE cohérents avec l'objet effectivement transmis, et libèrent la référence sur OOM au lieu de renvoyer un succès ou de fuir le handle. L'état d'activation channel/TSG est désormais distinct de la configuration GPFIFO : un ENABLE seul ne peut plus soumettre sans allocation réelle, et l'initialisation immédiate doit valider le scheduler avant publication du canal. ALLOC_GPFIFO_EX/EX2 accepte désormais l'allocation avant liaison GMMU sans perdre l'état runnable logique, mais la première soumission reste bloquée jusqu'au véritable bind. Les sessions GSV 202/305/497/1402 et les handles GPU 12/22 annulent leurs références MOVE si la mise en file IPC échoue par OOM. Contrôles hôtes vendor ciblés réussis ; console et build natif non vérifiés. USERD/doorbell reste **P** faute de preuve d’usage. La prochaine preuve décisive reste console : première vraie soumission puis `guest_frame_handoff`.

## 11. NVDRV — /dev/nvhost-tsg-gpu

| Ioctl | Nom SwitchBrew | Statut fonctionnel (F) | Traitement déclaré (R) | Handler Encore | Écart / raison |
| --- | --- | --- | --- | --- | --- |
| 0xC0045401 | NVGPU_TSG_IOCTL_BIND_CHANNEL | C | HANDLER INDIQUÉ | BindTsgChannel | owner process vérifié |
| 0xC0045402 | NVGPU_TSG_IOCTL_UNBIND_CHANNEL | C | HANDLER INDIQUÉ | Unbind | actif |
| 0x00005403 | NVGPU_TSG_IOCTL_ENABLE | C | HANDLER INDIQUÉ | SetTsgEnabled | propage l’état runnable aux channels authentifiés ; rollback transactionnel |
| 0x00005404 | NVGPU_TSG_IOCTL_DISABLE | C | HANDLER INDIQUÉ | SetTsgEnabled | désactive le même état partagé et bloque les submits |
| 0x00005405 | NVGPU_TSG_IOCTL_PREEMPT | M | REFUS EXPLICITE | TsgIoctl fail-closed | cas connu explicite; `// not implemented yet on Encore`, préemption GPU réelle absente |
| 0xC0085407 | NVGPU_TSG_IOCTL_SET_RUNLIST_INTERLEAVE | P | HANDLER PARTIEL INDIQUÉ | ConfigureTsgScheduling | Ounce exact; LOW/MEDIUM/HIGH validés et retenus avant bind; après bind → NotImplemented faute de runlist reload réel |
| 0xC0045408 | NVGPU_TSG_IOCTL_SET_TIMESLICE | P | HANDLER PARTIEL INDIQUÉ | ConfigureTsgScheduling | Ounce exact; 1000..50000 µs validés/retenus avant bind; après bind → NotImplemented faute de runlist reload réel |
| 0xC0105409 | NVGPU_TSG_IOCTL_EVENT_ID_CTRL | M | REFUS EXPLICITE | TsgIoctl fail-closed | cas connu explicite; `// not implemented yet on Encore`, livraison d'événement TSG absente |
| 0x8004540A | NVGPU_TSG_IOCTL_GET_TIMESLICE | C | HANDLER INDIQUÉ | GetTsgTimeslice | Ounce exact; renvoie l'état u32 retenu avant/après bind |
| 0xC018540B | NVGPU_TSG_IOCTL_BIND_CHANNEL_EX | C | HANDLER INDIQUÉ | BindTsgChannel extended | FD + VEID validés |
| 0xC018540C | NVGPU_TSG_IOCTL_READ_SINGLE_SM_ERROR_STATE | M | REFUS EXPLICITE | TsgIoctl fail-closed | cas connu explicite; `// not implemented yet on Encore`, état SM matériel par TSG absent |
| 0xC008540D | NVGPU_TSG_IOCTL_SET_L2_SECTOR_PROMOTION | M | REFUS EXPLICITE | TsgIoctl fail-closed | Ounce exact; cas connu explicite; `// not implemented yet on Encore`, politique cache L2 par TSG absente |


ENABLE/DISABLE ne sont plus des `Success` vides : ils modifient l’état runnable partagé channel/TSG et conditionnent réellement `SubmitGPFIFOImpl`. PREEMPT reste fail-closed tant qu’une frontière de préemption GPU réelle n’est pas modélisée.

**Preuve Ounce TSG (21/11)** : `libnvrm_gpu` émet réellement `0xC0085407` pour l'interleave, `0xC0045408` pour la timeslice et `0x8004540A` pour le getter. NVIDIA valide interleave 0/1/2 et timeslice 1000..50000 µs; tant que le TSG n'est pas lié à une runlist, son driver ne fait que stocker ces valeurs. Encore reproduit uniquement cette phase sûre. `0xC008540D` touche la politique L2 et reste explicitement non implémenté.

Les quatre commandes TSG encore classées **M** sont explicitement fail-closed : PREEMPT, EVENT_ID_CTRL, READ_SINGLE_SM_ERROR_STATE et SET_L2_SECTOR_PROMOTION. Le reload interleave/timeslice après bind reste **P** séparément.

## 12. NVDRV — /dev/nvhost-prof-dev-gpu

| Ioctl | Nom SwitchBrew | Statut fonctionnel (F) | Traitement déclaré (R) | Handler Encore | Écart / raison |
| --- | --- | --- | --- | --- | --- |
| 0x40085001 | NVGPU_PROFILER_IOCTL_BIND_CONTEXT | M | REFUS GÉNÉRIQUE EXPLICITE | nx2_stub_device::Stub | le node /dev/nvhost-prof-dev-gpu passe par le fallback /dev/nvhost-* actif ; ioctl renvoie NvResult::NotImplemented sans sortie/état fabriqué |
| 0x40105002 | NVGPU_PROFILER_IOCTL_RESERVE_PM_RESOURCE | M | REFUS GÉNÉRIQUE EXPLICITE | nx2_stub_device::Stub | le node /dev/nvhost-prof-dev-gpu passe par le fallback /dev/nvhost-* actif ; ioctl renvoie NvResult::NotImplemented sans sortie/état fabriqué |
| 0x40085003 | NVGPU_PROFILER_IOCTL_RELEASE_PM_RESOURCE | M | REFUS GÉNÉRIQUE EXPLICITE | nx2_stub_device::Stub | le node /dev/nvhost-prof-dev-gpu passe par le fallback /dev/nvhost-* actif ; ioctl renvoie NvResult::NotImplemented sans sortie/état fabriqué |
| 0xC0305004 | NVGPU_PROFILER_IOCTL_ALLOC_PMA_STREAM | M | REFUS GÉNÉRIQUE EXPLICITE | nx2_stub_device::Stub | le node /dev/nvhost-prof-dev-gpu passe par le fallback /dev/nvhost-* actif ; ioctl renvoie NvResult::NotImplemented sans sortie/état fabriqué |
| 0x00005005 | NVGPU_PROFILER_IOCTL_FREE_PMA_STREAM | M | REFUS GÉNÉRIQUE EXPLICITE | nx2_stub_device::Stub | le node /dev/nvhost-prof-dev-gpu passe par le fallback /dev/nvhost-* actif ; ioctl renvoie NvResult::NotImplemented sans sortie/état fabriqué |
| 0x00005006 | NVGPU_PROFILER_IOCTL_BIND_PM_RESOURCES | M | REFUS GÉNÉRIQUE EXPLICITE | nx2_stub_device::Stub | le node /dev/nvhost-prof-dev-gpu passe par le fallback /dev/nvhost-* actif ; ioctl renvoie NvResult::NotImplemented sans sortie/état fabriqué |
| 0x00005007 | NVGPU_PROFILER_IOCTL_UNBIND_PM_RESOURCES | M | REFUS GÉNÉRIQUE EXPLICITE | nx2_stub_device::Stub | le node /dev/nvhost-prof-dev-gpu passe par le fallback /dev/nvhost-* actif ; ioctl renvoie NvResult::NotImplemented sans sortie/état fabriqué |
| 0xC0285008 | NVGPU_PROFILER_IOCTL_PMA_STREAM_UPDATE_GET_PUT | M | REFUS GÉNÉRIQUE EXPLICITE | nx2_stub_device::Stub | le node /dev/nvhost-prof-dev-gpu passe par le fallback /dev/nvhost-* actif ; ioctl renvoie NvResult::NotImplemented sans sortie/état fabriqué |
| 0xC0205009 | NVGPU_PROFILER_IOCTL_EXEC_REG_OPS | M | REFUS GÉNÉRIQUE EXPLICITE | nx2_stub_device::Stub | le node /dev/nvhost-prof-dev-gpu passe par le fallback /dev/nvhost-* actif ; ioctl renvoie NvResult::NotImplemented sans sortie/état fabriqué |
| 0x0000500A | NVGPU_PROFILER_IOCTL_UNBIND_CONTEXT | M | REFUS GÉNÉRIQUE EXPLICITE | nx2_stub_device::Stub | le node /dev/nvhost-prof-dev-gpu passe par le fallback /dev/nvhost-* actif ; ioctl renvoie NvResult::NotImplemented sans sortie/état fabriqué |
| 0x4010500B | NVGPU_PROFILER_IOCTL_VAB_RESERVE | M | REFUS GÉNÉRIQUE EXPLICITE | nx2_stub_device::Stub | le node /dev/nvhost-prof-dev-gpu passe par le fallback /dev/nvhost-* actif ; ioctl renvoie NvResult::NotImplemented sans sortie/état fabriqué |
| 0x0000500C | NVGPU_PROFILER_IOCTL_VAB_RELEASE | M | REFUS GÉNÉRIQUE EXPLICITE | nx2_stub_device::Stub | le node /dev/nvhost-prof-dev-gpu passe par le fallback /dev/nvhost-* actif ; ioctl renvoie NvResult::NotImplemented sans sortie/état fabriqué |
| 0x4010500D | NVGPU_PROFILER_IOCTL_VAB_FLUSH_STATE | M | REFUS GÉNÉRIQUE EXPLICITE | nx2_stub_device::Stub | le node /dev/nvhost-prof-dev-gpu passe par le fallback /dev/nvhost-* actif ; ioctl renvoie NvResult::NotImplemented sans sortie/état fabriqué |


Ces commandes sont documentées par SwitchBrew mais restent **hors P0 boot/gameplay** tant qu’aucun titre retail ne prouve leur usage. Elles doivent rester explicitement non implémentées plutôt que recevoir des succès génériques.

## 13. Debug/profiler et commandes S2 sans nom public

SwitchBrew publie aussi des ioctls S2 `/dev/nvhost-dbg-gpu` dont plusieurs n’ont pas encore de nom (`0x4008441F`, `0x00004420`, `0xC0184421`, `0xC0184429`, `0x4010442A`, `0x4010442B`) ainsi que des variantes S2 nommées pour MMU/SM/HWPM. **Statut initial Encore : M/U** sauf preuve contraire future. Ils ne sont pas prioritaires pour MKW/Bananza et ne doivent pas détourner du chemin GSV→NVDRV→GPFIFO.

## 14. Arbitrage final de couverture source NS2 (sans faux succès)

Le critère de sortie **source** est borné au boot, au GPU, à la mémoire, aux IPC et aux services réellement sélectionnés pour les titres NS2 ciblés. Ce classement ne constitue **pas** une promesse de couverture exhaustive du firmware : les 96 observations du 20/11 n'étaient pas 96 bugs démontrés.

| Sous-système | Décision de portée | Condition qui rouvrirait une correction |
| --- | --- | --- |
| **P0 GSV → VM → NVDRV → GPFIFO** | Source native sélectionnée couverte jusqu'à SUBMIT_GPFIFO2, y compris ownership, fail-closed, remplacements sparse 214, OOM partielle et sessions ; **non qualifiée sur console** | Log du Title ID montrant le premier IPC ou GPU submit rejeté / bloqué, ou anomalie causale dans le C++ réellement compilé |
| **GSV cmd 437** | **U : hors implémentation P0** ; aucun paquet TIPC raw 0x1C5 observé. Le client Ounce connu utilise cmd 423 raw 0x1B7 pour la création native requise | Paquet 437 réel et ABI associée, sans inférer à partir du seul nom |
| **NVGPU CHANNEL_SETUP_BIND** | Noyau/runlist/GPFIFO effectifs côté source ; USERD/doorbell utilisateur explicitement NotImplemented. Ne pas fabriquer de token | Preuve d'un canal utilisateur/doorbell réellement utilisé par MKW/Bananza |
| **TSG** | ENABLE/DISABLE, interleave et timeslice pré-bind effectifs. Reload post-bind, PREEMPT, EVENT_ID_CTRL, état SM et politique L2 laissés partiels ou fail-closed | IPC/ioctl observé et blocage de scheduler imputable au chemin exact |
| **GSV vidéo** | Décodeur sélectionné ; remote-memory 210 non implémenté. **Encodeur 1001/1002 correctement aiguillé vers UnavailableVideoEncoder, pas vers le décodeur** : NotImplemented explicite | Utilisation effective d'un encodeur ou du buffer distant 210 par un titre ciblé |
| **Display / VI2** | 53 C-source (tick au release, non PS5) ; `13`, `107`, `113`, `301`, `302` U avec stubs nommés fail-closed | Tester l'ABI et la présentation réelle sur titre |
| **Camera / Adraw / InterModuleImage / debug / profiling** | Non nécessaires au P0 prouvé ; laisser les fonctions absentes ou fail-closed. Aucun stub Success | Preuve d'utilisation indispensable au démarrage/gameplay |
| **Variantes worker firmware 19.x** | Numérotation/ABI versionnée hors périmètre si le firmware invité ciblé utilise le chemin actuel | Title ID / version et commande raw imposant l'autre variante |

**Mémoire GPU 214/215/216 :** la lecture des propriétaires sélectionnés montre que le remap prépare les tables et les pins avant de modifier les PTE ; une OOM pendant la modification empoisonne l'AS et interdit une nouvelle mutation. Le worker doit alors garder les pages CPU aliasées, le handle NVMap et sa session, car le dernier FreeHandle ou CloseSession pourrait retirer un backing encore pointé par des PTE partielles. En dehors de cette quarantaine exceptionnelle, le rollback normal conserve le comportement de libération. Le test hôte exécutable est dans tools/ns2/check_native_gpu_worker_sparse_ipc_host.py ; **ne pas annoncer ce contrat validé avant son exécution verte sur le couple exact**.

**Règle de clôture :** une limitation U/M/P connue mais sans chemin prouvé n'impose pas une implémentation hypothétique ; une corruption mémoire, un faux succès HLE, une ABI démontrée incorrecte ou un blocage observé sur un chemin actif interdit la clôture. L'issue NS2 #123 et les tests PS5 restent requis pour valider les titres.

## 15. État console / critère de fermeture

**Validation PS5 native R457 (23/11) :** moteur [`25f12c02`](https://github.com/niakw/ProsperoEden-Encore/commit/25f12c020eb69ea9b7b29aac35dadcfe8b38f918), gitlink vendor [`716e069f`](https://github.com/niakw/Prospero.Eden-Encore-vendor/commit/716e069f212b89b6fd13af56b0677343cf41ba07), [run natif 45087056642](https://github.com/niakw/ProsperoEden-Encore/actions/runs/45087056642) : **compilation C++ native 1257/1257 et stage PS5 réussis**, `eboot.bin` de 80 433 455 octets et contrôles du dossier staged réussis (200 fichiers). L'upload FTP a réussi ; le run s'est arrêté **uniquement au retéléchargement**, l'API GitHub ayant retourné 0 artefact immédiatement après l'upload. L'artefact de 41 394 005 octets a été récupéré et son SHA-256 vérifié, de même que la racine ZIP unique `PPSA99008/`, les CRC et le `titleId`.

**Packaging vert sans recompilation :** [run 45089261067](https://github.com/niakw/ProsperoEden-Encore/actions/runs/45089261067), commit de reprise [`2e272949`](https://github.com/niakw/ProsperoEden-Encore/commit/2e2729497e3857bb892624a9242fd202727e9ca2), vendor test-only [`6c15ec8d`](https://github.com/niakw/Prospero.Eden-Encore-vendor/commit/6c15ec8d1143eb1ae3092a2b984f0bc5bfcc364b) : restauration du checkpoint déjà compilé **verte**, compilation sautée, upload + téléchargement/vérification FTP **verts**, distribution `dist/` publiée. L'artefact FTP de la reprise a 200 entrées ZIP et SHA-256 `96e01a8b21007e9ccd02b45ccec111f5d206b52275ebf49ba126eba8ac628cf8`, CRC intégral valide et `encore-release.json` porte toujours le **SHA réellement compilé `25f12c02`**. Les deux ZIP internes de la distribution passent aussi CRC/SHA256.

**Limite du packaging :** le bundle de reprise ne contient que `dist/` ; le `build/symbols/` (ELF non dépouillé, map et provenance crash) n'a pas été transporté par le checkpoint original. Cela **ne requalifie pas** le bundle crash-symboles. L'unique warning visible en compilation concerne la comparaison `u64 > size_t::max()` dans `nx.cpp:296` sur la cible 64 bits ; il ne bloque pas le runtime.

**Validation console : toujours absente pour ces SHAs**. Aucun lancement de Mario Kart World, Bananza ou FC27 avec le nouveau package n'a encore été constaté ; aucune amélioration de premier GPU submit / première frame invitée n'est déduite du build vert.


**Correctifs de compilation NUP/NIFM validés par compilation native du 23/11 :** sur le moteur, inclusion de `core/loader/loader.h` dans `headless/nup_v1_native_content.cpp` pour la définition complète de `Loader::ResultStatus` ; sur le vendor `716e069f`, virgule ajoutée à l'entrée `DestroyRewriteRule` de `nifm.cpp`. Leur couple moteur `25f12c02` / vendor `716e069f` a compilé et validé le staging ; le premier run est resté rouge uniquement sur la lecture immédiate de l'artefact GitHub, ensuite corrigée et revalidée en reprise.

**Actualisation build 23/11, couple moteur `1b772815` / vendor `ee20b5a0` :** [run 45084634419](https://github.com/niakw/ProsperoEden-Encore/actions/runs/45084634419) a échoué à la fin de la compilation native (Ninja, vers 1459/1463 unités), sur **deux causes C++ distinctes** : (1) `headless/nup_v1_native_content.cpp:50` utilise `Loader::ResultStatus::Success` avec un type incomplet ; (2) `vendor/encore-active/ns2-runtime/hle/core/hle/service/nifm/nifm.cpp:1111` a une initialisation de table incohérente (accolade manquante, puis échec `RegisterHandlers`). **Pas d'ELF/package installable, pas de validation PS5 de ces correctifs.** Ces erreurs de build ne sont pas des écarts Lichii de table de commandes.

Les derniers logs NS2 représentatifs disponibles avant ce registre pour Mario Kart World et Donkey Kong Bananza indiquaient toujours **`gpu_submit_sample=0`** et **`guest_frame_handoff=0`**. Ce registre ne change pas ce fait.

Une ligne **C** devient réellement qualifiée uniquement lorsque le couple moteur/vendor exact est :
1. compilé dans le build PS5 natif unique ;
2. lancé sur un jeu représentatif ;
3. observé sans faux succès IPC ;
4. puis, pour le P0 GPU, avec première soumission GPFIFO et première frame invitée confirmées.

## 16. Procédure de mise à jour

À chaque changement NS2 :
- noter le **SHA moteur** et le **gitlink vendor** ;
- comparer la page SwitchBrew et l’upstream SDK si la commande a changé ;
- modifier le statut de la **ligne existante**, pas créer un second inventaire ;
- renseigner les deux colonnes **F** et **R** séparément pour chaque commande, même si un stub ou refus explicite existe alors que la fonctionnalité reste `M` ;
- indiquer le handler/source réellement sélectionné ;
- ajouter le run GitHub hôte pertinent ;
- laisser la validation console à **non qualifiée** jusqu’au test PS5 réel.

Le présent registre reste le tableau NS2 de référence : couverture SwitchBrew (§0–§16) et Lichii (§17). L'audit du 20/11 reste une photographie historique plus large.

## 17. Parité structurelle avec Lichii `nx2` — suivi complémentaire daté du 23/11/2026

**Actualisation vérifiée :** le vendor `716e069f` a bien été sélectionné et compilé dans le moteur `25f12c02` (run natif `45087056642`, complété sur la reprise verte `45089261067`). **230/230 IDs nommés** dans les huit tables comparées ; la reprise conserve ce binaire. Le vendor `6c15ec8d` apporte seulement un correctif de vérification d'antériorité NX, sans modification des sources runtime ; le snapshot historique et son échec C++ précédent restent conservés pour la traçabilité.

**Réponse actualisée :** dans les huit tables d'interfaces examinées, **230 / 230 IDs Lichii ont un handler nommé chez Encore**, sans fallback nécessaire pour ces IDs. Les neuf stubs auparavant absents de la table GPU sont nommés depuis vendor `716e069f`. **Parité des identifiants de ces huit tables : complète.** Cela ne certifie **ni les retours exacts des stubs ni les autres services et ABI NS2**. Les stubs de Lichii sont acceptés comme structure, mais ne deviennent pas des fonctionnalités émulées.

### 17.1 Couple de révisions, périmètre et règle de comptage

- **Lichii `nx2` exact :** [`66c555ad9a21b1caaf57a5d9f8f1fea6f90c2508`](https://github.com/zortos293/Lichii/blob/66c555ad9a21b1caaf57a5d9f8f1fea6f90c2508/src/core/hle/service/nx2_gsv.h) ; tables des interfaces `INx2GraphicsSystemSession`, `INx2Vi2Session`, `INx2SyncptSession`, `INx2GpuTimeSession`, `INx2ChatGsvSession`, `INx2CameraSession`, `INx2VideoSession`, `INx2GpuSession`. Lichii déclare également `INx2NvsrvSession`, mais **aucun ID** dans cette classe ; elle n'entre pas dans le total 230.
- **Encore exact :** moteur [`1b772815a470008cc3bc80a3f97f65553569c649`](https://github.com/niakw/ProsperoEden-Encore/tree/1b772815a470008cc3bc80a3f97f65553569c649) → sous-module vendor [`ee20b5a00e4fd96c02b5d12d6f4eaabee8623bf3`](https://github.com/niakw/Prospero.Eden-Encore-vendor/tree/ee20b5a00e4fd96c02b5d12d6f4eaabee8623bf3). `headless/CMakeLists.txt` sélectionne `encore-active/ns2-runtime/graphics_supervisor/.../graphics_supervisor.cpp` dans `core`, les deux TU `gpu_session.cpp` et `gpu_worker.cpp` dans `core`, et `video_decoder/.../graphics_video_decoder_session.cpp` dans `core` sur le chemin `PS5_NATIVE && EDEN_REVIEWED_DUAL_NPDM`. **La sélection CMake est constatée dans les règles sources ; la compilation et l'exécution effectives restent des niveaux de preuve séparés.**
- **Méthode :** comparer des clés **(interface, ID)**, et non un ID isolé. Pour `GpuSession`, Lichii regroupe commandes du parent et de la sous-session dans sa classe ; Encore les sépare en `IGpuSession` et `IGpuWorker`. Les deux tables Encore sont donc réunies **sans double comptage** ; l'ID `0` du worker, déjà `0` dans le parent, n'ajoute pas une seconde commande Lichii.
- **Interprétation :** « nommé » signifie *entrée explicite dans la table de dispatch*, **pas** sortie IPC identique, effet identique, implémentation matérielle, ni test PS5. Les IDs supplémentaires propres à Encore ne comptent jamais dans le numérateur Lichii. Cette matrice **n'augmente pas** le total SwitchBrew 316 (§0–§16).

### 17.2 Tableau de parité, recalcul sur les tables sources

| Table / interface Lichii | IDs Lichii | IDs Lichii nommés chez Encore | IDs Lichii servis seulement par fallback | Limite vérifiée |
| --- | ---: | ---: | ---: | --- |
| GSV — `INx2GraphicsSystemSession` | **117** | **117** | 0 | La table GSV Encore possède 170 IDs au total (53 additionnels). Les 43 entrées ajoutées au dernier lot Lichii sont en majorité des refus nommés, non des effets émulés. |
| VI2 — `INx2Vi2Session` | **53** | **53** | 0 | Encore expose 54 IDs (dont le `21` supplémentaire). Cmd `53` fournit maintenant des ticks de release ; plusieurs IDs opaques ont seulement un `Unsupported` explicite. |
| Syncpt — `INx2SyncptSession` | 7 | 7 | 0 | Les 7 IDs sont présents ; le comportement du stub `21` n'est pas identique par simple existence. |
| GPU Time — `INx2GpuTimeSession` | 2 | 2 | 0 | GSV `1121` fournit désormais une **vraie session MOVE** ; mesure GPU `11` non disponible et refusée `NotSupported`. |
| Chat — `INx2ChatGsvSession` | 3 | 3 | 0 | Événements et virtual display encore à qualifier pour ABI et effet. |
| Camera — `INx2CameraSession` | 3 | 3 | 0 | Stubs acceptés comme structure, pas comme capture caméra fonctionnelle. |
| Video — `INx2VideoSession` | 17 | 17 | 0 | `210` est un refus explicite de mémoire distante chez Encore, contre une réponse `Success` de stub chez Lichii : divergence comportementale connue. |
| GPU parent + worker — `INx2GpuSession` | **28** | **28** | **0** | 20 IDs nommés dans `IGpuSession`, 8 autres dans `IGpuWorker` ; les neuf stubs auparavant génériques sont nommés et refusent `NotImplemented` (réponse différente des stubs zéro Lichii). |
| **Total des 8 tables comparées** | **230** | **230** | **0** | **100 % des ID de ces 8 tables ont un handler nommé.** Cette parité structurelle des tables ne démontre pas l'équivalence ABI/IPC ni la couverture des autres services. |

**9 écarts de déclaration clôturés au niveau source :** les commandes `23`, `24`, `25`, `34`, `51`, `8001`, `8002`, `8003`, `8004` ont maintenant chacune une entrée dans `IGpuSession::IGpuSession` vers `RejectOpaqueNx2Command`, avec test de présence des neuf IDs et du refus fail-closed dans `tests/ns2_gpu_partition_new_sdk_source.py`. **Une différence de comportement reste assumée :** `StubReplyZeroed` chez Lichii et `ResultNotImplemented` chez Encore. Aucun test PS5 de ces commandes n'a encore été reçu.

**Autres différences de comportement sans manque d'ID** : VI2 inconnu et Syncpt `21` peuvent produire une sortie nulle chez Lichii et `NotImplemented` chez Encore ; vidéo `210` retourne `Success` chez Lichii mais est refusée chez Encore tant que son backend remote-memory est absent. Un stub Lichii **compte comme structure**, mais **son retour n'établit pas une implémentation fonctionnelle ni la sécurité d'un faux succès** sur PS5.

### 17.3 Services hors de ces huit tables — aucune certification générale

| Domaine | Constat sur le couple moteur/vendor | Travail exact restant pour annoncer la parité structurelle |
| --- | --- | --- |
| **GSV / VI2 / Syncpt / GPU Time / Chat / Camera / Video** | IDs comparés exhaustivement **dans ces tables-là**, pas toutes les sous-interfaces ni tous les modes | ABI des arguments/réponses, types de handles, events, buffers, versions et sémantique des stubs Lichii à comparer avant une équivalence fonctionnelle |
| **GPU Session / Worker** | **28/28 IDs nommés**, dont neuf stubs explicitement enregistrés sur `IGpuSession` | Équivalence des réponses stub/ABI non démontrée ; vérifier séparément la progression GPFIFO |
| **AM / appletOE / SelfController** | C++ Lichii/overlays `ns2-runtime/hle/.../am`, `am_structure`, `self_controller` présents ; comparaison globale **non réalisée** | Diff versionné des IDs, des interfaces enfants et de l'ABI, puis CMake/nomenclature pour tous les propriétaires réellement sélectionnés |
| **HID** | Intégrations NS2 (Nmouse, vibration `213/214`) présentes ; parité totale **non mesurée** | Comparer toutes les commandes, leurs versions firmware et les stubs Lichii au `hid_server.cpp/.h` actif |
| **ACC / SET / NIFM / audio / CAPS / LM / MII** | Sources d'overlays présents dans `ns2-runtime/hle/core/hle/service/` ; ACC `130` corrigée ; **pas de ratio global vérifié** | Recouper les tables Lichii service par service, les objets et les résultats IPC ; ne pas inférer le statut depuis un répertoire présent |
| **NVDRV(2), SVC, kernel, loader, formats** | Plusieurs propriétaires natifs présents ; des chemins ont été vérifiés indépendamment | Confronter ioctls/ABI, CMake, ACL firmware, chargement et transitions réelles ; une table GSV pleine ne démontre pas le boot |
| **GPU Ampere, shader, présentation, vidéo et rendu PS5** | Les interfaces de service ne couvrent pas ce domaine matériel | Première soumission GPU invitée et première frame sur Mario Kart World et Bananza, puis cohérence buffers/fences et stabilité |

### 17.4 Critères de fermeture, sans confondre les objectifs

1. **SwitchBrew (§0–§16) :** compteur F/R de **316 commandes**, actuellement **175 C / 3 P / 108 M / 24 U / 6 V**, **316/316 avec comportement de dispatch identifié**. Ce n'est pas un certificat d'implémentation complète.
2. **Parité des huit tables Lichii :** **230/230 entrées nommées**, **0 fallback pour ces IDs** sur le vendor `716e069f` ; la différence de réponse des stubs reste documentée et ne vaut pas conformité des ABIs.
3. **Parité structurelle NS2 globale :** comparaison **non terminée** pour AM, HID, ACC, réseau, fichiers, kernel et variantes. **Aucun « 100 % NS2 vs Lichii » n'est revendiqué sans diff réellement réalisé.**
4. **Boot PS5 :** exiger un build valide à SHAs moteur/vendor connus et une preuve console des premières soumissions GPU `gpu_submit_sample > 0`, puis `guest_frame_handoff > 0` et première image invitée réelle. Ce n'est **pas** un sous-compteur de parité structurelle.

**Provenance des lots présents sur ce couple :** vendor `38382993` (VI2 53), `852c4be1` (ACC), `95cdffa8` (stubs VI2), `2873d15e` (table GSV), `ee20b5a0` (`gpu_time` et ABI). Le build [45084634419](https://github.com/niakw/ProsperoEden-Encore/actions/runs/45084634419) a **échoué en compilation C++ native** (`nup_v1_native_content.cpp:50`, `nifm.cpp:1111`), sans package ; les tests PS5 de ces correctifs n'ont pas été reçus.


---

## 18. Reprise sur `main` — revue ciblée Lichii / EglantinePS5 du 23/11/2026

**Révisions comparées :** Lichii [`nx2:63cde532`](https://github.com/zortos293/Lichii/tree/63cde5321e8402a827458807c4e09420db33afd1), EglantinePS5 [`main:5eb70367`](https://github.com/heydemoura/EglantinePS5/tree/5eb70367ffde039f237b3b828856f4b4247ea09e), Encore vendor `main:0390980a` (contrôle hôte sécurité/qualité [45200615951](https://github.com/niakw/Prospero.Eden-Encore-vendor/actions/runs/45200615951) vert). Cet addendum concerne le **source/dispatch sélectionné** ; aucun build ou essai console du nouveau couple n'est implicite. Les relevés antérieurs des §0 et §17 restent des instantanés historiques, pas des chiffres courants de tous les sous-systèmes.

### 18.1 Tables supplémentaires relues, propriétaires sélectionnés par CMake

Contrôle sur `headless/CMakeLists.txt` du moteur : `EDEN_SHARED_NS2_AM` remplace `application_functions.cpp`; `EDEN_NS2_EARLY_HLE_ROOT` remplace `hid_server.cpp`; `EDEN_NS2_SERVICE_PARITY_ROOT` remplace les fichiers ACC, NIFM, CAPS, SET, MII, LM et audio en natif PS5 avec l'option NS2 approuvée. Comparaison des déclarations `FunctionInfo` et de leurs IDs avec Lichii :

| Propriétaire actif comparé | Lichii / Encore (entrées) | Tables inspectées | Écart de déclaration et limite |
| --- | ---: | ---: | --- |
| `am/service/application_functions.cpp` | **74 / 74** | 1 | Zéro ID absent ; cmd 210 nommé `Unknown210` chez Encore vs `GetOperationModeRefreshEvent (guessed)` chez Lichii. Cmd 320 nommé/servi autrement. **Pas de parité d'ABI déduite.** |
| `hid/hid_server.cpp` | **235 / 235** | 1 | Zéro ID absent. Lichii a des stubs nommés pour 138/139 et 3130–3133/3138/3139, Encore des handlers d'état `SceneId` / `Nmouse`; 3110–3113 passent par `StubJcms`. Différence comportementale à tester, non un oubli d'ID. |
| `nifm/nifm.cpp` | **86 / 86** | Plusieurs interfaces | Entrées par table conservées ; 52 IDs numériques distincts dans le fichier ne représentent pas 52 fonctions uniques, car réutilisés dans plusieurs interfaces. |
| `caps/caps_u.cpp` + `caps/caps_su.cpp` | **18 / 18 ; 5 / 5** | 1 + 1 | Aucun ID absent dans les tables sélectionnées. |
| `set/settings_server.cpp` | **18 / 18** | 1 | Aucun ID absent. |
| `mii/mii.cpp` | **44 / 44** | 3 | Aucun ID absent par table ordonnée. |
| `lm/lm.cpp` | **10 / 10** | 3 | Aucun ID absent par table ordonnée. |
| `audio/audio_device.cpp` + `audio/audio_renderer_manager.cpp` | **22 / 22 ; 5 / 5** | 1 + 1 | Aucun ID absent. |
| `acc/acc.cpp` | **25 tables Lichii / 24 tables Encore** ; **502 / 490 entrées** | 25 vs 24 | **Écart structurel exact :** Lichii ajoute un `ScratchSystemAccount` de 12 entrées conditionné par `GetScratchProfileManager()` et son propre choix dans `LoopProcess`. Encore ne possède ni ce propriétaire ni ce mécanisme de profil scratch. Son `acc:su` classique est déjà enregistré. EglantinePS5 `main:5eb70367` a également 24 tables, sans `ScratchSystemAccount`. Il faut analyser l'ownership du profil avant de transplanter cet ajout ; son absence n'est **pas** un défaut de boot démontré. |

**Méthode/limites :** comparaison statique des tables et de leurs déclarations (non une exécution d'IPC). Les comptes `ACC` portent sur toutes les tables du fichier et `NIFM` sur plusieurs interfaces ; ne pas additionner ces entrées au total SwitchBrew 316 ou aux 230 IDs des huit tables GPU/VI2/GSV. La sémantique, les tailles de requête/réponse, les handles MOVE/COPY, les événements, les modes de firmware et les effets de `nullptr` / stub exigent des audits séparés.

### 18.2 Comparaison PS5 et Lichii : différences restantes sans faux positif

- **Avant première image :** les logs Encore R457 du 23/11 montrent toujours `gpu_submit_sample=0` et `guest_frame_handoff=0` sur MKW / Bananza / Z-A ; un chargement animé ne constitue pas une image du jeu. L'interface `IApplicationFunctions` cmd 22 est bien présente chez les trois projets ; son *résultat d'arrêt invité* est maintenant exposé par la nouvelle trace `EDEN_APP_TERMINATE_RESULT` du vendor, mais **aucune session PS5 de ce nouveau commit n'a encore prouvé le code retourné**. Ne pas attribuer la stalle à cmd 22 sur son seul ordre de journalisation.
- **Conteneur Pokopia (mise à jour source après la comparaison) :** le commit moteur [`be65b758`](https://github.com/niakw/ProsperoEden-Encore/commit/be65b75818064effa54532019d3490567b6dfef1) reprend la règle observée chez **Lichii `nx2` et EglantinePS5** : une plage de **métadonnées optionnelles hors du fichier ou sans offset** est ignorée sans lecture ni allocation, avec trace `EDEN_NUP_OPTIONAL_METADATA_SKIPPED`. Les métadonnées *internes* invalides, les alias au TOC et les dépassements de budget parser restent refusés (`EDEN_NUP_METADATA_BOUNDS_REJECT`), tout comme les empreintes du TOC et des membres. Test C++ hôte ajouté dans `tools/check-nup-v1-vfs-host.py`, avec cas positif hors fichier et négatif sur alias TOC ; [workflow NUP](https://github.com/niakw/ProsperoEden-Encore/actions/workflows/nup-v1-host.yml). **Pokopia non retesté sur console** : cela corrige un comportement source, sans certifier son boot.
- **Source Lichii actuelle :** les commits récents `#2481` (soumissions Vulkan à frontière de render-pass), `#2485` (durée de vie des images) et `#2470/#2215/#2173` (textures et coûts de Bananza) concernent essentiellement les ressources/pipelines **après progression du GPU**. Écart à comparer dans les sources PS5 sélectionnées, **pas** une résolution causalement prouvée du démarrage sans première soumission.
- **EglantinePS5 :** le dépôt porte une pile NS2 et un mécanisme mémoire `demand-zero` avec mesures de jeux **sur un autre binaire**. Encore a intégré les états `ZERO -> OWN` pour NS1/NS2 avec tests hôtes (document [architecture mémoire](../EDEN_ENCORE_GUEST_MEMORY_NS1_NS2_PS5_ARCHITECTURE.md)), sans preuve de cohérence GPU/boot sur la console pour les derniers commits. Les expériences mémoire, fragmentation, compression et optimisations shader d'EglantinePS5 ne doivent pas être déclarées « manquantes » si le propriétaire Encore a déjà un équivalent, ni fusionnées sans audit des différences de code/PS5 ABI.
- **Registre fonctionnel restant ouvert :** en dehors des tables comparées ici et au §17, le différentiel exhaustif des autres services, des sous-interfaces et des ABI NS2 (notamment `nvdrv`, `kernel/SVC`, `filesystem`, `loader`, `shader`, `GPU` et des variantes firmware) **n'est pas clos**. `230/230` ne signifie pas `100 % NS2`.



**Complément AoC ciblé (23/11, audit et qualification source) :** `headless/nup_v1_aoc_service.cpp` conservait **7 handlers à `nullptr`** dans le constructeur `IAddOnContentManager` alors que le propriétaire vendor `encore-active/eden-core/.../addon_content_manager.cpp` a des stubs explicites pour les IDs `9, 13, 110, 200, 300, 301, 302`. Les trois régions comparées hors pont NUP sont identiques au vendor épinglé ; les 7 entrées du constructeur ont été réalignées **sans toucher au comportement de Count/List/Base/Prepare**. C'est une correction de parité de dispatch, **pas** une implémentation fonctionnelle de ces commandes, encore moins une preuve de boot NS2.

### 18.3 Seuils de preuve et ordre du travail P0

1. Conserver les correctifs de fermeture FC27 et les traces NS2 sur `main` ; les deux tests historiques de provenance ont été réconciliés, CI vendor [45200615951](https://github.com/niakw/Prospero.Eden-Encore-vendor/actions/runs/45200615951) verte. L'état de la fermeture sur console reste **non prouvé**.
2. Pour MKW/Bananza, recouper le résultat CMIF/AM réel et la dernière SVC terminée avec l'entrée du processeur invité ; demander une preuve de transition à une **première soumission** avant d'importer des optimisations de texture/rendu qui présupposent déjà cette progression.
3. Pour Z-A, vérifier `EDEN_NS2_PROCESS_TRACE` : le correctif enregistre maintenant le PID NS2 des conteneurs acceptés, mais `active_pid=1` n'est qu'une trace diagnostique, pas un boot.
4. Pour Pokopia, examiner les valeurs de bornes NUP (taille de fichier déclarée, offset/longueur metadata, blob offset) et classer fichier tronqué, format incompatible ou parseur erroné ; ne jamais remplacer ce refus par une lecture hors limites.
5. N'intégrer un port Lichii/Eglantine qu'après diff de sa **source réellement sélectionnée**, de l'ABI PS5 et d'un test hôte pertinent ; puis qualification PS5. Aucune première frame MKW/Bananza/ZA ni gameplay NS2 certifiés par le présent audit.


---

## 19. Comparaison à trois propriétaires compilés — Lichii / EglantinePS5 / Encore (23 novembre 2026, complément)

**Références de comparaison :** Lichii `nx2:e7893bea` (après le correctif de fermeture #2502), EglantinePS5 `main:5eb70367`, Encore vendor `main:273680a5`. Les valeurs du tableau sont des **entrées de tables `FunctionInfo` observées dans les fichiers indiqués**, pas des implémentations complètes ni des commandes SwitchBrew additionnelles. Le moteur sélectionne ces propriétaires sur PS5 via `headless/CMakeLists.txt`, sans sélectionner ces remplacements pour les cibles non natives.

### 19.1 Comptage Lichii / Eglantine / Encore dans les propriétaires effectivement compilés

| Interface/fichier | Lichii | EglantinePS5 | Encore | Écarts démontrés |
| --- | ---: | ---: | ---: | --- |
| `am/service/application_functions.cpp` | 74 | 74 | 74 | Mêmes IDs. Encore a des noms/handlers spécifiques pour 210/320, qu'il ne faut pas écraser par des stubs plus anciens. |
| `hid/hid_server.cpp` | 235 | 235 | 235 | Mêmes IDs. Encore conserve SceneId, JCMS, Nmouse et vibration NS2 ; ces handlers ne doivent pas être rétrogradés en stubs Lichii/Eglantine. |
| `nifm/nifm.cpp` | 86 | 86 | 86 | Mêmes tables/IDs ; les 86 entrées ne sont pas 86 IDs distincts, car plusieurs interfaces les réutilisent. |
| `caps/caps_u.cpp` / `caps_su.cpp` | 18 / 5 | 18 / 5 | 18 / 5 | Aucun ID absent dans ces deux tables. |
| `set/settings_server.cpp` | 18 | 18 | 18 | Aucun ID absent. |
| `mii/mii.cpp` | 44 | 44 | 44 | Trois tables, mêmes IDs. |
| `lm/lm.cpp` | 10 | 10 | 10 | **Écart source corrigé** : ILogger cmd 2 `TransmitHashedLog` était `nullptr` chez Encore, stub explicite chez les deux amonts. |
| `audio/audio_device.cpp` / `audio_renderer_manager.cpp` | 22 / 5 | 22 / 5 | 22 / 5 | Aucun ID absent dans les tables sélectionnées. |
| `filesystem/fsp/fsp_srv.cpp` | 128 | 128 | 128 | **Parité des 128 IDs et noms/handlers dans la table.** Le fichier Encore compilé `encore-active/eden-backports/src/core/hle/service/filesystem/fsp/fsp_srv.cpp` est **identique à celui d'EglantinePS5** (blob Git `58303a0bd66387244c44968a0878e2f7c821bc9f`). |
| `acc/acc.cpp` | 25 tables | 24 tables | 24 tables | **12 entrées d'une table conditionnelle en plus chez Lichii** : `ScratchSystemAccount` et `GetScratchProfileManager`, absents des deux autres. Ne pas greffer ces commandes sans reprendre l'ownership du profil et prouver la non-régression NS1. |

Les comptes ACC précédemment affichés dans le §18 (502 / 490) utilisent un relevé textuel plus large ; la comparaison par blocs `FunctionInfo functions[]` strictement parsés donne **499 / 487** (Lichii / Encore) et exactement **12** entrées de différence. Ces chiffres désignent des méthodes de décompte différentes, **pas des fonctionnalités disparues**.

### 19.2 Backports réalisés sur `vendor/main`, sans remplacement des propriétaires NS1

1. **Lichii #2502 / AM WindowSystem** : un latch `m_exit_sent` empêche `WindowSystem::PruneTerminatedAppletsLocked()` de redemander `System::Exit()` après la première sortie. Source native sélectionnée : `encore-active/eden-core/src/core/hle/service/am/window_system.cpp` ; déclaration dans `sources/eden/src/core/hle/service/am/window_system.h`. Le `window_system.cpp` historique non natif est **inchangé**. Les tests [AM one-shot](https://github.com/niakw/Prospero.Eden-Encore-vendor/actions/runs/45224922997) valident deux sessions distinctes et la reconstitution exacte du précédent source PS5 hors latch, y compris le z-index des overlays NS1. Ce patch évite une répétition de la demande de fermeture ; **il n'établit pas que l'ancien crash NVDRV de FC27 est entièrement résolu sur console**.
2. **Lichii + EglantinePS5 / LM ILogger cmd 2** : l'entrée nulle `TransmitHashedLog` est remplacée par un handler explicite dans `encore-active/ns2-runtime/hle/core/hle/service/lm/lm.cpp`. Pour un titre classé NS2 par son ID de processus (`0x04...`), il renvoie le stub à **32 mots initialisés** via `StubReplyZeroed` ; pour NS1 ou un processus non identifié, il conserve **exactement le succès court à deux mots** que l'ancien `IsSafeOptionalNoOp` renvoyait. Pas de modification du dispatcher NS1 ni du protocole de `Log`/ `SetDestination`. [Test hôte LM](https://github.com/niakw/Prospero.Eden-Encore-vendor/actions/runs/45225294936) vert ; réponse IPC réelle console non encore observée.

### 19.3 Noyau/NPDM/GPU et particularités EglantinePS5

- **NPDM Switch 2** : les trois projets identifient le layout ACID étendu, mais le propriétaire Encore `encore-active/ns2-runtime/metadata/core/file_sys/program_metadata.cpp` utilise `FindAcidBody` avec validation des bornes et réinitialise `uses_extended_acid/is_switch2` au chargement. **Ne pas remplacer** par une version amont moins strictement bornée.
- **KProcess** : tous trois ont la majoration mémoire `GetHeapRegionSize() + GetAliasRegionSize()` pour `metadata.IsSwitch2()` ; Encore la garde strictement sous cette condition, sans ajouter de champ `m_is_switch2` à sa classe partagée. Eglantine ajoute ce champ : transplantation directe = **risque de divergence d'ABI NS1/NS2**.
- **SVC physical memory** : les trois sources exposent les variantes `MapPhysicalMemory`, `UnmapPhysicalMemory` et `Unsafe`, mais les corps/tailles et quelques chemins diffèrent. Le propriétaire compilé Encore est `encore-active/ns2-runtime/kernel/core/hle/kernel/svc/svc_physical_memory.cpp` ; aucun remplacement en bloc avant comparaison des contrats, codes retour et validation du comportement NS1.
- **Sémaphores GPU Eglantine** (port amont #1592) : `Puller::~Puller()` retire ses slots de `Nx2SemaphoreWaiters`. Encore compile son propre `encore-active/ns2-runtime/gpu_dispatch/video_core/engines/puller.cpp`, utilisant `PendingNativeAcquire` et des protections par génération/identité. Ces propriétaires ne sont **pas** interchangeables : risque d'accès libéré et de régression NS1 si copie brute.
- **Eglantine `EDEN_NX2_LIST_INDIRECT`** : option désactivée par défaut sur PS5 après mesure de régression d'environ 3–4 % sur Ocarina of Time. Fonction non requise pour la structure de démarrage Encore : pas de backport expérimental, conformément à l'objectif d'un seul cœur NS1/NS2 fonctionnel.
- **Lichii GPU/Vulkan** : soumissions aux frontières de render pass (#2481), cache de textures (#2485), économies Bananza ; aucune de ces optimisations n'est une preuve de résolution pour les sessions Encore qui n'atteignent pas la **première soumission GPU**.

### 19.4 Périmètre encore non certifié

La parité structurelle globale reste **ouverte** pour les ABI noyau/SVC (mapping des commandes, taille/alignement des entrées/sorties, erreurs), les opérations NVDRV et Ampere/Maxwell, le graphe des chargeurs/fichiers et les objets IPC/services non revus. Un tableau de commandes **complet en IDs** peut malgré tout avoir des réponses fonctionnellement différentes. La barrière P0 demeure : MKW/Bananza/Z-A doivent démontrer `gpu_submit_sample > 0` puis `guest_frame_handoff > 0` sur PS5 avant toute annonce de boot.

Le script hôte `tools/ns2/check-three-way-structural-baseline.py` épingle les preuves des **propriétaires locaux réellement sélectionnés**, pas l'intégralité des dépôts amont. Les références des trois dépôts restent fixées dans cet addendum : une nouvelle révision de Lichii ou Eglantine impose un nouveau différentiel et non une affirmation automatique de parité globale.


---

## 20. Revue complémentaire AM appletOE, NVDRV et SVC — comparaison triple

Périmètre **source** validé le 23 novembre 2026 : Lichii `nx2:e7893bea`, EglantinePS5 `main:5eb70367`, Encore vendor `main:273680a5`. Ce § distingue la correspondance de dispatch d'une preuve d'ABI et des essais console.

### 20.1 Interfaces AM de démarrage

| Source et interface | Lichii | Eglantine | Encore | Qualification |
| --- | ---: | ---: | ---: | --- |
| `IApplicationProxy` (15 `FunctionInfo`) | 15/15 | 15/15 | 15/15 | **IDs complets** ; commandes 40 et 60 volontairement plus spécifiques chez Encore. |
| `IApplicationProxyService` / `appletOE` (3 `FunctionInfo`) | 3/3 | 3/3 | 3/3 | **IDs complets** ; l'ABI de la commande 10 **diffère**. |
| `NVDRV` service `nvdrv.cpp` (3 tables `FunctionInfo`) | 22/22 | 22/22 | 22/22 | IDs, noms et handlers de déclaration concordent sur les trois dépôts ; ne prouve **aucune** parité des ioctl des périphériques. |

**Commandes AM dont le comportement diffère :**

- `IApplicationProxy cmd 40` : Lichii/Eglantine créent une interface générique `Nx2Getter40` ; Encore crée `IPerformanceFunctions` avec commandes `IsCpuOverclockEnabled` / `SetCpuOverclockEnabled` et état privé partagé `Ns2PerformanceRequest`. **Pas de changement du clock global à la demande du guest**, afin de garder les horloges NS1/NS2 stables.
- `IApplicationProxy cmd 60` : Lichii/Eglantine créent `IGraphicsScaleController`, Encore `IGraphicsScalingParametersFunctions`. Les deux interfaces ont les IDs enfants 10 et 1050, et la **réponse actuelle de la commande 10** est structurellement identique : trois `u32` valant `10, 0, 0`. Ce rapprochement du contenu ne prouve pas que tous les firmwares NS2 attendent le même nom ou la même taille dans toutes les variantes.
- `IApplicationProxyService cmd 10` : Lichii/Eglantine réutilisent directement `OpenApplicationProxy` comme cmd 0. Encore a un décodeur séparé `OpenApplicationProxyWithFlags`, qui lit le `u32 flags` additionnel (valeurs admises 0 ou 2) avant de déléguer. La réponse d'applet encore indisponible est un résultat de **retry AM 201** chez Encore plutôt que `ResultUnknown` en amont. **Ne pas écraser cet owner** sur la seule base des commandes numériquement identiques : le contrat HIPC de la commande 10 est un candidat P0 à qualifier par trace véritable.

### 20.2 SVC 32/64

Dans le `svc.cpp` généré des trois projets, exactement **123 noms `SvcId` distincts** sont présents, chacun en deux variantes de dispatch, soit **246 étiquettes `case SvcId::`**. La source PS5 Encore réellement compilée est `encore-active/ns2-runtime/gpu_access_svc/core/hle/kernel/svc.cpp` ; ses 123 noms correspondent à ceux de Lichii et Eglantine sans omission de *nom* dans les deux dispatchs. Les sources ne sont cependant **pas** identiques : Encore ajoute `SvcTrace`, la reconnaissance de l'accès GPU et des contrôles spécifiques à sa mémoire invitée.

**Limite impérative :** `123/123` est un résultat d'inventaire des dispatchs générés, pas une qualification des implémentations de chaque SVC, des registres argument/résultat A32/A64 ou des erreurs HOS. Ce compteur ne se combine pas au registre SwitchBrew des 316 commandes GPU.

### 20.3 Non-régression NS1 et priorité du boot

- Pas de remplacement en bloc de `Puller`, `svc.cpp`, `KProcess`, NPDM, `NVDRV`, `IApplicationProxy` ou `IApplicationProxyService` : les différences Encore ont des propriétaires et des contrats spécifiques. La conformité partielle aux références Lichii/Eglantine doit être prouvée méthode par méthode.
- Backports qualifiés : AM `m_exit_sent` et LM `TransmitHashedLog`, avec tests source/hôte NS1 et NS2. La comparaison des sources sélectionnées est couverte par le run [45226379447](https://github.com/niakw/ProsperoEden-Encore/actions/runs/45226379447) vert. Le cycle mémoire sparse par le run [45228287957](https://github.com/niakw/ProsperoEden-Encore/actions/runs/45228287957) vert. Les checks de provenance de vendor ont des listes de SHA exactes et des blobs scellés.
- **P0 console encore ouvert** : les dernières sessions MKW, Bananza, Z-A ne prouvent ni première soumission GPU, ni image invitée ; il faut relier `OpenApplicationProxy2` et le résultat AM/IPC, les SVC d'attente, les sessions GSV/NVDRV et le lancement du canal GPU dans un même journal. Ne pas attribuer un boot à la parité numérique ni aux CI hôtes.

### 24/11 — qualification comportementale du bootstrap (post-console)

Le relevé historique de 316 commandes reste inchangé comme photographie datée. Les deux lignes 1501/1502 (M) ont reçu un propriétaire de contexte dans vendor `3a32b5cd`, non encore validé console. La comparaison du **client** [libounce 32e7ac41, gsv.c](https://github.com/ouncebrew/libounce/blob/32e7ac414ee1cd98922f66a059be5a85e99feea5/nx/source/switch2/services/gsv.c#L108-L133) révèle une divergence additionnelle dans le bootstrap : `4 → 11 → 101 → 126 → [120 si mode 1] → 1501 → 1502`. Lichii `66c555ad` et EglantinePS5 `5eb70367` retournent le mode 0 pour 126. Vendor `d3038f8e2185c52ba615f983c51f5a49af0a0850` implémente la requête 126 sans entrée avec un résultat + un u32 mode 0, après authentification du contexte. Mode 1 et 120 restent non qualifiés, pas de succès générique. La commande 126 est additionnelle à la table SwitchBrew historique, donc ne pas l'ajouter au numérateur 316. Tests de protocole complétés, CI et PS5 à qualifier. Les autres refus opaques (dont 494, 801, 1503, 1601) ne sont pas présumés nécessaires au boot ni validés.

Suite de la comparaison : [libounce Syncpt](https://github.com/ouncebrew/libounce/blob/32e7ac414ee1cd98922f66a059be5a85e99feea5/nx/source/switch2/services/gsv.c#L450-L485) prouve que SyncptSession 21 reçoit un u32 (nombre de slots) après la requête de capacité 1. Le refus U du registre bloquait ce chemin entier. Vendor `9424fcd0c1d8ae189e5f9c65c63eebf09d9529e7` configure effectivement les slots, limite les opérations et interdit une réduction supprimant des événements vivants. Les SDK sans 21 conservent la limite historique. Contrat source/fixtures seulement, qualification PS5 ouverte.


GSV 204 : le miroir asynchrone conservait des adresses invitées mais pas les deux objets KTransferMemory acquis pendant l'IPC. Vendor `6d9ab07d0849889d1fb2a1ca775182a14aa2e6e0` retient désormais les deux objets jusqu'à destruction du dernier propriétaire asynchrone, annule la première acquisition si la seconde échoue, refuse l'alias du même objet et exige un bootstrap authentifié. Ce défaut de durée de vie est démontré au niveau source, pas encore sur console. Aucun changement NS1/FC27.


24/11 — Syncpt 103/201 : [libounce gsvSyncCheckNative](https://github.com/ouncebrew/libounce/blob/32e7ac414ee1cd98922f66a059be5a85e99feea5/nx/source/switch2/services/gsv.c#L630-L665) traite UINT64_MAX comme le producteur invalide/attente satisfaite. Encore retournait zéro pour un ID hors plage. Vendor `692e9819a7a1f1b818bf3739c72d8e5252cae661` corrige le retour et valide l'enveloppe 103/201. Le même correctif joint toute action encore en cours, même si son booléen pending est déjà faux, avant de réarmer le slot ; empêche le signal tardif d'une attente précédente. Comparaison du propriétaire Host1x actif et du code client, défaut source confirmé, validation console ouverte. Les comparaisons 64 bits et modulo du seuil restent à qualifier séparément.


24/11 — Syncpt 201 (suite) : libounce distingue comparaison modulaire signée 32 bits et seuil absolu 64 bits. Le handler Encore décodait le mode mais le perdait, et tronquait le seuil. Vendor `166e473e120a86a6edcd32a975ffe19b45ffdd42` conserve les deux modes dans les actions Host1x natives, incrémente un compteur natif 64 bits à partir des incréments réels, publie cette valeur dans GSV 103 et le miroir 204, joint les callbacks via les mécanismes existants. Les attentes historiques NS1 gardent leur comparaison et leur file ; le code partagé Host1x nécessite néanmoins une validation NS1. Tests hôtes étendus (seuil haut, modulo, annulation, coexistence). Console non qualifiée.


24/11 — GSV 202 : [libounce, gestion de session Syncpt](https://github.com/ouncebrew/libounce/blob/32e7ac414ee1cd98922f66a059be5a85e99feea5/nx/source/switch2/services/gsv.c#L434-L485) précise qu'une seule session est autorisée tant que le précédent enfant est vivant. Vendor `3522d8578fbcd7b46d2a439d5d718dfb570beb7b` impose l'authentification du bootstrap et conserve une référence faible de l'enfant publié en MOVE ; réouverture lorsque l'ancien serveur est réellement retiré, aucun propriétaire fort cyclique. Le résultat précis du firmware pour un doublon reste inconnu ; InvalidState utilisé sans prétendre à l'ABI exacte. Tests source, qualification console ouverte.


24/11 — Worker 212 / NVDRV changement de kind : libounce `gsvGpuChangeKind` envoie le kind pour un intervalle GPU existant. Le propriétaire CMake PS5 `eden-core/src/video_core/memory_manager.cpp` appelait `ModifyGPUMemory` uniquement sur changement d’état ou de page physique, alors que `kind_map` changeait aussi la disposition à backing identique. Le vendor `7e137d362f9679125726ef4876355a09d788795e` invalide l’ancien propriétaire TextureCache/BufferCache avant publication du nouveau kind (4K et grandes pages), conserve le no-op exact et protège l’écriture du kind 4K avec le verrou déjà employé pour les grandes pages. Test hôte existant étendu aux changements de kind seuls et à l’ordre ancien backing/ancien kind ; contrôle CI et PS5 encore requis. Le propriétaire est partagé NS1/NS2, donc non-régression NS1 à vérifier. Aucun lien causal avec l’écran noir NVN2 revendiqué.

24/11 — Worker 213/215, libération VA : [libounce](https://github.com/ouncebrew/libounce/blob/32e7ac414ee1cd98922f66a059be5a85e99feea5/nx/source/switch2/services/gsv.c) confirme la réponse Result seule pour 213 ; [Lichii e6a904dd](https://github.com/zortos293/Lichii/blob/e6a904dd4c4890cacea60789a1b04ed3e12e4cc6/src/core/hle/service/nx2_gsv.h) confirme l'ordre de complétion après travaux GPU. Le propriétaire CMake `nvdrv_as/.../nvhost_as_gpu.cpp` libérait le pin ou publiait le ledger sparse avant le `FlatAllocator::Free` (qui peut allouer lors d'une scission de bloc). Vendor `973d45ae0da5d9612d30900e39118d67d039b31a` place GMMU Unmap et Free dans la même phase protégée, avant retrait des pins et des ledgers. Échec de préparation 215 toujours retryable, échec pendant mutation mis en quarantaine InvalidState ; aucune notification de succès sur erreur. Modèle C++ local (propriétaires simulés) Clang/GCC O0/O2 UBSan réussi ; test hôte extrait étendu dans le contrôle existant, CI et console à confirmer. Chemins NS1 historiques non modifiés. Worker 211 cacheability reste à qualifier : bit décodé mais pas propagé au GMMU ; aucun effet matériel hôte démontré. Lichii documente aussi des mappings 211 dans des régions sparse, à confronter au contrat natif, sans reprendre ses succès inconditionnels.


24/11 — Worker 101/102/211 et durée de vie NVMap : le mapping d'identité ne peut libérer les pages invitées si son rollback est incertain (vendor `6b8fd06606f12be187f73e8809e56a49864794f9`). Les overlays 211 dans une réservation 214 non backée gardent un ledger distinct du VA, excluent les remaps physiques 216 et reviennent aux PTE sparse sur 213 (vendor `652f88555e8bb16ffeffd9d1fa3d0c49e7925dfc`). Cacheability est désormais conservée dans le propriétaire de mapping ; l'effet L2 matériel reste non implémenté. Références client : libounce `32e7ac4` et [OunceVK native map](https://github.com/ouncebrew/ouncevk/blob/main/src/nouveau/vulkan/nvkmd/nvgpu/nvkmd_nvgpu_native_map.c). Le destructeur ne libère plus les ressources après un drain GPU échoué ou un retrait d'identité incertain (vendor `881f6fb23c818ecfc387d2b134e1cd7328fc5995`). `NvMap::FreeHandleIfUnpinned` (vendor `d8155325107dbbb1f8ef44f75553595fe4c8ec8c`, moteur `57dd29b8738a260e1f60a03c06c58172bd0b4f4d`) impose atomiquement sous le mutex du handle une seule référence utilisateur, aucun duplicata interne ni pin, marque le handle retiré avant mutation et interdit le re-pin/dupe tardif. Worker 102, teardown et dense 214 utilisent ce chemin ; la voie FreeHandle historique conserve sa politique. Une mutation destructrice échouée conserve la session en quarantaine. Témoin C++ extrait à l'identique du bloc FreeHandle (backend simulé) : Clang/GCC O0/O2 UBSan local réussi, mêmes scénarios intégrés au test hôte existant. CI du couple exact à terminer, [build natif ignoré](https://github.com/niakw/ProsperoEden-Encore/actions/runs/45434772246). MKW/Bananza : première soumission et image invitée toujours non démontrées. Contrats restants : rollback VA lors d'une OOM du FlatAllocator sur 211, fin de vie AS importé et propagation réelle des fautes H:17 ; GSV 1411 non mesuré, USERD/doorbell non qualifié. Aucun travail FC27 engagé dans ce lot.

24/11 — GSV 1401/1411 et attente GPFIFO : [SwitchBrew GSV](https://switchbrew.org/wiki/Switch_2%3A_GSV_services) documente 1401 (donation TransferMemory) et 1411 (trois u64). Vendor `101eae5edb76fefc40b039009eb35bbaaae99386`, moteur `82a1759556ed4bc0fe1762901378d26de67215db` : le vrai enfant NVDRV retient la donation jusqu'à sa destruction ; 1411 rapporte la capacité de la donation vivante. Le backend HLE ne sous-alloue pas dans cette donation : used/peak sont zéro dans ce modèle, non une mesure de toute la consommation NVDRV ni une preuve de parité firmware. La session distante 1402 ne possède pas cette donation. Le [contrôle du graphe source](https://github.com/niakw/ProsperoEden-Encore/actions/runs/45437287652) est vert sur ce couple.

Vendor `3abd88bc1a3c334f53f345998b72e9cf8ae87abf`, moteur `503cee8ebe4495b2fc74dc781b8e9e89f605aa5c` : le vrai SubmitGPFIFOImpl n'écarte plus une attente NVDRV FENCE_WAIT non satisfaite ; le CommandList reçoit une dépendance host-only, authentifiée avant mutation du canal. Le DmaPusher et le scheduler natif existant suspendent uniquement ce canal jusqu'au compteur Host1x **hôte**, incrémenté après la retraite réelle des fences, sans utiliser le compteur invité anticipé. Le pool NVDRV invalide le jeton de génération avant réattribution du syncpoint ; le pusher refuse une dépendance retirée, y compris un retrait pendant lecture du compteur. Le chemin Maxwell conserve son paquet historique ; FENCE_ACTION natif brut reste non implémenté. Tests hôte existants étendus (allocation du jeton, attente, wrap, invalidation, non-régression admission NS1) et syntaxe du vrai owner prévue. [CI preflight](https://github.com/niakw/ProsperoEden-Encore/actions/runs/45439505422) encore en cours à la rédaction ; [build PS5 ignoré](https://github.com/niakw/ProsperoEden-Encore/actions/runs/45439505563). Pas de première soumission/frame PS5 démontrée. Restent notamment rollback VA 211, cycle AS importé, H:17, USERD/doorbell, cacheability L2 et validation réelle du bootstrap. Aucun chantier FC27 démarré.

24/11 — Import VM et révocation GSV : vendor `06705357e48b33d837b1f97dbb1c3979cb3d7c31`, moteur `9e454b35a2c4009cd893434fa2758b097c3e35de` (gitlink vérifié). L'AS_IMPORT publiait l'ID NVDRV après le retour du propriétaire GSV ; une destruction intercalée pouvait ignorer RetireNativeVm. Le propriétaire actif `gpu_worker_shared.cpp` appelle maintenant CommitNativeVmImport sous son mutex, après le replay d'identité, et `nvhost_as_gpu.cpp` ne réécrit plus l'ID après publication. Les deux tests source existants sont adaptés ; le témoin H06 extrait Import/Commit/Retire/Epoch et simule une révocation avant le retour du binding (exécution CI à confirmer). Référence client : [libounce GSV](https://github.com/ouncebrew/libounce/blob/main/nx/source/switch2/services/gsv.c) (création et enregistrement VM distincts) ; [OunceVK channel setup](https://github.com/ouncebrew/ouncevk/blob/main/src/nouveau/vulkan/nvkmd/nvgpu/nvkmd_nvgpu_native_channel_setup.c) / [submit](https://github.com/ouncebrew/ouncevk/blob/main/src/nouveau/vulkan/nvkmd/nvgpu/nvkmd_nvgpu_native_submit.c) utilisent H:1a puis H:1b Ioctl2, sans dépendance USERD/doorbell démontrée sur ce parcours. USERD reste ouvert pour les clients qui l'exigent ; ne pas inférer le chemin NVN des jeux commerciaux à partir d'OunceVK seul. Les deux contrôles de provenance rouges sur le précédent moteur ont été adaptés par reconstruction exacte des trois blobs antérieurs aux ajouts NS2 (pas de désactivation ni rollback runtime). [Sparse R457](https://github.com/niakw/ProsperoEden-Encore/actions/runs/45452081648) vert et [build natif ignoré](https://github.com/niakw/ProsperoEden-Encore/actions/runs/45452081340) ; [fast gate](https://github.com/niakw/ProsperoEden-Encore/actions/runs/45452081348) et [vendor pin](https://github.com/niakw/ProsperoEden-Encore/actions/runs/45452081290) en cours à cette écriture. Aucun test PS5, aucune première frame ni amélioration FC27 revendiquée.


24/11 — Admission GPFIFO après mutation GMMU incertaine : vendor `19a406a53bf4adb114bb33cb21ea8a42e655ea9c`. Les chemins de rollback 211/214/215/216 mettent déjà l'AS en quarantaine via native_sparse_poisoned, mais NativeSubmissionAllowed ne vérifiait que la révocation et l'époque du processus. Le propriétaire CMake nvdrv_as utilise maintenant un drapeau atomique et refuse les nouvelles admissions natives sur AS empoisonné ; aucune modification du chemin de soumission Maxwell NS1. Référence de principe : [NVIDIA UVM non-replayable faults](https://github.com/NVIDIA/open-gpu-kernel-modules/blob/main/kernel-open/nvidia-uvm/uvm_gpu_non_replayable_faults.c), qui retire le canal lors d'une faute fatale ; pas de transposition d'ABI. Le témoin H06 extrait le vrai prédicat et couvre AS sain, empoisonné et révoqué. CI à exécuter ; les commandes déjà admises et la notification asynchrone H:17 restent à qualifier. Aucun build PS5 ni gain console revendiqué.


24/11 — GPFIFO déjà admis / faute GMMU / H:17 : vendor `cd5ce4dabef1d32e0441d22dccdee358ebf23287` (runtime `ac60dbdb` + `29e32a0a` + `412dadea` + `d13311b3`, gardes G10/H:17 jusqu'à `cd5ce4da`). Le submit natif capture désormais un jeton de santé de l'espace GPU et l'attache au payload ainsi qu'aux paquets de complétion ; les 17 chemins de quarantaine GMMU et la révocation VM invalident ce jeton. Le DmaPusher refuse le travail déjà en file avant lecture, après attente et pendant le dispatch ; la validité du paquet ne dépend plus de `IsNative()`, qui devient volontairement faux après révocation GSV. Sur faute, le worker enregistre d'abord la cause GPU fatale puis signale l'événement erreur du canal via le registre de génération, avec sérialisation contre Unbind/destruction. Le même chemin couvre désormais les attentes syncpoint retirées/recyclées, curseur de préfetch invalide, fetch GMMU disparu, entrée raccourcie et subchannel natif non lié. Le Puller actif a été traité en famille : SET_OBJECT/fence-action, sémaphores Ampere, MME 3D/Compute, inline QMD, report semaphore, QMD3 et payload Compute synchrones utilisent tous FailNativeSubmission ; les trois fautes de backing différées restent confinées dans leurs callbacks Vulkan, qui enregistrent la cause puis réveillent H:17 sur le ChannelState capturé. Référence client ciblée : OunceVK ouvre `nvQueryEvent(fd, 7)` puis installe le notifier `0xC018480C`; le signal n'est donc pas conditionné au contrôle d'événement ID3. Les tests source existants ont été adaptés sans relâcher les propriétaires C++ et la provenance scelle le tree vendor exact. Build PS5 volontairement ignoré ; première soumission et première frame MKW/Bananza toujours non validées sur console.


24/11 — ABI strict completion dans les propriétaires CMake réellement sélectionnés : moteur `5f6fffe1` ajoute SignalNativeSyncPoint au rasterizer shutdown et au fence manager failure-aware (fence non stub, retraite hôte en callback, propagation de panne). Lot GPFIFO/H:17 : corrections intégrées ; qualification CI du couple final et premier submit/frame console restent ouverts. Les logs ee5d6d57 montrent un blocage avant le premier submit, donc ne prouvent pas que H:17 débloque MKW/Bananza.

24/11 — **Cause du dernier P0 NS2 avant soumission GPU, prouvée par provenance du binaire.** Dernier test PS5 `ee5d6d57d7d433b8406d1411d348ca60d304e2eb` → gitlink vendor **`d634b381d85dae30492dd6291fc4e6e96143f363`**, antérieur au correctif de GSV. **Bananza `040074A01BF12000` et MKW `0400C3F00006E000`** exécutent effectivement `IGraphicsSupervisor` TIPC **4 → 11 → 101 → 1501**, puis `IApplicationFunctions` 22 (`SetTerminateResult(0x4201)`) et `svcBreak` sans aucune soumission GPU invitée. La source *exacte du vendor testé* route `1501/1502` sur `UnavailableDocumentedFeature` : `ResultNotImplemented` 0x4201, tandis que le vendor **`3a32b5cda47014d0942f8d4625afa4651dc95a5f` du même jour à 11:31 UTC**, postérieur au build testé (10:45 UTC), route `1501/1502` vers `InitializeInterModuleImageContext` avec vérification du bootstrap `4/11/101`. Le HEAD vendor conserve ce correctif et le reçu `tests/ns2_syncpt_bootstrap_source.py`. Référence Lichii `nx2` : `src/core/hle/service/nx2_gsv.h`, `1501/1502` contrôles de permission. **Statut : cause historique 0x4201 sur GSV 1501 corrigée dans le C++ actif, non requalifiée sur PS5** ; ni première soumission ni première frame démontrées. Ne pas attribuer ce refus ancien aux GMMU/MaxwellDMA ou remplacer `GetInfo31/32` par de la mémoire physique fictive. Le test console suivant doit utiliser le couple SHA exact actuel et constater le passage après 1501, puis seulement évaluer les blocages suivants.

26/11 — **P0 NUP NS2 Edition (Pokémon Z-A, `0100F43008C44000`) : priorité du programme embarqué**. Les dernières traces identifient un NPDM NS1 / chemin GPU legacy, sans première frame ; elles ne démontrent pas le contenu exact du NUP. Différence source vérifiée contre `zortos293/Lichii` `nx2`, `NupContainer::SelectProgram` : quand un NUP de mise à jour autonome NS1 comporte à la fois un ExeFS ordinaire complet et `program1/exefs` NS2, Encore choisissait l’ExeFS NS1 avant même de vérifier l’édition NS2. Le correctif du moteur `main` (fichier `headless/nup_v1_native_content.cpp`) examine désormais `program1` en premier **seulement** si la mise à jour la plus récente est autonome, sans base, et si le NPDM du programme embarqué atteste Switch 2, le Title ID dérivé exact et le programme index 1. La sélection NS1 par défaut et les refus de NPDM non concordant restent inchangés. Le RomFS natif est superposé à la vue ordinaire via `LayeredVfsDirectory` (priorité native, fichiers partagés conservés) et non via l’argument extension IPS de `CreateRomFS`. Vendor gitlink `aece4f82a123a7bd1f4046237a82a0faecbee450` inchangé. Contrôle syntaxe/ABI contre header vendor exact et archive synthétique double ExeFS/ROMFS existante étendus ; CI et console restent à qualifier. **Aucun chargement ni première frame Z-A revendiqué**, aucune build PS5 lancée.

26/11 — Complément NUP édition NS2 : `ContentSet` refusait les addons de la mise à jour NS1 lorsque le NPDM sélectionné était le programme `04...` NS2 ; le même fichier actif conserve désormais la famille AoC NS1 uniquement si l'identifiant du `program1` embarqué a été validé byte-à-byte par `ProgramMetadata`. Une archive synthétique contenant l'ExeFS legacy, le programme1 NS2 et un AoC NS1 vérifie la priorité, le RomFS et l'isolement des Title IDs étrangers. Sans nouvelle compilation native ni qualification du contenu réel Pokémon Z-A.

26/11 — **ExeFS NS2 extrait : révision atomique sélectionnée**. L'inspection du vrai propriétaire CMake `vendor/encore-active/ns2-runtime/metadata/core/loader/deconstructed_rom_directory.cpp` a révélé un mélange possible de modules entre `base/exefs` et `updates/<version>/exefs` : `LayeredVfsDirectory({patch_exefs, dir})` prendrait `main` d'une mise à jour mais `main.npdm`, `rtld` ou `sdk` de la base si manquants. Vendor `45952eb648e7eb3502b517c06b3032edd3a9035a` exige maintenant `main` et `main.npdm` dans la mise à jour sélectionnée et charge **son seul ExeFS** ; refus explicite d'une révision incomplète plutôt qu'une composition de versions. `romfs` continue d'être superposé indépendamment ; NUP et NS1 ne sont pas modifiés. Source comparable : `Lichii nx2` `NupContainer::SelectProgram` (sélection d'un répertoire exefs complet). La source contractuelle vendor existante couvre la nouvelle règle. **Le PC=0x4 Bananza/MKW dans les anciens logs reste sans cause console prouvée**, et Eglantine #350 a attribué un cas similaire à une ancienne version de dump : ne pas considérer ce patch comme un déblocage de jeu sans premier draw/frame validé. CI et build natif PS5 non encore qualifiés pour cette révision.

26/11 — **NUP NS2 Edition : publication AoC jusqu'au service invité**. Défaut source confirmé : `ContentSet` n'admettait la famille AoC NS1 que pour `program1` d'une mise à jour autonome ; `AddOnIndex` rejetait ensuite même ce cas à cause de la différence des préfixes 01/04 et recalculait la base AoC à partir du programme NS2. Correctifs moteur `805a29885db7dcbaff73485cd138b1bb9e2a9064` et `3a8d41298abcd53cfd2b85f9d98b9ef25cc8d502` : admission de la base NS1 + édition NS2 seulement après validation du NPDM sélectionné et du programme exact, partage de la base AoC admise avec `AddOnIndex`, refus des familles étrangères et conservation du NACP explicite. `headless/nup_v1_runtime.cmake` sélectionne les deux unités dans `core`. Comparaison `Lichii nx2`, `NupContainer::SelectProgram` / `FindUpgradePack`, et commit upstream `31b3ac211296819384c01ed64f11a34fb62f28ac`. Extension de la suite hôte existante (`707e1d72533cbf15ae9d299d0174805cb524d5fb`, `c280e6c78f4a102fe6b704d4a5d5780c07021d12`) : deux formats d'édition, ID exact, `BaseId`, `Count`, accès RomFS AoC, refus des callers étrangers. Vendor épinglé inchangé `45952eb648e7eb3502b517c06b3032edd3a9035a`. Tests ajoutés mais exécution hôte/CI non confirmée ; aucune compilation PS5 déclenchée. L'écart source n'est pas une preuve de causalité du chargement infini de Z-A ou Pokopia, ni d'une première soumission GPU.
