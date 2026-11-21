# NS1 — Catalogue des fonctions Horizon / SwitchBrew et couverture Eden Encore

**Vérification : 2026-11-21 (Europe/Paris).** Branche `opt/ns1-fc27-runtime-20261121` ; moteur `5bef0df2b23f650b470659e928e3682cf2db3916` ; vendor `b8883667410054db189d00b3a5144088f47d3af9`. Aucun résultat de console PS5 n'est déduit de cette table.

> **Portée** : liste de référence exhaustive des entrées de la table SVC du miroir SwitchBrew consulté, index de familles de services IPC, et inventaire des lacunes déjà identifiées. Les commandes IPC seront classées une à une lors du croisement des interfaces C++ actives. Une déclaration/registration ne signifie jamais « implémenté ».

## Sources et version du référentiel

- [SwitchBrew SVC](https://switchbrew.org/wiki/SVC), [miroir technique](https://github.com/backupbrew/switchbrew/blob/master/SVC.md) (blob `74ea4faf68e8a59bf4c2243a110f3a695e794bd8`).
- [SwitchBrew Services API](https://switchbrew.org/wiki/Services_API), [miroir technique](https://github.com/backupbrew/switchbrew/blob/master/Services%20API.md) (blob `cd6490d27b0e383a6fac90273611d791f6926320`).
- [Énumération SVC Eden `svc.h`](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/b8883667410054db189d00b3a5144088f47d3af9/sources/eden/src/core/hle/kernel/svc.h) (blob `d1e02ec0bc83b538a7f372624958f7ed63bf1c37`).
- Répertoire `sources/eden/src/core/hle/kernel/svc` : **37 unités C++** ; **6 unités prioritaires** inspectées pour le premier classement, les autres **non qualifiées**.

Le miroir SwitchBrew n'est pas nécessairement à jour pour toutes les versions HOS ; les évolutions récentes de la page live, notamment **S1/S2**, devront être rapprochées séparément. **Aucune commande exclusive Switch 2 ne doit être comptée NS1.**

## Statuts (ne pas confondre source et gameplay)

| Code | Signification |
|---|---|
| **D** | Non implémenté explicite / rejet confirmé dans un corps C++ inspecté |
| **P** | Stub, support partiel ou réponse simulée avec limites connues |
| **Q** | ID ou fonction présente, mais réalisation, source compilée, ABI ou résultat non qualifiés |
| **E** | ID absent de l'énumération examinée, sans preuve d'absence du runtime complet |
| **C** | Correctif source actif et tests hôtes : console non prouvée |
| **V** | ELF exact, installation et résultat PS5 représentatif documentés |

**Politique de stub** : commenter `// Not implemented yet on Encore: <motif/contrat>` si utile ; ne jamais retourner `ResultSuccess` ou `0` pour une opération non réalisée (mapping, registres, sécurité, cache, GPU). Pour un `void`, ne rendre no-op que si le contrat l'autorise. Une fonction de retour facultatif peut indiquer l'absence de capacité selon l'ABI. Aucun stub factice ne doit masquer un nouveau blocage.

## Tableau SVC — 117 entrées documentées par le snapshot

| ID | Fonction | État | Référence de base et motif | Vérifié |
|---|---|---|---|---|
| `0x01` | [`svcSetHeapSize`](https://switchbrew.org/wiki/SVC#svcSetHeapSize) | **Q** | Dispatch énuméré ; corps non contrôlé dans ce lot | 2026-11-21 |
| `0x02` | [`svcSetMemoryPermission`](https://switchbrew.org/wiki/SVC#svcSetMemoryPermission) | **Q** | Dispatch énuméré ; corps non contrôlé dans ce lot | 2026-11-21 |
| `0x03` | [`svcSetMemoryAttribute`](https://switchbrew.org/wiki/SVC#svcSetMemoryAttribute) | **Q** | Dispatch énuméré ; corps non contrôlé dans ce lot | 2026-11-21 |
| `0x04` | [`svcMapMemory`](https://switchbrew.org/wiki/SVC#svcMapMemory) | **Q** | Dispatch énuméré ; corps non contrôlé dans ce lot | 2026-11-21 |
| `0x05` | [`svcUnmapMemory`](https://switchbrew.org/wiki/SVC#svcUnmapMemory) | **Q** | Dispatch énuméré ; corps non contrôlé dans ce lot | 2026-11-21 |
| `0x06` | [`svcQueryMemory`](https://switchbrew.org/wiki/SVC#svcQueryMemory) | **Q** | Dispatch énuméré ; corps non contrôlé dans ce lot | 2026-11-21 |
| `0x07` | [`svcExitProcess`](https://switchbrew.org/wiki/SVC#svcExitProcess) | **Q** | Dispatch énuméré ; corps non contrôlé dans ce lot | 2026-11-21 |
| `0x08` | [`svcCreateThread`](https://switchbrew.org/wiki/SVC#svcCreateThread) | **Q** | Dispatch énuméré ; corps non contrôlé dans ce lot | 2026-11-21 |
| `0x09` | [`svcStartThread`](https://switchbrew.org/wiki/SVC#svcStartThread) | **Q** | Dispatch énuméré ; corps non contrôlé dans ce lot | 2026-11-21 |
| `0x0A` | [`svcExitThread`](https://switchbrew.org/wiki/SVC#svcExitThread) | **Q** | Dispatch énuméré ; corps non contrôlé dans ce lot | 2026-11-21 |
| `0x0B` | [`svcSleepThread`](https://switchbrew.org/wiki/SVC#svcSleepThread) | **Q** | Dispatch énuméré ; corps non contrôlé dans ce lot | 2026-11-21 |
| `0x0C` | [`svcGetThreadPriority`](https://switchbrew.org/wiki/SVC#svcGetThreadPriority) | **Q** | Dispatch énuméré ; corps non contrôlé dans ce lot | 2026-11-21 |
| `0x0D` | [`svcSetThreadPriority`](https://switchbrew.org/wiki/SVC#svcSetThreadPriority) | **Q** | Dispatch énuméré ; corps non contrôlé dans ce lot | 2026-11-21 |
| `0x0E` | [`svcGetThreadCoreMask`](https://switchbrew.org/wiki/SVC#svcGetThreadCoreMask) | **Q** | Dispatch énuméré ; corps non contrôlé dans ce lot | 2026-11-21 |
| `0x0F` | [`svcSetThreadCoreMask`](https://switchbrew.org/wiki/SVC#svcSetThreadCoreMask) | **Q** | Dispatch énuméré ; corps non contrôlé dans ce lot | 2026-11-21 |
| `0x10` | [`svcGetCurrentProcessorNumber`](https://switchbrew.org/wiki/SVC#svcGetCurrentProcessorNumber) | **Q** | Dispatch énuméré ; corps non contrôlé dans ce lot | 2026-11-21 |
| `0x11` | [`svcSignalEvent`](https://switchbrew.org/wiki/SVC#svcSignalEvent) | **Q** | Dispatch énuméré ; corps non contrôlé dans ce lot | 2026-11-21 |
| `0x12` | [`svcClearEvent`](https://switchbrew.org/wiki/SVC#svcClearEvent) | **Q** | Dispatch énuméré ; corps non contrôlé dans ce lot | 2026-11-21 |
| `0x13` | [`svcMapSharedMemory`](https://switchbrew.org/wiki/SVC#svcMapSharedMemory) | **Q** | Dispatch énuméré ; corps non contrôlé dans ce lot | 2026-11-21 |
| `0x14` | [`svcUnmapSharedMemory`](https://switchbrew.org/wiki/SVC#svcUnmapSharedMemory) | **Q** | Dispatch énuméré ; corps non contrôlé dans ce lot | 2026-11-21 |
| `0x15` | [`svcCreateTransferMemory`](https://switchbrew.org/wiki/SVC#svcCreateTransferMemory) | **Q** | Dispatch énuméré ; corps non contrôlé dans ce lot | 2026-11-21 |
| `0x16` | [`svcCloseHandle`](https://switchbrew.org/wiki/SVC#svcCloseHandle) | **Q** | Dispatch énuméré ; corps non contrôlé dans ce lot | 2026-11-21 |
| `0x17` | [`svcResetSignal`](https://switchbrew.org/wiki/SVC#svcResetSignal) | **Q** | Dispatch énuméré ; corps non contrôlé dans ce lot | 2026-11-21 |
| `0x18` | [`svcWaitSynchronization`](https://switchbrew.org/wiki/SVC#svcWaitSynchronization) | **Q** | Dispatch énuméré ; corps non contrôlé dans ce lot | 2026-11-21 |
| `0x19` | [`svcCancelSynchronization`](https://switchbrew.org/wiki/SVC#svcCancelSynchronization) | **Q** | Dispatch énuméré ; corps non contrôlé dans ce lot | 2026-11-21 |
| `0x1A` | [`svcArbitrateLock`](https://switchbrew.org/wiki/SVC#svcArbitrateLock) | **Q** | Dispatch énuméré ; corps non contrôlé dans ce lot | 2026-11-21 |
| `0x1B` | [`svcArbitrateUnlock`](https://switchbrew.org/wiki/SVC#svcArbitrateUnlock) | **Q** | Dispatch énuméré ; corps non contrôlé dans ce lot | 2026-11-21 |
| `0x1C` | [`svcWaitProcessWideKeyAtomic`](https://switchbrew.org/wiki/SVC#svcWaitProcessWideKeyAtomic) | **Q** | Dispatch énuméré ; corps non contrôlé dans ce lot | 2026-11-21 |
| `0x1D` | [`svcSignalProcessWideKey`](https://switchbrew.org/wiki/SVC#svcSignalProcessWideKey) | **Q** | Dispatch énuméré ; corps non contrôlé dans ce lot | 2026-11-21 |
| `0x1E` | [`svcGetSystemTick`](https://switchbrew.org/wiki/SVC#svcGetSystemTick) | **Q** | Dispatch énuméré ; corps non contrôlé dans ce lot | 2026-11-21 |
| `0x1F` | [`svcConnectToNamedPort`](https://switchbrew.org/wiki/SVC#svcConnectToNamedPort) | **Q** | Dispatch énuméré ; corps non contrôlé dans ce lot | 2026-11-21 |
| `0x20` | [`svcSendSyncRequestLight`](https://switchbrew.org/wiki/SVC#svcSendSyncRequestLight) | **Q** | Dispatch énuméré ; corps non contrôlé dans ce lot | 2026-11-21 |
| `0x21` | [`svcSendSyncRequest`](https://switchbrew.org/wiki/SVC#svcSendSyncRequest) | **Q** | Dispatch énuméré ; corps non contrôlé dans ce lot | 2026-11-21 |
| `0x22` | [`svcSendSyncRequestWithUserBuffer`](https://switchbrew.org/wiki/SVC#svcSendSyncRequestWithUserBuffer) | **Q** | Dispatch énuméré ; corps non contrôlé dans ce lot | 2026-11-21 |
| `0x23` | [`svcSendAsyncRequestWithUserBuffer`](https://switchbrew.org/wiki/SVC#svcSendAsyncRequestWithUserBuffer) | **Q** | Dispatch énuméré ; corps non contrôlé dans ce lot | 2026-11-21 |
| `0x24` | [`svcGetProcessId`](https://switchbrew.org/wiki/SVC#svcGetProcessId) | **Q** | Dispatch énuméré ; corps non contrôlé dans ce lot | 2026-11-21 |
| `0x25` | [`svcGetThreadId`](https://switchbrew.org/wiki/SVC#svcGetThreadId) | **Q** | Dispatch énuméré ; corps non contrôlé dans ce lot | 2026-11-21 |
| `0x26` | [`svcBreak`](https://switchbrew.org/wiki/SVC#svcBreak) | **Q** | Dispatch énuméré ; corps non contrôlé dans ce lot | 2026-11-21 |
| `0x27` | [`svcOutputDebugString`](https://switchbrew.org/wiki/SVC#svcOutputDebugString) | **Q** | Dispatch énuméré ; corps non contrôlé dans ce lot | 2026-11-21 |
| `0x28` | [`svcReturnFromException`](https://switchbrew.org/wiki/SVC#svcReturnFromException) | **Q** | Dispatch énuméré ; corps non contrôlé dans ce lot | 2026-11-21 |
| `0x29` | [`svcGetInfo`](https://switchbrew.org/wiki/SVC#svcGetInfo) | **Q** | Dispatch énuméré ; corps non contrôlé dans ce lot | 2026-11-21 |
| `0x2A` | [`svcFlushEntireDataCache`](https://switchbrew.org/wiki/SVC#svcFlushEntireDataCache) | **D** | Opérations de cohérence cache non réalisées ; pas de no-op de succès | 2026-11-21 |
| `0x2B` | [`svcFlushDataCache`](https://switchbrew.org/wiki/SVC#svcFlushDataCache) | **D** | Opérations de cohérence cache non réalisées ; pas de no-op de succès | 2026-11-21 |
| `0x2C` | [`svcMapPhysicalMemory`](https://switchbrew.org/wiki/SVC#svcMapPhysicalMemory) | **Q** | Dispatch énuméré ; corps non contrôlé dans ce lot | 2026-11-21 |
| `0x2D` | [`svcUnmapPhysicalMemory`](https://switchbrew.org/wiki/SVC#svcUnmapPhysicalMemory) | **Q** | Dispatch énuméré ; corps non contrôlé dans ce lot | 2026-11-21 |
| `0x2E` | [`svcGetDebugFutureThreadInfo`](https://switchbrew.org/wiki/SVC#svcGetDebugFutureThreadInfo) | **Q** | Dispatch énuméré ; corps non contrôlé dans ce lot | 2026-11-21 |
| `0x2F` | [`svcGetLastThreadInfo`](https://switchbrew.org/wiki/SVC#svcGetLastThreadInfo) | **Q** | Dispatch énuméré ; corps non contrôlé dans ce lot | 2026-11-21 |
| `0x30` | [`svcGetResourceLimitLimitValue`](https://switchbrew.org/wiki/SVC#svcGetResourceLimitLimitValue) | **Q** | Dispatch énuméré ; corps non contrôlé dans ce lot | 2026-11-21 |
| `0x31` | [`svcGetResourceLimitCurrentValue`](https://switchbrew.org/wiki/SVC#svcGetResourceLimitCurrentValue) | **Q** | Dispatch énuméré ; corps non contrôlé dans ce lot | 2026-11-21 |
| `0x32` | [`svcSetThreadActivity`](https://switchbrew.org/wiki/SVC#svcSetThreadActivity) | **Q** | Dispatch énuméré ; corps non contrôlé dans ce lot | 2026-11-21 |
| `0x33` | [`svcGetThreadContext3`](https://switchbrew.org/wiki/SVC#svcGetThreadContext3) | **Q** | Dispatch énuméré ; corps non contrôlé dans ce lot | 2026-11-21 |
| `0x34` | [`svcWaitForAddress`](https://switchbrew.org/wiki/SVC#svcWaitForAddress) | **Q** | Dispatch énuméré ; corps non contrôlé dans ce lot | 2026-11-21 |
| `0x35` | [`svcSignalToAddress`](https://switchbrew.org/wiki/SVC#svcSignalToAddress) | **Q** | Dispatch énuméré ; corps non contrôlé dans ce lot | 2026-11-21 |
| `0x36` | [`svcSynchronizePreemptionState`](https://switchbrew.org/wiki/SVC#svcSynchronizePreemptionState) | **Q** | Dispatch énuméré ; corps non contrôlé dans ce lot | 2026-11-21 |
| `0x3C` | [`svcKernelDebug`](https://switchbrew.org/wiki/SVC#svcKernelDebug) | **Q** | Dispatch énuméré ; corps non contrôlé dans ce lot | 2026-11-21 |
| `0x3D` | [`svcChangeKernelTraceState`](https://switchbrew.org/wiki/SVC#svcChangeKernelTraceState) | **Q** | Dispatch énuméré ; corps non contrôlé dans ce lot | 2026-11-21 |
| `0x40` | [`svcCreateSession`](https://switchbrew.org/wiki/SVC#svcCreateSession) | **Q** | Dispatch énuméré ; corps non contrôlé dans ce lot | 2026-11-21 |
| `0x41` | [`svcAcceptSession`](https://switchbrew.org/wiki/SVC#svcAcceptSession) | **Q** | Dispatch énuméré ; corps non contrôlé dans ce lot | 2026-11-21 |
| `0x42` | [`svcReplyAndReceiveLight`](https://switchbrew.org/wiki/SVC#svcReplyAndReceiveLight) | **Q** | Dispatch énuméré ; corps non contrôlé dans ce lot | 2026-11-21 |
| `0x43` | [`svcReplyAndReceive`](https://switchbrew.org/wiki/SVC#svcReplyAndReceive) | **Q** | Dispatch énuméré ; corps non contrôlé dans ce lot | 2026-11-21 |
| `0x44` | [`svcReplyAndReceiveWithUserBuffer`](https://switchbrew.org/wiki/SVC#svcReplyAndReceiveWithUserBuffer) | **Q** | Dispatch énuméré ; corps non contrôlé dans ce lot | 2026-11-21 |
| `0x45` | [`svcCreateEvent`](https://switchbrew.org/wiki/SVC#svcCreateEvent) | **Q** | Dispatch énuméré ; corps non contrôlé dans ce lot | 2026-11-21 |
| `0x48` | [`svcMapPhysicalMemoryUnsafe`](https://switchbrew.org/wiki/SVC#svcMapPhysicalMemoryUnsafe) | **Q** | Dispatch énuméré ; corps non contrôlé dans ce lot | 2026-11-21 |
| `0x49` | [`svcUnmapPhysicalMemoryUnsafe`](https://switchbrew.org/wiki/SVC#svcUnmapPhysicalMemoryUnsafe) | **Q** | Dispatch énuméré ; corps non contrôlé dans ce lot | 2026-11-21 |
| `0x4A` | [`svcSetUnsafeLimit`](https://switchbrew.org/wiki/SVC#svcSetUnsafeLimit) | **Q** | Dispatch énuméré ; corps non contrôlé dans ce lot | 2026-11-21 |
| `0x4B` | [`svcCreateCodeMemory`](https://switchbrew.org/wiki/SVC#svcCreateCodeMemory) | **Q** | Dispatch énuméré ; corps non contrôlé dans ce lot | 2026-11-21 |
| `0x4C` | [`svcControlCodeMemory`](https://switchbrew.org/wiki/SVC#svcControlCodeMemory) | **Q** | Dispatch énuméré ; corps non contrôlé dans ce lot | 2026-11-21 |
| `0x4D` | [`svcSleepSystem`](https://switchbrew.org/wiki/SVC#svcSleepSystem) | **Q** | Dispatch énuméré ; corps non contrôlé dans ce lot | 2026-11-21 |
| `0x4E` | [`svcReadWriteRegister`](https://switchbrew.org/wiki/SVC#svcReadWriteRegister) | **D** | Registres matériels privilégiés : sortie initialisée mais résultat non implémenté | 2026-11-21 |
| `0x4F` | [`svcSetProcessActivity`](https://switchbrew.org/wiki/SVC#svcSetProcessActivity) | **Q** | Dispatch énuméré ; corps non contrôlé dans ce lot | 2026-11-21 |
| `0x50` | [`svcCreateSharedMemory`](https://switchbrew.org/wiki/SVC#svcCreateSharedMemory) | **Q** | Dispatch énuméré ; corps non contrôlé dans ce lot | 2026-11-21 |
| `0x51` | [`svcMapTransferMemory`](https://switchbrew.org/wiki/SVC#svcMapTransferMemory) | **Q** | Dispatch énuméré ; corps non contrôlé dans ce lot | 2026-11-21 |
| `0x52` | [`svcUnmapTransferMemory`](https://switchbrew.org/wiki/SVC#svcUnmapTransferMemory) | **Q** | Dispatch énuméré ; corps non contrôlé dans ce lot | 2026-11-21 |
| `0x53` | [`svcCreateInterruptEvent`](https://switchbrew.org/wiki/SVC#svcCreateInterruptEvent) | **Q** | Dispatch énuméré ; corps non contrôlé dans ce lot | 2026-11-21 |
| `0x54` | [`svcQueryPhysicalAddress`](https://switchbrew.org/wiki/SVC#svcQueryPhysicalAddress) | **Q** | Dispatch énuméré ; corps non contrôlé dans ce lot | 2026-11-21 |
| `0x55` | [`svcQueryIoMapping`](https://switchbrew.org/wiki/SVC#svcQueryIoMapping) | **Q** | Dispatch énuméré ; corps non contrôlé dans ce lot | 2026-11-21 |
| `0x56` | [`svcCreateDeviceAddressSpace`](https://switchbrew.org/wiki/SVC#svcCreateDeviceAddressSpace) | **Q** | Dispatch énuméré ; corps non contrôlé dans ce lot | 2026-11-21 |
| `0x57` | [`svcAttachDeviceAddressSpace`](https://switchbrew.org/wiki/SVC#svcAttachDeviceAddressSpace) | **Q** | Dispatch énuméré ; corps non contrôlé dans ce lot | 2026-11-21 |
| `0x58` | [`svcDetachDeviceAddressSpace`](https://switchbrew.org/wiki/SVC#svcDetachDeviceAddressSpace) | **Q** | Dispatch énuméré ; corps non contrôlé dans ce lot | 2026-11-21 |
| `0x59` | [`svcMapDeviceAddressSpaceByForce`](https://switchbrew.org/wiki/SVC#svcMapDeviceAddressSpaceByForce) | **Q** | Dispatch énuméré ; corps non contrôlé dans ce lot | 2026-11-21 |
| `0x5A` | [`svcMapDeviceAddressSpaceAligned`](https://switchbrew.org/wiki/SVC#svcMapDeviceAddressSpaceAligned) | **Q** | Dispatch énuméré ; corps non contrôlé dans ce lot | 2026-11-21 |
| `0x5B` | [`svcMapDeviceAddressSpace`](https://switchbrew.org/wiki/SVC#svcMapDeviceAddressSpace) | **E** | Énumération examinée sans cet ID | 2026-11-21 |
| `0x5C` | [`svcUnmapDeviceAddressSpace`](https://switchbrew.org/wiki/SVC#svcUnmapDeviceAddressSpace) | **Q** | Dispatch énuméré ; corps non contrôlé dans ce lot | 2026-11-21 |
| `0x5D` | [`svcInvalidateProcessDataCache`](https://switchbrew.org/wiki/SVC#svcInvalidateProcessDataCache) | **D** | Opérations de cohérence cache non réalisées ; pas de no-op de succès | 2026-11-21 |
| `0x5E` | [`svcStoreProcessDataCache`](https://switchbrew.org/wiki/SVC#svcStoreProcessDataCache) | **D** | Opérations de cohérence cache non réalisées ; pas de no-op de succès | 2026-11-21 |
| `0x5F` | [`svcFlushProcessDataCache`](https://switchbrew.org/wiki/SVC#svcFlushProcessDataCache) | **Q** | [svc_cache.cpp](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/b8883667410054db189d00b3a5144088f47d3af9/sources/eden/src/core/hle/kernel/svc/svc_cache.cpp#L36) ; corps repéré, comportement restant à qualifier | 2026-11-21 |
| `0x60` | [`svcDebugActiveProcess`](https://switchbrew.org/wiki/SVC#svcDebugActiveProcess) | **D** | [svc_debug.cpp](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/b8883667410054db189d00b3a5144088f47d3af9/sources/eden/src/core/hle/kernel/svc/svc_debug.cpp#L12) ; rejet explicite | 2026-11-21 |
| `0x61` | [`svcBreakDebugProcess`](https://switchbrew.org/wiki/SVC#svcBreakDebugProcess) | **D** | [svc_debug.cpp](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/b8883667410054db189d00b3a5144088f47d3af9/sources/eden/src/core/hle/kernel/svc/svc_debug.cpp#L17) ; rejet explicite | 2026-11-21 |
| `0x62` | [`svcTerminateDebugProcess`](https://switchbrew.org/wiki/SVC#svcTerminateDebugProcess) | **D** | [svc_debug.cpp](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/b8883667410054db189d00b3a5144088f47d3af9/sources/eden/src/core/hle/kernel/svc/svc_debug.cpp#L22) ; rejet explicite | 2026-11-21 |
| `0x63` | [`svcGetDebugEvent`](https://switchbrew.org/wiki/SVC#svcGetDebugEvent) | **D** | [svc_debug.cpp](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/b8883667410054db189d00b3a5144088f47d3af9/sources/eden/src/core/hle/kernel/svc/svc_debug.cpp#L27) ; rejet explicite | 2026-11-21 |
| `0x64` | [`svcContinueDebugEvent`](https://switchbrew.org/wiki/SVC#svcContinueDebugEvent) | **D** | [svc_debug.cpp](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/b8883667410054db189d00b3a5144088f47d3af9/sources/eden/src/core/hle/kernel/svc/svc_debug.cpp#L32) ; rejet explicite | 2026-11-21 |
| `0x65` | [`svcGetProcessList`](https://switchbrew.org/wiki/SVC#svcGetProcessList) | **Q** | Dispatch énuméré ; corps non contrôlé dans ce lot | 2026-11-21 |
| `0x66` | [`svcGetThreadList`](https://switchbrew.org/wiki/SVC#svcGetThreadList) | **Q** | Dispatch énuméré ; corps non contrôlé dans ce lot | 2026-11-21 |
| `0x67` | [`svcGetDebugThreadContext`](https://switchbrew.org/wiki/SVC#svcGetDebugThreadContext) | **D** | [svc_debug.cpp](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/b8883667410054db189d00b3a5144088f47d3af9/sources/eden/src/core/hle/kernel/svc/svc_debug.cpp#L38) ; rejet explicite | 2026-11-21 |
| `0x68` | [`svcSetDebugThreadContext`](https://switchbrew.org/wiki/SVC#svcSetDebugThreadContext) | **D** | [svc_debug.cpp](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/b8883667410054db189d00b3a5144088f47d3af9/sources/eden/src/core/hle/kernel/svc/svc_debug.cpp#L44) ; rejet explicite | 2026-11-21 |
| `0x69` | [`svcQueryDebugProcessMemory`](https://switchbrew.org/wiki/SVC#svcQueryDebugProcessMemory) | **D** | [svc_debug.cpp](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/b8883667410054db189d00b3a5144088f47d3af9/sources/eden/src/core/hle/kernel/svc/svc_debug.cpp#L50) ; rejet explicite | 2026-11-21 |
| `0x6A` | [`svcReadDebugProcessMemory`](https://switchbrew.org/wiki/SVC#svcReadDebugProcessMemory) | **D** | [svc_debug.cpp](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/b8883667410054db189d00b3a5144088f47d3af9/sources/eden/src/core/hle/kernel/svc/svc_debug.cpp#L56) ; rejet explicite | 2026-11-21 |
| `0x6B` | [`svcWriteDebugProcessMemory`](https://switchbrew.org/wiki/SVC#svcWriteDebugProcessMemory) | **D** | [svc_debug.cpp](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/b8883667410054db189d00b3a5144088f47d3af9/sources/eden/src/core/hle/kernel/svc/svc_debug.cpp#L62) ; rejet explicite | 2026-11-21 |
| `0x6C` | [`svcSetHardwareBreakPoint`](https://switchbrew.org/wiki/SVC#svcSetHardwareBreakPoint) | **D** | [svc_debug.cpp](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/b8883667410054db189d00b3a5144088f47d3af9/sources/eden/src/core/hle/kernel/svc/svc_debug.cpp#L68) ; rejet explicite | 2026-11-21 |
| `0x6D` | [`svcGetDebugThreadParam`](https://switchbrew.org/wiki/SVC#svcGetDebugThreadParam) | **D** | [svc_debug.cpp](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/b8883667410054db189d00b3a5144088f47d3af9/sources/eden/src/core/hle/kernel/svc/svc_debug.cpp#L74) ; rejet explicite | 2026-11-21 |
| `0x6F` | [`svcGetSystemInfo`](https://switchbrew.org/wiki/SVC#svcGetSystemInfo) | **Q** | Dispatch énuméré ; corps non contrôlé dans ce lot | 2026-11-21 |
| `0x70` | [`svcCreatePort`](https://switchbrew.org/wiki/SVC#svcCreatePort) | **Q** | Dispatch énuméré ; corps non contrôlé dans ce lot | 2026-11-21 |
| `0x71` | [`svcManageNamedPort`](https://switchbrew.org/wiki/SVC#svcManageNamedPort) | **Q** | Dispatch énuméré ; corps non contrôlé dans ce lot | 2026-11-21 |
| `0x72` | [`svcConnectToPort`](https://switchbrew.org/wiki/SVC#svcConnectToPort) | **Q** | Dispatch énuméré ; corps non contrôlé dans ce lot | 2026-11-21 |
| `0x73` | [`svcSetProcessMemoryPermission`](https://switchbrew.org/wiki/SVC#svcSetProcessMemoryPermission) | **Q** | [svc_process_memory.cpp](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/b8883667410054db189d00b3a5144088f47d3af9/sources/eden/src/core/hle/kernel/svc/svc_process_memory.cpp#L32) ; corps repéré, comportement restant à qualifier | 2026-11-21 |
| `0x74` | [`svcMapProcessMemory`](https://switchbrew.org/wiki/SVC#svcMapProcessMemory) | **Q** | [svc_process_memory.cpp](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/b8883667410054db189d00b3a5144088f47d3af9/sources/eden/src/core/hle/kernel/svc/svc_process_memory.cpp#L62) ; corps repéré, comportement restant à qualifier | 2026-11-21 |
| `0x75` | [`svcUnmapProcessMemory`](https://switchbrew.org/wiki/SVC#svcUnmapProcessMemory) | **Q** | [svc_process_memory.cpp](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/b8883667410054db189d00b3a5144088f47d3af9/sources/eden/src/core/hle/kernel/svc/svc_process_memory.cpp#L103) ; corps repéré, comportement restant à qualifier | 2026-11-21 |
| `0x76` | [`svcQueryProcessMemory`](https://switchbrew.org/wiki/SVC#svcQueryProcessMemory) | **Q** | Dispatch énuméré ; corps non contrôlé dans ce lot | 2026-11-21 |
| `0x77` | [`svcMapProcessCodeMemory`](https://switchbrew.org/wiki/SVC#svcMapProcessCodeMemory) | **Q** | [svc_process_memory.cpp](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/b8883667410054db189d00b3a5144088f47d3af9/sources/eden/src/core/hle/kernel/svc/svc_process_memory.cpp#L136) ; corps repéré, comportement restant à qualifier | 2026-11-21 |
| `0x78` | [`svcUnmapProcessCodeMemory`](https://switchbrew.org/wiki/SVC#svcUnmapProcessCodeMemory) | **Q** | [svc_process_memory.cpp](https://github.com/niakw/Prospero.Eden-Encore-vendor/blob/b8883667410054db189d00b3a5144088f47d3af9/sources/eden/src/core/hle/kernel/svc/svc_process_memory.cpp#L197) ; corps repéré, comportement restant à qualifier | 2026-11-21 |
| `0x79` | [`svcCreateProcess`](https://switchbrew.org/wiki/SVC#svcCreateProcess) | **Q** | Dispatch énuméré ; corps non contrôlé dans ce lot | 2026-11-21 |
| `0x7A` | [`svcStartProcess`](https://switchbrew.org/wiki/SVC#svcStartProcess) | **Q** | Dispatch énuméré ; corps non contrôlé dans ce lot | 2026-11-21 |
| `0x7B` | [`svcTerminateProcess`](https://switchbrew.org/wiki/SVC#svcTerminateProcess) | **Q** | Dispatch énuméré ; corps non contrôlé dans ce lot | 2026-11-21 |
| `0x7C` | [`svcGetProcessInfo`](https://switchbrew.org/wiki/SVC#svcGetProcessInfo) | **Q** | Dispatch énuméré ; corps non contrôlé dans ce lot | 2026-11-21 |
| `0x7D` | [`svcCreateResourceLimit`](https://switchbrew.org/wiki/SVC#svcCreateResourceLimit) | **Q** | Dispatch énuméré ; corps non contrôlé dans ce lot | 2026-11-21 |
| `0x7E` | [`svcSetResourceLimitLimitValue`](https://switchbrew.org/wiki/SVC#svcSetResourceLimitLimitValue) | **Q** | Dispatch énuméré ; corps non contrôlé dans ce lot | 2026-11-21 |
| `0x7F` | [`svcCallSecureMonitor`](https://switchbrew.org/wiki/SVC#svcCallSecureMonitor) | **D** | Communication privilégiée : stub ou refus, ne pas simuler un succès sécurisé | 2026-11-21 |

### IDs présents côté Eden hors de cette table SwitchBrew

Header Eden : **123 identifiants**, table wiki historique : **117 identifiants**. Cette différence est liée à l'étendue et aux versions des sources ; **elle ne représente pas des bugs confirmés**.

| ID | Nom Eden | Statut |
|---|---|---|
| `0x37` | `GetResourceLimitPeakValue` | Non présent dans le snapshot miroir : vérifier SVC live et HOS NS1 |
| `0x39` | `CreateIoPool` | Non présent dans le snapshot miroir : vérifier SVC live et HOS NS1 |
| `0x3A` | `CreateIoRegion` | Non présent dans le snapshot miroir : vérifier SVC live et HOS NS1 |
| `0x46` | `MapIoRegion` | Non présent dans le snapshot miroir : vérifier SVC live et HOS NS1 |
| `0x47` | `UnmapIoRegion` | Non présent dans le snapshot miroir : vérifier SVC live et HOS NS1 |
| `0x90` | `MapInsecureMemory` | Non présent dans le snapshot miroir : vérifier SVC live et HOS NS1 |
| `0x91` | `UnmapInsecureMemory` | Non présent dans le snapshot miroir : vérifier SVC live et HOS NS1 |

## Index des familles de services IPC

**Important** : cette section contient des familles et points d'entrée SwitchBrew, **pas encore toutes les commandes**. Une correspondance de répertoire C++ n'atteste pas que le service ou une commande fonctionne.

| Famille SwitchBrew | Services / alias connus (snapshot) | Statut | Dernière revue |
|---|---|---|---|
| [Account services](https://switchbrew.org/wiki/Account_services) | acc:u0, acc:u1, acc:aa, acc:su, [5.0.0+] dauth:0 | **Q** — parcours IPC commande par commande en cours | 2026-11-21 |
| [HID services](https://switchbrew.org/wiki/HID_services) | [1.0.0-8.1.0] ahid:cd, [1.0.0-8.1.0] ahid:hdr, hid, hid:dbg, hid:sys, irs, irs:sys, xcd:sys, [3.0.0-7.0.1] hid:tmp, [5.0.0+] hidbus | **Q** — parcours IPC commande par commande en cours | 2026-11-21 |
| [Applet Manager services](https://switchbrew.org/wiki/Applet_Manager_services) | appletAE, appletOE, idle:sys, omm, spsm, [5.0.0+] tcap, [6.0.0+] caps:su, [8.0.0+] apm | **Q** — parcours IPC commande par commande en cours | 2026-11-21 |
| [NS Services](https://switchbrew.org/wiki/NS_Services) | [1.0.0-2.3.0] aoc:u, mii:u, mii:e, ns:am, ns:su, ns:dev, pl:u, ovln:rcv, ovln:snd, pdm:ntfy, pdm:qry [3.0.0+] aoc:u, ns:am2, ns:dev, ns:ec, ns:rid, ns:rt, ns:su, ns:vm, ns:web, [1.0.0-7.0.1] ovln:rcv, [1.0.0-7.0.1] ovln:snd | **Q** — parcours IPC commande par commande en cours | 2026-11-21 |
| [PPC services](https://switchbrew.org/wiki/PPC_services) | [1.0.0-8.1.0] apm:dbg, [1.0.0-8.1.0] apm:sys, [1.0.0-8.1.0] fgm, [1.0.0-8.1.0] fgm:0, [1.0.0-8.1.0] fgm:9, [1.0.0-8.1.0] fgm:dbg, [1.0.0-7.0.1] apm, [1.0.0-7.0.1] apm:p, [8.0.0-8.1.0] apm:am | **Q** — parcours IPC commande par commande en cours | 2026-11-21 |
| [Glue services](https://switchbrew.org/wiki/Glue_services) | arp:r, arp:w, [2.0.0+] bgtc:t, [2.0.0+] bgtc:sc, [9.0.0+] time:a, [9.0.0+] time:r, [9.0.0+] time:u, [9.0.0+] notif:a, [9.0.0+] notif:s | **Q** — parcours IPC commande par commande en cours | 2026-11-21 |
| [Audio services](https://switchbrew.org/wiki/Audio_services) | audin:a, audin:d, audin:u, audout:a, audout:d, audout:u, audren:a, audren:d, audren:u, audrec:a, audrec:d, audrec:u, audctl, [1.0.0-2.3.0] codecctl, hwopus, auddebug, [6.0.0+] auddev | **Q** — parcours IPC commande par commande en cours | 2026-11-21 |
| [Profiler services](https://switchbrew.org/wiki/Profiler_services) | banana | **Q** — parcours IPC commande par commande en cours | 2026-11-21 |
| [BCAT services](https://switchbrew.org/wiki/BCAT_services) | [2.0.0+] bcat:a, [2.0.0+] bcat:u, [2.0.0+] bcat:m, [2.0.0+] bcat:s, news:a, news:c, news:m, news:p, news:v, prepo:u, prepo:s, prepo:m, [1.0.0-5.1.0] prepo:a, [1.0.0] prepo:d, [6.0.0+] prepo:a2 | **Q** — parcours IPC commande par commande en cours | 2026-11-21 |
| [PCV services](https://switchbrew.org/wiki/PCV_services) | [1.0.0] bpc:c, bpc:b, bpc:r, bpc:w, pcv, pcv:arb, pcv:imm, time:u, time:a, time:s [2.0.0+] bpc, bpc:r, pcv, [2.0.0-8.1.0] time:u, [2.0.0-8.1.0] time:a, [2.0.0-8.1.0] time:s, [1.0.0-7.0.1] pcv:arb, [1.0.0-7.0.1] pcv:imm, [8.0.0+] clkrst, [8.0.0+] clkrst:a, [8.0.0+] clkrst:i, [8.0.0+] rgltr, [8.0.0+] rtc | **Q** — parcours IPC commande par commande en cours | 2026-11-21 |
| [Sockets services](https://switchbrew.org/wiki/Sockets_services) | bsd:u, bsd:s, bsdcfg, ethc:c, ethc:i, nsd:u, nsd:a, sfdnsres | **Q** — parcours IPC commande par commande en cours | 2026-11-21 |
| [Bluetooth Driver services](https://switchbrew.org/wiki/Bluetooth_Driver_services) | btdrv, [5.0.0+] bt | **Q** — parcours IPC commande par commande en cours | 2026-11-21 |
| [BTM services](https://switchbrew.org/wiki/BTM_services) | btm, btm:dbg, btm:sys, [5.0.0+] btm:u | **Q** — parcours IPC commande par commande en cours | 2026-11-21 |
| [Capture services](https://switchbrew.org/wiki/Capture_services) | caps:a, caps:c, [1.0.0] mm:u, [5.0.0+] caps:u | **Q** — parcours IPC commande par commande en cours | 2026-11-21 |
| [Display services](https://switchbrew.org/wiki/Display_services) | [2.0.0+] caps:sc, [2.0.0+] caps:ss, vi:m, vi:s, vi:u, cec-mgr, [2.0.0+] mm:u, [3.0.0-5.1.0] caps:su | **Q** — parcours IPC commande par commande en cours | 2026-11-21 |
| [Nvnflinger services](https://switchbrew.org/wiki/Nvnflinger_services) | dispdrv | **Q** — parcours IPC commande par commande en cours | 2026-11-21 |
| [Debug Monitor services](https://switchbrew.org/wiki/Debug_Monitor_services) | dmnt:- | **Q** — parcours IPC commande par commande en cours | 2026-11-21 |
| [Error Report services](https://switchbrew.org/wiki/Error_Report_services) | erpt:c, erpt:r | **Q** — parcours IPC commande par commande en cours | 2026-11-21 |
| [Error Upload services](https://switchbrew.org/wiki/Error_Upload_services) | eupld:c, eupld:r | **Q** — parcours IPC commande par commande en cours | 2026-11-21 |
| [ETicket services](https://switchbrew.org/wiki/ETicket_services) | es | **Q** — parcours IPC commande par commande en cours | 2026-11-21 |
| [PTM services](https://switchbrew.org/wiki/PTM_services) | fan, psm, tc, ts, pcm, [9.0.0+] apm:sys, [9.0.0+] fgm, [9.0.0+] fgm:0, [9.0.0+] fgm:9, [9.0.0+] fgm:dbg, [9.0.0+] apm:am | **Q** — parcours IPC commande par commande en cours | 2026-11-21 |
| [Fatal services](https://switchbrew.org/wiki/Fatal_services) | fatal:u, fatal:p | **Q** — parcours IPC commande par commande en cours | 2026-11-21 |
| [Friend services](https://switchbrew.org/wiki/Friend_services) | friend:u, friend:v, friend:m, friend:s, friend:a, [5.0.0-6.0.0] nd:app, [5.0.0-6.0.0] nd:sys | **Q** — parcours IPC commande par commande en cours | 2026-11-21 |
| [Filesystem services](https://switchbrew.org/wiki/Filesystem_services) | fsp-srv, fsp-ldr, fsp-pr | **Q** — parcours IPC commande par commande en cours | 2026-11-21 |
| [Bus services](https://switchbrew.org/wiki/Bus_services) | gpio, i2c, i2c:pcv, pinmux, pwm, uart, [3.0.0+] sasbus, [9.0.0+] led | **Q** — parcours IPC commande par commande en cours | 2026-11-21 |
| [TMA services](https://switchbrew.org/wiki/TMA_services) | htc, htcs, htc:tenv, file_io, gds, tma_log, tmagent | **Q** — parcours IPC commande par commande en cours | 2026-11-21 |
| [JIT services](https://switchbrew.org/wiki/JIT_services) | jit:u | **Q** — parcours IPC commande par commande en cours | 2026-11-21 |
| [Backlight services](https://switchbrew.org/wiki/Backlight_services) | lbl | **Q** — parcours IPC commande par commande en cours | 2026-11-21 |
| [LDN services](https://switchbrew.org/wiki/LDN_services) | ldn:m, ldn:s, ldn:u, [5.0.0-6.0.0] ndd, [9.0.0+] lp2p:app, [9.0.0+] lp2p:sys | **Q** — parcours IPC commande par commande en cours | 2026-11-21 |
| [Loader services](https://switchbrew.org/wiki/Loader_services) | [1.0.0+] ldr:pm, ldr:ro, ldr:shel, ldr:dmnt [3.0.0+] ldr:pm, ldr:shel, ldr:dmnt | **Q** — parcours IPC commande par commande en cours | 2026-11-21 |
| [Log services](https://switchbrew.org/wiki/Log_services) | lm, lm:get | **Q** — parcours IPC commande par commande en cours | 2026-11-21 |
| [Manu Services](https://switchbrew.org/wiki/Manu_Services) | manu | **Q** — parcours IPC commande par commande en cours | 2026-11-21 |
| [NCM services](https://switchbrew.org/wiki/NCM_services) | lr, ncm, ncm:v | **Q** — parcours IPC commande par commande en cours | 2026-11-21 |
| [NFC services](https://switchbrew.org/wiki/NFC_services) | nfc:am, nfc:mf:u, nfc:user, nfc:sys, nfp:user, nfp:dbg, nfp:sys | **Q** — parcours IPC commande par commande en cours | 2026-11-21 |
| [Network Interface services](https://switchbrew.org/wiki/Network_Interface_services) | nifm:u, nifm:a, nifm:s | **Q** — parcours IPC commande par commande en cours | 2026-11-21 |
| [NIM services](https://switchbrew.org/wiki/NIM_services) | nim, nim:shp, ntc, [5.0.0+] nim:eca, [7.0.0+] nim:ecas | **Q** — parcours IPC commande par commande en cours | 2026-11-21 |
| [NPNS services](https://switchbrew.org/wiki/NPNS_services) | npns:u, npns:s | **Q** — parcours IPC commande par commande en cours | 2026-11-21 |
| [NV services](https://switchbrew.org/wiki/NV_services) | nvdrv:a, nvdrv:s, nvdrv:t, nvdrv, nvdrvdbg, nvgem:c, nvgem:cd, nvmemp | **Q** — parcours IPC commande par commande en cours | 2026-11-21 |
| [PCIe services](https://switchbrew.org/wiki/PCIe_services) | pcie, [6.0.0+] pcie:log | **Q** — parcours IPC commande par commande en cours | 2026-11-21 |
| [Parental Control services](https://switchbrew.org/wiki/Parental_Control_services) | pctl, pctl:a, pctl:s, pctl:r | **Q** — parcours IPC commande par commande en cours | 2026-11-21 |
| [Process Manager services](https://switchbrew.org/wiki/Process_Manager_services) | pm:bm, pm:info, pm:shell | **Q** — parcours IPC commande par commande en cours | 2026-11-21 |
| [PSC services](https://switchbrew.org/wiki/PSC_services) | psc:c, psc:m, [5.0.0+] srepo:u, [5.0.0+] srepo:a, [8.0.0+] ovln:rcv, [8.0.0+] ovln:snd, [9.0.0+] psc:l, [9.0.0+] time:su, [9.0.0+] time:s, [9.0.0+] time:al, [9.0.0+] time:m, [9.0.0+] time:p, [9.0.0+] ins:r, [9.0.0+] ins:s | **Q** — parcours IPC commande par commande en cours | 2026-11-21 |
| [RO services](https://switchbrew.org/wiki/RO_services) | [3.0.0+] ldr:ro, ro:dmnt, [7.0.0+] ro:1 | **Q** — parcours IPC commande par commande en cours | 2026-11-21 |
| [Settings services](https://switchbrew.org/wiki/Settings_services) | set, set:fd, set:cal, set:sys | **Q** — parcours IPC commande par commande en cours | 2026-11-21 |
| [Shared Database services](https://switchbrew.org/wiki/Shared_Database_services) | [3.0.0+] mii:u, [3.0.0+] mii:e, [3.0.0+] pdm:ntfy, [3.0.0+] pdm:qry, [3.0.0+] pl:u, [5.0.0+] miiimg, [6.0.0+] avm, [9.0.0+] pl:s | **Q** — parcours IPC commande par commande en cours | 2026-11-21 |
| [SSL services](https://switchbrew.org/wiki/SSL_services) | ssl | **Q** — parcours IPC commande par commande en cours | 2026-11-21 |
| [SPL services](https://switchbrew.org/wiki/SPL_services) | csrng, spl:, [4.0.0+] spl:mig, [4.0.0+] spl:fs, [4.0.0+] spl:ssl, [4.0.0+] spl:es, [5.0.0+] spl:manu | **Q** — parcours IPC commande par commande en cours | 2026-11-21 |
| [?](https://switchbrew.org/wiki/?) | sf-uds | **Q** — parcours IPC commande par commande en cours | 2026-11-21 |
| [?](https://switchbrew.org/wiki/?) | tspm | **Q** — parcours IPC commande par commande en cours | 2026-11-21 |
| [USB services](https://switchbrew.org/wiki/USB_services) | usb:ds, usb:hs, usb:pd, usb:pd:c, [1.0.0] usb:pd:m, usb:pm, [7.0.0+] usb:hs:a, [7.0.0+] usb:qdb, [8.0.0+] usb:obsv | **Q** — parcours IPC commande par commande en cours | 2026-11-21 |
| [WLAN services](https://switchbrew.org/wiki/WLAN_services) | wlan:inf, wlan:lcl, wlan:lg, wlan:lga, wlan:sg, wlan:soc, [6.0.0+] wlan:dtc | **Q** — parcours IPC commande par commande en cours | 2026-11-21 |
| [GRC services](https://switchbrew.org/wiki/GRC_services) | [4.0.0+] grc:c, [6.0.0+] grc:d | **Q** — parcours IPC commande par commande en cours | 2026-11-21 |
| [Migration services](https://switchbrew.org/wiki/Migration_services) | [4.0.0+] mig:usr | **Q** — parcours IPC commande par commande en cours | 2026-11-21 |
| [Jpegdec services](https://switchbrew.org/wiki/Jpegdec_services) | [4.0.0+] caps:dc | **Q** — parcours IPC commande par commande en cours | 2026-11-21 |
| [OLSC services](https://switchbrew.org/wiki/OLSC_services) | [6.0.0+] olsc:s | **Q** — parcours IPC commande par commande en cours | 2026-11-21 |
| [NGCT services](https://switchbrew.org/wiki/NGCT_services) | [9.0.0+] ngct:s, [9.0.0+] ngct:u | **Q** — parcours IPC commande par commande en cours | 2026-11-21 |

## Lacunes explicitement inventoriées (sources NS1, non exhaustif)

| Référence registre | Fonctions / interfaces | Motif | Comportement sûr tant que non implémenté |
|---|---|---|---|
| KR-01 | `FlushEntireDataCache`, `FlushDataCache`, `InvalidateProcessDataCache`, `StoreProcessDataCache` | Cohérence cache non émulée | Conserver le rejet / signalement ; jamais succès factice |
| KR-02 | `CreateIoPool`, `CreateIoRegion`, `MapIoRegion`, `UnmapIoRegion` | Mapping physique, permissions/handles manquants | `ResultNotImplemented`, pas de handle fictif |
| KR-03 | `ReadWriteRegister` | MMIO privilégié absent | Sortie sûre + erreur explicite |
| KR-04 | `CallSecureMonitor` / ABI From32 | SMC privilégié absent | Ne pas prétendre qu'un SMC a eu lieu |
| KR-05 | Services de débogage kernel | Plusieurs branches non implémentées | Rejet, pas de mémoire/état fictifs |
| SV-04 | SPL : crypto/config/boot reason | Cas non implémentés ou simulés | Ne jamais feindre une opération crypto |
| SV-05 | IRS : image/capteur IR | Matériel et commandes non intégralement disponibles | Déclarer absence/erreur selon API |
| SV-06 | CAPS : album/captures | API invitée partielle | Distinct des captures du launcher PS5 |
| SV-07/SV-08 | LDN, NPNS | Réseaux locaux/push partiels | Ne pas promettre connectivité fictive |
| SV-09 | MM : fréquence/perf | Valeurs simplifiées et politique à qualifier | Pas de fréquence fictive sans contrat |
| SV-10 | NGC : filtrage de texte | Réponses partielles | Aucun lien automatique avec glyphes HUD |
| SV-11 | NVMEMP | Mémoire GPU mappable non exhaustive | Pas de mapping fictif |
| SV-12 | NFC, I2C, capteurs | Matériel partiel | Retour d'indisponibilité documenté |
| SV-13 | NS : utilitaires système | Stubs dépendant du firmware | Vérifier versions et interfaces |

## Suivi et protocole de mise à jour

- Pour chaque ligne qualifiée, garder : **ID/nom SwitchBrew → version HOS → nom de service et commande → C++ effectivement compilé → statut/motif → commit + deux SHAs → CI → résultat PS5 → date**.
- D'abord le dispatch réel, `headless/CMakeLists.txt`, overlays et générateurs ; les fichiers originaux `sources/eden` ne prouvent pas toujours le propriétaire PS5.
- Les entrées Q ne deviennent ni D ni C sans éléments concrets. Les stubs restent D/P tant que leurs effets de bord ne sont pas implémentés.
- Avant d'exposer une fonction absente, consulter SwitchBrew et les sources système/upstream par identifiant exact, puis préserver ABI, mémoire, verrous et synchronisation.
- **P0/P1** : GPU/IPC/FC27 et démarrage/présentation ; **P2/P3** : fonctions accessoires à qualifier sans détourner le portage.

Références de suivi : [registre de complétude NS1](./EDEN_ENCORE_NS1_IMPLEMENTATION_COMPLETENESS_REGISTER_2026-11-21.md) et [issue maîtresse #298](https://github.com/niakw/ProsperoEden-Encore/issues/298).

**Limite de cette première livraison :** tous les IDs SVC du snapshot historique sont listés ; seules six unités kernel ont reçu un contrôle de corps C++ pour leur statut. Les interfaces/commandes IPC détaillées doivent encore être rapprochées du code réel, et les versions HOS actuelles du wiki live peuvent différer. **Aucun build ou test PS5 n'a été réalisé pour ce document.**
