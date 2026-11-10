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
PASS: 35 pinned QMD3 ReadStorageDescriptor owner checks
PASS: 16 exact native shader read callback checks; artificial remap can return TRUE with zeros
PASS: 19 NS2 SSBO extent research contracts
PASS: 23 NS2 backing lifetime research contracts
PASS: 30 leased GMMU memo research contracts; first 32MiB scan=8193, six scans under unchanged lease=8193 probes
PASS: 33 native Vulkan range contracts
PASS: 35 pinned QMD3 ReadStorageDescriptor owner checks
PASS: 16 exact native shader read callback checks; artificial remap can return TRUE with zeros
SKIP: exact-source NS2 QMD3 guard (pinned vendor checkout unavailable)
```

**156 distinct checks per compiler, 312 across both compilers.** No failed assertion or sanitizer report. This validates **research models**, not actual runtime owners or console behavior.

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

Recompiled and executed every one of the six host research suites with
Clang 17 and GCC 14, using both `-O0` and `-O2` while keeping
`-Wall -Wextra -Werror -fsanitize=undefined -fno-sanitize-recover=all`.
All **24 binary executions passed** (2 compilers × 2 optimization levels
× 6 suites), corresponding to **624 individual assertions** across these
additional runs: (19 + 23 + 30 + 33 + 35 + 16) × 2 × 2.
No sanitizer errors were observed. These are local host model results
only, not GitHub Actions and not PS5 hardware.

## O1 — direct maintained-descriptor-reader body, tested with faked owners

Added [`test_qmd3_descriptor_read_owner.cpp`](test_qmd3_descriptor_read_owner.cpp).
It wraps the **unmodified** vendor `ReadStorageDescriptor` method body
in tiny fake launch/CBUF/read structures and compiles the real method.
The normalized complete 747-character method matches pinned vendor code
(FNV-1a `2431638797`), with body SHA-256
`44e011a540a5d79669867c9ebc16e2a2d6534ac94d6cffc8880948326ce9ade6`.
The repository script also checks this body fingerprint when the full
pinned vendor checkout is available.

**35/35 on Clang and 35/35 on GCC, UBSan**; same results at `-O0`,
`-O1`, `-O2`. The source-body tests verify one 16-byte read callback,
CBUF bank/size/alignment/VA admission and guest read failure, **not**
atomicity against concurrent guest writes or any live PS5 process.

The complete bounded runner now passes **156 checks on each compiler**.
With separate 24-case GMMU/size-predicate excerpt, `-O1` local
tests total **360 checks across the two compilers**. The optional
full pinned-vendor script still reports **SKIP** without a checkout.

## O1 additional real-source callback status finding

`test_native_gpu_read_toctou.cpp` embeds the **unchanged**
`VideoCommon::ReadNs2GpuShader` body from pinned vendor
`encore-active/ns2-runtime/ampere/video_core/native_shader_capture.cpp`.
Normalized body: 293 chars, FNV-1a `3943302951`, SHA-256
`af4254dd7e7e00d246cef5a2d70f5790640077f6cc592c4a8c2b7871960eccf7`.
The 16 test checks pass Clang/GCC / UBSan at O0/O1/O2.

Deterministically mocked interleave: `IsFullyMappedRange` returns
true and then a synthetic unmap occurs before `ReadBlock`.
Because `ReadBlock` returns void and zero-fills unmapped bytes, the
unchanged `ReadNs2GpuShader` returns **true with all-zero data**.
Simulated partially copied bytes also return true. The production
`ReadBlockImpl` has zero-fill-on-unmapped behavior. This establishes
a *possible status-contract gap* if the interleave can occur; it
does not prove an actual PS5 GPU/channel synchronization failure.

Do not change the runtime or weaken guest mapping guards until the
actual remap lock/owner protocol is confirmed and actual-source
race tests demonstrate a safe replacement.

## Repeatability gate — committed GitHub inputs verified

On the refreshed audit pass, independently fetched all nine test/runner
source files from the GitHub PR #44 head and compared each file's exact
UTF-8 character count and FNV-1a checksum with the locally compiled copy:

| File | UTF-8 chars | FNV-1a 32-bit | Match |
| --- | ---: | ---: | --- |
| `run_host_checks.sh` | 1184 | 3584663938 | PASS |
| `ssbo_extent_contract.hpp` | 3647 | 3367749903 | PASS |
| `native_vk_range_contract.hpp` | 3273 | 1869386525 | PASS |
| `test_ssbo_extent_contract.cpp` | 4758 | 1420155762 | PASS |
| `test_gpu_backing_lifetime.cpp` | 5099 | 3112276382 | PASS |
| `test_epoch_guarded_gmmu_memo.cpp` | 7662 | 1243215862 | PASS |
| `test_native_vk_range_contract.cpp` | 5265 | 3696510677 | PASS |
| `test_qmd3_descriptor_read_owner.cpp` | 4954 | 3415830595 | PASS |
| `test_native_gpu_read_toctou.cpp` | 3879 | 3880345910 | PASS |

The local runner initially differed in comment/formatting only. It was
resynchronized to the **exact GitHub text** and verified at `(1184, 3584663938)`
before repeating the full run. The six test sources and both headers
were already byte-equivalent. No runtime implementation changed.

With that exact runner and inputs:

- **O1 / Clang 17 and GCC 14:** all six suites PASS; 156 checks each, 312 total.
- **O0/O2 / both compilers:** all 24 binaries PASS; 624 checks.
- **Vendor source extractor:** still SKIP (no pinned vendor git checkout), not PASS.

All results are **local host research evidence**, not GitHub CI, not PS5
and not proof of a real guest process race. Parent audit and refreshed
[upstream closeout](../../docs/NS2_UPSTREAM_REFRESH_AND_CLOSEOUT_2026-11-10.md).

