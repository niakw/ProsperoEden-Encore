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


## Update — 7th suite and authenticated pinned-vendor source review

**Previously stated six-suite totals above remain historical**; the current
bounded runner has **seven** standalone suites. All seven compile and pass
on Clang 17 and GCC 14 at `-O1`; the seventh suite additionally passed
on both compilers at `-O0` and `-O2` with **ASan + UBSan**.

Seventh suite: [`test_blocklinear_gob16_differential.cpp`](test_blocklinear_gob16_differential.cpp),
exact locally executed UTF-8 content **8605 chars, FNV-1a 18407156**,
Git blob `2f2ea5ee0d1a1d4f40508f40e34233136f3b5ee7`. The published
[runner](run_host_checks.sh) is also local-byte-identical:
**1371 chars, FNV-1a 2846275155**.

The seeded differential oracle covers **1536 layouts = 192 unique
BPP / block-height / block-depth / tiling profiles × 8 shapes**.
It checked **23,578,183 individual block-linear byte-address mappings**
per execution, plus positive/negative full-texture and partial-rectangle
swizzle/unswizzle output equivalence and legal roundtrips. Supported
BPP cases: `1,2,3,4,6,8,12,16`; 3/6/12 retain the original fallback.
All six compiler×optimization executions passed with ASan/UBSan enabled.
**This is a separately reconstructed source-formula differential model,
not compilation of either complete emulator decoder or a PS5 performance test.**

Additional vendor source evidence: [26/26 source-owner checks](PINNED_VENDOR_SOURCE_WITNESS_2026-11-10.md)
passed against six vendor files independently fetched at the exact
`22b69d60` commit, recording all six Git blob hashes. Those checks
do **not** replace the Python full-vendor Git-checkout extractor
(still **SKIP** in the local runner).

Current gate totals must be reported separately: **156 discrete SSBO/
memory/GMMU/Vulkan/QMD3/read contracts per compiler**, plus **1536
block-linear differential layouts per compiler** with 23.58 million
address-oracle comparisons each. Do not conflate these test classes
or infer 23.58 million real PS5 frames or CPU speedup.


## Update — eighth host suite: Lichii Vulkan upload-batch admission

Added [`test_vulkan_upload_batch_contract.cpp`](test_vulkan_upload_batch_contract.cpp)
(5200 characters, FNV-1a `432374617`, Git blob
`30a5afae2d9ef92d775f87c8d1e19851ed6603bb`).
The synthetic-handle fixture executes the **exact maintained upstream
`UploadBatch::CanAdd` and `UploadBatch::Add` C++ function bodies** from
`zortos293/Lichii@879b616b1b377bfd085bf20f440b895cf4b83ab8`.
Both normalized bodies match upstream (CanAdd 431 chars, FNV
`1290869894`; Add 304 chars, FNV `3125317133`).

**25/25 bounded host assertions pass** with Clang 17 and GCC 14 at
`-O0`, `-O1`, `-O2`, with ASan/UBSan.
Validated nonoverlap, same-buffer ordering, intergroup RAW/WAR hazards,
destination overlaps, 64-copy budget, and caller-per-region enforcement.

**Explicit hostile finding:** the upstream overlap expression adds
`dstOffset+size` without checking unsigned overflow. For *invalid*
simulated copy ranges near `UINT64_MAX`, it can miss an overlap.
This is **not** proof of a Vulkan bug under authentic, already-bounded
driver buffer lengths. A future Encore port must first reject any
zero-length, out-of-buffer or overflowing `srcOffset` / `dstOffset`
copy and must not batch overlaps or cross synchronization boundaries.

Runner now includes **eight** suites; exact local/GitHub runner content
matches (1453 chars, FNV `2912948555`, Git blob
`6f70d453beb67858a46816f81282f9fa56857b7d`).
The O1 matrix has **181 standalone assertion contracts per compiler**
(19+23+30+33+35+16+25), **plus 1536 block-linear differential
scenarios per compiler**. Do not treat the latter as 1536 extra
finite-assertion calls; each scenario exercises many byte offsets.

**Vendor checker remains SKIP** without the full pinned checkout.
No native PS5 code, Vulkan allocator, scheduler, source pin or build changed.



## Update — ninth suite: Lichii Fermi2D 3D volume-slice admission

Added [`test_volume_slice_admission.cpp`](test_volume_slice_admission.cpp),
**7,046 characters, FNV-1a 32-bit `1403218692`**, matching the exact
locally compiled file. Source behavior reviewed from the upstream
`TextureCache::CopyVolumeSlice` owner at Lichii nx2
`879b616b1b377bfd085bf20f440b895cf4b83ab8`; actual engine
types were replaced with small synthetic `Surface`, `CachedImage`,
`Copy` and `Slice` structures. **This is a transcribed decision
model**, not the original fully compiled Vulkan texture-cache method.

**50/50 assertions pass on each of Clang 17 and GCC 14 with
ASan/UBSan at `-O0`, `-O1`, `-O2` (six clean binaries).**
Cases cover source/destination cached volume selection and depth,
unmapped/undersized/malformed metadata, 2D/Pitch fallback, partial
copy coordinates, mismatched format/dimensions, bad mip, cached image
identity and explicit operation/filter negative admission.
`CopyVolumeSlice` upstream checks neither `operation` nor `filter`,
so a synthetic whole-volume `Blend`/`ROP`/`Bilinear` request is
admitted; the stricter *proposed* preflight rejects it. Real production
race/guest reachability was not tested.

Local published runner `run_host_checks.sh` now has **nine host suites**
and passed all nine with each compiler at `-O1`; `50` finite
R4 assertions are added to the previous `181`, totaling **231 finite
checks per compiler** alongside the **separate** 1,536 GOB scenarios.
The two compilers at `-O1` therefore execute 462 finite checks and
3,072 GOB scenarios, not 462 PS5 checks.

A complete nine-suite × three-optimization matrix was attempted:
**33 binary executions passed before the single batch timed out**
at the expensive GCC `-O0` GOB oracle. This is a **timeout, not a
passing complete 54-binary matrix**. The new volume-slice suite
independently passed all six compiler/optimization combinations,
and prior R2/R3 separate O0/O2 results remain recorded above.

The pinned vendor source extractor still reports `SKIP`, no
PS5 native build/CI tests executed, and no production files changed.

### R4 verified owner/ABI cross-check

The R4 test fixture now uses the **pinned real Fermi2D operation/filter
integer codes**, `SrcCopy=3`, `Blend=2`, `ROP=4`, `Point=0`,
`Bilinear=1`, rather than invented test-only enum ordinals. Source
owners and pinned Git blob IDs were independently verified:

- Lichii `src/video_core/texture_cache/texture_cache.h` at
  `879b616b1b377bfd085bf20f440b895cf4b83ab8`:
  `b497d4f1b08ccc4067613a4f769d857735d5bc61`.
- Encore active `encore-active/eden-vulkan/vulkan-cache/video_core/texture_cache/texture_cache.h`:
  `f0c685c1be128ec161ebd53f2ab507badff88bc1`.
- Encore `encore-active/eden-vulkan/vk_texture_cache_cost.cpp`:
  `97c11bebf775b2139f87f3a8d22e4d06446df14e`.
- Encore `sources/eden/src/video_core/engines/fermi_2d.h`:
  `7fddf9fdc19e3d1735bccab3bc8385756216cfee`.
- Encore `sources/eden/src/video_core/engines/fermi_2d.cpp`:
  `aeff5e156f8c331f5ec7c929aa1fdadd2eb5dc8a`.

Direct owner inspection confirms `CopyVolumeSlice` is not yet
integrated, while `TextureCacheRuntime::CopyImage`, cached image
lookup and `FlushDeferredClear` are already present. The native
source-copy acceptance guards still need real-owner integration.
After updating the enum values, the nine-suite `-O1` runner was
re-executed and **all nine suites passed under Clang and GCC**,
including the updated R4 50-case suite. The exact GitHub R4 source
is **7,046 characters, FNV-1a 1403218692**.

**Matrix qualification:** the R4 suite separately passed all
six compiler × optimization (`-O0`, `-O1`, `-O2`) combinations
with ASan/UBSan before and after the enum adjustment at `-O1`.
The full 54-binary matrix still has a timeout at GCC -O0
GOB16, so its completeness is not claimed.
