# PS5 P0 — Mario Kart World native sparse-memory boot fault (13 November 2026)

**Status:** native candidate source integrated; **PS5 hardware result pending**. No release or compatibility claim.

## Correlation and reported symptoms

The owner saw a SIGSEGV report at 07:52:23, 23 seconds after Encore started, while navigating with Circle; two subsequent PS5 `CE-108262-9` system errors occurred during repeated launches/autoloader attempts. The native boot trace associated with the same session records **`launcher closed: game selected` at +22877 ms**, followed immediately by the fault. Treat this as the **MKW startup fault**, not proof of a separate Circle-to-exit crash. The two system errors are confirmed reports, but neither their origin nor their causal relationship to the emulator is proven.

Observed: `SIGSEGV`, `si_code=2`, fault and `RDI=0x00000010dc20a000`, `RDX=0x0000000001100000` (17 MiB), `RIP=0x00000008000b8766` outside the ELF, main thread. `GPU completed commands=0`, `watchdog stalls=0`, `invalid guest-memory accesses=0`; largest free direct-memory block 11774 MiB / 12416 MiB. No evidence of exhaustion of the entire available direct-memory pool. The fault is *consistent* with a system zero-fill of a reserved but uncommitted guest backing page; proving the exact call site still requires the **matching unstripped ELF** (code-size signature `0x26da180`) and available system-library mappings.

## Integrated code changes

- Vendor [#98](https://github.com/niakw/Prospero.Eden-Encore-vendor/pull/98), merged as `f0f12590ff12e5e537284b6407966aa4e2341a5c`: NS2 `KSharedMemory::Initialize` uses `DeviceMemory::buffer.ClearBackingRegion(offset, size, 0)` under `PS5_NATIVE && EDEN_NS2_SPARSE_BACKING`, instead of raw `GetPointer` + `memset`. Maintains the prior `EdenNs2CommitGuestBacking` pre-admission and emits bounded begin/done diagnostics on blocks >=1 MiB.
- Encore [#95](https://github.com/niakw/ProsperoEden-Encore/pull/95), merged as `a71c24c3b847d60519a254565c7ac50e7e59bd8b`: native fatal signal handler saves the report and asks system services to EXIT, not silently restart. Desktop crash-test behavior remains unchanged. Ships associated UI/catalog changes and vendor gitlink pin `3c08dc54334a30889acea7d0eb38753bcabe4ce6`.
- Source owner `src/host_memory.cpp`: `HostMemory::ClearBackingRegion` validates `offset/length`, commits sparse pages through `impl->sparse->Commit(offset,length)`, then writes to the backing base. Upstream `sources/eden/src/common/host_memory.cpp` is **not** the linked PS5 implementation; check native CMake source selection if compilation/regression differs.

## Gates before claiming a fix

1. CI host regression, security, vendor consistency and native preflight must pass on **merged main**, not solely on PR SHA.
2. Full native PS5 build must produce an ELF + test package against an attested main SHA and pinned vendor; check link warnings, packaging and release metadata. **Never auto-publish**.
3. Validate MKW boot three successive cold starts and two warm returns, then try Bananza and FC27 NS1. Record crash report and `EDEN_NS2_SHARED_CLEAR begin/done` pairs; inspect first missing `done`.
4. Explicitly distinguish **game selection**, **return from game to launcher**, and **Circle application quit** on PS5. Each must avoid a console/system crash and an uncontrolled restart. Evaluate title/video shutdown, GPU fences, audio thread joins, JIT teardown and direct-memory releases independently.
5. Preserve and symbolize original report only with matching code-size `0x26da180` and exact original build ELF, not a newer candidate ELF. A stack scan marked `?` does not establish a verified call.
6. Two `CE-108262-9` errors warrant caution with repeated autoloader/console restarts; do not assume a host-only success makes the PS5 safe.

Tracking: [P0 #97](https://github.com/niakw/ProsperoEden-Encore/issues/97). Green CI is not a GPU boot or firmware-13.60 qualification.
