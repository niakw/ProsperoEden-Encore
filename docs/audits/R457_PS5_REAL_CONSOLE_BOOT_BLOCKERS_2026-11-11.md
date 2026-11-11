# Eden Encore R457 — two PS5 real-console boot blockers (2026-11-11)

## Evidence boundary

- **Actual native release source:** `ec8b519182532d3864c5a67dd27aa41aa9d43ff3`, pinned vendor `90c9c8a203a27181e23349a889a8f2a7d1cd9dd2`, R457 native workflow [#42942150990](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42942150990). Source identification is not proof that a runtime package was installed correctly; the crash code size matches the associated `llvm-pie.elf`.
- **Actual user console testing, cache cleared:** two crash files for NS1 FC27 and a normal failed launch log for NS2. Never upload the entire user log archives (which may expose paths/identifiers) as a PR asset. The minimal observations below are sufficient to reproduce forensic analyses.
- **Exact artifact recovered from GitHub:** `build/symbols/Prospero.Eden-Encore-R457.elf`, `199322632` bytes from the recovered R457 bundle, symbols trace to `memory_native_a32.cpp`; `crash-provenance.json` says `native_ps5_execution_verified=false`. Tests of this ELF alone do not qualify emulation on the console.

## P0-NS1 — FC27 null memory implementation on the audio thread

Two console crashes were observed at 10:06:47 and 10:07:14, both:
- Signal `SIGSEGV` (fault address `0x10`) on thread `audio`.
- Instruction offset `eboot+0x39152f`; `rdi=0`, `rdx=0xc00`, sample guest buffer address in `rsi`.
- Disassembly in the **actual R457 ELF** at `0x39152f`: `mov 0x10(%rdi), %r8`, exactly the failing 16-byte-offset memory dereference.
- Native symbol `Core::Memory::Memory::Impl::GetSpan(unsigned long, unsigned long) const`; the call stack resolves via `Core::Memory::GuestMemory<..., short, UnsafeRead>::Read` → `AudioCore::DeviceSession::AppendBuffers` → `AudioCore::AudioOut::System::Start` → `Service::Audio::IAudioOut::Start`. This is **not** a Vulkan driver or Opus decoder crash.
- Native wrapper `Memory::GetSpan` at `0x38d050` loads `Memory::impl` with `mov 0x8(%rdi), %rdi`, then jumps to `Impl::GetSpan`. At the crash site that **implementation pointer is null**. A preexisting `current_page_table == nullptr` guard inside `Impl::GetSpan` cannot execute because `Impl::this` is already null.

Pinned source audit:
- `vendor/encore-active/eden-core/src/core/memory_native_a32.cpp`: `Memory::Memory(Core::System&)` calls `Reset()`, which `make_unique<Impl>`; `GetSpan` simply forwards through `impl`.
- `vendor/encore-active/eden-core/src/core/hle/kernel/k_process.cpp`: `KProcess` constructs its `m_memory{kernel.System()}`.
- `vendor/sources/eden/src/audio_core/device/device_session.cpp`: audio output dereferences `handle->GetMemory()` in `AppendBuffers` and uses `CpuGuestMemory<UnsafeRead>`. `Initialize` calls `handle->Open(...)` and `Finalize` calls `handle->Close(...)`.
- **What is proved:** null `Memory::impl` dereference at the audio guest-read call. **Not proved:** why it becomes null (partially initialized/destroyed process object, stale handle, lifetime race, memory overwrite or another bug).

Resolution checklist (no fake success):
1. Trace the full audio service and `KProcess` lifetime at setup, guest launch, audio event scheduling, shutdown/relaunch; examine all paths that publish, Close, reuse or destroy `KProcess`, `Memory`, `AudioOut::System`, and `DeviceSession`. Include the process identity/generation, audio session ID, `handle`, and `m_memory` readiness in **diagnostics only**, no sensitive game data.
2. Reproduce the null implementation in a host fixture for audio-session process teardown/interleaving, then modify the **true owner** of the lifetime/initialization bug, not an unrelated GetSpan cast or synthetic zero-fill. Ensure audio event is cancelled before process destruction and that live process memory is initialized before publishing audio session.
3. Host negative test: no audio callback may access a finalized process; host positive test: AudioOut buffered reads continue with valid mapped memory. Avoid disabling audio globally.
4. Qualify touched native C++ source selected by real CMake, then at most one consented PS5 test candidate. Acceptance: FC27 advances past AudioOut startup, first game-presented frame, audio works, crash `0x39152f` absent.

## P0-NS2 — physically impossible monolithic 12 GiB guest backing on PS5

Two launches of NS2 titles fail *before* game boot with the same exception:
- `Direct allocation failed: rc=80020023 bytes=12886999040 limit=13019119616` → `Game load failed: Backing allocation: Cannot allocate memory`.
- The requested 12.00 GiB continuous allocation exceeds the largest single free direct-memory span measured at this point (~7.5 GiB); the overall direct-memory limit value is not the free contiguous capacity.
- Main `src/host_memory.cpp` `HostMemory::Impl(requested,...)` uses `AllocateMemoryPages(requested)` on `PS5_NATIVE` and throws `std::system_error(..., "Backing allocation")` on failure.
- Main `src/memory_pages.cpp` attempts a monolithic `sceKernelAllocateDirectMemory` for the full requested size. The existing sparse **JIT** reservations are not a replacement for the guest DRAM backing; logs show `EDEN_JIT_SPARSE_MEMORY phase=core_initialized reserved=0 committed=0` separately.
- In the same logs, the 3D-jacket snapshot was prepared before failure. No Vulkan/NS2 game frame was ever demonstrated. Do not infer that shader issues are fixed or still blocking until memory init succeeds.

Required architectural change: preserve the **full emulated NS2 guest DRAM address space** but reserve host virtual range independently of physically committed pages. Implement page/granule-level, owned, lazy direct-memory commit with synchronized read/write, GPU DMA/address-translation and Vulkan alias coherence, correct zero-fill on first touch, defined reuse and rollback; maintain alignment, exact ownership, use-after-free prevention, and peak physical memory budget. `std::memset` of a virtual hole, reduced declared NS2 DRAM, silent allocation retries, increasing swap on the console, or `malloc(12 GiB)` are NOT sufficient.

Resolution / test gates:
1. Host mapping ownership state machine and sparse commit/decommit test across 16KiB native granules, first/last page, cross-page CPU read/write, repeated alloc and no double-free.
2. Exhaustion and fragmentation behavior, predictable error handling and rollback, plus consistent CPU→GPU and GPU→CPU views; protect source shared with NS1 and use only real compiled overrides.
3. Real PS5 CMake graph selects all modified sources and headers; run an isolated memory test before a full build.
4. PS5 startup gate: direct backing no longer asks for 12 GiB physical at once; both NS2 games reach **guest CPU service startup and first GPU frame handoff** before claiming success.

## Launcher regression distinct from the boot blockers

[Draft PR #49](https://github.com/niakw/ProsperoEden-Encore/pull/49) is reserved for visible launcher fixes and host checks (L1/R1 routing, R457 display, firmware/ns1/ns2 format/status, centered settings gear). It does **not** fix the NS1/NS2 memory crashes. Other texture/orientation/timing defects remain separately unqualified.

## Do not regress

- Keep `main` and the pinned `vendor` untouched while the current R457 console build is under diagnosis.
- Do not repeatedly build the native package until the new P0 host gates and actual CMake source selection pass.
- Distinguish proven binary fault location from a merely hypothesized ownership cause.
- Never mark a CI-green result as PS5 gameplay success.
