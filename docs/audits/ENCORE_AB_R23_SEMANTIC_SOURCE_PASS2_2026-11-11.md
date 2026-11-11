# R23 — exact source-semantic dispositions, pass 2 (11 November 2026)

**Scope and proof level:** GitHub original commit patches compared to the pinned vendor source blob. Audit PR #45 only. No native build, no production import.

| Upstream | Source evidence | Disposition |
|---|---|---|
| **#53, `b7c1ded`** | Adds exactly one missing-key `LOG_ERROR` in `src/core/file_sys/content_archive.cpp`. Pinned original blob `b47b9437d0dfbc3f3adf40a45873d774f36b57f0`; `ErrorMissingKeyAreaKey` assignment and return unchanged | **Closed as observation-only**. No functional port for NS1. Optional error log remains separate |
| **#30, `2c40328`** | Adds macOS branches but also changes the `__FreeBSD__` network interface path and FreeBSD <15 API path | **Still open**, check PS5 libc/selected backend; title-only Mac exclusion would be inaccurate |
| **#93, `37fe911`** | Win32 fault handler correction **and** common `sparse_large_vector.h` non-Windows `mprotect` error handling and bool return | **Still open**, native sparse memory owner parity and failure tests required |

After this pass, the exact 155-commit ledger categorizes **106** runtime-semantic cases still awaiting decisions, **5** staged host candidates, **8** asset entries and **4** build/dependency entries. All native device/PS5 behavior gates remain open. Never count a source-only logging disposition as a tested emulator feature.
