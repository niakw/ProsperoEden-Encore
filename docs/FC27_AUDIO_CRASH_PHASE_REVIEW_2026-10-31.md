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
