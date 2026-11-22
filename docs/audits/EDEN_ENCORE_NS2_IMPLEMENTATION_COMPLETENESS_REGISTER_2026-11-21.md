# Eden Encore — registre de complétude d’implémentation NS2 / SwitchBrew (21 novembre 2026)

> **Nature** : registre vivant de couverture **statique et hôte** pour Nintendo Switch 2. Il reprend les commandes publiées par SwitchBrew et les compare au C++ réellement sélectionné par Eden Encore. Une ligne manquante n’est **pas** automatiquement un bug de Mario Kart World ou Donkey Kong Bananza ; une ligne implémentée n’est **pas** une preuve console.

**Issue maîtresse NS2 : [#123](https://github.com/niakw/ProsperoEden-Encore/issues/123).**
**Référence historique complémentaire : [analyse des écarts NS2 puis NS1 du 20/11](./EDEN_ENCORE_GAP_ANALYSIS_NS2_THEN_NS1_2026-11-20.md).**

## 0. Provenance et règle de mise à jour

| Élément | Révision / source |
| --- | --- |
| Moteur `main` à la création de ce registre | `a59cae85eb1dd7246f5648b46e6fddceb736a5a6` |
| Vendor gitlink sélectionné après intégration | `224b05e6f8b1a266b0d55d1ded5332f7a2eaed7c` |
| Moteur `main` avant intégration de cette branche | `814bc29918df3c1fc207229537c7d80dfa8c8891` |
| Vendor `main` fusionné + test de qualification | `224b05e6f8b1a266b0d55d1ded5332f7a2eaed7c` |
| Vendor `main` à la création | `546e1aa34d2ff183dd4c737f9da8fbf4a62be24e` |
| SwitchBrew GSV | https://www.switchbrew.org/wiki/Switch_2%3A_GSV_services — consultation 2026-11-21 |
| SwitchBrew NV services | https://www.switchbrew.org/wiki/NV_services — consultation 2026-11-21 |
| Client SDK recroisé | https://github.com/vexcited/fefw — notamment `src/nn/gpu/gpu_sdk_*.cpp` |
| Validation console du présent couple | **Aucune** : pas de build PS5, pas de première soumission/frame revendiquée |

**Codes** : **C** = implémentation C++ active et cohérente au niveau source/CI hôte ; **P** = partielle, contrat fusionné ou divergence ABI/nomenclature à revoir ; **M** = fonctionnalité non implémentée, que le dispatcher ait un refus/stub explicite ou aucun handler renseigné ; **U** = ID connu mais nom/ABI/sémantique publique insuffisante ; **V** = variante de version non couverte intentionnellement tant que le firmware invité cible ne la requiert pas.
**Tous les C/P restent console-non-qualifiés** tant qu’un build PS5 représentatif ne les a pas exercés.

**Colonnes séparées pour chaque commande (§1–§12)** : F = comportement de la commande elle-même ; R = dispatch. Les deux lecteurs d'erreur H:0x16/H:0x17 sont C : ils exposent correctement le snapshot courant. **Le manque d'un producteur de faute GPU réel reste un blocage transversal distinct** et ne doit plus maintenir artificiellement les lecteurs en P.

### Politique des fonctions connues mais non implémentées

Une commande connue peut recevoir un **handler nommé** afin que la couverture soit explicite, avec un commentaire du type `// not implemented yet on Encore`, **mais elle ne doit jamais retourner un faux `Success`**. Tant que son effet réel n’est pas implémenté, elle doit répondre `NotImplemented`, `InvalidState` ou une erreur plus précise adaptée au contrat. Les commandes dont même le format d’entrée est inconnu restent sans lecture de payload plutôt que de deviner une ABI.

**Mise à jour fail-closed NVHOST (21/11)** : le vendor `f65ccc43` conserve l’ouverture des nodes `/dev/nvhost-*` inconnus nécessaire à la découverte NVN, mais leur fallback générique ne fabrique plus de sortie zéro/copiée ni de `Success`. Toute ioctl non couverte retourne désormais explicitement `NotImplemented` avec le marqueur `// not implemented yet on Encore`. Les handlers TSG authentifiés `BIND_CHANNEL`, `UNBIND_CHANNEL` et `BIND_CHANNEL_EX` restent actifs. **Aucune qualification PS5 n’est revendiquée.**

### Double compteur : couverture fonctionnelle et représentation explicite (22/11/2026)

> Périmètre **316 commandes NS2**. Couverture source ≠ build PS5 ≠ validation console.

- **F** : **C=174**, **P=3**, M=108, U=25, V=6.
- **R** : **316/316** disposent d'un dispatch explicite ou d'un refus/stub identifié.

| Statut fonctionnel | Total | Traitement indiqué | Sans traitement |
| --- | ---: | ---: | ---: |
| C — implémentation source | **174** | 174 | 0 |
| P — partielle | **3** | 3 | 0 |
| M — non implémenté | 108 | 108 | 0 |
| U — contrat insuffisant | 25 | 25 | 0 |
| V — ancienne variante firmware | 6 | 6 | 0 |
| **Total** | **316** | **316** | **0** |

**Lecteurs d'erreur qualifiés C** : H:0x16 copie la structure 128 B du snapshot courant ; H:0x17 copie la structure 16 B et force le status Switch `0xFFFF`. Les deux vérifient ABI native, owner et initialisation du notifier. **Ouvert séparément** : aucun producteur GPU ne remplit encore ces snapshots ni ne signale l'événement en cas de faute matérielle/émulée réelle.

**Restent 3 P** : CHANNEL_SETUP_BIND userspace USERD/doorbell, SET_RUNLIST_INTERLEAVE post-bind et SET_TIMESLICE post-bind.

**Statut de clôture de la branche** : le chantier demandé « traiter toute entrée non-C » est **terminé au sens dispatch/runtime borné** : aucune des 316 entrées n'est sans comportement explicite. Les trois P ne sont pas des oublis : leur chemin supporté fonctionne, et leur sous-mode non supporté retourne explicitement `NotImplemented` plutôt qu'un faux succès. Ils ne peuvent passer C complet sans ajouter respectivement (1) USERD + doorbell + mappings utilisateurs réels, (2) rechargement/preemption de runlist après bind pour interleave, (3) application de timeslice au scheduler après bind. Ces trois capacités ne sont pas simulées.

---

## 1. UserSession GSV — liste SwitchBrew complète

État courant de la table (22/11, branche de couverture) : 142 commandes recensées ; C=55, P=0, M=70, U=17. État initial historique du 21/11 : C=27, P=26, M=72, U=17. Les divergences de nom sont volontairement visibles : elles signalent les endroits où la simple présence d’un handler ne suffit pas.

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
| 311 | Display | (nom inconnu) | U | REFUS GÉNÉRIQUE EXPLICITE | IGraphicsSupervisor::HandleSyncRequest fallback | ID connu sans contrat public suffisant ; ID absent de la table spécifique, fallback TIPC actif → ResultNotImplemented sans décoder de payload inconnu |
| 312 | Display | (nom inconnu) | U | REFUS GÉNÉRIQUE EXPLICITE | IGraphicsSupervisor::HandleSyncRequest fallback | ID connu sans contrat public suffisant ; ID absent de la table spécifique, fallback TIPC actif → ResultNotImplemented sans décoder de payload inconnu |
| 314 | Display | (nom inconnu) | C | HANDLER INDIQUÉ | ConfigureNativeWindowImagePool | Lichii : 314(first image) ; Encore retire exactement le groupe enregistré par 315, sans inférer la longueur depuis des IDs adjacents |
| 315 | Display | (nom inconnu) | C | HANDLER INDIQUÉ | ConfigureNativeWindowImagePool | Lichii : 315(first image,count) ; Encore mémorise le groupe exact, valide tous les IDs avant publication et marque chaque image alias |
| 321 | Display | (nom inconnu) | U | REFUS GÉNÉRIQUE EXPLICITE | IGraphicsSupervisor::HandleSyncRequest fallback | pas de handler / contrat insuffisant ; ID absent de la table spécifique, fallback TIPC actif → ResultNotImplemented sans décoder de payload inconnu |
| 327 | Display | (nom inconnu) | U | REFUS GÉNÉRIQUE EXPLICITE | IGraphicsSupervisor::HandleSyncRequest fallback | pas de handler / contrat insuffisant ; ID absent de la table spécifique, fallback TIPC actif → ResultNotImplemented sans décoder de payload inconnu |
| 361 | Display | (nom inconnu) | U | REFUS GÉNÉRIQUE EXPLICITE | IGraphicsSupervisor::HandleSyncRequest fallback | pas de handler / contrat insuffisant ; ID absent de la table spécifique, fallback TIPC actif → ResultNotImplemented sans décoder de payload inconnu |
| 391 | Display | CalculateRequiredBufferMemory | C | HANDLER INDIQUÉ | CalculateFeatureImagePoolRequirements | Lichii common feature-image template: preference[16]+count → u64 size/alignment; formats 1/4/5 + observed MKW 0x38, no image creation side effect |
| 401 | Gpu | CreateGpuContext | C | HANDLER INDIQUÉ | InitializeGpuContext | actif; création état GPU |
| 402 | Gpu | InitializeGpuContext | C | HANDLER INDIQUÉ | ActivateGpuContext | actif |
| 403 | Gpu | DestroyGpuContext | C | HANDLER INDIQUÉ | DestroyGpuContext | actif |
| 423 | Gpu | (nom public incomplet) | C | HANDLER INDIQUÉ | BindNativeGpuMemory | Ounce/fefw envoie raw `0x1B7` (TIPC 423) pour le bind enfant NativeMemory → parent GPU/NVMap; ownership, adresse, taille et offset sont validés |
| 424 | Gpu | (nom inconnu) | U | REFUS GÉNÉRIQUE EXPLICITE | IGraphicsSupervisor::HandleSyncRequest fallback | pas de handler / contrat public incomplet ; ID absent de la table spécifique, fallback TIPC actif → ResultNotImplemented sans décoder de payload inconnu |
| 425 | Gpu | (nom inconnu) | U | REFUS GÉNÉRIQUE EXPLICITE | IGraphicsSupervisor::HandleSyncRequest fallback | pas de handler / contrat public incomplet ; ID absent de la table spécifique, fallback TIPC actif → ResultNotImplemented sans décoder de payload inconnu |
| 426 | Gpu | MapNativeImage | C | HANDLER INDIQUÉ | MapNativeGpuImage | actif |
| 427 | Gpu | UnmapNativeImage | C | HANDLER INDIQUÉ | UnmapNativeGpuImage | actif |
| 428 | Gpu | QueryNativeImage | C | HANDLER INDIQUÉ | QueryNativeGpuImage | actif |
| 429 | Gpu | CreateNativeImage | C | HANDLER INDIQUÉ | CreateNativeImage | actif |
| 430 | Gpu | DestroyNativeImage | C | HANDLER INDIQUÉ | DestroyNativeImage | actif |
| 434 | Gpu | ExistsAddressSpace (nom public) | C | HANDLER INDIQUÉ | RegisterGpuAddressSpace | Ounce/fefw envoie raw `0x1C2` avec un seul AS fd et attend un résultat; Encore enregistre exactement l'AS possédé par le process |
| 435 | Gpu | CalculateNativeImageSize | C | HANDLER INDIQUÉ | CalculateNativeImageSize | actif |
| 437 | Gpu | CreateNativeMemoryWithGpukMemHandle | U | REFUS GÉNÉRIQUE EXPLICITE | IGraphicsSupervisor::HandleSyncRequest fallback | nom/ID public connu, mais l'implémentation Ounce observée utilise raw `0x1B7` → TIPC 423; aucun contrat raw `0x1C5` prouvé, donc pas de doublon inventé ; ID absent de la table spécifique, fallback TIPC actif → ResultNotImplemented sans décoder de payload inconnu |
| 493 | Gpu | CreateUserlandDebuggerSession | M | STUB NOMMÉ | UnavailableDocumentedFeature | pas de handler; debug non P0 ; handler TIPC explicite, NotImplemented sans objet ni handle (non fonctionnel) |
| 494 | Gpu | (nom inconnu) | U | REFUS GÉNÉRIQUE EXPLICITE | IGraphicsSupervisor::HandleSyncRequest fallback | pas de handler / contrat insuffisant ; ID absent de la table spécifique, fallback TIPC actif → ResultNotImplemented sans décoder de payload inconnu |
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
| 903 | VideoDecoder | DestroyVideoDecoderContext | M | STUB NOMMÉ | UnavailableDocumentedFeature | pas de handler UserSession ; handler TIPC explicite, NotImplemented sans objet ni handle (non fonctionnel) |
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
| 1091 | VideoEncoder | (nom inconnu) | U | REFUS GÉNÉRIQUE EXPLICITE | IGraphicsSupervisor::HandleSyncRequest fallback | ID connu sans contrat public suffisant ; ID absent de la table spécifique, fallback TIPC actif → ResultNotImplemented sans décoder de payload inconnu |
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
| 1601 |  | (nom inconnu) | U | REFUS GÉNÉRIQUE EXPLICITE | IGraphicsSupervisor::HandleSyncRequest fallback | ID connu sans documentation suffisante ; ID absent de la table spécifique, fallback TIPC actif → ResultNotImplemented sans décoder de payload inconnu |
| 1602 |  | (nom inconnu) | U | REFUS GÉNÉRIQUE EXPLICITE | IGraphicsSupervisor::HandleSyncRequest fallback | ID connu sans documentation suffisante ; ID absent de la table spécifique, fallback TIPC actif → ResultNotImplemented sans décoder de payload inconnu |
| 1603 |  | (nom inconnu) | U | REFUS GÉNÉRIQUE EXPLICITE | IGraphicsSupervisor::HandleSyncRequest fallback | ID connu sans documentation suffisante ; ID absent de la table spécifique, fallback TIPC actif → ResultNotImplemented sans décoder de payload inconnu |
| 1611 |  | (nom inconnu) | U | REFUS GÉNÉRIQUE EXPLICITE | IGraphicsSupervisor::HandleSyncRequest fallback | ID connu sans documentation suffisante ; ID absent de la table spécifique, fallback TIPC actif → ResultNotImplemented sans décoder de payload inconnu |
| 1612 |  | (nom inconnu) | U | REFUS GÉNÉRIQUE EXPLICITE | IGraphicsSupervisor::HandleSyncRequest fallback | ID connu sans documentation suffisante ; ID absent de la table spécifique, fallback TIPC actif → ResultNotImplemented sans décoder de payload inconnu |
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
| 13 | (SwitchBrew non nommé) | U | REFUS GÉNÉRIQUE EXPLICITE | IVi2Session::HandleSyncRequest fallback | pas de handler et sémantique publique insuffisante ; ID absent de la table spécifique, fallback TIPC actif → ResultNotImplemented sans décoder de payload inconnu |
| 21 | (SwitchBrew non nommé) | C | HANDLER INDIQUÉ | GetNotifications | handler sélectionné; console non qualifiée |
| 31 | (SwitchBrew non nommé) | C | HANDLER INDIQUÉ | GetVsyncEvent | handler sélectionné; console non qualifiée |
| 32 | (SwitchBrew non nommé) | C | HANDLER INDIQUÉ | GetDisplayVsyncEvent | handler sélectionné; console non qualifiée |
| 51 | (SwitchBrew non nommé) | C | HANDLER INDIQUÉ | ConfigureRequestGroups | handler sélectionné; console non qualifiée |
| 53 | (SwitchBrew non nommé) | U | REFUS GÉNÉRIQUE EXPLICITE | IVi2Session::HandleSyncRequest fallback | pas de handler et sémantique publique insuffisante ; ID absent de la table spécifique, fallback TIPC actif → ResultNotImplemented sans décoder de payload inconnu |
| 101 | (SwitchBrew non nommé) | C | HANDLER INDIQUÉ | OpenDisplay | handler sélectionné; console non qualifiée |
| 102 | (SwitchBrew non nommé) | C | HANDLER INDIQUÉ | CloseDisplay | handler sélectionné; console non qualifiée |
| 103 | (SwitchBrew non nommé) | C | HANDLER INDIQUÉ | QueryDisplayRefreshRate | handler sélectionné; console non qualifiée |
| 104 | (SwitchBrew non nommé) | C | HANDLER INDIQUÉ | QueryDisplayHdrStatus | handler sélectionné; console non qualifiée |
| 105 | (SwitchBrew non nommé) | C | HANDLER INDIQUÉ | QueryDisplayHdrPaperWhite | handler sélectionné; console non qualifiée |
| 106 | (SwitchBrew non nommé) | C | HANDLER INDIQUÉ | GetBufferMaxResolution | handler sélectionné; console non qualifiée |
| 107 | (SwitchBrew non nommé) | U | REFUS GÉNÉRIQUE EXPLICITE | IVi2Session::HandleSyncRequest fallback | pas de handler et sémantique publique insuffisante ; ID absent de la table spécifique, fallback TIPC actif → ResultNotImplemented sans décoder de payload inconnu |
| 111 | (SwitchBrew non nommé) | C | HANDLER INDIQUÉ | OpenEndpoint | handler sélectionné; console non qualifiée |
| 112 | (SwitchBrew non nommé) | C | HANDLER INDIQUÉ | CloseEndpoint | handler sélectionné; console non qualifiée |
| 113 | (SwitchBrew non nommé) | U | REFUS GÉNÉRIQUE EXPLICITE | IVi2Session::HandleSyncRequest fallback | pas de handler et sémantique publique insuffisante ; ID absent de la table spécifique, fallback TIPC actif → ResultNotImplemented sans décoder de payload inconnu |
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
| 301 | (SwitchBrew non nommé) | U | REFUS GÉNÉRIQUE EXPLICITE | IVi2Session::HandleSyncRequest fallback | pas de handler et sémantique publique insuffisante ; ID absent de la table spécifique, fallback TIPC actif → ResultNotImplemented sans décoder de payload inconnu |
| 302 | (SwitchBrew non nommé) | U | REFUS GÉNÉRIQUE EXPLICITE | IVi2Session::HandleSyncRequest fallback | pas de handler et sémantique publique insuffisante ; ID absent de la table spécifique, fallback TIPC actif → ResultNotImplemented sans décoder de payload inconnu |
| 351 | (SwitchBrew non nommé) | C | HANDLER INDIQUÉ | SetClientOutputEncoding | handler sélectionné; console non qualifiée |


**Manquants DisplaySession à ce snapshot** : `13`, `53`, `107`, `113`, `301`, `302`. Comme SwitchBrew ne donne pas leur sémantique dans la table publique, ils restent **U** et ne doivent pas devenir des stubs `Success`.

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


**Recoupement client libounce/OunceVK** : cmd 203 est désormais qualifié par un consommateur réel : `gsvGpuGetVmUserRanges` lit `u64 count + GsvGpuVaRange[4]` (72 B), et OunceVK exige un unique range `[0x08000000,0xBFFFFFFFFF]` avant l’import AS.

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
| 213 | [20.0.0+] NormalUnmapGpuMemory4K | C | HANDLER INDIQUÉ | NormalUnmapGpuMemory4K | actif |
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
| **Display** | IDs 13, 53, 107, 113, 301, 302 : **U**, format/effet public insuffisant. Pas de lecture spéculative ni de retour Success | Paquet raw et sémantique reproduits sur jeu réel |
| **Camera / Adraw / InterModuleImage / debug / profiling** | Non nécessaires au P0 prouvé ; laisser les fonctions absentes ou fail-closed. Aucun stub Success | Preuve d'utilisation indispensable au démarrage/gameplay |
| **Variantes worker firmware 19.x** | Numérotation/ABI versionnée hors périmètre si le firmware invité ciblé utilise le chemin actuel | Title ID / version et commande raw imposant l'autre variante |

**Mémoire GPU 214/215/216 :** la lecture des propriétaires sélectionnés montre que le remap prépare les tables et les pins avant de modifier les PTE ; une OOM pendant la modification empoisonne l'AS et interdit une nouvelle mutation. Le worker doit alors garder les pages CPU aliasées, le handle NVMap et sa session, car le dernier FreeHandle ou CloseSession pourrait retirer un backing encore pointé par des PTE partielles. En dehors de cette quarantaine exceptionnelle, le rollback normal conserve le comportement de libération. Le test hôte exécutable est dans tools/ns2/check_native_gpu_worker_sparse_ipc_host.py ; **ne pas annoncer ce contrat validé avant son exécution verte sur le couple exact**.

**Règle de clôture :** une limitation U/M/P connue mais sans chemin prouvé n'impose pas une implémentation hypothétique ; une corruption mémoire, un faux succès HLE, une ABI démontrée incorrecte ou un blocage observé sur un chemin actif interdit la clôture. L'issue NS2 #123 et les tests PS5 restent requis pour valider les titres.

## 15. État console / critère de fermeture

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

Ce registre est le tableau de complétude NS2 de référence à partir du 21/11 ; l’audit du 20/11 reste une photographie historique plus large.
