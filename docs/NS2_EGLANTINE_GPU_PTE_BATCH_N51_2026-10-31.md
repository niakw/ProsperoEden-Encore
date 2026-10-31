# NSW2 N51 — Eglantine GPU PTE changed-run batching (2026-10-31)

Branch: `research/ns2-ps5-compatibility`; production `main`, vendor and final release unchanged.

Upstream: [Eglantine f9fc1e1](https://github.com/Djihads80/Eglantine/commit/f9fc1e10fd7ed0a1c4664d48d2f095ce8826d87b). The pinned PS5 GPU memory owner still emits one rasterizer notification per changed small/big GPU page; large Switch 2 allocations can trigger hundreds of thousands of redundant invalidation calls.

The N51 opt-in complete owner overlay preserves all PS5 map/unmap, PTE handling, reverse mapping and address guards. It batches **only consecutive changed PTE pages** into a rasterizer notification; unchanged pages flush the pending run and the final run flushes before the kind map update. It does not merge across gaps. A source-bound parity checker rejects unrelated upstream drift.

CMake flag: `EDEN_NS2_EGLANTINE_GPU_RANGE_BATCH_EXPERIMENTAL=ON`, only with `PS5_NATIVE` and `EDEN_NS2_METADATA_EXPERIMENTAL`. OFF by default, forbidden by `EDEN_FINAL_RELEASE_PROFILE`.

Host test uses Clang and GCC with UBSan, two page granularities, randomized gap patterns, duplicate flush, invalid-range guard, and a synthetic 380,108-page all-changed case (one emitted notification vs 380,108 with the unbatched oracle). This is an algorithmic call-count result, **not** a PS5 frame-time measurement.

Next: verify GPU synchronization in an actual native environment before enabling; Eglantine partial ASTC and sparse terrain require additional PS5 shader/texture lifecycle review. N48 `Service::Process::Run` diagnostic issue still blocks full boot claims. No console tests, merge or release.
