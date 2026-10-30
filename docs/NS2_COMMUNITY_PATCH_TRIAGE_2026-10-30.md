# Switch 2 community patch — triage for PS5 Encore (2026-10-30)

## Evidence and provenance

A user supplied **NS2.patch.txt** (733,058 bytes, 14,931 lines), described in community discussions as an Eden PC patch. The diff changes **154 files**, creates **39 files** and adds approximately **11,700 lines** (187 deletions). This file is **untrusted experimental research input**, not a verified release, not necessarily attributable to the public repositories, and must **not** be applied wholesale.

Compare against the maintained sources at:

- https://github.com/0x2593/Eden-NS2 (main)
- https://github.com/ShadyHero/Eden-NS2 (main, redirects contributors to 0x2593)
- https://git.eden-emu.dev/eden-emu/eden/pulls/4588 (draft Switch 2 test build; its test status must be checked independently)

Spot checks on 2026-10-30 showed that all of the following **paths already exist** in 0x2593 and ShadyHero: `graphics_supervisor.cpp`, `gpu_session.cpp`, `dynarmic/tests/A64/lse.cpp`, `video_core/native_qmd.h`, `shader_recompiler/frontend/ampere/lower_to_maxwell.h`, `renderer_vulkan/vk_pipeline_cache.cpp`. Of eleven Git blob hashes reconstructed from *new-file* patch hunks and checked against 0x2593 main, **one matched byte-for-byte** (`program_override.h`); the others differed. Do not assume the uploaded snapshot is current, or copy old code on top of newer changes.

## What the configuration actually does

The circulated PC configuration sets:

```ini
[Core]
memory_layout_mode\default=false
memory_layout_mode=4
use_multi_core\default=false
use_multi_core=false

[Renderer]
backend\default=false
backend=1
```

Verified against Encore vendor `src/common/settings_enums.h`:

- `MemoryLayout`: `Memory_4Gb=0`, `Memory_6Gb=1`, `Memory_8Gb=2`, `Memory_10Gb=3`, `Memory_12Gb=4`; **4 selects a 12 GiB guest layout**. PS5 has a shared memory budget: *never* hard-code 12 GiB without measuring actual process/renderer/JIT availability and testing OOM handling.
- `RendererBackend`: `OpenGL_GLSL=0`, `Vulkan=1`. Encore PS5 already targets Vulkan. No native PS5 improvement from merely copying this INI.
- `use_multi_core=false` disables guest multicore; it can help isolate a race on a PC, but is not a performant PS5 release setting. Six guest CPU cores and exclusive monitor behavior require correct concurrent operation.

The `\default=false` keys are configuration override flags, not executable patch code. Never apply a PC SDL/Qt INI file as the PS5 runtime configuration.

## Components in the patch and PS5-native priority

1. **P0 CPU correctness & HLE loading.** Keep existing isolated RETAA/RETAB, LDAPR, LSE and NPDM/ExeFS owners. Extend real JIT tests and use `dynarmic/tests/A64/lse.cpp` / `pauth_returns.cpp` as test references, including CAS failure and retry, acquire/release ordering and six-guest-core contention.
2. **P0 kernel + services necessary to bootstrap.** Diff `SetGpuMemoryAttribute`, additional SVC/get-info, kernel process lifecycle, `application_proxy`, `graphics_supervisor`, `gpu_session`, TIPC, `nvhost_tsg_gpu`. Port only proven service contracts with synthetic packet tests and ownership/lifetime checks. Do not turn unknown commands into fake success.
3. **P0 Ampere → PS5 Vulkan.** Assess `lower_to_maxwell.h`, `native_qmd.h`, `program_address_map.h`, `native_gpu_characteristics.h`, native GPU kinds/context, shader cache, submit/syncpoints and VK rasterizer/cache. Prefer newer upstream and preserve Encore's PS5 RADV pipeline behavior, sparse JIT, memory manager and texture/HUD fixes. Shader architecture support **cannot** be produced by selecting `backend=1`.
4. **P1 image/frame presentation.** Review VI2, fences, NVNflinger and native image layout for PS5 rendering correctness. Never claim `Present` is complete until actual synchronisation and frame output are measured.
5. **P1 compatibility/repro.** Maintain Switch 1 behavior through strict mode gating and full existing F07 host/PS5 regression CI. Test the full PS5 memory allocation budget instead of copying a desktop setting.

## Merge gate

- All Switch 2 modifications remain in `research/ns2-ps5-compatibility`, isolated from `main` and shipping binaries.
- Never apply the entire 154-file patch or replace `vendor` from an unverified snapshot.
- Require focused source ownership, buildable tests, host runtime correctness, PS5 builds and actual console evidence before a selected feature is merged.
- As of this audit **no Switch 2 game is validated running on Encore PS5**. Host tests and HLE/shader probes are not game compatibility proof.
\n## N3a — Scoped graphics HLE protocol fixtures\n\n- Versioned upstream reference: `0x2593/Eden-NS2@5d2d3cf0a966293fc9ddeac33cf86830a5de206e` for `graphics_supervisor_protocol.h`, `native_image_layout.h` and `native_gpu_kind.h` (byte-for-byte copies in `headless/ns2/hle`); scoped `gpu_memory_registration.h` decoder from the user's `NS2.patch.txt` to avoid pulling unsupported sparse-remap dependencies.\n- Runtime host fixtures: `python3 tools/check-ns2-graphics-hle-host.py`, C++20 O0/O2 + UBSan; checks malformed TIPC, copied handles/identities, syncpoint width, frame sizes/pitch/padding, MMU compressed/uncompressed kind fallbacks and rejection of unsupported kinds.\n- This is an **isolated tested data/ABI layer**, not yet wired to `IApplicationProxy`, `IGraphicsSupervisor`, NVDRV or the actual video compositor. No change to the release's GPU service table.\n- Next merge gate: owner-aware `graphics_supervisor.cpp` integration, per-command handlers and tracing, then Vulkan/RADV frame submission and PS5 device memory tests.\n\n## N3b — Native AM application-manager command 320 (research build only)\n\n- Original source owner retained: `vendor/encore-active/eden-core/src/core/hle/service/am/service/application_functions.cpp` at `vendor` commit `92c5829174a1169c507b72438021d3dfa9e5dfa2`; no regression to its title/update metadata handling.\n- Added only `GetScreenShotAndContinuousRecordingInitiallyEnabled` (command `320`) per current `0x2593/Eden-NS2@5d2d3cf0`: reads existing locked applet screenshot and recording state, rather than claiming success with fixed values.\n- Build selection: `EDEN_NS2_AM_EXPERIMENTAL=ON` additionally requires `EDEN_NS2_METADATA_EXPERIMENTAL=ON`; CMake checks that the maintained AM source is the one being replaced. All options remain **OFF** in shipping profiles and the final release gate explicitly rejects AM experimental mode.\n- Host CI compiles the real full overlay TU with the corresponding isolated class header. This is **not** a real guest IPC runtime test; no new graphics supervisor instance, GPU command submission, or PS5 frame output is claimed.\n
## N3c — NVDRV native GPU characteristics packets (isolated)

- The experimental owner `nvhost_ctrl_gpu.cpp` is a copy of the pinned Eden source at `92c5829174a1169c507b72438021d3dfa9e5dfa2`, with a focused branch for **only** raw IOCTLs `0xc0e04705` (208-byte native characteristics) and `0xc0e84705` (216-byte native characteristics). All other requests retain the existing Maxwell `WrapFixedInlOut` dispatch. There is no global switch of guest GPU topology.
- Pure response builder `native_characteristics_ioctl.h` reuses upstream `native_gpu_characteristics.h` (`0x2593/Eden-NS2@5d2d3cf0a966293fc9ddeac33cf86830a5de206e`), validates buffer sizes **before any write**, zero-initializes native output, and leaves unrelated trailing data untouched.
- CI `tools/check-ns2-native-gpu-ioctl-host.py` executes O0/O2+UBSan fixtures for 208/216-byte formats, profile 0x807/0x808, 4-KiB pages, subcontext capacity, unsupported raw IDs and truncated in/out buffers. The actual research `nvhost_ctrl_gpu.cpp` is additionally syntax-compiled.
- `EDEN_NS2_NVDRV_EXPERIMENTAL=ON` is opt-in, requires metadata mode, and is forbidden in the final PS5 release profile. The original `vendor` remains immutable. A valid characteristics reply is **not evidence that a native NVIDIA GPU task can execute on PS5 RADV**.

## N3d — Native sparse GPU address mapping (host-only)

- Ported upstream `native_sparse_remap.h` and complete `gpu_memory_registration.h` from `0x2593/Eden-NS2@5d2d3cf0a966293fc9ddeac33cf86830a5de206e` to `headless/ns2/hle`, replacing the earlier reduced registration decoder. Header compilation now exercises real 4/64/128-KiB-page decoding and 4-KiB GPU page alignment assumptions.
- Added host tests for invalid flags, zero pages, overflow, nonzero source with null handle, sparse region bounds and page shifts. `NativeSparseMappingTable` regression validates split/replacement of overlapping ranges, corrected physical source offsets and release of superseded handle references.
- This does NOT yet map any PS5/GPU direct memory or hook NVIDIA memory allocation to RADV; live GPU virtual-address management, synchronization and OOM guards are separate requirements.
- The NVDRV owner syntax-check uses GCC instead of Clang 18: Clang 18 crashed **inside the old `WrapFixedInlOut` template** in GitHub run `#41033393201`, without a source-level error. GCC must compile the actual research file before this lot is qualified.

## N3e — Native GPU channel identities / syncpoint cache

- Added `native_gpu_context.h` and `graphics_syncpoint_cache.h` from pinned `0x2593/Eden-NS2@5d2d3cf0a966293fc9ddeac33cf86830a5de206e`. The host harness validates TSG packet size and reserved bytes, 0–63 native subcontexts, known GPU engine class identities, the 192-slot syncpoint layout and 32→64-bit counter rollover.
- Hardened `NativeSparseMappingTable::Replace` against zero-length, guest VA and source offset overflow, with regression checks preserving existing handle pins on invalid input.
- These are synthetic ABI tests only. Live GPU session, PS5 GPU execution, register mapping and syncpoint notification are not yet wired to NVDRV/RADV.

## CI throughput — separate expensive Dynarmic runtime build

- Host research CI (`.github/workflows/ns2-research-host.yml`) keeps C++ parser, A64 syntax, AM, NVDRV, HLE, GPU ISA probes and source-owner checks on each relevant change. Documentation-only edits no longer trigger a full build.
- Full x86-64 Dynarmic JIT execution moved **unchanged** into `.github/workflows/ns2-research-jit.yml` with path filters for A64/CPU6, the JIT-host fixture, vendor pin and the workflow itself. This avoids repeating the heavy Dynarmic compile after unrelated GPU service or doc changes.
- Both workflows support manual dispatch. A green host CI does **not** replace the latest green JIT runtime test when A64 code changes.

## N4a — Real AM application proxy command 60 (graphics scaling query)

- Selectable source owner `IApplicationProxy` is based on pinned Eden code at `92c5829174a1169c507b72438021d3dfa9e5dfa2`. Command `60` instantiates `IGraphicsScalingParametersFunctions` with the isolated new service source. `GetGraphicsScalingParameters` returns the **experimental default** (scale 10, screen ratio 1/1) from `0x2593/Eden-NS2@5d2d3cf0a966293fc9ddeac33cf86830a5de206e`. This is a provisional interpretation, not a verified Switch 2 OS contract.
- The upstream notification setter expects an applet state member unavailable in pinned Encore. For correctness, command `1050` stays **unimplemented**, not fake-success. Debug service commands are likewise unimplemented.
- `EDEN_NS2_GRAPHICS_SCALE_EXPERIMENTAL` requires opt-in AM mode, replaces only the original `IApplicationProxy` source, and is rejected by the final release gate. CI syntax-compiles both actual owner source files; the existing owner and source-guard fixtures detect any missing CMake selection.
- This is guest IPC service registration only. No NVIDIA session/channel, PS5 frame scaling, GPU supervisor, or game launch is claimed.

## N4b — GPU Session command ownership and 256-device lifecycle

- Extracted the bounded GPU-session command contract from `0x2593/Eden-NS2@5d2d3cf0` into `headless/ns2/hle/.../gpu_session_protocol.h`. It decodes command 41 (device create), 42 (destroy), 11/12 and 21/22 (notifications/worker), 202/203 (address-space partition) without exposing any guest GPU driver interfaces yet.
- **Hardening beyond the upstream prototype:** device ID 0 remains reserved, exactly 255 live devices are allowed, unsupported creation flags do not mutate allocation state and destruction validates the complete 32-bit ID before indexing (the upstream's `static_cast<u8>(packet[2])` can alias indices). Worker requests require an allocated event slot; no fake event/signal is generated.
- Synthetic host regression via `tools/check-ns2-graphics-hle-host.py` exercises 255 live devices, capacity exhaustion, reuse of id 255, double destruction, malformed packet lengths, out-of-range ID 256/257, 64 notification slots and TIPC partition headers under O0/O2 + UBSan.
- This is an **integration prerequisite**. The real `IGpuSession` and the much larger `IGraphicsSupervisor` still require kernel event/session ownership, NVDRV fd lifecycle, GPU virtual address manager and a verified PS5-RADV render path. No runtime IPC service registration or release path is claimed.

## N4c — GraphicsSupervisor ordered bootstrap contract

- Added `graphics_supervisor_bootstrap.h`, a **strict standalone state transition layer** derived from the actual upstream `IGraphicsSupervisor` command implementations `4/11/101/401/402/497`. A correctly decoded process handle and ARUID, local bootstrap flags, and ordered process binding are required before GPU session opening.
- Test fixtures use the **real** `GraphicsSupervisorProtocol::DecodeBootstrap` decoder and validate initial/ready transitions, bad handles and applet identity, duplicate bootstrap, unsupported remote bootstrap, GPU context init/activation, flag 4 requirements, and sm87/sm88 negotiation. Every failed transition must preserve the previous state.
- **Explicit limit:** this validates protocol/state correctness but does **not** register or instantiate `IGraphicsSupervisor`, hand out a kernel session, allocate NVDRV resources, or run a Switch 2 game. The upstream implementation is 133 KB and depends on native image registry/video/VI2/kernel lifetime work that has not been safely ported to Encore.

## N4d — Compiled native GPU Session TIPC service (unreachable until supervisor bridge)

- A real **C++20 HLE service implementation** now exists under `headless/ns2/gpu_session/core/hle/service/am/service`: `IGpuSession` registers the implemented TIPC commands 41/42 and uses the previously tested `GpuSessionProtocol::DeviceSlots` with service-level locking and kernel Result conversions. Unknown/unsupported commands always return explicit `ResultNotImplemented` rather than a fabricated GPU event, worker or memory mapping.
- Gated by `EDEN_NS2_GPU_SESSION_EXPERIMENTAL` (requires `EDEN_NS2_NVDRV_EXPERIMENTAL`, OFF by default and forbidden for `EDEN_FINAL_RELEASE_PROFILE`). CMake uses `target_sources(core PRIVATE ...)` to avoid overriding the stable Encore core source owner list; the GPU HLE source is syntax-compiled in host CI.
- **Not yet usable from guest:** no `IGraphicsSupervisor::OpenGpuSession` bridge/handle is installed; there is no NVDRV VA map, worker, queue submission or PS5 Vulkan/RADV execution. Device registry success only represents a local metadata ID, not a working GPU device.

## N4e — Guest-facing supervisor IPC to metadata-only GPU Session

- Experimental CMIF `ISelfController` command **2000** now constructs an actual kernel-owned `IGraphicsSupervisor` session and returns a copied handle. This uses the pinned Encore SelfController source, preserving existing commands.
- A small actual TIPC `IGraphicsSupervisor` implementation registers **4/11/101/401/402/497**, checks the calling process, ARUID, and ordered bootstrap with the existing tested state machine. **497** returns a real moved kernel session to the existing `IGpuSession`.
- The GPU session only implements **41/42 metadata device IDs**. Native VA/worker/event, NVDRV channel, VI2, submission and PS5 RADV rendering remain unimplemented and return explicit errors, never fabricated success.
- The compiler selector `EDEN_NS2_GRAPHICS_SUPERVISOR_EXPERIMENTAL` requires both AM and GPU-session research modes, defaults OFF and is forbidden in release. CI syntax-compiles the actual new service owners and guards their versioned source selection. No Switch 2 PS5 gameplay claim.

## N4f — Live NVDRV address-space FD lifecycle (experimental only)

- `IGraphicsSupervisor::OpenGpuSession` now acquires the **actual** existing Encore `nvdrv:s` module. If unavailable, command **497** fails; it no longer creates a GPU session backed only by metadata when NVDRV itself is absent.
- The GPU session holds a process reference and opens a real NVDRV process session. TIPC **33** opens `/dev/nvhost-as-gpu`, executes the real allocation IOCTL **0x40284109**, and publishes an FD only on successful initialization. It tracks **up to eight** owned FDs; failed opens and IOCTLs cannot consume slots.
- TIPC **202/203** resolve **owned FDs only**. User partition 203 calls the existing NVDRV VA-region IOCTL **0xc0404108**, checks zero sizes and 64-bit multiplication/addition overflow, and returns real region bounds. Supervisor **434** registers only FDs owned by live GPU sessions and only after GPU-context activation; destroying a GPU session closes all its fds and its NVDRV session.
- O0/O2+UBSan host fixtures cover slot exhaustion, duplicated/invalid/truncated FD registration, capacity, cleanup enumeration and VA overflow. Source-selection checks enforce the original code paths and the switch remains OFF/forbidden for release.
- **Important limit:** this is the existing Encore NVDRV address-space allocator, **not** native Switch 2 Ampere 4-KiB mapping or PS5 Vulkan submission. No GPU memory worker, notification signaling, rasterization, VI2 or Switch 2 gameplay is unlocked by this commit.

## N4g — Real kernel notification-event lifetime (worker still blocked)

- `IGpuSession` implements TIPC **11** (range 0–63) and **12** (per-index `KEvent`/readable handle) with the existing strict packet decoder. Events are lazily allocated, shared on repeated requests for the same index, moved with a real kernel reference, and cleaned up by `ServiceContext` when the session is destroyed.
- A failed kernel allocation reports `ResultOutOfResource`; invalid indices/header report `ResultInvalidCombination`. It does **not** invent a GPU completion signal. **21/22 worker request/acquire** remain unimplemented pending actual NVDRV native mapping and queue submission.
- The source owner guard ensures real event Create/Close and absence of fake worker handlers. CI syntax-compiles the full research service. This is not native PS5 GPU rendering or Switch 2 game support.

## N4h — GPU worker 4-KiB mapping preflight and ownership ledger (host-only)

- Added `gpu_worker_protocol.h` with strict TIPC **211/212/213** decoding: bounded words, inclusive-end overflow checks, 4-KiB alignment, max 32-bit page count, event IDs, byte parameter padding, and native kind fallback. Unsupported permissions/cache/mode/sync/kinds are rejected.
- Added a bounded **4,096-entry mapping ledger** enforcing per-AS non-overlap, exact unmap, contained modification and backend-commit-only semantics. This ledger **does not** map GPU memory; a future native backend must call it after successful page-table operations.
- C++20 O0/O2+UBSan host fixtures cover malformed/truncated messages, VA/offset overflow, duplicate/adjacent/intersecting allocations, and exhaustion. Source guards forbid registering worker commands without a real NVDRV mapping backend.
- All NS2 options remain OFF for shipping builds; no changes to `main` or F07, and **no Switch 2 GPU rendering or game compatibility is claimed**.

## N4i — Real bounded IGpuWorker IPC transport (no native mapping yet)

- Experimental GPU session commands **21 RequestWorker** and **22 AcquireWorker** now create one real kernel `KSession` with a `SessionRequestManager`. Requests require an existing notification event (0–63); successful registration signals it, and acquisition returns an independently opened move handle.
- The retained worker client reference is closed on GPU-session destruction, while guest-owned handles have independent kernel references. Malformed commands, absent notification events or worker, and kernel session exhaustion return explicit errors.
- The separate `IGpuWorker` implementation owns process/module references and returns `ResultNotImplemented` for **101/102** and **211–216**. This is *IPC transport only*: native 4-KiB mapping, command execution and Switch 2 rendering are not yet available.
- Both C++ source owners are compiled by the NS2 host CI and protected by source-selection guards. The PS5 release profile continues to forbid experimental NS2.

## N4j — Real GPU-accessible memory registration and release, 101/102

- Experimentally implements worker TIPC **101** by verifying the existing GPU device ownership and GPU-accessible kernel page attributes, then allocating an NVMap handle, taking a real `LockForMapDeviceAddressSpace` process-page reference, and binding the handle to an NVDRV process session. Failed checks, failed lock and failed allocation return errors with rollback; successful handles are owned by the worker.
- Worker TIPC **102** validates the notification slot and its kernel event, requires an owned handle with **exactly one guest ref, no internal duplicates and no pins**, frees the NVMap allocation, unlocks the associated process pages and signals the event only after release. Pinned/duplicated resources return `ResultBusy` rather than claiming release. Worker destruction frees remaining owned NVMap handles and attempts page unlocks, retaining process/module sessions until cleanup.
- A shared refcounted state now owns the GPU device IDs and kernel notification events so separately acquired worker handles cannot observe freed objects after their creator GPU session closes. Memory ownership is capped to **4096 handles** per worker. Malformed release, overflow, unaligned inclusive range and invalid notification are covered in C++20 host protocol fixtures; real service owners are host syntax-checked by CI.
- **Still unsupported:** worker GPU VA mapping 211-216, mapping completion/pin retirement polling, native NVDRV Ampere GMMU operations, Vulkan/RADV rendering and actual PS5 guest gameplay. NS2 research remains opt-in, forbidden in the release profile, without changes to `main` or F07.

### N4j compatibility: maintained Encore memory flags

The maintained Encore kernel has no upstream-only GpuAccessible memory attribute. The worker uses the real FlagCanAlignedDeviceMap and FlagReferenceCounted state bits, rejects IPC-locked and explicitly locked regions, then relies on the kernel's own LockForMapDeviceAddressSpace validation under its page-table mutex. These checks are not a native NS2-specific memory attribute; supporting such a guest-only flag remains separate work.

## N4k — Correct NVDRV GPU address-space FD lifetime for independently moved workers

The GPU worker (kernel session handle 22) may remain alive after the GPU session closes.
Previously the GPU session closed its owned NVDRV address-space FDs even while the
worker's separately moved handle was still valid. Device IDs, event handles, address-space
FDs and the owning NVDRV module/session now live together in a refcounted shared owner.
The last worker/session owner closes all owned FDs before the NVDRV process session.
All operations take the same state mutex; no native GPU mappings are attempted yet.

This fix is preparatory safety work. The maintained vendor's nvhost_as_gpu does not have
the Ampere-native MapNative4K/UnmapNative4K/ModifyNativeKind operations, and generic
Maxwell-era fixed-map IOCTLs must not be represented as full Switch 2 GPU support.

## N4l — Native 4-KiB NVDRV owner and GPU worker mappings (research only)

- Isolated overlay for the *pinned* `nvhost_as_gpu.{h,cpp}` owner in the already-disabled `EDEN_NS2_NVDRV_EXPERIMENTAL` CMake branch. The Switch 1 / shipping NVDRV source remains unchanged in `vendor/`.
- Added directly backed `MapNative4K`, `UnmapNative4K` and `ModifyNativeKind` operations to the experimental GMMU owner. Map validates owner process, live NVMap handle, page alignment, offset/size overflow, exact 4-KiB regions, address-space bounds, and overlap against both reserved VA and raw mappings. Reservation, pin, GMMU update, and mapping-table ownership are serialized by the existing AS mutex. Native unmap requires the matching live allocation and size, then unmaps/unpins/frees.
- Worker TIPC **211 map**, **212 modify kind**, and **213 unmap** now use the actual address-space FD, only a memory handle owned by this worker, the shared device/notification slots, and the bounded mapping ledger; only successful GMMU operations update the ledger and signal completion. Worker destruction unmaps before releasing NVMap backing handles.
- **Important limit:** this establishes an experimental 4-KiB address mapping path in Encore's inherited GMMU model, **not** a complete Ampere/T239 GPU implementation. Native shader interpretation, sparse 214–216, syncpoints/queues, and graphics output require separate verified work. This is not proof that a Switch 2 title boots or renders on PS5.

## N4m — Sparse 4-KiB VA reservation and exact release (research only)

- Implemented TIPC **214 CreateSparseRegion** for 4-KiB pages, and **215 DestroySparseRegion** for exact matching ranges. Both require the live GPU address-space FD, device ownership, allocated notification event, bounded packet/mode and valid inclusive VA range; only successful driver operations signal completion.
- The experimental `nvhost_as_gpu` overlay now owns true sparse GMMU reservations using `MapSparse`. Reservation and teardown are serialized against existing normal 4-KiB mappings and other allocations; sparse teardown explicitly unmaps the region and releases the underlying allocator pages without freeing mapped NVMap backing.
- A single **4,096-entry** worker allocation ledger tracks normal mappings and sparse reservations in the same VA namespace. It rejects overlaps, disallows normal 212/213 updates on sparse regions, and requires an exact sparse type, address-space, base and size for 215. Worker destruction performs type-specific cleanup before releasing memory.
- C++ host protocol tests cover TIPC 215 validation, truncation, duplicates, normal/sparse overlap, contained modification denial, cross-address-space isolation, exact release, page alignment and overflow. No change to `main`, F07 or the shipping NVDRV owner.
- **Still unsupported:** command **216 ExecuteSparseMapRequests** (requires transactional physical remapping, retained pins, and rollback), GPU queue/submission and Ampere rendering. 214/215 alone do not make NS2 games playable.

## N4n — Switch 2 native sparse 216 + Oct 30 upstream audit (research)

### Transactional native sparse remapping (experimental, not game-verified)
- Worker TIPC **216 ExecuteSparseMapRequests** decodes the 15-word envelope and at most 256 payload entries, checking 40-byte element width, exact input byte length, output capacity, address-space FD and notification ownership **before** reading or mutating the GPU.
- Each decoded entry must fit one existing 4-KiB sparse reservation owned by the same worker; any source NVMap handle must have been created by that worker. Memory bounds and Turing kinds/fallbacks are validated before the whole batch is submitted to NVDRV.
- The experimental NVDRV AS backend stages a copy of the active sparse interval table, verifies all guest NVMap handles and source ranges, and pins every handle needed by the *intermediate ordered GMMU operations*, even when superseded later in the same batch. Only after successful preflight and pin acquisition are GMMU updates applied. Pins no longer referenced by the final mapping are released after commit; 215 prunes the table and releases retired pins. A failed preflight cannot partially change GMMU state.
- GMMU's Map/MapSparse operations currently return void, so this provides **transactional validation + pin ownership**, not a hardware/GPU-execution rollback guarantee. No native Switch 2 rendering, syncpoint/queue, or PS5 runtime proof is claimed.
- C++ protocol tests now exercise count 0/257, 64-bit high words, packet truncation, stride mismatch, GPU AS owner, sparse containment and release invalidation; host CI syntax-checks the actual C++ worker and NVDRV backend.

### Newly verified external source candidates — Oct 30 2026
1. **Takoroka/eden-nx2**, tag `nx2-2026-10-29`, commit `b7ff03036c0eca49ed99d40973a6b94a410b88ae`: public Forgejo experimental Switch 2 source branch `eden-nx2`, Windows x64 build using official CI settings; release author confirms missing meshes due to unimplemented shaders, recommends ExeFS main launch and explicitly says Linux was not validated. **High-value independent compatibility reference, but release page alone is NOT a source diff**. Source: https://git.eden-emu.dev/Takoroka/eden-nx2/releases/tag/nx2-2026-10-29
2. **0x2593/Eden-NS2**, commit `e2f285ab1ecd3a2475c2ccad66f23b06b94ead5c` dated Oct 30: "Faster GPU processing" with `GpuSplit` front/back threading, ordered channel binding, buffer-cache mapped-prefix generation, ASTC wait elimination for native tiled textures, 3 rotating capture resource sets and ASTC mip trimming. ~1,234 changed lines: **do not blindly cherry-pick** into PS5; compare frame pacing and native GMMU mapping invalidation before selectively porting. Source: https://github.com/0x2593/Eden-NS2/commit/e2f285ab1ecd3a2475c2ccad66f23b06b94ead5c
3. **Djihads80/Eglantine**, `nx2` branch head `6e7edd7462325ee18a0db6fdc29ff7698ac108cc`: native QMD scheduler evicts completed, unreferenced cache states on reaching the 4,096-entry cap, avoiding stalling; a small candidate once native QMD queues are implemented. Source: https://github.com/Djihads80/Eglantine/commit/6e7edd7462325ee18a0db6fdc29ff7698ac108cc
4. **ShadyHero/Eden-NS2**, pre-release v0.0.1 (Oct 29) says Linux-only and explicitly untested on Switch 2 hardware, compiled with NS2.patch. Treat as packaging evidence, not independent GPU compatibility proof. Source: https://github.com/ShadyHero/Eden-NS2/releases
5. **crewmate-nx/eden-nx2**, default master head `26a03d2473787abf3223b2d0e65b291eee00c1e1` (Oct 26 Eden upstream revert), with no newer NX2 native patch established from the head. Low-priority until code differences can be demonstrated. Source: https://github.com/crewmate-nx/eden-nx2

### Next verified PS5 gates
- PS5 native full link/package + kernel resources and actual NS2 ExeFS load; GPU queue/submission, syncpoints, shader ISA Turing/Ampere, textures on RADV.
- Measure on PS5 before importing upstream GPU split: worker throughput, 1% lows, shader/sync waits, Vulkan queue idle and buffer-cache invalidation generation.

## N4o — Process-scoped native GPU GPFIFO handoff (research only)

- Unlike upstream `0x2593/Eden-NS2`, the pinned Encore kernel does **not** expose `KProcess::UsesPAuthReturns()`. A small bounded, refcounted `NativeGpuProcessRegistry` now marks only a guest process that actually opened a **research-only** `IGpuSession` through the NS2 graphics bootstrap. The final shared GPU session/worker owner removes this marker; an ordinary Switch 1 NVDRV session never activates it.
- Research-only source overlay for `nvhost_gpu.{h,cpp}` replaces the old channel owner **only** under `EDEN_NS2_NVDRV_EXPERIMENTAL` and the final PS5 release gate still refuses the research flags. The pinned `vendor/` and `main` stay unchanged.
- Existing NVDRV `SubmitGPFIFO` 0x08/0x1b paths and ordinary host GPU scheduling remain real. Native channel preflight now refuses uninitialized GMMU/channel submission and unknown/contradictory fence flags; supports up to 64 C56F-style completion increments emitted *after* the actual ordered GPU pushbuffer, and retains legacy two-increment fences on the non-native path. Registered native context classes C797 (3D), C7C0 (compute), C7B5 (DMA), C56F (GPFIFO) are mapped into their existing channel slots. QueryEvent(7) uses the already-owned error notifier only in native mode.
- Added C++ host tests for per-process opt-in and final-owner revocation, unknown fence flags, incomplete GPU channel, fence acquire/completion conflicts, native increment bound, and standard fence compatibility. Host CI syntax-checks actual NVDRV channel owner, not merely the pure protocol.
- **Important:** this step connects correct process identification, GPFIFO ordering and bounded syncpoint semantics; it does **not** implement Turing/Ampere 3D and compute engine methods, shader translation, PS5 RADV output, or real hardware runtime verification. NS2 GPU correctness and playability remain unproven.

## N4p — Switch 2 content formats and Mario Kart World loadability audit

**MKW is Mario Kart World, not an archive suffix.** The 5-vs-30 FPS question
from X is an unverified performance comparison; it must not drive acceptance
of a new file extension or false claims of emulator readiness.

Source audit: existing Encore experimental loader covers first-generation
XCI/XCZ, NSP/NSZ, NCA/NAX, NSO/NRO/KIP, and standalone ExeFS `main`
with NPDM; it does **not** establish retail Switch 2 archive decryption,
package installation, card-key licensing or stable MKW gameplay.
The pure `ns2_content_formats.h` now documents and tests existing filename
routes without registering invented `.xci2`, `.nsp2` or `.mkw` handlers.
The actual NS2 loader overlay uses it. See:
**[NS2 content format matrix](NS2_CONTENT_FORMAT_MATRIX_2026-10-30.md)**.

## N4r — Ampere SM70+ 128-bit shader ISA probe (research only)

- Independently pinned the **629-row** SM70+ opcode/mask table from
  `0x2593/Eden-NS2` commit `e2f285ab1ecd3a2475c2ccad66f23b06b94ead5c`,
  plus its instruction bit layout and opcode/control-flow classification
  (`src/shader_recompiler/frontend/ampere/` upstream). The table itself
  credits Mesa NAK SM70 field layouts, MIT licensed.
- The new `shader_recompiler/frontend/ampere/probe.{h,cpp}` reads a bounded
  stream of native **16-byte** instructions, validates exact alignment and
  65,536-instruction maximum, looks up the actual opcode, classifies
  branch/exit/control flow and records unknown opcodes or instruction bits
  outside the reviewed ISA masks. No arbitrary guest input can be claimed
  as a successfully decoded shader merely because a program blob exists.
- CMake option `EDEN_NS2_AMPERE_PROBE_EXPERIMENTAL` **OFF by default**
  adds the real source to `shader_recompiler` under an isolated overlay;
  the final PS5 release profile explicitly refuses it. Clang and GCC host
  fixtures exercise MOV/BRA/EXIT, unknown opcodes, unreviewed fields,
  truncated instructions and size-cap rejection.
- This is a **foundational ISA decoder**, not the upstream 255-KiB
  lowering-to-Maxwell translator or full task/mesh shader execution.
  Correct Ampere shader generation, pipeline state, render passes and
  validation on PS5 are still needed. No Mario Kart World FPS claim.

## N4s — First real Ampere -> Maxwell translation handoff (research only)

- Imports `lower_to_maxwell.h` and `register_pressure.h` directly from
  pinned `0x2593/Eden-NS2` commit
  `e2f285ab1ecd3a2475c2ccad66f23b06b94ead5c`, GPL-3.0-or-later
  (ISA encoding reference credits Mesa NAK MIT). No bulk video-core, texture,
  CMake or shader backend port; no change to `vendor/`.
- The new `lower_bridge.{h,cpp}` turns native guest **128-bit
  instructions** into **real Maxwell words** plus a native-to-output
  source-offset map through the upstream lowering routine. It requires an
  opcode recognized in the pinned 629-entry ISA table and rejects unknown
  bit fields, incorrect alignment, unsupported instructions, failed branch
  relocation, missing unconditional exit, bad source map and oversized output.
  This pathway is capped to **4096** native instructions, smaller than the
  65,536-instruction bare-probe capacity, until allocations/real guest runtime
  are validated. Error statuses are explicit and no partial output escapes
  on a failure.
- The existing `EDEN_NS2_AMPERE_PROBE_EXPERIMENTAL` option (default OFF,
  denied by PS5 final release gate) compiles the actual lowering bridge into
  `shader_recompiler` alongside the earlier opcode probe.
- Actual Clang and GCC host tests use **the real lowering implementation**,
  checking simple native NOP/EXIT and MOV/EXIT streams, generated Maxwell
  instructions and source mapping, unknown opcodes/fields, incomplete
  programs, invalid lengths and bounded input. Static source-owner guards
  enforce the dependency and CMake gates.
- **Not a shader pipeline yet:** Maxwell environment scheduling/header
  insertion, GPU-memory program capture, IR translation, cache identity,
  native task/mesh shader semantics, Vulkan RADV and PS5 game runtime
  remain separate gates. This implementation is a tested frontend
  conversion step, not proof of Mario Kart World rendering or playable FPS.

## N4t — Maxwell shader-environment image ABI (research-only, not shipping)

- Imported the pinned `program_address_map.h` from
  `0x2593/Eden-NS2` commit `e2f285ab1ecd3a2475c2ccad66f23b06b94ead5c`.
  The existing bounded `LowerReviewedToMaxwell` translator now feeds
  `BuildMaxwellShaderImage`: an exact **0x50-byte** preserved guest shader
  header, Maxwell instruction stream padded with **8-byte scheduling words
  every 32 bytes**, one unreachable padding word, and the source-to-Maxwell
  address table using the upstream `NativeAddressMapMagic`.
- Explicit `ReadMaxwellInstruction` and `TranslateNativeAddress` APIs
  refuse scheduling slots, unaligned addresses, missing destinations,
  out-of-range accesses and appended metadata. Successful images preserve
  consumed source size and the cached-image byte range.
- An **NS2-only versioned diagnostic key** incorporates stage, native source
  and shader-header bytes; it is intentionally not injected into the existing
  Switch 1 GPU disk cache until the actual graphics/compute environment
  selection can be validated. Invalid inputs produce no output or cache key.
- This source is compiled into `shader_recompiler` under the same opt-in
  `EDEN_NS2_AMPERE_PROBE_EXPERIMENTAL` flag; final release gate still refuses
  the experimental flag. Added actual Clang/GCC compiler tests with
  NOP/MOV/EXIT, first three native address relocations, scheduler slot
  exclusion, deterministic key isolation and fail-closed inputs. No
  change to shipped GPU runtime, vendor sources or `main`.
- **Next**: thread a process-scoped NS2 mode and correct native QMD/shader
  capture from guest GPU memory into the existing `GenericEnvironment`
  and `ShaderCache`. This image is ready for such an integration but
  is **not yet an executing shader or evidence of gameplay**.

## N4u — Real GMMU-backed Ampere shader capture bridge (research-only)

- Imported pinned upstream `program_capture.h` from `0x2593/Eden-NS2`
  commit `e2f285ab1ecd3a2475c2ccad66f23b06b94ead5c`.
  Bounded `CaptureNativeGraphicsShader` reads a verified **0x80-byte
  native graphics shader header**, preserves the first **0x50 bytes** as
  Maxwell header, and captures exactly **16-byte Ampere instructions**
  until the upstream forward-branch-aware termination detector reports
  an unconditional EXIT/complete return.
- Up to **4096** instructions are accepted. Invalid branch targets, missing
  full guest memory mappings, incomplete programs, address overflow,
  unsupported native instructions and translation mismatches fail closed:
  no partial Maxwell shader image is returned.
- Actual `Tegra::MemoryManager` adapter
  `video_core/native_shader_capture.cpp` checks
  `IsFullyMappedRange(address, size)` before each
  `ReadBlock(address, dest, size)`. This is **real GPU address-space
  integration at the source/API level**, not a simulated stand-in.
- Research opt-in CMake wires `capture.cpp` into
  `shader_recompiler` and the native GPU memory reader into
  `video_core`. Both stay OFF by default and blocked in the final PS5
  release configuration. CI compiles and executes real lowering/capture
  fixtures with Clang/GCC, and syntax-checks the actual GMMU adapter.
- Host tests include NOP/EXIT capture, deterministic translation identity,
  unmapped header/second instruction, invalid branch target, unsupported
  opcode, no-EXIT 4096-instruction limit, null reader and GPU VA overflow.
- **Limits:** The capture entrypoint has not yet been invoked by the
  existing `GenericEnvironment`/ShaderCache or PS5 rendering loop.
  Compute QMD/zero-header shaders, indirect-branch target tables,
  task/mesh shaders and runtime Vulkan pipelines are not yet implemented
  by this bridge. No Switch 2 retail game or PS5 render proof is claimed.

- Safety follow-up: reject native `BRX` (opcode `0x949`) while
  constant-buffer indirect branch target tables are not available to the
  adapter; a linear capture must never masquerade as complete when branches
  may jump beyond its last EXIT. Host regression includes this case.

## N4v — Bounded source-verified native shader translation cache (research)

- `NativeTranslationCache` is an **explicitly owned** opt-in bounded
  64-entry / 16-MiB LRU of successful Ampere-to-Maxwell images. The owner
  must be scoped to its NS2 graphics session and call `Clear()` on shader
  invalidation or destruction; **no global cache and no Switch 1 cache keys
  are modified**.
- Cache lookup matches the **complete captured native shader bytes,
  complete 0x50-byte header, and shader stage**, not the diagnostic 64-bit
  hash or GPU address. A hash collision or a rewrite at the same GMMU VA
  cannot silently reuse a different program.
- The actual native GMMU capture adapter accepts an optional cache pointer.
  It always **reads and validates all current guest shader bytes first**.
  It never serves a hit after an unmapped read, invalid indirect branch
  or incomplete capture. Failed translations and zero-capacity entries
  are not retained.
- Separate host Clang/GCC regressions cover repeated hits, in-place guest
  instruction mutation at the same address, header/stage isolation, LRU
  eviction and retranslation, unmapped pages, incomplete programs, failed
  translations, zero retention and explicit invalidation.
- This is a source-verified translation cache, **not** an active GPU
  disk cache or completed engine integration. The existing shader
  compilation/render loop has not yet been patched to pass an owned
  cache instance. A PS5 full link and runtime game verification remain
  outstanding.
