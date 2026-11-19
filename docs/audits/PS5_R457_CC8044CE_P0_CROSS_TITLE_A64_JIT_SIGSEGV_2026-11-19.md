# P0 PS5 — native SIGSEGV during A64 JIT initialization, 19 November 2026

**Status (19 Nov, 15:30 Europe/Paris):** A64 class-layout bug corrected in source and verified in the newly compiled native ELF; host CI and PS5 native build #44538202373 succeeded. PS5 console runtime NOT yet revalidated; P0 remains open. [Issue #297](https://github.com/niakw/ProsperoEden-Encore/issues/297).

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


## 19 November — verification of the **corrected** machine code and real downloadable artifacts

**Exact qualification:** [native PS5 run #44538202373](https://github.com/niakw/ProsperoEden-Encore/actions/runs/44538202373), engine `4a5b8cc05a662130b9033f7d9b97869c8df3310a`, Git submodule vendor **`8e564f61e6c8b86149ce0a0d6d2aa323a268dda6`** (confirmed in the engine commit's Git tree, mode `160000`). The build job completed successfully, including native compilation, staged app verification, FTP archive round-trip, release checks, ELF/map binding and artifact publishing. The independent `release` job was skipped, not a second build pass.

The actual downloaded corrected release ZIP and its contained `build/symbols/Prospero.Eden-Encore-R457.elf` were opened; the ELF is x86-64 PIE **unstripped** and matches the manifest (202,775,120 bytes, SHA-256 `87a12ed2cc08cb7bfeb97c306f6420e1308e71060f349920a0161a695be4a174`). Disassembly of the corrected executable, **at the same code addresses as the crashed build**, confirms the ODR-layout repair:

```asm
0x242d807: mov edi, 0x1004000               ; owning Jit::Impl allocation: 16,793,600 bytes
0x242d811: call operator new
0x242dbc5: lea r12, [rbx+0x1700]          ; A64EmitX64 object within Jit::Impl
0x242dc0f: call 0x242f000                  ; A64EmitX64::A64EmitX64(...)
0x242f20b: cmp rax, 0x10018b0              ; constructor's 16 MiB table initialization bound
0x242f224: mov qword ptr [rbx+0x10017f0], 0x3f
0x242f2bf: mov qword ptr [rbx+0x10018b8], 0x1
```

The sampled last constructor write through `rbx+0x1700+0x10018b8` ends at `0x1002fc0`, **4,160 bytes inside the 0x1004000 allocation boundary**. The old confirmed broken artifact allocated only `0x104000` but used the *same* >16 MiB constructor field offsets. Thus the exact observed cross-TU allocation/constructor inconsistency is no longer present in this binary. This is binary proof for **this ABI fix**, not a claim that all JIT bugs or the previous console RIP are resolved.

**Distribution audit — downloaded bytes, SHA-256 and every ZIP member individually checked:**

| Archive | Size compressed | ZIP members | SHA-256 |
|---|---:|---:|---|
| `Eden-Encore-PS5-FTP-PPSA99008` | 41,188,012 B | 200 | `8882d8998c4a3429fbce7eaa4d1ddbe19305879b342d843c2a4b96c4315ede42` |
| `Prospero.Eden-Encore-release` | 163,369,892 B | 7 | `e8ac89ebf68be780b3fd44d5e6894ad5e28191101007e2b5cccd7bb774139a2e` |
| Nested full distribution `Prospero.Eden-Encore-R457.zip` | 40,983,122 B | 279 | `425f944e47010726f405659a56f9c80215e4545403d2461367f9cbcb4c2bb804` |
| Nested light FTP `Eden-Encore-R457-4a5b8cc0-FTP-PPSA99008.zip` | 39,544,158 B | 87 | `60d42722e3b6c8cc2eee4ef98df2e7c4bdd9df32c4d9ba3e8bc8fd4116fb4001` |

All four ZIPs pass CRC and name/path validation; **zero** duplicate members, zero empty files and zero unsafe paths. Each of 200 FTP files is byte-identical to its counterpart in the full distribution; each of 87 light FTP files likewise matches. The full ZIP adds 79 root-level documentation/license files. The light FTP ZIP deliberately omits legal documents and the 31 redundant `.txt` locale copies; the complete FTP artifact preserves **31 `.po` and 31 identical `.txt` catalogs**. `eboot.bin` SHA-256 `a681cc396cd64cb66258f61d1d93f3a26c22abe963fc34778ed675ac63c5c8f6` matches all packages and the crash-provenance manifest. `link.map` and debug ELF also match manifest sizes and hashes. No payload mismatch found.

**Native warnings:** 8,380 build-log lines read. No actual C/C++ `warning:` diagnostic or compiler error is present in this run; note that caching can hide warnings from unchanged dependencies. Remaining nonblocking output: Mesa cross-compile TLS-dialect auto-detection (`meson.build:639`), Node `[DEP0005] Buffer()` from third-party GitHub `download-artifact`, and an OS-version `#pragma message` note in `u_process.c:186`. Keep these tracked under [#108](https://github.com/niakw/ProsperoEden-Encore/issues/108), without muting diagnostics.

**Still unverified:** `crash-provenance.json` intentionally reports `confirmed_same_console_binary=false` and `native_ps5_execution_verified=false`. The user is testing the new package on firmware 13.60. Preserve shader caches, pre-fix crash reports and saves for the A/B test. Do not close [#297](https://github.com/niakw/ProsperoEden-Encore/issues/297) without FC27, Bananza and MKW startup evidence; [#281](https://github.com/niakw/ProsperoEden-Encore/issues/281), [#100](https://github.com/niakw/ProsperoEden-Encore/issues/100) and [#123](https://github.com/niakw/ProsperoEden-Encore/issues/123) remain independent.
