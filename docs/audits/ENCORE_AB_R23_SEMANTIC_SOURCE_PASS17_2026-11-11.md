# R23 pass17 — #31 mmap IOFile and #45 NCZBLOCK optimization

**11 Nov 2026. Source evidence E1, audit-only PR #45.** Current target is PS5 native x64, not Android or desktop; do not confuse source disposition with a speedup on console.

## #31 — upstream mmap file reader is not a safe default replacement

Official Eden [`41b6807f127526e89ede0fb40748d6ae988fc0cc`](https://github.com/eden-emulator/mirror/commit/41b6807f127526e89ede0fb40748d6ae988fc0cc) changes `src/common/fs/file.cpp` and `file.h` with a read-only mmap/madvise path for `IOFile`. Original pinned `src/common/fs/file.cpp` blob **`461a5eee352dcc95025667f9e02d625fe00c52e5`** uses stdio, and pinned `file.h` **`b1ccfbd18a38f65dfa452d4632a66d3b5b55c308`** has no `mmap_fd` or `IsMappedFile`. The upstream code includes FreeBSD `MAP_ALIGNED(21)`, `MAP_NOSYNC`, large/small readahead and an `open(path)` check of `fd > 0` (fd zero is valid), while `mmap` of an empty file cannot be assumed successful. File truncation, concurrent changes, mapped lifetime and native memory pressure need direct testing.

**Disposition:** `reviewed-native-mmap-IOFile-experimental-policy-deferred`. Keep stable stdio implementation; the actual throughput/VM behavior on PS5 must be measured under memory pressure and source-compiled with PS5 SDK before considering such a port. No claimed performance equivalence.

## #45 — no compiled existing native NCZ decompressor TU to optimize

Official Eden [`ea92c081b710dc1fb6e35ce8bc05bee8dd6ddf06`](https://github.com/eden-emulator/mirror/commit/ea92c081b710dc1fb6e35ce8bc05bee8dd6ddf06) updates `src/core/crypto/ncz_decompressor.cpp` to a reusable `ZSTD_DCtx` and 32-slot direct-mapped decoded block cache, avoiding repeated decompression and cache traversal. In frozen pinned vendor `sources/eden/src/core/crypto` the upstream `ncz_decompressor.cpp` **does not exist**, and original native `src/core/CMakeLists.txt` Git blob **`508ace350173f5068bd7531f37e70199134fde3a`** does not mention that source. This proves only that **that specific TU** is not a current native compiled owner; it does not prove NSZ/NCZ support or performance parity of other Encore loaders.

**Disposition:** `reviewed-upstream-NCZBLOCK-optimization-module-not-current-native-owner`. Defer import until actual maintained NSZ/NCZ entrypoint and host ZSTD ABI identified; replay compressed/plain blocks, collisions, random seeks and decryption under real title I/O. Do not ship a new module solely to satisfy an audit count.

## Exit

155/155 original upstream commit-file inventory maintained; **31 general source semantic reviews**, **22 verified gaps**, **7 scoped policy/refactor checks**, **17 native changed-header receipts** and **7 corrective release-batch gates** remain. Neither case has been ported or measured on PS5. No impact on main/vendor/NS2 research.
