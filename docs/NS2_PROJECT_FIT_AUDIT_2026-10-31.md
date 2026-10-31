# Eden Encore NSW2 — project-fit and source ownership audit

**Date:** 2026-10-31. **Scope:** `research/ns2-ps5-compatibility` and pinned `vendor` research gitlink only. **Production main untouched.** Host CI is not console proof.

## Findings and actual corrections

| Concern | Action | Status |
| --- | --- | --- |
| Imported Eglantine emulator identity | Four `EDEN_NS2_EGLANTINE_*` CMake switches renamed to neutral `EDEN_NS2_*`; imported C++ namespaces renamed to `Eden::NS2::GpuMemory`; attribution retained in comments/review docs | Corrected |
| Parallel Ampere instruction tables | Removed obsolete `headless/ns2/gpu` ISA tree; decoder/address-map host regressions now use canonical renderer-selected Ampere owner | Corrected; host CI required |
| Source forks scattered in app | Moved 64 experimental AM/HLE/Ampere/GPU/NVDRV/CPU6 source files into `vendor/encore-active/ns2-runtime`, plus NPDM helper to `vendor/encore-active/ns2-helpers/include` | Corrected, complete `headless/ns2` source tree removed |
| Stale CMake/CI paths | Switched every referenced research-only CMake source owner, host-test include path and seven research workflows to `vendor`, with a fail-closed source-owner guard | Corrected; current host CI required |
| Fixture-specific runtime behavior | Removed `IsPublicHelloFixture(metadata.GetTitleID(), ...)` special-case SVC admission from real experimental ExeFS loader; keep only generic `KCapabilities`, per-SVC kernel enforcement, and main-thread permission checks | Corrected; test-only five-SVC oracle stays in host fixtures |
| Host JIT `boost::container::bad_alloc` | Raised two **host test** x64 code-cache bounds from 16 to 64 MiB because Dynarmic reserves a 16 MiB prelude, without changing PS5 production JIT | Changed; runtime CI must verify |
| N50/N51 parity snapshots | Refreshed exact Git blob SHA fixtures after namespace relocation, preserving source reversal and original PS5 F07 baseline checks | Corrected; full host CI must verify |

## Project architecture and hard boundaries

1. One maintained source owner for every current NSW2 runtime file under the pinned `vendor` research gitlink. The app carries CI/tests/build selectors and documentation; no `headless/ns2` runtime clones remain.
2. Experimental capabilities remain explicitly OFF by default and disallowed by `EDEN_FINAL_RELEASE_PROFILE`. Any future generic enhancements should be audited against shared PS5/Switch1 owners; avoid game-title IDs in runtime predicates.
3. The vendor still contains some **whole translation-unit experimental loader, NVDRV and HLE variants** behind research-only CMake switches. Moving them into vendor removes duplicated ownership but does **not** convert them into additive modifications to original production engine owners. Those require a separate native build/API review before mainline promotion.
4. Workload names such as FC27 or references to Mario Kart World/Splatoon Raiders describe source attribution or synthetic stress regressions, not game-specific runtime conditions or measured NS2 compatibility.

## What the tests actually prove

- A real pinned vendor gitlink can be checked out, syntactic C++/A64 source owner and source-parity tests run on Linux, a synthetic extracted-ExeFS NSP can be parsed, and public homebrew/Maxwell/SPIR-V oracles can execute in host test environments.
- Old FC27 stress fixtures include synthetic GPU/HUD fault injection: a green result is **not** 30/60 FPS proof or a measured fix on PS5.
- **Not proven:** a Switch 2 commercial title executing all the way through real `Core::System::Load` and `KProcess::Run`; complete HLE/TIPC/NVDRV and Ampere graphics; sparse Vulkan queue binding, fence retirement and RADV output; a native PS5 NSW2 research ELF/PKG and its real in-console boot.
- There are deliberate `NotImplemented` paths in experimental GPU/HLE services. These are fail-closed incomplete semantics, not successful implementations; do not claim Nintendo Switch 2 game compatibility until filled and tested.
- Existing PS5 Encore release packages target the established Switch 1 path. Do not relabel them as NSW2 artifacts. Keep `main` unmodified until a fully isolated native NSW2 integration passes build, release and console readiness gates.

## Release/test gate

**Current verdict: SOURCE OWNERSHIP CONSOLIDATED; NSW2 GAME-READY = NO.**

Only signal the user to test when a real native PS5 build produced from the NSW2 research sources exists as a verifiable artifact, its specific research switches are documented, the entire relevant CI is green for the exact SHA and the smoke-test limits are explicit. Host success alone does not satisfy that gate.

## Primary commits and validation references

- Ampere table deduplication and CPU6 source migration: [9788e3e](https://github.com/niakw/ProsperoEden-Encore/commit/9788e3e8042f8eff3c286d2a9afac8028456cf1f)
- Atomic migration of 62 engine files to vendor: [5c7dc2a](https://github.com/niakw/ProsperoEden-Encore/commit/5c7dc2a0eee19e72f697e409cd66606717b2848b)
- Final NPDM helper migration: [465019f](https://github.com/niakw/ProsperoEden-Encore/commit/465019ff07ad28ab1553b4297fd5f27679f4307b)
- Host JIT cache fixture fix: [1dcee50](https://github.com/niakw/ProsperoEden-Encore/commit/1dcee50342d322ecd11bf3a278dfde40ab3a9575)
- No title-ID exception in runtime: [d705d76](https://github.com/niakw/ProsperoEden-Encore/commit/d705d76c7ee792d7d3366fe733f8d0a6ff3b358d)
- Readability and hash snapshot updates: [00e04e3](https://github.com/niakw/ProsperoEden-Encore/commit/00e04e3eba784fd8eeae8383ea0fb70ae5b25837)
- Host CI: [NS2 research host guards](https://github.com/niakw/ProsperoEden-Encore/actions/workflows/ns2-research-host.yml), [JIT runtime](https://github.com/niakw/ProsperoEden-Encore/actions/workflows/ns2-research-jit.yml), [SPIR-V](https://github.com/niakw/ProsperoEden-Encore/actions/workflows/ns2-research-spirv.yml).

This file documents code facts and validation limits. Update evidence after final run conclusions; never treat running/cancelled jobs as passes.

### Confirmed origin of host JIT bad_alloc (supersedes earlier hypothesis)

The host test CMake recipe still referenced the **deleted** `headless/ns2/cpu6` include directory three times after the source migration. CMake did not reject this nonexistent include root, causing Dynarmic's original `exclusive_monitor.h` to be selected instead. That header has `MAX_NUM_CPU_CORES = 4` and a `boost::container::static_vector`, while both NSW2 host fixtures construct `ExclusiveMonitor{6}`. Adding a sixth element exceeds the static capacity and throws `boost::container::bad_alloc`.

The corrected host recipe points to `vendor/encore-active/ns2-runtime/cpu6` and rejects a missing maintained header at configure time. The source selection test now checks that recipe too. The earlier 16 MiB cache-size hypothesis was **not sufficient** (the error survived increasing to 64 MiB); it must not be cited as the established root cause. The 64 MiB host-only extra headroom does not change PS5 JIT settings. Final successful execution still requires new CI confirmation.

## Final research CI evidence (host only)

The final CMake source owner / host harness revision is `0a447ab7762535b5a34a76254b5048b63e8eab90`; the pinned research vendor revision is `b34ec82d9f3bda22f36f66e2b1e0d3517f76d764`. The source-only CMake and fixture-correction commits after `d705d76` did **not** change NSW2 runtime engine behavior.

| Validation | Proven success | Qualification |
| --- | --- | --- |
| [Source owners, real A64 frontend and N50/N51 parity](https://github.com/niakw/ProsperoEden-Encore/actions/runs/41181510860) | **SUCCESS, both jobs**, revision `0a447ab` | Actual selected host sources, Clang/GCC; not native PS5 |
| [Dynarmic guest JIT and public HOS NSO0](https://github.com/niakw/ProsperoEden-Encore/actions/runs/41181510921) | **SUCCESS**, revision `0a447ab` | Real x64 Dynarmic JIT, six-core overlay, host SVC shim |
| [Verify pinned vendor submodule](https://github.com/niakw/ProsperoEden-Encore/actions/runs/41181123116) | **SUCCESS**, runtime revision `d705d76` | Exact pinned checkout of research vendor |
| [Public homebrew and Vulkan corpus](https://github.com/niakw/ProsperoEden-Encore/actions/runs/41181123044) | **SUCCESS**, runtime revision `d705d76` | Host Linux Mesa/QEMU, not PS5 game rendering |
| [FC27 synthetic workload](https://github.com/niakw/ProsperoEden-Encore/actions/runs/41181123039) | **SUCCESS**, runtime revision `d705d76` | Synthetic stress and historical trace, no gameplay |
| [Real Maxwell IR](https://github.com/niakw/ProsperoEden-Encore/actions/runs/41181123101) | **SUCCESS**, runtime revision `d705d76` | Host translated IR tests only |
| [Real SPIR-V emitter](https://github.com/niakw/ProsperoEden-Encore/actions/runs/41181123166) | **SUCCESS**, runtime revision `d705d76` | Host Vulkan/SPIR-V shader tests only |

**Final audit outcome:** current project-fit cleanup is complete and the supported host research gates are green. The separate Switch 2 compatibility implementation and native PS5 build/boot tests are still unfinished. Do not merge to `main` or announce Switch 2 game support. The active readiness watch must notify only when a real experimental PS5 artifact exists with an explicit console smoke procedure.
