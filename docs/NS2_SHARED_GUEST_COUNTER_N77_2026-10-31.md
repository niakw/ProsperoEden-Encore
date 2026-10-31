# NSW2 N77 — shared CoreTiming and service guest-frequency conversions (2026-10-31)

**Scope:** `research/ns2-ps5-compatibility` + pinned `research/ns2-shared-core` in `vendor`. Production `main` remains untouched.

## Corrected actual owners

- `vendor/encore-active/eden-core/include/common/cpu_features.h` is a **single selected engine header overlay**, not a second CPU/JIT or renderer. The original source of this one common header is `vendor/sources/eden/src/common/cpu_features.h` and the only behavior changed is two CNTPCT conversion methods, guarded by `EDEN_NS2_GUEST_COUNTER`.
- `Common::WallClock::CPUTickToCNTPCT` is called by the existing `CoreTiming::GetClockTicks()` **non-multicore** path. It now uses the current verified per-program 19.2/31.25 MHz counter selection instead of a static 19.2 MHz ratio.
- `Common::WallClock::NSToCNTPCT` (also available to HLE/time services) now uses the same per-program selection; the calculation uses 128-bit multiplication to avoid intermediate overflow. This makes the *common conversion API* correct; it does **not** prove every service uses it.
- Multicore `WallClock::GetCNTPCT` and A64 `CNTFRQ_EL0` were connected in N76; their existing owners are unchanged. GPU clock remains on its independent frequency.
- NS1-only and production builds have the **exact prior inline conversion path**, as the experimental macro is not set.

## Tests

`tools/ns2/check_guest_counter_policy.py` now executes the **real selected common WallClock header** using both GCC and Clang/UBSan. It checks NS1→NS2→NS1 in-process changes, 60 Hz frame conversions, CPU tick conversions, and non-experimental header behavior. It also checks the real vendor `CoreTiming::GetClockTicks` callsite. The existing `NS2 research host guards` CI already calls this script; no duplicated workflow is needed.

## Limits / priority

No actual Switch 2 game running on Encore PS5 is proven. Some HLE time services may do their own raw tick conversions: audit those callers before claiming full service coverage. Next critical path: verify true 12 GiB guest virtual layout without allocating 12 GiB of host committed memory; gate native PS5 allocations by shared CPU/GPU pool; then first program → GPU channel → visible image integration.
