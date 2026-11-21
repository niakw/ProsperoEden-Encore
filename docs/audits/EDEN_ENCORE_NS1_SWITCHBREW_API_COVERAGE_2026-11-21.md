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

### BCAT services

[Wiki SwitchBrew](https://switchbrew.org/wiki/BCAT_services) · [miroir](https://github.com/backupbrew/switchbrew/blob/master/BCAT%20services.md)

**83 commandes documentées**.

| Interface / section | ID | Fonction | Disponibilité indiquée | Encore | Vérifié |
|---|---|---|---|---|---|
| bcat:a, bcat:m, bcat:u, bcat:s | `0` | `CreateBcatService` | — | Q | 2026-11-21 |
| bcat:a, bcat:m, bcat:u, bcat:s | `1` | `CreateDeliveryCacheStorageService` | — | Q | 2026-11-21 |
| bcat:a, bcat:m, bcat:u, bcat:s | `2` | `CreateDeliveryCacheStorageServiceWithApplicationId` | — | Q | 2026-11-21 |
| bcat:a, bcat:m, bcat:u, bcat:s | `10100` | `RequestSyncDeliveryCache` | — | Q | 2026-11-21 |
| bcat:a, bcat:m, bcat:u, bcat:s | `10101` | `RequestSyncDeliveryCacheWithDirectoryName` | 5.0.0+ | Q | 2026-11-21 |
| bcat:a, bcat:m, bcat:u, bcat:s | `10200` | `CancelSyncDeliveryCacheRequest` | 5.0.0+ | Q | 2026-11-21 |
| bcat:a, bcat:m, bcat:u, bcat:s | `20100` | `RequestSyncDeliveryCacheWithApplicationId` | — | Q | 2026-11-21 |
| bcat:a, bcat:m, bcat:u, bcat:s | `20101` | `RequestSyncDeliveryCacheWithApplicationIdAndDirectoryName` | 5.0.0+ | Q | 2026-11-21 |
| bcat:a, bcat:m, bcat:u, bcat:s | `20300` | `GetDeliveryCacheStorageUpdateNotifier` | 8.0.0+ | Q | 2026-11-21 |
| bcat:a, bcat:m, bcat:u, bcat:s | `20301` | `RequestSuspendDeliveryTask` | 8.0.0+ | Q | 2026-11-21 |
| bcat:a, bcat:m, bcat:u, bcat:s | `20400` | `RegisterSystemApplicationDeliveryTask` | 9.0.0+ | Q | 2026-11-21 |
| bcat:a, bcat:m, bcat:u, bcat:s | `20401` | `UnregisterSystemApplicationDeliveryTask` | 9.0.0+ | Q | 2026-11-21 |
| bcat:a, bcat:m, bcat:u, bcat:s | `30100` | `SetPassphrase` | — | Q | 2026-11-21 |
| bcat:a, bcat:m, bcat:u, bcat:s | `30200` | `RegisterDeliveryTask` | 3.0.0+ | Q | 2026-11-21 |
| bcat:a, bcat:m, bcat:u, bcat:s | `30201` | `UnregisterDeliveryTask` | 3.0.0+ | Q | 2026-11-21 |
| bcat:a, bcat:m, bcat:u, bcat:s | `30202` | `BlockDeliveryTask` | 3.0.0+ | Q | 2026-11-21 |
| bcat:a, bcat:m, bcat:u, bcat:s | `30203` | `UnblockDeliveryTask` | 3.0.0+ | Q | 2026-11-21 |
| bcat:a, bcat:m, bcat:u, bcat:s | `30300` | `RegisterSystemApplicationDeliveryTasks` | 8.0.0+ | Q | 2026-11-21 |
| bcat:a, bcat:m, bcat:u, bcat:s | `90100` | `GetDeliveryTaskList` | — | Q | 2026-11-21 |
| bcat:a, bcat:m, bcat:u, bcat:s | `90200` | `GetDeliveryList` | — | Q | 2026-11-21 |
| bcat:a, bcat:m, bcat:u, bcat:s | `90201` | `ClearDeliveryCacheStorage` | 3.0.0+ | Q | 2026-11-21 |
| bcat:a, bcat:m, bcat:u, bcat:s | `90202` | `ClearDeliveryTaskSubscriptionStatus` | 8.0.0+ | Q | 2026-11-21 |
| bcat:a, bcat:m, bcat:u, bcat:s | `90300` | `GetPushNotificationLog` | 3.0.0+ | Q | 2026-11-21 |
| bcat:a, bcat:m, bcat:u, bcat:s | `0` | `GetEvent` | — | Q | 2026-11-21 |
| bcat:a, bcat:m, bcat:u, bcat:s | `1` | `GetImpl` | — | Q | 2026-11-21 |
| bcat:a, bcat:m, bcat:u, bcat:s | `0` | `CreateFileService` | — | Q | 2026-11-21 |
| bcat:a, bcat:m, bcat:u, bcat:s | `1` | `CreateDirectoryService` | — | Q | 2026-11-21 |
| bcat:a, bcat:m, bcat:u, bcat:s | `10` | `EnumerateDeliveryCacheDirectory` | — | Q | 2026-11-21 |
| bcat:a, bcat:m, bcat:u, bcat:s | `0` | `Open` | — | Q | 2026-11-21 |
| bcat:a, bcat:m, bcat:u, bcat:s | `1` | `Read` | — | Q | 2026-11-21 |
| bcat:a, bcat:m, bcat:u, bcat:s | `2` | `GetSize` | — | Q | 2026-11-21 |
| bcat:a, bcat:m, bcat:u, bcat:s | `3` | `GetDigest` | — | Q | 2026-11-21 |
| bcat:a, bcat:m, bcat:u, bcat:s | `2` | `GetCount` | — | Q | 2026-11-21 |
| news:a, news:c, news:m, news:p, news:v | `0` | `CreateNewsService` | — | Q | 2026-11-21 |
| news:a, news:c, news:m, news:p, news:v | `1` | `CreateNewlyArrivedEventHolder` | — | Q | 2026-11-21 |
| news:a, news:c, news:m, news:p, news:v | `2` | `CreateNewsDataService` | — | Q | 2026-11-21 |
| news:a, news:c, news:m, news:p, news:v | `3` | `CreateNewsDatabaseService` | — | Q | 2026-11-21 |
| news:a, news:c, news:m, news:p, news:v | `4` | `CreateOverwriteEventHolder` | — | Q | 2026-11-21 |
| news:a, news:c, news:m, news:p, news:v | `10100` | `PostLocalNews` | — | Q | 2026-11-21 |
| news:a, news:c, news:m, news:p, news:v | `20100` | `SetPassphrase` | — | Q | 2026-11-21 |
| news:a, news:c, news:m, news:p, news:v | `30100` | `GetSubscriptionStatus` | — | Q | 2026-11-21 |
| news:a, news:c, news:m, news:p, news:v | `30101` | `GetTopicList` | 3.0.0+ | Q | 2026-11-21 |
| news:a, news:c, news:m, news:p, news:v | `30200` | `IsSystemUpdateRequired` | — | Q | 2026-11-21 |
| news:a, news:c, news:m, news:p, news:v | `30300` | `RequestImmediateReception` | — | Q | 2026-11-21 |
| news:a, news:c, news:m, news:p, news:v | `30400` | `DecodeArchiveFile` | 3.0.0+ | Q | 2026-11-21 |
| news:a, news:c, news:m, news:p, news:v | `30500` | `? (Takes a total of 8-bytes of input, a handle, and a type-0x9 input buffer, returns an IUnknown2)` | 8.0.0+ | Q | 2026-11-21 |
| news:a, news:c, news:m, news:p, news:v | `40100` | `SetSubscriptionStatus` | — | Q | 2026-11-21 |
| news:a, news:c, news:m, news:p, news:v | `40101` | `RequestAutoSubscription` | 3.0.0+ | Q | 2026-11-21 |
| news:a, news:c, news:m, news:p, news:v | `40200` | `ClearStorage` | — | Q | 2026-11-21 |
| news:a, news:c, news:m, news:p, news:v | `40201` | `ClearSubscriptionStatusAll` | — | Q | 2026-11-21 |
| news:a, news:c, news:m, news:p, news:v | `90100` | `GetNewsDatabaseDump` | — | Q | 2026-11-21 |
| news:a, news:c, news:m, news:p, news:v | `0` | `Get` | — | Q | 2026-11-21 |
| news:a, news:c, news:m, news:p, news:v | `0` | `Open` | — | Q | 2026-11-21 |
| news:a, news:c, news:m, news:p, news:v | `1` | `OpenWithNewsRecordV1` | — | Q | 2026-11-21 |
| news:a, news:c, news:m, news:p, news:v | `2` | `Read` | — | Q | 2026-11-21 |
| news:a, news:c, news:m, news:p, news:v | `3` | `GetSize` | — | Q | 2026-11-21 |
| news:a, news:c, news:m, news:p, news:v | `1001` | `OpenWithNewsRecord` | 6.0.0+ | Q | 2026-11-21 |
| news:a, news:c, news:m, news:p, news:v | `0` | `GetListV1` | — | Q | 2026-11-21 |
| news:a, news:c, news:m, news:p, news:v | `1` | `Count` | — | Q | 2026-11-21 |
| news:a, news:c, news:m, news:p, news:v | `2` | `CountWithKey` | — | Q | 2026-11-21 |
| news:a, news:c, news:m, news:p, news:v | `3` | `UpdateIntegerValue` | — | Q | 2026-11-21 |
| news:a, news:c, news:m, news:p, news:v | `4` | `UpdateIntegerValueWithAddition` | — | Q | 2026-11-21 |
| news:a, news:c, news:m, news:p, news:v | `5` | `UpdateStringValue` | — | Q | 2026-11-21 |
| news:a, news:c, news:m, news:p, news:v | `1000` | `GetList` | 6.0.0+ | Q | 2026-11-21 |
| prepo:a, prepo:a2, prepo:m, prepo:u, prepo:s | `10100` | `SaveReportOld ([1.0.0-5.1.0] SaveReport)` | — | Q | 2026-11-21 |
| prepo:a, prepo:a2, prepo:m, prepo:u, prepo:s | `10101` | `SaveReportWithUserOld ([1.0.0-5.1.0] SaveReportWithUser)` | — | Q | 2026-11-21 |
| prepo:a, prepo:a2, prepo:m, prepo:u, prepo:s | `10102` | `SaveReport` | 6.0.0+ | Q | 2026-11-21 |
| prepo:a, prepo:a2, prepo:m, prepo:u, prepo:s | `10103` | `SaveReportWithUser` | 6.0.0+ | Q | 2026-11-21 |
| prepo:a, prepo:a2, prepo:m, prepo:u, prepo:s | `10200` | `RequestImmediateTransmission` | — | Q | 2026-11-21 |
| prepo:a, prepo:a2, prepo:m, prepo:u, prepo:s | `10300` | `GetTransmissionStatus` | — | Q | 2026-11-21 |
| prepo:a, prepo:a2, prepo:m, prepo:u, prepo:s | `10400` | `GetSystemSessionId` | 9.0.0+ | Q | 2026-11-21 |
| prepo:a, prepo:a2, prepo:m, prepo:u, prepo:s | `20100` | `SaveSystemReport` | — | Q | 2026-11-21 |
| prepo:a, prepo:a2, prepo:m, prepo:u, prepo:s | `20101` | `SaveSystemReportWithUser` | — | Q | 2026-11-21 |
| prepo:a, prepo:a2, prepo:m, prepo:u, prepo:s | `20200` | `SetOperationMode` | 4.0.0+ | Q | 2026-11-21 |
| prepo:a, prepo:a2, prepo:m, prepo:u, prepo:s | `30100` | `ClearStorage` | — | Q | 2026-11-21 |
| prepo:a, prepo:a2, prepo:m, prepo:u, prepo:s | `30200` | `ClearStatistics` | 6.0.0+ | Q | 2026-11-21 |
| prepo:a, prepo:a2, prepo:m, prepo:u, prepo:s | `30300` | `GetStorageUsage` | 6.0.0+ | Q | 2026-11-21 |
| prepo:a, prepo:a2, prepo:m, prepo:u, prepo:s | `30400` | `GetStatistics` | 6.0.0+ | Q | 2026-11-21 |
| prepo:a, prepo:a2, prepo:m, prepo:u, prepo:s | `30401` | `GetThroughputHistory` | 6.0.0+ | Q | 2026-11-21 |
| prepo:a, prepo:a2, prepo:m, prepo:u, prepo:s | `30500` | `GetLastUploadError` | 6.0.0+ | Q | 2026-11-21 |
| prepo:a, prepo:a2, prepo:m, prepo:u, prepo:s | `40100` | `IsUserAgreementCheckEnabled` | 2.0.0+ | Q | 2026-11-21 |
| prepo:a, prepo:a2, prepo:m, prepo:u, prepo:s | `40101` | `SetUserAgreementCheckEnabled` | 2.0.0+ | Q | 2026-11-21 |
| prepo:a, prepo:a2, prepo:m, prepo:u, prepo:s | `90100` | `ReadAllReportFiles ([1.0.0-5.1.0] GetStorageUsage)` | 6.0.0+ | Q | 2026-11-21 |

### PCV services

[Wiki SwitchBrew](https://switchbrew.org/wiki/PCV_services) · [miroir](https://github.com/backupbrew/switchbrew/blob/master/PCV%20services.md)

**101 commandes documentées**.

| Interface / section | ID | Fonction | Disponibilité indiquée | Encore | Vérifié |
|---|---|---|---|---|---|
| bpc | `0` | `ShutdownSystem` | — | Q | 2026-11-21 |
| bpc | `1` | `RebootSystem` | — | Q | 2026-11-21 |
| bpc | `2` | `GetWakeupReason` | — | Q | 2026-11-21 |
| bpc | `3` | `GetShutdownReason` | — | Q | 2026-11-21 |
| bpc | `4` | `GetAcOk` | — | Q | 2026-11-21 |
| bpc | `5` | `GetBoardPowerControlEvent` | — | Q | 2026-11-21 |
| bpc | `6` | `GetSleepButtonState` | 2.0.0+ | Q | 2026-11-21 |
| bpc | `7` | `GetPowerEvent` | 2.0.0+ | Q | 2026-11-21 |
| bpc | `8` | `CreateWakeupTimer` | 2.0.0+ | Q | 2026-11-21 |
| bpc | `9` | `CancelWakeupTimer` | 2.0.0+ | Q | 2026-11-21 |
| bpc | `10` | `EnableWakeupTimerOnDevice` | 2.0.0+ | Q | 2026-11-21 |
| bpc | `11` | `CreateWakeupTimerEx` | 3.0.0+ | Q | 2026-11-21 |
| bpc | `12` | `GetLastEnabledWakeupTimerType` | 3.0.0+ | Q | 2026-11-21 |
| bpc | `13` | `CleanAllWakeupTimers` | 3.0.0+ | Q | 2026-11-21 |
| bpc:r | `0` | `GetRtcTime` | — | Q | 2026-11-21 |
| bpc:r | `1` | `SetRtcTime` | — | Q | 2026-11-21 |
| bpc:r | `2` | `GetRtcResetDetected` | — | Q | 2026-11-21 |
| bpc:r | `3` | `ClearRtcResetDetected` | 2.0.0+ | Q | 2026-11-21 |
| bpc:r | `4` | `SetUpRtcResetOnShutdown` | 3.0.0+ | Q | 2026-11-21 |
| pcv | `26` | `GetFuseInfo` | 3.0.0+ | Q | 2026-11-21 |
| pcv | `27` | `GetDramId` | 5.0.0+ | Q | 2026-11-21 |
| pcv:arb | `0` | `ReleaseControl` | — | Q | 2026-11-21 |
| pcv:imm | `0` | `SetClockRate` | — | Q | 2026-11-21 |
| clkrst, clkrst:i | `0` | `OpenSession` | — | Q | 2026-11-21 |
| clkrst, clkrst:i | `1` | `GetTemperatureThresholds` | — | Q | 2026-11-21 |
| clkrst, clkrst:i | `2` | `SetTemperature` | — | Q | 2026-11-21 |
| clkrst, clkrst:i | `3` | `GetPossibleClockRates` | — | Q | 2026-11-21 |
| clkrst, clkrst:i | `4` | `GetClockInfoEvent` | — | Q | 2026-11-21 |
| clkrst, clkrst:i | `5` | `GetClockModuleNumLimit` | — | Q | 2026-11-21 |
| clkrst, clkrst:i | `0` | `SetClockEnabled` | — | Q | 2026-11-21 |
| clkrst, clkrst:i | `1` | `SetClockDisabled` | — | Q | 2026-11-21 |
| clkrst, clkrst:i | `2` | `SetResetAsserted` | — | Q | 2026-11-21 |
| clkrst, clkrst:i | `3` | `SetResetDeasserted` | — | Q | 2026-11-21 |
| clkrst, clkrst:i | `4` | `SetPowerEnabled` | — | Q | 2026-11-21 |
| clkrst, clkrst:i | `5` | `SetPowerDisabled` | — | Q | 2026-11-21 |
| clkrst, clkrst:i | `6` | `GetState` | — | Q | 2026-11-21 |
| clkrst, clkrst:i | `7` | `SetClockRate` | — | Q | 2026-11-21 |
| clkrst, clkrst:i | `8` | `GetClockRate` | — | Q | 2026-11-21 |
| clkrst, clkrst:i | `9` | `SetMinVClockRate` | — | Q | 2026-11-21 |
| clkrst, clkrst:i | `10` | `GetPossibleClockRates` | — | Q | 2026-11-21 |
| clkrst, clkrst:i | `11` | `GetDvfsTable` | — | Q | 2026-11-21 |
| clkrst:a | `0` | `ReleaseControl` | — | Q | 2026-11-21 |
| rgltr | `0` | `OpenSession` | — | Q | 2026-11-21 |
| rgltr | `1` | `GetPowerDomainStateTable` | — | Q | 2026-11-21 |
| rgltr | `2` | `GetPowerInfoEvent` | — | Q | 2026-11-21 |
| rgltr | `3` | `GetPowerModuleNumLimit` | — | Q | 2026-11-21 |
| rgltr | `0` | `SetVoltageEnabled` | — | Q | 2026-11-21 |
| rgltr | `2` | `GetVoltageEnabled` | — | Q | 2026-11-21 |
| rgltr | `3` | `GetVoltageRange` | — | Q | 2026-11-21 |
| rgltr | `4` | `GetVoltageValue` | — | Q | 2026-11-21 |
| rgltr | `5` | `SetVoltageValue` | — | Q | 2026-11-21 |
| rgltr | `6` | `ChangeVoltage` | — | Q | 2026-11-21 |
| rtc | `0` | `GetRtcTime` | — | Q | 2026-11-21 |
| rtc | `1` | `SetRtcTime` | — | Q | 2026-11-21 |
| rtc | `2` | `SetRtcClientUnknownBool` | — | Q | 2026-11-21 |
| rtc | `3` | `GetRtcResetDetected` | — | Q | 2026-11-21 |
| rtc | `4` | `ClearRtcResetDetected` | — | Q | 2026-11-21 |
| time:u, time:a, time:s | `0` | `GetStandardUserSystemClock` | — | Q | 2026-11-21 |
| time:u, time:a, time:s | `1` | `GetStandardNetworkSystemClock` | — | Q | 2026-11-21 |
| time:u, time:a, time:s | `2` | `GetStandardSteadyClock` | — | Q | 2026-11-21 |
| time:u, time:a, time:s | `3` | `GetTimeZoneService` | — | Q | 2026-11-21 |
| time:u, time:a, time:s | `4` | `GetStandardLocalSystemClock` | — | Q | 2026-11-21 |
| time:u, time:a, time:s | `5` | `GetEphemeralNetworkSystemClock` | 4.0.0+ | Q | 2026-11-21 |
| time:u, time:a, time:s | `20` | `GetSharedMemoryNativeHandle` | 6.0.0+ | Q | 2026-11-21 |
| time:u, time:a, time:s | `30` | `GetStandardNetworkClockOperationEventReadableHandle` | 6.0.0+ | Q | 2026-11-21 |
| time:u, time:a, time:s | `31` | `GetEphemeralNetworkClockOperationEventReadableHandle` | 6.0.0+ | Q | 2026-11-21 |
| time:u, time:a, time:s | `50` | `SetStandardSteadyClockInternalOffset` | 4.0.0+ | Q | 2026-11-21 |
| time:u, time:a, time:s | `100` | `IsStandardUserSystemClockAutomaticCorrectionEnabled` | — | Q | 2026-11-21 |
| time:u, time:a, time:s | `101` | `SetStandardUserSystemClockAutomaticCorrectionEnabled` | — | Q | 2026-11-21 |
| time:u, time:a, time:s | `102` | `GetStandardUserSystemClockInitialYear` | 5.0.0+ | Q | 2026-11-21 |
| time:u, time:a, time:s | `200` | `IsStandardNetworkSystemClockAccuracySufficient` | 3.0.0+ | Q | 2026-11-21 |
| time:u, time:a, time:s | `201` | `GetStandardUserSystemClockAutomaticCorrectionUpdatedTime` | 6.0.0+ | Q | 2026-11-21 |
| time:u, time:a, time:s | `300` | `CalculateMonotonicSystemClockBaseTimePoint` | 4.0.0+ | Q | 2026-11-21 |
| time:u, time:a, time:s | `400` | `GetClockSnapshot` | 4.0.0+ | Q | 2026-11-21 |
| time:u, time:a, time:s | `401` | `GetClockSnapshotFromSystemClockContext` | 4.0.0+ | Q | 2026-11-21 |
| time:u, time:a, time:s | `500` | `CalculateStandardUserSystemClockDifferenceByUser` | 4.0.0+ | Q | 2026-11-21 |
| time:u, time:a, time:s | `501` | `CalculateSpanBetween` | 4.0.0+ | Q | 2026-11-21 |
| time:u, time:a, time:s | `0` | `GetCurrentTimePoint` | — | Q | 2026-11-21 |
| time:u, time:a, time:s | `2` | `GetTestOffset` | — | Q | 2026-11-21 |
| time:u, time:a, time:s | `3` | `SetTestOffset` | — | Q | 2026-11-21 |
| time:u, time:a, time:s | `100` | `GetRtcValue` | 2.0.0+ | Q | 2026-11-21 |
| time:u, time:a, time:s | `101` | `IsRtcResetDetected` | 2.0.0+ | Q | 2026-11-21 |
| time:u, time:a, time:s | `102` | `GetSetupResultValue` | 2.0.0+ | Q | 2026-11-21 |
| time:u, time:a, time:s | `200` | `GetInternalOffset` | 3.0.0+ | Q | 2026-11-21 |
| time:u, time:a, time:s | `201` | `SetInternalOffset` | 3.0.0-3.0.2 | Q | 2026-11-21 |
| time:u, time:a, time:s | `0` | `GetCurrentTime` | — | Q | 2026-11-21 |
| time:u, time:a, time:s | `1` | `SetCurrentTime` | — | Q | 2026-11-21 |
| time:u, time:a, time:s | `2` | `GetSystemClockContext` | — | Q | 2026-11-21 |
| time:u, time:a, time:s | `3` | `SetSystemClockContext` | — | Q | 2026-11-21 |
| time:u, time:a, time:s | `4` | `GetOperationEventReadableHandle` | 9.0.0+ | Q | 2026-11-21 |
| time:u, time:a, time:s | `0` | `GetDeviceLocationName` | — | Q | 2026-11-21 |
| time:u, time:a, time:s | `1` | `SetDeviceLocationName` | — | Q | 2026-11-21 |
| time:u, time:a, time:s | `2` | `GetTotalLocationNameCount` | — | Q | 2026-11-21 |
| time:u, time:a, time:s | `3` | `LoadLocationNameList` | — | Q | 2026-11-21 |
| time:u, time:a, time:s | `4` | `LoadTimeZoneRule` | — | Q | 2026-11-21 |
| time:u, time:a, time:s | `5` | `GetTimeZoneRuleVersion` | 2.0.0+ | Q | 2026-11-21 |
| time:u, time:a, time:s | `6` | `GetDeviceLocationNameAndUpdatedTime` | 5.0.0+ | Q | 2026-11-21 |
| time:u, time:a, time:s | `100` | `ToCalendarTime` | — | Q | 2026-11-21 |
| time:u, time:a, time:s | `101` | `ToCalendarTimeWithMyRule` | — | Q | 2026-11-21 |
| time:u, time:a, time:s | `201` | `ToPosixTime` | — | Q | 2026-11-21 |
| time:u, time:a, time:s | `202` | `ToPosixTimeWithMyRule` | — | Q | 2026-11-21 |

### Sockets services

[Wiki SwitchBrew](https://switchbrew.org/wiki/Sockets_services) · [miroir](https://github.com/backupbrew/switchbrew/blob/master/Sockets%20services.md)

**94 commandes documentées**.

| Interface / section | ID | Fonction | Disponibilité indiquée | Encore | Vérifié |
|---|---|---|---|---|---|
| bsd:u, bsd:s | `0` | `RegisterClient (Initialize)` | — | Q | 2026-11-21 |
| bsd:u, bsd:s | `1` | `StartMonitoring` | — | Q | 2026-11-21 |
| bsd:u, bsd:s | `2` | `Socket` | — | Q | 2026-11-21 |
| bsd:u, bsd:s | `3` | `SocketExempt` | — | Q | 2026-11-21 |
| bsd:u, bsd:s | `4` | `Open` | — | Q | 2026-11-21 |
| bsd:u, bsd:s | `5` | `Select` | — | Q | 2026-11-21 |
| bsd:u, bsd:s | `6` | `Poll` | — | Q | 2026-11-21 |
| bsd:u, bsd:s | `7` | `Sysctl` | — | Q | 2026-11-21 |
| bsd:u, bsd:s | `8` | `Recv` | — | Q | 2026-11-21 |
| bsd:u, bsd:s | `9` | `RecvFrom` | — | Q | 2026-11-21 |
| bsd:u, bsd:s | `10` | `Send` | — | Q | 2026-11-21 |
| bsd:u, bsd:s | `11` | `SendTo` | — | Q | 2026-11-21 |
| bsd:u, bsd:s | `12` | `Accept` | — | Q | 2026-11-21 |
| bsd:u, bsd:s | `13` | `Bind` | — | Q | 2026-11-21 |
| bsd:u, bsd:s | `14` | `Connect` | — | Q | 2026-11-21 |
| bsd:u, bsd:s | `15` | `GetPeerName` | — | Q | 2026-11-21 |
| bsd:u, bsd:s | `16` | `GetSockName` | — | Q | 2026-11-21 |
| bsd:u, bsd:s | `17` | `GetSockOpt` | — | Q | 2026-11-21 |
| bsd:u, bsd:s | `18` | `Listen` | — | Q | 2026-11-21 |
| bsd:u, bsd:s | `19` | `Ioctl` | — | Q | 2026-11-21 |
| bsd:u, bsd:s | `20` | `Fcntl` | — | Q | 2026-11-21 |
| bsd:u, bsd:s | `21` | `SetSockOpt` | — | Q | 2026-11-21 |
| bsd:u, bsd:s | `22` | `Shutdown` | — | Q | 2026-11-21 |
| bsd:u, bsd:s | `23` | `ShutdownAllSockets` | — | Q | 2026-11-21 |
| bsd:u, bsd:s | `24` | `Write` | — | Q | 2026-11-21 |
| bsd:u, bsd:s | `25` | `Read` | — | Q | 2026-11-21 |
| bsd:u, bsd:s | `26` | `Close` | — | Q | 2026-11-21 |
| bsd:u, bsd:s | `27` | `DuplicateSocket` | — | Q | 2026-11-21 |
| bsd:u, bsd:s | `28` | `GetResourceStatistics` | — | Q | 2026-11-21 |
| bsd:u, bsd:s | `29` | `RecvMMsg` | 3.0.0+ | Q | 2026-11-21 |
| bsd:u, bsd:s | `30` | `SendMMsg` | 3.0.0+ | Q | 2026-11-21 |
| bsd:u, bsd:s | `31` | `EventFd` | 7.0.0+ | Q | 2026-11-21 |
| bsd:u, bsd:s | `32` | `RegisterResourceStatisticsName` | 7.0.0+ | Q | 2026-11-21 |
| bsdcfg | `0` | `SetIfUp` | — | Q | 2026-11-21 |
| bsdcfg | `1` | `SetIfUpWithEvent` | — | Q | 2026-11-21 |
| bsdcfg | `2` | `CancelIf` | — | Q | 2026-11-21 |
| bsdcfg | `3` | `SetIfDown` | — | Q | 2026-11-21 |
| bsdcfg | `4` | `GetIfState` | — | Q | 2026-11-21 |
| bsdcfg | `5` | `DhcpRenew` | — | Q | 2026-11-21 |
| bsdcfg | `6` | `AddStaticArpEntry` | — | Q | 2026-11-21 |
| bsdcfg | `7` | `RemoveArpEntry` | — | Q | 2026-11-21 |
| bsdcfg | `8` | `LookupArpEntry` | — | Q | 2026-11-21 |
| bsdcfg | `9` | `LookupArpEntry2` | — | Q | 2026-11-21 |
| bsdcfg | `10` | `ClearArpEntries` | — | Q | 2026-11-21 |
| bsdcfg | `11` | `ClearArpEntries2` | — | Q | 2026-11-21 |
| bsdcfg | `12` | `PrintArpEntries` | — | Q | 2026-11-21 |
| ethc:c | `0` | `Initialize` | — | Q | 2026-11-21 |
| ethc:c | `1` | `Cancel` | — | Q | 2026-11-21 |
| ethc:c | `2` | `GetResult` | — | Q | 2026-11-21 |
| ethc:c | `3` | `GetMediaList` | — | Q | 2026-11-21 |
| ethc:c | `4` | `SetMediaType` | — | Q | 2026-11-21 |
| ethc:c | `5` | `GetMediaType` | — | Q | 2026-11-21 |
| ethc:i | `0` | `GetReadableHandle` | — | Q | 2026-11-21 |
| ethc:i | `1` | `Cancel` | — | Q | 2026-11-21 |
| ethc:i | `2` | `GetResult` | — | Q | 2026-11-21 |
| ethc:i | `3` | `GetInterfaceList` | — | Q | 2026-11-21 |
| ethc:i | `4` | `GetInterfaceCount` | — | Q | 2026-11-21 |
| sfdnsres | `0` | `SetDnsAddressesPrivateRequest (stubbed, returns 0x7FE03)` | — | Q | 2026-11-21 |
| sfdnsres | `1` | `GetDnsAddressPrivateRequest (stubbed, returns 0x7FE03)` | — | Q | 2026-11-21 |
| sfdnsres | `2` | `GetHostByNameRequest` | — | Q | 2026-11-21 |
| sfdnsres | `3` | `GetHostByAddrRequest` | — | Q | 2026-11-21 |
| sfdnsres | `4` | `GetHostStringErrorRequest` | — | Q | 2026-11-21 |
| sfdnsres | `5` | `GetGaiStringErrorRequest` | — | Q | 2026-11-21 |
| sfdnsres | `6` | `GetAddrInfoRequest` | — | Q | 2026-11-21 |
| sfdnsres | `7` | `GetNameInfoRequest` | — | Q | 2026-11-21 |
| sfdnsres | `8` | `GetCancelHandleRequest` | — | Q | 2026-11-21 |
| sfdnsres | `9` | `CancelRequest` | — | Q | 2026-11-21 |
| sfdnsres | `10` | `GetHostByNameRequestWithOptions` | 5.0.0+ | Q | 2026-11-21 |
| sfdnsres | `11` | `GetHostByAddrRequestWithOptions` | 5.0.0+ | Q | 2026-11-21 |
| sfdnsres | `12` | `GetAddrInfoRequestWithOptions` | 5.0.0+ | Q | 2026-11-21 |
| sfdnsres | `13` | `GetNameInfoRequestWithOptions` | 5.0.0+ | Q | 2026-11-21 |
| sfdnsres | `14` | `ResolverSetOptionRequest` | 5.0.0+ | Q | 2026-11-21 |
| sfdnsres | `15` | `ResolverGetOptionRequest` | 5.0.0+ | Q | 2026-11-21 |
| nsd:u, nsd:a | `10` | `GetSettingName` | — | Q | 2026-11-21 |
| nsd:u, nsd:a | `11` | `GetEnvironmentIdentifier` | — | Q | 2026-11-21 |
| nsd:u, nsd:a | `12` | `GetDeviceId` | — | Q | 2026-11-21 |
| nsd:u, nsd:a | `13` | `DeleteSettings` | — | Q | 2026-11-21 |
| nsd:u, nsd:a | `14` | `ImportSettings` | — | Q | 2026-11-21 |
| nsd:u, nsd:a | `15` | `SetChangeEnvironmentIdentifierDisabled` | 4.0.0+ | Q | 2026-11-21 |
| nsd:u, nsd:a | `20` | `Resolve` | — | Q | 2026-11-21 |
| nsd:u, nsd:a | `21` | `ResolveEx` | — | Q | 2026-11-21 |
| nsd:u, nsd:a | `30` | `GetNasServiceSetting` | — | Q | 2026-11-21 |
| nsd:u, nsd:a | `31` | `GetNasServiceSettingEx` | — | Q | 2026-11-21 |
| nsd:u, nsd:a | `40` | `GetNasRequestFqdn` | — | Q | 2026-11-21 |
| nsd:u, nsd:a | `41` | `GetNasRequestFqdnEx` | — | Q | 2026-11-21 |
| nsd:u, nsd:a | `42` | `GetNasApiFqdn` | — | Q | 2026-11-21 |
| nsd:u, nsd:a | `43` | `GetNasApiFqdnEx` | — | Q | 2026-11-21 |
| nsd:u, nsd:a | `50` | `GetCurrentSetting` | — | Q | 2026-11-21 |
| nsd:u, nsd:a | `51` | `WriteTestParameter` | 9.0.0+ | Q | 2026-11-21 |
| nsd:u, nsd:a | `52` | `ReadTestParameter` | 9.0.0+ | Q | 2026-11-21 |
| nsd:u, nsd:a | `60` | `ReadSaveDataFromFsForTest` | — | Q | 2026-11-21 |
| nsd:u, nsd:a | `61` | `WriteSaveDataToFsForTest` | — | Q | 2026-11-21 |
| nsd:u, nsd:a | `62` | `DeleteSaveDataOfFsForTest` | — | Q | 2026-11-21 |
| nsd:u, nsd:a | `63` | `IsChangeEnvironmentIdentifierDisabled` | 4.0.0+ | Q | 2026-11-21 |

### Bluetooth Driver services

[Wiki SwitchBrew](https://switchbrew.org/wiki/Bluetooth_Driver_services) · [miroir](https://github.com/backupbrew/switchbrew/blob/master/Bluetooth%20Driver%20services.md)

**89 commandes documentées**.

| Interface / section | ID | Fonction | Disponibilité indiquée | Encore | Vérifié |
|---|---|---|---|---|---|
| btdrv | `0` | `InitializeBluetoothDriver` | — | Q | 2026-11-21 |
| btdrv | `1` | `InitializeBluetooth` | — | Q | 2026-11-21 |
| btdrv | `2` | `EnableBluetooth` | — | Q | 2026-11-21 |
| btdrv | `3` | `DisableBluetooth` | — | Q | 2026-11-21 |
| btdrv | `4` | `CleanupBluetooth` | — | Q | 2026-11-21 |
| btdrv | `5` | `GetAdapterProperties` | — | Q | 2026-11-21 |
| btdrv | `6` | `GetAdapterProperty` | — | Q | 2026-11-21 |
| btdrv | `7` | `SetAdapterProperty` | — | Q | 2026-11-21 |
| btdrv | `8` | `StartDiscovery` | — | Q | 2026-11-21 |
| btdrv | `9` | `CancelDiscovery` | — | Q | 2026-11-21 |
| btdrv | `10` | `CreateBond` | — | Q | 2026-11-21 |
| btdrv | `11` | `RemoveBond` | — | Q | 2026-11-21 |
| btdrv | `12` | `CancelBond` | — | Q | 2026-11-21 |
| btdrv | `13` | `PinReply` | — | Q | 2026-11-21 |
| btdrv | `14` | `SspReply` | — | Q | 2026-11-21 |
| btdrv | `15` | `GetEventInfo` | — | Q | 2026-11-21 |
| btdrv | `16` | `InitializeHid` | — | Q | 2026-11-21 |
| btdrv | `17` | `HidConnect` | — | Q | 2026-11-21 |
| btdrv | `18` | `HidDisconnect` | — | Q | 2026-11-21 |
| btdrv | `19` | `HidSendData` | — | Q | 2026-11-21 |
| btdrv | `20` | `HidSendData2` | — | Q | 2026-11-21 |
| btdrv | `21` | `HidSetReport` | — | Q | 2026-11-21 |
| btdrv | `22` | `HidGetReport` | — | Q | 2026-11-21 |
| btdrv | `23` | `HidWakeController` | — | Q | 2026-11-21 |
| btdrv | `24` | `HidAddPairedDevice` | — | Q | 2026-11-21 |
| btdrv | `25` | `HidGetPairedDevice` | — | Q | 2026-11-21 |
| btdrv | `26` | `CleanupHid` | — | Q | 2026-11-21 |
| btdrv | `27` | `HidGetEventInfo` | — | Q | 2026-11-21 |
| btdrv | `28` | `ExtSetTsi` | — | Q | 2026-11-21 |
| btdrv | `29` | `ExtSetBurstMode` | — | Q | 2026-11-21 |
| btdrv | `30` | `ExtSetZeroRetran` | — | Q | 2026-11-21 |
| btdrv | `31` | `ExtSetMcMode` | — | Q | 2026-11-21 |
| btdrv | `32` | `ExtStartLlrMode` | — | Q | 2026-11-21 |
| btdrv | `33` | `ExtExitLlrMode` | — | Q | 2026-11-21 |
| btdrv | `34` | `ExtSetRadio` | — | Q | 2026-11-21 |
| btdrv | `35` | `ExtSetVisibility` | — | Q | 2026-11-21 |
| btdrv | `36` | `ExtSetTbfcScan` | — | Q | 2026-11-21 |
| btdrv | `37` | `RegisterHidReportEvent` | — | Q | 2026-11-21 |
| btdrv | `38` | `HidGetReportEventInfo` | — | Q | 2026-11-21 |
| btdrv | `39` | `GetLatestPlr` | — | Q | 2026-11-21 |
| btdrv | `40` | `ExtGetPendingConnections` | 3.0.0+ | Q | 2026-11-21 |
| btdrv | `41` | `GetChannelMap` | 3.0.0+ | Q | 2026-11-21 |
| btdrv | `42` | `EnableBluetoothBoostSetting` | 3.0.0+ | Q | 2026-11-21 |
| btdrv | `43` | `IsBluetoothBoostSettingEnabled` | 3.0.0+ | Q | 2026-11-21 |
| btdrv | `44` | `EnableBluetoothAfhSetting` | 3.0.0+ | Q | 2026-11-21 |
| btdrv | `45` | `IsBluetoothAfhSettingEnabled` | — | Q | 2026-11-21 |
| btdrv | `46` | `InitializeBluetoothLe` | 5.0.0+ | Q | 2026-11-21 |
| btdrv | `47` | `EnableBluetoothLe` | 5.0.0+ | Q | 2026-11-21 |
| btdrv | `48` | `DisableBluetoothLe` | 5.0.0+ | Q | 2026-11-21 |
| btdrv | `49` | `CleanupBluetoothLe` | 5.0.0+ | Q | 2026-11-21 |
| btdrv | `50` | `SetLeVisibility` | 5.0.0+ | Q | 2026-11-21 |
| btdrv | `51` | `SetLeConnectionParameter` | 5.0.0+ | Q | 2026-11-21 |
| btdrv | `52` | `SetLeDefaultConnectionParameter` | 5.0.0+ | Q | 2026-11-21 |
| btdrv | `53` | `SetLeAdvertiseData` | 5.0.0+ | Q | 2026-11-21 |
| btdrv | `54` | `SetLeAdvertiseParameter` | 5.0.0+ | Q | 2026-11-21 |
| btdrv | `55` | `StartLeScan` | 5.0.0+ | Q | 2026-11-21 |
| btdrv | `56` | `StopLeScan` | 5.0.0+ | Q | 2026-11-21 |
| btdrv | `57` | `AddLeScanFilterCondition` | 5.0.0+ | Q | 2026-11-21 |
| btdrv | `58` | `DeleteLeScanFilterCondition` | 5.0.0+ | Q | 2026-11-21 |
| btdrv | `59` | `DeleteLeScanFilter` | 5.0.0+ | Q | 2026-11-21 |
| btdrv | `60` | `ClearLeScanFilters` | 5.0.0+ | Q | 2026-11-21 |
| btdrv | `61` | `EnableLeScanFilter` | 5.0.0+ | Q | 2026-11-21 |
| btdrv | `62` | `RegisterLeClient` | 5.0.0+ | Q | 2026-11-21 |
| btdrv | `63` | `UnregisterLeClient` | 5.0.0+ | Q | 2026-11-21 |
| btdrv | `64` | `UnregisterLeClientAll` | 5.0.0+ | Q | 2026-11-21 |
| btdrv | `65` | `LeClientConnect` | 5.0.0+ | Q | 2026-11-21 |
| btdrv | `75` | `CreateLeService` | 5.0.0+ | Q | 2026-11-21 |
| btdrv | `77` | `AddLeCharacteristic` | 5.0.0+ | Q | 2026-11-21 |
| btdrv | `84` | `RegisterLeCoreDataPath` | 5.0.0+ | Q | 2026-11-21 |
| btdrv | `85` | `UnregisterLeCoreDataPath` | 5.0.0+ | Q | 2026-11-21 |
| btdrv | `86` | `RegisterLeHidDataPath` | 5.0.0+ | Q | 2026-11-21 |
| btdrv | `87` | `UnregisterLeHidDataPath` | 5.0.0+ | Q | 2026-11-21 |
| btdrv | `88` | `RegisterLeDataPath` | 5.0.0+ | Q | 2026-11-21 |
| btdrv | `94` | `LeClientRegisterNotification` | 5.0.0+ | Q | 2026-11-21 |
| btdrv | `97` | `RegisterBleHidEvent` | 5.0.0-5.0.2 | Q | 2026-11-21 |
| btdrv | `98` | `SetLeScanParameter` | 5.1.0+ | Q | 2026-11-21 |
| btdrv | `256` | `GetIsManufacturingMode` | 5.0.0+ | Q | 2026-11-21 |
| btdrv | `257` | `EmulateBluetoothCrash` | 7.0.0+ | Q | 2026-11-21 |
| btdrv | `258` | `GetBleChannelMap` | 9.0.0+ | Q | 2026-11-21 |
| bt | `0` | `LeClientReadCharacteristic` | — | Q | 2026-11-21 |
| bt | `1` | `LeClientReadDescriptor` | — | Q | 2026-11-21 |
| bt | `2` | `LeClientWriteCharacteristic` | — | Q | 2026-11-21 |
| bt | `3` | `LeClientWriteDescriptor` | — | Q | 2026-11-21 |
| bt | `4` | `LeClientRegisterNotification` | — | Q | 2026-11-21 |
| bt | `5` | `LeClientDeregisterNotification` | — | Q | 2026-11-21 |
| bt | `6` | `SetLeResponse` | — | Q | 2026-11-21 |
| bt | `7` | `LeSendIndication` | — | Q | 2026-11-21 |
| bt | `8` | `GetLeEventInfo` | — | Q | 2026-11-21 |
| bt | `9` | `RegisterBleEvent` | — | Q | 2026-11-21 |

### BTM services

[Wiki SwitchBrew](https://switchbrew.org/wiki/BTM_services) · [miroir](https://github.com/backupbrew/switchbrew/blob/master/BTM%20services.md)

**117 commandes documentées**.

| Interface / section | ID | Fonction | Disponibilité indiquée | Encore | Vérifié |
|---|---|---|---|---|---|
| btm | `0` | `GetState` | — | Q | 2026-11-21 |
| btm | `1` | `GetHostDeviceProperty` | — | Q | 2026-11-21 |
| btm | `2` | `AcquireDeviceConditionEvent` | — | Q | 2026-11-21 |
| btm | `3` | `GetDeviceCondition` | — | Q | 2026-11-21 |
| btm | `4` | `SetBurstMode` | — | Q | 2026-11-21 |
| btm | `5` | `SetSlotMode` | — | Q | 2026-11-21 |
| btm | `6` | `SetBluetoothMode` | 1.0.0-8.1.0 | Q | 2026-11-21 |
| btm | `7` | `SetWlanMode` | — | Q | 2026-11-21 |
| btm | `8` | `AcquireDeviceInfoEvent` | — | Q | 2026-11-21 |
| btm | `9` | `GetDeviceInfo` | — | Q | 2026-11-21 |
| btm | `10` | `AddDeviceInfo` | — | Q | 2026-11-21 |
| btm | `11` | `RemoveDeviceInfo` | — | Q | 2026-11-21 |
| btm | `12` | `IncreaseDeviceInfoOrder` | — | Q | 2026-11-21 |
| btm | `13` | `LlrNotify` | — | Q | 2026-11-21 |
| btm | `14` | `EnableRadio` | — | Q | 2026-11-21 |
| btm | `15` | `DisableRadio` | — | Q | 2026-11-21 |
| btm | `16` | `HidDisconnect` | — | Q | 2026-11-21 |
| btm | `17` | `HidSetRetransmissionMode` | — | Q | 2026-11-21 |
| btm | `18` | `AcquireAwakeReqEvent` | 2.0.0+ | Q | 2026-11-21 |
| btm | `19` | `AcquireLlrStateEvent` | 4.0.0+ | Q | 2026-11-21 |
| btm | `20` | `IsLlrStarted` | 4.0.0+ | Q | 2026-11-21 |
| btm | `21` | `EnableSlotSaving` | 4.0.0+ | Q | 2026-11-21 |
| btm | `22` | `ProtectDeviceInfo` | 5.0.0+ | Q | 2026-11-21 |
| btm | `23` | `AcquireBleScanEvent` | 5.0.0+ | Q | 2026-11-21 |
| btm | `24` | `GetBleScanParameterGeneral` | 5.0.0+ | Q | 2026-11-21 |
| btm | `25` | `GetBleScanParameterSmartDevice` | 5.0.0+ | Q | 2026-11-21 |
| btm | `26` | `StartBleScanForGeneral` | 5.0.0+ | Q | 2026-11-21 |
| btm | `27` | `StopBleScanForGeneral` | 5.0.0+ | Q | 2026-11-21 |
| btm | `28` | `GetBleScanResultsForGeneral` | 5.0.0+ | Q | 2026-11-21 |
| btm | `29` | `StartBleScanForPairedDevice` | 5.0.0+ | Q | 2026-11-21 |
| btm | `30` | `StopBleScanForPairedDevice` | 5.0.0+ | Q | 2026-11-21 |
| btm | `31` | `StartBleScanForSmartDevice` | 5.0.0+ | Q | 2026-11-21 |
| btm | `32` | `StopBleScanForSmartDevice` | 5.0.0+ | Q | 2026-11-21 |
| btm | `33` | `GetBleScanResultsForSmartDevice` | 5.0.0+ | Q | 2026-11-21 |
| btm | `34` | `AcquireBleConnectionEvent` | 5.0.0+ | Q | 2026-11-21 |
| btm | `35` | `BleConnect` | 5.0.0+ | Q | 2026-11-21 |
| btm | `36` | `BleOverrideConnection` | 5.0.0+ | Q | 2026-11-21 |
| btm | `37` | `BleDisconnect` | 5.0.0+ | Q | 2026-11-21 |
| btm | `38` | `BleGetConnectionState` | 5.0.0+ | Q | 2026-11-21 |
| btm | `39` | `BleGetGattClientConditionList` | 5.0.0+ | Q | 2026-11-21 |
| btm | `40` | `AcquireBlePairingEvent` | 5.0.0+ | Q | 2026-11-21 |
| btm | `41` | `BlePairDevice` | 5.0.0+ | Q | 2026-11-21 |
| btm | `42` | `BleUnpairDeviceOnBoth` | 5.0.0+ | Q | 2026-11-21 |
| btm | `43` | `BleUnpairDevice` | 5.1.0+ | Q | 2026-11-21 |
| btm | `44` | `BleGetPairedAddresses` | 5.1.0+ | Q | 2026-11-21 |
| btm | `45` | `AcquireBleServiceDiscoveryEvent` | 5.1.0+ | Q | 2026-11-21 |
| btm | `46` | `GetGattServices` | 5.1.0+ | Q | 2026-11-21 |
| btm | `47` | `GetGattService` | 5.1.0+ | Q | 2026-11-21 |
| btm | `48` | `GetGattIncludedServices` | 5.1.0+ | Q | 2026-11-21 |
| btm | `49` | `GetBelongingService` | 5.1.0+ | Q | 2026-11-21 |
| btm | `50` | `GetGattCharacteristics` | 5.1.0+ | Q | 2026-11-21 |
| btm | `51` | `GetGattDescriptors` | 5.1.0+ | Q | 2026-11-21 |
| btm | `52` | `AcquireBleMtuConfigEvent` | 5.1.0+ | Q | 2026-11-21 |
| btm | `53` | `ConfigureBleMtu` | 5.1.0+ | Q | 2026-11-21 |
| btm | `54` | `GetBleMtu` | 5.1.0+ | Q | 2026-11-21 |
| btm | `55` | `RegisterBleGattDataPath` | 5.1.0+ | Q | 2026-11-21 |
| btm | `56` | `UnregisterBleGattDataPath` | 5.1.0+ | Q | 2026-11-21 |
| btm | `57` | `RegisterAppletResourceUserId` | 5.1.0+ | Q | 2026-11-21 |
| btm | `58` | `UnregisterAppletResourceUserId` | 5.1.0+ | Q | 2026-11-21 |
| btm | `59` | `SetAppletResourceUserId` | 5.1.0+ | Q | 2026-11-21 |
| btm:dbg | `0` | `AcquireDiscoveryEvent` | — | Q | 2026-11-21 |
| btm:dbg | `1` | `StartDiscovery` | — | Q | 2026-11-21 |
| btm:dbg | `2` | `CancelDiscovery` | — | Q | 2026-11-21 |
| btm:dbg | `3` | `GetDeviceProperty` | — | Q | 2026-11-21 |
| btm:dbg | `4` | `CreateBond` | — | Q | 2026-11-21 |
| btm:dbg | `5` | `CancelBond` | — | Q | 2026-11-21 |
| btm:dbg | `6` | `SetTsiMode` | — | Q | 2026-11-21 |
| btm:dbg | `7` | `GeneralTest` | — | Q | 2026-11-21 |
| btm:dbg | `8` | `HidConnect` | — | Q | 2026-11-21 |
| btm:dbg | `9` | `GeneralGet` | 5.0.0+ | Q | 2026-11-21 |
| btm:dbg | `10` | `GetGattClientDisconnectionReason` | 5.1.0+ | Q | 2026-11-21 |
| btm:dbg | `11` | `GetBleConnectionParameter` | 5.1.0+ | Q | 2026-11-21 |
| btm:dbg | `12` | `GetBleConnectionParameterRequest` | 5.1.0+ | Q | 2026-11-21 |
| btm:sys | `0` | `GetCore` | — | Q | 2026-11-21 |
| btm:sys | `0` | `StartGamepadPairing` | — | Q | 2026-11-21 |
| btm:sys | `1` | `CancelGamepadPairing` | — | Q | 2026-11-21 |
| btm:sys | `2` | `ClearGamepadPairingDatabase` | — | Q | 2026-11-21 |
| btm:sys | `3` | `GetPairedGamepadCount` | — | Q | 2026-11-21 |
| btm:sys | `4` | `EnableRadio` | — | Q | 2026-11-21 |
| btm:sys | `5` | `DisableRadio` | — | Q | 2026-11-21 |
| btm:sys | `6` | `GetRadioOnOff` | — | Q | 2026-11-21 |
| btm:sys | `7` | `AcquireRadioEvent` | 3.0.0+ | Q | 2026-11-21 |
| btm:sys | `8` | `AcquireGamepadPairingEvent` | 3.0.0+ | Q | 2026-11-21 |
| btm:sys | `9` | `IsGamepadPairingStarted` | 3.0.0+ | Q | 2026-11-21 |
| btm:u | `0` | `GetCore` | — | Q | 2026-11-21 |
| btm:u | `0` | `AcquireBleScanEvent` | — | Q | 2026-11-21 |
| btm:u | `1` | `GetBleScanFilterParameter` | — | Q | 2026-11-21 |
| btm:u | `2` | `GetBleScanFilterParameter2` | — | Q | 2026-11-21 |
| btm:u | `3` | `StartBleScanForGeneral` | — | Q | 2026-11-21 |
| btm:u | `4` | `StopBleScanForGeneral` | — | Q | 2026-11-21 |
| btm:u | `5` | `GetBleScanResultsForGeneral` | — | Q | 2026-11-21 |
| btm:u | `6` | `StartBleScanForPaired` | — | Q | 2026-11-21 |
| btm:u | `7` | `StopBleScanForPaired` | — | Q | 2026-11-21 |
| btm:u | `8` | `StartBleScanForSmartDevice` | — | Q | 2026-11-21 |
| btm:u | `9` | `StopBleScanForSmartDevice` | — | Q | 2026-11-21 |
| btm:u | `10` | `GetBleScanResultsForSmartDevice` | — | Q | 2026-11-21 |
| btm:u | `17` | `AcquireBleConnectionEvent` | — | Q | 2026-11-21 |
| btm:u | `18` | `BleConnect` | — | Q | 2026-11-21 |
| btm:u | `19` | `BleDisconnect` | — | Q | 2026-11-21 |
| btm:u | `20` | `BleGetConnectionState` | — | Q | 2026-11-21 |
| btm:u | `21` | `AcquireBlePairingEvent` | — | Q | 2026-11-21 |
| btm:u | `22` | `BlePairDevice` | — | Q | 2026-11-21 |
| btm:u | `23` | `BleUnPairDevice` | — | Q | 2026-11-21 |
| btm:u | `24` | `BleUnPairDevice2` | — | Q | 2026-11-21 |
| btm:u | `25` | `BleGetPairedDevices` | — | Q | 2026-11-21 |
| btm:u | `26` | `AcquireBleServiceDiscoveryEvent` | — | Q | 2026-11-21 |
| btm:u | `27` | `GetGattServices` | — | Q | 2026-11-21 |
| btm:u | `28` | `GetGattService` | — | Q | 2026-11-21 |
| btm:u | `29` | `GetGattIncludedServices` | — | Q | 2026-11-21 |
| btm:u | `30` | `GetBelongingGattService` | — | Q | 2026-11-21 |
| btm:u | `31` | `GetGattCharacteristics` | — | Q | 2026-11-21 |
| btm:u | `32` | `GetGattDescriptors` | — | Q | 2026-11-21 |
| btm:u | `33` | `AcquireBleMtuConfigEvent` | — | Q | 2026-11-21 |
| btm:u | `34` | `ConfigureBleMtu` | — | Q | 2026-11-21 |
| btm:u | `35` | `GetBleMtu` | — | Q | 2026-11-21 |
| btm:u | `36` | `RegisterBleGattDataPath` | — | Q | 2026-11-21 |
| btm:u | `37` | `UnregisterBleGattDataPath` | — | Q | 2026-11-21 |

### Capture services

[Wiki SwitchBrew](https://switchbrew.org/wiki/Capture_services) · [miroir](https://github.com/backupbrew/switchbrew/blob/master/Capture%20services.md)

**98 commandes documentées**.

| Interface / section | ID | Fonction | Disponibilité indiquée | Encore | Vérifié |
|---|---|---|---|---|---|
| caps:a | `0` | `GetAlbumFileCount` | — | Q | 2026-11-21 |
| caps:a | `1` | `GetAlbumFileList` | — | Q | 2026-11-21 |
| caps:a | `2` | `LoadAlbumFile` | — | Q | 2026-11-21 |
| caps:a | `3` | `DeleteAlbumFile` | — | Q | 2026-11-21 |
| caps:a | `4` | `StorageCopyAlbumFile` | — | Q | 2026-11-21 |
| caps:a | `5` | `IsAlbumMounted` | — | Q | 2026-11-21 |
| caps:a | `6` | `GetAlbumUsage` | — | Q | 2026-11-21 |
| caps:a | `7` | `GetAlbumFileSize` | — | Q | 2026-11-21 |
| caps:a | `8` | `LoadAlbumFileThumbnail` | — | Q | 2026-11-21 |
| caps:a | `9` | `LoadAlbumScreenShotImage` | 2.0.0+ | Q | 2026-11-21 |
| caps:a | `10` | `LoadAlbumScreenShotThumbnailImage` | 2.0.0+ | Q | 2026-11-21 |
| caps:a | `11` | `GetAlbumEntryFromApplicationAlbumEntry` | 2.0.0+ | Q | 2026-11-21 |
| caps:a | `12` | `LoadAlbumScreenShotImageEx` | 3.0.0+ | Q | 2026-11-21 |
| caps:a | `13` | `LoadAlbumScreenShotThumbnailImageEx` | 3.0.0+ | Q | 2026-11-21 |
| caps:a | `14` | `LoadAlbumScreenShotImageEx0` | 3.0.0+ | Q | 2026-11-21 |
| caps:a | `15` | `GetAlbumUsage3` | 4.0.0+ | Q | 2026-11-21 |
| caps:a | `16` | `GetAlbumMountResult` | 4.0.0+ | Q | 2026-11-21 |
| caps:a | `17` | `GetAlbumUsage16` | 4.0.0+ | Q | 2026-11-21 |
| caps:a | `100` | `GetAlbumFileCountEx0` | 5.0.0+ | Q | 2026-11-21 |
| caps:a | `101` | `GetAlbumFileListEx0` | 5.0.0+ | Q | 2026-11-21 |
| caps:a | `202` | `SaveEditedScreenShot` | 1.0.0-2.3.0 | Q | 2026-11-21 |
| caps:a | `301` | `GetLastOverlayScreenShotThumbnail` | — | Q | 2026-11-21 |
| caps:a | `302` | `GetLastOverlayMovieThumbnail` | 4.0.0+ | Q | 2026-11-21 |
| caps:a | `401` | `GetAutoSavingStorage` | — | Q | 2026-11-21 |
| caps:a | `501` | `GetRequiredStorageSpaceSizeToCopyAll` | — | Q | 2026-11-21 |
| caps:a | `1001` | `LoadAlbumScreenShotThumbnailImageEx0` | 3.0.0+ | Q | 2026-11-21 |
| caps:a | `1002` | `LoadAlbumScreenShotImageEx1` | 3.0.0+ | Q | 2026-11-21 |
| caps:a | `1003` | `LoadAlbumScreenShotThumbnailImageEx1` | 4.0.0+ | Q | 2026-11-21 |
| caps:a | `8001` | `ForceAlbumUnmounted` | — | Q | 2026-11-21 |
| caps:a | `8002` | `ResetAlbumMountStatus` | — | Q | 2026-11-21 |
| caps:a | `8011` | `RefreshAlbumCache` | — | Q | 2026-11-21 |
| caps:a | `8012` | `GetAlbumCache` | — | Q | 2026-11-21 |
| caps:a | `8013` | `GetAlbumCacheEx` | 4.0.0+ | Q | 2026-11-21 |
| caps:a | `8021` | `GetAlbumEntryFromApplicationAlbumEntryAruid` | 2.0.0+ | Q | 2026-11-21 |
| caps:a | `10011` | `SetInternalErrorConversionEnabled` | — | Q | 2026-11-21 |
| caps:a | `50000` | `LoadMakerNoteInfoForDebug` | 6.0.0+ | Q | 2026-11-21 |
| caps:a | `60002` | `OpenAccessorSession` | 4.0.0+ | Q | 2026-11-21 |
| caps:a | `2001` | `OpenAlbumMovieReadStream` | — | Q | 2026-11-21 |
| caps:a | `2002` | `CloseAlbumMovieReadStream` | — | Q | 2026-11-21 |
| caps:a | `2003` | `GetAlbumMovieReadStreamMovieDataSize` | — | Q | 2026-11-21 |
| caps:a | `2004` | `ReadMovieDataFromAlbumMovieReadStream` | — | Q | 2026-11-21 |
| caps:a | `2005` | `GetAlbumMovieReadStreamBrokenReason` | — | Q | 2026-11-21 |
| caps:a | `2006` | `GetAlbumMovieReadStreamImageDataSize` | — | Q | 2026-11-21 |
| caps:a | `2007` | `ReadImageDataFromAlbumMovieReadStream` | — | Q | 2026-11-21 |
| caps:a | `2008` | `ReadFileAttributeFromAlbumMovieReadStream` | — | Q | 2026-11-21 |
| caps:c | `2001` | `NotifyAlbumStorageIsAvailable` | — | Q | 2026-11-21 |
| caps:c | `2002` | `NotifyAlbumStorageIsUnavailable` | — | Q | 2026-11-21 |
| caps:c | `2011` | `RegisterAppletResourceUserId` | 2.0.0+ | Q | 2026-11-21 |
| caps:c | `2012` | `UnregisterAppletResourceUserId` | 2.0.0+ | Q | 2026-11-21 |
| caps:c | `2013` | `GetApplicationIdFromAruid` | 2.0.0+ | Q | 2026-11-21 |
| caps:c | `2014` | `CheckApplicationIdRegistered` | 2.0.0+ | Q | 2026-11-21 |
| caps:c | `2101` | `GenerateCurrentAlbumFileId` | 2.0.0+ | Q | 2026-11-21 |
| caps:c | `2102` | `GenerateApplicationAlbumEnrty` | 2.0.0+ | Q | 2026-11-21 |
| caps:c | `2202` | `SaveAlbumScreenShotFileEx` | 4.0.0+ | Q | 2026-11-21 |
| caps:c | `2301` | `SetOverlayScreenShotThumbnailData` | 2.0.0+ | Q | 2026-11-21 |
| caps:c | `2302` | `SetOverlayMovieThumbnailData` | 4.0.0+ | Q | 2026-11-21 |
| caps:c | `60001` | `OpenControlSession` | 4.0.0+ | Q | 2026-11-21 |
| caps:c | `2001` | `OpenAlbumMovieReadStream` | — | Q | 2026-11-21 |
| caps:c | `2002` | `CloseAlbumMovieReadStream` | — | Q | 2026-11-21 |
| caps:c | `2003` | `GetAlbumMovieReadStreamMovieDataSize` | — | Q | 2026-11-21 |
| caps:c | `2004` | `ReadMovieDataFromAlbumMovieReadStream` | — | Q | 2026-11-21 |
| caps:c | `2005` | `GetAlbumMovieReadStreamBrokenReason` | — | Q | 2026-11-21 |
| caps:c | `2006` | `GetAlbumMovieReadStreamImageDataSize` | — | Q | 2026-11-21 |
| caps:c | `2007` | `ReadImageDataFromAlbumMovieReadStream` | — | Q | 2026-11-21 |
| caps:c | `2008` | `ReadFileAttributeFromAlbumMovieReadStream` | — | Q | 2026-11-21 |
| caps:c | `2401` | `OpenAlbumMovieWriteStream` | — | Q | 2026-11-21 |
| caps:c | `2402` | `FinishAlbumMovieWriteStream` | — | Q | 2026-11-21 |
| caps:c | `2403` | `CommitAlbumMovieWriteStream` | — | Q | 2026-11-21 |
| caps:c | `2404` | `DiscardAlbumMovieWriteStream` | — | Q | 2026-11-21 |
| caps:c | `2405` | `DiscardAlbumMovieWriteStreamNoDelete` | — | Q | 2026-11-21 |
| caps:c | `2411` | `StartAlbumMovieWriteStreamDataSection` | — | Q | 2026-11-21 |
| caps:c | `2412` | `EndAlbumMovieWriteStreamDataSection` | — | Q | 2026-11-21 |
| caps:c | `2413` | `StartAlbumMovieWriteStreamMetaSection` | — | Q | 2026-11-21 |
| caps:c | `2414` | `EndAlbumMovieWriteStreamMetaSection` | — | Q | 2026-11-21 |
| caps:c | `2421` | `ReadDataFromAlbumMovieWriteStream` | — | Q | 2026-11-21 |
| caps:c | `2422` | `WriteDataToAlbumMovieWriteStream` | — | Q | 2026-11-21 |
| caps:c | `2424` | `WriteMetaToAlbumMovieWriteStream` | — | Q | 2026-11-21 |
| caps:c | `2431` | `GetAlbumMovieWriteStreamBrokenReason` | — | Q | 2026-11-21 |
| caps:c | `2433` | `GetAlbumMovieWriteStreamDataSize` | — | Q | 2026-11-21 |
| caps:c | `2434` | `SetAlbumMovieWriteStreamDataSize` | — | Q | 2026-11-21 |
| caps:u | `32` | `SetShimLibraryVersion` | 7.0.0+ | Q | 2026-11-21 |
| caps:u | `102` | `GetAlbumFileList0AafeAruidDeprecated` | — | Q | 2026-11-21 |
| caps:u | `103` | `DeleteAlbumFileByAruid` | — | Q | 2026-11-21 |
| caps:u | `104` | `GetAlbumFileSizeByAruid` | — | Q | 2026-11-21 |
| caps:u | `105` | `DeleteAlbumFileByAruidForDebug` | — | Q | 2026-11-21 |
| caps:u | `110` | `LoadAlbumScreenShotImageByAruid` | — | Q | 2026-11-21 |
| caps:u | `120` | `LoadAlbumScreenShotThumbnailImageByAruid` | — | Q | 2026-11-21 |
| caps:u | `130` | `PrecheckToCreateContentsByAruid` | — | Q | 2026-11-21 |
| caps:u | `140` | `GetAlbumFileList1AafeAruidDeprecated` | 6.0.0+ | Q | 2026-11-21 |
| caps:u | `141` | `GetAlbumFileList2AafeUidAruidDeprecated` | 6.0.0+ | Q | 2026-11-21 |
| caps:u | `142` | `GetAlbumFileList3AaeAruid` | 7.0.0+ | Q | 2026-11-21 |
| caps:u | `143` | `GetAlbumFileList4AaeUidAruid` | 7.0.0+ | Q | 2026-11-21 |
| caps:u | `60002` | `OpenAccessorSessionForApplication` | — | Q | 2026-11-21 |
| caps:u | `2001` | `OpenAlbumMovieReadStream` | — | Q | 2026-11-21 |
| caps:u | `2002` | `CloseAlbumMovieReadStream` | — | Q | 2026-11-21 |
| caps:u | `2003` | `GetAlbumMovieReadStreamMovieDataSize` | — | Q | 2026-11-21 |
| caps:u | `2004` | `ReadMovieDataFromAlbumMovieReadStream` | — | Q | 2026-11-21 |
| caps:u | `2005` | `GetAlbumMovieReadStreamBrokenReason` | — | Q | 2026-11-21 |

### Display services

[Wiki SwitchBrew](https://switchbrew.org/wiki/Display_services) · [miroir](https://github.com/backupbrew/switchbrew/blob/master/Display%20services.md)

**183 commandes documentées**.

| Interface / section | ID | Fonction | Disponibilité indiquée | Encore | Vérifié |
|---|---|---|---|---|---|
| caps:sc | `1` | `CaptureRawImage` | — | Q | 2026-11-21 |
| caps:sc | `2` | `CaptureRawImageWithTimeout` | — | Q | 2026-11-21 |
| caps:sc | `3` | `AttachSharedBuffer` | 5.0.0+ | Q | 2026-11-21 |
| caps:sc | `5` | `CaptureRawImageToAttachedSharedBuffer` | 5.0.0+ | Q | 2026-11-21 |
| caps:sc | `210` | `?` | 6.0.0+ | Q | 2026-11-21 |
| caps:sc | `1004` | `RequestTakingScreenShotEx1` | 5.0.0+ | Q | 2026-11-21 |
| caps:sc | `1009` | `CancelTakingScreenShot` | 5.0.0+ | Q | 2026-11-21 |
| caps:sc | `1010` | `SetTakingScreenShotCancelState` | 5.0.0+ | Q | 2026-11-21 |
| caps:sc | `1011` | `NotifyTakingScreenShotRefused` | — | Q | 2026-11-21 |
| caps:sc | `1012` | `NotifyTakingScreenShotFailed` | — | Q | 2026-11-21 |
| caps:sc | `1101` | `SetupOverlayMovieThumbnail` | 4.0.0+ | Q | 2026-11-21 |
| caps:sc | `1106` | `?` | 4.0.0+ | Q | 2026-11-21 |
| caps:sc | `1107` | `?` | 4.0.0+ | Q | 2026-11-21 |
| caps:sc | `1201` | `OpenRawScreenShotReadStream` | 3.0.0+ | Q | 2026-11-21 |
| caps:sc | `1202` | `CloseRawScreenShotReadStream` | 3.0.0+ | Q | 2026-11-21 |
| caps:sc | `1203` | `ReadRawScreenShotReadStream` | 3.0.0+ | Q | 2026-11-21 |
| caps:ss | `201` | `SaveScreenShot` | — | Q | 2026-11-21 |
| caps:ss | `202` | `SaveEditedScreenShot` | — | Q | 2026-11-21 |
| caps:ss | `203` | `SaveScreenShotEx0` | 3.0.0+ | Q | 2026-11-21 |
| caps:ss | `204` | `SaveEditedScreenShotEx0` | 3.0.0+ | Q | 2026-11-21 |
| caps:ss | `206` | `[?+]` | — | Q | 2026-11-21 |
| caps:ss | `208` | `SaveScreenShotOfMovieEx1` | 5.0.0+ | Q | 2026-11-21 |
| caps:su | `201` | `SaveScreenShot` | — | Q | 2026-11-21 |
| caps:su | `203` | `SaveScreenShotEx0` | — | Q | 2026-11-21 |
| cec-mgr | `0` | `RegisterCallback` | — | Q | 2026-11-21 |
| cec-mgr | `1` | `UnregisterCallback` | — | Q | 2026-11-21 |
| cec-mgr | `2` | `TriggerSystemEvent` | — | Q | 2026-11-21 |
| cec-mgr | `3` | `PerformAction` | — | Q | 2026-11-21 |
| cec-mgr | `4` | `QueryState` | — | Q | 2026-11-21 |
| cec-mgr | `5` | `OnSystemEvent` | — | Q | 2026-11-21 |
| cec-mgr | `6` | `CancelCurrentCall` | 2.0.0+ | Q | 2026-11-21 |
| cec-mgr | `100` | `GetHdcpServiceObject` | 4.0.0+ | Q | 2026-11-21 |
| IHdcpController | `0` | `GetHdcpStateTransitionEvent` | — | Q | 2026-11-21 |
| IHdcpController | `1` | `GetHdcpAuthenticationState` | — | Q | 2026-11-21 |
| IHdcpController | `2` | `SetCurrentHdcpMode` | — | Q | 2026-11-21 |
| IHdcpController | `3` | `GetCurrentHdcpMode` | — | Q | 2026-11-21 |
| mm:u | `0` | `InitializeOld` | — | Q | 2026-11-21 |
| mm:u | `1` | `FinalizeOld` | — | Q | 2026-11-21 |
| mm:u | `2` | `SetAndWaitOld` | — | Q | 2026-11-21 |
| mm:u | `3` | `GetOld` | — | Q | 2026-11-21 |
| mm:u | `4` | `Initialize` | — | Q | 2026-11-21 |
| mm:u | `5` | `Finalize` | — | Q | 2026-11-21 |
| mm:u | `6` | `SetAndWait` | — | Q | 2026-11-21 |
| mm:u | `7` | `Get` | — | Q | 2026-11-21 |
| vi:u | `0` | `[GetDisplayService](#vi:u "wikilink")` | — | Q | 2026-11-21 |
| vi:u | `1` | `[GetDisplayServiceWithProxyNameExchange](#vi:u "wikilink")` | 9.0.0+ | Q | 2026-11-21 |
| vi:s | `1` | `[GetDisplayService](#vi:s "wikilink")` | — | Q | 2026-11-21 |
| vi:s | `3` | `[GetDisplayServiceWithProxyNameExchange](#vi:s "wikilink")` | — | Q | 2026-11-21 |
| vi:m | `2` | `[GetDisplayService](#vi:m "wikilink")` | — | Q | 2026-11-21 |
| vi:m | `3` | `[GetDisplayServiceWithProxyNameExchange](#vi:m "wikilink")` | — | Q | 2026-11-21 |
| IApplicationDisplayService | `100` | `GetRelayService` | — | Q | 2026-11-21 |
| IApplicationDisplayService | `101` | `GetSystemDisplayService` | — | Q | 2026-11-21 |
| IApplicationDisplayService | `102` | `GetManagerDisplayService` | — | Q | 2026-11-21 |
| IApplicationDisplayService | `103` | `GetIndirectDisplayTransactionService` | 2.0.0+ | Q | 2026-11-21 |
| IApplicationDisplayService | `1000` | `ListDisplays` | — | Q | 2026-11-21 |
| IApplicationDisplayService | `1010` | `OpenDisplay` | — | Q | 2026-11-21 |
| IApplicationDisplayService | `1011` | `OpenDefaultDisplay` | — | Q | 2026-11-21 |
| IApplicationDisplayService | `1020` | `CloseDisplay` | — | Q | 2026-11-21 |
| IApplicationDisplayService | `1101` | `SetDisplayEnabled` | — | Q | 2026-11-21 |
| IApplicationDisplayService | `1102` | `GetDisplayResolution` | — | Q | 2026-11-21 |
| IApplicationDisplayService | `2020` | `OpenLayer` | — | Q | 2026-11-21 |
| IApplicationDisplayService | `2021` | `CloseLayer` | — | Q | 2026-11-21 |
| IApplicationDisplayService | `2030` | `CreateStrayLayer` | — | Q | 2026-11-21 |
| IApplicationDisplayService | `2031` | `DestroyStrayLayer` | — | Q | 2026-11-21 |
| IApplicationDisplayService | `2101` | `SetLayerScalingMode` | — | Q | 2026-11-21 |
| IApplicationDisplayService | `2102` | `ConvertScalingMode` | 5.0.0+ | Q | 2026-11-21 |
| IApplicationDisplayService | `2450` | `GetIndirectLayerImageMap` | — | Q | 2026-11-21 |
| IApplicationDisplayService | `2451` | `GetIndirectLayerImageCropMap` | — | Q | 2026-11-21 |
| IApplicationDisplayService | `2460` | `GetIndirectLayerImageRequiredMemoryInfo` | — | Q | 2026-11-21 |
| IApplicationDisplayService | `5202` | `GetDisplayVsyncEvent` | — | Q | 2026-11-21 |
| IApplicationDisplayService | `5203` | `GetDisplayVsyncEventForDebug` | — | Q | 2026-11-21 |
| IApplicationDisplayService | `1200` | `GetZOrderCountMin` | — | Q | 2026-11-21 |
| IApplicationDisplayService | `1202` | `GetZOrderCountMax` | — | Q | 2026-11-21 |
| IApplicationDisplayService | `1203` | `GetDisplayLogicalResolution` | — | Q | 2026-11-21 |
| IApplicationDisplayService | `1204` | `SetDisplayMagnification` | 3.0.0+ | Q | 2026-11-21 |
| IApplicationDisplayService | `2201` | `SetLayerPosition` | — | Q | 2026-11-21 |
| IApplicationDisplayService | `2203` | `SetLayerSize` | — | Q | 2026-11-21 |
| IApplicationDisplayService | `2204` | `GetLayerZ` | — | Q | 2026-11-21 |
| IApplicationDisplayService | `2205` | `SetLayerZ` | — | Q | 2026-11-21 |
| IApplicationDisplayService | `2207` | `SetLayerVisibility` | — | Q | 2026-11-21 |
| IApplicationDisplayService | `2209` | `SetLayerAlpha` | — | Q | 2026-11-21 |
| IApplicationDisplayService | `2312` | `CreateStrayLayer` | 1.0.0-6.2.0 | Q | 2026-11-21 |
| IApplicationDisplayService | `2400` | `OpenIndirectLayer` | — | Q | 2026-11-21 |
| IApplicationDisplayService | `2401` | `CloseIndirectLayer` | — | Q | 2026-11-21 |
| IApplicationDisplayService | `2402` | `FlipIndirectLayer` | — | Q | 2026-11-21 |
| IApplicationDisplayService | `3000` | `ListDisplayModes` | — | Q | 2026-11-21 |
| IApplicationDisplayService | `3001` | `ListDisplayRgbRanges` | — | Q | 2026-11-21 |
| IApplicationDisplayService | `3002` | `ListDisplayContentTypes` | — | Q | 2026-11-21 |
| IApplicationDisplayService | `3200` | `GetDisplayMode` | — | Q | 2026-11-21 |
| IApplicationDisplayService | `3201` | `SetDisplayMode` | — | Q | 2026-11-21 |
| IApplicationDisplayService | `3202` | `GetDisplayUnderscan` | — | Q | 2026-11-21 |
| IApplicationDisplayService | `3203` | `SetDisplayUnderscan` | — | Q | 2026-11-21 |
| IApplicationDisplayService | `3204` | `GetDisplayContentType` | — | Q | 2026-11-21 |
| IApplicationDisplayService | `3205` | `SetDisplayContentType` | — | Q | 2026-11-21 |
| IApplicationDisplayService | `3206` | `GetDisplayRgbRange` | — | Q | 2026-11-21 |
| IApplicationDisplayService | `3207` | `SetDisplayRgbRange` | — | Q | 2026-11-21 |
| IApplicationDisplayService | `3208` | `GetDisplayCmuMode` | — | Q | 2026-11-21 |
| IApplicationDisplayService | `3209` | `SetDisplayCmuMode` | — | Q | 2026-11-21 |
| IApplicationDisplayService | `3210` | `GetDisplayContrastRatio` | — | Q | 2026-11-21 |
| IApplicationDisplayService | `3211` | `SetDisplayContrastRatio` | — | Q | 2026-11-21 |
| IApplicationDisplayService | `3214` | `GetDisplayGamma` | — | Q | 2026-11-21 |
| IApplicationDisplayService | `3215` | `SetDisplayGamma` | — | Q | 2026-11-21 |
| IApplicationDisplayService | `3216` | `GetDisplayCmuLuma` | — | Q | 2026-11-21 |
| IApplicationDisplayService | `3217` | `SetDisplayCmuLuma` | — | Q | 2026-11-21 |
| IApplicationDisplayService | `8225` | `GetSharedBufferMemoryHandleId` | 4.0.0+ | Q | 2026-11-21 |
| IApplicationDisplayService | `8250` | `OpenSharedLayer` | 4.0.0+ | Q | 2026-11-21 |
| IApplicationDisplayService | `8251` | `CloseSharedLayer` | 4.0.0+ | Q | 2026-11-21 |
| IApplicationDisplayService | `8252` | `ConnectSharedLayer` | 4.0.0+ | Q | 2026-11-21 |
| IApplicationDisplayService | `8253` | `DisconnectSharedLayer` | 4.0.0+ | Q | 2026-11-21 |
| IApplicationDisplayService | `8254` | `AcquireSharedFrameBuffer` | 4.0.0+ | Q | 2026-11-21 |
| IApplicationDisplayService | `8255` | `PresentSharedFrameBuffer` | 4.0.0+ | Q | 2026-11-21 |
| IApplicationDisplayService | `8256` | `GetSharedFrameBufferAcquirableEvent` | 4.0.0+ | Q | 2026-11-21 |
| IApplicationDisplayService | `8257` | `FillSharedFrameBufferColor` | 4.0.0+ | Q | 2026-11-21 |
| IApplicationDisplayService | `8258` | `CancelSharedFrameBuffer` | 5.0.0+ | Q | 2026-11-21 |
| IApplicationDisplayService | `200` | `AllocateProcessHeapBlock` | 4.0.0+ | Q | 2026-11-21 |
| IApplicationDisplayService | `201` | `FreeProcessHeapBlock` | 4.0.0+ | Q | 2026-11-21 |
| IApplicationDisplayService | `2010` | `CreateManagedLayer` | — | Q | 2026-11-21 |
| IApplicationDisplayService | `2011` | `DestroyManagedLayer` | — | Q | 2026-11-21 |
| IApplicationDisplayService | `2012` | `CreateStrayLayer` | 7.0.0+ | Q | 2026-11-21 |
| IApplicationDisplayService | `2050` | `CreateIndirectLayer` | — | Q | 2026-11-21 |
| IApplicationDisplayService | `2051` | `DestroyIndirectLayer` | — | Q | 2026-11-21 |
| IApplicationDisplayService | `2052` | `CreateIndirectProducerEndPoint` | — | Q | 2026-11-21 |
| IApplicationDisplayService | `2053` | `DestroyIndirectProducerEndPoint` | — | Q | 2026-11-21 |
| IApplicationDisplayService | `2054` | `CreateIndirectConsumerEndPoint` | — | Q | 2026-11-21 |
| IApplicationDisplayService | `2055` | `DestroyIndirectConsumerEndPoint` | — | Q | 2026-11-21 |
| IApplicationDisplayService | `2300` | `AcquireLayerTexturePresentingEvent` | — | Q | 2026-11-21 |
| IApplicationDisplayService | `2301` | `ReleaseLayerTexturePresentingEvent` | — | Q | 2026-11-21 |
| IApplicationDisplayService | `2302` | `GetDisplayHotplugEvent` | — | Q | 2026-11-21 |
| IApplicationDisplayService | `2303` | `GetDisplayModeChangedEvent` | 5.1.0+ | Q | 2026-11-21 |
| IApplicationDisplayService | `2402` | `GetDisplayHotplugState` | — | Q | 2026-11-21 |
| IApplicationDisplayService | `2501` | `GetCompositorErrorInfo` | 4.0.0+ | Q | 2026-11-21 |
| IApplicationDisplayService | `2601` | `GetDisplayErrorEvent` | 4.0.0+ | Q | 2026-11-21 |
| IApplicationDisplayService | `4201` | `SetDisplayAlpha` | — | Q | 2026-11-21 |
| IApplicationDisplayService | `4203` | `SetDisplayLayerStack` | — | Q | 2026-11-21 |
| IApplicationDisplayService | `4205` | `SetDisplayPowerState` | — | Q | 2026-11-21 |
| IApplicationDisplayService | `4206` | `SetDefaultDisplay` | 4.0.0+ | Q | 2026-11-21 |
| IApplicationDisplayService | `6000` | `AddToLayerStack` | — | Q | 2026-11-21 |
| IApplicationDisplayService | `6001` | `RemoveFromLayerStack` | — | Q | 2026-11-21 |
| IApplicationDisplayService | `6002` | `SetLayerVisibility` | — | Q | 2026-11-21 |
| IApplicationDisplayService | `6003` | `SetLayerConfig` | 5.0.0+ | Q | 2026-11-21 |
| IApplicationDisplayService | `6004` | `AttachLayerPresentationTracer` | 5.0.0+ | Q | 2026-11-21 |
| IApplicationDisplayService | `6005` | `DetachLayerPresentationTracer` | 5.0.0+ | Q | 2026-11-21 |
| IApplicationDisplayService | `6006` | `StartLayerPresentationRecording` | 5.0.0+ | Q | 2026-11-21 |
| IApplicationDisplayService | `6007` | `StopLayerPresentationRecording` | 5.0.0+ | Q | 2026-11-21 |
| IApplicationDisplayService | `6008` | `StartLayerPresentationFenceWait` | 5.0.0+ | Q | 2026-11-21 |
| IApplicationDisplayService | `6009` | `StopLayerPresentationFenceWait` | 5.0.0+ | Q | 2026-11-21 |
| IApplicationDisplayService | `6010` | `GetLayerPresentationAllFencesExpiredEvent` | 5.0.0+ | Q | 2026-11-21 |
| IApplicationDisplayService | `6011` | `EnableLayerAutoClearTransitionBuffer` | 7.0.0+ | Q | 2026-11-21 |
| IApplicationDisplayService | `6012` | `DisableLayerAutoClearTransitionBuffer` | 7.0.0+ | Q | 2026-11-21 |
| IApplicationDisplayService | `7000` | `SetContentVisibility` | — | Q | 2026-11-21 |
| IApplicationDisplayService | `8000` | `SetConductorLayer` | — | Q | 2026-11-21 |
| IApplicationDisplayService | `8001` | `SetTimestampTracking` | 8.0.0+ | Q | 2026-11-21 |
| IApplicationDisplayService | `8100` | `SetIndirectProducerFlipOffset` | — | Q | 2026-11-21 |
| IApplicationDisplayService | `8200` | `CreateSharedBufferStaticStorage` | 4.0.0+ | Q | 2026-11-21 |
| IApplicationDisplayService | `8201` | `CreateSharedBufferTransferMemory` | 4.0.0+ | Q | 2026-11-21 |
| IApplicationDisplayService | `8202` | `DestroySharedBuffer` | 4.0.0+ | Q | 2026-11-21 |
| IApplicationDisplayService | `8203` | `BindSharedLowLevelLayerToManagedLayer` | 4.0.0+ | Q | 2026-11-21 |
| IApplicationDisplayService | `8204` | `BindSharedLowLevelLayerToIndirectLayer` | 4.0.0+ | Q | 2026-11-21 |
| IApplicationDisplayService | `8207` | `UnbindSharedLowLevelLayer` | 4.0.0+ | Q | 2026-11-21 |
| IApplicationDisplayService | `8208` | `ConnectSharedLowLevelLayerToSharedBuffer` | 4.0.0+ | Q | 2026-11-21 |
| IApplicationDisplayService | `8209` | `DisconnectSharedLowLevelLayerFromSharedBuffer` | 4.0.0+ | Q | 2026-11-21 |
| IApplicationDisplayService | `8210` | `CreateSharedLayer` | 4.0.0+ | Q | 2026-11-21 |
| IApplicationDisplayService | `8211` | `DestroySharedLayer` | 4.0.0+ | Q | 2026-11-21 |
| IApplicationDisplayService | `8216` | `AttachSharedLayerToLowLevelLayer` | 4.0.0+ | Q | 2026-11-21 |
| IApplicationDisplayService | `8217` | `ForceDetachSharedLayerFromLowLevelLayer` | 4.0.0+ | Q | 2026-11-21 |
| IApplicationDisplayService | `8218` | `StartDetachSharedLayerFromLowLevelLayer` | 4.0.0+ | Q | 2026-11-21 |
| IApplicationDisplayService | `8219` | `FinishDetachSharedLayerFromLowLevelLayer` | 4.0.0+ | Q | 2026-11-21 |
| IApplicationDisplayService | `8220` | `GetSharedLayerDetachReadyEvent` | 4.0.0+ | Q | 2026-11-21 |
| IApplicationDisplayService | `8221` | `GetSharedLowLevelLayerSynchronizedEvent` | 4.0.0+ | Q | 2026-11-21 |
| IApplicationDisplayService | `8222` | `CheckSharedLowLevelLayerSynchronized` | 4.0.0+ | Q | 2026-11-21 |
| IApplicationDisplayService | `8223` | `RegisterSharedBufferImporterAruid` | 4.0.0+ | Q | 2026-11-21 |
| IApplicationDisplayService | `8224` | `UnregisterSharedBufferImporterAruid` | 4.0.0+ | Q | 2026-11-21 |
| IApplicationDisplayService | `8227` | `CreateSharedBufferProcessHeap` | 4.0.0+ | Q | 2026-11-21 |
| IApplicationDisplayService | `8228` | `GetSharedLayerLayerStacks` | 4.0.0+ | Q | 2026-11-21 |
| IApplicationDisplayService | `8229` | `SetSharedLayerLayerStacks` | 4.0.0+ | Q | 2026-11-21 |
| IApplicationDisplayService | `8291` | `PresentDetachedSharedFrameBufferToLowLevelLayer` | 4.0.0+ | Q | 2026-11-21 |
| IApplicationDisplayService | `8292` | `FillDetachedSharedFrameBufferColor` | 4.0.0+ | Q | 2026-11-21 |
| IApplicationDisplayService | `8293` | `GetDetachedSharedFrameBufferImage` | 4.0.0+ | Q | 2026-11-21 |
| IApplicationDisplayService | `8294` | `SetDetachedSharedFrameBufferImage` | 4.0.0+ | Q | 2026-11-21 |
| IApplicationDisplayService | `8295` | `CopyDetachedSharedFrameBufferImage` | 4.0.0+ | Q | 2026-11-21 |
| IApplicationDisplayService | `8296` | `SetDetachedSharedFrameBufferSubImage` | 4.0.0+ | Q | 2026-11-21 |
| IApplicationDisplayService | `8297` | `GetSharedFrameBufferContentParameter` | 4.0.0+ | Q | 2026-11-21 |
| IApplicationDisplayService | `8298` | `ExpandStartupLogoOnSharedFrameBuffer` | 5.0.0+ | Q | 2026-11-21 |

### Nvnflinger services

[Wiki SwitchBrew](https://switchbrew.org/wiki/Nvnflinger_services) · [miroir](https://github.com/backupbrew/switchbrew/blob/master/Nvnflinger%20services.md)

**4 commandes documentées**.

| Interface / section | ID | Fonction | Disponibilité indiquée | Encore | Vérifié |
|---|---|---|---|---|---|
| dispdrv | `0` | `TransactParcel` | — | Q | 2026-11-21 |
| dispdrv | `1` | `AdjustRefcount` | — | Q | 2026-11-21 |
| dispdrv | `2` | `GetNativeHandle` | — | Q | 2026-11-21 |
| dispdrv | `3` | `TransactParcelAuto` | 3.0.0+ | Q | 2026-11-21 |

### Debug Monitor services

[Wiki SwitchBrew](https://switchbrew.org/wiki/Debug_Monitor_services) · [miroir](https://github.com/backupbrew/switchbrew/blob/master/Debug%20Monitor%20services.md)

**51 commandes documentées**.

| Interface / section | ID | Fonction | Disponibilité indiquée | Encore | Vérifié |
|---|---|---|---|---|---|
| dmnt:- | `0` | `BreakDebugProcess` | — | Q | 2026-11-21 |
| dmnt:- | `1` | `TerminateDebugProcess` | — | Q | 2026-11-21 |
| dmnt:- | `2` | `CloseHandle` | — | Q | 2026-11-21 |
| dmnt:- | `3` | `LoadImage` | — | Q | 2026-11-21 |
| dmnt:- | `4` | `GetProcessId` | — | Q | 2026-11-21 |
| dmnt:- | `5` | `GetProcessHandle` | — | Q | 2026-11-21 |
| dmnt:- | `6` | `WaitSynchronization` | — | Q | 2026-11-21 |
| dmnt:- | `7` | `GetDebugEvent` | — | Q | 2026-11-21 |
| dmnt:- | `8` | `GetProcessModuleInfo` | — | Q | 2026-11-21 |
| dmnt:- | `9` | `GetProcessList` | — | Q | 2026-11-21 |
| dmnt:- | `10` | `GetThreadList` | — | Q | 2026-11-21 |
| dmnt:- | `11` | `GetDebugThreadContext` | — | Q | 2026-11-21 |
| dmnt:- | `12` | `ContinueDebugEvent` | — | Q | 2026-11-21 |
| dmnt:- | `13` | `ReadDebugProcessMemory` | — | Q | 2026-11-21 |
| dmnt:- | `14` | `WriteDebugProcessMemory` | — | Q | 2026-11-21 |
| dmnt:- | `15` | `SetDebugThreadContext` | — | Q | 2026-11-21 |
| dmnt:- | `16` | `GetDebugThreadParam` | — | Q | 2026-11-21 |
| dmnt:- | `17` | `InitializeThreadInfo` | — | Q | 2026-11-21 |
| dmnt:- | `18` | `SetHardwareBreakPoint` | — | Q | 2026-11-21 |
| dmnt:- | `19` | `QueryDebugProcessMemory` | — | Q | 2026-11-21 |
| dmnt:- | `20` | `GetProcessMemoryDetails` | — | Q | 2026-11-21 |
| dmnt:- | `21` | `AttachByProgramId` | — | Q | 2026-11-21 |
| dmnt:- | `22` | `AttachOnLaunch` | — | Q | 2026-11-21 |
| dmnt:- | `23` | `GetDebugMonitorProcessId` | — | Q | 2026-11-21 |
| dmnt:- | `25` | `GetJitDebugProcessList` | — | Q | 2026-11-21 |
| dmnt:- | `26` | `CreateCoreDump` | — | Q | 2026-11-21 |
| dmnt:- | `27` | `GetAllDebugThreadInfo` | — | Q | 2026-11-21 |
| dmnt:- | `29` | `TargetIO\_FileOpen` | — | Q | 2026-11-21 |
| dmnt:- | `30` | `TargetIO\_FileClose` | — | Q | 2026-11-21 |
| dmnt:- | `31` | `TargetIO\_FileRead` | — | Q | 2026-11-21 |
| dmnt:- | `32` | `TargetIO\_FileWrite` | — | Q | 2026-11-21 |
| dmnt:- | `33` | `TargetIO\_FileSetAttributes` | — | Q | 2026-11-21 |
| dmnt:- | `34` | `TargetIO\_FileGetInformation` | — | Q | 2026-11-21 |
| dmnt:- | `35` | `TargetIO\_FileSetTime` | — | Q | 2026-11-21 |
| dmnt:- | `36` | `TargetIO\_FileSetSize` | — | Q | 2026-11-21 |
| dmnt:- | `37` | `TargetIO\_FileDelete` | — | Q | 2026-11-21 |
| dmnt:- | `38` | `TargetIO\_FileMove` | — | Q | 2026-11-21 |
| dmnt:- | `39` | `TargetIO\_DirectoryCreate` | — | Q | 2026-11-21 |
| dmnt:- | `40` | `TargetIO\_DirectoryDelete` | — | Q | 2026-11-21 |
| dmnt:- | `41` | `TargetIO\_DirectoryRename` | — | Q | 2026-11-21 |
| dmnt:- | `42` | `TargetIO\_DirectoryGetCount` | — | Q | 2026-11-21 |
| dmnt:- | `43` | `TargetIO\_DirectoryOpen` | — | Q | 2026-11-21 |
| dmnt:- | `44` | `TargetIO\_DirectoryGetNext` | — | Q | 2026-11-21 |
| dmnt:- | `45` | `TargetIO\_DirectoryClose` | — | Q | 2026-11-21 |
| dmnt:- | `46` | `TargetIO\_GetFreeSpace` | — | Q | 2026-11-21 |
| dmnt:- | `47` | `TargetIO\_GetVolumeInformation` | — | Q | 2026-11-21 |
| dmnt:- | `48` | `InitiateCoreDump` | — | Q | 2026-11-21 |
| dmnt:- | `49` | `ContinueCoreDump` | — | Q | 2026-11-21 |
| dmnt:- | `50` | `AddTTYToCoreDump` | — | Q | 2026-11-21 |
| dmnt:- | `51` | `AddImageToCoreDump` | — | Q | 2026-11-21 |
| dmnt:- | `52` | `CloseCoreDump` | — | Q | 2026-11-21 |

### Error Report services

[Wiki SwitchBrew](https://switchbrew.org/wiki/Error_Report_services) · [miroir](https://github.com/backupbrew/switchbrew/blob/master/Error%20Report%20services.md)

**26 commandes documentées**.

| Interface / section | ID | Fonction | Disponibilité indiquée | Encore | Vérifié |
|---|---|---|---|---|---|
| erpt:c | `0` | `SubmitContext` | — | Q | 2026-11-21 |
| erpt:c | `1` | `CreateReport` | — | Q | 2026-11-21 |
| erpt:c | `2` | `SetInitialLaunchSettingsCompletionTime` | 3.0.0+ | Q | 2026-11-21 |
| erpt:c | `3` | `ClearInitialLaunchSettingsCompletionTime` | 3.0.0+ | Q | 2026-11-21 |
| erpt:c | `4` | `UpdatePowerOnTime` | 3.0.0+ | Q | 2026-11-21 |
| erpt:c | `5` | `UpdateAwakeTime` | 3.0.0+ | Q | 2026-11-21 |
| erpt:c | `6` | `SubmitMultipleCategoryContext` | 5.0.0+ | Q | 2026-11-21 |
| erpt:c | `7` | `UpdateApplicationLaunchTime` | 6.0.0+ | Q | 2026-11-21 |
| erpt:c | `8` | `ClearApplicationLaunchTime` | 6.0.0+ | Q | 2026-11-21 |
| erpt:c | `9` | `SubmitAttachment` | 8.0.0+ | Q | 2026-11-21 |
| erpt:c | `10` | `CreateReportWithAttachments` | 8.0.0+ | Q | 2026-11-21 |
| erpt:r | `0` | `OpenReport` | — | Q | 2026-11-21 |
| erpt:r | `1` | `OpenManager` | — | Q | 2026-11-21 |
| erpt:r | `2` | `OpenAttachment` | 8.0.0+ | Q | 2026-11-21 |
| erpt:r | `0` | `Open` | — | Q | 2026-11-21 |
| erpt:r | `1` | `Read` | — | Q | 2026-11-21 |
| erpt:r | `2` | `SetFlags` | — | Q | 2026-11-21 |
| erpt:r | `3` | `GetFlags` | — | Q | 2026-11-21 |
| erpt:r | `4` | `Close` | — | Q | 2026-11-21 |
| erpt:r | `5` | `GetSize` | — | Q | 2026-11-21 |
| erpt:r | `0` | `GetReportList` | — | Q | 2026-11-21 |
| erpt:r | `1` | `GetEvent` | — | Q | 2026-11-21 |
| erpt:r | `2` | `CleanupReports` | 4.0.0+ | Q | 2026-11-21 |
| erpt:r | `3` | `DeleteReport` | 5.0.0+ | Q | 2026-11-21 |
| erpt:r | `4` | `GetStorageUsageStatistics` | 5.0.0+ | Q | 2026-11-21 |
| erpt:r | `5` | `GetAttachmentList` | 8.0.0+ | Q | 2026-11-21 |

### Error Upload services

[Wiki SwitchBrew](https://switchbrew.org/wiki/Error_Upload_services) · [miroir](https://github.com/backupbrew/switchbrew/blob/master/Error%20Upload%20services.md)

**11 commandes documentées**.

| Interface / section | ID | Fonction | Disponibilité indiquée | Encore | Vérifié |
|---|---|---|---|---|---|
| eupld:c | `0` | `SetUrl` | — | Q | 2026-11-21 |
| eupld:c | `1` | `ImportCrt` | — | Q | 2026-11-21 |
| eupld:c | `2` | `ImportPki` | — | Q | 2026-11-21 |
| eupld:c | `3` | `SetAutoUpload` | — | Q | 2026-11-21 |
| eupld:c | `4` | `GetAutoUpload` | 6.0.0+ | Q | 2026-11-21 |
| eupld:r | `0` | `Initialize` | — | Q | 2026-11-21 |
| eupld:r | `1` | `UploadAll` | — | Q | 2026-11-21 |
| eupld:r | `2` | `UploadSelected` | — | Q | 2026-11-21 |
| eupld:r | `3` | `GetUploadStatus` | — | Q | 2026-11-21 |
| eupld:r | `4` | `CancelUpload` | — | Q | 2026-11-21 |
| eupld:r | `5` | `GetResult` | — | Q | 2026-11-21 |

### ETicket services

[Wiki SwitchBrew](https://switchbrew.org/wiki/ETicket_services) · [miroir](https://github.com/backupbrew/switchbrew/blob/master/ETicket%20services.md)

**42 commandes documentées**.

| Interface / section | ID | Fonction | Disponibilité indiquée | Encore | Vérifié |
|---|---|---|---|---|---|
| es | `1` | `ImportTicket` | — | Q | 2026-11-21 |
| es | `2` | `ImportTicketCertificateSet` | — | Q | 2026-11-21 |
| es | `3` | `DeleteTicket` | — | Q | 2026-11-21 |
| es | `4` | `DeletePersonalizedTicket` | — | Q | 2026-11-21 |
| es | `5` | `DeleteAllCommonTicket` | — | Q | 2026-11-21 |
| es | `6` | `DeleteAllPersonalizedTicket` | — | Q | 2026-11-21 |
| es | `7` | `DeleteAllPersonalizedTicketEx` | — | Q | 2026-11-21 |
| es | `8` | `GetTitleKey` | 2.0.0-5.1.0 | Q | 2026-11-21 |
| es | `9` | `CountCommonTicket` | — | Q | 2026-11-21 |
| es | `10` | `CountPersonalizedTicket` | — | Q | 2026-11-21 |
| es | `11` | `ListCommonTicketRightsIds ([2.0.0-5.1.0] ListCommonTicket)` | 6.0.0+ | Q | 2026-11-21 |
| es | `12` | `ListPersonalizedTicketRightsIds ([2.0.0-5.1.0] ListPersonalizedTicket)` | 6.0.0+ | Q | 2026-11-21 |
| es | `13` | `ListMissingPersonalizedTicket` | — | Q | 2026-11-21 |
| es | `14` | `GetCommonTicketSize` | — | Q | 2026-11-21 |
| es | `15` | `GetPersonalizedTicketSize` | 2.0.0-4.1.0 | Q | 2026-11-21 |
| es | `16` | `GetCommonTicketData` | — | Q | 2026-11-21 |
| es | `17` | `GetPersonalizedTicketData` | 2.0.0-4.1.0 | Q | 2026-11-21 |
| es | `18` | `OwnTicket` | — | Q | 2026-11-21 |
| es | `19` | `GetTicketInfo` | — | Q | 2026-11-21 |
| es | `20` | `ListLightTicketInfo` | — | Q | 2026-11-21 |
| es | `21` | `SignData` | 2.0.0-6.2.0 | Q | 2026-11-21 |
| es | `22` | `GetCommonTicketAndCertificateSize` | 4.0.0+ | Q | 2026-11-21 |
| es | `23` | `GetCommonTicketAndCertificateData` | 4.0.0+ | Q | 2026-11-21 |
| es | `24` | `ImportPrepurchaseRecord` | 4.0.0+ | Q | 2026-11-21 |
| es | `25` | `DeletePrepurchaseRecord` | 4.0.0+ | Q | 2026-11-21 |
| es | `26` | `DeleteAllPrepurchaseRecord` | 4.0.0+ | Q | 2026-11-21 |
| es | `27` | `CountPrepurchaseRecord` | 4.0.0+ | Q | 2026-11-21 |
| es | `28` | `ListPrepurchaseRecordRightsIds ([4.0.0-5.1.0] ListPrepurchaseRecord)` | 6.0.0+ | Q | 2026-11-21 |
| es | `29` | `ListPrepurchaseRecordInfo` | 4.0.0+ | Q | 2026-11-21 |
| es | `30` | `CountTicket` | 5.0.0+ | Q | 2026-11-21 |
| es | `31` | `ListTicketRightsIds` | 5.0.0+ | Q | 2026-11-21 |
| es | `32` | `CountPrepurchaseRecordEx` | 5.0.0+ | Q | 2026-11-21 |
| es | `33` | `ListPrepurchaseRecordRightsIdsEx` | 5.0.0-6.2.0 | Q | 2026-11-21 |
| es | `34` | `GetEncryptedTicketSize` | 5.0.0+ | Q | 2026-11-21 |
| es | `35` | `GetEncryptedTicketData` | 5.0.0+ | Q | 2026-11-21 |
| es | `36` | `DeleteAllInactiveELicenseRequiredPersonalizedTicket` | 6.0.0+ | Q | 2026-11-21 |
| es | `37` | `OwnTicket2` | 9.0.0+ | Q | 2026-11-21 |
| es | `38` | `OwnTicket3` | 9.0.0+ | Q | 2026-11-21 |
| es | `503` | `GetTitleKey` | 6.0.0+ | Q | 2026-11-21 |
| es | `1003` | `Returns an EsAsyncValue.` | 6.0.0+ | Q | 2026-11-21 |
| es | `2000` | `No input, returns an EsSubinterface2000.` | 6.0.0+ | Q | 2026-11-21 |
| es | `2001` | `No input, returns an EsSubinterface2000.` | 9.0.0+ | Q | 2026-11-21 |

### PTM services

[Wiki SwitchBrew](https://switchbrew.org/wiki/PTM_services) · [miroir](https://github.com/backupbrew/switchbrew/blob/master/PTM%20services.md)

**71 commandes documentées**.

| Interface / section | ID | Fonction | Disponibilité indiquée | Encore | Vérifié |
|---|---|---|---|---|---|
| fan | `0` | `OpenController` | — | Q | 2026-11-21 |
| fan | `0` | `SetRotationSpeedLevel` | — | Q | 2026-11-21 |
| fan | `1` | `SetRotationSpeedLevelByDiff` | — | Q | 2026-11-21 |
| fan | `2` | `GetRotationSpeedLevel` | — | Q | 2026-11-21 |
| fan | `3` | `SetRotationRate` | — | Q | 2026-11-21 |
| fan | `4` | `GetRotationRate` | — | Q | 2026-11-21 |
| fan | `5` | `EnableFan` | 1.0.0-6.2.0 | Q | 2026-11-21 |
| fan | `6` | `DisableFan` | 1.0.0-6.2.0 | Q | 2026-11-21 |
| fan | `7` | `GetActualRotationSpeedLevel` | 1.0.0-6.2.0 | Q | 2026-11-21 |
| psm | `0` | `GetBatteryChargePercentage` | — | Q | 2026-11-21 |
| psm | `1` | `GetChargerType` | — | Q | 2026-11-21 |
| psm | `2` | `EnableBatteryCharging` | — | Q | 2026-11-21 |
| psm | `3` | `DisableBatteryCharging` | — | Q | 2026-11-21 |
| psm | `4` | `IsBatteryChargingEnabled` | — | Q | 2026-11-21 |
| psm | `5` | `AcquireControllerPowerSupply` | — | Q | 2026-11-21 |
| psm | `6` | `ReleaseControllerPowerSupply` | — | Q | 2026-11-21 |
| psm | `7` | `OpenSession` | — | Q | 2026-11-21 |
| psm | `8` | `EnableEnoughPowerChargeEmulation` | — | Q | 2026-11-21 |
| psm | `9` | `DisableEnoughPowerChargeEmulation` | — | Q | 2026-11-21 |
| psm | `10` | `EnableFastBatteryCharging` | — | Q | 2026-11-21 |
| psm | `11` | `DisableFastBatteryCharging` | — | Q | 2026-11-21 |
| psm | `12` | `GetBatteryVoltageState` | — | Q | 2026-11-21 |
| psm | `13` | `GetRawBatteryChargePercentage` | — | Q | 2026-11-21 |
| psm | `14` | `IsEnoughPowerSupplied` | — | Q | 2026-11-21 |
| psm | `15` | `GetBatteryAgePercentage` | — | Q | 2026-11-21 |
| psm | `16` | `GetBatteryChargeInfoEvent` | — | Q | 2026-11-21 |
| psm | `17` | `GetBatteryChargeInfoFields` | — | Q | 2026-11-21 |
| psm | `18` | `GetBatteryChargeCalibratedEvent` | 3.0.0+ | Q | 2026-11-21 |
| psm | `0` | `BindStateChangeEvent` | — | Q | 2026-11-21 |
| psm | `1` | `UnbindStateChangeEvent` | — | Q | 2026-11-21 |
| psm | `2` | `SetChargerTypeChangeEventEnabled` | — | Q | 2026-11-21 |
| psm | `3` | `SetPowerSupplyChangeEventEnabled` | — | Q | 2026-11-21 |
| psm | `4` | `SetBatteryVoltageStateChangeEventEnabled` | — | Q | 2026-11-21 |
| tc | `0` | `SetOperatingMode` | — | Q | 2026-11-21 |
| tc | `1` | `GetThermalEvent` | — | Q | 2026-11-21 |
| tc | `2` | `IsActionAllowed` | — | Q | 2026-11-21 |
| tc | `3` | `EnableVirtualTemperature` | — | Q | 2026-11-21 |
| tc | `4` | `DisableVirtualTemperature` | — | Q | 2026-11-21 |
| tc | `5` | `SetVirtualTemperature` | — | Q | 2026-11-21 |
| tc | `6` | `EnableFanControl` | — | Q | 2026-11-21 |
| tc | `7` | `DisableFanControl` | — | Q | 2026-11-21 |
| tc | `8` | `IsFanControlEnabled` | — | Q | 2026-11-21 |
| tc | `9` | `GetSkinTemperatureMilliC` | 5.0.0+ | Q | 2026-11-21 |
| ts | `0` | `GetTemperatureRange` | — | Q | 2026-11-21 |
| ts | `1` | `GetTemperature` | — | Q | 2026-11-21 |
| ts | `2` | `SetMeasurementMode` | — | Q | 2026-11-21 |
| ts | `3` | `GetTemperatureMilliC` | — | Q | 2026-11-21 |
| ts | `4` | `? (Takes a total of 4-bytes of input, returns an IUnknown0)` | 8.0.0+ | Q | 2026-11-21 |
| pcm | `0` | `IsSupported` | — | Q | 2026-11-21 |
| pcm | `1` | `ReadCurrentPower` | — | Q | 2026-11-21 |
| apm:am | `0` | `OpenSession` | — | Q | 2026-11-21 |
| apm:am | `1` | `GetPerformanceMode` | — | Q | 2026-11-21 |
| apm:am | `6` | `IsCpuOverclockEnabled` | 7.0.0+ | Q | 2026-11-21 |
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

### Fatal services

[Wiki SwitchBrew](https://switchbrew.org/wiki/Fatal_services) · [miroir](https://github.com/backupbrew/switchbrew/blob/master/Fatal%20services.md)

**4 commandes documentées**.

| Interface / section | ID | Fonction | Disponibilité indiquée | Encore | Vérifié |
|---|---|---|---|---|---|
| fatal:u | `0` | `ThrowFatal` | — | Q | 2026-11-21 |
| fatal:u | `1` | `ThrowFatalWithPolicy` | — | Q | 2026-11-21 |
| fatal:u | `2` | `ThrowFatalWithCpuContext` | — | Q | 2026-11-21 |
| fatal:p | `0` | `GetFatalEvent` | — | Q | 2026-11-21 |

### Friend services

[Wiki SwitchBrew](https://switchbrew.org/wiki/Friend_services) · [miroir](https://github.com/backupbrew/switchbrew/blob/master/Friend%20services.md)

**123 commandes documentées**.

| Interface / section | ID | Fonction | Disponibilité indiquée | Encore | Vérifié |
|---|---|---|---|---|---|
| friend:u, friend:v, friend:m, friend:s, friend:a | `0` | `CreateFriendService` | — | Q | 2026-11-21 |
| friend:u, friend:v, friend:m, friend:s, friend:a | `1` | `CreateNotificationService` | 2.0.0+ | Q | 2026-11-21 |
| friend:u, friend:v, friend:m, friend:s, friend:a | `2` | `CreateDaemonSuspendSessionService` | 4.0.0+ | Q | 2026-11-21 |
| friend:u, friend:v, friend:m, friend:s, friend:a | `0` | `GetCompletionEvent` | — | Q | 2026-11-21 |
| friend:u, friend:v, friend:m, friend:s, friend:a | `1` | `Cancel` | — | Q | 2026-11-21 |
| friend:u, friend:v, friend:m, friend:s, friend:a | `10100` | `GetFriendListIds` | — | Q | 2026-11-21 |
| friend:u, friend:v, friend:m, friend:s, friend:a | `10101` | `GetFriendList` | — | Q | 2026-11-21 |
| friend:u, friend:v, friend:m, friend:s, friend:a | `10102` | `UpdateFriendInfo` | — | Q | 2026-11-21 |
| friend:u, friend:v, friend:m, friend:s, friend:a | `10110` | `GetFriendProfileImage` | — | Q | 2026-11-21 |
| friend:u, friend:v, friend:m, friend:s, friend:a | `10200` | `SendFriendRequestForApplication` | — | Q | 2026-11-21 |
| friend:u, friend:v, friend:m, friend:s, friend:a | `10211` | `AddFacedFriendRequestForApplication` | — | Q | 2026-11-21 |
| friend:u, friend:v, friend:m, friend:s, friend:a | `10400` | `GetBlockedUserListIds` | — | Q | 2026-11-21 |
| friend:u, friend:v, friend:m, friend:s, friend:a | `10500` | `GetProfileList` | — | Q | 2026-11-21 |
| friend:u, friend:v, friend:m, friend:s, friend:a | `10600` | `DeclareOpenOnlinePlaySession` | — | Q | 2026-11-21 |
| friend:u, friend:v, friend:m, friend:s, friend:a | `10601` | `DeclareCloseOnlinePlaySession` | — | Q | 2026-11-21 |
| friend:u, friend:v, friend:m, friend:s, friend:a | `10610` | `UpdateUserPresence` | — | Q | 2026-11-21 |
| friend:u, friend:v, friend:m, friend:s, friend:a | `10700` | `GetPlayHistoryRegistrationKey` | — | Q | 2026-11-21 |
| friend:u, friend:v, friend:m, friend:s, friend:a | `10701` | `GetPlayHistoryRegistrationKeyWithNetworkServiceAccountId` | — | Q | 2026-11-21 |
| friend:u, friend:v, friend:m, friend:s, friend:a | `10702` | `AddPlayHistory` | — | Q | 2026-11-21 |
| friend:u, friend:v, friend:m, friend:s, friend:a | `11000` | `GetProfileImageUrl` | — | Q | 2026-11-21 |
| friend:u, friend:v, friend:m, friend:s, friend:a | `20100` | `GetFriendCount` | — | Q | 2026-11-21 |
| friend:u, friend:v, friend:m, friend:s, friend:a | `20101` | `GetNewlyFriendCount` | — | Q | 2026-11-21 |
| friend:u, friend:v, friend:m, friend:s, friend:a | `20102` | `GetFriendDetailedInfo` | — | Q | 2026-11-21 |
| friend:u, friend:v, friend:m, friend:s, friend:a | `20103` | `SyncFriendList` | — | Q | 2026-11-21 |
| friend:u, friend:v, friend:m, friend:s, friend:a | `20104` | `RequestSyncFriendList` | — | Q | 2026-11-21 |
| friend:u, friend:v, friend:m, friend:s, friend:a | `20110` | `LoadFriendSetting` | — | Q | 2026-11-21 |
| friend:u, friend:v, friend:m, friend:s, friend:a | `20200` | `GetReceivedFriendRequestCount` | — | Q | 2026-11-21 |
| friend:u, friend:v, friend:m, friend:s, friend:a | `20201` | `GetFriendRequestList` | — | Q | 2026-11-21 |
| friend:u, friend:v, friend:m, friend:s, friend:a | `20300` | `GetFriendCandidateList` | — | Q | 2026-11-21 |
| friend:u, friend:v, friend:m, friend:s, friend:a | `20301` | `GetNintendoNetworkIdInfo` | 3.0.0+ | Q | 2026-11-21 |
| friend:u, friend:v, friend:m, friend:s, friend:a | `20302` | `GetSnsAccountLinkage` | 5.0.0+ | Q | 2026-11-21 |
| friend:u, friend:v, friend:m, friend:s, friend:a | `20303` | `GetSnsAccountProfile` | 5.0.0+ | Q | 2026-11-21 |
| friend:u, friend:v, friend:m, friend:s, friend:a | `20304` | `GetSnsAccountFriendList` | 5.0.0+ | Q | 2026-11-21 |
| friend:u, friend:v, friend:m, friend:s, friend:a | `20400` | `GetBlockedUserList` | — | Q | 2026-11-21 |
| friend:u, friend:v, friend:m, friend:s, friend:a | `20401` | `SyncBlockedUserList` | — | Q | 2026-11-21 |
| friend:u, friend:v, friend:m, friend:s, friend:a | `20500` | `GetProfileExtraList` | — | Q | 2026-11-21 |
| friend:u, friend:v, friend:m, friend:s, friend:a | `20501` | `GetRelationship` | — | Q | 2026-11-21 |
| friend:u, friend:v, friend:m, friend:s, friend:a | `20600` | `GetUserPresenceView` | — | Q | 2026-11-21 |
| friend:u, friend:v, friend:m, friend:s, friend:a | `20700` | `GetPlayHistoryList` | — | Q | 2026-11-21 |
| friend:u, friend:v, friend:m, friend:s, friend:a | `20701` | `GetPlayHistoryStatistics` | — | Q | 2026-11-21 |
| friend:u, friend:v, friend:m, friend:s, friend:a | `20800` | `LoadUserSetting` | — | Q | 2026-11-21 |
| friend:u, friend:v, friend:m, friend:s, friend:a | `20801` | `SyncUserSetting` | — | Q | 2026-11-21 |
| friend:u, friend:v, friend:m, friend:s, friend:a | `20900` | `RequestListSummaryOverlayNotification` | — | Q | 2026-11-21 |
| friend:u, friend:v, friend:m, friend:s, friend:a | `21000` | `GetExternalApplicationCatalog` | — | Q | 2026-11-21 |
| friend:u, friend:v, friend:m, friend:s, friend:a | `22000` | `GetReceivedFriendInvitationList` | 9.0.0+ | Q | 2026-11-21 |
| friend:u, friend:v, friend:m, friend:s, friend:a | `22001` | `GetReceivedFriendInvitationDetailedInfo` | 9.0.0+ | Q | 2026-11-21 |
| friend:u, friend:v, friend:m, friend:s, friend:a | `22010` | `GetReceivedFriendInvitationCountCache` | 9.0.0+ | Q | 2026-11-21 |
| friend:u, friend:v, friend:m, friend:s, friend:a | `30100` | `DropFriendNewlyFlags` | — | Q | 2026-11-21 |
| friend:u, friend:v, friend:m, friend:s, friend:a | `30101` | `DeleteFriend` | — | Q | 2026-11-21 |
| friend:u, friend:v, friend:m, friend:s, friend:a | `30110` | `DropFriendNewlyFlag` | — | Q | 2026-11-21 |
| friend:u, friend:v, friend:m, friend:s, friend:a | `30120` | `ChangeFriendFavoriteFlag` | — | Q | 2026-11-21 |
| friend:u, friend:v, friend:m, friend:s, friend:a | `30121` | `ChangeFriendOnlineNotificationFlag` | — | Q | 2026-11-21 |
| friend:u, friend:v, friend:m, friend:s, friend:a | `30200` | `SendFriendRequest` | — | Q | 2026-11-21 |
| friend:u, friend:v, friend:m, friend:s, friend:a | `30201` | `SendFriendRequestWithApplicationInfo` | — | Q | 2026-11-21 |
| friend:u, friend:v, friend:m, friend:s, friend:a | `30202` | `CancelFriendRequest` | — | Q | 2026-11-21 |
| friend:u, friend:v, friend:m, friend:s, friend:a | `30203` | `AcceptFriendRequest` | — | Q | 2026-11-21 |
| friend:u, friend:v, friend:m, friend:s, friend:a | `30204` | `RejectFriendRequest` | — | Q | 2026-11-21 |
| friend:u, friend:v, friend:m, friend:s, friend:a | `30205` | `ReadFriendRequest` | — | Q | 2026-11-21 |
| friend:u, friend:v, friend:m, friend:s, friend:a | `30210` | `GetFacedFriendRequestRegistrationKey` | — | Q | 2026-11-21 |
| friend:u, friend:v, friend:m, friend:s, friend:a | `30211` | `AddFacedFriendRequest` | — | Q | 2026-11-21 |
| friend:u, friend:v, friend:m, friend:s, friend:a | `30212` | `CancelFacedFriendRequest` | — | Q | 2026-11-21 |
| friend:u, friend:v, friend:m, friend:s, friend:a | `30213` | `GetFacedFriendRequestProfileImage` | — | Q | 2026-11-21 |
| friend:u, friend:v, friend:m, friend:s, friend:a | `30214` | `GetFacedFriendRequestProfileImageFromPath` | — | Q | 2026-11-21 |
| friend:u, friend:v, friend:m, friend:s, friend:a | `30215` | `SendFriendRequestWithExternalApplicationCatalogId` | — | Q | 2026-11-21 |
| friend:u, friend:v, friend:m, friend:s, friend:a | `30216` | `ResendFacedFriendRequest` | — | Q | 2026-11-21 |
| friend:u, friend:v, friend:m, friend:s, friend:a | `30217` | `SendFriendRequestWithNintendoNetworkIdInfo` | 3.0.0+ | Q | 2026-11-21 |
| friend:u, friend:v, friend:m, friend:s, friend:a | `30300` | `GetSnsAccountLinkPageUrl` | 5.0.0+ | Q | 2026-11-21 |
| friend:u, friend:v, friend:m, friend:s, friend:a | `30301` | `UnlinkSnsAccount` | 5.0.0+ | Q | 2026-11-21 |
| friend:u, friend:v, friend:m, friend:s, friend:a | `30400` | `BlockUser` | — | Q | 2026-11-21 |
| friend:u, friend:v, friend:m, friend:s, friend:a | `30401` | `BlockUserWithApplicationInfo` | — | Q | 2026-11-21 |
| friend:u, friend:v, friend:m, friend:s, friend:a | `30402` | `UnblockUser` | — | Q | 2026-11-21 |
| friend:u, friend:v, friend:m, friend:s, friend:a | `30500` | `GetProfileExtraFromFriendCode` | — | Q | 2026-11-21 |
| friend:u, friend:v, friend:m, friend:s, friend:a | `30700` | `DeletePlayHistory` | — | Q | 2026-11-21 |
| friend:u, friend:v, friend:m, friend:s, friend:a | `30810` | `ChangePresencePermission` | — | Q | 2026-11-21 |
| friend:u, friend:v, friend:m, friend:s, friend:a | `30811` | `ChangeFriendRequestReception` | — | Q | 2026-11-21 |
| friend:u, friend:v, friend:m, friend:s, friend:a | `30812` | `ChangePlayLogPermission` | — | Q | 2026-11-21 |
| friend:u, friend:v, friend:m, friend:s, friend:a | `30820` | `IssueFriendCode` | — | Q | 2026-11-21 |
| friend:u, friend:v, friend:m, friend:s, friend:a | `30830` | `ClearPlayLog` | — | Q | 2026-11-21 |
| friend:u, friend:v, friend:m, friend:s, friend:a | `30900` | `SendFriendInvitation` | 9.0.0+ | Q | 2026-11-21 |
| friend:u, friend:v, friend:m, friend:s, friend:a | `30910` | `ReadFriendInvitation` | 9.0.0+ | Q | 2026-11-21 |
| friend:u, friend:v, friend:m, friend:s, friend:a | `49900` | `DeleteNetworkServiceAccountCache` | — | Q | 2026-11-21 |
| friend:u, friend:v, friend:m, friend:s, friend:a | `0` | `GetEvent` | 2.0.0+ | Q | 2026-11-21 |
| friend:u, friend:v, friend:m, friend:s, friend:a | `1` | `Clear` | 2.0.0+ | Q | 2026-11-21 |
| friend:u, friend:v, friend:m, friend:s, friend:a | `2` | `Pop` | 2.0.0+ | Q | 2026-11-21 |
| nd:app | `0` | `GetReceivableNeighborInfoCountMax` | — | Q | 2026-11-21 |
| nd:app | `10` | `IsNeighborDetectionEnabled` | — | Q | 2026-11-21 |
| nd:sys | `0` | `GetReceivableNeighborInfoCountMax` | — | Q | 2026-11-21 |
| nd:sys | `10` | `IsNeighborDetectionEnabled` | — | Q | 2026-11-21 |
| nd:sys | `200` | `SetSystemData` | — | Q | 2026-11-21 |
| nd:sys | `201` | `ClearSystemData` | — | Q | 2026-11-21 |
| nd:sys | `203` | `GetReceivableNeighborInfoCountForSystem` | — | Q | 2026-11-21 |
| nd:sys | `204` | `ReceiveNeighborInfoForSystem` | — | Q | 2026-11-21 |
| nd:sys | `205` | `SetSender` | — | Q | 2026-11-21 |
| nd:sys | `206` | `GetSender` | — | Q | 2026-11-21 |
| nd:sys | `207` | `CreateScannerForSystem` | — | Q | 2026-11-21 |
| nd:sys | `208` | `CreateReceiveEventHolderForSystem` | — | Q | 2026-11-21 |
| nd:sys | `223` | `EnableNeighborDetection` | — | Q | 2026-11-21 |
| nd:sys | `224` | `DisableNeighborDetection` | — | Q | 2026-11-21 |
| nd:sys | `226` | `EnablePowerSave` | — | Q | 2026-11-21 |
| nd:sys | `227` | `DisablePowerSave` | — | Q | 2026-11-21 |
| nd:sys | `228` | `IsPowerSaveEnabled` | — | Q | 2026-11-21 |
| nd:sys | `232` | `ClearBlockedUsers` | — | Q | 2026-11-21 |
| nd:sys | `233` | `GetBlockedUserCount` | — | Q | 2026-11-21 |
| nd:sys | `234` | `BlockUserByLocalUserId` | — | Q | 2026-11-21 |
| nd:sys | `235` | `BlockUserByNetworkUserId` | — | Q | 2026-11-21 |
| nd:sys | `236` | `UnblockUserByLocalUserId` | — | Q | 2026-11-21 |
| nd:sys | `237` | `UnblockUserByNetworkUserId` | — | Q | 2026-11-21 |
| nd:sys | `240` | `DeleteApplication` | — | Q | 2026-11-21 |
| nd:sys | `250` | `InitializeApplicationInfo` | — | Q | 2026-11-21 |
| nd:sys | `260` | `CreateAccountSystemSaveDataAccessSuppressor` | — | Q | 2026-11-21 |
| nd:sys | `300` | `AddReceivedNeighborInfoForSystemForDebug` | — | Q | 2026-11-21 |
| nd:sys | `301` | `GetSendDataForDebug` | — | Q | 2026-11-21 |
| nd:sys | `302` | `ClearReceiveCounterForDebug` | — | Q | 2026-11-21 |
| nd:sys | `303` | `GetNextReceiveCounterForDebug` | — | Q | 2026-11-21 |
| nd:sys | `304` | `ListBlockedUsersForDebug` | — | Q | 2026-11-21 |
| nd:sys | `305` | `RefreshSendDataIdForDebug` | — | Q | 2026-11-21 |
| nd:sys | `306` | `ReloadFwdbgSettingsForDebug` | — | Q | 2026-11-21 |
| nd:sys | `307` | `EnableApplicationForDebug` | — | Q | 2026-11-21 |
| nd:sys | `308` | `GetNextReceiveCountersForDebug` | — | Q | 2026-11-21 |
| nd:sys | `309` | `ListApplicationInfoForDebug` | — | Q | 2026-11-21 |
| nd:sys | `310` | `SetApplicationDataForDebug` | — | Q | 2026-11-21 |
| nd:sys | `400` | `GetNetworkUserId` | — | Q | 2026-11-21 |
| nd:sys | `401` | `DeleteNetworkUserId` | — | Q | 2026-11-21 |

### Filesystem services

[Wiki SwitchBrew](https://switchbrew.org/wiki/Filesystem_services) · [miroir](https://github.com/backupbrew/switchbrew/blob/master/Filesystem%20services.md)

**257 commandes documentées**.

| Interface / section | ID | Fonction | Disponibilité indiquée | Encore | Vérifié |
|---|---|---|---|---|---|
| fsp-ldr | `0` | `OpenCodeFileSystem` | — | Q | 2026-11-21 |
| fsp-ldr | `1` | `IsArchivedProgram` | — | Q | 2026-11-21 |
| fsp-ldr | `2` | `SetCurrentProcess` | 4.0.0+ | Q | 2026-11-21 |
| fsp-pr | `0` | `RegisterProgram` | — | Q | 2026-11-21 |
| fsp-pr | `1` | `UnregisterProgram` | — | Q | 2026-11-21 |
| fsp-pr | `2` | `SetCurrentProcess` | 4.0.0+ | Q | 2026-11-21 |
| fsp-pr | `256` | `SetEnabledProgramVerification` | — | Q | 2026-11-21 |
| fsp-srv | `0` | `OpenFileSystem` | 1.0.0 | Q | 2026-11-21 |
| fsp-srv | `1` | `SetCurrentProcess` | — | Q | 2026-11-21 |
| fsp-srv | `2` | `OpenDataFileSystemByCurrentProcess` | — | Q | 2026-11-21 |
| fsp-srv | `7` | `OpenFileSystemWithPatch` | 2.0.0+ | Q | 2026-11-21 |
| fsp-srv | `8` | `OpenFileSystemWithId` | 2.0.0+ | Q | 2026-11-21 |
| fsp-srv | `9` | `OpenDataFileSystemByProgramId` | 3.0.0+ | Q | 2026-11-21 |
| fsp-srv | `11` | `OpenBisFileSystem` | — | Q | 2026-11-21 |
| fsp-srv | `12` | `OpenBisStorage` | — | Q | 2026-11-21 |
| fsp-srv | `13` | `InvalidateBisCache` | — | Q | 2026-11-21 |
| fsp-srv | `17` | `OpenHostFileSystem` | — | Q | 2026-11-21 |
| fsp-srv | `18` | `OpenSdCardFileSystem` | — | Q | 2026-11-21 |
| fsp-srv | `19` | `FormatSdCardFileSystem` | 2.0.0+ | Q | 2026-11-21 |
| fsp-srv | `21` | `DeleteSaveDataFileSystem` | — | Q | 2026-11-21 |
| fsp-srv | `22` | `CreateSaveDataFileSystem` | — | Q | 2026-11-21 |
| fsp-srv | `23` | `CreateSaveDataFileSystemBySystemSaveDataId` | — | Q | 2026-11-21 |
| fsp-srv | `24` | `RegisterSaveDataFileSystemAtomicDeletion` | — | Q | 2026-11-21 |
| fsp-srv | `25` | `DeleteSaveDataFileSystemBySaveDataSpaceId` | 2.0.0+ | Q | 2026-11-21 |
| fsp-srv | `26` | `FormatSdCardDryRun` | 2.0.0+ | Q | 2026-11-21 |
| fsp-srv | `27` | `IsExFatSupported` | 2.0.0+ | Q | 2026-11-21 |
| fsp-srv | `28` | `DeleteSaveDataFileSystemBySaveDataAttribute` | 4.0.0+ | Q | 2026-11-21 |
| fsp-srv | `30` | `OpenGameCardStorage` | — | Q | 2026-11-21 |
| fsp-srv | `31` | `OpenGameCardFileSystem` | — | Q | 2026-11-21 |
| fsp-srv | `32` | `ExtendSaveDataFileSystem` | 3.0.0+ | Q | 2026-11-21 |
| fsp-srv | `33` | `DeleteCacheStorage` | 5.0.0+ | Q | 2026-11-21 |
| fsp-srv | `34` | `GetCacheStorageSize` | 5.0.0+ | Q | 2026-11-21 |
| fsp-srv | `35` | `CreateSaveDataFileSystemWithHashSalt` | 6.0.0+ | Q | 2026-11-21 |
| fsp-srv | `36` | `OpenHostFileSystemWithOption` | 9.0.0+ | Q | 2026-11-21 |
| fsp-srv | `51` | `OpenSaveDataFileSystem` | — | Q | 2026-11-21 |
| fsp-srv | `52` | `OpenSaveDataFileSystemBySystemSaveDataId` | — | Q | 2026-11-21 |
| fsp-srv | `53` | `OpenReadOnlySaveDataFileSystem` | 2.0.0+ | Q | 2026-11-21 |
| fsp-srv | `57` | `ReadSaveDataFileSystemExtraDataBySaveDataSpaceId` | 3.0.0+ | Q | 2026-11-21 |
| fsp-srv | `58` | `ReadSaveDataFileSystemExtraData` | — | Q | 2026-11-21 |
| fsp-srv | `59` | `WriteSaveDataFileSystemExtraData` | 2.0.0+ | Q | 2026-11-21 |
| fsp-srv | `60` | `OpenSaveDataInfoReader` | — | Q | 2026-11-21 |
| fsp-srv | `61` | `OpenSaveDataInfoReaderBySaveDataSpaceId` | — | Q | 2026-11-21 |
| fsp-srv | `62` | `OpenSaveDataInfoReaderOnlyCacheStorage` | 5.0.0+ | Q | 2026-11-21 |
| fsp-srv | `64` | `OpenSaveDataInternalStorageFileSystem` | 5.0.0+ | Q | 2026-11-21 |
| fsp-srv | `65` | `UpdateSaveDataMacForDebug` | 5.0.0+ | Q | 2026-11-21 |
| fsp-srv | `66` | `WriteSaveDataFileSystemExtraDataWithMask` | 5.0.0+ | Q | 2026-11-21 |
| fsp-srv | `67` | `FindSaveDataWithFilter` | 6.0.0+ | Q | 2026-11-21 |
| fsp-srv | `68` | `OpenSaveDataInfoReaderWithFilter` | 6.0.0+ | Q | 2026-11-21 |
| fsp-srv | `69` | `ReadSaveDataFileSystemExtraDataBySaveDataAttribute` | 8.0.0+ | Q | 2026-11-21 |
| fsp-srv | `70` | `WriteSaveDataFileSystemExtraDataBySaveDataAttribute` | 8.0.0+ | Q | 2026-11-21 |
| fsp-srv | `80` | `OpenSaveDataMetaFile` | — | Q | 2026-11-21 |
| fsp-srv | `81` | `OpenSaveDataTransferManager` | 4.0.0+ | Q | 2026-11-21 |
| fsp-srv | `82` | `OpenSaveDataTransferManagerVersion2` | 5.0.0+ | Q | 2026-11-21 |
| fsp-srv | `83` | `OpenSaveDataTransferProhibiter` | 6.0.0+ | Q | 2026-11-21 |
| fsp-srv | `84` | `ListAccessibleSaveDataOwnerId` | 6.0.0+ | Q | 2026-11-21 |
| fsp-srv | `85` | `OpenSaveDataTransferManagerForSaveDataRepair` | 9.0.0+ | Q | 2026-11-21 |
| fsp-srv | `100` | `OpenImageDirectoryFileSystem` | — | Q | 2026-11-21 |
| fsp-srv | `110` | `OpenContentStorageFileSystem` | — | Q | 2026-11-21 |
| fsp-srv | `120` | `OpenCloudBackupWorkStorageFileSystem` | 6.0.0+ | Q | 2026-11-21 |
| fsp-srv | `130` | `OpenCustomStorageFileSystem` | 7.0.0+ | Q | 2026-11-21 |
| fsp-srv | `200` | `OpenDataStorageByCurrentProcess` | — | Q | 2026-11-21 |
| fsp-srv | `201` | `OpenDataStorageByProgramId` | 3.0.0+ | Q | 2026-11-21 |
| fsp-srv | `202` | `OpenDataStorageByDataId` | — | Q | 2026-11-21 |
| fsp-srv | `203` | `OpenPatchDataStorageByCurrentProcess` | — | Q | 2026-11-21 |
| fsp-srv | `204` | `OpenDataFileSystemWithProgramIndex` | 7.0.0+ | Q | 2026-11-21 |
| fsp-srv | `205` | `OpenDataStorageWithProgramIndex` | 7.0.0+ | Q | 2026-11-21 |
| fsp-srv | `400` | `OpenDeviceOperator` | — | Q | 2026-11-21 |
| fsp-srv | `500` | `OpenSdCardDetectionEventNotifier` | — | Q | 2026-11-21 |
| fsp-srv | `501` | `OpenGameCardDetectionEventNotifier` | — | Q | 2026-11-21 |
| fsp-srv | `510` | `OpenSystemDataUpdateEventNotifier` | 5.0.0+ | Q | 2026-11-21 |
| fsp-srv | `511` | `NotifySystemDataUpdateEvent` | 5.0.0+ | Q | 2026-11-21 |
| fsp-srv | `520` | `SimulateDeviceDetectionEvent` | 6.0.0+ | Q | 2026-11-21 |
| fsp-srv | `600` | `SetCurrentPosixTime` | 1.0.0-3.0.2 | Q | 2026-11-21 |
| fsp-srv | `601` | `QuerySaveDataTotalSize` | — | Q | 2026-11-21 |
| fsp-srv | `602` | `VerifySaveDataFileSystem` | — | Q | 2026-11-21 |
| fsp-srv | `603` | `CorruptSaveDataFileSystem` | — | Q | 2026-11-21 |
| fsp-srv | `604` | `CreatePaddingFile` | — | Q | 2026-11-21 |
| fsp-srv | `605` | `DeleteAllPaddingFiles` | — | Q | 2026-11-21 |
| fsp-srv | `606` | `GetRightsId` | 2.0.0+ | Q | 2026-11-21 |
| fsp-srv | `607` | `RegisterExternalKey` | 2.0.0+ | Q | 2026-11-21 |
| fsp-srv | `608` | `UnregisterAllExternalKey` | 2.0.0+ | Q | 2026-11-21 |
| fsp-srv | `609` | `GetRightsIdByPath` | 2.0.0+ | Q | 2026-11-21 |
| fsp-srv | `610` | `GetRightsIdAndKeyGenerationByPath` | 3.0.0+ | Q | 2026-11-21 |
| fsp-srv | `611` | `SetCurrentPosixTimeWithTimeDifference` | 4.0.0+ | Q | 2026-11-21 |
| fsp-srv | `612` | `GetFreeSpaceSizeForSaveData` | 4.0.0+ | Q | 2026-11-21 |
| fsp-srv | `613` | `VerifySaveDataFileSystemBySaveDataSpaceId` | 4.0.0+ | Q | 2026-11-21 |
| fsp-srv | `614` | `CorruptSaveDataFileSystemBySaveDataSpaceId` | 4.0.0+ | Q | 2026-11-21 |
| fsp-srv | `615` | `QuerySaveDataInternalStorageTotalSize` | 5.0.0+ | Q | 2026-11-21 |
| fsp-srv | `616` | `GetSaveDataCommitId` | 6.0.0+ | Q | 2026-11-21 |
| fsp-srv | `617` | `UnregisterExternalKey` | 7.0.0+ | Q | 2026-11-21 |
| fsp-srv | `620` | `SetSdCardEncryptionSeed` | 2.0.0+ | Q | 2026-11-21 |
| fsp-srv | `630` | `SetSdCardAccessibility` | 4.0.0+ | Q | 2026-11-21 |
| fsp-srv | `631` | `IsSdCardAccessible` | 4.0.0+ | Q | 2026-11-21 |
| fsp-srv | `640` | `IsSignedSystemPartitionOnSdCardValid` | 4.0.0-7.0.1 | Q | 2026-11-21 |
| fsp-srv | `700` | `OpenAccessFailureDetectionEventNotifier` | 5.0.0+ | Q | 2026-11-21 |
| fsp-srv | `701` | `GetAccessFailureDetectionEvent` | 5.0.0+ | Q | 2026-11-21 |
| fsp-srv | `702` | `IsAccessFailureDetected` | 5.0.0+ | Q | 2026-11-21 |
| fsp-srv | `710` | `ResolveAccessFailure` | 5.0.0+ | Q | 2026-11-21 |
| fsp-srv | `720` | `AbandonAccessFailure` | 5.0.0+ | Q | 2026-11-21 |
| fsp-srv | `800` | `GetAndClearErrorInfo` | 2.0.0+ | Q | 2026-11-21 |
| fsp-srv | `810` | `RegisterProgramIndexMapInfo` | 7.0.0+ | Q | 2026-11-21 |
| fsp-srv | `1000` | `SetBisRootForHost` | — | Q | 2026-11-21 |
| fsp-srv | `1001` | `SetSaveDataSize` | — | Q | 2026-11-21 |
| fsp-srv | `1002` | `SetSaveDataRootPath` | — | Q | 2026-11-21 |
| fsp-srv | `1003` | `DisableAutoSaveDataCreation` | — | Q | 2026-11-21 |
| fsp-srv | `1004` | `SetGlobalAccessLogMode` | — | Q | 2026-11-21 |
| fsp-srv | `1005` | `GetGlobalAccessLogMode` | — | Q | 2026-11-21 |
| fsp-srv | `1006` | `OutputAccessLogToSdCard` | — | Q | 2026-11-21 |
| fsp-srv | `1007` | `RegisterUpdatePartition` | 4.0.0+ | Q | 2026-11-21 |
| fsp-srv | `1008` | `OpenRegisteredUpdatePartition` | 4.0.0+ | Q | 2026-11-21 |
| fsp-srv | `1009` | `GetAndClearMemoryReportInfo` | 4.0.0+ | Q | 2026-11-21 |
| fsp-srv | `1010` | `SetDataStorageRedirectTarget` | 5.1.0-6.2.0 | Q | 2026-11-21 |
| fsp-srv | `1011` | `GetProgramIndexForAccessLog` | 7.0.0+ | Q | 2026-11-21 |
| fsp-srv | `1012` | `GetFsStackUsage` | 9.0.0+ | Q | 2026-11-21 |
| fsp-srv | `1013` | `UnsetSaveDataRootPath` | 9.0.0+ | Q | 2026-11-21 |
| fsp-srv | `1100` | `OverrideSaveDataTransferTokenSignVerificationKey` | 4.0.0+ | Q | 2026-11-21 |
| fsp-srv | `1110` | `CorruptSaveDataFileSystemByOffset` | 6.0.0+ | Q | 2026-11-21 |
| fsp-srv | `1200` | `OpenMultiCommitManager` | 6.0.0+ | Q | 2026-11-21 |
| IStorage | `0` | `Read` | — | Q | 2026-11-21 |
| IStorage | `1` | `Write` | — | Q | 2026-11-21 |
| IStorage | `2` | `Flush` | — | Q | 2026-11-21 |
| IStorage | `3` | `SetSize` | — | Q | 2026-11-21 |
| IStorage | `4` | `GetSize` | — | Q | 2026-11-21 |
| IStorage | `5` | `OperateRange` | 4.0.0+ | Q | 2026-11-21 |
| IFileSystem | `0` | `CreateFile` | — | Q | 2026-11-21 |
| IFileSystem | `1` | `DeleteFile` | — | Q | 2026-11-21 |
| IFileSystem | `2` | `CreateDirectory` | — | Q | 2026-11-21 |
| IFileSystem | `3` | `DeleteDirectory` | — | Q | 2026-11-21 |
| IFileSystem | `4` | `DeleteDirectoryRecursively` | — | Q | 2026-11-21 |
| IFileSystem | `5` | `RenameFile` | — | Q | 2026-11-21 |
| IFileSystem | `6` | `RenameDirectory` | — | Q | 2026-11-21 |
| IFileSystem | `7` | `GetEntryType` | — | Q | 2026-11-21 |
| IFileSystem | `8` | `OpenFile` | — | Q | 2026-11-21 |
| IFileSystem | `9` | `OpenDirectory` | — | Q | 2026-11-21 |
| IFileSystem | `10` | `Commit` | — | Q | 2026-11-21 |
| IFileSystem | `11` | `GetFreeSpaceSize` | — | Q | 2026-11-21 |
| IFileSystem | `12` | `GetTotalSpaceSize` | — | Q | 2026-11-21 |
| IFileSystem | `13` | `CleanDirectoryRecursively` | 3.0.0+ | Q | 2026-11-21 |
| IFileSystem | `14` | `GetFileTimeStampRaw` | 3.0.0+ | Q | 2026-11-21 |
| IFileSystem | `15` | `QueryEntry` | 4.0.0+ | Q | 2026-11-21 |
| IDirectory | `0` | `Read` | — | Q | 2026-11-21 |
| IDirectory | `1` | `GetEntryCount` | — | Q | 2026-11-21 |
| IFile | `0` | `Read` | — | Q | 2026-11-21 |
| IFile | `1` | `Write` | — | Q | 2026-11-21 |
| IFile | `2` | `Flush` | — | Q | 2026-11-21 |
| IFile | `3` | `SetSize` | — | Q | 2026-11-21 |
| IFile | `4` | `GetSize` | — | Q | 2026-11-21 |
| IFile | `5` | `OperateRange` | 4.0.0+ | Q | 2026-11-21 |
| ISaveDataInfoReader | `0` | `ReadSaveDataInfo` | — | Q | 2026-11-21 |
| IDeviceOperator | `0` | `IsSdCardInserted` | — | Q | 2026-11-21 |
| IDeviceOperator | `1` | `GetSdCardSpeedMode` | — | Q | 2026-11-21 |
| IDeviceOperator | `2` | `GetSdCardCid` | 2.0.0+ | Q | 2026-11-21 |
| IDeviceOperator | `3` | `GetSdCardUserAreaSize` | 2.0.0+ | Q | 2026-11-21 |
| IDeviceOperator | `4` | `GetSdCardProtectedAreaSize` | 2.0.0+ | Q | 2026-11-21 |
| IDeviceOperator | `5` | `GetAndClearSdCardErrorInfo` | 2.0.0+ | Q | 2026-11-21 |
| IDeviceOperator | `100` | `GetMmcCid` | — | Q | 2026-11-21 |
| IDeviceOperator | `101` | `GetMmcSpeedMode` | — | Q | 2026-11-21 |
| IDeviceOperator | `110` | `EraseMmc` | — | Q | 2026-11-21 |
| IDeviceOperator | `111` | `GetMmcPartitionSize` | — | Q | 2026-11-21 |
| IDeviceOperator | `112` | `GetMmcPatrolCount` | 2.0.0+ | Q | 2026-11-21 |
| IDeviceOperator | `113` | `GetAndClearMmcErrorInfo` | 2.0.0+ | Q | 2026-11-21 |
| IDeviceOperator | `114` | `GetMmcExtendedCsd` | 2.0.0+ | Q | 2026-11-21 |
| IDeviceOperator | `115` | `SuspendMmcPatrol` | 4.0.0+ | Q | 2026-11-21 |
| IDeviceOperator | `116` | `ResumeMmcPatrol` | 4.0.0+ | Q | 2026-11-21 |
| IDeviceOperator | `200` | `IsGameCardInserted` | — | Q | 2026-11-21 |
| IDeviceOperator | `201` | `EraseGameCard` | — | Q | 2026-11-21 |
| IDeviceOperator | `202` | `GetGameCardHandle` | — | Q | 2026-11-21 |
| IDeviceOperator | `203` | `GetGameCardUpdatePartitionInfo` | — | Q | 2026-11-21 |
| IDeviceOperator | `204` | `FinalizeGameCardDriver` | — | Q | 2026-11-21 |
| IDeviceOperator | `205` | `GetGameCardAttribute` | — | Q | 2026-11-21 |
| IDeviceOperator | `206` | `GetGameCardDeviceCertificate` | — | Q | 2026-11-21 |
| IDeviceOperator | `207` | `GetGameCardAsicInfo` | — | Q | 2026-11-21 |
| IDeviceOperator | `208` | `GetGameCardIdSet` | — | Q | 2026-11-21 |
| IDeviceOperator | `209` | `WriteToGameCardDirectly` | — | Q | 2026-11-21 |
| IDeviceOperator | `210` | `SetVerifyWriteEnalbleFlag` | — | Q | 2026-11-21 |
| IDeviceOperator | `211` | `GetGameCardImageHash` | — | Q | 2026-11-21 |
| IDeviceOperator | `212` | `GetGameCardDeviceIdForProdCard` | 2.0.0+ | Q | 2026-11-21 |
| IDeviceOperator | `213` | `EraseAndWriteParamDirectly` | 2.0.0+ | Q | 2026-11-21 |
| IDeviceOperator | `214` | `ReadParamDirectly` | 2.0.0+ | Q | 2026-11-21 |
| IDeviceOperator | `215` | `ForceEraseGameCard` | 2.0.0+ | Q | 2026-11-21 |
| IDeviceOperator | `216` | `GetGameCardErrorInfo` | 2.0.0+ | Q | 2026-11-21 |
| IDeviceOperator | `217` | `GetGameCardErrorReportInfo` | 2.1.0+ | Q | 2026-11-21 |
| IDeviceOperator | `218` | `GetGameCardDeviceId` | 3.0.0+ | Q | 2026-11-21 |
| IDeviceOperator | `219` | `ChallengeCardExistence` | 8.0.0+ | Q | 2026-11-21 |
| IDeviceOperator | `220` | `GetGameCardCompatibilityType` | 9.0.0+ | Q | 2026-11-21 |
| IDeviceOperator | `300` | `SetSpeedEmulationMode` | — | Q | 2026-11-21 |
| IDeviceOperator | `301` | `GetSpeedEmulationMode` | — | Q | 2026-11-21 |
| IDeviceOperator | `400` | `SuspendSdmmcControl` | 5.0.0+ | Q | 2026-11-21 |
| IDeviceOperator | `401` | `ResumeSdmmcControl` | 5.0.0+ | Q | 2026-11-21 |
| IDeviceOperator | `402` | `GetSdmmcConnectionStatus` | 6.0.0+ | Q | 2026-11-21 |
| IDeviceOperator | `500` | `SetDeviceSimulationEvent` | 6.0.0+ | Q | 2026-11-21 |
| IDeviceOperator | `501` | `ClearDeviceSimulationEvent` | 6.0.0+ | Q | 2026-11-21 |
| IEventNotifier | `0` | `GetEventHandle` | — | Q | 2026-11-21 |
| ISaveDataTransferManager | `0` | `GetChallenge` | — | Q | 2026-11-21 |
| ISaveDataTransferManager | `16` | `SetToken` | — | Q | 2026-11-21 |
| ISaveDataTransferManager | `32` | `OpenSaveDataExporter` | — | Q | 2026-11-21 |
| ISaveDataTransferManager | `64` | `OpenSaveDataImporter` | — | Q | 2026-11-21 |
| ISaveDataTransferManagerForSaveDataRepair | `0` | `GetChallenge` | — | Q | 2026-11-21 |
| ISaveDataTransferManagerForSaveDataRepair | `16` | `SetKeyPackage` | — | Q | 2026-11-21 |
| ISaveDataTransferManagerForSaveDataRepair | `80` | `OpenSaveDataExporterAndGetEncryptedKey` | — | Q | 2026-11-21 |
| ISaveDataTransferManagerForSaveDataRepair | `81` | `PrepareOpenSaveDataImporter` | — | Q | 2026-11-21 |
| ISaveDataTransferManagerForSaveDataRepair | `90` | `OpenSaveDataImporter` | — | Q | 2026-11-21 |
| ISaveDataTransferManagerForSaveDataRepair | `91` | `OpenSaveDataImporter2` | — | Q | 2026-11-21 |
| ISaveDataTransferManagerForSaveDataRepair | `100` | `OpenSaveDataExporterWithKey` | — | Q | 2026-11-21 |
| ISaveDataTransferManagerForSaveDataRepair | `110` | `OpenSaveDataImporterWithKey` | — | Q | 2026-11-21 |
| ISaveDataExporter | `0` | `GetSaveDataInfo` | — | Q | 2026-11-21 |
| ISaveDataExporter | `1` | `GetRestSize` | — | Q | 2026-11-21 |
| ISaveDataExporter | `16` | `Pull` | — | Q | 2026-11-21 |
| ISaveDataExporter | `17` | `PullInitialData` | — | Q | 2026-11-21 |
| ISaveDataImporter | `0` | `GetSaveDataInfo` | — | Q | 2026-11-21 |
| ISaveDataImporter | `1` | `GetRestSize` | — | Q | 2026-11-21 |
| ISaveDataImporter | `16` | `Push` | — | Q | 2026-11-21 |
| ISaveDataImporter | `17` | `Finalize` | — | Q | 2026-11-21 |
| ISaveDataTransferManagerWithDivision | `0` | `GetChallenge` | — | Q | 2026-11-21 |
| ISaveDataTransferManagerWithDivision | `16` | `SetKeySeedPackage` | — | Q | 2026-11-21 |
| ISaveDataTransferManagerWithDivision | `32` | `OpenSaveDataExporter` | — | Q | 2026-11-21 |
| ISaveDataTransferManagerWithDivision | `33` | `OpenSaveDataExporterForDiffExport` | — | Q | 2026-11-21 |
| ISaveDataTransferManagerWithDivision | `34` | `OpenSaveDataExporterByContext` | 6.0.0+ | Q | 2026-11-21 |
| ISaveDataTransferManagerWithDivision | `64` | `OpenSaveDataImporter` | 5.0.0-5.1.0 | Q | 2026-11-21 |
| ISaveDataTransferManagerWithDivision | `65` | `OpenSaveDataImporterForDiffImport` | — | Q | 2026-11-21 |
| ISaveDataTransferManagerWithDivision | `66` | `OpenSaveDataImporterForDuplicateDiffImport` | 6.0.0+ | Q | 2026-11-21 |
| ISaveDataTransferManagerWithDivision | `67` | `OpenSaveDataImporter` | 6.0.0+ | Q | 2026-11-21 |
| ISaveDataTransferManagerWithDivision | `68` | `OpenSaveDataImporterByContext` | 6.0.0+ | Q | 2026-11-21 |
| ISaveDataTransferManagerWithDivision | `69` | `CancelSuspendingImport` | 6.0.0+ | Q | 2026-11-21 |
| ISaveDataDivisionExporter | `0` | `SetDivisionCount` | — | Q | 2026-11-21 |
| ISaveDataDivisionExporter | `1` | `GetSaveDataInfo` | 6.0.0+ | Q | 2026-11-21 |
| ISaveDataDivisionExporter | `16` | `OpenSaveDataDiffChunkIterator` | — | Q | 2026-11-21 |
| ISaveDataDivisionExporter | `48` | `OpenSaveDataChunkExporter` | — | Q | 2026-11-21 |
| ISaveDataDivisionExporter | `64` | `FinalizeFullExport` | 6.0.0-8.1.0 | Q | 2026-11-21 |
| ISaveDataDivisionExporter | `65` | `FinalizeDiffExport` | 6.0.0-8.1.0 | Q | 2026-11-21 |
| ISaveDataDivisionExporter | `66` | `CancelExport` | 6.0.0+ | Q | 2026-11-21 |
| ISaveDataDivisionExporter | `67` | `SuspendExport` | 6.0.0+ | Q | 2026-11-21 |
| ISaveDataDivisionExporter | `70` | `GetKeySeed` | 6.0.0+ | Q | 2026-11-21 |
| ISaveDataDivisionExporter | `71` | `GetInitialDataMac` | 6.0.0+ | Q | 2026-11-21 |
| ISaveDataDivisionExporter | `72` | `FinalizeExport` | 6.0.0+ | Q | 2026-11-21 |
| ISaveDataDivisionExporter | `73` | `GetInitialDataMacKeyGeneration` | 9.0.0+ | Q | 2026-11-21 |
| ISaveDataDivisionExporter | `80` | `GetImportInitialDataAad` | 6.0.0+ | Q | 2026-11-21 |
| ISaveDataDivisionExporter | `81` | `SetExportInitialDataAad` | 6.0.0+ | Q | 2026-11-21 |
| ISaveDataDivisionExporter | `96` | `GetReportInfo` | 6.0.0+ | Q | 2026-11-21 |
| ISaveDataDivisionImporter | `0` | `GetSaveDataInfo` | 6.0.0+ | Q | 2026-11-21 |
| ISaveDataDivisionImporter | `16` | `OpenSaveDataDiffChunkIterator` | — | Q | 2026-11-21 |
| ISaveDataDivisionImporter | `32` | `InitializeImport` | — | Q | 2026-11-21 |
| ISaveDataDivisionImporter | `33` | `FinalizeImport` | — | Q | 2026-11-21 |
| ISaveDataDivisionImporter | `34` | `CancelImport` | 6.0.0+ | Q | 2026-11-21 |
| ISaveDataDivisionImporter | `35` | `GetImportContext` | 6.0.0+ | Q | 2026-11-21 |
| ISaveDataDivisionImporter | `36` | `SuspendImport` | 6.0.0+ | Q | 2026-11-21 |
| ISaveDataDivisionImporter | `48` | `OpenSaveDataChunkImporter` | — | Q | 2026-11-21 |
| ISaveDataDivisionImporter | `64` | `GetImportInitialDataAad` | 6.0.0+ | Q | 2026-11-21 |
| ISaveDataDivisionImporter | `80` | `GetReportInfo` | 6.0.0+ | Q | 2026-11-21 |
| ISaveDataChunkIterator | `0` | `Next` | — | Q | 2026-11-21 |
| ISaveDataChunkIterator | `1` | `IsEnd` | — | Q | 2026-11-21 |
| ISaveDataChunkIterator | `16` | `GetId` | — | Q | 2026-11-21 |
| ISaveDataChunkExporter | `0` | `Pull` | — | Q | 2026-11-21 |
| ISaveDataChunkExporter | `16` | `GetRestRawDataSize` | 6.0.0+ | Q | 2026-11-21 |
| ISaveDataChunkImporter | `0` | `Push` | — | Q | 2026-11-21 |
| IMultiCommitManager | `1` | `Add` | — | Q | 2026-11-21 |
| IMultiCommitManager | `2` | `Commit` | — | Q | 2026-11-21 |

### Bus services

[Wiki SwitchBrew](https://switchbrew.org/wiki/Bus_services) · [miroir](https://github.com/backupbrew/switchbrew/blob/master/Bus%20services.md)

**66 commandes documentées**.

| Interface / section | ID | Fonction | Disponibilité indiquée | Encore | Vérifié |
|---|---|---|---|---|---|
| gpio | `0` | `OpenSessionForDev` | — | Q | 2026-11-21 |
| gpio | `1` | `OpenSession` | — | Q | 2026-11-21 |
| gpio | `2` | `OpenSessionForTest` | — | Q | 2026-11-21 |
| gpio | `3` | `IsWakeEventActive` | 1.0.0-6.2.0 | Q | 2026-11-21 |
| gpio | `4` | `GetWakeEventActiveFlagSet` | 1.0.0-6.2.0 | Q | 2026-11-21 |
| gpio | `5` | `SetWakeEventActiveFlagSetForDebug` | 1.0.0-6.2.0 | Q | 2026-11-21 |
| gpio | `6` | `SetWakePinDebugMode` | — | Q | 2026-11-21 |
| gpio | `7` | `OpenSession2` | 5.0.0+ | Q | 2026-11-21 |
| gpio | `8` | `IsWakeEventActive2` | 5.0.0+ | Q | 2026-11-21 |
| gpio | `9` | `SetWakeEventActiveFlagSetForDebug2` | 5.0.0+ | Q | 2026-11-21 |
| gpio | `0` | `SetDirection` | — | Q | 2026-11-21 |
| gpio | `1` | `GetDirection` | — | Q | 2026-11-21 |
| gpio | `2` | `SetInterruptMode` | — | Q | 2026-11-21 |
| gpio | `3` | `GetInterruptMode` | — | Q | 2026-11-21 |
| gpio | `4` | `SetInterruptEnable` | — | Q | 2026-11-21 |
| gpio | `5` | `GetInterruptEnable` | — | Q | 2026-11-21 |
| gpio | `6` | `GetInterruptStatus` | — | Q | 2026-11-21 |
| gpio | `7` | `ClearInterruptStatus` | — | Q | 2026-11-21 |
| gpio | `8` | `SetValue` | — | Q | 2026-11-21 |
| gpio | `9` | `GetValue` | — | Q | 2026-11-21 |
| gpio | `10` | `BindInterrupt` | — | Q | 2026-11-21 |
| gpio | `11` | `UnbindInterrupt` | — | Q | 2026-11-21 |
| gpio | `12` | `SetDebounceEnabled` | — | Q | 2026-11-21 |
| gpio | `13` | `GetDebounceEnabled` | — | Q | 2026-11-21 |
| gpio | `14` | `SetDebounceTime` | — | Q | 2026-11-21 |
| gpio | `15` | `GetDebounceTime` | — | Q | 2026-11-21 |
| gpio | `16` | `SetValueForSleepState` | 4.0.0+ | Q | 2026-11-21 |
| gpio | `17` | `GetValueForSleepState` | 6.0.0+ | Q | 2026-11-21 |
| i2c, i2c:pcv | `0` | `[OpenSessionForDev](#OpenSessionForDev_2 "wikilink")` | — | Q | 2026-11-21 |
| i2c, i2c:pcv | `1` | `[OpenSession](#OpenSession_2 "wikilink")` | — | Q | 2026-11-21 |
| i2c, i2c:pcv | `4` | `[OpenSession2](#OpenSession2_2 "wikilink")` | 6.0.0+ | Q | 2026-11-21 |
| i2c, i2c:pcv | `10` | `SendAuto` | — | Q | 2026-11-21 |
| i2c, i2c:pcv | `11` | `ReceiveAuto` | — | Q | 2026-11-21 |
| i2c, i2c:pcv | `12` | `ExecuteCommandListAuto` | — | Q | 2026-11-21 |
| uart | `0` | `DoesUartExist` | — | Q | 2026-11-21 |
| uart | `1` | `DoesUartExistForTest` | — | Q | 2026-11-21 |
| uart | `2` | `IsUartBaudrateValid` | — | Q | 2026-11-21 |
| uart | `3` | `IsUartBaudrateValidForTest` | — | Q | 2026-11-21 |
| uart | `4` | `IsSomethingUartValid` | — | Q | 2026-11-21 |
| uart | `5` | `IsSomethingUartValidForTest` | — | Q | 2026-11-21 |
| uart | `6` | `GetSession` | — | Q | 2026-11-21 |
| uart | `7` | `IsSomethingUartValid2` | — | Q | 2026-11-21 |
| uart | `8` | `IsSomethingUartValid2ForTest` | — | Q | 2026-11-21 |
| uart | `9` | `IsSomethingUartValid3` | 7.0.0+ | Q | 2026-11-21 |
| uart | `10` | `IsSomethingUartValid3ForTest` | 7.0.0+ | Q | 2026-11-21 |
| uart | `0` | `OpenSession` | — | Q | 2026-11-21 |
| uart | `1` | `OpenSessionForTest` | — | Q | 2026-11-21 |
| pwm | `0` | `OpenSessionForDev` | — | Q | 2026-11-21 |
| pwm | `1` | `OpenSession` | — | Q | 2026-11-21 |
| pwm | `2` | `OpenSession2` | 6.0.0+ | Q | 2026-11-21 |
| pwm | `0` | `SetPeriod` | — | Q | 2026-11-21 |
| pwm | `1` | `GetPeriod` | — | Q | 2026-11-21 |
| pwm | `2` | `SetDuty` | — | Q | 2026-11-21 |
| pwm | `3` | `GetDuty` | — | Q | 2026-11-21 |
| pwm | `4` | `SetEnabled` | — | Q | 2026-11-21 |
| pwm | `5` | `GetEnabled` | — | Q | 2026-11-21 |
| pinmux | `0` | `OpenSession` | — | Q | 2026-11-21 |
| pinmux | `0` | `SetPinAssignment` | — | Q | 2026-11-21 |
| pinmux | `1` | `GetPinAssignment` | — | Q | 2026-11-21 |
| pinmux | `2` | `SetPinAssignmentForHardwareTest` | — | Q | 2026-11-21 |
| sasbus | `0` | `OpenSession` | — | Q | 2026-11-21 |
| sasbus | `0` | `Write` | — | Q | 2026-11-21 |
| sasbus | `1` | `Read` | — | Q | 2026-11-21 |
| sasbus | `2` | `StartPeriodicReceiveMode` | — | Q | 2026-11-21 |
| sasbus | `3` | `StopPeriodicReceiveMode` | — | Q | 2026-11-21 |
| led | `0` | `OpenController` | — | Q | 2026-11-21 |

### TMA services

[Wiki SwitchBrew](https://switchbrew.org/wiki/TMA_services) · [miroir](https://github.com/backupbrew/switchbrew/blob/master/TMA%20services.md)

**68 commandes documentées**.

| Interface / section | ID | Fonction | Disponibilité indiquée | Encore | Vérifié |
|---|---|---|---|---|---|
| htc | `0` | `GetEnvironmentVariable` | — | Q | 2026-11-21 |
| htc | `1` | `GetEnvironmentVariableLength` | — | Q | 2026-11-21 |
| htc | `2` | `BindHostConnectionEvent` | — | Q | 2026-11-21 |
| htc | `3` | `BindHostDisconnectionEvent` | — | Q | 2026-11-21 |
| htc | `4` | `BindHostConnectionEventForSystem` | — | Q | 2026-11-21 |
| htc | `5` | `BindHostDisconnectionEventForSystem` | — | Q | 2026-11-21 |
| htc | `6` | `GetBridgeIpAddress` | 3.0.0+ | Q | 2026-11-21 |
| htc | `7` | `GetBridgePort` | 3.0.0+ | Q | 2026-11-21 |
| htc | `8` | `SetCradleAttached` | 3.0.0+ | Q | 2026-11-21 |
| htc | `9` | `GetBridgeSubnetMask` | 4.0.0+ | Q | 2026-11-21 |
| htc | `10` | `GetBridgeMacAddress` | 4.0.0+ | Q | 2026-11-21 |
| htc | `11` | `GetWorkingDirectoryPath` | 6.0.0+ | Q | 2026-11-21 |
| htc | `12` | `GetWorkingDirectoryPathSize` | 6.0.0+ | Q | 2026-11-21 |
| htc | `13` | `RunOnHostStart` | 6.0.0+ | Q | 2026-11-21 |
| htc | `14` | `RunOnHostResults` | 9.0.0+ | Q | 2026-11-21 |
| htcs | `0` | `Socket` | — | Q | 2026-11-21 |
| htcs | `1` | `Close` | — | Q | 2026-11-21 |
| htcs | `2` | `Connect` | — | Q | 2026-11-21 |
| htcs | `3` | `Bind` | — | Q | 2026-11-21 |
| htcs | `4` | `Listen` | — | Q | 2026-11-21 |
| htcs | `5` | `Accept` | — | Q | 2026-11-21 |
| htcs | `6` | `Recv` | — | Q | 2026-11-21 |
| htcs | `7` | `Send` | — | Q | 2026-11-21 |
| htcs | `8` | `Shutdown` | — | Q | 2026-11-21 |
| htcs | `9` | `Fcntl` | — | Q | 2026-11-21 |
| htcs | `10` | `GetPeerNameAny` | — | Q | 2026-11-21 |
| htcs | `11` | `GetDefaultHostName` | — | Q | 2026-11-21 |
| htcs | `12` | `CreateSocketOld` | — | Q | 2026-11-21 |
| htcs | `13` | `CreateSocket` | — | Q | 2026-11-21 |
| htcs | `100` | `RegisterProcessId` | — | Q | 2026-11-21 |
| htcs | `101` | `MonitorManager` | — | Q | 2026-11-21 |
| htcs | `0` | `Close` | — | Q | 2026-11-21 |
| htcs | `1` | `Connect` | — | Q | 2026-11-21 |
| htcs | `2` | `Bind` | — | Q | 2026-11-21 |
| htcs | `3` | `Listen` | — | Q | 2026-11-21 |
| htcs | `4` | `Accept` | — | Q | 2026-11-21 |
| htcs | `5` | `Recv` | — | Q | 2026-11-21 |
| htcs | `6` | `Send` | — | Q | 2026-11-21 |
| htcs | `7` | `Shutdown` | — | Q | 2026-11-21 |
| htcs | `8` | `Fcntl` | — | Q | 2026-11-21 |
| htc:tenv | `0` | `GetServiceInterface` | — | Q | 2026-11-21 |
| htc:tenv | `0` | `GetVariable` | — | Q | 2026-11-21 |
| htc:tenv | `1` | `GetVariableLength` | — | Q | 2026-11-21 |
| htc:tenv | `2` | `WaitUntilVariableAvailable` | — | Q | 2026-11-21 |
| file\_io | `0` | `OpenFile` | — | Q | 2026-11-21 |
| file\_io | `1` | `FileExists` | — | Q | 2026-11-21 |
| file\_io | `2` | `DeleteFile` | — | Q | 2026-11-21 |
| file\_io | `3` | `RenameFile` | — | Q | 2026-11-21 |
| file\_io | `4` | `GetIOType` | — | Q | 2026-11-21 |
| file\_io | `5` | `OpenDirectory` | — | Q | 2026-11-21 |
| file\_io | `6` | `DirectoryExists` | — | Q | 2026-11-21 |
| file\_io | `7` | `CreateDirectory` | — | Q | 2026-11-21 |
| file\_io | `8` | `DeleteDirectory` | — | Q | 2026-11-21 |
| file\_io | `9` | `RenameDirectory` | — | Q | 2026-11-21 |
| file\_io | `10` | `CreateFile` | — | Q | 2026-11-21 |
| file\_io | `11` | `GetFileTimeStamp` | — | Q | 2026-11-21 |
| file\_io | `12` | `GetCaseSensitivePath` | — | Q | 2026-11-21 |
| file\_io | `0` | `ReadFile` | — | Q | 2026-11-21 |
| file\_io | `1` | `WriteFile` | — | Q | 2026-11-21 |
| file\_io | `2` | `GetFileSize` | — | Q | 2026-11-21 |
| file\_io | `3` | `SetFileSize` | — | Q | 2026-11-21 |
| file\_io | `4` | `FlushFile` | — | Q | 2026-11-21 |
| file\_io | `5` | `SetPriorityForFile` | — | Q | 2026-11-21 |
| file\_io | `6` | `GetPriorityForFile` | — | Q | 2026-11-21 |
| file\_io | `0` | `GetEntryCount` | — | Q | 2026-11-21 |
| file\_io | `1` | `ReadDirectory` | — | Q | 2026-11-21 |
| file\_io | `2` | `SetPriorityForDirectory` | — | Q | 2026-11-21 |
| file\_io | `3` | `GetPriorityForDirectory` | — | Q | 2026-11-21 |

### JIT services

[Wiki SwitchBrew](https://switchbrew.org/wiki/JIT_services) · [miroir](https://github.com/backupbrew/switchbrew/blob/master/JIT%20services.md)

**5 commandes documentées**.

| Interface / section | ID | Fonction | Disponibilité indiquée | Encore | Vérifié |
|---|---|---|---|---|---|
| jit:u | `0` | `CreateJitEnvironment` | — | Q | 2026-11-21 |
| IJitEnvironment | `0` | `GenerateCode` | — | Q | 2026-11-21 |
| IJitEnvironment | `1` | `Control` | — | Q | 2026-11-21 |
| IJitEnvironment | `1000` | `LoadPlugin` | — | Q | 2026-11-21 |
| IJitEnvironment | `1001` | `GetCodeAddress` | — | Q | 2026-11-21 |

### Backlight services

[Wiki SwitchBrew](https://switchbrew.org/wiki/Backlight_services) · [miroir](https://github.com/backupbrew/switchbrew/blob/master/Backlight%20services.md)

**29 commandes documentées**.

| Interface / section | ID | Fonction | Disponibilité indiquée | Encore | Vérifié |
|---|---|---|---|---|---|
| lbl | `0` | `SaveCurrentSetting` | — | Q | 2026-11-21 |
| lbl | `1` | `LoadCurrentSetting` | — | Q | 2026-11-21 |
| lbl | `2` | `SetCurrentBrightnessSetting` | — | Q | 2026-11-21 |
| lbl | `3` | `GetCurrentBrightnessSetting` | — | Q | 2026-11-21 |
| lbl | `4` | `ApplyCurrentBrightnessSettingToBacklight` | — | Q | 2026-11-21 |
| lbl | `5` | `GetBrightnessSettingAppliedToBacklight` | — | Q | 2026-11-21 |
| lbl | `6` | `SwitchBacklightOn` | — | Q | 2026-11-21 |
| lbl | `7` | `SwitchBacklightOff` | — | Q | 2026-11-21 |
| lbl | `8` | `GetBacklightSwitchStatus` | — | Q | 2026-11-21 |
| lbl | `9` | `EnableDimming` | — | Q | 2026-11-21 |
| lbl | `10` | `DisableDimming` | — | Q | 2026-11-21 |
| lbl | `11` | `IsDimmingEnabled` | — | Q | 2026-11-21 |
| lbl | `12` | `EnableAutoBrightnessControl` | — | Q | 2026-11-21 |
| lbl | `13` | `DisableAutoBrightnessControl` | — | Q | 2026-11-21 |
| lbl | `14` | `IsAutoBrightnessControlEnabled` | — | Q | 2026-11-21 |
| lbl | `15` | `SetAmbientLightSensorValue` | — | Q | 2026-11-21 |
| lbl | `16` | `GetAmbientLightSensorValue` | — | Q | 2026-11-21 |
| lbl | `17` | `SetBrightnessReflectionDelayLevel` | — | Q | 2026-11-21 |
| lbl | `18` | `GetBrightnessReflectionDelayLevel` | — | Q | 2026-11-21 |
| lbl | `19` | `SetCurrentBrightnessMapping` | — | Q | 2026-11-21 |
| lbl | `20` | `GetCurrentBrightnessMapping` | — | Q | 2026-11-21 |
| lbl | `21` | `SetCurrentAmbientLightSensorMapping` | — | Q | 2026-11-21 |
| lbl | `22` | `GetCurrentAmbientLightSensorMapping` | — | Q | 2026-11-21 |
| lbl | `23` | `IsAmbientLightSensorAvailable` | 3.0.0+ | Q | 2026-11-21 |
| lbl | `24` | `SetCurrentBrightnessSettingForVrMode` | 3.0.0+ | Q | 2026-11-21 |
| lbl | `25` | `GetCurrentBrightnessSettingForVrMode` | 3.0.0+ | Q | 2026-11-21 |
| lbl | `26` | `EnableVrMode` | 3.0.0+ | Q | 2026-11-21 |
| lbl | `27` | `DisableVrMode` | 3.0.0+ | Q | 2026-11-21 |
| lbl | `28` | `IsVrModeEnabled` | 3.0.0+ | Q | 2026-11-21 |

### LDN services

[Wiki SwitchBrew](https://switchbrew.org/wiki/LDN_services) · [miroir](https://github.com/backupbrew/switchbrew/blob/master/LDN%20services.md)

**97 commandes documentées**.

| Interface / section | ID | Fonction | Disponibilité indiquée | Encore | Vérifié |
|---|---|---|---|---|---|
| ldn:m | `0` | `CreateMonitorService` | — | Q | 2026-11-21 |
| ldn:m | `0` | `GetStateForMonitor` | — | Q | 2026-11-21 |
| ldn:m | `1` | `GetNetworkInfoForMonitor` | — | Q | 2026-11-21 |
| ldn:m | `2` | `GetIpv4AddressForMonitor` | — | Q | 2026-11-21 |
| ldn:m | `3` | `GetDisconnectReasonForMonitor` | — | Q | 2026-11-21 |
| ldn:m | `4` | `GetSecurityParameterForMonitor` | — | Q | 2026-11-21 |
| ldn:m | `5` | `GetNetworkConfigForMonitor` | — | Q | 2026-11-21 |
| ldn:m | `100` | `InitializeMonitor` | — | Q | 2026-11-21 |
| ldn:m | `101` | `FinalizeMonitor` | — | Q | 2026-11-21 |
| ldn:s | `0` | `CreateSystemLocalCommunicationService` | — | Q | 2026-11-21 |
| ldn:s | `0` | `GetState` | — | Q | 2026-11-21 |
| ldn:s | `1` | `GetNetworkInfo` | — | Q | 2026-11-21 |
| ldn:s | `2` | `GetIpv4Address` | — | Q | 2026-11-21 |
| ldn:s | `3` | `GetDisconnectReason` | — | Q | 2026-11-21 |
| ldn:s | `4` | `GetSecurityParameter` | — | Q | 2026-11-21 |
| ldn:s | `5` | `GetNetworkConfig` | — | Q | 2026-11-21 |
| ldn:s | `100` | `AttachStateChangeEvent` | — | Q | 2026-11-21 |
| ldn:s | `101` | `GetNetworkInfoLatestUpdate` | — | Q | 2026-11-21 |
| ldn:s | `102` | `Scan` | — | Q | 2026-11-21 |
| ldn:s | `103` | `ScanPrivate` | — | Q | 2026-11-21 |
| ldn:s | `104` | `SetWirelessControllerRestriction` | 5.0.0+ | Q | 2026-11-21 |
| ldn:s | `200` | `OpenAccessPoint` | — | Q | 2026-11-21 |
| ldn:s | `201` | `CloseAccessPoint` | — | Q | 2026-11-21 |
| ldn:s | `202` | `CreateNetwork` | — | Q | 2026-11-21 |
| ldn:s | `203` | `CreateNetworkPrivate` | — | Q | 2026-11-21 |
| ldn:s | `204` | `DestroyNetwork` | — | Q | 2026-11-21 |
| ldn:s | `205` | `Reject` | — | Q | 2026-11-21 |
| ldn:s | `206` | `SetAdvertiseData` | — | Q | 2026-11-21 |
| ldn:s | `207` | `SetStationAcceptPolicy` | — | Q | 2026-11-21 |
| ldn:s | `208` | `AddAcceptFilterEntry` | — | Q | 2026-11-21 |
| ldn:s | `209` | `ClearAcceptFilter` | — | Q | 2026-11-21 |
| ldn:s | `300` | `OpenStation` | — | Q | 2026-11-21 |
| ldn:s | `301` | `CloseStation` | — | Q | 2026-11-21 |
| ldn:s | `302` | `Connect` | — | Q | 2026-11-21 |
| ldn:s | `303` | `ConnectPrivate` | — | Q | 2026-11-21 |
| ldn:s | `304` | `Disconnect` | — | Q | 2026-11-21 |
| ldn:s | `400` | `InitializeSystem` | — | Q | 2026-11-21 |
| ldn:s | `401` | `FinalizeSystem` | — | Q | 2026-11-21 |
| ldn:s | `402` | `SetOperationMode` | 4.0.0+ | Q | 2026-11-21 |
| ldn:s | `403` | `InitializeSystem2` | 7.0.0+ | Q | 2026-11-21 |
| ldn:u | `0` | `CreateUserLocalCommunicationService` | — | Q | 2026-11-21 |
| ldn:u | `0` | `GetState` | — | Q | 2026-11-21 |
| ldn:u | `1` | `GetNetworkInfo` | — | Q | 2026-11-21 |
| ldn:u | `2` | `GetIpv4Address` | — | Q | 2026-11-21 |
| ldn:u | `3` | `GetDisconnectReason` | — | Q | 2026-11-21 |
| ldn:u | `4` | `GetSecurityParameter` | — | Q | 2026-11-21 |
| ldn:u | `5` | `GetNetworkConfig` | — | Q | 2026-11-21 |
| ldn:u | `100` | `AttachStateChangeEvent` | — | Q | 2026-11-21 |
| ldn:u | `101` | `GetNetworkInfoLatestUpdate` | — | Q | 2026-11-21 |
| ldn:u | `102` | `Scan` | — | Q | 2026-11-21 |
| ldn:u | `103` | `ScanPrivate` | — | Q | 2026-11-21 |
| ldn:u | `104` | `SetWirelessControllerRestriction` | 5.0.0+ | Q | 2026-11-21 |
| ldn:u | `200` | `OpenAccessPoint` | — | Q | 2026-11-21 |
| ldn:u | `201` | `CloseAccessPoint` | — | Q | 2026-11-21 |
| ldn:u | `202` | `CreateNetwork` | — | Q | 2026-11-21 |
| ldn:u | `203` | `CreateNetworkPrivate` | — | Q | 2026-11-21 |
| ldn:u | `204` | `DestroyNetwork` | — | Q | 2026-11-21 |
| ldn:u | `205` | `Reject` | — | Q | 2026-11-21 |
| ldn:u | `206` | `SetAdvertiseData` | — | Q | 2026-11-21 |
| ldn:u | `207` | `SetStationAcceptPolicy` | — | Q | 2026-11-21 |
| ldn:u | `208` | `AddAcceptFilterEntry` | — | Q | 2026-11-21 |
| ldn:u | `209` | `ClearAcceptFilter` | — | Q | 2026-11-21 |
| ldn:u | `300` | `OpenStation` | — | Q | 2026-11-21 |
| ldn:u | `301` | `CloseStation` | — | Q | 2026-11-21 |
| ldn:u | `302` | `Connect` | — | Q | 2026-11-21 |
| ldn:u | `303` | `ConnectPrivate` | — | Q | 2026-11-21 |
| ldn:u | `304` | `Disconnect` | — | Q | 2026-11-21 |
| ldn:u | `400` | `Initialize` | — | Q | 2026-11-21 |
| ldn:u | `401` | `Finalize` | — | Q | 2026-11-21 |
| ldn:u | `402` | `Initialize2` | 7.0.0+ | Q | 2026-11-21 |
| ndd | `0` | `EnableAutoCommunication` | — | Q | 2026-11-21 |
| ndd | `1` | `DisableAutoCommunication` | — | Q | 2026-11-21 |
| ndd | `2` | `IsAutoCommunicationEnabled` | — | Q | 2026-11-21 |
| ndd | `3` | `EnablePowerSave` | — | Q | 2026-11-21 |
| ndd | `4` | `DisablePowerSave` | — | Q | 2026-11-21 |
| ndd | `5` | `IsPowerSaveEnabled` | — | Q | 2026-11-21 |
| ndd | `6` | `IsNetworkActive` | — | Q | 2026-11-21 |
| ndd | `7` | `AcquireSendDataUpdateEvent` | — | Q | 2026-11-21 |
| ndd | `8` | `AddSendData` | — | Q | 2026-11-21 |
| ndd | `9` | `ClearSendData` | — | Q | 2026-11-21 |
| ndd | `10` | `GetSendData` | — | Q | 2026-11-21 |
| ndd | `11` | `AcquireReceiveDataEvent` | — | Q | 2026-11-21 |
| ndd | `12` | `GetCurrentReceiveDataCounter` | — | Q | 2026-11-21 |
| ndd | `13` | `GetOldestReceiveDataCounter` | — | Q | 2026-11-21 |
| ndd | `14` | `GetNextReceiveDataCounter` | — | Q | 2026-11-21 |
| ndd | `15` | `GetAvailableReceiveDataCount` | — | Q | 2026-11-21 |
| ndd | `16` | `GetRecentReceiveDataCounter` | — | Q | 2026-11-21 |
| ndd | `17` | `GetReceiveData` | — | Q | 2026-11-21 |
| ndd | `18` | `AddReceiveData` | — | Q | 2026-11-21 |
| ndd | `19` | `ClearReceiveData` | — | Q | 2026-11-21 |
| ndd | `20` | `ClearDataIdFilter` | — | Q | 2026-11-21 |
| ndd | `21` | `AcquireDeviceScanEvent` | — | Q | 2026-11-21 |
| ndd | `22` | `StartDeviceScan` | — | Q | 2026-11-21 |
| ndd | `23` | `CancelDeviceScan` | — | Q | 2026-11-21 |
| ndd | `24` | `GetDeviceScanResult` | — | Q | 2026-11-21 |
| lp2p:app, lp2p:sys | `0` | `CreateNetworkService` | — | Q | 2026-11-21 |
| lp2p:app, lp2p:sys | `8` | `CreateNetworkServiceMonitor` | — | Q | 2026-11-21 |

### Loader services

[Wiki SwitchBrew](https://switchbrew.org/wiki/Loader_services) · [miroir](https://github.com/backupbrew/switchbrew/blob/master/Loader%20services.md)

**9 commandes documentées**.

| Interface / section | ID | Fonction | Disponibilité indiquée | Encore | Vérifié |
|---|---|---|---|---|---|
| ldr:dmnt | `0` | `[AddProcessToDebugLaunchQueue](Loader%20services#AddProcessToDebugLaunchQueue.md##AddProcessToDebugLaunchQueue "wikilink")` | — | Q | 2026-11-21 |
| ldr:dmnt | `1` | `[ClearDebugLaunchQueue](Loader%20services#ClearDebugLaunchQueue.md##ClearDebugLaunchQueue "wikilink")` | — | Q | 2026-11-21 |
| ldr:dmnt | `2` | `[GetNsoInfos](Loader%20services#GetNsoInfos.md##GetNsoInfos "wikilink")` | — | Q | 2026-11-21 |
| ldr:pm | `0` | `CreateProcess` | — | Q | 2026-11-21 |
| ldr:pm | `1` | `GetProgramInfo` | — | Q | 2026-11-21 |
| ldr:pm | `2` | `RegisterTitle` | — | Q | 2026-11-21 |
| ldr:pm | `3` | `UnregisterTitle` | — | Q | 2026-11-21 |
| ldr:shel | `0` | `AddProcessToLaunchQueue` | — | Q | 2026-11-21 |
| ldr:shel | `1` | `ClearLaunchQueue` | — | Q | 2026-11-21 |

### Log services

[Wiki SwitchBrew](https://switchbrew.org/wiki/Log_services) · [miroir](https://github.com/backupbrew/switchbrew/blob/master/Log%20services.md)

**6 commandes documentées**.

| Interface / section | ID | Fonction | Disponibilité indiquée | Encore | Vérifié |
|---|---|---|---|---|---|
| lm | `0` | `OpenLogger` | — | Q | 2026-11-21 |
| lm | `0` | `Log` | — | Q | 2026-11-21 |
| lm | `1` | `SetDestination` | 3.0.0+ | Q | 2026-11-21 |
| lm:get | `0` | `StartLogging` | — | Q | 2026-11-21 |
| lm:get | `1` | `StopLogging` | — | Q | 2026-11-21 |
| lm:get | `2` | `GetLog` | — | Q | 2026-11-21 |

### Manu Services

[Wiki SwitchBrew](https://switchbrew.org/wiki/Manu_Services) · [miroir](https://github.com/backupbrew/switchbrew/blob/master/Manu%20Services.md)

**7 commandes documentées**.

| Interface / section | ID | Fonction | Disponibilité indiquée | Encore | Vérifié |
|---|---|---|---|---|---|
| manu | `0` | `InitUsbTransferPipeFsFile` | — | Q | 2026-11-21 |
| manu | `1` | `FsFile\_Exists` | — | Q | 2026-11-21 |
| manu | `2` | `FsFile\_Read` | — | Q | 2026-11-21 |
| manu | `3` | `FsFile\_Write` | — | Q | 2026-11-21 |
| manu | `4` | `InitUsbTransferPipeRaw` | — | Q | 2026-11-21 |
| manu | `5` | `Raw\_Read` | — | Q | 2026-11-21 |
| manu | `6` | `Raw\_Write` | — | Q | 2026-11-21 |

### NCM services

[Wiki SwitchBrew](https://switchbrew.org/wiki/NCM_services) · [miroir](https://github.com/backupbrew/switchbrew/blob/master/NCM%20services.md)

**101 commandes documentées**.

| Interface / section | ID | Fonction | Disponibilité indiquée | Encore | Vérifié |
|---|---|---|---|---|---|
| Location Resolver services | `0` | `OpenLocationResolver` | — | Q | 2026-11-21 |
| Location Resolver services | `1` | `OpenRegisteredLocationResolver` | — | Q | 2026-11-21 |
| Location Resolver services | `2` | `RefreshLocationResolver` | — | Q | 2026-11-21 |
| Location Resolver services | `3` | `OpenAddOnContentLocationResolver` | 2.0.0+ | Q | 2026-11-21 |
| Location Resolver services | `0` | `ResolveProgramPath` | — | Q | 2026-11-21 |
| Location Resolver services | `1` | `RedirectProgramPath` | — | Q | 2026-11-21 |
| Location Resolver services | `2` | `ResolveApplicationControlPath` | — | Q | 2026-11-21 |
| Location Resolver services | `3` | `ResolveApplicationHtmlDocumentPath` | — | Q | 2026-11-21 |
| Location Resolver services | `4` | `ResolveDataPath` | — | Q | 2026-11-21 |
| Location Resolver services | `5` | `RedirectApplicationControlPath` | — | Q | 2026-11-21 |
| Location Resolver services | `6` | `RedirectApplicationHtmlDocumentPath` | — | Q | 2026-11-21 |
| Location Resolver services | `7` | `ResolveApplicationLegalInformationPath` | — | Q | 2026-11-21 |
| Location Resolver services | `8` | `RedirectApplicationLegalInformationPath` | — | Q | 2026-11-21 |
| Location Resolver services | `9` | `Refresh` | — | Q | 2026-11-21 |
| Location Resolver services | `10` | `RedirectApplicationProgramPath` | 5.0.0+ | Q | 2026-11-21 |
| Location Resolver services | `11` | `ClearApplicationRedirection` | 5.0.0+ | Q | 2026-11-21 |
| Location Resolver services | `12` | `EraseProgramRedirection` | 5.0.0+ | Q | 2026-11-21 |
| Location Resolver services | `13` | `EraseApplicationControlRedirection` | 5.0.0+ | Q | 2026-11-21 |
| Location Resolver services | `14` | `EraseApplicationHtmlDocumentRedirection` | 5.0.0+ | Q | 2026-11-21 |
| Location Resolver services | `15` | `EraseApplicationLegalInformationRedirection` | 5.0.0+ | Q | 2026-11-21 |
| Location Resolver services | `16` | `ResolveProgramPathForDebug` | 7.0.0+ | Q | 2026-11-21 |
| Location Resolver services | `17` | `RedirectProgramPathForDebug` | 7.0.0+ | Q | 2026-11-21 |
| Location Resolver services | `18` | `RedirectApplicationProgramPathForDebug` | 7.0.0+ | Q | 2026-11-21 |
| Location Resolver services | `19` | `EraseProgramRedirectionForDebug` | 7.0.0+ | Q | 2026-11-21 |
| Location Resolver services | `1` | `RegisterProgramPath` | — | Q | 2026-11-21 |
| Location Resolver services | `2` | `UnregisterProgramPath` | — | Q | 2026-11-21 |
| Location Resolver services | `3` | `RedirectProgramPath` | — | Q | 2026-11-21 |
| Location Resolver services | `4` | `ResolveHtmlDocumentPath` | 2.0.0+ | Q | 2026-11-21 |
| Location Resolver services | `5` | `RegisterHtmlDocumentPath` | 2.0.0+ | Q | 2026-11-21 |
| Location Resolver services | `6` | `UnregisterHtmlDocumentPath` | 2.0.0+ | Q | 2026-11-21 |
| Location Resolver services | `7` | `RedirectHtmlDocumentPath` | 2.0.0+ | Q | 2026-11-21 |
| Location Resolver services | `8` | `Refresh` | 7.0.0+ | Q | 2026-11-21 |
| Location Resolver services | `9` | `RefreshExcluding` | 9.0.0+ | Q | 2026-11-21 |
| Location Resolver services | `0` | `ResolveAddOnContentPath` | — | Q | 2026-11-21 |
| Location Resolver services | `1` | `RegisterAddOnContentStorage` | — | Q | 2026-11-21 |
| Location Resolver services | `2` | `UnregisterAllAddOnContentPath` | — | Q | 2026-11-21 |
| Location Resolver services | `3` | `RefreshApplicationAddOnContent` | 9.0.0+ | Q | 2026-11-21 |
| Location Resolver services | `4` | `UnregisterApplicationAddOnContent` | 9.0.0+ | Q | 2026-11-21 |
| Content Manager services | `0` | `CreateContentStorage` | — | Q | 2026-11-21 |
| Content Manager services | `1` | `CreateContentMetaDatabase` | — | Q | 2026-11-21 |
| Content Manager services | `2` | `VerifyContentStorage` | — | Q | 2026-11-21 |
| Content Manager services | `3` | `VerifyContentMetaDatabase` | — | Q | 2026-11-21 |
| Content Manager services | `4` | `OpenContentStorage` | — | Q | 2026-11-21 |
| Content Manager services | `5` | `OpenContentMetaDatabase` | — | Q | 2026-11-21 |
| Content Manager services | `6` | `CloseContentStorageForcibly` | 1.0.0 | Q | 2026-11-21 |
| Content Manager services | `7` | `CloseContentMetaDatabaseForcibly` | 1.0.0 | Q | 2026-11-21 |
| Content Manager services | `8` | `CleanupContentMetaDatabase` | — | Q | 2026-11-21 |
| Content Manager services | `9` | `ActivateContentStorage` | 2.0.0+ | Q | 2026-11-21 |
| Content Manager services | `10` | `InactivateContentStorage` | 2.0.0+ | Q | 2026-11-21 |
| Content Manager services | `11` | `ActivateContentMetaDatabase` | 2.0.0+ | Q | 2026-11-21 |
| Content Manager services | `12` | `InactivateContentMetaDatabase` | 2.0.0+ | Q | 2026-11-21 |
| Content Manager services | `13` | `InvalidateRightsIdCache` | 9.0.0+ | Q | 2026-11-21 |
| Content Manager services | `0` | `GeneratePlaceHolderId` | — | Q | 2026-11-21 |
| Content Manager services | `1` | `CreatePlaceHolder` | — | Q | 2026-11-21 |
| Content Manager services | `2` | `DeletePlaceHolder` | — | Q | 2026-11-21 |
| Content Manager services | `3` | `HasPlaceHolder` | — | Q | 2026-11-21 |
| Content Manager services | `4` | `WritePlaceHolder` | — | Q | 2026-11-21 |
| Content Manager services | `5` | `Register` | — | Q | 2026-11-21 |
| Content Manager services | `6` | `Delete` | — | Q | 2026-11-21 |
| Content Manager services | `7` | `Has` | — | Q | 2026-11-21 |
| Content Manager services | `8` | `GetPath` | — | Q | 2026-11-21 |
| Content Manager services | `9` | `GetPlaceHolderPath` | — | Q | 2026-11-21 |
| Content Manager services | `10` | `CleanupAllPlaceHolder` | — | Q | 2026-11-21 |
| Content Manager services | `11` | `ListPlaceHolder` | — | Q | 2026-11-21 |
| Content Manager services | `12` | `GetContentCount` | — | Q | 2026-11-21 |
| Content Manager services | `13` | `ListContentId` | — | Q | 2026-11-21 |
| Content Manager services | `14` | `GetSizeFromContentId` | — | Q | 2026-11-21 |
| Content Manager services | `15` | `DisableForcibly` | — | Q | 2026-11-21 |
| Content Manager services | `16` | `RevertToPlaceHolder` | 2.0.0+ | Q | 2026-11-21 |
| Content Manager services | `17` | `SetPlaceHolderSize` | 2.0.0+ | Q | 2026-11-21 |
| Content Manager services | `18` | `ReadContentIdFile` | 2.0.0+ | Q | 2026-11-21 |
| Content Manager services | `19` | `GetRightsIdFromPlaceHolderId` | 2.0.0+ | Q | 2026-11-21 |
| Content Manager services | `20` | `GetRightsIdFromContentId` | 2.0.0+ | Q | 2026-11-21 |
| Content Manager services | `21` | `WriteContentForDebug` | 2.0.0+ | Q | 2026-11-21 |
| Content Manager services | `22` | `GetFreeSpaceSize` | 2.0.0+ | Q | 2026-11-21 |
| Content Manager services | `23` | `GetTotalSpaceSize` | 2.0.0+ | Q | 2026-11-21 |
| Content Manager services | `24` | `FlushPlaceHolder` | 3.0.0+ | Q | 2026-11-21 |
| Content Manager services | `25` | `GetSizeFromPlaceHolderId` | 4.0.0+ | Q | 2026-11-21 |
| Content Manager services | `26` | `RepairInvalidFileAttribute` | 4.0.0+ | Q | 2026-11-21 |
| Content Manager services | `27` | `GetRightsIdFromPlaceHolderIdWithCache` | 8.0.0+ | Q | 2026-11-21 |
| Content Manager services | `0` | `Set` | — | Q | 2026-11-21 |
| Content Manager services | `1` | `Get` | — | Q | 2026-11-21 |
| Content Manager services | `2` | `Remove` | — | Q | 2026-11-21 |
| Content Manager services | `3` | `GetContentIdByType` | — | Q | 2026-11-21 |
| Content Manager services | `4` | `ListContentInfo` | — | Q | 2026-11-21 |
| Content Manager services | `5` | `List` | — | Q | 2026-11-21 |
| Content Manager services | `6` | `GetLatestContentMetaKey` | — | Q | 2026-11-21 |
| Content Manager services | `7` | `ListApplication` | — | Q | 2026-11-21 |
| Content Manager services | `8` | `Has` | — | Q | 2026-11-21 |
| Content Manager services | `9` | `HasAll` | — | Q | 2026-11-21 |
| Content Manager services | `10` | `GetSize` | — | Q | 2026-11-21 |
| Content Manager services | `11` | `GetRequiredSystemVersion` | — | Q | 2026-11-21 |
| Content Manager services | `12` | `GetPatchId` | — | Q | 2026-11-21 |
| Content Manager services | `13` | `DisableForcibly` | — | Q | 2026-11-21 |
| Content Manager services | `14` | `LookupOrphanContent` | — | Q | 2026-11-21 |
| Content Manager services | `15` | `Commit` | — | Q | 2026-11-21 |
| Content Manager services | `16` | `HasContent` | — | Q | 2026-11-21 |
| Content Manager services | `17` | `ListContentMetaInfo` | — | Q | 2026-11-21 |
| Content Manager services | `18` | `GetAttributes` | — | Q | 2026-11-21 |
| Content Manager services | `19` | `GetRequiredApplicationVersion` | 2.0.0+ | Q | 2026-11-21 |
| Content Manager services | `20` | `GetContentIdByTypeAndIdOffset` | 5.0.0+ | Q | 2026-11-21 |

### NFC services

[Wiki SwitchBrew](https://switchbrew.org/wiki/NFC_services) · [miroir](https://github.com/backupbrew/switchbrew/blob/master/NFC%20services.md)

**161 commandes documentées**.

| Interface / section | ID | Fonction | Disponibilité indiquée | Encore | Vérifié |
|---|---|---|---|---|---|
| nfc:am | `0` | `CreateAmInterface` | — | Q | 2026-11-21 |
| nfc:am | `0` | `Initialize` | — | Q | 2026-11-21 |
| nfc:am | `1` | `Finalize` | — | Q | 2026-11-21 |
| nfc:am | `2` | `NotifyForegroundApplet` | — | Q | 2026-11-21 |
| nfc:mf:u | `0` | `CreateUserInterface` | — | Q | 2026-11-21 |
| nfc:mf:u | `0` | `Initialize` | — | Q | 2026-11-21 |
| nfc:mf:u | `1` | `Finalize` | — | Q | 2026-11-21 |
| nfc:mf:u | `2` | `ListDevices` | — | Q | 2026-11-21 |
| nfc:mf:u | `3` | `StartDetection` | — | Q | 2026-11-21 |
| nfc:mf:u | `4` | `StopDetection` | — | Q | 2026-11-21 |
| nfc:mf:u | `5` | `Read` | — | Q | 2026-11-21 |
| nfc:mf:u | `6` | `Write` | — | Q | 2026-11-21 |
| nfc:mf:u | `7` | `GetTagInfo` | — | Q | 2026-11-21 |
| nfc:mf:u | `8` | `GetActivateEventHandle` | — | Q | 2026-11-21 |
| nfc:mf:u | `9` | `GetDeactivateEventHandle` | — | Q | 2026-11-21 |
| nfc:mf:u | `10` | `GetState` | — | Q | 2026-11-21 |
| nfc:mf:u | `11` | `GetDeviceState` | — | Q | 2026-11-21 |
| nfc:mf:u | `12` | `GetNpadId` | — | Q | 2026-11-21 |
| nfc:mf:u | `13` | `GetAvailabilityChangeEventHandle` | 3.0.0+ | Q | 2026-11-21 |
| nfc:user | `0` | `CreateUserInterface` | — | Q | 2026-11-21 |
| nfc:user | `0` | `InitializeOld` | — | Q | 2026-11-21 |
| nfc:user | `1` | `FinalizeOld` | — | Q | 2026-11-21 |
| nfc:user | `2` | `GetStateOld` | — | Q | 2026-11-21 |
| nfc:user | `3` | `IsNfcEnabledOld` | — | Q | 2026-11-21 |
| nfc:user | `400` | `Initialize` | 4.0.0+ | Q | 2026-11-21 |
| nfc:user | `401` | `Finalize` | 4.0.0+ | Q | 2026-11-21 |
| nfc:user | `402` | `GetState` | 4.0.0+ | Q | 2026-11-21 |
| nfc:user | `403` | `IsNfcEnabled` | 4.0.0+ | Q | 2026-11-21 |
| nfc:user | `404` | `ListDevices` | 4.0.0+ | Q | 2026-11-21 |
| nfc:user | `405` | `GetDeviceState` | 4.0.0+ | Q | 2026-11-21 |
| nfc:user | `406` | `GetNpadId` | 4.0.0+ | Q | 2026-11-21 |
| nfc:user | `407` | `AttachAvailabilityChangeEvent` | 4.0.0+ | Q | 2026-11-21 |
| nfc:user | `408` | `StartDetection` | 4.0.0+ | Q | 2026-11-21 |
| nfc:user | `409` | `StopDetection` | 4.0.0+ | Q | 2026-11-21 |
| nfc:user | `410` | `GetTagInfo` | 4.0.0+ | Q | 2026-11-21 |
| nfc:user | `411` | `AttachActivateEvent` | 4.0.0+ | Q | 2026-11-21 |
| nfc:user | `412` | `AttachDeactivateEvent` | 4.0.0+ | Q | 2026-11-21 |
| nfc:user | `1000` | `ReadMifare` | 4.0.0+ | Q | 2026-11-21 |
| nfc:user | `1001` | `WriteMifare` | 4.0.0+ | Q | 2026-11-21 |
| nfc:user | `1300` | `SendCommandByPassThrough` | 4.0.0+ | Q | 2026-11-21 |
| nfc:user | `1301` | `KeepPassThroughSession` | 4.0.0+ | Q | 2026-11-21 |
| nfc:user | `1302` | `ReleasePassThroughSession` | 4.0.0+ | Q | 2026-11-21 |
| nfc:sys | `0` | `CreateSystemInterface` | — | Q | 2026-11-21 |
| nfc:sys | `0` | `Initialize` | — | Q | 2026-11-21 |
| nfc:sys | `1` | `Finalize` | — | Q | 2026-11-21 |
| nfc:sys | `2` | `GetStateOld` | — | Q | 2026-11-21 |
| nfc:sys | `3` | `IsNfcEnabledOld` | — | Q | 2026-11-21 |
| nfc:sys | `100` | `SetNfcEnabledOld` | — | Q | 2026-11-21 |
| nfc:sys | `400` | `InitializeSystem` | 4.0.0+ | Q | 2026-11-21 |
| nfc:sys | `401` | `FinalizeSystem` | 4.0.0+ | Q | 2026-11-21 |
| nfc:sys | `402` | `GetState` | 4.0.0+ | Q | 2026-11-21 |
| nfc:sys | `403` | `IsNfcEnabled` | 4.0.0+ | Q | 2026-11-21 |
| nfc:sys | `404` | `ListDevices` | 4.0.0+ | Q | 2026-11-21 |
| nfc:sys | `405` | `GetDeviceState` | 4.0.0+ | Q | 2026-11-21 |
| nfc:sys | `406` | `GetNpadId` | 4.0.0+ | Q | 2026-11-21 |
| nfc:sys | `407` | `AttachAvailabilityChangeEvent` | 4.0.0+ | Q | 2026-11-21 |
| nfc:sys | `408` | `StartDetection` | 4.0.0+ | Q | 2026-11-21 |
| nfc:sys | `409` | `StopDetection` | 4.0.0+ | Q | 2026-11-21 |
| nfc:sys | `410` | `GetTagInfo` | 4.0.0+ | Q | 2026-11-21 |
| nfc:sys | `411` | `AttachActivateEvent` | 4.0.0+ | Q | 2026-11-21 |
| nfc:sys | `412` | `AttachDeactivateEvent` | 4.0.0+ | Q | 2026-11-21 |
| nfc:sys | `500` | `SetNfcEnabled` | 4.0.0+ | Q | 2026-11-21 |
| nfc:sys | `510` | `OutputTestWave` | 7.0.0+ | Q | 2026-11-21 |
| nfc:sys | `1000` | `ReadMifare` | 4.0.0+ | Q | 2026-11-21 |
| nfc:sys | `1001` | `WriteMifare` | 4.0.0+ | Q | 2026-11-21 |
| nfc:sys | `1300` | `SendCommandByPassThrough` | 4.0.0+ | Q | 2026-11-21 |
| nfc:sys | `1301` | `KeepPassThroughSession` | 4.0.0+ | Q | 2026-11-21 |
| nfc:sys | `1302` | `ReleasePassThroughSession` | 4.0.0+ | Q | 2026-11-21 |
| nfp:user | `0` | `CreateUserInterface` | — | Q | 2026-11-21 |
| nfp:user | `0` | `Initialize` | — | Q | 2026-11-21 |
| nfp:user | `1` | `Finalize` | — | Q | 2026-11-21 |
| nfp:user | `2` | `ListDevices` | — | Q | 2026-11-21 |
| nfp:user | `3` | `StartDetection` | — | Q | 2026-11-21 |
| nfp:user | `4` | `StopDetection` | — | Q | 2026-11-21 |
| nfp:user | `5` | `Mount` | — | Q | 2026-11-21 |
| nfp:user | `6` | `Unmount` | — | Q | 2026-11-21 |
| nfp:user | `7` | `OpenApplicationArea` | — | Q | 2026-11-21 |
| nfp:user | `8` | `GetApplicationArea` | — | Q | 2026-11-21 |
| nfp:user | `9` | `SetApplicationArea` | — | Q | 2026-11-21 |
| nfp:user | `10` | `Flush` | — | Q | 2026-11-21 |
| nfp:user | `11` | `Restore` | — | Q | 2026-11-21 |
| nfp:user | `12` | `CreateApplicationArea` | — | Q | 2026-11-21 |
| nfp:user | `13` | `GetTagInfo` | — | Q | 2026-11-21 |
| nfp:user | `14` | `GetRegisterInfo` | — | Q | 2026-11-21 |
| nfp:user | `15` | `GetCommonInfo` | — | Q | 2026-11-21 |
| nfp:user | `16` | `GetModelInfo` | — | Q | 2026-11-21 |
| nfp:user | `17` | `AttachActivateEvent` | — | Q | 2026-11-21 |
| nfp:user | `18` | `AttachDeactivateEvent` | — | Q | 2026-11-21 |
| nfp:user | `19` | `GetState` | — | Q | 2026-11-21 |
| nfp:user | `20` | `GetDeviceState` | — | Q | 2026-11-21 |
| nfp:user | `21` | `GetNpadId` | — | Q | 2026-11-21 |
| nfp:user | `22` | `GetApplicationArea2` | — | Q | 2026-11-21 |
| nfp:user | `23` | `AttachAvailabilityChangeEvent` | 3.0.0+ | Q | 2026-11-21 |
| nfp:user | `24` | `RecreateApplicationArea` | 3.0.0+ | Q | 2026-11-21 |
| nfp:dbg | `0` | `CreateDebugInterface` | — | Q | 2026-11-21 |
| nfp:dbg | `0` | `InitializeDebug` | — | Q | 2026-11-21 |
| nfp:dbg | `1` | `FinalizeDebug` | — | Q | 2026-11-21 |
| nfp:dbg | `2` | `ListDevices` | — | Q | 2026-11-21 |
| nfp:dbg | `3` | `StartDetection` | — | Q | 2026-11-21 |
| nfp:dbg | `4` | `StopDetection` | — | Q | 2026-11-21 |
| nfp:dbg | `5` | `Mount` | — | Q | 2026-11-21 |
| nfp:dbg | `6` | `Unmount` | — | Q | 2026-11-21 |
| nfp:dbg | `7` | `OpenApplicationArea` | — | Q | 2026-11-21 |
| nfp:dbg | `8` | `GetApplicationArea` | — | Q | 2026-11-21 |
| nfp:dbg | `9` | `SetApplicationArea` | — | Q | 2026-11-21 |
| nfp:dbg | `10` | `Flush` | — | Q | 2026-11-21 |
| nfp:dbg | `11` | `Restore` | — | Q | 2026-11-21 |
| nfp:dbg | `12` | `CreateApplicationArea` | — | Q | 2026-11-21 |
| nfp:dbg | `13` | `GetTagInfo` | — | Q | 2026-11-21 |
| nfp:dbg | `14` | `GetRegisterInfo` | — | Q | 2026-11-21 |
| nfp:dbg | `15` | `GetCommonInfo` | — | Q | 2026-11-21 |
| nfp:dbg | `16` | `GetModelInfo` | — | Q | 2026-11-21 |
| nfp:dbg | `17` | `AttachActivateEvent` | — | Q | 2026-11-21 |
| nfp:dbg | `18` | `AttachDeactivateEvent` | — | Q | 2026-11-21 |
| nfp:dbg | `19` | `GetState` | — | Q | 2026-11-21 |
| nfp:dbg | `20` | `GetDeviceState` | — | Q | 2026-11-21 |
| nfp:dbg | `21` | `GetNpadId` | — | Q | 2026-11-21 |
| nfp:dbg | `22` | `GetApplicationArea2` | — | Q | 2026-11-21 |
| nfp:dbg | `23` | `AttachAvailabilityChangeEvent` | 3.0.0+ | Q | 2026-11-21 |
| nfp:dbg | `24` | `RecreateApplicationArea` | 3.0.0+ | Q | 2026-11-21 |
| nfp:dbg | `100` | `Format` | — | Q | 2026-11-21 |
| nfp:dbg | `101` | `GetAdminInfo` | — | Q | 2026-11-21 |
| nfp:dbg | `102` | `GetRegisterInfo` | — | Q | 2026-11-21 |
| nfp:dbg | `103` | `SetRegisterInfo` | — | Q | 2026-11-21 |
| nfp:dbg | `104` | `DeleteRegisterInfo` | — | Q | 2026-11-21 |
| nfp:dbg | `105` | `DeleteApplicationArea` | — | Q | 2026-11-21 |
| nfp:dbg | `106` | `ExistsApplicationArea` | — | Q | 2026-11-21 |
| nfp:dbg | `200` | `GetAll` | — | Q | 2026-11-21 |
| nfp:dbg | `201` | `SetAll` | — | Q | 2026-11-21 |
| nfp:dbg | `202` | `FlushDebug` | — | Q | 2026-11-21 |
| nfp:dbg | `203` | `BreakTag` | — | Q | 2026-11-21 |
| nfp:dbg | `204` | `ReadBackupData` | — | Q | 2026-11-21 |
| nfp:dbg | `205` | `WriteBackupData` | — | Q | 2026-11-21 |
| nfp:dbg | `206` | `WriteNtf` | — | Q | 2026-11-21 |
| nfp:sys | `0` | `CreateSystemInterface` | — | Q | 2026-11-21 |
| nfp:sys | `0` | `InitializeSystem` | — | Q | 2026-11-21 |
| nfp:sys | `1` | `FinalizeSystem` | — | Q | 2026-11-21 |
| nfp:sys | `2` | `ListDevices` | — | Q | 2026-11-21 |
| nfp:sys | `3` | `StartDetection` | — | Q | 2026-11-21 |
| nfp:sys | `4` | `StopDetection` | — | Q | 2026-11-21 |
| nfp:sys | `5` | `Mount` | — | Q | 2026-11-21 |
| nfp:sys | `6` | `Unmount` | — | Q | 2026-11-21 |
| nfp:sys | `10` | `Flush` | — | Q | 2026-11-21 |
| nfp:sys | `11` | `Restore` | — | Q | 2026-11-21 |
| nfp:sys | `13` | `GetTagInfo` | — | Q | 2026-11-21 |
| nfp:sys | `14` | `GetRegisterInfo` | — | Q | 2026-11-21 |
| nfp:sys | `15` | `GetCommonInfo` | — | Q | 2026-11-21 |
| nfp:sys | `16` | `GetModelInfo` | — | Q | 2026-11-21 |
| nfp:sys | `17` | `AttachActivateEvent` | — | Q | 2026-11-21 |
| nfp:sys | `18` | `AttachDeactivateEvent` | — | Q | 2026-11-21 |
| nfp:sys | `19` | `GetState` | — | Q | 2026-11-21 |
| nfp:sys | `20` | `GetDeviceState` | — | Q | 2026-11-21 |
| nfp:sys | `21` | `GetNpadId` | — | Q | 2026-11-21 |
| nfp:sys | `23` | `AttachAvailabilityChangeEvent` | 3.0.0+ | Q | 2026-11-21 |
| nfp:sys | `100` | `Format` | — | Q | 2026-11-21 |
| nfp:sys | `101` | `GetAdminInfo` | — | Q | 2026-11-21 |
| nfp:sys | `102` | `GetRegisterInfo` | — | Q | 2026-11-21 |
| nfp:sys | `103` | `SetRegisterInfo` | — | Q | 2026-11-21 |
| nfp:sys | `104` | `DeleteRegisterInfo` | — | Q | 2026-11-21 |
| nfp:sys | `105` | `DeleteApplicationArea` | — | Q | 2026-11-21 |
| nfp:sys | `106` | `ExistsApplicationArea` | — | Q | 2026-11-21 |

### Network Interface services

[Wiki SwitchBrew](https://switchbrew.org/wiki/Network_Interface_services) · [miroir](https://github.com/backupbrew/switchbrew/blob/master/Network%20Interface%20services.md)

**77 commandes documentées**.

| Interface / section | ID | Fonction | Disponibilité indiquée | Encore | Vérifié |
|---|---|---|---|---|---|
| nifm:a, nifm:s, nifm:u | `4` | `CreateGeneralServiceOld ([1.0.0-2.3.0] CreateGeneralService)` | — | Q | 2026-11-21 |
| nifm:a, nifm:s, nifm:u | `5` | `CreateGeneralService` | 3.0.0+ | Q | 2026-11-21 |
| nifm:a, nifm:s, nifm:u | `1` | `GetClientId` | — | Q | 2026-11-21 |
| nifm:a, nifm:s, nifm:u | `2` | `CreateScanRequest` | — | Q | 2026-11-21 |
| nifm:a, nifm:s, nifm:u | `4` | `CreateRequest` | — | Q | 2026-11-21 |
| nifm:a, nifm:s, nifm:u | `5` | `GetCurrentNetworkProfile` | — | Q | 2026-11-21 |
| nifm:a, nifm:s, nifm:u | `6` | `EnumerateNetworkInterfaces` | — | Q | 2026-11-21 |
| nifm:a, nifm:s, nifm:u | `7` | `EnumerateNetworkProfiles` | — | Q | 2026-11-21 |
| nifm:a, nifm:s, nifm:u | `8` | `GetNetworkProfile` | — | Q | 2026-11-21 |
| nifm:a, nifm:s, nifm:u | `9` | `SetNetworkProfile` | — | Q | 2026-11-21 |
| nifm:a, nifm:s, nifm:u | `10` | `RemoveNetworkProfile` | — | Q | 2026-11-21 |
| nifm:a, nifm:s, nifm:u | `11` | `GetScanDataOld ([1.0.0-3.0.2] GetScanData)` | — | Q | 2026-11-21 |
| nifm:a, nifm:s, nifm:u | `12` | `GetCurrentIpAddress` | — | Q | 2026-11-21 |
| nifm:a, nifm:s, nifm:u | `13` | `GetCurrentAccessPointOld ([1.0.0-3.0.2] GetCurrentAccessPoint)` | — | Q | 2026-11-21 |
| nifm:a, nifm:s, nifm:u | `14` | `CreateTemporaryNetworkProfile` | — | Q | 2026-11-21 |
| nifm:a, nifm:s, nifm:u | `15` | `GetCurrentIpConfigInfo` | — | Q | 2026-11-21 |
| nifm:a, nifm:s, nifm:u | `16` | `SetWirelessCommunicationEnabled` | — | Q | 2026-11-21 |
| nifm:a, nifm:s, nifm:u | `17` | `IsWirelessCommunicationEnabled` | — | Q | 2026-11-21 |
| nifm:a, nifm:s, nifm:u | `18` | `GetInternetConnectionStatus` | — | Q | 2026-11-21 |
| nifm:a, nifm:s, nifm:u | `19` | `SetEthernetCommunicationEnabled` | — | Q | 2026-11-21 |
| nifm:a, nifm:s, nifm:u | `20` | `IsEthernetCommunicationEnabled` | — | Q | 2026-11-21 |
| nifm:a, nifm:s, nifm:u | `21` | `IsAnyInternetRequestAccepted` | — | Q | 2026-11-21 |
| nifm:a, nifm:s, nifm:u | `22` | `IsAnyForegroundRequestAccepted` | — | Q | 2026-11-21 |
| nifm:a, nifm:s, nifm:u | `23` | `PutToSleep` | — | Q | 2026-11-21 |
| nifm:a, nifm:s, nifm:u | `24` | `WakeUp` | — | Q | 2026-11-21 |
| nifm:a, nifm:s, nifm:u | `25` | `GetSsidListVersion` | — | Q | 2026-11-21 |
| nifm:a, nifm:s, nifm:u | `26` | `SetExclusiveClient` | — | Q | 2026-11-21 |
| nifm:a, nifm:s, nifm:u | `27` | `GetDefaultIpSetting` | — | Q | 2026-11-21 |
| nifm:a, nifm:s, nifm:u | `28` | `SetDefaultIpSetting` | — | Q | 2026-11-21 |
| nifm:a, nifm:s, nifm:u | `29` | `SetWirelessCommunicationEnabledForTest` | — | Q | 2026-11-21 |
| nifm:a, nifm:s, nifm:u | `30` | `SetEthernetCommunicationEnabledForTest` | — | Q | 2026-11-21 |
| nifm:a, nifm:s, nifm:u | `31` | `GetTelemetorySystemEventReadableHandle` | 2.0.0+ | Q | 2026-11-21 |
| nifm:a, nifm:s, nifm:u | `32` | `GetTelemetryInfo` | 2.0.0+ | Q | 2026-11-21 |
| nifm:a, nifm:s, nifm:u | `33` | `ConfirmSystemAvailability` | 2.0.0+ | Q | 2026-11-21 |
| nifm:a, nifm:s, nifm:u | `34` | `SetBackgroundRequestEnabled` | 4.0.0+ | Q | 2026-11-21 |
| nifm:a, nifm:s, nifm:u | `35` | `GetScanData` | 4.0.0+ | Q | 2026-11-21 |
| nifm:a, nifm:s, nifm:u | `36` | `GetCurrentAccessPoint` | 4.0.0+ | Q | 2026-11-21 |
| nifm:a, nifm:s, nifm:u | `37` | `Shutdown` | 4.0.0+ | Q | 2026-11-21 |
| nifm:a, nifm:s, nifm:u | `38` | `GetAllowedChannels` | 6.0.0+ | Q | 2026-11-21 |
| nifm:a, nifm:s, nifm:u | `39` | `NotifyApplicationSuspended` | 8.0.0+ | Q | 2026-11-21 |
| nifm:a, nifm:s, nifm:u | `40` | `SetAcceptableNetworkTypeFlag` | 8.0.0+ | Q | 2026-11-21 |
| nifm:a, nifm:s, nifm:u | `41` | `GetAcceptableNetworkTypeFlag` | 8.0.0+ | Q | 2026-11-21 |
| nifm:a, nifm:s, nifm:u | `42` | `NotifyConnectionStateChanged` | 8.0.0+ | Q | 2026-11-21 |
| nifm:a, nifm:s, nifm:u | `43` | `SetWowlDelayedWakeTime` | 9.0.0+ | Q | 2026-11-21 |
| nifm:a, nifm:s, nifm:u | `0` | `Submit` | — | Q | 2026-11-21 |
| nifm:a, nifm:s, nifm:u | `1` | `IsProcessing` | — | Q | 2026-11-21 |
| nifm:a, nifm:s, nifm:u | `2` | `GetResult` | — | Q | 2026-11-21 |
| nifm:a, nifm:s, nifm:u | `3` | `GetSystemEventReadableHandle` | — | Q | 2026-11-21 |
| nifm:a, nifm:s, nifm:u | `4` | `SetChannels` | 6.0.0+ | Q | 2026-11-21 |
| nifm:a, nifm:s, nifm:u | `0` | `GetRequestState` | — | Q | 2026-11-21 |
| nifm:a, nifm:s, nifm:u | `1` | `GetResult` | — | Q | 2026-11-21 |
| nifm:a, nifm:s, nifm:u | `2` | `GetSystemEventReadableHandles` | — | Q | 2026-11-21 |
| nifm:a, nifm:s, nifm:u | `3` | `Cancel` | — | Q | 2026-11-21 |
| nifm:a, nifm:s, nifm:u | `4` | `Submit` | — | Q | 2026-11-21 |
| nifm:a, nifm:s, nifm:u | `5` | `SetRequirement` | — | Q | 2026-11-21 |
| nifm:a, nifm:s, nifm:u | `6` | `SetRequirementPreset` | — | Q | 2026-11-21 |
| nifm:a, nifm:s, nifm:u | `8` | `SetPriority` | — | Q | 2026-11-21 |
| nifm:a, nifm:s, nifm:u | `9` | `SetNetworkProfileId` | — | Q | 2026-11-21 |
| nifm:a, nifm:s, nifm:u | `10` | `SetRejectable` | — | Q | 2026-11-21 |
| nifm:a, nifm:s, nifm:u | `11` | `SetConnectionConfirmationOption` | — | Q | 2026-11-21 |
| nifm:a, nifm:s, nifm:u | `12` | `SetPersistent` | — | Q | 2026-11-21 |
| nifm:a, nifm:s, nifm:u | `13` | `SetInstant` | — | Q | 2026-11-21 |
| nifm:a, nifm:s, nifm:u | `14` | `SetSustainable` | — | Q | 2026-11-21 |
| nifm:a, nifm:s, nifm:u | `15` | `SetRawPriority` | — | Q | 2026-11-21 |
| nifm:a, nifm:s, nifm:u | `16` | `SetGreedy` | — | Q | 2026-11-21 |
| nifm:a, nifm:s, nifm:u | `17` | `SetSharable` | — | Q | 2026-11-21 |
| nifm:a, nifm:s, nifm:u | `18` | `SetRequirementByRevision` | — | Q | 2026-11-21 |
| nifm:a, nifm:s, nifm:u | `19` | `GetRequirement` | — | Q | 2026-11-21 |
| nifm:a, nifm:s, nifm:u | `20` | `GetRevision` | — | Q | 2026-11-21 |
| nifm:a, nifm:s, nifm:u | `21` | `GetAppletInfo` | — | Q | 2026-11-21 |
| nifm:a, nifm:s, nifm:u | `22` | `GetAdditionalInfo` | — | Q | 2026-11-21 |
| nifm:a, nifm:s, nifm:u | `23` | `SetKeptInSleep` | 3.0.0+ | Q | 2026-11-21 |
| nifm:a, nifm:s, nifm:u | `24` | `RegisterSocketDescriptor` | 3.0.0+ | Q | 2026-11-21 |
| nifm:a, nifm:s, nifm:u | `25` | `UnregisterSocketDescriptor` | 3.0.0+ | Q | 2026-11-21 |
| nifm:a, nifm:s, nifm:u | `0` | `Update` | — | Q | 2026-11-21 |
| nifm:a, nifm:s, nifm:u | `1` | `PersistOld ([1.0.0-2.3.0] Persist)` | — | Q | 2026-11-21 |
| nifm:a, nifm:s, nifm:u | `2` | `Persist` | 3.0.0+ | Q | 2026-11-21 |

### NIM services

[Wiki SwitchBrew](https://switchbrew.org/wiki/NIM_services) · [miroir](https://github.com/backupbrew/switchbrew/blob/master/NIM%20services.md)

**100 commandes documentées**.

| Interface / section | ID | Fonction | Disponibilité indiquée | Encore | Vérifié |
|---|---|---|---|---|---|
| nim | `0` | `CreateSystemUpdateTask` | — | Q | 2026-11-21 |
| nim | `1` | `DestroySystemUpdateTask` | — | Q | 2026-11-21 |
| nim | `2` | `ListSystemUpdateTask` | — | Q | 2026-11-21 |
| nim | `3` | `RequestSystemUpdateTaskRun` | — | Q | 2026-11-21 |
| nim | `4` | `GetSystemUpdateTaskInfo` | — | Q | 2026-11-21 |
| nim | `5` | `CommitSystemUpdateTask` | — | Q | 2026-11-21 |
| nim | `6` | `CreateNetworkInstallTask` | — | Q | 2026-11-21 |
| nim | `7` | `DestroyNetworkInstallTask` | — | Q | 2026-11-21 |
| nim | `8` | `ListNetworkInstallTask` | — | Q | 2026-11-21 |
| nim | `9` | `RequestNetworkInstallTaskRun` | — | Q | 2026-11-21 |
| nim | `10` | `GetNetworkInstallTaskInfo` | — | Q | 2026-11-21 |
| nim | `11` | `CommitNetworkInstallTask` | — | Q | 2026-11-21 |
| nim | `12` | `RequestLatestSystemUpdateMeta` | — | Q | 2026-11-21 |
| nim | `14` | `ListApplicationNetworkInstallTask` | — | Q | 2026-11-21 |
| nim | `15` | `ListNetworkInstallTaskContentMeta` | — | Q | 2026-11-21 |
| nim | `16` | `RequestLatestVersion` | — | Q | 2026-11-21 |
| nim | `17` | `SetNetworkInstallTaskAttribute` | — | Q | 2026-11-21 |
| nim | `18` | `AddNetworkInstallTaskContentMeta` | — | Q | 2026-11-21 |
| nim | `19` | `GetDownloadedSystemDataPath` | — | Q | 2026-11-21 |
| nim | `20` | `CalculateNetworkInstallTaskRequiredSize` | — | Q | 2026-11-21 |
| nim | `21` | `IsExFatDriverIncluded` | — | Q | 2026-11-21 |
| nim | `22` | `GetBackgroundDownloadStressTaskInfo` | — | Q | 2026-11-21 |
| nim | `23` | `RequestDeviceAuthenticationToken` | 2.0.0+ | Q | 2026-11-21 |
| nim | `24` | `RequestGameCardRegistrationStatus` | 2.0.0+ | Q | 2026-11-21 |
| nim | `25` | `RequestRegisterGameCard` | 2.0.0+ | Q | 2026-11-21 |
| nim | `26` | `RequestRegisterNotificationToken` | 2.0.0+ | Q | 2026-11-21 |
| nim | `27` | `RequestDownloadTaskList` | 2.0.0+ | Q | 2026-11-21 |
| nim | `28` | `RequestApplicationControl` | 2.0.0+ | Q | 2026-11-21 |
| nim | `29` | `RequestLatestApplicationControl` | 2.0.0+ | Q | 2026-11-21 |
| nim | `30` | `RequestVersionList` | 2.0.0+ | Q | 2026-11-21 |
| nim | `31` | `CreateApplyDeltaTask` | 2.0.0+ | Q | 2026-11-21 |
| nim | `32` | `DestroyApplyDeltaTask` | 2.0.0+ | Q | 2026-11-21 |
| nim | `33` | `ListApplicationApplyDeltaTask` | 2.0.0+ | Q | 2026-11-21 |
| nim | `34` | `RequestApplyDeltaTaskRun` | 2.0.0+ | Q | 2026-11-21 |
| nim | `35` | `GetApplyDeltaTaskInfo` | 2.0.0+ | Q | 2026-11-21 |
| nim | `36` | `ListApplyDeltaTask` | 2.0.0+ | Q | 2026-11-21 |
| nim | `37` | `CommitApplyDeltaTask` | 2.0.0+ | Q | 2026-11-21 |
| nim | `38` | `CalculateApplyDeltaTaskRequiredSize` | 2.0.0+ | Q | 2026-11-21 |
| nim | `39` | `PrepareShutdown` | 2.0.0+ | Q | 2026-11-21 |
| nim | `40` | `ListApplyDeltaTask2` | 2.0.0+ | Q | 2026-11-21 |
| nim | `41` | `ClearNotEnoughSpaceStateOfApplyDeltaTask` | 2.0.0+ | Q | 2026-11-21 |
| nim:shp | `0` | `RequestDeviceAuthenticationToken` | — | Q | 2026-11-21 |
| nim:shp | `1` | `RequestCachedDeviceAuthenticationToken` | 3.0.0+ | Q | 2026-11-21 |
| nim:shp | `100` | `RequestRegisterDeviceAccount` | — | Q | 2026-11-21 |
| nim:shp | `101` | `RequestUnregisterDeviceAccount` | — | Q | 2026-11-21 |
| nim:shp | `102` | `RequestDeviceAccountStatus` | — | Q | 2026-11-21 |
| nim:shp | `103` | `GetDeviceAccountInfo` | — | Q | 2026-11-21 |
| nim:shp | `104` | `RequestDeviceRegistrationInfo` | — | Q | 2026-11-21 |
| nim:shp | `105` | `RequestTransferDeviceAccount` | — | Q | 2026-11-21 |
| nim:shp | `106` | `RequestSyncRegistration` | 3.0.0+ | Q | 2026-11-21 |
| nim:shp | `107` | `IsOwnDeviceId` | 3.0.0+ | Q | 2026-11-21 |
| nim:shp | `200` | `RequestRegisterNotificationToken` | — | Q | 2026-11-21 |
| nim:shp | `300` | `RequestUnlinkDevice` | — | Q | 2026-11-21 |
| nim:shp | `301` | `RequestUnlinkDeviceIntegrated` | — | Q | 2026-11-21 |
| nim:shp | `302` | `RequestLinkDevice` | — | Q | 2026-11-21 |
| nim:shp | `303` | `HasDeviceLink` | — | Q | 2026-11-21 |
| nim:shp | `304` | `RequestUnlinkDeviceAll` | 4.0.0+ | Q | 2026-11-21 |
| nim:shp | `305` | `RequestCreateVirtualAccount` | 4.0.0+ | Q | 2026-11-21 |
| nim:shp | `306` | `RequestDeviceLinkStatus` | 4.0.0+ | Q | 2026-11-21 |
| nim:shp | `400` | `GetAccountByVirtualAccount` | — | Q | 2026-11-21 |
| nim:shp | `401` | `GetVirtualAccount` | 6.0.0+ | Q | 2026-11-21 |
| nim:shp | `500` | `RequestSyncTicketLegacy ([1.0.0-8.1.0] RequestSyncTicket)` | — | Q | 2026-11-21 |
| nim:shp | `501` | `RequestDownloadTicket` | — | Q | 2026-11-21 |
| nim:shp | `502` | `RequestDownloadTicketForPrepurchasedContents` | 4.0.0+ | Q | 2026-11-21 |
| nim:shp | `503` | `RequestSyncTicket` | 9.0.0+ | Q | 2026-11-21 |
| nim:shp | `504` | `RequestDownloadTicketForPrepurchasedContents2` | 9.0.0+ | Q | 2026-11-21 |
| nim:eca | `0` | `CreateServerInterface` | — | Q | 2026-11-21 |
| nim:eca | `1` | `RefreshDebugAvailability` | 6.0.0+ | Q | 2026-11-21 |
| nim:eca | `2` | `ClearDebugResponse` | 6.0.0+ | Q | 2026-11-21 |
| nim:eca | `3` | `RegisterDebugResponse` | 6.0.0+ | Q | 2026-11-21 |
| nim:eca | `0` | `CreateAccessorInterface` | — | Q | 2026-11-21 |
| nim:eca | `0` | `CreateAsyncInterface` | — | Q | 2026-11-21 |
| nim:eca | `0` | `Cancel` | — | Q | 2026-11-21 |
| nim:eca | `1` | `GetSize` | — | Q | 2026-11-21 |
| nim:eca | `2` | `Read` | — | Q | 2026-11-21 |
| nim:eca | `3` | `GetErrorCode` | — | Q | 2026-11-21 |
| nim:eca | `4` | `Request` | — | Q | 2026-11-21 |
| nim:eca | `5` | `Prepare` | — | Q | 2026-11-21 |
| nim:ecas | `0` | `RegisterSpecialClient` | — | Q | 2026-11-21 |
| nim:ecas | `1` | `UnregisterSpecialClient` | — | Q | 2026-11-21 |
| ntc | `0` | `OpenEnsureNetworkClockAvailabilityService` | — | Q | 2026-11-21 |
| ntc | `100` | `SuspendAutonomicTimeCorrection` | 3.0.0+ | Q | 2026-11-21 |
| ntc | `101` | `ResumeAutonomicTimeCorrection` | 3.0.0+ | Q | 2026-11-21 |
| ntc | `0` | `StartTask` | — | Q | 2026-11-21 |
| ntc | `1` | `GetFinishNotificationEvent` | — | Q | 2026-11-21 |
| ntc | `2` | `GetResult` | — | Q | 2026-11-21 |
| ntc | `3` | `Cancel` | — | Q | 2026-11-21 |
| ntc | `4` | `IsProcessing` | — | Q | 2026-11-21 |
| ntc | `5` | `GetServerTime` | 3.0.0+ | Q | 2026-11-21 |
| IAsyncValue | `0` | `GetSize` | — | Q | 2026-11-21 |
| IAsyncValue | `1` | `Get` | — | Q | 2026-11-21 |
| IAsyncValue | `2` | `Cancel` | — | Q | 2026-11-21 |
| IAsyncValue | `3` | `GetErrorContext` | 4.0.0+ | Q | 2026-11-21 |
| IAsyncResult | `0` | `Get` | — | Q | 2026-11-21 |
| IAsyncResult | `1` | `Cancel` | — | Q | 2026-11-21 |
| IAsyncResult | `2` | `GetErrorContext` | 4.0.0+ | Q | 2026-11-21 |
| IAsyncProgressResult | `0` | `Get` | — | Q | 2026-11-21 |
| IAsyncProgressResult | `1` | `Cancel` | — | Q | 2026-11-21 |
| IAsyncProgressResult | `2` | `GetProgress` | — | Q | 2026-11-21 |
| IAsyncProgressResult | `3` | `GetErrorContext` | 4.0.0+ | Q | 2026-11-21 |

### NPNS services

[Wiki SwitchBrew](https://switchbrew.org/wiki/NPNS_services) · [miroir](https://github.com/backupbrew/switchbrew/blob/master/NPNS%20services.md)

**58 commandes documentées**.

| Interface / section | ID | Fonction | Disponibilité indiquée | Encore | Vérifié |
|---|---|---|---|---|---|
| npns:u | `1` | `ListenAll` | — | Q | 2026-11-21 |
| npns:u | `2` | `ListenTo` | — | Q | 2026-11-21 |
| npns:u | `3` | `Receive` | — | Q | 2026-11-21 |
| npns:u | `4` | `ReceiveRaw` | — | Q | 2026-11-21 |
| npns:u | `5` | `GetReceiveEvent` | — | Q | 2026-11-21 |
| npns:u | `7` | `GetStateChangeEvent` | — | Q | 2026-11-21 |
| npns:u | `21` | `CreateToken` | — | Q | 2026-11-21 |
| npns:u | `23` | `DestroyToken` | — | Q | 2026-11-21 |
| npns:u | `25` | `QueryIsTokenValid` | — | Q | 2026-11-21 |
| npns:u | `26` | `ListenToMyApplicationId` | 5.0.0+ | Q | 2026-11-21 |
| npns:u | `101` | `Suspend` | — | Q | 2026-11-21 |
| npns:u | `102` | `Resume` | — | Q | 2026-11-21 |
| npns:u | `103` | `GetState` | — | Q | 2026-11-21 |
| npns:u | `104` | `GetStatistics` | 3.0.0+ | Q | 2026-11-21 |
| npns:u | `111` | `GetJid` | — | Q | 2026-11-21 |
| npns:u | `120` | `CreateNotificationReceiver` | 7.0.0+ | Q | 2026-11-21 |
| npns:u | `151` | `GetStateWithHandover` | 8.0.0+ | Q | 2026-11-21 |
| npns:u | `152` | `GetStateChangeEventWithHandover` | 8.0.0+ | Q | 2026-11-21 |
| npns:u | `153` | `GetDropEventWithHandover` | 8.0.0+ | Q | 2026-11-21 |
| npns:u | `1` | `ListenTo` | — | Q | 2026-11-21 |
| npns:u | `2` | `ListenToMyApplicationId` | — | Q | 2026-11-21 |
| npns:u | `4` | `GetReceiveEvent` | — | Q | 2026-11-21 |
| npns:s | `1` | `ListenAll` | — | Q | 2026-11-21 |
| npns:s | `2` | `ListenTo` | — | Q | 2026-11-21 |
| npns:s | `3` | `Receive` | — | Q | 2026-11-21 |
| npns:s | `4` | `ReceiveRaw` | — | Q | 2026-11-21 |
| npns:s | `5` | `GetReceiveEvent` | — | Q | 2026-11-21 |
| npns:s | `6` | `ListenUndelivered` | — | Q | 2026-11-21 |
| npns:s | `7` | `GetStateChangeEvent` | — | Q | 2026-11-21 |
| npns:s | `11` | `SubscribeTopic` | — | Q | 2026-11-21 |
| npns:s | `12` | `UnsubscribeTopic` | — | Q | 2026-11-21 |
| npns:s | `13` | `QueryIsTopicExist` | — | Q | 2026-11-21 |
| npns:s | `21` | `CreateToken` | — | Q | 2026-11-21 |
| npns:s | `22` | `CreateTokenWithApplicationId` | — | Q | 2026-11-21 |
| npns:s | `23` | `DestroyToken` | — | Q | 2026-11-21 |
| npns:s | `24` | `DestroyTokenWithApplicationId` | — | Q | 2026-11-21 |
| npns:s | `25` | `QueryIsTokenValid` | — | Q | 2026-11-21 |
| npns:s | `26` | `ListenToMyApplicationId` | 5.0.0+ | Q | 2026-11-21 |
| npns:s | `31` | `UploadTokenToBaaS` | — | Q | 2026-11-21 |
| npns:s | `32` | `DestroyTokenForBaaS` | — | Q | 2026-11-21 |
| npns:s | `33` | `CreateTokenForBaas` | 7.0.0+ | Q | 2026-11-21 |
| npns:s | `34` | `SetBaasDeviceAccountIdList` | 7.0.0+ | Q | 2026-11-21 |
| npns:s | `101` | `Suspend` | — | Q | 2026-11-21 |
| npns:s | `102` | `Resume` | — | Q | 2026-11-21 |
| npns:s | `103` | `GetState` | — | Q | 2026-11-21 |
| npns:s | `104` | `GetStatistics` | 3.0.0+ | Q | 2026-11-21 |
| npns:s | `105` | `GetPlayReportRequestEvent` | 3.0.0+ | Q | 2026-11-21 |
| npns:s | `111` | `GetJid` | — | Q | 2026-11-21 |
| npns:s | `112` | `CreateJid` | — | Q | 2026-11-21 |
| npns:s | `113` | `DestroyJid` | — | Q | 2026-11-21 |
| npns:s | `114` | `AttachJid` | — | Q | 2026-11-21 |
| npns:s | `115` | `DetachJid` | — | Q | 2026-11-21 |
| npns:s | `120` | `CreateNotificationReceiver` | 7.0.0+ | Q | 2026-11-21 |
| npns:s | `151` | `GetStateWithHandover` | 8.0.0+ | Q | 2026-11-21 |
| npns:s | `152` | `GetStateChangeEventWithHandover` | 8.0.0+ | Q | 2026-11-21 |
| npns:s | `153` | `GetDropEventWithHandover` | 8.0.0+ | Q | 2026-11-21 |
| npns:s | `201` | `RequestChangeStateForceTimed` | 3.0.0+ | Q | 2026-11-21 |
| npns:s | `202` | `RequestChangeStateForceAsync` | 3.0.0+ | Q | 2026-11-21 |

### NV services

[Wiki SwitchBrew](https://switchbrew.org/wiki/NV_services) · [miroir](https://github.com/backupbrew/switchbrew/blob/master/NV%20services.md)

**42 commandes documentées**.

| Interface / section | ID | Fonction | Disponibilité indiquée | Encore | Vérifié |
|---|---|---|---|---|---|
| nvdrv, nvdrv:a, nvdrv:s, nvdrv:t | `0` | `Open` | — | Q | 2026-11-21 |
| nvdrv, nvdrv:a, nvdrv:s, nvdrv:t | `1` | `Ioctl` | — | Q | 2026-11-21 |
| nvdrv, nvdrv:a, nvdrv:s, nvdrv:t | `2` | `Close` | — | Q | 2026-11-21 |
| nvdrv, nvdrv:a, nvdrv:s, nvdrv:t | `3` | `Initialize` | — | Q | 2026-11-21 |
| nvdrv, nvdrv:a, nvdrv:s, nvdrv:t | `4` | `QueryEvent` | — | Q | 2026-11-21 |
| nvdrv, nvdrv:a, nvdrv:s, nvdrv:t | `5` | `MapSharedMem` | — | Q | 2026-11-21 |
| nvdrv, nvdrv:a, nvdrv:s, nvdrv:t | `6` | `GetStatus` | — | Q | 2026-11-21 |
| nvdrv, nvdrv:a, nvdrv:s, nvdrv:t | `7` | `SetAruid` | — | Q | 2026-11-21 |
| nvdrv, nvdrv:a, nvdrv:s, nvdrv:t | `8` | `SetAruidByPID` | — | Q | 2026-11-21 |
| nvdrv, nvdrv:a, nvdrv:s, nvdrv:t | `9` | `DumpGraphicsMemoryInfo` | — | Q | 2026-11-21 |
| nvdrv, nvdrv:a, nvdrv:s, nvdrv:t | `10` | `InitializeDevtools` | 3.0.0+ | Q | 2026-11-21 |
| nvdrv, nvdrv:a, nvdrv:s, nvdrv:t | `11` | `Ioctl2` | 3.0.0+ | Q | 2026-11-21 |
| nvdrv, nvdrv:a, nvdrv:s, nvdrv:t | `12` | `Ioctl3` | 3.0.0+ | Q | 2026-11-21 |
| nvdrv, nvdrv:a, nvdrv:s, nvdrv:t | `13` | `FinishInitialize` | 3.0.0+ | Q | 2026-11-21 |
| nvmemp | `0` | `Open` | — | Q | 2026-11-21 |
| nvmemp | `1` | `GetPid` | — | Q | 2026-11-21 |
| nvdrvdbg | `0` | `OpenLog` | — | Q | 2026-11-21 |
| nvdrvdbg | `1` | `CloseLog` | — | Q | 2026-11-21 |
| nvdrvdbg | `2` | `ReadLog` | — | Q | 2026-11-21 |
| Errors | `0` | `Success` | — | Q | 2026-11-21 |
| Errors | `1` | `NotImplemented` | — | Q | 2026-11-21 |
| Errors | `2` | `NotSupported` | — | Q | 2026-11-21 |
| Errors | `3` | `NotInitialized` | — | Q | 2026-11-21 |
| Errors | `4` | `BadParameter` | — | Q | 2026-11-21 |
| Errors | `5` | `Timeout` | — | Q | 2026-11-21 |
| Errors | `6` | `InsufficientMemory` | — | Q | 2026-11-21 |
| Errors | `7` | `ReadOnlyAttribute` | — | Q | 2026-11-21 |
| Errors | `8` | `InvalidState` | — | Q | 2026-11-21 |
| Errors | `9` | `InvalidAddress` | — | Q | 2026-11-21 |
| Errors | `0xA` | `InvalidSize` | — | Q | 2026-11-21 |
| Errors | `0xB` | `BadValue` | — | Q | 2026-11-21 |
| Errors | `0xD` | `AlreadyAllocated` | — | Q | 2026-11-21 |
| Errors | `0xE` | `Busy` | — | Q | 2026-11-21 |
| Errors | `0xF` | `ResourceError` | — | Q | 2026-11-21 |
| Errors | `0x10` | `CountMismatch` | — | Q | 2026-11-21 |
| Errors | `0x1000` | `SharedMemoryTooSmall` | — | Q | 2026-11-21 |
| Errors | `0x30003` | `FileOperationFailed` | — | Q | 2026-11-21 |
| Errors | `0x30004` | `DirOperationFailed` | — | Q | 2026-11-21 |
| Errors | `0x3000F` | `IoctlFailed` | — | Q | 2026-11-21 |
| Errors | `0x30010` | `AccessDenied` | — | Q | 2026-11-21 |
| Errors | `0x30013` | `FileNotFound` | — | Q | 2026-11-21 |
| Errors | `0xA000E` | `ModuleNotPresent` | — | Q | 2026-11-21 |

### PCIe services

[Wiki SwitchBrew](https://switchbrew.org/wiki/PCIe_services) · [miroir](https://github.com/backupbrew/switchbrew/blob/master/PCIe%20services.md)

**23 commandes documentées**.

| Interface / section | ID | Fonction | Disponibilité indiquée | Encore | Vérifié |
|---|---|---|---|---|---|
| pcie | `0` | `RegisterClassDriver` | — | Q | 2026-11-21 |
| pcie | `1` | `QueryFunctionsUnregistered` | — | Q | 2026-11-21 |
| pcie | `0` | `QueryFunctions` | — | Q | 2026-11-21 |
| pcie | `1` | `AcquireFunction` | — | Q | 2026-11-21 |
| pcie | `2` | `ReleaseFunction` | — | Q | 2026-11-21 |
| pcie | `3` | `GetFunctionState` | — | Q | 2026-11-21 |
| pcie | `4` | `GetBarProfile` | — | Q | 2026-11-21 |
| pcie | `5` | `ReadConfig` | — | Q | 2026-11-21 |
| pcie | `6` | `WriteConfig` | — | Q | 2026-11-21 |
| pcie | `7` | `ReadBarRegion` | — | Q | 2026-11-21 |
| pcie | `8` | `WriteBarRegion` | — | Q | 2026-11-21 |
| pcie | `9` | `FindCapability` | — | Q | 2026-11-21 |
| pcie | `10` | `FindExtendedCapability` | — | Q | 2026-11-21 |
| pcie | `11` | `MapDma` | — | Q | 2026-11-21 |
| pcie | `12` | `UnmapDma` | — | Q | 2026-11-21 |
| pcie | `13` | `UnmapDmaBusAddress` | — | Q | 2026-11-21 |
| pcie | `14` | `GetDmaBusAddress` | — | Q | 2026-11-21 |
| pcie | `15` | `GetDmaBusAddressRange` | — | Q | 2026-11-21 |
| pcie | `16` | `SetDmaEnable` | — | Q | 2026-11-21 |
| pcie | `17` | `AcquireIrq` | — | Q | 2026-11-21 |
| pcie | `18` | `ReleaseIrq` | — | Q | 2026-11-21 |
| pcie | `19` | `SetIrqEnable` | — | Q | 2026-11-21 |
| pcie | `20` | `SetAspmEnable` | — | Q | 2026-11-21 |

### Parental Control services

[Wiki SwitchBrew](https://switchbrew.org/wiki/Parental_Control_services) · [miroir](https://github.com/backupbrew/switchbrew/blob/master/Parental%20Control%20services.md)

**98 commandes documentées**.

| Interface / section | ID | Fonction | Disponibilité indiquée | Encore | Vérifié |
|---|---|---|---|---|---|
| pctl:s, pctl:r, pctl:a, pctl | `0` | `CreateService` | — | Q | 2026-11-21 |
| pctl:s, pctl:r, pctl:a, pctl | `1` | `CreateServiceWithoutInitialize` | 4.0.0+ | Q | 2026-11-21 |
| pctl:s, pctl:r, pctl:a, pctl | `1` | `Initialize` | 4.0.0+ | Q | 2026-11-21 |
| pctl:s, pctl:r, pctl:a, pctl | `1001` | `CheckFreeCommunicationPermission` | — | Q | 2026-11-21 |
| pctl:s, pctl:r, pctl:a, pctl | `1002` | `ConfirmLaunchApplicationPermission` | — | Q | 2026-11-21 |
| pctl:s, pctl:r, pctl:a, pctl | `1003` | `ConfirmResumeApplicationPermission` | — | Q | 2026-11-21 |
| pctl:s, pctl:r, pctl:a, pctl | `1004` | `ConfirmSnsPostPermission` | — | Q | 2026-11-21 |
| pctl:s, pctl:r, pctl:a, pctl | `1005` | `ConfirmSystemSettingsPermission` | — | Q | 2026-11-21 |
| pctl:s, pctl:r, pctl:a, pctl | `1006` | `IsRestrictionTemporaryUnlocked` | — | Q | 2026-11-21 |
| pctl:s, pctl:r, pctl:a, pctl | `1007` | `RevertRestrictionTemporaryUnlocked` | — | Q | 2026-11-21 |
| pctl:s, pctl:r, pctl:a, pctl | `1008` | `EnterRestrictedSystemSettings` | — | Q | 2026-11-21 |
| pctl:s, pctl:r, pctl:a, pctl | `1009` | `LeaveRestrictedSystemSettings` | — | Q | 2026-11-21 |
| pctl:s, pctl:r, pctl:a, pctl | `1010` | `IsRestrictedSystemSettingsEntered` | — | Q | 2026-11-21 |
| pctl:s, pctl:r, pctl:a, pctl | `1011` | `RevertRestrictedSystemSettingsEntered` | — | Q | 2026-11-21 |
| pctl:s, pctl:r, pctl:a, pctl | `1012` | `GetRestrictedFeatures` | — | Q | 2026-11-21 |
| pctl:s, pctl:r, pctl:a, pctl | `1013` | `ConfirmStereoVisionPermission` | 4.0.0+ | Q | 2026-11-21 |
| pctl:s, pctl:r, pctl:a, pctl | `1014` | `ConfirmPlayableApplicationVideoOld` | 5.0.0+ | Q | 2026-11-21 |
| pctl:s, pctl:r, pctl:a, pctl | `1015` | `ConfirmPlayableApplicationVideo` | 5.0.0+ | Q | 2026-11-21 |
| pctl:s, pctl:r, pctl:a, pctl | `1016` | `ConfirmShowNewsPermission` | 6.0.0+ | Q | 2026-11-21 |
| pctl:s, pctl:r, pctl:a, pctl | `1031` | `IsRestrictionEnabled` | — | Q | 2026-11-21 |
| pctl:s, pctl:r, pctl:a, pctl | `1032` | `GetSafetyLevel` | — | Q | 2026-11-21 |
| pctl:s, pctl:r, pctl:a, pctl | `1033` | `SetSafetyLevel` | — | Q | 2026-11-21 |
| pctl:s, pctl:r, pctl:a, pctl | `1034` | `GetSafetyLevelSettings` | — | Q | 2026-11-21 |
| pctl:s, pctl:r, pctl:a, pctl | `1035` | `GetCurrentSettings` | — | Q | 2026-11-21 |
| pctl:s, pctl:r, pctl:a, pctl | `1036` | `SetCustomSafetyLevelSettings` | — | Q | 2026-11-21 |
| pctl:s, pctl:r, pctl:a, pctl | `1037` | `GetDefaultRatingOrganization` | — | Q | 2026-11-21 |
| pctl:s, pctl:r, pctl:a, pctl | `1038` | `SetDefaultRatingOrganization` | — | Q | 2026-11-21 |
| pctl:s, pctl:r, pctl:a, pctl | `1039` | `GetFreeCommunicationApplicationListCount` | — | Q | 2026-11-21 |
| pctl:s, pctl:r, pctl:a, pctl | `1042` | `AddToFreeCommunicationApplicationList` | — | Q | 2026-11-21 |
| pctl:s, pctl:r, pctl:a, pctl | `1043` | `DeleteSettings` | — | Q | 2026-11-21 |
| pctl:s, pctl:r, pctl:a, pctl | `1044` | `GetFreeCommunicationApplicationList` | — | Q | 2026-11-21 |
| pctl:s, pctl:r, pctl:a, pctl | `1045` | `UpdateFreeCommunicationApplicationList` | — | Q | 2026-11-21 |
| pctl:s, pctl:r, pctl:a, pctl | `1046` | `DisableFeaturesForReset` | — | Q | 2026-11-21 |
| pctl:s, pctl:r, pctl:a, pctl | `1047` | `NotifyApplicationDownloadStarted` | 3.0.0+ | Q | 2026-11-21 |
| pctl:s, pctl:r, pctl:a, pctl | `1048` | `NotifyNetworkProfileCreated` | 6.0.0+ | Q | 2026-11-21 |
| pctl:s, pctl:r, pctl:a, pctl | `1061` | `ConfirmStereoVisionRestrictionConfigurable` | 4.0.0+ | Q | 2026-11-21 |
| pctl:s, pctl:r, pctl:a, pctl | `1062` | `GetStereoVisionRestriction` | 4.0.0+ | Q | 2026-11-21 |
| pctl:s, pctl:r, pctl:a, pctl | `1063` | `SetStereoVisionRestriction` | 4.0.0+ | Q | 2026-11-21 |
| pctl:s, pctl:r, pctl:a, pctl | `1064` | `ResetConfirmedStereoVisionPermission` | 5.0.0+ | Q | 2026-11-21 |
| pctl:s, pctl:r, pctl:a, pctl | `1065` | `IsStereoVisionPermitted` | 5.0.0+ | Q | 2026-11-21 |
| pctl:s, pctl:r, pctl:a, pctl | `1201` | `UnlockRestrictionTemporarily` | — | Q | 2026-11-21 |
| pctl:s, pctl:r, pctl:a, pctl | `1202` | `UnlockSystemSettingsRestriction` | — | Q | 2026-11-21 |
| pctl:s, pctl:r, pctl:a, pctl | `1203` | `SetPinCode` | — | Q | 2026-11-21 |
| pctl:s, pctl:r, pctl:a, pctl | `1204` | `GenerateInquiryCode` | — | Q | 2026-11-21 |
| pctl:s, pctl:r, pctl:a, pctl | `1205` | `CheckMasterKey` | — | Q | 2026-11-21 |
| pctl:s, pctl:r, pctl:a, pctl | `1206` | `GetPinCodeLength` | — | Q | 2026-11-21 |
| pctl:s, pctl:r, pctl:a, pctl | `1207` | `GetPinCodeChangedEvent` | — | Q | 2026-11-21 |
| pctl:s, pctl:r, pctl:a, pctl | `1208` | `GetPinCode` | 4.0.0+ | Q | 2026-11-21 |
| pctl:s, pctl:r, pctl:a, pctl | `1403` | `IsPairingActive` | — | Q | 2026-11-21 |
| pctl:s, pctl:r, pctl:a, pctl | `1406` | `GetSettingsLastUpdated` | — | Q | 2026-11-21 |
| pctl:s, pctl:r, pctl:a, pctl | `1411` | `GetPairingAccountInfo` | — | Q | 2026-11-21 |
| pctl:s, pctl:r, pctl:a, pctl | `1421` | `GetAccountNickname` | — | Q | 2026-11-21 |
| pctl:s, pctl:r, pctl:a, pctl | `1424` | `GetAccountState` | — | Q | 2026-11-21 |
| pctl:s, pctl:r, pctl:a, pctl | `1425` | `RequestPostEvents` | 6.0.0+ | Q | 2026-11-21 |
| pctl:s, pctl:r, pctl:a, pctl | `1432` | `GetSynchronizationEvent` | — | Q | 2026-11-21 |
| pctl:s, pctl:r, pctl:a, pctl | `1451` | `StartPlayTimer` | — | Q | 2026-11-21 |
| pctl:s, pctl:r, pctl:a, pctl | `1452` | `StopPlayTimer` | — | Q | 2026-11-21 |
| pctl:s, pctl:r, pctl:a, pctl | `1453` | `IsPlayTimerEnabled` | — | Q | 2026-11-21 |
| pctl:s, pctl:r, pctl:a, pctl | `1454` | `GetPlayTimerRemainingTime` | — | Q | 2026-11-21 |
| pctl:s, pctl:r, pctl:a, pctl | `1455` | `IsRestrictedByPlayTimer` | — | Q | 2026-11-21 |
| pctl:s, pctl:r, pctl:a, pctl | `1456` | `GetPlayTimerSettings` | — | Q | 2026-11-21 |
| pctl:s, pctl:r, pctl:a, pctl | `1457` | `GetPlayTimerEventToRequestSuspension` | — | Q | 2026-11-21 |
| pctl:s, pctl:r, pctl:a, pctl | `1458` | `IsPlayTimerAlarmDisabled` | 4.0.0+ | Q | 2026-11-21 |
| pctl:s, pctl:r, pctl:a, pctl | `1471` | `NotifyWrongPinCodeInputManyTimes` | — | Q | 2026-11-21 |
| pctl:s, pctl:r, pctl:a, pctl | `1472` | `CancelNetworkRequest` | — | Q | 2026-11-21 |
| pctl:s, pctl:r, pctl:a, pctl | `1473` | `GetUnlinkedEvent` | — | Q | 2026-11-21 |
| pctl:s, pctl:r, pctl:a, pctl | `1474` | `ClearUnlinkedEvent` | — | Q | 2026-11-21 |
| pctl:s, pctl:r, pctl:a, pctl | `1601` | `DisableAllFeatures` | — | Q | 2026-11-21 |
| pctl:s, pctl:r, pctl:a, pctl | `1602` | `PostEnableAllFeatures` | — | Q | 2026-11-21 |
| pctl:s, pctl:r, pctl:a, pctl | `1603` | `IsAllFeaturesDisabled` | — | Q | 2026-11-21 |
| pctl:s, pctl:r, pctl:a, pctl | `1901` | `DeleteFromFreeCommunicationApplicationListForDebug` | — | Q | 2026-11-21 |
| pctl:s, pctl:r, pctl:a, pctl | `1902` | `ClearFreeCommunicationApplicationListForDebug` | — | Q | 2026-11-21 |
| pctl:s, pctl:r, pctl:a, pctl | `1903` | `GetExemptApplicationListCountForDebug` | 5.0.0+ | Q | 2026-11-21 |
| pctl:s, pctl:r, pctl:a, pctl | `1904` | `GetExemptApplicationListForDebug` | 5.0.0+ | Q | 2026-11-21 |
| pctl:s, pctl:r, pctl:a, pctl | `1905` | `UpdateExemptApplicationListForDebug` | 5.0.0+ | Q | 2026-11-21 |
| pctl:s, pctl:r, pctl:a, pctl | `1906` | `AddToExemptApplicationListForDebug` | 5.0.0+ | Q | 2026-11-21 |
| pctl:s, pctl:r, pctl:a, pctl | `1907` | `DeleteFromExemptApplicationListForDebug` | 5.0.0+ | Q | 2026-11-21 |
| pctl:s, pctl:r, pctl:a, pctl | `1908` | `ClearExemptApplicationListForDebug` | 5.0.0+ | Q | 2026-11-21 |
| pctl:s, pctl:r, pctl:a, pctl | `1941` | `DeletePairing` | — | Q | 2026-11-21 |
| pctl:s, pctl:r, pctl:a, pctl | `1951` | `SetPlayTimerSettingsForDebug` | — | Q | 2026-11-21 |
| pctl:s, pctl:r, pctl:a, pctl | `1952` | `GetPlayTimerSpentTimeForTest` | — | Q | 2026-11-21 |
| pctl:s, pctl:r, pctl:a, pctl | `1953` | `SetPlayTimerAlarmDisabledForDebug` | 4.0.0+ | Q | 2026-11-21 |
| pctl:s, pctl:r, pctl:a, pctl | `2001` | `RequestPairingAsync` | — | Q | 2026-11-21 |
| pctl:s, pctl:r, pctl:a, pctl | `2002` | `FinishRequestPairing` | — | Q | 2026-11-21 |
| pctl:s, pctl:r, pctl:a, pctl | `2003` | `AuthorizePairingAsync` | — | Q | 2026-11-21 |
| pctl:s, pctl:r, pctl:a, pctl | `2004` | `FinishAuthorizePairing` | — | Q | 2026-11-21 |
| pctl:s, pctl:r, pctl:a, pctl | `2005` | `RetrievePairingInfoAsync` | — | Q | 2026-11-21 |
| pctl:s, pctl:r, pctl:a, pctl | `2006` | `FinishRetrievePairingInfo` | — | Q | 2026-11-21 |
| pctl:s, pctl:r, pctl:a, pctl | `2007` | `UnlinkPairingAsync` | — | Q | 2026-11-21 |
| pctl:s, pctl:r, pctl:a, pctl | `2008` | `FinishUnlinkPairing` | — | Q | 2026-11-21 |
| pctl:s, pctl:r, pctl:a, pctl | `2009` | `GetAccountMiiImageAsync` | — | Q | 2026-11-21 |
| pctl:s, pctl:r, pctl:a, pctl | `2010` | `FinishGetAccountMiiImage` | — | Q | 2026-11-21 |
| pctl:s, pctl:r, pctl:a, pctl | `2011` | `GetAccountMiiImageContentTypeAsync` | — | Q | 2026-11-21 |
| pctl:s, pctl:r, pctl:a, pctl | `2012` | `FinishGetAccountMiiImageContentType` | — | Q | 2026-11-21 |
| pctl:s, pctl:r, pctl:a, pctl | `2013` | `SynchronizeParentalControlSettingsAsync` | — | Q | 2026-11-21 |
| pctl:s, pctl:r, pctl:a, pctl | `2014` | `FinishSynchronizeParentalControlSettings` | — | Q | 2026-11-21 |
| pctl:s, pctl:r, pctl:a, pctl | `2015` | `FinishSynchronizeParentalControlSettingsWithLastUpdated` | — | Q | 2026-11-21 |
| pctl:s, pctl:r, pctl:a, pctl | `2016` | `RequestUpdateExemptionListAsync` | 5.0.0+ | Q | 2026-11-21 |

### Process Manager services

[Wiki SwitchBrew](https://switchbrew.org/wiki/Process_Manager_services) · [miroir](https://github.com/backupbrew/switchbrew/blob/master/Process%20Manager%20services.md)

**10 commandes documentées**.

| Interface / section | ID | Fonction | Disponibilité indiquée | Encore | Vérifié |
|---|---|---|---|---|---|
| pm:bm | `0` | `GetBootMode` | — | Q | 2026-11-21 |
| pm:bm | `1` | `SetMaintenanceBoot` | — | Q | 2026-11-21 |
| pm:info | `0` | `GetProgramId` | — | Q | 2026-11-21 |
| pm:shell | `0` | `LaunchProgram` | — | Q | 2026-11-21 |
| pm:shell | `1` | `TerminateProcess` | — | Q | 2026-11-21 |
| pm:shell | `2` | `TerminateProgram` | — | Q | 2026-11-21 |
| pm:shell | `3` | `GetProcessEventHandle` | — | Q | 2026-11-21 |
| pm:shell | `4` | `GetProcessEventInfo` | — | Q | 2026-11-21 |
| pm:shell | `8` | `BoostApplicationThreadResourceLimit` | 7.0.0+ | Q | 2026-11-21 |
| pm:shell | `9` | `GetBootFinishedEventHandle` | 8.0.0+ | Q | 2026-11-21 |

### PSC services

[Wiki SwitchBrew](https://switchbrew.org/wiki/PSC_services) · [miroir](https://github.com/backupbrew/switchbrew/blob/master/PSC%20services.md)

**88 commandes documentées**.

| Interface / section | ID | Fonction | Disponibilité indiquée | Encore | Vérifié |
|---|---|---|---|---|---|
| psc:c | `0` | `Initialize` | — | Q | 2026-11-21 |
| psc:c | `1` | `DispatchRequest` | — | Q | 2026-11-21 |
| psc:c | `2` | `GetResult` | — | Q | 2026-11-21 |
| psc:c | `3` | `GetState` | — | Q | 2026-11-21 |
| psc:c | `4` | `Cancel` | — | Q | 2026-11-21 |
| psc:c | `5` | `PrintModuleInformation` | 1.0.0-6.2.0 | Q | 2026-11-21 |
| psc:c | `6` | `GetModuleInformation` | — | Q | 2026-11-21 |
| psc:m | `0` | `GetPmModule` | — | Q | 2026-11-21 |
| psc:m | `0` | `Initialize` | — | Q | 2026-11-21 |
| psc:m | `1` | `GetRequest` | — | Q | 2026-11-21 |
| psc:m | `2` | `Acknowledge` | — | Q | 2026-11-21 |
| psc:m | `3` | `Finalize` | — | Q | 2026-11-21 |
| psc:m | `4` | `AcknowledgeEx` | 5.1.0+ | Q | 2026-11-21 |
| ovln:rcv | `0` | `OpenReceiver` | — | Q | 2026-11-21 |
| ovln:rcv | `0` | `AddSource` | — | Q | 2026-11-21 |
| ovln:rcv | `1` | `RemoveSource` | — | Q | 2026-11-21 |
| ovln:rcv | `2` | `GetReceiveEventHandle` | — | Q | 2026-11-21 |
| ovln:rcv | `3` | `Receive` | — | Q | 2026-11-21 |
| ovln:rcv | `4` | `ReceiveWithTick` | — | Q | 2026-11-21 |
| ovln:snd | `0` | `OpenSender` | — | Q | 2026-11-21 |
| ovln:snd | `0` | `Send` | — | Q | 2026-11-21 |
| ovln:snd | `1` | `GetUnreceivedMessageCount` | — | Q | 2026-11-21 |
| time:m | `0` | `GetUserStaticService` | — | Q | 2026-11-21 |
| time:m | `5` | `GetAdminStaticService` | — | Q | 2026-11-21 |
| time:m | `6` | `GetRepairStaticService` | — | Q | 2026-11-21 |
| time:m | `9` | `GetManufactureStaticService` | — | Q | 2026-11-21 |
| time:m | `10` | `SetupStandardSteadyClock` | — | Q | 2026-11-21 |
| time:m | `11` | `SetupStandardLocalSystemClock` | — | Q | 2026-11-21 |
| time:m | `12` | `SetupStandardNetworkSystemClock` | — | Q | 2026-11-21 |
| time:m | `13` | `SetupStandardUserSystemClock` | — | Q | 2026-11-21 |
| time:m | `14` | `SetupTimeZoneManager` | — | Q | 2026-11-21 |
| time:m | `15` | `SetupEphemeralNetworkSystemClock` | — | Q | 2026-11-21 |
| time:m | `60` | `GetStandardUserSystemClockAutomaticCorrectionEvent` | — | Q | 2026-11-21 |
| time:m | `100` | `SetStandardSteadyClockRtcOffset` | — | Q | 2026-11-21 |
| time:m | `200` | `GetAlarmRegistrationEvent` | — | Q | 2026-11-21 |
| time:m | `201` | `UpdateSteadyAlarms` | — | Q | 2026-11-21 |
| time:al | `0` | `GetWakeUpEvent` | — | Q | 2026-11-21 |
| time:al | `1` | `Enable` | — | Q | 2026-11-21 |
| time:al | `2` | `Disable` | — | Q | 2026-11-21 |
| time:al | `3` | `IsEnabled` | — | Q | 2026-11-21 |
| time:su, time:s | `0` | `GetStandardUserSystemClock` | — | Q | 2026-11-21 |
| time:su, time:s | `1` | `GetStandardNetworkSystemClock` | — | Q | 2026-11-21 |
| time:su, time:s | `2` | `GetStandardSteadyClock` | — | Q | 2026-11-21 |
| time:su, time:s | `3` | `GetTimeZoneService` | — | Q | 2026-11-21 |
| time:su, time:s | `4` | `GetStandardLocalSystemClock` | — | Q | 2026-11-21 |
| time:su, time:s | `5` | `GetEphemeralNetworkSystemClock` | 4.0.0+ | Q | 2026-11-21 |
| time:su, time:s | `20` | `GetSharedMemoryNativeHandle` | 6.0.0+ | Q | 2026-11-21 |
| time:su, time:s | `30` | `GetStandardNetworkClockOperationEventReadableHandle` | 6.0.0-8.1.0 | Q | 2026-11-21 |
| time:su, time:s | `31` | `GetEphemeralNetworkClockOperationEventReadableHandle` | 6.0.0-8.1.0 | Q | 2026-11-21 |
| time:su, time:s | `50` | `SetStandardSteadyClockInternalOffset` | 4.0.0+ | Q | 2026-11-21 |
| time:su, time:s | `51` | `GetStandardSteadyClockRtcValue` | 9.0.0+ | Q | 2026-11-21 |
| time:su, time:s | `100` | `IsStandardUserSystemClockAutomaticCorrectionEnabled` | — | Q | 2026-11-21 |
| time:su, time:s | `101` | `SetStandardUserSystemClockAutomaticCorrectionEnabled` | — | Q | 2026-11-21 |
| time:su, time:s | `102` | `GetStandardUserSystemClockInitialYear` | 5.0.0+ | Q | 2026-11-21 |
| time:su, time:s | `200` | `IsStandardNetworkSystemClockAccuracySufficient` | 3.0.0+ | Q | 2026-11-21 |
| time:su, time:s | `201` | `GetStandardUserSystemClockAutomaticCorrectionUpdatedTime` | 6.0.0+ | Q | 2026-11-21 |
| time:su, time:s | `300` | `CalculateMonotonicSystemClockBaseTimePoint` | 4.0.0+ | Q | 2026-11-21 |
| time:su, time:s | `400` | `GetClockSnapshot` | 4.0.0+ | Q | 2026-11-21 |
| time:su, time:s | `401` | `GetClockSnapshotFromSystemClockContext` | 4.0.0+ | Q | 2026-11-21 |
| time:su, time:s | `500` | `CalculateStandardUserSystemClockDifferenceByUser` | 4.0.0+ | Q | 2026-11-21 |
| time:su, time:s | `501` | `CalculateSpanBetween` | 4.0.0+ | Q | 2026-11-21 |
| time:su, time:s | `0` | `GetCurrentTimePoint` | — | Q | 2026-11-21 |
| time:su, time:s | `2` | `GetTestOffset` | — | Q | 2026-11-21 |
| time:su, time:s | `3` | `SetTestOffset` | — | Q | 2026-11-21 |
| time:su, time:s | `100` | `GetRtcValue` | 2.0.0+ | Q | 2026-11-21 |
| time:su, time:s | `101` | `IsRtcResetDetected` | 2.0.0+ | Q | 2026-11-21 |
| time:su, time:s | `102` | `GetSetupResultValue` | 2.0.0+ | Q | 2026-11-21 |
| time:su, time:s | `200` | `GetInternalOffset` | 3.0.0+ | Q | 2026-11-21 |
| time:su, time:s | `201` | `SetInternalOffset` | 3.0.0-3.0.2 | Q | 2026-11-21 |
| time:su, time:s | `0` | `GetCurrentTime` | — | Q | 2026-11-21 |
| time:su, time:s | `1` | `SetCurrentTime` | — | Q | 2026-11-21 |
| time:su, time:s | `2` | `GetSystemClockContext` | — | Q | 2026-11-21 |
| time:su, time:s | `3` | `SetSystemClockContext` | — | Q | 2026-11-21 |
| time:su, time:s | `4` | `GetOperationEventReadableHandle` | 9.0.0+ | Q | 2026-11-21 |
| time:su, time:s | `0` | `GetDeviceLocationName` | — | Q | 2026-11-21 |
| time:su, time:s | `1` | `SetDeviceLocationName` | — | Q | 2026-11-21 |
| time:su, time:s | `2` | `GetTotalLocationNameCount` | — | Q | 2026-11-21 |
| time:su, time:s | `3` | `LoadLocationNameList` | — | Q | 2026-11-21 |
| time:su, time:s | `4` | `LoadTimeZoneRule` | — | Q | 2026-11-21 |
| time:su, time:s | `5` | `GetTimeZoneRuleVersion` | 2.0.0+ | Q | 2026-11-21 |
| time:su, time:s | `6` | `GetDeviceLocationNameAndUpdatedTime` | 5.0.0+ | Q | 2026-11-21 |
| time:su, time:s | `7` | `SetDeviceLocationNameWithTimeZoneRule` | 9.0.0+ | Q | 2026-11-21 |
| time:su, time:s | `8` | `ParseTimeZoneBinary` | 9.0.0+ | Q | 2026-11-21 |
| time:su, time:s | `20` | `GetDeviceLocationNameOperationEventReadableHandle` | 9.0.0+ | Q | 2026-11-21 |
| time:su, time:s | `100` | `ToCalendarTime` | — | Q | 2026-11-21 |
| time:su, time:s | `101` | `ToCalendarTimeWithMyRule` | — | Q | 2026-11-21 |
| time:su, time:s | `201` | `ToPosixTime` | — | Q | 2026-11-21 |
| time:su, time:s | `202` | `ToPosixTimeWithMyRule` | — | Q | 2026-11-21 |

### RO services

[Wiki SwitchBrew](https://switchbrew.org/wiki/RO_services) · [miroir](https://github.com/backupbrew/switchbrew/blob/master/RO%20services.md)

**6 commandes documentées**.

| Interface / section | ID | Fonction | Disponibilité indiquée | Encore | Vérifié |
|---|---|---|---|---|---|
| ldr:ro, ro:1 | `0` | `LoadNro` | — | Q | 2026-11-21 |
| ldr:ro, ro:1 | `1` | `UnloadNro` | — | Q | 2026-11-21 |
| ldr:ro, ro:1 | `2` | `LoadNrr` | — | Q | 2026-11-21 |
| ldr:ro, ro:1 | `3` | `UnloadNrr` | — | Q | 2026-11-21 |
| ldr:ro, ro:1 | `4` | `Initialize` | — | Q | 2026-11-21 |
| ldr:ro, ro:1 | `10` | `LoadNrrEx` | 7.0.0+ | Q | 2026-11-21 |

### Settings services

[Wiki SwitchBrew](https://switchbrew.org/wiki/Settings_services) · [miroir](https://github.com/backupbrew/switchbrew/blob/master/Settings%20services.md)

**250 commandes documentées**.

| Interface / section | ID | Fonction | Disponibilité indiquée | Encore | Vérifié |
|---|---|---|---|---|---|
| set | `0` | `GetLanguageCode` | — | Q | 2026-11-21 |
| set | `1` | `GetAvailableLanguageCodes` | — | Q | 2026-11-21 |
| set | `2` | `MakeLanguageCode` | 4.0.0+ | Q | 2026-11-21 |
| set | `3` | `GetAvailableLanguageCodeCount` | — | Q | 2026-11-21 |
| set | `4` | `GetRegionCode` | — | Q | 2026-11-21 |
| set | `5` | `GetAvailableLanguageCodes2` | 4.0.0+ | Q | 2026-11-21 |
| set | `6` | `GetAvailableLanguageCodeCount2` | 4.0.0+ | Q | 2026-11-21 |
| set | `7` | `GetKeyCodeMap` | 4.0.0+ | Q | 2026-11-21 |
| set | `8` | `GetQuestFlag` | 5.0.0+ | Q | 2026-11-21 |
| set | `9` | `GetKeyCodeMap2` | 6.0.0+ | Q | 2026-11-21 |
| set | `10` | `GetFirmwareVersionForDebug` | 9.0.0+ | Q | 2026-11-21 |
| set:fd | `2` | `SetSettingsItemValue` | — | Q | 2026-11-21 |
| set:fd | `3` | `ResetSettingsItemValue` | — | Q | 2026-11-21 |
| set:fd | `4` | `[CreateSettingsItemKeyIterator](#ISettingsItemKeyIterator "wikilink")` | — | Q | 2026-11-21 |
| set:fd | `10` | `ReadSettings` | 4.0.0+ | Q | 2026-11-21 |
| set:fd | `11` | `ResetSettings` | 4.0.0+ | Q | 2026-11-21 |
| set:fd | `20` | `SetWebInspectorFlag` | 4.0.0+ | Q | 2026-11-21 |
| set:fd | `21` | `SetAllowedSslHosts` | 4.0.0+ | Q | 2026-11-21 |
| set:fd | `22` | `SetHostFsMountPoint` | 4.0.0+ | Q | 2026-11-21 |
| set:fd | `23` | `SetMemoryUsageRateFlag` | 9.0.0+ | Q | 2026-11-21 |
| set:fd | `0` | `GoNext` | — | Q | 2026-11-21 |
| set:fd | `1` | `GetKeySize` | — | Q | 2026-11-21 |
| set:fd | `2` | `GetKey` | — | Q | 2026-11-21 |
| set:cal | `0` | `GetBluetoothBdAddress` | — | Q | 2026-11-21 |
| set:cal | `1` | `GetConfigurationId1` | — | Q | 2026-11-21 |
| set:cal | `2` | `GetAccelerometerOffset` | — | Q | 2026-11-21 |
| set:cal | `3` | `GetAccelerometerScale` | — | Q | 2026-11-21 |
| set:cal | `4` | `GetGyroscopeOffset` | — | Q | 2026-11-21 |
| set:cal | `5` | `GetGyroscopeScale` | — | Q | 2026-11-21 |
| set:cal | `6` | `GetWirelessLanMacAddress` | — | Q | 2026-11-21 |
| set:cal | `7` | `GetWirelessLanCountryCodeCount` | — | Q | 2026-11-21 |
| set:cal | `8` | `GetWirelessLanCountryCodes` | — | Q | 2026-11-21 |
| set:cal | `9` | `GetSerialNumber` | — | Q | 2026-11-21 |
| set:cal | `10` | `SetInitialSystemAppletProgramId` | — | Q | 2026-11-21 |
| set:cal | `11` | `SetOverlayDispProgramId` | — | Q | 2026-11-21 |
| set:cal | `12` | `GetBatteryLot` | — | Q | 2026-11-21 |
| set:cal | `14` | `GetEciDeviceCertificate` | — | Q | 2026-11-21 |
| set:cal | `15` | `GetEticketDeviceCertificate` | — | Q | 2026-11-21 |
| set:cal | `16` | `GetSslKey` | — | Q | 2026-11-21 |
| set:cal | `17` | `GetSslCertificate` | — | Q | 2026-11-21 |
| set:cal | `18` | `GetGameCardKey` | — | Q | 2026-11-21 |
| set:cal | `19` | `GetGameCardCertificate` | — | Q | 2026-11-21 |
| set:cal | `20` | `GetEciDeviceKey` | — | Q | 2026-11-21 |
| set:cal | `21` | `GetEticketDeviceKey` | — | Q | 2026-11-21 |
| set:cal | `22` | `GetSpeakerParameter` | — | Q | 2026-11-21 |
| set:cal | `23` | `GetLcdVendorId` | 4.0.0+ | Q | 2026-11-21 |
| set:cal | `24` | `GetEciDeviceCertificate2` | 5.0.0+ | Q | 2026-11-21 |
| set:cal | `25` | `GetEciDeviceKey2` | 5.0.0+ | Q | 2026-11-21 |
| set:cal | `26` | `GetAmiiboKey` | 5.0.0+ | Q | 2026-11-21 |
| set:cal | `27` | `GetAmiiboEcqvCertificate` | 5.0.0+ | Q | 2026-11-21 |
| set:cal | `28` | `GetAmiiboEcdsaCertificate` | 5.0.0+ | Q | 2026-11-21 |
| set:cal | `29` | `GetAmiiboEcqvBlsKey` | 5.0.0+ | Q | 2026-11-21 |
| set:cal | `30` | `GetAmiiboEcqvBlsCertificate` | 5.0.0+ | Q | 2026-11-21 |
| set:cal | `31` | `GetAmiiboEcqvBlsRootCertificate` | 5.0.0+ | Q | 2026-11-21 |
| set:cal | `32` | `GetUsbTypeCPowerSourceCircuitVersion` | 5.0.0+ | Q | 2026-11-21 |
| set:cal | `33` | `GetAnalogStickModuleTypeL` | 9.0.0+ | Q | 2026-11-21 |
| set:cal | `34` | `GetAnalogStickModelParameterL` | 9.0.0+ | Q | 2026-11-21 |
| set:cal | `35` | `GetAnalogStickFactoryCalibrationL` | 9.0.0+ | Q | 2026-11-21 |
| set:cal | `36` | `GetAnalogStickModuleTypeR` | 9.0.0+ | Q | 2026-11-21 |
| set:cal | `37` | `GetAnalogStickModelParameterR` | 9.0.0+ | Q | 2026-11-21 |
| set:cal | `38` | `GetAnalogStickFactoryCalibrationR` | 9.0.0+ | Q | 2026-11-21 |
| set:cal | `39` | `GetConsoleSixAxisSensorModuleType` | 9.0.0+ | Q | 2026-11-21 |
| set:cal | `40` | `GetConsoleSixAxisSensorHorizontalOffset` | 9.0.0+ | Q | 2026-11-21 |
| set:cal | `41` | `GetBatteryVersion` | 6.0.0+ | Q | 2026-11-21 |
| set:sys | `0` | `SetLanguageCode` | — | Q | 2026-11-21 |
| set:sys | `1` | `SetNetworkSettings` | — | Q | 2026-11-21 |
| set:sys | `2` | `GetNetworkSettings` | — | Q | 2026-11-21 |
| set:sys | `3` | `GetFirmwareVersion` | — | Q | 2026-11-21 |
| set:sys | `4` | `GetFirmwareVersion2` | 3.0.0+ | Q | 2026-11-21 |
| set:sys | `5` | `GetFirmwareVersionDigest` | 5.0.0+ | Q | 2026-11-21 |
| set:sys | `7` | `GetLockScreenFlag` | — | Q | 2026-11-21 |
| set:sys | `8` | `SetLockScreenFlag` | — | Q | 2026-11-21 |
| set:sys | `9` | `GetBacklightSettings` | — | Q | 2026-11-21 |
| set:sys | `10` | `SetBacklightSettings` | — | Q | 2026-11-21 |
| set:sys | `11` | `SetBluetoothDevicesSettings` | — | Q | 2026-11-21 |
| set:sys | `12` | `GetBluetoothDevicesSettings` | — | Q | 2026-11-21 |
| set:sys | `13` | `GetExternalSteadyClockSourceId` | — | Q | 2026-11-21 |
| set:sys | `14` | `SetExternalSteadyClockSourceId` | — | Q | 2026-11-21 |
| set:sys | `15` | `GetUserSystemClockContext` | — | Q | 2026-11-21 |
| set:sys | `16` | `SetUserSystemClockContext` | — | Q | 2026-11-21 |
| set:sys | `17` | `GetAccountSettings` | — | Q | 2026-11-21 |
| set:sys | `18` | `SetAccountSettings` | — | Q | 2026-11-21 |
| set:sys | `19` | `GetAudioVolume` | — | Q | 2026-11-21 |
| set:sys | `20` | `SetAudioVolume` | — | Q | 2026-11-21 |
| set:sys | `21` | `GetEulaVersions` | — | Q | 2026-11-21 |
| set:sys | `22` | `SetEulaVersions` | — | Q | 2026-11-21 |
| set:sys | `23` | `GetColorSetId` | — | Q | 2026-11-21 |
| set:sys | `24` | `SetColorSetId` | — | Q | 2026-11-21 |
| set:sys | `25` | `GetConsoleInformationUploadFlag` | — | Q | 2026-11-21 |
| set:sys | `26` | `SetConsoleInformationUploadFlag` | — | Q | 2026-11-21 |
| set:sys | `27` | `GetAutomaticApplicationDownloadFlag` | — | Q | 2026-11-21 |
| set:sys | `28` | `SetAutomaticApplicationDownloadFlag` | — | Q | 2026-11-21 |
| set:sys | `29` | `GetNotificationSettings` | — | Q | 2026-11-21 |
| set:sys | `30` | `SetNotificationSettings` | — | Q | 2026-11-21 |
| set:sys | `31` | `GetAccountNotificationSettings` | — | Q | 2026-11-21 |
| set:sys | `32` | `SetAccountNotificationSettings` | — | Q | 2026-11-21 |
| set:sys | `35` | `GetVibrationMasterVolume` | — | Q | 2026-11-21 |
| set:sys | `36` | `SetVibrationMasterVolume` | — | Q | 2026-11-21 |
| set:sys | `37` | `GetSettingsItemValueSize` | — | Q | 2026-11-21 |
| set:sys | `38` | `GetSettingsItemValue` | — | Q | 2026-11-21 |
| set:sys | `39` | `GetTvSettings` | — | Q | 2026-11-21 |
| set:sys | `40` | `SetTvSettings` | — | Q | 2026-11-21 |
| set:sys | `41` | `GetEdid` | — | Q | 2026-11-21 |
| set:sys | `42` | `SetEdid` | — | Q | 2026-11-21 |
| set:sys | `43` | `GetAudioOutputMode` | — | Q | 2026-11-21 |
| set:sys | `44` | `SetAudioOutputMode` | — | Q | 2026-11-21 |
| set:sys | `45` | `IsForceMuteOnHeadphoneRemoved` | — | Q | 2026-11-21 |
| set:sys | `46` | `SetForceMuteOnHeadphoneRemoved` | — | Q | 2026-11-21 |
| set:sys | `47` | `GetQuestFlag` | — | Q | 2026-11-21 |
| set:sys | `48` | `SetQuestFlag` | — | Q | 2026-11-21 |
| set:sys | `49` | `GetDataDeletionSettings` | — | Q | 2026-11-21 |
| set:sys | `50` | `SetDataDeletionSettings` | — | Q | 2026-11-21 |
| set:sys | `51` | `GetInitialSystemAppletProgramId` | — | Q | 2026-11-21 |
| set:sys | `52` | `GetOverlayDispProgramId` | — | Q | 2026-11-21 |
| set:sys | `53` | `GetDeviceTimeZoneLocationName` | — | Q | 2026-11-21 |
| set:sys | `54` | `SetDeviceTimeZoneLocationName` | — | Q | 2026-11-21 |
| set:sys | `55` | `GetWirelessCertificationFileSize` | — | Q | 2026-11-21 |
| set:sys | `56` | `[GetWirelessCertificationFile](Flash%20Filesystem#PRODINFOF.md##PRODINFOF "wikilink")` | — | Q | 2026-11-21 |
| set:sys | `57` | `SetRegionCode` | — | Q | 2026-11-21 |
| set:sys | `58` | `GetNetworkSystemClockContext` | — | Q | 2026-11-21 |
| set:sys | `59` | `SetNetworkSystemClockContext` | — | Q | 2026-11-21 |
| set:sys | `60` | `IsUserSystemClockAutomaticCorrectionEnabled` | — | Q | 2026-11-21 |
| set:sys | `61` | `SetUserSystemClockAutomaticCorrectionEnabled` | — | Q | 2026-11-21 |
| set:sys | `62` | `GetDebugModeFlag` | — | Q | 2026-11-21 |
| set:sys | `63` | `GetPrimaryAlbumStorage` | — | Q | 2026-11-21 |
| set:sys | `64` | `SetPrimaryAlbumStorage` | — | Q | 2026-11-21 |
| set:sys | `65` | `GetUsb30EnableFlag` | — | Q | 2026-11-21 |
| set:sys | `66` | `SetUsb30EnableFlag` | — | Q | 2026-11-21 |
| set:sys | `67` | `GetBatteryLot` | — | Q | 2026-11-21 |
| set:sys | `68` | `GetSerialNumber` | — | Q | 2026-11-21 |
| set:sys | `69` | `GetNfcEnableFlag` | — | Q | 2026-11-21 |
| set:sys | `70` | `SetNfcEnableFlag` | — | Q | 2026-11-21 |
| set:sys | `71` | `GetSleepSettings` | — | Q | 2026-11-21 |
| set:sys | `72` | `SetSleepSettings` | — | Q | 2026-11-21 |
| set:sys | `73` | `GetWirelessLanEnableFlag` | — | Q | 2026-11-21 |
| set:sys | `74` | `SetWirelessLanEnableFlag` | — | Q | 2026-11-21 |
| set:sys | `75` | `GetInitialLaunchSettings` | — | Q | 2026-11-21 |
| set:sys | `76` | `SetInitialLaunchSettings` | — | Q | 2026-11-21 |
| set:sys | `77` | `GetDeviceNickName` | — | Q | 2026-11-21 |
| set:sys | `78` | `SetDeviceNickName` | — | Q | 2026-11-21 |
| set:sys | `79` | `GetProductModel` | — | Q | 2026-11-21 |
| set:sys | `80` | `GetLdnChannel` | — | Q | 2026-11-21 |
| set:sys | `81` | `SetLdnChannel` | — | Q | 2026-11-21 |
| set:sys | `82` | `AcquireTelemetryDirtyFlagEventHandle` | — | Q | 2026-11-21 |
| set:sys | `83` | `GetTelemetryDirtyFlags` | — | Q | 2026-11-21 |
| set:sys | `84` | `GetPtmBatteryLot` | — | Q | 2026-11-21 |
| set:sys | `85` | `SetPtmBatteryLot` | — | Q | 2026-11-21 |
| set:sys | `86` | `GetPtmFuelGaugeParameter` | — | Q | 2026-11-21 |
| set:sys | `87` | `SetPtmFuelGaugeParameter` | — | Q | 2026-11-21 |
| set:sys | `88` | `GetBluetoothEnableFlag` | — | Q | 2026-11-21 |
| set:sys | `89` | `SetBluetoothEnableFlag` | — | Q | 2026-11-21 |
| set:sys | `90` | `GetMiiAuthorId` | — | Q | 2026-11-21 |
| set:sys | `91` | `SetShutdownRtcValue` | — | Q | 2026-11-21 |
| set:sys | `92` | `GetShutdownRtcValue` | — | Q | 2026-11-21 |
| set:sys | `93` | `AcquireFatalDirtyFlagEventHandle` | — | Q | 2026-11-21 |
| set:sys | `94` | `GetFatalDirtyFlags` | — | Q | 2026-11-21 |
| set:sys | `95` | `GetAutoUpdateEnableFlag` | 2.0.0+ | Q | 2026-11-21 |
| set:sys | `96` | `SetAutoUpdateEnableFlag` | 2.0.0+ | Q | 2026-11-21 |
| set:sys | `97` | `GetNxControllerSettings` | 2.0.0+ | Q | 2026-11-21 |
| set:sys | `98` | `SetNxControllerSettings` | 2.0.0+ | Q | 2026-11-21 |
| set:sys | `99` | `GetBatteryPercentageFlag` | 2.0.0+ | Q | 2026-11-21 |
| set:sys | `100` | `SetBatteryPercentageFlag` | 2.0.0+ | Q | 2026-11-21 |
| set:sys | `101` | `GetExternalRtcResetFlag` | 2.0.0+ | Q | 2026-11-21 |
| set:sys | `102` | `SetExternalRtcResetFlag` | 2.0.0+ | Q | 2026-11-21 |
| set:sys | `103` | `GetUsbFullKeyEnableFlag` | 3.0.0+ | Q | 2026-11-21 |
| set:sys | `104` | `SetUsbFullKeyEnableFlag` | 3.0.0+ | Q | 2026-11-21 |
| set:sys | `105` | `SetExternalSteadyClockInternalOffset` | 3.0.0+ | Q | 2026-11-21 |
| set:sys | `106` | `GetExternalSteadyClockInternalOffset` | 3.0.0+ | Q | 2026-11-21 |
| set:sys | `107` | `GetBacklightSettingsEx` | 3.0.0+ | Q | 2026-11-21 |
| set:sys | `108` | `SetBacklightSettingsEx` | 3.0.0+ | Q | 2026-11-21 |
| set:sys | `109` | `GetHeadphoneVolumeWarningCount` | 3.0.0+ | Q | 2026-11-21 |
| set:sys | `110` | `SetHeadphoneVolumeWarningCount` | 3.0.0+ | Q | 2026-11-21 |
| set:sys | `111` | `GetBluetoothAfhEnableFlag` | 3.0.0+ | Q | 2026-11-21 |
| set:sys | `112` | `SetBluetoothAfhEnableFlag` | 3.0.0+ | Q | 2026-11-21 |
| set:sys | `113` | `GetBluetoothBoostEnableFlag` | 3.0.0+ | Q | 2026-11-21 |
| set:sys | `114` | `SetBluetoothBoostEnableFlag` | 3.0.0+ | Q | 2026-11-21 |
| set:sys | `115` | `GetInRepairProcessEnableFlag` | 3.0.0+ | Q | 2026-11-21 |
| set:sys | `116` | `SetInRepairProcessEnableFlag` | 3.0.0+ | Q | 2026-11-21 |
| set:sys | `117` | `GetHeadphoneVolumeUpdateFlag` | 3.0.0+ | Q | 2026-11-21 |
| set:sys | `118` | `SetHeadphoneVolumeUpdateFlag` | 3.0.0+ | Q | 2026-11-21 |
| set:sys | `119` | `NeedsToUpdateHeadphoneVolume` | 3.0.0+ | Q | 2026-11-21 |
| set:sys | `120` | `GetPushNotificationActivityModeOnSleep` | 3.0.0+ | Q | 2026-11-21 |
| set:sys | `121` | `SetPushNotificationActivityModeOnSleep` | 3.0.0+ | Q | 2026-11-21 |
| set:sys | `122` | `GetServiceDiscoveryControlSettings` | 4.0.0+ | Q | 2026-11-21 |
| set:sys | `123` | `SetServiceDiscoveryControlSettings` | 4.0.0+ | Q | 2026-11-21 |
| set:sys | `124` | `GetErrorReportSharePermission` | 4.0.0+ | Q | 2026-11-21 |
| set:sys | `125` | `SetErrorReportSharePermission` | 4.0.0+ | Q | 2026-11-21 |
| set:sys | `126` | `GetAppletLaunchFlags` | 4.0.0+ | Q | 2026-11-21 |
| set:sys | `127` | `SetAppletLaunchFlags` | 4.0.0+ | Q | 2026-11-21 |
| set:sys | `128` | `GetConsoleSixAxisSensorAccelerationBias` | 4.0.0+ | Q | 2026-11-21 |
| set:sys | `129` | `SetConsoleSixAxisSensorAccelerationBias` | 4.0.0+ | Q | 2026-11-21 |
| set:sys | `130` | `GetConsoleSixAxisSensorAngularVelocityBias` | 4.0.0+ | Q | 2026-11-21 |
| set:sys | `131` | `SetConsoleSixAxisSensorAngularVelocityBias` | 4.0.0+ | Q | 2026-11-21 |
| set:sys | `132` | `GetConsoleSixAxisSensorAccelerationGain` | 4.0.0+ | Q | 2026-11-21 |
| set:sys | `133` | `SetConsoleSixAxisSensorAccelerationGain` | 4.0.0+ | Q | 2026-11-21 |
| set:sys | `134` | `GetConsoleSixAxisSensorAngularVelocityGain` | 4.0.0+ | Q | 2026-11-21 |
| set:sys | `135` | `SetConsoleSixAxisSensorAngularVelocityGain` | 4.0.0+ | Q | 2026-11-21 |
| set:sys | `136` | `GetKeyboardLayout` | 4.0.0+ | Q | 2026-11-21 |
| set:sys | `137` | `SetKeyboardLayout` | 4.0.0+ | Q | 2026-11-21 |
| set:sys | `138` | `GetWebInspectorFlag` | 4.0.0+ | Q | 2026-11-21 |
| set:sys | `139` | `GetAllowedSslHosts` | 4.0.0+ | Q | 2026-11-21 |
| set:sys | `140` | `GetHostFsMountPoint` | 4.0.0+ | Q | 2026-11-21 |
| set:sys | `141` | `GetRequiresRunRepairTimeReviser` | 5.0.0+ | Q | 2026-11-21 |
| set:sys | `142` | `SetRequiresRunRepairTimeReviser` | 5.0.0+ | Q | 2026-11-21 |
| set:sys | `143` | `SetBlePairingSettings` | 5.0.0+ | Q | 2026-11-21 |
| set:sys | `144` | `GetBlePairingSettings` | 5.0.0+ | Q | 2026-11-21 |
| set:sys | `145` | `GetConsoleSixAxisSensorAngularVelocityTimeBias` | 5.0.0+ | Q | 2026-11-21 |
| set:sys | `146` | `SetConsoleSixAxisSensorAngularVelocityTimeBias` | 5.0.0+ | Q | 2026-11-21 |
| set:sys | `147` | `GetConsoleSixAxisSensorAngularAcceleration` | 5.0.0+ | Q | 2026-11-21 |
| set:sys | `148` | `SetConsoleSixAxisSensorAngularAcceleration` | 5.0.0+ | Q | 2026-11-21 |
| set:sys | `149` | `GetRebootlessSystemUpdateVersion` | 5.0.0+ | Q | 2026-11-21 |
| set:sys | `150` | `GetDeviceTimeZoneLocationUpdatedTime` | 5.0.0+ | Q | 2026-11-21 |
| set:sys | `151` | `SetDeviceTimeZoneLocationUpdatedTime` | 5.0.0+ | Q | 2026-11-21 |
| set:sys | `152` | `GetUserSystemClockAutomaticCorrectionUpdatedTime` | 6.0.0+ | Q | 2026-11-21 |
| set:sys | `153` | `SetUserSystemClockAutomaticCorrectionUpdatedTime` | 6.0.0+ | Q | 2026-11-21 |
| set:sys | `154` | `GetAccountOnlineStorageSettings` | 6.0.0+ | Q | 2026-11-21 |
| set:sys | `155` | `SetAccountOnlineStorageSettings` | 6.0.0+ | Q | 2026-11-21 |
| set:sys | `156` | `GetPctlReadyFlag` | 6.0.0+ | Q | 2026-11-21 |
| set:sys | `157` | `SetPctlReadyFlag` | 6.0.0+ | Q | 2026-11-21 |
| set:sys | `158` | `GetAnalogStickUserCalibrationL` | 9.0.0+ | Q | 2026-11-21 |
| set:sys | `159` | `SetAnalogStickUserCalibrationL` | 9.0.0+ | Q | 2026-11-21 |
| set:sys | `160` | `GetAnalogStickUserCalibrationR` | 9.0.0+ | Q | 2026-11-21 |
| set:sys | `161` | `SetAnalogStickUserCalibrationR` | 9.0.0+ | Q | 2026-11-21 |
| set:sys | `162` | `GetPtmBatteryVersion` | 6.0.0+ | Q | 2026-11-21 |
| set:sys | `163` | `SetPtmBatteryVersion` | 6.0.0+ | Q | 2026-11-21 |
| set:sys | `164` | `GetUsb30HostEnableFlag` | 6.0.0+ | Q | 2026-11-21 |
| set:sys | `165` | `SetUsb30HostEnableFlag` | 6.0.0+ | Q | 2026-11-21 |
| set:sys | `166` | `GetUsb30DeviceEnableFlag` | 6.0.0+ | Q | 2026-11-21 |
| set:sys | `167` | `SetUsb30DeviceEnableFlag` | 6.0.0+ | Q | 2026-11-21 |
| set:sys | `168` | `GetThemeId` | 7.0.0+ | Q | 2026-11-21 |
| set:sys | `169` | `SetThemeId` | 7.0.0+ | Q | 2026-11-21 |
| set:sys | `170` | `GetChineseTraditionalInputMethod` | 7.0.0+ | Q | 2026-11-21 |
| set:sys | `171` | `SetChineseTraditionalInputMethod` | 7.0.0+ | Q | 2026-11-21 |
| set:sys | `172` | `GetPtmCycleCountReliability` | 7.0.0+ | Q | 2026-11-21 |
| set:sys | `173` | `SetPtmCycleCountReliability` | 7.0.0+ | Q | 2026-11-21 |
| set:sys | `174` | `GetHomeMenuScheme` | 9.0.0+ | Q | 2026-11-21 |
| set:sys | `175` | `GetThemeSettings` | 7.0.0+ | Q | 2026-11-21 |
| set:sys | `176` | `SetThemeSettings` | 7.0.0+ | Q | 2026-11-21 |
| set:sys | `177` | `GetThemeKey` | 7.0.0+ | Q | 2026-11-21 |
| set:sys | `178` | `SetThemeKey` | 7.0.0+ | Q | 2026-11-21 |
| set:sys | `179` | `GetZoomFlag` | 8.0.0+ | Q | 2026-11-21 |
| set:sys | `180` | `SetZoomFlag` | 8.0.0+ | Q | 2026-11-21 |
| set:sys | `181` | `GetT` | 8.0.0+ | Q | 2026-11-21 |
| set:sys | `182` | `SetT` | 8.0.0+ | Q | 2026-11-21 |
| set:sys | `183` | `GetPlatformRegion` | 9.0.0+ | Q | 2026-11-21 |
| set:sys | `184` | `SetPlatformRegion` | 9.0.0+ | Q | 2026-11-21 |
| set:sys | `185` | `GetHomeMenuSchemeModel` | 9.0.0+ | Q | 2026-11-21 |
| set:sys | `186` | `GetMemoryUsageRateFlag` | 9.0.0+ | Q | 2026-11-21 |
| set:sys | `187` | `GetTouchScreenMode` | 9.0.0+ | Q | 2026-11-21 |
| set:sys | `188` | `SetTouchScreenMode` | 9.0.0+ | Q | 2026-11-21 |

### Shared Database services

[Wiki SwitchBrew](https://switchbrew.org/wiki/Shared_Database_services) · [miroir](https://github.com/backupbrew/switchbrew/blob/master/Shared%20Database%20services.md)

**73 commandes documentées**.

| Interface / section | ID | Fonction | Disponibilité indiquée | Encore | Vérifié |
|---|---|---|---|---|---|
| pl:u, pl:s | `0` | `RequestSharedFontLoad` | — | Q | 2026-11-21 |
| pl:u, pl:s | `1` | `GetSharedFontLoadState` | — | Q | 2026-11-21 |
| pl:u, pl:s | `2` | `GetSharedFontSize` | — | Q | 2026-11-21 |
| pl:u, pl:s | `3` | `GetSharedFontAddress` | — | Q | 2026-11-21 |
| pl:u, pl:s | `4` | `GetSharedFontSharedMemoryHandle` | — | Q | 2026-11-21 |
| pl:u, pl:s | `5` | `GetSharedFontInOrderOfPriority` | — | Q | 2026-11-21 |
| pl:u, pl:s | `6` | `GetSharedFontInOrderOfPriorityForSystem` | 4.0.0+ | Q | 2026-11-21 |
| pl:u, pl:s | `100` | `RequestApplicationFunctionAuthorization` | 8.0.0+ | Q | 2026-11-21 |
| pl:u, pl:s | `101` | `RequestApplicationFunctionAuthorizationForSystem` | 8.0.0+ | Q | 2026-11-21 |
| pl:u, pl:s | `1000` | `LoadNgWordDataForPlatformRegionChina` | 9.0.0+ | Q | 2026-11-21 |
| pl:u, pl:s | `1001` | `GetNgWordDataSizeForPlatformRegionChina` | 9.0.0+ | Q | 2026-11-21 |
| mii:u, mii:e | `0` | `GetDatabaseService` | — | Q | 2026-11-21 |
| mii:u, mii:e | `0` | `IsUpdated` | — | Q | 2026-11-21 |
| mii:u, mii:e | `1` | `IsFullDatabase` | — | Q | 2026-11-21 |
| mii:u, mii:e | `2` | `GetCount` | — | Q | 2026-11-21 |
| mii:u, mii:e | `3` | `Get` | — | Q | 2026-11-21 |
| mii:u, mii:e | `4` | `Get1` | — | Q | 2026-11-21 |
| mii:u, mii:e | `5` | `UpdateLatest` | — | Q | 2026-11-21 |
| mii:u, mii:e | `6` | `BuildRandom` | — | Q | 2026-11-21 |
| mii:u, mii:e | `7` | `BuildDefault` | — | Q | 2026-11-21 |
| mii:u, mii:e | `8` | `Get2` | — | Q | 2026-11-21 |
| mii:u, mii:e | `9` | `Get3` | — | Q | 2026-11-21 |
| mii:u, mii:e | `10` | `UpdateLatest1` | — | Q | 2026-11-21 |
| mii:u, mii:e | `11` | `FindIndex` | — | Q | 2026-11-21 |
| mii:u, mii:e | `12` | `Move` | — | Q | 2026-11-21 |
| mii:u, mii:e | `13` | `AddOrReplace` | — | Q | 2026-11-21 |
| mii:u, mii:e | `14` | `Delete` | — | Q | 2026-11-21 |
| mii:u, mii:e | `15` | `DestroyFile` | — | Q | 2026-11-21 |
| mii:u, mii:e | `16` | `DeleteFile` | — | Q | 2026-11-21 |
| mii:u, mii:e | `17` | `Format` | — | Q | 2026-11-21 |
| mii:u, mii:e | `18` | `Import` | — | Q | 2026-11-21 |
| mii:u, mii:e | `19` | `Export` | — | Q | 2026-11-21 |
| mii:u, mii:e | `20` | `IsBrokenDatabaseWithClearFlag` | — | Q | 2026-11-21 |
| mii:u, mii:e | `21` | `GetIndex` | — | Q | 2026-11-21 |
| mii:u, mii:e | `22` | `SetInterfaceVersion` | 5.0.0+ | Q | 2026-11-21 |
| mii:u, mii:e | `23` | `Convert` | 5.0.0+ | Q | 2026-11-21 |
| mii:u, mii:e | `24` | `ConvertCoreDataToCharInfo` | 7.0.0+ | Q | 2026-11-21 |
| mii:u, mii:e | `25` | `ConvertCharInfoToCoreData` | 7.0.0+ | Q | 2026-11-21 |
| miiimg | `0` | `Initialize` | — | Q | 2026-11-21 |
| miiimg | `10` | `Reload` | — | Q | 2026-11-21 |
| miiimg | `11` | `GetCount` | — | Q | 2026-11-21 |
| miiimg | `12` | `IsEmpty` | — | Q | 2026-11-21 |
| miiimg | `13` | `IsFull` | — | Q | 2026-11-21 |
| miiimg | `14` | `GetAttribute` | — | Q | 2026-11-21 |
| miiimg | `15` | `LoadImage` | — | Q | 2026-11-21 |
| miiimg | `16` | `AddOrUpdateImage` | — | Q | 2026-11-21 |
| miiimg | `17` | `DeleteImages` | — | Q | 2026-11-21 |
| miiimg | `100` | `DeleteFile` | — | Q | 2026-11-21 |
| miiimg | `101` | `DestroyFile` | — | Q | 2026-11-21 |
| miiimg | `102` | `ImportFile` | — | Q | 2026-11-21 |
| miiimg | `103` | `ExportFile` | — | Q | 2026-11-21 |
| miiimg | `104` | `ForceInitialize` | — | Q | 2026-11-21 |
| pdm:ntfy | `0` | `NotifyAppletEvent` | — | Q | 2026-11-21 |
| pdm:ntfy | `2` | `NotifyOperationModeChangeEvent` | — | Q | 2026-11-21 |
| pdm:ntfy | `3` | `NotifyPowerStateChangeEvent` | — | Q | 2026-11-21 |
| pdm:ntfy | `4` | `NotifyClearAllEvent` | — | Q | 2026-11-21 |
| pdm:ntfy | `5` | `NotifyEventForDebug` | — | Q | 2026-11-21 |
| pdm:ntfy | `6` | `SuspendUserAccountEventService` | 4.0.0+ | Q | 2026-11-21 |
| pdm:ntfy | `7` | `ResumeUserAccountEventService` | 4.0.0+ | Q | 2026-11-21 |
| pdm:qry | `0` | `QueryApplicationEvent` | — | Q | 2026-11-21 |
| pdm:qry | `4` | `QueryPlayStatisticsByApplicationId` | — | Q | 2026-11-21 |
| pdm:qry | `5` | `QueryPlayStatisticsByApplicationIdAndUserAccountId` | — | Q | 2026-11-21 |
| pdm:qry | `7` | `QueryLastPlayTime` | — | Q | 2026-11-21 |
| pdm:qry | `8` | `QueryPlayEvent` | — | Q | 2026-11-21 |
| pdm:qry | `9` | `GetAvailablePlayEventRange` | — | Q | 2026-11-21 |
| pdm:qry | `10` | `QueryAccountEvent` | — | Q | 2026-11-21 |
| pdm:qry | `11` | `QueryAccountPlayEvent` | 4.0.0+ | Q | 2026-11-21 |
| pdm:qry | `12` | `GetAvailableAccountPlayEventRange` | 4.0.0+ | Q | 2026-11-21 |
| pdm:qry | `13` | `QueryApplicationPlayStatisticsForSystem` | 5.0.0+ | Q | 2026-11-21 |
| pdm:qry | `14` | `QueryRecentlyPlayedApplication` | 6.0.0+ | Q | 2026-11-21 |
| pdm:qry | `15` | `GetRecentlyPlayedApplicationUpdateEvent` | 6.0.0+ | Q | 2026-11-21 |
| pdm:qry | `16` | `QueryApplicationPlayStatisticsByUserAccountIdForSystem` | 6.0.0+ | Q | 2026-11-21 |
| avm | `103` | `No input, returns an IVersionListImporter.` | — | Q | 2026-11-21 |

### SSL services

[Wiki SwitchBrew](https://switchbrew.org/wiki/SSL_services) · [miroir](https://github.com/backupbrew/switchbrew/blob/master/SSL%20services.md)

**49 commandes documentées**.

| Interface / section | ID | Fonction | Disponibilité indiquée | Encore | Vérifié |
|---|---|---|---|---|---|
| ssl | `0` | `CreateContext` | — | Q | 2026-11-21 |
| ssl | `1` | `GetContextCount` | — | Q | 2026-11-21 |
| ssl | `2` | `GetCertificates` | — | Q | 2026-11-21 |
| ssl | `3` | `GetCertificateBufSize` | — | Q | 2026-11-21 |
| ssl | `4` | `DebugIoctl` | 3.0.0+ | Q | 2026-11-21 |
| ssl | `5` | `SetInterfaceVersion` | 3.0.0+ | Q | 2026-11-21 |
| ssl | `6` | `FlushSessionCache` | 5.0.0+ | Q | 2026-11-21 |
| ssl | `7` | `SetDebugOption` | 6.0.0+ | Q | 2026-11-21 |
| ssl | `8` | `GetDebugOption` | 6.0.0+ | Q | 2026-11-21 |
| ssl | `0` | `SetOption` | — | Q | 2026-11-21 |
| ssl | `1` | `GetOption` | — | Q | 2026-11-21 |
| ssl | `2` | `CreateConnection` | — | Q | 2026-11-21 |
| ssl | `3` | `GetConnectionCount` | — | Q | 2026-11-21 |
| ssl | `4` | `ImportServerPki` | — | Q | 2026-11-21 |
| ssl | `5` | `ImportClientPki` | — | Q | 2026-11-21 |
| ssl | `6` | `RemoveServerPki` | — | Q | 2026-11-21 |
| ssl | `7` | `RemoveClientPki` | — | Q | 2026-11-21 |
| ssl | `8` | `RegisterInternalPki` | — | Q | 2026-11-21 |
| ssl | `9` | `AddPolicyOid` | — | Q | 2026-11-21 |
| ssl | `10` | `ImportCrl` | 3.0.0+ | Q | 2026-11-21 |
| ssl | `11` | `RemoveCrl` | 3.0.0+ | Q | 2026-11-21 |
| ssl | `0` | `SetSocketDescriptor` | — | Q | 2026-11-21 |
| ssl | `1` | `SetHostName` | — | Q | 2026-11-21 |
| ssl | `2` | `SetVerifyOption` | — | Q | 2026-11-21 |
| ssl | `3` | `SetIoMode` | — | Q | 2026-11-21 |
| ssl | `4` | `GetSocketDescriptor` | — | Q | 2026-11-21 |
| ssl | `5` | `GetHostName` | — | Q | 2026-11-21 |
| ssl | `6` | `GetVerifyOption` | — | Q | 2026-11-21 |
| ssl | `7` | `GetIoMode` | — | Q | 2026-11-21 |
| ssl | `8` | `DoHandshake` | — | Q | 2026-11-21 |
| ssl | `9` | `DoHandshakeGetServerCert` | — | Q | 2026-11-21 |
| ssl | `10` | `Read` | — | Q | 2026-11-21 |
| ssl | `11` | `Write` | — | Q | 2026-11-21 |
| ssl | `12` | `Pending` | — | Q | 2026-11-21 |
| ssl | `13` | `Peek` | — | Q | 2026-11-21 |
| ssl | `14` | `Poll` | — | Q | 2026-11-21 |
| ssl | `15` | `GetVerifyCertError` | — | Q | 2026-11-21 |
| ssl | `16` | `GetNeededServerCertBufferSize` | — | Q | 2026-11-21 |
| ssl | `17` | `SetSessionCacheMode` | — | Q | 2026-11-21 |
| ssl | `18` | `GetSessionCacheMode` | — | Q | 2026-11-21 |
| ssl | `19` | `FlushSessionCache` | — | Q | 2026-11-21 |
| ssl | `20` | `SetRenegotiationMode` | — | Q | 2026-11-21 |
| ssl | `21` | `GetRenegotiationMode` | — | Q | 2026-11-21 |
| ssl | `22` | `SetOption` | — | Q | 2026-11-21 |
| ssl | `23` | `GetOption` | — | Q | 2026-11-21 |
| ssl | `24` | `GetVerifyCertErrors` | — | Q | 2026-11-21 |
| ssl | `25` | `GetCipherInfo` | 4.0.0+ | Q | 2026-11-21 |
| ssl | `26` | `SetNextAlpnProto` | 9.0.0+ | Q | 2026-11-21 |
| ssl | `27` | `GetNextAlpnProto` | 9.0.0+ | Q | 2026-11-21 |

### SPL services

[Wiki SwitchBrew](https://switchbrew.org/wiki/SPL_services) · [miroir](https://github.com/backupbrew/switchbrew/blob/master/SPL%20services.md)

**33 commandes documentées**.

| Interface / section | ID | Fonction | Disponibilité indiquée | Encore | Vérifié |
|---|---|---|---|---|---|
| csrng | `0` | `GenerateRandomBytes` | — | Q | 2026-11-21 |
| spl:, spl:mig, spl:fs, spl:ssl, spl:es, spl:manu | `0` | `GetConfig` | — | Q | 2026-11-21 |
| spl:, spl:mig, spl:fs, spl:ssl, spl:es, spl:manu | `1` | `ExpMod` | — | Q | 2026-11-21 |
| spl:, spl:mig, spl:fs, spl:ssl, spl:es, spl:manu | `2` | `GenerateAesKek` | — | Q | 2026-11-21 |
| spl:, spl:mig, spl:fs, spl:ssl, spl:es, spl:manu | `3` | `LoadAesKey` | — | Q | 2026-11-21 |
| spl:, spl:mig, spl:fs, spl:ssl, spl:es, spl:manu | `4` | `GenerateAesKey` | — | Q | 2026-11-21 |
| spl:, spl:mig, spl:fs, spl:ssl, spl:es, spl:manu | `5` | `SetConfig` | — | Q | 2026-11-21 |
| spl:, spl:mig, spl:fs, spl:ssl, spl:es, spl:manu | `7` | `GenerateRandomBytes` | — | Q | 2026-11-21 |
| spl:, spl:mig, spl:fs, spl:ssl, spl:es, spl:manu | `9` | `ImportLotusKey` | — | Q | 2026-11-21 |
| spl:, spl:mig, spl:fs, spl:ssl, spl:es, spl:manu | `10` | `DecryptLotusMessage` | — | Q | 2026-11-21 |
| spl:, spl:mig, spl:fs, spl:ssl, spl:es, spl:manu | `11` | `IsDevelopment` | — | Q | 2026-11-21 |
| spl:, spl:mig, spl:fs, spl:ssl, spl:es, spl:manu | `12` | `GenerateSpecificAesKey` | — | Q | 2026-11-21 |
| spl:, spl:mig, spl:fs, spl:ssl, spl:es, spl:manu | `13` | `DecryptRsaPrivateKey` | — | Q | 2026-11-21 |
| spl:, spl:mig, spl:fs, spl:ssl, spl:es, spl:manu | `14` | `DecryptAesKey` | — | Q | 2026-11-21 |
| spl:, spl:mig, spl:fs, spl:ssl, spl:es, spl:manu | `15` | `CryptAesCtr` | — | Q | 2026-11-21 |
| spl:, spl:mig, spl:fs, spl:ssl, spl:es, spl:manu | `16` | `ComputeCmac` | — | Q | 2026-11-21 |
| spl:, spl:mig, spl:fs, spl:ssl, spl:es, spl:manu | `17` | `ImportEsKey` | — | Q | 2026-11-21 |
| spl:, spl:mig, spl:fs, spl:ssl, spl:es, spl:manu | `18` | `UnwrapTitleKey` | — | Q | 2026-11-21 |
| spl:, spl:mig, spl:fs, spl:ssl, spl:es, spl:manu | `19` | `LoadTitleKey` | — | Q | 2026-11-21 |
| spl:, spl:mig, spl:fs, spl:ssl, spl:es, spl:manu | `20` | `UnwrapCommonTitleKey` | 2.0.0+ | Q | 2026-11-21 |
| spl:, spl:mig, spl:fs, spl:ssl, spl:es, spl:manu | `21` | `AllocateAesKeyslot` | 2.0.0+ | Q | 2026-11-21 |
| spl:, spl:mig, spl:fs, spl:ssl, spl:es, spl:manu | `22` | `FreeAesKeyslot` | 2.0.0+ | Q | 2026-11-21 |
| spl:, spl:mig, spl:fs, spl:ssl, spl:es, spl:manu | `23` | `GetAesKeyslotAvailableEvent` | 2.0.0+ | Q | 2026-11-21 |
| spl:, spl:mig, spl:fs, spl:ssl, spl:es, spl:manu | `24` | `SetBootReason` | 3.0.0+ | Q | 2026-11-21 |
| spl:, spl:mig, spl:fs, spl:ssl, spl:es, spl:manu | `25` | `GetBootReason` | 3.0.0+ | Q | 2026-11-21 |
| spl:, spl:mig, spl:fs, spl:ssl, spl:es, spl:manu | `26` | `ImportSslKey` | 5.0.0+ | Q | 2026-11-21 |
| spl:, spl:mig, spl:fs, spl:ssl, spl:es, spl:manu | `27` | `SslExpMod` | 5.0.0+ | Q | 2026-11-21 |
| spl:, spl:mig, spl:fs, spl:ssl, spl:es, spl:manu | `28` | `ImportDrmKey` | 5.0.0+ | Q | 2026-11-21 |
| spl:, spl:mig, spl:fs, spl:ssl, spl:es, spl:manu | `29` | `DrmExpMod` | 5.0.0+ | Q | 2026-11-21 |
| spl:, spl:mig, spl:fs, spl:ssl, spl:es, spl:manu | `30` | `ReEncryptRsaPrivateKey` | 5.0.0+ | Q | 2026-11-21 |
| spl:, spl:mig, spl:fs, spl:ssl, spl:es, spl:manu | `31` | `GetPackage2Hash` | 5.0.0+ | Q | 2026-11-21 |
| spl:, spl:mig, spl:fs, spl:ssl, spl:es, spl:manu | `31` | `UnwrapElicenseKey` | 6.0.0+ | Q | 2026-11-21 |
| spl:, spl:mig, spl:fs, spl:ssl, spl:es, spl:manu | `32` | `LoadElicenseKey` | 6.0.0+ | Q | 2026-11-21 |

### USB services

[Wiki SwitchBrew](https://switchbrew.org/wiki/USB_services) · [miroir](https://github.com/backupbrew/switchbrew/blob/master/USB%20services.md)

**52 commandes documentées**.

| Interface / section | ID | Fonction | Disponibilité indiquée | Encore | Vérifié |
|---|---|---|---|---|---|
| usb:ds | `0` | `BindDevice` | — | Q | 2026-11-21 |
| usb:ds | `1` | `BindClientProcess` | — | Q | 2026-11-21 |
| usb:ds | `2` | `GetDsInterface` | — | Q | 2026-11-21 |
| usb:ds | `3` | `GetStateChangeEvent` | — | Q | 2026-11-21 |
| usb:ds | `4` | `GetState` | — | Q | 2026-11-21 |
| usb:ds | `6` | `AddUsbStringDescriptor` | 5.0.0+ | Q | 2026-11-21 |
| usb:ds | `7` | `DeleteUsbStringDescriptor` | 5.0.0+ | Q | 2026-11-21 |
| usb:ds | `8` | `SetUsbDeviceDescriptor` | 5.0.0+ | Q | 2026-11-21 |
| usb:ds | `9` | `SetBinaryObjectStore` | 5.0.0+ | Q | 2026-11-21 |
| usb:ds | `10` | `Enable` | 5.0.0+ | Q | 2026-11-21 |
| usb:ds | `11` | `Disable` | 5.0.0+ | Q | 2026-11-21 |
| usb:ds | `0` | `GetDsEndpoint` | — | Q | 2026-11-21 |
| usb:ds | `1` | `GetSetupEvent` | — | Q | 2026-11-21 |
| usb:ds | `3` | `EnableInterface` | — | Q | 2026-11-21 |
| usb:ds | `4` | `DisableInterface` | — | Q | 2026-11-21 |
| usb:ds | `5` | `CtrlInPostBufferAsync` | — | Q | 2026-11-21 |
| usb:ds | `6` | `CtrlOutPostBufferAsync` | — | Q | 2026-11-21 |
| usb:ds | `7` | `GetCtrlInCompletionEvent` | — | Q | 2026-11-21 |
| usb:ds | `8` | `GetCtrlInReportData` | — | Q | 2026-11-21 |
| usb:ds | `9` | `GetCtrlOutCompletionEvent` | — | Q | 2026-11-21 |
| usb:ds | `10` | `GetCtrlOutReportData` | — | Q | 2026-11-21 |
| usb:ds | `11` | `StallCtrl` | — | Q | 2026-11-21 |
| usb:ds | `12` | `AppendConfigurationData` | 5.0.0+ | Q | 2026-11-21 |
| usb:ds | `0` | `PostBufferAsync` | — | Q | 2026-11-21 |
| usb:ds | `2` | `GetCompletionEvent` | — | Q | 2026-11-21 |
| usb:ds | `3` | `GetReportData` | — | Q | 2026-11-21 |
| usb:ds | `4` | `Stall` | — | Q | 2026-11-21 |
| usb:hs, usb:hs:a | `1` | `SetInterface` | — | Q | 2026-11-21 |
| usb:hs, usb:hs:a | `2` | `GetInterface` | — | Q | 2026-11-21 |
| usb:hs, usb:hs:a | `3` | `GetAlternateInterface` | — | Q | 2026-11-21 |
| usb:hs, usb:hs:a | `6` | `([1.0.0] SubmitControlInRequest)` | — | Q | 2026-11-21 |
| usb:hs, usb:hs:a | `7` | `GetCtrlXferReport ([1.0.0] SubmitControlOutRequest)` | — | Q | 2026-11-21 |
| usb:hs, usb:hs:a | `8` | `ResetDevice` | — | Q | 2026-11-21 |
| usb:hs, usb:hs:a | `0` | `Open ([1.0.0] SubmitOutRequest)` | — | Q | 2026-11-21 |
| usb:hs, usb:hs:a | `1` | `Close ([1.0.0] SubmitInRequest)` | — | Q | 2026-11-21 |
| usb:hs, usb:hs:a | `3` | `Populate ([1.0.0] Close)` | — | Q | 2026-11-21 |
| usb:pd | `0` | `GetPdSession` | — | Q | 2026-11-21 |
| usb:pd | `0` | `BindNoticeEvent` | — | Q | 2026-11-21 |
| usb:pd | `1` | `UnbindNoticeEvent` | — | Q | 2026-11-21 |
| usb:pd | `2` | `GetStatus` | — | Q | 2026-11-21 |
| usb:pd | `3` | `GetNotice` | — | Q | 2026-11-21 |
| usb:pd | `4` | `EnablePowerRequestNotice` | — | Q | 2026-11-21 |
| usb:pd | `5` | `DisablePowerRequestNotice` | — | Q | 2026-11-21 |
| usb:pd | `6` | `ReplyPowerRequest` | — | Q | 2026-11-21 |
| usb:pd:c | `0` | `GetPdCradleSession` | — | Q | 2026-11-21 |
| usb:pd:c | `0` | `VdmUserWrite` | — | Q | 2026-11-21 |
| usb:pd:c | `1` | `VdmUserRead` | — | Q | 2026-11-21 |
| usb:pd:c | `2` | `Vdm20Init` | — | Q | 2026-11-21 |
| usb:pd:c | `3` | `GetFwType` | 2.0.0+ | Q | 2026-11-21 |
| usb:pd:c | `4` | `GetFwRevision` | 2.0.0+ | Q | 2026-11-21 |
| usb:pd:c | `5` | `GetManufacturerId` | 2.0.0+ | Q | 2026-11-21 |
| usb:pd:c | `6` | `GetDeviceId` | 2.0.0+ | Q | 2026-11-21 |

<!-- NS1_IPC_APPEND -->
