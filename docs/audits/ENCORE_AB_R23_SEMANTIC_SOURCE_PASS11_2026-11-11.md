# R23 pass 11 — #75 Boost legacy ADL wrappers and #131 keep-connected fallback

**11 November 2026, audit branch PR #45 only.** Frozen vendor `22b69d6053db41b74edac2633c012f925b84f69e`. Source-only decisions E1; no linked PS5 ELF, controller, Vulkan or audio-runtime proof.

## #75 — current 1.90 Boost profile: compatibility cleanup, do not port indiscriminately

Eden [`4dc69c06f764a235bccd01afbfc765d9ddbebc9f`](https://github.com/eden-emulator/mirror/commit/4dc69c06f764a235bccd01afbfc765d9ddbebc9f) alters **seven** source/header paths to remove `FixStaticVectorADL`/`FixSmallVectorADL`. The pinned `sources/eden/cpmfile.json` (`af773e0bd08e1885990d2d8dba70b4bb08231502`) declares Boost **`boost-1.90.0`**, and the real maintained `encore-active/eden-core/src/video_core/texture_cache/util.h` Git blob `69a45a6f6ad1977b3015fc3bfeddfc35ef117cf1` retains `#if BOOST_VERSION >= 108100 || __GNUC__ > 12` with the first branch returning the **same** `boost::container::small_vector<T,N>` as its input. Original `audio_core/in/audio_in_system.cpp` blob `f71a2df6be6484be3427c1fc29b6e2c184de0d09` analogously returns `boost::container::static_vector<T,N>`.

**Scoped disposition:** `reviewed-current-Boost190-ADL-compat-wrapper-retained`. For the frozen bundled version, removing the wrapper does not add a required GPU/AudioIn operation; the existing wrapper *can* copy an intermediate container, so no proof of identical allocations/performance or identical behavior on a different Boost/compiler. Do **not** claim this is an optimized/compiled PS5 performance fix. Retain current source and reopen if a future boost/toolchain change triggers an ADL compile error, if span ownership contracts change, or a measurable regression justifies separately compiling/testing the direct-container calls.

## #131 — source-proven guest controller connection disruption

Eden [`b77308ced62abe890428955dba687c95e4d93aba`](https://github.com/eden-emulator/mirror/commit/b77308ced62abe890428955dba687c95e4d93aba) changes only `src/core/frontend/applets/controller.cpp`. The actual pinned copy (Git blob **`c4292c5a1257dbfb18c3709d4911193caf2ed5b6`**) has the comment **"First, disconnect all controllers regardless of the value of keep_controllers_connected"** and calls `controller->Disconnect()` on every normal player slot plus `handheld->Disconnect()`, then fills only `min_supported_players` slots.

The upstream code introduces an `std::array<bool, HID::HIDCore::available_controllers>` map, checks `parameters.keep_controllers_connected`, pre-reserves connected controllers whose styles remain legal, caps reservations to `max_supported_players`, preserves valid handheld when allowed/undocked, and only disconnects/reconfigures slots not marked to keep. This changes guest-visible HID connection event behavior. It is **not** just cosmetic and can matter independently of the direct PS5 pad adapter. Missing active implementation is a confirmed source-level gap.

**Scoped action:** `verified-relevant-source-gap-awaiting-native-proof`, to be handled on separate corrective PR #46 with exact context/owner and host positive/negative cases, then source-selected native compile and real guest applet/pad tests. Test keep flag on/off; min/max; allowed vs disallowed style; handheld/docked; currently connected slots >max; connection event count; cancellation/teardown. A controller-source test will not prove game boot. No change to `main` or `vendor`.

## Counts after pass 11

155 upstream commits / 2,376 original changed-file entries unchanged. **53** generic runtime semantic decisions pending; **13 source gaps** (including #131); **2** previously separated OpenGL/UTF policy gates; **0** currently unreviewed upstream build candidates; **17** native header inclusion receipts and **7** full C00–C06 qualification gates still open. Audit coverage != release readiness.
