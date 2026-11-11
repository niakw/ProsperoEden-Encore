# R23 — NS/OLSC Firmware 23.x–23.5 HLE: three commit-level source gaps

**Audit-only, 11 Nov 2026.** Compare Eden official upstream commits #1 `89d1a1cd7015ebd05ac1bb6a97d1a472bf28701b`, #132 `defddec47` and #137 `bfba95fd6` with Encore's frozen `vendor@22b69d6053db41b74edac2633c012f925b84f69e`. No guest source patched or native build triggered.

## Exact source and handler receipts

| Upstream index | Upstream actual change | Frozen Encore code (git source receipt) | Disposition |
|---|---|---|---|
| **#1** | `IApplicationManagerInterface`: 13 command IDs **3250–3262**, 12 new handlers (3252 remains unimplemented), and a new `present_event` with handle return for command 3250 | `vendor/sources/eden/src/core/hle/service/ns/application_manager_interface.cpp`, blob `c3b2aee8a8e7b87b9dd0c6952538e0ffad9e0424`; `.h` blob `f09ccf7b8180af08a501f295b3c7ce3dc4831ff2`. No IDs 3250–3262, `present_event` or handlers in the pinned snapshot. | **Relevant source gap** for firmware 23.5/qlaunch if the native NS service uses that command; actual invocation and PS5 behavior untested. |
| **#132** | `Unknown936` returns a zero `u64`; `Unknown4042` returns an asynchronous `IAsyncResult` interface and event. Adds **two brand-new source files** and registers them in `src/core/CMakeLists.txt`. | Pinned NS `.cpp` has `{936, nullptr}` at line ~233 and `{4042, nullptr}` at ~425. `vendor/sources/eden/src/core/hle/service/ns/i_async_result.cpp` **does not exist** at this gitlink. | **Relevant multi-file source gap**. Cannot fix safely with only two function table replacements: requires matching async interface owner and registration and positive/negative IPC tests. |
| **#137** | Adds `Unknown4105` NS stub, implements OLSC `GetTransferTaskProgress` command 21, and comments two existing service versions. | Pinned NS `.cpp` and `.h` have no `Unknown4105`; `vendor/sources/eden/src/core/hle/service/olsc/transfer_task_list_controller.cpp` blob `0f9042bf0189e8f7eb4dd305b7e38a2dc24a2f1f`, command 21 is `nullptr`. | **Relevant HLE source gap** for certain Switch 23 launch paths. Guest use and response semantics untested. |

The main PS5 CMake target `core` is derived from the pinned core source list. Audit `headless/CMakeLists.txt` contains no explicit alternative `application_manager_interface`, `i_async_result`, or `transfer_task_list_controller` owner selection. **This is evidence of source gaps, not a current-main compile DB/link map or PS5 execution receipt.** Check a newer `main` native source/ABI owner independently before any migration.

## Proposed controlled repair / verification gate

1. **Firmware IPC corpus:** permitted/denied command IDs 936, 4042, 4105, 3250–3262 and OLSC 21 on guest firmware versions 20–23.5; check command table dispatch, service counts, ABI and expected result/status. Do not claim success based on `R_SUCCEED()` stubs alone.
2. **Async lifecycle:** construct/cancel/close `IAsyncResult` and `present_event`, verify kernel handle ownership, event signalling, cancellation, teardown and disconnects. Preserve original NS error codes and HOS version gating.
3. **Link owners:** introduce maintained complete copies of NS/OLSC source and the new async interface through a coordinated pinned vendor PR only after exact native CMake input/headers and compilation tests. No edits in immutable `vendor/sources`.
4. **Regression:** NS1 launch and home/menu, applet exit/relaunch and any shared NS2 source routes. Reject copying code that only quiets IPC log messages without valid behavior.

**Count impact:** three previously runtime-semantic-pending upstream commits now receive an explicit `verified-relevant-source-gap-awaiting-native-proof` decision. That is 3 semantic dispositions, **0 fixes integrated, 0 host/device acceptance gates closed**. This does not imply three independent bugs seen on PS5.
