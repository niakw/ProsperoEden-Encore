# Eden Encore — registre de complétude d’implémentation NS2 / SwitchBrew (21 novembre 2026)

> **Nature** : registre vivant de couverture **statique et hôte** pour Nintendo Switch 2. Il reprend les commandes publiées par SwitchBrew et les compare au C++ réellement sélectionné par Eden Encore. Une ligne manquante n’est **pas** automatiquement un bug de Mario Kart World ou Donkey Kong Bananza ; une ligne implémentée n’est **pas** une preuve console.

**Issue maîtresse NS2 : [#123](https://github.com/niakw/ProsperoEden-Encore/issues/123).**  
**Référence historique complémentaire : [analyse des écarts NS2 puis NS1 du 20/11](./EDEN_ENCORE_GAP_ANALYSIS_NS2_THEN_NS1_2026-11-20.md).**

## 0. Provenance et règle de mise à jour

| Élément | Révision / source |
| --- | --- |
| Moteur `main` à la création de ce registre | `a59cae85eb1dd7246f5648b46e6fddceb736a5a6` |
| Vendor gitlink sélectionné | `546e1aa34d2ff183dd4c737f9da8fbf4a62be24e` |
| Vendor `main` à la création | `546e1aa34d2ff183dd4c737f9da8fbf4a62be24e` |
| SwitchBrew GSV | https://www.switchbrew.org/wiki/Switch_2%3A_GSV_services — consultation 2026-11-21 |
| SwitchBrew NV services | https://www.switchbrew.org/wiki/NV_services — consultation 2026-11-21 |
| Client SDK recroisé | https://github.com/vexcited/fefw — notamment `src/nn/gpu/gpu_sdk_*.cpp` |
| Validation console du présent couple | **Aucune** : pas de build PS5, pas de première soumission/frame revendiquée |

**Codes** : **C** = implémentation C++ active et cohérente au niveau source/CI hôte ; **P** = partielle, contrat fusionné ou divergence ABI/nomenclature à revoir ; **M** = commande connue mais pas de handler actif ; **U** = ID connu mais nom/ABI/sémantique publique insuffisante ; **V** = variante de version non couverte intentionnellement tant que le firmware invité cible ne la requiert pas.  
**Tous les C/P restent console-non-qualifiés** tant qu’un build PS5 représentatif ne les a pas exercés.

### Politique des fonctions connues mais non implémentées

Une commande connue peut recevoir un **handler nommé** afin que la couverture soit explicite, avec un commentaire du type `// not implemented yet on Encore`, **mais elle ne doit jamais retourner un faux `Success`**. Tant que son effet réel n’est pas implémenté, elle doit répondre `NotImplemented`, `InvalidState` ou une erreur plus précise adaptée au contrat. Les commandes dont même le format d’entrée est inconnu restent sans lecture de payload plutôt que de deviner une ABI.

## 1. UserSession GSV — liste SwitchBrew complète

État initial : 142 commandes recensées ; C=27, P=26, M=72, U=17. Les divergences de nom sont volontairement visibles : elles signalent les endroits où la simple présence d’un handler ne suffit pas.

| Cmd | Interface | Nom SwitchBrew | Statut | Handler Encore actif | Écart / raison |
| --- | --- | --- | --- | --- | --- |
| 1 | Gsv | BootWithTransferMemory | C | InitializeWithTransferMemory | handler actif; boot transfert réel, console non qualifiée |
| 4 | Gsv | BootWithRemoteMemory | C | Initialize | handler actif; remote-memory |
| 11 |  | SetCurrentProcessHandle | C | BindProcess | processus natif authentifié |
| 12 |  | (nom inconnu SwitchBrew) | U | — | ID connu, ABI/sémantique insuffisamment documentées |
| 101 |  | CreateContext | P | CompleteBootstrap | ID actif mais sémantique/nomenclature Encore à recroiser |
| 111 | NativeMemory | CreateNativeMemory | C | CreateNativeMemory | actif |
| 112 | NativeMemory | DestroyNativeMemory | C | DestroyNativeMemory | actif |
| 113 | NativeMemory | CreateNativeMemoryBlockByTransferMemory | C | CreateNativeMemoryWithTransferMemory | actif |
| 114 | NativeMemory | CreateNativeMemoryBlock | C | BindNativeMemory | actif; nom Encore différent |
| 115 | NativeMemory | BootNativeMemoryManagement | C | BootNativeMemoryManagement | actif |
| 187 | NativeMemory | QueryNativeMemoryNvsNvRmMemIdForDebug | M | — | aucun handler sélectionné; debug, non P0 |
| 201 | Syncpt | CreateSyncptContext | C | CreateSyncptContext | actif |
| 202 | Syncpt | InitializeSyncptContext | P | OpenSyncptSession | session réelle, nom/contrat à aligner |
| 211 | Syncpt | CreateDebugSyncDevice | M | — | aucun handler |
| 212 | Syncpt | DestroyDebugSyncDevice | M | — | aucun handler |
| 213 | Syncpt | CreateDebugSyncCounter | M | — | aucun handler |
| 214 | Syncpt | DestroyDebugSyncCounter | M | — | aucun handler |
| 215 | Syncpt | ReportDebugSyncCounterValue | M | — | aucun handler |
| 301 | Display | CreateDisplayContext | P | InitializeDisplayContext | ID actif; cycle create/init fusionné ou nomenclature divergente |
| 303 | Display | DestroyDisplayContext | C | FinalizeDisplayContext | actif |
| 305 | Display | InitializeDisplayContext | P | OpenDisplaySession | retour session réel; vérifier ABI version |
| 311 | Display | (nom inconnu) | U | — | ID connu sans contrat public suffisant |
| 312 | Display | (nom inconnu) | U | — | ID connu sans contrat public suffisant |
| 314 | Display | (nom inconnu) | P | DestroyNativeWindowAliasImagePool | handler actif; nom SwitchBrew absent |
| 315 | Display | (nom inconnu) | P | CreateNativeWindowAliasImagePool | handler actif; nom SwitchBrew absent |
| 321 | Display | (nom inconnu) | U | — | pas de handler / contrat insuffisant |
| 327 | Display | (nom inconnu) | U | — | pas de handler / contrat insuffisant |
| 361 | Display | (nom inconnu) | U | — | pas de handler / contrat insuffisant |
| 391 | Display | CalculateRequiredBufferMemory | M | — | pas de handler sélectionné |
| 401 | Gpu | CreateGpuContext | C | InitializeGpuContext | actif; création état GPU |
| 402 | Gpu | InitializeGpuContext | C | ActivateGpuContext | actif |
| 403 | Gpu | DestroyGpuContext | C | DestroyGpuContext | actif |
| 423 | Gpu | (nom inconnu) | P | BindNativeGpuMemory | handler actif; contrat public incomplet |
| 424 | Gpu | (nom inconnu) | U | — | pas de handler / contrat public incomplet |
| 425 | Gpu | (nom inconnu) | U | — | pas de handler / contrat public incomplet |
| 426 | Gpu | MapNativeImage | C | MapNativeGpuImage | actif |
| 427 | Gpu | UnmapNativeImage | C | UnmapNativeGpuImage | actif |
| 428 | Gpu | QueryNativeImage | C | QueryNativeGpuImage | actif |
| 429 | Gpu | CreateNativeImage | C | CreateNativeImage | actif |
| 430 | Gpu | DestroyNativeImage | C | DestroyNativeImage | actif |
| 434 | Gpu | ExistsAddressSpace | P | RegisterGpuAddressSpace | ID actif mais sémantique apparente divergente; audit ABI requis |
| 435 | Gpu | CalculateNativeImageSize | C | CalculateNativeImageSize | actif |
| 437 | Gpu | CreateNativeMemoryWithGpukMemHandle | M | — | pas de handler; ABI connue partiellement, ownership à établir |
| 493 | Gpu | CreateUserlandDebuggerSession | M | — | pas de handler; debug non P0 |
| 494 | Gpu | (nom inconnu) | U | — | pas de handler / contrat insuffisant |
| 496 | Gpu | CreateGpuSessionWithTransferMemory | C | OpenGpuSessionWithTransferMemory | session GPU réelle |
| 497 | Gpu | CreateGpuSessionWithRemoteMemory | C | OpenGpuSession | session GPU réelle |
| 498 | Gpu | TryQueryDonatedTransferMemoryUsage | M | — | pas de handler UserSession |
| 601 | Camera | CreateCameraContext | P | InitializeFeatureContext | ID actif mais create/init fusionné |
| 602 | Camera | InitializeCameraContext | P | OpenCameraContext | session partielle; contrat à aligner |
| 603 | Camera | DestroyCameraContext | M | — | pas de handler |
| 612 | Camera | DestroyOutputBufferPool | M | — | pas de handler |
| 613 | Camera | CreateAliasOutputBufferPool | M | — | pas de handler |
| 614 | Camera | DestroyAliasOutputBufferPool | M | — | pas de handler |
| 615 | Camera | CreateOutputBufferPool | M | — | pas de handler |
| 616 | Camera | ReadFrameDataAsync | M | — | pas de handler UserSession |
| 620 | Camera | InitializeB | M | — | pas de handler |
| 621 | Camera | FinalizeB | M | — | pas de handler |
| 622 | Camera | ListCameras | M | — | pas de handler |
| 623 | Camera | OpenCamera | M | — | pas de handler UserSession; sous-session caméra possède un OpenCamera séparé |
| 624 | Camera | CloseCamera | M | — | pas de handler |
| 626 | Camera | ListSensorMode | M | — | pas de handler |
| 627 | Camera | SetSensorMode | M | — | pas de handler |
| 628 | Camera | GetAvailableStreams | M | — | pas de handler |
| 629 | Camera | GetRequiredWorkBufferSize | M | — | pas de handler |
| 630 | Camera | CreateStream | M | — | pas de handler |
| 632 | Camera | GetReadDoneEvent | M | — | pas de handler |
| 633 | Camera | GetStreamOutputSize | M | — | pas de handler |
| 634 | Camera | DestroyStream | M | — | pas de handler |
| 636 | Camera | ReadFrameDataAsync | M | — | pas de handler |
| 637 | Camera | GetAttachedEvent | M | — | pas de handler |
| 638 | Camera | GetDetachedEvent | M | — | pas de handler |
| 639 | Camera | GetFrameInfo | M | — | pas de handler |
| 640 | Camera | GetFrameInfo2 | M | — | pas de handler |
| 641 | Camera | GetConnectionChangedEvent | M | — | pas de handler |
| 650 | Camera | SetPictureQualityConfig | M | — | pas de handler |
| 651 | Camera | GetPictureQualityConfig | M | — | pas de handler |
| 652 | Camera | SetDigitalWindow | M | — | pas de handler |
| 653 | Camera | GetDigitalWindow | M | — | pas de handler |
| 654 | Camera | GetDigitalWindowCapability | M | — | pas de handler |
| 655 | Camera | GetSupportedFunctions | M | — | pas de handler |
| 656 | Camera | GetSupportedDebugFunctions | M | — | pas de handler |
| 657 | Camera | GetCameraPrivacyCoverStatus | M | — | pas de handler |
| 658 | Camera | GetCameraDeviceTemperature | M | — | pas de handler |
| 659 | Camera | GetDeviceUniqueId | M | — | pas de handler |
| 660 | Camera | GetSensorMode | M | — | pas de handler |
| 661 | Camera | GetStride | M | — | pas de handler |
| 662 | Camera | UnlinkSensor | M | — | pas de handler |
| 663 | Camera | GetDeviceModel | M | — | pas de handler |
| 664 | Camera | SetRawSensorMode | M | — | pas de handler |
| 665 | Camera | GetAccessAllowed | M | — | pas de handler |
| 666 | Camera | GetHostDrivenAeRegion | M | — | pas de handler |
| 667 | Camera | SetHostDrivenAeRegion | M | — | pas de handler |
| 691 | Camera | CalculateImageArraySize | M | — | pas de handler |
| 901 | VideoDecoder | CreateVideoDecoderContext | P | InitializeVideoDecoderContext | ID actif, nom/séquence create/init divergents |
| 902 | VideoDecoder | InitializeVideoDecoderContext | P | OpenVideoDecoderSession | retour session réel; sémantique proche mais nom différent |
| 903 | VideoDecoder | DestroyVideoDecoderContext | M | — | pas de handler UserSession |
| 904 | VideoDecoderForSystem | InitializeVideoDecoderContextForSystem | M | — | pas de handler |
| 905 | VideoDecoder | InitializeVideoDecoderContext2 | P | OpenVideoDecoderSessionWithFlag | handler actif; ABI à comparer |
| 911 | VideoDecoder | InitializeDecoderImagePool | P | CreateVideoImagePool | pool réel, nomenclature différente |
| 912 | VideoDecoder | FinalizeDecoderImagePool | P | DestroyVideoImagePool | pool réel |
| 921 | VideoDecoderForSystem | InitializeDecoderAliasImagePool | M | — | pas de handler |
| 922 | VideoDecoderForSystem | FinalizeDecoderAliasImagePool | M | — | pas de handler |
| 961 | VideoDecoder | (nom inconnu) | P | GetCpuUserImageDescriptor | handler actif; contrat SwitchBrew incomplet |
| 991 | VideoDecoder | (nom inconnu) | P | CalculateDecoderImagePoolBuffer | handler actif; contrat SwitchBrew incomplet |
| 1001 | VideoEncoder | CreateVideoEncoderContext | P | InitializeVideoCodecContext2 | ID actif mais implémentation Encore est decoder-oriented; divergence à résoudre |
| 1002 | VideoEncoder | InitializeVideoEncoderContext | P | OpenVideoDecoderSession2 | ID actif mais retourne actuellement chemin decoder; divergence forte |
| 1003 | VideoEncoder | DestroyVideoEncoderContext | M | — | pas de handler |
| 1004 | VideoEncoderForSystem | InitializeVideoEncoderContextForSystem | M | — | pas de handler |
| 1011 | VideoEncoder | InitializeEncoderImagePool | M | — | pas de handler |
| 1012 | VideoEncoder | FinalizeEncoderImagePool | M | — | pas de handler |
| 1021 | VideoEncoderForSystem | InitializeEncoderAliasImagePool | M | — | pas de handler |
| 1022 | VideoEncoderForSystem | FinalizeEncoderAliasImagePool | M | — | pas de handler |
| 1061 | VideoEncoder | (nom inconnu) | U | — | ID connu sans contrat public suffisant |
| 1091 | VideoEncoder | (nom inconnu) | U | — | ID connu sans contrat public suffisant |
| 1101 | GraphicsFrame | CreateGraphicsFrameContext | C | CreateGraphicsFrameContext | host qualifié |
| 1102 | GraphicsFrame | InitializeGraphicsFrameContext | C | InitializeGraphicsFrameContext | host qualifié |
| 1111 | GraphicsFrame | SetGraphicsFrameLengthMode | C | SetGraphicsFrameLengthMode | valeurs bornées, host qualifié |
| 1112 | GraphicsFrame | SetGraphicsFrameRestartMode | C | SetGraphicsFrameRestartMode | valeurs bornées, host qualifié |
| 1113 | GraphicsFrame | SetGraphicsFrameGpuTimesliceMode | C | SetGraphicsFrameGpuTimesliceMode | valeurs bornées, host qualifié |
| 1201 | Chat | CreateChatContext | P | InitializeChatContext | ID actif, create/init fusionné |
| 1202 | Chat | InitializeChatContext | P | OpenChatSession | session réelle, nom différent |
| 1203 | Chat | DestroyChatContext | M | — | pas de handler |
| 1211 | Chat | CreateImagePool | P | CreateChatImagePool | actif |
| 1212 | Chat | DestroyImagePool | P | DestroyChatImagePool | actif |
| 1291 | Chat | CalculateRequiredBufferMemory | C | CalculateChatImagePoolSize | actif |
| 1301 | Adraw | CreateAdrawContext | M | — | pas de handler |
| 1302 | Adraw | InitializeAdrawContext | M | — | pas de handler |
| 1325 | Adraw | GetAdrawFrameBufferHandle | M | — | pas de handler |
| 1326 | Adraw | GetAdrawImageHandle | M | — | pas de handler |
| 1401 | NvDrv | CreateNvDrv2UserSessionWithTransferMemory | P | OpenNvsrvSessionWithTransferMemory | session NVDRV réelle; nom interne différent |
| 1402 | NvDrv | CreateNvDrv2UserSessionWithRemoteMemory | P | OpenNvsrvSession | session NVDRV réelle |
| 1411 | NvDrv | GetNvDrv2UserTransferMemoryUsage | M | — | pas de handler |
| 1501 | InterModuleImage | CreateInterModuleImageContext | M | — | pas de handler |
| 1502 | InterModuleImage | InitializeInterModuleImageContext | M | — | pas de handler |
| 1510 | InterModuleImage | (nom inconnu) | P | CalculateRequirements | handler actif; fonction SwitchBrew non nommée |
| 1601 |  | (nom inconnu) | U | — | ID connu sans documentation suffisante |
| 1602 |  | (nom inconnu) | U | — | ID connu sans documentation suffisante |
| 1603 |  | (nom inconnu) | U | — | ID connu sans documentation suffisante |
| 1611 |  | (nom inconnu) | U | — | ID connu sans documentation suffisante |
| 1612 |  | (nom inconnu) | U | — | ID connu sans documentation suffisante |
| 1691 |  | (nom inconnu) | U | — | ID connu sans documentation suffisante |


## 2. SyncptSession

SwitchBrew ne nomme publiquement que `Ping`; les autres IDs sont conservés comme inconnus au lieu d’inventer leur contrat.

| Cmd | Nom SwitchBrew | Statut | Handler Encore | Écart / raison |
| --- | --- | --- | --- | --- |
| 0 | Ping | C | Handshake | ping/handshake réel |
| 1 | (nom inconnu) | C | GetCount | ID couvert; sémantique publique incomplète |
| 21 | (nom inconnu) | P | Unknown21 | handler explicite mais fonction inconnue |
| 22 | (nom inconnu) | C | GetSlotEvent | événement réel |
| 103 | (nom inconnu) | C | QueryCounter | compteur réel |
| 201 | (nom inconnu) | C | RequestSlotEvent | événement réel |
| 202 | (nom inconnu) | C | CancelSlotEvent | événement réel |


## 3. DisplaySession

| Cmd | Nom SwitchBrew | Statut | Handler Encore | Écart / raison |
| --- | --- | --- | --- | --- |
| 1 | (SwitchBrew non nommé) | C | GetNotificationLimit | handler sélectionné; console non qualifiée |
| 3 | (SwitchBrew non nommé) | C | GetSessionLimit | handler sélectionné; console non qualifiée |
| 5 | (SwitchBrew non nommé) | C | GetRequestGroupLimit | handler sélectionné; console non qualifiée |
| 11 | (SwitchBrew non nommé) | C | GetNotificationEvent | handler sélectionné; console non qualifiée |
| 13 | (SwitchBrew non nommé) | U | — | pas de handler et sémantique publique insuffisante |
| 21 | (SwitchBrew non nommé) | C | GetNotifications | handler sélectionné; console non qualifiée |
| 31 | (SwitchBrew non nommé) | C | GetVsyncEvent | handler sélectionné; console non qualifiée |
| 32 | (SwitchBrew non nommé) | C | GetDisplayVsyncEvent | handler sélectionné; console non qualifiée |
| 51 | (SwitchBrew non nommé) | C | ConfigureRequestGroups | handler sélectionné; console non qualifiée |
| 53 | (SwitchBrew non nommé) | U | — | pas de handler et sémantique publique insuffisante |
| 101 | (SwitchBrew non nommé) | C | OpenDisplay | handler sélectionné; console non qualifiée |
| 102 | (SwitchBrew non nommé) | C | CloseDisplay | handler sélectionné; console non qualifiée |
| 103 | (SwitchBrew non nommé) | C | QueryDisplayRefreshRate | handler sélectionné; console non qualifiée |
| 104 | (SwitchBrew non nommé) | C | QueryDisplayHdrStatus | handler sélectionné; console non qualifiée |
| 105 | (SwitchBrew non nommé) | C | QueryDisplayHdrPaperWhite | handler sélectionné; console non qualifiée |
| 106 | (SwitchBrew non nommé) | C | GetBufferMaxResolution | handler sélectionné; console non qualifiée |
| 107 | (SwitchBrew non nommé) | U | — | pas de handler et sémantique publique insuffisante |
| 111 | (SwitchBrew non nommé) | C | OpenEndpoint | handler sélectionné; console non qualifiée |
| 112 | (SwitchBrew non nommé) | C | CloseEndpoint | handler sélectionné; console non qualifiée |
| 113 | (SwitchBrew non nommé) | U | — | pas de handler et sémantique publique insuffisante |
| 201 | (SwitchBrew non nommé) | C | RegisterClientState | handler sélectionné; console non qualifiée |
| 202 | (SwitchBrew non nommé) | C | UnregisterClientState | handler sélectionné; console non qualifiée |
| 212 | (SwitchBrew non nommé) | C | GetClientAvailability | handler sélectionné; console non qualifiée |
| 228 | (SwitchBrew non nommé) | C | CancelClientBuffer | handler sélectionné; console non qualifiée |
| 229 | (SwitchBrew non nommé) | C | PresentClientBuffer | handler sélectionné; console non qualifiée |
| 251 | (SwitchBrew non nommé) | C | BindClientDisplay | handler sélectionné; console non qualifiée |
| 252 | (SwitchBrew non nommé) | C | UnbindClientDisplay | handler sélectionné; console non qualifiée |
| 261 | (SwitchBrew non nommé) | C | BindDisplayVsyncEvent | handler sélectionné; console non qualifiée |
| 262 | (SwitchBrew non nommé) | C | UnbindDisplayVsyncEvent | handler sélectionné; console non qualifiée |
| 263 | (SwitchBrew non nommé) | C | BindDisplayRefreshRateEvent | handler sélectionné; console non qualifiée |
| 264 | (SwitchBrew non nommé) | C | UnbindDisplayRefreshRateEvent | handler sélectionné; console non qualifiée |
| 265 | (SwitchBrew non nommé) | C | BindDisplayHdrStatusEvent | handler sélectionné; console non qualifiée |
| 266 | (SwitchBrew non nommé) | C | UnbindDisplayHdrStatusEvent | handler sélectionné; console non qualifiée |
| 267 | (SwitchBrew non nommé) | C | BindDisplayHdrPaperWhiteEvent | handler sélectionné; console non qualifiée |
| 268 | (SwitchBrew non nommé) | C | UnbindDisplayHdrPaperWhiteEvent | handler sélectionné; console non qualifiée |
| 269 | (SwitchBrew non nommé) | C | BindDisplayBufferMaxResolutionEvent | handler sélectionné; console non qualifiée |
| 270 | (SwitchBrew non nommé) | C | UnbindDisplayBufferMaxResolutionEvent | handler sélectionné; console non qualifiée |
| 271 | (SwitchBrew non nommé) | C | BindDisplayModeCapabilityEvent | handler sélectionné; console non qualifiée |
| 272 | (SwitchBrew non nommé) | C | UnbindDisplayModeCapabilityEvent | handler sélectionné; console non qualifiée |
| 301 | (SwitchBrew non nommé) | U | — | pas de handler et sémantique publique insuffisante |
| 302 | (SwitchBrew non nommé) | U | — | pas de handler et sémantique publique insuffisante |
| 351 | (SwitchBrew non nommé) | C | SetClientOutputEncoding | handler sélectionné; console non qualifiée |


**Manquants DisplaySession à ce snapshot** : `13`, `53`, `107`, `113`, `301`, `302`. Comme SwitchBrew ne donne pas leur sémantique dans la table publique, ils restent **U** et ne doivent pas devenir des stubs `Success`.

## 4. VideoDecoderCreatorSession / VideoDecoderSession

Le runtime sélectionne `encore-active/ns2-runtime/video_decoder/.../graphics_video_decoder_session.cpp`. La couverture des IDs documentés est forte, mais la console reste non qualifiée.

| Cmd | Nom SwitchBrew | Statut | Handler Encore | Écart / raison |
| --- | --- | --- | --- | --- |
| 1 | CreateVideoDecoderSession | C | CreateDecoderService | creator/service actif |
| 3 | GetInputEvent | C | GetInputReadyEvent | event réel |
| 6 | Start | C | Start | actif |
| 8 | Flush | C | Stop/Flush | actif |
| 101 | Configure | C | Configure | actif |
| 109 | Decode | C | SubmitInput | FFmpeg/session réelle |
| 115 | FinalizeVideoDecoder | C | Finalize | actif |
| 200 | InitializeVideoDecoderWithTransferMemory | C | Initialize | actif |
| 207 | Stop | C | Stop | actif |
| 210 | InitializeVideoDecoderWithRemoteMemory | M | — | pas de handler explicite |
| 212 | UnbindFrame | C | UnregisterOutputImage | actif |
| 213 | GetFrame | C | GetOutputInfo | actif |
| 311 | BindFrame | C | RegisterOutputImage | actif |
| 314 | DestroyFrame | C | ReleaseOutputImage | actif |
| 400 | Decode2 | C | SubmitInputWithInfo | actif |


**Écart clair** : la commande `210 InitializeVideoDecoderWithRemoteMemory` n’a pas de handler correspondant dans la session active.

## 5. VideoEncoderCreatorSession / VideoEncoderSession

Aucune session encodeur NS2 équivalente n’est actuellement sélectionnée. Les IDs présents dans le **UserSession 1001/1002** sont actuellement raccordés à des chemins decoder-oriented et restent donc **P**, pas une implémentation encodeur.

| Cmd | Nom SwitchBrew | Statut | Handler Encore | Écart / raison |
| --- | --- | --- | --- | --- |
| 1 | CreateVideoEncoderSession | M | — | aucune session encodeur NS2 sélectionnée |
| 4 | GetOutputEvent | M | — | encodeur non implémenté |
| 5 | Start | M | — | encodeur non implémenté |
| 100 | InitializeVideoEncoder | M | — | encodeur non implémenté |
| 101 | Configure | M | — | encodeur non implémenté |
| 102 | GetBufferSize | M | — | encodeur non implémenté |
| 108 | Encode | M | — | encodeur non implémenté |
| 110 | GetBuffer | M | — | encodeur non implémenté |
| 111 | SetParameters | M | — | encodeur non implémenté |
| 112 | FinalizeVideoEncoder | M | — | encodeur non implémenté |
| 206 | Stop | M | — | encodeur non implémenté |


## 6. GpuSession

| Cmd | Nom SwitchBrew | Statut | Handler Encore | Écart / raison |
| --- | --- | --- | --- | --- |
| 11 | GetEventIdRange | C | GetNotificationRange | actif |
| 12 | CreateEvent | C | GetNotificationEvent | actif; nom interne différent |
| 21 | RequestKUserWorkerSession | C | RequestWorker | transport worker réel |
| 22 | GetKUserWorkerSession | C | AcquireWorker | transport worker réel |
| 33 | CreateGpuAddressSpace | C | CreateAddressSpace | AS réel |
| 41 | CreateGraphicsDevice | C | CreateGraphicsDevice | actif |
| 42 | DestroyGraphicsDevice | C | DestroyGraphicsDevice | actif |
| 102 | (nom inconnu) | U | — | ID SwitchBrew sans contrat public suffisant |
| 200 | SynchronizeGpuAddressSpace | C | SynchronizeGpuAddressSpace | ajouté et host qualifié |
| 201 | GetUserPartitionGpuAddress | C | GetUserPartition | actif |
| 202 | GetGsvPartitionGpuAddress | C | GetGsvPartition | actif |


**Extension Encore non publiée dans la table SwitchBrew consultée** : commande `203 GetVaRange`. Elle doit rester identifiée comme extension/contrat local jusqu’à recoupement upstream supplémentaire.

## 7. KUserWorkerSession / nn::gpuk::impl::kuser

La numérotation SwitchBrew change entre 19.x et 20.0+. Le runtime actuel suit le bloc **20.0+ 209–216**. Le client SDK `vexcited/fefw` confirme notamment les requêtes TIPC brutes `0xE1/0xE2`, dont le framework retire l’enveloppe pour dispatcher **209/210**.

| Cmd | Nom SwitchBrew / version | Statut | Handler Encore | Écart / raison |
| --- | --- | --- | --- | --- |
| 101 | CreateGpuMemory | C | CreateGpuAccessibleMemory | mémoire réelle |
| 102 | DestroyGpuMemory | C | DestroyGpuAccessibleMemory | libération + event |
| 171 | EnsureGpuMemoryComptags | C | EnsureGpuMemoryComptags | actif |
| 172 | SetGpuMemoryUserDebugLabel | C | SetGpuMemoryUserDebugLabel | metadata bornée |
| 173 | SetGpuMemorySdkDebugLabel | C | SetGpuMemorySdkDebugLabel | metadata bornée |
| 201 | [19.0.0–19.1.0] NormalMapGpuMemory4K | V | — | ancienne numérotation; non requise pour chemin 20.0+ tant que firmware invité cible confirmé |
| 202 | [19.0.0–19.1.0] NormalUnmapGpuMemory4K | V | — | ancienne numérotation |
| 203 | [19.0.0–19.1.0] CreateSparseRegion | V | — | ancienne numérotation |
| 204 | [19.0.0–19.1.0] DestroySparseRegion | V | — | ancienne numérotation |
| 205 | [19.0.0–19.1.0] ExecuteSparseMapRequests | V | — | ancienne numérotation |
| 207 | [19.0.0–19.1.0] NormalModifyMemoryKind4K | V | — | ancienne numérotation |
| 209 | [20.0.0+] SetGpuSegmentUserDebugLabel | C | SetGpuSegmentUserDebugLabel | actif; ID corrigé après vérification enveloppe TIPC |
| 210 | [20.0.0+] SetGpuSegmentSdkDebugLabel | C | SetGpuSegmentSdkDebugLabel | actif |
| 211 | [20.0.0+] NormalMapGpuMemory4K | C | NormalMapGpuMemory4K | GMMU réel |
| 212 | [20.0.0+] NormalModifyMemoryKind4K | C | NormalModifyGpuMemory4K | actif |
| 213 | [20.0.0+] NormalUnmapGpuMemory4K | C | NormalUnmapGpuMemory4K | actif |
| 214 | [20.0.0+] CreateSparseRegion | C | CreateSparseRegion | sparse réel |
| 215 | [20.0.0+] DestroySparseRegion | C | DestroySparseRegion | actif |
| 216 | [20.0.0+] ExecuteSparseMapRequests | C | ExecuteSparseMapRequests | actif |


## 8. NVDRV — /dev/nvhost-as-gpu

| Ioctl | Nom SwitchBrew | Statut | Handler Encore | Écart / raison |
| --- | --- | --- | --- | --- |
| 0x40044101 | NVGPU_AS_IOCTL_BIND_CHANNEL | C | BindChannel | actif |
| 0xC0184102 | NVGPU_AS_IOCTL_ALLOC_SPACE | C | AllocateSpace | actif |
| 0xC0104103 | NVGPU_AS_IOCTL_FREE_SPACE | C | FreeSpace | actif |
| 0xC0184104 | NVGPU_AS_IOCTL_MAP_BUFFER | C | MapBuffer | actif |
| 0xC0084105 | NVGPU_AS_IOCTL_UNMAP_BUFFER | C | UnmapBuffer | actif |
| 0xC0284106 | NVGPU_AS_IOCTL_MAP_BUFFER_EX | C | MapBufferEx | actif |
| 0x40104107 | NVGPU_AS_IOCTL_ALLOC_AS | C | AllocateAs | actif |
| 0xC0404108 | NVGPU_AS_IOCTL_GET_VA_REGIONS | C | GetVARegions | actif |
| 0x40284109 | NVGPU_AS_IOCTL_ALLOC_AS_EX | C | AllocateAsEx | actif |
| 0xC038410A | NVGPU_AS_IOCTL_MAP_BUFFER_EX2 | C | MapBufferEx2 | actif |


## 9. NVDRV — /dev/nvhost-ctrl-gpu, points S2

| Ioctl | Nom SwitchBrew | Statut | Handler Encore | Écart / raison |
| --- | --- | --- | --- | --- |
| 0xC0E04705 | [S2] NVGPU_GPU_IOCTL_GET_CHARACTERISTICS | C | GetCharacteristics native | layout S2 224 octets pris en charge |
| 0xC0084710 | [S2] NVGPU_GPU_IOCTL_WAIT_FOR_PAUSE | M | — | aucun handler natif |
| 0x80084712 | NVGPU_GPU_IOCTL_NUM_VSMS | C | NUM_VSMS | profil GA10F cohérent |
| 0xC0084713 | [S2] NVGPU_GPU_IOCTL_VSMS_MAPPING | C | VSMS_MAPPING | inline mapping GA10F |
| 0xC010471E | [S2] NVGPU_GPU_IOCTL_SET_DETERMINISTIC_OPTS | M | — | aucun handler |
| 0xC010471F | [S2] NVGPU_GPU_IOCTL_GET_ENGINE_INFO | C | GET_ENGINE_INFO | runlists graphics/copy exposés |


Les autres ioctls de contrôle hérités de Switch 1 restent suivis par les audits existants ; ce tableau met en avant les formes S2 ou modifiées S2 directement pertinentes.

## 10. NVDRV — /dev/nvhost-gpu / channel

| Ioctl | Nom SwitchBrew | Statut | Handler Encore | Écart / raison |
| --- | --- | --- | --- | --- |
| 0xC0??0001 | NVHOST_IOCTL_CHANNEL_SUBMIT | C/P | Submit | chemin historique, à qualifier séparément pour native |
| 0xC0080002 | NVHOST_IOCTL_CHANNEL_GET_SYNCPOINT | C | GetSyncpoint | actif |
| 0xC0080003 | NVHOST_IOCTL_CHANNEL_GET_WAITBASE | C | GetWaitbase | actif |
| 0xC0080004 | NVHOST_IOCTL_CHANNEL_GET_MODMUTEX | M | — | pas de case sélectionné |
| 0x40040007 | NVHOST_IOCTL_CHANNEL_SET_SUBMIT_TIMEOUT | M | — | pas de case sélectionné |
| 0xC0080023 | NVHOST_IOCTL_CHANNEL_GET_CLK_RATE | M | — | pas de case sélectionné |
| 0x40104812 | [S2] NVGPU_IOCTL_CHANNEL_EVENT_ID_CONTROL | M | — | pas de handler S2 |
| 0xC0104813 | NVGPU_IOCTL_CHANNEL_CYCLE_STATS_SNAPSHOT | M | — | pas de handler |
| 0x40084714 | NVGPU_IOCTL_CHANNEL_SET_USER_DATA | C | SetClientData | actif |
| 0x80084715 | NVGPU_IOCTL_CHANNEL_GET_USER_DATA | C | GetClientData | actif |
| 0x80804816 | NVGPU_IOCTL_CHANNEL_GET_ERROR_INFO | M | — | pas de handler |
| 0xC0104817 | NVGPU_IOCTL_CHANNEL_GET_ERROR_NOTIFICATION | M | — | pas de handler |
| 0x40204818 | NVGPU_IOCTL_CHANNEL_ALLOC_GPFIFO_EX | C | AllocGPFIFOEx | actif |
| 0xC0??4819 | NVGPU_IOCTL_CHANNEL_SUBMIT_GPFIFO_RETRY | M | — | pas de handler dédié |
| 0xC020481A | NVGPU_IOCTL_CHANNEL_ALLOC_GPFIFO_EX2 | C | AllocGPFIFOEx2 | actif |
| 0xC018481B | NVGPU_IOCTL_CHANNEL_SUBMIT_GPFIFO2 | C | SubmitGPFIFO | actif |
| 0xC018481C | NVGPU_IOCTL_CHANNEL_SUBMIT_GPFIFO2_RETRY | M | — | pas de handler dédié |
| 0xC004481D | NVGPU_IOCTL_CHANNEL_SET_TIMESLICE | C | SetChannelTimeslice | actif |
| 0xC010481E | [S2] NVGPU_IOCTL_CHANNEL_GET_USER_SYNCPOINT | C | GetUserSyncpoint | actif, valeur courante + shim GMMU |
| 0xC008481F | [S2] NVGPU_IOCTL_CHANNEL_SET_PREEMPTION_MODE | C | SetPreemptionMode | actif |
| 0x40044820 | [S2] NVGPU_IOCTL_CHANNEL_OPEN | C | ChannelOpen | runlist authentifié |
| 0xC0504821 | [S2] NVGPU_IOCTL_CHANNEL_SETUP_BIND | P | ChannelSetupBind | kernel-submit implémenté; USERD/doorbell explicitement NotImplemented |


**P0 actuel** : `0xC0504821 CHANNEL_SETUP_BIND` est volontairement **P**. Le mode kernel-submit initialise un vrai `ChannelState` après validation propriétaire/GMMU/runlist ; le mode userland `USERD/GPFIFO + doorbell` reste `NotImplemented` tant que les buffers invités, leur durée de vie et le mécanisme de notification GPU ne sont pas réellement modélisés.

## 11. NVDRV — /dev/nvhost-tsg-gpu

| Ioctl | Nom SwitchBrew | Statut | Handler Encore | Écart / raison |
| --- | --- | --- | --- | --- |
| 0xC0045401 | NVGPU_TSG_IOCTL_BIND_CHANNEL | C | BindTsgChannel | owner process vérifié |
| 0xC0045402 | NVGPU_TSG_IOCTL_UNBIND_CHANNEL | C | Unbind | actif |
| 0x00005403 | NVGPU_TSG_IOCTL_ENABLE | M | — | connu, pas de scheduling réel; doit rester NotImplemented |
| 0x00005404 | NVGPU_TSG_IOCTL_DISABLE | M | — | connu, pas de scheduling réel |
| 0x00005405 | NVGPU_TSG_IOCTL_PREEMPT | M | — | connu, préemption réelle absente |
| 0xC0085407 | NVGPU_TSG_IOCTL_SET_RUNLIST_INTERLEAVE | M | — | pas de handler |
| 0xC0045408 | NVGPU_TSG_IOCTL_SET_TIMESLICE | M | — | pas de handler TSG |
| 0xC0105409 | NVGPU_TSG_IOCTL_EVENT_ID_CTRL | M | — | pas de handler/event réel |
| 0x8004540A | NVGPU_TSG_IOCTL_GET_TIMESLICE | M | — | pas de handler |
| 0xC018540B | NVGPU_TSG_IOCTL_BIND_CHANNEL_EX | C | BindTsgChannel extended | FD + VEID validés |
| 0xC018540C | NVGPU_TSG_IOCTL_READ_SINGLE_SM_ERROR_STATE | M | — | pas de handler |
| 0xC008540D | NVGPU_TSG_IOCTL_SET_L2_SECTOR_PROMOTION | M | — | pas de handler |


Les commandes `ENABLE/DISABLE/PREEMPT` ne doivent surtout pas être converties en `Success` vide : elles modifient l’état du scheduler/runlist et peuvent provoquer un blocage GPU silencieux si elles sont faussement acquittées.

## 12. NVDRV — /dev/nvhost-prof-dev-gpu

| Ioctl | Nom SwitchBrew | Statut | Handler Encore | Écart / raison |
| --- | --- | --- | --- | --- |
| 0x40085001 | NVGPU_PROFILER_IOCTL_BIND_CONTEXT | M | — | device profiler S2 non implémenté dans le runtime actif |
| 0x40105002 | NVGPU_PROFILER_IOCTL_RESERVE_PM_RESOURCE | M | — | device profiler S2 non implémenté dans le runtime actif |
| 0x40085003 | NVGPU_PROFILER_IOCTL_RELEASE_PM_RESOURCE | M | — | device profiler S2 non implémenté dans le runtime actif |
| 0xC0305004 | NVGPU_PROFILER_IOCTL_ALLOC_PMA_STREAM | M | — | device profiler S2 non implémenté dans le runtime actif |
| 0x00005005 | NVGPU_PROFILER_IOCTL_FREE_PMA_STREAM | M | — | device profiler S2 non implémenté dans le runtime actif |
| 0x00005006 | NVGPU_PROFILER_IOCTL_BIND_PM_RESOURCES | M | — | device profiler S2 non implémenté dans le runtime actif |
| 0x00005007 | NVGPU_PROFILER_IOCTL_UNBIND_PM_RESOURCES | M | — | device profiler S2 non implémenté dans le runtime actif |
| 0xC0285008 | NVGPU_PROFILER_IOCTL_PMA_STREAM_UPDATE_GET_PUT | M | — | device profiler S2 non implémenté dans le runtime actif |
| 0xC0205009 | NVGPU_PROFILER_IOCTL_EXEC_REG_OPS | M | — | device profiler S2 non implémenté dans le runtime actif |
| 0x0000500A | NVGPU_PROFILER_IOCTL_UNBIND_CONTEXT | M | — | device profiler S2 non implémenté dans le runtime actif |
| 0x4010500B | NVGPU_PROFILER_IOCTL_VAB_RESERVE | M | — | device profiler S2 non implémenté dans le runtime actif |
| 0x0000500C | NVGPU_PROFILER_IOCTL_VAB_RELEASE | M | — | device profiler S2 non implémenté dans le runtime actif |
| 0x4010500D | NVGPU_PROFILER_IOCTL_VAB_FLUSH_STATE | M | — | device profiler S2 non implémenté dans le runtime actif |


Ces commandes sont documentées par SwitchBrew mais restent **hors P0 boot/gameplay** tant qu’aucun titre retail ne prouve leur usage. Elles doivent rester explicitement non implémentées plutôt que recevoir des succès génériques.

## 13. Debug/profiler et commandes S2 sans nom public

SwitchBrew publie aussi des ioctls S2 `/dev/nvhost-dbg-gpu` dont plusieurs n’ont pas encore de nom (`0x4008441F`, `0x00004420`, `0xC0184421`, `0xC0184429`, `0x4010442A`, `0x4010442B`) ainsi que des variantes S2 nommées pour MMU/SM/HWPM. **Statut initial Encore : M/U** sauf preuve contraire future. Ils ne sont pas prioritaires pour MKW/Bananza et ne doivent pas détourner du chemin GSV→NVDRV→GPFIFO.

## 14. Écarts structurels les plus importants à traiter

1. **P0 GPU submission** : compléter/valider le mode USERD de `CHANNEL_SETUP_BIND` seulement avec une vraie propriété des buffers et un mécanisme de doorbell ; ne pas le simuler.
2. **TSG scheduler** : `ENABLE/DISABLE/PREEMPT`, runlist interleave, timeslice/event control sont connus mais pas implémentés. Vérifier d’abord lesquels sont réellement appelés par le runtime retail avant de développer.
3. **GSV GPU** : `437 CreateNativeMemoryWithGpukMemHandle`, `498 TryQueryDonatedTransferMemoryUsage` et la divergence `434 ExistsAddressSpace` / `RegisterGpuAddressSpace` méritent une revue ABI.
4. **Vidéo** : décodeur largement couvert ; `210 remote-memory` manque. **Encodeur** pratiquement absent, et les IDs UserSession `1001/1002` sont raccordés à un chemin qui ressemble encore au décodeur.
5. **Display** : six IDs publiés sans sémantique suffisante restent U.
6. **Camera/Adraw/InterModuleImage** : nombreuses commandes connues mais non implémentées ; priorité basse tant qu’elles ne bloquent pas un titre retail.
7. **Version 19.x worker** : commandes 201–205/207 à implémenter seulement si le firmware invité réellement ciblé les exige ; la présence d’une ancienne numérotation SwitchBrew n’est pas un bug en soi.

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
- indiquer le handler/source réellement sélectionné ;
- ajouter le run GitHub hôte pertinent ;
- laisser la validation console à **non qualifiée** jusqu’au test PS5 réel.

Ce registre est le tableau de complétude NS2 de référence à partir du 21/11 ; l’audit du 20/11 reste une photographie historique plus large.
