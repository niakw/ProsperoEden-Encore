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
