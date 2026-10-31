# NSW2 N47 — maintained KProcess::LoadFromMetadata executed (host control path)

Date: 2026-10-31. Branch: `research/ns2-ps5-compatibility` only.
No `main` modifications, merges, releases, paid game dumps, firmware or keys.

## What runs

`tools/ns2/test_real_kprocess_metadata.py` extracts the **unchanged**
`KProcess::LoadFromMetadata` method body from pinned maintained source
`vendor/sources/eden/src/core/hle/kernel/k_process.cpp`. It compiles
that exact method using Clang and GCC with ASan/UBSan in host-only C++20.
It consumes both real physical files of the independently built
`main.npdm` + `main` public generic HOS AArch64 ExeFS corpus,
checks their identity, kernel descriptors and NSO memory footprint,
and supplies their expected values to a small fake metadata object.

The actual method runs its parameter, address-space, process resource
lifetime, `Initialize` call-routing and post-initialization flow against
host-owned fakes. Assertions require:
- correct code address/page count, title, 12-byte kernel process name;
- 39-bit, deprecated 36-bit, 32-bit and 32-bit-no-map address flags;
- correct 64-bit and application flags (with an additional system-pool case);
- original three KAC values and selected core forwarded unchanged;
- original ASLR start, resource-pool selection and resource-limit closure;
- failing `Initialize` short-circuits `InitializeInterfaces`, while still
  closing the kernel resource limit exactly once.

This test is a source-bound **actual method-body execution**, but it does
**not** instantiate a real kernel `KProcess`, use the real Horizon
`KernelCore` or page table, perform actual `Initialize`, schedule threads,
dispatch guest SVC/HLE, or run on PS5. The host fakes also define compact
equivalent enums and structs rather than compiling production headers.
Prior N44 real `KCapabilities` and metadata-parser CI tests remain
separate. Passing N47 is no evidence that Switch 2 commercial games boot.

## Reproducible CI

`.github/workflows/ns2-research-jit.yml` runs this validation immediately
after building the paired lawful ExeFS, before N46 original `LoadModule`
under host memory/page-table fakes and before the existing maintained
Dynarmic guest AArch64 execution. No console test is required.

Next hard gate: integration with an **actually initialized** production
`Kernel::KProcess` via `Core::System::Load` and the real main-thread/HLE
scheduler. That cannot be inferred from isolated method-body tests.
