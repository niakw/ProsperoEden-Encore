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

## 7. Catalogue des commandes IPC documentées par SwitchBrew

**Statut de toutes les entrées de cette section : Q** (commande référencée, mais chemin C++ exécuté et résultat PS5 non qualifiés). La date décrit une comparaison documentaire, pas un test du jeu. Les ID sont propres à leur interface et à la version HOS.

### Account services   
  u0: System, u1: User, su: Admin, aa: Baas

[Wiki SwitchBrew](https://switchbrew.org/wiki/Account_services___
__u0:_System,_u1:_User,_su:_Admin,_aa:_Baas) · [miroir](https://github.com/backupbrew/switchbrew/blob/master/Account%20services.md)

**221 commandes documentées** (snapshot du miroir).

| Interface / section | ID | Fonction | Disponibilité indiquée | Encore | Vérifié |
|---|---|---|---|---|---|
| acc:su | `0` | `GetUserCount` | — | Q | 2026-11-21 |
| acc:su | `1` | `GetUserExistence` | — | Q | 2026-11-21 |
| acc:su | `2` | `ListAllUsers` | — | Q | 2026-11-21 |
| acc:su | `3` | `ListOpenUsers` | — | Q | 2026-11-21 |
| acc:su | `4` | `GetLastOpenedUser` | — | Q | 2026-11-21 |
| acc:su | `5` | `GetProfile` | — | Q | 2026-11-21 |
| acc:su | `6` | `GetProfileDigest` | 3.0.0+ | Q | 2026-11-21 |
| acc:su | `50` | `IsUserRegistrationRequestPermitted` | — | Q | 2026-11-21 |
| acc:su | `51` | `TrySelectUserWithoutInteraction` | — | Q | 2026-11-21 |
| acc:su | `60` | `ListOpenContextStoredUsers` | 5.0.0-5.1.0 | Q | 2026-11-21 |
| acc:su | `99` | `DebugActivateOpenContextRetention` | 6.0.0+ | Q | 2026-11-21 |
| acc:su | `100` | `GetUserRegistrationNotifier` | — | Q | 2026-11-21 |
| acc:su | `101` | `GetUserStateChangeNotifier` | — | Q | 2026-11-21 |
| acc:su | `102` | `GetBaasAccountManagerForSystemService` | — | Q | 2026-11-21 |
| acc:su | `103` | `GetBaasUserAvailabilityChangeNotifier` | — | Q | 2026-11-21 |
| acc:su | `104` | `GetProfileUpdateNotifier` | — | Q | 2026-11-21 |
| acc:su | `105` | `CheckNetworkServiceAvailabilityAsync` | 4.0.0+ | Q | 2026-11-21 |
| acc:su | `106` | `GetProfileSyncNotifier` | 9.0.0+ | Q | 2026-11-21 |
| acc:su | `110` | `StoreSaveDataThumbnail` | — | Q | 2026-11-21 |
| acc:su | `111` | `ClearSaveDataThumbnail` | — | Q | 2026-11-21 |
| acc:su | `112` | `LoadSaveDataThumbnail` | — | Q | 2026-11-21 |
| acc:su | `113` | `GetSaveDataThumbnailExistence` | 5.0.0+ | Q | 2026-11-21 |
| acc:su | `130` | `ActivateOpenContextRetention` | 6.0.0+ | Q | 2026-11-21 |
| acc:su | `140` | `ListQualifiedUsers` | 6.0.0+ | Q | 2026-11-21 |
| acc:su | `190` | `GetUserLastOpenedApplication` | — | Q | 2026-11-21 |
| acc:su | `191` | `UpdateNotificationReceiverInfo ([5.0.0-5.1.0] ActivateOpenContextHolder)` | 7.0.0+ | Q | 2026-11-21 |
| acc:su | `200` | `BeginUserRegistration` | — | Q | 2026-11-21 |
| acc:su | `201` | `CompleteUserRegistration` | — | Q | 2026-11-21 |
| acc:su | `202` | `CancelUserRegistration` | — | Q | 2026-11-21 |
| acc:su | `203` | `DeleteUser` | — | Q | 2026-11-21 |
| acc:su | `204` | `SetUserPosition` | — | Q | 2026-11-21 |
| acc:su | `205` | `GetProfileEditor` | — | Q | 2026-11-21 |
| acc:su | `206` | `CompleteUserRegistrationForcibly` | — | Q | 2026-11-21 |
| acc:su | `210` | `CreateFloatingRegistrationRequest` | 3.0.0+ | Q | 2026-11-21 |
| acc:su | `211` | `CreateProcedureToRegisterUserWithNintendoAccount` | 8.0.0+ | Q | 2026-11-21 |
| acc:su | `212` | `ResumeProcedureToRegisterUserWithNintendoAccount` | 8.0.0+ | Q | 2026-11-21 |
| acc:su | `230` | `AuthenticateServiceAsync` | — | Q | 2026-11-21 |
| acc:su | `250` | `GetBaasAccountAdministrator` | — | Q | 2026-11-21 |
| acc:su | `290` | `ProxyProcedureForGuestLoginWithNintendoAccount` | — | Q | 2026-11-21 |
| acc:su | `291` | `ProxyProcedureForFloatingRegistrationWithNintendoAccount` | 3.0.0+ | Q | 2026-11-21 |
| acc:su | `299` | `SuspendBackgroundDaemon` | — | Q | 2026-11-21 |
| acc:su | `997` | `DebugInvalidateTokenCacheForUser` | 3.0.0+ | Q | 2026-11-21 |
| acc:su | `998` | `DebugSetUserStateClose` | — | Q | 2026-11-21 |
| acc:su | `999` | `DebugSetUserStateOpen` | — | Q | 2026-11-21 |
| acc:su | `0` | `CheckAvailability` | — | Q | 2026-11-21 |
| acc:su | `1` | `GetAccountId` | — | Q | 2026-11-21 |
| acc:su | `2` | `EnsureIdTokenCacheAsync` | — | Q | 2026-11-21 |
| acc:su | `3` | `LoadIdTokenCache` | — | Q | 2026-11-21 |
| acc:su | `100` | `SetSystemProgramIdentification` | — | Q | 2026-11-21 |
| acc:su | `101` | `RefreshNotificationTokenAsync` | 7.0.0+ | Q | 2026-11-21 |
| acc:su | `110` | `GetServiceEntryRequirementCache` | 4.0.0+ | Q | 2026-11-21 |
| acc:su | `111` | `InvalidateServiceEntryRequirementCache` | 4.0.0+ | Q | 2026-11-21 |
| acc:su | `112` | `InvalidateTokenCache` | 4.0.0-6.2.0 | Q | 2026-11-21 |
| acc:su | `113` | `GetServiceEntryRequirementCacheForOnlinePlay` | 6.1.0+ | Q | 2026-11-21 |
| acc:su | `120` | `GetNintendoAccountId` | — | Q | 2026-11-21 |
| acc:su | `121` | `CalculateNintendoAccountAuthenticationFingerprint` | 9.0.0+ | Q | 2026-11-21 |
| acc:su | `130` | `GetNintendoAccountUserResourceCache` | — | Q | 2026-11-21 |
| acc:su | `131` | `RefreshNintendoAccountUserResourceCacheAsync` | — | Q | 2026-11-21 |
| acc:su | `132` | `RefreshNintendoAccountUserResourceCacheAsyncIfSecondsElapsed` | — | Q | 2026-11-21 |
| acc:su | `133` | `GetNintendoAccountVerificationUrlCache` | 9.0.0+ | Q | 2026-11-21 |
| acc:su | `134` | `RefreshNintendoAccountVerificationUrlCacheAsync` | 9.0.0+ | Q | 2026-11-21 |
| acc:su | `135` | `RefreshNintendoAccountVerificationUrlCacheAsyncIfSecondsElapsed` | 9.0.0+ | Q | 2026-11-21 |
| acc:su | `140` | `GetNetworkServiceLicenseCache` | 5.0.0+ | Q | 2026-11-21 |
| acc:su | `141` | `RefreshNetworkServiceLicenseCacheAsync` | 5.0.0+ | Q | 2026-11-21 |
| acc:su | `142` | `RefreshNetworkServiceLicenseCacheAsyncIfSecondsElapsed` | 5.0.0+ | Q | 2026-11-21 |
| acc:su | `150` | `CreateAuthorizationRequest` | — | Q | 2026-11-21 |
| acc:su | `0` | `GetSessionId` | — | Q | 2026-11-21 |
| acc:su | `12` | `GetAccountId` | — | Q | 2026-11-21 |
| acc:su | `13` | `GetLinkedNintendoAccountId` | — | Q | 2026-11-21 |
| acc:su | `14` | `GetNickname` | — | Q | 2026-11-21 |
| acc:su | `15` | `GetProfileImage` | — | Q | 2026-11-21 |
| acc:su | `21` | `LoadIdTokenCache` | — | Q | 2026-11-21 |
| acc:su | `100` | `RegisterUser ([1.0.0-3.0.2] RegisterAsync)` | — | Q | 2026-11-21 |
| acc:su | `101` | `RegisterUserWithUid ([1.0.0-3.0.2] RegisterWithUidAsync)` | — | Q | 2026-11-21 |
| acc:su | `102` | `RegisterNetworkServiceAccountAsync` | 4.0.0+ | Q | 2026-11-21 |
| acc:su | `103` | `RegisterNetworkServiceAccountWithUidAsync` | 4.0.0+ | Q | 2026-11-21 |
| acc:su | `110` | `SetSystemProgramIdentification` | — | Q | 2026-11-21 |
| acc:su | `111` | `EnsureIdTokenCacheAsync` | — | Q | 2026-11-21 |
| acc:su | `200` | `IsRegistered` | — | Q | 2026-11-21 |
| acc:su | `201` | `RegisterAsync` | — | Q | 2026-11-21 |
| acc:su | `202` | `UnregisterAsync` | — | Q | 2026-11-21 |
| acc:su | `203` | `DeleteRegistrationInfoLocally` | — | Q | 2026-11-21 |
| acc:su | `220` | `SynchronizeProfileAsync` | — | Q | 2026-11-21 |
| acc:su | `221` | `UploadProfileAsync` | — | Q | 2026-11-21 |
| acc:su | `222` | `SynchronizeProfileAsyncIfSecondsElapsed` | — | Q | 2026-11-21 |
| acc:su | `250` | `IsLinkedWithNintendoAccount` | — | Q | 2026-11-21 |
| acc:su | `251` | `CreateProcedureToLinkWithNintendoAccount` | — | Q | 2026-11-21 |
| acc:su | `252` | `ResumeProcedureToLinkWithNintendoAccount` | — | Q | 2026-11-21 |
| acc:su | `255` | `CreateProcedureToUpdateLinkageStateOfNintendoAccount` | — | Q | 2026-11-21 |
| acc:su | `256` | `ResumeProcedureToUpdateLinkageStateOfNintendoAccount` | — | Q | 2026-11-21 |
| acc:su | `260` | `CreateProcedureToLinkNnidWithNintendoAccount` | 3.0.0+ | Q | 2026-11-21 |
| acc:su | `261` | `ResumeProcedureToLinkNnidWithNintendoAccount` | 3.0.0+ | Q | 2026-11-21 |
| acc:su | `280` | `ProxyProcedureToAcquireApplicationAuthorizationForNintendoAccount` | — | Q | 2026-11-21 |
| acc:su | `290` | `GetRequestForNintendoAccountUserResourceView` | 8.0.0+ | Q | 2026-11-21 |
| acc:su | `300` | `TryRecoverNintendoAccountUserStateAsync` | 6.0.0+ | Q | 2026-11-21 |
| acc:su | `400` | `IsServiceEntryRequirementCacheRefreshRequiredForOnlinePlay` | 6.1.0+ | Q | 2026-11-21 |
| acc:su | `401` | `RefreshServiceEntryRequirementCacheForOnlinePlayAsync` | 6.1.0+ | Q | 2026-11-21 |
| acc:su | `900` | `GetAuthenticationInfoForWin` | 9.0.0+ | Q | 2026-11-21 |
| acc:su | `901` | `ImportAsyncForWin` | 9.0.0+ | Q | 2026-11-21 |
| acc:su | `997` | `DebugUnlinkNintendoAccountAsync` | — | Q | 2026-11-21 |
| acc:su | `998` | `DebugSetAvailabilityErrorDetail` | — | Q | 2026-11-21 |
| acc:su | `10` | `InvokeWithoutInteractionAsync` | — | Q | 2026-11-21 |
| acc:su | `19` | `IsAuthorized` | — | Q | 2026-11-21 |
| acc:su | `20` | `GetAuthorizationCode` | — | Q | 2026-11-21 |
| acc:su | `21` | `GetIdToken` | — | Q | 2026-11-21 |
| acc:su | `22` | `GetState` | — | Q | 2026-11-21 |
| acc:su | `0` | `PrepareAsync` | — | Q | 2026-11-21 |
| acc:su | `1` | `GetRequest` | — | Q | 2026-11-21 |
| acc:su | `2` | `ApplyResponse` | — | Q | 2026-11-21 |
| acc:su | `3` | `ApplyResponseAsync` | — | Q | 2026-11-21 |
| acc:su | `10` | `Suspend` | — | Q | 2026-11-21 |
| acc:su | `100` | `GetAccountId` | — | Q | 2026-11-21 |
| acc:su | `101` | `GetLinkedNintendoAccountId` | — | Q | 2026-11-21 |
| acc:su | `102` | `GetNickname` | — | Q | 2026-11-21 |
| acc:su | `103` | `GetProfileImage` | — | Q | 2026-11-21 |
| acc:su | `100` | `GetRequestWithTheme` | — | Q | 2026-11-21 |
| acc:su | `101` | `IsNetworkServiceAccountReplaced` | — | Q | 2026-11-21 |
| acc:su | `0` | `GetSystemEvent` | — | Q | 2026-11-21 |
| acc:su | `0` | `Get` | — | Q | 2026-11-21 |
| acc:su | `1` | `GetBase` | — | Q | 2026-11-21 |
| acc:su | `10` | `GetImageSize` | — | Q | 2026-11-21 |
| acc:su | `11` | `LoadImage` | — | Q | 2026-11-21 |
| acc:su | `100` | `Store` | — | Q | 2026-11-21 |
| acc:su | `101` | `StoreWithImage` | — | Q | 2026-11-21 |
| acc:su | `1` | `Cancel` | — | Q | 2026-11-21 |
| acc:su | `2` | `HasDone` | — | Q | 2026-11-21 |
| acc:su | `3` | `GetResult` | — | Q | 2026-11-21 |
| acc:su | `999` | `Dummy` | — | Q | 2026-11-21 |
| acc:u0 | `0` | `GetUserCount` | — | Q | 2026-11-21 |
| acc:u0 | `1` | `GetUserExistence` | — | Q | 2026-11-21 |
| acc:u0 | `2` | `ListAllUsers` | — | Q | 2026-11-21 |
| acc:u0 | `3` | `ListOpenUsers` | — | Q | 2026-11-21 |
| acc:u0 | `4` | `GetLastOpenedUser` | — | Q | 2026-11-21 |
| acc:u0 | `5` | `GetProfile` | — | Q | 2026-11-21 |
| acc:u0 | `6` | `GetProfileDigest` | 3.0.0+ | Q | 2026-11-21 |
| acc:u0 | `50` | `IsUserRegistrationRequestPermitted` | — | Q | 2026-11-21 |
| acc:u0 | `51` | `TrySelectUserWithoutInteraction` | — | Q | 2026-11-21 |
| acc:u0 | `60` | `ListOpenContextStoredUsers` | 5.0.0-5.1.0 | Q | 2026-11-21 |
| acc:u0 | `99` | `DebugActivateOpenContextRetention` | 6.0.0+ | Q | 2026-11-21 |
| acc:u0 | `100` | `InitializeApplicationInfoV0` | — | Q | 2026-11-21 |
| acc:u0 | `101` | `GetBaasAccountManagerForApplication` | — | Q | 2026-11-21 |
| acc:u0 | `102` | `AuthenticateApplicationAsync` | — | Q | 2026-11-21 |
| acc:u0 | `103` | `CheckNetworkServiceAvailabilityAsync` | 4.0.0+ | Q | 2026-11-21 |
| acc:u0 | `110` | `StoreSaveDataThumbnail` | — | Q | 2026-11-21 |
| acc:u0 | `111` | `ClearSaveDataThumbnail` | — | Q | 2026-11-21 |
| acc:u0 | `120` | `CreateGuestLoginRequest` | — | Q | 2026-11-21 |
| acc:u0 | `130` | `LoadOpenContext` | 5.0.0+ | Q | 2026-11-21 |
| acc:u0 | `131` | `ListOpenContextStoredUsers` | 6.0.0+ | Q | 2026-11-21 |
| acc:u0 | `140` | `InitializeApplicationInfo` | 6.0.0+ | Q | 2026-11-21 |
| acc:u0 | `141` | `ListQualifiedUsers` | 6.0.0+ | Q | 2026-11-21 |
| acc:u0 | `150` | `IsUserAccountSwitchLocked` | 6.0.0+ | Q | 2026-11-21 |
| acc:u0 | `0` | `GetSessionId` | — | Q | 2026-11-21 |
| acc:u0 | `12` | `GetAccountId` | — | Q | 2026-11-21 |
| acc:u0 | `13` | `GetLinkedNintendoAccountId` | — | Q | 2026-11-21 |
| acc:u0 | `14` | `GetNickname` | — | Q | 2026-11-21 |
| acc:u0 | `15` | `GetProfileImage` | — | Q | 2026-11-21 |
| acc:u0 | `21` | `LoadIdTokenCache` | 3.0.0+ | Q | 2026-11-21 |
| acc:u0 | `0` | `CheckAvailability` | — | Q | 2026-11-21 |
| acc:u0 | `1` | `GetAccountId` | — | Q | 2026-11-21 |
| acc:u0 | `2` | `EnsureIdTokenCacheAsync` | — | Q | 2026-11-21 |
| acc:u0 | `3` | `LoadIdTokenCache` | — | Q | 2026-11-21 |
| acc:u0 | `130` | `GetNintendoAccountUserResourceCacheForApplication` | — | Q | 2026-11-21 |
| acc:u0 | `150` | `CreateAuthorizationRequest` | — | Q | 2026-11-21 |
| acc:u0 | `160` | `StoreOpenContext` | 5.0.0+ | Q | 2026-11-21 |
| acc:u0 | `170` | `LoadNetworkServiceLicenseKindAsync` | 6.0.0+ | Q | 2026-11-21 |
| acc:u0 | `0` | `GetSystemEvent` | — | Q | 2026-11-21 |
| acc:u0 | `1` | `Cancel` | — | Q | 2026-11-21 |
| acc:u0 | `2` | `HasDone` | — | Q | 2026-11-21 |
| acc:u0 | `3` | `GetResult` | — | Q | 2026-11-21 |
| acc:u0 | `100` | `GetNetworkServiceLicenseKind` | — | Q | 2026-11-21 |
| acc:u1 | `0` | `GetUserCount` | — | Q | 2026-11-21 |
| acc:u1 | `1` | `GetUserExistence` | — | Q | 2026-11-21 |
| acc:u1 | `2` | `ListAllUsers` | — | Q | 2026-11-21 |
| acc:u1 | `3` | `ListOpenUsers` | — | Q | 2026-11-21 |
| acc:u1 | `4` | `GetLastOpenedUser` | — | Q | 2026-11-21 |
| acc:u1 | `5` | `GetProfile` | — | Q | 2026-11-21 |
| acc:u1 | `6` | `GetProfileDigest` | 3.0.0+ | Q | 2026-11-21 |
| acc:u1 | `50` | `IsUserRegistrationRequestPermitted` | — | Q | 2026-11-21 |
| acc:u1 | `51` | `TrySelectUserWithoutInteraction` | — | Q | 2026-11-21 |
| acc:u1 | `60` | `ListOpenContextStoredUsers` | 5.0.0-5.1.0 | Q | 2026-11-21 |
| acc:u1 | `99` | `DebugActivateOpenContextRetention` | 6.0.0+ | Q | 2026-11-21 |
| acc:u1 | `100` | `GetUserRegistrationNotifier` | — | Q | 2026-11-21 |
| acc:u1 | `101` | `GetUserStateChangeNotifier` | — | Q | 2026-11-21 |
| acc:u1 | `102` | `GetBaasAccountManagerForSystemService` | — | Q | 2026-11-21 |
| acc:u1 | `103` | `GetBaasUserAvailabilityChangeNotifier` | — | Q | 2026-11-21 |
| acc:u1 | `104` | `GetProfileUpdateNotifier` | — | Q | 2026-11-21 |
| acc:u1 | `105` | `CheckNetworkServiceAvailabilityAsync` | 4.0.0+ | Q | 2026-11-21 |
| acc:u1 | `106` | `GetProfileSyncNotifier` | 9.0.0+ | Q | 2026-11-21 |
| acc:u1 | `110` | `StoreSaveDataThumbnail` | — | Q | 2026-11-21 |
| acc:u1 | `111` | `ClearSaveDataThumbnail` | — | Q | 2026-11-21 |
| acc:u1 | `112` | `LoadSaveDataThumbnail` | — | Q | 2026-11-21 |
| acc:u1 | `113` | `GetSaveDataThumbnailExistence` | 5.0.0+ | Q | 2026-11-21 |
| acc:u1 | `130` | `ActivateOpenContextRetention` | 6.0.0+ | Q | 2026-11-21 |
| acc:u1 | `140` | `ListQualifiedUsers` | 6.0.0+ | Q | 2026-11-21 |
| acc:u1 | `190` | `GetUserLastOpenedApplication` | — | Q | 2026-11-21 |
| acc:u1 | `191` | `UpdateNotificationReceiverInfo ([5.0.0-5.1.0] ActivateOpenContextHolder)` | 7.0.0+ | Q | 2026-11-21 |
| acc:u1 | `997` | `DebugInvalidateTokenCacheForUser` | 3.0.0+ | Q | 2026-11-21 |
| acc:u1 | `998` | `DebugSetUserStateClose` | — | Q | 2026-11-21 |
| acc:u1 | `999` | `DebugSetUserStateOpen` | — | Q | 2026-11-21 |
| acc:u1 | `0` | `PrepareAsync` | — | Q | 2026-11-21 |
| acc:u1 | `1` | `GetRequest` | — | Q | 2026-11-21 |
| acc:u1 | `2` | `ApplyResponse` | — | Q | 2026-11-21 |
| acc:u1 | `3` | `ApplyResponseAsync` | — | Q | 2026-11-21 |
| acc:u1 | `10` | `Suspend` | — | Q | 2026-11-21 |
| acc:u1 | `100` | `GetAccountId` | — | Q | 2026-11-21 |
| acc:u1 | `101` | `GetLinkedNintendoAccountId` | — | Q | 2026-11-21 |
| acc:u1 | `102` | `GetNickname` | — | Q | 2026-11-21 |
| acc:u1 | `103` | `GetProfileImage` | — | Q | 2026-11-21 |
| acc:u1 | `110` | `RegisterUserAsync` | — | Q | 2026-11-21 |
| acc:u1 | `111` | `GetUid` | — | Q | 2026-11-21 |
| acc:aa | `0` | `EnsureCacheAsync` | — | Q | 2026-11-21 |
| acc:aa | `1` | `LoadCache` | — | Q | 2026-11-21 |
| acc:aa | `2` | `GetDeviceAccountId` | — | Q | 2026-11-21 |
| dauth:0 | `0` | `EnsureAuthenticationTokenCacheAsync ([5.0.0-5.1.0] GeneratePostData)` | — | Q | 2026-11-21 |
| dauth:0 | `1` | `LoadAuthenticationTokenCache` | 6.0.0+ | Q | 2026-11-21 |
| dauth:0 | `10` | `EnsureEdgeTokenCacheAsync` | 6.0.0+ | Q | 2026-11-21 |
| dauth:0 | `11` | `LoadEdgeTokenCache` | 6.0.0+ | Q | 2026-11-21 |
| dauth:0 | `0` | `GetResult` | — | Q | 2026-11-21 |
| dauth:0 | `1` | `Cancel` | — | Q | 2026-11-21 |
| dauth:0 | `2` | `IsAvailable` | — | Q | 2026-11-21 |
| dauth:0 | `3` | `GetSystemEvent` | — | Q | 2026-11-21 |

### HID services

[Wiki SwitchBrew](https://switchbrew.org/wiki/HID_services) · [miroir](https://github.com/backupbrew/switchbrew/blob/master/HID%20services.md)

**440 commandes documentées** (snapshot du miroir).

| Interface / section | ID | Fonction | Disponibilité indiquée | Encore | Vérifié |
|---|---|---|---|---|---|
| hid | `0` | `CreateAppletResource` | — | Q | 2026-11-21 |
| hid | `1` | `ActivateDebugPad` | — | Q | 2026-11-21 |
| hid | `11` | `ActivateTouchScreen` | — | Q | 2026-11-21 |
| hid | `21` | `ActivateMouse` | — | Q | 2026-11-21 |
| hid | `31` | `ActivateKeyboard` | — | Q | 2026-11-21 |
| hid | `32` | `SendKeyboardLockKeyEvent` | 6.0.0+ | Q | 2026-11-21 |
| hid | `40` | `AcquireXpadIdEventHandle` | — | Q | 2026-11-21 |
| hid | `41` | `ReleaseXpadIdEventHandle` | — | Q | 2026-11-21 |
| hid | `51` | `ActivateXpad` | — | Q | 2026-11-21 |
| hid | `55` | `GetXpadIds` | — | Q | 2026-11-21 |
| hid | `56` | `ActivateJoyXpad` | — | Q | 2026-11-21 |
| hid | `58` | `GetJoyXpadLifoHandle` | — | Q | 2026-11-21 |
| hid | `59` | `GetJoyXpadIds` | — | Q | 2026-11-21 |
| hid | `60` | `ActivateSixAxisSensor` | — | Q | 2026-11-21 |
| hid | `61` | `DeactivateSixAxisSensor` | — | Q | 2026-11-21 |
| hid | `62` | `GetSixAxisSensorLifoHandle` | — | Q | 2026-11-21 |
| hid | `63` | `ActivateJoySixAxisSensor` | — | Q | 2026-11-21 |
| hid | `64` | `DeactivateJoySixAxisSensor` | — | Q | 2026-11-21 |
| hid | `65` | `GetJoySixAxisSensorLifoHandle` | — | Q | 2026-11-21 |
| hid | `66` | `StartSixAxisSensor` | — | Q | 2026-11-21 |
| hid | `67` | `StopSixAxisSensor` | — | Q | 2026-11-21 |
| hid | `68` | `IsSixAxisSensorFusionEnabled` | — | Q | 2026-11-21 |
| hid | `69` | `EnableSixAxisSensorFusion` | — | Q | 2026-11-21 |
| hid | `70` | `SetSixAxisSensorFusionParameters` | — | Q | 2026-11-21 |
| hid | `71` | `GetSixAxisSensorFusionParameters` | — | Q | 2026-11-21 |
| hid | `72` | `ResetSixAxisSensorFusionParameters` | — | Q | 2026-11-21 |
| hid | `73` | `SetAccelerometerParameters` | — | Q | 2026-11-21 |
| hid | `74` | `GetAccelerometerParameters` | — | Q | 2026-11-21 |
| hid | `75` | `ResetAccelerometerParameters` | — | Q | 2026-11-21 |
| hid | `76` | `SetAccelerometerPlayMode` | — | Q | 2026-11-21 |
| hid | `77` | `GetAccelerometerPlayMode` | — | Q | 2026-11-21 |
| hid | `78` | `ResetAccelerometerPlayMode` | — | Q | 2026-11-21 |
| hid | `79` | `SetGyroscopeZeroDriftMode` | — | Q | 2026-11-21 |
| hid | `80` | `GetGyroscopeZeroDriftMode` | — | Q | 2026-11-21 |
| hid | `81` | `ResetGyroscopeZeroDriftMode` | — | Q | 2026-11-21 |
| hid | `82` | `IsSixAxisSensorAtRest` | — | Q | 2026-11-21 |
| hid | `83` | `IsFirmwareUpdateAvailableForSixAxisSensor` | 6.0.0+ | Q | 2026-11-21 |
| hid | `91` | `ActivateGesture` | — | Q | 2026-11-21 |
| hid | `100` | `SetSupportedNpadStyleSet` | — | Q | 2026-11-21 |
| hid | `101` | `GetSupportedNpadStyleSet` | — | Q | 2026-11-21 |
| hid | `102` | `SetSupportedNpadIdType` | — | Q | 2026-11-21 |
| hid | `103` | `ActivateNpad` | — | Q | 2026-11-21 |
| hid | `104` | `DeactivateNpad` | — | Q | 2026-11-21 |
| hid | `106` | `AcquireNpadStyleSetUpdateEventHandle` | — | Q | 2026-11-21 |
| hid | `107` | `DisconnectNpad` | — | Q | 2026-11-21 |
| hid | `108` | `GetPlayerLedPattern` | — | Q | 2026-11-21 |
| hid | `109` | `ActivateNpadWithRevision` | 5.0.0+ | Q | 2026-11-21 |
| hid | `120` | `SetNpadJoyHoldType` | — | Q | 2026-11-21 |
| hid | `121` | `GetNpadJoyHoldType` | — | Q | 2026-11-21 |
| hid | `122` | `SetNpadJoyAssignmentModeSingleByDefault` | — | Q | 2026-11-21 |
| hid | `123` | `SetNpadJoyAssignmentModeSingle` | — | Q | 2026-11-21 |
| hid | `124` | `SetNpadJoyAssignmentModeDual` | — | Q | 2026-11-21 |
| hid | `125` | `MergeSingleJoyAsDualJoy` | — | Q | 2026-11-21 |
| hid | `126` | `StartLrAssignmentMode` | — | Q | 2026-11-21 |
| hid | `127` | `StopLrAssignmentMode` | — | Q | 2026-11-21 |
| hid | `128` | `SetNpadHandheldActivationMode` | — | Q | 2026-11-21 |
| hid | `129` | `GetNpadHandheldActivationMode` | — | Q | 2026-11-21 |
| hid | `130` | `SwapNpadAssignment` | — | Q | 2026-11-21 |
| hid | `131` | `IsUnintendedHomeButtonInputProtectionEnabled` | — | Q | 2026-11-21 |
| hid | `132` | `EnableUnintendedHomeButtonInputProtection` | — | Q | 2026-11-21 |
| hid | `133` | `SetNpadJoyAssignmentModeSingleWithDestination` | 5.0.0+ | Q | 2026-11-21 |
| hid | `134` | `SetNpadAnalogStickUseCenterClamp` | 6.1.0+ | Q | 2026-11-21 |
| hid | `135` | `SetNpadCaptureButtonAssignment` | 8.0.0+ | Q | 2026-11-21 |
| hid | `136` | `ClearNpadCaptureButtonAssignment` | 8.0.0+ | Q | 2026-11-21 |
| hid | `200` | `GetVibrationDeviceInfo` | — | Q | 2026-11-21 |
| hid | `201` | `SendVibrationValue` | — | Q | 2026-11-21 |
| hid | `202` | `GetActualVibrationValue` | — | Q | 2026-11-21 |
| hid | `203` | `CreateActiveVibrationDeviceList` | — | Q | 2026-11-21 |
| hid | `204` | `PermitVibration` | — | Q | 2026-11-21 |
| hid | `205` | `IsVibrationPermitted` | — | Q | 2026-11-21 |
| hid | `206` | `SendVibrationValues` | — | Q | 2026-11-21 |
| hid | `207` | `SendVibrationGcErmCommand` | 4.0.0+ | Q | 2026-11-21 |
| hid | `208` | `GetActualVibrationGcErmCommand` | 4.0.0+ | Q | 2026-11-21 |
| hid | `209` | `BeginPermitVibrationSession` | 4.0.0+ | Q | 2026-11-21 |
| hid | `210` | `EndPermitVibrationSession` | 4.0.0+ | Q | 2026-11-21 |
| hid | `211` | `IsVibrationDeviceMounted` | 7.0.0+ | Q | 2026-11-21 |
| hid | `300` | `ActivateConsoleSixAxisSensor` | 3.0.0+ | Q | 2026-11-21 |
| hid | `301` | `StartConsoleSixAxisSensor` | 3.0.0+ | Q | 2026-11-21 |
| hid | `302` | `StopConsoleSixAxisSensor` | 3.0.0+ | Q | 2026-11-21 |
| hid | `303` | `ActivateSevenSixAxisSensor` | 5.0.0+ | Q | 2026-11-21 |
| hid | `304` | `StartSevenSixAxisSensor` | 5.0.0+ | Q | 2026-11-21 |
| hid | `305` | `StopSevenSixAxisSensor` | 5.0.0+ | Q | 2026-11-21 |
| hid | `306` | `InitializeSevenSixAxisSensor` | 5.0.0+ | Q | 2026-11-21 |
| hid | `307` | `FinalizeSevenSixAxisSensor` | 5.0.0+ | Q | 2026-11-21 |
| hid | `308` | `SetSevenSixAxisSensorFusionStrength` | 5.0.0+ | Q | 2026-11-21 |
| hid | `309` | `GetSevenSixAxisSensorFusionStrength` | 5.0.0+ | Q | 2026-11-21 |
| hid | `310` | `ResetSevenSixAxisSensorTimestamp` | 6.0.0+ | Q | 2026-11-21 |
| hid | `400` | `IsUsbFullKeyControllerEnabled` | 3.0.0+ | Q | 2026-11-21 |
| hid | `401` | `EnableUsbFullKeyController` | 3.0.0+ | Q | 2026-11-21 |
| hid | `402` | `IsUsbFullKeyControllerConnected` | 3.0.0+ | Q | 2026-11-21 |
| hid | `403` | `HasBattery` | 4.0.0+ | Q | 2026-11-21 |
| hid | `404` | `HasLeftRightBattery` | 4.0.0+ | Q | 2026-11-21 |
| hid | `405` | `GetNpadInterfaceType` | 4.0.0+ | Q | 2026-11-21 |
| hid | `406` | `GetNpadLeftRightInterfaceType` | 4.0.0+ | Q | 2026-11-21 |
| hid | `407` | `GetNpadOfHighestBatteryLevelForJoyLeft` | 9.0.0+ | Q | 2026-11-21 |
| hid | `408` | `GetNpadOfHighestBatteryLevelForJoyRight` | 9.0.0+ | Q | 2026-11-21 |
| hid | `500` | `GetPalmaConnectionHandle` | 5.0.0+ | Q | 2026-11-21 |
| hid | `501` | `InitializePalma` | 5.0.0+ | Q | 2026-11-21 |
| hid | `502` | `AcquirePalmaOperationCompleteEvent` | 5.0.0+ | Q | 2026-11-21 |
| hid | `503` | `GetPalmaOperationInfo` | 5.0.0+ | Q | 2026-11-21 |
| hid | `504` | `PlayPalmaActivity` | 5.0.0+ | Q | 2026-11-21 |
| hid | `505` | `SetPalmaFrModeType` | 5.0.0+ | Q | 2026-11-21 |
| hid | `506` | `ReadPalmaStep` | 5.0.0+ | Q | 2026-11-21 |
| hid | `507` | `EnablePalmaStep` | 5.0.0+ | Q | 2026-11-21 |
| hid | `508` | `ResetPalmaStep` | 5.0.0+ | Q | 2026-11-21 |
| hid | `509` | `ReadPalmaApplicationSection` | 5.0.0+ | Q | 2026-11-21 |
| hid | `510` | `WritePalmaApplicationSection` | 5.0.0+ | Q | 2026-11-21 |
| hid | `511` | `ReadPalmaUniqueCode` | 5.0.0+ | Q | 2026-11-21 |
| hid | `512` | `SetPalmaUniqueCodeInvalid` | 5.0.0+ | Q | 2026-11-21 |
| hid | `513` | `WritePalmaActivityEntry` | 5.0.0+ | Q | 2026-11-21 |
| hid | `514` | `WritePalmaRgbLedPatternEntry` | 5.0.0+ | Q | 2026-11-21 |
| hid | `515` | `WritePalmaWaveEntry` | 5.0.0+ | Q | 2026-11-21 |
| hid | `516` | `SetPalmaDataBaseIdentificationVersion` | 5.0.0+ | Q | 2026-11-21 |
| hid | `517` | `GetPalmaDataBaseIdentificationVersion` | 5.0.0+ | Q | 2026-11-21 |
| hid | `518` | `SuspendPalmaFeature` | 5.0.0+ | Q | 2026-11-21 |
| hid | `519` | `GetPalmaOperationResult` | 5.1.0+ | Q | 2026-11-21 |
| hid | `520` | `ReadPalmaPlayLog` | 5.1.0+ | Q | 2026-11-21 |
| hid | `521` | `ResetPalmaPlayLog` | 5.1.0+ | Q | 2026-11-21 |
| hid | `522` | `SetIsPalmaAllConnectable` | 5.1.0+ | Q | 2026-11-21 |
| hid | `523` | `SetIsPalmaPairedConnectable` | 5.1.0+ | Q | 2026-11-21 |
| hid | `524` | `PairPalma` | 5.1.0+ | Q | 2026-11-21 |
| hid | `525` | `SetPalmaBoostMode` | 5.1.0+ | Q | 2026-11-21 |
| hid | `526` | `CancelWritePalmaWaveEntry` | 7.0.0+ | Q | 2026-11-21 |
| hid | `527` | `EnablePalmaBoostMode` | 8.0.0+ | Q | 2026-11-21 |
| hid | `528` | `GetPalmaBluetoothAddress` | 8.0.0+ | Q | 2026-11-21 |
| hid | `529` | `SetDisallowedPalmaConnection` | 8.0.0+ | Q | 2026-11-21 |
| hid | `1000` | `SetNpadCommunicationMode` | — | Q | 2026-11-21 |
| hid | `1001` | `GetNpadCommunicationMode` | — | Q | 2026-11-21 |
| hid | `1002` | `SetTouchScreenConfiguration` | 9.0.0+ | Q | 2026-11-21 |
| hid | `1003` | `IsFirmwareUpdateNeededForNotification` | 9.0.0+ | Q | 2026-11-21 |
| hid | `0` | `GetSharedMemoryHandle` | — | Q | 2026-11-21 |
| hid | `0` | `ActivateVibrationDevice` | — | Q | 2026-11-21 |
| hid:dbg | `0` | `DeactivateDebugPad` | — | Q | 2026-11-21 |
| hid:dbg | `1` | `SetDebugPadAutoPilotState` | — | Q | 2026-11-21 |
| hid:dbg | `2` | `UnsetDebugPadAutoPilotState` | — | Q | 2026-11-21 |
| hid:dbg | `10` | `DeactivateTouchScreen` | — | Q | 2026-11-21 |
| hid:dbg | `11` | `SetTouchScreenAutoPilotState` | — | Q | 2026-11-21 |
| hid:dbg | `12` | `UnsetTouchScreenAutoPilotState` | — | Q | 2026-11-21 |
| hid:dbg | `13` | `GetTouchScreenConfiguration` | 9.0.0+ | Q | 2026-11-21 |
| hid:dbg | `20` | `DeactivateMouse` | — | Q | 2026-11-21 |
| hid:dbg | `21` | `SetMouseAutoPilotState` | — | Q | 2026-11-21 |
| hid:dbg | `22` | `UnsetMouseAutoPilotState` | — | Q | 2026-11-21 |
| hid:dbg | `30` | `DeactivateKeyboard` | — | Q | 2026-11-21 |
| hid:dbg | `31` | `SetKeyboardAutoPilotState` | — | Q | 2026-11-21 |
| hid:dbg | `32` | `UnsetKeyboardAutoPilotState` | — | Q | 2026-11-21 |
| hid:dbg | `50` | `DeactivateXpad` | — | Q | 2026-11-21 |
| hid:dbg | `51` | `SetXpadAutoPilotState` | — | Q | 2026-11-21 |
| hid:dbg | `52` | `UnsetXpadAutoPilotState` | — | Q | 2026-11-21 |
| hid:dbg | `60` | `ClearNpadSystemCommonPolicy` | 9.0.0+ | Q | 2026-11-21 |
| hid:dbg | `91` | `DeactivateGesture` | — | Q | 2026-11-21 |
| hid:dbg | `110` | `DeactivateHomeButton` | — | Q | 2026-11-21 |
| hid:dbg | `111` | `SetHomeButtonAutoPilotState` | — | Q | 2026-11-21 |
| hid:dbg | `112` | `UnsetHomeButtonAutoPilotState` | — | Q | 2026-11-21 |
| hid:dbg | `120` | `DeactivateSleepButton` | — | Q | 2026-11-21 |
| hid:dbg | `121` | `SetSleepButtonAutoPilotState` | — | Q | 2026-11-21 |
| hid:dbg | `122` | `UnsetSleepButtonAutoPilotState` | — | Q | 2026-11-21 |
| hid:dbg | `123` | `DeactivateInputDetector` | — | Q | 2026-11-21 |
| hid:dbg | `130` | `DeactivateCaptureButton` | — | Q | 2026-11-21 |
| hid:dbg | `131` | `SetCaptureButtonAutoPilotState` | — | Q | 2026-11-21 |
| hid:dbg | `132` | `UnsetCaptureButtonAutoPilotState` | — | Q | 2026-11-21 |
| hid:dbg | `133` | `SetShiftAccelerometerCalibrationValue` | 3.0.0+ | Q | 2026-11-21 |
| hid:dbg | `134` | `GetShiftAccelerometerCalibrationValue` | 3.0.0+ | Q | 2026-11-21 |
| hid:dbg | `135` | `SetShiftGyroscopeCalibrationValue` | 3.0.0+ | Q | 2026-11-21 |
| hid:dbg | `136` | `GetShiftGyroscopeCalibrationValue` | 3.0.0+ | Q | 2026-11-21 |
| hid:dbg | `140` | `DeactivateConsoleSixAxisSensor` | 3.0.0+ | Q | 2026-11-21 |
| hid:dbg | `141` | `GetConsoleSixAxisSensorSamplingFrequency` | 5.0.0+ | Q | 2026-11-21 |
| hid:dbg | `142` | `DeactivateSevenSixAxisSensor` | 5.0.0+ | Q | 2026-11-21 |
| hid:dbg | `143` | `GetConsoleSixAxisSensorCountStates` | 5.0.0+ | Q | 2026-11-21 |
| hid:dbg | `144` | `GetAccelerometerFsr` | 8.0.0+ | Q | 2026-11-21 |
| hid:dbg | `145` | `SetAccelerometerFsr` | 8.0.0+ | Q | 2026-11-21 |
| hid:dbg | `146` | `GetAccelerometerOdr` | 8.0.0+ | Q | 2026-11-21 |
| hid:dbg | `147` | `SetAccelerometerOdr` | 8.0.0+ | Q | 2026-11-21 |
| hid:dbg | `148` | `GetGyroscopeFsr` | 8.0.0+ | Q | 2026-11-21 |
| hid:dbg | `149` | `SetGyroscopeFsr` | 8.0.0+ | Q | 2026-11-21 |
| hid:dbg | `150` | `GetGyroscopeOdr` | 8.0.0+ | Q | 2026-11-21 |
| hid:dbg | `151` | `SetGyroscopeOdr` | 8.0.0+ | Q | 2026-11-21 |
| hid:dbg | `201` | `ActivateFirmwareUpdate` | — | Q | 2026-11-21 |
| hid:dbg | `202` | `DeactivateFirmwareUpdate` | — | Q | 2026-11-21 |
| hid:dbg | `203` | `StartFirmwareUpdate` | — | Q | 2026-11-21 |
| hid:dbg | `204` | `GetFirmwareUpdateStage` | — | Q | 2026-11-21 |
| hid:dbg | `205` | `GetFirmwareVersion` | — | Q | 2026-11-21 |
| hid:dbg | `206` | `GetDestinationFirmwareVersion` | — | Q | 2026-11-21 |
| hid:dbg | `207` | `DiscardFirmwareInfoCacheForRevert` | — | Q | 2026-11-21 |
| hid:dbg | `208` | `StartFirmwareUpdateForRevert` | 3.0.0+ | Q | 2026-11-21 |
| hid:dbg | `209` | `GetAvailableFirmwareVersionForRevert` | 3.0.0+ | Q | 2026-11-21 |
| hid:dbg | `210` | `IsFirmwareUpdatingDevice` | 4.0.0+ | Q | 2026-11-21 |
| hid:dbg | `211` | `StartFirmwareUpdateIndividual` | 6.0.0+ | Q | 2026-11-21 |
| hid:dbg | `215` | `SetUsbFirmwareForceUpdateEnabled` | 6.0.0+ | Q | 2026-11-21 |
| hid:dbg | `216` | `SetAllKuinaDevicesToFirmwareUpdateMode` | 6.0.0+ | Q | 2026-11-21 |
| hid:dbg | `221` | `UpdateControllerColor` | 3.0.0+ | Q | 2026-11-21 |
| hid:dbg | `222` | `ConnectUsbPadsAsync` | 4.0.0+ | Q | 2026-11-21 |
| hid:dbg | `223` | `DisconnectUsbPadsAsync` | 4.0.0+ | Q | 2026-11-21 |
| hid:dbg | `224` | `UpdateDesignInfo` | 5.0.0+ | Q | 2026-11-21 |
| hid:dbg | `225` | `GetUniquePadDriverState` | 5.0.0+ | Q | 2026-11-21 |
| hid:dbg | `226` | `GetSixAxisSensorDriverStates` | 5.0.0+ | Q | 2026-11-21 |
| hid:dbg | `227` | `GetRxPacketHistory` | 5.0.0+ | Q | 2026-11-21 |
| hid:dbg | `228` | `AcquireOperationEventHandle` | 6.0.0+ | Q | 2026-11-21 |
| hid:dbg | `229` | `ReadSerialFlash` | 6.0.0+ | Q | 2026-11-21 |
| hid:dbg | `230` | `WriteSerialFlash` | 6.0.0+ | Q | 2026-11-21 |
| hid:dbg | `231` | `GetOperationResult` | 6.0.0+ | Q | 2026-11-21 |
| hid:dbg | `232` | `EnableShipmentMode` | 6.0.0+ | Q | 2026-11-21 |
| hid:dbg | `233` | `ClearPairingInfo` | 6.0.0+ | Q | 2026-11-21 |
| hid:dbg | `234` | `GetUniquePadDeviceTypeSetInternal` | 6.0.0+ | Q | 2026-11-21 |
| hid:dbg | `235` | `EnableAnalogStickPower` | 7.0.0+ | Q | 2026-11-21 |
| hid:dbg | `236` | `RequestKuinaUartClockCal` | 9.0.0+ | Q | 2026-11-21 |
| hid:dbg | `237` | `GetKuinaUartClockCal` | 9.0.0+ | Q | 2026-11-21 |
| hid:dbg | `238` | `SetKuinaUartClockTrim` | 9.0.0+ | Q | 2026-11-21 |
| hid:dbg | `239` | `KuinaLoopbackTest` | 9.0.0+ | Q | 2026-11-21 |
| hid:dbg | `240` | `RequestBatteryVoltage` | 9.0.0+ | Q | 2026-11-21 |
| hid:dbg | `241` | `GetBatteryVoltage` | 9.0.0+ | Q | 2026-11-21 |
| hid:dbg | `242` | `GetUniquePadPowerInfo` | 9.0.0+ | Q | 2026-11-21 |
| hid:dbg | `243` | `RebootUniquePad` | 9.0.0+ | Q | 2026-11-21 |
| hid:dbg | `244` | `RequestKuinaFirmwareVersion` | 9.0.0+ | Q | 2026-11-21 |
| hid:dbg | `245` | `GetKuinaFirmwareVersion` | 9.0.0+ | Q | 2026-11-21 |
| hid:dbg | `246` | `GetVidPid` | 9.0.0+ | Q | 2026-11-21 |
| hid:dbg | `301` | `GetAbstractedPadHandles` | 5.0.0-8.1.0 | Q | 2026-11-21 |
| hid:dbg | `302` | `GetAbstractedPadState` | 5.0.0-8.1.0 | Q | 2026-11-21 |
| hid:dbg | `303` | `GetAbstractedPadsState` | 5.0.0-8.1.0 | Q | 2026-11-21 |
| hid:dbg | `321` | `SetAutoPilotVirtualPadState` | 5.0.0-8.1.0 | Q | 2026-11-21 |
| hid:dbg | `322` | `UnsetAutoPilotVirtualPadState` | 5.0.0-8.1.0 | Q | 2026-11-21 |
| hid:dbg | `323` | `UnsetAllAutoPilotVirtualPadState` | 5.0.0+ | Q | 2026-11-21 |
| hid:dbg | `324` | `AttachHdlsWorkBuffer` | 7.0.0+ | Q | 2026-11-21 |
| hid:dbg | `325` | `ReleaseHdlsWorkBuffer` | 7.0.0+ | Q | 2026-11-21 |
| hid:dbg | `326` | `DumpHdlsNpadAssignmentState` | 7.0.0+ | Q | 2026-11-21 |
| hid:dbg | `327` | `DumpHdlsStates` | 7.0.0+ | Q | 2026-11-21 |
| hid:dbg | `328` | `ApplyHdlsNpadAssignmentState` | 7.0.0+ | Q | 2026-11-21 |
| hid:dbg | `329` | `ApplyHdlsStateList` | 7.0.0+ | Q | 2026-11-21 |
| hid:dbg | `330` | `AttachHdlsVirtualDevice` | 7.0.0+ | Q | 2026-11-21 |
| hid:dbg | `331` | `DetachHdlsVirtualDevice` | 7.0.0+ | Q | 2026-11-21 |
| hid:dbg | `332` | `SetHdlsState` | 7.0.0+ | Q | 2026-11-21 |
| hid:dbg | `350` | `AddRegisteredDevice` | 5.0.0+ | Q | 2026-11-21 |
| hid:dbg | `400` | `DisableExternalMcuOnNxDevice` | 6.0.0+ | Q | 2026-11-21 |
| hid:dbg | `401` | `DisableRailDeviceFiltering` | 6.0.0+ | Q | 2026-11-21 |
| hid:dbg | `500` | `SetFactoryInt` | 8.0.0+ | Q | 2026-11-21 |
| hid:dbg | `501` | `IsFactoryBootEnabled` | 8.0.0+ | Q | 2026-11-21 |
| hid:dbg | `550` | `SetAnalogStickModelDataTemporarily` | 9.0.0+ | Q | 2026-11-21 |
| hid:dbg | `551` | `GetAnalogStickModelData` | 9.0.0+ | Q | 2026-11-21 |
| hid:dbg | `552` | `ResetAnalogStickModelData` | 9.0.0+ | Q | 2026-11-21 |
| hid:sys | `31` | `SendKeyboardLockKeyEvent` | — | Q | 2026-11-21 |
| hid:sys | `101` | `AcquireHomeButtonEventHandle` | — | Q | 2026-11-21 |
| hid:sys | `111` | `ActivateHomeButton` | — | Q | 2026-11-21 |
| hid:sys | `121` | `AcquireSleepButtonEventHandle` | — | Q | 2026-11-21 |
| hid:sys | `131` | `ActivateSleepButton` | — | Q | 2026-11-21 |
| hid:sys | `141` | `AcquireCaptureButtonEventHandle` | — | Q | 2026-11-21 |
| hid:sys | `151` | `ActivateCaptureButton` | — | Q | 2026-11-21 |
| hid:sys | `161` | `GetPlatformConfig` | 7.0.0+ | Q | 2026-11-21 |
| hid:sys | `210` | `AcquireNfcDeviceUpdateEventHandle` | — | Q | 2026-11-21 |
| hid:sys | `211` | `GetNpadsWithNfc` | — | Q | 2026-11-21 |
| hid:sys | `212` | `AcquireNfcActivateEventHandle` | — | Q | 2026-11-21 |
| hid:sys | `213` | `ActivateNfc` | — | Q | 2026-11-21 |
| hid:sys | `214` | `GetXcdHandleForNpadWithNfc` | 4.0.0+ | Q | 2026-11-21 |
| hid:sys | `215` | `IsNfcActivated` | 4.0.0+ | Q | 2026-11-21 |
| hid:sys | `230` | `AcquireIrSensorEventHandle` | — | Q | 2026-11-21 |
| hid:sys | `231` | `ActivateIrSensor` | — | Q | 2026-11-21 |
| hid:sys | `301` | `ActivateNpadSystem` | — | Q | 2026-11-21 |
| hid:sys | `303` | `ApplyNpadSystemCommonPolicy` | — | Q | 2026-11-21 |
| hid:sys | `304` | `EnableAssigningSingleOnSlSrPress` | — | Q | 2026-11-21 |
| hid:sys | `305` | `DisableAssigningSingleOnSlSrPress` | — | Q | 2026-11-21 |
| hid:sys | `306` | `GetLastActiveNpad` | — | Q | 2026-11-21 |
| hid:sys | `307` | `GetNpadSystemExtStyle` | — | Q | 2026-11-21 |
| hid:sys | `308` | `ApplyNpadSystemCommonPolicyFull` | 5.0.0+ | Q | 2026-11-21 |
| hid:sys | `309` | `GetNpadFullKeyGripColor` | 5.0.0+ | Q | 2026-11-21 |
| hid:sys | `310` | `GetMaskedSupportedNpadStyleSet` | 6.0.0+ | Q | 2026-11-21 |
| hid:sys | `311` | `SetNpadPlayerLedBlinkingDevice` | — | Q | 2026-11-21 |
| hid:sys | `312` | `SetSupportedNpadStyleSetAll` | 6.0.0+ | Q | 2026-11-21 |
| hid:sys | `313` | `GetNpadCaptureButtonAssignment` | 9.0.0+ | Q | 2026-11-21 |
| hid:sys | `314` | `GetAppletFooterUiType` | 9.0.0+ | Q | 2026-11-21 |
| hid:sys | `315` | `GetAppletDetailedUiType` | 9.0.0+ | Q | 2026-11-21 |
| hid:sys | `321` | `GetUniquePadsFromNpad` | 3.0.0+ | Q | 2026-11-21 |
| hid:sys | `322` | `GetIrSensorState` | — | Q | 2026-11-21 |
| hid:sys | `323` | `GetXcdHandleForNpadWithIrSensor` | — | Q | 2026-11-21 |
| hid:sys | `500` | `SetAppletResourceUserId` | — | Q | 2026-11-21 |
| hid:sys | `501` | `RegisterAppletResourceUserId` | — | Q | 2026-11-21 |
| hid:sys | `502` | `UnregisterAppletResourceUserId` | — | Q | 2026-11-21 |
| hid:sys | `503` | `EnableAppletToGetInput` | — | Q | 2026-11-21 |
| hid:sys | `504` | `SetAruidValidForVibration` | — | Q | 2026-11-21 |
| hid:sys | `505` | `EnableAppletToGetSixAxisSensor` | — | Q | 2026-11-21 |
| hid:sys | `510` | `SetVibrationMasterVolume` | — | Q | 2026-11-21 |
| hid:sys | `511` | `GetVibrationMasterVolume` | — | Q | 2026-11-21 |
| hid:sys | `512` | `BeginPermitVibrationSession` | 3.0.0+ | Q | 2026-11-21 |
| hid:sys | `513` | `EndPermitVibrationSession` | 3.0.0+ | Q | 2026-11-21 |
| hid:sys | `520` | `EnableHandheldHids` | — | Q | 2026-11-21 |
| hid:sys | `521` | `DisableHandheldHids` | — | Q | 2026-11-21 |
| hid:sys | `522` | `SetJoyConRailEnabled` | 9.0.0+ | Q | 2026-11-21 |
| hid:sys | `523` | `IsJoyConRailEnabled` | 9.0.0+ | Q | 2026-11-21 |
| hid:sys | `540` | `AcquirePlayReportControllerUsageUpdateEvent` | — | Q | 2026-11-21 |
| hid:sys | `541` | `GetPlayReportControllerUsages` | — | Q | 2026-11-21 |
| hid:sys | `542` | `AcquirePlayReportRegisteredDeviceUpdateEvent` | — | Q | 2026-11-21 |
| hid:sys | `543` | `GetRegisteredDevicesOld ([1.0.0-4.1.0] GetRegisteredDevices)` | — | Q | 2026-11-21 |
| hid:sys | `544` | `AcquireConnectionTriggerTimeoutEvent` | 3.0.0+ | Q | 2026-11-21 |
| hid:sys | `545` | `SendConnectionTrigger` | 3.0.0+ | Q | 2026-11-21 |
| hid:sys | `546` | `AcquireDeviceRegisteredEventForControllerSupport` | 3.0.0+ | Q | 2026-11-21 |
| hid:sys | `547` | `GetAllowedBluetoothLinksCount` | 3.0.0+ | Q | 2026-11-21 |
| hid:sys | `548` | `GetRegisteredDevices` | 5.0.0+ | Q | 2026-11-21 |
| hid:sys | `549` | `GetConnectableRegisteredDevices` | 6.0.0+ | Q | 2026-11-21 |
| hid:sys | `700` | `ActivateUniquePad` | — | Q | 2026-11-21 |
| hid:sys | `702` | `AcquireUniquePadConnectionEventHandle` | — | Q | 2026-11-21 |
| hid:sys | `703` | `GetUniquePadIds` | — | Q | 2026-11-21 |
| hid:sys | `751` | `AcquireJoyDetachOnBluetoothOffEventHandle` | — | Q | 2026-11-21 |
| hid:sys | `800` | `ListSixAxisSensorHandles` | — | Q | 2026-11-21 |
| hid:sys | `801` | `IsSixAxisSensorUserCalibrationSupported` | — | Q | 2026-11-21 |
| hid:sys | `802` | `ResetSixAxisSensorCalibrationValues` | — | Q | 2026-11-21 |
| hid:sys | `803` | `StartSixAxisSensorUserCalibration` | — | Q | 2026-11-21 |
| hid:sys | `804` | `CancelSixAxisSensorUserCalibration` | — | Q | 2026-11-21 |
| hid:sys | `805` | `GetUniquePadBluetoothAddress` | 3.0.0+ | Q | 2026-11-21 |
| hid:sys | `806` | `DisconnectUniquePad` | 3.0.0+ | Q | 2026-11-21 |
| hid:sys | `807` | `GetUniquePadType` | 5.0.0+ | Q | 2026-11-21 |
| hid:sys | `808` | `GetUniquePadInterface` | 5.0.0+ | Q | 2026-11-21 |
| hid:sys | `809` | `GetUniquePadSerialNumber` | 5.0.0+ | Q | 2026-11-21 |
| hid:sys | `810` | `GetUniquePadControllerNumber` | 5.0.0+ | Q | 2026-11-21 |
| hid:sys | `811` | `GetSixAxisSensorUserCalibrationStage` | 5.0.0+ | Q | 2026-11-21 |
| hid:sys | `812` | `GetConsoleUniqueSixAxisSensorHandle` | 8.0.0+ | Q | 2026-11-21 |
| hid:sys | `821` | `StartAnalogStickManualCalibration` | — | Q | 2026-11-21 |
| hid:sys | `822` | `RetryCurrentAnalogStickManualCalibrationStage` | — | Q | 2026-11-21 |
| hid:sys | `823` | `CancelAnalogStickManualCalibration` | — | Q | 2026-11-21 |
| hid:sys | `824` | `ResetAnalogStickManualCalibration` | — | Q | 2026-11-21 |
| hid:sys | `825` | `GetAnalogStickState` | 5.0.0+ | Q | 2026-11-21 |
| hid:sys | `826` | `GetAnalogStickManualCalibrationStage` | 5.0.0+ | Q | 2026-11-21 |
| hid:sys | `827` | `IsAnalogStickButtonPressed` | 5.0.0+ | Q | 2026-11-21 |
| hid:sys | `828` | `IsAnalogStickInReleasePosition` | 5.0.0+ | Q | 2026-11-21 |
| hid:sys | `829` | `IsAnalogStickInCircumference` | 5.0.0+ | Q | 2026-11-21 |
| hid:sys | `830` | `SetNotificationLedPattern` | 7.0.0+ | Q | 2026-11-21 |
| hid:sys | `831` | `SetNotificationLedPatternWithTimeout` | 9.0.0+ | Q | 2026-11-21 |
| hid:sys | `832` | `PrepareHidsForNotificationWake` | 9.0.0+ | Q | 2026-11-21 |
| hid:sys | `850` | `IsUsbFullKeyControllerEnabled` | 3.0.0+ | Q | 2026-11-21 |
| hid:sys | `851` | `EnableUsbFullKeyController` | 3.0.0+ | Q | 2026-11-21 |
| hid:sys | `852` | `IsUsbConnected` | 3.0.0+ | Q | 2026-11-21 |
| hid:sys | `870` | `IsHandheldButtonPressedOnConsoleMode` | 5.1.0+ | Q | 2026-11-21 |
| hid:sys | `900` | `ActivateInputDetector` | — | Q | 2026-11-21 |
| hid:sys | `901` | `NotifyInputDetector` | — | Q | 2026-11-21 |
| hid:sys | `1000` | `InitializeFirmwareUpdate` | 3.0.0+ | Q | 2026-11-21 |
| hid:sys | `1001` | `GetFirmwareVersion` | 3.0.0+ | Q | 2026-11-21 |
| hid:sys | `1002` | `GetAvailableFirmwareVersion` | 3.0.0+ | Q | 2026-11-21 |
| hid:sys | `1003` | `IsFirmwareUpdateAvailable` | 3.0.0+ | Q | 2026-11-21 |
| hid:sys | `1004` | `CheckFirmwareUpdateRequired` | 3.0.0+ | Q | 2026-11-21 |
| hid:sys | `1005` | `StartFirmwareUpdate` | 3.0.0+ | Q | 2026-11-21 |
| hid:sys | `1006` | `AbortFirmwareUpdate` | 3.0.0+ | Q | 2026-11-21 |
| hid:sys | `1007` | `GetFirmwareUpdateState` | 3.0.0+ | Q | 2026-11-21 |
| hid:sys | `1008` | `ActivateAudioControl` | 4.0.0+ | Q | 2026-11-21 |
| hid:sys | `1009` | `AcquireAudioControlEventHandle` | 4.0.0+ | Q | 2026-11-21 |
| hid:sys | `1010` | `GetAudioControlStates` | 4.0.0+ | Q | 2026-11-21 |
| hid:sys | `1011` | `DeactivateAudioControl` | 4.0.0+ | Q | 2026-11-21 |
| hid:sys | `1050` | `IsSixAxisSensorAccurateUserCalibrationSupported` | 5.0.0+ | Q | 2026-11-21 |
| hid:sys | `1051` | `StartSixAxisSensorAccurateUserCalibration` | 5.0.0+ | Q | 2026-11-21 |
| hid:sys | `1052` | `CancelSixAxisSensorAccurateUserCalibration` | 5.0.0+ | Q | 2026-11-21 |
| hid:sys | `1053` | `GetSixAxisSensorAccurateUserCalibrationState` | 5.0.0+ | Q | 2026-11-21 |
| hid:sys | `1100` | `GetHidbusSystemServiceObject` | 5.0.0+ | Q | 2026-11-21 |
| hid:sys | `1120` | `SetFirmwareHotfixUpdateSkipEnabled` | 6.0.0+ | Q | 2026-11-21 |
| hid:sys | `1130` | `InitializeUsbFirmwareUpdate` | 6.0.0+ | Q | 2026-11-21 |
| hid:sys | `1131` | `FinalizeUsbFirmwareUpdate` | 6.0.0+ | Q | 2026-11-21 |
| hid:sys | `1132` | `CheckUsbFirmwareUpdateRequired` | 6.0.0+ | Q | 2026-11-21 |
| hid:sys | `1133` | `StartUsbFirmwareUpdate` | 6.0.0+ | Q | 2026-11-21 |
| hid:sys | `1134` | `GetUsbFirmwareUpdateState` | 6.0.0+ | Q | 2026-11-21 |
| hid:sys | `1150` | `SetTouchScreenMagnification` | 8.0.0+ | Q | 2026-11-21 |
| hid:sys | `1151` | `GetTouchScreenFirmwareVersion` | 9.0.0+ | Q | 2026-11-21 |
| hid:sys | `1152` | `SetTouchScreenDefaultConfiguration` | 9.0.0+ | Q | 2026-11-21 |
| hid:sys | `1153` | `GetTouchScreenDefaultConfiguration` | 9.0.0+ | Q | 2026-11-21 |
| hid:sys | `1154` | `IsFirmwareAvailableForNotification` | 9.0.0+ | Q | 2026-11-21 |
| hid:sys | `1155` | `SetForceHandheldStyleVibration` | 9.0.0+ | Q | 2026-11-21 |
| hid:sys | `1156` | `SendConnectionTriggerWithoutTimeoutEvent` | 9.0.0+ | Q | 2026-11-21 |
| hid:tmp | `0` | `GetConsoleSixAxisSensorCalibrationValues` | — | Q | 2026-11-21 |
| irs | `302` | `ActivateIrsensor` | — | Q | 2026-11-21 |
| irs | `303` | `DeactivateIrsensor` | — | Q | 2026-11-21 |
| irs | `304` | `GetIrsensorSharedMemoryHandle` | — | Q | 2026-11-21 |
| irs | `305` | `StopImageProcessor` | — | Q | 2026-11-21 |
| irs | `306` | `RunMomentProcessor` | — | Q | 2026-11-21 |
| irs | `307` | `RunClusteringProcessor` | — | Q | 2026-11-21 |
| irs | `308` | `RunImageTransferProcessor` | — | Q | 2026-11-21 |
| irs | `309` | `GetImageTransferProcessorState` | — | Q | 2026-11-21 |
| irs | `310` | `RunTeraPluginProcessor` | — | Q | 2026-11-21 |
| irs | `311` | `GetNpadIrCameraHandle` | — | Q | 2026-11-21 |
| irs | `312` | `RunPointingProcessor` | — | Q | 2026-11-21 |
| irs | `313` | `SuspendImageProcessor` | — | Q | 2026-11-21 |
| irs | `314` | `CheckFirmwareVersion` | 3.0.0+ | Q | 2026-11-21 |
| irs | `315` | `SetFunctionLevel` | 4.0.0+ | Q | 2026-11-21 |
| irs | `316` | `RunImageTransferExProcessor` | 4.0.0+ | Q | 2026-11-21 |
| irs | `317` | `RunIrLedProcessor` | 4.0.0+ | Q | 2026-11-21 |
| irs | `318` | `StopImageProcessorAsync` | 4.0.0+ | Q | 2026-11-21 |
| irs | `319` | `ActivateIrsensorWithFunctionLevel` | 4.0.0+ | Q | 2026-11-21 |
| irs:sys | `500` | `SetAppletResourceUserId` | — | Q | 2026-11-21 |
| irs:sys | `501` | `RegisterAppletResourceUserId` | — | Q | 2026-11-21 |
| irs:sys | `502` | `UnregisterAppletResourceUserId` | — | Q | 2026-11-21 |
| irs:sys | `503` | `EnableAppletToGetInput` | — | Q | 2026-11-21 |
| ahid:cd | `0` | `AcquireDevice` | — | Q | 2026-11-21 |
| ahid:cd | `1` | `ReleaseDevice` | — | Q | 2026-11-21 |
| ahid:cd | `2` | `GetCtrlSession` | — | Q | 2026-11-21 |
| ahid:cd | `3` | `GetReadSession` | — | Q | 2026-11-21 |
| ahid:cd | `0` | `GetString` | — | Q | 2026-11-21 |
| ahid:cd | `1` | `GetCodeBook` | — | Q | 2026-11-21 |
| ahid:cd | `2` | `GetReport` | — | Q | 2026-11-21 |
| ahid:cd | `3` | `SetReport` | — | Q | 2026-11-21 |
| ahid:cd | `4` | `GetIdle` | — | Q | 2026-11-21 |
| ahid:cd | `5` | `SetIdle` | — | Q | 2026-11-21 |
| ahid:cd | `6` | `GetProtocol` | — | Q | 2026-11-21 |
| ahid:cd | `7` | `SetProtocol` | — | Q | 2026-11-21 |
| ahid:cd | `8` | `GetDescriptor` | — | Q | 2026-11-21 |
| ahid:cd | `9` | `SetDescriptor` | — | Q | 2026-11-21 |
| ahid:cd | `10` | `GetStateChangeEvent` | — | Q | 2026-11-21 |
| ahid:cd | `11` | `SignalStateChangeEvent` | — | Q | 2026-11-21 |
| ahid:cd | `12` | `Write` | 3.0.0+ | Q | 2026-11-21 |
| ahid:cd | `0` | `Read` | — | Q | 2026-11-21 |
| ahid:cd | `0` | `Write` | — | Q | 2026-11-21 |
| ahid:hdr | `0` | `GetDeviceEntries` | — | Q | 2026-11-21 |
| ahid:hdr | `1` | `GetDeviceList` | — | Q | 2026-11-21 |
| ahid:hdr | `2` | `GetDeviceParameters` | — | Q | 2026-11-21 |
| ahid:hdr | `3` | `AttachDevice` | — | Q | 2026-11-21 |
| ahid:hdr | `4` | `DetachDevice` | — | Q | 2026-11-21 |
| ahid:hdr | `5` | `SetDeviceFilter` | 6.0.0+ | Q | 2026-11-21 |
| xcd:sys | `0` | `GetDataFormat` | — | Q | 2026-11-21 |
| xcd:sys | `1` | `SetDataFormat` | — | Q | 2026-11-21 |
| xcd:sys | `2` | `GetMcuState` | — | Q | 2026-11-21 |
| xcd:sys | `3` | `SetMcuState` | — | Q | 2026-11-21 |
| xcd:sys | `4` | `GetMcuVersionForNfc` | — | Q | 2026-11-21 |
| xcd:sys | `5` | `CheckNfcDevicePower` | — | Q | 2026-11-21 |
| xcd:sys | `10` | `SetNfcEvent` | — | Q | 2026-11-21 |
| xcd:sys | `11` | `GetNfcInfo` | — | Q | 2026-11-21 |
| xcd:sys | `12` | `StartNfcDiscovery` | — | Q | 2026-11-21 |
| xcd:sys | `13` | `StopNfcDiscovery` | — | Q | 2026-11-21 |
| xcd:sys | `14` | `StartNtagRead` | — | Q | 2026-11-21 |
| xcd:sys | `15` | `StartNtagWrite` | — | Q | 2026-11-21 |
| xcd:sys | `16` | `SendNfcRawData` | — | Q | 2026-11-21 |
| xcd:sys | `17` | `RegisterMifareKey` | — | Q | 2026-11-21 |
| xcd:sys | `18` | `ClearMifareKey` | — | Q | 2026-11-21 |
| xcd:sys | `19` | `StartMifareRead` | — | Q | 2026-11-21 |
| xcd:sys | `20` | `StartMifareWrite` | — | Q | 2026-11-21 |
| xcd:sys | `101` | `GetAwakeTriggerReasonForLeftRail` | — | Q | 2026-11-21 |
| xcd:sys | `102` | `GetAwakeTriggerReasonForRightRail` | — | Q | 2026-11-21 |
| hidbus | `1` | `GetBusHandle` | — | Q | 2026-11-21 |
| hidbus | `2` | `IsExternalDeviceConnected` | — | Q | 2026-11-21 |
| hidbus | `3` | `Initialize` | — | Q | 2026-11-21 |
| hidbus | `4` | `Finalize` | — | Q | 2026-11-21 |
| hidbus | `5` | `EnableExternalDevice` | — | Q | 2026-11-21 |
| hidbus | `6` | `GetExternalDeviceId` | — | Q | 2026-11-21 |
| hidbus | `7` | `SendCommandAsync` | — | Q | 2026-11-21 |
| hidbus | `8` | `GetSendCommandAsynceResult` | — | Q | 2026-11-21 |
| hidbus | `9` | `SetEventForSendCommandAsycResult` | — | Q | 2026-11-21 |
| hidbus | `10` | `GetSharedMemoryHandle` | — | Q | 2026-11-21 |
| hidbus | `11` | `EnableJoyPollingReceiveMode` | — | Q | 2026-11-21 |
| hidbus | `12` | `DisableJoyPollingReceiveMode` | — | Q | 2026-11-21 |
| hidbus | `14` | `SetStatusManagerType` | 6.0.0+ | Q | 2026-11-21 |

### Applet Manager services

[Wiki SwitchBrew](https://switchbrew.org/wiki/Applet_Manager_services) · [miroir](https://github.com/backupbrew/switchbrew/blob/master/Applet%20Manager%20services.md)

**410 commandes documentées** (snapshot du miroir).

| Interface / section | ID | Fonction | Disponibilité indiquée | Encore | Vérifié |
|---|---|---|---|---|---|
| appletAE | `100` | `OpenSystemAppletProxy` | — | Q | 2026-11-21 |
| appletAE | `200` | `OpenLibraryAppletProxyOld ([1.0.0-2.3.0] OpenLibraryAppletProxy)` | — | Q | 2026-11-21 |
| appletAE | `201` | `OpenLibraryAppletProxy` | 3.0.0+ | Q | 2026-11-21 |
| appletAE | `300` | `OpenOverlayAppletProxy` | — | Q | 2026-11-21 |
| appletAE | `350` | `OpenSystemApplicationProxy` | — | Q | 2026-11-21 |
| appletAE | `400` | `CreateSelfLibraryAppletCreatorForDevelop` | — | Q | 2026-11-21 |
| appletAE | `410` | `GetSystemAppletControllerForDebug` | 6.0.0+ | Q | 2026-11-21 |
| appletAE | `1000` | `GetDebugFunctions` | 6.0.0+ | Q | 2026-11-21 |
| appletAE | `0` | `GetCommonStateGetter` | — | Q | 2026-11-21 |
| appletAE | `1` | `GetSelfController` | — | Q | 2026-11-21 |
| appletAE | `2` | `GetWindowController` | — | Q | 2026-11-21 |
| appletAE | `3` | `GetAudioController` | — | Q | 2026-11-21 |
| appletAE | `4` | `GetDisplayController` | — | Q | 2026-11-21 |
| appletAE | `10` | `GetProcessWindingController` | — | Q | 2026-11-21 |
| appletAE | `11` | `GetLibraryAppletCreator` | — | Q | 2026-11-21 |
| appletAE | `20` | `GetHomeMenuFunctions` | — | Q | 2026-11-21 |
| appletAE | `21` | `GetGlobalStateController` | — | Q | 2026-11-21 |
| appletAE | `22` | `GetApplicationCreator` | — | Q | 2026-11-21 |
| appletAE | `23` | `GetAppletCommonFunctions` | 7.0.0+ | Q | 2026-11-21 |
| appletAE | `10` | `RequestToGetForeground` | — | Q | 2026-11-21 |
| appletAE | `11` | `LockForeground` | — | Q | 2026-11-21 |
| appletAE | `12` | `UnlockForeground` | — | Q | 2026-11-21 |
| appletAE | `20` | `PopFromGeneralChannel` | — | Q | 2026-11-21 |
| appletAE | `21` | `GetPopFromGeneralChannelEvent` | — | Q | 2026-11-21 |
| appletAE | `30` | `GetHomeButtonWriterLockAccessor` | — | Q | 2026-11-21 |
| appletAE | `31` | `GetWriterLockAccessorEx` | 2.0.0+ | Q | 2026-11-21 |
| appletAE | `100` | `PopRequestLaunchApplicationForDebug` | 6.0.0+ | Q | 2026-11-21 |
| appletAE | `110` | `IsForceTerminateApplicationDisabledForDebug` | 9.0.0+ | Q | 2026-11-21 |
| appletAE | `200` | `LaunchDevMenu` | 8.0.0+ | Q | 2026-11-21 |
| appletAE | `1` | `TryLock` | — | Q | 2026-11-21 |
| appletAE | `2` | `Unlock` | — | Q | 2026-11-21 |
| appletAE | `3` | `GetEvent` | — | Q | 2026-11-21 |
| appletAE | `0` | `RequestToEnterSleep` | — | Q | 2026-11-21 |
| appletAE | `1` | `EnterSleep` | — | Q | 2026-11-21 |
| appletAE | `2` | `StartSleepSequence` | — | Q | 2026-11-21 |
| appletAE | `3` | `StartShutdownSequence` | — | Q | 2026-11-21 |
| appletAE | `4` | `StartRebootSequence` | — | Q | 2026-11-21 |
| appletAE | `9` | `IsAutoPowerDownRequested` | 7.0.0+ | Q | 2026-11-21 |
| appletAE | `10` | `LoadAndApplyIdlePolicySettings` | — | Q | 2026-11-21 |
| appletAE | `11` | `NotifyCecSettingsChanged` | 2.0.0+ | Q | 2026-11-21 |
| appletAE | `12` | `SetDefaultHomeButtonLongPressTime` | 3.0.0+ | Q | 2026-11-21 |
| appletAE | `13` | `UpdateDefaultDisplayResolution` | 3.0.0+ | Q | 2026-11-21 |
| appletAE | `14` | `ShouldSleepOnBoot` | 3.0.0+ | Q | 2026-11-21 |
| appletAE | `15` | `GetHdcpAuthenticationFailedEvent` | 4.0.0+ | Q | 2026-11-21 |
| appletAE | `0` | `CreateApplication` | — | Q | 2026-11-21 |
| appletAE | `1` | `PopLaunchRequestedApplication` | — | Q | 2026-11-21 |
| appletAE | `10` | `CreateSystemApplication` | — | Q | 2026-11-21 |
| appletAE | `100` | `PopFloatingApplicationForDevelopment` | — | Q | 2026-11-21 |
| appletAE | `0` | `GetAppletStateChangedEvent` | — | Q | 2026-11-21 |
| appletAE | `1` | `IsCompleted` | — | Q | 2026-11-21 |
| appletAE | `10` | `Start` | — | Q | 2026-11-21 |
| appletAE | `20` | `RequestExit` | — | Q | 2026-11-21 |
| appletAE | `25` | `Terminate` | — | Q | 2026-11-21 |
| appletAE | `30` | `GetResult` | — | Q | 2026-11-21 |
| appletAE | `101` | `RequestForApplicationToGetForeground` | — | Q | 2026-11-21 |
| appletAE | `110` | `TerminateAllLibraryApplets` | — | Q | 2026-11-21 |
| appletAE | `111` | `AreAnyLibraryAppletsLeft` | — | Q | 2026-11-21 |
| appletAE | `112` | `GetCurrentLibraryApplet` | — | Q | 2026-11-21 |
| appletAE | `120` | `GetApplicationId` | — | Q | 2026-11-21 |
| appletAE | `121` | `PushLaunchParameter` | — | Q | 2026-11-21 |
| appletAE | `122` | `GetApplicationControlProperty` | — | Q | 2026-11-21 |
| appletAE | `123` | `GetApplicationLaunchProperty` | 2.0.0+ | Q | 2026-11-21 |
| appletAE | `124` | `GetApplicationLaunchRequestInfo` | 6.0.0+ | Q | 2026-11-21 |
| appletAE | `130` | `SetUsers` | 6.0.0+ | Q | 2026-11-21 |
| appletAE | `131` | `CheckRightsEnvironmentAvailable` | 6.0.0+ | Q | 2026-11-21 |
| appletAE | `132` | `GetNsRightsEnvironmentHandle` | 6.0.0+ | Q | 2026-11-21 |
| appletAE | `140` | `GetDesirableUids` | 6.0.0+ | Q | 2026-11-21 |
| appletAE | `150` | `ReportApplicationExitTimeout` | 6.0.0+ | Q | 2026-11-21 |
| appletAE | `160` | `SetApplicationAttribute` | 8.0.0+ | Q | 2026-11-21 |
| appletAE | `170` | `HasSaveDataAccessPermission` | 8.0.0+ | Q | 2026-11-21 |
| appletAE | `180` | `PushToFriendInvitationStorageChannel` | 9.0.0+ | Q | 2026-11-21 |
| appletAE | `190` | `PushToNotificationStorageChannel` | 9.0.0+ | Q | 2026-11-21 |
| appletAE | `0` | `SetTerminateResult` | 9.0.0+ | Q | 2026-11-21 |
| appletAE | `10` | `ReadThemeStorage` | — | Q | 2026-11-21 |
| appletAE | `11` | `WriteThemeStorage` | — | Q | 2026-11-21 |
| appletAE | `20` | `PushToAppletBoundChannel` | 9.0.0+ | Q | 2026-11-21 |
| appletAE | `21` | `TryPopFromAppletBoundChannel` | 9.0.0+ | Q | 2026-11-21 |
| appletAE | `40` | `GetDisplayLogicalResolution` | 8.0.0+ | Q | 2026-11-21 |
| appletAE | `42` | `SetDisplayMagnification` | 8.0.0+ | Q | 2026-11-21 |
| appletAE | `50` | `SetHomeButtonDoubleClickEnabled` | 8.0.0+ | Q | 2026-11-21 |
| appletAE | `51` | `GetHomeButtonDoubleClickEnabled` | 8.0.0+ | Q | 2026-11-21 |
| appletAE | `20` | `OpenLibraryAppletSelfAccessor` | — | Q | 2026-11-21 |
| appletAE | `21` | `GetAppletCommonFunctions` | 7.0.0+ | Q | 2026-11-21 |
| appletAE | `0` | `PopInData` | — | Q | 2026-11-21 |
| appletAE | `1` | `PushOutData` | — | Q | 2026-11-21 |
| appletAE | `2` | `PopInteractiveInData` | — | Q | 2026-11-21 |
| appletAE | `3` | `PushInteractiveOutData` | — | Q | 2026-11-21 |
| appletAE | `5` | `GetPopInDataEvent` | — | Q | 2026-11-21 |
| appletAE | `6` | `GetPopInteractiveInDataEvent` | — | Q | 2026-11-21 |
| appletAE | `10` | `ExitProcessAndReturn` | — | Q | 2026-11-21 |
| appletAE | `11` | `GetLibraryAppletInfo` | — | Q | 2026-11-21 |
| appletAE | `12` | `GetMainAppletIdentityInfo` | — | Q | 2026-11-21 |
| appletAE | `13` | `CanUseApplicationCore` | — | Q | 2026-11-21 |
| appletAE | `14` | `GetCallerAppletIdentityInfo` | — | Q | 2026-11-21 |
| appletAE | `15` | `GetMainAppletApplicationControlProperty` | 2.0.0+ | Q | 2026-11-21 |
| appletAE | `16` | `GetMainAppletStorageId` | 2.0.0+ | Q | 2026-11-21 |
| appletAE | `17` | `GetCallerAppletIdentityInfoStack` | 3.0.0+ | Q | 2026-11-21 |
| appletAE | `18` | `GetNextReturnDestinationAppletIdentityInfo` | 4.0.0+ | Q | 2026-11-21 |
| appletAE | `19` | `GetDesirableKeyboardLayout` | 4.0.0+ | Q | 2026-11-21 |
| appletAE | `20` | `PopExtraStorage` | — | Q | 2026-11-21 |
| appletAE | `25` | `GetPopExtraStorageEvent` | — | Q | 2026-11-21 |
| appletAE | `30` | `UnpopInData` | — | Q | 2026-11-21 |
| appletAE | `31` | `UnpopExtraStorage` | — | Q | 2026-11-21 |
| appletAE | `40` | `GetIndirectLayerProducerHandle` | 2.0.0+ | Q | 2026-11-21 |
| appletAE | `50` | `ReportVisibleError` | 3.0.0+ | Q | 2026-11-21 |
| appletAE | `51` | `ReportVisibleErrorWithErrorContext` | 4.0.0+ | Q | 2026-11-21 |
| appletAE | `60` | `GetMainAppletApplicationDesiredLanguage` | 4.0.0+ | Q | 2026-11-21 |
| appletAE | `70` | `GetCurrentApplicationId` | 8.0.0+ | Q | 2026-11-21 |
| appletAE | `80` | `RequestExitToSelf` | 6.0.0+ | Q | 2026-11-21 |
| appletAE | `90` | `CreateApplicationAndPushAndRequestToLaunch` | 5.0.0+ | Q | 2026-11-21 |
| appletAE | `100` | `CreateGameMovieTrimmer` | 4.0.0+ | Q | 2026-11-21 |
| appletAE | `101` | `ReserveResourceForMovieOperation` | 5.0.0+ | Q | 2026-11-21 |
| appletAE | `102` | `UnreserveResourceForMovieOperation` | 5.0.0+ | Q | 2026-11-21 |
| appletAE | `110` | `GetMainAppletAvailableUsers` | 6.0.0+ | Q | 2026-11-21 |
| appletAE | `120` | `GetLaunchStorageInfoForDebug` | 9.0.0+ | Q | 2026-11-21 |
| appletAE | `130` | `GetGpuErrorDetectedSystemEvent` | 9.0.0+ | Q | 2026-11-21 |
| appletAE | `20` | `GetOverlayFunctions` | — | Q | 2026-11-21 |
| appletAE | `0` | `BeginToWatchShortHomeButtonMessage` | — | Q | 2026-11-21 |
| appletAE | `1` | `EndToWatchShortHomeButtonMessage` | — | Q | 2026-11-21 |
| appletAE | `2` | `GetApplicationIdForLogo` | — | Q | 2026-11-21 |
| appletAE | `3` | `SetGpuTimeSliceBoost` | — | Q | 2026-11-21 |
| appletAE | `4` | `SetAutoSleepTimeAndDimmingTimeEnabled` | 2.0.0+ | Q | 2026-11-21 |
| appletAE | `5` | `TerminateApplicationAndSetReason` | 2.0.0+ | Q | 2026-11-21 |
| appletAE | `6` | `SetScreenShotPermissionGlobally` | 3.0.0+ | Q | 2026-11-21 |
| appletAE | `10` | `StartShutdownSequenceForOverlay` | 6.0.0+ | Q | 2026-11-21 |
| appletAE | `11` | `StartRebootSequenceForOverlay` | 6.0.0+ | Q | 2026-11-21 |
| appletAE | `20` | `SetHandlingHomeButtonShortPressedEnabled` | 8.0.0+ | Q | 2026-11-21 |
| appletAE | `30` | `SetHealthWarningShowingState` | 9.0.0+ | Q | 2026-11-21 |
| appletAE | `90` | `SetRequiresGpuResourceUse` | 7.0.0+ | Q | 2026-11-21 |
| appletAE | `101` | `BeginToObserveHidInputForDevelop` | 5.0.0+ | Q | 2026-11-21 |
| appletAE | `20` | `GetApplicationFunctions` | — | Q | 2026-11-21 |
| appletAE | `1` | `PopLaunchParameter` | — | Q | 2026-11-21 |
| appletAE | `10` | `CreateApplicationAndPushAndRequestToStart` | — | Q | 2026-11-21 |
| appletAE | `11` | `CreateApplicationAndPushAndRequestToStartForQuest` | 3.0.0+ | Q | 2026-11-21 |
| appletAE | `12` | `CreateApplicationAndRequestToStart` | 4.0.0+ | Q | 2026-11-21 |
| appletAE | `13` | `CreateApplicationAndRequestToStartForQuest` | 4.0.0+ | Q | 2026-11-21 |
| appletAE | `14` | `CreateApplicationWithAttributeAndPushAndRequestToStartForQuest` | 7.0.0+ | Q | 2026-11-21 |
| appletAE | `15` | `CreateApplicationWithAttributeAndRequestToStartForQuest` | 7.0.0+ | Q | 2026-11-21 |
| appletAE | `20` | `EnsureSaveData` | — | Q | 2026-11-21 |
| appletAE | `21` | `GetDesiredLanguage` | — | Q | 2026-11-21 |
| appletAE | `22` | `SetTerminateResult` | — | Q | 2026-11-21 |
| appletAE | `23` | `GetDisplayVersion` | — | Q | 2026-11-21 |
| appletAE | `24` | `GetLaunchStorageInfoForDebug` | 2.0.0+ | Q | 2026-11-21 |
| appletAE | `25` | `ExtendSaveData` | 3.0.0+ | Q | 2026-11-21 |
| appletAE | `26` | `GetSaveDataSize` | 3.0.0+ | Q | 2026-11-21 |
| appletAE | `27` | `CreateCacheStorage` | 5.0.0+ | Q | 2026-11-21 |
| appletAE | `30` | `BeginBlockingHomeButtonShortAndLongPressed` | — | Q | 2026-11-21 |
| appletAE | `31` | `EndBlockingHomeButtonShortAndLongPressed` | — | Q | 2026-11-21 |
| appletAE | `32` | `BeginBlockingHomeButton` | — | Q | 2026-11-21 |
| appletAE | `33` | `EndBlockingHomeButton` | — | Q | 2026-11-21 |
| appletAE | `40` | `NotifyRunning` | — | Q | 2026-11-21 |
| appletAE | `50` | `GetPseudoDeviceId` | 2.0.0+ | Q | 2026-11-21 |
| appletAE | `60` | `SetMediaPlaybackStateForApplication` | 2.0.0+ | Q | 2026-11-21 |
| appletAE | `65` | `IsGamePlayRecordingSupported` | 3.0.0+ | Q | 2026-11-21 |
| appletAE | `66` | `InitializeGamePlayRecording` | 3.0.0+ | Q | 2026-11-21 |
| appletAE | `67` | `SetGamePlayRecordingState` | 3.0.0+ | Q | 2026-11-21 |
| appletAE | `68` | `RequestFlushGamePlayingMovieForDebug` | 4.0.0+ | Q | 2026-11-21 |
| appletAE | `70` | `RequestToShutdown` | 3.0.0+ | Q | 2026-11-21 |
| appletAE | `71` | `RequestToReboot` | 3.0.0+ | Q | 2026-11-21 |
| appletAE | `80` | `ExitAndRequestToShowThanksMessage` | 4.0.0+ | Q | 2026-11-21 |
| appletAE | `90` | `EnableApplicationCrashReport` | 4.0.0+ | Q | 2026-11-21 |
| appletAE | `100` | `InitializeApplicationCopyrightFrameBuffer` | 5.0.0+ | Q | 2026-11-21 |
| appletAE | `101` | `SetApplicationCopyrightImage` | 5.0.0+ | Q | 2026-11-21 |
| appletAE | `102` | `SetApplicationCopyrightVisibility` | 5.0.0+ | Q | 2026-11-21 |
| appletAE | `110` | `QueryApplicationPlayStatistics` | 5.0.0+ | Q | 2026-11-21 |
| appletAE | `111` | `QueryApplicationPlayStatisticsByUid` | 6.0.0+ | Q | 2026-11-21 |
| appletAE | `120` | `ExecuteProgram` | 5.0.0+ | Q | 2026-11-21 |
| appletAE | `121` | `ClearUserChannel` | 5.0.0+ | Q | 2026-11-21 |
| appletAE | `122` | `UnpopToUserChannel` | 5.0.0+ | Q | 2026-11-21 |
| appletAE | `123` | `GetPreviousProgramIndex` | 5.0.0+ | Q | 2026-11-21 |
| appletAE | `124` | `EnableApplicationAllThreadDumpOnCrash` | 6.0.0+ | Q | 2026-11-21 |
| appletAE | `140` | `GetFriendInvitationStorageChannelEvent` | 9.0.0+ | Q | 2026-11-21 |
| appletAE | `141` | `TryPopFromFriendInvitationStorageChannel` | 9.0.0+ | Q | 2026-11-21 |
| appletAE | `150` | `GetNotificationStorageChannelEvent` | 9.0.0+ | Q | 2026-11-21 |
| appletAE | `151` | `TryPopFromNotificationStorageChannel` | 9.0.0+ | Q | 2026-11-21 |
| appletAE | `160` | `GetHealthWarningDisappearedSystemEvent` | 9.0.0+ | Q | 2026-11-21 |
| appletAE | `170` | `SetHdcpAuthenticationActivated` | 9.0.0+ | Q | 2026-11-21 |
| appletAE | `500` | `StartContinuousRecordingFlushForDebug` | 5.0.0+ | Q | 2026-11-21 |
| appletAE | `1000` | `CreateMovieMaker` | 5.0.0+ | Q | 2026-11-21 |
| appletAE | `1001` | `PrepareForJit` | 5.0.0+ | Q | 2026-11-21 |
| appletAE | `0` | `GetGrcMovieMaker` | — | Q | 2026-11-21 |
| appletAE | `1` | `GetLayerHandle` | — | Q | 2026-11-21 |
| appletAE | `0` | `CreateLibraryApplet` | — | Q | 2026-11-21 |
| appletAE | `1` | `TerminateAllLibraryApplets` | — | Q | 2026-11-21 |
| appletAE | `2` | `AreAnyLibraryAppletsLeft` | — | Q | 2026-11-21 |
| appletAE | `10` | `CreateStorage` | — | Q | 2026-11-21 |
| appletAE | `11` | `CreateTransferMemoryStorage` | — | Q | 2026-11-21 |
| appletAE | `12` | `CreateHandleStorage` | 2.0.0+ | Q | 2026-11-21 |
| appletAE | `50` | `SetOutOfFocusApplicationSuspendingEnabled` | — | Q | 2026-11-21 |
| appletAE | `100` | `PushInData` | — | Q | 2026-11-21 |
| appletAE | `101` | `PopOutData` | — | Q | 2026-11-21 |
| appletAE | `102` | `PushExtraStorage` | — | Q | 2026-11-21 |
| appletAE | `103` | `PushInteractiveInData` | — | Q | 2026-11-21 |
| appletAE | `104` | `PopInteractiveOutData` | — | Q | 2026-11-21 |
| appletAE | `105` | `GetPopOutDataEvent` | — | Q | 2026-11-21 |
| appletAE | `106` | `GetPopInteractiveOutDataEvent` | — | Q | 2026-11-21 |
| appletAE | `110` | `NeedsToExitProcess` | — | Q | 2026-11-21 |
| appletAE | `120` | `GetLibraryAppletInfo` | — | Q | 2026-11-21 |
| appletAE | `150` | `RequestForAppletToGetForeground` | — | Q | 2026-11-21 |
| appletAE | `160` | `GetIndirectLayerConsumerHandle` | 2.0.0+ | Q | 2026-11-21 |
| appletAE | `0` | `GetEventHandle` | — | Q | 2026-11-21 |
| appletAE | `1` | `ReceiveMessage` | — | Q | 2026-11-21 |
| appletAE | `2` | `GetThisAppletKind` | — | Q | 2026-11-21 |
| appletAE | `3` | `AllowToEnterSleep` | — | Q | 2026-11-21 |
| appletAE | `4` | `DisallowToEnterSleep` | — | Q | 2026-11-21 |
| appletAE | `5` | `GetOperationMode` | — | Q | 2026-11-21 |
| appletAE | `6` | `GetPerformanceMode` | — | Q | 2026-11-21 |
| appletAE | `7` | `GetCradleStatus` | — | Q | 2026-11-21 |
| appletAE | `8` | `GetBootMode` | — | Q | 2026-11-21 |
| appletAE | `9` | `GetCurrentFocusState` | — | Q | 2026-11-21 |
| appletAE | `10` | `RequestToAcquireSleepLock` | — | Q | 2026-11-21 |
| appletAE | `11` | `ReleaseSleepLock` | — | Q | 2026-11-21 |
| appletAE | `12` | `ReleaseSleepLockTransiently` | — | Q | 2026-11-21 |
| appletAE | `13` | `GetAcquiredSleepLockEvent` | — | Q | 2026-11-21 |
| appletAE | `20` | `PushToGeneralChannel` | — | Q | 2026-11-21 |
| appletAE | `30` | `GetHomeButtonReaderLockAccessor` | — | Q | 2026-11-21 |
| appletAE | `31` | `GetReaderLockAccessorEx` | 2.0.0+ | Q | 2026-11-21 |
| appletAE | `32` | `GetWriterLockAccessorEx` | 7.0.0+ | Q | 2026-11-21 |
| appletAE | `40` | `GetCradleFwVersion` | 2.0.0+ | Q | 2026-11-21 |
| appletAE | `50` | `IsVrModeEnabled` | 3.0.0+ | Q | 2026-11-21 |
| appletAE | `51` | `SetVrModeEnabled` | 3.0.0+ | Q | 2026-11-21 |
| appletAE | `52` | `SetLcdBacklighOffEnabled` | 4.0.0+ | Q | 2026-11-21 |
| appletAE | `53` | `BeginVrModeEx` | 7.0.0+ | Q | 2026-11-21 |
| appletAE | `54` | `EndVrModeEx` | 7.0.0+ | Q | 2026-11-21 |
| appletAE | `55` | `IsInControllerFirmwareUpdateSection` | 3.0.0+ | Q | 2026-11-21 |
| appletAE | `60` | `GetDefaultDisplayResolution` | 3.0.0+ | Q | 2026-11-21 |
| appletAE | `61` | `GetDefaultDisplayResolutionChangeEvent` | 3.0.0+ | Q | 2026-11-21 |
| appletAE | `62` | `GetHdcpAuthenticationState` | 4.0.0+ | Q | 2026-11-21 |
| appletAE | `63` | `GetHdcpAuthenticationStateChangeEvent` | 4.0.0+ | Q | 2026-11-21 |
| appletAE | `64` | `SetTvPowerStateMatchingMode` | 5.0.0+ | Q | 2026-11-21 |
| appletAE | `65` | `GetApplicationIdByContentActionName` | 5.1.0+ | Q | 2026-11-21 |
| appletAE | `66` | `SetCpuBoostMode` | 6.0.0+ | Q | 2026-11-21 |
| appletAE | `80` | `PerformSystemButtonPressingIfInFocus` | 6.0.0+ | Q | 2026-11-21 |
| appletAE | `90` | `SetPerformanceConfigurationChangedNotification` | 7.0.0+ | Q | 2026-11-21 |
| appletAE | `91` | `GetCurrentPerformanceConfiguration` | 7.0.0+ | Q | 2026-11-21 |
| appletAE | `200` | `GetOperationModeSystemInfo` | 7.0.0+ | Q | 2026-11-21 |
| appletAE | `300` | `GetSettingsPlatformRegion` | 9.0.0+ | Q | 2026-11-21 |
| appletAE | `0` | `Exit` | — | Q | 2026-11-21 |
| appletAE | `1` | `LockExit` | — | Q | 2026-11-21 |
| appletAE | `2` | `UnlockExit` | — | Q | 2026-11-21 |
| appletAE | `3` | `EnterFatalSection` | 2.0.0+ | Q | 2026-11-21 |
| appletAE | `4` | `LeaveFatalSection` | 2.0.0+ | Q | 2026-11-21 |
| appletAE | `9` | `GetLibraryAppletLaunchableEvent` | — | Q | 2026-11-21 |
| appletAE | `10` | `SetScreenShotPermission` | — | Q | 2026-11-21 |
| appletAE | `11` | `SetOperationModeChangedNotification` | — | Q | 2026-11-21 |
| appletAE | `12` | `SetPerformanceModeChangedNotification` | — | Q | 2026-11-21 |
| appletAE | `13` | `SetFocusHandlingMode` | — | Q | 2026-11-21 |
| appletAE | `14` | `SetRestartMessageEnabled` | — | Q | 2026-11-21 |
| appletAE | `15` | `SetScreenShotAppletIdentityInfo` | 2.0.0+ | Q | 2026-11-21 |
| appletAE | `16` | `SetOutOfFocusSuspendingEnabled` | 2.0.0+ | Q | 2026-11-21 |
| appletAE | `17` | `SetControllerFirmwareUpdateSection` | 3.0.0+ | Q | 2026-11-21 |
| appletAE | `18` | `SetRequiresCaptureButtonShortPressedMessage` | 3.0.0+ | Q | 2026-11-21 |
| appletAE | `19` | `SetAlbumImageOrientation` | 3.0.0+ | Q | 2026-11-21 |
| appletAE | `20` | `SetDesirableKeyboardLayout` | 4.0.0+ | Q | 2026-11-21 |
| appletAE | `40` | `CreateManagedDisplayLayer` | — | Q | 2026-11-21 |
| appletAE | `41` | `IsSystemBufferSharingEnabled` | 4.0.0+ | Q | 2026-11-21 |
| appletAE | `42` | `GetSystemSharedLayerHandle` | 4.0.0+ | Q | 2026-11-21 |
| appletAE | `43` | `GetSystemSharedBufferHandle` | 5.0.0+ | Q | 2026-11-21 |
| appletAE | `50` | `SetHandlesRequestToDisplay` | — | Q | 2026-11-21 |
| appletAE | `51` | `ApproveToDisplay` | — | Q | 2026-11-21 |
| appletAE | `60` | `OverrideAutoSleepTimeAndDimmingTime` | — | Q | 2026-11-21 |
| appletAE | `61` | `SetMediaPlaybackState` | — | Q | 2026-11-21 |
| appletAE | `62` | `SetIdleTimeDetectionExtension` | — | Q | 2026-11-21 |
| appletAE | `63` | `GetIdleTimeDetectionExtension` | — | Q | 2026-11-21 |
| appletAE | `64` | `SetInputDetectionSourceSet` | — | Q | 2026-11-21 |
| appletAE | `65` | `ReportUserIsActive` | 2.0.0+ | Q | 2026-11-21 |
| appletAE | `66` | `GetCurrentIlluminance` | 3.0.0+ | Q | 2026-11-21 |
| appletAE | `67` | `IsIlluminanceAvailable` | 3.0.0+ | Q | 2026-11-21 |
| appletAE | `68` | `SetAutoSleepDisabled` | 5.0.0+ | Q | 2026-11-21 |
| appletAE | `69` | `IsAutoSleepDisabled` | 5.0.0+ | Q | 2026-11-21 |
| appletAE | `70` | `ReportMultimediaError` | 4.0.0+ | Q | 2026-11-21 |
| appletAE | `71` | `GetCurrentIlluminanceEx` | 5.0.0+ | Q | 2026-11-21 |
| appletAE | `72` | `SetInputDetectionPolicy` | 9.0.0+ | Q | 2026-11-21 |
| appletAE | `80` | `SetWirelessPriorityMode` | 4.0.0+ | Q | 2026-11-21 |
| appletAE | `90` | `GetAccumulatedSuspendedTickValue` | 6.0.0+ | Q | 2026-11-21 |
| appletAE | `91` | `GetAccumulatedSuspendedTickChangedEvent` | 6.0.0+ | Q | 2026-11-21 |
| appletAE | `100` | `SetAlbumImageTakenNotificationEnabled` | 7.0.0+ | Q | 2026-11-21 |
| appletAE | `110` | `SetApplicationAlbumUserData` | 8.0.0+ | Q | 2026-11-21 |
| appletAE | `1000` | `GetDebugStorageChannel` | 7.0.0+ | Q | 2026-11-21 |
| appletAE | `0` | `Push` | — | Q | 2026-11-21 |
| appletAE | `1` | `Unpop` | — | Q | 2026-11-21 |
| appletAE | `2` | `Pop` | — | Q | 2026-11-21 |
| appletAE | `3` | `GetPopEventHandle` | — | Q | 2026-11-21 |
| appletAE | `4` | `Clear` | — | Q | 2026-11-21 |
| appletAE | `0` | `CreateWindow` | — | Q | 2026-11-21 |
| appletAE | `1` | `GetAppletResourceUserId` | — | Q | 2026-11-21 |
| appletAE | `2` | `GetAppletResourceUserIdOfCallerApplet` | 6.0.0+ | Q | 2026-11-21 |
| appletAE | `10` | `AcquireForegroundRights` | — | Q | 2026-11-21 |
| appletAE | `11` | `ReleaseForegroundRights` | — | Q | 2026-11-21 |
| appletAE | `12` | `RejectToChangeIntoBackground` | — | Q | 2026-11-21 |
| appletAE | `20` | `SetAppletWindowVisibility` | 7.0.0+ | Q | 2026-11-21 |
| appletAE | `21` | `SetAppletGpuTimeSlice` | 7.0.0+ | Q | 2026-11-21 |
| appletAE | `0` | `SetExpectedMasterVolume` | — | Q | 2026-11-21 |
| appletAE | `1` | `GetMainAppletExpectedMasterVolume` | — | Q | 2026-11-21 |
| appletAE | `2` | `GetLibraryAppletExpectedMasterVolume` | — | Q | 2026-11-21 |
| appletAE | `3` | `ChangeMainAppletMasterVolume` | — | Q | 2026-11-21 |
| appletAE | `4` | `SetTransparentVolumeRate` | — | Q | 2026-11-21 |
| appletAE | `0` | `GetLastForegroundCaptureImage` | — | Q | 2026-11-21 |
| appletAE | `1` | `UpdateLastForegroundCaptureImage` | — | Q | 2026-11-21 |
| appletAE | `2` | `GetLastApplicationCaptureImage` | — | Q | 2026-11-21 |
| appletAE | `3` | `GetCallerAppletCaptureImage` | — | Q | 2026-11-21 |
| appletAE | `4` | `UpdateCallerAppletCaptureImage` | — | Q | 2026-11-21 |
| appletAE | `5` | `GetLastForegroundCaptureImageEx` | — | Q | 2026-11-21 |
| appletAE | `6` | `GetLastApplicationCaptureImageEx` | — | Q | 2026-11-21 |
| appletAE | `7` | `GetCallerAppletCaptureImageEx` | — | Q | 2026-11-21 |
| appletAE | `8` | `TakeScreenShotOfOwnLayer` | 2.0.0+ | Q | 2026-11-21 |
| appletAE | `9` | `CopyBetweenCaptureBuffers` | 5.0.0+ | Q | 2026-11-21 |
| appletAE | `10` | `AcquireLastApplicationCaptureBuffer` | — | Q | 2026-11-21 |
| appletAE | `11` | `ReleaseLastApplicationCaptureBuffer` | — | Q | 2026-11-21 |
| appletAE | `12` | `AcquireLastForegroundCaptureBuffer` | — | Q | 2026-11-21 |
| appletAE | `13` | `ReleaseLastForegroundCaptureBuffer` | — | Q | 2026-11-21 |
| appletAE | `14` | `AcquireCallerAppletCaptureBuffer` | — | Q | 2026-11-21 |
| appletAE | `15` | `ReleaseCallerAppletCaptureBuffer` | — | Q | 2026-11-21 |
| appletAE | `16` | `AcquireLastApplicationCaptureBufferEx` | — | Q | 2026-11-21 |
| appletAE | `17` | `AcquireLastForegroundCaptureBufferEx` | — | Q | 2026-11-21 |
| appletAE | `18` | `AcquireCallerAppletCaptureBufferEx` | — | Q | 2026-11-21 |
| appletAE | `20` | `ClearCaptureBuffer` | 3.0.0+ | Q | 2026-11-21 |
| appletAE | `21` | `ClearAppletTransitionBuffer` | 3.0.0+ | Q | 2026-11-21 |
| appletAE | `22` | `AcquireLastApplicationCaptureSharedBuffer` | 4.0.0+ | Q | 2026-11-21 |
| appletAE | `23` | `ReleaseLastApplicationCaptureSharedBuffer` | 4.0.0+ | Q | 2026-11-21 |
| appletAE | `24` | `AcquireLastForegroundCaptureSharedBuffer` | 4.0.0+ | Q | 2026-11-21 |
| appletAE | `25` | `ReleaseLastForegroundCaptureSharedBuffer` | 4.0.0+ | Q | 2026-11-21 |
| appletAE | `26` | `AcquireCallerAppletCaptureSharedBuffer` | 4.0.0+ | Q | 2026-11-21 |
| appletAE | `27` | `ReleaseCallerAppletCaptureSharedBuffer` | 4.0.0+ | Q | 2026-11-21 |
| appletAE | `28` | `TakeScreenShotOfOwnLayerEx` | 6.0.0+ | Q | 2026-11-21 |
| appletAE | `1` | `RequestLaunchApplicationForDebug` | — | Q | 2026-11-21 |
| appletAE | `2` | `GetDebugStorageChannel` | 7.0.0+ | Q | 2026-11-21 |
| appletAE | `3` | `CreateStorageForDebug` | 7.0.0+ | Q | 2026-11-21 |
| appletAE | `0` | `GetLaunchReason` | — | Q | 2026-11-21 |
| appletAE | `11` | `OpenCallingLibraryApplet` | — | Q | 2026-11-21 |
| appletAE | `21` | `PushContext` | — | Q | 2026-11-21 |
| appletAE | `22` | `PopContext` | — | Q | 2026-11-21 |
| appletAE | `23` | `CancelWindingReservation` | — | Q | 2026-11-21 |
| appletAE | `30` | `WindAndDoReserved` | — | Q | 2026-11-21 |
| appletAE | `40` | `ReserveToStartAndWaitAndUnwindThis` | — | Q | 2026-11-21 |
| appletAE | `41` | `ReserveToStartAndWait` | 4.0.0+ | Q | 2026-11-21 |
| appletAE | `0` | `NotifyMessageToHomeMenuForDebug` | — | Q | 2026-11-21 |
| appletAE | `1` | `OpenMainApplication` | — | Q | 2026-11-21 |
| appletAE | `10` | `PerformSystemButtonPressing` | — | Q | 2026-11-21 |
| appletAE | `20` | `InvalidateTransitionLayer` | — | Q | 2026-11-21 |
| appletAE | `30` | `RequestLaunchApplicationWithUserAndArgumentForDebug` | 6.0.0+ | Q | 2026-11-21 |
| appletAE | `40` | `GetAppletResourceUsageInfo` | 6.0.0+ | Q | 2026-11-21 |
| appletAE | `100` | `SetCpuBoostModeForApplet` | 7.0.0+ | Q | 2026-11-21 |
| appletAE | `110` | `PushToAppletBoundChannelForDebug` | 9.0.0+ | Q | 2026-11-21 |
| appletAE | `111` | `TryPopFromAppletBoundChannelForDebug` | 9.0.0+ | Q | 2026-11-21 |
| appletAE | `120` | `AlarmSettingNotificationEnableAppEventReserve` | 9.0.0+ | Q | 2026-11-21 |
| appletAE | `121` | `AlarmSettingNotificationDisableAppEventReserve` | 9.0.0+ | Q | 2026-11-21 |
| appletAE | `122` | `AlarmSettingNotificationPushAppEventNotify` | 9.0.0+ | Q | 2026-11-21 |
| appletAE | `130` | `FriendInvitationSetApplicationParameter` | 9.0.0+ | Q | 2026-11-21 |
| appletAE | `131` | `FriendInvitationClearApplicationParameter` | 9.0.0+ | Q | 2026-11-21 |
| appletAE | `132` | `FriendInvitationPushApplicationParameter` | 9.0.0+ | Q | 2026-11-21 |
| appletAE | `0` | `Open` | — | Q | 2026-11-21 |
| appletAE | `1` | `OpenTransferStorage` | 2.0.0+ | Q | 2026-11-21 |
| appletAE | `0` | `GetSize` | — | Q | 2026-11-21 |
| appletAE | `10` | `Write` | — | Q | 2026-11-21 |
| appletAE | `11` | `Read` | — | Q | 2026-11-21 |
| appletAE | `1` | `GetHandle` | — | Q | 2026-11-21 |
| appletOE | `0` | `OpenApplicationProxy` | — | Q | 2026-11-21 |
| idle:sys | `0` | `GetAutoPowerDownEvent` | — | Q | 2026-11-21 |
| idle:sys | `3` | `SetHandlingContext` | — | Q | 2026-11-21 |
| idle:sys | `4` | `LoadAndApplySettings` | — | Q | 2026-11-21 |
| idle:sys | `5` | `ReportUserIsActive` | — | Q | 2026-11-21 |
| omm | `0` | `GetOperationMode` | — | Q | 2026-11-21 |
| omm | `1` | `GetOperationModeChangeEvent` | — | Q | 2026-11-21 |
| omm | `2` | `EnableAudioVisual` | — | Q | 2026-11-21 |
| omm | `3` | `DisableAudioVisual` | — | Q | 2026-11-21 |
| omm | `4` | `EnterSleepAndWait` | — | Q | 2026-11-21 |
| omm | `5` | `GetCradleStatus` | — | Q | 2026-11-21 |
| omm | `6` | `FadeInDisplay` | — | Q | 2026-11-21 |
| omm | `7` | `FadeOutDisplay` | — | Q | 2026-11-21 |
| omm | `8` | `GetCradleFwVersion` | 2.0.0+ | Q | 2026-11-21 |
| omm | `9` | `NotifyCecSettingsChanged` | 2.0.0+ | Q | 2026-11-21 |
| omm | `10` | `SetOperationModePolicy` | 3.0.0+ | Q | 2026-11-21 |
| omm | `11` | `GetDefaultDisplayResolution` | 3.0.0+ | Q | 2026-11-21 |
| omm | `12` | `GetDefaultDisplayResolutionChangeEvent` | 3.0.0+ | Q | 2026-11-21 |
| omm | `13` | `UpdateDefaultDisplayResolution` | 3.0.0+ | Q | 2026-11-21 |
| omm | `14` | `ShouldSleepOnBoot` | 3.0.0+ | Q | 2026-11-21 |
| omm | `15` | `NotifyHdcpApplicationExecutionStarted` | 4.0.0+ | Q | 2026-11-21 |
| omm | `16` | `NotifyHdcpApplicationExecutionFinished` | 4.0.0+ | Q | 2026-11-21 |
| omm | `17` | `NotifyHdcpApplicationDrawingStarted` | 4.0.0+ | Q | 2026-11-21 |
| omm | `18` | `NotifyHdcpApplicationDrawingFinished` | 4.0.0+ | Q | 2026-11-21 |
| omm | `19` | `GetHdcpAuthenticationFailedEvent` | 4.0.0+ | Q | 2026-11-21 |
| omm | `20` | `GetHdcpAuthenticationFailedEmulationEnabled` | 4.0.0+ | Q | 2026-11-21 |
| omm | `21` | `SetHdcpAuthenticationFailedEmulation` | 4.0.0+ | Q | 2026-11-21 |
| omm | `22` | `GetHdcpStateChangeEvent` | 4.0.0+ | Q | 2026-11-21 |
| omm | `23` | `GetHdcpState` | 4.0.0+ | Q | 2026-11-21 |
| omm | `24` | `ShowCardUpdateProcessing` | 5.0.0+ | Q | 2026-11-21 |
| omm | `25` | `SetApplicationCecSettingsAndNotifyChanged` | 5.0.0+ | Q | 2026-11-21 |
| omm | `26` | `GetOperationModeSystemInfo` | 7.0.0+ | Q | 2026-11-21 |
| omm | `27` | `GetAppletFullAwakingSystemEvent` | 9.0.0+ | Q | 2026-11-21 |
| spsm | `0` | `GetCurrentState` | — | Q | 2026-11-21 |
| spsm | `1` | `EnterSleep` | — | Q | 2026-11-21 |
| spsm | `2` | `GetLastWakeReason` | — | Q | 2026-11-21 |
| spsm | `3` | `Shutdown` | — | Q | 2026-11-21 |
| spsm | `4` | `GetNotificationMessageEventHandle` | — | Q | 2026-11-21 |
| spsm | `5` | `ReceiveNotificationMessage` | — | Q | 2026-11-21 |
| spsm | `6` | `AnalyzeLogForLastSleepWakeSequence` | — | Q | 2026-11-21 |
| spsm | `7` | `ResetEventLog` | — | Q | 2026-11-21 |
| spsm | `8` | `AnalyzePerformanceLogForLastSleepWakeSequence` | — | Q | 2026-11-21 |
| spsm | `9` | `ChangeHomeButtonLongPressingTime` | — | Q | 2026-11-21 |
| spsm | `10` | `PutErrorState` | — | Q | 2026-11-21 |
| spsm | `11` | `InvalidateCurrentHomeButtonPressing` | 1.0.0-3.0.2 | Q | 2026-11-21 |
| tcap | `0` | `GetContinuousHighSkinTemperatureEvent` | — | Q | 2026-11-21 |
| tcap | `1` | `SetOperationMode` | — | Q | 2026-11-21 |
| tcap | `2` | `LoadAndApplySettings` | — | Q | 2026-11-21 |
| caps:su | `32` | `SetShimLibraryVersion` | 7.0.0+ | Q | 2026-11-21 |
| caps:su | `201` | `SaveScreenShot` | — | Q | 2026-11-21 |
| caps:su | `203` | `SaveScreenShotEx0` | — | Q | 2026-11-21 |
| caps:su | `205` | `SaveScreenShotEx1` | 8.0.0+ | Q | 2026-11-21 |
| caps:su | `210` | `SaveScreenShotEx2` | — | Q | 2026-11-21 |

### NS Services   
  am: Application Manager, su: System Update

[Wiki SwitchBrew](https://switchbrew.org/wiki/NS_Services___
__am:_Application_Manager,_su:_System_Update) · [miroir](https://github.com/backupbrew/switchbrew/blob/master/NS%20Services.md)

**471 commandes documentées** (snapshot du miroir).

| Interface / section | ID | Fonction | Disponibilité indiquée | Encore | Vérifié |
|---|---|---|---|---|---|
| aoc:u | `0` | `CountAddOnContentByApplicationId` | 1.0.0-6.2.0 | Q | 2026-11-21 |
| aoc:u | `1` | `ListAddOnContentByApplicationId` | 1.0.0-6.2.0 | Q | 2026-11-21 |
| aoc:u | `2` | `CountAddOnContent` | — | Q | 2026-11-21 |
| aoc:u | `3` | `ListAddOnContent` | — | Q | 2026-11-21 |
| aoc:u | `4` | `GetAddOnContentBaseIdByApplicationId` | 1.0.0-6.2.0 | Q | 2026-11-21 |
| aoc:u | `5` | `GetAddOnContentBaseId` | — | Q | 2026-11-21 |
| aoc:u | `6` | `PrepareAddOnContentByApplicationId` | 1.0.0-6.2.0 | Q | 2026-11-21 |
| aoc:u | `7` | `PrepareAddOnContent` | — | Q | 2026-11-21 |
| aoc:u | `8` | `GetAddOnContentListChangedEvent` | 4.0.0+ | Q | 2026-11-21 |
| aoc:u | `100` | `[CreateEcPurchasedEventManager](#IPurchaseEventManager "wikilink")` | 7.0.0+ | Q | 2026-11-21 |
| aoc:u | `101` | `[CreatePermanentEcPurchasedEventManager](#IPurchaseEventManager "wikilink")` | 9.0.0+ | Q | 2026-11-21 |
| aoc:u | `0` | `SetDefaultDeliveryTarget` | — | Q | 2026-11-21 |
| aoc:u | `1` | `SetDeliveryTarget` | — | Q | 2026-11-21 |
| aoc:u | `2` | `GetPurchasedEventReadableHandle` | — | Q | 2026-11-21 |
| aoc:u | `3` | `PopPurchasedProductInfo` | — | Q | 2026-11-21 |
| aoc:u | `4` | `PopPurchasedProductInfoWithUid` | 9.0.0+ | Q | 2026-11-21 |
| ns:am | `0` | `ListApplicationRecord` | — | Q | 2026-11-21 |
| ns:am | `1` | `GenerateApplicationRecordCount` | — | Q | 2026-11-21 |
| ns:am | `2` | `GetApplicationRecordUpdateSystemEvent` | — | Q | 2026-11-21 |
| ns:am | `3` | `GetApplicationViewDeprecated` | — | Q | 2026-11-21 |
| ns:am | `4` | `DeleteApplicationEntity` | — | Q | 2026-11-21 |
| ns:am | `5` | `DeleteApplicationCompletely` | — | Q | 2026-11-21 |
| ns:am | `6` | `IsAnyApplicationEntityRedundant` | — | Q | 2026-11-21 |
| ns:am | `7` | `DeleteRedundantApplicationEntity` | — | Q | 2026-11-21 |
| ns:am | `8` | `IsApplicationEntityMovable` | — | Q | 2026-11-21 |
| ns:am | `9` | `MoveApplicationEntity` | — | Q | 2026-11-21 |
| ns:am | `11` | `CalculateApplicationOccupiedSize` | — | Q | 2026-11-21 |
| ns:am | `16` | `PushApplicationRecord` | — | Q | 2026-11-21 |
| ns:am | `17` | `ListApplicationRecordContentMeta` | — | Q | 2026-11-21 |
| ns:am | `19` | `LaunchApplication` | — | Q | 2026-11-21 |
| ns:am | `21` | `GetApplicationContentPath` | — | Q | 2026-11-21 |
| ns:am | `22` | `TerminateApplication` | — | Q | 2026-11-21 |
| ns:am | `23` | `ResolveApplicationContentPath` | 2.0.0+ | Q | 2026-11-21 |
| ns:am | `26` | `BeginInstallApplication` | — | Q | 2026-11-21 |
| ns:am | `27` | `DeleteApplicationRecord` | — | Q | 2026-11-21 |
| ns:am | `30` | `RequestApplicationUpdateInfo` | — | Q | 2026-11-21 |
| ns:am | `31` | `RequestUpdateApplication` | — | Q | 2026-11-21 |
| ns:am | `32` | `CancelApplicationDownload` | — | Q | 2026-11-21 |
| ns:am | `33` | `ResumeApplicationDownload` | — | Q | 2026-11-21 |
| ns:am | `35` | `UpdateVersionList` | — | Q | 2026-11-21 |
| ns:am | `36` | `PushLaunchVersion` | — | Q | 2026-11-21 |
| ns:am | `37` | `ListRequiredVersion` | — | Q | 2026-11-21 |
| ns:am | `38` | `CheckApplicationLaunchVersion` | — | Q | 2026-11-21 |
| ns:am | `39` | `CheckApplicationLaunchRights` | — | Q | 2026-11-21 |
| ns:am | `40` | `GetApplicationLogoData` | — | Q | 2026-11-21 |
| ns:am | `41` | `CalculateApplicationDownloadRequiredSize` | — | Q | 2026-11-21 |
| ns:am | `42` | `CleanupSdCard` | — | Q | 2026-11-21 |
| ns:am | `43` | `CheckSdCardMountStatus` | — | Q | 2026-11-21 |
| ns:am | `44` | `GetSdCardMountStatusChangedEvent` | — | Q | 2026-11-21 |
| ns:am | `45` | `GetGameCardAttachmentEvent` | — | Q | 2026-11-21 |
| ns:am | `46` | `GetGameCardAttachmentInfo` | — | Q | 2026-11-21 |
| ns:am | `47` | `GetTotalSpaceSize` | — | Q | 2026-11-21 |
| ns:am | `48` | `GetFreeSpaceSize` | — | Q | 2026-11-21 |
| ns:am | `49` | `GetSdCardRemovedEvent` | — | Q | 2026-11-21 |
| ns:am | `52` | `GetGameCardUpdateDetectionEvent` | — | Q | 2026-11-21 |
| ns:am | `53` | `DisableApplicationAutoDelete` | — | Q | 2026-11-21 |
| ns:am | `54` | `EnableApplicationAutoDelete` | — | Q | 2026-11-21 |
| ns:am | `55` | `GetApplicationDesiredLanguage` | — | Q | 2026-11-21 |
| ns:am | `56` | `SetApplicationTerminateResult` | — | Q | 2026-11-21 |
| ns:am | `57` | `ClearApplicationTerminateResult` | — | Q | 2026-11-21 |
| ns:am | `58` | `GetLastSdCardMountUnexpectedResult` | — | Q | 2026-11-21 |
| ns:am | `59` | `ConvertApplicationLanguageToLanguageCode` | — | Q | 2026-11-21 |
| ns:am | `60` | `ConvertLanguageCodeToApplicationLanguage` | — | Q | 2026-11-21 |
| ns:am | `61` | `GetBackgroundDownloadStressTaskInfo` | — | Q | 2026-11-21 |
| ns:am | `62` | `GetGameCardStopper` | — | Q | 2026-11-21 |
| ns:am | `63` | `IsSystemProgramInstalled` | — | Q | 2026-11-21 |
| ns:am | `64` | `StartApplyDeltaTask` | 2.0.0+ | Q | 2026-11-21 |
| ns:am | `65` | `GetRequestServerStopper` | 2.0.0+ | Q | 2026-11-21 |
| ns:am | `100` | `ResetToFactorySettings` | — | Q | 2026-11-21 |
| ns:am | `101` | `ResetToFactorySettingsWithoutUserSaveData` | — | Q | 2026-11-21 |
| ns:am | `102` | `ResetToFactorySettingsForRefurbishment` | 2.0.0+ | Q | 2026-11-21 |
| ns:am | `200` | `CalculateUserSaveDataStatistics` | — | Q | 2026-11-21 |
| ns:am | `201` | `DeleteUserSaveDataAll` | — | Q | 2026-11-21 |
| ns:am | `210` | `DeleteUserSystemSaveData` | — | Q | 2026-11-21 |
| ns:am | `220` | `UnregisterNetworkServiceAccount` | — | Q | 2026-11-21 |
| ns:am | `300` | `GetApplicationShellEvent` | — | Q | 2026-11-21 |
| ns:am | `301` | `PopApplicationShellEventInfo` | — | Q | 2026-11-21 |
| ns:am | `302` | `LaunchLibraryApplet` | — | Q | 2026-11-21 |
| ns:am | `303` | `TerminateLibraryApplet` | — | Q | 2026-11-21 |
| ns:am | `304` | `LaunchSystemApplet` | — | Q | 2026-11-21 |
| ns:am | `305` | `TerminateSystemApplet` | — | Q | 2026-11-21 |
| ns:am | `306` | `LaunchOverlayApplet` | — | Q | 2026-11-21 |
| ns:am | `307` | `TerminateOverlayApplet` | — | Q | 2026-11-21 |
| ns:am | `400` | `GetApplicationControlData` | — | Q | 2026-11-21 |
| ns:am | `401` | `InvalidateAllApplicationControlCache` | — | Q | 2026-11-21 |
| ns:am | `402` | `RequestDownloadApplicationControlData` | — | Q | 2026-11-21 |
| ns:am | `403` | `GetMaxApplicationControlCacheCount` | — | Q | 2026-11-21 |
| ns:am | `404` | `InvalidateApplicationControlCache` | 2.0.0+ | Q | 2026-11-21 |
| ns:am | `405` | `ListApplicationControlCacheEntryInfo` | 2.0.0+ | Q | 2026-11-21 |
| ns:am | `502` | `RequestCheckGameCardRegistration` | 2.0.0+ | Q | 2026-11-21 |
| ns:am | `503` | `RequestGameCardRegistrationGoldPoint` | 2.0.0+ | Q | 2026-11-21 |
| ns:am | `504` | `RequestRegisterGameCard` | 2.0.0+ | Q | 2026-11-21 |
| ns:am | `600` | `CountApplicationContentMeta` | 2.0.0+ | Q | 2026-11-21 |
| ns:am | `601` | `ListApplicationContentMetaStatus` | 2.0.0+ | Q | 2026-11-21 |
| ns:am | `602` | `ListAvailableAddOnContent` | 2.0.0+ | Q | 2026-11-21 |
| ns:am | `603` | `GetOwnedApplicationContentMetaStatus` | 2.0.0+ | Q | 2026-11-21 |
| ns:am | `604` | `RegisterContentsExternalKey` | 2.0.0+ | Q | 2026-11-21 |
| ns:am | `605` | `ListApplicationContentMetaStatusWithRightsCheck` | 2.0.0+ | Q | 2026-11-21 |
| ns:am | `700` | `PushDownloadTaskList` | 2.0.0+ | Q | 2026-11-21 |
| ns:am | `701` | `ClearTaskStatusList` | 2.0.0+ | Q | 2026-11-21 |
| ns:am | `702` | `RequestDownloadTaskList` | 2.0.0+ | Q | 2026-11-21 |
| ns:am | `703` | `RequestEnsureDownloadTask` | 2.0.0+ | Q | 2026-11-21 |
| ns:am | `704` | `ListDownloadTaskStatus` | 2.0.0+ | Q | 2026-11-21 |
| ns:am | `705` | `RequestDownloadTaskListData` | 2.0.0+ | Q | 2026-11-21 |
| ns:am | `800` | `RequestVersionList` | 2.0.0+ | Q | 2026-11-21 |
| ns:am | `801` | `ListVersionList` | 2.0.0+ | Q | 2026-11-21 |
| ns:am | `900` | `GetApplicationRecord` | 2.0.0+ | Q | 2026-11-21 |
| ns:am | `901` | `GetApplicationRecordProperty` | 2.0.0+ | Q | 2026-11-21 |
| ns:am | `902` | `EnableApplicationAutoUpdate` | 2.0.0+ | Q | 2026-11-21 |
| ns:am | `903` | `DisableApplicationAutoUpdate` | 2.0.0+ | Q | 2026-11-21 |
| ns:am | `904` | `TouchApplication` | 2.0.0+ | Q | 2026-11-21 |
| ns:am | `905` | `RequestApplicationUpdate` | 2.0.0+ | Q | 2026-11-21 |
| ns:am | `906` | `IsApplicationUpdateRequested` | 2.0.0+ | Q | 2026-11-21 |
| ns:am | `907` | `WithdrawApplicationUpdateRequest` | 2.0.0+ | Q | 2026-11-21 |
| ns:am | `908` | `ListApplicationRecordInstalledContentMeta` | 2.0.0+ | Q | 2026-11-21 |
| ns:am | `1000` | `RequestVerifyApplicationDeprecated` | 2.0.0+ | Q | 2026-11-21 |
| ns:am | `1001` | `CorruptApplicationForDebug` | 2.0.0+ | Q | 2026-11-21 |
| ns:am | `1200` | `NeedsUpdateVulnerability` | 2.0.0+ | Q | 2026-11-21 |
| ns:am | `1300` | `IsAnyApplicationEntityInstalled` | 2.0.0+ | Q | 2026-11-21 |
| ns:am | `1301` | `DeleteApplicationContentEntities` | 2.0.0+ | Q | 2026-11-21 |
| ns:am | `1302` | `CleanupUnrecordedApplicationEntity` | 2.0.0+ | Q | 2026-11-21 |
| ns:am | `1400` | `PrepareShutdown` | 2.0.0+ | Q | 2026-11-21 |
| ns:am | `1500` | `FormatSdCard` | 2.0.0+ | Q | 2026-11-21 |
| ns:am | `1501` | `NeedsSystemUpdateToFormatSdCard` | 2.0.0+ | Q | 2026-11-21 |
| ns:am | `1502` | `GetLastSdCardFormatUnexpectedResult` | 2.0.0+ | Q | 2026-11-21 |
| ns:am | `1600` | `GetSystemSeedForPseudoDeviceId` | 2.0.0+ | Q | 2026-11-21 |
| ns:am | `1700` | `ListApplicationDownloadingContentMeta` | 2.0.0+ | Q | 2026-11-21 |
| ns:am | `1800` | `IsNotificationSetupCompleted` | 2.0.0+ | Q | 2026-11-21 |
| ns:am | `1801` | `GetLastNotificationInfoCount` | 2.0.0+ | Q | 2026-11-21 |
| ns:am | `1802` | `ListLastNotificationInfo` | 2.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `7988` | `[GetDynamicRightsInterface](#IDynamicRightsInterface "wikilink").` | 6.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `7989` | `[GetReadOnlyApplicationControlDataInterface](#IReadOnlyApplicationControlDataInterface "wikilink").` | 5.1.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `7991` | `[GetReadOnlyApplicationRecordInterface](#IReadOnlyApplicationRecordInterface "wikilink").` | 5.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `7992` | `[GetECommerceInterface](#IECommerceInterface "wikilink")` | 4.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `7993` | `[GetApplicationVersionInterface](#IApplicationVersionInterface "wikilink")` | 4.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `7994` | `[GetFactoryResetInterface](#IFactoryResetInterface "wikilink")` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `7995` | `[GetAccountProxyInterface](#IAccountProxyInterface "wikilink")` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `7996` | `[GetApplicationManagerInterface](#IApplicationManagerInterface "wikilink")` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `7997` | `[GetDownloadTaskInterface](#IDownloadTaskInterface "wikilink")` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `7998` | `[GetContentManagementInterface](#IContentManagementInterface "wikilink")` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `7999` | `[GetDocumentInterface](#IDocumentInterface "wikilink")` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `0` | `CreateUserAccount` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `0` | `ListApplicationRecord` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `1` | `GenerateApplicationRecordCount` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `2` | `GetApplicationRecordUpdateSystemEvent` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `3` | `GetApplicationViewDeprecated` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `4` | `DeleteApplicationEntity` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `5` | `DeleteApplicationCompletely` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `6` | `IsAnyApplicationEntityRedundant` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `7` | `DeleteRedundantApplicationEntity` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `8` | `IsApplicationEntityMovable` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `9` | `MoveApplicationEntity` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `11` | `CalculateApplicationOccupiedSize` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `16` | `PushApplicationRecord` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `17` | `ListApplicationRecordContentMeta` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `19` | `LaunchApplicationOld` | 1.0.0-5.1.0 | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `21` | `GetApplicationContentPath` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `22` | `TerminateApplication` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `23` | `ResolveApplicationContentPath` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `26` | `BeginInstallApplication` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `27` | `DeleteApplicationRecord` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `30` | `RequestApplicationUpdateInfo` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `32` | `CancelApplicationDownload` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `33` | `ResumeApplicationDownload` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `35` | `UpdateVersionList` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `36` | `PushLaunchVersion` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `37` | `ListRequiredVersion` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `38` | `CheckApplicationLaunchVersion` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `39` | `CheckApplicationLaunchRights` | 1.0.0-6.2.0 | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `40` | `GetApplicationLogoData` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `41` | `CalculateApplicationDownloadRequiredSize` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `42` | `CleanupSdCard` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `43` | `CheckSdCardMountStatus` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `44` | `GetSdCardMountStatusChangedEvent` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `45` | `GetGameCardAttachmentEvent` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `46` | `GetGameCardAttachmentInfo` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `47` | `GetTotalSpaceSize` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `48` | `GetFreeSpaceSize` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `49` | `GetSdCardRemovedEvent` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `52` | `GetGameCardUpdateDetectionEvent` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `53` | `DisableApplicationAutoDelete` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `54` | `EnableApplicationAutoDelete` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `55` | `GetApplicationDesiredLanguage` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `56` | `SetApplicationTerminateResult` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `57` | `ClearApplicationTerminateResult` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `58` | `GetLastSdCardMountUnexpectedResult` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `59` | `ConvertApplicationLanguageToLanguageCode` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `60` | `ConvertLanguageCodeToApplicationLanguage` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `61` | `GetBackgroundDownloadStressTaskInfo` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `62` | `GetGameCardStopper` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `63` | `IsSystemProgramInstalled` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `64` | `StartApplyDeltaTask` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `65` | `GetRequestServerStopper` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `66` | `GetBackgroundApplyDeltaStressTaskInfo` | 3.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `67` | `CancelApplicationApplyDelta` | 3.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `68` | `ResumeApplicationApplyDelta` | 3.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `69` | `CalculateApplicationApplyDeltaRequiredSize` | 3.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `70` | `ResumeAll` | 3.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `71` | `GetStorageSize` | 3.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `80` | `RequestDownloadApplication` | 3.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `81` | `RequestDownloadAddOnContent` | 3.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `82` | `DownloadApplication` | 3.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `83` | `CheckApplicationResumeRights` | 4.0.0-6.2.0 | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `84` | `GetDynamicCommitEvent` | 4.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `85` | `RequestUpdateApplication2` | 4.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `86` | `EnableApplicationCrashReport` | 4.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `87` | `IsApplicationCrashReportEnabled` | 4.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `90` | `BoostSystemMemoryResourceLimit` | 4.0.0-8.1.0 | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `91` | `DeprecatedLaunchApplication` | 5.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `92` | `GetRunningApplicationProgramId` | 5.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `93` | `GetMainApplicationProgramIndex` | 5.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `94` | `LaunchApplication` | 6.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `95` | `GetApplicationLaunchInfo` | 6.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `96` | `AcquireApplicationLaunchInfo` | 6.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `97` | `GetMainApplicationProgramIndexByApplicationLaunchInfo` | 6.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `98` | `EnableApplicationAllThreadDumpOnCrash` | 6.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `99` | `LaunchDevMenu` | 8.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `100` | `ResetToFactorySettings` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `101` | `ResetToFactorySettingsWithoutUserSaveData` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `102` | `ResetToFactorySettingsForRefurbishment` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `200` | `CalculateUserSaveDataStatistics` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `201` | `DeleteUserSaveDataAll` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `210` | `DeleteUserSystemSaveData` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `211` | `DeleteSaveData` | 6.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `220` | `UnregisterNetworkServiceAccount` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `221` | `UnregisterNetworkServiceAccountWithUserSaveDataDeletion` | 6.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `300` | `GetApplicationShellEvent` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `301` | `PopApplicationShellEventInfo` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `302` | `LaunchLibraryApplet` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `303` | `TerminateLibraryApplet` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `304` | `LaunchSystemApplet` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `305` | `TerminateSystemApplet` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `306` | `LaunchOverlayApplet` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `307` | `TerminateOverlayApplet` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `400` | `GetApplicationControlData` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `401` | `InvalidateAllApplicationControlCache` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `402` | `RequestDownloadApplicationControlData` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `403` | `GetMaxApplicationControlCacheCount` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `404` | `InvalidateApplicationControlCache` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `405` | `ListApplicationControlCacheEntryInfo` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `406` | `GetApplicationControlProperty` | 6.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `407` | `ListApplicationTitle` | 8.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `408` | `ListApplicationIcon` | 8.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `502` | `RequestCheckGameCardRegistration` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `503` | `RequestGameCardRegistrationGoldPoint` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `504` | `RequestRegisterGameCard` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `505` | `GetGameCardMountFailureEvent` | 3.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `506` | `IsGameCardInserted` | 3.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `507` | `EnsureGameCardAccess` | 3.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `508` | `GetLastGameCardMountFailureResult` | 3.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `509` | `ListApplicationIdOnGameCard` | 5.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `510` | `GetGameCardPlatformRegion` | 9.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `600` | `CountApplicationContentMeta` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `601` | `ListApplicationContentMetaStatus` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `602` | `ListAvailableAddOnContent` | 2.0.0-5.1.0 | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `603` | `GetOwnedApplicationContentMetaStatus` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `604` | `RegisterContentsExternalKey` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `605` | `ListApplicationContentMetaStatusWithRightsCheck` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `606` | `GetContentMetaStorage` | 3.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `607` | `ListAvailableAddOnContent` | 6.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `700` | `PushDownloadTaskList` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `701` | `ClearTaskStatusList` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `702` | `RequestDownloadTaskList` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `703` | `RequestEnsureDownloadTask` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `704` | `ListDownloadTaskStatus` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `705` | `RequestDownloadTaskListData` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `800` | `RequestVersionList` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `801` | `ListVersionList` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `802` | `RequestVersionListData` | 3.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `900` | `GetApplicationRecord` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `901` | `GetApplicationRecordProperty` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `902` | `EnableApplicationAutoUpdate` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `903` | `DisableApplicationAutoUpdate` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `904` | `TouchApplication` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `905` | `RequestApplicationUpdate` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `906` | `IsApplicationUpdateRequested` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `907` | `WithdrawApplicationUpdateRequest` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `908` | `ListApplicationRecordInstalledContentMeta` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `909` | `WithdrawCleanupAddOnContentsWithNoRightsRecommendation` | 3.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `910` | `HasApplicationRecord` | 5.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `911` | `SetPreInstalledApplication` | 5.1.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `912` | `ClearPreInstalledApplicationFlag` | 5.1.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `913` | `ListAllApplicationRecord` | 9.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `914` | `HideApplicationRecord` | 9.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `915` | `ShowApplicationRecord` | 9.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `1000` | `RequestVerifyApplicationDeprecated` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `1001` | `CorruptApplicationForDebug` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `1002` | `RequestVerifyAddOnContentsRights` | 3.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `1003` | `RequestVerifyApplication` | 5.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `1004` | `CorruptContentForDebug` | 5.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `1200` | `NeedsUpdateVulnerability` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `1300` | `IsAnyApplicationEntityInstalled` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `1301` | `DeleteApplicationContentEntities` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `1302` | `CleanupUnrecordedApplicationEntity` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `1303` | `CleanupAddOnContentsWithNoRights` | 3.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `1304` | `DeleteApplicationContentEntity` | 3.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `1308` | `DeleteApplicationCompletelyForDebug` | 5.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `1309` | `CleanupUnavailableAddOnContents` | 6.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `1400` | `PrepareShutdown` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `1500` | `FormatSdCard` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `1501` | `NeedsSystemUpdateToFormatSdCard` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `1502` | `GetLastSdCardFormatUnexpectedResult` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `1504` | `InsertSdCard` | 3.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `1505` | `RemoveSdCard` | 3.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `1506` | `GetSdCardStartupStatus` | 9.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `1600` | `GetSystemSeedForPseudoDeviceId` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `1601` | `ResetSystemSeedForPseudoDeviceId` | 3.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `1700` | `ListApplicationDownloadingContentMeta` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `1701` | `GetApplicationView` | 3.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `1702` | `GetApplicationDownloadTaskStatus` | 3.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `1703` | `GetApplicationViewDownloadErrorContext` | 4.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `1704` | `GetApplicationViewWithPromotionInfo` | 8.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `1800` | `IsNotificationSetupCompleted` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `1801` | `GetLastNotificationInfoCount` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `1802` | `ListLastNotificationInfo` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `1803` | `ListNotificationTask` | 3.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `1900` | `IsActiveAccount` | 3.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `1901` | `RequestDownloadApplicationPrepurchasedRights` | 4.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `1902` | `GetApplicationTicketInfo` | 5.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `2000` | `GetSystemDeliveryInfo` | 4.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `2001` | `SelectLatestSystemDeliveryInfo` | 4.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `2002` | `VerifyDeliveryProtocolVersion` | 4.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `2003` | `GetApplicationDeliveryInfo` | 4.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `2004` | `HasAllContentsToDeliver` | 4.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `2005` | `CompareApplicationDeliveryInfo` | 4.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `2006` | `CanDeliverApplication` | 4.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `2007` | `ListContentMetaKeyToDeliverApplication` | 4.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `2008` | `NeedsSystemUpdateToDeliverApplication` | 4.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `2009` | `EstimateRequiredSize` | 4.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `2010` | `RequestReceiveApplication` | 4.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `2011` | `CommitReceiveApplication` | 4.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `2012` | `GetReceiveApplicationProgress` | 4.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `2013` | `RequestSendApplication` | 4.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `2014` | `GetSendApplicationProgress` | 4.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `2015` | `CompareSystemDeliveryInfo` | 4.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `2016` | `ListNotCommittedContentMeta` | 4.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `2017` | `RecoverDownloadTask` | 4.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `2018` | `GetApplicationDeliveryInfoHash` | 5.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `2050` | `GetApplicationRightsOnClient` | 6.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `2051` | `InvalidateRightsIdCache` | 9.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `2100` | `GetApplicationTerminateResult` | 6.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `2101` | `GetRawApplicationTerminateResult` | 6.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `2150` | `CreateRightsEnvironment` | 6.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `2151` | `DestroyRightsEnvironment` | 6.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `2152` | `ActivateRightsEnvironment` | 6.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `2153` | `DeactivateRightsEnvironment` | 6.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `2154` | `ForceActivateRightsContextForExit` | 6.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `2155` | `UpdateRightsEnvironmentStatus` | 7.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `2156` | `CreateRightsEnvironmentForPreomia` | 9.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `2160` | `AddTargetApplicationToRightsEnvironment` | 6.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `2161` | `SetUsersToRightsEnvironment` | 6.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `2170` | `GetRightsEnvironmentStatus` | 6.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `2171` | `GetRightsEnvironmentStatusChangedEvent` | 6.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `2180` | `RequestExtendExpirationInRightsEnvironment` | 6.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `2181` | `GetResultOfExtendExpirationInRightsEnvironment` | 6.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `2182` | `SetActiveRightsContextUsingStateToRightsEnvironment` | 6.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `2190` | `GetRightsEnvironmentHandleForApplication` | 6.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `2199` | `GetRightsEnvironmentCountForDebug` | 6.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `2200` | `GetGameCardApplicationCopyIdentifier` | 6.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `2201` | `GetInstalledApplicationCopyIdentifier` | 6.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `2250` | `RequestReportActiveELicence` | 6.0.0-6.2.0 | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `2300` | `ListEventLog` | 6.0.0-8.1.0 | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `2350` | `PerformAutoUpdateByApplicationId` | 7.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `2351` | `RequestNoDownloadRightsErrorResolution` | 9.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `2352` | `RequestResolveNoDownloadRightsError` | 9.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `2400` | `GetPromotionInfo` | 8.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `2401` | `CountPromotionInfo` | 8.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `2402` | `ListPromotionInfo` | 8.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `2403` | `ImportPromotionJsonForDebug` | 8.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `2404` | `ClearPromotionInfoForDebug` | 8.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `2500` | `ConfirmAvailableTime` | 8.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `2510` | `CreateApplicationResource` | 9.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `2511` | `GetApplicationResource` | 9.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `2513` | `LaunchPreomia` | 9.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `2514` | `ClearTaskOfAsyncTaskManager` | 9.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `2800` | `GetApplicationIdOfPreomia` | 9.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `0` | `GetLaunchRequiredVersion` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `1` | `UpgradeLaunchRequiredVersion` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `1000` | `PerformAutoUpdate` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `607` | `IsAnyApplicationRunning` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `706` | `TryCommitCurrentApplicationDownloadTask` | 4.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `707` | `EnableAutoCommit` | 4.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `708` | `DisableAutoCommit` | 4.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `709` | `TriggerDynamicCommitEvent` | 4.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `0` | `HasApplicationRecord` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `0` | `GetApplicationControlData` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `1` | `GetApplicationDesiredLanguage` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `2` | `ConvertApplicationLanguageToLanguageCode` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `3` | `ConvertLanguageCodeToApplicationLanguage` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `4` | `SelectApplicationDesiredLanguage` | 9.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `0` | `RequestApplicationRightsOnServer` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `1` | `RequestAssignRights` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `4` | `DeprecatedRequestAssignRightsToResume` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `5` | `VerifyActivatedRightsOwners` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `6` | `DeprecatedGetApplicationRightsStatus` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `7` | `RequestPrefetchForDynamicRights` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `8` | `GetDynamicRightsState` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `9` | `RequestApplicationRightsOnServerToResume` | 7.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `10` | `RequestAssignRightsToResume` | 7.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `11` | `GetActivatedRightsUsers` | 7.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `12` | `GetApplicationRightsStatus` | 8.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `13` | `GetRunningApplicationStatus` | 8.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `0` | `RequestLinkDevice` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `1` | `RequestCleanupAllPreInstalledApplications` | 6.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `2` | `RequestCleanupPreInstalledApplication` | 6.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `3` | `RequestSyncRights` | 6.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `4` | `RequestUnlinkDevice` | 6.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `5` | `RequestRevokeAllELicense` | 6.1.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `6` | `RequestSyncRightsBasedOnAssignedELicenses` | 9.0.0+ | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `0` | `Attach` | — | Q | 2026-11-21 |
| ns:am2, ns:ec, ns:rid, ns:rt, ns:web | `1` | `BoostSystemMemoryResourceLimit` | — | Q | 2026-11-21 |
| ns:vm | `1200` | `NeedsUpdateVulnerability` | 3.0.0+ | Q | 2026-11-21 |
| ns:vm | `1201` | `UpdateSafeSystemVersionForDebug` | 4.0.0+ | Q | 2026-11-21 |
| ns:vm | `1202` | `GetSafeSystemVersion` | 4.0.0+ | Q | 2026-11-21 |
| ns:su | `0` | `GetBackgroundNetworkUpdateState` | — | Q | 2026-11-21 |
| ns:su | `1` | `OpenSystemUpdateControl` | — | Q | 2026-11-21 |
| ns:su | `2` | `NotifyExFatDriverRequired` | — | Q | 2026-11-21 |
| ns:su | `3` | `ClearExFatDriverStatusForDebug` | — | Q | 2026-11-21 |
| ns:su | `4` | `RequestBackgroundNetworkUpdate` | — | Q | 2026-11-21 |
| ns:su | `5` | `NotifyBackgroundNetworkUpdate` | — | Q | 2026-11-21 |
| ns:su | `6` | `NotifyExFatDriverDownloadedForDebug` | — | Q | 2026-11-21 |
| ns:su | `9` | `GetSystemUpdateNotificationEventForContentDelivery` | — | Q | 2026-11-21 |
| ns:su | `10` | `NotifySystemUpdateForContentDelivery` | — | Q | 2026-11-21 |
| ns:su | `11` | `PrepareShutdown` | 3.0.0+ | Q | 2026-11-21 |
| ns:su | `16` | `DestroySystemUpdateTask` | 4.0.0+ | Q | 2026-11-21 |
| ns:su | `17` | `RequestSendSystemUpdate` | 4.0.0+ | Q | 2026-11-21 |
| ns:su | `18` | `GetSendSystemUpdateProgress` | 4.0.0+ | Q | 2026-11-21 |
| ns:su | `0` | `HasDownloaded` | — | Q | 2026-11-21 |
| ns:su | `1` | `RequestCheckLatestUpdate` | — | Q | 2026-11-21 |
| ns:su | `2` | `RequestDownloadLatestUpdate` | — | Q | 2026-11-21 |
| ns:su | `3` | `GetDownloadProgress` | — | Q | 2026-11-21 |
| ns:su | `4` | `ApplyDownloadedUpdate` | — | Q | 2026-11-21 |
| ns:su | `5` | `RequestPrepareCardUpdate` | — | Q | 2026-11-21 |
| ns:su | `6` | `GetPrepareCardUpdateProgress` | — | Q | 2026-11-21 |
| ns:su | `7` | `HasPreparedCardUpdate` | — | Q | 2026-11-21 |
| ns:su | `8` | `ApplyCardUpdate` | — | Q | 2026-11-21 |
| ns:su | `9` | `GetDownloadedEulaDataSize` | — | Q | 2026-11-21 |
| ns:su | `10` | `GetDownloadedEulaData` | — | Q | 2026-11-21 |
| ns:su | `11` | `SetupCardUpdate` | — | Q | 2026-11-21 |
| ns:su | `12` | `GetPreparedCardUpdateEulaDataSize` | — | Q | 2026-11-21 |
| ns:su | `13` | `GetPreparedCardUpdateEulaData` | — | Q | 2026-11-21 |
| ns:su | `14` | `SetupCardUpdateViaSystemUpdater` | 4.0.0+ | Q | 2026-11-21 |
| ns:su | `15` | `HasReceived` | 4.0.0+ | Q | 2026-11-21 |
| ns:su | `16` | `RequestReceiveSystemUpdate` | 4.0.0+ | Q | 2026-11-21 |
| ns:su | `17` | `GetReceiveProgress` | 4.0.0+ | Q | 2026-11-21 |
| ns:su | `18` | `ApplyReceivedUpdate` | 4.0.0+ | Q | 2026-11-21 |
| ns:su | `19` | `GetReceivedEulaDataSize` | 4.0.0+ | Q | 2026-11-21 |
| ns:su | `20` | `GetReceivedEulaData` | 4.0.0+ | Q | 2026-11-21 |
| ns:su | `21` | `SetupToReceiveSystemUpdate` | 4.0.0+ | Q | 2026-11-21 |
| ns:su | `22` | `RequestCheckLatestUpdateIncludesRebootlessUpdate` | 6.0.0+ | Q | 2026-11-21 |
| IAsyncValue | `0` | `GetSize` | — | Q | 2026-11-21 |
| IAsyncValue | `1` | `Get` | — | Q | 2026-11-21 |
| IAsyncValue | `2` | `Cancel` | — | Q | 2026-11-21 |
| IAsyncValue | `3` | `GetErrorContext` | 4.0.0+ | Q | 2026-11-21 |
| IAsyncResult | `0` | `Get` | — | Q | 2026-11-21 |
| IAsyncResult | `1` | `Cancel` | — | Q | 2026-11-21 |
| IAsyncResult | `2` | `GetErrorContext` | 4.0.0+ | Q | 2026-11-21 |
| ns:dev | `0` | `LaunchProgram` | — | Q | 2026-11-21 |
| ns:dev | `1` | `TerminateProcess` | — | Q | 2026-11-21 |
| ns:dev | `2` | `TerminateProgram` | — | Q | 2026-11-21 |
| ns:dev | `4` | `GetShellEvent` | — | Q | 2026-11-21 |
| ns:dev | `5` | `GetShellEventInfo` | — | Q | 2026-11-21 |
| ns:dev | `6` | `TerminateApplication` | — | Q | 2026-11-21 |
| ns:dev | `7` | `PrepareLaunchProgramFromHost` | — | Q | 2026-11-21 |
| ns:dev | `8` | `LaunchApplicationForDevelop` | — | Q | 2026-11-21 |
| ns:dev | `9` | `LaunchApplicationWithStorageIdForDevelop` | — | Q | 2026-11-21 |
| ns:dev | `10` | `IsSystemMemoryResourceLimitBoosted` | 6.0.0-8.1.0 | Q | 2026-11-21 |
| ns:dev | `11` | `GetRunningApplicationProcessIdForDevelop` | 6.0.0+ | Q | 2026-11-21 |
| ns:dev | `12` | `SetCurrentApplicationRightsEnvironmentCanBeActiveForDevelop` | 6.0.0+ | Q | 2026-11-21 |
| ns:dev | `13` | `CreateApplicationResourceForDevelop` | 9.0.0+ | Q | 2026-11-21 |
| ns:dev | `14` | `IsPreomiaForDevelop` | 9.0.0+ | Q | 2026-11-21 |

### PPC services   
  fgm:1, fgm:2, fgm:3, fgm:4, fgm:5, fgm:6 and fgm:7 used to exist, but are now deprecated.

[Wiki SwitchBrew](https://switchbrew.org/wiki/PPC_services___
__fgm:1,_fgm:2,_fgm:3,_fgm:4,_fgm:5,_fgm:6_and_fgm:7_used_to_exist,_but_are_now_deprecated.) · [miroir](https://github.com/backupbrew/switchbrew/blob/master/PPC%20services.md)

**22 commandes documentées** (snapshot du miroir).

| Interface / section | ID | Fonction | Disponibilité indiquée | Encore | Vérifié |
|---|---|---|---|---|---|
| apm | `0` | `OpenSession` | — | Q | 2026-11-21 |
| apm | `1` | `GetPerformanceMode` | — | Q | 2026-11-21 |
| apm | `6` | `IsCpuOverclockEnabled` | 7.0.0+ | Q | 2026-11-21 |
| apm:p | `0` | `OpenSession` | — | Q | 2026-11-21 |
| apm:sys | `0` | `RequestPerformanceMode` | — | Q | 2026-11-21 |
| apm:sys | `1` | `GetPerformanceEvent` | — | Q | 2026-11-21 |
| apm:sys | `2` | `GetThrottlingState` | — | Q | 2026-11-21 |
| apm:sys | `3` | `GetLastThrottlingState` | — | Q | 2026-11-21 |
| apm:sys | `4` | `ClearLastThrottlingState` | — | Q | 2026-11-21 |
| apm:sys | `5` | `LoadAndApplySettings` | 5.0.0+ | Q | 2026-11-21 |
| apm:sys | `6` | `SetCpuBoostMode` | 7.0.0+ | Q | 2026-11-21 |
| apm:sys | `7` | `GetCurrentPerformanceConfiguration` | 7.0.0+ | Q | 2026-11-21 |
| ISession | `0` | `SetPerformanceConfiguration` | — | Q | 2026-11-21 |
| ISession | `1` | `GetPerformanceConfiguration` | — | Q | 2026-11-21 |
| ISession | `2` | `SetCpuOverclockEnabled` | 8.0.0+ | Q | 2026-11-21 |
| fgm, fgm:0, fgm:9 | `0` | `Initialize` | — | Q | 2026-11-21 |
| fgm, fgm:0, fgm:9 | `1` | `Set` | — | Q | 2026-11-21 |
| fgm, fgm:0, fgm:9 | `2` | `Get` | — | Q | 2026-11-21 |
| fgm, fgm:0, fgm:9 | `3` | `Cancel` | — | Q | 2026-11-21 |
| fgm:dbg | `0` | `Initialize` | — | Q | 2026-11-21 |
| fgm:dbg | `1` | `Read` | — | Q | 2026-11-21 |
| fgm:dbg | `2` | `Cancel` | — | Q | 2026-11-21 |

### Glue services

[Wiki SwitchBrew](https://switchbrew.org/wiki/Glue_services) · [miroir](https://github.com/backupbrew/switchbrew/blob/master/Glue%20services.md)

**93 commandes documentées** (snapshot du miroir).

| Interface / section | ID | Fonction | Disponibilité indiquée | Encore | Vérifié |
|---|---|---|---|---|---|
| arp:r | `0` | `GetApplicationLaunchProperty` | — | Q | 2026-11-21 |
| arp:r | `1` | `GetApplicationLaunchPropertyWithApplicationId` | — | Q | 2026-11-21 |
| arp:r | `2` | `GetApplicationControlProperty` | — | Q | 2026-11-21 |
| arp:r | `3` | `GetApplicationControlPropertyWithApplicationId` | — | Q | 2026-11-21 |
| arp:w | `0` | `AcquireRegistrar` | — | Q | 2026-11-21 |
| arp:w | `1` | `DeleteProperties` | — | Q | 2026-11-21 |
| arp:w | `0` | `Issue` | — | Q | 2026-11-21 |
| arp:w | `1` | `SetApplicationLaunchProperty` | — | Q | 2026-11-21 |
| arp:w | `2` | `SetApplicationControlProperty` | — | Q | 2026-11-21 |
| bgtc:t | `1` | `NotifyTaskStarting` | — | Q | 2026-11-21 |
| bgtc:t | `2` | `NotifyTaskFinished` | — | Q | 2026-11-21 |
| bgtc:t | `3` | `GetTriggerEvent` | — | Q | 2026-11-21 |
| bgtc:t | `4` | `IsInHalfAwake` | — | Q | 2026-11-21 |
| bgtc:t | `5` | `NotifyClientName` | — | Q | 2026-11-21 |
| bgtc:t | `6` | `IsInFullAwake` | 3.0.0+ | Q | 2026-11-21 |
| bgtc:t | `11` | `ScheduleTask` | — | Q | 2026-11-21 |
| bgtc:t | `12` | `GetScheduledTaskInterval` | — | Q | 2026-11-21 |
| bgtc:t | `13` | `UnscheduleTask` | — | Q | 2026-11-21 |
| bgtc:t | `14` | `GetScheduleEvent` | — | Q | 2026-11-21 |
| bgtc:t | `15` | `SchedulePeriodicTask` | — | Q | 2026-11-21 |
| bgtc:t | `101` | `GetOperationMode` | 3.0.0+ | Q | 2026-11-21 |
| bgtc:t | `102` | `WillDisconnectNetworkWhenEnteringSleep` | 3.0.0+ | Q | 2026-11-21 |
| bgtc:t | `103` | `WillStayHalfAwakeInsteadSleep` | 3.0.0+ | Q | 2026-11-21 |
| bgtc:sc | `1` | `GetState` | — | Q | 2026-11-21 |
| bgtc:sc | `2` | `GetStateChangedEvent` | — | Q | 2026-11-21 |
| bgtc:sc | `3` | `NotifyEnteringHalfAwake` | — | Q | 2026-11-21 |
| bgtc:sc | `4` | `NotifyLeavingHalfAwake` | — | Q | 2026-11-21 |
| bgtc:sc | `5` | `SetIsUsingSleepUnsupportedDevices` | 3.0.0+ | Q | 2026-11-21 |
| time:a, time:r, time:u | `0` | `GetStandardUserSystemClock` | — | Q | 2026-11-21 |
| time:a, time:r, time:u | `1` | `GetStandardNetworkSystemClock` | — | Q | 2026-11-21 |
| time:a, time:r, time:u | `2` | `GetStandardSteadyClock` | — | Q | 2026-11-21 |
| time:a, time:r, time:u | `3` | `GetTimeZoneService` | — | Q | 2026-11-21 |
| time:a, time:r, time:u | `4` | `GetStandardLocalSystemClock` | — | Q | 2026-11-21 |
| time:a, time:r, time:u | `5` | `GetEphemeralNetworkSystemClock` | 4.0.0+ | Q | 2026-11-21 |
| time:a, time:r, time:u | `20` | `GetSharedMemoryNativeHandle` | 6.0.0+ | Q | 2026-11-21 |
| time:a, time:r, time:u | `30` | `GetStandardNetworkClockOperationEventReadableHandle` | 6.0.0-8.1.0 | Q | 2026-11-21 |
| time:a, time:r, time:u | `31` | `GetEphemeralNetworkClockOperationEventReadableHandle` | 6.0.0-8.1.0 | Q | 2026-11-21 |
| time:a, time:r, time:u | `50` | `SetStandardSteadyClockInternalOffset` | 4.0.0+ | Q | 2026-11-21 |
| time:a, time:r, time:u | `51` | `GetStandardSteadyClockRtcValue` | 9.0.0+ | Q | 2026-11-21 |
| time:a, time:r, time:u | `100` | `IsStandardUserSystemClockAutomaticCorrectionEnabled` | — | Q | 2026-11-21 |
| time:a, time:r, time:u | `101` | `SetStandardUserSystemClockAutomaticCorrectionEnabled` | — | Q | 2026-11-21 |
| time:a, time:r, time:u | `102` | `GetStandardUserSystemClockInitialYear` | 5.0.0+ | Q | 2026-11-21 |
| time:a, time:r, time:u | `200` | `IsStandardNetworkSystemClockAccuracySufficient` | 3.0.0+ | Q | 2026-11-21 |
| time:a, time:r, time:u | `201` | `GetStandardUserSystemClockAutomaticCorrectionUpdatedTime` | 6.0.0+ | Q | 2026-11-21 |
| time:a, time:r, time:u | `300` | `CalculateMonotonicSystemClockBaseTimePoint` | 4.0.0+ | Q | 2026-11-21 |
| time:a, time:r, time:u | `400` | `GetClockSnapshot` | 4.0.0+ | Q | 2026-11-21 |
| time:a, time:r, time:u | `401` | `GetClockSnapshotFromSystemClockContext` | 4.0.0+ | Q | 2026-11-21 |
| time:a, time:r, time:u | `500` | `CalculateStandardUserSystemClockDifferenceByUser` | 4.0.0+ | Q | 2026-11-21 |
| time:a, time:r, time:u | `501` | `CalculateSpanBetween` | 4.0.0+ | Q | 2026-11-21 |
| time:a, time:r, time:u | `0` | `GetCurrentTimePoint` | — | Q | 2026-11-21 |
| time:a, time:r, time:u | `2` | `GetTestOffset` | — | Q | 2026-11-21 |
| time:a, time:r, time:u | `3` | `SetTestOffset` | — | Q | 2026-11-21 |
| time:a, time:r, time:u | `100` | `GetRtcValue` | 2.0.0+ | Q | 2026-11-21 |
| time:a, time:r, time:u | `101` | `IsRtcResetDetected` | 2.0.0+ | Q | 2026-11-21 |
| time:a, time:r, time:u | `102` | `GetSetupResultValue` | 2.0.0+ | Q | 2026-11-21 |
| time:a, time:r, time:u | `200` | `GetInternalOffset` | 3.0.0+ | Q | 2026-11-21 |
| time:a, time:r, time:u | `201` | `SetInternalOffset` | 3.0.0-3.0.2 | Q | 2026-11-21 |
| time:a, time:r, time:u | `0` | `GetCurrentTime` | — | Q | 2026-11-21 |
| time:a, time:r, time:u | `1` | `SetCurrentTime` | — | Q | 2026-11-21 |
| time:a, time:r, time:u | `2` | `GetSystemClockContext` | — | Q | 2026-11-21 |
| time:a, time:r, time:u | `3` | `SetSystemClockContext` | — | Q | 2026-11-21 |
| time:a, time:r, time:u | `4` | `GetOperationEventReadableHandle` | 9.0.0+ | Q | 2026-11-21 |
| time:a, time:r, time:u | `0` | `GetDeviceLocationName` | — | Q | 2026-11-21 |
| time:a, time:r, time:u | `1` | `SetDeviceLocationName` | — | Q | 2026-11-21 |
| time:a, time:r, time:u | `2` | `GetTotalLocationNameCount` | — | Q | 2026-11-21 |
| time:a, time:r, time:u | `3` | `LoadLocationNameList` | — | Q | 2026-11-21 |
| time:a, time:r, time:u | `4` | `LoadTimeZoneRule` | — | Q | 2026-11-21 |
| time:a, time:r, time:u | `5` | `GetTimeZoneRuleVersion` | 2.0.0+ | Q | 2026-11-21 |
| time:a, time:r, time:u | `6` | `GetDeviceLocationNameAndUpdatedTime` | 5.0.0+ | Q | 2026-11-21 |
| time:a, time:r, time:u | `7` | `SetDeviceLocationNameWithTimeZoneRule` | 9.0.0+ | Q | 2026-11-21 |
| time:a, time:r, time:u | `8` | `ParseTimeZoneBinary` | 9.0.0+ | Q | 2026-11-21 |
| time:a, time:r, time:u | `20` | `GetDeviceLocationNameOperationEventReadableHandle` | 9.0.0+ | Q | 2026-11-21 |
| time:a, time:r, time:u | `100` | `ToCalendarTime` | — | Q | 2026-11-21 |
| time:a, time:r, time:u | `101` | `ToCalendarTimeWithMyRule` | — | Q | 2026-11-21 |
| time:a, time:r, time:u | `201` | `ToPosixTime` | — | Q | 2026-11-21 |
| time:a, time:r, time:u | `202` | `ToPosixTimeWithMyRule` | — | Q | 2026-11-21 |
| notif:a | `500` | `RegisterAlarmSetting` | — | Q | 2026-11-21 |
| notif:a | `510` | `UpdateAlarmSetting` | — | Q | 2026-11-21 |
| notif:a | `520` | `ListAlarmSettings` | — | Q | 2026-11-21 |
| notif:a | `530` | `LoadApplicationParameter` | — | Q | 2026-11-21 |
| notif:a | `540` | `DeleteAlarmSetting` | — | Q | 2026-11-21 |
| notif:a | `1000` | `Initialize` | — | Q | 2026-11-21 |
| notif:s | `500` | `RegisterAlarmSetting` | — | Q | 2026-11-21 |
| notif:s | `510` | `UpdateAlarmSetting` | — | Q | 2026-11-21 |
| notif:s | `520` | `ListAlarmSettings` | — | Q | 2026-11-21 |
| notif:s | `530` | `LoadApplicationParameter` | — | Q | 2026-11-21 |
| notif:s | `540` | `DeleteAlarmSetting` | — | Q | 2026-11-21 |
| notif:s | `1010` | `GetNotification` | — | Q | 2026-11-21 |
| notif:s | `1020` | `DeleteNotification` | — | Q | 2026-11-21 |
| notif:s | `1500` | `SetPresentationSetting` | — | Q | 2026-11-21 |
| notif:s | `1510` | `GetPresentationSetting` | — | Q | 2026-11-21 |
| notif:s | `2010` | `MuteAlarm` | — | Q | 2026-11-21 |
| notif:s | `2020` | `IsAlarmMuted` | — | Q | 2026-11-21 |

### Audio services

[Wiki SwitchBrew](https://switchbrew.org/wiki/Audio_services) · [miroir](https://github.com/backupbrew/switchbrew/blob/master/Audio%20services.md)

**158 commandes documentées** (snapshot du miroir).

| Interface / section | ID | Fonction | Disponibilité indiquée | Encore | Vérifié |
|---|---|---|---|---|---|
| audout:u | `0` | `ListAudioOuts` | — | Q | 2026-11-21 |
| audout:u | `1` | `OpenAudioOut` | — | Q | 2026-11-21 |
| audout:u | `2` | `ListAudioOutsAuto` | 3.0.0+ | Q | 2026-11-21 |
| audout:u | `3` | `OpenAudioOutAuto` | 3.0.0+ | Q | 2026-11-21 |
| audout:u | `0` | `GetAudioOutState` | — | Q | 2026-11-21 |
| audout:u | `1` | `StartAudioOut` | — | Q | 2026-11-21 |
| audout:u | `2` | `StopAudioOut` | — | Q | 2026-11-21 |
| audout:u | `3` | `AppendAudioOutBuffer` | — | Q | 2026-11-21 |
| audout:u | `4` | `RegisterBufferEvent` | — | Q | 2026-11-21 |
| audout:u | `5` | `GetReleasedAudioOutBuffer` | — | Q | 2026-11-21 |
| audout:u | `6` | `ContainsAudioOutBuffer` | — | Q | 2026-11-21 |
| audout:u | `7` | `AppendAudioOutBufferAuto` | 3.0.0+ | Q | 2026-11-21 |
| audout:u | `8` | `GetReleasedAudioOutBufferAuto` | 3.0.0+ | Q | 2026-11-21 |
| audout:u | `9` | `GetAudioOutBufferCount` | 4.0.0+ | Q | 2026-11-21 |
| audout:u | `10` | `GetAudioOutPlayedSampleCount` | 4.0.0+ | Q | 2026-11-21 |
| audout:u | `11` | `FlushAudioOutBuffers` | 4.0.0+ | Q | 2026-11-21 |
| audout:u | `12` | `SetAudioOutVolume` | 6.0.0+ | Q | 2026-11-21 |
| audout:u | `13` | `GetAudioOutVolume` | 6.0.0+ | Q | 2026-11-21 |
| audin:u | `0` | `ListAudioIns` | — | Q | 2026-11-21 |
| audin:u | `1` | `OpenAudioIn` | — | Q | 2026-11-21 |
| audin:u | `2` | `ListAudioInsAuto` | 3.0.0+ | Q | 2026-11-21 |
| audin:u | `3` | `OpenAudioInAuto` | 3.0.0+ | Q | 2026-11-21 |
| audin:u | `4` | `ListAudioInsAutoFiltered` | 3.0.0+ | Q | 2026-11-21 |
| audin:u | `0` | `GetAudioInState` | — | Q | 2026-11-21 |
| audin:u | `1` | `StartAudioIn` | — | Q | 2026-11-21 |
| audin:u | `2` | `StopAudioIn` | — | Q | 2026-11-21 |
| audin:u | `3` | `AppendAudioInBuffer` | — | Q | 2026-11-21 |
| audin:u | `4` | `RegisterBufferEvent` | — | Q | 2026-11-21 |
| audin:u | `5` | `GetReleasedAudioInBuffer` | — | Q | 2026-11-21 |
| audin:u | `6` | `ContainsAudioInBuffer` | — | Q | 2026-11-21 |
| audin:u | `7` | `AppendAudioInBufferWithUserEvent` | 3.0.0+ | Q | 2026-11-21 |
| audin:u | `8` | `AppendAudioInBufferAuto` | 3.0.0+ | Q | 2026-11-21 |
| audin:u | `9` | `GetReleasedAudioInBufferAuto` | 3.0.0+ | Q | 2026-11-21 |
| audin:u | `10` | `AppendAudioInBufferWithUserEventAuto` | 3.0.0+ | Q | 2026-11-21 |
| audin:u | `11` | `GetAudioInBufferCount` | 4.0.0+ | Q | 2026-11-21 |
| audin:u | `12` | `SetAudioInDeviceGain` | 4.0.0+ | Q | 2026-11-21 |
| audin:u | `13` | `GetAudioInDeviceGain` | 4.0.0+ | Q | 2026-11-21 |
| audin:u | `14` | `FlushAudioInBuffers` | 6.0.0+ | Q | 2026-11-21 |
| audrec:u | `0` | `OpenFinalOutputRecorder` | — | Q | 2026-11-21 |
| audrec:u | `0` | `GetFinalOutputRecorderState` | — | Q | 2026-11-21 |
| audrec:u | `1` | `StartFinalOutputRecorder` | — | Q | 2026-11-21 |
| audrec:u | `2` | `StopFinalOutputRecorder` | — | Q | 2026-11-21 |
| audrec:u | `3` | `AppendFinalOutputRecorderBuffer` | — | Q | 2026-11-21 |
| audrec:u | `4` | `RegisterBufferEvent` | — | Q | 2026-11-21 |
| audrec:u | `5` | `GetReleasedFinalOutputRecorderBuffer` | — | Q | 2026-11-21 |
| audrec:u | `6` | `ContainsFinalOutputRecorderBuffer` | — | Q | 2026-11-21 |
| audrec:u | `7` | `GetFinalOutputRecorderBufferEndTime` | — | Q | 2026-11-21 |
| audrec:u | `8` | `AppendFinalOutputRecorderBufferAuto` | 3.0.0+ | Q | 2026-11-21 |
| audrec:u | `9` | `GetReleasedFinalOutputRecorderBufferAuto` | 3.0.0+ | Q | 2026-11-21 |
| audrec:u | `10` | `FlushFinalOutputRecorderBuffers` | 6.0.0+ | Q | 2026-11-21 |
| audren:u | `0` | `OpenAudioRenderer` | — | Q | 2026-11-21 |
| audren:u | `1` | `GetWorkBufferSize` | — | Q | 2026-11-21 |
| audren:u | `2` | `GetAudioDeviceService` | — | Q | 2026-11-21 |
| audren:u | `3` | `OpenAudioRendererForManualExecution` | 3.0.0+ | Q | 2026-11-21 |
| audren:u | `4` | `GetAudioDeviceServiceWithRevisionInfo` | 4.0.0+ | Q | 2026-11-21 |
| audren:u | `0` | `GetSampleRate` | — | Q | 2026-11-21 |
| audren:u | `1` | `GetSampleCount` | — | Q | 2026-11-21 |
| audren:u | `2` | `GetMixBufferCount` | — | Q | 2026-11-21 |
| audren:u | `3` | `GetState` | — | Q | 2026-11-21 |
| audren:u | `4` | `RequestUpdate` | — | Q | 2026-11-21 |
| audren:u | `5` | `Start` | — | Q | 2026-11-21 |
| audren:u | `6` | `Stop` | — | Q | 2026-11-21 |
| audren:u | `7` | `QuerySystemEvent` | — | Q | 2026-11-21 |
| audren:u | `8` | `SetRenderingTimeLimit` | — | Q | 2026-11-21 |
| audren:u | `9` | `GetRenderingTimeLimit` | — | Q | 2026-11-21 |
| audren:u | `10` | `RequestUpdateAuto` | 3.0.0+ | Q | 2026-11-21 |
| audren:u | `11` | `ExecuteAudioRendererRendering` | 3.0.0+ | Q | 2026-11-21 |
| audren:u | `0` | `ListAudioDeviceName` | — | Q | 2026-11-21 |
| audren:u | `1` | `SetAudioDeviceOutputVolume` | — | Q | 2026-11-21 |
| audren:u | `2` | `GetAudioDeviceOutputVolume` | — | Q | 2026-11-21 |
| audren:u | `3` | `GetActiveAudioDeviceName` | — | Q | 2026-11-21 |
| audren:u | `4` | `QueryAudioDeviceSystemEvent` | — | Q | 2026-11-21 |
| audren:u | `5` | `GetActiveChannelCount` | — | Q | 2026-11-21 |
| audren:u | `6` | `ListAudioDeviceNameAuto` | 3.0.0+ | Q | 2026-11-21 |
| audren:u | `7` | `SetAudioDeviceOutputVolumeAuto` | 3.0.0+ | Q | 2026-11-21 |
| audren:u | `8` | `GetAudioDeviceOutputVolumeAuto` | 3.0.0+ | Q | 2026-11-21 |
| audren:u | `10` | `GetActiveAudioDeviceNameAuto` | 3.0.0+ | Q | 2026-11-21 |
| audren:u | `11` | `QueryAudioDeviceInputEvent` | 3.0.0+ | Q | 2026-11-21 |
| audren:u | `12` | `QueryAudioDeviceOutputEvent` | 3.0.0+ | Q | 2026-11-21 |
| audren:u | `13` | `GetAudioSystemMasterVolumeSetting` | 5.0.0+ | Q | 2026-11-21 |
| audout:a | `0` | `RequestSuspendAudioOuts` | — | Q | 2026-11-21 |
| audout:a | `1` | `RequestResumeAudioOuts` | — | Q | 2026-11-21 |
| audout:a | `2` | `GetAudioOutsProcessMasterVolume` | — | Q | 2026-11-21 |
| audout:a | `3` | `SetAudioOutsProcessMasterVolume` | — | Q | 2026-11-21 |
| audout:a | `4` | `GetAudioOutsProcessRecordVolume` | 4.0.0+ | Q | 2026-11-21 |
| audout:a | `5` | `SetAudioOutsProcessRecordVolume` | 4.0.0+ | Q | 2026-11-21 |
| audin:a | `0` | `RequestSuspendAudioIns` | — | Q | 2026-11-21 |
| audin:a | `1` | `RequestResumeAudioIns` | — | Q | 2026-11-21 |
| audin:a | `2` | `GetAudioInsProcessMasterVolume` | — | Q | 2026-11-21 |
| audin:a | `3` | `SetAudioInsProcessMasterVolume` | — | Q | 2026-11-21 |
| audrec:a | `0` | `RequestSuspendFinalOutputRecorders` | — | Q | 2026-11-21 |
| audrec:a | `1` | `RequestResumeFinalOutputRecorders` | — | Q | 2026-11-21 |
| audren:a | `0` | `RequestSuspendAudioRenderers` | — | Q | 2026-11-21 |
| audren:a | `1` | `RequestResumeAudioRenderers` | — | Q | 2026-11-21 |
| audren:a | `2` | `GetAudioRenderersProcessMasterVolume` | — | Q | 2026-11-21 |
| audren:a | `3` | `SetAudioRenderersProcessMasterVolume` | — | Q | 2026-11-21 |
| audren:a | `4` | `RegisterAppletResourceUserId` | — | Q | 2026-11-21 |
| audren:a | `5` | `UnregisterAppletResourceUserId` | — | Q | 2026-11-21 |
| audren:a | `6` | `GetAudioRenderersProcessRecordVolume` | 4.0.0+ | Q | 2026-11-21 |
| audren:a | `7` | `SetAudioRenderersProcessRecordVolume` | 4.0.0+ | Q | 2026-11-21 |
| audout:d, audin:d, audrec:d, audren:d | `0` | `RequestSuspendForDebug` | — | Q | 2026-11-21 |
| audout:d, audin:d, audrec:d, audren:d | `1` | `RequestResumeForDebug` | — | Q | 2026-11-21 |
| audctl | `0` | `GetTargetVolume` | — | Q | 2026-11-21 |
| audctl | `1` | `SetTargetVolume` | — | Q | 2026-11-21 |
| audctl | `2` | `GetTargetVolumeMin` | — | Q | 2026-11-21 |
| audctl | `3` | `GetTargetVolumeMax` | — | Q | 2026-11-21 |
| audctl | `4` | `IsTargetMute` | — | Q | 2026-11-21 |
| audctl | `5` | `SetTargetMute` | — | Q | 2026-11-21 |
| audctl | `6` | `IsTargetConnected` | — | Q | 2026-11-21 |
| audctl | `7` | `SetDefaultTarget` | — | Q | 2026-11-21 |
| audctl | `8` | `GetDefaultTarget` | — | Q | 2026-11-21 |
| audctl | `9` | `GetAudioOutputMode` | — | Q | 2026-11-21 |
| audctl | `10` | `SetAudioOutputMode` | — | Q | 2026-11-21 |
| audctl | `11` | `SetForceMutePolicy` | — | Q | 2026-11-21 |
| audctl | `12` | `GetForceMutePolicy` | — | Q | 2026-11-21 |
| audctl | `13` | `GetOutputModeSetting` | — | Q | 2026-11-21 |
| audctl | `14` | `SetOutputModeSetting` | — | Q | 2026-11-21 |
| audctl | `15` | `SetOutputTarget` | — | Q | 2026-11-21 |
| audctl | `16` | `SetInputTargetForceEnabled` | — | Q | 2026-11-21 |
| audctl | `17` | `SetHeadphoneOutputLevelMode` | 3.0.0+ | Q | 2026-11-21 |
| audctl | `18` | `GetHeadphoneOutputLevelMode` | 3.0.0+ | Q | 2026-11-21 |
| audctl | `19` | `AcquireAudioVolumeUpdateEventForPlayReport` | 3.0.0+ | Q | 2026-11-21 |
| audctl | `20` | `AcquireAudioOutputDeviceUpdateEventForPlayReport` | 3.0.0+ | Q | 2026-11-21 |
| audctl | `21` | `GetAudioOutputTargetForPlayReport` | 3.0.0+ | Q | 2026-11-21 |
| audctl | `22` | `NotifyHeadphoneVolumeWarningDisplayedEvent` | 3.0.0+ | Q | 2026-11-21 |
| audctl | `23` | `SetSystemOutputMasterVolume` | 4.0.0+ | Q | 2026-11-21 |
| audctl | `24` | `GetSystemOutputMasterVolume` | 4.0.0+ | Q | 2026-11-21 |
| audctl | `25` | `GetAudioVolumeDataForPlayReport` | 4.0.0+ | Q | 2026-11-21 |
| audctl | `26` | `UpdateHeadphoneSettings` | 4.0.0+ | Q | 2026-11-21 |
| codecctl | `0` | `InitializeCodecController` | — | Q | 2026-11-21 |
| codecctl | `1` | `FinalizeCodecController` | — | Q | 2026-11-21 |
| codecctl | `2` | `SleepCodecController` | — | Q | 2026-11-21 |
| codecctl | `3` | `WakeCodecController` | — | Q | 2026-11-21 |
| codecctl | `4` | `SetCodecVolume` | — | Q | 2026-11-21 |
| codecctl | `5` | `GetCodecVolumeMax` | — | Q | 2026-11-21 |
| codecctl | `6` | `GetCodecVolumeMin` | — | Q | 2026-11-21 |
| codecctl | `7` | `SetCodecActiveTarget` | — | Q | 2026-11-21 |
| codecctl | `8` | `GetCodecActiveTarget` | — | Q | 2026-11-21 |
| codecctl | `9` | `BindCodecHeadphoneMicJackInterrupt` | — | Q | 2026-11-21 |
| codecctl | `10` | `IsCodecHeadphoneMicJackInserted` | — | Q | 2026-11-21 |
| codecctl | `11` | `ClearCodecHeadphoneMicJackInterrupt` | — | Q | 2026-11-21 |
| codecctl | `12` | `IsCodecDeviceRequested` | — | Q | 2026-11-21 |
| hwopus | `0` | `Initialize` | — | Q | 2026-11-21 |
| hwopus | `1` | `GetWorkBufferSize` | — | Q | 2026-11-21 |
| hwopus | `2` | `OpenHardwareOpusDecoderForMultiStream` | 3.0.0+ | Q | 2026-11-21 |
| hwopus | `3` | `GetWorkBufferSizeForMultiStream` | 3.0.0+ | Q | 2026-11-21 |
| hwopus | `0` | `DecodeInterleavedOld ([1.0.0-3.0.2] DecodeInterleaved)` | 4.0.0+ | Q | 2026-11-21 |
| hwopus | `1` | `SetContext` | — | Q | 2026-11-21 |
| hwopus | `2` | `DecodeInterleavedForMultiStreamOld ([3.0.0-3.0.2] DecodeInterleavedForMultiStream)` | 4.0.0+ | Q | 2026-11-21 |
| hwopus | `3` | `SetContextForMultiStream` | 3.0.0+ | Q | 2026-11-21 |
| hwopus | `4` | `DecodeInterleavedWithPerfOld ([4.0.0-5.1.0] DecodeInterleavedWithPerf)` | 6.0.0+ | Q | 2026-11-21 |
| hwopus | `5` | `DecodeInterleavedForMultiStreamWithPerfOld ([4.0.0-5.1.0] DecodeInterleavedForMultiStreamWithPerf)` | 6.0.0+ | Q | 2026-11-21 |
| hwopus | `6` | `DecodeInterleaved` | 6.0.0+ | Q | 2026-11-21 |
| hwopus | `7` | `DecodeInterleavedForMultiStream` | 6.0.0+ | Q | 2026-11-21 |
| auddebug | `0` | `StartDspProfiler` | — | Q | 2026-11-21 |
| auddebug | `1` | `StopDspProfiler` | — | Q | 2026-11-21 |
| auddebug | `2` | `StartCpuProfiler` | — | Q | 2026-11-21 |
| auddebug | `3` | `StopCpuProfiler` | — | Q | 2026-11-21 |

### Profiler services   
  Not currently available on retail units.

[Wiki SwitchBrew](https://switchbrew.org/wiki/Profiler_services___
__Not_currently_available_on_retail_units.) · [miroir](https://github.com/backupbrew/switchbrew/blob/master/Profiler%20services.md)

**3 commandes documentées** (snapshot du miroir).

| Interface / section | ID | Fonction | Disponibilité indiquée | Encore | Vérifié |
|---|---|---|---|---|---|
| banana | `0` | `GetSystemEvent` | — | Q | 2026-11-21 |
| banana | `1` | `StartSignalingEvent` | — | Q | 2026-11-21 |
| banana | `2` | `StopSignalingEvent` | — | Q | 2026-11-21 |

<!-- NS1_IPC_APPEND -->
