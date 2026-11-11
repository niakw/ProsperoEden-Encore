# R23 pass24 — selected G11 debugger and x64 RO/NCE applicability

**11 November 2026. Evidence level E1 only.** Exact official upstream patch plus pinned selected production source comparison; this is not a GDB guest session, compiled PS5 ELF proof, or empirical debugger correctness proof.

## #10 — partial native equivalence; **A32 debugger optimizer guard remains missing**

Upstream [`656cdd948e09`](https://github.com/eden-emulator/mirror/commit/656cdd948e09) changes six files, adding cached-code-page reset `m_cb->last_code_addr = u64(-1)` before `InvalidateCacheRange` for A32 and A64, and disabling `Optimization::A32GetSetElimination` when `conf.check_halt_on_memory_access` so GDB-stub watchpoints/halts cannot be eliminated by the optimizer. This last condition already existed for A64.

The original pinned vendor `sources/eden/src/core/arm/dynarmic/arm_dynarmic_32.cpp`, blob **`80e2b2dca9f7e83b7ef00820b63c7b13bb01ee48`**, and original A64 `arm_dynarmic_64.cpp` blob **`9662bf17129c48fa7e88ab2ff7027665eccaf5ee`** are **NOT the selected native owners**. `headless/CMakeLists.txt` selects:
- Native G11 A32 `vendor/encore-active/eden-core/src/core/arm/dynarmic/g11/arm_dynarmic_32_native_normal.cpp`, blob **`753f1fc3f8fc9807d64a997e48b057ddde3b3ca7`**: **already** resets `last_code_addr` in `InvalidateCacheRange`, rejects zero-size invalidation, handles addresses outside u32 bounds with a cache-clear fallback. No redundant upstream cache-reset patch.
- Native G11 A64 `vendor/encore-active/eden-core/src/core/arm/dynarmic/g11/arm_dynarmic_64_native_normal.cpp`, blob **`b03c862e9e2d54adaa49e4200bd980ec6d605c0b`**: **already** resets `last_code_addr`, rejects zero size.
- However the actually compiled Dynarmic common optimizer `sources/eden/src/dynarmic/src/dynarmic/ir/opt_passes.cpp`, blob **`02b8e821da888b2b5a25b642c6b3ee8b71b5d4cf`**, still has `if (conf.HasOptimization(OptimizationFlag::GetSetElimination))` on **A32** (no `!conf.check_halt_on_memory_access` guard). Its A64 optimizer already has the debugger guard. The source paths include `core/arm/dynarmic/arm_dynarmic_32.cpp` and `dynarmic/ir/opt_passes.cpp` in the standard/native targets, with G11 A32 ownership replacing the original.

**Disposition:** source-verified **partial** relevant gap #10, **NOT** a 6-file blind backport. Only A32 debugger safety remains source-different; A32/A64 native cached-code invalidation already has an equivalent or stricter implementation. Runtime acceptance: A32 guest breakpoint/watchpoint and HaltExecution with optimization enabled, emitted IR inspection on watchpoint, GDB attach/detach/restart, A64 negative/no-regression; source-only proof does not certify debugger support on actual PS5.

## #68 — x64 RO memory protection already matches; runtime NCE patch is outside PS5 native backend

Upstream [`aaa0bcb9bf56`](https://github.com/eden-emulator/mirror/commit/aaa0bcb9bf56) changes nine files. Its actual RO runtime change is guarded by `#ifdef HAS_NCE`: new arm64 host `NCE::Patcher(std::span<const u8>)`, `RelocateRuntimeTls` and shared memory patching of runtime NRO/TLS. The Android/settings changes expose the NCE runtime patch toggle.

On the pinned **PS5 x64 Dynarmic** native path, no `HAS_NCE` compile definition in the selected headless CMake graph. This is consistent with the separate earlier E1 #82 architecture guard review: NCE is ARM64 (Linux/Android) host-specific and not a PS5 guest ARM64 direct execution replacement. The active maintained RO owner in native graph is the pinned `sources/eden/src/core/hle/service/ro/ro.cpp` blob **`922fc10440bad898f392b1f290ec18fd2e3cc5e7`**, which **already validates the guest NRO regions and calls unconditional `SetNroPerms(context->GetProcess(), base, rx, ro, rw+bss)`** before committing the module info. There is **no `#ifdef HAS_NCE`** in that original pinned `ro.cpp`; the upstream line move does not change the native x64 guest protection policy. On x64, porting the ARM64 NCE patcher would be an unrelated backend fork and can harm the single native target.

**Disposition:** reviewed **native-scope equivalent/no NCE runtime patch**, no PS5 production port required. This applies ONLY to selected x64 native build. It **does not** certify ARM64 Android NCE, Linux, or a future alternative direct-execution PS5 backend. Keep tests for RO NRO RX/RO/RW+BSS permissions, unload/reload and invalid region boundaries on real guest; these are device E4 gates but not a generic unsettled R23 semantic branch.

## Accounting and boundaries

#10 moves generic → **verified relevant partial source gap**. #68 moves generic → **source-scoped current PS5 native equivalent/no-port**. Generic upstream semantic reviews **22 → 20**, confirmed source gaps **28 → 29**. The unchanged **8** separate refactor/policy decisions, **17** compiler-header inclusion receipts, **0/7** full PS5 corrective-release gates, native game launch and R18 security/provenance obligations still block exhaustive signoff. No implementation changes, no merges, no experimental runtime modes.
