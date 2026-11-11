# R23 pass 12 — native network selected owner, not Mac network refactor

**11 November 2026. E1 source-only disposition; no PS5 network device test.** Official upstream [`2c40328a23630353f4dd20778eb587e586cd83a5`](https://github.com/eden-emulator/mirror/commit/2c40328a23630353f4dd20778eb587e586cd83a5) changes exactly `src/core/internal_network/network_interface.cpp`. The diff introduces `__APPLE__` getifaddrs/route support, a Darwin-specific SA_SIZE macro, and a FreeBSD version conditional when calling `link_ntoa` vs `link_ntoa_r`.

Frozen vendor original Git blob `f68d4617ebb7a665f270052889d4262f83b07641`; active maintained native `encore-active/eden-core/src/core/internal_network/network_interface.cpp` Git blob **`8ea8093bf09c20ede50cab1993e7cfaebe645816`**. Under the actual headless PS5 CMake selection, `internal_network/network_interface.cpp` is removed from `core SOURCES` and the maintained active unit appended instead.

The maintained source uses `#elif defined(__linux__) || defined(__ANDROID__) || defined(__FreeBSD__)` for includes, and `#if defined(__ANDROID__) || defined(__linux__) || defined(__FreeBSD__)` at `GetAvailableNetworkInterfaces()` to take the `getifaddrs` branch with zero gateway on FreeBSD. Its subsequent `#elif defined(__FreeBSD__)` route-socket branch containing `link_ntoa_r` cannot execute when `__FreeBSD__` is true, because the first branch already matched. If the PS5 compiler does not expose that macro, the upstream Darwin changes still do not activate by themselves. **Actual compiler macro predefinition is not proven here**.

**Decision:** `reviewed-current-PS5-native-ifaddrs-Mac-route-not-selected` — do not import this Darwin/legacy route change into the current native owner. Reopen if CMake target/source selection, actual SDK macro profile, route interfaces or multiplayer requirements change. This does **not** establish correct PS5 interface/gateway results; that requires a device test. No vendor or main edit.

After pass 12: **52** generic semantic entries, **13** relevant source gaps, **2** distinct open GL/UTF policy gates, **17** native header receipts, **7** full corrective batches.
