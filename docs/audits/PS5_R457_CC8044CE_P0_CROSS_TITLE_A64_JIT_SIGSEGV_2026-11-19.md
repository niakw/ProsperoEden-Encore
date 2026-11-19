# P0 PS5 — native SIGSEGV during A64 JIT initialization, 19 November 2026

**Status:** source-level ABI mismatch reproduced and rollback committed; host CI and new native build remain qualification gates; PS5 console runtime NOT yet revalidated. [Issue #297](https://github.com/niakw/ProsperoEden-Encore/issues/297).

## Verified console evidence from `Archive(4).zip`

Tested engine `cc8044cee42ad0e74af4edadaac6595de9128c31`, vendor `6c38328fbef33de747f5c31ea30d13541a513a4a`, firmware 13.60, [run #44520885201](https://github.com/niakw/ProsperoEden-Encore/actions/runs/44520885201).

| Title / mode | Report | Native RIP | Fault address | Last known stage | GPU commands completed |
|---|---|---|---|---|---|
| FC27 / NS1 `0100c49025d3e000` | `ns1/crash-20261119-140804.txt` | `0x8000ac03f` | `0x7` | `guest_loading`, first `EDEN_JIT_FEATURES` | 0 |
| Bananza / NS2 `040074a01bf12000` | `ns2/crash-20261119-140903.txt` | `0x8000ac03f` | `0x7` | `guest_loading`, first `EDEN_JIT_FEATURES` | 0 |
| Mario Kart World / NS2 `0400c3f00006e000` | `ns2/crash-20261119-141015.txt` | `0x8000ab98d` | `0x7` | `guest_loading`, JIT `SPARSE_TRIM` observed | 0 |

The reports' native RIPs are outside the PS5 app ELF, and the reporter's candidate calls on the stack are **heuristic**, not a verified native unwind. Symbolizing likely eboot return addresses against exact [run #44520885201] ELF shows `Core::ArmDynarmic64::MakeJit`, `Dynarmic::A64::Jit`, `A64EmitX64::GenFastmemFallbacks`, Xbyak emit and Boost flat-map stack candidates. The NS1 report still has a 7,712 MiB largest free extent; neither memory exhaustion nor an Ampere/Vulkan rendering failure is established. Empty secondary crash files may be interrupted report writing, not separate fully evidenced incidents.

## Root cause: cross-translation-unit C++ class layout divergence

The selected A64 dispatch header, `vendor/encore-active/eden-core/src/dynarmic/backend/x64/a64_emit_x64_standard.h`, had acquired a conditional **class member array** from vendor [6c38328](https://github.com/niakw/Prospero.Eden-Encore-vendor/commit/6c38328fbef33de747f5c31ea30d13541a513a4a): `PS5_NATIVE` made 65,536 entries (1 MiB), otherwise 1,048,576 entries (16 MiB). [EglantinePS5 #104](https://github.com/heydemoura/EglantinePS5/pull/104) instead gates its native behavior with toolchain-wide `__PROSPERO__`, **not** our selectively applied `PS5_NATIVE`.

Engine `headless/CMakeLists.txt` applies `PS5_NATIVE=1` **per source** to the `a64_interface.cpp` constructor/owner TU but not the generated out-of-line `a64_emit_x64.cpp` and `a64_emit_x64_memory.cpp` units. They include the same C++ header, but disagree on `sizeof(A64EmitX64)` and member positions. Independent compilation succeeded despite an ODR/ABI violation.

### Reproducible negative and positive host controls

A Clang two-TU AddressSanitizer fixture reproducing exactly the old member-array sizes yields a **heap-buffer-overflow** when the `-DPS5_NATIVE=1` owner allocates 1,048,576 bytes and the unflagged method fills 16,777,216 bytes. The same fixture with the rollback's unconditionally 16,777,216-byte class terminates successfully. This proves a real native corruption mechanism, **not** that the exact PS5 `0x8000ac03f` RIP was definitely caused by this particular write.

### Native machine-code proof from the exact crashed package

Independently disassembled the **real compiled** `Encore-R457-symbols.elf` from the
verified `cc8044ce` package (SHA256
`719895f14998f0001000d2437bb5c516bf22f7d65ed39b9a2216c1afcf603a27`).
The incompatible class layouts are visible in x86-64 instructions, **not only
in the CMake or headers**:

```asm
0x242d807: mov edi, 0x104000               ; Jit::Jit allocates 1,064,960 bytes
0x242d811: call operator new               ; aligned owning Jit::Impl
0x242dbc5: lea r12, [rbx+0x1700]          ; emitter member inside Impl
0x242dc0f: call 0x242f000                  ; A64EmitX64::A64EmitX64(...)
0x242f224: mov qword ptr [rbx+0x10017f0], 0x3f ; constructor field at >16 MiB
0x242f23a: mov qword ptr [rbx+0x1001808], 0
```

The out-of-line constructor writes to an object field more than **14.99 MiB
past** the total heap allocation made by the inlined owner constructor, even
*before* accounting for the emitter member's positive offset. This proves a
definite out-of-bounds code path in the **installed console binary**. A
separate source-level ASan reproducer supports the same mechanism, but the
exact system-library `RIP=0x8000ac03f` remains to be confirmed via new
console execution. The corrected ELF must be checked for a consistent
`Jit::Impl` allocation and `A64EmitX64` field offsets before asking for
another hardware test.

## Corrective lineage and test controls

- Vendor [8e564f61](https://github.com/niakw/Prospero.Eden-Encore-vendor/commit/8e564f61e6c8b86149ce0a0d6d2aa323a268dda6): restores the **byte-exact previously used** stable 16-MiB A64 dispatch table and old mask, keeping all other vendor runtime fixes untouched.
- Engine [8376bbda](https://github.com/niakw/ProsperoEden-Encore/commit/8376bbda212a3e5aaa7ff0298f0f45be798d143e): pins that vendor, upgrades `tools/check-maintained-emitters.py` to enforce one class layout under both preprocessing modes.
- Engine [4cbc5472](https://github.com/niakw/ProsperoEden-Encore/commit/4cbc5472b9b7d28db145d6618191c749320198f4): updates seven checked vendor-graph provenance gates, keeping exact FC27/Vulkan hashes.
- Engine [fdf5ec90](https://github.com/niakw/ProsperoEden-Encore/commit/fdf5ec90b7801ce410c3145c4aed434e758bc2fd): fixes the CMake generated-A64 filename assertion in the gate. It now tests actual target ownership.
- Both vendor host/security workflows passed on `8e564f61`. Engine source preflight and core fast gate are running for `fdf5ec90` at the time of this audit. Any failed CI prevents qualifying the next build.

## Acceptance gates and open issues

1. Source preflight (six shards), core fast gate, CodeQL/security, strict gitlink and native build source checks. Do **not** treat a skipped native job as success.
2. One native PS5 SELF and package with verified ELF/map and exact engine/vendor SHAs, followed by real firmware 13.60 launch evidence.
3. Confirm all three games advance past the native A64 JIT startup without SIGSEGV. Only then separately diagnose FC27 HUD, frame pacing, pause and repeat-launch [#100](https://github.com/niakw/ProsperoEden-Encore/issues/100) / [#281](https://github.com/niakw/ProsperoEden-Encore/issues/281) and the NS2 guest `PC=0x4` [#123](https://github.com/niakw/ProsperoEden-Encore/issues/123).
4. For A/B comparison, preserve current shader caches and old logs; do not wipe saves. New full build must be distinguishable from tested `cc8044ce` even though the displayed R revision may remain R457.

**Do not close #297 from a compiler-green result alone.**
