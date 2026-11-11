# R23 pass 9 — #147 FW23 NS command 23 and AM overlay must be separated

**11 November 2026; audit PR #45 only.** Official Eden commit [`5d150cac5c6624fa6a0e94266846b75d91a6a5d0`](https://github.com/eden-emulator/mirror/commit/5d150cac5c6624fa6a0e94266846b75d91a6a5d0) changes exactly **four** paths: Android `Game.kt`, HLE `am/display_layer_manager.cpp`, HLE `ns/read_only_application_control_data_interface.cpp`, and Dynarmic ARM64 `emit_arm64_memory.cpp`. A source comparison is **E1 evidence only**, not real PS5 guest IPC or visual execution.

## Confirmed missing native NS HLE entry (source E1)

- Pinned vendor `22b69d6053db41b74edac2633c012f925b84f69e`, `sources/eden/src/core/hle/service/ns/read_only_application_control_data_interface.cpp`, Git blob **`c7606a83bf771c9251ef8a44add72b72a2589870`**, contains **cmd 19** mapped to `D<&IReadOnlyApplicationControlDataInterface::GetApplicationControlData3>` with the `"GetApplicationControlData"` service description. The dispatch table has **no cmd 23** entry.
- Upstream #147 adds only one line to this file: command **23** mapped to that exact existing `GetApplicationControlData3` handler. The pinned `src/core/CMakeLists.txt`, blob **`508ace350173f5068bd7531f37e70199134fde3a`**, already schedules the original NS file. Audit `headless/CMakeLists.txt` has no alternative NS TU substitution at this frozen pin.
- **Decision:** a relevant NS1 firmware 23 source gap awaits actual selected native compilation and guest IPC tests. Verify cmd19 remains present, cmd23 request and response buffer shape, title launch data, permission/error results, legacy firmware acceptance, and no regression with upstream command-family #1/#132/#137. Avoid claiming this guarantees NS1 boot or fixes a specific console crash.

## AM overlay change: different semantic and dependency track

- Pinned `sources/eden/src/core/hle/service/am/display_layer_manager.cpp`, Git blob **`494e8a132b30962c5d13f20155eb00725652207a`**, still uses old `CreateManagedDisplayLayer` and `IsSystemBufferSharingEnabled` ordering.
- Upstream #147 additionally calls `SetLayerVisibility`, `SetLayerStackMask` on managed layers, alters overlay Z index and layer stack/blending order and tracks the system shared layer in `m_managed_display_layers`. Importing this logic would affect overlay applets and perhaps other display stacks, independent of NS command 23.
- The upstream diff refers to `Overlay` and `Foreground` names. The **pinned header** does not contain those identifiers, so a direct copy is not compilation-qualified; resolve the real declarations and selected VI APIs first. Test launch with and without overlay applets, layer Z/visibility, display presentation and teardown. No blanket import or fabricated on-device success.
- ARM64 `TBNZ` → `TST`/`B.NE` source is for the Dynarmic ARM64 host backend, not the PS5 x86-64 Dynarmic execution backend; Android Kotlin `toLongOrNull` is not the native launcher.

## Exit status

#147 moves from generic unresolved semantic queue to **`verified-relevant-source-gap-awaiting-native-proof`** on **one commit**. It is not merged, patched or compiled. R23 totals: **56** generic semantic reviews, **1** scoped PS5 OpenGL async-depth policy needing real device testing, **12** confirmed relevant source differences requiring repair/test decisions, **0** current-profile build-only candidates, **17** native header include receipts and **7** fully unqualified C00–C06 release batches. All 155 upstream file lists remain complete. The broader AM visual behavior and linked native dependencies remain separately open.
