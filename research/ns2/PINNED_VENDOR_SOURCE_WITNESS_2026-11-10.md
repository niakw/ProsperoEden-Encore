# Pinned vendor source witness — NS2, 2026-11-10

**Scope:** direct GitHub connector reads at immutable vendor commit
`niakw/Prospero.Eden-Encore-vendor@22b69d6053db41b74edac2633c012f925b84f69e`.
This is a separate source-only verification of Python gate invariants, **NOT**
an executed Python checkout gate, actual vendor compilation, or PS5 launch.

## Independently fetched source blobs

| Key | Source at pinned commit | Git blob SHA-1 |
| --- | --- | --- |
| H | `encore-active/ns2-runtime/ampere/shader_recompiler/frontend/ampere/native_qmd_compute_environment.h` | `ff57773021b024935d5150c1c6a3708a2faa25b5` |
| P | `encore-active/eden-vulkan/vk_compute_pipeline_cost.cpp` | `53a545c32a034cfdd3421f381f354a28b306c259` |
| R | `encore-active/eden-vulkan/vulkan_rasterizer.cpp` | `921fd6d9db216d3a4a745bcdccb4a454addcf623` |
| B | `encore-active/eden-core/src/video_core/buffer_cache/buffer_cache.h` | `3d1cba92005617c96a15af481133513ff3feef1b` |
| M | `encore-active/eden-core/src/video_core/memory_manager.cpp` | `f36837c70435a919fd8d51b46983707c634039cc` |
| S | `encore-active/ns2-runtime/ampere/video_core/native_shader_capture.cpp` | `979d5273d286d543d739e3f26ad51ee83106d479` |

## Source checks: 26/26 PASS

Checks were executed on the directly fetched textual sources, using
source owner function-boundary extraction plus targeted assertions. They
cover: distinct legacy/native Configure owners, native Vulkan descriptor
staging, the exact 4-word QMD3 size and fail-closed gates, 8 MiB *legacy*
fallback isolation, 4 KiB GMMU scans including the final byte, existing
global mapping revision versus absent cross-stage read lease, native
`GpuToCpuAddress` table lookup, prechecked shader reads with `void ReadBlock`
returning success, possible unmapped zero-fill, snapshot Capture/Matches
owners, staging preflight, CBUF/SSBO mapped spans, and exact six-pass
native Compute call graph.

Observed static cost: for one aligned 32 MiB span, **8,193 map lookups per
complete traversal**, six traversals = **49,158 calls** before other
endpoint lookups. This is a source-derived count, not wall-clock PS5 timing.

## Explicitly NOT qualified

- The full `research/ns2/check_native_qmd_owners.py` requires an actual
  checked-out Git vendor repository with `HEAD` equal to the pinned SHA;
  local offline runner still returns **SKIP** for it.
- No real guest QMD3 four-word descriptor sample, live GMMU remap
  interleaving, real `VkPhysicalDeviceLimits` query, or native PS5 dispatch.
- Source checks are exact owner patterns, not general proof of thread
  safety or a functional emulator fix.

**Decision:** the source review gate is supported by authenticated
GitHub blobs; keep the source-checkout, hardware and runtime gates
independently open. No change to `main`, vendor or build workflows.
