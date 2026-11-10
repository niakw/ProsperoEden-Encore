# NS2 optimization research — local host receipt (2026-11-10)

**Scope:** isolated audit PR #44; no PS5 build, no vendor main changes, no guest ROMs, no Vulkan device. This file records reproducible local results rather than claiming GitHub Actions ran.

## Environment

- Clang 17.0.0; GCC/G++ 14.2.0; C++20.
- Compile flags: `-std=c++20 -pthread -O1 -Wall -Wextra -Werror -fsanitize=undefined -fno-sanitize-recover=all`.
- Command: `bash research/ns2/run_host_checks.sh` from an offline working copy of this research directory. The copy had no pinned vendor checkout.

## Actual stdout

```text
PASS: 19 NS2 SSBO extent research contracts
PASS: 23 NS2 backing lifetime research contracts
PASS: 30 leased GMMU memo research contracts; first 32MiB scan=8193, six scans under unchanged lease=8193 probes
PASS: 33 native Vulkan range contracts
PASS: 19 NS2 SSBO extent research contracts
PASS: 23 NS2 backing lifetime research contracts
PASS: 30 leased GMMU memo research contracts; first 32MiB scan=8193, six scans under unchanged lease=8193 probes
PASS: 30 native Vulkan range contracts
SKIP: exact-source NS2 QMD3 guard (pinned vendor checkout unavailable)
```

**105 distinct assertions per compiler, 210 total across both compilers.** No failed assertion or sanitizer report. This validates **research models**, not actual runtime owners or console behavior.

Additionally compiled and executed an offline standalone `native_guard_real.cpp` excerpt of the native mapping guard and its `known_size` predicate: **PASS: 24 exact native guard and descriptor conditions** on each compiler. The function body was compared with the GitHub connector-fetched pinned vendor's `NativeQmdContiguousGpuSpan`: the normalized 460-byte function body had the same FNV-1a 32-bit fingerprint **1556815272** and local SHA-256 **90c871905ad8c6d5a193acea84a457816cf1bc432d71c06de6f6ab68e0f9b7a2**. The actual repository source-extraction Python script was **not executed end-to-end** in this environment.

## Safety blocker

The 16-entry positive GMMU span memo requires a real shared mapping read lease that **spans the check and subsequent use**, including writer exclusion and unique owner lifetimes. The current production `MemoryManager::GpuToCpuAddress` does not provide that lease through the Vulkan native QMD3 owner. Hence its synthetic 83.3% drop in 32 MiB repeated translation callbacks is **not a PS5 performance gain** and may never be applied by removing existing remap checks. Proof of safe lock ownership plus actual PS5 profile is a prerequisite.

## Source references

- Vendor pinned: `niakw/Prospero.Eden-Encore-vendor@22b69d6053db41b74edac2633c012f925b84f69e`.
- `encore-active/ns2-runtime/ampere/shader_recompiler/frontend/ampere/native_qmd_compute_environment.h` — exact GMMU guard and QMD3 size admission.
- `encore-active/eden-vulkan/vk_compute_pipeline_cost.cpp` and `vulkan_rasterizer.cpp` — native owner and six full-span calls.
- `encore-active/eden-core/src/video_core/memory_manager.cpp` — revision-keyed existing range cache, but no cross-dispatch mapping read lease.

## O11 range admission local evidence (new suite)

The 33 assertions in `test_native_vk_range_contract.cpp`, using
`native_vk_range_contract.hpp`, passed under both Clang 17 and GCC 14 with
UBSan. These test 49-bit guest boundaries, native 256 MiB ceiling, real
driver range limit inputs (including zero / exact maximum / maximum + 1),
uniform-CBUF 64 KiB limit, Vulkan descriptor offsets, backing-size bounds,
and overflow-safe descriptor-buffer device-address calculation.

Compiled local files match the exact UTF-8 content pushed to PR #44:
`native_vk_range_contract.hpp` FNV-1a `1869386525` (3273 bytes) and
`test_native_vk_range_contract.cpp` FNV-1a `3696510677` (5265 bytes).

This remains host-only **candidate validation**, not an authentic Vulkan
driver limit query and not proof the production `ConfigureNative` contains
such a check. No GH Actions job was triggered by this research-only change.

### Main-build driver provenance cross-check

`tools/build-package.sh` selects `EDEN_VULKAN_DRIVER=RADV` in the current
main source. Vendor `encore-active/ps5-mesa/src/amd/vulkan/radv_physical_device.c`
advertises both descriptor range limits as `UINT32_MAX`.
The *non-selected* PS5VK driver advertises 128 MiB SSBO / 16 KiB UBO.
The 33-case fixture includes three tests for these distinct source-advertised
profiles. These constants have **not** been verified through a real PS5
`vkGetPhysicalDeviceProperties` call.

## Additional optimizer matrix (host only)

Recompiled and executed every one of the four research suites with
Clang 17 and GCC 14, using both `-O0` and `-O2` while keeping
`-Wall -Wextra -Werror -fsanitize=undefined -fno-sanitize-recover=all`.
All **16 binary executions passed** (2 compilers × 2 optimization levels
× 4 suites), corresponding to **420 individual assertions** across these
additional runs: (19 + 23 + 30 + 33) × 2 × 2.
No sanitizer errors were observed. These are local host model results
only, not GitHub Actions and not PS5 hardware.
