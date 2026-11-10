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
