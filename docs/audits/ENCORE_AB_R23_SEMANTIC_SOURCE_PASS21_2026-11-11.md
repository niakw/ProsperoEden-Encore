# R23 pass21 — actual selected NS1 HLE service gaps: SSL #120 and session limits/BPC #149

**11 Nov 2026.** Exact upstream source diff + pinned-current vendor source owner check. Scope E1 only, PR #45, no source port, no actual PS5 IPC/console certification.

## #120 — SSL functionality is genuinely absent in the native source owner

Official Eden [#120 `8c1194474e`](https://github.com/eden-emulator/mirror/commit/8c1194474e) changes three coordinated units: `core/hle/service/ssl/ssl.cpp`, `ssl_backend.h`, `ssl_backend_openssl.cpp`. It adds actual implementations to formerly null IPC handlers `Peek`(13), `Poll`(14), `Get/SetRenegotiationMode`(20/21) and several socket/hostname/session methods, plus backend ABI changes. At current vendor `f8f5d8e` the original `sources/eden/src/core/hle/service/ssl/ssl.cpp` blob **`750a7de236a8606b139bb9b2529c75e412cb104a`** still lists command 20/21 as `nullptr` and has no `Peek` or `Poll` implementation. Original OpenSSL implementation blob **`f0e05266ba0bc2bbbb2f94208c87c85df6cce573`** does not implement the new `SSLConnectionBackend` API. The actual maintained `encore-active/eden-core/src/core/hle/service/` tree contains no `ssl` override owner; selected original CMake/compile database still needs final target receipt, but no maintained implementation was found in the inspected source slots.

**Disposition:** source-verified NS1 HLE SSL gap, E1, release-level OPEN. Do not copy only `ssl.cpp`; native ABI requires three matched units. Tests: CMIF command IDs/result codes, socket ownership, null/short buffers, blocking/nonblocking, renegotiation policy, OpenSSL error semantics, pause/resume and guest old/new FW; target SDK/OpenSSL linkage must be proven.

## #149 — guest service session limits and bpc:ams missing in original native owners

Official Eden [#149 `8a22f1845b`](https://github.com/eden-emulator/mirror/commit/8a22f1845b) adds `bpc:ams` (commands 65000/65001 stubs), explicit max-session caps (BPC=13, bpc:ams=4, audio=30 except hwopus=25) and related service caps, plus an audio renderer session ID guard. Pinned `sources/eden/src/core/hle/service/bpc/bpc.cpp` blob **`6fd7001821e7e4c762861ccb97472e300c823376`** has five BPC services with default caps and **no `bpc:ams` registration**. `sources/eden/src/core/hle/service/audio/audio.cpp` blob **`c4332833042d7bca6309fdbe532637d80d90b4e6`** still registers audio without explicit caps. Existing `server_manager.h` blob `5173ce46e1b0acce0d68f2373590d065279281b5` provides the compatible optional `max_sessions=64` parameter, but current service defaults are not semantically equivalent to the upstream caps. No maintained BPC source override exists under `encore-active/eden-core/src/core/hle/service/`. This does not prove crashes but is a **real guest-visible resource policy difference**.

**Disposition:** source-verified NS1 HLE service gap, E1, release-level OPEN. Preserve the already staged separate #46 audren:d fix; do not mistake it for #149 session cap change. Tests: create/reject/retire per-service sessions, no off-by-one on `audio_render_manager`, bpc:ams stub commands and handles, old firmware fallbacks, service startup/shutdown with many guest threads.

## Strict counter update

Both cases move from the generic unreviewed bin into the **verified relevant source-gap** bin, **without** calling them runtime repaired. Generic 28 → **26**. Verified relevant source gaps 22 → **24**. Scoped policies **8**; native header include receipts **17**; complete C00–C06 release gates **0/7**. No production code modified, no automatic branch merge or repin.
