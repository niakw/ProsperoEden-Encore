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

Current bounded runner now tests **102 standalone assertions per compiler**
(19 SSBO, 23 backing lifecycle, 30 lease/memo, 30 native Vulkan range). The **24-case**
separate source-expression harness remains a previously reproduced local
test; it is not added to the standalone runner because it requires
a pinned vendor source checkout for trustworthy extraction.

## O11 — native QMD3 Vulkan descriptor range guard (research only)

The standalone [range contract](native_vk_range_contract.hpp) and
[30-case fixture](test_native_vk_range_contract.cpp) model a **native-only
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

Run all four host suites with `bash research/ns2/run_host_checks.sh`.
