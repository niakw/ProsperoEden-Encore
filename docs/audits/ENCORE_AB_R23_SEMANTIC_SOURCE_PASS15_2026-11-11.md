# R23 pass 15 — #90 (NCE), #33/#136 (Dynarmic x64), #109 (AM lifecycle)

**11 November 2026. E1 pinned source, read-only PR #45.** No code port, native PS5 compiled C++ or guest execution is certified.

### #90 — upstream NCE patch does not execute on the PS5 x64 host

Official [`3f78512c83fca84a36bb450a10043b368830f8b0`](https://github.com/eden-emulator/mirror/commit/3f78512c83fca84a36bb450a10043b368830f8b0) introduces runtime NRO TLS patching inside `#ifdef HAS_NCE` and `Settings::IsNceEnabled()`. The unguarded new method signature passes a KernelCore reference to the same internal call, not a new guest IPC operation. Pinned `sources/eden/src/core/hle/service/ro/ro.cpp` blob **`922fc10440bad898f392b1f290ec18fd2e3cc5e7`** has neither NCE patch use nor the wrapper; PS5 native target is x64 Dynarmic, not ARM64 NCE. Exclusion is limited to the currently intended architecture: actual compiler macro output is a separate native attestation. **Class:** `reviewed-NCE-only-runtime-NRO-patch-not-PS5-x64`. No code copied.

### #33 — x64 Dynarmic constant pool format needs actual JIT qualification

Official [`be972d7fdc50376d231d4f6b0ca912adc958aadd`](https://github.com/eden-emulator/mirror/commit/be972d7fdc50376d231d4f6b0ca912adc958aadd) reworks `constant_pool.cpp/.h`: 64-byte-aligned native constant slots, span of `u128`, compact integer offsets in a dedup map, and changed code-memory commit reserve. Pinned x64 sources `constant_pool.cpp` blob **`8782ab0c73e9defb4f7744063c6691806147effb`** and `constant_pool.h` blob `d3bad95d701c75b3a3e616a46a916590387e867` still use pointer-value map and `insertion_point`. Both are x64 guest JIT paths. **Class:** source gap needing paired changes, Xbyak RIP relocation, dedup and cache-boundary host/native tests. No assumption of performance/correctness parity.

### #109 — AM frontend applets can accumulate without release correction

Official [`847e91c3a8ca2d699cc9ce0df68b733dd5f37b97`](https://github.com/eden-emulator/mirror/commit/847e91c3a8ca2d699cc9ce0df68b733dd5f37b97) reorders `FrontendApplet::Exit()`, erases finished applets from caller `child_applets` under caller lock, requests a window system update and locks caller child insertion in both guest/frontend creator paths. Selected frozen `src/core/hle/service/am/frontend/applets.cpp` blob **`407ca10602a1fe9107d13aa8393f4145ac7d715a`** has a signal-only Exit. Selected `library_applet_creator.cpp` blob **`c20a77f8c40c7fbf023411fd47a299662b798cb3`** appends without new per-caller lock. **Class:** one confirmed two-file source gap; correlate with reviewed #84 None applet and create/exit locking. Native guest process lifecycle, deadlock and display-update testing still required before port.

### #136 — direct x64 page-table sign-extension bug candidate

Official [`1575f55abee50a563502e5afb098ebed9d5d8995`](https://github.com/eden-emulator/mirror/commit/1575f55abee50a563502e5afb098ebed9d5d8995) changes x64 Dynarmic `emit_x64_memory.h` from unconditional `shl` stride to scaled addressing for small stride, and changes sign-bit handling from `shl(page, sign_extension)` to `shl(page, 63-sign_extension)` followed by `sar`. Frozen header Git blob **`9686e4fc047f78d0863df3ccb5149c8ecc9dc484`** retains the former logic. **Class:** confirmed x64 source gap; test configured page-table sign bit, mapping, marked/unmapped page lookups, and x64 Xbyak emitted machine code before admitting C04. The fact it is present does not prove the current NS1 game crash is due to it.

### Updated gates

155/155 upstream commit entries remain recorded; **40** general semantic decisions, **18** confirmed source gaps, **2** separate GL/UTF policy gates, **17** native changed-header proof receipts, **7** corrective release batches. **No production merge, no vendor modification, no full PS5 build.**
