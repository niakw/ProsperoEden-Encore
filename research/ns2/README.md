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
that existing owner. To promote: first prove precise `native_pointer` and
`compute` provenance from real Ampere resource reflection and mapping epoch;
then implement in a vendor research branch, test actual source and build
against then-pinned Encore, and verify NS1 and NS2 before main integration.

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

The same function text and 17-case C++ harness passed on Clang and GCC
locally; the Python extractor has not yet executed on GitHub Actions.
