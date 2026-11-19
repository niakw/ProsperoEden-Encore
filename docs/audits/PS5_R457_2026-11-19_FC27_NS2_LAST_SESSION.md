# PS5 R457 — user session 19 November 2026: FC27 NS1 and NS2

**Source of evidence:** user-supplied archive `logs19110141.zip` (15 ZIP members: separate `ns1/` and `ns2/` `stderr.log`, `heap.log`, boot traces and NS2 durable failure receipts). The raw console archive is not reproduced here; all measurements below were calculated from that upload. No new console execution was performed by this audit.

**Exact binary:** engine `2b0975f7c02f1cb663dd9ecd8c148ea1c4eea10e`; vendor gitlink `9a83a6ba1cb464c9e5d14457cab18ad511c1104b`; [native build #44423348645](https://github.com/niakw/ProsperoEden-Encore/actions/runs/44423348645). Both boot traces attest `source_sha=2b0975f7...`, PS5 firmware `0x13600007`. The build is the R457 01.400.457 title `PPSA99008`. Console installation/launcher/guest execution is **confirmed by these user-provided logs**; game compatibility/performance stability is not.

## P1 — FC27 NS1 `0100C49025D3E000`: measured buffer-cache contention

The 117 complete `EDEN_VULKAN_FRAME` five-second windows from `ns1/heap.log` span **approximately 585 seconds** (last complete frame total `16841`; one additional frame line is truncated and excluded). Parse only complete measurements and do not treat a sum of concurrent waits as wall time.

| Reproducible measure | Value |
|---|---:|
| FPS mean across equal-duration windows | `28.6658` |
| FPS median | `30.000` |
| Windows under 25 FPS | **14 / 117** |
| Windows under 20 FPS | **4 / 117** |
| Lowest measured window | **15.107 FPS** at frame `15382` |
| Worst individual present interval | **726.260 ms** at frame `2873` |
| Intervals over 100 ms (summed per-window) | **32** |
| Intervals over 500 ms (summed per-window) | **5** |
| Cache lock contention acquisitions, cumulative | **624,280** |
| Cache lock waiting, cumulative across threads | **15,440.964 ms** |
| Buffer-cache domain waiting | **15,414.493 ms (99.83%)** |
| Texture-cache domain waiting | **26.471 ms** |
| Worst five-second window of summed buffer+texture waiting | **910.940 ms** (frame `10485`, 32,802 contended acquisitions) |
| Max individual measured buffer cache lock wait (lifetime) | **5.279 ms**, **not** 910 ms |
| Accumulated GPU fence duration across the 117 windows | **1,401.709 ms** |
| Shader misses | **357** (305 graphics, 52 compute) |
| Shader miss CPU durations, summed | **2,320.752 ms** |
| Slowest individual shader miss CPU duration | **124.502 ms** |
| Five draw-drop categories | all 117 windows show `window=0` for each; this does **not** establish that HUD content is complete |
| Input | Last `EDEN_PAD_HEARTBEAT`: `polls=146250`, `samples=398909`, `errors=0`, `edges=670` |

High-contention low-FPS windows: frame 15382 = **15.107 FPS / 890.641 ms summed lock waiting**; frame 15306 = **19.611 FPS / 907.127 ms**; frame 15092 = **19.939 FPS / 847.952 ms**. Correlation is measurable, but not proof that the cache lock **alone** explains every stall. Shader miss outliers can also contribute. Do not conflate 15.4 s total thread waits with continuous stalling or a single contended lock acquisition; maximal single wait measured was ~5.3 ms. Original logs do not expose a complete guest-request→HUD-consumed→scanout causal chain.

Source path: selected `vendor/encore-active/eden-vulkan/vulkan_rasterizer.cpp::OnCPUWrite` enters `GuestCacheLock(buffer_cache.mutex,false)`, then executes `buffer_cache.OnCPUWrite` and write-ahead invalidation under the held cache mutex. The selected source already has `BufferPages::NeverRegistered` fast-path. `headless/performance.h::GuestCacheLock` uses original blocking `mutex.lock()` when detailed diagnostics are OFF, so lock-contention figures in a detailed session must **not** be assumed identical to quiet-mode timing.

Upstream comparators examined:
- [Lichii #1518](https://github.com/zortos293/Lichii/pull/1518), merged: defers CPU page-protection updates until after releasing the buffer mutex for certain guest writes. Its exact `GpuSplit`/device-page invalidation ordering is different and the initial port needed a remap-race fix. **Candidate for comparative analysis, not a safe blind NS1 import.**
- [Lichii #413](https://github.com/zortos293/Lichii/pull/413), merged: skip `MustFlushRegion` buffer lock on provably never-GPU-written **Ampere/NS2** pages. The PR expressly retains the locked path for non-Ampere titles; it is **not** a direct FC27 NS1 fix.
- [Eden Issue-Reports #771](https://github.com/eden-emulator/Issue-Reports/issues/771) and older R457 FC27 records require checking exact shader/pipeline keys and guest timeline before changing behavior.

**Priority:** P1. Compare time spent inside `BufferCache::OnCPUWrite`/page-protection work versus wait-to-acquire, and bound any lock-elision with an exact correctness invariant and concurrency test. Don't discard shader miss outliers. FC27 HUD and pause delays remain open.

## P0 — Mario Kart World / Bananza: exactly reproduced guest-fault signature

| Evidence | Mario Kart World | Donkey Kong Bananza |
|---|---|---|
| Title ID | `0400C3F00006E000` | `040074A01BF12000` |
| Main code entry | `0x80384000` | `0x807a4000` |
| Mapped main stack | `0x1085604000..0x1085704000` | `0x1084004000..0x1084104000` |
| Mapped stack bytes | `0x100000` (1 MiB) | `0x100000` (1 MiB) |
| Final guest PC/LR | `0x4 / 0x0` | `0x4 / 0x0` |
| Faulted SP | `0x1085603f00` | `0x1084003ef0` |
| SP below mapped bottom | **0x100 (256 bytes)** | **0x110 (272 bytes)** |
| SP page-table state | **0 (unmapped)** | **0 (unmapped)** |
| Failed direct allocation receipt | **none (direct_failure=0)** | **none (direct_failure=0)** |
| Last largest-free direct-memory extent | `10825498624` bytes | `10825498624` bytes |

Both sessions reached `core_loaded`, `gpu_started` and `guest_run_begin` with a valid initial `EDEN_MAIN_STACK_MAP` state. The **new strong** `EDEN_NS2_GUEST_FAULT_V1` was saved for both, followed by `EDEN_SESSION_FAILURE_V1` (attempts 1 and 2). Last SVC 0x06 (`QueryMemory`) and 0x29 (`GetInfo`) reported completed result zero; their precise values are present in the original log. SVC 0x25 in the short history is `GetThreadId`, **not** a 1 MiB memory-allocation SVC: the previous 0x100000 stack-size value in x4 is an unsanitized stale register for that call. SVC 0x0C / 0x25 entries do not carry a completed outcome in this ring; do not infer that their result was successful or unsuccessful from the absent field. `PC=0x4`/under-bottom SP is a reproducible **failure signature**, not yet proof that an undersized NPDM stack was the initiating defect.

There is no evidence for `Cannot allocate memory` in these **two NS2 attempts**. The prior title-relaunch P0 memory issue is separate; in NS2 `heap.log`, host heap `pieces=1207959552` bytes persists across both core shutdowns, but this alone is not a proven leak. JIT sparse reserved/committed counters reach zero by shutdown.

**Upstream:** [Eglantine #350](https://github.com/Eglantine-Community/Eglantine/issues/350) documents a **different** Bananza loose-dump configuration: `base/exefs/main` + manually merged update RomFS ended at `PC=0x4`; starting from the correct update ExeFS/RomFS adjacency eliminated thousands of null writes but moved the failure to a service wait. This is a credible installation/loader provenance comparison, **not proof** Encore has the same missing update layers. The console log identifies `EDEN_CONTENT_PATH kind=extracted_exefs manual_nca=not_applicable romfs=loader_owned`; no full verified update-container provenance is present in this archive. Do not assume assets/firmware are invalid. The boot log's `runtime=research_only` NS2 firmware status is a separate caveat, not direct evidence for the guest PC fault.

**CMake-selected debug gap:** This exact released binary included `EDEN_NS2_GUEST_FAULT_V1` but excluded the PS5-only GPU worker diagnostic groups because `gpu_worker.cpp` lacked a per-TU `PS5_NATIVE=1` definition. The native build produced `restored_sparse_ranges set but not used`. Source-only candidate: engine [PR #290](https://github.com/niakw/ProsperoEden-Encore/pull/290). It does **not** correct a memory map, invalid guest return PC, stack frame or game GPU program. It needs CI and build qualification before any future release; no extra console test requested tonight.

## Negative evidence and limits

- `ns1/session-active.txt` ends `stage=guest_running`; the supplied NS1 archive does not include an FC27 shutdown, relaunch or terminal native crash. **Do not** classify FC27 same-process OOM/exit as fixed or reproduced by this specific archive.
- `ns2/boot-trace.txt` has two launcher→game→launcher cycles, and the last line returns to the launcher; there is no logged native console termination in that part.
- Black-screen loading HUD presentation is not a guest frame. Neither NS2 title has a proven submitted real guest frame.
- The release artifact is valid and installed; source compilation and packaging alone never certify runtime behavior.

## Next engineering actions (without extra console requests tonight)

1. Keep NS2 [issue #123](https://github.com/niakw/ProsperoEden-Encore/issues/123) and FC27 [issue #100](https://github.com/niakw/ProsperoEden-Encore/issues/100), relaunch [issue #281](https://github.com/niakw/ProsperoEden-Encore/issues/281) open.
2. Compare `GetThreadId`/thread context and correct update-content mounting against Eglantine's reproducible case before altering the **guest-declared** 1 MiB stack; blind 2–4 MiB allocation might merely move the fault.
3. For FC27, use the existing combined `EDEN_FRAME_CACHE_DOMAIN` / shader-miss telemetry to build a host repeatable race/backpressure witness; compare Lichii #1518 only after proving the native PS5 NS1 page-protection lifetime and lock-order behavior.
4. Preserve all this evidence against compiled SHA `2b0975f7`; never claim that future source commits affect the console session captured here.
