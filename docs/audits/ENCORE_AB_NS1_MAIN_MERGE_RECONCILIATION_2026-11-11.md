# NS1 corrective PR #46 — merge reconciliation safety register (11 Nov 2026)

**Isolated research, no merge or vendor repin.** This document compares PR #46 at `01d4bedef04efb2d134b3074ef4000a4cdb15a5a` with `main@ce175860d6a1692967ddf50702af72d430766826`, at the time of observation. GitHub reports `mergeable_state=dirty`. **This is not a resolved merge conflict** or a qualification to override newer main code.

## Frozen history and vendor truth

- Shared corrective fork baseline: `main@d829ab4ed7e76f6341a45145e2e70dc180c0e518`.
- Correction branch vendor gitlink: `22b69d6053db41b74edac2633c012f925b84f69e`.
- Current main vendor gitlink: `90c9c8a203a27181e23349a889a8f2a7d1cd9dd2`.
- Vendor-maintained IPS `encore-active/eden-core/src/core/file_sys/ips_layer.cpp` is **the same blob** `f6687abf25ef2874c06c2523c530b5ba197e6d45` at BOTH pins. Do not replace it with the older source-derived headless IPS duplicate. The later corrector removed that duplicate, preserving the one selected native source.
- Full native/PS5 test has **not** executed at the corrective SHA; any green GitHub host checks provide a narrower contract.

## Shared paths independently changed after fork on both branches

1. `headless/CMakeLists.txt`. Latest main introduced a pinned native libwebp C SSE2 ABI exception and real shader atomic CAS owner selection. Corrective PR additionally selects C00 device session, C01 RomFS, C02 shared SPIR-V, R23 F2I/BCAT/Audren, controller #131 and reviewed header. **Merge requirement:** preserve all new main WebP/CAS and other PS5/NS2 rules; apply corrective source selectors in their true final target-order with exactly one selected file for each owner, and native CMake graph/source command attestation. Never overwrite entire main CMake with the corrective branch's older copy.
2. `tools/prepare-vulkan-port.py`. Latest main adds capability-guarded Vulkan image/view and sampler GPU pins safe for the OpenGL target. Corrective PR proposes a negative-Y viewport source transformation. **Merge requirement:** preserve main's OpenGL-safe pin capability checks; qualify viewport against actual maintained Vulkan rasterizer owner (not only generator output). No bulk replacement of the generator file.
3. `docs/EDEN_POST_F07_CHANGED_SOURCE_REGISTER_2026-11-08.json`. Main updates graphics/JIT source receipts; PR #46 adds C00 AudioIn source receipts. **Merge requirement:** reconcile entries semantically, preserving historical baseline/count and SHA/byte contracts. This register is not an implementation target.
4. The `vendor` gitlink itself differs (see pins above). **Merge requirement:** resolve dependency/API compatibility using current production pin and native compilation; do not silently reset main to `22b69d6` or force update current vendor.

These are **overlapping paths and pin hazards**, not verified exhaustive Git conflict markers. Actual conflict hunks and source versions must be obtained against a frozen new integration branch from latest main before ready-for-review.

## Narrow acceptance sequence (avoid 150 full builds)

- Reconcile existing current main source owners against isolated changes, inspect exact native CMake `core`, `audio_core`, `video_core`, `shader_recompiler`, RADV Meson owners, and header include order. Reject duplicates and missing owners.
- Host sanitizer+source tests for C00 AudioIn, C01 RomFS, C02 SPIR-V, R23 IPS/Audren, #131 HID and original/maintained code receipts.
- Cross compile the **actual changed C/C++ units only**, plus link-map/header dependency checks. Do **not** relink or package a PS5 release if these fail.
- Integrate C03 RADV as a coherent three-unit fix and qualify Dynarmic x64 C04 only after selected maintained owners, tests and ABI are known; do not import unreviewed Mesa/Eden changes.
- One controlled PS5 native build and game/launch session matrix for NS1 crash, AudioIn, RomFS, Vulkan/OpenGL, shader output, controller applet, IPC firmware 23 command and shutdown. Compare exact ELF SHA/SDK headers, source-owner receipt and logs. Package/release only after all gates succeed.

**Status at writing:** PR #45 has 52 generic semantic decisions pending, 2 scoped policies, 13 source gaps, 17 header proofs and 7 corrective release batches not fully qualified. PR #46 remains draft, conflicting, and not merge-ready. **No part of this document certifies PS5 functionality.**
