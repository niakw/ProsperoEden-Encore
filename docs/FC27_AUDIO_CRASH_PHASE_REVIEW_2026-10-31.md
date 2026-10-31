# PS5 native audio crash phase breadcrumbs — source review (2026-10-31)

| Source | Audit disposition after this review |
| --- | --- |
| `headless/audio.cpp` | Existing U04 code-changed disposition, bounded instrumentation only |
| `headless/crash_report.cpp` | Signal handler source re-reviewed; fixed-buffer snapshot |
| `headless/crash_report.h` | Lock-free diagnostic ABI re-reviewed |

**Evidence:** owner-provided hardware logs from code `46aaa92e` show FC27 crashed twice on the `audio` thread at `eboot+0x321b83` (SIGSEGV, fault `0x10`). Matching upstream and research blobs show `headless/audio.cpp` and maintained `audio_core/sink/sink_stream.cpp` did not change across NS2 merge. This does **not** localize the failure to an audio source line.

**Change:** `headless/crash_report.h` publishes four bounded lock-free inline atomics for the current PS5 native audio worker: pthread handle, phase (wait/render/device output/accounting/exit), accepted block count, and last output rc. In `headless/audio.cpp`, only two phase stores per 256-frame output block are added to the existing worker, with a third store during accounting; there is **no** additional audio mutex, allocation, syscall, file or log on the hot path. The existing ring-buffer rendering, producer lock release, failure handling and drain remain unchanged. The existing `tools/check-ps5-audio-output-lock-scope-host.py` source extraction from `lock.unlock()` through `lock.lock()` remains byte-compatible. The reporter reads these atomics only for the crashing worker thread, never another thread, and prints `audio worker snapshot` before the existing GPU and register diagnostics. Signal handling does no blocking or dynamic allocation.

**Host proof:** `tools/check-crash-report.py` exercises a deliberate SIGSEGV on a named audio thread with phase=3, blocks=41 and failed rc=0xfffffffb; normal CPU-thread crash reports must not include this line. It exercises the production signal handler in both host and PS5 shim modes. Source-early and runtime gate must pass before using the next build.

**Non-qualification:** This is *diagnostic instrumentation*, **not a fix** for FC27. It does not certify audio stability, first NS2 frame or gameplay. The old build's fault offset must be symbolized only with a matching native unstripped ELF. No game-specific behavior or NS1/NS2 conditional was introduced.

## ABI re-review — AudioOut worker token (31 October 2026)

- **Current source reviewed:** `headless/audio.cpp` Git blob `a927dcc543fea01f7f548a9a614abf81180e923d` at `main` HEAD `37ea5b4463f5356fb83016bc632ae96684a69b68`. The production change in `0f02ffe4fefc7a37d7536f7faafcb7982e4e3d75` is confined to the conversion `(std::uintptr_t)pthread_self()` in the existing release-store; it replaces a `static_cast` rejected by the pointer-form PS5 `pthread_t` at native build #41217142792 (1010/1607). Worker phases, PCM scan outside the mutex, error/frame accounting and exit cleanup remain unchanged.
- **Contract:** production worker publishes exactly one nonzero pthread token with `memory_order_release` and clears it with a second release-store of zero on exit; the crash-test worker intentionally only publishes the token before crashing. The source-extracted witness must assert both production stores, the single crash-harness store, and the exact conversion; it compiles both pointer/integer `pthread_t` representations at -O0/-O2 with UBSan. No relaxation of the strict reviewed-source Git blob guard.
- **CI requalification:** preflight #41221549362 failed on the stale source blob and on the witness mistakenly expecting only one production store. CodeQL #41221549477 succeeded. Fixes are test/ledger-only, not a new native engine change. Source/host CI must rerun on the new commit; no native PS5 build, FPS, audio-stability or gameplay result is claimed.
