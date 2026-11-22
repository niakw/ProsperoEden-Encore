# Eden Encore — registre de complétude d’implémentation NS2 / SwitchBrew (21 novembre 2026)

> **Nature** : registre vivant de couverture **statique et hôte** pour Nintendo Switch 2. Il reprend les commandes publiées par SwitchBrew et les compare au C++ réellement sélectionné par Eden Encore. Une ligne manquante n’est **pas** automatiquement un bug de Mario Kart World ou Donkey Kong Bananza ; une ligne implémentée n’est **pas** une preuve console.

**Issue maîtresse NS2 : [#123](https://github.com/niakw/ProsperoEden-Encore/issues/123).**
**Référence historique complémentaire : [analyse des écarts NS2 puis NS1 du 20/11](./EDEN_ENCORE_GAP_ANALYSIS_NS2_THEN_NS1_2026-11-20.md).**

## 0. Provenance et règle de mise à jour

| Élément | Révision / source |
| --- | --- |
| Moteur `main` à la création de ce registre | `a59cae85eb1dd7246f5648b46e6fddceb736a5a6` |
| Vendor gitlink sélectionné | `a8c9170802811e7bb19345a461c3ae8dc72c27be` |
| Vendor `main` à la création | `546e1aa34d2ff183dd4c737f9da8fbf4a62be24e` |
| SwitchBrew GSV | https://www.switchbrew.org/wiki/Switch_2%3A_GSV_services — consultation 2026-11-21 |
| SwitchBrew NV services | https://www.switchbrew.org/wiki/NV_services — consultation 2026-11-21 |
| Client SDK recroisé | https://github.com/vexcited/fefw — notamment `src/nn/gpu/gpu_sdk_*.cpp` |
| Validation console du présent couple | **Aucune** : pas de build PS5, pas de première soumission/frame revendiquée |

**Codes** : **C** = implémentation C++ active et cohérente au niveau source/CI hôte ; **P** = partielle, contrat fusionné ou divergence ABI/nomenclature à revoir ; **M** = fonctionnalité non implémentée, que le dispatcher ait un refus/stub explicite ou aucun handler renseigné ; **U** = ID connu mais nom/ABI/sémantique publique insuffisante ; **V** = variante de version non couverte intentionnellement tant que le firmware invité cible ne la requiert pas.
**Tous les C/P restent console-non-qualifiés** tant qu’un build PS5 représentatif ne les a pas exercés.

**Colonnes séparées pour chaque commande (§1–§12)** : `Statut fonctionnel (F)` = comportement `C/P/M/U/V` ; `Traitement déclaré (R)` = représentation dans le registre : `HANDLER INDIQUÉ` (144), `HANDLER PARTIEL INDIQUÉ` (30), `STUB NOMMÉ` (2), `REFUS EXPLICITE` (6), `AUCUN HANDLER INDIQUÉ` (103), `ABI INCONNUE · AUCUN HANDLER` (25), `VARIANTE HORS VERSION` (6). Un refus peut être assuré par le **fallback générique** sans handler spécifique ; une absence de handler indiqué **n'exclut pas un fallback global**. Cette classification documentaire est **à distinguer** de la preuve CMake/ELF/console. Ne jamais compter un stub ou refus comme implémentation fonctionnelle.

### Politique des fonctions connues mais non implémentées

Une commande connue peut recevoir un **handler nommé** afin que la couverture soit explicite, avec un commentaire du type `// not implemented yet on Encore`, **mais elle ne doit jamais retourner un faux `Success`**. Tant que son effet réel n’est pas implémenté, elle doit répondre `NotImplemented`, `InvalidState` ou une erreur plus précise adaptée au contrat. Les commandes dont même le format d’entrée est inconnu restent sans lecture de payload plutôt que de deviner une ABI.

**Mise à jour fail-closed NVHOST (21/11)** : le vendor `f65ccc43` conserve l’ouverture des nodes `/dev/nvhost-*` inconnus nécessaire à la découverte NVN, mais leur fallback générique ne fabrique plus de sortie zéro/copiée ni de `Success`. Toute ioctl non couverte retourne désormais explicitement `NotImplemented` avec le marqueur `// not implemented yet on Encore`. Les handlers TSG authentifiés `BIND_CHANNEL`, `UNBIND_CHANNEL` et `BIND_CHANNEL_EX` restent actifs. **Aucune qualification PS5 n’est revendiquée.**

### Double compteur : couverture fonctionnelle et représentation explicite (22/11/2026)

> **Périmètre exact** : tables §1 à §12 de ce registre **sur `main`**, vérifiées sur moteur `1454df745f980d1db3448b0f4d63f5a41e7a7807`. Les 316 lignes sont des **entrées d'interface recensées**, pas la totalité du firmware SwitchBrew (ni les 4 903 lignes du catalogue NS1). Les ioctls historiques hors tables, les commandes debug S2 non énumérées (§13) et les variantes non recensées ne font pas partie du dénominateur. Ces comptes classent le **registre**, pas un nouveau test CMake/ELF/PS5.

Deux dimensions **indépendantes** doivent être suivies, sans assimiler un stub à une implémentation :

1. **Fonctionnelle (F)** : `C` = implémentation source renseignée, **144** ; `P` ou `C/P` = contrat partiel, **30** ; `M` = comportement non implémenté, **111**, qu'un stub existe ou non ; `U` = ABI/nature inconnue, **25** ; `V` = variante firmware non ciblée, **6**. `C` ne signifie **ni API exhaustive, ni build natif vert, ni succès console**.
2. **Représentation (R) dans le registre** : **182/316** possèdent une entrée non vide dans la colonne « Handler Encore » : les **144 C**, **29 P**, **1 C/P**, **8 M** avec stub/refus explicite indiqué. **134/316** ne disposent **d'aucun handler renseigné** : **103 M**, **25 U**, **6 V**. La valeur « fail-closed » est parfois un refus du dispatcher, **pas nécessairement un handler C++ propre à l'ID**. `R=mentionné` n'est donc **pas** une preuve de branchement IPC natif ; la couverture déclarative réellement validée demande une vérification ID → enregistrement/fallback → ABI → code de retour dans le C++ sélectionné.

| Statut fonctionnel | Total | Handler/stub/refus indiqué (R) | Aucun handler indiqué | Conséquence |
| --- | ---: | ---: | ---: | --- |
| C — couvert en source | 144 | 144 | 0 | À qualifier PS5 |
| P — partiel | 29 | 29 | 0 | Compléter le contrat requis |
| C/P — mixte | 1 | 1 | 0 | Examiner les deux chemins |
| M — non implémenté | 111 | **8** | **103** | Ne pas confondre refus explicite et absence |
| U — contrat inconnu | 25 | 0 | 25 | Ne pas inventer l'ABI |
| V — variante hors version | 6 | 0 | 6 | Garder conditionné au firmware |
| **Total** | **316** | **182** | **134** | **R ≠ F ≠ validation console** |

**Détail des huit `M` avec traitement indiqué (2 stubs nommés + 6 refus explicites) :** GSV `1001`/`1002` → `UnavailableVideoEncoder` ; channel `0x00004810`/`0x00004811` → refus `fail-closed` ; TSG `0x00005405`, `0xC0105409`, `0xC018540C`, `0xC008540D` → refus `TsgIoctl fail-closed`. Ces huit restent **M fonctionnels**.

**Consignes de mise à jour :** garder les statuts C/P/M/U/V et ajouter séparément le niveau de représentation (handler spécifique / stub sûr / refus générique / aucun / version exclue), avec chemin CMake/owner actif et commit moteur/vendor. Ne cocher « déclaré » comme **validé** qu'après contrôle de l'enregistrement ou du fallback réellement compilé. Un stub qui retourne `Success`/`0` sans exécuter une action mémoire, GPU, synchronisation ou sécurité est interdit. Ne pas ajouter de stub pour un payload/ABI inconnu ; ne pas détourner le P0 première soumission GPU / première frame pour caméra/profiler.

---

## 1. UserSession GSV — liste SwitchBrew complète

État courant de la table (22/11) : 142 commandes recensées ; C=30, P=22, M=72, U=18. État initial historique du 21/11 : C=27, P=26, M=72, U=17. Les divergences de nom sont volontairement visibles : elles signalent les endroits où la simple présence d’un handler ne suffit pas.

| Cmd | Interface | Nom SwitchBrew | Statut fonctionnel (F) | Traitement déclaré (R) | Handler Encore actif | Écart / raison |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Gsv | BootWithTransferMemory | C | HANDLER INDIQUÉ | InitializeWithTransferMemory | handler actif; boot transfert réel, console non qualifiée |
| 4 | Gsv | BootWithRemoteMemory | C | HANDLER INDIQUÉ | Initialize | handler actif; remote-memory |
| 11 |  | SetCurrentProcessHandle | C | HANDLER INDIQUÉ | BindProcess | processus natif authentifié |
| 12 |  | (nom inconnu SwitchBrew) | U | ABI INCONNUE · AUCUN HANDLER | — | ID connu, ABI/sémantique insuffisamment documentées |
| 101 |  | CreateContext | P | HANDLER PARTIEL INDIQUÉ | CompleteBootstrap | ID actif mais sémantique/nomenclature Encore à recroiser |
| 111 | NativeMemory | CreateNativeMemory | C | HANDLER INDIQUÉ | CreateNativeMemory | actif |
| 112 | NativeMemory | DestroyNativeMemory | C | HANDLER INDIQUÉ | DestroyNativeMemory | actif |
| 113 | NativeMemory | CreateNativeMemoryBlockByTransferMemory | C | HANDLER INDIQUÉ | CreateNativeMemoryWithTransferMemory | actif |
| 114 | NativeMemory | CreateNativeMemoryBlock | C | HANDLER INDIQUÉ | BindNativeMemory | actif; nom Encore différent |
| 115 | NativeMemory | BootNativeMemoryManagement | C | HANDLER INDIQUÉ | BootNativeMemoryManagement | actif |
| 187 | NativeMemory | QueryNativeMemoryNvsNvRmMemIdForDebug | M | AUCUN HANDLER INDIQUÉ | — | aucun handler sélectionné; debug, non P0 |
| 201 | Syncpt | CreateSyncptContext | C | HANDLER INDIQUÉ | CreateSyncptContext | actif |
| 202 | Syncpt | InitializeSyncptContext | P | HANDLER PARTIEL INDIQUÉ | OpenSyncptSession | session réelle, nom/contrat à aligner |
| 211 | Syncpt | CreateDebugSyncDevice | M | AUCUN HANDLER INDIQUÉ | — | aucun handler |
| 212 | Syncpt | DestroyDebugSyncDevice | M | AUCUN HANDLER INDIQUÉ | — | aucun handler |
| 213 | Syncpt | CreateDebugSyncCounter | M | AUCUN HANDLER INDIQUÉ | — | aucun handler |
| 214 | Syncpt | DestroyDebugSyncCounter | M | AUCUN HANDLER INDIQUÉ | — | aucun handler |
| 215 | Syncpt | ReportDebugSyncCounterValue | M | AUCUN HANDLER INDIQUÉ | — | aucun handler |
| 301 | Display | CreateDisplayContext | P | HANDLER PARTIEL INDIQUÉ | InitializeDisplayContext | ID actif; cycle create/init fusionné ou nomenclature divergente |
| 303 | Display | DestroyDisplayContext | C | HANDLER INDIQUÉ | FinalizeDisplayContext | actif |
| 305 | Display | InitializeDisplayContext | P | HANDLER PARTIEL INDIQUÉ | OpenDisplaySession | retour session réel; vérifier ABI version |
| 311 | Display | (nom inconnu) | U | ABI INCONNUE · AUCUN HANDLER | — | ID connu sans contrat public suffisant |
| 312 | Display | (nom inconnu) | U | ABI INCONNUE · AUCUN HANDLER | — | ID connu sans contrat public suffisant |
| 314 | Display | (nom inconnu) | P | HANDLER PARTIEL INDIQUÉ | DestroyNativeWindowAliasImagePool | handler actif; nom SwitchBrew absent |
| 315 | Display | (nom inconnu) | P | HANDLER PARTIEL INDIQUÉ | CreateNativeWindowAliasImagePool | handler actif; nom SwitchBrew absent |
| 321 | Display | (nom inconnu) | U | ABI INCONNUE · AUCUN HANDLER | — | pas de handler / contrat insuffisant |
| 327 | Display | (nom inconnu) | U | ABI INCONNUE · AUCUN HANDLER | — | pas de handler / contrat insuffisant |
| 361 | Display | (nom inconnu) | U | ABI INCONNUE · AUCUN HANDLER | — | pas de handler / contrat insuffisant |
| 391 | Display | CalculateRequiredBufferMemory | M | AUCUN HANDLER INDIQUÉ | — | pas de handler sélectionné |
| 401 | Gpu | CreateGpuContext | C | HANDLER INDIQUÉ | InitializeGpuContext | actif; création état GPU |
| 402 | Gpu | InitializeGpuContext | C | HANDLER INDIQUÉ | ActivateGpuContext | actif |
| 403 | Gpu | DestroyGpuContext | C | HANDLER INDIQUÉ | DestroyGpuContext | actif |
| 423 | Gpu | (nom public incomplet) | C | HANDLER INDIQUÉ | BindNativeGpuMemory | Ounce/fefw envoie raw `0x1B7` (TIPC 423) pour le bind enfant NativeMemory → parent GPU/NVMap; ownership, adresse, taille et offset sont validés |
| 424 | Gpu | (nom inconnu) | U | ABI INCONNUE · AUCUN HANDLER | — | pas de handler / contrat public incomplet |
| 425 | Gpu | (nom inconnu) | U | ABI INCONNUE · AUCUN HANDLER | — | pas de handler / contrat public incomplet |
| 426 | Gpu | MapNativeImage | C | HANDLER INDIQUÉ | MapNativeGpuImage | actif |
| 427 | Gpu | UnmapNativeImage | C | HANDLER INDIQUÉ | UnmapNativeGpuImage | actif |
| 428 | Gpu | QueryNativeImage | C | HANDLER INDIQUÉ | QueryNativeGpuImage | actif |
| 429 | Gpu | CreateNativeImage | C | HANDLER INDIQUÉ | CreateNativeImage | actif |
| 430 | Gpu | DestroyNativeImage | C | HANDLER INDIQUÉ | DestroyNativeImage | actif |
| 434 | Gpu | ExistsAddressSpace (nom public) | C | HANDLER INDIQUÉ | RegisterGpuAddressSpace | Ounce/fefw envoie raw `0x1C2` avec un seul AS fd et attend un résultat; Encore enregistre exactement l'AS possédé par le process |
| 435 | Gpu | CalculateNativeImageSize | C | HANDLER INDIQUÉ | CalculateNativeImageSize | actif |
| 437 | Gpu | CreateNativeMemoryWithGpukMemHandle | U | ABI INCONNUE · AUCUN HANDLER | — | nom/ID public connu, mais l'implémentation Ounce observée utilise raw `0x1B7` → TIPC 423; aucun contrat raw `0x1C5` prouvé, donc pas de doublon inventé |
| 493 | Gpu | CreateUserlandDebuggerSession | M | AUCUN HANDLER INDIQUÉ | — | pas de handler; debug non P0 |
| 494 | Gpu | (nom inconnu) | U | ABI INCONNUE · AUCUN HANDLER | — | pas de handler / contrat insuffisant |
| 496 | Gpu | CreateGpuSessionWithTransferMemory | C | HANDLER INDIQUÉ | OpenGpuSessionWithTransferMemory | session GPU réelle |
| 497 | Gpu | CreateGpuSessionWithRemoteMemory | C | HANDLER INDIQUÉ | OpenGpuSession | session GPU réelle |
| 498 | Gpu | TryQueryDonatedTransferMemoryUsage | C | HANDLER INDIQUÉ | QueryDonatedTransferMemoryUsage | ABI Ounce exacte: aucune entrée, trois u64 total/used/peak; le cmd 1 conserve le vrai KTransferMemory donné, remote-memory échoue fermé |

**Réconciliation Ounce 21/11** : le SDK reconstruit par fefw appelle `CreateNativeMemoryWithGpukMemHandle` via `Invoke(0x1B7)`, soit TIPC **423** après retrait de `0x10`, et appelle l'enregistrement d'address-space via raw `0x1C2`, soit **434**. Pour **498**, il appelle raw `0x202` sans entrée et lit trois `u64`. Ces observations priment pour le runtime actif sur une simple attribution de nom non documentée; elles ne constituent pas une validation console PS5.
| 601 | Camera | CreateCameraContext | P | HANDLER PARTIEL INDIQUÉ | InitializeFeatureContext | ID actif mais create/init fusionné |
| 602 | Camera | InitializeCameraContext | P | HANDLER PARTIEL INDIQUÉ | OpenCameraContext | session partielle; contrat à aligner |
| 603 | Camera | DestroyCameraContext | M | AUCUN HANDLER INDIQUÉ | — | pas de handler |
| 612 | Camera | DestroyOutputBufferPool | M | AUCUN HANDLER INDIQUÉ | — | pas de handler |
| 613 | Camera | CreateAliasOutputBufferPool | M | AUCUN HANDLER INDIQUÉ | — | pas de handler |
| 614 | Camera | DestroyAliasOutputBufferPool | M | AUCUN HANDLER INDIQUÉ | — | pas de handler |
| 615 | Camera | CreateOutputBufferPool | M | AUCUN HANDLER INDIQUÉ | — | pas de handler |
| 616 | Camera | ReadFrameDataAsync | M | AUCUN HANDLER INDIQUÉ | — | pas de handler UserSession |
| 620 | Camera | InitializeB | M | AUCUN HANDLER INDIQUÉ | — | pas de handler |
| 621 | Camera | FinalizeB | M | AUCUN HANDLER INDIQUÉ | — | pas de handler |
| 622 | Camera | ListCameras | M | AUCUN HANDLER INDIQUÉ | — | pas de handler |
| 623 | Camera | OpenCamera | M | AUCUN HANDLER INDIQUÉ | — | pas de handler UserSession; sous-session caméra possède un OpenCamera séparé |
| 624 | Camera | CloseCamera | M | AUCUN HANDLER INDIQUÉ | — | pas de handler |
| 626 | Camera | ListSensorMode | M | AUCUN HANDLER INDIQUÉ | — | pas de handler |
| 627 | Camera | SetSensorMode | M | AUCUN HANDLER INDIQUÉ | — | pas de handler |
| 628 | Camera | GetAvailableStreams | M | AUCUN HANDLER INDIQUÉ | — | pas de handler |
| 629 | Camera | GetRequiredWorkBufferSize | M | AUCUN HANDLER INDIQUÉ | — | pas de handler |
| 630 | Camera | CreateStream | M | AUCUN HANDLER INDIQUÉ | — | pas de handler |
| 632 | Camera | GetReadDoneEvent | M | AUCUN HANDLER INDIQUÉ | — | pas de handler |
| 633 | Camera | GetStreamOutputSize | M | AUCUN HANDLER INDIQUÉ | — | pas de handler |
| 634 | Camera | DestroyStream | M | AUCUN HANDLER INDIQUÉ | — | pas de handler |
| 636 | Camera | ReadFrameDataAsync | M | AUCUN HANDLER INDIQUÉ | — | pas de handler |
| 637 | Camera | GetAttachedEvent | M | AUCUN HANDLER INDIQUÉ | — | pas de handler |
| 638 | Camera | GetDetachedEvent | M | AUCUN HANDLER INDIQUÉ | — | pas de handler |
| 639 | Camera | GetFrameInfo | M | AUCUN HANDLER INDIQUÉ | — | pas de handler |
| 640 | Camera | GetFrameInfo2 | M | AUCUN HANDLER INDIQUÉ | — | pas de handler |
| 641 | Camera | GetConnectionChangedEvent | M | AUCUN HANDLER INDIQUÉ | — | pas de handler |
| 650 | Camera | SetPictureQualityConfig | M | AUCUN HANDLER INDIQUÉ | — | pas de handler |
| 651 | Camera | GetPictureQualityConfig | M | AUCUN HANDLER INDIQUÉ | — | pas de handler |
| 652 | Camera | SetDigitalWindow | M | AUCUN HANDLER INDIQUÉ | — | pas de handler |
| 653 | Camera | GetDigitalWindow | M | AUCUN HANDLER INDIQUÉ | — | pas de handler |
| 654 | Camera | GetDigitalWindowCapability | M | AUCUN HANDLER INDIQUÉ | — | pas de handler |
| 655 | Camera | GetSupportedFunctions | M | AUCUN HANDLER INDIQUÉ | — | pas de handler |
| 656 | Camera | GetSupportedDebugFunctions | M | AUCUN HANDLER INDIQUÉ | — | pas de handler |
| 657 | Camera | GetCameraPrivacyCoverStatus | M | AUCUN HANDLER INDIQUÉ | — | pas de handler |
| 658 | Camera | GetCameraDeviceTemperature | M | AUCUN HANDLER INDIQUÉ | — | pas de handler |
| 659 | Camera | GetDeviceUniqueId | M | AUCUN HANDLER INDIQUÉ | — | pas de handler |
| 660 | Camera | GetSensorMode | M | AUCUN HANDLER INDIQUÉ | — | pas de handler |
| 661 | Camera | GetStride | M | AUCUN HANDLER INDIQUÉ | — | pas de handler |
| 662 | Camera | UnlinkSensor | M | AUCUN HANDLER INDIQUÉ | — | pas de handler |
| 663 | Camera | GetDeviceModel | M | AUCUN HANDLER INDIQUÉ | — | pas de handler |
| 664 | Camera | SetRawSensorMode | M | AUCUN HANDLER INDIQUÉ | — | pas de handler |
| 665 | Camera | GetAccessAllowed | M | AUCUN HANDLER INDIQUÉ | — | pas de handler |
| 666 | Camera | GetHostDrivenAeRegion | M | AUCUN HANDLER INDIQUÉ | — | pas de handler |
| 667 | Camera | SetHostDrivenAeRegion | M | AUCUN HANDLER INDIQUÉ | — | pas de handler |
| 691 | Camera | CalculateImageArraySize | M | AUCUN HANDLER INDIQUÉ | — | pas de handler |
| 901 | VideoDecoder | CreateVideoDecoderContext | P | HANDLER PARTIEL INDIQUÉ | InitializeVideoDecoderContext | ID actif, nom/séquence create/init divergents |
| 902 | VideoDecoder | InitializeVideoDecoderContext | P | HANDLER PARTIEL INDIQUÉ | OpenVideoDecoderSession | retour session réel; sémantique proche mais nom différent |
| 903 | VideoDecoder | DestroyVideoDecoderContext | M | AUCUN HANDLER INDIQUÉ | — | pas de handler UserSession |
| 904 | VideoDecoderForSystem | InitializeVideoDecoderContextForSystem | M | AUCUN HANDLER INDIQUÉ | — | pas de handler |
| 905 | VideoDecoder | InitializeVideoDecoderContext2 | P | HANDLER PARTIEL INDIQUÉ | OpenVideoDecoderSessionWithFlag | handler actif; ABI à comparer |
| 911 | VideoDecoder | InitializeDecoderImagePool | P | HANDLER PARTIEL INDIQUÉ | CreateVideoImagePool | pool réel, nomenclature différente |
| 912 | VideoDecoder | FinalizeDecoderImagePool | P | HANDLER PARTIEL INDIQUÉ | DestroyVideoImagePool | pool réel |
| 921 | VideoDecoderForSystem | InitializeDecoderAliasImagePool | M | AUCUN HANDLER INDIQUÉ | — | pas de handler |
| 922 | VideoDecoderForSystem | FinalizeDecoderAliasImagePool | M | AUCUN HANDLER INDIQUÉ | — | pas de handler |
| 961 | VideoDecoder | (nom inconnu) | P | HANDLER PARTIEL INDIQUÉ | GetCpuUserImageDescriptor | handler actif; contrat SwitchBrew incomplet |
| 991 | VideoDecoder | (nom inconnu) | P | HANDLER PARTIEL INDIQUÉ | CalculateDecoderImagePoolBuffer | handler actif; contrat SwitchBrew incomplet |
| 1001 | VideoEncoder | CreateVideoEncoderContext | M | STUB NOMMÉ | UnavailableVideoEncoder | stub nommé, commentaire not implemented yet on Encore, retourne NotImplemented ; encodeur non fourni |
| 1002 | VideoEncoder | InitializeVideoEncoderContext | M | STUB NOMMÉ | UnavailableVideoEncoder | stub nommé, commentaire not implemented yet on Encore, retourne NotImplemented ; aucune session décodeur créée |
| 1003 | VideoEncoder | DestroyVideoEncoderContext | M | AUCUN HANDLER INDIQUÉ | — | pas de handler |
| 1004 | VideoEncoderForSystem | InitializeVideoEncoderContextForSystem | M | AUCUN HANDLER INDIQUÉ | — | pas de handler |
| 1011 | VideoEncoder | InitializeEncoderImagePool | M | AUCUN HANDLER INDIQUÉ | — | pas de handler |
| 1012 | VideoEncoder | FinalizeEncoderImagePool | M | AUCUN HANDLER INDIQUÉ | — | pas de handler |
| 1021 | VideoEncoderForSystem | InitializeEncoderAliasImagePool | M | AUCUN HANDLER INDIQUÉ | — | pas de handler |
| 1022 | VideoEncoderForSystem | FinalizeEncoderAliasImagePool | M | AUCUN HANDLER INDIQUÉ | — | pas de handler |
| 1061 | VideoEncoder | (nom inconnu) | U | ABI INCONNUE · AUCUN HANDLER | — | ID connu sans contrat public suffisant |
| 1091 | VideoEncoder | (nom inconnu) | U | ABI INCONNUE · AUCUN HANDLER | — | ID connu sans contrat public suffisant |
| 1101 | GraphicsFrame | CreateGraphicsFrameContext | C | HANDLER INDIQUÉ | CreateGraphicsFrameContext | host qualifié |
| 1102 | GraphicsFrame | InitializeGraphicsFrameContext | C | HANDLER INDIQUÉ | InitializeGraphicsFrameContext | host qualifié |
| 1111 | GraphicsFrame | SetGraphicsFrameLengthMode | C | HANDLER INDIQUÉ | SetGraphicsFrameLengthMode | valeurs bornées, host qualifié |
| 1112 | GraphicsFrame | SetGraphicsFrameRestartMode | C | HANDLER INDIQUÉ | SetGraphicsFrameRestartMode | valeurs bornées, host qualifié |
| 1113 | GraphicsFrame | SetGraphicsFrameGpuTimesliceMode | C | HANDLER INDIQUÉ | SetGraphicsFrameGpuTimesliceMode | valeurs bornées, host qualifié |
| 1201 | Chat | CreateChatContext | P | HANDLER PARTIEL INDIQUÉ | InitializeChatContext | ID actif, create/init fusionné |
| 1202 | Chat | InitializeChatContext | P | HANDLER PARTIEL INDIQUÉ | OpenChatSession | session réelle, nom différent |
| 1203 | Chat | DestroyChatContext | M | AUCUN HANDLER INDIQUÉ | — | pas de handler |
| 1211 | Chat | CreateImagePool | P | HANDLER PARTIEL INDIQUÉ | CreateChatImagePool | actif |
| 1212 | Chat | DestroyImagePool | P | HANDLER PARTIEL INDIQUÉ | DestroyChatImagePool | actif |
| 1291 | Chat | CalculateRequiredBufferMemory | C | HANDLER INDIQUÉ | CalculateChatImagePoolSize | actif |
| 1301 | Adraw | CreateAdrawContext | M | AUCUN HANDLER INDIQUÉ | — | pas de handler |
| 1302 | Adraw | InitializeAdrawContext | M | AUCUN HANDLER INDIQUÉ | — | pas de handler |
| 1325 | Adraw | GetAdrawFrameBufferHandle | M | AUCUN HANDLER INDIQUÉ | — | pas de handler |
| 1326 | Adraw | GetAdrawImageHandle | M | AUCUN HANDLER INDIQUÉ | — | pas de handler |
| 1401 | NvDrv | CreateNvDrv2UserSessionWithTransferMemory | P | HANDLER PARTIEL INDIQUÉ | OpenNvsrvSessionWithTransferMemory | session NVDRV réelle; nom interne différent |
| 1402 | NvDrv | CreateNvDrv2UserSessionWithRemoteMemory | P | HANDLER PARTIEL INDIQUÉ | OpenNvsrvSession | session NVDRV réelle |
| 1411 | NvDrv | GetNvDrv2UserTransferMemoryUsage | M | AUCUN HANDLER INDIQUÉ | — | pas de handler |
| 1501 | InterModuleImage | CreateInterModuleImageContext | M | AUCUN HANDLER INDIQUÉ | — | pas de handler |
| 1502 | InterModuleImage | InitializeInterModuleImageContext | M | AUCUN HANDLER INDIQUÉ | — | pas de handler |
| 1510 | InterModuleImage | (nom inconnu) | P | HANDLER PARTIEL INDIQUÉ | CalculateRequirements | handler actif; fonction SwitchBrew non nommée |
| 1601 |  | (nom inconnu) | U | ABI INCONNUE · AUCUN HANDLER | — | ID connu sans documentation suffisante |
| 1602 |  | (nom inconnu) | U | ABI INCONNUE · AUCUN HANDLER | — | ID connu sans documentation suffisante |
| 1603 |  | (nom inconnu) | U | ABI INCONNUE · AUCUN HANDLER | — | ID connu sans documentation suffisante |
| 1611 |  | (nom inconnu) | U | ABI INCONNUE · AUCUN HANDLER | — | ID connu sans documentation suffisante |
| 1612 |  | (nom inconnu) | U | ABI INCONNUE · AUCUN HANDLER | — | ID connu sans documentation suffisante |
| 1691 |  | (nom inconnu) | U | ABI INCONNUE · AUCUN HANDLER | — | ID connu sans documentation suffisante |


## 2. SyncptSession

SwitchBrew ne nomme publiquement que `Ping`; les autres IDs sont conservés comme inconnus au lieu d’inventer leur contrat.

| Cmd | Nom SwitchBrew | Statut fonctionnel (F) | Traitement déclaré (R) | Handler Encore | Écart / raison |
| --- | --- | --- | --- | --- | --- |
| 0 | Ping | C | HANDLER INDIQUÉ | Handshake | ping/handshake réel |
| 1 | (nom inconnu) | C | HANDLER INDIQUÉ | GetCount | ID couvert; sémantique publique incomplète |
| 21 | (nom inconnu) | P | HANDLER PARTIEL INDIQUÉ | Unknown21 | handler explicite mais fonction inconnue |
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
| 13 | (SwitchBrew non nommé) | U | ABI INCONNUE · AUCUN HANDLER | — | pas de handler et sémantique publique insuffisante |
| 21 | (SwitchBrew non nommé) | C | HANDLER INDIQUÉ | GetNotifications | handler sélectionné; console non qualifiée |
| 31 | (SwitchBrew non nommé) | C | HANDLER INDIQUÉ | GetVsyncEvent | handler sélectionné; console non qualifiée |
| 32 | (SwitchBrew non nommé) | C | HANDLER INDIQUÉ | GetDisplayVsyncEvent | handler sélectionné; console non qualifiée |
| 51 | (SwitchBrew non nommé) | C | HANDLER INDIQUÉ | ConfigureRequestGroups | handler sélectionné; console non qualifiée |
| 53 | (SwitchBrew non nommé) | U | ABI INCONNUE · AUCUN HANDLER | — | pas de handler et sémantique publique insuffisante |
| 101 | (SwitchBrew non nommé) | C | HANDLER INDIQUÉ | OpenDisplay | handler sélectionné; console non qualifiée |
| 102 | (SwitchBrew non nommé) | C | HANDLER INDIQUÉ | CloseDisplay | handler sélectionné; console non qualifiée |
| 103 | (SwitchBrew non nommé) | C | HANDLER INDIQUÉ | QueryDisplayRefreshRate | handler sélectionné; console non qualifiée |
| 104 | (SwitchBrew non nommé) | C | HANDLER INDIQUÉ | QueryDisplayHdrStatus | handler sélectionné; console non qualifiée |
| 105 | (SwitchBrew non nommé) | C | HANDLER INDIQUÉ | QueryDisplayHdrPaperWhite | handler sélectionné; console non qualifiée |
| 106 | (SwitchBrew non nommé) | C | HANDLER INDIQUÉ | GetBufferMaxResolution | handler sélectionné; console non qualifiée |
| 107 | (SwitchBrew non nommé) | U | ABI INCONNUE · AUCUN HANDLER | — | pas de handler et sémantique publique insuffisante |
| 111 | (SwitchBrew non nommé) | C | HANDLER INDIQUÉ | OpenEndpoint | handler sélectionné; console non qualifiée |
| 112 | (SwitchBrew non nommé) | C | HANDLER INDIQUÉ | CloseEndpoint | handler sélectionné; console non qualifiée |
| 113 | (SwitchBrew non nommé) | U | ABI INCONNUE · AUCUN HANDLER | — | pas de handler et sémantique publique insuffisante |
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
| 301 | (SwitchBrew non nommé) | U | ABI INCONNUE · AUCUN HANDLER | — | pas de handler et sémantique publique insuffisante |
| 302 | (SwitchBrew non nommé) | U | ABI INCONNUE · AUCUN HANDLER | — | pas de handler et sémantique publique insuffisante |
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
| 210 | InitializeVideoDecoderWithRemoteMemory | M | AUCUN HANDLER INDIQUÉ | — | pas de handler explicite |
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
| 1 | CreateVideoEncoderSession | M | AUCUN HANDLER INDIQUÉ | — | aucune session encodeur NS2 sélectionnée |
| 4 | GetOutputEvent | M | AUCUN HANDLER INDIQUÉ | — | encodeur non implémenté |
| 5 | Start | M | AUCUN HANDLER INDIQUÉ | — | encodeur non implémenté |
| 100 | InitializeVideoEncoder | M | AUCUN HANDLER INDIQUÉ | — | encodeur non implémenté |
| 101 | Configure | M | AUCUN HANDLER INDIQUÉ | — | encodeur non implémenté |
| 102 | GetBufferSize | M | AUCUN HANDLER INDIQUÉ | — | encodeur non implémenté |
| 108 | Encode | M | AUCUN HANDLER INDIQUÉ | — | encodeur non implémenté |
| 110 | GetBuffer | M | AUCUN HANDLER INDIQUÉ | — | encodeur non implémenté |
| 111 | SetParameters | M | AUCUN HANDLER INDIQUÉ | — | encodeur non implémenté |
| 112 | FinalizeVideoEncoder | M | AUCUN HANDLER INDIQUÉ | — | encodeur non implémenté |
| 206 | Stop | M | AUCUN HANDLER INDIQUÉ | — | encodeur non implémenté |


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
| 102 | (nom inconnu) | U | ABI INCONNUE · AUCUN HANDLER | — | ID SwitchBrew sans contrat public suffisant |
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
| 201 | [19.0.0–19.1.0] NormalMapGpuMemory4K | V | VARIANTE HORS VERSION | — | ancienne numérotation; non requise pour chemin 20.0+ tant que firmware invité cible confirmé |
| 202 | [19.0.0–19.1.0] NormalUnmapGpuMemory4K | V | VARIANTE HORS VERSION | — | ancienne numérotation |
| 203 | [19.0.0–19.1.0] CreateSparseRegion | V | VARIANTE HORS VERSION | — | ancienne numérotation |
| 204 | [19.0.0–19.1.0] DestroySparseRegion | V | VARIANTE HORS VERSION | — | ancienne numérotation |
| 205 | [19.0.0–19.1.0] ExecuteSparseMapRequests | V | VARIANTE HORS VERSION | — | ancienne numérotation |
| 207 | [19.0.0–19.1.0] NormalModifyMemoryKind4K | V | VARIANTE HORS VERSION | — | ancienne numérotation |
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
| 0xC0084710 | [S2] NVGPU_GPU_IOCTL_WAIT_FOR_PAUSE | M | AUCUN HANDLER INDIQUÉ | — | aucun handler natif |
| 0x80084712 | NVGPU_GPU_IOCTL_NUM_VSMS | C | HANDLER INDIQUÉ | NUM_VSMS | profil GA10F cohérent |
| 0xC0084713 | [S2] NVGPU_GPU_IOCTL_VSMS_MAPPING | C | HANDLER INDIQUÉ | VSMS_MAPPING | inline mapping GA10F |
| 0xC010471E | [S2] NVGPU_GPU_IOCTL_SET_DETERMINISTIC_OPTS | M | AUCUN HANDLER INDIQUÉ | — | aucun handler |
| 0xC010471F | [S2] NVGPU_GPU_IOCTL_GET_ENGINE_INFO | C | HANDLER INDIQUÉ | GET_ENGINE_INFO | runlists graphics/copy exposés |


Les autres ioctls de contrôle hérités de Switch 1 restent suivis par les audits existants ; ce tableau met en avant les formes S2 ou modifiées S2 directement pertinentes.

## 10. NVDRV — /dev/nvhost-gpu / channel

| Ioctl | Nom SwitchBrew | Statut fonctionnel (F) | Traitement déclaré (R) | Handler Encore | Écart / raison |
| --- | --- | --- | --- | --- | --- |
| 0xC0??0001 | NVHOST_IOCTL_CHANNEL_SUBMIT | C/P | HANDLER PARTIEL INDIQUÉ | Submit | chemin historique, à qualifier séparément pour native |
| 0xC0080002 | NVHOST_IOCTL_CHANNEL_GET_SYNCPOINT | C | HANDLER INDIQUÉ | GetSyncpoint | actif |
| 0xC0080003 | NVHOST_IOCTL_CHANNEL_GET_WAITBASE | C | HANDLER INDIQUÉ | GetWaitbase | actif |
| 0xC0080004 | NVHOST_IOCTL_CHANNEL_GET_MODMUTEX | M | AUCUN HANDLER INDIQUÉ | — | pas de case sélectionné |
| 0x40040007 | NVHOST_IOCTL_CHANNEL_SET_SUBMIT_TIMEOUT | M | AUCUN HANDLER INDIQUÉ | — | pas de case sélectionné |
| 0xC0080023 | NVHOST_IOCTL_CHANNEL_GET_CLK_RATE | M | AUCUN HANDLER INDIQUÉ | — | pas de case sélectionné |
| 0xC018480C | NVGPU_IOCTL_CHANNEL_SET_ERROR_NOTIFIER | C | HANDLER INDIQUÉ | SetErrorNotifier | S2: état interne Switch; mem non nul initialise, mem=0 désinitialise; offset/size ignorés; aucun faux backing NvMap |
| 0x0000480E | NVGPU_IOCTL_CHANNEL_ENABLE | C | HANDLER INDIQUÉ | NativeChannelSetEnabled | état runnable natif partagé avec TSG |
| 0x0000480F | NVGPU_IOCTL_CHANNEL_DISABLE | C | HANDLER INDIQUÉ | NativeChannelSetEnabled | bloque réellement les submits natifs |
| 0x00004810 | NVGPU_IOCTL_CHANNEL_PREEMPT | M | REFUS EXPLICITE | fail-closed | préemption GPU réelle absente |
| 0x00004811 | NVGPU_IOCTL_CHANNEL_FORCE_RESET | M | REFUS EXPLICITE | fail-closed | reset GPU réel absent |
| 0x40104812 | [S2] NVGPU_IOCTL_CHANNEL_EVENT_ID_CONTROL | P | HANDLER PARTIEL INDIQUÉ | NativeEventIdControl | Ounce exact: 16 B {cmd,id,u64=0}, appel observé {enable,2,0}; QueryEvent 1/2/3 configurés et clear réel, IDs 4..6 → NotImplemented faute de producteurs |
| 0xC0104813 | NVGPU_IOCTL_CHANNEL_CYCLE_STATS_SNAPSHOT | M | AUCUN HANDLER INDIQUÉ | — | pas de handler |
| 0x40084714 | NVGPU_IOCTL_CHANNEL_SET_USER_DATA | C | HANDLER INDIQUÉ | SetClientData | actif |
| 0x80084715 | NVGPU_IOCTL_CHANNEL_GET_USER_DATA | C | HANDLER INDIQUÉ | GetClientData | actif |
| 0x80804816 | NVGPU_IOCTL_CHANNEL_GET_ERROR_INFO | P | HANDLER PARTIEL INDIQUÉ | GetErrorInfo | ABI 128 B actif; état no_error courant renvoyé; publication d'une faute GPU réelle pas encore reliée |
| 0xC0104817 | NVGPU_IOCTL_CHANNEL_GET_ERROR_NOTIFICATION | P | HANDLER PARTIEL INDIQUÉ | GetErrorNotification | ABI 16 B actif; status Switch 0xFFFF et état interne courant; publication d'une faute GPU réelle pas encore reliée |
| 0x40204818 | NVGPU_IOCTL_CHANNEL_ALLOC_GPFIFO_EX | C | HANDLER INDIQUÉ | AllocGPFIFOEx | actif |
| 0xC0??4819 | NVGPU_IOCTL_CHANNEL_SUBMIT_GPFIFO_RETRY | M | AUCUN HANDLER INDIQUÉ | — | pas de handler dédié |
| 0xC020481A | NVGPU_IOCTL_CHANNEL_ALLOC_GPFIFO_EX2 | C | HANDLER INDIQUÉ | AllocGPFIFOEx2 | actif |
| 0xC018481B | NVGPU_IOCTL_CHANNEL_SUBMIT_GPFIFO2 | C | HANDLER INDIQUÉ | SubmitGPFIFO | actif; S2 conserve les flags d'entrée dans la réponse Ioctl2 (Ounce utilise 6), NS1 conserve le zéro historique |
| 0xC018481C | NVGPU_IOCTL_CHANNEL_SUBMIT_GPFIFO2_RETRY | M | AUCUN HANDLER INDIQUÉ | — | pas de handler dédié |
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
| 0x40085001 | NVGPU_PROFILER_IOCTL_BIND_CONTEXT | M | AUCUN HANDLER INDIQUÉ | — | device profiler S2 non implémenté dans le runtime actif |
| 0x40105002 | NVGPU_PROFILER_IOCTL_RESERVE_PM_RESOURCE | M | AUCUN HANDLER INDIQUÉ | — | device profiler S2 non implémenté dans le runtime actif |
| 0x40085003 | NVGPU_PROFILER_IOCTL_RELEASE_PM_RESOURCE | M | AUCUN HANDLER INDIQUÉ | — | device profiler S2 non implémenté dans le runtime actif |
| 0xC0305004 | NVGPU_PROFILER_IOCTL_ALLOC_PMA_STREAM | M | AUCUN HANDLER INDIQUÉ | — | device profiler S2 non implémenté dans le runtime actif |
| 0x00005005 | NVGPU_PROFILER_IOCTL_FREE_PMA_STREAM | M | AUCUN HANDLER INDIQUÉ | — | device profiler S2 non implémenté dans le runtime actif |
| 0x00005006 | NVGPU_PROFILER_IOCTL_BIND_PM_RESOURCES | M | AUCUN HANDLER INDIQUÉ | — | device profiler S2 non implémenté dans le runtime actif |
| 0x00005007 | NVGPU_PROFILER_IOCTL_UNBIND_PM_RESOURCES | M | AUCUN HANDLER INDIQUÉ | — | device profiler S2 non implémenté dans le runtime actif |
| 0xC0285008 | NVGPU_PROFILER_IOCTL_PMA_STREAM_UPDATE_GET_PUT | M | AUCUN HANDLER INDIQUÉ | — | device profiler S2 non implémenté dans le runtime actif |
| 0xC0205009 | NVGPU_PROFILER_IOCTL_EXEC_REG_OPS | M | AUCUN HANDLER INDIQUÉ | — | device profiler S2 non implémenté dans le runtime actif |
| 0x0000500A | NVGPU_PROFILER_IOCTL_UNBIND_CONTEXT | M | AUCUN HANDLER INDIQUÉ | — | device profiler S2 non implémenté dans le runtime actif |
| 0x4010500B | NVGPU_PROFILER_IOCTL_VAB_RESERVE | M | AUCUN HANDLER INDIQUÉ | — | device profiler S2 non implémenté dans le runtime actif |
| 0x0000500C | NVGPU_PROFILER_IOCTL_VAB_RELEASE | M | AUCUN HANDLER INDIQUÉ | — | device profiler S2 non implémenté dans le runtime actif |
| 0x4010500D | NVGPU_PROFILER_IOCTL_VAB_FLUSH_STATE | M | AUCUN HANDLER INDIQUÉ | — | device profiler S2 non implémenté dans le runtime actif |


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
