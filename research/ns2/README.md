# NS2 host-only research fixtures — not linked to Encore

These standalone contracts intentionally live under `research/`, outside active
`tools/ns2`, `headless`, `vendor`, CI workflows, release, and submodule paths.
They are **not production code**, cannot change PS5 behavior and do not prove
that the native guest renderer passes any game. Do not merge unreviewed.

Compile offline with no project dependencies or SDK:

```bash
clang++ -std=c++20 -O1 -Wall -Wextra -Werror -fsanitize=undefined -fno-sanitize-recover=all \
  research/ns2/test_ssbo_extent_contract.cpp -o /tmp/ns2-ssbo-contract
/tmp/ns2-ssbo-contract
```

Also run GCC when convenient. The positive/negative cases describe a **desired
candidate** for the active `StorageBufferBinding` owner; they do not exercise
that existing owner. This is a *model* of a possible storage-length policy. Do not wire it into
legacy `BindComputeStorageBuffer`: native QMD3 instead goes through
`NativeQmdResourcePlan` and `ConfigureNative`. Require real native descriptor
ABI evidence and an actual-source test before any implementation review.

Evidence snapshot: Encore `dd9f2b96`, pinned vendor `22b69d60`.
Existing owner currently reads a size candidate from `ssbo_addr + 8` and uses
an 8 MiB fallback. This prototype requires explicit descriptor type and a
fully contiguous device range and treats the next qword as a non-size parameter
for proven native bare pointers. Both the interpretation and the range source
must be verified before applying it to the real renderer.

## Backing lifetime / alias-epoch research

`test_gpu_backing_lifetime.cpp` is an independent **model** of GPU device/CPU
backing registration, mapping, alias teardown, pending GPU fences and generation
re-use. It is deliberately not linked to `IGpuWorker` or `nvhost_as_gpu`.
Building it proves a proposed behavioral contract, not that Encore implements it.

```bash
clang++ -std=c++20 -O1 -Wall -Wextra -Werror -fsanitize=undefined -fno-sanitize-recover=all \
  research/ns2/test_gpu_backing_lifetime.cpp -o /tmp/ns2-backing-contract
/tmp/ns2-backing-contract
```

Local test counts on both clang++ and g++: SSBO contract **19/19** each;
backing lifetime model **23/23** each. This totals 42 distinct assertions
per compiler, all passed. No GitHub Actions or PS5 build were run.

## Critical correction: the native NS2 path is separate

The first SSBO extent prototype above models a policy, but **must not** be
wired into `BufferCache::StorageBufferBinding` as the native NS2 fix.
The native path uses `ComputePipeline::ConfigureNative` and its own
`NativeQmdResourcePlan::StageVulkanBufferBindings`; the shared
`BindComputeStorageBuffer` fallback is a *legacy* path. The QMD3 reader
accepts a descriptor only when `tag == 0 && bytes != 0` and rejects
unrecognized sizes. A real supported bare pointer may need a new
native-only, mapping-backed sizing contract, *after ABI proof*.

## Exact production-owner source witness (no PS5 build)

Run from the Encore repository root with the pinned vendor submodule checked out:

```bash
python3 -B research/ns2/check_native_qmd_owners.py --vendor vendor
```

The command asserts the actual legacy/native call split, the strict
`known_size` gate, and the real mapping helper's ownership. It then
extracts the unchanged `NativeQmdContiguousGpuSpan` C++ function from
the checked-out vendor and compiles it with a synthetic mapping harness
(Clang and GCC; UBSan, -O1). Positive/negative checks include holes,
noncontiguous pages, a changed last byte mapping, overflow and exceptions.

On the reviewed pinned code, one 32 MiB aligned span requests **8,193**
`GpuToCpuAddress` callback lookups. This is algorithmic evidence only:
not PS5 profiling and not proof that memoization is safe. The real
process epochs, fence lifetime and map/revision race checks must remain.

The inspected mapping function body plus the actual native size predicate passed
**24 cases** with Clang and GCC / UBSan in an isolated local C++ harness.
The complete repository extractor has **not** run on a pinned vendor checkout
or GitHub Actions, so that verification is still outstanding.

## Single bounded offline command

```bash
bash research/ns2/run_host_checks.sh
```

Runs 19 SSBO policy and 23 backing-lifetime assertions per compiler (Clang/GCC),
then runs the exact-source native validator **only when** the pinned vendor
checkout is present. Otherwise it reports `SKIP` and never pretends the source
test passed. The source witness also checks the six-pass native mapping call
graph and native descriptor-size predicate. There is no native PS5 build.

## O10 — versioned mapping memo research (not a deployable renderer fix)

The [lease-scoped GMMU memo fixture](test_epoch_guarded_gmmu_memo.cpp)
covers 30 assertions per compiler, tested locally with Clang 17 / GCC 14
under UBSan. All passed. The memo keys each positive result to the
**owner identity, process generation, mapping revision, GPU base and byte
length**, and a typed `ReadLease` holds a `shared_mutex` while the caller
checks/reuses the entry. Writer mutations acquire exclusive ownership and
increment the revision. A mapping hole, rebind, process reuse, overflow,
same-address owner destruction/recreation (ABA), or mapping change is
rejected or causes a new full scan. A concurrent writer test verifies that
an exclusive mapping update cannot finish during an active shared read lease;
revisions invalidate reused cache results after the writer commits.
A separate mutex protects memo state when readers overlap.

Under this **synthetic shared-lease assumption only**, six identical
32 MiB checks require 8,193 GPU→CPU translation callbacks rather than
49,158: an **83.3% reduction in lookups**, not a measured PS5 speedup.

**Do not port this memo into Encore yet.** The pinned production
`MemoryManager::GpuToCpuAddress` reads page entries without such a
public `ReadLease`, and native `ConfigureNative` does not acquire a mapping
revision/lease that extends through its descriptor and dispatch phases.
A global mapping revision is incremented around mutations, but merely
reading that revision without a real writer-exclusion protocol does NOT
prove a stable mapping (especially during overlapping writes). Holding
a new lock across scheduler waits or Vulkan recording could deadlock or
stall remaps. Preserve every current preflight, post-staging and commit
verification until actual ownership is redesigned and tested.

Current bounded runner now tests **156 standalone checks per compiler**
(19 SSBO, 23 backing lifecycle, 30 lease/memo, 33 Vulkan range, 35 QMD3 descriptor reader, 16 native GPU read status). The **24-case**
separate source-expression harness remains a previously reproduced local
test; it is not added to the standalone runner because it requires
a pinned vendor source checkout for trustworthy extraction.

## O11 — native QMD3 Vulkan descriptor range guard (research only)

The standalone [range contract](native_vk_range_contract.hpp) and
[33-case fixture](test_native_vk_range_contract.cpp) model a **native-only
two-stage Vulkan admission rule**. Both pass with Clang 17 / GCC 14 under UBSan.
This does **not** alter the maintained vendor or PS5 runtime.

- **Before GMMU staging:** reject zero, overflowing 49-bit guest spans,
  spans above the current native 256 MiB ceiling, and descriptor lengths
  exceeding the *queried* Vulkan `maxStorageBufferRange` or
  `maxUniformBufferRange` (also enforce the 64 KiB QMD3 CBUF ABI ceiling).
- **After `BufferCache::ObtainBuffer`:** require the actual buffer offset
  to meet device alignment, and `bytes <= backing_size - offset` using
  overflow-safe subtraction. Descriptor-buffer mode must have a nonzero
  base device address and valid `base + offset` arithmetic.
- **No silent clamping.** Reducing a declared guest buffer span can change
  shader semantics. Reject unsupported descriptors instead.
- Reviewed source owners at vendor `22b69d60`: `ConfigureNative` in
  `encore-active/eden-vulkan/vk_compute_pipeline_cost.cpp`;
  `Device::GetMaxStorageBufferRange()` / alignments in the maintained Vulkan
  device header; `Buffer::SizeBytes()` inherited from `BufferBase`; and
  `GuestDescriptorQueue::AddBuffer()` in `vk_update_descriptor.h`.

The actual PS5 driver `maxStorageBufferRange` and `maxUniformBufferRange`
have **not** been queried. A real-source/driver test must precede any
production patch. Preserve existing GMMU snapshot/remap checks, GPU
write tracking, and Switch 1 behavior.

Run all six host suites with `bash research/ns2/run_host_checks.sh`.

### Which PS5 Vulkan driver is actually packaged?

On the reviewed Encore `main`, `tools/build-package.sh` sets
`EDEN_PS5_VULKAN=ON EDEN_VULKAN_DRIVER=RADV`, and the maintained
RADV physical-device source at pinned vendor `22b69d60` advertises
`maxStorageBufferRange = UINT32_MAX` and `maxUniformBufferRange = UINT32_MAX`.
The *separate* `sources/ps5-vulkan-tools/driver/ps5vk_physical_device.c`
advertises 128 MiB SSBO and 16 KiB UBO, but this PS5VK driver is **not**
the main package's selected RADV path. The O11 128 MiB conflict therefore
does **not** establish a current Encore main-build defect.

The test fixture contains both source-advertised profiles (33 cases).
Source constants are **not** a console query: the actual reported
`VkPhysicalDeviceLimits` at runtime should still be recorded before
changing production code. O11 becomes a low-priority future-proof
admission guard rather than the NS2 optimization blocker.

## O1 — exact native QMD3 descriptor reader (35 source-owner tests)

[`test_qmd3_descriptor_read_owner.cpp`](test_qmd3_descriptor_read_owner.cpp)
embeds the **exact** `NativeMaxwellEnvironment::ReadStorageDescriptor`
method from pinned vendor `22b69d60`, with minimal fake QMD3 CBUF
ownership and a replaceable guest read callback. The method's normalized
747-character source matches the vendor's body and signature byte-for-byte
after removing whitespace/comments (FNV-1a **2431638797**; body-only
SHA-256 **44e011a540a5d79669867c9ebc16e2a2d6534ac94d6cffc8880948326ce9ade6**).

**35/35 tests pass on Clang 17 and GCC 14 under UBSan.** Cases cover
the eight-bank ABI, 4-byte descriptor offset alignment, complete 16-byte
single-callback GMMU read, end of 64 KiB window, disabled/undersized
CBUF, 49-bit guest VA boundary and read callback failure. The 16-byte
single callback is **not automatically an atomic snapshot** against
concurrent guest writes; later QMD3/renderer checks still matter.

The reader intentionally returns raw record words. It does **not** decide
whether word 2 is a legitimate byte length: `BuildResourcePlan` separately
uses `known_size = tag == 0 && bytes != 0` and refuses unknown sizes.
These tests therefore qualify the *reading* stage only, not native shader
descriptor semantics, Vulkan dispatch, or any PS5 game.

Current host runner: **156 checks per compiler** (19+23+30+33+35+16).
Separate real mapping-guard/known-size reproduction: 24 checks per compiler.
The full pinned-vendor checkout validator remains **SKIPPED** locally.

## O1 follow-up: native GPU shader read TOCTOU status hazard

The [exact native read callback fixture](test_native_gpu_read_toctou.cpp)
embeds the **unchanged** `VideoCommon::ReadNs2GpuShader` function from
`encore-active/ns2-runtime/ampere/video_core/native_shader_capture.cpp`
at pinned vendor `22b69d60`. The normalized method body matches the
vendor byte-for-byte after comments/whitespace removal (293 chars,
FNV-1a `3943302951`, SHA-256
`af4254dd7e7e00d246cef5a2d70f5790640077f6cc592c4a8c2b7871960eccf7`).
**16/16 checks pass under Clang 17 and GCC 14 / UBSan**, including
`-O0`, `-O1`, `-O2`. The fake `MemoryManager` controls a mapping
change between `IsFullyMappedRange` and `ReadBlock`.

Source-level contract concern: production `ReadNs2GpuShader`
prechecks `IsFullyMappedRange` but returns `true` unconditionally
after the **void** `MemoryManager::ReadBlock`, while the maintained
`ReadBlockImpl` zero-fills unmapped pages without reporting failure.
The mocked interleaving therefore accepts a zero-filled or partially
copied descriptor as a successful read. A single GMMU read callback is
NOT an atomic guest-memory transaction.

**Do not assume the race is reachable on PS5.** Before any patch,
trace map/unmap serialization, GPU channel lock and guest memory lifetime
at `NativeQmdComputeEnvironment` call sites. A safe correction needs
a real checked read/snapshot/lease guarantee under concurrent remaps.
Do not detect failure from zero contents: valid guest data can be zero.
Do not replace the existing safety barriers with a second unsound check.

The full vendor source validator now also refuses a change to the
callback body or zero-fill contract, but is still SKIPPED locally
because the complete pinned vendor checkout is absent.

## Audit disposition / refreshed forks

The full source-review decisions for Lichii's 17 newer commits and
nxnative's 2 new commits are recorded in
[NS2_UPSTREAM_REFRESH_AND_CLOSEOUT_2026-11-10.md](../../docs/NS2_UPSTREAM_REFRESH_AND_CLOSEOUT_2026-11-10.md).
The six-suite local runner and its inputs now match their published
GitHub source copies byte-for-byte in the reviewed snapshot; no
vendor checkout or native console execution is implied.


## R3 — GOB16 differential qualification

[`test_blocklinear_gob16_differential.cpp`](test_blocklinear_gob16_differential.cpp)
adds the seventh host suite to `run_host_checks.sh`. The C++ model
compares the pinned Encore per-pixel block-linear address formula against
Lichii's 16-byte group offset formula. Its **1536 seeded layouts** cover
all 192 combinations of 8 BPP values, block heights 0–3, block depths 0–2,
and both tiling orders, eight dimensions per combination, including
full-texture and subrectangle swizzle/unswizzle with canary-filled output.
23,578,183 byte-level address comparisons per execution passed; six
Clang/GCC × `-O0/-O1/-O2` executions passed with ASan and UBSan.

Only `BPP=16` uses the whole-image 16-byte fast copy in this model;
power-of-two BPP (1/2/4/8/16) may use split 16-byte subrectangle
runs, while 3/6/12 retain the original legacy per-pixel copy.
That restriction is intentional: the decoder's old memcpy semantics
do not guarantee a mathematically invertible path for non-power BPP
straddling swizzled unit boundaries. We test output equivalence there,
not claim a new valid roundtrip.

**Research-only:** identical mathematical offsets and sanitizer-clean
test runs justify a **candidate optimization**, not source-level
replacement in the maintained decoder, general performance benefit,
PS5 Vulkan result, or NS1 safety. The original decoder and vendor
remain unchanged. Source check: [pinned vendor witness](PINNED_VENDOR_SOURCE_WITNESS_2026-11-10.md).


## R2 — Vulkan upload batching source-equivalent negative/positive fixture

Added [`test_vulkan_upload_batch_contract.cpp`](test_vulkan_upload_batch_contract.cpp)
to the **eighth** bounded host suite. It embeds source-equivalent
`CanAdd` / `Add` bodies from Lichii's pinned `upload_batch.h`
(body fingerprints 1290869894 and 3125317133) and executes them
with synthetic Vulkan buffer handles and copy regions.
**25/25 tests pass with Clang/GCC across O0/O1/O2 and ASan/UBSan.**

The R2 candidate must preserve explicit barriers, ordered staging and
tick-based GPU lifetime. An integer-overflow negative test proves that
the upstream overlap predicate assumes valid Vulkan copy offsets:
a **separate fail-closed allocation-bound preflight** is mandatory
before source-equivalent batching. This is an invalid-input test,
not evidence that a real PS5 copy with valid offsets currently fails.

The current runner has **eight host-only suites**, including 181
discrete contracts and 1536 separately counted GOB differential layouts
on each compiler. The optional full pinned-vendor checker remains SKIP
until a real checkout is provided.


## Reproduce pinned vendor owner gate without cloning vendor

The original full-checkout form remains:
`python3 -B research/ns2/check_native_qmd_owners.py --vendor vendor`.

For a machine with Internet access, the alternate **six-source snapshot**
form avoids a complete vendor checkout:

```bash
bash research/ns2/fetch_pinned_vendor_snapshot.sh /tmp/encore-vendor-snapshot
```

The helper explicitly downloads six files from immutable vendor SHA
`22b69d60`, then calls the real Python validator with `--source-snapshot`.
The validator independently calculates Git's raw-blob SHA-1 for all six
files and **fails closed** on even a single wrong source byte. It then
compiles the exact native mapping helper on Clang/GCC and checks owner
and 6-pass rules. This is different from the synthetic standalone suite.

**Execution honesty:** snapshot downloader passed `bash -n`; hash
math passed against an existing published Git blob and a changed-byte
negative case. Full six-blob download+Python gate **not executable in the
current offline environment**, remains unverified. No source snapshot
or production vendor files were committed into this PR.



## R4 — Fermi2D cached 3D volume-slice admissibility

The ninth host suite,
[`test_volume_slice_admission.cpp`](test_volume_slice_admission.cpp),
transcribes the cached 3D-slice eligibility conditions from
[`Lichii nx2`](https://github.com/zortos293/Lichii/blob/879b616b1b377bfd085bf20f440b895cf4b83ab8/src/video_core/texture_cache/texture_cache.h).
It models `ForEachImageInRegionGPU`, eligible zero-mip slices, matching
cached volume dimensions/format, whole-slice source/destination rectangles,
independent source/destination cache image IDs, and a hypothetical stricter
admission rule. **It does not copy real Vulkan image bytes**, and unlike
the QMD3 owner tests, this is a **policy transcription**, NOT compilation
of the unmodified full upstream template method.

**50/50 host checks pass with each of Clang 17 and GCC 14 at
`-O0`, `-O1`, `-O2`, ASan+UBSan.** The candidate-specific negative
tests show that the upstream selection method does not test
`Fermi2D::Config::operation` or `filter`: it would accept synthetic
`Blend`, `ROP`, or `Bilinear` full-slice requests as a direct copy.
The current pinned Fermi2D `Blit()` emits an UNIMPLEMENTED diagnostic
for non-`SrcCopy` operations but does not return immediately before
calling `AccelerateSurfaceCopy`. Therefore, **require explicit native
`SrcCopy` operation admission and qualify the filter** if integrating.
This is a *source-level semantic risk*, not a proven PS5 gameplay
regression. A conservative research `StrictCandidate` rejects unknown
operations, filters, malformed metadata, and overwide image offsets.
The real mapped region and `u32` narrowing must be authenticated before
using `slice_offsets`.

The positive test resolves distinct cached volume IDs and selects
specific slices; partial rectangles, dimensions/formats mismatches,
nonzero layers, mip levels other than zero, absent images and
same-image copies fall back to generic `BlitImage`. Rejecting
same-image copies is **upstream behavior**, not automatically a bug.

**Current local host runner: nine suites, 231 finite research checks per
compiler, plus 1,536 GOB differential scenarios per compiler.**
Do not add the 1,536 separately to the 231 as if both represented
identical individual assertions. The pinned vendor gate still reports
`SKIP` in this environment. No PS5 speedup or rendering proof.


### R4 compatibility and provenance addendum

The synthetic Fermi2D operation codes are now pinned to actual
`Fermi2D::Operation` values from the vendor: SrcCopy=3, Blend=2,
ROP=4; filters Point=0 and Bilinear=1. The updated 50-case
fixture is **7046 characters, FNV-1a 1403218692**, and passes
both Clang/GCC in the whole `-O1` runner. The pinned
`Fermi2D::Blit()` logs unsupported non-copy operations but does
not short-circuit before calling `AccelerateSurfaceCopy`, so
do not rely on that diagnostic for safe copy-only admission.

Encore's active texture cache already has `CopyImage`,
`ForEachImageInRegionGPU`, and `FlushDeferredClear` support;
only **source-safe slice selection and cache integration** are
candidate additions. This remains a host-only policy model.
